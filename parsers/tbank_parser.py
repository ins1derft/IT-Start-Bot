import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from sentry_service import get_service_logger, init_sentry


BASE_URL = "https://www.tbank.ru"
LIST_PATH = "/career/vacancies/it/"
API_LIST_PATH = "/pfpjobs/papi/getVacancies"


class TBankParser:
    """
    Парсер IT‑вакансий Т‑Банка, адаптированный под логику приложения:
    - CLI выводит JSON в stdout (или файл по флагу --output)
    - Поля соответствуют ожиданиям parsing_service (_normalize_item)
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout: float = 20.0) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        self.logger = get_service_logger("tbank_parser")
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
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            # Уточняем кодировку, чтобы не получить кракозябры в описании.
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            resp.raise_for_status()
            return resp.text
        except Exception:
            self.logger.exception("Failed to GET %s params=%s", url, params)
            raise

    def fetch_api_page(self, offset: int = 0, city_id: str = "0c5b2444-70a0-4932-980c-b4dc0d3f02b5") -> Dict:
        """
        Вызывает внутренний API вакансий с пагинацией.
        city_id по умолчанию — «Любой город».
        """
        payload = {
            "filters": {"cityId": [city_id]},
            "pagination": {"it": {"offset": offset, "isFinished": False}},
        }
        try:
            resp = self.session.post(
                urljoin(BASE_URL, API_LIST_PATH),
                json=payload,
                timeout=self.timeout,
            )
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            resp.raise_for_status()
            return resp.json()
        except Exception:
            self.logger.exception("Failed to POST vacancies API offset=%s city_id=%s", offset, city_id)
            raise

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

    def fetch_detail(self, url: str, fallback_title: str = "", fallback_desc_html: str = "") -> Dict[str, Optional[str]]:
        html = self._get_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title_el = soup.select_one("h1") or soup.select_one('[data-qa-type$="title"]')
        title = title_el.get_text(strip=True) if title_el else fallback_title

        # Ищем описание, избегая захвата шапки.
        desc_container = None
        selector_candidates = [
            '[data-qa-type*="vacancy-description"]',
            '[data-qa-type*="VacancyDescription"]',
            '[data-test*="vacancy-description"]',
            'section[data-qa-type*="description"]',
            '.VacancyDescriptionView__cards-desktop_djsrvZ .Card__card_aZ3-\\+--E .atom-desktop-dangerously-html__box_aCYBaw',
            '.VacancyDescriptionView__cards-desktop_djsrvZ .atom-desktop-dangerously-html__box_aCYBaw',
        ]
        for selector in selector_candidates:
            desc_container = soup.select_one(selector)
            if desc_container:
                break

        heading_capture: List[str] = []
        if not desc_container:
            heading_tags = ["h2", "h3", "h4", "h5"]
            keywords = ("опис", "ваканси")
            for heading in soup.find_all(heading_tags):
                heading_text = heading.get_text(" ", strip=True).lower()
                if any(k in heading_text for k in keywords):
                    for node in heading.next_elements:
                        if getattr(node, "name", None) in heading_tags:
                            break
                        if getattr(node, "name", None) in ["p", "li"]:
                            text = node.get_text(" ", strip=True)
                            if text:
                                heading_capture.append(text)
                        if getattr(node, "name", None) in ["div", "section", "article"]:
                            block_text = node.get_text(" ", strip=True)
                            if block_text:
                                heading_capture.append(block_text)
                    break
        if heading_capture and not desc_container:
            description = "\n\n".join(heading_capture)
        else:
            description = ""

        if not heading_capture:
            if not desc_container:
                desc_container = soup.select_one('div[data-test*="htmlTag"], div.atom-desktop-dangerously-html__box_aCYBaw')

            text_parts: List[str] = []
            if desc_container:
                paragraphs = desc_container.select("p, li")
                for p in paragraphs:
                    text = p.get_text(" ", strip=True)
                    if text:
                        text_parts.append(text)
                if not text_parts:
                    fallback_text = desc_container.get_text(" ", strip=True)
                    if fallback_text:
                        text_parts.append(fallback_text)
            description = description or "\n\n".join(text_parts)

        if not description and fallback_desc_html:
            description = self._html_to_text(fallback_desc_html)

        return {
            "title": title,
            "company": "Т-Банк",
            "description": description,
            "url": url,
            "type": "job",
            "vacancy_created_at": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def _extract_urls_from_list_page(self, html: str) -> Dict[str, str]:
        """
        Извлекает полные URL вакансий из HTML страницы со списком.
        Возвращает словарь {slug: full_url} для сопоставления.
        """
        soup = BeautifulSoup(html, "html.parser")
        url_map = {}
        vacancy_links = soup.select('a[href*="/career/it/"]')

        for link in vacancy_links:
            href = link.get("href", "")
            if "/career/it/" in href and href.count("/") >= 4:
                parts = href.rstrip("/").split("/")
                if len(parts) >= 2:
                    slug = parts[-1]
                    if href.startswith("/"):
                        full_url = urljoin(BASE_URL, href)
                    elif href.startswith("http"):
                        full_url = href
                    else:
                        full_url = urljoin(BASE_URL, f"/{href}")
                    url_map[slug] = full_url

        return url_map

    def scrape_all(self, max_pages: int = 50) -> List[Dict[str, Optional[str]]]:
        results: List[Dict[str, Optional[str]]] = []
        seen: Set[str] = set()

        offset = 0
        for _ in range(max_pages):
            data = self.fetch_api_page(offset=offset)
            payload = data.get("payload") or {}
            vacancies = payload.get("vacancies") or []
            if not vacancies:
                break

            list_url = urljoin(BASE_URL, LIST_PATH)
            if offset == 0:
                try:
                    list_html = self._get_html(list_url)
                    url_map = self._extract_urls_from_list_page(list_html)
                except Exception:
                    url_map = {}
            else:
                url_map = {}

            for vac in vacancies:
                slug = vac.get("urlSlug")
                if not slug:
                    continue

                url = url_map.get(slug)
                if not url:
                    specialty = vac.get("specialty", "")
                    if isinstance(specialty, str) and specialty:
                        url = urljoin(BASE_URL, f"/career/it/{specialty}/{slug}")
                    else:
                        if slug.startswith("/career/"):
                            url = urljoin(BASE_URL, slug)
                        elif slug.startswith("career/"):
                            url = urljoin(BASE_URL, f"/{slug}")
                        else:
                            url = urljoin(BASE_URL, f"/career/it/{slug}")

                if url in seen:
                    continue
                try:
                    detail = self.fetch_detail(
                        url,
                        fallback_title=vac.get("title", ""),
                        fallback_desc_html=vac.get("shortDescription", ""),
                    )
                except requests.HTTPError:
                    if not url_map.get(slug):
                        try:
                            resp = self.session.head(url, allow_redirects=True, timeout=self.timeout)
                            if resp.status_code == 200:
                                url = resp.url
                                detail = self.fetch_detail(
                                    url,
                                    fallback_title=vac.get("title", ""),
                                    fallback_desc_html=vac.get("shortDescription", ""),
                                )
                            else:
                                self.logger.warning("Vacancy detail returned status=%s url=%s", resp.status_code, url)
                                continue
                        except Exception:
                            self.logger.exception("Vacancy detail fetch failed (after redirect probe) url=%s", url)
                            continue
                    else:
                        self.logger.warning("Vacancy detail fetch failed (HTTPError) url=%s", url)
                        continue
                except Exception:
                    self.logger.exception("Vacancy detail parse failed url=%s", url)
                    continue
                results.append(detail)
                seen.add(url)

            next_pagination = payload.get("nextPagination", {}).get("it", {})
            next_offset = next_pagination.get("offset")
            is_finished = next_pagination.get("isFinished")
            if next_offset is None or is_finished:
                break
            offset = next_offset

        return results


def save_vacancies_to_file(
    parser: Optional[TBankParser] = None,
    output_path: str = "tbank_vacancies.json",
    max_pages: int = 50,
) -> str:
    """
    Скрапит вакансии и сохраняет JSON. Возвращает путь к файлу.
    """
    parser = parser or TBankParser()
    vacancies = parser.scrape_all(max_pages=max_pages)
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)
    return str(out_path)


def main() -> None:
    """CLI совместим с текущим раннером (python3 parsers/tbank_parser.py --output -)."""

    init_sentry("tbank_parser")

    argp = argparse.ArgumentParser(description="Scrape T-Bank IT vacancies")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' или /dev/stdout печатает в stdout",
    )
    argp.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="Сколько страниц пагинации дергать",
    )
    args = argp.parse_args()

    parser = TBankParser()
    vacancies = parser.scrape_all(max_pages=args.max_pages)

    if args.output in ("-", "/dev/stdout"):
        json.dump(vacancies, sys.stdout, ensure_ascii=False)
    else:
        output_path = save_vacancies_to_file(parser, args.output, max_pages=args.max_pages)
        print(output_path)


if __name__ == "__main__":
    main()
