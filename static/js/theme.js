/**
 * PD Triglav Theme Controller
 * Handles light/dark theme switching with persistence
 */

class ThemeController {
    constructor() {
        this.storageKey = 'pd-triglav-theme';
        this.themes = ['light', 'dark', 'auto'];
        this.currentTheme = this.getStoredTheme() || 'auto';
        
        this.init();
    }
    
    init() {
        // Wait for CSS to be loaded before applying theme
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.applyTheme(this.currentTheme);
            });
        } else {
            this.applyTheme(this.currentTheme);
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
                if (this.currentTheme === 'auto') {
                    this.applyTheme('auto');
                }
            });
        }
        
        // Initialize toggle button if present
        this.initToggleButton();
    }
    
    getStoredTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            console.warn('Theme storage not available:', e);
            return null;
        }
    }
    
    setStoredTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            console.warn('Theme storage not available:', e);
        }
    }
    
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }
    
    getEffectiveTheme(theme) {
        if (theme === 'auto') {
            return this.getSystemTheme();
        }
        return theme;
    }
    
    applyTheme(theme) {
        const effectiveTheme = this.getEffectiveTheme(theme);
        
        // Apply to document
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        
        // Update meta theme-color for mobile browsers
        this.updateThemeColor(effectiveTheme);
        
        // Store preference
        this.setStoredTheme(theme);
        this.currentTheme = theme;
        
        // Update toggle button if present
        this.updateToggleButton();
        
        // Dispatch custom event
        document.dispatchEvent(new CustomEvent('themechange', {
            detail: { theme: theme, effectiveTheme: effectiveTheme }
        }));
    }
    
    updateThemeColor(effectiveTheme) {
        let themeColor = '#f7f5f1'; // Light theme surface
        if (effectiveTheme === 'dark') {
            themeColor = '#18191a'; // Dark theme surface
        }
        
        let metaTag = document.querySelector('meta[name="theme-color"]');
        if (!metaTag) {
            metaTag = document.createElement('meta');
            metaTag.name = 'theme-color';
            document.head.appendChild(metaTag);
        }
        metaTag.content = themeColor;
    }
    
    cycleTheme() {
        const currentIndex = this.themes.indexOf(this.currentTheme);
        const nextIndex = (currentIndex + 1) % this.themes.length;
        const nextTheme = this.themes[nextIndex];
        
        this.applyTheme(nextTheme);
    }
    
    setTheme(theme) {
        if (this.themes.includes(theme)) {
            this.applyTheme(theme);
        }
    }
    
    initToggleButton() {
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.cycleTheme();
            });
            
            this.updateToggleButton();
        }
    }
    
    updateToggleButton() {
        const toggleButton = document.getElementById('theme-toggle');
        if (!toggleButton) return;
        
        const icons = {
            light: 'bi-sun-fill',
            dark: 'bi-moon-fill',
            auto: 'bi-circle-half'
        };
        
        const labels = {
            light: 'Svetla tema',
            dark: 'Temna tema', 
            auto: 'Sistemska tema'
        };
        
        // Update icon
        const icon = toggleButton.querySelector('i');
        if (icon) {
            icon.className = `bi ${icons[this.currentTheme]}`;
        }
        
        // Update tooltip/title
        toggleButton.title = labels[this.currentTheme];
        
        // Update screen reader text
        const srText = toggleButton.querySelector('.sr-only');
        if (srText) {
            srText.textContent = labels[this.currentTheme];
        }
    }
    
    // Public API
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    getEffectiveCurrentTheme() {
        return this.getEffectiveTheme(this.currentTheme);
    }
}

// Initialize theme controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeController = new ThemeController();
});

// Expose theme controller globally for debugging
window.ThemeController = ThemeController;