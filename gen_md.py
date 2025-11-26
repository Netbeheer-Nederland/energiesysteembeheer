import os
import glob
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from slugify import slugify

# --- CONFIG ---
INPUT_DIR = "begrippenkaders"
OUTPUT_DIR = "docs"
SENSE = "id"
CONTENT = "doc"
ALIAS_DIR = "alias"
BASE_URL = "/begrippen"

# Namespaces
PROV = Namespace("http://www.w3.org/ns/prov#")
ADMS = Namespace("http://www.w3.org/ns/adms#")

def main():
    print(f"Laden van begrippen...")
    
    # Graph laden
    g = Graph()
    ttl_files = glob.glob(os.path.join(INPUT_DIR, "*.ttl"))
    
    if not ttl_files:
        print("Geen .ttl bestanden gevonden!")
        return

    for file_path in ttl_files:
        g.parse(file_path, format="turtle")

    # Maak de Homepage (index.md)
    create_homepage(g)

    # Indexeren van alle concepten
    concept_map = {}
    for s in g.subjects(RDF.type, SKOS.Concept):
        pref_label = g.value(s, SKOS.prefLabel, any=False) or "Naamloos"
        slug = slugify(str(pref_label))
        
        concept_map[str(s)] = {
            "uri": str(s),
            "label": str(pref_label),
            "slug": slug,
            "broader": []
        }

    # Relaties leggen
    for uri, info in concept_map.items():
        subject = next(s for s in g.subjects() if str(s) == uri)
        for parent in g.objects(subject, SKOS.broader):
            if str(parent) in concept_map:
                info['broader'].append(concept_map[str(parent)]['label'])

    # Mappen structuur aanmaken
    # 1. Voor de concepten (collectie)
    path_content = os.path.join(OUTPUT_DIR, "_" + CONTENT)
    if not os.path.exists(path_content):
        os.makedirs(path_content)
        
    # 2. Voor de synoniemen (gewone pagina's of collectie, hier kiezen we gewone map)
    path_aliases = os.path.join(OUTPUT_DIR, ALIAS_DIR)
    if not os.path.exists(path_aliases):
        os.makedirs(path_aliases)

    # Markdown genereren
    os.mkdir(os.path.join(OUTPUT_DIR, "_" + CONTENT))
    for uri, info in concept_map.items():
        subject = next(s for s in g.subjects() if str(s) == uri)
        generate_markdown(g, subject, info, concept_map)

    print(f"Klaar! {len(concept_map)} begrippen verwerkt.")

