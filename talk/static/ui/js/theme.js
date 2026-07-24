(function () {
    'use strict';

    function preferredTheme() {
        return localStorage.getItem('color-theme') === 'dark' ||
            (!localStorage.getItem('color-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
    }

    function syncTheme() {
        var isDark = document.documentElement.classList.contains('dark');
        var pairs = [
            ['theme-toggle-dark-icon', 'theme-toggle-light-icon'],
            ['console-theme-toggle-dark-icon', 'console-theme-toggle-light-icon']
        ];
        pairs.forEach(function (ids) {
            var darkIcon = document.getElementById(ids[0]);
            var lightIcon = document.getElementById(ids[1]);
            if (darkIcon) darkIcon.classList.toggle('hidden', !isDark);
            if (lightIcon) lightIcon.classList.toggle('hidden', isDark);
        });
    }

    function setTheme(isDark) {
        document.documentElement.classList.toggle('dark', isDark);
        localStorage.setItem('color-theme', isDark ? 'dark' : 'light');
        syncTheme();
        document.dispatchEvent(new Event('dark-mode'));
    }

    function initTheme() {
        document.documentElement.classList.toggle('dark', preferredTheme());
        syncTheme();

        ['theme-toggle', 'console-theme-toggle'].forEach(function (id) {
            var button = document.getElementById(id);
            if (!button || button.dataset.themeBound === 'true') return;
            button.dataset.themeBound = 'true';
            button.addEventListener('click', function () {
                setTheme(!document.documentElement.classList.contains('dark'));
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme, { once: true });
    } else {
        initTheme();
    }
})();
