import asyncio
import logging
from typing import Dict, Any, List, Set
from crawl4ai import AsyncWebCrawler
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scraper tuning defaults
custom_settings = {
    'DEPTH_LIMIT': 3,
    'MAX_PAGES': 20,
    'REQUEST_DELAY': 0.5,  # seconds delay between requests to throttle
    'SCRAPE_TIMEOUT': 30,  # seconds per page timeout
    'MAX_RETRIES': 2,      # retries per page
}

# Anti-bot / garbage content indicators
BLOCKED_INDICATORS = [
    "blocked by anti-bot",
    "access denied",
    "403 forbidden",
    "captcha",
    "please verify you are a human",
    "enable javascript",
    "checking your browser",
    "cloudflare",
    "just a moment",
    "ray id",
    "security check",
    "bot detection",
]


def _is_blocked_content(text: str) -> bool:
    """Check if scraped content is actually an anti-bot/WAF block page."""
    if not text:
        return True
    # Very short content is suspicious
    if len(text.strip()) < 200:
        return True
    lower = text.lower()
    # If most of the content is block-related
    matches = sum(1 for indicator in BLOCKED_INDICATORS if indicator in lower)
    if matches >= 2:
        return True
    return False


class OptimizedWebScraper:
    """
    Async web scraper that reuses a single AsyncWebCrawler instance
    to avoid opening multiple browsers.
    """

    def __init__(self):
        self.crawler = None

    async def __aenter__(self):
        """Async context manager entry."""
        if not self.crawler:
            self.crawler = AsyncWebCrawler()
            await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.crawler:
            try:
                await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
                logger.info("Crawler closed successfully")
            except Exception as e:
                logger.error(f"Error closing crawler: {e}")
            finally:
                self.crawler = None

    async def scrape_single_page(self, url: str, timeout: int = None) -> Dict[str, Any]:
        """Scrape a single page using the shared crawler instance with timeout and retry."""
        if not self.crawler:
            raise RuntimeError("Scraper not initialized. Use 'async with OptimizedWebScraper():'")

        timeout = timeout or custom_settings.get('SCRAPE_TIMEOUT', 30)
        max_retries = custom_settings.get('MAX_RETRIES', 2)

        for attempt in range(max_retries + 1):
            try:
                result = await asyncio.wait_for(
                    self.crawler.arun(url=url),
                    timeout=timeout
                )
                markdown = result.markdown or ''

                # Validate content is not a block page
                if _is_blocked_content(markdown):
                    logger.warning(f"Blocked/garbage content detected for {url} (attempt {attempt + 1})")
                    if attempt < max_retries:
                        await asyncio.sleep(2 ** attempt)  # exponential backoff
                        continue
                    return {
                        'url': url,
                        'markdown': '',
                        'links': {},
                        'success': False,
                        'error': 'Content blocked by anti-bot protection'
                    }

                return {
                    'url': url,
                    'markdown': markdown,
                    'links': result.links or {},
                    'success': True
                }

            except asyncio.TimeoutError:
                logger.warning(f"Timeout scraping {url} (attempt {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    'url': url,
                    'markdown': '',
                    'links': {},
                    'success': False,
                    'error': f'Timeout after {timeout}s'
                }
            except Exception as e:
                logger.error(f"Error scraping {url} (attempt {attempt + 1}): {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return {
                    'url': url,
                    'markdown': '',
                    'links': {},
                    'success': False,
                    'error': str(e)
                }

        return {
            'url': url,
            'markdown': '',
            'links': {},
            'success': False,
            'error': 'All retry attempts exhausted'
        }


def _get_internal_links(result: Dict[str, Any]) -> List[str]:
    """Extract internal link URLs from a scrape result."""
    links = result.get('links') or {}
    internal = links.get('internal', [])
    hrefs = []
    for link in internal:
        href = link.get("href") if isinstance(link, dict) else link
        if href and isinstance(href, str):
            hrefs.append(href)
    return hrefs


