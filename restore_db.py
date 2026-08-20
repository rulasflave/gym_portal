import psycopg2
import os
import sys

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:NPzWzbrhcWcDilGWzpJZcxriHLWvGqVs@sakura.proxy.rlwy.net:11397/railway')

def restore(filename):
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found")
        return
    
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        statements = []
        current = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('--') or stripped == '':
                continue
            current.append(line)
            if stripped.endswith(';'):
                statements.append('\n'.join(current))
                current = []
        
        total = len(statements)
        success = 0
        
        for i, stmt in enumerate(statements, 1):
            try:
                cur.execute(stmt)
                conn.commit()
                success += 1
            except Exception as e:
                print(f"  Statement {i}: ERROR - {e}")
                conn.rollback()
        
        print(f"\nRestore complete: {success}/{total} statements executed")
    except Exception as e:
        print(f"Error reading backup file: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python restore_db.py <backup_file.sql>")
        sys.exit(1)
    restore(sys.argv[1])
