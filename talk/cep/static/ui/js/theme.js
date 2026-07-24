(function () {
  'use strict';

  function sync() {
    const dark = document.documentElement.classList.contains('dark');
    ['theme-toggle-dark-icon', 'console-theme-toggle-dark-icon'].forEach(id => document.getElementById(id)?.classList.toggle('hidden', !dark));
    ['theme-toggle-light-icon', 'console-theme-toggle-light-icon'].forEach(id => document.getElementById(id)?.classList.toggle('hidden', dark));
  }

  function init() {
    const dark = localStorage.getItem('color-theme') === 'dark' ||
      (!localStorage.getItem('color-theme') && window.matchMedia('(prefers-color-scheme: dark)').matches);
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