async def scrape_website(url: str, max_depth: int = None, max_pages: int = None, delay: float = None) -> str:
    """
    Crawl a website following internal links and return the collected
    page content as a single markdown string.
    Returns empty string if site is fully blocked (anti-bot).
    """
    visited: Set[str] = set()
    content_list: List[str] = []
    max_depth = max_depth if max_depth is not None else custom_settings.get('DEPTH_LIMIT', 3)
    max_pages = max_pages if max_pages is not None else custom_settings.get('MAX_PAGES', 20)
    delay = delay if delay is not None else custom_settings.get('REQUEST_DELAY', 0.5)

    try:
        async with OptimizedWebScraper() as scraper:

            async def crawl_recursive(current_url: str, depth: int):
                if depth > max_depth or current_url in visited or len(visited) >= max_pages:
                    return

                # Skip sitemap pages other than the seed URL
                if "sitemap" in urlparse(current_url).path.lower() and current_url != url:
                    return

                visited.add(current_url)
                logger.info(f"Scraping page {len(visited)}/{max_pages}: {current_url}")

                result = await scraper.scrape_single_page(current_url)

                # Only append genuinely successful, non-blocked content
                if result['success'] and result['markdown']:
                    content_list.append(result['markdown'])

                # Respect throttling: delay between requests
                await asyncio.sleep(delay)

                if len(visited) < max_pages:
                    for href in _get_internal_links(result):
                        if len(visited) >= max_pages:
                            break
                        full_link = urljoin(current_url, href)
                        if urlparse(full_link).netloc == urlparse(url).netloc:
                            await crawl_recursive(full_link, depth + 1)

            await crawl_recursive(url, 0)

    except Exception as e:
        logger.error(f"Critical scraper error for {url}: {e}")
        # Don't crash - return whatever we collected
    
    logger.info(f"Completed scraping {len(visited)} pages, collected {len(content_list)} content pieces")
    return "\n\n".join(content_list)


async def scrape_competitor_website(url: str, max_pages: int = 15, delay: float = None) -> str:
    """
    Crawl a competitor website (single level of depth) and return the
    collected content as a markdown string.
    """
    visited: Set[str] = set()
    content_list: List[str] = []
    max_depth = 1  # fixed for competitors
    delay = delay if delay is not None else custom_settings.get('REQUEST_DELAY', 0.5)

    try:
        async with OptimizedWebScraper() as scraper:

            async def crawl_recursive(current_url: str, depth: int):
                if depth > max_depth or current_url in visited or len(visited) >= max_pages:
                    return

                if "sitemap" in urlparse(current_url).path.lower() and current_url != url:
                    return

                visited.add(current_url)
                logger.info(f"Scraping competitor page {len(visited)}/{max_pages}: {current_url}")

                result = await scraper.scrape_single_page(current_url)

                # Only append genuinely successful content
                if result['success'] and result['markdown']:
                    content_list.append(result['markdown'])

                await asyncio.sleep(delay)

                if len(visited) < max_pages:
                    for href in _get_internal_links(result):
                        if len(visited) >= max_pages:
                            break
                        full_link = urljoin(current_url, href)
                        if urlparse(full_link).netloc == urlparse(url).netloc:
                            await crawl_recursive(full_link, depth + 1)

            await crawl_recursive(url, 0)

    except Exception as e:
        logger.error(f"Critical competitor scraper error for {url}: {e}")

    logger.info(f"Completed competitor scraping {len(visited)} pages, collected {len(content_list)} content pieces")
    return "\n\n".join(content_list)


async def scrape_multiple_competitors(competitor_urls: List[str], max_pages_per_site: int = 15, delay: float = None) -> Dict[str, str]:
    """
    Scrape multiple competitor websites sequentially and return a mapping
    of URL -> scraped markdown content.
    """
    results: Dict[str, str] = {}
    delay = delay if delay is not None else custom_settings.get('REQUEST_DELAY', 0.5)

    for i, url in enumerate(competitor_urls, 1):
        logger.info(f"Starting competitor {i}/{len(competitor_urls)}: {url}")
        try:
            content = await scrape_competitor_website(url, max_pages_per_site, delay)
            results[url] = content
            logger.info(f"Completed competitor {i}/{len(competitor_urls)}")

            if i < len(competitor_urls):
                await asyncio.sleep(delay * 2)  # Longer delay between different sites
        except Exception as e:
            logger.error(f"Failed to scrape competitor {url}: {e}")
            results[url] = ""

    return results