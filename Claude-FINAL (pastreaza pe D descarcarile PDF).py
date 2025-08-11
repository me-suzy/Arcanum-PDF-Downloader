#!/usr/bin/env python3
"""
Automatizare descărcare PDF-uri din Arcanum (Gazeta Matematica și colecții adiacente):
- FIXED: Combinarea PDF-urilor în ordinea corectă numerică (1-49, 50-99, 100-149, etc.)
- FIXED: Copiază fișierele în folder în loc să le mute
- FIXED: Procesează issue-urile în ordinea corectă din HTML
- FIXED: Continuă cu următorul issue după cel terminat, nu se întoarce la primul
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

# Colecțiile adiționale (procesate DUPĂ colecția principală din main())
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
                    completed_collections = data.get("completed_collections", [])  # ADAUGĂ ACEASTĂ LINIE

                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_urls)
                    self.dynamic_skip_urls.update(url.rstrip('/') for url in completed_collections)  # ADAUGĂ ACEASTĂ LINIE

                    print(f"📋 Încărcat {len(completed_urls)} URL-uri complet descărcate din {SKIP_URLS_FILENAME}")
                    print(f"📋 Încărcat {len(completed_collections)} colecții complet procesate din {SKIP_URLS_FILENAME}")  # ADAUGĂ ACEASTĂ LINIE
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
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Salvat {len(data['completed_urls'])} URL-uri în {SKIP_URLS_FILENAME}")
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
                            print(f"📁 Găsit PDF existent: {filename} (pagini {start_page}-{end_page})")
        except Exception as e:
            print(f"⚠ Eroare la scanarea fișierelor: {e}")

        return max_page

    def sync_json_with_disk_files(self):
        """FIXED: Combină informațiile din JSON cu fișierele de pe disk, fără să șteargă datele existente"""
        print("🔄 Sincronizez JSON-ul cu fișierele de pe disk...")

        try:
            # PASUL 1: Păstrează toate issue-urile existente din JSON
            existing_issues = {}
            for item in self.state.get("downloaded_issues", []):
                url = item.get("url", "").rstrip('/')
                existing_issues[url] = item.copy()

            # PASUL 2: Scanează PDF-urile de pe disk și actualizează progresul
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

            # PASUL 3: Actualizează issue-urile cu progresul de pe disk
            for issue_id, data in pdf_files.items():
                max_page = data["max_page"]
                files = data["files"]
                latest_time = data["latest_mod_time"]
                issue_url = data["url"]

                if not issue_url:
                    continue

                # Verifică dacă issue-ul e complet
                is_complete = self.is_issue_complete_by_end_page(max_page)

                # Actualizează issue-ul existent sau creează unul nou
                if issue_url in existing_issues:
                    issue = existing_issues[issue_url]
                    # Actualizează doar dacă progresul de pe disk e mai mare
                    if max_page > issue.get("last_successful_segment_end", 0):
                        issue["last_successful_segment_end"] = max_page
                        print(f"🔄 Actualizat progres din disk: {issue_url} → {max_page} pagini")

                    # Marchează ca complet dacă este cazul
                    if is_complete and not issue.get("completed_at"):
                        issue["completed_at"] = datetime.now().isoformat(timespec="seconds")
                        issue["pages"] = max_page
                        issue["total_pages"] = max_page
                        print(f"✅ Marcat ca complet din disk: {issue_url}")

                    # Adaugă timestamp pentru sortare
                    issue["_sort_time"] = latest_time
                else:
                    # Issue nou găsit doar pe disk
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
                    print(f"➕ Adăugat issue nou din disk: {issue_url} → {max_page} pagini")

                # Afișează fișierele pentru acest issue
                for start, end, fname in files:
                    print(f"   📄 {fname} (pagini {start}-{end})")

            # PASUL 4: Sortează issue-urile: parțiale primele, apoi complete
            partial_issues = []
            complete_issues = []

            for issue in existing_issues.values():
                # Elimină timestamp-ul temporar
                if "_sort_time" in issue:
                    sort_time = issue.pop("_sort_time")
                else:
                    sort_time = 0

                # Clasifică în parțiale vs complete
                is_partial = (issue.get("last_successful_segment_end", 0) > 0 and
                             not issue.get("completed_at") and
                             issue.get("total_pages") and
                             issue.get("last_successful_segment_end", 0) < issue.get("total_pages", 0))

                issue["_sort_key"] = sort_time  # Pentru sortare temporară

                if is_partial:
                    partial_issues.append(issue)
                    print(f"🔄 Issue parțial: {issue['url']} ({issue.get('last_successful_segment_end', 0)}/{issue.get('total_pages', 0)} pagini)")
                else:
                    complete_issues.append(issue)

            # Sortează: parțiale după ultimele modificare, complete la urmă
            partial_issues.sort(key=lambda x: x.get("_sort_key", 0), reverse=True)
            complete_issues.sort(key=lambda x: x.get("_sort_key", 0), reverse=True)

            # Combină listele
            final_issues = partial_issues + complete_issues

            # Elimină cheia temporară de sortare
            for issue in final_issues:
                if "_sort_key" in issue:
                    del issue["_sort_key"]

            # Actualizează starea
            self.state["downloaded_issues"] = final_issues
            completed_count = len([i for i in final_issues if i.get("completed_at")])
            self.state["count"] = completed_count

            self._save_state()
            self._save_skip_urls()

            partial_count = len(partial_issues)
            print(f"✅ Sincronizare completă: {partial_count} issue-uri parțiale, {len(complete_issues)} complete")
            if partial_count > 0:
                print("🎯 Issue-urile parțiale vor fi procesate primele!")

        except Exception as e:
            print(f"⚠ Eroare la sincronizarea cu disk-ul: {e}")

    def get_pending_partial_issues(self):
        """FIXED: Returnează lista issue-urilor parțiale care trebuie continuate, indiferent de colecție"""
        pending_partials = []

        for item in self.state.get("downloaded_issues", []):
            url = item.get("url", "").rstrip('/')
            last_segment = item.get("last_successful_segment_end", 0)
            total_pages = item.get("total_pages")
            completed_at = item.get("completed_at", "")

            # Skip URL-urile complet descărcate
            if url in self.dynamic_skip_urls:
                continue

            # Issue parțial: are progres, nu e complet, și mai sunt pagini de descărcat
            if (last_segment > 0 and
                not completed_at and
                total_pages and
                last_segment < total_pages):

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
                    # Aceeași zi - păstrează totul
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
                    # Zi nouă - păstrează doar issue-urile parțial descărcate
                    old_issues = self._normalize_downloaded_issues(loaded.get("downloaded_issues", []))
                    partial_issues = []

                    for issue in old_issues:
                        last_segment = issue.get("last_successful_segment_end", 0)
                        total_pages = issue.get("total_pages")
                        completed_at = issue.get("completed_at", "")

                        if (last_segment > 0 and not completed_at and total_pages and last_segment < total_pages):
                            print(f"📋 Păstrez progresul parțial pentru: {issue['url']} (pagini {last_segment}/{total_pages})")
                            partial_issues.append(issue)

                    self.state = {
                        "date": today,
                        "count": 0,
                        "downloaded_issues": partial_issues,
                        "pages_downloaded": 0,
                        "recent_links": [],
                        "daily_limit_hit": False,
                        "main_collection_completed": loaded.get("main_collection_completed", False),
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
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠ Nu am putut salva state-ul: {e}")

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
            print(f"➕ Adăugat issue nou în progres: {normalized}")

        self._save_state()
        print(f"💾 Progres parțial salvat: {normalized} - pagini {last_successful_segment_end}/{total_pages or '?'}")

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
        print(f"✅ Issue marcat ca terminat: {normalized} ({pages_count} pagini)")

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
        """FIXED: Verifică limita zilnică după fiecare segment descărcat"""
        for attempt in range(1, retries + 2):
            print(f"🔄 Încep segmentul {start}-{end}, încercarea {attempt}")

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
        """FIXED: Oprește instant la detectarea limitei zilnice"""
        total = self.get_total_pages()
        if total <= 0:
            print("⚠ Nu am obținut numărul total de pagini; nu pot continua.")
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

        print(f"🎯 FOCUSEZ PE ACEST ISSUE: Voi descărca {len(segments)} segmente fără întreruperi")

        for (start, end) in segments:
            print(f"📦 Procesez segmentul {start}-{end}")
            result = self.save_page_range(start, end, retries=1)

            if not result:
                # VERIFICĂ DACĂ EȘECUL E DIN CAUZA LIMITEI ZILNICE
                if self.state.get("daily_limit_hit", False):
                    print(f"🛑 OPRIRE INSTANT - Limită zilnică atinsă la segmentul {start}-{end}")
                    return last_successful_page, True  # Returnează TRUE pentru limită zilnică

                print(f"❌ Eșec persistent la segmentul {start}-{end}, opresc acest issue.")
                return last_successful_page, False

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
        FIXED: Copiază PDF-urile în folder (nu le mută), le combină în ordinea numerică corectă și șterge copiile
        """
        prefix = issue_url.rstrip('/').split('/')[-1]
        folder_name = self._safe_folder_name(issue_title or prefix)
        dest_dir = os.path.join(self.download_dir, folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        copied = False
        pdf_files = []

        print(f"📁 Procesez PDF-urile pentru '{issue_title}' cu prefix '{prefix}'")

        # PASUL 1: Copiază toate PDF-urile în folder (nu le mută!)
        for fname in os.listdir(self.download_dir):
            if not fname.lower().endswith(".pdf"):
                continue
            if prefix in fname and '__pages' in fname:  # Verificare mai strictă
                src = os.path.join(self.download_dir, fname)
                dst = os.path.join(dest_dir, fname)
                try:
                    shutil.copy2(src, dst)  # COPY2 în loc de MOVE
                    copied = True
                    pdf_files.append(dst)
                    print(f"📄 Copiat: {fname} → {folder_name}/")
                except Exception as e:
                    print(f"⚠ Nu am reușit să copiez {fname} în {dest_dir}: {e}")

        if not copied:
            print(f"ℹ️ Nu am găsit PDF-uri de copiat pentru '{issue_title}' cu prefix '{prefix}'.")
            return

        print(f"📁 Toate PDF-urile pentru '{issue_title}' au fost copiate în '{dest_dir}'.")

        output_file = os.path.join(dest_dir, f"{folder_name}.pdf")
        files_to_delete = []

        try:
            if len(pdf_files) > 1:
                print(f"🔗 Combinez {len(pdf_files)} fișiere PDF în ordinea corectă...")

                # FIXED: Sortează după range-urile numerice din numele fișierului
                pdf_files_with_ranges = []
                for pdf_path in pdf_files:
                    filename = os.path.basename(pdf_path)
                    start_page, end_page = self.extract_page_range_from_filename(filename)
                    pdf_files_with_ranges.append((start_page, end_page, pdf_path))

                # Sortează după pagina de început
                pdf_files_with_ranges.sort(key=lambda x: x[0])
                sorted_files = [x[2] for x in pdf_files_with_ranges]

                # Afișează ordinea de combinare
                print("📋 Ordinea de combinare:")
                for start, end, path in pdf_files_with_ranges:
                    filename = os.path.basename(path)
                    print(f"   📄 {filename} (pagini {start}-{end})")

                from PyPDF2 import PdfMerger
                merger = PdfMerger()

                for pdf_path in sorted_files:
                    try:
                        merger.append(pdf_path)
                        files_to_delete.append(pdf_path)
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

                    # Șterge doar copiile din folder, NU originalele de pe D:\
                    deleted_count = 0
                    total_deleted_size = 0

                    for file_to_delete in files_to_delete:
                        try:
                            file_size = os.path.getsize(file_to_delete)
                            os.remove(file_to_delete)
                            deleted_count += 1
                            total_deleted_size += file_size
                            print(f"   🗑️ Șters copia: {os.path.basename(file_to_delete)}")
                        except Exception as e:
                            print(f"   ⚠ Nu am putut șterge copia {file_to_delete}: {e}")

                    deleted_size_mb = total_deleted_size / (1024 * 1024)
                    print(f"🎉 FINALIZAT: Păstrat doar fișierul combinat '{os.path.basename(output_file)}'")
                    print(f"🗑️ Șterse {deleted_count} copii din folder ({deleted_size_mb:.2f} MB)")
                    print(f"🔒 IMPORTANT: Originalele rămân pe D:\\ pentru siguranță")

                else:
                    print(f"❌ EROARE: Fișierul combinat nu a fost creat corect!")
                    print(f"🛡️ SIGURANȚĂ: Păstrez copiile pentru siguranță")

            elif len(pdf_files) == 1:
                # Un singur fișier - doar redenumește copia
                original_file = pdf_files[0]
                original_size_mb = os.path.getsize(original_file) / (1024 * 1024)

                try:
                    os.replace(original_file, output_file)
                    print(f"✅ Copia redenumită în: {os.path.basename(output_file)} ({original_size_mb:.2f} MB)")
                except Exception as e:
                    print(f"⚠ Nu am putut redenumi copia {original_file}: {e}")

            else:
                print(f"ℹ️ Nu există fișiere PDF de combinat în '{dest_dir}'.")

        except Exception as e:
            print(f"❌ EROARE la combinarea PDF-urilor: {e}")
            print(f"🛡️ SIGURANȚĂ: Păstrez copiile din cauza erorii")
            return

        # PASUL 3: Raport final
        try:
            if os.path.exists(output_file):
                final_size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"\n📋 RAPORT FINAL pentru '{issue_title}':")
                print(f"   📁 Folder destinație: {dest_dir}")
                print(f"   📄 Fișier final: {os.path.basename(output_file)} ({final_size_mb:.2f} MB)")
                print(f"   🔒 Fișiere originale pe D:\\: PĂSTRATE pentru siguranță")
                print(f"   🗑️ Copii temporare din folder: ȘTERSE")
            else:
                print(f"⚠ Nu s-a putut crea fișierul final pentru '{issue_title}'")
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
        """
        Găsește ultimul issue complet descărcat din colecția curentă
        """
        for item in self.state.get("downloaded_issues", []):
            url = item.get("url", "").rstrip('/')
            if url in [link.rstrip('/') for link in collection_links]:
                if item.get("completed_at"):  # Issue complet
                    print(f"🏁 Ultimul issue complet din colecție: {url}")
                    return url

        print("🆕 Niciun issue complet găsit în colecția curentă")
        return None

    def open_new_tab_and_download(self, url):
        """FIXED: Se focusează pe un singur issue până la final, fără skip-uri"""
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

            time.sleep(1)

            # Verifică DOAR o dată la început pentru limită
            if self.check_daily_limit_in_all_windows(set_flag=False):
                print("⚠ Pagină cu limită zilnică detectată - opresc aici.")
                self.state["daily_limit_hit"] = True
                self._save_state()
                return False

            print("✅ Pagina e OK, încep extragerea metadatelor...")
            title, subtitle = self.get_issue_metadata()

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

            # Actualizează progresul în JSON
            existing_item = next((item for item in self.state.get("downloaded_issues", []) if item.get("url") == normalized_url), None)
            if not existing_item:
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)
            elif actual_progress > existing_item.get("last_successful_segment_end", 0):
                self._update_partial_issue_progress(normalized_url, actual_progress, title=title, subtitle=subtitle)

            print(f"🔒 INTRÂND ÎN MODUL FOCUS - nu mai fac alte verificări până nu termin!")

            # DESCĂRCAREA PROPRIU-ZISĂ - fără întreruperi
            pages_done, limit_hit = self.save_all_pages_in_batches(resume_from=resume_from)

            if pages_done == 0 and not limit_hit:
                print(f"⚠ Descărcarea pentru {url} a eșuat complet.")
                return False

            if limit_hit:
                print(f"⚠ Probleme în timpul descărcării pentru {url}; progresul parțial a fost salvat.")
                return False

            # Marchează ca terminat
            self.mark_issue_done(url, pages_done, title=title, subtitle=subtitle, total_pages=pages_done)
            print(f"✅ Descărcarea pentru {url} finalizată complet ({pages_done} pagini).")

            # Copiază și combină PDF-urile
            self.copy_and_combine_issue_pdfs(url, title or normalized_url)

            print("=" * 60)
            print(f"🎉 FOCUSAREA COMPLETĂ PE {url} FINALIZATĂ CU SUCCES!")
            print("=" * 60)
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
        """Procesează colecțiile adiționale după colecția principală"""
        start_index = self.state.get("current_additional_collection_index", 0)

        for i in range(start_index, len(ADDITIONAL_COLLECTIONS)):
            collection_url = ADDITIONAL_COLLECTIONS[i]

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
                self.mark_collection_complete(collection_url)  # ADAUGĂ ACEASTĂ LINIE
                self.state["current_additional_collection_index"] = i + 1
                self._save_state()
            elif self.state.get("daily_limit_hit", False):
                break
            else:
                break

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

            print("🔄 Resetez flag-ul de limită zilnică și verific ferestrele existente...")
            self.state["daily_limit_hit"] = False
            self._save_state()

            # FIXED: Sincronizează cu disk-ul fără să șteargă datele
            self.sync_json_with_disk_files()

            if self.check_daily_limit_in_all_windows(set_flag=False):
                print("⚠ Am găsit ferestre cu limita deschise din sesiuni anterioare.")
                print("🔄 Le-am închis și reîncerc procesarea...")

            # FIXED: ETAPA 0: Procesează mai întâi issue-urile parțiale
            print(f"\n🎯 ETAPA 0: Procesez issue-urile parțiale din toate colecțiile")
            if self.process_pending_partials_first():
                print("✅ Issue-urile parțiale au fost procesate sau limita a fost atinsă.")

            if self.remaining_quota() <= 0 or self.state.get("daily_limit_hit", False):
                print("⚠ Limita zilnică atinsă după procesarea issue-urilor parțiale.")
                return True

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
    if len(sys.argv) >= 2:
        url = sys.argv[1]
        print(f"🎯 URL specificat manual: {url}")
    else:
        temp_downloader = ChromePDFDownloader("temp", download_dir="D:\\", batch_size=50)

        pending_partials = temp_downloader.get_pending_partial_issues()
        if pending_partials:
            url = ADDITIONAL_COLLECTIONS[0]  # SCHIMBĂ ACEASTA - folosește prima din lista adițională
            print(f"🔄 Există {len(pending_partials)} issue-uri parțiale de procesat. Start cu: {url}")
        else:
            main_collection_completed = temp_downloader.state.get("main_collection_completed", False)
            current_additional_index = temp_downloader.state.get("current_additional_collection_index", 0)

            if not main_collection_completed:
                url = "https://adt.arcanum.com/ro/collection/GazetaMatematicaSiFizicaSeriaB"
                print(f"📚 Continuă colecția principală: {url}")
            elif current_additional_index < len(ADDITIONAL_COLLECTIONS):
                # GĂSEȘTE PRIMA COLECȚIE INCOMPLETĂ
                for i in range(current_additional_index, len(ADDITIONAL_COLLECTIONS)):
                    potential_url = ADDITIONAL_COLLECTIONS[i]
                    if potential_url.rstrip('/') not in temp_downloader.dynamic_skip_urls:
                        url = potential_url
                        print(f"📚 Continuă colecția adițională {i + 1}/{len(ADDITIONAL_COLLECTIONS)}: {url}")
                        break
                else:
                    print("🎉 TOATE colecțiile au fost procesate complet!")
                    print("💡 Pentru a reporni de la început, șterge state.json")
                    return True
            else:
                print("🎉 TOATE colecțiile au fost procesate complet!")
                print("💡 Pentru a reporni de la început, șterge state.json")
                return True

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