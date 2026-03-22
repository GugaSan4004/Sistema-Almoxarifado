
from PIL import Image
from pathlib import Path
from functools import wraps
from datetime import datetime
from flask_socketio import SocketIO
from static.py import imageocr, return_generator, sqlite_core
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, abort, request, jsonify, render_template, send_from_directory, session, redirect, url_for, flash, make_response

import re
import sys
import json
import psutil
import random
import string
import shutil
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


# ################################ #
#       Essencial Variables        #
# ################################ #


FOLDER = Path.cwd()

imgReader = imageocr.init()
sqlite = sqlite_core.init(FOLDER)
returnGen = return_generator.init(FOLDER)

mails_db = sqlite_core.init.mails(sqlite)
users_db = sqlite_core.init.users(sqlite)


app = Flask(__name__)
new_secret_key = secrets.token_urlsafe(32)
app.secret_key = new_secret_key
print(f"Secret key for this section -> {new_secret_key}")

Socket = SocketIO(
    app,
    async_mode="eventlet",
    ping_interval=25,
    ping_timeout=60,
    cors_allowed_origins="*"
)


# ################################ #
#     Setting up Environement      #
# ################################ #


app.config["ENV"] = "production"
app.config["DEBUG"] = False

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)


# ################################ #
#             Firewall             #
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
        user = users_db.getUserData(name=session.get(
            "user_name"), id=session.get("user_id"))

        if 'user_id' not in session:
            return redirect(url_for('login'))
        if user:
            if user[4] < 0:
                return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


