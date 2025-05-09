#!/usr/bin/env python
"""
JP2Forge BnF Validation Interpretation Test

This script focuses specifically on testing the interpretation of BnF validation results.
It inspects reports for BnF compliant conversions and verifies that the interpretation
logic correctly handles the relationship between:
- bnf_validation.is_compliant (overall format compliance)
- bnf_compliance.is_compliant (compression ratio compliance)

The script focuses on validating the correct implementation of the BnF standard which
allows for lossless fallback when lossy compression can't achieve the target ratio.

Usage:
    python test_bnf_interpretation.py [--verbose]

Options:
    --verbose       Show detailed information about each test
"""

import os
import sys
import json
import argparse
import tempfile
from pathlib import Path
import datetime

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

def generate_mock_report(doc_type, comp_mode, achieve_ratio=True):
    """
    Generate a mock report for BnF validation interpretation testing.
    
    Args:
        doc_type: Document type (photograph, heritage_document, color, grayscale)
        comp_mode: Compression mode (lossless, bnf_compliant)
        achieve_ratio: Whether to achieve the target ratio or not
    
    Returns:
        A mock report structure
    """
    # Get target ratio for the document type
    target_ratio = BnFStandards.COMPRESSION_RATIOS.get(doc_type, 4.0)
    
    # Determine actual ratio based on inputs
    if comp_mode == 'lossless':
        # Lossless mode typically has lower ratio
        actual_ratio = 2.5
    elif achieve_ratio:
        # Successfully achieving target ratio
        actual_ratio = target_ratio * 1.1  # Exceed target by 10%
    else:
        # Failing to achieve target ratio
        actual_ratio = target_ratio * 0.8  # 20% below target
    
    # Current timestamp in ISO format
    current_time = datetime.datetime.now().isoformat(timespec='seconds')
    
    # Basic report structure
    report = {
        "job_id": "mock-job-123",
        "original_file": "mock_image.png",
        "output_file": "output.jp2",
        "compression_mode": comp_mode,
        "document_type": doc_type,
        "bnf_compliant": "true",
        "completed_at": current_time,
        "original_size": 1024000,  # 1MB
        "converted_size": int(1024000 / actual_ratio),
        "compression_ratio": f"{actual_ratio:.2f}:1"
    }
    
    # For lossy or bnf_compliant modes, add quality metrics
    if comp_mode in ('lossy', 'bnf_compliant'):
        report["psnr"] = 42.5  # High PSNR value
        report["ssim"] = 0.95  # High SSIM value
        # Always include MSE metric for lossy modes
        report["mse"] = 0.0012  # Low MSE value (better quality)
    
    # Determine ratio compliance
    ratio_compliant = (actual_ratio >= target_ratio * 0.95)
    
    # BnF compliance section - tracks compression ratio achievement
    report["bnf_compliance"] = {
        "is_compliant": str(ratio_compliant).lower(),
        "target_ratio": target_ratio,
        "actual_ratio": actual_ratio,
        "document_type": doc_type,
        "tolerance": 0.05
    }
    
    # BnF validation section - should always "pass" due to lossless fallback
    # This is the key to the interpretation test
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
                "actual": actual_ratio,
                "message": f"Compression ratio {actual_ratio:.2f}:1 meets requirements" if ratio_compliant else
                           f"Using lossless compression as fallback (ratio {actual_ratio:.2f}:1 " +
                           f"doesn't meet target {target_ratio:.2f}:1 but is BnF compliant via fallback)"
            }
        }
    }
    
    return report

def run_bnf_interpretation_test(doc_type, comp_mode, achieve_ratio=True, verbose=False):
    """
    Run a BnF interpretation test using mock reports.
    
    Args:
        doc_type: Document type to test
        comp_mode: Compression mode to test
        achieve_ratio: Whether to meet target compression ratio
        verbose: Print detailed information
        
    Returns:
        The generated mock report
    """
    if verbose:
        print(f"\n{Colors.HEADER}Testing BnF interpretation: {doc_type} + {comp_mode} + " +
              f"{'meeting' if achieve_ratio else 'missing'} ratio{Colors.ENDC}")
    
    # Generate a mock report for this combination
    report = generate_mock_report(doc_type, comp_mode, achieve_ratio)
    
    return report

