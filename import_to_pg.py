import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:NPzWzbrhcWcDilGWzpJZcxriHLWvGqVs@sakura.proxy.rlwy.net:11397/railway'

from app import create_app
from extensions import db
from models.cliente import Cliente
from models.admin import Admin
from models.asistencia import Asistencia
from models.pago import Pago
from models.noticia import Noticia
from werkzeug.security import generate_password_hash
from datetime import date, datetime, timedelta
import csv
import io

CSV_DATA = """Marca temporal,ID,Nombre ( como te llamas ),Número Personal,Último pago,Dias,Nombre Completo,Horario frecuente,Dirección de correo electrónico,Fecha de nacimiento,Contacto de Emergencia,"Lesión, enfermedad  o condición médica especial?"
Beca,V001,Bubu,3312381421,Sin registro,,Ashley Jatzeny Ulate Sánchez ,VESPERTINO,,12/9/2014,3322406638,Ninguna
25/06/2026,V002,Ximena,3312616289,Sin registro,,Ximena Landeros,,,25/6/2013,3322246097,
Programa,V003,Gael,3318749598,Sin registro,,Gael Montes Ulloa,VESPERTINO,andresmontesulloa@gmail.com,12/1/2007,3331735763 papa andres montes,Ninguna
Programa,V004,El gordo ,3324494717,Sin registro,,Axel Joshue Flores Castro ,VESPERTINO,ajoshue05@gmail.com,15/3/2004,3322001290 Mama,Ninguna 
Beca,V005,Romario,,Sin registro,,Romario Betancourt,VESPERTINO,,,,
25/06/2026,,Emiliano,3310937385,Sin registro,,Emiliano Puga,,,16/04/2014,3322246097,
29/7/2026,,Jonas ,3339714803,29/7/2026 10:21:59,,Marni Jonas orosio Mendoza ,VESPERTINO,marbijonas@gmail.com,12/10/2009,3327867305 madre Alicia ,Ninguna 
31/7/2026,,Rufus,3318554593,Sin registro,,Luis Fernando Ramos Ramos,VESPERTINO,lr3548807@gmail.com,21/9/2009,3317379920,Ninguna
12/6/2026,V007,Beto,5662998834,20/7/2026 11:16:05,,Alberto Bizarro,MATUTINO,btobiz2@gmail.com,28/6/1974,5662998834,Hernia post quirúrgica 
15/6/2026,,Monserrat,3316995390,Sin registro,,Monserrat Rodríguez,,,,,
14/7/2026,,Mafer,3315578051,14/7/2026 11:12:28,,María Fernanda Rocha Rico,MATUTINO,maryferrocha1@gmail.com,16/11/1984,331536 2801 marido marco ,Ninguna
Visita,,Ximena,3332372664,Sin registro,,Ximena Cuéllar González,MATUTINO,xcuellar766@gmail.com,28/10/2006,3319814156 mamá maria,Ninguna 
13/7/2026 11:40:17,,Sofy,3331767098,Sin registro,,Sofía Berenice Martínez Gómez ,MATUTINO,sofiberemar20@icloud.com,20/3/1996,3331397764 amiga ale,Ninguna
6/7/2026,,Yaquelin,6462869957,6/7/2026 10:35:25,,Ivana Yaquelin,VESPERTINO,ivanayaquelinorozcoalvarez@gmail.com,23/4/2008,9632254293,Ninguna
13/7/2026,,Maciel,3313196101,13/7/2026 11:00:09,,Leonardo Joel trinidad maciel,VESPERTINO,Leonardotrinidadmaciel@gmail.com,13/1/2011,3330059377,Ninguna
Visita,,Caeli,3343211856,Sin registro,,Caeli Enid Bizarro Arechiga ,VESPERTINO,caelarechiga@gmail.com,9/11/2013,3343211856,No
6/7/2026,,Santi,3314354097,6/7/2026 10:36:53,,Jonathan Santiago Velarde caudillo,VESPERTINO,jvelardecaudillo@gmail.com,4/3/2010,3319010690,Ninguna
13/7/2026,,Leonel ,3313089268,13/7/2026 11:04:59,,Leonel Alejandro Urzua Pulido ,VESPERTINO,leonelurzua1010@gmail.com,9/5/1996,3313089268/Eunice pulido/madre,Ninguna 
13/7/2026,,Jesús ,3316388785,13/7/2026 11:05:30,,José de Jesús Rivera Silva,VESPERTINO,jose.srivera110@gmail.com,4/12/2001,3313089268 Eunice Pulido Godínez Tía ,Ninguna
6/7/2026,,Chiwiwi,3321787618,6/7/2026 10:36:02,,Carlos Levi Ramos Ramos,VESPERTINO,carlosleviramosramos@gmail.com,23/2/2007,3317379920,Ninguna
Visita,,Carmen ,3323410612,Sin registro,,Carmen cristera ,VESPERTINO,carmen_mayi_tt@hotmail.com,26/11/1996,3313811233,Ninguna
13/7/2026,,Diana,3320311630,13/7/2026 11:09:41,,Diana Guadalupe Romo Ibarra,VESPERTINO,diana.romo005@icloud.com,14/11/2005,3328238107,Ninguna
13/7/2026,,Ale,3328238107,13/7/2026 11:09:19,,Alexandra osorio,VESPERTINO,ale.osorio07@icloud.com,20/9/2006,3320311630,No
8/7/2026,,Arias ,3311171678,8/7/2026 10:52:32,,Jorge Arias Miran ,MATUTINO,jorgeariasmoran@gmil.com,9/2/1980,Alejandra esposa,Ninguna
8/7/2026,,Nico,3343400341,8/7/2026 10:52:52,,Jorge Nicolás Arias Aviña,MATUTINO,jorgenicolasariasavina@gmail.com,24/11/2012,3311171678,Al 100
14/7/2026,,Kary,3339597452,14/7/2026 11:10:57,,Karina Gonzalez,VESPERTINO,karyprincess1203@gmail.com,3/12/1984,3324111554 esposo Hugo García ,Ninguna
19/6/2026,,Massimo,3324494862,19/6/2026 10:08:43,,Massimo Castillo Torres,MATUTINO,castillomassimo94@gmail.com,3/1/2009,"3331720743, Miriam Torres",Ninguna 
15/7/2026,,Ismael,3326030335,15/7/2026 11:15:35,,Ismael Alejandro Zermeño Moreno,MATUTINO,rojonintendo0@gmail.com,18/11/2011,3334624133 Mayra,Ninguna 
22/6/2026,,Oliver,3310486418,Sin registro,,Oliver García Rubio ,MATUTINO,oliverg.rubio96@gmail.col,9/5/1996,3334034037,No
Visita,,Samuel ,3339812947,Sin registro,,Samuel Bautista Vallejo,VESPERTINO,sambauval@gmail.com,9/9/2006,3311862006 / Mamá,Ninguna
22/7/2026,,Ángel Yahir ,3328092023,Sin registro,,Ángel Yahir Rubio Gomez,,,,,
15/6/2026,,Mauricio,4374733423,15/6/2026 10:14:35,,Mauricio castillo,,,,,
30/6/2026,,Sofia,9632254293,30/6/2026 10:27:36,,Frida sophia Luna Álvarez ,,,,,
7/7/2026,,Meredit,3314836446,7/7/2026 10:44:32,,Meredit Marion Candelas,,,,,
6/7/2026,,Miriam,6681160079,Sin registro,,Miriam Lizbeth Pérez Vázquez ,MATUTINO,,23/8/1994,3111033296 Álvaro ,Ninguna
23/7/2026 20:16:24,,Jordan,3329397231,23/7/2026 21:24:53,,Jordan Alexander Arellano Sandoval ,VESPERTINO,,28/6/2015,3329397231 mamá ,Ninguna
15/6/2026,,,,Sin registro,,Oscar Adrian,,,,,
01/07/2026,,Héctor,3327940150,Sin registro,,Héctor Ruiz Rosales,VESPERTINO,,31/3/2010,,Ninguna
18/06/2026,,Cristian,,Sin registro,,Cristian Rosales,,,,,
25/06/2026,,Alejandra,3322246097,Sin registro,,Alejandra Puga,,,,,
20/07/2026,,Damián,,Sin registro,,,,,,,
30/06/2026,,Ari,,Sin registro,,,,,,,
29/06/2026,,Sofi,,Sin registro,,,,,,,
06/07/2026,,Pablo,3320128619,Sin registro,,Pablo Guzmán,VESPERTINO ,guzmanlunajuanpablo@gmail.com,1/11/2003,3331655090 casa,Ninguna
08/07/2026,,Toño,3313073772,Sin registro,,Antonio betancourt,VESPERTINO,,5/3/1953,,
Visita,,Bruno,,Sin registro,,Bruno Alejandro Anaya Guzmán ,VESPERTINO,,,,
9/7/2026,,Bryan,Pendiente,Sin registro,,Brayan Hernández ,VESPERTINO,,,3315378212 Gabriel ,
9/7/2026,,Dana ,3313816968,Sin registro,,Dana Baltazar ,,,,3315378212 Gabriel,
9/7/2026,,,,Sin registro,,Tadeo Ramez,,,,,
13/7/2026,,Eunice,,Sin registro,,,,,,,
13/7/2026,,Tieso,,Sin registro,,Ángel Oswaldo,,,,,
14/7/2026,,,,Sin registro,,José Padilla ,,,,, """

