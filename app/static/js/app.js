const imageInput = document.getElementById('imageInput');
const preview = document.getElementById('preview');
const loading = document.getElementById('loading');
const colorsGrid = document.getElementById('colorsGrid');
const stats = document.getElementById('stats');
const copiedNotification = document.getElementById('copiedNotification');
const sortControls = document.getElementById('sortControls');
const sortSelect = document.getElementById('sortSelect');
const limitInput = document.getElementById('limitInput');
const autoLimitCheckbox = document.getElementById('autoLimitCheckbox');

let currentImageData = null;
let allColors = null;

// Listen for paste events globally
document.addEventListener('paste', async (e) => {
    e.preventDefault();

    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of items) {
        if (item.type.indexOf('image') !== -1) {
            const blob = item.getAsFile();

            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
                preview.style.display = 'block';
            };
            reader.readAsDataURL(blob);

            // Process image with slight delay to allow UI update
            setTimeout(() => {
                const limitValue = getLimitValue();
                const autoLimit = autoLimitCheckbox.checked;
                processImageFile(blob, sortSelect.value, limitValue, autoLimit);
            }, 50);
            return;
        }
    }
});

imageInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
        preview.src = e.target.result;
        preview.style.display = 'block';
    };
    reader.readAsDataURL(file);

    // Upload and process with slight delay to allow UI update
    setTimeout(() => {
        const limitValue = getLimitValue();
        const autoLimit = autoLimitCheckbox.checked;
        processImageFile(file, sortSelect.value, limitValue, autoLimit);
    }, 50);
});

sortSelect.addEventListener('change', async () => {
    if (currentImageData) {
        const limitValue = getLimitValue();
        const autoLimit = autoLimitCheckbox.checked;
        await processImageFile(currentImageData, sortSelect.value, limitValue, autoLimit);
    }
});

limitInput.addEventListener('change', async () => {
    if (currentImageData) {
        const limitValue = getLimitValue();
        const autoLimit = autoLimitCheckbox.checked;
        await processImageFile(currentImageData, sortSelect.value, limitValue, autoLimit);
    }
});

autoLimitCheckbox.addEventListener('change', async () => {
    // Disable/enable limit input based on checkbox
    limitInput.disabled = autoLimitCheckbox.checked;

    if (currentImageData) {
        const limitValue = getLimitValue();
        const autoLimit = autoLimitCheckbox.checked;
        await processImageFile(currentImageData, sortSelect.value, limitValue, autoLimit);
    }
});

// Helper function to get limit value from input
function getLimitValue() {
    const value = limitInput.value.trim();
    if (value === '' || value === '0') {
        return null; // Default to 64
    }
    const numValue = parseInt(value);
    // Clamp between 1 and 64
    return Math.min(Math.max(numValue, 1), 64);
}

async function processImageFile(file, sortBy = 'frequency', limit = null, autoLimit = false) {
    // File size warning for very large images
    const maxRecommendedSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxRecommendedSize) {
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const proceed = confirm(`This image is ${sizeMB}MB which may take longer to process. Continue?`);
        if (!proceed) {
            return;
        }
    }

    loading.style.display = 'block';
    colorsGrid.innerHTML = '';
    stats.innerHTML = '';

    const formData = new FormData();
    formData.append('file', file);

    try {
        let url = `/extract-colors?sort_by=${sortBy}`;
        if (autoLimit) {
            url += `&auto_limit=true`;
        } else if (limit !== null) {
            url += `&limit=${limit}`;
        }

        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.colors) {
            // Store file for re-sorting
            currentImageData = file;

            displayColors(data.colors);

            let limitText = '';
            if (autoLimit) {
                limitText = ` (auto-detected: ${data.total_colors})`;
            } else if (limit) {
                limitText = ` (limited to ${limit})`;
            } else {
                limitText = ` (max 64)`;
            }
            stats.innerHTML = `Found <strong>${data.total_colors}</strong> unique colors${limitText}`;
            sortControls.style.display = 'flex';
        }
    } catch (error) {
        alert('Error processing image: ' + error.message);
    } finally {
        loading.style.display = 'none';
    }
}

async function processImageData(imageData, sortBy = 'frequency', limit = null, autoLimit = false) {
    loading.style.display = 'block';

    if (imageData instanceof Blob) {
        // If it's a blob/file, use the file upload method
        await processImageFile(imageData, sortBy, limit, autoLimit);
        return;
    }

    loading.style.display = 'none';
}

function displayColors(colors) {
    colorsGrid.innerHTML = '';

    // Use document fragment for better performance
    const fragment = document.createDocumentFragment();

    colors.forEach(color => {
        const card = document.createElement('div');
        card.className = 'color-card';
        card.onclick = () => copyToClipboard(color.hex);

        card.innerHTML = `
            <div class="color-preview" style="background-color: ${color.hex}"></div>
            <div class="color-info">
                <div class="color-hex">${color.hex}</div>
                <div class="color-rgb">${color.rgb}</div>
                <div class="color-percentage">${color.percentage}%</div>
                <div class="color-count">Pixels: ${color.count.toLocaleString()}</div>
            </div>
        `;

        fragment.appendChild(card);
    });

    // Add all cards at once for better performance
    colorsGrid.appendChild(fragment);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        copiedNotification.style.display = 'block';
        setTimeout(() => {
            copiedNotification.style.display = 'none';
        }, 2000);
    });
}
