#!/usr/bin/env python3
"""
Script de monitorizare pentru Arcanum Downloader
- Generează rapoarte de progres
- Verifică spațiul pe disk
- Trimite rapoarte prin email (opțional)
- Poate fi rulat de la distanță pentru monitorizare
"""

import os
import json
import psutil
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Configurații
DOWNLOAD_DIR = "D:\\"
BACKUP_DIR = "E:\\"
STATE_FILE = os.path.join(DOWNLOAD_DIR, "state.json")
LOG_FILE = os.path.join(DOWNLOAD_DIR, "arcanum_daily_log.txt")
MOVED_FOLDERS_FILE = os.path.join(DOWNLOAD_DIR, "moved_folders.json")

# Configurare email (opțional - completează cu datele tale)
EMAIL_CONFIG = {
    "enabled": False,  # Setează True pentru a activa emailul
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "from_email": "your_email@gmail.com",
    "from_password": "your_app_password",  # App password pentru Gmail
    "to_email": "your_email@gmail.com"
}

ADDITIONAL_COLLECTIONS = [
    "https://adt.arcanum.com/ro/collection/Convietuirea/",
    "https://adt.arcanum.com/ro/collection/StudiiSiCercetariMatematice/",
    "https://adt.arcanum.com/ro/collection/MinePetrolGaze/"
]


