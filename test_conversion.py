#!/usr/bin/env python
"""
JP2Forge Conversion Test

This script performs a quick test conversion using image files that exist in the project.
Use this script for simple testing without needing to specify an image path.
It automatically finds suitable test images within the project or creates a simple test image if needed.

Examples:
    # Run with default settings (lossless mode, photograph document type)
    python test_conversion.py

    # Test with lossy compression
    python test_conversion.py --mode lossy

    # Test with BnF compliance for heritage documents
    python test_conversion.py --mode bnf_compliant --document-type heritage_document
"""

import os
import sys
import argparse
from pathlib import Path

# Add the current directory to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings before importing any Django-dependent modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
import django
django.setup()

# Now import the JP2Forge adapter
from converter.jp2forge_adapter import adapter

def get_test_image():
    """Find an existing image in the project that we can use for testing"""
    # List of potential test images in the project
    test_images = [
        os.path.join("static", "images", "docs", "jp2forge_web_config.png"),
        os.path.join("static", "images", "docs", "jp2forge_web_welcome.png"),
    ]
    
    for image_path in test_images:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path)
        if os.path.exists(full_path):
            return full_path
    
    # If no existing images found, create a simple test image
    from PIL import Image
    import tempfile
    
    test_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img.save(test_image.name)
    
    return test_image.name

def run_test_conversion(mode="lossless", document_type="photograph"):
    """Run a test conversion using an image that exists in the project"""
    print("JP2Forge Conversion Test")
    print("========================")
    
    # First check JP2Forge availability
    print(f"JP2Forge availability: {adapter.jp2forge_available}")
    if not adapter.jp2forge_available:
        print("JP2Forge is not available. Conversion will run in mock mode.")
    
    # Find a test image
    input_path = get_test_image()
    print(f"Using test image: {input_path}")
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    report_dir = os.path.join(output_dir, "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    print(f"Testing conversion with mode: {mode}")
    
    # Create configuration
    config_params = {
        'output_dir': output_dir,
        'report_dir': report_dir,
        'compression_mode': mode.upper(),
        'document_type': document_type.upper(),
        'keep_temp': True,
        'quality': 90.0 if mode.lower() == "lossy" else None
    }
    
    config = adapter.create_config(**config_params)
    if not config:
        print("Failed to create configuration")
        return False
    
    # Process file
    print("\nStarting conversion...")
    
    def progress_callback(data):
        progress = data.get('percent_complete', 0)
        print(f"Progress: {progress:.1f}%", end="\r")
    
    result = adapter.process_file(config, input_path, progress_callback=progress_callback)
    
    if result.success:
        print("\nConversion completed successfully!")
        if isinstance(result.output_file, list):
            print(f"Multiple output files generated ({len(result.output_file)})")
            for i, f in enumerate(result.output_file):
                print(f"  Output {i+1}: {f}")
        else:
            print(f"Output file: {result.output_file}")
        
        # Print metrics
        if result.metrics:
            print("\nQuality metrics:")
            for key, value in result.metrics.items():
                print(f"  {key}: {value}")
        
        # Print file sizes
        if result.file_sizes:
            print("\nFile size information:")
            for key, value in result.file_sizes.items():
                print(f"  {key}: {value}")
        
        print("\nYou can check the output file at:")
        if isinstance(result.output_file, list):
            print(f"  {result.output_file[0]}")
        else:
            print(f"  {result.output_file}")
        
        return True
    else:
        print(f"\nConversion failed: {result.error}")
        return False

def main():
    """Main function for command-line use"""
    parser = argparse.ArgumentParser(description='Test JP2Forge conversion with an existing image')
    parser.add_argument('--mode', '-m', default='lossless', 
                        choices=['lossless', 'lossy', 'supervised', 'bnf_compliant'],
                        help='Compression mode')
    parser.add_argument('--document-type', '-d', default='photograph',
                        choices=['photograph', 'heritage_document', 'color', 'grayscale'],
                        help='Document type')
    
    args = parser.parse_args()
    
    # Run the test conversion
    run_test_conversion(
        mode=args.mode,
        document_type=args.document_type
    )

if __name__ == "__main__":
    main()