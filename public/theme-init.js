// Kept external so the Content-Security-Policy can stay free of inline scripts.
(function () {
  try {
    var root = document.documentElement;
    if (localStorage.getItem('hm-theme') === 'light') root.dataset.theme = 'light';
    if (localStorage.getItem('hm-language') === 'km') root.lang = 'km';
  } catch (e) {
    // Storage can be blocked; the defaults still render correctly.
  }
})();
