const tabList = ["resumo", "reg-entrada", "reg-saida", "gen-devolucao"]

let actualTab = "resumo"
let lastFilter = ""
let lastOrderBy = "id"
let orderDirection = ""

function updateTab() {
    const main = document.querySelector("main")

    if (actualTab == tabList[0]) {
        fetch("/mails/get-mails", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify([lastFilter, lastOrderBy,  ])
        })
            .then(response => response.json())
            .then(json => {
                main.innerHTML = json
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