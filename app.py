import io
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Configurar matplotlib para evitar problemas
plt.ioff()  # Turn off interactive mode

BASE_DIR = os.path.join(os.path.dirname(__file__), "data")

CSV_PATH = os.path.join(BASE_DIR, "respuestas_datos.csv")

COLUMNS = [
    "id","nombre","apellido","escuela","transporte",
    "tiempo_encuesta","comentario","origen","distrito","duracion_encuesta_seg"
]

app = Flask(__name__, static_folder="static", template_folder="templates")

# -------------------------
# Auxiliares
# -------------------------
def load_df():
    if not os.path.exists(CSV_PATH):
        os.makedirs(BASE_DIR, exist_ok=True)
        return pd.DataFrame(columns=COLUMNS)
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8")
    return df

def save_df(df):
    os.makedirs(BASE_DIR, exist_ok=True)
    df.to_csv(CSV_PATH, sep=";", encoding="utf-8", index=False)

def filter_df(df, escuela=None, fecha=None, transporte=None):
    if escuela:
        df = df[df["escuela"].astype(str).str.lower() == escuela.lower()]
    if transporte:
        df = df[df["transporte"].astype(str).str.lower() == transporte.lower()]
    if fecha:
        df = df[df["tiempo_encuesta"].astype(str).str.startswith(fecha)]
    return df

