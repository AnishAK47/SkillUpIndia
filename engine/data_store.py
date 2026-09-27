import sqlite3
class SkillUpStore:
    def __init__(self,path="skillupindia.db"):
        self.path=path
        with sqlite3.connect(path) as c:
            c.execute("CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,target_role TEXT,skills TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
            c.execute("CREATE TABLE IF NOT EXISTS progress(student_id INTEGER,skill TEXT,status TEXT,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(student_id,skill))")
            c.execute("CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,area TEXT,page TEXT,skill TEXT,details TEXT,expected TEXT,issue_url TEXT,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    def add_student(self,n,r,s):
        with sqlite3.connect(self.path) as c:return c.execute("INSERT INTO students(name,target_role,skills) VALUES(?,?,?)",(n,r,", ".join(s))).lastrowid
    def students(self):
        with sqlite3.connect(self.path) as c:return c.execute("SELECT * FROM students ORDER BY id DESC").fetchall()
    def set_progress(self,i,s,st):
        with sqlite3.connect(self.path) as c:c.execute("INSERT INTO progress(student_id,skill,status) VALUES(?,?,?) ON CONFLICT(student_id,skill) DO UPDATE SET status=excluded.status,updated_at=CURRENT_TIMESTAMP",(i,s,st))
    def get_progress(self,i):
        with sqlite3.connect(self.path) as c:return c.execute("SELECT skill,status FROM progress WHERE student_id=?",(i,)).fetchall()
    def add_feedback(self,area,page,skill,details,expected,issue_url=None):
        with sqlite3.connect(self.path) as c:return c.execute("INSERT INTO feedback(area,page,skill,details,expected,issue_url) VALUES(?,?,?,?,?,?)",(area,page,skill,details,expected,issue_url)).lastrowid
    def feedback(self):
        with sqlite3.connect(self.path) as c:return c.execute("SELECT created_at,area,page,skill,details,expected,issue_url FROM feedback ORDER BY id DESC").fetchall()
