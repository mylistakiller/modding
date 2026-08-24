#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hs2_mission_editor.py — GUI editor for Hidden Stroke II map-editor mission files
(maps_ap.src/map.XXX/mis.YYY : support, players, scripts2, misdesc).

Run it, a browser page opens:
    python3 hs2_mission_editor.py            (macOS / Linux)
    py hs2_mission_editor.py                 (Windows)

- Browse every map / mission, see the minimap and description.
- Edit support convoys: every unit's HP / Ammo / Expa / Morale / Lives /
  Grp / Crew / In, with explanations and observed ranges for each field,
  plus bulk operations ("set Expa of everything to 50").
- Edit players: plane flights and paradrop packages (incl. experience).
- Edit scripts safely: the "size" byte-count header is recomputed for you.
- Every save first writes a timestamped backup under Tools/backups/.

Stdlib only, works on macOS and Windows (Python 3.8+).
"""

import datetime
import json
import re
import shutil
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ENC = "cp1252"
SCRIPT_DIR = Path(__file__).resolve().parent
GAME_ROOT = SCRIPT_DIR.parent
MAPS_DIR = GAME_ROOT / "Run" / "APRM WW II_Edit" / "maps_ap.src"
UNITS_DIR = GAME_ROOT / "Modding" / "UNITS"
BACKUP_DIR = SCRIPT_DIR / "backups"

# allow overriding the maps folder:  python3 hs2_mission_editor.py /path/to/maps_ap.src
if len(sys.argv) > 1 and Path(sys.argv[1]).is_dir():
    MAPS_DIR = Path(sys.argv[1])


# ----------------------------------------------------------------------------
# support file : 16 "flag" lines, blank line, 64 blocks
#   support "name"
#    ID=... HP=. Ammo=. Expa=. Morale=. Lives=. Grp=. [Crew=.] [In=.]
#     ID=...            (2 spaces = passenger of the unit above)
#   end
# ----------------------------------------------------------------------------

UNIT_RE = re.compile(
    r"^( {1,2})ID=(\S+) HP=(-?\d+) Ammo=(-?\d+) Expa=(-?\d+) Morale=(-?\d+)"
    r" Lives=(-?\d+) Grp=(-?\d+)(?: Crew=(-?\d+))?(?: In=(-?\d+))? ?$"
)


def parse_support(text):
    flags, blocks = [], []
    cur = None
    for line in text.split("\n"):
        if line.startswith("flag "):
            vals = [int(x) for x in line[5:].split(",")]
            flags.append({"raw": line, "vals": vals, "dirty": False})
        elif line.startswith('support "'):
            cur = {"name": line[9 : line.rindex('"')], "units": []}
            blocks.append(cur)
        elif line == "end":
            cur = None
        elif line.strip() == "":
            continue
        else:
            m = UNIT_RE.match(line)
            if not m or cur is None:
                raise ValueError("unrecognised support line: %r" % line)
            unit = {
                "raw": line,
                "dirty": False,
                "id": m.group(2),
                "hp": int(m.group(3)),
                "ammo": int(m.group(4)),
                "expa": int(m.group(5)),
                "morale": int(m.group(6)),
                "lives": int(m.group(7)),
                "grp": int(m.group(8)),
                "crew": int(m.group(9)) if m.group(9) is not None else None,
                "inn": int(m.group(10)) if m.group(10) is not None else None,
            }
            if m.group(1) == " ":
                unit["passengers"] = []
                cur["units"].append(unit)
            else:
                if not cur["units"]:
                    raise ValueError("passenger with no transport: %r" % line)
                cur["units"][-1]["passengers"].append(unit)
    return {"flags": flags, "blocks": blocks}


def fmt_unit(u, indent):
    s = "%sID=%s HP=%d Ammo=%d Expa=%d Morale=%d Lives=%d Grp=%d" % (
        " " * indent,
        u["id"],
        u["hp"],
        u["ammo"],
        u["expa"],
        u["morale"],
        u["lives"],
        u["grp"],
    )
    if u.get("crew") is not None:
        s += " Crew=%d" % u["crew"]
    if u.get("inn") is not None:
        s += " In=%d" % u["inn"]
    if indent == 1:
        s += " "  # top-level lines carry a trailing space in editor output
    return s


def serialize_support(obj):
    lines = []
    for f in obj["flags"]:
        if f.get("dirty") or "raw" not in f:
            lines.append("flag " + ",".join(str(v) for v in f["vals"]))
        else:
            lines.append(f["raw"])
    lines.append("")
    for b in obj["blocks"]:
        lines.append('support "%s"' % b["name"])
        for u in b["units"]:
            lines.append(
                u["raw"] if not u.get("dirty") and u.get("raw") else fmt_unit(u, 1)
            )
            for p in u.get("passengers", []):
                lines.append(
                    p["raw"] if not p.get("dirty") and p.get("raw") else fmt_unit(p, 2)
                )
        lines.append("end")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------
# players file (rigid layout written by the map editor)
# ----------------------------------------------------------------------------


def parse_players(text):
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    players = []
    i = 0

    def expect(pat):
        nonlocal i
        m = re.match(pat, lines[i])
        if not m:
            raise ValueError("players: expected %r got %r" % (pat, lines[i]))
        i += 1
        return m

    while i < len(lines):
        m = expect(r"^Player (\d+)$")
        p = {"num": int(m.group(1))}
        p["name"] = expect(r'^ name="([^"]*)"$').group(1)
        p["team"] = int(expect(r"^ team=(-?\d+)$").group(1))
        p["nation"] = int(expect(r"^ nation=(-?\d+)$").group(1))
        p["color"] = [
            int(x) for x in expect(r"^ color=(-?\d+) (-?\d+) (-?\d+)$").groups()
        ]
        p["planes"] = []
        while i < len(lines) and lines[i].startswith(" plane "):
            t = lines[i][7:]
            i += 1
            pl = {"type": t}
            pl["id"] = expect(r"^  ID=(\S*)$").group(1)
            pl["number"] = int(expect(r"^  Number=(-?\d+)$").group(1))
            pl["bombs"] = int(expect(r"^  Bombs=(-?\d+)$").group(1))
            pl["reload"] = int(expect(r"^  Reload=(-?\d+)$").group(1))
            p["planes"].append(pl)
        p["descents"] = []
        while i < len(lines) and lines[i].startswith(" descent "):
            d = {"num": int(lines[i][9:])}
            i += 1
            d["group"] = int(expect(r"^  group=(-?\d+)$").group(1))
            d["expa"] = int(expect(r"^  expa=(-?\d+)$").group(1))
            d["slots"] = []
            while i < len(lines) and re.match(r"^  ID \d+=", lines[i]):
                sid = expect(r"^  ID \d+=(\S*)$").group(1)
                num = int(expect(r"^  number \d+=(-?\d+)$").group(1))
                d["slots"].append({"id": sid, "number": num})
            p["descents"].append(d)
        p["planesdir"] = int(expect(r"^ planesdir=(-?\d+)$").group(1))
        players.append(p)
    return {"players": players}


def serialize_players(obj):
    out = []
    for p in obj["players"]:
        out.append("Player %d" % p["num"])
        out.append(' name="%s"' % p["name"])
        out.append(" team=%d" % p["team"])
        out.append(" nation=%d" % p["nation"])
        out.append(" color=%d %d %d" % tuple(p["color"]))
        for pl in p["planes"]:
            out.append(" plane %s" % pl["type"])
            out.append("  ID=%s" % pl["id"])
            out.append("  Number=%d" % pl["number"])
            out.append("  Bombs=%d" % pl["bombs"])
            out.append("  Reload=%d" % pl["reload"])
        for d in p["descents"]:
            out.append(" descent %d" % d["num"])
            out.append("  group=%d" % d["group"])
            out.append("  expa=%d" % d["expa"])
            for k, s in enumerate(d["slots"]):
                out.append("  ID %d=%s" % (k, s["id"]))
                out.append("  number %d=%d" % (k, s["number"]))
        out.append(" planesdir=%d" % p["planesdir"])
    return "\n".join(out) + "\n"


# ----------------------------------------------------------------------------
# scripts2 file : records 'script "name" size N\n<N payload bytes>'
# joined by \r\n (payload lines themselves are \n)
# ----------------------------------------------------------------------------


def parse_scripts(raw_bytes):
    scripts = []
    rest = raw_bytes
    while rest:
        m = re.match(rb'script "([^"]*)" size (\d+)\n', rest)
        if not m:
            raise ValueError("scripts2: bad record header: %r" % rest[:40])
        size = int(m.group(2))
        payload = rest[m.end() : m.end() + size]
        if len(payload) != size:
            raise ValueError("scripts2: truncated payload")
        scripts.append({"name": m.group(1).decode(ENC), "text": payload.decode(ENC)})
        rest = rest[m.end() + size :]
        if rest[:2] != b"\r\n":
            raise ValueError("scripts2: missing record separator")
        rest = rest[2:]
    return {"scripts": scripts}


def serialize_scripts(obj):
    out = bytearray()
    for s in obj["scripts"]:
        payload = s["text"].replace("\r\n", "\n").encode(ENC, "replace")
        out += b'script "%s" size %d\n' % (
            s["name"].encode(ENC, "replace"),
            len(payload),
        )
        out += payload
        out += b"\r\n"
    return bytes(out)


# ----------------------------------------------------------------------------
# unit index (names from Modding/UNITS)
# ----------------------------------------------------------------------------

_unit_cache = None


def unit_index():
    global _unit_cache
    if _unit_cache is not None:
        return _unit_cache
    idx = {}
    if UNITS_DIR.is_dir():
        for f in UNITS_DIR.iterdir():
            if not f.is_file() or f.name.startswith("."):
                continue
            name = short = ""
            try:
                head = f.read_bytes()[:4096].decode(ENC, "replace")
                m = re.search(r'^name "([^"]*)"', head, re.M)
                if m:
                    name = m.group(1)
                m = re.search(r'^shortname "([^"]*)"', head, re.M)
                if m:
                    short = m.group(1)
            except OSError:
                pass
            idx[f.name] = [name, short]
    _unit_cache = idx
    return idx


# ----------------------------------------------------------------------------
# unit stats from the HS2 Unit Comparator HTML (Tools/HS2_Unit_Comparator_*.html)
# The comparator embeds `const units=[...]` — 250+ rated units with the computed
# Overall and AT Skill scores. We join on the `name "..."` field of the unit
# files, so the scores shown here are exactly the comparator's.
# ----------------------------------------------------------------------------

_stats_cache = None


def comparator_rows():
    """Raw comparator rows keyed by unit display name (latest comparator wins)."""
    files = sorted(SCRIPT_DIR.glob("HS2_Unit_Comparator_*.html"))
    if not files:
        return {}, None
    src = files[-1]
    try:
        html = src.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"const units=(\[.*?\]);", html, re.S)
        rows = json.loads(m.group(1)) if m else []
    except (OSError, ValueError):
        return {}, None
    by_name = {}
    for r in rows:
        # one comparator name carries a stray leading quote — strip it
        nm = (r.get("Nom de l'unité") or "").lstrip('"').strip()
        by_name.setdefault(nm, r)
    return by_name, src.name


def unit_stats():
    """unit-file id -> {nation, overall, at} from the comparator."""
    global _stats_cache
    if _stats_cache is not None:
        return _stats_cache
    by_name, src = comparator_rows()
    stats = {}
    for uid, (name, _short) in unit_index().items():
        r = by_name.get(name)
        if r:
            stats[uid] = {
                "nation": r.get("Nation") or "Other",
                "overall": r.get("Overall") or 0,
                "at": r.get("AT Skill") or 0,
            }
    _stats_cache = {"units": stats, "source": src}
    return _stats_cache


# ----------------------------------------------------------------------------
# missions
# ----------------------------------------------------------------------------


def read_text(path):
    return path.read_bytes().decode(ENC)


def list_maps():
    maps = []
    if not MAPS_DIR.is_dir():
        return maps
    for mp in sorted(MAPS_DIR.iterdir()):
        if not mp.is_dir() or not mp.name.startswith("map."):
            continue
        desc = ""
        if (mp / "desc").is_file():
            desc = read_text(mp / "desc").strip()
        missions = []
        for ms in sorted(mp.iterdir()):
            if ms.is_dir() and ms.name.startswith("mis."):
                mdesc = ""
                if (ms / "desc").is_file():
                    mdesc = read_text(ms / "desc").strip()
                missions.append({"id": ms.name, "desc": mdesc})
        maps.append({"id": mp.name, "desc": desc, "missions": missions})
    return maps


def mission_dir(map_id, mis_id):
    d = (MAPS_DIR / map_id / mis_id).resolve()
    if not str(d).startswith(str(MAPS_DIR.resolve())) or not d.is_dir():
        raise ValueError("bad mission path")
    return d


def load_mission(map_id, mis_id):
    d = mission_dir(map_id, mis_id)
    res = {"map": map_id, "mis": mis_id}

    res["misdesc"] = read_text(d / "misdesc") if (d / "misdesc").is_file() else ""
    res["has_image"] = (d / "JPG1024.jpg").is_file()

    # support
    sup = d / "support"
    if sup.is_file():
        raw = read_text(sup)
        try:
            obj = parse_support(raw)
            ok = serialize_support(obj) == raw
            res["support"] = obj if ok else None
            res["support_roundtrip"] = ok
        except ValueError:
            res["support"] = None
            res["support_roundtrip"] = False
        res["support_raw"] = raw
    else:
        res["support"] = None
        res["support_raw"] = None

    # players
    ply = d / "players"
    if ply.is_file():
        raw = read_text(ply)
        try:
            obj = parse_players(raw)
            ok = serialize_players(obj) == raw
            res["players"] = obj if ok else None
            res["players_roundtrip"] = ok
        except ValueError:
            res["players"] = None
            res["players_roundtrip"] = False
        res["players_raw"] = raw
    else:
        res["players"] = None
        res["players_raw"] = None

    # scripts2
    scr = d / "scripts2"
    if scr.is_file():
        raw_b = scr.read_bytes()
        try:
            obj = parse_scripts(raw_b)
            ok = serialize_scripts(obj) == raw_b
            res["scripts"] = obj if ok else None
            res["scripts_roundtrip"] = ok
        except ValueError:
            res["scripts"] = None
            res["scripts_roundtrip"] = False
        res["scripts_raw"] = raw_b.decode(ENC)
    else:
        res["scripts"] = None
        res["scripts_raw"] = None

    return res


def backup(path, map_id, mis_id):
    dst_dir = BACKUP_DIR / map_id / mis_id
    dst_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = dst_dir / ("%s.%s" % (path.name, ts))
    shutil.copy2(path, dst)
    return dst


def save_file(map_id, mis_id, which, mode, data):
    d = mission_dir(map_id, mis_id)
    if which == "support":
        path = d / "support"
        blob = (serialize_support(data) if mode == "structured" else data).encode(
            ENC, "replace"
        )
        if mode == "structured":
            parse_support(blob.decode(ENC))  # self-check before writing
    elif which == "players":
        path = d / "players"
        blob = (serialize_players(data) if mode == "structured" else data).encode(
            ENC, "replace"
        )
        if mode == "structured":
            parse_players(blob.decode(ENC))
    elif which == "scripts2":
        path = d / "scripts2"
        blob = (
            serialize_scripts(data)
            if mode == "structured"
            else data.encode(ENC, "replace")
        )
        if mode == "structured":
            parse_scripts(blob)
    elif which == "misdesc":
        path = d / "misdesc"
        blob = data.encode(ENC, "replace")
    else:
        raise ValueError("unknown file: %s" % which)

    bak = backup(path, map_id, mis_id) if path.exists() else None
    path.write_bytes(blob)
    return {"saved": str(path), "backup": str(bak) if bak else None, "bytes": len(blob)}


# ----------------------------------------------------------------------------
# HTTP server
# ----------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, "application/json", json.dumps(obj).encode("utf-8"))

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs

        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        try:
            if u.path == "/":
                self._send(200, "text/html; charset=utf-8", HTML.encode("utf-8"))
            elif u.path == "/api/state":
                self._json(
                    {
                        "root": str(GAME_ROOT),
                        "maps_dir": str(MAPS_DIR),
                        "maps": list_maps(),
                        "units_count": len(unit_index()),
                    }
                )
            elif u.path == "/api/units":
                self._json(unit_index())
            elif u.path == "/api/stats":
                self._json(unit_stats())
            elif u.path == "/api/mission":
                self._json(load_mission(q["map"], q["mis"]))
            elif u.path == "/img":
                p = mission_dir(q["map"], q["mis"]) / "JPG1024.jpg"
                blob = p.read_bytes()
                # most minimaps carry a 12-byte game header before the JPEG
                j = blob.find(b"\xff\xd8", 0, 64)
                if j < 0:
                    self._send(404, "text/plain", b"minimap not in JPEG format")
                else:
                    self._send(200, "image/jpeg", blob[j:])
            else:
                self._send(404, "text/plain", b"not found")
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/save":
                res = save_file(
                    req["map"], req["mis"], req["file"], req["mode"], req["data"]
                )
                self._json(res)
            else:
                self._json({"error": "unknown endpoint"}, 404)
        except Exception as e:  # noqa: BLE001
            self._json({"error": str(e)}, 500)


HTML = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>HS2 Mission Editor</title>
<style>
:root { --bg:#14171c; --panel:#1d2129; --panel2:#232834; --line:#2c313c;
  --tx:#d7dbe2; --dim:#8a91a0; --acc:#5aa0e8; --ok:#5cbf74; --warn:#e8b45a;
  --err:#e86a5a; --exp:#c792ea; }
* { box-sizing:border-box; }
body { margin:0; font:13px/1.45 -apple-system,'Segoe UI',Roboto,sans-serif;
  background:var(--bg); color:var(--tx); display:flex; height:100vh; overflow:hidden; }
#sidebar { width:290px; min-width:290px; background:var(--panel);
  border-right:1px solid var(--line); display:flex; flex-direction:column; }
#sidebar h1 { font-size:15px; margin:0; padding:14px 14px 8px; }
#sidebar h1 span { color:var(--dim); font-weight:normal; font-size:11px; display:block; }
#filter { margin:0 12px 8px; padding:6px 10px; background:#12151a; color:var(--tx);
  border:1px solid var(--line); border-radius:6px; font:inherit; }
#maplist { overflow-y:auto; flex:1; padding:0 6px 12px; }
.mapitem { padding:5px 8px; border-radius:6px; cursor:pointer; }
.mapitem:hover { background:var(--panel2); }
.mapitem .mid { color:var(--dim); font-size:11px; }
.misitem { padding:4px 8px 4px 22px; border-radius:6px; cursor:pointer; font-size:12px; }
.misitem:hover, .misitem.active { background:var(--acc); color:#fff; }
#main { flex:1; overflow-y:auto; padding:18px 26px; }
h2 { font-size:17px; margin:0 0 2px; }
.crumb { color:var(--dim); font-size:12px; margin-bottom:10px; }
.tabs { display:flex; gap:4px; margin:14px 0 0; border-bottom:1px solid var(--line); }
.tab { padding:7px 16px; cursor:pointer; border-radius:8px 8px 0 0; color:var(--dim); }
.tab.active { background:var(--panel); color:var(--tx); border:1px solid var(--line);
  border-bottom-color:var(--panel); }
.pane { display:none; background:var(--panel); border:1px solid var(--line);
  border-top:none; border-radius:0 0 10px 10px; padding:16px; }
.pane.active { display:block; }
button { background:var(--acc); color:#fff; border:none; border-radius:6px;
  padding:7px 14px; font:inherit; font-weight:600; cursor:pointer; }
button.small { padding:2px 8px; font-size:11px; font-weight:normal; }
button.ghost { background:#333a47; }
button.danger { background:var(--err); }
button:disabled { opacity:.4; cursor:default; }
input.num { width:52px; background:#12151a; color:var(--tx); text-align:center;
  border:1px solid var(--line); border-radius:4px; padding:3px 2px; font:inherit; }
input.num.neg { color:var(--dim); }
input.num.mod, input.txt.mod, select.mod { border-color:var(--warn); }
input.txt { background:#12151a; color:var(--tx); border:1px solid var(--line);
  border-radius:4px; padding:3px 6px; font:inherit; }
select { background:#12151a; color:var(--tx); border:1px solid var(--line);
  border-radius:4px; padding:4px 6px; font:inherit; }
table.units { border-collapse:collapse; width:100%; margin:4px 0 10px; }
table.units th { color:var(--dim); font-size:11px; text-transform:uppercase;
  letter-spacing:.4px; text-align:center; padding:3px 4px; cursor:help; }
table.units th:first-child, table.units th:nth-child(2) { text-align:left; }
table.units td { padding:2px 4px; border-top:1px solid #262b35; text-align:center; }
table.units td.idcell { text-align:left; white-space:nowrap; }
table.units td.namecell { text-align:left; color:var(--dim); font-size:12px;
  max-width:210px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
tr.passenger td.idcell { padding-left:26px; }
tr.passenger { background:#191d25; }
.block { border:1px solid var(--line); border-radius:8px; margin:10px 0;
  background:var(--panel2); }
.block > .bh { padding:8px 12px; cursor:pointer; display:flex; gap:10px;
  align-items:center; }
.block > .bh b { color:var(--acc); }
.block > .bh .cnt { color:var(--dim); font-size:12px; }
.block > .bc { padding:0 12px 10px; display:none; overflow-x:auto; }
.block.open > .bc { display:block; }
.bulk { background:var(--panel2); border:1px solid var(--line); border-radius:8px;
  padding:10px 12px; display:flex; gap:10px; align-items:center; flex-wrap:wrap;
  margin-bottom:12px; }
.bulk label { color:var(--dim); font-size:12px; }
.savebar { position:sticky; top:0; z-index:5; display:flex; gap:10px; align-items:center;
  background:var(--bg); padding:8px 0; }
.savemsg { font-size:12px; color:var(--dim); }
.savemsg.ok { color:var(--ok); } .savemsg.err { color:var(--err); }
textarea { width:100%; background:#12151a; color:var(--tx); border:1px solid var(--line);
  border-radius:6px; padding:8px 10px; font:12px/1.5 ui-monospace,Menlo,Consolas,monospace; }
.help-table { border-collapse:collapse; margin:6px 0 18px; }
.help-table td, .help-table th { border:1px solid var(--line); padding:6px 10px;
  vertical-align:top; text-align:left; }
.help-table th { background:var(--panel2); }
.help-table td:first-child { font-weight:600; color:var(--acc); white-space:nowrap; }
.help-table .rng { color:var(--warn); white-space:nowrap; }
.badge { font-size:10px; background:#333a47; border-radius:4px; padding:1px 6px;
  color:var(--dim); }
.pcard { border:1px solid var(--line); border-radius:8px; background:var(--panel2);
  padding:10px 14px; margin:10px 0; }
.pcard h3 { margin:0 0 6px; font-size:14px; }
.pcard h4 { margin:10px 0 4px; font-size:12px; color:var(--dim);
  text-transform:uppercase; letter-spacing:.4px; }
.swatch { display:inline-block; width:14px; height:14px; border-radius:3px;
  vertical-align:-2px; margin-left:6px; border:1px solid #0006; }
.exp { color:var(--exp); font-weight:600; }
.minimap { max-width:280px; border-radius:8px; border:1px solid var(--line);
  cursor:zoom-in; }
.minimap.big { max-width:100%; cursor:zoom-out; }
.misdesc { white-space:pre-wrap; background:#12151a; border-radius:8px;
  padding:10px 14px; color:var(--dim); font-size:12px; }
.warnbox { background:#3a2f1a; border:1px solid var(--warn); color:var(--warn);
  border-radius:8px; padding:8px 12px; margin-bottom:10px; font-size:12px; }
.script { border:1px solid var(--line); border-radius:8px; background:var(--panel2);
  padding:8px 12px; margin:8px 0; }
.flexrow { display:flex; gap:18px; flex-wrap:wrap; }
abbr { cursor:help; text-decoration:underline dotted var(--dim); }
#welcome { color:var(--dim); max-width:640px; }
#welcome h2 { color:var(--tx); }
.balwrap { border:1px solid var(--line); border-radius:8px; background:var(--panel2);
  padding:10px 12px; margin-bottom:12px; }
.balwrap h4 { margin:0 0 6px; font-size:12px; color:var(--dim);
  text-transform:uppercase; letter-spacing:.4px; }
.balcards { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:6px; }
.balcard { background:#12151a; border:1px solid var(--line); border-radius:6px;
  padding:6px 10px; font-size:12px; }
.balcard span { color:var(--dim); display:block; }
.balcard strong { font-size:13px; }
.balcard.pickable { cursor:pointer; border-color:var(--acc); }
.balcard.pickable:hover { background:#1a2230; }
.balcard.pending { outline:2px solid var(--acc); }
.balcard.grouped { border-color:var(--ok); }
.balstatus { font-size:12px; font-weight:600; margin:2px 0 8px; }
.balstatus.ok { color:var(--ok); } .balstatus.warn { color:var(--warn); }
.balstatus.err { color:var(--err); }
.balnote { color:var(--dim); font-size:11px; }
</style></head><body>

<div id="sidebar">
  <h1>HS2 Mission Editor<span id="rootinfo"></span></h1>
  <input id="filter" placeholder="Filter maps… (name or number)">
  <div id="maplist"></div>
</div>

<div id="main">
  <div id="welcome">
    <h2>Pick a mission on the left</h2>
    <p>Each map (<code>map.XXX</code>) holds one or more missions
    (<code>mis.YYY</code>). Select one to edit its reinforcement convoys
    (<b>support</b>), its <b>players</b> (planes, paradrops, experience) and its
    <b>scripts</b>.</p>
    <p>Every save writes a timestamped backup in <code>Tools/backups/</code> first,
    so nothing is ever lost. To make the game use your changes, save the map from
    the map editor afterwards (the editor reads these source files).</p>
  </div>
  <div id="editor" style="display:none"></div>
</div>

<datalist id="unitids"></datalist>

<script>
"use strict";
const $ = s => document.querySelector(s);
let STATE=null, UNITS={}, CUR=null, M=null; // M = loaded mission data
let STATS={}, STATSRC=null; // comparator scores: unit id -> {nation,overall,at}

const FIELD_HELP = {
  hp:    "HP — starting health, in % of the unit's max health.\nRange -1…100. 100 = intact, low values = spawns damaged. -1 = default (full).",
  ammo:  "Ammo — starting ammunition, in % of max capacity.\nRange -1…100. -1 = default (full).",
  expa:  "Expa — EXPERIENCE (veterancy), 0…100 %.\n-1 = default (passengers usually inherit / start at 0).\nHigher experience = better accuracy, faster reactions, higher rank in game.\nCommon values in APRM: 0, 30, 40, 45, 50 … up to 100 for elites.",
  morale:"Morale — 0…100 %. -1 = default (≈50).\nUnits with low morale panic and rout more easily under fire.",
  lives: "Lives — almost always 0 (100 on a few missions).\nExact effect uncertain; recommended to leave unchanged.",
  grp:   "Grp — AI/control group number the unit joins on arrival.\n-1 = no group. Observed range 0…99.",
  crew:  "Crew — number of crew soldiers manning this vehicle/gun.\n0 = arrives empty (abandoned). Observed 0…31.\nOnly present on top-level (transport) lines.",
  inn:   "In — number of loaded passengers: the indented lines that follow ride inside this unit.\nObserved 1…30. Keep it equal to the number of passenger lines."
};
const FIELDS = ["hp","ammo","expa","morale","lives","grp","crew","inn"];
const FLABEL = {hp:"HP", ammo:"Ammo", expa:"Expa", morale:"Morale",
                lives:"Lives", grp:"Grp", crew:"Crew", inn:"In"};

const sleep = ms => new Promise(r=>setTimeout(r,ms));
async function api(path, body){
  let lastErr;
  for (let attempt=0; attempt<3; attempt++){
    try {
      const r = await fetch(path, body?{method:"POST",body:JSON.stringify(body)}:{});
      const j = await r.json();
      if (j.error) throw new Error(j.error);
      return j;
    } catch(e){
      lastErr=e;
      if (!(e instanceof TypeError)) throw e;  // server-side error: don't retry
      await sleep(600);
    }
  }
  throw new Error("cannot reach the Mission Editor server — its terminal window "+
    "was probably closed. Relaunch it and reload this page. ("+lastErr.message+")");
}

/* ---------- sidebar ---------- */
function renderMapList(){
  const f = $("#filter").value.toLowerCase();
  const el = $("#maplist"); el.innerHTML="";
  for (const mp of STATE.maps){
    const label = (mp.desc||"(no name)");
    if (f && !(mp.id+" "+label).toLowerCase().includes(f)) continue;
    const d = document.createElement("div");
    d.className="mapitem";
    d.innerHTML = `<div>${esc(label)}</div><div class="mid">${mp.id} · ${mp.missions.length} mission(s)</div>`;
    el.appendChild(d);
    for (const ms of mp.missions){
      const m = document.createElement("div");
      m.className="misitem"; m.dataset.map=mp.id; m.dataset.mis=ms.id;
      if (CUR && CUR.map===mp.id && CUR.mis===ms.id) m.classList.add("active");
      m.textContent = ms.desc || ms.id;
      m.onclick = ()=>openMission(mp.id, ms.id);
      el.appendChild(m);
    }
  }
}
function esc(s){ return String(s).replace(/[&<>"]/g,
  c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

/* ---------- mission ---------- */
async function openMission(map, mis){
  if (M && dirtyCount()>0 &&
      !confirm("Unsaved changes will be lost. Continue?")) return;
  CUR={map,mis};
  try{
    M = await api(`/api/mission?map=${map}&mis=${mis}`);
  }catch(e){
    alert("Could not open "+map+"/"+mis+":\n"+e.message);
    return;
  }
  window._othersDirty=0;  // fresh mission: forget abandoned edits from the last one
  $("#welcome").style.display="none";
  const ed=$("#editor"); ed.style.display="block";
  renderMapList();
  renderMission();
}

function dirtyCount(){
  let n=0;
  if (M && M.support) for (const b of M.support.blocks)
    for (const u of b.units){ if(u.dirty)n++; for(const p of u.passengers) if(p.dirty)n++; }
  return n + (window._othersDirty||0);
}

function renderMission(){
  const ed=$("#editor");
  const mapDesc = STATE.maps.find(x=>x.id===CUR.map)?.desc || "";
  ed.innerHTML = `
  <h2>${esc(mapDesc)} <span class="badge">${CUR.map}/${CUR.mis}</span></h2>
  <div class="crumb">${esc((M.misdesc||"").split("\n")[0]||"")}</div>
  <div class="tabs">
    <div class="tab active" data-t="support">Support (reinforcements)</div>
    <div class="tab" data-t="players">Players &amp; paradrops</div>
    <div class="tab" data-t="scripts">Scripts</div>
    <div class="tab" data-t="info">Mission info</div>
    <div class="tab" data-t="helppane">❓ Parameter help</div>
  </div>
  <div class="pane active" id="pane-support"></div>
  <div class="pane" id="pane-players"></div>
  <div class="pane" id="pane-scripts"></div>
  <div class="pane" id="pane-info"></div>
  <div class="pane" id="pane-helppane"></div>`;
  for (const t of ed.querySelectorAll(".tab")) t.onclick=()=>{
    ed.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
    ed.querySelectorAll(".pane").forEach(x=>x.classList.remove("active"));
    t.classList.add("active");
    ed.querySelector("#pane-"+t.dataset.t).classList.add("active");
  };
  renderSupport(); renderPlayers(); renderScripts(); renderInfo(); renderHelp();
}

/* ---------- nation balance (scores from the Unit Comparator HTML) ---------- */
/* nation grouping — same mechanics as the comparator's "Group nations":
   pick 2+ nations, validate, their scores merge into one "A + B" entry.
   Groups are remembered across missions/reloads (localStorage). */
let nationGroups=[], groupPickMode=false, pendingGroupNations=[];
try{ nationGroups=JSON.parse(localStorage.getItem("hs2_nation_groups")||"[]")
       .filter(g=>Array.isArray(g)&&g.length>=2); }catch(e){}
function saveGroups(){
  try{ localStorage.setItem("hs2_nation_groups", JSON.stringify(nationGroups)); }catch(e){}
}
function groupKeyForNation(nation){
  const idx=nationGroups.findIndex(g=>g.includes(nation));
  return idx>=0 ? "__grp_"+idx : nation;
}
function groupMembersFromKey(key){
  if(String(key).startsWith("__grp_"))
    return nationGroups[+String(key).slice(6)]||[];
  return [key];
}
function groupDisplayName(key){ return groupMembersFromKey(key).join(" + "); }
function startNationGrouping(){ groupPickMode=true; pendingGroupNations=[]; renderBalance(); }
function cancelNationGrouping(){ groupPickMode=false; pendingGroupNations=[]; renderBalance(); }
function togglePendingNation(nation){
  if(!groupPickMode) return;
  const idx=pendingGroupNations.indexOf(nation);
  if(idx>=0) pendingGroupNations.splice(idx,1); else pendingGroupNations.push(nation);
  renderBalance();
}
function validateNationGrouping(){
  if(pendingGroupNations.length>=2){
    // remove picked nations from any prior group, then create the new group
    nationGroups=nationGroups.map(g=>g.filter(n=>!pendingGroupNations.includes(n)))
                             .filter(g=>g.length>=2);
    nationGroups.push([...pendingGroupNations]);
    saveGroups();
  }
  pendingGroupNations=[]; groupPickMode=false; renderBalance();
}
function resetNationGroups(){
  nationGroups=[]; pendingGroupNations=[]; groupPickMode=false;
  saveGroups(); renderBalance();
}

function missionBalance(){
  const sums={}; let unrated=0;
  const add=(id,mult)=>{
    if(!id||mult<=0) return;
    const st=STATS[id];
    if(!st){ unrated+=mult; return; }
    // while picking, show individual nations so they can be clicked
    const n=groupPickMode ? st.nation : groupKeyForNation(st.nation);
    if(!sums[n]) sums[n]={count:0,overall:0,at:0};
    sums[n].count+=mult; sums[n].overall+=st.overall*mult; sums[n].at+=st.at*mult;
  };
  if(M.support) for(const b of M.support.blocks) for(const u of b.units){
    add(u.id,1);
    for(const p of u.passengers) add(p.id,1);
  }
  if(M.players) for(const p of M.players.players)
    for(const d of p.descents) for(const s of d.slots) add(s.id, s.number);
  return {sums,unrated};
}

/* same rule as the comparator: gap = (max-min)/max,
   <15% balanced, <=30% moderate, >30% strong imbalance */
function gapLabel(entries, key){
  if(entries.length<2) return null;
  const vals=entries.map(e=>e[1][key]);
  const hi=Math.max(...vals), lo=Math.min(...vals);
  const gap=hi>0?(hi-lo)/hi*100:0;
  if(gap<15)  return {gap, txt:"Balanced", cls:"ok"};
  if(gap<=30) return {gap, txt:"Moderate imbalance", cls:"warn"};
  return {gap, txt:"Strong imbalance", cls:"err"};
}

function balanceRow(title, entries, key, pickRow){
  let html=`<h4>${title}</h4><div class="balcards">`;
  for(const [k,x] of entries.slice().sort((a,b)=>b[1][key]-a[1][key])){
    const members=groupMembersFromKey(k);
    const pickable=pickRow&&groupPickMode&&members.length===1;
    const pending=pickable&&pendingGroupNations.includes(members[0]);
    const grouped=!groupPickMode&&members.length>1;
    html+=`<div class="balcard${pickable?" pickable":""}${pending?" pending":""}${grouped?" grouped":""}"
      ${pickable?`data-nation="${esc(members[0])}"`:""}>
      <span>${esc(groupDisplayName(k))} · ${x.count} unit(s)</span>
      <strong>${Math.round(x[key]).toLocaleString("en-US")}</strong></div>`;
  }
  html+="</div>";
  const g=gapLabel(entries,key);
  if(g) html+=`<div class="balstatus ${g.cls}">${g.txt}
    <span style="font-weight:normal">(gap: ${g.gap.toFixed(1)} %)</span></div>`;
  return html;
}

function renderBalance(){
  const el=$("#balpanel"); if(!el) return;
  if(!Object.keys(STATS).length){ el.innerHTML=""; return; }
  const {sums,unrated}=missionBalance();
  const entries=Object.entries(sums);
  if(!entries.length){
    el.innerHTML=`<div class="balwrap"><h4>Nation balance</h4>
      <div class="balnote">No rated units in this mission
      (infantry, guns and planes are not rated by the comparator).</div></div>`;
    return;
  }
  let html=`<div class="balwrap">`;
  html+=balanceRow("Nation balance — Overall", entries, "overall", true);
  html+=balanceRow("Nation balance — AT Skill", entries, "at", false);
  if(groupPickMode){
    html+=`<div style="margin:4px 0 8px">
      <button class="small" onclick="validateNationGrouping()"
        ${pendingGroupNations.length>=2?"":"disabled"}>Validate group</button>
      <button class="small ghost" onclick="cancelNationGrouping()">Cancel</button>
      <span class="balnote"> click 2+ nations in the Overall row to merge them
      (e.g. French + American + British allies)</span></div>`;
  } else {
    html+=`<div style="margin:4px 0 8px">
      <button class="small ghost" onclick="startNationGrouping()">Group nations (allies)</button>
      ${nationGroups.length?`<button class="small ghost" onclick="resetNationGroups()">Reset groups</button>`:""}
      </div>`;
  }
  html+=`<div class="balnote">Counts support convoys, passengers and paradrop
    packages. ${unrated?unrated+" unit(s) not rated by the comparator (infantry, guns, planes…). ":""}
    Scores from ${esc(STATSRC||"the Unit Comparator")}.
    ${nationGroups.length&&!groupPickMode?" Nation groups are remembered for every mission.":""}</div></div>`;
  el.innerHTML=html;
  el.querySelectorAll(".balcard.pickable").forEach(c=>
    c.onclick=()=>togglePendingNation(c.dataset.nation));
}

/* ---------- support tab ---------- */
function numInput(obj, key, cls){
  const v = obj[key];
  return `<input class="num ${cls||""} ${v===-1?"neg":""}" type="text" value="${v}"
    data-key="${key}" title="${esc(FIELD_HELP[key]||"")}">`;
}

function renderSupport(){
  const pane=$("#pane-support");
  if (!M.support_raw){ pane.innerHTML="<i>No support file in this mission.</i>"; return; }
  if (!M.support){
    pane.innerHTML = `<div class="warnbox">This support file has an unusual layout —
      structured editing is disabled to stay safe. You can still edit the raw text
      below (a backup is made on save).</div>
      <textarea id="sup_raw" rows="24">${esc(M.support_raw)}</textarea>
      <p><button onclick="saveRaw('support','sup_raw')">Save raw support</button>
      <span class="savemsg" id="msg-support"></span></p>`;
    return;
  }
  const S=M.support;
  let html = `
  <div class="savebar">
    <button onclick="saveSupport()">💾 Save support</button>
    <span class="savemsg" id="msg-support"></span>
  </div>
  <div id="balpanel"></div>
  <div class="bulk">
    <b>Bulk edit:</b>
    <label>set</label>
    <select id="bk_field">${["expa","morale","hp","ammo"].map(f=>
      `<option value="${f}">${FLABEL[f]}</option>`).join("")}</select>
    <label>to</label><input id="bk_val" class="num" value="50">
    <label>for</label>
    <select id="bk_scope">
      <option value="all">all units (whole mission)</option>
      <option value="top">transports / vehicles only</option>
      <option value="pass">passengers only</option>
    </select>
    <label><input type="checkbox" id="bk_skip" checked>
      leave “-1 (default)” untouched</label>
    <button class="ghost" onclick="bulkApply()">Apply</button>
  </div>
  <div class="block" id="flagsblock">
    <div class="bh" onclick="this.parentNode.classList.toggle('open')">
      <b>Entry flags</b><span class="cnt">${S.flags.filter(f=>f.vals[0]>=0).length}
      active of ${S.flags.length} — arrival &amp; destination points of support convoys</span>
    </div>
    <div class="bc"><table class="units"><tr>
      <th title="Arrival point (map cell coordinates)">X1</th>
      <th title="Arrival point (map cell coordinates)">Y1</th>
      <th title="Middle value — observed 0…6 (flag index / owner). 0 on unused slots.">K</th>
      <th title="Destination point (map cell coordinates)">X2</th>
      <th title="Destination point (map cell coordinates)">Y2</th></tr>`;
  S.flags.forEach((f,i)=>{
    html += "<tr>" + f.vals.map((v,j)=>
      `<td><input class="num ${v===-1?"neg":""}" data-flag="${i}" data-j="${j}"
        value="${v}"></td>`).join("") + "</tr>";
  });
  html += `</table><div class="crumb">-1,-1,0,-1,-1 = unused slot. Coordinates are
    map cells (0…map size-1).</div></div></div>
  <label style="font-size:12px;color:var(--dim)">
    <input type="checkbox" id="showempty" onchange="renderSupportBlocks()">
    show empty support slots</label>
  <div id="supblocks"></div>`;
  pane.innerHTML=html;
  pane.querySelectorAll("input[data-flag]").forEach(inp=>{
    inp.onchange=()=>{
      const f=S.flags[+inp.dataset.flag];
      f.vals[+inp.dataset.j]=parseInt(inp.value||0,10)||0;
      f.dirty=true; inp.classList.add("mod");
    };
  });
  renderSupportBlocks();
}

function unitRow(u, isPass, bi, ui, pi){
  const info = UNITS[u.id];
  const nm = info ? (info[0]||info[1]||"") : "⚠ unknown unit id";
  const st = STATS[u.id];
  const tip = nm + (st?` — ${st.nation} · Overall ${st.overall} · AT Skill ${st.at}`:"");
  const ref = `data-b="${bi}" data-u="${ui}"` + (isPass?` data-p="${pi}"`:"");
  let tds = `<td class="idcell">${isPass?"↳ ":""}<input class="txt" list="unitids"
      style="width:120px" value="${esc(u.id)}" data-key="id" ${ref}></td>
    <td class="namecell" title="${esc(tip)}">${esc(nm)}</td>`;
  for (const f of FIELDS){
    if ((f==="crew"||f==="inn") && u[f]===null){ tds+="<td>—</td>"; continue; }
    tds += `<td><input class="num ${u[f]===-1?"neg":""} ${f==="expa"?"exp":""}"
      value="${u[f]}" data-key="${f}" ${ref}
      title="${esc(FIELD_HELP[f])}"></td>`;
  }
  tds += `<td><button class="small danger" title="Delete this line" ${ref}
      data-del="1">✕</button></td>`;
  return `<tr class="${isPass?"passenger":""}">${tds}</tr>`;
}

function renderSupportBlocks(){
  const S=M.support, showEmpty=$("#showempty")?.checked;
  const wrap=$("#supblocks"); let html="";
  S.blocks.forEach((b,bi)=>{
    const total = b.units.reduce((a,u)=>a+1+u.passengers.length,0);
    if (!total && !showEmpty) return;
    let bOv=0, bAt=0;
    for(const u of b.units){
      const s1=STATS[u.id]; if(s1){bOv+=s1.overall;bAt+=s1.at;}
      for(const p of u.passengers){ const s2=STATS[p.id]; if(s2){bOv+=s2.overall;bAt+=s2.at;} }
    }
    const score = bOv?` · Overall ${Math.round(bOv).toLocaleString("en-US")} · AT ${Math.round(bAt).toLocaleString("en-US")}`:"";
    html += `<div class="block ${total?"open":""}"><div class="bh"
      onclick="if(event.target.tagName!=='INPUT')this.parentNode.classList.toggle('open')">
      <b>${esc(b.name||"(empty slot)")}</b>
      <span class="cnt">${b.units.length} group(s), ${total} unit(s)${score}</span></div>
      <div class="bc">`;
    if (total){
      html += `<table class="units"><tr><th>ID</th><th>Unit</th>` +
        FIELDS.map(f=>`<th title="${esc(FIELD_HELP[f])}">${FLABEL[f]} ⓘ</th>`).join("") +
        `<th></th></tr>`;
      b.units.forEach((u,ui)=>{
        html += unitRow(u,false,bi,ui);
        u.passengers.forEach((p,pi)=>{ html += unitRow(p,true,bi,ui,pi); });
      });
      html += "</table>";
    }
    html += `<button class="small ghost" data-addtop="${bi}">+ add vehicle/group</button> `;
    if (b.units.length)
      html += `<button class="small ghost" data-addpass="${bi}">+ add passenger to last vehicle</button>`;
    html += "</div></div>";
  });
  wrap.innerHTML=html;

  wrap.querySelectorAll("input[data-key]").forEach(inp=>{
    inp.onchange=()=>{
      const u = locate(inp);
      const k = inp.dataset.key;
      if (k==="id"){ u.id=inp.value.trim(); }
      else {
        const v = parseInt(inp.value,10);
        if (isNaN(v)) { inp.value=u[k]; return; }
        u[k]=v;
        inp.classList.toggle("neg", v===-1);
      }
      u.dirty=true; inp.classList.add("mod");
      if (k==="id"){
        const info=UNITS[u.id];
        const cell=inp.closest("tr").querySelector(".namecell");
        cell.textContent = info?(info[0]||info[1]||""):"⚠ unknown unit id";
        renderBalance();
      }
    };
  });
  wrap.querySelectorAll("button[data-del]").forEach(btn=>{
    btn.onclick=()=>{
      const b=M.support.blocks[+btn.dataset.b];
      if (btn.dataset.p!==undefined){
        const u=b.units[+btn.dataset.u];
        u.passengers.splice(+btn.dataset.p,1);
        if (u.inn!==null){ u.inn=u.passengers.length; u.dirty=true; }
      } else {
        b.units.splice(+btn.dataset.u,1);
      }
      window._othersDirty=(window._othersDirty||0)+1;
      renderSupportBlocks();
    };
  });
  wrap.querySelectorAll("button[data-addtop]").forEach(btn=>{
    btn.onclick=()=>{
      M.support.blocks[+btn.dataset.addtop].units.push({
        raw:null, dirty:true, id:"relite", hp:100, ammo:100, expa:40,
        morale:50, lives:0, grp:0, crew:1, inn:null, passengers:[]});
      window._othersDirty=(window._othersDirty||0)+1;
      renderSupportBlocks();
    };
  });
  wrap.querySelectorAll("button[data-addpass]").forEach(btn=>{
    btn.onclick=()=>{
      const b=M.support.blocks[+btn.dataset.addpass];
      const u=b.units[b.units.length-1];
      u.passengers.push({raw:null, dirty:true, id:"relite", hp:100, ammo:100,
        expa:-1, morale:-1, lives:0, grp:-1, crew:null, inn:null});
      if (u.inn!==null){ u.inn=u.passengers.length; u.dirty=true; }
      window._othersDirty=(window._othersDirty||0)+1;
      renderSupportBlocks();
    };
  });
  renderBalance();
}

function locate(inp){
  const b=M.support.blocks[+inp.dataset.b];
  const u=b.units[+inp.dataset.u];
  return inp.dataset.p!==undefined ? u.passengers[+inp.dataset.p] : u;
}

function bulkApply(){
  const f=$("#bk_field").value, v=parseInt($("#bk_val").value,10);
  if (isNaN(v) || v<-1 || v>100){ alert("Value must be between -1 and 100."); return; }
  const scope=$("#bk_scope").value, skip=$("#bk_skip").checked;
  let n=0;
  for (const b of M.support.blocks)
    for (const u of b.units){
      if (scope!=="pass"){ if(!(skip&&u[f]===-1)&&u[f]!==v){u[f]=v;u.dirty=true;n++;} }
      if (scope!=="top")
        for (const p of u.passengers)
          if(!(skip&&p[f]===-1)&&p[f]!==v){p[f]=v;p.dirty=true;n++;}
    }
  renderSupportBlocks();
  msg("support", n+" unit(s) changed — remember to save.", "");
}

async function saveSupport(){
  try{
    // strip helper fields the server doesn't need? (it ignores extras)
    const r = await api("/api/save", {map:CUR.map, mis:CUR.mis, file:"support",
      mode:"structured", data:M.support});
    msg("support","Saved ("+r.bytes+" bytes). Backup: "+r.backup,"ok");
    window._othersDirty=0;
    M = await api(`/api/mission?map=${CUR.map}&mis=${CUR.mis}`);
    renderSupport();
    msg("support","Saved — support file overwritten ✓ (open + re-save the map in "+
        "the map editor for the game to pick it up)","ok");
  }catch(e){ msg("support","SAVE FAILED: "+e.message,"err"); }
}

async function saveRaw(file, taId){
  try{
    const r = await api("/api/save",{map:CUR.map,mis:CUR.mis,file,
      mode:"raw", data: $("#"+taId).value});
    msg(file==="scripts2"?"scripts":file,
        "Saved ("+r.bytes+" bytes). Backup: "+r.backup,"ok");
  }catch(e){ msg(file==="scripts2"?"scripts":file,"SAVE FAILED: "+e.message,"err"); }
}

function msg(which, text, cls){
  const el=$("#msg-"+which); if(!el) return;
  el.textContent=text; el.className="savemsg "+(cls||"");
}

/* ---------- players tab ---------- */
const PLANE_HELP={
  bomber:"Bomber flight (dive/level bombers).",
  spy:"Reconnaissance / spotter plane.",
  transport:"Paratrooper transport (drops 'descent 0').",
  boxer:"Cargo plane (drops 'descent 1': ammunition / supplies).",
  interceptor:"Fighter cover intercepting enemy planes."};
function renderPlayers(){
  const pane=$("#pane-players");
  if (!M.players_raw){ pane.innerHTML="<i>No players file.</i>"; return; }
  if (!M.players){
    pane.innerHTML=`<div class="warnbox">Unusual players layout — raw editing only.</div>
      <textarea id="ply_raw" rows="24">${esc(M.players_raw)}</textarea>
      <p><button onclick="saveRaw('players','ply_raw')">Save raw players</button>
      <span class="savemsg" id="msg-players"></span></p>`;
    return;
  }
  let html=`<div class="savebar"><button onclick="savePlayers()">💾 Save players</button>
    <span class="savemsg" id="msg-players"></span></div>
    <div class="crumb">Planes: <b>Number</b> = flights available (0 disables),
    <b>Bombs</b> = bombs per pass, <b>Reload</b> = seconds between flights
    (600 = 10 min). Paradrop packages: <b class="exp">expa</b> = experience of the
    dropped units (0–100), 4 unit slots each.</div>`;
  M.players.players.forEach((p,pi)=>{
    const col=`rgb(${p.color[0]},${p.color[1]},${p.color[2]})`;
    html+=`<div class="pcard"><h3>Player ${p.num} —
      <input class="txt" style="width:140px" value="${esc(p.name)}" data-pk="name" data-pi="${pi}">
      <span class="swatch" style="background:${col}"></span>
      <span class="badge">team <input class="num" style="width:34px" value="${p.team}"
        data-pk="team" data-pi="${pi}" title="Team number: players with the same team are allied."></span>
      <span class="badge">nation <input class="num" style="width:34px" value="${p.nation}"
        data-pk="nation" data-pi="${pi}" title="Nation index (voice set / default camo)."></span>
      <span class="badge">planesdir <input class="num" style="width:34px" value="${p.planesdir}"
        data-pk="planesdir" data-pi="${pi}"
        title="Map edge/direction the planes fly in from."></span></h3>
      <h4>Planes</h4><table class="units">
      <tr><th>Type</th><th>Plane ID</th>
      <th title="Number of flights available. 0 = this plane type disabled.">Number</th>
      <th title="Bombs dropped per pass.">Bombs</th>
      <th title="Cooldown between two flights, in seconds (600 = 10 minutes).">Reload s</th></tr>`;
    p.planes.forEach((pl,li)=>{
      html+=`<tr><td style="text-align:left" title="${esc(PLANE_HELP[pl.type]||"")}">${pl.type}</td>
        <td><input class="txt" list="unitids" style="width:130px" value="${esc(pl.id)}"
          data-pl="${pi}:${li}:id"></td>
        <td><input class="num" value="${pl.number}" data-pl="${pi}:${li}:number"></td>
        <td><input class="num" value="${pl.bombs}" data-pl="${pi}:${li}:bombs"></td>
        <td><input class="num" style="width:64px" value="${pl.reload}" data-pl="${pi}:${li}:reload"></td></tr>`;
    });
    html+=`</table>`;
    p.descents.forEach((d,di)=>{
      html+=`<h4>Paradrop package ${d.num} ${d.num===0?"(paratroopers — 'transport' plane)":"(cargo drop — 'boxer' plane)"}</h4>
      <div style="margin-bottom:4px">
        <span class="badge">group <input class="num" style="width:34px" value="${d.group}"
          data-dc="${pi}:${di}:group" title="AI group the dropped units join. Same idea as Grp in support."></span>
        <span class="badge exp">expa <input class="num exp" style="width:40px" value="${d.expa}"
          data-dc="${pi}:${di}:expa"
          title="Experience of the dropped units, 0…100 %."></span></div>
      <table class="units"><tr><th>#</th><th>Unit ID (empty = unused slot)</th>
        <th title="How many of this unit are dropped.">number</th></tr>`;
      d.slots.forEach((s,si)=>{
        const info=UNITS[s.id];
        html+=`<tr><td>${si}</td><td style="text-align:left">
          <input class="txt" list="unitids" style="width:150px" value="${esc(s.id)}"
            data-ds="${pi}:${di}:${si}:id">
          <span class="namecell" style="border:none">${esc(info?(info[0]||""):"")}</span></td>
          <td><input class="num" value="${s.number}" data-ds="${pi}:${di}:${si}:number"></td></tr>`;
      });
      html+=`</table>`;
    });
    html+=`</div>`;
  });
  pane.innerHTML=html;
  const mark = el=>{el.classList.add("mod"); window._othersDirty=(window._othersDirty||0)+1;
    renderBalance();};
  pane.querySelectorAll("input[data-pk]").forEach(inp=>inp.onchange=()=>{
    const p=M.players.players[+inp.dataset.pi]; const k=inp.dataset.pk;
    p[k] = (k==="name")? inp.value : (parseInt(inp.value,10)||0); mark(inp);});
  pane.querySelectorAll("input[data-pl]").forEach(inp=>inp.onchange=()=>{
    const [pi,li,k]=inp.dataset.pl.split(":");
    const pl=M.players.players[+pi].planes[+li];
    pl[k] = (k==="id")? inp.value.trim() : (parseInt(inp.value,10)||0); mark(inp);});
  pane.querySelectorAll("input[data-dc]").forEach(inp=>inp.onchange=()=>{
    const [pi,di,k]=inp.dataset.dc.split(":");
    M.players.players[+pi].descents[+di][k]=parseInt(inp.value,10)||0; mark(inp);});
  pane.querySelectorAll("input[data-ds]").forEach(inp=>inp.onchange=()=>{
    const [pi,di,si,k]=inp.dataset.ds.split(":");
    const s=M.players.players[+pi].descents[+di].slots[+si];
    s[k] = (k==="id")? inp.value.trim() : (parseInt(inp.value,10)||0); mark(inp);});
}

async function savePlayers(){
  try{
    const r=await api("/api/save",{map:CUR.map,mis:CUR.mis,file:"players",
      mode:"structured",data:M.players});
    msg("players","Saved ("+r.bytes+" bytes). Backup: "+r.backup,"ok");
    window._othersDirty=0;
  }catch(e){ msg("players","SAVE FAILED: "+e.message,"err"); }
}

/* ---------- scripts tab ---------- */
function reverseNums(t){
  return t.replace(/#(\d+)/g,(m,d)=>"#"+d+" ("+parseInt(d.split("").reverse().join(""),10)+")");
}
function revDigits(d){ return d ? parseInt(d.split("").reverse().join(""),10) : 0; }
function toRev(n){ return String(n).split("").reverse().join(""); }
function fmtMMSS(s){ return Math.floor(s/60)+" min "+String(s%60).padStart(2,"0")+" s"; }
function maskFlags(m){
  const f=[]; for(let k=0;k<16;k++) if(m>>k&1) f.push(k);
  return f.join(",");
}

/* Every "$T" line followed by "#digits" is a time in seconds (digits reversed).
   Walk back to find what it belongs to: a timed reserve ($sres…$sres5), a
   flag-triggered reserve ($fres/$Fmask…$fres5) or a script trigger ($sp_6…). */
function parseTimings(text){
  const L=text.split("\n"); const out=[];
  for(let i=0;i<L.length-1;i++){
    if(L[i].trim()!=="$T" || !L[i+1].startsWith("#")) continue;
    const digits=L[i+1].slice(1).trim();
    if(!/^\d*$/.test(digits)) continue;
    const prev=(L[i-1]||"").trim();
    let kind="trigger", slots=null, mask=null;
    if(prev==="$sres5"||prev==="$fres5"){
      kind = prev==="$sres5" ? "timed" : "flag";
      slots=[];
      for(let j=i-2;j>=Math.max(0,i-30);j--){
        const t=L[j].trim();
        if(t.startsWith("#") && (L[j-1]||"").trim()==="$resv")
          slots.unshift(revDigits(t.slice(1).trim()));
        if(t==="$Fmask" && L[j+1] && L[j+1].startsWith("#"))
          mask=revDigits(L[j+1].slice(1).trim());
        if(t==="$sres"||t==="$fres") break;
      }
    }
    out.push({line:i+1, secs:revDigits(digits), kind, slots, mask, prev});
  }
  return out;
}

function slotLabel(v){
  const b = M.support && M.support.blocks && M.support.blocks[v];
  return b && b.name ? b.name : ("slot "+v);
}

function renderTimings(){
  let rows="";
  M.scripts.scripts.forEach((s,si)=>{
    for(const t of parseTimings(s.text)){
      let what, detail;
      if(t.kind==="timed"){
        what="⏱ timed reserve";
        detail="sends "+t.slots.map(v=>"#"+v).join(" ")+" (one slot per player)";
      } else if(t.kind==="flag"){
        what="🚩 flag reserve";
        detail="flags "+maskFlags(t.mask||0)+" held → sends "+
               t.slots.map(v=>"#"+v).join(" ");
      } else {
        what="⚡ trigger ("+esc(t.prev)+")";
        detail="condition timer of this script";
      }
      const names = t.slots ? t.slots.map(slotLabel).join(" · ") : "";
      rows+=`<tr><td style="text-align:left">${esc(s.name)}</td>
        <td style="text-align:left">${what}</td>
        <td style="text-align:left" class="namecell" title="${esc(names)}">${esc(detail)}</td>
        <td><input class="num" style="width:70px" value="${t.secs}"
          data-tim="${si}:${t.line}"
          title="Delay in SECONDS before this support arrives (stored digit-reversed in the script).\nExample: 600 = 10 min. 0 = immediately."></td>
        <td class="mmss" style="color:var(--dim)">${fmtMMSS(t.secs)}</td></tr>`;
    }
  });
  if(!rows) return "";
  return `<div class="block open"><div class="bh"
    onclick="if(event.target.tagName!=='INPUT')this.parentNode.classList.toggle('open')">
    <b>⏱ Support arrival timings</b><span class="cnt">every delay found in the
    scripts — edit the seconds, the script text updates itself</span></div>
    <div class="bc"><table class="units"><tr>
    <th>Script</th><th>Type</th><th>Sends</th>
    <th title="Delay in seconds. Stored digit-reversed in the script text (600 → #006) — handled for you.">Seconds ⓘ</th>
    <th>=</th></tr>${rows}</table>
    <div class="crumb">“timed reserve” delays count from when the script fires
    (usually mission start). “flag reserve” delays count from capturing the
    listed entry flags. Hover “sends” to see the support names; edit the
    convoys themselves in the Support tab.</div></div></div>`;
}
function renderScripts(){
  const pane=$("#pane-scripts");
  if (!M.scripts_raw){ pane.innerHTML="<i>No scripts2 file.</i>"; return; }
  if (!M.scripts){
    pane.innerHTML=`<div class="warnbox">Unusual scripts2 layout — raw editing only.
      Careful: each script header carries a byte size that must match its body.</div>
      <textarea id="scr_raw" rows="24">${esc(M.scripts_raw)}</textarea>
      <p><button onclick="saveRaw('scripts2','scr_raw')">Save raw scripts2</button>
      <span class="savemsg" id="msg-scripts"></span></p>`;
    return;
  }
  let html=`<div class="savebar"><button onclick="saveScripts()">💾 Save scripts</button>
    <span class="savemsg" id="msg-scripts"></span></div>
    <div class="crumb">The <code>size</code> byte-count in each script header is
    recomputed automatically on save — safe to edit here, dangerous by hand.<br>
    ⚠ Numeric literals after <code>#</code> are stored with their digits
    <b>reversed</b>: <code>#006</code> means 600 (seconds), <code>#0012</code>
    means 2100. Toggle the decoded preview to check timings.</div>
    <label style="font-size:12px"><input type="checkbox" id="scr_decode"
      onchange="renderScripts()"> show decoded numbers preview (read-only)</label>`;
  html += renderTimings();
  const dec=$("#scr_decode")?.checked;
  M.scripts.scripts.forEach((s,si)=>{
    html+=`<div class="script"><b>${esc(s.name)}</b>
      <span class="badge">${s.text.length} bytes</span><br>`;
    if (dec){
      html+=`<pre style="white-space:pre-wrap;font-size:11px;color:var(--dim)">${esc(reverseNums(s.text))}</pre>`;
    } else {
      html+=`<textarea rows="${Math.min(16,s.text.split("\n").length+1)}"
        data-si="${si}">${esc(s.text)}</textarea>`;
    }
    html+=`</div>`;
  });
  pane.innerHTML=html;
  pane.querySelectorAll("textarea[data-si]").forEach(ta=>ta.onchange=()=>{
    M.scripts.scripts[+ta.dataset.si].text=ta.value;
    window._othersDirty=(window._othersDirty||0)+1;
    ta.classList.add("mod");
    renderScripts();          // keep the timing table in sync
  });
  pane.querySelectorAll("input[data-tim]").forEach(inp=>inp.onchange=()=>{
    const v=parseInt(inp.value,10);
    if(isNaN(v)||v<0||v>86400){
      alert("Enter a delay in seconds (0 … 86400)."); renderScripts(); return;
    }
    const [si,line]=inp.dataset.tim.split(":").map(Number);
    const L=M.scripts.scripts[si].text.split("\n");
    if(!L[line] || !L[line].startsWith("#")){ renderScripts(); return; }
    L[line]="#"+toRev(v);
    M.scripts.scripts[si].text=L.join("\n");
    window._othersDirty=(window._othersDirty||0)+1;
    renderScripts();
    msg("scripts","Timing updated — remember to 💾 Save scripts.","");
  });
}
async function saveScripts(){
  try{
    const r=await api("/api/save",{map:CUR.map,mis:CUR.mis,file:"scripts2",
      mode:"structured",data:M.scripts});
    msg("scripts","Saved ("+r.bytes+" bytes). Backup: "+r.backup,"ok");
    window._othersDirty=0;
  }catch(e){ msg("scripts","SAVE FAILED: "+e.message,"err"); }
}

/* ---------- info tab ---------- */
function renderInfo(){
  const pane=$("#pane-info");
  let html=`<div class="flexrow"><div style="flex:1;min-width:300px">
    <h4 style="color:var(--dim)">Mission description (misdesc — shown in the game lobby)</h4>
    <textarea id="misdesc_ta" rows="16">${esc(M.misdesc||"")}</textarea>
    <p><button onclick="saveMisdesc()">💾 Save description</button>
    <span class="savemsg" id="msg-misdesc"></span></p></div>`;
  if (M.has_image)
    html+=`<div><h4 style="color:var(--dim)">Minimap</h4>
      <img class="minimap" src="/img?map=${CUR.map}&mis=${CUR.mis}"
      onclick="this.classList.toggle('big')"
      onerror="this.outerHTML='<i style=color:var(--dim)>minimap preview not available for this format</i>'"></div>`;
  html+="</div>";
  pane.innerHTML=html;
}
async function saveMisdesc(){
  try{
    const r=await api("/api/save",{map:CUR.map,mis:CUR.mis,file:"misdesc",
      mode:"raw",data:$("#misdesc_ta").value});
    msg("misdesc","Saved. Backup: "+r.backup,"ok");
  }catch(e){ msg("misdesc","SAVE FAILED: "+e.message,"err"); }
}

/* ---------- help tab ---------- */
function renderHelp(){
  $("#pane-helppane").innerHTML=`
  <h3>Support unit parameters</h3>
  <p>Each <b>support</b> slot is a reinforcement convoy the player can call in
  (or a scripted arrival). Lines with one space are vehicles / groups arriving on
  the map; the double-indented lines below a vehicle are its passengers
  (<code>In</code> = how many ride inside). All percentage values were verified
  against the 200+ missions of this APRM install.</p>
  <table class="help-table">
  <tr><th>Field</th><th>Meaning</th><th>Range</th><th>Notes</th></tr>
  <tr><td>ID</td><td>Unit type — the file name inside <code>lang.aps → UNITS</code>
    (also in <code>Modding/UNITS</code>). Autocompleted; the full unit name shows
    next to it.</td><td class="rng">unit id</td><td>An unknown ID is flagged ⚠ and
    would crash / vanish in game.</td></tr>
  <tr><td>HP</td><td>Starting health, % of the unit's max health.</td>
    <td class="rng">-1 … 100</td><td>100 = intact. Low value = arrives damaged.</td></tr>
  <tr><td>Ammo</td><td>Starting ammunition, % of max.</td>
    <td class="rng">-1 … 100</td><td></td></tr>
  <tr><td>Expa</td><td><b>Experience / veterancy, %.</b> Experienced units aim
    better, react faster and rank up on the in-game unit card.</td>
    <td class="rng">-1 … 100</td><td>-1 = default (used by most passengers).
    Typical APRM values: 0 conscripts, 30–50 regulars, 80–100 elites.</td></tr>
  <tr><td>Morale</td><td>Starting morale, %. Low morale troops panic and rout
    under fire.</td><td class="rng">-1 … 100</td><td>-1 = default (≈50, the value
    used almost everywhere).</td></tr>
  <tr><td>Lives</td><td>Almost always 0; 100 on a few missions. Exact effect not
    confirmed.</td><td class="rng">0 / 100</td><td>Recommended: leave as-is.</td></tr>
  <tr><td>Grp</td><td>AI / control group joined on arrival (see the
    <code>groups</code> file &amp; scripts).</td><td class="rng">-1 … 99</td>
    <td>-1 = no group.</td></tr>
  <tr><td>Crew</td><td>Crew soldiers manning the vehicle / gun.</td>
    <td class="rng">0 … 31</td><td>0 = arrives abandoned. Top-level lines only.</td></tr>
  <tr><td>In</td><td>Passengers loaded inside (the indented lines below).</td>
    <td class="rng">1 … 30</td><td>Keep equal to the number of passenger lines —
    the editor maintains this when you add/delete passengers.</td></tr>
  </table>

  <h3>Entry flags</h3>
  <p>16 slots of <code>flag x1,y1,k,x2,y2</code>: arrival point (x1,y1) and
  destination (x2,y2) in map cells, k observed 0…6 (flag index / owner).
  <code>-1,-1,0,-1,-1</code> = unused.</p>

  <h3>Players</h3>
  <table class="help-table">
  <tr><th>Field</th><th>Meaning</th><th>Range</th></tr>
  <tr><td>plane Number</td><td>Flights available for this plane type
    (0 = disabled).</td><td class="rng">0 … ~9</td></tr>
  <tr><td>plane Bombs</td><td>Bombs dropped per pass.</td><td class="rng">0 … ~9</td></tr>
  <tr><td>plane Reload</td><td>Seconds between two flights.</td>
    <td class="rng">0 … 3600 (600 = 10 min)</td></tr>
  <tr><td>descent expa</td><td><b>Experience of paradropped units.</b></td>
    <td class="rng">0 … 100</td></tr>
  <tr><td>descent group</td><td>AI group the dropped units join.</td>
    <td class="rng">-1 … 99</td></tr>
  <tr><td>planesdir</td><td>Map edge / direction planes arrive from.</td>
    <td class="rng">0 … 7</td></tr>
  <tr><td>team</td><td>Players sharing a team number are allied.</td>
    <td class="rng">0 …</td></tr>
  </table>

  <h3>Scripts &amp; support timing</h3>
  <p>The <code>scripts2</code> tokens are the map editor's condition/action
  language ($-prefixed opcodes). <b>When a support arrives is decided here,
  not in the support file</b> — use the “⏱ Support arrival timings” table at
  the top of the Scripts tab to change the delays without touching the tokens.</p>
  <ul>
  <li><b>⏱ timed reserve</b> (<code>$sres…$sres5 $T #delay</code>): sends one
    support slot per player (the 5 <code>$resv</code> values are the block
    indices of the Support tab) after <i>delay</i> seconds from the script
    firing — with a plain <code>$mist</code> condition that means from mission
    start.</li>
  <li><b>🚩 flag reserve</b> (<code>$fres $Fmask #mask…$T #delay</code>): same,
    but triggered by holding the entry flags in the bitmask (bit k = flag k of
    the Support tab), after <i>delay</i> seconds.</li>
  <li><b>⚡ trigger</b> (<code>$sp_6/$sp_5 $T #time</code>): the timer condition
    of the script itself (e.g. “fire at 35:00”).</li>
  <li>Each script header stores its body's <b>byte size</b> — this editor
    recomputes it on save (editing the file by hand without fixing it corrupts
    the mission).</li>
  <li>Numbers after <code>#</code> are stored with <b>reversed digits</b>:
    <code>#006</code> = 600 s, <code>#0012</code> = 2100 s. The timing table
    does the conversion for you; the decoded preview shows the rest.</li>
  </ul>

  <h3>Workflow</h3>
  <ol>
  <li>Edit and save here (backups land in <code>Tools/backups/</code>).</li>
  <li>These are the <b>map-editor source files</b>: open the map in
    <code>Mapeditor.exe</code>/<code>edit3.exe</code> and re-save it so the game
    picks up the changes packed into the mission.</li>
  </ol>`;
}

/* ---------- init ---------- */
(async function(){
  STATE = await api("/api/state");
  UNITS = await api("/api/units");
  try {
    const st = await api("/api/stats");
    STATS = st.units || {}; STATSRC = st.source;
  } catch(e) { STATS = {}; }
  $("#rootinfo").textContent = STATE.maps.length + " maps · " +
    STATE.units_count + " unit types";
  const dl=$("#unitids");
  for (const id of Object.keys(UNITS).sort()){
    const o=document.createElement("option");
    o.value=id; o.label=UNITS[id][0]||"";
    dl.appendChild(o);
  }
  $("#filter").oninput=renderMapList;
  renderMapList();
})();
window.onbeforeunload = () =>
  (M && dirtyCount()>0) ? "Unsaved changes" : undefined;
</script>
</body></html>
"""


def run(port=8765):
    if not MAPS_DIR.is_dir():
        print("Maps folder not found: %s" % MAPS_DIR)
        print(
            "Pass it as an argument:  python3 hs2_mission_editor.py "
            '"/path/to/maps_ap.src"'
        )
        sys.exit(1)
    httpd = None
    for p in range(port, port + 20):
        try:
            httpd = ThreadingHTTPServer(("127.0.0.1", p), Handler)
            port = p
            break
        except OSError:
            continue
    if httpd is None:
        print("No free port found.")
        sys.exit(1)
    url = "http://127.0.0.1:%d/" % port
    print("HS2 Mission Editor running at %s  (Ctrl+C to quit)" % url)
    print("Maps: %s" % MAPS_DIR)
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
