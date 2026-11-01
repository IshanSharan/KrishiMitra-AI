
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings


class LocalEmbeddings(Embeddings):

    def __init__(self):
        # Load the embedding model
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    # Convert multiple documents into embeddings
    def embed_documents(self, texts):

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        return vectors.tolist()

    # Convert a single question into embedding
    def embed_query(self, text):

        vector = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return vector.tolist()
