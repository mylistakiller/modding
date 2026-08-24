# Hidden Stroke 2 : outillage et rétro-ingénierie

Outils et notes de modding pour Hidden Stroke 2, standalone bâti sur le moteur Sudden Strike 2
et Sudden Strike Forever.

## Documentation

[Architecture des fichiers `.aps`](docs/format-aps.md) décrit la structure du conteneur FZFF et
le contenu réel de chaque type de fichier : sprites, `lang.aps`, atlas `main*.aps`, fichiers
d'environnement. Le document répond aussi à une question récurrente du modding, celle du
blindage qui varierait selon l'environnement. Il n'existe pas de mécanisme systématique, mais
les copies dupliquées dans les fichiers `*_unit.aps` ne suivent pas les mises à jour de
`lang.aps`, ce qui produit des divergences bien réelles.

## `tools/` : outillage actuel (Python 3.8+)

Deux outils sans dépendance, qui ouvrent une interface dans le navigateur et fonctionnent à
l'identique sur macOS et Windows.

- `hs2_aps_tool.py`, l'APS Tool : décompacte et recompacte `lang.aps`, et plus généralement
  n'importe quelle archive FZFF.
- `hs2_mission_editor.py`, le Mission Editor : édite les convois de renfort, l'expérience, les
  joueurs et les scripts de chaque carte.
- `decompile_aps.py` : décompression brute d'une archive, en ligne de commande.
- `HS2_Unit_Comparator_V11_26.html` : comparateur d'unités, page autonome à ouvrir dans un
  navigateur.

Les lanceurs `.command` et `.bat` évitent le passage par le terminal. Le détail est dans
[`tools/README.md`](tools/README.md), en anglais.

## `scripts/perl-legacy/` : scripts historiques (2014)

Une vingtaine de scripts Perl écrits pour l'édition en masse des fiches d'unités, à l'époque où
le travail se faisait sur les fichiers décompilés. Ils extraient des listes par caractéristique
(`liste_accuracy.pl`, `liste_tank_armor_pierce.pl`, `liste_shot_speed.pl`, `liste_arty_damage.pl`)
ou modifient en lot (`moving_accuracy.pl`, `moving_range.pl`, `moving_gundelay.pl`,
`moving_planes.pl`).

Ils attendent en entrée une arborescence de fiches d'unités décompilées, qui n'est pas fournie
ici : ce sont des données du jeu, à extraire de votre propre installation avec l'APS Tool.
`unites-hs.txt` et `unites-rw.txt` donnent les listes de noms d'unités correspondantes.

## `game/` : l'installation de référence

Copie de l'installation Hidden Stroke II 4.21 (`Misc/`, `Run/`). C'est sur ces fichiers que la
documentation du format `.aps` a été établie, et l'outillage a besoin d'eux pour être exercé.

`SOUNDAP.RUS` (373 Mo) n'y est pas, GitHub refusant tout fichier de plus de 100 Mo.
L'installation n'est donc pas complète : récupérez ce fichier depuis votre propre copie du jeu
pour la reconstituer.

## Ce que ce dépôt ne contient pas

Aucun binaire tiers d'outillage. `SUE.EXE`, `UNSUE.EXE` et les autres outils communautaires
historiques appartiennent à leurs auteurs et se récupèrent auprès d'eux.

La rétro-ingénierie documentée ici a été faite à partir d'une installation légitime, à fin
d'interopérabilité et de documentation communautaire.
