from __future__ import annotations

from datetime import date
from math import ceil
import requests

from scrapers import make_item, normalize_text

BOKJIRO_HOME_URL = "https://www.bokjiro.go.kr/ssis-tbu/index.do"
BOKJIRO_SEARCH_PAGE_URL = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52005M.do"
BOKJIRO_SEARCH_API_URL = "https://www.bokjiro.go.kr/ssis-tbu/TWAT52005M/twataa/wlfareInfo/selectWlfareInfo.do"
BOKJIRO_DETAIL_URL = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do"
BOKJIRO_ALT_DETAIL_URL = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52015M.do"

BOKJIRO_REGION = "부산"
BOKJIRO_SIDO_CD = "26"
BOKJIRO_SEARCH_TERM = "청년"
BOKJIRO_PERIOD = "청년"
BOKJIRO_PAGE_SIZE = 9


def _prime_session(session: requests.Session) -> None:
    session.get(BOKJIRO_HOME_URL, timeout=20)
    session.get(
        BOKJIRO_SEARCH_PAGE_URL,
        params={
            "page": 1,
            "orderBy": "date",
            "tabId": 1,
            "period": BOKJIRO_PERIOD,
            "sidoCd": BOKJIRO_SIDO_CD,
            "searchTerm": BOKJIRO_SEARCH_TERM,
        },
        timeout=20,
    )


def _build_payload(page: int) -> dict[str, dict[str, str]]:
    return {
        "dmSearchParam": {
            "page": str(page),
            "tabId": "1",
            "orderBy": "date",
            "bkjrLftmCycCd": "",
            "daesang": "",
            "period": BOKJIRO_PERIOD,
            "age": "",
            "region": BOKJIRO_REGION,
            "jjim": "",
            "subject": "",
            "favoriteKeyword": "Y",
            "sidoCd": BOKJIRO_SIDO_CD,
            "sggCd": "",
            "endYn": "N",
            "onlineYn": "",
            "searchTerm": BOKJIRO_SEARCH_TERM,
        }
    }


def _parse_return_str(value: str | None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for chunk in normalize_text(value).split(";"):
        if ":" not in chunk:
            continue
        key, raw_value = chunk.split(":", 1)
        parsed[normalize_text(key)] = normalize_text(raw_value)
    return parsed


def _has_target_age(age_text: str, life_cycle_text: str, title: str, body: str) -> bool:
    merged = f"{title} {body} {age_text} {life_cycle_text}"
    if "청년" in merged:
        return True
    for token in ["19~34세", "19~39세", "20~34세", "18~34세"]:
        if token in age_text:
            return True
    return False


def _has_supported_benefit_type(benefit_type: str) -> bool:
    return "현금" in benefit_type or "현물" in benefit_type


def _normalize_deadline(raw_value: str | None) -> str:
    text = normalize_text(raw_value)
    if len(text) == 8 and text.isdigit():
        year = int(text[:4])
        month = int(text[4:6])
        day = int(text[6:8])
        if year >= 2000:
            return f"{year:04d}-{month:02d}-{day:02d}"
    return "2099-12-31"


def _build_detail_url(row: dict[str, object]) -> str:
    detail_base = BOKJIRO_DETAIL_URL
    if normalize_text(str(row.get("WLFARE_GDNC_TRGT_KCD", ""))) == "03":
        detail_base = BOKJIRO_ALT_DETAIL_URL
    return f"{detail_base}?wlfareInfoId={normalize_text(str(row.get('WLFARE_INFO_ID', '')))}"


def _collect_rows(session: requests.Session) -> list[dict[str, object]]:
    response = session.post(
        BOKJIRO_SEARCH_API_URL,
        json=_build_payload(1),
        headers={"Content-Type": "application/json", "Referer": BOKJIRO_SEARCH_PAGE_URL},
        timeout=20,
    )
    response.raise_for_status()
    first_page = response.json()

    count_map = first_page.get("dmCount", {})
    max_count = max(
        int(count_map.get("dsServiceList1Count", 0) or 0),
        int(count_map.get("dsServiceList2Count", 0) or 0),
        int(count_map.get("dsServiceList3Count", 0) or 0),
    )
    max_pages = max(1, ceil(max_count / BOKJIRO_PAGE_SIZE))

    pages = [first_page]
    for page in range(2, max_pages + 1):
        page_response = session.post(
            BOKJIRO_SEARCH_API_URL,
            json=_build_payload(page),
            headers={"Content-Type": "application/json", "Referer": BOKJIRO_SEARCH_PAGE_URL},
            timeout=20,
        )
        page_response.raise_for_status()
        pages.append(page_response.json())

    rows: list[dict[str, object]] = []
    for page_data in pages:
        for key in ["dsServiceList1", "dsServiceList2", "dsServiceList3"]:
            dataset = page_data.get(key, [])
            if isinstance(dataset, list):
                rows.extend(row for row in dataset if isinstance(row, dict))
    return rows


def scrape(session: requests.Session) -> list[dict[str, object]]:
    _prime_session(session)
    rows = _collect_rows(session)

    items: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for row in rows:
        service_id = normalize_text(str(row.get("WLFARE_INFO_ID", "")))
        if not service_id or service_id in seen_ids:
            continue

        title = normalize_text(str(row.get("WLFARE_INFO_NM", "")))
        outline = normalize_text(str(row.get("WLFARE_INFO_OUTL_CN", "")))
        tag_name = normalize_text(str(row.get("TAG_NM", "")))
        org = normalize_text(str(row.get("BIZ_CHR_INST_NM", ""))) or "복지로"
        addr = normalize_text(str(row.get("ADDR", "")))
        meta = _parse_return_str(str(row.get("RETURN_STR", "")))
        age_text = meta.get("WLFARE_INFO_AGGRP_CD", "")
        life_cycle_text = meta.get("BKJR_LFTM_CYC_CD", "")
        benefit_type = meta.get("WLBZSL_TCD", "")
        full_text = normalize_text(" ".join([title, outline, tag_name, org, addr, str(row.get("RETURN_STR", ""))]))

        if not _has_target_age(age_text, life_cycle_text, title, full_text):
            continue
        if not _has_supported_benefit_type(benefit_type):
            continue

        seen_ids.add(service_id)

        deadline = _normalize_deadline(str(row.get("ENFC_END_YMD", "")))

        item = make_item(
            source_code="bokjiro",
            source_name="복지로",
            category="지원금",
            title=title,
            org=org,
            deadline=deadline,
            url=_build_detail_url(row),
            region=BOKJIRO_REGION,
            text_blob=full_text,
        )
        if item:
            items.append(item)

    return items
