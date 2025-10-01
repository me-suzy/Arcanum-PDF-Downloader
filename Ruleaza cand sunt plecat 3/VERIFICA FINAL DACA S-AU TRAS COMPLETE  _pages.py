import os
import re
import json

def load_state_json(json_path):
    """Încarcă fișierul state.json"""
    if not os.path.exists(json_path):
        print(f"❌ Fișierul {json_path} nu există!")
        return []

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # Verifică dacă este un array sau un obiect
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Dacă e un dict, poate are o cheie care conține lista
                # Încearcă să găsești prima listă din dict
                for value in data.values():
                    if isinstance(value, list):
                        return value
                return []
            else:
                print(f"⚠️  Structură JSON neașteptată în {json_path}")
                return []
    except json.JSONDecodeError as e:
        print(f"❌ Eroare la parsarea JSON: {e}")
        return []

def extract_key_from_url(url):
    """
    Extrage cheia din URL pentru matching
    Exemplu: https://adt.arcanum.com/ro/view/Energetica_1969 -> Energetica_1969
    """
    if not isinstance(url, str):
        return None
    match = re.search(r'/view/([^/?]+)', url)
    if match:
        return match.group(1)
    return None

def extract_key_from_folder(folder_name):
    """
    Extrage cheia din numele folderului pentru matching
    Exemplu: "Energetica, 1969 (Anul 17, nr. 2-8)" -> Energetica_1969
    """
    # Caută pattern-ul: cuvânt, anul
    match = re.search(r'^([^,]+),\s*(\d{4})', folder_name)
    if match:
        name = match.group(1).strip()
        year = match.group(2)
        # Elimină spațiile și creează cheia
        key = f"{name.replace(' ', '')}_{year}"
        return key
    return None

def extract_page_range_from_filename(filename):
    """Extrage intervalul de pagini din numele fișierului"""
    match = re.search(r'__pages(\d+)-(\d+)\.pdf$', filename)
    if match:
        start_page = int(match.group(1))
        end_page = int(match.group(2))
        return (start_page, end_page)
    return None

def calculate_segment_size(pdf_segments):
    """Calculează dimensiunea standard a unui segment bazat pe PDF-urile existente"""
    if not pdf_segments:
        return 49  # Default

    # Calculează dimensiunile tuturor segmentelor
    sizes = [end - start + 1 for start, end in pdf_segments]

    # Returnează dimensiunea cea mai comună (moda)
    # Sau media, dacă toate sunt similare
    if sizes:
        return max(set(sizes), key=sizes.count)
    return 49

def split_gap_into_segments(gap_start, gap_end, segment_size):
    """Împarte o gaură mare în segmente mai mici"""
    segments = []
    current = gap_start

    while current <= gap_end:
        segment_end = min(current + segment_size - 1, gap_end)
        segments.append((current, segment_end))
        current = segment_end + 1

    return segments

def find_all_gaps(base_directory, state_json_path):
    """Găsește toate găurile din secvențele PDF, inclusiv de la final"""

    # Încarcă state.json
    state_data = load_state_json(state_json_path)

    if not state_data:
        print("⚠️  Nu s-au putut încărca date din state.json")
        return

    # Creează un dicționar pentru matching rapid
    state_dict = {}
    for entry in state_data:
        if not isinstance(entry, dict):
            continue

        url = entry.get('url')
        if not url:
            continue

        key = extract_key_from_url(url)
        if key:
            state_dict[key] = {
                'total_pages': entry.get('total_pages', entry.get('pages', 0)),
                'title': entry.get('title', 'Unknown')
            }

    print(f"✅ Încărcat state.json cu {len(state_dict)} intrări\n")

    # Parcurge toate subfolderele
    for root, dirs, files in os.walk(base_directory):
        # Skip directorul de bază
        if root == base_directory:
            continue

        folder_name = os.path.basename(root)
        folder_key = extract_key_from_folder(folder_name)

        # Găsește informațiile despre total_pages din state.json
        total_pages = None
        if folder_key and folder_key in state_dict:
            total_pages = state_dict[folder_key]['total_pages']

        # Găsește toate fișierele PDF cu pattern-ul __pages
        pdf_segments = []
        for filename in files:
            if filename.endswith('.pdf') and '__pages' in filename:
                page_range = extract_page_range_from_filename(filename)
                if page_range:
                    pdf_segments.append(page_range)

        if not pdf_segments:
            continue

        # Sortează segmentele după pagina de început
        pdf_segments.sort(key=lambda x: x[0])

        # Calculează dimensiunea standard a segmentelor
        segment_size = calculate_segment_size(pdf_segments)

        # Verifică găurile în secvență (între PDF-uri existente)
        gaps = []
        for i in range(len(pdf_segments) - 1):
            current_end = pdf_segments[i][1]
            next_start = pdf_segments[i + 1][0]

            if next_start > current_end + 1:
                gaps.append((current_end + 1, next_start - 1))

        # Verifică dacă lipsesc PDF-uri de la final
        last_segment_end = pdf_segments[-1][1]

        if total_pages and total_pages > last_segment_end:
            gaps.append((last_segment_end + 1, total_pages))

        # Afișează doar dacă sunt probleme
        if gaps:
            print(f"{'='*80}")
            print(f"📁 {folder_name}")
            if folder_key:
                print(f"🔑 Key: {folder_key}")
            if total_pages:
                print(f"📄 Total pagini (din state.json): {total_pages}")
            else:
                print(f"⚠️  Total pagini: NECUNOSCUT (nu s-a găsit în state.json)")
                print(f"   Folder key generat: {folder_key}")
            print(f"📊 PDF-uri existente: {len(pdf_segments)}")
            print(f"   Primul segment: pages {pdf_segments[0][0]}-{pdf_segments[0][1]}")
            print(f"   Ultimul segment: pages {pdf_segments[-1][0]}-{last_segment_end}")
            print(f"   Dimensiune segment standard: {segment_size} pagini")
            print(f"{'='*80}")

            # Împarte fiecare gaură în segmente și afișează
            for gap_start, gap_end in gaps:
                gap_segments = split_gap_into_segments(gap_start, gap_end, segment_size)
                for seg_start, seg_end in gap_segments:
                    print(f"❌ GĂURĂ în secvență: pages {seg_start}-{seg_end}")

            print()

def main():
    # Directoarele
    base_dir = r"g:\Temporare"
    state_json = r"g:\state.json"

    if not os.path.exists(base_dir):
        print(f"❌ Directorul {base_dir} nu există!")
        return

    if not os.path.exists(state_json):
        print(f"❌ Fișierul {state_json} nu există!")
        return

    print("🔍 Verificare PDF-uri lipsă în colecții...\n")
    find_all_gaps(base_dir, state_json)
    print("✅ Verificare finalizată!")

if __name__ == "__main__":
    main()