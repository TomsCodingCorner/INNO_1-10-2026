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
├── tests/                 Backendtests (pytest); bewijzen niet dat n8n werkt
├── test-artifacts/        Opgeslagen testuitvoer als bewijs
└── docs/                  Alle deliverables en procesdocumentatie
```

Data en configuratie: de runtime draait op drie Docker-containers: `postgres`, `api` en `n8n`. PostgreSQL bewaart de applicatietabellen en de n8n-database. Lokale opslag staat onder `./data/postgres`, `./data/n8n` en `./data/app`; deze map staat niet in Git.

Keys, databasewachtwoord en n8n-encryptiesleutel staan alleen in de lokale `.env`.

## Hoe de onderdelen communiceren

```text
Browser (http://localhost:8000)
   │  POST /submit
   ▼
n8n-webhook /webhook/wmo-aanvraag
   │
   │  n8n orkestreert via HTTP naar http://api:8000
   │
   ├── 1. POST /prepare
   │      Validatie + toestemming + leeftijdsgroep + token + AI-input
   │
   ├── 2. GET /policy/...
   │      Fictieve beleidsregels
   │
   ├── 3. POST /ai/propose
   │      AI-stub: voorbereidend voorstel, geen besluit
   │
   ├── 4. POST /assess
   │      Risico + fairness + onderbouwingscontrole
   │
   ├── 5. POST /cases
   │      Dossier + audit-events opslaan
   │
   └── 6. IF prioriteit
          → vast burgerbericht

Ongeldige aanvraag / geen toestemming
   → POST /audit/events + HTTP 400

Technische fout
   → HTTP 503

Beoordelaar
   → UI + X-Reviewer-Key
   → /reviews, /cases, /audit
   → /reviews/{id}/decision

PostgreSQL
   → applicatietabellen in database `zorgagent`
   → n8n-tabellen in database `n8n`
```

Interne API-stappen zijn beveiligd met `X-Internal-Key`. n8n leest deze sleutel uit zijn containeromgeving.

## Deliverables

| #  | Deliverable                      | Bestand                                                                                 |
| -- | -------------------------------- | --------------------------------------------------------------------------------------- |
| 1  | BPMN-diagram                     | `docs/proces.bpmn`, `docs/proces.png`, `docs/proces.svg`                                |
| 2  | Architectuurdiagram              | `docs/architectuur.md`                                                                  |
| 3  | n8n-workflow (JSON-export)       | `n8n/workflow.json`                                                                     |
| 4  | Endpoints                        | Endpointtabel hieronder; live op `http://localhost:8000/docs`                           |
| 5  | Audit-database                   | `docs/audit-demo.sqlite`, `docs/audit-voorbeeld.json`                                   |
| 6  | Prompt Charter                   | `docs/prompt-charter.md`                                                                |
| 7  | README/installatie               | Dit bestand                                                                             |
| 8  | Bewijs Double Diamond            | `docs/double-diamond.md`                                                                |
| 9  | Bewijs feedback                  | `docs/feedback.md`                                                                      |
| 10 | AI-gebruikslog                   | `docs/ai-gebruikslog.md`                                                                |
| –  | Scrum, presentatie, eisen, tests | `docs/scrum.md`, `docs/presentatie.md`, `docs/eisenmatrix.md`, `docs/testresultaten.md` |

---

# Installatie voor nieuwe teamleden

Voor dit project zijn **Git, Python 3.11+ en Docker Desktop** nodig.

Docker Desktop draait de API, PostgreSQL en n8n in containers.

## 1. Benodigdheden installeren

| Benodigd       | Versie                         | Controle                 |
| -------------- | ------------------------------ | ------------------------ |
| Git            | Recente versie                 | `git --version`          |
| Python         | 3.11 of nieuwer                | `python --version`       |
| Docker Desktop | Recente versie                 | `docker --version`       |
| Docker Compose | Meegeleverd met Docker Desktop | `docker compose version` |

### Git

Installeer Git for Windows en gebruik tijdens de installatie de standaardinstellingen.

Controleer daarna:

```bash
git --version
```

### Python

Installeer Python **3.11 of nieuwer**.

Controleer daarna:

```bash
python --version
python -m pip --version
```

Je moet bijvoorbeeld `Python 3.11.x` of hoger zien.

### Docker Desktop

Installeer Docker Desktop en start het programma.

Op een normale Windows-laptop met een 64-bit Intel- of AMD-processor gebruik je de **Windows AMD64/x86_64-versie**.

Controleer daarna:

```bash
docker --version
docker compose version
```

Op Windows kan Docker Desktop vragen om **WSL 2** te installeren. Volg in dat geval de instructies van Docker en herstart de computer wanneer daarom wordt gevraagd.

## 2. Repository downloaden

Clone de repository:

```bash
git clone <REPOSITORY_URL>
```

Ga daarna naar de projectmap:

```bash
cd INNO_1-10-2026
```

Voer de commando's in deze README uit vanuit de **root van de repository**, dus de map waarin onder andere `README.md` en `docker-compose.yml` staan.

## 3. Lokale configuratie instellen

Maak de lokale configuratie aan:

```bash
python scripts/setup.py
```

Dit maakt of vult `.env` aan met lokale configuratie, zoals:

* interne API-key;
* reviewer-key;
* databasegegevens;
* n8n-encryptiesleutel.

Als je ziet:

```text
.env bestaat al; niet overschreven.
```

is dat normaal. De bestaande `.env` wordt dan behouden.

> **Let op:** `.env` bevat geheime lokale gegevens. Commit `.env` nooit naar GitHub en deel `REVIEWER_KEY`, `INTERNAL_KEY`, wachtwoorden of encryptiesleutels niet in screenshots, presentaties of de inlevering.

## 4. Docker starten

Start Docker Desktop en voer vanuit de projectroot uit:

```bash
docker compose up -d --build
```

Controleer daarna:

```bash
docker compose ps
```

De services `postgres`, `api` en `n8n` moeten actief zijn.

De API hoort uiteindelijk de status `healthy` te hebben.

## 5. n8n-workflow importeren

Importeer de meegeleverde workflow:

```bash
docker compose exec n8n n8n import:workflow --input=/workflows/workflow.json
```

Open daarna:

```text
http://localhost:5678
```

Maak bij het eerste bezoek eventueel een lokaal n8n-account aan.

Open de workflow:

```text
WMO — Zelfstandige Zorgagent (synthetische demo)
```

Controleer of de workflow actief/gepubliceerd is.

De productie-webhook is:

```text
http://localhost:5678/webhook/wmo-aanvraag
```

> Als de workflow na het importeren gedeactiveerd is, activeer hem handmatig in n8n.

## 6. Demo-interface controleren

Open:

```text
http://localhost:8000
```

Controleer ook:

```text
http://localhost:8000/health
```

en:

```text
http://localhost:8000/docs
```

Als deze pagina's openen, draait de backend correct.

## 7. Reviewer-key instellen

Voor:

* Aanvragenoverzicht;
* Menselijke beoordeling;
* Auditlog;

is de lokale `REVIEWER_KEY` nodig.

Deze staat in:

```text
.env
```

Gebruik de waarde uit je eigen lokale `.env`.

De key wordt gebruikt via de header:

```text
X-Reviewer-Key
```

> Deel deze sleutel niet en zet hem niet in frontendcode of screenshots.

## 8. De vier verplichte scenario's testen

Voer de vier synthetische scenario's uit via de demo-interface.

De fixtures staan in:

```text
fixtures/
```

| # | Scenario                      | Verwacht resultaat                         |
| - | ----------------------------- | ------------------------------------------ |
| 1 | Laag risico                   | Automatische voorbereiding + burgerbericht |
| 2 | Hoog risico / ernstig         | Doorsturen naar menselijke beoordeling     |
| 3 | Verboden term / fairness-flag | Flag + menselijke beoordeling              |
| 4 | `consent_ai=false`            | Geen AI-verwerking + audit-event           |

Na de installatie is de volledige testprocedure beschreven in [Testen](#testen).

---

# Belangrijke adressen

| Onderdeel             | Adres                                        |
| --------------------- | -------------------------------------------- |
| Demo-interface        | `http://localhost:8000`                      |
| API-documentatie      | `http://localhost:8000/docs`                 |
| Healthcheck           | `http://localhost:8000/health`               |
| n8n-editor            | `http://localhost:5678`                      |
| n8n productie-webhook | `http://localhost:5678/webhook/wmo-aanvraag` |
| PostgreSQL            | `127.0.0.1:5432`                             |

Binnen Docker gebruikt n8n voor de backend:

```text
http://api:8000
```

Gebruik vanuit een container dus niet `localhost:8000` om de API te bereiken.

---

# Interface en waar je bewijs vindt

De startpagina heeft vijf onderdelen:

| Onderdeel              | Doel                                                                                                     |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| Aanvraag indienen      | Vier synthetische scenario's via n8n versturen; toont dossiernummer, status en veilige burgertekst.      |
| Aanvragenoverzicht     | Alle opgeslagen dossiers, inclusief afgehandelde zaken, met zoeken/filteren en aantallen uit echte data. |
| Menselijke beoordeling | Alleen openstaande zaken; prioriteit, risico, flags en onderbouwing zichtbaar vóór beslissing.           |
| Auditlog               | Gebeurtenissen en mislukte pogingen met filters op dossier en eventtype.                                 |
| Demo en uitleg         | Spreekroute en onderscheid tussen overzicht, auditlog en n8n Executions.                                 |

Nieuwe aanvragen verversen het overzicht automatisch wanneer een reviewer-key is ingevuld.

Na een menselijke beslissing wordt de werkvoorraad bijgewerkt en blijft de zaak vindbaar in het volledige overzicht met status:

* `Toegekend door medewerker`
* `Afgewezen door medewerker`
* `Meer informatie nodig`

---

# Endpointtabel

| Endpoint                          | Toegang                   | Functie                                                                      |
| --------------------------------- | ------------------------- | ---------------------------------------------------------------------------- |
| `GET /`                           | Publiek lokaal            | Demo-interface.                                                              |
| `GET /health`                     | Publiek lokaal            | Healthcheck, demomodus en stubversie.                                        |
| `POST /submit`                    | Publiek lokaal            | Transportproxy naar de echte n8n-webhook; voert geen inhoudelijke keten uit. |
| `POST /prepare`                   | Intern `X-Internal-Key`   | Valideert, minimaliseert, maakt token en AI-input.                           |
| `GET /policy/household_support`   | Intern `X-Internal-Key`   | Fictieve beleidsregels.                                                      |
| `POST /ai/propose`                | Intern `X-Internal-Key`   | Deterministische AI-stub met strikt schema.                                  |
| `POST /assess`                    | Intern `X-Internal-Key`   | Risico-, fairness- en onderbouwingscontrole.                                 |
| `POST /cases`                     | Intern `X-Internal-Key`   | Transactioneel opslaan van dossier en audit-events.                          |
| `POST /audit/events`              | Intern `X-Internal-Key`   | Mislukte validatie of technische fout zonder ruwe payload loggen.            |
| `GET /cases`                      | Reviewer `X-Reviewer-Key` | Volledig aanvragenoverzicht met filters.                                     |
| `GET /cases/{caseId}`             | Reviewer `X-Reviewer-Key` | Details, exacte AI-input, tijdlijn, oordeel en audit-events.                 |
| `GET /reviews`                    | Reviewer `X-Reviewer-Key` | Openstaande werkvoorraad.                                                    |
| `POST /reviews/{caseId}/decision` | Reviewer `X-Reviewer-Key` | Menselijke beslissing met verplichte toelichting.                            |
| `GET /audit`                      | Reviewer `X-Reviewer-Key` | Auditlog met optionele filters `caseId` en `eventType`.                      |
| `GET /metrics`                    | Reviewer `X-Reviewer-Key` | AI-aanroepteller voor tests, onder meer toestemming=false.                   |

---

# Testen

## End-to-end test

Zorg dat Docker, de backend en n8n gestart zijn en dat de workflow gepubliceerd/geactiveerd is.

Voer daarna uit:

```bash
python scripts/test_e2e.py
```

Deze test controleert de vier verplichte scenario's:

1. laag risico;
2. hoog risico;
3. verboden AI-term/fairness-flag;
4. `consent_ai=false`.

Controleer daarnaast handmatig:

* n8n Executions;
* de demo-interface;
* de menselijke werkvoorraad;
* de Auditlog;
* het uiteindelijke burgerbericht.

> Een geslaagde backendtest bewijst niet automatisch dat de volledige n8n-workflow werkt. Controleer daarom ook de echte n8n-keten.

## Backendtests

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

Aanvullende tests controleren onder andere:

* dat persoonsgegevens niet worden geaccepteerd door het AI-schema;
* dat ongeldige beleidsreferenties tot menselijke beoordeling leiden;
* dat een menselijk oordeel een audit-event toevoegt.

## Persistentie controleren

Noteer tijdens een test een `caseId`.

Herstart daarna de containers:

```bash
docker compose restart
```

Zoek vervolgens dezelfde zaak opnieuw op via de interface en controleer of de audit-events nog aanwezig zijn.

---

# Stoppen en opnieuw starten

## Tijdelijk stoppen

```bash
docker compose stop
```

## Opnieuw starten

```bash
docker compose start
```

## Containers verwijderen

```bash
docker compose down
```

Dit verwijdert containers en het Docker-netwerk, maar laat de lokale data onder `./data/` staan.

## Opnieuw bouwen

```bash
docker compose up -d --build
```

> Verwijder de map `data/` alleen als je bewust opnieuw wilt beginnen met lege databases en een nieuwe lokale n8n-configuratie.

---

# Snelle controle vóór een demo

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

# Problemen oplossen

| Symptoom                   | Controle / oplossing                                                                                                           |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Webhook 404                | Controleer of de workflow gepubliceerd/geactiveerd is. Gebruik `/webhook/`, niet `/webhook-test/`.                             |
| Test-webhook reageert niet | Klik eerst op `Listen for Test Event`; testlisteners zijn tijdelijk.                                                           |
| n8n bereikt backend niet   | De node-URL moet `http://api:8000` zijn. `localhost` in een container verwijst naar die container zelf.                        |
| Poort bezet                | Pas de hostpoort in Compose aan en werk de browser-URL bij.                                                                    |
| Reviewer geeft 401/403     | Vul de key uit de actuele `.env` in. Herstart na een configuratiewijziging.                                                    |
| Backend niet bereikbaar    | Bekijk `docker compose ps` en `docker compose logs api`.                                                                       |
| PostgreSQL start niet      | Controleer of `POSTGRES_PASSWORD` in `.env` staat en of `./data/postgres` niet van een oude, conflicterende database-run komt. |
| Workflowimport lukt niet   | Gebruik eventueel de n8n-UI-import en controleer n8n-versie en nodeparameters.                                                 |
| Opslagfout                 | Controleer schrijfrechten, volumes en containerlogs.                                                                           |

Voor containerlogs:

```bash
docker compose logs api
docker compose logs n8n
docker compose logs postgres
```

---

# Privacy en grenzen

Alleen synthetische invoer wordt gebruikt.

De AI krijgt uitsluitend een allowlistobject met bijvoorbeeld:

* leeftijdsgroep;
* type voorziening;
* ernst;
* aantal problemen;
* beperkingen;
* bestaande ondersteuning.

De AI krijgt **geen**:

* naam;
* adres;
* geboortedatum;
* `citizenId`;
* intern token.

Pseudonimisering is **geen anonimisering**. Ook geminimaliseerde zorggegevens kunnen gevoelig blijven.

De koppelingen en auditgegevens zijn in deze demo logisch gescheiden op databaseniveau. Dit is geen productieklare beveiligingsarchitectuur.

De fairness-check gebruikt een woordenlijst en de onderbouwingscheck gebruikt een heuristiek. Deze controles vinden niet alle mogelijke problemen en kunnen ook onschuldige tekst markeren.

De gebruikte AI is een deterministische stub en geen echt LLM.

De reviewer-key, lokale PostgreSQL-inrichting en n8n-executie-instellingen vormen geen productiebeveiliging en zijn geen bewijs van AVG-compliance.

Gebruik geen echte inwonersdata en publiceer deze demo niet publiek.

---

# Inleveren en eigen acties

Maak het inleverpakket met:

```bash
python scripts/make_submission_zip.py
```

Het pakket bevat onder andere:

* broncode;
* Docker Compose;
* `n8n/workflow.json`;
* `postgres/initdb/`;
* fixtures;
* tests;
* `docs/`;
* `NOG-TE-DOEN.md`;
* het gegenereerde ZIP-bestand in `dist/`.

`dist/` staat bewust niet in Git. Genereer het pakket daarom opnieuw vlak voor het inleveren.

Het script sluit onder andere uit:

* `.env`;
* credentials;
* lokale `data/`;
* identity-databases;
* virtuele omgevingen;
* caches;
* `node_modules`;
* oude ZIP-bestanden;
* ruwe n8n-exportmetadata.

`docs/audit-demo.sqlite` is synthetisch testbewijs uit de eerdere auditdatabase en is niet de identity-mappingdatabase.

## Nog uit te voeren vóór inlevering

Controleer `NOG-TE-DOEN.md` en voer de resterende teamacties uit, waaronder:

* lokale start controleren;
* E2E-test uitvoeren;
* Docker-herstartcheck uitvoeren;
* rollen en namen invullen;
* twee niet-ICT-studenten laten testen;
* foto's met toestemming maken;
* feedback geven aan én ontvangen van een andere groep;
* echte wijzigingen vastleggen;
* presentatie oefenen.

De bijbehorende formats en documentatie staan in:

```text
docs/
```
