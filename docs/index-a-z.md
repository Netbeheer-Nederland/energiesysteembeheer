---
title: Index A-Z
nav_order: 5
---

{: .note }
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# Alfabetisch overzicht

{% assign entries_string = "" %}

{% comment %} --- STAP 1: Bouw de lijst met HTML/Markdown inbegrepen --- {% endcomment %}
{% for p in site.documents %}
  {% assign url = p.url | relative_url %}

  {% comment %} 1. De hoofdpagina: Gewone Markdown link {% endcomment %}
  {% comment %} Formaat: SorteerNaam :: OutputString {% endcomment %}
  {% assign link_md = "[" | append: p.title | append: "](" | append: url | append: ")" %}
  {% assign entry = p.title | append: "::" | append: link_md %}
  {% assign entries_string = entries_string | append: entry | append: "|||" %}

  {% comment %} 2. De alt_labels: HTML met grijze tekst en pijl {% endcomment %}
  {% if p.alt_labels %}
    {% for alt in p.alt_labels %}
      {% assign alt_span = '<span class="grey-dk-000">' | append: alt | append: '</span>' %}
      {% assign display_string = alt_span | append: " &rarr; " | append: md_link %}
      {% assign entry = alt | append: "::" | append: alt_html %}
      {% assign entries_string = entries_string | append: entry | append: "|||" %}
    {% endfor %}
  {% endif %}
{% endfor %}

{% comment %} --- STAP 2: Sorteren --- {% endcomment %}
{% assign sorted_entries = entries_string | split: "|||" | sort_natural %}
{% assign current_letter = "" %}

{% comment %} --- STAP 3: Output --- {% endcomment %}
{% for item in sorted_entries %}
  {% if item == "" %}{% continue %}{% endif %}

  {% comment %} Splits op de eerste '::' {% endcomment %}
  {% assign parts = item | split: "::" %}
  {% assign sort_name = parts[0] %}
  {% comment %} Omdat parts[1] de rest is, moeten we oppassen als je '::' in je titels gebruikt, maar meestal gaat dit goed {% endcomment %}
  {% assign display_string = parts[1] %}

  {% assign char = sort_name | slice: 0, 1 | slugify | upcase %}

  {% if char != current_letter %}
    {% assign current_letter = char %}
## {{ char }}

  {% endif %}
{{ display_string }}
{: .lh-tight}

{% endfor %}
