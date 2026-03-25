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

    if len(data) > 500_000:
        abort(413)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = users_db.getUserData(
            id=session.get("user_id")
        )

        if user:
            if user.get("status") < 0:
                return redirect(
                    location=url_for(
                        endpoint='login'
                    )
                )
        else:
            return redirect(
                location=url_for(
                    endpoint='login'
                )
            )

        return f(*args, **kwargs)
    return decorated_function


def roles_required(allowed_roles: list = []):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = users_db.getUserData(
                id=session.get('user_id')
            )

            if user.get("role") not in allowed_roles:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def has_tab_access(requested_tab: str):
    def decorator(f):
        @login_required
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = users_db.getUserData(
                id=session.get('user_id')
            )

            tabs = user.get("allowed_tabs")

            if requested_tab not in [tab.get("id") for tab in tabs]:
                return redirect(
                    location=url_for(
                        endpoint='mails'
                    )
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_code(code: str) -> bool:
    if re.match(r'^[A-Za-z]{2}\d{9}BR$', str(code).upper()):
        return True
    return False


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


def fix_and_format_date(date_str: str):
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


def get_priority_class(priority: str):
    color = "bg-red-500/30" if priority == "Judicial" else "bg-green-500/30"
    return f"{color} rounded-full px-2 font-semibold pb-0.5"


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

            if not change_pass_cookie and session.get('user_id'):
                return redirect(url_for("mails"))
        except Exception:
            pass

        return render_template("initial/login.html")
    elif request.method == "POST":
        try:
            data = request.form
            username = data.get("username")

            user = users_db.getUserData(
                name=username
            )

            if not user:
                flash(
                    message="Usuário não encontrado!",
                    category="danger"
                )
                return redirect(
                    location=url_for(
                        endpoint='login'
                    )
                )

            if not check_password_hash(user.get("password"), data["password"]):
                flash(
                    message="Senha incorreta!",
                    category="warning"
                )
                return redirect(
                    location=url_for(
                        endpoint='login'
                    )
                )

            if user.get("status") == -1:
                flash(
                    message="Essa conta ainda não está aprovada! <br> Peça ao administrador para ativa-la!",
                    category="danger"
                )
                return redirect(
                    location=url_for(
                        endpoint='login'
                    )
                )

            if user.get("status") == -2:
                flash(
                    message="Sua conta foi desativada! <br> Consulte o administrador para mais informações!",
                    category="danger"
                )

                return redirect(
                    location=url_for(
                        endpoint='login'
                    )
                )

            session.permanent = False
            session['user_id'] = user.get("id")

            if user.get("status") == 1:
                response = make_response(
                    redirect(
                        location=url_for(
                            endpoint='login'
                        )
                    )
                )

                response.set_cookie('change_pass', 'true', max_age=30)
                return response

            return redirect(
                location=url_for(
                    endpoint='mails'
                )
            )
        except Exception:
            return redirect(
                location=url_for(
                    endpoint='login'
                )
            )


@app.route("/register", methods=["GET", "POST"])
def register():
    try:
        if request.method == "GET":
            return render_template("initial/register.html")
        elif request.method == "POST":
            data = request.form
            username = data.get("username")
            password = data.get("password")
            rep_password = data.get("confirm_password")

            if password != rep_password:
                flash(
                    message="As senhas não coicidem!",
                    category="warning"
                )
                return redirect(
                    location=url_for(
                        endpoint='register'
                    )
                )

            if len(password) > 8:
                flash(
                    message="A senha deve ter pelo menos 8 caracteres!",
                    category="warning"
                )
                return redirect(
                    location=url_for(
                        endpoint='register'
                    )
                )

            name_parts = username.split()
            check_name = " ".join(name_parts[:2]) if len(
                name_parts) >= 2 else name_parts[0] if name_parts else ""

            if users_db.getUserData(name=check_name):
                flash(
                    message="Já existe um usuario cadastrado com esse nome!",
                    category="danger"
                )
                return redirect(
                    location=url_for(
                        endpoint='register'
                    )
                )

            users_db.registerNewUser(
                username=username,
                password=generate_password_hash(password, salt_length=64)
            )

            flash(
                message="Cadastro efetuado com sucesso! <br> Peça para um administrador ativar sua conta!",
                category="success"
            )
            return redirect(
                location=url_for(
                    endpoint='login'
                )
            )
        else:
            raise Exception("Method not allowed")
    except Exception:
        flash(
            message="Erro ao cadastrar. <br> Tente novamente mais tarde!",
            category="danger"
        )
        return redirect(
            location=url_for(
                endpoint='login'
            )
        )


@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route("/mails", methods=["GET"])
@login_required
def mails():
    user = users_db.getUserData(
        id=session.get('user_id')
    )

    values = {
        "allowed_tabs": user.get("allowed_tabs"),
        "user_name": user.get("name"),
    }

    return render_template(
        template_name_or_list="mails/mails.html",
        **values
    )


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
        values = {
            "totals": mails_db.getTotals(),
            "mails": mails_db.getMails(request.args.get("filter", ""), request.args.get("order", "id"), request.args.get("direction", "DESC")),
            "is_delayed_function": is_delayed,
            "format_date_function": format_date,
            "get_priority_class_function": get_priority_class,
            "filter": request.args.get("filter", ""),
            "actualOrder": request.args.get("order", "id"),
            "is_admin": users_db.getUserData(
                id=session.get('user_id')
            ).get("role") == "admin"
        }

        if request.method == "GET":
            return render_template(
                template_name_or_list="tabs/resume.html",
                **values
            )
        elif request.method == "POST":
            @roles_required(["Admin"])
            def update_mails():
                data = request.form

                id = data.get('id')

                fantasy = data.get('fantasy')
                name = data.get('name')
                priority = data.get('priority')
                _type = data.get('type')

                mailValues = {
                    "fantasy": fantasy.title() if (fantasy != "" and fantasy) else "---",
                    "name": name.title() if (name != "" and name) else "---",
                    "priority": priority.title() if (priority != "" and priority) else "Simples",
                    "type": _type.title() if (_type != "" and _type) else "Caixa"
                }

                mailSearch = {
                    "id": id.upper()
                }

                mails_db.updateMail(
                    values=mailValues,
                    search=mailSearch
                )

                return jsonify({
                    "head": "reload",
                    "Message": "OK"
                }), 200

            return update_mails()
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/registerNewMail", methods=["GET", "POST"])
@has_tab_access("registerNewMail")
def register_mail():
    try:
        if request.method == "GET":
            return render_template(
                template_name_or_list="tabs/registerNewMail.html"
            )
        elif request.method == "POST":
            data = request.form

            if not validate_code(data.get("code")):
                raise Exception("Codigo de correspondencia invalida!")

            mails_db.registerNewMail(
                sender=data.get("sender"),
                code=data.get("code"),
                fantasy=data.get("fantasy", ""),
                _type=data.get("type"),
                priority=data.get("priority"),
                user_id=session.get('user_id')
            )

            return jsonify({
                "head": "default",
                "Message": "Correspondencia cadastrada com sucesso!"
            }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        if "unique constraint failed" in str(e).lower():
            e = "Correspondencia já cadastrada!"

        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/registerPickup", methods=["GET", "POST"])
@has_tab_access("registerPickup")
def register_pickup():
    try:
        if request.method == "GET":
            values = {
                "users": users_db.getUsernames(inactives=False)
            }

            return render_template(f"tabs/registerPickup.html", **values)
        elif request.method == "POST":
            data = request.form

            if not validate_code(data.get("code")):
                raise Exception("Codigo de correspondencia invalida!")

            mails_db.registerPickup(
                code=data.get("code"),
                pickupuserid=users_db.getUserData(
                    name=data.get("user")
                ).get("id"),
                responsableuserid=session.get('user_id')
            )

            return jsonify({
                "head": "default",
                "Message": "Coleta registrada com sucesso!"
            }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/manageUsers", methods=["GET", "POST"])
@has_tab_access("manageUsers")
def manage_user():
    try:
        if request.method == "GET":
            values = {
                "users": users_db.getUsernames(),
                "username_session": users_db.getUserData(
                    id=session.get('user_id')
                ).get("name")
            }

            return render_template(f"tabs/manageUsers.html", **values)
        elif request.method == "POST":
            data = request.form
            username = data.get('username')

            if data.get('submit') == "True":
                userdata = users_db.getUserData(name=username)

                if not userdata:
                    raise Exception("Usuario não encontrado!")

                if username.lower() == users_db.getUserData(
                    id=session.get("user_id")
                ).get("name").lower():
                    raise Exception(
                        "Você não pode atualizar a sua propria conta!")

                if int(data.get('status')) not in [1, 0, -2]:
                    raise Exception("Status invalido!")

                users_db.updateUser(
                    id=userdata.get('id'),
                    role=users_db.getRoles(
                        filter=data.get('role')
                    )[0][0],
                    status=int(
                        data.get('status')
                    )
                )

                return jsonify({
                    "head": "realert",
                    "Message": "Cadastro atualizado com sucesso!"
                }), 200
            else:
                userdata = users_db.getUserData(
                    name=username
                )

                if not userdata:
                    raise Exception("Usuario não encontrado!")

                role = userdata.get('role')
                status = userdata.get('status')

                values = {
                    "username_session": users_db.getUserData(
                        id=session.get('user_id')
                    ).get("name"),
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
                    "Message": f"{
                        render_template(
                            "tabs/manageUsers.html",
                            **values
                        )
                    }"
                }), 200
        else:
            raise Exception("Method not allowed")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/registerExit", methods=["GET", "POST"])
@has_tab_access("registerExit")
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

                tmp_name = ''.join(
                    random.choices(
                        (string.ascii_letters + string.digits),
                        k=16
                    )
                )

                tmp_path = FOLDER / "pictures" / "temp" / f"{tmp_name}.jpg"

                file.save(tmp_path)

                try:
                    Image.open(file.stream).verify()
                except:
                    raise Exception("Tipo de arquivo invalido!")

                extraction = imgReader.extractInfo(
                    path=tmp_path
                )

                result_format = str(extraction[0]).upper().replace(" ", "")

                if "TERMODEDEVOLUCAOAOSCORREIOS" in result_format:
                    token_match = re.search(
                        pattern=r'ID:\s*([^\s]+)',
                        string=extraction[0]
                    )

                    extracted_token = token_match.group(
                        1) if token_match else ""

                    mails = mails_db.getMails(
                        mail_filter=extracted_token,
                        column="pictureId"
                    )

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
                            "head": "realert",
                            "Message": "Devolução registrada com sucesso"
                        }), 200
                    else:
                        raise Exception(
                            "Nenhuma devolução pendente corresponde a esse documento!")
                else:
                    raw_date_match = re.search(
                        pattern=r'(?:DOCUMENTO|DATA)\s*:\s*([0-9Iil\/]{6,10})',
                        string=result_format,
                        flags=re.IGNORECASE
                    )

                    raw_date_str = raw_date_match.group(
                        1) if raw_date_match else None

                    if code := re.search(r'([A-Z]{2}\d{9}[A-Z]{2})', result_format):
                        code = code.group(0)

                    if mail := mails_db.getMails(
                        mail_filter=code,
                        fetchOne=True,
                        column="code"
                    ) if code else None:
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

                if not validate_code(code):
                    raise Exception("Codigo da correspondencia invalida!")

                date = data.get("date", datetime.now().strftime('%Y-%m-%d'))
                people = data.get("people", "")

                if not date or not people:
                    raise Exception("Valores insuficientes!")

                if "final_submit" in data:
                    picture_id = data.get("picture_id").upper()
                    temp_pictureId = data.get("tmp_picture_id").upper()

                    if not picture_id:
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
                        'deliveredBy': session.get('user_id'),
                        'pictureId': picture_id.upper()
                    }

                    mailSearch = {
                        'code': code.upper()
                    }

                    mails_db.updateMail(
                        values=mailValues,
                        search=mailSearch
                    )

                    return jsonify({
                        "head": "realert",
                        "Message": "Registro efetuado com sucesso!"
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
                        "potential_people": [people],
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
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/set-userpass", methods=["POST"])
@login_required
def set_password():
    try:
        data = request.form
        user_id = session.get('user_id')

        userdata = users_db.getUserData(
            id=user_id
        )

        if userdata.get("status") != 1:
            raise Exception("Permissão negada!")

        password = generate_password_hash(
            password=data["password"],
            salt_length=64
        )

        if users_db.changePassword(
            password=password,
            userid=user_id
        ):
            return redirect(
                location=url_for(
                    endpoint='mails'
                )
            )
        else:
            raise Exception("Nao foi possivel alterar a senha!")
    except Exception as e:
        return jsonify({
            "Message": f"{e}"
        }), 400


@app.route("/mails-api/generateReturn", methods=["GET", "POST"])
@has_tab_access("generateReturn")
def generate_return():
    try:
        if request.method == "GET":
            if code := request.args.get("code"):
                if not validate_code(code):
                    raise Exception("Codigo de correspondencia invalida!")

                if mail := mails_db.getMails(
                    mail_filter=request.args.get("code").upper(),
                    fetchOne=True,
                    column="code"
                ):
                    if mail[11] != "almox":
                        raise Exception(
                            "Correspondencia indisponivel para devolução!")

                    return jsonify({
                        "head": "append_return",
                        "Message": mail[2]
                    }), 200
                else:
                    raise Exception("Correspondencia não encontrada!")

            values = {
                "format_date_function": format_date,
                "get_priority_class_function": get_priority_class
            }

            if request.args.get("return_data"):
                if request.args.get("return_data") != "{}":
                    values["mails"] = mails_db.getMails(
                        mail_filter=json.loads(
                            s=request.args.get("return_data")
                        )
                    )

            return render_template(f"tabs/generateReturn.html", **values)
        elif request.method == "POST":
            data = json.loads(
                s=request.form.get("values")
            )

            formated_data = {}

            for code, reason in data.items():
                if mail := mails_db.getMails(
                    mail_filter=code,
                    fetchOne=True,
                    column="code"
                ):
                    if mail[11] != "almox":
                        raise Exception(
                            "Correspondencia indisponivel encontrada. Geração cancelada!")
                    formated_data[code] = {
                        "name": mail[1],
                        "reason": reason
                    }
                else:
                    raise Exception(
                        "Correspondencia inexistente encontrada. Geração cancelada!")

            token = returnGen.generate_return(
                data=formated_data,
                username=users_db.getUserData(
                    id=session.get('user_id')
                ).get("name")
            )

            for code, reason in data.items():

                mailValues = {
                    'status': 'pre_returned',
                    'deliveryDetail': reason.title() if reason else "Desconhecido",
                    'deliveredBy': session.get('user_id'),
                    'pictureId': token
                }

                mailSearch = {
                    'code': code
                }

                mails_db.updateMail(
                    values=mailValues,
                    search=mailSearch
                )

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


@app.route("/mails-api/manageRoles", methods=["GET", "POST"])
@has_tab_access("manageRoles")
def manage_roles():
    try:
        if request.method == "GET":
            all_tabs = users_db.getAllTabs()
            roles = users_db.getRolesWithIds()

            roles_data = []
            for r_id, r_name in roles:
                allowed = users_db.getAllowedTabs(role_id=r_id)
                tabs = [t["id"] for t in allowed] if allowed else []
                if r_id == 1:
                    tabs = [t["id"] for t in all_tabs]

                roles_data.append({
                    "id": r_id,
                    "name": r_name,
                    "tabs": tabs
                })

            return render_template("tabs/manageRoles.html", all_tabs=all_tabs, roles_data=roles_data)
        elif request.method == "POST":
            data = request.form
            mode = data.get("mode")
            is_edit_mode = mode == "on"

            selected_tabs = request.form.getlist("tabs")
            action = data.get("form_action", "save")


            if is_edit_mode:
                role_id = data.get("role_id")
                if not role_id:
                    raise Exception("Cargo não selecionado!")
                role_id = int(role_id)

                if action == "delete":
                    if role_id in [0]:
                        raise Exception("Cargos padrões não podem ser deletados!")

                    if users_db.checkRoleUsage(role_id) > 0:
                        raise Exception("Existem usuários usando este cargo. Remova-os primeiro!")

                    if users_db.deleteRole(role_id):
                        message = "Cargo deletado com sucesso!"
                    else:
                        raise Exception("Falha ao deletar o cargo!")
                else:
                    if role_id == 1:
                        raise Exception(
                            "Não é possível editar as abas do Administrador!")
                    users_db.updateRoleTabs(
                        role_id=role_id, tab_ids=selected_tabs)
                    message = "Permissões atualizadas com sucesso!"
            else:
                role_name = data.get("role_name", "").strip()
                if not role_name:
                    raise Exception("O nome do cargo não deve estar vazio!")

                if users_db.getRoleByName(role_name):
                    raise Exception("Um cargo com este nome já existe!")

                new_role_id = users_db.createRole(
                    name=role_name, created_by=session.get("user_id"))
                users_db.updateRoleTabs(
                    role_id=new_role_id, tab_ids=selected_tabs)
                message = "Cargo criado com sucesso!"

            return jsonify({
                "head": "realert",
                "Message": message
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
