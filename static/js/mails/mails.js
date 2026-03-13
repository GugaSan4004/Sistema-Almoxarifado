// const ALLOWED_TABS FORMS_ID
let main = ""
let sidebar = ""
let sidebarIsOpen = true;
let actualTabId = "resume"

let resume_lastFilter = ""
let resume_lastOrderBy = "id"
let resume_orderDirection = "DESC"
let resume_hoverTimeout

let return_mails = {}

const loading = (on) => {
    const overlay = document.getElementById('overlay')
    const message = document.getElementById('loading')

    if (on) {
        document.querySelector('body').setAttribute('inert', '');
        overlay.classList.remove('hidden');
        message.classList.remove('hidden');
    } else {
        document.querySelector('body').removeAttribute('inert');
        overlay.classList.add('hidden');
        message.classList.add('hidden');
    }
}

async function loadBody(optional = "") {
    loading(true)
    const response = await fetch(`/api/render-body/${actualTabId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify([resume_lastFilter, resume_lastOrderBy, resume_orderDirection, return_mails, optional])
    });

    if (response.ok) {
        loading(false)
        const result = await response.text()
        if (response.redirected) {
            window.location.reload();
            return
        }

        main.innerHTML = result

        const selector = FORMS_ID.map(id => `#${id}`).join(',');
        const forms = document.querySelectorAll(selector);

        forms.forEach(form => {
            form.addEventListener("submit", async (e) => {
                loading(true)
                e.preventDefault();

                const formData = new FormData(form);

                if (form.id == "generate-return") formData.append('mails', JSON.stringify(return_mails));

                try {
                    console.log(formData)
                    
                    const response = await fetch(form.action, {
                        method: form.method,
                        body: formData
                    });

                    if (response.ok) {
                        const result = await response.json();

                        loading(false)
                        if (response.status == 200) {
                            alert(result.Message)
                        }

                        if (response.status == 202) {
                            let iframe = document.querySelector("iframe")
                            if (!iframe) {
                                iframe = document.createElement("iframe");
                            }

                            iframe.className = "hidden";
                            document.body.appendChild(iframe);

                            iframe.src = result.Message;

                            iframe.onload = () => {
                                iframe.contentWindow.focus();
                                iframe.contentWindow.print();

                                return_mails = {}

                                loadBody()
                            };
                        }

                        form.querySelectorAll('input:not([type="hidden"]), textarea').forEach(input => input.value = '');

                        if (form.id == "get-mail") {
                            if (return_mails[result.Message[2]]) {
                                alert("Erro: " + "Correspondencia já adicionada!");
                            } else {
                                return_mails[result.Message[2]] = {
                                    'reason': 'Desconhecido',
                                    'name': result.Message[1]
                                };
                                loadBody();
                            }
                            return
                        }

                        if (form.id == "extract-image" || form.id == "get-mail-exit") {
                            loadBody(result.Message)
                        }
                    } else {
                        const result = await response.json();
                        loading(false)
                        alert("Erro: " + result.Message);
                    }
                } catch (error) {
                    console.error(error);
                    alert("Não foi possível conectar ao servidor.");
                }
            });
        });
    } else {
        loading(false)
        const result = await response.json()
        alert(result.Message);
    }

};

const toggleHelpers = () => {
    sidebarIsOpen = !sidebarIsOpen;

    const statsExtra = document.getElementById('stats-extra');

    if (sidebarIsOpen) {
        statsExtra.classList.remove('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
        statsExtra.classList.add('opacity-100', 'translate-x-0', 'max-w-4xl');
    } else {
        statsExtra.classList.add('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
        statsExtra.classList.remove('opacity-100', 'translate-x-0', 'max-w-4xl');
    }
};

const setFilter = (e) => {
    resume_lastFilter = e
    loadBody()
};

const setOrderBy = (e) => {
    if (e == resume_lastOrderBy) {
        resume_orderDirection = resume_orderDirection == "ASC" ? "DESC" : "ASC"
    } else {
        resume_lastOrderBy = e
        resume_orderDirection = "ASC"
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
        span.href = "#"
        span.innerHTML = tab.name

        if (tab.id == "resume") {
            span.className = "bg-gray-400/50 border-l-6 border-default-secondary"
        }

        span.onclick = (span_clicked) => {
            if (!span_clicked.target.className) {
                actualTabId = span_clicked.target.id
                Array.from(sidebar_opt.children).forEach(a => a.className = "")
                span_clicked.target.className = "bg-gray-400/50 border-l-6 border-default-secondary"
                loadBody()
                sidebar.classList.toggle('-translate-x-full');
            }
        }

        sidebar_opt.appendChild(span)
    })

    loadBody()
};