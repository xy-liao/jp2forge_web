"""
JP2Forge Adapter Module

This module provides a compatibility layer between JP2Forge Web and the JP2Forge library.
It handles differences in API and provides fallback implementations when necessary.
"""

import os
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, Union, List
from django.conf import settings

# Configure logging
logger = logging.getLogger(__name__)

# Try to import JP2Forge modules
try:
    from core.types import WorkflowConfig, CompressionMode, DocumentType
    from workflow.standard import StandardWorkflow
    JP2FORGE_AVAILABLE = True
    logger.info("Successfully imported JP2Forge modules")
except ImportError as e:
    JP2FORGE_AVAILABLE = False
    logger.error(f"Failed to import JP2Forge modules: {e}")

# Check if mock mode is enabled in settings
MOCK_MODE = getattr(settings, 'JP2FORGE_SETTINGS', {}).get('MOCK_MODE', False)
if MOCK_MODE:
    logger.info("JP2Forge mock mode is enabled in settings")

class JP2ForgeResult:
    """
    Standardized result object for JP2Forge conversions, regardless of actual JP2Forge version.
    Ensures consistent interface for the web application.
    """
    def __init__(self, 
                 output_file: Union[str, List[str]], 
                 file_sizes: Dict[str, Any] = None,
                 metrics: Dict[str, Any] = None,
                 success: bool = True,
                 error: str = None):
        self.output_file = output_file  # Path to output file(s)
        self.file_sizes = file_sizes or {}  # File size information
        self.metrics = metrics or {}  # Quality metrics (PSNR, SSIM, etc.)
        self.success = success  # Conversion success flag
        self.error = error  # Error message if any

