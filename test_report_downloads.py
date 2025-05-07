#!/usr/bin/env python
"""
JP2Forge Report Download Testing Utility

This script tests the ability to download reports for all compression modes
and document types. It creates test jobs, uploads images, processes them,
and then tries to download the reports through the API endpoint.

This helps ensure that reports are properly generated and downloadable for all
combinations of:
- Document types (photograph, heritage_document, color, grayscale)
- Compression modes (lossless, lossy, supervised, bnf_compliant)
- BnF compliance settings (True/False where applicable)
- Single-page and multi-page documents

Usage:
    python test_report_downloads.py [--verbose] [--server-url SERVER_URL] [--username USERNAME] [--password PASSWORD]

Options:
    --verbose           Show detailed information about each test
    --server-url        URL of the JP2Forge Web server (default: http://localhost:8000)
    --username          Username to login with (default: admin)
    --password          Password for login (default: admin)
"""

import os
import sys
import json
import time
import argparse
import requests
import tempfile
import shutil
from pathlib import Path
from urllib.parse import urljoin

# Add the current directory to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings before importing any Django-dependent modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
import django
django.setup()

# Import the JP2Forge adapter and BnF validator
from converter.jp2forge_adapter import adapter, JP2ForgeResult
from converter.models import ConversionJob
from django.contrib.auth.models import User
from django.test import Client

# Terminal colors for better output formatting
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_test_image(multipage=False):
    """Find an existing image in the project or create one for testing"""
    # For multi-page, create a multi-page TIFF
    if multipage:
        from PIL import Image
        
        # Create a simple multi-page TIFF file
        test_image = tempfile.NamedTemporaryFile(suffix='.tiff', delete=False)
        imgs = []
        # Create 3 pages with different colors
        for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
            imgs.append(Image.new('RGB', (100, 100), color=color))
        
        # Save as multi-page TIFF
        imgs[0].save(test_image.name, save_all=True, append_images=imgs[1:])
        return test_image.name
    
    # For single-page, use existing images or create one
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
    
    test_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img = Image.new('RGB', (100, 100), color=(73, 109, 137))
    img.save(test_image.name)
    
    return test_image.name

def ensure_test_user_exists(username='admin', password='admin'):
    """Ensure the test user exists in the database"""
    try:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=f"{username}@example.com", password=password)
            print(f"Created test user {username}")
        return True
    except Exception as e:
        print(f"Error creating test user: {e}")
        return False

