"""Tests for the .notdef check and warning dialog (introduced in listener v0.46 + server v0.10).

FontLab, PythonQt and the MCP SDK are STUBBED, so this proves the logic and wording, NOT how real FontLab behaves
(a real QMessageBox has to be seen in FontLab). Part 1-3 drive the real listener source, part 4 the real server source with
a faked listener, part 5 wires the two together (stub FontLab -> listener -> server), part 6 checks the wording of the timeout message. Output is print based: review the diff
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
    def __init__(self, name, layers=1, body=None, comps=0, layers_raises=False, comps_raises=False):
        self.name, self._n, self._body, self._lr, self._cr = name, layers, body, layers_raises, comps_raises
        self._comps = [object()] * comps
        self.width = 500.0
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
    def __init__(self, glyphs, path="fontA"):
        self.glyphs, self.path, self.info = glyphs, path, types.SimpleNamespace()


CUR = {"font": None}
SHOWN = []                                # every dialog that was "shown"


class Rec:                                # recording QMessageBox
    Information, Warning, Ok, Yes, No = "Information", "Warning", "Ok", "Yes", "No"
    raises = False
    def __init__(self, icon, title, text, buttons): self.args = (icon, title, text, buttons)
    def exec_(self):
        if Rec.raises: raise RuntimeError("no GUI available")
        SHOWN.append(self.args)
        return 1


fl = types.ModuleType("fontlab"); fl.CurrentFont = lambda: CUR["font"]
pq = types.ModuleType("PythonQt"); qc = types.ModuleType("QtCore"); pq.QtCore = qc
qg = types.ModuleType("PythonQt.QtGui"); qg.QMessageBox = object
sys.modules.update({"fontlab": fl, "PythonQt": pq, "PythonQt.QtCore": qc, "PythonQt.QtGui": qg})
src = open(find("glyphbridge_fontlab_mcp_listener.py"), encoding="utf-8").read().replace("\nstart()\n", "\n")
ns = {}
exec(compile(src, "glyphbridge_fontlab_mcp_listener.py", "exec"), ns)
ns["QMessageBox"] = Rec
NOTDEF_WARNED = ns["_NOTDEF_WARNED"]


def lget(path):
    h, _, b = ns["_route"]("GET", path).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def lpost(path, payload=None, raw=None):
    body = raw if raw is not None else json.dumps(payload or {}).encode()
    h, _, b = ns["_route"]("POST", path, body).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def setfont(glyphs, path="fontA"):
    CUR["font"] = Font(glyphs, path)
    NOTDEF_WARNED.clear(); SHOWN.clear(); Rec.raises = False


def nd(**kw): return Gl(".notdef", **kw)


def status_of(glyphs):
    setfont(glyphs); c, d = lget("/font/notdef")
    return d


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
setfont([nd(layers=0)]); n0 = len(SHOWN); lget("/font/notdef"); lget("/font/notdef")
print("1n  GET never shows a dialog                            -> dialogs shown:", len(SHOWN) - n0)

# ---------------------------------------------------------------- part 2: the dialog ----
print("\n==== 2. warning dialog (POST /font/notdef/warn) ====")
setfont([nd(layers=0)], "fontA")
c, d = lpost("/font/notdef/warn")
print("2a  empty -> shown:", d["dialog_shown"], "| already_warned:", d["already_warned"], "| dialogs:", len(SHOWN))
icon, title, text, buttons = SHOWN[0]
print("    icon:", icon, "| buttons:", buttons, "\n    title:", title, "\n    text :", repr(text))
c, d = lpost("/font/notdef/warn")
print("2b  second call, same font -> shown:", d["dialog_shown"], "| already_warned:", d["already_warned"], "| dialogs:", len(SHOWN))
c, d = lpost("/font/notdef/warn", {"force": True})
print("2c  force=true -> shown:", d["dialog_shown"], "| dialogs:", len(SHOWN))
c, d = lpost("/font/notdef/warn", {"force": "yes"})
print("2d  force=\"yes\" (not boolean true) -> shown:", d["dialog_shown"], "| already_warned:", d["already_warned"])
CUR["font"].path = "fontB"
c, d = lpost("/font/notdef/warn")
print("2e  different font path -> shown:", d["dialog_shown"], "| dialogs:", len(SHOWN))
setfont([Gl("A")], "fontC")
c, d = lpost("/font/notdef/warn")
print("2f  missing -> shown:", d["dialog_shown"], "| status:", d["status"], "\n    text :", repr(SHOWN[-1][2]))
for label, glyphs in (("drawn   ", [nd(layers=1, body=Lyr(8, 2, 1))]), ("unknown ", [nd(layers=1, body=None)]),
                      ("two lyrs", [nd(layers=2, body=Lyr())]), ("comp    ", [nd(layers=0, comps=1)])):
    setfont(glyphs); c, d = lpost("/font/notdef/warn")
    print("2g ", label, "-> status:", d["status"], "| shown:", d["dialog_shown"], "| dialogs:", len(SHOWN), "|", d.get("reason", ""))
setfont([nd(layers=0)]); Rec.raises = True
c, d = lpost("/font/notdef/warn")
print("2h  dialog raises -> shown:", d["dialog_shown"], "| dialog_error:", d.get("dialog_error"), "| remembered as warned:", bool(NOTDEF_WARNED))
Rec.raises = False; c, d = lpost("/font/notdef/warn")
print("    next call tries again -> shown:", d["dialog_shown"])
print("2i  bad JSON ->", lpost("/font/notdef/warn", raw=b"{nope")[0], "| JSON list ->", lpost("/font/notdef/warn", raw=b"[1]")[0])
CUR["font"] = None
print("2j  no font open ->", lpost("/font/notdef/warn"))

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
REPLIES["/font/notdef"] = {"open": True, "status": "has_outline", "evidence": ev}
r = run(srv.check_notdef_glyph)
print("4a  has_outline -> status:", r["status"], "| calls:", CALLS, "| agent_instruction:", r.get("agent_instruction"))
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "dialog_shown": True, "already_warned": False}
r = run(srv.check_notdef_glyph)
print("4b  empty, dialog shown -> shown:", r["dialog_shown"], "| calls:", CALLS)
print("    instruction:", r["agent_instruction"])
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "dialog_shown": False, "already_warned": True}
r = run(srv.check_notdef_glyph); print("4c  already warned ->", r["already_warned"], "|", r["agent_instruction"][:70])
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "dialog_shown": False, "already_warned": False, "dialog_error": "RuntimeError: no GUI"}
r = run(srv.check_notdef_glyph); print("4d  dialog failed ->", r["dialog_error"], "|", r["agent_instruction"][:60])
REPLIES["/font/notdef"] = {"open": True, "status": "unknown", "evidence": ["bodyLayer was None"]}
r = run(srv.check_notdef_glyph); print("4e  unknown -> calls:", CALLS, "|", r["agent_instruction"][:58])
REPLIES["/font/notdef"] = {"open": True, "status": "missing", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "missing", "evidence": ev, "dialog_shown": True, "already_warned": False}
r = run(srv.check_notdef_glyph); print("4f  missing -> shown:", r["dialog_shown"], "|", r["agent_instruction"][:68])
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "has_outline", "evidence": ["now drawn"], "dialog_shown": False, "already_warned": False}
r = run(srv.check_notdef_glyph); print("4g  changed between reads -> status:", r["status"], "|", r.get("notes"))
REPLIES["/font/notdef"] = {"open": True, "status": "bogus"}
print("4h  malformed status ->", run(srv.check_notdef_glyph))
REPLIES["/font/notdef"] = {"open": False}
print("4i  no font open ->", run(srv.check_notdef_glyph)[:40])

print("\n-- get_current_font automatic check")
REPLIES["/font/current"] = {"open": True, "family_name": "F", "glyph_count": 2}
REPLIES["/font/notdef"] = {"open": True, "status": "has_outline", "evidence": ev}
r = run(srv.get_current_font); print("4j  auto on, drawn -> notdef status:", r["notdef"]["status"], "| calls:", [c[1] for c in CALLS])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = run(srv.get_current_font); print("4k  GLYPHBRIDGE_NOTDEF_WARN=0 -> 'notdef' key:", "notdef" in r, "| calls:", [c[1] for c in CALLS])
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN")
REPLIES["/font/notdef"] = srv.ToolError("The FontLab listener did not answer /font/notdef within 5s.")
r = run(srv.get_current_font); print("4l  notdef check fails -> font still returned:", r["family_name"], "| notdef:", r["notdef"]["status"], "|", r["notdef"]["detail"][:34])
REPLIES["/font/current"] = {"open": False}
print("4m  no font open -> still raises:", run(srv.get_current_font)[:40])

print("\n-- get_glyph_outline wording")
REPLIES["/glyph/outline?name=Q"] = {"open": True, "found": True, "layer_route": "body", "layer_count": 1, "layer_unreachable": True,
                                    "error": "layer route 'body' was None on every attempt"}
print("4n  unreachable (not .notdef):", run(srv.get_glyph_outline, "Q"))
REPLIES["/glyph/outline?name=.notdef"] = dict(REPLIES["/glyph/outline?name=Q"])
print("4o  unreachable (.notdef)     :", run(srv.get_glyph_outline, ".notdef"))
REPLIES["/glyph/outline?name=R"] = {"open": True, "found": True, "layer_route": "body", "error": "boom"}
print("4p  other error unchanged     :", run(srv.get_glyph_outline, "R"))
REPLIES["/glyph/outline?name=.notdef"] = {"open": True, "found": True, "name": ".notdef", "layer_count": 0, "node_count": 0,
                                          "contour_count_reported": 0, "contour_count_grouped": 0, "contours": [], "component_count": 0}
REPLIES["/font/notdef"] = {"open": True, "status": "empty", "evidence": ev}
REPLIES["/font/notdef/warn"] = {"open": True, "status": "empty", "evidence": ev, "dialog_shown": True, "already_warned": False}
r = run(srv.get_glyph_outline, ".notdef")
print("4q  .notdef empty -> empty:", r["empty"], "| notdef_check:", r["notdef_check"]["status"], "dialog_shown:", r["notdef_check"]["dialog_shown"], "\n    notes:", r["notes"])
REPLIES["/glyph/outline?name=space"] = dict(REPLIES["/glyph/outline?name=.notdef"], name="space")
r = run(srv.get_glyph_outline, "space"); print("4r  another empty glyph -> notdef_check present:", "notdef_check" in r, "| calls:", [c[1] for c in CALLS])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = run(srv.get_glyph_outline, ".notdef"); print("4s  .notdef empty, env off -> notdef_check present:", "notdef_check" in r)
os.environ.pop("GLYPHBRIDGE_NOTDEF_WARN")
REPLIES["/font/glyphs"] = {"open": True, "count": 1, "names": [".notdef"]}
r = run(srv.list_glyphs); print("4t  list_glyphs never checks .notdef -> calls:", [c[1] for c in CALLS])

print("\n-- self-check flags")
for argv in (["x", "--check"], ["x", "--notdef-warn"]):
    REPLIES.update({"/health": {"status": "ok"}, "/font/current": {"open": True, "family_name": "F"},
                    "/version": {"version": "0.51"},
                    "/font/glyphs": {"open": True, "count": 1, "names": [".notdef"]},
                    "/font/notdef": {"open": True, "status": "empty", "evidence": ev}})
    CALLS.clear(); old = sys.argv; sys.argv = argv; buf = io.StringIO()
    with contextlib.redirect_stdout(buf): srv._self_check()
    sys.argv = old
    lines = [l for l in buf.getvalue().splitlines() if ".notdef status" in l or "check_notdef" in l]
    print("   ", argv[1], "-> notdef check lines:", [l[:46] for l in lines], "| POSTs:", [c[1] for c in CALLS if c[0] == "POST"])

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

def e2e(label, glyphs, fn, *a, path="fontA"):
    setfont(glyphs, path); r = fn(*a)
    return r

r = e2e("", [nd(layers=0), Gl("A")], srv.get_current_font)
print("5a  get_current_font, empty .notdef  -> notdef:", r["notdef"]["status"], "| dialogs:", len(SHOWN), "| instruction:", r["notdef"]["agent_instruction"][:48])
r = srv.get_current_font(); print("5b  get_current_font again          -> already_warned:", r["notdef"]["already_warned"], "| dialogs still:", len(SHOWN))
srv.list_glyphs(); print("5c  list_glyphs                     -> dialogs still:", len(SHOWN))
r = srv.check_notdef(); print("5d  check_notdef tool               -> status:", r["status"], "| dialogs still:", len(SHOWN), "(once per font)")
r = e2e("", [nd(layers=0)], srv.get_glyph_outline, ".notdef", path="fontB")
print("5e  get_glyph_outline('.notdef'), new font -> empty:", r["empty"], "| dialogs:", len(SHOWN), "| notdef_check.dialog_shown:", r["notdef_check"]["dialog_shown"])
r = e2e("", [nd(layers=1, body=Lyr(8, 2, 1))], srv.get_current_font)
print("5f  drawn .notdef                   -> notdef:", r["notdef"]["status"], "| dialogs:", len(SHOWN), "(none)")
r = e2e("", [nd(layers=1, body=None)], srv.get_current_font)
print("5g  unreachable .notdef             -> notdef:", r["notdef"]["status"], "| dialogs:", len(SHOWN), "(none) |", r["notdef"]["agent_instruction"][:44])
r = e2e("", [Gl("A")], srv.get_current_font)
print("5h  font without .notdef            -> notdef:", r["notdef"]["status"], "| dialogs:", len(SHOWN), "| text starts:", SHOWN[0][2][:42])
os.environ["GLYPHBRIDGE_NOTDEF_WARN"] = "0"
r = e2e("", [nd(layers=0)], srv.get_current_font)
print("5i  GLYPHBRIDGE_NOTDEF_WARN=0       -> 'notdef' key:", "notdef" in r, "| dialogs:", len(SHOWN))
r = srv.check_notdef(); print("5j  ...but the explicit tool still works -> status:", r["status"], "| dialogs:", len(SHOWN))
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
m = srv._timeout_message("/x", 120.0)
print("6d  mentions a waiting dialog:", "dialog" in m, "| still names busy/frozen:", "frozen" in m,
      "| tells to check the state before repeating a change:", "check the font's current state" in m, "| path and seconds:", "/x within 120s" in m)
