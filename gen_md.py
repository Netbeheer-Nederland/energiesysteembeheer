import os
import shutil
import glob
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from slugify import slugify

# --- CONFIG ---
INPUT_DIR = "begrippenkaders"
OUTPUT_DIR = "docs"
BASE_URL = "/begrippen"

# Namespaces
PROV = Namespace("http://www.w3.org/ns/prov#")
ADMS = Namespace("http://www.w3.org/ns/adms#")

def main():
    print(f"Laden van begrippen...")
    
    # Graph laden
    g = Graph()
    # Pakt alle .ttl files in de map (handig als je het ooit splitst, maar toch 1 geheel wilt)
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
            "permalink": f"/{slug}/",
            "broader": []
        }

    # Relaties leggen (wie is mijn ouder?)
    for uri, info in concept_map.items():
        subject = next(s for s in g.subjects() if str(s) == uri)
        for parent in g.objects(subject, SKOS.broader):
            if str(parent) in concept_map:
                info['broader'].append(concept_map[str(parent)]['label'])

    # Markdown genereren
    for uri, info in concept_map.items():
        subject = next(s for s in g.subjects() if str(s) == uri)
        generate_markdown(g, subject, info, concept_map)

    print(f"Klaar! {len(concept_map)} begrippen gegenereerd in de root.")

def create_homepage(g):
    """Maakt de index.md die als 'Home' fungeert, gevuld met ConceptScheme data."""
    
    # We zoeken het subject dat gedefinieerd is als een skos:ConceptScheme
    # g.value zoekt één willekeurige match (er is er meestal maar 1)
    scheme = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
    
    # Standaard teksten voor fallback
    title_text = "Begrippenkader"
    description_text = "Gebruik het navigatiemenu of de zoekbalk om begrippen te vinden."

    if scheme:
        # Haal de titel op (skos:prefLabel)
        label = g.value(scheme, DCTERMS.title)
        if label:
            title_text = str(label)
        
        # Haal de beschrijving op (rdfs:comment)
        comment = g.value(scheme, RDFS.comment)
        if comment:
            description_text = str(comment)

    md = f"""---
title: Home
nav_exclude: true
permalink: /
hash_redirect: true
---

{{: .note }}
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# {title_text}

{description_text}

Gebruik het nagivatiemenu of de zoekbalk om begrippen te vinden.
"""
    with open(os.path.join(OUTPUT_DIR, "index.md"), "w", encoding="utf-8") as f:
        f.write(md)

