from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, make_item, normalize_text, select_candidate_tags

WORKNET_URL = "https://www.work.go.kr/empInfo/empInfoSrch/list/dtlEmpSrchList.do"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(
        WORKNET_URL,
        params={
            "region": "부산",
            "keyword": "공공기관 인턴 신입",
        },
        timeout=20,
    )
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(
        soup,
        [
            "#contents tbody tr",
            ".list tbody tr",
            ".cp_list li",
            ".jobsList li",
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
        if not title or not any(keyword in title for keyword in ["인턴", "신입", "채용", "공공"]):
            continue

        cells = [normalize_text(node.get_text(" ", strip=True)) for node in candidate.find_all(["td", "span", "div"])[:10]]
        full_text = normalize_text(candidate.get_text(" ", strip=True))
        deadline = extract_deadline(full_text, *cells)
        org = next((cell for cell in cells if "공사" in cell or "공단" in cell or "기관" in cell or "은행" in cell), "워크넷 등록기관")

        item = make_item(
            source_code="worknet",
            source_name="워크넷",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=absolute_url(WORKNET_URL, anchor.get("href")),
            region="부산",
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
