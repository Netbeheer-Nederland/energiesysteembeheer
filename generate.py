import os, glob, json, unicodedata, spacy
from slugify import slugify
from jinja2 import Environment, FileSystemLoader
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from pyshacl import validate
from spacy.matcher import PhraseMatcher
from pattern.nl import pluralize, attributive

try:
    nlp = spacy.load("nl_core_news_sm")
    print("SpaCy Nederlands model geladen.")
except OSError:
    print("FOUT: SpaCy Nederlands model niet gevonden. Draai: python -m spacy download nl_core_news_sm")
    exit(1)

# ==============================================================================
# CONFIGURATIE & PADEN
# ==============================================================================

# Paden (relatief aan scriptlocatie)
INPUT_DIR = "begrippenkader"
DOCS_ROOT = "docs"
TEMPLATE_DIR = "templates"

# Output-locaties
BEGRIPPEN_DIR = os.path.join(DOCS_ROOT, "_doc")  # Jekyll Collectie
ALIAS_DIR = os.path.join(DOCS_ROOT, "alias")     # Redirects
LIST_FILE = os.path.join(DOCS_ROOT, "lijst.md")  # A-Z Index
INDEX_FILE = os.path.join(DOCS_ROOT, "index.md") # Homepage
TTL_OUTPUT_FILE = os.path.join(DOCS_ROOT, "begrippenkader.ttl")
BEGRIPPENLIJST_FILE = os.path.join(DOCS_ROOT, "assets", "begrippenlijst.json")

# URL-instellingen
# Let op: BASE_URL wordt hier gebruikt voor absolute links in gegenereerde lijsten.
# Voor interne navigatie vertrouwen we op `baseurl` in Jekyll's `_config.yml`.
BASE_URL = "/energiesysteembeheer"
PUBLISH_BASE_URI = "https://begrippen.netbeheernederland.nl" # komt overeen met @base in TTL
CONCEPT_NAMESPACE = "https://begrippen.netbeheernederland.nl/id/" # komt overeen met @prefix : in TTL

# Validatie instellingen
# URL naar het SHACL profiel van NL-SBB (Geonovum)
NL_SBB_SHACL_URL = "https://raw.githubusercontent.com/geonovum/NL-SBB/main/profiles/skos-ap-nl.ttl"

# RDF Namespaces
ADMS = Namespace("http://www.w3.org/ns/adms#")
ISO_THES = Namespace("http://purl.org/iso25964/skos-thes#")

# ==============================================================================
# DATA MAPPING (RDF -> NL-SBB)
# ==============================================================================
# Deze configuratie bepaalt welke RDF-eigenschappen worden opgehaald en hoe ze
# worden genoemd in de templates. Dit volgt de NL-SBB standaard.

