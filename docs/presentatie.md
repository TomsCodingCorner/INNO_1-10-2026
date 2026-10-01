# Presentatiedraaiboek — 20 minuten inclusief vragen

Vul namen en echte bewijsresultaten in. De teksten hieronder beschrijven de bedoelde demo, niet dat de uitvoering al geslaagd is.

| Tijd | Spreker | Inhoud / scherm |
|---|---|---|
| 0:00–2:00 | Teamlid 1 [naam] | Probleem, Project Goal, Sprint Goal, Scrum-rollen en scope. |
| 2:00–5:00 | Teamlid 2 [naam] | Double Diamond met echte foto's/notities; ontwerpkeuzes. |
| 5:00–8:00 | Teamlid 3 [naam] | Architectuur, n8n-workflow, test 1 en minimale AI-input. |
| 8:00–11:00 | Teamlid 4 [naam] | Test 2, BPMN en menselijke review met audit. |
| 11:00–15:00 | Teamlid 5 [naam] | Test 3 en 4, charter en grenzen van controles. |
| 15:00–17:00 | Teamlid 6 [naam] | Echte gebruikers-/groepsfeedback, wijzigingen, Sprint Review en korte retrospective. |
| 17:00–20:00 | Iedereen | Vragen; laat eigenaar van het betreffende onderdeel antwoorden. |

## Context en doel

“Ons prototype bereidt synthetische aanvragen voor huishoudelijke hulp voor. Het verlaagt de hoeveelheid handmatig voorbereidend werk, terwijl een mens de beslissing houdt. Deze demo gebruikt fictief beleid en een AI-stub.” Toon Sprint Goal en DoD. Motiveer de stub: voorspelbare tests en focus op de keten binnen vier uur.

## Double Diamond

Toon echte bewijsstukken per fase, inclusief wat jullie eerst aannamen en wat testers werkelijk vonden. Toon geen leeg werkblad alsof het afgerond onderzoek is. Leg uit waarom jullie één service en een minimale interface kozen.

## Demo voorbereiden

Vooraf: containers gestart; workflow gepubliceerd; browser op UI, n8n en diagram; reviewerkey beschikbaar maar niet zichtbaar projecteren; vier fixtures getest; synthetisch auditbewijs zichtbaar; `test-artifacts/ui-home.png` en eventueel eigen opname/screenshots als back-up.

1. **Laag risico:** klik scenario, toon bericht zonder toekenningsclaim en dossiernummer. Open `Aanvragenoverzicht`, zoek het dossier, klik `Bekijken` en toon exacte AI-input zonder naam/adres/geboortedatum/citizenId/token. Leg een beslissing `Meer informatie nodig` vast en toon dat de zaak in het volledige overzicht blijft staan.
2. **Hoog risico:** toon hoge ernst en meerdere problemen, prioriteitsreview, score en concrete reden. Open de detailtijdlijn en wijs het onderscheid aan tussen aanvraagstatus, voorlopig AI-voorstel en menselijk oordeel.
3. **Fairness:** activeer de duidelijk gemarkeerde demofixture. Toon de verboden term alleen in reviewcontext, echte flag, prioriteitsreview en veilig burgerbericht. Leg uit dat woordenlijsten zowel missers als vals-positieven hebben.
4. **Geen toestemming:** toon foutmelding, audit-event `validation_failed` met correlatie-ID en concrete testinstrumentatie dat geen AI-aanroep plaatsvond.

Leg het Prompt Charter uit: beperkt voorstel, geen discriminatoire grond, alleen aangeboden beleid, geen tools, strikte velden en menselijke beslissing.

## Feedback en terugblik

Gebruik uitsluitend de echte tabel feedback → besluit → aanpassing. Toon de twee toegestane foto's, opleiding van testers en relevante observaties. Benoem ook ontvangen én gegeven presentatiefeedback. Sluit dit blok af met één echt samenwerkingssucces en één concrete volgende verbeteractie.

## Mogelijke vragen

- Waarom n8n? Het bepaalt en visualiseert alle processtappen; de backend levert afgebakende functies.
- Waarom een stub? Toegestaan door de opdracht; maakt de keten en edgecases reproduceerbaar. We claimen geen kwaliteit van een echt LLM.
- Is dit AVG-compliant? Dat is niet aangetoond. Alleen synthetische data; geminimaliseerde zorgdata kan nog gevoelig zijn.
- Is een fairness-flag bewijs van discriminatie? Nee, het is een eenvoudige signalering voor menselijke beoordeling.
- Beslist het systeem bij laag risico? Nee, het geeft een ontvangstbericht en bereidt voor op reguliere menselijke review.
- Wat als een service faalt? Geen succes claimen; technische fout tonen en waar mogelijk loggen.

Als de demo faalt: benoem de echte oorzaak, toon bestaande opname/screenshots en leg uit wat wel en niet is geverifieerd. Gebruik nooit een mockscherm als bewijs van een werkende n8n-uitvoering.
