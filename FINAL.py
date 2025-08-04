#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum (Gazeta Matematica și colecții adiacente):
- Conectare la sesiune Chrome existentă cu remote debugging.
- Dintr-o pagină de colecție extrage toate issue-urile (/view/...).
- Sare peste cele deja descărcate complet sau în SKIP_URLS.
- Limitează la 102 issue-uri pe zi.
- Detectează mesajul de limită zilnică și oprește progresul imediat.
- Reia parțial un issue neterminat (folosind last_successful_segment_end).
- Păstrează stare în state.json: date, count, downloaded_issues (cu metadata), pages_downloaded, recent_links, daily_limit_hit.
- După completarea unui issue, mută PDF-urile aferente într-un folder cu numele titlului.
- La final, raportează dacă s-a terminat totul.
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

# colecții de start adiționale
BASE_COLLECTIONS = [
    "https://adt.arcanum.com/en/collection/GazetaMatematica/",
    "https://adt.arcanum.com/ro/collection/GazetaMatematicaSiFizicaSeriaB/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMatematice/",
    "https://adt.arcanum.com/ro/collection/MinePetrolGaze/"
]

SKIP_URLS = {
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

DAILY_LIMIT = 102
STATE_FILENAME = "state.json"


class ChromePDFDownloader:
    def __init__(self, test_url, download_dir=None, batch_size=50, timeout=15):
        self.test_url = test_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.download_dir = download_dir or os.getcwd()
        self.driver = None
        self.wait = None
        self.attached_existing = False
        self.state_path = os.path.join(self.download_dir, STATE_FILENAME)
        self.current_issue_url = None
        self._load_state()

    def _safe_folder_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _snapshot_folder(self):
        snaps = {}
        try:
            for f in os.listdir(self.download_dir):
                full = os.path.join(self.download_dir, f)
                if os.path.isfile(full):
                    try:
                        snaps[f] = os.path.getsize(full)
                    except Exception:
                        snaps[f] = None
        except Exception:
            pass
        return snaps


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
            "daily_limit_hit": False
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
                        "count": len(issues),
                        "downloaded_issues": issues,
                        "pages_downloaded": loaded.get("pages_downloaded", 0),
                        "recent_links": loaded.get("recent_links", []),
                        "daily_limit_hit": loaded.get("daily_limit_hit", False)
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
                        "daily_limit_hit": False  # Resetează limita zilnică
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
        for item in self.state.setdefault("downloaded_issues", []):
            if item["url"] == normalized:
                item["last_successful_segment_end"] = last_successful_segment_end
                if total_pages is not None:
                    item["total_pages"] = total_pages
                if title:
                    item["title"] = title
                if subtitle:
                    item["subtitle"] = subtitle
                break
        else:
            self.state["downloaded_issues"].append({
                "url": normalized,
                "title": title or "",
                "subtitle": subtitle or "",
                "pages": 0,
                "completed_at": "",
                "last_successful_segment_end": last_successful_segment_end,
                "total_pages": total_pages
            })
        self._save_state()

    def mark_issue_done(self, issue_url, pages_count, title=None, subtitle=None, total_pages=None):
        normalized = issue_url.rstrip('/')
        now_iso = datetime.now().isoformat(timespec="seconds")
        existing = None
        for item in self.state.setdefault("downloaded_issues", []):
            if item.get("url") == normalized:
                existing = item
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
            existing.update(record)
        else:
            self.state["downloaded_issues"].append(record)

        self.state["count"] = len(self.state.get("downloaded_issues", []))
        self.state["pages_downloaded"] = self.state.get("pages_downloaded", 0) + pages_count

        recent_entry = {
            "url": normalized,
            "title": record["title"],
            "subtitle": record["subtitle"],
            "pages": pages_count,
            "timestamp": now_iso
        }
        self.state.setdefault("recent_links", []).append(recent_entry)
        self.state["daily_limit_hit"] = False
        self._save_state()

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

    def check_daily_limit_reached(self):
        try:
            body_text = self.driver.find_element(By.TAG_NAME, "body").text
            if "Daily download limit reached" in body_text:
                print("⚠ Limita zilnică de download a fost atinsă (mesaj detectat pe pagină).")
                return True
        except Exception:
            pass
        return False

    def save_page_range(self, start, end, retries=1):
        for attempt in range(1, retries + 2):
            print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")
            # verifica încă o dată dacă e pagina de limită înainte de orice
            if self.check_daily_limit_reached():
                self.state["daily_limit_hit"] = True
                self._save_state()
                return "limit_reached"

            if not self.open_save_popup():
                print(f"⚠ Eșec la deschiderea popup-ului pentru {start}-{end}")
                time.sleep(1)
                continue

            # încă o verificare imediat după deschiderea popup-ului
            if self.check_daily_limit_reached():
                self.state["daily_limit_hit"] = True
                self._save_state()
                return "limit_reached"

            success = self.fill_and_save_range(start, end)
            if success:
                print("⏳ Aștept 5s pentru finalizarea descărcării segmentului...")
                time.sleep(5)
                if self.check_daily_limit_reached():
                    self.state["daily_limit_hit"] = True
                    self._save_state()
                    return "limit_reached"
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

        for (start, end) in segments:
            if self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică a fost deja atinsă anterior; opresc segmentele.")
                return end - bs, True  # reiau de după ultimul complet efectiv
            print(f"📦 Procesez segmentul {start}-{end}")
            result = self.save_page_range(start, end, retries=1)
            if result == "limit_reached":
                # actualizez progresul parțial și setez flag-ul
                self._update_partial_issue_progress(self.current_issue_url, end, total_pages=total)
                self.state["daily_limit_hit"] = True
                self._save_state()
                print("⚠ Am atins limita zilnică în timpul acestui issue; reiau de aici mâine.")
                return end, True
            if not result:
                print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc.")
                return 0, False
            # actualizez progresul parțial după fiecare segment reușit
            self._update_partial_issue_progress(self.current_issue_url, end, total_pages=total)
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
        already_done = any(
            item.get("url") == normalized_url and item.get("last_successful_segment_end", 0)
            >= (item.get("total_pages") or float('inf'))
            for item in self.state.get("downloaded_issues", [])
        )
        if normalized_url in SKIP_URLS or already_done:
            print(f"⏭️ Sar peste {url} (deja descărcat).")
            return False

        if self.state.get("daily_limit_hit", False):
            print("⚠ Nu mai pot continua din cauza limitei zilnice.")
            return False

        if self.remaining_quota() <= 0:
            print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă. Oprind procesarea.")
            return False

        try:
            print(f"\n📥 Deschid fila pentru {url}")
            if not self.attached_existing:
                self.ensure_alive_fallback()

            before_snap = self._snapshot_folder()

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
            if self.check_daily_limit_reached():
                print("⚠ Nu mai pot continua din cauza limitei zilnice (pagina de limită detectată).")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return False

            title, subtitle = self.get_issue_metadata()

            # determină de unde reiau
            resume_from = 1
            for item in self.state.get("downloaded_issues", []):
                if item.get("url") == normalized_url:
                    last = item.get("last_successful_segment_end", 0)
                    total_pages = item.get("total_pages")
                    if last and total_pages and last < total_pages:
                        resume_from = last + 1
                    elif last and total_pages and last >= total_pages:
                        resume_from = None
                    break

            if resume_from is None:
                print(f"⏭️ Sar peste {url} (deja complet).")
                return False

            self.current_issue_url = normalized_url

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
            print("✅ Toate operațiunile au fost inițate.")
            return True

        issue_links = self.extract_issue_links_from_collection()
        if not issue_links:
            print("⚠ Nu s-au găsit issue-uri în colecție.")
            return False

        pending = []
        done = []
        for link in issue_links:
            normalized = link.rstrip('/')
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if exists and exists.get("last_successful_segment_end", 0) and exists.get("total_pages") and exists.get("last_successful_segment_end", 0) < exists.get("total_pages", 0):
                pending.append(link)
            elif not exists:
                pending.append(link)
            else:
                done.append(link)
        ordered = pending + [l for l in issue_links if l not in pending]

        for link in ordered:
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print(f"⚠ Limita zilnică atinsă ({DAILY_LIMIT}) sau flag daily_limit_hit; opresc.")
                break
            self.open_new_tab_and_download(link)
            time.sleep(1)

        all_done = True
        for link in issue_links:
            normalized = link.rstrip('/')
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if not exists or (exists.get("last_successful_segment_end", 0) == 0):
                all_done = False
                break
        if all_done:
            print("🎉 Am terminat totul de downloadat")
        else:
            print("⚠ Mai rămân issue-uri neterminate, le reiau la următoarea rulare dacă e altă zi.")
        return True

    def run(self):
        print("🧪 Încep executarea Chrome PDF Downloader")
        print("=" * 60)
        try:
            if not self.setup_chrome_driver():
                return False

            if self.state.get("daily_limit_hit", False):
                print("⚠ Nu mai pot continua din cauza limitei zilnice.")
                print("✅ Toate operațiunile au fost inițate.")

                return True

            if any(col.rstrip('/') in self.test_url.rstrip('/') for col in BASE_COLLECTIONS):
                for base in BASE_COLLECTIONS:
                    if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                        break
                    if base.rstrip('/') in self.test_url.rstrip('/') or self.test_url.rstrip('/') == base.rstrip('/'):
                        self.run_collection(base)
            elif "/collection/" in self.test_url:
                if not self.run_collection(self.test_url):
                    return False
            else:
                if not self.navigate_to_page(self.test_url):
                    return False
                title, subtitle = self.get_issue_metadata()
                resume_from = 1
                exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == self.test_url.rstrip('/')), None)
                if exists and exists.get("last_successful_segment_end", 0):
                    resume_from = exists.get("last_successful_segment_end", 0) + 1
                self.current_issue_url = self.test_url.rstrip('/')
                pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)
                if pages_done:
                    if not limit_hit:
                        self.mark_issue_done(self.test_url, pages_done, title=title, subtitle=subtitle, total_pages=pages_done)
                        self.move_issue_pdfs(self.test_url, title or self.test_url.rstrip('/'))
                        print(f"📊 Issue unic descărcat complet: {self.state['count']}/{DAILY_LIMIT}, pagini totale: {self.state['pages_downloaded']}")
                    else:
                        print("⚠ Issue neterminat din cauza limitei; progresul salvat.")
                else:
                    return False

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
    downloader = ChromePDFDownloader(test_url=url, download_dir="D:\\", batch_size=50)
    success = downloader.run()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")
        sys.exit(1)
