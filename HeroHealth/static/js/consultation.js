// HeroHealth Consultation Page Interactions

document.addEventListener('DOMContentLoaded', () => {
    const consultationForm = document.getElementById('consultationForm');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const fileInput = document.getElementById('id_image'); // Django default form id
    const uploadZone = document.getElementById('uploadZone');
    
    // Toggle loading screen on form submit
    if (consultationForm && loadingOverlay) {
        consultationForm.addEventListener('submit', () => {
            loadingOverlay.style.display = 'flex';
        });
    }

    // Trigger file click when clicking the zone
    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag and drop events
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = 'var(--primary)';
                uploadZone.style.background = 'rgba(0, 242, 254, 0.05)';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                uploadZone.style.borderColor = 'rgba(255, 255, 255, 0.15)';
                uploadZone.style.background = 'rgba(255, 255, 255, 0.02)';
            }, false);
        });

        uploadZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFilePreview(files[0]);
            }
        });

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                updateFilePreview(fileInput.files[0]);
            }
        });
    }

    function updateFilePreview(file) {
        const textElement = uploadZone.querySelector('.upload-text');
        const iconElement = uploadZone.querySelector('.upload-icon');
        
        if (file && textElement) {
            textElement.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            if (iconElement) {
                iconElement.className = 'fas fa-file-image upload-icon';
                iconElement.style.color = 'var(--accent)';
            }
        }
    }
});
