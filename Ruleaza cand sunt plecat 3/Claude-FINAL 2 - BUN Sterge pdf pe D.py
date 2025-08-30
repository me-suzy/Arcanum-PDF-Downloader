#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum (FIXED VERSION cu SORTARE CRONOLOGICĂ):
- FIXED: Scanează corect toate fișierele existente de pe disk
- FIXED: Păstrează progresul parțial între zile
- FIXED: Procesează și combină corect TOATE PDF-urile pentru fiecare issue
- FIXED: Resume logic corect pentru issue-urile parțiale
- FIXED: Detectează corect prefix-urile pentru fișiere
- FIXED: Verifică corect issue-urile complete pentru skip URLs
- FIXED: Elimină dublurile automat
- FIXED: Detectează mai bine numărul total de pagini
- FIXED: Sortare cronologică corectă în downloaded_issues
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

import logging
import sys

def setup_logging():
    """Configurează logging în timp real"""
    log_dir = r"E:\Carte\BB\17 - Site Leadership\alte\Ionel Balauta\Aryeht\Task 1 - Traduce tot site-ul\Doar Google Web\Andreea\Meditatii\2023\++Arcanum Download + Chrome\Ruleaza cand sunt plecat 3\Logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"arcanum_download_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler):
            handler.stream.reconfigure(line_buffering=True)

    print(f"📝 LOGGING ACTIVAT: {log_file}")
    return log_file

# Colecțiile adiționale (procesate DUPĂ colecția principală din main())
ADDITIONAL_COLLECTIONS = [
    "https://adt.arcanum.com/ro/collection/Convietuirea/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMecanicaSiAplicata/",
    "https://adt.arcanum.com/ro/collection/CalitateFiabilitat/",
    "https://adt.arcanum.com/ro/collection/Metrologie/",
    "https://adt.arcanum.com/ro/collection/MetrologiaAplicata/",
    "https://adt.arcanum.com/ro/collection/AnaleleUnivBucuresti_GeologieGeografie/",
    "https://adt.arcanum.com/ro/collection/BuletinulStiintificTechnicInstitutuluiPolitehnicTimisoara_MatematicaFizicaMecanica/",
    "https://adt.arcanum.com/ro/collection/AlmanahAteneu/",
    "https://adt.arcanum.com/hu/collection/AMatematikaTanitasa/",
    "https://adt.arcanum.com/hu/collection/AFizikaTanitasa/",
    "https://adt.arcanum.com/hu/collection/AKemiaTanitasa/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMatematice/",
    "https://adt.arcanum.com/ro/collection/AnaleleUnivBucuresti_MatematicaMecanicaFizica/",
    "https://adt.arcanum.com/ro/collection/RevistaMatematicaDinTimisoara/",
    "https://adt.arcanum.com/ro/collection/BuletInstPolitehIasi_1/",
    "https://adt.arcanum.com/ro/collection/Energetica/",
    "https://adt.arcanum.com/ro/collection/CulturaFizicaSiSport/",
    "https://adt.arcanum.com/ro/collection/Almanahul_Satelor/",
    "https://adt.arcanum.com/ro/collection/SteauaRomaniei/",
    "https://adt.arcanum.com/ro/collection/RevistaDeFolclor/",
    "https://adt.arcanum.com/ro/collection/AlmanahBTT/",
    "https://adt.arcanum.com/ro/collection/MinePetrolGaze/",
    "https://adt.arcanum.com/ro/collection/BuletinulInstitutuluiPolitehnicBucuresti_Mecanica/",
    "https://adt.arcanum.com/ro/collection/RevistaMinelor/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariDeGeologie/",
    "https://adt.arcanum.com/ro/collection/RevistaIndustriaAlimentare/",
    "https://adt.arcanum.com/ro/collection/IndustriaLemnului/",
    "https://adt.arcanum.com/ro/collection/Electricitatea/",
    "https://adt.arcanum.com/ro/collection/SzatmariMuzeumKiadvanyai_Evkonyv_ADT/",
    "https://adt.arcanum.com/ro/collection/ConstructiaDeMasini/",
    "https://adt.arcanum.com/ro/collection/SufletNou/",
    "https://adt.arcanum.com/ro/collection/Rondul/",
    "https://adt.arcanum.com/ro/collection/RomaniaMilitara/",
    "https://adt.arcanum.com/ro/collection/Magazin/",
    "https://adt.arcanum.com/ro/collection/TribunaSibiului/",
    "https://adt.arcanum.com/ro/collection/Metalurgia/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariDeMetalurgie/",
    "https://adt.arcanum.com/ro/collection/BuletinulInstitutuluiPolitehnicBucuresti_ChimieMetalurgie/",
    "https://adt.arcanum.com/ro/collection/RomaniaMuncitoare/",
    "https://adt.arcanum.com/ro/collection/Cronica/",
    "https://adt.arcanum.com/ro/collection/Marisia_ADT/",
    "https://adt.arcanum.com/ro/collection/RevistaDeEtnografieSiFolclor/",
    "https://adt.arcanum.com/ro/collection/RevistaMuzeelor/",
    "https://adt.arcanum.com/ro/collection/GazetaDeDuminica/",
    "https://adt.arcanum.com/ro/collection/BuletInstPolitehIasi_0/",
    "https://adt.arcanum.com/ro/collection/JurnalulNational/",
    "https://adt.arcanum.com/ro/collection/UnireaBlajPoporului/",
    "https://adt.arcanum.com/ro/collection/TranssylvaniaNostra/",
    "https://adt.arcanum.com/ro/collection/CuvantulPoporului/",
    "https://adt.arcanum.com/ro/collection/Agrarul/",
    "https://adt.arcanum.com/ro/collection/Radiofonia/",
    "https://adt.arcanum.com/ro/collection/CurierulDeIasi/",
    "https://adt.arcanum.com/ro/collection/CurierulFoaiaIntereselorGenerale/",
    "https://adt.arcanum.com/ro/collection/EconomiaNationala/",
    "https://adt.arcanum.com/ro/collection/Constitutionalul/",
    "https://adt.arcanum.com/ro/collection/Semnalul/",
    "https://adt.arcanum.com/ro/collection/Rampa/",
    "https://adt.arcanum.com/ro/collection/ViataRomaneasca/",
    "https://adt.arcanum.com/ro/collection/SteauaRosie/",
    "https://adt.arcanum.com/ro/collection/Almanah_ScinteiaTineretului/",
    "https://adt.arcanum.com/ro/collection/EvenimentulZilei/",
    "https://adt.arcanum.com/ro/collection/CurierulFoaiaIntereselorGenerale/",
    "https://adt.arcanum.com/hu/collection/IdegenNyelvekTanitasa/",
    "https://adt.arcanum.com/hu/collection/AzEnekZeneTanitasa/",
    "https://adt.arcanum.com/hu/collection/ABiologiaTanitasa/",
    "https://adt.arcanum.com/hu/collection/ErtekezesekEmlekezesek/",
    "https://adt.arcanum.com/hu/collection/Books_SorozatonKivul/",
    "https://adt.arcanum.com/hu/collection/Books_22_OrvoslasTermeszetrajz/",
    "https://adt.arcanum.com/hu/collection/DomolkiKonyvek/"
]

