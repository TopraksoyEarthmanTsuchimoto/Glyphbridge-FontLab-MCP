"""Tests for the .notdef check and its note (introduced in listener v0.46 + server v0.10; since listener v0.203 + server v0.83 the
note is one OUTPUT line and NO dialog, remembered per font by its package fgId, with the font's maturity for an empty .notdef).

FontLab, PythonQt and the MCP SDK are STUBBED, so this proves the logic and wording, NOT how real FontLab behaves.
Part 1-3 drive the real listener source, part 4 the real server source with a faked listener, part 5 wires the two together
(stub FontLab -> listener -> server), part 6 checks the wording of the timeout message. Output is print based: review the diff
against expected_notdef_output.txt before using run_all.py --update."""
import contextlib, importlib.util, io, json, os, sys, types
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))


def find(name):
    for d in (os.path.join(HERE, ".."), HERE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit("cannot find " + name)


# ---------------------------------------------------------------- fake FontLab ----
class Lyr:                               # a layer: counts only
    def __init__(self, nodes=0, contours=0, shapes=0, raises=False):
        self.n, self.c, self.s, self.raises = nodes, contours, shapes, raises
        self.name = "L"
    def countNodes(self):
        if self.raises: raise RuntimeError("countNodes failed")
        return self.n
    def countContours(self): return self.c
    def countShapes(self): return self.s


class Seq:                               # stands for fgLayers: only len() works
    def __init__(self, n): self.n = n
    def __len__(self): return self.n


class Gl:
    def __init__(self, name, layers=1, body=None, comps=0, layers_raises=False, comps_raises=False, unicode=None, drawn=False,
                 unicode_raises=False):
        self.name, self._n, self._body, self._lr, self._cr = name, layers, body, layers_raises, comps_raises
        self._comps = [object()] * comps
        self.width = 500.0
        self._u, self._ur, self.drawn = unicode, unicode_raises, drawn
    @property
    def unicode(self):
        if self._ur: raise RuntimeError("unicode failed")
        return self._u
    @property
    def layers(self):
        if self._lr: raise RuntimeError("layers failed")
        return Seq(self._n)
    @property
    def components(self):
        if self._cr: raise RuntimeError("components failed")
        return self._comps
    @property
    def layer(self): return Lyr()                # the always-empty "Body" placeholder
    bodyLayerStrict = layer
    @property
    def bodyLayer(self): return self._body
    activeLayer = bodyLayer


class Font:
    def __init__(self, glyphs, path="fontA", fgid=1):
        self.glyphs, self.path, self.info, self.fgid = glyphs, path, types.SimpleNamespace(), fgid


CUR = {"font": None, "ws_raises": False}
MADE = []                                # every QMessageBox that was constructed (since v0.203 there must be none)


class Rec:                                # recording QMessageBox
    Information, Warning, Ok, Yes, No = "Information", "Warning", "Ok", "Yes", "No"
    def __init__(self, icon, title, text, buttons): MADE.append((icon, title, text, buttons))
    def exec_(self): return 1


class WS:                                 # flWorkspace.instance(): its currentPackage follows the font in front
    @property
    def currentPackage(self):
        if CUR["ws_raises"]: raise RuntimeError("no workspace package")
        return types.SimpleNamespace(fgId=CUR["font"].fgid)


fl = types.ModuleType("fontlab"); fl.CurrentFont = lambda: CUR["font"]
fl.flWorkspace = types.SimpleNamespace(instance=lambda: WS())
pq = types.ModuleType("PythonQt"); qc = types.ModuleType("QtCore"); pq.QtCore = qc
qg = types.ModuleType("PythonQt.QtGui"); qg.QMessageBox = object
sys.modules.update({"fontlab": fl, "PythonQt": pq, "PythonQt.QtCore": qc, "PythonQt.QtGui": qg})
src = open(find("glyphbridge_fontlab_mcp_listener.py"), encoding="utf-8").read().replace("\nstart()\n", "\n")
ns = {}
exec(compile(src, "glyphbridge_fontlab_mcp_listener.py", "exec"), ns)
ns["QMessageBox"] = Rec
NOTDEF_NOTED = ns["_NOTDEF_NOTED"]
# the modern-layer count (real FontLab only): a stub glyph is "drawn" when it says so; .notdef is never, so part 1 runs the legacy checks
ns["_notdef_modern_outline_counts"] = lambda g, f: {"nodes": 4, "shapes": 1, "components": 0} if getattr(g, "drawn", False) else None


def lget(path):
    h, _, b = ns["_route"]("GET", path).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def lpost(path, payload=None, raw=None):
    body = raw if raw is not None else json.dumps(payload or {}).encode()
    h, _, b = ns["_route"]("POST", path, body).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def setfont(glyphs, path="fontA", fgid=1, keep_memory=False):
    CUR["font"] = Font(glyphs, path, fgid)
    CUR["ws_raises"] = False
    if not keep_memory:
        NOTDEF_NOTED.clear()
    MADE.clear()


def nd(**kw): return Gl(".notdef", **kw)


def status_of(glyphs):
    setfont(glyphs); c, d = lget("/font/notdef")
    return d


def letters(drawn="", skip="", unreadable=False):
    """The 52 letters A-Z a-z as glyphs carrying their codepoints; `drawn` letters hold an outline, `skip` letters are left out."""
    out = [Gl(chr(cp), unicode=cp, drawn=chr(cp) in drawn) for cp in list(range(0x41, 0x5B)) + list(range(0x61, 0x7B)) if chr(cp) not in skip]
    if unreadable:
        out.append(Gl("bad", unicode_raises=True))
    return out


# ---------------------------------------------------------------- part 1: the detector ----
print("==== 1. detector (GET /font/notdef, read-only) ====")
cases = [
    ("1a  zero layers, no components (the real empty .notdef)", [nd(layers=0)]),
    ("1b  one layer, 0 nodes/contours/shapes, no components ", [nd(layers=1, body=Lyr())]),
    ("1c  one layer with 8 nodes, 2 contours (Arial-like)    ", [nd(layers=1, body=Lyr(8, 2, 1))]),
    ("1d  zero layers but 1 component                        ", [nd(layers=0, comps=1)]),
    ("1e  zero layers, component count unreadable            ", [nd(layers=0, comps_raises=True)]),
    ("1f  one layer, bodyLayer unreachable (None)            ", [nd(layers=1, body=None)]),
    ("1g  TWO layers, both empty-looking                     ", [nd(layers=2, body=Lyr())]),
    ("1h  len(glyph.layers) raises                           ", [nd(layers_raises=True)]),
    ("1i  one layer, countNodes raises                       ", [nd(layers=1, body=Lyr(raises=True))]),
    ("1j  one layer, empty, but 1 component                  ", [nd(layers=1, body=Lyr(), comps=1)]),
    ("1k  NO glyph named .notdef (glyph 0 is 'A')            ", [Gl("A"), Gl("B")]),
]
for label, glyphs in cases:
    d = status_of(glyphs)
    print(label, "->", d["status"], "|", d["evidence"][0][:78])
d = status_of([Gl("A"), Gl("B"), nd(layers=1, body=Lyr(8, 2, 1))])
print("1l  .notdef is glyph 2 (not first)                      ->", d["status"], "| notes:", d.get("notes"))
CUR["font"] = None
print("1m  no font open                                        ->", lget("/font/notdef"))
setfont([nd(layers=0)]); lget("/font/notdef"); lget("/font/notdef")
print("1n  GET never makes a dialog                            -> dialogs made:", len(MADE))

print("\n-- maturity of a font with an empty .notdef (v0.203)")
mcases = [
    ("1o  only A and B                    ", [nd(layers=0), Gl("A", unicode=0x41), Gl("B", unicode=0x42)]),
    ("1p  all 52, none drawn (placeholders)", [nd(layers=0)] + letters()),
    ("1q  all 52, n drawn                 ", [nd(layers=0)] + letters(drawn="n")),
    ("1r  all 52, only z drawn            ", [nd(layers=0)] + letters(drawn="z")),
    ("1s  51 letters, one glyph unreadable", [nd(layers=0)] + letters(skip="Q", unreadable=True)),
    ("1t  all 52 and one unreadable glyph ", [nd(layers=0)] + letters(drawn="H", unreadable=True)),
    ("1u  A by name only, no codepoint    ", [nd(layers=0)] + letters(skip="A") + [Gl("A", unicode=None, drawn=True)]),
    ("1v  A twice: the first holder counts", [nd(layers=0)] + letters(skip="A") + [Gl("A.alt", unicode=0x41), Gl("A", unicode=0x41, drawn=True)]),
]
for label, glyphs in mcases:
    d = status_of(glyphs)
    print(label, "->", d["status"], "|", d.get("maturity"))
print("1w  missing .notdef has no maturity :", "maturity" in status_of(letters(drawn="n")),
      "| drawn .notdef has none            :", "maturity" in status_of([nd(layers=1, body=Lyr(8, 2, 1))] + letters(drawn="n")))

# ---------------------------------------------------------------- part 2: the note, no dialog ----
print("\n==== 2. the note (POST /font/notdef/warn): one OUTPUT line per font, NO dialog (v0.203) ====")
KEYS = ("status", "noted", "already_noted", "already_warned", "dialog_shown")
setfont([nd(layers=0)], "fontA", fgid=5)
c, d = lpost("/font/notdef/warn")
print("2a  empty -> ", {k: d[k] for k in KEYS}, "| maturity:", d.get("maturity"), "| dialogs made:", len(MADE), "| memory:", dict(NOTDEF_NOTED))
c, d = lpost("/font/notdef/warn")
print("2b  second call, same font -> noted:", d["noted"], "| already_noted:", d["already_noted"], "| already_warned:", d["already_warned"])
c, d = lpost("/font/notdef/warn", {"force": True})
print("2c  force=true -> noted:", d["noted"])
c, d = lpost("/font/notdef/warn", {"force": "yes"})
print("2d  force=\"yes\" (not boolean true) -> noted:", d["noted"], "| already_noted:", d["already_noted"])
setfont([nd(layers=0)], "", fgid=8)
lpost("/font/notdef/warn")
setfont([nd(layers=0)], "", fgid=9, keep_memory=True)
c, d = lpost("/font/notdef/warn")
print("2e  a second UNSAVED font (same empty path, its own fgId) -> noted:", d["noted"], "| already_noted:", d["already_noted"],
      "| memory:", dict(NOTDEF_NOTED))
setfont([nd(layers=0)], "", fgid=8, keep_memory=True)
c, d = lpost("/font/notdef/warn")
print("    back to the first unsaved font -> already_noted:", d["already_noted"])
setfont([Gl("A")], "fontC", fgid=6, keep_memory=True)
c, d = lpost("/font/notdef/warn")
print("2f  missing -> noted:", d["noted"], "| status:", d["status"], "| maturity in reply:", "maturity" in d)
NOTDEF_NOTED[6] = "empty"
c, d = lpost("/font/notdef/warn")
print("    the same font noted as empty before, now missing -> noted:", d["noted"])
for label, glyphs in (("drawn   ", [nd(layers=1, body=Lyr(8, 2, 1))]), ("unknown ", [nd(layers=1, body=None)]),
                      ("two lyrs", [nd(layers=2, body=Lyr())]), ("comp    ", [nd(layers=0, comps=1)])):
    setfont(glyphs); c, d = lpost("/font/notdef/warn")
    print("2g ", label, "-> status:", d["status"], "| noted:", d["noted"], "|", d.get("reason", ""), "| memory:", dict(NOTDEF_NOTED))
setfont([nd(layers=0)]); CUR["ws_raises"] = True
c1, d1 = lpost("/font/notdef/warn"); c2, d2 = lpost("/font/notdef/warn")
print("2h  fgId unreadable -> noted:", d1["noted"], d2["noted"], "(never wrongly held back) | memory:", dict(NOTDEF_NOTED),
      "\n    memory_note:", d1.get("memory_note"))
CUR["ws_raises"] = False
setfont([nd(layers=0)] + letters(drawn="o"))
c, d = lpost("/font/notdef/warn")
print("2i  mature font -> noted:", d["noted"], "| maturity:", d.get("maturity"))
print("2j  bad JSON ->", lpost("/font/notdef/warn", raw=b"{nope")[0], "| JSON list ->", lpost("/font/notdef/warn", raw=b"[1]")[0])
CUR["font"] = None
print("2k  no font open ->", lpost("/font/notdef/warn"))
print("2l  dialogs made in part 2:", len(MADE), "| the dialog code is gone:", "_show_notdef_dialog" not in src and "_NOTDEF_DIALOG_TEXT" not in src)

# ---------------------------------------------------------------- part 3: /glyph/outline ----
print("\n==== 3. /glyph/outline for a layerless / unreachable glyph ====")
setfont([nd(layers=0)]); c, d = lget("/glyph/outline?name=.notdef")
print("3a  zero layers ->", c, {k: d[k] for k in ("node_count", "layer_count", "contours", "component_count") if k in d}, "| error:", d.get("error"))
setfont([nd(layers=1, body=None)]); c, d = lget("/glyph/outline?name=.notdef")
print("3b  1 layer, unreachable ->", c, "| error:", d.get("error"), "| layer_unreachable:", d.get("layer_unreachable"), "| layer_count:", d.get("layer_count"))
setfont([nd(layers=0)]); c, d = lget("/glyph/outline?name=.notdef&layer=strict")
print("3c  zero layers, route=strict ->", c, "| node_count:", d.get("node_count"), "| layer_name:", d.get("layer_name"), "(the always-empty placeholder)")

# ---------------------------------------------------------------- server with the SDK stubbed ----
for modname in ("mcp", "mcp.server", "mcp.server.mcpserver", "mcp.server.mcpserver.exceptions"):
    sys.modules[modname] = types.ModuleType(modname)
class ToolError(Exception): pass
class MCPServer:
    def __init__(self, *a, **k): pass
    def tool(self): return lambda f: f
sys.modules["mcp.server"].MCPServer = MCPServer
sys.modules["mcp.server.mcpserver"].Context = type("Context", (), {})  # server v0.34
sys.modules["mcp.server.mcpserver.exceptions"].ToolError = ToolError
spec = importlib.util.spec_from_file_location("srv", find("glyphbridge_mcp_server.py"))
srv = importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

CALLS, REPLIES = [], {}


def fake_get(path):
    CALLS.append(("GET", path)); r = REPLIES[path]
    if isinstance(r, Exception): raise r
    return r


def fake_post(path, payload, timeout=srv.TIMEOUT_SECONDS):
    CALLS.append(("POST", path, timeout)); r = REPLIES[path]
    if isinstance(r, Exception): raise r
    return r


srv._call_listener, srv._call_listener_post = fake_get, fake_post
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN", None)


def run(fn, *a):
    CALLS.clear()
    try: return fn(*a)
    except ToolError as e: return "ToolError: " + str(e)


def short(o): return json.dumps(o, ensure_ascii=False)[:230]


print("\n==== 4. server (listener faked) ====")
ev = ["e"]
REPLIES["/version"] = {"version": "0.203"}
REPLIES["/font/notdef"] = {"open": True, "status": "has_outline", "evidence": ev}
r = run(srv.check_notdef_glyph)
print("4a  has_outline -> status:", r["status"], "| calls:", CALLS, "| agent_instruction:", r.get("agent_instruction"))
EARLY = {"mature": False, "letters_present": 2, "letters_missing": "CDEFGHIJKLMNOPQRSTUVWXYZcdefghijklmnopqrstuvwxyz", "unreadable": 0}
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": EARLY}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "noted": True, "already_noted": False, "already_warned": False,
                                "dialog_shown": False, "maturity": EARLY}
