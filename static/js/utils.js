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
    if (typeof bytes !== 'number') {
        throw new TypeError('Expected a number');
    }
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.max(0, Math.min(Math.floor(Math.log(bytes) / Math.log(k)), sizes.length - 1));
    
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
    // Validate parameters
    const validTypes = ['success', 'danger', 'warning', 'info'];
    const validatedType = validTypes.includes(type) ? type : 'info';
    const sanitizedMessage = String(message);
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${validatedType} ${dismissible ? 'alert-dismissible fade show' : ''}`;
    alertDiv.setAttribute('role', 'alert');
    
    // Use textContent for proper DOM sanitization
    alertDiv.textContent = sanitizedMessage;
    
    if (dismissible) {
        const closeButton = document.createElement('button');
        closeButton.setAttribute('type', 'button');
        closeButton.setAttribute('class', 'btn-close');
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
    if (!badgeElement || !(badgeElement instanceof HTMLElement)) {
        return;
    }
    
    // Define valid statuses and their corresponding classes/labels
    const statusConfigs = {
        'pending': { classes: ['bg-secondary'], text: 'Pending' },
        'processing': { classes: ['bg-primary'], text: 'Processing' },
        'completed': { classes: ['bg-success'], text: 'Completed' },
        'failed': { classes: ['bg-danger'], text: 'Failed' }
    };
    
    // Clear existing classes
    badgeElement.classList.remove('bg-secondary', 'bg-primary', 'bg-success', 'bg-danger');
    
    // Apply new classes and text if status is valid
    const config = statusConfigs[status];
    if (config) {
        config.classes.forEach(cls => badgeElement.classList.add(cls));
        badgeElement.textContent = config.text;
    }
}