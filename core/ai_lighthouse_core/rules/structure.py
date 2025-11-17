from typing import List, Optional
from urllib.parse import urlparse, urljoin
import httpx
import re
from bs4 import BeautifulSoup
from .base import BaseRule, Issue, Impact
from .registry import register


def _text_or_empty(tag) -> str:
    return tag.string.strip() if tag and tag.string else ""


def _char_length(text: str) -> int:
    return len(text.strip()) if text else 0


def _is_internal_link(href: str, base_url: str) -> bool:
    if not href:
        return False
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return False
    parsed_base = urlparse(base_url)
    if parsed_base.netloc == "" or parsed_base.netloc.endswith(base_url):
        return True
    return False


@register
class TitlePresentRule(BaseRule):
    id = "title-present"
    title = "<title> exists"
    impact = Impact.MEDIUM
    tags = ["seo", "accessibility"]

    def run(
        self, html: str, url: str, soup: BeautifulSoup, headers: Optional[dict] = None
    ) -> List[Issue]:
        issues = []
        title_tag = soup.find("title")
        if not title_tag or not title_tag.string or not title_tag.string.strip():
            issues.append(
                Issue(
                    id=self.id,
                    title="Missing or Empty Title Tag",
                    description="The page is missing a <title> tag or it is empty. A descriptive title is important for SEO and accessibility.",
                    impact=self.impact,
                    recommendation="Add a meaningful <title> tag to the HTML document head.",
                )
            )
        return issues


@register
class TitleLengthRule(BaseRule):
    id = "title_length_ok"
    title = "Title length 30–65 characters"
    impact = Impact.LOW
    tags = ["seo", "accessibility"]

    def run(
        self, html: str, url: str, soup: BeautifulSoup, headers: Optional[dict] = None
    ) -> List[Issue]:
        issues = []
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title_length = len(title_tag.string.strip())
            if title_length < 30 or title_length > 65:
                issues.append(
                    Issue(
                        id=self.id,
                        title="Suboptimal Title Length",
                        description=f"The <title> tag length is {title_length} characters. Optimal length is between 30 and 65 characters for better SEO.",
                        impact=self.impact,
                        recommendation="Adjust the <title> tag to be between 30 and 65 characters long.",
                    )
                )
        return issues


@register
class TitleMatchesPageRule(BaseRule):
    id = "title_matches_page"
    title = "Title contains main entity/topic"
    impact = Impact.MEDIUM
    tags = ["seo", "content"]

    def run(
        self, html: str, url: str, soup: BeautifulSoup, headers: Optional[dict] = None
    ) -> List[Issue]:
        title = _text_or_empty(soup.find("title")).lower()
        h1 = _text_or_empty(soup.find("h1")).lower()
        issues = []
        if title and h1 and h1 not in title:
            issues.append(
                Issue(
                    id=self.id,
                    title="Title does not match main page topic",
                    description="The <title> tag does not contain the main topic of the page as indicated by the <h1> tag. This can negatively impact SEO.",
                    impact=self.impact,
                    recommendation="Ensure the <title> tag includes the main topic of the page, ideally matching or closely relating to the <h1> tag content.",
                )
            )
        return issues


@register
class MetaDescriptionPresentRule(BaseRule):
    id = "meta-description-present"
    title = "<meta name='description'> exists"
    impact = Impact.MEDIUM
    tags = ["seo", "accessibility"]

    def run(
        self, html: str, url: str, soup: BeautifulSoup, headers: Optional[dict] = None
    ) -> List[Issue]:
        issues = []
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if (
            not meta_desc
            or not meta_desc.get("content")
            or not meta_desc["content"].strip()
        ):
            issues.append(
                Issue(
                    id=self.id,
                    title="Missing or Empty Meta Description",
                    description="The page is missing a meta description or it is empty. A meta description is important for SEO and accessibility.",
                    impact=self.impact,
                    recommendation="Add a meaningful meta description to the HTML document head.",
                )
            )
        return issues


@register
class MetaDescriptionLengthRule(BaseRule):
    id = "meta-description-length-ok"
    title = "Meta description length 50–160 characters"
    impact = Impact.LOW
    tags = ["seo", "accessibility"]

    def run(
        self, html: str, url: str, soup: BeautifulSoup, headers: Optional[dict] = None
    ) -> List[Issue]:
        issues = []
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            desc_length = len(meta_desc["content"].strip())
            if desc_length < 50 or desc_length > 160:
                issues.append(
                    Issue(
                        id=self.id,
                        title="Suboptimal Meta Description Length",
                        description=f"The meta description length is {desc_length} characters. Optimal length is between 50 and 160 characters for better SEO.",
                        impact=self.impact,
                        recommendation="Adjust the meta description to be between 50 and 160 characters long.",
                    )
                )
        return issues


