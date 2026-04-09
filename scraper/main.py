from __future__ import annotations

import json
from pathlib import Path

from scrapers import build_session, now_iso_timestamp
from scrapers.alio import scrape as scrape_alio
from scrapers.bokjiro import scrape as scrape_bokjiro
from scrapers.busan import scrape as scrape_busan
from scrapers.fsc import scrape as scrape_fsc
from scrapers.jobkorea import scrape as scrape_jobkorea
from scrapers.worknet import scrape as scrape_worknet
from scrapers.youth import scrape as scrape_youth
from scrapers.youthdb import scrape as scrape_youthdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_ROOT / "data" / "posts.json"

SOURCE_URLS = {
    "잡알리오": "https://job.alio.go.kr",
    "워크넷": "https://www.work.go.kr",
    "잡코리아": "https://www.jobkorea.co.kr",
    "금융위원회": "https://www.fsc.go.kr",
    "온통청년": "https://www.youthcenter.go.kr",
    "청년인재DB": "https://www.2030db.go.kr/user/youthIntern/selectYouthInternList.do",
    "복지로": "https://www.bokjiro.go.kr",
    "부산청년포털": "https://youth.busan.go.kr",
}

SCRAPERS = [
    ("잡알리오", scrape_alio),
    ("워크넷", scrape_worknet),
    ("잡코리아", scrape_jobkorea),
    ("금융위원회", scrape_fsc),
    ("온통청년", scrape_youth),
    ("청년인재DB", scrape_youthdb),
    ("복지로", scrape_bokjiro),
    ("부산청년포털", scrape_busan),
]


def load_existing_ids() -> set[str]:
    if not DATA_PATH.exists():
        return set()
    try:
        with DATA_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return set()

    items = data.get("items", [])
    return {item.get("id", "") for item in items if isinstance(item, dict) and item.get("id")}


def load_existing_items() -> list[dict[str, object]]:
    if not DATA_PATH.exists():
        return []
    try:
        with DATA_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    items = data.get("items", [])
    return [item for item in items if isinstance(item, dict)]


def dedupe_and_mark(items: list[dict[str, object]], existing_ids: set[str]) -> list[dict[str, object]]:
    deduped: list[dict[str, object]] = []
    seen_ids: set[str] = set()

    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id or item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        item["is_new"] = item_id not in existing_ids
        deduped.append(item)

    deduped.sort(
        key=lambda item: (
            str(item.get("deadline", "9999-12-31")),
            str(item.get("category", "")),
            str(item.get("title", "")),
        )
    )
    return deduped


def build_failed_source(label: str, reason: str) -> dict[str, str]:
    return {
        "name": label,
        "url": SOURCE_URLS.get(label, ""),
        "reason": reason,
    }


def write_posts(items: list[dict[str, object]], failed_sources: list[dict[str, str]]) -> None:
    payload = {
        "updated_at": now_iso_timestamp(),
        "failed_sources": failed_sources,
        "items": items,
    }
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
        file.write("\n")


def main() -> None:
    existing_ids = load_existing_ids()
    existing_items = load_existing_items()
    session = build_session()
    collected: list[dict[str, object]] = []
    failed_sources: list[dict[str, str]] = []

    for label, scraper in SCRAPERS:
        try:
            items = scraper(session)
            collected.extend(items)
            print(f"{label}: {len(items)}개 수집")
            if not items:
                failed_sources.append(build_failed_source(label, "0건 수집"))
        except Exception as error:
            print(f"{label}: 실패 ({error})")
            failed_sources.append(build_failed_source(label, f"수집 실패: {error}"))

    final_items = dedupe_and_mark(collected, existing_ids)
    if not final_items:
        if existing_items:
            write_posts(existing_items, failed_sources)
            print("완료: 총 0개 항목 수집 (기존 데이터 유지)")
            return
        write_posts([], failed_sources)
        print("완료: 총 0개 항목 수집")
        return

    write_posts(final_items, failed_sources)
    print(f"완료: 총 {len(final_items)}개 항목 수집")


if __name__ == "__main__":
    main()