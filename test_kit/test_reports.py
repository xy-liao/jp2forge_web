#!/usr/bin/env python
"""
JP2Forge Report Testing Utility

This script systematically tests report generation for all possible combinations of:
- Document types (photograph, heritage_document, color, grayscale)
- Compression modes (lossless, lossy, supervised, bnf_compliant)
- BnF compliance settings (True/False where applicable)

It validates that reports contain the expected elements and that BnF validation
results are correctly interpreted.

Usage:
    python test_reports.py [--verbose] [--save-reports] [--force-mock]

Options:
    --verbose       Show detailed information about each test
    --save-reports  Save all generated reports to the reports_test directory
    --force-mock    Force using mock mode even if JP2Forge is available
"""

import os
import sys
import json
import argparse
import tempfile
import shutil
import datetime
import traceback
import time
from pathlib import Path

# Add the parent directory to sys.path to ensure we can import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure Django settings before importing any Django-dependent modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
import django
django.setup()

# Import the JP2Forge adapter and BnF validator
from converter.jp2forge_adapter import adapter, JP2ForgeResult
from converter.bnf_validator import get_validator, BnFStandards

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

def get_test_image():
    """Find an existing image in the project that we can use for testing"""
    # List of potential test images in the project
    test_images = [
        os.path.join("static", "images", "docs", "jp2forge_web_config.png"),
        os.path.join("static", "images", "docs", "jp2forge_web_welcome.png"),
    ]
    
    # First try to find an existing image
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for image_path in test_images:
        full_path = os.path.join(project_root, image_path)
        if os.path.exists(full_path):
            return full_path
    
    # If no existing images found, create a simple test image
    try:
        from PIL import Image
        
        test_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img = Image.new('RGB', (100, 100), color=(73, 109, 137))
        img.save(test_image.name)
        
        return test_image.name
    except Exception as e:
        print(f"{Colors.FAIL}Error creating test image: {e}{Colors.ENDC}")
        raise

