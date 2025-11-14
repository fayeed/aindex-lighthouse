import logging
import asyncio
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional
import xml.etree.ElementTree as ET

# Import shared client from utils
from .utils import async_client, fetch_text_cached

logger = logging.getLogger(__name__)

_SITEMAP_CACHE = {}
_SITEMAP_LOCKS = {}
# Cache parsed sitemap URLs to avoid re-parsing
_PARSED_URLS_CACHE = {}


async def _fetch_text(url: str) -> Optional[str]:
    """Fetch text using cached utility function."""
    return await fetch_text_cached(url)


async def _parse_sitemap_text(text: str) -> List[str]:
    """Parse sitemap XML and extract URLs. Handles sitemap index recursively."""
    urls = []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        logger.error(f"Error parsing sitemap XML: {e}")
        return urls

    # Handle sitemap index - collect all sub-sitemaps first, then batch fetch
    if root.tag.endswith("sitemapindex"):
        sub_urls = []
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                sub_urls.append(loc.text.strip())
        
        # Batch fetch all sub-sitemaps concurrently
        if sub_urls:
            tasks = [_fetch_text(url) for url in sub_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Parse all results
            for subtxt in results:
                if isinstance(subtxt, str) and subtxt:
                    urls.extend(await _parse_sitemap_text(subtxt))
    else:
        # Regular sitemap - extract all URLs
        for loc in root.findall(".//{*}loc"):
            if loc.text:
                urls.append(loc.text.strip())

    return urls


async def get_sitemaps_for_domain(domain_root: str) -> List[str]:
    """Get sitemap URLs for a domain with caching and lock protection."""
    parsed = urlparse(domain_root)
    netloc = parsed.netloc

    if netloc in _SITEMAP_CACHE:
        return _SITEMAP_CACHE[netloc]

    lock = _SITEMAP_LOCKS.setdefault(netloc, asyncio.Lock())
    async with lock:
        # Double-check after acquiring lock
        if netloc in _SITEMAP_CACHE:
            return _SITEMAP_CACHE[netloc]

        robots_url = urljoin(domain_root, "/robots.txt")
        txt = await _fetch_text(robots_url)
        sitemap_urls = []

        if txt:
            sitemap_urls = [
                line.split(":", 1)[1].strip()
                for line in txt.splitlines()
                if line.lower().startswith("sitemap:")
            ]

        if not sitemap_urls:
            sitemap_urls.append(urljoin(domain_root, "/sitemap.xml"))

        # Verify sitemaps concurrently
        tasks = [_fetch_text(sm) for sm in sitemap_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        verified = []
        for sm, txt in zip(sitemap_urls, results):
            if isinstance(txt, str) and txt:
                verified.append(sm)
            else:
                logger.warning(f"Sitemap URL not reachable: {sm}")

        _SITEMAP_CACHE[netloc] = verified
        return verified


async def sitemap_urls_containing(domain_root: str, target_url: str) -> bool:
    """
    Check if target_url exists in any sitemap for the domain.
    Uses cached parsed URLs to avoid re-parsing sitemaps.
    """
    sitemap_urls = await get_sitemaps_for_domain(domain_root)
    if not sitemap_urls:
        return False

    target_norm = target_url.rstrip("/")
    
    # Check if we've already parsed these sitemaps
    cache_key = tuple(sorted(sitemap_urls))
    if cache_key in _PARSED_URLS_CACHE:
        parsed_urls = _PARSED_URLS_CACHE[cache_key]
        return target_norm in parsed_urls

    # Parse all sitemaps and cache the results
    all_urls = set()
    for sm in sitemap_urls:
        text = await _fetch_text(sm)
        if not text:
            continue

        try:
            root = ET.fromstring(text)
            for loc in root.findall(".//{*}loc"):
                if loc.text:
                    all_urls.add(loc.text.strip().rstrip("/"))
        except ET.ParseError as e:
            logger.error(f"Error parsing sitemap XML from {sm}: {e}")
            # Fallback to text search for malformed XML
            if target_norm in text:
                all_urls.add(target_norm)

    _PARSED_URLS_CACHE[cache_key] = all_urls
    return target_norm in all_urls
