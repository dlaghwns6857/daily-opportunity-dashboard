from __future__ import annotations

import requests

from scrapers import absolute_url, build_item_id, clean_title, extract_deadline, normalize_text

FSC_URL = "https://www.fsc.go.kr/no010104"
FSC_KEYWORDS = ["청년인턴", "인턴"]
FSC_MAX_PAGES = 8


def scrape(session: requests.Session) -> list[dict[str, object]]:
    from bs4 import BeautifulSoup

    items: list[dict[str, object]] = []

    for page in range(1, FSC_MAX_PAGES + 1):
        response = session.get(FSC_URL, params={"curPage": page}, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or response.encoding

        soup = BeautifulSoup(response.text, "html.parser")
        candidates = soup.select(".board-wrap li")
        if not candidates:
            break

        for candidate in candidates:
            anchor = candidate.select_one(".subject a[href]")
            if anchor is None:
                continue

            title = normalize_text(anchor.get_text(" ", strip=True))
            if not title or not any(keyword in title for keyword in FSC_KEYWORDS):
                continue

            date_text = normalize_text((candidate.select_one(".day") or candidate).get_text(" ", strip=True))
            full_text = normalize_text(candidate.get_text(" ", strip=True))
            deadline = extract_deadline(title, full_text, date_text)
            normalized_title = clean_title(title)
            if not normalized_title:
                continue

            items.append(
                {
                    "id": build_item_id("fsc", normalized_title),
                    "category": "채용",
                    "subcategory": "인턴",
                    "title": normalized_title,
                    "org": "금융위원회",
                    "deadline": deadline or date_text,
                    "url": absolute_url(FSC_URL, anchor.get("href")),
                    "source": "금융위원회",
                    "region": "전국",
                }
            )

    return items
