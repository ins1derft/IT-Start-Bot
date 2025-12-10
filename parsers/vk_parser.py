import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://team.vk.company"
LIST_PATH = "/vacancy/"

# IT-специальности для фильтра; передаются как ?specialty=<id>
IT_SPECIALTY_IDS = [
    "268",  # BI аналитика
    "282",  # Backend
    "281",  # Data Science
    "269",  # Data-аналитика
    "278",  # DevOps
    "287",  # Frontend
    "304",  # Full-stack
    "283",  # Machine Learning
    "286",  # Mobile
    "284",  # QA
    "203",  # Архитекторы
    "359",  # Инженерия данных
    "270",  # Информационная безопасность
    "295",  # Продуктовая аналитика
    "315",  # Разработка и технические специальности КР
    "280",  # Сетевое администрирование
    "306",  # Системная аналитика
    "305",  # Системное администрирование
    "292",  # Управление IT продуктом
    "288",  # Управление IT проектами
    "271",  # Управление продуктом
]


class VKParser:
    """Лёгкий парсер вакансий VK (team.vk.company) без Selenium."""

    def __init__(self, session: Optional[requests.Session] = None, timeout: float = 15.0) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru,en;q=0.9",
            }
        )

    def _get_html(self, url: str, params: Optional[dict] = None) -> str:
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
        return resp.text

    def _html_to_text(self, html: str) -> str:
        soup = BeautifulSoup(html or "", "html.parser")
        parts = []
        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text:
                parts.append(text)
        if not parts:
            text = soup.get_text(" ", strip=True)
            if text:
                parts.append(text)
        return "\n\n".join(parts)

    def _parse_list(self, html: str) -> List[Dict[str, str]]:
        soup = BeautifulSoup(html, "html.parser")
        vacancies: List[Dict[str, str]] = []
        seen: Set[str] = set()

        # Ссылки на карточки вакансий
        cards = soup.select('a[href*="/vacancy/"]')
        for card in cards:
            href = card.get("href", "")
            if not href:
                continue
            # пропускаем ссылку на корневой список
            if href.rstrip("/") in {"/vacancy", "/vacancy/"}:
                continue
            full_url = urljoin(BASE_URL, href)
            if full_url in seen:
                continue

            # заголовок внутри карточки
            title_el = (
                card.select_one("h3")
                or card.select_one("h2")
                or card.select_one('[class*="title"]')
                or card.select_one('[class*="Title"]')
            )
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            vacancies.append({"title": title, "url": full_url})
            seen.add(full_url)

        return vacancies

    def _parse_detail(self, url: str, fallback_title: str = "") -> Dict[str, Optional[str]]:
        html = self._get_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h1") or soup.select_one("h2")
        title = title_el.get_text(strip=True) if title_el else fallback_title

        # Описание — берём основной текст из <main> или <article>, пытаемся собрать параграфы и списки
        main = soup.find("main") or soup.find("article") or soup
        text_parts: List[str] = []
        for p in main.select("p"):
            text = p.get_text(" ", strip=True)
            if len(text) >= 40:
                text_parts.append(text)
        # списки
        for ul in main.select("ul"):
            items = [li.get_text(" ", strip=True) for li in ul.select("li") if li.get_text(strip=True)]
            if items:
                text_parts.append("\n".join(f"• {item}" for item in items))

        description = "\n\n".join(text_parts).strip()

        return {
            "title": title,
            "company": "VK",
            "description": description,
            "url": url,
            "type": "job",
            "vacancy_created_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def scrape_all(self, specialty_ids: Optional[List[str]] = None, max_pages: int = 5) -> List[Dict[str, Optional[str]]]:
        specialties = specialty_ids or IT_SPECIALTY_IDS
        results: List[Dict[str, Optional[str]]] = []
        seen: Set[str] = set()

        for specialty in specialties:
            page = 1
            while page <= max_pages:
                params = {"specialty": specialty, "page": page}
                html = self._get_html(urljoin(BASE_URL, LIST_PATH), params=params)
                vacancies = self._parse_list(html)
                new_cards = 0
                for vac in vacancies:
                    if vac["url"] in seen:
                        continue
                    try:
                        detail = self._parse_detail(vac["url"], fallback_title=vac["title"])
                        results.append(detail)
                        seen.add(vac["url"])
                        new_cards += 1
                    except Exception:
                        continue
                if new_cards == 0:
                    break
                page += 1

        return results


def save_vacancies_to_file(
    parser: Optional[VKParser] = None,
    output_path: str = "vk_vacancies.json",
    specialty_ids: Optional[List[str]] = None,
    max_pages: int = 5,
) -> str:
    parser = parser or VKParser()
    vacancies = parser.scrape_all(specialty_ids=specialty_ids, max_pages=max_pages)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)
    return str(out_path)


def main() -> None:
    argp = argparse.ArgumentParser(description="Scrape VK vacancies (team.vk.company)")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' or /dev/stdout prints to stdout",
    )
    argp.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Pages per specialty to crawl",
    )
    args = argp.parse_args()

    parser = VKParser()
    vacancies = parser.scrape_all(max_pages=args.max_pages)

    if args.output in ("-", "/dev/stdout"):
        json.dump(vacancies, sys.stdout, ensure_ascii=False)
    else:
        output_path = save_vacancies_to_file(parser, args.output, max_pages=args.max_pages)
        print(output_path)


if __name__ == "__main__":
    main()
