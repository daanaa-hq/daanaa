window.plausible = window.plausible || function () {
  (window.plausible.q = window.plausible.q || []).push(arguments);
};
window.plausible.init = window.plausible.init || function (options) {
  window.plausible.o = options || {};
};
window.plausible.init({ endpoint: "https://stats.daanaa.org/api/event" });
