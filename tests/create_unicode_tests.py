"""Tests for the Unicode reporting of create_glyph (listener v0.49 + server v0.13) and, from listener v0.50 + server v0.14, for
uniXXXX / uXXXX names and the duplicate-codepoint warning of set_glyph_unicode; from listener v0.51 + server v0.15 for the three live
fixes (clearing a codepoint with 0, FontLab stripping characters from names, holders at creation); server v0.16 refuses every
character outside A-Z a-z 0-9 . _ - (the set FontLab was seen to keep); server v0.17 reports versions in fontlab_status and words the
warning for lowercase / malformed uniXXXX names accurately (FontLab maps lowercase hex, seen live).
Server v0.18 (save policy): part 8 checks that nothing in Glyphbridge saves (a spy font and a static scan), font_modified on every real change,
the single finish_changes reminder per task package, and which transport errors count as an unknown outcome.

FontLab and the MCP SDK are STUBBED. The fake font's createGlyph() mimics what was SEEN live (checklist scenario 20): a standard
name gets a codepoint by itself ('B' -> 66, 'C' -> 67, 'eacute' and 'uni00E9' -> 233), any other name gets none; characters outside printable ASCII are STRIPPED
from the name (e-acute -> 'eacut', 'a b' -> 'ab', a lone e-acute -> an empty name); and the automatic codepoint is SKIPPED when another
glyph already holds it (seen once: B.alt held 66, then B got none). So this proves the logic and wording,
NOT how real FontLab behaves: that the codepoint is already readable INSIDE the same create call needs the live check.
Part 1 drives the real listener source, part 2 the real server source with a faked listener, part 3 the naming hints, part 4
wires both together (stub FontLab -> listener -> server) including set_glyph_unicode's 'changed', part 5 the duplicate-codepoint scan
(listener), warning (server) and an end-to-end run. Output is print based: review
the diff against expected_create_unicode_output.txt before using run_all.py --update."""
import importlib.util, json, os, sys, types

HERE = os.path.dirname(os.path.abspath(__file__))


