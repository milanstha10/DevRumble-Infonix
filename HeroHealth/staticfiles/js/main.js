(() => {
    'use strict';

    const HeroHealth = {
        config: {
            alertDuration: 5000,
            alertFadeDuration: 400
        },

        state: {
            initialized: false,
            eventsInitialized: false,
            observerInitialized: false
        },

        init() {
            this.initAlerts();
            this.initGlobalEvents();
            this.initAlertObserver();

            this.state.initialized = true;
        },

        initAlerts() {
            const alerts = document.querySelectorAll('.alert-message');

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
                delete alert.dataset.dismissTimer;
            }

            const reducedMotion = window.matchMedia(
                '(prefers-reduced-motion: reduce)'
            ).matches;

            if (reducedMotion) {
                this.removeAlert(alert);
                return;
            }

            alert.style.transition = [
                `opacity ${this.config.alertFadeDuration}ms ease`,
                `transform ${this.config.alertFadeDuration}ms ease`
            ].join(', ');

            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            alert.style.pointerEvents = 'none';

            window.setTimeout(() => {
                this.removeAlert(alert);
            }, this.config.alertFadeDuration);
        },

        removeAlert(alert) {
            if (!alert) {
                return;
            }

            if (alert.dataset.removed === 'true') {
                return;
            }

            alert.dataset.removed = 'true';

            const timer = alert.dataset.dismissTimer;

            if (timer) {
                window.clearTimeout(Number(timer));
            }

            alert.remove();
        },

        dismissLatestAlert() {
            const alerts = Array.from(
                document.querySelectorAll(
                    '.alert-message:not([data-dismissed="true"])'
                )
            );

            if (!alerts.length) {
                return;
            }

            this.dismissAlert(alerts[alerts.length - 1]);
        },

        initGlobalEvents() {
            if (this.state.eventsInitialized) {
                return;
            }

            this.state.eventsInitialized = true;

            document.addEventListener('keydown', (event) => {
                this.handleKeyboardEvents(event);
            });

            window.addEventListener('pageshow', () => {
                this.handlePageShow();
            });
        },

        initAlertObserver() {
            if (
                this.state.observerInitialized ||
                typeof MutationObserver === 'undefined'
            ) {
                return;
            }

            const container = document.querySelector(
                '.messages-container'
            );

            if (!container) {
                return;
            }

            this.state.observerInitialized = true;

            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.addedNodes.forEach((node) => {
                        if (!(node instanceof HTMLElement)) {
                            return;
                        }

                        if (node.matches('.alert-message')) {
                            this.setupAlert(node);
                        }

                        node.querySelectorAll?.(
                            '.alert-message'
                        ).forEach((alert) => {
                            this.setupAlert(alert);
                        });
                    });
                });
            });

            observer.observe(container, {
                childList: true,
                subtree: true
            });
        },

        handleKeyboardEvents(event) {
            if (event.key !== 'Escape') {
                return;
            }

            this.dismissLatestAlert();
        },

        handlePageShow() {
            this.initAlerts();
        }
    };

    const initialize = () => {
        HeroHealth.init();
    };

    if (document.readyState === 'loading') {
        document.addEventListener(
            'DOMContentLoaded',
            initialize,
            { once: true }
        );
    } else {
        initialize();
    }

    window.HeroHealth = HeroHealth;
})();