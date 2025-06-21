#!/usr/bin/env python
"""
JP2Forge Import Test

This script tests the different import paths for JP2Forge modules.
Use this script to troubleshoot import path issues and check JP2Forge installation.
"""

import os
import sys

# Add the parent directory to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings before importing any Django-dependent modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
import django
django.setup()

print("Python paths:", sys.path)

# Test direct imports (used in development environments or source installs)
print("\nTesting direct import path:")
try:
    from core.types import WorkflowConfig
    print("✓ Direct import works!")
except ImportError as e:
    print(f"✗ Direct import failed: {e}")

# Test package imports (used when installed via pip or as a package)
print("\nTesting package import path:")
try:
    import jp2forge
    print(f"✓ Package import works! Version: {getattr(jp2forge, '__version__', 'unknown')}")
    
    # Test if specific modules can be imported
    try:
        from jp2forge.core.types import WorkflowConfig as PackageWorkflowConfig
        print("✓ Package module imports work!")
    except ImportError as e:
        print(f"✗ Package module imports failed: {e}")
except ImportError as e:
    print(f"✗ Package import failed: {e}")

# Test adapter import (this should always work if Django is set up correctly)
print("\nTesting adapter import:")
try:
    from converter.jp2forge_adapter import adapter
    print(f"✓ Adapter import works! Availability: {adapter.jp2forge_available}")
    if not adapter.jp2forge_available:
        print("  Note: JP2Forge is not available or mock mode is enabled")
except ImportError as e:
    print(f"✗ Adapter import failed: {e}")

if __name__ == "__main__":
    print("\nSummary: Use the appropriate import path in your code based on the test results above.")
    print("If all imports failed, ensure JP2Forge is properly installed.")