def find(name):
    for d in (os.path.join(HERE, ".."), HERE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit("cannot find " + name)


# ---------------------------------------------------------------- fake FontLab ----
AUTO = {"B": 66, "C": 67, "eacute": 233, "uni00E9": 233}   # what FontLab was seen to assign by itself (uni names too)


class Gl:
    def __init__(self, name, uni=0, read_raises=False):
        self.name, self._uni, self._rr, self.width = name, uni, read_raises, 500.0
        self.layers, self.components = [], []     # a fresh glyph: no layer, no component (positively empty; v0.68 width route)
    @property
    def unicode(self):
        if self._rr: raise RuntimeError("unicode read failed")
        return self._uni
    @unicode.setter
    def unicode(self, v): self._uni = v
    def update(self): pass


class Font:
    def __init__(self, glyphs=(), none_value=0, noop=False, read_raises=False, path="fontA", strip_extra=""):
        self.glyphs, self.path, self.info = list(glyphs), path, types.SimpleNamespace()
        self.none_value, self.noop, self.read_raises = none_value, noop, read_raises
        self.strip_extra = strip_extra               # HYPOTHETICAL extra characters FontLab might strip (not seen live)
    def _held(self, code):
        for g in self.glyphs:
            try:
                if g.unicode == code: return True
            except Exception: pass
        return False
    def createGlyph(self, name):
        if self.noop: return None                     # FontLab "did nothing"
        kept = "".join(c for c in name if 33 <= ord(c) <= 126 and c not in self.strip_extra)   # stripped silently (seen live)
        code = AUTO.get(kept, self.none_value)
        if code and self._held(code): code = self.none_value                                     # automatic codepoint skipped
        g = Gl(kept, code, self.read_raises)
        self.glyphs.append(g); return g
    def update(self): pass


CUR = {"font": None}
fl = types.ModuleType("fontlab"); fl.CurrentFont = lambda: CUR["font"]
pq = types.ModuleType("PythonQt"); qc = types.ModuleType("QtCore"); pq.QtCore = qc
qg = types.ModuleType("PythonQt.QtGui"); qg.QMessageBox = object
sys.modules.update({"fontlab": fl, "PythonQt": pq, "PythonQt.QtCore": qc, "PythonQt.QtGui": qg})
src = open(find("glyphbridge_fontlab_mcp_listener.py"), encoding="utf-8").read().replace("\nstart()\n", "\n")
ns = {}
exec(compile(src, "glyphbridge_fontlab_mcp_listener.py", "exec"), ns)
# v0.127: the parts below test names and Unicode; the layer step of create_glyph has its own part 30, which restores the real one.
_real_create_glyph_layer = ns["_create_glyph_layer"]
ns["_create_glyph_layer"] = lambda name: {}


def lget(path):
    h, _, b = ns["_route"]("GET", path).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def lpost(path, payload=None):
    h, _, b = ns["_route"]("POST", path, json.dumps(payload or {}).encode()).partition(b"\r\n\r\n")
    return int(h.split()[1]), json.loads(b)


def short(d, keys):
    return {k: d[k] for k in keys if k in d}


# ---------------------------------------------------------------- part 1: the listener ----
print("==== 1. listener POST /glyph/create reports the Unicode of the new glyph ====")
K = ("created", "unicode", "unicode_status", "unicode_error", "reason")
cases = [
    ("1a  'B'  (standard)                   ", "B", Font()),
    ("1b  'eacute' (Adobe Glyph List name)  ", "eacute", Font()),
    ("1c  'zzcontrol', FontLab says 0       ", "zzcontrol", Font(none_value=0)),
    ("1d  'zzcontrol', FontLab says None    ", "zzcontrol", Font(none_value=None)),
    ("1e  'B', reading .unicode raises      ", "B", Font(read_raises=True)),
    ("1f  createGlyph does nothing          ", "B", Font(noop=True)),
    ("1g  name already exists               ", "B", Font(glyphs=[Gl("B", 66)])),
]
for label, name, font in cases:
    CUR["font"] = font; c, d = lpost("/glyph/create", {"name": name})
    print(label, "->", c, short(d, K))
K2 = ("created", "unicode", "unicode_status", "created_under_other_names", "duplicate_check", "reason")
for label, name, font, extra in (
        ("1j  e-acute at the end of a name (stripped)  ", "eacut\u00e9", Font(), {}),
        ("1k  a lone e-acute (name becomes EMPTY)      ", "\u00e9", Font(), {}),
        ("1l  ...and an empty-named glyph already there", "\u00e9", Font(glyphs=[Gl("")]), {}),
        ("1m  'a b' (space stripped)                   ", "a b", Font(), {}),
        ("1n  B, scan 66, B.alt already holds 66       ", "B", Font(glyphs=[Gl("B.alt", 66)]), {"scan_unicode": 66}),
        ("1o  B, scan 66, nobody holds it (assigned)   ", "B", Font(), {"scan_unicode": 66}),
        ("1p  zzcontrol, scan 66 (none, nobody holds)  ", "zzcontrol", Font(glyphs=[Gl("A", 65)]), {"scan_unicode": 66}),
        ("1q  zzcontrol, scan 65: A is the holder      ", "zzcontrol", Font(glyphs=[Gl("A", 65)]), {"scan_unicode": 65}),
        ("1r  zzcontrol, no scan_unicode field         ", "zzcontrol", Font(glyphs=[Gl("A", 65)]), {}),
        ("1s  scan_unicode True (ignored)              ", "zzcontrol", Font(glyphs=[Gl("A", 1)]), {"scan_unicode": True}),
        ("1t  scan_unicode 0 (ignored)                 ", "zzcontrol", Font(), {"scan_unicode": 0}),
        ("1u  scan_unicode '66' (ignored)              ", "zzcontrol", Font(), {"scan_unicode": "66"}),
        ("1v  scan_unicode 1114112 (ignored)           ", "zzcontrol", Font(), {"scan_unicode": 0x110000})):
    CUR["font"] = font; c, d = lpost("/glyph/create", {"name": name, **extra})
    print(label, "->", c, short(d, K2))
CUR["font"] = None
print("1h  no font open                       ->", lpost("/glyph/create", {"name": "B"}))
CUR["font"] = Font(); print("1i  /version                           ->", lget("/version")[1])

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

REPLY = {}


POSTED = []


def fake_post(path, payload, timeout=srv.TIMEOUT_SECONDS):
    POSTED.append((path, payload))
    return REPLY[path]


srv._call_listener_post = fake_post


def listener_says(**kw):
    base = {"open": True, "created": True, "before_count": 6, "after_count": 7}
    base.update(kw); REPLY["/glyph/create"] = base


# ---------------------------------------------------------------- part 2: the server's reading of the reply ----
print("\n==== 2. server create_glyph: fields and agent_instruction (faked listener replies) ====")
SK = ("unicode", "unicode_status", "unicode_assigned_by_fontlab", "unicode_matches_standard", "name_warnings")
cases = [
    ("2a  'B' assigned 66 (matches)            ", "B", dict(unicode=66, unicode_status="assigned")),
    ("2b  'eacute' assigned 233 (not judged)   ", "eacute", dict(unicode=233, unicode_status="assigned")),
    ("2c  'zzcontrol' none                     ", "zzcontrol", dict(unicode=None, unicode_status="none")),
    ("2d  single char 'Q' but none             ", "Q", dict(unicode=None, unicode_status="none")),
    ("2e  'B' but FontLab gave 67 (wrong)      ", "B", dict(unicode=67, unicode_status="assigned")),
    ("2f  unreadable                           ", "zzcontrol", dict(unicode=None, unicode_status="unreadable", unicode_error="boom")),
    ("2g  OLDER listener (no unicode fields)   ", "B", {}),
    ("2h  'assigned' with a non-codepoint value", "B", dict(unicode="66", unicode_status="assigned")),
    ("2i  'assigned' with True                 ", "B", dict(unicode=True, unicode_status="assigned")),
    ("2n  'uni00E9' none (no holder info)      ", "uni00E9", dict(unicode=None, unicode_status="none")),
    ("2o  'uni00E9' assigned 233 (matches)     ", "uni00E9", dict(unicode=233, unicode_status="assigned")),
    ("2p  'uni00E9' assigned 234 (wrong)       ", "uni00E9", dict(unicode=234, unicode_status="assigned")),
    ("2q  'u1F600' none                        ", "u1F600", dict(unicode=None, unicode_status="none")),
    ("2r  'uniD800' (surrogate) none           ", "uniD800", dict(unicode=None, unicode_status="none")),
    ("2s  'uni00E90041' (a sequence) none      ", "uni00E90041", dict(unicode=None, unicode_status="none")),
    ("2t  'uni00e9' (lowercase) none           ", "uni00e9", dict(unicode=None, unicode_status="none")),
]
for label, name, kw in cases:
    listener_says(**kw); r = srv.create_new_glyph(name)
    print(label, "->", short(r, SK))
    print("     instruction:", r["agent_instruction"])
listener_says(unicode=None, unicode_status="none"); r = srv.create_new_glyph("9lives")
print("2m  naming hint is appended to the instruction ->", r["agent_instruction"][-96:], "|", len(r["name_warnings"]), "warning")
SK2 = ("unicode_status", "unicode_matches_standard", "also_held_by", "glyphs_scanned")
for label, name, check in (
        ("2u  B none, B.alt holds 66                ", "B", dict(scanned=5, also_held_by=["B.alt"], unreadable=0)),
        ("2v  B none, two holders                   ", "B", dict(scanned=5, also_held_by=["B.alt", "B.sc"], unreadable=0)),
        ("2w  uni00E9 none, clean scan, no holder   ", "uni00E9", dict(scanned=5, also_held_by=[], unreadable=0)),
        ("2x  uni00E9 none, 2 unreadable glyphs     ", "uni00E9", dict(scanned=3, also_held_by=[], unreadable=2)),
        ("2y  uni00E9 none, scan failed             ", "uni00E9", dict(scanned=0, also_held_by=[], unreadable=0, scan_error="boom")),
        ("2z  uni00E9 none, a holder AND unreadable ", "uni00E9", dict(scanned=3, also_held_by=["eacute"], unreadable=1))):
    listener_says(unicode=None, unicode_status="none", duplicate_check=check); r = srv.create_new_glyph(name)
    print(label, "->", short(r, SK2))
    print("     instruction:", r["agent_instruction"])
listener_says(unicode=233, unicode_status="assigned", duplicate_check=dict(scanned=5, also_held_by=["x"], unreadable=0)); r = srv.create_new_glyph("eacute")
print("2za assigned: a stray duplicate_check is not used ->", short(r, SK2))
listener_says(unicode=None, unicode_status="none", duplicate_check=dict(scanned=5, also_held_by=["x"], unreadable=0)); r = srv.create_new_glyph("zzcontrol")
print("2zb non-standard name: holders ignored (no stated codepoint) ->", short(r, SK2))

print("-- names FontLab would strip are refused BEFORE the listener is called")
for name in ("\u00e9", "eacut\u00e9", "a b", "tab\there", "x\x00y", "\u00e9\u00e8", "caf\u00e9",
             "a#b/c*d:e", "p+q@r!s$t%u&v(w)x~y=z", "x/y", "q'r", 'q"r', "q\\r", "q[r]", "q{r}", "q<r>", "q,r;s?t", "q^r|s`t"):
    POSTED.clear()
    try:
        srv.create_new_glyph(name); print("2zc ", repr(name), "-> NOT refused (listener calls:", len(POSTED), ")")
    except ToolError as e:
        print("2zc ", ascii(name).ljust(16), "-> refused | listener calls:", len(POSTED), "|", str(e)[:78], "...", str(e)[-62:])
print("-- names built from the safe set, or with a warning FontLab accepts, are NOT refused")
for name in ("m-n_o.p", "9lives", ".hidden", "A.alt", "f_i", "uni00E9", "a" * 64, "k" * 130):
    POSTED.clear(); listener_says(unicode=None, unicode_status="none")
    try:
        r = srv.create_new_glyph(name)
        print("2zf ", (name if len(name) < 20 else name[:6] + "...(" + str(len(name)) + ")").ljust(12), "-> accepted | listener calls:", len(POSTED), "| warnings:", len(r.get("name_warnings", [])))
    except ToolError as e:
        print("2zf ", name[:12], "-> REFUSED:", str(e)[:70])
print("-- what is sent to the listener")
for name in ("B", "uni00E9", "u1F600", "zzcontrol", "A.alt", "uniD800"):
    POSTED.clear(); listener_says(unicode=None, unicode_status="none"); srv.create_new_glyph(name)
    print("2zd ", name.ljust(10), "->", POSTED[-1])
print("-- a glyph appeared under another name (the server's message)")
for other in (["eacut"], [""], ["", "x"]):
    REPLY["/glyph/create"] = {"open": True, "created": False, "created_under_other_names": other,
                              "reason": "createGlyph() did not raise, but FontLab created a glyph under a different name instead",
                              "before_count": 6, "after_count": 7}
    try:
        srv.create_new_glyph("a-b")
    except ToolError as e:
        print("2ze ", other, "->", e)
listener_says(unicode=66, unicode_status="assigned"); r = srv.create_new_glyph("  B  ")
print("2j  name is stripped; keys in order     ->", list(r))
REPLY["/glyph/create"] = {"open": True, "created": False, "reason": "a glyph with this name already exists"}
try:
    srv.create_new_glyph("B")
except ToolError as e:
    print("2k  failed creation still raises         ->", e)
REPLY["/glyph/create"] = {"open": False}
try:
    srv.create_new_glyph("B")
except ToolError as e:
    print("2l  no font open still raises            ->", str(e)[:50])

# ---------------------------------------------------------------- part 3: naming hints ----
print("\n==== 3. name_warnings (hints only; the glyph is created regardless) ====")
for name in ("B", "7", "A.alt", "f_i", "uni00E9", "my-glyph", "eacute", ".notdef",
             "9lives", ".hidden", "x" * 64, "x" * 63, "x" * 130,
             "uni00e9", "uni00E", "uni00E90041", "u1F600", "u00e9", "unite", "uniform",
             "uni00e8", "u1f600", "uni00e90041", "uni00E9004", "u00E9X"):
    w = srv._name_warnings(name)
    label = name if len(name) < 20 else name[:8] + "...(" + str(len(name)) + ")"
    print(f"3   {label!r:24}", "->", [x[:44] for x in w] if w else "no warnings")

print("3b  full text, lowercase hex  :", srv._name_warnings("uni00e8")[0])
print("3c  full text, wrong length    :", srv._name_warnings("uni00E")[0])
print("3d  suggested fix for u1f600   :", srv._name_warnings("u1f600")[0][:80])

# ---------------------------------------------------------------- part 4: end to end ----
print("\n==== 4. end to end: stub FontLab -> real listener -> real server ====")
def wire_post(path, payload, timeout=0):
    return lpost(path, payload)[1]
def wire_get(path):
    c, d = lget(path)
    if c != 200: raise ToolError(f"HTTP {c}")
    return d
srv._call_listener, srv._call_listener_post = wire_get, wire_post

CUR["font"] = Font(glyphs=[Gl(".notdef"), Gl("A", 65)])
for name in ("B", "eacute", "zzcontrol", "9lives"):
    r = srv.create_new_glyph(name)
    print("4a ", name.encode("ascii", "backslashreplace").decode(), "->", short(r, ("unicode", "unicode_status", "unicode_assigned_by_fontlab", "unicode_matches_standard")),
          "| warnings:", len(r.get("name_warnings", [])))
print("4b  full reply for 'A.alt':", json.dumps(srv.create_new_glyph("A.alt")))
r = srv.set_glyph_unicode("B", 66)
print("4c  set_glyph_unicode('B', 66) after creation   ->", short(r, ("unicode_before", "unicode_after", "changed")), "| note starts:", r.get("note", "")[:34])
r = srv.set_glyph_unicode("zzcontrol", 0xE000)
print("4d  set_glyph_unicode('zzcontrol', 0xE000)      ->", short(r, ("unicode_before", "unicode_after", "changed")), "| note:", r.get("note"))
r = srv.set_glyph_unicode("zzcontrol", 0xE000)
print("4e  ...same call again                          ->", short(r, ("unicode_before", "unicode_after", "changed")), "| note starts:", r.get("note", "")[:34])
try:
    srv.set_glyph_unicode("nosuch", 65)
except ToolError as e:
    print("4f  unknown glyph still raises                  ->", e)
print("4g  docstrings mention the rule: create_glyph:", "do NOT call set_glyph_unicode" in srv.create_glyph.__doc__,
      "| set_glyph_unicode:", "Never guess a codepoint" in srv.set_glyph_unicode.__doc__)

# ---------------------------------------------------------------- part 5: duplicate codepoints ----
print("\n==== 5. duplicate codepoints: listener scan, server warning, end to end ====")
def dfont(*extra):
    return Font(glyphs=[Gl(".notdef"), Gl("A", 65), Gl("eacute", 233), Gl("uni00E9", 0), *extra])
DK = ("set", "before", "after", "duplicate_check")
cases = [
    ("5a  uni00E9 -> 233, eacute holds it        ", dfont(), "uni00E9", 233),
    ("5b  uni00E9 -> 8364, nobody holds it       ", dfont(), "uni00E9", 8364),
    ("5c  two other holders                      ", dfont(Gl("eacute.alt", 233)), "uni00E9", 233),
    ("5d  an unreadable glyph in the font        ", dfont(Gl("bad", 0, read_raises=True)), "uni00E9", 233),
    ("5e  A -> 65 (A itself is not 'another')    ", dfont(), "A", 65),
    ("5f  clearing: uni00E9 -> 0                 ", dfont(), "uni00E9", 0),
    ("5f2 clearing a glyph that already has none", dfont(), "uni00E9", 0),
    ("5g  glyph does not exist                   ", dfont(), "nosuch", 233),
]
for label, font, name, cp in cases:
    CUR["font"] = font; c, d = lpost("/glyph/unicode", {"name": name, "unicode": cp})
    print(label, "->", short(d, DK))
class BadGlyphs:
    @property
    def glyphs(self): raise RuntimeError("glyphs unreadable")
print("5h  font.glyphs raises (helper direct)      ->", ns["_other_glyphs_with_unicode"](BadGlyphs(), "x", 1))

srv._call_listener_post = fake_post
def set_says(**kw):
    base = {"open": True, "set": True, "name": "uni00E9", "before": None, "after": 233, "requested": 233}
    base.update(kw); REPLY["/glyph/unicode"] = base
def dup(cp=233, **check):
    return {"duplicate_check": check}
DS = ("changed", "also_held_by", "glyphs_scanned", "duplicate_check", "duplicate_warning", "duplicate_note")
for label, kw, cp in (
        ("5i  one other holder                       ", dup(scanned=3, also_held_by=["eacute"], unreadable=0), 233),
        ("5j  two other holders                      ", dup(scanned=4, also_held_by=["eacute", "eacute.alt"], unreadable=0), 233),
        ("5k  nobody, clean scan                     ", dup(scanned=3, also_held_by=[], unreadable=0), 233),
        ("5l  nobody found but 2 unreadable          ", dup(scanned=3, also_held_by=[], unreadable=2), 233),
        ("5m  scan failed                            ", dup(scanned=0, also_held_by=[], unreadable=0, scan_error="boom"), 233),
        ("5n  OLDER listener (no duplicate_check)    ", {}, 233),
        ("5o  clearing (codepoint 0): no scan, no claim", dict(after=None, before=233), 0),
        ("5o2 clearing a glyph that has none         ", dict(after=None, before=None), 0)):
    set_says(**kw); r = srv.write_glyph_unicode("uni00E9", cp)
    print(label, "->", short(r, DS))
    for key in ("duplicate_warning", "duplicate_note"):
        if key in r: print("       ", key + ":", r[key])
set_says(set=False, before=233, after=233, reason="unicode did not change to the requested value after setting")
try:
    srv.write_glyph_unicode("uni00E9", 0)
except ToolError as e:
    print("5o3 OLDER listener (< 0.51) still reports clearing as a failure ->", e)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

print("-- end to end, the live scenario: eacute holds 233, then uni00E9 is created and set")
CUR["font"] = Font(glyphs=[Gl(".notdef"), Gl("eacute", 233)])
r = srv.create_new_glyph("uni00E9")
print("5p  create uni00E9                          ->", short(r, ("unicode", "unicode_status", "unicode_matches_standard")), "\n       instruction:", r["agent_instruction"])
r = srv.check_glyph_unicode("uni00E9")
print("5q  check_glyph_unicode before setting      ->", short(r, ("unicode", "has_unicode", "expected_unicode", "matches_standard", "note")))
r = srv.set_glyph_unicode("uni00E9", 233)
print("5r  set_glyph_unicode('uni00E9', 233)       ->", short(r, DS), "\n       warning:", r.get("duplicate_warning"))
r = srv.check_glyph_unicode("uni00E9")
print("5s  check_glyph_unicode after setting       ->", short(r, ("unicode", "expected_unicode", "matches_standard")))
r = srv.check_glyph_unicode("eacute")
print("5t  check_glyph_unicode('eacute')           ->", short(r, ("unicode", "expected_unicode", "matches_standard")), "| note starts:", r["note"][:60])
print("5u  docstrings: set mentions also_held_by:", "also_held_by" in srv.set_glyph_unicode.__doc__,
      "| create mentions uniXXXX:", "uniXXXX" in srv.create_glyph.__doc__, "| check mentions uni00E9:", "uni00E9" in srv.check_glyph_unicode.__doc__)

# ---------------------------------------------------------------- part 6: the live fixes end to end ----
print("\n==== 6. end to end: the three live fixes (stub FontLab -> real listener -> real server) ====")
CUR["font"] = Font(glyphs=[Gl(".notdef"), Gl("B.alt", 66)])
r = srv.create_new_glyph("B")
print("6a  create B while B.alt holds 66           ->", short(r, SK2), "\n       instruction:", r["agent_instruction"])
r = srv.create_new_glyph("C")
print("6b  create C (nobody holds 67)              ->", short(r, SK2 + ("unicode",)))
r = srv.create_new_glyph("eacute"); r2 = srv.create_new_glyph("uni00E9")
print("6c  eacute then uni00E9: the second gets none ->", short(r, ("unicode", "unicode_status")), short(r2, ("unicode", "unicode_status", "also_held_by")))
print("       instruction for uni00E9:", r2["agent_instruction"])
r = srv.create_new_glyph("zzcontrol")
print("6d  plain non-standard name                 ->", short(r, ("unicode_status",)), "\n       instruction:", r["agent_instruction"])
r = srv.create_new_glyph("A.alt")
print("6e  suffixed name                           ->", short(r, ("unicode_status",)), "| mentions 'BUT':", "BUT" in r["agent_instruction"])
before = [g.name for g in CUR["font"].glyphs]
for name in ("\u00e9", "eacut\u00e9", "a b", "a#b/c*d:e"):
    try:
        srv.create_new_glyph(name)
    except ToolError as e:
        print("6f ", ascii(name).ljust(14), "-> refused; font unchanged:", [g.name for g in CUR["font"].glyphs] == before)
CUR["font"] = Font(glyphs=[Gl(".notdef")], strip_extra="-")   # HYPOTHETICAL safety-net test: pretend FontLab also strips '-' (it does NOT, seen live)
try:
    srv.create_new_glyph("a-b")
except ToolError as e:
    print("6g  a glyph appears under another name (hypothetical '-' stripping) ->", str(e)[:140], "...\n       glyphs now:", [g.name for g in CUR["font"].glyphs])
CUR["font"] = Font(glyphs=[Gl(".notdef"), Gl("B.alt", 66)])
r = srv.set_glyph_unicode("B.alt", 0)
print("6h  set_glyph_unicode('B.alt', 0)           ->", short(r, ("unicode_before", "unicode_after", "changed", "also_held_by", "duplicate_check")))
r = srv.check_glyph_unicode("B.alt")
print("6i  check_glyph_unicode('B.alt') afterwards ->", short(r, ("unicode", "has_unicode")))
r = srv.set_glyph_unicode("B.alt", 0)
print("6j  clearing again                          ->", short(r, ("changed", "note")))
print("6k  docstrings: create mentions refusal:", "refused before FontLab is called" in srv.create_glyph.__doc__,
      "| set mentions codepoint 0:", "codepoint 0" in srv.set_glyph_unicode.__doc__,
      "| no stale claim:", "does NOT map" not in srv.set_glyph_unicode.__doc__ and "no Unicode\n    from FontLab" not in srv.create_glyph.__doc__)

# ---------------------------------------------------------------- part 7: fontlab_status reports versions ----
print("\n==== 7. fontlab_status: server_version, listener_version, compatibility_note ====")
srv._call_listener, srv._call_listener_post = wire_get, wire_post
srv._reset_change_tracking()   # part 7 judges the status fields of a server that has not changed anything yet
CUR["font"] = Font(glyphs=[Gl(".notdef")])
r = srv.check_status()
print("7a  real listener behind the server  -> fields:", sorted(r))
print("    listener_version matches the listener's VERSION:", r["listener_version"] == ns["VERSION"],
      "| server_version matches SERVER_VERSION:", r["server_version"] == srv.SERVER_VERSION,
      "| compatibility_note:", "compatibility_note" in r)


def status_with(version_reply):
    def fake(path):
        if path == "/health": return {"status": "ok"}
        if path == "/font/current": return {"open": True, "family_name": "F", "style_name": "R", "path": "p"}
        if path == "/version":
            if version_reply is None: raise ToolError("HTTP 404")
            return version_reply
        raise AssertionError(path)
    srv._call_listener = fake
    return srv.check_status()


for label, reply in (
        ("7b  listener 0.81 (the minimum)    ", {"version": "0.81"}),
        ("7c  listener 0.50 (older)          ", {"version": "0.50"}),
        ("7d  listener 0.9 (much older)      ", {"version": "0.9"}),
        ("7e  listener 1.0 (newer)           ", {"version": "1.0"}),
        ("7f  listener 0.81.1                ", {"version": "0.81.1"}),
        ("7g  unparseable 'abc'              ", {"version": "abc"}),
        ("7h  unparseable '0.5x'             ", {"version": "0.5x"}),
        ("7i  /version answers without a version", {}),
        ("7j  version is a number, not text  ", {"version": 51}),
        ("7k  version is blank               ", {"version": "  "}),
        ("7l  /version fails (very old listener)", None)):
    r = status_with(reply)
    print(label, "->", {"listener_reachable": r["listener_reachable"], "listener_version": r["listener_version"],
                         "note": "compatibility_note" in r})
r = status_with({"version": "0.50"})
print("7m  the note itself                 ->", r["compatibility_note"])
print("7n  the fields stay in front of the font details ->", list(status_with({"version": "0.81"})))
import re
hdr_srv = re.search(r"MCP server \(v([0-9.]+)\)", open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()).group(1)
hdr_lis = re.search(r"FontLab-side listener \(v([0-9.]+)", open(find("glyphbridge_fontlab_mcp_listener.py"), encoding="utf-8").read()).group(1)
print("7o  header versions equal the constants: server", hdr_srv == srv.SERVER_VERSION, "| listener", hdr_lis == ns["VERSION"])
print("7p  fontlab_status docstring mentions the versions:", "server_version" in srv.fontlab_status.__doc__)

# ---------------------------------------------------------------- part 8: the save policy (server v0.18) ----
print("\n==== 8. save policy: nothing is ever saved; ONE bold reminder per task package (server v0.18) ====")
import io, urllib.error


def fresh(font=None):
    srv._reset_change_tracking()
    srv._call_listener, srv._call_listener_post = wire_get, wire_post
    CUR["font"] = font if font is not None else Font(glyphs=[Gl(".notdef"), Gl("A", 65)])


def fview(r):
    return {"changes": r.get("changes_in_package"), "uncertain": r.get("uncertain_changes_in_package"),
            "reminder_given": r.get("save_reminder") is not None}


fresh()
r = srv.create_new_glyph("zz1")
print("8a  create: font_modified:", r["font_modified"], "| instruction names finish_changes:", "finish_changes" in r["agent_instruction"],
      "| says do NOT remind per step:", "Do NOT remind the person after every step" in r["agent_instruction"])
f = srv.finish_change_package()
print("8b  finish_changes ->", fview(f))
t = f["save_reminder"]
print("8c  the reminder text:", t)
print("8d  bold:", t.startswith("**") and t.endswith("**"), "| names File menu and Ctrl+S:", "File menu" in t and "Ctrl+S" in t,
      "| equals SAVE_REMINDER:", t == srv.SAVE_REMINDER, "| mentions a dialog:", "dialog" in t.lower())
f2 = srv.finish_change_package()
print("8e  second finish_changes (same package) ->", fview(f2), "| note:", f2["note"])

fresh()
creates = [srv.create_new_glyph(n)["font_modified"] for n in ("p1", "p2", "p3")]
w1, w2 = srv.write_glyph_width("p1", 640), srv.write_glyph_width("p1", 640)
u1, u2 = srv.write_glyph_unicode("p2", 0xE000), srv.write_glyph_unicode("p2", 0xE000)
print("8f  three creates:", creates, "| width new / repeated:", w1["font_modified"], w2["font_modified"],
      "| unicode new / repeated:", u1["font_modified"], u2["font_modified"])
print("8g  the repeated (no-op) writes carry no save instruction:", "agent_instruction" not in w2 and "agent_instruction" not in u2)
srv._call_listener_post = lambda path, payload, timeout=0: {"open": True, "deleted": True, "before_count": 6, "after_count": 5}
d = srv.delete_existing_glyph("p3")
print("8h  delete (faked Yes in FontLab): font_modified:", d["font_modified"])
srv._call_listener_post = wire_post
print("8i  status before the package ends ->", {k: v for k, v in srv.check_status().items() if k.startswith("glyphbridge")})
f = srv.finish_change_package()
print("8j  ONE finish_changes for the whole package (3 creates + 1 width + 1 unicode + 1 delete) ->", fview(f))
st = srv.check_status()
print("8k  status after finish_changes (session total stays) ->", {k: v for k, v in st.items() if k.startswith("glyphbridge")}, "| save_note present:", "save_note" in st)
fresh()
print("8l  status with no change made: glyphbridge fields absent:", not any(k.startswith("glyphbridge") or k == "save_note" for k in srv.check_status()))

print("-- nothing changed, nothing counted")
fresh()
for label, fn in (("name with a space (refused)", lambda: srv.create_new_glyph("a b")),
                  ("name that already exists  ", lambda: srv.create_new_glyph("A")),
                  ("write to a missing glyph  ", lambda: srv.write_glyph_width("nope", 600))):
    try:
        fn(); res = "NO ERROR"
    except ToolError:
        res = "error"
    print("8m ", label, "->", res)
srv._call_listener_post = lambda path, payload, timeout=0: {"open": True, "deleted": False, "user_declined": True}
try:
    srv.delete_existing_glyph("A"); res = "NO ERROR"
except ToolError:
    res = "error"
srv._call_listener_post = wire_post
print("8n  delete declined in FontLab        ->", res)
f = srv.finish_change_package()
print("8o  finish_changes ->", fview(f), "| note says do not invent one:", "Do not invent one" in f["note"])

print("-- a failed create that still changed the font")
fresh()
srv._call_listener_post = lambda path, payload, timeout=0: {"open": True, "created": False, "created_under_other_names": ["abcde"]}
try:
    srv.create_new_glyph("abc"); msg = ""
except ToolError as e:
    msg = str(e)
print("8p  error still names the other glyph:", "'abcde'" in msg, "| says it counts as a change:", "counts as a change" in msg)
print("8q  finish_changes ->", fview(srv.finish_change_package()))

print("-- outcome unknown (timeout / unusable reply)")
fresh()
def timing_out(path, payload, timeout=0):
    raise srv.OutcomeUnknown("The FontLab listener did not answer " + path + ".")
srv._call_listener_post = timing_out
for label, fn in (("create", lambda: srv.create_new_glyph("t1")), ("width", lambda: srv.write_glyph_width("A", 700)),
                  ("unicode", lambda: srv.write_glyph_unicode("A", 65)), ("delete", lambda: srv.delete_existing_glyph("A"))):
    try:
        fn(); res = "NO ERROR"
    except srv.OutcomeUnknown as e:
        res = "error; says it may or may not have been applied: " + str("may or may not" in str(e))
    print("8r ", label, "timed out ->", res)
f = srv.finish_change_package()
print("8s  finish_changes ->", fview(f), "| uncertain_note:", "uncertain_note" in f, "| bold reminder:", f["save_reminder"] == srv.SAVE_REMINDER)
fresh()
srv._call_listener_post = lambda *a, **k: (_ for _ in ()).throw(ToolError(srv.NOT_REACHABLE))
try:
    srv.create_new_glyph("t2"); kind = "NO ERROR"
except ToolError as e:
    kind = "OutcomeUnknown" if isinstance(e, srv.OutcomeUnknown) else "plain ToolError"
print("8t  listener not reachable (nothing was sent) ->", kind, "|", fview(srv.finish_change_package()))
fresh()
srv._call_listener = lambda path: (_ for _ in ()).throw(srv.OutcomeUnknown("slow"))
try:
    srv.read_glyph_names()
except ToolError:
    pass
print("8u  a READ that times out is not counted ->", fview(srv.finish_change_package()))

print("-- which transport errors count as 'outcome unknown' (real _do_request, fake opener)")
class _Opener:
    def __init__(self, exc=None, body=b""): self.exc, self.body = exc, body
    def open(self, req, timeout=None):
        if self.exc: raise self.exc
        body = self.body
        class R:
            def __enter__(s): return s
            def __exit__(s, *a): return False
            def read(s): return body
        return R()
real_opener = srv._opener
for label, opener in (("TimeoutError", _Opener(TimeoutError())), ("URLError(timeout)", _Opener(urllib.error.URLError(TimeoutError()))),
                      ("HTTP 500", _Opener(urllib.error.HTTPError("u", 500, "x", {}, io.BytesIO(b"boom")))),
                      ("connection refused", _Opener(urllib.error.URLError(ConnectionRefusedError()))),
                      ("OSError", _Opener(OSError("x"))), ("reply not JSON", _Opener(body=b"nope")),
                      ("reply is a JSON list", _Opener(body=b"[1]")), ("valid reply", _Opener(body=b'{"a": 1}'))):
    srv._opener = opener
    try:
        out = srv._do_request("http://x", "/p", 1.0); res = "returned " + str(out)
    except ToolError as e:
        res = "OutcomeUnknown" if isinstance(e, srv.OutcomeUnknown) else "plain ToolError"
    print("8v ", label.ljust(20), "->", res)
srv._opener = real_opener

print("-- nothing in Glyphbridge may save: a spy font and a static scan")
SAVES = []
def _spy(name):
    def f(*a, **k):
        SAVES.append(name); raise RuntimeError("SAVE CALLED: " + name)
    return f
class SpyFont(Font): pass
for _n in ("save", "saveAs", "SaveAs", "saveFont", "SaveFont", "export", "exportFont", "generate", "write", "close"):
    setattr(SpyFont, _n, _spy(_n))
for _n in ("Save", "SaveAs", "SaveFont", "save", "saveAs"):
    setattr(fl, _n, _spy("fontlab." + _n))
fresh(SpyFont(glyphs=[Gl(".notdef"), Gl("A", 65)]))
for p in ("/health", "/version", "/font/current", "/font/glyphs", "/font/notdef", "/font/nonempty", "/glyph/width?name=A",
          "/glyph/unicode?name=A", "/glyph/outline?name=A"):
    lget(p)
srv.create_new_glyph("s1"); srv.write_glyph_width("s1", 610); srv.write_glyph_unicode("s1", 0xE001)
srv.check_status(); srv.read_glyph_names(); srv.read_glyph_width("A"); srv.finish_change_package()
print("8w  save-like members called on the font or on the fontlab module:", SAVES)
for _n in ("Save", "SaveAs", "SaveFont", "save", "saveAs"):
    delattr(fl, _n)
for fname in ("glyphbridge_fontlab_mcp_listener.py", "glyphbridge_mcp_server.py"):
    code = open(find(fname), encoding="utf-8").read()
    print("8x ", fname, "-> save / export / generate call syntax found:", re.findall(r"\.(?:save\w*|export\w*|generate\w*)\s*\(", code, re.I))
print("8y  the server never touches a FontLab dialog class:", "QMessageBox" not in open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read())

print("-- wording and tool surface")
print("8z  finish_changes is a tool function:", callable(srv.finish_changes), "| docstring says ONCE:", "ONCE" in srv.finish_changes.__doc__,
      "| says it changes nothing in FontLab:", "changes nothing in FontLab" in srv.finish_changes.__doc__)
print("8za write tool docstrings say the tool NEVER saves:",
      [("NEVER saves" in fn.__doc__) for fn in (srv.create_glyph, srv.set_glyph_width, srv.set_glyph_unicode, srv.delete_glyph)])
print("8zb the instruction added to every real change:", srv._SAVE_INSTRUCTION)
print("8zc the note added to an unknown outcome:      ", srv._UNSURE_NOTE)
fresh()


# ---------------------------------------------------------------- part 9: server 0.19 - advance width and sidebearing tools ----
print("\n==== 9. server 0.19: set_glyph_sidebearings, get_glyph_sidebearings, set_glyph_width extras (faked listener replies) ====")
S9 = {"posts": [], "gets": [], "version": "0.68", "get": {}, "post": {}}
def s9_get(path):
    S9["gets"].append(path)
    if path == "/version":
        if S9["version"] is None: raise srv.OutcomeUnknown("slow")
        return {"version": S9["version"]}
    return S9["get"][path.split("?")[0]]
def s9_post(path, payload, timeout=0):
    S9["posts"].append((path, payload))
    r = S9["post"][path]
    if isinstance(r, Exception): raise r
    return r
def s9_reset():
    srv._reset_change_tracking(); S9["posts"].clear(); S9["gets"].clear(); S9["version"] = "0.68"
    srv._call_listener, srv._call_listener_post = s9_get, s9_post
def s9_try(fn):
    try:
        return fn()
    except srv.OutcomeUnknown as e:
        return "OutcomeUnknown: " + str(e)[:80]
    except ToolError as e:
        return "ToolError: " + str(e)
OKSB = {"open": True, "name": "tri", "set": True, "route": "modern", "requested": {"left": 88.0, "right": 77.0},
        "before": {"lsb": 0.0, "rsb": 0.0, "advance": 500.0}, "after": {"lsb": 88.0, "rsb": 77.0, "advance": 665.0}, "ink_width": 500.0,
        "changed": True, "display_refreshed": True, "display_note": "NOTE", "checks": {"lsb_ok": True, "rsb_ok": True, "advance_ok": True}}
s9_reset(); S9["post"]["/glyph/sidebearings"] = dict(OKSB)
r = srv.write_glyph_sidebearings("tri", 88, 77)
print("9a  set 88/77        ->", r)
print("9b  sent to the listener ->", S9["posts"])
s9_reset(); S9["post"]["/glyph/sidebearings"] = dict(OKSB)
srv.write_glyph_sidebearings("tri", 60)
print("9c  right omitted    -> sent", S9["posts"][0][1])
s9_reset(); S9["post"]["/glyph/sidebearings"] = dict(OKSB, changed=False)
r = srv.write_glyph_sidebearings("tri", 88, 77)
print("9d  no-op (changed false) -> font_modified:", r["font_modified"], "| instruction absent:", "agent_instruction" not in r, "|", fview(srv.finish_change_package()))
for label, left, right in (("9e  bool left", True, 5), ("9f  string right", 5, "7"), ("9g  huge left", 99999, 5), ("9h  NaN right", 5, float("nan")), ("9i  infinite", float("inf"), 5)):
    s9_reset(); n = len(S9["posts"])
    print(label, "->", s9_try(lambda: srv.write_glyph_sidebearings("tri", left, right)), "| posts", len(S9["posts"]) - n)
s9_reset(); print("9j  empty name       ->", s9_try(lambda: srv.write_glyph_sidebearings("  ", 5, 5)), "| posts", len(S9["posts"]))
s9_reset(); S9["post"]["/glyph/sidebearings"] = {"open": False}
print("9k  no font open     ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5)))
s9_reset(); S9["post"]["/glyph/sidebearings"] = {"open": True, "found": False, "set": False, "reason": "no glyph named 'tri'"}
print("9l  unknown glyph    ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5)))
s9_reset(); S9["post"]["/glyph/sidebearings"] = {"open": True, "name": "tri", "set": False, "modern_layer": False, "reason": "this glyph has no editable layer yet: open it once in an editor tab in FontLab (double-click it in the glyph overview), then try again."}
print("9m  no editable layer ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5)), "|", fview(srv.finish_change_package()))
s9_reset(); S9["post"]["/glyph/sidebearings"] = {"open": True, "name": "tri", "set": False, "reason": "this glyph has no outline, so it has no sidebearings to set: use set_glyph_width for its advance width"}
print("9n  no outline        ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5)))
s9_reset(); S9["post"]["/glyph/sidebearings"] = dict(OKSB, set=False, changed=False, after=dict(OKSB["before"]), reason="FontLab raised an error in setSB; the re-read margins differ from the request: lsb_ok, rsb_ok, advance_ok", call_error="RuntimeError: x")
print("9o  setSB error, nothing moved ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 88, 77)), "|", fview(srv.finish_change_package()))
s9_reset(); S9["post"]["/glyph/sidebearings"] = dict(OKSB, set=False, after={"lsb": 40.0, "rsb": 65.0, "advance": 605.0}, reason="the re-read margins do not match the request: rsb_ok, advance_ok")
print("9p  moved but the re-read does not match ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 40, 60)), "|", fview(srv.finish_change_package()))
s9_reset(); S9["version"] = "0.67"; S9["post"]["/glyph/sidebearings"] = dict(OKSB)
print("9q  listener 0.67    ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5)), "| posts", len(S9["posts"]), "|", fview(srv.finish_change_package()))
s9_reset(); S9["version"] = None; S9["post"]["/glyph/sidebearings"] = dict(OKSB)
print("9r  /version unreadable -> the call goes ahead:", s9_try(lambda: srv.write_glyph_sidebearings("tri", 88, 77))["verified"], "| posts", len(S9["posts"]))
s9_reset(); S9["post"]["/glyph/sidebearings"] = srv.OutcomeUnknown("timed out")
print("9s  write times out  ->", s9_try(lambda: srv.write_glyph_sidebearings("tri", 5, 5))[:60], "|", fview(srv.finish_change_package()))
RD = {"open": True, "found": True, "name": "tri", "modern_layer": True, "readable": True, "lsb": 88.0, "rsb": 77.0, "advance": 665.0, "ink_width": 500.0}
s9_reset(); S9["get"]["/glyph/sidebearings"] = dict(RD)
print("9t  get_glyph_sidebearings ->", srv.read_glyph_sidebearings("tri"), "|", fview(srv.finish_change_package()))
s9_reset(); S9["get"]["/glyph/sidebearings"] = {"open": True, "found": True, "name": "tri", "modern_layer": False, "reason": "this glyph has no editable layer yet: open it"}
print("9u  read, no layer   ->", s9_try(lambda: srv.read_glyph_sidebearings("tri")))
s9_reset(); S9["get"]["/glyph/sidebearings"] = dict(RD, readable=False, reason="RuntimeError: getLSB refused")
print("9v  read, unreadable ->", s9_try(lambda: srv.read_glyph_sidebearings("tri")))
s9_reset(); S9["get"]["/glyph/sidebearings"] = {"open": True, "found": False, "reason": "no glyph named 'x'"}
print("9w  read, unknown    ->", s9_try(lambda: srv.read_glyph_sidebearings("x")))
s9_reset(); S9["get"]["/glyph/sidebearings"] = {"open": False}
print("9x  read, no font    ->", s9_try(lambda: srv.read_glyph_sidebearings("x")))
s9_reset(); S9["version"] = "0.60"
print("9y  read, listener 0.60 ->", s9_try(lambda: srv.read_glyph_sidebearings("x")))
s9_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "tri", "route": "modern", "before": 500.0, "after": 700.0, "requested": 700,
                                          "outline_untouched": True, "display_refreshed": True, "display_note": "NOTE"}
r = srv.write_glyph_width("tri", 700)
print("9z  width, modern reply ->", r)
s9_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "tri", "route": "modern", "before": 500.0, "after": 700.0, "requested": 700,
                                          "outline_untouched": False, "warning": "the left sidebearing changed although only the advance width was set: the outline may have moved", "display_note": "NOTE"}
print("9za width, outline moved warning passes through ->", srv.write_glyph_width("tri", 700).get("warning", "")[:40])
s9_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": False, "name": "tri", "before": None, "after": None, "requested": 700,
                                          "reason": "this glyph has no editable layer yet: open it once in an editor tab in FontLab (double-click it in the glyph overview), then try again."}
print("9zb width refused, no layer ->", s9_try(lambda: srv.write_glyph_width("tri", 700)))
s9_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "tri", "before": 500.0, "after": 640.0, "requested": 640, "route": "legacy_empty_glyph"}
r = srv.write_glyph_width("tri", 640)
print("9zc width, legacy reply (empty glyph) -> route:", r.get("route"), "| display_note absent:", "display_note" not in r, "| font_modified:", r["font_modified"])
print("9zd tool surface     -> set_glyph_sidebearings:", callable(srv.set_glyph_sidebearings), "| get_glyph_sidebearings:", callable(srv.get_glyph_sidebearings),
      "| NEVER saves in set docstring:", "NEVER saves" in srv.set_glyph_sidebearings.__doc__, "| outline moved explained:", "OUTLINE is moved" in srv.set_glyph_sidebearings.__doc__,
      "| right defaults to left:", "defaults to `left`" in srv.set_glyph_sidebearings.__doc__, "| width tool says advance only:", "ONLY the advance width" in srv.set_glyph_width.__doc__)
import inspect as _inspect
print("9ze signature        ->", _inspect.signature(srv.set_glyph_sidebearings), "|", _inspect.signature(srv.get_glyph_sidebearings))
print("9zf MIN_LISTENER_VERSION ->", srv.MIN_LISTENER_VERSION, "| server", srv.SERVER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 10: server 0.20 - draw_polygon, layer_created, reader modern_check ----
print("\n==== 10. server 0.20: draw_polygon, layer_created on set_glyph_width, get_glyph_outline modern_check (faked listener replies) ====")
S9["version"] = "0.82"
def s10_reset():
    s9_reset(); S9["version"] = "0.82"
OKPOLY = {"open": True, "name": "fresh", "drawn": True, "route": "modern", "layer_created": "test_font", "points": 4,
          "state_before": {"active_layer": "present", "shapes": 0, "nodes": 0}, "state_after": {"active_layer": "present", "shapes": 1, "nodes": 4},
          "checks": {"shapes_ok": True, "nodes_ok": True}, "changed": True, "margins": {"lsb": 0.0, "rsb": -400.0, "advance": 0.0}, "ink_width": 400.0,
          "display_refreshed": True, "display_note": "NOTE"}
RECT = [[0, 0], [400, 0], [400, 300], [0, 300]]
s10_reset(); S9["post"]["/glyph/polygon"] = dict(OKPOLY)
r = srv.write_glyph_polygon("fresh", RECT)
print("10a draw_polygon     ->", r)
print("10b sent             ->", S9["posts"], "|", fview(srv.finish_change_package()))
s10_reset(); S9["post"]["/glyph/polygon"] = dict(OKPOLY); r = srv.write_glyph_polygon("fresh", [(0, 0), (10, 0), (5, 9)])
print("10c tuples accepted  -> sent", S9["posts"][0][1]["points"])
s10_reset(); S9["post"]["/glyph/polygon"] = {k: v for k, v in OKPOLY.items() if k != "layer_created"}
print("10d layer existed    -> layer_created absent:", "layer_created" not in srv.write_glyph_polygon("fresh", RECT))
for label, pts in (("10e not a list", "abc"), ("10f two points", [[0, 0], [1, 1]]), ("10g 501 points", [[i, i * 2] for i in range(501)]),
                   ("10h bool coordinate", [[True, 0], [5, 0], [5, 5]]), ("10i string coordinate", [["0", 0], [5, 0], [5, 5]]),
                   ("10j NaN", [[float("nan"), 0], [5, 0], [5, 5]]), ("10k huge", [[20001, 0], [5, 0], [5, 5]]),
                   ("10l three numbers in a point", [[0, 0, 0], [5, 0], [5, 5]]), ("10m two distinct positions", [[0, 0], [5, 5], [0, 0], [5, 5]]),
                   ("10n point is a number", [1, 2, 3])):
    s10_reset(); n = len(S9["posts"])
    print(label, "->", s9_try(lambda: srv.write_glyph_polygon("fresh", pts)), "| posts", len(S9["posts"]) - n)
s10_reset(); print("10o empty name       ->", s9_try(lambda: srv.write_glyph_polygon("  ", RECT)), "| posts", len(S9["posts"]))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": False}; print("10p no font          ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": True, "found": False, "drawn": False, "reason": "no glyph named 'fresh'"}
print("10q unknown glyph    ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": True, "name": "fresh", "drawn": False, "reason": "the glyph's layer is not KNOWN to be empty (x), so nothing was drawn"}
print("10r not empty        ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)), "|", fview(srv.finish_change_package()))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": True, "name": "fresh", "drawn": False, "layer_created": "test_font", "changed": False, "reason": "layer.addShape(shape) failed: RuntimeError: boom"}
print("10s layer made, draw failed ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)), "|", fview(srv.finish_change_package()))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": True, "name": "fresh", "drawn": False, "changed": True, "reason": "after drawing, the layer reads 1 shape(s) and 6 node(s); expected 1 and 4"}
print("10t drawn but mismatch ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)), "|", fview(srv.finish_change_package()))
s10_reset(); S9["post"]["/glyph/polygon"] = {"open": True, "name": "fresh", "drawn": False, "reason": "the glyph has no layer yet and one could not be created automatically: the glyphs of this font have different layer names (['A', 'B']), so the right one cannot be chosen automatically"}
print("10u no layer name    ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)), "|", fview(srv.finish_change_package()))
s10_reset(); S9["version"] = "0.71"; S9["post"]["/glyph/polygon"] = dict(OKPOLY)
print("10v listener 0.71    ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT)), "| posts", len(S9["posts"]))
s10_reset(); S9["version"] = None; S9["post"]["/glyph/polygon"] = dict(OKPOLY)
print("10w /version unreadable -> goes ahead:", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT))["verified"], "| posts", len(S9["posts"]))
s10_reset(); S9["post"]["/glyph/polygon"] = srv.OutcomeUnknown("timed out")
print("10x times out        ->", s9_try(lambda: srv.write_glyph_polygon("fresh", RECT))[:50], "|", fview(srv.finish_change_package()))
s10_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "fresh", "route": "modern", "before": 0.0, "after": 600.0, "requested": 600, "layer_created": "test_font", "display_note": "NOTE"}
r = srv.write_glyph_width("fresh", 600); print("10y width + layer_created ->", {k: r.get(k) for k in ("route", "layer_created", "font_modified")})
s10_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "fresh", "route": "modern", "before": 0.0, "after": 0.0, "requested": 0, "layer_created": "test_font"}
print("10z layer made, width unchanged -> font_modified:", srv.write_glyph_width("fresh", 0)["font_modified"])
s10_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": True, "name": "fresh", "route": "legacy_empty_glyph", "before": 0.0, "after": 600.0, "requested": 600, "layer_create_note": "no other glyph of the font has an editable layer"}
print("10za legacy fallback note passes ->", srv.write_glyph_width("fresh", 600).get("layer_create_note"))
s10_reset(); S9["post"]["/glyph/width"] = {"open": True, "set": False, "name": "fresh", "layer_created": "test_font", "reason": "width did not change to the requested value after setting"}
print("10zb layer made, width failed ->", s9_try(lambda: srv.write_glyph_width("fresh", 600)), "|", fview(srv.finish_change_package()))
print("10zc tool surface    -> draw_polygon:", callable(srv.draw_polygon), "| NEVER saves:", "NEVER saves" in srv.draw_polygon.__doc__, "| example rectangle:", "[[0, 0], [400, 0], [400, 300], [0, 300]]" in srv.draw_polygon.__doc__,
      "| signature:", _inspect.signature(srv.draw_polygon), "| sidebearings doc: never creates a layer:", "never creates a layer" in srv.set_glyph_sidebearings.__doc__)
# reader
def outline_reply(**kw):
    base = {"open": True, "found": True, "name": "fresh", "layer_route": "body", "layer_name": "x", "node_count": 0, "contour_count_reported": 0,
            "contour_count_grouped": 0, "contours": [], "component_count": 0, "layer_count": 0}
    base.update(kw); return base
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(modern_check={"available": True, "modern_layer": True, "modern_nodes": 4, "modern_shapes": 1, "agree": False})
print("10zd legacy blind, modern has nodes ->", s9_try(lambda: srv.read_glyph_outline("fresh")))
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(modern_check={"available": True, "modern_layer": False})
print("10ze empty, no modern layer ->", s9_try(lambda: srv.read_glyph_outline("fresh")))
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(modern_check={"available": True, "modern_layer": True, "modern_nodes": 0, "modern_shapes": 0, "agree": True})
print("10zf empty, modern agrees ->", s9_try(lambda: srv.read_glyph_outline("fresh")))
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(modern_check={"available": False, "error": "x"})
print("10zg modern check unavailable ->", s9_try(lambda: srv.read_glyph_outline("fresh")))
_real_analyze = srv.analyze_outline
srv.analyze_outline = lambda data: {"verification": {"status": "verified"}, "notes": []}
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(node_count=3, contours=[{"nodes": []}], modern_check={"available": True, "modern_layer": True, "modern_nodes": 5, "modern_shapes": 1, "agree": False})
r = srv.read_glyph_outline("fresh"); print("10zh outline mismatch ->", r["verification"]["status"], "|", r["verification"]["modern_check"]["modern_nodes"], "|", r["notes"])
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(node_count=3, contours=[{"nodes": []}], margins={"left": 5.0, "right": 6.0, "width": 111.0}, modern_check={"available": True, "modern_layer": True, "modern_nodes": 3, "modern_shapes": 1, "agree": True})
S9["get"]["/glyph/sidebearings"] = {"open": True, "found": True, "readable": True, "modern_layer": True, "lsb": 5.0, "rsb": 6.0, "advance": 111.0, "ink_width": 100.0}   # v0.25: the extra read agrees, so the notes stay empty
r = srv.read_glyph_outline("fresh"); print("10zi outline agrees   ->", r["verification"]["status"], "| notes", r["notes"], "| modern_check kept out:", "modern_check" not in r["verification"])
s10_reset(); S9["get"]["/glyph/outline"] = outline_reply(node_count=3, contours=[{"nodes": []}])
r = srv.read_glyph_outline("fresh"); print("10zj old listener reply (no modern_check) ->", r["verification"]["status"])
srv.analyze_outline = _real_analyze
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 11: server 0.21 - outline read back from the modern layer ----
print("\n==== 11. server 0.21: get_glyph_outline with modern_outline (faked listener replies) ====")
def node(i, x, y, on=True, curve=False): return {"index": i, "x": float(x), "y": float(y), "isOn": on, "isOff": not on, "isCurve": curve, "smooth": False}
HOUSE_N = [node(i, x, y) for i, (x, y) in enumerate([(10, 20), (410, 20), (410, 220), (210, 320), (10, 220)])]
CW_N = [node(i, x, y) for i, (x, y) in enumerate([(0, 0), (0, 100), (100, 100), (100, 0)])]
def mo_reply(nodes=HOUSE_N, flag=True, margins=None, available=True, **kw):
    mo = {"available": available, "contours": [{"index": 0, "closed": True, "clockwise": flag, "nodesCount": len(nodes), "nodes": nodes}],
          "node_count": len(nodes), "expected_node_count": len(nodes)}
    if margins is not False: mo["margins"] = margins or {"lsb": 10.0, "rsb": 90.0, "advance": 500.0}
    if not available: mo = {"available": False, "error": "contour 0 node 2: getNodeAt failed: boom"}
    mo.update(kw)
    return {"open": True, "found": True, "name": "rdback", "layer_route": "body", "layer_name": "x", "node_count": 0, "contour_count_reported": 0,
            "contour_count_grouped": 0, "contours": [], "component_count": 0, "layer_count": 0,
            "modern_check": {"available": True, "modern_layer": True, "modern_nodes": len(nodes), "modern_shapes": 1, "agree": False}, "modern_outline": mo}
def read11(reply):
    s10_reset(); S9["get"]["/glyph/outline"] = reply; return srv.read_glyph_outline("rdback")
r = read11(mo_reply())
print("11a house, verified   ->", r["source"], "|", r["verification"]["status"], "|", r["verification"]["bounding_box_vs_margins"], "| bbox", r["ink_bbox"], "exact", r["ink_bbox_exact"])
print("11b fields            ->", {k: r[k] for k in ("left", "right", "advance_width", "ink_width", "contour_count", "node_count")})
c0 = r["contours"][0]
print("11c contour           ->", {k: c0[k] for k in ("closed", "node_count", "clockwise_reported", "direction_computed", "svg_path")})
print("11d first nodes       ->", c0["node_list"][:2])
print("11e notes             ->", r["notes"])
r = read11(mo_reply(CW_N, flag=False, margins={"lsb": 0.0, "rsb": 50.0, "advance": 150.0}))
print("11f clockwise points, flag false ->", r["contours"][0]["direction_computed"], "| disagreement noted:", any("clockwise flag" in n for n in r["notes"]), "|", r["verification"]["status"])
r = read11(mo_reply(CW_N, flag=True, margins={"lsb": 0.0, "rsb": 50.0, "advance": 150.0}))
print("11g clockwise points, flag true  ->", r["contours"][0]["direction_computed"], "| disagreement noted:", any("clockwise flag" in n for n in r["notes"]))
r = read11(mo_reply(margins={"lsb": 12.0, "rsb": 90.0, "advance": 500.0}))
print("11h box differs from lsb ->", r["verification"]["status"], "|", r["verification"]["reason"], "|", r["verification"]["bounding_box_vs_margins"]["left_ok"], r["verification"]["bounding_box_vs_margins"]["width_ok"])
r = read11(mo_reply(margins={"lsb": 10.0, "rsb": 90.0, "advance": 520.0}))
print("11i width differs     ->", r["verification"]["status"], "|", r["verification"]["bounding_box_vs_margins"])
curved = [node(0, 0, 0), node(1, 50, 100, on=False, curve=True), node(2, 100, 0), node(3, 100, 100)]
r = read11(mo_reply(curved, margins={"lsb": 0.0, "rsb": 0.0, "advance": 100.0}))
print("11j curves            ->", r["verification"]["status"], "|", r["verification"]["reason"][:60], "| exact", r["ink_bbox_exact"], "| kinds", [n["kind"] for n in r["contours"][0]["node_list"]], "| svg_path absent:", "svg_path" not in r["contours"][0])
r = read11(mo_reply(margins=False))
print("11k no margins        ->", r["verification"]["status"], "|", r["verification"]["reason"], "| left absent:", "left" not in r)
print("11l modern unavailable ->", s9_try(lambda: read11(mo_reply(available=False))))
bad = mo_reply(); bad["modern_check"]["agree"] = None
print("11m agree unknown, legacy blind ->", s9_try(lambda: read11(bad)))
ok = mo_reply(); ok["component_count"] = 2
print("11n components note   ->", [n for n in read11(ok)["notes"] if "component" in n])
legacy_ok = mo_reply(); legacy_ok["modern_check"].update(agree=True, modern_nodes=0, modern_shapes=0)
print("11o agree true, empty ->", read11(legacy_ok).get("empty"), "| source key absent:", "source" not in read11(legacy_ok))
print("11p doc mentions the modern route:", "source': 'modern layer'" in srv.get_glyph_outline.__doc__, "| MIN_LISTENER_VERSION", srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 12: server 0.22 - several contours, direction notes ----
print("\n==== 12. server 0.22: draw_polygon with contours, flag_follows_known_inversion (faked listener replies) ====")
RING = [[[0, 0], [300, 0], [300, 300], [0, 300]], [[100, 100], [100, 200], [200, 200], [200, 100]]]
OKRING = dict(OKPOLY, points=8, contours=2, contour_sizes=[4, 4], state_after={"active_layer": "present", "shapes": 1, "nodes": 8},
              checks={"shapes_ok": True, "nodes_ok": True, "contours_ok": True}, margins={"lsb": 0.0, "rsb": -300.0, "advance": 0.0}, ink_width=300.0)
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = dict(OKRING)
r = srv.write_glyph_polygon("ring", contours=RING)
print("12a ring              ->", {k: r[k] for k in ("verified", "points", "contours", "contour_sizes", "shapes", "nodes", "ink_width")})
print("12b sent              ->", S9["posts"])
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = dict(OKPOLY)
r = srv.write_glyph_polygon("fresh", points=RECT); print("12c single points still works -> contours", r["contours"], "| sizes", r["contour_sizes"], "| sent keys", sorted(S9["posts"][0][1]))
for label, kw in (("12d both given", dict(points=RECT, contours=RING)), ("12e neither given", dict()), ("12f empty contours", dict(contours=[])),
                  ("12g 21 contours", dict(contours=[RECT] * 21)), ("12h contours not a list", dict(contours="abc")),
                  ("12i one contour has 2 points", dict(contours=[RECT, [[0, 0], [1, 1]]])), ("12j contour is a number", dict(contours=[RECT, 5])),
                  ("12k 2500 points", dict(contours=[[[i, i * 2] for i in range(500)]] * 5)), ("12l bad coordinate", dict(contours=[RECT, [[0, 0], [5, "x"], [5, 5]]]))):
    s10_reset(); S9["version"] = "0.82"; n = len(S9["posts"])
    print(label, "->", s9_try(lambda: srv.write_glyph_polygon("fresh", **kw)), "| posts", len(S9["posts"]) - n)
s10_reset(); S9["version"] = "0.81"; S9["post"]["/glyph/polygon"] = dict(OKRING)
print("12m contours need 0.82 ->", s9_try(lambda: srv.write_glyph_polygon("ring", contours=RING)), "| posts", len(S9["posts"]))
s10_reset(); S9["version"] = "0.81"; S9["post"]["/glyph/polygon"] = dict(OKPOLY)
print("12n single contour needs 0.82 too ->", s9_try(lambda: srv.write_glyph_polygon("fresh", points=RECT)), "| posts", len(S9["posts"]))
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = {"open": True, "name": "ring", "drawn": False, "changed": True, "reason": "after drawing, the layer reads 1 shape(s), 4 node(s) and 1 contour(s); expected 1, 8 and 2"}
print("12o second contour dropped ->", s9_try(lambda: srv.write_glyph_polygon("ring", contours=RING)), "|", fview(srv.finish_change_package()))
print("12p docs              -> contours example:", "contours=[[[0,0]" in srv.draw_polygon.__doc__, "| direction advice:", "COUNTERCLOCKWISE" in srv.draw_polygon.__doc__, "| signature:", _inspect.signature(srv.draw_polygon))
# direction notes
r = read11(mo_reply())
c0 = r["contours"][0]
print("12q house, flag True   ->", c0["direction_computed"], c0["clockwise_reported"], "| follows inversion:", c0["flag_follows_known_inversion"], "| warning:", any("WARNING" in n for n in r["notes"]), "| general note:", any("opposite way round" in n for n in r["notes"]))
r = read11(mo_reply(CW_N, flag=False, margins={"lsb": 0.0, "rsb": 50.0, "advance": 150.0}))
c0 = r["contours"][0]
print("12r clockwise, flag False ->", c0["direction_computed"], c0["clockwise_reported"], "| follows inversion:", c0["flag_follows_known_inversion"], "| warning:", any("WARNING" in n for n in r["notes"]))
r = read11(mo_reply(CW_N, flag=True, margins={"lsb": 0.0, "rsb": 50.0, "advance": 150.0}))
c0 = r["contours"][0]
print("12s clockwise, flag True (not inverted) ->", c0["flag_follows_known_inversion"], "| warning:", [n for n in r["notes"] if "WARNING" in n])
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 13: server 0.23 - draw_path, rule B reports ----
print("\n==== 13. server 0.23: draw_path, coordinates_rounded, listener 0.81 (faked listener replies) ====")
def P(x, y, c1=None, c2=None, smooth=None):
    d = {"x": x, "y": y}
    if c1 is not None: d["c1"] = {"x": c1[0], "y": c1[1]}; d["c2"] = {"x": c2[0], "y": c2[1]}
    if smooth is not None: d["smooth"] = smooth
    return d
PATH_RECT = [[P(0, 0), P(400, 0), P(400, 400, (500, 100), (500, 300)), P(0, 400)]]
OKPATH = {"open": True, "name": "fresh", "drawn": True, "route": "modern", "layer_created": "test_font", "points": 4, "segments_curved": 1, "contours": 1,
          "contour_sizes": [6], "coordinates_rounded": [], "nodes_match": True, "state_before": {"active_layer": "present", "shapes": 0, "nodes": 0},
          "state_after": {"active_layer": "present", "shapes": 1, "nodes": 6}, "checks": {"shapes_ok": True, "nodes_ok": True, "nodes_match": True}, "changed": True,
          "margins": {"lsb": 0.0, "rsb": -400.0, "advance": 0.0}, "ink_width": 400.0, "display_refreshed": True, "display_note": "NOTE"}
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/path"] = dict(OKPATH)
r = srv.write_glyph_path("fresh", PATH_RECT)
print("13a curved rectangle   ->", {k: r[k] for k in ("drawn", "verified", "nodes_match", "points", "curved_segments", "contours", "contour_sizes", "shapes", "nodes", "ink_width", "coordinates_rounded")}, "| rounding_note absent:", "rounding_note" not in r, "| font_modified", r.get("font_modified"))
print("13b sent               ->", S9["posts"])
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/path"] = dict(OKPATH, coordinates_rounded=[{"contour": 0, "point": 1, "field": "x", "requested": 10.5, "used": 11.0}, {"contour": 0, "point": 2, "field": "c1.y", "requested": 3.2, "used": 3.0}])
r = srv.write_glyph_path("fresh", [[P(0, 0), P(10.5, 0), P(5, 20, (10.5, 3.2), (9, 12))]])
print("13c rounding reported  ->", r["coordinates_rounded"], "|", r["rounding_note"][:40], "| sent", S9["posts"][0][1]["contours"][0][1])
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = dict(OKPOLY, coordinates_rounded=[{"contour": 0, "point": 1, "field": "x", "requested": 10.5, "used": 11.0}])
r = srv.write_glyph_polygon("fresh", points=RECT); print("13d polygon rounding   ->", r["coordinates_rounded"], "| note", "rounding_note" in r)
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = dict(OKPOLY)
r = srv.write_glyph_polygon("fresh", points=RECT); print("13e polygon, whole numbers ->", r["coordinates_rounded"], "| note absent", "rounding_note" not in r)
s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/polygon"] = dict(OKPOLY); 
r = srv.write_glyph_polygon("fresh", points=RECT); print("13f older listener's polygon reply ->", r["coordinates_rounded"])
s10_reset(); S9["version"] = "0.81"; S9["post"]["/glyph/path"] = dict(OKPATH)
print("13g listener 0.81 (no layer guard) ->", s9_try(lambda: srv.write_glyph_path("fresh", PATH_RECT)), "| posts", len(S9["posts"]))
for label, name, cont in (("13h empty name", " ", PATH_RECT), ("13i contours None", "fresh", None), ("13j empty list", "fresh", []), ("13k 21 contours", "fresh", PATH_RECT * 21),
                          ("13l contour a number", "fresh", [5]), ("13m 2 points", "fresh", [[P(0, 0), P(1, 1)]]), ("13n point is a list", "fresh", [[[0, 0], [1, 0], [1, 1]]]),
                          ("13o unknown key", "fresh", [[dict(P(0, 0), z=1), P(1, 0), P(1, 1)]]), ("13p missing y", "fresh", [[{"x": 0}, P(1, 0), P(1, 1)]]),
                          ("13q x text", "fresh", [[P("0", 0), P(1, 0), P(1, 1)]]), ("13r x bool", "fresh", [[P(True, 0), P(1, 0), P(1, 1)]]),
                          ("13s x NaN", "fresh", [[P(float("nan"), 0), P(1, 0), P(1, 1)]]), ("13t x out of range", "fresh", [[P(20001, 0), P(1, 0), P(1, 1)]]),
                          ("13u c1 without c2", "fresh", [[dict(P(0, 0), c1={"x": 1, "y": 1}), P(1, 0), P(1, 1)]]),
                          ("13v c1 is a list", "fresh", [[dict(P(0, 0), c1=[1, 1], c2=[2, 2]), P(1, 0), P(1, 1)]]),
                          ("13w c1 stray key", "fresh", [[dict(P(0, 0), c1={"x": 1, "y": 1, "k": 1}, c2={"x": 1, "y": 1}), P(1, 0), P(1, 1)]]),
                          ("13x smooth text", "fresh", [[dict(P(0, 0), smooth="yes"), P(1, 0), P(1, 1)]]),
                          ("13y same position", "fresh", [[P(0, 0), P(0, 0), P(1, 1)]]),
                          ("13z too many nodes", "fresh", [[P(i, (i * 7) % 90) for i in range(500)]] * 4 + [[P(i, (i * 7) % 90) for i in range(10)]])):
    s10_reset(); S9["version"] = "0.82"; n = len(S9["posts"])
    print(label, "->", s9_try(lambda: srv.write_glyph_path(name, cont)), "| posts", len(S9["posts"]) - n)
for label, reply in (("13za refused, nothing changed", {"open": True, "name": "fresh", "drawn": False, "reason": "the request cannot be drawn, nothing was changed: contour 0: the smooth node at (400.0, 0.0) is not smooth"}),
                     ("13zb drawn but layer differs", {"open": True, "name": "fresh", "drawn": False, "changed": True, "reason": "the layer does not match the request: layer contour 0 node 0: position (5.0, 0.0) instead of (0.0, 0.0)"}),
                     ("13zc layer created, then refused", {"open": True, "name": "fresh", "drawn": False, "layer_created": "test_font", "reason": "x"}),
                     ("13zd no font", {"open": False}), ("13ze unknown glyph", {"open": True, "found": False})):
    s10_reset(); S9["version"] = "0.82"; S9["post"]["/glyph/path"] = reply
    print(label, "->", s9_try(lambda: srv.write_glyph_path("fresh", PATH_RECT)), "|", fview(srv.finish_change_package()))
print("13zf docs              -> tool listed:", callable(getattr(srv, "draw_path", None)), "| rule B:", "RULE B" in srv.draw_path.__doc__, "| closing segment:", "closing segment" in srv.draw_path.__doc__, "| NEVER saves:", "NEVER saves" in srv.draw_path.__doc__, "| signature:", _inspect.signature(srv.draw_path))
print("13zg polygon doc       -> rounding mentioned:", "coordinates_rounded" in srv.draw_polygon.__doc__, "| points to draw_path:", "draw_path" in srv.draw_polygon.__doc__)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 14: server 0.24 - cubic curves read back (live data of crv81a-e) ----
print("\n==== 14. server 0.24: get_glyph_outline reads cubic curves: Curve labels, curve_type, svg_path, exact extents (live data) ====")
def hnode(i, x, y): return node(i, x, y, on=False, curve=True)
def cn(rows):
    out = []
    for i, r in enumerate(rows):
        out.append(hnode(i, r[0], r[1]) if len(r) == 3 else node(i, r[0], r[1]))
    return out
def rd(nodes, margins, **kw):
    return read11(mo_reply(cn(nodes), margins=margins, **kw))
def show14(tag, r):
    c = r["contours"][0]
    print(tag, "->", r["verification"]["status"], "|", r["verification"].get("reason", "")[:70], "| bbox", r["ink_bbox"], "exact", r["ink_bbox_exact"], "| type", c["curve_type"], "| kinds", [n["kind"] for n in c["node_list"]], "| svg", c.get("svg_path"))
show14("14a crv81a bulge right (ink 475)  ", rd([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)], {"lsb": 0.0, "rsb": -475.0, "advance": 0.0}))
show14("14b crv81c, closing handles at the END (left -75)", rd([(0, 0), (400, 0), (400, 400), (0, 400), (-100, 300, 1), (-100, 100, 1)], {"lsb": -75.0, "rsb": -400.0, "advance": 0.0}))
show14("14c crv81b circle, 4 smooth nodes ", rd([(400, 200), (400, 310, 1), (310, 400, 1), (200, 400), (90, 400, 1), (0, 310, 1), (0, 200), (0, 90, 1), (90, 0, 1), (200, 0), (310, 0, 1), (400, 90, 1)], {"lsb": 0.0, "rsb": -400.0, "advance": 0.0}))
show14("14d crv81e rounded (left -2, right 10.75)", rd([(1, 0), (10, 0), (11, 3, 1), (11, 8, 1), (10, 11), (-2, 10)], {"lsb": -2.0, "rsb": -10.75, "advance": 0.0}))
show14("14e margins disagree (box says 475)", rd([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)], {"lsb": 0.0, "rsb": -400.0, "advance": 0.0}))
show14("14f only 0.04 off is still verified", rd([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)], {"lsb": 0.0, "rsb": -475.04, "advance": 0.0}))
show14("14g 0.1 off is not", rd([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)], {"lsb": 0.0, "rsb": -475.1, "advance": 0.0}))
show14("14h three handles in a row     ", rd([(0, 0), (400, 0), (500, 100, 1), (500, 200, 1), (500, 300, 1), (400, 400)], {"lsb": 0.0, "rsb": -475.0, "advance": 0.0}))
show14("14i one handle only           ", rd([(0, 0), (400, 0), (500, 100, 1), (400, 400)], {"lsb": 0.0, "rsb": -475.0, "advance": 0.0}))
show14("14j quadratic off-curve point ", rd([(0, 0), (400, 0), (500, 200), (400, 400)], {"lsb": 0.0, "rsb": -400.0, "advance": 0.0}) if False else read11(mo_reply([node(0, 0, 0), node(1, 400, 0), node(2, 500, 200, on=False, curve=False), node(3, 400, 400)], margins={"lsb": 0.0, "rsb": -400.0, "advance": 0.0})))
show14("14k margins unreadable        ", read11(mo_reply(cn([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)]), margins=False)))
r = rd([(0, 0), (400, 0), (500, 100, 1), (500, 300, 1), (400, 400), (0, 400)], {"lsb": 0.0, "rsb": -475.0, "advance": 0.0}); r0 = r["contours"][0]
print("14l fields              ->", {k: r[k] for k in ("left", "right", "advance_width", "ink_width", "node_count")}, "| curve flag kept", [n["curve"] for n in r0["node_list"]])
# a counter that is curved, two contours (crv81d): outer straight, inner with a curve that stays inside
two = {"index": 0, "closed": True, "clockwise": True, "nodesCount": 4, "nodes": cn([(0, 0), (300, 0), (300, 300), (0, 300)])}
two2 = {"index": 1, "closed": True, "clockwise": False, "nodesCount": 6, "nodes": cn([(100, 100), (60, 130, 1), (60, 170, 1), (100, 200), (200, 200), (200, 100)])}
reply = mo_reply(cn([(0, 0)]), margins={"lsb": 0.0, "rsb": -300.0, "advance": 0.0}); reply["modern_outline"]["contours"] = [two, two2]; reply["modern_outline"]["node_count"] = 10; reply["modern_outline"]["expected_node_count"] = 10
r = read11(reply)
print("14m two contours        ->", r["verification"]["status"], "| types", [c["curve_type"] for c in r["contours"]], "| svg", [c.get("svg_path") for c in r["contours"]], "| bbox", r["ink_bbox"], "exact", r["ink_bbox_exact"])
two2o = dict(two2, closed=False)
reply["modern_outline"]["contours"] = [two2o]; reply["modern_outline"]["node_count"] = 6; reply["modern_outline"]["expected_node_count"] = 6
r = read11(reply); print("14n open contour        ->", r["verification"]["status"], "|", r["verification"].get("reason", "")[:90])
# the extents helper itself
import math as _m
def ext(*pts): return sorted((round(x, 4), round(y, 4)) for x, y in srv._cubic_extremes(*pts))
print("14o extremes            ->", ext((400, 0), (500, 100), (500, 300), (400, 400)), "|", ext((0, 0), (0, 0), (100, 100), (100, 100)), "|", ext((0, 0), (100, 0), (200, 0), (300, 0)), "| s-curve", ext((0, 0), (100, 200), (200, -200), (300, 0)))
print("14p circle quadrant     ->", ext((400, 200), (400, 310), (310, 400), (200, 400)))
print("14q docs                -> Curve explained:", "Curve = cubic control point" in srv.get_glyph_outline.__doc__, "| unverified-for-curves wording gone:", "stays 'unverified' (the curve extents" not in srv.get_glyph_outline.__doc__)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ---------------------------------------------------------------- part 15: server 0.25 - stale legacy view (live finding, v0.24) ----
print("\n==== 15. server 0.25: stale legacy view - modern margins vs the legacy reader's margins (faked listener replies) ====")
import os as _os15
def legacy_reply(x0, margins, **kw):
    # a rectangle 400 x 300 whose left edge is at x0, as the LEGACY reader reports it (kinds as in a real reply)
    pts = [(x0, 0, "Move"), (x0 + 400, 0, "On"), (x0 + 400, 300, "On"), (x0, 300, "On")]
    nodes = [{"index": i, "x": float(x), "y": float(y), "kind": k, "smooth": False} for i, (x, y, k) in enumerate(pts)]
    return outline_reply(node_count=4, contour_count_reported=1, contour_count_grouped=1, contours=[{"node_count": 4, "nodes": nodes}],
                         fontlab_bbox={"left": float(x0), "right": float(x0 + 400), "bottom": 0.0, "top": 300.0}, margins=margins,
                         modern_check={"available": True, "modern_layer": True, "modern_nodes": 4, "modern_shapes": 1, "agree": True}, **kw)