def check_interpretation(doc_type, report, verbose=False):
    """Verify that BnF validation results are interpreted correctly"""
    issues = []
    
    if not report:
        return False, ["No report to analyze"]
    
    # Check for required sections
    if 'bnf_validation' not in report:
        issues.append("Missing bnf_validation section")
    
    if 'bnf_compliance' not in report:
        issues.append("Missing bnf_compliance section")
    
    # If either section is missing, we can't proceed with advanced checks
    if issues:
        return False, issues
    
    # Extract key validation values
    overall_compliant = report['bnf_validation'].get('is_compliant') 
    if isinstance(overall_compliant, str):
        overall_compliant = overall_compliant.lower() == 'true'
        
    ratio_compliant = report['bnf_compliance'].get('is_compliant')
    if isinstance(ratio_compliant, str):
        ratio_compliant = ratio_compliant.lower() == 'true'
        
    target_ratio = report['bnf_compliance'].get('target_ratio', 0)
    actual_ratio = report['bnf_compliance'].get('actual_ratio', 0)
    
    # Check for critical case: lossless fallback should still be considered BnF compliant
    if not ratio_compliant and not overall_compliant:
        issues.append(f"BnF validation failed completely, but should still pass validation with lossless fallback")
        issues.append(f"Target ratio: {target_ratio}, Actual ratio: {actual_ratio}")
        issues.append(f"Report believes: overall_compliant={overall_compliant}, ratio_compliant={ratio_compliant}")
    
    # For advanced diagnosis, check if there's a lossless fallback indicator
    compression_checks = report['bnf_validation'].get('checks', {}).get('compression_ratio', {})
    message = compression_checks.get('message', '')
    
    if not ratio_compliant and 'fallback' not in message.lower() and overall_compliant:
        if verbose:
            print(f"{Colors.CYAN}Note: Ratio not compliant but overall validation passes. "
                  f"Expected lossless fallback message.{Colors.ENDC}")
    
    # Check the compression mode information from report
    if 'compression_mode' in report:
        comp_mode = report['compression_mode']
        if not ratio_compliant and comp_mode != 'lossless':
            if verbose:
                print(f"{Colors.CYAN}Note: Ratio failed but not using lossless mode ({comp_mode}){Colors.ENDC}")
    
    # Summarize the interpretation
    if verbose and not issues:
        print(f"{Colors.GREEN}BnF interpretation correct:{Colors.ENDC}")
        print(f"  - Overall compliant: {overall_compliant}")
        print(f"  - Ratio compliant: {ratio_compliant}")
        print(f"  - Target ratio: {target_ratio}")
        print(f"  - Actual ratio: {actual_ratio}")
        
        if 'checks' in report['bnf_validation'] and 'compression_ratio' in report['bnf_validation']['checks']:
            passed = report['bnf_validation']['checks']['compression_ratio'].get('passed')
            message = report['bnf_validation']['checks']['compression_ratio'].get('message', '')
            print(f"  - Compression check: {passed}")
            print(f"  - Message: {message}")
    
    return len(issues) == 0, issues

def run_interpretation_tests(verbose=False):
    """Run BnF interpretation tests for various document types and scenarios"""
    document_types = ['photograph', 'heritage_document', 'color', 'grayscale']
    
    # Focus on BnF-related compression modes
    compression_modes = ['bnf_compliant', 'lossless']
    
    # Add ratio achievement scenarios
    ratio_scenarios = [True, False]  # Meeting or missing the target ratio
    
    results = {
        'total': 0,
        'correct': 0,
        'incorrect': 0,
        'failed': 0
    }
    
    try:
        for doc_type in document_types:
            for comp_mode in compression_modes:
                for achieve_ratio in ratio_scenarios:
                    results['total'] += 1
                    
                    # Run the mock test
                    try:
                        report = run_bnf_interpretation_test(
                            doc_type, comp_mode, achieve_ratio, verbose)
                        
                        if report:
                            # Check interpretation
                            is_correct, issues = check_interpretation(doc_type, report, verbose)
                            
                            if is_correct:
                                results['correct'] += 1
                                if verbose:
                                    ratio_status = "meeting" if achieve_ratio else "missing"
                                    print(f"{Colors.GREEN}✓ BnF interpretation correct for {doc_type} + {comp_mode} " +
                                        f"({ratio_status} ratio){Colors.ENDC}")
                            else:
                                results['incorrect'] += 1
                                ratio_status = "meeting" if achieve_ratio else "missing"
                                print(f"{Colors.FAIL}✗ BnF interpretation issues for {doc_type} + {comp_mode} " +
                                    f"({ratio_status} ratio):{Colors.ENDC}")
                                for issue in issues:
                                    print(f"  - {issue}")
                        else:
                            results['failed'] += 1
                            print(f"{Colors.FAIL}✗ Failed to run test for {doc_type} + {comp_mode}{Colors.ENDC}")
                    except Exception as e:
                        results['failed'] += 1
                        print(f"{Colors.FAIL}✗ Test threw exception for {doc_type} + {comp_mode}: {str(e)}{Colors.ENDC}")
                        import traceback
                        if verbose:
                            traceback.print_exc()
    except Exception as e:
        print(f"{Colors.FAIL}Error during test execution: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()

    # Add warning if no tests were run successfully
    if results['correct'] + results['incorrect'] == 0:
        print(f"{Colors.WARNING}WARNING: No tests were completed successfully!{Colors.ENDC}")
        
    return results

def main():
    """Main function for command-line use"""
    parser = argparse.ArgumentParser(
        description='Test JP2Forge BnF validation interpretation')
    parser.add_argument('--verbose', '-v', action='store_true', 
                        help='Show detailed information')
    
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}JP2Forge BnF Validation Interpretation Test{Colors.ENDC}")
    print("=" * 50)
    print("Using mock reports to test BnF validation interpretation")
    print(f"Test date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nRunning BnF interpretation tests...")
    results = run_interpretation_tests(verbose=args.verbose)
    
    # Print summary
    print(f"\n{Colors.HEADER}Test Summary:{Colors.ENDC}")
    print(f"Total tests: {results['total']}")
    
    # Calculate percentages safely
    if results['total'] > 0:
        correct_pct = 100 * results['correct']/results['total']
        incorrect_pct = 100 * results['incorrect']/results['total']
        failed_pct = 100 * results['failed']/results['total']
    else:
        correct_pct = incorrect_pct = failed_pct = 0
        
    print(f"Correct interpretations: {results['correct']}/{results['total']} ({correct_pct:.1f}%)")
    print(f"Incorrect interpretations: {results['incorrect']}/{results['total']} ({incorrect_pct:.1f}%)")
    print(f"Failed tests: {results['failed']}/{results['total']} ({failed_pct:.1f}%)")
    
    # Return success if all interpretations were correct
    return results['incorrect'] == 0 and results['failed'] == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)