POSTS = lambda: [c[1] for c in CALLS if c[0] == "POST"]
SILENT = srv._NOTDEF_SILENT; IFASKED = srv._NOTDEF_IF_ASKED
r = run(srv.check_notdef_glyph)
print("4b  empty, early font (v0.84: not an issue) -> noted_in_output_panel:", r["noted_in_output_panel"], "| already_noted:", r.get("already_noted"),
      "| font_mature:", r["font_mature"], "| calls:", CALLS)
print("    instruction:", r["agent_instruction"], "| the silent one:", r["agent_instruction"] == SILENT)
print("    font_maturity:", r["font_maturity"])
r = run(srv.check_notdef_glyph, True)
print("4b2 the same, asked (check_notdef) -> POSTs:", POSTS(), "| instruction:", r["agent_instruction"], "| the asked one:", r["agent_instruction"] == IFASKED)
MATURE = {"mature": True, "letters_present": 52, "letters_missing": "", "unreadable": 0, "drawn_letter": "n", "letters_checked_for_outline": 1}
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": MATURE}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "noted": True, "already_noted": False, "maturity": MATURE}
r = run(srv.check_notdef_glyph); print("4d  empty, mature font -> noted:", r["noted_in_output_panel"], "| font_mature:", r["font_mature"], "| font_maturity:", r["font_maturity"],
                                       "| calls:", CALLS)
