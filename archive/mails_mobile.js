async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: { exact: "environment" }
            },
            audio: false
        });

        const video = document.getElementById("camera");
        video.srcObject = stream;
    } catch (err) {
        console.error("Erro ao acessar a câmera:", err);
        alert("Não foi possível acessar a câmera");
    }
}

startCamera();

function capture() {
    const video = document.getElementById("camera");
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    canvas.width = video.videoWidth - 120;
    canvas.height = video.videoHeight - 160;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const container = document.getElementById("camera-container")

    container.innerHTML = ``

    const img = document.createElement("img");
    img.id = "photo"
    img.alt = "preview"
    img.src = canvas.toDataURL("image/jpeg", 1);

    container.appendChild(img)

    const footer = document.querySelector("footer")

    footer.innerHTML = ``

    const resetBtn = document.createElement("button")
    resetBtn.classList.add("resetBtn")
    resetBtn.innerText = "Tirar Outra"
    footer.appendChild(resetBtn)

    const sendBtn = document.createElement("button")
    sendBtn.classList.add("sendBtn")
    sendBtn.innerText = "Enviar"
    footer.appendChild(sendBtn)

    resetBtn.addEventListener("click", () => {
        container.innerHTML = `
            <video id="camera" autoplay playsinline></video>
            <canvas id="canvas" hidden></canvas>
        `
        footer.innerHTML = `<button id="captureBtn" onclick="capture()"></button>`

        startCamera();
    })

    sendBtn.addEventListener("click", () => {
        sendBtn.disabled = true
        resetBtn.disabled = true

        img.style = "filter: brightness(0.4);"
        container.classList.add("loading")

        canvas.toBlob(blob => {
            const formData = new FormData();
            formData.append("file", blob, "foto.jpg");

            fetch("/mails/upload_file", {
                method: "POST",
                body: formData
            })
                .then(response => response.json())
                .then(json => {
                    if (json[1] !== 200) {
                        alert("ERROR")
                    }

                    img.style = "filter: brightness(1);"

                    json = json[0].Message

                    container.classList.remove("loading")
                    container.style = "height: 50vh;"

                    const main = document.querySelector("main")
                    main.style = "grid-template-rows: 30em 6em;"

                    footer.innerHTML = ``

                    const regexCodigo = /([A-Z]{2}\d{9}[A-Z]{2})/;
                    const codigoMatch = json[0].replaceAll(" ", "").toUpperCase().match(regexCodigo);
                    const codigo = codigoMatch ? codigoMatch[1] : null;

                    const code_input = document.createElement("input")
                    const user_input = document.createElement("input")

                    const submit = document.createElement("button")

                    submit.type = "submit"
                    submit.classList.add("submit")
                    submit.innerHTML = "Registrar"

                    user_input.value = json[1][0] ? json[1][0] : ""
                    user_input.id = "user_input"
                    user_input.placeholder = "Nome Recebedor"

                    code_input.value = codigo
                    code_input.id = "code_input"
                    code_input.placeholder = "codigo AR"

                    footer.appendChild(code_input)
                    footer.appendChild(user_input)

                    footer.appendChild(submit)

                    submit.addEventListener("click", () => {
                        var today = new Date();

                        let payload = {
                            type: "shipment",
                            date: `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`,
                            code: code_input.value,
                            user: user_input.value
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
                                    alert("Registrado com Sucesso!")
                                    location.href = location.pathname + '?reload=' + Date.now();
                                } else if (data[1] == 404 || data[1] == 409) {
                                    document.getElementById("code_input").classList.add("not_found")
                                    alert(data[0].Message)
                                } else {
                                    document.querySelectorAll("footer input").forEach(i => {
                                        i.classList.add("not_found")
                                    })
                                    alert(data[0].Message)
                                }
                            })
                    })
                })
        }, "image/jpeg", 0.9);
    })

}

document.addEventListener("keydown", function (event) {
    if ("not_found" == event.target.classList[0]) {
        event.target.classList.remove("not_found")
    }
})