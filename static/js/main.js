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
    document.querySelectorAll('.language-selector[open], .header-search[open]').forEach(menu => menu.open = false);
  }
});
document.addEventListener('click', event => {
  document.querySelectorAll('.language-selector[open], .header-search[open]').forEach(menu => {
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

// Homepage banner slider: fades every few seconds, stops while it is hovered or focused, and can be swiped. It does not
// advance by itself with reduced motion turned on.
document.querySelectorAll('[data-hero-slider]').forEach(slider => {
  const slides = [...slider.querySelectorAll('.hero-slide')];
  const dots = [...slider.querySelectorAll('.hero-slider-dot')];
  let current = 0;
  let timer = null;
  const show = index => {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.classList.toggle('is-active', i === current);
      if (i === current) slide.removeAttribute('aria-hidden');
      else slide.setAttribute('aria-hidden', 'true');
    });
    dots.forEach((dot, i) => {
      dot.classList.toggle('is-active', i === current);
      if (i === current) dot.setAttribute('aria-current', 'true');
      else dot.removeAttribute('aria-current');
    });
  };
  const stop = () => {
    clearInterval(timer);
    timer = null;
  };
  const start = () => {
    stop();
    if (!reduceMotion && !document.hidden && !slider.matches(':hover') && !slider.matches(':focus-within')) {
      timer = setInterval(() => show(current + 1), 5000);
    }
  };
  dots.forEach((dot, i) => dot.addEventListener('click', () => show(i)));
  slider.addEventListener('mouseenter', stop);
  slider.addEventListener('mouseleave', start);
  slider.addEventListener('focusin', stop);
  slider.addEventListener('focusout', () => setTimeout(start));
  document.addEventListener('visibilitychange', start);
  let touchStart = null;
  slider.addEventListener('touchstart', event => {
    touchStart = event.touches[0].clientX;
  }, {passive: true});
  slider.addEventListener('touchend', event => {
    if (touchStart === null) return;
    const distance = event.changedTouches[0].clientX - touchStart;
    touchStart = null;
    if (Math.abs(distance) > 40) show(current + (distance < 0 ? 1 : -1));
    start();
  }, {passive: true});
  start();
});

// Video highlights and team photos: a carousel that loops by itself (not with reduced motion) and pauses while hovered, focused,
// touched, off screen or while an item is open. The cards are repeated once so the end runs straight into the start.
document.querySelectorAll('[data-video-carousel], [data-photo-carousel]').forEach(section => {
  const track = section.querySelector('.video-track');
  const cards = [...track.children];
  const dialog = section.querySelector('.video-dialog');
  const player = dialog.querySelector('video, img');
  const isVideo = player.tagName === 'VIDEO';
  const sources = cards.map(card => card.querySelector('.video-open').getAttribute('href'));
  cards.forEach((card, index) => card.dataset.index = index);
  cards.forEach(card => {
    const copy = card.cloneNode(true);
    copy.setAttribute('aria-hidden', 'true');
    copy.querySelectorAll('a').forEach(link => link.tabIndex = -1);
    track.append(copy);
  });

  const stepSize = () => cards[1].offsetLeft - cards[0].offsetLeft;
  const loopSize = () => stepSize() * cards.length;
  // Scroll position, within one step, at which a card sits exactly in the middle.
  const centerOffset = () => {
    const step = stepSize();
    return ((cards[0].offsetLeft + cards[0].offsetWidth / 2 - track.clientWidth / 2) % step + step) % step;
  };
  // Silently moves back by exactly one set of cards, which looks identical.
  const wrap = () => {
    if (track.scrollLeft >= loopSize()) track.scrollLeft -= loopSize();
  };
  const move = direction => {
    wrap();
    if (direction < 0 && track.scrollLeft < stepSize()) track.scrollLeft += loopSize();
    const step = stepSize();
    const offset = centerOffset();
    const target = (Math.round((track.scrollLeft - offset) / step) + direction) * step + offset;
    track.scrollTo({left: target, behavior: reduceMotion ? 'auto' : 'smooth'});
  };
  // Starts with the first video in the middle and earlier ones on its left.
  const showFirst = () => {
    track.scrollLeft = loopSize() + cards[0].offsetLeft + cards[0].offsetWidth / 2 - track.clientWidth / 2;
  };

  // 3D turn: each card is angled, scaled and dimmed by how far it is from the middle.
  const allCards = [...track.children];
  let painting = false;
  const paint = () => {
    painting = false;
    const middle = track.scrollLeft + track.clientWidth / 2;
    const step = stepSize();
    allCards.forEach(card => {
      const distance = (card.offsetLeft + card.offsetWidth / 2 - middle) / step;
      const away = Math.min(Math.abs(distance), 2);
      card.style.transform = `perspective(1000px) rotateY(${(Math.max(-2, Math.min(2, distance)) * -24).toFixed(2)}deg) scale(${(1.1 - Math.min(away, 1) * .22 - Math.max(away - 1, 0) * .06).toFixed(3)})`;
      card.style.opacity = (1 - away * .22).toFixed(3);
      card.style.zIndex = String(10 - Math.round(away));
      card.classList.toggle('is-center', away < .5);
    });
  };
  const schedulePaint = () => {
    if (!painting && !reduceMotion) {
      painting = true;
      requestAnimationFrame(paint);
    }
  };
  track.addEventListener('scroll', schedulePaint, {passive: true});
  window.addEventListener('resize', () => {
    showFirst();
    schedulePaint();
  });
  showFirst();
  schedulePaint();

  let timer = null;
  let onScreen = false;
  let touching = false;
  const stop = () => {
    clearInterval(timer);
    timer = null;
  };
  const start = () => {
    stop();
    if (!reduceMotion && onScreen && !touching && !document.hidden && !dialog.open && !track.matches(':hover') && !track.matches(':focus-within')) {
      timer = setInterval(() => move(1), 1800);
    }
  };
  track.addEventListener('mouseenter', stop);
  track.addEventListener('mouseleave', start);
  track.addEventListener('focusin', stop);
  track.addEventListener('focusout', () => setTimeout(start));
  track.addEventListener('touchstart', () => {
    touching = true;
    stop();
  }, {passive: true});
  track.addEventListener('touchend', () => {
    touching = false;
    start();
  }, {passive: true});
  let settle = null;
  track.addEventListener('scroll', () => {
    clearTimeout(settle);
    settle = setTimeout(wrap, 200);
  }, {passive: true});
  document.addEventListener('visibilitychange', start);
  new IntersectionObserver(entries => {
    onScreen = entries[0].isIntersecting;
    start();
  }, {threshold: .25}).observe(track);

  let current = 0;
  const playCurrent = () => {
    player.src = sources[current];
    if (isVideo) player.play().catch(() => {});
    else player.alt = cards[current].querySelector('img').alt;
  };
  track.addEventListener('click', event => {
    const link = event.target.closest('.video-open');
    if (!link) return;
    event.preventDefault();
    current = Number(link.closest('.video-card').dataset.index);
    stop();
    dialog.showModal();
    playCurrent();
  });
  section.querySelectorAll('[data-video-prev], [data-video-next]').forEach(button => {
    const direction = button.hasAttribute('data-video-next') ? 1 : -1;
    button.addEventListener('click', () => {
      if (dialog.open) {
        current = (current + direction + sources.length) % sources.length;
        playCurrent();
      } else {
        move(direction);
        start();
      }
    });
  });
  section.querySelector('[data-video-close]').addEventListener('click', () => dialog.close());
  // A click on the dark area outside closes it too.
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => {
    if (isVideo) player.pause();
    player.removeAttribute('src');
    if (isVideo) player.load();
    start();
  });
});

// Pop-ups: a link with data-open-dialog opens that dialog; the close button or the dark area outside closes it.
document.addEventListener('click', event => {
  const opener = event.target.closest('[data-open-dialog]');
  if (opener) {
    event.preventDefault();
    document.getElementById(opener.dataset.openDialog).showModal();
    return;
  }
  const closer = event.target.closest('[data-close-dialog]');
  if (closer) closer.closest('dialog').close();
  else if (event.target.matches('.detail-dialog')) event.target.close();
});

// Header search: ready to type as soon as it opens.
document.querySelector('.header-search')?.addEventListener('toggle', event => {
  if (event.target.open) event.target.querySelector('input').focus();
});
