"""Doctor-facing Streamlit review workspace."""
from __future__ import annotations

import html
from typing import Any

import requests
import streamlit as st

API_BASE = "http://localhost:8000"
SAMPLES = {
    "Asthma exacerbation": "Discharge Summary\n\nDiagnosis: Asthma exacerbation\n\nMedications\n- Salbutamol inhaler, as needed\n- Prednisolone course\n\nFollow-up\n- Review with primary care\n\nCurrent condition\nBreathing improved. Patient is stable for discharge.",
    "Type 2 diabetes": "Discharge Summary\n\nDiagnosis: Type 2 diabetes mellitus\n\nMedications\n- Metformin 500 mg twice daily\n\nFollow-up\n- Follow up with the clinic\n\nCurrent condition\nGlucose is stable. Patient understands medication schedule.",
    "High blood pressure": "Discharge Summary\n\nDiagnosis: High blood pressure\n\nMedications\n- Amlodipine 5 mg daily\n\nFollow-up\n- Return to clinic as advised\n\nCurrent condition\nPatient is stable and ready for discharge.",
}
DEMO_SUGGESTIONS = [
    {"section": "Warning signs", "explanation": "Add clear symptoms that should prompt urgent medical attention after discharge.", "guideline_passage": "Seek immediate help for severe breathing difficulty, bluish lips, or symptoms that worsen despite treatment.", "decision": None},
    {"section": "Follow-up", "explanation": "Make the follow-up plan more specific by including a timeframe and responsible clinic.", "guideline_passage": "Follow-up should be arranged with the treating clinician to review symptom control and the treatment plan.", "decision": None},
]


def styles() -> None:
    st.markdown("""<style>
    :root{--ink:#183438;--muted:#6d8082;--line:#dce7e6;--accent:#2c6e73;--soft:#f4f8f7}
    .stApp{background:#f7faf9;color:var(--ink)} [data-testid=stSidebar]{background:#edf4f3;border-right:1px solid var(--line)}
    .brand{display:flex;gap:.7rem;align-items:center;padding:.3rem 0 1.2rem}.brand-mark{width:34px;height:34px;border:1px solid #9fc4c2;border-radius:10px;display:grid;place-items:center;color:var(--accent);font-weight:800;background:white}.brand-title{font-weight:750}.brand-sub{font-size:.72rem;color:var(--muted)}
    .eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-size:.68rem;font-weight:750}.page-title{font-size:2rem;letter-spacing:-.04em;font-weight:780;margin:.15rem 0 .25rem}.page-subtitle{color:var(--muted);font-size:.92rem}
    .surface{background:white;border:1px solid var(--line);border-radius:16px;padding:1rem 1.1rem;box-shadow:0 4px 18px rgba(24,52,56,.04)}.doc{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1.25rem;min-height:390px;white-space:pre-wrap;font-family:Georgia,serif;line-height:1.7;color:#263d40}.doc-label{display:flex;justify-content:space-between;margin-bottom:.7rem;color:var(--muted);font-size:.76rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.status{padding:.25rem .55rem;border-radius:999px;font-size:.7rem;font-weight:700;background:#e5f1ef;color:var(--accent)}
    .suggestion{border:1px solid #e1e9e8;border-left:3px solid #d3a74b;border-radius:10px;padding:.8rem .85rem;margin:.55rem 0;background:#fffdf8}.suggestion.accepted{border-left-color:#3c8a62;background:#f5fbf7}.suggestion.ignored{border-left-color:#a2afb0;background:#f7f9f9;opacity:.8}.suggestion-title{font-weight:750;font-size:.88rem}.suggestion-copy{color:#546b6c;font-size:.82rem;line-height:1.45;margin:.3rem 0 .5rem}.evidence{font-size:.75rem;color:#6d8082;padding:.55rem .65rem;background:#f5f8f7;border-radius:7px;line-height:1.4}.metric{font-size:1.65rem;font-weight:780}.metric-label{color:var(--muted);font-size:.75rem}.step{text-align:center;color:#8a999a;font-size:.72rem}.step.active{color:var(--accent);font-weight:750}.step-dot{width:25px;height:25px;border-radius:50%;border:1px solid #bfd3d1;display:grid;place-items:center;margin:auto auto .3rem;background:white}.step.active .step-dot{background:var(--accent);color:white;border-color:var(--accent)}.stButton>button{border-radius:9px;min-height:2.35rem;font-weight:650;border-color:var(--line)}.stButton>button[kind=primary]{background:var(--accent);border-color:var(--accent)}
    </style>""", unsafe_allow_html=True)