print("    instruction:", r["agent_instruction"])
r = run(srv.check_notdef_glyph, True); print("    asked: the same instruction ->", r["agent_instruction"].startswith("The font has every letter"))
REPLIES["/font/notdef/warn"] = dict(REPLIES["/font/notdef/warn"], noted=False, already_noted=True, already_warned=True)
r = run(srv.check_notdef_glyph); print("4c  mature, already noted ->", r["already_noted"], "|", r["agent_instruction"])
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "dialog_shown": False, "already_warned": True, "maturity": MATURE}
r = run(srv.check_notdef_glyph); print("    an older listener's already_warned counts too ->", r["already_noted"])
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "noted": True, "maturity": MATURE}
for label, mat in (("unknown (None)", dict(MATURE, mature=None)), ("not a bool", dict(MATURE, mature="yes")), ("absent", None)):
    REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev}
    if mat is not None:
        REPLIES["/font/notdef"]["maturity"] = mat
    r = run(srv.check_notdef_glyph)
    print("    maturity", label, "-> font_mature:", r.get("font_mature"), "| POSTs:", POSTS(), "| silent:", r["agent_instruction"] == SILENT)
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": EARLY}
r = run(srv.check_notdef_glyph)
print("4d2 the first read decides (GET early, a later read would say mature) -> POSTs:", POSTS(), "| font_mature:", r.get("font_mature"))
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": MATURE}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "noted": True, "maturity": EARLY}
r = run(srv.check_notdef_glyph)
print("4d3 the listener's re-check is reported (GET mature, warn early) -> font_mature:", r.get("font_mature"), "| letters_present:",
      r["font_maturity"].get("letters_present"))
