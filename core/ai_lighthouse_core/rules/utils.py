import httpx
from urllib.parse import urljoin

async_client = httpx.AsyncClient(follow_redirects=False, timeout=10)


async def fetch_head_or_get(url: str) -> httpx.Response:
    try:
        response = await async_client.head(url)
        if response.status_code >= 400 or response.status_code == 405:
            response = await async_client.get(url)
        return response
    except httpx.RequestError as e:
        raise RuntimeError(f"Error fetching {url}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error fetching {url}: {e}") from e


async def fetch_follow_redirects(url: str, max_redirects: int = 5) -> httpx.Response:
    chain = []
    current = url
    
    for _ in range(max_redirects):
        response = await async_client.get(current, follow_redirects=False)
        chain.append((current, response.status_code, response.headers.get("location")))
        
        if response.status_code in (301, 302, 303, 307, 308) and response.headers.get("location"):
            next_url = urljoin(current, response.headers["location"])
            current = next_url
            continue
        
        break
      
    return chain