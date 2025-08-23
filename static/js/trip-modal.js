/**
 * PD Triglav Trip Modal System
 * Handles trip signup and withdrawal modals with AJAX functionality
 */

class TripModalManager {
    constructor() {
        this.currentTripId = null;
        this.isLoading = false;
        this.signupModal = null;
        this.withdrawModal = null;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeModals();
    }
    
    initializeModals() {
        this.signupModal = document.getElementById('tripSignupModal');
        this.withdrawModal = document.getElementById('tripWithdrawModal');
        
        if (!this.signupModal || !this.withdrawModal) {
            console.warn('Trip modals not found in DOM');
            return;
        }
        
        this.setupModalEvents();
    }
    
    bindEvents() {
        // Handle signup buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="trip-signup"], [data-action="trip-signup"] *')) {
                e.preventDefault();
                const button = e.target.closest('[data-action="trip-signup"]');
                const tripId = parseInt(button.dataset.tripId);
                if (tripId) {
                    this.showSignupModal(tripId);
                }
            }
        });
        
        // Handle withdraw buttons  
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="trip-withdraw"], [data-action="trip-withdraw"] *')) {
                e.preventDefault();
                const button = e.target.closest('[data-action="trip-withdraw"]');
                const tripId = parseInt(button.dataset.tripId);
                if (tripId) {
                    this.showWithdrawModal(tripId);
                }
            }
        });
        
        // Keyboard events
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });
    }
    
    setupModalEvents() {
        // Signup modal events
        if (this.signupModal) {
            const signupForm = this.signupModal.querySelector('#signupForm');
            const signupCancelBtn = this.signupModal.querySelector('#signupCancelBtn');
            const signupCloseBtn = this.signupModal.querySelector('.trip-modal-close');
            const signupOverlay = this.signupModal.querySelector('.trip-modal-overlay');
            
            signupForm?.addEventListener('submit', (e) => this.handleSignupSubmit(e));
            signupCancelBtn?.addEventListener('click', () => this.closeModal(this.signupModal));
            signupCloseBtn?.addEventListener('click', () => this.closeModal(this.signupModal));
            signupOverlay?.addEventListener('click', () => this.closeModal(this.signupModal));
        }
        
        // Withdraw modal events
        if (this.withdrawModal) {
            const withdrawForm = this.withdrawModal.querySelector('#withdrawForm');
            const withdrawCancelBtn = this.withdrawModal.querySelector('#withdrawCancelBtn');
            const withdrawCloseBtn = this.withdrawModal.querySelector('.trip-modal-close');
            const withdrawOverlay = this.withdrawModal.querySelector('.trip-modal-overlay');
            
            withdrawForm?.addEventListener('submit', (e) => this.handleWithdrawSubmit(e));
            withdrawCancelBtn?.addEventListener('click', () => this.closeModal(this.withdrawModal));
            withdrawCloseBtn?.addEventListener('click', () => this.closeModal(this.withdrawModal));
            withdrawOverlay?.addEventListener('click', () => this.closeModal(this.withdrawModal));
        }
    }
    
    async showSignupModal(tripId) {
        if (this.isLoading || !this.signupModal) return;
        
        this.currentTripId = tripId;
        this.isLoading = true;
        
        try {
            // Get trip data
            const tripData = await this.fetchTripData(tripId);
            this.populateSignupModal(tripData);
            this.showModal(this.signupModal);
        } catch (error) {
            console.error('Error loading trip data:', error);
            this.showError('Napaka pri nalaganju podatkov o izletu');
        } finally {
            this.isLoading = false;
        }
    }
    
    async showWithdrawModal(tripId) {
        if (this.isLoading || !this.withdrawModal) return;
        
        this.currentTripId = tripId;
        this.isLoading = true;
        
        try {
            // Get trip data
            const tripData = await this.fetchTripData(tripId);
            this.populateWithdrawModal(tripData);
            this.showModal(this.withdrawModal);
        } catch (error) {
            console.error('Error loading trip data:', error);
            this.showError('Napaka pri nalaganju podatkov o izletu');
        } finally {
            this.isLoading = false;
        }
    }
    
    async fetchTripData(tripId) {
        const response = await fetch(`/trips/${tripId}/modal-data`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    populateSignupModal(data) {
        // Update trip details
        this.updateElement('#signupTripName', data.title);
        this.updateElement('#signupDestination', data.destination);
        this.updateElement('#signupDate', data.trip_date);
        this.updateElement('#signupTime', data.meeting_time || 'TBD');
        this.updateElement('#signupLeader', data.leader_name);
        
        // Update difficulty badge
        const difficultyBadge = this.signupModal.querySelector('#signupDifficultyBadge');
        if (difficultyBadge) {
            difficultyBadge.textContent = data.difficulty.name;
            difficultyBadge.className = `difficulty-badge difficulty-${data.difficulty.value}`;
        }
        
        // Update participant info
        const participantCount = this.signupModal.querySelector('#signupParticipantCount');
        if (participantCount) {
            participantCount.textContent = data.max_participants ? 
                `${data.confirmed_count}/${data.max_participants}` : 
                `${data.confirmed_count}`;
        }
        
        // Update waitlist info
        const waitlistInfo = this.signupModal.querySelector('#signupWaitlistInfo');
        const waitlistCount = this.signupModal.querySelector('#signupWaitlistCount');
        if (waitlistInfo && waitlistCount) {
            if (data.waitlist_count > 0) {
                waitlistCount.textContent = data.waitlist_count;
                waitlistInfo.style.display = 'block';
            } else {
                waitlistInfo.style.display = 'none';
            }
        }
        
        // Update status badge and button text
        const statusBadge = this.signupModal.querySelector('#signupStatusBadge');
        const submitBtn = this.signupModal.querySelector('#signupSubmitBtn .btn-text');
        
        if (data.is_full) {
            if (statusBadge) {
                statusBadge.textContent = 'Polno - čakalna lista';
                statusBadge.className = 'status-badge status-waitlist';
                statusBadge.style.display = 'inline';
            }
            if (submitBtn) {
                submitBtn.textContent = 'Dodaj na čakalno listo';
            }
        } else {
            if (statusBadge) {
                statusBadge.style.display = 'none';
            }
            if (submitBtn) {
                submitBtn.textContent = 'Prijavi se na izlet';
            }
        }
        
        // Update description
        const descriptionDiv = this.signupModal.querySelector('#signupDescription');
        const descriptionText = descriptionDiv?.querySelector('.description-text');
        if (descriptionDiv && descriptionText && data.description) {
            descriptionText.textContent = data.description;
            descriptionDiv.style.display = 'block';
        } else if (descriptionDiv) {
            descriptionDiv.style.display = 'none';
        }
    }
    
    populateWithdrawModal(data) {
        // Update trip details
        this.updateElement('#withdrawTripName', data.title);
        this.updateElement('#withdrawDate', data.trip_date);
        this.updateElement('#withdrawDestination', data.destination);
        
        // Show/hide waitlist info
        const waitlistInfo = this.withdrawModal.querySelector('#withdrawWaitlistInfo');
        if (waitlistInfo) {
            waitlistInfo.style.display = data.waitlist_count > 0 ? 'inline' : 'none';
        }
    }
    
    async handleSignupSubmit(e) {
        e.preventDefault();
        
        if (this.isLoading || !this.currentTripId) return;
        
        const form = e.target;
        const submitBtn = form.querySelector('#signupSubmitBtn');
        const termsCheckbox = form.querySelector('#signupTerms');
        
        // Validate terms acceptance
        if (!termsCheckbox?.checked) {
            this.showAlert('#signupAlerts', 'Prosimo, sprejmite pravila PD Triglav', 'danger');
            return;
        }
        
        this.setLoadingState(submitBtn, true);
        
        try {
            const formData = new FormData(form);
            const data = {
                notes: formData.get('notes') || ''
            };
            
            const response = await fetch(`/trips/${this.currentTripId}/signup-ajax`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data),
                credentials: 'same-origin'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('#signupAlerts', result.message, 'success');
                setTimeout(() => {
                    this.closeModal(this.signupModal);
                    this.updateTripCards(this.currentTripId, result);
                    this.showGlobalMessage(result.message, 'success');
                }, 1500);
            } else {
                this.showAlert('#signupAlerts', result.error, 'danger');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showAlert('#signupAlerts', 'Napaka pri prijavi. Poskusite znova.', 'danger');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }
    
    async handleWithdrawSubmit(e) {
        e.preventDefault();
        
        if (this.isLoading || !this.currentTripId) return;
        
        const form = e.target;
        const submitBtn = form.querySelector('#withdrawSubmitBtn');
        
        this.setLoadingState(submitBtn, true);
        
        try {
            const response = await fetch(`/trips/${this.currentTripId}/withdraw-ajax`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('#withdrawAlerts', result.message, 'success');
                setTimeout(() => {
                    this.closeModal(this.withdrawModal);
                    this.updateTripCards(this.currentTripId, result);
                    this.showGlobalMessage(result.message, 'info');
                }, 1500);
            } else {
                this.showAlert('#withdrawAlerts', result.error, 'danger');
            }
        } catch (error) {
            console.error('Withdraw error:', error);
            this.showAlert('#withdrawAlerts', 'Napaka pri odjavi. Poskusite znova.', 'danger');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }
    
    updateTripCards(tripId, data) {
        // Update all trip cards/elements with this trip ID
        const elements = document.querySelectorAll(`[data-trip-id="${tripId}"]`);
        
        elements.forEach(element => {
            // Update participant count
            const countElement = element.querySelector('.participant-count, [data-participant-count]');
            if (countElement) {
                const countText = data.max_participants ? 
                    `${data.confirmed_count}/${data.max_participants}` : 
                    `${data.confirmed_count}`;
                countElement.textContent = countText;
            }
            
            // Update buttons based on new status
            const signupBtn = element.querySelector('[data-action="trip-signup"]');
            const withdrawBtn = element.querySelector('[data-action="trip-withdraw"]');
            
            if (data.success) {
                // User just signed up - show withdraw button, hide signup
                if (signupBtn) {
                    signupBtn.style.display = 'none';
                }
                if (withdrawBtn) {
                    withdrawBtn.style.display = 'inline-block';
                }
                
                // Add registered badge
                let badge = element.querySelector('.registration-badge');
                if (!badge) {
                    badge = document.createElement('span');
                    badge.className = 'badge bg-success registration-badge';
                    badge.innerHTML = '<i class="bi bi-check-circle me-1"></i>Prijavljen';
                    element.querySelector('.trip-card-footer')?.appendChild(badge);
                }
            } else if (data.message && data.message.includes('odjavili')) {
                // User just withdrew - show signup button, hide withdraw
                if (withdrawBtn) {
                    withdrawBtn.style.display = 'none';
                }
                if (signupBtn) {
                    signupBtn.style.display = 'inline-block';
                }
                
                // Remove registered badge
                const badge = element.querySelector('.registration-badge');
                if (badge) {
                    badge.remove();
                }
            }
        });
    }
    
    showModal(modal) {
        if (!modal) return;
        
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        
        // Animate in
        requestAnimationFrame(() => {
            modal.classList.add('show');
        });
        
        // Focus first input
        const firstInput = modal.querySelector('input, textarea, button');
        if (firstInput) {
            setTimeout(() => firstInput.focus(), 100);
        }
    }
    
    closeModal(modal) {
        if (!modal) return;
        
        modal.classList.remove('show');
        
        setTimeout(() => {
            modal.style.display = 'none';
            document.body.style.overflow = '';
            this.currentTripId = null;
            
            // Clear form data and alerts
            const form = modal.querySelector('form');
            if (form) {
                form.reset();
            }
            
            const alerts = modal.querySelectorAll('.alert-container');
            alerts.forEach(alert => {
                alert.style.display = 'none';
                alert.innerHTML = '';
            });
        }, 300);
    }
    
    closeAllModals() {
        this.closeModal(this.signupModal);
        this.closeModal(this.withdrawModal);
    }
    
    setLoadingState(button, loading) {
        if (!button) return;
        
        const text = button.querySelector('.btn-text');
        const spinner = button.querySelector('.btn-loading');
        
        if (loading) {
            button.disabled = true;
            if (text) text.style.display = 'none';
            if (spinner) spinner.style.display = 'inline';
        } else {
            button.disabled = false;
            if (text) text.style.display = 'inline';
            if (spinner) spinner.style.display = 'none';
        }
    }
    
    updateElement(selector, text) {
        const element = this.signupModal?.querySelector(selector) || this.withdrawModal?.querySelector(selector);
        if (element) {
            element.textContent = text;
        }
    }
    
    showAlert(containerSelector, message, type) {
        const container = this.signupModal?.querySelector(containerSelector) || 
                         this.withdrawModal?.querySelector(containerSelector);
        
        if (!container) return;
        
        container.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
            </div>
        `;
        container.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                container.style.display = 'none';
            }, 3000);
        }
    }
    
    showGlobalMessage(message, type) {
        // Show a flash-like message at the top of the page
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        messageDiv.style.cssText = 'top: 20px; right: 20px; z-index: 10000; max-width: 400px;';
        messageDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(messageDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 5000);
    }
    
    getCSRFToken() {
        // Try to get CSRF token from meta tag
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }
        
        // Fallback: get from form
        const tokenInput = document.querySelector('input[name="csrf_token"]');
        if (tokenInput) {
            return tokenInput.value;
        }
        
        console.warn('CSRF token not found');
        return '';
    }
    
    showError(message) {
        this.showGlobalMessage(message, 'danger');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.tripModalManager = new TripModalManager();
});

// CSS for spinning animation
const style = document.createElement('style');
style.textContent = `
    .spin {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .trip-modal {
        opacity: 0;
        visibility: hidden;
        transition: opacity 0.3s ease, visibility 0.3s ease;
    }
    
    .trip-modal.show {
        opacity: 1;
        visibility: visible;
    }
`;
document.head.appendChild(style);