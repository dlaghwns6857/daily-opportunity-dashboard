from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, infer_amount, make_item, normalize_text, select_candidate_tags

BUSAN_URL = "https://youth.busan.go.kr/"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(BUSAN_URL, timeout=20, allow_redirects=True)
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(
        soup,
        [
            ".board_list li",
            ".notice_list li",
            ".list li",
            "li",
        ],
    )

    items: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, Tag):
            continue
        anchor = candidate.select_one("a[href]")
        if anchor is None:
            continue

        title = normalize_text(anchor.get_text(" ", strip=True))
        full_text = normalize_text(candidate.get_text(" ", strip=True))
        merged = f"{title} {full_text}"
        if not title or not any(keyword in merged for keyword in ["청년", "지원", "모집", "사업", "수당"]):
            continue

        deadline = extract_deadline(full_text, title)
        amount = infer_amount(full_text, title)
        item = make_item(
            source_code="busan",
            source_name="부산청년포털",
            category="지원금",
            title=title,
            org="부산광역시",
            deadline=deadline,
            url=absolute_url(response.url, anchor.get("href")),
            region="부산",
            amount=amount,
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
