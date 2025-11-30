---
title: Identificatie
parent: Redacteurs
---

# Identificatie
Conceptversie
{: .label .label-yellow }

We kennen aan ieder begrip een betekenisloze, stabiele UUID (versie 4) toe en leggen deze vast met [`dct:identifier`](http://purl.org/dc/terms/identifier).

Daarnaast leiden we een URI af uit de UUID vereist voor het SKOS-model en .


We volgen de conventies uit de [Stelselcatalogus](https://www.stelselcatalogus.nl/documenten/linked_data_structuur) en [PLDN-URI-strategie](https://www.pldn.nl/wiki/Boek/URI-strategie).

{: .text-delta }
URI-patroon
<dl>
    <dt>Begrip</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/id/{uuid}</code></dd>
    <dt>Document</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/doc/{uuid}</code></dd>
</dl>

waarbij `{uuid}` wordt vervangen door de UUID van het begrip.

{: .note }
Wanneer een verzoek naar de URI van het begrip wordt gedaan vindt automatisch een doorverwijzing plaats naar de URI van het document.

---

{: .note }
Het begrippenkader zelf wordt geïdentificeerd door de URI `https://begrippen.netbeheernederland.nl`.[^1]

De UUIDv4-code wordt vastgelegd met [`dct:identifier`](http://purl.org/dc/terms/identifier).

<details closed markdown="block">
  <summary>
    Voorbeeldcode
  </summary>
  {: .text-delta }
  <pre>
  <11358ed2-de31-455e-8f72-f7f0d8adaa29> a skos:Concept ;
      dct:identifier "11358ed2-de31-455e-8f72-f7f0d8adaa29" ;
      skos:prefLabel "aansluiting"@nl .
  </pre>
</details>

[^1]: Het begrippenkader is een [information resource](#) en zodoende is er geen aparte documentatie-URI nodig.

