import asyncio
import aiohttp
import json
import ssl
import os
from datetime import datetime, time
from supabase import create_client, Client

ssl_context = ssl.create_default_context()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta supabase_url"
assert SUPABASE_KEY is not None, "Falta supabase_key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CONCURRENT_REQUESTS = 10


async def check_url_async(session, url, token, timeout):
    try:
        async with session.get(url, headers={'Authorization': f'Basic {token}'}, timeout=timeout) as response:
            response.raise_for_status()
            json_response = await response.json()

            if isinstance(json_response, dict) and json_response.get('loged'):
                return True, None
            elif isinstance(json_response, list) and any(
                item.get('loged') for item in json_response if isinstance(item, dict)):
                return True, None

            return False, f'no se encontró ("loged":True), status: {response.status}'
    except aiohttp.ClientConnectionError as e:
        return False, f"Error de conexión: {e}"
    except asyncio.TimeoutError:
        return False, "Timeout en la petición"
    except aiohttp.ClientResponseError as e:
        return False, f"Error de respuesta: {e.status} {e.message}"
    except aiohttp.ClientError as e:
        return False, f"Error de cliente: {e}"
    except json.JSONDecodeError:
        return False, "Error al decodificar la respuesta JSON"
    except Exception as e:
        return False, f"Error inesperado: {e}"


async def check_url_with_retry(session, url, token, timeout, retries=3, backoff_factor=0.5):
    error = None
    for attempt in range(retries):
        result, current_error = await check_url_async(session, url, token, timeout)
        if result:
            return result, current_error
        elif attempt < retries - 1:
            await asyncio.sleep(backoff_factor * (2 ** attempt))
        error = current_error
    return False, f"error luego de {retries} reintentos: {error}"


async def process_instance_async(instance_data, session, semaphore):
    instance = instance_data['name']
    token = instance_data['token']
    sessions = instance_data['sessions']
    env = instance_data['env']
    url_base = instance_data['url']

    base = f"https://api-risk.{env}.{url_base}.com.ar"

    checks = {
        'P': 'PBCP',
        'R': 'ROFX',
        'M': 'MATRIZ',
        'B_OR': 'BYMA_OR',
        'B_MDP': 'BYMA_MDP',
        'B_CON': 'BYMA_CON'
    }

    urls_to_check = {}
    now = datetime.now().time()
    skip_matriz = now < time(9, 36)

    for s in sessions:
        if s == 'M' and skip_matriz:
            continue
        if s == 'B':
            for suffix in ['OR', 'MDP', 'CON']:
                name = f"BYMA_{suffix}"
                url_row = next((u for u in instance_data['urls'] if u['name'] == name), None)
                if url_row:
                    urls_to_check[name] = base + url_row['url']
        else:
            name = checks.get(s)
            if name:
                url_row = next((u for u in instance_data['urls'] if u['name'] == name), None)
                if url_row:
                    urls_to_check[name] = base + url_row['url']

    timeout = 50 if instance == "Inviu" else 15
    errores = []
    timeouts = []

    async with semaphore:
        tasks = [check_url_with_retry(session, url, token, timeout) for url in urls_to_check.values()]
        results = await asyncio.gather(*tasks)

    for (key, url), (ok, error) in zip(urls_to_check.items(), results):
        if not ok:
            if "Timeout" in str(error):
                timeouts.append(f"Timeout en {url}")
            else:
                errores.append(f"{key}: {error}")

    if errores:
        return {
            "check_name": "Check Sesiones",
            "instance": instance,
            "date": datetime.now().isoformat(),
            "output": " | ".join(errores),
            "error": True
        }
    elif timeouts:
        return {
            "check_name": "Check Sesiones",
            "instance": instance,
            "date": datetime.now().isoformat(),
            "output": " | ".join(timeouts),
            "error": False
        }
    else:
        return {
            "check_name": "Check Sesiones",
            "instance": instance,
            "date": datetime.now().isoformat(),
            "output": "Sesiones OK",
            "error": False
        }


async def run_check():
    instancias_res = supabase.table("instancias").select("*").eq("status", 1).execute()
    instancias = instancias_res.data

    urls_res = supabase.table("url_checks").select("name,url").eq("type", "SESSION").execute()
    url_checks = urls_res.data

    instancias_data = []
    for inst in instancias:
        inst_limpia = {k: v.strip() if isinstance(v, str) else v for k, v in inst.items()}
        instancias_data.append({
            **inst_limpia,
            "urls": url_checks
        })

    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
        tasks = [process_instance_async(row, session, semaphore) for row in instancias_data]
        logs = await asyncio.gather(*tasks)

    logs = [log for log in logs if log is not None]
    if logs:
        supabase.table("checks_logs").insert(logs).execute()

    return {"inserted_logs": len(logs), "status": "ok"}


# Solo para correrlo manualmente
if __name__ == "__main__":
    asyncio.run(run_check())
