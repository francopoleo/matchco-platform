(function () {
  'use strict';

  function sync() {
    const dark = document.documentElement.classList.contains('dark');
    ['theme-toggle-dark-icon', 'console-theme-toggle-dark-icon'].forEach(id => document.getElementById(id)?.classList.toggle('hidden', !dark));
    ['theme-toggle-light-icon', 'console-theme-toggle-light-icon'].forEach(id => document.getElementById(id)?.classList.toggle('hidden', dark));
    document.querySelectorAll('.mc-wordmark--light').forEach(el => el.style.setProperty('display', dark ? 'none' : 'block', 'important'));
    document.querySelectorAll('.mc-wordmark--dark').forEach(el => el.style.setProperty('display', dark ? 'block' : 'none', 'important'));
  }

  function init() {
    // A experiência pública institucional permanece no campo claro da marca.
    // A preferência do Console/app não deve escurecer login, convite, QR ou
    // a landing comercial.
    const publicLight = document.body.classList.contains('mc-public-light');
    const dark = !publicLight && (localStorage.getItem('color-theme') === 'dark' ||
      (!localStorage.getItem('color-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches));
    document.documentElement.classList.toggle('dark', dark);
    sync();
    ['theme-toggle', 'console-theme-toggle'].forEach(id => {
      const button = document.getElementById(id);
      if (!button || button.dataset.themeBound === 'true') return;
      button.dataset.themeBound = 'true';
      button.addEventListener('click', () => {
        document.documentElement.classList.toggle('dark');
        localStorage.setItem('color-theme', document.documentElement.classList.contains('dark') ? 'dark' : 'light');
        sync();
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
