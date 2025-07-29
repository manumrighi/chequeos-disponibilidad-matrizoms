import aiohttp
import asyncio
from datetime import datetime
import ssl
from supabase import create_client, Client
import os

ssl_context = ssl.create_default_context()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

assert SUPABASE_URL is not None, "Falta supabase_url"
assert SUPABASE_KEY is not None, "Falta supabase_key"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def check_url_async(session, url, retries=3, backoff_factor=0.3):
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                return True, url
        except (aiohttp.ClientConnectionError, aiohttp.ClientResponseError):
            if attempt < retries - 1:
                await asyncio.sleep(backoff_factor * (2**attempt))
        except asyncio.TimeoutError:
            return False, url
    return False, url


async def run_check():
    base_url_data = (supabase.table("url_checks").select("url").eq(
        "name", "ADMIN").eq("type", "PLATFORM").limit(1).execute())

    if not base_url_data.data:
        return {"error": "No se pudo obtener la URL base"}, 500

    base_url = base_url_data.data[0]["url"].strip()

    envs_data = (supabase.table("instancias").select("env, url, name").eq(
        "status", 1).execute())

    if not envs_data.data:
        return {"error": "No se obtuvieron entornos"}, 500

    check_name = "Check Admin"
    date = datetime.now().isoformat()
    all_logs = []

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(
            ssl=ssl_context)) as session:
        tasks = []
        for row in envs_data.data:
            env = row["env"].strip()
            url = row["url"].strip()
            name = row["name"].strip()
            full_url = f"https://{base_url}.{env}.{url}.com.ar"
            tasks.append(check_url_async(session, full_url))

        results = await asyncio.gather(*tasks)

        for (success, checked_url), row in zip(results, envs_data.data):
            name = row["name"].strip()
            output = "Admin OK" if success else checked_url
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
