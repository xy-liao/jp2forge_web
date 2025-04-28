#!/usr/bin/env python
"""
Test script for JP2Forge library functionality

This script tests if the JP2Forge library is working correctly in your
Python environment by attempting a minimal conversion operation.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jp2forge_test")

def test_jp2forge_imports():
    """Test if JP2Forge modules can be imported"""
    try:
        from core.types import WorkflowConfig, CompressionMode, DocumentType
        from workflow.standard import StandardWorkflow
        logger.info("✓ Successfully imported JP2Forge modules")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import JP2Forge modules: {e}")
        return False

def get_workflow_config_params():
    """Get the WorkflowConfig parameters to understand what's supported"""
    try:
        import inspect
        from core.types import WorkflowConfig
        
        params = inspect.signature(WorkflowConfig.__init__).parameters
        param_names = list(params.keys())
        logger.info(f"Available WorkflowConfig parameters: {', '.join(param_names[1:])}")  # Skip 'self'
        return param_names[1:]  # Return all param names except 'self'
    except Exception as e:
        logger.error(f"Error examining WorkflowConfig parameters: {e}")
        return []

def test_minimal_conversion(input_file, output_dir):
    """Attempt a minimal JP2FORGE conversion operation"""
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        return False
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    try:
        from core.types import WorkflowConfig, CompressionMode, DocumentType
        from workflow.standard import StandardWorkflow
        
        # Create minimal config
        config = WorkflowConfig(
            output_dir=output_dir,
            report_dir=output_dir,
            compression_mode=CompressionMode.SUPERVISED,
            document_type=DocumentType.PHOTOGRAPH
        )
        
        logger.info("Created WorkflowConfig successfully")
        
        # Progress callback
        def progress_callback(progress_data):
            logger.info(f"Progress: {progress_data.get('percent_complete', 0)}%")
        
        # Process file
        workflow = StandardWorkflow(config)
        logger.info("Starting conversion...")
        result = workflow.process_file(input_file, progress_callback=progress_callback)
        logger.info("Conversion completed successfully!")
        
        # Check result
        if hasattr(result, 'output_file'):
            if isinstance(result.output_file, list):
                logger.info(f"Created {len(result.output_file)} output files")
                for f in result.output_file:
                    logger.info(f"  - {f}")
            else:
                logger.info(f"Created output file: {result.output_file}")
        
        return True
    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_mock_conversion(input_file, output_dir):
    """
    Test a mock conversion process for development/testing
    when the actual JP2Forge library is not working correctly
    """
    import time
    import shutil
    from PIL import Image
    
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get base filename without extension
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(output_dir, f"{base_name}.jp2")
        
        # Simple progress simulation
        for i in range(0, 101, 10):
            logger.info(f"Mock conversion progress: {i}%")
            time.sleep(0.5)
        
        # Create a blank "JP2" file (it won't actually be a valid JP2)
        try:
            # First try to use PIL to read and save the image
            img = Image.open(input_file)
            img.save(output_file.replace('.jp2', '.png'))
            logger.info(f"Created mock PNG output: {output_file.replace('.jp2', '.png')}")
            
            # Create an empty JP2 file
            with open(output_file, 'wb') as f:
                f.write(b'MOCK JP2 FILE')
                
            logger.info(f"Created mock output: {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error in mock conversion: {e}")
            # Fallback - just create an empty file
            with open(output_file, 'wb') as f:
                f.write(b'MOCK JP2 FILE')
            logger.info(f"Created empty mock output: {output_file}")
            return True
            
    except Exception as e:
        logger.error(f"Error in mock conversion: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=== JP2Forge Library Test ===")
    
    # Test imports
    if not test_jp2forge_imports():
        logger.error("JP2Forge import test failed. Cannot continue.")
        sys.exit(1)
    
    # Get WorkflowConfig parameters
    config_params = get_workflow_config_params()
    
    # Check for test files
    input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media", "jobs")
    
    # Find any TIFF files in the media/jobs directory
    tiff_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.tif', '.tiff')):
                tiff_files.append(os.path.join(root, file))
    
    if not tiff_files:
        logger.error("No TIFF files found for testing in the media/jobs directory.")
        sys.exit(1)
    
    # Choose the first TIFF file for testing
    test_file = tiff_files[0]
    logger.info(f"Using test file: {test_file}")
    
    # Create test output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Test real conversion
    logger.info("\n=== Testing actual JP2Forge conversion ===")
    real_result = test_minimal_conversion(test_file, output_dir)
    
    # If real conversion fails, try mock conversion
    if not real_result:
        logger.info("\n=== Testing mock conversion (fallback) ===")
        mock_result = test_mock_conversion(test_file, output_dir)
        if mock_result:
            logger.info("Mock conversion successful. Consider using mock mode for development/testing.")
    
    logger.info("Test completed.")

if __name__ == "__main__":
    main()