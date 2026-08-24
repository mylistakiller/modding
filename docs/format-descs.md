# Le format des descs Sudden Strike : grammaire et index des champs

Les fiches d'unités et d'objets du moteur Sudden Strike — les *descs* — sont des fichiers texte
en `clé valeur`. C'est ce que [`format-aps.md`](format-aps.md) trouve à l'intérieur de
`lang.aps` et des fichiers `*_unit.aps` une fois le conteneur FZFF ouvert. Le présent document
en donne la grammaire et l'index des champs.

## Source

Ce document reprend et met en forme un catalogue publié sur le forum **sudden-strike.ru**
(*Каталог всех десков юнитов и объектов с описанием*, 26 pages, en russe).

Ce qui suit n'est pas une traduction intégrale : c'est la grammaire du format, traduite et
remise en ordre, plus l'index complet des champs. Les descriptions détaillées, champ par champ,
restent dans le document d'origine — leur mise en page sur trois colonnes ne s'extrait pas
proprement, et je préfère ne rien affirmer plutôt que de publier une extraction brouillée.

## La grammaire du format

Ce sont les règles générales, et ce sont elles qui permettent de lire le reste.

**Syntaxe.** Un paramètre et sa valeur sont séparés par une espace ou une tabulation,
indifféremment. Les majuscules et les minuscules ne sont pas distinguées. Les valeurs peuvent
être négatives ou fractionnaires.

**Le tiret désactive.** Le caractère `-` seul met un paramètre hors service, il joue le rôle
d'un commentaire. Employé avec une valeur, il peut aussi signifier « valeur par défaut », ou
simplement un nombre négatif — le contexte tranche.

**L'astérisque est réservé à l'éditeur.** Tout champ commençant par `*` n'existe que pour
l'éditeur de missions, le moteur de jeu les ignore.

**Les descs auxiliaires.** La notation `#\CHEMIN\fichier` renvoie à un desc partagé : on peut
regrouper dans un fichier à part les paramètres communs à des unités semblables, puis y faire
référence. En cas de doublon, **le desc principal l'emporte** sur l'auxiliaire.

**Les unités de mesure.** Une case de la carte — un losange, une tuile — vaut **32 unités** en
pixels. Pour le temps, **25 unités valent une seconde réelle**. Et **10 points de vie
correspondent à une seconde** : plus une unité a de points de vie, plus son corps reste
longtemps sur le champ de bataille après sa mort.

**Les listes obligatoires.** Le jeu exige la présence de `boomtypes`, `groundtypes`,
`hitsnames`, `priceptypes`, `selunittypes` et `targettypes`. La liste `reinftemplates` sert au
générateur automatique de renforts de l'éditeur : sans elle, le générateur ne fonctionne pas.

## Les types de descs

Le catalogue couvre, outre les unités terrestres et l'aviation, les descs complets des maisons
(`Land\dom`), des éléments de décor (`Land\stand`), des clôtures (`Land\zabor`), ainsi que
`CGAME\cgame_flags`, `MISC\interface`, `MISC\misc`, `MISC\mines`, `MISC\waves`,
`MISC\weather` et `MISC\sounds`.

## Index des champs

