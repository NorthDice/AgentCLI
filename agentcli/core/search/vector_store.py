"""Module for vector storage using ChromaDB."""

import os
import logging
from typing import List, Dict, Any, Optional

# Import ChromaDB with error handling
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from agentcli.core.search.interfaces import VectorStore

logger = logging.getLogger(__name__)

class ChromaVectorStore(VectorStore):
    """Vector store implementation using ChromaDB."""
    
    def __init__(self, index_dir: str = ".agentcli/search_index", collection_name: str = "code_chunks"):
        """Initialize the vector store.
        
        Args:
            index_dir: Directory to store the ChromaDB index.
            collection_name: Name of the collection to use.
        """
        self.index_dir = index_dir
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    def _initialize(self):
        """Initialize the ChromaDB client and collection."""
        if not CHROMADB_AVAILABLE:
            logger.error("chromadb package not installed.")
            raise ImportError("Please install chromadb: pip install chromadb")
            
        if self.client is None:
            try:
                # Create directory if it doesn't exist
                os.makedirs(self.index_dir, exist_ok=True)
                
                # Initialize client
                self.client = chromadb.PersistentClient(path=self.index_dir)
            except Exception as e:
                logger.error(f"Error initializing ChromaDB client: {str(e)}")
                raise
        
        if self.collection is None:
            try:
                # Get or create collection
                try:
                    self.collection = self.client.get_collection(name=self.collection_name)
                    logger.info(f"Using existing collection '{self.collection_name}'")
                except Exception:
                    self.collection = self.client.create_collection(name=self.collection_name)
                    logger.info(f"Created new collection '{self.collection_name}'")
            except Exception as e:
                logger.error(f"Error with ChromaDB collection: {str(e)}")
                raise
    
    def add(self, items: List[Dict[str, Any]]) -> None:
        """Add items to the vector store.
        
        Args:
            items: List of dictionaries containing content, metadata, and embeddings.
        """
        if not items:
            return
            
        self._initialize()
        
        try:
            # Prepare data for ChromaDB format
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for item in items:
                # Create a unique ID from file path and line numbers
                metadata = item["metadata"]
                item_id = f"{metadata.get('file_path', 'unknown')}:{metadata.get('start_line', 0)}:{metadata.get('end_line', 0)}"
                
                ids.append(item_id)
                documents.append(item["content"])
                embeddings.append(item["embedding"])
                metadatas.append(metadata)
            
            # Add to collection in batches (ChromaDB has limits on batch size)
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                self.collection.add(
                    ids=ids[i:i+batch_size],
                    documents=[doc for doc in documents[i:i+batch_size]],
                    embeddings=[emb for emb in embeddings[i:i+batch_size]],
                    metadatas=metadatas[i:i+batch_size]
                )
            
            logger.info(f"Added {len(items)} items to ChromaDB collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error adding items to ChromaDB: {str(e)}")
    
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in the store.
        
        Args:
            query_embedding: Query embedding vector.
            top_k: Number of top results to return.
            
        Returns:
            List of dictionaries containing found items with relevance scores.
        """
        if not query_embedding:
            return []
            
        self._initialize()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            
            if results["ids"] and len(results["ids"][0]) > 0:
                for i, (doc_id, document, metadata, distance) in enumerate(zip(
                    results["ids"][0], 
                    results["documents"][0], 
                    results["metadatas"][0], 
                    results["distances"][0]
                )):
                    # Convert distance to relevance score (higher is better)
                    relevance = 1.0 - distance
                    
                    formatted_results.append({
                        "content": document,
                        "metadata": metadata,
                        "relevance": relevance
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching in ChromaDB: {str(e)}")
            return []
    
    def delete(self, item_ids: List[str]) -> None:
        """Delete items from the store.
        
        Args:
            item_ids: List of item IDs to delete.
        """
        if not item_ids:
            return
            
        self._initialize()
        
        try:
            self.collection.delete(ids=item_ids)
            logger.info(f"Deleted {len(item_ids)} items from ChromaDB collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error deleting items from ChromaDB: {str(e)}")
    
    def clear(self) -> None:
        """Clear the entire store."""
        self._initialize()
        
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(self.collection_name)
            logger.info(f"Cleared ChromaDB collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error clearing ChromaDB collection: {str(e)}")
    
    def count(self) -> int:
        """Get the number of items in the store.
        
        Returns:
            Number of items in the store.
        """
        self._initialize()
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Error getting count from ChromaDB: {str(e)}")
            return 0
