from flask import Flask, render_template, request, redirect, url_for, flash
from gc_service import GoogleService
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# CONFIGURACIÓN BASE
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")

TZ = ZoneInfo("America/Guayaquil")
CALENDAR_ID = os.getenv("CALENDAR_ID", "mariodanielq.p@gmail.com")

# Inicializar GoogleService de forma segura
def get_gc_service():
    try:
        return GoogleService()
    except Exception as e:
        print("❌ Error inicializando GoogleService:", e)
        return None


# DATOS SIMULADOS
SEDES = {
    "Matriz": {"foto": "static/img/sede-matriz.jpg", "map_url": "https://goo.gl/maps/..."},
    "Centro": {"foto": "static/img/sede-centro.jpg", "map_url": "https://goo.gl/maps/..."},
    "Urban": {"foto": "static/img/sede-urban.jpg", "map_url": "https://goo.gl/maps/..."},
    "Veloz": {"foto": "static/img/sede-veloz.jpg", "map_url": "https://goo.gl/maps/..."},
}

# 💈 BARBEROS POR SEDE
BARBEROS_POR_SEDE = {
    "Matriz": [
        {"nombre": "Carlos", "foto": "static/img/Carlos_SedeMatriz.jpg", "email": CALENDAR_ID},
        {"nombre": "Jose", "foto": "static/img/Jose_SedeMatriz.jpg", "email": CALENDAR_ID},
        {"nombre": "Josue", "foto": "static/img/Josue_SedeMatriz.jpg", "email": CALENDAR_ID},
        {"nombre": "Santiago", "foto": "static/img/Santiago_SedeMatriz.jpg", "email": CALENDAR_ID},
        {"nombre": "Wilson", "foto": "static/img/Wilson_SedeMatriz.jpg", "email": CALENDAR_ID},
    ],
    "Centro": [
        {"nombre": "Dani", "foto": "static/img/barber-dani.jpg", "email": CALENDAR_ID},
        {"nombre": "Don Luis", "foto": "static/img/barber-don-luis.jpg", "email": CALENDAR_ID},
    ],
    "Urban": [
        {"nombre": "Anthony", "foto": "static/img/Anthony_SedeUrban.jpg", "email": CALENDAR_ID},
        {"nombre": "Israel", "foto": "static/img/barber-isra.jpg", "email": CALENDAR_ID},
    ],
    "Veloz": [
        {"nombre": "Fabián", "foto": "static/img/Fabian_SedeVeloz.jpg", "email": CALENDAR_ID},
        {"nombre": "Kevin", "foto": "static/img/Kevin_SedeVeloz.jpg", "email": CALENDAR_ID},
        {"nombre": "Marcos", "foto": "static/img/Marcos_SedeVeloz.jpg", "email": CALENDAR_ID},
        {"nombre": "José", "foto": "static/img/barber-jose.jpg", "email": CALENDAR_ID},
    ],
}

# ✂️ SERVICIOS COMPLETOS
SERVICIOS = [
    {"nombre": "Corte de Cabello Clásico", "precio": 7, "duracion": 40,
     "descripcion": "Incluye: diagnóstico, corte a máquina con disminución gradual en laterales, perfilado de nuca y patillas, y estilizado final."},
    {"nombre": "Corte Tendencia: Fade o Degradado", "precio": 8, "duracion": 45,
     "descripcion": "Degradado alto, medio o bajo, conexión con parte superior y asesoramiento de estilizado."},
    {"nombre": "Arreglo y Perfilado de Barba", "precio": 5, "duracion": 30,
     "descripcion": "Recorte y arreglo de barba, delineado de contornos y humectación con aceite o bálsamo."},
    {"nombre": "Corte de Cabello y Barba", "precio": 12, "duracion": 60,
     "descripcion": "Asesoría, corte, peinado y arreglo de barba con productos de alta calidad."},
    {"nombre": "Barba SPA (Ritual tradicional)", "precio": 8, "duracion": 45,
     "descripcion": "Diseño, recorte, delineado y toalla caliente con vapor y bálsamo hidratante."},
]

