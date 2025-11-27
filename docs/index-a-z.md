---
title: Index A-Z
---

{: .note }
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# Alfabetisch overzicht

{% assign current_letter = "" %}
{% assign sorted_pages = site.html_pages | sort: "title" %}

{% for p in sorted_pages %}
  {% if p.url contains "/doc/" and p.url != page.url %}

    {% assign char = p.title | slice: 0, 1 | upcase %}

    {% if char != current_letter %}

      {% if current_letter != "" %}
        </ul>
      {% endif %}

      <h2 style="text-delta">{{ char }}</h2>

      <ul>

      {% assign current_letter = char %}

    {% endif %}

    <li>
      <a href="{{ p.url | relative_url }}">{{ p.title }}</a>
    </li>

  {% endif %}
{% endfor %}

{% if current_letter != "" %}
  </ul>
{% endif %}

<h3>Debug Modus</h3>
<ul>
  {% for p in site.html_pages %}
    <li>
      Titel: <strong>{{ p.title }}</strong> <br>
      Interne URL: <code>{{ p.url }}</code>
    </li>
  {% endfor %}
</ul>
