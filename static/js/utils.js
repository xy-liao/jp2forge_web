/**
 * JP2Forge Web - Shared Utility Functions
 * 
 * This file contains common utility functions used across multiple pages
 * to reduce code duplication and improve maintainability.
 */

/**
 * Format a file size in bytes to a human-readable string
 * @param {number} bytes - The size in bytes
 * @return {string} Formatted size string (e.g., "2.5 MB")
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Create an alert message element
 * @param {string} message - The message text
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {boolean} dismissible - Whether the alert can be dismissed
 * @return {HTMLElement} The created alert element
 */
function createAlert(message, type = 'info', dismissible = true) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} ${dismissible ? 'alert-dismissible fade show' : ''}`;
    alertDiv.role = 'alert';
    
    alertDiv.textContent = message;
    
    if (dismissible) {
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('data-bs-dismiss', 'alert');
        closeButton.setAttribute('aria-label', 'Close');
        alertDiv.appendChild(closeButton);
    }
    
    return alertDiv;
}

/**
 * Update the status badge element based on job status
 * @param {HTMLElement} badgeElement - The badge element to update
 * @param {string} status - Job status (pending, processing, completed, failed)
 */
function updateStatusBadge(badgeElement, status) {
    if (!badgeElement) return;
    
    // Clear existing classes
    badgeElement.classList.remove('bg-secondary', 'bg-primary', 'bg-success', 'bg-danger');
    
    // Set new classes and text based on status
    switch (status) {
        case 'pending':
            badgeElement.classList.add('bg-secondary');
            badgeElement.textContent = 'Pending';
            break;
        case 'processing':
            badgeElement.classList.add('bg-primary');
            badgeElement.textContent = 'Processing';
            break;
        case 'completed':
            badgeElement.classList.add('bg-success');
            badgeElement.textContent = 'Completed';
            break;
        case 'failed':
            badgeElement.classList.add('bg-danger');
            badgeElement.textContent = 'Failed';
            break;
    }
}