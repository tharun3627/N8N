import ollama
import logging
import re
from typing import Optional, List, Dict, Tuple, Any
from backend.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with Ollama LLM for community services"""
    
    # Keywords that indicate community service queries
    COMMUNITY_KEYWORDS = [
        'hospital', 'clinic', 'doctor', 'health', 'medical', 'pharmacy', 'medicine',
        'police', 'fire', 'emergency', 'municipal', 'civic', 'government', 'office',
        'electricity', 'water', 'gas', 'utility', 'bill', 'power', 'tangedco',
        'school', 'education', 'college', 'library', 'study', 'admission',
        'bus', 'metro', 'train', 'auto', 'transport', 'travel',
        'bank', 'atm', 'loan', 'account', 'financial',
        'grocery', 'market', 'shop', 'store', 'ration',
        'salon', 'barber', 'spa', 'beauty',
        'electrician', 'plumber', 'repair', 'service', 'pest',
        'legal', 'lawyer', 'court', 'advocate',
        'vet', 'veterinary', 'pet', 'animal',
        'contact', 'address', 'location', 'where', 'how', 'timings', 'hours',
        'near', 'nearby', 'closest', 'available', 'open',
        'adyar', 't nagar', 'velachery', 'besant nagar', 'chennai', 'tamil nadu'
    ]
    
    def __init__(self):
        """Initialize Ollama client"""
        self.client = ollama.Client(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Initialized Ollama client with model: {self.model}")
    
    def check_availability(self) -> bool:
        """Check if Ollama service is available"""
        try:
            self.client.list()
            logger.info("Ollama service is available")
            return True
        except Exception as e:
            logger.error(f"Ollama service unavailable: {e}")
            return False
    
    def is_community_query(self, query: str) -> Tuple[bool, str]:
        """
        Check if the query is related to community services
        
        Args:
            query: User's question
            
        Returns:
            Tuple of (is_valid, reason)
        """
        query_lower = query.lower()
        
        # Check for community service keywords
        for keyword in self.COMMUNITY_KEYWORDS:
            if keyword in query_lower:
                return True, "community_service"
        
        # Check for question patterns about services
        service_patterns = [
            r'\b(where|find|locate|show|get|need)\b.*\b(service|facility|center|office)\b',
            r'\bhow (do|can|to)\b.*\b(contact|reach|find)\b',
            r'\b(timings?|hours?|schedule)\b',
            r'\b(phone|number|email|website)\b',
            r'\b(near|nearby|closest|around)\b'
        ]
        
        for pattern in service_patterns:
            if re.search(pattern, query_lower):
                return True, "service_inquiry"
        
        # If no match, it's likely not a community service query
        return False, "off_topic"
    
    def generate_off_topic_response(self) -> str:
        """Generate response for off-topic queries"""
        return f"""I apologize, but I can only help with community service queries related to Chennai, Tamil Nadu. 

I can help you find information about:
🏥 Healthcare services (hospitals, clinics, pharmacies)
🏛️ Civic services (police, fire, municipal offices)
⚡ Utilities (electricity, water, gas)
🎓 Educational institutions
🚌 Transportation services
🏦 Banks and financial services
🛒 Local shops and markets
And many more local services!

If you need assistance with something else, please contact:
📞 Customer Care: {settings.CUSTOMER_CARE_PHONE}
📧 Email: {settings.CUSTOMER_CARE_EMAIL}
⏰ Available: {settings.CUSTOMER_CARE_HOURS}"""
    
    def generate_escalation_response(self) -> str:
        """Generate escalation response when no services found"""
        return f"""I apologize, but I couldn't find the specific information you're looking for in my current database.

For immediate assistance, please contact:

📞 **Greater Chennai Corporation Helpline**
   Phone: {settings.CUSTOMER_CARE_PHONE}
   Available: {settings.CUSTOMER_CARE_HOURS}

📧 **Email Support**
   {settings.CUSTOMER_CARE_EMAIL}

🌐 **Online Portal**
   Visit: www.chennaicorporation.gov.in

