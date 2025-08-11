#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum (Gazeta Matematica și colecții adiacente):
- Conectare la sesiune Chrome existentă cu remote debugging.
- Dintr-o pagină de colecție extrage toate issue-urile (/view/...).
- Sare peste cele deja descărcate complet sau în SKIP_URLS.
- Limitează la 102 issue-uri pe zi.
- Detectează mesajul de limită zilnică și oprește progresul imediat..
- Reia parțial un issue neterminat (folosind last_successful_segment_end).
- Păstrează stare în state.json: date, count, downloaded_issues (cu metadata), pages_downloaded, recent_links, daily_limit_hit.
- După completarea unui issue, mută PDF-urile aferente într-un folder cu numele titlului.
- La final, raportează dacă s-a terminat totul.
- Procesează prima colecția din main(), apoi colecțiile adiționale în ordine.
- Salvează și încarcă automat skip_urls.json pentru optimizare.
- Detectează ferestre noi cu mesajul de limită zilnică și le închide.

- Inainte sa pornesti codul trebuie sa deschizi fisierul start_chrome_debug.bat ca sa pornesti o sesiune noua Chrome unde se vor accesa link-urile.
Iata ce contine acest fisier .bat:


@echo off
REM Pornește Chrome pe profilul Default cu remote debugging activat
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"
set PROFILE_DIR="C:/Users/necul/AppData/Local/Google/Chrome/User Data/Default"
REM Asigură-te că nu mai e deja un Chrome deschis pe acel profil
%CHROME_PATH% --remote-debugging-port=9222 --user-data-dir=%PROFILE_DIR%

