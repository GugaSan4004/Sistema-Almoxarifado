import os
import re
import shutil
import sqlite3
import unicodedata

from rapidfuzz import fuzz
from datetime import datetime


class init:
    def __init__(self, folder) -> None:
        db_path = folder / 'db.sqlite'
        if not os.path.exists(db_path):
            shutil.copyfile(folder / '.sqltemplate', folder / 'db.sqlite')
        self.connector = sqlite3.connect(db_path, check_same_thread=False)
        self.folder = folder

    class mails:
        def __init__(self, parent: "init") -> None:
            self.connection: sqlite3.Connection = parent.connector
            self.AllowedOrderDirection = [
                "ASC",
                "DESC"
            ]
            self.folder = parent.folder

        def updateMail(self, values: dict, search: dict, search_logic: str = "AND") -> None:
            cur = self.connection.cursor()

            set_clause = ", ".join([f"{k} = ?" for k in values.keys()])
            set_values = list(values.values())

            where_clause = ""
            where_values = []

            if search:
                logic = search_logic.upper()

            if logic not in ["AND", "OR"]:
                logic = "AND"

            where_clause = " WHERE " + f" {logic} ".join([f"{k} = ?" for k in search.keys()])
            where_values = list(search.values())

            sql = f"UPDATE mails SET {set_clause}{where_clause}"
            cur.execute(sql, set_values + where_values)
                
            self.connection.commit()

            cur.close()

        def registerPickup(self, code: str, pickupuser: str, responsableuser: str) -> None:
            cur = self.connection.cursor()

            cur.execute("SELECT status FROM mails WHERE code = ?",
                        (code.upper(),)
                        )

            result = cur.fetchone()

            if (not result):
                raise Exception("Correspondencia não encontrada!")

            if (result[0] != "reception"):
                raise Exception(
                    "Correspondencia não disponivel para retirada!")

            cur.execute("UPDATE mails set receivedOnReceptionBy = ?, sendedOnReceptionBy = ?, status = ?, leaveReceptionAt = ? WHERE code = ?",
                        (
                            pickupuser,
                            responsableuser,
                            "almox",
                            datetime.now().strftime("%Y-%m-%d %H:%M"),
                            code.upper()
                        )
                        )
            self.connection.commit()
            cur.close()

        def registerNewMail(self, sender: str, code: str, fantasy: str, type_: str, priority: str, username: str):
            cur = self.connection.cursor()

            def normalize(text):
                if not text:
                    return ""

                text = text.lower()
                text = unicodedata.normalize("NFKD", text).encode(
                    "ascii", "ignore").decode("ascii")

                text = re.sub(
                    r'\b(ltda|sa|s\/a|me|eireli|comercio|de|alimentos)\b', '', text)

                text = re.sub(r'[^a-z0-9 ]', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text

            if not fantasy or fantasy == "":
                threshold = 85

                cur.execute("""
                    SELECT DISTINCT name, fantasy
                    FROM mails
                    WHERE fantasy IS NOT NULL AND fantasy != ''
                """
                            )

                known_rows = [
                    {"name": n, "fantasy": f}
                    for n, f in cur.fetchall()
                ]

                name_norm = normalize(sender)

                best_score = 0
                best_fantasy = ""

                for row in known_rows:
                    known_name_norm = normalize(row["name"])
                    score = fuzz.token_set_ratio(
                        name_norm, known_name_norm)

                    if score > best_score:
                        best_score = score
                        best_fantasy = row["fantasy"]

                if best_score >= threshold:
                    fantasy = best_fantasy

            cur.execute("""
                INSERT INTO mails (name, code, fantasy, type, priority, joinDate, registeredBy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                sender.title(),
                code.upper(),
                fantasy.title(),
                type_.title(),
                priority.title(),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                username.title()
            )
            )
            self.connection.commit()

            cur.close()
            return None

        def getMails(self, mail_filter: str | dict = "", orderBy: str = "", orderDirection: str = "ASC", fetchOne: bool = False) -> list:
            cur = self.connection.cursor()

            if orderDirection not in self.AllowedOrderDirection:
                orderDirection = "ASC"

            cur.execute("PRAGMA table_info(mails)")
            tableColumns = cur.fetchall()

            allowedCols = [coluna[1] for coluna in tableColumns]

            if orderBy not in allowedCols:
                orderBy = "id"

            if mail_filter:
                if mail_filter == "delayed":
                    cur.execute(
                        f"SELECT * FROM mails WHERE((priority = 'Simples' AND (julianday('now') - julianday(joinDate || ':00')) * 24 >= 120) OR ( priority = 'Judicial' AND (julianday('now') - julianday(joinDate || ':00')) * 24 >= 72)) AND (status = 'almox' OR status = 'reception') ORDER BY {orderBy} {orderDirection}",
                    )
                elif mail_filter == "returned":
                    cur.execute(
                        f"SELECT * FROM mails WHERE status = ? OR status = ? ORDER BY {orderBy} {orderDirection}",
                        (
                            "returned",
                            "pre_returned"
                        )
                    )
                elif type(mail_filter) == dict:
                    correspondences = []
                    for mailCode, returnReason in mail_filter.items():
                        cur.execute(
                            f"SELECT * FROM mails WHERE code = ?",
                            (mailCode,)
                        )
                        correspondences.append(
                            cur.fetchone() + (returnReason['reason'],))
                    cur.close()
                    return correspondences
                else:
                    cur.execute(
                        f"SELECT * FROM mails WHERE code LIKE ? OR name LIKE ? OR fantasy LIKE ? OR pictureId LIKE ? OR deliveryDetail LIKE ? OR status = ? OR type LIKE ? OR priority LIKE ? ORDER BY {orderBy} {orderDirection}",
                        (
                            "%" + mail_filter + "%",
                            "%" + mail_filter + "%",
                            "%" + mail_filter + "%",
                            "%" + mail_filter + "%",
                            "%" + mail_filter + "%",
                            mail_filter,
                            "%" + mail_filter.title() + "%",
                            "%" + mail_filter.title() + "%"
                        )
                    )
            else:
                cur.execute(
                    f"SELECT * FROM mails ORDER BY {orderBy} {orderDirection}")

            correspondences = cur.fetchone() if fetchOne else cur.fetchmany(300)

            cur.close()

            return correspondences

        def getTotals(self) -> dict[str, int]:
            cur = self.connection.cursor()
            cur.execute("SELECT status, joinDate, priority FROM mails")

            rows = cur.fetchall()
            cur.close()

            total = 0
            returned = 0
            shipped = 0
            delayed = 0
            casualty = 0
            reception = 0
            almox = 0

            for status, join_date, priority in rows:
                total += 1

                if status == "returned" or status == "pre_returned":
                    returned += 1
                elif status == "shipped":
                    shipped += 1
                elif status == "casualty":
                    casualty += 1
                elif status == "reception":
                    reception += 1
                elif status == "almox":
                    almox += 1

                if join_date and status in ["almox", "reception"]:
                    try:
                        entry_date = datetime.strptime(
                            join_date, "%Y-%m-%d %H:%M")
                        now = datetime.now()

                        diff = now - entry_date
                        hours_passed = diff.total_seconds() / 3600

                        thresholds = {
                            "Simples": 120,
                            "Judicial": 72
                        }

                        limit = thresholds.get(priority, 48)

                        if hours_passed > limit:
                            delayed += 1
                    except Exception:
                        pass

            return {
                "total": total,
                "returned": returned,
                "shipped": shipped,
                "delayed": delayed,
                "casualty": casualty,
                "reception": reception,
                "almox": almox
            }

    class users:
        def __init__(self, parent: "init") -> None:
            self.connection: sqlite3.Connection = parent.connector

        def getUserData(self, param: str) -> list | None:
            cur = self.connection.cursor()

            cur.execute("SELECT * FROM users WHERE name LIKE ? or id = ?",
                        (param.title() + "%" if type(param) == str else param, param))

            result = cur.fetchone()

            cur.close()

            return result

        def getUsernames(self) -> list:
            cur = self.connection.cursor()

            cur.execute("SELECT name FROM users")

            result = cur.fetchall()

            cur.close()

            return result

        def getAllowedTabs(self, role: str) -> list | None:
            cur = self.connection.cursor()

            allowed_tabs = []

            cur.execute(
                "SELECT allowed_tabs FROM roles WHERE name = ?", (role,))

            for line in cur.fetchone()[0].splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)

                    allowed_tabs.append({"id": key, "name": value})

            return allowed_tabs

        def registerNewUser(self, username: str, role: str) -> None:
            cur = self.connection.cursor()

            cur.execute("INSERT INTO users (name, role) VALUES (?, ?)",
                        (username.title(), role.lower()))
            self.connection.commit()
            cur.close()

        def changePassword(self, password: str, userid: str, username: str) -> bool:
            cur = self.connection.cursor()
            cur.execute(
                "SELECT id, name FROM users WHERE id = ? AND name = ?", (userid, username.title()))
            row = cur.fetchone()
            if not row:
                cur.close()
                return False
            cur.execute("UPDATE users set password = ?, changepass = 0 WHERE id = ? AND name = ?",
                        (password, userid, username.title()))
            self.connection.commit()
            cur.close()
            return True

        def getRoles(self) -> list | None:
            cur = self.connection.cursor()

            cur.execute("SELECT name FROM roles")

            result = cur.fetchall()

            cur.close()

            return result
