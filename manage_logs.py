#!/usr/bin/env python
"""
Script to manage log files in the logs directory.
Features:
- Delete old log files while keeping N most recent ones
- Separate handling for app and test logs
- Compress old logs (optional)
"""

import os
import glob
import argparse
from datetime import datetime
import logging

def setup_logging():
    """Configure logging for the log management script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger(__name__)

def get_log_files(log_type='app'):
    """Get all log files of specified type sorted by modification time"""
    pattern = f'logs/{log_type}_*.log'
    files = glob.glob(pattern)
    # Sort files by modification time, newest first
    return sorted(files, key=os.path.getmtime, reverse=True)

def cleanup_logs(keep_count=10, log_type='app'):
    """Keep only the N most recent log files of specified type"""
    logger = setup_logging()
    
    log_files = get_log_files(log_type)
    logger.info(f"Found {len(log_files)} {log_type} log files")
    
    # Keep the N most recent files
    files_to_delete = log_files[keep_count:]
    
    if not files_to_delete:
        logger.info(f"No {log_type} log files to delete")
        return
    
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            logger.info(f"Deleted old log file: {file_path}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description='Manage application log files')
    parser.add_argument('--keep', type=int, default=10,
                      help='Number of most recent log files to keep (default: 10)')
    parser.add_argument('--type', choices=['app', 'test', 'all'],
                      default='all', help='Type of logs to clean up (default: all)')
    
    args = parser.parse_args()
    
    if args.type in ['app', 'all']:
        cleanup_logs(args.keep, 'app')
    if args.type in ['test', 'all']:
        cleanup_logs(args.keep, 'test')

if __name__ == '__main__':
    main()