# TODO: Implement site-wide uniqueness check separately
@register
class MetaDescriptionUniqueRule(BaseRule):
    id = "meta_description_unique"
    title = "Meta description is unique"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        return [
            Issue(
                self.id,
                self.title,
                "Uniqueness cannot be determined for a single page. Run a site-wide check to validate uniqueness.",
                self.impact,
                recommendation="Run a site-level audit to ensure meta descriptions are unique across pages.",
            )
        ]


@register
class H1PresentRule(BaseRule):
    id = "h1_present"
    title = "At least one <h1> exists"
    impact = Impact.MEDIUM

    def run(self, html, url, soup, headers):
        h1s = soup.find_all("h1")
        if not h1s:
            return [
                Issue(
                    self.id,
                    self.title,
                    "No <h1> found on page.",
                    self.impact,
                    recommendation="Include a single clear H1 representing the page topic.",
                )
            ]
        return []


@register
class H1SingleRule(BaseRule):
    id = "h1_single"
    title = "Only one <h1> on the page"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        h1s = soup.find_all("h1")
        if len(h1s) > 1:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"Multiple <h1> tags found ({len(h1s)}).",
                    self.impact,
                    recommendation="Prefer a single H1 per page.",
                )
            ]
        return []


@register
class H1MatchesTopicRule(BaseRule):
    id = "h1_matches_topic"
    title = "H1 matches page topic/main intent"
    impact = Impact.MEDIUM

    def run(self, html, url, soup, headers):
        h1 = _text_or_empty(soup.find("h1")).lower()
        title = _text_or_empty(soup.find("title")).lower()
        if h1 and title and h1 not in title:
            return [
                Issue(
                    self.id,
                    self.title,
                    "H1 doesn't appear in the page title (may not match main intent).",
                    self.impact,
                    recommendation="Ensure the H1 reflects the page's main topic and appears in title.",
                    data={"h1": h1, "title": title},
                )
            ]
        return []


@register
class HeadingHierarchyValidRule(BaseRule):
    id = "heading_hierarchy_valid"
    title = "Proper heading structure (H1 → H2 → H3...)"
    impact = Impact.MEDIUM

    def run(self, html, url, soup, headers):
        headings = []
        for level in range(1, 7):
            for h in soup.find_all(f"h{level}"):
                headings.append((level, _text_or_empty(h)))

        last_level = 0
        for level, _ in headings:
            if last_level and level - last_level > 1:
                return [
                    Issue(
                        self.id,
                        self.title,
                        f"Heading level jump detected: {last_level} → {level}.",
                        self.impact,
                        recommendation="Maintain logical heading order (do not skip levels).",
                    )
                ]
            last_level = level
        return []


@register
class SemanticMainRule(BaseRule):
    id = "semantic_main"
    title = "<main> tag present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("main"):
            return [
                Issue(
                    self.id,
                    self.title,
                    "<main> tag not found.",
                    self.impact,
                    recommendation="Wrap the main content in a <main> element for semantic clarity.",
                )
            ]
        return []


@register
class SemanticArticleRule(BaseRule):
    id = "semantic_article"
    title = "<article> tag present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("article"):
            return [
                Issue(
                    self.id,
                    self.title,
                    "<article> not found - consider using for standalone content.",
                    self.impact,
                )
            ]
        return []


@register
class OGTitleRule(BaseRule):
    id = "og_title"
    title = "og:title present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("meta", property="og:title"):
            return [
                Issue(
                    self.id,
                    self.title,
                    "Missing Open Graph og:title meta tag.",
                    self.impact,
                )
            ]
        return []


@register
class OGDescriptionRule(BaseRule):
    id = "og_description"
    title = "og:description present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("meta", property="og:description"):
            return [
                Issue(
                    self.id,
                    self.title,
                    "Missing Open Graph og:description meta tag.",
                    self.impact,
                )
            ]
        return []


@register
class OGTypeRule(BaseRule):
    id = "og_type"
    title = "og:type present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("meta", property="og:type"):
            return [
                Issue(
                    self.id,
                    self.title,
                    "Missing Open Graph og:type meta tag (website/article).",
                    self.impact,
                )
            ]
        return []


@register
class TwitterCardRule(BaseRule):
    id = "twitter_card"
    title = "twitter:card meta tag exists"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("meta", attrs={"name": "twitter:card"}):
            return [
                Issue(
                    self.id, self.title, "Missing twitter:card meta tag.", self.impact
                )
            ]
        return []


@register
class ViewportMetaRule(BaseRule):
    id = "viewport_meta"
    title = "<meta name='viewport'> present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        if not soup.find("meta", {"name": "viewport"}):
            return [
                Issue(
                    self.id,
                    self.title,
                    "Missing viewport meta tag for responsive behavior.",
                    self.impact,
                )
            ]
        return []



