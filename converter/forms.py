"""Django forms for the JP2Forge Web converter application.

This module defines the form classes used for JPEG2000 conversion job creation
and configuration. The forms handle file uploads, compression settings, and
BnF compliance options with dynamic JavaScript behavior.
"""

from django import forms
from .models import ConversionJob
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML
from .bnf_validator import BnFStandards

class ConversionJobForm(forms.ModelForm):
    """Form for creating and configuring JPEG2000 conversion jobs.
    
    This form provides a comprehensive interface for users to upload files
    and configure conversion parameters including compression modes, document
    types, and BnF compliance settings. The form includes extensive JavaScript
    functionality for dynamic field behavior and real-time validation feedback.
    
    Features:
    - File upload with size and type validation
    - Dynamic compression mode selection with conditional fields
    - BnF compliance configuration with document type-specific ratios
    - Real-time quality setting adjustments
    - Interactive file list with size formatting
    - Responsive form layout using Crispy Forms
    
    Attributes:
        files (FileField): File upload field for source images
        Meta (class): Form metadata linking to ConversionJob model
        helper (FormHelper): Crispy Forms helper for layout and styling
    """
    # Simple file field without multiple attribute
    files = forms.FileField(
        required=True,
        help_text="Select an image file to convert to JPEG2000. Supported formats include JPEG, TIFF, PNG, and BMP."
    )
    
    class Meta:
        model = ConversionJob
        fields = ['compression_mode', 'document_type', 'bnf_compliant', 'quality']
        widgets = {
            'quality': forms.NumberInput(attrs={
                'min': 0, 
                'max': 100, 
                'step': 0.1,
                'class': 'quality-field'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize the form with Crispy Forms layout and field configuration.
        
        Sets up the form layout, field requirements, help texts, and JavaScript
        behavior for dynamic form interactions. Configures BnF compliance options
        and document type-specific compression ratio information.
        
        Args:
            *args: Variable positional arguments passed to parent __init__
            **kwargs: Variable keyword arguments passed to parent __init__
        """
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        
        # Make quality field not required by default
        self.fields['quality'].required = False
        
        self.helper.layout = Layout(
            'files',
            HTML('''
            <div class="selected-files-info mt-3 d-none">
                <h6>Selected Files: <span id="fileCount">0</span></h6>
                <div id="fileList" class="list-group small"></div>
            </div>
            '''),
            Row(
                Column('compression_mode', css_class='form-group col-md-6 mb-0'),
                Column('document_type', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            'bnf_compliant',
            'quality',
            HTML('''
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    const compressionSelect = document.querySelector('[name="compression_mode"]');
                    const qualityField = document.querySelector('[name="quality"]').closest('.form-group');
                    const qualityInput = document.querySelector('[name="quality"]');
                    const bnfCompliantField = document.querySelector('[name="bnf_compliant"]').closest('.form-group');
                    const documentTypeSelect = document.querySelector('[name="document_type"]');
                    
                    function updateBnfInfo() {
                        const selectedDocType = documentTypeSelect.value;
                        const isBnfMode = compressionSelect.value === 'bnf_compliant' || 
                                         document.querySelector('[name="bnf_compliant"]').checked;
                        
                        // Get the existing BnF info element or create it
                        let bnfInfoEl = document.getElementById('bnf-info');
                        if (!bnfInfoEl) {
                            bnfInfoEl = document.createElement('div');
                            bnfInfoEl.id = 'bnf-info';
                            bnfInfoEl.className = 'alert alert-info mt-3';
                            documentTypeSelect.parentNode.appendChild(bnfInfoEl);
                        }
                        
                        // Get the ratio for the selected document type
                        let ratio = '4:1';
                        switch (selectedDocType) {
                            case 'photograph':
                            case 'heritage_document':
                                ratio = '4:1';
                                break;
                            case 'color':
                                ratio = '6:1';
                                break;
                            case 'grayscale':
                                ratio = '16:1';
                                break;
                        }
                        
                        // Show/hide BnF info based on mode
                        if (isBnfMode) {
                            bnfInfoEl.innerHTML = `
                                <strong>BnF Mode:</strong> Document type "${selectedDocType}" requires a compression ratio of <strong>${ratio}</strong> with 5% tolerance.
                                <br>BnF compliance uses 10 resolution levels and applies special technical parameters per BnF standards.
                            `;
                            bnfInfoEl.style.display = 'block';
                        } else {
                            bnfInfoEl.style.display = 'none';
                        }
                    }
                    
                    function updateQualityField() {
                        const selectedMode = compressionSelect.value;
                        // Hide quality field for both lossless and bnf_compliant modes
                        if (selectedMode === 'lossless' || selectedMode === 'bnf_compliant') {
                            qualityField.style.display = 'none';
                            qualityInput.value = '40';  // Default value
                            qualityInput.required = false;
                            
                            // If BnF mode, hide the BnF checkbox (it's redundant)
                            if (selectedMode === 'bnf_compliant') {
                                bnfCompliantField.style.display = 'none';
                            } else {
                                bnfCompliantField.style.display = 'block';
                            }
                        } else {
                            qualityField.style.display = 'block';
                            qualityInput.required = true;
                            bnfCompliantField.style.display = 'block';
                        }
                        
                        // Update BnF info
                        updateBnfInfo();
                    }
                    
                    // Run once on page load
                    updateQualityField();
                    
                    // Run when compression mode changes
                    compressionSelect.addEventListener('change', updateQualityField);
                    
                    // Run when document type changes
                    documentTypeSelect.addEventListener('change', updateBnfInfo);
                    
                    // Run when BnF checkbox changes
                    document.querySelector('[name="bnf_compliant"]').addEventListener('change', updateBnfInfo);
                    
                    // Files handling
                    const filesInput = document.querySelector('input[name="files"]');
                    if (filesInput) {
                        const fileCountElement = document.getElementById('fileCount');
                        const fileListElement = document.getElementById('fileList');
                        const fileInfoElement = document.querySelector('.selected-files-info');
                        
                        filesInput.addEventListener('change', function() {
                            // Clear the previous list
                            fileListElement.innerHTML = '';
                            
                            // Update file count
                            const numFiles = filesInput.files.length;
                            fileCountElement.textContent = numFiles;
                            
                            // Show file info section if files are selected
                            if (numFiles > 0) {
                                fileInfoElement.classList.remove('d-none');
                                
                                // Display file list with sizes
                                for (let i = 0; i < numFiles; i++) {
                                    const file = filesInput.files[i];
                                    const fileSize = formatFileSize(file.size);
                                    
                                    const listItem = document.createElement('div');
                                    listItem.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2';
                                    listItem.innerHTML = `
                                        <span class="text-truncate" style="max-width: 80%;">${file.name}</span>
                                        <span class="badge bg-secondary">${fileSize}</span>
                                    `;
                                    fileListElement.appendChild(listItem);
                                }
                            } else {
                                fileInfoElement.classList.add('d-none');
                            }
                        });
                    }
                    
                    // Helper function to format file size
                    function formatFileSize(bytes) {
                        if (bytes === 0) return '0 Bytes';
                        
                        const k = 1024;
                        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                        const i = Math.floor(Math.log(bytes) / Math.log(k));
                        
                        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
                    }
                });
            </script>
            '''),
            Submit('submit', 'Upload and Convert', css_class='btn btn-primary')
        )
        
        # Add help texts
        self.fields['compression_mode'].help_text = """
            <strong>Lossless</strong><br>
            Preserves image quality exactly but results in larger files.<br>
            <strong>Lossy</strong><br>
            Some quality reduction but smaller file sizes.<br>
            <strong>Supervised</strong><br>
            Balanced compression with quality controls.<br>
            <strong>BnF Compliant</strong><br>
            Meets Bibliothèque nationale de France standards with fixed compression ratios based on document type.
        """
        
        # Build document type help text with BnF compression ratios
        doc_type_help = "<strong>Document Types:</strong><br>"
        for doc_type, ratio in BnFStandards.COMPRESSION_RATIOS.items():
            doc_type_label = doc_type.replace('_', ' ').title()
            doc_type_help += f"""
                <div class="document-type-card mt-2 mb-2 p-2 border-start border-primary ps-3">
                    <h6 class="mb-1">{doc_type_label}</h6>
                    <div class="mb-1">
            """
            
            if doc_type in ['photograph', 'heritage_document']:
                doc_type_help += "For detailed photographic or heritage content."
            elif doc_type == 'color':
                doc_type_help += "For general color documents."
            elif doc_type == 'grayscale':
                doc_type_help += "For black & white or grayscale content."
                
            doc_type_help += f"""
                    </div>
                    <div class="text-muted small">
                        <strong>BnF compression ratio:</strong> {ratio:.1f}:1
                    </div>
                </div>
            """
        
        self.fields['document_type'].help_text = doc_type_help
        
        self.fields['bnf_compliant'].help_text = """
            When enabled, sets parameters according to BnF (Bibliothèque nationale de France) preservation standards.
            <ul class='small mt-2'>
              <li>Enforces document type-specific compression ratios</li>
              <li>Sets 10 resolution levels as required by BnF</li>
              <li>Applies RPCL progression order and required markers</li>
            </ul>
        """
        
        self.fields['quality'].help_text = """
            Higher values preserve more image detail but increase file size.<br>
            <div class="quality-ranges mt-2">
                <div class="quality-range">
                    <strong>20-40</strong> - Lower quality but smaller files
                </div>
                <div class="quality-range">
                    <strong>40-70</strong> - Balanced quality/size
                </div>
                <div class="quality-range">
                    <strong>70-100</strong> - High quality but larger files
                </div>
            </div>
            <div class="alert alert-warning small mt-2">
                <i class="fa fa-info-circle"></i> Note: Quality setting is ignored when using BnF compliance mode, 
                which uses fixed compression ratios based on document type.
            </div>
        """
    
    def clean(self):
        """Validate form data with compression mode-specific rules.
        
        Performs cross-field validation to ensure that quality settings
        are appropriate for the selected compression mode. Quality is
        required for Lossy and Supervised modes but optional for Lossless
        and BnF Compliant modes where it's ignored.
        
        Returns:
            dict: Cleaned and validated form data
            
        Raises:
            ValidationError: If quality is missing for modes that require it
        """
        cleaned_data = super().clean()
        compression_mode = cleaned_data.get('compression_mode')
        quality = cleaned_data.get('quality')
        
        # Make quality optional for both Lossless and BnF Compliant modes
        if compression_mode not in ['lossless', 'bnf_compliant'] and not quality:
            self.add_error('quality', 'This field is required for Lossy and Supervised compression modes.')
        
        return cleaned_data
