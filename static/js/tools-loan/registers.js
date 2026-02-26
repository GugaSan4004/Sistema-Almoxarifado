socket = io();

function updateGrid(data) {
    const tools = {}

    data.loaned_tools.forEach(tool => {
        tools[tool[2]] = tool[4];
    });

    document.querySelectorAll(".animate-fade-in").forEach(
        container => container.classList.replace("animate-fade-in", "animate-fade-out")
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
            tool_container.classList.add("flex-[0_1_calc(20%-11px)]", "select-none", "grid", "grid-cols-3", "bg-white", "font-bold", "text-lg", "border", "border-gray-600/60", "rounded-md", "p-2", "shadow-[4px_4px_7px]", "justify-items-center", "animate-fade-in");
            tool_container.id = `${tool.replaceAll('\"', "").toLowerCase()}-container`

            let allTool

            data.all_tools.forEach(to => {
                if (to[2] === tool) {
                    allTool = to
                }
            });

            let pictureData = data.all_movements.find(mov => mov[0] === movement_id);
            let picturePath = null

            if (pictureData != undefined) {
                picturePath = `/pictures/loans/${pictureData[4]}/${pictureData[3]}/${String(pictureData[0]).padStart(6, '0')}.jpg`;
            } else {
                pictureData = [""]
            }

            if (!picturePath || allTool[3] == "Casualty") {
                tool_container.classList.add("shadow-red-400")
            } else {
                tool_container.classList.add("shadow-white/50")
            }

            const dictionary = {
                'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
                'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                'ç': 'c', 'ñ': 'n'
            };

            let toolid = ""
            for (const toolnow of data.loaned_tools) {
                if (toolnow[2] == tool) {
                    toolid = toolnow[0];
                    break;
                }
            }


            // if(tool_container.classList.contains('casualty')) {
            //     tool_container.innerHTML = `
            //         <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
            //             <h1>&#9888;</h1>
            //         </div>

            //         <h1 class="number">
            //             &#9888;
            //         </h1>
            //     `
            // } else if(tool_container.classList.contains('missing')) {
            //     tool_container.innerHTML = `
            //         <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
            //             <h1>&#9888;</h1>
            //         </div>

            //         <h1 class="number">
            //             &#9888;
            //         </h1>
            //     `
            // } else {
            // <div id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}-traffic" class="mac-traffic">
            //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="green"></span>
            //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="yellow"></span>
            //     <span id="${tool.replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"ºª]/g, char => dictionary[char] || '').replaceAll(' ', '-').toLowerCase()}" class="red"></span>
            // </div>


            // }
            const number = document.createElement("h1")
            number.innerText = pictureData[0].toString().padStart(6, '0')
            number.classList.add("justify-self-start", "text-base")

            
            const mac = document.createElement("div")
            mac.classList.add("justify-self-end", "flex", "gap-x-0.5")
            mac.id = `${toolid}-traffic`
            
            for(c of ["green", "yellow", "red"]) {
                const span = document.createElement("span")
                span.id = toolid
                span.classList.add("block", `bg-${c}-500`, "w-4", "h-4", "rounded-full", "cursor-pointer", "border-2", "border-gray-700/70")
                mac.appendChild(span)
            }

            const svg = document.createElement("img")
            svg.classList.add("h-20", "border", "border-3", "p-1.5", "rounded-md")
            svg.src = `/static/imgs/tools-loan/${tool.toLowerCase()
                .replace(/[ãáàâäéèêëíìîïóòôöúùûüçñ'"º ª]/g, char => dictionary[char] || '-')
                .replace(/^-+|-+$/g, '')
                }.png
            `
            svg.alt = `Imagem de: ${tool}`

            const tool_name = document.createElement("h1")
            tool_name.classList.add("font-md", "col-span-3", "my-2")
            tool_name.innerText = tool.replaceAll(" ", "-").toLowerCase()
                .replace(".png", "")
                .replace(/-/gm, " ")
                .replace(/\b\w/g, c => c.toUpperCase())

            const picture = document.createElement("img")
            picture.classList.add("flex", "col-span-3", "row-span-2", "border-3", "rounded-md", "h-46", "w-70", "justify-center", "items-center")
            picture.src = picturePath
            picture.alt = `${picturePath ? 'Foto de: ' + tool : 'Não registrado!'}`

            tool_container.appendChild(number)
            tool_container.appendChild(svg)
            tool_container.appendChild(mac)
            tool_container.appendChild(tool_name)
            tool_container.appendChild(picture)

            body.appendChild(tool_container);

            tool_container.addEventListener("click", function (event) {
                if (event.target.classList.contains("bg-green-500")) {
                    document.getElementById(`${String(event.target.id).replaceAll(" ", "-").toLowerCase()}-traffic`).remove()
                    fetch("/tools-loan/add-tool", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: event.target.id.toLowerCase() })
                    }).then(() => {
                        load()
                    })
                } else if (event.target.classList.contains("bg-yellow-500")) {
                    fetch("/tools-loan/registers/missing", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ code: event.target.id.toLowerCase() })
                    }).then(() => {
                        load()
                    })
                } else if (event.target.classList.contains("bg-red-500")) {
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
            if (data[1] !== 200) {
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