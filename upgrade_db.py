import sqlite3

def upgrade_db():
    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()
    
    try: c.execute("ALTER TABLE councils ADD COLUMN decision_number VARCHAR(100)")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE councils ADD COLUMN meeting_date DATE")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE councils ADD COLUMN meeting_time TIME")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE councils ADD COLUMN location VARCHAR(255)")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE councils ADD COLUMN decision_file_url VARCHAR(255)")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE council_members ADD COLUMN role VARCHAR(50) DEFAULT 'member'")
    except Exception as e: print(e)
    
    try: c.execute("ALTER TABLE topics ADD COLUMN council_id INTEGER")
    except Exception as e: print(e)
    
    conn.commit()
    conn.close()
    print("DB Upgrade Complete")

if __name__ == '__main__':
    upgrade_db()
