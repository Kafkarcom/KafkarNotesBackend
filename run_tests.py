#!/usr/bin/env python
"""
Test runner script that properly configures the environment for tests
"""
import os
import unittest
import sys
import logging

# Configure the environment for testing
os.environ['TESTING'] = 'True'
os.environ['DEBUG'] = 'False'
os.environ['LOG_LEVEL'] = 'DEBUG'  # Capture all log levels in test log file

def run_tests():
    """Run all tests in the tests directory"""
    print("Running tests - all logs will be stored in logs/test.log")
    
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Find and run all test cases in the tests directory
    tests = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    
    print(f"\nTest run completed. Full logs available in logs/test.log")
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    # Exit with non-zero code if tests failed
    sys.exit(0 if success else 1)