{
    window.handleUserChange = function (select) {
        select.form.requestSubmit();
    }

    window.prepareUserUpdate = function () {
        const submitInp = document.getElementById('submit');
        if (submitInp) {
            submitInp.value = 'True';
        }
    }
}
