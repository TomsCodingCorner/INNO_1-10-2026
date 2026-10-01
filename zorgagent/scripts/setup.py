"""Generate local-only secrets. Never overwrites an existing .env."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
p=root/'.env'
if p.exists():
    print('.env bestaat al; niet overschreven.')
else:
    p.write_text('REVIEWER_KEY='+secrets.token_urlsafe(32)+'\nINTERNAL_KEY='+secrets.token_urlsafe(32)+'\nDEMO_MODE=true\nN8N_IMAGE=docker.n8n.io/n8nio/n8n:1.112.6\n')
    try: p.chmod(0o600)
    except OSError: pass
    print('.env aangemaakt. Lees REVIEWER_KEY lokaal uit dit bestand voor het reviewer-scherm.')
