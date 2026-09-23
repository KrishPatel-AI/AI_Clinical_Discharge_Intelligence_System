"""Build and query the local FAISS guideline vector index."""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib
import json
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

faiss: Any = importlib.import_module("faiss")
np: Any = importlib.import_module("numpy")

DEFAULT_GUIDELINES_DIR = Path(__file__).parent / "guidelines"
DEFAULT_INDEX_DIR = Path(__file__).parent / ".faiss"
INDEX_FILENAME = "guidelines.index"
METADATA_FILENAME = "metadata.json"
EMBEDDING_DIMENSION = 2048
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


class _TextExtractor(HTMLParser):
    """Extract readable text from HTML stored inside source XML."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self.parts).split())


def _html_to_text(value: str) -> str:
    parser = _TextExtractor()
    parser.feed(html.unescape(value))
    return parser.text()


def _chunks(text: str) -> list[str]:
    if not text.strip():
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = end - CHUNK_OVERLAP
    return [chunk for chunk in chunks if chunk]


def _read_records(guidelines_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    markdown_paths = sorted(guidelines_dir.glob("*/*.md"))
    for source_path in markdown_paths:
        text = source_path.read_text(encoding="utf-8")
        if not text.strip():
            raise ValueError(f"Empty Markdown document: {source_path}")
        if "�" in text:
            continue
        metadata_path = source_path.parent / "metadata.json"
        source_url = ""
        diagnosis = source_path.parent.name
        if metadata_path.exists():
            source_metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            for document in source_metadata.get("documents", []):
                document_filename = str(document.get("filename") or "")
                if Path(document_filename).stem == source_path.stem:
                    source_url = str(document.get("source_url") or "")
                    diagnosis = str(document.get("diagnosis") or diagnosis)
                    break
        if not source_url:
            continue
        for chunk_number, chunk in enumerate(_chunks(text)):
            records.append(
                {
                    "id": f"{source_path.parent.name}:{source_path.name}:{chunk_number}",
                    "document": chunk,
                    "metadata": {
                        "diagnosis": diagnosis,
                        "diagnosis_slug": source_path.parent.name,
                        "source_url": source_url,
                        "source_file": source_path.name,
                        "chunk_number": chunk_number,
                    },
                }
            )

    for source_path in sorted(guidelines_dir.glob("*/medlineplus-health-topic.xml")):
        root = ET.parse(source_path).getroot()
        if root is None:
            raise ValueError(f"Empty XML document: {source_path}")
        document = root.find(".//document")
        health_topic = root.find(".//health-topic")
        summary = root.findtext(".//full-summary")
        if document is None or health_topic is None or not summary:
            raise ValueError(f"Missing required health-topic fields: {source_path}")
        source_url = document.attrib.get("url", health_topic.attrib.get("url", ""))
        title = health_topic.attrib.get("title", source_path.parent.name)
        for chunk_number, chunk in enumerate(_chunks(_html_to_text(summary))):
            records.append(
                {
                    "id": f"{source_path.parent.name}:{chunk_number}",
                    "document": chunk,
                    "metadata": {
                        "diagnosis": title,
                        "diagnosis_slug": source_path.parent.name,
                        "source_url": source_url,
                        "source_file": source_path.name,
                        "chunk_number": chunk_number,
                    },
                }
            )
    return records


def _embed(texts: list[str]) -> np.ndarray:
    vectors = np.zeros((len(texts), EMBEDDING_DIMENSION), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            column = int.from_bytes(digest[:4], "little") % EMBEDDING_DIMENSION
            vectors[row, column] += 1.0
        norm = np.linalg.norm(vectors[row])
        if norm:
            vectors[row] /= norm
    return vectors


def _index_paths(index_dir: Path) -> tuple[Path, Path]:
    return index_dir / INDEX_FILENAME, index_dir / METADATA_FILENAME


def build_index(
    guidelines_dir: Path = DEFAULT_GUIDELINES_DIR,
    index_dir: Path = DEFAULT_INDEX_DIR,
) -> int:
    """Incrementally add new chunks without duplicating existing chunks."""
    records = _read_records(guidelines_dir)
    if not records:
        raise ValueError(f"No guideline Markdown or XML files found in {guidelines_dir}")
    index_dir.mkdir(parents=True, exist_ok=True)
    index_path, metadata_path = _index_paths(index_dir)
    current_by_id = {record["id"]: record for record in records}
    if index_path.exists() and metadata_path.exists():
        index = faiss.read_index(str(index_path))
        stored_records = json.loads(metadata_path.read_text(encoding="utf-8"))
        stored_by_id = {record["id"]: record for record in stored_records}
        unchanged = all(
            record_id in current_by_id
            and current_by_id[record_id]["document"] == record["document"]
            for record_id, record in stored_by_id.items()
        )
        if unchanged and set(stored_by_id).issubset(current_by_id):
            new_records = [
                record for record in records if record["id"] not in stored_by_id
            ]
            if new_records:
                index.add(_embed([record["document"] for record in new_records]))
                stored_records.extend(new_records)
            metadata_path.write_text(
                json.dumps(stored_records, indent=2), encoding="utf-8"
            )
            faiss.write_index(index, str(index_path))
            return len(stored_records)
    index = faiss.IndexFlatIP(EMBEDDING_DIMENSION)
    index.add(_embed([record["document"] for record in records]))
    metadata_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
    faiss.write_index(index, str(index_path))
    return len(records)


def query_index(
    query: str,
    index_dir: Path = DEFAULT_INDEX_DIR,
    limit: int = 3,
) -> dict[str, list[Any]]:
    """Return the nearest indexed guideline chunks for a query."""
    if not query.strip():
        raise ValueError("Query must not be empty")
    index_path, metadata_path = _index_paths(index_dir)
    if not index_path.exists() or not metadata_path.exists():
        raise ValueError(f"No index found in {index_dir}")
    index = faiss.read_index(str(index_path))
    records = json.loads(metadata_path.read_text(encoding="utf-8"))
    distances, positions = index.search(_embed([query]), min(limit, index.ntotal))
    return {
        "documents": [records[position]["document"] for position in positions[0]],
        "metadatas": [records[position]["metadata"] for position in positions[0]],
        "distances": distances[0].tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--guidelines-dir", type=Path, default=DEFAULT_GUIDELINES_DIR)
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR)
    args = parser.parse_args()
    count = build_index(args.guidelines_dir, args.index_dir)
    print(f"Indexed {count} guideline chunks in FAISS.")


if __name__ == "__main__":
    main()