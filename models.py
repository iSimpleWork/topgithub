import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'github.db')
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建项目主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS github_project (
                    id INTEGER PRIMARY KEY,
                    project_id INTEGER,
                    repo_id TEXT,           
                    name TEXT,
                    full_name TEXT,
                    description TEXT,
                    url TEXT,
                    language TEXT,
                    collect_date DATE,
                    stars INTEGER,
                    forks INTEGER,
                    watchers INTEGER,
                    UNIQUE(project_id),
                    UNIQUE(repo_id) 
                )
            ''')
            
            # 创建历史记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS github_project_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    collect_date DATE,
                    stars INTEGER,
                    forks INTEGER,
                    watchers INTEGER,
                    FOREIGN KEY (project_id) REFERENCES github_project(project_id)
                )
            ''')
            conn.commit() 