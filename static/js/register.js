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