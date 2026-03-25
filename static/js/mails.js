// const ALLOWED_TABS FORMS_ID
let actualTabId = "resume";

let URLParams = {};

let resume_lastFilter = "";
let resume_helpersOpen = true;
let resume_lastOrderBy = "id";
let resume_orderDirection = "DESC";

let return_data = {};

const setInnerHTMLAndExecuteScripts = (element, html) => {
    element.innerHTML = html;
    Array.from(element.querySelectorAll("script")).forEach(oldScript => {
        const newScript = document.createElement("script");
        Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
        newScript.appendChild(document.createTextNode(oldScript.innerHTML));
        oldScript.parentNode.replaceChild(newScript, oldScript);
    });
}

const loading = (on) => {
    const overlay = document.getElementById('overlay')
    const message = document.getElementById('loading')

    if (on) {
        document.querySelector('body').setAttribute('inert', '');
        overlay.hidden = false;
        message.hidden = false;
    } else {
        document.querySelector('body').removeAttribute('inert');
        overlay.hidden = true;
        message.hidden = true;
    }
}


let toastTimer = null;

const triggerToast = (message, success) => {
    const sound = document.getElementById('sound-effect')
    const toast = document.getElementById('toast');
    const progressBar = document.getElementById('toast-progress');
    const status_color = success ? "green" : "red";
    const duration = 6000;
    
    sound.currentTime = 0;
    sound.src = `/static/sounds/${success ? "success" : "error"}.mp3`;
    
    document.querySelector("#toast > h2").innerHTML = success ? "Sucesso" : "Error";
    document.querySelector("#toast > h1").innerHTML = message;

    sound.play();

    toast.classList.remove('border-green-600', 'border-red-600', 'text-green-600', 'text-red-600');
    progressBar.classList.remove('bg-green-600', 'bg-red-600');

    toast.classList.add(`border-${status_color}-600`, `text-${status_color}-600`);
    progressBar.classList.add(`bg-${status_color}-600`);
    

    progressBar.style.transition = 'none';
    progressBar.style.width = '100%';
    

    void progressBar.offsetWidth;

    toast.classList.remove('translate-x-full');
    progressBar.style.transition = `width ${duration}ms linear`;
    progressBar.style.width = '0%';

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {        
        toast.classList.add('translate-x-full');
        
        setTimeout(() => {
            toast.classList.remove(`border-${status_color}-600`);
        }, 300);
    }, duration);
}


const bindForms = () => {
    const forms = document.querySelectorAll("form");

    forms.forEach(form => {
        if (form.dataset.bound) return;
        form.dataset.bound = "true";
        form.addEventListener("submit", async (e) => {
            try {
                loading(true)

                e.preventDefault();

                let url = form.action;
                let method = form.method.toUpperCase();
                let response
            

                const formData = new FormData(form);

                if (method === "POST") {
                    response = await fetch(url, {
                        method,
                        body: formData
                    });
                } else if (method === "GET") {
                    const params = new URLSearchParams(formData);
                    url += `?${params.toString()}`;
                    response = await fetch(url, {
                        method
                    });
                }
                
                const result = await response.json();
                
                const message = result.Message;
                
                loading(false)
         
                if (!response.ok) {
                    triggerToast(message, false);
                    return;
                }

                const head = result.head;

                form.querySelectorAll('input:not([type="hidden"]), textarea').forEach(input => input.value = '');

                switch (head) {
                    case "reload":
                        loadBody();
                        break;
                    case "print":
                        return_data = {};
                        
                        let iframe = document.querySelector("iframe");
                        
                        if (!iframe) {
                            iframe = document.createElement("iframe");
                        };
                        
                        iframe.className = "hidden";
                        document.body.appendChild(iframe);
                        
                        iframe.src = `/pictures/temp/${message}.pdf`;
                        
                        iframe.onload = () => {
                            iframe.contentWindow.focus();
                            iframe.contentWindow.print();

                            sendReturnMail();
                        };

                        break;
                    case "load":
                        setInnerHTMLAndExecuteScripts(main, message);
                        bindForms(main);
                        break;
                    case "realert":
                        triggerToast(message, true);
                        loadBody();
                        break;
                    case "append_return":
                        return_data[message] = "Desconhecido";
                        sendReturnMail();
                        break;
                    default:
                        triggerToast(message, true);
                        break;
                }
            } catch (e) {
                loading(false)
                triggerToast("Um erro fatal aconteceu! Por favor atualize a pagina!", false);
                console.error(e)
            }
        });
    });
}

