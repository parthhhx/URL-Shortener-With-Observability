from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
import time
import sys

def wait_for_elasticsearch(es, timeout=30):
    """Wait for Elasticsearch to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            if es.ping():
                return True
            print("Waiting for Elasticsearch to become available...")
        except Exception as e:
            print(f"Connection failed: {e}")
        time.sleep(5)
    return False

def setup_elasticsearch():
    """Setup and verify Elasticsearch connection"""
    # Load environment variables
    load_dotenv()

    # Get Elasticsearch credentials
    es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    es_user = os.getenv('ELASTICSEARCH_USER', 'elastic')
    es_password = os.getenv('ELASTICSEARCH_PASSWORD', '')

    print(f"\nTrying to connect to Elasticsearch at {es_url}")
    
    # Initialize Elasticsearch client
    es = Elasticsearch(
        es_url,
        basic_auth=(es_user, es_password),
        verify_certs=False
    )

    # Wait for Elasticsearch to become available
    if not wait_for_elasticsearch(es):
        print("Error: Could not connect to Elasticsearch")
        sys.exit(1)

    print("\nSuccessfully connected to Elasticsearch!")
    
    # Print cluster information
    info = es.info()
    print(f"\nCluster Name: {info['cluster_name']}")
    print(f"Elasticsearch Version: {info['version']['number']}")

    # Create index if it doesn't exist
    index_name = 'url_shortener_logs'
    if not es.indices.exists(index=index_name):
        mapping = {
            "mappings": {
                "properties": {
                    "short_url": {"type": "keyword"},
                    "long_url": {"type": "keyword"},
                    "ip_address": {"type": "ip"},
                    "user_agent": {"type": "text"},
                    "timestamp": {"type": "date"},
                    "request_duration": {"type": "float"},
                    "status_code": {"type": "integer"},
                    "request_method": {"type": "keyword"},
                    "request_path": {"type": "keyword"},
                    "referrer": {"type": "keyword"},
                    "country": {"type": "keyword"},
                    "city": {"type": "keyword"}
                }
            }
        }
        es.indices.create(index=index_name, body=mapping)
        print(f"\nCreated index: {index_name}")
    else:
        print(f"\nIndex {index_name} already exists")

    # Test index
    test_doc = {
        "timestamp": "2024-02-20T12:00:00",
        "message": "Test document"
    }
    try:
        es.index(index=index_name, document=test_doc)
        print("\nSuccessfully indexed test document")
    except Exception as e:
        print(f"\nError indexing test document: {e}")

if __name__ == "__main__":
    setup_elasticsearch() 