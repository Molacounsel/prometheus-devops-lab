from flask import Flask, Response, jsonify
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import random
import time
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Prometheus metrics definitions
REQUEST_COUNT = Counter('app_requests_total', 'Total number of requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('app_request_duration_seconds', 'Request latency', ['endpoint'])
ACTIVE_USERS = Gauge('app_active_users', 'Number of active users')
SYSTEM_CPU = Gauge('app_system_cpu_percent', 'System CPU usage')
SYSTEM_MEMORY = Gauge('app_system_memory_percent', 'System memory usage')
ERROR_COUNT = Counter('app_errors_total', 'Total number of application errors', ['error_type'])

@app.before_request
def before_request():
    """Record request start time for latency measurement"""
    import flask
    flask.g.start_time = time.time()

@app.after_request
def after_request(response):
    """Record metrics after each request"""
    import flask
    
    # Calculate request duration
    request_duration = time.time() - flask.g.start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=flask.request.method,
        endpoint=flask.request.endpoint or 'unknown',
        status_code=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        endpoint=flask.request.endpoint or 'unknown'
    ).observe(request_duration)
    
    return response

@app.route('/')
def home():
    """Main application page with monitoring links"""
    return '''
    <h1>🚀 DevOps Monitoring Lab</h1>
    <p>Sample application demonstrating Prometheus monitoring integration.</p>
    
    <h2>🔍 Application Endpoints:</h2>
    <ul>
        <li><a href="/metrics">📊 Prometheus Metrics</a></li>
        <li><a href="/health">❤️ Health Check</a></li>
        <li><a href="/simulate-load">⚡ Simulate Load</a></li>
        <li><a href="/simulate-error">💥 Simulate Errors</a></li>
        <li><a href="/user-activity">👥 User Activity</a></li>
    </ul>
    
    <h2>📊 Monitoring Stack:</h2>
    <ul>
        <li><a href="http://localhost:9090" target="_blank">Prometheus UI</a> - Metrics & Alerts</li>
        <li><a href="http://localhost:3000" target="_blank">Grafana</a> - Dashboards (admin/devops123)</li>
        <li><a href="http://localhost:8080" target="_blank">cAdvisor</a> - Container Metrics</li>
        <li><a href="http://localhost:9100/metrics" target="_blank">Node Exporter</a> - System Metrics</li>
    </ul>
    '''

@app.route('/health')
def health():
    """Health check endpoint with system status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        health_data = {
            'status': 'healthy',
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent
            }
        }
        
        # Determine health status based on system load
        if cpu_percent > 90 or memory.percent > 90:
            health_data['status'] = 'degraded'
            health_data['warnings'] = []
            if cpu_percent > 90:
                health_data['warnings'].append('High CPU usage')
            if memory.percent > 90:
                health_data['warnings'].append('High memory usage')
        
        return jsonify(health_data)
        
    except Exception as e:
        ERROR_COUNT.labels(error_type='health_check').inc()
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/simulate-load')
def simulate_load():
    """Simulate system load for testing monitoring"""
    try:
        duration = random.uniform(0.5, 3.0)
        
        # Simulate CPU work
        start_time = time.time()
        while time.time() - start_time < duration:
            sum(i*i for i in range(1000))
        
        # Update user activity
        ACTIVE_USERS.set(random.randint(20, 100))
        
        return jsonify({
            'message': 'Load simulation completed',
            'duration': f'{duration:.2f}s',
            'timestamp': time.time()
        })
        
    except Exception as e:
        ERROR_COUNT.labels(error_type='load_simulation').inc()
        return jsonify({'error': str(e)}), 500

@app.route('/simulate-error')
def simulate_error():
    """Simulate random application errors for testing alerting"""
    error_chance = random.random()
    
    if error_chance < 0.2:  # 20% server error
        ERROR_COUNT.labels(error_type='server_error').inc()
        return jsonify({'error': 'Internal server error'}), 500
    elif error_chance < 0.3:  # 10% client error
        ERROR_COUNT.labels(error_type='client_error').inc()
        return jsonify({'error': 'Bad request'}), 400
    else:  # 70% success
        return jsonify({
            'message': 'Success response',
            'value': random.randint(1, 100)
        })

@app.route('/user-activity')
def user_activity():
    """Simulate realistic user activity patterns"""
    hour = time.localtime().tm_hour
    
    # Simulate business hours activity
    if 9 <= hour <= 17:
        users = random.randint(30, 80)
    else:
        users = random.randint(5, 25)
    
    ACTIVE_USERS.set(users)
    
    return jsonify({
        'active_users': users,
        'hour': hour,
        'timestamp': time.time()
    })

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update system metrics
        SYSTEM_CPU.set(psutil.cpu_percent(interval=0.1))
        SYSTEM_MEMORY.set(psutil.virtual_memory().percent)
        
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
        
    except Exception as e:
        ERROR_COUNT.labels(error_type='metrics_error').inc()
        return Response("# Metrics unavailable\n", mimetype=CONTENT_TYPE_LATEST), 500

if __name__ == '__main__':
    print("Starting DevOps Sample Application...")
    print("Metrics: http://localhost:5000/metrics")
    print("Health: http://localhost:5000/health")
    
    # Initialize metrics
    ACTIVE_USERS.set(random.randint(10, 50))
    
    app.run(host='0.0.0.0', port=5000, debug=False)