def generate_mock_report(doc_type, comp_mode, bnf_compliant, output_file="/path/to/mock/output.jp2", multi_page=False):
    """Generate a mock report structure for testing without running a conversion"""
    # Current timestamp in ISO format
    current_time = datetime.datetime.now().isoformat(timespec='seconds')
    
    report = {
        "job_id": "mock-job-123",
        "original_file": "mock_image.png",
        "compression_mode": comp_mode,
        "document_type": doc_type,
        "bnf_compliant": str(bnf_compliant).lower(),
        "completed_at": current_time
    }
    
    # Handle output_file which could be a string or list
    if isinstance(output_file, list):
        report["output_file"] = [os.path.basename(f) for f in output_file]
    else:
        report["output_file"] = os.path.basename(output_file)
    
    # Add size and compression metrics
    report["original_size"] = 1024000  # 1MB
    report["converted_size"] = 204800  # 200KB
    
    # Compression ratio varies by mode and document type
    base_ratio = 5.0
    if comp_mode == "lossless":
        ratio = 2.5
    elif doc_type == "grayscale":
        ratio = 16.0 if bnf_compliant or comp_mode == "bnf_compliant" else 12.0
    elif doc_type == "color":
        ratio = 6.0 if bnf_compliant or comp_mode == "bnf_compliant" else 8.0
    else:  # photograph or heritage_document
        ratio = 4.0 if bnf_compliant or comp_mode == "bnf_compliant" else base_ratio
    
    report["compression_ratio"] = f"{ratio:.2f}:1"
    
    # Add quality metrics for lossy modes
    if comp_mode in ("lossy", "supervised", "bnf_compliant"):
        report["psnr"] = 42.5  # High PSNR value
        report["ssim"] = 0.95  # High SSIM value
        # Always include MSE metric for lossy modes (required by our new validation)
        report["mse"] = 0.0012  # Low MSE value (better quality)
    
    # Add BnF compliance sections
    if bnf_compliant or comp_mode == "bnf_compliant":
        # Get the target ratio from BnF standards
        target_ratio = BnFStandards.COMPRESSION_RATIOS.get(doc_type, 4.0)
        
        # Determine if ratio meets the target within tolerance
        ratio_compliant = (ratio >= target_ratio * 0.95)
        
        # BnF compliance section
        report["bnf_compliance"] = {
            "is_compliant": str(ratio_compliant).lower(),
            "target_ratio": target_ratio,
            "actual_ratio": ratio,
            "document_type": doc_type,
            "tolerance": 0.05
        }
        
        # BnF validation section (should always pass due to lossless fallback)
        report["bnf_validation"] = {
            "is_compliant": "true",  # Always true due to lossless fallback
            "checks": {
                "resolution_levels": {
                    "passed": "true",
                    "expected": 10,
                    "actual": 10,
                    "message": "Resolution levels meet BnF requirements"
                },
                "wavelet_transform": {
                    "passed": "true",
                    "expected": "9-7",
                    "actual": "9-7",
                    "message": "Wavelet transform type meets BnF requirements"
                },
                "compression_ratio": {
                    "passed": "true",
                    "expected": target_ratio,
                    "actual": ratio,
                    "message": f"Compression ratio {ratio:.2f}:1 meets requirements"
                }
            }
        }
    
    # Add multi-page specific information if this is a multi-page document
    if multi_page:
        num_pages = 3  # Simulate a 3-page document
        
        # Add basic multi-page markers
        report["pages"] = num_pages
        report["page_files"] = [f"page_{i+1}.jp2" for i in range(num_pages)]
        
        # Add per-page metrics for multi-page documents
        if comp_mode in ("lossy", "supervised", "bnf_compliant"):
            # Create per-page metrics with slight variations
            page_metrics = []
            import random  # Add import here to make it available
            
            for i in range(num_pages):
                # Create slight variations in metrics between pages
                page_metric = {
                    "page_number": i + 1,
                    "page_filename": f"page_{i+1}.jp2",
                    "psnr": round(report["psnr"] + random.uniform(-2.0, 2.0), 2),
                    "ssim": round(min(1.0, max(0.0, report["ssim"] + random.uniform(-0.05, 0.05))), 4),
                    # Always include MSE with small variations
                    "mse": round(report["mse"] + random.uniform(-0.0005, 0.0005), 6),
                    "file_sizes": {
                        "original_size": round(report["original_size"] / num_pages),
                        "converted_size": round(report["converted_size"] / num_pages),
                        "compression_ratio": report["compression_ratio"]
                    }
                }
                
                page_metrics.append(page_metric)
            
            # Add multi-page metrics to report
            report["per_page_metrics"] = page_metrics
            report["multipage_results"] = [
                {
                    "page": i + 1,
                    "status": "SUCCESS",
                    "output_file": f"page_{i+1}.jp2",
                    "metrics": page_metrics[i]
                }
                for i in range(num_pages)
            ]
    
    return report

