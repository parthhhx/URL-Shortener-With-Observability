#!/bin/bash

# Wait for Elasticsearch to be ready
echo "Waiting for Elasticsearch..."
until curl -s -u elastic:87654321 http://localhost:9200/_cluster/health > /dev/null; do
    sleep 5
done

# Create the Kibana service account token
echo "Creating Kibana service account token..."
TOKEN=$(curl -s -X POST -u elastic:87654321 \
    "http://localhost:9200/_security/service/elastic/kibana/credential/token/kibana1" \
    -H "Content-Type: application/json" | grep -o '"value":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    # Create or update .env file with the token
    echo "KIBANA_TOKEN=$TOKEN" > .env
    echo "Token created and saved to .env file"
    echo "Now restart Kibana with: docker-compose up -d kibana"
else
    echo "Failed to create token"
    exit 1
fi 