NL_SBB_MAPPING = {
    # --- Labels & beschrijvingen ---
    "code":                 {"label": "Code", "pred": SKOS.notation, "type": "single"},
    "definitie":            {"label": "Definitie", "pred": SKOS.definition, "type": "single"},
    "uitleg":               {"label": "Uitleg", "pred": RDFS.comment, "type": "list"},
    "toelichting":          {"label": "Toelichting", "pred": SKOS.scopeNote, "type": "list"},
    "voorbeeld":            {"label": "Voorbeeld", "pred": SKOS.example, "type": "list"},
    "alternatieve_term":    {"label": "Alternatieve term", "pred": SKOS.altLabel, "type": "list"},
    "zoekterm":             {"label": "Zoekterm", "pred": SKOS.hiddenLabel, "type": "list"},
    
    # --- Notities ---
    "redactionele_notitie": {"label": "Redactionele notitie", "pred": SKOS.editorialNote, "type": "list"},
    "wijzigingsnotitie":    {"label": "Wijzigingsnotitie", "pred": SKOS.changeNote, "type": "list"},
    "historie_notitie":     {"label": "Historie notitie", "pred": SKOS.historyNote, "type": "list"},
    
    # --- Interne relaties (links naar andere begrippen) ---
    "heeft_bovenliggend_begrip": {"label": "Heeft bovenliggend begrip", "pred": SKOS.broader, "type": "internal"},
    "heeft_onderliggend_begrip": {"label": "Heeft onderliggend begrip", "pred": SKOS.narrower, "type": "internal"},
    "is_gerelateerd_aan":        {"label": "Is gerelateerd aan", "pred": SKOS.related, "type": "internal"},
    
    # --- ISO thesaurus relaties (specifieke hiërarchie) ---
    "is_onderdeel_van":     {"label": "Is onderdeel van", "pred": ISO_THES.broaderPartitive, "type": "internal"},
    "omvat":                {"label": "Omvat", "pred": ISO_THES.narrowerPartitive, "type": "internal"},
    "is_specialisatie_van": {"label": "Is specialisatie van", "pred": ISO_THES.broaderGeneric, "type": "internal"},
    "is_generalisatie_van": {"label": "Is generalisatie van", "pred": ISO_THES.narrowerGeneric, "type": "internal"},
    "is_exemplaar_van":     {"label": "Is exemplaar van", "pred": ISO_THES.broaderInstantial, "type": "internal"},
    "is_categorie_van":     {"label": "Is categorie van", "pred": ISO_THES.narrowerInstantial, "type": "internal"},
    
    # --- Externe relaties (harmonisatie & bronnen) ---
    "is_exact_overeenkomstig":           {"label": "Is exact overeenkomstig", "pred": SKOS.exactMatch, "type": "external"},
    "is_vrijwel_overeenkomstig":         {"label": "Is vrijwel overeenkomstig", "pred": SKOS.closeMatch, "type": "external"},
    "heeft_overeenkomstig_bovenliggend": {"label": "Heeft overeenkomstig bovenliggend", "pred": SKOS.broadMatch, "type": "external"},
    "heeft_overeenkomstig_onderliggend": {"label": "Heeft overeenkomstig onderliggend", "pred": SKOS.narrowMatch, "type": "external"},
    "is_overeenkomstig_verwant":         {"label": "Is overeenkomstig verwant", "pred": SKOS.relatedMatch, "type": "external"},
    "heeft_bron":                        {"label": "Heeft bron", "pred": DCTERMS.source, "type": "external"},
}

# ==============================================================================
# HULPFUNCTIES (UTILS)
# ==============================================================================

def get_reference(uri_str):
    """
    Haalt de 'referentie' uit de URI conform NL URI-Strategie.
    """
    return uri_str.rstrip("/").split("/")[-1]

def get_status(g, s):
    """Haalt de ADMS status op van een concept (bijv. 'valid', 'deprecated')."""
    status_uri = g.value(s, ADMS.status)
    return str(status_uri).split("/")[-1] if status_uri else None

def ensure_directory(path):
    """Maakt een map aan als deze nog niet bestaat."""
    if not os.path.exists(path):
        os.makedirs(path)

def normalize_for_sort(text):
    """Zorgt voor A-Z sortering zonder last te hebben van accenten (é -> e)."""
    if not text: return ""
    text = text.lower()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def build_matcher_and_url_map(lookup, base_url):
    matcher = PhraseMatcher(nlp.vocab)
    url_map = {}

    for _, data in lookup.items():
        term = data['label']
        url = f"{base_url}/doc/{data['reference']}"
        
        doc = nlp(term)
        pattern = []

        for token in doc:
            base_word = token.text.lower()
            
            if token.pos_ == 'NOUN': # Strategie voor zelfstandige naamwoorden
                singular = token.text
                plural = pluralize(singular)
                pattern.append({"LOWER": {"IN": [singular.lower(), plural.lower()]}}) 

            elif token.pos_ == 'ADJ': # Strategie voor bijvoeglijke naamwoorden
                predicative_form = base_word
                attributive_form = attributive(predicative_form)
                forms = {
                    predicative_form.lower(), 
                    attributive_form.lower()
                }
                pattern.append({"LOWER": {"IN": list(forms)}})
                
            else: # Fallback
                 pattern.append({"LOWER": token.text.lower()})

        match_id = term
        matcher.add(match_id, [pattern])
        url_map[match_id] = url
        
    return matcher, url_map