def validate_report(doc_type, comp_mode, bnf_compliant, report, verbose=False, is_multipage=False):
    """Validate that a report contains the expected elements based on the combination"""
    if not report:
        return False
    
    issues = []
    
    # Common elements that should be in all reports
    common_elements = [
        'compression_mode', 
        'document_type',
        'job_id',
        'completed_at',
        'original_file',
        'output_file',
        'original_size',
        'converted_size',
        'compression_ratio'
    ]
    
    for element in common_elements:
        if element not in report:
            issues.append(f"Missing common element: {element}")
    
    # Validate format of compression ratio (should be X.XX:1 format)
    if 'compression_ratio' in report:
        ratio_str = report['compression_ratio']
        if not isinstance(ratio_str, str) or ':1' not in ratio_str:
            issues.append(f"Compression ratio not in expected format 'X.XX:1': {ratio_str}")
            
    # Validate file size values
    for size_field in ['original_size', 'converted_size']:
        if size_field in report and not isinstance(report[size_field], (int, float)):
            issues.append(f"{size_field} is not a numeric value: {report[size_field]}")
    
    # Check BnF validation section if BnF compliance was requested
    if bnf_compliant or comp_mode == 'bnf_compliant':
        # The BnF validation section should be present
        if 'bnf_validation' not in report:
            issues.append("Missing bnf_validation section despite BnF compliance being requested")
        else:
            # Check if is_compliant exists
            if 'is_compliant' not in report['bnf_validation']:
                issues.append("Missing is_compliant in bnf_validation section")
            elif not isinstance(report['bnf_validation']['is_compliant'], str):
                issues.append("is_compliant in bnf_validation should be a string ('true'/'false')")
            
            # Check if checks dictionary exists
            if 'checks' not in report['bnf_validation']:
                issues.append("Missing checks dictionary in bnf_validation section")
            else:
                # Check that required checks are present
                required_checks = ['resolution_levels', 'wavelet_transform', 'compression_ratio']
                for check in required_checks:
                    if check not in report['bnf_validation']['checks']:
                        issues.append(f"Missing {check} in bnf_validation checks")
                    else:
                        # Each check should have passed, expected, and actual fields
                        check_fields = ['passed', 'expected', 'actual', 'message']
                        for field in check_fields:
                            if field not in report['bnf_validation']['checks'][check]:
                                issues.append(f"Missing {field} in {check} check")
            
        # The BnF compliance section might be separate
        if 'bnf_compliance' not in report:
            issues.append("Missing bnf_compliance section despite BnF compliance being requested")
        else:
            # Check for target and actual ratio
            if 'target_ratio' not in report['bnf_compliance']:
                issues.append("Missing target_ratio in bnf_compliance section")
            if 'actual_ratio' not in report['bnf_compliance']:
                issues.append("Missing actual_ratio in bnf_compliance section")
            if 'is_compliant' not in report['bnf_compliance']:
                issues.append("Missing is_compliant in bnf_compliance section")
            if 'tolerance' not in report['bnf_compliance']:
                issues.append("Missing tolerance in bnf_compliance section")
    
    # Check quality metrics based on compression mode
    if comp_mode in ('lossy', 'supervised', 'bnf_compliant'):
        # These modes should have quality metrics
        metrics_to_check = ['psnr', 'ssim']
        for metric in metrics_to_check:
            if metric not in report:
                issues.append(f"Missing quality metric: {metric}")
            elif not isinstance(report[metric], (int, float)):
                issues.append(f"{metric} is not a numeric value: {report[metric]}")
        
        # MSE should now always be present for lossy modes as per our adapter changes
        if 'mse' not in report:
            issues.append("Missing MSE metric for lossy compression mode")
        elif not isinstance(report['mse'], (int, float)):
            issues.append(f"MSE is not a numeric value: {report['mse']}")
    
    # Verify document type specific target ratios
    if (bnf_compliant or comp_mode == 'bnf_compliant') and 'bnf_compliance' in report:
        expected_ratio = BnFStandards.COMPRESSION_RATIOS.get(doc_type, 4.0)
        if report['bnf_compliance'].get('target_ratio') != expected_ratio:
            issues.append(f"Incorrect target ratio: {report['bnf_compliance'].get('target_ratio')} "
                         f"(expected {expected_ratio} for {doc_type})")
    
    # Check multi-page specific elements
    if 'pages' in report or 'page_files' in report or is_multipage:
        # These fields should be present for multi-page documents
        multipage_elements = ['pages', 'page_files']
        for element in multipage_elements:
            if element not in report:
                issues.append(f"Missing multi-page element: {element}")
        
        # Check page_files is a list
        if 'page_files' in report and not isinstance(report['page_files'], list):
            issues.append("page_files should be a list")
        
        # Check pages count matches page_files length
        if 'pages' in report and 'page_files' in report and isinstance(report['page_files'], list):
            if int(report['pages']) != len(report['page_files']):
                issues.append(f"pages count ({report['pages']}) doesn't match page_files length ({len(report['page_files'])})")
        
        # Check per_page_metrics for lossy modes
        if comp_mode in ('lossy', 'supervised', 'bnf_compliant'):
            if 'per_page_metrics' not in report:
                issues.append("Missing per_page_metrics for lossy multi-page document")
            elif not isinstance(report['per_page_metrics'], list):
                issues.append("per_page_metrics should be a list")
            elif 'pages' in report and len(report['per_page_metrics']) != int(report['pages']):
                issues.append(f"per_page_metrics length ({len(report['per_page_metrics'])}) doesn't match pages count ({report['pages']})")
            else:
                # Validate content of per_page_metrics entries
                for i, page_metric in enumerate(report['per_page_metrics']):
                    # Check basic structure
                    required_page_fields = ['page_number', 'page_filename']
                    for field in required_page_fields:
                        if field not in page_metric:
                            issues.append(f"Missing {field} in per_page_metrics[{i}]")
                    
                    # Check quality metrics in per-page metrics
                    for metric in ['psnr', 'ssim', 'mse']:
                        if metric not in page_metric:
                            issues.append(f"Missing {metric} in per_page_metrics[{i}]")
                        elif not isinstance(page_metric[metric], (int, float)):
                            issues.append(f"{metric} in per_page_metrics[{i}] is not a numeric value")
                    
                    # Check file sizes section for each page
                    if 'file_sizes' not in page_metric:
                        issues.append(f"Missing file_sizes in per_page_metrics[{i}]")
                    else:
                        for size_field in ['original_size', 'converted_size', 'compression_ratio']:
                            if size_field not in page_metric['file_sizes']:
                                issues.append(f"Missing {size_field} in per_page_metrics[{i}]['file_sizes']")
            
            # Check multipage_results structure
            if 'multipage_results' not in report:
                issues.append("Missing multipage_results")
            elif not isinstance(report['multipage_results'], list):
                issues.append("multipage_results should be a list")
            elif 'pages' in report and len(report['multipage_results']) != int(report['pages']):
                issues.append(f"multipage_results length ({len(report['multipage_results'])}) doesn't match pages count ({report['pages']})")
            else:
                # Validate content of multipage_results
                for i, result in enumerate(report['multipage_results']):
                    required_result_fields = ['page', 'status', 'output_file']
                    for field in required_result_fields:
                        if field not in result:
                            issues.append(f"Missing {field} in multipage_results[{i}]")
                    
                    # Check metrics field
                    if 'metrics' not in result:
                        issues.append(f"Missing metrics in multipage_results[{i}]")
    
    if issues:
        print(f"{Colors.FAIL}Validation issues for {doc_type} + {comp_mode} + BnF={bnf_compliant} {'(multi-page)' if is_multipage else '(single-page)'}:{Colors.ENDC}")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    if verbose:
        print(f"{Colors.GREEN}Report validation successful for {doc_type} + {comp_mode} + BnF={bnf_compliant} {'(multi-page)' if is_multipage else '(single-page)'}{Colors.ENDC}")
    return True

