from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

DEFAULT_TIMEOUT = 20


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_soup(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, object] | None = None,
    data: dict[str, object] | None = None,
    method: str = "GET",
) -> BeautifulSoup:
    response = session.request(
        method=method,
        url=url,
        params=params,
        data=data,
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def absolute_url(base_url: str, href: str | None) -> str:
    if not href:
        return base_url
    return urljoin(base_url, href)


def parse_date_text(value: str | None) -> date | None:
    text = normalize_text(value)
    if not text:
        return None

    text = text.replace("년", ".").replace("월", ".").replace("일", "")
    text = text.replace("/", ".").replace("-", ".")
    text = re.sub(r"[^0-9. ]", " ", text)

    full_matches = re.findall(r"(20\d{2}|19\d{2})\.(\d{1,2})\.(\d{1,2})", text)
    if full_matches:
        year, month, day = full_matches[-1]
        return safe_date(int(year), int(month), int(day))

    short_matches = re.findall(r"\b(\d{2})\.(\d{1,2})\.(\d{1,2})\b", text)
    if short_matches:
        year, month, day = short_matches[-1]
        return safe_date(2000 + int(year), int(month), int(day))

    month_day_matches = re.findall(r"\b(\d{1,2})\.(\d{1,2})\b", text)
    if month_day_matches:
        month, day = month_day_matches[-1]
        today = date.today()
        candidate = safe_date(today.year, int(month), int(day))
        if candidate is None:
            return None
        if candidate < today.replace(month=1, day=1):
            return safe_date(today.year + 1, int(month), int(day))
        return candidate

    return None


def safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None


def iso_date(value: date) -> str:
    return value.isoformat()


def extract_deadline(*texts: str) -> str | None:
    for text in texts:
        parsed = parse_date_text(text)
        if parsed is not None:
            return iso_date(parsed)
    return None


def is_expired(deadline: str | None) -> bool:
    if not deadline:
        return True
    parsed = parse_date_text(deadline)
    if parsed is None:
        return True
    return parsed < date.today()


def infer_region(*texts: str) -> str:
    merged = " ".join(normalize_text(text) for text in texts)
    if "부산" in merged:
        return "부산"
    return "전국"


def infer_subcategory(category: str, title: str, body: str) -> str:
    merged = f"{title} {body}"
    if category == "채용":
        if "체험형" in merged and "인턴" in merged:
            return "체험형 인턴"
        if "인턴" in merged:
            return "인턴"
        if "신입" in merged:
            return "신입"
        return "채용"

    if "청년수당" in merged:
        return "청년수당"
    if "월세" in merged or "주거" in merged:
        return "주거지원"
    if "창업" in merged:
        return "창업지원"
    if "취업" in merged or "자격증" in merged:
        return "취업지원"
    if "생활" in merged or "저축" in merged:
        return "생활지원"
    return "지원사업"


def infer_amount(*texts: str) -> str | None:
    patterns = [
        r"(월\s*최대?\s*[0-9,]+\s*만\s*원(?:\s*[x×]\s*\d+\s*개월)?)",
        r"(월\s*[0-9,]+\s*만\s*원(?:\s*[x×]\s*\d+\s*개월)?)",
        r"(연\s*최대?\s*[0-9,]+\s*만\s*원)",
        r"(최대\s*[0-9,]+\s*만\s*원(?:\s*사업화\s*자금)?)",
        r"([0-9,]+\s*만\s*원\s*지급)",
    ]
    for text in texts:
        normalized = normalize_text(text)
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return normalize_text(match.group(1).replace("만 원", "만원"))
    return None


def build_item_id(source_code: str, title: str) -> str:
    digest = hashlib.sha1(normalize_text(title).encode("utf-8")).hexdigest()[:10]
    return f"{source_code}_{digest}"


def extract_anchor(tag: Tag, base_url: str) -> tuple[str, str]:
    anchors = [anchor for anchor in tag.select("a[href]") if normalize_text(anchor.get_text(" ", strip=True))]
    if not anchors:
        return "", base_url

    best_anchor = max(anchors, key=lambda anchor: len(normalize_text(anchor.get_text(" ", strip=True))))
    title = normalize_text(best_anchor.get_text(" ", strip=True))
    href = absolute_url(base_url, best_anchor.get("href"))
    return title, href


def extract_cell_texts(tag: Tag) -> list[str]:
    cells = tag.find_all(["td", "th"])
    return [normalize_text(cell.get_text(" ", strip=True)) for cell in cells if normalize_text(cell.get_text(" ", strip=True))]


def iter_unique_tags(tags: Iterable[Tag]) -> list[Tag]:
    seen: set[int] = set()
    unique: list[Tag] = []
    for tag in tags:
        identity = id(tag)
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(tag)
    return unique


def select_candidate_tags(soup: BeautifulSoup, selectors: list[str]) -> list[Tag]:
    selected: list[Tag] = []
    for selector in selectors:
        selected.extend(tag for tag in soup.select(selector) if isinstance(tag, Tag))
    return iter_unique_tags(selected)


def clean_title(title: str) -> str:
    title = normalize_text(title)
    title = re.sub(r"^N\s+", "", title)
    return title


def make_item(
    *,
    source_code: str,
    source_name: str,
    category: str,
    title: str,
    org: str,
    deadline: str | None,
    url: str,
    region: str | None = None,
    subcategory: str | None = None,
    amount: str | None = None,
    text_blob: str = "",
) -> dict[str, object] | None:
    cleaned_title = clean_title(title)
    if not cleaned_title or len(cleaned_title) < 4:
        return None
    if not url:
        return None
    if is_expired(deadline):
        return None

    blob = normalize_text(text_blob)
    item = {
        "id": build_item_id(source_code, cleaned_title),
        "category": category,
        "subcategory": subcategory or infer_subcategory(category, cleaned_title, blob),
        "title": cleaned_title,
        "org": normalize_text(org) or source_name,
        "deadline": normalize_text(deadline),
        "url": url,
        "source": source_name,
        "region": region or infer_region(cleaned_title, blob, org),
    }
    if amount:
        item["amount"] = normalize_text(amount)
    return item


def now_iso_timestamp() -> str:
    return datetime.now().replace(microsecond=0).isoformat()
