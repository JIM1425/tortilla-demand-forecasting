'''
Compara los clientes únicos del CSV contra la lista oficial de clientes,
aplicando el mapeo conocido (customer_map) primero.
Genera sugerencias de conversión para nombres con similitud >= THRESHOLD.
'''

import csv
import re
from difflib import SequenceMatcher


THRESHOLD = 0.80          # umbral de similitud: que tan parecidos deben ser los nombres

# clientes oficiales 
OFFICIAL_CUSTOMERS = [
    "chabela", "omar"
]

#Mapeo conocido (customer_map.txt) 
KNOWN_MAP = {
    "chabe": "chabela", 
}

# Funciones de similitud 

def normalize(name: str) -> str: 
    n = name.lower().strip()
    replacements = {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n"}
    for k, v in replacements.items():
        n = n.replace(k, v)
    n = re.sub(r"[\-\s]+", "_", n)
    return n

def sequence_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def token_overlap(a: str, b: str) -> float:  # útil para nombres compuestos
    ta = set(re.split(r"[_\-\s]+", a))
    tb = set(re.split(r"[_\-\s]+", b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))

def substring_bonus(a: str, b: str) -> float:  
    if a in b or b in a:
        return 0.15
    return 0.0

def best_similarity(raw: str, official: str) -> float:
    """Combina varias métricas para un score final."""
    a = normalize(raw)
    b = normalize(official)
    seq   = sequence_similarity(a, b)
    token = token_overlap(a, b)
    bonus = substring_bonus(a, b)
    score = max(seq, token) + bonus
    return min(score, 1.0)


def get_unique_clients(csv_path: str) -> set:
    clients = set()
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clients.add(row["cliente"].strip())
    return clients

# logica principal 

def run(csv_path: str, threshold: float = THRESHOLD):
    unique = get_unique_clients(csv_path)
    official_set = set(OFFICIAL_CUSTOMERS)
    official_norm = {normalize(c): c for c in OFFICIAL_CUSTOMERS}

    # clasificar cada cliente ú
    already_mapped  = {}   # cliente -> destino (por KNOWN_MAP)
    already_official = []  # ya es un cliente oficial
    suggestions      = []  # (cliente, mejor_match, score)
    no_match         = []  # nada parecido

    for raw in sorted(unique):
        norm = normalize(raw)

     
        if norm in {normalize(k): v for k, v in KNOWN_MAP.items()}:
            dest = KNOWN_MAP.get(raw) or KNOWN_MAP.get(norm)
            already_mapped[raw] = dest
            continue

   
        if norm in official_norm:
            already_official.append(raw)
            continue

      
        best_score = 0.0
        best_match = None
        for off in OFFICIAL_CUSTOMERS:
            sc = best_similarity(raw, off)
            if sc > best_score:
                best_score = sc
                best_match = off

        if best_score >= threshold:
            suggestions.append((raw, best_match, best_score))
        else:
            no_match.append((raw, best_match, best_score))

    # resultados 
    print("=" * 65)
    print(f"umbral de similitud: {threshold*100:.0f}%")
    print("=" * 65)

    print(f"\n Clietes en lista oficial ({len(already_official)}):")
    for c in sorted(already_official):
        print(f"   {c}")

    print(f"\n Ya cubiertos ({len(already_mapped)}):")
    for raw, dest in sorted(already_mapped.items()):
        print(f"   '{raw}' → '{dest}'")

    print(f"\n Sugerencias (similitud ≥ {threshold*100:.0f}%) — {len(suggestions)} encontradas:")
    for raw, match, score in sorted(suggestions, key=lambda x: -x[2]):
        print(f"   '{raw}' → '{match}'  ({score*100:.1f}%)")

    print(f"\n Sin coincidencia sufuciente (<{threshold*100:.0f}%) — {len(no_match)} clientes:")
    for raw, match, score in sorted(no_match, key=lambda x: -x[2]):
        print(f"   '{raw}'  (mejor: '{match}', {score*100:.1f}%)")


    print("\n" + "=" * 65)
    print("Nuevo bloque para agregar a customer_map  (sugerencias):")
    print("=" * 65)
    for raw, match, score in sorted(suggestions, key=lambda x: x[0]):
        print(f'    "{normalize(raw)}":"{match}" ' ) # {score*100:.1f}%

    return suggestions, no_match

#entrada
if __name__ == "__main__":
    suggestions, no_match = run(
        csv_path="2026_DB.csv",
        threshold=THRESHOLD
    )
