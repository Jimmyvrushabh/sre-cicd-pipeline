from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
# Main Route
# ─────────────────────────────────────────
@app.route('/')
def home():
    return jsonify({
        "message": "SRE Python App",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "status": "running"
    }), 200

# ─────────────────────────────────────────
# Health Check — Is app alive?
# ─────────────────────────────────────────
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# ─────────────────────────────────────────
# Readiness Check — Is app ready for traffic?
# ─────────────────────────────────────────
@app.route('/ready')
def ready():
    return jsonify({
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }), 200

# ─────────────────────────────────────────
# Version Info
# ─────────────────────────────────────────
@app.route('/version')
def version():
    return jsonify({
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "build": os.getenv("BUILD_NUMBER", "local"),
        "environment": os.getenv("ENV", "development")
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