def sb_reply(lsb, rsb, adv, **kw):
    r = {"open": True, "found": True, "readable": True, "modern_layer": True, "lsb": float(lsb), "rsb": float(rsb), "advance": float(adv),
         "ink_width": float(adv - lsb - rsb)}
    r.update(kw); return r
def read15(outline, sb):
    s10_reset(); S9["get"]["/glyph/outline"] = outline
    if sb is None: S9["get"].pop("/glyph/sidebearings", None)
    else: S9["get"]["/glyph/sidebearings"] = sb
    r = srv.read_glyph_outline("grd83a")
    return r, sum(1 for g in S9["gets"] if g.startswith("/glyph/sidebearings"))
def brief15(r, n):
    v = r["verification"]; c = v.get("modern_margins_check")
    return f"{v['status']} | check {c if c is None else c.get('status')} | stale_legacy_view {r.get('stale_legacy_view')} | extra reads {n}"
# the live finding: nodes and margins still the OLD ones (left 0 / right 100), the modern layer already moved by 40 (40 / 60)
r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500))
print("15a stale legacy view     ->", brief15(r, n))
print("15b  detail               ->", r["verification"]["modern_margins_check"], "|", r["verification"]["reason"][:70], "|", r["notes"][-1][:60], "...")
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), sb_reply(40, 60, 500))
print("15c legacy and modern agree ->", brief15(r, n), "| notes", r["notes"])
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), sb_reply(40.04, 59.96, 500))
print("15d difference 0.04       ->", brief15(r, n))
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), sb_reply(40.06, 60, 500.06))
print("15e difference 0.06       ->", brief15(r, n), "| differs", r["verification"]["modern_margins_check"].get("differs"))
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), sb_reply(40, 60, 700))
print("15f advance only differs  ->", brief15(r, n), "| differs", r["verification"]["modern_margins_check"].get("differs"))
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), None)
print("15g extra read fails      ->", brief15(r, n), "|", r["verification"]["modern_margins_check"]["reason"][:60], "| note:", r["notes"][-1][:60])
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), {"open": True, "found": True, "readable": False, "reason": "no editable layer"})
print("15h modern not readable   ->", brief15(r, n), "|", r["verification"]["modern_margins_check"]["reason"])
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), dict(sb_reply(40, 60, 500), lsb="x"))
print("15i modern not a number   ->", brief15(r, n))
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0}), sb_reply(40, 60, 500))
print("15j legacy margins missing ->", brief15(r, n))
oc = legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}); oc["modern_check"] = {"available": True, "modern_layer": False}
r, n = read15(oc, sb_reply(0, 0, 0))
print("15k no modern layer       ->", brief15(r, n))
oc = legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}); oc.pop("modern_check")
r, n = read15(oc, sb_reply(0, 0, 0))
print("15l old listener (no modern_check) ->", brief15(r, n))
_os15.environ["GLYPHBRIDGE_MODERN"] = "0"
try:
    r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500))
finally:
    del _os15.environ["GLYPHBRIDGE_MODERN"]
print("15m modern API switched off ->", brief15(r, n))
oc = legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}); oc["modern_check"].update(agree=False, modern_nodes=6)
oc["modern_outline"] = {"available": False, "error": "x"}
r, n = read15(oc, sb_reply(40, 60, 500))
print("15n node counts disagree (old path) ->", brief15(r, n), "| modern_check kept:", "modern_check" in r["verification"])
_real_analyze15 = srv.analyze_outline
srv.analyze_outline = lambda data: {"verification": {"status": "unverified", "reason": "x"}, "notes": []}
r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500))
srv.analyze_outline = _real_analyze15
print("15o already unverified    ->", brief15(r, n))
srv.analyze_outline = lambda data: {"verification": {"status": "calibrated"}, "notes": []}
r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500))
srv.analyze_outline = _real_analyze15
print("15p calibrated is checked too ->", brief15(r, n))
_doc15 = srv.get_glyph_outline.__doc__
print("15q docs                  -> stale view explained:", "'stale_legacy_view' is true" in _doc15, "| close-and-reopen advice:", "close the glyph's editor tab" in _doc15 and "reopen the glyph from the grid" in _doc15, "| old grid-tab advice gone:", "ask the person to switch to the grid tab" not in _doc15)
r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500))
_note15 = r["notes"][-1]
print("15s note wording          -> close and reopen:", "CLOSED (X)" in _note15 and "reopened from the grid" in _note15, "| old advice gone:", "switches to the grid tab and back" not in _note15, "| says plain grid-tab switch did not do it:", "plain switch to the grid tab and back did not do it" in _note15)
print("15r no write, no save     -> posts sent:", S9["posts"])
srv._call_listener, srv._call_listener_post = wire_get, wire_post


