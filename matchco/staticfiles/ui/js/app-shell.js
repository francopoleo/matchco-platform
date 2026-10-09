(() => {
    const sidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('app-backdrop');
    const toggle = document.getElementById('app-sidebar-toggle');
    const main = document.getElementById('app-main');
    const userButton = document.getElementById('app-user-menu-button');
    const userMenu = document.getElementById('app-user-menu');

    if (!sidebar || !main) return;

    const setMainMargin = (visible) => {
        main.style.marginLeft = window.innerWidth >= 1024 && visible ? '16rem' : '0';
    };

    const closeMobile = () => {
        sidebar.classList.add('-translate-x-full');
        backdrop?.classList.add('hidden');
        toggle?.setAttribute('aria-expanded', 'false');
    };

    const initSidebar = () => {
        if (window.innerWidth < 1024) {
            sidebar.style.display = '';
            sidebar.style.transform = '';
            sidebar.classList.add('-translate-x-full');
            backdrop?.classList.add('hidden');
            setMainMargin(false);
            return;
        }

        const collapsed = localStorage.getItem('app-sidebar-collapsed') === 'true';
        sidebar.classList.remove('-translate-x-full');
        sidebar.style.display = collapsed ? 'none' : '';
        sidebar.style.transform = '';
        backdrop?.classList.add('hidden');
        setMainMargin(!collapsed);
        toggle?.setAttribute('aria-expanded', String(!collapsed));
    };

    const toggleSidebar = () => {
        if (window.innerWidth < 1024) {
            const open = sidebar.classList.toggle('-translate-x-full');
            backdrop?.classList.toggle('hidden', open);
            toggle?.setAttribute('aria-expanded', String(!open));
            return;
        }

        const collapsed = sidebar.style.display === 'none';
        sidebar.style.display = collapsed ? '' : 'none';
        setMainMargin(collapsed);
        localStorage.setItem('app-sidebar-collapsed', String(!collapsed));
        toggle?.setAttribute('aria-expanded', String(collapsed));
    };

    initSidebar();
    toggle?.addEventListener('click', toggleSidebar);
    backdrop?.addEventListener('click', closeMobile);
    window.addEventListener('resize', initSidebar);

    sidebar.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
        if (window.innerWidth < 1024) closeMobile();
    }));

    userButton?.addEventListener('click', (event) => {
        event.stopPropagation();
        const open = !userMenu?.classList.toggle('hidden');
        userButton.setAttribute('aria-expanded', String(open));
    });

    document.addEventListener('click', (event) => {
        if (userMenu && userButton && !userMenu.contains(event.target) && !userButton.contains(event.target)) {
            userMenu.classList.add('hidden');
            userButton.setAttribute('aria-expanded', 'false');
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMobile();
            userMenu?.classList.add('hidden');
            userButton?.setAttribute('aria-expanded', 'false');
        }
    });
})();
