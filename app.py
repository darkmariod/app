from flask import Flask, render_template, request, redirect, url_for, flash
from gc_service import GoogleService
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# =========================
# CONFIGURACIÓN BASE
# =========================
app = Flask(__name__)
app.secret_key = "supersecretkey"  # para usar mensajes flash

TZ = ZoneInfo("America/Guayaquil")
GC = GoogleService()
CALENDAR_ID = "mariodanielq.p@gmail.com"

# =========================
# DATOS SIMULADOS
# =========================
SEDES = {
    "Matriz": {
        "foto": "static/img/sede-matriz.jpg",
        "map_url": "https://goo.gl/maps/...",
    },
    "Centro": {
        "foto": "static/img/sede-centro.jpg",
        "map_url": "https://goo.gl/maps/...",
    },
    "Urban": {
        "foto": "static/img/sede-urban.jpg",
        "map_url": "https://goo.gl/maps/...",
    },
    "Veloz": {
        "foto": "static/img/sede-veloz.jpg",
        "map_url": "https://goo.gl/maps/...",
    },
}

BARBEROS = [
    {"nombre": "Anthony", "foto": "static/img/Anthony_SedeUrban.jpg"},
    {"nombre": "Santiago", "foto": "static/img/Santiago_SedeCentro.jpg"},
    {"nombre": "Wilson", "foto": "static/img/Wilson_SedeMatriz.jpg"},
]

SERVICIOS = [
    {"nombre": "Corte Clásico", "precio": 7, "duracion": 40},
    {"nombre": "Corte Tendencia", "precio": 8, "duracion": 45},
    {"nombre": "Barba Completa", "precio": 5, "duracion": 30},
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
    return render_template("barbero.html", sede=sede, servicio=servicio, barberos=BARBEROS)


# =========================
# CONFIRMACIÓN DE CITA
# =========================
@app.route("/confirmacion", methods=["POST"])
def confirmacion():
    sede = request.form.get("sede")
    servicio = request.form.get("servicio")
    barbero = request.form.get("barbero")

    # Buscar info del servicio
    servicio_info = next((s for s in SERVICIOS if s["nombre"] == servicio), None)
    precio = servicio_info["precio"] if servicio_info else "N/A"
    duracion = servicio_info["duracion"] if servicio_info else 30

    # Buscar foto de sede y barbero
    foto_sede = SEDES[sede]["foto"] if sede in SEDES else ""
    foto_barbero = next((b["foto"] for b in BARBEROS if b["nombre"] == barbero), "")

    # 🕒 Obtener horas libres de hoy desde Google Calendar
    fecha_actual = datetime.now(TZ)
    horas_disponibles = GC.generar_slots_libres(CALENDAR_ID, fecha_actual, duracion)

    return render_template(
        "confirmacion.html",
        sede=sede,
        servicio=servicio,
        barbero=barbero,
        precio=precio,
        duracion=duracion,
        foto_sede=foto_sede,
        foto_barbero=foto_barbero,
        horas=horas_disponibles
    )


# =========================
# GUARDAR CITA (CONFIRMAR)
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
        GC.crear_evento(CALENDAR_ID, resumen, descripcion, inicio, fin, "America/Guayaquil")
        flash("✅ Tu cita fue agendada correctamente y sincronizada con Google Calendar.")
    except Exception as e:
        print("❌ Error al crear evento:", e)
        flash("⚠️ No se pudo crear el evento en Google Calendar.")

    return redirect(url_for("sede"))


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