def review_upload(file: Any) -> dict[str, Any] | None:
    try:
        response = requests.post(f"{API_BASE}/discharge/review", files={"file": (file.name, file.getvalue(), file.type)}, timeout=90)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">CI</div><div><div class="brand-title">Clinical Insight</div><div class="brand-sub">Discharge review</div></div></div>', unsafe_allow_html=True)
        st.button("+  New review", type="primary", use_container_width=True)
        st.markdown("**Workspace**")
        st.button("Review workspace", use_container_width=True)
        st.button("Review history", use_container_width=True)
        st.markdown("**Recent reviews**")
        for name in ["Asthma exacerbation", "Type 2 diabetes", "High blood pressure"]:
            st.button(name, key=f"history-{name}", use_container_width=True)
        st.caption("Advisory review only. Every suggestion requires doctor approval.")


def steps(active: int) -> None:
    cols = st.columns(5)
    for number, (col, label) in enumerate(zip(cols, ["Upload", "Analyze", "Review", "Approve", "Export"]), 1):
        with col:
            active_class = "active" if number <= active else ""
            st.markdown(f'<div class="step {active_class}"><div class="step-dot">{number}</div>{label}</div>', unsafe_allow_html=True)


def suggestion(index: int, item: dict[str, Any]) -> None:
    decision = item.get("decision")
    label = "Pending review" if decision is None else decision.capitalize()
    st.markdown(f'<div class="suggestion {decision or ""}"><div class="suggestion-title">{html.escape(item["section"])} <span class="status">{label}</span></div><div class="suggestion-copy">{html.escape(item["explanation"])}</div><div class="evidence"><strong>Guideline evidence</strong><br>{html.escape(item["guideline_passage"])}</div></div>', unsafe_allow_html=True)
    if decision is None:
        accept, ignore, _ = st.columns([1, 1, 3])
        with accept:
            if st.button("Accept", key=f"accept-{index}", type="primary", use_container_width=True):
                item["decision"] = "accepted"
                st.rerun()
        with ignore:
            if st.button("Ignore", key=f"ignore-{index}", use_container_width=True):
                item["decision"] = "ignored"
                st.rerun()


