import os
import shutil
import warnings
import streamlit as st
from dotenv import load_dotenv
import pandas as pd

from src.resume_checker.crew import ResumeReaderCrew

# ==== ENV and Setup ====
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
warnings.filterwarnings("ignore", message="missing ScriptRunContext")

# Load API Key
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("❌ OPENAI_API_KEY not found. Check your .env file.")


# uploader_key setup, to reload the state after clear all button
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if "jd_key" not in st.session_state:
    st.session_state["jd_key"] = 0

if "jd_text" not in st.session_state:
    st.session_state["jd_text"] = ""

# =========================================
# 🎯 MAIN APP AFTER LOGIN
# =========================================
st.title("📄 Resume Screening AI")
st.subheader("Empowering Recruiters with Agentic Intelligence")

st.set_page_config(
    page_title="Resume Screening AI",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f9f9f9;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ==== Sidebar Upload ====
with st.sidebar:
    st.header("📤 Upload Resumes (⚠ Only add PDF files)")
    st.header("⚠ Max limit : 30 PDFs")

    uploaded_resumes = st.file_uploader(
        "Upload Resume PDFs(Max 30)", type=["pdf"], accept_multiple_files=True, key=f"resume_files_{st.session_state['uploader_key']}"
    )

    unique_resumes = []
    duplicate_files = []
    seen_files = set()

    if uploaded_resumes:
        for file in uploaded_resumes:
            if file.name not in seen_files:
                unique_resumes.append(file)
                seen_files.add(file.name)
            else:
                duplicate_files.append(file.name)

        st.success(f"{len(unique_resumes)} unique resume(s) selected.")
        if duplicate_files:
            st.warning(f"⚠ Duplicates skipped: {', '.join(duplicate_files)}")

# ==== Job Description in the center====
jd_text = st.text_area(
    "📋 Paste the Job Description (JD) here",
    value=st.session_state["jd_text"],
    key=f"jd_text_area_{st.session_state['jd_key']}"
)

st.session_state["jd_text"]  = jd_text

# ==== Run Screening in Batches ====
if st.button("▶ Run Screening in Batches"):
    if not unique_resumes or not jd_text:
        st.warning("⚠ Upload at least one resume and enter the job description.")
    else:

        with st.spinner("Processing resumes in batches...", show_time=True):

            from datetime import datetime
            st.caption(f"🕒 Last run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


            UPLOAD_DIR = "uploaded_resumes"
            RESULT_DIR = "batch_results"

            # Clean previous uploads and results if any
            shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
            shutil.rmtree(RESULT_DIR, ignore_errors=True)

            os.makedirs(UPLOAD_DIR, exist_ok=True)
            os.makedirs(RESULT_DIR, exist_ok=True)

            # ✅ Batching Logic
            batch_size = 10
            total = len(unique_resumes)
            batches = [unique_resumes[i:i + batch_size] for i in range(0, total, batch_size)]

            crew = ResumeReaderCrew()
            all_warnings = []

            for idx, batch_files in enumerate(batches, start=1):
                st.subheader(f"🚀 Processing Batch {idx} ")

                batch_folder = os.path.join(UPLOAD_DIR, f"batch_{idx}")
                os.makedirs(batch_folder, exist_ok=True)

                for file in batch_files:
                    file_path = os.path.join(batch_folder, file.name)
                    with open(file_path, "wb") as f:
                        f.write(file.getvalue())

                result_data = crew.kickoff_batch(batch_folder, jd_text, idx)

                # ✅ Collect warnings if any
                if result_data.get("warnings"):
                    all_warnings.extend(result_data["warnings"])

            # 🔥 Display warnings in sidebar
            with st.sidebar:
                if all_warnings:
                    st.markdown("## ⚠ Extraction Warnings")
                    for warn in all_warnings:
                        st.warning(warn)
                else:
                    st.success("✅ All PDFs processed successfully with no issues.")

            st.success("✅ All batches processed! You can now generate the final report.")


# ==== Generate Final Table ====
if st.button("📥 Generate Final Table"):
    with st.spinner("Compiling all batch results..."):
        crew = ResumeReaderCrew()
        batch_results = crew.load_all_batches()

        all_candidates = []
        all_warnings = []

        for batch in batch_results:
            if "candidates" in batch and batch["candidates"]:
                all_candidates.extend(batch["candidates"])

            if "warnings" in batch and batch["warnings"]:
                all_warnings.extend(batch["warnings"])

        if not all_candidates:
            st.warning("⚠ No candidates found in any batch.")
        else:
            df = pd.DataFrame(all_candidates)

            df['score'] = pd.to_numeric(df['score'], errors='coerce')
            df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
            df["Rank"] = df.index + 1

            # ✅ Keep full dataframe with all columns
            full_columns = [
                "Rank", "name", "score", "fit_indicator",
                "top_strength_1", "top_strength_2",
                "primary_gap_1", "primary_gap_2",
                "skill_match", "experience", "education", "culture_fit", "keywords",
                "email", "fit_summary"
            ]
            df = df[full_columns]

            # ✅ Prepare table view (hide second strengths/gaps & fit summary)
            table_df = df[[
                "Rank", "name", "score", "fit_indicator",
                "top_strength_1", "primary_gap_1", "email"
            ]]
            table_df.columns = [
                "Rank", "Candidate", "Score", "Fit",
                "Top Strength", "Primary Gap", "Email"
            ]

            st.markdown("## 📊 Final Sorted Ranking Table")
            st.dataframe(table_df, use_container_width=True)

            # ✅ Candidate Fit Summaries
            st.markdown("---")
            st.markdown("## 📑 Candidate Fit Summaries")

            for _, row in df.iterrows():
                st.markdown(f"### 🔍 {row['name']} ({row['fit_indicator']}) - Score: {row['score']}")

                st.markdown(f"Fit Summary: {row.get('fit_summary', '')}")

                st.markdown("Component Scores:")
                st.markdown(f"""
                | Skill Match | Experience | Education | Culture Fit | Keywords |
                |--------------|------------|-----------|-------------|----------|
                | {row.get('skill_match', '')} | {row.get('experience', '')} | {row.get('education', '')} | {row.get('culture_fit', '')} | {row.get('keywords', '')} |
                """)

                st.markdown("Top Strengths:")
                st.markdown(f"""
                1. {row.get('top_strength_1', '')}  
                2. {row.get('top_strength_2', '')}
                """)

                st.markdown("Primary Gaps:")
                st.markdown(f"""
                1. {row.get('primary_gap_1', '')}  
                2. {row.get('primary_gap_2', '')}
                """)

            
            # ✅ CSV Download (has table)
            csv = table_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name='final_resume_ranking.csv',
                mime='text/csv',
            )

            # 🔥 Display Warnings Again if needed
            if all_warnings:
                st.markdown("---")
                st.markdown("## ⚠ Warnings Summary")
                for warn in all_warnings:
                    st.warning(warn)


# ==== Clear All Results to start new Screening====
if st.button("🗑 Clear All Data and Start New Screening"):
    crew = ResumeReaderCrew()
    crew.clear_all_batches()

    # Delete folders
    shutil.rmtree("uploaded_resumes", ignore_errors=True)
    shutil.rmtree("batch_results", ignore_errors=True)

    # 🔄 Force component resets
    st.session_state["uploader_key"] += 1
    st.session_state["jd_key"] += 1

    # Clear text memory
    st.session_state["jd_text"] = ""

    st.success("🗑 Cleared all resumes, JD, and previous results.")

    st.rerun()