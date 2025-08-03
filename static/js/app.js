/*
PD Triglav - Application JavaScript
Simple, clean navigation functionality
*/

document.addEventListener('DOMContentLoaded', function() {
    
    // === BASIC FORM ENHANCEMENTS === //
    
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
    
    // === SIDEBAR NAVIGATION === //
    
    initSidebar();
    
    function initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const sidebarToggle = document.getElementById('sidebar-toggle');
        const sidebarOverlay = document.getElementById('sidebar-overlay');
        
        // Mobile sidebar toggle
        if (sidebarToggle && sidebar && sidebarOverlay) {
            sidebarToggle.addEventListener('click', function(e) {
                e.preventDefault();
                toggleSidebar();
            });
            
            // Close sidebar when clicking overlay
            sidebarOverlay.addEventListener('click', function() {
                closeSidebar();
            });
            
            // Close sidebar on Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && sidebar.classList.contains('show')) {
                    closeSidebar();
                }
            });
        }
        
        // Expandable navigation sections - SIMPLE VERSION
        const navToggles = document.querySelectorAll('.nav-toggle');
        
        navToggles.forEach(toggle => {
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                
                const toggleId = this.getAttribute('data-toggle');
                const submenu = document.getElementById(toggleId + '-submenu');
                const toggleIcon = this.querySelector('.toggle-icon');
                
                if (!submenu || !toggleIcon) return;
                
                // Simple toggle logic
                const isExpanded = submenu.classList.contains('expanded');
                
                if (isExpanded) {
                    // Collapse
                    submenu.classList.remove('expanded');
                    toggleIcon.classList.remove('rotated');
                    this.setAttribute('aria-expanded', 'false');
                    submenu.style.maxHeight = '0px';
                } else {
                    // Expand
                    submenu.classList.add('expanded');
                    toggleIcon.classList.add('rotated');
                    this.setAttribute('aria-expanded', 'true');
                    submenu.style.maxHeight = submenu.scrollHeight + 'px';
                    
                    // Reset to auto after animation
                    setTimeout(() => {
                        if (submenu.classList.contains('expanded')) {
                            submenu.style.maxHeight = 'auto';
                        }
                    }, 300);
                }
            });
        });
        
        // Set active navigation states (but don't override server-side expansion)
        updateActiveStates();
        
        // Handle window resize
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 992 && sidebar.classList.contains('show')) {
                closeSidebar();
            }
        });
    }
    
    function toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        if (sidebar && overlay) {
            const isOpen = sidebar.classList.contains('show');
            
            if (isOpen) {
                closeSidebar();
            } else {
                openSidebar();
            }
        }
    }
    
    function openSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        sidebar?.classList.add('show');
        overlay?.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus first navigation item for accessibility
        const firstNavLink = sidebar?.querySelector('.nav-link');
        firstNavLink?.focus();
    }
    
    function closeSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        sidebar?.classList.remove('show');
        overlay?.classList.remove('show');
        document.body.style.overflow = '';
        
        // Return focus to toggle button
        const toggle = document.getElementById('sidebar-toggle');
        toggle?.focus();
    }
    
    function updateActiveStates() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.sidebar-nav .nav-link, .nav-submenu a');
        
        // Remove all active classes
        navLinks.forEach(link => link.classList.remove('active'));
        
        // Find best matching link
        let bestMatch = null;
        let bestMatchLength = 0;
        
        navLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href && href !== '#') {
                if (href === currentPath) {
                    // Exact match - use this
                    bestMatch = link;
                    bestMatchLength = href.length;
                } else if (currentPath.startsWith(href) && href.length > bestMatchLength && href !== '/') {
                    // Partial match - use if longer than current best
                    bestMatch = link;
                    bestMatchLength = href.length;
                }
            }
        });
        
        // Apply active state
        if (bestMatch) {
            bestMatch.classList.add('active');
        }
    }
    
    // Server-side rendering now handles initial expansion state
    // JavaScript only needed for interactive clicking, not initial state
});