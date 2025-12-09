import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.tbank.ru"
LIST_PATH = "/career/vacancies/it/"
API_LIST_PATH = "/pfpjobs/papi/getVacancies"


class TBankParser:
    """
    Minimal parser for T‑Bank IT vacancies.
    Fetches list pages (with simple page param pagination) and drills into each vacancy card.
    """

    def __init__(self, session: Optional[requests.Session] = None, timeout: float = 20.0) -> None:
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
        # Ensure correct decoding to avoid mojibake in Cyrillic.
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
        return resp.text

    def fetch_api_page(self, offset: int = 0, city_id: str = "0c5b2444-70a0-4932-980c-b4dc0d3f02b5") -> Dict:
        """
        Call internal vacancies API with pagination offset.
        City filter uses the default "Любой город" cityId provided from DevTools.
        """
        payload = {
            "filters": {"cityId": [city_id]},
            "pagination": {"it": {"offset": offset, "isFinished": False}},
        }
        resp = self.session.post(
            urljoin(BASE_URL, API_LIST_PATH),
            json=payload,
            timeout=self.timeout,
        )
        if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
            resp.encoding = resp.apparent_encoding or "utf-8"
        resp.raise_for_status()
        return resp.json()

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

        # Prefer the "Описание" card container to avoid grabbing other HTML blocks.
        desc_container = None
        for card in soup.select('div.VacancyDescriptionView__cards-desktop_djsrvZ div[class*="Card__card"]'):
            title_el = card.select_one("h2")
            if title_el and "Описание" in title_el.get_text(strip=True):
                desc_container = card.select_one("div.atom-desktop-dangerously-html__box_aCYBaw")
                break
        if not desc_container:
            # Fallback: any htmlTag/dangerously-html container.
            desc_container = soup.select_one('div[data-test*="htmlTag"], div.atom-desktop-dangerously-html__box_aCYBaw')
        text_parts: List[str] = []
        if desc_container:
            paragraphs = desc_container.select("p")
            for p in paragraphs:
                text = p.get_text(" ", strip=True)
                if text:
                    text_parts.append(text)
            # Fallback: if no <p>, take full text of the container.
            if not text_parts:
                fallback_text = desc_container.get_text(" ", strip=True)
                if fallback_text:
                    text_parts.append(fallback_text)
        description = "\n\n".join(text_parts)
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

            for vac in vacancies:
                slug = vac.get("urlSlug")
                if not slug:
                    continue
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
                    # Skip broken detail pages but continue pagination.
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
    Scrape all vacancies and persist them to JSON file.
    Returns the path to the created file so caller can use it downstream.
    """
    parser = parser or TBankParser()
    vacancies = parser.scrape_all(max_pages=max_pages)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(vacancies, f, ensure_ascii=False, indent=2)
    return output_path


def main() -> None:
    """CLI entrypoint.

    By default prints JSON to stdout; use -o/--output to write a file and echo its path.
    """

    argp = argparse.ArgumentParser(description="Scrape T-Bank IT vacancies")
    argp.add_argument(
        "-o",
        "--output",
        default="-",
        help="Path to write JSON; '-' or /dev/stdout prints to stdout",
    )
    argp.add_argument("--max-pages", type=int, default=50, help="Pagination pages to fetch")
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

