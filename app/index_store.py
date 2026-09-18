import hashlib
import json
import os

import numpy as np


# =========================================================
# INDEX ROOT
# =========================================================

INDEX_ROOT = "indexes"


# =========================================================
# DOCUMENT IDENTIFIER
# =========================================================

def document_id_from_bytes(
    pdf_bytes
):
    """
    Create a stable identifier from the PDF contents.

    The same PDF produces the same ID.
    A changed PDF produces a different ID.
    """

    return hashlib.sha256(
        pdf_bytes
    ).hexdigest()[:16]


# =========================================================
# INDEX PATHS
# =========================================================

def get_index_directory(
    document_id
):
    """Return the directory containing one document index."""

    return os.path.join(
        INDEX_ROOT,
        document_id
    )


def get_units_path(
    document_id
):
    """Return semantic-units JSON path."""

    return os.path.join(
        get_index_directory(
            document_id
        ),
        "units.json"
    )


def get_embeddings_path(
    document_id
):
    """Return embeddings NumPy path."""

    return os.path.join(
        get_index_directory(
            document_id
        ),
        "embeddings.npy"
    )


def get_metadata_path(
    document_id
):
    """Return metadata JSON path."""

    return os.path.join(
        get_index_directory(
            document_id
        ),
        "metadata.json"
    )


# =========================================================
# SAVE INDEX
# =========================================================

def save_index(
    document_id,
    units,
    embeddings,
    metadata
):
    """
    Save a processed document index to disk.

    Files:
        units.json
        embeddings.npy
        metadata.json
    """

    directory = get_index_directory(
        document_id
    )

    os.makedirs(
        directory,
        exist_ok=True
    )

    # -----------------------------------------------------
    # Semantic units
    # -----------------------------------------------------

    with open(
        get_units_path(
            document_id
        ),
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            units,
            file,
            ensure_ascii=False,
            indent=2
        )

    # -----------------------------------------------------
    # Embeddings
    # -----------------------------------------------------

    np.save(
        get_embeddings_path(
            document_id
        ),
        np.asarray(
            embeddings
        )
    )

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------

    metadata = metadata.copy()

    metadata.setdefault(
        "document_id",
        document_id
    )

    metadata.setdefault(
        "index_version",
        1
    )

    with open(
        get_metadata_path(
            document_id
        ),
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# LOAD INDEX
# =========================================================

def load_index(
    document_id
):
    """
    Load a previously saved document index.

    Returns:
        units,
        embeddings,
        metadata

    Raises:
        FileNotFoundError if the index does not exist.
    """

    required_files = [
        get_units_path(
            document_id
        ),
        get_embeddings_path(
            document_id
        ),
        get_metadata_path(
            document_id
        ),
    ]

    for path in required_files:

        if not os.path.exists(
            path
        ):

            raise FileNotFoundError(
                f"Index file not found: {path}"
            )

    # -----------------------------------------------------
    # Units
    # -----------------------------------------------------

    with open(
        get_units_path(
            document_id
        ),
        "r",
        encoding="utf-8"
    ) as file:

        units = json.load(
            file
        )

    # -----------------------------------------------------
    # Embeddings
    # -----------------------------------------------------

    embeddings = np.load(
        get_embeddings_path(
            document_id
        )
    )

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------

    with open(
        get_metadata_path(
            document_id
        ),
        "r",
        encoding="utf-8"
    ) as file:

        metadata = json.load(
            file
        )

    return (
        units,
        embeddings,
        metadata
    )


# =========================================================
# INDEX EXISTENCE
# =========================================================

def index_exists(
    document_id
):
    """Return True if a complete index exists."""

    required_files = [
        get_units_path(
            document_id
        ),
        get_embeddings_path(
            document_id
        ),
        get_metadata_path(
            document_id
        ),
    ]

    return all(
        os.path.exists(
            path
        )
        for path in required_files
    )


# =========================================================
# LIST INDEXED DOCUMENTS
# =========================================================

def list_indexed_documents():
    """
    Return metadata for every complete document index.
    """

    documents = []

    if not os.path.isdir(
        INDEX_ROOT
    ):
        return documents

    for document_id in os.listdir(
        INDEX_ROOT
    ):

        index_directory = os.path.join(
            INDEX_ROOT,
            document_id
        )

        if not os.path.isdir(
            index_directory
        ):
            continue

        if not index_exists(
            document_id
        ):
            continue

        try:

            _, _, metadata = load_index(
                document_id
            )

            metadata = metadata.copy()

            metadata.setdefault(
                "document_id",
                document_id
            )

            documents.append(
                metadata
            )

        except Exception:
            continue

    documents.sort(
        key=lambda item:
        item.get(
            "filename",
            "Unnamed document"
        ).lower()
    )

    return documents