REPLIES["/version"] = {"version": "0.202"}
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": EARLY}
r = run(srv.check_notdef_glyph)
print("4e  older listener (0.202), early font -> calls:", CALLS, "| notes:", r.get("notes"), "| silent:", r["agent_instruction"] == SILENT)
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev, "maturity": MATURE}
r = run(srv.check_notdef_glyph)
print("    older listener, mature font -> calls:", CALLS, "| noted:", r["noted_in_output_panel"], "| notes:", r.get("notes"))
REPLIES["/font/notdef"] = {"open": True, "status": "missing", "evidence": ev}
r = run(srv.check_notdef_glyph)
print("    older listener, missing     -> calls:", CALLS, "| noted:", r["noted_in_output_panel"])
REPLIES["/version"] = {"version": "0.203"}
REPLIES["/font/notdef"] = {"open": True, "status": "unknown", "evidence": ["bodyLayer was None"]}
r = run(srv.check_notdef_glyph); print("4f  unknown -> calls:", CALLS, "|", r["agent_instruction"][:58])
REPLIES["/font/notdef"] = {"open": True, "status": "missing", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "missing", "evidence": ev, "noted": True}
r = run(srv.check_notdef_glyph); print("4g  missing -> noted:", r["noted_in_output_panel"], "| font_mature in reply:", "font_mature" in r, "\n    instruction:", r["agent_instruction"])
REPLIES["/font/notdef"] = {"open": True, "status": "missing", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "has_outline", "evidence": ["now drawn"], "noted": False}
r = run(srv.check_notdef_glyph); print("4h  changed between reads -> status:", r["status"], "|", r.get("notes"), "| instruction:", r.get("agent_instruction"))
REPLIES["/font/notdef"] = {"open": True, "status": "bogus"}
print("4i  malformed status ->", run(srv.check_notdef_glyph))
REPLIES["/font/notdef"] = {"open": False}
print("4j  no font open ->", run(srv.check_notdef_glyph)[:40])

