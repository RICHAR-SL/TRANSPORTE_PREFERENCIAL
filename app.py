from flask import Flask, render_template_string, request, jsonify
import json
import csv
import io
from datetime import datetime

app = Flask(__name__)

# Datos en memoria para almacenar las respuestas
survey_data = []

# Leer el archivo HTML
def load_html():
    try:
        with open('transporte.html', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return "<h1>Error: archivo transporte.html no encontrado</h1>"

@app.route('/')
def index():
    html_content = load_html()
    return render_template_string(html_content)

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
        from flask import Response
        
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
def get_data():
    """Endpoint para obtener todos los datos"""
    return jsonify({
        'total_responses': len(survey_data),
        'data': survey_data
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)