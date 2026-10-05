# Security Notes

## Dependency audit exceptions (2026-10-05)

The CI dependency audit explicitly ignores the following two PYSEC IDs using
`pip-audit --ignore-vuln`. These are scoped decisions for the current usage,
not claims that the upstream packages are generally safe. Reassess both if
application or evaluation code begins using the affected features, and remove
the ignores when patched releases become available.

- **PYSEC-2026-2447 (`diskcache` 5.6.3):** The advisory concerns unsafe
  pickle deserialization when an attacker can write to a DiskCache directory
  that the application later reads. No backend or test code imports
  `diskcache`, creates a DiskCache instance, configures a cache directory, or
  reads DiskCache content. Ragas installs DiskCache as a dependency, but this
  project's evaluation runner does not instantiate Ragas' optional
  `DiskCacheBackend`; it uses the local Ollama model and embedding endpoints
  directly. The vulnerable pickle read/write path is therefore not exercised
  by this codebase as currently configured. Recheck if Ragas caching is added.

- **PYSEC-2026-3046 (`ragas` 0.4.3):** The advisory concerns SSRF in Ragas'
  multimodal faithfulness collection when attacker-controlled media references
  are processed. The evaluation runner imports only the text metrics
  `Faithfulness`, `AnswerRelevancy`, and `ContextPrecisionWithReference` from
  `ragas.metrics.collections`. It passes synthetic text, retrieved text
  passages, and textual references; it does not import or call multimodal
  metrics, media resolvers, or URL/file processing helpers. That affected
  multimodal path is not exercised by the current evaluation. Recheck if
  multimodal evaluation is introduced.

Both findings were reported by pip-audit as having no available fix version
in the configured package index at the time of this review. CI ignores only
these IDs; all other findings continue to fail the audit. `--skip-editable`
excludes the repository's editable local distribution, which is not a PyPI
package and cannot be independently audited by pip-audit; it does not skip
any installed dependency.