# ================= server v0.27: the listener's v0.87 guard fields are forwarded (faked listener replies) =================
print("\n==== 16. server 0.27: guard fields of listener 0.87 are forwarded, type-checked, with short instructions (faked listener replies) ====")
_save16 = (srv._call_listener, srv._call_listener_post)
R16 = {}
srv._call_listener = lambda path: {"version": "0.87"}
srv._call_listener_post = lambda path, payload, timeout=srv.TIMEOUT_SECONDS: R16[path]
GK16 = ("synced_with_fontlab", "durability_note", "display_refresh", "display_refresh_note", "display_refresh_skipped_to_protect", "display_refresh_unreadable_glyphs", "layers_missing_since_drawn")
GUARD16 = dict(synced_with_fontlab=False, durability_note="N", display_refresh="skipped", display_refresh_skipped_to_protect=["a"],
               display_refresh_unreadable_glyphs=["u"], display_refresh_note="n", layers_missing_since_drawn=["z"], secret_extra=["must not pass"])
SB16 = {"lsb": 10.0, "rsb": 20.0, "advance": 530.0}
def replies16(**g):
    R16["/glyph/create"] = dict({"open": True, "created": True, "before_count": 6, "after_count": 7, "unicode": None, "unicode_status": "none"}, **g)
    R16["/glyph/width"] = dict({"open": True, "set": True, "before": 500, "after": 640, "route": "modern"}, **g)
    R16["/glyph/sidebearings"] = dict({"open": True, "set": True, "changed": True, "before": SB16, "after": dict(SB16, lsb=30.0, advance=550.0), "ink_width": 500.0}, **g)
    R16["/glyph/polygon"] = dict({"open": True, "drawn": True, "points": 4, "state_after": {"shapes": 1, "nodes": 4}, "contour_sizes": [4]}, **g)
    R16["/glyph/path"] = dict({"open": True, "drawn": True, "nodes_match": True, "points": 4, "state_after": {"shapes": 1, "nodes": 4}, "segments_curved": 1}, **g)
    R16["/glyph/unicode"] = dict({"open": True, "set": True, "before": None, "after": 65}, **g)
    R16["/glyph/delete"] = dict({"open": True, "deleted": True, "before_count": 7, "after_count": 6}, **g)
TOOLS16 = (("create_glyph", lambda: srv.create_new_glyph("g1")), ("set_glyph_width", lambda: srv.write_glyph_width("g1", 640)),
           ("set_glyph_sidebearings", lambda: srv.write_glyph_sidebearings("g1", 30, 20)),
           ("draw_polygon", lambda: srv.write_glyph_polygon("g1", points=[[0, 0], [400, 0], [400, 300], [0, 300]])),
           ("draw_path", lambda: srv.write_glyph_path("g1", [[{"x": 0, "y": 0}, {"x": 400, "y": 0}, {"x": 400, "y": 300}]])),
           ("set_glyph_unicode", lambda: srv.write_glyph_unicode("g1", 65)), ("delete_glyph", lambda: srv.delete_existing_glyph("g1")))
def row16(label, r):
    ins = r.get("agent_instruction", "")
    print(label, ":", sorted(k for k in r if k in GK16 or k == "secret_extra"), "| unsynced sentence", "synced_with_fontlab is false" in ins,
          "| skipped sentence", "display refresh was skipped" in ins, "| missing sentence", "layers_missing_since_drawn lists" in ins, "| font_modified", r.get("font_modified"))
replies16(**GUARD16)
for _label, _fn in TOOLS16:
    row16("16a " + _label.ljust(22), _fn())
replies16()
for _label, _fn in TOOLS16:
    row16("16b older listener, " + _label.ljust(22), _fn())
replies16(synced_with_fontlab="no", durability_note=5, display_refresh=["skipped"], display_refresh_skipped_to_protect=[1, 2],
          display_refresh_unreadable_glyphs=[], display_refresh_note="", layers_missing_since_drawn="z")
for _label, _fn in TOOLS16[:3]:
    row16("16c wrong types ignored, " + _label.ljust(22), _fn())
replies16(synced_with_fontlab=True)
row16("16d synced true: no unsynced sentence ", srv.write_glyph_width("g1", 640))
replies16(layers_missing_since_drawn=["z"])
row16("16e only missing layers               ", srv.create_new_glyph("g1"))
replies16(display_refresh="skipped"); r = srv.create_new_glyph("g1")
print("16f instruction keeps the create text and the save reminder:", r["agent_instruction"].startswith("FontLab"), "|", "finish_changes" in r["agent_instruction"], "| tail ok", "Mention it to the person." in r["agent_instruction"])
R16["/glyph/create"] = {"open": True, "created": False, "reason": "x", "display_refresh": "skipped"}
try: srv.create_new_glyph("g1"); print("16g failed create: no error?!")
except ToolError as e: print("16g failed create still raises ToolError:", str(e)[:50])
_r16 = {"x": 1}; srv._add_guard_fields(_r16, None); srv._add_guard_fields(_r16, "text"); print("16i a broken reply never raises, adds nothing:", _r16)
print("16h version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = _save16

# ================= server v0.28: a stale legacy view is answered from the modern layer (faked listener replies) =================
print("\n==== 17. server 0.28: stale legacy view answered from the modern layer when the listener (0.88) sends margins_agree false (faked listener replies) ====")
def modern_rect(x0, margins=None, **kw):
    pts = [(x0, 0), (x0 + 400, 0), (x0 + 400, 300), (x0, 300)]
    nodes = [{"index": i, "x": float(x), "y": float(y), "isOn": True, "isOff": False, "isCurve": False, "smooth": False} for i, (x, y) in enumerate(pts)]
    mo = {"available": True, "contours": [{"index": 0, "closed": True, "clockwise": True, "nodesCount": 4, "nodes": nodes}], "node_count": 4, "expected_node_count": 4,
          "margins": margins if margins is not None else {"lsb": float(x0), "rsb": float(500 - x0 - 400), "advance": 500.0}}
    mo.update(kw); return mo
def stale_reply(modern_outline="auto", **mc_extra):
    r = legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0})
    r["modern_check"].update(margins_agree=False, margins_differ=["left", "right"], legacy_margins={"left": 0.0, "right": 100.0, "advance_width": 500.0},
                             modern_margins={"left": 40.0, "right": 60.0, "advance_width": 500.0})
    r["modern_check"].update(mc_extra)
    if modern_outline == "auto": r["modern_outline"] = modern_rect(40)
    elif modern_outline is not None: r["modern_outline"] = modern_outline
    return r
def brief17(r, n):
    v = r["verification"]
    return f"source {r.get('source')} | {v['status']} | legacy_view_was_stale {r.get('legacy_view_was_stale')} | stale_legacy_view {r.get('stale_legacy_view')} | extra sidebearing reads {n}"
r, n = read15(stale_reply(), sb_reply(40, 60, 500))
print("17a stale margins + modern_outline ->", brief17(r, n))
_xs17 = [nd["x"] for nd in r["contours"][0]["node_list"]]
print("17b  detail               ->", "x range", min(_xs17), max(_xs17), "| margins", r["left"], r["right"], r["advance_width"], "| ink_bbox", r["ink_bbox"], "| node_count", r["node_count"])
print("17c  verification         ->", r["verification"]["legacy_margins_vs_modern"], "|", r["verification"].get("bounding_box_vs_margins"))
print("17d  note                 ->", [x for x in r["notes"] if x.startswith("STALE")][0])
print("17e  old note not used    ->", not any(x.startswith("The legacy reader sees") for x in r["notes"]))
r, n = read15(legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}), sb_reply(40, 60, 500))
print("17f margins_agree true: legacy route kept ->", brief15(r, n), "| source", r.get("source"))
oc = legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}); oc["modern_check"].update(margins_agree=True)
r, n = read15(oc, sb_reply(40, 60, 500)); print("17g margins_agree true (listener says so) ->", brief15(r, n), "| source", r.get("source"))
r, n = read15(stale_reply(modern_outline={"available": False, "error": "x"}), sb_reply(40, 60, 500))
print("17h stale, modern_outline unavailable: v0.25 check takes over ->", brief15(r, n), "| source", r.get("source"), "| legacy_view_was_stale", r.get("legacy_view_was_stale"))
r, n = read15(stale_reply(modern_outline=None), sb_reply(40, 60, 500))
print("17i stale, no modern_outline at all    ->", brief15(r, n), "| source", r.get("source"))
oc = legacy_reply(40, {"left": 40.0, "right": 60.0, "width": 500.0}); oc["modern_check"].update(margins_agree=None, margins_note="the modern margins were not read: x")
r, n = read15(oc, sb_reply(40, 60, 500)); print("17j listener could not compare, margins agree ->", brief15(r, n), "| source", r.get("source"))
oc = legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}); oc["modern_check"].update(margins_agree=None, margins_note="x")
r, n = read15(oc, sb_reply(40, 60, 500)); print("17k listener could not compare, stale -> server check ->", brief15(r, n), "| source", r.get("source"))
oc = legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}); oc["modern_check"].update(agree=False, modern_nodes=4); oc["modern_outline"] = modern_rect(0)
r, n = read15(oc, sb_reply(0, 100, 500)); print("17l node counts disagree: old note, no flag ->", brief17(r, n), "|", r["notes"][-1][:46])
oc = stale_reply(); oc["modern_check"].update(agree=False)
r, n = read15(oc, sb_reply(40, 60, 500)); print("17m both flags false: old note, no flag   ->", brief17(r, n), "|", r["notes"][-1][:46])
r, n = read15(stale_reply(modern_outline=modern_rect(40, margins={"lsb": 0.0, "rsb": 100.0, "advance": 500.0})), sb_reply(40, 60, 500))
print("17n modern box disagrees with modern margins ->", brief17(r, n), "|", r["verification"].get("reason", "")[:70])
r, n = read15(stale_reply(legacy_margins="x", modern_margins=None), sb_reply(40, 60, 500)); print("17o margins of mc not dicts: no raise ->", brief17(r, n), "|", [x for x in r["notes"] if x.startswith("STALE")][0][:70], "| differs", r["verification"]["legacy_margins_vs_modern"]["differs"])
r, n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(40, 60, 500)); print("17p old listener (no margins_agree): v0.25 behaviour ->", brief15(r, n), "| source", r.get("source"))
_doc17 = srv.get_glyph_outline.__doc__
print("17q docs                  -> modern answer explained:", "Since listener 0.88" in _doc17 and "legacy_view_was_stale" in _doc17, "| v0.25 text kept:", "'stale_legacy_view' is true" in _doc17 and "close the glyph's editor tab" in _doc17)
print("17r no write, no save     -> posts sent:", S9["posts"])
print("17s version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post

# ================= server v0.29: the listener's v0.89 fontlab_sync block is forwarded (faked listener replies) =================
print("\n==== 18. server 0.29: fontlab_sync of listener 0.89 is forwarded, type-checked; the editor-tab advice only when the sync attempt failed (faked listener replies) ====")
_save18 = (srv._call_listener, srv._call_listener_post)
srv._call_listener = lambda path: {"version": "0.89"}
srv._call_listener_post = lambda path, payload, timeout=srv.TIMEOUT_SECONDS: R16[path]
W18 = TOOLS16[1:5]          # width, sidebearings, draw_polygon, draw_path: the four tools the listener syncs
def row18(label, r):
    ins = r.get("agent_instruction", "")
    print(label, ": synced_with_fontlab", r.get("synced_with_fontlab"), "| fontlab_sync", r.get("fontlab_sync"), "| secret", "secret_extra" in r,
          "| failed-sync sentence", "asked FontLab to sync this glyph" in ins, "| unsynced sentence", "synced_with_fontlab is false" in ins, "| editor advice", "editor in FontLab" in ins)
OK18 = dict(synced_with_fontlab=True, durability_note="synced", fontlab_sync=dict(attempted=True, synced=True, verdict="synced", secret_extra=1), secret_extra=["x"])
replies16(**OK18)
for _label, _fn in W18: row18("18a synced " + _label.ljust(22), _fn())
BAD18 = dict(synced_with_fontlab=False, durability_note="N", fontlab_sync=dict(attempted=True, synced=False, verdict="at_risk", call_error="RuntimeError: Update refused"))
replies16(**BAD18)
for _label, _fn in W18: row18("18b not synced " + _label.ljust(22), _fn())
r = srv.write_glyph_width("g1", 640); _i = r["agent_instruction"]
print("18c order of the sentences       :", _i.index("asked FontLab to sync this glyph") < _i.index("synced_with_fontlab is false"), "| editor advice still last-resort text:", "sync it." in _i)
replies16(synced_with_fontlab=False, durability_note="N", fontlab_sync=dict(attempted=False, reason="the fontlab module has no Update function"))
row18("18d not attempted                  ", srv.write_glyph_width("g1", 640))
replies16(synced_with_fontlab=False, durability_note="N", fontlab_sync=dict(attempted="yes", synced=1, verdict=5, call_error="", reason=["x"]))
row18("18e wrong types ignored            ", srv.write_glyph_width("g1", 640))
replies16(synced_with_fontlab=False, fontlab_sync="synced")
row18("18f fontlab_sync not a dict        ", srv.write_glyph_width("g1", 640))
replies16(synced_with_fontlab=False, fontlab_sync=["a"])
row18("18g fontlab_sync a list            ", srv.write_glyph_width("g1", 640))
replies16(synced_with_fontlab=False)
row18("18h older listener                 ", srv.write_glyph_width("g1", 640))
replies16(synced_with_fontlab=True, fontlab_sync=dict(attempted=True, synced=True, verdict="synced"))
r = srv.write_glyph_polygon("g1", points=[[0, 0], [400, 0], [400, 300], [0, 300]]); print("18i synced: no agent_instruction about sync:", "asked FontLab" not in r.get("agent_instruction", ""), "| font_modified", r.get("font_modified"))
_r18 = {"x": 1}; srv._add_guard_fields(_r18, None); srv._add_guard_fields(_r18, {"fontlab_sync": {"attempted": object()}}); print("18j a broken reply never raises  :", _r18)
print("18k version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = _save18




# ================= server v0.30: get_kerning (faked listener replies) =================
print("\n==== 19. server 0.30 / 0.31: get_kerning reads selected pairs through POST /kerning/pairs; no upper limit, approval above 250 (faked listener replies) ====")
_save19 = (srv._call_listener, srv._call_listener_post)
K19 = {"version": "0.95", "reply": None, "paths": [], "posts": []}
def _k19_get(path):
    K19["paths"].append(path)
    if path == "/version":
        v = K19["version"]
        if isinstance(v, Exception): raise v
        return {"version": v}
    raise AssertionError("unexpected GET " + path)
def _k19_post(path, payload, timeout=0):
    K19["posts"].append((path, payload, timeout))
    r = K19["reply"]
    if isinstance(r, Exception): raise r
    return r
srv._call_listener, srv._call_listener_post = _k19_get, _k19_post
def k19(reply=None, version="0.104", **call):
    K19["reply"] = reply; K19["version"] = version; K19["paths"].clear(); K19["posts"] = []
    srv._reset_change_tracking()
    try:
        return srv.read_kerning(**call)
    except srv.ToolError as e:
        return "ToolError: " + str(e)
def k19reads(): return [(p, pl) for p, pl, _t in K19["posts"]]
def k19other(): return [p for p, _pl, _t in K19["posts"] if p != "/kerning/pairs"] + [p for p in K19["paths"] if p != "/version"]
def _src19(e):
    """v0.33: listener 0.104 sends a source with every read value; give the older fakes a plausible one unless the case sets its own."""
    if not isinstance(e, dict) or "source" in e or "error" in e:
        return e
    v = e.get("value")
    zero = isinstance(v, (int, float)) and not isinstance(v, bool) and v == 0
    return dict(e, source="none" if zero else "glyph : glyph")
def okreply(results, **extra):
    return dict({"open": True, "mode": "pairs", "master": "Regular", "master_count": 1, "units_per_em": 2048.0, "count": len(results), "errors": 0, "table_size": 1370,
                 "side_effect_detected": False, "results": [_src19(e) for e in results]}, **extra)
def row19(label, r):
    if isinstance(r, str): print(label, ":", r[:230]); return
    print(label, ":", {k: v for k, v in r.items() if k not in ("results", "agent_instruction")}, "| instruction", len(r["agent_instruction"]) > 100)
    for e in r["results"]: print("       ", e)

R1 = okreply([{"left": "A", "right": "V", "value": -152.0, "kerned": True}, {"left": "T", "right": "o", "value": -227.0, "kerned": True},
              {"left": "A", "right": "B", "value": 0, "kerned": False}, {"left": "o", "right": "o", "value": -12.5, "kerned": True}])
r = k19(R1, pairs=[["A", "V"], ["T", "o"], ["A", "B"], ["o", "o"]]); row19("19a pairs, tidy numbers         ", r)
print("19b request sent                 :", k19reads(), "| timeout", K19["posts"][0][2], "| other requests", k19other(), "| changes", dict(srv._CHANGES))
print("19c instruction                  :", r["agent_instruction"])
k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}]), pairs=[[" A ", "V "]]); print("19d names are stripped           :", k19reads())
k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}]), pairs=(("A", "V"),)); print("19e tuple of tuples accepted     :", k19reads())
TXT = okreply([{"chars": "AV", "left": "A", "right": "V", "value": -152.0, "kerned": True}, {"chars": "V ", "left": "V", "right": "space", "value": -37.0, "kerned": True},
               {"chars": " é", "left": "space", "right": None, "error": "character 'e' (U+00E9): no glyph has this codepoint as its primary Unicode"}], mode="text")
r = k19(TXT, text="AV é"); row19("19f text mode                    ", r); print("19g text request (JSON body)     :", k19reads())
r = k19(TXT, text="AV é"); print("19h text mode: errors counted    :", r["errors"], "| mode", r["mode"], "| error entry has no value:", "value" not in r["results"][2], "| chars kept:", [e.get("chars") for e in r["results"]])

print("--- input validation: nothing is sent, not even the version check")
BAD19 = [("19i neither", {}), ("19j both", dict(pairs=[["A", "V"]], text="AV")), ("19k empty pairs list", dict(pairs=[])), ("19l empty text", dict(text="")),
         ("19n pairs not a list", dict(pairs="A:V")), ("19o pair is a string", dict(pairs=["AV"])),
         ("19p pair has 3 names", dict(pairs=[["A", "V", "T"]])), ("19q pair has 1 name", dict(pairs=[["A"]])), ("19r name empty", dict(pairs=[["A", ""]])),
         ("19s name blank", dict(pairs=[["A", "   "]])), ("19t name with colon", dict(pairs=[["A:V", "B"]])), ("19u name with comma", dict(pairs=[["A,V", "B"]])),
         ("19v name 64 long", dict(pairs=[["A", "x" * 64]])), ("19w name not a string", dict(pairs=[["A", 5]])), ("19x name with space inside", dict(pairs=[["A", "a b"]])),
         ("19y name non-ASCII", dict(pairs=[["A", "é"]])), ("19z text 1 char", dict(text="A")), 
         ("19ab text not a string", dict(text=12)), ("19ac text newline", dict(text="A\nV")), ("19ad text DEL", dict(text="A\x7fV")), ("19ae text U+0080", dict(text="A\x80V")),
         ("19af text tab", dict(text="A\tV"))]
for label, kw in BAD19:
    r = k19(R1, **kw); print(label.ljust(30), ":", str(r)[:120], "| sent", len(K19["paths"]))
r = k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}] * 40), pairs=[["A", "V"]] * 40); print("19ag 40 pairs ok         :", isinstance(r, dict), r["count"], "| pairs sent", len(k19reads()[0][1]["pairs"]))
r = k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}] * 40, mode="text"), text="A" * 41); print("19ah 41 chars ok         :", isinstance(r, dict), r["count"])
r = k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}] * 1, mode="text"), text="AV"); print("19ai exactly 2 chars ok          :", isinstance(r, dict), r["count"])
r = k19(okreply([{"left": "A", "right": "V", "value": 0, "kerned": False}] * 1, mode="text"), text="A "); print("19aj U+00A0 is not a control char:", isinstance(r, dict), k19reads())

print("--- listener version and state")
for v in ("0.93", "0.82", "0.9", "0.94", "0.95", "0.103", "0.104", "0.105", "1.0", "garbage"):
    r = k19(okreply([{"left": "A", "right": "V", "value": -1.0}]), version=v, pairs=[["A", "V"]]); print("19ak listener", v.ljust(8), ":", (r[:90] if isinstance(r, str) else "read ok"), "| kerning requests", len(k19reads()))
r = k19(okreply([{"left": "A", "right": "V", "value": -1.0}]), version=RuntimeError("down"), pairs=[["A", "V"]]); print("19al version unreadable          :", "read ok" if isinstance(r, dict) else r[:90], "| kerning requests", len(k19reads()))
r = k19({"open": False}, pairs=[["A", "V"]]); print("19am no font open                :", r[:100], "| NO_FONT text", r == "ToolError: " + srv.NO_FONT)
r = k19({"open": True, "error": "font.kerning / kerning.get not reachable: RuntimeError: boom"}, pairs=[["A", "V"]]); print("19an listener error              :", r)
r = k19({"open": True, "error": "x" * 900}, pairs=[["A", "V"]]); print("19ao long listener error cut     :", len(r))
r = k19(srv.ToolError("listener says no"), pairs=[["A", "V"]]); print("19ap transport error passes      :", r)
r = k19({}, pairs=[["A", "V"]]); print("19aq empty reply                 :", r[:90])

print("--- odd listener answers become errors, never zeros")
def one(entry, **extra):
    r = k19(okreply([entry], **extra), pairs=[["A", "V"]]); return r["results"][0] if isinstance(r, dict) else r
for label, e in (("19ar value is a string", {"left": "A", "right": "V", "value": "0"}), ("19as value is bool", {"left": "A", "right": "V", "value": True}),
                 ("19at value NaN", {"left": "A", "right": "V", "value": float("nan")}), ("19au value inf", {"left": "A", "right": "V", "value": float("inf")}),
                 ("19av value -inf", {"left": "A", "right": "V", "value": float("-inf")}), ("19aw no value, no error", {"left": "A", "right": "V"}),
                 ("19ax value None", {"left": "A", "right": "V", "value": None}), ("19ay entry not a dict", "oops"), ("19az entry None", None),
                 ("19ba other pair answered", {"left": "T", "right": "V", "value": -5.0}), ("19bb right differs", {"left": "A", "right": "W", "value": -5.0}),
                 ("19bc error empty string", {"left": "A", "right": "V", "error": ""}), ("19bd error not a string", {"left": "A", "right": "V", "error": 5}),
                 ("19be error kept, value ignored", {"left": "A", "right": "V", "value": -9.0, "error": "no glyph named 'V'"}),
                 ("19bf kerned lie ignored", {"left": "A", "right": "V", "value": 0, "kerned": True}), ("19bg kerned lie 2", {"left": "A", "right": "V", "value": -4, "kerned": False}),
                 ("19bh extra fields dropped", {"left": "A", "right": "V", "value": -4, "secret": 1}), ("19bi long error cut", {"left": "A", "right": "V", "error": "e" * 900}),
                 ("19bj int value", {"left": "A", "right": "V", "value": -152}), ("19bk float value", {"left": "A", "right": "V", "value": -152.25}),
                 ("19bl tiny value", {"left": "A", "right": "V", "value": 0.0}), ("19bm negative zero", {"left": "A", "right": "V", "value": -0.0})):
    r = one(e); print(label.ljust(31), ":", (r if not isinstance(r, dict) else {k: (v if k != "error" else v[:60] + ("..." if len(v) > 60 else "")) for k, v in r.items()}))
r = k19(okreply([{"left": "A", "right": "V", "value": 0}, {"left": "T", "right": "o", "error": "x"}, {"left": "o", "right": "o", "value": "bad"}]), pairs=[["A", "V"], ["T", "o"], ["o", "o"]])
print("19bi2 listener error cut at 600  :", len(one({"left": "A", "right": "V", "error": "e" * 900})["error"]), "| 19bi3 short error unchanged:", one({"left": "A", "right": "V", "error": "short"})["error"])
print("19bn errors counted by the server:", r["errors"], "| listener said", 0)
print("19bo count from results          :", k19(okreply([{"left": "A", "right": "V", "value": 0}] * 3, count=99, errors=0), pairs=[["A", "V"]] * 3)["count"])

print("--- reply shape")
for label, rep in (("19bp results missing", {"open": True}), ("19bq results not a list", {"open": True, "results": "x"}), ("19br too few results", okreply([{"left": "A", "right": "V", "value": 0}])),
                   ("19bs too many results", okreply([{"left": "A", "right": "V", "value": 0}] * 3))):
    print(label.ljust(31), ":", str(k19(rep, pairs=[["A", "V"], ["T", "o"]]))[:110])
for label, extra in (("19bt table_size 0", dict(table_size=0)), ("19bu table_size missing", dict(table_size=None)), ("19bv table_size bool", dict(table_size=True)), ("19bw table_size string", dict(table_size="9")),
                     ("19bx upm int-valued float", dict(units_per_em=1000.0)), ("19by upm fractional", dict(units_per_em=1000.5)), ("19bz upm bool", dict(units_per_em=True)), ("19ca upm missing", dict(units_per_em=None)),
                     ("19cb upm string", dict(units_per_em="2048")), ("19cc side effect True", dict(side_effect_detected=True)), ("19cd side effect False", dict(side_effect_detected=False)),
                     ("19ce side effect None", dict(side_effect_detected=None)), ("19cf side effect string", dict(side_effect_detected="yes"))):
    rep = okreply([{"left": "A", "right": "V", "value": -1.0}]); rep.update(extra)
    r = k19(rep, pairs=[["A", "V"]]); print(label.ljust(31), ":", {k: v for k, v in r.items() if k not in ("results", "agent_instruction")}, "| 0-note", "no kerning at all" in r["agent_instruction"], "| WARNING", "WARNING" in r["agent_instruction"])
r = k19(okreply([{"left": "A", "right": "V", "value": -1.0}], secret_extra=["x"]), pairs=[["A", "V"]]); print("19cg unknown top-level field dropped:", "secret_extra" not in r, "| keys", sorted(r))
print("19ch no change counters, only the read:", dict(srv._CHANGES), "| other requests", k19other(), "| posts", len(K19["posts"]))

print("--- v0.31: no upper limit, approval above 250")
def many(n): return [{"left": "A", "right": "V", "value": -1.0}] * n
r = k19(okreply(many(250)), pairs=[["A", "V"]] * 250); print("19cn 250 pairs: no approval needed :", isinstance(r, dict) and r["count"], "| flag in reply", isinstance(r, dict) and "large_read_confirmed" in r, "| requests", len(k19reads()))
r = k19(okreply(many(251)), pairs=[["A", "V"]] * 251); print("19co 251 pairs: refused            :", r[:420], "| requests (incl. version)", len(K19["paths"]) + len(K19["posts"]))
r = k19(okreply(many(251)), pairs=[["A", "V"]] * 251, confirmed_large_read=False); print("19cp 251 pairs, flag false: refused:", r[:60], "| requests", len(K19["paths"]) + len(K19["posts"]))
r = k19(okreply(many(251)), pairs=[["A", "V"]] * 251, confirmed_large_read=True); print("19cq 251 pairs, approved           :", isinstance(r, dict) and (r["count"], r["errors"], r.get("large_read_confirmed")), "| requests", len(k19reads()), "| payload pairs", len(k19reads()[0][1]["pairs"]))
for label, flag in (("19cr flag is the string yes", "yes"), ("19cs flag is 1", 1), ("19ct flag is a list", [True])):
    r = k19(okreply(many(251)), pairs=[["A", "V"]] * 251, confirmed_large_read=flag); print(label.ljust(34), ":", str(r)[:90], "| requests", len(K19["paths"]) + len(K19["posts"]))
