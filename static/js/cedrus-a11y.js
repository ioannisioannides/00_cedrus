/**
 * Cedrus Accessibility Module
 * Comprehensive WCAG 2.1 AAA accessibility utilities
 */

(function(window) {
    'use strict';

    const CedrusA11y = {
        version: '1.0.0',
        
        // Configuration
        config: {
            announceDelay: 100,
            focusTrapEnabled: true,
            keyboardNavEnabled: true,
        },

        // State management
        state: {
            focusTraps: new Map(),
            shortcuts: new Map(),
            keyboardMode: false,
        },

        /**
         * Initialize accessibility features
         */
        init: function() {
            this.setupKeyboardDetection();
            this.setupAriaLiveRegion();
            this.registerDefaultShortcuts();
            this.enhanceInteractiveElements();
            console.log('✓ Cedrus Accessibility initialized');
        },

        /**
         * Detect keyboard navigation mode
         */
        setupKeyboardDetection: function() {
            let mouseUsed = false;
            
            document.addEventListener('mousedown', () => {
                mouseUsed = true;
                document.body.classList.remove('keyboard-nav-mode');
                this.state.keyboardMode = false;
            });

            document.addEventListener('keydown', (e) => {
                if (e.key === 'Tab' && !mouseUsed) {
                    document.body.classList.add('keyboard-nav-mode');
                    this.state.keyboardMode = true;
                }
            });
        },

        /**
         * Create ARIA live region for announcements
         */
        setupAriaLiveRegion: function() {
            if (!document.getElementById('aria-announcer')) {
                const announcer = document.createElement('div');
                announcer.id = 'aria-announcer';
                announcer.className = 'sr-only';
                announcer.setAttribute('aria-live', 'polite');
                announcer.setAttribute('aria-atomic', 'true');
                announcer.setAttribute('role', 'status');
                document.body.appendChild(announcer);
            }
        },

        /**
         * Announce message to screen readers
         * @param {string} message - Message to announce
         * @param {string} priority - 'polite' or 'assertive'
         */
        announce: function(message, priority = 'polite') {
            const announcer = document.getElementById('aria-announcer');
            if (!announcer) return;

            announcer.setAttribute('aria-live', priority);
            
            // Clear and set with delay to ensure announcement
            announcer.textContent = '';
            setTimeout(() => {
                announcer.textContent = message;
            }, this.config.announceDelay);

            // Auto-clear after announcement
            setTimeout(() => {
                announcer.textContent = '';
            }, 3000);
        },

        /**
         * Create focus trap for modals/dialogs
         * @param {HTMLElement} element - Element to trap focus within
         * @param {Object} options - Configuration options
         * @returns {Object} Focus trap controller
         */
        createFocusTrap: function(element, options = {}) {
            if (!this.config.focusTrapEnabled) return null;

            const {
                initialFocus = null,
                onEscape = null,
                restoreFocus = true,
            } = options;

            const previouslyFocused = document.activeElement;
            
            const getFocusableElements = () => {
                return element.querySelectorAll(
                    'a[href], button:not([disabled]), textarea:not([disabled]), ' +
                    'input:not([disabled]), select:not([disabled]), ' +
                    '[tabindex]:not([tabindex="-1"]):not([disabled])'
                );
            };

            const handleTab = (e) => {
                const focusables = Array.from(getFocusableElements());
                const firstFocusable = focusables[0];
                const lastFocusable = focusables[focusables.length - 1];

                if (e.key !== 'Tab') return;

                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        e.preventDefault();
                        lastFocusable?.focus();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        e.preventDefault();
                        firstFocusable?.focus();
                    }
                }
            };

            const handleEscape = (e) => {
                if (e.key === 'Escape') {
                    if (onEscape) onEscape(e);
                    trap.destroy();
                }
            };

            const trap = {
                activate: () => {
                    element.addEventListener('keydown', handleTab);
                    element.addEventListener('keydown', handleEscape);
                    
                    const focusTarget = initialFocus || getFocusableElements()[0];
                    focusTarget?.focus();
                    
                    this.state.focusTraps.set(element, trap);
                    this.announce('Dialog opened. Press Escape to close.', 'polite');
                },
                
                destroy: () => {
                    element.removeEventListener('keydown', handleTab);
                    element.removeEventListener('keydown', handleEscape);
                    
                    if (restoreFocus && previouslyFocused) {
                        previouslyFocused.focus();
                    }
                    
                    this.state.focusTraps.delete(element);
                    this.announce('Dialog closed', 'polite');
                },
            };

            trap.activate();
            return trap;
        },

        /**
         * Register keyboard shortcut
         * @param {string} key - Key to bind
         * @param {Function} callback - Function to execute
         * @param {Object} options - Shortcut options
         */
        registerShortcut: function(key, callback, options = {}) {
            const {
                ctrl = false,
                alt = false,
                shift = false,
                description = '',
                scope = 'global',
            } = options;

            const shortcutId = this.createShortcutId(key, ctrl, alt, shift);
            
            this.state.shortcuts.set(shortcutId, {
                callback,
                description,
                scope,
                ctrl,
                alt,
                shift,
                key,
            });
        },

        /**
         * Create unique shortcut ID
         */
        createShortcutId: function(key, ctrl, alt, shift) {
            const parts = [];
            if (ctrl) parts.push('ctrl');
            if (alt) parts.push('alt');
            if (shift) parts.push('shift');
            parts.push(key.toLowerCase());
            return parts.join('+');
        },

        /**
         * Handle keyboard shortcuts
         */
        handleShortcut: function(e) {
            const shortcutId = this.createShortcutId(
                e.key,
                e.ctrlKey || e.metaKey,
                e.altKey,
                e.shiftKey
            );

            const shortcut = this.state.shortcuts.get(shortcutId);
            
            if (shortcut) {
                // Don't interfere with input fields unless explicitly allowed
                const tagName = e.target.tagName;
                if (['INPUT', 'TEXTAREA', 'SELECT'].includes(tagName) && shortcut.scope === 'global') {
                    return;
                }

                e.preventDefault();
                shortcut.callback(e);
                return false;
            }
        },

        /**
         * Register default keyboard shortcuts
         */
        registerDefaultShortcuts: function() {
            // Focus search (/)
            this.registerShortcut('/', () => {
                const search = document.querySelector('input[type="search"], input[name="search"]');
                if (search) {
                    search.focus();
                    this.announce('Search field focused', 'polite');
                }
            }, { description: 'Focus search' });

            // Show keyboard shortcuts help (?)
            this.registerShortcut('?', () => {
                this.showShortcutsHelp();
            }, { description: 'Show keyboard shortcuts help', shift: true });

            // Go to dashboard (Ctrl+D)
            this.registerShortcut('d', () => {
                const dashLink = document.querySelector('a[href*="dashboard"]');
                if (dashLink) {
                    window.location.href = dashLink.href;
                }
            }, { description: 'Go to dashboard', ctrl: true });

            // Toggle theme (Alt+T)
            this.registerShortcut('t', () => {
                const themeToggle = document.getElementById('theme-toggle');
                if (themeToggle) {
                    themeToggle.click();
                }
            }, { description: 'Toggle theme', alt: true });

            // Global shortcut handler
            document.addEventListener('keydown', this.handleShortcut.bind(this));
        },

        /**
         * Show keyboard shortcuts help modal
         */
        showShortcutsHelp: function() {
            const shortcuts = Array.from(this.state.shortcuts.entries()).map(([id, data]) => ({
                keys: id,
                description: data.description
            }));

            const helpText = shortcuts
                .map(s => `${s.keys}: ${s.description}`)
                .join('\n');

            this.announce(`Keyboard shortcuts available. ${shortcuts.length} shortcuts registered.`, 'polite');
            
            console.log('Keyboard Shortcuts:\n', helpText);
        },

        /**
         * Enhance interactive elements with ARIA
         */
        enhanceInteractiveElements: function() {
            // Add aria-label to icon-only buttons
            document.querySelectorAll('button:not([aria-label])').forEach(btn => {
                if (btn.querySelector('i, svg') && !btn.textContent.trim()) {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        const iconClass = Array.from(icon.classList).find(c => c.startsWith('bi-'));
                        if (iconClass) {
                            const label = iconClass.replace('bi-', '').replace(/-/g, ' ');
                            btn.setAttribute('aria-label', label);
                        }
                    }
                }
            });

            // Ensure all links have accessible text
            document.querySelectorAll('a:not([aria-label])').forEach(link => {
                if (!link.textContent.trim() && !link.getAttribute('aria-label')) {
                    const img = link.querySelector('img');
                    if (img && img.alt) {
                        link.setAttribute('aria-label', img.alt);
                    }
                }
            });
        },

        /**
         * Create loading indicator with accessible label
         * @param {string} label - Loading message
         * @returns {HTMLElement} Loading element
         */
        createLoader: function(label = 'Loading...') {
            const loader = document.createElement('div');
            loader.className = 'spinner';
            loader.setAttribute('role', 'status');
            loader.setAttribute('aria-label', label);
            
            const srText = document.createElement('span');
            srText.className = 'sr-only';
            srText.textContent = label;
            loader.appendChild(srText);
            
            return loader;
        },
    };

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => CedrusA11y.init());
    } else {
        CedrusA11y.init();
    }

    // Export to window
    window.CedrusA11y = CedrusA11y;

})(window);
