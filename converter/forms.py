from django import forms
from .models import ConversionJob
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML

class ConversionJobForm(forms.ModelForm):
    # Unified file field that supports multiple uploads
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'multiple': True,
            'class': 'unified-file-input'
        }),
        required=True,
        help_text="Select one or multiple image files to convert to JPEG2000. Supported formats include JPEG, TIFF, PNG, and BMP."
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
                    
                    function updateQualityField() {
                        const selectedMode = compressionSelect.value;
                        // Hide quality field for both lossless and bnf_compliant modes
                        if (selectedMode === 'lossless' || selectedMode === 'bnf_compliant') {
                            qualityField.style.display = 'none';
                            qualityInput.value = '40';  // Default value
                            qualityInput.required = false;
                        } else {
                            qualityField.style.display = 'block';
                            qualityInput.required = true;
                        }
                    }
                    
                    // Run once on page load
                    updateQualityField();
                    
                    // Run when compression mode changes
                    compressionSelect.addEventListener('change', updateQualityField);
                    
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
            Meets Bibliothèque nationale de France standards.
        """
        
        self.fields['document_type'].help_text = """
            <strong>Photograph</strong><br>
            Optimal for detailed photos.<br>
            <strong>Heritage Document</strong><br>
            Best for historical manuscripts and documents.<br>
            <strong>Color</strong><br>
            Optimized for vibrant color images.<br>
            <strong>Grayscale</strong><br>
            Best for black & white or grayscale content.
        """
        
        self.fields['bnf_compliant'].help_text = """
            When enabled, sets parameters according to BnF (Bibliothèque nationale de France) preservation standards.
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
        """
    
    def clean(self):
        cleaned_data = super().clean()
        compression_mode = cleaned_data.get('compression_mode')
        quality = cleaned_data.get('quality')
        
        # Make quality optional for both Lossless and BnF Compliant modes
        if compression_mode not in ['lossless', 'bnf_compliant'] and not quality:
            self.add_error('quality', 'This field is required for Lossy and Supervised compression modes.')
        
        return cleaned_data
