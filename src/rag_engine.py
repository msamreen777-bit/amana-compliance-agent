import os
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import chromadb
from chromadb.utils import embedding_functions
from src.config import settings

class HybridComplianceRetriever:
    """
    Hybrid RAG Engine combining:
    - Dense Search: ChromaDB with Local Default Embeddings (ONNX/MiniLM - 100% Local & Free)
    - Sparse Search: BM25 for precise regulatory clause matching
    - Fusion: Reciprocal Rank Fusion (RRF)
    """
    def __init__(self, collection_name: str = "uae_compliance_rules"):
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Free local embeddings running directly on your CPU (no OpenAI credit needed!)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )
        self.documents: List[str] = []
        self.doc_ids: List[str] = []
        self.bm25: BM25Okapi = None

    def index_document(self, file_path: str):
        """Chunks and indexes regulatory documents into ChromaDB and BM25."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Split by regulatory rule sections
        import re
        raw_chunks = re.split(r'\n(?=## \d+\. )', text)
        self.documents = []
        self.doc_ids = []

        for i, chunk in enumerate(raw_chunks):
            if chunk.strip():
                clean_chunk = "## " + chunk if not chunk.startswith("#") else chunk
                doc_id = f"rule_chunk_{i}"
                self.documents.append(clean_chunk.strip())
                self.doc_ids.append(doc_id)

        # 1. Index in ChromaDB (Dense)
        self.collection.upsert(
            documents=self.documents,
            ids=self.doc_ids,
            metadatas=[{"source": os.path.basename(file_path)} for _ in self.documents]
        )

        # 2. Tokenize and index in BM25 (Sparse)
        tokenized_corpus = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)
        print(f"Successfully indexed {len(self.documents)} regulatory chunks into ChromaDB & BM25.")

    def hybrid_search(self, query: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """Executes dense + sparse search and combines results via Reciprocal Rank Fusion."""
        if not self.bm25 or not self.documents:
            raise ValueError("Corpus has not been indexed yet. Call index_document() first.")

        # 1. Sparse Search (BM25)
        query_tokens = query.lower().split()
        bm25_scores = self.bm25.get_scores(query_tokens)
        bm25_ranked = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)

        # 2. Dense Search (ChromaDB)
        chroma_res = self.collection.query(
            query_texts=[query],
            n_results=min(top_k * 2, len(self.documents))
        )
        chroma_ids = chroma_res["ids"][0]

        # 3. Reciprocal Rank Fusion (RRF, constant k=60)
        rrf_scores: Dict[str, float] = {}
        k = 60

        for rank, (idx, _) in enumerate(bm25_ranked[:5]):
            doc_id = self.doc_ids[idx]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

        for rank, doc_id in enumerate(chroma_ids):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

        # Sort combined results by highest score
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for doc_id, score in sorted_docs[:top_k]:
            idx = self.doc_ids.index(doc_id)
            results.append({
                "doc_id": doc_id,
                "score": round(score, 4),
                "content": self.documents[idx]
            })
        return results

if __name__ == "__main__":
    retriever = HybridComplianceRetriever()
    retriever.index_document("data/regulatory_docs/uae_aml_guidelines.md")
    
    test_query = "What are the rules regarding Politically Exposed Persons (PEPs) in DIFC?"
    matches = retriever.hybrid_search(test_query, top_k=1)
    
    print("\n--- Test Hybrid Search Output ---")
    for m in matches:
        print(f"Doc ID: {m['doc_id']} | Fusion Score: {m['score']}")
        print(f"Content:\n{m['content']}")
