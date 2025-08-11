#!/usr/bin/env python3
"""
Script simplu pentru resetarea flag-ului de limită zilnică
Rulează înainte de scriptul principal pentru a permite continuarea în zile noi
"""

import json
import os
from datetime import datetime

def reset_daily_limit_flag():
    """Resetează flag-ul daily_limit_hit pentru ziua nouă"""
    state_file = "state.json"
    
    if not os.path.exists(state_file):
        print("🔍 state.json nu există încă - nu e nimic de resetat")
        return
    
    try:
        # Încarcă state-ul curent
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        
        today = datetime.now().strftime("%Y-%m-%d")
        current_date = state.get("date", "")
        daily_limit_hit = state.get("daily_limit_hit", False)
        
        print(f"📅 Data curentă: {today}")
        print(f"📅 Data din state: {current_date}")
        print(f"🚫 Limită zilnică setată: {daily_limit_hit}")
        
        # Verifică dacă e o zi nouă
        if current_date != today:
            print(f"🆕 ZI NOUĂ detectată! Resetez flag-ul de limită zilnică")
            
            # Resetează flag-ul și actualizează data
            state["daily_limit_hit"] = False
            state["date"] = today
            
            # Salvează state-ul actualizat
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Flag-ul daily_limit_hit resetat pentru ziua nouă: {today}")
            print(f"🚀 Scriptul principal poate continua de unde a rămas!")
            
        elif daily_limit_hit:
            print(f"⚠ Limita zilnică încă activă pentru astăzi ({today})")
            print(f"⏰ Va fi resetată automat mâine la prima rulare")
            
        else:
            print(f"✅ Flag-ul de limită nu este setat - scriptul poate rula normal")
            
    except Exception as e:
        print(f"❌ Eroare la resetarea flag-ului: {e}")
        print(f"🔄 Scriptul principal va încerca să continue oricum...")

if __name__ == "__main__":
    print("🔄 RESETARE FLAG LIMITĂ ZILNICĂ")
    print("=" * 50)
    reset_daily_limit_flag()
    print("=" * 50)
    print("✅ VERIFICARE COMPLETĂ")