async function loadBody() {
    loading(true)

    const url = new URLSearchParams();

    Object.entries(URLParams).forEach(([key, value]) => {
        if (typeof value === 'object' && value !== null) {
            url.append(key, JSON.stringify(value));
        } else {
            url.append(key, value);
        };
    });

    const response = await fetch(`/mails-api/${actualTabId}?${url.toString()}`, {
        method: "GET",
    });

    loading(false)

    if (response.ok) {
        const result = await response.text()

        if (response.redirected) {
            window.location.reload();
            return
        }

        setInnerHTMLAndExecuteScripts(main, result);
        bindForms(main)
    } else {
        const result = await response.json()
        triggerToast(result.Message, false);
    }
}

const setFilter = (e) => {
    URLParams.filter = e
    loadBody()
};

const setOrderBy = (e) => {
    if (e == URLParams.order) {
        URLParams.direction = URLParams.direction == "ASC" ? "DESC" : "ASC"
    } else {
        URLParams.order = e
        URLParams.direction = "ASC"
    }

    loadBody()
};

const changePreviewPicture = (e) => {
    const pp = document.getElementById('pp')
    if (e) {
        pp.src = e
    } else {
        pp.classList.add('opacity-0');
        return
    }

    pp.classList.remove('opacity-0');
};

const updatePreviewPosition = (e) => {
    const element = document.getElementById('pp')
    const margin = 15;
    const { offsetWidth: w, offsetHeight: h } = element;

    let x = e.pageX - 360;
    let y = e.pageY - 180;

    const maxX = window.scrollX + window.innerWidth - w - margin;
    const maxY = window.scrollY + window.innerHeight - h - margin;

    x = Math.max(margin, Math.min(x, maxX));
    y = Math.max(margin, Math.min(y, maxY));

    element.style.transform = `translate(${x}px, ${y}px)`;
};

const sendReturnMail = () => {
    URLParams.return_data = return_data
    loadBody()
}

const showPreview = (file) => {
    if (!file) return;
    const url = URL.createObjectURL(file);
    document.getElementById('preview-container').innerHTML = `
        <img src="${url}" class="max-h-80 mx-auto rounded-sm shadow-lg border border-slate-200" alt="Preview">
        <p class="text-sm text-slate-500 mt-2">${file.name}</p>
    `;
    document.getElementById("submit-btn").disabled = false
};

window.onload = () => {
    sidebar = document.getElementById("sidebar")
    main = document.querySelector("main")

    const sidebar_opt = document.getElementById("aside-options")

    ALLOWED_TABS.forEach(tab => {
        const span = document.createElement("a")
        span.id = tab.id
        span.innerHTML = tab.name

        if (tab.id == "resume") {
            span.className = "bg-gray-400/50 border-l-6 border-light-default-secondary"
        }

        span.onclick = (span_clicked) => {
            if (!span_clicked.target.className) {
                actualTabId = span_clicked.target.id
                Array.from(sidebar_opt.children).forEach(a => a.className = "")
                span_clicked.target.className = "bg-gray-400/50 border-l-6 border-light-default-secondary"
                loadBody()
                sidebar.classList.toggle('-translate-x-full');
            }
        }

        sidebar_opt.appendChild(span)
    })

    if (ALLOWED_TABS) {
        loadBody()
    }
};