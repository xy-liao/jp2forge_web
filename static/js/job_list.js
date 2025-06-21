/**
 * JP2Forge Web - Job List Management Script
 * 
 * This script provides functionality for the job list page:
 * - Real-time updates for job status
 * - Filter handling
 * - Quick actions
 */

// Configuration
const UPDATE_INTERVAL = 5000;  // Job status update interval (5 seconds)
let updateTimer = null;

/**
 * Initialize the job list functionality
 */
function initJobList() {
    // Only run on the job list page
    if (window.location.pathname !== '/converter/jobs/') {
        return;
    }
    
    // Set up real-time updates for in-progress jobs
    updateJobStatuses();
    
    // Set up filter form submission
    setupFilterForm();
    
    // Set up bulk actions (if implemented)
    setupBulkActions();
}

/**
 * Update status of in-progress jobs
 */
function updateJobStatuses() {
    // Find all job rows with processing or pending status
    const jobRows = document.querySelectorAll('tr[data-job-status="processing"], tr[data-job-status="pending"]');
    
    if (jobRows.length === 0) {
        return; // No in-progress jobs
    }
    
    // Update each job status
    jobRows.forEach(row => {
        const jobId = row.getAttribute('data-job-id');
        
        fetch(`/converter/jobs/${jobId}/status/`)
            .then(response => response.json())
            .then(data => {
                // Update status cell
                const statusCell = row.querySelector('td:nth-child(2)');
                if (statusCell) {
                    let statusHTML = '';
                    
                    if (data.status === 'pending') {
                        statusHTML = '<span class="badge bg-secondary">Pending</span>';
                    } else if (data.status === 'processing') {
                        statusHTML = `
                            <span class="badge bg-primary">Processing</span>
                            <div class="progress">
                                <div class="progress-bar" role="progressbar" style="width: ${data.progress}%;" 
                                    aria-valuenow="${data.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        `;
                    } else if (data.status === 'completed') {
                        statusHTML = '<span class="badge bg-success">Completed</span>';
                    } else if (data.status === 'failed') {
                        statusHTML = '<span class="badge bg-danger">Failed</span>';
                    }
                    
                    statusCell.innerHTML = statusHTML;
                }
                
                // Update row status attribute
                row.setAttribute('data-job-status', data.status);
                
                // Update actions cell if status changed to completed
                if (data.status === 'completed' && data.output_filename) {
                    const actionsCell = row.querySelector('td.job-actions');
                    if (actionsCell) {
                        // Check if download button already exists
                        if (!actionsCell.querySelector('a.btn-success')) {
                            // Create download button (this is a simplified version)
                            const downloadBtn = document.createElement('a');
                            downloadBtn.href = `/media/jobs/${jobId}/output/${data.output_filename}`;
                            downloadBtn.className = 'btn btn-sm btn-success';
                            downloadBtn.setAttribute('download', '');
                            downloadBtn.innerHTML = '<i class="bi bi-download"></i> Download';
                            
                            // Insert after view button
                            const viewBtn = actionsCell.querySelector('a.btn-outline-primary');
                            if (viewBtn) {
                                viewBtn.insertAdjacentElement('afterend', downloadBtn);
                            } else {
                                actionsCell.prepend(downloadBtn);
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error(`Error updating job ${jobId}:`, error);
            });
    });
    
    // Continue updating as long as there are in-progress jobs
    updateTimer = setTimeout(updateJobStatuses, UPDATE_INTERVAL);
}

/**
 * Setup the filter form functionality
 */
function setupFilterForm() {
    const filterForm = document.querySelector('.job-filters form');
    if (!filterForm) return;
    
    // Add event listeners to auto-submit on select changes
    const selectFields = filterForm.querySelectorAll('select');
    selectFields.forEach(select => {
        select.addEventListener('change', () => {
            // Add a small delay to allow multiple changes
            setTimeout(() => filterForm.submit(), 200);
        });
    });
    
    // Add search functionality
    const searchInput = filterForm.querySelector('input[name="search"]');
    if (searchInput) {
        // Debounce function to avoid too many submissions
        let searchTimeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (searchInput.value.length >= 2 || searchInput.value.length === 0) {
                    filterForm.submit();
                }
            }, 500);
        });
    }
}

/**
 * Setup bulk action functionality
 */
function setupBulkActions() {
    const bulkActionForm = document.getElementById('bulk-action-form');
    if (!bulkActionForm) return;
    
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-jobs');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const jobCheckboxes = document.querySelectorAll('.job-checkbox');
            jobCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            
            // Update selected count
            updateSelectedCount();
        });
    }
    
    // Individual checkboxes
    const jobCheckboxes = document.querySelectorAll('.job-checkbox');
    jobCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateSelectedCount);
    });
    
    // Bulk action select
    const bulkActionSelect = document.getElementById('bulk-action');
    if (bulkActionSelect) {
        bulkActionSelect.addEventListener('change', function() {
            const applyBtn = document.getElementById('apply-bulk-action');
            if (applyBtn) {
                applyBtn.disabled = !this.value;
            }
        });
    }
    
    // Apply button
    const applyBtn = document.getElementById('apply-bulk-action');
    if (applyBtn) {
        applyBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Check if any jobs are selected
            const selectedJobs = document.querySelectorAll('.job-checkbox:checked');
            if (selectedJobs.length === 0) {
                alert('Please select at least one job.');
                return;
            }
            
            // Check if action is selected
            const action = bulkActionSelect.value;
            if (!action) {
                alert('Please select an action.');
                return;
            }
            
            // Confirm action
            if (action === 'delete') {
                if (!confirm(`Are you sure you want to delete ${selectedJobs.length} selected job(s)? This cannot be undone.`)) {
                    return;
                }
            }
            
            // Submit the form
            bulkActionForm.submit();
        });
    }
}

/**
 * Update the selected jobs count
 */
function updateSelectedCount() {
    const selectedCount = document.querySelectorAll('.job-checkbox:checked').length;
    const countElement = document.getElementById('selected-count');
    
    if (countElement) {
        countElement.textContent = selectedCount;
        
        // Show/hide the bulk actions container
        const bulkActionsContainer = document.getElementById('bulk-actions-container');
        if (bulkActionsContainer) {
            bulkActionsContainer.style.display = selectedCount > 0 ? 'block' : 'none';
        }
    }
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', initJobList);

// Re-initialize when page visibility changes (tab focus)
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        clearTimeout(updateTimer);
        initJobList();
    }
});
