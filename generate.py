import sys
import os
import glob
import json
import unicodedata
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable, Union

import spacy
from spacy.matcher import Matcher
from slugify import slugify
from jinja2 import Environment, FileSystemLoader
from rdflib import Graph, Namespace, RDF, SKOS, DCTERMS, RDFS, URIRef, FOAF
from rdflib.namespace import split_uri
from pyshacl import validate
from pattern.nl import pluralize, attributive

# ==============================================================================
# 1. OMGEVING & CONFIGURATIE
# ==============================================================================

@dataclass
class ProjectPaths:
    """Centraliseert alle paden die gebruikt worden in het generatieproces."""
    root: str
    templates: str = "templates"
    ttl_source: str = "begrippenkader"
    
    @property
    def output_pages(self) -> str: return os.path.join(self.root, "_doc")
    
    @property
    def output_aliases(self) -> str: return os.path.join(self.root, "alias")
    
    @property
    def output_nav(self) -> str: return os.path.join(self.root, "assets", "json", "alphabetical-nav.json")
    
    @property
    def output_homepage(self) -> str: return os.path.join(self.root, "index.md")
    
    @property
    def output_ttl(self) -> str: return os.path.join(self.root, "begrippenkader.ttl")
    
    @property
    def output_json(self) -> str: return os.path.join(self.root, "begrippen.json")

# Namespaces
NS = {
    "skos": SKOS,
    "dct": DCTERMS,
    "rdfs": RDFS,
    "adms": Namespace("http://www.w3.org/ns/adms#"),
    "iso": Namespace("http://purl.org/iso25964/skos-thes#"),
    "foaf": FOAF
}

TTL_CONFIG = {
    "base": "https://begrippen.netbeheernederland.nl",
    "prefix": "https://begrippen.netbeheernederland.nl/id/",
    "shacl_profile": "https://raw.githubusercontent.com/geonovum/NL-SBB/main/profiles/skos-ap-nl.ttl"
}

# ==============================================================================
# 2. SCHEMA DEFINITIE
# ==============================================================================

class VeldType(Enum):
    TEKST_ENKEL = "extract_single_text"
    TEKST_LIJST = "extract_text_list"
    LINK_INTERN = "extract_internal_links"
    LINK_EXTERN = "extract_external_links"

@dataclass
class VeldDefinitie:
    label: str
    predicaat: URIRef
    type: VeldType
    auto_link: bool = False

# De blauwdruk van een begrippenpagina op basis van NL-SBB
BEGRIPPEN_SCHEMA = {
    # Metadata
    "code":        VeldDefinitie("Code", NS["skos"].notation, VeldType.TEKST_ENKEL),
    "definitie":   VeldDefinitie("Definitie", NS["skos"].definition, VeldType.TEKST_ENKEL, auto_link=True),
    "uitleg":      VeldDefinitie("Uitleg", NS["rdfs"].comment, VeldType.TEKST_LIJST, auto_link=True),
    "toelichting": VeldDefinitie("Toelichting", NS["skos"].scopeNote, VeldType.TEKST_LIJST, auto_link=True),
    "voorbeeld":   VeldDefinitie("Voorbeeld", NS["skos"].example, VeldType.TEKST_LIJST, auto_link=True),
    
    # Termen
    "alternatieve_term": VeldDefinitie("Alternatieve term", NS["skos"].altLabel, VeldType.TEKST_LIJST),
    "zoekterm":          VeldDefinitie("Zoekterm", NS["skos"].hiddenLabel, VeldType.TEKST_LIJST),
    
    # Beheernotities
    "redactionele_notitie": VeldDefinitie("Redactionele notitie", NS["skos"].editorialNote, VeldType.TEKST_LIJST),
    "wijzigingsnotitie":    VeldDefinitie("Wijzigingsnotitie", NS["skos"].changeNote, VeldType.TEKST_LIJST),
    "historie_notitie":     VeldDefinitie("Historie notitie", NS["skos"].historyNote, VeldType.TEKST_LIJST),
    
    # Interne relaties
    "heeft_bovenliggend_begrip": VeldDefinitie("Heeft bovenliggend begrip", NS["skos"].broader, VeldType.LINK_INTERN),
    "heeft_onderliggend_begrip": VeldDefinitie("Heeft onderliggend begrip", NS["skos"].narrower, VeldType.LINK_INTERN),
    "is_gerelateerd_aan":        VeldDefinitie("Is gerelateerd aan", NS["skos"].related, VeldType.LINK_INTERN),
    "is_onderdeel_van":          VeldDefinitie("Is onderdeel van", NS["iso"].broaderPartitive, VeldType.LINK_INTERN),
    "omvat":                     VeldDefinitie("Omvat", NS["iso"].narrowerPartitive, VeldType.LINK_INTERN),
    "is_specialisatie_van":      VeldDefinitie("Is specialisatie van", NS["iso"].broaderGeneric, VeldType.LINK_INTERN),
    "is_generalisatie_van":      VeldDefinitie("Is generalisatie van", NS["iso"].narrowerGeneric, VeldType.LINK_INTERN),
    
    # Externe relaties
    "is_exact_overeenkomstig":           VeldDefinitie("Is exact overeenkomstig", NS["skos"].exactMatch, VeldType.LINK_EXTERN),
    "is_vrijwel_overeenkomstig":         VeldDefinitie("Is vrijwel overeenkomstig", NS["skos"].closeMatch, VeldType.LINK_EXTERN),
    "heeft_overeenkomstig_bovenliggend": VeldDefinitie("Heeft overeenkomstig bovenliggend", NS["skos"].broadMatch, VeldType.LINK_EXTERN),
    "heeft_overeenkomstig_onderliggend": VeldDefinitie("Heeft overeenkomstig onderliggend", NS["skos"].narrowMatch, VeldType.LINK_EXTERN),
    "is_overeenkomstig_verwant":         VeldDefinitie("Is overeenkomstig verwant", NS["skos"].relatedMatch, VeldType.LINK_EXTERN),
    "heeft_bron":                        VeldDefinitie("Heeft bron", NS["dct"].source, VeldType.LINK_EXTERN),
}

