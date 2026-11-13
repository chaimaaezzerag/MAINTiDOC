"""Règles indépendantes : l'identité d'une pièce n'est pas une simple cooccurrence.

Acceptation automatique limitée aux citations extractives et à quelques
paraphrases techniques explicitement reconnues. Les autres phrases nécessitent
une preuve supplémentaire et restent insuffisantes, même si le VLM les approuve.
"""
import re
import unicodedata

TERMS = {
    "vis": r"vis|screws?", "ecrou": r"ecrous?|nuts?",
    "boulon": r"boulons?|bolts?", "joint": r"joints?|sealings?|seals?|gaskets?",
}
TERM_PATTERN = "|".join(f"(?:{pattern})" for pattern in TERMS.values())

def normalized(text):
    text = unicodedata.normalize("NFKD", text.casefold())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text.replace("’", "'")).strip()

def kind(term):
    return next((name for name, pattern in TERMS.items() if re.fullmatch(pattern, term)), None)

def source_bindings(text):
    """Associer seulement un terme immédiatement attaché au repère imprimé."""
    text = normalized(text)
    result = {}
    for match in re.finditer(r"\b(" + TERM_PATTERN + r")\s*\((\d{2,5})\)", text):
        result.setdefault(match[2], set()).add(kind(match[1]))
    return result

def independent_verdict(claim, quote):
    """Retourner verdict/motif fondés sur l'extrait réellement cité."""
    c, q = normalized(claim), normalized(quote)
    if not q:
        return "insufficient", "Extrait justificatif absent"
    # Une citation mot à mot ne traduit ni ne reformule son contenu.
    clean = lambda value: value.strip(' .:;!?«»"')
    if clean(c) == clean(q):
        return "supported", "Citation extractive exacte, sans ajout"
    for prefix in ("le manuel indique :", "le document indique :", "extrait du manuel :"):
        if c.startswith(prefix) and clean(c[len(prefix):]) == clean(q):
            return "supported", "Citation extractive explicitement attribuée"
    bindings = source_bindings(q)
    claimed_ids = re.findall(r"(?<!\d)\d{2,5}(?!\d)", c)
    claimed_kinds = {kind(m[0]) for m in re.finditer(r"\b(?:" + TERM_PATTERN + r")\b", c)}
    if len(set(claimed_ids)) == 1 and len(claimed_kinds) == 1:
        part = claimed_ids[0]
        noun = next(iter(claimed_kinds))
        if part in bindings and len(bindings[part]) > 1:
            return "contradicted", f"Associations incompatibles pour le repère {part} dans l'extrait"
        if part in bindings and noun not in bindings[part]:
            return "contradicted", f"Le terme attribué au repère {part} contredit son association dans l'extrait"
        if part not in bindings:
            return "insufficient", f"Aucune association explicite terme-repère {part} dans cet extrait"
        if re.search(r"\b(?:pas|jamais|aucun|aucune|absent|sans)\b|n'", c):
            return "contradicted", "Négation d'une identité explicitement donnée dans l'extrait"
        term = r"(?:" + TERM_PATTERN + r")"
        part_pattern = re.escape(part)
        # Le reste de la phrase doit être une simple identification, pas une
        # propriété, un matériau, un couple ou une instruction ajoutée.
        identity = [
            r"(?:le )?repere " + part_pattern + r" (?:designe|correspond a|est|identifie) (?:un |une |des |les |le |la |aux |au )?" + term + r"(?: d'etancheite)?[.!]?",
            r"(?:le |la |les |un |une |des )?" + term + r"(?: d'etancheite)? (?:porte|portent|a|ont) (?:le )?repere " + part_pattern + r"[.!]?",
        ]
        flat = c.replace("(", "").replace(")", "")
        if any(re.fullmatch(pattern, flat) for pattern in identity):
            return "supported", "Paraphrase d'identité vérifiée par l'association locale terme-repère"
    for label, names in (("table", r"tableau|table"), ("figure", r"figure|fig\.?")):
        refs = re.findall(r"\b(?:" + names + r")\s+(\d+)\b", c)
        for ref in refs:
            match = re.search(r"\b(?:" + names + r")\s+" + re.escape(ref) + r"\b", q)
            if not match:
                return "insufficient", f"Référence {label} {ref} non établie dans cet extrait ; cela ne prouve pas son absence du document"
            if label == "table" and re.fullmatch(r"(?:le )?tableau " + ref + r" (?:concerne|presente|indique|porte sur) (?:les )?couples(?: de serrage)?[.!]?", c):
                caption = q[match.start():match.end()+60]
                if "torque" in caption or "couple" in caption:
                    return "supported", "Numéro et sujet du tableau associés dans la légende citée"
    return "insufficient", "La citation et le verdict du modèle ne suffisent pas à valider indépendamment toute cette reformulation"
