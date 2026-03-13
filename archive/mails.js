let last_filter = ""
let last_orderBy = "id"
let orderDirection = ""

const preview = document.createElement("img");
preview.className = "picture_preview";
document.body.appendChild(preview);

document.addEventListener("DOMContentLoaded", function () {
    fetch("/user-ip", {
        method: "GET",
        headers: {
            "Content-Type": "application/json"
        }
    })
        .then(response => response.json())
        .then(data => {
            if (["192.168.7.119", "192.168.7.94", "127.0.0.1"].includes(data[0].Message)) {
                document.querySelector(".options").innerHTML += `
                <button id="returns" onclick="focuses('return-container')">Gerar Devoluções</button>
            `

                focuses("db-container")
                getCorrespondences()
            }

            if (["192.168.7.58", "192.168.7.94", "127.0.0.1"].includes(data[0].Message)) {
                document.querySelector(".options").insertAdjacentHTML("afterbegin", `
                <button id="register" onclick="focuses('insert-container')">Cadastrar</button>
            `);
                focuses("insert-container")
            }
        })
});

function changeShipContainer(event) {
    document.querySelectorAll(".ship-container").forEach(container => {
        container.style.display = "none";
    });

    if (event.target.checked) {
        document.getElementById("ship-almox").style.display = "grid";
    } else {
        document.getElementById("ship-mall").style.display = "grid";
    }
}

first = true

