from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, make_item, normalize_text, select_candidate_tags

JOBKOREA_URL = "https://www.jobkorea.co.kr/Search/"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(
        JOBKOREA_URL,
        params={
            "stext": "금융 인턴",
            "ctcd": "I210",
        },
        timeout=20,
    )
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(
        soup,
        [
            ".list-default .list-post",
            ".list .post",
            ".recruit-info > li",
            "article",
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

        if not title or "인턴" not in f"{title} {full_text}" or "금융" not in f"{title} {full_text}":
            continue

        nodes = candidate.find_all(["span", "div", "dd", "dt"])
        texts = [normalize_text(node.get_text(" ", strip=True)) for node in nodes[:14] if normalize_text(node.get_text(" ", strip=True))]
        org = next((text for text in texts if any(keyword in text for keyword in ["은행", "카드", "캐피탈", "증권", "보험", "금융"])), "잡코리아 등록기업")
        deadline = extract_deadline(full_text, *texts)

        item = make_item(
            source_code="jobkorea",
            source_name="잡코리아",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=absolute_url(JOBKOREA_URL, anchor.get("href")),
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
