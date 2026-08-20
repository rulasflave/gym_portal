import psycopg2
import json
import os
from datetime import datetime, date

DB_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:NPzWzbrhcWcDilGWzpJZcxriHLWvGqVs@sakura.proxy.rlwy.net:11397/railway')

TABLES = [
    'clientes',
    'asistencias',
    'pagos',
    'noticias',
    'configuracion_recordatorio',
    'recordatorios_enviados',
    'admin',
]

def export_value(val, col_type):
    if val is None:
        return 'NULL'
    if isinstance(val, bool):
        return 'TRUE' if val else 'FALSE'
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (datetime, date)):
        return f"'{val.isoformat()}'"
    if isinstance(val, bytes):
        import base64
        return f"decode('{base64.b64encode(val).decode()}', 'base64')"
    return f"'{str(val).replace(chr(39), chr(39)+chr(39))}'"

def backup():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{timestamp}.sql'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"-- Backup Gym Portal - {datetime.now().isoformat()}\n")
        f.write(f"-- Database backup for restoration\n\n")
        
        for table in TABLES:
            try:
                cur.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                if not cur.fetchone()[0]:
                    continue
                    
                cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}' ORDER BY ordinal_position")
                columns = cur.fetchall()
                col_names = [c[0] for c in columns]
                col_types = {c[0]: c[1] for c in columns}
                
                cur.execute(f"SELECT * FROM {table}")
                rows = cur.fetchall()
                
                if not rows:
                    continue
                
                f.write(f"\n-- Table: {table} ({len(rows)} rows)\n")
                f.write(f"DELETE FROM {table};\n")
                
                for row in rows:
                    vals = []
                    for i, val in enumerate(row):
                        vals.append(export_value(val, col_types.get(col_names[i], 'text')))
                    cols_str = ', '.join(col_names)
                    vals_str = ', '.join(vals)
                    f.write(f"INSERT INTO {table} ({cols_str}) VALUES ({vals_str});\n")
                
                print(f"  {table}: {len(rows)} rows exported")
            except Exception as e:
                print(f"  {table}: ERROR - {e}")
                conn.rollback()
        
        f.write("\n-- End of backup\n")
    
    cur.close()
    conn.close()
    
    size = os.path.getsize(filename)
    print(f"\nBackup saved: {filename} ({size:,} bytes)")
    return filename

if __name__ == '__main__':
    print("=== Gym Portal Database Backup ===\n")
    backup()
