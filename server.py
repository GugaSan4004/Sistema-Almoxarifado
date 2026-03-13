import ast

from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, abort, request, jsonify, render_template, send_from_directory, session, redirect, url_for, flash, make_response
from static.py import imageocr, return_generator, sqlite_core
from flask_socketio import SocketIO
from PIL import Image
from functools import wraps
from datetime import datetime

import re
import os
import sys
import json
import shutil
import psutil
import random
import string
import secrets

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

# from static.py.screen import screen
# from static.py.cam_service import camera
# from static.py.clock import control


# ################################ #
#      Initializing Essencial      #
#             Modules              #
# ################################ #


FOLDER = r"C:\Users\GUGA4\Documents\Projects\Sistema Almoxarifado\Sistema-Almoxarifado"
# FOLDER = r"\\192.168.7.252\dados\OPERACOES\13-ALMOXARIFADO\0 - Sistema Almox"

sqlite = sqlite_core.init(FOLDER)

mails_db = sqlite_core.init.mails(sqlite)
users_db = sqlite_core.init.users(sqlite)

imgReader = imageocr.init()
returnGen = return_generator.init(FOLDER)


app = Flask(__name__)
new_secret_key = secrets.token_urlsafe(32)
app.secret_key = new_secret_key

print(f"Secret key for this section -> {new_secret_key}")

app.config["ENV"] = "production"
app.config["DEBUG"] = False

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

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


# lastImage = ""

# meses = {
#     "01": "jan",
#     "02": "fev",
#     "03": "mar",
#     "04": "abr",
#     "05": "mai",
#     "06": "jun",
#     "07": "jul",
#     "08": "ago",
#     "09": "set",
#     "10": "out",
#     "11": "nov",
#     "12": "dez"
# }


# ################################ #
#        Defining Security         #
#              Routes              #
# ################################ #

with app.app_context():
    print("> Server initiated successfully!")


@app.before_request
def firewall():
    data = request.get_data(as_text=True)

    if len(data) > 10_000_000:
        abort(413)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('initial'))
        return f(*args, **kwargs)
    return decorated_function


