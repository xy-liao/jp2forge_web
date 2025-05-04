import sys
print("Python paths:", sys.path)
try:
    from core.types import WorkflowConfig
    print("Direct import works!")
except ImportError as e:
    print(f"Direct import failed: {e}")
try:
    import jp2forge
    print(f"Package import works! Version: {jp2forge.__version__}")
except ImportError as e:
    print(f"Package import failed: {e}")
