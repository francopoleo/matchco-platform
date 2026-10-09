(() => {
    document.querySelectorAll('[data-module-toggle]').forEach((button) => {
        button.addEventListener('click', () => {
            const content = button.nextElementSibling;
            const expanded = button.getAttribute('aria-expanded') === 'true';
            button.setAttribute('aria-expanded', String(!expanded));
            content.hidden = expanded;
        });
    });
})();
