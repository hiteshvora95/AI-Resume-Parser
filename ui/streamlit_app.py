import httpx
import streamlit as st
from config.variables import API_BASE_URL

st.set_page_config(
    page_title="Resume Parser",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Resume Parser")
st.markdown("Upload a **PDF** or **DOCX** resume to extract structured information using AI.")
st.divider()


def parse_resume(data: dict):
    """Parse extracted resume data as formatted Streamlit components."""

    # Contact Information
    contact = data.get("contact") or {}
    if any(contact.values()):
        st.subheader("📋 Contact Information")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Name", contact.get("name") or "—")
        c2.metric("Email", contact.get("email") or "—")
        c3.metric("Phone", contact.get("phone") or "—")
        c4.metric("Location", contact.get("location") or "—")
        st.divider()

    # Professional Summary
    if data.get("summary"):
        st.subheader("📝 Professional Summary")
        st.info(data["summary"])
        st.divider()

    # Work Experience
    work_experience = data.get("work_experience") or []
    if work_experience:
        st.subheader("💼 Work Experience")
        for job in work_experience:
            start = job.get("start_date") or ""
            end = job.get("end_date") or ""
            duration = f"{start} – {end}".strip(" –")
            header = f"**{job.get('role', 'Role')}** at {job.get('company', 'Company')}"
            if duration:
                header += f"  |  {duration}"
            with st.expander(header):
                responsibilities = job.get("responsibilities") or []
                if responsibilities:
                    for r in responsibilities:
                        st.markdown(f"- {r}")
                else:
                    st.markdown("_No responsibilities listed_")
        st.divider()

    # Education
    education = data.get("education") or []
    if education:
        st.subheader("🎓 Education")
        for edu in education:
            year = f" ({edu['year']})" if edu.get("year") else ""
            st.markdown(
                f"**{edu.get('degree', 'Degree')}** — "
                f"{edu.get('institution', 'Institution')}{year}"
            )
        st.divider()

    # Skills
    skills = data.get("skills") or {}
    technical = skills.get("technical") or []
    soft = skills.get("soft") or []
    if technical or soft:
        st.subheader("🛠 Skills")
        sk1, sk2 = st.columns(2)
        with sk1:
            st.markdown("**Technical Skills**")
            st.markdown(", ".join(technical) if technical else "_None listed_")
        with sk2:
            st.markdown("**Soft Skills**")
            st.markdown(", ".join(soft) if soft else "_None listed_")
        st.divider()

    # Certifications
    certifications = data.get("certifications") or []
    if certifications:
        st.subheader("📜 Certifications")
        for cert in certifications:
            issuer = f" — {cert['issuer']}" if cert.get("issuer") else ""
            year = f" ({cert['year']})" if cert.get("year") else ""
            st.markdown(f"- **{cert['name']}**{issuer}{year}")


tab_upload, tab_search = st.tabs(["Upload Resume", "Search by Document ID"])

with tab_upload:
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx"])

    if uploaded_file:
        col1, col2 = st.columns([1, 5])
        with col1:
            extract = st.button("Extract Resume", type="primary", use_container_width=True)

        if extract:
            with st.spinner("Extracting resume information..."):
                try:
                    response = httpx.post(
                        f"{API_BASE_URL}/api/upload",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=60,
                    )
                except httpx.ConnectError:
                    st.error("Cannot reach the API server. Make sure the backend is running.")
                    st.stop()
                except httpx.TimeoutException:
                    st.error("Request timed out. Please try again.")
                    st.stop()

            if response.status_code == 200:
                result = response.json()
                doc_id = result["document_id"]
                st.success(f"Extracted successfully!  |  Document ID: `{doc_id}`")
                st.divider()
                parse_resume(result["data"])
            else:
                try:
                    detail = response.json().get("detail") or response.json().get("error") or "Unknown error"
                except Exception:
                    detail = response.text or "Unknown error"

                if response.status_code == 400:
                    st.error(f"Upload error: {detail}")
                elif response.status_code == 429:
                    st.warning(f"Rate limit: {detail}")
                elif response.status_code == 503:
                    st.error(f"Service unavailable: {detail}")
                else:
                    st.error(f"Error ({response.status_code}): {detail}")


with tab_search:
    doc_id_input = st.text_input("Enter Document ID", placeholder="e.g. 3f2a1b4c-...")

    col1, col2 = st.columns([1, 5])
    with col1:
        search = st.button("Search", type="primary", use_container_width=True)

    if search:
        if not doc_id_input.strip():
            st.warning("Please enter a Document ID.")
        else:
            with st.spinner("Fetching resume..."):
                try:
                    response = httpx.get(
                        f"{API_BASE_URL}/api/resume/{doc_id_input.strip()}",
                        timeout=60,
                    )
                except httpx.ConnectError:
                    st.error("Cannot reach the API server. Make sure the backend is running.")
                    st.stop()
                except httpx.TimeoutException:
                    st.error("Request timed out. Please try again.")
                    st.stop()

            if response.status_code == 200:
                result = response.json()
                st.success(f"Resume found  |  Document ID: `{result.get('document_id')}`")
                st.divider()
                parse_resume(result["data"])
            elif response.status_code == 404:
                st.error(f"No resume found with ID: `{doc_id_input.strip()}`")
            else:
                try:
                    detail = response.json().get("detail") or "Unknown error"
                except Exception:
                    detail = response.text or "Unknown error"
                st.error(f"Error ({response.status_code}): {detail}")
