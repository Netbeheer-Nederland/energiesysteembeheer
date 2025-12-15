---
title: Proces
parent: Redacteurs
---

# Proces
Conceptversie
{: .label .label-yellow }

![Proces]({{ site.baseurl }}/assets/images/proces.drawio.svg)

## Lifecycle van een begrip

### Status

Om de lifecycle-status van een begrip te duiden maken we gebruik van de [INSPIRE Registry Status-codes](https://inspire.ec.europa.eu/registry/status).

We voorzien deze statussen van een Nederlandse vertaling en een [toelichting](https://docs.geostandaarden.nl/nl-sbb/nl-sbb/#dfn-toelichting) voor de toepassing ervan op de lifecycle van begrippen.

Statuscodes
{: .text-delta }
<dl>
<dt><a href="https://inspire.ec.europa.eu/registry/status/invalid">ongeldig</a></dt>
<dd>Een begrip dat eerder <a href="https://inspire.ec.europa.eu/registry/status/valid">geldig</a> was, is door foutieve wijzigingen ongeldig geworden.</dd>

<dt><a href="https://inspire.ec.europa.eu/registry/status/retired">buiten gebruik</a></dt>
<dd>Dit begrip is niet langer in gebruik en is niet vervangen door een ander begrip.</dd>

<dt><a href="https://inspire.ec.europa.eu/registry/status/submitted">ingediend</a></dt>
<dd>Dit begrip is ingediend om in het begrippenkader te worden opgenomen.</dd>

<dt><a href="https://inspire.ec.europa.eu/registry/status/superseded">vervangen</a></dt>
<dd>Dit begrip is niet langer in gebruik en is vervangen door een ander begrip.</dd>

<dt><a href="https://inspire.ec.europa.eu/registry/status/valid">geldig</a></dt>
<dd>Dit begrip is geldig en in gebruik.</dd>
</dl>

---

```mermaid
stateDiagram-v2
    direction LR
    state "in concept" as concept
    state review <<choice>>
    state reviewOpties <<choice>>
    state definitief
    state uitgefaseerd
    state opgeheven
    state uitfasering <<choice>>
    
    [*] --> concept
    concept --> review
    review --> definitief: goedgekeurd
    review --> reviewOpties : afgekeurd
    reviewOpties --> concept
    reviewOpties --> verwijderd
    definitief --> uitfasering
    uitfasering --> definitief: goedgekeurd
    uitfasering --> uitgefaseerd: afgekeurd
    uitgefaseerd --> [*]
    verwijderd --> [*]
```