print("\n-- get_current_font automatic check")
REPLIES["/font/current"] = {"open": True, "family_name": "F", "glyph_count": 2}
REPLIES["/font/notdef"] = {"open": True, "status": "has_outline", "evidence": ev}
r = run(srv.get_current_font); print("4k  auto on, drawn -> notdef status:", r["notdef"]["status"], "| calls:", [c[1] for c in CALLS])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = run(srv.get_current_font); print("4l  GLYPHBRIDGE_NOTDEF_WARN=0 -> 'notdef' key:", "notdef" in r, "| calls:", [c[1] for c in CALLS])
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN")
REPLIES["/font/notdef"] = srv.ToolError("The FontLab listener did not answer /font/notdef within 5s.")
r = run(srv.get_current_font); print("4m  notdef check fails -> font still returned:", r["family_name"], "| notdef:", r["notdef"]["status"], "|", r["notdef"]["detail"][:34])
REPLIES["/font/current"] = {"open": False}
print("4n  no font open -> still raises:", run(srv.get_current_font)[:40])
print("4o  no dialog wait left in the server:", not hasattr(srv, "NOTDEF_DIALOG_TIMEOUT_SECONDS"),
      "| the .notdef POST uses the normal time limit:", "_call_listener_post(\"/font/notdef/warn\", {})" in open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read())
