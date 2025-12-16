---
title: Identificatie
parent: Redacteurs
---

# Identificatie

Ieder begrip krijgt een betekenisloos, stabiel [NanoID](https://github.com/ai/nanoid).

<dl>
    <dt>Aantal karakters</dt>
    <dd>5</dd>
    <dt>Alafabet</dt>
    <dd><code>2346789abcdefghijkmnpqrtwxyz</code></dd>
</dl>

Hiermee kunnen meer dan 17 miljoen unieke NanoID's worden gegenereerd. Bij 588 voorkomens is de kans op botsing 1%.

Het alfabet bevat geen hoofdletters om problemen met bestandsnamen op Windows te voorkomen. Daarnaast vermijden we look-alikes (`1l0ouv5s`). Reeds bestaande NanoID's die deze karakters bevatten, blijven ongewijzigd.

{: .text-delta }
Voorbeeld

```text
ez6ya
k4anw
kd3hm
d3x6c
wtdtf
```

## Vastlegging

Het NanoID maakt onderdeel uit van de [URI](uris) van een begrip en wordt momenteel op geen andere wijze vastgelegd.[^1] Daarmee zijn enkel mensen, en niet systemen, in staat het NanoID van een begrip te achterhalen.

{: .tip}
> NanoID's kunnen eenvoudig worden gegenereerd met hulpmiddelen in bijvoorbeeld Visual Studio Code of via diverse websites zoals [nanoid.jormaechea.com.ar](https://nanoid.jormaechea.com.ar/?alphabet=2346789abcdefghijkmnpqrtwxyz&length=5) of [nanoid.yuuniworks.com](https://nanoid.yuuniworks.com/).
>
> In Visual Studio Code kun je [Mentor](https://marketplace.visualstudio.com/items?itemName=faubulous.mentor) gebruiken om bij een NanoID de voorkeursterm te tonen.

---

{: .text-delta }
Voetnoten

[^1]: Het is gangbaar `dcterms:identifier` te gebruiken voor het vastleggen van een identifier, maar het extra onderhoud en de foutgevoeligheid dat dit met zich meebrengt maakt dat wij hiertegen hebben besloten. Tevens schrijft [NL-SBB](NL-SBB) dit niet voor.
