from __future__ import annotations

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_deadline, infer_amount, make_item, normalize_text, select_candidate_tags

YOUTH_URL = "https://www.youthcenter.go.kr/youngPlcyList.do"


def scrape(session: requests.Session) -> list[dict[str, object]]:
    response = session.get(
        YOUTH_URL,
        params={
            "srchSido": "부산",
            "keyword": "청년 수당 지원금",
        },
        timeout=20,
        allow_redirects=True,
    )
    response.raise_for_status()

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = select_candidate_tags(
        soup,
        [
            "tbody tr",
            ".list_wrap li",
            ".policy_list li",
            ".cont_list li",
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
        if not title or not any(keyword in merged for keyword in ["청년", "수당", "지원", "월세", "자격증", "창업"]):
            continue

        deadline = extract_deadline(full_text, title)
        amount = infer_amount(full_text, title)
        org = next(
            (
                text
                for text in [normalize_text(node.get_text(" ", strip=True)) for node in candidate.find_all(["span", "div", "td"])[:10]]
                if any(keyword in text for keyword in ["부산", "광역시", "부", "센터", "진흥원", "부처", "공단"])
            ),
            "온통청년",
        )

        item = make_item(
            source_code="youth",
            source_name="온통청년",
            category="지원금",
            title=title,
            org=org,
            deadline=deadline,
            url=absolute_url(response.url, anchor.get("href")),
            region="부산" if "부산" in merged else None,
            amount=amount,
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
