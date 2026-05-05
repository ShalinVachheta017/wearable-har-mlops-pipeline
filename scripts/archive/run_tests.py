#!/usr/bin/env python3
"""
Run Tests Script
================

Convenience script to run the test suite with common configurations.

Usage:
    python scripts/run_tests.py                    # Run all tests
    python scripts/run_tests.py --unit             # Run unit tests only
    python scripts/run_tests.py --coverage         # Run with coverage report
    python scripts/run_tests.py --quick            # Run without slow tests
    python scripts/run_tests.py --specific trigger # Run specific test file

Author: HAR MLOps Pipeline
Date: January 30, 2026
"""

import argparse
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"


def run_command(cmd: list) -> int:
    """Run command and return exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Run HAR MLOps test suite')
    
    parser.add_argument('--unit', action='store_true',
                       help='Run unit tests only')
    parser.add_argument('--integration', action='store_true',
                       help='Run integration tests only')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate coverage report')
    parser.add_argument('--quick', action='store_true',
                       help='Skip slow tests')
    parser.add_argument('--specific', type=str, default=None,
                       help='Run specific test file (e.g., "trigger" for test_trigger_policy.py)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--parallel', '-p', action='store_true',
                       help='Run tests in parallel')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Test path
    if args.specific:
        # Find matching test file
        test_files = list(TESTS_DIR.glob(f'*{args.specific}*.py'))
        if test_files:
            cmd.append(str(test_files[0]))
        else:
            print(f"No test file matching '{args.specific}' found")
            return 1
    else:
        cmd.append(str(TESTS_DIR))
    
    # Options
    if args.verbose:
        cmd.append('-v')
    else:
        cmd.append('-v')  # Always use verbose for better output
    
    if args.unit:
        cmd.extend(['-m', 'unit'])
    
    if args.integration:
        cmd.extend(['-m', 'integration'])
    
    if args.quick:
        cmd.extend(['-m', 'not slow'])
    
    if args.coverage:
        cmd.extend([
            '--cov=src',
            '--cov-report=term-missing',
            '--cov-report=html'
        ])
    
    if args.parallel:
        cmd.extend(['-n', 'auto'])
    
    # Additional useful options
    cmd.extend([
        '--tb=short',        # Shorter tracebacks
        '-ra',               # Show summary of all test outcomes
    ])
    
    # Run tests
    exit_code = run_command(cmd)
    
    # Summary
    print(f"\n{'='*60}")
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code: {exit_code}")
    
    if args.coverage:
        print(f"\nCoverage report generated in: {PROJECT_ROOT / 'htmlcov' / 'index.html'}")
    
    print(f"{'='*60}\n")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
