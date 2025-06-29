from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv
import time
import sys
import requests
from requests.auth import HTTPBasicAuth

def wait_for_elasticsearch(url, username, password, timeout=300):
    """Wait for Elasticsearch to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                f"{url}/_cluster/health",
                auth=HTTPBasicAuth(username, password),
                verify=False
            )
            if response.status_code == 200:
                return True
            print("Waiting for Elasticsearch to become available...")
        except Exception as e:
            print(f"Connection failed: {e}")
        time.sleep(5)
    return False

def create_kibana_token():
    """Create a service account token for Kibana"""
    # Load environment variables
    load_dotenv()

    # Get Elasticsearch credentials
    es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    es_user = os.getenv('ELASTICSEARCH_USER', 'elastic')
    es_password = os.getenv('ELASTICSEARCH_PASSWORD', '87654321')

    print(f"\nTrying to connect to Elasticsearch at {es_url}")
    
    # Wait for Elasticsearch
    if not wait_for_elasticsearch(es_url, es_user, es_password):
        print("Error: Could not connect to Elasticsearch")
        sys.exit(1)

    # Create service account token
    token_url = f"{es_url}/_security/service/elastic/kibana/credential/token/kibana_token"
    try:
        response = requests.post(
            token_url,
            auth=HTTPBasicAuth(es_user, es_password),
            verify=False
        )
        
        if response.status_code == 200:
            token = response.json()['token']['value']
            print("\nSuccessfully created Kibana service account token!")
            print("\nUpdate your docker-compose.yml with this token:")
            print(f"\nELASTICSEARCH_SERVICEACCOUNTTOKEN={token}")
        else:
            print(f"\nError creating token: {response.text}")
            sys.exit(1)

    except Exception as e:
        print(f"\nError creating token: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_kibana_token() 