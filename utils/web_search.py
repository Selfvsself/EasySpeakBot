import logging

from ddgs import DDGS


async def duckduckgo_search(query: str, max_results: int = 10) -> list[dict]:
    if not query.strip():
        return []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query=query,
                max_results=max_results,
                region="us-en",
                safesearch="on",
                backend="api"
            )

            return [
                {
                    "title": r.get("title"),
                    "link": r.get("href"),
                    "snippet": r.get("body")
                }
                for r in results
            ]
    except Exception as exc:
        logging.warning("DuckDuckGo search failed: %s", exc)
        return []


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