# ==============================================================================
# 3. CORE LOGICA
# ==============================================================================

class ContentLinker:
    """Verrijkt tekst door begrippen automatisch om te zetten naar links."""
    
    def __init__(self, lookup_index: Dict[str, dict]):
        try:
            self.nlp = spacy.load("nl_core_news_sm", disable=["ner", "parser", "lemmatizer"])
        except OSError:
            print("FOUT: SpaCy model ontbreekt.")
            sys.exit(1)
            
        self.matcher = Matcher(self.nlp.vocab)
        self.url_map = {}
        self._compile_patterns(lookup_index)

    def _compile_patterns(self, lookup: Dict[str, dict]):
        for _, data in lookup.items():
            term = data['label']
            if not term.strip(): continue

            doc = self.nlp(term)
            pattern = []
            
            for token in doc:
                if not token.text.strip(): continue # Skip lege tokens
                
                # Eenvoudige patroon generatie
                p_opt = {"LOWER": token.text.lower()}
                if token.pos_ == 'NOUN':
                    try:
                        forms = {token.text.lower(), pluralize(token.text).lower()}
                        p_opt = {"LOWER": {"IN": list(forms)}}
                    except: pass
                elif token.pos_ == 'ADJ':
                    try:
                        forms = {token.text.lower(), attributive(token.text).lower()}
                        p_opt = {"LOWER": {"IN": list(forms)}}
                    except: pass
                
                pattern.append(p_opt)

            if pattern:
                self.matcher.add(term, [pattern])
                self.url_map[term] = f"/doc/{data['reference']}"

    def process(self, text: str, current_page_title: str = "") -> str:
        if not text: return text
        
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        # Sorteer: eerst vroegste start, daarna langste match
        matches.sort(key=lambda x: (x[1], -(x[2] - x[1])))
        
        parts = []
        last_idx = 0 # Karakterindex
        
        for match_id, start, end in matches:
            span = doc[start:end]
            
            if span.start_char < last_idx: continue # Overlap
            
            # Checks: lege tekst of zelf-referentie
            if not span.text.strip(): continue
            if span.text.strip().lower() == current_page_title.strip().lower(): continue
            
            term = self.nlp.vocab.strings[match_id]
            url = self.url_map.get(term)
            
            # Voeg tekst voor de match toe
            parts.append(text[last_idx:span.start_char])
            
            # Voeg link toe
            if url:
                parts.append(f'<a href="{{{{ \'{url}\' | relative_url }}}}" class="auto-link">{span.text}</a>')
            else:
                parts.append(span.text)
                
            last_idx = span.end_char
            
        parts.append(text[last_idx:])
        return "".join(parts)