"""

import time
import os
import sys
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException

# Colecțiile adiționale (procesate DUPĂ colecția principală din main())
ADDITIONAL_COLLECTIONS = [
    "https://adt.arcanum.com/ro/collection/GazetaMatematicaSiFizicaSeriaB/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMatematice/",
    "https://adt.arcanum.com/ro/collection/MinePetrolGaze/"
]

# Skip URLs statice (hardcoded)
STATIC_SKIP_URLS = {
    "https://adt.arcanum.com/en/view/GazetaMatematica_1922-23",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1923-24",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1924-25",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1925-26",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1926-27",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1929-30",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1930-31",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1931-32",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1932-33",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1933-34",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1934-35",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1934-35_Sup",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1935-36",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1935-36_Sup",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1936-37",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1936-37_Sup",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1937-38",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1937-38_Sup",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1938-39",
    "https://adt.arcanum.com/en/view/GazetaMatematica_1938-39_Sup"
}

DAILY_LIMIT = 105
STATE_FILENAME = "state.json"
SKIP_URLS_FILENAME = "skip_urls.json"


class ChromePDFDownloader:
    def __init__(self, main_collection_url, download_dir=None, batch_size=50, timeout=15):
        self.main_collection_url = main_collection_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.download_dir = download_dir or os.getcwd()
        self.driver = None
        self.wait = None
        self.attached_existing = False
        self.state_path = os.path.join(self.download_dir, STATE_FILENAME)
        self.skip_urls_path = os.path.join(self.download_dir, SKIP_URLS_FILENAME)
        self.current_issue_url = None
        self.dynamic_skip_urls = set()
        self._load_skip_urls()
        self._load_state()

    def _load_skip_urls(self):
        """Încarcă skip URLs din fișierul separat"""
        self.dynamic_skip_urls = set(STATIC_SKIP_URLS)  # Începe cu cele statice

        if os.path.exists(self.skip_urls_path):
            try:
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    completed_urls = data.get("completed_urls", [])
                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_urls)
                    print(f"📋 Încărcat {len(completed_urls)} URL-uri complet descărcate din {SKIP_URLS_FILENAME}")
            except Exception as e:
                print(f"⚠ Eroare la citirea {SKIP_URLS_FILENAME}: {e}")

        print(f"🚫 Total URL-uri de skip: {len(self.dynamic_skip_urls)}")

    def _save_skip_urls(self):
        """Salvează skip URLs în fișierul separat"""
        try:
            # Extrage doar URL-urile complet descărcate din state
            completed_urls = []
            for item in self.state.get("downloaded_issues", []):
                if (item.get("completed_at") and
                    item.get("total_pages") and
                    item.get("last_successful_segment_end", 0) >= item.get("total_pages", 0)):
                    completed_urls.append(item["url"])

            # Adaugă și cele statice
            all_completed = list(STATIC_SKIP_URLS) + completed_urls

            data = {
                "last_updated": datetime.now().isoformat(),
                "completed_urls": sorted(list(set(all_completed)))
            }

            with open(self.skip_urls_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            print(f"💾 Salvat {len(data['completed_urls'])} URL-uri în {SKIP_URLS_FILENAME}")
        except Exception as e:
            print(f"⚠ Eroare la salvarea {SKIP_URLS_FILENAME}: {e}")

    def _safe_folder_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def get_existing_pdf_segments(self, issue_url):
        """Scanează folderul pentru PDF-uri existente și returnează ultimul segment descărcat"""
        issue_id = issue_url.rstrip('/').split('/')[-1]
        max_page = 0

        try:
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf') and issue_id in filename:
                    # Caută pattern-ul __pages1-49.pdf
                    match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        start_page = int(match.group(1))
                        end_page = int(match.group(2))
                        if end_page > max_page:
                            max_page = end_page
                        print(f"📁 Găsit PDF existent: {filename} (pagini {start_page}-{end_page})")
        except Exception as e:
            print(f"⚠ Eroare la scanarea fișierelor: {e}")

        return max_page

    def verify_pdf_exists(self, issue_url, end_page):
        """Verifică dacă PDF-ul pentru segmentul respectiv există pe disk"""
        issue_id = issue_url.rstrip('/').split('/')[-1]
        try:
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf') and issue_id in filename:
                    match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        file_start = int(match.group(1))
                        file_end = int(match.group(2))
                        if file_end >= end_page:
                            print(f"✅ Confirmat: PDF existent pentru pagini până la {end_page}")
                            return True
        except Exception as e:
            print(f"⚠ Eroare la verificarea PDF: {e}")

        print(f"❌ PDF pentru pagini până la {end_page} NU există pe disk")
        return False

    def sync_json_with_disk_files(self):
        """Scanează toate PDF-urile de pe disk și actualizează JSON-ul cu progresul real, ordonate după data modificării"""
        print("🔄 Sincronizez JSON-ul cu fișierele de pe disk...")

        try:
            pdf_files = {}

            # Scanează toate PDF-urile din folder cu data modificării
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf'):
                    # Extrage issue_id și paginile
                    match = re.search(r'([^-]+(?:-[^-]+)*)-\d+__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        issue_id = match.group(1)
                        start_page = int(match.group(2))
                        end_page = int(match.group(3))

                        # Obține data modificării fișierului
                        file_path = os.path.join(self.download_dir, filename)
                        try:
                            mod_time = os.path.getmtime(file_path)
                        except Exception:
                            mod_time = 0

                        # Construiește URL-ul complet
                        if issue_id not in pdf_files:
                            pdf_files[issue_id] = {
                                "max_page": 0,
                                "files": [],
                                "latest_mod_time": 0
                            }

                        pdf_files[issue_id]["files"].append((start_page, end_page, filename))
                        if end_page > pdf_files[issue_id]["max_page"]:
                            pdf_files[issue_id]["max_page"] = end_page

                        # Ține evidența celei mai recente modificări
                        if mod_time > pdf_files[issue_id]["latest_mod_time"]:
                            pdf_files[issue_id]["latest_mod_time"] = mod_time

            # Sortează issue-urile după data ultimei modificări (cel mai recent primul)
            sorted_issues = sorted(pdf_files.items(), key=lambda x: x[1]["latest_mod_time"], reverse=True)

            # Creează lista nouă de issues ordonată
            new_downloaded_issues = []

            # Procesează issue-urile în ordinea sortată
            for issue_id, data in sorted_issues:
                max_page = data["max_page"]
                files = data["files"]
                latest_time = data["latest_mod_time"]

                # Găsește URL-ul complet în JSON existent
                possible_urls = [
                    f"https://adt.arcanum.com/en/view/{issue_id}",
                    f"https://adt.arcanum.com/ro/view/{issue_id}"
                ]

                found_item = None
                for item in self.state.get("downloaded_issues", []):
                    if any(url in item.get("url", "") for url in possible_urls):
                        found_item = item.copy()  # Fă o copie
                        break

                if found_item:
                    # Actualizează cu progresul de pe disk
                    if max_page > found_item.get("last_successful_segment_end", 0):
                        found_item["last_successful_segment_end"] = max_page
                    new_downloaded_issues.append(found_item)
                    print(f"📁 Actualizat din disk: {found_item['url']} → pagini {max_page}")
                else:
                    # Adaugă issue nou
                    new_issue = {
                        "url": possible_urls[0],  # Încearcă prima variantă
                        "title": "",
                        "subtitle": "",
                        "pages": 0,
                        "completed_at": "",
                        "last_successful_segment_end": max_page,
                        "total_pages": None
                    }
                    new_downloaded_issues.append(new_issue)
                    print(f"➕ Adăugat din disk: {possible_urls[0]} → pagini {max_page}")

                # Afișează fișierele pentru acest issue
                for start, end, fname in files:
                    print(f"   📄 Fișier: {fname} (pagini {start}-{end})")

            # Adaugă la sfârșitul listei issue-urile din JSON care nu au fișiere pe disk
            for item in self.state.get("downloaded_issues", []):
                if not any(issue_item.get("url") == item.get("url") for issue_item in new_downloaded_issues):
                    new_downloaded_issues.append(item)

            # Înlocuiește lista cu cea ordonată
            self.state["downloaded_issues"] = new_downloaded_issues

            self._save_state()
            print(f"✅ Sincronizare completă: {len(pdf_files)} issue-uri găsite pe disk, ordonate după data modificării")

        except Exception as e:
            print(f"⚠ Eroare la sincronizarea cu disk-ul: {e}")

    def _normalize_downloaded_issues(self, raw):
        normalized = []
        for item in raw:
            if isinstance(item, str):
                normalized.append({
                    "url": item.rstrip('/'),
                    "title": "",
                    "subtitle": "",
                    "pages": 0,
                    "completed_at": "",
                    "last_successful_segment_end": 0,
                    "total_pages": None
                })
            elif isinstance(item, dict):
                normalized.append({
                    "url": item.get("url", "").rstrip('/'),
                    "title": item.get("title", ""),
                    "subtitle": item.get("subtitle", ""),
                    "pages": item.get("pages", 0),
                    "completed_at": item.get("completed_at", ""),
                    "last_successful_segment_end": item.get("last_successful_segment_end", 0),
                    "total_pages": item.get("total_pages")
                })
        return normalized

    def _load_state(self):
        today = datetime.now().strftime("%Y-%m-%d")
        default = {
            "date": today,
            "count": 0,
            "downloaded_issues": [],
            "pages_downloaded": 0,
            "recent_links": [],
            "daily_limit_hit": False,
            "main_collection_completed": False,
            "current_additional_collection_index": 0
        }
        self.state = default

        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)

                if loaded.get("date") == today:
                    # Aceeași zi - păstrează totul
                    issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))
                    self.state = {
                        "date": loaded.get("date", today),
                        "count": len([i for i in issues if i.get("completed_at")]),  # Doar cele complet terminate
                        "downloaded_issues": issues,
                        "pages_downloaded": loaded.get("pages_downloaded", 0),
                        "recent_links": loaded.get("recent_links", []),
                        "daily_limit_hit": loaded.get("daily_limit_hit", False),
                        "main_collection_completed": loaded.get("main_collection_completed", False),
                        "current_additional_collection_index": loaded.get("current_additional_collection_index", 0)
                    }
                else:
                    # Zi nouă - păstrează doar issue-urile parțial descărcate, resetează limitele zilnice
                    old_issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))

                    # Filtrează doar issue-urile neterminate (parțial descărcate)
                    partial_issues = []
                    for issue in old_issues:
                        last_segment = issue.get("last_successful_segment_end", 0)
                        total_pages = issue.get("total_pages")
                        completed_at = issue.get("completed_at", "")

                        # Păstrează issue-ul dacă:
                        # 1. Are progres parțial (last_successful_segment_end > 0)
                        # 2. Nu este complet terminat (completed_at gol sau last_segment < total_pages)
                        if (last_segment > 0 and
                            not completed_at and
                            total_pages and
                            last_segment < total_pages):

                            print(f"📋 Păstrez progresul parțial pentru: {issue['url']} (pagini {last_segment}/{total_pages})")
                            partial_issues.append(issue)

                    self.state = {
                        "date": today,
                        "count": 0,  # Resetează count-ul zilnic
                        "downloaded_issues": partial_issues,  # Păstrează doar cele parțiale
                        "pages_downloaded": 0,  # Resetează pagini zilnice
                        "recent_links": [],  # Șterge linkurile din ziua anterioară
                        "daily_limit_hit": False,  # Resetează limita zilnică
                        "main_collection_completed": loaded.get("main_collection_completed", False),  # Păstrează progresul
                        "current_additional_collection_index": loaded.get("current_additional_collection_index", 0)
                    }

                    if partial_issues:
                        print(f"🔄 Zi nouă detectată. Păstrez {len(partial_issues)} issue-uri parțial descărcate.")
                    else:
                        print(f"🆕 Zi nouă detectată. Încep cu stare curată.")

            except Exception as e:
                print(f"⚠ Eroare la citirea stării ({e}), resetez.")
                self.state = default

        self._save_state()

    def _save_state(self):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"⚠ Nu am putut salva state-ul: {e}")

    def remaining_quota(self):
        return max(0, DAILY_LIMIT - self.state.get("count", 0))

    def _update_partial_issue_progress(self, issue_url, last_successful_segment_end, total_pages=None, title=None, subtitle=None):
        normalized = issue_url.rstrip('/')
        updated = False

        # Găsește și actualizează issue-ul existent
        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item["url"] == normalized:
                item["last_successful_segment_end"] = last_successful_segment_end
                if total_pages is not None:
                    item["total_pages"] = total_pages
                if title:
                    item["title"] = title
                if subtitle:
                    item["subtitle"] = subtitle

                # Mută la începutul listei pentru a fi primul în JSON
                updated_item = self.state["downloaded_issues"].pop(i)
                self.state["downloaded_issues"].insert(0, updated_item)
                updated = True
                break

        if not updated:
            # Issue nou - adaugă la ÎNCEPUTUL listei
            new_issue = {
                "url": normalized,
                "title": title or "",
                "subtitle": subtitle or "",
                "pages": 0,
                "completed_at": "",
                "last_successful_segment_end": last_successful_segment_end,
                "total_pages": total_pages
            }
            self.state["downloaded_issues"].insert(0, new_issue)
            print(f"➕ Adăugat issue nou în progres: {normalized}")

        # Salvează imediat progresul
        self._save_state()
        print(f"💾 Progres parțial salvat: {normalized} - pagini {last_successful_segment_end}/{total_pages or '?'}")

    def mark_issue_done(self, issue_url, pages_count, title=None, subtitle=None, total_pages=None):
        normalized = issue_url.rstrip('/')
        now_iso = datetime.now().isoformat(timespec="seconds")
        existing = None
        existing_index = -1

        # Găsește issue-ul existent
        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item.get("url") == normalized:
                existing = item
                existing_index = i
                break

        record = {
            "url": normalized,
            "title": title or (existing.get("title") if existing else ""),
            "subtitle": subtitle or (existing.get("subtitle") if existing else ""),
            "pages": pages_count,
            "completed_at": now_iso,
            "last_successful_segment_end": pages_count,
            "total_pages": total_pages if total_pages is not None else (existing.get("total_pages") if existing else None)
        }

        if existing:
            # Actualizează și mută la începutul listei
            existing.update(record)
            completed_item = self.state["downloaded_issues"].pop(existing_index)
            self.state["downloaded_issues"].insert(0, completed_item)
        else:
            # Adaugă la începutul listei
            self.state["downloaded_issues"].insert(0, record)

        # Actualizează count-ul doar cu cele complet terminate
        completed_count = len([i for i in self.state["downloaded_issues"] if i.get("completed_at")])
        self.state["count"] = completed_count
        self.state["pages_downloaded"] = self.state.get("pages_downloaded", 0) + pages_count

        recent_entry = {
            "url": normalized,
            "title": record["title"],
            "subtitle": record["subtitle"],
            "pages": pages_count,
            "timestamp": now_iso
        }
        self.state.setdefault("recent_links", []).insert(0, recent_entry)  # Și aici la început
        self.state["daily_limit_hit"] = False

        # Adaugă URL-ul în skip list dinamice
        self.dynamic_skip_urls.add(normalized)

        self._save_state()
        self._save_skip_urls()
        print(f"✅ Issue marcat ca terminat: {normalized} ({pages_count} pagini)")

    def setup_chrome_driver(self):
        try:
            print("🔧 Inițializare WebDriver – încerc conectare la instanța Chrome existentă via remote debugging...")
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            chrome_options.add_experimental_option("prefs", prefs)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, self.timeout)
                self.attached_existing = True
                print("✅ Conectat la instanța Chrome existentă cu succes.")
                return True
            except WebDriverException as e:
                print(f"⚠ Conexiune la Chrome existent eșuat ({e}); pornesc o instanță nouă.")
                chrome_options = Options()
                chrome_options.add_experimental_option("prefs", prefs)
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--incognito")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, self.timeout)
                self.attached_existing = False
                print("✅ Chrome nou pornit cu succes.")
                return True
        except WebDriverException as e:
            print(f"❌ Eroare la inițializarea WebDriver-ului: {e}")
            return False

    def navigate_to_page(self, url):
        try:
            print(f"🌐 Navighez către: {url}")
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
            print("✅ Pagina încărcată.")
            return True
        except Exception as e:
            print(f"❌ Eroare la navigare sau încărcare: {e}")
            return False

    def get_issue_metadata(self):
        title = ""
        subtitle = ""
        try:
            breadcrumb = self.driver.find_element(By.CSS_SELECTOR, "li.breadcrumb-item.active")
            try:
                sub_elem = breadcrumb.find_element(By.CSS_SELECTOR, "#pdfview-pdfcontents span")
                subtitle = sub_elem.text.strip()
            except Exception:
                subtitle = ""
            raw = breadcrumb.text.strip()
            if subtitle and subtitle in raw:
                title = raw.replace(subtitle, "").strip()
            else:
                title = raw
        except Exception:
            pass
        return title, subtitle

    def get_total_pages(self, max_attempts=5, delay_between=1.0):
        for attempt in range(1, max_attempts + 1):
            try:
                elems = self.driver.find_elements(By.CSS_SELECTOR, 'div.MuiInputAdornment-root.MuiInputAdornment-positionEnd')
                for el in elems:
                    text = el.text.strip()
                    match = re.search(r'/\s*(\d+)', text)
                    if match:
                        total = int(match.group(1))
                        print(f"✅ (metoda principală) Numărul total de pagini detectat: {total}")
                        return total
                all_texts = self.driver.find_elements(By.XPATH, "//*[contains(text(), '/')]")
                for el in all_texts:
                    text = el.text.strip()
                    match = re.search(r'/\s*(\d+)', text)
                    if match:
                        total = int(match.group(1))
                        print(f"✅ (fallback text) Numărul total de pagini detectat: {total} din '{text}'")
                        return total
                js_result = self.driver.execute_script("""
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    const regex = /\\/\\s*(\\d+)/;
                    while(walker.nextNode()) {
                        const t = walker.currentNode.nodeValue;
                        const m = t.match(regex);
                        if (m) return m[1];
                    }
                    return null;
                """)
                if js_result:
                    total = int(js_result)
                    print(f"✅ (fallback JS) Numărul total de pagini detectat: {total}")
                    return total
                print(f"⚠ ({attempt}) Nu am găsit încă numărul total de pagini, reîncerc în {delay_between}s...")
                time.sleep(delay_between)
            except Exception as e:
                print(f"⚠ ({attempt}) Eroare în get_total_pages: {e}")
                time.sleep(delay_between)
        print("❌ Nu s-a reușit extragerea numărului total de pagini după multiple încercări.")
        return 0

    def open_save_popup(self):
        try:
            try:
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiDialog-container')))
            except Exception:
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            svg = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]')))
            button = svg
            if svg.tag_name.lower() == "svg":
                try:
                    button = svg.find_element(By.XPATH, "./ancestor::button")
                except Exception:
                    pass
            for attempt in range(1, 4):
                try:
                    button.click()
                    return True
                except ElementClickInterceptedException:
                    print(f"⚠ click interceptat (încercarea {attempt}), trimit ESC și reiau...")
                    self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    continue
            print("❌ Nu am reușit să dau click pe butonul de deschidere a popup-ului după retry-uri.")
            return False
        except Exception as e:
            print(f"❌ Nu am reușit să deschid popup-ul de salvare: {e}")
            return False

    def fill_and_save_range(self, start, end):
        try:
            first_input = self.wait.until(EC.presence_of_element_located((By.ID, "first page")))
            print("⏳ Aștept 2s înainte de a completa primul input...")
            time.sleep(2)
            first_input.send_keys(Keys.CONTROL + "a")
            first_input.send_keys(str(start))
            print(f"✏️ Am introdus primul număr: {start}")
            print("⏳ Aștept 2s înainte de a completa al doilea input...")
            time.sleep(2)
            last_input = self.wait.until(EC.presence_of_element_located((By.ID, "last page")))
            last_input.send_keys(Keys.CONTROL + "a")
            last_input.send_keys(str(end))
            print(f"✏️ Am introdus al doilea număr: {end}")
            print("⏳ Aștept 2s înainte de a apăsa butonul de salvare...")
            time.sleep(2)
            save_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//button[.//text()[contains(normalize-space(.), "Salvați") or contains(normalize-space(.), "Save")]]'
            )))
            save_btn.click()
            print(f"✅ Segmentul {start}-{end} salvat.")
            return True
        except Exception as e:
            print(f"❌ Eroare la completarea/salvarea intervalului {start}-{end}: {e}")
            return False

    def check_daily_limit_in_all_windows(self, set_flag=True):
        """Verifică mesajul de limită zilnică în toate ferestrele deschise"""
        current_window = self.driver.current_window_handle
        limit_reached = False

        try:
            all_handles = self.driver.window_handles
            for handle in all_handles:
                try:
                    self.driver.switch_to.window(handle)
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text

                    # Verifică mesajul de limită
                    if ("Daily download limit reached" in body_text or
                        "Terms and conditions" in body_text):
                        print(f"⚠ Limita zilnică detectată în fereastra: {handle}")
                        limit_reached = True

                        # Închide această fereastră dacă nu e principală
                        if handle != current_window and len(all_handles) > 1:
                            print(f"🗙 Închid fereastra cu limita zilnică: {handle}")
                            self.driver.close()
                        break

                except Exception as e:
                    # Fereastră închisă sau inaccessibilă
                    continue

            # Revine la fereastra originală dacă încă există
            try:
                if current_window in self.driver.window_handles:
                    self.driver.switch_to.window(current_window)
                elif self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

        except Exception as e:
            print(f"⚠ Eroare la verificarea ferestrelor: {e}")

        # Setează flag-ul doar dacă e cerut (pentru a distinge între curățenie inițială și detectare reală)
        if limit_reached and set_flag:
            self.state["daily_limit_hit"] = True
            self._save_state()

        return limit_reached

    def save_page_range(self, start, end, retries=1):
        for attempt in range(1, retries + 2):
            print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")

            if self.check_daily_limit_in_all_windows():
                self.state["daily_limit_hit"] = True
                self._save_state()
                return "limit_reached"

            if not self.open_save_popup():
                print(f"⚠ Eșec la deschiderea popup-ului pentru {start}-{end}")
                time.sleep(1)
                continue

            if self.check_daily_limit_in_all_windows():
                self.state["daily_limit_hit"] = True
                self._save_state()
                return "limit_reached"

            success = self.fill_and_save_range(start, end)
            if success:
                print("⏳ Aștept 5s pentru finalizarea descărcării segmentului...")
                time.sleep(5)

                # AICI E CHEIA - verifică din nou după așteptare
                if self.check_daily_limit_in_all_windows():
                    self.state["daily_limit_hit"] = True
                    self._save_state()
                    print(f"⚠ Segmentul {start}-{end} a eșuat din cauza limitei - NU se marchează ca reușit")
                    return "limit_reached"

                # Doar aici marchează ca reușit dacă nu e limită
                print(f"✅ Segmentul {start}-{end} descărcat cu succes")
                return True
            else:
                print(f"⚠ Retry pentru segmentul {start}-{end}")
                time.sleep(1)
        print(f"❌ Renunț la segmentul {start}-{end} după {retries+1} încercări.")
        return False

    def save_all_pages_in_batches(self, resume_from=1):
        total = self.get_total_pages()
        if total <= 0:
            print("⚠ Nu am obținut numărul total de pagini; nu pot continua.")
            return 0, False  # pagini, limit_reached_flag

        bs = self.batch_size
        segments = []

        if resume_from == 1:
            first_end = min(bs - 1, total)
            if first_end >= 1:
                segments.append((1, first_end))
            current = bs
        else:
            current = resume_from

        while current <= total:
            end = min(current + bs - 1, total)
            segments.append((current, end))
            current += bs

        last_successful_page = resume_from - 1  # Ultima pagină cu adevărat reușită

        for (start, end) in segments:
            if self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică a fost deja atinsă anterior; opresc segmentele.")
                return last_successful_page, True

            print(f"📦 Procesez segmentul {start}-{end}")
            result = self.save_page_range(start, end, retries=1)

            if result == "limit_reached":
                print(f"⚠ Segmentul {start}-{end} a eșuat din cauza limitei - progresul rămâne la {last_successful_page}")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return last_successful_page, True

            if not result:
                print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc.")
                return last_successful_page, False

            # DOAR dacă segmentul a reușit cu adevărat, actualizează progresul
            last_successful_page = end
            self._update_partial_issue_progress(self.current_issue_url, end, total_pages=total)
            print(f"✅ Progres real salvat: pagini până la {end}")
            time.sleep(1)

        print("🎯 Toate segmentele au fost procesate pentru acest issue.")
        return total, False

    def extract_issue_links_from_collection(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-group')))
            anchors = self.driver.find_elements(By.CSS_SELECTOR, 'li.list-group-item a[href^="/view/"], li.list-group-item a[href^="/en/view/"], li.list-group-item a[href^="/ro/view/"]')
            links = []
            for a in anchors:
                href = a.get_attribute("href")
                if href and '/view/' in href:
                    normalized = href.split('?')[0].rstrip('/')
                    links.append(normalized)
            unique = []
            seen = set()
            for l in links:
                if l not in seen:
                    seen.add(l)
                    unique.append(l)
            print(f"🔗 Am găsit {len(unique)} linkuri de issue în colecție.")
            return unique
        except Exception as e:
            print(f"❌ Eroare la extragerea linkurilor din colecție: {e}")
            return []

    def move_issue_pdfs(self, issue_url: str, issue_title: str):
        prefix = issue_url.rstrip('/').split('/')[-1]
        folder_name = self._safe_folder_name(issue_title or prefix)
        dest_dir = os.path.join(self.download_dir, folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        moved = False
        for fname in os.listdir(self.download_dir):
            if not fname.lower().endswith(".pdf"):
                continue
            if prefix in fname:
                src = os.path.join(self.download_dir, fname)
                dst = os.path.join(dest_dir, fname)
                try:
                    os.replace(src, dst)
                    moved = True
                except Exception as e:
                    print(f"⚠ Nu am reușit să mut {fname} în {dest_dir}: {e}")
        if moved:
            print(f"📁 Toate PDF-urile pentru '{issue_title}' au fost mutate în '{dest_dir}'.")
        else:
            print(f"ℹ️ Nu am găsit PDF-uri de mutat pentru '{issue_title}' cu prefix '{prefix}'.")

    def open_new_tab_and_download(self, url):
        normalized_url = url.rstrip('/')

        # Verifică cu skip URLs dinamice
        if normalized_url in self.dynamic_skip_urls:
            print(f"⏭️ Sar peste {url} (în skip list).")
            return False

        already_done = any(
            item.get("url") == normalized_url and item.get("completed_at") and
            item.get("last_successful_segment_end", 0) >= (item.get("total_pages") or float('inf'))
            for item in self.state.get("downloaded_issues", [])
        )
        if already_done:
            print(f"⏭️ Sar peste {url} (deja descărcat complet).")
            return False

        if self.state.get("daily_limit_hit", False):
            print("⚠ Nu mai pot continua din cauza limitei zilnice.")
            return False

        if self.remaining_quota() <= 0:
            print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă. Opresc procesarea.")
            return False

        try:
            print(f"\n📥 Deschid fila pentru {url}")
            if not self.attached_existing:
                self.ensure_alive_fallback()

            prev_handles = set(self.driver.window_handles)
            self.driver.execute_script("window.open('');")
            new_handles = set(self.driver.window_handles)
            diff = new_handles - prev_handles
            new_handle = diff.pop() if diff else self.driver.window_handles[-1]
            self.driver.switch_to.window(new_handle)

            if not self.navigate_to_page(url):
                return False

            time.sleep(1)

            # verificare imediată dacă e pagina cu limita
            if self.check_daily_limit_in_all_windows():
                print("⚠ Nu mai pot continua din cauza limitei zilnice (pagina de limită detectată).")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return False

            title, subtitle = self.get_issue_metadata()

            # Verifică fișierele existente pe disk
            existing_pages = self.get_existing_pdf_segments(url)
            print(f"📊 Pagini existente pe disk: {existing_pages}")

            # determină de unde reiau - combină JSON + fișiere existente
            resume_from = 1
            json_progress = 0
            for item in self.state.get("downloaded_issues", []):
                if item.get("url") == normalized_url:
                    json_progress = item.get("last_successful_segment_end", 0)
                    total_pages = item.get("total_pages")
                    if json_progress and total_pages and json_progress >= total_pages:
                        resume_from = None
                    break

            # Ia maximul dintre progresul din JSON și fișierele existente
            actual_progress = max(json_progress, existing_pages)
            if actual_progress > 0 and resume_from is not None:
                resume_from = actual_progress + 1
                print(f"📄 Reiau de la pagina {resume_from} (JSON: {json_progress}, Disk: {existing_pages})")

            if resume_from is None:
                print(f"⏭️ Sar peste {url} (deja complet).")
                return False

            self.current_issue_url = normalized_url

            # Adaugă issue-ul în progres dacă nu există sau actualizează cu progresul real
            existing_item = next((item for item in self.state.get("downloaded_issues", []) if item.get("url") == normalized_url), None)
            if not existing_item:
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)
            elif actual_progress > existing_item.get("last_successful_segment_end", 0):
                # Actualizează cu progresul real de pe disk
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)

            pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)
            if pages_done == 0 and not limit_hit:
                print(f"⚠ Descărcarea pentru {url} a eșuat complet.")
                return False

            if limit_hit:
                print(f"⚠ Limita zilnică atinsă în timpul issue-ului {url}; progresul parțial a fost salvat.")
                return False

            # === AICI se marchează completarea ===
            self.mark_issue_done(url, pages_done, title=title, subtitle=subtitle, total_pages=pages_done)
            print(f"✅ Descărcarea pentru {url} finalizată complet ({pages_done} pagini).")
            self.move_issue_pdfs(url, title or normalized_url)
            return True

        except WebDriverException as e:
            print(f"❌ Eroare WebDriver pentru {url}: {e}")
            return False
        except Exception as e:
            print(f"❌ Eroare în open_new_tab_and_download pentru {url}: {e}")
            return False
        finally:
            try:
                self.driver.close()
                if self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

    def ensure_alive_fallback(self):
        try:
            _ = self.driver.title
        except Exception as e:
            print(f"⚠ Conexiune WebDriver moartă ({e}), pornesc instanță nouă ca fallback.")
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--incognito")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.attached_existing = False

    def run_collection(self, collection_url):
        print(f"🌐 Încep procesarea colecției: {collection_url}")
        if not self.driver:
            print("❌ Driver neinițializat.")
            return False
        if not self.navigate_to_page(collection_url):
            return False

        if self.state.get("daily_limit_hit", False):
            print("⚠ Nu mai pot continua din cauza limitei zilnice.")
            return True

        issue_links = self.extract_issue_links_from_collection()
        if not issue_links:
            print("⚠ Nu s-au găsit issue-uri în colecție.")
            return False

        # Sortează linkurile: mai întâi cele parțial descărcate, apoi restul
        pending = []
        for link in issue_links:
            normalized = link.rstrip('/')
            if normalized in self.dynamic_skip_urls:
                continue  # Skip complet
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if exists and exists.get("last_successful_segment_end", 0) and exists.get("total_pages") and exists.get("last_successful_segment_end", 0) < exists.get("total_pages", 0):
                pending.append(link)
            elif not exists or not exists.get("completed_at"):
                pending.append(link)

        print(f"📊 Procesez {len(pending)} issue-uri din colecția curentă")

        processed_any = False
        for link in pending:
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print(f"⚠ Limita zilnică atinsă ({DAILY_LIMIT}) sau flag daily_limit_hit; opresc.")
                break
            result = self.open_new_tab_and_download(link)
            if result:
                processed_any = True
            time.sleep(1)

        # Verifică dacă toate issue-urile din această colecție sunt complete
        all_done = True
        for link in issue_links:
            normalized = link.rstrip('/')
            if normalized in self.dynamic_skip_urls:
                continue
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if not exists or not exists.get("completed_at") or \
               (exists.get("total_pages") and exists.get("last_successful_segment_end", 0) < exists.get("total_pages", 0)):
                all_done = False
                break

        return all_done

    def run_additional_collections(self):
        """Procesează colecțiile adiționale după colecția principală"""
        start_index = self.state.get("current_additional_collection_index", 0)

        for i in range(start_index, len(ADDITIONAL_COLLECTIONS)):
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print(f"⚠ Limita zilnică atinsă, opresc procesarea colecțiilor adiționale.")
                break

            collection_url = ADDITIONAL_COLLECTIONS[i]
            print(f"\n🔄 Procesez colecția adițională {i+1}/{len(ADDITIONAL_COLLECTIONS)}: {collection_url}")

            # Actualizează indexul colecției curente
            self.state["current_additional_collection_index"] = i
            self._save_state()

            collection_completed = self.run_collection(collection_url)

            if collection_completed and not self.state.get("daily_limit_hit", False):
                # Colecția completă, trecem la următoarea
                print(f"✅ Colecția adițională {i+1} completă, trec la următoarea.")
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
            elif self.state.get("daily_limit_hit", False):
                # Limita atinsă, opresc
                break
            else:
                # Progres parțial, opresc pentru astăzi
                break

        # Verifică dacă toate colecțiile adiționale sunt complete
        current_index = self.state.get("current_additional_collection_index", 0)
        if current_index >= len(ADDITIONAL_COLLECTIONS):
            print("🎉 TOATE colecțiile adiționale au fost procesate!")
            return True
        else:
            remaining = len(ADDITIONAL_COLLECTIONS) - current_index
            print(f"⚠ Mai rămân {remaining} colecții adiționale de procesat.")
            return True

    def run(self):
        print("🧪 Încep executarea Chrome PDF Downloader")
        print("=" * 60)

        try:
            if not self.setup_chrome_driver():
                return False

            # Resetează flag-ul de limită și curăță ferestrele vechi cu limita
            print("🔄 Resetez flag-ul de limită zilnică și verific ferestrele existente...")
            self.state["daily_limit_hit"] = False
            self._save_state()

            # Sincronizează JSON-ul cu fișierele de pe disk
            self.sync_json_with_disk_files()

            # Verifică și închide ferestrele cu limita deschise din sesiuni anterioare (fără să seteze flag-ul)
            if self.check_daily_limit_in_all_windows(set_flag=False):
                print("⚠ Am găsit ferestre cu limita deschise din sesiuni anterioare.")
                print("🔄 Le-am închis și reîncerc procesarea...")

            # ETAPA 1: Procesează colecția principală (dacă nu e completă)
            if not self.state.get("main_collection_completed", False):
                print(f"\n📚 ETAPA 1: Procesez colecția principală: {self.main_collection_url}")

                main_completed = self.run_collection(self.main_collection_url)

                if self.state.get("daily_limit_hit", False):
                    print("⚠ Limita zilnică atinsă în colecția principală.")
                    return True

                if main_completed:
                    print("✅ Colecția principală completă!")
                    self.state["main_collection_completed"] = True
                    self._save_state()
                else:
                    print("⚠ Colecția principală nu este completă încă.")
                    return True
            else:
                print("✅ Colecția principală a fost deja completată.")

            # ETAPA 2: Procesează colecțiile adiționale
            if self.remaining_quota() > 0 and not self.state.get("daily_limit_hit", False):
                print(f"\n📚 ETAPA 2: Procesez colecțiile adiționale")
                self.run_additional_collections()

            print("✅ Toate operațiunile au fost inițate.")
            self._finalize_session()
            return True

        except KeyboardInterrupt:
            print("\n\n⚠ Intervenție manuală: întrerupt.")
            return False
        except Exception as e:
            print(f"\n❌ Eroare neașteptată: {e}")
            return False
        finally:
            if not self.attached_existing and self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass

    def _finalize_session(self):
        if self.driver:
            if self.attached_existing:
                print("🔖 Am păstrat sesiunea Chrome existentă deschisă (nu fac quit).")
            else:
                print("🚪 Închid browserul.")
                try:
                    self.driver.quit()
                except Exception:
                    pass


def main():
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    else:
        url = "https://adt.arcanum.com/en/collection/GazetaMatematica/"
    downloader = ChromePDFDownloader(main_collection_url=url, download_dir="D:\\", batch_size=50)
    success = downloader.run()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")
        sys.exit(1)