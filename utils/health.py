"""Health check module to monitor server status"""
import os
import psutil
import time
from datetime import datetime

_start_time = time.time()

def get_server_health():
    """Get server health information"""
    try:
        process = psutil.Process(os.getpid())
        
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': int(time.time() - _start_time),
            'process': {
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
            },
            'message': 'Server is running normally'
        }
    except Exception as e:
        return {
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'message': f'Error checking server health: {str(e)}'
        }
