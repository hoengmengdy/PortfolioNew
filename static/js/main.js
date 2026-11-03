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
