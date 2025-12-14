import os
import glob
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from slugify import slugify
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

# --- CONFIGURATIE ---
INPUT_DIR = "begrippenkaders"
DOCS_ROOT = "docs"
BEGRIPPEN_DIR = os.path.join(DOCS_ROOT, "_doc") # Jekyll collectie map
ALIAS_DIR = os.path.join(DOCS_ROOT, "alias")
TEMPLATE_DIR = "templates"
BASE_URL = "/energiesysteembeheer" # Voor absolute links in HTML (indien nodig)

ADMS = Namespace("http://www.w3.org/ns/adms#")
ISO_THES = Namespace("http://purl.org/iso25964/skos-thes#")

NL_SBB_MAPPING = {
    "code": {"label": "Code", "pred": SKOS.notation, "type": "single"},
    "definitie": {"label": "Definitie", "pred": SKOS.definition, "type": "single"},
    "uitleg": {"label": "Uitleg", "pred": RDFS.comment, "type": "list"},
    "toelichting": {"label": "Toelichting", "pred": SKOS.scopeNote, "type": "list"},
    "voorbeeld": {"label": "Voorbeeld", "pred": SKOS.example, "type": "list"},
    "alternatieve_term": {"label": "Alternatieve term", "pred": SKOS.altLabel, "type": "list"},
    "zoekterm": {"label": "Zoekterm", "pred": SKOS.hiddenLabel, "type": "list"},
    "redactionele_notitie": {"label": "Redactionele notitie", "pred": SKOS.editorialNote, "type": "list"},
    "wijzigingsnotitie": {"label": "Wijzigingsnotitie", "pred": SKOS.changeNote, "type": "list"},
    "historie_notitie": {"label": "Historie notitie", "pred": SKOS.historyNote, "type": "list"},
    "heeft_bovenliggend_begrip": {"label": "Heeft bovenliggend begrip", "pred": SKOS.broader, "type": "internal"},
    "heeft_onderliggend_begrip": {"label": "Heeft onderliggend begrip", "pred": SKOS.narrower, "type": "internal"},
    "is_gerelateerd_aan": {"label": "Is gerelateerd aan", "pred": SKOS.related, "type": "internal"},
    "is_onderdeel_van": {"label": "Is onderdeel van", "pred": ISO_THES.broaderPartitive, "type": "internal"},
    "omvat": {"label": "Omvat", "pred": ISO_THES.narrowerPartitive, "type": "internal"},
    "is_specialisatie_van": {"label": "Is specialisatie van", "pred": ISO_THES.broaderGeneric, "type": "internal"},
    "is_generalisatie_van": {"label": "Is generalisatie van", "pred": ISO_THES.narrowerGeneric, "type": "internal"},
    "is_exemplaar_van": {"label": "Is exemplaar van", "pred": ISO_THES.broaderInstantial, "type": "internal"},
    "is_categorie_van": {"label": "Is categorie van", "pred": ISO_THES.narrowerInstantial, "type": "internal"},
    "is_exact_overeenkomstig": {"label": "Is exact overeenkomstig", "pred": SKOS.exactMatch, "type": "external"},
    "is_vrijwel_overeenkomstig": {"label": "Is vrijwel overeenkomstig", "pred": SKOS.closeMatch, "type": "external"},
    "heeft_overeenkomstig_bovenliggend": {"label": "Heeft overeenkomstig bovenliggend", "pred": SKOS.broadMatch, "type": "external"},
    "heeft_overeenkomstig_onderliggend": {"label": "Heeft overeenkomstig onderliggend", "pred": SKOS.narrowMatch, "type": "external"},
    "is_overeenkomstig_verwant": {"label": "Is overeenkomstig verwant", "pred": SKOS.relatedMatch, "type": "external"},
    "bron": {"label": "Bron", "pred": DCTERMS.source, "type": "external"},
}

def main():
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("begrip.md.j2")
    
    print("Begrippenkader laden...")
    g = Graph()
    for file_path in glob.glob(os.path.join(INPUT_DIR, "*.ttl")):
        g.parse(file_path, format="turtle")

    generate_homepage(g, env, os.path.join(DOCS_ROOT, "index.md"))

    lookup = build_lookup(g)
    
    if not os.path.exists(BEGRIPPEN_DIR):
        os.makedirs(BEGRIPPEN_DIR)

    count = 0
    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        data = extract_data(g, s, lookup)
        output = template.render(data)

        filename = f"{data['id']}.md"
        with open(os.path.join(BEGRIPPEN_DIR, filename), "w", encoding="utf-8") as f:
            f.write(output)
        count += 1

    generate_aliases(g, env, lookup, ALIAS_DIR)

    generate_list(g, env, lookup, os.path.join(DOCS_ROOT, "lijst.md"))

    print(f"Gereed. {count} begrippen verwerkt.")

def get_local_id(uri_str):
    if "#" in uri_str:
        return uri_str.split("#")[-1]
    return uri_str.rstrip("/").split("/")[-1]

def build_lookup(g):
    lookup = {}
    for s in g.subjects(RDF.type, SKOS.Concept):
        if isinstance(s, URIRef):
            local_id = get_local_id(str(s))
            label_val = g.value(s, SKOS.prefLabel)
            label_str = str(label_val) if label_val else local_id
            slug = slugify(label_str)

            lookup[str(s)] = {
                "id": local_id, 
                "label": label_str,
                "slug": slug
            }
    return lookup

