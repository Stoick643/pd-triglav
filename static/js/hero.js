/**
 * Hero Landing Page JavaScript
 * Handles parallax effects, animations, and lazy loading
 */

document.addEventListener('DOMContentLoaded', function() {
    initHeroParallax();
    initHeroAnimations();
    initScrollIndicator();
});

/**
 * Initializes smooth parallax scrolling effect for hero background image
 */
function initHeroParallax() {
    const heroSection = document.querySelector('.hero-section');
    const heroBackground = document.querySelector('.hero-background');
    
    if (!heroSection || !heroBackground) return;
    
    // Check if user prefers reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }
    
    let ticking = false;
    
    function updateParallax() {
        const scrolled = window.pageYOffset;
        const viewportHeight = window.innerHeight;
        const heroHeight = heroSection.offsetHeight;
        
        // Only apply parallax when hero is visible
        if (scrolled < heroHeight) {
            const rate = scrolled * -0.5;
            heroBackground.style.transform = `translate3d(0, ${rate}px, 0)`;
        }
        
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            ticking = true;
            requestAnimationFrame(updateParallax);
        }
    }
    
    // Throttle scroll events
    window.addEventListener('scroll', requestTick, { passive: true });
    
    // Handle resize
    window.addEventListener('resize', function() {
        if (!ticking) {
            requestTick();
        }
    });
}

/**
 * Handles entrance animations for hero text and CTA buttons on page load
 */
function initHeroAnimations() {
    const heroContent = document.querySelector('.hero-content');
    
    if (!heroContent) return;
    
    // Check if user prefers reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return;
    }
    
    // Add staggered animation delays
    const heroTitle = heroContent.querySelector('.hero-title');
    const heroSubtitle = heroContent.querySelector('.hero-subtitle');
    const heroStats = heroContent.querySelector('.hero-stats');
    const heroButtons = heroContent.querySelector('.hero-cta-buttons');
    
    const elementsToAnimate = [
        { element: heroTitle, delay: 0 },
        { element: heroSubtitle, delay: 300 },
        { element: heroStats, delay: 600 },
        { element: heroButtons, delay: 900 }
    ];
    
    elementsToAnimate.forEach(({ element, delay }) => {
        if (element) {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
            element.style.transition = 'opacity 0.8s ease-out, transform 0.8s ease-out';
            
            setTimeout(() => {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }, delay);
        }
    });
}

/**
 * Initializes scroll indicator functionality
 */
function initScrollIndicator() {
    const scrollIndicator = document.querySelector('.hero-scroll-indicator');
    const scrollArrow = document.querySelector('.scroll-arrow');
    
    if (!scrollIndicator || !scrollArrow) return;
    
    // Smooth scroll to content when clicked
    scrollArrow.addEventListener('click', function() {
        const nextSection = document.querySelector('#hero').nextElementSibling;
        if (nextSection) {
            nextSection.scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
    
    // Hide scroll indicator when scrolling down
    let scrollTimeout;
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        
        clearTimeout(scrollTimeout);
        
        if (scrolled > 100) {
            scrollIndicator.style.opacity = '0';
            scrollIndicator.style.transform = 'translateX(-50%) translateY(20px)';
        } else {
            scrollIndicator.style.opacity = '0.8';
            scrollIndicator.style.transform = 'translateX(-50%) translateY(0)';
        }
        
        // Add transition delay to prevent flickering
        scrollTimeout = setTimeout(() => {
            scrollIndicator.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        }, 50);
    }, { passive: true });
}

/**
 * Implements progressive image loading with blur-to-sharp transition effect
 */
function lazyLoadHeroImage() {
    const heroBackground = document.querySelector('.hero-background');
    
    if (!heroBackground) return;
    
    const imageUrl = heroBackground.style.backgroundImage.match(/url\(["']?(.*?)["']?\)/);
    
    if (!imageUrl || !imageUrl[1]) return;
    
    // Create a new image to preload
    const img = new Image();
    
    img.onload = function() {
        heroBackground.style.filter = 'blur(0px)';
        heroBackground.style.transition = 'filter 0.5s ease-out';
    };
    
    img.onerror = function() {
        console.warn('Hero image failed to load:', imageUrl[1]);
        // Fallback to a solid color background
        heroBackground.style.background = 'linear-gradient(135deg, var(--pd-primary) 0%, var(--pd-primary-dark) 100%)';
    };
    
    // Start with blurred image
    heroBackground.style.filter = 'blur(5px)';
    heroBackground.style.transition = 'filter 0.5s ease-out';
    
    // Start loading the image
    img.src = imageUrl[1];
}

/**
 * Handles hero section resize for responsive behavior
 */
function handleHeroResize() {
    const heroSection = document.querySelector('.hero-section');
    
    if (!heroSection) return;
    
    function updateHeroHeight() {
        const viewportHeight = window.innerHeight;
        const isMobile = window.innerWidth <= 768;
        
        // Adjust hero height based on viewport and device
        if (isMobile) {
            heroSection.style.minHeight = Math.max(viewportHeight * 0.9, 600) + 'px';
        } else {
            heroSection.style.minHeight = viewportHeight + 'px';
        }
    }
    
    // Update on load and resize
    updateHeroHeight();
    window.addEventListener('resize', updateHeroHeight);
}

// Initialize responsive behavior
handleHeroResize();

// Initialize lazy loading
lazyLoadHeroImage();