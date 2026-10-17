import sqlite3, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app
from models import db

conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db'))
cursor = conn.cursor()

with app.app_context():
    for t_name, table in db.metadata.tables.items():
        cursor.execute(f'PRAGMA table_info("{t_name}")')
        sqlite_cols = {r[1]: (r[2], r[3]) for r in cursor.fetchall()} # name: (type, notnull)
        model_cols = {c.name: (str(c.type), c.nullable) for c in table.columns}
        
        diff_sqlite_not_model = set(sqlite_cols.keys()) - set(model_cols.keys())
        diff_model_not_sqlite = set(model_cols.keys()) - set(sqlite_cols.keys())
        
        print(f"=== TABLE {t_name} ===")
        if diff_sqlite_not_model:
            print(f"  In SQLite but NOT in Model: {diff_sqlite_not_model}")
        if diff_model_not_sqlite:
            print(f"  In Model but NOT in SQLite: {diff_model_not_sqlite}")
            
        # Check nullable mismatches where sqlite has NULL but model has NOT NULL
        for col_name in set(sqlite_cols.keys()) & set(model_cols.keys()):
            col = table.columns[col_name]
            cursor.execute(f'SELECT COUNT(*) FROM "{t_name}" WHERE "{col_name}" IS NULL')
            null_count = cursor.fetchone()[0]
            if null_count > 0 and not col.nullable and not col.primary_key:
                print(f"  [!] Column {col_name} has {null_count} NULL rows in SQLite but model has nullable=False!")
