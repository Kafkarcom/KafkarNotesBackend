#!/usr/bin/env python
"""
Test runner script that properly configures the environment for tests
and generates markdown reports of test results
"""
import os
import unittest
import sys
import logging
from datetime import datetime
import inspect
import glob

# Configure the environment for testing
os.environ['TESTING'] = 'True'
os.environ['DEBUG'] = 'False'
os.environ['LOG_LEVEL'] = 'DEBUG'  # Capture all log levels in test log file

class MarkdownTestResult(unittest.TestResult):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.test_results = []
        
    def startTest(self, test):
        self.start_time = datetime.now()
        super().startTest(test)
        
    def addSuccess(self, test):
        self.test_results.append({
            'name': test.id(),
            'result': 'PASS',
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'doc': test._testMethodDoc or "No description available"
        })
        super().addSuccess(test)
        
    def addError(self, test, err):
        self.test_results.append({
            'name': test.id(),
            'result': 'ERROR',
            'error': str(err[1]),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'doc': test._testMethodDoc or "No description available"
        })
        super().addError(test, err)
        
    def addFailure(self, test, err):
        self.test_results.append({
            'name': test.id(),
            'result': 'FAIL',
            'error': str(err[1]),
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'doc': test._testMethodDoc or "No description available"
        })
        super().addFailure(test, err)

def generate_test_report(result, start_time, end_time):
    """Generate a markdown report from test results"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f'test_reports/test_report_{timestamp}.md'
    
    # Clean up old reports (keep only the latest)
    old_reports = glob.glob('test_reports/test_report_*.md')
    for old_report in old_reports:
        try:
            os.remove(old_report)
        except Exception as e:
            print(f"Warning: Could not remove old report {old_report}: {e}")
    
    with open(report_file, 'w') as f:
        f.write(f"# Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        total_duration = (end_time - start_time).total_seconds()
        f.write("## Summary\n\n")
        f.write(f"- **Start Time:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **End Time:** {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- **Duration:** {total_duration:.2f} seconds\n")
        f.write(f"- **Total Tests:** {result.testsRun}\n")
        f.write(f"- **Successes:** {len(result.test_results) - len(result.failures) - len(result.errors)}\n")
        f.write(f"- **Failures:** {len(result.failures)}\n")
        f.write(f"- **Errors:** {len(result.errors)}\n\n")
        
        # Detailed Results
        f.write("## Detailed Results\n\n")
        for test_result in result.test_results:
            f.write(f"### {test_result['name']}\n\n")
            f.write(f"- **Result:** {test_result['result']}\n")
            f.write(f"- **Duration:** {test_result['duration']:.3f} seconds\n")
            f.write(f"- **Description:** {test_result['doc']}\n")
            if 'error' in test_result:
                f.write(f"- **Error:** {test_result['error']}\n")
            f.write("\n")
            
    return report_file

def run_tests():
    """Run all tests and generate a markdown report"""
    print("Running tests - all logs will be stored in logs/test.log")
    
    # Ensure required directories exist
    for directory in ['logs', 'test_reports']:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    start_time = datetime.now()
    
    # Find and run all test cases
    test_suite = unittest.TestLoader().discover('tests', pattern='test_*.py')
    result = MarkdownTestResult()
    test_suite.run(result)
    
    end_time = datetime.now()
    
    # Generate report
    report_file = generate_test_report(result, start_time, end_time)
    
    print(f"\nTest run completed.")
    print(f"- Full logs available in logs/test.log")
    print(f"- Test report available in {report_file}")
    
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == '__main__':
    success = run_tests()
    # Exit with non-zero code if tests failed
    sys.exit(0 if success else 1)