# De Zelfstandige Zorgagent

Lokaal hackathonprototype voor het voorbereiden van synthetische aanvragen voor huishoudelijke hulp. **Alle beleidsregels en risicoscores zijn fictief. AI bereidt voor; een mens beslist.** Een ontvangstbericht is nooit een toekenning.

Hackathon-opdracht: WMO-aanvragen automatisch en transparant voorbereiden met AI, zonder persoonsgegevens aan de AI te geven, en complexe of risicovolle aanvragen naar een menselijke beoordelaar sturen.

## Projectstructuur

```text
.
├── README.md              Dit bestand: wat, hoe starten, waar staat wat
├── NOG-TE-DOEN.md         Resterende teamacties vóór inlevering
├── docker-compose.yml     Start de drie services: postgres, api (FastAPI) en n8n
├── .env.example           Sjabloon voor lokale keys; echte .env maakt scripts/setup.py (nooit committen)
├── backend/               FastAPI-service (Docker-image "api")
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/main.py        Validatie, minimalisatie, pseudonimisering, beleid, AI-stub, fairness/risico, audit, review-API
│   └── static/index.html  Demo-interface voor burger en beoordelaar
├── n8n/workflow.json      De n8n-workflow (orkestratie); read-only gemount in de n8n-container op /workflows
├── postgres/initdb/       Eenmalige database-initialisatie voor de n8n-database
├── fixtures/              De vier verplichte testaanvragen (synthetisch)
├── scripts/               setup.py, start.py, test_e2e.py, build_workflow.py, make_submission_zip.py
├── tests/                 Backendtests (pytest); bewijzen níet dat n8n werkt
├── test-artifacts/        Opgeslagen testuitvoer als bewijs
└── docs/                  Alle deliverables en procesdocumentatie (zie tabel hieronder)
```

Data en configuratie: de runtime draait op drie Docker-containers: `postgres`, `api` en `n8n`. PostgreSQL bewaart de applicatietabellen en de n8n-database. Lokale opslag staat onder `./data/postgres`, `./data/n8n` en `./data/app`; deze map staat niet in Git. Keys, databasewachtwoord en n8n-encryptiesleutel staan alleen in de lokale `.env`.

## Hoe de onderdelen communiceren

```text
Browser (http://localhost:8000)
   │  POST /submit  (alleen doorgeefproxy)
   ▼
n8n-webhook /webhook/wmo-aanvraag ──► n8n-workflow orkestreert elke stap via HTTP naar http://api:8000:
   1. POST /prepare          validatie + toestemming, leeftijdsgroep, token, AI-input (allowlist)
   2. GET  /policy/...       fictieve beleidsregels
   3. POST /ai/propose       AI-stub: voorbereidend voorstel (geen besluit)
   4. POST /assess           risico, fairness en onderbouwingscontrole
   5. POST /cases            dossier + audit-events opslaan
   6. IF prioriteit          → vast burgerbericht (standaard of extra beoordeling)
   ✗  ongeldig / geen toestemming → POST /audit/events + HTTP 400; technische fout → HTTP 503
Beoordelaar (UI + X-Reviewer-Key) ──► GET /reviews, /cases, /audit · POST /reviews/{id}/decision
PostgreSQL ──► applicatietabellen in database `zorgagent`; n8n-tabellen in database `n8n`
```

Interne stappen zijn beveiligd met `X-Internal-Key`; n8n leest die uit zijn containeromgeving.

## Deliverables

