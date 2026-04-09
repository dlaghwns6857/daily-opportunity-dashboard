from __future__ import annotations

import json
import requests

from scrapers import absolute_url, extract_deadline, infer_amount, make_item, normalize_text

YOUTH_HOME_URL = "https://www.youthcenter.go.kr"
YOUTH_LIST_URL = f"{YOUTH_HOME_URL}/youthPolicy/ythPlcyTotalSearch"
YOUTH_LIST_API_URL = f"{YOUTH_HOME_URL}/wrk/yrm/plcyInfo/selectPlcy"
YOUTH_DETAIL_API_URL = f"{YOUTH_HOME_URL}/wrk/yrm/plcyInfo/plcy/{{plcy_no}}"
YOUTH_PAGE_SIZE = 60
YOUTH_MAX_ITEMS = 40

SUPPORT_KEYWORDS = [
    "지원",
    "지원금",
    "수당",
    "장려금",
    "월세",
    "주거",
    "창업",
    "적금",
    "금융",
    "복지",
    "바우처",
    "생활",
    "자립",
]


def _format_compact_date(value: str | None) -> str | None:
    text = normalize_text(value)
    digits = "".join(character for character in text if character.isdigit())
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"
    return None


def _build_amount(detail: dict[str, object], merged_text: str) -> str | None:
    earn_min = int(detail.get("earnMinAmt") or 0)
    earn_max = int(detail.get("earnMaxAmt") or 0)
    if earn_max > 0 and earn_min > 0:
        return f"{earn_min:,}원~{earn_max:,}원"
    if earn_max > 0:
        return f"최대 {earn_max:,}원"
    if earn_min > 0:
        return f"최소 {earn_min:,}원"
    return infer_amount(merged_text)


def _pick_deadline(detail: dict[str, object], merged_text: str) -> str | None:
    for key in ["aplyPrdEndYmd", "lastAplyPrdEndYmd", "bizPrdEndYmd"]:
        formatted = _format_compact_date(str(detail.get(key) or ""))
        if formatted:
            return formatted
    return extract_deadline(str(detail.get("aplyPeriod") or ""), merged_text)


def _is_support_item(merged_text: str, region_text: str) -> bool:
    if any(keyword in merged_text for keyword in SUPPORT_KEYWORDS):
        return True
    return "부산" in region_text and any(keyword in merged_text for keyword in ["청년", "지원", "수당"])


def scrape(session: requests.Session) -> list[dict[str, object]]:
    home_response = session.get(YOUTH_HOME_URL, timeout=20)
    home_response.raise_for_status()

    list_response = session.post(
        YOUTH_LIST_API_URL,
        json={
            "paggingVO": {"pageNum": 0, "pageSize": YOUTH_PAGE_SIZE},
            "plcyReq": {
                "useYn": "Y",
                "plcyAprvSttsCd": "0044002",
            },
        },
        headers={
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": YOUTH_LIST_URL,
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=20,
    )
    list_response.raise_for_status()
    payload = list_response.json()
    candidates = payload.get("result", {}).get("plcyList", [])

    items: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        region_text = normalize_text(str(candidate.get("stdgCtpvSggCdList") or ""))
        title = normalize_text(str(candidate.get("plcyNm") or ""))
        org = normalize_text(
            str(candidate.get("operInstCdNm") or candidate.get("rgtrInstCdNm") or candidate.get("rgtrUpInstCdNm") or "온통청년")
        )
        preview_text = normalize_text(
            " ".join(
                str(candidate.get(key) or "")
                for key in ["plcyExplnCn", "plcySprtCn", "userLclsfNm", "rgtrUpInstCdNm", "stdgCtpvSggCdList"]
            )
        )
        merged_preview = normalize_text(f"{title} {org} {preview_text} {region_text}")
        if not title or not _is_support_item(merged_preview, region_text):
            continue

        plcy_no = normalize_text(str(candidate.get("plcyNo") or ""))
        detail_response = session.get(
            YOUTH_DETAIL_API_URL.format(plcy_no=plcy_no),
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": YOUTH_LIST_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
            timeout=20,
        )
        detail_response.raise_for_status()
        detail_payload = detail_response.json().get("result", {}).get("plcy", {})
        detail_text = normalize_text(
            " ".join(
                str(detail_payload.get(key) or "")
                for key in [
                    "plcyExplnCn",
                    "plcySprtCn",
                    "etcMttrCn",
                    "addAplyQlfcCndCn",
                    "refUrlAddr1",
                    "refUrlAddr2",
                ]
            )
        )
        merged_text = normalize_text(f"{merged_preview} {detail_text}")
        if not _is_support_item(merged_text, region_text):
            continue

        deadline = _pick_deadline(detail_payload, merged_text)
        amount = _build_amount(detail_payload, merged_text)
        detail_url = absolute_url(YOUTH_HOME_URL, f"/youthPolicy/ythPlcyTotalSearch/ythPlcyDetail/{plcy_no}")

        item = make_item(
            source_code="youth",
            source_name="온통청년",
            category="지원금",
            title=title,
            org=org,
            deadline=deadline,
            url=detail_url,
            region="부산" if "부산" in region_text else None,
            amount=amount,
            text_blob=merged_text,
        )
        if item:
            items.append(item)
        if len(items) >= YOUTH_MAX_ITEMS:
            break

    return items
