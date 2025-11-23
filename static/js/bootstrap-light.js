/**
 * Minimal Bootstrap JavaScript for AIS E-bike Rental
 * Contains only essential components: Alert, Button, Collapse, Dropdown
 * Avoids CDN blocking issues with Tracking Prevention
 */

(function() {
  'use strict'

  // Polyfill for Element.prototype.matches
  if (!Element.prototype.matches) {
    Element.prototype.matches = Element.prototype.msMatchesSelector ||
                                Element.prototype.webkitMatchesSelector;
  }

  // Polyfill for Element.prototype.closest
  if (!Element.prototype.closest) {
    Element.prototype.closest = function(s) {
      var el = this;
      do {
        if (el.matches(s)) return el;
        el = el.parentElement || el.parentNode;
      } while (el !== null && el.nodeType === 1);
      return null;
    };
  }

  // Utility function to get parent element
  function getParent(el, selector) {
    return el.closest(selector);
  }

  // Event handling utilities
  function addEvent(el, event, handler) {
    if (el.addEventListener) {
      el.addEventListener(event, handler, false);
    } else if (el.attachEvent) {
      el.attachEvent('on' + event, handler);
    }
  }

  // Alert component
  function initAlerts() {
    var alerts = document.querySelectorAll('.alert-dismissible .btn-close');

    for (var i = 0; i < alerts.length; i++) {
      addEvent(alerts[i], 'click', function() {
        var alert = getParent(this, '.alert');
        if (alert) {
          alert.style.display = 'none';
        }
      });
    }
  }

  // Collapse component
  function initCollapse() {
    var toggles = document.querySelectorAll('[data-bs-toggle="collapse"]');

    for (var i = 0; i < toggles.length; i++) {
      addEvent(toggles[i], 'click', function(e) {
        e.preventDefault();

        var target = this.getAttribute('data-bs-target');
        if (!target) {
          var href = this.getAttribute('href');
          if (href && href.charAt(0) === '#') {
            target = href;
          }
        }

        if (target) {
          var collapseElement = document.querySelector(target);
          if (collapseElement) {
            var isExpanded = collapseElement.classList.contains('show');
            var parent = getParent(this, '.navbar');

            if (parent && parent.classList.contains('navbar')) {
              // Handle navbar collapse specially
              var navbarCollapse = parent.querySelector('.navbar-collapse');
              if (navbarCollapse) {
                if (isExpanded) {
                  navbarCollapse.classList.remove('show');
                } else {
                  navbarCollapse.classList.add('show');
                }
              }
            } else {
              // Standard collapse
              if (isExpanded) {
                collapseElement.classList.remove('show');
              } else {
                collapseElement.classList.add('show');
              }
            }
          }
        }
      });
    }
  }

  // Initialize components when DOM is ready
  function init() {
    initAlerts();
    initCollapse();
  }

  // DOM ready check
  function domReady(fn) {
    if (document.readyState === 'loading') {
      addEvent(document, 'DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  // Initialize when DOM is ready
  domReady(init);

  // Modal-like functionality for simple implementations
  // (Basic modal support for any future needs)

})();