function getCorrespondences(filter, orderBy, btn) {
    if (btn === "me" && first) {
        orderDirection = "DESC"
        first = false
    } else if (btn === "me" && !first) {
        orderDirection = orderDirection
    } else {
        if (last_orderBy != orderBy && orderBy) {
            last_orderBy = orderBy
            orderDirection = "DESC"
        } else {
            orderDirection = orderDirection == "ASC" ? "DESC" : "ASC"
        }

        if (filter !== "" && filter !== null) {
            last_filter = filter
        } else if (filter === "") {
            last_filter = null
        }

    }

    fetch("/mails/get-mails", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify([last_filter, last_orderBy, orderDirection])
    })
        .then(response => response.json())
        .then(json => {
            const container = document.getElementById("db-container");

            document.querySelectorAll('.db-container-values, .db-container-title')
                .forEach(el => el.remove());

            container.innerHTML += `
            <div class="db-container-title">
                <b id="id">ID</b>
                <b id="name">Nome</b>
                <b id="code">Codigo AR</b>
                <b id="fantasy">Nome Fantasia</b>
                <b id="type">Tipo</b>
                <b id="priority">Prioridade</b>
                <b id="join_date">Data Entrada</b>
                <b id="receive_name">Recebedor / Motivo</b>
                <b id="receive_date">Data Saida</b>
                <b id="photo_id">Comprovante</b>
            </div>
        `
            const headers = document.querySelectorAll(".db-container-title b");

            headers.forEach(header => {
                header.classList.remove("order")
                header.addEventListener("click", () => {
                    const orderByButton = header.id;
                    getCorrespondences(null, orderByButton);
                });
            });

            document.getElementById(last_orderBy).classList.add("order")
            document.getElementById("search_input").value = last_filter ? last_filter : ""

            const content_container = document.createElement("div");

            content_container.classList.add("db-container-values")

            Object.entries(json[0].mails).forEach(data => {
                Object.entries(data[1]).forEach((correpondence, index, array) => {
                    if (index !== 6 && index !== 7 && index !== 8 && index !== 9) {
                        const [y, m, d] = data[1][10].split("-").map(Number);

                        const delayed = ((new Date().setHours(0, 0, 0, 0) - new Date(y, m - 1, d).setHours(0, 0, 0, 0)) / (1000 * 60 * 60 * 24));

                        if (index === array.length - 1) {
                            const td = document.createElement("td");
                            td.classList.add("picture_link");

                            td.textContent = correpondence[1];
                            td.dataset.img = data[1][13] ? `/pictures/mails/${data[1][13]}.jpg` : "";

                            if (data[1][9] == "on_reception") {
                                td.classList.add("on_reception")
                            } else if (data[1][9] == "returned") {
                                td.classList.add("returned")
                            }

                            if (["casualty"].includes(data[1][9])) {
                                td.classList.add("casualty")
                            } else if (delayed > 6 && !["shipped", "returned"].includes(data[1][9])) {
                                td.classList.add("delayed")
                            }


                            content_container.appendChild(td);

                            if (td.dataset.img) {
                                td.style.cursor = "pointer"

                                td.addEventListener("click", function () {
                                    window.open(td.dataset.img, "_blank");
                                })

                                let hoverTimeout = null;

                                td.addEventListener("mouseover", function (e) {
                                    hoverTimeout = setTimeout(() => {
                                        if (preview.src !== td.dataset.img) {
                                            preview.src = td.dataset.img;

                                            preview.style.display = "block";

                                            const previewWidth = preview.offsetWidth;
                                            const previewHeight = preview.offsetHeight;

                                            const margin = 15; // espaço de segurança da borda

                                            let x = e.pageX - 360;
                                            let y = e.pageY - 180;

                                            const maxX = window.scrollX + window.innerWidth - previewWidth - margin;
                                            const maxY = window.scrollY + window.innerHeight - previewHeight - margin;

                                            if (x < margin) x = margin;
                                            if (y < margin) y = margin;
                                            if (x > maxX) x = maxX;
                                            if (y > maxY) y = maxY;

                                            preview.style.left = x + "px";
                                            preview.style.top = y + "px";
                                        }
                                    }, 150);
                                });

                                td.addEventListener("mouseout", function () {
                                    clearTimeout(hoverTimeout);
                                    preview.style.display = "none";
                                });

                                td.addEventListener("mousemove", function (e) {
                                    const previewWidth = preview.offsetWidth;
                                    const previewHeight = preview.offsetHeight;

                                    const margin = 15;

                                    let x = e.pageX - 360;
                                    let y = e.pageY - 180;

                                    const maxX = window.scrollX + window.innerWidth - previewWidth - margin;
                                    const maxY = window.scrollY + window.innerHeight - previewHeight - margin;

                                    if (x < margin) x = margin;
                                    if (y < margin) y = margin;
                                    if (x > maxX) x = maxX;
                                    if (y > maxY) y = maxY;

                                    preview.style.left = x + "px";
                                    preview.style.top = y + "px";
                                });
                            }
                        } else if ((index === 3 || index === 1) && ["almox", "reception"].includes(data[1][9])) {
                            const field = document.createElement("input");

                            field.value = data[1][index];
                            field.classList.add("input_db")
                            field.id = data[1][2]

                            if (data[1][9] == "on_reception") {
                                field.classList.add("on_reception")
                            } else if (data[1][9] == "returned") {
                                field.classList.add("returned")
                            }

                            if (delayed > 6 && !["shipped", "returned"].includes(data[1][9])) {
                                field.classList.add("delayed")
                            }


                            let old_value = ""
                            field.addEventListener("focus", () => {
                                old_value = field.value
                            })

                            field.addEventListener("blur", function () {
                                if (field.value == old_value) return
                                else {
                                    fetch("/mails/update-column", {
                                        method: "POST",
                                        headers: {
                                            "Content-Type": "application/json"
                                        },
                                        body: JSON.stringify({
                                            code: field.id,
                                            column: headers[index].id,
                                            new_value: field.value,
                                            old_value: old_value
                                        })
                                    })
                                }
                            })

                            field.addEventListener("keydown", function (e) {
                                if (e.key === 'Enter') {
                                    field.blur();
                                } else if (e.key === "Escape") {
                                    field.value = old_value;
                                    field.blur();
                                }
                            })

                            content_container.appendChild(field);
                        } else {
                            const dictionary = {
                                "on_reception": "Na Recepção",
                                "returned": "Devolvido",
                                "casualty": "Sinistro na Correspondencia",
                                "shipped": "Entregue",
                                "almox": "No Almoxarifado",
                            }

                            const field = document.createElement("td");
                            if (data[1][9] == "on_reception") {
                                field.classList.add("on_reception")
                            } else if (data[1][9] == "returned") {
                                field.classList.add("returned")
                            }

                            if (["casualty"].includes(data[1][9])) {
                                field.classList.add("casualty")
                            } else if (delayed > 6 && !["shipped", "returned"].includes(data[1][9])) {
                                field.classList.add("delayed")
                            }

                            if (index == 10) {
                                if (["almox", "reception"].includes(data[1][9])) {
                                    field.title = `Dias parado: ${delayed}`
                                } else {
                                    field.title = !data[1][13] && data[1][9] == "returned" ? "Documento de devolução Emitido" : dictionary[data[1][9]]
                                }
                                field.textContent = `${String(d).padStart(2, "0") + "-" + String(m).padStart(2, "0") + "-" + y}`;
                            } else {
                                field.title = !data[1][13] && data[1][9] == "returned" ? "Documento de devolução Emitido" : dictionary[data[1][9]]
                                if (index == 12) {
                                    if (data[1][12]) {
                                        const [y12, m12, d12] = data[1][12].split("-").map(Number)
                                        field.textContent = `${String(d12).padStart(2, "0") + "-" + String(m12).padStart(2, "0") + "-" + y12}`;
                                    } else {
                                        field.textContent = null
                                    }
                                } else {
                                    field.textContent = correpondence[1];
                                }
                            }
                            content_container.appendChild(field);
                        }
                    }
                });
            });

            const counts = json[0].totals

            document.getElementById("caption_total").innerText = `Total: ${counts.total}`
            document.getElementById("caption_returned").innerText = `Devolvido: ${counts.returned}`
            document.getElementById("caption_shipped").innerText = `Entregue: ${counts.shipped}`
            document.getElementById("caption_delayed").innerText = `Atrasadas: ${counts.delayed}`

            container.appendChild(content_container);
        })
}

