"""Generate local-only secrets. Never overwrites an existing .env."""
from pathlib import Path
import secrets
root=Path(__file__).resolve().parents[1]
p=root/'.env'
defaults = {
    'REVIEWER_KEY': lambda: secrets.token_urlsafe(32),
    'INTERNAL_KEY': lambda: secrets.token_urlsafe(32),
    'DEMO_MODE': lambda: 'true',
    'N8N_IMAGE': lambda: 'docker.n8n.io/n8nio/n8n:1.112.6',
    'POSTGRES_IMAGE': lambda: 'postgres:16-alpine',
    'POSTGRES_USER': lambda: 'zorgagent',
    'POSTGRES_PASSWORD': lambda: secrets.token_urlsafe(32),
    'POSTGRES_DB': lambda: 'zorgagent',
    'N8N_DB_NAME': lambda: 'n8n',
    'N8N_ENCRYPTION_KEY': lambda: secrets.token_urlsafe(32),
}
if p.exists():
    current = {}
    for line in p.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith('#') and '=' in line:
            key,value=line.split('=',1)
            current[key.strip()]=value
    missing = [key for key in defaults if not current.get(key)]
    if missing:
        with p.open('a', encoding='utf-8') as f:
            if p.read_text() and not p.read_text().endswith('\n'):
                f.write('\n')
            for key in missing:
                f.write(key+'='+defaults[key]()+'\n')
        print('.env bestond al; ontbrekende waarden aangevuld: '+', '.join(missing))
    else:
        print('.env bestaat al; niet overschreven.')
else:
    p.write_text(''.join(key+'='+factory()+'\n' for key,factory in defaults.items()))
    try: p.chmod(0o600)
    except OSError: pass
    print('.env aangemaakt. Lees REVIEWER_KEY lokaal uit dit bestand voor het reviewer-scherm.')
