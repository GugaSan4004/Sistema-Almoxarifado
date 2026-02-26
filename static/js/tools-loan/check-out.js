socket = io();

window.onload = function () {
    let code_input = document.getElementById("code-input")
    document.addEventListener("click", function () {
        code_input.focus();
    });

    document.addEventListener("keydown", function (e) {
        code_input.focus();

        if (e.key === "Enter") {
            const code = e.target.value;

            if (code.trim() !== "") {
                fetch("/tools-loan/add-tool", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ code: code })
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data[1] != 200) {
                            code_input.classList.add("error");
                            setTimeout(() => {
                                code_input.value = ""
                            }, 700)
                            setTimeout(() => {
                                code_input.classList.remove("error");
                            }, 1300);
                        } else {
                            data = data[0]
                            const msgBox = document.getElementById("message-box");

                            msgBox.classList.add("text-green-400");
                            msgBox.innerText = "Registro realizado com sucesso!";

                            code_input.value = "";

                            const imgBox = document.createElement("div");
                            imgBox.classList.add("grid", "place-items-center", "col-span-46", "row-start-8", "col-start-14", "col-end-34", "h-max", "bg-default-blue")
                            document.querySelector("main").appendChild(imgBox)

                            const img = document.createElement("img");
                            const svg = document.createElement("img");
                            const msg = document.createElement("p");

                            msg.innerText = `${data.movement[6].replace(/\b\w/g, c => c.toUpperCase())} de ${data.item[2].toLowerCase().replace(/\b\w/g, c => c.toUpperCase())}`;

                            msg.classList.add("text-3xl", "mb-3", "mt-2")

                            svg.src = `/static/imgs/tools-loan/${(data.item[2]).toLowerCase().replaceAll(" ", "-").replaceAll("'", "").replaceAll('"', "")}.png`;
                            svg.alt = `${data.item[2]}`;
                            svg.classList.add("bg-white", "h-18", "rounded-md", "border-3", "border-black", "p-1");

                            img.src = `/pictures/loans/${data.movement[4]}/${data.movement[3]}/${String(data.movement[0]).padStart(6, '0')}.jpg`;
                            img.alt = `${data.item[2]}`;
                            img.classList.add("h-64", "bg-white", "text-black", "border-3", "border-black", "rounded-md");

                            imgBox.appendChild(svg);
                            imgBox.appendChild(msg);
                            imgBox.appendChild(img);

                            setTimeout(() => {
                                img.classList.add("animate-slide-out");

                                setTimeout(() => {
                                    svg.classList.add("animate-slide-out");
                                }, 100);

                                socket.emit("update_pictures");

                                setTimeout(() => {
                                    msgBox.innerText = "Escaneie o codigo ou digite o nome da ferramenta.";
                                    msgBox.classList.remove("text-green-400");
                                    imgBox.remove()
                                }, 1400);
                            }, 4000);
                        }
                    })
                    .catch(error => {
                        console.error("Fetch error:", error);
                    });
            }
        }
    });
};