| Champ | Arguments |
|---|---|
| `*canbereinf` | `[1,0]` |
| `*comment` | `"Text"` |
| `*guncrewunit` | `[sold_desc]` |
| `*name` | `"Text"` |
| `*nationtype` | `[nation_type]` |
| `*picture` | `[filename.pck filename.col]` |
| `airscandelay` | `[x]` |
| `Alarmrange` | `[x y]` |
| `ammo1` | `[x]` |
| `ammo2` | `[x]` |
| `ammoregendelay` | `a b c d` |
| `ani` | `[x]` |
| `AnimateRun` | `[1,0]` |
| `Aninum` | `[x]` |
| `anireload` | `1 2 -1` |
| `anibuildez1` | `1 2 -1` |
| `anibuildez2` | `1 2 -1` |
| `anifixmost` | `1 2 -1` |
| `anibuildpont` | `2 3 -1` |
| `anispeed` | `Die a b c d` |
| `armor` | `[hittype x y x y x y]` |
| `art` | `[art_descname]` |
| `attackcrew` | `[x]` |
| `attackpref` | `[target x]` |
| `backmovespeed` | `[x y]` |
| `Bigpressrange` | `[1,0]` |
| `Binocular` | `[x у]` |
| `bonus_shotdeadzone` | `[x y]` |
| `bonus_shotrange` | `[x y]` |
| `bonus_sight` | `[x y]` |
| `camouflage` | `[text or digit]` |
| `canattackpoint` | `[0,1,2]` |
| `canbecrew` | `[0,1,2]` |
| `Canbecrushed` | `[1,0]` |
| `canbepara` | `[1,0]` |
| `canbetowed` | `[priseptypes]` |
| `cancrouchexpa` | `[0, never]` |
| `canfirefrominside` | `[1,0]` |
| `canmovebackward` | `[1,0]` |
| `cannotmove` | `[1,0]` |
| `Collisionexplosion` | `[explosion]` |
| `crew_number` | `[x]` |
| `crew_unit` | `[solder_desc]` |
| `crew_ver` | `[x y]` |
| `crewcanbehealed` | `[1,0]` |
| `Crewpickupdir` | `[x]` |
| `Passpickupdir` | `[x]` |
| `crouchmovespeed` | `[x y]` |
| `Crouchtofire` | `[1,0]` |
| `davirange` | `[x y или auto]` |
| `dieexplosion` | `[explosion]` |
| `dirboomtype` | `[boomtype]` |
| `doubletrace` | `[1,0]` |
| `Engine` | `[track, whell]` |
| `Speedfactor` | `[x]` |
| `Expa_crush` | `[x y]` |
| `expa_loosehp` | `[x y]` |
| `expa_reload` | `[x y]` |
| `ez1` | `x………..n` |
| `ez2` | `x………..n` |
| `ez1buildcost` | `[x]` |
| `ez1buildtime` | `[x y]` |
| `ez2buildcost` | `[x]` |
| `ez2buildtime` | `[x y]` |
| `pontbuildcost` | `[x]` |
| `pontbuildtime` | `[x y]` |
| `fixrailcost` | `[x]` |
| `fixrailtime` | `[x]` |
| `file` | `[filename]` |
| `fileupright` | `[desc_file]` |
| `fileupleft` | `[desc_file]` |
| `filedownright` | `[desc_file]` |
| `filedownleft` | `[desc_file]` |
| `fixrailradius` | `[х]` |
| `Fallspeed` | `[x]` |
| `getminetime` | `[x y]` |
| `groundtrace` | `[explosion]` |
| `gunshotwait` | `[x]` |
| `gunturndelay` | `[x]` |
| `Haveladder` | `[1,0]` |
| `havepricep` | `[priceptype] , ... , [priceptype] или all или none` |
| `healdelay` | `[x y]` |
| `health` | `[x]` |
| `icon` | `[x]` |
| `idlesnd_fixmost` | `[soundheader]` |
| `idlesnd_idle` | `[soundheader priority perm\load x y]` |
| `idlesnd_move` | `[soundheader priority perm\load x y]` |
| `Ignoremines` | `[1,0]` |
| `iscruiser` | `[1,0]` |
| `Kamikazepctg` | `[%]` |
| `Laddershowtime` | `[time]` |
| `layminetime` | `[x y]` |
| `Longunit` | `[1,0]` |
| `Marad` | `0..32678` |
| `marchenabled` | `[1,0]` |
| `marchsightbonus` | `[x]` |
| `maxgund` | `[x]` |
| `mech` | `[1,0]` |
| `mineammo` | `[x]` |
| `moraleautoincrease` | `[x]` |
| `moralemax` | `32768` |
| `moralenoattack` | `-18432` |
| `moralerage` | `21845` |
| `moraleresist` | `12288` |
| `moralerndmove` | `-22528` |
| `movecrew` | `[x]` |
| `movedamagehp` | `[x]` |
| `MoveSmoke` | `[anidesc]` |
| `MoveSmokeSound` | `[soundheader]` |
| `movespeed` | `[x y]` |
| `Name` | `"Текст"` |
| `native` | `[nation]` |
| `newtypegaub` | `[1,0]` |
| `OfficerRadius` | `[x y]` |
| `paraani` | `[х]` |
| `paraexplosions` | `[explosion][explosion]` |
| `Paraanicenter` | `[x]` |
| `Paraframedelay` | `[x]` |
| `Passcanfire` | `[1,0]` |
| `permanentanimask` | `[delay_time]` |
| `planeform` | `[avia_desc]` |
| `Pricepaspickup` | `[1,0]` |
| `PricepSpeed` | `[priceptype] [float]` |
| `protection` | `[hittype x y x y x y]` |
| `radboomtype` | `[boomtype]` |
| `radius` | `[x]` |
| `reload1` | `[x y]` |
| `reload2` | `[x y]` |
| `removeexplosion` | `[explosion]` |
| `repair` | `[x y]` |
| `scandelay` | `[x]` |
| `scanrange` | `[x y]` |
| `scoretype` | `[scoretypes]` |
| `scorevalue` | `[x]` |
| `selector` | `[x]` |
| `seltype` | `[selunittypes]` |
| `shortname` | `«Text»` |
| `shot_accuracy` | `[x y]` |
| `shot_animat` | `[ani_desc]` |
| `shot_animation` | `[anidesc]` |
| `shot_burstreloadtime` | `[x y]` |
| `shot_burstshots` | `[x y]` |
| `shot_damage` | `[x y]` |
| `shot_deadzone` | `[x y]` |
| `shot_delay` | `[x,y]` |
| `shot_expa` | `[x y]` |
| `shot_id` | `[shotdesc]` |
| `shot_range` | `[x y]` |
| `shot_reloadtime` | `[x y]` |
| `shot_speed` | `[x y]` |
| `shot_useammo` | `[x y]` |
| `siegesound` | `[soundheader]` |
| `unsiegesound` | `[soundheader]` |
| `siegespeed` | `[x]` |
| `sight` | `[x y]` |
| `smokeani` | `[explosion]` |
| `SoldAngle` | `[a][b][c][d]` |
| `SoldRadius` | `[a][b][c][d]` |
| `SoldDirection` | `[a][b][c][d]` |
| `soldonarmor` | `[solder_desc]` |
| `soldtomove` | `[x]` |
| `soundtype` | `[soundmaker]` |
| `Spyfurg` | `[x]` |
| `stock` | `[x]` |
| `targettype` | `[targettypes]` |
| `turndelay` | `[x y]` |
| `turret_type` | `[turret_type]` |
| `turret_0_unit` | `[desc_file]` |
| `turret_1_unit` | `[desc_file]` |
| `turret_2_unit` | `[desc_file]` |
| `TwoSoldBonus` | `[reload, burstreload, accuracy]` |
| `walkonground` | `[1,0]` |
| `walkonwater` | `[1,0]` |
| `walkonshallows` | `[1,0]` |
| `watertrace` | `[explosion]` |
| `actiontime` | `[x]` |
| `altitude` | `[x]` |
| `bombaccuracy` | `[x]` |
| `bombaltitude` | `[x]` |
| `bombdamage` | `[x]` |
| `bombdistance` | `[x]` |
| `Bombflyspeed` | `[x]` |
| `bombid` | `[shot_desc]` |
| `bombreloadtime` | `[x]` |
| `bombsnumber` | `[x]` |
| `bombspeed` | `[x]` |
| `Bombstartdistance` | `[x]` |
| `crashtime` | `[x]` |
| `dropflyspeed` | `[x]` |
| `dropaltitude` | `[x]` |
| `explosion` | `[explosion]` |
| `falldownspeed` | `[x]` |
| `fallsmoke` | `[explosion]` |
| `flysmoke` | `[explosion]` |
| `flyspeed` | `[x]` |
| `Fuel` | `[x]` |
| `maxdistance` | `[x]` |
| `para` | `[para_desc]` |
| `shot_grn_accuracy` | `[x]` |
| `shot_grn_altitude` | `[x]` |
| `shot_grn_ammo` | `[x]` |
| `shot_grn_burstreload` | `[x]` |
| `shot_grn_burstshots` | `[x]` |
| `shot_grn_damage` | `[x]` |
| `shot_grn_flyspeed` | `[x]` |
| `shot_grn_id` | `[shot_desc]` |
| `shot_grn_maxddir` | `[x]` |
| `shot_grn_maxdistance` | `[x]` |
| `shot_grn_mindistance` | `[x]` |
| `shot_grn_reload` | `[x]` |
| `shot_grn_scanradius` | `[x]` |
| `shot_grn_speed` | `[x]` |
| `shot_grn_useammo` | `[x]` |
| `Shotanimation` | `[ani_desc]` |
| `spyflyspeed` | `[x]` |
| `turnspeed` | `[x]` |
| `Unitform` | `[avia_ground_desc]` |
| `Abjectiveshot` | `[1,0]` |
| `Body` | `[animat]` |
| `Checkstolb` | `[1,0]` |
| `Destroyland` | `[landnames landnames… ]` |
| `Dz` | `[x]` |
| `Explosionrnd` | `[x]` |
| `Hitid` | `[hitsnames]` |
| `Sled` | `[1,0] [animat] [fl layer] [a b c d]` |
| `Sled2x` | `[1,0]` |
| `Useh` | `[x]` |
| `Animats` | `[x]` |
| `animat_x` | `[animat] [fl_layer] [a b c d]` |
| `Addshot` | `[shots]` |
| `Addshotaccuracy` | `[x y]` |
| `Addshotdelay` | `[x y]` |
| `Addshotdmg` | `[x]` |
| `Addshotnum` | `[x y]` |
| `Addshotrnd` | `[x]` |
| `Nodamage` | `[1,0]` |
| `Vor` | `[№]` |
| `Anifilename` | `[x y]` |

## Ce que ce document apporte à `format-aps.md`

Les deux se complètent sans se recouvrir. `format-aps.md` décrit le **conteneur** : la structure
FZFF, les flux zlib concaténés, ce que contient chaque type de fichier `.aps`, et la
désynchronisation entre `lang.aps` et les copies des fichiers d'environnement. Le présent
document décrit le **contenu** : la grammaire des fiches et les 238 champs qu'on y trouve.

Lire l'un sans l'autre laisse à mi-chemin : le premier ouvre l'archive, le second explique ce
qu'on y lit.
