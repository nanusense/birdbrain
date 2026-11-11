#!/usr/bin/env python3
"""Builds data/daily.js: the frozen lists the Daily Birdbrain game picks from.

Each day takes the next few birds from four lists, so a bird never repeats until a whole list has been used:
  A  3 well-known birds        (everyday Indian birds + famous birds from around the world)
  B  4 birds of India          (clear, recognisable ones: no look-alike warblers or sandpipers)
  C  2 birds from the world    (charismatic families: parrots, owls, kingfishers, toucans...)
  D  1 hard finish             (a rarer or trickier bird from those same families)
The lists are shuffled ONCE here with a fixed seed and written to the file, so the day's birds never change
when the bird data is rebuilt. Run:  python3 build_daily.py            (writes data/daily.js)
Preview what's coming:               python3 build_daily.py --preview 14
"""
import json, random, sys, datetime, re, pathlib

HERE = pathlib.Path(__file__).parent
START = '2026-11-11'          # Daily #1 (an IST date)
SEED = 20261111
PER = [3, 4, 2, 1]

raw = (HERE / 'data' / 'birds-data.js').read_text(encoding='utf-8')
D = json.loads(re.sub(r'^window\.BIRD_DATA=|;\s*$', '', raw))
birds, fams, places = D['birds'], D['fams'], D['places']
by_en = {b['n'][0]: b for b in birds}
INDIA = places.index('India')
fam_l = lambda b: fams[b['f']]['l']

# well-known birds from around the world (names that are not in the data are skipped and reported)
FAMOUS = '''Bald Eagle|Emperor Penguin|Scarlet Macaw|Greater Flamingo|Snowy Owl|Toco Toucan|Common Ostrich|Atlantic Puffin|Peregrine Falcon|Mallard|Mute Swan
Common Kingfisher|Rainbow Lorikeet|Northern Cardinal|Blue Jay|American Robin|European Robin|Laughing Kookaburra|Secretarybird|Shoebill|Southern Cassowary|Emu
Resplendent Quetzal|Great Horned Owl|Harpy Eagle|Andean Condor|California Condor|Golden Eagle|Eurasian Magpie|Grey Crowned Crane|Sandhill Crane|Brown Pelican
Great White Pelican|Blue-footed Booby|King Penguin|Adelie Penguin|Superb Lyrebird|Lilac-breasted Roller|Common Starling|House Sparrow|Great Tit|Common Blackbird
Eurasian Jay|Ruby-throated Hummingbird|Hyacinth Macaw|Sulphur-crested Cockatoo|Galah|Budgerigar|Kea|Kakapo|Hoatzin|Common Loon|Wood Duck|Mandarin Duck
Red-crowned Crane|Whooping Crane|Greater Roadrunner|Roseate Spoonbill|Scarlet Ibis|Marabou Stork|African Fish Eagle|Hamerkop|Northern Gannet|Golden Pheasant
Wild Turkey|Helmeted Guineafowl|Greater Bird-of-paradise|Satin Bowerbird|Eurasian Eagle-Owl|Great Grey Owl|Burrowing Owl|Northern Lapwing|Eurasian Wren
Common Cuckoo|Superb Fairywren|Keel-blooded Toucan|Keel-billed Toucan|Osprey|Great Spotted Woodpecker|Pileated Woodpecker|Pied Kingfisher|Belted Kingfisher
Great Blue Heron|Grey Heron|Painted Stork|Sarus Crane|Great Hornbill|Rhinoceros Hornbill|Indian Pitta|Common Moorhen|Common Pheasant|Barn Swallow|Eurasian Hoopoe
Eurasian Blue Tit|Eurasian Skylark|White Stork|Common Kestrel|Eurasian Spoonbill|Black-headed Gull|Herring Gull|Little Egret|Great Egret|Cattle Egret'''.replace('\n', '|').split('|')
FAMOUS = [n.strip() for n in FAMOUS if n.strip()]
missing = [n for n in FAMOUS if n not in by_en]