def parse_date(date_str):
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    for fmt in ['%d/%m/%Y', '%d/%m/%y']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

app = create_app()
with app.app_context():
    print('Connecting to PostgreSQL...')
    print(f'DB: {app.config["SQLALCHEMY_DATABASE_URI"][:50]}...')
    db.create_all()
    print('Tables created!')
    
    total = Cliente.query.count()
    print(f'Existing clients: {total}')
    
    if total > 0:
        print('Database already has data, skipping import.')
    else:
        admin = Admin(
            nombre='Administrador',
            email='admin@gym.com',
            password_hash=generate_password_hash('admin123'),
            rol='superadmin'
        )
        db.session.add(admin)
        
        reader = csv.DictReader(io.StringIO(CSV_DATA))
        next_id_num = 8
        existing_ids = set()
        imported = 0
        
        for row in reader:
            nombre_completo = row.get('Nombre Completo', '').strip()
            if not nombre_completo:
                continue
            
            numero_id = row.get('ID', '').strip()
            if not numero_id or numero_id == 'Pendiente':
                while f'V{next_id_num:03d}' in existing_ids:
                    next_id_num += 1
                numero_id = f'V{next_id_num:03d}'
                next_id_num += 1
            
            if numero_id in existing_ids:
                continue
            
            nickname = row.get('Nombre ( como te llamas )', '').strip()
            telefono = row.get('Número Personal', '').strip()
            if telefono == 'Pendiente':
                telefono = ''
            email = row.get('Dirección de correo electrónico', '').strip()
            fecha_nacimiento = parse_date(row.get('Fecha de nacimiento', ''))
            contacto_emergencia = row.get('Contacto de Emergencia', '').strip()
            lesiones = row.get('Lesión, enfermedad  o condición médica especial?', '').strip()
            
            tipo_membresia_raw = row.get('Marca temporal', '').strip()
            tipo_membresia = None
            if tipo_membresia_raw in ['Beca', 'Programa', 'Normal', 'Visita']:
                tipo_membresia = tipo_membresia_raw
            
            fecha_registro = parse_date(row.get('Marca temporal', ''))
            fecha_inicio = None
            fecha_fin = None
            if fecha_registro and fecha_registro >= date(2026, 1, 1):
                fecha_inicio = fecha_registro
                fecha_fin = fecha_inicio + timedelta(days=60)
            elif tipo_membresia:
                fecha_inicio = date(2026, 6, 25)
                fecha_fin = date(2026, 8, 25)
            
            cliente = Cliente(
                numero_registro=numero_id,
                nombre_completo=nombre_completo,
                nickname=nickname if nickname else nombre_completo.split()[0],
                telefono=telefono if telefono else None,
                email=email if email else None,
                fecha_nacimiento=fecha_nacimiento,
                contacto_emergencia=contacto_emergencia if contacto_emergencia else None,
                lesiones_medicas=lesiones if lesiones else None,
                tipo_membresia=tipo_membresia,
                fecha_inicio_membresia=fecha_inicio,
                fecha_fin_membresia=fecha_fin,
                usuario_login=numero_id,
                password_hash=generate_password_hash('cambiar123'),
                primer_login=True,
                activo=True
            )
            
            db.session.add(cliente)
            existing_ids.add(numero_id)
            imported += 1
            print(f'  {numero_id} - {nombre_completo}')
        
        noticia = Noticia(
            titulo='¡Bienvenidos al Gym Portal!',
            contenido='Ya puedes consultar tu información en línea. Inicia sesión con tu número de registro.',
            activa=True
        )
        db.session.add(noticia)
        
        db.session.commit()
        print(f'\nDone! Imported {imported} clients + 1 admin + 1 noticia')
    
    final = Cliente.query.count()
    print(f'Total clients in PostgreSQL: {final}')
