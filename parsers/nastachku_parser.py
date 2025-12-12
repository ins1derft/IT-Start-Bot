import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests
from bs4 import BeautifulSoup, Tag

from sentry_service import get_service_logger, init_sentry

BASE_URL = "https://nastachku.ru/"
COMPANY = "Стачка"
TYPE = "conference"

MONTHS = {
    "января": 1,
    "февраля": 2,
    "марта": 3,
    "апреля": 4,
    "мая": 5,
    "июня": 6,
    "июля": 7,
    "августа": 8,
    "сентября": 9,
    "октября": 10,
    "ноября": 11,
    "декабря": 12,
}

logger = get_service_logger("nastachku_parser")


def _parse_date(text: str) -> Optional[str]:
    """
    Парсит дату вида '10-11 апреля 2026' или '2-3 октября 2025' -> ISO UTC.
    Берём стартовый день.
    """
    text = text.lower()
    m = re.search(r"(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\s+([а-яё]+)\s+(\d{4})", text)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2)
    year = int(m.group(3))
    month = MONTHS.get(month_name)
    if not month:
        return None
    try:
        dt = datetime(year=year, month=month, day=day, tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None


def _nearest_link(node: Tag) -> Optional[str]:
    """Ищем ближайшую ссылку с href вверх по дереву."""
    if isinstance(node, Tag):
        inner_link = node.find("a", href=True)
        if inner_link and inner_link.get("href"):
            href = inner_link["href"]
            if href.startswith("/"):
                href = BASE_URL.rstrip("/") + href
            return href

    cur = node
    depth = 0
    while cur and depth < 5:
        if isinstance(cur, Tag) and cur.name == "a" and cur.get("href"):
            href = cur["href"]
            if href.startswith("/"):
                href = BASE_URL.rstrip("/") + href
            return href
        cur = cur.parent
        depth += 1
    return None


def _extract_card_info(card: Tag) -> Optional[Dict]:
    """Извлекает данные конференции из карточки (контейнер вокруг кнопки)."""
    url = _nearest_link(card) or BASE_URL

    text = card.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    lines = [ln for ln in lines if not re.search(r"КУПИТЬ|КАК ЭТО БЫЛО", ln, re.I)]

    title = None
    for ln in lines:
        if "conf" in ln.lower() or "стачка" in ln.lower() or ln.startswith("#"):
            title = ln
            break
    if not title and lines:
        title = lines[0]
    title = title or "Конференция"

    vacancy_created_at = _parse_date(text)
    description = "\n".join(lines) if lines else text

    description = description.strip() or title

    return {
        "title": title,
        "company": COMPANY,
        "description": description,
        "url": url,
        "type": TYPE,
        "vacancy_created_at": vacancy_created_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _parse_cards(soup: BeautifulSoup) -> List[Dict]:
    """Ищет карточки конференций по кнопкам 'КУПИТЬ БИЛЕТ' или 'КАК ЭТО БЫЛО'."""
    results: List[Dict] = []
    seen: Set[tuple[str, str]] = set()
    buttons = soup.find_all(string=re.compile(r"(КУПИТЬ БИЛЕТ|КАК ЭТО БЫЛО)", re.I))
    for btn in buttons:
        node = btn
        for _ in range(5):
            if hasattr(node, "parent") and node.parent:
                node = node.parent
        if not isinstance(node, Tag):
            continue
        info = _extract_card_info(node)
        if not info:
            continue
        key = (info["title"], info["url"])
        if key in seen:
            continue
        results.append(info)
        seen.add(key)
    return results


def _get_html(url: str, session: requests.Session, timeout: float) -> str:
    try:
        resp = session.get(url, timeout=timeout)
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
        return resp.text
    except Exception:
        logger.exception("Failed to GET %s", url)
        raise


def scrape_nastachku(session: Optional[requests.Session] = None, timeout: float = 15.0) -> List[Dict]:
    session = session or requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "ru,en;q=0.9",
        }
    )
    html = _get_html(BASE_URL, session=session, timeout=timeout)
    soup = BeautifulSoup(html, "html.parser")
    items = _parse_cards(soup)
    if not items:
        logger.warning("nastachku: no conference cards found")
    return items


def save_to_file(
    output_path: str = "nastachku_conferences.json",
    session: Optional[requests.Session] = None,
    timeout: float = 15.0,
) -> str:
    conferences = scrape_nastachku(session=session, timeout=timeout)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(conferences, f, ensure_ascii=False, indent=2)
    return str(out_path)


def main() -> None:
    init_sentry("nastachku_parser")

    argp = argparse.ArgumentParser(description="Scrape Nastachku conferences")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' or /dev/stdout prints to stdout",
    )
    argp.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout, seconds")
    args = argp.parse_args()

    conferences = scrape_nastachku(timeout=args.timeout)

    if args.output in ("-", "/dev/stdout"):
        json.dump(conferences, sys.stdout, ensure_ascii=False)
    else:
        output_path = save_to_file(args.output, timeout=args.timeout)
        print(output_path)


if __name__ == "__main__":
    main()

