/*
PD Triglav - Application JavaScript
Subtle interactions and progressive enhancement
*/

document.addEventListener('DOMContentLoaded', function() {
    
    // === PROGRESSIVE ENHANCEMENT === //
    
    // Add enhanced classes to forms if JavaScript is enabled
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
        if (!control.classList.contains('form-control-enhanced')) {
            control.classList.add('focus-visible');
        }
    });
    
    // === CARD INTERACTIONS === //
    
    // Add subtle hover effects to interactive cards
    const interactiveCards = document.querySelectorAll('.trip-card, .card');
    interactiveCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transition = 'all 200ms cubic-bezier(0.4, 0, 0.2, 1)';
        });
    });
    
    // === FORM ENHANCEMENTS === //
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) return;
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.style.transition = 'opacity 300ms ease-out, transform 300ms ease-out';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-10px)';
                
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }
        }, 5000);
    });
    
    // Form validation feedback
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let hasErrors = false;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    hasErrors = true;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            // Add subtle shake animation to form if there are errors
            if (hasErrors) {
                form.style.animation = 'shake 0.5s cubic-bezier(0.36, 0.07, 0.19, 0.97)';
                setTimeout(() => {
                    form.style.animation = '';
                }, 500);
            }
        });
        
        // Remove validation classes on input
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                this.classList.remove('is-invalid', 'is-valid');
            });
        });
    });
    
    // === BUTTON ENHANCEMENTS === //
    
    // Add loading state to form buttons
    const submitButtons = document.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(button => {
        const form = button.closest('form');
        if (!form) return;
        
        form.addEventListener('submit', function() {
            if (button.classList.contains('btn-mountain') || button.classList.contains('btn-mountain-outline')) {
                const originalText = button.innerHTML;
                button.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Pošiljam...';
                button.disabled = true;
                
                // Re-enable after 3 seconds as fallback
                setTimeout(() => {
                    button.innerHTML = originalText;
                    button.disabled = false;
                }, 3000);
            }
        });
    });
    
    // === NAVIGATION ENHANCEMENTS === //
    
    // Highlight active navigation items
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
            link.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
            link.style.borderRadius = 'var(--pd-radius)';
        }
    });
    
    // === ACCESSIBILITY ENHANCEMENTS === //
    
    // Keyboard navigation for cards
    const clickableCards = document.querySelectorAll('.trip-card, [data-clickable]');
    clickableCards.forEach(card => {
        // Make card focusable
        if (!card.getAttribute('tabindex')) {
            card.setAttribute('tabindex', '0');
        }
        
        // Handle keyboard navigation
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const link = card.querySelector('a');
                if (link) {
                    link.click();
                }
            }
        });
    });
    
    // === SMOOTH SCROLLING === //
    
    // Smooth scroll for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // === PERFORMANCE OPTIMIZATIONS === //
    
    // Lazy load images when they come into view
    const lazyImages = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.removeAttribute('data-src');
                img.classList.add('fade-in');
                observer.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
    
    // === MOUNTAIN-THEMED EASTER EGGS === //
    
    // Add subtle mountain peaks to page borders on special occasions
    const today = new Date();
    const isMountainDay = today.getMonth() === 6 && today.getDate() === 11; // International Mountain Day
    
    if (isMountainDay) {
        document.body.style.borderTop = '4px solid var(--pd-primary)';
        document.body.style.borderImage = 'linear-gradient(90deg, var(--pd-primary) 0%, var(--pd-primary-light) 50%, var(--pd-primary) 100%) 1';
        
        // Add a subtle notification
        const mountainNotice = document.createElement('div');
        mountainNotice.innerHTML = `
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                <i class="bi bi-mountain me-2"></i>
                Danes je mednarodni dan gora! 🏔️
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        document.querySelector('main').prepend(mountainNotice);
    }
});

// === CSS ANIMATIONS === //

// Add CSS animations via JavaScript for better performance
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        10%, 90% { transform: translate3d(-1px, 0, 0); }
        20%, 80% { transform: translate3d(2px, 0, 0); }
        30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
        40%, 60% { transform: translate3d(4px, 0, 0); }
    }
    
    .is-invalid {
        border-color: var(--pd-danger) !important;
        box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1) !important;
    }
    
    .is-valid {
        border-color: var(--pd-success) !important;
        box-shadow: 0 0 0 3px rgba(81, 207, 102, 0.1) !important;
    }
    
    /* Loading spinner for buttons */
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .bi-arrow-clockwise {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);