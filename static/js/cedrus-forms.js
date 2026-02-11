/**
 * Cedrus Forms Enhancement Module
 * ================================
 * Implements:
 * - Loading states for form submissions
 * - Custom confirmation modal (replacing native confirm())
 * - Client-side date validation
 * - ARIA announcements for form results
 * 
 * @version 1.0.0
 */

(function() {
    'use strict';

    // ============================================
    // CONFIGURATION
    // ============================================
    const CONFIG = {
        loadingMinDuration: 300,  // Minimum loading state duration (ms)
        toastDuration: 5000,      // Toast auto-dismiss duration
        animationDuration: 200    // Modal animation duration
    };

    // ============================================
    // FORM LOADING STATES
    // ============================================
    
    /**
     * Add loading state to form submissions
     * Prevents double-clicks and provides visual feedback
     */
    function initFormLoadingStates() {
        document.querySelectorAll('form').forEach(form => {
            // Skip forms with data-no-loading attribute
            if (form.dataset.noLoading) return;
            
            form.addEventListener('submit', function(e) {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (!submitBtn || submitBtn.classList.contains('btn-loading')) {
                    e.preventDefault();
                    return false;
                }
                
                // Store original content
                submitBtn.dataset.originalText = submitBtn.innerHTML;
                
                // Apply loading state
                submitBtn.classList.add('btn-loading');
                submitBtn.disabled = true;
                
                // Announce to screen readers
                if (window.CedrusA11y) {
                    CedrusA11y.announce('Submitting form, please wait...', 'polite');
                }
                
                // Ensure minimum loading duration for UX
                const startTime = Date.now();
                const originalAction = form.action;
                
                // For AJAX forms, handle loading state removal
                // For regular forms, the page will reload anyway
            });
        });
    }

    // ============================================
    // CUSTOM CONFIRMATION MODAL
    // ============================================
    
    let confirmModal = null;
    let confirmCallback = null;
    let previousActiveElement = null;
    
    /**
     * Create confirmation modal HTML structure
     */
    function createConfirmModal() {
        const modal = document.createElement('div');
        modal.id = 'cedrus-confirm-modal';
        modal.className = 'cedrus-modal-overlay';
        modal.setAttribute('role', 'alertdialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'confirm-modal-title');
        modal.setAttribute('aria-describedby', 'confirm-modal-message');
        modal.innerHTML = `
            <div class="cedrus-modal" role="document">
                <div class="cedrus-modal-header">
                    <h3 id="confirm-modal-title" class="cedrus-modal-title">Confirm Action</h3>
                    <button type="button" class="cedrus-modal-close" aria-label="Close" data-dismiss-modal>
                        <i class="bi bi-x-lg" aria-hidden="true"></i>
                    </button>
                </div>
                <div class="cedrus-modal-body">
                    <p id="confirm-modal-message" class="cedrus-modal-message"></p>
                    <p id="confirm-modal-warning" class="cedrus-modal-warning"></p>
                </div>
                <div class="cedrus-modal-footer">
                    <button type="button" class="btn btn-secondary" data-dismiss-modal>Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirm-modal-action">Confirm</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        confirmModal = modal;
        
        // Event listeners
        modal.querySelector('[data-dismiss-modal]').addEventListener('click', closeConfirmModal);
        modal.querySelectorAll('[data-dismiss-modal]').forEach(btn => {
            btn.addEventListener('click', closeConfirmModal);
        });
        
        modal.querySelector('#confirm-modal-action').addEventListener('click', () => {
            if (confirmCallback) {
                confirmCallback(true);
            }
            closeConfirmModal();
        });
        
        // Close on overlay click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeConfirmModal();
            }
        });
        
        // Close on Escape
        modal.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeConfirmModal();
            }
        });
        
        return modal;
    }
    
    /**
     * Show confirmation modal
     * @param {Object} options - Modal options
     * @param {string} options.title - Modal title
     * @param {string} options.message - Main message
     * @param {string} options.warning - Warning message (optional)
     * @param {string} options.confirmText - Confirm button text
     * @param {string} options.confirmClass - Confirm button class (default: btn-primary)
     * @param {Function} callback - Called with true if confirmed, false if cancelled
     */
    function showConfirmModal(options, callback) {
        if (!confirmModal) {
            createConfirmModal();
        }
        
        // Store previous focus
        previousActiveElement = document.activeElement;
        
        // Update modal content
        const titleEl = confirmModal.querySelector('#confirm-modal-title');
        const messageEl = confirmModal.querySelector('#confirm-modal-message');
        const warningEl = confirmModal.querySelector('#confirm-modal-warning');
        const actionBtn = confirmModal.querySelector('#confirm-modal-action');
        
        titleEl.textContent = options.title || 'Confirm Action';
        messageEl.textContent = options.message || 'Are you sure?';
        
        if (options.warning) {
            warningEl.textContent = options.warning;
            warningEl.style.display = 'block';
        } else {
            warningEl.style.display = 'none';
        }
        
        actionBtn.textContent = options.confirmText || 'Confirm';
        actionBtn.className = 'btn ' + (options.confirmClass || 'btn-primary');
        
        // Store callback
        confirmCallback = callback;
        
        // Show modal
        confirmModal.classList.add('active');
        document.body.style.overflow = 'hidden';
        
        // Focus first focusable element
        setTimeout(() => {
            const firstBtn = confirmModal.querySelector('button');
            if (firstBtn) firstBtn.focus();
        }, CONFIG.animationDuration);
        
        // Announce to screen readers
        if (window.CedrusA11y) {
            CedrusA11y.announce(options.message, 'assertive');
        }
    }
    
    /**
     * Close confirmation modal
     */
    function closeConfirmModal() {
        if (!confirmModal) return;
        
        confirmModal.classList.remove('active');
        document.body.style.overflow = '';
        
        // Return focus
        if (previousActiveElement) {
            previousActiveElement.focus();
        }
        
        // Call callback with false if not confirmed
        if (confirmCallback) {
            confirmCallback(false);
            confirmCallback = null;
        }
    }
    
    /**
     * Replace native confirm() on links/buttons with data-confirm
     */
    function initConfirmReplacements() {
        document.addEventListener('click', function(e) {
            const trigger = e.target.closest('[data-confirm]');
            if (!trigger) return;
            
            e.preventDefault();
            
            const message = trigger.dataset.confirm;
            const warning = trigger.dataset.confirmWarning || '';
            const title = trigger.dataset.confirmTitle || 'Confirm Action';
            const confirmText = trigger.dataset.confirmButton || 'Confirm';
            const confirmClass = trigger.dataset.confirmClass || 'btn-primary';
            
            showConfirmModal({
                title: title,
                message: message,
                warning: warning,
                confirmText: confirmText,
                confirmClass: confirmClass
            }, (confirmed) => {
                if (confirmed) {
                    if (trigger.tagName === 'A') {
                        window.location.href = trigger.href;
                    } else if (trigger.form) {
                        trigger.form.submit();
                    } else if (trigger.tagName === 'BUTTON') {
                        // For buttons without forms, dispatch click
                        trigger.dispatchEvent(new Event('confirmed'));
                    }
                }
            });
        });
    }

    // ============================================
    // DATE VALIDATION
    // ============================================
    
    /**
     * Validate date ranges (end date must be after start date)
     */
    function initDateValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            // Find date range pairs
            const startDate = form.querySelector('[name*="date_from"], [name*="start_date"], [name*="from_date"]');
            const endDate = form.querySelector('[name*="date_to"], [name*="end_date"], [name*="to_date"]');
            
            if (startDate && endDate) {
                // Validate on end date change
                endDate.addEventListener('change', () => validateDateRange(startDate, endDate));
                startDate.addEventListener('change', () => validateDateRange(startDate, endDate));
                
                // Validate on form submit
                form.addEventListener('submit', (e) => {
                    if (!validateDateRange(startDate, endDate)) {
                        e.preventDefault();
                        if (window.CedrusA11y) {
                            CedrusA11y.announce('Please fix the date range: end date must be after start date', 'assertive');
                        }
                    }
                });
            }
        });
    }
    
    /**
     * Validate that end date is after start date
     * @param {HTMLInputElement} startInput - Start date input
     * @param {HTMLInputElement} endInput - End date input
     * @returns {boolean} - Whether date range is valid
     */
    function validateDateRange(startInput, endInput) {
        if (!startInput.value || !endInput.value) return true;
        
        const startDate = new Date(startInput.value);
        const endDate = new Date(endInput.value);
        
        const isValid = endDate >= startDate;
        
        // Update visual feedback
        if (isValid) {
            endInput.classList.remove('is-invalid');
            removeError(endInput);
        } else {
            endInput.classList.add('is-invalid');
            showError(endInput, 'End date must be on or after start date');
        }
        
        return isValid;
    }
    
    /**
     * Show error message below input
     */
    function showError(input, message) {
        removeError(input);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback d-block';
        errorDiv.setAttribute('role', 'alert');
        errorDiv.textContent = message;
        
        input.parentNode.appendChild(errorDiv);
    }
    
    /**
     * Remove error message from input
     */
    function removeError(input) {
        const existing = input.parentNode.querySelector('.invalid-feedback');
        if (existing) existing.remove();
    }

    // ============================================
    // ARIA ENHANCEMENTS
    // ============================================
    
    /**
     * Add aria-label to icon-only buttons that lack them
     */
    function enhanceIconButtons() {
        document.querySelectorAll('a.btn, button.btn').forEach(btn => {
            // Check if button has only an icon (no text content)
            const textContent = btn.textContent.trim();
            const hasIcon = btn.querySelector('i, svg');
            
            if (hasIcon && textContent.length === 0) {
                // If no aria-label, try to derive from title or icon class
                if (!btn.getAttribute('aria-label')) {
                    const title = btn.getAttribute('title');
                    if (title) {
                        btn.setAttribute('aria-label', title);
                    } else {
                        const icon = btn.querySelector('i');
                        if (icon) {
                            // Try to derive from Bootstrap icon class
                            const iconClass = Array.from(icon.classList).find(c => c.startsWith('bi-'));
                            if (iconClass) {
                                const label = iconClass.replace('bi-', '').replace(/-/g, ' ');
                                btn.setAttribute('aria-label', label);
                            }
                        }
                    }
                }
                
                // Hide icon from screen readers
                if (hasIcon) {
                    hasIcon.setAttribute('aria-hidden', 'true');
                }
            }
        });
    }

    // ============================================
    // INITIALIZATION
    // ============================================
    
    function init() {
        initFormLoadingStates();
        initConfirmReplacements();
        initDateValidation();
        enhanceIconButtons();
        
        console.log('Cedrus Forms Enhancement Module loaded');
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose API
    window.CedrusForms = {
        showConfirmModal,
        closeConfirmModal,
        validateDateRange
    };
    
})();
