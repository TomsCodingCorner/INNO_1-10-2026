# Eisenmatrix — De Zelfstandige Zorgagent

Statusdatum: 1 oktober 2026. Gebruik deze matrix als beoordelingschecklist. Statussen claimen alleen wat in deze workspace of in de actuele testuitvoer is aangetoond.

| Eis / deliverable | Implementatie of bestand | Concrete verificatie | Status | Resterende menselijke actie |
|---|---|---|---|---|
| Aanvragen indienen via echte n8n-webhook | `n8n/workflow.json`, `backend/app/main.py`, UI | `python scripts/test_e2e.py`: vier scenario's via `http://localhost:5678/webhook/wmo-aanvraag` | Geïmplementeerd en getest | Demo live herhalen op presentatielaptop |
| Gegevens en AI-toestemming valideren | `/prepare`, fixtures | Geen-toestemming geeft HTTP 400, AI-teller blijft gelijk | Geïmplementeerd en getest | Geen |
| citizenId vervangen door token | `/prepare`, `IDENTITY_PATH` buiten pakket | Audit bevat token/caseId, geen citizenId | Geïmplementeerd en getest | Geen echte data invoeren |
| AI-input via allowlist minimaliseren | `AIInput` schema | Backendtest weigert extra velden; E2E controleert exacte keys | Geïmplementeerd en getest | Geen |
| Fictieve beleidsregels ophalen | `/policy/household_support` | n8n roept policy-node aan; detailpagina toont beleid | Geïmplementeerd en getest | Uitleggen dat beleid fictief is |
| AI-stub aanroepen | `/ai/propose` | E2E laag/hoog/fairness verhoogt teller behalve bij geen toestemming | Geïmplementeerd en getest | Geen |
| Fairness en onderbouwing controleren | `/assess`, woordenlijst, beleidsreferentiecheck | Fairness-fixture veroorzaakt `fairness:geslacht`; ongeldige referentie backendtest | Geïmplementeerd en getest | Beperkingen als heuristiek toelichten |
| Menselijke review klaarzetten | `/cases`, `/reviews` | Hoog risico en fairness staan in review; prioriteit zichtbaar | Geïmplementeerd en getest | Geen |
| Transparant burgerbericht | n8n Respond nodes, UI | E2E controleert bericht en dat fairness-term niet lekt | Geïmplementeerd en getest | In gebruikerstest begrijpelijkheid toetsen |
| Persistent token, risico, flags, voorstel en beslissingen loggen | SQLite `cases`, `audit_events` | `docs/audit-demo.sqlite`, `docs/audit-voorbeeld.json`, beslissing in E2E | Geïmplementeerd en getest | Geen echte persoonsgegevens bewaren |
| Volledig aanvragenoverzicht | Beveiligde `GET /cases` en UI-tab | E2E zoekt dossier, filters status `needs_information`, afgehandelde zaak blijft vindbaar | Geïmplementeerd en getest | Geen |
| Aanvraagdetails met AI-input, voorstel, oordeel en audit | Beveiligde `GET /cases/{caseId}` en UI-detail | E2E controleert detail en tijdlijn | Geïmplementeerd en getest | Geen |
| Auditlog met filters en mislukte pogingen | `GET /audit`, `POST /audit/events`, UI-tab | Geen-toestemming schrijft `validation_failed` met correlatie-ID | Geïmplementeerd en getest | Geen |
| Reviewer-authenticatie zonder key in frontendcode | `X-Reviewer-Key`, invoerveld zonder opslag | Backendtests weigeren geen/verkeerde key | Geïmplementeerd en getest | Key niet projecteren of inleveren |
| Onbevoegde toegang weigeren | `/reviews`, `/audit`, `/metrics`, `/cases` | Backendtests en E2E access-controls | Geïmplementeerd en getest | Geen |
| Servicefout geeft geen vals succes | `/submit` en n8n foutpad | Bestaand testdocument beschrijft eerdere check; na UI-wijziging niet opnieuw geforceerd | Aanwezig, nog te verifiëren | Tijdens demo alleen claimen als opnieuw getest |
| Browserinterface render/syntax | `backend/static/index.html` | Node VM syntaxcheck, in-app browser startpagina screenshot `test-artifacts/ui-home.png` | Aanwezig, nog te verifiëren | Klikflow handmatig doorlopen; browserautomatisering wisselde tabs niet |
| BPMN-diagram | `docs/proces.bpmn`, `docs/proces.png`, `docs/proces.svg` | Bestanden aanwezig; eerdere XML/visuele controle | Aanwezig, nog te verifiëren | Controleren tegen nieuwe UI-termen |
| Architectuurdiagram | `docs/architectuur.md` | Toont interface, n8n, FastAPI, AI-stub, SQLite, reviewer en minimalisatie | Geïmplementeerd en getest | Eventueel als afbeelding exporteren voor slides |
| n8n-workflowexport | `n8n/workflow.json` | Live-export vergeleken: 14 nodes; gesaneerde actuele export zonder eigenaarmetadata | Geïmplementeerd en getest | Niet blind overschrijven met oude export |
| Endpointtabel | README | Publieke, interne en reviewer-endpoints opgenomen | Geïmplementeerd en getest | Geen |
| Audit-database | `docs/audit-demo.sqlite`, `docs/audit-voorbeeld.json` | Gekopieerd uit actieve synthetische runtime; identity-db niet meegeleverd | Geïmplementeerd en getest | Geen |
| Prompt Charter | `docs/prompt-charter.md` | Bevat rol, privacy, toon, outputschema, toolverbod, stubbetekenis | Geïmplementeerd en getest | Team moet kunnen toelichten |
| README | `README.md` | Start, URL's, reviewer-key, tests, troubleshooting en beperkingen | Geïmplementeerd en getest | Presentatielaptop volgen |
| Double Diamond-bewijs | `docs/double-diamond.md` | Werkblad markeert aannames en ontbrekende foto's/interviews | Format aanwezig, bewijs ontbreekt | Echte sessies/foto's toevoegen |
| Feedbackbewijs | `docs/feedback.md` | Invulformats en tabel feedback → besluit → aanpassing | Format aanwezig, bewijs ontbreekt | Twee niet-ICT-studenten + groepsfeedback verzamelen |
| AI-gebruikslog | `docs/ai-gebruikslog.md` | Onderscheid ontwikkel-AI en productstub | Geïmplementeerd en getest | Team vult eigen handmatige controles aan |
| Scrumdocumentatie | `docs/scrum.md` | Goal, sprint goal, backlog, DoD, review/retro formats | Aanwezig, nog te verifiëren | Rollen/namen en echte review/retro invullen |
| Presentatie/draaiboek | `docs/presentatie.md` | 20-minutenindeling en demostappen | Aanwezig, nog te verifiëren | Sprekersnamen invullen en oefenen |
| Inleverpakket | `scripts/make_submission_zip.py`, `dist/zelfstandige-zorgagent-inleverpakket.zip` | Script sluit secrets/caches/oude zips uit | Geïmplementeerd en getest | ZIP openen en uploaden volgens schoolinstructie |
| `NOG-TE-DOEN.md` | Rootbestand | Alleen resterende teamacties | Geïmplementeerd en getest | Uitvoeren voor beoordeling |
