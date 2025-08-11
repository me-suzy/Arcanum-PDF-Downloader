"""
Automatizare descărcare PDF-uri din Arcanum:
- Păstrează toate issue-urile în state.json.
- Prioritizează issue-urile parțial descărcate și respectă ordinea din colecție.
- Copiază fișierele PDF din D:\ în folderul specific issue-ului și păstrează originalele în D:\.
- Șterge fișierele PDF originale din folderul specific issue-ului după combinare.
- Folosește segmente de 49 de pagini (1-49, 50-99, 100-149, etc.).
- Începe cu următorul issue (ex. Convietuirea_1999-2000).
"""

import time
import os
import sys
import re
import json
import shutil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException

# Colecțiile adiționale
ADDITIONAL_COLLECTIONS = [
    "https://adt.arcanum.com/ro/collection/Convietuirea/",
    # Adaugă alte colecții aici
]

STATIC_SKIP_URLS = {
    ""
}

DAILY_LIMIT = 105
STATE_FILENAME = "state.json"
SKIP_URLS_FILENAME = "skip_urls.json"

class ChromePDFDownloader:
    def __init__(self, main_collection_url, download_dir=None, batch_size=49, timeout=15):
        self.main_collection_url = main_collection_url
        self.batch_size = batch_size  # 49 pentru segmentele dorite
        self.timeout = timeout
        self.download_dir = download_dir or os.getcwd()
        self.driver = None
        self.wait = None
        self.attached_existing = False
        self.state_path = os.path.join(self.download_dir, STATE_FILENAME)
        self.skip_urls_path = os.path.join(self.download_dir, SKIP_URLS_FILENAME)
        self.current_issue_url = None
        self.dynamic_skip_urls = set()
        self._issue_links_cache = {}  # Cache pentru lista de issue-uri
        self._load_skip_urls()
        self._load_state()
        self.fix_existing_json()

    def _load_skip_urls(self):
        self.dynamic_skip_urls = set(STATIC_SKIP_URLS)
        if os.path.exists(self.skip_urls_path):
            try:
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dynamic_skip_urls.update(url.rstrip('/') for url in data.get("completed_urls", []))
                print(f"📋 Încărcat {len(self.dynamic_skip_urls)} URL-uri de skip")
            except Exception as e:
                print(f"⚠ Eroare la citirea {SKIP_URLS_FILENAME}: {e}")

    def _save_skip_urls(self):
        try:
            completed_urls = [item["url"] for item in self.state.get("downloaded_issues", [])
                            if item.get("completed_at") and item.get("last_successful_segment_end", 0) >= item.get("total_pages", 0)]
            data = {
                "last_updated": datetime.now().isoformat(),
                "completed_urls": sorted(list(set(STATIC_SKIP_URLS | set(completed_urls))))
            }
            with open(self.skip_urls_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Salvat {len(data['completed_urls'])} URL-uri în {SKIP_URLS_FILENAME}")
        except Exception as e:
            print(f"⚠ Eroare la salvarea {SKIP_URLS_FILENAME}: {e}")

    def _safe_folder_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _decode_unicode_escapes(self, obj):
        if isinstance(obj, dict):
            return {key: self._decode_unicode_escapes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._decode_unicode_escapes(item) for item in obj]
        elif isinstance(obj, str) and '\\u' in obj:
            try:
                return obj.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
            except:
                return obj
        return obj

    def get_existing_pdf_segments(self, issue_url):
        issue_id = issue_url.rstrip('/').split('/')[-1]
        max_page = 0
        print(f"🔍 Caut fișiere pentru issue_id: {issue_id}")
        try:
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf') and issue_id in filename:
                    match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        start_page = int(match.group(1))
                        end_page = int(match.group(2))
                        max_page = max(max_page, end_page)
                        print(f"📁 Găsit: {filename} (pagini {start_page}-{end_page})")
        except Exception as e:
            print(f"⚠ Eroare la scanarea fișierelor: {e}")
        print(f"📊 Pagini maxime pe disk: {max_page}")
        return max_page

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
                    loaded = self._decode_unicode_escapes(loaded)
                issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))
                completed_count = len([i for i in issues if i.get("completed_at")])
                if loaded.get("date") == today:
                    self.state = {
                        **loaded,
                        "downloaded_issues": issues,
                        "count": completed_count
                    }
                else:
                    self.state = {
                        **default,
                        "downloaded_issues": issues,
                        "main_collection_completed": loaded.get("main_collection_completed", False),
                        "current_additional_collection_index": loaded.get("current_additional_collection_index", 0),
                        "count": completed_count
                    }
                    print(f"🆕 Zi nouă: {len(issues)} issue-uri păstrate")
            except Exception as e:
                print(f"⚠ Eroare la citirea stării: {e}")
        self._save_state()

    def _save_state(self):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Eroare la salvarea stării: {e}")

    def _normalize_downloaded_issues(self, raw):
        normalized = []
        seen_urls = set()
        for item in raw:
            url = item.get("url", "").rstrip('/')
            if url and url not in seen_urls:
                normalized.append({
                    "url": url,
                    "title": item.get("title", ""),
                    "subtitle": item.get("subtitle", ""),
                    "pages": item.get("pages", 0),
                    "completed_at": item.get("completed_at", ""),
                    "last_successful_segment_end": item.get("last_successful_segment_end", 0),
                    "total_pages": item.get("total_pages")
                })
                seen_urls.add(url)
        return normalized

    def fix_existing_json(self):
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data = self._decode_unicode_escapes(data)
            data["downloaded_issues"] = self._normalize_downloaded_issues(data.get("downloaded_issues", []))
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("✅ JSON reparat")

    def remaining_quota(self):
        return max(0, DAILY_LIMIT - self.state.get("count", 0))

    def _update_partial_issue_progress(self, issue_url, last_successful_segment_end, total_pages=None, title=None, subtitle=None):
        normalized = issue_url.rstrip('/')
        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item["url"] == normalized:
                item.update({
                    "last_successful_segment_end": last_successful_segment_end,
                    "total_pages": total_pages or item.get("total_pages"),
                    "title": title or item.get("title", ""),
                    "subtitle": subtitle or item.get("subtitle", "")
                })
                self.state["downloaded_issues"].pop(i)
                self.state["downloaded_issues"].insert(0, item)
                break
        else:
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
        self._save_state()
        print(f"💾 Progres: {normalized} - pagini {last_successful_segment_end}/{total_pages or '?'}")

    def mark_issue_done(self, issue_url, pages_count, title=None, subtitle=None, total_pages=None):
        normalized = issue_url.rstrip('/')
        now_iso = datetime.now().isoformat(timespec="seconds")
        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item["url"] == normalized:
                item.update({
                    "title": title or item.get("title", ""),
                    "subtitle": subtitle or item.get("subtitle", ""),
                    "pages": pages_count,
                    "completed_at": now_iso,
                    "last_successful_segment_end": pages_count,
                    "total_pages": total_pages or item.get("total_pages")
                })
                self.state["downloaded_issues"].pop(i)
                self.state["downloaded_issues"].insert(0, item)
                break
        else:
            self.state["downloaded_issues"].insert(0, {
                "url": normalized,
                "title": title or "",
                "subtitle": subtitle or "",
                "pages": pages_count,
                "completed_at": now_iso,
                "last_successful_segment_end": pages_count,
                "total_pages": total_pages
            })
        self.state["count"] = len([i for i in self.state["downloaded_issues"] if i.get("completed_at")])
        self.state["pages_downloaded"] = self.state.get("pages_downloaded", 0) + pages_count
        self.state.setdefault("recent_links", []).insert(0, {
            "url": normalized,
            "title": title or "",
            "subtitle": subtitle or "",
            "pages": pages_count,
            "timestamp": now_iso
        })
        self.dynamic_skip_urls.add(normalized)
        self._save_state()
        self._save_skip_urls()
        print(f"✅ Issue finalizat: {normalized} ({pages_count} pagini)")

    def setup_chrome_driver(self):
        try:
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
                print("✅ Conectat la Chrome existent")
                return True
            except WebDriverException:
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
                print("✅ Chrome nou pornit")
                return True
        except WebDriverException as e:
            print(f"❌ Eroare WebDriver: {e}")
            return False

    def navigate_to_page(self, url):
        try:
            print(f"🌐 Navighez la: {url}")
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
            print("✅ Pagina încărcată")
            return True
        except Exception as e:
            print(f"❌ Eroare navigare: {e}")
            return False

    def get_issue_metadata(self):
        title = subtitle = ""
        try:
            breadcrumb = self.driver.find_element(By.CSS_SELECTOR, "li.breadcrumb-item.active")
            try:
                subtitle = breadcrumb.find_element(By.CSS_SELECTOR, "#pdfview-pdfcontents span").text.strip()
            except:
                pass
            raw = breadcrumb.text.strip()
            title = raw.replace(subtitle, "").strip() if subtitle else raw
        except:
            pass
        return title, subtitle

    def get_total_pages(self, max_attempts=5, delay_between=1.0):
        for attempt in range(1, max_attempts + 1):
            try:
                for el in self.driver.find_elements(By.CSS_SELECTOR, 'div.MuiInputAdornment-root.MuiInputAdornment-positionEnd'):
                    match = re.search(r'/\s*(\d+)', el.text.strip())
                    if match:
                        print(f"✅ Total pagini: {match.group(1)}")
                        return int(match.group(1))
                for el in self.driver.find_elements(By.XPATH, "//*[contains(text(), '/')]"):
                    match = re.search(r'/\s*(\d+)', el.text.strip())
                    if match:
                        print(f"✅ Total pagini (text): {match.group(1)}")
                        return int(match.group(1))
                js_result = self.driver.execute_script("""
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    const regex = /\\/\\s*(\\d+)/;
                    while(walker.nextNode()) {
                        const m = walker.currentNode.nodeValue.match(regex);
                        if (m) return m[1];
                    }
                    return null;
                """)
                if js_result:
                    print(f"✅ Total pagini (JS): {js_result}")
                    return int(js_result)
                print(f"⚠ Încercare {attempt}: Nu am găsit totalul")
                time.sleep(delay_between)
            except Exception as e:
                print(f"⚠ Eroare get_total_pages: {e}")
                time.sleep(delay_between)
        print("❌ Nu s-a găsit totalul paginilor")
        return 0

    def open_save_popup(self):
        try:
            try:
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiDialog-container')))
            except:
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]')))
            if button.tag_name.lower() == "svg":
                button = button.find_element(By.XPATH, "./ancestor::button")
            for _ in range(3):
                try:
                    button.click()
                    return True
                except ElementClickInterceptedException:
                    self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                    time.sleep(1)
            print("❌ Eșec popup salvare")
            return False
        except Exception as e:
            print(f"❌ Eroare popup salvare: {e}")
            return False

    def fill_and_save_range(self, start, end):
        try:
            time.sleep(2)
            first_input = self.wait.until(EC.presence_of_element_located((By.ID, "first page")))
            first_input.send_keys(Keys.CONTROL + "a")
            first_input.send_keys(str(start))
            print(f"✏️ Start: {start}")
            time.sleep(2)
            last_input = self.wait.until(EC.presence_of_element_located((By.ID, "last page")))
            last_input.send_keys(Keys.CONTROL + "a")
            last_input.send_keys(str(end))
            print(f"✏️ End: {end}")
            time.sleep(2)
            save_btn = self.wait.until(EC.element_to_be_clickable((
                By.XPATH, '//button[.//text()[contains(normalize-space(.), "Salvați") or contains(normalize-space(.), "Save")]]'
            )))
            save_btn.click()
            print(f"✅ Segment {start}-{end} salvat")
            return True
        except Exception as e:
            print(f"❌ Eroare salvare {start}-{end}: {e}")
            return False

    def check_daily_limit_in_all_windows(self, set_flag=True):
        current_window = self.driver.current_window_handle
        limit_reached = False
        for handle in self.driver.window_handles:
            if handle != current_window:  # Verifică doar tab-ul curent pentru a evita comutarea
                continue
            try:
                self.driver.switch_to.window(handle)
                if "Daily download limit reached" in self.driver.find_element(By.TAG_NAME, "body").text:
                    print(f"⚠ Limita zilnică în fereastra {handle}")
                    limit_reached = True
            except:
                continue
        self.driver.switch_to.window(current_window)
        if limit_reached and set_flag:
            self.state["daily_limit_hit"] = True
            self._save_state()
        return limit_reached

    def save_page_range(self, start, end, retries=1):
        for attempt in range(1, retries + 2):
            print(f"🔄 Segment {start}-{end}, încercarea {attempt}")
            if self.check_daily_limit_in_all_windows():
                return "limit_reached"
            if not self.open_save_popup():
                time.sleep(1)
                continue
            if self.check_daily_limit_in_all_windows():
                return "limit_reached"
            if self.fill_and_save_range(start, end):
                time.sleep(5)
                if self.check_daily_limit_in_all_windows():
                    print(f"⚠ Segment {start}-{end} a eșuat: limită")
                    return "limit_reached"
                print(f"✅ Segment {start}-{end} descărcat")
                return True
            time.sleep(1)
        print(f"❌ Eșec segment {start}-{end}")
        return False

    def save_all_pages_in_batches(self, resume_from=1):
        total = self.get_total_pages()
        if total <= 0:
            print("⚠ Nu s-a obținut totalul paginilor")
            return 0, False
        bs = self.batch_size  # 49
        segments = []
        current = resume_from
        while current <= total:
            start = current
            next_multiple = ((start - 1) // bs + 1) * bs
            end = min(next_multiple, total)
            segments.append((start, end))
            current = end + 1
        print(f"📋 Segmente: {segments}")
        last_successful_page = resume_from - 1
        for start, end in segments:
            if self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică atinsă")
                return last_successful_page, True
            result = self.save_page_range(start, end)
            if result == "limit_reached":
                return last_successful_page, True
            if not result:
                print(f"❌ Eșec segment {start}-{end}")
                return last_successful_page, False
            last_successful_page = end
            self._update_partial_issue_progress(self.current_issue_url, end, total_pages=total)
            time.sleep(1)
        return total, False

    def extract_issue_links_from_collection(self, collection_url):
        if collection_url in self._issue_links_cache:
            print(f"📋 Folosesc cache pentru {collection_url}")
            return self._issue_links_cache[collection_url]
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-group')))
            anchors = self.driver.find_elements(By.CSS_SELECTOR, 'li.list-group-item a[href*="/view/"]')
            links = []
            for a in anchors:
                href = a.get_attribute("href").split('?')[0].rstrip('/')
                if '/view/' in href:
                    links.append((href, a.text.strip()))
            unique = []
            seen = set()
            for href, title in links:
                if href not in seen:
                    unique.append((href, title))
                    seen.add(href)
            self._issue_links_cache[collection_url] = unique
            print(f"🔗 {len(unique)} issue-uri găsite pentru {collection_url}")
            return unique
        except Exception as e:
            print(f"❌ Eroare extragere linkuri pentru {collection_url}: {e}")
            return []

    def move_issue_pdfs(self, issue_url: str, issue_title: str):
        prefix = issue_url.rstrip('/').split('/')[-1]
        folder_name = self._safe_folder_name(issue_title or prefix)
        dest_dir = os.path.join(self.download_dir, folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        pdf_files = []
        for fname in os.listdir(self.download_dir):
            if fname.lower().endswith(".pdf") and prefix in fname:
                src = os.path.join(self.download_dir, fname)
                dst = os.path.join(dest_dir, fname)
                try:
                    shutil.copy2(src, dst)
                    pdf_files.append(dst)
                    print(f"📁 Copiat: {fname} → {folder_name}/")
                except Exception as e:
                    print(f"⚠ Eroare copiere {fname}: {e}")
        if not pdf_files:
            print(f"ℹ️ Nu s-au găsit PDF-uri pentru '{issue_title}'")
            return
        try:
            output_file = os.path.join(dest_dir, f"{folder_name}.pdf")
            if len(pdf_files) > 1:
                from PyPDF2 import PdfMerger
                merger = PdfMerger()
                def get_page_number(pdf_path):
                    match = re.search(r'__pages(\d+)-(\d+)\.pdf', os.path.basename(pdf_path))
                    return int(match.group(1)) if match else float('inf')
                sorted_pdfs = sorted(pdf_files, key=get_page_number)
                for pdf in sorted_pdfs:
                    merger.append(pdf)
                    print(f"📄 Adăugat: {os.path.basename(pdf)}")
                merger.write(output_file)
                merger.close()
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                    print(f"✅ Fișier combinat: {file_size_mb:.2f} MB")
                    for pdf in pdf_files:
                        try:
                            os.remove(pdf)
                            print(f"🗑️ Șters: {os.path.basename(pdf)} din {folder_name}/")
                        except Exception as e:
                            print(f"⚠ Eroare ștergere {os.path.basename(pdf)}: {e}")
            elif len(pdf_files) == 1:
                shutil.copy2(pdf_files[0], output_file)
                print(f"✅ PDF copiat: {os.path.basename(output_file)}")
                try:
                    os.remove(pdf_files[0])
                    print(f"🗑️ Șters: {os.path.basename(pdf_files[0])} din {folder_name}/")
                except Exception as e:
                    print(f"⚠ Eroare ștergere {os.path.basename(pdf_files[0])}: {e}")
        except Exception as e:
            print(f"❌ Eroare combinare PDF: {e}")

    def get_pending_issues(self, collection_url):
        issue_links = self.extract_issue_links_from_collection(collection_url)
        pending = []
        for item in self.state.get("downloaded_issues", []):
            normalized = item["url"].rstrip('/')
            if normalized in [link for link, _ in issue_links] and not item.get("completed_at") and \
               item.get("last_successful_segment_end", 0) < item.get("total_pages", float('inf')):
                title = next((t for l, t in issue_links if l == normalized), item.get("title", ""))
                pending.append((normalized, title))
                print(f"📋 Prioritate: {normalized} (parțial, {item['last_successful_segment_end']}/{item['total_pages']})")
        for link, title in issue_links:
            normalized = link.rstrip('/')
            if normalized not in self.dynamic_skip_urls and \
               not any(i.get("url") == normalized and i.get("completed_at") for i in self.state.get("downloaded_issues", [])):
                if normalized not in [p[0] for p in pending]:
                    pending.append((link, title))
                    print(f"📋 Adăugat: {normalized} (nou)")
        return pending

    def open_new_tab_and_download(self, url, provided_title=None):
        normalized_url = url.rstrip('/')
        print(f"🔍 Procesez: {normalized_url}")
        if normalized_url in self.dynamic_skip_urls:
            print(f"⏭️ Sar peste (în skip list)")
            return False
        for item in self.state.get("downloaded_issues", []):
            if item.get("url") == normalized_url and item.get("completed_at") and \
               item.get("last_successful_segment_end", 0) >= item.get("total_pages", float('inf')):
                print(f"⏭️ Sar peste (complet)")
                return False
        if self.state.get("daily_limit_hit", False) or self.remaining_quota() <= 0:
            print(f"⚠ Limita zilnică atinsă")
            return False
        try:
            prev_handles = set(self.driver.window_handles)
            self.driver.execute_script("window.open('');")
            new_handle = (set(self.driver.window_handles) - prev_handles).pop() if (set(self.driver.window_handles) - prev_handles) else self.driver.window_handles[-1]
            self.driver.switch_to.window(new_handle)
            if not self.navigate_to_page(url):
                return False
            self.current_issue_url = normalized_url
            title, subtitle = self.get_issue_metadata()
            title = provided_title or title
            existing_pages = self.get_existing_pdf_segments(url)
            json_progress = 0
            total_pages = None
            for item in self.state.get("downloaded_issues", []):
                if item.get("url") == normalized_url:
                    json_progress = item.get("last_successful_segment_end", 0)
                    total_pages = item.get("total_pages")
                    break
            print(f"📋 JSON: {json_progress}, Disk: {existing_pages}, Total: {total_pages}")
            actual_progress = max(json_progress, existing_pages)
            resume_from = actual_progress + 1 if actual_progress > 0 else 1
            if total_pages and actual_progress >= total_pages:
                print(f"⏭️ Sar peste (complet: {actual_progress}/{total_pages})")
                return False
            print(f"📄 Reiau de la pagina {resume_from}")
            if actual_progress > 0:
                self._update_partial_issue_progress(normalized_url, actual_progress, total_pages, title, subtitle)
            pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)
            if pages_done == 0 and not limit_hit:
                return False
            if limit_hit:
                return False
            self.mark_issue_done(url, pages_done, title, subtitle, total_pages=pages_done)
            self.move_issue_pdfs(url, title or normalized_url)
            return True
        except Exception as e:
            print(f"❌ Eroare: {e}")
            return False
        finally:
            try:
                if self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass

    def run_collection(self, collection_url):
        print(f"📚 Procesez colecția: {collection_url}")
        if not self.driver:
            return False
        if self.state.get("daily_limit_hit", False):
            print("⚠ Limita zilnică atinsă")
            return True
        if not self.navigate_to_page(collection_url):
            return False
        pending = self.get_pending_issues(collection_url)
        print(f"📊 {len(pending)} issue-uri de procesat")
        processed_any = False
        for link, title in pending:
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                break
            processed_any |= self.open_new_tab_and_download(link, title)
            time.sleep(1)
        all_done = all(link.rstrip('/') in self.dynamic_skip_urls or
                       any(i.get("url") == link.rstrip('/') and i.get("completed_at") and
                           i.get("last_successful_segment_end", 0) >= i.get("total_pages", float('inf'))
                           for i in self.state.get("downloaded_issues", []))
                       for link, _ in self._issue_links_cache.get(collection_url, []))
        return all_done

    def run_additional_collections(self):
        start_index = self.state.get("current_additional_collection_index", 0)
        for i in range(start_index, len(ADDITIONAL_COLLECTIONS)):
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                break
            collection_url = ADDITIONAL_COLLECTIONS[i]
            print(f"📚 Colecția adițională {i+1}/{len(ADDITIONAL_COLLECTIONS)}: {collection_url}")
            self.state["current_additional_collection_index"] = i
            self._save_state()
            if self.run_collection(collection_url) and not self.state.get("daily_limit_hit", False):
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
            else:
                break
        return self.state.get("current_additional_collection_index", 0) >= len(ADDITIONAL_COLLECTIONS)

    def run(self):
        print("🧪 Pornesc Chrome PDF Downloader")
        if not self.setup_chrome_driver():
            return False
        try:
            self.state["daily_limit_hit"] = False
            self._save_state()
            if not self.state.get("main_collection_completed", False):
                print(f"📚 Colecția principală: {self.main_collection_url}")
                if self.run_collection(self.main_collection_url):
                    self.state["main_collection_completed"] = True
                    self._save_state()
                else:
                    return True
            else:
                print("✅ Colecția principală completă")
            if self.remaining_quota() > 0 and not self.state.get("daily_limit_hit", False):
                self.run_additional_collections()
            print("✅ Operațiuni finalizate")
            return True
        except KeyboardInterrupt:
            print("⚠ Întrerupt manual")
            return False
        except Exception as e:
            print(f"❌ Eroare neașteptată: {e}")
            return False
        finally:
            if not self.attached_existing and self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

def main():
    if len(sys.argv) >= 2:
        url = sys.argv[1]
    else:
        downloader = ChromePDFDownloader("temp", download_dir="D:\\", batch_size=49)
        if not downloader.state.get("main_collection_completed", False):
            url = "https://adt.arcanum.com/ro/collection/GazetaMatematicaSiFizicaSeriaB"
        elif downloader.state.get("current_additional_collection_index", 0) < len(ADDITIONAL_COLLECTIONS):
            url = ADDITIONAL_COLLECTIONS[downloader.state.get("current_additional_collection_index", 0)]
        else:
            print("🎉 Toate colecțiile procesate! Șterge state.json pentru restart.")
            return True
    downloader = ChromePDFDownloader(main_collection_url=url, download_dir="D:\\", batch_size=49)
    if not downloader.run():
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")
        sys.exit(1)