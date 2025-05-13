#!/usr/bin/env python
import argparse
import os
from app import app

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run the Flask API application')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # Override environment variable if --debug is provided
    if args.debug:
        os.environ['DEBUG'] = 'True'
    
    app.run(host=args.host, port=args.port, debug=app.config.get('DEBUG', False))