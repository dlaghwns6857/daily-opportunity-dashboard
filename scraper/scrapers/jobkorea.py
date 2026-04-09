from __future__ import annotations

import re

import requests

from scrapers import absolute_url, extract_deadline, fetch_text, make_item, normalize_text

JOBKOREA_URL = "https://www.jobkorea.co.kr/Search/"

FINANCE_KEYWORDS = ["금융", "은행", "보험", "증권", "카드", "캐피탈", "인슈어런스"]
HIRING_KEYWORDS = ["인턴", "신입", "채용", "공개채용"]


def _extract_company(detail_title: str) -> str:
    if " 채용 - " in detail_title:
        return normalize_text(detail_title.split(" 채용 - ", 1)[0])
    return "잡코리아 등록기업"


def _extract_title(detail_html: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(detail_html, "html.parser")
    heading = soup.select_one("h1")
    if heading is not None:
        title = normalize_text(heading.get_text(" ", strip=True))
        if title:
            return title

    if soup.title is not None:
        title_text = normalize_text(soup.title.get_text(" ", strip=True))
        if " 채용 - " in title_text:
            remainder = title_text.split(" 채용 - ", 1)[1]
            return normalize_text(remainder.replace("| 잡코리아", ""))

    return ""


def _extract_deadline_from_detail(detail_html: str) -> str | None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(detail_html, "html.parser")
    text = soup.get_text("\n", strip=True)
    match = re.search(r"마감일\s*(20\d{2}\.\d{2}\.\d{2})", text)
    if match:
        return extract_deadline(match.group(1))

    return extract_deadline(text)


def scrape(session: requests.Session) -> list[dict[str, object]]:
    from bs4 import BeautifulSoup

    search_html = fetch_text(
        session,
        JOBKOREA_URL,
        params={
            "stext": "금융 인턴",
            "ctcd": "I210",
        },
    )
    soup = BeautifulSoup(search_html, "html.parser")

    items: list[dict[str, object]] = []
    seen_urls: set[str] = set()

    for anchor in soup.select('a[href*="GI_Read"]'):
        href = absolute_url(JOBKOREA_URL, anchor.get("href"))
        if href in seen_urls:
            continue
        seen_urls.add(href)

        candidate_text = normalize_text(anchor.get_text(" ", strip=True))
        parent = anchor.find_parent(["li", "article", "div"])
        list_blob = normalize_text(parent.get_text(" ", strip=True)) if parent is not None else candidate_text
        merged = f"{candidate_text} {list_blob}"

        if not any(keyword in merged for keyword in HIRING_KEYWORDS):
            continue
        if not any(keyword in merged for keyword in FINANCE_KEYWORDS):
            continue

        detail_html = fetch_text(session, href)
        detail_soup = BeautifulSoup(detail_html, "html.parser")
        detail_title = normalize_text(detail_soup.title.get_text(" ", strip=True)) if detail_soup.title else ""
        title = _extract_title(detail_html) or candidate_text
        deadline = _extract_deadline_from_detail(detail_html)
        org = _extract_company(detail_title)

        detail_blob = normalize_text(detail_soup.get_text(" ", strip=True))

        item = make_item(
            source_code="jobkorea",
            source_name="잡코리아",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=href,
            text_blob=f"{list_blob} {detail_blob}",
        )
        if item:
            items.append(item)

        if len(items) >= 20:
            break

    return items
