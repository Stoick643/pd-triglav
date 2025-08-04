/**
 * PD Triglav Confirmation Modal System
 * Professional confirmation dialogs replacing basic browser confirm() dialogs
 */

class PDTriglavConfirmModal {
    constructor() {
        this.currentModal = null;
        this.isOpen = false;
        this.activeElement = null;
        
        // Bind event handlers
        this.bindEvents();
    }
    
    bindEvents() {
        // Handle form submissions with data-confirm
        document.addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Handle button clicks with data-confirm
        document.addEventListener('click', (e) => this.handleButtonClick(e));
        
        // Handle keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Clean up on page unload
        window.addEventListener('beforeunload', () => this.cleanup());
    }
    
    handleFormSubmit(event) {
        const form = event.target;
        const confirmMessage = form.dataset.confirm;
        
        if (confirmMessage && !form.dataset.confirmed) {
            event.preventDefault();
            event.stopPropagation();
            
            const options = {
                type: form.dataset.confirmType || 'danger',
                confirmText: form.dataset.confirmText || 'Potrdi',
                cancelText: form.dataset.cancelText || 'Prekliči',
                icon: form.dataset.confirmIcon || 'bi-exclamation-triangle'
            };
            
            this.showConfirmModal(confirmMessage, () => {
                // Mark form as confirmed to prevent recursive confirmation
                form.dataset.confirmed = 'true';
                // Submit the form
                form.submit();
            }, options);
        }
    }
    
    handleButtonClick(event) {
        const button = event.target.closest('[data-confirm]');
        if (!button || button.tagName === 'FORM') return;
        
        const confirmMessage = button.dataset.confirm;
        if (confirmMessage) {
            event.preventDefault();
            event.stopPropagation();
            
            const options = {
                type: button.dataset.confirmType || 'danger',
                confirmText: button.dataset.confirmText || 'Potrdi',
                cancelText: button.dataset.cancelText || 'Prekliči',
                icon: button.dataset.confirmIcon || 'bi-exclamation-triangle'
            };
            
            this.showConfirmModal(confirmMessage, () => {
                // Execute the original click action
                this.executeButtonAction(button);
            }, options);
        }
    }
    
    executeButtonAction(button) {
        // If button has onclick, execute it
        if (button.onclick) {
            button.onclick.call(button);
        }
        
        // If button has href, navigate to it
        if (button.href) {
            window.location.href = button.href;
        }
        
        // If button is in a form and has type="submit", submit the form
        if (button.type === 'submit' && button.form) {
            button.form.dataset.confirmed = 'true';
            button.form.submit();
        }
        
        // If button has data-action, execute it
        if (button.dataset.action) {
            this.executeDataAction(button.dataset.action, button);
        }
    }
    
    executeDataAction(action, button) {
        switch (action) {
            case 'reload':
                window.location.reload();
                break;
            case 'back':
                window.history.back();
                break;
            case 'delete':
                // Handle delete action (usually form submission)
                if (button.form) {
                    button.form.dataset.confirmed = 'true';
                    button.form.submit();
                }
                break;
            default:
                console.warn(`Unknown data-action: ${action}`);
        }
    }
    
    showConfirmModal(message, onConfirm, options = {}) {
        if (this.isOpen) {
            this.close();
        }
        
        this.activeElement = document.activeElement;
        
        const modalOptions = {
            type: options.type || 'danger',
            confirmText: options.confirmText || 'Potrdi',
            cancelText: options.cancelText || 'Prekliči',
            icon: options.icon || 'bi-exclamation-triangle',
            title: options.title || this.getDefaultTitle(options.type),
            ...options
        };
        
        this.createModal(message, onConfirm, modalOptions);
        this.show();
    }
    
    getDefaultTitle(type) {
        switch (type) {
            case 'danger':
                return 'Potrditev potrebna';
            case 'warning':
                return 'Opozorilo';
            case 'info':
                return 'Potrditev';
            default:
                return 'Potrditev potrebna';
        }
    }
    
