import io
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file, Response

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Configurar matplotlib para evitar problemas
plt.ioff()  # Turn off interactive mode

# --- GOOGLE SHEETS CONFIG ---
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "service_account_credentials.json"  # archivo JSON de credenciales
SPREADSHEET_ID = "1oO1sB8u0Ou2VsZXimUEgBgK1ejZnFA-HNcfJfT7JaNI"   # tu hoja compartida

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).sheet1  # usar la primera hoja

# --- FIN Google Sheets ---

COLUMNS = [
    "id","nombre","apellido","escuela","transporte",
    "tiempo_encuesta","comentario","origen","distrito","duracion_encuesta_seg"
]

app = Flask(__name__, static_folder="static", template_folder="templates")

# -------------------------
# Auxiliares adaptados a Google Sheets
# -------------------------
def load_df():
    """Leer toda la hoja de Google Sheets como DataFrame"""
    try:
        values = sheet.get_all_values()
        if not values or len(values) < 2:
            return pd.DataFrame(columns=COLUMNS)
        df = pd.DataFrame(values[1:], columns=values[0])
        return df
    except Exception as e:
        print("Error en load_df:", e)
        return pd.DataFrame(columns=COLUMNS)

def append_row_to_sheet(row_dict):
    """Agregar una fila nueva a la hoja de Google Sheets"""
    try:
        header = sheet.row_values(1)
        # asegurar que todas las columnas existan
        values = [row_dict.get(col, "") for col in header]
        sheet.append_row(values)
    except Exception as e:
        print("Error en append_row_to_sheet:", e)

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
        append_row_to_sheet(new_row)
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
            "counts": {str(k): int(v) for k, v in counts.items()},
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
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=respuestas_export.csv"})
    except Exception as e:
        print(f"Error en api_export: {e}")
        return jsonify({"error": str(e)}), 500

# -------------------------
# Funciones de gráficos (sin cambios)
# -------------------------
def create_error_image(message="Error al generar gráfico"):
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
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        return fig
    except Exception as e:
        print(f"Error en bar chart: {e}")
        return create_error_image(f"Error: {str(e)}")

def create_line_chart(data, title):
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
        for i, v in enumerate(values):
            ax.annotate(str(v), (labels[i], v), textcoords="offset points",
                        xytext=(0,10), ha='center')
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        return fig
    except Exception as e:
        print(f"Error en line chart: {e}")
        return create_error_image(f"Error: {str(e)}")

def create_comparison_chart(data_general, data_filtered):
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
        if len(labels) > 3:
            plt.xticks(rotation=45, ha='right')
        return fig
    except Exception as e:
        print(f"Error en comparison chart: {e}")
        return create_error_image(f"Error: {str(e)}")

@app.route("/api/voiceflow-submit", methods=["POST"])
def voiceflow_submit():
    """Endpoint específico para recibir datos de Voiceflow"""
    try:
        data = request.json
        print(f"Datos recibidos de Voiceflow: {data}")
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
        append_row_to_sheet(new_row)
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

from flask_cors import CORS
CORS(app)

@app.route("/api/chart/<chart_type>.png")
def api_chart(chart_type):
    try:
        escuela = request.args.get("escuela")
        fecha = request.args.get("fecha")
        transporte = request.args.get("transporte")
        compare = request.args.get("compare", "0") == "1"

        print(f"Generando gráfico: {chart_type}, compare: {compare}")
        print(f"Filtros: escuela={escuela}, fecha={fecha}, transporte={transporte}")

        df = load_df()
        if df.empty:
            # datos de ejemplo
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

        df_filtered = filter_df(df, escuela, fecha, transporte)
        counts_filtered = df_filtered["transporte"].fillna("No especificado").value_counts().to_dict()
        counts_general = df["transporte"].fillna("No especificado").value_counts().to_dict()

        if compare:
            fig = create_comparison_chart(counts_general, counts_filtered)
        else:
            if escuela or fecha or transporte:
                data = counts_filtered
                title_suffix = " (Filtrado)"
            else:
                data = counts_general
                title_suffix = ""
            title = f"Distribución de Medios de Transporte{title_suffix}"
            if chart_type == "pie":
                fig = create_pie_chart(data, title)
            elif chart_type == "bar":
                fig = create_bar_chart(data, title)
            elif chart_type == "line":
                fig = create_line_chart(data, title)
            else:
                fig = create_error_image(f"Tipo de gráfico no válido: {chart_type}")

        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)

        response = send_file(buf, mimetype="image/png")
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error crítico en api_chart: {e}")
        try:
            fig = create_error_image(f"Error crítico: {str(e)}")
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
            plt.close(fig)
            buf.seek(0)
            return send_file(buf, mimetype="image/png")
        except:
            return jsonify({"error": f"Error al generar gráfico: {str(e)}"}), 500

if __name__ == "__main__":
    print("Iniciando aplicación Flask...")
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
