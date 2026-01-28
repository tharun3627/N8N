from backend.rag_engine import RAGEngine

rag = RAGEngine()
print(f"Total services: {rag.get_service_count()}")

services, context = rag.retrieve_services("hospital", top_k=5)
print(f"\nFound {len(services)} services for 'hospital'")

for s in services:
    print(f"- {s.service_name} (score: {s.similarity_score})")

services2, context2 = rag.retrieve_services("Adyar", top_k=5)
print(f"\nFound {len(services2)} services for 'Adyar'")

for s in services2[:3]:  # Show first 3
    print(f"- {s.service_name} (score: {s.similarity_score})")