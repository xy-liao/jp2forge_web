/**
 * JP2Forge Web - Dashboard Auto-Refresh Script
 * 
 * This script provides real-time updates for the dashboard page:
 * - Auto-refreshes the dashboard when in-progress jobs are present
 * - Updates job progress bars in real-time
 * - Provides notifications when jobs complete
 */

// Configuration
const REFRESH_INTERVAL = 30000; // Full page refresh interval (30 seconds)
const UPDATE_INTERVAL = 5000;   // Job status update interval (5 seconds)
let refreshTimer = null;
let updateTimer = null;

/**
 * Sets up the dashboard auto-refresh functionality
 */
function setupDashboardRefresh() {
    // Only setup refresh on the dashboard page
    if (window.location.pathname !== '/converter/dashboard/' && 
        window.location.pathname !== '/dashboard/') {
        return;
    }
    
    // Clear any existing timers
    if (refreshTimer) clearTimeout(refreshTimer);
    if (updateTimer) clearTimeout(updateTimer);
    
    // Check if there are any in-progress jobs
    const processingJobs = document.querySelectorAll('.badge.bg-primary');
    const pendingJobs = document.querySelectorAll('.badge.bg-secondary');
    
    if (processingJobs.length > 0 || pendingJobs.length > 0) {
        // Start job status updates
        updateJobStatuses();
        
        // Set up page refresh timer
        refreshTimer = setTimeout(function() {
            window.location.reload();
        }, REFRESH_INTERVAL);
    }
}

/**
 * Updates the status of in-progress jobs on the dashboard
 */
function updateJobStatuses() {
    // Find all job cards with processing or pending status
    const jobCards = document.querySelectorAll('.recent-job-link');
    const activeJobs = [];
    
    // Collect job IDs for active jobs
    jobCards.forEach(card => {
        const statusBadge = card.querySelector('.badge');
        if (statusBadge && 
            (statusBadge.classList.contains('bg-primary') || statusBadge.classList.contains('bg-secondary'))) {
            const jobUrl = card.getAttribute('href');
            const jobId = jobUrl.split('/').filter(segment => segment.length > 0).pop();
            activeJobs.push(jobId);
        }
    });
    
    // If no active jobs, stop updating
    if (activeJobs.length === 0) {
        return;
    }
    
    // Update each active job
    let completedJobsCount = 0;
    let failedJobsCount = 0;
    
    activeJobs.forEach(jobId => {
        fetch(`/converter/jobs/${jobId}/status/`)
            .then(response => response.json())
            .then(data => {
                // Find the job card
                const jobLinks = document.querySelectorAll(`.recent-job-link[href*="${jobId}"]`);
                if (jobLinks.length === 0) return;
                
                const jobCard = jobLinks[0];
                const statusBadge = jobCard.querySelector('.badge');
                const progressBar = jobCard.querySelector('.progress-bar');
                
                // Update progress bar if present
                if (progressBar && data.status === 'processing') {
                    progressBar.style.width = `${data.progress}%`;
                    progressBar.setAttribute('aria-valuenow', data.progress);
                }
                
                // Update status badge
                if (statusBadge) {
                    if (data.status === 'pending') {
                        statusBadge.className = 'badge bg-secondary';
                        statusBadge.textContent = 'Pending';
                    } else if (data.status === 'processing') {
                        statusBadge.className = 'badge bg-primary';
                        statusBadge.textContent = 'Processing';
                    } else if (data.status === 'completed') {
                        statusBadge.className = 'badge bg-success';
                        statusBadge.textContent = 'Completed';
                        completedJobsCount++;
                    } else if (data.status === 'failed') {
                        statusBadge.className = 'badge bg-danger';
                        statusBadge.textContent = 'Failed';
                        failedJobsCount++;
                    }
                }
                
                // Add or remove progress bar based on status
                if (data.status === 'processing') {
                    // Add a progress bar if not present
                    if (!progressBar) {
                        const progressDiv = document.createElement('div');
                        progressDiv.className = 'progress mt-2';
                        progressDiv.style.height = '5px';
                        
                        const progressBarDiv = document.createElement('div');
                        progressBarDiv.className = 'progress-bar';
                        progressBarDiv.role = 'progressbar';
                        progressBarDiv.style.width = `${data.progress}%`;
                        progressBarDiv.setAttribute('aria-valuenow', data.progress);
                        progressBarDiv.setAttribute('aria-valuemin', '0');
                        progressBarDiv.setAttribute('aria-valuemax', '100');
                        
                        progressDiv.appendChild(progressBarDiv);
                        const infoRow = jobCard.querySelector('.d-flex.w-100.justify-content-between:last-child');
                        if (infoRow) {
                            infoRow.parentNode.insertBefore(progressDiv, infoRow.nextSibling);
                        }
                    }
                } else {
                    // Remove progress bar if present and job is not processing
                    if (progressBar && data.status !== 'processing') {
                        const progressDiv = progressBar.parentNode;
                        if (progressDiv) {
                            progressDiv.remove();
                        }
                    }
                }
            })
            .catch(error => {
                console.error(`Error updating job ${jobId}:`, error);
            });
    });
    
    // Show desktop notification if jobs completed or failed
    if (completedJobsCount > 0 || failedJobsCount > 0) {
        const totalChanged = completedJobsCount + failedJobsCount;
        
        // Show notification if allowed
        if (window.Notification && Notification.permission === "granted") {
            let notificationTitle = 'JP2Forge Job Update';
            let notificationBody = '';
            
            if (completedJobsCount > 0 && failedJobsCount > 0) {
                notificationBody = `${completedJobsCount} job(s) completed and ${failedJobsCount} job(s) failed.`;
            } else if (completedJobsCount > 0) {
                notificationBody = `${completedJobsCount} job(s) completed successfully.`;
            } else {
                notificationBody = `${failedJobsCount} job(s) failed.`;
            }
            
            const notification = new Notification(notificationTitle, {
                body: notificationBody,
                icon: '/static/images/jp2forge-icon.png'
            });
            
            // Auto-close notification after 5 seconds
            setTimeout(() => {
                notification.close();
            }, 5000);
        }
        
        // If jobs changed status, refresh the page soon
        if (totalChanged > 0) {
            clearTimeout(refreshTimer);
            refreshTimer = setTimeout(function() {
                window.location.reload();
            }, 2000);
            return;
        }
    }
    
    // Continue updating as long as there are active jobs
    updateTimer = setTimeout(updateJobStatuses, UPDATE_INTERVAL);
}

/**
 * Requests notification permission if not already granted
 */
function requestNotificationPermission() {
    if (window.Notification && Notification.permission !== "granted") {
        Notification.requestPermission();
    }
}

// Initialize when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    setupDashboardRefresh();
    requestNotificationPermission();
});

// Re-initialize on page visibility change (tab focus)
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') {
        setupDashboardRefresh();
    }
});
