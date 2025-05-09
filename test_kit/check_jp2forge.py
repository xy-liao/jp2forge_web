try:
    import jp2forge
    print(f"JP2Forge is installed (version {jp2forge.__version__})")
except ImportError:
    print("JP2Forge is NOT installed")
