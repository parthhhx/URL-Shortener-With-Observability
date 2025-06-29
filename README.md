# URL Shortener with Flask, MySQL, and Elasticsearch

A URL shortening service built with Flask, using MySQL for URL storage and Elasticsearch + Kibana for request logging and monitoring.

## Prerequisites

- Python 3.x
- Docker and Docker Compose
- MySQL Server
- pip (Python package installer)

## Project Structure

```
url_shortner/
├── app.py                    # Main Flask application
├── create_kibana_token.sh    # Script to create Kibana service token
├── docker-compose.yml        # Docker configuration for ELK stack
├── logs/                     # Application logs directory
├── requirements.txt          # Python dependencies
├── setup_elasticsearch.py    # Elasticsearch setup script
├── setup_kibana_token.py    # Kibana token setup script
└── templates/               
    └── index.html           # Main webpage template
```

## Setup Instructions

1. **Clone the repository and navigate to the project directory**
   ```bash
   git clone <repository-url>
   cd url_shortner
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up MySQL Database**
   - Create a new MySQL database:
     ```sql
     CREATE DATABASE url_shortener;
     ```
   - The tables will be automatically created when you run the application

5. **Start Elasticsearch and Kibana using Docker**
   ```bash
   docker-compose up -d
   ```
   Wait for a few moments for the services to start up completely.

6. **Create and run the Kibana service token script**
   ```bash
   # Make the script executable
   chmod +x create_kibana_token.sh
   
   # Run the script to create a Kibana service token
   ./create_kibana_token.sh
   ```
   This script will:
   - Create a service account token for Kibana
   - Set the token in your environment
   - Update the Docker Compose configuration
   - Restart Kibana with the new token

7. **Set up environment variables**
   Create a `.env` file in the project root with the following content:
   ```
   ELASTICSEARCH_URL=http://localhost:9200
   ELASTICSEARCH_USER=elastic
   ELASTICSEARCH_PASSWORD=87654321
   MYSQL_USER=root
   MYSQL_PASSWORD=
   MYSQL_HOST=localhost
   MYSQL_DATABASE=url_shortener
   ```
   Adjust the values according to your setup.

8. **Run the Elasticsearch setup script**
   ```bash
   python setup_elasticsearch.py
   ```
   This will create the necessary index and mappings in Elasticsearch.

9. **Start the Flask application**
   ```bash
   flask run
   ```
   The application will be available at http://localhost:5000

## Accessing Kibana and Logs

1. **Access Kibana**
   - Open http://localhost:5601 in your browser
   - Log in with the credentials from your environment variables

2. **Set up the Data View in Kibana**
   - Go to Stack Management → Data Views
   - Click "Create data view"
   - Set the following:
     - Name: "URL Shortener"
     - Index pattern: `url_shortener_logs`
     - Timestamp field: `timestamp`
   - Click "Save data view to Kibana"

3. **View Logs**
   - Go to Analytics → Discover
   - Select the "URL Shortener" data view
   - You can now see all request logs and create visualizations

## Available Endpoints

- `GET /` - Home page with URL shortening form
- `POST /shorten` - Create a short URL
- `GET /<short_url>` - Redirect to the original URL

## Logging Information

The application logs the following information for each request:
- Short URL and Long URL
- IP address
- User agent
- Timestamp
- Request duration
- Status code
- Request method
- Request path
- Referrer

## Troubleshooting

1. **Elasticsearch Connection Issues**
   - Verify Elasticsearch is running: `curl localhost:9200`
   - Check credentials in .env file
   - Ensure ports 9200 is not being used by other services

2. **Kibana Access Issues**
   - Verify Kibana is running: `curl localhost:5601`
   - Check if Elasticsearch is healthy
   - Ensure port 5601 is not being used by other services

3. **MySQL Issues**
   - Verify MySQL service is running
   - Check database credentials
   - Ensure the database exists

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 