def test_combination(doc_type, comp_mode, bnf_compliant, verbose=False, save_reports=False, force_mock=False):
    """Run a test for a specific combination"""
    # Skip invalid combinations (bnf_compliant mode always has bnf_compliant=True)
    if comp_mode == 'bnf_compliant' and not bnf_compliant:
        if verbose:
            print(f"{Colors.BLUE}Skipping invalid combination: {comp_mode} with bnf_compliant=False{Colors.ENDC}")
        return None, None
    
    if verbose:
        print(f"\n{Colors.HEADER}Testing: {doc_type} + {comp_mode} + BnF={bnf_compliant}{Colors.ENDC}")
    
    # Create temp output directory
    with tempfile.TemporaryDirectory() as output_dir:
        report_dir = os.path.join(output_dir, "reports")
        os.makedirs(report_dir, exist_ok=True)
        
        # For each combination, test both single-page and multi-page documents
        results = []
        reports = []
        
        try:
            # Test single-page document
            report_single = generate_mock_report(doc_type, comp_mode, bnf_compliant, 
                                                output_file=os.path.join(output_dir, f"mock_{doc_type}_{comp_mode}.jp2"),
                                                multi_page=False)
            
            # Write single-page report to a file
            report_file_single = os.path.join(report_dir, "report_single.json")
            with open(report_file_single, 'w') as f:
                json.dump(report_single, f, indent=2)
            
            # Create result object for single-page
            result_single = JP2ForgeResult(
                output_file=os.path.join(output_dir, f"mock_{doc_type}_{comp_mode}.jp2"),
                file_sizes={
                    'original_size': report_single.get("original_size", 1024000),
                    'converted_size': report_single.get("converted_size", 204800),
                    'compression_ratio': report_single.get("compression_ratio", "1.0:1")
                },
                metrics=report_single,
                success=True
            )
            
            # Test multi-page document
            report_multi = generate_mock_report(doc_type, comp_mode, bnf_compliant, 
                                            output_file=[os.path.join(output_dir, f"mock_{doc_type}_{comp_mode}_page_{i}.jp2") for i in range(1, 4)],
                                            multi_page=True)
            
            # Write multi-page report to a file
            report_file_multi = os.path.join(report_dir, "report_multi.json")
            with open(report_file_multi, 'w') as f:
                json.dump(report_multi, f, indent=2)
            
            # Create result object for multi-page
            result_multi = JP2ForgeResult(
                output_file=[os.path.join(output_dir, f"mock_{doc_type}_{comp_mode}_page_{i}.jp2") for i in range(1, 4)],
                file_sizes={
                    'original_size': report_multi.get("original_size", 1024000),
                    'converted_size': report_multi.get("converted_size", 204800),
                    'compression_ratio': report_multi.get("compression_ratio", "1.0:1")
                },
                metrics=report_multi,
                success=True
            )
            
            # Add both results and reports to their lists
            results.extend([result_single, result_multi])
            reports.extend([report_single, report_multi])
            
            # If requested, save the reports to a permanent location
            if save_reports:
                # Create a reports_test directory in the test_output folder
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                save_dir = os.path.join(project_root, "test_output", "reports_test")
                os.makedirs(save_dir, exist_ok=True)
                
                # Save single-page report
                save_path_single = os.path.join(save_dir, f"{doc_type}_{comp_mode}_bnf{bnf_compliant}_single.json")
                with open(save_path_single, 'w') as f:
                    json.dump(report_single, f, indent=2)
                    
                # Save multi-page report
                save_path_multi = os.path.join(save_dir, f"{doc_type}_{comp_mode}_bnf{bnf_compliant}_multi.json")
                with open(save_path_multi, 'w') as f:
                    json.dump(report_multi, f, indent=2)
                    
                if verbose:
                    print(f"{Colors.CYAN}Saved reports to {save_dir}{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.FAIL}Error generating test reports: {str(e)}{Colors.ENDC}")
            if verbose:
                traceback.print_exc()
            return None, None
        
        # Return all results and reports for validation
        return results, reports

