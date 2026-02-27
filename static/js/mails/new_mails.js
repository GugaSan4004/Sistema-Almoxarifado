let actualTab = "resumo"
let lastFilter = ""
let lastOrderBy = "id"
let orderDirection = "DESC"

let tabList = []

let resumoMailsBody
let resumoMailsContainer

let MainBody

function updateTab() {
    const main = document.querySelector("main")

    main.innerHTML = ""

    if (actualTab == tabList[0]) {
        fetch("/mails/get-mails", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify([lastFilter, lastOrderBy, orderDirection])
        })
            .then(response => response.json())
            .then(json => {
                const mails = json[0].mails

                resumoMailsBody.innerHTML = ""

                mails.forEach((mail) => {
                    const maildiv = document.createElement("div")

                    mail.forEach((info, index) => {
                        if (index != 6 && index != 7 && index != 8 && index != 9) {
                            const span = document.createElement("span")
                            span.innerText = info

                            maildiv.appendChild(span)
                        }
                    })

                    resumoMailsBody.appendChild(maildiv)

                })

                resumoMailsContainer.appendChild(resumoMailsBody)


                main.classList.toggle("**:**:grid-cols-[1cm_1fr_3.2cm_0.5fr_1.4cm_2cm_2.2cm_3.7cm_2.5cm_2.8cm]")
                MainBody.appendChild(resumoMailsContainer)




                // <div>
                //     <span class="text-gray-400">360</span>
                //     <span class="truncate font-medium" title="Nome Completo do Usuário Aqui">Transporte De Passageiros E
                //         Serviços De Fretamento</span>
                //     <span class="font-bold">QB782685462BR</span>
                //     <span class="truncate text-gray-300" title="Nome Fantasia da Empresa">Bemto Fragoso da minha</span>
                //     <span>Carta</span>
                //     <span
                //         class="px-2 py-0.5 bg-red-900/50 text-red-100 rounded-full text-center text-[10px]">Simples</span>
                //     <span>26/02/2026</span>
                //     <span class="truncate">Larissa de sousa</span>
                //     <span>25-02-2026</span>
                //     <button class="bg-blue-600 hover:bg-blue-500 py-1 rounded cursor-pointer">CAI588BR352</button>
                // </div>
                // main.innerHTML = json[0].mails
            })

    } else if (actualTab == tabList[1]) {
        main.innerHTML = "Entradas"
    } else if (actualTab == tabList[2]) {
        main.innerHTML = "Saidas"
    } else if (actualTab == tabList[3]) {
        main.innerHTML = "Devolção"
    }
}

window.onload = function () {
    MainBody = document.querySelector("main")

    document.querySelectorAll("#aside-options > a").forEach(element => {
        tabList.push(element.id)
    })

    resumoMailsContainer = document.createElement("div")
    resumoMailsContainer.classList.add("bg-default-blue", "h-100", "w-full", "overflow-x-auto", "overflow-y-scroll", "self-end", "mx-4", "mb-4", "text-white", "border", "border-gray-600")

    const titleList = {
        "ID": "id",
        "Nome": "name",
        "Cod. AR": "code",
        "Nome Fantasia": "fantasy",
        "Tipo": "type",
        "Prioridade": "priority",
        "Entrada": "join_date",
        "Recebedor / Motivo": "receive_name",
        "Data Saída": "receive_date",
        "Comprovante": "photo_id"
    }

    const titleContainer = document.createElement("div")
    titleContainer.classList.add("grid-cols-[1cm_1fr_3.2cm_0.5fr_1.4cm_2cm_2.2cm_3.7cm_2.5cm_2.8cm]", "cursor-pointer", "grid", "sticky", "top-0", "z-10", "gap-2", "bg-gray-800", "*:h-10", "font-bold", "border-b", "border-gray-600", "text-sm", "min-w-300", "*:flex", "*:items-center", "*:justify-center")

    resumoMailsBody = document.createElement("div")
    resumoMailsBody.classList.add("*:grid-cols-[1cm_1fr_3.2cm_0.5fr_1.4cm_2cm_2.2cm_3.7cm_2.5cm_2.8cm]", "*:grid", "flex", "flex-col", "min-w-300",
        "*:gap-2", "*:py-3", "*:border-b", "*:border-gray-700/50", "*:hover:bg-white/5", "*:items-center", "*:text-xs", "*:transition-colors", "*:text-center", "**:text-ellipsis", "**:whitespace-nowrap", "**:overflow-hidden")

    Object.keys(titleList).forEach(element => {
        const span = document.createElement("span")
        span.innerText = element

        if(element == "ID") {
            span.classList.add("text-default-green")
        }

        titleContainer.appendChild(span)
    });

    resumoMailsContainer.appendChild(titleContainer)

    function toggle() {
        document.getElementById("sidebar").classList.toggle('-translate-x-full');
        document.getElementById('sidebar-overlay').classList.toggle("hidden")
    };

    document.getElementById('sidebar-overlay').addEventListener("click", () => {
        toggle()
    });

    document.getElementById("open-sidebar").addEventListener("click", () => {
        toggle()
    });

    document.getElementById("close-sidebar").addEventListener("click", () => {
        toggle()
    });

    document.addEventListener("keydown", k => {
        if (k.key == "Escape") {
            toggle()
        }
    });

    const optList = document.querySelectorAll("#aside-options > a")

    optList.forEach(opt => {
        opt.addEventListener("click", () => {
            if (opt.id == actualTab) {
            } else {
                actualTab = opt.id

                optList.forEach(e => {
                    e.classList.remove("bg-gray-400/50", "border-l-6", "border-default-green")
                });

                opt.classList.add("bg-gray-400/50", "border-l-6", "border-default-green")

                updateTab()
            }
        });
    });

    updateTab()
}