| # | Deliverable | Bestand |
|---|---|---|
| 1 | BPMN-diagram | `docs/proces.bpmn`, `docs/proces.png`, `docs/proces.svg` |
| 2 | Architectuurdiagram | `docs/architectuur.md` |
| 3 | n8n-workflow (JSON-export) | `n8n/workflow.json` |
| 4 | Endpoints | [Endpointtabel](#endpointtabel) hieronder; live op http://localhost:8000/docs |
| 5 | Audit-database | `docs/audit-demo.sqlite`, `docs/audit-voorbeeld.json` |
| 6 | Prompt Charter | `docs/prompt-charter.md` |
| 7 | README/installatie | Dit bestand |
| 8 | Bewijs Double Diamond | `docs/double-diamond.md` |
| 9 | Bewijs feedback | `docs/feedback.md` |
| 10 | AI-gebruikslog | `docs/ai-gebruikslog.md` |
| – | Scrum, presentatie, eisen, tests | `docs/scrum.md`, `docs/presentatie.md`, `docs/eisenmatrix.md`, `docs/testresultaten.md` |

## Installatie voor nieuwe teamleden

Voor dit project zijn **Git, Python 3.11+ en Docker Desktop** nodig. Docker Desktop draait de API, PostgreSQL en n8n in containers.

### 1. Benodigdheden installeren

| Benodigd       | Versie                         | Controle                 |
| -------------- | ------------------------------ | ------------------------ |
| Git            | Recente versie                 | `git --version`          |
| Python         | 3.11 of nieuwer                | `python --version`       |
| Docker Desktop | Recente versie                 | `docker --version`       |
| Docker Compose | Meegeleverd met Docker Desktop | `docker compose version` |

#### Git

Installeer Git for Windows en gebruik tijdens de installatie de standaardinstellingen.

Controleer daarna:

```bash
git --version
```

#### Python

Installeer Python **3.11 of nieuwer**.

Controleer daarna:

```bash
python --version
```

Je moet bijvoorbeeld `Python 3.11.x` of hoger zien.

Controleer ook:

```bash
python -m pip --version
```

#### Docker Desktop

Installeer Docker Desktop.

Op een normale Windows-laptop met een 64-bit Intel- of AMD-processor gebruik je de **Windows AMD64/x86_64-versie**.

Start daarna Docker Desktop en wacht totdat Docker volledig is gestart.

Controleer in een nieuwe terminal:

```bash
docker --version
docker compose version
```

Op Windows kan Docker Desktop vragen om **WSL 2** te installeren. Volg in dat geval de instructies van Docker en herstart de computer wanneer daarom wordt gevraagd.

> Docker Desktop is een aparte applicatie. Het hoeft niet in Python of Conda geïnstalleerd te worden.

---

### 2. Repository downloaden

Clone de repository:

```bash
git clone <REPOSITORY_URL>
```

Ga daarna naar de projectmap:

```bash
cd INNO_1-10-2026
```

Voer de volgende commando's uit vanuit de **root van de repository**, dus de map waarin onder andere `README.md` en `docker-compose.yml` staan.

---

### 3. Lokale configuratie instellen

Maak de lokale configuratie aan:

```bash
python scripts/setup.py
```

Dit maakt of vult `.env` aan met lokale configuratie, zoals sleutels, databasegegevens en de n8n-encryptiesleutel.

Als je ziet:

```text
.env bestaat al; niet overschreven.
```

is dat normaal. De bestaande `.env` wordt dan behouden.

> **Let op:** `.env` bevat geheime lokale gegevens. Commit `.env` nooit naar GitHub en deel `REVIEWER_KEY`, `INTERNAL_KEY`, wachtwoorden of encryptiesleutels niet in screenshots, presentaties of de inlevering.

---

## Snelste start

Start **Docker Desktop**, open een terminal in de root van de repository en voer uit:

```bash
python scripts/setup.py
docker compose up -d --build
```

Controleer daarna:

```bash
docker compose ps
```

De services `postgres`, `api` en `n8n` moeten actief zijn. De API hoort uiteindelijk de status `healthy` te hebben.

---

### 4. n8n-workflow importeren

Importeer de meegeleverde workflow:

```bash
docker compose exec n8n n8n import:workflow --input=/workflows/workflow.json
```

Open daarna:

**http://localhost:5678**

Maak bij het eerste bezoek eventueel een lokaal n8n-account aan.

Open de workflow **WMO — Zelfstandige Zorgagent (synthetische demo)** en controleer of deze actief/gepubliceerd is.

De productie-webhook is:

```text
http://localhost:5678/webhook/wmo-aanvraag
```

> Als de workflow na het importeren gedeactiveerd is, activeer hem handmatig in n8n.

---

### 5. Demo-interface controleren

Open:

**http://localhost:8000**

Controleer ook:

**http://localhost:8000/health**

en:

**http://localhost:8000/docs**

Als deze pagina's openen, draait de backend correct.

---

### 6. Reviewer-key instellen

Voor **Aanvragenoverzicht**, **Menselijke beoordeling** en **Auditlog** is de lokale `REVIEWER_KEY` nodig.

Deze staat in:

```text
.env
```

Gebruik de waarde uit je eigen lokale `.env`.

De key wordt gebruikt via de header:

```text
X-Reviewer-Key
```

> Deel deze sleutel niet en zet hem niet in frontendcode, screenshots, GitHub of het inleverpakket.

---

### 7. De vier verplichte scenario's testen

Voer de vier synthetische scenario's uit via de demo-interface.

| # | Scenario                      | Verwacht resultaat                         |
| - | ----------------------------- | ------------------------------------------ |
| 1 | Laag risico                   | Automatische voorbereiding + burgerbericht |
| 2 | Hoog risico / ernstig         | Doorsturen naar menselijke beoordeling     |
| 3 | Verboden term / fairness-flag | Flag + menselijke beoordeling              |
| 4 | `consent_ai=false`            | Geen AI-verwerking + audit-event           |

De synthetische fixtures staan in:

```text
fixtures/
```

Automatische E2E-test:

```bash
python scripts/test_e2e.py
```

Controleer daarna ook de **n8n Executions**, de demo-interface en de **Auditlog**.

> Een geslaagde backendtest bewijst niet automatisch dat de volledige n8n-workflow werkt. Controleer daarom altijd ook de echte n8n-keten.

---

### 8. Backendtests uitvoeren

Voor lokale backendtests:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install pytest
python -m pytest tests -q
```

De testresultaten en het beschikbare bewijs staan in:

```text
docs/testresultaten.md
```

---

## Belangrijke adressen

| Onderdeel             | Adres                                      |
| --------------------- | ------------------------------------------ |
| Demo-interface        | http://localhost:8000                      |
| API-documentatie      | http://localhost:8000/docs                 |
| Healthcheck           | http://localhost:8000/health               |
| n8n-editor            | http://localhost:5678                      |
| n8n productie-webhook | http://localhost:5678/webhook/wmo-aanvraag |
| PostgreSQL            | `127.0.0.1:5432`                           |

---

## Stoppen en opnieuw starten

Tijdelijk stoppen:

```bash
docker compose stop
```

Opnieuw starten:

```bash
docker compose start
```

Containers verwijderen zonder lokale data te verwijderen:

```bash
docker compose down
```

Opnieuw bouwen:

```bash
docker compose up -d --build
```

> Verwijder de map `data/` alleen als je bewust opnieuw wilt beginnen met lege databases en een nieuwe lokale n8n-configuratie.

---

## Snelle controle vóór een demo

Voer vanuit de projectroot uit:

```bash
python --version
docker --version
docker compose version
docker compose ps
```

Controleer vervolgens:

* [ ] Docker Desktop draait.
* [ ] `postgres` draait.
* [ ] `api` draait en is `healthy`.
* [ ] `n8n` draait.
* [ ] De n8n-workflow is geïmporteerd.
* [ ] De n8n-workflow is actief/gepubliceerd.
* [ ] `http://localhost:8000` opent.
* [ ] `http://localhost:8000/health` werkt.
* [ ] De reviewer-key werkt.
* [ ] De vier scenario's zijn getest.
* [ ] n8n Executions zijn gecontroleerd.
* [ ] Auditlog bevat de verwachte gebeurtenissen.
* [ ] Alleen synthetische data is gebruikt.

---

## Problemen oplossen

### Docker werkt niet

Controleer:

```bash
docker --version
docker compose version
```

Controleer daarna of Docker Desktop actief is.

### Backend werkt niet

```bash
docker compose ps
docker compose logs api
```

### n8n werkt niet

```bash
docker compose logs n8n
```

Controleer ook of de workflow actief/gepubliceerd is.

### n8n kan de backend niet bereiken

Gebruik binnen de n8n-workflow:

```text
http://api:8000
```

Gebruik **niet** `http://localhost:8000` vanuit de n8n-container. Binnen Docker verwijst `localhost` namelijk naar de n8n-container zelf.

### Webhook geeft 404

Controleer of de workflow actief/gepubliceerd is en gebruik:

```text
/webhook/wmo-aanvraag
```

niet:

```text
/webhook-test/wmo-aanvraag
```

### Reviewer geeft 401/403

Controleer of je de actuele `REVIEWER_KEY` uit je lokale `.env` gebruikt.

### Poort 8000 of 5678 is al bezet

Controleer welke applicatie de poort gebruikt of pas de hostpoort aan in `docker-compose.yml`.

## Snelste start (eenmalig)

Start Docker Desktop, clone de repository en open een terminal in de root van de repository:

```bash
python scripts/start.py
```

Dit genereert lokale sleutels, het PostgreSQL-wachtwoord en de n8n-encryptiesleutel, bouwt de API, start PostgreSQL, importeert de geleverde workflow via de officiële n8n-CLI en activeert deze vóór n8n start. Open daarna **http://localhost:8000**. De eerste download/build kan enkele minuten duren. Open **http://localhost:5678** om de workflow te bekijken; maak daar bij eerste bezoek een lokaal beheerdersaccount.

`start.py` importeert de meegeleverde demo opnieuw. Gebruik voor latere herstarts `docker compose start`, zodat eigen workflowwijzigingen behouden blijven. `start.py` zelf is nog niet aantoonbaar op een schone machine getest; de Docker Compose-omgeving wel (zie `docs/testresultaten.md`). Handmatige stappen volgen hieronder.

## Snel starten

Benodigd: Docker Desktop met Compose, Python 3.11 of nieuwer, internet voor de eerste image-build. Start vanuit de root van de repository.

```bash
python scripts/setup.py
docker compose up -d --build postgres api
docker compose run --rm --no-deps n8n import:workflow --input=/workflows/workflow.json
docker compose run --rm --no-deps n8n update:workflow --id=zorgagentDemo01 --active=true
docker compose up -d n8n
```

1. Open http://localhost:5678 en voltooi de lokale n8n-accountconfiguratie indien nodig.
2. Open de geïmporteerde workflow. Verschijnt die nog niet, vernieuw de pagina. Als CLI-import niet beschikbaar is, kies in de editor **Import from File** en selecteer `n8n/workflow.json`.
3. Publiceer/activeer de workflow met de knop die jouw n8n-versie toont. Gebruik de productie-webhook `/webhook/wmo-aanvraag`.
4. Open http://localhost:8000 voor de demo-interface.
5. Lees de lokaal gegenereerde `REVIEWER_KEY` in `.env` en vul deze in het reviewergedeelte in. Deel deze niet mee in het inleverpakket. De key wordt via `X-Reviewer-Key` verzonden.
6. Voer de vier scenario's uit en controleer daarna **Aanvragenoverzicht**, **Aanvraagdetails**, **Menselijke beoordeling** en **Auditlog**. Afgehandelde zaken verdwijnen uit de werkvoorraad maar blijven in het volledige overzicht staan.

De eerste build kan langer duren dan het programmeren. **De uitvoerstatus van echte tests staat in `docs/testresultaten.md`.** Een geslaagde backendtest bewijst niet dat de n8n-workflow werkt. De bootstrap activeert de workflow; voer de webhooktest ook op jouw eigen Docker-installatie uit.

## Configuratie en adressen

`setup.py` maakt of vult de lokale configuratie aan; `.env.example` beschrijft de variabelen. De Compose-configuratie gebruikt n8n 1.112.6, PostgreSQL 16 en bindt poorten alleen aan localhost. `INTERNAL_KEY` beschermt interne backendstappen; n8n leest deze uit de containeromgeving. `REVIEWER_KEY` beschermt review, audit en metrics. `POSTGRES_PASSWORD` en `N8N_ENCRYPTION_KEY` worden lokaal gegenereerd. Gebruik de ingestelde demomodus alleen voor synthetische tests. Een verboden-termfixture is testgedrag, geen productiefunctionaliteit.

| Doel | Adres |
|---|---|
| Burger- en reviewinterface | http://localhost:8000 |
| Backend API-specificatie | http://localhost:8000/docs |
| Healthcheck | http://localhost:8000/health |
| n8n-editor | http://localhost:5678 |
| Productie-webhook op host | http://localhost:5678/webhook/wmo-aanvraag |
| Backend vanuit n8n-container | http://api:8000 |
| PostgreSQL op host | 127.0.0.1:5432 |

De UI geeft aanvragen via een proxy door aan n8n. De proxy voert geen inhoudelijke workflow uit. Elke validatie-, AI-, controle- en opslagstap wordt vanuit n8n aangeroepen. Menselijke review gebeurt later via aparte reviewer-endpoints. De interne overzichten zijn beveiligd met `X-Reviewer-Key`; zet deze sleutel niet in frontendcode, screenshots of het inleverpakket.

## Interface en waar je bewijs vindt

De startpagina heeft vijf onderdelen:

| Onderdeel | Doel |
|---|---|
| Aanvraag indienen | Vier synthetische scenario's via n8n versturen; toont dossiernummer, status en veilige burgertekst. |
| Aanvragenoverzicht | Alle opgeslagen dossiers, inclusief afgehandelde zaken, met zoeken/filteren en aantallen uit echte data. |
| Menselijke beoordeling | Alleen openstaande zaken; prioriteit, risico, flags en onderbouwing zichtbaar vóór beslissing. |
| Auditlog | Gebeurtenissen en mislukte pogingen met filters op dossier en eventtype. |
| Demo en uitleg | Spreekroute en onderscheid tussen overzicht, auditlog en n8n Executions. |

Nieuwe aanvragen verversen het overzicht automatisch wanneer een reviewer-key is ingevuld. Na een menselijke beslissing wordt de werkvoorraad bijgewerkt en blijft de zaak vindbaar in het volledige overzicht met status `Toegekend door medewerker`, `Afgewezen door medewerker` of `Meer informatie nodig`.

## Endpointtabel

| Endpoint | Toegang | Functie |
|---|---|---|
| `GET /` | Publiek lokaal | Demo-interface. |
| `GET /health` | Publiek lokaal | Healthcheck, demomodus en stubversie. |
| `POST /submit` | Publiek lokaal | Transportproxy naar de echte n8n-webhook; voert geen inhoudelijke keten uit. |
| `POST /prepare` | Intern `X-Internal-Key` | Valideert, minimaliseert, maakt token en AI-input. |
| `GET /policy/household_support` | Intern `X-Internal-Key` | Fictieve beleidsregels. |
| `POST /ai/propose` | Intern `X-Internal-Key` | Deterministische AI-stub met strikt schema. |
| `POST /assess` | Intern `X-Internal-Key` | Risico-, fairness- en onderbouwingscontrole. |
| `POST /cases` | Intern `X-Internal-Key` | Transactioneel opslaan van dossier en audit-events. |
| `POST /audit/events` | Intern `X-Internal-Key` | Mislukte validatie of technische fout zonder ruwe payload loggen. |
| `GET /cases` | Reviewer `X-Reviewer-Key` | Volledig aanvragenoverzicht met filters. |
| `GET /cases/{caseId}` | Reviewer `X-Reviewer-Key` | Details, exacte AI-input, tijdlijn, oordeel en audit-events. |
| `GET /reviews` | Reviewer `X-Reviewer-Key` | Openstaande werkvoorraad. |
| `POST /reviews/{caseId}/decision` | Reviewer `X-Reviewer-Key` | Menselijke beslissing met verplichte toelichting. |
| `GET /audit` | Reviewer `X-Reviewer-Key` | Auditlog met optionele filters `caseId` en `eventType`. |
| `GET /metrics` | Reviewer `X-Reviewer-Key` | AI-aanroepteller voor tests, onder meer toestemming=false. |

## Testen

Na workflowpublicatie, met de backend en n8n gestart:

```bash
python scripts/test_e2e.py
```

Backendtests, na installatie van de backendrequirements en pytest in een eigen Python-omgeving:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install pytest
python -m pytest tests -q
```

Lees de scriptuitvoer; sla actuele resultaten op voor de presentatie. De vier verplichte tests zijn laag risico, hoog risico, verboden AI-term en toestemming=false. Aanvullende tests controleren dat persoonsgegevens niet worden geaccepteerd door het AI-schema, ongeldige beleidsreferenties review opleveren en een menselijk oordeel een audit-event toevoegt.

Controleer persistentie: noteer een caseId, voer `docker compose restart` uit en zoek die zaak en audit-events opnieuw op. In de actuele run is de echte n8n-keten getest; een volledige handmatige browserklikflow moet het team nog op de presentatielaptop doorlopen.

## Stoppen en herstarten

```bash
docker compose stop
docker compose start
```

`docker compose down` verwijdert containers/netwerk maar behoudt de lokale data in `./data`. Verwijder `./data` alleen als je bewust opnieuw wilt beginnen met lege databases en een lege n8n-configuratie.

## Problemen oplossen

| Symptoom | Controle / oplossing |
|---|---|
| Webhook 404 | Workflow gepubliceerd/geactiveerd? Gebruik `/webhook/`, niet `/webhook-test/`. |
| Test-webhook reageert niet | Klik eerst “Listen for Test Event”; testlisteners zijn tijdelijk. |
| n8n bereikt backend niet | Node-URL moet `http://api:8000` zijn. `localhost` in een container verwijst naar die container. |
| Poort bezet | Pas de hostpoort in Compose aan en werk de browser-URL bij. |
| Reviewer geeft 401/403 | Vul de key uit de actuele `.env` in; herstart na configuratiewijziging. |
| Backend niet bereikbaar | Bekijk `docker compose ps` en `docker compose logs api`. |
| PostgreSQL start niet | Controleer of `POSTGRES_PASSWORD` in `.env` staat en of `./data/postgres` niet van een oude, conflicterende database-run komt. |
| Workflowimport lukt niet | Gebruik de UI-import en controleer n8n-versie/nodeparameters. |
| Opslagfout | Geen succesbericht verwachten; controleer schrijfrechten, volume en containerlogs. |

## Privacy en grenzen

Alleen synthetische invoer. AI krijgt een allowlistobject met leeftijdsgroep, type voorziening, ernst, aantal problemen, beperkingen en bestaande ondersteuning. Geen naam, adres, geboortedatum, citizenId of intern token. Pseudonimisering is **geen anonimisering**; ook geminimaliseerde zorggegevens blijven gevoelig. Koppelingen en audit staan gescheiden op logisch tabelniveau, niet in een productieklare beveiligingsarchitectuur.

De fairness-check is een woordenlijst en de onderbouwingscheck een heuristiek. Deze vinden niet alle problemen en kunnen onschuldige tekst markeren. De stub is geen echt LLM. Reviewer-key, lokale PostgreSQL-inrichting en n8n-executie-instellingen vormen geen productiebeveiliging of bewijs van AVG-compliance. Geen echte inwonersdata en geen publieke deployment.

## Inleveren en eigen acties

Maak het pakket met:

```bash
python scripts/make_submission_zip.py
```

Lever code, Compose, `n8n/workflow.json`, `postgres/initdb/`, fixtures, tests, `docs/`, `NOG-TE-DOEN.md` en het ZIP-bestand uit `dist/` in. `dist/` staat bewust niet in Git: genereer het pakket opnieuw vlak voor het inleveren. Het script sluit `.env`, credentials, lokale `data/`, identity-databases, virtuele omgevingen, caches, node_modules, oude ZIP-bestanden en ruwe n8n-exportmetadata uit. `docs/audit-demo.sqlite` is synthetisch testbewijs uit de eerdere auditdatabase, niet de identity-mappingdatabase.

Nog zelf uitvoeren: lokale start en E2E-/Docker-herstartcheck, rollen/namen invullen, twee niet-ICT-studenten laten testen, foto's met toestemming maken, feedback geven aan én ontvangen van een andere groep, echte wijzigingen vastleggen en presentatie oefenen. Formats staan in `docs/`.
