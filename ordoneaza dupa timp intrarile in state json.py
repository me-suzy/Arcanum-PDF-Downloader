#!/usr/bin/env python3
"""
Script de reparare pentru state.json - aplică sortarea cronologică și marchează issue-urile complete
"""

import json
import os
import shutil
from datetime import datetime

def fix_state_json():
    """Repară state.json cu sortarea cronologică corectă și issue-urile complete"""
    
    state_file = "D:\\state.json"
    
    if not os.path.exists(state_file):
        print(f"❌ Nu găsesc {state_file}")
        return
    
    # Creează backup
    backup_file = state_file + ".backup_before_fix"
    shutil.copy2(state_file, backup_file)
    print(f"💾 Backup creat: {backup_file}")
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        issues = data.get("downloaded_issues", [])
        print(f"🔍 Procesez {len(issues)} issues...")
        
        # PASUL 1: Identifică și marchează issue-urile complete care nu sunt marcate
        fixed_issues = []
        now_iso = datetime.now().isoformat(timespec="seconds")
        
        for issue in issues:
            last_segment = issue.get("last_successful_segment_end", 0)
            total_pages = issue.get("total_pages", 0)
            completed_at = issue.get("completed_at", "")
            url = issue.get("url", "")
            
            # Verifică dacă issue-ul e complet dar nu e marcat
            if (last_segment > 0 and 
                total_pages > 0 and 
                last_segment >= total_pages and 
                not completed_at):
                
                print(f"🔧 REPAIR: {url.split('/')[-1]} - marchez ca terminat ({last_segment}/{total_pages})")
                
                # Marchează ca terminat
                issue["completed_at"] = now_iso
                issue["pages"] = last_segment
                
            fixed_issues.append(issue)
        
        # PASUL 2: Sortează corect - parțiale primul, apoi complete cronologic
        partial_issues = []
        complete_issues = []
        
        for issue in fixed_issues:
            completed_at = issue.get("completed_at", "")
            last_segment = issue.get("last_successful_segment_end", 0)
            total_pages = issue.get("total_pages", 0)
            
            # Issue parțial: are progres dar nu e complet
            is_partial = (last_segment > 0 and 
                         (not completed_at or 
                          (total_pages > 0 and last_segment < total_pages)))
            
            if is_partial:
                partial_issues.append(issue)
            else:
                complete_issues.append(issue)
        
        # Sortează parțialele după progres (desc)
        partial_issues.sort(key=lambda x: x.get("last_successful_segment_end", 0), reverse=True)
        
        # Sortează complete-urile cronologic (cel mai recent primul)
        def sort_key_for_complete(issue):
            completed_at = issue.get("completed_at", "")
            if completed_at:
                try:
                    return datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except:
                    return datetime.min
            return datetime.min
        
        complete_issues.sort(key=sort_key_for_complete, reverse=True)
        
        print(f"\n📊 REZULTAT SORTARE:")
        print(f"   🔄 Issue-uri parțiale: {len(partial_issues)}")
        print(f"   ✅ Issue-uri complete: {len(complete_issues)}")
        
        # Afișează ordinea cronologică pentru verificare
        if complete_issues:
            print(f"\n✅ ORDINEA CRONOLOGICĂ CORECTATĂ:")
            for i, issue in enumerate(complete_issues):
                url = issue.get("url", "").split("/")[-1]
                completed_at = issue.get("completed_at", "")
                try:
                    dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = completed_at
                print(f"   {i+1}. {url} - {formatted_date}")
        
        # PASUL 3: Reconstruiește lista finală
        final_issues = partial_issues + complete_issues
        
        # PASUL 4: Actualizează count-ul corect
        completed_count = len([i for i in final_issues if i.get("completed_at")])
        data["downloaded_issues"] = final_issues
        data["count"] = max(data.get("count", 0), completed_count)
        
        # PASUL 5: Salvează JSON-ul reparat
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ REPARARE COMPLETĂ!")
        print(f"   📊 Total issues: {len(final_issues)}")
        print(f"   🔄 Parțiale: {len(partial_issues)}")
        print(f"   ✅ Complete: {len(complete_issues)}")
        print(f"   🎯 Count actualizat: {data['count']}")
        
        # Afișează parțialele pentru verificare
        if partial_issues:
            print(f"\n🔄 ISSUE-URI PARȚIALE RĂMASE:")
            for issue in partial_issues:
                url = issue.get("url", "").split("/")[-1]
                progress = issue.get("last_successful_segment_end", 0)
                total = issue.get("total_pages", 0)
                print(f"   📄 {url} - progres: {progress}/{total}")
        
    except Exception as e:
        print(f"❌ Eroare la repararea JSON: {e}")
        # Restabilește din backup
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, state_file)
            print(f"🔄 JSON restabilit din backup")

def update_skip_urls():
    """Actualizează skip_urls.json cu issue-urile complete"""
    
    state_file = "D:\\state.json"
    skip_file = "D:\\skip_urls.json"
    
    if not os.path.exists(state_file):
        print(f"❌ Nu găsesc {state_file}")
        return
    
    try:
        # Citește state.json
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)
        
        # Extrage URL-urile complete
        completed_urls = []
        static_urls = ["https://adt.arcanum.com/ro/view/Convietuirea_1997-1998"]
        
        for item in state_data.get("downloaded_issues", []):
            completed_at = item.get("completed_at")
            total_pages = item.get("total_pages")
            last_segment = item.get("last_successful_segment_end", 0)
            
            if (completed_at and 
                total_pages and 
                total_pages > 0 and 
                last_segment >= total_pages):
                completed_urls.append(item["url"])
        
        all_completed = static_urls + completed_urls
        
        # Actualizează skip_urls.json
        skip_data = {
            "last_updated": datetime.now().isoformat(),
            "completed_urls": sorted(list(set(all_completed))),
            "completed_collections": []
        }
        
        with open(skip_file, "w", encoding="utf-8") as f:
            json.dump(skip_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📋 SKIP_URLS ACTUALIZAT:")
        print(f"   🔗 URLs complete: {len(skip_data['completed_urls'])}")
        
    except Exception as e:
        print(f"❌ Eroare la actualizarea skip_urls.json: {e}")

if __name__ == "__main__":
    print("🔧 REPARARE STATE.JSON - SORTARE CRONOLOGICĂ")
    print("=" * 60)
    
    fix_state_json()
    update_skip_urls()
    
    print("\n" + "=" * 60)
    print("✅ REPARARE COMPLETĂ - Rulează din nou verificatorul pentru confirmare!")