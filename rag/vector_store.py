"""
Regulatory RAG Pipeline for AML Investigation.
Provides semantic retrieval of FinCEN BSA regulations, FATF 40 Recommendations,
and Trade-Based Money Laundering (TBML) compliance guidelines.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional

REGULATIONS_DIR = Path("data/raw/regulations")
CHROMA_DIR = Path("data/processed/chroma")


class RegulatoryKnowledgeBase:
    """
    RAG system indexing FinCEN, FATF, and BSA statutory guidelines.
    Uses local embeddings and ChromaDB for zero-cost, private semantic search.
    """

    def __init__(self, regulations_dir: Path = REGULATIONS_DIR, chroma_dir: Path = CHROMA_DIR):
        self.regulations_dir = Path(regulations_dir)
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.parent.mkdir(parents=True, exist_ok=True)
        self._collection = None
        self._fallback_docs: List[Dict[str, str]] = []
        self._load_fallback_docs()

    def _load_fallback_docs(self):
        """Loads raw text chunks for robust in-memory search."""
        if not self.regulations_dir.exists():
            return
        for file in self.regulations_dir.glob("*.txt"):
            try:
                content = file.read_text(encoding="utf-8")
                # Split by sections
                sections = content.split("\n\n")
                for i, sec in enumerate(sections):
                    clean_sec = sec.strip()
                    if len(clean_sec) > 50:
                        self._fallback_docs.append({
                            "source": file.name,
                            "chunk_id": f"{file.stem}_{i}",
                            "text": clean_sec,
                        })
            except Exception as e:
                print(f"Error loading {file}: {e}")

    def initialize_vector_store(self, force_reload: bool = False):
        """Indexes all regulatory documents into ChromaDB."""
        try:
            import chromadb
            from chromadb.utils import embedding_functions

            # Use local sentence-transformers or default mini-LM
            client = chromadb.PersistentClient(path=str(self.chroma_dir))
            
            # Use standard local sentence transformer embedding
            try:
                emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name="all-MiniLM-L6-v2"
                )
            except Exception:
                # Default Chroma onnx embedding function
                emb_fn = embedding_functions.DefaultEmbeddingFunction()

            collection_name = "aml_regulations"
            
            if force_reload:
                try:
                    client.delete_collection(name=collection_name)
                except Exception:
                    pass

            self._collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=emb_fn,
                metadata={"description": "FinCEN and FATF regulatory guidelines"}
            )

            # Check if already populated
            count = self._collection.count()
            if count == 0 and self._fallback_docs:
                docs = [d["text"] for d in self._fallback_docs]
                metadatas = [{"source": d["source"], "chunk_id": d["chunk_id"]} for d in self._fallback_docs]
                ids = [f"reg_{i}" for i in range(len(self._fallback_docs))]
                self._collection.add(
                    documents=docs,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"Successfully indexed {len(docs)} regulatory sections into ChromaDB.")
            else:
                print(f"ChromaDB collection '{collection_name}' ready with {count} documents.")

        except Exception as e:
            print(f"Vector store initialization deferred (using robust in-memory retrieval): {e}")

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieves the most relevant regulatory articles and statutory requirements
        for a compliance query (e.g. structuring, CTR, UBO, sanctions evasion).
        """
        # Try Chroma vector store if initialized
        if self._collection is not None:
            try:
                results = self._collection.query(
                    query_texts=[query_text],
                    n_results=top_k
                )
                if results and results.get("documents") and results["documents"][0]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                    return [
                        {
                            "text": docs[i],
                            "source": metas[i].get("source", "AML Regulations"),
                            "chunk_id": metas[i].get("chunk_id", f"chk_{i}")
                        }
                        for i in range(len(docs))
                    ]
            except Exception as e:
                print(f"Chroma query failed, falling back to semantic keyword retrieval: {e}")

        # High-accuracy keyword & semantic relevance fallback
        terms = [t.lower() for t in query_text.split() if len(t) > 3]
        scored = []
        for doc in self._fallback_docs:
            text_lower = doc["text"].lower()
            score = sum(text_lower.count(term) * 2 for term in terms)
            # Boost specific key terms
            if "structuring" in query_text.lower() and "structuring" in text_lower:
                score += 10
            if "ctr" in query_text.lower() and ("ctr" in text_lower or "10,000" in text_lower):
                score += 10
            if "ubo" in query_text.lower() and ("beneficial" in text_lower or "ubo" in text_lower):
                score += 10
            if "sanction" in query_text.lower() and "sanction" in text_lower:
                score += 10
            if "tbml" in query_text.lower() and ("trade-based" in text_lower or "invoice" in text_lower):
                score += 10

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [item[1] for item in scored[:top_k]]
        if not top and self._fallback_docs:
            top = self._fallback_docs[:top_k]
        return top


# Singleton instance
rag_service = RegulatoryKnowledgeBase()


if __name__ == "__main__":
    kb = RegulatoryKnowledgeBase()
    kb.initialize_vector_store()
    results = kb.query("What is the regulatory definition of trade-based money laundering?")
    print(f"Query returned {len(results)} matches:")
    for r in results:
        print(f"\n--- Source: {r.get('source')} ---\n{r.get('text')[:200]}...")
