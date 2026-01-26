socket = io();

window.onload = function () {

    document.addEventListener("click", function () {
        document.getElementById("code-input").focus();
    });
    
    document.addEventListener("keydown", function(e) {
        const code_input = document.getElementById("code-input");
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

                        msgBox.classList.add("success");
                        msgBox.innerText = "Registro realizado com sucesso!";
                        
                        code_input.hidden = true;
                        code_input.disabled = true;
                        
                        const imgBox = document.createElement("div");
                        
                        document.querySelector("main").appendChild(imgBox)

                        const img = document.createElement("img");
                        const svg = document.createElement("img");
                        const msg = document.createElement("p");

                        msg.innerText = `${data.movement[6].replace(/\b\w/g, c => c.toUpperCase())} de ${data.item[2].toLowerCase().replace(/\b\w/g, c => c.toUpperCase())}`;
                        msg.classList.add("img-msg");

                        svg.src = `/static/imgs/tools-loan/${(data.item[2]).toLowerCase().replaceAll(" ", "-").replaceAll("'", "").replaceAll('"', "")}.png`;
                        svg.alt = `${data.item[2]}`;
                        svg.classList.add("icon");

                        img.src = `/pictures/loans/${data.movement[4]}/${data.movement[3]}/${String(data.movement[0]).padStart(6, '0')}.jpg`;
                        img.alt = `${data.item[2]}`;
                        img.classList.add("picture");

                        imgBox.appendChild(svg);
                        imgBox.appendChild(msg);
                        imgBox.appendChild(img);

                        setTimeout(() => {

                            img.classList.add("fade-out");

                            setTimeout(() => {
                                svg.classList.add("fade-out");
                            }, 100);

                            socket.emit("update_pictures");
                            
                            setTimeout(() => {
                                msgBox.innerText = "Escaneie o codigo ou digite o nome da ferramenta.";
                                msgBox.classList.remove("success");
                                imgBox.remove()
                                
                                code_input.hidden = false;
                                code_input.disabled = false;
                                code_input.value = "";
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