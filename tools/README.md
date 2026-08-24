# Hidden Stroke II — Modding Tools

Two zero-dependency tools (Python 3.8+, standard library only). Both open a GUI
in your web browser and work the same on macOS and Windows.

| Tool | Launch (macOS) | Launch (Windows) |
|---|---|---|
| **Mission Editor** — edit support convoys, experience, players, scripts of every map | double-click `Mission Editor.command` or run `python3 hs2_mission_editor.py` | double-click `Mission Editor.bat` |
| **APS Tool** — unpack / repack `lang.aps` (and any other FZFF archive) | double-click `APS Tool.command` or run `python3 hs2_aps_tool.py` | double-click `APS Tool.bat` |

Stop either tool with `Ctrl+C` in the terminal window (or just close it).

---

## 1. Mission Editor (`hs2_mission_editor.py`)

Edits the map-editor source files under
`Run/APRM WW II_Edit/maps_ap.src/map.XXX/mis.YYY/`.

- **Support tab** — the reinforcement convoys (`support` file): every unit's
  `HP / Ammo / Expa / Morale / Lives / Grp / Crew / In`, with a tooltip on every
  column, an autocomplete on unit IDs (with the unit's full name shown), the
  16 entry flags, and a **bulk edit** bar ("set Expa of the whole mission to 50").
- **Nation balance panel** (top of the Support tab) — per-nation **Overall** and
  **AT Skill** totals over every rated unit of the mission (support convoys,
  passengers, paradrop packages), with the Unit Comparator's balance rule:
  gap = (max−min)/max, `<15 %` balanced, `≤30 %` moderate, `>30 %` strong
  imbalance. Scores come straight from `Tools/HS2_Unit_Comparator_*.html`
  (latest version found is used; units are joined by their `name` field), so the
  numbers match the comparator exactly. Each support block header also shows its
  Overall / AT totals, and unit-name tooltips carry the unit's nation and scores.
  Infantry, guns and planes are not rated by the comparator and are counted
  separately as "unrated".
- **Group nations (allies)** — same mechanics as the comparator: click "Group
  nations", pick 2+ nations in the Overall row (e.g. French + American +
  British), Validate — their scores merge into one entry before the balance is
  evaluated. "Reset groups" ungroups. Unlike the comparator, groups are
  remembered (localStorage) across missions and reloads.
- **Players tab** — the `players` file: plane flights (bomber / spy / transport /
  boxer / interceptor: Number, Bombs, Reload in seconds) and the two paradrop
  packages per player, including their **expa** (experience).
- **Scripts tab** — the `scripts2` file, with the **⏱ Support arrival timings**
  table on top: every reinforcement delay found in the scripts (timed reserves,
  flag-triggered reserves, script trigger timers) shown in plain seconds with a
  min:sec conversion — edit the number and the script text updates itself.
  The `size` byte-count in each script header is **recomputed automatically on
  save** (the #1 way to corrupt a mission when editing by hand). Numbers after
  `#` are stored digit-reversed (`#006` = 600 s); a read-only decoded preview
  is available.
- **Mission info tab** — `misdesc` (lobby text) + the minimap.
- **❓ Parameter help tab** — meaning and valid range of every field, verified
  against the 200+ missions of this install.

Safety:
- Every save first copies the old file to `Tools/backups/<map>/<mis>/<file>.<timestamp>`.
- On load, each file is parsed and re-serialized; only if the result is
  byte-identical is structured editing enabled — otherwise the tab falls back to
  raw-text editing so the tool can never mangle an unusual file.
- Unedited lines are written back byte-for-byte; an edit touches only its own line.

After editing, open the map in the map editor and re-save it so the game picks
up the changes.

To point it at a different maps folder:
`python3 hs2_mission_editor.py "/path/to/maps_ap.src"`.

## 2. APS Tool (`hs2_aps_tool.py`)

Unpacks and repacks the game's FZFF `.aps` archives. Presets are filled in for
the main use case: **lang.aps ⇄ Modding/UNITS** (779 unit definition files).
Also works on the other sections (EXPLOSIONS, SHOTS, ANIMAT, AVIA, MISC…) and
other `.aps` archives found under `Run/`.

- **Unpack**: extracts a section (or everything) to a folder. "Flat" drops the
  section prefix so `UNITS\zis-2` becomes `Modding/UNITS/zis-2`.
- **Repack**: rebuilds the archive using the original as template — files from
  your folder replace the matching entries, new files are added, and entries you
  did not touch are carried over unchanged. A timestamped backup
  (`lang.aps.bak-YYYYMMDD-HHMMSS`) is written first, and the new archive is
  fully re-read and verified; on any mismatch the original is restored.
- **Unit stats**: type a unit id (autocompleted from `Modding/UNITS`) and see
  its values interpreted exactly as in the Unit Comparator HTML — armor per
  side, penetration, range, accuracy, reload, Overall and AT Skill — including
  the comparator's armor color rule (red `<43 mm`, orange `≤50 mm`). Reads the
  latest `Tools/HS2_Unit_Comparator_*.html` at startup.

Long operations run in the background with live progress in the log — the page
never hangs on a request, and section listings read only the archive directory,
so even the 80 MB terrain archives list instantly. If the log ever says it
cannot reach the server, the tool's terminal window was closed: relaunch it and
reload the page.

Command line (same engine):

```bash
python3 hs2_aps_tool.py list   "../Run/APRM/lang.aps"
python3 hs2_aps_tool.py unpack "../Run/APRM/lang.aps" --only UNITS --flat --out "../Modding/UNITS"
python3 hs2_aps_tool.py pack   "../Run/APRM/lang.aps" --section UNITS --from "../Modding/UNITS"
```

### FZFF format (reverse-engineered)

`"FZFF"` + u32 body length; body = each file's data deflate-compressed in
16 KB chunks, zlib streams back to back (0-byte files have no stream); then a
compressed directory of 20-byte records `(name_offset, 8, index+streams_before,
size, 16384)` and a compressed `\0`-separated name table (cp1252, `\` paths).
Verified by byte-identical extraction of all 1562 entries of `lang.aps`.
