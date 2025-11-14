from urllib.parse import urljoin, urlparse

from .sitemap_helpers import get_sitemaps_for_domain, sitemap_urls_containing
from .registry import register
from .base import BaseRule, Impact, Issue
from .utils import fetch_head_or_get, fetch_follow_redirects, async_client


@register
class RobotTxtPresent(BaseRule):
    id = "robot-txt-present"
    title = "Robots.txt is accessble"
    impact = Impact.LOW
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        robots_url = urljoin(root, "/robots.txt")
        response = await fetch_head_or_get(robots_url)
        if response is None or response.status_code >= 400:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="The robots.txt file is missing or unreachable.",
                    impact=self.impact,
                    recommendation="Ensure that a valid robots.txt file is present at the root of your domain.",
                    data={
                        "robots_url": robots_url,
                        "status_code": (
                            response.status_code if response else "No Response"
                        ),
                    },
                )
            ]

        return []


@register
class NoSoft404(BaseRule):
    id = "no-soft-404"
    title = "Avoid soft 404 errors"
    impact = Impact.HIGH
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        text_len = len(soup.get_text(strip=True))
        h1s = soup.find_all("h1")
        if text_len < 50 or ("404" in "".join([h1.get_text() for h1 in h1s]).lower()):
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="The page appears to be a soft 404 (very little content or error indicators).",
                    impact=self.impact,
                    recommendation="Ensure that valid content is served for this URL and that it does not return a soft 404.",
                    data={"url": url, "text_length": text_len},
                )
            ]

        return []


@register
class No302Homepage(BaseRule):
    id = "no-302-homepage"
    title = "Homepage is not 302-redirected"
    impact = Impact.LOW
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
        chain = await fetch_follow_redirects(root, max_redirects=5)
        if chain and chain[0][1] == 302:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="The homepage URL returns a 302 redirect.",
                    impact=self.impact,
                    recommendation="Use 301 for permanent redirects, avoid unnecessary redirects.",
                    data={"homepage_url": root, "redirect_chain": chain},
                )
            ]

        return []


@register
class HreflangSelf(BaseRule):
    id = "hreflang-self"
    title = "hreflang has correct self-reference"
    impact = Impact.LOW
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        canonical = soup.find("link", rel="canonical")
        if not canonical:
            return []
        canonical_url = canonical.get("href", "").rstrip("/")

        hreflangs = soup.find_all("link", rel="alternate", hreflang=True)
        for h in hreflangs:
            if h.get("hreflang") == "x-default":
                continue
            if h.get("href", "").rstrip("/") == canonical_url:
                return []  # correct self-reference

        return [
            Issue(
                id=self.id,
                title=self.title,
                description="No hreflang self-reference found matching canonical.",
                impact=self.impact,
                recommendation="Add an hreflang entry pointing to the canonical URL.",
                data={
                    "canonical_url": canonical_url,
                    "hreflangs": [h.get("href") for h in hreflangs],
                },
            )
        ]


@register
class HreflangValid(BaseRule):
    id = "hreflang-valid"
    title = "hreflang attributes are valid"
    impact = Impact.HIGH
    tags = ["crawlability"]

    VALID_HREFLANGS = {"en", "fr", "de", "es", "it", "x-default"}  # extend as needed

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        hreflangs = soup.find_all("link", rel="alternate", hreflang=True)
        invalids = []
        for h in hreflangs:
            hl = h.get("hreflang")
            if hl not in self.VALID_HREFLANGS:
                invalids.append(hl)

        if invalids:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="Invalid hreflang attributes found.",
                    impact=self.impact,
                    recommendation=f"Use valid hreflang values: {', '.join(sorted(self.VALID_HREFLANGS))}.",
                    data={"invalid_hreflangs": invalids},
                )
            ]

        return []


@register
class CanonicalPresent(BaseRule):
    id = "canonical-present"
    title = "Canonical tag exists"
    impact = Impact.HIGH
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        canonical = soup.find("link", rel="canonical")
        if not canonical or not canonical.get("href"):
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="No canonical link tag found in the page.",
                    impact=self.impact,
                    recommendation="Add a canonical link tag to specify the preferred URL for this page.",
                    data={"current_url": url},
                )
            ]

        return []


