(() => {
    'use strict';

    const HeroHealth = {
        config: {
            alertDuration: 5000,
            alertFadeDuration: 400
        },

        init() {
            this.initAlerts();
            this.initGlobalEvents();
        },

        initAlerts() {
            const alerts = document.querySelectorAll('.alert-message');

            if (!alerts.length) {
                return;
            }

            alerts.forEach((alert) => {
                this.setupAlert(alert);
            });
        },

        setupAlert(alert) {
            if (!alert || alert.dataset.initialized === 'true') {
                return;
            }

            alert.dataset.initialized = 'true';

            const closeButton = alert.querySelector('.alert-close');

            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    this.dismissAlert(alert);
                });
            }

            const timer = window.setTimeout(() => {
                this.dismissAlert(alert);
            }, this.config.alertDuration);

            alert.dataset.dismissTimer = String(timer);
        },

        dismissAlert(alert) {
            if (!alert || alert.dataset.dismissed === 'true') {
                return;
            }

            alert.dataset.dismissed = 'true';

            const timer = alert.dataset.dismissTimer;

            if (timer) {
                window.clearTimeout(Number(timer));
            }

            const reducedMotion = window.matchMedia(
                '(prefers-reduced-motion: reduce)'
            ).matches;

            if (reducedMotion) {
                alert.remove();
                return;
            }

            alert.style.transition = `opacity ${this.config.alertFadeDuration}ms ease, transform ${this.config.alertFadeDuration}ms ease`;
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            alert.style.pointerEvents = 'none';

            window.setTimeout(() => {
                alert.remove();
            }, this.config.alertFadeDuration);
        },

        initGlobalEvents() {
            document.addEventListener('keydown', (event) => {
                this.handleKeyboardEvents(event);
            });

            window.addEventListener('pageshow', () => {
                this.handlePageShow();
            });
        },

        handleKeyboardEvents(event) {
            if (event.key === 'Escape') {
                const visibleAlert = document.querySelector(
                    '.alert-message:not([data-dismissed="true"])'
                );

                if (visibleAlert) {
                    this.dismissAlert(visibleAlert);
                }
            }
        },

        handlePageShow() {
            const alerts = document.querySelectorAll('.alert-message');

            alerts.forEach((alert) => {
                if (alert.dataset.initialized !== 'true') {
                    this.setupAlert(alert);
                }
            });
        }
    };

    document.addEventListener('DOMContentLoaded', () => {
        HeroHealth.init();
    });

    window.HeroHealth = HeroHealth;
})();
