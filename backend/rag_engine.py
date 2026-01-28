"""
RAG (Retrieval-Augmented Generation) Engine for Community Services
Handles service record retrieval and semantic search - ALL TYPE ERRORS FIXED
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
import logging
import numpy as np
from typing import List, Tuple, Optional, Dict, Any, cast
from backend.config import settings
from backend.models import RetrievedService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGEngine:
    """RAG engine for community services semantic search"""
    
    def __init__(self):
        """Initialize RAG engine with ChromaDB and embedding model"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"description": "Community services knowledge base"}
            )
            
            # Initialize embedding model
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            
            logger.info("RAG Engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing RAG Engine: {e}")
            raise
    
    def check_availability(self) -> bool:
        """Check if ChromaDB is available and has data"""
        try:
            count = self.collection.count()
            logger.info(f"ChromaDB collection has {count} service records")
            return True
        except Exception as e:
            logger.error(f"ChromaDB unavailable: {e}")
            return False
    
    def retrieve_services(
        self,
        query: str,
        locality: Optional[str] = None,
        top_k: int = settings.TOP_K_RESULTS
    ) -> Tuple[List[RetrievedService], List[Dict[str, Any]]]:
        """
        Retrieve relevant service records from vector database
        
        Args:
            query: User's question about services
            locality: Optional locality filter (e.g., "Adyar")
            top_k: Number of top results to retrieve
            
        Returns:
            Tuple of (list of retrieved services, list of service dicts for LLM context)
        """
        try:
            # Generate query embedding
            query_array = self.embedding_model.encode(query)
            query_embedding = cast(List[float], np.array(query_array).tolist())
            
            # Build where filter if locality is specified
            where_filter: Optional[Dict[str, Any]] = None
            if locality:
                where_filter = {"locality": {"$eq": locality}}
            
            # Query ChromaDB
            if where_filter:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter
                )
            else:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k
                )
            
            # Process results
            retrieved_services: List[RetrievedService] = []
            services_for_llm: List[Dict[str, Any]] = []
            
            # Safely extract results with proper type checking
            documents_list = results.get('documents')
            distances_list = results.get('distances')
            metadatas_list = results.get('metadatas')
            
            documents = documents_list[0] if documents_list and len(documents_list) > 0 else []
            distances = distances_list[0] if distances_list and len(distances_list) > 0 else []
            metadatas = metadatas_list[0] if metadatas_list and len(metadatas_list) > 0 else []
            
            if documents:
                for i, doc in enumerate(documents):
                    # Get distance and convert to similarity
                    distance = float(distances[i]) if i < len(distances) else 1.0
                    similarity = 1.0 - distance
                    
                    # Only include results above similarity threshold
                    if similarity >= settings.SIMILARITY_THRESHOLD:
                        # Get metadata safely
                        metadata = metadatas[i] if i < len(metadatas) else {}
                        
                        # Ensure metadata is a dictionary
                        if not isinstance(metadata, dict):
                            metadata = {}
                        
                        # Create RetrievedService object
                        retrieved_services.append(
                            RetrievedService(
                                service_name=str(metadata.get('service_name', 'N/A')),
                                category=str(metadata.get('category', 'N/A')),
                                description=str(metadata.get('description', 'N/A')),
                                address=str(metadata.get('address', 'N/A')),
                                contact_phone=str(metadata.get('contact_phone')) if metadata.get('contact_phone') else None,
                                hours=str(metadata.get('hours')) if metadata.get('hours') else None,
                                similarity_score=round(similarity, 3),
                                metadata=dict(metadata)
                            )
                        )
                        
                        # Create service dict for LLM context
                        services_for_llm.append(dict(metadata))
                
                logger.info(f"Retrieved {len(retrieved_services)} relevant services")
            else:
                logger.warning("No services found for query")
            
            return retrieved_services, services_for_llm
            
        except Exception as e:
            logger.error(f"Error retrieving services: {e}")
            return [], []
    
    def add_services(self, services: List[Dict[str, Any]]) -> bool:
        """
        Add service records to the vector database
        
        Args:
            services: List of service dictionaries with complete fields
            
        Returns:
            True if successful, False otherwise
        """
        try:
            ids: List[str] = []
            texts: List[str] = []
            metadatas: List[Dict[str, Any]] = []
            
            for service in services:
                # Use service ID as document ID
                service_id = str(service.get('id', f"service_{self.collection.count() + len(ids) + 1}"))
                ids.append(service_id)
                
                # Create searchable text from key fields
                searchable_text = self._create_searchable_text(service)
                texts.append(searchable_text)
                
                # Store all metadata
                metadatas.append(dict(service))
            
            # Generate embeddings
            embeddings_array = self.embedding_model.encode(texts)
            embeddings_ndarray = np.array(embeddings_array, dtype=np.float32)
            
            # Add to ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings_ndarray,
                documents=texts,
                metadatas=metadatas  # type: ignore
            )
            
            logger.info(f"Added {len(services)} service records to ChromaDB")
            return True
            
        except Exception as e:
            logger.error(f"Error adding services: {e}")
            return False
    
    def _create_searchable_text(self, service: Dict[str, Any]) -> str:
        """
        Create searchable text from service record
        Combines key fields for better semantic search
        
        Args:
            service: Service dictionary
            
        Returns:
            Searchable text string
        """
        fields = [
            str(service.get('service_name', '')),
            str(service.get('category', '')),
            str(service.get('subcategory', '')),
            str(service.get('description', '')),
            str(service.get('locality', '')),
            str(service.get('tags', '')),
            str(service.get('address', '')),
        ]
        
        # Add emergency flag if applicable
        if service.get('emergency_service') == 'yes':
            fields.append('emergency service 24/7 urgent')
        
        # Filter out empty fields and join
        searchable = ' '.join([f for f in fields if f])
        return searchable
    
    def get_service_count(self) -> int:
        """Get total number of service records in database"""
        try:
            return self.collection.count()
        except Exception:
            return 0
    
    def get_services_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get services by category
        
        Args:
            category: Category name (e.g., "Healthcare")
            limit: Maximum number of results
            
        Returns:
            List of service metadata dictionaries
        """
        try:
            # Safely extract metadatas
            results = self.collection.get(
                where={"category": {"$eq": category}},
                limit=limit
            )
            
            # Extract and convert metadatas safely
            metadatas_list = results.get('metadatas')
            if metadatas_list and isinstance(metadatas_list, list):
                return [dict(m) if isinstance(m, dict) else {} for m in metadatas_list]
            return []
            
        except Exception as e:
            logger.error(f"Error getting services by category: {e}")
            return []