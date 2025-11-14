import logging
import asyncio
from urllib.parse import urljoin, urlparse
import httpx
from typing import List, Set, Optional
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

_SITEMAP_CACHE = {}
_SITEMAP_LOCKS = {}

async_client = httpx.AsyncClient(follow_redirects=True, timeout=15)


async def _fetch_text(url: str) -> str:
    try:
        response = await async_client.get(url)
        response.raise_for_status()
        return response.text
    except httpx.RequestError as e:
        logger.error(f"Error fetching {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise


async def _parse_sitemap_text(text: str) -> List[str]:
    urls = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        logger.error(f"Error parsing sitemap XML: {e}")
        return urls

    if root.tag.endswith("sitemapindex"):
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                subtxt = await _fetch_text(loc.text.strip())
                if subtxt:
                    urls.extend(await _parse_sitemap_text(subtxt))

    else:
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                urls.append(loc.text.strip())

    return urls


async def get_sitemaps_for_domain(domain_root: str) -> List[str]:
    parsed = urlparse(domain_root)
    netloc = parsed.netloc

    if netloc in _SITEMAP_CACHE:
        return _SITEMAP_CACHE[netloc]

    lock = _SITEMAP_LOCKS.setdefault(netloc, asyncio.Lock())
    async with lock:
        if netloc in _SITEMAP_CACHE:
            return _SITEMAP_CACHE[netloc]

        robots_url = urljoin(domain_root, "/robots.txt")
        txt = await _fetch_text(robots_url)
        sitemap_urls = []

        if txt:
            for line in txt.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    sitemap_urls.append(sitemap_url)

        if not sitemap_urls:
            sitemap_urls.append(urljoin(domain_root, "/sitemap.xml"))

        verified = []
        for sm in sitemap_urls:
            txt = await _fetch_text(sm)
            if txt:
                verified.append(sm)
            else:
                logger.warning(f"Sitemap URL not reachable: {sm}")

        _SITEMAP_CACHE[netloc] = verified
        return verified


async def sitemap_urls_containing(domain_root: str, target_url: str) -> bool:
    sitemap_urls = await get_sitemaps_for_domain(domain_root)
    if not sitemap_urls:
        return False

    target_norm = target_url.rstrip("/")

    for sm in sitemap_urls:
        text = await _fetch_text(sm)
        if not text:
            continue

        try:
            root = ET.fromstring(text)
            for loc in root.findall(".//{*}loc"):
                if loc.text and loc.text.strip().rstrip("/") == target_norm:
                    return True
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap XML from {sm}: {e}")

            if target_norm in text:
                return True

    return False
