# Architecture des fichiers `.aps` — Hidden Stroke 2

Rétro-ingénierie du format de fichiers `.aps` utilisé par Hidden Stroke 2 (standalone basé sur le moteur Sudden Strike 2 / Sudden Strike Forever). Ce document décrit la structure du conteneur, les différents types de contenu qu'il transporte selon le fichier, et répond empiriquement à une question récurrente du modding : **le blindage des unités change-t-il selon l'environnement (été/hiver/désert/jungle) ?**

Réalisé par rétro-ingénierie sur des fichiers déjà présents dans une installation du jeu, à but d'interopérabilité et de documentation communautaire. Aucun asset protégé (sprite, son) n'est redistribué ici — uniquement la structure des formats et de courts extraits illustratifs de données de jeu.

## Sommaire

- [Le conteneur FZFF](#le-conteneur-fzff)
- [Script de décompression générique](#script-de-décompression-générique)
- [Ce que contient chaque type de fichier](#ce-que-contient-chaque-type-de-fichier)
  - [1. Sprite d'unité individuel (`<unit>.aps`)](#1-sprite-dunité-individuel-unitaps)
  - [2. `lang.aps` — fiches de caractéristiques](#2-langaps--fiches-de-caractéristiques)
  - [3. `main*.aps` — atlas graphiques](#3-mainaps--atlas-graphiques)
  - [4. `*_unit.aps` — fichiers par région/environnement](#4-_unitaps--fichiers-par-régionenvironnement)
- [Le blindage change-t-il selon l'environnement ?](#le-blindage-change-t-il-selon-lenvironnement)
- [Pistes pour aller plus loin](#pistes-pour-aller-plus-loin)

## Le conteneur FZFF

Tous les fichiers `.aps` observés partagent le même conteneur, quel que soit leur contenu :

```
Offset 0 : "FZFF"           (4 octets, magic)
Offset 4 : uint32 LE        (champ de taille, proche de la taille totale décompressée — usage exact non confirmé)
Offset 8 : flux zlib #1
           flux zlib #2
           ...
           flux zlib #N     (concaténés bout à bout, sans en-tête de longueur entre eux)
```

Chaque entrée est un flux **zlib/deflate standard** (RFC 1950), directement concaténé au précédent — le flux suivant démarre à l'octet exact où le précédent s'arrête (repérable par sa somme de contrôle Adler-32 finale). Il n'y a **aucune table des matières explicite avec noms de fichiers** : le seul moyen de savoir ce qu'une entrée contient est de la décompresser et d'inspecter son contenu (texte ou binaire).

L'en-tête zlib le plus fréquent est `78 9c` (compression par défaut) mais on trouve aussi `78 da` (compression maximale) selon l'outil qui a généré l'archive — un détecteur robuste doit tester tout couple d'octets `78 XX` valide (`(0x78*256 + XX) % 31 == 0`), pas seulement `78 9c`.

## Script de décompression générique

```python
import zlib

def is_zlib_header(b0, b1):
    return b0 == 0x78 and (b0 * 256 + b1) % 31 == 0

def decompress_aps(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:4] == b"FZFF", "pas un conteneur FZFF"
    pos = 8
    entries = []
    n = len(data)
    while pos < n - 1:
        if data[pos] == 0x78 and is_zlib_header(data[pos], data[pos + 1]):
            d = zlib.decompressobj()
            chunk = data[pos:pos + 2_000_000]  # marge large, le flux s'arrête tout seul
            out = d.decompress(chunk)
            consumed = len(chunk) - len(d.unused_data)
            if consumed > 0 and len(out) > 0:
                entries.append(out)
                pos += consumed
                continue
        pos += 1
    return entries  # liste de blobs bytes, texte ou binaire selon le fichier source
```

Ce script suffit à extraire le contenu brut de n'importe quel `.aps` du jeu. Ce qu'on fait ensuite de chaque entrée dépend du type de fichier (voir sections suivantes).

## Ce que contient chaque type de fichier

### 1. Sprite d'unité individuel (`<unit>.aps`)

Exemple : `15cm-K-39.aps` (obusier lourd allemand). Une fois décompilé, produit trois fichiers :

| Fichier | Taille | Contenu |
|---|---|---|
| `.pck` | variable | Table d'offsets 32 bits LE pointant vers des blocs de pixels/frames compressés |
| `.col` | 512 octets exactement | Palette de 256 couleurs (2 octets/couleur, 16 bits, probablement RGB565) |
| `.hot` | 768 octets (typique) | 96 paires `(x, y)` int32 LE = 3 groupes de 32 points, chacun décrivant une trajectoire quasi circulaire autour du centre du sprite — les points d'ancrage ("hotspots") pour un effet donné (ex. bouche du canon) à chaque angle de rotation (32 directions standard du moteur) |

Le nom de base doit rester identique entre les trois fichiers (`15cm-K-39.pck` / `.col` / `.hot`) : les outils historiques (SuSt Graph, PCK Explorer, `pckView` du projet [WarToolKit](https://github.com/americusmaximus/WarToolKit)) les associent par nom de fichier, pas par en-tête interne.

### 2. `lang.aps` — fiches de caractéristiques

Fichier **unique et global** (confirmé par une note d'un patch communautaire prévenant explicitement de ne pas l'écraser). Contient une entrée texte par unité du jeu — **532 fiches** dans l'exemplaire analysé. Chaque fiche regroupe l'identité, le comportement et les statistiques de combat d'une unité :

```
name "obusier Allemand (150mm K39 / tres lourd)"
shortname "obusier 150mm"
file 15cm-k-39
camouflage ...
native german
crew_unit ...
health 340
movespeed 0.1 0.1
armor EXPLOSIVE 1 1 1 1 1 1
armor FIRE 24 24 24 24 24 24
protection EXPLOSIVE 3 3 3 3 0 0
...
```

Les champs `armor` / `protection` prennent 6 valeurs (avant/côté/arrière × 2, probablement haut/bas de caisse ou état intact/endommagé) par type de dégât (`EXPLOSIVE`, `PIERCE`, `MACHINE`, `MINE`, `MINE_AT`, `FIRE`, `SNIPER`, `TRANSPIERCE`, `PIAT`, `ABJECTIVE`, `AIR`). Le champ `file` fait le lien avec le sprite `.aps` correspondant.

### 3. `main*.aps` — atlas graphiques

`main.aps`, `main_patch.aps`, `main_war.aps`, `main_war_patch.aps`, `main_winter.aps`, `main_winter_patch.aps` : tous **100% binaires**, aucune fiche texte. Les entrées font très majoritairement 16 384 octets décompressés (0x4000 = 128×128 pixels en bitmap indexé), cohérent avec des tuiles de terrain ou des sprites d'unité empaquetés en masse. Schéma probable : une paire base + correctif par variante graphique (`main`/`main_patch` = mode standard, `main_war`/`main_war_patch` = mode "War", `main_winter`/`main_winter_patch` = reskin hiver).

### 4. `*_unit.aps` — fichiers par région/environnement

Seize fichiers examinés (`asien`, `beach_unit_s1`, `europe2`, `franz`, `land`, `land2`, `mount`, `russ1`, `russ2`, `sommer_unit`, `sommer_unit_s1`, `stadt`, `sud`, `winter_unit`, `winter_unit_s1`, `wuste_unit_s1`), regroupant en réalité **trois contenus distincts** :

**a) Fiches véhicule (mêmes champs que `lang.aps`)** — présentes dans exactement 8 des 16 fichiers, toujours les 15 mêmes unités (véhicules de ravitaillement/logistique : `f_sup`, `gmc_ver`, `lancia`, `m-4w`, `m-5wrus`, `m5_versorger`, `morris_c8`, `mun_pz4`, `opel_ver`, `scammell`, `sdkfz-251`, `sdkfz-252`, `sdkfz11`, `ss_indginer`, `zis5_ver`).

**b) Fiches d'objets de décor** (`name obj N "..."`, `HP obj N ...`, `ARMOR obj N ...`) — bâtiments, bunkers, murs, arbres destructibles, indexés par un numéro d'objet et non par un nom de fichier. Ce sont des **structures propres au thème visuel de la région** (une hutte en thème asiatique, un bunker en thème hiver) : des types d'objets différents, pas la redéfinition d'un même objet.

**c) Tables d'effet de terrain** (`explosion <type_de_sol> <effet>`) — associent un type de sol (`grass`, `sand`, `darkground`, `swamp`...) à un effet visuel de poussière/boue au passage d'un véhicule. Purement cosmétique.

**d) Liste de ressources nommées** en fin d'archive (chemins vers d'autres fichiers du thème, ex. `land\CLIFF`, `land\STAND`).

## Le blindage change-t-il selon l'environnement ?

Question testée empiriquement en comparant les 15 fiches véhicule communes entre `lang.aps` et les 8 fichiers d'environnement qui en contiennent (120 combinaisons).

**Résultat : 119 combinaisons sur 120 sont strictement identiques**, `armor`/`protection`/`movespeed`/`health`/`shot_*`/`onDmg_*`/`onHit_*` compris — jusqu'au moindre caractère (diff ligne à ligne vide).

**Une exception vérifiée** : `sdkfz-252` dans `sommer_unit_s1.aps` (thème été) diffère de `lang.aps` :

```diff
- armor MACHINE 256 256 200 200 200 200
+ armor MACHINE 200 200 200 200 200 200

- armor SNIPER 256 256 256 256 256 256
+ armor SNIPER 200 200 200 200 200 200

- protection MACHINE 256 256 200 200 200 200
+ protection MACHINE 200 200 200 200 200 200

- protection MINE 256 256 256 256 256 256
+ protection MINE 200 200 200 200 200 200

- protection SNIPER 256 256 256 256 256 256
+ protection SNIPER 200 200 200 200 200 200

- ez2 73 81 89 97 105
+ ez2 73 105
```

(`256` est la valeur plafond utilisée ailleurs dans les fiches pour signifier une quasi-immunité à un type de dégât ; `ez2` semble être une liste d'options de production/équipement disponibles pour l'unité.)

**Conclusion** : il n'existe pas de mécanisme systématique de blindage dépendant de l'environnement dans les fichiers de données. L'écart trouvé sur le SdKfz-252 ressemble à une correction isolée faite à la main sur cette unité précise plutôt qu'à une règle de design volontaire — mais il prouve que le mécanisme de redéfinition *existe* et peut être utilisé (volontairement ou par erreur) au niveau des fichiers `*_unit.aps`.

**Reste non vérifié** : quelle valeur le moteur retient réellement en jeu quand une fiche est dupliquée entre `lang.aps` et un fichier d'environnement (`lang.aps` chargé en premier et écrasé par le fichier d'environnement, ou l'inverse). Par analogie avec le moteur Sudden Strike 2 d'origine documenté (où `lang.sue` écrase `desc_common.sue`), l'hypothèse la plus probable est que le fichier le plus spécifique (environnement) prime — mais seul un test en jeu peut le confirmer avec certitude (ex. modifier une valeur `HP` très visible côté environnement et vérifier si elle s'applique en partie).

## Pistes pour aller plus loin

- **Test empirique en jeu** pour confirmer l'ordre de priorité entre `lang.aps` et les fichiers d'environnement.
- **Cartographier `main.aps`** (83 Mo) : probablement l'atlas graphique maître regroupant pck/col/hot pour l'ensemble des unités du jeu — les premières entrées observées (512 puis 768 octets) correspondent exactement aux tailles d'un `.col` et d'un `.hot`.
- **Recenser les ~2700 fiches d'objets de décor** (`obj N`) pour vérifier si d'autres incohérences du même type que le SdKfz-252 existent côté bâtiments/structures.
- Contributions bienvenues — ouvrez une issue ou une PR sur ce repo avec vos propres trouvailles.
