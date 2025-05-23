"""persistent vector memory for sandbox agents."""

from __future__ import annotations
import uuid
import chromadb
import os
import asyncio
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from typing import Dict, List, Optional
import hashlib
from sandbox import llm
from sandbox.llm import _get_semaphore  # reuse same one

_SUMMARISE_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_LARGE   = 700           # char threshold before we summarise
_MAX_LEN = 400           # truncate final doc to this many chars

def _hash(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()

async def _rate_limited(fn, *a, **kw):
    async with _get_semaphore():
        return await asyncio.to_thread(fn, *a, **kw)

class MemoryStore:
    """A persistent vector memory store for agents using Chroma with OpenAI embeddings."""

    def __init__(self, path: str = "mem_db", collection: str = "mem") -> None:
        """Initialize the memory store with a persistent Chroma client.

        Args:
            path: Directory path for persistent Chroma storage.
            collection: Name of the collection to store memories.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY missing")
        embed = OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small",
        )
        self._client = chromadb.PersistentClient(path=path)
        self._coll = self._client.get_or_create_collection(
            name=collection,
            embedding_function=embed,
        )

    async def add(self, agent: str, text: str, *, metadata: Optional[Dict] = None) -> str:
        """Add a text snippet to the memory store for a specific agent.

        Args:
            agent: Identifier for the agent storing the memory.
            text: Text content to store.
            metadata: Optional additional metadata to associate with the text.

        Returns:
            Unique ID assigned to the stored memory.
        """
        doc_id = uuid.uuid4().hex
        meta = {"agent": agent, **(metadata or {})}
        try:
            # Chroma's .add() can block on disk; delegate to thread pool
            await _rate_limited(
                self._coll.add,
                documents=[text],
                metadatas=[meta],
                ids=[doc_id],
            )
            return doc_id
        except Exception as e:
            print(f"[memory] Error adding document to store: {str(e)}")
            return doc_id  # Return ID anyway for tracking, even if add fails

    async def recall(self, agent: str, query: str, k: int = 5) -> List[str]:
        """Recall relevant text snippets for an agent based on a query.

        Args:
            agent: Identifier for the agent recalling memories.
            query: Query text to search for relevant memories.
            k: Number of top relevant memories to return.

        Returns:
            List of recalled text snippets, ordered by relevance.
        """
        try:
            res = await _rate_limited(
                self._coll.query,
                query_texts=[query],
                n_results=k,
                where={"agent": agent},
            )
            return res["documents"][0] if res["documents"] else []
        except Exception as e:
            print(f"[memory] Error recalling memories: {str(e)}")
            return []

    def contains(self, doc_hash: str) -> bool:
        """Check if a document with the given hash exists in the store.

        Args:
            doc_hash: Hash of the document to check for.

        Returns:
            Boolean indicating if the document exists.
        """
        try:
            result = self._coll.get(ids=[doc_hash], include=[])
            return bool(result.get("ids", []))
        except Exception as e:
            print(f"[memory] Error checking document existence: {str(e)}")
            return False

    async def summarise_and_add(self, agent: str, text: str):
        """
        Summarise long content (> _LARGE chars) then add.
        Skip if already stored (hash collision check).
        """
        # Validate and sanitize input
        if not text or not isinstance(text, str):
            return
        
        # Clean the text to prevent API errors
        text = self._sanitize_text(text)
        
        h = _hash(text)
        if self.contains(h):
            return
        doc = (text if len(text) <= _LARGE else
               (await self._summarise(text))[:_MAX_LEN])
        try:
            await _rate_limited(self._coll.add, documents=[doc], metadatas=[{"agent": agent}], ids=[h])
            print(f"[memory] Added summarized document for {agent}")
        except Exception as e:
            print(f"[memory] Error adding summarized document for {agent}: {str(e)}")

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to prevent API errors."""
        if not text:
            return ""
        
        # Remove null bytes and other problematic characters
        text = text.replace('\x00', '').replace('\r', ' ').replace('\n\n\n', '\n\n')
        
        # Limit length to prevent excessive API costs
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        # Ensure text is valid UTF-8
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except UnicodeError:
            text = repr(text)  # Fallback to repr if all else fails
        
        return text.strip()

    async def _summarise(self, text: str) -> str:
        """Summarize long text using OpenAI API."""
        # Sanitize input before sending to API
        text = self._sanitize_text(text)
        
        if not text:
            return "Empty content"
            
        prompt = ("Condense the following message to <=120 words, "
                  "keeping names and key facts:\n\n" + text[:4000])
        try:
            summary = await llm.chat(
                [{"role": "user", "content": prompt}],
                model=_SUMMARISE_MODEL,
                temperature=0.3,
                max_tokens=256,
            )
            return summary
        except Exception as e:
            print(f"[memory] Error summarizing text: {str(e)}")
            return text[:_MAX_LEN]  # Fallback to truncated original text