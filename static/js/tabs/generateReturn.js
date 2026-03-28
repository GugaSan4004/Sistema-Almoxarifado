{
    window.removeReturnMail = function (event, code) {  
        if (event.target.tagName != 'OPTION' && event.target.tagName != 'SELECT') {
            if (confirm(`Tem certeza que deseja remover ${code} da lista?`)) {
                delete return_data[code];
                sendReturnMail();
            }
        }
    }

    window.updateReturnReason = function (code, reason) {
        return_data[code] = reason;
        const valuesInp = document.getElementById('values');
        if (valuesInp) {
            valuesInp.value = JSON.stringify(return_data);
        }
    }

    // Initialize return_data in the main values input if it exists
    const valuesInp = document.getElementById('values');
    if (valuesInp && typeof return_data !== 'undefined') {
        valuesInp.value = JSON.stringify(return_data);
    }
}
