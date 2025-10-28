#!/usr/bin/env python3
"""
Test runner script for Animus Letta MCP Server.

This script provides easy access to run different types of tests:
- Unit tests
- Integration tests
- End-to-end tests
- All tests with coverage

Copyright (c) 2025 Mark Rizzn Hopkins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test runner for MCP Server")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "all", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--no-cov",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    base_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        base_cmd.append("-v")
    
    if not args.no_cov and args.type in ["all", "coverage"]:
        base_cmd.extend(["--cov=smcp", "--cov-report=term-missing"])
    
    success = True
    
    if args.type == "unit":
        success = run_command(
            base_cmd + ["tests/unit/", "-m", "unit"],
            "Unit Tests"
        )
    
    elif args.type == "integration":
        success = run_command(
            base_cmd + ["tests/integration/", "-m", "integration"],
            "Integration Tests"
        )
    
    elif args.type == "e2e":
        success = run_command(
            base_cmd + ["tests/e2e/", "-m", "e2e"],
            "End-to-End Tests"
        )
    
    elif args.type == "all":
        success = run_command(
            base_cmd + ["tests/"],
            "All Tests"
        )
    
    elif args.type == "coverage":
        success = run_command(
            base_cmd + ["tests/", "--cov-report=html:htmlcov", "--cov-report=xml"],
            "All Tests with Coverage Reports"
        )
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main() 