let returns_id = []

function addReturn(element) {

    const container = document.getElementById("return-mails-values")
    const message = document.getElementById("return-message")

    const regexCodigo = /([A-Z]{2}\d{9}[A-Z]{2})/;

    if (!element.value.replaceAll(" ", "").toUpperCase().match(regexCodigo)) {
        element.classList.add("not_found");
        message.innerText = "Codigo invalido!"
        return;
    }

    fetch("/mails/get-mails", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify([element.value, 'id', "ASC"])
    })
        .then(response => response.json())
        .then(json => {

            if (json[0].mails.length === 0) {
                element.classList.add("not_found");
                message.innerText = "Correspondencia não encontrada!"
                return;
            }

            Object.entries(json[0].mails).forEach(data => {
                if (returns_id.includes(data[1][2])) {
                    element.classList.add("not_found");
                    message.innerText = 'Correspondencia já adicionada!';
                    return;
                } else if ("almox" !== data[1][9]) {
                    element.classList.add("not_found");
                    message.innerText = 'Correspondencia não disponivel!'
                    return;
                }

                returns_id.push(data[1][2])

                Object.entries(data[1]).forEach((mail, index, array) => {
                    if ([0, 1, 2, 3, 4, 5, 10].includes(index)) {
                        const td = document.createElement('td')

                        td.innerText = data[1][index]
                        td.classList.add("remove_button")
                        td.id = data[1][2]

                        container.appendChild(td)

                        td.addEventListener('click', function (e) {
                            document.querySelectorAll(`#${e.target.id}`).forEach(b => {
                                b.remove()
                            })
                            returns_id.splice(returns_id.indexOf(e.target.id), 1)
                        })
                    }
                })

                const select = document.createElement('select')

                select.id = data[1][2]
                select.classList.add("return-mails-input")
                select.name = data[1][1]
                select.required = true

                select.innerHTML = `
                <option value="desconhecido">Desconhecido</option>
                <option value="recusado">Recusado</option>
                <option value="mudou-se">Mudou-se</option>
            `

                container.appendChild(select)
                element.value = ""
            })
        })
}