_srv_src = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
print("4w  v0.84 source: no 'light sentence':", "light sentence" not in _srv_src, "| no new-font .notdef note:", "_NEW_FONT_NOTDEF" not in _srv_src and "notdef_note" not in _srv_src,
      "| check_notdef asks:", "_with_font(check_notdef_glyph, True)" in _srv_src, "| --notdef-warn asks:", "check_notdef_glyph(asked=True)" in _srv_src)

print("\n-- get_glyph_outline wording")
REPLIES["/glyph/outline?name=Q"] = {"open": True, "found": True, "layer_route": "body", "layer_count": 1, "layer_unreachable": True,
                                    "error": "layer route 'body' was None on every attempt"}
print("4p  unreachable (not .notdef):", run(srv.get_glyph_outline, "Q"))
REPLIES["/glyph/outline?name=.notdef"] = dict(REPLIES["/glyph/outline?name=Q"])
print("4q  unreachable (.notdef)     :", run(srv.get_glyph_outline, ".notdef"))
REPLIES["/glyph/outline?name=R"] = {"open": True, "found": True, "layer_route": "body", "error": "boom"}
print("4r  other error unchanged     :", run(srv.get_glyph_outline, "R"))
REPLIES["/glyph/outline?name=.notdef"] = {"open": True, "found": True, "name": ".notdef", "layer_count": 0, "node_count": 0,
                                          "contour_count_reported": 0, "contour_count_grouped": 0, "contours": [], "component_count": 0}
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "noted": True}
r = run(srv.get_glyph_outline, ".notdef")
print("4s  .notdef empty -> empty:", r["empty"], "| notdef_check:", r["notdef_check"]["status"], "noted:", r["notdef_check"]["noted_in_output_panel"],
      "| POSTs:", POSTS(), "| silent:", r["notdef_check"]["agent_instruction"] == SILENT, "\n    notes:", r["notes"])
