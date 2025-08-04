/**
 * PD Triglav Photo Lightbox
 * Professional photo viewing experience for mountain trip galleries
 */

class PDTriglavLightbox {
    constructor() {
        this.currentIndex = 0;
        this.photos = [];
        this.isOpen = false;
        this.touchStartX = null;
        this.touchStartY = null;
        
        // Create modal elements
        this.createLightboxElements();
        
        // Bind event handlers
        this.bindEvents();
    }
    
    createLightboxElements() {
        // Main modal container
        const modalHTML = `
            <div id="pdtriglav-lightbox" class="lightbox-modal" role="dialog" aria-modal="true" aria-labelledby="lightbox-caption">
                <div class="lightbox-overlay"></div>
                <div class="lightbox-container">
                    <button class="lightbox-close" aria-label="Zapri galerijo" title="Zapri (ESC)">
                        <i class="bi bi-x-lg"></i>
                    </button>
                    
                    <div class="lightbox-content">
                        <div class="lightbox-image-wrapper">
                            <img class="lightbox-image" alt="" />
                            <div class="lightbox-loading">
                                <div class="spinner-border text-light" role="status">
                                    <span class="visually-hidden">Nalaganje...</span>
                                </div>
                            </div>
                        </div>
                        
                        <div class="lightbox-nav">
                            <button class="lightbox-prev" aria-label="Prejšnja fotografija" title="Prejšnja (←)">
                                <i class="bi bi-chevron-left"></i>
                            </button>
                            <button class="lightbox-next" aria-label="Naslednja fotografija" title="Naslednja (→)">
                                <i class="bi bi-chevron-right"></i>
                            </button>
                        </div>
                        
                        <div class="lightbox-info">
                            <div class="lightbox-counter">
                                <span class="current-photo">1</span> / <span class="total-photos">1</span>
                            </div>
                            <div class="lightbox-caption" id="lightbox-caption"></div>
                            <div class="lightbox-metadata"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Cache elements
        this.modal = document.getElementById('pdtriglav-lightbox');
        this.overlay = this.modal.querySelector('.lightbox-overlay');
        this.image = this.modal.querySelector('.lightbox-image');
        this.loading = this.modal.querySelector('.lightbox-loading');
        this.closeBtn = this.modal.querySelector('.lightbox-close');
        this.prevBtn = this.modal.querySelector('.lightbox-prev');
        this.nextBtn = this.modal.querySelector('.lightbox-next');
        this.counter = this.modal.querySelector('.lightbox-counter');
        this.caption = this.modal.querySelector('.lightbox-caption');
        this.metadata = this.modal.querySelector('.lightbox-metadata');
    }
    
    bindEvents() {
        // Close events
        this.closeBtn.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', () => this.close());
        
        // Navigation
        this.prevBtn.addEventListener('click', () => this.navigate(-1));
        this.nextBtn.addEventListener('click', () => this.navigate(1));
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));
        
        // Touch gestures for mobile
        this.modal.addEventListener('touchstart', (e) => this.handleTouchStart(e), { passive: true });
        this.modal.addEventListener('touchend', (e) => this.handleTouchEnd(e), { passive: true });
        
        // Prevent image drag
        this.image.addEventListener('dragstart', (e) => e.preventDefault());
    }
    
    init() {
        // Find all photo links in galleries
        const galleries = document.querySelectorAll('.photo-mosaic, .photo-gallery');
        
        galleries.forEach(gallery => {
            const photoLinks = gallery.querySelectorAll('.photo-link');
            const photos = Array.from(photoLinks).map((link, index) => {
                const img = link.querySelector('.photo-img');
                const captionEl = link.querySelector('.photo-caption-overlay');
                const metaEl = link.querySelector('.photo-meta-overlay');
                
                return {
                    url: link.href,
                    caption: captionEl ? captionEl.textContent.trim() : img.alt,
                    metadata: metaEl ? metaEl.textContent.trim() : '',
                    element: link,
                    index: index
                };
            });
            
            // Attach click handlers
            photoLinks.forEach((link, index) => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.open(photos, index);
                });
            });
        });
    }
    
    open(photos, startIndex = 0) {
        this.photos = photos;
        this.currentIndex = startIndex;
        this.isOpen = true;
        
        // Show modal
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Update navigation visibility
        this.updateNavigation();
        
        // Load current photo
        this.loadPhoto(this.currentIndex);
        
        // Preload adjacent photos
        this.preloadAdjacent();
        
        // Focus for accessibility
        this.modal.focus();
        
        // Announce to screen readers
        this.announcePhoto();
    }
    
    close() {
        if (!this.isOpen) return;
        
        this.isOpen = false;
        this.modal.classList.remove('show');
        document.body.style.overflow = '';
        
        // Clear image to free memory
        this.image.src = '';
        
        // Return focus to trigger element
        if (this.photos[this.currentIndex]?.element) {
            this.photos[this.currentIndex].element.focus();
        }
    }
    
    navigate(direction) {
        const newIndex = this.currentIndex + direction;
        
        if (newIndex >= 0 && newIndex < this.photos.length) {
            this.currentIndex = newIndex;
            this.loadPhoto(this.currentIndex);
            this.updateNavigation();
            this.preloadAdjacent();
            this.announcePhoto();
        }
    }
    
    loadPhoto(index) {
        const photo = this.photos[index];
        if (!photo) return;
        
        // Show loading
        this.loading.style.display = 'flex';
        this.image.style.opacity = '0';
        
        // Create new image to preload
        const tempImg = new Image();
        
        tempImg.onload = () => {
            // Update main image
            this.image.src = photo.url;
            this.image.alt = photo.caption || `Fotografija ${index + 1} od ${this.photos.length}`;
            
            // Fade in
            requestAnimationFrame(() => {
                this.loading.style.display = 'none';
                this.image.style.opacity = '1';
            });
            
            // Update info
            this.updatePhotoInfo(photo);
        };
        
        tempImg.onerror = () => {
            this.loading.style.display = 'none';
            this.showError();
        };
        
        tempImg.src = photo.url;
    }
    
    updatePhotoInfo(photo) {
        // Counter
        this.counter.querySelector('.current-photo').textContent = this.currentIndex + 1;
        this.counter.querySelector('.total-photos').textContent = this.photos.length;
        
        // Caption
        this.caption.textContent = photo.caption || '';
        
        // Metadata
        this.metadata.textContent = photo.metadata || '';
    }
    
    updateNavigation() {
        // Show/hide navigation buttons
        this.prevBtn.style.display = this.currentIndex > 0 ? 'flex' : 'none';
        this.nextBtn.style.display = this.currentIndex < this.photos.length - 1 ? 'flex' : 'none';
        
        // Update counter
        this.counter.style.display = this.photos.length > 1 ? 'block' : 'none';
    }
    
    preloadAdjacent() {
        // Preload next photo
        if (this.currentIndex < this.photos.length - 1) {
            const nextImg = new Image();
            nextImg.src = this.photos[this.currentIndex + 1].url;
        }
        
        // Preload previous photo
        if (this.currentIndex > 0) {
            const prevImg = new Image();
            prevImg.src = this.photos[this.currentIndex - 1].url;
        }
    }
    
    handleKeyboard(e) {
        if (!this.isOpen) return;
        
        switch(e.key) {
            case 'Escape':
                e.preventDefault();
                this.close();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                this.navigate(-1);
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.navigate(1);
                break;
        }
    }
    
    handleTouchStart(e) {
        if (!this.isOpen) return;
        
        const touch = e.touches[0];
        this.touchStartX = touch.clientX;
        this.touchStartY = touch.clientY;
    }
    
    handleTouchEnd(e) {
        if (!this.isOpen || !this.touchStartX) return;
        
        const touch = e.changedTouches[0];
        const deltaX = touch.clientX - this.touchStartX;
        const deltaY = touch.clientY - this.touchStartY;
        
        // Reset
        this.touchStartX = null;
        this.touchStartY = null;
        
        // Check if horizontal swipe
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            if (deltaX > 0) {
                this.navigate(-1); // Swipe right - previous
            } else {
                this.navigate(1); // Swipe left - next
            }
        }
    }
    
    showError() {
        this.image.style.display = 'none';
        this.caption.innerHTML = '<i class="bi bi-exclamation-triangle me-2"></i>Fotografije ni mogoče naložiti';
        this.metadata.textContent = '';
    }
    
    announcePhoto() {
        // Announce current photo to screen readers
        const announcement = `Fotografija ${this.currentIndex + 1} od ${this.photos.length}. ${this.photos[this.currentIndex].caption || ''}`;
        
        // Create temporary live region
        const liveRegion = document.createElement('div');
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        liveRegion.className = 'visually-hidden';
        liveRegion.textContent = announcement;
        
        document.body.appendChild(liveRegion);
        
        setTimeout(() => {
            document.body.removeChild(liveRegion);
        }, 1000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.pdTriglavLightbox = new PDTriglavLightbox();
    window.pdTriglavLightbox.init();
});

// Reinitialize after HTMX content updates
document.body.addEventListener('htmx:afterSwap', () => {
    if (window.pdTriglavLightbox) {
        window.pdTriglavLightbox.init();
    }
});