# gc_service.py
import os
import json
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build

TZ = ZoneInfo("America/Guayaquil")


class GoogleService:
    def __init__(self, creds_file: str = "credentials.json"):
        """
        Inicializa conexión con Google Calendar.
        Compatible con:
        1️⃣ Variable GOOGLE_CREDENTIALS_JSON (texto JSON)
        2️⃣ Variable GOOGLE_CREDENTIALS_B64 (Base64)
        3️⃣ Archivo local credentials.json (modo desarrollo)
        """
        creds = None
        last_error = None

        # --- 1) Intentar JSON plano en variable de entorno
        raw_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if raw_env:
            try:
                info = json.loads(raw_env)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = e

        # --- 2) Intentar Base64 (Render, más seguro)
        if creds is None:
            b64_env = os.getenv("GOOGLE_CREDENTIALS_B64")
            if b64_env:
                try:
                    decoded = base64.b64decode(b64_env).decode("utf-8")
                    info = json.loads(decoded)
                    creds = service_account.Credentials.from_service_account_info(
                        info, scopes=["https://www.googleapis.com/auth/calendar"]
                    )
                except Exception as e:
                    last_error = e

        # --- 3) Intentar archivo local (solo desarrollo)
        if creds is None and os.path.exists(creds_file):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    creds_file, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = e

        # --- Si nada funcionó, lanzar error
        if creds is None:
            raise RuntimeError(
                f"❌ No se pudieron cargar las credenciales. Último error: {last_error}"
            )

        # Inicializar servicio
        self.service = build("calendar", "v3", credentials=creds)

    # =============================
    # 🕒 Generar horas disponibles
    # =============================
    def generar_slots_libres(self, calendar_id: str, fecha: datetime, duracion_min: int):
        try:
            start_day = datetime(fecha.year, fecha.month, fecha.day, 9, 0, tzinfo=TZ)
            end_day = datetime(fecha.year, fecha.month, fecha.day, 20, 0, tzinfo=TZ)
            step = timedelta(minutes=30)
            horas = []

            events = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    timeMin=start_day.isoformat(),
                    timeMax=end_day.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
                .get("items", [])
            )

            ocupados = []
            for e in events:
                s = e["start"].get("dateTime")
                f = e["end"].get("dateTime")
                if s and f:
                    s_dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
                    f_dt = datetime.fromisoformat(f.replace("Z", "+00:00"))
                    ocupados.append((s_dt, f_dt))

            current = start_day
            while current + timedelta(minutes=duracion_min) <= end_day:
                libre = all(not (s <= current < f) for (s, f) in ocupados)
                if libre:
                    horas.append(current.strftime("%H:%M"))
                current += step

            print(f"✅ Slots generados: {horas}")
            return horas

        except Exception as e:
            print("❌ Error generando slots:", e)
            return []

    # =============================
    # 📅 Crear evento en Calendar
    # =============================
    def crear_evento(self, calendar_id, resumen, descripcion, inicio, fin, timezone):
        try:
            evento = {
                "summary": resumen,
                "description": descripcion,
                "start": {"dateTime": inicio.isoformat(), "timeZone": timezone},
                "end": {"dateTime": fin.isoformat(), "timeZone": timezone},
                "reminders": {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": 30}],
                },
            }
            evento = (
                self.service.events().insert(calendarId=calendar_id, body=evento).execute()
            )
            print(f"✅ Evento creado: {evento.get('htmlLink')}")
            return evento

        except Exception as e:
            print("❌ Error creando evento:", e)
            raise e