REPLIES["/glyph/outline?name=space"] = dict(REPLIES["/glyph/outline?name=.notdef"], name="space")
r = run(srv.get_glyph_outline, "space"); print("4t  another empty glyph -> notdef_check present:", "notdef_check" in r, "| calls:", [c[1] for c in CALLS])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = run(srv.get_glyph_outline, ".notdef"); print("4u  .notdef empty, env off -> notdef_check present:", "notdef_check" in r)
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN")
REPLIES["/font/glyphs"] = {"open": True, "count": 1, "names": [".notdef"]}
r = run(srv.list_glyphs); print("4v  list_glyphs never checks .notdef -> calls:", [c[1] for c in CALLS])

print("\n-- self-check flags")
REPLIES["/font/notdef/warn"] = {"open": True, "status": "missing", "evidence": ev, "noted": True}
for argv, st in ((["x", "--check"], "empty"), (["x", "--notdef-warn"], "empty"), (["x", "--notdef-warn"], "missing")):
    REPLIES.update({"/health": {"status": "ok"}, "/font/current": {"open": True, "family_name": "F"},
                    "/version": {"version": "0.203"},
                    "/font/glyphs": {"open": True, "count": 1, "names": [".notdef"]},
                    "/font/notdef": {"open": True, "status": st, "evidence": ev}})
    CALLS.clear(); old = sys.argv; sys.argv = argv; buf = io.StringIO()
    with contextlib.redirect_stdout(buf): srv._self_check()
    sys.argv = old
    lines = [l for l in buf.getvalue().splitlines() if ".notdef status" in l or "check_notdef" in l]
    print("   ", argv[1], st, "-> notdef check lines:", [l[:46] for l in lines], "| POSTs:", [c[1] for c in CALLS if c[0] == "POST"])

# ---------------------------------------------------------------- part 5: both halves wired together ----
print("\n==== 5. end to end: stub FontLab -> real listener -> real server ====")
def wire_get(path):
    c, d = lget(path)
    if c != 200: raise ToolError(f"HTTP {c}")
    return d
def wire_post(path, payload, timeout=0):
    return lpost(path, payload)[1]
srv._call_listener, srv._call_listener_post = wire_get, wire_post
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN", None)

def e2e(glyphs, fn, *a, path="fontA", fgid=1, keep_memory=False):
    setfont(glyphs, path, fgid, keep_memory)
    return fn(*a)

r = e2e([nd(layers=0), Gl("A", unicode=0x41)], srv.get_current_font)
n = r["notdef"]
print("5a  get_current_font, empty .notdef, early font -> notdef:", n["status"], "| noted:", n["noted_in_output_panel"], "| font_mature:", n["font_mature"],
      "| silent:", n["agent_instruction"] == SILENT, "| dialogs made:", len(MADE), "| listener memory:", dict(NOTDEF_NOTED))
