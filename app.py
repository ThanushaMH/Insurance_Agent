
"""
app.py
Professional UI for FNOL Claims Routing Agent
"""

import json
import streamlit as st
from pipeline import run_fnol_agent

st.set_page_config(
    page_title="FNOL Claims Routing Agent",
    page_icon="📋",
    layout="wide"
)

# ======================
# CUSTOM CSS
# ======================
st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.hero {
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    padding: 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 20px;
}

.hero h1 {
    margin: 0;
}

.metric-box {
    background: #f8fafc;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
}

.route-card {
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 15px;
}

.fast {
    background: #16a34a;
}

.manual {
    background: #eab308;
    color: black;
}

.investigation {
    background: #dc2626;
}

.specialist {
    background: #2563eb;
}

.standard {
    background: #64748b;
}

.stButton > button {
    width: 100%;
    height: 50px;
    border-radius: 10px;
    font-size: 18px;
}

.field-card {
    background: black;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    margin-bottom: 10px;
}

</style>
""", unsafe_allow_html=True)

# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.title("📋 FNOL Agent")

    st.markdown("### Workflow")

    st.markdown("""
    1️⃣ Upload FNOL Document

    2️⃣ Extract Information

    3️⃣ Validate Fields

    4️⃣ Apply Routing Rules

    5️⃣ Generate Reasoning

    6️⃣ Save to Excel
    """)

    st.divider()

    st.markdown("### Routing Rules")

    st.markdown("""
    🟡 Manual Review

    🔴 Investigation Flag

    🔵 Specialist Queue

    🟢 Fast-track

    ⚪ Standard Review
    """)

# ======================
# HERO SECTION
# ======================
st.markdown("""
<div class="hero">
    <h1>📋 FNOL Claims Routing Agent</h1>
    <p>
    AI-powered insurance claim triage system that extracts claim information,
    validates mandatory fields, detects suspicious claims, and automatically
    routes them to the correct processing queue.
    </p>
</div>
""", unsafe_allow_html=True)

# ======================
# FILE UPLOAD
# ======================
st.markdown("## 📂 Upload FNOL Document")

uploaded_file = st.file_uploader(
    "Upload a TXT or PDF file",
    type=["txt", "pdf"]
)

ROUTE_COLORS = {
    "Fast-track": "🟢",
    "Manual Review": "🟡",
    "Investigation Flag": "🔴",
    "Specialist Queue": "🔵",
    "Standard Review": "⚪",
}

if uploaded_file is not None:

    # ======================
    # READ FILE
    # ======================
    if uploaded_file.name.lower().endswith(".pdf"):
        try:
            import pdfplumber

            with pdfplumber.open(uploaded_file) as pdf:
                document_text = "\n".join(
                    page.extract_text() or ""
                    for page in pdf.pages
                )

        except Exception as e:
            st.error(f"Could not read PDF file: {e}")
            document_text = None

    else:
        document_text = uploaded_file.read().decode(
            "utf-8",
            errors="ignore"
        )

    if document_text:

        with st.expander("📄 View Raw Document"):
            st.text(document_text)

        if st.button("🚀 Process Claim", type="primary"):

            with st.spinner("Running extraction and routing..."):

                try:
                    result = run_fnol_agent(document_text)

                except Exception as e:
                    st.error(
                        f"Agent pipeline failed unexpectedly: {e}"
                    )
                    result = None

            if result:

                route = result["recommendedRoute"]

                route_class = {
                    "Fast-track": "fast",
                    "Manual Review": "manual",
                    "Investigation Flag": "investigation",
                    "Specialist Queue": "specialist",
                    "Standard Review": "standard"
                }

                badge = ROUTE_COLORS.get(route, "⚪")

                # ======================
                # ROUTE CARD
                # ======================
                st.markdown(
                    f"""
                    <div class="route-card {route_class.get(route, 'standard')}">
                        {badge} {route}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.success(result["reasoning"])

                # ======================
                # METRICS
                # ======================
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Recommended Route",
                        route
                    )

                with col2:
                    st.metric(
                        "Missing Fields",
                        len(result["missingFields"])
                    )

                with col3:
                    st.metric(
                        "Extraction Method",
                        result["_extractionMethod"]
                    )

                # ======================
                # STATUS MESSAGES
                # ======================
                if result["_extractionMethod"] == "regex_fallback":
                    st.warning(
                        "Extraction used regex fallback because "
                        "LLM was unavailable."
                    )

                log_status = result.get("_excelLogStatus")

                if log_status == "appended":
                    st.info(
                        "📊 New claim added to claims_log.xlsx"
                    )

                elif log_status == "updated":
                    st.info(
                        "📊 Existing claim updated in claims_log.xlsx"
                    )

                elif log_status == "failed":
                    st.warning(
                        "Could not update claims_log.xlsx"
                    )

                st.divider()

                # ======================
                # EXTRACTED FIELDS
                # ======================
                st.markdown("## 📑 Extracted Fields")

                left, right = st.columns(2)

                items = list(
                    result["extractedFields"].items()
                )

                for i, (field, value) in enumerate(items):

                    with left if i % 2 == 0 else right:

                        st.markdown(
                            f"""
                            <div class="field-card">
                                <b>{field}</b><br>
                                {value if value else "Not Available"}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.divider()

                # ======================
                # MISSING FIELDS
                # ======================
                if result["missingFields"]:

                    st.error(
                        "Missing Mandatory Fields: "
                        + ", ".join(result["missingFields"])
                    )

                else:
                    st.success(
                        "All mandatory fields are present."
                    )

                st.divider()

                # ======================
                # JSON OUTPUT
                # ======================
                with st.expander("🔍 View JSON Output"):

                    internal_keys = {
                        "_extractionMethod",
                        "_excelLogStatus"
                    }

                    clean_result = {
                        k: v
                        for k, v in result.items()
                        if k not in internal_keys
                    }

                    st.code(
                        json.dumps(
                            clean_result,
                            indent=2,
                            ensure_ascii=False
                        ),
                        language="json"
                    )