def extract_data(g, s, lookup):
    uri = str(s)
    local_id = get_local_id(uri)
    pref_label = str(g.value(s, SKOS.prefLabel) or local_id)
    slug = lookup.get(uri, {}).get("slug", slugify(pref_label))
    
    data = {
        "uri": uri,
        "id": local_id,
        "voorkeursterm": pref_label,
        "slug": slug, 
        "permalink": f"/doc/{local_id}", 
        "status": get_status(g, s),
        "mapping": NL_SBB_MAPPING, 
        "parent_label": None
    }

    # Dynamische extractie
    for var_name, config in NL_SBB_MAPPING.items():
        predicate = config["pred"]
        extract_type = config["type"]
        
        if extract_type == "single":
            val = g.value(s, predicate)
            data[var_name] = str(val) if val else None
            
        elif extract_type == "list":
            data[var_name] = [str(o) for o in g.objects(s, predicate)]
            
        elif extract_type == "internal":
            links = []
            for obj in g.objects(s, predicate):
                obj_uri = str(obj)
                if obj_uri in lookup:
                    target_id = lookup[obj_uri]['id']
                    links.append({
                        "url": f"{BASE_URL}/doc/{target_id}",
                        "label": lookup[obj_uri]['label']
                    })
            data[var_name] = links
            
        elif extract_type == "external":
            links = []
            for obj in g.objects(s, predicate):
                lbl = g.value(obj, RDFS.label) or g.value(obj, DCTERMS.title) or str(obj)
                url = str(g.value(obj, FOAF.page)) if g.value(obj, FOAF.page) else str(obj)
                links.append({"url": url, "label": str(lbl)})
            data[var_name] = links

    if data["heeft_bovenliggend_begrip"]:
        data["parent_label"] = data["heeft_bovenliggend_begrip"][0]["label"]

    return data

def get_status(g, s):
    status_uri = g.value(s, ADMS.status)
    return str(status_uri).split("/")[-1] if status_uri else None

def generate_homepage(g, env, output_path):
    print("Homepage genereren...")
    template = env.get_template("index.md.j2")
    scheme = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
    
    # Default waardes
    title = "Begrippenkader"
    description = "Welkom bij het begrippenkader."

    # Metadata ophalen als er een scheme is
    if scheme:
        val_title = g.value(scheme, DCTERMS.title)
        if val_title: 
            title = str(val_title)

        val_desc = g.value(scheme, RDFS.comment)
        if val_desc: 
            description = str(val_desc)

    output = template.render(title=title, description=description)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

def generate_aliases(g, env, lookup, output_dir):
    print("Aliassen genereren...")
    
    template = env.get_template("alias.md.j2")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    count = 0
    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        
        uri = str(s)
        if uri not in lookup: continue

        # Haal data van het DOEL (waar we naar moeten redirecten)
        target_id = lookup[uri]['id']
        target_label = lookup[uri]['label']
        # De URL waar we de bezoeker heen sturen
        target_url = f"/doc/{target_id}" 

        # Verzamel alle aliassen voor DIT begrip
        aliases = []
        aliases.extend([str(l) for l in g.objects(s, SKOS.altLabel)])
        aliases.extend([str(l) for l in g.objects(s, SKOS.hiddenLabel)])

        for alias in aliases:
            alias_slug = slugify(alias)
            
            # UNIEK MAKEN: We plakken de ID aan de slug
            # Bestand:  docs/_term/fiets-mer53.md
            # URL:      /term/fiets-mer53
            unique_slug = f"{alias_slug}-{target_id}"
            
            output = template.render(
                alias_term=alias,
                target_label=target_label,
                target_url=target_url
            )
            
            filename = f"{unique_slug}.md"
            with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                f.write(output)
            count += 1

    print(f"Klaar! {count} alias-redirects gegenereerd.")

from collections import defaultdict

def generate_list(g, env, lookup, output_path):
    print("Begrippenlijst A-Z genereren...")
    template = env.get_template("lijst.md.j2")
    
    # Lijst om alles te verzamelen
    # Item format: { "sort_key": "...", "label": "...", "url": "...", "type": "main/alias", "target_label": "..." }
    all_items = []

    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        uri = str(s)
        if uri not in lookup: continue
        
        # Voeg Voorkeursterm toe
        pref_label = lookup[uri]['label']
        target_id = lookup[uri]['id']
        url = f"/doc/{target_id}" # Korte URL, Jekyll fixt de baseurl
        
        all_items.append({
            "sort_key": slugify(pref_label), # Voor sorteren
            "label": pref_label,
            "url": url,
            "type": "main"
        })

        # Voeg Aliassen toe (altLabel)
        aliases = [str(l) for l in g.objects(s, SKOS.altLabel)]
        
        for alias in aliases:
            all_items.append({
                "sort_key": slugify(alias),
                "label": alias,
                "url": url, # Linkt direct naar het hoofdbegrip
                "type": "alias",
                "target_label": pref_label
            })

    # Sorteren op alfabet
    all_items.sort(key=lambda x: x['sort_key'])

    # Groeperen op eerste letter
    grouped_items = defaultdict(list)
    for item in all_items:
        # Pak eerste letter, forceer hoofdletter. Negeer symbolen (stop in '#')
        first_char = item['label'][0].upper()
        if not first_char.isalpha():
            first_char = '#'
        grouped_items[first_char].append(item)

    # Zorg dat de letters gesorteerd zijn voor de navigatie
    sorted_letters = sorted(grouped_items.keys())
    if '#' in sorted_letters: # '#' achteraan zetten
        sorted_letters.remove('#')
        sorted_letters.append('#')

    # Renderen
    output = template.render(
        letters=sorted_letters,
        grouped_items=grouped_items
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

if __name__ == "__main__":
    main()
