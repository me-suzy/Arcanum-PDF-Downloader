import os
import subprocess
import sys

# Căi posibile pentru Git pe Windows
GIT_PATHS = [
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Program Files (x86)\Git\bin\git.exe",
    r"D:\Program Files\Git\bin\git.exe",
    r"D:\Program Files (x86)\Git\bin\git.exe",
    "git"  # Dacă este deja în PATH
]

def find_git():
    """Găsește Git pe sistem"""
    print("🔍 Caut Git pe sistem...")

    for git_path in GIT_PATHS:
        try:
            if git_path == "git":
                result = subprocess.run(["git", "--version"],
                                      capture_output=True, timeout=5)
            else:
                if os.path.exists(git_path):
                    result = subprocess.run([git_path, "--version"],
                                          capture_output=True, timeout=5)
                else:
                    continue

            if result.returncode == 0:
                print(f"✅ Git găsit: {git_path}")
                print(f"   Versiune: {result.stdout.decode().strip()}")
                return git_path

        except Exception as e:
            continue

    print("❌ Git nu a fost găsit!")
    return None

def configure_git(git_path):
    """Configurează Git cu credentialele"""
    print(f"\n⚙️  Configurez Git...")

    try:
        # Configurează numele și email-ul
        subprocess.run([git_path, "config", "--global", "user.name", "me-suzy"],
                      check=True, timeout=10)
        subprocess.run([git_path, "config", "--global", "user.email", "me-suzy@users.noreply.github.com"],
                      check=True, timeout=10)

        print("✅ Git configurat cu succes!")
        return True

    except Exception as e:
        print(f"❌ Eroare la configurarea Git: {e}")
        return False

def add_git_to_path(git_path):
    """Adaugă Git la PATH pentru sesiunea curentă"""
    if git_path != "git" and os.path.exists(git_path):
        git_dir = os.path.dirname(git_path)
        current_path = os.environ.get('PATH', '')

        if git_dir not in current_path:
            os.environ['PATH'] = git_dir + os.pathsep + current_path
            print(f"✅ Git adăugat la PATH: {git_dir}")
            return True

    return False

def test_git_operations(git_path):
    """Testează operațiile Git de bază"""
    print(f"\n🧪 Testez operațiile Git...")

    test_dir = "temp_git_test"

    try:
        # Creează director de test
        os.makedirs(test_dir, exist_ok=True)
        os.chdir(test_dir)

        # Test git init
        subprocess.run([git_path, "init"], check=True, capture_output=True, timeout=10)

        # Creează fișier test
        with open("test.txt", "w") as f:
            f.write("Test Git")

        # Test git add
        subprocess.run([git_path, "add", "test.txt"], check=True, capture_output=True, timeout=10)

        # Test git commit
        subprocess.run([git_path, "commit", "-m", "Test commit"],
                      check=True, capture_output=True, timeout=10)

        print("✅ Toate operațiile Git funcționează!")
        return True

    except Exception as e:
        print(f"❌ Eroare la testarea Git: {e}")
        return False
    finally:
        # Cleanup
        try:
            os.chdir("..")
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)
        except:
            pass

def main():
    print("🔧 CONFIGURARE GIT PENTRU WINDOWS")
    print("=" * 40)

    # Găsește Git
    git_path = find_git()
    if not git_path:
        print("\n💡 SOLUȚII:")
        print("   1. Reinstalează Git și adaugă la PATH")
        print("   2. Sau descarcă de la: https://git-scm.com/download/win")
        print("   3. În timpul instalării, alege 'Add Git to PATH'")
        return False

    # Configurează Git
    if not configure_git(git_path):
        return False

    # Adaugă la PATH dacă e nevoie
    add_git_to_path(git_path)

    # Testează operațiile
    if not test_git_operations(git_path):
        return False

    print(f"\n🎉 GIT CONFIGURAT CU SUCCES!")
    print(f"✅ Calea Git: {git_path}")
    print(f"✅ User: me-suzy")
    print(f"✅ Email: me-suzy@users.noreply.github.com")
    print(f"✅ Operații testate și funcționale")

    print(f"\n🚀 URMĂTORUL PAS:")
    print("   Rulează din nou script-ul principal pentru template-uri!")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)