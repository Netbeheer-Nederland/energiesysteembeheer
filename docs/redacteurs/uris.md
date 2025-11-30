---
title: URI-beleid
parent: Redacteurs
---

# URI-beleid
Conceptversie
{: .label .label-yellow }

{: .text-delta }
URI-patroon
<dl>
    <dt>Begrippenkader</dt>
    <dd><code>https://begrippen.netbeheernederland.nl</code></dd>
    <dt>Begrip</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/id/{id}</code></dd>
    <dt>Begrip (beschrijving)</dt>
    <dd><code>https://begrippen.netbeheernederland.nl/doc/{id}</code></dd>
</dl>

waarbij `{id}` wordt vervangen door de <a href="/energiesysteembeheer/doc/redacteurs/identificatie">identifier</a> van het begrip.

---

Voor begrippen volgen we - net als de [Stelselcatalogus](https://www.stelselcatalogus.nl/documenten/linked_data_structuur) en de [PLDN-URI-strategie](https://www.pldn.nl/wiki/Boek/URI-strategie) - de strategie beschreven in [sectie 4.1 van Cool URIs for the Semantic Web
](https://www.w3.org/TR/cooluris/#r303gendocument).

Voor het begrippenkader hanteren we enkel één URI, wat volstaat omdat het een [information resource](https://www.w3.org/TR/2004/REC-webarch-20041215/#def-information-resource) is.

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