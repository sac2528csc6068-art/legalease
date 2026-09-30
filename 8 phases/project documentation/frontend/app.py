import html
from datetime import date

import requests
import streamlit as st

from utils.document_formatter import (
    format_docx,
    format_pdf,
    format_txt,
)
from utils.text_utils import format_html_preview


st.set_page_config(
    page_title="LegalEase",
    page_icon="⚖️",
    layout="wide",
)


# ---------------------------------------------------------
# Page styling
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            margin-bottom: 0;
        }

        .subtitle {
            font-size: 18px;
            color: #666;
            margin-bottom: 25px;
        }

        .section-title {
            font-size: 22px;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .legal-note {
            padding: 12px 16px;
            border-radius: 8px;
            background-color: #f5f5f5;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    '<div class="main-title">⚖️ LegalEase</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">AI-Powered Legal Document Generator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="legal-note">
        <strong>Note:</strong> LegalEase generates draft legal documents
        for review and customization. It does not provide legal advice.
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Settings")

    backend_url = st.text_input(
        "Backend API URL",
        value="http://127.0.0.1:8000",
    ).rstrip("/")

    st.divider()

    st.subheader("Branding")

    logo_file = st.file_uploader(
        "Optional logo",
        type=["png", "jpg", "jpeg"],
    )

    if logo_file:
        st.image(
            logo_file,
            caption="Selected logo",
            width=180,
        )


# ---------------------------------------------------------
# Document types
# ---------------------------------------------------------

document_types = [
    "Employment Agreement",
    "Lease Agreement",
    "Non-Disclosure Agreement",
    "Service Agreement",
    "Freelance Agreement",
    "Consulting Agreement",
    "Partnership Agreement",
    "Custom Legal Document",
]


# ---------------------------------------------------------
# Input section
# ---------------------------------------------------------

st.markdown(
    '<div class="section-title">📄 Document Details</div>',
    unsafe_allow_html=True,
)

document_type = st.selectbox(
    "Document Type",
    document_types,
)

if document_type == "Custom Legal Document":
    custom_type = st.text_input(
        "Enter custom document type",
        placeholder="Example: Software License Agreement",
    )

    if custom_type.strip():
        document_type = custom_type.strip()


parties = st.text_area(
    "Parties",
    placeholder=(
        "Example:\n"
        "Employer: ABC Technologies Pvt. Ltd.\n"
        "Employee: John Doe\n"
        "Address: Chennai, Tamil Nadu"
    ),
    height=140,
)


terms = st.text_area(
    "Terms & Conditions",
    placeholder=(
        "Enter the important terms of the agreement.\n\n"
        "Example:\n"
        "• Monthly salary: ₹50,000\n"
        "• Working hours: 9 AM to 6 PM\n"
        "• Notice period: 30 days\n"
        "• Confidentiality requirements\n"
        "• Termination conditions"
    ),
    height=220,
)


effective_date = st.date_input(
    "Effective Date",
    value=date.today(),
)


# ---------------------------------------------------------
# Generate button
# ---------------------------------------------------------

generate_clicked = st.button(
    "✨ Generate Legal Document",
    type="primary",
    use_container_width=True,
)


if generate_clicked:

    if not parties.strip():
        st.error("Please enter the parties involved.")

    elif not terms.strip():
        st.error("Please enter the terms and conditions.")

    else:

        payload = {
            "document_type": document_type,
            "parties": parties.strip(),
            "terms": terms.strip(),
            "effective_date": effective_date.isoformat(),
        }

        with st.spinner("Generating your legal document..."):

            try:
                response = requests.post(
                    f"{backend_url}/api/generate",
                    json=payload,
                    timeout=180,
                )

                if response.status_code == 200:

                    data = response.json()

                    st.session_state["document_content"] = data["content"]
                    st.session_state["document_type"] = data[
                        "document_type"
                    ]
                    st.session_state["effective_date"] = data[
                        "effective_date"
                    ]
                    st.session_state["terms"] = terms

                    st.success(
                        "Legal document generated successfully."
                    )

                else:

                    try:
                        error_data = response.json()
                        error_message = error_data.get(
                            "detail",
                            "Unknown backend error.",
                        )
                    except Exception:
                        error_message = response.text

                    st.error(
                        f"Backend error ({response.status_code}): "
                        f"{error_message}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "Could not connect to the FastAPI backend. "
                    "Make sure the backend is running at "
                    f"{backend_url}."
                )

            except requests.exceptions.Timeout:

                st.error(
                    "The request timed out. "
                    "The AI model may still be processing the document."
                )

            except Exception as exc:

                st.error(
                    f"Unexpected error: {exc}"
                )


# ---------------------------------------------------------
# Generated document section
# ---------------------------------------------------------

if "document_content" in st.session_state:

    st.divider()

    st.markdown(
        '<div class="section-title">📝 Generated Document</div>',
        unsafe_allow_html=True,
    )

    edited_content = st.text_area(
        "Edit your document",
        value=st.session_state["document_content"],
        height=600,
        key="editable_document",
    )

    st.session_state["document_content"] = edited_content

    # -----------------------------------------------------
    # Preview
    # -----------------------------------------------------

    st.subheader("👁️ Preview")

    preview_html = format_html_preview(
        edited_content
    )

    st.components.v1.html(
        preview_html,
        height=700,
        scrolling=True,
    )

    # -----------------------------------------------------
    # Downloads
    # -----------------------------------------------------



    document_title = st.session_state.get(
        "document_type",
        "LegalEase Document",
    )

    document_date = st.session_state.get(
        "effective_date",
        effective_date.isoformat(),
    )

    document_terms = st.session_state.get(
        "terms",
        "",
    )

    logo_bytes = (
        logo_file.getvalue()
        if logo_file is not None
        else None
    )

        # ============================================================
    # DOWNLOAD SECTION
    # ============================================================

    st.markdown("## ⬇ Download")

    download_col1, download_col2, download_col3 = st.columns(3)

    # ------------------------------------------------------------
    # TXT DOWNLOAD
    # ------------------------------------------------------------

    with download_col1:
        try:
            txt_bytes = format_txt(
                content=edited_content,
                title=document_title,
                effective_date=document_date,
            )

            st.download_button(
                label="📄 Download TXT",
                data=txt_bytes,
                file_name="legalease_document.txt",
                mime="text/plain",
                use_container_width=True,
            )

        except Exception as e:
            st.error(
                f"TXT export unavailable: {e}"
            )

    # ------------------------------------------------------------
    # DOCX DOWNLOAD
    # ------------------------------------------------------------

    with download_col2:
        try:
            docx_bytes = format_docx(
                content=edited_content,
                title=document_title,
                effective_date=document_date,
            )

            st.download_button(
                label="📝 Download DOCX",
                data=docx_bytes,
                file_name="legalease_document.docx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                use_container_width=True,
            )

        except Exception as e:
            st.error(
                f"DOCX export unavailable: {e}"
            )

    # ------------------------------------------------------------
    # PDF DOWNLOAD
    # ------------------------------------------------------------

    with download_col3:
        try:
            pdf_bytes = format_pdf(
                content=edited_content,
                title=document_title,
                effective_date=document_date,
            )

            st.download_button(
                label="📕 Download PDF",
                data=pdf_bytes,
                file_name="legalease_document.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        except Exception as e:
            st.error(
                f"PDF export unavailable: {e}"
            )
