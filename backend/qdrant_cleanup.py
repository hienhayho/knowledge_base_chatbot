import requests
from qdrant_client import QdrantClient

def clean_qdrant_storage_http(qdrant_url):
    """Clean Qdrant storage using HTTP requests."""
    # Get all collections
    collections_response = requests.get(f"{qdrant_url}/collections")
    collections = collections_response.json()["result"]["collections"]

    # Delete each collection
    for collection in collections:
        delete_response = requests.delete(f"{qdrant_url}/collections/{collection['name']}")
        if delete_response.status_code == 200:
            print(f"Deleted collection: {collection['name']}")
        else:
            print(f"Failed to delete collection: {collection['name']}")

def clean_qdrant_storage_client(qdrant_url):
    """Clean Qdrant storage using the Qdrant client."""
    client = QdrantClient(qdrant_url)
    
    # Get all collections
    collections = client.get_collections().collections

    # Delete each collection
    for collection in collections:
        client.delete_collection(collection_name=collection.name)
        print(f"Deleted collection: {collection.name}")

if __name__ == "__main__":
    qdrant_url = "http://localhost:6333"  # Replace with your Qdrant server URL
    
    # Choose one of the methods below:
    clean_qdrant_storage_http(qdrant_url)
    # clean_qdrant_storage_client(qdrant_url)