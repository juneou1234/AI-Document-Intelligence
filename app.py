import os
import tempfile

import streamlit as st

from app.document_elements import (
    extract_all_document_elements
)

from app.document_builder import (
    build_document_units
)

from app.query_decomposer import (
    decompose_query
)

from app.retriever import (
    build_document_embeddings,
    retrieve_multi_query
)

from app.context_builder import (
    build_context
)

from app.llm import (
    generate_answer
)

from app.index_store import (
    document_id_from_bytes,
    index_exists,
    load_index,
    save_index,
)


# =========================================================
# CONFIGURATION
# =========================================================

TOP_K_PER_QUERY = 3
FINAL_TOP_K = 8
MAX_CONTEXT_CHARS = 7000


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# SESSION STATE
# =========================================================

if "document_id" not in st.session_state:
    st.session_state.document_id = None

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "document_units" not in st.session_state:
    st.session_state.document_units = None

if "document_embeddings" not in st.session_state:
    st.session_state.document_embeddings = None

if "document_ready" not in st.session_state:
    st.session_state.document_ready = False


# =========================================================
# PDF PROCESSING
# =========================================================

def process_pdf(
    pdf_bytes,
    filename,
    document_id
):
    """
    Extract, structure, embed, and persist a new PDF.
    """

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(
            pdf_bytes
        )

        temp_path = temp_file.name

    try:

        # -------------------------------------------------
        # Extract document elements
        # -------------------------------------------------

        elements = (
            extract_all_document_elements(
                temp_path
            )
        )

        if not elements:

            raise ValueError(
                "No readable content was found in the PDF."
            )

        # -------------------------------------------------
        # Build semantic units
        # -------------------------------------------------

        units = (
            build_document_units(
                elements
            )
        )

        if not units:

            raise ValueError(
                "The PDF was read, but no usable "
                "semantic sections were created."
            )

        # -------------------------------------------------
        # Build embeddings
        # -------------------------------------------------

        embeddings = (
            build_document_embeddings(
                units
            )
        )

        if len(embeddings) != len(units):

            raise ValueError(
                "The number of embeddings does not match "
                "the number of semantic sections."
            )

        # -------------------------------------------------
        # Metadata
        # -------------------------------------------------

        metadata = {
            "document_id": document_id,
            "filename": filename,
            "element_count": len(elements),
            "unit_count": len(units),
            "embedding_count": len(embeddings),
        }

        # -------------------------------------------------
        # Save persistent index
        # -------------------------------------------------

        save_index(
            document_id,
            units,
            embeddings,
            metadata
        )

        return (
            units,
            embeddings,
            metadata
        )

    finally:

        if os.path.exists(
            temp_path
        ):

            os.remove(
                temp_path
            )


# =========================================================
# HEADER
# =========================================================

st.title(
    "📄 AI Document Intelligence"
)

st.write(
    "Upload one PDF and ask questions using only "
    "the information contained in that document."
)


# =========================================================
# UPLOAD
# =========================================================

st.subheader(
    "Upload a PDF"
)

uploaded_file = st.file_uploader(
    "Choose a PDF",
    type=["pdf"],
    label_visibility="collapsed"
)


# =========================================================
# HANDLE UPLOAD
# =========================================================

if uploaded_file is not None:

    file_bytes = (
        uploaded_file.getvalue()
    )

    document_id = (
        document_id_from_bytes(
            file_bytes
        )
    )

    # -----------------------------------------------------
    # Only process when a different PDF is uploaded.
    # -----------------------------------------------------

    if (
        st.session_state.document_id
        != document_id
    ):

        # Clear the previous active document.
        st.session_state.document_id = None
        st.session_state.document_name = None
        st.session_state.document_units = None
        st.session_state.document_embeddings = None
        st.session_state.document_ready = False

        try:

            # ---------------------------------------------
            # Existing index
            # ---------------------------------------------

            if index_exists(
                document_id
            ):

                with st.spinner(
                    "Loading your document..."
                ):

                    (
                        units,
                        embeddings,
                        metadata
                    ) = load_index(
                        document_id
                    )

            # ---------------------------------------------
            # New PDF
            # ---------------------------------------------

            else:

                with st.spinner(
                    "Reading and indexing your PDF..."
                ):

                    (
                        units,
                        embeddings,
                        metadata
                    ) = process_pdf(
                        file_bytes,
                        uploaded_file.name,
                        document_id
                    )

            # ---------------------------------------------
            # Store active document
            # ---------------------------------------------

            st.session_state.document_id = (
                document_id
            )

            st.session_state.document_name = (
                metadata.get(
                    "filename",
                    uploaded_file.name
                )
            )

            st.session_state.document_units = (
                units
            )

            st.session_state.document_embeddings = (
                embeddings
            )

            st.session_state.document_ready = (
                True
            )

        except Exception as error:

            st.session_state.document_ready = (
                False
            )

            st.error(
                "We could not process this PDF."
            )

            with st.expander(
                "Technical details"
            ):

                st.exception(
                    error
                )

            st.stop()


