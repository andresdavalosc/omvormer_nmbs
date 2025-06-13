import subprocess
import sys
import os

# Pad naar je lokale repo folder
REPO_DIR = "/home/wie/omvormer_nmbs"

# Bestandsnaam die je wil runnen
SCRIPT_NAME = "Python.py"

def run_command(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, cwd=cwd,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result

def main():
    # Eerst kijken of er nieuwe commits zijn
    print("Controleren op updates in GitHub repo...")

    # git fetch haalt remote veranderingen binnen zonder te mergen
    fetch_res = run_command("git fetch", cwd=REPO_DIR)
    if fetch_res.returncode != 0:
        print("Fout bij git fetch:", fetch_res.stderr)
        sys.exit(1)

    # Check of remote HEAD is veranderd tov lokale HEAD
    local_head = run_command("git rev-parse HEAD", cwd=REPO_DIR).stdout.strip()
    remote_head = run_command("git rev-parse origin/main", cwd=REPO_DIR).stdout.strip()  # pas evt aan branchnaam

    if local_head != remote_head:
        print("Nieuwe update gevonden! Pullen en uitvoeren...")
        pull_res = run_command("git pull", cwd=REPO_DIR)
        if pull_res.returncode != 0:
            print("Fout bij git pull:", pull_res.stderr)
            sys.exit(1)
        else:
            print("Update binnengehaald. Script runnen...")

            # Script runnen (eventueel je eigen command hier)
            run_res = run_command(f"python3 {SCRIPT_NAME}", cwd=REPO_DIR)
            if run_res.returncode != 0:
                print("Fout bij uitvoeren script:", run_res.stderr)
            else:
                print("Script succesvol uitgevoerd.")
    else:
        print("Geen updates gevonden.")

if __name__ == "__main__":
    main()
