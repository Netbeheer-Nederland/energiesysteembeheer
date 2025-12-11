import os
import glob
from collections import defaultdict # Nodig voor het groeperen
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from slugify import slugify

# --- CONFIG ---
INPUT_DIR = "begrippenkaders"
OUTPUT_DIR = "docs"
SENSE = "term"
CONTENT = "doc"
ALIAS_DIR = "alias"
BASE_URL = "/energiesysteembeheer"

def main():
    print(f"Laden van begrippen...")
    
    g = Graph()
    ttl_files = glob.glob(os.path.join(INPUT_DIR, "*.ttl"))
    
    if not ttl_files:
        print("Geen .ttl bestanden gevonden!")
        return

    for file_path in ttl_files:
        g.parse(file_path, format="turtle")

    create_homepage(g)

    # Concepten indexeren
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

    # Mappen aanmaken
    path_content = os.path.join(OUTPUT_DIR, "_" + CONTENT)
    path_aliases = os.path.join(OUTPUT_DIR, ALIAS_DIR)
    os.makedirs(path_content, exist_ok=True)
    os.makedirs(path_aliases, exist_ok=True)

    # --- Dictionary om altLabels te verzamelen ---
    # Structuur: { "afnemer": [ {"label": "Klant", "url": "/doc/klant"}, ... ] }
    alias_collection = defaultdict(list)

    # Markdown genereren voor begrippen
    for uri, info in concept_map.items():
        subject = next(s for s in g.subjects() if str(s) == uri)
        
        # We geven de alias_collection mee om te vullen
        generate_markdown(g, subject, info, concept_map, alias_collection)

    # Nu pas de alias-bestanden genereren
    process_aliases(alias_collection)

    print(f"Klaar! {len(concept_map)} begrippen en {len(alias_collection)} synoniemen verwerkt.")

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

def generate_markdown(g, s, info, concept_map, alias_collection):
    label = info['label']
    target_slug = info['slug']
    target_permalink = f"/{CONTENT}/{target_slug}"
    
    # --- VERZAMELEN ZOEKTERMEN ---
    alt_labels = [str(l) for l in g.objects(s, SKOS.altLabel)]
    hidden_labels = [str(l) for l in g.objects(s, SKOS.hiddenLabel)]
    
    # Alles op één hoop (Just the Docs maakt geen onderscheid in redirect-gedrag)
    all_search_terms = alt_labels + hidden_labels
    
    for term in all_search_terms:
        alias_slug = slugify(term)
        alias_collection[alias_slug].append({
            "term": term, 
            "target_label": label, 
            "target_url": target_permalink
        })

    parent_line = ""
    if info['broader']:
        parent_line = f"parent: {info['broader'][0]}"

    alt_labels_str = "".join([f"\n  - {alt}" for alt in alt_labels])

    md = f"""---
title: {label}
{parent_line}
permalink: {target_permalink}
alt_labels:{alt_labels_str}
redirect_from:
  - /{SENSE}/{target_slug}
  - /energiesysteembeheer/nl/page/{target_slug}
---

{{: .note }}
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# {label}
"""

    notation = g.value(s, SKOS.notation)
    if notation: md += f"\n{notation}\n{{: .fs-4 .text-grey-dk-000 .fw-300 .float-right}}\n"

    definition = g.value(s, SKOS.definition)
    if definition:
        md += f"\n> {definition}\n"

    comments = [str(l) for l in g.objects(s, RDFS.comment)]
    for comment in comments: md += f"\n{comment}\n"

    scope_notes = [str(l) for l in g.objects(s, SKOS.scopeNote)]
    for scope_note in scope_notes: md += f"\n{scope_note}\n"

    examples = [str(l) for l in g.objects(s, SKOS.example)]
    if examples:
        md += f"\nVoorbeeld: <em>{'</em>, <em>'.join(examples)}</em>\n"

    if alt_labels:
        md += f"\nAlternatieve term: <em>{'</em>, <em>'.join(alt_labels)}</em>\n"

    if hidden_labels:
        md += f"\nZoekterm: <em>{'</em>, <em>'.join(hidden_labels)}</em>\n"

    md += "\n---\n"

    md += "\n<dl>\n"

    broader = get_internal_links(g, s, SKOS.broader, concept_map)
    if broader:
        md += "<dt>Bovenliggend</dt>\n"
        for broader_i in broader: md += f"<dd>{broader_i}</dd>\n"

    narrower = get_internal_links(g, s, SKOS.narrower, concept_map)
    if narrower:
        md += "<dt>Onderliggend</dt>\n"
        for narrower_i in narrower: md += f"<dd>{narrower_i}</dd>\n"

    related = get_internal_links(g, s, SKOS.related, concept_map)
    if related:
        md += "<dt>Gerelateerd</dt>\n"
        for related_i in related: md += f"<dd>{related_i}</dd>\n"

    broad_match = get_external_links(g, s, SKOS.broadMatch)
    if broad_match:
        md += "<dt>Overeenkomstig bovenliggend</dt>\n"
        for broad_match_i in broad_match: md += f"<dd>{broad_match_i}</dd>\n"

    narrow_match = get_external_links(g, s, SKOS.narrowMatch)
    if narrow_match:
        md += "<dt>Overeenkomstig onderliggend</dt>\n"
        for narrow_match_i in narrow_match: md += f"<dd>{narrow_match_i}</dd>\n"

    close_match = get_external_links(g, s, SKOS.closeMatch)
    if close_match:
        md += "<dt>Vrijwel overeenkomstig</dt>\n"
        for close_match_i in close_match: md += f"<dd>{close_match_i}</dd>\n"

    exact_match = get_external_links(g, s, SKOS.exactMatch)
    if exact_match:
        md += "<dt>Exact overeenkomstig</dt>\n"
        for exact_match_i in exact_match: md += f"<dd>{exact_match_i}</dd>\n"

    related_match = get_external_links(g, s, SKOS.relatedMatch)
    if related_match:
        md += "<dt>Overeenkomstig verwant</dt>\n"
        for related_match_i in related_match: md += f"<dd>{related_match_i}</dd>\n"

    sources = get_external_links(g, s, DCTERMS.source)
    if sources:
        md += "<dt>Bron</dt>\n"
        for source in sources: md += f"<dd>{source}</dd>\n"

    change_notes = [str(l) for l in g.objects(s, SKOS.changeNote)]
    if change_notes:
        md += "<dt>Wijzigingsnotities</dt>\n"
        for change_note in change_notes: md += f"<dd>{change_note}</dd>\n"

    history_notes = [str(l) for l in g.objects(s, SKOS.historyNote)]
    if history_notes:
        md += "<dt>Historie</dt>\n"
        for history_note in history_notes: md += f"<dd>{history_note}</dd>\n"

    md += f"<dt>URI</dt> <dd><code>{str(s)}</code></dd>\n"

    md += "</dl>\n"

    md += '<div id="concept-usages" class="mt-6"></div>'

    filename = f"{info['slug']}.md"
    with open(os.path.join(OUTPUT_DIR, "_" + CONTENT, filename), "w", encoding="utf-8") as f:
        f.write(md)