# =========================================================
# DOCUMENT STATUS
# =========================================================

if (
    st.session_state.document_ready
    and st.session_state.document_units
    is not None
):

    st.success(
        "Document ready"
    )

    st.caption(
        f"{st.session_state.document_name} · "
        f"{len(st.session_state.document_units)} "
        "semantic sections indexed."
    )

else:

    st.info(
        "Upload a PDF above to begin."
    )

    st.stop()


# =========================================================
# QUESTION
# =========================================================

st.subheader(
    "Ask a question"
)

question = st.text_area(
    "Question",
    placeholder=(
        "Example: What are the protein requirements "
        "for growing pigs?"
    ),
    height=100,
    label_visibility="collapsed"
)

ask_button = st.button(
    "Ask",
    type="primary",
    use_container_width=True
)


# =========================================================
# ASK QUESTION
# =========================================================

if ask_button:

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

        st.stop()

    # -----------------------------------------------------
    # Query decomposition + retrieval
    # -----------------------------------------------------

    with st.spinner(
        "Searching the document..."
    ):

        try:

            sub_queries = (
                decompose_query(
                    question
                )
            )

            results = (
                retrieve_multi_query(
                    question,
                    st.session_state.document_units,
                    sub_queries,
                    top_k_per_query=TOP_K_PER_QUERY,
                    final_top_k=FINAL_TOP_K,
                    document_embeddings=(
                        st.session_state.document_embeddings
                    )
                )
            )

        except Exception as error:

            st.error(
                "We could not search the document."
            )

            with st.expander(
                "Technical details"
            ):

                st.exception(
                    error
                )

            st.stop()

    if not results:

        st.warning(
            "I could not find relevant information "
            "in this document."
        )

        st.stop()

    # -----------------------------------------------------
    # Build context
    # -----------------------------------------------------

    with st.spinner(
        "Preparing the answer..."
    ):

        try:

            context = (
                build_context(
                    results,
                    st.session_state.document_units,
                    max_chars=MAX_CONTEXT_CHARS
                )
            )

        except Exception as error:

            st.error(
                "We could not prepare the document evidence."
            )

            with st.expander(
                "Technical details"
            ):

                st.exception(
                    error
                )

            st.stop()

    # -----------------------------------------------------
    # Generate answer
    # -----------------------------------------------------

    with st.spinner(
        "Generating answer..."
    ):

        try:

            answer = generate_answer(
                question,
                context
            )

        except Exception as error:

            st.error(
                "We could not generate the answer."
            )

            with st.expander(
                "Technical details"
            ):

                st.exception(
                    error
                )

            st.stop()

    # =====================================================
    # ANSWER
    # =====================================================

    st.subheader(
        "Answer"
    )

    st.write(
        answer
    )

    # =====================================================
    # SOURCES
    # =====================================================

    st.subheader(
        "Sources"
    )

    for index, result in enumerate(
        results,
        start=1
    ):

        section = result.get(
            "section"
        )

        topic = result.get(
            "topic"
        )

        source_question = result.get(
            "question"
        )

        page_start = result.get(
            "page_start"
        )

        page_end = result.get(
            "page_end"
        )

        label_parts = []

        if section:

            label_parts.append(
                section
            )

        if topic:

            label_parts.append(
                topic
            )

        label = (
            " → ".join(
                label_parts
            )
        )

        if not label:

            label = "Document source"

        with st.expander(
            f"Source {index} · {label}"
        ):

            st.caption(
                f"Pages {page_start}-{page_end}"
            )

            if source_question:

                st.write(
                    f"**Document question:** "
                    f"{source_question}"
                )

            st.write(
                result.get(
                    "text",
                    ""
                )
            )