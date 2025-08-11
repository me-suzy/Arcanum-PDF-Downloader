#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum cu programare zilnică automată
- Rulează zilnic la ora specificată
- Logging complet în consolă și fișier
- Headless Chrome pentru rulare în background
- Continuă de unde a rămas pe baza JSON-ului
- Opțiuni: --now (rulare imediată), --test (verificare configurație)
"""

import time
import os
import sys
import re
import json
import shutil
import argparse
import logging
import schedule
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException

# ============================================================================
# CONFIGURARE CENTRALIZATĂ
# ============================================================================

DOWNLOAD_DIR = "D:\\"                    # Directorul de descărcare
SCHEDULED_TIME = "09:57"                 # Ora de pornire zilnică (HH:MM)
DAILY_LIMIT = 105                        # Limite zilnice de issue-uri
BATCH_SIZE = 50                          # Pagini per segment PDF
TIMEOUT = 5                              # Timeout pentru operațiuni web distanta timp intre paginile incarcare
LOG_FILE = "download_log.txt"            # Fișier pentru log-uri

STATE_FILENAME = "state.json"            # Fișier pentru starea progresului
SKIP_URLS_FILENAME = "skip_urls.json"    # Fișier pentru URL-uri completate

# Colecțiile adiționale (procesate DUPĂ colecția principală)
ADDITIONAL_COLLECTIONS = [
    "https://adt.arcanum.com/ro/collection/Convietuirea/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMecanicaSiAplicata/",
    "https://adt.arcanum.com/ro/collection/CalitateFiabilitat/",
    "https://adt.arcanum.com/ro/collection/Metrologie/",
    "https://adt.arcanum.com/ro/collection/MetrologiaAplicata/",
    "https://adt.arcanum.com/ro/collection/AnaleleUnivBucuresti_GeologieGeografie/",
    "https://adt.arcanum.com/ro/collection/BuletinulStiintificTechnicInstitutuluiPolitehnicTimisoara_MatematicaFizicaMecanica/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMatematice/",
    "https://adt.arcanum.com/ro/collection/AnaleleUnivBucuresti_MatematicaMecanicaFizica/",
    "https://adt.arcanum.com/ro/collection/RevistaMatematicaDinTimisoara/",
    "https://adt.arcanum.com/ro/collection/BuletInstPolitehIasi_1/",
    "https://adt.arcanum.com/ro/collection/Energetica/",
    "https://adt.arcanum.com/ro/collection/CulturaFizicaSiSport/",
    "https://adt.arcanum.com/ro/collection/Almanahul_Satelor/",
    "https://adt.arcanum.com/ro/collection/RevistaDeFolclor/",
    "https://adt.arcanum.com/ro/collection/AlmanahBTT/",
    "https://adt.arcanum.com/ro/collection/MinePetrolGaze/",
    "https://adt.arcanum.com/ro/collection/BuletinulInstitutuluiPolitehnicBucuresti_Mecanica/",
    "https://adt.arcanum.com/ro/collection/RevistaMinelor/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariDeGeologie/",
    "https://adt.arcanum.com/ro/collection/RevistaIndustriaAlimentare/",
    "https://adt.arcanum.com/en/collection/RevistaMinelor/",
    "https://adt.arcanum.com/ro/collection/IndustriaLemnului/",
    "https://adt.arcanum.com/en/collection/ProblemeDeInformareSiDocumentare/",
    "https://adt.arcanum.com/ro/collection/Electricitatea/",
    "https://adt.arcanum.com/ro/collection/SzatmariMuzeumKiadvanyai_Evkonyv_ADT/",
    "https://adt.arcanum.com/ro/collection/ConstructiaDeMasini/",
    "https://adt.arcanum.com/en/collection/IdeiInDialog/",
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
    "https://adt.arcanum.com/ro/collection/RenastereaBanateana/?decade=1980#collection-contents",
    "https://adt.arcanum.com/ro/collection/RenastereaBanateana/?decade=1990#collection-contents",
    "https://adt.arcanum.com/ro/collection/RenastereaBanateana/?decade=2000#collection-contents",
    "https://adt.arcanum.com/ro/collection/RenastereaBanateana/?decade=2010#collection-contents",
    "https://adt.arcanum.com/ro/collection/GazetaDeDuminica/",
    "https://adt.arcanum.com/ro/collection/BuletInstPolitehIasi_0/",
    "https://adt.arcanum.com/ro/collection/BuletinulOficial/?decade=1950#collection-contents",
    "https://adt.arcanum.com/ro/collection/BuletinulOficial/?decade=1960#collection-contents",
    "https://adt.arcanum.com/ro/collection/BuletinulOficial/?decade=1970#collection-contents",
    "https://adt.arcanum.com/ro/collection/BuletinulOficial/?decade=1980#collection-contents",
    "https://adt.arcanum.com/ro/collection/JurnalulNational/",
    "https://adt.arcanum.com/ro/collection/MonitorulOficial/?decade=1910#collection-contents",
    "https://adt.arcanum.com/ro/collection/MonitorulOficial/?decade=1920#collection-contents",
    "https://adt.arcanum.com/ro/collection/MonitorulOficial/?decade=1930#collection-contents",
    "https://adt.arcanum.com/ro/collection/MonitorulOficial/?decade=1940#collection-contents",
    "https://adt.arcanum.com/ro/collection/GraiulSalajului/?decade=1980#collection-contents",
    "https://adt.arcanum.com/ro/collection/GraiulSalajului/?decade=1990#collection-contents",
    "https://adt.arcanum.com/ro/collection/GraiulSalajului/?decade=2000#collection-contents",
    "https://adt.arcanum.com/ro/collection/GraiulSalajului/?decade=2010#collection-contents",
    "https://adt.arcanum.com/ro/collection/GraiulSalajului/?decade=2020#collection-contents",
    "https://adt.arcanum.com/ro/collection/EvenimentulZilei/?decade=1990#collection-contents",
    "https://adt.arcanum.com/ro/collection/EvenimentulZilei/?decade=2000#collection-contents",
    "https://adt.arcanum.com/ro/collection/EvenimentulZilei/?decade=2010#collection-contents",
    "https://adt.arcanum.com/ro/collection/TineretulLiber_OSA/?decade=1980#collection-contents",
    "https://adt.arcanum.com/ro/collection/TineretulLiber_OSA/?decade=1990#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=1950#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=1960#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=1970#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=1980#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=1990#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=2000#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=2010#collection-contents",
    "https://adt.arcanum.com/ro/collection/RomaniaLiterara/?decade=2020#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1880#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1890#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1900#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1910#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1920#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1930#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1940#collection-contents",
    "https://adt.arcanum.com/ro/collection/Adeverul/?decade=1950#collection-contents",
    "https://adt.arcanum.com/ro/collection/UnireaBlajPoporului/",
    "https://adt.arcanum.com/ro/collection/TranssylvaniaNostra/",
    "https://adt.arcanum.com/ro/collection/CuvantulPoporului/",
    "https://adt.arcanum.com/ro/collection/Agrarul/",
    "https://adt.arcanum.com/ro/collection/CurierulFoaiaIntereselorGenerale/",
    "https://adt.arcanum.com/ro/collection/EconomiaNationala/",
    "https://adt.arcanum.com/ro/collection/Constitutionalul/"
]

# Skip URLs statice (hardcoded)
STATIC_SKIP_URLS = {
    "https://adt.arcanum.com/ro/view/Convietuirea_1997-1998"
}

# ============================================================================
# SETUP LOGGING
# ============================================================================

class DualLogger:
    """Logger care scrie atât în consolă cât și în fișier cu timestampuri"""

    def __init__(self, log_file_path):
        self.log_file_path = log_file_path

        # Configurează logging pentru fișier
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)

# Logger global
logger = None

def log_print(message, level="info"):
    """Wrapper pentru logging cu print ca fallback"""
    if logger:
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")

# ============================================================================
# CLASA PRINCIPALĂ
# ============================================================================

class ScheduledPDFDownloader:
    def __init__(self, main_collection_url, download_dir=None, batch_size=50, timeout=15, headless=True):
        self.main_collection_url = main_collection_url
        self.batch_size = batch_size
        self.timeout = timeout
        self.download_dir = download_dir or DOWNLOAD_DIR
        self.headless = headless
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
        self.dynamic_skip_urls = set(STATIC_SKIP_URLS)

        if os.path.exists(self.skip_urls_path):
            try:
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    completed_urls = data.get("completed_urls", [])
                    completed_collections = data.get("completed_collections", [])

                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_urls)
                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_collections)

                    log_print(f"📋 Încărcat {len(completed_urls)} URL-uri complet descărcate din {SKIP_URLS_FILENAME}")
                    log_print(f"📋 Încărcat {len(completed_collections)} colecții complet procesate din {SKIP_URLS_FILENAME}")
            except Exception as e:
                log_print(f"⚠ Eroare la citirea {SKIP_URLS_FILENAME}: {e}", "error")

        log_print(f"🚫 Total URL-uri de skip: {len(self.dynamic_skip_urls)}")

    def _save_skip_urls(self):
        """Salvează skip URLs în fișierul separat - ADAUGĂ, nu suprascrie"""
        try:
            # CITEȘTE SKIP URLS EXISTENTE
            existing_data = {"completed_urls": [], "completed_collections": []}
            if os.path.exists(self.skip_urls_path):
                with open(self.skip_urls_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)

            # ADAUGĂ NOILE URL-URI COMPLETATE
            new_completed_urls = []
            for item in self.state.get("downloaded_issues", []):
                if (item.get("completed_at") and
                    item.get("total_pages") and
                    item.get("last_successful_segment_end", 0) >= item.get("total_pages", 0)):
                    new_completed_urls.append(item["url"])

            # COMBINĂ CU CELE EXISTENTE + STATIC
            all_existing = set(existing_data.get("completed_urls", []))
            all_existing.update(STATIC_SKIP_URLS)
            all_existing.update(new_completed_urls)

            data = {
                "last_updated": datetime.now().isoformat(),
                "completed_urls": sorted(list(all_existing)),
                "completed_collections": existing_data.get("completed_collections", [])
            }

            with open(self.skip_urls_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_print(f"💾 Salvat {len(data['completed_urls'])} URL-uri în {SKIP_URLS_FILENAME} (adăugate {len(new_completed_urls)} noi)")
        except Exception as e:
            log_print(f"⚠ Eroare la salvarea {SKIP_URLS_FILENAME}: {e}", "error")

    def _safe_folder_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

    def _decode_unicode_escapes(self, obj):
        """Decodifică secvențele unicode din JSON"""
        if isinstance(obj, dict):
            return {key: self._decode_unicode_escapes(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._decode_unicode_escapes(item) for item in obj]
        elif isinstance(obj, str):
            try:
                return obj.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8') if '\\u' in obj else obj
            except:
                return obj
        else:
            return obj

    def is_issue_complete_by_end_page(self, end_page):
        """Determină dacă un issue e complet pe baza ultimei pagini"""
        return not ((end_page + 1) % 50 == 0 or (end_page + 1) % 100 == 0)

    def extract_issue_url_from_filename(self, filename):
        """Extrage URL-ul issue-ului din numele fișierului"""
        match = re.search(r'([^-]+(?:-[^-]+)*)-\d+__pages', filename)
        if match:
            issue_id = match.group(1)
            if "Convietuirea" in issue_id:
                return f"https://adt.arcanum.com/ro/view/{issue_id}"
            elif "GazetaMatematica" in issue_id:
                return f"https://adt.arcanum.com/en/view/{issue_id}"
            else:
                return f"https://adt.arcanum.com/ro/view/{issue_id}"
        return None

    def get_existing_pdf_segments(self, issue_url):
        """Scanează folderul pentru PDF-uri existente și returnează ultimul segment descărcat"""
        issue_id = issue_url.rstrip('/').split('/')[-1]
        title = next((item["title"] for item in self.state.get("downloaded_issues", []) if item.get("url") == issue_url.rstrip('/')), "")
        max_page = 0

        try:
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf'):
                    if (issue_id in filename or (title and title.replace(" ", "").lower() in filename.lower().replace(" ", ""))):
                        match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
                        if match:
                            start_page = int(match.group(1))
                            end_page = int(match.group(2))
                            if end_page > max_page:
                                max_page = end_page
                            log_print(f"📁 Găsit PDF existent: {filename} (pagini {start_page}-{end_page})")
        except Exception as e:
            log_print(f"⚠ Eroare la scanarea fișierelor: {e}", "error")

        return max_page

    def sync_json_with_disk_files(self):
        """Combină informațiile din JSON cu fișierele de pe disk"""
        log_print("🔄 Sincronizez JSON-ul cu fișierele de pe disk...")

        try:
            existing_issues = {}
            for item in self.state.get("downloaded_issues", []):
                url = item.get("url", "").rstrip('/')
                existing_issues[url] = item.copy()

            pdf_files = {}
            for filename in os.listdir(self.download_dir):
                if filename.lower().endswith('.pdf'):
                    match = re.search(r'([^-]+(?:-[^-]+)*)-\d+__pages(\d+)-(\d+)\.pdf', filename)
                    if match:
                        issue_id = match.group(1)
                        start_page = int(match.group(2))
                        end_page = int(match.group(3))

                        file_path = os.path.join(self.download_dir, filename)
                        try:
                            mod_time = os.path.getmtime(file_path)
                        except Exception:
                            mod_time = 0

                        if issue_id not in pdf_files:
                            pdf_files[issue_id] = {
                                "max_page": 0,
                                "files": [],
                                "latest_mod_time": 0,
                                "url": self.extract_issue_url_from_filename(filename)
                            }

                        pdf_files[issue_id]["files"].append((start_page, end_page, filename))
                        if end_page > pdf_files[issue_id]["max_page"]:
                            pdf_files[issue_id]["max_page"] = end_page
                        if mod_time > pdf_files[issue_id]["latest_mod_time"]:
                            pdf_files[issue_id]["latest_mod_time"] = mod_time

            for issue_id, data in pdf_files.items():
                max_page = data["max_page"]
                files = data["files"]
                latest_time = data["latest_mod_time"]
                issue_url = data["url"]

                if not issue_url:
                    continue

                is_complete = self.is_issue_complete_by_end_page(max_page)

                if issue_url in existing_issues:
                    issue = existing_issues[issue_url]
                    if max_page > issue.get("last_successful_segment_end", 0):
                        issue["last_successful_segment_end"] = max_page
                        log_print(f"🔄 Actualizat progres din disk: {issue_url} → {max_page} pagini")

                    if is_complete and not issue.get("completed_at"):
                        issue["completed_at"] = datetime.now().isoformat(timespec="seconds")
                        issue["pages"] = max_page
                        issue["total_pages"] = max_page
                        log_print(f"✅ Marcat ca complet din disk: {issue_url}")

                    issue["_sort_time"] = latest_time
                else:
                    existing_issues[issue_url] = {
                        "url": issue_url,
                        "title": issue_id.replace("-", " ").replace("_", " "),
                        "subtitle": "",
                        "pages": max_page if is_complete else 0,
                        "completed_at": datetime.now().isoformat(timespec="seconds") if is_complete else "",
                        "last_successful_segment_end": max_page,
                        "total_pages": max_page if is_complete else None,
                        "_sort_time": latest_time
                    }
                    log_print(f"➕ Adăugat issue nou din disk: {issue_url} → {max_page} pagini")

                for start, end, fname in files:
                    log_print(f"   📄 {fname} (pagini {start}-{end})")

            partial_issues = []
            complete_issues = []

            for issue in existing_issues.values():
                if "_sort_time" in issue:
                    sort_time = issue.pop("_sort_time")
                else:
                    sort_time = 0

                is_partial = (issue.get("last_successful_segment_end", 0) > 0 and
                             not issue.get("completed_at") and
                             issue.get("total_pages") and
                             issue.get("last_successful_segment_end", 0) < issue.get("total_pages", 0))

                issue["_sort_key"] = sort_time

                if is_partial:
                    partial_issues.append(issue)
                    log_print(f"🔄 Issue parțial: {issue['url']} ({issue.get('last_successful_segment_end', 0)}/{issue.get('total_pages', 0)} pagini)")
                else:
                    complete_issues.append(issue)

            partial_issues.sort(key=lambda x: x.get("_sort_key", 0), reverse=True)
            complete_issues.sort(key=lambda x: x.get("_sort_key", 0), reverse=True)

            final_issues = partial_issues + complete_issues

            for issue in final_issues:
                if "_sort_key" in issue:
                    del issue["_sort_key"]

            self.state["downloaded_issues"] = final_issues
            completed_count = len([i for i in final_issues if i.get("completed_at")])
            self.state["count"] = completed_count

            self._save_state()
            self._save_skip_urls()

            partial_count = len(partial_issues)
            log_print(f"✅ Sincronizare completă: {partial_count} issue-uri parțiale, {len(complete_issues)} complete")
            if partial_count > 0:
                log_print("🎯 Issue-urile parțiale vor fi procesate primele!")

        except Exception as e:
            log_print(f"⚠ Eroare la sincronizarea cu disk-ul: {e}", "error")

    def get_pending_partial_issues(self):
        """Returnează lista issue-urilor parțiale care trebuie continuate"""
        pending_partials = []

        for item in self.state.get("downloaded_issues", []):
            url = item.get("url", "").rstrip('/')
            last_segment = item.get("last_successful_segment_end", 0)
            total_pages = item.get("total_pages")
            completed_at = item.get("completed_at", "")

            if url in self.dynamic_skip_urls:
                continue

            if (last_segment > 0 and
                not completed_at and
                total_pages and
                last_segment < total_pages):

                pending_partials.append(item)
                log_print(f"🔄 Issue parțial găsit: {url} (pagini {last_segment}/{total_pages})")

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

                if loaded.get("date") == today:
                    issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))
                    self.state = {
                        "date": loaded.get("date", today),
                        "count": len([i for i in issues if i.get("completed_at")]),
                        "downloaded_issues": issues,
                        "pages_downloaded": loaded.get("pages_downloaded", 0),
                        "recent_links": loaded.get("recent_links", []),
                        "daily_limit_hit": loaded.get("daily_limit_hit", False),
                        "main_collection_completed": loaded.get("main_collection_completed", False),
                        "current_additional_collection_index": loaded.get("current_additional_collection_index", 0)
                    }
                else:
                    old_issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))
                    partial_issues = []
                    completed_issues = []

                    for issue in old_issues:
                        last_segment = issue.get("last_successful_segment_end", 0)
                        total_pages = issue.get("total_pages")
                        completed_at = issue.get("completed_at", "")

                        if (last_segment > 0 and not completed_at and total_pages and last_segment < total_pages):
                            log_print(f"📋 Păstrez progresul parțial pentru: {issue['url']} (pagini {last_segment}/{total_pages})")
                            partial_issues.append(issue)
                        elif completed_at:  # PĂSTREAZĂ TOATE ISSUE-URILE COMPLETATE
                            completed_issues.append(issue)

                    # PĂSTREAZĂ ISSUE-URILE COMPLETATE + PARȚIALE
                    all_preserved_issues = partial_issues + completed_issues

                    self.state = {
                        "date": today,
                        "count": len(completed_issues),  # Numără doar cele completate
                        "downloaded_issues": all_preserved_issues,  # ✅ PĂSTREAZĂ TOT
                        "pages_downloaded": loaded.get("pages_downloaded", 0),  # PĂSTREAZĂ PROGRESUL
                        "recent_links": loaded.get("recent_links", [])[:10],  # Păstrează ultimele 10
                        "daily_limit_hit": False,
                        "main_collection_completed": loaded.get("main_collection_completed", False),
                        "current_additional_collection_index": loaded.get("current_additional_collection_index", 0)
                    }

                    if all_preserved_issues:
                        log_print(f"🔄 Zi nouă detectată. Păstrez {len(completed_issues)} issue-uri completate + {len(partial_issues)} parțiale.")
                    else:
                        log_print(f"🆕 Zi nouă detectată. Încep cu stare curată.")

            except Exception as e:
                log_print(f"⚠ Eroare la citirea stării ({e}), resetez.", "error")
                self.state = default

        self._save_state()

    def _save_state(self):
        try:
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log_print(f"⚠ Nu am putut salva state-ul: {e}", "error")

    def fix_existing_json(self):
        """Funcție temporară pentru a repara caracterele din JSON existent"""
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                data = self._decode_unicode_escapes(data)

                with open(self.state_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                log_print("✅ JSON reparat cu caractere românești")
            except Exception as e:
                log_print(f"⚠ Eroare la repararea JSON: {e}", "error")

    def remaining_quota(self):
        return max(0, DAILY_LIMIT - self.state.get("count", 0))

    def _update_partial_issue_progress(self, issue_url, last_successful_segment_end, total_pages=None, title=None, subtitle=None):
        normalized = issue_url.rstrip('/')
        updated = False

        for i, item in enumerate(self.state.setdefault("downloaded_issues", [])):
            if item["url"] == normalized:
                item["last_successful_segment_end"] = last_successful_segment_end
                if total_pages is not None:
                    item["total_pages"] = total_pages
                if title:
                    item["title"] = title
                if subtitle:
                    item["subtitle"] = subtitle

                updated_item = self.state["downloaded_issues"].pop(i)
                self.state["downloaded_issues"].insert(0, updated_item)
                updated = True
                break

        if not updated:
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
            log_print(f"➕ Adăugat issue nou în progres: {normalized}")

        self._save_state()
        log_print(f"💾 Progres parțial salvat: {normalized} - pagini {last_successful_segment_end}/{total_pages or '?'}")

    def mark_issue_done(self, issue_url, pages_count, title=None, subtitle=None, total_pages=None):
        normalized = issue_url.rstrip('/')
        now_iso = datetime.now().isoformat(timespec="seconds")
        existing = None
        existing_index = -1

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
            existing.update(record)
            completed_item = self.state["downloaded_issues"].pop(existing_index)
            self.state["downloaded_issues"].insert(0, completed_item)
        else:
            self.state["downloaded_issues"].insert(0, record)

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
        self.state.setdefault("recent_links", []).insert(0, recent_entry)
        self.state["daily_limit_hit"] = False

        self.dynamic_skip_urls.add(normalized)

        self._save_state()
        self._save_skip_urls()
        log_print(f"✅ Issue marcat ca terminat: {normalized} ({pages_count} pagini)")

    def mark_collection_complete(self, collection_url):
        """Marchează o colecție ca fiind complet procesată în skip_urls.json"""
        try:
            normalized_collection = collection_url.rstrip('/')

            self.dynamic_skip_urls.add(normalized_collection)

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

                log_print(f"✅ Colecția marcată ca completă: {normalized_collection}")
        except Exception as e:
            log_print(f"⚠ Eroare la marcarea colecției complete: {e}", "error")

    def setup_chrome_driver(self):
        try:
            log_print("🔧 Încerc să mă conectez la Chrome-ul existent...")

            # OPȚIUNEA 1: Încearcă să se conecteze la instanța existentă
            try:
                chrome_options = Options()
                chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

                # Setează preferințele pentru descărcare
                prefs = {
                    "download.default_directory": os.path.abspath(self.download_dir),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True,
                    "profile.default_content_setting_values.notifications": 2,
                }
                chrome_options.add_experimental_option("prefs", prefs)

                self.driver = webdriver.Chrome(options=chrome_options)
                self.attached_existing = True
                log_print("✅ M-am conectat la Chrome-ul existent cu debugging port 9222")

            except Exception as e:
                log_print(f"⚠ Nu m-am putut conecta la Chrome-ul existent: {e}", "warning")
                log_print("🔧 Pornesc instanță nouă cu același profil...")

                # OPȚIUNEA 2: Deschide nouă instanță cu același profil
                prefs = {
                    "download.default_directory": os.path.abspath(self.download_dir),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "safebrowsing.enabled": True,
                    "profile.default_content_setting_values.notifications": 2,
                }

                chrome_options = Options()
                chrome_options.add_experimental_option("prefs", prefs)

                # Folosește același profil ca în .bat
                chrome_options.add_argument("--user-data-dir=C:/Users/necul/AppData/Local/Google/Chrome/User Data")
                chrome_options.add_argument("--profile-directory=Default")

                # Debugging și stabilitate
                chrome_options.add_argument("--remote-debugging-port=9223")  # Port diferit
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")

                if self.headless:
                    log_print("⚠️ DEBUGGING: Rulez în mod VIZIBIL pentru debugging")
                    chrome_options.add_argument("--window-size=1920,1080")
                else:
                    chrome_options.add_argument("--start-maximized")

                # Anti-detection
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)

                self.driver = webdriver.Chrome(options=chrome_options)
                self.attached_existing = False
                log_print("✅ Instanță nouă Chrome cu același profil")

            # Setări comune pentru ambele cazuri - FĂRĂ JAVASCRIPT
            self.driver.set_page_load_timeout(5)  # 10 secunde pentru încărcarea paginii
            self.driver.implicitly_wait(3)        # 10 secunde pentru găsirea elementelor

            self.wait = WebDriverWait(self.driver, self.timeout)
            log_print("✅ Enhanced Chrome driver setup complete")
            return True

        except WebDriverException as e:
            log_print(f"❌ WebDriver setup failed: {e}", "error")
            return False

    def navigate_to_page(self, url):
        try:
            log_print(f"🌐 Navighez către: {url}")
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))
            log_print("✅ Pagina încărcată.")
            return True
        except Exception as e:
            log_print(f"❌ Eroare la navigare sau încărcare: {e}", "error")
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

    def get_total_pages(self, max_attempts=8, delay_between=3.0):
        """Enhanced total pages detection with multiple strategies"""
        for attempt in range(1, max_attempts + 1):
            try:
                log_print(f"🔍 Attempt {attempt}/{max_attempts} to detect page count")

                # STRATEGY 1: Original method
                elems = self.driver.find_elements(By.CSS_SELECTOR, 'div.MuiInputAdornment-root.MuiInputAdornment-positionEnd')
                for el in elems:
                    text = el.text.strip()
                    match = re.search(r'/\s*(\d+)', text)
                    if match:
                        total = int(match.group(1))
                        log_print(f"✅ (Strategy 1) Total pages detected: {total}")
                        return total

                # STRATEGY 2: Check existing state first (for resumed downloads)
                if self.current_issue_url:
                    for item in self.state.get("downloaded_issues", []):
                        if item.get("url") == self.current_issue_url.rstrip('/'):
                            total_pages = item.get("total_pages")
                            if total_pages and total_pages > 0:
                                log_print(f"✅ (Strategy 2 - Cached) Using saved page count: {total_pages}")
                                return total_pages

                # STRATEGY 3: Enhanced text search
                all_texts = self.driver.find_elements(By.XPATH, "//*[contains(text(), '/')]")
                for el in all_texts:
                    text = el.text.strip()
                    # Look for patterns like "299 / 1407" or "Page 299 of 1407"
                    patterns = [
                        r'(\d+)\s*/\s*(\d+)',
                        r'page\s+\d+\s+of\s+(\d+)',
                        r'(\d+)\s+of\s+(\d+)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            # Get the larger number (likely total pages)
                            numbers = [int(g) for g in match.groups() if g.isdigit()]
                            if numbers:
                                total = max(numbers)
                                if total > 100:  # Reasonable page count
                                    log_print(f"✅ (Strategy 3) Total pages from text '{text}': {total}")
                                    return total

                # STRATEGY 4: JavaScript deep search
                # ÎNLOCUIEȘTE CU (adaugă 'r' înainte de ghilimele):
                js_result = self.driver.execute_script(r"""
                    const patterns = [
                        /(\d+)\s*\/\s*(\d+)/g,
                        /page\s+\d+\s+of\s+(\d+)/gi,
                        /total[:\s]+(\d+)/gi
                    ];

                    const bodyText = document.body.innerText;
                    const results = [];

                    for(let pattern of patterns) {
                        let match;
                        while((match = pattern.exec(bodyText)) !== null) {
                            const nums = match.slice(1).map(n => parseInt(n)).filter(n => !isNaN(n));
                            if(nums.length > 0) {
                                results.push(Math.max(...nums));
                            }
                        }
                    }

                    // Return the largest reasonable number
                    const validResults = results.filter(n => n > 100 && n < 10000);
                    return validResults.length > 0 ? Math.max(...validResults) : null;
                """)

                if js_result:
                    log_print(f"✅ (Strategy 4 - JavaScript) Total pages detected: {js_result}")
                    return js_result

                # STRATEGY 5: Manual override for known issues
                # Add specific cases for problematic URLs
                if self.current_issue_url:
                    issue_id = self.current_issue_url.split('/')[-1]
                    known_totals = {
                        "StudiiSiCercetariMecanicaSiAplicata_1957": 1407,
                        # Add more known problematic issues here
                    }
                    if issue_id in known_totals:
                        total = known_totals[issue_id]
                        log_print(f"✅ (Strategy 5 - Manual) Using known total for {issue_id}: {total}")
                        # Save this to state for future use
                        self._update_partial_issue_progress(self.current_issue_url,
                            self.get_existing_pdf_segments(self.current_issue_url), total_pages=total)
                        return total

                log_print(f"⚠ Attempt {attempt} failed, retrying in {delay_between}s...")
                time.sleep(delay_between)

                # Try to refresh the page elements
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)

            except Exception as e:
                log_print(f"⚠ Attempt {attempt} error: {e}", "warning")
                time.sleep(delay_between)

        log_print("❌ Could not detect total pages after all attempts", "error")
        return 0

    def open_save_popup(self):
        try:
            try:
                WebDriverWait(self.driver, 3).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div.MuiDialog-container')))
            except Exception:
                self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                time.sleep(0.2)

            svg = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'svg[data-testid="SaveAltIcon"]')))
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
                    log_print(f"⚠ click interceptat (încercarea {attempt}), trimit ESC și reiau...", "warning")
                    self.driver.switch_to.active_element.send_keys(Keys.ESCAPE)
                    time.sleep(1)
                    continue

            log_print("❌ Nu am reușit să dau click pe butonul de deschidere a popup-ului după retry-uri.", "error")
            return False

        except Exception as e:
            log_print(f"❌ Nu am reușit să deschid popup-ul de salvare: {e}", "error")
            return False

    def fill_and_save_range(self, start, end):
        try:
            first_input = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "first page")))

            log_print("⏳ Aștept 0.5s înainte de a completa primul input...")
            time.sleep(0.5)

            first_input.send_keys(Keys.CONTROL + "a")
            first_input.send_keys(str(start))
            log_print(f"✏️ Am introdus primul număr: {start}")

            log_print("⏳ Aștept 0.5s înainte de a completa al doilea input...")
            time.sleep(0.5)

            last_input = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.ID, "last page")))
            last_input.send_keys(Keys.CONTROL + "a")
            last_input.send_keys(str(end))
            log_print(f"✏️ Am introdus al doilea număr: {end}")

            log_print("⏳ Aștept 0.5s înainte de a apăsa butonul de salvare...")
            time.sleep(0.5)

            save_btn = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((
                By.XPATH,
                '//button[.//text()[contains(normalize-space(.), "Salvați") or contains(normalize-space(.), "Save")]]'
            )))
            save_btn.click()
            log_print(f"✅ Segmentul {start}-{end} salvat.")
            return True

        except Exception as e:
            log_print(f"❌ Eroare la completarea/salvarea intervalului {start}-{end}: {e}", "error")
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
                        log_print(f"⚠ Limita zilnică detectată în fereastra: {handle}", "warning")
                        limit_reached = True

                        if handle != current_window and len(all_handles) > 1:
                            log_print(f"🗙 Închid fereastra cu limita zilnică: {handle}")
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
            log_print(f"⚠ Eroare la verificarea ferestrelor: {e}", "warning")

        if limit_reached and set_flag:
            self.state["daily_limit_hit"] = True
            self._save_state()

        return limit_reached

    def check_for_daily_limit_popup(self):
        """Verifică dacă s-a deschis o filă nouă cu mesajul de limită zilnică după descărcare"""
        try:
            current_handles = set(self.driver.window_handles)

            for handle in current_handles:
                try:
                    self.driver.switch_to.window(handle)
                    body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()

                    if "Daily download limit reached" in body_text:
                        log_print(f"🛑 LIMITĂ ZILNICĂ DETECTATĂ în filă nouă: {handle}", "warning")
                        log_print(f"📄 Conținut filă: {body_text}")

                        self.driver.close()

                        if self.driver.window_handles:
                            self.driver.switch_to.window(self.driver.window_handles[0])

                        self.state["daily_limit_hit"] = True
                        self._save_state()
                        return True

                except Exception as e:
                    continue

            return False

        except Exception as e:
            log_print(f"⚠ Eroare la verificarea popup-ului de limită: {e}", "warning")
            return False

    def save_page_range(self, start, end, retries=1):
        """Verifică limita zilnică după fiecare segment descărcat"""
        for attempt in range(1, retries + 2):
            log_print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")

            if not self.open_save_popup():
                log_print(f"⚠ Eșec la deschiderea popup-ului pentru {start}-{end}", "warning")
                time.sleep(1)
                continue

            success = self.fill_and_save_range(start, end)
            if success:
                log_print("⏳ Aștept 5s pentru finalizarea descărcării segmentului...")
                time.sleep(5)

                if self.check_for_daily_limit_popup():
                    log_print(f"🛑 OPRIRE INSTANT - Limită zilnică detectată după segmentul {start}-{end}", "warning")
                    return False

                log_print(f"✅ Segmentul {start}-{end} descărcat cu succes")
                return True
            else:
                log_print(f"⚠ Retry pentru segmentul {start}-{end}", "warning")
                time.sleep(1)
        log_print(f"❌ Renunț la segmentul {start}-{end} după {retries+1} încercări.", "error")
        return False

    def save_all_pages_in_batches(self, resume_from=1):
        """Oprește instant la detectarea limitei zilnice"""
        total = self.get_total_pages()
        if total <= 0:
            log_print("⚠ Nu am obținut numărul total de pagini; nu pot continua.", "warning")
            return 0, False

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

        log_print(f"🎯 FOCUSEZ PE ACEST ISSUE: Voi descărca {len(segments)} segmente fără întreruperi")

        for (start, end) in segments:
            log_print(f"📦 Procesez segmentul {start}-{end}")
            result = self.save_page_range(start, end, retries=1)

            if not result:
                if self.state.get("daily_limit_hit", False):
                    log_print(f"🛑 OPRIRE INSTANT - Limită zilnică atinsă la segmentul {start}-{end}", "warning")
                    return last_successful_page, True

                log_print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc acest issue.", "error")
                return last_successful_page, False

            last_successful_page = end
            self._update_partial_issue_progress(self.current_issue_url, end, total_pages=total)
            log_print(f"✅ Progres real salvat: pagini până la {end}")
            time.sleep(1)

        log_print("🎯 Toate segmentele au fost procesate pentru acest issue.")
        return total, False

    def extract_issue_links_from_collection(self):
        """Enhanced link extraction with multiple fallback strategies"""
        try:
            # Wait longer and ensure page is fully loaded
            log_print("🔍 Extracting collection links with enhanced method...")

            # Wait for basic page structure
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                time.sleep(5)  # Additional wait for dynamic content
            except TimeoutException:
                log_print("⚠ Timeout waiting for page body", "warning")

            # STRATEGY 1: Original method with longer wait
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.list-group'))
                )
                anchors = self.driver.find_elements(By.CSS_SELECTOR,
                    'li.list-group-item a[href^="/view/"], li.list-group-item a[href^="/en/view/"], li.list-group-item a[href^="/ro/view/"]')

                if anchors:
                    links = []
                    for a in anchors:
                        href = a.get_attribute("href")
                        if href and '/view/' in href:
                            normalized = href.split('?')[0].rstrip('/')
                            links.append(normalized)

                    if links:
                        unique = self._deduplicate_links(links)
                        log_print(f"✅ (Strategy 1) Found {len(unique)} links")
                        return unique
            except Exception as e:
                log_print(f"⚠ Strategy 1 failed: {e}", "warning")

            # STRATEGY 2: Broader search
            try:
                all_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/view/"]')
                links = []
                for a in all_links:
                    href = a.get_attribute("href")
                    if href and '/view/' in href and not any(skip in href for skip in ['#', 'javascript:']):
                        normalized = href.split('?')[0].rstrip('/')
                        links.append(normalized)

                if links:
                    unique = self._deduplicate_links(links)
                    log_print(f"✅ (Strategy 2) Found {len(unique)} links")
                    return unique
            except Exception as e:
                log_print(f"⚠ Strategy 2 failed: {e}", "warning")

            # STRATEGY 3: Scroll and retry
            try:
                log_print("🔄 Trying scroll strategy...")
                # Scroll to bottom to load any lazy content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

                # Retry original search
                anchors = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/view/"]')
                if anchors:
                    links = []
                    for a in anchors:
                        href = a.get_attribute("href")
                        if href and '/view/' in href:
                            normalized = href.split('?')[0].rstrip('/')
                            links.append(normalized)

                    if links:
                        unique = self._deduplicate_links(links)
                        log_print(f"✅ (Strategy 3 - Scroll) Found {len(unique)} links")
                        return unique
            except Exception as e:
                log_print(f"⚠ Strategy 3 failed: {e}", "warning")

            # STRATEGY 4: JavaScript extraction
            try:
                js_links = self.driver.execute_script("""
                    const links = [];
                    const anchors = document.querySelectorAll('a');
                    anchors.forEach(a => {
                        const href = a.href;
                        if(href && href.includes('/view/') && !href.includes('#')) {
                            links.push(href.split('?')[0]);
                        }
                    });
                    return [...new Set(links)]; // Remove duplicates
                """)

                if js_links:
                    normalized_links = [link.rstrip('/') for link in js_links]
                    log_print(f"✅ (Strategy 4 - JavaScript) Found {len(normalized_links)} links")
                    return normalized_links
            except Exception as e:
                log_print(f"⚠ Strategy 4 failed: {e}", "warning")

            log_print("❌ All link extraction strategies failed", "error")
            return []

        except Exception as e:
            log_print(f"❌ Critical error in enhanced link extraction: {e}", "error")
            return []

    def _deduplicate_links(self, links):
        """Helper method to remove duplicates while preserving order"""
        unique = []
        seen = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                unique.append(link)
        return unique

    def fix_problematic_issue_state(self):
        """Fix the state for the problematic StudiiSiCercetariMecanicaSiAplicata_1957 issue"""
        problematic_url = "https://adt.arcanum.com/ro/view/StudiiSiCercetariMecanicaSiAplicata_1957"

        for item in self.state.get("downloaded_issues", []):
            if item.get("url") == problematic_url.rstrip('/'):
                if not item.get("total_pages"):
                    item["total_pages"] = 1407  # Set the known total
                    log_print(f"🔧 Fixed total_pages for {problematic_url}: set to 1407")
                    self._save_state()
                    return True
        return False

    def extract_page_range_from_filename(self, filename):
        """Extrage range-ul de pagini din numele fișierului pentru sortare corectă"""
        match = re.search(r'__pages(\d+)-(\d+)\.pdf', filename)
        if match:
            start_page = int(match.group(1))
            end_page = int(match.group(2))
            return (start_page, end_page)
        return (0, 0)

    def copy_and_combine_issue_pdfs(self, issue_url: str, issue_title: str):
        """Copiază PDF-urile în folder, le combină în ordinea numerică corectă și șterge copiile + originalele"""
        prefix = issue_url.rstrip('/').split('/')[-1]
        folder_name = self._safe_folder_name(issue_title or prefix)
        dest_dir = os.path.join(self.download_dir, folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        copied = False
        pdf_files = []

        log_print(f"📁 Procesez PDF-urile pentru '{issue_title}' cu prefix '{prefix}'")

        for fname in os.listdir(self.download_dir):
            if not fname.lower().endswith(".pdf"):
                continue
            if prefix in fname and '__pages' in fname:
                src = os.path.join(self.download_dir, fname)
                dst = os.path.join(dest_dir, fname)
                try:
                    shutil.copy2(src, dst)
                    copied = True
                    pdf_files.append(dst)
                    log_print(f"📄 Copiat: {fname} → {folder_name}/")
                except Exception as e:
                    log_print(f"⚠ Nu am reușit să copiez {fname} în {dest_dir}: {e}", "error")

        if not copied:
            log_print(f"ℹ️ Nu am găsit PDF-uri de copiat pentru '{issue_title}' cu prefix '{prefix}'.")
            return

        log_print(f"📁 Toate PDF-urile pentru '{issue_title}' au fost copiate în '{dest_dir}'.")

        output_file = os.path.join(dest_dir, f"{folder_name}.pdf")
        files_to_delete = []

        try:
            if len(pdf_files) > 1:
                log_print(f"🔗 Combinez {len(pdf_files)} fișiere PDF în ordinea corectă...")

                pdf_files_with_ranges = []
                for pdf_path in pdf_files:
                    filename = os.path.basename(pdf_path)
                    start_page, end_page = self.extract_page_range_from_filename(filename)
                    pdf_files_with_ranges.append((start_page, end_page, pdf_path))

                pdf_files_with_ranges.sort(key=lambda x: x[0])
                sorted_files = [x[2] for x in pdf_files_with_ranges]

                log_print("📋 Ordinea de combinare:")
                for start, end, path in pdf_files_with_ranges:
                    filename = os.path.basename(path)
                    log_print(f"   📄 {filename} (pagini {start}-{end})")

                from PyPDF2 import PdfMerger
                merger = PdfMerger()

                for pdf_path in sorted_files:
                    try:
                        merger.append(pdf_path)
                        files_to_delete.append(pdf_path)
                        filename = os.path.basename(pdf_path)
                        log_print(f"   ✅ Adăugat în ordine: {filename}")
                    except Exception as e:
                        log_print(f"   ⚠ Eroare la adăugarea {pdf_path}: {e}", "error")

                merger.write(output_file)
                merger.close()

                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                    log_print(f"✅ Fișierul combinat creat cu succes: {file_size_mb:.2f} MB")

                    # ȘTERGE COPIILE DIN FOLDER
                    deleted_count = 0
                    total_deleted_size = 0

                    for file_to_delete in files_to_delete:
                        try:
                            file_size = os.path.getsize(file_to_delete)
                            os.remove(file_to_delete)
                            deleted_count += 1
                            total_deleted_size += file_size
                            log_print(f"   🗑️ Șters copia: {os.path.basename(file_to_delete)}")
                        except Exception as e:
                            log_print(f"   ⚠ Nu am putut șterge copia {file_to_delete}: {e}", "error")

                    deleted_size_mb = total_deleted_size / (1024 * 1024)
                    log_print(f"🎉 FINALIZAT: Păstrat doar fișierul combinat '{os.path.basename(output_file)}'")
                    log_print(f"🗑️ Șterse {deleted_count} copii din folder ({deleted_size_mb:.2f} MB)")

                    # ȘTERGE ORIGINALELE DE PE D:\
                    log_print(f"🗑️ ATENȚIE: Șterg fișierele originale de pe D:\\ pentru a elibera spațiu...")
                    time.sleep(1)  # Pauză de 1 secundă pentru a citi mesajul

                    deleted_originals = 0
                    total_deleted_original_size = 0

                    for fname in os.listdir(self.download_dir):
                        if not fname.lower().endswith(".pdf"):
                            continue
                        if prefix in fname and '__pages' in fname:
                            original_path = os.path.join(self.download_dir, fname)
                            try:
                                file_size = os.path.getsize(original_path)
                                os.remove(original_path)
                                deleted_originals += 1
                                total_deleted_original_size += file_size
                                log_print(f"   🗑️ Șters original: {fname}")
                            except Exception as e:
                                log_print(f"   ⚠ Nu am putut șterge originalul {fname}: {e}", "error")

                    deleted_original_size_mb = total_deleted_original_size / (1024 * 1024)
                    log_print(f"✅ Șterse {deleted_originals} fișiere originale de pe D:\\ ({deleted_original_size_mb:.2f} MB)")

                else:
                    log_print(f"❌ EROARE: Fișierul combinat nu a fost creat corect!", "error")
                    log_print(f"🛡️ SIGURANȚĂ: Păstrez copiile pentru siguranță")

            elif len(pdf_files) == 1:
                original_file = pdf_files[0]
                original_size_mb = os.path.getsize(original_file) / (1024 * 1024)

                try:
                    os.replace(original_file, output_file)
                    log_print(f"✅ Copia redenumită în: {os.path.basename(output_file)} ({original_size_mb:.2f} MB)")

                    # ȘTERGE ORIGINALUL DE PE D:\ (pentru cazul cu un singur fișier)
                    for fname in os.listdir(self.download_dir):
                        if not fname.lower().endswith(".pdf"):
                            continue
                        if prefix in fname and '__pages' in fname:
                            original_path = os.path.join(self.download_dir, fname)
                            try:
                                os.remove(original_path)
                                log_print(f"🗑️ Șters originalul: {fname}")
                            except Exception as e:
                                log_print(f"⚠ Nu am putut șterge originalul {fname}: {e}", "error")

                except Exception as e:
                    log_print(f"⚠ Nu am putut redenumi copia {original_file}: {e}", "error")

            else:
                log_print(f"ℹ️ Nu există fișiere PDF de combinat în '{dest_dir}'.")

        except Exception as e:
            log_print(f"❌ EROARE la combinarea PDF-urilor: {e}", "error")
            log_print(f"🛡️ SIGURANȚĂ: Păstrez copiile din cauza erorii")
            return

        try:
            if os.path.exists(output_file):
                final_size_mb = os.path.getsize(output_file) / (1024 * 1024)

                # CALCULEAZĂ SPAȚIUL TOTAL ELIBERAT
                total_freed_space = 0
                if 'deleted_size_mb' in locals():
                    total_freed_space += deleted_size_mb
                if 'deleted_original_size_mb' in locals():
                    total_freed_space += deleted_original_size_mb

                log_print(f"\n📋 RAPORT FINAL pentru '{issue_title}':")
                log_print(f"   📁 Folder destinație: {dest_dir}")
                log_print(f"   📄 Fișier final: {os.path.basename(output_file)} ({final_size_mb:.2f} MB)")
                log_print(f"   🗑️ Copii temporare din folder: ȘTERSE")
                log_print(f"   🗑️ Fișiere originale de pe D:\\: ȘTERSE COMPLET")
                if total_freed_space > 0:
                    log_print(f"   💾 SPAȚIU ELIBERAT TOTAL: {total_freed_space:.2f} MB")
                log_print(f"   ✅ RĂMÂNE DOAR: Fișierul combinat în folder dedicat")
            else:
                log_print(f"⚠ Nu s-a putut crea fișierul final pentru '{issue_title}'", "warning")
        except Exception as e:
            log_print(f"⚠ Eroare la raportul final: {e}", "error")

        log_print("=" * 60)

    def find_next_issue_in_collection_order(self, collection_links, last_completed_url):
        """Găsește următorul issue de procesat în ordinea din HTML"""
        if not last_completed_url:
            return collection_links[0] if collection_links else None

        try:
            last_index = collection_links.index(last_completed_url.rstrip('/'))
            next_index = last_index + 1
            if next_index < len(collection_links):
                next_url = collection_links[next_index]
                log_print(f"🎯 Următorul issue după '{last_completed_url}' este: '{next_url}'")
                return next_url
            else:
                log_print(f"✅ Toate issue-urile din colecție au fost procesate!")
                return None
        except ValueError:
            log_print(f"⚠ URL-ul '{last_completed_url}' nu e în colecția curentă, încep cu primul din listă", "warning")
            return collection_links[0] if collection_links else None

    def get_last_completed_issue_from_collection(self, collection_links):
        """Găsește ultimul issue complet descărcat din colecția curentă"""
        for item in self.state.get("downloaded_issues", []):
            url = item.get("url", "").rstrip('/')
            if url in [link.rstrip('/') for link in collection_links]:
                if item.get("completed_at"):
                    log_print(f"🏁 Ultimul issue complet din colecție: {url}")
                    return url

        log_print("🆕 Niciun issue complet găsit în colecția curentă")
        return None

    def open_new_tab_and_download(self, url):
        """Se focusează pe un singur issue până la final, fără skip-uri"""
        normalized_url = url.rstrip('/')

        if normalized_url in self.dynamic_skip_urls:
            log_print(f"⏭️ Sar peste {url} (în skip list).")
            return False

        already_done = any(
            item.get("url") == normalized_url and item.get("completed_at") and
            item.get("last_successful_segment_end", 0) >= (item.get("total_pages") or float('inf'))
            for item in self.state.get("downloaded_issues", [])
        )
        if already_done:
            log_print(f"⏭️ Sar peste {url} (deja descărcat complet).")
            return False

        log_print(f"\n🎯 ÎNCEP FOCUSAREA PE: {url}")
        log_print("=" * 60)

        try:
            if not self.attached_existing:
                self.ensure_alive_fallback()

            prev_handles = set(self.driver.window_handles)
            self.driver.execute_script("window.open('');")
            new_handles = set(self.driver.window_handles)
            diff = new_handles - prev_handles
            new_handle = diff.pop() if diff else self.driver.window_handles[-1]
            self.driver.switch_to.window(new_handle)

            if not self.navigate_to_page(url):
                log_print(f"❌ Nu am putut naviga la {url}", "error")
                return False

            time.sleep(1)

            if self.check_daily_limit_in_all_windows(set_flag=False):
                log_print("⚠ Pagină cu limită zilnică detectată - opresc aici.", "warning")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return False

            log_print("✅ Pagina e OK, încep extragerea metadatelor...")
            title, subtitle = self.get_issue_metadata()

            existing_pages = self.get_existing_pdf_segments(url)
            log_print(f"📊 Pagini existente pe disk: {existing_pages}")

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
                log_print(f"📄 Reiau de la pagina {resume_from} (JSON: {json_progress}, Disk: {existing_pages})")

            if resume_from is None:
                log_print(f"⏭️ Issue-ul {url} este deja complet.")
                return False

            self.current_issue_url = normalized_url

            existing_item = next((item for item in self.state.get("downloaded_issues", []) if item.get("url") == normalized_url), None)
            if not existing_item:
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)
            elif actual_progress > existing_item.get("last_successful_segment_end", 0):
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)

            log_print(f"🔒 INTRÂND ÎN MODUL FOCUS - nu mai fac alte verificări până nu termin!")

            pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)

            if pages_done == 0 and not limit_hit:
                log_print(f"⚠ Descărcarea pentru {url} a eșuat complet.", "warning")
                return False

            if limit_hit:
                log_print(f"⚠ Probleme în timpul descărcării pentru {url}; progresul parțial a fost salvat.", "warning")
                return False

            self.mark_issue_done(url, pages_done, title=title, subtitle=subtitle, total_pages=pages_done)
            log_print(f"✅ Descărcarea pentru {url} finalizată complet ({pages_done} pagini).")

            self.copy_and_combine_issue_pdfs(url, title or normalized_url)

            log_print("=" * 60)
            log_print(f"🎉 FOCUSAREA COMPLETĂ PE {url} FINALIZATĂ CU SUCCES!")
            log_print("=" * 60)
            return True

        except WebDriverException as e:
            log_print(f"❌ Eroare WebDriver pentru {url}: {e}", "error")
            return False
        except Exception as e:
            log_print(f"❌ Eroare în open_new_tab_and_download pentru {url}: {e}", "error")
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
            log_print(f"⚠ Conexiune WebDriver moartă ({e}), pornesc instanță nouă ca fallback.", "warning")
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            chrome_options = Options()
            chrome_options.add_experimental_option("prefs", prefs)
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, self.timeout)
            self.attached_existing = False

    def run_collection(self, collection_url):
        """Procesează UN SINGUR issue pe rând, fără să sară la altele"""
        log_print(f"🌐 Încep procesarea colecției: {collection_url}")
        if not self.driver:
            log_print("❌ Driver neinițializat.", "error")
            return False
        if not self.navigate_to_page(collection_url):
            return False

        if self.state.get("daily_limit_hit", False):
            log_print("⚠ Nu mai pot continua din cauza limitei zilnice setate anterior.", "warning")
            return True

        if self.remaining_quota() <= 0:
            log_print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă.", "warning")
            return True

        issue_links = self.extract_issue_links_from_collection()
        if not issue_links:
            log_print("⚠ Nu s-au găsit issue-uri în colecție.", "warning")
            return False

        last_completed = self.get_last_completed_issue_from_collection(issue_links)
        next_to_process = self.find_next_issue_in_collection_order(issue_links, last_completed)

        if not next_to_process:
            log_print("✅ Toate issue-urile din această colecție sunt complete!")
            return True

        start_index = issue_links.index(next_to_process)
        pending_links = issue_links[start_index:]

        actual_pending = []
        for link in pending_links:
            normalized = link.rstrip('/')
            if normalized in self.dynamic_skip_urls:
                continue
            exists = next((i for i in self.state.get("downloaded_issues", []) if i.get("url") == normalized), None)
            if not exists or not exists.get("completed_at"):
                actual_pending.append(link)

        log_print(f"📊 Procesez {len(actual_pending)} issue-uri din colecția curentă (începând cu {next_to_process})")

        processed_any = False
        for i, link in enumerate(actual_pending):
            log_print(f"\n🔢 ISSUE {i+1}/{len(actual_pending)}: {link}")

            if self.remaining_quota() <= 0:
                log_print(f"⚠ Limita zilnică de {DAILY_LIMIT} issue-uri atinsă înainte de a începe acest issue.", "warning")
                break

            if self.state.get("daily_limit_hit", False):
                log_print("⚠ Flag daily_limit_hit setat - opresc procesarea.", "warning")
                break

            log_print(f"🎯 Mă focusez EXCLUSIV pe: {link}")
            result = self.open_new_tab_and_download(link)

            if result:
                processed_any = True
                log_print(f"✅ Issue-ul {link} procesat cu succes!")
            else:
                log_print(f"⚠ Issue-ul {link} nu a fost procesat.", "warning")

            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                log_print("⚠ Limita zilnică atinsă după procesarea acestui issue.", "warning")
                break

            if i < len(actual_pending) - 1:
                log_print("⏳ Pauză de 2s între issue-uri...")
                time.sleep(2)

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

    def process_pending_partials_first(self):
        """Procesează mai întâi issue-urile parțiale, indiferent de colecție"""
        pending_partials = self.get_pending_partial_issues()

        if not pending_partials:
            log_print("✅ Nu există issue-uri parțiale de procesat.")
            return True

        log_print(f"\n🎯 PRIORITATE: Procesez {len(pending_partials)} issue-uri parțiale:")
        for item in pending_partials:
            url = item.get("url")
            progress = item.get("last_successful_segment_end", 0)
            total = item.get("total_pages", 0)
            log_print(f"   🔄 {url} - pagini {progress}/{total}")

        processed_any = False
        for item in pending_partials:
            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                log_print(f"⚠ Limita zilnică atinsă în timpul issue-urilor parțiale.", "warning")
                break

            url = item.get("url")
            result = self.open_new_tab_and_download(url)
            if result:
                processed_any = True
            time.sleep(1)

        return processed_any

    def run_additional_collections(self):
        """Procesează colecțiile adiționale după colecția principală"""
        start_index = self.state.get("current_additional_collection_index", 0)

        for i in range(start_index, len(ADDITIONAL_COLLECTIONS)):
            collection_url = ADDITIONAL_COLLECTIONS[i]

            if collection_url.rstrip('/') in self.dynamic_skip_urls:
                log_print(f"⏭️ Sar peste colecția {i+1}/{len(ADDITIONAL_COLLECTIONS)} (deja completă): {collection_url}")
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
                continue

            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                log_print(f"⚠ Limita zilnică atinsă, opresc procesarea colecțiilor adiționale.", "warning")
                break

            log_print(f"\n🔄 Procesez colecția adițională {i+1}/{len(ADDITIONAL_COLLECTIONS)}: {collection_url}")

            self.state["current_additional_collection_index"] = i
            self._save_state()

            collection_completed = self.run_collection(collection_url)

            if collection_completed and not self.state.get("daily_limit_hit", False):
                log_print(f"✅ Colecția adițională {i+1} completă, o marchez și trec la următoarea.")
                self.mark_collection_complete(collection_url)
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
            elif self.state.get("daily_limit_hit", False):
                break
            else:
                break

        current_index = self.state.get("current_additional_collection_index", 0)
        if current_index >= len(ADDITIONAL_COLLECTIONS):
            log_print("🎉 TOATE colecțiile adiționale au fost procesate!")
            return True
        else:
            remaining = len(ADDITIONAL_COLLECTIONS) - current_index
            log_print(f"⚠ Mai rămân {remaining} colecții adiționale de procesat.")
            return True

    def run(self):
        log_print("🧪 Încep executarea Scheduled PDF Downloader")
        log_print("=" * 60)

        # 🐛 DEBUGGING INFO
        log_print(f"📁 Download dir: {self.download_dir}")
        log_print(f"📄 State file: {self.state_path}")
        log_print(f"📄 Skip URLs file: {self.skip_urls_path}")
        log_print(f"🔍 Headless mode: {self.headless}")
        log_print(f"📊 Current state count: {self.state.get('count', 0)}")
        log_print(f"📊 Downloaded issues în state: {len(self.state.get('downloaded_issues', []))}")

        try:
            if not self.setup_chrome_driver():
                return False

            log_print("🔄 Resetez flag-ul de limită zilnică și verific ferestrele existente...")
            self.state["daily_limit_hit"] = False
            self._save_state()

            self.sync_json_with_disk_files()

            if self.check_daily_limit_in_all_windows(set_flag=False):
                log_print("⚠ Am găsit ferestre cu limita deschise din sesiuni anterioare.")
                log_print("🔄 Le-am închis și reîncerc procesarea...")

            log_print(f"\n🎯 ETAPA 0: Procesez issue-urile parțiale din toate colecțiile")
            if self.process_pending_partials_first():
                log_print("✅ Issue-urile parțiale au fost procesate sau limita a fost atinsă.")

            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                log_print("⚠ Limita zilnică atinsă după procesarea issue-urilor parțiale.", "warning")
                return True

            if not self.state.get("main_collection_completed", False):
                log_print(f"\n📚 ETAPA 1: Procesez colecția principală: {self.main_collection_url}")

                main_completed = self.run_collection(self.main_collection_url)

                if self.state.get("daily_limit_hit", False):
                    log_print("⚠ Limita zilnică atinsă în colecția principală.", "warning")
                    return True

                if main_completed:
                    log_print("✅ Colecția principală completă!")
                    self.state["main_collection_completed"] = True
                    self._save_state()
                else:
                    log_print("⚠ Colecția principală nu este completă încă.", "warning")
                    return True
            else:
                log_print("✅ Colecția principală a fost deja completată.")

            if self.remaining_quota() > 0 and not self.state.get("daily_limit_hit", False):
                log_print(f"\n📚 ETAPA 2: Procesez colecțiile adiționale")
                self.run_additional_collections()

            log_print("✅ Toate operațiunile au fost inițiate.")
            self._finalize_session()
            return True

        except KeyboardInterrupt:
            log_print("\n\n⚠ Intervenție manuală: întrerupt.", "warning")
            return False
        except Exception as e:
            log_print(f"\n❌ Eroare neașteptată: {e}", "error")
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
                log_print("🔖 Am păstrat sesiunea Chrome existentă deschisă (nu fac quit).")
            else:
                log_print("🚪 Închid browserul.")
                try:
                    self.driver.quit()
                except Exception:
                    pass

# ============================================================================
# FUNCȚII DE DETERMINARE A URL-ULUI DE START
# ============================================================================

def determine_start_url():
    """Determină URL-ul de start pe baza progresului salvat"""
    temp_downloader = ScheduledPDFDownloader("temp", download_dir=DOWNLOAD_DIR, batch_size=BATCH_SIZE, headless=False)

    pending_partials = temp_downloader.get_pending_partial_issues()
    if pending_partials:
        # Determină colecția din care provine primul issue parțial
        first_partial_url = pending_partials[0].get("url", "")

        # Găsește colecția potrivită
        if "StudiiSiCercetariMecanicaSiAplicata" in first_partial_url:
            url = "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMecanicaSiAplicata/"
        elif "Convietuirea" in first_partial_url:
            url = "https://adt.arcanum.com/ro/collection/Convietuirea/"
        else:
            url = ADDITIONAL_COLLECTIONS[0]  # Fallback

        log_print(f"🔄 Există {len(pending_partials)} issue-uri parțiale de procesat. Start cu: {url}")
        return url

    main_collection_completed = temp_downloader.state.get("main_collection_completed", False)
    current_additional_index = temp_downloader.state.get("current_additional_collection_index", 0)

    if not main_collection_completed:
        url = "https://adt.arcanum.com/ro/collection/GazetaMatematicaSiFizicaSeriaB"
        log_print(f"📚 Continuă colecția principală: {url}")
        return url
    elif current_additional_index < len(ADDITIONAL_COLLECTIONS):
        for i in range(current_additional_index, len(ADDITIONAL_COLLECTIONS)):
            potential_url = ADDITIONAL_COLLECTIONS[i]
            if potential_url.rstrip('/') not in temp_downloader.dynamic_skip_urls:
                log_print(f"📚 Continuă colecția adițională {i + 1}/{len(ADDITIONAL_COLLECTIONS)}: {potential_url}")
                return potential_url
        else:
            log_print("🎉 TOATE colecțiile au fost procesate complet!")
            return None
    else:
        log_print("🎉 TOATE colecțiile au fost procesate complet!")
        return None

def run_download_session():
    """Rulează o sesiune de descărcare"""
    log_print("🌅 ÎNCEPE SESIUNEA AUTOMATĂ DE DESCĂRCARE")
    log_print("=" * 80)

    try:
        start_url = determine_start_url()
        if not start_url:
            log_print("✅ Nu mai există colecții de procesat. Sesiunea se închide.")
            return True

        downloader = ScheduledPDFDownloader(
            main_collection_url=start_url,
            download_dir=DOWNLOAD_DIR,
            batch_size=BATCH_SIZE,
            timeout=TIMEOUT,
            headless=True  # Întotdeauna headless pentru sesiunile programate
        )

        success = downloader.run()

        if success:
            log_print("✅ SESIUNEA COMPLETĂ CU SUCCES")
        else:
            log_print("⚠ SESIUNEA ÎNCHEIATĂ CU PROBLEME", "warning")

        return success

    except Exception as e:
        log_print(f"❌ EROARE FATALĂ ÎN SESIUNE: {e}", "error")
        return False
    finally:
        log_print("🌇 SESIUNEA ÎNCHEIATĂ")
        log_print("=" * 80)

def test_configuration():
    """Testează configurația sistemului"""
    log_print("🧪 TESTARE CONFIGURAȚIE")
    log_print("=" * 50)

    # Testează directorul de descărcare
    if os.path.exists(DOWNLOAD_DIR):
        log_print(f"✅ Director de descărcare: {DOWNLOAD_DIR}")
    else:
        log_print(f"❌ Directorul de descărcare nu există: {DOWNLOAD_DIR}", "error")
        return False

    # Testează fișierele de stare
    state_path = os.path.join(DOWNLOAD_DIR, STATE_FILENAME)
    skip_urls_path = os.path.join(DOWNLOAD_DIR, SKIP_URLS_FILENAME)

    log_print(f"📄 Stare JSON: {state_path} ({'EXISTĂ' if os.path.exists(state_path) else 'NU EXISTĂ'})")
    log_print(f"📄 Skip URLs: {skip_urls_path} ({'EXISTĂ' if os.path.exists(skip_urls_path) else 'NU EXISTĂ'})")

    # Testează browser-ul (fără headless pentru test)
    try:
        log_print("🌐 Testez browser-ul...")
        test_downloader = ScheduledPDFDownloader(
            main_collection_url="test",
            download_dir=DOWNLOAD_DIR,
            headless=True  # Chiar și pentru test, folosim headless
        )

        if test_downloader.setup_chrome_driver():
            log_print("✅ Browser OK")
            test_downloader.driver.quit()
        else:
            log_print("❌ Probleme cu browser-ul", "error")
            return False

    except Exception as e:
        log_print(f"❌ Eroare la testarea browser-ului: {e}", "error")
        return False

    # Testează programarea
    log_print(f"⏰ Ora programată: {SCHEDULED_TIME}")
    log_print(f"📊 Limită zilnică: {DAILY_LIMIT}")
    log_print(f"📦 Mărime batch: {BATCH_SIZE}")

    # Verifică progresul actual
    start_url = determine_start_url()
    if start_url:
        log_print(f"🎯 Următorul URL de procesat: {start_url}")
    else:
        log_print("✅ Toate colecțiile sunt complete")

    log_print("✅ CONFIGURAȚIA ESTE OK")
    return True

# ============================================================================
# SCHEDULER ȘI MAIN
# ============================================================================

def main():
    global logger

    parser = argparse.ArgumentParser(description="Scheduled PDF Downloader pentru Arcanum")
    parser.add_argument("--now", action="store_true", help="Rulează imediat (bypass scheduler)")
    parser.add_argument("--test", action="store_true", help="Testează configurația")
    args = parser.parse_args()

    # Inițializează logger-ul
    log_file_path = os.path.join(DOWNLOAD_DIR, LOG_FILE)
    logger = DualLogger(log_file_path)

    if args.test:
        if test_configuration():
            log_print("🎉 TESTARE COMPLETĂ - SISTEMUL ESTE GATA")
            sys.exit(0)
        else:
            log_print("❌ TESTARE EȘUATĂ - VERIFICĂ CONFIGURAȚIA", "error")
            sys.exit(1)

    if args.now:
        log_print("🚀 RULARE IMEDIATĂ SOLICITATĂ")
        success = run_download_session()
        sys.exit(0 if success else 1)

    # Scheduler normal
    log_print(f"📅 SCHEDULER PORNIT - Descărcare programată zilnic la {SCHEDULED_TIME}")
    log_print(f"📁 Director descărcare: {DOWNLOAD_DIR}")
    log_print(f"📄 Log file: {log_file_path}")
    log_print("💡 Pentru rulare imediată: python scheduled_downloader.py --now")
    log_print("🧪 Pentru testare: python scheduled_downloader.py --test")
    log_print("⏸️  Pentru oprire: Ctrl+C")

    # Programează descărcarea zilnică
    schedule.every().day.at(SCHEDULED_TIME).do(run_download_session)

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifică la fiecare minut
    except KeyboardInterrupt:
        log_print("\n🛑 SCHEDULER OPRIT MANUAL")
        log_print("👋 La revedere!")

if __name__ == "__main__":
    main()