def test_report_download(doc_type, comp_mode, bnf_compliant, multipage=False, verbose=False, server_url="http://localhost:8000", username="admin", password="admin"):
    """Test report generation and download for a specific combination"""
    # Skip invalid combinations (bnf_compliant mode always has bnf_compliant=True)
    if comp_mode == 'bnf_compliant' and not bnf_compliant:
        if verbose:
            print(f"{Colors.BLUE}Skipping invalid combination: {comp_mode} with bnf_compliant=False{Colors.ENDC}")
        return None
    
    if verbose:
        print(f"\n{Colors.HEADER}Testing: {doc_type} + {comp_mode} + BnF={bnf_compliant}{Colors.ENDC}")
    
    # First, test direct model approach (without HTTP)
    try:
        # Get test image
        input_path = get_test_image(multipage=multipage)
        
        # Create a test job in the database
        user = User.objects.get(username=username)
        
        job = ConversionJob.objects.create(
            user=user,
            compression_mode=comp_mode,
            document_type=doc_type,
            bnf_compliant=bnf_compliant,
            status='pending',
            quality=90 if comp_mode in ('lossy', 'supervised') else None,
            original_filename=os.path.basename(input_path)
        )
        
        if verbose:
            print(f"Created test job: {job.id}")
        
        # Process the job (non-HTTP approach)
        # Create output and report directories
        output_dir = os.path.join("media", f"jobs/{job.id}/output")
        report_dir = os.path.join("media", f"jobs/{job.id}/reports")
        
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(report_dir, exist_ok=True)
        
        # Create mock config and process file
        config = adapter.create_config(
            output_dir=output_dir,
            report_dir=report_dir,
            compression_mode=comp_mode.upper(),
            document_type=doc_type.upper(),
            bnf_compliant=bnf_compliant,
            quality=90.0 if comp_mode in ('lossy', 'supervised') else None
        )
        
        result = adapter.process_file(config, input_path)
        
        # Update job with results
        job.status = 'completed'
        if isinstance(result.output_file, list):
            job.output_filename = ', '.join([os.path.basename(f) for f in result.output_file])
        else:
            job.output_filename = os.path.basename(result.output_file)
        
        # Add metrics from result
        if result.file_sizes:
            job.original_size = result.file_sizes.get('original_size', 0)
            job.converted_size = result.file_sizes.get('converted_size', 0)
            
            # Handle compression ratio
            compression_ratio = result.file_sizes.get('compression_ratio', '0')
            if isinstance(compression_ratio, str) and ':' in compression_ratio:
                job.compression_ratio = float(compression_ratio.split(':')[0])
            else:
                job.compression_ratio = float(compression_ratio) if compression_ratio else 0
                
        # Store metrics
        job.metrics = result.metrics
        job.save()
        
        # Now test downloading the report through Django client
        client = Client()
        client.login(username=username, password=password)
        
        # Try to download the report
        response = client.get(f"/media/jobs/{job.id}/reports/report.json")
        
        if response.status_code == 200:
            if verbose:
                print(f"{Colors.GREEN}Report download successful!{Colors.ENDC}")
            
            # Validate the report content
            try:
                report_content = json.loads(response.content)
                
                # Basic validation checks
                if not report_content:
                    raise ValueError("Empty report")
                
                # Success - store the report for future use if needed
                report_path = os.path.join("test_output", f"report_{doc_type}_{comp_mode}_{bnf_compliant}_{multipage}.json")
                os.makedirs(os.path.dirname(report_path), exist_ok=True)
                with open(report_path, 'w') as f:
                    json.dump(report_content, f, indent=2)
                
                if verbose:
                    print(f"Saved report to: {report_path}")
                
                return True
                
            except Exception as e:
                print(f"{Colors.FAIL}Report validation error: {e}{Colors.ENDC}")
                return False
        else:
            print(f"{Colors.FAIL}Report download failed: status {response.status_code}{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.FAIL}Test failed: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up if needed
        pass

def run_all_tests(verbose=False, server_url="http://localhost:8000", username="admin", password="admin"):
    """Run tests for all possible combinations"""
    document_types = ['photograph', 'heritage_document', 'color', 'grayscale']
    compression_modes = ['lossless', 'lossy', 'supervised', 'bnf_compliant']
    bnf_values = [True, False]
    page_types = [False, True]  # False=single-page, True=multi-page
    
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'single_page': {'passed': 0, 'failed': 0},
        'multi_page': {'passed': 0, 'failed': 0}
    }
    
    # Ensure test user exists
    if not ensure_test_user_exists(username=username, password=password):
        print(f"{Colors.FAIL}Failed to create test user - aborting tests{Colors.ENDC}")
        return results
    
    for doc_type in document_types:
        for comp_mode in compression_modes:
            for bnf_compliant in bnf_values:
                for is_multipage in page_types:
                    # Skip invalid combination
                    if comp_mode == 'bnf_compliant' and not bnf_compliant:
                        results['skipped'] += 1
                        continue
                    
                    results['total'] += 1
                    
                    # Test this combination
                    test_result = test_report_download(
                        doc_type=doc_type,
                        comp_mode=comp_mode,
                        bnf_compliant=bnf_compliant,
                        multipage=is_multipage,
                        verbose=verbose,
                        server_url=server_url,
                        username=username,
                        password=password
                    )
                    
                    # Record results
                    if test_result is True:
                        results['passed'] += 1
                        if is_multipage:
                            results['multi_page']['passed'] += 1
                        else:
                            results['single_page']['passed'] += 1
                    elif test_result is False:
                        results['failed'] += 1
                        if is_multipage:
                            results['multi_page']['failed'] += 1
                        else:
                            results['single_page']['failed'] += 1
    
    return results

def main():
    """Main function for command-line use"""
    parser = argparse.ArgumentParser(description='Test JP2Forge report downloads')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    parser.add_argument('--server-url', default="http://localhost:8000", 
                        help='URL of the JP2Forge Web server')
    parser.add_argument('--username', default="admin",
                        help='Username to login with')
    parser.add_argument('--password', default="admin", 
                        help='Password for login')
    
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}JP2Forge Report Download Testing Utility{Colors.ENDC}")
    print("=" * 40)
    
    # Make sure Django server is running
    print(f"Testing against server: {args.server_url}")
    print(f"JP2Forge availability: {adapter.jp2forge_available}")
    if not adapter.jp2forge_available:
        print("JP2Forge is not available. Tests will run in mock mode.")
    
    print("\nRunning report download tests for all valid combinations...")
    start_time = time.time()
    results = run_all_tests(
        verbose=args.verbose,
        server_url=args.server_url,
        username=args.username,
        password=args.password
    )
    duration = time.time() - start_time
    
    # Print summary
    print(f"\n{Colors.HEADER}Test Summary:{Colors.ENDC}")
    print(f"Total combinations tested: {results['total']}")
    print(f"Skipped combinations: {results['skipped']} (invalid combinations)")
    
    if results['total'] > results['skipped']:
        print(f"Tests passed: {results['passed']}/{results['total'] - results['skipped']} "
              f"({100 * results['passed']/(results['total'] - results['skipped']):.1f}%)")
        print(f"Tests failed: {results['failed']}/{results['total'] - results['skipped']} "
              f"({100 * results['failed']/(results['total'] - results['skipped']):.1f}%)")
        
        print(f"\nSingle-page report tests passed: {results['single_page']['passed']}/{results['single_page']['passed'] + results['single_page']['failed']}")
        print(f"Multi-page report tests passed: {results['multi_page']['passed']}/{results['multi_page']['passed'] + results['multi_page']['failed']}")
    
    print(f"\nTotal test duration: {duration:.2f} seconds")
    
    # Return success if all tests passed
    return results['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)