def autolink_text(text, matcher, url_map, current_page_title=""):
    """
    Vervangt termen in een tekst met links via de spaCy PhraseMatcher.
    """
    if not text or not matcher:
        return text

    doc = nlp(text)
    matches = matcher(doc)

    valid_matches = [] # We bouwen een lijst met matches die we willen behouden
    for match_id_hash, start, end in matches:
        span = doc[start:end]
        if span.text.lower() != current_page_title.lower(): # De match_id is een integer hash. We vertalen hem terug naar de originele string.
            original_term_key = nlp.vocab.strings[match_id_hash]
            valid_matches.append((original_term_key, start, end))

    if not valid_matches:
        return text

    # Bouw de nieuwe tekst op om index-conflicten te voorkomen
    new_text_parts = []
    last_index = 0

    # Sorteer matches op start-positie om overlap te voorkomen
    # (dit is een extra veiligheidsmaatregel)
    valid_matches.sort(key=lambda x: x[1])

    for original_term_key, start, end in valid_matches:
        # Voorkom dat matches binnen andere matches worden gelinkt
        if doc[start].idx < last_index:
            continue

        new_text_parts.append(text[last_index:doc[start].idx])
        
        original_phrase = doc[start:end].text
        url = url_map[original_term_key]
        tooltip = "Automatisch herkend begrip"
        link = f'<a href="{url}" class="auto-link" title="{tooltip}">{original_phrase}</a>'
        new_text_parts.append(link)
        
        last_index = doc[end-1].idx + len(doc[end-1].text)
        
    new_text_parts.append(text[last_index:])
    
    return "".join(new_text_parts)

# ==============================================================================
# DATA-EXTRACTIE (ETL-LAAG)
# ==============================================================================

def build_lookup(g):
    """
    Bouwt een index van alle begrippen in de graaf.
    Output: { "URI_STRING": { "reference": "...", "label": "...", "slug": "..." } }
    """
    lookup = {}
    for s in g.subjects(RDF.type, SKOS.Concept):
        if isinstance(s, URIRef):
            ref = get_reference(str(s))
            label_val = g.value(s, SKOS.prefLabel)
            label_str = str(label_val) if label_val else ref
            slug = slugify(label_str)

            lookup[str(s)] = {
                "reference": ref,
                "label": label_str,
                "slug": slug
            }
    return lookup

