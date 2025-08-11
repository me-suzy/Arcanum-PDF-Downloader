#!/usr/bin/env python3
"""
MASS FRESH DAY INTERCEPTOR - Maximizează beneficiul zilnic
Strategia: Dimineața când daily limit e resetat, descarcă rapid MULTE documente diferite
pentru a capta cât mai multe URL-uri de bypass
"""

import time
import os
import json
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class MassFreshDayInterceptor:
    def __init__(self, download_dir="D:\\"):
        self.download_dir = download_dir
        self.driver = None
        self.wait = None
        self.captured_urls = {}  # {document_info: [urls]}
        self.monitoring = False
        self.daily_limit_reached = False

    def setup_chrome_monitoring(self):
        """Setup Chrome pentru mass interceptare"""
        try:
            print("🔧 Setup Chrome pentru MASS FRESH DAY INTERCEPTOR...")

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            self.driver.execute_cdp_cmd('Runtime.enable', {})
            self.driver.execute_cdp_cmd('Network.enable', {})

            print("✅ Chrome mass interceptor ACTIVAT")
            return True

        except Exception as e:
            print(f"❌ Setup eșuat: {e}")
            return False

    def get_document_priority_list(self):
        """Lista de documente prioritare pentru captare"""
        documents = [
            {
                "name": "Gazeta Matematică Seria B 1960",
                "url": "https://adt.arcanum.com/ro/view/GazetaMatematicaSiFizicaSeriaB_1960/?pg=0&layout=s",
                "segments": [(1, 50), (51, 100), (101, 150), (151, 200)]
            },
            {
                "name": "Gazeta Matematică Seria B 1961",
                "url": "https://adt.arcanum.com/ro/view/GazetaMatematicaSiFizicaSeriaB_1961/?pg=0&layout=s",
                "segments": [(1, 50), (51, 100), (101, 150)]
            },
            {
                "name": "Gazeta Matematică Seria B 1962",
                "url": "https://adt.arcanum.com/ro/view/GazetaMatematicaSiFizicaSeriaB_1962/?pg=0&layout=s",
                "segments": [(1, 50), (51, 100)]
            }
            # Adaugă mai multe documente după necesitate
        ]
        return documents

    def navigate_to_document(self, doc_info):
        """Navighează la un document specific"""
        try:
            print(f"\n📖 Navighează la: {doc_info['name']}")
            self.driver.get(doc_info['url'])

            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)  # Lasă timpul să se încarce
            print(f"✅ Document încărcat: {doc_info['name']}")
            return True

        except Exception as e:
            print(f"❌ Navigare eșuată pentru {doc_info['name']}: {e}")
            return False

    def attempt_segment_download(self, start_page, end_page):
        """Încearcă să descarce un segment de pagini"""
        try:
            print(f"🎯 Încerc segment {start_page}-{end_page}...")

            # Găsește butonul de salvare
            save_icon = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]')))
            save_button = save_icon.find_element(By.XPATH, "./ancestor::button")
            save_button.click()

            time.sleep(2)

            # Completează input-urile
            first_input = self.wait.until(EC.presence_of_element_located((By.ID, "first page")))
            last_input = self.wait.until(EC.presence_of_element_located((By.ID, "last page")))

            # Șterge și completează
            first_input.clear()
            first_input.send_keys(str(start_page))

            last_input.clear()
            last_input.send_keys(str(end_page))

            time.sleep(1)

            # Apasă Save final
            final_save = self.wait.until(EC.element_to_be_clickable((
                By.XPATH,
                '//button[contains(text(), "Save") or contains(text(), "Salvați")]'
            )))

            final_save.click()
            print(f"✅ Download inițiat pentru {start_page}-{end_page}")

            return True

        except Exception as e:
            print(f"❌ Eroare la download {start_page}-{end_page}: {e}")
            return False

    def monitor_for_urls_and_limit(self, doc_name, timeout_seconds=30):
        """Monitorizează pentru URL-uri și detectează daily limit"""
        print(f"👀 Monitorizez URL-uri pentru {doc_name}...")

        found_urls = []
        start_time = time.time()

        while (time.time() - start_time) < timeout_seconds:
            try:
                logs = self.driver.get_log('performance')

                for log_entry in logs:
                    try:
                        message = json.loads(log_entry['message'])

                        if message['message']['method'] == 'Network.responseReceived':
                            url = message['message']['params']['response']['url']

                            # Detectează URL-uri PDF
                            if ('static-cdn.arcanum.com/downloads/' in url and
                                url.endswith('.pdf') and
                                url not in found_urls):

                                found_urls.append(url)
                                print(f"🎯 URL capturat pentru {doc_name}: {url}")

                            # Detectează daily limit
                            elif 'check-access-save' in url:
                                print(f"⚠️ DAILY LIMIT DETECTAT pentru {doc_name}!")
                                self.daily_limit_reached = True
                                return found_urls

                    except (KeyError, json.JSONDecodeError):
                        continue

                time.sleep(1)

            except Exception as e:
                print(f"⚠️ Eroare monitorizare: {e}")
                time.sleep(1)

        return found_urls

    def run_mass_fresh_day_capture(self):
        """Rulează captura masivă fresh day"""
        print("🌅 MASS FRESH DAY INTERCEPTOR")
        print("=" * 60)
        print("STRATEGIA MAXIMIZĂRII:")
        print("✅ Dimineața când daily limit e resetat")
        print("✅ Descarcă RAPID multe documente diferite")
        print("✅ Captează URL-uri pentru fiecare")
        print("✅ Oprește când daily limit devine activ")
        print("✅ Salvează toate URL-urile pentru bypass")
        print("=" * 60)

        if not self.setup_chrome_monitoring():
            return False

        documents = self.get_document_priority_list()
        total_urls_captured = 0

        for doc_info in documents:
            if self.daily_limit_reached:
                print(f"🛑 Daily limit atins - opresc captura")
                break

            print(f"\n📚 PROCESEZ DOCUMENTUL: {doc_info['name']}")

            if not self.navigate_to_document(doc_info):
                continue

            doc_urls = []

            for start_page, end_page in doc_info['segments']:
                if self.daily_limit_reached:
                    break

                print(f"\n📄 Segment {start_page}-{end_page} din {doc_info['name']}")

                if self.attempt_segment_download(start_page, end_page):
                    # Monitorizează pentru URL-uri
                    segment_urls = self.monitor_for_urls_and_limit(
                        f"{doc_info['name']} ({start_page}-{end_page})",
                        timeout_seconds=45
                    )

                    if segment_urls:
                        doc_urls.extend(segment_urls)
                        total_urls_captured += len(segment_urls)
                        print(f"✅ {len(segment_urls)} URL-uri capturate pentru segment")

                    # Pauză între segmente
                    if not self.daily_limit_reached:
                        time.sleep(5)
                else:
                    print(f"⚠️ Nu am putut descărca segmentul {start_page}-{end_page}")

            if doc_urls:
                self.captured_urls[doc_info['name']] = doc_urls
                print(f"📊 Total pentru {doc_info['name']}: {len(doc_urls)} URL-uri")

        # Sumarizează rezultatele
        print(f"\n🎉 CAPTURA MASIVĂ COMPLETĂ!")
        print(f"📊 Total URL-uri capturate: {total_urls_captured}")
        print(f"📚 Documente procesate: {len(self.captured_urls)}")

        for doc_name, urls in self.captured_urls.items():
            print(f"   📖 {doc_name}: {len(urls)} URL-uri")

        # Salvează toate URL-urile
        self.save_mass_urls_to_file()

        # Testează câteva URL-uri random
        self.test_random_urls()

        return len(self.captured_urls) > 0

    def save_mass_urls_to_file(self):
        """Salvează toate URL-urile capturate"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"mass_fresh_urls_{timestamp}.json"
            filepath = os.path.join(self.download_dir, filename)

            # Salvează ca JSON pentru structură
            data = {
                "timestamp": timestamp,
                "total_documents": len(self.captured_urls),
                "total_urls": sum(len(urls) for urls in self.captured_urls.values()),
                "daily_limit_reached": self.daily_limit_reached,
                "documents": self.captured_urls
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Mass URLs salvate în: {filename}")

            # Salvează și ca text pentru referință rapidă
            txt_filename = f"mass_fresh_urls_{timestamp}.txt"
            txt_filepath = os.path.join(self.download_dir, txt_filename)

            with open(txt_filepath, 'w', encoding='utf-8') as f:
                f.write(f"Mass Fresh Day URLs - {timestamp}\n")
                f.write(f"{'='*50}\n\n")

                for doc_name, urls in self.captured_urls.items():
                    f.write(f"{doc_name}:\n")
                    for i, url in enumerate(urls, 1):
                        f.write(f"  {i}. {url}\n")
                    f.write(f"\n")

            print(f"💾 Text URLs salvate în: {txt_filename}")

        except Exception as e:
            print(f"⚠️ Nu am putut salva mass URLs: {e}")

    def test_random_urls(self, max_tests=3):
        """Testează câteva URL-uri random pentru validare"""
        print(f"\n🧪 Testez {max_tests} URL-uri random pentru validare...")

        all_urls = []
        for doc_name, urls in self.captured_urls.items():
            for url in urls:
                all_urls.append((doc_name, url))

        if not all_urls:
            print("❌ Nu există URL-uri de testat")
            return

        import random
        test_urls = random.sample(all_urls, min(max_tests, len(all_urls)))

        for i, (doc_name, url) in enumerate(test_urls, 1):
            print(f"\n🧪 Test {i}/{len(test_urls)}: {doc_name}")
            self.test_direct_download(url, f"_mass_test_{i}")

    def test_direct_download(self, static_url, suffix=""):
        """Testează descărcarea directă"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*',
                'Referer': 'https://adt.arcanum.com/',
            }

            head_response = requests.head(static_url, headers=headers, timeout=10)

            if head_response.status_code == 200:
                content_length = int(head_response.headers.get('content-length', 0))
                print(f"✅ URL valid - Size: {content_length/1024/1024:.2f} MB")

                # Download mic pentru test
                response = requests.get(static_url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()

                filename = f"mass_test{suffix}_{int(time.time())}.pdf"
                filepath = os.path.join(self.download_dir, filename)

                # Salvează doar primii câteva MB pentru test
                total_size = 0
                max_size = 5 * 1024 * 1024  # 5 MB max pentru test

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk and total_size < max_size:
                            f.write(chunk)
                            total_size += len(chunk)
                        else:
                            break

                file_size_mb = total_size / (1024 * 1024)
                print(f"✅ Test reușit: {filename} ({file_size_mb:.2f} MB)")
                return True
            else:
                print(f"❌ URL invalid - Status: {head_response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Test eșuat: {e}")
            return False

def main():
    """Funcția principală pentru mass fresh day"""
    print("🌅 MASS FRESH DAY INTERCEPTOR - Maximizează beneficiul")
    print("=" * 60)
    print("REALITATEA BYPASS-ULUI:")
    print("✅ Funcționează doar pentru documente capturate dimineața")
    print("❌ NU generează URL-uri pentru documente noi după daily limit")
    print("💡 SOLUȚIA: Captează URL-uri pentru MULTE documente dimineața!")
    print("=" * 60)
    print("STRATEGIA MASS CAPTURE:")
    print("✅ Dimineața: Descarcă segmente din MULTE documente")
    print("✅ Captează URL-uri pentru fiecare document")
    print("✅ Oprește când daily limit devine activ")
    print("✅ Salvează toate URL-urile pentru bypass")
    print("✅ Toată ziua: Folosește URL-urile pentru orice segment")
    print("=" * 60)

    input("Apasă ENTER când Chrome cu debugging este pregătit și daily limit e resetat...")

    interceptor = MassFreshDayInterceptor(download_dir="D:\\")

    success = interceptor.run_mass_fresh_day_capture()

    if success:
        print(f"\n🎉 MASS FRESH DAY CAPTURE REUȘIT!")
        print(f"✅ Ai URL-uri pentru multiple documente!")
        print(f"✅ Folosește-le toată ziua pentru bypass!")
    else:
        print(f"\n❌ MASS CAPTURE INCOMPLET")
        print(f"💡 Încearcă mâine dimineața")

    input("\nApasă ENTER pentru a închide...")

if __name__ == "__main__":
    main()