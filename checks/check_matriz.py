import aiohttp
import asyncio
from datetime import datetime
from supabase import create_client, Client
import ssl
import os

# Configuración SSL
ssl_context = ssl.create_default_context()

# Leer credenciales desde variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta SUPABASE_URL"
assert SUPABASE_KEY is not None, "Falta SUPABASE_KEY"

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Función para chequear una URL con retry
async def check_url_async(session, url, retries=3, backoff_factor=0.3):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                return True, url
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError):
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2 ** attempt))
        except asyncio.TimeoutError:
            return False, url
    return False, url

# Función principal
async def run_check():
    # Obtener URL base
    base_url_data = (
        supabase.table("url_checks")
        .select("url")
        .eq("name", "MATRIZ")
        .eq("type", "PLATFORM")
        .limit(1)
        .execute()
    )

    if not base_url_data.data:
        return {"error": "No se pudo obtener la URL base"}, 500

    base_url = base_url_data.data[0]["url"].strip()

    # Obtener entornos activos
    envs_data = (
        supabase.table("instancias")
        .select("env, url, name, sessions")
        .eq("status", 1)
        .execute()
    )

    if not envs_data.data:
        return {"error": "No se obtuvieron entornos"}, 500

    # Separar por presencia de "M" en sessions
    envs_con_m = [row for row in envs_data.data if row.get("sessions") and "M" in row["sessions"]]
    envs_sin_m = [row for row in envs_data.data if not row.get("sessions") or "M" not in row["sessions"]]

    check_name = "Check Matriz"
    date = datetime.now().isoformat()
    all_logs = []

    # Chequeo real para los que tienen "M"
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = []
        for row in envs_con_m:
            env = row["env"].strip()
            url = row["url"].strip()
            full_url = f"https://{base_url}.{env}.{url}.com.ar"
            tasks.append(check_url_async(session, full_url))

        results = await asyncio.gather(*tasks)

        for (success, checked_url), row in zip(results, envs_con_m):
            name = row["name"].strip()
            output = "Matriz OK" if success else checked_url
            error = 0 if success else 1
            all_logs.append({
                "check_name": check_name,
                "instance": name,
                "date": date,
                "output": output,
                "error": error
            })

    # Para los que no tienen "M"
    for row in envs_sin_m:
        name = row["name"].strip()
        all_logs.append({
            "check_name": check_name,
            "instance": name,
            "date": date,
            "output": "Matriz OK",
            "error": 0
        })

    # Insertar en Supabase
    supabase.table("checks_logs").insert(all_logs).execute()
    return {"inserted_logs": len(all_logs), "status": "ok"}