@register
class AltAttributesPresentRule(BaseRule):
    id = "alt_attributes_present"
    title = "All <img> elements have accessible alt text"
    impact = Impact.MEDIUM

    def run(self, html, url, soup, headers):
        imgs = soup.find_all("img")
        missing = []
        for img in imgs:
            alt = img.get("alt")
            if alt is None or alt.strip() == "":
                missing.append(img.get("src") or "<inline-img>")
        if missing:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"{len(missing)} <img> elements missing alt text.",
                    self.impact,
                    data={"samples": missing[:5]},
                    recommendation="Provide descriptive alt text for images for accessibility and AI understanding.",
                )
            ]
        return []


@register
class InternalLinkDensityRule(BaseRule):
    id = "internal_link_density_ok"
    title = "Enough internal links for discoverability"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        anchors = soup.find_all("a", href=True)
        parsed = urlparse(url)
        netloc = parsed.netloc
        internal = sum(1 for a in anchors if _is_internal_link(a["href"], netloc))
        text_len = len(soup.get_text(" ", strip=True).split())
        expected = max(2, text_len // 100)
        if internal < expected:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"Low internal link count: {internal} internal links (expected >= {expected}).",
                    self.impact,
                    recommendation="Add more internal links to related pages to help discoverability.",
                    data={"internal": internal, "expected": expected},
                )
            ]
        return []


@register
class ExternalLinkRatioRule(BaseRule):
    id = "external_link_ratio_ok"
    title = "Safe balance of outbound links"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        anchors = soup.find_all("a", href=True)
        parsed = urlparse(url)
        netloc = parsed.netloc
        external = sum(1 for a in anchors if not _is_internal_link(a["href"], netloc))
        total = len(anchors)
        if total > 0:
            ratio = external / total
            if ratio > 0.4:
                return [
                    Issue(
                        self.id,
                        self.title,
                        f"High external link ratio: {ratio:.2f} ({external}/{total}).",
                        self.impact,
                        recommendation="Reduce outbound links or mark them appropriately (nofollow) if necessary.",
                        data={"external": external, "total": total, "ratio": ratio},
                    )
                ]
        return []


@register
class NoLargeInlineScriptsRule(BaseRule):
    id = "no_large_inline_scripts"
    title = "No excessive inline JavaScript blocks"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        scripts = soup.find_all("script")
        big = []
        for s in scripts:
            if not s.get("src"):
                text = s.string or ""
                if len(text) > 2000:  # arbitrary threshold
                    big.append(len(text))
        if big:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"Found {len(big)} large inline script blocks (sizes: {big[:3]}).",
                    self.impact,
                    recommendation="Externalize large JS into files and use proper bundling.",
                )
            ]
        return []


@register
class NoHiddenTextAbuseRule(BaseRule):
    id = "no_hidden_text_abuse"
    title = "Detect hidden/abusive text (0px, off-screen)"
    impact = Impact.HIGH

    def run(self, html, url, soup, headers):
        hidden = []
        for el in soup.find_all(True):
            style = el.get("style", "")
            if style:
                s = style.replace(" ", "").lower()
                if (
                    "display:none" in s
                    or "visibility:hidden" in s
                    or "font-size:0" in s
                    or "text-indent:-9999" in s
                ):
                    hidden.append(el.name)
        for el in soup.find_all(class_=True):
            clsnames = " ".join(el.get("class"))
            if (
                "sr-only" in clsnames
                or "visually-hidden" in clsnames
                or "offscreen" in clsnames
            ):
                continue
        if hidden:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"Found {len(hidden)} elements with hidden styles (possible hidden text abuse).",
                    self.impact,
                    data={"examples": hidden[:5]},
                    recommendation="Remove hidden text used to manipulate indexing; keep only accessibility patterns.",
                )
            ]
        return []


@register
class HeroDetectedRule(BaseRule):
    id = "hero_detected"
    title = "Hero/primary visual section present"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        hero = soup.find(id=re.compile("hero", re.I)) or soup.find(
            class_=re.compile("hero", re.I)
        )
        if hero:
            return []
        header = soup.find("header")
        if header and header.find("h1"):
            return []
        return [
            Issue(
                self.id,
                self.title,
                "Hero/primary visual section not detected.",
                self.impact,
                recommendation="Consider a prominent hero section that states your primary value proposition.",
            )
        ]


@register
class TableContentCleanRule(BaseRule):
    id = "table_content_clean"
    title = "Tables are correctly structured and readable"
    impact = Impact.LOW

    def run(self, html, url, soup, headers):
        tables = soup.find_all("table")
        bad = []
        for t in tables:
            if not t.find("thead") and not t.find("th"):
                bad.append(True)
        if bad:
            return [
                Issue(
                    self.id,
                    self.title,
                    f"Found {len(bad)} tables without header cells (<th>) or <thead>.",
                    self.impact,
                    recommendation="Use <thead>/<th> for table headers and provide accessible captions.",
                )
            ]
        return []