function genReturn() {
    if (returns_id.length > 0) {
        let payload = {};

        returns_id.forEach(id => {
            const select = document.querySelector(`select#${id}`)
            payload[id] = [select.value, select.name];
        })

        const mails_container = document.getElementById("return-mails-container")

        document.body.classList.add("locked")
        mails_container.classList.add("loading")

        fetch("/mails/generate-return", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
            .then(response => response.json())
            .then(json => {
                if (json[1] != 200) {
                    return;
                }

                let iframe = document.getElementById("print-frame");

                if (!iframe) {
                    iframe = document.createElement("iframe");
                    iframe.id = "print-frame";
                    iframe.style.display = "none";
                    document.body.appendChild(iframe);
                }

                iframe.src = json[0].Message;

                iframe.onload = () => {
                    iframe.contentWindow.focus();
                    iframe.contentWindow.print();

                    document.body.classList.remove("locked")
                    mails_container.classList.remove("loading")
                    returns_id = []

                    document.querySelectorAll("#return-mails-values > *").forEach(b => {
                        b.remove()
                    })
                };

            });

    } else {
        document.getElementById("generate_button").classList.add("not_found");
        setTimeout(() => {
            document.getElementById("generate_button").classList.remove("not_found");
        }, 500)
    }
}

function updateReceiver() {
    const input = document.getElementById("file_input");

    const btn = document.querySelector(".to_almox")

    if (btn) {
        btn.style.display = "none"
    }

    const formData = new FormData();
    formData.append("file", input.files[0]);

    const img_container = document.getElementById("image-container")
    const ur_button = document.getElementById("updateReceiver-button")

    if (input.files[0]) {
        ur_button.classList.remove("not_found")

        ur_button.disabled = true
        document.getElementById("file_input").disabled = true

        img_container.classList.add("loading");
    }

    fetch("/mails/upload_file", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(json => {
            if (json[1] !== 200) {
                ur_button.disabled = false
                ur_button.classList.add("not_found")

                document.getElementById("file_input").disabled = false

                img_container.classList.remove("loading")

                return;
            }

            json = json[0].Message

            console.log(json)

            const text = json[0]
                .replace(/\r/g, "")
                .replace(/\n+/g, "\n")
                .replace(/\s+/g, " ")
                .toUpperCase();

            const regexCodigo = /([A-Z]{2}\d{9}[A-Z]{2})/;
            const codigoMatch = json[0].replaceAll(" ", "").toUpperCase().match(regexCodigo);
            const codigo = codigoMatch ? codigoMatch[1] : null;

            // const regexRecebido = /RECEBIDO:?\s*(?:P[O0]R\s*:\s*)?([^\n\r]+)/;
            // const recebidoMatch = json.replaceAll(" ", "").toUpperCase().match(regexRecebido);
            // const recebido = recebidoMatch ? recebidoMatch[1] : null;

            let regexData = /(?:D[O0]C[UUV][MNN][E3][N][T][O0]|DATA)\s*:\s*([0-9Iil\/]{6,12})/i;
            let dataMatch = json[0].replaceAll(" ", "").match(regexData);

            if (!dataMatch) {
                regexData = /\b(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[0-2])\/(\d{2}|\d{4})\b/g;
                dataMatch = json[0].match(regexData);

                if (dataMatch) {
                    if (dataMatch.length <= 1) {
                        dataMatch = null
                    }
                } else {
                    dataMatch = null
                }
            }

            const returnDetected = json[0].replaceAll(" ", "").toUpperCase().includes("DEVOLUCAOAOSCORREIOS") ||
                json[0].replaceAll(" ", "").toUpperCase().includes("DEVOLUÇÃOAOSCORREIOS")

            let ARCodes, reasons, result

            if (returnDetected) {
                const regexAllCodes = /[A-Z]{2}\s*\d{3}\s*\d{3}\s*\d{3}\s*[A-Z]{2}/g;
                ARCodes = text.match(regexAllCodes) || [];

                const regexReasons = /DESCONHECIDO|MUDOU[- ]SE|RECUSADO\s*POR\s*:\s*[A-Z ]+/g;
                reasons = text.match(regexReasons) || [];
            }

            if (ARCodes) {
                result = ARCodes.map((ar, index) => ({
                    code: ar,
                    motivo: reasons[index] || "MOTIVO NÃO IDENTIFICADO"
                }));
            }

            let data = null

            if (dataMatch) {
                let raw = dataMatch[1];

                raw = raw.replace(/[^0-9]/g, "");

                const day = raw.slice(0, 2);
                const month = raw.slice(2, 4);
                let year = raw.slice(4, 8);

                if (year.length === 2) {
                    year = `20${year}`;
                } else if (year.length !== 4) {
                    year = new Date().getFullYear();
                }

                data = `${year}-${month}-${day}`
            }

            if (data == null || isNaN(new Date(data).getTime())) {
                const today = new Date();
                const dd = String(today.getDate()).padStart(2, '0');
                const mm = String(today.getMonth() + 1).padStart(2, '0');
                const yyyy = today.getFullYear();

                data = `${yyyy}-${mm}-${dd}`;
            }

            img_container.classList.add("pp-small")
            img_container.classList.remove("loading")
            img_container.addEventListener("click", function () {
                window.open(document.getElementById("picture-preview").src)
            })

            ur_button.remove()

            const container = document.getElementById("ship-container");

            const body = document.createElement("div")
            body.classList.add("sc-body")

            const user_input = document.createElement("input")
            const data_input = document.createElement("input")
            const type_select = document.createElement("select")

            const submit = document.createElement("button")

            submit.type = "submit"
            submit.classList.add("submit")
            submit.innerHTML = "Registrar"

            user_input.value = json[1][0] ? json[1][0] : ""
            user_input.id = "user_input"

            data_input.type = "date"
            data_input.value = data
            data_input.id = "data_input"

            type_select.id = "type_mail"
            type_select.name = "type"
            type_select.disabled = true
            type_select.innerHTML = `
            <option value="return">Devolução</option>
            <option value="shipment">Entrega</option>
        `

            if (returnDetected) {
                const div_container = document.createElement("div");
                div_container.classList.add("mail-code-list")

                body.style.gridTemplateColumns = "1fr 1fr";
                submit.style.gridColumn = "1 / span 2";

                result.forEach(item => {
                    const ar_input = document.createElement("input");
                    const reason_input = document.createElement("input");

                    ar_input.value = item.code.replaceAll(" ", "");
                    reason_input.value = item.motivo;

                    reason_input.id = item.code;

                    ar_input.classList.add("ar_code")
                    reason_input.classList.add("reason")

                    div_container.appendChild(ar_input);
                    div_container.appendChild(reason_input);
                });

                body.appendChild(div_container)
            } else {
                const code_input = document.createElement("input")
                code_input.value = codigo
                code_input.id = "code_input"

                type_select.value = "shipment"

                body.appendChild(code_input)
                body.appendChild(user_input)
            }

            body.appendChild(type_select)
            body.appendChild(data_input)
            body.appendChild(submit)

            container.appendChild(body)

            submit.addEventListener("click", () => {
                function collectReturnData() {
                    const codes = document.querySelectorAll(".ar_code");
                    const reasons = document.querySelectorAll(".reason");

                    const items = [];

                    codes.forEach((codeInput, index) => {
                        items.push({
                            code: codeInput.value.trim(),
                            motivo: reasons[index]?.value.trim() || ""
                        });
                    });

                    return items;
                }

                const [year, month, day] = data_input.value.split("-");

                let payload

                if (returnDetected) {
                    const items = collectReturnData();

                    if (!items.length) {
                        alert("Nenhum código AR encontrado.");
                        return;
                    }

                    if (items.some(i => !i.code)) {
                        alert("Existe código AR vazio.");
                        return;
                    }

                    payload = {
                        type: "return",
                        date: `${year}-${month}-${day}`,
                        items
                    };
                } else {
                    payload = {
                        type: "shipment",
                        date: `${year}-${month}-${day}`,
                        code: code_input.value,
                        user: user_input.value
                    }
                }

                fetch("/mails/update", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(payload)
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data[1] == 200) {
                            if (data[0].type == "returns") {
                                focuses("db-container")
                                getCorrespondences() -

                                    fetch("/mails/update", {
                                        method: "POST",
                                        headers: {
                                            "Content-Type": "application/json"
                                        },
                                        body: JSON.stringify(payload)
                                    })
                                        .then(response => response.json())
                                        .then(data => {
                                            container.innerHTML = `        
                                <div id="to_almox_button" class="to_almox" ${["192.168.7.58", "192.168.7.94", "127.0.0.1"].includes(data[0].Message) ? "" : "style='display: none'"}>
                                    <label for="to_almox">Para o Almoxarifado</label>
                                    <input type="checkbox" id="to_almox" name="to_almox" value="to_almox" onchange="changeShipContainer(event)">
                                </div>
                                            
                                <form class="ship-container ship-almox" id="ship-almox" style="display: none">
                                    <h1 id="reception-insert-message">Preencha os campos abaixo!</h1>

                                    <input id="mail_code" name="code" type="text" placeholder="Codigo AR" required="">

                                    <select id="receiver_name" name="type" required="">
                                        <option value="kayro">Kayro</option>
                                        <option value="guilherme">Guilherme</option>
                                        <option value="gustavo">Gustavo</option>
                                        <option value="other">Outro(a)</option>
                                    </select>

                                    <select id="sender_name" name="type" required="">
                                        <option value="yara">Yara</option>
                                        <option value="lidia">Lidia</option>
                                        <option value="Michelle">Michelle</option>
                                        <option value="other">Outro(a)</option>
                                    </select>

                                    <button class="submit" onclick="receivedOnReception()" type="button" id="reception-submit">Enviar</button>
                                </form>

                                <div class="ship-container ship-mall" id="ship-mall">
                                    <input type="file" id="file_input" style="display: none">
                                    <div id="image-container" class="image-container">
                                        Clique para selecionar uma imagem!
                                    </div>
                                    <button class="submit" id="updateReceiver-button" onclick="updateReceiver()">Enviar</button>
                                </div>
                            `
                                        })
                            } else {
                                focuses("db-container")
                                getCorrespondences(data[0].PictureName)

                                setTimeout(() => document.querySelectorAll(".db-container-values td").forEach(b => b.classList.add("highlight")), 100)
                                setTimeout(() => document.querySelectorAll(".db-container-values input").forEach(b => b.classList.add("highlight")), 100)

                                fetch("/mails/update", {
                                    method: "POST",
                                    headers: {
                                        "Content-Type": "application/json"
                                    },
                                    body: JSON.stringify(payload)
                                })
                                    .then(response => response.json())
                                    .then(data => {
                                        container.innerHTML = `        
                                <div id="to_almox_button" class="to_almox" ${["192.168.7.58", "192.168.7.94", "127.0.0.1"].includes(data[0].Message) ? "" : "style='display: none'"}>
                                    <label for="to_almox">Para o Almoxarifado</label>
                                    <input type="checkbox" id="to_almox" name="to_almox" value="to_almox" onchange="changeShipContainer(event)">
                                </div>
                                            
                                <form class="ship-container ship-almox" id="ship-almox" style="display: none">
                                    <h1 id="reception-insert-message">Preencha os campos abaixo!</h1>

                                    <input id="mail_code" name="code" type="text" placeholder="Codigo AR" required="">

                                    <select id="receiver_name" name="type" required="">
                                        <option value="kayro">Kayro</option>
                                        <option value="guilherme">Guilherme</option>
                                        <option value="gustavo">Gustavo</option>
                                        <option value="other">Outro(a)</option>
                                    </select>

                                    <select id="sender_name" name="type" required="">
                                        <option value="yara">Yara</option>
                                        <option value="lidia">Lidia</option>
                                        <option value="Michelle">Michelle</option>
                                        <option value="other">Outro(a)</option>
                                    </select>

                                    <button class="submit" onclick="receivedOnReception()" type="button" id="reception-submit">Enviar</button>
                                </form>

                                <div class="ship-container ship-mall" id="ship-mall">
                                    <input type="file" id="file_input" style="display: none">
                                    <div id="image-container" class="image-container">
                                        Clique para selecionar uma imagem!
                                    </div>
                                    <button class="submit" id="updateReceiver-button" onclick="updateReceiver()">Enviar</button>
                                </div>
                            `
                                    })
                            }
                        } else if (data[1] == 404 || data[1] == 409) {
                            document.getElementById("code_input").classList.add("not_found")

                            let errorMsg = document.getElementById("error_message")

                            if (errorMsg) {
                                errorMsg.innerText = data[0].Message
                            } else {
                                const h1 = document.createElement("h1")
                                h1.id = "error_message"
                                h1.innerHTML = data[0].Message
                                body.appendChild(h1)
                            }
                        } else {
                            document.querySelectorAll(".sc-body input").forEach(i => {
                                i.classList.add("not_found")
                            })

                            let errorMsg = document.getElementById("error_message")

                            if (errorMsg) {
                                errorMsg.innerText = data[0].Message
                            } else {
                                const h1 = document.createElement("h1")
                                h1.id = "error_message"
                                h1.innerHTML = data[0].Message
                                body.appendChild(h1)
                            }
                        }
                    })
            })
        });
}

