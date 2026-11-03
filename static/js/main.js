'use strict';

const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('#navigation');
toggle?.addEventListener('click', () => {
  const open = toggle.getAttribute('aria-expanded') !== 'true';
  toggle.setAttribute('aria-expanded', String(open));
  nav.classList.toggle('is-open', open);
});
nav?.addEventListener('click', event => {
  if (event.target.closest('a')) {
    toggle.setAttribute('aria-expanded', 'false');
    nav.classList.remove('is-open');
  }
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    if (nav?.classList.contains('is-open')) {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.focus();
    }
    document.querySelectorAll('.language-selector[open]').forEach(menu => menu.open = false);
  }
});
document.addEventListener('click', event => {
  document.querySelectorAll('.language-selector[open]').forEach(menu => {
    if (!menu.contains(event.target)) menu.open = false;
  });
});

// Keep navigation predictable when tapping outside it or returning to desktop.
document.addEventListener('click', event => {
  if (!event.target.closest('.site-header') && nav?.classList.contains('is-open')) {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
});
window.matchMedia('(min-width: 801px)').addEventListener('change', event => {
  if (event.matches) {
    nav?.classList.remove('is-open');
    toggle?.setAttribute('aria-expanded', 'false');
  }
});

document.querySelector('.password-toggle')?.addEventListener('click', event => {
  const button = event.currentTarget;
  const password = document.getElementById(button.getAttribute('aria-controls'));
  const show = password.type === 'password';
  password.type = show ? 'text' : 'password';
  button.setAttribute('aria-pressed', String(show));
  button.setAttribute('aria-label', show ? button.dataset.hideLabel : button.dataset.showLabel);
  button.querySelector('i').className = show ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
});

const dialog = document.querySelector('.lightbox');
let lightboxTrigger;
document.querySelectorAll('[data-lightbox]').forEach(button => {
  button.addEventListener('click', () => {
    lightboxTrigger = button;
    const image = dialog.querySelector('img');
    image.src = button.dataset.lightbox;
    image.alt = button.querySelector('img').alt;
    dialog.querySelector('p').textContent = image.alt;
    dialog.showModal();
  });
});
dialog?.querySelector('.lightbox-close').addEventListener('click', () => dialog.close());
dialog?.addEventListener('click', event => {
  if (event.target === dialog) dialog.close();
});
dialog?.addEventListener('close', () => lightboxTrigger?.focus());
// Continue straight to the payment page; the visible button is the fallback without JavaScript.
document.querySelector('form[data-autosubmit]')?.submit();

document.querySelectorAll('[data-confirm]').forEach(form => form.addEventListener('submit', event => {
  if (!window.confirm(form.dataset.confirm)) event.preventDefault();
}));

// Scroll reveal for public pages. Only elements below the first screen are hidden first, so nothing visible
// flashes, and nothing is hidden when JavaScript or IntersectionObserver is unavailable.
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduceMotion && 'IntersectionObserver' in window && !document.body.classList.contains('page-admin')) {
  const targets = document.querySelectorAll('main .section-heading, main .product-card, main .step-card, main .gallery-item, main .numbered-feature, main .ritual-image, main .story-photo, main .sustainability img, main .three-grid article, main .retailer-card, main .inquiry, main .commitment > div:first-child');
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      const element = entry.target;
      element.classList.add('is-visible');
      observer.unobserve(element);
      // Once shown, drop the reveal timing so hover effects respond immediately again.
      setTimeout(() => {
        element.classList.remove('reveal', 'is-visible');
        element.style.transitionDelay = '';
      }, 1000);
    }
  }), {rootMargin: '0px 0px -8% 0px', threshold: 0.12});
  targets.forEach(element => {
    if (element.getBoundingClientRect().top < window.innerHeight) return;
    // Cards in the same row appear one after another.
    const siblings = [...element.parentElement.children].filter(child => child.matches(element.tagName));
    element.style.transitionDelay = `${(siblings.indexOf(element) % 3) * 90}ms`;
    element.classList.add('reveal');
    observer.observe(element);
  });
}

// Delivery address: each choice fills the next list (province -> district/khan -> commune/sangkat).
const places = document.querySelector('[data-places]');
if (places) {
  const [province, district, commune] = ['province', 'district', 'commune'].map(id => document.getElementById(id));
  const khmer = document.documentElement.lang === 'km';
  let request;
  const load = () => request ??= fetch(places.dataset.places).then(response => response.json());
  const fill = (select, rows) => {
    select.length = 1;
    rows.map(row => [row[0], khmer ? row[1] : row[2]])
      .sort((a, b) => a[1].localeCompare(b[1], khmer ? 'km' : 'en'))
      .forEach(([value, label]) => select.add(new Option(label, value)));
    select.disabled = !rows.length;
  };
  province.addEventListener('change', async () => {
    const data = await load();
    fill(district, data.districts[province.value] || []);
    fill(commune, []);
  });
  district.addEventListener('change', async () => fill(commune, (await load()).communes[district.value] || []));
}