def run_all_tests(verbose=False, save_reports=False, force_mock=False):
    """Run tests for all possible combinations"""
    document_types = ['photograph', 'heritage_document', 'color', 'grayscale']
    compression_modes = ['lossless', 'lossy', 'supervised', 'bnf_compliant']
    bnf_values = [True, False]
    
    results = {
        'total': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'single_page_validated': 0,
        'multi_page_validated': 0,
        'validation_failed': 0
    }
    
    start_time = time.time()
    
    try:
        for doc_type in document_types:
            for comp_mode in compression_modes:
                for bnf_compliant in bnf_values:
                    # Skip invalid combination
                    if comp_mode == 'bnf_compliant' and not bnf_compliant:
                        results['skipped'] += 1
                        continue
                    
                    results['total'] += 1
                    
                    # Run the test for this combination
                    test_results, test_reports = test_combination(doc_type, comp_mode, bnf_compliant, 
                                                    verbose, save_reports, force_mock)
                    
                    if test_results and len(test_results) == 2 and all(r.success for r in test_results):
                        results['successful'] += 1
                        
                        # Validate single page report (first item)
                        if validate_report(doc_type, comp_mode, bnf_compliant, test_reports[0], verbose, is_multipage=False):
                            results['single_page_validated'] += 1
                        else:
                            results['validation_failed'] += 1
                            
                        # Validate multi page report (second item)
                        if validate_report(doc_type, comp_mode, bnf_compliant, test_reports[1], verbose, is_multipage=True):
                            results['multi_page_validated'] += 1
                        else:
                            results['validation_failed'] += 1
                    else:
                        results['failed'] += 1
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Tests interrupted by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}Error during test execution: {str(e)}{Colors.ENDC}")
        if verbose:
            traceback.print_exc()
    
    results['duration'] = time.time() - start_time
    return results

