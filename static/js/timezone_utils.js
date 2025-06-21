/**
 * JP2Forge Web Timezone Utilities
 * 
 * This script provides utility functions for handling timezone conversions
 * between the server (UTC) and the client's local timezone.
 */

/**
 * Format a UTC date string from the server to local timezone
 * @param {string} dateString - The date string in server timezone (UTC)
 * @param {boolean} includeTime - Whether to include time in the formatted string
 * @returns {string} - Formatted date string in user's local timezone
 */
function formatToLocalTimezone(dateString, includeTime = true) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        
        if (isNaN(date)) return dateString;
        
        const options = includeTime 
            ? { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' }
            : { year: 'numeric', month: 'long', day: 'numeric' };
            
        return date.toLocaleString(undefined, options);
    } catch (error) {
        console.error('Error formatting date:', error);
        return dateString;
    }
}

/**
 * Initialize timezone conversion for all elements with data-utc-date attribute
 */
function initializeTimezoneConversion() {
    const dateElements = document.querySelectorAll('[data-utc-date]');
    
    dateElements.forEach(element => {
        const dateString = element.getAttribute('data-utc-date');
        const includeTime = element.getAttribute('data-include-time') !== 'false';
        
        if (dateString && dateString !== 'None') {
            element.textContent = formatToLocalTimezone(dateString, includeTime);
        }
    });
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeTimezoneConversion();
});
