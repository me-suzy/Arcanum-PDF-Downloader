#!/usr/bin/env python3
"""
FRESH DAY INTERCEPTOR - Pentru când daily limit se resetează
Strategia: Rulează IMEDIAT după ce daily limit se resetează (în fiecare zi la miezul nopții)
"""

import time
import os
import json
import requests
import threading
import queue
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

class FreshDayInterceptor:
    def __init__(self, download_dir="D:\\"):
        self.download_dir = download_dir
        self.driver = None
        self.wait = None
        self.captured_urls = []
        self.monitoring = False

    def setup_chrome_monitoring(self):
        """Setup Chrome pentru interceptare fresh day"""
        try:
            print("🔧 Setup Chrome pentru FRESH DAY INTERCEPTOR...")

            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 30)

            # Activează CDP
            self.driver.execute_cdp_cmd('Runtime.enable', {})
            self.driver.execute_cdp_cmd('Network.enable', {})

            print("✅ Chrome fresh day interceptor ACTIVAT")
            return True

        except Exception as e:
            print(f"❌ Setup eșuat: {e}")
            return False

    def check_daily_limit_status(self):
        """Verifică dacă daily limit este activ sau resetat"""
        try:
            print("🔍 Verific starea daily limit...")

            # Încearcă o descărcare test pentru a vedea dacă daily limit e activ
            current_url = self.driver.current_url

            # Simulează click pe Save pentru test
            try:
                save_button = self.driver.find_element(By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]')
                parent_button = save_button.find_element(By.XPATH, "./ancestor::button")
                parent_button.click()

                time.sleep(2)

                # Verifică dacă s-a deschis popup-ul sau direct daily limit
                current_tabs = self.driver.window_handles

                for tab in current_tabs:
                    self.driver.switch_to.window(tab)
                    tab_url = self.driver.current_url

                    if 'check-access-save' in tab_url:
                        print("❌ Daily limit încă ACTIV")
                        return False

                # Dacă nu s-a deschis tab de daily limit, înseamnă că e resetat
                print("✅ Daily limit RESETAT - gata pentru interceptare!")
                return True

            except Exception:
                print("⚠️ Nu pot testa direct - presupun că daily limit e resetat")
                return True

        except Exception as e:
            print(f"⚠️ Eroare la verificarea daily limit: {e}")
            return True

    def navigate_to_issue(self, issue_url):
        """Navighează la issue"""
        try:
            print(f"🌐 Navighează la: {issue_url}")
            self.driver.get(issue_url)

            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✅ Issue încărcat")
            return True

        except Exception as e:
            print(f"❌ Navigare eșuată: {e}")
            return False

    def start_fresh_day_monitoring(self):
        """Pornește monitorizarea pentru fresh day"""
        print("\n🌅 FRESH DAY INTERCEPTOR ACTIVAT!")
        print("=" * 60)
        print("📝 INSTRUCȚIUNI PENTRU ZIUA NOUĂ:")
        print("1. 🌅 Daily limit a fost resetat!")
        print("2. 🚀 EXECUTĂ RAPID prima descărcare (Save -> pagini -> Save)")
        print("3. 👀 EU voi capta URL-urile PDF generate")
        print("4. 💾 Voi testa imediat bypass-ul")
        print("5. 🎯 Acestea vor fi URL-urile pentru toată ziua!")
        print("=" * 60)
        print("⚡ ÎNCEPE DESCĂRCAREA ACUM - EU MONITORIZEZ!")

        self.monitoring = True
        captured_count = 0
        seconds_elapsed = 0

        while self.monitoring and seconds_elapsed < 300:  # 5 minute max
            try:
                # Verifică performance logs
                logs = self.driver.get_log('performance')

                for log_entry in logs:
                    try:
                        message = json.loads(log_entry['message'])

                        if message['message']['method'] == 'Network.responseReceived':
                            url = message['message']['params']['response']['url']

                            # Caută URL-uri PDF directe
                            if ('static-cdn.arcanum.com/downloads/' in url and
                                url.endswith('.pdf') and
                                url not in self.captured_urls):

                                self.captured_urls.append(url)
                                captured_count += 1

                                print(f"\n🎯 FRESH DAY URL CAPTURAT #{captured_count}: {url}")
                                print(f"🎉 ACESTA VA FI URL-ul pentru BYPASS!")

                                # Testează imediat
                                if self.test_direct_download(url, f"_fresh_day_{captured_count}"):
                                    print(f"🌅 FRESH DAY BYPASS REUȘIT!")
                                    print(f"✅ Ai acum URL-ul pentru toată ziua!")

                                    # Salvează URL-ul într-un fișier pentru referință
                                    self.save_fresh_url_to_file(url)
                                    return True

                            # Detectează dacă apare din nou daily limit
                            elif 'check-access-save' in url:
                                print(f"\n⚠️ Daily limit a apărut din nou după {captured_count} URL-uri")
                                if self.captured_urls:
                                    print(f"✅ Dar am capturat {len(self.captured_urls)} URL-uri valide!")
                                    return True

                    except (KeyError, json.JSONDecodeError):
                        continue

                # Progress indicator
                if seconds_elapsed % 15 == 0:
                    minutes = seconds_elapsed // 60
                    seconds = seconds_elapsed % 60
                    print(f"⏳ {minutes:02d}:{seconds:02d} | Fresh day URL-uri: {captured_count}")

                time.sleep(1)
                seconds_elapsed += 1

            except Exception as e:
                print(f"⚠️ Eroare monitorizare fresh day: {e}")
                time.sleep(1)
                seconds_elapsed += 1

        # Sumarizează rezultatele
        print(f"\n📊 REZULTATE FRESH DAY:")
        if self.captured_urls:
            print(f"✅ {len(self.captured_urls)} fresh URL-uri capturate:")
            for i, url in enumerate(self.captured_urls, 1):
                print(f"   {i}. {url}")

            self.save_all_urls_to_file()
            return True
        else:
            print(f"❌ Nu s-au capturat fresh URL-uri")
            return False

    def test_direct_download(self, static_url, suffix=""):
        """Testează descărcarea directă"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*',
                'Referer': 'https://adt.arcanum.com/',
            }

            # Test cu HEAD request
            head_response = requests.head(static_url, headers=headers, timeout=10)

            if head_response.status_code == 200:
                content_length = int(head_response.headers.get('content-length', 0))
                print(f"✅ Fresh URL valid - Size: {content_length/1024/1024:.2f} MB")

                # Download efectiv
                response = requests.get(static_url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()

                filename = f"fresh_day_bypass{suffix}_{int(time.time())}.pdf"
                filepath = os.path.join(self.download_dir, filename)

                total_size = 0
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)

                file_size_mb = total_size / (1024 * 1024)
                print(f"🎉 FRESH DAY DESCĂRCARE REUȘITĂ!")
                print(f"   📄 Fișier: {filename}")
                print(f"   📊 Dimensiune: {file_size_mb:.2f} MB")
                print(f"   📁 Locație: {filepath}")

                return True
            else:
                print(f"❌ Fresh URL invalid - Status: {head_response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Test fresh descărcare eșuat: {e}")
            return False

    def save_fresh_url_to_file(self, url):
        """Salvează URL-ul fresh într-un fișier pentru referință"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"fresh_day_urls_{timestamp}.txt"
            filepath = os.path.join(self.download_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Fresh Day URL captat la: {timestamp}\n")
                f.write(f"URL: {url}\n")
                f.write(f"Folosește acest URL pentru bypass-ul de azi!\n")

            print(f"💾 Fresh URL salvat în: {filename}")

        except Exception as e:
            print(f"⚠️ Nu am putut salva fresh URL-ul: {e}")

    def save_all_urls_to_file(self):
        """Salvează toate URL-urile într-un fișier"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"all_fresh_urls_{timestamp}.txt"
            filepath = os.path.join(self.download_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Fresh Day URLs capturate la: {timestamp}\n")
                f.write(f"Total URL-uri: {len(self.captured_urls)}\n\n")

                for i, url in enumerate(self.captured_urls, 1):
                    f.write(f"{i}. {url}\n")

                f.write(f"\nFolosește aceste URL-uri pentru bypass!\n")

            print(f"💾 Toate fresh URL-urile salvate în: {filename}")

        except Exception as e:
            print(f"⚠️ Nu am putut salva toate URL-urile: {e}")

    def run_fresh_day_test(self, issue_url):
        """Rulează testul complet fresh day"""
        print("🌅 FRESH DAY INTERCEPTOR - Pentru daily limit resetat")
        print("=" * 70)
        print("STRATEGIA FRESH DAY:")
        print("✅ Daily limit se resetează în fiecare zi la miezul nopții")
        print("✅ Prima descărcare generează URL-uri PDF valide")
        print("✅ Acestea rămân active chiar după ce apare din nou daily limit")
        print("✅ Un fresh URL poate fi folosit pentru mai multe descărcări")
        print("=" * 70)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"⏰ Ora curentă: {current_time}")

        try:
            # 1. Setup
            if not self.setup_chrome_monitoring():
                return False

            # 2. Navighează la issue
            if not self.navigate_to_issue(issue_url):
                return False

            # 3. Verifică daily limit status
            if not self.check_daily_limit_status():
                print("❌ Daily limit încă activ - încearcă mâine dimineața!")
                print("💡 Programează acest script să ruleze automat la 00:01")
                return False

            # 4. Pornește interceptarea fresh day
            success = self.start_fresh_day_monitoring()

            return success

        except Exception as e:
            print(f"❌ EROARE FRESH DAY: {e}")
            return False

        finally:
            self.monitoring = False

def main():
    """Funcția principală pentru fresh day interceptor"""
    print("🌅 FRESH DAY INTERCEPTOR - Soluția DEFINITIVĂ")
    print("=" * 60)
    print("REALITATEA IDENTIFICATĂ:")
    print("❌ Daily limit este ACTIV - nu se generează URL-uri noi")
    print("✅ Dar daily limit se RESETEAZĂ în fiecare zi!")
    print("✅ Prima descărcare după reset generează URL-uri valide")
    print("✅ Acestea funcționează chiar după ce limit-ul revine")
    print("=" * 60)
    print("ACEASTĂ STRATEGIE:")
    print("✅ Rulează când daily limit este resetat")
    print("✅ Captează prima șansă de URL-uri")
    print("✅ Salvează URL-urile pentru referință")
    print("✅ Testează imediat bypass-ul")
    print("=" * 60)
    print("CÂND SĂ RULEZI:")
    print("🌅 Dimineața devreme (după 00:01)")
    print("🌅 Sau când știi că daily limit s-a resetat")
    print("🌅 Ideally: programează automat la miezul nopții")
    print("=" * 60)

    input("Apasă ENTER când Chrome cu debugging este pregătit și daily limit e resetat...")

    # URL de test
    issue_url = input("URL issue (ENTER pentru default): ").strip()
    if not issue_url:
        issue_url = "https://adt.arcanum.com/ro/view/GazetaMatematicaSiFizicaSeriaB_1960/?pg=0&layout=s"

    # Creează fresh day interceptorul
    interceptor = FreshDayInterceptor(download_dir="D:\\")

    # Rulează testul
    success = interceptor.run_fresh_day_test(issue_url)

    if success:
        print(f"\n🎉 FRESH DAY INTERCEPTOR REUȘIT!")
        print(f"✅ Am capturat fresh URL-uri pentru toată ziua!")
        print(f"✅ Poți folosi aceste URL-uri pentru bypass nelimitat!")
        print(f"🚀 Integrează strategia în codul principal!")
    else:
        print(f"\n⚠️ FRESH DAY INTERCEPTOR INCOMPLET")
        print(f"💡 Încearcă mâine dimineața când daily limit se resetează")
        print(f"💡 Sau programează scriptul să ruleze automat la 00:01")

    input("\nApasă ENTER pentru a închide...")

if __name__ == "__main__":
    main()