class JP2ForgeAdapter:
    """
    Adapter class for JP2Forge library to provide a consistent interface
    regardless of the actual JP2Forge version installed.
    """
    
    def __init__(self):
        """Initialize the adapter and check JP2Forge availability"""
        self.jp2forge_available = JP2FORGE_AVAILABLE and not MOCK_MODE
        if MOCK_MODE:
            logger.info("JP2Forge adapter running in mock mode")
        elif not JP2FORGE_AVAILABLE:
            logger.warning("JP2Forge is not available, will use mock mode when needed")
        else:
            logger.info("JP2Forge adapter initialized with actual library")
        
    def create_config(self, **kwargs) -> Any:
        """
        Create a configuration object compatible with the installed JP2Forge version.
        Handles parameter name differences and missing parameters.
        
        Args:
            **kwargs: Parameters for WorkflowConfig
            
        Returns:
            WorkflowConfig object or None if JP2Forge is not available
        """
        if not self.jp2forge_available:
            logger.error("Cannot create config: JP2Forge is not available")
            return None
        
        # Essential parameters that must be present
        required_params = ['output_dir', 'report_dir', 'compression_mode', 'document_type']
        for param in required_params:
            if param not in kwargs:
                logger.error(f"Missing required parameter: {param}")
                return None
        
        # Check which parameters are actually supported by the WorkflowConfig in this version
        import inspect
        supported_params = list(inspect.signature(WorkflowConfig.__init__).parameters.keys())
        # Remove 'self' from the list
        if 'self' in supported_params:
            supported_params.remove('self')
            
        logger.info(f"Supported WorkflowConfig parameters: {', '.join(supported_params)}")
        
        # Map potential parameter name variations
        param_mappings = {
            'keep_temp': ['temp_dir', 'tmp_dir', 'temporary_dir'],
            'keep_intermediates': ['save_intermediates'],
        }
        
        # Create a clean dictionary for parameters that will actually be used
        config_params = {}
        used_params = set()
        
        # First, handle exact matches with supported parameters
        for param_name in supported_params:
            if param_name in kwargs:
                config_params[param_name] = kwargs[param_name]
                used_params.add(param_name)
                logger.info(f"Using parameter {param_name} directly")
        
        # Then, try to map any remaining parameters if their target is supported
        for target_param, variation_list in param_mappings.items():
            # Only consider this mapping if the target parameter is supported
            if target_param in supported_params and target_param not in config_params:
                # Check if any of the variations are in the provided kwargs
                for variation in variation_list:
                    if variation in kwargs and variation not in used_params:
                        config_params[target_param] = kwargs[variation]
                        used_params.add(variation)
                        logger.info(f"Mapped parameter {variation} to {target_param}")
                        break
        
        # Special handling for enum parameters
        if 'compression_mode' in config_params and isinstance(config_params['compression_mode'], str):
            try:
                config_params['compression_mode'] = getattr(CompressionMode, config_params['compression_mode'].upper())
                logger.info(f"Converted compression_mode string to enum: {config_params['compression_mode']}")
            except (AttributeError, TypeError) as e:
                logger.error(f"Failed to convert compression_mode to enum: {e}")
        
        if 'document_type' in config_params and isinstance(config_params['document_type'], str):
            try:
                config_params['document_type'] = getattr(DocumentType, config_params['document_type'].upper())
                logger.info(f"Converted document_type string to enum: {config_params['document_type']}")
            except (AttributeError, TypeError) as e:
                logger.error(f"Failed to convert document_type to enum: {e}")
        
        # Log any parameters that were provided but not used
        unused_params = set(kwargs.keys()) - used_params
        if unused_params:
            logger.warning(f"The following parameters were provided but not used because they're not supported: {', '.join(unused_params)}")
        
        try:
            logger.info(f"Creating WorkflowConfig with parameters: {config_params}")
            return WorkflowConfig(**config_params)
        except Exception as e:
            logger.error(f"Error creating WorkflowConfig: {e}")
            return None
    
    def process_file(self, 
                    config: Any, 
                    input_path: str, 
                    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> JP2ForgeResult:
        """
        Process a file with JP2Forge, handling API differences between versions.
        
        Args:
            config: WorkflowConfig object
            input_path: Path to input file
            progress_callback: Optional callback function for progress updates
            
        Returns:
            JP2ForgeResult object with conversion results
        """
        # Use mock mode if explicitly enabled or if JP2Forge is not available
        if MOCK_MODE or not self.jp2forge_available:
            logger.info(f"Using mock conversion for {input_path} (MOCK_MODE={MOCK_MODE}, JP2FORGE_AVAILABLE={JP2FORGE_AVAILABLE})")
            # Extract output directory from config
            output_dir = getattr(config, 'output_dir', os.path.join(settings.MEDIA_ROOT, 'jobs'))
            return self.mock_conversion(input_path, output_dir, progress_callback)
            
        if not config:
            logger.error("Cannot process file: Invalid configuration")
            return JP2ForgeResult(None, success=False, error="Invalid configuration")
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return JP2ForgeResult(None, success=False, error=f"Input file not found: {input_path}")
        
        try:
            workflow = StandardWorkflow(config)
            logger.info("Created StandardWorkflow successfully")
            
            # Check if progress tracking is supported
            import inspect
            process_file_signature = inspect.signature(workflow.process_file)
            supports_progress = 'progress_callback' in process_file_signature.parameters
            
            # If progress tracking is supported, use it directly
            if supports_progress:
                logger.info("Using process_file with progress tracking")
                result = workflow.process_file(input_path, progress_callback=progress_callback)
            else:
                # Otherwise, use a background thread to simulate progress updates
                logger.info("Progress tracking not supported, using background thread")
                progress_thread = None
                stop_event = threading.Event()
                
                if progress_callback:
                    # Start a background thread to simulate progress updates
                    def update_progress_thread():
                        progress = 0
                        steps = ['init', 'analyze', 'convert', 'optimize', 'finalize']
                        current_step_index = 0
                        step_progress = [0, 10, 30, 60, 80] # Progress percentage at which each step starts
                        
                        # Initial update
                        progress_callback({'percent_complete': 0, 'current_step': steps[0]})
                        time.sleep(0.2)
                        
                        while progress < 99 and not stop_event.is_set():
                            # Calculate progress increment - faster at beginning, slower near end
                            if progress < 30:
                                increment = 0.8  # Faster progress during initialization/analysis
                            elif progress < 70:
                                increment = 0.5  # Medium speed during conversion
                            else:
                                increment = 0.2  # Slowdown during optimization/finalization
                                
                            progress += increment
                            
                            # Determine the current step based on progress
                            while (current_step_index < len(steps) - 1 and 
                                  progress >= step_progress[current_step_index + 1]):
                                current_step_index += 1
                            
                            # Send progress update with current step
                            progress_callback({
                                'percent_complete': min(progress, 99), 
                                'current_step': steps[current_step_index]
                            })
                            
                            # More frequent updates - 100-200ms between updates
                            time.sleep(0.1 + (progress / 200))  # Slightly increase delay as progress increases
                    
                    progress_thread = threading.Thread(target=update_progress_thread)
                    progress_thread.daemon = True  # Thread won't block process exit
                    progress_thread.start()
                
                try:
                    # Process the file without progress callback
                    result = workflow.process_file(input_path)
                finally:
                    # Stop the progress thread if it was started
                    if progress_thread:
                        stop_event.set()
                        # Send one final 99% update (we'll set 100% after we know it succeeded)
                        if progress_callback:
                            progress_callback({'percent_complete': 99})
            
            # Extract result information
            output_file = getattr(result, 'output_file', None)
            file_sizes = getattr(result, 'file_sizes', {})
            metrics = getattr(result, 'metrics', {})
            
            # Final progress update
            if progress_callback:
                progress_callback({'percent_complete': 100})
            
            return JP2ForgeResult(
                output_file=output_file,
                file_sizes=file_sizes,
                metrics=metrics,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return JP2ForgeResult(None, success=False, error=str(e))

    @staticmethod
    def mock_conversion(input_path: str, output_dir: str, 
                       progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> JP2ForgeResult:
        """
        Create a mock conversion when JP2Forge is not available or for testing.
        
        Args:
            input_path: Path to input file
            output_dir: Directory for output files
            progress_callback: Optional callback function for progress updates
            
        Returns:
            JP2ForgeResult with mock conversion results
        """
        import time
        import os
        import shutil
        
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return JP2ForgeResult(None, success=False, error=f"Input file not found: {input_path}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Get input file size
        input_size = os.path.getsize(input_path)
        
        # Simulate conversion progress
        total_steps = 10
        for i in range(total_steps + 1):
            if progress_callback:
                progress_callback({'percent_complete': i * (100 / total_steps)})
            time.sleep(0.3)  # Simulate work
        
        # Get the base filename
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_file = os.path.join(output_dir, f"{base_name}.jp2")
        
        # Try to copy the file as a mock "conversion"
        try:
            shutil.copy(input_path, output_file)
        except Exception as e:
            # If copy fails (e.g., incompatible format), create an empty file
            with open(output_file, 'wb') as f:
                f.write(b'MOCK JP2 FILE CONVERSION')
        
        # Calculate mock file sizes and compression ratio
        output_size = os.path.getsize(output_file)
        compression_ratio = input_size / output_size if output_size > 0 else 1.0
        
        # Prepare mock result
        file_sizes = {
            'original_size': input_size,
            'converted_size': output_size,
            'compression_ratio': f"{compression_ratio:.2f}:1"
        }
        
        metrics = {
            'psnr': 40.0,  # Mock PSNR value
            'ssim': 0.95,  # Mock SSIM value
        }
        
        return JP2ForgeResult(
            output_file=output_file,
            file_sizes=file_sizes,
            metrics=metrics,
            success=True
        )

# Create a singleton instance
adapter = JP2ForgeAdapter()