# -------------------------
# Rutas
# -------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/submit", methods=["POST"])
def submit():
    try:
        data = request.json or request.form
        df = load_df()
        new_row = {
            "id": str(uuid.uuid4())[:8],
            "nombre": data.get("nombre","").strip(),
            "apellido": data.get("apellido","").strip(),
            "escuela": data.get("escuela","").strip(),
            "transporte": data.get("transporte","").strip(),
            "tiempo_encuesta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "comentario": data.get("comentario","").strip(),
            "origen": data.get("origen","Web"),
            "distrito": "Huancayo",
            "duracion_encuesta_seg": 0
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_df(df)
        return jsonify({"status":"ok","id": new_row["id"]}), 201
    except Exception as e:
        print(f"Error en submit: {e}")
        return jsonify({"status":"error","message":str(e)}), 500

@app.route("/api/data")
def api_data():
    try:
        escuela = request.args.get("escuela")
        fecha = request.args.get("fecha")
        transporte = request.args.get("transporte")
        df = load_df()
        df_filtered = filter_df(df, escuela, fecha, transporte)
        total = len(df)
        counts = df_filtered["transporte"].fillna("No especificado").value_counts().to_dict()
        escuelas = sorted(df["escuela"].dropna().unique().tolist())
        fechas = sorted(df["tiempo_encuesta"].dropna().unique().tolist())
        registros = df_filtered.tail(20).iloc[::-1].to_dict(orient="records")
        return jsonify({
            "total": total,
            "counts": {str(k): int(v) for k,v in counts.items()},
            "escuelas": escuelas,
            "fechas": fechas,
            "registros": registros
        })
    except Exception as e:
        print(f"Error en api_data: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/export")
def api_export():
    try:
        escuela = request.args.get("escuela")
        fecha = request.args.get("fecha")
        transporte = request.args.get("transporte")
        df = load_df()
        df = filter_df(df, escuela, fecha, transporte)
        buf = io.StringIO()
        df.to_csv(buf, sep=";", encoding="utf-8", index=False)
        buf.seek(0)
        return send_file(io.BytesIO(buf.getvalue().encode("utf-8")),
                         mimetype="text/csv", as_attachment=True, download_name="respuestas_export.csv")
    except Exception as e:
        print(f"Error en export: {e}")
        return jsonify({"error": str(e)}), 500

# -------------------------
# Funciones de gráficos más robustas
# -------------------------
def create_error_image(message="Error al generar gráfico"):
    """Crea una imagen simple con mensaje de error"""
    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('white')
    ax.text(0.5, 0.5, message, horizontalalignment='center', 
            verticalalignment='center', transform=ax.transAxes, 
            fontsize=14, color='#dc3545')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return fig

def create_pie_chart(data, title):
    """Crear gráfico de pastel"""
    try:
        if not data or sum(data.values()) == 0:
            return create_error_image("No hay datos para mostrar")
        
        fig, ax = plt.subplots(figsize=(8, 6))
        fig.patch.set_facecolor('white')
        
        labels = list(data.keys())
        values = list(data.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
        
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90,
               colors=colors[:len(labels)])
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.axis('equal')
        
        return fig
    except Exception as e:
        print(f"Error en pie chart: {e}")
        return create_error_image(f"Error: {str(e)}")

def create_bar_chart(data, title):
    """Crear gráfico de barras"""
    try:
        if not data or sum(data.values()) == 0:
            return create_error_image("No hay datos para mostrar")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        labels = list(data.keys())
        values = list(data.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
        
        bars = ax.bar(labels, values, color=colors[:len(labels)])
        ax.set_ylabel('Cantidad')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        # Agregar valores encima de las barras
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom')
        
        # Rotar etiquetas si es necesario
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        
        ax.grid(True, alpha=0.3, axis='y')
        
        return fig
    except Exception as e:
        print(f"Error en bar chart: {e}")
        return create_error_image(f"Error: {str(e)}")

def create_line_chart(data, title):
    """Crear gráfico de líneas"""
    try:
        if not data or sum(data.values()) == 0:
            return create_error_image("No hay datos para mostrar")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('white')
        
        labels = list(data.keys())
        values = list(data.values())
        
        ax.plot(labels, values, marker='o', linewidth=2, markersize=8, color='#45B7D1')
        ax.set_ylabel('Cantidad')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        ax.grid(True, alpha=0.3)
        
        # Agregar valores en los puntos
        for i, v in enumerate(values):
            ax.annotate(str(v), (labels[i], v), textcoords="offset points", 
                       xytext=(0,10), ha='center')
        
        # Rotar etiquetas si es necesario
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        
        return fig
    except Exception as e:
        print(f"Error en line chart: {e}")
        return create_error_image(f"Error: {str(e)}")

def create_comparison_chart(data_general, data_filtered):
    """Crear gráfico comparativo"""
    try:
        all_labels = set(data_general.keys()) | set(data_filtered.keys())
        if not all_labels:
            return create_error_image("No hay datos para comparar")
        
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('white')
        
        labels = sorted(all_labels)
        values_general = [data_general.get(lbl, 0) for lbl in labels]
        values_filtered = [data_filtered.get(lbl, 0) for lbl in labels]
        
        x = range(len(labels))
        width = 0.35
        
        bars1 = ax.bar([i - width/2 for i in x], values_general, width, 
                      label='General', color='#45B7D1', alpha=0.8)
        bars2 = ax.bar([i + width/2 for i in x], values_filtered, width, 
                      label='Filtrado', color='#FF6B6B', alpha=0.8)
        
        # Agregar valores encima de las barras
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Medio de Transporte')
        ax.set_ylabel('Cantidad')
        ax.set_title('Comparación: General vs Filtrado', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # Rotar etiquetas si es necesario
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        
        return fig
    except Exception as e:
        print(f"Error en comparison chart: {e}")
        return create_error_image(f"Error: {str(e)}")
# Agregar esta ruta a tu app.py después de las otras rutas

@app.route("/api/voiceflow-submit", methods=["POST"])
def voiceflow_submit():
    """Endpoint específico para recibir datos de Voiceflow"""
    try:
        data = request.json
        print(f"Datos recibidos de Voiceflow: {data}")
        
        df = load_df()
        new_row = {
            "id": str(uuid.uuid4())[:8],
            "nombre": data.get("nombre", "").strip(),
            "apellido": data.get("apellido", "").strip(),
            "escuela": data.get("escuela", "").strip(),
            "transporte": data.get("transporte", "").strip(),
            "tiempo_encuesta": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "comentario": data.get("comentario", "").strip(),
            "origen": "Chatbot",  # Identificar que viene de Voiceflow
            "distrito": "Huancayo",
            "duracion_encuesta_seg": 0
        }
        
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_df(df)
        
        return jsonify({
            "status": "ok",
            "id": new_row["id"],
            "message": "Respuesta guardada correctamente"
        }), 201
        
    except Exception as e:
        print(f"Error en voiceflow_submit: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# También agregar soporte para CORS si es necesario
from flask_cors import CORS
# Agregar después de crear la app
CORS(app)
@app.route("/api/chart/<chart_type>.png")
def api_chart(chart_type):
    """Generar gráficos de forma más robusta"""
    try:
        # Obtener parámetros
        escuela = request.args.get("escuela")
        fecha = request.args.get("fecha") 
        transporte = request.args.get("transporte")
        compare = request.args.get("compare", "0") == "1"
        
        print(f"Generando gráfico: {chart_type}, compare: {compare}")
        print(f"Filtros: escuela={escuela}, fecha={fecha}, transporte={transporte}")
        
        # Cargar datos
        df = load_df()
        
        # Si no hay datos, crear datos de ejemplo
        if df.empty:
            sample_data = {
                'id': ['001', '002', '003'],
                'nombre': ['Juan', 'María', 'Carlos'],
                'apellido': ['Pérez', 'García', 'López'],
                'escuela': ['SENATI', 'SENATI', 'TECSUP'],
                'transporte': ['Bus', 'Bicicleta', 'Auto'],
                'tiempo_encuesta': ['24/09/2025 10:00', '24/09/2025 11:00', '24/09/2025 12:00'],
                'comentario': ['', '', ''],
                'origen': ['Web', 'Web', 'Chatbot'],
                'distrito': ['Huancayo', 'Huancayo', 'Huancayo'],
                'duracion_encuesta_seg': [0, 0, 0]
            }
            df = pd.DataFrame(sample_data)
        
        # Obtener datos
        df_filtered = filter_df(df, escuela, fecha, transporte)
        counts_filtered = df_filtered["transporte"].fillna("No especificado").value_counts().to_dict()
        counts_general = df["transporte"].fillna("No especificado").value_counts().to_dict()
        
        # Generar gráfico según el tipo
        if compare:
            fig = create_comparison_chart(counts_general, counts_filtered)
        else:
            # Decidir qué datos usar
            if escuela or fecha or transporte:
                data = counts_filtered
                title_suffix = " (Filtrado)"
            else:
                data = counts_general
                title_suffix = ""
            
            title = f"Distribución de Medios de Transporte{title_suffix}"
            
            # Crear gráfico según tipo
            if chart_type == "pie":
                fig = create_pie_chart(data, title)
            elif chart_type == "bar":
                fig = create_bar_chart(data, title)
            elif chart_type == "line":
                fig = create_line_chart(data, title)
            else:
                fig = create_error_image(f"Tipo de gráfico no válido: {chart_type}")
        
        # Guardar en buffer
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close(fig)  # Importante: cerrar la figura para liberar memoria
        buf.seek(0)
        
        # Crear respuesta
        response = send_file(buf, mimetype="image/png")
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        print(f"Error crítico en api_chart: {e}")
        # En caso de error total, crear imagen de error
        try:
            fig = create_error_image(f"Error crítico: {str(e)}")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            return send_file(buf, mimetype="image/png")
        except:
            # Si todo falla, devolver error HTTP
            return jsonify({"error": f"Error al generar gráfico: {str(e)}"}), 500

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    print("Iniciando aplicación Flask...")
    print(f"Directorio de datos: {BASE_DIR}")
    print(f"Archivo CSV: {CSV_PATH}")  
    app.run(debug=True, host='127.0.0.1', port=5000)