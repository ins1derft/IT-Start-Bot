import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://podlodka.io/crew"

logger = logging.getLogger(__name__)


def _parse_conference_rows(soup: BeautifulSoup) -> List[Dict]:
    """Извлекает конференции из секции расписания."""
    results: List[Dict] = []

    schedule_block = soup.find(string=lambda s: isinstance(s, str) and "Расписание конференций" in s)
    if not schedule_block:
        logger.warning("podlodka: schedule section not found")
        return results

    container = schedule_block
    for _ in range(5):
        container = container.parent

    rows = container.select(".t513__row")

    for row in rows:
        date_text_el = row.select_one(".t513__time")
        title_el = row.select_one(".t513__title")
        text_el = row.select_one(".t513__text")

        date_text = date_text_el.get_text(strip=True) if date_text_el else ""
        title = title_el.get_text(separator=" ", strip=True) if title_el else "Подлодка конференция"
        description_parts: List[str] = []
        if text_el:
            description_parts.append(text_el.get_text(" ", strip=True))

        link_el = row.find("a", href=True)
        url = link_el["href"] if link_el else BASE_URL
        if url.startswith("/"):
            url = BASE_URL.rstrip("/") + url

        vacancy_created_at = None
        if date_text:
            try:
                dt = datetime.strptime(f"{date_text} {datetime.now(timezone.utc).year}", "%d %B %Y")
                vacancy_created_at = dt.replace(tzinfo=timezone.utc).isoformat()
            except ValueError:
                months = {
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
                try:
                    day, month_name = date_text.split()
                    month = months.get(month_name.lower())
                    if month:
                        dt = datetime(year=datetime.now(timezone.utc).year, month=month, day=int(day))
                        vacancy_created_at = dt.replace(tzinfo=timezone.utc).isoformat()
                except Exception:
                    vacancy_created_at = None

        description = "\n".join([part for part in description_parts if part]).strip() or title

        results.append(
            {
                "title": title,
                "company": "Podlodka",
                "description": description,
                "url": url,
                "type": "conference",
                "vacancy_created_at": vacancy_created_at,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return results


def _get_html(url: str, session: requests.Session, timeout: float) -> str:
    resp = session.get(url, timeout=timeout)
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    resp.raise_for_status()
    return resp.text


def scrape_podlodka_crew(session: Optional[requests.Session] = None, timeout: float = 15.0) -> List[Dict]:
    """Скрейпить страницу Podlodka Crew и вернуть список конференций."""
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
    return _parse_conference_rows(soup)


def save_to_file(
    output_path: str = "podlodka_conferences.json",
    session: Optional[requests.Session] = None,
    timeout: float = 15.0,
) -> str:
    conferences = scrape_podlodka_crew(session=session, timeout=timeout)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(conferences, f, ensure_ascii=False, indent=2)
    return str(out_path)


def main() -> None:
    argp = argparse.ArgumentParser(description="Scrape Podlodka Crew conferences")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' or /dev/stdout prints to stdout",
    )
    argp.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout, seconds")
    args = argp.parse_args()

    conferences = scrape_podlodka_crew(timeout=args.timeout)

    if args.output in ("-", "/dev/stdout"):
        json.dump(conferences, sys.stdout, ensure_ascii=False)
    else:
        output_path = save_to_file(args.output, timeout=args.timeout)
        print(output_path)


if __name__ == "__main__":
    main()

