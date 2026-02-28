import re
import os
import sys
import shutil
import psutil
import datetime

current_pid = sys.argv[0]
for process in psutil.process_iter(['pid', 'cmdline']):
    if process.info['cmdline'] and current_pid in ' '.join(process.info['cmdline']) and process.info['pid'] != psutil.Process().pid:
        try:
            process.terminate()
            process.wait(timeout=5)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            process.kill()

from PIL import Image
from flask_socketio import SocketIO
from static.py.screen import screen
from static.py.cam_service import camera
from static.py import imareocr, return_generator, sqlite_core
from flask import Flask, abort, request, jsonify, render_template, send_from_directory
# from static.py.clock import control



# ################################ #
#      Initializing Essencial      #
#             Modules              #
# ################################ # 


FOLDER = r"C:\Users\GUGA4\Documents\Projects\Sistema Almoxarifado\Sistema-Almoxarifado"
# FOLDER = r"\\192.168.7.252\dados\OPERACOES\13-ALMOXARIFADO\0 - Sistema Almox"

sqlite = sqlite_core.init(FOLDER)

tools_db = sqlite_core.init.tools(sqlite)
mails_db = sqlite_core.init.mails(sqlite)

# imgReader = imareocr.init()
returnGen = return_generator.init(FOLDER)

app = Flask(__name__)

app.config["ENV"] = "production"
app.config["DEBUG"] = False

Socket = SocketIO(
    app,
    async_mode="eventlet",
    ping_interval=25,
    ping_timeout=60,
    cors_allowed_origins="*"
)



# ################################ #
#          Setting Global          #
#            Variables             #
# ################################ # 



lastImage = ""

meses = {
    "01": "jan",
    "02": "fev",
    "03": "mar",
    "04": "abr",
    "05": "mai",
    "06": "jun",
    "07": "jul",
    "08": "ago",
    "09": "set",
    "10": "out",
    "11": "nov",
    "12": "dez"
}



# ################################ #
#          Defining Main           #
#              Routes              #
# ################################ # 



with app.app_context():
    print("> Server initiated successfully!")


@app.before_request
def firewall():
    data = request.get_data(as_text=True)

    if len(data) > 10_000_000:
        abort(413)
        
    if request.remote_addr not in ["192.168.7.94", "127.0.0.1", "192.168.7.58", "192.168.7.119", "192.168.7.2"] and "mobile" not in str(request.headers.get("User-Agent")).lower():
        abort(403)

@app.route("/")
def fallback():
    if "mobile" in str(request.headers.get("User-Agent")).lower():
        return render_template("mails/mails_mobile.html")
    return render_template("mails/mails.html")

@app.route("/tools-loan/list")
def tools_list():
    res = tools_db.getTools()
    
    result = []
    
    if res:
        for r in res:
            result.append([r[2], r[3]])
            
    return [{"nome": d[0], "status": d[1]} for d in result]

@app.route("/tools-loan/")
@app.route("/tools-loan/<subpath>")
def tool_loans(subpath = None):
    if subpath is None or subpath != "registers":
        return render_template("tools-loan/check-out.html")
    else:  
        return render_template("tools-loan/registers.html")

@app.route("/mails")
def mails():
    return render_template("mails/mails.html")

@app.route("/dev")
def newmails():
    return render_template("mails/new_mails.html")

@app.route("/user-ip", methods=["GET"])
def getIp():
    return jsonify({
        "Message": request.remote_addr
    }, 200)

@app.route("/pictures/<path:filename>")
def picture(filename):
    return send_from_directory(FOLDER + r"\pictures", filename)



# ################################ #
#          Routes to the           #
#          Tools-loan Tab          #
# ################################ # 



