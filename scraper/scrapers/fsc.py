from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, make_item, normalize_text, select_candidate_tags

FSC_URL = "https://www.fsc.go.kr/no010104"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(FSC_URL, timeout=20)
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(soup, ["tbody tr", ".board_list li", "li"])

    items: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, Tag):
            continue

        anchor = candidate.select_one("a[href]")
        if anchor is None:
            continue
        title = normalize_text(anchor.get_text(" ", strip=True))
        full_text = normalize_text(candidate.get_text(" ", strip=True))
        if not title or not any(keyword in f"{title} {full_text}" for keyword in ["청년인턴", "청년보좌역", "인턴"]):
            continue

        deadline = extract_deadline(title, full_text)
        item = make_item(
            source_code="fsc",
            source_name="금융위원회",
            category="채용",
            title=title,
            org="금융위원회",
            deadline=deadline,
            url=absolute_url(FSC_URL, anchor.get("href")),
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
