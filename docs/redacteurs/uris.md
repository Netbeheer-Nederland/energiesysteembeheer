---
title: URI-strategie
parent: Redacteurs
---

# URI-strategie

Met deze URI-strategie borgen we een persistente en webvriendelijke identificatie in lijn met [Linked Data](https://www.w3.org/DesignIssues/LinkedData.html)- en [FAIR-principes](https://www.go-fair.org/fair-principles/).

URI-syntax
{: .text-delta }

<dl>
    <dt>Begrippenkader</dt>
    <dd><code>https://begrippen.netbeheernederland.nl</code></dd>
    <dt>Begrip (identiteit)</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/id/{id}</code></dd>
    <dt>Begrip (documentatie)</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/doc/{id}</code></dd>
</dl>

waarbij `{id}` wordt vervangen door de [identifier](identificatie) van het begrip.

---

Het begrippenkader is een [information resource](https://www.w3.org/TR/2004/REC-webarch-20041215/#def-information-resource) en wordt daarom geïdentificeerd met één URI, die tevens het adres vormt van de documentatie.

Voor begrippen volgen we de strategie beschreven in [sectie 4.1 van Cool URIs for the Semantic Web](https://www.w3.org/TR/cooluris/#r303gendocument). Hiermee sluiten we aan bij conventies uit de [Stelselcatalogus](https://www.stelselcatalogus.nl/documenten/linked_data_structuur) en de [PLDN-URI-strategie](https://www.pldn.nl/wiki/Boek/URI-strategie). Deze strategie maakt onderscheid tussen de identiteit van het begrip (`/id/{id}`) en het document dat een beschrijving van het begrip biedt (`/doc/{id}`), en schrijft een automatisch doorverwijzingsmechanisme voor om de documentatie te bereiken.[^1]

{: .text-delta }
Voorbeeld

Het begrip met NanoID `yp6xq` krijgt de URI `https://begrippen.netbeheernederland.nl/id/yp6xq`.

---

{: .text-delta }
Voetnoten

[^1]: Voor nu is een client-side doorverwijzingsmechanisme geïmplementeerd in plaats van een server-side 303-redirect. Daarnaast is vooralsnog alleen een HTML-representatie beschikbaar, totdat we [content-negotiation](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Content_negotiation) inrichten.
