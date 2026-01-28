from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from typing import Optional

from backend.config import settings
from backend.models import (
    ChatRequest, ChatResponse, HealthResponse,
    DataIngestionRequest, RetrievedService, CommunityService
)
from backend.rag_engine import RAGEngine
from backend.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
rag_engine: Optional[RAGEngine] = None
ollama_client: Optional[OllamaClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    global rag_engine, ollama_client
    
    logger.info("Starting Community Helpdesk Chatbot API...")
    
    try:
        # Initialize RAG Engine
        rag_engine = RAGEngine()
        logger.info("✓ RAG Engine initialized")
        
        # Initialize Ollama Client
        ollama_client = OllamaClient()
        
        # Check and pull model if needed
        if not ollama_client.pull_model():
            logger.warning("⚠ Could not verify Ollama model. Please ensure Ollama is running.")
        else:
            logger.info("✓ Ollama client initialized")
        
        logger.info("=" * 70)
        logger.info("🚀 Community Helpdesk Chatbot API is ready!")
        logger.info(f"🤖 Model: {settings.OLLAMA_MODEL}")
        logger.info(f"🏘️ Total services in database: {rag_engine.get_service_count()}")
        logger.info(f"📍 Serving: {settings.DEFAULT_CITY}, {settings.DEFAULT_STATE}")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Community Helpdesk Chatbot API...")


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered community helpdesk for services",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Community Helpdesk Chatbot API for Tamil Nadu Services",
        "version": settings.API_VERSION,
        "model": settings.OLLAMA_MODEL,
        "location": f"{settings.DEFAULT_CITY}, {settings.DEFAULT_STATE}",
        "status": "running"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Verifies that all services are running
    """
    try:
        if ollama_client is None or rag_engine is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services not initialized"
            )
        
        ollama_available = ollama_client.check_availability()
        chroma_available = rag_engine.check_availability()
        total_services = rag_engine.get_service_count()
        
        if ollama_available and chroma_available:
            status_msg = "healthy"
            message = f"All services operational. {total_services} community services available."
        else:
            status_msg = "degraded"
            message = "Some services are unavailable"
        
        return HealthResponse(
            status=status_msg,
            ollama_available=ollama_available,
            chroma_available=chroma_available,
            total_services=total_services,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main chat endpoint for community service queries
    Processes user questions using RAG and returns AI-generated answers
    Enhanced with location context and query filtering
    """
    try:
        if ollama_client is None or rag_engine is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services not initialized"
            )
        
        logger.info(f"Received query: {request.question}")
        if request.location:
            logger.info(f"Location filter: {request.location}")
        
        # Step 1: Check if query is community-related
        is_valid, reason = ollama_client.is_community_query(request.question)
        
        if not is_valid:
            logger.info(f"Off-topic query rejected: {reason}")
            answer = ollama_client.generate_off_topic_response()
            return ChatResponse(
                answer=answer,
                services=[],
                confidence="low",
                service_count=0
            )
        
        # Step 2: Retrieve relevant services from vector database
        retrieved_services, services_for_llm = rag_engine.retrieve_services(
            query=request.question,
            locality=request.location,
            top_k=settings.TOP_K_RESULTS
        )
        
        # Step 3: Determine confidence level based on retrieval results
        service_count = len(retrieved_services)
        
        if service_count == 0:
            confidence = "low"
            logger.info("No relevant services found - escalating")
            answer = ollama_client.generate_escalation_response()
        else:
            if service_count >= 3 and retrieved_services[0].similarity_score > 0.7:
                confidence = "high"
            elif service_count >= 2 and retrieved_services[0].similarity_score > 0.5:
                confidence = "medium"
            else:
                confidence = "medium"
            
            # Step 4: Generate response using Ollama with location context
            answer = ollama_client.generate_response(
                prompt=request.question,
                services_context=services_for_llm,
                user_location=request.location
            )
        
        logger.info(f"Generated answer with confidence: {confidence}, services found: {service_count}")
        
        # Step 5: Return response
        return ChatResponse(
            answer=answer,
            services=retrieved_services,
            confidence=confidence,
            service_count=service_count
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing your question. Please try again."
        )


@app.post("/ingest", tags=["Admin"])
async def ingest_services(request: DataIngestionRequest):
    """
    Ingest new service records into the knowledge base
    Admin endpoint for adding/updating community services
    """
    try:
        if rag_engine is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG engine not initialized"
            )
        
        # Convert Pydantic models to dictionaries
        service_dicts = [service.model_dump() for service in request.services]
        
        success = rag_engine.add_services(service_dicts)
        
        if success:
            return {
                "message": f"Successfully ingested {len(service_dicts)} service records",
                "total_services": rag_engine.get_service_count()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to ingest services"
            )
            
    except Exception as e:
        logger.error(f"Error ingesting services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.get("/stats", tags=["Admin"])
async def get_stats():
    """Get database statistics and service breakdown"""
    try:
        if rag_engine is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="RAG engine not initialized"
            )
        
        total = rag_engine.get_service_count()
        
        # Get counts by category
        categories = ["Healthcare", "Civic", "Utilities", "Education", "Transport", 
                     "Food & Retail", "Home Services", "Personal Care", "Financial", 
                     "Legal & Govt", "Animal & Pet", "Community"]
        
        category_counts = {}
        for cat in categories:
            services = rag_engine.get_services_by_category(cat, limit=100)
            category_counts[cat] = len(services)
        
        return {
            "total_services": total,
            "model": settings.OLLAMA_MODEL,
            "location": f"{settings.DEFAULT_CITY}, {settings.DEFAULT_STATE}",
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "category_breakdown": category_counts,
            "customer_care": {
                "phone": settings.CUSTOMER_CARE_PHONE,
                "email": settings.CUSTOMER_CARE_EMAIL,
                "hours": settings.CUSTOMER_CARE_HOURS
            }
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching statistics"
        )


@app.get("/categories", tags=["Info"])
async def get_categories():
    """Get list of available service categories"""
    return {
        "categories": [
            {"name": "Healthcare", "icon": "🏥", "description": "Hospitals, Clinics, Pharmacies"},
            {"name": "Civic", "icon": "🏛️", "description": "Police, Fire, Municipal Services"},
            {"name": "Utilities", "icon": "⚡", "description": "Electricity, Water, Gas"},
            {"name": "Education", "icon": "🎓", "description": "Schools, Libraries, Coaching"},
            {"name": "Transport", "icon": "🚌", "description": "Bus, Metro, Auto Services"},
            {"name": "Food & Retail", "icon": "🛒", "description": "Grocery, Markets"},
            {"name": "Home Services", "icon": "🔧", "description": "Repairs, Maintenance"},
            {"name": "Personal Care", "icon": "💇", "description": "Salons, Spas"},
            {"name": "Financial", "icon": "🏦", "description": "Banks, ATMs"},
            {"name": "Legal & Govt", "icon": "⚖️", "description": "Legal Aid, Govt Offices"},
            {"name": "Animal & Pet", "icon": "🐾", "description": "Veterinary Services"},
            {"name": "Community", "icon": "📚", "description": "Libraries, Community Centers"}
        ]
    }


@app.get("/customer-care", tags=["Info"])
async def get_customer_care():
    """Get customer care contact information"""
    return {
        "phone": settings.CUSTOMER_CARE_PHONE,
        "email": settings.CUSTOMER_CARE_EMAIL,
        "hours": settings.CUSTOMER_CARE_HOURS,
        "website": "www.chennaicorporation.gov.in",
        "message": "For queries not handled by the chatbot, please contact our customer care team"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )