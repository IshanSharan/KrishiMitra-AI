
from pathlib import Path
import re

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from rag.embeddings import LocalEmbeddings


# ==================================
# PROJECT PATHS
# ==================================

BASE_DIR = Path(__file__).resolve().parent

DOCUMENTS_PATH = BASE_DIR / "documents"
FAISS_PATH = BASE_DIR / "faiss_index"


# ==================================
# DOCUMENT CLASSIFICATION
# ==================================

def normalize_filename(filename):

    filename = Path(filename).stem.lower()

    return re.sub(r"[^a-z0-9]", "", filename)


def classify_document(filename):

    normalized = normalize_filename(filename)

    # Assam-specific documents

    assam_documents = [
        "packageofpracticeforhorticulturalcropsofassam2025",
        "popkharif2025newrevised03062026",
        "poprabi2025newrevised03062026"
    ]

    if normalized in assam_documents:

        return {
            "region_scope": "assam",
            "state": "Assam",
            "source_type": "state_agricultural_practice"
        }

    # ICAR advisory document

    elif (
        "icar" in normalized
        and "advisories" in normalized
        and "farmers" in normalized
    ):

        return {
            "region_scope": "check_applicability",
            "state": "Multiple/Verify",
            "source_type": "icar_advisory"
        }

    # Other documents

    else:

        return {
            "region_scope": "unknown",
            "state": "Unknown",
            "source_type": "general_reference"
        }


# ==================================
# STEP 1: LOAD PDF DOCUMENTS
# ==================================

def load_documents():

    documents = []

    pdf_files = sorted(DOCUMENTS_PATH.glob("*.pdf"))

    if not pdf_files:

        raise FileNotFoundError(
            f"No PDF files found in {DOCUMENTS_PATH}"
        )

    print(f"\nFound {len(pdf_files)} PDF files.")

    for pdf_file in pdf_files:

        print(f"\nLoading: {pdf_file.name}")

        try:

            loader = PyPDFLoader(str(pdf_file))

            pages = loader.load()

            classification = classify_document(
                pdf_file.name
            )

            for page in pages:

                page.metadata["region_scope"] = (
                    classification["region_scope"]
                )

                page.metadata["state"] = (
                    classification["state"]
                )

                page.metadata["source_type"] = (
                    classification["source_type"]
                )

                page.metadata["document_name"] = (
                    pdf_file.name
                )

            documents.extend(pages)

            print(f"Loaded {len(pages)} pages.")

            print(
                "Region:",
                classification["region_scope"]
            )

            print(
                "Source type:",
                classification["source_type"]
            )

        except Exception as e:

            print(
                f"Error loading {pdf_file.name}: {e}"
            )

    if not documents:

        raise ValueError(
            "No PDF pages could be loaded."
        )

    return documents


# ==================================
# STEP 2: SPLIT DOCUMENTS
# ==================================

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    print(
        "\nTotal chunks created:",
        len(chunks)
    )

    return chunks


# ==================================
# STEP 3: CREATE FAISS DATABASE
# ==================================

def create_vector_database(chunks):

    if not chunks:

        raise ValueError(
            "No chunks available."
        )

    print("\nLoading embedding model...")

    embedding_model = LocalEmbeddings()

    print("\nCreating FAISS vector database...")

    vector_db = FAISS.from_documents(
        documents=chunks,
        embedding=embedding_model
    )

    FAISS_PATH.mkdir(
        parents=True,
        exist_ok=True
    )

    vector_db.save_local(
        str(FAISS_PATH)
    )

    print(
        "\nFAISS database created successfully!"
    )

    print(
        "Total vectors:",
        vector_db.index.ntotal
    )

    print(
        "Database location:",
        FAISS_PATH
    )

    return vector_db


# ==================================
# STEP 4: LOAD FAISS DATABASE
# ==================================

_VECTOR_DB = None


