#!/usr/bin/env python3
"""
Naebak API Gateway Service
Central gateway for all microservices
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Service URLs
SERVICES = {
    'auth': os.getenv('AUTH_SERVICE_URL', 'https://naebak-auth-service-jux3rvgvka-uc.a.run.app'),
    'content': os.getenv('CONTENT_SERVICE_URL', 'https://naebak-content-service-jux3rvgvka-uc.a.run.app'),
}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'naebak-gateway',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'services': SERVICES
    })

@app.route('/api/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_auth(path):
    """Proxy requests to auth service"""
    try:
        url = f"{SERVICES['auth']}/api/auth/{path}"
        
        # Forward the request
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False
        )
        
        # Return the response
        return response.content, response.status_code, response.headers.items()
    
    except Exception as e:
        logger.error(f"Error proxying to auth service: {str(e)}")
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/content/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_content(path):
    """Proxy requests to content service"""
    try:
        url = f"{SERVICES['content']}/api/{path}"
        
        # Forward the request
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            params=request.args,
            allow_redirects=False
        )
        
        # Return the response
        return response.content, response.status_code, response.headers.items()
    
    except Exception as e:
        logger.error(f"Error proxying to content service: {str(e)}")
        return jsonify({'error': 'Service unavailable'}), 503

@app.route('/api/services', methods=['GET'])
def list_services():
    """List all available services"""
    service_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            # Try to ping each service
            response = requests.get(f"{service_url}/api/health/", timeout=5)
            service_status[service_name] = {
                'url': service_url,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except Exception as e:
            service_status[service_name] = {
                'url': service_url,
                'status': 'unhealthy',
                'error': str(e)
            }
    
    return jsonify({
        'gateway': 'naebak-gateway',
        'version': '1.0.0',
        'services': service_status,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'message': 'Naebak API Gateway',
        'version': '1.0.0',
        'endpoints': {
            '/health': 'Gateway health check',
            '/api/services': 'List all services',
            '/api/auth/*': 'Authentication service',
            '/api/content/*': 'Content service'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
