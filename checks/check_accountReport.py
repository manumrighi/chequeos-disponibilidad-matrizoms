import aiohttp
import asyncio
from datetime import datetime
from supabase import create_client, Client
import ssl
import os

# SSL seguro y compatible con Replit
ssl_context = ssl.create_default_context()
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    ssl_context.options |= ssl.OP_LEGACY_SERVER_CONNECT

# Variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta SUPABASE_URL"
assert SUPABASE_KEY is not None, "Falta SUPABASE_KEY"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Obtener datos de Supabase
def get_db_data():
    envs_resp = supabase.table("instancias").select("*").eq("status", 1).execute()
    urls_resp = supabase.table("url_checks").select("url").eq("name", "ACCOUNT").execute()

    envs = envs_resp.data
    urls = urls_resp.data

    if not envs or not urls:
        raise Exception("No se encontraron datos en instancias o url_checks.")

    url_base = urls[0]["url"].strip()  # Usamos solo una entrada

    combined = []
    for env in envs:
        combined.append({
            "instance": env["name"].strip(),
            "token": env["token"].strip(),
            "endpoint": f"https://api-risk.{env['env'].strip()}.{env['url'].strip()}.com.ar{url_base}{env['testacc'].strip()}"
        })

    return combined

# Verifica una URL
async def check_url(session, url, token, timeout):
    headers = {'Authorization': f'Basic {token}'}
    try:
        async with session.get(url, headers=headers, timeout=timeout, ssl=ssl_context) as response:
            if response.status == 200:
                data = await response.json()
                return ('Cuenta OK', 0) if data is True else ('Error en la cuenta', 1)
            else:
                return f'Error HTTP {response.status}', 1
    except asyncio.TimeoutError:
        return 'Timeout en la solicitud', 0
    except Exception as e:
        return f"Error: {str(e)}", 1

# Intenta varias veces
async def check_with_retries(session, url, token, timeout, retries=3, backoff=0.5):
    for attempt in range(retries):
        result, error = await check_url(session, url, token, timeout)
        if result:
            return result, error
        if attempt < retries - 1:
            await asyncio.sleep(backoff * (2 ** attempt))
    return "Error luego de intentar 3 veces", 1

# Función principal
async def run_check():
    check_name = "Check Account Report"
    date = datetime.now().isoformat()
    all_logs = []

    loop = asyncio.get_running_loop()
    rows = await loop.run_in_executor(None, get_db_data)

    timeout_mapping = {'Inviu': 40}

    async with aiohttp.ClientSession() as session:
        tasks = []
        for row in rows:
            timeout = timeout_mapping.get(row["instance"], 10)
            tasks.append(check_with_retries(session, row["endpoint"], row["token"], timeout))

        results = await asyncio.gather(*tasks)

        for (result, error), row in zip(results, rows):
            all_logs.append({
                "check_name": check_name,
                "instance": row["instance"],
                "date": date,
                "output": result,
                "error": error
            })

    supabase.table("checks_logs").insert(all_logs).execute()
    return {"inserted_logs": len(all_logs), "status": "ok"}

# Ejecutar si es principal
if __name__ == "__main__":
    asyncio.run(run_check())
