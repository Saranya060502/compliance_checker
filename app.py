import streamlit as st
from pipeline import run_compliance_check

st.set_page_config(
    page_title="GDPR Compliance Checker",
    page_icon="🔒",
    layout="wide"
)

# --- Styling ---
st.markdown("""
<style>
    .compliant { color: #22c55e; font-weight: bold; }
    .partial { color: #f59e0b; font-weight: bold; }
    .non-compliant { color: #ef4444; font-weight: bold; }
    .score-box {
        text-align: center;
        padding: 2rem;
        border-radius: 12px;
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .score-number { font-size: 4rem; font-weight: 800; }
    .category-card {
        padding: 1rem 1.2rem;
        border-radius: 8px;
        border-left: 4px solid;
        margin-bottom: 0.8rem;
        background: #fafafa;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🔒 GDPR Compliance Checker")
st.markdown("Paste any privacy policy below to instantly analyze its GDPR compliance.")
st.divider()

# --- Input ---
col1, col2 = st.columns([2, 1])

with col1:
    policy_text = st.text_area(
        "Privacy Policy Text",
        height=300,
        placeholder="Paste the full privacy policy text here..."
    )

with col2:
    st.markdown("### How it works")
    st.markdown("""
    1. Paste a privacy policy
    2. The system chunks and analyzes the text
    3. Each section is matched against **10 GDPR categories**
    4. An LLM assesses compliance and flags gaps
    5. You get a score + detailed breakdown
    """)
    st.markdown("**Powered by:** Blended RAG + Llama 3 (Groq)")

# --- Analyze Button ---
if st.button("🔍 Analyze Compliance", type="primary", use_container_width=True):
    if not policy_text.strip():
        st.warning("Please paste a privacy policy to analyze.")
    elif len(policy_text.strip()) < 100:
        st.warning("The text seems too short. Please paste the full privacy policy.")
    else:
        with st.spinner("Analyzing compliance... this takes ~20 seconds"):
            try:
                output = run_compliance_check(policy_text)
                score = output["score"]
                results = output["results"]

                st.divider()

                # --- Score ---
                if score >= 80:
                    score_color = "#22c55e"
                    score_label = "Good Compliance"
                elif score >= 50:
                    score_color = "#f59e0b"
                    score_label = "Partial Compliance"
                else:
                    score_color = "#ef4444"
                    score_label = "Poor Compliance"

                st.markdown(f"""
                <div class="score-box">
                    <div class="score-number" style="color:{score_color}">{score}/100</div>
                    <div style="font-size:1.2rem; color:#64748b">{score_label}</div>
                </div>
                """, unsafe_allow_html=True)

                # --- Summary Stats ---
                compliant = sum(1 for r in results.values() if r["status"] == "COMPLIANT")
                partial = sum(1 for r in results.values() if r["status"] == "PARTIAL")
                non_compliant = sum(1 for r in results.values() if r["status"] == "NON-COMPLIANT")

                c1, c2, c3 = st.columns(3)
                c1.metric("✅ Compliant", compliant)
                c2.metric("⚠️ Partial", partial)
                c3.metric("❌ Non-Compliant", non_compliant)

                st.divider()
                st.markdown("### Detailed Breakdown")

                # --- Category Results ---
                for category, result in results.items():
                    status = result["status"]
                    if status == "COMPLIANT":
                        border_color = "#22c55e"
                        icon = "✅"
                        css_class = "compliant"
                    elif status == "PARTIAL":
                        border_color = "#f59e0b"
                        icon = "⚠️"
                        css_class = "partial"
                    else:
                        border_color = "#ef4444"
                        icon = "❌"
                        css_class = "non-compliant"

                    with st.expander(f"{icon} {category} — {status}"):
                        st.markdown(f"**Assessment:** {result['explanation']}")
                        if result["gap"] and result["gap"].lower() != "none":
                            st.markdown(f"**Gap:** {result['gap']}")

                # --- Gaps Summary ---
                gaps = [(cat, r["gap"]) for cat, r in results.items()
                        if r["gap"] and r["gap"].lower() != "none"]

                if gaps:
                    st.divider()
                    st.markdown("### 🚨 Gaps to Address")
                    for cat, gap in gaps:
                        st.markdown(f"- **{cat}:** {gap}")

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")
                st.markdown("Make sure your `GROQ_API_KEY` is set in the `.env` file.")

# --- Footer ---
st.divider()
st.markdown(
    "<div style='text-align:center; color:#94a3b8; font-size:0.85rem'>"
    "Built by Saranya · Blended RAG Architecture · IEEE COMPSAC 2025"
    "</div>",
    unsafe_allow_html=True
)