from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json, base64

TZ = ZoneInfo("America/Guayaquil")

class GoogleService:
    def __init__(self):
        creds = None
        last_error = None

        # Intentar con variable de entorno Base64 (Render)
        b64_env = os.getenv("GOOGLE_CREDENTIALS_B64")

        if b64_env:
            try:
                info = json.loads(base64.b64decode(b64_env))
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = f"Error al decodificar GOOGLE_CREDENTIALS_B64 → {e}"

        # En local: usar credentials.json
        elif os.path.exists("credentials.json"):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    "credentials.json",
                    scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = f"Error al leer credentials.json → {e}"

        if not creds:
            raise RuntimeError(f"No se pudieron cargar las credenciales. {last_error}")

        self.service = build("calendar", "v3", credentials=creds)

    # =========================================================
    # 🔹 Horas disponibles
    # =========================================================
    def get_free_slots(self, calendar_id: str, date: str, duration_minutes: int = 45):
        try:
            service = self.service

            date_start = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=TZ)
            date_end = date_start + timedelta(days=1)

            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=date_start.isoformat(),
                timeMax=date_end.isoformat(),
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])
            busy_slots = []

            for e in events:
                start = e["start"].get("dateTime")
                end = e["end"].get("dateTime")
                if start and end:
                    busy_slots.append((start, end))

            # Horario de barbería
            open_hour = 9
            close_hour = 20
            slots = []
            start_time = date_start.replace(hour=open_hour, minute=0)

            while start_time.hour < close_hour:
                end_time = start_time + timedelta(minutes=duration_minutes)
                overlap = False
                for s, e in busy_slots:
                    s_dt = datetime.fromisoformat(s)
                    e_dt = datetime.fromisoformat(e)
                    if not (end_time <= s_dt or start_time >= e_dt):
                        overlap = True
                        break
                if not overlap:
                    slots.append(start_time.strftime("%H:%M"))
                start_time = end_time

            return slots

        except Exception as e:
            print("❌ Error generando slots:", e)
            return []
