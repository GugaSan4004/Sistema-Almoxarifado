let main;

let actualTab = "resumo";
let lastFilter = "";
let lastOrderBy = "id";
let orderDirection = "DESC";

let resumo_Body;
let resumo_ImgPreview;
let resumo_FilterInput;
let resumo_TotalsPreview;
let resumo_MailsPreviewContainer;

let register_Inputs;

let entrada_Inputs

const CONFIG = {
    GRID_LAYOUT: "grid-cols-[1cm_1fr_3.2cm_0.5fr_1.4cm_2cm_2.2cm_3.7cm_2.5cm_2.8cm]",
    STATUSCOLORS: {
        "delayed": "red-600",
        "returned": "stone-500",
        "casualty": "pink-600",
        "on_reception": "yellow-600",
        "default": "default-blue"
    },
    TITLES: {
        "ID": "id",
        "Nome": "name",
        "Codigo AR": "code",
        "Nome Fantasia": "fantasy",
        "Tipo": "type",
        "Prioridade": "priority",
        "Entrada": "join_date",
        "Recebedor(a)": "receive_name",
        "Saída": "receive_date",
        "Comprovante": "photo_id"
    },
    COMMONTABLIST: {
        "resumo": "Resumo",
        "reg-saida": "Registrar Saida",
        "gen-devolucao": "Gerar Devolução"
    },
    HIGLEVELTABLIST: {
        "reg-user": "Registrar Usuario",
        "reg-entrada": "Registrar Entrada"
    }
};

function formatDate(dateStr) {
    if (!dateStr) return "";
    dateStr = dateStr.split(" ")
    return dateStr[0].split('-').reverse().join("/");
}

function isDelayed(dateStr, priority) {
    const [d, m, y] = formatDate(dateStr).split("/");
    const diff = (new Date().setHours(0, 0, 0, 0) - new Date(`${y}-${m}-${d}`).setHours(0, 0, 0, 0)) / 86400000;
    const limit = (priority === "Simples") ? 7 : 4;
    return diff > limit;
}

function getPriorityClass(priority) {
    const color = priority === "Judicial" ? "bg-red-500/30" : "bg-green-500/30";
    return ` ${color} rounded-full px-2 font-semibold pb-0.5`;
}

