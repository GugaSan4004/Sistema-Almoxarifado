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
            self.AllowedTypes = [
                "Caixa",
                "Carta",
                "Pacote"
            ]
            self.AllowedPriority = [
                "Simples",
                "Judicial"
            ]

            cur = self.connection.cursor()
            cur.execute("PRAGMA table_info(mails)")

            tableColumns = cur.fetchall()

            self.AllowedCols = [coluna[1] for coluna in tableColumns]

            cur.close()

            self.folder = parent.folder

        def updateMail(self,
                       values: dict,
                       search: dict,
                       search_logic: str = "AND"
                       ) -> None:
            cur = self.connection.cursor()

            set_clause = ", ".join([f"{k} = ?" for k in values.keys()])
            set_values = list(values.values())

            where_clause = ""
            where_values = []

            if search:
                logic = search_logic.upper()

            if logic not in ["AND", "OR"]:
                logic = "AND"

            where_clause = " WHERE " + \
                f" {logic} ".join([f"{k} = ?" for k in search.keys()])
            where_values = list(search.values())

            sql = f"UPDATE mails SET {set_clause}{where_clause}"
            cur.execute(sql, set_values + where_values)

            self.connection.commit()

            cur.close()

        def registerPickup(self,
                           code: str,
                           pickupuser: str,
                           responsableuser: str
                           ) -> None:
            cur = self.connection.cursor()

            cur.execute(
                "SELECT status FROM mails WHERE code = ?",
                (
                    code.upper(),
                )
            )

            result = cur.fetchone()

            if not result:
                raise Exception("Correspondencia não encontrada!")

            if result[0] != "reception":
                raise Exception(
                    "Correspondencia não disponivel para retirada!")

            cur.execute(
                "UPDATE mails set receivedOnReceptionBy = ?, sendedOnReceptionBy = ?, status = ?, leaveReceptionAt = ? WHERE code = ?",
                (
                    pickupuser.lower(),
                    responsableuser.lower(),
                    "almox",
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    code.upper()
                )
            )

            self.connection.commit()
            cur.close()

            return

        def registerNewMail(self,
            sender: str,
            code: str,
            fantasy: str,
            _type: str,
            priority: str,
            user_id: int
        ) -> None:
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
                """)

                known_rows = [
                    {
                        "name": n, 
                        "fantasy": f
                    }
                    for n, f in cur.fetchall()
                ]

                name_norm = normalize(sender)

                best_score = 0
                best_fantasy = ""

                for row in known_rows:
                    known_name_norm = normalize(row["name"])
                    score = fuzz.token_set_ratio(
                        s1=name_norm,
                        s2=known_name_norm
                    )

                    if score > best_score:
                        best_score = score
                        best_fantasy = row["fantasy"]

                if best_score >= threshold:
                    fantasy = best_fantasy
                else:
                    fantasy = "---"

            if _type.title() not in self.AllowedTypes:
                raise Exception("Tipo de correspondencia invalida!")

            if priority.title() not in self.AllowedPriority:
                raise Exception("Prioridade de correspondencia invalida!")

            cur.execute("""
                INSERT INTO mails (name, code, fantasy, type, priority, joinDate, registeredBy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    sender.title(),
                    code.upper(),
                    fantasy.title(),
                    _type.title(),
                    priority.title(),
                    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    user_id
                )
            )

            self.connection.commit()

            cur.close()
            
            return

        def getMails(self,
                     mail_filter: str | dict = "",
                     orderBy: str = "",
                     orderDirection: str = "ASC",
                     fetchOne: bool = False,
                     column: str = ""
                     ) -> list:
            cur = self.connection.cursor()

            if orderDirection.upper() not in self.AllowedOrderDirection:
                orderDirection = "ASC"

            if orderBy not in self.AllowedCols:
                orderBy = "id"

            if mail_filter:
                if mail_filter == "delayed":
                    cur.execute(f"""
                        SELECT * FROM mails 
                        WHERE((priority = 'Simples' AND (julianday('now') - julianday(joinDate || ':00')) * 24 >= 120) OR 
                        (priority = 'Judicial' AND (julianday('now') - julianday(joinDate || ':00')) * 24 >= 72)) AND 
                        (status = 'almox' OR status = 'reception') 
                        ORDER BY {orderBy} {orderDirection}
                    """)
                elif mail_filter == "returned":
                    cur.execute(
                        f"""
                            SELECT * FROM mails WHERE status = ? OR status = ? 
                            ORDER BY {orderBy} {orderDirection}
                        """,
                        (
                            "returned",
                            "pre_returned"
                        )
                    )
                elif type(mail_filter) == dict:
                    correspondences = []
                    for mailCode, reason in mail_filter.items():
                        cur.execute(
                            """
                                SELECT * FROM mails WHERE code = ?
                            """,
                            (
                                mailCode,
                            )
                        )
                        correspondences.append(
                            cur.fetchone() + (reason,)
                        )
                    cur.close()
                    return correspondences
                else:
                    if column != "":
                        cur.execute(
                            f"""
                                SELECT * FROM mails WHERE {column} = ? 
                                ORDER BY {orderBy} {orderDirection}
                            """,
                            (
                                mail_filter,
                            )
                        )
                    else:
                        cur.execute(
                            f"""
                                SELECT * FROM mails WHERE 
                                code LIKE ? OR 
                                name LIKE ? OR 
                                fantasy LIKE ? OR 
                                pictureId LIKE ? OR 
                                deliveryDetail LIKE ? OR 
                                status = ? OR 
                                type LIKE ? OR 
                                priority LIKE ? 
                                ORDER BY {orderBy} {orderDirection}
                            """,
                            (
                                "%" + mail_filter.upper() + "%",
                                "%" + mail_filter.title() + "%",
                                "%" + mail_filter.title() + "%",
                                "%" + mail_filter.upper() + "%",
                                "%" + mail_filter + "%",
                                mail_filter.lower(),
                                "%" + mail_filter.title() + "%",
                                "%" + mail_filter.title() + "%"
                            )
                        )
            else:
                cur.execute(
                    f"""
                        SELECT * FROM mails 
                        ORDER BY {orderBy} {orderDirection}
                    """
                )

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

        def getUserData(self,
                        name: str = None,
                        id: str = None
                        ) -> dict | None:
            cur = self.connection.cursor()

            user_data = {
                "id": None,
                "name": None,
                "password": None,
                "role": None,
                "theme": None,
                "status": None
            }

            allowed_tabs = []

            if name and id:
                cur.execute(
                    "SELECT * FROM users WHERE name LIKE ? OR id = ?",
                    (
                        name.title() + "%",
                        id
                    )
                )
            elif name:
                cur.execute(
                    "SELECT * FROM users WHERE name LIKE ?",
                    (
                        name.title() + "%",
                    )
                )
            elif id:
                cur.execute(
                    "SELECT * FROM users WHERE id = ?",
                    (
                        id,
                    )
                )
            else:
                cur.close()
                return

            result = cur.fetchone()

            if not result:
                cur.close()
                return

            user_data["id"] = result[0]
            user_data["name"] = result[1]
            user_data["password"] = result[2]
            user_data["theme"] = result[4]
            user_data["status"] = result[5]

            cur.execute(
                "SELECT name FROM roles WHERE id = ?",
                (
                    result[3],
                )
            )

            user_data["role"] = cur.fetchone()[0]

            allowed_tabs = self.getAllowedTabs(
                role_id=result[3]
            )

            user_data["allowed_tabs"] = allowed_tabs

            cur.close()

            return user_data

        def getUsernames(self,
                         inactives: bool = True
                         ) -> list:
            cur = self.connection.cursor()

            if inactives:
                cur.execute(
                    """
                        SELECT name FROM users
                    """
                )
            else:
                cur.execute(
                    """
                        SELECT name FROM users WHERE status >= 0
                    """
                )

            result = cur.fetchall()

            cur.close()

            return result

        def getAllowedTabs(self,
                           role_id: str
                           ) -> list | None:
            cur = self.connection.cursor()

            cur.execute(
                """
                SELECT t.id, t.tab_name 
                FROM tabs t
                JOIN role_tabs rt ON t.id = rt.tab_id
                WHERE rt.role_id = ?
                ORDER BY t.rowid ASC
                """,
                (role_id,)
            )

            rows = cur.fetchall()

            cur.close()

            return [{"id": row[0], "name": row[1]} for row in rows]

        def registerNewUser(self,
                            username: str,
                            password: str
                            ) -> None:
            cur = self.connection.cursor()

            cur.execute(
                """
                    INSERT INTO users (name, password) VALUES (?, ?)
                """,
                (
                    username.title(),
                    password
                )
            )

            self.connection.commit()
            cur.close()

            return

        def changePassword(self,
                           password: str,
                           userid: str
                           ) -> bool:
            cur = self.connection.cursor()

            cur.execute(
                """
                    SELECT id, name FROM users WHERE id = ?
                """,
                (
                    userid,
                )
            )

            row = cur.fetchone()

            if not row:
                cur.close()
                return False

            cur.execute(
                """
                    UPDATE users set password = ?, status = 0 WHERE id = ?
                """,
                (
                    password,
                    userid
                )
            )

            self.connection.commit()
            cur.close()

            return True

        def getRoles(self
                     ) -> list | None:
            cur = self.connection.cursor()

            cur.execute("SELECT name FROM roles")

            result = cur.fetchall()

            cur.close()

            return result

        def updateUser(self,
                       id: str,
                       name: str,
                       role: str = None,
                       status: int = None
                       ) -> None:
            # -2: Disabled
            # -1: New Account
            # 0: Normal
            # 1: Change Password

            cur = self.connection.cursor()

            set_parts = []
            values = []

            if role is not None:
                set_parts.append("role = ?")
                values.append(role.lower())

            if status is not None:
                set_parts.append("status = ?")
                values.append(status)

            if set_parts:
                set_clause = ", ".join(set_parts)
                sql = f"UPDATE users SET {set_clause} WHERE id = ? AND name = ?"
                values.extend([id, name])

                cur.execute(
                    sql,
                    values
                )

            self.connection.commit()
            cur.close()

            return
