from __future__ import annotations

import re

from bs4 import Tag
import requests

from scrapers import extract_deadline, make_item, normalize_text

YOUTHDB_LIST_URL = "https://www.2030db.go.kr/user/youthIntern/selectYouthInternList.do"
YOUTHDB_DETAIL_URL = "https://www.2030db.go.kr/user/youthIntern/selectYouthInternDetail.do"

EXCLUDED_TITLE_KEYWORDS = [
    "합격자",
    "최종합격",
    "서류전형",
    "면접",
    "발표",
    "등록 안내",
    "등록일정",
    "후보자 등록",
]


def _extract_youth_id(candidate: Tag) -> str:
    anchor = candidate.select_one("a[onclick]")
    if anchor is None:
        return ""

    onclick = normalize_text(anchor.get("onclick"))
    match = re.search(r"fn_selectYouthInternDetail\('([^']+)'", onclick)
    if not match:
        return ""
    return normalize_text(match.group(1))


def _is_live_recruitment(status_text: str, title: str) -> bool:
    if status_text != "접수진행":
        return False
    if "청년인턴" not in title:
        return False
    if "채용" not in title and "재채용" not in title:
        return False
    return not any(keyword in title for keyword in EXCLUDED_TITLE_KEYWORDS)


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(YOUTHDB_LIST_URL, timeout=20)
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("tbody tr")

    items: list[dict[str, object]] = []
    for row in rows:
        if not isinstance(row, Tag):
            continue

        cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in row.select("td")]
        if len(cells) < 6:
            continue

        status_text = cells[2]
        title = cells[3]
        org = cells[4]
        period = cells[5]

        if not _is_live_recruitment(status_text, title):
            continue

        youth_id = _extract_youth_id(row)
        if not youth_id:
            continue

        detail_url = f"{YOUTHDB_DETAIL_URL}?youthId={youth_id}"
        deadline = extract_deadline(period)
        text_blob = normalize_text(f"{status_text} {title} {org} {period}")

        item = make_item(
            source_code="youthdb",
            source_name="청년인재DB",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=detail_url,
            text_blob=text_blob,
        )
        if item:
            items.append(item)

    return items