r = k19(okreply(many(3)), pairs=[["A", "V"]] * 3, confirmed_large_read=True); print("19cu flag true on a small read     :", r["count"], "| flag in reply", "large_read_confirmed" in r)
r = k19(okreply(many(3)), pairs=[["A", "V"]] * 3, confirmed_large_read=False); print("19cv flag false on a small read    :", r["count"], "| flag in reply", "large_read_confirmed" in r)
r = k19(okreply(many(1000)), pairs=[["A", "V"]] * 1000, confirmed_large_read=True); print("19cw 1000 pairs approved           :", r["count"], "| timeout", K19["posts"][0][2])
r = k19(okreply(many(30000)), pairs=[["A", "V"]] * 30000, confirmed_large_read=True); print("19cx 30000 pairs approved          :", r["count"], "| timeout", K19["posts"][0][2], "| large flag", r.get("large_read_confirmed"))
r = k19(okreply(many(1)), pairs=[["A", "V"]]); print("19cy small read timeout            :", K19["posts"][0][2], "| not below TIMEOUT_SECONDS", K19["posts"][0][2] >= srv.TIMEOUT_SECONDS)
r = k19(okreply(many(250)), pairs=[["A", "V"]] * 250); print("19cz 250 pairs timeout             :", K19["posts"][0][2])
r = k19(okreply(many(250), mode="text"), text="A" * 251); print("19da text of 251 chars = 250 pairs :", isinstance(r, dict) and r["count"])
r = k19(okreply(many(251), mode="text"), text="A" * 252); print("19db text of 252 chars = 251 pairs :", r[:70], "| requests", len(K19["paths"]) + len(K19["posts"]))
r = k19(okreply(many(251), mode="text"), text="A" * 252, confirmed_large_read=True); print("19dc same text, approved           :", isinstance(r, dict) and (r["count"], r.get("large_read_confirmed")), "| payload", {k: len(v) for k, v in k19reads()[0][1].items()})
r = k19(okreply(many(2999), mode="text"), text="AV" * 1500, confirmed_large_read=True); print("19dd 3000 characters approved      :", isinstance(r, dict) and r["count"])
r = k19(okreply(many(300)), pairs=[["A", "V"]] * 299 + [["A", "bad name"]]); print("19de invalid name beats threshold  :", r[:70], "| requests", len(K19["paths"]) + len(K19["posts"]))
r = k19(okreply(many(300)), pairs=[["A", "V"]] * 300, confirmed_large_read=True, text="AV") if False else k19(okreply(many(300)), pairs=[["A", "V"]] * 300, text="AV", confirmed_large_read=True); print("19df both inputs still refused     :", r[:60])
r = k19(okreply(many(300)), version="0.94", pairs=[["A", "V"]] * 300, confirmed_large_read=True); print("19dg approved but listener 0.94    :", r[:95], "| kerning requests", len(k19reads()))

print("--- v0.33: source, class names and master from listener 0.104 (P0.8)")
for label, e in (("19x01 glyph : class with its class", {"left": "A", "right": "V", "value": -76.0, "source": "glyph : class", "right_class": "W"}),
                 ("19x02 class : glyph with its class", {"left": "A", "right": "V", "value": -80.0, "source": "class : glyph", "left_class": "Aring"}),
                 ("19x03 class : class, both classes", {"left": "A", "right": "V", "value": -76.0, "source": "class : class", "left_class": "Aring", "right_class": "W"}),
                 ("19x04 explicit 0 entry", {"left": "A", "right": "V", "value": 0.0, "source": "glyph : class", "right_class": "W"}),
                 ("19x05 none with value 0", {"left": "A", "right": "V", "value": 0, "source": "none"}),
                 ("19x06 extra class on glyph : glyph dropped", {"left": "A", "right": "V", "value": -5.0, "source": "glyph : glyph", "left_class": "X"}),
                 ("19x07 source missing", {"left": "A", "right": "V", "value": -5.0, "source": None}),
                 ("19x08 source unknown", {"left": "A", "right": "V", "value": -5.0, "source": "glyph:glyph"}),
                 ("19x09 source not a string", {"left": "A", "right": "V", "value": -5.0, "source": 3}),
                 ("19x10 none but a value", {"left": "A", "right": "V", "value": -5.0, "source": "none"}),
                 ("19x11 glyph : class without class", {"left": "A", "right": "V", "value": -5.0, "source": "glyph : class"}),
                 ("19x12 class : class, one class", {"left": "A", "right": "V", "value": -5.0, "source": "class : class", "left_class": "Aring"}),
                 ("19x13 class name with a space", {"left": "A", "right": "V", "value": -5.0, "source": "glyph : class", "right_class": "W W"}),
                 ("19x14 class name not a string", {"left": "A", "right": "V", "value": -5.0, "source": "class : glyph", "left_class": 7}),
                 ("19x15 class name 64 long", {"left": "A", "right": "V", "value": -5.0, "source": "class : glyph", "left_class": "x" * 64}),
                 ("19x16 bad value beats source", {"left": "A", "right": "V", "value": "x", "source": "glyph : glyph"})):
    r = one(e); print(label.ljust(40), ":", r)
for label, extra in (("19x17 master and count", {}), ("19x18 master missing", dict(master=None)), ("19x19 master not a string", dict(master=5)),
                     ("19x20 master empty", dict(master="")), ("19x21 master with a newline", dict(master="Reg\nular")), ("19x22 master 64 long", dict(master="M" * 64)),
                     ("19x23 two masters", dict(master="Bold", master_count=2)), ("19x24 master_count bool", dict(master_count=True)), ("19x25 master_count 0", dict(master_count=0)),
                     ("19x26 master_count string", dict(master_count="2"))):
    rep = okreply([{"left": "A", "right": "V", "value": -1.0}]); rep.update(extra)
    r = k19(rep, pairs=[["A", "V"]]); print(label.ljust(31), ":", {k: r[k] for k in ("master", "master_count")}, "| masters note", "only the current one was read" in r["agent_instruction"])
r = k19(okreply([{"left": "A", "right": "V", "value": -1.0}], table_size=0), pairs=[["A", "V"]]); print("19x27 empty master table note       :", r["agent_instruction"][-200:])
r = k19({"open": True, "error": "2 fonts are open: the kerning table can be matched to the current font only when exactly one font is open, so close the other fonts"}, pairs=[["A", "V"]]); print("19x28 two fonts: listener error     :", r)
print("19x29 tool docstring                :", "listener v0.104" in srv.get_kerning.__doc__, "| source named:", "never guess whether a value comes from a class" in srv.get_kerning.__doc__, "| current font (v0.37):", "whose window is in front" in srv.get_kerning.__doc__)
r = k19(okreply(many(2)), version="0.94", pairs=[["A", "V"]] * 2); print("19dh small read, listener 0.94     :", r[:95], "| kerning requests", len(k19reads()))
r = k19(okreply(many(1)), pairs=[["A", "V"]]); print("19di request shape                 :", k19reads()[0][0], sorted(k19reads()[0][1]), "| only POST", k19other() == [])
r = k19(okreply(many(1), mode="text"), text="AV"); print("19dj text request shape            :", k19reads()[0][0], k19reads()[0][1], "| only POST", k19other() == [])
r = k19(okreply(many(2)), pairs=[(" A ", "V "), ("T", " o")]); print("19dk payload: stripped lists       :", k19reads()[0][1])
r = k19(srv.ToolError("listener says no"), pairs=[["A", "V"]]); print("19dl transport error on POST       :", r)
print("19dm refusal text mentions       :", all(w in k19(okreply(many(251)), pairs=[["A", "V"]] * 251) for w in ("251 kerning pairs", "250-pair threshold", "nothing was read", "ask whether they approve", "confirmed_large_read=true", "Never set that flag")))

print("--- the tool")
tool_src = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
_body = tool_src[tool_src.index("_KERN_NAME_RE = "):tool_src.index("def write_glyph_sidebearings(")]
import re as _re19
print("19ci static scan                 : posts present", "_call_listener_post" in _body, "| change tracking", bool(_re19.search(r"_note_change|_mark_modified|_CHANGES|finish_changes", _body)),
      "| save", bool(_re19.search(r"\.save\(|save\(", _body)), "| GET listener calls", len(_re19.findall(r"_call_listener\(", _body)), "| requires 0.104", '_require_listener((0, 104), "get_kerning")' in _body, "| posts to the listener", len(_re19.findall(r"_call_listener_post\(", _body)))
doc = srv.get_kerning.__doc__
_need = ("exactly one of", "Never ask for the whole", "Needs listener v0.104", "never a zero", "more than 250 pairs", "confirmed_large_read=true", "Never set confirmed_large_read=true on your own", "no upper limit")
print("19cj docstring has the key phrases:", [w for w in _need if w not in doc] == [], "| missing", [w for w in _need if w not in doc])
K19["reply"] = okreply([{"left": "A", "right": "V", "value": -152.0}]); K19["version"] = "0.104"
_w = srv.get_kerning(pairs=[["A", "V"]]); _d = srv.read_kerning(pairs=[["A", "V"]]); print("19ck wrapper equals read_kerning (pairs):", _w == _d)
K19["reply"] = okreply([{"chars": "AV", "left": "A", "right": "V", "value": -152.0}], mode="text"); print("19cl wrapper equals read_kerning (text) :", srv.get_kerning(text="AV") == srv.read_kerning(text="AV"), "| both None ->", k19(None, pairs=None, text=None)[:40])
K19["reply"] = okreply([{"left": "A", "right": "V", "value": -1.0}] * 251)
try: srv.get_kerning(pairs=[["A", "V"]] * 251); _w1 = "no error"
except srv.ToolError as e: _w1 = "refused"
try: _w2 = srv.get_kerning(pairs=[["A", "V"]] * 251, confirmed_large_read=True)["count"]
except srv.ToolError as e: _w2 = "refused"
print("19cl2 wrapper passes the approval flag :", _w1, "/", _w2)
print("19cm MIN_LISTENER_VERSION unchanged / server version:", srv.MIN_LISTENER_VERSION, srv.SERVER_VERSION)
# server 0.37: which font was read, with several fonts open (listener 0.112)
K19["version"] = "0.112"
for _lbl, _extra in (("19dn two fonts, matched by path  ", dict(fonts_open=2, matched_by="path", family_name="Arial")),
                     ("19do one font                    ", dict(fonts_open=1, matched_by="only font", family_name="Arial")),
                     ("19dp two fonts, no family name   ", dict(fonts_open=2, matched_by="path", family_name=None)),
                     ("19dq odd values dropped          ", dict(fonts_open=True, matched_by="guess", family_name="x" * 64)),
                     ("19dr older listener: no fields   ", dict())):
    K19["reply"] = okreply([{"left": "A", "right": "V", "value": -152.0}], **_extra)
    _r = srv.read_kerning(pairs=[["A", "V"]])
    _ins = _r["agent_instruction"]
    print(_lbl, ":", {k: _r[k] for k in ("fonts_open", "matched_by", "family_name")}, "| names the font:", "fonts are open in FontLab" in _ins, "(Arial)" in _ins, "| say which:", "Say which font" in _ins)
print("19ds docstring: front window, no one-font rule:", "whose window is in front" in srv.get_kerning.__doc__, "Exactly one font must be open" not in srv.get_kerning.__doc__, "v0.112" in srv.get_kerning.__doc__)
srv._call_listener, srv._call_listener_post = _save19

# ==== 20. server 0.34: the connected app's name goes to the listener in the X-Glyphbridge-Client header ====
print("\n==== 20. server 0.34: client name header ====")
import io as _io20
from types import SimpleNamespace as _NS20
class _Ctx20:
    def __init__(self, session): self.session = session
def ctx20(name=None, title=None, info=True, params=True):
    if not params: return _Ctx20(_NS20(client_params=None))
    return _Ctx20(_NS20(client_params=_NS20(client_info=_NS20(name=name, title=title) if info else None)))
class _Boom20:
    @property
    def session(self): raise RuntimeError("no session")
for tag, value in (("plain", "claude-code"), ("spaces", "  Claude   Desktop "), ("control chars", "a\nb\tc\x7fd\x85e"), ("61 characters", "y" * 61),
                   ("empty", ""), ("only spaces", "   "), ("not text", 5), ("None", None)):
    print(f"20a clean {tag:14}->", repr(srv._clean_client_name(value)))
for tag, ctx in (("name only", ctx20("claude-code")), ("title wins", ctx20("claude-ai", "Claude")), ("blank title", ctx20("claude-ai", "  ")),
                 ("no client_info", ctx20(info=False)), ("no client_params", ctx20(params=False)), ("session raises", _Boom20()), ("ctx None", None)):
    srv._CLIENT["name"] = "before"; srv._note_client(ctx)
    print(f"20b note {tag:16}->", srv._CLIENT["name"])
srv._CLIENT["name"] = None; print("20c headers, no name      ->", srv._client_headers())
srv._CLIENT["name"] = "Test App é"; print("20c headers, UTF-8 name   ->", srv._client_headers())
SENT20 = []
class _Resp20(_io20.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
class _Opener20:
    def open(self, req, timeout=None):
        SENT20.append((req.get_method(), req.full_url.rsplit(str(srv.LISTENER_PORT), 1)[1], req.get_header("X-glyphbridge-client"), req.get_header("Content-type")))
        return _Resp20(json.dumps({"open": True, "x": 1}).encode())
# a fresh copy of the module: earlier sections replaced srv's listener calls with fakes
_spec20 = importlib.util.spec_from_file_location("srv20", find("glyphbridge_mcp_server.py")); srv20 = importlib.util.module_from_spec(_spec20); _spec20.loader.exec_module(srv20)
srv20._opener = _Opener20()
for name in ("claude-code", None):
    srv20._CLIENT["name"] = name; SENT20.clear()
    srv20._call_listener("/font/current"); srv20._call_listener_post("/glyph/width", {"name": "A", "width": 600})
    print(f"20d sent with name {name!r:14}->", SENT20)
_src20 = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
_tools20 = _re19.findall(r"@_tool\(\)\ndef (\w+)\((.*?)\) -> dict\[str, Any\]:\n    \"\"\".*?\"\"\"\n    (.*?)\n", _src20, _re19.S)
print("20e tools:", len(_tools20), "| every one takes ctx: Context | None = None:", all(p.rstrip().endswith("ctx: Context | None = None") for _, p, _ in _tools20),
      "| first statement _note_client(ctx):", [t for t, _, first in _tools20 if first.strip() != "_note_client(ctx)"] == [])
print("20f --check labels itself:", '_CLIENT["name"] = "glyphbridge --check"' in _src20.split("def _self_check")[1][:400])
srv._CLIENT["name"] = None

# ==== 21. server 0.35: the launcher names (file names only) go to the listener in the X-Glyphbridge-Launcher header ====
print("\n==== 21. server 0.35: launcher names header ====")
for tag, value in (("plain", "claude.exe"), ("Windows path", r"C:\Program Files\Claude\claude.exe"), ("macOS path", "/Applications/Claude.app/Contents/MacOS/Claude"),
                   ("control chars", "a\nb\tc.exe"), ("61 characters", "w" * 61), ("ends in slash", "dir/"), ("empty", ""), ("not text", 5), ("None", None)):
    print(f"21a clean {tag:14}->", repr(srv._clean_launcher_name(value)))
def fake21(table):
    return lambda pid: table.get(pid)
CODE21 = {100: ("python.exe", 90, 50), 90: ("python.exe", 80, 40), 80: ("claude.exe", 70, 30), 70: ("claude.exe", 60, 20), 60: ("explorer.exe", 1, 10)}
for tag, table, pid, skip in (
        ("Code session, venv           ", CODE21, 100, True),
        ("chat, venv                   ", {**CODE21, 80: ("claude.exe", 60, 30)}, 100, True),
        ("no venv: no skip             ", CODE21, 100, False),
        ("venv, parent named otherwise ", {**CODE21, 100: ("python.exe", 80, 50)}, 100, True),
        ("venv, a python further up    ", {100: ("python.exe", 80, 50), 80: ("claude.exe", 90, 30), 90: ("python.exe", 70, 25), 70: ("explorer.exe", 1, 10)}, 100, True),
        ("venv, name in other case     ",{**CODE21, 90: ("Python.EXE", 80, 40)}, 100, True),
        ("three pythons: skip only once", {**CODE21, 80: ("python.exe", 70, 30)}, 100, True),
        ("reused id: level 2 is younger", {**CODE21, 70: ("claude.exe", 60, 35)}, 100, True),
        ("reused id: level 1 is younger", {**CODE21, 80: ("claude.exe", 70, 45)}, 100, True),
        ("same start time is accepted  ", {**CODE21, 80: ("claude.exe", 70, 40), 70: ("claude.exe", 60, 40)}, 100, True),
        ("level 1 start unreadable     ", {**CODE21, 80: ("claude.exe", 70, None)}, 100, True),
        ("level 2 start unreadable     ",{**CODE21, 70: ("claude.exe", 60, None)}, 100, True),
        ("own start unreadable         ", {**CODE21, 100: ("python.exe", 90, None)}, 100, True),
        ("own process missing          ", CODE21, 999, True),
        ("parent id 0                  ", {100: ("python.exe", 0, 50)}, 100, False),
        ("parent gone                  ", {100: ("python.exe", 90, 50)}, 100, False),
        ("only the venv launcher above ", {100: ("python.exe", 90, 50), 90: ("python.exe", 5, 40)}, 100, True),
        ("a name that cleans to nothing", {**CODE21, 80: ("  ", 70, 30)}, 100, True),
        ("a path as process name       ", {**CODE21, 80: ("/usr/bin/zsh", 70, 30)}, 100, True)):
    print(f"21b walk {tag}->", srv._walk_launchers(fake21(table), pid, skip))
_spec21 = importlib.util.spec_from_file_location("srv21", find("glyphbridge_mcp_server.py")); srv21 = importlib.util.module_from_spec(_spec21); _spec21.loader.exec_module(srv21)
print("21c importing the module reads nothing:", srv21._LAUNCHER["value"] is None)
def _raise21(*a): raise OSError("no snapshot")
for tag, os_name, platform, prefix, win, mac in (
        ("Windows, venv          ", "nt", "win32", "venv", lambda: fake21(CODE21), None),
        ("Windows, no venv       ", "nt", "win32", "base", lambda: fake21(CODE21), None),
        ("Windows, snapshot fails", "nt", "win32", "venv", _raise21, None),
        ("Windows, nothing above ", "nt", "win32", "venv", lambda: fake21({100: ("python.exe", 0, 50)}), None),
        ("macOS                  ", "posix", "darwin", "venv", None, fake21({100: ("Python", 80, (5, 0)), 80: ("Claude", 70, (4, 0)), 70: ("launchd", 0, (1, 0))})),
        ("macOS, libproc fails   ", "posix", "darwin", "venv", None, _raise21),
        ("Linux                  ", "posix", "linux", "venv", lambda: fake21(CODE21), fake21(CODE21))):
    srv21.os = _NS20(name=os_name, getpid=lambda: 100)
    srv21.sys = _NS20(platform=platform, prefix=prefix, base_prefix="base")
    srv21._windows_process_info, srv21._mac_process_info = win, mac
    print(f"21d read {tag}->", repr(srv21._read_launcher()))
srv20._opener = _Opener20()
SENT21 = []
class _Opener21:
    def open(self, req, timeout=None):
        SENT21.append((req.full_url.rsplit(str(srv20.LISTENER_PORT), 1)[1], req.get_header("X-glyphbridge-client"), req.get_header("X-glyphbridge-launcher")))
        return _Resp20(json.dumps({"open": True, "x": 1}).encode())
srv20._opener = _Opener21()
for name, launcher in (("claude-code", "claude.exe < claude.exe"), (None, "Claude < launchd"), ("claude-code", None), (None, None), ("x", "é.exe < a.exe")):
    srv20._CLIENT["name"], srv20._LAUNCHER["value"] = name, launcher; SENT21.clear()
    srv20._call_listener("/font/current"); srv20._call_listener_post("/glyph/width", {"name": "A", "width": 600})
    print(f"21e sent {name!r:14} {launcher!r:26}->", SENT21)
srv20._CLIENT["name"] = srv20._LAUNCHER["value"] = None
_main21 = _src20.split('if __name__ == "__main__":')
_block21 = _src20[_src20.index("# ---- launcher names (v0.35)"):_src20.index("# --------------------------------------------------------------------------", _src20.index("def _read_launcher"))]
_code21 = "\n".join(l.split("#")[0] for l in _re19.sub(r'"""(?:.|\n)*?"""', '""', _block21).splitlines())
_calls21 = [l for l in _src20.splitlines() if "_read_launcher()" in l and "def _read_launcher" not in l]
print("21f read once, only when run as a program:", len(_calls21) == 1 and _calls21[0] in _main21[-1],
      "| privacy scan of the launcher code, forbidden words found:",
      [w for w in ("environ", "argv", "CommandLine", "QueryFullProcessImageName", "GetModuleFileName", ".uid", ".gid", "getlogin", "getpass", "expanduser", "pwd", "print(")
       if w in _code21], "| scanned chars > 3000:", len(_code21) > 3000)

# ==== 22. server 0.38: every reply names its font (listener 0.113 headers) ====
print("\n==== 22. server 0.38: the font a reply came from ====")
import email.message as _em22
from urllib.parse import quote
H22 = {"queue": []}
def _hdr22(family=None, style="Regular", key="aaaaaaaaaaaa", count=1, raw=None):
    m = _em22.Message()
    if raw is not None:
        for k, v in raw.items(): m[k] = v
    elif family is not None:
        m["X-Glyphbridge-Font"] = quote(family, safe="") + "/" + quote(style, safe="")
        m["X-Glyphbridge-Font-Key"] = key
        if count is not None: m["X-Glyphbridge-Fonts-Open"] = str(count)
    return m
class _Opener22:
    def open(self, req, timeout=None):
        r = _Resp20(json.dumps({"open": True, "found": True, "width": 600.0}).encode())
        r.headers = H22["queue"].pop(0) if H22["queue"] else _hdr22()
        return r
_spec22 = importlib.util.spec_from_file_location("srv22", find("glyphbridge_mcp_server.py")); srv22 = importlib.util.module_from_spec(_spec22); _spec22.loader.exec_module(srv22)
srv22._opener = _Opener22()
def w22(label, *hdrs):
    H22["queue"][:] = list(hdrs)
    r = srv22.get_glyph_width("A")
    print(label, ":", {k: r[k] for k in r if k not in ("name", "width")})
w22("22a first call, one font            ", _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 1))
w22("22b same font again                 ", _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 1))
w22("22c two fonts open                  ", _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2))
w22("22d the font in front changed       ", _hdr22("testfont", "Regular", "b2b2b2b2b2b2", 2))
w22("22e older listener: no headers      ", _hdr22())
w22("22f after it: same font, no change  ", _hdr22("testfont", "Regular", "b2b2b2b2b2b2", 2))
w22("22g an unsaved font, two open       ", _hdr22("Unnamed", "Regular", "none", 2))
w22("22h another unsaved font, same name ", _hdr22("Unnamed", "Regular", "none", 2))
w22("22i same name, other path           ", _hdr22("Unnamed", "Regular", "c3c3c3c3c3c3", 2))
w22("22j malformed key and count         ", _hdr22(raw={"X-Glyphbridge-Font": "Ari%0Aal/Reg%07ular", "X-Glyphbridge-Font-Key": "XYZ", "X-Glyphbridge-Fonts-Open": "two"}))
w22("22k non-ASCII name, no style part   ", _hdr22(raw={"X-Glyphbridge-Font": quote("Ünïcode Sans", safe=""), "X-Glyphbridge-Font-Key": "d4d4d4d4d4d4"}))
w22("22l empty family and style          ", _hdr22(raw={"X-Glyphbridge-Font": "/", "X-Glyphbridge-Font-Key": "e5e5e5e5e5e5", "X-Glyphbridge-Fonts-Open": "2"}))
def _two_calls22(modified):
    srv22._call_listener("/glyph/width?name=A"); srv22._call_listener("/glyph/width?name=A")
    return {"font_modified": modified}
for lbl, mod in (("22m changed during a write call ", True), ("22n changed during a read call  ", None)):
    H22["queue"][:] = [_hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2), _hdr22("testfont", "Regular", "b2b2b2b2b2b2", 2)]
    print(lbl, ":", srv22._with_font(_two_calls22, mod))
def _refuse22():
    srv22._call_listener("/glyph/width?name=A"); raise srv22.ToolError("refused")
H22["queue"][:] = [_hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2)]
try: srv22._with_font(_refuse22)
except srv22.ToolError as e: print("22o a refusal still updates the remembered font:", srv22._FONT_SEEN, "| message:", str(e))
H22["queue"][:] = [_hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2)]
r = srv22.get_glyph_width("A"); print("22p next call, same font: no font_changed:", "font_changed" not in r)
H22["queue"][:] = [_hdr22("Arial", "Regular", "f6f6f6f6f6f6", 2)]
r = srv22.get_glyph_width("A"); print("22t same name, another path: changed :", r.get("font_changed"), "| note says another file:", "from a different file" in r.get("font_note", ""))
H22["queue"][:] = [_hdr22("Arial Renamed", "Regular", "f6f6f6f6f6f6", 2)]
r = srv22.get_glyph_width("A"); print("22u same path, renamed: not changed :", r.get("font_changed"))
H22["queue"][:] = [_hdr22("Leaked", "Regular", "0a0a0a0a0a0a", 2), _hdr22()]
srv22._call_listener("/glyph/width?name=A")
r = srv22.get_glyph_width("A"); print("22v a call outside a tool does not leak into the next tool:", {k: r[k] for k in r if k.startswith("font")})
print("22q finish_changes makes no listener call: no font fields:", [k for k in srv22.finish_changes() if k.startswith("font")])
_src22 = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
_tools22 = _re19.findall(r"@_tool\(\)\ndef (\w+)\((?:.|\n)*?\n    return (.*)\n", _src22)
print("22r every tool returns through _with_font:", len(_tools22), [n for n, ret in _tools22 if not ret.startswith("_with_font(")])
print("22s headers read inside _do_request    :", "_note_font_headers(getattr(resp, \"headers\", None))" in _src22[_src22.index("def _do_request("):_src22.index("def _call_listener(")])
# v0.39: a ToolError carries the font_note (test 277: a failed first call after a window switch hid the switch).
def _refuse_unknown22():
    srv22._call_listener("/glyph/width?name=A"); raise srv22.OutcomeUnknown("timed out")
for lbl, seen, hdr, fn in (("22w a refusal after a switch         ", ("testfont Regular", "b2b2b2b2b2b2"), _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2), _refuse22),
                           ("22x one font, no switch: unchanged  ", ("Arial Regular", "a1a1a1a1a1a1"), _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 1), _refuse22),
                           ("22y OutcomeUnknown keeps its class  ", ("testfont Regular", "b2b2b2b2b2b2"), _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2), _refuse_unknown22),
                           ("22z older listener: unchanged       ", ("testfont Regular", "b2b2b2b2b2b2"), _hdr22(), _refuse22)):
    srv22._FONT_SEEN.update(name=seen[0], key=seen[1], seen=True); H22["queue"][:] = [hdr]
    try: srv22._with_font(fn)
    except srv22.ToolError as e: print(lbl, ":", type(e).__name__, "|", str(e), "| args", len(e.args))
srv22._FONT_SEEN.update(name="testfont Regular", key="b2b2b2b2b2b2", seen=True)
H22["queue"][:] = [_hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2), _hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2)]
try: srv22._with_font(_refuse22)
except srv22.ToolError as e: print("22w2 a refusal after a switch carries the switch:", "changed since the previous" in str(e))
r = srv22.get_glyph_width("A"); print("22w3 the call after it: no font_changed:", "font_changed" not in r)
srv22._FONT_SEEN.update(name="testfont Regular", key="b2b2b2b2b2b2", seen=True); H22["queue"][:] = [_hdr22("Arial", "Regular", "a1a1a1a1a1a1", 2)]
try: srv22.get_glyph_width("")
except srv22.ToolError as e: print("22x2 refused before any listener call:", str(e), "| remembered font kept:", srv22._FONT_SEEN["name"])
H22["queue"][:] = []

