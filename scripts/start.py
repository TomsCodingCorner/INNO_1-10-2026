"""One-time local bootstrap. Re-imports the provided demo workflow; use compose start thereafter."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
def run(*args):
    print('>', ' '.join(args),flush=True)
    subprocess.run(args,cwd=root,check=True)
try:
    run('docker','compose','version')
    run(sys.executable,str(root/'scripts/setup.py'))
    run('docker','compose','up','-d','--build','api')
    # Offline CLI writes prevent concurrent n8n database migration/import operations.
    run('docker','compose','stop','n8n')
    run('docker','compose','run','--rm','--no-deps','n8n','import:workflow','--input=/workflows/workflow.json')
    run('docker','compose','run','--rm','--no-deps','n8n','update:workflow','--id=zorgagentDemo01','--active=true')
    run('docker','compose','up','-d','n8n')
except (OSError,subprocess.CalledProcessError) as exc:
    print('Starten gestopt:',exc,file=sys.stderr)
    print('Controleer Docker Desktop en volg de handmatige stappen in README.md.',file=sys.stderr)
    raise SystemExit(1)
print('Wacht kort op n8n. Open http://localhost:8000. Reviewer-key staat lokaal in .env.')
print('n8n-editor: http://localhost:5678 (maak bij eerste bezoek je lokale beheerdersaccount).')
print('Herstart later met docker compose start; start.py importeert de geleverde demo opnieuw.')