def extract_concept_data(g, s, lookup, matcher, url_map):
    """
    Verzamelt alle data voor één begrip op basis van de NL_SBB_MAPPING.
    Geeft een schone dictionary terug voor de Template.
    """
    uri = str(s)
    ref = get_reference(uri)
    pref_label = str(g.value(s, SKOS.prefLabel) or ref)
    slug = lookup.get(uri, {}).get("slug", slugify(pref_label))
    
    data = { # Basis Metadata
        "uri": uri,
        "reference": ref,
        "voorkeursterm": pref_label,
        "slug": slug, 
        "permalink": f"/doc/{ref}", 
        "status": get_status(g, s),
        "mapping": NL_SBB_MAPPING, # Config doorgeven aan template voor labels
        "parent_label": None
    }

    fields_to_link = ["definitie", "uitleg", "toelichting", "voorbeeld"] # Velden die we willen auto-linken

    # Dynamische extractie o.b.v. config
    for var_name, config in NL_SBB_MAPPING.items():
        predicate = config["pred"]
        extract_type = config["type"]
        
        # Type 1: enkele tekstwaarde (bijv. Definitie)
        if extract_type == "single":
            val = g.value(s, predicate)
            data[var_name] = str(val) if val else None
            
        # Type 2: lijst van teksten (bijv. Uitleg)
        elif extract_type == "list":
            data[var_name] = [str(o) for o in g.objects(s, predicate)]
            
        # Type 3: interne links (naar andere begrippen binnen dit stelsel)
        elif extract_type == "internal":
            links = []
            for obj in g.objects(s, predicate):
                obj_uri = str(obj)
                if obj_uri in lookup:
                    target_reference = lookup[obj_uri]['reference']
                    links.append({
                        "url": f"{BASE_URL}/doc/{target_reference}",
                        "label": lookup[obj_uri]['label']
                    })
            data[var_name] = links
            
        # Type 4: externe links (naar bronnen of harmonisatie buiten dit stelsel)
        elif extract_type == "external":
            links = []
            for obj in g.objects(s, predicate):
                # Probeer een mooi label te vinden, anders fallback naar URL
                lbl = g.value(obj, RDFS.label) or g.value(obj, DCTERMS.title) or str(obj)
                # Zoek de URL (foaf:page) of gebruik de URI zelf
                url = str(g.value(obj, FOAF.page)) if g.value(obj, FOAF.page) else str(obj)
                links.append({"url": url, "label": str(lbl)})
            data[var_name] = links

        # Auto linking
        current_title = data.get("voorkeursterm", "")
        if var_name in fields_to_link:
            if config["type"] == "single" and data.get(var_name):
                data[var_name] = autolink_text(data[var_name], matcher, url_map, current_title)
            elif config["type"] == "list" and data.get(var_name):
                data[var_name] = [autolink_text(item, matcher, url_map, current_title) for item in data[var_name]]

    # Speciale logica: parent bepalen voor kruimelpad (breadcrumbs)
    if data["heeft_bovenliggend_begrip"]:
        data["parent_label"] = data["heeft_bovenliggend_begrip"][0]["label"]

    return data

# ==============================================================================
# GENERATOREN (BESTANDEN SCHRIJVEN)
# ==============================================================================

def generate_homepage(g, env):
    print(" - Homepage genereren...")
    template = env.get_template("index.md.j2")
    
    scheme = g.value(predicate=RDF.type, object=SKOS.ConceptScheme)
    title = "Begrippenkader"
    description = "Welkom bij het begrippenkader."

    if scheme:
        val_title = g.value(scheme, DCTERMS.title)
        if val_title: title = str(val_title)
        val_desc = g.value(scheme, RDFS.comment)
        if val_desc: description = str(val_desc)

    output = template.render(title=title, description=description)
    
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(output)

def generate_downloadable_ttl(g):
    """
    Schrijft de volledige graph weg als één genormaliseerd Turtle-bestand.
    """
    print(f" - Downloadbare TTL genereren in {TTL_OUTPUT_FILE}...")
    
    # Bind de lege prefix (:) aan de juiste namespace
    g.bind("", Namespace(CONCEPT_NAMESPACE))
    # Bind andere veelgebruikte prefixes
    g.bind("skos", SKOS)
    g.bind("dct", DCTERMS)
    g.bind("adms", ADMS)

    try:
        g.serialize(destination=TTL_OUTPUT_FILE, format="turtle", base=PUBLISH_BASE_URI)
    except Exception as e:
        print("FOUT: Kon TTL bestand niet wegschrijven.")
        raise(e)

def generate_concepts(g, env, lookup, matcher, url_map):
    print(f" - Begrippen genereren in {BEGRIPPEN_DIR}...")
    template = env.get_template("begrip.md.j2")
    ensure_directory(BEGRIPPEN_DIR)

    count = 0
    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        
        data = extract_concept_data(g, s, lookup, matcher, url_map)
        output = template.render(data)

        filename = f"{data['reference']}.md"
        with open(os.path.join(BEGRIPPEN_DIR, filename), "w", encoding="utf-8") as f:
            f.write(output)
        count += 1
    return count

