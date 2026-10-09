(() => {
    const sidebar = document.getElementById('user-course-sidebar');
    if (!sidebar) return;

    document.querySelectorAll('[data-course-sidebar-toggle]').forEach((toggle) => {
        toggle.addEventListener('click', (event) => {
            event.preventDefault();
            const open = document.body.classList.toggle('course-sidebar-open');
            document.querySelectorAll('[data-course-sidebar-toggle]').forEach((button) => {
                button.setAttribute('aria-expanded', String(open));
            });
        });
    });
})();
