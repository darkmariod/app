# gc_service.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os, json, base64

TZ = ZoneInfo("America/Guayaquil")

class GoogleService:
    def __init__(self, creds_file: str = "credentials.json"):
        raw_env = os.getenv("GOOGLE_CREDENTIALS_JSON")
        b64_env = os.getenv("GOOGLE_CREDENTIALS_B64")

        creds = None
        last_error = None

        # 1) JSON “normal” (con \n escapados)
        if raw_env and creds is None:
            try:
                info = json.loads(raw_env)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
                # listo
            except Exception as e:
                last_error = e

        # 2) JSON pegado con saltos de línea crudos (repara el private_key)
        if raw_env and creds is None:
            try:
                # Si falló antes, intentamos “arreglar” sólo la clave privada.
                # Buscamos el dict de forma robusta:
                obj = json.loads(_escape_private_key_newlines(raw_env))
                creds = service_account.Credentials.from_service_account_info(
                    obj, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = e

        # 3) Base64 (más seguro en cualquier PaaS)
        if b64_env and creds is None:
            try:
                decoded = base64.b64decode(b64_env).decode("utf-8")
                info = json.loads(decoded)
                creds = service_account.Credentials.from_service_account_info(
                    info, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                last_error = e

        # 4) Archivo local (desarrollo)
        if creds is None:
            try:
                creds = service_account.Credentials.from_service_account_file(
                    creds_file, scopes=["https://www.googleapis.com/auth/calendar"]
                )
            except Exception as e:
                raise RuntimeError(
                    f"No pude cargar credenciales desde entorno ni archivo. Último error: {last_error}"
                ) from e

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


def _escape_private_key_newlines(raw: str) -> str:
    """
    Si el JSON trae saltos de línea crudos dentro de "private_key",
    convertimos sólo esos a '\\n'. Lo demás del JSON no se toca.
    """
    # Intento rápido: parsear como JSON; si pasa, devolvemos tal cual.
    try:
        json.loads(raw)
        return raw
    except:
        pass

    # Reparamos el campo private_key con una pequeña heurística:
    #  - Encontramos "private_key":"-----BEGIN PRIVATE KEY----- ... -----END PRIVATE KEY-----"
    #  - Dentro de esas comillas reemplazamos \n crudos por \\n
    out = []
    i = 0
    in_string = False
    key_mode = False
    pk_mode = False
    buf = []
    key_name = []

    while i < len(raw):
        ch = raw[i]
        out.append(ch)

        # Detectar inicio de string JSON (muy simple, suficiente aquí)
        if ch == '"':
            # mirar atrás si no era escape
            backslashes = 0
            j = i - 1
            while j >= 0 and raw[j] == '\\':
                backslashes += 1
                j -= 1
            if backslashes % 2 == 0:
                in_string = not in_string
                if in_string:
                    # empezamos a leer posible nombre de clave
                    key_mode = True
                    key_name = []
                else:
                    # terminamos string
                    if pk_mode:
                        # acabamos de cerrar private_key, salimos de modo pk
                        pk_mode = False

        elif in_string and key_mode:
            # construimos nombre de clave hasta cerrar comillas + luego ver ":"
            if ch != '"':
                key_name.append(ch)
            # detectar si justo después viene ":"
            # (dejamos que ciclo continúe; validación sencilla)
        elif not in_string and key_mode:
            # salimos de modo nombre y comprobamos si fue "private_key"
            # buscamos los últimos caracteres añadidos a out para ver si justo cerró el nombre
            key_mode = False
            name = "".join(key_name)
            if name == "private_key":
                # activar modo 'estamos dentro de private_key' cuando entremos al siguiente string
                # buscamos la siguiente comilla para abrir el valor
                # (el bucle normal lo hará; sólo marcamos bandera)
                pk_mode = True

        # Si estamos dentro del string del valor de private_key y vemos salto de línea crudo, lo escapamos.
        if pk_mode and ch == '\n':
            # Reemplazamos en la salida ese último '\n' por '\\n'
            out[-1] = '\\n'

        i += 1

    return "".join(out)