def generate_aliases(g, env, lookup):
    print(f" - Aliassen genereren in {ALIAS_DIR}...")
    template = env.get_template("alias.md.j2")
    ensure_directory(ALIAS_DIR)

    count = 0
    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        uri = str(s)
        if uri not in lookup: continue

        # Doelwit van de redirect
        target_ref = lookup[uri]['reference']
        target_label = lookup[uri]['label']
        
        # Verzamel aliassen (altLabel & hiddenLabel)
        aliases = [str(l) for l in g.objects(s, SKOS.altLabel)]

        for alias in aliases:
            # Maak een unieke slug: term + target_id (om dubbele termen op te lossen)
            alias_slug = slugify(alias)
            unique_slug = f"{alias_slug}-{target_ref}"
            
            output = template.render(
                alias_term=alias,
                target_label=target_label,
                target_url=f"/doc/{target_ref}" # korte URL voor redirect plugin
            )
            
            filename = f"{unique_slug}.md"
            with open(os.path.join(ALIAS_DIR, filename), "w", encoding="utf-8") as f:
                f.write(output)
            count += 1
    return count

def generate_json_index(g, lookup):
    print(f" - JSON Index genereren in {BEGRIPPENLIJST_FILE}...")
    ensure_directory(os.path.dirname(BEGRIPPENLIJST_FILE))
    
    index_items = []

    for s in g.subjects(RDF.type, SKOS.Concept):
        if not isinstance(s, URIRef): continue
        uri = str(s)
        if uri not in lookup: continue
        
        data = lookup[uri]
        target_url = f"{BASE_URL}/doc/{data['reference']}"
        
        # Hoofdbegrip
        index_items.append({
            "title": data['label'],
            "url": target_url,
            "type": "concept",
            "sort_key": normalize_for_sort(data['label'])
        })

        # Aliassen
        aliases = [str(l) for l in g.objects(s, SKOS.altLabel)]
        for alias in aliases:
            index_items.append({
                "title": alias,
                "url": target_url, # Verwijs direct naar het hoofdbegrip
                "type": "alias",
                "target_label": data['label'],
                "sort_key": normalize_for_sort(alias)
            })

    index_items.sort(key=lambda x: x['sort_key']) # Sorteren op de genormaliseerde sleutel
    
    for item in index_items:
        del item['sort_key'] # Sleutel verwijderen voor opslaan (bespaart bytes)

    with open(BEGRIPPENLIJST_FILE, "w", encoding="utf-8") as f:
        json.dump(index_items, f, separators=(',', ':')) # Minified JSON

# ==============================================================================
# MAIN EXECUTION FLOW
# ==============================================================================

def main():
    print("=== Start sitegeneratie ===")
    
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    print("RDF-data inlezen...")
    g = Graph()
    ttl_files = glob.glob(os.path.join(INPUT_DIR, "*.ttl"))
    if not ttl_files:
        print(f"FOUT: Geen .ttl bestanden gevonden in {INPUT_DIR}")
        return
    for file_path in ttl_files:
        g.parse(file_path, format="turtle")
    
    print("SHACL-validatie uitvoeren...")
    conforms, _, v_text = validate(
        g,
        shacl_graph=NL_SBB_SHACL_URL,
        inference='rdfs',
        abort_on_first=False,
        meta_shacl=False,
        advanced=True
    )
    if not conforms:
        print("!!! SHACL VALIDATIE NIET GESLAAGD !!!")
        print(v_text)
        exit(1) # Stop het script met een error code
    else:
        print("SHACL Validatie geslaagd.")

    print("TTL genereren...")
    generate_downloadable_ttl(g)

    print("Index opbouwen...")
    lookup = build_lookup(g)
    matcher, url_map = build_matcher_and_url_map(lookup, BASE_URL)

    print("Bestanden genereren...")
    generate_homepage(g, env)
    
    n_concepts = generate_concepts(g, env, lookup, matcher, url_map)
    print(f"   -> {n_concepts} begrippenpagina's aangemaakt.")
    
    n_aliases = generate_aliases(g, env, lookup)
    print(f"   -> {n_aliases} redirects aangemaakt.")
    
    generate_json_index(g, lookup)
    print("   -> Begrippenlijst aangemaakt.")

    print("=== Klaar! ===")

if __name__ == "__main__":
    main()