# look-alike families: lovely birds, but too hard to be a fair "daily" question
HARD = set('''Phylloscopidae Acrocephalidae Locustellidae Cisticolidae Sylviidae Scotocercidae Muscicapidae Emberizidae Motacillidae Alaudidae Scolopacidae
Cettiidae Hirundinidae Estrildidae Passeridae Ploceidae Fringillidae Parulidae Tyrannidae Furnariidae Thamnophilidae Trochilidae Cuculidae Charadriidae
Laridae Procellariidae Hydrobatidae Rallidae Apodidae Caprimulgidae Zosteropidae Pycnonotidae Timaliidae Pellorneidae Leiothrichidae Troglodytidae
Hylocichlidae Vireonidae Icteridae Thraupidae Tachyphonidae Conopophagidae Grallariidae Rhinocryptidae Formicariidae'''.split())
CHARISMATIC = set('''Psittacidae Cacatuidae Psittaculidae Psittrichasiidae Strigidae Tytonidae Ramphastidae Alcedinidae Halcyonidae Cerylidae Meropidae Coraciidae Bucerotidae
Phasianidae Paradisaeidae Spheniscidae Pelecanidae Ardeidae Ciconiidae Threskiornithidae Gruidae Accipitridae Falconidae Anatidae Corvidae Trogonidae Pittidae
Cotingidae Pipridae Ptilonorhynchidae Cardinalidae Upupidae Phoenicopteridae Sulidae Podargidae Megapodiidae Bucconidae Galbulidae Capitonidae Megalaimidae
Lybiidae Picidae Musophagidae Nectariniidae Dicruridae Campephagidae Oriolidae Monarchidae Rhipiduridae Sittidae Paridae Turdidae Sturnidae Menuridae
Cracidae Odontophoridae Numididae Struthionidae Rheidae Casuariidae Apterygidae Anhingidae Phalacrocoracidae Pandionidae Sagittariidae Cathartidae
Steatornithidae Opisthocomidae Balaenicipitidae Scopidae Psophiidae Rhynochetidae Eurypygidae Cariamidae'''.split())

used = set()
def take(lst):
    out = []
    for b in lst:
        if b['i'] not in used:
            used.add(b['i']); out.append(b)
    return out

A = take([b for b in birds if b['k']] + [by_en[n] for n in FAMOUS if n in by_en])
# widespread, well-studied birds are the ones people have seen: more regions / subspecies / bigger bodies
def known(b): return len(b['r']) + min(b['ss'], 6) // 2 + (2 if b['w'] >= 300 else 0) + (1 if b['w'] >= 100 else 0)
india = [b for b in birds if INDIA in b['p'] and b['c'] == 0 and b['w'] >= 15 and fam_l(b) not in HARD and known(b) >= 2]
B = take(india)
world_ok = [b for b in birds if INDIA not in b['p'] and b['c'] == 0 and b['w'] >= 20 and fam_l(b) in CHARISMATIC and fam_l(b) not in HARD]
C = take(sorted(world_ok, key=lambda b: -known(b))[:420])
hard_ok = [b for b in birds if fam_l(b) in CHARISMATIC and b['w'] >= 15 and known(b) >= 2]
Dd = take(sorted(hard_ok, key=lambda b: -known(b))[:420])

rng = random.Random(SEED)
lists = {}
for name, lst in (('A', A), ('B', B), ('C', C), ('D', Dd)):
    ids = [b['i'] for b in lst]
    rng.shuffle(ids)
    lists[name] = ids

out = {'start': START, 'per': PER, **lists}
(HERE / 'data' / 'daily.js').write_text('window.DAILY=' + json.dumps(out, separators=(',', ':')) + ';\n', encoding='utf-8')
by_id = {b['i']: b for b in birds}
print('lists:', {k: len(v) for k, v in lists.items()}, '| days before any list repeats:', min(len(lists[k]) // p for k, p in zip('ABCD', PER)))
if missing: print('not in data, skipped:', ', '.join(missing))

if '--preview' in sys.argv:
    n = int(sys.argv[sys.argv.index('--preview') + 1])
    d0 = datetime.date.fromisoformat(START)
    for day in range(n):
        names = []
        for t, p in zip('ABCD', PER):
            L = lists[t]
            names += [by_id[L[(day * p + j) % len(L)]]['n'][0] for j in range(p)]
        print(f'#{day + 1} {d0 + datetime.timedelta(days=day)}: ' + ' | '.join(names))
