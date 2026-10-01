# Scrum — één sprint van vier uur

## Project Goal

Een werkend prototype dat WMO-aanvragen automatisch en transparant voorbereidt met AI, zonder identificerende persoonsgegevens aan de AI te geven, en complexe of risicovolle aanvragen naar menselijke beoordeling stuurt. Gebruikersfeedback moet aantoonbaar worden opgehaald en verwerkt.

## Sprint Goal

Binnen vier uur doorloopt een synthetische aanvraag voor huishoudelijke hulp de n8n-keten, inclusief minimalisatie, stubvoorstel, controles, audit en review. De vier verplichte scenario's worden aantoonbaar gedemonstreerd en de verplichte feedback wordt verwerkt.

## Rollen — zelf invullen

Product Owner: [naam]. Scrum Master: [naam]. Teamleden 1–6: [namen]. Sprint: [start/eindtijd]. De hieronder opgenomen status is een overdrachtschecklist, geen claim dat het team deze stappen al heeft afgerond.

| ID | Prio | User story / sprintitem | Status bij overdracht |
|---|---|---|---|
| 1 | Must | Als burger wil ik een aanvraag via een webhook indienen. | Getest via echte n8n-webhook. |
| 2 | Must | Als burger wil ik dat de AI geen identificerende gegevens ontvangt. | Backend- en E2E-tests geslaagd. |
| 3 | Must | Als reviewer wil ik een voorstel met verwijzingen naar beleid. | Aanwezig in detail- en reviewweergave; getest. |
| 4 | Must | Als reviewer wil ik risico, fairness en ongeldige redenen herkennen. | Getest met hoog risico en fairness-fixture. |
| 5 | Must | Als burger wil ik begrijpen wie beslist. | UI en vaste berichten aangepast; echte gebruikerstest open. |
| 6 | Must | Als auditor wil ik beslissingen kunnen reconstrueren. | Overzicht, detail, tijdlijn en auditlog toegevoegd; getest. |
| 7 | Must | Als beoordelaar wil ik een menselijk oordeel vastleggen. | E2E-beslissing `needs_information` getest. |
| 8 | Must | Als team wil ik de vier testcases live aantonen. | Automatisch via echte webhook getest; live presentatie nog oefenen. |
| 9 | Must | Als team wil ik feedback van twee niet-ICT-studenten verwerken. | Nog uit te voeren. |
| 10 | Must | Als team wil ik presentatiefeedback uitwisselen. | Nog uit te voeren. |
| 11 | Must | Als ander team wil ik het systeem starten. | README aangeleverd; onafhankelijke installatiecheck open. |

Maak hiervan desgewenst het bord Te doen → Bezig → Klaar. Werk de status alleen bij op basis van bewijs. Alle Must-items vormen de Sprint Backlog; mogelijke latere Product Backlog-items zijn een echte LLM-integratie, fijnmazige autorisatie en robuustere fairness-evaluatie.

## Definition of Done

- [x] Laag risico geeft automatisch een transparant bericht en opgeslagen zaak.
- [x] Hoog risico/hoge ernst geeft een zichtbare menselijke reviewtaak.
- [x] Verboden term veroorzaakt een echte flag en review.
- [x] Toestemming=false geeft foutmelding zonder AI-aanroep.
- [x] AI-input heeft alleen toegestane velden.
- [x] Audit en menselijke beslissing zijn controleerbaar.
- [x] n8n-export en installatie-instructies zijn controleerbaar.
- [ ] Browserklikflow en Docker-herstartcheck zijn handmatig op presentatielaptop gecontroleerd.
- [ ] Twee echte gebruikerstests en presentatiefeedback zijn vastgelegd en verwerkt.

## Sprint Review — invullen na demo

Getoond: [scenario's]. Aanwezigen: [namen]. Geaccepteerd: [items]. Niet af: [items en gevolg]. Feedback/vervolg: [concrete punten].

## Retrospective — invullen na samenwerking

Wat ging goed: [werkelijk voorbeeld]. Wat kostte onnodig tijd: [werkelijk voorbeeld]. Volgende keer anders: [één concrete afspraak met eigenaar].