@register
class CanonicalSelfRef(BaseRule):
    id = "canonical-self-ref"
    title = "Canonical URL self-reference = Page"
    impact = Impact.MEDIUM
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        canonical = soup.find("link", rel="canonical")
        if not canonical:
            return []
        canonical_url = canonical.get("href", "").rstrip("/")
        if canonical_url != url.rstrip("/"):
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="Canonical URL does not self-reference the current URL.",
                    impact=self.impact,
                    recommendation="Ensure the canonical link points to the current page URL.",
                    data={"canonical_url": canonical_url, "current_url": url},
                )
            ]

        return []


@register
class CanonicalResolves(BaseRule):
    id = "canonical-resolves"
    title = "Canonical URL resolves successfully"
    impact = Impact.HIGH
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        canonical = soup.find("link", rel="canonical")
        if not canonical:
            return []
        canonical_url = canonical.get("href", "")
        response = await fetch_head_or_get(canonical_url)
        if response is None or response.status_code >= 400:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="Canonical URL does not resolve successfully.",
                    impact=self.impact,
                    recommendation="Ensure the canonical URL is valid and returns a successful response.",
                    data={
                        "canonical_url": canonical_url,
                        "status_code": (
                            response.status_code if response else "No Response"
                        ),
                    },
                )
            ]

        return []


@register
class CanonicalConsistent(BaseRule):
    id = "canonical-consistent"
    title = "Canonical URL is consistent across redirects"
    impact = Impact.HIGH
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        canonical_tag = soup.find("link", rel="canonical")
        if not canonical_tag or not canonical_tag.get("href"):
            return []

        canonical = canonical_tag.get("href").rstrip("/")
        parsed = urlparse(canonical)
        domain_root = f"{parsed.scheme}://{parsed.netloc}/"

        sitemaps = await get_sitemaps_for_domain(domain_root)
        if not sitemaps:
            return []

        in_sitemap = await sitemap_urls_containing(domain_root, canonical)
        page_in_sitemap = await sitemap_urls_containing(domain_root, url.strip("/"))
        issues = []

        if not in_sitemap:
            issues.append(
                Issue(
                    id=self.id,
                    title=self.title,
                    description=f"Canonical URL {canonical} not found in any sitemap.",
                    impact=self.impact,
                    recommendation="Ensure the canonical URL is included in your sitemap files.",
                    data={"canonical_url": canonical, "sitemaps": sitemaps},
                )
            )

        return issues


@register
class RedirectChainSmall(BaseRule):
    id = "redirect-chain-small"
    title = "Redirect chain is small"
    impact = Impact.MEDIUM
    tags = ["crawlability"]

    MAX_REDIRECTS = 3

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        chain = await fetch_follow_redirects(url, max_redirects=10)
        if len(chain) > self.MAX_REDIRECTS:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="The redirect chain is too long.",
                    impact=self.impact,
                    recommendation=f"Reduce the redirect chain to {self.MAX_REDIRECTS} or fewer redirects.",
                    data={"redirect_chain": chain},
                )
            ]

        return []


@register
class HTTPStatusOk(BaseRule):
    id = "http-status-ok"
    title = "HTTP status is 200 OK"
    impact = Impact.CRITICAL
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        chain = await fetch_follow_redirects(url)
        last = chain[-1]
        if last[1] >= 400:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description=f"The final HTTP status code is {last[1]}, indicating an error.",
                    impact=self.impact,
                    recommendation="Ensure the URL returns a 200 OK status code.",
                    data={"final_url": last[0], "status_code": last[1], "chain": chain},
                )
            ]

        return []


@register
class SitemapPresent(BaseRule):
    id = "sitemap-present"
    title = "Sitemap referenced in robots.txt"
    impact = Impact.MEDIUM
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        sitemap_url = urljoin(root, "/robots.txt")
        response = await fetch_head_or_get(sitemap_url)
        if response is None or response.status_code >= 400:
            return []
        try:
            txt = (await async_client.get(sitemap_url)).text.lower()
        except:
            return []
        if "sitemap:" not in txt:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="No sitemap reference found in robots.txt.",
                    impact=self.impact,
                    recommendation="Add a Sitemap directive in your robots.txt file to help crawlers discover your sitemap.",
                    data={"robots_url": sitemap_url},
                )
            ]

        return []


