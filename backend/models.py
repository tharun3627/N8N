from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import date


class CommunityService(BaseModel):
    """Model for a community service record"""
    id: str
    service_name: str
    category: str
    subcategory: str
    description: str
    address: str
    locality: str
    pincode: str
    city: str
    state: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    languages_supported: Optional[str] = None
    fees: Optional[str] = None
    payment_options: Optional[str] = None
    wheelchair_accessible: Optional[str] = None
    ownership: Optional[str] = None
    documents_required: Optional[str] = None
    tags: Optional[str] = None
    emergency_service: Optional[str] = None
    response_time_estimate: Optional[str] = None
    geo_lat: Optional[str] = None
    geo_lng: Optional[str] = None
    last_updated: Optional[str] = None
    notes: Optional[str] = None


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    question: str = Field(..., min_length=1, description="User's question about local services")
    location: Optional[str] = Field(None, description="User's locality/area (e.g., Adyar, T. Nagar)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "Where is the nearest hospital in Adyar?",
                "location": "Adyar"
            }
        }


class RetrievedService(BaseModel):
    """Model for retrieved service from vector database"""
    service_name: str
    category: str
    description: str
    address: str
    contact_phone: Optional[str] = None
    hours: Optional[str] = None
    similarity_score: float
    metadata: Dict


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    answer: str = Field(..., description="Chatbot's answer")
    services: List[RetrievedService] = Field(default=[], description="Retrieved service records")
    confidence: str = Field(..., description="Confidence level: high, medium, low")
    service_count: int = Field(default=0, description="Number of relevant services found")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "I found 2 hospitals in Adyar area...",
                "services": [],
                "confidence": "high",
                "service_count": 2
            }
        }


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    ollama_available: bool
    chroma_available: bool
    total_services: int
    message: str


class DataIngestionRequest(BaseModel):
    """Request model for data ingestion"""
    services: List[CommunityService] = Field(..., description="List of service records to ingest")
    
    class Config:
        json_schema_extra = {
            "example": {
                "services": [
                    {
                        "id": "tn-0001",
                        "service_name": "Adyar Primary Health Centre",
                        "category": "Healthcare",
                        "subcategory": "Clinic",
                        "description": "Primary care clinic",
                        "address": "12 Adyar Main Road",
                        "locality": "Adyar",
                        "pincode": "600020",
                        "city": "Chennai",
                        "state": "Tamil Nadu"
                    }
                ]
            }
        }