def process_aliases(alias_collection):
    """
    Kijkt naar alle verzamelde synoniemen.
    - Is er 1 doel? -> Maak een Redirect pagina.
    - Zijn er meer? -> Maak een Doorverwijspagina.
    """
    for slug, targets in alias_collection.items():
        
        # De leesbare term pakken we van de eerste entry (ze zijn toch hetzelfde, op hoofdletters na)
        readable_term = targets[0]['term']
        filename = f"{slug}.md"
        filepath = os.path.join(OUTPUT_DIR, ALIAS_DIR, filename)
        
        # SCENARIO 1: Uniek synoniem (Directe redirect)
        if len(targets) == 1:
            target = targets[0]
            md = f"""---
title: "{readable_term} &rarr; {target['target_label']}"
nav_exclude: true
search_exclude: false
redirect_to: {target['target_url']}
---
<meta http-equiv="refresh" content="0; url={target['target_url']}">

# Doorverwijzing
Je zoekt naar **{readable_term}**. Dit is een synoniem voor [{target['target_label']}]({target['target_url']}).
"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)

        # SCENARIO 2: Dubbele alias (Doorverwijspagina)
        else:
            # We maken een lijstje met bullet points
            list_items = ""
            for t in targets:
                list_items += f"- [{t['target_label']}]({t['target_url']})\n"

            md = f"""---
title: "{readable_term} (Doorverwijspagina)"
---

# {readable_term}

De term **{readable_term}** kan verwijzen naar meerdere begrippen:

{list_items}

{{: .note }}
Kies hierboven het begrip dat u zoekt.
"""
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(md)

# --- Helper Functies ---

def get_internal_links(g, subject, predicate, concept_map):
    links = []
    for obj in g.objects(subject, predicate):
        uri = str(obj)
        if uri in concept_map:
            lbl = concept_map[uri]['label']
            links.append(f"<a href=\"{BASE_URL}/{CONTENT}/{concept_map[uri]['slug']}\">{lbl}</a>")
    return links

def get_external_links(g, subject, predicate):
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
