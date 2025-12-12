# -*- coding: utf-8 -*-
"""
Парсер стажировок с https://it.fut.ru/internship.
Источник: публичное API Fut.ru (CMS).
Заполняет поля:
- title
- company
- description (текст без HTML, формируем из description/text)
- url (каноническая ссылка)
- type = "internship"
- vacancy_created_at (published_at в UTC, если есть)
- created_at (текущее UTC)
- deadline_at (если есть явный дедлайн; иначе None)
- contact_info / contact_info_encrypted отсутствуют в источнике -> None
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests

from sentry_service import get_service_logger, init_sentry

BASE_LIST_URL = "https://it.fut.ru/api/cms/api/publications"
SITE_BASE = "https://it.fut.ru"

logger = get_service_logger("internships_parser")


def _parse_dt(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    try:
        # API возвращает строки вроде "2023-12-31 05:12" или ISO с Z
        if "T" in val:
            return datetime.fromisoformat(val.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        dt = datetime.strptime(val, "%Y-%m-%d %H:%M")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return None


def _extract_text(blocks: Optional[Dict]) -> str:
    """
    Разворачиваем editor.js структуру (blocks) в плоский текст.
    """
    if not isinstance(blocks, dict):
        return ""
    out: List[str] = []
    for blk in blocks.get("blocks", []):
        data = blk.get("data", {}) if isinstance(blk, dict) else {}
        txt = data.get("text") or data.get("title") or data.get("items")
        if isinstance(txt, list):
            out.append("\n".join(str(x) for x in txt if x))
        elif txt:
            out.append(str(txt))
    return "\n".join([t.replace("\xa0", " ") for t in out if t]).strip()


def fetch_internships(limit: int = 100, direction: str = "it") -> List[Dict]:
    """
    Получаем стажировки из публичного API.
    direction='it' — ограничиваем IT-направлением (поле direction).
    """
    params = {
        "type": "internship",
        "offset": 0,
        "limit": limit,
        "direction": direction,
    }
    try:
        resp = requests.get(BASE_LIST_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logger.exception("Failed to fetch internships list from %s with params=%s", BASE_LIST_URL, params)
        raise
    items = data.get("data", [])

    results: List[Dict] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for item in items:
        title = item.get("title") or ""
        company = ""
        comp = item.get("company") or {}
        if isinstance(comp, dict):
            company = comp.get("caption") or comp.get("alias") or ""

        description_parts: List[str] = []
        if item.get("description"):
            description_parts.append(str(item.get("description")))
        if item.get("text"):
            description_parts.append(_extract_text(item.get("text")))
        if comp and isinstance(comp, dict) and comp.get("description"):
            description_parts.append(_extract_text(comp.get("description")))
        description = "\n".join([p.strip() for p in description_parts if p]).strip()
        description = description or title

        alias = item.get("alias") or item.get("uuid") or ""
        if not alias:
            logger.warning("Skipping internship without alias/uuid: title=%s", title)
            continue
        url = f"{SITE_BASE}/{alias.lstrip('/')}"

        vacancy_created_at = _parse_dt(item.get("published_at"))
        deadline_at = _parse_dt(item.get("unpublished_at"))

        results.append(
            {
                "title": title,
                "company": company,
                "description": description,
                "url": url,
                "type": "internship",
                "vacancy_created_at": vacancy_created_at,
                "created_at": now_iso,
                "deadline_at": deadline_at,
                "contact_info": None,
                "contact_info_encrypted": None,
            }
        )

    return results


def save_to_file(path: str = "internships.json", limit: int = 100, direction: str = "it") -> str:
    data = fetch_internships(limit=limit, direction=direction)
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saved %s internships to %s", len(data), out_path)
    return str(out_path)


def main() -> None:
    init_sentry("internships_parser")

    argp = argparse.ArgumentParser(description="Fetch internships from it.fut.ru API")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' or /dev/stdout prints to stdout",
    )
    argp.add_argument("--limit", type=int, default=100, help="Limit publications per request")
    argp.add_argument("--direction", default="it", help="Direction filter (e.g. 'it')")
    args = argp.parse_args()

    data = fetch_internships(limit=args.limit, direction=args.direction)

    if args.output in ("-", "/dev/stdout"):
        json.dump(data, sys.stdout, ensure_ascii=False)
    else:
        output_path = save_to_file(args.output, limit=args.limit, direction=args.direction)
        print(output_path)


if __name__ == "__main__":
    main()

