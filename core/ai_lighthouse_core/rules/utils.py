import httpx
from urllib.parse import urljoin
from functools import lru_cache
from typing import Optional, Dict, Tuple

# Shared async client to avoid creating multiple connections
async_client = httpx.AsyncClient(follow_redirects=False, timeout=10)

# Simple in-memory cache for responses during a single audit run
_response_cache: Dict[Tuple[str, str], Optional[httpx.Response]] = {}


async def fetch_head_or_get(url: str, use_cache: bool = True) -> Optional[httpx.Response]:
    """
    Fetch URL using HEAD first, falling back to GET if needed.
    Caches responses to avoid redundant fetches.
    """
    cache_key = ("head_or_get", url)
    if use_cache and cache_key in _response_cache:
        return _response_cache[cache_key]
    
    try:
        response = await async_client.head(url)
        if response.status_code >= 400 or response.status_code == 405:
            response = await async_client.get(url)
        
        if use_cache:
            _response_cache[cache_key] = response
        return response
    except httpx.RequestError as e:
        if use_cache:
            _response_cache[cache_key] = None
        return None
    except Exception as e:
        if use_cache:
            _response_cache[cache_key] = None
        return None


async def fetch_follow_redirects(url: str, max_redirects: int = 5) -> list:
    """
    Follow redirect chain and return list of (url, status_code, location) tuples.
    Caches redirect chains to avoid redundant fetches.
    """
    cache_key = ("redirects", url)
    if cache_key in _response_cache:
        return _response_cache[cache_key]
    
    chain = []
    current = url
    
    for _ in range(max_redirects):
        try:
            response = await async_client.get(current, follow_redirects=False)
            chain.append((current, response.status_code, response.headers.get("location")))
            
            if response.status_code in (301, 302, 303, 307, 308) and response.headers.get("location"):
                next_url = urljoin(current, response.headers["location"])
                current = next_url
                continue
            
            break
        except Exception:
            # If request fails, add error entry and stop
            chain.append((current, 0, None))
            break
    
    _response_cache[cache_key] = chain
    return chain


async def fetch_text_cached(url: str) -> Optional[str]:
    """
    Fetch text content from URL with caching.
    """
    cache_key = ("text", url)
    if cache_key in _response_cache:
        return _response_cache[cache_key]
    
    try:
        response = await async_client.get(url)
        response.raise_for_status()
        text = response.text
        _response_cache[cache_key] = text
        return text
    except Exception:
        _response_cache[cache_key] = None
        return None


def clear_cache():
    """Clear the response cache. Useful between audit runs."""
    _response_cache.clear()