# ---------------------------------------------------------------- 23. server 0.40: the save shortcut ----
print("\n==== 23. server 0.40: the save shortcut is read from the system the server runs on ====")
_plat23 = sys.platform
_src23 = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
_tools23 = _re19.findall(r"@_tool\(\)\ndef (\w+)\(", _src23)
for _p23 in ("win32", "darwin", "linux"):
    sys.platform = _p23
    try:
        _spec23 = importlib.util.spec_from_file_location("srv23" + _p23, find("glyphbridge_mcp_server.py")); m23 = importlib.util.module_from_spec(_spec23); _spec23.loader.exec_module(m23)
    finally:
        sys.platform = _plat23
    _docs23 = [getattr(m23, n).__doc__ or "" for n in _tools23]
    m23._call_listener = lambda path: {"/health": {"status": "ok"}, "/font/current": {"open": False}, "/version": {"version": "0.114"}}[path]
    m23._CHANGES["session"] = 1
    _note23 = m23.check_status().get("save_note", "")
    other = "Ctrl+S" if m23.SAVE_SHORTCUT == "Cmd+S" else "Cmd+S"
    print(f"23a {_p23:<7}: SAVE_SHORTCUT {m23.SAVE_SHORTCUT} | reminder: {m23.SAVE_REMINDER}")
    print(f"23b {_p23:<7}: tools {len(_tools23)} | descriptions naming it {sum(m23.SAVE_SHORTCUT in d for d in _docs23)} | naming the other {sum(other in d for d in _docs23)}"
          f" | placeholder left {sum('SAVE_KEYS' in d for d in _docs23)} | save_note names it: {_note23.endswith(f'File menu or {m23.SAVE_SHORTCUT}.')}")
print("23c the shortcuts are written once each:", _src23.count("Ctrl+S"), _src23.count("Cmd+S"), "| every tool is registered through _tool():", "@mcp.tool()" not in _src23)

# ---------------------------------------------------------------- 24. server 0.41: PostScript names from the font package ----
print("\n==== 24. server 0.41: the PostScript names FontLab's Font Info shows (font package), with their source ====")
_base24 = {"open": True, "path": None, "glyph_count": 2, "family_name": "Unnamed1", "style_name": "Regular", "postscript_font_name": "Unnamed1-Regular",
           "postscript_full_name": "Unnamed1 Regular", "units_per_em": 1000.0}
_pkg24 = {"psn": "W6aTest-Regular", "ffn": "Unnamed1 Regular", "tfn": "Unnamed1", "tsn": "Regular", "sgn": "Unnamed1"}
def c24(tag, extra, base=None):
    r = srv._clean_font({**(base or _base24), **extra})
    print(tag, ":", {k: v for k, v in r.items() if k.startswith(("postscript", "legacy", "package"))}, "| notes:", r.get("notes"))
c24("24a package equals the older view     ", {"package_names": {**_pkg24, "psn": "Unnamed1-Regular"}, "package_matched_by": "only font"})
c24("24b test 298: package differs         ", {"package_names": _pkg24, "package_matched_by": "only font"})
c24("24b2 the full name differs too         ", {"package_names": {**_pkg24, "ffn": "W6a Test Regular"}, "package_matched_by": "path"})
c24("24c psn unreadable in the package     ", {"package_names": {**_pkg24, "psn": None}, "package_matched_by": "path", "package_name_errors": ["psn could not be read (RuntimeError: x)"]})
c24("24d package not matched (two unsaved) ", {"package_names_unavailable": "2 fonts are open and this font's package could not be matched to it: the current font has no file path (a new, unsaved font)"})
c24("24e an older listener                 ", {})
c24("24f a real family named Unnamed Sans  ", {}, {**_base24, "family_name": "Unnamed Sans", "postscript_font_name": "UnnamedSans-Regular", "postscript_full_name": "Unnamed Sans Regular"})
c24("24g package_names not a dict          ", {"package_names": "x", "package_names_unavailable": ""})
_src24 = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
print("24h no fixed placeholder test left:", 'startswith("Unnamed")' not in _src24, "| the description warns against 'unset':", "do not call a name 'unset'" in (srv.get_current_font.__doc__ or ""))

print("\n==== 25. server 0.42: listener 0.120 reads a glyph with modern nodes from the modern layer only (F1); element transforms applied, horizontal check ====")
def mf_reply(pts=((192.466, 0), (464.534, 0), (328.5, 700)), dx=0.0, margins="auto", elements="auto", **kw):
    nodes = [{"index": i, "x": float(x), "y": float(y), "isOn": True, "isOff": False, "isCurve": False, "smooth": False} for i, (x, y) in enumerate(pts)]
    xs = [x + dx for x, _y in pts]
    mo = {"available": True, "contours": [{"index": 0, "closed": True, "clockwise": True, "nodesCount": len(nodes), "nodes": nodes}],
          "node_count": len(nodes), "expected_node_count": len(nodes),
          "margins": {"lsb": min(xs), "rsb": 639.0 - max(xs), "advance": 639.0} if margins == "auto" else margins}
    el = ({"available": True, "wrapper": "cached", "shapes": [{"shape_type": "brush", "contours": 1, "is_component": False, "is_composite": True,
           "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": dx, "dy": 0.0}}]} if elements == "auto" else elements)
    r = {"open": True, "found": True, "name": "A", "source": "modern", "layer_route": "body", "layer_name": "test_font", "node_count": len(nodes),
         "contour_count": 1, "modern_outline": mo, "elements": el, "component_count": 0, "shape_count": 1}
    r.update(kw); return r
def mf(tag, reply, extra_keys=()):
    s10_reset(); S9["get"]["/glyph/outline"] = reply
    r = s9_try(lambda: srv.read_glyph_outline("A"))
    if isinstance(r, str):
        print(tag, "->", r[:160], "| requests", S9["gets"]); return r
    v = r["verification"]
    print(tag, "->", r.get("source"), "|", v["status"], "| y_extent_checked", v.get("y_extent_checked"), "| box", v.get("bounding_box_vs_margins"),
          "| reason", (v.get("reason") or "")[:90], "| requests", S9["gets"], *[f"| {k} {r.get(k)}" for k in extra_keys])
    return r
