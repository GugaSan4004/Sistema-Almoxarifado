
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

sqlite = sqlite_core.init(FOLDER)

mails_db = sqlite_core.init.mails(sqlite)
users_db = sqlite_core.init.users(sqlite)
imgReader = imageocr.init()
returnGen = return_generator.init(FOLDER)


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
#            Main Routes           #
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
def page_not_found(e):
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

    return render_template("mails/mails.html", allowed_tabs=allowed_tabs)


@app.route("/pictures/<path:filename>")
def picture(filename):
    return send_from_directory(FOLDER / "pictures", filename)


# ################################ #
#          Mails Api Routes        #
# ################################ #


@app.route("/mails-api/set-userpass", methods=["POST"])
@login_required
def set_password():
    data = request.form
    password = generate_password_hash(data["password"])

    try:
        if (users_db.changePassword(password, session.get('user_id'), session.get('user_name'))):
            return redirect(url_for('mails'))
        else:
            raise Exception("!!!!!!!!Não era pra você estar aqui!!!!!!!")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/render-body/<tab_id>", methods=["POST"])
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

        values = {}

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

            if tab_id == "resume":
                values["totals"] = mails_db.getTotals()
                values["mails"] = mails_db.getMails(data[0], data[1], data[2])
                values["is_delayed"] = is_delayed
                values["format_date"] = format_date
                values["get_priority_class"] = get_priority_class
                values["filter"] = data[0]
                values["actualOrder"] = data[1]
            elif tab_id == "registerPickup":
                values["users"] = users_db.getUsernames()
            elif tab_id == "generateReturn":
                if data[3]:
                    values["pre_return_mails"] = mails_db.getMails(data[3])
                values["get_priority_class"] = get_priority_class
                values["format_date"] = format_date
            elif tab_id == "registerNewUser":
                values["roles"] = users_db.getRoles()

            return render_template(f"tabs/{tab_id}.html", **values)
        else:
            raise Exception("Permissão negada!")
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
        }), 400


@app.route("/mails-api/register-user", methods=["POST"])
@roles_required([""])
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


@app.route("/mails-api/register-mail", methods=["POST"])
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


@app.route("/mails-api/register-pickup", methods=["POST"])
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


@app.route("/mails-api/get-mail", methods=["POST"])
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


@app.route("/mails-api/exit-values", methods=["POST"])
@roles_required(["assistant"])
def exit_values():
    data = request.form

    code = data.get("code", "")
    tmp_id = data.get("tmp_id", "")
    date = data.get("date", datetime.now().strftime('%Y-%m-%d'))
    people = data.get("people", "")

    try:
        if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
            mail = mails_db.getMails(code, fetchOne=True)

            if not mail:
                raise Exception("Correspondencia não encontrada!")

            if mail[11] != "almox":
                raise Exception(
                    "Correspondencia não disponivel!")

            values = {
                "tmp_id": tmp_id,
                "fetched_code": code,
                "date": date,
                "potential_people": [people] if people else [""],
                "mail": mail
            }

            return jsonify({
                "Message": render_template("tabs/exitValues.html", **values)
            }), 203
        else:
            raise Exception("Codigo de rastreio invalido!")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/register-exit", methods=["POST"])
@roles_required(['assistant'])
def register_exit():
    data = request.form

    code = data.get("code").upper()
    picture_id = data.get("picture_id").upper()
    temp_pictureId = data.get("tmp_picture_id").upper()
    date = data.get("date")
    people = data.get("people")

    try:
        if not re.match(r'^[A-Za-z]{2}\d{9}BR$', code):
            raise Exception("Codigo de rastreio invalido!")

        if not picture_id or not date or not people:
            raise Exception("Valores insuficientes!")

        mails_db.updateMail(session.get('user_name'),
                            code, people, date, picture_id, temp_pictureId)

        return jsonify({
            "Message": "Registrado com sucesso!"
        }), 210
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/generate-return", methods=["POST"])
@roles_required(['assistant'])
def generate_return():
    data = request.form

    _dict = json.loads(data['mails'])

    pdf_path, token = returnGen.generate_return(_dict, session.get('user_name'))



    return jsonify({
        "Message": pdf_path
    }), 202


@app.route("/mails-api/extract-image", methods=["POST"])
@roles_required(['assistant'])
def extract_image():
    def fix_and_format_date(date_str):
        if not date_str:
            return datetime.now().strftime('%Y-%m-%d')

        clean_str = date_str.replace('I', '1').replace(
            'l', '1').replace('i', '1')
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

        tmp_path = FOLDER / "pictures" / "temp" / f"{tmp_name}.jpg"

        file.save(tmp_path)

        try:
            Image.open(file.stream).verify()
        except:
            raise Exception("Tipo de arquivo invalido!")

        extraction = imgReader.extractInfo(tmp_path)

        result_format = str(extraction[0]).upper().replace(" ", "")

        raw_date_match = re.search(
            r'(?:DOCUMENTO|DATA)\s*:\s*([0-9Iil\/]{6,10})', result_format, re.IGNORECASE)
        raw_date_str = raw_date_match.group(1) if raw_date_match else None

        code = re.search(r'([A-Z]{2}\d{9}[A-Z]{2})', result_format).group(0)
        values = {
            "tmp_id": tmp_name,
            "fetched_code": code,
            "date": fix_and_format_date(raw_date_str),
            "potential_people": extraction[1],
            "mail": mails_db.getMails(code, fetchOne=True)
        }

        return jsonify({
            "Message": f"{render_template("tabs/exitValues.html", **values)}"
        }), 203
    except Exception as e:
        return jsonify({
            "Message": f"Error: {e}"
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
