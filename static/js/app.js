// RSS Curation System - Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('RSS Curation System loaded');
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle AI suggestion generation
    const generateSuggestionButtons = document.querySelectorAll('.generate-suggestion');
    generateSuggestionButtons.forEach(button => {
        button.addEventListener('click', handleGenerateSuggestion);
    });

    // Handle quick add feeds
    const quickAddButtons = document.querySelectorAll('.quick-add');
    quickAddButtons.forEach(button => {
        button.addEventListener('click', handleQuickAdd);
    });

    // Auto-refresh functionality
    setupAutoRefresh();
    
    // Form validation
    setupFormValidation();
});

/**
 * Handle AI suggestion generation
 */
async function handleGenerateSuggestion(event) {
    const button = event.target.closest('.generate-suggestion');
    const itemId = button.getAttribute('data-item-id');
    const suggestionContainer = document.getElementById(`suggestion-${itemId}`);
    
    if (!itemId || !suggestionContainer) {
        console.error('Missing item ID or suggestion container');
        return;
    }

    try {
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span>Generating...';
        
        // Show loading modal
        const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
        loadingModal.show();

        // Make API request
        const response = await fetch(`/generate_suggestion/${itemId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.suggestion) {
            // Update the UI with the suggestion
            const suggestionHtml = `
                <div class="alert alert-info mb-3">
                    <p class="mb-0">${escapeHtml(data.suggestion)}</p>
                </div>
            `;
            
            // Replace the button with the suggestion
            const buttonContainer = button.parentElement;
            buttonContainer.innerHTML = suggestionHtml;
            
            // Add success animation
            const alertElement = suggestionContainer.querySelector('.alert');
            alertElement.style.opacity = '0';
            alertElement.style.transform = 'translateY(10px)';
            
            setTimeout(() => {
                alertElement.style.transition = 'all 0.3s ease-in-out';
                alertElement.style.opacity = '1';
                alertElement.style.transform = 'translateY(0)';
            }, 100);
            
        } else if (data.error) {
            throw new Error(data.error);
        }

    } catch (error) {
        console.error('Error generating suggestion:', error);
        
        // Show error message
        showAlert('Error generating AI suggestion: ' + error.message, 'danger');
        
        // Reset button state
        button.disabled = false;
        button.innerHTML = '<i data-feather="cpu" class="me-1"></i>Generate AI Suggestion';
        feather.replace();
        
    } finally {
        // Hide loading modal
        const loadingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
        if (loadingModal) {
            loadingModal.hide();
        }
    }
}

/**
 * Handle quick add feed functionality
 */
function handleQuickAdd(event) {
    const button = event.target;
    const feedUrl = button.getAttribute('data-url');
    const feedName = button.getAttribute('data-name');
    
    if (!feedUrl) {
        console.error('Missing feed URL');
        return;
    }

    // Fill in the form
    const urlInput = document.getElementById('feed_url');
    const nameInput = document.getElementById('feed_name');
    
    if (urlInput) urlInput.value = feedUrl;
    if (nameInput) nameInput.value = feedName || '';
    
    // Scroll to form
    const form = urlInput.closest('form');
    if (form) {
        form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Highlight the form briefly
        const card = form.closest('.card');
        if (card) {
            card.style.transition = 'box-shadow 0.3s ease-in-out';
            card.style.boxShadow = '0 0 20px rgba(var(--bs-primary-rgb), 0.3)';
            
            setTimeout(() => {
                card.style.boxShadow = '';
            }, 2000);
        }
    }
}

/**
 * Setup auto-refresh functionality
 */
function setupAutoRefresh() {
    // Check if we should auto-refresh (only on dashboard)
    if (window.location.pathname !== '/') {
        return;
    }

    // Auto-refresh every 10 minutes (600000 ms)
    const refreshInterval = 10 * 60 * 1000;
    
    setInterval(() => {
        // Only refresh if the page is visible
        if (!document.hidden) {
            console.log('Auto-refreshing feeds...');
            
            fetch('/refresh_feeds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            }).then(response => {
                if (response.ok) {
                    // Reload the page to show new items
                    window.location.reload();
                }
            }).catch(error => {
                console.error('Auto-refresh failed:', error);
            });
        }
    }, refreshInterval);

    // Show auto-refresh indicator
    const indicator = document.createElement('div');
    indicator.className = 'position-fixed bottom-0 end-0 m-3';
    indicator.innerHTML = `
        <div class="alert alert-secondary alert-dismissible fade show" role="alert">
            <i data-feather="clock" class="me-1"></i>
            <small>Auto-refresh enabled (every 10min)</small>
            <button type="button" class="btn-close btn-close-sm" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.appendChild(indicator);
    feather.replace();
    
    // Auto-hide the indicator after 5 seconds
    setTimeout(() => {
        const alert = indicator.querySelector('.alert');
        if (alert) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // URL validation for RSS feed input
    const urlInputs = document.querySelectorAll('input[type="url"]');
    urlInputs.forEach(input => {
        input.addEventListener('blur', function() {
            const url = input.value.trim();
            if (url && !isValidUrl(url)) {
                input.setCustomValidity('Please enter a valid RSS feed URL');
            } else {
                input.setCustomValidity('');
            }
        });
    });
}

/**
 * Utility function to validate URLs
 */
function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch (_) {
        return false;
    }
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.container');
    if (!alertContainer) return;

    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.setAttribute('role', 'alert');
    alertElement.innerHTML = `
        ${escapeHtml(message)}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Insert after navigation
    const existingAlerts = alertContainer.querySelector('.alert');
    if (existingAlerts) {
        existingAlerts.parentNode.insertBefore(alertElement, existingAlerts);
    } else {
        alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    }

    // Auto-dismiss after 5 seconds for non-error messages
    if (type !== 'danger') {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getInstance(alertElement);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    }
}

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + R: Refresh feeds
    if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
        if (window.location.pathname === '/') {
            event.preventDefault();
            
            const refreshForm = document.querySelector('form[action="/refresh_feeds"]');
            if (refreshForm) {
                refreshForm.submit();
            }
        }
    }
});

/**
 * Service Worker registration for offline functionality (optional)
 */
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Note: Service worker file would need to be created separately
        // navigator.serviceWorker.register('/sw.js').then(function(registration) {
        //     console.log('SW registered: ', registration);
        // }).catch(function(registrationError) {
        //     console.log('SW registration failed: ', registrationError);
        // });
    });
}
