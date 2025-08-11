#!/usr/bin/env python3
"""
Script pentru descărcarea paginilor din PDF folosind Chrome + Selenium,
împărțind în batch-uri (ex: 1-50, 51-96) pe baza numărului total de pagini detectat automat.
Include delay-uri vizibile și apăsare Ctrl+A pentru suprascrierea inputurilor.
"""

import time
import os
import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
    ElementClickInterceptedException,
)

class ChromePDFDownloader:
    def __init__(self, test_url, download_dir=None, batch_size=50, timeout=15):
        self.test_url = test_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.download_dir = download_dir or os.getcwd()
        self.driver = None
        self.wait = None

    def setup_chrome_driver(self):
        """Configurează și, dacă se poate, se conectează la Chrome deja pornit cu remote debugging; altfel deschide unul nou."""
        try:
            print("🔧 Inițializare WebDriver – încerc conectare la Chrome existent via remote debugging...")
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")  # se conectează la instanța deja deschisă

            # Dacă se conectează, nu e nevoie de prefs (downloads sunt ale sesiunii existente), dar le poți seta ca fallback
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            # Nu adăugăm incognito aici, că vrem să reutilizăm sesiunea existentă

            try:
                # Încearcă conectarea la Chrome deja deschis
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, self.timeout)
                print("✅ Conectat la instanța Chrome existentă cu succes.")
                return True
            except WebDriverException as e:
                print(f"⚠ Nu s-a putut conecta la Chrome existent (fallback la pornire nouă): {e}")
                # fallback: pornește o instanță nouă
                chrome_options = Options()
                chrome_options.add_experimental_option("prefs", prefs)
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--window-size=1920,1080")
                chrome_options.add_argument("--incognito")
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, self.timeout)
                print("✅ Chrome nou pornit cu succes.")
                return True
        except WebDriverException as e:
            print(f"❌ Eroare la inițializarea WebDriver-ului: {e}")
            return False


    def navigate_to_page(self):
        try:
            print(f"🌐 Navighez către: {self.test_url}")
            self.driver.get(self.test_url)
            self.wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                'div.MuiInputAdornment-root.MuiInputAdornment-positionEnd'
            )))
            print("✅ Pagina încărcată.")
            return True
        except Exception as e:
            print(f"❌ Eroare la navigare sau încărcare: {e}")
            return False

    def get_total_pages(self, max_attempts=5, delay_between=1.0):
        """Extrage numărul total de pagini din elementul de tip '/ 96', cu fallback-uri și retry."""
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
        """Dă click pe butonul de salvare pentru a deschide popup-ul, cu retry dacă e interceptat sau blocat."""
        try:
            # Așteaptă să dispară eventuale dialoguri vechi
            try:
                self.wait.until(EC.invisibility_of_element_located((
                    By.CSS_SELECTOR, 'div.MuiDialog-container'
                )), message="Aștept dispariția dialogurilor vechi")
            except Exception:
                # fallback: încearcă să închid cu ESC
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                time.sleep(0.5)

            svg = self.wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]'
            )))
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
        """Completează popup-ul cu intervalul și apasă butonul de salvare (Salvați/Save), cu delay-uri și suprascriere prin Ctrl+A."""
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

            # XPath combinat pentru "Salvați" sau "Save"
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
        """Flux complet pentru un segment: deschide popup + completează + salvează, cu retry."""
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

        # primul segment: 1 .. bs-1 (dacă total >=1)
        if total >= 1:
            first_end = min(bs - 1, total)
            if first_end >= 1:
                segments.append((1, first_end))

        # segmentele următoare în trepte de bs, începând de la bs
        start = bs
        while start <= total:
            end = min(start + bs - 1, total)
            segments.append((start, end))
            start += bs

        # Execută fiecare segment
        for (start, end) in segments:
            print(f"📦 Procesez segmentul {start}-{end}")
            ok = self.save_page_range(start, end, retries=1)
            if not ok:
                print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc.")
                return False
            time.sleep(1)  # pauză între segmente

        print("🎯 Toate segmentele au fost procesate.")
        return True


    def run(self):
        print("🧪 Încep testul Chrome PDF Downloader")
        print("=" * 60)
        try:
            if not self.setup_chrome_driver():
                return False
            if not self.navigate_to_page():
                return False

            time.sleep(1)

            if not self.save_all_pages_in_batches():
                return False

            print("✅ Toate operațiunile au reușit.")
            return True
        except KeyboardInterrupt:
            print("\n\n⚠ Test întrerupt de utilizator")
            return False
        except Exception as e:
            print(f"\n❌ Eroare neașteptată: {e}")
            return False
        finally:
            if self.driver:
                print("🚪 Închid browserul.")
                try:
                    self.driver.quit()
                except Exception:
                    pass

def main():
    test_url = "https://adt.arcanum.com/ro/view/Convietuirea_1997-1/"
    if len(sys.argv) >= 2:
        test_url = sys.argv[1]
    downloader = ChromePDFDownloader(test_url=test_url, download_dir="D:\\", batch_size=50)
    return downloader.run()

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")
        sys.exit(1)
