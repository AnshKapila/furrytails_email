/* Kite report design kit — dialog wiring. Ships beside report-theme.css (see
 * that file's header for the source-of-truth contract).
 *
 * Wires every native <dialog> on the page:
 *   - a button with data-open="<dialog id>" opens that dialog (showModal);
 *   - a button with data-close inside a dialog closes it;
 *   - clicking the backdrop closes the dialog.
 * Pages load this with <script src="assets/report-kit.js" defer></script> and
 * add no dialog script of their own. */

(function () {
  function init() {
    document.querySelectorAll('[data-open]').forEach(function (button) {
      button.addEventListener('click', function () {
        var dialog = document.getElementById(button.dataset.open);
        if (dialog && typeof dialog.showModal === 'function') {
          dialog.showModal();
        }
      });
    });
    document.querySelectorAll('[data-close]').forEach(function (button) {
      button.addEventListener('click', function () {
        var dialog = button.closest('dialog');
        if (dialog) {
          dialog.close();
        }
      });
    });
    document.querySelectorAll('dialog').forEach(function (dialog) {
      dialog.addEventListener('click', function (event) {
        if (event.target === dialog) {
          dialog.close();
        }
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