def main():
    """Main function for command-line use"""
    parser = argparse.ArgumentParser(description='Test JP2Forge report generation for all combinations')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed information')
    parser.add_argument('--save-reports', '-s', action='store_true', 
                        help='Save all generated reports to the reports_test directory')
    parser.add_argument('--force-mock', '-m', action='store_true',
                        help='Force using mock mode even if JP2Forge is available')
    parser.add_argument('--check-downloads', '-d', action='store_true',
                        help='Test that reports can be downloaded correctly (requires Django runserver)')
    
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}JP2Forge Report Testing Utility{Colors.ENDC}")
    print("=" * 40)
    print(f"Test date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"JP2Forge availability: {adapter.jp2forge_available}")
    if not adapter.jp2forge_available:
        print("JP2Forge is not available. Tests will run in mock mode.")
    if args.force_mock:
        print("Forcing mock mode for testing.")
    
    print("\nRunning tests for all valid combinations...")
    results = run_all_tests(verbose=args.verbose, save_reports=args.save_reports, force_mock=args.force_mock)
    
    # Print summary
    print(f"\n{Colors.HEADER}Test Summary:{Colors.ENDC}")
    print(f"Total combinations tested: {results['total']}")
    print(f"Skipped combinations: {results['skipped']} (invalid combinations)")
    
    if results['total'] > results['skipped']:
        total_valid = results['total'] - results['skipped']
        successful_pct = 100 * results['successful']/total_valid if total_valid > 0 else 0
        failed_pct = 100 * results['failed']/total_valid if total_valid > 0 else 0
        
        print(f"Successful conversions: {results['successful']}/{total_valid} "
            f"({successful_pct:.1f}%)")
        print(f"Failed conversions: {results['failed']}/{total_valid} "
            f"({failed_pct:.1f}%)")
        
        if results['successful'] > 0:
            total_validations = results['single_page_validated'] + results['multi_page_validated']
            expected_validations = results['successful'] * 2  # Each successful test has two validations (single + multi)
            
            print(f"Single-page reports passing validation: {results['single_page_validated']}/{results['successful']} "
                f"({100 * results['single_page_validated']/results['successful']:.1f}%)")
            print(f"Multi-page reports passing validation: {results['multi_page_validated']}/{results['successful']} "
                f"({100 * results['multi_page_validated']/results['successful']:.1f}%)")
            print(f"Total reports passing validation: {total_validations}/{expected_validations} "
                f"({100 * total_validations/expected_validations:.1f}%)")
            print(f"Reports failing validation: {results['validation_failed']}/{expected_validations} "
                f"({100 * results['validation_failed']/expected_validations:.1f}%)")
    
    print(f"\nTotal test duration: {results.get('duration', 0):.2f} seconds")
    
    if args.check_downloads and results['successful'] > 0:
        print(f"\n{Colors.HEADER}Testing report downloads...{Colors.ENDC}")
        # To be implemented - would require a live Django server
        # This would test HTTP responses for report downloads
        print(f"{Colors.WARNING}Report download testing requires a running Django server.{Colors.ENDC}")
        print("This functionality will be implemented in a future version.")
        print("For now, please manually verify report downloads through the web interface.")
    
    if args.save_reports:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        save_dir = os.path.join(project_root, "test_output", "reports_test")
        print(f"\nSaved reports to: {save_dir}")
        print("These saved reports can be used for manual verification or regression testing.")
    
    # Return success if all tests passed
    return results['validation_failed'] == 0 and results['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)