r = mf("25a identity, Power Brush A      ", mf_reply(), ("left", "right", "advance_width", "ink_bbox"))
print("25b  notes and space           ->", [n[:70] for n in r["notes"][1:]], "|", r["coordinate_space"][:60], "| elements", [(e["description"], e["is_composite"]) for e in r["elements"]])
print("25c  no legacy keys            ->", sorted(k for k in r if k in ("legacy_view_was_stale", "stale_legacy_view", "modern_check")), "| modern_check in verification:", "modern_check" in r["verification"])
r = mf("25d dx -142, raw coordinates    ", mf_reply(dx=-142.466))
print("25e  node 0 after the transform ->", r["contours"][0]["node_list"][0], "|", r["coordinate_space"][:70], "| elements", [e["description"] for e in r["elements"]])
_pts_moved = ((50.0, 0), (322.068, 0), (186.034, 700))
r = mf("25f dx -142, coordinates already moved", mf_reply(pts=_pts_moved, dx=-142.466, margins={"lsb": 50.0, "rsb": 316.932, "advance": 639.0}))
print("25g  coordinate space          ->", r["coordinate_space"][:110], "| raw_x present:", "raw_x" in r["contours"][0]["node_list"][0])
r = mf("25h dy only: ambiguous         ", mf_reply(elements={"available": True, "shapes": [{"contours": 1, "is_composite": True, "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 0.0, "dy": 30.0}}]}))
r = mf("25i margins disagree           ", mf_reply(margins={"lsb": 100.0, "rsb": 174.466, "advance": 639.0}))
r = mf("25j margins unreadable         ", mf_reply(margins=None))
r = mf("25k elements unreadable        ", mf_reply(elements={"available": False, "error": "no shapes list"}))
print("25l  the note                   ->", [n for n in r["notes"] if "transform" in n])
r = mf("25m element list does not map   ", mf_reply(elements={"available": True, "shapes": [{"contours": 2, "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 9.0, "dy": 0.0}}]}))
print("25n  the note                   ->", [n for n in r["notes"] if "map" in n], "| elements key:", "elements" in r)
mf("25o listener error (modern side) ", {"open": True, "found": True, "name": "A", "source": "modern", "error": "the outline could not be read from FontLab's modern layer (x); the legacy layer was not read instead, because reading it can flatten a Power Brush glyph"})
mf("25p malformed modern reply      ", mf_reply(modern_outline={"available": False, "error": "x"}))
mf("25q no modern_outline at all    ", mf_reply(modern_outline=None))
r = mf("25r a component count           ", mf_reply(component_count=2))
print("25s  component note             ->", [n for n in r["notes"] if "component" in n])
_curve = {"available": True, "contours": [{"index": 0, "closed": True, "clockwise": False, "nodesCount": 4, "nodes": [
    {"x": 0.0, "y": 0.0, "isOn": True, "isCurve": False}, {"x": 100.0, "y": 0.0, "isOn": True, "isCurve": False},
    {"x": 100.0, "y": 100.0, "isOn": True, "isCurve": False}, {"x": 0.0, "y": 100.0, "isOn": True, "isCurve": False}]}],
    "node_count": 4, "expected_node_count": 4, "margins": {"lsb": 10.0, "rsb": 10.0, "advance": 120.0}}
r = mf("25t dx 10 on a square           ", mf_reply(modern_outline=_curve, elements={"available": True, "shapes": [{"contours": 1, "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 10.0, "dy": 0.0}}]}))
os.environ["GLYPHBRIDGE_MODERN"] = "0"
r, _n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(0, 100, 500))
print("25u GLYPHBRIDGE_MODERN=0        ->", S9["gets"][:1], "| F1 note:", [n[:60] for n in (r.get("notes", []) if isinstance(r, dict) else []) if "Power Brush" in n] if isinstance(r, dict) else r[:100])
del os.environ["GLYPHBRIDGE_MODERN"]
r, _n = read15(legacy_reply(0, {"left": 0.0, "right": 100.0, "width": 500.0}), sb_reply(0, 100, 500))
print("25v an older listener (no source) ->", (r.get("verification", {}).get("status") if isinstance(r, dict) else r[:80]), "| F1 note:", any("Power Brush" in n for n in r.get("notes", [])) if isinstance(r, dict) else None)
print("25w version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)

print("\n==== 26. server 0.43: exact quadratic extents; the vertical extent checked against FontLab's ink box (listener 0.121, layer.inkBox()) ====")
# Live data (521-530): testglyph1 (quadratic, scale and offset), testglyph2 (cubic), testglyph3 (quadratic), A (Power Brush). FontLab's
# inkBox() names its sides y-down: "top" is the lower y.
def qn(i, x, y): return node(i, x, y, on=False, curve=False)
def kn(rows):                                    # (x, y) on-curve, (x, y, "q") quadratic off-curve, (x, y, "c") cubic control point
    return [qn(i, r[0], r[1]) if len(r) == 3 and r[2] == "q" else hnode(i, r[0], r[1]) if len(r) == 3 else node(i, r[0], r[1]) for i, r in enumerate(rows)]
def ink(lo, hi, **kw):
    d = {"type": "QRectF", "left": 0.0, "right": 1.0, "top": float(lo), "bottom": float(hi), "width": 1.0, "height": float(hi) - float(lo)}
    d.update(kw); return d
def g26(contours, margins, matrix=None, **kw):
    cs = [{"index": i, "closed": True, "clockwise": False, "nodesCount": len(n), "nodes": n} for i, n in enumerate(contours)]
    nn = sum(len(n) for n in contours)
    mo = {"available": True, "contours": cs, "node_count": nn, "expected_node_count": nn, "margins": margins}
    m = matrix or {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 0.0, "dy": 0.0}
    el = {"available": True, "wrapper": "cached", "shapes": [{"shape_type": "contours", "contours": len(contours), "is_component": False, "is_composite": False, "matrix": m}]}
    r = {"open": True, "found": True, "name": "A", "source": "modern", "layer_route": "body", "layer_name": "test_font", "node_count": nn,
         "contour_count": len(contours), "modern_outline": mo, "elements": el, "component_count": 0, "shape_count": 1}
    r.update(kw); return r
def m26(tag, reply):
    s10_reset(); S9["get"]["/glyph/outline"] = reply
    r = s9_try(lambda: srv.read_glyph_outline("A"))
    if isinstance(r, str):
        print(tag, "->", r[:160]); return r
    v = r["verification"]
    print(tag, "->", v["status"], "| y_extent_checked", v.get("y_extent_checked"), "| bbox", r.get("ink_bbox"), "exact", r.get("ink_bbox_exact"),
          "| vs FontLab", v.get("ink_box_vs_fontlab"), "| reason", (v.get("reason") or "")[:110], "| y note", (v.get("y_extent_note") or "")[:90])
    return r
G3 = kn([(128, 414), (383, 274), (357, 267, "q"), (307, 235, "q"), (255, 208, "q"), (202, 200, "q"), (173, 217), (144, 234, "q"), (110, 281, "q"), (99, 334, "q"), (111, 389, "q")])
G3_M = {"lsb": 101.86956521739131, "rsb": 117.0, "advance": 500.0}
r = m26("26a testglyph3, quadratic (live 525/526)", g26([G3], G3_M, fontlab_ink_box=ink(203.2380952380952, 414.0)))
print("26b  svg and checked_against   ->", r["contours"][0].get("svg_path"), "|", r["verification"]["checked_against"])
_a1, _d1 = (93.0201210975647 - 15) / 82, (390.1471252441406 - 24) / 378
G1 = [kn([(82, 378), (99, 416, "q"), (167, 430, "q"), (201, 418), (218, 412, "q"), (243, 385, "q"), (257, 350, "q"), (255, 314, "q"), (245, 299), (235, 284, "q"), (214, 251, "q"),
          (191, 223, "q"), (169, 206, "q"), (157, 207), (145, 208, "q"), (122, 208, "q"), (100, 214, "q"), (82, 230, "q"), (76, 248), (64, 283, "q"), (72, 355, "q")]),
      kn([(167, 159), (152, 153, "q"), (127, 139, "q"), (113, 123, "q"), (113, 106, "q"), (125, 97), (137, 88, "q"), (160, 70, "q"), (183, 61, "q"), (203, 63, "q"), (212, 72),
          (221, 81, "q"), (237, 101, "q"), (247, 120, "q"), (247, 138, "q"), (239, 146), (223, 163, "q"), (184, 167, "q")])]
r = m26("26c testglyph1, quadratic, scale and offset (live 521/522)", g26(G1, {"lsb": 78.74814772605895, "rsb": 74.30605468153954, "advance": 333.0},
        {"m11": _a1, "m12": 0.0, "m21": 0.0, "m22": _d1, "dx": 15.0, "dy": 24.0}, fontlab_ink_box=ink(83.8797607421875, 436.2341485274465)))
print("26d  coordinate space          ->", r["coordinate_space"][:80])
G2 = kn([(128, 414), (383, 274), (314, 255, "c"), (250, 172, "c"), (173, 217), (96, 262, "c"), (83, 347, "c")])
m26("26e testglyph2, cubic (live 523/524)  ", g26([G2], {"lsb": 102.15479625533814, "rsb": 117.0, "advance": 500.0}, fontlab_ink_box=ink(203.80555555555554, 414.0)))
m26("26f A, ink box top = lower y          ", mf_reply(fontlab_ink_box=ink(0.0, 700.0)))
m26("26g A, sides named the other way      ", mf_reply(fontlab_ink_box=ink(700.0, 0.0)))
m26("26h A, FontLab's box 2 units higher   ", mf_reply(fontlab_ink_box=ink(2.0, 702.0)))
m26("26i A, 0.04 off vertically            ", mf_reply(fontlab_ink_box=ink(0.04, 700.0)))
m26("26j A, 0.06 off vertically            ", mf_reply(fontlab_ink_box=ink(0.0, 700.06)))
m26("26k inkBox failed                     ", mf_reply(fontlab_ink_box={"error": "RuntimeError: inkBox boom"}))
m26("26l an older listener: no ink box     ", mf_reply())
m26("26m a getter that was not a number    ", mf_reply(fontlab_ink_box={"type": "QRectF", "error": "rect.left was not a number (str)"}))
m26("26n top not a number                  ", mf_reply(fontlab_ink_box=ink(0.0, 700.0, top="x")))
m26("26o ink box not a dict                ", mf_reply(fontlab_ink_box="box"))
m26("26p horizontal mismatch, y agrees     ", mf_reply(margins={"lsb": 100.0, "rsb": 174.466, "advance": 639.0}, fontlab_ink_box=ink(0.0, 700.0)))
_dy = {"available": True, "shapes": [{"contours": 1, "is_composite": True, "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 0.0, "dy": 30.0}}]}
r = m26("26q dy 30, FontLab box = raw nodes    ", mf_reply(elements=_dy, fontlab_ink_box=ink(0.0, 700.0)))
print("26r  coordinate space          ->", r["coordinate_space"][:90])
r = m26("26s dy 30, FontLab box = moved nodes  ", mf_reply(elements=_dy, fontlab_ink_box=ink(30.0, 730.0)))
print("26t  coordinate space          ->", r["coordinate_space"][:90])
m26("26u dy 30, FontLab box = neither      ", mf_reply(elements=_dy, fontlab_ink_box=ink(10.0, 710.0)))
m26("26v dy 30, no ink box: ambiguous      ", mf_reply(elements=_dy))
_flip = {"available": True, "shapes": [{"contours": 1, "is_composite": True, "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": -1.0, "dx": 0.0, "dy": 700.0}}]}
m26("26w mirrored in its own box: ambiguous", mf_reply(pts=((192.466, 0), (464.534, 0), (464.534, 700), (192.466, 700)), elements=_flip, fontlab_ink_box=ink(0.0, 700.0)))
MIX = kn([(0, 0), (400, 0), (500, 100, "c"), (500, 300, "c"), (400, 400), (200, 500, "q"), (0, 400)])
m26("26x mixed contour: not exact, no y check", g26([MIX], {"lsb": 0.0, "rsb": -500.0, "advance": 0.0}, fontlab_ink_box=ink(0.0, 450.0)))
m26("26y polygon, exact without curves     ", mf_reply(pts=((10, 20), (110, 20), (60, 220)), margins={"lsb": 10.0, "rsb": 529.0, "advance": 639.0}, fontlab_ink_box=ink(20.0, 220.0)))
# a flat top at the implied on-curve point (150, 100): both pieces have their y extreme at t = 1 / t = 0, so only the piece ends give it
m26("26y2 flat top at an implied point     ", g26([kn([(0, 0), (100, 100, "q"), (200, 100, "q"), (300, 0)])], {"lsb": 0.0, "rsb": -300.0, "advance": 0.0}, fontlab_ink_box=ink(0.0, 100.0)))
# the parser and the quadratic extremes themselves
def pieces(rows, closed=True):
    p = srv._contour_pieces([{"x": float(r[0]), "y": float(r[1]), "on": len(r) == 2, "curve": len(r) == 3 and r[2] == "c"} for r in rows], closed)
    return None if p is None else (p[0], [(pc[0],) + tuple(tuple(round(v, 3) for v in q) for q in pc[1:]) for pc in p[1]])
print("26z1 two off-curve points       ->", pieces([(0, 0), (100, 100, "q"), (200, 100, "q"), (300, 0)]))
print("26z2 starts on an off-curve point ->", pieces([(100, 100, "q"), (200, 100, "q"), (300, 0), (0, 0)]))
print("26z3 closing run at the end     ->", pieces([(0, 0), (300, 0), (300, 100, "q"), (0, 100, "q")]))
print("26z4 no on-curve point          ->", pieces([(0, 0, "q"), (100, 0, "q"), (100, 100, "q")]))
print("26z5 one segment, both kinds    ->", pieces([(0, 0), (100, 100, "c"), (200, 100, "q"), (300, 0)]))
print("26z6 open contour               ->", pieces([(0, 0), (100, 100, "q"), (300, 0)], closed=False))
print("26z7 three cubic handles        ->", pieces([(0, 0), (100, 100, "c"), (200, 100, "c"), (250, 50, "c"), (300, 0)]))
def qx(*pts): return [tuple(round(v, 4) for v in p) for p in srv._quad_extremes(*pts)]
print("26z8 quad extremes              -> peak", qx((0, 0), (50, 100), (100, 0)), "| monotonic", qx((0, 0), (50, 50), (100, 100)), "| x only (y linear)", qx((0, 0), (100, 100), (0, 200)),
      "| at an end (t=0)", qx((0, 0), (0, 100), (100, 100)))
_d26 = srv.get_glyph_outline.__doc__ or ""
print("26z9 docs                       -> quadratic extents:", "cubic and quadratic segments" in _d26, "| FontLab's ink box:", "FontLab's own ink box vertically" in _d26,
      "| old 'quadratic stays unverified' gone:", "quadratic or malformed curves stay" not in _d26)
print("26zz version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)

# ==== 27. server 0.44: set_kerning writes glyph : glyph pairs through POST /kerning/set (listener 0.124; faked listener replies) ====
print("\n==== 27. server 0.44: set_kerning (faked listener replies) ====")
_save27 = (srv._call_listener, srv._call_listener_post)
K27 = {"version": "0.124", "reply": None, "paths": [], "posts": []}
def _k27_get(path):
    K27["paths"].append(path)
    if path == "/version":
        v = K27["version"]
        if isinstance(v, Exception): raise v
        return {"version": v}
    raise AssertionError("unexpected GET " + path)
def _k27_post(path, payload, timeout=0):
    K27["posts"].append((path, payload, timeout))
    r = K27["reply"]
    if isinstance(r, Exception): raise r
    return r
srv._call_listener, srv._call_listener_post = _k27_get, _k27_post
def k27(reply=None, version="0.124", **call):
    K27["reply"] = reply; K27["version"] = version; K27["paths"].clear(); K27["posts"] = []
    srv._reset_change_tracking()
    try:
        return srv.write_kerning(**call)
    except srv.ToolError as e:
        return "ToolError: " + str(e)
def k27sent(): return [(p, pl) for p, pl, _t in K27["posts"]]
def k27chg(): return (srv._CHANGES["package"], srv._CHANGES["package_unsure"])
def side(value, source="glyph : glyph", **cls): return dict({"value": value, "kerned": value != 0, "source": source}, **cls)
def okset(left, right, value, before=None, changed=True, over=False):
    return {"left": left, "right": right, "requested": value, "before": before or side(0, "none"), "after": side(float(value)),
            "status": "set", "set": True, "changed": changed, "exception_over_class": over}
def setreply(results, **extra):
    return dict({"open": True, "fonts_open": 1, "matched_by": "only font", "family_name": "Kern Test", "master": "Regular", "master_count": 1,
                 "units_per_em": 1000.0, "count": len(results), "set_count": sum(1 for e in results if e.get("set") is True), "stopped": False,
                 "table_size_before": 2, "table_size_after": 3, "table_size_as_expected": True, "results": results}, **extra)
def row27(label, r):
    if isinstance(r, str): print(label, ":", r[:400], "| changes", k27chg()); return
    print(label, ":", {k: v for k, v in r.items() if k not in ("results", "agent_instruction")}, "| changes", k27chg())
    for e in r["results"]: print("       ", e)

r = k27(setreply([okset("ks2L", "ks2R", -50)]), pairs=[[" ks2L ", "ks2R", -50]]); row27("27a one new pair                ", r)
print("27b request                      :", k27sent(), "| timeout", K27["posts"][0][2], "| GETs", K27["paths"])
print("27c instruction                  :", r["agent_instruction"])
r = k27(setreply([okset("A", "V", -152, before=side(-152.0), changed=False)], table_size_after=2), pairs=[["A", "V", -152]]); row27("27d the same value: no change    ", r)
print("27d2 no save text when unchanged :", "finish_changes" not in r["agent_instruction"])
r = k27(setreply([okset("Aacute", "W.c2sc", -30, before=side(-76.0, "class : class", left_class="Aring", right_class="W"), over=True)]), pairs=[["Aacute", "W.c2sc", -30]])
row27("27e over a class value           ", r)
r = k27(setreply([okset("A", "B", -60), okset("T", "o", -200, before=side(-227.0)), okset("V", "A", 10, before=side(-152.0))]), pairs=[["A", "B", -60], ["T", "o", -200], ("V", "A", 10)])
row27("27f three pairs                  ", r)
print("--- refused before anything is sent")
for _lbl, _kw in (("27g pairs not a list          ", dict(pairs="A:V:-10")), ("27g2 pairs empty               ", dict(pairs=[])), ("27g3 an item of two            ", dict(pairs=[["A", "V"]])),
                  ("27g4 a bad name                ", dict(pairs=[["A V", "W", -1]])), ("27g5 an empty name             ", dict(pairs=[["  ", "W", -1]])), ("27g6 a value that is True     ", dict(pairs=[["A", "V", True]])),
                  ("27g7 a value as text           ", dict(pairs=[["A", "V", "-10"]])), ("27g8 NaN                       ", dict(pairs=[["A", "V", float("nan")]])),
                  ("27g9 infinity                  ", dict(pairs=[["A", "V", float("-inf")]])), ("27g10 a pair twice (stripped)  ", dict(pairs=[["A", "V", -1], [" A", "V ", -2]])),
                  ("27g11 flag not a bool          ", dict(pairs=[["A", "V", -1]], confirmed_large_write="yes")), ("27g12 a name not a string      ", dict(pairs=[[5, "V", -1]]))):
    r = k27(setreply([]), **_kw); print(_lbl, ":", r[:200], "| sent", k27sent(), "| GETs", K27["paths"], "| changes", k27chg())
r = k27(setreply([]), pairs=[["A", "V", -1]] * 1 + [[f"g{i}", "V", -1] for i in range(250)]); print("27h 251 pairs, no approval       :", r[:160], "| sent", len(k27sent()))
print("27h2 refusal text mentions       :", all(w in r for w in ("251 kerning pairs", "250-pair threshold", "nothing was changed", "ask whether they approve", "confirmed_large_write=true", "Never set that flag")))
_big = [[f"g{i}", "V", -1] for i in range(251)]
r = k27(setreply([okset(a, b, v) for a, b, v in _big]), pairs=_big, confirmed_large_write=True); print("27h3 251 pairs, approved         :", r.get("set_count"), r.get("large_write_confirmed"), "| timeout", K27["posts"][0][2])
r = k27(setreply([okset(a, b, v) for a, b, v in _big[:250]]), pairs=_big[:250]); print("27h4 250 pairs need no approval  :", r.get("set_count"), "large_write_confirmed" in r)
for _v in ("0.123", "0.104"):
    r = k27(setreply([okset("A", "V", -1)]), version=_v, pairs=[["A", "V", -1]]); print("27i listener", _v.ljust(6), "          :", r[:150], "| sent", k27sent())
r = k27(setreply([okset("A", "V", -1)]), version=RuntimeError("down"), pairs=[["A", "V", -1]]); print("27i2 version unreadable           :", "set" if isinstance(r, dict) else r[:90], "| sent", len(k27sent()))
print("--- the listener's answer")
r = k27({"open": False}, pairs=[["A", "V", -1]]); row27("27j no font open                 ", r)
r = k27({"open": True, "error": "no glyph named 'Q' in the current font; nothing was set"}, pairs=[["Q", "V", -1]]); row27("27k listener refuses             ", r)
r = k27(setreply([okset("A", "V", -1)]), pairs=[["A", "V", -1], ["T", "o", -2]]); row27("27l answer has too few results   ", r)
r = k27(dict(setreply([]), results="x"), pairs=[["A", "V", -1]]); row27("27l2 results not a list         ", r)
_fail2 = {"left": "T", "right": "o", "requested": -200, "before": side(-227.0), "after": side(-227.0), "status": "failed", "set": False, "changed": False,
          "exception_over_class": False, "call_error": "RuntimeError: set boom", "reason": "kerning.set raised RuntimeError: set boom"}
r = k27(setreply([okset("A", "B", -60), _fail2, {"left": "V", "right": "A", "requested": -10, "status": "not attempted"}], stopped=True), pairs=[["A", "B", -60], ["T", "o", -200], ["V", "A", -10]])
row27("27m stopped at pair 2 of 3       ", r)
r = k27(setreply([_fail2, {"left": "V", "right": "A", "requested": -10, "status": "not attempted"}], stopped=True), pairs=[["T", "o", -200], ["V", "A", -10]])
row27("27n first pair failed, unchanged ", r)
_unk = dict(_fail2, changed=None, after={"error": "kerning.get raised RuntimeError: boom"}, reason="the entry could not be read back: boom")
r = k27(setreply([_unk], stopped=True), pairs=[["T", "o", -200]]); row27("27o read back failed: unknown    ", r)
_round = dict(_fail2, call_error=None, after=side(-13.0), changed=True, reason="the entry reads -13.0 after setting, not -12"); _round.pop("call_error")
r = k27(setreply([_round], stopped=True), pairs=[["T", "o", -12]]); row27("27p another value stored: changed", r)
_lie = okset("A", "V", -30, before=side(-76.0, "class : class", left_class="Aring", right_class="W")); _lie["after"] = side(-76.0, "class : class", left_class="Aring", right_class="W")
r = k27(setreply([_lie]), pairs=[["A", "V", -30]]); row27("27q set true, a class answers    ", r)
_lie2 = okset("A", "V", -30); _lie2["after"] = side(-31.0)
r = k27(setreply([_lie2]), pairs=[["A", "V", -30]]); row27("27q2 set true, another value     ", r)
_lie3 = okset("A", "V", -30); _lie3["changed"] = "yes"
r = k27(setreply([_lie3]), pairs=[["A", "V", -30]]); row27("27q3 changed not a bool          ", r)
r = k27(setreply([okset("T", "o", -30)]), pairs=[["A", "V", -30]]); row27("27r answered for another pair    ", r)
r = k27(setreply([okset("A", "B", -60)], table_size_as_expected=False), pairs=[["A", "B", -60]]); row27("27s table grew unexpectedly      ", r)
print("27s2 warning in the instruction  :", "WARNING" in r["agent_instruction"])
r = k27(setreply([okset("A", "B", -60)], fonts_open=2, matched_by="path", master_count=3, master="Bold"), pairs=[["A", "B", -60]]); row27("27t two fonts, three masters     ", r)
print("27t2 notes                       :", "2 fonts are open" in r["agent_instruction"], "(Kern Test)" in r["agent_instruction"], "3 masters" in r["agent_instruction"])
r = k27(setreply([okset("A", "B", -60)], fonts_open=True, family_name="x" * 64, master=5, units_per_em="1000", table_size_before=True), pairs=[["A", "B", -60]]); row27("27u odd header values dropped    ", r)
r = k27(setreply([dict(okset("A", "B", -60), before={"value": "x", "source": "none"})]), pairs=[["A", "B", -60]]); row27("27v unusable 'before' value      ", r)
r = k27(srv.OutcomeUnknown("The FontLab listener did not answer /kerning/set within 5s."), pairs=[["A", "B", -60]]); row27("27w timeout: outcome unknown     ", r)
r = k27(srv.ToolError("Cannot reach the listener"), pairs=[["A", "B", -60]]); row27("27w2 listener not reachable      ", r)
print("--- the tool")
_src27 = open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read()
_body27 = _src27[_src27.index("_KERN_SET_INSTRUCTION = ("):_src27.index("def _check_polygon_points(")]
print("27x static scan                  : posts", _re19.findall(r'_write_post\("([^"]+)"', _body27), "| direct posts", len(_re19.findall(r"_call_listener_post\(", _body27)),
      "| GETs", len(_re19.findall(r"_call_listener\(", _body27)), "| save", bool(_re19.search(r"\.save\(|save\(", _body27)), "| requires 0.124", '_require_listener((0, 124), "set_kerning")' in _body27,
      "| read scan (19ci) ends before it:", _src27.index("def write_glyph_sidebearings(") < _src27.index("_KERN_SET_INSTRUCTION = ("))
_d27 = srv.set_kerning.__doc__ or ""
_need27 = ("[left, right, value]", "class (group) names cannot be used", "exception_over_class", "verified by re-reading", "'before'", "More than 250 pairs",
           "Never set confirmed_large_write=true on your own", "only after switching", "another open font and back", "saved and reopened", "whole numbers", "asks no save",
           "Edit > Undo cannot take them back", "whose window is in front", "Needs listener v0.124", "NEVER saves", "finish_changes ONCE")
print("27y docstring key phrases        :", [w for w in _need27 if w not in _d27] == [], "| missing", [w for w in _need27 if w not in _d27], "| save shortcut filled in:", "SAVE_KEYS" not in _d27)
K27["reply"] = setreply([okset("A", "B", -60)]); K27["version"] = "0.124"
srv._reset_change_tracking(); _w27 = srv.set_kerning(pairs=[["A", "B", -60]]); srv._reset_change_tracking(); _d27r = srv.write_kerning(pairs=[["A", "B", -60]])
print("27z wrapper equals write_kerning :", {k: v for k, v in _w27.items() if k not in ("font", "fonts_open")} == {k: v for k, v in _d27r.items() if k not in ("font", "fonts_open")}, "| font field added:", "font" in _w27 or "fonts_open" in _w27)
print("--- server 0.45: whole units, the entry's value after a failure, matched_by, message fixes (live 567-569, 574)")
for _lbl, _p in (("27za -12.5 refused before sending", [["A", "V", -12.5]]), ("27zb 12.4 refused              ", [["A", "V", 12.4]]),
                 ("27zc 0.5 in pair 2 of 2         ", [["A", "V", -10], ["T", "o", 0.5]]), ("27zd a tiny fraction           ", [["A", "V", -10.000001]])):
    r = k27(setreply([]), pairs=_p); print(_lbl, ":", r[:200], "| sent", k27sent(), "| GETs", K27["paths"], "| changes", k27chg())
r = k27(setreply([okset("A", "V", -12)]), pairs=[["A", "V", -12.0]]); print("27ze -12.0 is whole: sent        :", k27sent(), "| set", r.get("set_count") if isinstance(r, dict) else r[:120])
r = k27(setreply([okset("A", "V", 1000)]), pairs=[["A", "V", 1000]]); print("27zf a large whole number        :", r.get("set_count") if isinstance(r, dict) else r[:120])
for _lbl, _m in (("27zg matched_by path            ", "path"), ("27zh matched_by odd: dropped    ", "guess"), ("27zi matched_by missing        ", None)):
    _rep = setreply([okset("A", "B", -60)]); _rep.pop("matched_by")
    if _m is not None: _rep["matched_by"] = _m
    r = k27(_rep, pairs=[["A", "B", -60]]); print(_lbl, ":", r.get("matched_by"))
r = k27({"open": True, "error": "the kerning table of master 'Regular' is not reachable: RuntimeError: boom"}, pairs=[["A", "V", -1]]); print("27zj refusal without the listener's 'nothing was set':", r)
r = k27({"open": True, "error": "no glyph named 'Q' in the current font; nothing was set."}, pairs=[["Q", "V", -1]]); print("27zk listener text ends in a stop :", r)
_held = dict(_fail2, call_error=None, after=side(-13.0), changed=True, reason="the entry reads -13.0 after setting, not -12"); _held.pop("call_error")
r = k27(setreply([okset("A", "B", -60), _held], stopped=True), pairs=[["A", "B", -60], ["T", "o", -12]]); print("27zl now holds, after one set     :", r)
_noafter = dict(_fail2, call_error=None, changed=True, reason="odd"); _noafter.pop("call_error"); _noafter.pop("after")
r = k27(setreply([_noafter], stopped=True), pairs=[["T", "o", -12]]); print("27zm changed, no 'after' value   :", "now holds" in r, "|", r[:160])
_errafter = dict(_noafter, after={"error": "boom"})
r = k27(setreply([_errafter], stopped=True), pairs=[["T", "o", -12]]); print("27zn changed, 'after' an error   :", "now holds" in r)
r = k27(setreply([_fail2], stopped=True), pairs=[["T", "o", -200]]); print("27zo unchanged: no 'now holds'   :", "now holds" in r)
r = k27(setreply([okset("A", "B", -60)]), pairs=[["A", "B", -60]]); _i27 = r["agent_instruction"]
print("27zp instruction: panel facts    :", all(w in _i27 for w in ("a new pair is missing from the panel", "keeps its old value", "switches to another open font and back",
      "File > New Font", "saves and reopens")), "| old wording gone:", "does not list the pair until" not in _i27)
_save27b = srv._call_listener_post
for _lbl, _err in (("27zq read refusal: stop added    ", "2 fonts are open; close the others"), ("27zr read refusal: one stop only ", "the table is not reachable."),
                   ("27zs read refusal: question mark", "was another window brought to the front?")):
    srv._call_listener_post = lambda p, pl, timeout=0, e=_err: {"open": True, "error": e}
    try: srv.read_kerning(pairs=[["A", "V"]]); _o = "no error"
    except srv.ToolError as e: _o = str(e)
    print(_lbl, ":", _o)
srv._call_listener_post = _save27b
print("27zz version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = _save27
srv._reset_change_tracking()

# ==== 28. server 0.46: open contours read from the modern layer (live 581: an open straight V; 583: an open cubic arch) ====
print("\n==== 28. server 0.46: open contours (live 581 / 583) ====")
def g28(contours, margins, **kw):
    # contours: (closed flag, nodes); FontLab's clockwise flag as seen live (581 True, 583 False)
    cs = [{"index": i, "closed": cl, "clockwise": i % 2 == 0, "nodesCount": len(n), "nodes": n} for i, (cl, n) in enumerate(contours)]
    nn = sum(len(n) for _cl, n in contours)
    mo = {"available": True, "contours": cs, "node_count": nn, "expected_node_count": nn, "margins": margins}
    el = {"available": True, "wrapper": "cached", "shapes": [{"shape_type": "contours", "contours": len(contours), "is_component": False, "is_composite": False,
          "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 0.0, "dy": 0.0}}]}
    r = {"open": True, "found": True, "name": "A", "source": "modern", "layer_route": "body", "layer_name": "Regular", "node_count": nn,
         "contour_count": len(contours), "modern_outline": mo, "elements": el, "component_count": 0, "shape_count": 1}
    r.update(kw); return r
def m28(tag, reply):
    r = m26(tag, reply)
    if isinstance(r, str):
        return r
    for c in r["contours"]:
        print("     contour", c["index"], "closed", c["closed"], "| direction", c["direction_computed"], "| inversion", c["flag_follows_known_inversion"],
              "| svg", c.get("svg_path"))
    print("     open note:", [n for n in r["notes"] if "OPEN" in n])
    _why = r["verification"].get("reason") or ""
    if "could not be told apart (" in _why:
        print("     why:", _why.split("could not be told apart (", 1)[1].split(")", 1)[0])
    return r
V581 = kn([(24, 482), (132, 69), (228, 462)])
ARCH583 = kn([(105, 104), (105, 280, "c"), (398, 255, "c"), (398, 104)])
m28("28a open V (live 581)               ", g28([(False, V581)], {"lsb": 24.0, "rsb": -228.0, "advance": 0.0}, fontlab_ink_box=ink(69.0, 482.0)))
m28("28b open arch (live 583), FontLab top 226.804", g28([(False, ARCH583)], {"lsb": 105.0, "rsb": -398.0, "advance": 0.0}, fontlab_ink_box=ink(104.0, 226.8040)))
m28("28c open arch, FontLab top 240      ", g28([(False, ARCH583)], {"lsb": 105.0, "rsb": -398.0, "advance": 0.0}, fontlab_ink_box=ink(104.0, 240.0)))
m28("28d open arch, starts on a handle   ", g28([(False, kn([(105, 280, "c"), (398, 255, "c"), (398, 104), (105, 104)]))], {"lsb": 105.0, "rsb": -398.0, "advance": 0.0}))
m28("28e open arch, ends on a handle     ", g28([(False, kn([(105, 104), (105, 280, "c"), (398, 255, "c")]))], {"lsb": 105.0, "rsb": -398.0, "advance": 0.0}))
m28("28f open quadratic                  ", g28([(False, kn([(0, 0), (100, 100, "q"), (300, 0)]))], {"lsb": 0.0, "rsb": -300.0, "advance": 0.0}, fontlab_ink_box=ink(0.0, 50.0)))
m28("28g closed flag unreadable, a curve ", g28([(None, ARCH583)], {"lsb": 105.0, "rsb": -398.0, "advance": 0.0}))
m28("28h closed flag unreadable, straight", g28([(None, V581)], {"lsb": 24.0, "rsb": -228.0, "advance": 0.0}, fontlab_ink_box=ink(69.0, 482.0)))
m28("28i closed V (control: as before)   ", g28([(True, V581)], {"lsb": 24.0, "rsb": -228.0, "advance": 0.0}, fontlab_ink_box=ink(69.0, 482.0)))
m28("28j open and closed together        ", g28([(True, kn([(0, 0), (100, 0), (100, 100), (0, 100)])), (False, ARCH583)], {"lsb": 0.0, "rsb": -398.0, "advance": 0.0},
                                                fontlab_ink_box=ink(0.0, 226.8040)))
m28("28k open, a single node             ", g28([(False, kn([(50, 60)]))], {"lsb": 50.0, "rsb": -50.0, "advance": 0.0}, fontlab_ink_box=ink(60.0, 60.0)))
print("28l parser, open cubic             ->", pieces([(105, 104), (105, 280, "c"), (398, 255, "c"), (398, 104)], closed=False))
print("28m parser, open straight + quad   ->", pieces([(0, 0), (100, 0), (150, 80, "q"), (200, 0)], closed=False))
print("28n parser, closed flag None       ->", pieces([(0, 0), (100, 0), (100, 100)], closed=None))
print("28o svg, open / closed            ->", srv._svg_path((0, 0), [("L", (0, 0), (10, 0))], closed=False), "|", srv._svg_path((0, 0), [("L", (0, 0), (10, 0))]))
_d28 = srv.get_glyph_outline.__doc__ or ""
print("28p docs                           -> open contours:", "An open contour ('closed': false)" in _d28, "| no direction:", "'not applicable (open contour)'" in _d28)
print("28z version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)

# ==== 29. server 0.47: draw_path draws OPEN contours ({"points": [...], "closed": false}; listener 0.126; faked listener replies) ====
print("\n==== 29. server 0.47: draw_path with open contours (faked listener replies) ====")
OPEN_V = {"points": [P(24, 482), P(132, 69), P(228, 462)], "closed": False}
OPEN_ARCH = {"points": [P(105, 104), P(398, 104, (105, 280), (398, 255))], "closed": False}
OKOPEN = dict(OKPATH, points=3, segments_curved=0, contour_sizes=[3], state_after={"active_layer": "present", "shapes": 1, "nodes": 3},
              margins={"lsb": 24.0, "rsb": -228.0, "advance": 0.0}, ink_width=204.0, open_contours=[0])
def d29(tag, contours, version="0.126", reply=None, show=("drawn", "verified", "closed", "contours", "nodes")):
    s10_reset(); S9["version"] = version; S9["post"]["/glyph/path"] = dict(reply or OKOPEN); n = len(S9["posts"])
    r = s9_try(lambda: srv.write_glyph_path("od", contours))
    sent = S9["posts"][n][1]["contours"] if len(S9["posts"]) > n else None
    if isinstance(r, str):
        print(tag, "->", r, "| posts", len(S9["posts"]) - n); return r, sent
    print(tag, "->", {k: r.get(k) for k in show}, "| posts", len(S9["posts"]) - n)
    return r, sent
r, sent = d29("29a open V                    ", [OPEN_V])
print("29b  sent                      ->", sent)
print("29c  note / open note          ->", r["note"][:60], "|", r.get("open_contours_note"))
print("29d  agent_instruction         ->", r["agent_instruction"])
r, sent = d29("29e open arch                 ", [OPEN_ARCH]); print("29f  sent                      ->", sent)
r, sent = d29("29g open V and a closed square", [OPEN_V, [P(0, 0), P(100, 0), P(100, 100), P(0, 100)]]); print("29h  sent                      ->", sent)
r, sent = d29("29i object with closed true   ", [{"points": PATH_RECT[0], "closed": True}], reply=OKPATH, show=("drawn", "closed", "open_contours_note"))
print("29j  sent as a plain list: ", sent == PATH_RECT, "| instruction is the save text only:", r["agent_instruction"] == srv._SAVE_INSTRUCTION, "| note:", r["note"][:40])
r, sent = d29("29k object without closed     ", [{"points": PATH_RECT[0]}], reply=OKPATH, show=("drawn", "closed")); print("29l  sent as a plain list: ", sent == PATH_RECT)
d29("29m listener 0.125, open      ", [OPEN_V], version="0.125")
d29("29n listener 0.125, closed only", PATH_RECT, version="0.125", reply=OKPATH, show=("drawn", "closed"))
d29("29o listener version unreadable, open", [OPEN_V], version=None)
for tag, cont in (("29p object without points     ", [{"closed": False}]),
                  ("29q object with a stray key   ", [{"points": OPEN_V["points"], "closed": False, "smooth": True}]),
                  ("29r closed is a string        ", [{"points": OPEN_V["points"], "closed": "no"}]),
                  ("29s closed is 0               ", [{"points": OPEN_V["points"], "closed": 0}]),
                  ("29t open, one point           ", [{"points": [P(0, 0)], "closed": False}]),
                  ("29u open, 501 points          ", [{"points": [P(i, 0) for i in range(501)], "closed": False}]),
                  ("29v open, two equal points    ", [{"points": [P(5, 5), P(5, 5)], "closed": False}]),
                  ("29w open, c1 on the first point", [{"points": [P(0, 0, (10, 10), (20, 20)), P(100, 0)], "closed": False}]),
                  ("29x open, smooth first point  ", [{"points": [P(0, 0, smooth=True), P(50, 50), P(100, 0)], "closed": False}]),
                  ("29y open, smooth last point   ", [{"points": [P(0, 0), P(50, 50), P(100, 0, smooth=True)], "closed": False}]),
                  ("29z closed object, 2 points   ", [{"points": [P(0, 0), P(100, 0)], "closed": True}]),
                  ("29za points is not a list     ", [{"points": 5, "closed": False}])):
    d29(tag, cont)
r, sent = d29("29zb open, smooth inner point ", [{"points": [P(0, 0), P(100, 100, (0, 50), (50, 100), smooth=True), P(200, 0, (150, 100), (200, 50))], "closed": False}])
print("29zc  sent                     ->", sent)
d29("29zd open, two points, straight", [{"points": [P(0, 0), P(300, 0)], "closed": False}])
_closed_back = {"open": True, "name": "od", "drawn": False, "changed": True, "open_contours": [0],
                "reason": "the layer does not match the request: layer contour 0: closed reads True, an open contour was requested"}
d29("29ze FontLab closes it on attach", [OPEN_V], reply=_closed_back)
print("29zf  the change is counted     ->", fview(srv.finish_change_package()))
_d29 = srv.draw_path.__doc__ or ""
print("29zg docs                       -> open contours:", "OPEN contours" in _d29, "| object form:", '"closed": false' in _d29, "| listener 0.126:", "listener 0.126" in _d29,
      "| export untested:", "has not been tested" in _d29, "| signature:", _inspect.signature(srv.draw_path))
print("29zz version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post
srv._reset_change_tracking()

# ---------------------------------------------------------------- part 30: listener 0.127 / server 0.48, the layer of a new glyph ----
print("\n==== 30. listener 0.127 / server 0.48: create_glyph gives the new glyph its layer (live 612-619 are the reason; stubs only) ====")
ns["_create_glyph_layer"] = _real_create_glyph_layer
T30 = {"target": None, "calls": []}
_saved30 = {k: ns[k] for k in ("_modern_edit_target", "_guard_mark")}


def _target30(name, create_layer=False):
    T30["calls"].append(f"target({name}, create_layer={create_layer})")
    if isinstance(T30["target"], Exception):
        raise T30["target"]
    return T30["target"]


def _guard30(font, name, how, result):
    T30["calls"].append(f"guard({name}, {how})")
    result["synced_with_fontlab"] = True


ns["_modern_edit_target"], ns["_guard_mark"] = _target30, _guard30


class Pk30:
    def __init__(self, masters):
        self._m = masters
    @property
    def mastersCount(self):
        if isinstance(self._m, Exception):
            raise self._m
        return self._m


def ws30(pkg):
    fl.flWorkspace = types.SimpleNamespace(instance=lambda: types.SimpleNamespace(currentPackage=pkg))


def c30(tag, pkg, target=None):
    T30["target"], T30["calls"] = target, []
    ws30(pkg)
    print(tag, "->", ns["_create_glyph_layer"]("g30"), "| calls:", T30["calls"])


_made30 = ({"font": "F", "layer_created": "Regular", "layer_name_source": "other glyphs"}, None)
c30("30a one master, layer made", Pk30(1), _made30)
c30("30b one master, already has a layer", Pk30(1), ({"font": "F", "layer_created": None}, None))
c30("30c layer refused, with its reason", Pk30(1), (None, {"reason": "the glyphs of this font have different layer names"}))
c30("30d layer refused, no reason given", Pk30(1), (None, {}))
c30("30e the layer step raises", Pk30(1), RuntimeError("boom"))
c30("30f two masters: nothing attempted", Pk30(2), _made30)
c30("30g no master at all", Pk30(0), _made30)
c30("30h mastersCount raises", Pk30(RuntimeError("no count")), _made30)
c30("30i mastersCount is True, not a number", Pk30(True), _made30)
c30("30j mastersCount is text", Pk30("1"), _made30)
c30("30k no current package", None, _made30)
del fl.flWorkspace
T30["target"], T30["calls"] = _made30, []
print("30l no workspace ->", ns["_create_glyph_layer"]("g30"), "| calls:", T30["calls"])


class Font30(Font):
    def createGlyph(self, name):
        T30["calls"].append("createGlyph")
        return Font.createGlyph(self, name)
    def update(self):
        T30["calls"].append("font.update")


K30 = ("created", "layer_created", "layer_name_source", "layer_note", "synced_with_fontlab")


def r30(tag, font, masters, target, name="g30"):
    T30["target"], T30["calls"] = target, []
    ws30(Pk30(masters))
    CUR["font"] = font
    c, d = lpost("/glyph/create", {"name": name})
    print(tag, "->", c, short(d, K30), "| calls:", T30["calls"])


r30("30m route: order of the calls", Font30(), 1, _made30)
r30("30n route: layer refused, glyph still created", Font30(), 1, (None, {"reason": "no name"}))
r30("30o route: the layer step raises, glyph still created", Font30(), 1, RuntimeError("boom"))
r30("30p route: two masters, glyph still created", Font30(), 2, _made30)
r30("30q route: createGlyph did nothing, no layer step", Font30(noop=True), 1, _made30)
r30("30r route: name exists, no layer step", Font30(glyphs=[Gl("g30")]), 1, _made30)
for k, v in _saved30.items():
    ns[k] = v
ns["_create_glyph_layer"] = lambda name: {}
del fl.flWorkspace
CUR["font"] = None

srv._call_listener_post = fake_post
_warn30 = "not to use Glyph > Add Component"
K30S = ("created", "layer_created", "layer_name_source", "layer_note", "font_modified")


def s30(tag, **kw):
    listener_says(unicode=None, **kw)
    r = srv.create_new_glyph("zzcontrol")
    print(tag, "->", short(r, K30S), "| warns:", _warn30 in r["agent_instruction"], "| save rule kept:", "finish_changes ONCE" in r["agent_instruction"])


s30("30s layer made", layer_created="Regular", layer_name_source="other glyphs")
s30("30t no layer", layer_note="The glyph has no layer: this font has 2 masters, and a layer at creation was tested only with one.")
s30("30u older listener: neither field")
s30("30v layer_created is not text", layer_created=5, layer_name_source=7)
s30("30w empty texts", layer_created="", layer_note="")
s30("30x layer_note is not text", layer_note=9)
s30("30y layer_name_source missing", layer_created="Regular")
_d30 = srv.create_glyph.__doc__ or ""
print("30z docs -> layer at once:", "gets its editable layer at once" in _d30, "| layer_note:", "'layer_note' says why" in _d30, "| warns:", "Glyph > Add Component" in _d30)
srv._call_listener, srv._call_listener_post = wire_get, wire_post
srv._reset_change_tracking()

# ---------------------------------------------------------------- part 31: listener 0.128 / server 0.49, components are labelled ----
print("\n==== 31. listener 0.128 / server 0.49: a component says what it is (live 606-611 are the reason; stubs only) ====")


class Tr31:
    m11, m12, m21, m22, dx, dy = 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
    isIdentity = True


class Sd31:
    def __init__(self, glyph="base", layer="Regular", log=None):
        self._g, self._l, self._log = glyph, layer, log
    @property
    def componentGlyph(self):
        if isinstance(self._g, Exception): raise self._g
        return self._g
    def componentLayer(self):                     # a method, on purpose: the listener's _get calls a callable
        if isinstance(self._l, Exception): raise self._l
        return self._l


class Sh31:
    shapeType, contoursCount, isComposite, transform = "ShapeContours", 1, False, Tr31()
    def __init__(self, comp=True, data=None):
        self._c, self._d, self.asked = comp, data, []
    @property
    def isComponent(self):
        if isinstance(self._c, Exception): raise self._c
        return self._c
    @property
    def shapeData(self):
        self.asked.append("shapeData")
        if isinstance(self._d, Exception): raise self._d
        return self._d if self._d is not None else Sd31()


def l31(tag, shape):
    glyph = types.SimpleNamespace(name="g", activeLayer=types.SimpleNamespace(name="Regular", nodesCount=4, shapes=[shape]))
    out = {}
    ns["_describe_modern_glyph"](glyph, out)
    e = out["shapes"][0]
    print(tag, "->", {k: e[k] for k in ("is_component", "component_glyph", "component_layer", "component_error") if k in e}, "| asked:", shape.asked)


l31("31a listener: a component", Sh31())
l31("31b listener: a plain shape is not asked", Sh31(comp=False))
l31("31c listener: shapeData raises", Sh31(data=RuntimeError("boom")))
l31("31d listener: componentGlyph raises", Sh31(data=Sd31(glyph=RuntimeError("no name"))))
l31("31e listener: componentGlyph is not text", Sh31(data=Sd31(glyph=5)))
l31("31f listener: componentGlyph is empty", Sh31(data=Sd31(glyph="")))
l31("31g listener: componentLayer raises, the name stays", Sh31(data=Sd31(layer=RuntimeError("no layer"))))
l31("31h listener: componentLayer is empty", Sh31(data=Sd31(layer="")))
l31("31i listener: isComponent raises, nothing asked", Sh31(comp=RuntimeError("x")))
_N31 = kn([(100, 50), (400, 50), (400, 250), (100, 250)])
_M31 = {"lsb": 100.0, "rsb": -400.0, "advance": 0.0}


def s31(tag, shape_fields, margins=_M31, elements=None, matrix=None):
    reply = g26([_N31], margins, matrix=matrix, fontlab_ink_box=ink(50, 250))
    reply["elements"]["shapes"][0].update(shape_fields)
    for k in [k for k, v in shape_fields.items() if v is DEL31]:
        del reply["elements"]["shapes"][0][k]
    if elements is not None:
        reply["elements"] = elements
    s10_reset(); S9["get"]["/glyph/outline"] = reply
    r = srv.read_glyph_outline("A")
    e = (r.get("elements") or [{}])[0]
    notes = [n for n in r["notes"] if "component" in n]
    print(tag, "->", r["verification"]["status"], "|", {k: e[k] for k in ("is_component", "component_glyph", "component_layer", "description") if k in e}, "| notes:", notes)
    return r


DEL31 = object()
_OK31 = {"is_component": True, "component_glyph": "base", "component_layer": "Regular"}
s31("31j component, source and layer", _OK31)
s31("31k plain shape", {"is_component": False})
s31("31l name not read, reason given", {"is_component": True, "component_error": "RuntimeError: boom"})
s31("31m name not read, no reason (older listener)", {"is_component": True})
s31("31n flag could not be read", {"is_component": "<error: x>"})
s31("31o flag is None", {"is_component": None})
s31("31p no flag at all", {"is_component": DEL31})
s31("31q name is not text", {"is_component": True, "component_glyph": 5})
s31("31qa reason is not text", {"is_component": True, "component_error": 7})
s31("31r no layer name", {"is_component": True, "component_glyph": "base", "component_layer": ""})
_off31 = {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 50.0, "dy": 30.0}
_inkoff31 = {"lsb": 150.0, "rsb": -450.0, "advance": 0.0}
reply31 = g26([_N31], _inkoff31, matrix=_off31, fontlab_ink_box=ink(80, 280)); reply31["elements"]["shapes"][0].update(_OK31)
s10_reset(); S9["get"]["/glyph/outline"] = reply31
r31 = srv.read_glyph_outline("A")
print("31s component with an offset ->", r31["verification"]["status"], "| first node:", r31["contours"][0]["node_list"][0]["x"], r31["contours"][0]["node_list"][0]["y"],
      "| description:", r31["elements"][0]["description"], "| notes:", sum("component of" in n for n in r31["notes"]))
s31("31t element list does not map", {"contours": 2})
s31("31u element list unavailable", {}, elements={"available": False, "error": "no list"})
print("31v -0 in a description ->", srv._describe_matrix((1.0, 0.0, 0.0, 1.0, -0.0, 30.0)), "|", srv._describe_matrix((1.0, 0.0, 0.0, 1.0, 40.0, -0.0)), "|", srv._describe_matrix((2.0, 0.0, 0.0, 1.0, -100.0, 30.0)))
_g31, _p31 = srv.get_glyph_outline.__doc__ or "", srv.draw_polygon.__doc__ or ""
print("31w docs -> outline names is_component:", "is_component" in _g31, "| names source:", "component_glyph" in _g31, "| old claim only for legacy:", "On the older legacy route a composite glyph" in _g31,
      "| draw_polygon corrected:", "A glyph made by create_glyph has no editable layer" not in _p31, "| still explains layer_created:", "layer_created" in _p31)
print("31z version / MIN_LISTENER_VERSION:", srv.SERVER_VERSION, srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post
srv._reset_change_tracking()

# ---------------------------------------------------------------- part 32: listener 0.130 / server 0.50, boxes per component ----
print("\n==== 32. listener 0.130 / server 0.50: a box per component, an accent inside its base, a composite behind its source (live 633-650 are the reason; stubs only) ====")


class Box32:
    def __init__(self, left, right, top, bottom):
        self.v = (left, right, top, bottom)
    def left(self): return self.v[0]
    def right(self): return self.v[1]
    def top(self): return self.v[2]
    def bottom(self): return self.v[3]
    def width(self): return self.v[1] - self.v[0]
    def height(self): return self.v[3] - self.v[2]


SPY32 = {"forbidden": [], "ink": [], "source": []}


class Spy32:
    def __getattr__(self, a):
        SPY32["forbidden"].append(a); raise AttributeError(a)


class Sh32(Spy32):
    def __init__(self, tag, box):
        self.__dict__.update(tag=tag, box=box)
    def inkBox(self, *a):
        SPY32["ink"].append((self.tag, a))
        if isinstance(self.box, Exception): raise self.box
        return self.box


class Src32(Spy32):
    def __init__(self, name, box):
        self.__dict__.update(name=name, box=box)
    def inkBox(self, *a):
        SPY32["source"].append((self.name, a))
        if isinstance(self.box, Exception): raise self.box
        return self.box


class Lay32(Spy32):
    def __init__(self, shapes):
        self.__dict__["_s"] = shapes
    @property
    def shapes(self):
        if isinstance(self._s, Exception): raise self._s
        return self._s
    def inkBox(self):                             # the glyph's own layer: the proven layer.inkBox() of every outline read
        return Box32(50, 650, 0, 880)


class W32(Spy32):
    def __init__(self, layer):
        self.__dict__["activeLayer"] = layer


def C32(glyph="acc", layer="Regular"):
    return {"is_component": True, "component_glyph": glyph, "component_layer": layer}


def b32(d):
    return d.get("error") if "error" in d else (d["left"], d["right"], d["top"], d["bottom"])


_saved32 = {k: ns[k] for k in ("_find_glyph", "_modern_wrapper", "_open_font", "_tryshape_modern_state", "_read_modern_outline", "_describe_modern_glyph")}


def src32():
    return {"base": Src32("Regular", Box32(50, 650, 0, 700)), "acc": Src32("Regular", Box32(70, 330, 780, 880))}


def patch32(sources, wrap_raises=False):
    SPY32.update(forbidden=[], ink=[], source=[])
    def wrapper(g, f):
        if wrap_raises: raise RuntimeError("wrap boom")
        return W32(sources[g[2:]]), "cached"
    ns["_find_glyph"] = lambda f, n: ("G:" + n) if n in sources else None
    ns["_modern_wrapper"] = wrapper


def a32(tag, entries, shapes, sources=None, wrap_raises=False):
    patch32(src32() if sources is None else sources, wrap_raises)
    ns["_add_component_boxes"](W32(Lay32(shapes)), object(), entries)
    print(tag, "->", [{k: b32(e[k]) for k in ("ink_box", "source_ink_box") if k in e} for e in entries], "| inkBox", SPY32["ink"], "| source", SPY32["source"], "| forbidden", SPY32["forbidden"])


_A32 = Box32(220, 480, 780, 880)
_B32 = Box32(50, 650, 0, 700)
a32("32a two components", [C32("base"), C32()], [Sh32(0, _B32), Sh32(1, _A32)])
a32("32b a plain element gets no key", [{"is_component": False}, C32()], [Sh32(0, _B32), Sh32(1, _A32)])
a32("32c no component: nothing is asked", [{"is_component": False}], RuntimeError("must not be read"))
a32("32d flag could not be read: no key", [{"is_component": "<error: x>"}], [Sh32(0, _B32)])
a32("32e inkBox raises, the source is still read", [C32()], [Sh32(0, RuntimeError("ink boom"))])
a32("32f inkBox returns None", [C32()], [Sh32(0, None)])
a32("32g layer.shapes raises", [C32()], RuntimeError("shapes boom"))
a32("32h layer.shapes is not a list", [C32()], (Sh32(0, _A32),))
a32("32i layer.shapes has another length", [C32(), {"is_component": False}], [Sh32(0, _A32)])
a32("32j 21 elements", [C32()] + [{"is_component": False}] * 20, [Sh32(i, _A32) for i in range(21)])
a32("32k 20 elements", [C32()] + [{"is_component": False}] * 19, [Sh32(i, _A32) for i in range(20)])
a32("32l the source name is missing", [{"is_component": True, "component_layer": "Regular"}], [Sh32(0, _A32)])
a32("32m the source glyph is gone", [C32("nope")], [Sh32(0, _A32)])
a32("32n the source's wrapper raises", [C32()], [Sh32(0, _A32)], wrap_raises=True)
a32("32o the source has no active layer", [C32()], [Sh32(0, _A32)], sources={"acc": None})
a32("32p another layer name", [C32(layer="Bold")], [Sh32(0, _A32)])
a32("32q the source's inkBox raises", [C32()], [Sh32(0, _A32)], sources={"acc": Src32("Regular", RuntimeError("src boom"))})
a32("32r one source used twice: read once", [C32(), C32()], [Sh32(0, _A32), Sh32(1, _A32)])
patch32(src32())
ns["_open_font"] = lambda: object()
ns["_tryshape_modern_state"] = lambda w: ({"nodes": 4, "layer_name": "Regular", "components": 0, "shapes": 1}, w.activeLayer)
ns["_read_modern_outline"] = lambda name: {"available": True, "node_count": 4, "contours": []}
ns["_describe_modern_glyph"] = lambda w, out: out.update(layer_name="Regular", shapes=[C32()])
_mw32 = ns["_modern_wrapper"]
ns["_modern_wrapper"] = lambda g, f: (W32(Lay32([Sh32(0, _A32)])), "cached") if g == "G:acc" and not SPY32.get("target") and not SPY32.update(target=True) else _mw32(g, f)
_o32 = ns["_modern_only_outline"]("acc", "body")
print("32s the outline route adds the boxes ->", {k: b32(_o32["elements"]["shapes"][0][k]) for k in ("ink_box", "source_ink_box")}, "| forbidden", SPY32["forbidden"])
ns["_describe_modern_glyph"] = lambda w, out: out.update(shapes_error="no list")
SPY32.pop("target", None)
_o32 = ns["_modern_only_outline"]("acc", "body")
print("32t no element list: no boxes, the error stays ->", _o32["elements"])
SPY32.pop("target", None)
for k, v in _saved32.items(): ns[k] = v
_lsrc32 = open(find("glyphbridge_fontlab_mcp_listener.py"), encoding="utf-8").read()
_body32 = "\n".join(l for l in _lsrc32[_lsrc32.index("_COMPONENT_BOX_MAX = 20"):_lsrc32.index("def _modern_only_outline(")].split("\n") if not l.lstrip().startswith("#"))
print("32u static scan of the new listener code:", len(_body32) > 1500, "| forbidden call syntax:",
      re.findall(r"\.(?:update|save\w*|export\w*|close|release|remove\w*|bindDependencies|resetInkBox|changed|applyTransform|transform|setProperty\w*)\s*\(", _body32),
      "| subscripts of native objects other than a checked list:", [m for m in re.findall(r"\b(\w+)\[", _body32) if m in ("layer", "glyph", "shape", "w")])


def sq32(left, right, bottom, top):
    return kn([(left, bottom), (right, bottom), (right, top), (left, top)])


def rect32(left, right, bottom, top):
    return {"type": "QRectF", "left": float(left), "right": float(right), "top": float(bottom), "bottom": float(top), "width": float(right - left), "height": float(top - bottom)}


def mx32(dx=0.0, dy=0.0, m11=1.0, m12=0.0):
    return {"m11": m11, "m12": m12, "m21": 0.0, "m22": 1.0, "dx": float(dx), "dy": float(dy)}


_RB32, _RA32 = rect32(50, 650, 0, 700), rect32(220, 480, 780, 880)
_SA32 = rect32(70, 330, 780, 880)


def el32(name, matrix, **kw):
    return dict({"shape_type": "contours", "contours": 1, "is_component": True, "is_composite": True, "component_glyph": name, "component_layer": "Regular", "matrix": matrix}, **kw)


def base32(**kw):
    return el32("base", mx32(), ink_box=_RB32, source_ink_box=_RB32, **kw)


_M32 = {"lsb": 50.0, "rsb": 50.0, "advance": 700.0}


def reply32(accent, margins=_M32, extra=None):
    contours = [sq32(50, 650, 0, 700), sq32(70, 330, 780, 880)] + ([e[0] for e in extra] if extra else [])
    reply = g26(contours, margins, fontlab_ink_box=ink(0, 880))
    reply["elements"]["shapes"] = [base32(), accent] + ([e[1] for e in extra] if extra else [])
    reply["shape_count"] = len(reply["elements"]["shapes"])
    return reply


def s32(tag, reply):
    s10_reset(); S9["get"]["/glyph/outline"] = reply
    r = srv.read_glyph_outline("A")
    v = r["verification"]
    print(tag, "->", v["status"], "| element_boxes_checked", v.get("element_boxes_checked", "absent"), "| note", v.get("element_boxes_note", "absent"), "| reason", (v.get("reason") or "none")[:230],
          "| in step", [e.get("source_in_step", "absent") for e in r.get("elements", [])], "| step notes", [e["source_in_step_note"] for e in r.get("elements", []) if "source_in_step_note" in e],
          "| instruction", (r.get("agent_instruction") or "none")[:240])
    return r


s32("32v accent inside its base, in step", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=_SA32)))
s32("32w sides in Qt's y-down order are ordered by value", reply32(el32("acc", mx32(150), ink_box=dict(_RA32, top=880.0, bottom=780.0), source_ink_box=_SA32)))
s32("32x older listener: no boxes, as before", reply32(el32("acc", mx32(150))))
s32("32y element box is an error", reply32(el32("acc", mx32(150), ink_box={"error": "ink boom"}, source_ink_box=_SA32)))
s32("32z element box is malformed", reply32(el32("acc", mx32(150), ink_box={"left": "x"}, source_ink_box=_SA32)))
s32("32za element box elsewhere", reply32(el32("acc", mx32(150), ink_box=rect32(225, 485, 780, 880), source_ink_box=rect32(75, 335, 780, 880))))
s32("32zb element box fits the untransformed nodes", reply32(el32("acc", mx32(150), ink_box=_SA32, source_ink_box=rect32(-80, 180, 780, 880))))
s32("32zba an offset too small to tell the readings apart", reply32(el32("acc", mx32(0.01), ink_box=_SA32, source_ink_box=_SA32)))
s32("32zc source box is an error, boxes still settle it", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box={"error": "src boom"})))
s32("32zd only a source box arrived", reply32(el32("acc", mx32(150), source_ink_box=_SA32)))
s32("32ze behind its source, accent inside the base", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=rect32(90, 350, 780, 880))))
s32("32zf behind vertically only", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=rect32(70, 330, 790, 890))))
s32("32zg just inside the tolerance", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=rect32(70.04, 330.04, 780, 880))))
s32("32zh just outside the tolerance", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=rect32(70.06, 330.06, 780, 880))))
_P32 = {"lsb": 50.0, "rsb": 20.0, "advance": 700.0}
s32("32zi accent past its base, in step", reply32(el32("acc", mx32(350), ink_box=rect32(420, 680, 780, 880), source_ink_box=_SA32), margins=_P32))
s32("32zj accent past its base, behind its source", reply32(el32("acc", mx32(350), ink_box=rect32(420, 680, 780, 880), source_ink_box=rect32(90, 350, 780, 880)), margins=_P32))
s32("32zk scaled component inside its base", reply32(el32("acc", mx32(150, m11=0.5), ink_box=rect32(185, 315, 780, 880), source_ink_box=_SA32)))
s32("32zl slanted component", reply32(el32("acc", mx32(150, m12=0.1), ink_box=_RA32, source_ink_box=_SA32)))
_plain32 = {"shape_type": "contours", "contours": 1, "is_component": False, "is_composite": False, "matrix": mx32(100)}
s32("32zm a moved plain element beside a moved component", reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=_SA32), extra=[(sq32(100, 200, 300, 400), _plain32)]))
s32("32zn only a moved plain element", reply32(dict(_plain32, matrix=mx32(150), is_component=False)))
_r32 = reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=rect32(90, 350, 780, 880))); _r32["modern_outline"]["margins"] = {"lsb": 40.0, "rsb": 50.0, "advance": 700.0}
s32("32zo behind its source and an earlier reason", _r32)
_r32 = reply32(el32("acc", mx32(150), ink_box=_RA32, source_ink_box=_SA32)); _r32["elements"]["shapes"][1]["contours"] = 2
s32("32zp element list does not map: no check", _r32)
_r32 = reply32(el32("acc", mx32(150, 20), ink_box=rect32(220, 480, 800, 900), source_ink_box=_SA32)); _r32["fontlab_ink_box"] = ink(0, 900)
s32("32zpa a vertical offset, in step", _r32)
s32("32zpb a plain element carrying boxes gets no verdict", reply32(dict(_plain32, matrix=mx32(0.0), ink_box=_SA32, source_ink_box=rect32(0, 10, 0, 10))))
s32("32zpc a box with an error beside its numbers", reply32(el32("acc", mx32(150), ink_box=dict(_RA32, error="partial read"), source_ink_box=_SA32)))
_g32, _s32 = srv.get_glyph_outline.__doc__ or "", srv.set_glyph_sidebearings.__doc__ or ""
print("32zq docs -> outline names source_in_step:", "source_in_step" in _g32, "| element_boxes_checked:", "element_boxes_checked" in _g32, "| sidebearings warns:", "may not follow" in _s32, "component_note" in _s32)
print("32zr listener / server versions:", ns["VERSION"], srv.SERVER_VERSION, "| MIN_LISTENER_VERSION:", srv.MIN_LISTENER_VERSION)
srv._call_listener, srv._call_listener_post = wire_get, wire_post
srv._reset_change_tracking()

# ---------------------------------------------------------------- part 33: server 0.51, the changed mark in a write reply ----
print("\n==== 33. server 0.51: fontlab_changed_mark and save_question_note (stubs only) ====")


def r33(data, modified=True):
    res = {}
    srv._add_guard_fields(res, data)
    srv._mark_modified(res, modified)
    return {k: res[k] for k in ("fontlab_changed_mark", "save_question_note", "font_modified") if k in res}


M33 = "fontlab_changed_mark"
print("33a confirmed                    ->", r33({M33: {"called": True, "glyph_has_changes": True}}))
print("33b not called, with its reason  ->", r33({M33: {"called": False, "reason": "the width did not change"}}))
print("33c the call failed              ->", r33({M33: {"called": True, "call_error": "RuntimeError: x", "glyph_has_changes": True}}))
print("33d hasChanges false             ->", r33({M33: {"called": True, "glyph_has_changes": False}}))
print("33e hasChanges unknown           ->", r33({M33: {"called": True, "glyph_has_changes": "unknown"}}))
print("33f an older listener: no field  ->", r33({}))
print("33g no real change, no note      ->", r33({M33: {"called": False, "reason": "same value"}}, modified=False))
print("33h not a dict                   ->", r33({M33: "yes"}))
print("33i called is not a bool         ->", r33({M33: {"called": 1, "glyph_has_changes": True}}))
print("33j hasChanges 1 is not passed on ->", r33({M33: {"called": True, "glyph_has_changes": 1}}))
print("33k unknown keys are not passed on ->", r33({M33: {"called": True, "glyph_has_changes": True, "extra": "x", "reason": 5}}))
print("33ka not called, whatever else it says ->", r33({M33: {"called": False, "glyph_has_changes": True}}))
_w33 = srv._write_post
srv._write_post = lambda path, payload, timeout=None: {"open": True, "set": True, "before": 400.0, "after": 500.0, M33: {"called": True, "glyph_has_changes": True}, "synced_with_fontlab": True}
_r33 = srv.write_glyph_width("g", 500)
print("33l write_glyph_width carries it :", _r33.get(M33), "| note", "save_question_note" in _r33, "| modified", _r33.get("font_modified"))
srv._write_post = lambda path, payload, timeout=None: {"open": True, "set": True, "before": 0, "after": 500.0, "route": "legacy_empty_glyph", M33: {"called": False, "reason": "the legacy width route is used only for a glyph with no modern layer"}}
_r33 = srv.write_glyph_width("g", 500)
print("33m the legacy route gets the note:", _r33.get(M33), "| note", _r33.get("save_question_note"))
print("33o via_glyph is passed on        ->", r33({M33: {"called": True, "glyph_has_changes": True, "via_glyph": "a"}}))
print("33p via_glyph not text is dropped ->", r33({M33: {"called": True, "glyph_has_changes": True, "via_glyph": 5}}))
_d33 = {"open": True, "deleted": True, "before_count": 3, "after_count": 2}
srv._write_post = lambda path, payload, timeout=None: dict(_d33, **{M33: {"called": True, "glyph_has_changes": True, "via_glyph": "a"}})
_r33 = srv.delete_existing_glyph("b")
print("33q a delete carries the mark     :", _r33.get(M33), "| note", "save_question_note" in _r33, "| modified", _r33.get("font_modified"))
srv._write_post = lambda path, payload, timeout=None: dict(_d33, **{M33: {"called": False, "reason": "no glyph other than .notdef is left to notify"}})
_r33 = srv.delete_existing_glyph("b")
print("33r a delete it could not mark    :", _r33.get(M33), "| note", "save_question_note" in _r33)
srv._write_post = lambda path, payload, timeout=None: dict(_d33)
_r33 = srv.delete_existing_glyph("b")
print("33s an older listener: no field   :", _r33.get(M33), "| note", "save_question_note" in _r33)
srv._write_post = _w33
print("--- server 0.54: set_kerning carries the mark and changes point (2) of its instruction (faked listener replies)")
_keep33 = (srv._call_listener, srv._call_listener_post)
srv._call_listener, srv._call_listener_post = _k27_get, _k27_post
def k33(label, mark, changed=True, version="0.134"):
    extra = {} if mark is None else {M33: mark}
    r = k27(setreply([okset("A", "B", -60, changed=changed)], **extra), version=version, pairs=[["A", "B", -60]])
    ai = r["agent_instruction"]
    print(label, ":", r.get(M33, "<no field>"), "| note", "save_question_note" in r, "| modified", r.get("font_modified"), "| old warning", srv._KERN_NOT_MARKED in ai, "| marked text", srv._KERN_MARKED in ai, "| placeholder left", "{save}" in ai)
k33("33t marked                       ", {"called": True, "glyph_has_changes": True, "via_glyph": "A"})
k33("33u hasChanges false, still marked", {"called": True, "glyph_has_changes": False, "via_glyph": "A"})
k33("33v an older listener: no field  ", None, version="0.133")
k33("33w not called, with its reason  ", {"called": False, "reason": "none of the 2 glyphs tried could be notified (x)"})
k33("33x the call failed              ", {"called": True, "call_error": "RuntimeError: x", "glyph_has_changes": "unknown", "via_glyph": "A"})
k33("33y same value, no call          ", {"called": False, "reason": "no kerning entry is known to have changed"}, changed=False)
k33("33z not a dict                   ", "yes")
k33("33za called is not a bool        ", {"called": 1, "via_glyph": "A"})
srv._call_listener, srv._call_listener_post = _keep33
print("33zb the marked text claims no icon and no question:", not any(t in srv._KERN_MARKED.lower() for t in ("blue", "will ask", "asks", "icon")), "| says it is lost unsaved:", "closed without saving" in srv._KERN_MARKED)
print("33zc the docstring names both cases:", all(t in (srv.set_kerning.__doc__ or "") for t in ("listener 0.134", "fontlab_changed_mark", "save_question_note", "asks no save question")))
print("--- server 0.55: the icon note (policy of 2026-11-10) and the sentence for a request that changed nothing (faked listener replies)")
_keep33b = (srv._call_listener, srv._call_listener_post)
srv._call_listener, srv._call_listener_post = _k27_get, _k27_post
def k34(label, mark, rows=None, version="0.134"):
    extra = {} if mark is None else {M33: mark}
    rows = rows or [okset("A", "B", -60)]
    r = k27(setreply(rows, **extra), version=version, pairs=[[e["left"], e["right"], e["requested"]] for e in rows])
    ai = r["agent_instruction"]
    print(label, ":", "(2)", "marked" if srv._KERN_MARKED in ai else "not-marked" if srv._KERN_NOT_MARKED in ai else "no-change" if srv._KERN_NO_CHANGE in ai else "NONE",
          "| icon note", srv._KERN_ICON_LAG in ai, "| save note", "save_question_note" in r, "| modified", r.get("font_modified"), "| placeholder left", "{" in ai)
_m34 = {"called": True, "glyph_has_changes": True, "via_glyph": "A"}
_lag34 = srv._ICON_MAY_LAG_KERNING; srv._ICON_MAY_LAG_KERNING = True        # v0.57: the shipped switch is off (749-753); the note's path stays tested with it on
k34("34a marked: the icon note          ", _m34)
srv._ICON_MAY_LAG_KERNING = False
k34("34b marked, the switch is off      ", _m34); srv._ICON_MAY_LAG_KERNING = True
k34("34c changed, not called            ", {"called": False, "reason": "none of the 2 glyphs tried could be notified (x)"})
k34("34d changed, the call failed       ", {"called": True, "call_error": "RuntimeError: x", "via_glyph": "A"})
k34("34e changed, an older listener     ", None, version="0.133")
k34("34f same value, no call            ", {"called": False, "reason": "no kerning entry is known to have changed"}, rows=[okset("A", "B", -60, changed=False)])
k34("34g same value, an older listener  ", None, rows=[okset("A", "B", -60, changed=False)], version="0.133")
k34("34h one changed of two, marked     ", _m34, rows=[okset("A", "B", -60, changed=False), okset("T", "o", -40)])
k34("34i one changed of two, not called ", {"called": False, "reason": "x"}, rows=[okset("A", "B", -60, changed=False), okset("T", "o", -40)])
srv._ICON_MAY_LAG_KERNING = _lag34
k34("34l as shipped: marked, no icon note", _m34)
srv._call_listener, srv._call_listener_post = _keep33b
_t34 = srv._KERN_ICON_LAG.lower()
print("34j the note says may, not will   :", "may stay dark" in _t34, "can make" in _t34, not any(t in _t34 for t in ("will turn", "will ask", "always")), "| names the title:", "font's title" in _t34, "| not a failure:", "does not mean the change failed" in _t34, "| once per package:", "once per package" in _t34)
print("34k the no-change text            :", "changed no entry" in srv._KERN_NO_CHANGE, "| shipped switch off:", _lag34 is False, "| docstring no longer names the title:", "font's title" not in (srv.set_kerning.__doc__ or ""))
print("--- server 0.56: fontlab_panel_refresh and point (1) of the set_kerning instruction (faked listener replies)")
_keep35 = (srv._call_listener, srv._call_listener_post)
srv._call_listener, srv._call_listener_post = _k27_get, _k27_post
P35 = "fontlab_panel_refresh"
def k35(label, panel, rows=None, version="0.136"):
    extra = {M33: {"called": True, "glyph_has_changes": True, "via_glyph": "A"}}
    if panel is not None: extra[P35] = panel
    rows = rows or [okset("A", "B", -60)]
    r = k27(setreply(rows, **extra), version=version, pairs=[[e["left"], e["right"], e["requested"]] for e in rows])
    ai = r["agent_instruction"]
    print(label, ":", r.get(P35, "<no field>"), "| (1)", "asked" if srv._KERN_PANEL_ASKED in ai else "stale" if srv._KERN_PANEL_STALE in ai else "no-change" if srv._KERN_PANEL_NO_CHANGE in ai else "NONE", "| placeholder left", "{" in ai, "| modified", r.get("font_modified"))
k35("35a the refresh was made          ", {"called": True})
k35("35b an older listener: no field   ", None, version="0.135")
k35("35c not called, with its reason   ", {"called": False, "reason": "the package's fgId is None, not a plain number that fits a uint"})
k35("35d the call failed               ", {"called": True, "call_error": "RuntimeError: x"})
k35("35e same value, no call           ", {"called": False, "reason": "no kerning entry is known to have changed"}, rows=[okset("A", "B", -60, changed=False)])
k35("35f not a dict                    ", "yes")
k35("35g called is not a bool          ", {"called": 1})
k35("35h a reason that is not text     ", {"called": False, "reason": 5})
k35("35i an empty call_error           ", {"called": True, "call_error": ""})
k35("35j an unknown key is dropped     ", {"called": True, "panel_shows_it": True})
k35("35m same value, an older listener ", None, rows=[okset("A", "B", -60, changed=False)], version="0.135")
k35("35n a call reported, nothing changed", {"called": True}, rows=[okset("A", "B", -60, changed=False)])
k35("35o one changed of two, not called", {"called": False, "reason": "x"}, rows=[okset("A", "B", -60, changed=False), okset("T", "o", -40)])
srv._call_listener, srv._call_listener_post = _keep35
_t35 = srv._KERN_PANEL_ASKED.lower()
print("35k the asked text claims nothing :", not any(t in _t35 for t in ("now shows", "now lists", "is listed", "will show", "will list")), "| names the field:", P35 in _t35, "| keeps the fallback:", "another open font and back" in _t35, "saving and reopening" in _t35)
print("35p the no-change text            :", "already set" in srv._KERN_PANEL_NO_CHANGE, "was not asked" in srv._KERN_PANEL_NO_CHANGE, "| claims nothing about the panel's state:", not any(t in srv._KERN_PANEL_NO_CHANGE.lower() for t in ("does not show", "shows", "lists")))
print("35l the docstring                 :", all(t in (srv.set_kerning.__doc__ or "") for t in ("listener 0.136", P35, "another open font and back")))
print("33n the note claims no icon and no question:", not any(t in srv._SAVE_QUESTION_NOTE.lower() for t in ("blue", "will ask", "asks to save")), "| kerning warning kept:", "closing the font asks no save question" in srv._SET_KERNING_INSTRUCTION if hasattr(srv, "_SET_KERNING_INSTRUCTION") else "asks no save question" in open(find("glyphbridge_mcp_server.py"), encoding="utf-8").read())
srv._reset_change_tracking()