# --- Extractie Strategieën ---
# Deze functies corresponderen 1-op-1 met de VeldTypes.

def extract_single_text(graph: Graph, subject: URIRef, pred: URIRef, **kwargs) -> Optional[str]:
    val = graph.value(subject, pred)
    return str(val) if val else None

def extract_text_list(graph: Graph, subject: URIRef, pred: URIRef, **kwargs) -> List[str]:
    return [str(o) for o in graph.objects(subject, pred)]

def extract_internal_links(graph: Graph, subject: URIRef, pred: URIRef, lookup: dict, **kwargs) -> List[dict]:
    links = []
    for obj in graph.objects(subject, pred):
        uri = str(obj)
        if uri in lookup:
            links.append({
                "url": f"/doc/{lookup[uri]['reference']}",
                "label": lookup[uri]['label']
            })
    return links

def extract_external_links(graph: Graph, subject: URIRef, pred: URIRef, **kwargs) -> List[dict]:
    links = []
    for obj in graph.objects(subject, pred):
        label = graph.value(obj, NS["rdfs"].label) or graph.value(obj, NS["dct"].title) or str(obj)
        url = str(graph.value(obj, NS["foaf"].page)) if graph.value(obj, NS["foaf"].page) else str(obj)
        links.append({"url": url, "label": str(label)})
    return links

# Mapping van VeldType naar de uitvoerende functie
EXTRACTORS = {
    VeldType.TEKST_ENKEL: extract_single_text,
    VeldType.TEKST_LIJST: extract_text_list,
    VeldType.LINK_INTERN: extract_internal_links,
    VeldType.LINK_EXTERN: extract_external_links
}

# ==============================================================================
# 4. DATA PROCESSING
# ==============================================================================

def build_index(graph: Graph) -> Dict[str, dict]:
    """Maakt een lookup tabel van URI naar basisgegevens."""
    index = {}
    for concept in graph.subjects(RDF.type, NS["skos"].Concept):
        if not isinstance(concept, URIRef): continue
        
        uri = str(concept)
        # Robuuste reference extractie (ook bij trailing slashes)
        try:
            ref = split_uri(uri)[1] or uri.strip('/').split('/')[-1]
        except:
            ref = uri.strip('/').split('/')[-1]

        label_val = graph.value(concept, NS["skos"].prefLabel)
        label = str(label_val) if label_val else ref
        
        # FILTER: Sla begrippen zonder tekst over (voorkomt lege matches)
        if not ref or not label or not label.strip():
            continue

        index[uri] = {
            "reference": ref,
            "label": label.strip(),
            "slug": slugify(label)
        }
    return index

def process_concept(graph: Graph, concept: URIRef, lookup: dict, linker: ContentLinker) -> dict:
    """Verzamelt alle data en past autolinking toe."""
    uri = str(concept)
    meta = lookup[uri]
    
    data = {
        "uri": uri,
        "reference": meta["reference"],
        "voorkeursterm": meta["label"],
        "slug": meta["slug"],
        "permalink": f"/doc/{meta['reference']}",
        "status": str(graph.value(concept, NS["adms"].status)).split("/")[-1] if graph.value(concept, NS["adms"].status) else None,
        "mapping": BEGRIPPEN_SCHEMA, # Voor de template
        "parent_label": None
    }

    # Dynamische extractie via de strategy map
    for field_key, config in BEGRIPPEN_SCHEMA.items():
        extractor_func = EXTRACTORS[config.type]
        value = extractor_func(graph, concept, config.predicaat, lookup=lookup)
        
        # Autolink tekstvelden indien nodig
        if config.auto_link and value:
            if isinstance(value, list):
                value = [linker.process(item, meta["label"]) for item in value]
            elif isinstance(value, str):
                value = linker.process(value, meta["label"])
                
        data[field_key] = value

    # Breadcrumb helper
    if data.get("heeft_bovenliggend_begrip"):
        data["parent_label"] = data["heeft_bovenliggend_begrip"][0]["label"]

    return data

def get_normalized_sort_key(text: str) -> str:
    """Zorgt voor correcte A-Z sortering (negeert accenten)."""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

# ==============================================================================
# 5. GENERATOREN
# ==============================================================================

