---
title: NBility
parent: Redacteurs
---

# NBility

De top-begrippen van het begrippenkader worden gevormd door de NBility-bedrijfsobjecten. Dit zorgt voor duidelijkheid over eigenaarschap voor wat betreft de begrippen en hun definities. Elk nieuw begrip moet onder een van deze top-begrippen worden gehangen, direct of indirect.

## Wat is NBility?

[NBility](https://nbility-model.github.io/) is een gezamenlijk model van de Nederlandse netbeheerders en beschrijft in samenhang hun functies, processen en objecten, op verschillende detailniveaus. Het biedt een gemeenschappelijke taal om de activiteiten van netbeheerders te beschrijven, gericht op de waarde die wij leveren aan klanten en de maatschappij.

Een belangrijk onderdeel van NBility zijn de bedrijfsobjecten: de dingen die wij transformeren in processen om waarde te creëren, zoals `aansluiting` en `netcomponent`.

## Waarom vormt NBility de basis?

In dit begrippenkader hanteren we de bedrijfsobjecten uit NBility als de 'top-begrippen' (`skos:topConceptOf`). We kiezen hiermee voor een indeling op basis van bedrijfscontext. Neem een elektriciteitskabel. Ligt deze in het magazijn, dan is het in de context van de organisatie `materiaal` (voorraad). Ligt diezelfde kabel in de grond, dan vervult hij de rol van `netcomponent`. Hoewel het fysieke object hetzelfde blijft, is de betekenis voor de organisatie, en daarmee de data die we erover vastleggen, veranderd. Door NBility als basis te nemen, koppelen we de definitie van een begrip direct aan deze functionele rol.

Maar belangrijker: NBility is cruciaal voor goed eigenaarschap. Omdat elk begrip in dit kader te herleiden is tot een NBility-bedrijfsobject, weten we bij wie we moeten zijn. Het bedrijfsobject wijst ons de weg naar de juiste afdeling of rol binnen de netbeheerders.

## Synchronisatie en levenscyclus

Een begrip in een woordenboek is iets anders dan een bedrijfsobject in een architectuurmodel. Ze hebben hun eigen spelregels en levenscyclus. Daarom nemen we de definitie van een NBility-bedrijfsobject over, maar hanteren we het begrip als deel van dit begrippenkader, met een eigen identificatie (URI). We verwijzen wel naar NBility als bron (`dct:source`). Dezelfde werkwijze hanteren we bij begrippen die we overnemen uit wetteksten.

Deze manier van werken beschermt ons begrippenkader tegen onbedoelde wijzigingen. Mocht een bedrijfsobject in NBility van betekenis veranderen, dan passen we de definitie hier niet stilzwijgend aan. In plaats daarvan creëren we een nieuw begrip voor de nieuwe betekenis. Het oude begrip krijgt een nieuwe plek in de hiërarchie (onder een van de NBility-topbegrippen) of wordt buiten gebruik gesteld. Zo blijft de historie zuiver en de data-uitwisseling stabiel.
