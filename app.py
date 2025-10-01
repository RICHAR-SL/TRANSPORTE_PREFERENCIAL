from flask import Flask, render_template, request, jsonify, redirect, url_for, session, Response
import json
import csv
import io
from datetime import datetime
from functools import wraps
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)
app.secret_key = 'senati_secret_key_2025'

# Datos en memoria para almacenar las respuestas
survey_data = []

# Configuración de Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1oO1sB8u0Ou2VsZXimUEgBgK1ejZnFA-HNcfJfT7JaNI'

def get_google_sheet():
    """Conectar con Google Sheets"""
    try:
        # En producción, las credenciales vienen de variables de entorno
        if os.path.exists('credentials.json'):
            creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        else:
            # Para Render: usa variable de entorno
            creds_dict = json.loads(os.environ.get('GOOGLE_CREDENTIALS', '{}'))
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        return sheet
    except Exception as e:
        print(f"Error conectando con Google Sheets: {e}")
        return None

def save_to_google_sheets(data):
    """Guardar datos en Google Sheets"""
    try:
        sheet = get_google_sheet()
        if sheet is None:
            return False
        
        # Obtener el último ID
        all_values = sheet.get_all_values()
        last_id = len(all_values) if len(all_values) > 1 else 1
        
        # Preparar fila
        row = [
            last_id,  # ID
            data.get('nombre1', data.get('studentName', '')),  # Nombre
            data.get('edad', ''),  # Edad
            data.get('lugar', data.get('studentLocation', '')),  # Ubicación
            data.get('transporte', data.get('transport', '')),  # Transporte
            'SENATI',  # Centro (fijo)
            data.get('tiempo_llegada', data.get('travelMinutes', ''))  # Minutos
        ]
        
        # Agregar fila
        sheet.append_row(row)
        print(f"✅ Datos guardados en Google Sheets: {row}")
        return True
    except Exception as e:
        print(f"❌ Error guardando en Google Sheets: {e}")
        return False

# Credenciales de login
USERS = {
    'admin': 'senati2025',
    'director': 'director123',
    'coordinador': 'coord2025',
    'profesor': 'profe456'
}

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta raíz - redirecciona según estado de login
@app.route('/')
def root():
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in USERS and USERS[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Usuario o contraseña incorrectos')
    
    return render_template('login.html')

# Ruta de logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Ruta principal del dashboard (protegida)
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/survey', methods=['POST'])
def save_survey():
    """Endpoint para guardar datos de la encuesta desde Voiceflow"""
    try:
        data = request.get_json()
        
        # Agregar timestamp
        data['timestamp'] = datetime.now().isoformat()
        data['source'] = 'chatbot'
        
        # Guardar en memoria
        survey_data.append(data)
        
        print(f"Datos guardados: {data}")
        
        return jsonify({
            'status': 'success',
            'message': 'Datos guardados correctamente',
            'data': data
        })
    
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/export-csv')
@login_required
def export_csv():
    """Endpoint para exportar datos a CSV"""
    try:
        # Crear CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        headers = ['Nombre', 'Ubicación', 'Edad', 'Transporte', 'Tiempo Llegada', 'Timestamp', 'Fuente']
        writer.writerow(headers)
        
        # Escribir datos
        for record in survey_data:
            row = [
                record.get('nombre1', ''),
                record.get('lugar', ''),
                record.get('edad', ''),
                record.get('transporte', ''),
                record.get('tiempo_llegada', ''),
                record.get('timestamp', ''),
                record.get('source', 'chatbot')
            ]
            writer.writerow(row)
        
        # Preparar respuesta
        output.seek(0)
        csv_data = output.getvalue()
        output.close()
        
        # Crear respuesta con headers para descarga
        response = Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=encuesta_transporte_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
        return response
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error al exportar CSV: {str(e)}'
        }), 500

@app.route('/api/data')
@login_required
def get_data():
    """Endpoint para obtener todos los datos"""
    return jsonify({
        'total_responses': len(survey_data),
        'data': survey_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)