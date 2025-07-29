import aiohttp
import asyncio
from datetime import datetime
from supabase import create_client, Client
import ssl
import os

# Set up SSL context
ssl_context = ssl.create_default_context()
if hasattr(ssl, 'OP_LEGACY_SERVER_CONNECT'):
    ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT

# Credenciales desde entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta SUPABASE_URL"
assert SUPABASE_KEY is not None, "Falta SUPABASE_KEY"

# Cliente Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Chequeo URL con retry
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
    base_url_data = (
        supabase.table("url_checks")
        .select("url")
        .eq("name", "ETRADER")
        .eq("type", "PLATFORM")
        .limit(1)
        .execute()
    )

    if not base_url_data.data:
        return {"error": "No se pudo obtener la URL base"}, 500

    base_url = base_url_data.data[0]["url"].strip()

    envs_data = (
        supabase.table("instancias")
        .select("env, url, name")
        .eq("status", 1)
        .execute()
    )

    if not envs_data.data:
        return {"error": "No se obtuvieron entornos"}, 500

    check_name = "Check eTrader"
    date = datetime.now().isoformat()
    all_logs = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = []
        urls_to_check = []
        rows_to_check = []

        for row in envs_data.data:
            env = row["env"].strip()
            url = row["url"].strip()
            name = row["name"].strip()

            if env.lower() == "tiendabroker":
                all_logs.append({
                    "check_name": check_name,
                    "instance": name,
                    "date": date,
                    "output": "Etrader OK",
                    "error": 0
                })
            else:
                full_url = f"https://{base_url}.{env}.{url}.com.ar"
                tasks.append(check_url_async(session, full_url))
                rows_to_check.append(row)

        results = await asyncio.gather(*tasks)

        for (success, checked_url), row in zip(results, rows_to_check):
            name = row["name"].strip()
            output = "Etrader OK" if success else checked_url
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
