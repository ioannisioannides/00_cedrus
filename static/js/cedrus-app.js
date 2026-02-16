/**
 * Cedrus Application Module
 * =========================
 * Core application functionality extracted from base.html inline scripts.
 * Handles: dropdown navigation, theme toggle, sidebar, toasts, page animations.
 *
 * @version 1.0.0
 */

(function () {
    'use strict';

    // ============================================
    // DROPDOWN HANDLER (replaces Bootstrap JS)
    // ============================================

    function initDropdowns() {
        document.addEventListener('click', function (e) {
            // Close all dropdowns when clicking outside
            document.querySelectorAll('.dropdown-menu.show').forEach(function (menu) {
                if (!menu.parentElement.contains(e.target)) {
                    menu.classList.remove('show');
                }
            });

            // Toggle dropdown on click
            var toggle = e.target.closest('[data-dropdown-toggle]');
            if (toggle) {
                e.preventDefault();
                var menu = toggle.nextElementSibling;
                if (menu && menu.classList.contains('dropdown-menu')) {
                    document.querySelectorAll('.dropdown-menu.show').forEach(function (m) {
                        if (m !== menu) m.classList.remove('show');
                    });
                    menu.classList.toggle('show');
                }
            }
        });

        // Keyboard navigation for dropdowns
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                document.querySelectorAll('.dropdown-menu.show').forEach(function (menu) {
                    menu.classList.remove('show');
                    // Return focus to the toggle button
                    var toggle = menu.previousElementSibling;
                    if (toggle && toggle.hasAttribute('data-dropdown-toggle')) {
                        toggle.focus();
                    }
                });
            }
        });
    }

    // ============================================
    // THEME TOGGLE
    // ============================================

    function initThemeToggle() {
        var toggle = document.getElementById('theme-toggle');
        var sun = document.getElementById('theme-icon-sun');
        var moon = document.getElementById('theme-icon-moon');
        var html = document.documentElement;

        var saved = localStorage.getItem('theme');
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        var theme = saved || (prefersDark ? 'dark' : 'light');

        function applyTheme(t) {
            html.setAttribute('data-theme', t);
            if (t === 'dark') {
                if (sun) sun.style.display = '';
                if (moon) moon.style.display = 'none';
            } else {
                if (sun) sun.style.display = 'none';
                if (moon) moon.style.display = '';
            }
            // Announce theme change to screen readers
            if (window.CedrusA11y) {
                window.CedrusA11y.announce(
                    t === 'dark' ? 'Dark theme activated' : 'Light theme activated',
                    'polite'
                );
            }
        }

        applyTheme(theme);

        if (toggle) {
            toggle.addEventListener('click', function () {
                theme = theme === 'dark' ? 'light' : 'dark';
                localStorage.setItem('theme', theme);
                applyTheme(theme);
            });
        }
    }

    // ============================================
    // SIDEBAR TOGGLE (Mobile)
    // ============================================

    function initSidebar() {
        var sidebar = document.getElementById('sidebar');
        var overlay = document.getElementById('sidebar-overlay');
        var openBtn = document.getElementById('sidebar-open');
        var closeBtn = document.getElementById('sidebar-close');

        function openSidebar() {
            if (sidebar) sidebar.classList.add('open');
            if (overlay) overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            if (window.CedrusA11y) {
                window.CedrusA11y.announce('Navigation sidebar opened', 'polite');
            }
        }

        function closeSidebar() {
            if (sidebar) sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
            document.body.style.overflow = '';
        }

        if (openBtn) openBtn.addEventListener('click', openSidebar);
        if (closeBtn) closeBtn.addEventListener('click', closeSidebar);
        if (overlay) overlay.addEventListener('click', closeSidebar);

        // Close sidebar on Escape
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
                closeSidebar();
                if (openBtn) openBtn.focus();
            }
        });
    }

    // ============================================
    // AUTO-DISMISS TOASTS
    // ============================================

    function initToasts() {
        document.querySelectorAll('.cedrus-toast').forEach(function (toast) {
            toast.style.animation = 'slideInRight 0.4s cubic-bezier(0.16, 1, 0.3, 1)';

            // Announce toast to screen readers
            var toastText = toast.querySelector('.cedrus-toast-body');
            if (toastText && window.CedrusA11y) {
                window.CedrusA11y.announce(toastText.textContent, 'polite');
            }

            setTimeout(function () {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(function () {
                    toast.remove();
                }, 300);
            }, 5000);
        });
    }

    // ============================================
    // PAGE-LOAD ANIMATION
    // ============================================

    function initPageAnimations() {
        var animTargets = document.querySelectorAll(
            '.page-content .cedrus-card, .page-content .stat-card-wrapper, .page-content .page-header'
        );
        animTargets.forEach(function (el, i) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(12px)';
            setTimeout(function () {
                el.style.transition =
                    'opacity 0.5s cubic-bezier(0.16, 1, 0.3, 1), transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 50 * i);
        });
    }

    // ============================================
    // INITIALIZATION
    // ============================================

    function init() {
        initDropdowns();
        initThemeToggle();
        initSidebar();
        initToasts();
        initPageAnimations();
        console.log('Cedrus App Module loaded');
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
