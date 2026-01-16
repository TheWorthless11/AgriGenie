/* ===========================
   AgriGenie Main JavaScript
   =========================== */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initializeTooltips();
    
    // Auto-close alerts after 5 seconds
    autoCloseAlerts();
    
    // Form validation
    initializeFormValidation();
    
    // Notification badge update
    initializeNotifications();
});

/**
 * Initialize Bootstrap Tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Auto-close alert messages
 */
function autoCloseAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (!alert.classList.contains('alert-danger')) {
            setTimeout(function() {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
}

/**
 * Form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize notifications with auto-refresh
 */
function initializeNotifications() {
    const notificationBadge = document.querySelector('[data-notification-badge]');
    
    if (notificationBadge) {
        // Refresh notifications every 30 seconds
        setInterval(function() {
            refreshNotifications();
        }, 30000);
    }
}

/**
 * Refresh notifications via AJAX
 */
function refreshNotifications() {
    fetch('/api/notifications/unread-count/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        const badge = document.querySelector('[data-notification-badge]');
        if (badge && data.count > 0) {
            badge.textContent = data.count;
            badge.style.display = 'inline';
        } else if (badge) {
            badge.style.display = 'none';
        }
    })
    .catch(error => console.error('Error fetching notifications:', error));
}

/**
 * Delete item with confirmation
 */
function deleteItem(deleteUrl, itemName = 'this item') {
    if (confirm(`Are you sure you want to delete ${itemName}? This action cannot be undone.`)) {
        window.location.href = deleteUrl;
    }
}

/**
 * Add to wishlist
 */
function addToWishlist(cropId, button) {
    const url = `/buyer/wishlist/add/${cropId}/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.classList.add('text-danger');
            button.innerHTML = '<i class="fas fa-heart-solid"></i> Remove from Wishlist';
            showNotification('success', data.message);
        } else {
            showNotification('error', data.message || 'Failed to add to wishlist');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', 'An error occurred. Please try again.');
    });
}

/**
 * Remove from wishlist
 */
function removeFromWishlist(cropId, button) {
    const url = `/buyer/wishlist/remove/${cropId}/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            button.classList.remove('text-danger');
            button.innerHTML = '<i class="fas fa-heart-outline"></i> Add to Wishlist';
            showNotification('success', data.message);
        } else {
            showNotification('error', data.message || 'Failed to remove from wishlist');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('error', 'An error occurred. Please try again.');
    });
}

/**
 * Mark notification as read
 */
function markNotificationAsRead(notificationId, link) {
    const url = `/users/notifications/${notificationId}/read/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && link) {
            window.location.href = link;
        }
    })
    .catch(error => console.error('Error:', error));
}

/**
 * Show notification toast
 */
function showNotification(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}

/**
 * Get CSRF token from cookies
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'INR') {
    const formatter = new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: currency,
    });
    return formatter.format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-IN', options);
}

/**
 * Debounce function for search
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Search crops on input
 */
const searchCrops = debounce(function(searchTerm) {
    if (searchTerm.length < 2) return;
    
    const url = new URL(window.location.href);
    url.searchParams.set('search', searchTerm);
    window.location.href = url.toString();
}, 300);

/**
 * Filter by category
 */
function filterByCategory(category) {
    const url = new URL(window.location.href);
    url.searchParams.set('category', category);
    window.location.href = url.toString();
}

/**
 * Filter by price range
 */
function filterByPrice(minPrice, maxPrice) {
    const url = new URL(window.location.href);
    url.searchParams.set('min_price', minPrice);
    url.searchParams.set('max_price', maxPrice);
    window.location.href = url.toString();
}

/**
 * Upload image preview
 */
function previewImage(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}

/**
 * Toggle form fields based on conditions
 */
function toggleFormField(fieldId, show) {
    const field = document.getElementById(fieldId);
    if (field) {
        field.style.display = show ? 'block' : 'none';
    }
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text, buttonElement = null) {
    navigator.clipboard.writeText(text).then(function() {
        if (buttonElement) {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(function() {
                buttonElement.innerHTML = originalText;
            }, 2000);
        }
    }).catch(function(err) {
        console.error('Error copying to clipboard:', err);
    });
}

/**
 * Export table to CSV
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    rows.forEach(function(row) {
        const cols = row.querySelectorAll('td, th');
        const rowData = [];
        cols.forEach(function(col) {
            rowData.push(col.textContent.trim());
        });
        csv.push(rowData.join(','));
    });
    
    downloadCSV(csv.join('\n'), filename);
}

/**
 * Download CSV file
 */
function downloadCSV(csv, filename) {
    const csvFile = new Blob([csv], { type: 'text/csv' });
    const downloadLink = document.createElement('a');
    downloadLink.href = URL.createObjectURL(csvFile);
    downloadLink.download = filename + '.csv';
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

/**
 * Initialize date picker (requires additional library)
 */
function initializeDatePicker(selector) {
    const dateInputs = document.querySelectorAll(selector);
    dateInputs.forEach(function(input) {
        input.addEventListener('click', function() {
            this.type = 'date';
        });
    });
}

/**
 * Real-time form validation
 */
function setupRealtimeValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            validateField(this);
        });
    });
}

/**
 * Validate single field
 */
function validateField(field) {
    const parent = field.closest('.mb-3');
    if (!parent) return;
    
    const feedback = parent.querySelector('.invalid-feedback');
    if (!field.value.trim()) {
        field.classList.add('is-invalid');
        if (feedback) feedback.style.display = 'block';
    } else {
        field.classList.remove('is-invalid');
        if (feedback) feedback.style.display = 'none';
    }
}

/**
 * Scroll to element
 */
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Pagination
 */
function goToPage(pageNumber) {
    const url = new URL(window.location.href);
    url.searchParams.set('page', pageNumber);
    window.location.href = url.toString();
}

console.log('AgriGenie JavaScript initialized');