def load_vector_database():

    global _VECTOR_DB

    # Load only once and reuse.

    if _VECTOR_DB is not None:

        return _VECTOR_DB

    if not FAISS_PATH.exists():

        raise FileNotFoundError(
            "FAISS database not found. "
            "Run: python -m rag.retriever"
        )

    print("\nLoading FAISS database...")

    embedding_model = LocalEmbeddings()

    _VECTOR_DB = FAISS.load_local(
        str(FAISS_PATH),
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )

    print("FAISS database loaded successfully.")

    return _VECTOR_DB


# ==================================
# STEP 5: LOCATION FILTERING
# ==================================

def is_document_allowed(metadata, location):

    region_scope = metadata.get(
        "region_scope",
        "unknown"
    )

    location = location.lower()

    is_assam = "assam" in location

    # Assam-specific documents are only eligible
    # for farmers located in Assam.

    if region_scope == "assam":

        return is_assam

    # ICAR and unknown documents can be retrieved
    # as candidate references, but their content
    # must be checked before claiming local applicability.

    if region_scope in [
        "check_applicability",
        "unknown"
    ]:

        return True

    return False


# ==================================
# STEP 6: DUPLICATE REMOVAL
# ==================================

def remove_duplicate_chunks(documents):

    unique_documents = []

    seen = set()

    for doc in documents:

        key = (
            doc.metadata.get("document_name", ""),
            doc.metadata.get("page", ""),
            re.sub(
                r"\s+",
                " ",
                doc.page_content
            ).strip().lower()
        )

        if key in seen:

            continue

        seen.add(key)

        unique_documents.append(doc)

    return unique_documents


# ==================================
# STEP 7: LOCATION-AWARE RETRIEVAL
# ==================================

def retrieve_documents(
    question,
    location=None,
    crop=None,
    k=4
):

    vector_db = load_vector_database()

    location = location or ""

    print("\nFarmer location:", location)

    print("Farmer crop:", crop)

    # Build a focused semantic query.
    # Avoid adding unrelated terms.

    search_query = f"""
Crop: {crop or 'Not specified'}

Location: {location}

Farmer's question: {question}
"""

    # Retrieve extra candidates because some
    # may be removed by regional filtering.

    candidate_count = max(k * 5, 20)

    print("\nSearching FAISS database...")

    results = vector_db.similarity_search_with_score(
        search_query,
        k=candidate_count
    )

    relevant_documents = []

    for doc, score in results:

        metadata = doc.metadata

        # Apply location eligibility.

        if not is_document_allowed(
            metadata,
            location
        ):

            continue

        # Store FAISS distance for inspection.

        doc.metadata["retrieval_score"] = float(score)

        relevant_documents.append(doc)

    # Remove duplicate results.

    relevant_documents = remove_duplicate_chunks(
        relevant_documents
    )

    # Keep the best k results.

    relevant_documents = relevant_documents[:k]

    print(
        "\nRelevant candidate documents:",
        len(relevant_documents)
    )

    for i, doc in enumerate(
        relevant_documents,
        start=1
    ):

        metadata = doc.metadata

        print(f"\n--- Result {i} ---")

        print(
            "Source:",
            metadata.get("document_name")
        )

        print(
            "Page:",
            metadata.get("page")
        )

        print(
            "State:",
            metadata.get("state")
        )

        print(
            "Region:",
            metadata.get("region_scope")
        )

        print(
            "Source type:",
            metadata.get("source_type")
        )

        print(
            "FAISS distance:",
            round(
                metadata.get("retrieval_score", 0),
                4
            )
        )

        print(
            "Content:",
            doc.page_content[:400]
        )

    return relevant_documents


# ==================================
# MAIN EXECUTION
# ==================================

if __name__ == "__main__":

    print("\n===== KRISHIMITRA AI RAG =====")

    # Rebuild database from all PDFs.

    docs = load_documents()

    print(
        "\nTotal pages loaded:",
        len(docs)
    )

    chunks = split_documents(docs)

    create_vector_database(chunks)

    print("\n===== DATABASE READY =====")

    # Test retrieval.

    results = retrieve_documents(
        question="Which fertilizer should I use?",
        location="Patna, Bihar",
        crop="rice",
        k=4
    )

    print("\n===== RAG TEST COMPLETED =====")