# Skip URLs statice (hardcoded)
STATIC_SKIP_URLS = {
    "https://adt.arcanum.com/ro/view/Convietuirea_1997-1998"
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
        self.fix_existing_json()

    def _load_skip_urls(self):
        """Încarcă skip URLs din fișierul separat"""
        self.dynamic_skip_urls = set(STATIC_SKIP_URLS)  # Începe cu cele statice

        if os.path.exists(self.skip_urls_path):
            try:
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    completed_urls = data.get("completed_urls", [])
                    completed_collections = data.get("completed_collections", [])

                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_urls)
                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_collections)

                    print(f"📋 Încărcat {len(completed_urls)} URL-uri complet descărcate din {SKIP_URLS_FILENAME}")
                    print(f"📋 Încărcat {len(completed_collections)} colecții complet procesate din {SKIP_URLS_FILENAME}")
            except Exception as e:
                print(f"⚠ Eroare la citirea {SKIP_URLS_FILENAME}: {e}")

        print(f"🚫 Total URL-uri de skip: {len(self.dynamic_skip_urls)}")

    def _save_skip_urls(self):
        """FIXED: Verifică corect dacă un issue este complet - FOLOSEȘTE last_successful_segment_end!"""
        try:
            completed_urls = []
            for item in self.state.get("downloaded_issues", []):
                # VERIFICARE CORECTĂ: folosește last_successful_segment_end, NU pages!
                completed_at = item.get("completed_at")
                total_pages = item.get("total_pages")
                last_segment = item.get("last_successful_segment_end", 0)
                pages = item.get("pages", 0)  # Pentru debug

                # CONDIȚIE FIXATĂ: verifică progresul REAL (last_segment), nu pages!
                if (completed_at and  # Marcat ca terminat
                    total_pages and  # Are total_pages setat
                    total_pages > 0 and  # Total valid
                    last_segment >= total_pages):  # Progresul REAL este complet

                    completed_urls.append(item["url"])
                    print(f"✅ Issue complet pentru skip: {item['url']} ({last_segment}/{total_pages})")

                    # DEBUG: Afișează discrepanțele
                    if pages != last_segment:
                        print(f"   ⚠ DISCREPANȚĂ: pages={pages}, last_segment={last_segment}")
                else:
                    # DEBUG: Afișează de ce nu e considerat complet
                    if item.get("url"):  # Doar dacă are URL valid
                        print(f"🔄 Issue incomplet: {item.get('url', 'NO_URL')}")
                        print(f"   completed_at: {bool(completed_at)}")
                        print(f"   total_pages: {total_pages}")
                        print(f"   last_segment: {last_segment}")
                        print(f"   pages: {pages}")

                        # Verifică fiecare condiție individual
                        if not completed_at:
                            print(f"   → Lipsește completed_at")
                        elif not total_pages or total_pages <= 0:
                            print(f"   → total_pages invalid")
                        elif last_segment < total_pages:
                            print(f"   → Progres incomplet: {last_segment}/{total_pages}")

            # Adaugă și cele statice
            all_completed = list(STATIC_SKIP_URLS) + completed_urls

            # Păstrează și colecțiile complete dacă există
            existing_data = {}
            if os.path.exists(self.skip_urls_path):
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            data = {
                "last_updated": datetime.now().isoformat(),
                "completed_urls": sorted(list(set(all_completed))),
                "completed_collections": existing_data.get("completed_collections", [])
            }

            with open(self.skip_urls_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Salvat {len(data['completed_urls'])} URL-uri CORECT VERIFICATE în {SKIP_URLS_FILENAME}")

            # RAPORT FINAL pentru debugging
            print(f"📋 ISSUES COMPLETE în skip_urls:")
            for url in sorted(completed_urls):
                year = url.split('_')[-1] if '_' in url else 'UNKNOWN'
                print(f"   ✅ {year}")

        except Exception as e:
            print(f"⚠ Eroare la salvarea {SKIP_URLS_FILENAME}: {e}")

    def _safe_folder_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _decode_unicode_escapes(self, obj):
        """Decodifică secvențele unicode din JSON"""
        if isinstance(obj, dict):
            return {key: self._decode_unicode_escapes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._decode_unicode_escapes(item) for item in obj]
        elif isinstance(obj, str):
            # Decodifică secvențele unicode ca \u0103, \u0219
            try:
                return obj.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') if '\\u' in obj else obj
            except:
                return obj
        else:
            return obj

    def is_issue_complete_by_end_page(self, end_page):
        """Determină dacă un issue e complet pe baza ultimei pagini"""
        return not ((end_page + 1) % 50 == 0 or (end_page + 1) % 100 == 0)

    def extract_issue_id_from_filename(self, filename):
        """FIXED: Extrage ID-ul issue-ului din numele fișierului (fără timestamp)"""
        # Caută pattern-ul: PrefixIssue-TIMESTAMP__pages
        match = re.search(r'([^-]+(?:-[^-]+)*)-\d+__pages', filename)
        if match:
            return match.group(1)
        return None

    def extract_issue_url_from_filename(self, filename):
        """FIXED: Extrage URL-ul issue-ului din numele fișierului"""
        issue_id = self.extract_issue_id_from_filename(filename)
        if not issue_id:
            return None

        if "Convietuirea" in issue_id:
            return f"https://adt.arcanum.com/ro/view/{issue_id}"
        elif "GazetaMatematica" in issue_id:
            return f"https://adt.arcanum.com/en/view/{issue_id}"
        else:
            return f"https://adt.arcanum.com/ro/view/{issue_id}"

    def get_all_pdf_segments_for_issue(self, issue_url):
        """FIXED: Scanează toate fișierele PDF pentru un issue specific"""
        issue_id = issue_url.rstrip('/').split('/')[-1]
        segments = []

        try:
            for filename in os.listdir(self.download_dir):
                if not filename.lower().endswith('.pdf'):
                    continue

                file_issue_id = self.extract_issue_id_from_filename(filename)
                if file_issue_id == issue_id:
                    # Extrage intervalul de pagini
                    match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        start_page = int(match.group(1))
                        end_page = int(match.group(2))
                        segments.append({
                            'filename': filename,
                            'start': start_page,
                            'end': end_page,
                            'path': os.path.join(self.download_dir, filename)
                        })

        except Exception as e:
            print(f"⚠ Eroare la scanarea fișierelor pentru {issue_url}: {e}")

        # Sortează după pagina de început
        segments.sort(key=lambda x: x['start'])
        return segments

    def get_existing_pdf_segments(self, issue_url):
        """FIXED: Scanează toate segmentele existente și returnează ultima pagină"""
        segments = self.get_all_pdf_segments_for_issue(issue_url)

        if not segments:
            return 0

        # Găsește cea mai mare pagină finală
        max_page = max(seg['end'] for seg in segments)

        print(f"📊 Fișiere PDF existente pentru {issue_url}:")
        for seg in segments:
            print(f"   📄 {seg['filename']} (pagini {seg['start']}-{seg['end']})")

        return max_page

    def reconstruct_all_issues_from_disk(self):
        """FIXED: Reconstruiește complet progresul din fișierele de pe disk"""
        print("🔍 SCANEZ COMPLET toate fișierele PDF de pe disk...")

        # Grupează fișierele după issue ID
        issues_on_disk = {}

        try:
            for filename in os.listdir(self.download_dir):
                if not filename.lower().endswith('.pdf'):
                    continue

                issue_id = self.extract_issue_id_from_filename(filename)
                if not issue_id:
                    continue

                # Extrage intervalul de pagini
                match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                if not match:
                    continue

                start_page = int(match.group(1))
                end_page = int(match.group(2))

                if issue_id not in issues_on_disk:
                    issues_on_disk[issue_id] = {
                        'segments': [],
                        'max_page': 0,
                        'url': self.extract_issue_url_from_filename(filename)
                    }

                issues_on_disk[issue_id]['segments'].append({
                    'filename': filename,
                    'start': start_page,
                    'end': end_page
                })

                if end_page > issues_on_disk[issue_id]['max_page']:
                    issues_on_disk[issue_id]['max_page'] = end_page

        except Exception as e:
            print(f"⚠ Eroare la scanarea disk-ului: {e}")
            return {}

        # Afișează rezultatele scanării
        print(f"📊 Găsite {len(issues_on_disk)} issue-uri pe disk:")
        for issue_id, data in issues_on_disk.items():
            segments_count = len(data['segments'])
            max_page = data['max_page']
            url = data['url']

            print(f"   📁 {issue_id}: {segments_count} segmente, max pagina {max_page}")
            print(f"      🔗 URL: {url}")

            # Afișează segmentele sortate
            data['segments'].sort(key=lambda x: x['start'])
            for seg in data['segments'][:3]:  # Primele 3
                print(f"      📄 {seg['filename']} ({seg['start']}-{seg['end']})")
            if segments_count > 3:
                print(f"      📄 ... și încă {segments_count - 3} segmente")

        return issues_on_disk

    def sync_json_with_disk_files(self):
        """SAFE: Îmbogățește informațiile din JSON cu cele de pe disk, ZERO pierderi + SORTARE CRONOLOGICĂ CORECTĂ"""
        print("🔄 MERGE SAFE - combinez informațiile din JSON cu cele de pe disk...")

        # PASUL 1: Scanează complet disk-ul
        issues_on_disk = self.reconstruct_all_issues_from_disk()

        # PASUL 2: PĂSTREAZĂ TOATE issue-urile existente din JSON (ZERO pierderi)
        existing_issues_by_url = {}
        for item in self.state.get("downloaded_issues", []):
            url = item.get("url", "").rstrip('/')
            existing_issues_by_url[url] = item.copy()  # DEEP COPY pentru siguranță

        print(f"📋 PĂSTREZ {len(existing_issues_by_url)} issue-uri din JSON existent")

        # PASUL 3: MERGE cu datele de pe disk (doar îmbogățește, nu șterge)
        enriched_count = 0
        new_from_disk_count = 0

        for issue_id, disk_data in issues_on_disk.items():
            url = disk_data['url']
            if not url:
                continue

            max_page = disk_data['max_page']
            segments_count = len(disk_data['segments'])
            is_complete = self.is_issue_complete_by_end_page(max_page)

            if url in existing_issues_by_url:
                # ÎMBOGĂȚEȘTE issue-ul existent (doar dacă progresul e mai mare)
                existing_issue = existing_issues_by_url[url]
                current_progress = existing_issue.get("last_successful_segment_end", 0)

                if max_page > current_progress:
                    # ÎMBOGĂȚEȘTE doar câmpurile necesare, păstrează restul
                    existing_issue["last_successful_segment_end"] = max_page
                    if not existing_issue.get("total_pages"):
                        existing_issue["total_pages"] = max_page
                    enriched_count += 1
                    print(f"🔄 ÎMBOGĂȚIT: {url} - progres {current_progress} → {max_page}")

                # Marchează ca complet DOAR dacă nu era deja marcat
                if is_complete and not existing_issue.get("completed_at"):
                    existing_issue["completed_at"] = datetime.now().isoformat(timespec="seconds")
                    existing_issue["pages"] = max_page
                    existing_issue["total_pages"] = max_page
                    print(f"✅ MARCAT ca complet: {url} ({max_page} pagini)")

            else:
                # Issue complet nou găsit doar pe disk - ADAUGĂ
                new_issue = {
                    "url": url,
                    "title": issue_id.replace("-", " ").replace("_", " "),
                    "subtitle": "",
                    "pages": max_page if is_complete else 0,
                    "completed_at": datetime.now().isoformat(timespec="seconds") if is_complete else "",
                    "last_successful_segment_end": max_page,
                    "total_pages": max_page if is_complete else None
                }
                existing_issues_by_url[url] = new_issue
                new_from_disk_count += 1
                print(f"➕ ADĂUGAT nou din disk: {url} ({max_page} pagini, {segments_count} segmente)")

        # PASUL 4: Reconstruiește lista finală (TOATE issue-urile păstrate)
        all_issues_list = list(existing_issues_by_url.values())

        # PASUL 5: SORTARE CRONOLOGICĂ CORECTĂ
        partial_issues = []
        complete_issues = []

        for issue in all_issues_list:
            is_partial = (issue.get("last_successful_segment_end", 0) > 0 and
                         not issue.get("completed_at") and
                         issue.get("total_pages") and
                         issue.get("last_successful_segment_end", 0) < issue.get("total_pages", 0))

            if is_partial:
                partial_issues.append(issue)
                print(f"🔄 Issue parțial: {issue['url']} ({issue.get('last_successful_segment_end', 0)}/{issue.get('total_pages', 0)} pagini)")
            else:
                complete_issues.append(issue)

        # SORTARE CRONOLOGICĂ PENTRU COMPLETE ISSUES
        # Sortează issue-urile complete după completed_at (cel mai recent primul)
        def sort_key_for_complete(issue):
            completed_at = issue.get("completed_at", "")
            if completed_at:
                try:
                    # Convertește la datetime pentru sortare corectă
                    return datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except:
                    return datetime.min
            else:
                # Issue-urile fără completed_at merg la sfârșit
                return datetime.min

        # Sortează: parțiale după progres (desc), complete după data (desc - cel mai recent primul)
        partial_issues.sort(key=lambda x: x.get("last_successful_segment_end", 0), reverse=True)
        complete_issues.sort(key=sort_key_for_complete, reverse=True)  # Cel mai recent primul

        print(f"\n📊 SORTARE CRONOLOGICĂ APLICATĂ:")
        print(f"   🔄 Issue-uri parțiale: {len(partial_issues)} (sortate după progres)")

        if complete_issues:
            print(f"   ✅ Issue-uri complete: {len(complete_issues)} (sortate cronologic)")
            print(f"      📅 Cel mai recent: {complete_issues[0].get('completed_at', 'N/A')}")
            print(f"      📅 Cel mai vechi: {complete_issues[-1].get('completed_at', 'N/A')}")

            # Afișează primele 5 pentru verificare
            print(f"      🔍 Ordinea cronologică (primele 5):")
            for i, issue in enumerate(complete_issues[:5]):
                url = issue.get('url', '').split('/')[-1]
                completed_at = issue.get('completed_at', 'N/A')
                print(f"         {i+1}. {url} - {completed_at}")

        # PASUL 6: Actualizează starea SAFE (păstrează tot ce nu modificăm)
        original_count = self.state.get("count", 0)
        final_issues = partial_issues + complete_issues  # Parțiale primul, apoi complete cronologic
        actual_complete_count = len([i for i in final_issues if i.get("completed_at")])

        # PĂSTREAZĂ toate câmpurile existente, actualizează doar ce e necesar
        self.state["downloaded_issues"] = final_issues
        self.state["count"] = max(original_count, actual_complete_count)  # Nu scade niciodată

        self._save_state_safe()

        print(f"✅ MERGE COMPLET cu SORTARE CRONOLOGICĂ CORECTĂ - ZERO pierderi:")
        print(f"   📊 Total issues: {len(final_issues)} (înainte: {len(existing_issues_by_url) - new_from_disk_count})")
        print(f"   🔄 Îmbogățite: {enriched_count}")
        print(f"   ➕ Adăugate din disk: {new_from_disk_count}")
        print(f"   🔄 Parțiale: {len(partial_issues)}")
        print(f"   ✅ Complete: {len(complete_issues)}")
        print(f"   🎯 Count păstrat/actualizat: {original_count} → {self.state['count']}")

        if partial_issues:
            print("🎯 Issue-urile parțiale vor fi procesate primele!")

        print("📅 Issue-urile complete sunt acum sortate cronologic (cel mai recent primul)!")

    def cleanup_duplicate_issues(self):
        """NOUĂ FUNCȚIE: Elimină dublurile din state.json"""
        print("🧹 CURĂȚARE: Verific și elimin dublurile din state.json...")

        issues = self.state.get("downloaded_issues", [])
        if not issues:
            return

        # Grupează după URL normalizat
        url_groups = {}
        for i, item in enumerate(issues):
            url = item.get("url", "").rstrip('/').lower()
            if not url:
                continue

            if url not in url_groups:
                url_groups[url] = []
            url_groups[url].append((i, item))

        # Găsește și rezolvă dublurile
        duplicates_found = 0
        clean_issues = []
        processed_urls = set()

        for original_url, group in url_groups.items():
            if len(group) > 1:
                duplicates_found += 1
                print(f"🔍 DUBLURĂ găsită pentru {original_url}: {len(group)} intrări")

                # Găsește cea mai completă versiune
                best_item = None
                best_score = -1

                for idx, item in group:
                    score = 0
                    if item.get("completed_at"): score += 100
                    if item.get("total_pages"): score += 50
                    if item.get("title"): score += 10
                    if item.get("last_successful_segment_end", 0) > 0: score += 20

                    print(f"   📊 Index {idx}: score {score}, completed: {bool(item.get('completed_at'))}")

                    if score > best_score:
                        best_score = score
                        best_item = item

                print(f"   ✅ Păstrez cea mai completă versiune (score: {best_score})")
                clean_issues.append(best_item)
            else:
                # Nu e dublură, păstrează-l
                clean_issues.append(group[0][1])

            processed_urls.add(original_url)

        if duplicates_found > 0:
            print(f"🧹 ELIMINAT {duplicates_found} dubluri din {len(issues)} issues")
            print(f"📊 Rămas cu {len(clean_issues)} issues unice")

            self.state["downloaded_issues"] = clean_issues
            self._save_state_safe()
        else:
            print("✅ Nu am găsit dubluri în state.json")

    def is_issue_really_complete(self, item):
            """HELPER: Verifică dacă un issue este REAL complet (nu doar marcat ca atare)"""
            completed_at = item.get("completed_at")
            last_segment = item.get("last_successful_segment_end", 0)
            total_pages = item.get("total_pages")
            pages = item.get("pages", 0)

            # Un issue este REAL complet dacă:
            # 1. Are completed_at setat ȘI
            # 2. Are progresul complet (last_segment >= total_pages) ȘI
            # 3. Are pages > 0 (nu e marcat greșit)
            return (
                completed_at and
                total_pages and
                total_pages > 0 and
                last_segment >= total_pages and
                pages > 0
            )

    def fix_incorrectly_marked_complete_issues(self):
            """NOUĂ FUNCȚIE: Corectează issue-urile marcate greșit ca complete"""
            print("🔧 CORECTEZ issue-urile marcate GREȘIT ca complete...")

            fixes_applied = 0

            for item in self.state.get("downloaded_issues", []):
                completed_at = item.get("completed_at")
                last_segment = item.get("last_successful_segment_end", 0)
                total_pages = item.get("total_pages")
                pages = item.get("pages", 0)
                url = item.get("url", "")

                # Detectează issue-uri marcate greșit ca complete
                if (completed_at and
                    pages == 0 and
                    total_pages and
                    last_segment < total_pages):

                    print(f"🚨 CORECTEZ issue marcat GREȘIT ca complet: {url}")
                    print(f"   Înainte: completed_at={completed_at}, pages={pages}")
                    print(f"   Progres real: {last_segment}/{total_pages}")

                    # Șterge completed_at pentru a-l face parțial din nou
                    item["completed_at"] = ""
                    item["pages"] = 0  # Asigură-te că pages rămâne 0

                    fixes_applied += 1
                    print(f"   După: completed_at='', pages=0 (va fi reluat)")

            if fixes_applied > 0:
                print(f"🔧 CORECTAT {fixes_applied} issue-uri marcate greșit ca complete")
                self._save_state_safe()

                # Actualizează și skip URLs
                self._save_skip_urls()
            else:
                print("✅ Nu am găsit issue-uri marcate greșit ca complete")

            return fixes_applied

    def get_pending_partial_issues(self):
            """FIXED: Returnează issue-urile parțiale care trebuie continuate (inclusiv cele cu completed_at setat greșit)"""
            pending_partials = []

            for item in self.state.get("downloaded_issues", []):
                url = item.get("url", "").rstrip('/')
                last_segment = item.get("last_successful_segment_end", 0)
                total_pages = item.get("total_pages")
                completed_at = item.get("completed_at", "")
                pages = item.get("pages", 0)

                # Skip URL-urile complet descărcate
                if url in self.dynamic_skip_urls:
                    continue

                # LOGICĂ CORECTATĂ: Un issue este parțial dacă:
                # 1. Are progres (last_segment > 0)
                # 2. Are total_pages setat
                # 3. Progresul nu este complet (last_segment < total_pages)
                # 4. SAU are completed_at setat dar pages = 0 (marcat greșit ca complet)

                is_partial = False

                # Caz 1: Issue cu progres dar necomplet
                if (last_segment > 0 and
                    total_pages and
                    last_segment < total_pages):
                    is_partial = True

                # Caz 2: Issue marcat ca complet dar cu pages = 0 (eroare de marcare)
                elif (completed_at and
                      pages == 0 and
                      total_pages and
                      last_segment < total_pages):
                    is_partial = True
                    print(f"🚨 DETECTAT issue marcat GREȘIT ca complet: {url}")
                    print(f"   completed_at: {completed_at}, pages: {pages}")
                    print(f"   progres real: {last_segment}/{total_pages}")

                if is_partial:
                    pending_partials.append(item)
                    print(f"🔄 Issue parțial găsit: {url} (pagini {last_segment}/{total_pages})")

            return pending_partials

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
        """ULTRA SAFE: Nu șterge NICIODATĂ datele existente"""
        today = datetime.now().strftime("%Y-%m-%d")

        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    loaded = self._decode_unicode_escapes(loaded)

                # PĂSTREAZĂ TOATE issue-urile existente - ZERO ȘTERS
                existing_issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))

                print(f"📋 ÎNCĂRCAT {len(existing_issues)} issue-uri din state.json")

                # Găsește issue-urile parțiale
                partial_issues = []
                for issue in existing_issues:
                    last_segment = issue.get("last_successful_segment_end", 0)
                    total_pages = issue.get("total_pages")
                    completed_at = issue.get("completed_at", "")

                    if (last_segment > 0 and not completed_at and total_pages and last_segment < total_pages):
                        partial_issues.append(issue)
                        print(f"🔄 PARȚIAL: {issue['url']} - {last_segment}/{total_pages} pagini")

                complete_count = len([i for i in existing_issues if i.get("completed_at")])

                # PĂSTREAZĂ TOT - doar actualizează data
                self.state = {
                    "date": today,
                    "count": loaded.get("count", complete_count),
                    "downloaded_issues": existing_issues,  # TOATE PĂSTRATE
                    "pages_downloaded": loaded.get("pages_downloaded", 0),
                    "recent_links": loaded.get("recent_links", []),
                    "daily_limit_hit": False,
                    "main_collection_completed": loaded.get("main_collection_completed", False),
                    "current_additional_collection_index": loaded.get("current_additional_collection_index", 0)
                }

                print(f"✅ PĂSTRAT TOT: {complete_count} complete, {len(partial_issues)} parțiale")

            except Exception as e:
                print(f"❌ JSON CORRUPT: {e}")
                print(f"🛠️ RECUPEREZ din backup sau disk...")

                # Încearcă backup
                backup_path = self.state_path + ".backup"
                if os.path.exists(backup_path):
                    print(f"🔄 Restabilesc din backup...")
                    shutil.copy2(backup_path, self.state_path)
                    return self._load_state()  # Recursiv cu backup

                # Altfel începe gol dar SCANEAZĂ DISK-UL
                print(f"🔍 SCANEZ DISK-UL pentru recuperare...")
                self.state = {
                    "date": today,
                    "count": 0,
                    "downloaded_issues": [],
                    "pages_downloaded": 0,
                    "recent_links": [],
                    "daily_limit_hit": False,
                    "main_collection_completed": False,
                    "current_additional_collection_index": 0
                }
        else:
            print(f"📄 Nu există state.json")
            self.state = {
                "date": today,
                "count": 0,
                "downloaded_issues": [],
                "pages_downloaded": 0,
                "recent_links": [],
                "daily_limit_hit": False,
                "main_collection_completed": False,
                "current_additional_collection_index": 0
            }

        self._save_state()

    def _save_state_safe(self):
        """SAFE: Salvează starea doar dacă există modificări, păstrează backup"""
        try:
            # Creează backup înainte de salvare
            if os.path.exists(self.state_path):
                backup_path = self.state_path + ".backup"
                shutil.copy2(self.state_path, backup_path)

            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠ Nu am putut salva state-ul: {e}")
            # Încearcă să restabilească din backup
            backup_path = self.state_path + ".backup"
            if os.path.exists(backup_path):
                print(f"🔄 Încerc să restabilesc din backup...")
                try:
                    shutil.copy2(backup_path, self.state_path)
                    print(f"✅ State restabilit din backup")
                except:
                    print(f"❌ Nu am putut restabili din backup")

    def _save_state(self):
        """WRAPPER: Folosește salvarea safe"""
        self._save_state_safe()

    def fix_existing_json(self):
        """Funcție temporară pentru a repara caracterele din JSON existent"""
        if os.path.exists(self.state_path):
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            data = self._decode_unicode_escapes(data)

            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print("✅ JSON reparat cu caractere românești")

    def remaining_quota(self):
        return max(0, DAILY_LIMIT - self.state.get("count", 0))

    def _update_partial_issue_progress(self, issue_url, last_successful_segment_end, total_pages=None, title=None, subtitle=None):
        """FIXED: Previne dublurile - verifică și după title dacă URL-ul nu se potrivește"""
        normalized = issue_url.rstrip('/')
        updated = False

        # STEP 1: Caută după URL exact
        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item["url"] == normalized:
                # ACTUALIZEAZĂ issue-ul existent
                if last_successful_segment_end > item.get("last_successful_segment_end", 0):
                    item["last_successful_segment_end"] = last_successful_segment_end

                if total_pages is not None and not item.get("total_pages"):
                    item["total_pages"] = total_pages

                if title and not item.get("title"):
                    item["title"] = title

                if subtitle and not item.get("subtitle"):
                    item["subtitle"] = subtitle

                # Mută la început pentru prioritate
                updated_item = self.state["downloaded_issues"].pop(i)
                self.state["downloaded_issues"].insert(0, updated_item)
                updated = True
                print(f"🔄 ACTUALIZAT progres pentru: {normalized} → {last_successful_segment_end} pagini")
                break

        # STEP 2: Dacă nu găsești după URL, caută după title (prevenire dubluri)
        if not updated and title:
            for i, item in enumerate(self.state["downloaded_issues"]):
                if item.get("title") == title and not item["url"].startswith("http"):
                    # GĂSIT dublu cu title ca URL - șterge-l!
                    print(f"🗑️ ȘTERG DUBLU GREȘIT: {item['url']} (era title în loc de URL)")
                    self.state["downloaded_issues"].pop(i)
                    break

        # STEP 3: Doar dacă nu există deloc, creează nou
        if not updated:
            # VALIDEAZĂ că URL-ul e corect
            if not normalized.startswith("https://"):
                print(f"❌ URL INVALID: {normalized} - nu creez issue nou!")
                return

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
            print(f"➕ ADĂUGAT issue nou în progres: {normalized}")

        self._save_state_safe()
        print(f"💾 Progres salvat SAFE: {normalized} - pagini {last_successful_segment_end}/{total_pages or '?'}")

    def mark_issue_done(self, issue_url, pages_count, title=None, subtitle=None, total_pages=None):
        """ULTRA SAFE: Verificări stricte înainte de a marca ca terminat"""
        normalized = issue_url.rstrip('/')
        now_iso = datetime.now().isoformat(timespec="seconds")

        # ===== VERIFICĂRI ULTRA SAFE ÎNAINTE DE A MARCA CA TERMINAT =====

        print(f"🔒 VERIFICĂRI ULTRA SAFE pentru marcarea ca terminat: {normalized}")

        # VERIFICARE 1: total_pages trebuie să fie rezonabil
        if total_pages is None or total_pages <= 0:
            print(f"❌ BLOCARE SAFETY: total_pages invalid ({total_pages}) pentru {normalized}")
            print(f"🛡️ NU MARCHEZ ca terminat fără total_pages valid!")
            print(f"🔄 Marchează ca parțial cu progres {pages_count}")

            # Marchează ca parțial, NU ca terminat
            self._update_partial_issue_progress(
                normalized, pages_count, total_pages=None, title=title, subtitle=subtitle
            )
            return

        # VERIFICARE 2: pages_count trebuie să fie aproape de total_pages
        completion_percentage = (pages_count / total_pages) * 100

        if completion_percentage < 95:  # Trebuie să fie cel puțin 95% complet
            print(f"❌ BLOCARE SAFETY: Progres insuficient pentru {normalized}")
            print(f"📊 Progres: {pages_count}/{total_pages} ({completion_percentage:.1f}%)")
            print(f"🛡️ Trebuie cel puțin 95% pentru a marca ca terminat!")
            print(f"🔄 Marchează ca parțial în loc de terminat")

            # Marchează ca parțial, NU ca terminat
            self._update_partial_issue_progress(
                normalized, pages_count, total_pages=total_pages, title=title, subtitle=subtitle
            )
            return

        # VERIFICARE 3: Detectează batch size suspicious
        if pages_count < 100 and total_pages > 500:
            print(f"❌ BLOCARE SAFETY: Progres suspect de mic pentru {normalized}")
            print(f"📊 {pages_count} pagini par să fie doar primul batch din {total_pages}")
            print(f"🛡️ Probabil s-a oprit prematur, NU marchez ca terminat")

            # Marchează ca parțial
            self._update_partial_issue_progress(
                normalized, pages_count, total_pages=total_pages, title=title, subtitle=subtitle
            )
            return

        # VERIFICARE 4: Verifică dacă pages_count pare să fie doar primul segment
        if total_pages >= 1000 and pages_count < 100:
            print(f"❌ BLOCARE SAFETY: {pages_count} pagini din {total_pages} pare primul segment")
            print(f"🛡️ NU marchez issues mari ca terminate cu progres atât de mic")

            # Marchează ca parțial
            self._update_partial_issue_progress(
                normalized, pages_count, total_pages=total_pages, title=title, subtitle=subtitle
            )
            return

        # ===== TOATE VERIFICĂRILE AU TRECUT - SAFE SĂ MARCHEZ CA TERMINAT =====

        print(f"✅ TOATE VERIFICĂRILE ULTRA SAFE trecute pentru {normalized}")
        print(f"📊 Progres: {pages_count}/{total_pages} ({completion_percentage:.1f}%)")
        print(f"🎯 Marchez ca TERMINAT")

        # Continuă cu logica originală de marcare ca terminat...
        existing = None
        existing_index = -1

        # CĂUTARE ÎMBUNĂTĂȚITĂ: încearcă mai multe variante de URL
        search_variants = [
            normalized,
            normalized + '/',
            normalized.replace('https://', 'http://'),
            normalized.replace('http://', 'https://')
        ]

        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            item_url = item.get("url", "").rstrip('/')
            if item_url in search_variants or normalized in [item_url, item_url + '/']:
                existing = item
                existing_index = i
                print(f"🔍 GĂSIT issue existent la index {i}: {item_url}")
                break

        # Creează record-ul de completare
        completion_data = {
            "pages": pages_count,
            "completed_at": now_iso,
            "last_successful_segment_end": pages_count,
            "total_pages": total_pages  # SETEAZĂ ÎNTOTDEAUNA!
        }

        # Adaugă title/subtitle doar dacă nu există sau sunt goale
        if title:
            completion_data["title"] = title
        if subtitle:
            completion_data["subtitle"] = subtitle

        if existing:
            # ÎMBOGĂȚEȘTE issue-ul existent
            for key, value in completion_data.items():
                if key in ["title", "subtitle"]:
                    if not existing.get(key):
                        existing[key] = value
                else:
                    existing[key] = value

            # SCOATE din poziția curentă
            updated_issue = self.state["downloaded_issues"].pop(existing_index)
            print(f"✅ ACTUALIZAT și SCOS din poziția {existing_index}: {normalized}")
        else:
            # Creează issue nou complet
            updated_issue = {
                "url": normalized,
                "title": title or "",
                "subtitle": subtitle or "",
                **completion_data
            }
            print(f"➕ CREAT issue nou: {normalized}")

        # INSEREAZĂ ÎN POZIȚIA CRONOLOGICĂ CORECTĂ
        # Găsește primul issue cu completed_at mai vechi decât cel curent
        insert_position = 0

        # Sari peste issue-urile parțiale (care sunt mereu primele)
        while (insert_position < len(self.state["downloaded_issues"]) and
               not self.state["downloaded_issues"][insert_position].get("completed_at")):
            insert_position += 1

        # Găsește poziția corectă între issue-urile complete (sortate cronologic descendent)
        while insert_position < len(self.state["downloaded_issues"]):
            other_completed_at = self.state["downloaded_issues"][insert_position].get("completed_at", "")
            if other_completed_at and other_completed_at < now_iso:
                break
            insert_position += 1

        # Inserează în poziția cronologică corectă
        self.state["downloaded_issues"].insert(insert_position, updated_issue)
        print(f"📅 INSERAT în poziția CRONOLOGICĂ {insert_position} (după issue-urile parțiale și în ordine de completed_at)")

        # Actualizează contoarele SAFE
        completed_count = len([i for i in self.state["downloaded_issues"] if i.get("completed_at")])
        self.state["count"] = max(self.state.get("count", 0), completed_count)

        # Actualizează pages_downloaded SAFE
        current_pages = self.state.get("pages_downloaded", 0)
        self.state["pages_downloaded"] = current_pages + pages_count

        # Adaugă în recent_links (păstrează max 10)
        recent_entry = {
            "url": normalized,
            "title": (existing and existing.get("title")) or title or "",
            "subtitle": (existing and existing.get("subtitle")) or subtitle or "",
            "pages": pages_count,
            "timestamp": now_iso
        }
        recent_links = self.state.setdefault("recent_links", [])
        recent_links.insert(0, recent_entry)
        self.state["recent_links"] = recent_links[:10]

        # Resetează flag-ul de limită
        self.state["daily_limit_hit"] = False

        # Adaugă în skip URLs
        self.dynamic_skip_urls.add(normalized)

        self._save_state_safe()
        self._save_skip_urls()

        print(f"✅ Issue marcat ca terminat cu SORTARE CRONOLOGICĂ CORECTĂ: {normalized}")
        print(f"📊 Detalii: {pages_count} pagini, total_pages: {total_pages}")
        print(f"📊 Total complet: {self.state['count']}, Total pagini: {self.state['pages_downloaded']}")
        print(f"📅 Plasat în poziția cronologică {insert_position} din {len(self.state['downloaded_issues'])}")

    def mark_collection_complete(self, collection_url):
        """Marchează o colecție ca fiind complet procesată în skip_urls.json"""
        try:
            normalized_collection = collection_url.rstrip('/')

            # Adaugă în dynamic skip URLs
            self.dynamic_skip_urls.add(normalized_collection)

            # Salvează în skip_urls.json cu un marker special pentru colecții
            skip_data = {}
            if os.path.exists(self.skip_urls_path):
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    skip_data = json.load(f)

            completed_collections = skip_data.get("completed_collections", [])
            if normalized_collection not in completed_collections:
                completed_collections.append(normalized_collection)
                skip_data["completed_collections"] = completed_collections
                skip_data["last_updated"] = datetime.now().isoformat()

                with open(self.skip_urls_path, "w", encoding="utf-8") as f:
                    json.dump(skip_data, f, indent=2, ensure_ascii=False)

                print(f"✅ Colecția marcată ca completă: {normalized_collection}")
        except Exception as e:
            print(f"⚠ Eroare la marcarea colecției complete: {e}")

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
            # VERIFICĂ ÎNTÂI DACĂ BROWSER-UL MAI EXISTĂ
            try:
                _ = self.driver.current_url
            except:
                print("⚠ Browser închis, încerc reconectare...")
                if not self.setup_chrome_driver():
                    print("❌ Nu pot reconecta browser-ul")
                    return False

            print(f"🌐 Navighez către: {url}")
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
            print("✅ Pagina încărcată.")
            return True
        except Exception as e:
            print(f"❌ Eroare la navigare sau încărcare: {e}")
            # ÎNCEARCĂ O RECONECTARE CA ULTIM RESORT
            try:
                print("🔄 Încerc reconectare de urgență...")
                if self.setup_chrome_driver():
                    self.driver.get(url)
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
                    print("✅ Reconectat și navigat cu succes!")
                    return True
            except:
                pass
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
        """FIXED: Detectează corect numărul total de pagini"""
        for attempt in range(1, max_attempts + 1):
            try:
                # Metoda 1: Caută pattern-ul "număr / total" în mai multe locuri
                page_patterns = [
                    r'(\d+)\s*/\s*(\d+)',  # "249 / 1565"
                    r'/\s*(\d+)',          # "/ 1565"
                    r'of\s+(\d+)',         # "of 1565"
                ]

                # Caută în toate textele de pe pagină
                all_texts = self.driver.find_elements(By.XPATH, "//*[contains(text(), '/') or contains(text(), 'of')]")

                for el in all_texts:
                    text = el.text.strip()
                    for pattern in page_patterns:
                        matches = re.findall(pattern, text)
                        if matches:
                            if pattern == page_patterns[0]:  # "număr / total"
                                current, total = matches[0]
                                total = int(total)
                                print(f"✅ TOTAL PAGINI detectat din '{text}': {total} (curent: {current})")
                                return total
                            else:  # "/ total" sau "of total"
                                total = int(matches[0])
                                print(f"✅ TOTAL PAGINI detectat din '{text}': {total}")
                                return total

                # Metoda 2: JavaScript pentru căutare mai profundă
                js_result = self.driver.execute_script(r"""
                    const patterns = [
                        /(\d+)\s*\/\s*(\d+)/g,
                        /\/\s*(\d+)/g,
                        /of\s+(\d+)/g
                    ];

                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                    while(walker.nextNode()) {
                        const text = walker.currentNode.nodeValue;
                        for (let pattern of patterns) {
                            const matches = [...text.matchAll(pattern)];
                            if (matches.length > 0) {
                                const match = matches[0];
                                if (match.length === 3) {  // "număr / total"
                                    return {text: text, total: parseInt(match[2]), current: parseInt(match[1])};
                                } else {  // "/ total"
                                    return {text: text, total: parseInt(match[1])};
                                }
                            }
                        }
                    }
                    return null;
                """)

                if js_result:
                    total = js_result['total']
                    current = js_result.get('current', 0)
                    text = js_result['text']
                    print(f"✅ TOTAL PAGINI detectat prin JS din '{text}': {total} (curent: {current})")
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

                    if ("Daily download limit reached" in body_text or
                        "Terms and conditions" in body_text):
                        print(f"⚠ Limita zilnică detectată în fereastra: {handle}")
                        limit_reached = True

                        if handle != current_window and len(all_handles) > 1:
                            print(f"🗙 Închid fereastra cu limita zilnică: {handle}")
                            self.driver.close()
                        break

                except Exception as e:
                    continue

            try:
                if current_window in self.driver.window_handles:
                    self.driver.switch_to.window(current_window)
                elif self.driver.window_handles:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception:
                pass

        except Exception as e:
            print(f"⚠ Eroare la verificarea ferestrelor: {e}")

        if limit_reached and set_flag:
            self.state["daily_limit_hit"] = True
            self._save_state()

        return limit_reached

    def check_for_daily_limit_popup(self):
        """Verifică dacă s-a deschis o filă nouă cu mesajul de limită zilnică după descărcare"""
        try:
            current_handles = set(self.driver.window_handles)

            # Verifică toate filele deschise pentru mesajul de limită
            for handle in current_handles:
                try:
                    self.driver.switch_to.window(handle)
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()

                    if "Daily download limit reached" in body_text:
                        print(f"🛑 LIMITĂ ZILNICĂ DETECTATĂ în filă nouă: {handle}")
                        print(f"📄 Conținut filă: {body_text}")

                        # Închide fila cu limita
                        self.driver.close()

                        # Revine la prima filă disponibilă
                        if self.driver.window_handles:
                            self.driver.switch_to.window(self.driver.window_handles[0])

                        # Setează flag-ul și oprește procesarea
                        self.state["daily_limit_hit"] = True
                        self._save_state()
                        return True

                except Exception as e:
                    continue

            return False

        except Exception as e:
            print(f"⚠ Eroare la verificarea popup-ului de limită: {e}")
            return False

    def save_page_range(self, start, end, retries=1):
            """FIXED: Verifică URL-ul înainte de fiecare descărcare + verifică limita zilnică"""
            for attempt in range(1, retries + 2):
                print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")

                # VERIFICARE CRITICĂ: Suntem pe documentul corect?
                try:
                    current_url = self.driver.current_url
                    if self.current_issue_url not in current_url:
                        print(f"🚨 EROARE: Browser-ul a navigat la URL greșit!")
                        print(f"   Așteptat: {self.current_issue_url}")
                        print(f"   Actual: {current_url}")
                        print(f"🔄 Renavigez la documentul corect...")

                        if not self.navigate_to_page(self.current_issue_url):
                            print(f"❌ Nu pot renaviga la {self.current_issue_url}")
                            return False

                        time.sleep(3)  # Așteaptă încărcarea completă
                        print(f"✅ Renavigat cu succes la documentul corect")
                except Exception as e:
                    print(f"⚠ Eroare la verificarea URL-ului: {e}")

                if not self.open_save_popup():
                    print(f"⚠ Eșec la deschiderea popup-ului pentru {start}-{end}")
                    time.sleep(1)
                    continue

                success = self.fill_and_save_range(start, end)
                if success:
                    print("⏳ Aștept 5s pentru finalizarea descărcării segmentului...")
                    time.sleep(5)

                    # VERIFICĂ LIMITA ZILNICĂ IMEDIAT DUPĂ DESCĂRCARE
                    if self.check_for_daily_limit_popup():
                        print(f"🛑 OPRIRE INSTANT - Limită zilnică detectată după segmentul {start}-{end}")
                        return False

                    print(f"✅ Segmentul {start}-{end} descărcat cu succes")
                    return True
                else:
                    print(f"⚠ Retry pentru segmentul {start}-{end}")
                    time.sleep(1)
            print(f"❌ Renunț la segmentul {start}-{end} după {retries+1} încercări.")
            return False

    def save_all_pages_in_batches(self, resume_from=1):
        """FIXED: Oprește instant la detectarea limitei zilnice și NU marchează ca terminat dacă e incomplet"""
        total = self.get_total_pages()
        if total <= 0:
            print("⚠ Nu am obținut numărul total de pagini; nu pot continua.")
            return 0, False

        print(f"🎯 TOTAL PAGINI DETECTAT: {total}")

        # Verificare de siguranță pentru total_pages suspect
        if total < 50:
            print(f"⚠ ATENȚIE: total_pages pare suspect de mic ({total})")
            print(f"🔄 Încerc din nou detecția...")
            time.sleep(3)
            total_retry = self.get_total_pages()
            if total_retry > total:
                total = total_retry
                print(f"✅ Total actualizat la: {total}")

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

        last_successful_page = resume_from - 1

        print(f"🎯 FOCUSEZ PE ACEST ISSUE: Voi descărca {len(segments)} segmente fără întreruperi")

        for (start, end) in segments:
            print(f"📦 Procesez segmentul {start}-{end}")
            result = self.save_page_range(start, end, retries=1)

            if not result:
                # VERIFICĂ DACĂ EȘECUL E DIN CAUZA LIMITEI ZILNICE
                if self.state.get("daily_limit_hit", False):
                    print(f"🛑 OPRIRE INSTANT - Limită zilnică atinsă la segmentul {start}-{end}")
                    return last_successful_page, True  # Returnează TRUE pentru limită zilnică

                print(f"❌ Eșec persistent la segmentul {start}-{end}")
                print(f"📊 PROGRES PARȚIAL: {last_successful_page}/{total} pagini")
                print(f"🔄 Issue-ul va rămâne PARȚIAL pentru continuare ulterioară")
                return last_successful_page, False  # Eșec - nu e terminat

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

    def extract_page_range_from_filename(self, filename):
        """Extrage range-ul de pagini din numele fișierului pentru sortare corectă"""
        match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
        if match:
            start_page = int(match.group(1))
            end_page = int(match.group(2))
            return (start_page, end_page)
        return (0, 0)

    def copy_and_combine_issue_pdfs(self, issue_url: str, issue_title: str):
        """
        FIXED: MUTĂ fișierele în folder și le combină (nu mai păstrează pe D:)
        ADDED: Face backup în g:Temporare înainte de procesare
        """
        issue_id = issue_url.rstrip('/').split('/')[-1]
        folder_name = self._safe_folder_name(issue_title or issue_id)
        dest_dir = os.path.join(self.download_dir, folder_name)
        os.makedirs(dest_dir, exist_ok=True)

        # DIRECTORUL DE BACKUP
        backup_base_dir = r"g:\Temporare"
        backup_dir = os.path.join(backup_base_dir, folder_name)

        print(f"📁 Procesez PDF-urile pentru '{issue_title}' cu ID '{issue_id}'")

        # ⏳ AȘTEAPTĂ CA TOATE FIȘIERELE SĂ FIE COMPLET DESCĂRCATE
        print("⏳ Aștept 10 secunde ca toate fișierele să se termine de descărcat...")
        time.sleep(10)

        # PASUL 1: Găsește TOATE fișierele pentru acest issue
        all_segments = self.get_all_pdf_segments_for_issue(issue_url)

        if not all_segments:
            print(f"ℹ️ Nu am găsit fișiere PDF pentru '{issue_title}' cu ID '{issue_id}'.")
            return

        print(f"🔍 Am găsit {len(all_segments)} fișiere PDF pentru '{issue_id}':")
        for seg in all_segments:
            print(f"   📄 {seg['filename']} (pagini {seg['start']}-{seg['end']})")

        # PASUL 1.5: CREEAZĂ BACKUP-UL ÎNAINTE DE PROCESARE
        print(f"💾 Creez backup în: {backup_dir}")
        try:
            os.makedirs(backup_dir, exist_ok=True)
            backup_success = True
            backup_size_total = 0

            for seg in all_segments:
                src = seg['path']
                backup_dst = os.path.join(backup_dir, seg['filename'])

                try:
                    shutil.copy2(src, backup_dst)  # copy2 păstrează și metadata
                    file_size = os.path.getsize(backup_dst)
                    backup_size_total += file_size
                    print(f"💾 BACKUP: {seg['filename']} → g:\\Temporare\\{folder_name}\\")
                except Exception as e:
                    print(f"⚠ EROARE backup pentru {seg['filename']}: {e}")
                    backup_success = False

            backup_size_mb = backup_size_total / (1024 * 1024)
            if backup_success:
                print(f"✅ BACKUP COMPLET: {len(all_segments)} fișiere ({backup_size_mb:.2f} MB) în {backup_dir}")
            else:
                print(f"⚠ BACKUP PARȚIAL: Unele fișiere nu au putut fi copiate în backup")

        except Exception as e:
            print(f"❌ EROARE la crearea backup-ului: {e}")
            print(f"🛡️ OPRESC PROCESAREA pentru siguranță - fișierele rămân pe D:\\")
            return

        # PASUL 2: MUTĂ (nu copiază) TOATE fișierele în folder (DOAR DUPĂ backup SUCCESS)
        moved_files = []
        for seg in all_segments:
            src = seg['path']
            dst = os.path.join(dest_dir, seg['filename'])
            try:
                shutil.move(src, dst)  # MOVE în loc de COPY
                moved_files.append(dst)
                print(f"📄 MUTAT: {seg['filename']} → {folder_name}/")
            except Exception as e:
                print(f"⚠ Nu am reușit să mut {seg['filename']}: {e}")

        if not moved_files:
            print(f"❌ Nu am reușit să mut niciun fișier pentru '{issue_title}'.")
            return

        print(f"📁 Toate {len(moved_files)} PDF-urile pentru '{issue_title}' au fost MUTATE în '{dest_dir}'.")
        print(f"💾 BACKUP SIGUR găsit în: {backup_dir}")

        # PASUL 3: Combină PDF-urile în ordinea corectă
        output_file = os.path.join(dest_dir, f"{folder_name}.pdf")

        try:
            if len(moved_files) > 1:
                print(f"🔗 Combinez {len(moved_files)} fișiere PDF în ordinea corectă...")

                # Sortează fișierele după range-ul de pagini
                files_with_ranges = []
                for file_path in moved_files:
                    filename = os.path.basename(file_path)
                    start_page, end_page = self.extract_page_range_from_filename(filename)
                    files_with_ranges.append((start_page, end_page, file_path))

                # Sortează după pagina de început
                files_with_ranges.sort(key=lambda x: x[0])
                sorted_files = [x[2] for x in files_with_ranges]

                # Afișează ordinea de combinare
                print("📋 Ordinea de combinare:")
                for start, end, path in files_with_ranges:
                    filename = os.path.basename(path)
                    print(f"   📄 {filename} (pagini {start}-{end})")

                from PyPDF2 import PdfMerger
                merger = PdfMerger()

                for pdf_path in sorted_files:
                    try:
                        merger.append(pdf_path)
                        filename = os.path.basename(pdf_path)
                        print(f"   ✅ Adăugat în ordine: {filename}")
                    except Exception as e:
                        print(f"   ⚠ Eroare la adăugarea {pdf_path}: {e}")

                # Scrie fișierul combinat
                merger.write(output_file)
                merger.close()

                # Verifică că fișierul combinat a fost creat cu succes
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                    print(f"✅ Fișierul combinat creat cu succes: {file_size_mb:.2f} MB")

                    # ȘTERGE SEGMENTELE DIN FOLDER (nu mai sunt copii, sunt originalele mutate)
                    deleted_count = 0
                    total_deleted_size = 0

                    for file_to_delete in moved_files:
                        try:
                            file_size = os.path.getsize(file_to_delete)
                            os.remove(file_to_delete)
                            deleted_count += 1
                            total_deleted_size += file_size
                            print(f"   🗑️ Șters segment: {os.path.basename(file_to_delete)}")
                        except Exception as e:
                            print(f"   ⚠ Nu am putut șterge {file_to_delete}: {e}")

                    deleted_size_mb = total_deleted_size / (1024 * 1024)
                    print(f"🎉 FINALIZAT: Păstrat doar fișierul combinat '{os.path.basename(output_file)}'")
                    print(f"🗑️ Șterse {deleted_count} segmente originale ({deleted_size_mb:.2f} MB)")
                    print(f"💾 BACKUP SIGUR: Segmentele originale păstrate în {backup_dir}")

                else:
                    print(f"❌ EROARE: Fișierul combinat nu a fost creat corect!")
                    print(f"🛡️ SIGURANȚĂ: Păstrez segmentele pentru siguranță")
                    print(f"💾 BACKUP DISPONIBIL: {backup_dir}")

            elif len(moved_files) == 1:
                # Un singur fișier - doar redenumește
                original_file = moved_files[0]
                original_size_mb = os.path.getsize(original_file) / (1024 * 1024)

                try:
                    os.replace(original_file, output_file)
                    print(f"✅ Fișierul redenumit în: {os.path.basename(output_file)} ({original_size_mb:.2f} MB)")
                    print(f"💾 BACKUP SIGUR: Originalul păstrat în {backup_dir}")
                except Exception as e:
                    print(f"⚠ Nu am putut redenumi {original_file}: {e}")

            else:
                print(f"ℹ️ Nu există fișiere PDF de combinat în '{dest_dir}'.")

        except Exception as e:
            print(f"❌ EROARE la combinarea PDF-urilor: {e}")
            print(f"🛡️ SIGURANȚĂ: Păstrez segmentele din cauza erorii")
            print(f"💾 BACKUP DISPONIBIL: {backup_dir}")
            return

        # PASUL 4: Raport final
        try:
            if os.path.exists(output_file):
                final_size_mb = os.path.getsize(output_file) / (1024 * 1024)

                print(f"\n📋 RAPORT FINAL pentru '{issue_title}':")
                print(f"   📁 Folder destinație: {dest_dir}")
                print(f"   📄 Fișier final: {os.path.basename(output_file)} ({final_size_mb:.2f} MB)")
                print(f"   🔍 Combinat din {len(all_segments)} segmente")
                print(f"   💾 BACKUP SIGUR: {backup_dir} ({backup_size_mb:.2f} MB)")
                print(f"   ✅ STATUS: SUCCES - fișier complet creat, backup realizat, segmente șterse de pe D:\\")
            else:
                print(f"⚠ Nu s-a putut crea fișierul final pentru '{issue_title}'")
                print(f"💾 BACKUP DISPONIBIL: {backup_dir}")
        except Exception as e:
            print(f"⚠ Eroare la raportul final: {e}")

        print(f"=" * 60)

    def find_next_issue_in_collection_order(self, collection_links, last_completed_url):
        """
        FIXED: Găsește următorul issue de procesat în ordinea din HTML, nu primul din listă
        """
        if not last_completed_url:
            # Dacă nu avem istoric, începe cu primul din listă
            return collection_links[0] if collection_links else None

        try:
            last_index = collection_links.index(last_completed_url.rstrip('/'))
            # Returnează următorul din listă după cel completat
            next_index = last_index + 1
            if next_index < len(collection_links):
                next_url = collection_links[next_index]
                print(f"🎯 Următorul issue după '{last_completed_url}' este: '{next_url}'")
                return next_url
            else:
                print(f"✅ Toate issue-urile din colecție au fost procesate!")
                return None
        except ValueError:
            # Dacă last_completed_url nu e în lista curentă, începe cu primul
            print(f"⚠ URL-ul '{last_completed_url}' nu e în colecția curentă, încep cu primul din listă")
            return collection_links[0] if collection_links else None

    def get_last_completed_issue_from_collection(self, collection_links):
            """FIXED: Găsește ultimul issue REAL complet descărcat din colecția curentă"""
            for item in self.state.get("downloaded_issues", []):
                url = item.get("url", "").rstrip('/')
                if url in [link.rstrip('/') for link in collection_links]:

                    # VERIFICARE CORECTĂ: Issue-ul trebuie să fie REAL complet
                    if self.is_issue_really_complete(item):
                        print(f"🏁 Ultimul issue REAL complet din colecție: {url}")
                        return url
                    elif item.get("completed_at"):
                        last_segment = item.get("last_successful_segment_end", 0)
                        total_pages = item.get("total_pages")
                        pages = item.get("pages", 0)
                        print(f"⚠ Issue marcat ca complet dar INCOMPLET: {url} ({last_segment}/{total_pages}, pages: {pages})")

            print("🆕 Niciun issue REAL complet găsit în colecția curentă")
            return None

    def open_new_tab_and_download(self, url):
        """FIXED: Se focusează pe un singur issue până la final cu verificări ultra-safe"""
        normalized_url = url.rstrip('/')

        # DOAR verificările esențiale la început
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

        print(f"\n🎯 ÎNCEP FOCUSAREA PE: {url}")
        print("=" * 60)

        try:
            if not self.attached_existing:
                self.ensure_alive_fallback()

            # Deschide fila nouă
            prev_handles = set(self.driver.window_handles)
            self.driver.execute_script("window.open('');")
            new_handles = set(self.driver.window_handles)
            diff = new_handles - prev_handles
            new_handle = diff.pop() if diff else self.driver.window_handles[-1]
            self.driver.switch_to.window(new_handle)

            if not self.navigate_to_page(url):
                print(f"❌ Nu am putut naviga la {url}")
                return False

            time.sleep(2)

            # Verifică DOAR o dată la început pentru limită
            if self.check_daily_limit_in_all_windows(set_flag=False):
                print("⚠ Pagină cu limită zilnică detectată - opresc aici.")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return False

            print("✅ Pagina e OK, încep extragerea metadatelor...")
            title, subtitle = self.get_issue_metadata()

            # FIXED: Scanează corect fișierele existente pentru acest issue specific
            existing_pages = self.get_existing_pdf_segments(url)
            print(f"📊 Pagini existente pe disk: {existing_pages}")

            resume_from = 1
            json_progress = 0
            for item in self.state.get("downloaded_issues", []):
                if item.get("url") == normalized_url:
                    json_progress = item.get("last_successful_segment_end", 0)
                    total_pages = item.get("total_pages")
                    if json_progress and total_pages and json_progress >= total_pages:
                        resume_from = None
                    break

            actual_progress = max(json_progress, existing_pages)
            if actual_progress > 0 and resume_from is not None:
                resume_from = actual_progress + 1
                print(f"📄 Reiau de la pagina {resume_from} (JSON: {json_progress}, Disk: {existing_pages})")

            if resume_from is None:
                print(f"⏭️ Issue-ul {url} este deja complet.")
                return False

            self.current_issue_url = normalized_url

            # FIXED: Obține total_pages și actualizează progresul
            total_pages = self.get_total_pages()
            if total_pages > 0:
                self._update_partial_issue_progress(normalized_url, actual_progress, total_pages=total_pages, title=title, subtitle=subtitle)
            else:
                print("⚠ Nu am putut obține numărul total de pagini!")

            print(f"🔒 INTRÂND ÎN MODUL FOCUS - nu mai fac alte verificări până nu termin!")

            # ==================== DESCĂRCAREA PROPRIU-ZISĂ ====================
            print(f"📥 ÎNCEPE DESCĂRCAREA pentru {url}...")
            pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)

            print(f"📊 REZULTAT DESCĂRCARE:")
            print(f"   📄 Pagini descărcate: {pages_done}")
            print(f"   📄 Total necesar: {total_pages}")
            print(f"   🛑 Limită zilnică: {limit_hit}")

            if pages_done == 0 and not limit_hit:
                print(f"⚠ Descărcarea pentru {url} a eșuat complet.")
                return False

            if limit_hit:
                print(f"⚠ Limită zilnică atinsă în timpul descărcării pentru {url}; progresul parțial a fost salvat.")
                return False

            # ==================== VERIFICĂRI ULTRA SAFE ÎNAINTE DE FINALIZARE ====================

            print(f"🔍 VERIFICĂRI FINALE ULTRA SAFE pentru {url}...")
            print(f"📊 Rezultat descărcare: {pages_done} pagini din {total_pages}")

            # Verifică dacă total_pages a fost detectat corect
            if total_pages <= 0:
                print(f"❌ OPRIRE SAFETY: total_pages nu a fost detectat corect ({total_pages})")
                print(f"🛡️ NU marchez ca terminat fără total_pages valid")
                print(f"🔄 Păstrez ca parțial cu progres {pages_done}")

                self._update_partial_issue_progress(
                    normalized_url, pages_done, total_pages=None, title=title, subtitle=subtitle
                )
                return True  # Succes parțial

            # VERIFICARE CRITICĂ: Progresul trebuie să fie aproape complet
            completion_percent = (pages_done / total_pages) * 100
            print(f"📊 Completitudine calculată: {completion_percent:.1f}%")

            if completion_percent < 95:  # Cel puțin 95%
                print(f"❌ BLOCARE SAFETY: Progres insuficient pentru marcare ca terminat")
                print(f"📊 Progres: {pages_done}/{total_pages} ({completion_percent:.1f}%)")
                print(f"🛡️ Trebuie cel puțin 95% pentru a marca ca terminat!")
                print(f"🔄 Păstrez ca PARȚIAL pentru continuare ulterioară")

                # Marchează ca parțial, NU ca terminat
                self._update_partial_issue_progress(
                    normalized_url, pages_done, total_pages=total_pages, title=title, subtitle=subtitle
                )

                print(f"💾 Issue {url} păstrat ca parțial: {pages_done}/{total_pages}")
                print(f"🔄 Va fi continuat automat la următoarea rulare")
                return True  # Succes parțial - va continua mai târziu

            # VERIFICARE SUPLIMENTARĂ: Issues mari cu progres mic
            if total_pages >= 500 and pages_done < 200:
                print(f"❌ BLOCARE SPECIALĂ: Issue mare cu progres suspect de mic")
                print(f"📊 {pages_done} pagini din {total_pages} pare eșec de descărcare!")
                print(f"🛡️ Probabil eroare tehnică sau limită - NU marchez terminat")

                self._update_partial_issue_progress(
                    normalized_url, pages_done, total_pages=total_pages, title=title, subtitle=subtitle
                )
                return True  # Succes parțial

            # ===== TOATE VERIFICĂRILE AU TRECUT - SAFE SĂ MARCHEZ CA TERMINAT =====

            print(f"✅ TOATE VERIFICĂRILE ULTRA SAFE au trecut pentru {url}")
            print(f"🎯 Progres: {pages_done}/{total_pages} ({completion_percent:.1f}%)")
            print(f"🎯 Marchez ca TERMINAT COMPLET")

            # PAUZĂ CRITICĂ 1: Așteaptă ca toate fișierele să fie complet scrise pe disk
            print("⏳ SINCRONIZARE: Aștept 30 secunde ca toate fișierele să fie complet salvate pe disk...")
            time.sleep(30)

            # FIXED: Marchează ca terminat cu total_pages corect
            self.mark_issue_done(url, pages_done, title=title, subtitle=subtitle, total_pages=total_pages)
            print(f"✅ Issue marcat ca terminat în JSON: {url} ({pages_done} pagini)")

            # PAUZĂ CRITICĂ 2: Așteaptă ca JSON să fie salvat complet
            print("⏳ SINCRONIZARE: Aștept 5 secunde pentru sincronizarea JSON...")
            time.sleep(5)

            # ==================== PROCESAREA PDF-URILOR ====================
            print(f"🔄 ÎNCEPE PROCESAREA PDF-URILOR pentru {url}...")

            # Verifică din nou că toate fișierele sunt pe disk
            final_segments = self.get_all_pdf_segments_for_issue(url)
            print(f"🔍 VERIFICARE FINALĂ: Am găsit {len(final_segments)} fișiere PDF pentru acest issue")

            if len(final_segments) == 0:
                print(f"⚠ PROBLEMĂ: Nu am găsit fișiere PDF pentru {url}!")
                return False

            # Copiază și combină PDF-urile
            self.copy_and_combine_issue_pdfs(url, title or normalized_url)

            # PAUZĂ CRITICĂ 3: Așteaptă ca procesarea PDF să fie completă
            print("⏳ SINCRONIZARE: Aștept 15 secunde după procesarea PDF-urilor...")
            time.sleep(15)

            # ==================== FINALIZARE COMPLETĂ ====================
            print("=" * 60)
            print(f"🎉 FOCUSAREA COMPLETĂ PE {url} FINALIZATĂ CU SUCCES!")
            print(f"📊 REZULTAT: {pages_done} pagini descărcate și procesate")
            print("=" * 60)

            # PAUZĂ FINALĂ: Înainte să treacă la următorul issue
            print("⏳ PAUZĂ FINALĂ: 10 secunde înainte de următorul issue...")
            time.sleep(10)

            return True

        except WebDriverException as e:
            print(f"❌ Eroare WebDriver pentru {url}: {e}")
            return False
        except Exception as e:
            print(f"❌ Eroare în open_new_tab_and_download pentru {url}: {e}")
            return False
        finally:
            try:
                # NU ÎNCHIDE DACĂ E ULTIMA FEREASTRĂ
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                else:
                    # Doar revine la prima fereastră fără să închidă
                    if self.driver.window_handles:
                        self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception as e:
                print(f"⚠ Eroare în finally: {e}")
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
        """FIXED: Procesează UN SINGUR issue pe rând, fără să sară la altele"""
        print(f"🌐 Încep procesarea colecției: {collection_url}")
        if not self.driver:
            print("❌ Driver neinițializat.")
            return False
        if not self.navigate_to_page(collection_url):
            return False

        # Verifică limita DOAR la început
        if self.state.get("daily_limit_hit", False):
            print("⚠ Nu mai pot continua din cauza limitei zilnice setate anterior.")
            return True

        if self.remaining_quota() <= 0:
            print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă.")
            return True

        issue_links = self.extract_issue_links_from_collection()
        if not issue_links:
            print("⚠ Nu s-au găsit issue-uri în colecție.")
            return False

        # FIXED: Găsește ultimul issue complet din colecție și continuă cu următorul
        last_completed = self.get_last_completed_issue_from_collection(issue_links)
        next_to_process = self.find_next_issue_in_collection_order(issue_links, last_completed)

        if not next_to_process:
            print("✅ Toate issue-urile din această colecție sunt complete!")
            return True

        # Procesează issue-urile începând cu următorul după cel completat
        start_index = issue_links.index(next_to_process)
        pending_links = issue_links[start_index:]

        # Filtrează doar cele care nu sunt în skip list sau complete
        actual_pending = []
        for link in pending_links:
            normalized = link.rstrip('/')
            if normalized in self.dynamic_skip_urls:
                continue
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if not exists or not exists.get("completed_at"):
                actual_pending.append(link)

        print(f"📊 Procesez {len(actual_pending)} issue-uri din colecția curentă (începând cu {next_to_process})")

        # PROCESEAZĂ CÂTE UN ISSUE PE RÂND - fără să sară la altele
        processed_any = False
        for i, link in enumerate(actual_pending):
            print(f"\n🔢 ISSUE {i+1}/{len(actual_pending)}: {link}")

            # Verifică cota DOAR înainte să înceapă un issue nou
            if self.remaining_quota() <= 0:
                print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă înainte de a începe acest issue.")
                break

            if self.state.get("daily_limit_hit", False):
                print("⚠ Flag daily_limit_hit setat - opresc procesarea.")
                break

            # FOCUSEAZĂ PE UN SINGUR ISSUE
            print(f"🎯 Mă focusez EXCLUSIV pe: {link}")
            result = self.open_new_tab_and_download(link)

            if result:
                processed_any = True
                print(f"✅ Issue-ul {link} procesat cu succes!")
            else:
                print(f"⚠ Issue-ul {link} nu a fost procesat.")

            # Verifică din nou cota după procesare
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică atinsă după procesarea acestui issue.")
                break

            # Pauză între issue-uri
            if i < len(actual_pending) - 1:  # Nu pune pauză după ultimul
                print("⏳ Pauză de 2s între issue-uri...")
                time.sleep(2)

        # ACUM VERIFICAREA E DUPĂ BUCLA FOR, NU ÎNĂUNTRUL EI!
        # FIXED: Verifică dacă TOATE issue-urile din această colecție sunt complete
        all_done = True
        total_issues = len(issue_links)
        completed_issues = 0
        pending_issues = []

        for link in issue_links:
            normalized = link.rstrip('/')

            # Verifică în skip URLs (complet descărcate)
            if normalized in self.dynamic_skip_urls:
                completed_issues += 1
                continue

            # Verifică în state.json
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)

            if exists and exists.get("completed_at") and \
               exists.get("total_pages") and \
               exists.get("last_successful_segment_end", 0) >= exists.get("total_pages", 0):
                completed_issues += 1
            else:
                all_done = False
                pending_issues.append(link)

        print(f"📊 VERIFICARE COLECȚIE: {completed_issues}/{total_issues} issue-uri complete")
        if pending_issues:
            print(f"🔄 Issue-uri rămase: {len(pending_issues)}")
            for idx, link in enumerate(pending_issues[:5]):  # Afișează primele 5
                print(f"   {idx+1}. {link}")
            if len(pending_issues) > 5:
                print(f"   ... și încă {len(pending_issues) - 5} issue-uri")

        return all_done

    def process_pending_partials_first(self):
        """FIXED: Procesează mai întâi issue-urile parțiale, indiferent de colecție"""
        pending_partials = self.get_pending_partial_issues()

        if not pending_partials:
            print("✅ Nu există issue-uri parțiale de procesat.")
            return True

        print(f"\n🎯 PRIORITATE: Procesez {len(pending_partials)} issue-uri parțiale:")
        for item in pending_partials:
            url = item.get("url")
            progress = item.get("last_successful_segment_end", 0)
            total = item.get("total_pages", 0)
            print(f"   🔄 {url} - pagini {progress}/{total}")

        # Procesează issue-urile parțiale
        processed_any = False
        for item in pending_partials:
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print(f"⚠ Limita zilnică atinsă în timpul issue-urilor parțiale.")
                break

            url = item.get("url")
            result = self.open_new_tab_and_download(url)
            if result:
                processed_any = True
            time.sleep(1)

        return processed_any

    def run_additional_collections(self):
        """FIXED: Procesează colecțiile adiționale în ordinea corectă"""
        start_index = self.state.get("current_additional_collection_index", 0)

        # VERIFICĂ că indexul e valid
        if start_index >= len(ADDITIONAL_COLLECTIONS):
            print("✅ TOATE colecțiile adiționale au fost procesate!")
            return True

        print(f"🔄 Continuez cu colecțiile adiționale de la indexul {start_index}")

        for i in range(start_index, len(ADDITIONAL_COLLECTIONS)):
            collection_url = ADDITIONAL_COLLECTIONS[i]

            print(f"\n📚 COLECȚIA {i+1}/{len(ADDITIONAL_COLLECTIONS)}: {collection_url}")

            # ADAUGĂ ACEASTĂ VERIFICARE
            if collection_url.rstrip('/') in self.dynamic_skip_urls:
                print(f"⏭️ Sar peste colecția {i+1}/{len(ADDITIONAL_COLLECTIONS)} (deja completă): {collection_url}")
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
                continue

            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print(f"⚠ Limita zilnică atinsă, opresc procesarea colecțiilor adiționale.")
                break

            print(f"\n🔄 Procesez colecția adițională {i+1}/{len(ADDITIONAL_COLLECTIONS)}: {collection_url}")

            self.state["current_additional_collection_index"] = i
            self._save_state()

            collection_completed = self.run_collection(collection_url)

            if collection_completed and not self.state.get("daily_limit_hit", False):
                print(f"✅ Colecția adițională {i+1} completă, o marchez și trec la următoarea.")
                self.mark_collection_complete(collection_url)
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
                print(f"🔄 Continu cu următoarea colecție adițională...")
            elif self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică atinsă - opresc procesarea.")
                break
            else:
                print(f"⚠ Colecția adițională {i+1} nu este completă încă - voi continua cu următoarea!")
                print(f"🔄 Continu cu următoarea colecție adițională...")

        current_index = self.state.get("current_additional_collection_index", 0)
        if current_index >= len(ADDITIONAL_COLLECTIONS):
            print("🎉 TOATE colecțiile adiționale au fost procesate!")
            print("🔄 Voi continua cu următoarea colecție disponibilă...")
            return False  # Returnez False pentru a continua cu următoarea colecție
        else:
            remaining = len(ADDITIONAL_COLLECTIONS) - current_index
            print(f"⚠ Mai rămân {remaining} colecții adiționale de procesat.")
            print("🔄 Voi continua cu următoarea colecție...")
            return False  # Returnez False pentru a continua

    def run(self):
            print("🧪 Încep executarea Chrome PDF Downloader FIXED cu SORTARE CRONOLOGICĂ")
            print("=" * 60)

            try:
                if not self.setup_chrome_driver():
                    return False

                print("🔄 Resetez flag-ul de limită zilnică și verific ferestrele existente...")
                self.state["daily_limit_hit"] = False
                self._save_state()

                # FIXED: Reconstruiește progresul din fișierele de pe disk
                self.sync_json_with_disk_files()

                # CLEANUP dubluri DUPĂ sincronizarea cu disk-ul
                self.cleanup_duplicate_issues()

                # NOUĂ ETAPĂ: Corectează issue-urile marcate greșit ca complete
                print("\n🔧 ETAPA CORECTARE: Verific issue-urile marcate greșit ca complete")
                fixes_applied = self.fix_incorrectly_marked_complete_issues()

                if fixes_applied > 0:
                    print(f"✅ Corectat {fixes_applied} issue-uri - acestea vor fi reluate")

                if self.check_daily_limit_in_all_windows(set_flag=False):
                    print("⚠ Am găsit ferestre cu limita deschise din sesiuni anterioare.")
                    print("🔄 Le-am închis și reîncerc procesarea...")

                # FIXED: ETAPA 0: Procesează MAI ÎNTÂI issue-urile parțiale (PRIORITATE ABSOLUTĂ)
                print(f"\n🎯 ETAPA 0: PRIORITATE ABSOLUTĂ - Procesez issue-urile parțiale")
                if self.process_pending_partials_first():
                    print("✅ Issue-urile parțiale au fost procesate sau limita a fost atinsă.")
                    # OPREȘTE aici dacă există parțiale - nu trece la colecții noi
                    if self.get_pending_partial_issues():
                        print("🔄 Încă mai există issue-uri parțiale - voi continua cu ele următoarea dată")
                        return True

                if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                    print("⚠ Limita zilnică atinsă după procesarea issue-urilor parțiale.")
                    return True

                # ETAPA 1: Procesează colecția principală (dacă nu e completă)
                # FIXED: Verifică întotdeauna dacă colecția principală e completă
                print(f"\n📚 ETAPA 1: Verific colecția principală: {self.main_collection_url}")

                main_completed = self.run_collection(self.main_collection_url)

                if self.state.get("daily_limit_hit", False):
                    print("⚠ Limita zilnică atinsă în colecția principală.")
                    return True

                if main_completed:
                    print("✅ Colecția principală este completă!")
                    self.state["main_collection_completed"] = True
                    self._save_state()
                else:
                    print("🔄 Colecția principală nu este completă încă - continuez cu ea.")
                    self.state["main_collection_completed"] = False  # RESETEAZĂ dacă nu e completă
                    self._save_state()
                    return True

                # ETAPA 2: Procesează colecțiile adiționale
                if self.remaining_quota() > 0 and not self.state.get("daily_limit_hit", False):
                    print(f"\n📚 ETAPA 2: Procesez colecțiile adiționale")
                    self.run_additional_collections()

                print("✅ Toate operațiunile au fost inițiate.")
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
    """
    MAIN FUNCTION CORECTATĂ - FOCUSEAZĂ PE StudiiSiCercetariMecanicaSiAplicata
    Nu mai sare la alte colecții până nu termină cu aceasta complet!
    """

    log_file = setup_logging()  # ADĂUGAT - PRIMA LINIE


    print("🚀 PORNIRE SCRIPT - ANALIZA INIȚIALĂ")
    print("=" * 70)

    # PASUL 1: Creează downloader temporar pentru analiza stării
    temp_downloader = ChromePDFDownloader("temp", download_dir="D:\\", batch_size=50)

    # PASUL 2: Analizează starea curentă
    print("🔍 ANALIZA STĂRII CURENTE:")
    current_state = temp_downloader.state

    main_completed = current_state.get("main_collection_completed", False)
    current_index = current_state.get("current_additional_collection_index", 0)
    total_issues = len(current_state.get("downloaded_issues", []))

    print(f"   📊 Total issues în state: {total_issues}")
    print(f"   🏁 Main collection completed: {main_completed}")
    print(f"   🔢 Current additional index: {current_index}")

    # PASUL 3: Verifică issue-urile parțiale (PRIORITATE ABSOLUTĂ)
    print(f"\n🎯 VERIFICARE ISSUE-URI PARȚIALE:")
    pending_partials = temp_downloader.get_pending_partial_issues()

    if pending_partials:
        print(f"🚨 GĂSITE {len(pending_partials)} ISSUE-URI PARȚIALE!")
        print(f"🔥 PRIORITATE ABSOLUTĂ - acestea trebuie continuate:")

        for item in pending_partials:
            url = item.get("url", "")
            progress = item.get("last_successful_segment_end", 0)
            total = item.get("total_pages", 0)
            title = item.get("title", "")
            print(f"   🔄 {title}")
            print(f"      📍 {url}")
            print(f"      🎯 CONTINUĂ de la pagina {progress + 1} (progres: {progress}/{total})")

        print(f"\n✅ VA PROCESA AUTOMAT issue-urile parțiale primul!")
    else:
        print(f"✅ Nu există issue-uri parțiale de procesat")

    # PASUL 4: Analizează progresul StudiiSiCercetariMecanicaSiAplicata
    print(f"\n📚 ANALIZA COLECȚIEI StudiiSiCercetariMecanicaSiAplicata:")

    # Lista completă a anilor disponibili din HTML (1954-1992, minus 1964)
    expected_years = []
    for year in range(1954, 1993):  # 1954-1992
        if year != 1964:  # 1964 nu există în colecție
            expected_years.append(year)

    # Verifică care ani au fost descărcați
    downloaded_years = []
    partial_years = []

    for item in current_state.get("downloaded_issues", []):
        url = item.get("url", "")
        if "StudiiSiCercetariMecanicaSiAplicata" in url:
            # Extrage anul din URL
            year_match = re.search(r'StudiiSiCercetariMecanicaSiAplicata_(\d{4})', url)
            if year_match:
                year = int(year_match.group(1))
                if item.get("completed_at"):
                    downloaded_years.append(year)
                else:
                    partial_years.append(year)

    downloaded_years.sort()
    partial_years.sort()
    missing_years = [year for year in expected_years if year not in downloaded_years and year not in partial_years]

    print(f"   📅 Ani disponibili: {len(expected_years)} (1954-1992, minus 1964)")
    print(f"   ✅ Ani descărcați: {len(downloaded_years)} - {downloaded_years}")
    print(f"   🔄 Ani parțiali: {len(partial_years)} - {partial_years}")
    print(f"   ❌ Ani lipsă: {len(missing_years)} - {missing_years[:10]}{'...' if len(missing_years) > 10 else ''}")

    # PASUL 5: Determină strategia
    total_remaining = len(partial_years) + len(missing_years)

    if total_remaining > 0:
        print(f"\n🎯 STRATEGIA DE PROCESARE:")
        print(f"   🔥 RĂMÂN {total_remaining} ani de procesat din StudiiSiCercetariMecanicaSiAplicata")
        print(f"   🚫 NU se trece la alte colecții până nu se termină aceasta!")
        print(f"   📈 Progres: {len(downloaded_years)}/{len(expected_years)} ani completați ({len(downloaded_years)/len(expected_years)*100:.1f}%)")
    else:
        print(f"\n✅ StudiiSiCercetariMecanicaSiAplicata este COMPLET!")
        print(f"   🎯 Va trece la următoarea colecție din ADDITIONAL_COLLECTIONS")

    # PASUL 6: Resetează starea pentru a continua corect cu StudiiSiCercetariMecanicaSiAplicata
    if total_remaining > 0:
        print(f"\n🔧 RESETEZ STAREA pentru a continua cu StudiiSiCercetariMecanicaSiAplicata:")

        # Resetează flag-urile greșite
        if main_completed:
            print(f"   🔄 Resetez main_collection_completed: True → False")
            temp_downloader.state["main_collection_completed"] = False

        if current_index > 1:  # StudiiSiCercetariMecanicaSiAplicata e pe index 1
            print(f"   🔄 Resetez current_additional_collection_index: {current_index} → 1")
            temp_downloader.state["current_additional_collection_index"] = 1

        temp_downloader._save_state()
        print(f"   ✅ Starea resetată pentru a continua cu StudiiSiCercetariMecanicaSiAplicata")

    # PASUL 7: Setează URL-ul colecției principale
    main_collection_url = "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMecanicaSiAplicata/"

    print(f"\n🚀 ÎNCEPE PROCESAREA:")
    print(f"📍 URL principal: {main_collection_url}")
    print(f"📁 Director descărcare: D:\\")
    print(f"📦 Batch size: 50 pagini per segment")

    if pending_partials:
        print(f"⚡ Va începe cu {len(pending_partials)} issue-uri parțiale")
    if missing_years:
        print(f"📅 Va continua cu anii lipsă: {missing_years[:5]}{'...' if len(missing_years) > 5 else ''}")

    print("=" * 70)

    # PASUL 8: Creează downloader-ul principal și pornește procesarea
    try:
        downloader = ChromePDFDownloader(
            main_collection_url=main_collection_url,
            download_dir="D:\\",
            batch_size=50
        )

        print("🎯 ÎNCEPE EXECUȚIA PRINCIPALĂ...")
        success = downloader.run()

        if success:
            print("\n✅ EXECUȚIE FINALIZATĂ CU SUCCES!")
        else:
            print("\n⚠ EXECUȚIE FINALIZATĂ CU PROBLEME!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ OPRIRE MANUALĂ - Progresul a fost salvat")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ EROARE FATALĂ în main(): {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Eroare fatală în __main__: {e}")
        sys.exit(1)