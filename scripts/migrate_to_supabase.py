import os
import sys
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Load .env
load_dotenv(override=True)

target_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')

if not target_url or 'sqlite' in target_url:
    print("\n[!] CHƯA CÓ CẤU HÌNH DATABASE SUPABASE!")
    print("Vui lòng cấu hình biến DATABASE_URL trong file .env:")
    print("DATABASE_URL=postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres\n")
    sys.exit(1)

if target_url.startswith("postgres://"):
    target_url = target_url.replace("postgres://", "postgresql://", 1)

print(f"[*] Đang kết nối tới Supabase Database...")

from app import app
from models import db
from sqlalchemy import create_engine, MetaData, Table, select, text

# Set app config to target database
app.config['SQLALCHEMY_DATABASE_URI'] = target_url

with app.app_context():
    print("[*] 1. Khởi tạo schema & các bảng trên Supabase...")
    db.create_all()
    print("[+] Đã tạo cấu trúc các bảng trên Supabase thành công!")

sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'database.db')
if not os.path.exists(sqlite_path):
    # Try current directory
    sqlite_path = os.path.join(os.path.dirname(__file__), '..', 'database.db')

if not os.path.exists(sqlite_path):
    print(f"[!] Không tìm thấy file SQLite để chuyển dữ liệu tại {sqlite_path}. Đã tạo bảng trống trên Supabase.")
    sys.exit(0)

print(f"[*] 2. Đang đọc dữ liệu từ SQLite ({sqlite_path}) để đẩy lên Supabase...")

# Tables in topological dependency order
TABLES_ORDER = [
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

sqlite_engine = create_engine(f'sqlite:///{os.path.abspath(sqlite_path)}')
pg_engine = create_engine(target_url)

sqlite_meta = MetaData()
sqlite_meta.reflect(bind=sqlite_engine)

pg_meta = MetaData()
pg_meta.reflect(bind=pg_engine)

with sqlite_engine.connect() as sqlite_conn, pg_engine.begin() as pg_conn:
    # Disable foreign key checks / truncate if needed or insert in order
    for table_name in TABLES_ORDER:
        if table_name not in sqlite_meta.tables or table_name not in pg_meta.tables:
            continue
            
        s_table = sqlite_meta.tables[table_name]
        p_table = pg_meta.tables[table_name]
        
        # Read all rows from sqlite
        rows = sqlite_conn.execute(select(s_table)).mappings().all()
        if not rows:
            print(f"  - {table_name}: 0 dòng (trống)")
            continue
            
        data = [dict(r) for r in rows]
        
        # Clean up data if necessary for boolean/datetime
        # Insert into PostgreSQL
        try:
            # Clear existing data in table to avoid duplicate primary keys
            pg_conn.execute(text(f'DELETE FROM "{table_name}" CASCADE;'))
        except Exception:
            try:
                pg_conn.execute(text(f'DELETE FROM "{table_name}";'))
            except Exception:
                pass
                
        pg_conn.execute(p_table.insert(), data)
        print(f"  [+] Đã chuyển {len(data)} dòng vào bảng '{table_name}'")
        
        # Reset serial/identity sequence in Postgres for id column
        try:
            seq_sql = f"""
            SELECT setval(pg_get_serial_sequence('"{table_name}"', 'id'), 
                          coalesce(max(id), 1), 
                          max(id) IS NOT null) 
            FROM "{table_name}";
            """
            pg_conn.execute(text(seq_sql))
        except Exception:
            pass

print("\n=======================================================")
print("[THÀNH CÔNG] Toàn bộ database đã được chuyển lên Supabase!")
print("=======================================================\n")
