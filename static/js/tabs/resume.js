{
    window.handleFilterKeydown = function(event) {
        if(event.key == 'Enter') { 
            setFilter(event.target.value);
        }
    }

    window.toggleStats = function() {
        if (typeof resume_helpersOpen === 'undefined') window.resume_helpersOpen = false;
        resume_helpersOpen = !resume_helpersOpen;
        const statsExtra = document.getElementById('stats-extra');
        if (!statsExtra) return;

        if (resume_helpersOpen) {
            statsExtra.classList.remove('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
            statsExtra.classList.add('opacity-100', 'translate-x-0', 'max-w-4xl');
        } else {
            statsExtra.classList.add('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
            statsExtra.classList.remove('opacity-100', 'translate-x-0', 'max-w-4xl');
        }
    }

    window.handlePhotoClick = function(event) {
        if (event.target.dataset.img) {
            window.open(event.target.dataset.img, '_blank').focus();
        }
    }

    window.handlePhotoMouseOver = function(event) {
        window.resume_hoverTimeout = setTimeout(() => {
            const imgSrc = event.target.dataset.img;
            if (!imgSrc) return;

            if (document.getElementById('pp').src !== imgSrc) {
                changePreviewPicture(imgSrc);
            }

            updatePreviewPosition(event);
        }, 150);
    }

    window.handlePhotoMouseMove = function(event) {
        if (!document.getElementById('pp').className.split(' ').some(function (w) { return w === 'opacity-0' })) {
            updatePreviewPosition(event);
        }
    }

    window.handlePhotoMouseLeave = function() {
        clearTimeout(window.resume_hoverTimeout);
        changePreviewPicture();
    }

    window.handleSubmitOnChange = function(element) {
        element.form.requestSubmit();
    }
}