def main() -> None:
    st.set_page_config(page_title="Clinical Insight | Discharge review", layout="wide", initial_sidebar_state="expanded")
    styles(); sidebar()
    st.session_state.setdefault("document", "")
    st.session_state.setdefault("review", {})
    st.session_state.setdefault("suggestions", [])
    st.markdown('<div class="eyebrow">Doctor workspace</div><div class="page-title">Discharge review</div><p class="page-subtitle">Check completeness against sourced health guidance before the document leaves your care team.</p>', unsafe_allow_html=True)
    steps(3 if st.session_state.document else 1); st.divider()
    if not st.session_state.document:
        left, right = st.columns([1.1, .9], gap="large")
        with left:
            st.markdown("### Start a review")
            st.write("Upload a discharge summary or open a synthetic case to test the complete doctor approval flow.")
            file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"], label_visibility="collapsed")
            if file and st.button("Analyze discharge summary", type="primary", use_container_width=True):
                with st.spinner("Extracting and comparing with sourced guidance..."):
                    result = review_upload(file)
                if result:
                    st.session_state.review = result; st.session_state.document = file.getvalue().decode("utf-8", errors="ignore") if file.type == "text/plain" else f"{file.name}\n\nDocument processed by the clinical review service."; st.session_state.suggestions = result.get("suggestions", []); st.rerun()
                st.error("The review service is unavailable. Confirm that FastAPI is running, then try again.")
            st.caption("or use a synthetic test case")
            sample = st.selectbox("Synthetic case", list(SAMPLES), label_visibility="collapsed")
            if st.button("Open sample case", use_container_width=True):
                st.session_state.document = SAMPLES[sample]; st.session_state.review = {"diagnosis": sample, "completeness_score": 72}; st.session_state.suggestions = [dict(item) for item in DEMO_SUGGESTIONS]; st.rerun()
        with right:
            st.markdown('<div class="surface"><div class="eyebrow">How it works</div><h3>A second reviewer, never an editor</h3><p style="color:#6d8082;line-height:1.55">Clinical Insight identifies possible gaps, shows the source passage behind each suggestion, and waits for your explicit decision. Nothing is applied automatically.</p><hr><div style="color:#546b6c;line-height:1.8">1. Upload a summary<br>2. Review grounded suggestions<br>3. Accept or ignore each item<br>4. Export the final reviewed document</div></div>', unsafe_allow_html=True)
        return
    review = st.session_state.review; items = st.session_state.suggestions; accepted = sum(i.get("decision") == "accepted" for i in items); ignored = sum(i.get("decision") == "ignored" for i in items); pending = len(items) - accepted - ignored
    a, b, c = st.columns([2.2, 1, 1])
    with a: st.markdown(f'<div class="surface"><div class="eyebrow">Active review</div><h3>{html.escape(str(review.get("diagnosis", "Discharge summary")))}</h3><span style="color:#6d8082;font-size:.8rem">Original summary · doctor-controlled review</span></div>', unsafe_allow_html=True)
    with b: st.markdown(f'<div class="surface"><div class="metric">{review.get("completeness_score", 72)}%</div><div class="metric-label">Completeness score</div></div>', unsafe_allow_html=True)
    with c: st.markdown(f'<div class="surface"><div class="metric">{pending}</div><div class="metric-label">Pending decisions</div></div>', unsafe_allow_html=True)
    st.write("")
    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown('<div class="doc-label"><span>Original document</span><span class="status">Read only</span></div>', unsafe_allow_html=True); st.markdown(f'<div class="doc">{html.escape(st.session_state.document)}</div>', unsafe_allow_html=True)
    with right:
        export_type = st.selectbox("Export format", ["PDF", "DOCX", "TXT"]); final = st.session_state.document; approved = [i["section"] for i in items if i.get("decision") == "accepted"]
        if approved: final += "\n\nReviewed additions\n" + "\n".join(f"- {section}: Added after doctor approval." for section in approved)
        st.markdown('<div class="doc-label"><span>Final reviewed document</span><span class="status">Doctor controlled</span></div>', unsafe_allow_html=True); st.markdown(f'<div class="doc">{html.escape(final)}</div>', unsafe_allow_html=True); st.download_button(f"Export final document as {export_type}", final, file_name=f"reviewed-discharge.{export_type.lower()}", mime="text/plain", use_container_width=True)
    st.markdown(f"### Suggestions <span style='font-size:.8rem;color:#6d8082;font-weight:400'>{accepted} accepted · {ignored} ignored · {pending} pending</span>", unsafe_allow_html=True); st.caption("Each suggestion is grounded in retrieved source text. Decide individually; accepted items appear in the final document.")
    for index, item in enumerate(items): suggestion(index, item)
    if pending == 0 and items: st.success("All suggestions have a doctor decision. The final document is ready to export.")
    if st.button("Start a new review"):
        for key in ["document", "review", "suggestions"]: st.session_state.pop(key, None)
        st.rerun()


if __name__ == "__main__":
    main()