class ArcanumMonitor:
    def __init__(self):
        self.report_time = datetime.now()

    def get_disk_space(self, drive):
        """Returnează informații despre spațiul pe disk"""
        try:
            usage = psutil.disk_usage(drive)
            return {
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round((usage.total - usage.free) / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "free_mb": round(usage.free / (1024**2), 0),
                "percent_used": round(((usage.total - usage.free) / usage.total) * 100, 1)
            }
        except Exception as e:
            return {"error": str(e)}

    def load_state(self):
        """Încarcă starea curentă"""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                return {"error": f"Eroare la citirea state.json: {e}"}
        return {"error": "state.json nu există"}

    def load_moved_folders(self):
        """Încarcă lista folderelor mutate"""
        if os.path.exists(MOVED_FOLDERS_FILE):
            try:
                with open(MOVED_FOLDERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"moved_folders": [], "last_cleanup": ""}

    def get_recent_logs(self, hours=24):
        """Extrage log-urile recente"""
        if not os.path.exists(LOG_FILE):
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_logs = []

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line in lines[-200:]:  # Doar ultimele 200 de linii
                if line.strip():
                    # Extrage timestamp-ul din log
                    if line.startswith("["):
                        try:
                            timestamp_str = line.split("]")[0][1:]
                            log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if log_time >= cutoff_time:
                                recent_logs.append(line.strip())
                        except:
                            pass
        except Exception as e:
            recent_logs.append(f"Eroare la citirea log-ului: {e}")

        return recent_logs

    def analyze_progress(self, state):
        """Analizează progresul descărcărilor"""
        if "error" in state:
            return {"error": state["error"]}

        downloaded_issues = state.get("downloaded_issues", [])
        completed_count = len([i for i in downloaded_issues if i.get("completed_at")])
        in_progress_count = len([i for i in downloaded_issues if i.get("last_successful_segment_end", 0) > 0 and not i.get("completed_at")])

        total_pages = sum(i.get("pages", 0) for i in downloaded_issues if i.get("completed_at"))

        # Calculează progresul pe colecții
        main_completed = state.get("main_collection_completed", False)
        current_additional_index = state.get("current_additional_collection_index", 0)

        collections_progress = {
            "main_collection_completed": main_completed,
            "additional_collections_completed": current_additional_index,
            "additional_collections_total": len(ADDITIONAL_COLLECTIONS),
            "current_collection": ""
        }

        if not main_completed:
            collections_progress["current_collection"] = "Colecția principală (GazetaMatematicaSiFizicaSeriaB)"
        elif current_additional_index < len(ADDITIONAL_COLLECTIONS):
            collections_progress["current_collection"] = ADDITIONAL_COLLECTIONS[current_additional_index]
        else:
            collections_progress["current_collection"] = "TOATE COMPLETE!"

        return {
            "completed_issues": completed_count,
            "in_progress_issues": in_progress_count,
            "total_pages_downloaded": total_pages,
            "daily_count": state.get("count", 0),
            "daily_limit_hit": state.get("daily_limit_hit", False),
            "last_update": state.get("date", ""),
            "collections_progress": collections_progress
        }

    def count_folders_and_size(self, directory):
        """Contorizează folderele și dimensiunea totală"""
        if not os.path.exists(directory):
            return {"error": f"Directorul {directory} nu există"}

        folders = []
        total_size = 0

        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    # Calculează dimensiunea folderului
                    folder_size = 0
                    try:
                        for dirpath, dirnames, filenames in os.walk(item_path):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                try:
                                    folder_size += os.path.getsize(filepath)
                                except (OSError, FileNotFoundError):
                                    continue
                    except Exception:
                        folder_size = 0

                    folders.append({
                        "name": item,
                        "size_mb": round(folder_size / (1024**2), 2)
                    })
                    total_size += folder_size
        except Exception as e:
            return {"error": f"Eroare la scanarea folderelor: {e}"}

        return {
            "folder_count": len(folders),
            "total_size_gb": round(total_size / (1024**3), 2),
            "folders": sorted(folders, key=lambda x: x["size_mb"], reverse=True)[:10]  # Top 10
        }

    def generate_report(self):
        """Generează raportul complet"""
        report = {
            "timestamp": self.report_time.strftime("%Y-%m-%d %H:%M:%S"),
            "disk_space": {
                "D_drive": self.get_disk_space("D:\\"),
                "E_drive": self.get_disk_space("E:\\")
            },
            "download_progress": self.analyze_progress(self.load_state()),
            "folders_info": {
                "D_drive": self.count_folders_and_size(DOWNLOAD_DIR),
                "E_drive": self.count_folders_and_size(BACKUP_DIR)
            },
            "moved_folders": self.load_moved_folders(),
            "recent_logs": self.get_recent_logs(24)
        }

        return report

    def format_report_text(self, report):
        """Formatează raportul pentru afișare text"""
        lines = []
        lines.append("=" * 80)
        lines.append(f"RAPORT ARCANUM DOWNLOADER - {report['timestamp']}")
        lines.append("=" * 80)

        # Spațiu pe disk
        lines.append("\n📊 SPAȚIU PE DISK:")
        d_space = report['disk_space']['D_drive']
        e_space = report['disk_space']['E_drive']

        if 'error' not in d_space:
            lines.append(f"   D:\\ - {d_space['free_gb']} GB liberi din {d_space['total_gb']} GB ({d_space['percent_used']}% folosit)")
            if d_space['free_mb'] < 500:
                lines.append(f"   ⚠️  ALERTĂ: Doar {d_space['free_mb']} MB rămas pe D:\\!")

        if 'error' not in e_space:
            lines.append(f"   E:\\ - {e_space['free_gb']} GB liberi din {e_space['total_gb']} GB ({e_space['percent_used']}% folosit)")

        # Progres descărcări
        lines.append("\n📥 PROGRES DESCĂRCĂRI:")
        progress = report['download_progress']

        if 'error' not in progress:
            lines.append(f"   ✅ Issue-uri complete: {progress['completed_issues']}")
            lines.append(f"   ⏳ Issue-uri în progres: {progress['in_progress_issues']}")
            lines.append(f"   📄 Total pagini descărcate: {progress['total_pages_downloaded']}")
            lines.append(f"   📊 Progres zilnic: {progress['daily_count']}/105")

            if progress['daily_limit_hit']:
                lines.append(f"   ⚠️  Limita zilnică atinsă!")

            # Progres colecții
            col_prog = progress['collections_progress']
            lines.append(f"\n📚 PROGRES COLECȚII:")
            lines.append(f"   Principală: {'✅ Completă' if col_prog['main_collection_completed'] else '⏳ În progres'}")
            lines.append(f"   Adiționale: {col_prog['additional_collections_completed']}/{col_prog['additional_collections_total']}")
            lines.append(f"   Curent: {col_prog['current_collection']}")

        # Foldere
        lines.append("\n📁 FOLDERE:")
        d_folders = report['folders_info']['D_drive']
        e_folders = report['folders_info']['E_drive']

        if 'error' not in d_folders:
            lines.append(f"   D:\\ - {d_folders['folder_count']} foldere, {d_folders['total_size_gb']} GB")

        if 'error' not in e_folders:
            lines.append(f"   E:\\ - {e_folders['folder_count']} foldere, {e_folders['total_size_gb']} GB")

        moved = report['moved_folders']
        if moved.get('moved_folders'):
            lines.append(f"   🔄 Foldere mutate pe E:\\: {len(moved['moved_folders'])}")
            lines.append(f"   📅 Ultima curățare: {moved.get('last_cleanup', 'N/A')}")

        # Log-uri recente (doar ultimele 10)
        recent_logs = report['recent_logs']
        if recent_logs:
            lines.append(f"\n📋 ACTIVITATE RECENTĂ (ultimele 10 intrări):")
            for log in recent_logs[-10:]:
                lines.append(f"   {log}")

        lines.append("\n" + "=" * 80)

        return "\n".join(lines)

    def send_email_report(self, report_text):
        """Trimite raportul prin email"""
        if not EMAIL_CONFIG["enabled"]:
            return False

        try:
            msg = MimeMultipart()
            msg['From'] = EMAIL_CONFIG["from_email"]
            msg['To'] = EMAIL_CONFIG["to_email"]
            msg['Subject'] = f"Raport Arcanum Downloader - {self.report_time.strftime('%Y-%m-%d')}"

            msg.attach(MimeText(report_text, 'plain', 'utf-8'))

            server = smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"])
            server.starttls()
            server.login(EMAIL_CONFIG["from_email"], EMAIL_CONFIG["from_password"])
            text = msg.as_string()
            server.sendmail(EMAIL_CONFIG["from_email"], EMAIL_CONFIG["to_email"], text)
            server.quit()

            print("✅ Raport trimis prin email cu succes!")
            return True

        except Exception as e:
            print(f"❌ Eroare la trimiterea email-ului: {e}")
            return False

    def save_report_to_file(self, report_text):
        """Salvează raportul într-un fișier"""
        try:
            report_filename = f"report_{self.report_time.strftime('%Y%m%d_%H%M%S')}.txt"
            report_path = os.path.join(DOWNLOAD_DIR, report_filename)

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_text)

            print(f"📄 Raport salvat în: {report_path}")
            return report_path

        except Exception as e:
            print(f"❌ Eroare la salvarea raportului: {e}")
            return None


def main():
    print("🔍 Generez raport de monitorizare Arcanum Downloader...")

    monitor = ArcanumMonitor()
    report = monitor.generate_report()
    report_text = monitor.format_report_text(report)

    # Afișează raportul
    print(report_text)

    # Salvează raportul
    monitor.save_report_to_file(report_text)

    # Trimite prin email dacă e activat
    if EMAIL_CONFIG["enabled"]:
        monitor.send_email_report(report_text)

    # Salvează și raportul JSON pentru procesare automată
    try:
        json_filename = f"report_{monitor.report_time.strftime('%Y%m%d_%H%M%S')}.json"
        json_path = os.path.join(DOWNLOAD_DIR, json_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📊 Raport JSON salvat în: {json_path}")

    except Exception as e:
        print(f"⚠️ Nu am putut salva raportul JSON: {e}")


if __name__ == "__main__":
    main()