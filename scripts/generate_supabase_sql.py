import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db')
if not os.path.exists(sqlite_path):
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')

conn = sqlite3.connect(sqlite_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Order of tables
TABLES = [
    'users',
    'batches',
    'councils',
    'council_members',
    'groups',
    'group_members',
    'topics',
    'topic_registrations',
    'milestones',
    'progresses',
    'submissions',
    'meetings',
    'messages',
    'notifications',
    'documents',
    'rubrics',
    'evaluations',
    'skills',
    'achievements',
    'experiences'
]

# Get existing tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
existing_tables = set(r[0] for r in cursor.fetchall())

output_sql_path = os.path.join(os.path.dirname(__file__), '..', 'supabase_schema_and_data.sql')

# Generate the DDL using SQLAlchemy Postgres dialect
from models import db
from app import app
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
from sqlalchemy import Boolean

with app.app_context():
    ddl_statements = []
    # Drop statements
    for table_name in reversed(TABLES):
        if table_name in db.metadata.tables:
            ddl_statements.append(f'DROP TABLE IF EXISTS "{table_name}" CASCADE;')
            
    ddl_sql = "\n".join(ddl_statements) + "\n\n"
    
    # Create statements
    for table_name in TABLES:
        if table_name in db.metadata.tables:
            table = db.metadata.tables[table_name]
            stmt = CreateTable(table).compile(dialect=postgresql.dialect())
            ddl_sql += str(stmt).strip() + ";\n\n"

# Now generate INSERT statements from sqlite
insert_sql = ""
for table_name in TABLES:
    if table_name not in existing_tables:
        continue
    cursor.execute(f'SELECT * FROM "{table_name}"')
    rows = cursor.fetchall()
    if not rows:
        continue
    
    table_obj = db.metadata.tables.get(table_name)
    cols = [d[0] for d in cursor.description]
    col_str = ', '.join([f'"{c}"' for c in cols])
    
    insert_sql += f"\n-- Dữ liệu bảng {table_name} ({len(rows)} dòng)\n"
    for r in rows:
        vals = []
        for c in cols:
            val = r[c]
            col_col = table_obj.columns.get(c) if table_obj is not None else None
            is_bool = isinstance(getattr(col_col, 'type', None), Boolean)
            
            if val is None:
                vals.append("NULL")
            elif is_bool:
                if val in (1, '1', True, 'true', 'True'):
                    vals.append("TRUE")
                else:
                    vals.append("FALSE")
            elif isinstance(val, bool):
                vals.append("TRUE" if val else "FALSE")
            elif isinstance(val, (int, float)):
                vals.append(str(val))
            else:
                s_val = str(val).replace("'", "''")
                vals.append(f"'{s_val}'")
        insert_sql += f'INSERT INTO "{table_name}" ({col_str}) VALUES ({", ".join(vals)});\n'
    
    # Sequence reset for Postgres
    insert_sql += f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM \"{table_name}\";\n"

full_sql = f"""-- ==========================================================
-- SUPABASE POSTGRESQL SCHEMA & INITIAL DATA
-- HOU-S-RIMS Management System
-- Hướng dẫn: Copy toàn bộ nội dung file này và paste vào
-- Supabase Dashboard -> SQL Editor -> Nhấn 'Run'
-- ==========================================================

-- 1. XÓA CÁC BẢNG CŨ (NẾU CÓ)
{ddl_sql}

-- 2. INSERT DỮ LIỆU BAN ĐẦU
{insert_sql}

-- ==========================================================
-- HOÀN TẤT TẠO BẢNG VÀ NẠP DỮ LIỆU LÊN SUPABASE
-- ==========================================================
"""

with open(output_sql_path, 'w', encoding='utf-8') as f:
    f.write(full_sql)

print(f"Generated SQL script at: {output_sql_path}")
print(f"File size: {os.path.getsize(output_sql_path)} bytes")
