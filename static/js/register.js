window.onload = () => {
    const form = document.getElementById('form');

    const passwordInput = document.getElementById('password');
    const repPasswordInput = document.getElementById('confirm_password');
    const submitButton = document.querySelector('button[type="submit"]');

    function validateForm() {
        const password = passwordInput.value;
        const repPassword = repPasswordInput.value;
        
        const passwordsMatch = password === repPassword && ( password.length >= 6 && repPassword.length >= 6 );

        submitButton.disabled = !passwordsMatch;

        // if (passwordsMatch) {
        //     submitButton.classList.remove('opacity-50', 'cursor-not-allowed');
        //     submitButton.classList.add('hover:text-default-secondary');
        // } else {
        //     submitButton.classList.add('opacity-50', 'cursor-not-allowed');
        //     submitButton.classList.remove('hover:text-default-secondary');
        // }
    }

    passwordInput.addEventListener('input', validateForm);
    repPasswordInput.addEventListener('input', validateForm);

    validateForm();

    form.addEventListener('submit', function(e) {
        const password = passwordInput.value;
        const repPassword = repPasswordInput.value;

        if (password !== repPassword) {
            alert('As senhas não coincidem.');
            e.preventDefault();
            return;
        }
    });
};