let actual_focus = "insert-container"

function focuses(container) {
    document.querySelectorAll(".container").forEach(container => {
        container.style.display = "none";
    });
    document.getElementById(container).style.display = "grid";
    actual_focus = String(container)

    if (container == "ship-container") {
        fetch("/user-ip", {
            method: "GET",
            headers: {
                "Content-Type": "application/json"
            }
        })
            .then(response => response.json())
            .then(data => {
                if (["192.168.7.58", "192.168.7.94", "127.0.0.1"].includes(data[0].Message) && !document.getElementById("to_almox_button")) {
                    document.getElementById(container).insertAdjacentHTML('afterbegin', `
                <div id="to_almox_button" class="to_almox">
                    <label for="to_almox">Para o Almoxarifado</label>
                    <input type="checkbox" id="to_almox" name="to_almox" value="to_almox" onchange="changeShipContainer(event)">
                </div>
            `)
                }

                if (["192.168.7.58"].includes(data[0].Message)) {
                    document.getElementById("to_almox").click()
                }

            })

        const img_container = document.getElementById("image-container")

        const file_input = document.getElementById("file_input")

        img_container.addEventListener("click", () => {
            if (!img_container.classList.contains("pp-small")) {
                file_input.click()
            }
        })

        file_input.addEventListener("change", () => {
            const file = file_input.files[0]
            if (file) {
                img_container.innerHTML = `
                    <img id="picture-preview" class="picture-preview" src="${URL.createObjectURL(file)}" alt="image">
                `
            }
        })

        const ship_mall = document.getElementById("ship-mall")

        ship_mall.addEventListener("drop", (e) => {
            ship_mall.classList.remove("dragover");
            e.preventDefault();

            const files = e.dataTransfer.files;
            file_input.files = files;

            img_container.innerHTML = `
                <img id="picture-preview" class="picture-preview" src="${URL.createObjectURL(file_input.files[0])}" alt="image">
            `
        });

        ship_mall.addEventListener("dragover", (e) => {
            ship_mall.classList.add("dragover");
            e.preventDefault();
        })


        ship_mall.addEventListener("dragleave", () => {
            ship_mall.classList.remove("dragover");
        });
    }
}

