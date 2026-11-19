// App shell initialization and interactive components
(function() {
  'use strict';

  // Sidebar toggle
  const sidebarToggle = document.getElementById('console-sidebar-toggle') || document.getElementById('app-sidebar-toggle');
  const appBackdrop = document.getElementById('app-backdrop');
  const sidebar = document.getElementById('console-sidebar') || document.getElementById('app-sidebar');
  const sidebarMode = sidebar?.dataset.sidebarMode || 'console';

  function setSidebarOpen(open) {
    if (!sidebar) return;
    if (sidebarMode === 'app') {
      // The App uses `hidden lg:block`; Console uses translate classes.
      // Keep one state model so refreshes and viewport changes cannot mix them.
      if (window.matchMedia('(min-width: 1024px)').matches) {
        sidebar.classList.remove('hidden');
      } else {
        sidebar.classList.toggle('hidden', !open);
      }
    } else {
      sidebar.classList.toggle('translate-x-0', open);
      sidebar.classList.toggle('-translate-x-full', !open);
    }
    appBackdrop?.classList.toggle('hidden', !open || window.matchMedia('(min-width: 1024px)').matches);
  }

  function toggleSidebar() {
    if (!sidebar) return;
    const isOpen = sidebarMode === 'app'
      ? !sidebar.classList.contains('hidden')
      : sidebar.classList.contains('translate-x-0');
    setSidebarOpen(!isOpen);
  }

  if (sidebarToggle && sidebarToggle.dataset.sidebarBound !== 'true') {
    sidebarToggle.addEventListener('click', toggleSidebar);
    sidebarToggle.dataset.sidebarBound = 'true';
  }

  if (appBackdrop && appBackdrop.dataset.sidebarBound !== 'true') {
    appBackdrop.addEventListener('click', toggleSidebar);
    appBackdrop.dataset.sidebarBound = 'true';
  }

  // Close sidebar on medium+ screens
  const mediaQuery = window.matchMedia('(min-width: 1024px)');
  function handleMediaChange(e) {
    if (e.matches && sidebar) {
      setSidebarOpen(true);
    } else if (!e.matches && sidebar) {
      setSidebarOpen(false);
    }
  }
  mediaQuery.addEventListener('change', handleMediaChange);
  // Normalize the initial state after a full refresh. The App and Console use
  // different responsive classes, so relying only on CSS can leave a stale
  // hidden/translated state when the shell is restored from cache.
  if (sidebar) setSidebarOpen(mediaQuery.matches);

  // User menu toggle
  const userMenuButton = document.getElementById('console-user-menu-button') || document.getElementById('app-user-menu-button');
  const userMenu = document.getElementById('console-user-menu') || document.getElementById('app-user-menu');

  if (userMenuButton && userMenu) {
    userMenuButton.addEventListener('click', () => {
      userMenu.classList.toggle('hidden');
      userMenuButton.setAttribute('aria-expanded',
        userMenu.classList.contains('hidden') ? 'false' : 'true');
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!userMenuButton.contains(e.target) && !userMenu.contains(e.target)) {
        userMenu.classList.add('hidden');
        userMenuButton.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Form validation (basic HTML5)
  const forms = document.querySelectorAll('form[data-validate="true"]');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!form.checkValidity()) {
        e.preventDefault();
        e.stopPropagation();
      }
      form.classList.add('was-validated');
    });
  });

  // Dropdown menus
  const dropdownButtons = document.querySelectorAll('[data-dropdown-toggle]');
  dropdownButtons.forEach(button => {
    const dropdownId = button.getAttribute('data-dropdown-toggle');
    const dropdown = document.getElementById(dropdownId);

    if (dropdown) {
      button.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('hidden');
      });

      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!button.contains(e.target) && !dropdown.contains(e.target)) {
          dropdown.classList.add('hidden');
        }
      });

      // Close on Escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          dropdown.classList.add('hidden');
        }
      });
    }
  });

  // Smooth scroll links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#' && document.querySelector(href)) {
        e.preventDefault();
        document.querySelector(href).scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Initialize Flowbite components if available
  if (typeof Flowbite !== 'undefined' && Flowbite.initModals) {
    Flowbite.initModals();
    Flowbite.initTooltips();
    Flowbite.initDropdowns();
  }

  // Add feedback for form submissions
  document.querySelectorAll('form').forEach(form => {
    const submitButtons = form.querySelectorAll('button[type="submit"]');
    form.addEventListener('submit', () => {
      submitButtons.forEach(btn => {
        btn.disabled = true;
        const text = btn.textContent;
        const locale = (document.documentElement.lang || 'pt-br').toLowerCase().split('-')[0];
        const loadingText = btn.getAttribute('data-loading-text') || {
          en: 'Processing...',
          es: 'Procesando...',
          pt: 'Processando...'
        }[locale] || 'Processando...';
        btn.innerHTML = '<span class="inline-block animate-spin mr-2">⋯</span>' + loadingText;
      });
    });
  });
})();