r = srv.get_current_font(); print("5b  get_current_font again          -> noted:", r["notdef"]["noted_in_output_panel"], "| silent:", r["notdef"]["agent_instruction"] == SILENT)
srv.list_glyphs(); print("5c  list_glyphs                     -> dialogs made:", len(MADE))
r = srv.check_notdef(); print("5d  check_notdef tool               -> status:", r["status"], "| noted:", r["noted_in_output_panel"], "| answers if asked:", r["agent_instruction"] == IFASKED)
r = e2e([nd(layers=0)], srv.get_glyph_outline, ".notdef", path="", fgid=2, keep_memory=True)
print("5e  get_glyph_outline('.notdef'), another unsaved font -> empty:", r["empty"], "| noted:", r["notdef_check"]["noted_in_output_panel"], "| dialogs made:", len(MADE))
r = e2e([nd(layers=0), Gl("A", unicode=0x41)] + letters(drawn="O", skip="A"), srv.get_current_font, fgid=1, keep_memory=True)
print("5e2 the first font grows mature    -> noted:", r["notdef"]["noted_in_output_panel"], "| font_mature:", r["notdef"]["font_mature"], "| listener memory:", dict(NOTDEF_NOTED))
r = srv.get_current_font(); print("    and again                       -> already_noted:", r["notdef"]["already_noted"], "| noted:", r["notdef"]["noted_in_output_panel"])
r = e2e([nd(layers=1, body=Lyr(8, 2, 1))], srv.get_current_font)
print("5f  drawn .notdef                   -> notdef:", r["notdef"]["status"], "| dialogs made:", len(MADE), "(none)")
r = e2e([nd(layers=1, body=None)], srv.get_current_font)
print("5g  unreachable .notdef             -> notdef:", r["notdef"]["status"], "| dialogs made:", len(MADE), "(none) |", r["notdef"]["agent_instruction"][:44])
r = e2e([Gl("A")], srv.get_current_font)
print("5h  font without .notdef            -> notdef:", r["notdef"]["status"], "| noted:", r["notdef"]["noted_in_output_panel"], "| dialogs made:", len(MADE),
      "|", r["notdef"]["agent_instruction"][:52])
r = e2e([nd(layers=0)] + letters(drawn="O"), srv.get_current_font)
print("5i  mature font, empty .notdef      -> noted:", r["notdef"]["noted_in_output_panel"], "| font_mature:", r["notdef"]["font_mature"],
      "| drawn letter:", r["notdef"]["font_maturity"].get("drawn_letter"), "|", r["notdef"]["agent_instruction"][:66])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = e2e([nd(layers=0)], srv.get_current_font)
print("5j  GLYPHBRIDGE_NOTDEF_WARN=0       -> 'notdef' key:", "notdef" in r, "| dialogs made:", len(MADE))
r = srv.check_notdef(); print("5k  ...but the explicit tool still works -> status:", r["status"], "| noted:", r["noted_in_output_panel"], "| answers if asked:", r["agent_instruction"] == IFASKED)
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN")

# ---------------------------------------------------------------- part 6: wording of the timeout message ----
print("\n==== 6. timeout wording (_do_request with a fake opener) ====")
import urllib.error


class FakeOpener:
    def __init__(self, exc): self.exc = exc
    def open(self, req, timeout=None): raise self.exc


real_opener = srv._opener
for label, exc in (("6a  socket timeout      ", TimeoutError()),
                   ("6b  URLError(timeout)   ", urllib.error.URLError(TimeoutError())),
                   ("6c  connection refused  ", urllib.error.URLError(ConnectionRefusedError()))):
    srv._opener = FakeOpener(exc)
    try:
        srv._do_request("http://127.0.0.1:8765/glyph/create", "/glyph/create", 5.0)
    except ToolError as e:
        print(label, "->", e)
srv._opener = real_opener
m = srv._timeout_message("/x", 55.0)
print("6d  says a dialog may be waiting:", "answer or close it" in m, "| names busy/frozen:", "frozen" in m, "| names the dialogs' own limit:",
      f"within {srv.DIALOG_SECONDS} s" in m, "| tells to check the state before repeating a change:", "check the font's current state" in m,
      "| path and seconds:", "/x within 55s" in m)