@app.route("/tools-loan/add-tool", methods=["POST"])
def add_tool():
    data = request.json
    
    if not data:
        sqlite.log_edit(
            route="/tools-loan/add-tool",
            method="[POST]",
            value_id=None,
            code=400,
            message="Invalid Code",
            fields_changed=None,
            list_values=data,
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Error: Nenhum valor foi passado!"
        }, 400)

    if not (item := tools_db.searchTools(data.get("code"))):
        sqlite.log_edit(
            route="/tools-loan/add-tool",
            method="[POST]",
            value_id=None,
            code=404,
            message="Code not found",
            fields_changed=None,
            list_values=data,
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Error: Código não encontrado!"
        }, 404)

    movement_type = "saida" if item[3].lower() == "disponivel" else "entrada"

    status = "Emprestado" if item[3].lower() == "disponivel" else "Disponivel"
    
    movements_count = tools_db.getMovementsCount()
    
    photo = camera.capture(str(movements_count).zfill(6))
        
    try:
        tools_db.updateTools(item[0], "status", status)
        
        movement = tools_db.addMovement(
            movements_count, 
            item[0], 
            photo["day"], 
            photo["month"], 
            photo["year"], 
            photo["time"], 
            movement_type
        )
        
        tools_db.updateTools(item[0], "id_movements", movement[0])
    except Exception as e:
        sqlite.log_edit(
            route="/tools-loan/add-tool",
            method="[POST]",
            value_id=item[0],
            code=500,
            message=e,
            fields_changed=None,
            list_values=data,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Erro inesperado!"
        }, 500)
    else:
        sqlite.log_edit(
            route="/tools-loan/add-tool",
            method="[POST]",
            value_id=item[0],
            code=200,
            message="OK",
            fields_changed='{"tools": "status", "tools_movements": "new", "tools": "id_movements"}',
            list_values='{"status": "' + status + '", "new": "' + str(movement[0]) + '", "id_movements": "' + str(movement[0]) + '"}',
            ip=request.remote_addr
        )
        
        return jsonify({
            "item": item, 
            "movement": movement,
            "photo": photo
        }, 200)

@app.route("/tools-loan/get-registers", methods=["GET"])
def get_registers():
    
    return jsonify({
        "loaned_tools": tools_db.getAllLoanedItems(),
        "all_movements": tools_db.getAllMovements(),
        "all_tools": tools_db.getTools()
    }, 200)
    
    
@app.route("/tools-loan/registers/missing", methods=["POST"])
def missing():
    data = request.json
    
    if data:
        tools_db.setToolMissing(data.get("code"))
        sqlite.log_edit(
            route="/tools-loan/registers/missing",
            method="[POST]",
            value_id=None,
            code=200,
            message="OK",
            fields_changed='{"tools": "id_movements"}',
            list_values='{"id_movements": "NULL"}',
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Ok"
        }, 200)
    else:
        sqlite.log_edit(
            route="/tools-loan/registers/missing",
            method="[POST]",
            value_id=None,
            code=400,
            message="Invalid Values",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Valores invalidos!"
        }, 400)