def generate_markdown(g, s, info, concept_map):
    label = info['label']
    
    # --- DE TRUC VOOR DE NAVIGATIE ---
    # Heeft het begrip een ouder (broader)?
    # JA -> Parent veld invullen -> Hij wordt ingeklapt
    # NEE -> Geen Parent veld -> Hij wordt een TOP ITEM in de sidebar
    
    parent_line = ""
    if info['broader']:
        # Pak de eerste parent
        parent_line = f"parent: {info['broader'][0]}"
    else:
        # DIT IS EEN TOP CONCEPT
        parent_line = "" 

    # Front Matter
    md = f"""---
title: {label}
{parent_line}
permalink: {info['permalink']}
---

{{: .note }}
Kijk gerust rond! Aan deze website wordt momenteel nog gewerkt.

# {label}
"""

    # --- Content (NL-SBB Standaard) ---

    # URI, code en definitie
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
        md += "<dl>"
        if comments:
            md += "<dt>Uitleg</dt>"
            for comment in comments: md += f"<dd>{comment}</dd>"
        if scope_notes:
            md += "<dt>Toelichting</dt>"
            for scope_note in scope_notes: md += f"<dd>{scope_note}</dd>"
        if examples:
            md += "<dt>Voorbeeld</dt>"
            for example in examples: md += f"<dd>{example}</dd>"
        md += "</dl>"

    # Terminologie
    alt_labels = [str(l) for l in g.objects(s, SKOS.altLabel)]
    hidden_labels = [str(l) for l in g.objects(s, SKOS.hiddenLabel)]
    if alt_labels or hidden_labels or notation:
        md += "\n## Terminologie\n{: .text-delta }\n"
        md += "<dl>"
        md += f"<dt>Voorkeursterm</dt><dd>{label}</dd>"
        if alt_labels:
            md += "<dt>Alternatieve term</dt>"
            for alt_label in alt_labels: md += f"<dd>{alt_label}</dd>"
        if hidden_labels:
            md += "<dt>Zoekterm</dt>"
            for hidden_label in hidden_labels: md += f"<dd>{hidden_label}</dd>"
        md += "</dl>"

    # Relaties
    broader = get_internal_links(g, s, SKOS.broader, concept_map)
    narrower = get_internal_links(g, s, SKOS.narrower, concept_map)
    related = get_internal_links(g, s, SKOS.related, concept_map)
    if broader or narrower or related:
        md += "\n## Relaties\n{: .text-delta }\n\n"
        md += "<dl>"
        if broader:
            md += "<dt>Bovenliggend</dt>"
            for broader_i in broader: md += f"<dd>{broader_i}</dd>"
        if narrower:
            md += "<dt>Onderliggend</dt>"
            for narrower_i in narrower: md += f"<dd>{narrower_i}</dd>"
        if related:
            md += "<dt>Gerelateerd</dt>"
            for related_i in related: md += f"<dd>{related_i}</dd>"
        md += "</dl>"

    # Overeenkomstig
    broad_match = get_external_links(g, s, SKOS.broadMatch)
    narrow_match = get_external_links(g, s, SKOS.narrowMatch)
    close_match = get_external_links(g, s, SKOS.closeMatch)
    exact_match = get_external_links(g, s, SKOS.exactMatch)
    related_match = get_external_links(g, s, SKOS.relatedMatch)
    if broad_match or narrow_match or close_match or exact_match or related_match:
        md += "\n## Overeenkomstig\n{: .text-delta }\n\n"
        md += "<dl>"
        if broad_match:
            md += "<dt>Overeenkomstig bovenliggend</dt>"
            for broad_match_i in broad_match: md += f"<dd>{broad_match_i}</dd>"
        if narrow_match:
            md += "<dt>Overeenkomstig onderliggend</dt>"
            for narrow_match_i in narrow_match: md += f"<dd>{narrow_match_i}</dd>"
        if close_match:
            md += "<dt>Vrijwel overeenkomstig</dt>"
            for close_match_i in close_match: md += f"<dd>{close_match_i}</dd>"
        if exact_match:
            md += "<dt>Exact overeenkomstig</dt>"
            for exact_match_i in exact_match: md += f"<dd>{exact_match_i}</dd>"
        if related_match:
            md += "<dt>Overeenkomstig verwant</dt>"
            for related_match_i in related_match: md += f"<dd>{related_match_i}</dd>"
        md += "</dl>"

    # Verantwoording
    sources = get_external_links(g, s, DCTERMS.source)
    change_notes = [str(l) for l in g.objects(s, SKOS.changeNote)]
    history_notes = [str(l) for l in g.objects(s, SKOS.historyNote)]
    if sources or change_notes or history_notes:
        md += "\n## Verantwoording\n{: .text-delta }\n\n"
        md += "<dl>"
        if sources:
            md += "<dt>Bron</dt>"
            for source in sources: md += f"<dd>{source}</dd>"
        if change_notes:
            md += "<dt>Wijzigingsnotities</dt>"
            for change_note in change_notes: md += f"<dd>{change_note}</dd>"
        if history_notes:
            md += "<dt>Historie</dt>"
            for history_note in history_notes: md += f"<dd>{history_note}</dd>"
        md += "</dl>"

    # Gebruik (placeholder voor gebruik door client-side JavaScript)
    md += '<div id="concept-usages" class="mt-6"></div>'

    # Opslaan in de root van docs/
    filename = f"{info['slug']}.md"
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(md)

# --- Helper Functies ---

def get_internal_links(g, subject, predicate, concept_map):
    links = []
    for obj in g.objects(subject, predicate):
        uri = str(obj)
        if uri in concept_map:
            lbl = concept_map[uri]['label']
            links.append(f"<a href=\"{BASE_URL}{concept_map[uri]['permalink']}\">{lbl}</a>")
    return links

from rdflib import URIRef, Literal
from rdflib.namespace import SKOS, DCTERMS, RDFS, FOAF

def get_external_links(g, subject, predicate):
    """
    Haalt objecten op via een predicaat en probeert ze slim te formatteren als Markdown link.
    Werkt voor:
    1. Rijke nodes (bv. Documenten met label + foaf:page) -> [Label](Page)
    2. Directe URI's met een bekend label in de graaf -> [Label](URI)
    3. Directe URI's zonder label -> [URI](URI)
    4. Literals (alleen tekst) -> "Tekst"
    """
    items = []
    
    # Loop door alle objecten die bij dit subject en predicaat horen
    for obj in g.objects(subject, predicate):
        
        # Probeer eigenschappen van het object zelf op te halen
        # (Dit werkt alleen als 'obj' ook als subject elders in je graaf staat)
        label = g.value(obj, RDFS.label) or g.value(obj, SKOS.prefLabel) or g.value(obj, DCTERMS.title)
        page = g.value(obj, FOAF.page)
        
        # SCENARIO A: Het is een 'Rijke Node' (zoals jouw Bron-document)
        # Het object is een placeholder, de echte link staat in foaf:page
        if page:
            link_text = str(label) if label else "Link"
            items.append(f'<a href="{str(page)}">{link_text}</a>')
        
        # SCENARIO B: Het is een directe link (zoals skos:exactMatch naar Wikidata)
        elif isinstance(obj, URIRef):
            url = str(obj)
            
            if label:
                # We hebben de URI, én toevallig ook een label in onze graaf
                items.append(f'<a href="{url}">{str(label)}</a>')
            else:
                # Alleen de kale URL. 
                # Tip: Je kunt hier kiezen om de hele URL te tonen, of 'Externe link'
                items.append(f'<a href="{url}">{url}</a>')
        
        # SCENARIO C: Het is gewoon tekst (Literal)
        else:
            items.append(str(obj))
            
    return items

if __name__ == "__main__":
    main()