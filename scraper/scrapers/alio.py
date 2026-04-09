from __future__ import annotations

import json
import time

from bs4 import Tag
import requests

from scrapers import absolute_url, extract_cell_texts, extract_deadline, make_item, normalize_text

ALIO_API_URL = "https://opendata.alio.go.kr/recruit/list"
ALIO_MAIN_URL = "https://job.alio.go.kr/recruit.do"
ALIO_TIMEOUT = 10
ALIO_RETRY_COUNT = 3
ALIO_RETRY_DELAY = 2
ALIO_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)


def _get_with_retry(session: requests.Session, url: str, **kwargs) -> requests.Response | None:
    session.headers.setdefault("User-Agent", ALIO_USER_AGENT)

    for attempt in range(1, ALIO_RETRY_COUNT + 1):
        try:
            response = session.get(url, timeout=ALIO_TIMEOUT, **kwargs)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or response.encoding
            return response
        except requests.RequestException as error:
            print(f"잡알리오 요청 실패 ({attempt}/{ALIO_RETRY_COUNT}) [{url}]: {error}")
            if attempt < ALIO_RETRY_COUNT:
                time.sleep(ALIO_RETRY_DELAY)

    print(f"잡알리오 요청 3회 모두 실패: {url}")
    return None


def _parse_html_rows(soup, base_url: str) -> list[dict[str, object]]:
    rows = soup.select("tbody tr") or soup.select("table tr")
    items: list[dict[str, object]] = []

    for row in rows:
        if not isinstance(row, Tag):
            continue

        texts = extract_cell_texts(row)
        if len(texts) < 8:
            continue

        anchor = row.select_one('a[href*="recruitview.do"]')
        if anchor is None:
            continue

        title = texts[2]
        org = texts[3]
        deadline = extract_deadline(texts[7], *texts)
        full_text = normalize_text(row.get_text(" ", strip=True))

        item = make_item(
            source_code="alio",
            source_name="잡알리오",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=absolute_url(base_url, anchor.get("href")),
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items


def _parse_api_response(response: requests.Response) -> list[dict[str, object]]:
    content_type = (response.headers.get("content-type") or "").lower()
    if "json" not in content_type:
        return []

    try:
        payload = response.json()
    except json.JSONDecodeError:
        return []

    records: list[dict[str, object]] = []
    if isinstance(payload, list):
        records = [record for record in payload if isinstance(record, dict)]
    elif isinstance(payload, dict):
        for key in ["items", "list", "data", "result", "results"]:
            value = payload.get(key)
            if isinstance(value, list):
                records = [record for record in value if isinstance(record, dict)]
                break

    items: list[dict[str, object]] = []
    for record in records:
        title = normalize_text(
            str(
                record.get("recrutPbancTtl")
                or record.get("title")
                or record.get("recruitTitle")
                or record.get("pbancNm")
                or ""
            )
        )
        org = normalize_text(
            str(
                record.get("instNm")
                or record.get("orgNm")
                or record.get("institutionName")
                or "잡알리오 등록기관"
            )
        )
        detail_url = normalize_text(
            str(
                record.get("detailUrl")
                or record.get("url")
                or record.get("recrutUrlAddr")
                or record.get("homepageUrlAddr")
                or ""
            )
        )
        deadline = extract_deadline(
            str(record.get("aplyEndDt") or ""),
            str(record.get("endDate") or ""),
            str(record.get("recrutEndDt") or ""),
            str(record.get("dday") or ""),
        )

        item = make_item(
            source_code="alio",
            source_name="잡알리오",
            category="채용",
            title=title,
            org=org,
            deadline=deadline,
            url=detail_url or ALIO_MAIN_URL,
            text_blob=normalize_text(json.dumps(record, ensure_ascii=False)),
        )
        if item:
            items.append(item)

    return items


def scrape(session: requests.Session) -> list[dict[str, object]]:
    from bs4 import BeautifulSoup

    api_response = _get_with_retry(session, ALIO_API_URL, allow_redirects=True)
    if api_response is not None:
        api_items = _parse_api_response(api_response)
        if api_items:
            return api_items

        api_soup = BeautifulSoup(api_response.text, "html.parser")
        api_html_items = _parse_html_rows(api_soup, api_response.url)
        if api_html_items:
            return api_html_items

    main_response = _get_with_retry(session, ALIO_MAIN_URL)
    if main_response is None:
        return []

    main_soup = BeautifulSoup(main_response.text, "html.parser")
    return _parse_html_rows(main_soup, ALIO_MAIN_URL)
