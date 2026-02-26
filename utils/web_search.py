import asyncio
import html
import logging
from urllib.parse import quote_plus
from xml.etree import ElementTree

import aiohttp

DUCKDUCKGO_RSS_URL = "https://duckduckgo.com/rss"


async def duckduckgo_search(query: str, max_results: int = 6, timeout_sec: int = 12) -> list[dict]:
    if not query.strip():
        return []

    url = f"{DUCKDUCKGO_RSS_URL}?q={quote_plus(query)}"

    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    headers = {
        "User-Agent": "EasySpeakBot/1.0 (+https://duckduckgo.com)",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    }

    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                rss_text = await response.text()
    except Exception as exc:
        logging.warning("DuckDuckGo search request failed: %s", exc)
        return []

    return await asyncio.to_thread(_parse_rss_results, rss_text, max_results)


def _parse_rss_results(rss_text: str, max_results: int) -> list[dict]:
    try:
        root = ElementTree.fromstring(rss_text)
    except Exception as exc:
        logging.warning("DuckDuckGo RSS parse failed: %s", exc)
        return []

    items = []
    for item in root.findall("./channel/item")[:max_results]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()

        clean_description = _strip_html(description)
        if not (title or clean_description or link):
            continue

        items.append({
            "title": title,
            "link": link,
            "snippet": clean_description,
        })

    return items


def _strip_html(text: str) -> str:
    plain = html.unescape(text)
    result = []
    inside_tag = False
    for char in plain:
        if char == "<":
            inside_tag = True
            continue
        if char == ">":
            inside_tag = False
            continue
        if not inside_tag:
            result.append(char)
    return " ".join("".join(result).split())


def format_search_results(results: list[dict]) -> str:
    if not results:
        return "No web results found."

    lines = []
    for idx, row in enumerate(results, start=1):
        lines.append(
            f"{idx}. {row.get('title', '').strip()}\n"
            f"URL: {row.get('link', '').strip()}\n"
            f"Snippet: {row.get('snippet', '').strip()}"
        )
    return "\n\n".join(lines)
