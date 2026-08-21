// HeroHealth Main Javascript

document.addEventListener('DOMContentLoaded', () => {
    // Auto-dismiss alert messages after 5 seconds
    const alerts = document.querySelectorAll('.alert-message');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.6s ease';
            setTimeout(() => {
                alert.remove();
            }, 600);
        }, 5000);
    });

    // Close button for alerts
    const closeButtons = document.querySelectorAll('.alert-close');
    closeButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alert = e.target.closest('.alert-message');
            if (alert) alert.remove();
        });
    });

    // Mobile nav helper
    console.log("HeroHealth System Initialized.");
});
