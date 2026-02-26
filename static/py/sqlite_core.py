import re
import sqlite3
import unicodedata
from rapidfuzz import fuzz

from datetime import datetime, date

class init:
    def __init__(self, folder) -> None:
        self.connector = sqlite3.connect(folder + r"\almoxarifado.sqlite", check_same_thread=False)
    
    def log_edit(self, route, method, value_id, code, message, fields_changed, list_values, ip):
        cur = self.connector.cursor()
        cur.execute("""
            INSERT INTO edit_logs
            (route, method, value_id, code, message, fields_changed, list_values, ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (str(route), str(method), str(value_id), str(code), str(message), str(fields_changed), str(list_values), str(ip))
        )
        self.connector.commit()
        cur.close()

    class mails:
        def __init__(self, parent: "init") -> None:
            self.connection = parent.connector
            self.connection: sqlite3.Connection = self.connection
            
        def updatePicture(self, receive_name, receive_date, photo_id, code, status):
            cur = self.connection.cursor()
            try:
                cur.execute(
                    "UPDATE mails SET receive_name = ?, receive_date = ?, photo_id = ?, status = ? WHERE code = ?",
                    (receive_name.title(), receive_date, photo_id, status, code.upper())
                )
                self.connection.commit()
            except Exception as e:
                print(e)
            cur.close()

        def updateReceiver(self, code, receiver, sender):
            cur = self.connection.cursor()
            try:
                cur.execute(
                    "UPDATE mails SET ReceivedOnReceptionBy = ?, SendedOnReceptionBy = ?, LeaveReceptionAt = ?, status = 'almox' WHERE code = ?",
                    (receiver, sender, str(datetime.now().strftime("%d-%m-%Y %H:%M")), code.upper())
                )
                self.connection.commit()
            except Exception as e:
                print(e)
            
            cur.close()

        def update(self, code: str, value: str, column: str):
            cur = self.connection.cursor()
            try:
                cur.execute(
                    f"UPDATE mails SET {column.lower()} = ? WHERE code = ?",
                    (
                    value.title() if column.lower() != "status" else value,
                    code.upper()
                    )
                )
                self.connection.commit()
            except Exception as e:
                print(e)
            
            cur.close()
            
        def register(self, name: str, code: str, fantasy: str, type_: str, priority: str, status: str):
            cur = self.connection.cursor()
            
            def normalize(text):
                if not text:
                    return ""

                text = text.lower()
                text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

                text = re.sub(r'\b(ltda|sa|s\/a|me|eireli|comercio|de|alimentos)\b', '', text)

                text = re.sub(r'[^a-z0-9 ]', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text
            
            try:
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
                    
                    name_norm = normalize(name)

                    best_score = 0
                    best_fantasy = ""

                    for row in known_rows:
                        known_name_norm = normalize(row["name"])
                        score = fuzz.token_set_ratio(name_norm, known_name_norm)

                        if score > best_score:
                            best_score = score
                            best_fantasy = row["fantasy"]

                    if best_score >= threshold:
                        fantasy = best_fantasy
                        
                cur.execute("""
                    INSERT INTO mails (name, code, fantasy, type, priority, status, join_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                        name.title(), 
                        code.upper(), 
                        fantasy.title(),
                        type_.title(), 
                        priority.title(),
                        status,
                        datetime.now().strftime("%Y-%m-%d")
                    )
                )
                self.connection.commit()
            except Exception as e:
                return e

            cur.close()
            return None

        
        def getMails(self, mail_filter, orderBy, orderDirection):
            cur = self.connection.cursor()
        
            if mail_filter:
                # if orderBy == self.temp_orderBy:
                #     self.direction_orderBy = "DESC" if self.direction_orderBy == "ASC" else "ASC"
                # else:
                #     self.temp_orderBy = orderBy
                #     self.direction_orderBy = "DESC"
                cur.execute(
                    f"SELECT * FROM mails WHERE code LIKE ? OR name LIKE ? OR fantasy LIKE ? OR photo_id LIKE ? OR receive_name LIKE ? OR status = ? OR type LIKE ? OR priority LIKE ? ORDER BY {orderBy} {orderDirection}",
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
                correspondences = cur.fetchmany(300)
            else:
                # if orderBy == self.temp_orderBy:
                #     self.direction_orderBy = "DESC" if self.direction_orderBy == "ASC" else "ASC"
                # else:
                #     self.temp_orderBy = orderBy
                #     self.direction_orderBy = "DESC"
                
                cur.execute(f"SELECT * FROM mails ORDER BY {orderBy} {orderDirection}")
                
                correspondences = cur.fetchmany(300)
                
            cur.close()

            return correspondences

        def getTotals(self):
            cur = self.connection.cursor()
            cur.execute("SELECT status, join_date FROM mails")

            rows = cur.fetchall()
            cur.close()
            
            
            today = date.today()
            
            total = 0
            returned = 0
            shipped = 0
            delayed = 0
            
            for status, join_date in rows:
                total += 1

                if status == "returned":
                    returned += 1
                elif status == "shipped":
                    shipped += 1

                if join_date and status in ["almox", "on_reception"]:
                    try:
                        d = datetime.strptime(join_date, "%Y-%m-%d").date()
                        if (today - d).days > 6:
                            delayed += 1
                    except ValueError:
                        pass
            
            return {
                "total": total,
                "returned": returned,
                "shipped": shipped,
                "delayed": delayed
            }
    
    class users:
        def __init__(self, parent: "init") -> None:
            self.connection = parent.connector
        
        
                
    class tools:
        def __init__(self, parent: "init") -> None:
            self.connection = parent.connector
        
        def getTools(self):
            try:
                cur = self.connection.cursor()
                cur.execute("SELECT * FROM tools")
                result = cur.fetchall()
                
                cur.close()
                
                return result
            except Exception as e:
                print(e)
                
        def getMovementsCount(self):
            cur = self.connection.cursor()
            cur.execute("SELECT MAX(id) FROM tools_movements")
            
            count: int = cur.fetchone()[0]
            
            cur.close()
            return 1 if count is None else count + 1
        
        def setToolMissing(self, code: str):
            try:
                cur = self.connection.cursor()
                cur.execute("UPDATE tools set id_movements = NULL WHERE (id = ? OR nome LIKE ?)", 
                    (code, "%" + code + "%")
                )
                
                self.connection.commit()
                cur.close()
            except Exception as e:
                print(e)
                
        def setToolCasualty(self, code: str):
            try:
                cur = self.connection.cursor()
                cur.execute("UPDATE tools set status = 'Casualty' WHERE (id = ? OR nome LIKE ?)", 
                    (code, "%" + code + "%")
                )
                
                self.connection.commit()
                cur.close()
            except Exception as e:
                print(e)
                
        def searchTools(self, code: str):
            cur = self.connection.cursor()
            
            if not code:
                cur.execute("SELECT * FROM tools")
                result = cur.fetchall()
            else:
                cur.execute("SELECT * FROM tools WHERE id LIKE '%' || ? || '%' OR nome LIKE '%' || ? || '%' OR id_alternative LIKE '%' || ? || '%'", (code, code, code))
                result = cur.fetchone()

            cur.close()
            return result
        
        def updateTools(self, tool_id, column, value) -> None:
            cur = self.connection.cursor()
            
            cur.execute(f"UPDATE tools SET {column} = ? WHERE id = ?", (value, tool_id))
            self.connection.commit()
            
            cur.close()
        
        def addMovement(self, tool_id, item, day, month, year, time, movement_type):
            cur = self.connection.cursor()
            
            cur.execute("INSERT INTO tools_movements (id, item, day, month, year, time, type) VALUES (?, ?, ?, ?, ?, ?, ?)", (str(tool_id).zfill(6), item, day, month, year, time, movement_type))
            cur.execute("SELECT * FROM tools_movements WHERE id = ?", (str(tool_id).zfill(6),))
            result = cur.fetchone()
            
            self.connection.commit()
            cur.close()

            return result 

        def getAllLoanedItems(self):
            cur = self.connection.cursor()
            
            cur.execute("SELECT * FROM tools WHERE status = 'Emprestado' OR status = 'Casualty'")
            results = cur.fetchall()
            
            cur.close()
            return results

        def getAllMovements(self):
            cur = self.connection.cursor()
            
            cur.execute("SELECT * FROM tools_movements ORDER BY id DESC")
            results = cur.fetchall()
            
            cur.close()
            return results