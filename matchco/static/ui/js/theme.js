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
            ['console-theme-toggle-dark-icon', 'console-theme-toggle-light-icon'],
            ['public-theme-toggle-dark-icon', 'public-theme-toggle-light-icon']
        ];
        pairs.forEach(function (ids) {
            var darkIcon = document.getElementById(ids[0]);
            var lightIcon = document.getElementById(ids[1]);
            if (darkIcon) darkIcon.classList.toggle('hidden', !isDark);
            if (lightIcon) lightIcon.classList.toggle('hidden', isDark);
        });
        document.querySelectorAll('#theme-toggle, #console-theme-toggle, #public-theme-toggle').forEach(function (button) {
            button.setAttribute('aria-pressed', isDark ? 'true' : 'false');
            button.setAttribute('data-theme', isDark ? 'dark' : 'light');
        });
        document.querySelectorAll('[data-matchco-theme-logo]').forEach(function (logo) {
            var source = isDark ? logo.getAttribute('data-dark-src') : logo.getAttribute('data-light-src');
            if (source && logo.getAttribute('src') !== source) logo.setAttribute('src', source);
        });
    }

    function setTheme(isDark) {
        document.documentElement.classList.toggle('dark', isDark);
        localStorage.setItem('color-theme', isDark ? 'dark' : 'light');
        syncTheme();
        document.dispatchEvent(new Event('dark-mode'));
    }

    function initTheme() {
        var publicLight = document.body && document.body.classList.contains('mc-public-light');
        document.documentElement.classList.toggle('dark', publicLight ? false : preferredTheme());
        syncTheme();

        /* Delegação: continua funcionando quando o HTMX troca o navbar. */
        if (document.documentElement.dataset.themeClickBound !== 'true') {
            document.documentElement.dataset.themeClickBound = 'true';
            document.addEventListener('click', function (event) {
            var button = event.target.closest('#theme-toggle, #console-theme-toggle, #public-theme-toggle');
                if (!button) return;
                event.preventDefault();
                setTheme(!document.documentElement.classList.contains('dark'));
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme, { once: true });
    } else {
        initTheme();
    }
})();
