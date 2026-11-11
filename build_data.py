#!/usr/bin/env python3
"""Build data/birds-data.js for the game from huashu-bird-sticker's data/ folder.

Usage: python3 -I build_data.py <path-to-huashu-bird-sticker/data> [out.js]
"""
import csv, json, re, sys, os, collections

src = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "birds-data.js")

species = json.load(open(os.path.join(src, "species.json")))["species"]
stk = json.load(open(os.path.join(src, "stickers.json")))
cdn = stk["cdn"]
page = {s["id"]: (s.get("page") or "").replace("https://birdalbum.com/birds/", "").strip("/") for s in stk["stickers"]}

LANGS = [("en", "English", "en"), ("es", "Español", "es"), ("fr", "Français", "fr"), ("de", "Deutsch", "de"),
         ("pt", "Português", "pt-x-lusophone"), ("it", "Italiano", "it"), ("nl", "Nederlands", "nl"),
         ("ja", "日本語", "ja"), ("zh", "中文", "zh-Hans"), ("ru", "Русский", "ru")]
names = {}
with open(os.path.join(src, "names.csv"), newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        names[row["id"]] = [(row.get(col) or "").strip() for _, _, col in LANGS]

REGIONS = [  # IOC breeding-region code -> label
    ("NA", "North America", "🦅"), ("MA", "Middle America & Caribbean", "🌴"), ("SA", "South America", "🦜"),
    ("PAL", "Europe, N. Asia & N. Africa", "🏰"), ("AF", "Africa", "🦒"), ("OR", "South & Southeast Asia", "🐯"),
    ("AU", "Australasia", "🦘"), ("PO", "Pacific Ocean", "🏝️"), ("IO", "Indian Ocean", "🐚"),
    ("AO", "Atlantic Ocean", "⚓"), ("SO", "Southern Ocean", "🌊"), ("AN", "Antarctica", "🐧"),
]
rcode = {c: i for i, (c, _, _) in enumerate(REGIONS)}
rcode["TrO"] = rcode["PO"]  # tropical oceans: lump with Pacific so they stay findable

IND_CORE = (r"\bIndia\b|Indian [Ss]ubcontinent|South(ern)? Asia|Indomalay|Andaman(?! Sea)|Nicobar|Kashmir|Assam|Sikkim|Kerala|Ghats|Gujarat|Rajasthan|"
            r"Maharashtra|Karnataka|Tamil Nadu|(?<!Bay of )Bengal|Odisha|Orissa|Himachal|Uttarakhand|Arunachal|Meghalaya|Nagaland|Manipur|Mizoram|Tripura|Deccan|"
            r"Himalaya|Nepal|Bhutan|Bangladesh|Pakistan (to|through|and|east)|from Pakistan")
IND_STRICT = r"\bIndia\b|Indian [Ss]ubcontinent|South(ern)? Asia|Andaman(?! Sea)|Nicobar|Kerala|Ghats|Gujarat|Rajasthan|(?<!Bay of )Bengal|Deccan|Assam|Pakistan (to|through)"
PLACES = [
    ("India", IND_CORE),
    ("Himalayas", r"Himalaya"),
    ("Western Ghats & South India", r"Ghats|Kerala|Karnataka|Tamil Nadu|Nilgiri|\b[Ss]outhern Indian?\b(?!\s+(?:Ocean|oceans?|and (?:Pacific|Atlantic)))|\b[Pp]eninsular Indian?\b(?!\s+(?:Ocean|oceans?|and (?:Pacific|Atlantic)))|\b[Ss]outhwestern Indian?\b(?!\s+(?:Ocean|oceans?|and (?:Pacific|Atlantic)))|\bGoa\b"),
    ("Northeast India", r"Assam|Arunachal|Meghalaya|Nagaland|Manipur|Mizoram|Tripura|Sikkim|[Nn]ortheast(ern)? Indian?\b(?!\s+(?:Ocean|oceans?|and (?:Pacific|Atlantic)))"),
    ("Andaman & Nicobar", r"Andaman(?! Sea)|Nicobar"),
    ("Sri Lanka", r"Sri Lanka"), ("Nepal", r"Nepal"),
    ("Australia", r"\bAustralia\b|Queensland|New South Wales|Tasmania"),
    ("New Zealand", r"New Zealand"), ("New Guinea", r"New Guinea"),
    ("Indonesia", r"Indonesia|Sumatra|\bJava\b|Sulawesi|Moluccas|Lesser Sundas|\bBali\b"),
    ("Borneo", r"Borneo|Kalimantan|Sabah|Sarawak"), ("Philippines", r"Philippines"),
    ("China", r"\bChina\b|Tibet|Yunnan|Sichuan"), ("Japan", r"\bJapan\b|Honshu|Hokkaido|Ryukyu"),
    ("Russia & Siberia", r"Russia|Siberia"), ("Middle East", r"Arabia|\bIran\b|\bIraq\b|Israel|Syria|Türkiye|Turkey|Yemen|Oman"),
    ("Britain & Ireland", r"Britain|\bIreland\b|United Kingdom|\bUK\b"),
    ("Europe", r"Europe|Spain|France|Italy|Germany|Scandinavia|Iberia|Mediterranean"),
    ("South Africa", r"South Africa"), ("Madagascar", r"Madagascar"),
    ("East Africa", r"Kenya|Tanzania|Uganda|Ethiopia"), ("Congo Basin", r"Congo|Gabon|Cameroon"),
    ("USA", r"\bUSA\b|United States|Alaska|California|Texas|Florida|Arizona"), ("Canada", r"Canada"),
    ("Mexico", r"Mexico"), ("Costa Rica & Panama", r"Costa Rica|Panama"),
    ("Caribbean", r"Caribbean|Cuba|Jamaica|Hispaniola|Puerto Rico|Bahamas|Lesser Antilles"),
    ("Hawaii", r"Hawaii"), ("Galápagos", r"Galápagos|Galapagos"), ("Pacific Islands", r"Fiji|Samoa|Tonga|Vanuatu|Solomon Is|New Caledonia|Micronesia|Polynesia|Marquesas|Tahiti"),
    ("Amazon", r"Amazon"), ("Andes", r"Andes|Andean"), ("Brazil", r"Brazil"), ("Colombia", r"Colombia"),
    ("Ecuador", r"Ecuador"), ("Peru", r"Peru"), ("Argentina & Chile", r"Argentina|Chile|Patagonia"),
    ("Arctic", r"Arctic"), ("Antarctica", r"Antarctic"),
]

# "Everyday Indian birds" deck: well-known birds a casual observer in India would recognise (English names as in AviList)
EVERYDAY = {
    "Indian Peafowl", "Rose-ringed Parakeet", "House Crow", "Common Myna", "Red-vented Bulbul", "Asian Koel",
    "Indian Roller", "White-throated Kingfisher", "Common Kingfisher", "Pied Kingfisher", "Common Hoopoe",
    "Black Kite", "Brahminy Kite", "Spotted Owlet", "Indian Eagle-Owl", "Indian Pond Heron", "Western Cattle Egret",
    "Little Egret", "Great Egret", "Sarus Crane", "Demoiselle Crane", "Greater Flamingo", "Painted Stork",
    "Asian Openbill", "Greater Adjutant", "Eurasian Spoonbill", "Oriental Darter", "Little Cormorant",
    "Little Grebe", "Purple Swamphen", "Black-winged Stilt", "Bronze-winged Jacana", "Red-wattled Lapwing",
    "Oriental Magpie-Robin", "House Sparrow", "Rock Dove", "Spotted Dove", "Black Drongo", "Great Hornbill",
    "Greater Coucal", "Common Tailorbird", "Purple Sunbird", "Jungle Babbler", "Great Indian Bustard",
    "Indian Pitta", "Grey Francolin", "Black Francolin", "Common Quail", "Red Junglefowl", "Common Hawk-Cuckoo",
    "Indian Golden Oriole", "Shikra", "Peregrine Falcon", "Indian Vulture", "Barn Swallow", "Baya Weaver",
    "Scaly-breasted Munia", "Red Avadavat", "Rosy Starling", "White Wagtail", "Asian Green Bee-eater",
    "Coppersmith Barbet", "Himalayan Monal",
}
# Name corrections. AviList's English name (left) is shown to players as the name on the right.
# The original name is still accepted when someone types an answer. Add a line here to fix any other name.
NAME_OVERRIDES = {
    "Rock Dove": "Rock Pigeon",   # the name used in India (and by eBird)
}
PLACES = [(n, re.compile(rx)) for n, rx in PLACES]
IND_STRICT_RX = re.compile(IND_STRICT)
PELAGIC_RX = re.compile(r"Petrel|Shearwater|Albatross|Penguin|Booby|Boobies|Frigatebird|Tropicbird|Skua|Auk")
enseen = set()
enseen = set()

HAB = ["Forest", "Woodland", "Shrubland", "Grassland", "Wetland", "Riverine", "Coastal", "Marine", "Desert", "Rock", "Human Modified"]
DIET = ["Invertivore", "Omnivore", "Frugivore", "Granivore", "Nectarivore", "Aquatic predator", "Vertivore", "Herbivore terrestrial", "Herbivore aquatic", "Scavenger"]
MIG = ["sedentary", "partially migratory", "migratory"]
LIFE = ["Aerial", "Aquatic", "Terrestrial"]  # only the lifestyles that make a fun fact
IUCN = ["LC", "NT", "VU", "EN", "CR", "EX"]  # EX incl. EW
fams, famidx = [], {}
birds = []
placecount = collections.Counter()
for s in species:
    t = s["taxonomy"]
    key = (t["order"], t["family"])
    if key not in famidx:
        famidx[key] = len(fams)
        fams.append({"l": t["family"], "e": t.get("familyEnglish") or t["family"], "o": t["order"]})
    tr = s.get("traits") or {}
    rng = s.get("range") or {}
    ioc = rng.get("ioc") or {}
    regs = set()
    for c in (ioc.get("breedingRegion") or "").split(","):
        c = c.strip()
        if c in rcode:
            regs.add(rcode[c])
        elif c.startswith("Worldwide"):
            regs.update(range(len(REGIONS)))
    text = " ".join([rng.get("text") or "", ioc.get("breeding") or "", ioc.get("nonbreeding") or ""])
    pel = bool(PELAGIC_RX.search(t.get("familyEnglish") or ""))   # open-ocean families
    places = [i for i, (n, rx) in enumerate(PLACES) if rx.search(text)]
    if pel:  # open-ocean birds (petrels, shearwaters, penguins...) stay out of the India decks: nobody sees them from land
        places = [i for i in places if PLACES[i][0] not in ("India", "Himalayas", "Western Ghats & South India", "Northeast India", "Andaman & Nicobar")]
    if s["names"]["en"] in EVERYDAY and 0 not in places:
        places.insert(0, 0)  # index 0 = India
    for i in places:
        placecount[PLACES[i][0]] += 1
    en_name = s["names"]["en"]
    br_txt = ioc.get("breeding") or (rng.get("text") or "").split("winter")[0]
    nb_txt = (ioc.get("nonbreeding") or "") + " " + ("winter".join((rng.get("text") or "").split("winter")[1:]) if "winter" in (rng.get("text") or "") else "")
    visitor = (not pel) and bool(IND_STRICT_RX.search(nb_txt)) and not IND_STRICT_RX.search(br_txt) and tr.get("migration") in ("migratory", "partially migratory")
    iu = (s.get("conservation") or {}).get("iucn") or ""
    iu = iu.split(" ")[0]
    iu = "EX" if iu in ("EW",) else iu
    b = {
        "i": s["id"], "s": s["scientificName"], "f": famidx[key],
        "h": HAB.index(tr["habitat"]) if tr.get("habitat") in HAB else -1,
        "d": DIET.index(tr["trophicNiche"]) if tr.get("trophicNiche") in DIET else -1,
        "m": MIG.index(tr["migration"]) if tr.get("migration") in MIG else -1,
        "c": IUCN.index(iu) if iu in IUCN else -1,
        "w": round(tr["massG"], 1) if tr.get("massG") else 0,
        "hw": round(tr["handWingIndex"]) if tr.get("handWingIndex") else 0,   # hand-wing index: how long and pointed the wings are
        "ls": LIFE.index(tr["primaryLifestyle"]) if tr.get("primaryLifestyle") in LIFE else -1,
        "ss": min(len(s.get("subspecies") or []), 99),                         # number of subspecies
        "r": sorted(regs), "p": places,
        "n": names.get(s["id"]) or [s["names"]["en"]] + [""] * (len(LANGS) - 1),
        "g": page.get(s["id"], ""),
        "v": 1 if visitor else 0,
        "k": 1 if en_name in EVERYDAY else 0,
    }
    b["n"][0] = b["n"][0] or s["names"]["en"]
    if en_name in NAME_OVERRIDES:
        b["alt"] = [en_name]
        b["n"][0] = NAME_OVERRIDES[en_name]
    if en_name in EVERYDAY: enseen.add(en_name)
    birds.append(b)

# drop places with too few species to be a good filter
keep = [i for i, (n, _) in enumerate(PLACES) if placecount[n] >= 40 or i < 7]
remap = {old: new for new, old in enumerate(keep)}
for b in birds:
    b["p"] = [remap[i] for i in b["p"] if i in remap]
places_out = [PLACES[i][0] for i in keep]

data = {
    "cdn": cdn, "credit": stk["credit"], "langs": [[c, l] for c, l, _ in LANGS],
    "regions": [[l, e] for _, l, e in REGIONS], "places": places_out,
    "habitats": HAB, "diets": DIET, "migrations": MIG, "iucn": IUCN,
    "fams": fams, "birds": birds,
}
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("window.BIRD_DATA=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
print("birds", len(birds), "families", len(fams), "size MB", round(os.path.getsize(out) / 1e6, 2))
print({n: placecount[n] for n, _ in PLACES})
print("everyday matched", len(enseen), "missing:", sorted(EVERYDAY - enseen))
print("winter visitors", sum(b["v"] for b in birds))
print("region coverage", sum(1 for b in birds if b["r"]), "habitat", sum(1 for b in birds if b["h"] >= 0))
