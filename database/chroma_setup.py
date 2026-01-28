"""
ChromaDB Setup and Initialization Script
Loads community services data from JSON and populates the vector database
"""
import json
import logging
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.rag_engine import RAGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_community_services(json_file: str = "database/community_services.json") -> list:
    """
    Load community services data from JSON file
    
    Args:
        json_file: Path to the JSON data file
        
    Returns:
        List of service dictionaries
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        services = data.get('services', [])
        logger.info(f"Loaded {len(services)} service records from {json_file}")
        return services
        
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON file: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error loading data: {e}")
        return []


def initialize_database():
    """
    Initialize ChromaDB with community services data
    """
    try:
        logger.info("=" * 80)
        logger.info("Community Services Database Initialization")
        logger.info("=" * 80)
        
        # Initialize RAG Engine
        logger.info("\nStep 1: Initializing RAG Engine...")
        rag_engine = RAGEngine()
        
        # Check current service count
        current_count = rag_engine.get_service_count()
        logger.info(f"Current services in database: {current_count}")
        
        if current_count > 0:
            user_input = input(f"\n⚠️  Database already contains {current_count} services. "
                             "Do you want to add more services? (yes/no): ").strip().lower()
            if user_input != 'yes':
                logger.info("Initialization cancelled by user.")
                return
        
        # Load data from JSON
        logger.info("\nStep 2: Loading community services from JSON...")
        services = load_community_services()
        
        if not services:
            logger.error("No services to load. Exiting.")
            return
        
        logger.info(f"Found {len(services)} service records to process")
        
        # Display sample service
        logger.info("\n" + "-" * 80)
        logger.info("Sample Service Record:")
        logger.info(f"  ID: {services[0]['id']}")
        logger.info(f"  Name: {services[0]['service_name']}")
        logger.info(f"  Category: {services[0]['category']} - {services[0]['subcategory']}")
        logger.info(f"  Locality: {services[0]['locality']}")
        logger.info(f"  Description: {services[0]['description'][:80]}...")
        logger.info("-" * 80)
        
        # Add services to ChromaDB
        logger.info("\nStep 3: Adding services to ChromaDB...")
        logger.info("Generating embeddings... This may take a few moments...")
        
        success = rag_engine.add_services(services)
        
        if success:
            final_count = rag_engine.get_service_count()
            logger.info("\n" + "=" * 80)
            logger.info("✅ Database initialization completed successfully!")
            logger.info(f"📊 Total services in database: {final_count}")
            logger.info(f"🏘️ Collection name: {rag_engine.collection.name}")
            
            # Show category breakdown
            logger.info("\n📋 Services by Category:")
            categories = {}
            for service in services:
                cat = service['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for cat, count in sorted(categories.items()):
                logger.info(f"  • {cat}: {count} services")
            
            logger.info("=" * 80)
        else:
            logger.error("\n❌ Failed to add services to database")
        
    except Exception as e:
        logger.error(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()


def view_database_stats():
    """
    View current database statistics
    """
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Community Services Database Statistics")
        logger.info("=" * 80)
        
        rag_engine = RAGEngine()
        count = rag_engine.get_service_count()
        
        logger.info(f"\n📊 Total services: {count}")
        logger.info(f"🗂️  Collection name: {rag_engine.collection.name}")
        
        # Get category breakdown
        categories = ["Healthcare", "Civic", "Utilities", "Education", "Transport", 
                     "Food & Retail", "Home Services", "Personal Care", "Financial", 
                     "Legal & Govt", "Animal & Pet", "Community"]
        
        logger.info("\n📋 Services by Category:")
        for cat in categories:
            services = rag_engine.get_services_by_category(cat, limit=100)
            if services:
                logger.info(f"  • {cat}: {len(services)} services")
        
        # Try to get a sample service
        if count > 0:
            results = rag_engine.collection.get(limit=1)
            if results and results['documents'] and results['metadatas']:
                logger.info("\n📄 Sample Service Record:")
                metadata = results['metadatas'][0]
                logger.info(f"  ID: {results['ids'][0]}")
                logger.info(f"  Name: {metadata.get('service_name', 'N/A')}")
                logger.info(f"  Category: {metadata.get('category', 'N/A')}")
                logger.info(f"  Locality: {metadata.get('locality', 'N/A')}")
                logger.info(f"  Address: {metadata.get('address', 'N/A')}")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error viewing stats: {e}")


def search_services():
    """
    Interactive service search
    """
    try:
        logger.info("\n" + "=" * 80)
        logger.info("Service Search")
        logger.info("=" * 80)
        
        rag_engine = RAGEngine()
        
        query = input("\nEnter your search query (e.g., 'hospital in Adyar'): ").strip()
        
        if not query:
            logger.info("No query entered. Exiting search.")
            return
        
        logger.info(f"\n🔍 Searching for: {query}")
        
        retrieved_services, services_for_llm = rag_engine.retrieve_services(query, top_k=5)
        
        if retrieved_services:
            logger.info(f"\n✅ Found {len(retrieved_services)} matching services:\n")
            
            for i, service in enumerate(retrieved_services, 1):
                logger.info(f"--- Result {i} (Similarity: {service.similarity_score:.3f}) ---")
                logger.info(f"Name: {service.service_name}")
                logger.info(f"Category: {service.category}")
                logger.info(f"Address: {service.address}")
                if service.contact_phone:
                    logger.info(f"Phone: {service.contact_phone}")
                if service.hours:
                    logger.info(f"Hours: {service.hours}")
                logger.info(f"Description: {service.description}\n")
        else:
            logger.info("\n❌ No matching services found.")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during search: {e}")


if __name__ == "__main__":
    print("\n🏘️ Community Helpdesk Chatbot - Database Setup\n")
    print("Options:")
    print("1. Initialize/Add services to database")
    print("2. View database statistics")
    print("3. Search services")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        initialize_database()
    elif choice == "2":
        view_database_stats()
    elif choice == "3":
        search_services()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice. Exiting...")