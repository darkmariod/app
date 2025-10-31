from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json

TZ = ZoneInfo("America/Guayaquil")

class GoogleService:
    def __init__(self, creds_file: str = "credentials.json"):
        creds_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_env:
            creds_env = creds_env.replace("\\n", "\n")
            info = json.loads(creds_env)
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=["https://www.googleapis.com/auth/calendar"]
            )
        else:
            creds = service_account.Credentials.from_service_account_file(
                creds_file, scopes=["https://www.googleapis.com/auth/calendar"]
            )

        self.service = build("calendar", "v3", credentials=creds)

    # =====================================
    # HORAS DISPONIBLES
    # =====================================
    def generar_slots_libres(self, calendar_id: str, fecha: datetime, duracion_min: int):
        try:
            start_day = datetime(fecha.year, fecha.month, fecha.day, 9, 0, tzinfo=TZ)
            end_day = datetime(fecha.year, fecha.month, fecha.day, 20, 0, tzinfo=TZ)
            step = timedelta(minutes=30)
            horas = []

            events = self.service.events().list(
                calendarId=calendar_id,
                timeMin=start_day.isoformat(),
                timeMax=end_day.isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute().get("items", [])

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
                libre = True
                for (s, f) in ocupados:
                    if s <= current < f:
                        libre = False
                        break
                if libre:
                    horas.append(current.strftime("%H:%M"))
                current += step

            return horas
        except Exception as e:
            print("❌ Error generando slots:", e)
            return []

    # =====================================
    # CREAR EVENTO
    # =====================================
    def crear_evento(self, calendar_id, resumen, descripcion, inicio, fin, timezone):
        evento = {
            "summary": resumen,
            "description": descripcion,
            "start": {"dateTime": inicio.isoformat(), "timeZone": timezone},
            "end": {"dateTime": fin.isoformat(), "timeZone": timezone},
            "reminders": {"useDefault": False, "overrides": [{"method": "popup", "minutes": 30}]},
        }
        self.service.events().insert(calendarId=calendar_id, body=evento).execute()
        print(f"✅ Evento creado: {resumen}")
