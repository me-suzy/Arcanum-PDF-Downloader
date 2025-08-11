
import json
import os

def manual_state_fix():
    """Manual fix for your current state file"""
    state_path = r"D:\state.json"

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)

        # Find and fix the problematic issue
        for item in state.get('downloaded_issues', []):
            if 'StudiiSiCercetariMecanicaSiAplicata_1957' in item.get('url', ''):
                if not item.get('total_pages'):
                    item['total_pages'] = 1407
                    print(f"✅ Fixed total_pages for problematic issue")
                    break

        # Save the fixed state
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        print("✅ State file fixed successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to fix state file: {e}")
        return False

# Run this fix immediately:
if __name__ == "__main__":
    manual_state_fix()