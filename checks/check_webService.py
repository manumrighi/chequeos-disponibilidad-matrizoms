import aiohttp
import asyncio
import ssl
from datetime import datetime
from supabase import create_client, Client
import os

# SSL context compatible con Replit
ssl_context = ssl.create_default_context()
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT

# Variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta SUPABASE_URL"
assert SUPABASE_KEY is not None, "Falta SUPABASE_KEY"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Reintento de conexión
async def check_webservice_async(session, full_url, headers, retries=3, backoff_factor=0.5):
    for attempt in range(retries):
        try:
            async with session.get(full_url, headers=headers, timeout=20) as response:
                response.raise_for_status()
                text = await response.text()
                return response.status == 200 and "CONNECTED" in text, full_url
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError, asyncio.TimeoutError, ConnectionResetError):
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2 ** attempt))
    return False, full_url

# Función principal
async def run_check():
    check_name = "Check WebService"
    date = datetime.now().isoformat()
    all_logs = []

    # Obtener datos de Supabase
    envs_data = supabase.table("instancias").select("env, url, name, token").eq("status", 1).execute()
    urls_data = supabase.table("url_checks").select("url").eq("type", "WEBSERVICE").execute()

    if not envs_data.data or not urls_data.data:
        return {"error": "Faltan datos de instancias o URL_CHECKS"}, 500

    endpoint_url = urls_data.data[0]["url"].strip()  # Usamos solo una entrada

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = []
        rows_to_check = []

        for row in envs_data.data:
            env = row["env"].strip()
            base_url = row["url"].strip()
            name = row["name"].strip()
            token = row["token"].strip()

            full_url = f"https://api-risk.{env}.{base_url}.com.ar{endpoint_url}"
            headers = {
                "Authorization": f"Basic {token}"
            }

            tasks.append(check_webservice_async(session, full_url, headers))
            rows_to_check.append(row)

        results = await asyncio.gather(*tasks)

        for (success, checked_url), row in zip(results, rows_to_check):
            name = row["name"].strip()
            output = "WebService OK" if success else f"Error en: {checked_url}"
            error = 0 if success else 1
            all_logs.append({
                "check_name": check_name,
                "instance": name,
                "date": date,
                "output": output,
                "error": error
            })

    supabase.table("checks_logs").insert(all_logs).execute()
    return {"inserted_logs": len(all_logs), "status": "ok"}

# Ejecutar si es principal (útil si querés correrlo en Replit directamente)
if __name__ == "__main__":
    asyncio.run(run_check())
