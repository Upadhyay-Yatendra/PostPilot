import httpx

async def call_service(method, url, headers=None, params=None, json=None, timeout=10):
    async with httpx.AsyncClient(timeout=timeout) as client:
        req = getattr(client, method.lower())
        resp = await req(url, headers=headers, params=params, json=json)
        resp.raise_for_status()
        return resp.json()
