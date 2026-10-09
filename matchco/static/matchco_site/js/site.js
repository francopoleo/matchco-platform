/* MatchCo site v0.1 — comportamento mínimo: menu, revelação, formulário */
(function () {
  'use strict';
  // Campo de marca: exatamente uma variante do wordmark por tema.
  var dark = document.documentElement.classList.contains('dark');
  document.querySelectorAll('.mc-wordmark--light').forEach(function (el) {
    el.style.setProperty('display', dark ? 'none' : 'block', 'important');
  });
  document.querySelectorAll('.mc-wordmark--dark').forEach(function (el) {
    el.style.setProperty('display', dark ? 'block' : 'none', 'important');
  });
  // Menu (celular)
  var btn = document.querySelector('.mc-menu-btn');
  var menu = document.getElementById('mc-menu');
  if (btn && menu) {
    var iconOpen = btn.querySelector('.mc-ico-open'), iconClose = btn.querySelector('.mc-ico-close');
    function setOpen(open) {
      btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      btn.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
      menu.hidden = !open;
      if (iconOpen) iconOpen.style.display = open ? 'none' : '';
      if (iconClose) iconClose.style.display = open ? '' : 'none';
    }
    setOpen(false);
    btn.addEventListener('click', function () { setOpen(menu.hidden); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !menu.hidden) { setOpen(false); btn.focus(); }
    });
  }

  // Revelação ao rolar — só abaixo da dobra; nunca com movimento reduzido
  try {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduce && 'IntersectionObserver' in window) {
      var vh = window.innerHeight;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
        });
      }, { rootMargin: '0px 0px -12% 0px' });
      document.querySelectorAll('.mc-unit:not(.mc-hero-unit)').forEach(function (u) {
        if (u.getBoundingClientRect().top > vh * 0.92) { u.classList.add('mc-reveal'); io.observe(u); }
      });
    }
  } catch (err) {}

  // Formulário (Conversar) — validação acessível; envio não conectado nesta versão
  var form = document.querySelector('.mc-form');
  if (form) {
    var ORDER = ['shopping', 'cidade', 'nome', 'funcao', 'email'];
    var MSG = {
      shopping: 'Informe o Shopping ou a administradora.',
      cidade: 'Informe a cidade.',
      nome: 'Informe seu nome.',
      funcao: 'Informe sua função.',
      email: 'Informe seu e-mail profissional.'
    };
    var EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
    var summary = form.querySelector('.mc-form__summary');
    var list = summary.querySelector('ul');
    var status = form.querySelector('.mc-annot');
    function check(k) {
      var v = (form.elements[k].value || '').trim();
      if (!v) return MSG[k];
      if (k === 'email' && !EMAIL.test(v)) return 'Confira o formato do e-mail.';
      return '';
    }
    function show(k, msg) {
      var input = form.elements[k], p = document.getElementById('erro-' + k);
      input.setAttribute('aria-invalid', msg ? 'true' : 'false');
      if (msg) { input.setAttribute('aria-describedby', 'erro-' + k); p.textContent = msg; p.hidden = false; }
      else { input.removeAttribute('aria-describedby'); p.textContent = ''; p.hidden = true; }
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      list.innerHTML = '';
      var errors = 0;
      ORDER.forEach(function (k) {
        var msg = check(k);
        show(k, msg);
        if (msg) {
          errors++;
          var li = document.createElement('li'), a = document.createElement('a');
          a.href = '#campo-' + k; a.textContent = msg;
          li.appendChild(a); list.appendChild(li);
        }
      });
      summary.hidden = errors === 0;
      status.hidden = errors > 0;
      if (errors) summary.focus(); else status.focus();
    });
    form.addEventListener('input', function (e) {
      var k = e.target && e.target.name;
      if (ORDER.indexOf(k) < 0 || e.target.getAttribute('aria-invalid') !== 'true') return;
      if (!check(k)) show(k, '');
    });
  }
})();

/* V2 — trilho horizontal e máscara de imagem */
(function () {
  'use strict';
  document.querySelectorAll('[data-rail]').forEach(function (wrap) {
    var rail = wrap.querySelector('.v2-rail');
    var prev = wrap.querySelector('[data-rail-prev]'), next = wrap.querySelector('[data-rail-next]');
    function step() { var it = rail.querySelector('.v2-rail__item'); return it ? it.getBoundingClientRect().width + 16 : rail.clientWidth * 0.8; }
    function sync() {
      prev.disabled = rail.scrollLeft < 4;
      next.disabled = rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 4;
    }
    var smooth = !(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
    prev.addEventListener('click', function () { rail.scrollBy({ left: -step(), behavior: smooth ? 'smooth' : 'auto' }); });
    next.addEventListener('click', function () { rail.scrollBy({ left: step(), behavior: smooth ? 'smooth' : 'auto' }); });
    rail.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); next.click(); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev.click(); }
    });
    rail.addEventListener('scroll', sync, { passive: true });
    window.addEventListener('resize', sync);
    sync();
  });
  try {
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduce || !('IntersectionObserver' in window)) return;
    var vh = window.innerHeight;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.remove('is-pending'); e.target.classList.add('is-in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    document.querySelectorAll('.v2-mask').forEach(function (m) {
      if (m.closest('.v2-rail')) return;
      if (m.getBoundingClientRect().top > vh) { m.classList.add('is-pending'); io.observe(m); }
    });
  } catch (err) {}
})();
