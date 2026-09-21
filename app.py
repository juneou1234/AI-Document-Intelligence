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
    list_indexed_documents,
    load_index,
    save_index,
)

from app.document_overview import (
    build_section_outline,
    build_suggested_questions,
    count_pages,
)

from app.pdf_limits import (
    MAX_PDF_MB,
    MAX_PDF_PAGES,
    PdfTooLargeError,
    check_pdf_can_be_indexed,
)


# =========================================================
# CONFIGURATION
# =========================================================

TOP_K_PER_QUERY = 3
FINAL_TOP_K = 8
MAX_CONTEXT_CHARS = 7000

FOLLOW_UP_HINTS = {
    "it",
    "this",
    "that",
    "those",
    "these",
    "they",
    "them",
    "same",
    "more",
    "also",
    "and",
    "what about",
    "how about",
}


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="AI Document Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# SESSION STATE
# =========================================================

def init_session_state():
    """Create session keys used by the chat UI."""

    defaults = {
        "document_id": None,
        "document_name": None,
        "document_units": None,
        "document_embeddings": None,
        "document_ready": False,
        "document_metadata": None,
        "messages": [],
        "pending_question": None,
        "rejected_document_id": None,
        "rejected_document_message": None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


init_session_state()


# =========================================================
# DOCUMENT HELPERS
# =========================================================

def reset_active_document():
    """Clear the currently loaded document and chat."""

    st.session_state.document_id = None
    st.session_state.document_name = None
    st.session_state.document_units = None
    st.session_state.document_embeddings = None
    st.session_state.document_ready = False
    st.session_state.document_metadata = None
    st.session_state.messages = []
    st.session_state.pending_question = None
    st.session_state.rejected_document_id = None
    st.session_state.rejected_document_message = None


def set_active_document(
    document_id,
    units,
    embeddings,
    metadata
):
    """Store one document as the active chat document."""

    previous_id = (
        st.session_state.document_id
    )

    st.session_state.document_id = (
        document_id
    )

    st.session_state.document_name = (
        metadata.get(
            "filename",
            "Untitled document"
        )
    )

    st.session_state.document_units = (
        units
    )

    st.session_state.document_embeddings = (
        embeddings
    )

    st.session_state.document_metadata = (
        metadata
    )

    st.session_state.document_ready = (
        True
    )

    if previous_id != document_id:

        st.session_state.messages = []
        st.session_state.pending_question = None


def process_pdf(
    pdf_bytes,
    filename,
    document_id
):
    """
    Extract, structure, embed, and persist a new PDF.
    """

    check_pdf_can_be_indexed(
        pdf_bytes,
        filename
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(
            pdf_bytes
        )

        temp_path = temp_file.name

    try:

        elements = (
            extract_all_document_elements(
                temp_path
            )
        )

        if not elements:

            raise ValueError(
                "No readable content was found in the PDF."
            )

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

        metadata = {
            "document_id": document_id,
            "filename": filename,
            "element_count": len(elements),
            "unit_count": len(units),
            "embedding_count": len(embeddings),
            "page_count": count_pages(
                units
            ),
        }

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


def activate_saved_document(
    document_id
):
    """Load a previously indexed PDF into the chat."""

    units, embeddings, metadata = load_index(
        document_id
    )

    set_active_document(
        document_id,
        units,
        embeddings,
        metadata
    )


def show_error(
    message,
    error
):
    """Show a user-facing error with optional details."""

    st.error(
        message
    )

    with st.expander(
        "Technical details"
    ):

        st.exception(
            error
        )


def last_user_question(
    messages
):
    """Return the most recent user question from chat history."""

    for message in reversed(
        messages
    ):

        if message.get(
            "role"
        ) == "user":

            return str(
                message.get(
                    "content",
                    ""
                )
            ).strip()

    return ""


def build_search_question(
    question,
    messages
):
    """
    Expand short follow-up questions using the previous
    user question so retrieval still finds the right pages.
    """

    previous = last_user_question(
        messages
    )

    if not previous:
        return question

    lowered = question.lower()

    is_short = (
        len(question.split()) <= 8
    )

    looks_like_follow_up = any(
        hint in lowered
        for hint in FOLLOW_UP_HINTS
    )

    if is_short or looks_like_follow_up:

        return (
            f"{previous} {question}"
        )

    return question


def answer_question(
    question
):
    """
    Search the active document and generate a grounded answer.
    """

    search_question = build_search_question(
        question,
        st.session_state.messages
    )

    sub_queries = (
        decompose_query(
            search_question
        )
    )

    results = (
        retrieve_multi_query(
            search_question,
            st.session_state.document_units,
            sub_queries,
            top_k_per_query=TOP_K_PER_QUERY,
            final_top_k=FINAL_TOP_K,
            document_embeddings=(
                st.session_state.document_embeddings
            )
        )
    )

    if not results:

        return (
            "I could not find relevant information "
            "in this document.",
            []
        )

    context = (
        build_context(
            results,
            st.session_state.document_units,
            max_chars=MAX_CONTEXT_CHARS
        )
    )

    answer = generate_answer(
        question,
        context,
        conversation=st.session_state.messages
    )

    return (
        answer,
        results
    )


def render_sources(
    results
):
    """Show retrieved evidence under an answer."""

    if not results:
        return

    st.caption(
        "Evidence from the document"
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
            f"[{index}] {label}"
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


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        "Documents"
    )

    uploaded_file = st.file_uploader(
        "Upload a PDF",
        type=["pdf"],
        help=(
            f"Each PDF is indexed once, then saved so "
            f"you can reopen it later. Limit: "
            f"{MAX_PDF_PAGES} pages or {MAX_PDF_MB} MB."
        )
    )

    if uploaded_file is not None:

        file_bytes = (
            uploaded_file.getvalue()
        )

        document_id = (
            document_id_from_bytes(
                file_bytes
            )
        )

        if (
            document_id
            == st.session_state.rejected_document_id
        ):

            st.error(
                st.session_state.rejected_document_message
                or "This PDF is too large to process."
            )

        elif (
            st.session_state.document_id
            != document_id
        ):

            try:

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

                else:

                    with st.spinner(
                        "Checking PDF size..."
                    ):

                        check_pdf_can_be_indexed(
                            file_bytes,
                            uploaded_file.name
                        )

                    with st.spinner(
                        "Reading and indexing your PDF. "
                        "This can take a minute the first time."
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

                st.session_state.rejected_document_id = (
                    None
                )

                st.session_state.rejected_document_message = (
                    None
                )

                set_active_document(
                    document_id,
                    units,
                    embeddings,
                    metadata
                )

                st.rerun()

            except PdfTooLargeError as error:

                st.session_state.rejected_document_id = (
                    document_id
                )

                st.session_state.rejected_document_message = (
                    str(error)
                )

                st.error(
                    str(error)
                )

            except Exception as error:

                reset_active_document()

                show_error(
                    "We could not process this PDF.",
                    error
                )

    saved_documents = (
        list_indexed_documents()
    )

    if saved_documents:

        st.subheader(
            "Library"
        )

        st.caption(
            "Open a PDF you already indexed."
        )

        for document in saved_documents:

            saved_id = document.get(
                "document_id"
            )

            filename = document.get(
                "filename",
                "Untitled document"
            )

            unit_count = document.get(
                "unit_count"
            )

            button_label = filename

            if unit_count:

                button_label = (
                    f"{filename} · {unit_count} sections"
                )

            is_active = (
                saved_id
                == st.session_state.document_id
            )

            if st.button(
                button_label,
                key=f"open_{saved_id}",
                use_container_width=True,
                type=(
                    "primary"
                    if is_active
                    else "secondary"
                ),
                disabled=is_active,
            ):

                try:

                    with st.spinner(
                        "Opening document..."
                    ):

                        activate_saved_document(
                            saved_id
                        )

                    st.rerun()

                except Exception as error:

                    show_error(
                        "We could not open that saved document.",
                        error
                    )

    if st.session_state.document_ready:

        st.divider()

        st.subheader(
            "This document"
        )

        st.write(
            f"**{st.session_state.document_name}**"
        )

        units = (
            st.session_state.document_units
            or []
        )

        metadata = (
            st.session_state.document_metadata
            or {}
        )

        page_count = metadata.get(
            "page_count"
        ) or count_pages(
            units
        )

        col_a, col_b = st.columns(
            2
        )

        col_a.metric(
            "Sections",
            len(units)
        )

        col_b.metric(
            "Pages",
            page_count or "—"
        )

        outline = build_section_outline(
            units
        )

        if outline:

            with st.expander(
                "Document outline"
            ):

                for section in outline:

                    st.markdown(
                        f"- {section}"
                    )

        suggestions = build_suggested_questions(
            units
        )

        if suggestions:

            st.caption(
                "Try a question from the document"
            )

            for index, suggestion in enumerate(
                suggestions
            ):

                if st.button(
                    suggestion,
                    key=f"suggest_{index}",
                    use_container_width=True,
                ):

                    st.session_state.pending_question = (
                        suggestion
                    )

                    st.rerun()

        if st.button(
            "Clear chat",
            use_container_width=True,
        ):

            st.session_state.messages = []
            st.session_state.pending_question = None
            st.rerun()


# =========================================================
# MAIN PAGE
# =========================================================

st.title(
    "📄 AI Document Intelligence"
)

st.write(
    "Upload a PDF, then chat with it. Answers stay grounded "
    "in the document, with the pages they came from."
)

if not st.session_state.document_ready:

    st.info(
        "Start by uploading a PDF in the sidebar, or open "
        "one from your library."
    )

    feature_one, feature_two, feature_three = st.columns(
        3
    )

    with feature_one:

        st.markdown(
            "#### Chat, not one question"
        )

        st.write(
            "Ask a first question, then follow up with "
            "“what about grower pigs?” without starting over."
        )

    with feature_two:

        st.markdown(
            "#### Saved document library"
        )

        st.write(
            "Each PDF is indexed once. Reopen it later "
            "without waiting through extraction again."
        )

    with feature_three:

        st.markdown(
            "#### Sources you can check"
        )

        st.write(
            "Every answer includes the sections and pages "
            "used as evidence."
        )

    st.stop()


st.success(
    f"Ready · {st.session_state.document_name}"
)


# =========================================================
# CHAT HISTORY
# =========================================================

if not st.session_state.messages:

    st.caption(
        "Ask anything the document can answer. "
        "Follow-up questions work too."
    )

for message in st.session_state.messages:

    with st.chat_message(
        message[
            "role"
        ]
    ):

        st.write(
            message.get(
                "content",
                ""
            )
        )

        if (
            message.get(
                "role"
            ) == "assistant"
        ):

            render_sources(
                message.get(
                    "sources",
                    []
                )
            )


# =========================================================
# NEW QUESTION
# =========================================================

chat_question = st.chat_input(
    "Ask a question about this document"
)

question = (
    st.session_state.pending_question
    or chat_question
)

if question:

    st.session_state.pending_question = None

    question = question.strip()

    if not question:

        st.warning(
            "Please enter a question."
        )

        st.stop()

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message(
        "user"
    ):

        st.write(
            question
        )

    with st.chat_message(
        "assistant"
    ):

        try:

            with st.spinner(
                "Searching the document and writing an answer..."
            ):

                answer, results = answer_question(
                    question
                )

        except Exception as error:

            show_error(
                "We could not answer that question.",
                error
            )

            st.session_state.messages.pop()
            st.stop()

        st.write(
            answer
        )

        render_sources(
            results
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": results,
            }
        )
