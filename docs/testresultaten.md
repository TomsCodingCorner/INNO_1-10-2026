# Werkelijk uitgevoerde tests — 1 oktober 2026

## Samenvatting

| Controle | Status | Bewijs / grens |
|---|---|---|
| Backend regressietests | 21 geslaagd | `docker compose run --rm --no-deps -v "${PWD}:/workspace" -w /workspace api python -m pytest tests -q` |
| Laag risico via echte n8n-webhook | Geslaagd | HTTP 200, opgeslagen dossier, detailpagina-data, audit en menselijke demo-beslissing `needs_information`. |
| Hoog risico via echte n8n-webhook | Geslaagd | HTTP 200, prioriteitsreview, risicoscore 100 en begrijpelijke reden. |
| Fairness via echte n8n-webhook | Geslaagd | Stub produceert verboden term; fairness-check detecteert `fairness:geslacht`; burgerbericht lekt term niet. |
| Geen toestemming via echte n8n-webhook | Geslaagd | HTTP 400, AI-aanroepteller blijft gelijk, audit-event `validation_failed`. |
| Volledig aanvragenoverzicht | Geslaagd | E2E zoekt op dossiernummer, filtert status `needs_information` en vindt afgehandelde zaak. |
| Aanvraagdetails | Geslaagd | E2E controleert exacte AI-input, voorstel en tijdlijn met `ai_preparation`. |
| Menselijke beslissing | Geslaagd | E2E slaat `needs_information` op en controleert detail plus werkvoorraad. |
| Onbevoegde reviewerdata | Geslaagd | E2E en backendtests weigeren ontbrekende/verkeerde reviewer-key. |
| JavaScript syntax | Geslaagd | Script uit `backend/static/index.html` geparseerd met Node `vm.Script`. |
| Browser render | Beperkt geslaagd | In-app browser opent startpagina; screenshot `test-artifacts/ui-home.png`. Tabwissel via browserautomatisering werkte niet betrouwbaar. |
| Actuele n8n-export | Geslaagd | Live-export uit container vergeleken: 14 nodes; gesaneerd opgeslagen in `n8n/workflow.json`. |
| Auditdatabase bewijs | Geslaagd | `docs/audit-demo.sqlite` gekopieerd uit actieve synthetische auditdatabase; identity-database niet meegeleverd. |
| Servicefout geen vals succes | Aanwezig, nog te verifiëren | Foutpad bestaat in workflow en `/submit`; in deze ronde niet opnieuw geforceerd door n8n/API uit te schakelen. |
| Docker-herstart persistentie | Geslaagd | `docker compose restart postgres api n8n`; daarna `/health` = `ok`, database = `postgres`, eerder dossier teruggevonden. |
| Echte gebruikers-/presentatiefeedback | Niet uitgevoerd | Teamtaak, zie `docs/feedback.md` en `NOG-TE-DOEN.md`. |

## Uitvoerbestanden

- `test-artifacts/backend-results.xml`
- `test-artifacts/e2e-results.json`
- `test-artifacts/ui-home.png`
- `docs/audit-voorbeeld.json`
- `docs/audit-demo.sqlite`

## Testomgeving

Docker Compose draaide lokaal met drie containers: `inno_1-10-2026-postgres-1`, `inno_1-10-2026-api-1` en `inno_1-10-2026-n8n-1`. De API-healthcheck rapporteerde `database: postgres`. De aanvragen in `scripts/test_e2e.py` zijn naar de echte n8n-productiewebhook gestuurd; het script heeft geen fallback naar losse backendfuncties voor het indienen van aanvragen.

De browsercheck is eerlijk beperkt: de pagina renderde zichtbaar, maar de gebruikte in-app browserautomatisering kon tabwissels niet betrouwbaar activeren. De functionele gebruikersflow is daarom via echte HTTP/n8n/API-controles getest en moet handmatig in de browser worden nagespeeld voor de presentatie.

## Auditbewijs

`docs/audit-voorbeeld.json` bevat 22 events uit de synthetische runtime. `docs/audit-demo.sqlite` bevat de actieve auditdatabase met zaken, events en AI-teller. Deze database bevat geen identity-mappingdatabase en geen reviewer/internal keys. Gebruik deze kopie als testbewijs, niet als productie- of persoonsgegevensdatabase.