def roles_required(allowed_roles: list = []):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            allowed_roles.append("admin")

            user = users_db.getUserData(name=session.get(
                'user_name'), id=session.get('user_id'))

            if session.get('user_role') not in allowed_roles or user[3] not in allowed_roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def has_tab_access(requested_tab: str):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            tabs = users_db.getAllowedTabs(session.get('user_role'))

            tabs = [tab.get('id') for tab in tabs]

            if requested_tab not in tabs:
                return redirect(url_for('mails'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_code(code: str) -> bool:
    if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
        return True
    return False


@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('mails'))


# ################################ #
#            Main Routes           #
# ################################ #


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        try:
            change_pass_cookie = request.cookies.get('change_pass')

            if not change_pass_cookie and (session.get('user_id') and session.get('user_role') and session.get("user_name")):
                return redirect(url_for("mails"))
        except Exception:
            pass

        return render_template("initial/login.html")
    elif request.method == "POST":
        try:
            data = request.form
            username = data.get("username")

            user = users_db.getUserData(name=username)

            if not user:
                flash("Usuário não encontrado!", "danger")
                return redirect(url_for('login'))

            if check_password_hash(user[2], data["password"]):
                if user[4] == -1:
                    flash(
                        "Essa conta está inativa! <br> Consulte o administrador para mais informações!", "danger")
                    return redirect(url_for('login'))

                if user[4] == -2:
                    flash(
                        "Sua conta foi desativada! <br> Consulte o administrador para mais informações!", "danger")
                    return redirect(url_for('login'))

                session.permanent = False
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_role'] = user[3]

                if user[4] == 1:
                    response = make_response(redirect(url_for('login')))

                    response.set_cookie('change_pass', 'true', max_age=30)
                    return response

                return redirect(url_for('mails'))
            else:
                flash("Senha incorreta!", "warning")
                return redirect(url_for('login'))
        except Exception:
            return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("initial/register.html")
    elif request.method == "POST":
        data = request.form
        username = data.get("username")
        password = data.get("new_password")
        rep_password = data.get("rep_new_password")

        if password != rep_password:
            flash("As senhas não coicidem!", "warning")
            return redirect(url_for('register'))

        name_parts = username.split()
        check_name = " ".join(name_parts[:2]) if len(
            name_parts) >= 2 else name_parts[0] if name_parts else ""

        user = users_db.getUserData(name=check_name)

        if user:
            flash("Já existe um usuario cadastrado com esse nome!", "danger")
            return redirect(url_for('register'))

        try:
            password = generate_password_hash(password, salt_length=64)

            users_db.registerNewUser(username, password)
        except Exception:
            flash("Erro ao cadastrar. <br> Tente novamente mais tarde!", "danger")
            return redirect(url_for('login'))
        else:
            flash(
                "Cadastro efetuado com sucesso! <br> Peça para um administrador ativar sua conta!", "success")
            return redirect(url_for('login'))


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/mails", methods=["GET"])
@login_required
def mails():
    user_role = session.get('user_role')
    allowed_tabs = users_db.getAllowedTabs(user_role)

    return render_template("mails/mails.html", allowed_tabs=allowed_tabs)


@app.route("/pictures/<path:filename>")
def picture(filename):
    return send_from_directory(FOLDER / "pictures", filename)


# ################################ #
#          Mails Api Routes        #
# ################################ #


@app.route("/mails-api/resume", methods=["GET", "POST"])
@has_tab_access("resume")
def resume():
    try:
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
            "mails": mails_db.getMails(request.args.get("filter", ""), request.args.get("order", "id"), request.args.get("direction", "DESC")),
            "is_delayed": is_delayed,
            "format_date": format_date,
            "get_priority_class": get_priority_class,
            "filter": request.args.get("filter", ""),
            "actualOrder": request.args.get("order", "id"),
            "user_role": session.get("user_role")
        }

        if request.method == "GET":
            return render_template("tabs/resume.html", **values)
        elif request.method == "POST":
            @roles_required(["admin"])
            def update_mails():
                data = request.form

                id = data.get('id')

                fantasy = data.get('fantasy')
                name = data.get('name')
                priority = data.get('priority')
                receiverName = data.get('receiverName')
                _type = data.get('type')

                mailValues = {
                    "fantasy": fantasy.title() if (fantasy != "" and fantasy) else "---",
                    "name": name.title() if (name != "" and name) else "---",
                    "priority": priority.title() if (priority != "" and priority) else "Simples",
                    "deliveredBy": receiverName.title() if (receiverName != "" and receiverName) else "---",
                    "type": _type.title() if (_type != "" and _type) else "Caixa"
                }

                mailSearch = {
                    "id": id.upper()
                }

                mails_db.updateMail(values=mailValues, search=mailSearch)

                return jsonify({
                    "head": "reload",
                    "Message": "OK"
                }), 200

            return update_mails()
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/registerNewMail", methods=["GET", "POST"])
@has_tab_access("registerNewMail")
@roles_required(["recepcionista"])
def register_mail():
    try:
        if request.method == "GET":
            return render_template("tabs/registerNewMail.html")
        elif request.method == "POST":
            data = request.form

            code = data["code"]
            sender = data["sender"]
            fantasy = data["fantasy"] if data["fantasy"] else ""
            _type = data["type"]
            priority = data["priority"]
            username = session.get('user_name')

            if not validate_code(code):
                raise Exception("Codigo de rastreio invalido!")
            
            mails_db.registerNewMail(
                sender=sender,
                code=code,
                fantasy=fantasy,
                _type=_type,
                priority=priority,
                username=username
            )

            return jsonify({
                "head": "default",
                "Message": "Cadastrado Com Sucesso!"
            }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        if "unique constraint failed" in str(e).lower():
            e = "Correspondencia já cadastrada!"

        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/registerPickup", methods=["GET", "POST"])
@has_tab_access("registerPickup")
@roles_required(["recepcionista"])
def register_pickup():
    try:
        if request.method == "GET":
            values = {
                "users": users_db.getUsernames()
            }

            return render_template(f"tabs/registerPickup.html", **values)
        elif request.method == "POST":
            data = request.form

            code = data["code"]
            pickupuser = data["user"]
            responsableuser = session.get('user_name')

            if not validate_code(code):
                raise Exception("Codigo de rastreio invalido!")
            
            mails_db.registerPickup(code, pickupuser, responsableuser)

            return jsonify({
                "head": "default",
                "Message": "Registrado Com Sucesso!"
            }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/manageUsers", methods=["GET", "POST"])
@has_tab_access("manageUsers")
@roles_required()
def manage_user():
    try:
        if request.method == "GET":
            values = {
                "users": users_db.getUsernames(),
                "username_session": session.get("user_name")
            }

            return render_template(f"tabs/manageUsers.html", **values)
        elif request.method == "POST":
            data = request.form
            username = data.get('username')

            if data.get('submit') == "True":
                userdata = users_db.getUserData(name=username)

                if username.lower() == session.get("user_name").lower():
                    raise Exception(
                        "Você não pode atualizar a sua propria conta!")

                if int(data.get('status')) not in [1, 0, -2]:
                    raise Exception("Status invalido!")

                if userdata:
                    users_db.updateUser(
                        id=userdata[0],
                        name=username,
                        role=data.get('role'),
                        status=int(data.get('status'))
                    )

                    return jsonify({
                        "head": "realert",
                        "Message": "Cadastro atualizado com sucesso!"
                    }), 200
                else:
                    raise Exception("Usuario não encontrado!")
            else:
                userdata = users_db.getUserData(name=username)

                if not userdata:
                    raise Exception("Usuario não encontrado!")

                role = userdata[3]
                status = userdata[4]

                values = {
                    "username_session": session.get("user_name"),
                    "selected_user": username,
                    "users": users_db.getUsernames(),
                    "roles": users_db.getRoles(),
                    "userdata": {
                        "role": role,
                        "status": status
                    }
                }

                return jsonify({
                    "head": "load",
                    "Message": f"{render_template(f"tabs/manageUsers.html", **values)}"
                }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/registerExit", methods=["GET", "POST"])
@has_tab_access("registerExit")
@roles_required(['almoxarife'])
def register_exit():
    try:
        if request.method == "GET":
            values = {
                "users": users_db.getUsernames()
            }

            return render_template(f"tabs/registerExit.html", **values)
        elif request.method == "POST":
            if "image" in request.files:
                file = request.files["image"]

                def fix_and_format_date(date_str):
                    if not date_str:
                        return datetime.now().strftime('%Y-%m-%d')

                    clean_str = date_str.replace('I', '1').replace(
                        'l', '1').replace('i', '1')
                    clean_str = re.sub(r'[^0-9/]', '', clean_str)

                    match = re.search(
                        r'(\d{1,2})/(\d{1,2})/(\d{2,4})', clean_str)

                    if match:
                        day, month, year = match.groups()

                        if len(year) == 2:
                            year = "20" + year

                        day = day.zfill(2)
                        month = month.zfill(2)

                        try:
                            dt = datetime.strptime(
                                f"{day}/{month}/{year}", "%d/%m/%Y")
                            return dt.strftime('%Y-%m-%d')
                        except ValueError:
                            return datetime.now().strftime('%Y-%m-%d')

                    return datetime.now().strftime('%Y-%m-%d')

                tmp_name = ''.join(random.choices(
                    (string.ascii_letters + string.digits), k=16))

                tmp_path = FOLDER / "pictures" / "temp" / f"{tmp_name}.jpg"

                file.save(tmp_path)

                try:
                    Image.open(file.stream).verify()
                except:
                    raise Exception("Tipo de arquivo invalido!")

                extraction = imgReader.extractInfo(tmp_path)

                result_format = str(extraction[0]).upper().replace(" ", "")

                if "TERMODEDEVOLUCAOAOSCORREIOS" in result_format:
                    token_match = re.search(r'ID:\s*([^\s]+)', extraction[0])
                    extracted_token = token_match.group(
                        1) if token_match else ""

                    mails = mails_db.getMails(mail_filter=extracted_token)

                    if mails:
                        for mail in mails:
                            if mail[11] != "pre_returned":
                                raise Exception(
                                    "Correspondencia divergente encontrada! Registro cancelado.")

                        for mail in mails:
                            id = mail[0]
                            _type = mail[4]
                            code = mail[2]

                            new_id = _type[:3].upper() + code[-5:] + str(id)

                            mailValues = {
                                'status': 'returned',
                                'deliveredAt': datetime.now().strftime("%Y-%m-%d %H:%M"),
                                'pictureId': new_id
                            }

                            mailSearch = {
                                'pictureId': extracted_token
                            }

                            mails_db.updateMail(mailValues, mailSearch)

                            shutil.copyfile(
                                src=FOLDER / 'pictures' /
                                'temp' / f'{tmp_name}.jpg',
                                dst=FOLDER / 'pictures' /
                                'mails' / f'{new_id}.jpg'
                            )

                        (FOLDER / 'pictures' / 'temp' /
                         f'{tmp_name}.jpg').unlink(missing_ok=True)
                        (FOLDER / 'pictures' / 'temp' /
                         f'{extracted_token}.jpg').unlink(missing_ok=True)

                        return jsonify({
                            "head": "default",
                            "Message": "Devolução registrada com sucesso"
                        }), 200
                    else:
                        raise Exception(
                            "Nenhuma devolução pendente corresponde a esse documento!")
                else:
                    raw_date_match = re.search(
                        r'(?:DOCUMENTO|DATA)\s*:\s*([0-9Iil\/]{6,10})', result_format, re.IGNORECASE)
                    raw_date_str = raw_date_match.group(
                        1) if raw_date_match else None

                    if code := re.search(r'([A-Z]{2}\d{9}[A-Z]{2})', result_format):
                        code = code.group(0)

                    if mail := mails_db.getMails(code, fetchOne=True) if code else None:
                        mail = None if mail[11] != "almox" else mail

                    values = {
                        "tmp_id": tmp_name,
                        "fetched_code": code,
                        "date": fix_and_format_date(raw_date_str),
                        "potential_people": extraction[1],
                        "mail": mail
                    }

                    return jsonify({
                        "head": "load",
                        "Message": f"{render_template("tabs/exitValues.html", **values)}"
                    }), 200
            else:
                data = request.form

                code = data.get("code", "")
                date = data.get("date", datetime.now().strftime('%Y-%m-%d'))
                people = data.get("people", "")

                if not validate_code(code):
                    raise Exception("Codigo de rastreio invalido!")

                if "final_submit" in data:
                    picture_id = data.get("picture_id").upper()
                    temp_pictureId = data.get("tmp_picture_id").upper()

                    if not picture_id or not date or not people:
                        raise Exception("Valores insuficientes!")

                    shutil.move(
                        src=FOLDER / 'pictures' / 'temp' /
                        f'{temp_pictureId}.jpg',
                        dst=FOLDER / 'pictures' / 'mails' / f'{picture_id}.jpg'
                    )

                    mailValues = {
                        'status': 'shipped',
                        'deliveryDetail': people.title(),
                        'deliveredAt': datetime.strptime(date, "%Y-%m-%d"),
                        'deliveredBy': session.get('user_name'),
                        'pictureId': picture_id.upper()
                    }

                    mailSearch = {
                        'code': code.upper()
                    }

                    mails_db.updateMail(values=mailValues, search=mailSearch)

                    return jsonify({
                        "head": "realert",
                        "Message": "Registrado com sucesso!"
                    }), 200
                else:
                    tmp_id = data.get("tmp_id", "")
                    mail = mails_db.getMails(code, fetchOne=True)

                    if not mail:
                        raise Exception("Correspondencia não encontrada!")

                    if mail[11] != "almox":
                        raise Exception(
                            "Correspondencia indisponivel para retirada!")

                    values = {
                        "tmp_id": tmp_id,
                        "fetched_code": code,
                        "date": date,
                        "potential_people": [people] if people else [""],
                        "mail": mail
                    }

                    return jsonify({
                        "head": "load",
                        "Message": render_template("tabs/exitValues.html", **values)
                    }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/set-userpass", methods=["POST"])
@login_required
def set_password():
    try:
        data = request.form
        user_id = session.get('user_id')
        user_name = session.get('user_name')

        userdata = users_db.getUserData(
            name=session.get('user_name'),
            id=session.get('user_id')
        )

        if user_id != userdata[0] or user_name != userdata[1] or userdata[4] != 1:
            raise Exception("Permissão negada!")

        password = generate_password_hash(data["password"], salt_length=64)

        if (users_db.changePassword(password, user_id, user_name)):
            return redirect(url_for('mails'))
        else:
            raise Exception("Erro inesperado")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/generateReturn", methods=["GET", "POST"])
@has_tab_access("generateReturn")
@roles_required(['almoxarife'])
def generate_return():
    try:
        def format_date(dateStr: str):
            if not dateStr:
                return ""
            return "/".join(dateStr.split(' ')[0].split('-')[::-1])
        
        def get_priority_class(priority: str):
            color = "bg-red-500/30" if priority == "Judicial" else "bg-green-500/30"
            return f"{color} rounded-full px-2 font-semibold pb-0.5"
            
        if request.method == "GET":
            if code := request.args.get("code"):
                if not validate_code(code):
                    raise Exception("Codigo de rastreio invalido!")
                
                if mail := mails_db.getMails(mail_filter=request.args.get("code").upper(), fetchOne=True, column="code"):
                    if mail[11] != "almox":
                        raise Exception("Correspondencia indisponivel para devolução!")
                    return jsonify({
                        "head": "append_return",
                        "Message": mail[2]
                    }), 200
                else:
                    raise Exception("Correspondencia não encontrada!")
                
            values = {
                "format_date": format_date,
                "get_priority_class": get_priority_class
            }

            if request.args.get("return_data"):
                if request.args.get("return_data") != "{}":
                    values["mails"] = mails_db.getMails(mail_filter=json.loads(request.args.get("return_data")))

            return render_template(f"tabs/generateReturn.html", **values)
        elif request.method == "POST":
            data = json.loads(request.form.get("values"))
            formated_data = {}

            for code, reason in data.items():
                input(reason)
                if mail := mails_db.getMails(mail_filter=code, fetchOne=True, column="code"):
                    if mail[11] != "almox":
                        raise Exception("Correspondencia indisponivel para devolução encontrada!")
                    formated_data[code] = {
                        "name": mail[1],
                        "reason": reason
                    }
                else:
                    raise Exception("Correspondencia inexistente encontrada!")
                
            token = returnGen.generate_return(formated_data , session.get('user_name'))

            for code, reason in data.items():
                mailValues = {
                    'status': 'pre_returned',
                    'deliveryDetail': reason.title() if reason else "Desconhecido",
                    'deliveredBy': session.get('user_name'),
                    'pictureId': token
                }

                mailSearch = {
                    'code': code
                }

                mails_db.updateMail(values=mailValues, search=mailSearch)

                return jsonify({
                    "head": "print",
                    "Message": token
                }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


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
