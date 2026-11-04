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

// Motion for public pages: scroll reveals, 3D card tilt, button ripples and a scroll progress bar. Only elements below
// the first screen are hidden first, so nothing visible flashes, and nothing is hidden without JavaScript or with
// reduced motion turned on.
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const publicPage = !document.body.classList.contains('page-admin');
if (!reduceMotion && publicPage && 'IntersectionObserver' in window) {
  // Each kind of element enters its own way: headings slide in, cards jump up, steps flip up, photos spin in.
  const effects = [
    ['main .section-heading, main .numbered-feature', 'left'],
    ['main .product-card, main .retailer-card, main .three-grid article, main .inquiry, main .commitment > div:first-child', 'up'],
    ['main .step-card', 'flip'],
    ['main .gallery-item', 'zoom'],
    ['main .ritual-image, main .story-photo, main .sustainability img', 'side'],
  ];
  const observer = new IntersectionObserver(entries => entries.forEach(entry => {
    if (entry.isIntersecting) {
      const element = entry.target;
      element.classList.add('is-visible');
      observer.unobserve(element);
      // Once shown, drop the reveal timing so hover effects respond immediately again.
      setTimeout(() => {
        element.classList.remove('reveal', 'is-visible');
        element.removeAttribute('data-reveal');
        element.style.transitionDelay = '';
      }, 1600);
    }
  }), {rootMargin: '0px 0px -10% 0px', threshold: 0.1});
  let side = 0;
  effects.forEach(([selector, effect]) => document.querySelectorAll(selector).forEach(element => {
    if (element.getBoundingClientRect().top < window.innerHeight) return;
    // Cards in the same row arrive one after another.
    const siblings = [...element.parentElement.children].filter(child => child.matches(element.tagName));
    element.style.transitionDelay = `${(siblings.indexOf(element) % 4) * 130}ms`;
    element.dataset.reveal = effect === 'side' ? (side++ % 2 ? 'left' : 'right') : effect;
    element.classList.add('reveal');
    observer.observe(element);
  }));
}
if (!reduceMotion && publicPage) {
  // Cards lean towards the mouse pointer.
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('.product-card').forEach(card => {
      card.addEventListener('mousemove', event => {
        if (card.classList.contains('reveal')) return;
        const box = card.getBoundingClientRect();
        const x = (event.clientX - box.left) / box.width - 0.5;
        const y = (event.clientY - box.top) / box.height - 0.5;
        card.classList.add('is-tilting');
        card.style.transform = `perspective(900px) rotateX(${-y * 12}deg) rotateY(${x * 14}deg) translateY(-12px) scale(1.03)`;
      });
      card.addEventListener('mouseleave', () => {
        card.classList.remove('is-tilting');
        card.style.transform = '';
      });
    });
  }
  // A ripple spreads from where a button is pressed.
  document.addEventListener('pointerdown', event => {
    const button = event.target.closest('.button');
    if (!button) return;
    const box = button.getBoundingClientRect();
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.left = `${event.clientX - box.left}px`;
    ripple.style.top = `${event.clientY - box.top}px`;
    button.append(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  });
  // Reading progress along the top edge.
  const progress = document.createElement('div');
  progress.className = 'scroll-progress';
  progress.setAttribute('aria-hidden', 'true');
  document.body.append(progress);
  let ticking = false;
  const update = () => {
    const scrollable = document.documentElement.scrollHeight - window.innerHeight;
    progress.style.transform = `scaleX(${scrollable > 0 ? window.scrollY / scrollable : 0})`;
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) requestAnimationFrame(update);
    ticking = true;
  }, {passive: true});
  update();
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

// Product photos: shrink large pictures in the browser before upload, since the host refuses bodies over 4.5 MB.
document.querySelectorAll('input[type=file][data-max-bytes]').forEach(input => {
  const maxBytes = Number(input.dataset.maxBytes);
  const maxSide = Number(input.dataset.maxSide);
  const submit = input.form?.querySelector('[type=submit]');
  const encode = (canvas, type) => new Promise(resolve => canvas.toBlob(resolve, type, 0.9));
  input.addEventListener('change', async () => {
    input.setCustomValidity('');
    const file = input.files[0];
    if (!file) return;
    if (submit) submit.disabled = true;
    try {
      const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
      const scale = Math.min(1, maxSide / Math.max(bitmap.width, bitmap.height));
      if (scale < 1 || file.size > maxBytes / 2) {
        const canvas = document.createElement('canvas');
        canvas.width = Math.round(bitmap.width * scale);
        canvas.height = Math.round(bitmap.height * scale);
        canvas.getContext('2d').drawImage(bitmap, 0, 0, canvas.width, canvas.height);
        let blob = await encode(canvas, 'image/webp');
        // Browsers without WebP encoding fall back to PNG, which can be larger than the original.
        if (!blob || blob.type !== 'image/webp') blob = await encode(canvas, 'image/jpeg');
        if (blob && blob.size < file.size) {
          const name = file.name.replace(/\.[^.]+$/, '') + (blob.type === 'image/webp' ? '.webp' : '.jpg');
          const files = new DataTransfer();
          files.items.add(new File([blob], name, { type: blob.type }));
          input.files = files.files;
        }
      }
    } catch {
      // Not a picture the browser can read; the server will refuse it with a clear message.
    } finally {
      if (submit) submit.disabled = false;
    }
    if (input.files[0].size > maxBytes) {
      input.setCustomValidity(input.dataset.tooLarge);
      input.reportValidity();
    }
  });
});