@app.route("/tools-loan/registers/casualty", methods=["POST"])
def casualty():
    data = request.json
    
    if data:
        tools_db.setToolCasualty(data.get("code"))
        sqlite.log_edit(
            route="/tools-loan/registers/casualty",
            method="[POST]",
            value_id=None,
            code=200,
            message="OK",
            fields_changed='{"tools": "id_movements"}',
            list_values='{"id_movements": "NULL"}',
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Ok"
        }, 200)
    else:
        sqlite.log_edit(
            route="/tools-loan/registers/casualty",
            method="[POST]",
            value_id=None,
            code=400,
            message="Invalid Values",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        return jsonify({
            "Message": "Valores invalidos!"
        }, 400)



# ################################ #
#          Routes to the           #
#            mails Tab             # 
# ################################ # 



@app.route("/mails/get-mails", methods=["POST"])
def get_mails():
    data = request.get_json()

    return jsonify({
        "mails": mails_db.getMails(data[0], data[1], data[2]),
        "totals": mails_db.getTotals()
    }, 200)

@app.route("/mails/upload_file", methods=["POST"])
def upload_file():
    try:
        if "file" not in request.files:
            sqlite.log_edit(
                route="/mails/upload_file",
                method="[POST]",
                value_id=None,
                code=400,
                message="Invalid Values",
                fields_changed=None,
                list_values=None,
                ip=request.remote_addr
            )
            return jsonify({
                "Message": "Error: Nenhum arquivo enviado!"
            }, 400)
        
        file = request.files["file"]
    
        tmp_path = FOLDER + r"\pictures\mails\temp_image.jpg"

        file.save(tmp_path)
        
        try:
            Image.open(file.stream).verify()
        except:
            sqlite.log_edit(
                route="/mails/upload_file",
                method="[POST]",
                value_id=None,
                code=400,
                message="Invalid Values",
                fields_changed=None,
                list_values=None,
                ip=request.remote_addr
            )

            return jsonify({
                "Message": "Error: Tipo de arquivo invalido!"
            }, 400)
        
        global lastImage

        lastImage = tmp_path
        extract= imgReader.extractInfo(tmp_path)
        
        sqlite.log_edit(
            route="/mails/upload_file",
            method="[POST]",
            value_id=None,
            code=200,
            message="OK",
            fields_changed='{"global": "lastImage"}',
            list_values='{"lastImage": "' + lastImage + '", "extract": "' + str(extract) + '"}',
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": extract
        }, 200)
    except Exception as e:
        sqlite.log_edit(
            route="/mails/upload_file",
            method="[POST]",
            value_id=None,
            code=500,
            message=e,
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        return jsonify(":("), 500
    
@app.route("/mails/update", methods=["POST"])
def update():
    data = request.get_json()

    mail_type = data.get("type")
    date = data.get("date")
    
    if not date:
        sqlite.log_edit(
            route="/mails/update",
            method="[POST]",
            value_id=None,
            code=400,
            message="Invalid date Value",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "data inválida"
        }, 400)

    if mail_type == "return":
        items = data.get("items", [])

        if not items:
            sqlite.log_edit(
                route="/mails/update",
                method="[POST]",
                value_id=None,
                code=400,
                message="Invalid Values",
                fields_changed=None,
                list_values=None,
                ip=request.remote_addr
            )
            return jsonify({
                "Message": "Nenhuma devolução informada"
            }, 400)

        inserted = []

        for item in items:
            code = item.get("code")
            motivo = item.get("motivo")

            if not code:
                continue

            infos = mails_db.getMails(code, "id", "ASC")
            
            if not infos:
                continue
            
            infos = infos[0]
            
            if infos[13]:
                return jsonify({
                    "Message": "Correspondencia já devolvida detectada!"
                }, 400)

            pname = (
                str(infos[4][:3].upper()) +
                str(infos[2][-5:]) +
                str(infos[0])
            )

            dest_path = FOLDER + r"\pictures\mails\\" + pname + ".jpg"

            shutil.copy(lastImage, dest_path)
            
            mails_db.updatePicture(
                motivo,
                date,
                pname,
                code,
                "returned"
            )

            inserted.append(code)

            sqlite.log_edit(
                route="/mails/update",
                method="[POST]",
                value_id=item.get("code"),
                code=200,
                message="OK",
                fields_changed='{"mails": ["receive_name", "receive_date", "photo_id", "status"]}',
                list_values='{"receive_name": "' + motivo + '", "receive_date": "' + date + '", "photo_id": "' + pname + '", "status": "' + code + '"}',
                ip=request.remote_addr
            )
        
        if os.path.exists(lastImage):
            os.remove(lastImage)

        return jsonify({
            "Message": "Devoluções registradas",
            "type": "returns"
        }, 200)
    
    code = data.get("code")
    user = data.get("user")

    if (not code or not re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper())) or not user:
        sqlite.log_edit(
            route="/mails/update",
            method="[POST]",
            value_id=None,
            code=400,
            message="Invalid Values",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Codigo ou Recebedor invalido!"
        }, 400)

    infos = mails_db.getMails(code, "id", "ASC")
    
    if not infos:
        sqlite.log_edit(
            route="/mails/update",
            method="[POST]",
            value_id=None,
            code=404,
            message="Mail not found",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Correspondência não encontrada"
        }, 404)
        
    elif infos[0][9].lower() == "shipped":
        sqlite.log_edit(
            route="/mails/update",
            method="[POST]",
            value_id=None,
            code=409,
            message="Mail already shipped",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Correspondência já consta como entregue!"
        }, 409)

    infos = infos[0]

    pname = (
        str(infos[4][:3].upper()) +
        str(infos[2][-5:]) +
        str(infos[0])
    )

    dest_path = FOLDER + r"\pictures\mails\\" + pname + ".jpg"
    
    shutil.move(lastImage, dest_path)

    mails_db.updatePicture(user, date, pname, code, "shipped")

    sqlite.log_edit(
        route="/mails/update",
        method="[POST]",
        value_id=code,
        code=200,
        message="OK",
        fields_changed='{"mails": ["receive_name", "receive_date", "photo_id", "status"]}',
        list_values='{"receive_name": "' + user + '", "receive_date": "' + date + '", "photo_id": "' + pname + '", "status": "' + code + '"}',
        ip=request.remote_addr
    )
    
    return jsonify({
        "Message": "Entrega registrada",
        "PictureName": pname
    }, 200)

@app.route("/mails/register", methods=["POST"])
def register():
    data = request.get_json()

    code = data["code"]
    name = data["name"]
    fantasy = data["fantasy"]
    type_ = data["type"]
    status = data["status"]
    priority = data["priority"]
    
    if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
        if "unique constraint failed" in str(mails_db.register(str(name), str(code), str(fantasy), str(type_), str(priority), str(status))).lower():
            sqlite.log_edit(
                route="/mails/register",
                method="[POST]",
                value_id=code,
                code=409,
                message="unique constraint failed",
                fields_changed=None,
                list_values=None,
                ip=request.remote_addr
            )

            return jsonify({
                "Message": "Essa correspondencia ja está cadastrada!"
            }, 409)
        else:
            sqlite.log_edit(
                route="/mails/register",
                method="[POST]",
                value_id=code,
                code=200,
                message="OK",
                fields_changed='{"mails": ["name", "code", "fantasy", "type", "priority", "status"]}',
                list_values=(
                    '{"name": "' + str(name) +
                    '", "code": "' + str(code) +
                    '", "fantasy": "' + str(fantasy) +
                    '", "type": "' + str(type_) +
                    '", "priority": "' + str(priority) +
                    '", "status": "' + str(status) + '"}'
                ),
                ip=request.remote_addr
            )


            return jsonify({
                "Message": "Registro efetuado com Sucesso!"
            }, 200)
    else:
        sqlite.log_edit(
            route="/mails/register",
            method="[POST]",
            value_id=code,
            code=400,
            message="Invalid Values",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Código de rastreio invalido!"
        }, 400)

