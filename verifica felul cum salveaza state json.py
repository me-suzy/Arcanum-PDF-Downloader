#!/usr/bin/env python3
"""
Script mic pentru verificarea ordinii cronologice în state.json
"""

import json
import os
from datetime import datetime

def check_json_structure():
    """Verifică cum sunt salvate issue-urile în state.json"""
    
    state_file = "D:\\state.json"
    
    if not os.path.exists(state_file):
        print(f"❌ Nu găsesc {state_file}")
        return
    
    print("🔍 ANALIZA state.json")
    print("=" * 60)
    
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        issues = data.get("downloaded_issues", [])
        
        print(f"📊 Total issues găsite: {len(issues)}")
        print(f"📊 Count în JSON: {data.get('count', 0)}")
        print(f"📊 Pages downloaded: {data.get('pages_downloaded', 0)}")
        
        # Separă issue-urile parțiale și complete
        partial_issues = []
        complete_issues = []
        
        for issue in issues:
            completed_at = issue.get("completed_at", "")
            if completed_at:
                complete_issues.append(issue)
            else:
                partial_issues.append(issue)
        
        print(f"\n📋 STRUCTURA:")
        print(f"   🔄 Issue-uri parțiale: {len(partial_issues)}")
        print(f"   ✅ Issue-uri complete: {len(complete_issues)}")
        
        # Verifică issue-urile parțiale
        if partial_issues:
            print(f"\n🔄 ISSUE-URI PARȚIALE:")
            for i, issue in enumerate(partial_issues[:5]):  # Primele 5
                url = issue.get("url", "").split("/")[-1]
                progress = issue.get("last_successful_segment_end", 0)
                total = issue.get("total_pages", 0)
                print(f"   {i+1}. {url} - progres: {progress}/{total}")
        
        # Verifică ordinea cronologică a celor complete
        if complete_issues:
            print(f"\n✅ ISSUE-URI COMPLETE (ordinea din JSON):")
            
            # Afișează primele 10 pentru verificare
            for i, issue in enumerate(complete_issues[:10]):
                url = issue.get("url", "").split("/")[-1]
                completed_at = issue.get("completed_at", "N/A")
                pages = issue.get("pages", 0)
                
                # Formatează data pentru citire mai ușoară
                try:
                    dt = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = completed_at
                
                print(f"   {i+1}. {url}")
                print(f"      📅 Completat: {formatted_date}")
                print(f"      📄 Pagini: {pages}")
        
        # Verifică dacă sunt sortate cronologic corect
        print(f"\n🕐 VERIFICARE SORTARE CRONOLOGICĂ:")
        
        if len(complete_issues) >= 2:
            is_sorted_correctly = True
            previous_datetime = None
            
            for i, issue in enumerate(complete_issues):
                completed_at = issue.get("completed_at", "")
                try:
                    current_datetime = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    
                    if previous_datetime and current_datetime > previous_datetime:
                        is_sorted_correctly = False
                        url = issue.get("url", "").split("/")[-1]
                        print(f"   ❌ EROARE la poziția {i+1}: {url}")
                        print(f"      Este mai recent ({current_datetime}) decât precedentul ({previous_datetime})")
                    
                    previous_datetime = current_datetime
                except Exception as e:
                    print(f"   ⚠ Nu pot parsa data pentru issue-ul {i+1}: {completed_at}")
            
            if is_sorted_correctly:
                print("   ✅ Issue-urile complete sunt sortate CORECT cronologic (cel mai recent primul)")
                
                # Afișează prima și ultima dată pentru confirmare
                try:
                    first_date = datetime.fromisoformat(complete_issues[0].get("completed_at", "").replace('Z', '+00:00'))
                    last_date = datetime.fromisoformat(complete_issues[-1].get("completed_at", "").replace('Z', '+00:00'))
                    
                    print(f"   📅 Cel mai recent: {first_date.strftime('%Y-%m-%d %H:%M')}")
                    print(f"   📅 Cel mai vechi: {last_date.strftime('%Y-%m-%d %H:%M')}")
                except:
                    pass
            else:
                print("   ❌ Issue-urile complete NU sunt sortate corect cronologic!")
        
        # Verifică recent_links
        recent_links = data.get("recent_links", [])
        if recent_links:
            print(f"\n🔗 RECENT LINKS (primele 5):")
            for i, link in enumerate(recent_links[:5]):
                url = link.get("url", "").split("/")[-1]
                timestamp = link.get("timestamp", "N/A")
                pages = link.get("pages", 0)
                
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_date = timestamp
                    
                print(f"   {i+1}. {url} - {formatted_date} ({pages} pagini)")
        
        print(f"\n🎯 REZUMAT:")
        total_complete = len([i for i in issues if i.get("completed_at")])
        total_partial = len([i for i in issues if not i.get("completed_at") and i.get("last_successful_segment_end", 0) > 0])
        
        print(f"   📊 Total issues: {len(issues)}")
        print(f"   ✅ Complete: {total_complete}")
        print(f"   🔄 Parțiale: {total_partial}")
        print(f"   📄 Total pagini descărcate: {data.get('pages_downloaded', 0)}")
        
    except Exception as e:
        print(f"❌ Eroare la citirea JSON: {e}")

def check_skip_urls():
    """Verifică și skip_urls.json"""
    
    skip_file = "D:\\skip_urls.json"
    
    if not os.path.exists(skip_file):
        print(f"\n📋 Nu găsesc {skip_file}")
        return
    
    print(f"\n📋 ANALIZA skip_urls.json")
    print("=" * 40)
    
    try:
        with open(skip_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        completed_urls = data.get("completed_urls", [])
        completed_collections = data.get("completed_collections", [])
        last_updated = data.get("last_updated", "N/A")
        
        print(f"📊 URLs complete: {len(completed_urls)}")
        print(f"📊 Colecții complete: {len(completed_collections)}")
        print(f"📊 Ultima actualizare: {last_updated}")
        
        if completed_urls:
            print(f"\n🔗 URLS COMPLETE (primele 5):")
            for i, url in enumerate(completed_urls[:5]):
                issue_name = url.split("/")[-1]
                print(f"   {i+1}. {issue_name}")
        
        if completed_collections:
            print(f"\n📚 COLECȚII COMPLETE:")
            for i, collection in enumerate(completed_collections):
                collection_name = collection.split("/")[-1]
                print(f"   {i+1}. {collection_name}")
                
    except Exception as e:
        print(f"❌ Eroare la citirea skip_urls.json: {e}")

if __name__ == "__main__":
    print("🔍 VERIFICATOR JSON - ORDINEA CRONOLOGICĂ")
    print("=" * 70)
    
    check_json_structure()
    check_skip_urls()
    
    print("\n" + "=" * 70)
    print("✅ VERIFICARE COMPLETĂ")