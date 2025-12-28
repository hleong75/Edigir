#!/usr/bin/env python3
"""
Edigir - LED Destination Sign Editor
Main entry point for the application.
"""

import sys
import os

# Add the parent directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edigir_py.main import main

if __name__ == "__main__":
    main()