@app.route("/mails/update-reception-received", methods=["POST"])
def reception_received():
    data = request.get_json()

    code = data["code"]
    receiver = data["receiver"]
    sender = data["sender"]
    
    if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
        filteredMails = mails_db.getMails(str(code), 'id', "ASC")
        if filteredMails:
            filteredMails = filteredMails[0]
            if not filteredMails[6] or not filteredMails[7]:
                mails_db.updateReceiver(str(code), str(receiver), str(sender))

                sqlite.log_edit(
                    route="/mails/update-reception-received",
                    method="[POST]",
                    value_id=code,
                    code=200,
                    message="OK",
                    fields_changed='{"mails": ["ReceivedOnReceptionBy", "SendedOnReceptionBy", "LeaveReceptionAt", "status"]}',
                    list_values=(
                        '{"ReceivedOnReceptionBy": "' + str(receiver) +
                        '", "SendedOnReceptionBy": "' + str(sender) +
                        '", "LeaveReceptionAt": "' + datetime.datetime.now().strftime("%d-%m-%Y %H:%M") +
                        '", "status": "almox"}'
                    ),
                    ip=request.remote_addr
                )

                return jsonify({
                    "Message": "Status atualizado com sucesso!"
                }, 200)
            else:
                sqlite.log_edit(
                    route="/mails/update-reception-received",
                    method="[POST]",
                    value_id=code,
                    code=409,
                    message="mail already shipped",
                    fields_changed=None,
                    list_values=None,
                    ip=request.remote_addr
                )
                
                return jsonify({
                    "Message": "A correspondencia ja foi coletada!",
                    "Values": [f"Recebedor: {filteredMails[6].title()}" , f"Liberador: {filteredMails[7].title()}", f"Data: {filteredMails[8]}"]
                }, 409)
        else:
            sqlite.log_edit(
                route="/mails/update-reception-received",
                method="[POST]",
                value_id=code,
                code=404,
                message="mail not found",
                fields_changed=None,
                list_values=None,
                ip=request.remote_addr
            )
            
            return jsonify({
                "Message": "Correspondencia não encontrada!"
            }, 404)
    else:
        sqlite.log_edit(
            route="/mails/update-reception-received",
            method="[POST]",
            value_id=code,
            code=422,
            message="Invalid code format",
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Código de rastreio invalido!"
        }, 422)

@app.route("/mails/update-column", methods=["POST"])
def update_column():
    data = request.get_json()

    code = data.get("code")
    column = data.get("column")
    new_value = data.get("new_value")
    old_value = data.get("old_value")

    try:
        mails_db.update(str(code), str(new_value), str(column))


    except Exception as e:
        sqlite.log_edit(
            route="/mails/update-column",
            method="[POST]",
            value_id=code,
            code=500,
            message=e,
            fields_changed=None,
            list_values=None,
            ip=request.remote_addr
        )
        return jsonify({
            "Message": f"Erro não esperado!"
        }, 500)
    else:
        sqlite.log_edit(
            route="/mails/update-column",
            method="[POST]",
            value_id=code,
            code=200,
            message="OK",
            fields_changed='{"mails", "' + column +'"}',
            list_values='{"' + column + '", "' + old_value + ' -> ' + new_value + '",}',
            ip=request.remote_addr
        )
        
        return jsonify({
            "Message": "Nome atualizado com sucesso!"
        }, 200)

@app.route("/mails/generate-return", methods=["POST"])
def generate_return():
    data = request.get_json()

    file_path = returnGen.generate_return(
        data=data
    )
    
    for code in data:
        mails_db.update(
            code=code,
            value="returned",
            column="status"
        )

    return jsonify({
        "Message": file_path
    }, 200)



# ################################ #
#             SocketIO             #
#              Repass              #
# ################################ # 



@Socket.on("update_pictures")
def update_pictures():
    Socket.emit("update_pictures")



if __name__ == "__main__":
    Socket.run(
        app,
        host="0.0.0.0",
        port=80,
        debug=False
    )