# =========================
# RUTAS
# =========================
@app.route("/")
def sede():
    return render_template("sede.html", sedes=SEDES)


@app.route("/servicios", methods=["POST"])
def servicios():
    sede = request.form.get("sede")
    return render_template("servicios.html", sede=sede, servicios=SERVICIOS)


@app.route("/barberos", methods=["POST"])
def barberos():
    sede = request.form.get("sede")
    servicio = request.form.get("servicio")

    if not sede or sede not in BARBEROS_POR_SEDE:
        flash("⚠️ Selecciona una sede válida.")
        return redirect(url_for("sede"))

    barberos_sede = BARBEROS_POR_SEDE[sede]
    return render_template("barbero.html", sede=sede, servicio=servicio, barberos=barberos_sede)


# =========================
# CONFIRMACIÓN DE CITA
# =========================
@app.route("/confirmacion", methods=["POST"])
def confirmacion():
    sede = request.form.get("sede")
    servicio = request.form.get("servicio")
    barbero = request.form.get("barbero")

    servicio_info = next((s for s in SERVICIOS if s["nombre"] == servicio), None)
    precio = servicio_info["precio"] if servicio_info else "N/A"
    duracion = servicio_info["duracion"] if servicio_info else 30

    foto_sede = SEDES[sede]["foto"] if sede in SEDES else ""
    foto_barbero = ""
    for lista in BARBEROS_POR_SEDE.values():
        for b in lista:
            if b["nombre"] == barbero:
                foto_barbero = b["foto"]

    # 🕒 Obtener horas libres desde Google Calendar
    try:
        gc = get_gc_service()
        fecha_actual = datetime.now(TZ).strftime("%Y-%m-%d")
        horas_disponibles = gc.get_free_slots(CALENDAR_ID, fecha_actual, duracion) if gc else []
    except Exception as e:
        print("❌ Error obteniendo horas:", e)
        horas_disponibles = []

    return render_template(
        "confirmacion.html",
        sede=sede,
        servicio=servicio,
        barbero=barbero,
        precio=precio,
        duracion=duracion,
        foto_sede=foto_sede,
        foto_barbero=foto_barbero,
        horas=horas_disponibles,
    )


# =========================
# GUARDAR CITA
# =========================
@app.route("/guardar_cita", methods=["POST"])
def guardar_cita():
    sede = request.form["sede"]
    servicio = request.form["servicio"]
    barbero = request.form["barbero"]
    fecha = request.form["fecha"]
    hora = request.form["hora"]

    duracion = next((s["duracion"] for s in SERVICIOS if s["nombre"] == servicio), 30)
    inicio = datetime.fromisoformat(f"{fecha}T{hora}:00").replace(tzinfo=TZ)
    fin = inicio + timedelta(minutes=duracion)

    resumen = f"{servicio} con {barbero} ({sede})"
    descripcion = f"Cita en {sede} con {barbero} para {servicio}"

    try:
        gc = get_gc_service()
        if gc:
            gc.service.events().insert(
                calendarId=CALENDAR_ID,
                body={
                    "summary": resumen,
                    "description": descripcion,
                    "start": {"dateTime": inicio.isoformat(), "timeZone": "America/Guayaquil"},
                    "end": {"dateTime": fin.isoformat(), "timeZone": "America/Guayaquil"},
                },
            ).execute()
            flash("✅ Tu cita fue agendada y sincronizada con Google Calendar.")
        else:
            flash("⚠️ No se pudo conectar a Google Calendar.")
    except Exception as e:
        print("❌ Error al crear evento:", e)
        flash("⚠️ No se pudo crear el evento en Google Calendar.")

    return redirect(url_for("sede"))


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
