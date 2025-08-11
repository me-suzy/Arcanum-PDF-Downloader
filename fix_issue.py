#!/usr/bin/env python3
"""
SCRIPT PENTRU CORECȚIA IMEDIATĂ a issue-ului StudiiSiCercetariMecanicaSiAplicata_1963
Rulează acest script pentru a corecta manual problemele identificate.
"""

import json
import os
import shutil
from datetime import datetime

def fix_current_issue():
    """Corectează manual issue-ul problematic"""

    problematic_url = "https://adt.arcanum.com/ro/view/StudiiSiCercetariMecanicaSiAplicata_1963"

    print("🔧 CORECTEZ MANUAL issue-ul problematic...")
    print(f"📍 URL: {problematic_url}")
    print("📊 Problema: 249/1565 pagini (marcat greșit ca complet)")
    print("=" * 60)

    # PASUL 1: Corectează skip_urls.json
    skip_path = "skip_urls.json"
    if os.path.exists(skip_path):
        print("🔄 Corectez skip_urls.json...")

        # Creează backup
        backup_skip = f"{skip_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(skip_path, backup_skip)
        print(f"💾 Backup creat: {backup_skip}")

        # Încarcă și corectează
        with open(skip_path, "r", encoding="utf-8") as f:
            skip_data = json.load(f)

        completed_urls = skip_data.get("completed_urls", [])
        original_count = len(completed_urls)

        # Șterge URL-ul problematic din toate variantele posibile
        urls_to_remove = [
            problematic_url,
            problematic_url.rstrip('/'),
            problematic_url + '/'
        ]

        for url in urls_to_remove:
            if url in completed_urls:
                completed_urls.remove(url)
                print(f"🗑️ ȘTERS din skip_urls: {url}")

        skip_data["completed_urls"] = completed_urls
        skip_data["last_updated"] = datetime.now().isoformat()

        # Salvează
        with open(skip_path, "w", encoding="utf-8") as f:
            json.dump(skip_data, f, indent=2, ensure_ascii=False)

        print(f"✅ skip_urls.json corectat: {original_count} → {len(completed_urls)} URL-uri")
    else:
        print("⚠ skip_urls.json nu există")

    # PASUL 2: Corectează state.json
    state_path = "state.json"
    if os.path.exists(state_path):
        print("\n🔄 Corectez state.json...")

        # Creează backup
        backup_state = f"{state_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(state_path, backup_state)
        print(f"💾 Backup creat: {backup_state}")

        # Încarcă și corectează
        with open(state_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)

        issues = state_data.get("downloaded_issues", [])
        found_issues = []
        duplicates_removed = 0

        # Găsește și corectează toate variantele URL-ului
        corrected_issues = []
        for issue in issues:
            url = issue.get("url", "").rstrip('/')

            if url == problematic_url.rstrip('/'):
                found_issues.append(issue)
            else:
                corrected_issues.append(issue)

        if found_issues:
            print(f"🔍 Găsite {len(found_issues)} intrări pentru URL-ul problematic:")

            # Găsește cea mai bună versiune (cu cel mai mult progres)
            best_issue = None
            best_progress = -1

            for issue in found_issues:
                progress = issue.get("last_successful_segment_end", 0)
                print(f"   📊 Progres: {progress}, completed_at: {bool(issue.get('completed_at'))}")

                if progress > best_progress:
                    best_progress = progress
                    best_issue = issue

            if len(found_issues) > 1:
                duplicates_removed = len(found_issues) - 1
                print(f"🗑️ Elimin {duplicates_removed} dubluri")

            # Corectează cea mai bună versiune
            if best_issue:
                print(f"🔧 Corectez issue-ul cu progresul {best_progress}...")

                best_issue.update({
                    "url": problematic_url,
                    "pages": 0,  # Resetează pentru că nu e complet
                    "completed_at": "",  # Resetează
                    "last_successful_segment_end": 249,  # Păstrează progresul actual
                    "total_pages": 1565  # CORECTEAZĂ cu valoarea reală!
                })

                corrected_issues.append(best_issue)
                print("✅ Issue corectat cu:")
                print(f"   📄 total_pages: 1565")
                print(f"   🔄 last_successful_segment_end: 249")
                print(f"   ❌ completed_at: '' (gol)")
                print(f"   📊 Status: PARȚIAL (va fi continuat)")
        else:
            print("⚠ Nu am găsit issue-ul problematic în state.json")

        # Actualizează state-ul
        state_data["downloaded_issues"] = corrected_issues

        # Recalculează count-ul corect
        actual_completed = len([i for i in corrected_issues if i.get("completed_at")])
        state_data["count"] = actual_completed

        # Salvează
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False)

        print(f"✅ state.json corectat:")
        print(f"   📊 Issues: {len(issues)} → {len(corrected_issues)}")
        print(f"   🗑️ Dubluri eliminate: {duplicates_removed}")
        print(f"   ✅ Complet recalculat: {actual_completed}")
    else:
        print("⚠ state.json nu există")

    print("\n" + "=" * 60)
    print("🎉 CORECȚIA COMPLETĂ!")
    print("🎯 Acum poți rula din nou scriptul - va continua de la pagina 250")
    print("📊 Progres așteptat: 249 → 1565 pagini")
    print("=" * 60)


def verify_correction():
    """Verifică că corecția a funcționat"""
    problematic_url = "https://adt.arcanum.com/ro/view/StudiiSiCercetariMecanicaSiAplicata_1963"

    print("\n🔍 VERIFICARE POST-CORECȚIE:")

    # Verifică skip_urls.json
    if os.path.exists("skip_urls.json"):
        with open("skip_urls.json", "r", encoding="utf-8") as f:
            skip_data = json.load(f)

        completed_urls = skip_data.get("completed_urls", [])
        is_in_skip = any(url.rstrip('/') == problematic_url.rstrip('/') for url in completed_urls)

        print(f"📋 skip_urls.json: {'❌ ÎNCĂ ÎN SKIP' if is_in_skip else '✅ ȘTERS DIN SKIP'}")

    # Verifică state.json
    if os.path.exists("state.json"):
        with open("state.json", "r", encoding="utf-8") as f:
            state_data = json.load(f)

        issues = state_data.get("downloaded_issues", [])
        found = None

        for issue in issues:
            if issue.get("url", "").rstrip('/') == problematic_url.rstrip('/'):
                found = issue
                break

        if found:
            total = found.get("total_pages")
            progress = found.get("last_successful_segment_end", 0)
            completed = found.get("completed_at", "")

            print(f"📊 state.json găsit:")
            print(f"   📄 total_pages: {total} {'✅' if total == 1565 else '❌'}")
            print(f"   🔄 progres: {progress} {'✅' if progress == 249 else '❌'}")
            print(f"   ❌ completed_at: {'GOL ✅' if not completed else 'SETAT ❌'}")
        else:
            print("📊 state.json: ❌ NU GĂSIT")


if __name__ == "__main__":
    print("🚨 SCRIPT DE CORECȚIE URGENTĂ")
    print("Corectez issue-ul StudiiSiCercetariMecanicaSiAplicata_1963")
    print()

    fix_current_issue()
    verify_correction()

    print("\n🎯 URMĂTORII PAȘI:")
    print("1. Verifică că corecția a funcționat (vezi output-ul de mai sus)")
    print("2. Rulează din nou scriptul principal Claude-FINAL.py")
    print("3. Scriptul va detecta automat issue-ul parțial și va continua de la pagina 250")
    print("4. Va descărca paginile 250-1565 pentru a completa issue-ul")