@register
class SitemapReachable(BaseRule):
    id = "sitemap-reachable"
    title = "Sitemap URL is reachable"
    impact = Impact.MEDIUM
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        sitemap_url = urljoin(root, "/robots.txt")
        try:
            txt = (await async_client.get(sitemap_url)).text.lower()
        except:
            return []

        sitemaps = [
            line.split(":", 1)[1].strip()
            for line in txt.splitlines()
            if line.startswith("sitemap:")
        ]
        issues = []
        for sm_url in sitemaps:
            response = await fetch_head_or_get(sm_url)
            if response is None or response.status_code >= 400:
                issues.append(
                    Issue(
                        id=self.id,
                        title=self.title,
                        description=f"Sitemap URL {sm_url} is not reachable.",
                        impact=self.impact,
                        recommendation="Ensure the sitemap URL is valid and accessible.",
                        data={
                            "sitemap_url": sm_url,
                            "status_code": (
                                response.status_code if response else "No Response"
                            ),
                        },
                    )
                )

        return issues


@register
class SitemapContainsURLs(BaseRule):
    id = "sitemap-contains-urls"
    title = "Page exists in sitemap"
    impact = Impact.LOW
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        parsed = urlparse(url)
        domain_root = f"{parsed.scheme}://{parsed.netloc}/"
        canonical_tag = soup.find("link", rel="canonical")
        target = (
            canonical_tag.get("href").rstrip("/") if canonical_tag else url.rstrip("/")
        )

        sitemaps = await get_sitemaps_for_domain(domain_root)
        if not sitemaps:
            return []

        found = await sitemap_urls_containing(domain_root, target)
        if not found:
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="The page URL is not listed in any sitemap.",
                    impact=self.impact,
                    recommendation="Include the page URL in your sitemap files to improve discoverability.",
                    data={"page_url": target, "sitemaps": sitemaps},
                )
            ]

        return []


@register
class RobotsHeaderNoindex(BaseRule):
    id = "robots-header-noindex"
    title = "X-Robots-Tag header does not contain noindex"
    impact = Impact.CRITICAL
    tags = ["crawlability"]

    async def run(
        self, html: str, url: str, soup, headers=None
    ) -> list[BaseRule.Issue]:
        hdrs = headers or {}
        x_robots = None
        for k, v in hdrs.items():
            if k.lower() == "x-robots-tag":
                x_robots = v
                break

        if not x_robots:
            return []

        if "noindex" in x_robots.lower():
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description=f"X-Robots-Tag header contains 'noindex': {x_robots}",
                    impact=self.impact,
                    recommendation="Remove 'noindex' from the X-Robots-Tag header to allow indexing.",
                    data={"url": url, "x_robots_tag": x_robots},
                )
            ]

        return []


@register
class RobotsMetaNoindex(BaseRule):
    id = "robots-meta-noindex"
    title = "Meta robots tag does not contain noindex"
    impact = Impact.CRITICAL
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        meta_robots = soup.find("meta", attrs={"name": "robots"})
        if meta_robots and "noindex" in meta_robots.get("content", "").lower():
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="Meta robots tag contains 'noindex'.",
                    impact=self.impact,
                    recommendation="Remove 'noindex' from the meta robots tag to allow indexing.",
                    data={"url": url},
                )
            ]

        return []


@register
class CrawlAllowed(BaseRule):
    id = "crawl-allowed"
    title = "Crawling is allowed by robots.txt"
    impact = Impact.CRITICAL
    tags = ["crawlability"]

    async def run(self, html: str, url: str, soup) -> list[BaseRule.Issue]:
        root = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        robots_url = urljoin(root, "/robots.txt")
        try:
            txt = (await async_client.get(robots_url)).text.lower()
        except:
            return []

        path = urlparse(url).path or "/"
        disallow_lines = [
            line.split(":", 1)[1].strip()
            for line in txt.splitlines()
            if line.startswith("disallow:")
        ]

        if any(path.startswith(d) for d in disallow_lines):
            return [
                Issue(
                    id=self.id,
                    title=self.title,
                    description="Crawling of this URL is disallowed by robots.txt.",
                    impact=self.impact,
                    recommendation="Update robots.txt to allow crawling of this URL.",
                    data={"url": url, "robots_url": robots_url},
                )
            ]

        return []
