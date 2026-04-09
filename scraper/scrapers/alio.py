from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import extract_anchor, extract_cell_texts, extract_deadline, fetch_soup, make_item, normalize_text

ALIO_URL = "https://job.alio.go.kr/recruit.do?task=list"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    soup = fetch_soup(session, ALIO_URL)
    rows = soup.select("tbody tr") or soup.select("table tr")
    items: list[dict[str, object]] = []

    for row in rows:
        if not isinstance(row, Tag):
            continue
        title, url = extract_anchor(row, ALIO_URL)
        if not title:
            continue

        texts = extract_cell_texts(row)
        full_text = normalize_text(row.get_text(" ", strip=True))
        org = texts[1] if len(texts) > 1 else "잡알리오 등록기관"
        deadline = extract_deadline(*texts, full_text)

        item = make_item(
            source_code="alio",
            source_name="잡알리오",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=url,
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