function register() {
    const form = document.getElementById("insert-container");

    if (!form.reportValidity()) {
        return;
    }

    const code = document.getElementById("ar_code")
    const name = document.getElementById("mail_name")
    const fantasy = document.getElementById("mail_fantasy")
    const type = document.getElementById("mail_type")
    const priority = document.getElementById("mail_priority")

    const payload = {
        code: code.value,
        name: name.value,
        fantasy: fantasy.value,
        type: type.value,
        status: "on_reception",
        priority: priority.value
    };

    fetch("/mails/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {

            document.getElementById("insert-message").innerHTML = data[0].Message;
            switch (data[1]) {
                case 200:
                    code.value = ""
                    name.value = ""
                    fantasy.value = ""
                    break
                case 400:
                case 409:
                    code.classList.add("not_found")
                    break
                default:
                    document.getElementById("insert-message").innerHTML = "Occorreu um erro não esperado!"
            }

        })


    // if (response.status === 200) {
    //     setTimeout(() => location.reload(), 900);
    // }
}

function receivedOnReception() {
    const form = document.getElementById("ship-almox");

    if (!form.reportValidity()) {
        return;
    }

    const code = document.getElementById("mail_code")
    const receiver = document.getElementById("receiver_name")
    const sender = document.getElementById("sender_name")

    const payload = {
        code: code.value,
        receiver: receiver.value,
        sender: sender.value
    };

    fetch("/mails/update-reception-received", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
        .then(response => response.json())
        .then(data => {
            messageh1 = document.getElementById("reception-insert-message")
            messageh1.innerHTML = data[0].Message;

            switch (data[1]) {
                case 200:
                    code.value = ""
                    break
                case 404:
                case 422:
                    code.classList.add("not_found")
                    break
                case 409:
                    code.classList.add("not_found")
                    messageh1.innerHTML += `
                    <br>
                    <br>
                    ${data[0].Values[0]}
                    <br>
                    ${data[0].Values[1]}
                    <br>
                    ${data[0].Values[2]}
                `
                    break
                default:
                    document.getElementById("reception-insert-message").innerHTML = "Occorreu um erro não esperado!"
            }
        })
}


document.addEventListener("keydown", function (event) {
    if (event.key == " " && event.target.id == "ar_code") {
        event.preventDefault();
    }

    if ((event.target.id == "code_input" || event.target.id == "ar_code" || event.target.id == "mail_code" || event.target.id == "data_input" || event.target.id == "user_input") && "not_found" == event.target.classList[0]) {
        event.target.classList.remove("not_found")

        if (actual_focus === "ship-container") {
            errorh1 = document.getElementById("error_message")

            if (errorh1) {
                errorh1.innerText = ""
            } else {
                document.getElementById("reception-insert-message").innerText = "Preencha os campos abaixo!"
            }

        } else if (actual_focus === "insert-container") {
            document.getElementById("insert-message").innerText = "Preencha os campos abaixo!"
        } else if (actual_focus === "reception-container") {
            document.getElementById("reception-insert-message").innerText = "Preencha os campos abaixo!"
        }
    }

    function openSelect(el) {
        if (!el) return;
        if (typeof el.showPicker === "function") {
            try {
                el.focus();
                el.showPicker();
                return;
            } catch (e) {
                // continua para fallback
            }
        }

        try {
            el.focus();
            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
            el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
        } catch (e) {
            console.warn("openSelect fallback falhou:", e);
        }
    }

    if (event.key === 'Tab' || event.key === 'Enter') { event.preventDefault(); }

    if ((event.key === 'Enter' || event.key === "Tab") && actual_focus === "insert-container") {
        const inputs = ["ar_code", "mail_name", "mail_fantasy", "mail_type", "mail_priority", "submit"];

        const activeElement = document.activeElement;
        const currentIndex = inputs.indexOf(activeElement.id);

        const nextIndex = (currentIndex + 1) % inputs.length;
        const prevIndex = (currentIndex - 1 + inputs.length) % inputs.length; // evita negativo

        if (event.shiftKey) {
            const target = document.getElementById(inputs[prevIndex]);
            if (prevIndex <= 2) {
                target && target.select();
            } else if (prevIndex === 3 || prevIndex === 4) {
                openSelect(target);
            } else {
                target && target.focus();
            }
            return;
        }

        const target = document.getElementById(inputs[nextIndex]);
        if (nextIndex <= 2) {
            target && (target.focus(), target.select());
        } else if (nextIndex === 3 || nextIndex === 4) {
            openSelect(target);
        } else if (nextIndex === 5) {
            target && target.focus();
        }

        if (
            (currentIndex == 5 && event.key === 'Enter') ||
            ((currentIndex == 3 || currentIndex == 4) &&
                (event.key === 'Enter' || event.key === 'Tab'))
        ) {
            document.getElementById(inputs[currentIndex])?.click();
        }
    } else if (actual_focus === "db-container") {
        const inputs = ["search_input", "search_button"];

        const activeElement = document.activeElement;
        const currentIndex = inputs.indexOf(activeElement.id);

        const nextIndex = (currentIndex + 1) % inputs.length;

        if (currentIndex == 0 && event.key === 'Enter') {
            document.getElementById(inputs[nextIndex])?.click();
            setTimeout(() =>
                document.getElementById(inputs[currentIndex]).focus()
                , 200)
        }
        // } else if(currentIndex != 0) {
        //     document.getElementById(inputs[0]).focus()
        // }
    } else if ((event.key === 'Enter') && (document.getElementById("to_almox") ? document.getElementById("to_almox").checked : false) && actual_focus === "ship-container") {
        // const inputs = ["mail_code", "receiver_name", "sender_name", "reception-submit"];

        // const activeElement = document.activeElement;
        // const currentIndex = inputs.indexOf(activeElement.id);

        // const nextIndex = (currentIndex + 1) % inputs.length;
        // const prevIndex = (currentIndex - 1 + inputs.length) % inputs.length;

        // if (event.shiftKey) {
        //     const target = document.getElementById(inputs[prevIndex]);
        //     if (prevIndex <= 0) {
        //         target && target.select();
        //     } else if (prevIndex === 1 || prevIndex === 2) {
        //         openSelect(target);
        //     } else {
        //         target && target.focus();
        //     }
        //     return;
        // }

        // const target = document.getElementById(inputs[nextIndex]);
        // if (nextIndex === 0) {
        //     target && target.select();
        // } else if (nextIndex === 2 || nextIndex === 1) {
        //     openSelect(target);
        // } else {
        //     target && target.focus();
        // }

        // if (currentIndex == 3 && event.key === 'Enter') {
        document.getElementById('reception-submit')?.click();
        // }
    } else if (actual_focus === "return-container") {
        const activeElement = document.activeElement

        if (event.key === 'Enter' && activeElement.id === 'return_input' && !activeElement.value == "") {
            addReturn(activeElement)
        } else if (activeElement.id == 'return_input' && document.getElementById("return_input").classList.contains('not_found')) {
            document.getElementById("return_input").classList.remove("not_found")
            document.getElementById("return-message").innerText = "Escaneie o codigo da correspondencia!"
        }
    }
});