    createModal(message, onConfirm, options) {
        const modalHTML = `
            <div id="pd-confirm-modal" class="confirm-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
                <div class="confirm-modal-overlay" aria-hidden="true"></div>
                <div class="confirm-modal-container">
                    <div class="confirm-modal-content">
                        <div class="confirm-modal-header">
                            <div class="confirm-modal-icon confirm-modal-icon-${options.type}">
                                <i class="bi ${options.icon}"></i>
                            </div>
                            <h3 id="confirm-modal-title" class="confirm-modal-title">
                                ${options.title}
                            </h3>
                        </div>
                        
                        <div class="confirm-modal-body">
                            <p class="confirm-modal-message">${message}</p>
                        </div>
                        
                        <div class="confirm-modal-footer">
                            <button type="button" class="btn btn-outline-secondary confirm-modal-cancel" id="confirm-modal-cancel">
                                ${options.cancelText}
                            </button>
                            <button type="button" class="btn btn-${this.getButtonClass(options.type)} confirm-modal-confirm" id="confirm-modal-confirm">
                                ${options.confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        this.currentModal = document.getElementById('pd-confirm-modal');
        
        // Bind modal events
        this.bindModalEvents(onConfirm);
    }
    
    getButtonClass(type) {
        switch (type) {
            case 'danger':
                return 'danger';
            case 'warning':
                return 'warning';
            case 'info':
                return 'primary';
            default:
                return 'danger';
        }
    }
    
    bindModalEvents(onConfirm) {
        const cancelBtn = this.currentModal.querySelector('.confirm-modal-cancel');
        const confirmBtn = this.currentModal.querySelector('.confirm-modal-confirm');
        const overlay = this.currentModal.querySelector('.confirm-modal-overlay');
        
        // Cancel button
        cancelBtn.addEventListener('click', () => this.close());
        
        // Confirm button
        confirmBtn.addEventListener('click', () => {
            this.close();
            onConfirm();
        });
        
        // Overlay click
        overlay.addEventListener('click', () => this.close());
        
        // Prevent clicks inside modal from closing
        this.currentModal.querySelector('.confirm-modal-content').addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    show() {
        if (!this.currentModal) return;
        
        this.isOpen = true;
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        // Show modal with animation
        requestAnimationFrame(() => {
            this.currentModal.classList.add('show');
            
            // Focus on cancel button by default (safer)
            const cancelBtn = this.currentModal.querySelector('.confirm-modal-cancel');
            if (cancelBtn) {
                cancelBtn.focus();
            }
        });
        
        // Announce to screen readers
        this.announceToScreenReader('Modalno okno je odprto. Uporabite Tab za navigacijo.');
    }
    
    close() {
        if (!this.currentModal || !this.isOpen) return;
        
        this.isOpen = false;
        
        // Hide modal
        this.currentModal.classList.remove('show');
        
        // Restore body scroll
        document.body.style.overflow = '';
        
        // Remove modal after animation
        setTimeout(() => {
            if (this.currentModal) {
                this.currentModal.remove();
                this.currentModal = null;
            }
        }, 300);
        
        // Restore focus
        if (this.activeElement) {
            this.activeElement.focus();
            this.activeElement = null;
        }
        
        // Announce to screen readers
        this.announceToScreenReader('Modalno okno je zaprto.');
    }
    
    handleKeyboard(event) {
        if (!this.isOpen || !this.currentModal) return;
        
        switch (event.key) {
            case 'Escape':
                event.preventDefault();
                this.close();
                break;
                
            case 'Tab':
                this.handleTabNavigation(event);
                break;
                
            case 'Enter':
                // If focus is on confirm button, prevent default to avoid double-trigger
                if (document.activeElement === this.currentModal.querySelector('.confirm-modal-confirm')) {
                    event.preventDefault();
                }
                break;
        }
    }
    
    handleTabNavigation(event) {
        const focusableElements = this.currentModal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey) {
            // Shift + Tab (backwards)
            if (document.activeElement === firstFocusable) {
                event.preventDefault();
                lastFocusable.focus();
            }
        } else {
            // Tab (forwards)
            if (document.activeElement === lastFocusable) {
                event.preventDefault();
                firstFocusable.focus();
            }
        }
    }
    
    announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'visually-hidden';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    cleanup() {
        if (this.currentModal) {
            this.currentModal.remove();
        }
        document.body.style.overflow = '';
    }
    
    // Static helper method for direct usage
    static show(message, onConfirm, options = {}) {
        const instance = window.pdTriglavConfirmModal || new PDTriglavConfirmModal();
        instance.showConfirmModal(message, onConfirm, options);
        return instance;
    }
}

// Initialize global instance
window.PDTriglavConfirmModal = PDTriglavConfirmModal;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pdTriglavConfirmModal = new PDTriglavConfirmModal();
});

// Also initialize after HTMX swaps for dynamic content
document.body.addEventListener('htmx:afterSwap', () => {
    if (!window.pdTriglavConfirmModal) {
        window.pdTriglavConfirmModal = new PDTriglavConfirmModal();
    }
});