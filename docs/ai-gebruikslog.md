# AI-gebruikslog

Datum: 1 oktober 2026. Gebruikte assistent: OpenAI Codex in ChatGPT Work. De gebruiker gaf een uitgebreide bouwprompt met functionele, ethische en onderwijscriteria. De assistent is gebruikt voor implementatie, workflowexport, interface, tests, diagrammen en documentatie. Waar parallelle agents werden ingezet, werkten zij aan afgebakende onderdelen onder integratie van de hoofdagent.

| Gebruik | Resultaat | Controle / eigenaar |
|---|---|---|
| Backend en privacygrens genereren | FastAPI-code, schema's, volledig zaakoverzicht en detailendpoint | Automatische teststatus: zie `testresultaten.md`. Menselijke codecontrole nog uitvoeren. |
| n8n-workflow genereren en controleren | Gesaneerde actuele JSON-export | Live Docker/n8n-webhooktests geslaagd; ruwe exportmetadata met eigenaarinformatie niet ingeleverd. |
| UI genereren | Tabs voor indienen, aanvragenoverzicht, beoordeling, auditlog en demo-uitleg | Syntaxcheck en render-screenshot geslaagd; handmatige klikflow en bruikbaarheidstest nog uitvoeren. |
| Testgevallen formuleren en uitvoeren waar mogelijk | Fixtures, tests en testrapport | Alleen werkelijk uitgevoerde resultaten in rapport gebruiken. |
| BPMN, architectuur en formats schrijven | Diagrammen, charter, presentatie en werkbladen | XML-controle en gerenderde visuele BPMN-controle door assistent; team controleert procesinterpretatie. |

De documentatie-agent heeft de aangeleverde opdrachttekst gelezen en documenten daarop gebaseerd. De BPMN- en SVG-bestanden zijn als XML geparseerd; alle 18 sequence flows verwijzen naar bestaande knopen en diagramcoördinaten zijn opgenomen. Geen externe beleidsbronnen gebruikt: de beleidsregels zijn bewust fictief. Geen deelnemers, interviewresultaten, foto's, gebruikersfeedback of menselijke goedkeuringen verzonnen.

## Zelf nog controleren en registreren

- [ ] Kan ieder teamlid uitleggen waar n8n orkestreert?
- [ ] AI-input inspecteren: geen identificerende gegevens of token.
- [x] Vier demo's automatisch via echte n8n-webhook uitgevoerd en uitslag genoteerd.
- [ ] Risico- en fairnesscode begrijpen; beperkingen uitleggen.
- [x] Menselijke demo-beslissing en audit automatisch gecontroleerd.
- [ ] Frontend handmatig door team laten klikken en beoordelen.
- [ ] Eigen aanpassingen noteren: [bestanden, wijziging, reden, datum].
- [ ] Namen en werkelijke feedback invullen.

De AI-stub in het product is een deterministische simulatie. Dit staat los van de AI-assistent die hielp het prototype te programmeren. Maak dit onderscheid expliciet tijdens de presentatie.
