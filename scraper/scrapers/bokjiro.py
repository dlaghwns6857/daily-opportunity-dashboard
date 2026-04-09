from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, infer_amount, make_item, normalize_text, select_candidate_tags

BOKJIRO_URL = "https://www.bokjiro.go.kr/ssis-tbu/twatbz/mkclAsis/retrieveTwatbzList.do"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(
        BOKJIRO_URL,
        params={
            "keyword": "청년 현금 지원",
        },
        timeout=20,
    )
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(
        soup,
        [
            "tbody tr",
            ".service_list li",
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
        if not title or "청년" not in merged or not any(keyword in merged for keyword in ["수당", "지원", "급여", "현금", "월세", "저축"]):
            continue

        deadline = extract_deadline(full_text, title)
        amount = infer_amount(full_text, title)
        org = next(
            (
                text
                for text in [normalize_text(node.get_text(" ", strip=True)) for node in candidate.find_all(["span", "div", "td"])[:10]]
                if any(keyword in text for keyword in ["부", "청", "공단", "센터", "광역시", "복지"])
            ),
            "복지로",
        )

        item = make_item(
            source_code="bokjiro",
            source_name="복지로",
            category="지원금",
            title=title,
            org=org,
            deadline=deadline,
            url=absolute_url(BOKJIRO_URL, anchor.get("href")),
            amount=amount,
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