const updatePreviewPosition = (e, element) => {
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

function createMailRow(mail) {
    const row = document.createElement("div");

    const data = {
        id: mail[0],
        priority: mail[5],
        status: mail[11],
        entryDate: mail[6],
        exitDate: mail[13],
        receipt: mail[14]
    };

    if (data.status === "returned") row.classList.add(`text-${CONFIG.STATUSCOLORS["returned"]}`);
    if (data.status === "casualty") row.classList.add(`text-${CONFIG.STATUSCOLORS["casualty"]}`);

    if (["almox", "on_reception"].includes(data.status) && data.entryDate) {
        if (isDelayed(data.entryDate, data.priority)) {
            row.classList.add(`text-${CONFIG.STATUSCOLORS["delayed"]}`);
        } else if (data.status == "on_reception") {
            row.classList.add(`text-${CONFIG.STATUSCOLORS["on_reception"]}`);
        }
    }

    mail.forEach((info, idx) => {
        if ([7, 8, 9, 10, 11].includes(idx)) return;

        const span = document.createElement("span");
        span.className = "truncate overflow-hidden whitespace-nowrap";

        let content = info;
        if (idx === 6 || idx === 13) content = formatDate(info);
        if (idx === 1 || idx === 3 || idx === 11) span.classList.add("text-start")
        if (idx === 2) span.classList.add("font-semibold");
        if (idx === 5) span.className += getPriorityClass(info);
        if (idx === 14) {
            span.className += " rounded-sm duration-300 transition-colors cursor-pointer bg-gray-600/20 hover:bg-default-blue hover:text-white py-1";

            if (data.receipt) {
                span.dataset.img = `/pictures/mails/${data.receipt}.jpg`

                span.addEventListener("click", function (e) {
                    window.open(span.dataset.img, '_blank').focus();
                })

                span.addEventListener("mouseenter", function (e) {
                    hoverTimeout = setTimeout(() => {
                        const imgSrc = span.dataset.img;
                        if (!imgSrc) return;

                        if (resumo_ImgPreview.src !== imgSrc) {
                            resumo_ImgPreview.src = imgSrc;
                        }

                        resumo_ImgPreview.classList.remove("opacity-0");
                        updatePreviewPosition(e, resumo_ImgPreview);
                    }, 150);
                });

                span.addEventListener("mousemove", function (e) {
                    if (!resumo_ImgPreview.className.split(' ').some(function (w) { return w === "opacity-0" })) {
                        updatePreviewPosition(e, resumo_ImgPreview);
                    }
                });

                span.addEventListener("mouseleave", function () {
                    clearTimeout(hoverTimeout);
                    resumo_ImgPreview.classList.add("opacity-0");
                });
            }

        }
        span.innerText = content || "---";
        row.appendChild(span);
    });

    return row;
};

function updateTotalContainer(type, value) {
    const campo = resumo_TotalsPreview.querySelector(`[data-field="${type}"]`);

    if (campo) {
        campo.textContent = value;
    }
};

async function updateTab() {
    if (["resumo"].includes(actualTab)) {
        try {
            const response = await fetch("/mails/get-mails", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify([lastFilter, lastOrderBy, orderDirection])
            })

            const json = await response.json();

            resumo_Body.innerHTML = "";

            const fragment = document.createDocumentFragment();

            json[0].mails.forEach(mail => {
                const mailDiv = createMailRow(mail);
                mailDiv.classList.add(`${CONFIG.GRID_LAYOUT}`, "duration-300", "transition-colors", "grid", "gap-2", "py-2", "pr-2", "border-b", "border-gray-700/50", "hover:bg-default-blue/15", "items-center", "text-xs", "text-center", "*:text-ellipsis", "*:whitespace-nowrap", "*:overflow-hidden", "*:truncate");
                fragment.appendChild(mailDiv);
            });

            Object.entries(json[0].totals).forEach(([type, value]) => {
                updateTotalContainer(type, value)
            })

            resumo_Body.appendChild(fragment);
            resumo_MailsPreviewContainer.appendChild(resumo_Body);

            main.appendChild(resumo_TotalsPreview)
            main.appendChild(resumo_FilterInput)
            main.appendChild(resumo_MailsPreviewContainer);

            const statsExtra = document.getElementById("stats-extra");
            const newStatsExtra = statsExtra.cloneNode(true);
            statsExtra.parentNode.replaceChild(newStatsExtra, statsExtra);

            Array.from(newStatsExtra.children).forEach((block) => {
                block.addEventListener("click", (e) => {
                    lastFilter = e.currentTarget.lastElementChild.dataset.field
                    document.getElementById("filter-input").value = e.currentTarget.lastElementChild.dataset.field
                    updateTab()
                });
            });

            let isOpen = true;

            document.getElementById("btn-Total").addEventListener("click", (e) => {
                isOpen = !isOpen;

                const statsExtra = document.getElementById('stats-extra');

                if (isOpen) {
                    statsExtra.classList.remove('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
                    statsExtra.classList.add('opacity-100', 'translate-x-0', 'max-w-4xl');
                } else {
                    statsExtra.classList.add('opacity-0', 'translate-x-10', 'pointer-events-none', 'max-w-0');
                    statsExtra.classList.remove('opacity-100', 'translate-x-0', 'max-w-4xl');
                }
            })
        } catch (err) {
            console.error("Error:", err);
        }
    } else if (["reg-user"].includes(actualTab)) {
        main.appendChild(register_Inputs)
    } else if (["reg-entrada"].includes(actualTab)) {
        main.appendChild(entrada_Inputs)
    } else {
        main.innerHTML = `<h1>${actualTab.toUpperCase()}</h1>`;
        return;
    }
}

async function checkUser() {
    const response = await fetch('/api/user-info');
    const data = await response.json();

    return data.role
}

class Preload {
    constructor() {
        main = document.querySelector("main");

        this.resumo_Body = class {
            constructor() {
                resumo_Body = document.createElement("div");
                resumo_Body.className = `flex flex-col min-w-300`;

                resumo_ImgPreview = document.getElementById("img-preview");

                resumo_TotalsPreview = document.createElement("div");
                resumo_TotalsPreview.className = "-row-start-2 flex mr-4 mb-4 items-center gap-2 justify-end col-span-2 min-h-18"
                resumo_TotalsPreview.innerHTML = `
                    <div id="stats-extra" class="flex gap-3 transition-all duration-800 ease-in-out overflow-hidden *:rounded-sm *:text-ellipsis *:whitespace-nowrap *:overflow-hidden *:truncate h-full *:flex *:justify-center *:flex-col opacity-100 translate-x-0 max-w-4xl">
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["delayed"]}/8 hover:bg-${CONFIG.STATUSCOLORS["delayed"]}/20 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["delayed"]} text-${CONFIG.STATUSCOLORS["delayed"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Atrasadas</p>
                            <p data-field="delayed" class="font-semibold"></p>
                        </div>
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["returned"]}/8 hover:bg-${CONFIG.STATUSCOLORS["returned"]}/20 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["returned"]} text-${CONFIG.STATUSCOLORS["returned"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Devolvidas</p>
                            <p data-field="returned" class="font-semibold"></p>
                        </div>
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["default"]}/8 hover:bg-${CONFIG.STATUSCOLORS["default"]}/25 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["default"]} text-${CONFIG.STATUSCOLORS["default"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Entregues</p>
                            <p data-field="shipped" class="font-semibold"></p>
                        </div>
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["casualty"]}/7 hover:bg-${CONFIG.STATUSCOLORS["casualty"]}/16 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["casualty"]} text-${CONFIG.STATUSCOLORS["casualty"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Sinistros</p>
                            <p data-field="casualty" class="font-semibold"></p>
                        </div>
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["on_reception"]}/7 hover:bg-${CONFIG.STATUSCOLORS["on_reception"]}/16 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["on_reception"]} text-${CONFIG.STATUSCOLORS["on_reception"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Na recepção</p>
                            <p data-field="on_reception" class=" font-semibold"></p>
                        </div>
                        <div class="cursor-pointer bg-${CONFIG.STATUSCOLORS["default"]}/8 hover:bg-${CONFIG.STATUSCOLORS["default"]}/25 duration-300 transition-colors border-${CONFIG.STATUSCOLORS["default"]} text-${CONFIG.STATUSCOLORS["default"]} border-l-4 p-2 px-4 shadow-sm w-45">
                            <p class="uppercase font-bold">Almoxarifado</p>
                            <p data-field="almox" class="font-semibold"></p>
                        </div>
                    </div>
                    <div id="btn-Total" class="bg-default-blue p-4 rounded-sm shadow-md w-27 cursor-pointer transition duration-300 hover:bg-blue-600 z-10 h-full flex justify-center flex-col">
                        <p class="text-xs font-bold text-blue-100 uppercase tracking-wider">Total</p>
                        <p data-field="total" class="text-2xl font-black text-white">total</p>
                    </div>
                `


                resumo_FilterInput = document.createElement("div");

                resumo_FilterInput.className = "ml-4 mt-4 relative w-full md:w-80 items-center flex"
                resumo_FilterInput.innerHTML = `
                    <span class="absolute inset-y-0 left-0 flex items-center pl-3">
                        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </span>
                    <input
                        class="block w-full rounded-sm px-10 py-2 border border-gray-300 leading-5 bg-white text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-default-blue focus:border-default-blue sm:text-sm transition duration-300 ease-in-out"
                        placeholder="Buscar por nome, código AR, data..." type="search" id="filter-input">
                `
                const span = document.createElement("span")
                span.className = `
                    cursor-pointer absolute inset-y-0 right-2 flex items-center pl-3
                `
                span.innerHTML = `
                    <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                `

                resumo_FilterInput.appendChild(span)



                resumo_FilterInput.addEventListener("keypress", e => {
                    if (e.key === 'Enter') {
                        lastFilter = e.target.value
                        updateTab()
                    }
                })

                span.addEventListener("click", () => {
                    const input = document.getElementById("filter-input")
                    if (input.value) {
                        input.value = ""
                        lastFilter = ""
                        updateTab()
                    }
                })

                resumo_MailsPreviewContainer = document.createElement("div");
                resumo_MailsPreviewContainer.className = "rounded-t-sm -row-start-1 col-span-2 bg-white h-[60vh] overflow-x-auto overflow-y-scroll scrollbar-hide self-end mx-4 mb-4 border-b border-gray-600";

                const titleContainer = document.createElement("div");
                titleContainer.id = "title-container";
                titleContainer.className = `grid ${CONFIG.GRID_LAYOUT} pr-2  *:transition-colors *:duration-300 bg-default-blue cursor-pointer text-white sticky top-0 z-10 gap-2 *:h-10 font-semibold border-b border-gray-600 text-sm min-w-300 *:flex *:items-center *:justify-center *:select-none`;

                Object.entries(CONFIG.TITLES).forEach(([titleText, columnId]) => {
                    const span = document.createElement("span");
                    span.innerText = titleText;
                    span.id = columnId;

                    if (columnId === lastOrderBy) {
                        span.classList.add("text-default-green");
                    }

                    span.addEventListener("click", e => {
                        const clickedSort = e.currentTarget.id;

                        if (clickedSort === lastOrderBy) {
                            orderDirection = (orderDirection === "DESC") ? "ASC" : "DESC";
                        } else {
                            titleContainer.querySelector(`#${lastOrderBy}`)?.classList.remove("text-default-green");

                            lastOrderBy = clickedSort;
                            e.currentTarget.classList.add("text-default-green");
                            orderDirection = "DESC";
                        }
                        updateTab();
                    });

                    titleContainer.appendChild(span);
                });

                resumo_MailsPreviewContainer.appendChild(titleContainer);
            }
        }

        this.loadSidebarTabs = class {
            constructor() {
                const aside = document.getElementById("aside-options");

                const toggleSidebar = () => {
                    document.getElementById("sidebar").classList.toggle('-translate-x-full');
                    document.getElementById('sidebar-overlay').classList.toggle("hidden");
                };

                function genTab(id, label) {
                    const a = document.createElement("a");
                    a.id = id;
                    a.href = "#";
                    a.innerText = label;

                    if (id === actualTab) {
                        a.className = "bg-gray-400/50 border-l-6 border-default-green";
                    }

                    a.addEventListener("click", e => {
                        e.preventDefault();
                        const clickedId = e.currentTarget.id;

                        if (clickedId === actualTab) return;

                        actualTab = clickedId;

                        Array.from(aside.children).forEach(el => {
                            el.classList.remove("bg-gray-400/50", "border-l-6", "border-default-green");
                        });

                        e.currentTarget.classList.add("bg-gray-400/50", "border-l-6", "border-default-green");

                        main.innerHTML = "";
                        updateTab();
                        toggleSidebar();
                    });

                    aside.appendChild(a);
                }

                Object.entries(CONFIG.COMMONTABLIST).forEach(([id, label]) => {
                    genTab(id, label)
                });

                checkUser().then(role => {
                    if (role === "admin") {
                        Object.entries(CONFIG.HIGLEVELTABLIST).forEach(([id, label]) => {
                            genTab(id, label);
                        });
                    }

                    if (role === "reception") {
                        genTab(Object.entries(CONFIG.HIGLEVELTABLIST)[1][0], Object.entries(CONFIG.HIGLEVELTABLIST)[1][1]);
                    }
                });

                document.querySelectorAll('#sidebar-overlay, #open-sidebar, #close-sidebar').forEach(btn => {
                    btn.addEventListener("click", toggleSidebar);
                });

                document.addEventListener("keydown", e => {
                    if (e.key === "Escape" && !document.getElementById('sidebar-overlay').classList.contains("hidden")) {
                        toggleSidebar();
                    }
                });
            }
        }

        this.registerUser = class {
            constructor() {
                register_Inputs = document.createElement("form")
                register_Inputs.className = "p-8 bg-white rounded-xl shadow-lg overflow-hidden border-t-4 border-default-blue row-span-4 w-150 h-100 self-center justify-self-center flex flex-col justify-center items-center *:w-full *:mb-8"
                register_Inputs.action = "/api/register-user"
                register_Inputs.method = "post"
                register_Inputs.innerHTML = `<h2 class="text-3xl! mt-8 font-bold text-center text-default-blue">Cadastrar Usuário</h2>`

                register_Inputs.addEventListener("submit", async (e) => {
                    e.preventDefault();

                    const formData = new FormData(register_Inputs);

                    try {
                        const response = await fetch(register_Inputs.action, {
                            method: register_Inputs.method,
                            body: formData
                        });

                        const result = await response.json();

                        if (response.ok) {
                            console.log("Sucesso:", result.Message); 
                            alert("Usuário cadastrado com sucesso!");
                            register_Inputs.reset();
                        } else {
                            console.error("Erro no servidor:", result.Message);
                            alert("Erro ao cadastrar: " + result.Message);
                        }
                    } catch (error) {
                        console.error("Erro na requisição:", error);
                        alert("Não foi possível conectar ao servidor.");
                    }
                });

                const usernameInput = document.createElement("div")
                usernameInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Nome de Usuário</label>
                    <input name="username" type="text" minlength="4" placeholder="Ex: admin" class="rounded-sm w-full px-4 py-2 border border-gray-300 focus:ring-2 focus:ring-default-blue focus:border-transparent outline-none transition-all">
                `

                // const usernameInput = document.createElement("input")
                // usernameInput.placeholder = "Nome do Usuario"
                // usernameInput.name = "username"
                // usernameInput.required = true
                // usernameInput.minLength = "4"
                // usernameInput.type = "text"

                const roleInput = document.createElement("div")
                roleInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Nível de Acesso</label>
                    <select name="role" class="rounded-sm w-full px-4 py-2 border border-gray-300 focus:ring-2 focus:ring-default-blue outline-none appearance-none bg-white">
                        <option value="User">User</option>
                        <option value="Admin">Admin</option>
                        <option value="Reception">Reception</option>
                        <option value="Aprendiz">Aprendiz</option>
                    </select>
                `

                const btn = document.createElement("button")
                btn.type = "submit"
                btn.className = "cursor-pointer rounded-sm hover:text-default-green w-full bg-default-blue text-white font-bold py-3 shadow-md transform active:scale-95 transition-all uppercase tracking-wide mt-4"
                btn.innerText = "Salvar Registro"

                register_Inputs.appendChild(usernameInput)
                register_Inputs.appendChild(roleInput)
                register_Inputs.appendChild(btn)
            }
        }

        this.registerNewMail = class {
            constructor() {
                entrada_Inputs = document.createElement("form")
                entrada_Inputs.className = "p-8 md:gap-6 bg-white rounded-xl shadow-lg overflow-hidden border-t-4 border-default-blue row-span-4 w-200 h-120 self-center justify-self-center grid justify-center items-center grid-cols-2 *:w-full "
                entrada_Inputs.action = "/mails/register"
                entrada_Inputs.method = "post"
                entrada_Inputs.innerHTML = `<h2 class="col-span-2 text-3xl! mt-8 font-bold text-center text-default-blue">Cadastrar Nova Correspondencia</h2>`

                entrada_Inputs.addEventListener("submit", async (e) => {
                    e.preventDefault();

                    const formData = new FormData(entrada_Inputs);
                    
                    try {
                        // console.log(formData)
                        const response = await fetch(entrada_Inputs.action, {
                            method: entrada_Inputs.method,
                            body: formData
                        });

                        const result = await response.json();

                        if (response.ok) {
                            console.log("Sucesso:", result.Message);
                            alert("Correspondencia cadastrada com sucesso!");
                            entrada_Inputs.reset();
                        } else {
                            console.error("Erro no servidor:", result.Message);
                            alert("Erro ao cadastrar: " + result.Message);
                        }
                    } catch (error) {
                        console.error("Erro na requisição:", error);
                        alert("Não foi possível conectar ao servidor.");
                    }
                });

                const senderInput = document.createElement("div")
                senderInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Destinatario Completo</label>
                    <input name="sender" required type="text" minlength="4" placeholder="Ex: Arcos Dourados Comercio de Alim S.A" class=" w-full px-4 py-2 rounded-sm border border-gray-300 focus:ring-2 focus:ring-default-blue focus:border-transparent outline-none transition-all">
                `

                const fantInput = document.createElement("div")
                fantInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Nome Fantasia</label>
                    <input name="fantasy" type="text" minlength="4" placeholder="Ex: MC Donald's" class=" w-full px-4 py-2 border border-gray-300 rounded-sm focus:ring-2 focus:ring-default-blue focus:border-transparent outline-none transition-all">
                `

                const codeInput = document.createElement("div")
                codeInput.className = "col-span-2"
                codeInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Codigo de Rastreio</label>
                    <input name="code" required type="text" minlength="4" placeholder="Ex: AB123456789BR" class="w-full px-4 py-2 border border-gray-300 rounded-sm focus:ring-2 focus:ring-default-blue focus:border-transparent outline-none transition-all">
                `

                const typeInput = document.createElement("div")
                typeInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Tipo da Correspondencia</label>
                    <select name="type" class="w-full rounded-sm px-4 py-2 border border-gray-300 focus:ring-2 focus:ring-default-blue outline-none appearance-none bg-white">
                        <option value="Caixa">Caixa</option>
                        <option value="Carta">Carta</option>
                        <option value="Pacote">Pacote</option>
                    </select>
                `

                const priorInput = document.createElement("div")
                priorInput.innerHTML = `
                    <label class="block font-semibold text-gray-600 mb-1">Prioridade da Correspondencia</label>
                    <select name="priority" class="w-full rounded-sm px-4 py-2 border border-gray-300 focus:ring-2 focus:ring-default-blue outline-none appearance-none bg-white">
                        <option value="Simples">Simples</option>
                        <option value="Judicial">Judicial</option>
                    </select>
                `

                const btn = document.createElement("button")
                btn.type = "submit"
                btn.className = "cursor-pointer rounded-sm hover:text-default-green col-span-2 w-full bg-default-blue text-white font-bold py-3 shadow-md transform active:scale-95 transition-all uppercase tracking-wide mt-4"
                btn.innerText = "Salvar Registro"

                entrada_Inputs.appendChild(senderInput)
                entrada_Inputs.appendChild(fantInput)
                entrada_Inputs.appendChild(typeInput)
                entrada_Inputs.appendChild(priorInput)
                entrada_Inputs.appendChild(codeInput)
                entrada_Inputs.appendChild(btn)
            }
        }
    }
}

window.onload = function () {
    const preload = new Preload()

    new preload.resumo_Body()
    new preload.loadSidebarTabs()

    checkUser().then(role => {
        if (role === "reception") {
            new preload.registerNewMail()
        } else if (role === "admin") {
            new preload.registerUser()
            new preload.registerNewMail()
        }
    });

    updateTab();
};