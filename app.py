from flask import Flask, render_template, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import time
from elasticsearch import Elasticsearch
import json

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Elasticsearch
es = Elasticsearch(
    os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200'),
    basic_auth=(
        os.getenv('ELASTICSEARCH_USER', 'elastic'),
        os.getenv('ELASTICSEARCH_PASSWORD', '')
    )
)

# Create Elasticsearch index for request logs if it doesn't exist
def setup_elasticsearch():
    index_name = 'url_shortener_logs'
    if not es.indices.exists(index=index_name):
        # Define mapping for request logs
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
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1
            }
        }
        es.indices.create(index=index_name, body=mapping)
        app.logger.info(f'Created Elasticsearch index: {index_name}')

# Configure logging
def setup_logger():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Configure file handler
    file_handler = RotatingFileHandler(
        'logs/url_shortener.log',
        maxBytes=1024 * 1024,  # 1MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(logging.INFO)

    # Add handlers to app logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info('URL Shortener startup')

setup_logger()
setup_elasticsearch()

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql://{os.getenv('MYSQL_USER', 'root')}:"
    f"{os.getenv('MYSQL_PASSWORD', '')}@"
    f"{os.getenv('MYSQL_HOST', 'localhost')}/"
    f"{os.getenv('MYSQL_DATABASE', 'url_shortener')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Initialize SQLAlchemy
db = SQLAlchemy(app)

class URLMapping(db.Model):
    __tablename__ = 'url_mappings'
    
    id = db.Column(db.Integer, primary_key=True)
    long_url = db.Column(db.String(2048), nullable=False)
    short_url = db.Column(db.String(16), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<URLMapping {self.short_url}>'

def log_request_to_elasticsearch(request_data):
    """Log request data to Elasticsearch"""
    try:
        es.index(
            index='url_shortener_logs',
            document=request_data
        )
    except Exception as e:
        app.logger.error(f'Error logging to Elasticsearch: {str(e)}', exc_info=True)

@app.before_request
def before_request():
    # Add request timestamp for performance logging
    request.start_time = time.time()

@app.after_request
def after_request(response):
    # Log request details and performance
    if not request.path.startswith('/static'):
        try:
            # Calculate request duration
            duration = time.time() - request.start_time
            
            # Prepare log data
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'request_method': request.method,
                'request_path': request.path,
                'status_code': response.status_code,
                'request_duration': round(duration, 3),
                'ip_address': request.remote_addr,
                'user_agent': request.user_agent.string,
                'referrer': request.referrer or '',
                'short_url': request.path[1:] if request.path.count('/') == 1 else '',
            }

            # Add URL mapping data if available
            if request.path.count('/') == 1 and request.path != '/':
                url_mapping = URLMapping.query.filter_by(short_url=request.path[1:]).first()
                if url_mapping:
                    log_data['long_url'] = url_mapping.long_url

            # Log to Elasticsearch
            log_request_to_elasticsearch(log_data)
            
            # Log to application logger
            app.logger.info(
                f'Request: {request.method} {request.path} - '
                f'Status: {response.status_code} - '
                f'Duration: {duration:.2f}s - '
                f'IP: {request.remote_addr}'
            )
        
        except Exception as e:
            app.logger.error(f'Error in after_request: {str(e)}', exc_info=True)
    
    return response

@app.route('/')
def index():
    """Render the main page"""
    app.logger.debug('Rendering index page')
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten_url():
    """Create a short URL from a long URL"""
    try:
        long_url = request.form.get('url')
        if not long_url:
            app.logger.warning('URL shortening attempted without URL')
            return jsonify({'error': 'URL is required'}), 400

        # Log the shortening request
        app.logger.info(f'Shortening URL request received for: {long_url[:100]}...')

        # Check if URL already exists
        existing_url = URLMapping.query.filter_by(long_url=long_url).first()
        if existing_url:
            app.logger.info(f'Returning existing short URL for: {long_url[:100]}...')
            return jsonify({
                'short_url': request.host_url + existing_url.short_url
            })

        # Generate new short URL
        short_url = generate_short_url()
        
        # Create new URL mapping
        new_url = URLMapping(
            long_url=long_url,
            short_url=short_url
        )
        
        db.session.add(new_url)
        db.session.commit()

        app.logger.info(f'Created new short URL: {short_url} for: {long_url[:100]}...')
        return jsonify({
            'short_url': request.host_url + short_url
        })

    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Error shortening URL: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/<short_url>')
def redirect_to_url(short_url):
    """Redirect to the original URL and log the request"""
    try:
        # Find the URL mapping
        url_mapping = URLMapping.query.filter_by(short_url=short_url).first()
        if not url_mapping:
            app.logger.warning(f'Attempted to access non-existent short URL: {short_url}')
            abort(404)

        app.logger.info(f'Redirecting {short_url} to: {url_mapping.long_url[:100]}...')
        return redirect(url_mapping.long_url)

    except Exception as e:
        app.logger.error(f'Error redirecting URL: {str(e)}', exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Short URL not found'}), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    app.logger.error(f'Server Error: {str(e)}', exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

def generate_short_url(length=6):
    """Generate a random short URL of specified length"""
    import string
    import random
    characters = string.ascii_letters + string.digits
    while True:
        short_url = ''.join(random.choice(characters) for _ in range(length))
        # Check if short_url already exists
        if not URLMapping.query.filter_by(short_url=short_url).first():
            return short_url

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        app.logger.info('Database tables created')
    app.run(debug=True) 