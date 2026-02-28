let actualTab = "resumo"
let lastFilter = ""
let lastOrderBy = "id"
let orderDirection = "DESC"

let resumoMailsBody
let resumoMailsContainer

let MainBody

const CONFIG = {
    GRID_LAYOUT: "grid-cols-[1cm_1fr_3.2cm_0.5fr_1.4cm_2cm_2.2cm_3.7cm_2.5cm_2.8cm]",
    TITLES: {
        "ID": "id",
        "Nome": "name",
        "Codigo AR": "code",
        "Nome Fantasia": "fantasy",
        "Tipo": "type",
        "Prioridade": "priority",
        "Entrada": "join_date",
        "Recebedor / Motivo": "receive_name",
        "Data Saída": "receive_date",
        "Comprovante": "photo_id"
    },
    TABLIST: {
        "resumo": "Resumo",
        "reg-entrada": "Registrar Entrada",
        "reg-saida": "Registrar Saida",
        "gen-devolucao": "Gerar Devolção"
    }
};

function formatDate(dateStr) {
    if (!dateStr) return "";
    return dateStr.split('-').reverse().join("/");
}

function isDelayed(dateStr, priority) {
    const [d, m, y] = formatDate(dateStr).split("/");
    const diff = (new Date().setHours(0, 0, 0, 0) - new Date(`${y}-${m}-${d}`).setHours(0, 0, 0, 0)) / 86400000;
    const limit = (priority === "Simples") ? 7 : 4;
    return diff > limit;
}

function getPriorityClass(priority) {
    const color = priority === "Judicial" ? "bg-red-500/30" : "bg-green-500/30";
    return ` ${color} rounded-full px-2`;
}

function createMailRow(mail) {
    const row = document.createElement("div");
    row.className = `grid ${CONFIG.GRID_LAYOUT} gap-2 py-3 border-b border-gray-700/50 hover:bg-white/5 items-center text-xs transition-colors text-center`;

    const data = {
        id: mail[0],
        priority: mail[5],
        status: mail[9],
        entryDate: mail[10],
        exitDate: mail[12],
        receipt: mail[13]
    };

    if (data.status === "returned") row.classList.add("text-gray-500");
    if (data.status === "casualty") row.classList.add("underline", "decoration-red-500", "decoration-wavy");

    if (["almox", "on_reception"].includes(data.status) && data.entryDate) {
        if (isDelayed(data.entryDate, data.priority)) {
            row.classList.add("text-red-500");
        }
    }

    mail.forEach((info, idx) => {
        if ([6, 7, 8, 9].includes(idx)) return;

        const span = document.createElement("span");
        span.className = "truncate overflow-hidden whitespace-nowrap";

        let content = info;
        if (idx === 10 || idx === 12) content = formatDate(info);
        if (idx === 2) span.classList.add("font-bold");
        if (idx === 5) span.className += getPriorityClass(info);
        if (idx === 13) span.className += " cursor-pointer bg-blue-300/30 hover:bg-blue-700";

        span.innerText = content || "";
        row.appendChild(span);
    });

    return row;
}


function renderMails(mails) {
    resumoMailsBody.innerHTML = "";
    const fragment = document.createDocumentFragment();

    mails.forEach(mail => {
        const mailDiv = createMailRow(mail);
        fragment.appendChild(mailDiv);
    });

    resumoMailsBody.appendChild(fragment);
    resumoMailsContainer.appendChild(resumoMailsBody);

    MainBody.innerHTML = ""; // Limpa antes de adicionar
    MainBody.classList.add(CONFIG.GRID_LAYOUT); // Aplica a classe ao container pai se necessário
    MainBody.appendChild(resumoMailsContainer);
}

async function updateTab() {
    if (!["resumo"].includes(actualTab)) {
        MainBody.innerHTML = `<h1>${actualTab.toUpperCase()}</h1>`;
        return;
    }

    try {
        const response = await fetch("/mails/get-mails", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify([lastFilter, lastOrderBy, orderDirection])
        });

        const json = await response.json();
        renderMails(json[0].mails);
    } catch (err) {
        console.error("Erro ao buscar e-mails:", err);
    }
}

window.onload = function () {
    MainBody = document.querySelector("main");
    const aside = document.getElementById("aside-options");

    Object.entries(CONFIG.TABLIST).forEach(([id, label]) => {
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

            MainBody.innerHTML = "";
            updateTab();
        });

        aside.appendChild(a);
    });

    resumoMailsContainer = document.createElement("div");
    resumoMailsContainer.className = "bg-default-blue h-100 w-full overflow-x-auto overflow-y-scroll self-end mx-4 mb-4 text-white border border-gray-600";

    const titleContainer = document.createElement("div");
    titleContainer.id = "title-container";
    titleContainer.className = `grid ${CONFIG.GRID_LAYOUT} cursor-pointer sticky top-0 z-10 gap-2 bg-gray-800 *:h-10 font-bold border-b border-gray-600 text-sm min-w-300 *:flex *:items-center *:justify-center *:select-none`;

    resumoMailsBody = document.createElement("div");
    resumoMailsBody.className = `*:${CONFIG.GRID_LAYOUT} *:grid flex flex-col min-w-300 *:gap-2 *:py-3 *:border-b *:border-gray-700/50 *:hover:bg-white/5 *:items-center *:text-xs *:transition-colors *:text-center **:text-ellipsis **:whitespace-nowrap **:overflow-hidden`;

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

    resumoMailsContainer.appendChild(titleContainer);

    const toggleSidebar = () => {
        document.getElementById("sidebar").classList.toggle('-translate-x-full');
        document.getElementById('sidebar-overlay').classList.toggle("hidden");
    };

    document.querySelectorAll('#sidebar-overlay, #open-sidebar, #close-sidebar').forEach(btn => {
        btn.addEventListener("click", toggleSidebar);
    });

    document.addEventListener("keydown", e => {
        if (e.key === "Escape" && !document.getElementById('sidebar-overlay').classList.contains("hidden")) {
            toggleSidebar();
        }
    });

    updateTab();
};