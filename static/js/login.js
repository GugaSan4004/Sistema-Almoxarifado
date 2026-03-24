
const getCookie = (name) => {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

window.onload = function () {
    if (getCookie('change_pass') === 'true') {
        const main = document.querySelector("main")
        main.className = "grid bg-white grid-flow-col h-140 w-270 rounded-md z-1"
        main.removeChild(document.getElementById("message-body"))

        document.getElementById("your-name").innerHTML = "Nova senha"

        document.getElementById("your-pass").innerHTML = "Repetir Nova senha"

        const form = document.querySelector("form")
        form.action = "/mails-api/set-userpass"
        form.innerHTML = `
                <h1 class="font-bold text-4xl text-center">Primeiro Login</h1>
                <input class="duration-300 transition-colors rounded-sm border border-gray-300 focus:ring-2 focus:ring-light-default-main 0 bg-gray-200 h-11 w-11/15 px-4" required minlength="8" placeholder="Senha" name="password" id="pwd"
                type="password">
                <input class="duration-300 transition-colors rounded-sm border border-gray-300 focus:ring-2 focus:ring-light-default-main 0 bg-gray-200 h-11 w-11/15 px-4" required minlength="8" placeholder="Repita a Senha" name="password_repeat"
                id="pwd_repeat" type="password">
                <button id="submit" class="duration-300 transition-all rounded-sm active:scale-95 cursor-pointer font-bold hover:text-light-default-secondary h-11 w-11/15 bg-light-default-main text-white disabled:opacity-50 disabled:cursor-not-allowed" type="submit" disabled>Entrar</button>
            `
        document.cookie = "change_pass=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";

        const password = document.getElementById("pwd")
        const confirmPassword = document.getElementById("pwd_repeat")
        const submitBtn = document.getElementById("submit")

        function validarSenhas() {
            const equal = password.value === confirmPassword.value;
            const min = password.value.length >= 6;

            if (equal && min) {
                submitBtn.disabled = false;
            } else {
                submitBtn.disabled = true;
            }
        }

        password.addEventListener('input', validarSenhas);
        confirmPassword.addEventListener('input', validarSenhas);
    }
}