A customer care representative will be happy to assist you with your specific query."""
    
    def generate_response(
        self,
        prompt: str,
        services_context: Optional[List[Dict[str, Any]]] = None,
        user_location: Optional[str] = None,
        temperature: float = settings.TEMPERATURE,
        max_tokens: int = settings.MAX_TOKENS
    ) -> str:
        """
        Generate response from Ollama model for community services query
        
        Args:
            prompt: User's question about local services
            services_context: Retrieved service records from vector database
            user_location: User's specified location
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Generated response text
        """
        import re
        try:
            # First, check if this is a community service query
            is_valid, reason = self.is_community_query(prompt)
            
            if not is_valid:
                logger.info(f"Off-topic query detected: {reason}")
                return self.generate_off_topic_response()
            
            # Check if services were found
            if not services_context or len(services_context) == 0:
                logger.info("No services found, escalating to customer care")
                return self.generate_escalation_response()
            
            # Build the full prompt with service context
            full_prompt = self._build_community_prompt(prompt, services_context, user_location)
            
            logger.info(f"Generating response for community query, context services: {len(services_context)}")
            
            # Call Ollama API
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            # Safely extract response - handle both dict and iterator types
            if isinstance(response, dict):
                answer = str(response.get('response', '')).strip()
            else:
                # If it's an iterator, accumulate all chunks
                full_response = ""
                for chunk in response:
                    if isinstance(chunk, dict):
                        full_response += chunk.get('response', '')
                answer = full_response.strip()
            
            # Remove any HTML tags that might have been generated
            answer = re.sub(r'<[^>]+>', '', answer)
            
            logger.info(f"Generated response length: {len(answer)}")
            
            return answer
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request. Please try again or contact customer care."
    
    def _build_community_prompt(
        self, 
        question: str, 
        services_context: List[Dict[str, Any]],
        user_location: Optional[str] = None
    ) -> str:
        """Build the full prompt with instructions and service context"""
        
        context_text = self._format_services_context(services_context)
        location_info = f" in {user_location}" if user_location else ""
        
        prompt = f"""You are a helpful community helpdesk assistant for Chennai, Tamil Nadu.

CRITICAL RULES:
1. Answer ONLY in PLAIN TEXT - NO HTML, NO formatting tags, NO markdown
2. Answer based ONLY on the service information provided below
3. Be concise, friendly, and conversational
4. Include: service name, address, contact, hours, fees
5. Use simple bullet points with dashes (-) if listing multiple services
6. Do NOT include any HTML tags like <div>, <span>, <strong>, etc.

User Location{location_info}: {user_location or "Not specified"}

Available Services:
{context_text}

User Question: {question}

Provide a helpful PLAIN TEXT answer (no HTML tags):"""
        
        return prompt
        
    def _format_services_context(self, services: List[Dict[str, Any]]) -> str:
        """
        Format service records into readable text context
        
        Args:
            services: List of service dictionaries
            
        Returns:
            Formatted context string
        """
        formatted = []
        
        for i, service in enumerate(services, 1):
            service_text = f"\n{'='*60}\nSERVICE {i}\n{'='*60}"
            service_text += f"\nName: {service.get('service_name', 'N/A')}"
            service_text += f"\nCategory: {service.get('category', 'N/A')} ({service.get('subcategory', 'N/A')})"
            service_text += f"\nDescription: {service.get('description', 'N/A')}"
            service_text += f"\nAddress: {service.get('address', 'N/A')}, {service.get('locality', 'N/A')}"
            service_text += f"\nCity: {service.get('city', 'N/A')} - {service.get('pincode', 'N/A')}"
            
            if service.get('contact_phone'):
                service_text += f"\nPhone: {service['contact_phone']}"
            if service.get('contact_email'):
                service_text += f"\nEmail: {service['contact_email']}"
            if service.get('website'):
                service_text += f"\nWebsite: {service['website']}"
            if service.get('hours'):
                service_text += f"\nOperating Hours: {service['hours']}"
            if service.get('fees'):
                service_text += f"\nFees: {service['fees']}"
            if service.get('payment_options'):
                service_text += f"\nPayment Options: {service['payment_options']}"
            if service.get('wheelchair_accessible') == 'yes':
                service_text += f"\nAccessibility: Wheelchair accessible"
            if service.get('emergency_service') == 'yes':
                service_text += f"\n⚠️ EMERGENCY SERVICE AVAILABLE 24/7"
            if service.get('languages_supported'):
                service_text += f"\nLanguages: {service['languages_supported']}"
            if service.get('notes'):
                service_text += f"\nAdditional Info: {service['notes']}"
            
            formatted.append(service_text)
        
        return "\n".join(formatted)
    
    def pull_model(self) -> bool:
        """
        Pull the model if not already available
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Checking if model {self.model} is available...")
            models_response = self.client.list()
            
            # Safely extract models list
            models_list = models_response.get('models', []) if isinstance(models_response, dict) else []
            
            model_exists = any(self.model in str(model.get('name', '')) for model in models_list)
            
            if not model_exists:
                logger.info(f"Pulling model {self.model}... This may take a few minutes.")
                self.client.pull(self.model)
                logger.info(f"Successfully pulled model {self.model}")
            else:
                logger.info(f"Model {self.model} is already available")
            
            return True
            
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False