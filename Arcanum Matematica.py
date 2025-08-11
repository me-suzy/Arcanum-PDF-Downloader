#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum (Gazeta Matematică):
- Se conectează la o sesiune Chrome existentă cu remote debugging.
- Dintr-o pagină de colecție extrage toate issue-urile (/en/view/...).
- Sare peste link-urile deja procesate (ex: cele din SKIP_URLS).
- Limitează la 102 PDF-uri (issue-uri) pe zi.
- Reface conexiunea doar dacă nu e attach-uit la un Chrome existent; altfel sare la erori de sesiune.
- Pentru fiecare: deschide filă nouă, detectează numărul de pagini, salvează în segmente, închide fila.
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
from selenium.common.exceptions import (
    WebDriverException,
    ElementClickInterceptedException,
)

# URL-urile pe care să le sărim (already downloaded), normalizate fără slash final
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
    "https://adt.arcanum.com/en/view/GazetaMatematica_1935-36"
}
DAILY_LIMIT = 102  # maxim PDF-uri per zi
QUOTA_FILENAME = ".download_quota.json"

class ChromePDFDownloader:
    def __init__(self, test_url, download_dir=None, batch_size=50, timeout=15):
        self.test_url = test_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.download_dir = download_dir or os.getcwd()
        self.driver = None
        self.wait = None
        self.attached_existing = False
        self.quota_path = os.path.join(self.download_dir, QUOTA_FILENAME)
        self._load_quota()

    def _load_quota(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.quota = {"date": today, "count": 0}
        if os.path.exists(self.quota_path):
            try:
                with open(self.quota_path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                if stored.get("date") == today:
                    self.quota["count"] = stored.get("count", 0)
                else:
                    self.quota = {"date": today, "count": 0}
            except Exception:
                self.quota = {"date": today, "count": 0}
        self._save_quota()

    def _save_quota(self):
        try:
            with open(self.quota_path, "w", encoding="utf-8") as f:
                json.dump(self.quota, f)
        except Exception as e:
            print(f"⚠ Nu am putut salva quota: {e}")

    def _increment_quota(self):
        self.quota["count"] += 1
        self._save_quota()

    def remaining_quota(self):
        return max(0, DAILY_LIMIT - self.quota["count"])

    def setup_chrome_driver(self):
        try:
            print("🔧 Inițializare WebDriver – încerc conectare la Chrome existent via remote debugging...")
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
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
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiDialog-container')), message="Aștept dispariția dialogurilor vechi")
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
            print("⏳ Aștept 5s înainte de a completa primul input...")
            time.sleep(5)
            first_input.send_keys(Keys.CONTROL + "a")
            first_input.send_keys(str(start))
            print(f"✏️ Am introdus primul număr: {start}")

            print("⏳ Aștept 5s înainte de a completa al doilea input...")
            time.sleep(5)
            last_input = self.wait.until(EC.presence_of_element_located((By.ID, "last page")))
            last_input.send_keys(Keys.CONTROL + "a")
            last_input.send_keys(str(end))
            print(f"✏️ Am introdus al doilea număr: {end}")

            print("⏳ Aștept 5s înainte de a apăsa butonul de salvare...")
            time.sleep(5)
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

    def save_page_range(self, start, end, retries=1):
        for attempt in range(1, retries + 2):
            print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")
            if not self.open_save_popup():
                print(f"⚠ Eșec la deschiderea popup-ului pentru {start}-{end}")
                time.sleep(1)
                continue
            success = self.fill_and_save_range(start, end)
            if success:
                time.sleep(0.8)
                return True
            else:
                print(f"⚠ Retry pentru segmentul {start}-{end}")
                time.sleep(1)
        print(f"❌ Renunț la segmentul {start}-{end} după {retries+1} încercări.")
        return False

    def save_all_pages_in_batches(self):
        total = self.get_total_pages()
        if total <= 0:
            print("⚠ Nu am obținut numărul total de pagini; nu pot continua.")
            return False

        bs = self.batch_size
        segments = []

        if total >= 1:
            first_end = min(bs - 1, total)
            if first_end >= 1:
                segments.append((1, first_end))

        start = bs
        while start <= total:
            end = min(start + bs - 1, total)
            segments.append((start, end))
            start += bs

        for (start, end) in segments:
            print(f"📦 Procesez segmentul {start}-{end}")
            ok = self.save_page_range(start, end, retries=1)
            if not ok:
                print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc.")
                return False
            time.sleep(1)
        print("🎯 Toate segmentele au fost procesate.")
        return True

    def extract_issue_links_from_collection(self):
        try:
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-group')))
            anchors = self.driver.find_elements(By.CSS_SELECTOR, 'li.list-group-item a[href^="/en/view/"]')
            links = []
            for a in anchors:
                href = a.get_attribute("href")
                if href and '/en/view/' in href:
                    normalized = href.split('?')[0].rstrip('/')
                    links.append(normalized)
            seen = set()
            unique = []
            for l in links:
                if l not in seen:
                    seen.add(l)
                    unique.append(l)
            print(f"🔗 Am găsit {len(unique)} linkuri de issue în colecție.")
            return unique
        except Exception as e:
            print(f"❌ Eroare la extragerea linkurilor din colecție: {e}")
            return []

    def open_new_tab_and_download(self, url):
        normalized_url = url.rstrip('/')
        if normalized_url in SKIP_URLS:
            print(f"⏭️ Sar peste {url} (deja descărcat).")
            return
        if self.remaining_quota() <= 0:
            print(f"⚠ Limita zilnică de {DAILY_LIMIT} PDF-uri atinsă. Oprind procesarea.")
            return

        try:
            print(f"\n📥 Deschid fila pentru {url}")
            # dacă nu e atașat la sesiune existentă, verificăm și facem fallback dacă s-a stricat
            if not self.attached_existing:
                self.ensure_alive_fallback()
            self.driver.execute_script("window.open('');")
            new_handle = self.driver.window_handles[-1]
            self.driver.switch_to.window(new_handle)
            if not self.navigate_to_page(url):
                return
            time.sleep(1)
            if not self.save_all_pages_in_batches():
                print(f"⚠ Descărcarea pentru {url} a întâmpinat probleme.")
            else:
                print(f"✅ Descărcarea pentru {url} finalizată.")
                self._increment_quota()
                print(f"📊 PDF-uri descărcate astăzi: {self.quota['count']}/{DAILY_LIMIT}")
        except WebDriverException as e:
            print(f"❌ Eroare WebDriver pentru {url}: {e}")
        except Exception as e:
            print(f"❌ Eroare în open_new_tab_and_download pentru {url}: {e}")
        finally:
            try:
                self.driver.close()
                if self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

    def ensure_alive_fallback(self):
        """Fallback pentru driver dacă sesiunea nu e atașată (și moare)."""
        try:
            _ = self.driver.title
        except Exception as e:
            print(f"⚠ Conexiune WebDriver moartă ({e}), pornesc instanță nouă ca fallback.")
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
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
        issue_links = self.extract_issue_links_from_collection()
        if not issue_links:
            print("⚠ Nu s-au găsit issue-uri în colecție.")
            return False
        for link in issue_links:
            if self.remaining_quota() <= 0:
                print(f"⚠ Limita zilnică atinsă ({DAILY_LIMIT}), opresc.")
                break
            self.open_new_tab_and_download(link)
            time.sleep(1)
        print("🎯 Toate issue-urile din colecție au fost procesate (sau s-a atins limita).")
        return True

    def run(self):
        print("🧪 Încep executarea Chrome PDF Downloader")
        print("=" * 60)
        try:
            if not self.setup_chrome_driver():
                return False
            if "/collection/" in self.test_url:
                if not self.run_collection(self.test_url):
                    return False
            else:
                if not self.navigate_to_page(self.test_url):
                    return False
                if not self.save_all_pages_in_batches():
                    return False
                self._increment_quota()
                print(f"📊 PDF-uri descărcate astăzi: {self.quota['count']}/{DAILY_LIMIT}")
            print("✅ Toate operațiunile au reușit.")
            return True
        except KeyboardInterrupt:
            print("\n\n⚠ Intervenție manuală: întrerupt.")
            return False
        except Exception as e:
            print(f"\n❌ Eroare neașteptată: {e}")
            return False
        finally:
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