def roles_required(allowed_roles: list):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            allowed_roles.append("admin")

            user = users_db.getUserData(session.get('user_id'))

            if session.get('user_role') not in allowed_roles or user[3] not in allowed_roles:
                return redirect(url_for('initial'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.errorhandler(404)
def page_not_found():
    return redirect(url_for('mails'))


@app.route("/")
def initial():
    try:
        has_first_login_cookie = request.cookies.get('first_login')

        if not has_first_login_cookie and (session.get('user_id') or session.get('user_role')):
            session.clear()
    except Exception:
        pass

    return render_template("initial/login.html")


@app.route("/api/set-userpass", methods=["POST"])
@login_required
def set_password():
    data = request.form
    password = generate_password_hash(data["password"])

    try:
        users_db.changePassword(
            password, session.get('user_id'), session.get('user_name'))
        return redirect(url_for('mails'))
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/initial/login", methods=["POST"])
def login():
    data = request.form
    username = data["username"]

    user = users_db.getUserData(username)

    if not user:
        flash("Usuário não encontrado!", "danger")
        return redirect(url_for('initial'))

    if user[4] == 1:
        response = make_response(redirect(url_for('initial')))

        session.permanent = False
        session['user_id'] = user[0]
        session['user_name'] = user[1]
        session['user_role'] = user[3]

        response.set_cookie('first_login', 'true', max_age=30)
        return response

    elif not check_password_hash(user[2], data["password"]):
        flash("Senha incorreta!", "warning")
        return redirect(url_for('initial'))

    session.permanent = False
    session['user_id'] = user[0]
    session['user_name'] = user[1]
    session['user_role'] = user[3]

    return redirect(url_for('mails'))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('initial'))


@app.route("/mails")
@login_required
def mails():
    user_role = session.get('user_role')
    allowed_tabs = users_db.getAllowedTabs(user_role)
    forms_id = [
        'register-mail',
        'register-user',
        'register-pickup',
        'get-mail',
        'generate-return',
        'extract-image'
    ]

    return render_template("mails/mails.html", allowed_tabs=allowed_tabs, forms_id=forms_id)


@app.route("/pictures/<path:filename>")
def picture(filename):
    return send_from_directory(FOLDER + r"\pictures", filename)


@app.route("/api/render-body/<tab_id>", methods=["POST"])
@login_required
def render_body(tab_id):
    data = request.get_json()
    role = session.get("user_role")

    try:
        tabs_list = []
        if tabs := users_db.getAllowedTabs(role):
            for tab in tabs:
                tabs_list.append(tab.get("id"))
        else:
            raise Exception("Permissão negada!")

        if tab_id in tabs_list:
            def is_delayed(entry_date_str: str, priority: str):
                if not entry_date_str:
                    return False
                try:
                    entry_date = datetime.strptime(
                        entry_date_str, "%Y-%m-%d %H:%M")
                    now = datetime.now()

                    diff = now - entry_date
                    hours_passed = diff.total_seconds() / 3600

                    thresholds = {
                        "Simples": 120,
                        "Judicial": 72
                    }

                    limit = thresholds.get(priority, 48)

                    return hours_passed, limit
                except Exception:
                    return False

            def format_date(dateStr: str):
                if not dateStr:
                    return ""
                return "/".join(dateStr.split(' ')[0].split('-')[::-1])

            def get_priority_class(priority: str):
                color = "bg-red-500/30" if priority == "Judicial" else "bg-green-500/30"
                return f"{color} rounded-full px-2 font-semibold pb-0.5"

            values = {
                "totals": mails_db.getTotals(),
                "mails": mails_db.getMails(data[0], data[1], data[2]),
                "is_delayed": is_delayed,
                "format_date": format_date,
                "get_priority_class": get_priority_class,
                "filter": data[0],
                "actualOrder": data[1],
                "roles": users_db.getRoles(),
                "users": users_db.getUsernames()
            }

            
            if data[3]:
                values["pre_return_mails"] = mails_db.getMails(data[3])
            elif data[4]:
                values["exit"] = {
                    'values': ast.literal_eval(data[4]),
                    'mail': mails_db.getMails(ast.literal_eval(data[4])['ar_code'], fetchOne=True)
                }

            return render_template(f"tabs/{tab_id}.html", **values)
        else:
            raise Exception("Permissão negada!")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/api/register-user", methods=["POST"])
@roles_required
def users_register():
    data = request.form

    username = data["username"]
    role = data["role"]

    try:
        users_db.registerNewUser(username, role)
    except Exception as e:
        e = "Usuario já cadastrado!" if "unique constraint failed" in str(
            e).lower() else e
        return jsonify({
            "Message": f"{e}"
        }), 400
    else:
        return jsonify({
            "Message": "Cadastrado Com Sucesso!"
        }), 200


@app.route("/api/register-mail", methods=["POST"])
@roles_required(["receptionist"])
def mails_register():
    data = request.form

    code = data["code"]
    sender = data["sender"]
    fantasy = data["fantasy"] if data["fantasy"] else ""
    type_ = data["type"]
    priority = data["priority"]
    username = session.get('user_name')

    try:
        if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
            mails_db.registerNewMail(str(sender), str(code), str(
                fantasy), str(type_), str(priority), str(username))
        else:
            raise Exception("Codigo de rastreio invalido!")
    except Exception as e:
        e = "Correspondencia já cadastrada!" if "unique constraint failed" in str(
            e).lower() else e
        return jsonify({
            "Message": f"{e}"
        }), 400
    else:
        return jsonify({
            "Message": "Cadastrado Com Sucesso!"
        }), 200


@app.route("/api/register-pickup", methods=["POST"])
@roles_required(["receptionist"])
def pickup_register():
    data = request.form

    code = data["code"]
    pickupuser = data["user"]
    responsableuser = session.get('user_name')

    try:
        if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
            mails_db.registerPickup(code, pickupuser, responsableuser)
        else:
            raise Exception("Codigo de rastreio invalido!")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400
    else:
        return jsonify({
            "Message": "Registrado Com Sucesso!"
        }), 200


@app.route("/api/get-mail", methods=["POST"])
@roles_required(["assistant"])
def get_mail():
    data = request.form

    code = data["code"]
    try:
        if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
            mail = mails_db.getMails(data["code"], fetchOne=True)

            if not mail:
                raise Exception("Correspondencia não encontrada!")

            if mail[11] != "almox":
                raise Exception(
                    "Correspondencia não disponivel para devolução!")

            return jsonify({
                "Message": mail
            }), 201
        else:
            raise Exception("Codigo de rastreio invalido!")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/api/generate-return", methods=["POST"])
@roles_required(['assistant'])
def generate_return():
    data = request.form

    _dict = json.loads(data['mails'])

    return jsonify({
        "Message": returnGen.generate_return(_dict, session.get('user_name'))
    }), 202


@app.route("/api/extract-image", methods=["POST"])
@roles_required(['assistant'])
def extract_image():
    def fix_and_format_date(date_str):
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        clean_str = date_str.replace('I', '1').replace('l', '1').replace('i', '1')
        clean_str = re.sub(r'[^0-9/]', '', clean_str)

        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', clean_str)

        if match:
            day, month, year = match.groups()

            if len(year) == 2:
                year = "20" + year

            day = day.zfill(2)
            month = month.zfill(2)

            try:
                dt = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return datetime.now().strftime('%Y-%m-%d')

        return datetime.now().strftime('%Y-%m-%d')
    
    try:
        file = request.files["image"]

        tmp_name = ''.join(random.choices(
            (string.ascii_letters + string.digits), k=16))

        tmp_path = FOLDER + rf"\pictures\temp\{tmp_name}.jpg"

        file.save(tmp_path)

        try:
            Image.open(file.stream).verify()
        except:
            raise Exception("Tipo de arquivo invalido!")

        extraction = imgReader.extractInfo(tmp_path)

        result_format = str(extraction[0]).upper().replace(" ", "")


        raw_date_match = re.search(r'(?:DOCUMENTO|DATA)\s*:\s*([0-9Iil\/]{6,10})', result_format, re.IGNORECASE)
        raw_date_str = raw_date_match.group(1) if raw_date_match else None

        values = {
            "tmp_id": tmp_name,
            "ar_code": re.search(r'([A-Z]{2}\d{9}[A-Z]{2})', result_format).group(0),
            "date": fix_and_format_date(raw_date_str),
            "potential_people": extraction[1]
        }
        
        return jsonify({
            "Message": f"{values}"
        }), 201
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


# @app.route("/mails/update", methods=["POST"])
# def update():
#     data = request.get_json()

#     mail_type = data.get("type")
#     date = data.get("date")

#     if not date:
#         sqlite.log_edit(
#             route="/mails/update",
#             method="[POST]",
#             value_id=None,
#             code=400,
#             message="Invalid date Value",
#             fields_changed=None,
#             list_values=None,
#             ip=request.remote_addr
#         )

#         return jsonify({
#             "Message": "data inválida"
#         }, 400)

#     if mail_type == "return":
#         items = data.get("items", [])

#         if not items:
#             sqlite.log_edit(
#                 route="/mails/update",
#                 method="[POST]",
#                 value_id=None,
#                 code=400,
#                 message="Invalid Values",
#                 fields_changed=None,
#                 list_values=None,
#                 ip=request.remote_addr
#             )
#             return jsonify({
#                 "Message": "Nenhuma devolução informada"
#             }, 400)

#         inserted = []

#         for item in items:
#             code = item.get("code")
#             motivo = item.get("motivo")

#             if not code:
#                 continue

#             infos = mails_db.getMails(code, "id", "ASC")

#             if not infos:
#                 continue

#             infos = infos[0]

#             if infos[13]:
#                 return jsonify({
#                     "Message": "Correspondencia já devolvida detectada!"
#                 }, 400)

#             pname = (
#                 str(infos[4][:3].upper()) +
#                 str(infos[2][-5:]) +
#                 str(infos[0])
#             )

#             dest_path = FOLDER + r"\pictures\mails\\" + pname + ".jpg"

#             shutil.copy(lastImage, dest_path)

#             mails_db.updatePicture(
#                 motivo,
#                 date,
#                 pname,
#                 code,
#                 "returned"
#             )

#             inserted.append(code)

#             sqlite.log_edit(
#                 route="/mails/update",
#                 method="[POST]",
#                 value_id=item.get("code"),
#                 code=200,
#                 message="OK",
#                 fields_changed='{"mails": ["receive_name", "receive_date", "photo_id", "status"]}',
#                 list_values='{"receive_name": "' + motivo + '", "receive_date": "' +
#                 date + '", "photo_id": "' + pname + '", "status": "' + code + '"}',
#                 ip=request.remote_addr
#             )

#         if os.path.exists(lastImage):
#             os.remove(lastImage)

#         return jsonify({
#             "Message": "Devoluções registradas",
#             "type": "returns"
#         }, 200)

#     code = data.get("code")
#     user = data.get("user")

#     if (not code or not re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper())) or not user:
#         sqlite.log_edit(
#             route="/mails/update",
#             method="[POST]",
#             value_id=None,
#             code=400,
#             message="Invalid Values",
#             fields_changed=None,
#             list_values=None,
#             ip=request.remote_addr
#         )

#         return jsonify({
#             "Message": "Codigo ou Recebedor invalido!"
#         }, 400)

#     infos = mails_db.getMails(code, "id", "ASC")

#     if not infos:
#         sqlite.log_edit(
#             route="/mails/update",
#             method="[POST]",
#             value_id=None,
#             code=404,
#             message="Mail not found",
#             fields_changed=None,
#             list_values=None,
#             ip=request.remote_addr
#         )

#         return jsonify({
#             "Message": "Correspondência não encontrada"
#         }, 404)

#     elif infos[0][9].lower() == "shipped":
#         sqlite.log_edit(
#             route="/mails/update",
#             method="[POST]",
#             value_id=None,
#             code=409,
#             message="Mail already shipped",
#             fields_changed=None,
#             list_values=None,
#             ip=request.remote_addr
#         )

#         return jsonify({
#             "Message": "Correspondência já consta como entregue!"
#         }, 409)

#     infos = infos[0]

#     pname = (
#         str(infos[4][:3].upper()) +
#         str(infos[2][-5:]) +
#         str(infos[0])
#     )

#     dest_path = FOLDER + r"\pictures\mails\\" + pname + ".jpg"

#     shutil.move(lastImage, dest_path)

#     mails_db.updatePicture(user, date, pname, code, "shipped")

#     sqlite.log_edit(
#         route="/mails/update",
#         method="[POST]",
#         value_id=code,
#         code=200,
#         message="OK",
#         fields_changed='{"mails": ["receive_name", "receive_date", "photo_id", "status"]}',
#         list_values='{"receive_name": "' + user + '", "receive_date": "' +
#         date + '", "photo_id": "' + pname + '", "status": "' + code + '"}',
#         ip=request.remote_addr
#     )

#     return jsonify({
#         "Message": "Entrega registrada",
#         "PictureName": pname
#     }, 200)


# @app.route("/mails/update-column", methods=["POST"])
# def update_column():
#     data = request.get_json()

#     code = data.get("code")
#     column = data.get("column")
#     new_value = data.get("new_value")
#     old_value = data.get("old_value")

#     try:
#         mails_db.update(str(code), str(new_value), str(column))

#     except Exception as e:
#         sqlite.log_edit(
#             route="/mails/update-column",
#             method="[POST]",
#             value_id=code,
#             code=500,
#             message=e,
#             fields_changed=None,
#             list_values=None,
#             ip=request.remote_addr
#         )
#         return jsonify({
#             "Message": f"Erro não esperado!"
#         }, 500)
#     else:
#         sqlite.log_edit(
#             route="/mails/update-column",
#             method="[POST]",
#             value_id=code,
#             code=200,
#             message="OK",
#             fields_changed='{"mails", "' + column + '"}',
#             list_values='{"' + column + '", "' +
#             old_value + ' -> ' + new_value + '",}',
#             ip=request.remote_addr
#         )

#         return jsonify({
#             "Message": "Nome atualizado com sucesso!"
#         }, 200)

# ################################ #
#             SocketIO             #
#              Repass              #
# ################################ #
if __name__ == "__main__":
    Socket.run(
        app,
        host="0.0.0.0",
        port=80,
        debug=False
    )
