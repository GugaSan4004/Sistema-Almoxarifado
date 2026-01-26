socket = io();

function updateGrid(data) {
    const tools = {}

    data.loaned_tools.forEach(tool => {
        tools[tool[2]] = tool[4];
    });

    document.querySelectorAll(".tool-container").forEach(
        container => container.classList.add("fade-out")
    );

    setTimeout(() => {
        const body = document.querySelector("main");
        body.innerHTML = "";

        if (Object.keys(tools).length === 0) {
            body.innerHTML = "Todas as ferramentas estão disponíveis!";
            return;
        }

        Object.entries(tools).forEach(([tool, movement_id]) => {
            const tool_container = document.createElement("div");
            tool_container.classList.add("tool-container");
            tool_container.id = `${tool.replaceAll('\"', "").toLowerCase()}-container`

            let picture = data.all_movements.find(mov => mov[0] === movement_id);
            let picturePath = null

            if (picture != undefined) {
                picturePath = `/pictures/loans/${picture[4]}/${picture[3]}/${String(picture[0]).padStart(6, '0')}.jpg`;
            } else {
                picture = [""]
            }

            const dictionary = {
                'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
                'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                'ç': 'c', 'ñ': 'n'
            };

            let allTool

            data.all_tools.forEach(to => {
                if(to[2] === tool) {
                    allTool = to
                }
            });

            if (!picturePath) {
                tool_container.classList.add("missing")
            } else if(allTool[3] == "Casualty") {
                tool_container.classList.add("casualty")
            }

            if(tool_container.classList.contains('casualty')) {
                tool_container.innerHTML = `
                    <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
                        <h1>&#9888;</h1>
                    </div>

                    <h1 class="number">
                        &#9888;
                    </h1>
                `
            } else if(tool_container.classList.contains('missing')) {
                tool_container.innerHTML = `
                    <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
                        <h1>&#9888;</h1>
                    </div>

                    <h1 class="number">
                        &#9888;
                    </h1>
                `
            } else {
                    // <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
                    //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="green"></span>
                    //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="yellow"></span>
                    //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="red"></span>
                    // </div>
                
                let toolid = ""
                for (const toolnow of data.loaned_tools) {
                    if (toolnow[2] == tool) {
                        toolid = toolnow[0];
                        break;
                    }
                }

                tool_container.innerHTML = `
                    <div id="${toolid}-traffic" class="mac-traffic">
                        <span id="${toolid}" class="green"></span>
                        <span id="${toolid}" class="yellow"></span>
                        <span id="${toolid}" class="red"></span>
                    </div>

                    <h1 class="number">
                        ${picture[0].toString().padStart(6, '0')}
                    </h1>
                `
            }

            tool_container.innerHTML += `
            <img class="svg" src="/static/imgs/tools-loan/${tool.toLowerCase()
                    .replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"º ª]/g, char => dictionary[char] || '-')
                    .replace(/^-+|-+$/g, '')
            }.png" alt="Imagem de: ${tool}">
            
            <h1 class="name">${tool.replaceAll(" ", "-").toLowerCase()
                .replace(".png", "")
                .replace(/-/gm, " ")
                .replace(/\b\w/g, c => c.toUpperCase())
            }</h1>
            <img class="picture" src="${picturePath}" alt="${picturePath ? 'Foto de: ' + tool : 'Não registrado!'}">
            `;

            body.appendChild(tool_container);

            tool_container.addEventListener("click", function (event) {
                if (event.target.classList.contains("green")) {
                    document.getElementById(`${String(event.target.id).replaceAll(" ", "-").toLowerCase()}-traffic`).remove()
                    fetch("/tools-loan/add-tool", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: event.target.id.toLowerCase() })
                    }).then(() => {
                        load()
                    })
                } else if (event.target.classList.contains("yellow")) {
                    fetch("/tools-loan/registers/missing", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: event.target.id.toLowerCase() })
                    }).then(() => {
                        load()
                    })
                } else if (event.target.classList.contains("red")) {
                    fetch("/tools-loan/registers/casualty", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: event.target.id.toLowerCase() })
                    }).then(() => {
                        load()
                    })
                }
            })
        });


    }, 600);
}

function load() {
    fetch("/tools-loan/get-registers", {
        method: "GET",
        headers: { "Content-Type": "application/json" }
    })
    .then(response => response.json())
    .then(data => {
        if(data[1] !== 200 ) {
            return
        } else {
            updateGrid(data[0])
        }
    })
}

socket.on("update_pictures", () => {
    load()
});

window.onload = function () {
    load()
}