def generate_site(graph: Graph, paths: ProjectPaths):
    env = Environment(loader=FileSystemLoader(paths.templates))
    lookup = build_index(graph)
    linker = ContentLinker(lookup)
    
    # Homepage
    print(f" - Homepage: {paths.output_homepage}")
    scheme = graph.value(None, RDF.type, NS["skos"].ConceptScheme)
    title = str(graph.value(scheme, NS["dct"].title) or "Begrippenkader")
    desc = str(graph.value(scheme, NS["rdfs"].comment) or "")
    
    ensure_dir(paths.output_homepage)
    with open(paths.output_homepage, "w", encoding="utf-8") as f:
        f.write(env.get_template("index.md.jinja2").render(naam=title, uitleg=desc))

    # Begrippenpagina's
    print(f" - Begrippen: {paths.output_pages}")
    template = env.get_template("begrip.md.jinja2")
    ensure_dir(paths.output_pages + "/") # Zorg dat map bestaat
    
    for concept in graph.subjects(RDF.type, NS["skos"].Concept):
        if not isinstance(concept, URIRef): continue
        data = process_concept(graph, concept, lookup, linker)
        
        with open(os.path.join(paths.output_pages, f"{data['reference']}.md"), "w", encoding="utf-8") as f:
            f.write(template.render(data))

    # Aliassen (redirects)
    print(f" - Aliassen: {paths.output_aliases}")
    template = env.get_template("alias.md.jinja2")
    ensure_dir(paths.output_aliases + "/")
    
    for concept in graph.subjects(RDF.type, NS["skos"].Concept):
        uri = str(concept)
        if uri not in lookup: continue
        
        target = lookup[uri]
        for alias in graph.objects(concept, NS["skos"].altLabel):
            slug = f"{slugify(str(alias))}-{target['reference']}"
            with open(os.path.join(paths.output_aliases, f"{slug}.md"), "w", encoding="utf-8") as f:
                f.write(template.render(alias_term=str(alias), target_label=target['label'], target_url=f"/doc/{target['reference']}"))

    # JSON alfabetische nav
    print(f" - Index: {paths.output_nav}")
    index_items = []
    for uri, data in lookup.items():
        url = f"/doc/{data['reference']}"
        # Voorkeursterm
        index_items.append({"title": data['label'], "url": url, "type": "concept", "sort": get_normalized_sort_key(data['label'])})
        # Alternatieve termen
        for alias in graph.objects(URIRef(uri), NS["skos"].altLabel):
            index_items.append({"title": str(alias), "url": url, "type": "alias", "target_label": data['label'], "sort": get_normalized_sort_key(str(alias))})
    
    index_items.sort(key=lambda x: x.pop('sort')) # Sorteer en verwijder direct de sort key
    ensure_dir(paths.output_nav)
    with open(paths.output_nav, "w", encoding="utf-8") as f:
        json.dump(index_items, f, separators=(',', ':'))

    # Downloadable TTL
    print(" - Exports (TTL/JSON)")
    graph.bind("", Namespace(TTL_CONFIG["prefix"]))
    for prefix, ns in NS.items(): graph.bind(prefix, ns)
    graph.serialize(destination=paths.output_ttl, format="turtle", base=TTL_CONFIG["base"])

    # Downloadable lookup JSON
    lookup_export = {uri.replace(TTL_CONFIG["prefix"], ""): {"label": data["label"], "uri": uri} for uri, data in lookup.items()}
    with open(paths.output_json, "w", encoding="utf-8") as f:
        json.dump(lookup_export, f, indent=2)

# ==============================================================================
# 6. MAIN EXECUTION
# ==============================================================================

def main():
    print("=== Start Generator ===")
    
    # Setup
    paths = ProjectPaths(root=sys.argv[1] if len(sys.argv) > 1 else "docs")
    graph = Graph()
    
    # Load
    files = glob.glob(os.path.join(paths.ttl_source, "*.ttl"))
    if not files:
        print(f"Geen data gevonden in {paths.ttl_source}"); return
    for f in files: graph.parse(f, format="turtle")
    print(f"{len(graph)} triples ingeladen.")

    # Validate
    valid, _, report = validate(graph, shacl_graph=TTL_CONFIG["shacl_profile"], inference='rdfs')
    if not valid:
        print("!!! SHACL-validatiefout !!!\n", report)
        sys.exit(1)
    print("SHACL-validatie geslaagd.")

    # Generate
    generate_site(graph, paths)
    print("=== Klaar! ===")

if __name__ == "__main__":
    main()