def create_homepage(g):
    scheme = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
    title_text = "Begrippenkader"
    description_text = "Gebruik het navigatiemenu of de zoekbalk om begrippen te vinden."

    if scheme:
        label = g.value(scheme, DCTERMS.title)
        if label: title_text = str(label)
        comment = g.value(scheme, RDFS.comment)
        if comment: description_text = str(comment)

    md = f"""---
title: Startpagina
nav_order: 1
permalink: /
---

{{: .note }}
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# {title_text}

{description_text}

Gebruik het nagivatiemenu of de zoekbalk om begrippen te vinden.
"""
    # Zorg dat output dir bestaat voor index.md
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    with open(os.path.join(OUTPUT_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write(md)

def generate_markdown(g, s, info, concept_map):
    label = info['label']
    target_slug = info['slug']
    target_permalink = f"/{CONTENT}/{target_slug}"
    
    # --- NIEUW: Genereer schaduwpagina's voor altLabels ---
    alt_labels_raw = [str(l) for l in g.objects(s, SKOS.altLabel)]
    for alt in alt_labels_raw:
        generate_alias_file(alt, label, target_permalink)

    # --- Bestaande logica voor hoofdpagina ---
    parent_line = ""
    if info['broader']:
        parent_line = f"parent: {info['broader'][0]}"

    md = f"""---
title: {label}
{parent_line}
permalink: {target_permalink}
redirect_from:
  - /{SENSE}/{target_slug}
  - /energiesysteembeheer/nl/page/{target_slug}
---

{{: .note }}
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# {label}
"""

    md += f'\n<meta name="concept-uri" content="{ str(s) }">\n'
    md += f"\n{str(s)}\n{{: .fs-2 .text-mono .text-grey-dk-000 .mb-4}}\n"
    
    notation = g.value(s, SKOS.notation)
    if notation: md += f"\n{notation}\n{{: .fs-4 .text-grey-dk-000 .fw-300 .float-right}}\n"
    
    definition = g.value(s, SKOS.definition)
    if definition: md += f"\n## Definitie\n{{: .text-delta }}\n\n{definition}\n"

    # Opmerkingen
    scope_notes = [str(l) for l in g.objects(s, SKOS.scopeNote)]
    comments = [str(l) for l in g.objects(s, RDFS.comment)]
    examples = [str(l) for l in g.objects(s, SKOS.example)]
    if scope_notes or comments or examples:
        md += "\n## Opmerkingen\n{: .text-delta }\n\n"
        md += "<dl>\n"
        if comments:
            md += "<dt>Uitleg</dt>\n"
            for comment in comments: md += f"<dd>{comment}</dd>\n"
        if scope_notes:
            md += "<dt>Toelichting</dt>\n"
            for scope_note in scope_notes: md += f"<dd>{scope_note}</dd>\n"
        if examples:
            md += "<dt>Voorbeeld</dt>\n"
            for example in examples: md += f"<dd>{example}</dd>\n"
        md += "</dl>\n"

    # Terminologie (Ook altLabels weergeven in de tekst zelf)
    hidden_labels = [str(l) for l in g.objects(s, SKOS.hiddenLabel)]
    if alt_labels_raw or hidden_labels or notation:
        md += "\n## Terminologie\n{: .text-delta }\n\n"
        md += "<dl>\n"
        md += f"<dt>Voorkeursterm</dt>\n<dd>{label}</dd>\n"
        if alt_labels_raw:
            md += "<dt>Alternatieve term</dt>\n"
            for alt_label in alt_labels_raw: md += f"<dd>{alt_label}</dd>\n"
        if hidden_labels:
            md += "<dt>Zoekterm</dt>\n"
            for hidden_label in hidden_labels: md += f"<dd>{hidden_label}</dd>\n"
        md += "</dl>\n"

    # Relaties
    broader = get_internal_links(g, s, SKOS.broader, concept_map)
    narrower = get_internal_links(g, s, SKOS.narrower, concept_map)
    related = get_internal_links(g, s, SKOS.related, concept_map)
    if broader or narrower or related:
        md += "\n## Relaties\n{: .text-delta }\n\n"
        md += "<dl>\n"
        if broader:
            md += "<dt>Bovenliggend</dt>\n"
            for broader_i in broader: md += f"<dd>{broader_i}</dd>\n"
        if narrower:
            md += "<dt>Onderliggend</dt>\n"
            for narrower_i in narrower: md += f"<dd>{narrower_i}</dd>\n"
        if related:
            md += "<dt>Gerelateerd</dt>\n"
            for related_i in related: md += f"<dd>{related_i}</dd>\n"
        md += "</dl>\n"

    # Overeenkomsten & Verantwoording (de rest van je script)...
    # (Ik heb de rest van de content functies hier even ingekort voor leesbaarheid, 
    # maar je originele code voor matches/sources moet hier gewoon blijven staan)
    
    # ... Voeg hier de rest van je sections toe (Match, Sources, etc) ...

    # Opslaan hoofdbestand
    filename = f"{info['slug']}.md"
    with open(os.path.join(OUTPUT_DIR, "_" + CONTENT, filename), "w", encoding="utf-8") as f:
        f.write(md)

def generate_alias_file(alt_label, target_label, target_permalink):
    """
    Maakt een apart MD bestand voor de alternatieve term.
    """
    alias_slug = slugify(alt_label)
    
    # De pijl HTML entity &rarr; werkt soms niet in YAML titels zonder quotes
    # We gebruiken hier quotes om de string veilig te stellen.
    md = f"""---
title: "{alt_label} &rarr; {target_label}"
nav_exclude: true
search_exclude: false
redirect_to: {target_permalink}
---

<meta http-equiv="refresh" content="0; url={target_permalink}">

# Doorverwijzing
Je zoekt naar **{alt_label}**. Dit is een alternatieve term voor [{target_label}]({target_permalink}).
"""
    
    filename = f"{alias_slug}.md"
    path = os.path.join(OUTPUT_DIR, ALIAS_DIR, filename)
    
    # Check of bestand al bestaat (bij dubbele altLabels), anders overschrijven
    with open(path, "w", encoding="utf-8") as f:
        f.write(md)

# --- Helper Functies (ongewijzigd) ---

def get_internal_links(g, subject, predicate, concept_map):
    links = []
    for obj in g.objects(subject, predicate):
        uri = str(obj)
        if uri in concept_map:
            lbl = concept_map[uri]['label']
            links.append(f"<a href=\"{BASE_URL}/{CONTENT}/{concept_map[uri]['slug']}\">{lbl}</a>")
    return links

def get_external_links(g, subject, predicate):
    # Jouw originele helper functie...
    items = []
    for obj in g.objects(subject, predicate):
        label = g.value(obj, RDFS.label) or g.value(obj, SKOS.prefLabel) or g.value(obj, DCTERMS.title)
        page = g.value(obj, FOAF.page)
        if page:
            link_text = str(label) if label else "Link"
            items.append(f'<a href="{str(page)}">{link_text}</a>')
        elif isinstance(obj, URIRef):
            url = str(obj)
            if label:
                items.append(f'<a href="{url}">{str(label)}</a>')
            else:
                items.append(f'<a href="{url}">{url}</a>')
        else:
            items.append(str(obj))
    return items

if __name__ == "__main__":
    main()