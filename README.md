# Hidden Stroke 2 — outillage et rétro-ingénierie

Outils et notes de modding pour **Hidden Stroke 2**, standalone bâti sur le moteur
Sudden Strike 2 / Sudden Strike Forever.

## Documentation

- **[Architecture des fichiers `.aps`](docs/format-aps.md)** — structure du conteneur FZFF,
  contenu réel de chaque type de fichier (sprites, `lang.aps`, atlas `main*.aps`, fichiers
  d'environnement), et la réponse empirique à la question récurrente du blindage variable
  selon l'environnement : il n'existe pas de mécanisme systématique, mais une exception
  vérifiée prouve que la redéfinition est possible.

## `tools/` — outillage actuel (Python 3.8+)

Deux outils sans aucune dépendance, qui ouvrent une interface dans le navigateur et
fonctionnent à l'identique sur macOS et Windows :

- **APS Tool** (`hs2_aps_tool.py`) — décompacte et recompacte `lang.aps`, et plus
  généralement n'importe quelle archive FZFF.
- **Mission Editor** (`hs2_mission_editor.py`) — édite les convois de renfort, l'expérience,
  les joueurs et les scripts de chaque carte.
- `decompile_aps.py` — décompression brute d'une archive, en ligne de commande.
- `HS2_Unit_Comparator_V11_26.html` — comparateur d'unités, page autonome à ouvrir
  directement dans un navigateur.

Les lanceurs `.command` (macOS) et `.bat` (Windows) évitent d'avoir à passer par le terminal.
Voir [`tools/README.md`](tools/README.md) pour le détail, en anglais.

## `scripts/perl-legacy/` — scripts historiques (2014)

Une vingtaine de scripts Perl écrits pour l'édition en masse des fiches d'unités, à l'époque
où le travail se faisait sur les fichiers décompilés : extraction de listes par
caractéristique (`liste_accuracy.pl`, `liste_tank_armor_pierce.pl`, `liste_shot_speed.pl`,
`liste_arty_damage.pl`…) et modification en lot (`moving_accuracy.pl`, `moving_range.pl`,
`moving_gundelay.pl`, `moving_planes.pl`…).

Ils attendent en entrée une arborescence de fiches d'unités décompilées, qui **n'est pas
fournie ici** : ce sont des données du jeu, à extraire de votre propre installation avec
l'APS Tool. `unites-hs.txt` et `unites-rw.txt` donnent les listes de noms d'unités
correspondantes.

## `game/` — l'installation de référence

Copie de l'installation **Hidden Stroke II 4.21** (`Misc/`, `Run/`), conservée ici comme
référence pour la rétro-ingénierie : c'est sur ces fichiers que la documentation du format
`.aps` a été établie, et l'outillage a besoin d'eux pour être exercé.

`SOUNDAP.RUS` (373 Mo) n'y est **pas** : GitHub refuse tout fichier de plus de 100 Mo.
L'installation n'est donc pas complète — récupérez ce fichier depuis votre propre copie du
jeu si vous voulez la reconstituer.

> **Dépôt privé, à garder privé.** `game/` contient les assets du jeu — graphismes, sons,
> cartes, données d'unités. Ce sont des œuvres publiées par CDV et leurs auteurs ; les
> conserver ici relève de l'archivage personnel d'une copie légitime, pas de la
> redistribution. Rendre ce dépôt public en ferait une redistribution.

## Ce que ce dépôt ne contient pas

- **Aucun binaire tiers d'outillage** : `SUE.EXE` / `UNSUE.EXE` et les autres outils
  communautaires historiques appartiennent à leurs auteurs et se récupèrent auprès d'eux.
- **`SOUNDAP.RUS`**, écarté pour raison de taille (voir ci-dessus).

La rétro-ingénierie documentée ici a été faite à partir d'une installation légitime du jeu,
à fin d'interopérabilité et de documentation communautaire.
