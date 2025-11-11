from flask import Flask, render_template, request, redirect, url_for, flash
from gc_service import GoogleService
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

# CONFIGURACIÓN BASE
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecretkey")

TZ = ZoneInfo("America/Guayaquil")
GC = GoogleService()
CALENDAR_ID = os.getenv("CALENDAR_ID", "mariodanielq.p@gmail.com")

# DATOS SIMULADOS
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

# 💈 BARBEROS POR SEDE
BARBEROS_POR_SEDE = {
    "Matriz": [
        {"nombre": "Carlos", "foto": "static/img/Carlos_SedeMatriz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Jose", "foto": "static/img/Jose_SedeMatriz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Josue", "foto": "static/img/Josue_SedeMatriz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Santiago", "foto": "static/img/Santiago_SedeMatriz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Wilson", "foto": "static/img/Wilson_SedeMatriz.jpg", "email": "mariodanielq.p@gmail.com"},
    ],
    "Centro": [
        {"nombre": "Dani", "foto": "static/img/barber-dani.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Don Luis", "foto": "static/img/barber-don-luis.jpg", "email": "mariodanielq.p@gmail.com"},
    ],
    "Urban": [
        {"nombre": "Anthony", "foto": "static/img/Anthony_SedeUrban.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Israel", "foto": "static/img/barber-isra.jpg", "email": "mariodanielq.p@gmail.com"},
    ],
    "Veloz": [
        {"nombre": "Fabián", "foto": "static/img/Fabian_SedeVeloz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Kevin", "foto": "static/img/Kevin_SedeVeloz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "Marcos", "foto": "static/img/Marcos_SedeVeloz.jpg", "email": "mariodanielq.p@gmail.com"},
        {"nombre": "José", "foto": "static/img/barber-jose.jpg", "email": "mariodanielq.p@gmail.com"},
    ],
}

# ✂️ SERVICIOS COMPLETOS
SERVICIOS = [
    {
        "nombre": "Corte de Cabello Clásico",
        "precio": 7,
        "duracion": 40,
        "descripcion": "Incluye: diagnóstico, corte a máquina con disminución gradual en laterales, perfilado de nuca y patillas, y estilizado final."
    },
    {
        "nombre": "Corte Tendencia: Fade o Degradado",
        "precio": 8,
        "duracion": 45,
        "descripcion": "El look del momento. Incluye: Degradado (alto, medio o bajo) o Taper Fade con máquina y navaja, conexión con la parte superior, y asesoramiento de estilizado."
    },
    {
        "nombre": "Arreglo y Perfilado de Barba",
        "precio": 5,
        "duracion": 30,
        "descripcion": "Servicio de precisión para definir la forma. Incluye: Recorte y arreglo de la barba (tijera/máquina), delineado de contornos (cuello y mejillas), y humectación con aceite o bálsamo."
    },
    {
        "nombre": "Corte de Cabello y Barba",
        "precio": 12,
        "duracion": 60,
        "descripcion": "La combinación perfecta. Incluye: asesoría de corte, corte a tijera o máquina, peinado con productos importados de alta calidad y arreglo de la barba con aromáticos y navaja."
    },
    {
        "nombre": "Barba SPA (Ritual tradicional)",
        "precio": 8,
        "duracion": 45,
        "descripcion": "Incluye: diseño personalizado, recorte, delineado de líneas con navaja y toalla caliente para abrir poros junto con vapor de ozono y aplicación de tónico o bálsamo hidratante."
    },
    {
        "nombre": "Servicio VIP Completo",
        "precio": 20,
        "duracion": 120,
        "descripcion": "La experiencia de máxima relajación. Incluye: asesoramiento de imagen personalizado (ficha personal), corte de cabello, lavado prolongado con masaje craneal, perfilado de barba con ritual de toalla caliente y tratamiento facial express o mascarilla capilar."
    },
    {
        "nombre": "Ritual VIP Exclusivo",
        "precio": 16,
        "duracion": 90,
        "descripcion": "Un servicio de lujo con todos los detalles. Disfrute de: corte de cabello + barba + cejas Premium, aplicación de productos de alta gama y bebida de cortesía."
    },
    {
        "nombre": "Perfilado de Cejas",
        "precio": 3,
        "duracion": 15,
        "descripcion": "Servicio de alta precisión. Incluye: perfilado con navaja o pinza, recorte profesional y aplicación de gel o tónico calmante para minimizar el enrojecimiento."
    },
    {
        "nombre": "Diseño y Perfilado de Cejas con CERA",
        "precio": 5,
        "duracion": 20,
        "descripcion": "Incluye: asesoramiento de la forma según el rostro, eliminación de vello no deseado y recorte para un acabado limpio y natural."
    },
    {
        "nombre": "Asesoría de Imagen y Estilismo Personal",
        "precio": 15,
        "duracion": 90,
        "descripcion": "Servicio de consultoría para transformar tu estilo. Incluye: análisis de forma de rostro y tipo de cabello, recomendación personalizada de corte de cabello con lavado, sugerencias de peinado y productos ideales, disfruta de tu bebida cortesía con o sin alcohol."
    },
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

    # Buscar info del servicio
    servicio_info = next((s for s in SERVICIOS if s["nombre"] == servicio), None)
    precio = servicio_info["precio"] if servicio_info else "N/A"
    duracion = servicio_info["duracion"] if servicio_info else 30

    # Buscar foto de sede y barbero
    foto_sede = SEDES[sede]["foto"] if sede in SEDES else ""
    foto_barbero = ""
    for lista in BARBEROS_POR_SEDE.values():
        for b in lista:
            if b["nombre"] == barbero:
                foto_barbero = b["foto"]

    # 🕒 Obtener horas libres desde Google Calendar
    fecha_actual = datetime.now(TZ)
    try:
        horas_disponibles = GC.generar_slots_libres(CALENDAR_ID, fecha_actual, duracion)
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

# GUARDAR CITA (CONFIRMAR)
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

# MAIN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
