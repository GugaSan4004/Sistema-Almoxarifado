{
    window.openPreviewImage = function(event) {
        window.open(event.target.src, '_blank').focus();
    }

    window.handleDragOver = function(event) {
        event.preventDefault();
        event.target.classList.add('border-blue-500', 'bg-blue-50');
    }

    window.handleDragLeave = function(event) {
        event.target.classList.remove('border-blue-500', 'bg-blue-50');
    }

    window.handleDrop = function(event) {
        event.preventDefault();
        event.target.classList.remove('border-blue-500', 'bg-blue-50');
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const fileInput = document.getElementById('file_input');
            if (fileInput) {
                fileInput.files = files;
                showPreview(files[0]);
            }
        }
    }

    window.showPreview = function(file) {
        if (!file) return;
        const url = URL.createObjectURL(file);
        const container = document.getElementById('preview-container');
        if (container) {
            container.innerHTML = `
                <img src="${url}" class="max-h-80 mx-auto rounded-sm shadow-lg border border-slate-200" alt="Preview">
                <p class="text-sm text-slate-500 mt-2">${file.name}</p>
            `;
        }
        const submitBtn = document.getElementById("submit-btn");
        if (submitBtn) submitBtn.disabled = false;
    }
}
