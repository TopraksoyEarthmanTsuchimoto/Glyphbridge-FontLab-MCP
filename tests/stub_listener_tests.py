"""Stub-FontLab test harness for glyphbridge_fontlab_mcp_listener.py (stdlib only, no FontLab needed).
It fakes the `fontlab` and `PythonQt` modules, executes the listener source with its start() call removed,
and calls every route through the listener's own _route(). The checks are PRINT based: compare the output
with expected_listener_output.txt (run_all.py does that). Numbered lines (1..80) are the individual cases."""
import sys, types, json
import os
HERE = os.path.dirname(os.path.abspath(__file__))
def _find(name):
    """Locate a project file: next to this script, one folder up, or in the current folder."""
    for d in (os.path.join(HERE, ".."), HERE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit("cannot find " + name + ": put the tests folder inside the project folder (next to it), or run from there")
fl = types.ModuleType("fontlab")
class Node:
    x=10.0; y=20.0
    point=type('P',(),{'x':11.0,'y':21.0,'move':lambda self:0,'left':lambda self:10.0,'right':lambda self:20.0,'top':lambda self:30.0,'bottom':lambda self:5.0,'width':lambda self:10.0,'ll':type('P',(),{'x':10.0,'y':5.0})()})()
    def move(self): pass
    def isOn(self): return True
    def isOff(self): return False
    def isCurve(self): return False
    def setG2(self,v=True): raise SystemExit('SETTER CALLED')
class Layer:
    name="L"
    matrix=type('M',(),{'dx':1.0})()
    reference=type('R',(),{'x':0.0,'y':0.0})()
    def countNodes(self): return 3
    def boundingBox(self,m): return type('Rect',(),{'left':lambda self:10.0,'right':lambda self:20.0,'top':lambda self:30.0,'bottom':lambda self:5.0,'width':lambda self:10.0,'height':25.0,'ll':type('P',(),{'x':10.0,'y':5.0})(),'ur':type('P',(),{'x':20.0,'y':30.0})()})()
    def countContours(self): return 1
    def countShapes(self): return 1
    def __len__(self): return 1
    def findNode(self,i):
        if i>=3: return None
        n=Node(); n.kind=['Move','Off','On'][i]; n.smooth=(i==0); return n
class Glyph:
    components=[1,2]
    def draw(self,pen):
        pen.moveTo((1,2)); pen.lineTo((3,4)); pen.closePath(); return None
    leftMargin=1.5; rightMargin=2.5
    name="A"; width=500.0; unicode=65
    _l=Layer()
    @property
    def layer(self): return self._l
    @property
    def bodyLayer(self): return self._l
    bodyLayerStrict=_l
    activeLayer=_l
class Font:
    glyphs=[Glyph(), type('E',(),{'name':'empty','layer':None,'bodyLayer':None})(), type('G2',(),{'name':'B','layer':1,'bodyLayer':type('L2',(Layer,),{'countNodes':lambda self:0})()})()]; path="x"
    info=types.SimpleNamespace(familyName="F",styleName="R",postscriptFontName="",postscriptFullName="",unitsPerEm=1000,ascender=800,descender=-200,capHeight=700,xHeight=500,openTypeOS2WeightClass=400)
fl.CurrentFont=lambda: Font()
pq=types.ModuleType("PythonQt"); qc=types.ModuleType("QtCore"); pq.QtCore=qc
qg=types.ModuleType("PythonQt.QtGui"); qg.QMessageBox=object
sys.modules.update({"fontlab":fl,"PythonQt":pq,"PythonQt.QtCore":qc,"PythonQt.QtGui":qg})
src=open(_find("glyphbridge_fontlab_mcp_listener.py"),encoding="utf-8").read().replace("\nstart()\n","\n")
ns={}; exec(compile(src,"l","exec"),ns)
# Listener 0.120 (F1) answers a glyph with modern nodes from the modern layer only. The cases before the v0.120 block test the
# legacy reader (still used for glyphs without modern nodes and for modern=no), so the switch is off until that block.
ns["_MODERN_FIRST"] = False
def call(path):
    r=ns["_route"]("GET",path); h,_,b=r.partition(b"\r\n\r\n")
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
for p in ["/health","/version","/font/current","/font/glyphs","/glyph/width?name=A","/glyph/unicode?name=A","/debug/layerstats?name=A",
 "/debug/findnode?name=A&index=1",
 "/debug/findnode?name=A&index=1&stage=dir",
 "/debug/findnode?name=A&index=1&stage=read&attrs=x,y,move,zzz",
 "/debug/findnode?name=A&index=3",
 "/debug/findnode?name=A&index=abc",
 "/debug/findnode?name=Q&index=0",
 "/debug/findnode?name=A&index=0&stage=bogus"]:
    print(p, call(p))
print(call("/glyph/nodes?name=A"))
print(call("/glyph/nodes?name=A&attrs=move,zzz"))
print(call("/glyph/nodes?name=Q"))

print(call("/debug/findnode?name=A&index=1&stage=call&attrs=isOn,isOff,isCurve,isCurveOff,setG2,bogus"))
print(call("/glyph/nodes?name=A&calls=isOn,setG2"))

print(call("/font/nonempty"))
print(call("/glyph/outline?name=A"))
print(call("/glyph/outline?name=Q"))

print(call("/debug/objdir?name=A&target=glyph&stage=dir"))
print(call("/debug/objdir?name=A&target=layer&stage=dir"))
print(call("/debug/objdir?name=A&target=glayer&stage=read&attrs=name,countNodes,zzz"))
print(call("/debug/objdir?name=A&target=bogus"))
print(call("/debug/objdir?name=A&target=layer&stage=bogus"))

print(call("/debug/objdir?name=A&target=layermatrix&stage=dir"))
print(call("/debug/objdir?name=A&target=layermatrix&stage=read&attrs=dx"))
print(call("/debug/objdir?name=A&target=strictlayer&stage=dir"))

for r in ("body","active","strict","glayer","nope"):
    c,d=call("/glyph/outline?name=A&layer="+r); print(r,c,d.get("layer_route"),d.get("layer_name"),d.get("node_count"),d.get("error"))
print(call("/glyph/outline?name=A")[1]["layer_route"])

print(call("/debug/findnode?name=A&index=1&stage=point"))
print(call("/debug/findnode?name=A&index=1&stage=point&attrs=x,zzz"))

print(call("/debug/objdir?name=A&target=layerref&stage=dir"))
print(call("/debug/objdir?name=A&target=layerref&stage=read&attrs=x,y"))
print(call("/debug/objdir?name=A&target=glyph&stage=read&attrs=components,name,layers"))

print(call("/debug/layerbbox?name=A&stage=call"))
print(call("/debug/layerbbox?name=A&stage=dir"))
print(call("/debug/layerbbox?name=A&stage=read&attrs=x,width,move,zzz"))
print(call("/debug/layerbbox?name=A&stage=bogus"))
print(call("/debug/layerbbox?name=Q"))

print(call("/debug/layerbbox?name=A&stage=measure"))

c,d=call("/glyph/outline?name=A"); print(c,{k:d.get(k) for k in ("fontlab_bbox","margins","component_count","node_count")})

print(call("/debug/drawpen?name=A&limit=5"))
print(call("/debug/drawpen?name=Q"))
print(call("/debug/drawpen?name=A&limit=x"))
print(call("/debug/fldir?contains=current,zzz"))
c,d=call("/glyph/outline?name=A"); print("shape_count in outline:",d.get("shape_count"))

import sys as _s
_fm=_s.modules["fontlab"]
class flShape:
    """flShape(glyph) -> a shape"""
    transform=1
    def move(self): pass
_fm.flShape=flShape
print(call("/debug/classdir?name=flShape&doc=40"))
print(call("/debug/classdir?name=nope"))
print(call("/debug/classdir?name=__import__"))
print(call("/debug/classdir?name=a.b"))
print(call("/debug/classdir?name=flShape&doc=x"))
# v0.69: members= returns docstrings only
print(call("/debug/classdir?name=flShape&doc=40&members=move,transform,nope,_x,a.b"))
print(call("/debug/classdir?name=flShape&doc=40&members=" + ",".join("m%d" % i for i in range(13))))

# ---------------- /debug/walk tests ----------------
class FlTransform:
    def getProperties(self): return ["m11","m22","dx","dy"]
    def scale(self,a,b): raise SystemExit("MUTATOR scale() CALLED")
class FlShape:
    name="Shape 1"; shapeType=1; transform=FlTransform()
    def contoursCount(self): return 2
    def remove(self): raise SystemExit("MUTATOR remove() CALLED")
class NativeLike:
    def __getitem__(self,i): raise SystemExit("NATIVE [] INDEXING CALLED")
class FlLayer(NativeLike):
    name="test_font"; _hidden=1
    def shapesCount(self): return 1
    def componentsCount(self): return 0
    def getShapes(self): return [FlShape()]
    def getActiveShape(self): return FlShape()
    def remove(self): raise SystemExit("MUTATOR remove() CALLED")
    def clone(self): raise SystemExit("MUTATOR clone() CALLED")
class FlGlyph:
    name="testglyph1"; bodyLayer=FlLayer()
_fm.CurrentGlyph=lambda: FlGlyph()
W="/debug/walk?path="
def w(p,extra=""):
    c,d=call(W+p+extra); return c,d
print("1 root read     :",w("CurrentGlyph()","&stage=read&attrs=name")[1]["values"])
print("2 layer counts  :",w("CurrentGlyph().bodyLayer","&stage=read&attrs=name,shapesCount,componentsCount")[1]["values"])
r=w("CurrentGlyph().bodyLayer.getShapes()[0].transform","&stage=dir")[1]; print("3 transform dir :",r["public_names"],"| trace types:",[t_["type"] for t_ in r["trace"]])
r=w("CurrentGlyph().bodyLayer.getShapes()[0]","&stage=read&attrs=name,shapeType,contoursCount,remove")[1]; print("4 shape read    :",r["values"])
r=w("CurrentGlyph().bodyLayer.getShapes()[0].transform","&stage=read&attrs=getProperties,scale")[1]; print("5 transform read:",r["values"])
print("--- refusals (none of these may trigger a MUTATOR/NATIVE message) ---")
print("6 call remove() :",w("CurrentGlyph().bodyLayer.remove()","&stage=read")[1].get("error"))
print("7 call clone()  :",w("CurrentGlyph().bodyLayer.clone()","&stage=read")[1].get("error"))
print("8 native index  :",w("CurrentGlyph().bodyLayer[0]","&stage=read")[1].get("error")[:75])
print("9 bad start     :",w("bodyLayer","&stage=read")[1].get("error"))
print("10 underscore   :",w("CurrentGlyph()._hidden","&stage=read")[1].get("error"))
print("11 too long     :",w("CurrentGlyph()"+".bodyLayer"*8,"&stage=read")[1].get("error"))
print("12 list range   :",w("CurrentGlyph().bodyLayer.getShapes()[5]","&stage=read")[1].get("error"))
print("13 bad stage    :",w("CurrentGlyph()","&stage=zz")[1].get("error"))
r=w("CurrentGlyph().bodyLayer.getShapes()[0]","&stage=read&attrs=scale,_x,a.b")[1]; print("14 attr guards  :",r["values"])
_fm.CurrentGlyph=lambda: None
print("15 no glyph open:",w("CurrentGlyph()","&stage=read")[1].get("final_is_none"))

class WS:
    glyph=FlGlyph()
    def remove(self): raise SystemExit("MUTATOR ws.remove CALLED")
_fm.fl=WS()
print("16 fl root       :",w("fl","&stage=dir")[1]["public_names"])
r=w("fl.glyph.bodyLayer","&stage=read&attrs=name,shapesCount")[1]; print("17 fl.glyph...   :",r["values"],"| root type:",r["trace"][0]["type"])
print("18 fl root call  :",w("fl.remove()","&stage=read")[1].get("error"))
del _fm.fl
print("19 fl missing    :",w("fl","&stage=read")[1].get("error")[:60])
print("20 bad root      :",w("flx","&stage=read")[1].get("error"))

# ---------------- v0.37 walker tests: flWorkspace root ----------------
_fm.CurrentGlyph=lambda: FlGlyph()
class MTransform:
    def getProperties(self): return ["m11","m22","dx","dy","slant"]
    def getPropertyFloat(self,name): return {"m11":0.95146,"m22":0.96864,"dx":15.0,"dy":24.0}.get(name,0.0)
    def setPropertyFloat(self,name,v=0): raise SystemExit("MUTATOR setPropertyFloat CALLED")
    def scale(self,a,b=0): raise SystemExit("MUTATOR scale CALLED")
    def translate(self,a,b=0): raise SystemExit("MUTATOR translate CALLED")
class MShape:
    transform=MTransform(); name="Shape 1"
    def isComponent(self): return False
class MLayer(NativeLike):
    name="test_font"
    def shapesCount(self): return 1
    def getShapes(self): return [MShape()]
class MGlyph:
    name="testglyph1"; bodyLayer=MLayer()
class WSInst:
    currentGlyph=MGlyph()          # property style
    def currentPackage(self): return "pkg"   # method style
    def remove(self): raise SystemExit("MUTATOR ws.remove CALLED")
    def setToolPen(self): raise SystemExit("MUTATOR setToolPen CALLED")
class flWorkspace:
    @staticmethod
    def instance(): return WSInst()
_fm.flWorkspace=flWorkspace
W2="flWorkspace.instance().currentGlyph"
r=w(W2+".bodyLayer","&stage=read&attrs=name,shapesCount")[1]; print("21 modern path   :",r["values"],"| types:",[x["type"] for x in r["trace"]])
r=w("flWorkspace.instance().currentPackage","&stage=read")[1]; print("22 method-style  :",r["final_value"])
T=W2+".bodyLayer.getShapes()[0].transform"
r=w(T,"&stage=read&attrs=getProperties,getPropertyFloat(m11),getPropertyFloat(dy)")[1]; print("23 transform read:",r["values"])
r=w(T+".getPropertyFloat(m22)","&stage=read")[1]; print("24 path arg call :",r["final_value"])
print("--- v0.37 refusals (no MUTATOR message may appear) ---")
print("25 setPropertyFloat in path  :",w(T+".setPropertyFloat(m11)","&stage=read")[1].get("error"))
print("26 scale(2) in path          :",w(T+".scale(2)","&stage=read")[1].get("error"))
print("27 bad arg chars             :",w(T+".getPropertyFloat(m11;x)","&stage=read")[1].get("error"))
print("28 ws.remove()               :",w("flWorkspace.instance().remove()","&stage=read")[1].get("error"))
print("29 ws.setToolPen()           :",w("flWorkspace.instance().setToolPen()","&stage=read")[1].get("error"))
r=w(T,"&stage=read&attrs=scale(2),setPropertyFloat(m11),getPropertyFloat(m11;x),translate")[1]; print("30 attr-spec guards          :",r["values"])
print("31 native [] still refused   :",w(W2+".bodyLayer[0]","&stage=read")[1].get("error")[:60])

# ---- v0.38: navigation names as METHOD vs PROPERTY, via an *Info wrapper ----
class InfoShape:
    def shape(self): return MShape()            # method style
class InfoGlyphMethod:
    def glyph(self): return MGlyph()            # method style
class InfoGlyphProp:
    glyph=MGlyph()                              # property style
class WS2:
    def __init__(self,info): self.currentGlyph=info
for label,info in (("method",InfoGlyphMethod()),("property",InfoGlyphProp())):
    _fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda i=info: WS2(i))})
    r=w("flWorkspace.instance().currentGlyph.glyph.bodyLayer","&stage=read&attrs=name,shapesCount")[1]
    print("32 glyph as",label,":",r.get("values") or r.get("error"))

# ---- v0.39: QTransform-style getters through a flTransform.transform() chain ----
class QT:
    def m11(self): return 0.95146
    def m12(self): return 0.0
    def m21(self): return 0.0
    def m22(self): return 0.96864
    def dx(self): return 15.0
    def dy(self): return 24.0
    def isIdentity(self): return False
    def rotate(self,a): raise SystemExit("MUTATOR QTransform.rotate CALLED")
    def scale(self,a,b): raise SystemExit("MUTATOR QTransform.scale CALLED")
class MTransform2:
    def transform(self): return QT()
class MShape2:
    transform=MTransform2(); name="Shape 1"
    def isComponent(self): return False
class MLayer2:
    name="test_font"; shapes=[MShape2()]
class MGlyph2:
    name="testglyph1"; activeLayer=MLayer2()
class Info2: glyph=MGlyph2()
class WS3: currentGlyph=Info2()
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WS3())})
P="flWorkspace.instance().currentGlyph.glyph.activeLayer.shapes[0]"
print("33 shape via real list :",w(P,"&stage=read&attrs=name,isComponent")[1]["values"])
print("34 matrix getters      :",w(P+".transform.transform","&stage=read&attrs=m11,m12,m21,m22,dx,dy,isIdentity")[1]["values"])
print("35 mutators still refused:",w(P+".transform.transform","&stage=read&attrs=rotate,scale")[1]["values"])

# ================= v0.40: /debug/setcurrent =================
class LG:                                     # legacy glyph stub
    def __init__(self,n): self.name=n
class QTm:
    def __init__(self,**k): self.k=dict(m11=1.0,m12=0.0,m21=0.0,m22=1.0,dx=0.0,dy=0.0,isIdentity=False); self.k.update(k)
    def __getattr__(self,a):
        if a in self.__dict__.get("k",{}): return lambda: self.k[a]
        raise AttributeError(a)
class MSh:
    def __init__(self,**k): self.transform=QTm(**k)
    def shapeType(self): return "ShapeContours"
    def contoursCount(self): return 1
    def isComponent(self): return False
    def isComposite(self): return False
class MLy:
    def __init__(self,shapes): self.name="test_font"; self.shapes=shapes
class MGl:
    def __init__(self,n,shapes): self.name=n; self.activeLayer=MLy(shapes)
TRANSFORMS={"testglyph1":[MSh(m11=0.9514648914337158,m22=0.9686431884765625,dx=15.0,dy=24.0)],
            "testglyph4":[MSh(m21=0.17632698070846498)],
            "A":[MSh()]}
STATE={"cur":"testglyph1","calls":[],"mode":"ok"}
class InfoS:
    @property
    def glyph(self):
        if STATE["mode"]=="read_fails" and STATE["cur"]!="testglyph1": raise RuntimeError("boom while reading")
        return MGl(STATE["cur"],TRANSFORMS[STATE["cur"]])
class WSS: currentGlyph=InfoS()
def _set(g):
    STATE["calls"].append(g.name)
    if STATE["mode"]=="set_fails" and g.name!="testglyph1": raise RuntimeError("SetCurrentGlyph refused")
    if STATE["mode"]=="ignored": return
    STATE["cur"]=g.name
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WSS())})
_fm.SetCurrentGlyph=_set
_fm.CurrentGlyph=lambda: (None if STATE["mode"]=="no_orig" else LG(STATE["cur"]))
class FontS:
    glyphs=[LG("testglyph1"),LG("testglyph4"),LG("A")]
_fm.CurrentFont=lambda: FontS()
SC="/debug/setcurrent?name="
def sc(name,extra="&go=yes",mode="ok"):
    STATE.update(cur="testglyph1",calls=[],mode=mode); c,d=call(SC+name+extra); return d
d=sc("testglyph4",extra=""); print("36 no go          :",d.get("error")[:70],"| SetCurrentGlyph calls:",STATE["calls"])
d=sc("testglyph4"); m=d["after_switch"]["shapes"][0]["matrix"]
print("37 switch ok      : orig",d["original_name"],"| now",d["after_switch"]["modern_glyph_name"],"| m21 %.5f m11 %.1f"%(m["m21"],m["m11"]),"| restored_ok",d["restored_ok"],"| calls",STATE["calls"],"| final",STATE["cur"])
d=sc("testglyph1"); m=d["after_switch"]["shapes"][0]["matrix"]
print("38 same glyph     : m11 %.6f m22 %.6f dx %s dy %s"%(m["m11"],m["m22"],m["dx"],m["dy"]),"| shape_type",d["after_switch"]["shapes"][0]["shape_type"])
d=sc("testglyph4",mode="set_fails"); print("39 set raises     : called",d["set_current_called"],"|",d["set_current_error"][:40],"| after_switch name",d["after_switch"]["modern_glyph_name"],"| restored_ok",d["restored_ok"])
d=sc("testglyph4",mode="ignored"); print("40 set ignored    : after_switch name",d["after_switch"]["modern_glyph_name"],"(unchanged => honest) | restored_ok",d["restored_ok"])
d=sc("testglyph4",mode="read_fails"); print("41 read fails     : error",d["after_switch"].get("error"),"| restore_called",d["restore_called"],"| final",STATE["cur"])
d=sc("nope"); print("42 unknown glyph  :",d.get("found"),"| calls",STATE["calls"])
d=sc("testglyph4",mode="no_orig"); print("43 no original    :",d.get("restore_note"),"| restore_called",d["restore_called"])

# ================= v0.41: deferred switch (simulated event loop) =================
S2={"leg":"testglyph1","cur":"testglyph1","pending":None,"calls":[],"mode":"deferred"}
def _set2(g):
    S2["calls"].append(g.name)
    if S2["mode"]=="raises": raise RuntimeError("SetCurrentGlyph refused")
    S2["leg"]=g.name                      # legacy view changes immediately
    if S2["mode"]=="deferred": S2["pending"]=g.name   # modern view changes after the event loop runs
    else: S2["cur"]=g.name
def tick():
    if S2["pending"]: S2["cur"]=S2["pending"]; S2["pending"]=None
class InfoS2:
    @property
    def glyph(self):
        if S2["mode"]=="read_fails": raise RuntimeError("boom while reading")
        return MGl(S2["cur"],TRANSFORMS[S2["cur"]])
class WSS2: currentGlyph=InfoS2()
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WSS2())})
_fm.SetCurrentGlyph=_set2
_fm.CurrentGlyph=lambda: LG(S2["leg"])
def reset(mode="deferred"): S2.update(leg="testglyph1",cur="testglyph1",pending=None,calls=[],mode=mode)
def c2(path):
    c,d=call(path); tick(); return d
reset(); d=c2("/debug/setcurrent?name=testglyph4&go=yes")
print("44 same-request (reproduces the real result): modern after_switch =",d["after_switch"]["modern_glyph_name"],
      "| legacy after switch =",d["legacy_current_after_switch"],"| restored_ok =",d["restored_ok"])
reset(); d=c2("/debug/setcurrent?name=testglyph4&go=yes&phase=set")
print("45a phase=set returned:",{k:d[k] for k in ("set_current_called","legacy_current_before","legacy_current_after_in_same_request")})
d=c2("/debug/currentshapes"); m=d["shapes"][0]["matrix"]
print("45b currentshapes     : modern",d["modern_glyph_name"],"| legacy",d["legacy_current_name"],"| m21 %.5f"%m["m21"])
d=c2("/debug/setcurrent?name=testglyph1&go=yes&phase=set"); d=c2("/debug/currentshapes")
print("45c switched back     : modern",d["modern_glyph_name"],"| m11 %.6f dx %s"%(d["shapes"][0]["matrix"]["m11"],d["shapes"][0]["matrix"]["dx"]))
reset(); d=c2("/debug/setcurrent?name=testglyph4&phase=set"); print("46 phase=set no go    :",d.get("error")[:55],"| calls:",S2["calls"])
d=c2("/debug/setcurrent?name=testglyph4&go=yes&phase=zz"); print("47 bad phase          :",d.get("error"))
d=c2("/debug/setcurrent?name=nope&go=yes&phase=set"); print("48 unknown glyph      :",d.get("found"),"| calls:",S2["calls"])
reset("raises"); d=c2("/debug/setcurrent?name=testglyph4&go=yes&phase=set"); print("49 set raises         :",d["set_current_called"],"|",d["set_current_error"][:35])
reset("read_fails"); d=c2("/debug/currentshapes"); print("50 read fails         :",d.get("error"),"| legacy still reported:",d.get("legacy_current_name"))

# ================= v0.42: id getters =================
class IdProp:
    id=1234; name="A"
class IdMeth:
    name="A"
    def id(self): return 1234
    def index(self): return 7
class FontI:
    glyphs=[IdProp()]
_fm.CurrentFont=lambda: FontI()
c,d=call("/debug/objdir?name=A&target=glyph&stage=read&attrs=id,index,name"); print("51 objdir id (property):",d["values"])
FontI.glyphs=[IdMeth()]
c,d=call("/debug/objdir?name=A&target=glyph&stage=read&attrs=id,index,name"); print("52 objdir id (method)  :",d["values"])
class MG:
    name="testglyph1"
    def id(self): return 1234
    def fgGlyphId(self): return 5678
class Info9: glyph=MG()
class WS9: currentGlyph=Info9()
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WS9())})
c,d=call("/debug/walk?path=flWorkspace.instance().currentGlyph.glyph&stage=read&attrs=id,fgGlyphId,name"); print("53 walker id getters   :",d["values"])

# ================= v0.43: /debug/buildglyph =================
class LGi:
    def __init__(self,n,i): self.name=n; self.id=i
class FontB:
    glyphs=[LGi("testglyph1",4),LGi("testglyph4",7)]
_fm.CurrentFont=lambda: FontB()
LIVE_ID={"testglyph1":999,"testglyph4":888}
class MGl2:
    def __init__(self,n,shapes,gid,fgid): self.name=n; self.activeLayer=MLy(shapes); self._gid=gid; self.fgGlyphId=fgid; self.refCnt=1
    def id(self): return self._gid
    def nodesCount(self): return 39
BMODE={"mode":"linked"}
class flGlyph:
    def __init__(self,glyph,font):
        if BMODE["mode"]=="raises": raise RuntimeError("cannot build")
        n=glyph.name
        if BMODE["mode"]=="linked":
            m=MGl2(n,TRANSFORMS[n],LIVE_ID[n],glyph.id)           # same object as the live one
        else:
            m=MGl2(n,[MSh()],555,glyph.id)                         # fresh copy, transform lost
        self.__dict__.update(m.__dict__); self._gid=m._gid
    def id(self): return self._gid
    def nodesCount(self): return 39
_fm.flGlyph=flGlyph
class InfoL:
    @property
    def glyph(self): return MGl2("testglyph1",TRANSFORMS["testglyph1"],999,4)
class WSL: currentGlyph=InfoL()
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WSL())})
def bg(name,extra="&go=yes",mode="linked"):
    BMODE["mode"]=mode; c,d=call("/debug/buildglyph?name="+name+extra); return d
d=bg("testglyph4",extra=""); print("54 no go             :",d["error"][:60])
d=bg("testglyph4"); m=d["built_glyph"]["shapes"][0]["matrix"]
print("55 linked testglyph4 : fgGlyphId",d["built_fgGlyphId"],"legacy_id",d["legacy_id"],"| m21 %.5f"%m["m21"],"| same_as_live",d.get("same_object_as_live_current"))
d=bg("testglyph1"); m=d["built_glyph"]["shapes"][0]["matrix"]
print("56 linked testglyph1 : built_id",d["built_id"],"live id",d["live_current_modern_id"],"| same_as_live",d["same_object_as_live_current"],"| dx",m["dx"],"m11 %.6f"%m["m11"])
d=bg("testglyph1",mode="copy"); m=d["built_glyph"]["shapes"][0]["matrix"]
print("57 COPY  testglyph1  : built_id",d["built_id"],"live id",d["live_current_modern_id"],"| same_as_live",d["same_object_as_live_current"],"| dx",m["dx"],"isIdentity",m["isIdentity"])
d=bg("testglyph4",mode="raises"); print("58 constructor raises:",d["construct_error"])
d=bg("nope"); print("59 unknown glyph     :",d["found"])
del _fm.flGlyph; d=bg("testglyph4"); print("60 no flGlyph class  :",d["error"])

# ================= v0.44: reads/gc options =================
_fm.flGlyph=flGlyph   # test 60 removed it on purpose; restore for these cases
BMODE["mode"]="linked"
def bg2(extra): c,d=call("/debug/buildglyph?name=testglyph1&go=yes"+extra); return d
d=bg2("&reads=none"); print("61 reads=none   :",sorted(k for k in d if k.startswith("built_")),"| built_glyph:",d["built_glyph"])
d=bg2("&reads=layer"); print("62 reads=layer  :",d["built_glyph"])
d=bg2("&reads=shapes"); print("63 reads=shapes :",d["built_glyph"])
d=bg2("&reads=full&gc=yes"); print("64 full + gc    : shapes",d["built_glyph"]["shape_count"],"| gc ran (before >= 0, after):",d["gc_collected_before"]>=0,d["gc_collected_after"],"| refCnt first key:",list(d).index("built_refCnt")<list(d).index("built_name"))
print("65 bad reads    :",bg2("&reads=zz")["error"])
print("66 bad gc       :",bg2("&gc=zz")["error"])
print("67 defaults still full:",bg2("")["built_glyph"]["shape_count"])

# ================= v0.45: elements in /glyph/outline, cached wrapper =================
class Gx(Glyph):
    id=10
class FontX:
    path="fontA"
    glyphs=[Gx()]
FONT_STATE={"path":"fontA"}
def _font():
    f=FontX(); f.path=FONT_STATE["path"]; return f
_fm.CurrentFont=_font
CTR={"built":0}
class MLy3:
    def __init__(self,name,nodes,shapes): self.name=name; self._n=nodes; self.shapes=shapes
    def nodesCount(self): return self._n
class flGlyph3:
    mode={}
    def __init__(self,glyph,font):
        CTR["built"]+=1
        m=flGlyph3.mode
        if m["raise"]: raise RuntimeError("cannot build")
        self.name=m["name"]; self.fgGlyphId=m["fgid"]; self._valid=m["valid"]
        self.activeLayer=MLy3(m["layer"],m["nodes"],[MSh(m11=0.5,m22=0.25,dx=7.0,dy=9.0)])
    def isValid(self): return self._valid
def setmode(**k):
    flGlyph3.mode=dict(layer="L",nodes=3,name="A",fgid=10,valid=True,**{"raise":False}); flGlyph3.mode.update(k)
_fm.flGlyph=flGlyph3
def reset3(**k):
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0]=None; CTR["built"]=0; FONT_STATE["path"]="fontA"; setmode(**k)
def outl(extra=""): c,d=call("/glyph/outline?name=A"+extra); return d
reset3(); d=outl(); e=d["elements"]
print("68 first call   :",e["available"],e["wrapper"],"| matrix m11",e["shapes"][0]["matrix"]["m11"],"dx",e["shapes"][0]["matrix"]["dx"],"| built",CTR["built"],"| outline nodes still there:",d["node_count"],"| bbox present:",bool(d.get("fontlab_bbox")))
d=outl(); print("69 second call  :",d["elements"]["wrapper"],"| constructor calls so far",CTR["built"],"(must stay 1)")
d=outl(); print("70 third call   :",d["elements"]["wrapper"],"| constructor calls",CTR["built"],"(must stay 1)")
w=list(ns["_MODERN_CACHE"].values())[0]; w._valid=False
d=outl(); print("71 cached but isValid()=False ->",d["elements"]["wrapper"],"| constructor calls",CTR["built"],"(must be 2)")
w=list(ns["_MODERN_CACHE"].values())[0]; w.name="OTHER"
d=outl(); print("72 cached name changed (id reuse) ->",d["elements"]["wrapper"],"| constructor calls",CTR["built"],"(must be 3)")
w=list(ns["_MODERN_CACHE"].values())[0]; w.fgGlyphId=99
d=outl(); print("73 cached fgGlyphId changed      ->",d["elements"]["wrapper"],"| constructor calls",CTR["built"],"(must be 4)")
FONT_STATE["path"]="fontB"; d=outl(); print("74 different font ->",d["elements"]["wrapper"],"| constructor calls",CTR["built"],"(must be 5)")
reset3(); d=outl("&modern=no"); print("75 modern=no    :",d["elements"],"| constructor calls",CTR["built"],"(must be 0)")
reset3(**{"raise":True}); d=outl(); print("76 constructor raises ->",d["elements"]["available"],"|",d["elements"]["error"][:40],"| outline unaffected, nodes:",d["node_count"])
reset3(name="WRONG"); d=outl(); print("77 built glyph name mismatch ->",d["elements"]["available"],"|",d["elements"]["error"][:60],"| cache size",len(ns["_MODERN_CACHE"]))
reset3(layer="test_font"); d=outl(); print("78 modern layer differs ->",d["elements"]["available"],"|",d["elements"]["error"][:70])
reset3(nodes=5); d=outl(); print("79 modern node count differs ->",d["elements"]["available"])
reset3(); del _fm.flGlyph; d=outl(); print("80 no flGlyph class ->",d["elements"]["error"]); _fm.flGlyph=flGlyph3

# ================= v0.52: /debug/tryshape (pen route; gated, refuses non-empty glyphs) =================
TS_LOG=[]
class TsLayer(Layer):                      # reuses the fake layer of the first cases (findNode, boundingBox, matrix ...)
    def __init__(self,c,n): self._c=c; self._n=n; self.name="Body"
    def __len__(self): return self._n
    def countContours(self): return self._c
    def countNodes(self): return self._n
    def countShapes(self): return 1 if self._c else 0
class TsPen:
    def __init__(self,g,fail=None): self.g=g; self.fail=fail; self.pts=0; self.closed=False
    def moveTo(self,p):
        if self.fail=="moveTo": raise RuntimeError("moveTo boom")
        TS_LOG.append(("moveTo",p)); self.pts=1
    def lineTo(self,p): TS_LOG.append(("lineTo",p)); self.pts+=1
    def closePath(self):
        TS_LOG.append(("closePath",)); self.closed=True
        self.g._layers=[TsLayer(1,self.pts)]            # the pen creates the layer, as hoped (stub behaviour only)
class TsGlyph:
    def __init__(self,name,layers,comps=0,pen_mode="ok"):
        self.name=name; self._layers=layers; self._comps=comps; self.pen_mode=pen_mode; self.id=5
        self.leftMargin=1.5; self.rightMargin=2.5; self.width=500.0; self.unicode=None
    @property
    def layers(self): return self._layers
    @property
    def components(self): return [0]*self._comps
    @property
    def layer(self): return self._layers[0] if self._layers else None
    @property
    def bodyLayer(self): return self._layers[0] if self._layers else None
    @property
    def activeLayer(self): return self._layers[0] if self._layers else None
    bodyLayerStrict=None
    def getPen(self):
        TS_LOG.append(("getPen",))
        if self.pen_mode=="raises": raise RuntimeError("getPen boom")
        if self.pen_mode=="none": return None
        return TsPen(self,fail="moveTo" if self.pen_mode=="movefail" else None)
TS={}
class TsFont:
    path="ts"
    @property
    def glyphs(self): return list(TS.values())
def ts_reset():
    TS.clear(); TS_LOG.clear()
    for g in (TsGlyph("tri",[]), TsGlyph("full",[TsLayer(1,3)]), TsGlyph("comp",[],comps=1), TsGlyph("emptylayer",[TsLayer(0,0)]),
              TsGlyph("raises",[],pen_mode="raises"), TsGlyph("nopen",[],pen_mode="none"), TsGlyph("movefail",[],pen_mode="movefail")):
        TS[g.name]=g
_fm.CurrentFont=lambda: TsFont()
_fm.flGlyph=flGlyph3 if "flGlyph3" in dir() else None
if _fm.flGlyph is None: del _fm.flGlyph
def ts(q):
    ts_reset(); c,d=call("/debug/tryshape?"+q); return c,d
c,d=ts("name=tri&stage=draw"); print("81 no go          :",c,d["error"][:40],"| calls made:",TS_LOG)
c,d=ts("name=tri&go=yes&route=createContour"); print("82 unknown route  :",c,d["error"],"| calls made:",TS_LOG)
c,d=ts("name=tri&go=yes&stage=bogus"); print("83 unknown stage  :",c,d["error"],"| calls made:",TS_LOG)
c,d=ts("go=yes"); print("84 missing name   :",c,d["error"][:30])
c,d=ts("name=nope&go=yes"); print("85 unknown glyph  :",c,d["found"],"| calls made:",TS_LOG)
for nm in ("full","comp"):
    c,d=ts("name="+nm+"&go=yes&stage=draw"); print("86 refuse",nm.ljust(5),":",c,d["refused"],"| state_before:",d["state_before"],"| calls made:",TS_LOG)
c,d=ts("name=emptylayer&go=yes&stage=dir"); print("87 one layer, 0 nodes allowed:",c,d.get("refused"),d["state_before"],"| calls",d["calls"])
c,d=ts("name=tri&go=yes&stage=dir"); print("88 stage=dir      :",c,"| pen",d["pen_type"],"| names",d["pen_names"][:3],"| calls",d["calls"],"| log",TS_LOG,"| before",d["state_before"],"| after",d["state_after"],"| may_change",d["font_may_have_changed"],"| outline key present:","outline_after" in d)
c,d=ts("name=tri&go=yes&stage=draw"); print("89 stage=draw     :",c,"| calls",d["calls"],"| after",d["state_after"],"| matches",d["counts_match_expected"],"| expected",d["expected"],"| outline key:",[k for k in d if k.startswith("outline_after")],"| outline err:",str(d.get("outline_after_error"))[:90],"| may_change",d["font_may_have_changed"])
c,d=ts("name=tri&go=yes&stage=draw"); print("90 default route/stage on draw ->",d["route"],d["stage"]); c,d=ts("name=tri&go=yes"); print("91 defaults       :",d["route"],d["stage"],"| draw ops in log:",[x for x in TS_LOG if x[0]!="getPen"])
c,d=ts("name=raises&go=yes&stage=draw"); print("92 getPen raises  :",c,d["failed_at"],"|",d["error"],"| after",d["state_after"])
c,d=ts("name=nopen&go=yes&stage=draw"); print("93 getPen None    :",c,d["pen_is_none"],"| calls",d["calls"],"| log",TS_LOG)
c,d=ts("name=movefail&go=yes&stage=draw"); print("94 moveTo raises  :",c,d["failed_at"],"|",d["error"],"| calls",d["calls"],"| matches",d["counts_match_expected"])
_fm.CurrentFont=lambda: None; c,d=call("/debug/tryshape?name=tri&go=yes"); print("95 no font open   :",c,d)

# ================= v0.53: /debug/tryshape route=modern (build / attach / refresh) =================
_fm.CurrentFont=lambda: TsFont()
CTRM={"node":0,"contour":0,"shape":0,"addShape":0,"update":0}
MODE={}
class MNode:
    def __init__(s,x,y): CTRM["node"]+=1; s.x=x; s.y=y
class MContour:
    clockwise=False
    def __init__(s,nodes,*rest):
        if MODE.get("contour_raises"): raise RuntimeError("contour boom")
        CTRM["contour"]+=1; s.n=len(nodes); s.closed=bool(rest[-1]) if rest else False; s.args=rest; MODE['last_contour_args']=rest
    def nodesCount(s): return s.n
class MShape2:
    def __init__(s,*a):
        CTRM["shape"]+=1; s.c=0
        if a:
            if MODE.get("shape_ctor_fails"): raise TypeError("Wrong argument type. No ctor takes a contour")
            s.c=1
    def addContour(s,c):
        if MODE.get("addcontour_fails"): raise IndexError("Unexpected SeqBase<T> length.")
        s.c+=1
    def addContours(s,lst):
        if MODE.get("addcontours_fails"): raise IndexError("Unexpected SeqBase<T> length.")
        s.c+=len(lst) if isinstance(lst,list) else 1
    def contoursCount(s): return s.c
    def hasContours(s): return s.c>0
    def isEmpty(s): return s.c==0
class MShapeDataLink:                      # the shape's own shapeData: adding a contour makes the shape report it
    def __init__(s,shape): s.shape=shape; s._c=[]
    def addContour(s,c):
        if MODE.get("sd_fails"): raise IndexError("Unexpected SeqBase<T> length.")
        s._c.append(c)
        if not MODE.get("sd_noeffect"): s.shape.c+=1
    @property
    def contours(s): return s._c
MShape2.shapeData=property(lambda s: None if MODE.get("sd_none") else MShapeDataLink(s))
class MLayer2:
    name="test_font"
    def __init__(s,shapes=0,nodes=0): s.shapes=[]; s._sh=shapes; s._n=nodes
    def shapesCount(s): return s._sh
    def nodesCount(s): return s._n
    def componentsCount(s): return 0
    def addShape(s,shape):
        if MODE.get("add_raises"): raise RuntimeError("addShape boom")
        CTRM["addShape"]+=1; s._sh+=1; s._n+=3; s.shapes.append(MSh())
    def update(s): CTRM["update"]+=1
MODERN_LAYERS={}
class flGlyphM:
    def __init__(s,glyph,font): s.name=glyph.name; s.fgGlyphId=glyph.id; s.activeLayer=MODERN_LAYERS.get(glyph.name)
    def isValid(s): return True
    def update(s): CTRM["update"]+=1
def tm(q,layers=None,**mode):
    ts_reset(); ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0]=None
    for k in CTRM: CTRM[k]=0
    MODE.clear(); MODE.update(mode); MODERN_LAYERS.clear(); MODERN_LAYERS.update(layers or {})
    _fm.flNode=MNode; _fm.flContour=MContour; _fm.flShape=MShape2; _fm.flGlyph=flGlyphM
    c,d=call("/debug/tryshape?"+q); return c,d
M="name=tri&go=yes&route=modern&variant=nodes"      # cases 96-109 keep testing the v0.53 form explicitly
c,d=tm("name=tri&route=modern&stage=attach",{"tri":MLayer2()}); print("96 modern, no go     :",c,d["error"][:30],"| objects built / addShape:",CTRM)
c,d=tm(M,{"tri":MLayer2()}); print("97 default stage     :",d["stage"],"| calls",d["calls"],"| built",d["built"],"| before",d["state_before"],"| may_change",d["font_may_have_changed"],"| addShape",CTRM["addShape"])
c,d=tm(M+"&stage=build",{"tri":MLayer2(2,12)}); print("98 build on non-empty:",c,d.get("refused"),"| calls",len(d["calls"]),"| addShape",CTRM["addShape"],"| layer untouched:",d["state_before"])
c,d=tm(M+"&stage=attach",{"tri":MLayer2()}); print("99 attach            :",c,"| calls",d["calls"],"| after",d["state_after"],"| matches",d["counts_match_expected"],"| modern view shapes",d["modern_view_after"]["shape_count"],d["modern_view_after"]["layer_nodes_count"],"| legacy",d["legacy_state_after"],"| may_change",d["font_may_have_changed"],"| addShape",CTRM["addShape"])
c,d=tm(M+"&stage=attach",{"tri":MLayer2(1,3)}); print("100 attach refused (layer has a shape):",c,d["refused"],"| objects built / addShape:",CTRM)
c,d=tm(M+"&stage=attach",{}); print("101 attach refused (no modern layer)  :",c,d["refused"],d["state_before"],"| objects built / addShape:",CTRM)
c,d=tm(M+"&stage=attach",{"tri":MLayer2()},add_raises=True); print("102 addShape raises  :",d["failed_at"],"|",d["error"],"| after",d["state_after"],"| matches",d["counts_match_expected"],"| calls",len(d["calls"]))
c,d=tm(M+"&stage=build",{"tri":MLayer2()}); del _fm.flNode; ns["_MODERN_CACHE"].clear(); c,d=call("/debug/tryshape?"+M+"&stage=build"); print("103 no flNode class  :",d["failed_at"],"|",d["error"])
c,d=tm(M+"&stage=build",{"tri":MLayer2()},contour_raises=True); print("104 flContour raises :",d["failed_at"],"|",d["error"],"| calls",d["calls"])
c,d=tm(M+"&stage=refresh",{"tri":MLayer2()}); print("105a refresh layer   :",d["calls"],"| update calls",CTRM["update"],"| addShape",CTRM["addShape"],"| may_change",d["font_may_have_changed"])
c,d=tm(M+"&stage=refresh&what=glyph",{"tri":MLayer2()}); print("105b refresh glyph   :",d["calls"],"| update calls",CTRM["update"])
c,d=tm(M+"&stage=refresh&what=bogus",{"tri":MLayer2()}); print("105c what=bogus      :",d["error"],"| update calls",CTRM["update"])
c,d=tm(M+"&stage=refresh",{}); print("105d refresh, no modern layer:",d["error"],"| update calls",CTRM["update"])
c,d=tm(M+"&stage=build",{"tri":MLayer2()}); del _fm.flGlyph; ns["_MODERN_CACHE"].clear(); c,d=call("/debug/tryshape?"+M+"&stage=build"); print("106 no flGlyph class :",d["modern_wrapper_error"],"|",d["error"],"| calls",d["calls"])
c,d=tm(M+"&stage=dir",{"tri":MLayer2()}); print("107a modern + dir    :",d["error"])
c,d=tm("name=tri&go=yes&route=pen&stage=build",{"tri":MLayer2()}); print("107b pen + build     :",d["error"])
c,d=tm("name=tri&go=yes&route=bogus"); print("107c unknown route   :",d["error"])
c,d=tm("name=nope&go=yes&route=modern",{"tri":MLayer2()}); print("108 unknown glyph    :",d["found"],"| objects built:",CTRM["node"])
c,d=tm("name=tri&go=yes&stage=draw"); print("109 pen draw still works:",d["calls"][-1],d["counts_match_expected"])

# ================= v0.54: route=modern stage=names and variant=points (QPointF list + node type On + closed) =================
class MPoint:
    def __init__(s,x,y): CTRM["point"]=CTRM.get("point",0)+1; s.x=x; s.y=y
qc.QPointF=MPoint
MNode.NodeType=type("NodeType",(),{"On":"ON_ENUM","Off":"OFF_ENUM"})
MNode.NodeKind=type("NodeKind",(),{"Sharp":1,"Smooth":2})
MContour.FigureType=type("FigureType",(),{"Line":1})
def tp(q,layers=None,**mode):
    c,d=tm(q,layers,**mode); return c,d
P="name=tri&go=yes&route=modern"
PP=P+"&variant=points"        # cases 110-129 test the v0.54 / v0.55 variant explicitly
c,d=tp(PP+"&stage=names",{"tri":MLayer2()}); n=d["names"]; print("110 names            :",c,n["QtCore.QPointF"],"| NodeType",n["flNode.NodeType"]["names"],"| NodeKind",n["flNode.NodeKind"]["names"],"| FigureType",n["flContour.FigureType"]["names"],"| direct",n["flNode_direct_value_names"],"| may_change",d["font_may_have_changed"],"| objects built",CTRM)
c,d=tp(PP+"&stage=names"); print("110b names without modern layer / wrapper needed:",c,"names" in d)
c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("111 points build (default variant):",d["variant"],"| calls",d["calls"],"| notes",d["notes"],"| built",d["built"],"| points made",CTRM["point"],"| addShape",CTRM["addShape"])
c,d=tp(PP+"&stage=attach",{"tri":MLayer2()}); print("112 points attach    :",c,"| after",d["state_after"],"| matches",d["counts_match_expected"],"| addShape",CTRM["addShape"],"| flContour got (node type, closed):",MODE.get("last_contour_args"))
del MNode.NodeType; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("113 On unresolved (no NodeType):",d["failed_at"],"|",d["error"][:120],"| points made",CTRM.get("point"),"| contours",CTRM["contour"])
MNode.On="DIRECT_ON"; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("113b flNode.On fallback:",d["notes"],"| calls[0]",d["calls"][0]); del MNode.On
MNode.NodeType=type("NodeType",(),{"On":"ON_ENUM","Off":"OFF_ENUM"})
_qp=qc.QPointF; del qc.QPointF; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("114 QPointF missing  :",d["failed_at"],"|",d["error"],"| calls",d["calls"]); qc.QPointF=_qp
c,d=tp(P+"&stage=build&variant=bogus",{"tri":MLayer2()}); print("115 bogus variant    :",d["error"])
c,d=tp(PP+"&stage=attach",{"tri":MLayer2(1,3)}); print("116 points attach refused on non-empty layer:",d["refused"],"| points made",CTRM.get("point"),"| contours",CTRM["contour"],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=build&variant=nodes",{"tri":MLayer2()}); print("117 variant=nodes still available:",d["variant"],d["calls"][3])
_ng=MNode.NodeKind; del MNode.NodeKind; c,d=tp(PP+"&stage=names",{"tri":MLayer2()}); n=d["names"]; print("118 names, NodeKind missing:",list(n["flNode.NodeKind"]),"| NodeType still read:",n["flNode.NodeType"]["names"]); MNode.NodeKind=_ng
c,d=tp(P+"&stage=build&variant=points",{"tri":MLayer2()},contour_raises=True); print("119 points flContour raises:",d["failed_at"],"|",d["error"])

# ================= v0.55: the enums are real dicts (live, v0.54); ontype=value|key =================
_cls_nt=MNode.NodeType; _cls_nk=MNode.NodeKind; _cls_ft=MContour.FigureType
MNode.NodeType={"Off":0,"On":1,"Curve":2}; MNode.NodeKind={"Sharp":1,"Smooth":2}; MContour.FigureType={"Line":1}
c,d=tp(PP+"&stage=names",{"tri":MLayer2()}); n=d["names"]; print("120 names, dict enums:",n["flNode.NodeType"],"| NodeKind",n["flNode.NodeKind"]["items"],"| FigureType",n["flContour.FigureType"]["items"])
c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("121 dict build, value:",d["ontype"],"| notes",d["notes"],"| flContour got",MODE.get("last_contour_args"),"| calls[0]",d["calls"][0])
c,d=tp(PP+"&stage=build&ontype=key",{"tri":MLayer2()}); print("122 dict build, key  :",d["ontype"],"| notes",d["notes"],"| flContour got",MODE.get("last_contour_args"))
c,d=tp(PP+"&stage=attach&ontype=value",{"tri":MLayer2()}); print("123 dict attach      :",d["counts_match_expected"],"| flContour got",MODE.get("last_contour_args"),"| addShape",CTRM["addShape"])
MNode.NodeType={"Off":0,"Curve":2}; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("124 dict without On  :",d["failed_at"],"|",d["error"][:130],"| points made",CTRM.get("point"))
MNode.NodeType={"on":7}; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("125 lowercase key 'on':",d["notes"],"| flContour got",MODE.get("last_contour_args"))
MNode.NodeType={"Off":0,"On":0}; c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("126 On maps to 0 (falsy value) still used:",MODE.get("last_contour_args"),d["notes"])
c,d=tp(PP+"&stage=build&ontype=bogus",{"tri":MLayer2()}); print("127 bogus ontype     :",d["error"])
c,d=tp(P+"&stage=build&variant=nodes&ontype=key",{"tri":MLayer2()}); print("128 variant=nodes ignores ontype:",d["variant"],"ontype" in d,d["calls"][3])
MNode.NodeType=_cls_nt; MNode.NodeKind=_cls_nk; MContour.FigureType=_cls_ft
c,d=tp(PP+"&stage=build",{"tri":MLayer2()}); print("129 class-style enums still resolve:",d["notes"])

# ================= v0.56: variant=probe (read-only: every flContour constructor form on detached objects) =================
MNode.NodeType={"On":1,"Off":2,"Curve":4,"AnyNodeMask":7}
_old_init=MContour.__init__
def _arity_init(s,nodes=None,*rest):
    if MODE.get("ctor_fail_arity3") and len(rest)==2: raise AttributeError("Incorrect # of args")
    if nodes is None: nodes=[]
    _old_init(s,nodes,*rest)
MContour.__init__=_arity_init
def probe_print(tag,d):
    print(tag,[(f["form"],"ok" if f.get("ok") else ("skipped" if f.get("skipped") else "ERR "+f["error"][:30])) for f in d["ctor_probe"] if "form" in f],"| notes",[f["note"][:40] for f in d["ctor_probe"] if "note" in f])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); probe_print("130 probe       :",d); print("    ...reads of form 2:",d["ctor_probe"][1]["read"],"| may_change",d["font_may_have_changed"],"| shape/addShape/layer untouched:",CTRM["shape"],CTRM["addShape"])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},ctor_fail_arity3=True); probe_print("131 arity-3 fails:",d)
c,d=tp(P+"&stage=attach&variant=probe",{"tri":MLayer2()}); print("132 attach+probe refused:",d["error"],"| objects built",CTRM)
c,d=tp(P+"&stage=refresh&variant=probe",{"tri":MLayer2()}); print("132b refresh+probe     :",d["error"])
MNode.NodeType={"Off":2}; c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); probe_print("133 no On key    :",d)
MNode.NodeType={"On":1,"Off":2,"Curve":4,"AnyNodeMask":7}
_qp=qc.QPointF; del qc.QPointF; c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); print("134 QPointF missing:",d["ctor_probe"]); qc.QPointF=_qp
c,d=tp(P+"&stage=build&variant=bogus",{"tri":MLayer2()}); print("135 bogus variant msg:",d["error"])
MContour.__init__=_old_init
MNode.NodeType=_cls_nt


# ================= v0.57: default variant=single (flContour(points) + contour.closed = True) + the close probe =================
_old_setattr=MContour.__setattr__
def _ro_closed(s,k,v):
    if k=="closed" and MODE.get("closed_ignored") and "closed" in s.__dict__: return
    if k=="closed" and MODE.get("closed_raises") and "closed" in s.__dict__: raise AttributeError("closed is read-only")
    object.__setattr__(s,k,v)
MContour.__setattr__=_ro_closed
c,d=tp(P+"&stage=build",{"tri":MLayer2()}); print("140 default = single:",d["variant"],"| ontype in reply:","ontype" in d,"| calls",d["calls"],"| notes",d["notes"],"| flContour got",MODE.get("last_contour_args"),"| built",d["built"])
_fn=_fm.flNode; del _fm.flNode; c,d=tp(P+"&stage=build",{"tri":MLayer2()}); print("141 single needs no flNode class:",d.get("failed_at"),d["variant"],len(d["calls"])); _fm.flNode=_fn
c,d=tp(P+"&stage=attach",{"tri":MLayer2()}); print("142 single attach    :",d["counts_match_expected"],"| addShape",CTRM["addShape"],"| flContour got",MODE.get("last_contour_args"),"| calls[-3:]",d["calls"][-3:])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},closed_ignored=True); print("143 closed=True ignored by FontLab:",d["failed_at"],"|",d["error"][:100],"| addShape",CTRM["addShape"],"| layer untouched (before):",d["state_before"]["shapes"],"| no state_after / counts reported:",("state_after" not in d and "counts_match_expected" not in d),"| calls",d["calls"][-2:])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},closed_raises=True); print("144 closed setter raises:",d["failed_at"],"|",d["error"],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2(1,3)}); print("145 single attach refused on non-empty layer:",d["refused"],"| points made",CTRM.get("point"),"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=build&variant=points",{"tri":MLayer2()}); print("146 variant=points still available:",d["variant"],d["ontype"],"|",d["notes"])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); cp=next(x["close_probe"] for x in d["ctor_probe"] if "close_probe" in x); print("147 probe close section:",[ (x.get("step") or list(x)[0], x.get("ok"), x.get("read",{}).get("closed")) for x in cp])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},closed_raises=True); cp=next(x["close_probe"] for x in d["ctor_probe"] if "close_probe" in x); print("148 probe, closed setter raises:",cp[0])
_qr=getattr(qc,"QRectF",None)
class MRect:
    def __init__(s,x,y,w,h): s.r=(x,y,w,h)
qc.QRectF=MRect; c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); cp=next(x["close_probe"] for x in d["ctor_probe"] if "close_probe" in x); print("149 probe with QRectF   :",cp[-1]["step"],cp[-1].get("ok"),cp[-1].get("error","")[:40]); del qc.QRectF
print("149b probe without QRectF:",next(x["close_probe"] for x in tp(P+"&stage=build&variant=probe",{"tri":MLayer2()})[1]["ctor_probe"] if "close_probe" in x)[-1])
c,d=tp(P+"&stage=build&variant=bogus",{"tri":MLayer2()}); print("150 bogus variant msg:",d["error"])
MContour.__setattr__=_old_setattr


# ================= v0.58: variant=probe shape section (which shape.addContour / addContours / flShape(contour) forms work) =================
def sps(d): return next(x["shape_probe"] for x in d["ctor_probe"] if "shape_probe" in x)
def sp_print(tag,d): print(tag,[(f["form"][:44],"ok "+str(f["read"].get("contoursCount")) if f.get("ok") else "ERR "+f["error"][:34]) for f in sps(d) if "form" in f])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); sp_print("160 shape probe, all ok :",d)
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},addcontour_fails=True,shape_ctor_fails=True); sp_print("161 live-like failures  :",d)
qc.QRectF=MRect; c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); print("162 with QRectF forms   :",[f["form"] for f in sps(d)][-2:]); del qc.QRectF
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); print("163 without QRectF      :",len(sps(d)),"forms |  last:",sps(d)[-1]["form"])
c,d=tm(P+"&stage=build&variant=probe",{"tri":MLayer2()}); del _fm.flShape; ns["_MODERN_CACHE"].clear(); c,d=call("/debug/tryshape?"+P+"&stage=build&variant=probe"); print("164 no flShape class    :",sps(d))
MContour.__setattr__=_ro_closed
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},closed_raises=True); sp_print("165 closed setter raises:",d)
MContour.__setattr__=_old_setattr
print("166 nothing attached by the probe:",CTRM["addShape"],"| may_change",d["font_may_have_changed"])

# ================= v0.59: variant=probe data section (flShapeData route on detached objects) =================
class MShapeData:
    def __init__(s):
        s._c=[]
    def addContour(s,c):
        if MODE.get("sd_fails"): raise IndexError("Unexpected SeqBase<T> length.")
        s._c.append(c)
    def addContours(s,lst):
        if MODE.get("sd_fails"): raise IndexError("Unexpected SeqBase<T> length.")
        s._c.extend(lst)
    @property
    def contours(s): return s._c
    def isNull(s): return False
    def isValid(s): return True
_fm.flShapeData=MShapeData
MShape2.ensurePaths=lambda s: (_ for _ in ()).throw(RuntimeError("ensurePaths boom")) if MODE.get("ensure_fails") else None
MShape2.isNull=lambda s: False
_old_shape_init=MShape2.__init__
def _shape_init(s,*a):
    _old_shape_init(s,*a)
    if a and hasattr(a[0],"_c"): s.c=len(a[0]._c)
MShape2.__init__=_shape_init
def dps(d): return next(x["data_probe"] for x in d["ctor_probe"] if "data_probe" in x)
def dp_print(tag,d):
    print(tag,[(f["form"][:40],("ok "+str(f["read"].get("data_contours_len",f["read"].get("shape",{}).get("contoursCount")))) if f.get("ok") else "ERR "+f["error"][:28]) for f in dps(d) if "form" in f])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); dp_print("170 data probe, all ok:",d); print("    fresh reads:",[(f["fresh"],f.get("read",f.get("error"))) for f in dps(d) if "fresh" in f])
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},addcontour_fails=True,shape_ctor_fails=False,ensure_fails=True); dp_print("171 live-like (shape.addContour fails, data route works):",d)
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},sd_fails=True); dp_print("172 flShapeData fails too:",d)
c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()},shape_ctor_fails=True); dp_print("173 flShape(flShapeData) refused:",d)
c,d=tm(P+"&stage=build&variant=probe",{"tri":MLayer2()}); del _fm.flShapeData; ns["_MODERN_CACHE"].clear(); c,d=call("/debug/tryshape?"+P+"&stage=build&variant=probe"); print("174 no flShapeData class:",dps(d)); _fm.flShapeData=MShapeData
qc.QRectF=MRect; c,d=tp(P+"&stage=build&variant=probe",{"tri":MLayer2()}); print("175 with QRectF, last form:",[f["form"] for f in dps(d) if "form" in f][-1]); del qc.QRectF
print("176 probe attached nothing:",CTRM["addShape"],"| may_change",d["font_may_have_changed"])
MShape2.__init__=_old_shape_init


# ================= v0.60: default build adds the contour through shape.shapeData.addContour =================
c,d=tp(P+"&stage=build",{"tri":MLayer2()}); print("180 default build   :",d["variant"],"| calls[-5:]",d["calls"][-5:],"| notes",d["notes"][-1:],"| built shape",d["built"]["shape"],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()}); print("181 attach          :",d["counts_match_expected"],"| addShape",CTRM["addShape"],"| calls[-3:]",d["calls"][-3:],"| after",d["state_after"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},sd_fails=True); print("182 shapeData.addContour raises:",d["failed_at"],"|",d["error"],"| addShape",CTRM["addShape"],"| attach not attempted:","layer.addShape(shape)" not in d["calls"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},sd_noeffect=True); print("183 shape does not report the contour:",d["failed_at"],"|",d["error"][:95],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},sd_none=True); print("184 shapeData is None:",d["failed_at"],"|",d["error"][:70],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=attach&variant=points",{"tri":MLayer2()}); print("185 variant=points keeps the old direct call:",d["calls"][-2:],"| shapeData in calls:", any("shapeData" in x for x in d["calls"]))
c,d=tp(P+"&stage=attach",{"tri":MLayer2(1,3)}); print("186 attach still refused on non-empty layer:",d["refused"],"| objects built",CTRM["shape"],"| addShape",CTRM["addShape"])
c,d=tp(P+"&stage=attach",{"tri":MLayer2()},add_raises=True); print("187 addShape raises after a good build:",d["failed_at"],"|",d["error"],"| calls[-2:]",d["calls"][-2:],"| after",d["state_after"]["shapes"],d["counts_match_expected"])


# ================= v0.61: /debug/trymetrics (names / read / set; only glyph names starting with "tri") =================
class QTransformStub: pass
qg.QTransform=QTransformStub
MM={"calls":[]}
class MetGlyph(TsGlyph):
    def update(self): MM["calls"].append("glyph.update")
class MetModern:
    def __init__(s,glyph,font):
        s.g=glyph; s.name=glyph.name; s.fgGlyphId=glyph.id
        s.activeLayer=MLayer2(1,3)
    def isValid(s): return True
    def update(s): MM["calls"].append("flGlyph.update")
    @property
    def advanceWidth(s): return s.g.width
    @advanceWidth.setter
    def advanceWidth(s,v):
        if MODE.get("adv_raises"): raise AttributeError("advanceWidth is read-only")
        s.g.width=v
    def getLSB(s,tr):
        if tr is None or MODE.get("getter_noarg"): raise IndexError("Unexpected SeqBase<T> length.")
        return s.g.leftMargin
    def getRSB(s,tr): return s.g.rightMargin
    def getSB(s,tr): return (s.g.leftMargin,s.g.rightMargin)
    def setLSB(s,v,mg,tr):
        MM["calls"].append(("setLSB",v,mg,type(tr).__name__)); s.g.leftMargin=v
        return True
    def setRSB(s,v,tr): MM["calls"].append(("setRSB",v,type(tr).__name__)); s.g.rightMargin=v; return True
    def invalidateView(s): raise SystemExit('CALLED invalidateView')
    def updateSidebearings(s,n):
        MM['calls'].append(('updateSidebearings',n)); return True
    def setSB(s,a,b,mg,al,tr): MM["calls"].append(("setSB",a,b,mg,al,type(tr).__name__)); return True
    def notAMetric(s): raise SystemExit("UNRELATED CALL")
def tmx(q,**mode):
    ts_reset(); ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0]=None
    MM["calls"].clear(); MODE.clear(); MODE.update(mode)
    TS.clear(); g=MetGlyph("tri",[TsLayer(1,3)]); g.width=0.0; g.leftMargin=0.0; g.rightMargin=-500.0; TS["tri"]=g
    TS["A"]=MetGlyph("A",[TsLayer(1,3)])
    _fm.flGlyph=MetModern
    c,d=call("/debug/trymetrics?"+q); return c,d,g
c,d,g=tmx("name=tri&stage=names"); print("190 names           :",c,"| legacy",d["legacy_names"],"| modern",d["modern_names"],"| calls",MM["calls"])
c,d,g=tmx("name=tri&stage=read"); print("191 read            :",c,d["state_before"]["legacy"],d["state_before"]["modern"]["advanceWidth"],d["state_before"]["modern_margins"]["lsb"],"| bbox",d["state_before"]["outline"]["fontlab_bbox"],"| calls",MM["calls"])
c,d,g=tmx("name=tri&stage=set&what=width&value=600"); print("192 set without go  :",c,d["error"][:40],"| width",g.width)
c,d,g=tmx("name=A&stage=set&go=yes&what=width&value=600"); print("193 not a tri glyph :",c,d["error"][:40],"| width",TS["A"].width)
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600"); print("194 legacy width    :",d["calls"],"| before",d["state_before"]["legacy"],"| after",d["state_after"]["legacy"],"| ink_moved",d["ink_moved"],"| w=l+ink+r",d["width_equals_lsb_ink_rsb"],d.get("lsb_plus_ink_plus_rsb"),"| may_change",d["font_may_have_changed"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=50"); print("195 legacy lsb (now refused, v0.62):",d.get("refused"),"| leftMargin untouched",g.leftMargin)
c,d,g=tmx("name=tri&stage=set&go=yes&what=rsb&value=50"); print("196 legacy rsb (now refused, v0.62):",d.get("refused"),"| rightMargin untouched",g.rightMargin)
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=50&route=modern"); print("197 modern lsb      :",d["calls"],"| modern calls",MM["calls"],"| after modern",d["state_after"]["modern_margins"]["lsb"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=700&route=modern"); print("198 modern width    :",d["calls"],"| width",g.width)
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=700&route=modern",adv_raises=True); print("199 advanceWidth refused:",d["failed_at"],"|",d["error"],"| width",g.width)
c,d,g=tmx("name=tri&stage=set&go=yes&what=sb&value=40&value2=60&route=modern"); print("200 modern sb two values:",d["calls"],"| modern calls",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=sb&value=40&route=legacy"); print("201 sb on legacy    :",d["error"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=abc"); print("202 bad value       :",d["error"],"| calls",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=99999"); print("203 out of range    :",d["error"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb"); print("204 no value        :",d["error"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=bogus&value=1"); print("205 bad what        :",d["error"])
c,d,g=tmx("name=tri&stage=bogus"); print("206 bad stage       :",d["error"][:30])
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=5&route=bogus"); print("207 bad route       :",d["error"][:30])
c,d,g=tmx("name=trinope&stage=read"); print("208 unknown tri glyph:",d["found"],d["reason"])
_fm.CurrentFont=lambda: None; c,d=call("/debug/trymetrics?name=tri&stage=read"); print("209 no font open    :",d)
_fm.CurrentFont=lambda: TsFont()
c,d=call("/version"); print("210 version         :",d)


# ================= v0.62: legacy lsb/rsb refused (crash), stage=doc =================
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=50&route=legacy"); print("220 legacy lsb refused:",d.get("refused"),d["error"][:60],"| leftMargin",g.leftMargin,"| calls",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=rsb&value=50&route=legacy"); print("221 legacy rsb refused:",d.get("refused"),"| rightMargin",g.rightMargin)
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=legacy"); print("222 legacy width still allowed:",d["calls"][0],"| width",g.width)
c,d,g=tmx("name=tri&stage=set&what=lsb&value=50&route=legacy"); print("223 legacy lsb without go:",d["error"][:40])
MetModern.setSB.__doc__="setSB(l, r, mg, al, tr) doc"
c,d,g=tmx("name=tri&stage=doc"); print("224 doc             :",c,"| legacy",{k:v.get("type") or v.get("error")[:20] for k,v in d["legacy_docs"].items()},"| modern",{k:(v.get("type"),v.get("doc")) if "type" in v else "err" for k,v in d["modern_docs"].items() if k.startswith("set")},"| calls",MM["calls"])
c,d,g=tmx("name=A&stage=doc"); print("225 doc not tri     :",d["error"][:30])


# ================= v0.63: QTransform argument for the modern getters / setters =================
c,d,g=tmx("name=tri&stage=read"); print("230 read, modern margins:",d["transform_source"],"|",d["state_before"]["modern_margins"],"| calls",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=rsb&value=100&route=modern"); print("231 modern rsb      :",d["calls"][0],"| returned",d.get("returned"),"| MM",MM["calls"][0],"| w=l+ink+r",d["width_equals_lsb_ink_rsb"],d.get("lsb_plus_ink_plus_rsb"),d.get("width_check_note"))
c,d,g=tmx("name=tri&stage=set&go=yes&what=sb&value=40&value2=60&route=modern"); print("232 modern sb       :",d["calls"][0],"| returned",d.get("returned"),"| MM",MM["calls"][0])
c,d,g=tmx("name=tri&stage=set&go=yes&what=sb&value=40&route=modern"); print("233 sb without value2:",d["failed_at"],"|",d["error"],"| MM",MM["calls"])
del qg.QTransform; _fm.QTransform=QTransformStub
c,d,g=tmx("name=tri&stage=read"); print("234 QTransform from fontlab module:",d["transform_source"])
del _fm.QTransform
c,d,g=tmx("name=tri&stage=set&go=yes&what=lsb&value=50&route=modern"); print("235 no QTransform anywhere:",d["transform_source"][:40],"|",d["failed_at"],"|",d["error"][:40],"| MM",MM["calls"][:1],"| margins",d["state_before"].get("modern_margins"))
qg.QTransform=QTransformStub
c,d,g=tmx("name=tri&stage=read",getter_noarg=True); print("236 getter error is reported:",d["state_before"]["modern_margins"].get("lsb_error"))
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=700&route=modern"); print("237 modern width unchanged path:",d["calls"][0],"| width",g.width)


# ================= v0.64: update switch, stage=refresh, legacy_layers =================
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=modern"); print("240 modern default: only flGlyph.update:",d["update_mode"],d["calls"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=modern&update=none"); print("241 update=none     :",d["update_mode"],d["calls"],"| MM",MM["calls"],"| width",g.width)
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=modern&update=glyph"); print("242 update=glyph    :",d["calls"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=modern&update=both"); print("243 update=both     :",d["calls"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=legacy"); print("244 legacy default  :",d["update_mode"],d["calls"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=set&go=yes&what=width&value=600&route=modern&update=bogus"); print("245 bad update      :",d["error"][:50],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=refresh"); print("246 refresh without go:",d["error"][:50],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=refresh&go=yes"); print("247 refresh         :",d["calls"],"| returned",d["returned"],"| MM",MM["calls"],"| margins after",d["state_after"]["modern_margins"],"| may_change",d["font_may_have_changed"])
c,d,g=tmx("name=A&stage=refresh&go=yes"); print("248 refresh, not tri:",d["error"][:40],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=read"); print("249 legacy_layers in snapshot:",d["state_before"]["legacy_layers"])


# ================= v0.65: refresh notify switch, update_names =================
c,d,g=tmx("name=tri&stage=refresh&go=yes"); print("250 refresh default notify:",d["calls"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=refresh&go=yes&notify=yes"); print("251 refresh notify=yes:",d["calls"],"| MM",MM["calls"],"| returned",d["returned"])
c,d,g=tmx("name=tri&stage=refresh&go=yes&notify=maybe"); print("252 bad notify     :",d["error"],"| MM",MM["calls"])
c,d,g=tmx("name=tri&stage=refresh&notify=yes"); print("253 notify=yes without go:",d["error"][:40],"| MM",MM["calls"])
class MLayerU(MLayer2):
    def refreshView(s): raise SystemExit("CALLED refreshView")
    def __init__(s,*a):
        MLayer2.__init__(s,*a); s.shapes=[type("Sh",(),{"isModified":lambda s: 1,"redrawNow":lambda s: 1})()]
class WsU:
    def updateAll(s): raise SystemExit("CALLED updateAll")
    def changedSomething(s): raise SystemExit("CALLED changedSomething")
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: WsU())})
c,d,g=tmx("name=tri&stage=names"); MM["calls"].clear()
_orig=MetModern.__init__
MetModern.__init__=lambda s,glyph,font: (_orig(s,glyph,font), setattr(s,"activeLayer",MLayerU(1,3)))[0]
c,d,g=tmx("name=tri&stage=names"); print("254 update_names   :",d["update_names"],"| calls",MM["calls"])
MetModern.__init__=_orig
del _fm.flWorkspace
c,d,g=tmx("name=tri&stage=names"); print("255 no workspace   :",d["update_names"]["flWorkspace_instance"][:60])
c,d,g=tmx("name=A&stage=names"); print("256 names not tri  :",d["error"][:30])


# ================= v0.66: stage=doc with target/members, stage=poke (allowlist, one call, no arguments) =================
PK={"calls":[]}
class PkShape:
    isChanged=False
    def changed(s): PK["calls"].append("shape.changed"); return None
    def update(s): PK["calls"].append("shape.update"); return True
    def blockUpdate(s): raise SystemExit("CALLED shape.blockUpdate")
class PkLayer(MLayer2):
    def __init__(s,*a):
        MLayer2.__init__(s,*a); s.shapes=[PkShape()]
    isChanged=False
    def changed(s): PK["calls"].append("layer.changed"); return None
    def update(s): PK["calls"].append("layer.update"); return None
class PkWs:
    def changed(s): PK["calls"].append("ws.changed"); return None
    def updateActiveViewport(s): PK["calls"].append("ws.updateActiveViewport"); return True
    def blockUpdate(s): raise SystemExit("CALLED blockUpdate")
    def unblockUpdate(s): raise SystemExit("CALLED unblockUpdate")
class PkModern(MetModern):
    def __init__(s,glyph,font): MetModern.__init__(s,glyph,font); s.activeLayer=PkLayer(1,3)
    isChanged=False
    def changed(s): PK["calls"].append("glyph.changed"); return None
    def updateFgGlyph(s,gid):
        PK["calls"].append(("glyph.updateFgGlyph",gid)); return True
    def updateActiveLayer(s,flag):
        PK["calls"].append(("glyph.updateActiveLayer",flag)); return None
def pk(q,**mode):
    PK["calls"].clear()
    c,d,g=tmx(q,**mode); return c,d
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: PkWs())})
def pk2(q,**mode):
    PK["calls"].clear(); ts_reset(); ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0]=None; MM["calls"].clear(); MODE.clear(); MODE.update(mode)
    TS.clear(); g=MetGlyph("tri",[TsLayer(1,3)]); g.width=0.0; g.leftMargin=0.0; g.rightMargin=-500.0; TS["tri"]=g; TS["A"]=MetGlyph("A",[TsLayer(1,3)])
    _fm.flGlyph=PkModern
    return call("/debug/trymetrics?"+q)
c,d=pk2("name=tri&stage=doc&target=workspace&members=updateActiveViewport,blockUpdate"); print("260 doc workspace  :",d["member_docs"],"| calls",PK["calls"])
c,d=pk2("name=tri&stage=doc&target=glyph&members=updateFgGlyph,updateActiveLayer,updateSidebearings"); print("261 doc glyph      :",{k:v.get("type") for k,v in d["member_docs"].items()},"| calls",PK["calls"])
c,d=pk2("name=tri&stage=doc&target=layer&members=update"); print("262 doc layer      :",d["member_docs"])
c,d=pk2("name=tri&stage=doc&target=shape&members=update"); print("263 doc shape      :",d["member_docs"])
c,d=pk2("name=tri&stage=doc&target=glyph&members=delete"); print("264 non-update member refused:",d["error"][:60])
c,d=pk2("name=tri&stage=doc&target=glyph&members=update;rm"); print("265 not an identifier:",d["error"])
c,d=pk2("name=tri&stage=doc&target=bogus&members=update"); print("266 bad target     :",d["error"][:40])
c,d=pk2("name=tri&stage=poke&target=workspace&member=updateActiveViewport"); print("267 poke without go:",d["error"][:40],"| calls",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=workspace&member=updateActiveViewport"); print("268 poke workspace :",d["calls"],"| returned",d["returned"],"| PK",PK["calls"],"| may_change",d["font_may_have_changed"],"| has before/after",("state_before" in d,"state_after" in d))
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateFgGlyph"); print("269 updateFgGlyph without arg (v0.67: refused):",d["error"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateFgGlyph&arg=auto"); print("270 updateFgGlyph arg=auto:",d["calls"],d["returned"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateActiveLayer&arg=yes"); print("271 updateActiveLayer arg=yes:",d["calls"],d["returned"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=layer&member=update"); print("272 poke layer.update:",d["returned"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=shape&member=update"); print("273 poke shape.update:",d["returned"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=workspace&member=blockUpdate"); print("274 blockUpdate refused:",d["error"][:50],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=workspace&member=unblockUpdate"); print("275 unblockUpdate refused:",d["error"][:50])
c,d=pk2("name=tri&stage=poke&go=yes&target=legacy&member=update"); print("276 legacy refused :",d["error"][:50])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=delete"); print("277 other member refused:",d["error"][:50])
c,d=pk2("name=A&stage=poke&go=yes&target=workspace&member=updateActiveViewport"); print("278 not tri        :",d["error"][:40],"| PK",PK["calls"])
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: (_ for _ in ()).throw(RuntimeError("no workspace")))})
c,d=pk2("name=tri&stage=poke&go=yes&target=workspace&member=updateActiveViewport"); print("279 workspace unavailable:",d["error"])


# ================= v0.67: changed() pokes, arg=, is_changed =================
_fm.flWorkspace=type("flWorkspace",(),{"instance":staticmethod(lambda: PkWs())})
for t,m in (("glyph","changed"),("layer","changed"),("shape","changed"),("workspace","changed")):
    c,d=pk2(f"name=tri&stage=poke&go=yes&target={t}&member={m}"); print(f"280 poke {t}.{m}:",d["calls"],d["returned"],"| PK",PK["calls"],"| is_changed before/after",d["state_before"]["is_changed"],d["state_after"]["is_changed"]["glyph"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateActiveLayer"); print("281 updateActiveLayer without arg:",d["error"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateActiveLayer&arg=maybe"); print("282 bad bool arg  :",d["error"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateFgGlyph&arg=7"); print("283 uint arg other than auto:",d["error"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=changed&arg=1"); print("284 arg given to a no-arg member:",d["error"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=glyph&member=updateActiveLayer&arg=no"); print("285 updateActiveLayer arg=no:",d["calls"],"| PK",PK["calls"])
c,d=pk2("name=tri&stage=poke&go=yes&target=legacy&member=modified"); print("286 legacy.modified still refused:",d["error"][:48])
c,d=pk2("name=tri&stage=read"); print("287 read has is_changed:",d["state_before"]["is_changed"])


# ================= v0.68: REAL TOOLS - GET/POST /glyph/sidebearings, POST /glyph/width on the modern route =================
def sbpost(path, payload):
    r = ns["_route"]("POST", path, json.dumps(payload).encode()); h, _, b = r.partition(b"\r\n\r\n")
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
SBX = {}
def sbx_reset(**kw):
    SBX.clear(); SBX.update(calls=[], vp=[], nolayer=False, nodes=3, adv=500.0, lsb=0.0, ink=500.0, adv_raises=False, adv_ignored=False,
                            setsb="ok", getter_raises=False, adv_moves_lsb=False, ws="ok")
    SBX.update(kw)
class SbLayerX:
    name = "L"
    def __init__(s, nodes): s.nodesCount = nodes; s.shapes = []
class SbModernX:
    def __init__(s, glyph, font):
        s.name = glyph.name; s.fgGlyphId = glyph.id
        s.activeLayer = None if SBX["nolayer"] else SbLayerX(SBX["nodes"])
        s._adv, s._lsb, s.ink = SBX["adv"], SBX["lsb"], SBX["ink"]
    def isValid(s): return True
    @property
    def advanceWidth(s): return s._adv
    @advanceWidth.setter
    def advanceWidth(s, v):
        SBX["calls"].append(("advanceWidth", v))
        if SBX["adv_raises"]: raise RuntimeError("advance refused")
        if not SBX["adv_ignored"]:
            s._adv = v + SBX.get("adv_off", 0.0)     # v0.197: adv_off fakes a width that lands elsewhere than asked
            if SBX["adv_moves_lsb"]: s._lsb += 1.0
    def getLSB(s, tr):
        if SBX["getter_raises"]: raise RuntimeError("getLSB refused")
        return s._lsb
    def getRSB(s, tr): return s._adv - s._lsb - s.ink
    def setSB(s, l, r, mg, al, tr):
        SBX["calls"].append(("setSB", l, r, mg, al, type(tr).__name__))
        mode = SBX["setsb"]
        if mode == "raises": raise RuntimeError("setSB refused")
        if mode == "ignore": return False
        if mode == "wrongadv":
            s._lsb = l; s._adv = l + s.ink + r + 5.0; return True
        old = (s._lsb, s._adv)
        s._lsb = l; s._adv = l + s.ink + r
        return old != (s._lsb, s._adv)
class SbWsX:
    def updateActiveViewport(s):
        if SBX["ws"] == "raises": raise RuntimeError("no viewport")
        SBX["vp"].append("updateActiveViewport")
def sbx_setup(glyph=None, **kw):
    sbx_reset(**kw)
    TS.clear(); ts_reset()
    TS["tri"] = glyph if glyph is not None else TsGlyph("tri", [TsLayer(1, 3)])
    TS["tri"].width = 500.0; TS["tri"].leftMargin = 1.5; TS["tri"].rightMargin = 2.5
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    _fm.flGlyph = SbModernX
    _fm.flWorkspace = type("flWorkspace", (), {"instance": staticmethod(lambda: SbWsX())})
    qg.QTransform = QTransformStub
def short_sb(d, keys): return {k: d.get(k) for k in keys}
_fm.CurrentFont = lambda: TsFont()
sbx_setup(adv=500.0, lsb=0.0)
c, d = call("/glyph/sidebearings?name=tri"); print("300 read sidebearings:", c, {k: d[k] for k in ("modern_layer", "readable", "lsb", "rsb", "advance", "ink_width", "layer_nodes")})
sbx_setup(adv=665.0, lsb=88.0)
c, d = call("/glyph/sidebearings?name=tri"); print("301 read 88/77/665   :", d["lsb"], d["rsb"], d["advance"], d["ink_width"], "| no writes:", SBX["calls"], SBX["vp"])
sbx_setup()
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77})
print("302 set 88/77        :", c, short_sb(d, ("set", "route", "changed", "expected_advance", "ink_width", "display_refreshed", "setter_returned")), "| checks", d["checks"])
print("303 before / after   :", d["before"], d["after"], "| calls", SBX["calls"], "| viewport", SBX["vp"], "| note starts:", d["display_note"][:30])
print("304 legacy untouched :", TS["tri"].width, TS["tri"].leftMargin, TS["tri"].rightMargin)
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77})
print("305 same values again:", d["set"], "| changed", d["changed"], "| setter_returned", d["setter_returned"])
sbx_setup(setsb="ignore")
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("306 setSB ignored    :", d["set"], "|", d["reason"], "|", d["checks"], "| changed", d["changed"])
sbx_setup(setsb="raises")
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("307 setSB raises     :", d["set"], "|", d["call_error"], "|", d["reason"][:50], "| before", d["before"], "after", d["after"])
sbx_setup(setsb="wrongadv")
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("308 advance mismatch :", d["set"], "|", d["reason"], "|", d["checks"], "| changed", d["changed"], "| after", d["after"])
sbx_setup(nolayer=True)
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("309 no modern layer  :", d["set"], d["modern_layer"], "|", d["reason"], "| calls", SBX["calls"], "| keys", sorted(d))
sbx_setup(nodes=0)
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("310 no outline       :", d["set"], "|", d["reason"][:60], "| calls", SBX["calls"])
sbx_setup(); del qg.QTransform
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 40, "right": 60})
print("311 no QTransform    :", d["set"], "|", d["reason"][:50], "| calls", SBX["calls"])
qg.QTransform = QTransformStub
sbx_setup()
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": -20, "right": 10})
print("312 negative left    :", d["set"], "| expected", d["expected_advance"], "| after", d["after"])
for label, payload in (("313 bool left        ", {"name": "tri", "left": True, "right": 5}), ("314 string right     ", {"name": "tri", "left": 5, "right": "7"}),
                       ("315 huge left        ", {"name": "tri", "left": 99999, "right": 5}), ("316 missing right    ", {"name": "tri", "left": 5}),
                       ("317 empty name       ", {"name": " ", "left": 5, "right": 5}), ("318 NaN left         ", {"name": "tri", "left": float("nan"), "right": 5})):
    sbx_calls = len(SBX["calls"]); c, d = sbpost("/glyph/sidebearings", payload); print(label, ":", c, d["error"], "| calls added", len(SBX["calls"]) - sbx_calls)
c, d = ns["_route"]("POST", "/glyph/sidebearings", b"{bad"), None
print("319 bad JSON         :", c.split(b"\r\n")[0].decode()[9:12])
c, d = sbpost("/glyph/sidebearings", {"name": "nope", "left": 5, "right": 5}); print("320 unknown glyph    :", c, d)
_fm.CurrentFont = lambda: None; c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 5, "right": 5}); print("321 no font open     :", d)
c, d = call("/glyph/sidebearings?name=tri"); print("322 no font, read    :", d)
_fm.CurrentFont = lambda: TsFont()
sbx_setup(ws="raises")
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77}); print("323 viewport fails   :", d["set"], "| display_refreshed", d["display_refreshed"], "| note still given:", bool(d["display_note"]))
sbx_setup(); del _fm.flGlyph
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77}); print("324 no flGlyph class :", d["set"], "|", d["reason"][:60], "| TS width", TS["tri"].width)
sbx_setup(getter_raises=True)
c, d = call("/glyph/sidebearings?name=tri"); print("325 getter raises    :", d["readable"], "|", d["reason"])
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77}); print("326 getter raises, set:", d["set"], "|", d["reason"][:60], "| calls", SBX["calls"])
sbx_setup(nolayer=True)
c, d = call("/glyph/sidebearings?name=tri"); print("327 read, no layer   :", d["modern_layer"], "|", d["reason"][:50], "| 'set' key absent:", "set" not in d)
c, d = call("/glyph/sidebearings"); print("328 read without name:", c, d["error"])
c, d = call("/glyph/sidebearings?name=nope"); print("329 read unknown     :", d)

# ---- POST /glyph/width on the modern route ----
sbx_setup()
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700})
print("330 width modern     :", short_sb(d, ("set", "route", "before", "after", "requested", "outline_untouched", "display_refreshed")), "| calls", SBX["calls"], "| viewport", SBX["vp"])
print("331 legacy untouched :", TS["tri"].width, "| TS_LOG", list(TS_LOG)[:3])
sbx_setup(adv_ignored=True)
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("332 width ignored    :", d["set"], "|", d["reason"], "| after", d["after"])
sbx_setup(adv_raises=True)
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("333 width raises     :", d["set"], "|", d["call_error"], "| after", d["after"])
sbx_setup(adv_moves_lsb=True)
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("334 lsb moved too    :", d["set"], "| outline_untouched", d["outline_untouched"], "|", d["warning"][:50])
sbx_setup(nolayer=True, glyph=TsGlyph("tri", []))
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("335 no layer, empty  :", d["set"], d["route"], "| legacy width", TS["tri"].width, "| MM calls", SBX["calls"])
sbx_setup(nolayer=True, glyph=TsGlyph("tri", [TsLayer(1, 3)]))
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("336 no layer, outline:", d["set"], "|", d["reason"][:60], "| before", d["before"], "| legacy width", TS["tri"].width)
sbx_setup(nolayer=True, glyph=TsGlyph("tri", [], comps=1))
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("337 no layer, component:", d["set"], "|", d["reason"][:40], "| legacy width", TS["tri"].width)
sbx_setup(ws="raises")
c, d = sbpost("/glyph/width", {"name": "tri", "width": 640}); print("338 viewport fails   :", d["set"], d["display_refreshed"])
c, d = sbpost("/glyph/width", {"name": "tri", "width": -1}); print("339 negative width   :", c, d["error"])
c, d = sbpost("/glyph/width", {"name": "nope", "width": 600}); print("340 unknown glyph    :", d)
_fm.CurrentFont = lambda: None; c, d = sbpost("/glyph/width", {"name": "tri", "width": 600}); print("341 no font          :", d)
_fm.CurrentFont = lambda: TsFont()
# ---- v0.197: whole units (rule B) and a width that moved but not to the request (AW 1449, AW2 1456) ----
_WK = ("set", "route", "before", "after", "requested", "width_rounded", "changed", "reason")
sbx_setup()
c, d = sbpost("/glyph/width", {"name": "tri", "width": 437.5}); print("341a 437.5 rounds up :", short_sb(d, _WK), "| calls", SBX["calls"], "| mark", "fontlab_changed_mark" in d)
print("341b OUTPUT line     :", ns["_act_describe_write"]("/glyph/width", {"name": "tri", "width": 437.5}, 200, d))
sbx_setup()
c, d = sbpost("/glyph/width", {"name": "tri", "width": 437.4}); print("341c 437.4 rounds down:", short_sb(d, _WK), "| calls", SBX["calls"])
sbx_setup()
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("341d whole number   :", short_sb(d, _WK), "| width_rounded absent:", "width_rounded" not in d)
sbx_setup(adv_off=1.0)
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("341e lands at 701   :", short_sb(d, _WK), "| mark", "fontlab_changed_mark" in d, "| synced key", "synced_with_fontlab" in d)
print("341f OUTPUT line     :", ns["_act_describe_write"]("/glyph/width", {"name": "tri", "width": 700}, 200, d))
sbx_setup(adv_ignored=True)
c, d = sbpost("/glyph/width", {"name": "tri", "width": 700}); print("341g unchanged      :", short_sb(d, _WK), "| mark", "fontlab_changed_mark" in d)
print("341h OUTPUT line     :", ns["_act_describe_write"]("/glyph/width", {"name": "tri", "width": 700}, 200, d))
sbx_setup(nolayer=True, glyph=TsGlyph("tri", []))
c, d = sbpost("/glyph/width", {"name": "tri", "width": 640.5}); print("341i legacy route rounds:", short_sb(d, _WK), "| legacy width", TS["tri"].width)
c, d = call("/version"); print("342 version          :", d)

# ================= v0.70: /debug/trylayer - the missing modern layer =================
LY = {}
def ly_reset(**kw):
    LY.clear(); LY.update(calls=[], fail=None, has=False, persist=True, newlayer=None); LY.update(kw)
LY_STORE = {}     # glyph id -> layer created (what FontLab's own data would keep)
class LyLayerX:
    def __init__(s, name="x"): s.name = name; s.nodesCount = 0; s.shapes = []
class LyModern:
    def __init__(s, glyph, font):
        s.name = glyph.name; s.fgGlyphId = glyph.id; s._id = glyph.id
        s.layers = []
        s._layer = LY_STORE.get(glyph.id) if LY["persist"] else None
        if LY["has"]: s._layer = LyLayerX("Master")
    @property
    def activeLayer(s): return s._layer
    @property
    def bodyLayer(s): return s._layer
    def hasBody(s): return s._layer is not None
    @property
    def advanceWidth(s): return 0.0
    def isValid(s): return True
    def getLSB(s, tr): return 0.0
    def getRSB(s, tr): return 0.0
    def findLayer(s, name, cs=None): LY["calls"].append(("findLayer", name)); return None
    def getLayerByName(s, name, create=False):
        LY["calls"].append(("getLayerByName", name, create))
        if LY["fail"] == "raise": raise RuntimeError("refused")
        if create:
            s._layer = LyLayerX(name); LY_STORE[s._id] = s._layer; s.layers.append(s._layer); return s._layer
        return None
    def findLayerCreate(s, name, cs=None):
        LY["calls"].append(("findLayerCreate", name))
        if LY["fail"] == "raise": raise RuntimeError("refused")
        if LY["fail"] == "none": return None
        s._layer = LyLayerX(name); LY_STORE[s._id] = s._layer; s.layers.append(s._layer); return s._layer
    def addLayer(s, layer, back=False):
        LY["calls"].append(("addLayer", getattr(layer, "name", None), back)); s._layer = layer; s.layers.append(layer)
class LyFlLayer(LyLayerX): pass
def ly_setup(glyph=None, **kw):
    ly_reset(**kw); LY_STORE.clear()
    TS.clear(); ts_reset()
    TS["tri"] = glyph if glyph is not None else TsGlyph("tri", [])
    TS["opened"] = TsGlyph("opened", [TsLayer(1, 3)])
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    _fm.flGlyph = LyModern; _fm.flLayer = LyFlLayer
    qg.QTransform = QTransformStub
def ly_short(d, keys): return {k: d.get(k) for k in keys}
ly_setup()
c, d = call("/debug/trylayer?name=tri&stage=state&layer=Master&ref=opened")
print("343 state            :", c, d["modern_before"]["activeLayer"], d["modern_before"]["layers_len"], "| findLayer", d["findLayer"], "| nocreate", d["getLayerByName_no_create"], "| ref", d["ref"]["found"], "| calls", LY["calls"])
ly_setup(); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master"); print("344 create without go:", c, d["error"][:40], "| calls", LY["calls"])
ly_setup(); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes")
print("345 findLayerCreate  :", c, d["call"], "| returned", d["returned"], "| same", d["modern_after_same_wrapper"]["activeLayer"], "| rebuilt", d["rebuilt_wrapper"], d["modern_after_rebuilt_wrapper"]["activeLayer"], "| margins", d["margins_same_wrapper"])
ly_setup(); c, d = call("/debug/trylayer?name=tri&stage=create&method=getLayerByName&layer=Master&go=yes"); print("346 getLayerByName   :", d["call"], "|", d["returned"], "| calls", LY["calls"])
ly_setup(); c, d = call("/debug/trylayer?name=tri&stage=create&method=addLayer&layer=Master&go=yes"); print("347 addLayer         :", d["call"], "|", d["returned"], "| calls", LY["calls"])
ly_setup(persist=False); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes")
LY_STORE.clear(); ly_setup(fail="raise"); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes"); print("348 call raises      :", d["call_error"], "| after", d["modern_after_same_wrapper"]["activeLayer"])
ly_setup(fail="none"); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes"); print("349 returns None     :", d["returned"], "| after", d["modern_after_same_wrapper"]["activeLayer"])
ly_setup(has=True); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes"); print("350 already has layer:", d.get("refused"), d["error"][:50], "| calls", LY["calls"])
ly_setup(glyph=TsGlyph("tri", [TsLayer(1, 3)])); c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes"); print("351 not empty        :", d.get("refused"), d["error"][:40], "| calls", LY["calls"])
ly_setup(); c, d = call("/debug/trylayer?name=tri&stage=create&method=bogus&layer=Master&go=yes"); print("352 bad method       :", d["error"][:30])
c, d = call("/debug/trylayer?name=tri&stage=create&method=addLayer&go=yes"); print("353 no layer name    :", d["error"])
c, d = call("/debug/trylayer?name=tri&stage=create&method=addLayer&layer=a%3Bb&go=yes"); print("354 bad layer name   :", d["error"][:30], "| calls", LY["calls"])
c, d = call("/debug/trylayer?name=tri&stage=bogus"); print("355 bad stage        :", d["error"])
c, d = call("/debug/trylayer"); print("356 no name          :", c)
c, d = call("/debug/trylayer?name=nope&stage=state"); print("357 unknown glyph    :", d)
_fm.CurrentFont = lambda: None; c, d = call("/debug/trylayer?name=tri&stage=state"); print("358 no font          :", d)
_fm.CurrentFont = lambda: TsFont()
c, d = call("/version"); print("359 version          :", d)

# ================= v0.71: /debug/trylayer stage=state - font_master =================
class FmLayer:
    name = "test_font"; id = 7; isMasterLayer = True
    def isBodyLayer(s): return False
    def mutate(s): raise AssertionError("must never be called")
class FmFont(TsFont):
    master = FmLayer()
class FmNoneFont(TsFont):
    master = None
class FmRaisesFont(TsFont):
    @property
    def master(s): raise RuntimeError("no master")
ly_setup()
_fm.CurrentFont = lambda: FmFont()
c, d = call("/debug/trylayer?name=tri&stage=state")
print("360 font_master      :", c, d["font_master"])
c, d = call("/debug/trylayer?name=nope&stage=state"); print("361 master, no glyph :", d["found"], d["font_master"]["name"])
c, d = call("/debug/trylayer?name=tri&stage=create&method=findLayerCreate&layer=Master&go=yes"); print("362 create has no section:", "font_master" in d)
_fm.CurrentFont = lambda: FmNoneFont(); c, d = call("/debug/trylayer?name=tri&stage=state"); print("363 master is None   :", d["font_master"])
_fm.CurrentFont = lambda: FmRaisesFont(); c, d = call("/debug/trylayer?name=tri&stage=state"); print("364 master raises    :", d["font_master"])
_fm.CurrentFont = lambda: TsFont(); c, d = call("/debug/trylayer?name=tri&stage=state"); print("365 no master member :", d["font_master"])
c, d = call("/version"); print("366 version          :", d)

# ================= v0.72: automatic layer creation, POST /glyph/polygon, reader modern_check =================
P72 = {"layers": {}, "calls": [], "mode": {}}
class P72Layer:
    def __init__(s, name, shapes=0, nodes=0): s.name = name; s._sh = shapes; s._n = nodes; s._contours = []
    def getContours(s):
        m = P72["mode"].get("contours_type")
        if m == "raises": raise IndexError("Unexpected SeqBase<T> length.")
        if m == "native": return NativeSeq()
        return tuple(s._contours) if m == "tuple" else list(s._contours)
    def shapesCount(s): return s._sh
    def nodesCount(s): return s._n
    def componentsCount(s): return 0
    def addShape(s, shape):
        P72["calls"].append("addShape")
        if P72["mode"].get("add_raises"): raise RuntimeError("addShape boom")
        s._sh += 1; s._n += shape.n + P72["mode"].get("extra_nodes", 0); s._contours.extend(shape.contours)
class NativeSeq:
    def __getitem__(s, i): raise SystemExit("NATIVE OBJECT WAS INDEXED")
    def __len__(s): return 1
class P72Pt:
    def __init__(s, x, y): s.x, s.y = x, y
class P72Node:
    def __init__(s, pt, i): s._pt = pt; s.index = i; s.x = pt.x; s.y = pt.y; s.smooth = False
    def isOn(s): return True
    def isOff(s): return False
    def isCurve(s): return False
class P72Contour:
    def __init__(s, pts):
        P72["calls"].append("flContour")
        if P72["mode"].get("contour_raises"): raise RuntimeError("contour boom")
        s.pts = pts; s._closed = False; s.clockwise = True
    def getNodeAt(s, i):
        m = P72["mode"]
        if m.get("node_raises") == i: raise RuntimeError("getNodeAt boom")
        if m.get("node_none") == i: return None
        nd = P72Node(s.pts[i], i)
        if m.get("x_text") == i: nd.x = "ten"
        if m.get("off_node") == i: nd.isOn = lambda: False; nd.isOff = lambda: True; nd.isCurve = lambda: True
        return nd
    @property
    def closed(s): return s._closed
    @closed.setter
    def closed(s, v): s._closed = False if P72["mode"].get("noclose") else v
    def nodesCount(s): return len(s.pts)
class P72ShapeData:
    def __init__(s, shape): s.shape = shape
    def addContour(s, c):
        m = P72["mode"]
        if m.get("addcontour_raises_second") and s.shape.contours: raise IndexError("Unexpected SeqBase<T> length.")
        if m.get("drop_second") and s.shape.contours: return
        s.shape.n += c.nodesCount(); s.shape.contours.append(c)
class P72Shape:
    def __init__(s): s.n = 0; s.contours = []; s.shapeData = P72ShapeData(s)
class P72Mod:
    def __init__(s, glyph, font):
        s.name = glyph.name; s.fgGlyphId = glyph.id
    def isValid(s): return True
    @property
    def activeLayer(s):
        if s.name in P72["mode"].get("inactive", ()): return None       # v0.82 tests: the wrapper reports no active layer although one exists
        return P72["layers"].get(s.name)
    @property
    def layers(s):      # v0.187: the glyph's layers, the active one only (the v0.181 fakes below replace it with the full model)
        if s.name in P72.get("layers_unreadable", ()): raise RuntimeError("layers boom")
        lay = P72["layers"].get(s.name)
        return [lay] if lay is not None else []
    def _ask(s, name):                                                    # read-only question: does a layer of this name exist? (not logged)
        if P72["mode"].get("ask_raises"): raise RuntimeError("ask boom")
        lay = P72["layers"].get(s.name)
        return lay if (lay is not None and lay.name == name and not P72["mode"].get("ask_blind")) else None
    @property
    def getLayerByName(s):
        if P72["mode"].get("ask_missing"): raise AttributeError("getLayerByName")
        return lambda name, create=False: s._ask(name)
    @property
    def findLayer(s):
        if P72["mode"].get("ask_missing_find"): raise AttributeError("findLayer")
        return lambda name: s._ask(name)
    @property
    def advanceWidth(s): return P72.setdefault("widths", {}).get(s.name, 0.0)
    @advanceWidth.setter
    def advanceWidth(s, v): P72["calls"].append(("advanceWidth", s.name, v)); P72.setdefault("widths", {})[s.name] = v
    def findLayerCreate(s, name, cs=None):
        P72["calls"].append(("findLayerCreate", s.name, name))
        m = P72["mode"].get("create")
        if m == "raises": raise RuntimeError("findLayerCreate boom")
        if m == "nolayer": return None
        P72["layers"][s.name] = P72Layer(name)
        return P72["layers"][s.name]
    def getLSB(s, tr): return 0.0
    def getRSB(s, tr): return 0.0
    def setSB(s, *a): P72["calls"].append("setSB")
def p72_setup(refs=(("ref", "test_font"),), empties=("fresh",), mode=None, extra_glyphs=()):
    ts_reset(); TS.clear()
    P72["layers"].clear(); P72["calls"].clear(); P72["mode"].clear(); P72["widths"] = {}; P72["mode"].update(mode or {})
    for gname, lname in refs:
        TS[gname] = TsGlyph(gname, [TsLayer(1, 3)]); P72["layers"][gname] = P72Layer(lname, 1, 3)
    for gname in empties: TS[gname] = TsGlyph(gname, [])
    for g in extra_glyphs: TS[g.name] = g
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    _fm.CurrentFont = lambda: TsFont()
    _fm.flGlyph = P72Mod; _fm.flContour = P72Contour; _fm.flShape = P72Shape
    _fm.flWorkspace = type("flWorkspace", (), {"instance": staticmethod(lambda: SbWsX())}); SBX.clear(); SBX.update(ws="ok", vp=[])
    qc.QPointF = P72Pt; qg.QTransform = QTransformStub
def p72_post(path, payload):
    return sbpost(path, payload)
TRI4 = [[0, 0], [400, 0], [400, 300], [0, 300]]
p72_setup()
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600})
print("400 width, new glyph  :", c, short_sb(d, ("set", "route", "layer_created", "before", "after")), "| calls", P72["calls"])
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 610})
print("401 width again       :", d["set"], d["route"], "| layer_created" , d.get("layer_created"), "| creates", sum(1 for x in P72["calls"] if isinstance(x, tuple) and x[0] == "findLayerCreate"))
p72_setup(refs=(("r1", "Alpha"), ("r2", "Beta")))
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600})
print("402 names disagree    :", d["set"], d["route"], "|", d["layer_create_note"][:60], "| creates", [x for x in P72["calls"] if isinstance(x, tuple) and x[0] == "findLayerCreate"], "| legacy width", TS["fresh"].width)
p72_setup(refs=())
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600}); print("403 no reference layer:", d["set"], d["route"], "|", d["layer_create_note"][:50])
p72_setup(mode={"create": "raises"})
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600}); print("404 create raises     :", d["set"], d["route"], "|", d["layer_create_note"])
p72_setup(mode={"create": "nolayer"})
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600}); print("405 create, no layer  :", d["set"], d["route"], "|", d["layer_create_note"][:60])
p72_setup(extra_glyphs=(TsGlyph("outlined", [TsLayer(1, 3)]),))
c, d = p72_post("/glyph/width", {"name": "outlined", "width": 600}); print("406 outline, no layer :", d["set"], "|", d["reason"][:50], "| creates", len([x for x in P72["calls"] if isinstance(x, tuple)]))
p72_setup(refs=(("r1", "test_font"),))
c, d = p72_post("/glyph/sidebearings", {"name": "fresh", "left": 10, "right": 10}); print("407 sidebearings, empty:", d["set"], "|", d["reason"][:60], "| calls", P72["calls"])
c, d = call("/glyph/sidebearings?name=fresh"); print("408 read sb, empty    :", d["modern_layer"], "|", d["reason"][:40], "| calls", P72["calls"])

# ---- POST /glyph/polygon ----
p72_setup()
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
print("410 polygon, new glyph:", c, short_sb(d, ("drawn", "layer_created", "points", "changed", "checks", "ink_width")), "| after", d["state_after"], "| margins", d["margins"], "| note", d["display_note"][:28], "| viewport", SBX["vp"])
print("411 calls             :", P72["calls"])
p72_setup(empties=("fresh",), mode={})
P72["layers"]["fresh"] = P72Layer("test_font")
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": [[0, 0], [10.5, 0], [5, 20]]}); print("412 layer exists      :", d["drawn"], "| layer_created" , d.get("layer_created"), "| after", d["state_after"])
p72_setup(); P72["layers"]["fresh"] = P72Layer("test_font", 1, 3)
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("413 layer not empty   :", d["drawn"], "|", d["reason"][:60], "| calls", P72["calls"])
p72_setup(mode={"contour_raises": 1})
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("414 flContour raises  :", d["drawn"], "|", d["reason"], "| changed", d["changed"], "| shapes", d["state_after"]["shapes"])
p72_setup(mode={"add_raises": 1})
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("415 addShape raises   :", d["drawn"], "|", d["reason"], "| changed", d["changed"])
p72_setup(mode={"noclose": 1})
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("416 contour not closed:", d["drawn"], "|", d["reason"][:55], "| addShape calls", P72["calls"].count("addShape"))
p72_setup(mode={"extra_nodes": 2})
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("417 node count wrong  :", d["drawn"], "|", d["reason"], "| changed", d["changed"], "| checks", d["checks"])
p72_setup(extra_glyphs=(TsGlyph("outlined", [TsLayer(1, 3)]),))
c, d = p72_post("/glyph/polygon", {"name": "outlined", "points": TRI4}); print("418 outline, no layer :", d["drawn"], "|", d["reason"][:45], "| calls", P72["calls"])
p72_setup(refs=())
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("419 no layer name     :", d["drawn"], "|", d["reason"][:70])
c, d = p72_post("/glyph/polygon", {"name": "nope", "points": TRI4}); print("420 unknown glyph     :", d)
_fm.CurrentFont = lambda: None; c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("421 no font           :", d)
_fm.CurrentFont = lambda: TsFont()
for label, payload in (("422 points missing   ", {"name": "fresh"}), ("423 two points        ", {"name": "fresh", "points": [[0, 0], [1, 1]]}),
                       ("424 501 points        ", {"name": "fresh", "points": [[i, i * 2] for i in range(501)]}),
                       ("425 bool coordinate   ", {"name": "fresh", "points": [[True, 0], [5, 0], [5, 5]]}),
                       ("426 string coordinate ", {"name": "fresh", "points": [["0", 0], [5, 0], [5, 5]]}),
                       ("427 NaN coordinate    ", {"name": "fresh", "points": [[float("nan"), 0], [5, 0], [5, 5]]}),
                       ("428 huge coordinate   ", {"name": "fresh", "points": [[20001, 0], [5, 0], [5, 5]]}),
                       ("429 point of 3 numbers", {"name": "fresh", "points": [[0, 0, 0], [5, 0], [5, 5]]}),
                       ("430 two distinct only ", {"name": "fresh", "points": [[0, 0], [5, 5], [0, 0], [5, 5]]}),
                       ("431 empty name        ", {"name": " ", "points": TRI4})):
    n0 = len(P72["calls"]); c, d = p72_post("/glyph/polygon", payload); print(label, ":", c, d["error"], "| calls added", len(P72["calls"]) - n0)
r = ns["_route"]("POST", "/glyph/polygon", b"{bad"); print("432 bad JSON          :", r.split(b"\r\n")[0].decode()[9:12])

# ---- reader: modern_check ----
p72_setup()
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
c, d = call("/glyph/outline?name=fresh"); print("433 reader, API-drawn :", d["node_count"], "| modern_check", d["modern_check"])
TS["ref"].leftMargin, TS["ref"].rightMargin, TS["ref"].width = 0.0, 0.0, 0.0     # v0.88: the fake's modern margins are 0 / 0 / 0, so the legacy ones must agree for "agree" to stay true
c, d = call("/glyph/outline?name=ref"); print("434 reader, agree     :", d["node_count"], "| modern_check", d["modern_check"])
c, d = call("/glyph/outline?name=ref&modern=no"); print("435 reader, modern=no :", "modern_check" in d)
p72_setup(extra_glyphs=(TsGlyph("outlined", [TsLayer(1, 3)]),))
c, d = call("/glyph/outline?name=outlined"); print("436 reader, no modern :", d["node_count"], "| modern_check", d["modern_check"])
c, d = call("/version"); print("437 version           :", d)

# ================= v0.73: /debug/readmodern - reading the modern outline back (read-only) =================
class R73Node:
    def __init__(s, i, x, y, on=True): s._i, s.x, s.y, s._on = i, x, y, on; s.smooth = False
    def isOn(s): return s._on
    def isOff(s): return not s._on
    def isCurve(s): return False
    @property
    def index(s): return s._i
class R73Contour:
    def __init__(s, pts): s._nodes = [R73Node(i, x, y) for i, (x, y) in enumerate(pts)]; s.closed = True; s.clockwise = False
    def nodesCount(s): return len(s._nodes)
    @property
    def nodes(s): return list(s._nodes)
    def getNodeAt(s, i):
        P72["calls"].append(("getNodeAt", i))
        if P72["mode"].get("getnode_raises"): raise RuntimeError("getNodeAt boom")
        return None if P72["mode"].get("getnode_none") else s._nodes[i]
    def at(s, i): P72["calls"].append(("at", i)); return s._nodes[i]
class R73Native:                 # a native-like container: not a list, must never be indexed
    def __len__(s): return 2
    def __getitem__(s, i): raise SystemExit("NATIVE OBJECT INDEXED")
class R73Layer(P72Layer):
    def getContours(s):
        m = P72["mode"].get("contours")
        if m == "raises": raise RuntimeError("getContours boom")
        if m == "native": return R73Native()
        return [R73Contour([(0, 0), (400, 0), (400, 300), (0, 300)])]
    def getShapes(s): return [object()]
    @property
    def shapes(s): return R73Native()
P72["rm"] = True
def r73_setup(**mode):
    p72_setup(refs=(), empties=("fresh",), mode=mode)
    P72["layers"]["fresh"] = R73Layer("test_font", 1, 4)
def rm(q): return call("/debug/readmodern?" + q)
r73_setup(); c, d = rm("name=fresh&stage=layer")
print("440 stage=layer       :", c, d["layer_state"]["shapes"], "| getContours", d["getContours()"], "| getShapes", d["getShapes()"], "| shapes", d["shapes"], "| shapesCount", d["shapesCount"])
r73_setup(); c, d = rm("name=fresh&stage=contour&index=0")
print("441 stage=contour     :", d["contours"], d["closed"], d["clockwise"], d["nodesCount"], d["nodes"])
r73_setup(); c, d = rm("name=fresh&stage=node&index=0&node=2&via=getNodeAt")
print("442 node via getNodeAt:", d["node"], "| calls", P72["calls"])
r73_setup(); c, d = rm("name=fresh&stage=node&index=0&node=3&via=at"); print("443 node via at       :", d["node"]["x"], d["node"]["y"], d["node"]["isOn"], "| calls", P72["calls"])
r73_setup(); c, d = rm("name=fresh&stage=node&index=0&node=4&via=at"); print("444 node out of range :", d["error"], "| calls", P72["calls"])
r73_setup(); c, d = rm("name=fresh&stage=contour&index=3"); print("445 contour out of range:", d["error"])
r73_setup(contours="native"); c, d = rm("name=fresh&stage=contour&index=0"); print("446 native container   :", d["error"][:70])
r73_setup(contours="native"); c, d = rm("name=fresh&stage=layer"); print("447 layer, native      :", d["getContours()"], "| shapes", d["shapes"])
r73_setup(contours="raises"); c, d = rm("name=fresh&stage=contour&index=0"); print("448 getContours raises :", d["error"])
r73_setup(getnode_raises=1); c, d = rm("name=fresh&stage=node&index=0&node=0&via=getNodeAt"); print("449 getNodeAt raises   :", d["error"])
r73_setup(getnode_none=1); c, d = rm("name=fresh&stage=node&index=0&node=0&via=getNodeAt"); print("450 getNodeAt None     :", d["node"])
r73_setup(); c, d = rm("name=fresh&stage=node&index=0&node=0"); print("451 no via             :", c, d["error"])
r73_setup(); c, d = rm("name=fresh&stage=node&index=0&node=0&via=nodes"); print("452 bad via            :", d["error"])
r73_setup(); c, d = rm("name=fresh&stage=bogus"); print("453 bad stage          :", d["error"])
r73_setup(); c, d = rm("name=fresh&stage=contour&index=x"); print("454 bad index          :", c, d["error"])
r73_setup(); c, d = rm("name=fresh&stage=contour&index=10000"); print("455 index too big      :", c, d["error"])
r73_setup(); c, d = rm("name=fresh&stage=contour&index=-1"); print("456 negative index     :", c, d["error"])
c, d = call("/debug/readmodern"); print("457 no name            :", c)
c, d = rm("name=nope&stage=layer"); print("458 unknown glyph      :", d)
r73_setup(); P72["layers"].pop("fresh"); c, d = rm("name=fresh&stage=layer"); print("459 no modern layer    :", d["error"])
_fm.CurrentFont = lambda: None; c, d = rm("name=fresh&stage=layer"); print("460 no font            :", d)
_fm.CurrentFont = lambda: TsFont()
r73_setup(); c, d = rm("name=fresh&stage=layer"); print("461 read-only          : calls", P72["calls"], "| shapes still", P72["layers"]["fresh"].shapesCount())
c, d = call("/version"); print("462 version           :", d)

# ================= v0.74: GET /glyph/outline - modern_outline =================
HOUSE = [[10, 20], [410, 20], [410, 220], [210, 320], [10, 220]]
def mo_get(name="fresh"):
    c, d = call("/glyph/outline?name=" + name); return d
p72_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE})
d = mo_get(); mo = d["modern_outline"]
print("470 modern_outline    :", mo["available"], "| nodes", mo["node_count"], "of", mo["expected_node_count"], "| margins", mo["margins"], "| check agree", d["modern_check"]["agree"])
print("471 contour 0         :", {k: v for k, v in mo["contours"][0].items() if k != "nodes"})
print("472 nodes             :", [(n["x"], n["y"], n["isOn"]) for n in mo["contours"][0]["nodes"]])
p72_setup(); TS["ref"].leftMargin, TS["ref"].rightMargin, TS["ref"].width = 0.0, 0.0, 0.0; d = mo_get("ref"); print("473 legacy agrees     : modern_outline present:", "modern_outline" in d, "| agree", d["modern_check"]["agree"])
p72_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); c, d = call("/glyph/outline?name=fresh&modern=no")
print("474 modern=no         : modern_check", "modern_check" in d, "| modern_outline", "modern_outline" in d)
p72_setup(mode={"contours_type": "tuple"}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("475 tuple accepted    :", mo_get()["modern_outline"]["available"])
p72_setup(mode={"contours_type": "native"}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("476 native sequence   :", mo_get()["modern_outline"])
p72_setup(mode={"contours_type": "raises"}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("477 getContours raises:", mo_get()["modern_outline"])
p72_setup(mode={"node_raises": 2}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("478 getNodeAt raises  :", mo_get()["modern_outline"])
p72_setup(mode={"node_none": 3}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("479 getNodeAt None    :", mo_get()["modern_outline"])
p72_setup(mode={"x_text": 1}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("480 x is text         :", mo_get()["modern_outline"])
p72_setup(mode={"off_node": 1}); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); n = mo_get()["modern_outline"]["contours"][0]["nodes"][1]; print("481 off-curve node    :", n["isOn"], n["isOff"], n["isCurve"])
p72_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); P72["layers"]["fresh"]._n = 6; print("482 count mismatch    :", mo_get()["modern_outline"])
p72_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); ns["_MODERN_OUTLINE_MAX_NODES"] = 3; print("483 too many nodes    :", mo_get()["modern_outline"]); ns["_MODERN_OUTLINE_MAX_NODES"] = 5000
del qg.QTransform; p72_setup(); del qg.QTransform; p72_post("/glyph/polygon", {"name": "fresh", "points": HOUSE}); print("484 no QTransform     : margins key", "margins" in mo_get()["modern_outline"], "| available", mo_get()["modern_outline"]["available"])
qg.QTransform = QTransformStub
c, d = call("/version"); print("485 version           :", d)

# ================= v0.75: POST /glyph/polygon with "contours" =================
OUTER = [[0, 0], [300, 0], [300, 300], [0, 300]]
HOLE = [[100, 100], [100, 200], [200, 200], [200, 100]]
p72_setup(); n0 = len(P72["calls"])
c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]})
print("490 two contours      :", c, short_sb(d, ("drawn", "points", "contours", "contour_sizes", "changed", "checks", "layer_created")), "| after", d["state_after"])
print("491 calls             :", P72["calls"])
d2 = mo_get(); print("492 read back         :", d2["modern_outline"]["available"], "| contours", len(d2["modern_outline"]["contours"]), [len(c["nodes"]) for c in d2["modern_outline"]["contours"]])
p72_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": OUTER}); print("493 points still works:", d["drawn"], d["contours"], d["contour_sizes"], d["checks"])
for label, payload in (("494 points and contours", {"name": "fresh", "points": OUTER, "contours": [OUTER]}), ("495 neither           ", {"name": "fresh"}),
                       ("496 empty contours    ", {"name": "fresh", "contours": []}), ("497 21 contours        ", {"name": "fresh", "contours": [OUTER] * 21}),
                       ("498 contours not list ", {"name": "fresh", "contours": "abc"}), ("499 contour of 2 points", {"name": "fresh", "contours": [OUTER, [[0, 0], [1, 1]]]}),
                       ("500 contour not list  ", {"name": "fresh", "contours": [OUTER, 5]}), ("501 two distinct in one", {"name": "fresh", "contours": [OUTER, [[0, 0], [5, 5], [0, 0]]]}),
                       ("502 bad coordinate    ", {"name": "fresh", "contours": [OUTER, [[0, 0], [5, "x"], [5, 5]]]}),
                       ("503 2500 points total ", {"name": "fresh", "contours": [[[i, i * 2] for i in range(500)]] * 5})):
    n1 = len(P72["calls"]); c, d = p72_post("/glyph/polygon", payload); print(label, ":", c, d["error"], "| calls added", len(P72["calls"]) - n1)
p72_setup(mode={"contour_raises": 1}); c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]}); print("504 first flContour raises:", d["drawn"], "|", d["reason"][:60], "| addShape", P72["calls"].count("addShape"))
class _Cnt: pass
p72_setup(mode={"addcontour_raises_second": 1}); c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]}); print("505 second addContour raises:", d["drawn"], "|", d["reason"][:70], "| changed", d["changed"], "| addShape", P72["calls"].count("addShape"))
p72_setup(mode={"drop_second": 1}); c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]}); print("506 second contour dropped:", d["drawn"], "|", d["reason"], "| changed", d["changed"], "| checks", d["checks"])
p72_setup(mode={"contours_type": "raises"}); c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]}); print("507 getContours unreadable:", d["drawn"], "| checks", d["checks"])
p72_setup(); P72["layers"]["fresh"] = P72Layer("test_font", 1, 3); c, d = p72_post("/glyph/polygon", {"name": "fresh", "contours": [OUTER, HOLE]}); print("508 not empty         :", d["drawn"], "|", d["reason"][:50], "| calls", P72["calls"])
c, d = call("/version"); print("509 version           :", d)

# ================= v0.76: /debug/tryshape variant=curve (detached square, convertToCurve ONCE on node 1, nodes read before and after) =================
CV = {"mode": {}, "log": []}
def _cv_r(v, *modes):                       # live (v0.78): FontLab ROUNDS fractional coordinates (setPoint at least); the stub rounds only when asked
    return float(round(v)) if any(CV["mode"].get(m) for m in modes) else v
class CvPt:
    def __init__(s, x, y): s.x = x; s.y = y
class CvNode:
    def __init__(s, c, i): s.c = c; s.i = i
    @property
    def x(s): return s.c.nodes[s.i]["x"]
    @x.setter
    def x(s, v):
        if not CV["mode"].get("settable"): raise AttributeError("can't set attribute")
        s.c.nodes[s.i]["x"] = _cv_r(v, "round_all"); s._pair()
    @property
    def y(s): return s.c.nodes[s.i]["y"]
    @y.setter
    def y(s, v):
        if not CV["mode"].get("settable"): raise AttributeError("can't set attribute")
        s.c.nodes[s.i]["y"] = _cv_r(v, "round_all"); s._pair()
    @property
    def position(s): return CvPt(s.c.nodes[s.i]["x"], s.c.nodes[s.i]["y"])
    @position.setter
    def position(s, p):
        if not CV["mode"].get("settable"): raise AttributeError("can't set attribute")
        s.c.nodes[s.i]["x"] = _cv_r(p.x, "round_all"); s.c.nodes[s.i]["y"] = _cv_r(p.y, "round_all")
    @property
    def type(s): return "on" if s.c.nodes[s.i]["on"] else "curve"      # live (v0.76): the strings "on" and "curve"
    @property
    def smooth(s): return bool(s.c.nodes[s.i].get("smooth", False))
    @smooth.setter
    def smooth(s, v):
        if not CV["mode"].get("smooth_settable"): raise AttributeError("can't set attribute")
        s.c.nodes[s.i]["smooth"] = bool(v)
    def _pair(s):                    # stub ASSUMPTION (mode smooth_pairs): a handle next to a smooth on-curve node drags its partner through the node
        n = s.c.nodes
        if CV["mode"].get("smooth_pairs") and not n[s.i]["on"] and s.i + 2 < len(n) and n[s.i + 1]["on"] and n[s.i + 1].get("smooth") and not n[s.i + 2]["on"]:
            n[s.i + 2]["x"] = 2 * n[s.i + 1]["x"] - n[s.i]["x"]; n[s.i + 2]["y"] = 2 * n[s.i + 1]["y"] - n[s.i]["y"]
    @property
    def index(s): return s.i
    def isOn(s): return s.c.nodes[s.i]["on"]
    def isOff(s): return False                                          # live (v0.76): a cubic handle is NOT isOff
    def isCurve(s): return not s.c.nodes[s.i]["on"]
    def moveBy(s, dx, dy, round=False):
        CV["log"].append(("moveBy", s.i, dx, dy))
        if CV["mode"].get("moveby_raises"): raise RuntimeError("moveBy boom")
        if CV["mode"].get("moveby_noeffect"): return None
        s.c.nodes[s.i]["x"] = _cv_r(s.c.nodes[s.i]["x"] + dx, "round_all", "round_moveby"); s.c.nodes[s.i]["y"] = _cv_r(s.c.nodes[s.i]["y"] + dy, "round_all", "round_moveby")
    def convertToCurve(s, smooth=False):
        CV["log"].append(("convertToCurve", s.i, smooth))
        if CV["mode"].get("convert_raises"): raise RuntimeError("convert boom")
        if CV["mode"].get("convert_noeffect"): return False
        a, b = s.c.nodes[s.i - 1], s.c.nodes[s.i]
        h1 = {"x": a["x"] + 0.33 * (b["x"] - a["x"]), "y": a["y"] + 0.33 * (b["y"] - a["y"]), "on": False}   # live (v0.76): 132 and 268 on a 400 edge
        h2 = {"x": a["x"] + 0.67 * (b["x"] - a["x"]), "y": a["y"] + 0.67 * (b["y"] - a["y"]), "on": False}
        if smooth and CV["mode"].get("conv_smooth_sets"): b["smooth"] = True
        if s.i == 0: s.c.nodes.extend([h1, h2])                         # stub ASSUMPTION for the closing segment: the handles are appended at the end of the node list
        else: s.c.nodes[s.i:s.i] = [h1, h2]
        return True
class CvContour:
    clockwise = False
    def __init__(s, pts):
        CV["log"].append(("flContour", len(pts)))
        s.nodes = [{"x": _cv_r(p.x, "round_all"), "y": _cv_r(p.y, "round_all"), "on": True} for p in pts]; s._closed = False
    @property
    def closed(s): return s._closed
    @closed.setter
    def closed(s, v):
        if not CV["mode"].get("noclose"): s._closed = bool(v)
    def nodesCount(s): return "many" if CV["mode"].get("count_text") else len(s.nodes)
    def setPoint(s, i, p):
        CV["log"].append(("setPoint", i, p.x, p.y))
        if CV["mode"].get("setpoint_raises"): raise RuntimeError("setPoint boom")
        if CV["mode"].get("setpoint_noeffect"): return CvNode(s, i)
        s.nodes[i]["x"] = _cv_r(p.x, "round_all", "round_setpoint"); s.nodes[i]["y"] = _cv_r(p.y, "round_all", "round_setpoint")
        return CvNode(s, i)
    def insert(s, i, node):
        CV["log"].append(("insert", i, node.x, node.y, node.t))
        if CV["mode"].get("insert_raises"): raise RuntimeError("insert boom")
        s.nodes.insert(i, {"x": node.x, "y": node.y, "on": node.t == "on"})
    def getNodeAt(s, i):
        if CV["mode"].get("getnode_raises"): raise RuntimeError("getNodeAt boom")
        if CV["mode"].get("getnode_none"): return None
        return CvNode(s, i)
class CvFlNode:
    def __init__(s, x, y, t="on"):
        CV["log"].append(("flNode", x, y, t))
        if CV["mode"].get("flnode_raises"): raise TypeError("flNode boom")
        s.x = x; s.y = y; s.t = t
def cvp(q, **mode):
    ts_reset(); CV["mode"] = dict(mode); CV["log"].clear()
    _fm.CurrentFont = lambda: TsFont(); _fm.flContour = CvContour; _fm.flNode = CvFlNode; qc.QPointF = CvPt
    c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve" + q); return c, d
def cv2(q, **mode):
    cvp("&stage=build", **mode); CV["log"].clear()
    c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve2" + q); return c, d
_cv_qp = getattr(qc, "QPointF", None)
c, d = cvp("&stage=build"); cp = d["curve_probe"]
print("510 curve probe        :", c, d["variant"], "| call", cp["call"], "| returned", cp["returned"], "| nodes_added", cp["nodes_added"], "| may_change", d["font_may_have_changed"])
print("    before             :", cp["before"]["nodesCount"], cp["before"]["closed"], cp["before"]["summary"])
print("    after              :", cp["after"]["nodesCount"], cp["after"]["closed"], cp["after"]["summary"])
print("    calls made         :", CV["log"], "| no wrapper / calls / notes keys:", [k for k in d if k in ("wrapper", "calls", "notes", "state_before", "state_after")])
c, d = cvp("&stage=build", convert_raises=1); cp = d["curve_probe"]; print("511 convertToCurve raises:", cp["convert_error"], "returned" in cp, "| nodes_added", cp["nodes_added"], "| after", cp["after"]["summary"])
c, d = cvp("&stage=build", convert_noeffect=1); cp = d["curve_probe"]; print("512 returns False, no change:", cp["returned"], "| nodes_added", cp["nodes_added"], "convert_error" in cp)
c, d = cvp("&stage=build", getnode_raises=1); cp = d["curve_probe"]; print("513 getNodeAt raises   :", cp["error"], "| before rows", cp["before"]["summary"][:2], "| calls", CV["log"])
c, d = cvp("&stage=build", getnode_none=1); cp = d["curve_probe"]; print("514 getNodeAt None     :", cp["error"], "| calls", CV["log"])
c, d = cvp("&stage=build", noclose=1); cp = d["curve_probe"]; print("515 square not closed  :", cp["error"], "| calls", CV["log"])
c, d = cvp("&stage=build", count_text=1); cp = d["curve_probe"]; print("516 nodesCount not a number:", cp["before"].get("nodes_note"), "|", cp["error"], "| calls", CV["log"])
for stg in ("attach", "refresh"):
    c, d = cvp("&stage=" + stg); print("517 stage=" + stg + " refused:", c, d["error"], "| calls", CV["log"], "curve_probe" in d)
c, d = cvp("&stage=build"); del _fm.flContour; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve&stage=build"); print("518 no flContour class :", d["curve_probe"]["error"])
c, d = cvp("&stage=build"); del qc.QPointF; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve&stage=build"); print("519 QPointF missing    :", d["curve_probe"]["error"])
c, d = cvp("&stage=bogus"); print("520 bogus stage        :", d.get("error"))
c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=bogus&stage=build"); print("521 bogus variant      :", d["error"])
c, d = call("/debug/tryshape?name=tri&route=modern&variant=curve&stage=build"); print("522 curve without go   :", c, d["error"][:40])
if _cv_qp is not None: qc.QPointF = _cv_qp
c, d = call("/version"); print("523 version           :", d)

# ================= v0.77: /debug/tryshape variant=curve2 (A: convertToCurve + setPoint + moveBy; B: insert flNode(x, y, "curve")) =================
def c2_print(tag, d):
    p = d["curve2_probe"]; a = p["experiment_A"]; b = p["experiment_B"]
    print(tag, "| may_change", d["font_may_have_changed"], "| keys", sorted(k for k in d if k in ("wrapper", "calls", "notes", "state_before", "state_after")))
    for nm, e in (("A", a), ("B", b)):
        print("    " + nm, "plan:", e["plan"][:60], "| error:", e.get("error"), "| note:", e.get("note"), "| final_as_expected:", e.get("final_as_expected"))
        for st in e["steps"]:
            print("      step", st["step"], "| returned", st.get("returned"), "| error", st.get("error"), "| as_expected", st.get("as_expected"), "| n", st["nodesCount"])
        if e["steps"]:
            print("      last nodes:", e["steps"][-1]["nodes"])
c, d = cv2("&stage=build"); c2_print("524 curve2 normal", d); print("    calls made:", CV["log"])
c, d = cv2("&stage=build", setpoint_raises=1); c2_print("525 setPoint raises", d)
c, d = cv2("&stage=build", setpoint_noeffect=1, moveby_noeffect=1); c2_print("526 setPoint / moveBy do nothing", d)
c, d = cv2("&stage=build", moveby_raises=1); c2_print("527 moveBy raises", d)
c, d = cv2("&stage=build", convert_raises=1); c2_print("528 convertToCurve raises (A skipped, B runs)", d)
c, d = cv2("&stage=build", insert_raises=1); c2_print("529 insert raises (second skipped)", d)
c, d = cv2("&stage=build", flnode_raises=1); c2_print("530 flNode raises", d)
cvp("&stage=build"); del _fm.flNode; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve2&stage=build"); print("531 no flNode class   :", d["curve2_probe"]["experiment_B"]["error"], "| A still ran:", len(d["curve2_probe"]["experiment_A"]["steps"]), "steps")
c, d = cv2("&stage=build", getnode_raises=1); c2_print("532 getNodeAt raises", d)
c, d = cv2("&stage=build", noclose=1); p = d["curve2_probe"]; print("533 square not closed  :", p["experiment_A"].get("error"), "|", p["experiment_B"].get("error"), "| calls", CV["log"])
c, d = cv2("&stage=build", count_text=1); p = d["curve2_probe"]; print("534 nodesCount text    :", p["experiment_A"].get("error"), "|", p["experiment_B"].get("error"))
for stg in ("attach", "refresh"):
    c, d = cv2("&stage=" + stg); print("535 stage=" + stg + " refused:", d["error"], "| calls", CV["log"], "| probe key", "curve2_probe" in d)
cvp("&stage=build"); del _fm.flContour; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve2&stage=build"); print("536 no flContour class :", d["curve2_probe"]["error"])
c, d = cv2("&stage=build"); del qc.QPointF; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve2&stage=build"); print("537 QPointF missing    :", d["curve2_probe"]["error"])
c, d = call("/debug/tryshape?name=tri&route=modern&variant=curve2&stage=build"); print("538 curve2 without go  :", c, d["error"][:40])
c, d = cvp("&stage=build"); print("539 variant=curve still works:", d["curve_probe"]["nodes_added"], d["curve_probe"]["after"]["summary"][1])
if _cv_qp is not None: qc.QPointF = _cv_qp
c, d = call("/version"); print("540 version           :", d)

# ================= v0.78: /debug/tryshape variant=curve3 (rounded corner: convertToCurve + setPoint, detached read-back, gated attach) =================
class C3Shape:
    def __init__(s): CV["log"].append(("flShape",)); s.sd = C3Data()
    @property
    def shapeData(s): return s.sd
    def contoursCount(s): return len(s.sd.contours)
    def hasContours(s): return len(s.sd.contours) > 0
    def isEmpty(s): return len(s.sd.contours) == 0
class C3Data:
    def __init__(s): s.contours = []
    def addContour(s, c):
        CV["log"].append(("shapeData.addContour", c.nodesCount()))
        if CV["mode"].get("adddata_raises"): raise IndexError("Unexpected SeqBase<T> length.")
        s.contours.append(c)
class C3Layer(MLayer2):
    def addShape(s, shape):
        CV["log"].append(("layer.addShape",))
        if CV["mode"].get("add_raises"): raise RuntimeError("addShape boom")
        s._sh += 1; s._n += sum(c.nodesCount() for c in shape.sd.contours); s.shapes.append(MSh())
def c3(q, layers=None, **mode):
    ts_reset(); ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    CV["mode"] = dict(mode); CV["log"].clear()
    MODERN_LAYERS.clear(); MODERN_LAYERS.update({"tri": C3Layer()} if layers is None else layers)
    _fm.CurrentFont = lambda: TsFont(); _fm.flContour = CvContour; _fm.flShape = C3Shape; _fm.flGlyph = flGlyphM; qc.QPointF = CvPt
    c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve3" + q); return c, d
def c3_layer(): return MODERN_LAYERS.get("tri")
c, d = c3("&stage=build"); L = c3_layer()
print("541 build (dry run)   :", c, d["variant"], "| built", d["built"], "| may_change", d["font_may_have_changed"], "| layer shapes/nodes", L._sh, L._n)
print("    calls             :", d["calls"]); print("    notes             :", d["notes"])
print("    stub calls        :", CV["log"])
c, d = c3("&stage=attach"); L = c3_layer()
print("542 attach            :", c, "| after", d["state_after"], "| expected", d["expected"], "| match", d["counts_match_expected"], "| may_change", d["font_may_have_changed"], "| layer shapes/nodes", L._sh, L._n)
print("    calls             :", d["calls"], "| modern view", d["modern_view_after"]["shape_count"], d["modern_view_after"]["layer_nodes_count"])
print("    stub calls        :", CV["log"])
c, d = c3("&stage=attach", layers={"tri": C3Layer(1, 3)}); print("543 layer not empty   :", c, d.get("refused"), "| stub calls", CV["log"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", layers={}); print("544 no modern layer   :", c, d.get("refused"), d["state_before"], "| stub calls", CV["log"])
c, d = c3("&stage=attach", convert_raises=1); print("545 convertToCurve raises:", d["failed_at"], "|", d["error"], "| layer", c3_layer()._sh, c3_layer()._n, "| addShape called:", ("layer.addShape",) in CV["log"])
c, d = c3("&stage=attach", convert_noeffect=1); print("546 convertToCurve returns False:", d["failed_at"], "|", d["error"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", setpoint_raises=1); print("547 setPoint raises   :", d["failed_at"], "|", d["error"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", setpoint_noeffect=1); print("548 setPoint does nothing:", d["failed_at"], "|", d["error"][:90], "| notes", [n[:70] for n in d["notes"]], "| layer", c3_layer()._sh, c3_layer()._n, "| addShape called:", ("layer.addShape",) in CV["log"])
c, d = c3("&stage=attach", noclose=1); print("549 contour does not close:", d["failed_at"], "|", d["error"][:90], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", getnode_raises=1); print("550 getNodeAt raises  :", d["failed_at"], "|", d["error"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", adddata_raises=1); print("551 shapeData.addContour raises:", d["failed_at"], "|", d["error"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", add_raises=1); print("552 layer.addShape raises:", d["failed_at"], "|", d["error"], "| after", d["state_after"], "| match", d["counts_match_expected"], "| may_change", d["font_may_have_changed"])
c, d = c3("&stage=build"); del _fm.flShape; ns["_MODERN_CACHE"].clear(); c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve3&stage=build"); print("553 no flShape class  :", d["failed_at"], "|", d["error"])
c, d = c3("&stage=build"); del _fm.flContour; ns["_MODERN_CACHE"].clear(); c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve3&stage=build"); print("554 no flContour class:", d["failed_at"], "|", d["error"])
c, d = c3("&stage=build"); del qc.QPointF; ns["_MODERN_CACHE"].clear(); c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve3&stage=build"); print("555 QPointF missing   :", d["failed_at"], "|", d["error"])
c, d = c3("&stage=refresh"); print("556 stage=refresh     :", d.get("calls"), "| may_change", d["font_may_have_changed"], "| addShape called:", ("layer.addShape",) in CV["log"])
c, d = call("/debug/tryshape?name=tri&route=modern&variant=curve3&stage=attach"); print("557 attach without go :", c, d["error"][:40])
c, d = c3("&stage=attach", layers={"tri": C3Layer()}); c, d2 = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve3&stage=attach"); print("558 second attach refused:", d2.get("refused"), "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach"); c, d2 = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=single&stage=build"); print("559 variant=single unchanged:", d2["variant"], d2["built"]["contour"])
c, d = call("/version"); print("560 version           :", d)

# ================= v0.79: curve3 with whole-number handles; /debug/tryshape variant=curve4 (precision probe: does FontLab keep fractional coordinates?) =================
c, d = c3("&stage=build"); print("561 curve3 whole-number handles:", d.get("error"), "| built", d["built"], "| calls", d["calls"][3:5])
c, d = c3("&stage=attach"); print("562 curve3 attach     :", d["counts_match_expected"], d["expected"], "| layer", c3_layer()._sh, c3_layer()._n)
c, d = c3("&stage=attach", round_all=1); print("563 curve3, FontLab rounds everything:", d.get("error"), "| layer", c3_layer()._sh, c3_layer()._n)
def c4(q, **mode):
    cvp("&stage=build", **mode); CV["log"].clear()
    c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve4" + q); return c, d
def c4_print(tag, d):
    p = d["curve4_probe"]
    print(tag, "| may_change", d["font_may_have_changed"], "| error", p.get("error"))
    for t in p.get("trials", []):
        print("    ", t["trial"][:58].ljust(58), "| req", t.get("requested_xy", t.get("requested_points")), "| read", t.get("read_xy", t.get("read_points")), "| kept", t.get("kept_fraction"), "| changed", t.get("changed"), "| errors", [t.get(k) for k in ("error", "call_error", "read_error") if t.get(k)])
    print("     summary:", p.get("summary"))
c, d = c4("&stage=build", settable=1); c4_print("564 curve4, nothing rounds, setters work", d); print("     stub calls:", len(CV["log"]))
c, d = c4("&stage=build", round_setpoint=1); c4_print("565 curve4, only setPoint rounds, assignment refused", d)
c, d = c4("&stage=build", round_all=1, settable=1); c4_print("566 curve4, everything rounds", d)
c, d = c4("&stage=build", convert_raises=1); c4_print("567 convertToCurve raises (setup fails for the trials)", d)
c, d = c4("&stage=build", getnode_raises=1); c4_print("568 getNodeAt raises", d)
c, d = c4("&stage=build", moveby_raises=1, setpoint_raises=1, settable=1); c4_print("569 moveBy and setPoint raise", d)
c, d = c4("&stage=build", setpoint_noeffect=1, moveby_noeffect=1); c4_print("570 setPoint / moveBy do nothing", d)
for stg in ("attach", "refresh"):
    c, d = c4("&stage=" + stg); print("571 stage=" + stg + " refused:", d["error"], "| calls", CV["log"], "| probe key", "curve4_probe" in d)
cvp("&stage=build"); del _fm.flContour; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve4&stage=build"); print("572 no flContour class:", d["curve4_probe"]["error"])
c, d = c4("&stage=build"); del qc.QPointF; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve4&stage=build"); print("573 QPointF missing   :", d["curve4_probe"]["error"])
c, d = call("/debug/tryshape?name=tri&route=modern&variant=curve4&stage=build"); print("574 curve4 without go :", c, d["error"][:40])
c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=bogus&stage=build"); print("575 bogus variant     :", d["error"])
if _cv_qp is not None: qc.QPointF = _cv_qp
c, d = call("/version"); print("576 version           :", d)

# ================= v0.80: /debug/tryshape variant=curve5 (closing segment, smooth flag, handle pairing; detached) =================
def c5(q, **mode):
    cvp("&stage=build", **mode); CV["log"].clear()
    c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve5" + q); return c, d
def c5_print(tag, d):
    p = d["curve5_probe"]
    print(tag, "| may_change", d["font_may_have_changed"], "| error", p.get("error"))
    for t in p.get("trials", []):
        keys = ("returned", "call_error", "handle_indices", "nodesCount", "smooth_flags", "smooth_before", "smooth_after", "smooth_set_error", "coords_changed", "move_error", "partner_before", "partner_after", "partner_moved", "moved_handle_after", "handles_vs_node3", "error")
        print("    ", t["trial"][:70], "|", {k: t[k] for k in keys if k in t})
    print("     summary:", p.get("summary"))
c, d = c5("&stage=build", settable=1, smooth_settable=1, conv_smooth_sets=1, smooth_pairs=1); c5_print("577 curve5, everything works (stub assumptions)", d)
c, d = c5("&stage=build", settable=1); c5_print("578 curve5, smooth cannot be set, no pairing", d)
c, d = c5("&stage=build", settable=1, smooth_settable=1); c5_print("579 curve5, smooth sticks but nothing pairs", d)
c, d = c5("&stage=build", smooth_settable=1, smooth_pairs=1); c5_print("580 curve5, x / y assignment refused", d)
c, d = c5("&stage=build", convert_raises=1, settable=1); c5_print("581 convertToCurve raises", d)
c, d = c5("&stage=build", getnode_raises=1, settable=1); c5_print("582 getNodeAt raises", d)
c, d = c5("&stage=build", convert_noeffect=1, settable=1); c5_print("583 convertToCurve returns False", d)
for stg in ("attach", "refresh"):
    c, d = c5("&stage=" + stg); print("584 stage=" + stg + " refused:", d["error"], "| calls", CV["log"], "| probe key", "curve5_probe" in d)
cvp("&stage=build"); del _fm.flContour; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve5&stage=build"); print("585 no flContour class:", d["curve5_probe"]["error"])
c, d = c5("&stage=build"); del qc.QPointF; c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=curve5&stage=build"); print("586 QPointF missing   :", d["curve5_probe"]["error"])
c, d = call("/debug/tryshape?name=tri&route=modern&variant=curve5&stage=build"); print("587 curve5 without go :", c, d["error"][:40])
c, d = call("/debug/tryshape?name=tri&go=yes&route=modern&variant=bogus&stage=build"); print("588 bogus variant     :", d["error"])
if _cv_qp is not None: qc.QPointF = _cv_qp
c, d = call("/version"); print("589 version           :", d)

# ================= v0.81: POST /glyph/path (cubic curves), rule B rounding, polygon rounding report =================
# The fake contour below models what was SEEN live (v0.76-v0.80): convertToCurve(False) converts the segment that ENDS at the node and inserts
# two handles before it at 33% / 67% (rounded); on node 0 the closing segment is converted and the handles are APPENDED at the end (last node
# towards node 0); node.smooth = True realigns the next handle onto the line opposite the previous handle (length kept, rounded); x / y
# assignment keeps the value and pairs nothing. Modes: conv_false, conv_raises, smooth_ignored, place_ignored, round_place (assignment rounds
# to a different value), attach_alter (the attached layer reads one node differently).
P81 = {}
class P81Row(dict): pass
class P81Node:
    def __init__(s, c, row): s._c = c; s._r = row
    def _get(s, k): return s._r[k]
    @property
    def x(s): return s._r["x"]
    @x.setter
    def x(s, v):
        if P72["mode"].get("place_ignored") and not s._r["on"]: return
        s._r["x"] = float(v) + (1.0 if P72["mode"].get("round_place") and not s._r["on"] else 0.0)
    @property
    def y(s): return s._r["y"]
    @y.setter
    def y(s, v):
        if P72["mode"].get("place_ignored") and not s._r["on"]: return
        s._r["y"] = float(v)
    @property
    def isOn(s): return s._r["on"]
    @property
    def isOff(s): return False
    @property
    def isCurve(s): return not s._r["on"]
    @property
    def smooth(s): return s._r["smooth"]
    @smooth.setter
    def smooth(s, v):
        if P72["mode"].get("smooth_ignored"): return
        s._r["smooth"] = bool(v)
        rows = s._c.rows; i = rows.index(s._r); n = len(rows)
        a, b = rows[(i - 1) % n], rows[(i + 1) % n]
        if v and not a["on"] and not b["on"]:
            vx, vy = s._r["x"] - a["x"], s._r["y"] - a["y"]; ln = (b["x"] - s._r["x"]) ** 2 + (b["y"] - s._r["y"]) ** 2
            L = ln ** 0.5; m = (vx * vx + vy * vy) ** 0.5
            if m:
                b["x"] = round(s._r["x"] + vx / m * L); b["y"] = round(s._r["y"] + vy / m * L)
    def convertToCurve(s, smooth=False):
        m = P72["mode"]; P72["calls"].append("convertToCurve")
        if m.get("conv_raises"): raise RuntimeError("convert boom")
        if m.get("conv_false"): return False
        rows = s._c.rows; i = rows.index(s._r)
        prev = rows[i - 1] if i > 0 else rows[-1]
        h = [P81Row(x=float(round(prev["x"] + (s._r["x"] - prev["x"]) * f)), y=float(round(prev["y"] + (s._r["y"] - prev["y"]) * f)), on=False, smooth=False) for f in (0.33, 0.67)]
        if i > 0: rows[i:i] = h
        else: rows.extend(h)
        return True
class P81Contour:
    def __init__(s, pts):
        P72["calls"].append("flContour")
        if P72["mode"].get("contour_raises"): raise RuntimeError("contour boom")
        s.rows = [P81Row(x=float(p.x), y=float(p.y), on=True, smooth=False) for p in pts]; s._closed = False; s.clockwise = False
    def getNodeAt(s, i):
        if P72["mode"].get("node_raises") == i: raise RuntimeError("getNodeAt boom")
        node = P81Node(s, s.rows[i])
        return node
    @property
    def closed(s): return s._closed
    @closed.setter
    def closed(s, v): s._closed = False if P72["mode"].get("noclose") else v
    def nodesCount(s): return len(s.rows)
class P81Layer(P72Layer):
    def addShape(s, shape):
        P72Layer.addShape(s, shape)
        if P72["mode"].get("attach_alter"): shape.contours[0].rows[0]["x"] += 5.0
def p81_setup(mode=None):
    p72_setup(mode=mode); _fm.flContour = P81Contour
    real = P81["real_create"] = P81.get("real_create") or P72Mod.findLayerCreate     # wrap the ORIGINAL once, never a wrapper
    def create(s, name, cs=None):
        r = real(s, name, cs); P72["layers"][s.name] = P81Layer(name); return P72["layers"][s.name]
    P72Mod.findLayerCreate = create
def pp(x, y, c1=None, c2=None, smooth=None):
    d = {"x": x, "y": y}
    if c1 is not None: d["c1"] = {"x": c1[0], "y": c1[1]}; d["c2"] = {"x": c2[0], "y": c2[1]}
    if smooth is not None: d["smooth"] = smooth
    return d
def path_nodes():
    m = mo_get()["modern_outline"]
    return [[(round(n["x"], 3), round(n["y"], 3), "on" if n["isOn"] else "h", n["smooth"]) for n in c["nodes"]] for c in m["contours"]]
def show_path(tag, d, keys=("drawn", "nodes_match", "points", "segments_curved", "contour_sizes", "changed", "checks")):
    print(tag, ":", {k: d.get(k) for k in keys if k in d}, "| rounded", len(d.get("coordinates_rounded") or []), "| reason", (d.get("reason") or "")[:150])
RRECT = [pp(0, 0), pp(400, 0), pp(400, 400, (500, 100), (500, 300)), pp(0, 400)]
CIRC = [pp(400, 200, c1=(310, 0), c2=(400, 90), smooth=True), pp(200, 400, c1=(400, 310), c2=(310, 400), smooth=True),
        pp(0, 200, c1=(90, 400), c2=(0, 310), smooth=True), pp(200, 0, c1=(0, 90), c2=(90, 0), smooth=True)]
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]})
show_path("600 one curved segment      ", d); print("601 nodes read back       :", path_nodes(), "| after", d["state_after"], "| margins", d.get("margins"))
print("602 calls                 :", P72["calls"], "| layer_created", d.get("layer_created"))
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [CIRC]}); show_path("603 circle, 4 smooth nodes  ", d); print("604 nodes read back       :", path_nodes())
print("605 convert order         :", P72["calls"].count("convertToCurve"), "conversions; closing segment handles last in list:", path_nodes()[0][-2:])
CLOSE = [pp(0, 0, c1=(0, 300), c2=(0, 100)), pp(400, 0), pp(400, 400), pp(0, 400)]
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [CLOSE]}); show_path("606 curve over closing seg  ", d); print("607 nodes read back       :", path_nodes())
OUT2 = [pp(0, 0), pp(300, 0), pp(300, 300), pp(0, 300)]
HOLE2 = [pp(100, 100), pp(100, 200, c1=(100, 130), c2=(100, 170)), pp(200, 200), pp(200, 100)]
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [OUT2, HOLE2]}); show_path("608 curved counter          ", d); print("609 nodes read back       :", path_nodes())
# rule B
FRAC = [pp(0.5, 0), pp(10.49, 0), pp(10, 10.5, c1=(10.5, 3.2), c2=(10.5, 7.5)), pp(-2.5, 10)]
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [FRAC]}); show_path("610 rule B                  ", d)
print("611 coordinates_rounded   :", d["coordinates_rounded"]); print("612 nodes read back       :", path_nodes())
p81_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": [[0, 0], [10.5, 0], [5.4, 20], [-0.5, 3]]})
print("613 polygon rounding      :", d["drawn"], d["coordinates_rounded"], "|", [(n["x"], n["y"]) for n in mo_get()["modern_outline"]["contours"][0]["nodes"]])
p81_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("614 polygon, whole numbers:", d["drawn"], d["coordinates_rounded"])
p81_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": [[0, 0], [0.4, 0], [0.3, 0.2]]}); print("615 polygon collapses     :", c, d.get("error"), "| calls", P72["calls"])
# refusals before anything is built
def refuse(tag, payload, mode=None):
    p81_setup(mode=mode); n0 = len(P72["calls"]); c, d = p72_post("/glyph/path", payload)
    print(tag, ":", c, d.get("error") or ("drawn " + str(d.get("drawn")) + " | " + (d.get("reason") or "")[:130]), "| calls added", len(P72["calls"]) - n0, "| layers", sorted(P72["layers"]))
BADTAN = [pp(0, 0), pp(400, 0, smooth=True), pp(400, 400, c1=(500, 100), c2=(500, 300)), pp(0, 400)]
refuse("620 smooth, not collinear     ", {"name": "fresh", "contours": [BADTAN]})
refuse("621 smooth, handle on node    ", {"name": "fresh", "contours": [[pp(0, 0), pp(400, 0, c1=(400, 0), c2=(400, 100), smooth=True), pp(400, 400), pp(0, 400)]]})
refuse("622 smooth between two lines  ", {"name": "fresh", "contours": [[pp(0, 0), pp(400, 0, smooth=True), pp(400, 400), pp(0, 400)]]})
GOODSM = [pp(0, 0), pp(400, 0, smooth=True), pp(400, 400, c1=(500, 0), c2=(400, 300)), pp(0, 400)]
refuse("623 smooth, line + handle     ", {"name": "fresh", "contours": [GOODSM]})
for tag, payload in (("630 name empty             ", {"name": " ", "contours": [RRECT]}), ("631 no contours key         ", {"name": "fresh"}),
                     ("632 contours empty          ", {"name": "fresh", "contours": []}), ("633 contour is not a list   ", {"name": "fresh", "contours": [5]}),
                     ("634 two points only         ", {"name": "fresh", "contours": [[pp(0, 0), pp(5, 5)]]}),
                     ("635 point is a list         ", {"name": "fresh", "contours": [[[0, 0], [5, 0], [5, 5]]]}),
                     ("636 unknown key             ", {"name": "fresh", "contours": [[dict(pp(0, 0), z=1), pp(5, 0), pp(5, 5)]]}),
                     ("637 x is text               ", {"name": "fresh", "contours": [[pp("0", 0), pp(5, 0), pp(5, 5)]]}),
                     ("638 x is bool               ", {"name": "fresh", "contours": [[pp(True, 0), pp(5, 0), pp(5, 5)]]}),
                     ("639 x out of range          ", {"name": "fresh", "contours": [[pp(30000, 0), pp(5, 0), pp(5, 5)]]}),
                     ("640 c1 without c2           ", {"name": "fresh", "contours": [[dict(pp(0, 0), c1={"x": 1, "y": 1}), pp(5, 0), pp(5, 5)]]}),
                     ("641 c1 is a list            ", {"name": "fresh", "contours": [[dict(pp(0, 0), c1=[1, 1], c2=[2, 2]), pp(5, 0), pp(5, 5)]]}),
                     ("642 c1 with a stray key     ", {"name": "fresh", "contours": [[dict(pp(0, 0), c1={"x": 1, "y": 1, "z": 2}, c2={"x": 1, "y": 1}), pp(5, 0), pp(5, 5)]]}),
                     ("643 smooth is text          ", {"name": "fresh", "contours": [[dict(pp(0, 0), smooth="yes"), pp(5, 0), pp(5, 5)]]}),
                     ("644 three equal points      ", {"name": "fresh", "contours": [[pp(0, 0), pp(0, 0), pp(5, 5)]]}),
                     ("645 collapse after rounding ", {"name": "fresh", "contours": [[pp(0, 0), pp(0.4, 0), pp(0.3, 0.2)]]}),
                     ("646 21 contours             ", {"name": "fresh", "contours": [OUT2] * 21}),
                     ("647 too many nodes          ", {"name": "fresh", "contours": [[pp(i, (i * 7) % 90) for i in range(500)]] * 3 + [[pp(i, (i * 7) % 90) for i in range(500)]] * 2})):
    refuse(tag, payload)
r = ns["_route"]("POST", "/glyph/path", b"{bad"); print("648 bad JSON              :", r.split(b"\r\n")[0].decode()[9:12])
# failures while building (detached: nothing attached, nothing changed)
for tag, mode in (("650 convertToCurve returns False", {"conv_false": 1}), ("651 convertToCurve raises     ", {"conv_raises": 1}),
                  ("652 smooth is ignored          ", {"smooth_ignored": 1}), ("653 handle placement ignored   ", {"place_ignored": 1}),
                  ("654 handle placed off by one   ", {"round_place": 1}), ("655 flContour raises           ", {"contour_raises": 1}),
                  ("656 contour will not close     ", {"noclose": 1}), ("657 getNodeAt raises           ", {"node_raises": 1})):
    p81_setup(mode=mode); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [CIRC]})
    print(tag, ":", d["drawn"], "|", (d.get("reason") or "")[:140], "| changed", d.get("changed"), "| addShape", P72["calls"].count("addShape"), "| layer", P72["layers"]["fresh"]._sh)
p81_setup(mode={"attach_alter": 1}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); show_path("658 layer differs after attach", d); print("659 changed is reported   :", d["changed"], "|", d["reason"][:140])
p81_setup(mode={"add_raises": 1}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("660 addShape raises       :", d["drawn"], "|", d["reason"][:80], "| changed", d["changed"])
p81_setup(mode={"extra_nodes": 1}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("661 node count off        :", d["drawn"], "|", d["reason"][:110], "| checks", d["checks"])
p81_setup(mode={"contours_type": "raises"}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("662 read-back unreadable  :", d["drawn"], "| nodes_match", d["nodes_match"], "|", d["reason"][:120])
p81_setup(); P72["layers"]["fresh"] = P72Layer("test_font", 1, 3); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("663 layer not empty       :", d["drawn"], "|", d["reason"][:50], "| calls", P72["calls"])
p81_setup(); c, d = p72_post("/glyph/path", {"name": "nope", "contours": [RRECT]}); print("664 unknown glyph         :", d)
p81_setup(); _fm.CurrentFont = lambda: None; c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("665 no font               :", d)
p81_setup(); qc.QPointF = None; c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("666 QPointF missing       :", d["drawn"], "|", d["reason"][:70])
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); print("667 second draw refused   :", d["drawn"], "|", d["reason"][:50])
p81_setup(); n = len(P72["calls"]); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [[pp(0, 0), pp(100, 0), pp(100, 100)]]}); show_path("668 plain triangle via path", d); print("669 no convert calls      :", P72["calls"].count("convertToCurve"))
c, d = call("/version"); print("671 version               :", d)
print("672 pure helpers          :", ns["_round_half_up"](2.5), ns["_round_half_up"](-2.5), ns["_round_half_up"](-0.5), ns["_round_half_up"](0.49999), ns["_round_half_up"](1e-9), ns["_round_half_up"](-3.0))


# ================= v0.82: layer guard (never call findLayerCreate when the glyph may already have a layer) =================
def snap82():
    lay = P72["layers"].get("fresh")
    return (lay._sh, lay._n, len(lay._contours)) if lay is not None else None
def creates82(): return sum(1 for x in P72["calls"] if isinstance(x, tuple) and x[0] == "findLayerCreate")
p81_setup(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); first = snap82()
print("700 first draw             :", d["drawn"], "| layer_created", d.get("layer_created"), "| layer", first, "| creates", creates82())
P72["mode"]["inactive"] = ("fresh",)          # live v0.81: the layer exists, the wrapper reports none, the legacy view still reads 'empty'
print("701 legacy view lags       :", ns["_tryshape_known_empty"](ns["_tryshape_state"](TS["fresh"])), "| wrapper activeLayer", P72Mod(TS["fresh"], None).activeLayer)
c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [OUT2]})
print("702 second draw_path       :", d["drawn"], "|", d["reason"][:150], "| existing_layer", d.get("existing_layer"), "| changed", d.get("changed"), "| creates", creates82(), "| layer unchanged", snap82() == first)
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
print("703 draw_polygon too       :", d["drawn"], "|", d["reason"][:60], "| creates", creates82(), "| layer unchanged", snap82() == first)
w0 = TS["fresh"].width
c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600})
print("704 width, no legacy write :", d["set"], "|", d.get("route"), "|", d["reason"][:60], "| legacy width unchanged", TS["fresh"].width == w0, "| creates", creates82())
for tag, mode in (("706 ask raises            ", {"inactive": ("fresh",), "ask_raises": 1}), ("707 getLayerByName missing  ", {"ask_missing": 1}),
                  ("708 findLayer missing       ", {"ask_missing_find": 1})):
    p81_setup(mode=mode); P72["mode"].update(mode); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]})
    print(tag, ":", d["drawn"], "|", d["reason"][:140], "| creates", creates82(), "| layer", snap82())
p81_setup(mode={"ask_blind": 1}); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]})
print("709 glyph without layer, nobody answers yes:", d["drawn"], "| layer_created", d.get("layer_created"), "| creates", creates82())
p81_setup(); c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600}); print("710 width on a glyph with no layer still works:", d["set"], d["route"], "| layer_created", d.get("layer_created"), "| creates", creates82())
c, d = call("/version"); print("711 version                :", d)


# ================= v0.83: /debug/tryfont (can a script make a new, empty font? gated experiment; faked flPackage / flWorkspace) =================
import re as _re83
TF = {"calls": [], "forbidden": [], "packages": [], "mode": {}}
def _tf_spy(label):
    def f(self, *a, **k):
        TF["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
class TFFgFont: pass
class TFPackage:
    def __init__(self):
        TF["calls"].append("flPackage()")
        if TF["mode"].get("ctor_raises"): raise RuntimeError("ctor refused")
        if TF["mode"].get("register_on_construct"): TF["packages"].append(self)
    name = ""
    upm = 1000.0
    mastersCount = 0
    defaultMaster = ""
    glyphsCount = 0
    path = ""
    @property
    def fileName(self): raise RuntimeError("no file name")
    @property
    def fgPackage(self): return TFFgFont()
    def isNull(self): return False
for _n in ("release", "remove", "close", "save", "resetPackage", "setUpm", "addMaster", "addGlyph"):
    setattr(TFPackage, _n, _tf_spy("flPackage." + _n))
class TFWorkspace:
    @staticmethod
    def instance(): return TF_WS
    def packages(self): return list(TF["packages"])
    @property
    def currentPackage(self): return TF["packages"][-1] if TF["packages"] else None
    def hasPackage(self, p): return p in TF["packages"]
    def addPackage(self, p):
        TF["calls"].append("addPackage")
        if TF["mode"].get("add_raises"): raise RuntimeError("addPackage refused")
        TF["packages"].append(p)
        return None
for _n in ("createNewProject", "closePackage", "closeProject", "saveProject", "exportFont", "exportTo", "exportCurrentFont", "readProject", "release", "remove"):
    setattr(TFWorkspace, _n, _tf_spy("flWorkspace." + _n))
TF_WS = TFWorkspace()
_tf_mods = []
for _m in (fl, sys.modules.get("fontlab"), ns.get("fl")):
    if _m is not None and all(_m is not x for x in _tf_mods): _tf_mods.append(_m)
_tf_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flPackage", "flWorkspace")]
for _m in _tf_mods:
    _m.CountFonts = lambda: len(TF["packages"])
    _m.CurrentFont = lambda: Font() if TF["packages"] else None
    _m.flPackage = TFPackage
    _m.flWorkspace = TFWorkspace
def tf_reset(**mode):
    TF["calls"].clear(); TF["forbidden"].clear(); TF["packages"].clear(); TF["mode"] = dict(mode)
    ns["_TRYFONT"].update(package=None, constructed=False, attached=False)
def tf_ws(d, key="workspace_state"):
    w = d.get(key) or {}
    cp = w.get("currentPackage")
    return {"CountFonts": w.get("CountFonts"), "CurrentFont": w.get("CurrentFont") if not isinstance(w.get("CurrentFont"), dict) else "font", "packages_len": w.get("packages_len"),
            "currentPackage": cp if not isinstance(cp, dict) else {"isNull": cp.get("isNull"), "name": cp.get("name")}, "hasPackage": w.get("hasPackage")}
tf_reset(); c, d = call("/debug/tryfont?stage=state")
print("720 state, nothing open        :", c, tf_ws(d), "| constructed", d["constructed"], "| attached", d["attached"], "| calls", TF["calls"])
c, d = call("/debug/tryfont")
print("721 default stage is state     :", c, d["stage"])
c, d = call("/debug/tryfont?stage=construct")
print("722 construct without go       :", c, d.get("error"), "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=attach")
print("723 attach without go          :", c, d.get("error")[:60], "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=attach&go=yes")
print("724 attach before construct    :", c, d.get("error"), "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=construct&go=maybe")
print("725 go must be exactly yes     :", c, d.get("error")[:40], "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=bogus&go=yes")
print("726 unknown stage              :", c, d, "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=construct&go=yes")
print("727 construct                  :", c, d["package_type"], d["reads"], "| before", tf_ws(d, "workspace_before"), "| after", tf_ws(d, "workspace_after"), "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=construct&go=yes")
print("728 second construct refused   :", c, d["error"][:70], "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=state")
print("729 state after construct      :", tf_ws(d), "| constructed", d["constructed"], "| attached", d["attached"])
c, d = call("/debug/tryfont?stage=attach&go=yes")
print("730 attach                     :", c, d["call"], "| return", d["return_value"], "| error", d["call_error"], "| before", tf_ws(d, "workspace_before"), "| after", tf_ws(d, "workspace_after"), "| calls", TF["calls"])
c, d = call("/debug/tryfont?stage=attach&go=yes")
print("731 second attach refused      :", c, d["error"][:60], "| addPackage calls", TF["calls"].count("addPackage"))
c, d = call("/debug/tryfont?stage=state")
print("732 state after attach         :", tf_ws(d), "| constructed", d["constructed"], "| attached", d["attached"])
_cp = d["workspace_state"].get("currentPackage") or {}
print("732b state names the package   :", {k: _cp.get(k) for k in ("path", "fileName")}, "| packages_type", d["workspace_state"].get("packages_type"))
class TFSavedPackage(TFPackage):
    path = "C:/fonts/saved.vfc"
    fileName = "saved.vfc"
TF["packages"].append(TFSavedPackage()); c, d = call("/debug/tryfont?stage=state")
_cp = d["workspace_state"].get("currentPackage") or {}
print("732c state, a saved package    :", c, tf_ws(d), {k: _cp.get(k) for k in ("path", "fileName")}, "| packages_type", d["workspace_state"].get("packages_type"), "| forbidden", TF["forbidden"])
tf_reset(add_raises=1); call("/debug/tryfont?stage=construct&go=yes"); c, d = call("/debug/tryfont?stage=attach&go=yes")
print("733 addPackage raises          :", c, "| error", d["call_error"], "| attached", d["attached"], "| after", tf_ws(d, "workspace_after"))
c, d = call("/debug/tryfont?stage=attach&go=yes")
print("734 no retry after a failure   :", c, d["error"][:60], "| addPackage calls", TF["calls"].count("addPackage"))
tf_reset(ctor_raises=1); c, d = call("/debug/tryfont?stage=construct&go=yes")
print("735 constructor raises         :", c, d["error"][:60], "| constructed", ns["_TRYFONT"]["constructed"], "| package", ns["_TRYFONT"]["package"])
TF["mode"] = {}; c, d = call("/debug/tryfont?stage=construct&go=yes")
print("736 retry after a failed ctor  :", c, d.get("package_type"), "| constructed", ns["_TRYFONT"]["constructed"])
tf_reset(register_on_construct=1); c, d = call("/debug/tryfont?stage=construct&go=yes")
print("737 construct that registers   :", c, "| before", tf_ws(d, "workspace_before"), "| after", tf_ws(d, "workspace_after"))
tf_reset(); fl_none = [m.flPackage for m in _tf_mods]
for _m in _tf_mods: del _m.flPackage
c, d = call("/debug/tryfont?stage=construct&go=yes")
print("738 no flPackage class         :", c, d["error"], "| constructed", ns["_TRYFONT"]["constructed"])
for _m in _tf_mods: _m.flPackage = TFPackage
tf_reset(); call("/debug/tryfont?stage=construct&go=yes"); call("/debug/tryfont?stage=attach&go=yes"); call("/debug/tryfont?stage=state")
print("739 forbidden members called   :", TF["forbidden"], "| calls", TF["calls"])
_src83 = src[src.index("_TRYFONT_STAGES = "):src.index("def debug_layer_item(")]
print("740 static scan of the probe   : forbidden call syntax found:", _re83.findall(r"\.(?:createNewProject|closePackage|closeProject|saveProject|readProject|export\w*|save\w*|release|remove|close|resetPackage|setUpm|addMaster|addGlyph)\s*\(", _src83),
      "| real addPackage calls:", len(_re83.findall(r"mod\.flWorkspace\.instance\(\)\.addPackage\(", _src83)), "| scanned chars > 3000:", len(_src83) > 3000)
c, d = call("/version"); print("741 version                    :", d)
for _m, _a, _v in _tf_saved:
    if _v is None: delattr(_m, _a)
    else: setattr(_m, _a, _v)
tf_reset()


# ================= v0.84: layer name for the FIRST glyph of a new font (fallback to the single master of the font's package) =================
import types as _types84
P84 = {"reads": [], "forbidden": [], "cfg": {}}
def _p84_get(key):
    P84["reads"].append(key); v = P84["cfg"][key]
    if isinstance(v, Exception): raise v
    return v
def _p84_spy(label):
    def f(self, *a, **k):
        P84["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
class Pkg84:
    """v0.150: two roles. "gp" is the glyph's own package (w.package): isNull, fgId (key gp_fgId) and the master reads.
    "cp" is the workspace's current package: only cp_isNull and cp_fgId are read from it."""
    def __init__(s, role="gp"): s.role = role
    def isNull(s): return _p84_get("isNull" if s.role == "gp" else "cp_isNull")
    fgId = property(lambda s: _p84_get(s.role + "_fgId"))
    mastersCount = property(lambda s: _p84_get("mastersCount"))
    defaultMaster = property(lambda s: _p84_get("defaultMaster"))
    master = property(lambda s: _p84_get("master"))
    masters = property(lambda s: _p84_get("masters"))
    upm = property(lambda s: _p84_get("upm"))
    @property
    def glyphsCount(s):
        v = _p84_get("glyphsCount"); return len(TS) if v is None else v
for _n in ("close", "release", "remove", "save", "resetPackage", "setUpm", "addMaster", "addGlyph", "renameMaster", "setMaster"):
    setattr(Pkg84, _n, _p84_spy("flPackage." + _n))
class Ws84(SbWsX):
    def packages(s):
        v = _p84_get("packages"); return [0] * v
    @property
    def currentPackage(s):
        v = _p84_get("cp"); return None if v is None else Pkg84("cp")
def _p72_package(s):                                   # v0.150: the glyph's own package, only inside the v0.84 gate tests
    if not P72["mode"].get("pkg84"): raise AttributeError("package")
    v = _p84_get("gp"); return None if v is None else Pkg84("gp")
P72Mod.package = property(_p72_package)
for _n in ("addPackage", "createNewProject", "closePackage", "closeProject", "saveProject", "exportFont", "exportTo", "readProject", "release", "remove"):
    setattr(Ws84, _n, _p84_spy("flWorkspace." + _n))
class TfFont(TsFont):
    @property
    def info(s):
        v = P84["cfg"]["font_upm"]
        if v is None: raise AttributeError("info")
        return _types84.SimpleNamespace(unitsPerEm=v)
def p84_fakes(**over):
    P84["reads"].clear(); P84["forbidden"].clear()
    P84["cfg"] = dict(count=1, packages=1, cp="pkg", isNull=False, mastersCount=1, defaultMaster="Regular", master="Regular", masters=["Regular"],
                      glyphsCount=None, upm=1000.0, font_upm=1000.0, gp="pkg", gp_fgId=5, cp_fgId=5, cp_isNull=False)
    P84["cfg"].update(over)
    P72["mode"]["pkg84"] = True
    def _count():
        v = P84["cfg"]["count"]
        if isinstance(v, Exception): raise v
        return v
    _fm.CountFonts = _count
    _fm.CurrentFont = lambda: TfFont()
    _fm.flWorkspace = type("flWorkspace", (), {"instance": staticmethod(lambda: Ws84())})
def p84_setup(refs=(), empties=("fresh",), mode=None, **over):
    p72_setup(refs=refs, empties=empties, mode=mode); p84_fakes(**over)
def creates84(): return [x[2] for x in P72["calls"] if isinstance(x, tuple) and x[0] == "findLayerCreate"]
def why84(d):
    r = d.get("reason") or ""
    return (r.split("was not used either: ", 1)[1] if "was not used either: " in r else r[:90])[:120]
def r84(tag, d, keys=("drawn", "set", "layer_created", "layer_name_source")):
    print(tag, ":", {k: d.get(k) for k in keys if k in d}, "| creates", creates84(), "| why:", why84(d) if not (d.get("drawn") or d.get("set")) else "-", "| forbidden", P84["forbidden"])
p84_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
r84("750 first glyph of a new font, polygon   ", d); print("751 what was read             :", sorted(set(P84["reads"])), "| reads", len(P84["reads"]))
p84_setup(); c, d = p72_post("/glyph/width", {"name": "fresh", "width": 600}); r84("752 first glyph, width              ", d)
p81_setup(); TS.pop("ref"); P72["layers"].pop("ref"); p84_fakes(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); r84("753 first glyph, curved draw_path     ", d)
p84_setup(refs=(("ref", "test_font"),)); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
r84("754 other glyph has a layer: it wins   ", d); print("755 the package was not consulted:", P84["reads"])
p84_setup(refs=(("r1", "Alpha"), ("r2", "Beta"))); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
r84("756 glyphs disagree: NOT overridden    ", d); print("757 the package was not consulted:", P84["reads"], "| note", d["reason"][-60:])
p84_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
P72["mode"]["inactive"] = ("fresh",); c2, d2 = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
print("758 second draw: guard unchanged  :", d2["drawn"], "|", d2["reason"][:58], "| creates", creates84())
GATES84 = [
    ("761 no font counted              ", dict(count=0)),
    ("762 CountFonts raises            ", dict(count=RuntimeError("count boom"))), ("763 CountFonts returns True       ", dict(count=True)),
    ("764 CountFonts returns '1'       ", dict(count="1")), ("765 v0.150 the glyph names no package", dict(gp=None)),
    ("766 v0.150 w.package raises      ", dict(gp=RuntimeError("pk boom"))), ("767 no current package           ", dict(cp=None)),
    ("767b v0.150 current package null ", dict(cp_isNull=True)), ("767c v0.150 current isNull raises ", dict(cp_isNull=RuntimeError("cnull boom"))),
    ("767d v0.150 fgIds differ (5 / 8) ", dict(cp_fgId=8)), ("767e v0.150 glyph fgId is text    ", dict(gp_fgId="5")),
    ("767f v0.150 glyph fgId is a bool  ", dict(gp_fgId=True, cp_fgId=True)), ("767g v0.150 glyph fgId raises     ", dict(gp_fgId=RuntimeError("fg boom"))),
    ("767h v0.150 current fgId raises   ", dict(cp_fgId=RuntimeError("cfg boom"))), ("767i v0.150 current fgId is None  ", dict(cp_fgId=None)),
    ("768 currentPackage raises        ", dict(cp=RuntimeError("cp boom"))), ("769 package is null              ", dict(isNull=True)),
    ("770 isNull not a bool            ", dict(isNull="no")), ("771 isNull raises                ", dict(isNull=RuntimeError("null boom"))),
    ("772 two masters                  ", dict(mastersCount=2)), ("773 zero masters                 ", dict(mastersCount=0)),
    ("774 mastersCount is text         ", dict(mastersCount="1")), ("775 empty master name            ", dict(defaultMaster="", master="")),
    ("776 blank master name            ", dict(defaultMaster="  ", master="  ")), ("777 master name with newline     ", dict(defaultMaster="Reg\nular", master="Reg\nular")),
    ("778 master differs from default  ", dict(master="Bold")), ("779 master name not text         ", dict(defaultMaster=5, master=5)),
    ("780 master name 101 characters   ", dict(defaultMaster="R" * 101, master="R" * 101)), ("781 masters list has two names  ", dict(masters=["Regular", "Bold"])),
    ("782 masters list names another   ", dict(masters=["Light"])), ("783 glyph count differs          ", dict(glyphsCount=7)),
    ("784 glyph count not a number     ", dict(glyphsCount="two")), ("785 upm differs                  ", dict(upm=2048.0)),
    ("786 font unitsPerEm unreadable   ", dict(font_upm=None)), ("787 upm unreadable                ", dict(upm=RuntimeError("upm boom"))),
]
for tag, over in GATES84:
    p84_setup(**over); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); r84(tag, d, keys=("drawn", "layer_created"))
for tag, over in (("790 masters is a tuple: accepted   ", dict(masters=("Regular",))), ("791 masters not a plain list: skipped", dict(masters=object())),
                  ("792 masters unreadable: skipped    ", dict(masters=RuntimeError("masters boom"))), ("793 glyphsCount as float 1.0     ", dict(glyphsCount=1.0)),
                  ("794 other master name 'Light'      ", dict(defaultMaster="Light", master="Light", masters=["Light"])),
                  ("760 v0.150 two fonts open: accepted ", dict(count=2, packages=2)), ("760b v0.150 three fonts open: accepted", dict(count=3, packages=3)),
                  ("760c v0.150 packages() not read    ", dict(packages=RuntimeError("pk boom")))):
    p84_setup(**over); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); r84(tag, d, keys=("drawn", "layer_created", "layer_name_source"))
p84_setup(); _fm.CountFonts = None; del _fm.CountFonts
c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); r84("795 the module has no CountFonts      ", d, keys=("drawn", "layer_created"))
p84_setup(); print("796 v0.150 no wrapper: no master name:", ns["_derive_layer_name"](TfFont(), "fresh")[1][-80:], "| with a wrapper:", ns["_derive_layer_name"](TfFont(), "fresh", True, P72Mod(TS["fresh"], None)))
p84_setup(count=0); print("796b v0.150 direct call, CountFonts() 0:", ns["_package_layer_name"](TfFont(), P72Mod(TS["fresh"], None)), "| reads", P84["reads"])
p84_setup(refs=(("ref", "test_font"),)); print("797 other glyphs, with source    :", ns["_derive_layer_name"](TfFont(), "fresh", True), "| reads", P84["reads"])
p84_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); print("798 forbidden members called, whole run:", P84["forbidden"], "| addShape calls", P72["calls"].count("addShape"))
_src84 = src[src.index("def _pkg_get("):src.index('_EXISTING_LAYER_MAYBE = "the glyph may already have a layer"')]
print("799 static scan of the fallback  : forbidden call syntax found:", _re83.findall(r"\.(?:addPackage|createNewProject|closePackage|closeProject|saveProject|readProject|export\w*|save\w*|release|remove|close|resetPackage|setUpm|addMaster|addGlyph|setMaster|renameMaster|findLayerCreate)\s*\(", _src84), "| scanned chars > 3000:", len(_src84) > 3000)
_src150 = "\n".join(l.split("#")[0] for l in src.splitlines())
_body150 = lambda fn: _src150[_src150.index("def " + fn + "("):_src150.index("\ndef ", _src150.index("def " + fn + "(") + 5)]
print("799b v0.150 no isEqual in the product: layer name", ".isEqual(" in _body150("_package_layer_name"), "| create_font", ".isEqual(" in _body150("_create_font_in_front"),
      "| calls in the whole listener:", _src150.count(".isEqual("), "(4: research probes only, trynotify 1 call + 1 docstring, trypackage 2) | w.package read:", '_pkg_get(w, "package")' in _body150("_package_layer_name"))
c, d = call("/version"); print("800 version                      :", d)


# ================= v0.85: /debug/trysync (can a plain API call sync the modern layers? gated experiment; faked flPackage / flWorkspace) =================
TS85 = {"calls": [], "forbidden": [], "cfg": {}}
S85 = {"pkg": False, "ws": False}
def _ts85_spy(label):
    def f(self, *a, **k):
        TS85["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
class TS85Native: pass
def _ts85_flag(key, state_key):
    v = TS85["cfg"].get(key)
    if isinstance(v, Exception): raise v
    return S85[state_key]
class TS85Package:
    glyphsCount = 1
    def isNull(self):
        v = TS85["cfg"].get("isNull", False)
        if isinstance(v, Exception): raise v
        return v
    def isChanged(self): return _ts85_flag("pkg_changed_error", "pkg")
    def update(self):
        TS85["calls"].append("flPackage.update()")
        if TS85["cfg"].get("update_raises"): raise RuntimeError("package update refused")
        S85["pkg"] = True
        return TS85["cfg"].get("update_returns")
class TS85Workspace:
    @staticmethod
    def instance(): return TS85_WS
    def packages(self):
        v = TS85["cfg"].get("packages", 1)
        if isinstance(v, Exception): raise v
        return [TS85_PKG] * v
    @property
    def currentPackage(self):
        v = TS85["cfg"].get("cp", "auto")
        if isinstance(v, Exception): raise v
        return TS85_PKG if v == "auto" else v
    def isChanged(self): return _ts85_flag("ws_changed_error", "ws")
    def update(self):
        TS85["calls"].append("flWorkspace.update()")
        if TS85["cfg"].get("update_raises"): raise RuntimeError("workspace update refused")
        S85["ws"] = True
        return TS85["cfg"].get("update_returns")
for _n in ("blockUpdate", "unblockUpdate", "changed", "updateActiveViewport", "addPackage", "createNewProject", "closePackage", "closeProject", "saveProject",
           "exportFont", "readProject", "release", "remove", "close", "save", "resetPackage", "setUpm", "addMaster", "addGlyph"):
    setattr(TS85Package, _n, _ts85_spy("flPackage." + _n)); setattr(TS85Workspace, _n, _ts85_spy("flWorkspace." + _n))
TS85_PKG = TS85Package(); TS85_WS = TS85Workspace()
def _ts85_count():
    v = TS85["cfg"].get("count", 1)
    if isinstance(v, Exception): raise v
    return v
def ts85_setup(**cfg):
    TS85["calls"].clear(); TS85["forbidden"].clear(); TS85["cfg"] = dict(cfg); S85.update(pkg=False, ws=False)
    ns["_TRYSYNC"].update(package_update=0, workspace_update=0)
    for _m in _tf_mods:
        _m.flWorkspace = TS85Workspace; _m.CountFonts = _ts85_count
def t85(tag, path, keys=None):
    c, d = call(path)
    print(tag, ":", c, d if keys is None else {k: d.get(k) for k in keys}, "| calls", TS85["calls"])
    return d
ts85_setup(); t85("810 state, one font open              ", "/debug/trysync?stage=state")
t85("811 default stage is state          ", "/debug/trysync", keys=("stage", "calls_so_far"))
t85("812 package_update without go       ", "/debug/trysync?stage=package_update")
t85("813 workspace_update without go     ", "/debug/trysync?stage=workspace_update")
t85("814 go must be exactly yes          ", "/debug/trysync?stage=package_update&go=maybe")
t85("815 unknown stage                   ", "/debug/trysync?stage=bogus&go=yes")
t85("816 package_update                  ", "/debug/trysync?stage=package_update&go=yes", keys=("stage", "call", "return_value", "call_error", "before", "after", "calls_so_far"))
t85("817 workspace_update                ", "/debug/trysync?stage=workspace_update&go=yes", keys=("stage", "call", "return_value", "call_error", "before", "after", "calls_so_far"))
t85("818 package_update again, allowed   ", "/debug/trysync?stage=package_update&go=yes", keys=("call_error", "calls_so_far"))
ts85_setup(update_raises=1)
t85("819 package update raises           ", "/debug/trysync?stage=package_update&go=yes", keys=("call", "return_value", "call_error", "before", "after", "calls_so_far"))
t85("820 workspace update raises         ", "/debug/trysync?stage=workspace_update&go=yes", keys=("call", "return_value", "call_error", "calls_so_far"))
ts85_setup(update_returns=TS85Native())
t85("821 a native return value is typed  ", "/debug/trysync?stage=package_update&go=yes", keys=("return_value", "call_error"))
ts85_setup(pkg_changed_error=RuntimeError("pkg boom"), ws_changed_error=RuntimeError("ws boom"))
t85("822 isChanged raises: reported, call still made", "/debug/trysync?stage=package_update&go=yes", keys=("call_error", "before", "after", "calls_so_far"))
GATES85 = [
    ("830 no font open                ", dict(count=0)), ("831 two fonts open               ", dict(count=2)),
    ("832 CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("833 CountFonts returns True      ", dict(count=True)),
    ("834 CountFonts returns '1'      ", dict(count="1")), ("835 two packages                ", dict(packages=2)),
    ("836 packages() raises           ", dict(packages=RuntimeError("pk boom"))), ("837 no current package          ", dict(cp=None)),
    ("838 currentPackage raises       ", dict(cp=RuntimeError("cp boom"))), ("839 package is null             ", dict(isNull=True)),
    ("840 isNull not a bool           ", dict(isNull="no")), ("841 isNull raises               ", dict(isNull=RuntimeError("null boom"))),
    ("841a isNull is 0 (falsy, no bool)", dict(isNull=0)), ("841b isNull is None             ", dict(isNull=None)),
]
for tag, over in GATES85:
    ts85_setup(**over)
    rows = []
    for stage in ("state", "package_update&go=yes", "workspace_update&go=yes"):
        c, d = call("/debug/trysync?stage=" + stage); rows.append((c, (d.get("error") or "")[:70], "call" in d))
    print(tag, ":", rows, "| calls", TS85["calls"], "| counters", ns["_TRYSYNC"])
ts85_setup()
for _m in _tf_mods:
    if hasattr(_m, "CountFonts"): del _m.CountFonts
t85("842 the module has no CountFonts    ", "/debug/trysync?stage=package_update&go=yes", keys=("error", "calls_so_far"))
ts85_setup()
for _p in ("/debug/trysync?stage=state", "/debug/trysync?stage=package_update&go=yes", "/debug/trysync?stage=workspace_update&go=yes", "/debug/trysync?stage=package_update"): call(_p)
print("843 forbidden members called    :", TS85["forbidden"], "| calls", TS85["calls"])
_src85 = src[src.index("_TRYSYNC_STAGES = "):src.index("# /debug/trycreate (v0.86)")]
print("844 static scan of the probe     : forbidden call syntax found:", _re83.findall(r"\.(?:blockUpdate|unblockUpdate|changed|updateActiveViewport|addPackage|createNewProject|closePackage|closeProject|saveProject|readProject|export\w*|save\w*|release|remove|close|resetPackage|setUpm|addMaster|addGlyph|findLayerCreate)\s*\(", _src85),
      "| real update calls:", len(_re83.findall(r"target\.update\(", _src85)), "| scanned chars > 3000:", len(_src85) > 3000)
c, d = call("/version"); print("845 version                      :", d)


# ================= v0.86: /debug/trycreate (which part of create_glyph removes unsynced layers? gated experiment; faked font) =================
TC86 = {"font": None, "calls": [], "forbidden": [], "cfg": {}}
def _tc86_spy(label):
    def f(self, *a, **k):
        TC86["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
class TC86Glyph:
    def __init__(self, n): self.name = n
class TC86Font:
    def __init__(self, names): self.glyphs = [TC86Glyph(n) for n in names]
    def createGlyph(self, name):
        TC86["calls"].append("createGlyph")
        if TC86["cfg"].get("create_raises"): raise RuntimeError("createGlyph refused")
        if TC86["cfg"].get("create_noop"): return None
        self.glyphs.append(TC86Glyph(name.replace("-", "") if TC86["cfg"].get("create_renames") else name))
        return object()
    def update(self):
        TC86["calls"].append("update")
        if TC86["cfg"].get("update_raises"): raise RuntimeError("update refused")
for _n in ("removeGlyph", "remove", "delete", "save", "close", "export", "exportFont", "release", "blockUpdate", "unblockUpdate", "addGlyph", "clone"):
    setattr(TC86Font, _n, _tc86_spy("font." + _n))
def tc86_setup(names=(".notdef", "A"), ws=None, **cfg):
    ts85_setup(**(ws or {})); TC86["calls"].clear(); TC86["forbidden"].clear(); TC86["cfg"] = dict(cfg); TC86["font"] = TC86Font(names)
    ns["_TRYCREATE"].update(plain=0, legacy_update=0)
    for _m in _tf_mods: _m.CurrentFont = lambda: TC86["font"]
def t86(tag, query, keys=None):
    c, d = call("/debug/trycreate" + query)
    print(tag, ":", c, d if keys is None else {k: d.get(k) for k in keys}, "| names", [g.name for g in TC86["font"].glyphs] if TC86["font"] else None, "| calls", TC86["calls"])
    return d
KEYS86 = ("how", "name", "calls", "call_error", "update_error", "before_count", "after_count", "present", "created", "calls_so_far", "created_under_other_names")
tc86_setup(); t86("850 no go                        ", "?name=X1&how=plain")
t86("851 go must be exactly yes          ", "?name=X1&how=plain&go=maybe")
t86("852 unknown how                     ", "?name=X1&how=bogus&go=yes")
t86("853 how missing                     ", "?name=X1&go=yes")
t86("854 plain: createGlyph only         ", "?name=X1&how=plain&go=yes", keys=KEYS86)
t86("855 legacy_update: create + update  ", "?name=X2&how=legacy_update&go=yes", keys=KEYS86)
t86("856 existing name refused           ", "?name=X1&how=plain&go=yes", keys=("error", "before_count", "calls_so_far"))
for _tag, _nm in (("857 empty name                   ", ""), ("858 name of 41 characters         ", "N" * 41), ("859 name with a space             ", "A%20B"),
                  ("860 name with a slash             ", "A%2FB"), ("861 non-ASCII name                ", "%C3%A4"), ("862 name with a semicolon         ", "A%3Bb")):
    t86(_tag, "?name=" + _nm + "&how=plain&go=yes", keys=("error", "calls_so_far"))
t86("863 name of 40 characters, accepted ", "?name=" + "N" * 40 + "&how=plain&go=yes", keys=("created", "calls_so_far"))
tc86_setup(create_raises=1); t86("864 plain, createGlyph raises      ", "?name=X1&how=plain&go=yes", keys=KEYS86)
tc86_setup(create_raises=1); t86("865 legacy_update, createGlyph raises", "?name=X1&how=legacy_update&go=yes", keys=KEYS86)
tc86_setup(create_noop=1); t86("866 createGlyph does nothing       ", "?name=X1&how=plain&go=yes", keys=KEYS86)
tc86_setup(create_renames=1); t86("867 createGlyph renames           ", "?name=X-1&how=plain&go=yes", keys=KEYS86)
tc86_setup(update_raises=1); t86("868 font.update raises             ", "?name=X1&how=legacy_update&go=yes", keys=KEYS86)
tc86_setup(update_raises=1); t86("869 plain never calls update        ", "?name=X1&how=plain&go=yes", keys=("created", "update_error"))
GATES86 = [("870 no font counted             ", dict(count=0)), ("871 two fonts open              ", dict(count=2)),
           ("872 CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("873 two packages               ", dict(packages=2)),
           ("874 no current package          ", dict(cp=None)), ("875 package is null             ", dict(isNull=True)),
           ("876 isNull is 0 (falsy, no bool)", dict(isNull=0))]
for _tag, _over in GATES86:
    tc86_setup(ws=_over); c, d = call("/debug/trycreate?name=X1&how=plain&go=yes")
    print(_tag, ":", c, (d.get("error") or "")[:70], "| calls", TC86["calls"], "| counters", ns["_TRYCREATE"], "| names", [g.name for g in TC86["font"].glyphs])
tc86_setup(); _fonts_none = [m.CurrentFont for m in _tf_mods]
for _m in _tf_mods: _m.CurrentFont = lambda: None
c, d = call("/debug/trycreate?name=X1&how=plain&go=yes"); print("877 no current font object       :", c, d, "| counters", ns["_TRYCREATE"])
tc86_setup()
for _q in ("?name=P1&how=plain&go=yes", "?name=P2&how=legacy_update&go=yes", "?name=P3&how=plain", "?name=P4&how=legacy_update&go=maybe"): call("/debug/trycreate" + _q)
print("878 forbidden members called     :", TC86["forbidden"], "| calls", TC86["calls"], "| names", [g.name for g in TC86["font"].glyphs])
_src86 = src[src.index("_TRYCREATE_HOWS = "):src.index("def debug_layer_item(")]
print("879 static scan of the probe     : forbidden call syntax found:", _re83.findall(r"\.(?:removeGlyph|remove|delete\w*|save\w*|close|export\w*|release|blockUpdate|unblockUpdate|addGlyph|addPackage|createNewProject|closePackage|closeProject|saveProject|readProject|updateActiveViewport)\s*\(", _src86),
      "| real createGlyph calls:", len(_re83.findall(r"(?m)^\s+font\.createGlyph\(name\)$", _src86)), "| real font.update calls:", len(_re83.findall(r"(?m)^\s+font\.update\(\)$", _src86)), "| scanned chars > 2000:", len(_src86) > 2000)
print("880 create_glyph itself unchanged:", "font.createGlyph(name)" in src[src.index("def create_glyph("):src.index("def _confirm_deletion(")], "| still calls font.update():", "font.update()" in src[src.index("def create_glyph("):src.index("def _confirm_deletion(")])
c, d = call("/version"); print("881 version                      :", d)
for _m, _a, _v in _tf_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)


# ================= v0.87: guard - no legacy update call while a drawn layer is unsynced (faked font that WIPES unsynced layers on update, like FontLab) =================
G87 = {"calls": [], "cfg": {}}
_orig_confirm87 = ns["_confirm_deletion"]
class G87Font(TsFont):
    @property
    def path(self): return G87["cfg"].get("path", "ts")
    def createGlyph(self, name):
        G87["calls"].append("createGlyph"); TS[name] = TsGlyph(name, []); TS[name].update = (lambda n=name: G87["calls"].append("glyph.update"))
    def removeGlyph(self, name):
        G87["calls"].append("removeGlyph"); TS.pop(name, None)
    def update(self):
        G87["calls"].append("font.update")
        for _n in list(P72["layers"]):                       # what FontLab really does (v0.85 / v0.86 live): unsynced layers are thrown away
            if _n in TS and not TS[_n]._layers: P72["layers"].pop(_n)
def g87_setup(mode=None, refs=(("ref", "test_font"),), empties=("fresh",), **cfg):
    p72_setup(mode=mode, refs=refs, empties=empties); G87["calls"].clear(); G87["cfg"] = dict(cfg)
    for _g in TS.values(): _g.update = (lambda n=_g.name: G87["calls"].append("glyph.update"))
    ns["_UNSYNCED"].update(font=None, overflow=False); ns["_UNSYNCED"]["glyphs"].clear(); ns["_UNSYNCED_MAX"] = 500
    ns["_confirm_deletion"] = lambda n, s=45: {"answer": "yes", "seconds": s}   # v0.203: the dialog's result
    _fm.CurrentFont = lambda: G87Font()
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
def g87_sync(name, nodes, width=None):
    TS[name]._layers = [TsLayer(1, nodes)]
    if width is not None: TS[name].width = width; P72["widths"][name] = width
def g87_show(tag, c, d, keys=()):
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", G87["calls"], "| layers", sorted(P72["layers"]), "| tracked", sorted(ns["_UNSYNCED"]["glyphs"]))
K87 = ("created", "deleted", "set", "display_refresh", "display_refresh_skipped_to_protect", "display_refresh_unreadable_glyphs", "layers_missing_since_drawn")
g87_setup(); c, d = sbpost("/glyph/create", {"name": "n1"}); g87_show("890 nothing tracked: update runs      ", c, d, K87)
g87_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
g87_show("891 draw: reply says not synced        ", c, d, ("drawn", "synced_with_fontlab")); print("891b durability note present  :", "durability_note" in d, "| mentions create_glyph:", "create_glyph" in d.get("durability_note", ""))
c, d = sbpost("/glyph/create", {"name": "n1"}); g87_show("892 create: update skipped, layer kept ", c, d, K87); print("892b note                     :", d.get("display_refresh_note", "")[:60])
c, d = sbpost("/glyph/delete", {"name": "n1"}); g87_show("893 delete: update skipped             ", c, d, K87)
TS["other"] = TsGlyph("other", []); TS["other"].update = (lambda: G87["calls"].append("glyph.update")); TS["other"].unicode = None
c, d = sbpost("/glyph/unicode", {"name": "other", "unicode": 65}); g87_show("894 unicode elsewhere: no update calls ", c, d, K87)
c, d = sbpost("/glyph/unicode", {"name": "fresh", "unicode": 66}); g87_show("895 unicode on the drawn glyph itself  ", c, d, K87)
g87_setup(refs=(("r1", "Alpha"), ("r2", "Beta")), empties=("fresh", "other")); c, d = p72_post("/glyph/width", {"name": "r1", "width": 640}); g87_show("896a modern width on r1 remembered       ", c, d, ("set", "synced_with_fontlab"))
G87["calls"].clear(); c, d = p72_post("/glyph/width", {"name": "other", "width": 640}); g87_show("896b legacy width route: no updates   ", c, d, ("set", "route", "display_refresh", "display_refresh_skipped_to_protect"))
g87_setup(refs=(("r1", "Alpha"), ("r2", "Beta")), empties=("fresh", "other")); c, d = p72_post("/glyph/width", {"name": "other", "width": 640}); g87_show("896c legacy width route, nothing tracked ", c, d, ("set", "route", "display_refresh"))
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); g87_sync("fresh", 4, width=500.0); G87["calls"].clear()
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("897 synced: forgotten, update runs     ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); g87_sync("fresh", 4, width=500.0); TS["fresh"].width = 480.0
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("898 widths differ: still at risk       ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); g87_sync("fresh", 3, width=500.0)
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("899 node counts differ: at risk        ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); TS.pop("fresh")
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("900 glyph gone: forgotten, update runs ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); P72["layers"].pop("fresh")
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("901 layer lost already: reported       ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
class _G87Bad(TsGlyph):
    @property
    def layers(self): raise RuntimeError("layers boom")
TS["fresh"].__class__ = _G87Bad
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("902 legacy layers unreadable: skip     ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); _fm.flGlyph = type("Boom", (), {"__init__": lambda s, g, f: (_ for _ in ()).throw(RuntimeError("wrapper boom"))})
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("903 modern wrapper fails: skip         ", c, d, K87); _fm.flGlyph = P72Mod
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); _real_state = ns["_guard_state"]
def _boom_state(font): raise RuntimeError("state boom")
ns["_guard_state"] = _boom_state
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("904 guard itself fails: skip, no raise ", c, d, K87); print("904b note                     :", d.get("display_refresh_note", "")[:60]); ns["_guard_state"] = _real_state
g87_setup(); ns["_UNSYNCED_MAX"] = 2
for _n in ("e1", "e2", "e3"):
    TS[_n] = TsGlyph(_n, []); p72_post("/glyph/polygon", {"name": _n, "points": TRI4})
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("905 more than the cap: overflow skip   ", c, d, K87); print("905b overflow flag/note       :", ns["_UNSYNCED"]["overflow"], d.get("display_refresh_note", "")[:40])
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); G87["cfg"]["path"] = "other-font"
c, d = sbpost("/glyph/create", {"name": "n2"}); g87_show("906 another font: registry reset       ", c, d, K87)
g87_setup(mode={"add_raises": 1}); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); g87_show("907 draw fails after layer creation   ", c, d, ("drawn", "synced_with_fontlab"))
g87_setup(); c, d = p72_post("/glyph/polygon", {"name": "tri", "points": TRI4}); g87_setup(); TS["comp"] = TsGlyph("comp", [], comps=1)
c, d = p72_post("/glyph/polygon", {"name": "comp", "points": TRI4}); g87_show("908 refused draw: nothing remembered     ", c, d, ("drawn", "synced_with_fontlab"))
g87_setup(); p81_setup(); _fm.CurrentFont = lambda: G87Font(); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); g87_show("909 draw_path remembers               ", c, d, ("drawn", "synced_with_fontlab"))
g87_setup(); c, d = p72_post("/glyph/width", {"name": "fresh", "width": 640}); g87_show("910 modern width remembers             ", c, d, ("set", "synced_with_fontlab"))
c, d = sbpost("/glyph/create", {"name": "n3"}); g87_show("911 create after width only: skipped   ", c, d, K87)
g87_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); G87["calls"].clear()
for _k in range(3): sbpost("/glyph/create", {"name": "m%d" % _k})
print("912 three creates, all skipped   :", G87["calls"], "| layers", sorted(P72["layers"]))
g87_setup(); c, d = sbpost("/glyph/create", {"name": "ref"}); print("913 no regression: duplicate name   :", c, {k: d.get(k) for k in K87 if k in d})
_src87 = src[src.index("# v0.87 guard:"):src.index("def create_glyph(")]
print("914 static scan of the guard     : forbidden call syntax found:", _re83.findall(r"\.(?:update|save\w*|export\w*|generate\w*|close|release|remove\w*|delete\w*|createGlyph|blockUpdate|unblockUpdate)\s*\(", _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _src87)), "| scanned chars > 3000:", len(_src87) > 3000)
_fns87 = [src[src.index(a):src.index(b)] for a, b in (("def create_glyph(", "def _confirm_deletion("), ("def delete_glyph(", "def debug_glyph_info("), ("def _set_width_legacy(", "def set_glyph_width("), ("def set_glyph_unicode(", "class _RecordingPen:"))]
print("915 every legacy update is guarded:", [(f.count("_guard_decide(font)"), f.count("if guard_ok:"), f.count(".update()")) for f in _fns87])
c, d = call("/version"); print("916 version                      :", d)
ns["_UNSYNCED"].update(font=None, overflow=False); ns["_UNSYNCED"]["glyphs"].clear(); _fm.CurrentFont = lambda: TsFont(); sbx_setup()
c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77}); print("917 sidebearings change remembered:", c, {k: d.get(k) for k in ("set", "changed", "synced_with_fontlab")}, "| tracked", sorted(ns["_UNSYNCED"]["glyphs"]))
ns["_UNSYNCED"]["glyphs"].clear(); c, d = sbpost("/glyph/sidebearings", {"name": "tri", "left": 88, "right": 77}); print("918 same values again: not remembered:", {k: d.get(k) for k in ("set", "changed", "synced_with_fontlab")}, "| tracked", sorted(ns["_UNSYNCED"]["glyphs"]))
_fm.CurrentFont = lambda: TsFont(); ns["_confirm_deletion"] = _orig_confirm87; ns["_UNSYNCED_MAX"] = 500


# ================= v0.88: reader - margins compared when the node counts agree (stale legacy view); modern_outline attached on a mismatch =================
F88 = {"m": (1.5, 2.5, 500.0)}
class F88Mod(P72Mod):
    def getLSB(s, tr):
        if F88.get("raises"): raise RuntimeError("getLSB boom")
        return F88["m"][0]
    def getRSB(s, tr): return F88["m"][1]
    @property
    def advanceWidth(s): return F88["m"][2]
def f88_setup(legacy=(1.5, 2.5, 500.0), modern=(1.5, 2.5, 500.0), legacy_nodes=3, modern_nodes=3, points=3, mode=None, glyph="st88"):
    p72_setup(refs=(), empties=(), mode=mode); F88.clear(); F88["m"] = modern
    g = TsGlyph(glyph, [TsLayer(1, legacy_nodes)]); g.leftMargin, g.rightMargin, g.width = legacy; TS[glyph] = g
    lay = P72Layer("test_font", 1, modern_nodes)
    ct = P72Contour([P72Pt(0, 0), P72Pt(400, 0), P72Pt(400, 300), P72Pt(0, 300)][:points]); ct.closed = True; lay._contours = [ct]
    P72["layers"][glyph] = lay; P72["calls"].clear()
    _fm.flGlyph = F88Mod; ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
def f88_get(tag, path="/glyph/outline?name=st88"):
    c, d = call(path); mc = d.get("modern_check", {}); mo = d.get("modern_outline")
    print(tag, ":", c, "node_count", d.get("node_count"), "| check", {k: v for k, v in mc.items() if k not in ("available", "modern_layer")},
          "| modern_outline", None if mo is None else {"available": mo.get("available"), "nodes": mo.get("node_count"), "margins": mo.get("margins"), "error": (mo.get("error") or "")[:50] or None})
    return d
f88_setup(); f88_get("920 margins agree                   ")
f88_setup(modern=(21.5, 2.5, 500.0)); f88_get("921 stale: left differs              ")
f88_setup(modern=(1.5, 12.5, 500.0)); f88_get("922 stale: right differs             ")
f88_setup(modern=(1.5, 2.5, 520.0)); f88_get("923 stale: advance differs           ")
f88_setup(modern=(1.54, 2.46, 500.04)); f88_get("924 differences of 0.04 tolerated    ")
f88_setup(modern=(1.56, 2.5, 500.0)); f88_get("925 difference of 0.06 flagged        ")
f88_setup(modern=(21.5, 2.5, 500.0), modern_nodes=4, points=4); f88_get("926 counts disagree: old trigger, no margins")
f88_setup(); F88["raises"] = 1; f88_get("927 modern getter raises: unknown      ")
f88_setup(); del qg.QTransform; f88_get("928 no QTransform: unknown             "); qg.QTransform = QTransformStub
f88_setup(); TS["st88"].leftMargin = None; f88_get("929 legacy margin not a number: unknown")
f88_setup(modern=(21.5, 2.5, 500.0)); f88_get("930 modern=no: nothing at all          ", "/glyph/outline?name=st88&modern=no")
f88_setup(modern=(21.5, 2.5, 500.0)); P72["layers"].pop("st88"); f88_get("931 no modern layer                  ")
f88_setup(legacy_nodes=0, modern_nodes=0, modern=(21.5, 2.5, 500.0)); f88_get("932 modern layer empty: not compared   ")
f88_setup(modern=(21.5, 2.5, 500.0), mode={"contours_type": "raises"}); f88_get("933 stale, outline unreadable: attached  ")
f88_setup(modern=(21.5, 2.5, 500.0)); f88_get("934a stale read"); print("934 reader wrote nothing         :", [x for x in P72["calls"] if x != "flContour"])
f88_setup(); print("935 old two-argument call        :", ns["_reader_modern_check"]("st88", 3))
print("936 margins argument not a dict  :", ns["_reader_modern_check"]("st88", 3, "bad"))
print("937 direct compare, missing key  :", ns["_reader_margins_compare"](F88Mod(TS["st88"], None), {"left": 1.5}))
_src88 = src[src.index("_READER_MARGIN_TOLERANCE = 0.05"):src.index("_MODERN_OUTLINE_MAX_NODES = 5000")]
_code88 = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _src88)
print("938 static scan of the compare   : forbidden call syntax found:", _re83.findall(r"(?<!out)\.(?:set\w*|update\w*|save\w*|export\w*|findLayerCreate|addShape|addLayer\w*|createGlyph|removeGlyph|release|remove\w*|convert\w*|move\w*)\s*\(", _code88),
      "| getLSB / getRSB reads in the helper:", _src88.count("_modern_margins_read(w, tr)"), "| scanned chars > 1500:", len(_src88) > 1500)
c, d = call("/version"); print("939 version                      :", d)


# ================= v0.88: /debug/trymodern (modern glyph creation and sync candidates; gated experiment; faked flPackage / flGlyph / Update) =================
M88 = {"calls": [], "forbidden": [], "cfg": {}, "extra": 0}
def _m88_spy(label):
    def f(self, *a, **k):
        M88["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
def m88_effect(name):
    e = M88["cfg"].get("effect")
    if e == "sync" and name in TS: g87_sync(name, 4, width=500.0)
    elif e == "wipe": P72["layers"].pop(name, None)
class M88Mod(P72Mod):
    def __init__(s, glyph=None, font=None):
        if glyph is None:
            M88["calls"].append("flGlyph()")
            if M88["cfg"].get("ctor_raises"): raise RuntimeError("flGlyph() boom")
            object.__setattr__(s, "name", ""); object.__setattr__(s, "fgGlyphId", None); object.__setattr__(s, "_detached", True)
        else:
            P72Mod.__init__(s, glyph, font); object.__setattr__(s, "_detached", False)
    def __setattr__(s, k, v):
        if k == "name" and getattr(s, "_detached", False):
            M88["calls"].append("glyph.name=")
            if M88["cfg"].get("name_raises"): raise AttributeError("name is read-only")
            if M88["cfg"].get("name_ignored"): return
        object.__setattr__(s, k, v)
    def updatedFgGlyphs(s):
        M88["calls"].append("updatedFgGlyphs")
        v = M88["cfg"].get("ids", [])
        if isinstance(v, Exception): raise v
        return v
    def fillFgData(s, g, h):
        M88["calls"].append(("fillFgData", g, h)); m88_effect(s.name)
        if M88["cfg"].get("call_raises"): raise RuntimeError("fillFgData refused")
        return object()
for _n in ("assignFontGateData", "ensureFgData", "release", "remove", "blockUpdate", "unblockUpdate", "removeLayer", "addLayer", "setLayers"):
    setattr(M88Mod, _n, _m88_spy("flGlyph." + _n))
class M88Found:
    def isNull(s): return False
class M88Package(TS85Package):
    @property
    def glyphsCount(s): return len(TS) + M88["extra"]
    def addGlyph(s, g):
        M88["calls"].append(("addGlyph", g.name)); c = M88["cfg"]
        if c.get("add_raises"): raise RuntimeError("addGlyph refused")
        if c.get("add_noop"): return None
        if c.get("add_invisible"): M88["extra"] += 1; return True
        _nm = g.name.replace("-", "") if c.get("add_renames") else g.name
        TS[_nm] = TsGlyph(_nm, []); return True
    def findName(s, name):
        M88["calls"].append(("findName", name)); c = M88["cfg"]
        if c.get("find_raises"): raise RuntimeError("findName boom")
        return M88Found() if (name in TS or M88["extra"]) else None
    def prepareFontGateData(s, b):
        M88["calls"].append(("prepareFontGateData", b))
        for _n in list(ns["_UNSYNCED"]["glyphs"]): m88_effect(_n)
        if M88["cfg"].get("call_raises"): raise RuntimeError("prepareFontGateData refused")
        return None
for _n in ("replaceGlyph", "deleteGlyph", "renameGlyph", "activateGlyph", "assignData", "completeData", "ensureProteusData", "generateGlyph"):
    setattr(M88Package, _n, _m88_spy("flPackage." + _n))
P72Layer.assignFgLayer = _m88_spy("flLayer.assignFgLayer")
def _m88_update(*a):
    M88["calls"].append(("Update",) + tuple(type(x).__name__ for x in a))
    if M88["cfg"].get("call_raises"): raise RuntimeError("Update refused")
    for x in a: m88_effect(getattr(x, "name", None))
    return M88["cfg"].get("returns")
def _m88_updateall():
    M88["calls"].append("UpdateAll")
    if M88["cfg"].get("call_raises"): raise RuntimeError("UpdateAll refused")
    for _n in list(ns["_UNSYNCED"]["glyphs"]): m88_effect(_n)
_TS85_PKG_ORIG = TS85_PKG
def m88_setup(draw=True, cfg=None, ws=None):
    global TS85_PKG
    g87_setup(); ns["_AUTO_SYNC"] = False        # v0.89: the probe tests need a drawn glyph that stays unsynced (auto sync would sync it at once)
    if draw: p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})        # layer created, 4 nodes, remembered by the guard, legacy view still empty
    ts85_setup(**(ws or {})); TS85_PKG = M88Package()
    M88["calls"].clear(); M88["forbidden"].clear(); M88["cfg"] = dict(cfg or {}); M88["extra"] = 0
    for _k in ns["_TRYMODERN"]: ns["_TRYMODERN"][_k] = 0
    for _m in _tf_mods:
        _m.flGlyph = M88Mod; _m.Update = _m88_update; _m.UpdateAll = _m88_updateall
        for _n in ("UpdateGlyphRect", "UpdateActiveCanvas", "SetCurrentGlyph", "SetCurrentFont"): setattr(_m, _n, _m88_spy("fontlab." + _n))
    _fm.CurrentFont = lambda: G87Font()
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
def t88(tag, query, keys=None):
    c, d = call("/debug/trymodern" + query)
    print(tag, ":", c, d if keys is None else {k: d.get(k) for k in keys}, "| calls", M88["calls"])
    return d
def g88(d):
    g = d.get("glyph") or {}
    return {"found": g.get("found"), "legacy_layers": (g.get("legacy") or {}).get("layers"), "modern": (g.get("modern") or {}).get("active_layer"),
            "modern_nodes": (g.get("modern") or {}).get("nodes"), "updated_fg_glyphs": g.get("updated_fg_glyphs"), "legacy_width": g.get("legacy_width"),
            "modern_advance": g.get("modern_advance"), "verdict": g.get("verdict")}
def sum88(d):
    if "before" not in d: return {k: d.get(k) for k in ("stage", "how", "error", "calls_so_far")}
    return {"how": d["how"], "return_value": d["return_value"], "call_error": d["call_error"], "layer_lost": d["layer_lost"], "synced_after": d["synced_after"],
            "verdicts": (d["before"]["glyph"].get("verdict"), d["after"]["glyph"].get("verdict")), "registry": (d["before"]["registry"], d["after"]["registry"]),
            "after_modern": (d["after"]["glyph"].get("modern") or {}).get("active_layer"), "after_legacy_layers": (d["after"]["glyph"].get("legacy") or {}).get("layers"),
            "counters": d["calls_so_far"]}
m88_setup(); d = t88("940 state, drawn glyph                 ", "?stage=state&name=fresh"); print("940b                              :", g88(d), "| registry", d["registry"], "| counters", d["calls_so_far"])
m88_setup(cfg=dict(ids=[5, 7])); d = t88("941 state, updatedFgGlyphs ids         ", "?name=fresh"); print("941b default stage is state       :", d["stage"], d["glyph"]["updated_fg_glyphs"])
for _tag, _ids in (("942a ids object, not a list      ", object()), ("942b ids with a text element    ", ["a"]), ("942c ids raises                 ", RuntimeError("ids boom")), ("942d bool inside ids            ", [True])):
    m88_setup(cfg=dict(ids=_ids)); d = call("/debug/trymodern?name=fresh")[1]; print(_tag, ":", d["glyph"]["updated_fg_glyphs"])
m88_setup(cfg=dict(ids=list(range(60)))); d = call("/debug/trymodern?name=fresh")[1]; ids = d["glyph"]["updated_fg_glyphs"]; print("943 ids truncated to 50          :", ids["count"], len(ids["ids"]))
m88_setup(); d = t88("944 state, unknown glyph              ", "?stage=state&name=nope", keys=("glyph", "registry"))
m88_setup(); t88("945 call without go                  ", "?stage=call&how=fillFgData&name=fresh")
t88("946 go must be exactly yes            ", "?stage=call&how=fillFgData&name=fresh&go=maybe")
t88("947 create without go                 ", "?stage=create&name=newg")
t88("948 how missing                       ", "?stage=call&name=fresh&go=yes")
t88("949 how unknown                       ", "?stage=call&how=assignFgLayer&name=fresh&go=yes")
t88("950 stage unknown                     ", "?stage=bogus&name=fresh&go=yes")
for _tag, _nm in (("951a empty name                   ", ""), ("951b name of 41 characters         ", "N" * 41), ("951c name with a space             ", "A%20B"),
                  ("951d name with a slash             ", "A%2FB"), ("951e non-ASCII name                ", "%C3%A4"), ("951f name with a semicolon         ", "A%3Bb")):
    for _st in ("state", "call&how=Update_all&go=yes", "create&go=yes"):
        c, d = call("/debug/trymodern?stage=" + _st + "&name=" + _nm); print(_tag, _st.split("&")[0].ljust(6), ":", c, d.get("error"))
print("951g calls so far                :", M88["calls"], "| counters", ns["_TRYMODERN"])
m88_setup(); d = t88("952 Update(legacy glyph), no effect    ", "?stage=call&how=Update_fgGlyph&name=fresh&go=yes", keys=()); print("952b                              :", sum88(d))
m88_setup(cfg=dict(effect="sync", returns=True)); d = t88("953 Update(legacy glyph) SYNCS          ", "?stage=call&how=Update_fgGlyph&name=fresh&go=yes", keys=()); print("953b                              :", sum88(d))
m88_setup(cfg=dict(effect="wipe")); d = t88("954 Update(legacy glyph) WIPES          ", "?stage=call&how=Update_fgGlyph&name=fresh&go=yes", keys=()); print("954b                              :", sum88(d))
m88_setup(cfg=dict(effect="sync")); d = t88("955 Update(modern glyph)                ", "?stage=call&how=Update_flGlyph&name=fresh&go=yes", keys=()); print("955b                              :", sum88(d))
m88_setup(cfg=dict(effect="sync")); d = t88("956 UpdateAll()                         ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=()); print("956b                              :", sum88(d))
m88_setup(cfg=dict(effect="sync")); d = t88("957 fillFgData(False, False)            ", "?stage=call&how=fillFgData&name=fresh&go=yes", keys=()); print("957b                              :", sum88(d))
m88_setup(cfg=dict(effect="sync")); d = t88("958 prepareFontGateData(False)          ", "?stage=call&how=prepareFontGateData&name=fresh&go=yes", keys=()); print("958b                              :", sum88(d))
m88_setup(cfg=dict(call_raises=1)); d = t88("959 the call raises                    ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=()); print("959b                              :", sum88(d))
m88_setup(); t88("960a first call", "?stage=call&how=fillFgData&name=fresh&go=yes", keys=()); d = t88("960 same how again: refused            ", "?stage=call&how=fillFgData&name=fresh&go=yes", keys=("error", "calls_so_far"))
d = t88("961 another how is still allowed      ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=("call_error", "calls_so_far"))
m88_setup(draw=False); d = t88("962 glyph not remembered: refused    ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=("error", "calls_so_far"))
m88_setup(); d = t88("963 unknown glyph: refused             ", "?stage=call&how=Update_all&name=nope&go=yes", keys=("error", "calls_so_far"))
GATES88 = [("964a no font counted            ", dict(count=0)), ("964b two fonts open             ", dict(count=2)), ("964c CountFonts raises          ", dict(count=RuntimeError("count boom"))),
           ("964d two packages               ", dict(packages=2)), ("964e no current package         ", dict(cp=None)), ("964f package is null            ", dict(isNull=True)),
           ("964g isNull is 0 (falsy, no bool)", dict(isNull=0))]
for _tag, _over in GATES88:
    m88_setup(ws=_over); rows = []
    for _q in ("?stage=state&name=fresh", "?stage=call&how=Update_all&name=fresh&go=yes", "?stage=create&name=newg&go=yes"):
        c, d = call("/debug/trymodern" + _q); rows.append((c, (d.get("error") or "")[:48]))
    print(_tag, ":", rows, "| calls", M88["calls"], "| counters", ns["_TRYMODERN"])
m88_setup()
for _m in _tf_mods:
    if hasattr(_m, "CountFonts"): del _m.CountFonts
t88("965 the module has no CountFonts      ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=("error", "calls_so_far"))
m88_setup(); _fm.CurrentFont = lambda: None; c, d = call("/debug/trymodern?stage=call&how=Update_all&name=fresh&go=yes"); print("966 no current font object       :", c, d, "| calls", M88["calls"])
m88_setup(); _fm.flGlyph = type("Boom", (), {"__init__": lambda s, g=None, f=None: (_ for _ in ()).throw(RuntimeError("wrapper boom"))})
d = t88("967 modern wrapper fails: refused      ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=("error", "calls_so_far")); d = call("/debug/trymodern?stage=state&name=fresh")[1]; print("967b state shows the failure      :", d["glyph"].get("modern_error"), "|", d["glyph"].get("verdict"))
m88_setup(); _real_gs88 = ns["_guard_state"]
def _boom88(font): raise RuntimeError("state boom")
ns["_guard_state"] = _boom88
d = t88("968 guard registry unreadable           ", "?stage=call&how=Update_all&name=fresh&go=yes", keys=("error", "calls_so_far")); d = call("/debug/trymodern?stage=state&name=fresh")[1]; print("968b state shows registry error    :", d["registry"])
ns["_guard_state"] = _real_gs88
m88_setup(); d = t88("969 create, visible to the legacy font", "?stage=create&name=newg&go=yes", keys=())
print("969b                              :", {k: d.get(k) for k in ("steps", "name_read_back", "return_value", "call_error", "before_count", "after_count", "present_in_legacy_font", "created", "package_glyphsCount_before", "package_glyphsCount_after", "package_findName", "calls_so_far")})
print("969c new glyph / registry        :", {k: (d["new_glyph"] or {}).get(k) for k in ("found", "verdict")}, "| legacy layers", ((d["new_glyph"] or {}).get("legacy") or {}).get("layers"), "|", d["registry_before"], d["registry_after"], "| note", d["note"][:34])
m88_setup(cfg=dict(name_ignored=1)); d = t88("970 name not accepted: NOT added        ", "?stage=create&name=newg&go=yes", keys=("steps", "name_read_back", "call_error", "created", "present_in_legacy_font"))
m88_setup(cfg=dict(name_raises=1)); d = t88("971 name setter raises: NOT added        ", "?stage=create&name=newg&go=yes", keys=("steps", "call_error", "created"))
m88_setup(cfg=dict(ctor_raises=1)); d = t88("972 flGlyph() raises                    ", "?stage=create&name=newg&go=yes", keys=("steps", "call_error", "created"))
m88_setup(cfg=dict(add_raises=1)); d = t88("973 addGlyph raises                      ", "?stage=create&name=newg&go=yes", keys=("steps", "call_error", "created", "present_in_legacy_font"))
m88_setup(cfg=dict(add_noop=1)); d = t88("974 addGlyph does nothing                ", "?stage=create&name=newg&go=yes", keys=("steps", "return_value", "created", "present_in_legacy_font", "package_findName"))
m88_setup(cfg=dict(add_invisible=1)); d = t88("975 package counts it, legacy font does not", "?stage=create&name=newg&go=yes", keys=("created", "present_in_legacy_font", "package_glyphsCount_before", "package_glyphsCount_after", "package_findName", "new_glyph"))
m88_setup(cfg=dict(find_raises=1)); d = t88("976 findName raises                     ", "?stage=create&name=newg&go=yes", keys=("created", "package_findName"))
m88_setup(cfg=dict(add_renames=1)); d = t88("977 added under another name            ", "?stage=create&name=n-g&go=yes", keys=("created", "present_in_legacy_font", "created_under_other_names"))
m88_setup(); d = t88("978 existing name refused               ", "?stage=create&name=fresh&go=yes", keys=("error", "before_count", "calls_so_far"))
m88_setup(); t88("979a first create", "?stage=create&name=newg&go=yes", keys=()); d = t88("979 second create refused               ", "?stage=create&name=newh&go=yes", keys=("error", "calls_so_far"))
m88_setup(draw=False); d = t88("980 create needs no remembered glyph    ", "?stage=create&name=newg&go=yes", keys=("created", "registry_before", "registry_after"))
m88_setup(cfg=dict(effect="sync"))
for _q in ("?stage=state&name=fresh", "?stage=call&how=Update_fgGlyph&name=fresh&go=yes", "?stage=call&how=Update_flGlyph&name=fresh&go=yes", "?stage=call&how=Update_all&name=fresh&go=yes",
           "?stage=call&how=fillFgData&name=fresh&go=yes", "?stage=call&how=prepareFontGateData&name=fresh&go=yes", "?stage=create&name=newg&go=yes", "?stage=create&name=newh&go=yes"):
    call("/debug/trymodern" + _q)
print("981 forbidden members called     :", M88["forbidden"], "| pkg.update / other recorded package calls:", TS85["calls"])
_src88b = src[src.index("_TRYMODERN_STAGES = "):src.index("# HTTP plumbing")]
_code88b = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', "\n".join(l for l in _src88b.splitlines() if not l.lstrip().startswith("#")))
print("982 static scan of the probe     : forbidden call syntax found:", _re83.findall(r"\.(?:assign\w*|replaceGlyph|deleteGlyph|removeGlyph|remove\w*|save\w*|close\w*|export\w*|release|blockUpdate|unblockUpdate|createGlyph|update|updateFgGlyph|clearUpdateFgGlyphs|setLayers|addLayer\w*|addShape|findLayerCreate|convert\w*)\s*\(", _code88b),
      "| real calls: Update", len(_re83.findall(r"mod\.Update\(", _code88b)), "UpdateAll", len(_re83.findall(r"mod\.UpdateAll\(", _code88b)), "fillFgData", len(_re83.findall(r"w\.fillFgData\(False, False\)", _code88b)),
      "prepareFontGateData", len(_re83.findall(r"pkg\.prepareFontGateData\(False\)", _code88b)), "addGlyph", len(_re83.findall(r"pkg\.addGlyph\(", _code88b)), "flGlyph()", len(_re83.findall(r"mod\.flGlyph\(\)", _code88b)),
      "| scanned chars > 6000:", len(_src88b) > 6000)
print("983 no other tool changed        :", "debug_try_modern" not in src[src.index("def create_glyph("):src.index("def _confirm_deletion(")], "| create_glyph still calls font.update():", "font.update()" in src[src.index("def create_glyph("):src.index("def _confirm_deletion(")])
c, d = call("/version"); print("984 version                      :", d)
for _m, _a, _v in _tf_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
# ================= v0.89: automatic sync right after a modern write (fontlab.Update(<modern glyph>), faked; guard classification afterwards) =================
A89 = {"all_calls": []}
S89 = {"m": [0.0, -400.0]}
class S89Mod(M88Mod):                                     # stateful margins for set_glyph_sidebearings (ink width 400, as the polygon)
    def getLSB(s, tr): return S89["m"][0]
    def getRSB(s, tr): return S89["m"][1]
    def setSB(s, l, r, mg, al, tr): P72["calls"].append("setSB"); S89["m"] = [float(l), float(r)]; return True
    @property
    def advanceWidth(s): return S89["m"][0] + 400.0 + S89["m"][1]
def _u89(*a):                                             # like _m88_update, but a 'sync' copies the MODERN advance to the legacy glyph (what a real sync does)
    M88["calls"].append(("Update",) + tuple(type(x).__name__ for x in a))
    if M88["cfg"].get("call_raises"): raise RuntimeError("Update refused")
    for x in a:
        n, e = getattr(x, "name", None), M88["cfg"].get("effect")
        if e == "sync" and n in TS and n in P72["layers"]: g87_sync(n, P72["layers"][n].nodesCount(), width=float(x.advanceWidth))
        elif e == "wipe": P72["layers"].pop(n, None)
def m89_setup(cfg=None, refs=(("ref", "test_font"),), empties=("fresh",), update=True, mod=None, path=False):
    g87_setup(refs=refs, empties=empties); M88["calls"].clear(); M88["forbidden"].clear(); M88["cfg"] = dict(cfg or {}); M88["extra"] = 0
    ns["_AUTO_SYNC"] = True
    S89["m"] = [0.0, -400.0]
    if path:
        _fm.flContour = P81Contour
        P72Mod.findLayerCreate = lambda s, name, cs=None: (P81["real_create"](s, name, cs), P72["layers"].__setitem__(s.name, P81Layer(name)))[1] and P72["layers"][s.name]
    for _m in _tf_mods:
        _m.flGlyph = mod or M88Mod; _m.UpdateAll = _m88_updateall
        if update: _m.Update = _u89
        elif hasattr(_m, "Update"): delattr(_m, "Update")
    _fm.CurrentFont = lambda: G87Font()
    ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
def s89(tag, c, d, keys=("drawn", "set")):
    A89["all_calls"] += list(M88["calls"])
    fs = d.get("fontlab_sync")
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| synced_with_fontlab", d.get("synced_with_fontlab"), "| fontlab_sync", fs,
          "| note", (d.get("durability_note") or "")[:22], "| calls", [x for x in M88["calls"]], "| tracked", sorted(ns["_UNSYNCED"]["glyphs"]))
m89_setup(cfg=dict(effect="sync")); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("990 polygon, Update syncs          ", c, d)
print("990b                              :", "unsynced note gone:", "FontLab has not synced" not in d.get("durability_note", ""), "| layer kept:", "fresh" in P72["layers"], "| legacy layers:", len(TS["fresh"]._layers))
m89_setup(); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("991 polygon, Update has no effect    ", c, d)
print("991b unsynced note kept          :", "FontLab has not synced" in d.get("durability_note", ""))
m89_setup(cfg=dict(call_raises=1)); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("992 Update raises                   ", c, d)
m89_setup(cfg=dict(effect="wipe")); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("993 Update wipes the modern layer     ", c, d)
m89_setup(update=False); c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("994 no Update function in fontlab   ", c, d)
m89_setup(cfg=dict(effect="sync")); ns["_AUTO_SYNC"] = False; c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("995 _AUTO_SYNC False: v0.88 behaviour ", c, d)
print("995b no fontlab_sync key         :", "fontlab_sync" not in d); ns["_AUTO_SYNC"] = True
m89_setup(cfg=dict(effect="sync"), path=True); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]}); s89("996 draw_path, Update syncs          ", c, d)
m89_setup(cfg=dict(effect="sync"), mod=S89Mod); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); M88["calls"].clear()
c, d = p72_post("/glyph/sidebearings", {"name": "fresh", "left": 10, "right": 20}); s89("997 sidebearings on a synced glyph   ", c, d, keys=("set", "changed"))
m89_setup(cfg=dict(effect="sync"), mod=S89Mod); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); M88["cfg"] = {}; M88["calls"].clear()
c, d = p72_post("/glyph/sidebearings", {"name": "fresh", "left": 10, "right": 20}); s89("997b second edit, Update no effect  ", c, d, keys=("set", "changed"))
m89_setup(cfg=dict(effect="sync"), refs=(("r1", "Alpha"), ("r2", "Beta")), empties=("fresh", "other")); c, d = p72_post("/glyph/width", {"name": "r1", "width": 640}); s89("998 modern width route, Update syncs ", c, d, keys=("set", "route"))
m89_setup(cfg=dict(effect="sync"), refs=(("r1", "Alpha"), ("r2", "Beta")), empties=("fresh", "other")); c, d = p72_post("/glyph/width", {"name": "other", "width": 640}); s89("998b legacy width route: no sync     ", c, d, keys=("set", "route"))
m89_setup(cfg=dict(effect="sync")); _real_find = ns["_find_glyph"]; ns["_find_glyph"] = lambda f, n: None
print("999 glyph not found              :", ns["_auto_sync"](G87Font(), "fresh"), "| calls", M88["calls"]); ns["_find_glyph"] = _real_find
_real_mw = ns["_modern_wrapper"]
def _boom89(g, f): raise RuntimeError("wrapper boom")
ns["_modern_wrapper"] = _boom89; print("1000 wrapper fails               :", ns["_auto_sync"](G87Font(), "fresh"), "| calls", M88["calls"]); ns["_modern_wrapper"] = _real_mw
m89_setup(cfg=dict(effect="sync")); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); G87["calls"].clear()
c, d = sbpost("/glyph/create", {"name": "n1"}); g87_show("1001 after the auto sync: create runs  ", c, d, K87)
print("1001b layer survived font.update :", "fresh" in P72["layers"])
m89_setup(); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); G87["calls"].clear()
c, d = sbpost("/glyph/create", {"name": "n1"}); g87_show("1002 sync failed: guard still skips  ", c, d, K87)
m89_setup(cfg=dict(effect="sync")); _real_as = ns["_auto_sync"]
def _boom_as(font, name): raise RuntimeError("auto sync boom")
ns["_auto_sync"] = _boom_as; c, d = p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4}); s89("1003 _auto_sync raises: reply intact  ", c, d); ns["_auto_sync"] = _real_as
m89_setup(cfg=dict(effect="sync"), empties=("fresh", "other")); p72_post("/glyph/polygon", {"name": "fresh", "points": TRI4})
M88["cfg"] = {}; c, d = p72_post("/glyph/polygon", {"name": "other", "points": TRI4}); s89("1004 second glyph: only it is at risk ", c, d)
print("1005 calls over all cases        : UpdateAll called:", "UpdateAll" in A89["all_calls"], "| forbidden:", M88["forbidden"], "| Update calls:", sum(1 for x in A89["all_calls"] if isinstance(x, tuple) and x[0] == "Update"),
      "| all Update args are the modern wrapper:", all(x[1:] in (("M88Mod",), ("S89Mod",)) for x in A89["all_calls"] if isinstance(x, tuple) and x[0] == "Update"))
_src89 = src[src.index("def _auto_sync("):src.index("def _guard_classify(")]
_code89 = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _src89)
print("1006 static scan of the sync     : forbidden call syntax found:", _re83.findall(r"\.(?:assign\w*|replaceGlyph|deleteGlyph|removeGlyph|fillFgData|prepareFontGateData|UpdateAll|save\w*|close|export\w*|release|remove\w*|blockUpdate|unblockUpdate)\(", _code89),
      "| upd(w) calls:", _code89.count("upd(w)"), "| scanned chars > 900:", len(_src89) > 900)
print("1007 constants                   : shipped default", _re83.findall(r"(?m)^_AUTO_SYNC = (\w+)", src), "| synced note mentions legacy view:", "legacy view" in ns["_SYNCED_NOTE"])
c, d = call("/version"); print("1008 version                     :", d)


# ================= v0.90: /debug/fontdir (names-only probe of the FONT object; faked font with spies) =================
print("\n==== v0.90 /debug/fontdir ====")
FD = {"touched": [], "called": [], "count": 1, "cur_calls": 0}
class FDNoLen:
    pass
class FDSub:
    __doc__ = "Glyph groups list"
    def __len__(self): return 5
class FDKern:
    """sub-object: records every non-dunder member access (there must be none)."""
    __doc__ = "Kerning representation " + "x" * 600
    def __getattribute__(self, n):
        if not n.startswith("__"): FD["touched"].append(n)
        return object.__getattribute__(self, n)
    def __len__(self): return 3
    def get(self):
        FD["called"].append("kern.get"); return 1
    def hasGroupKerning(self): FD["called"].append("kern.hasGroupKerning"); return True
    groups = "g"
    sub = FDSub()
    nolenobj = FDNoLen()
    flagm = True
    @property
    def bad(self): raise RuntimeError("member boom")
    _hid = "secret"
FDKern.get.__doc__ = "Return the value of a pair. " + "d" * 600
class FDLenBoom:
    def __len__(self): raise RuntimeError("len boom")
class FDFont:
    familyName = "Arial"; unitsPerEm = 2048; flag = True; nothing = None
    kerning = FDKern(); nolen = FDNoLen(); lenboom = FDLenBoom(); _private = "secret"
    def method(self): FD["called"].append("font.method"); return "called!"
    @property
    def boom(self): raise RuntimeError("getattr boom")
def fd_setup(count=1, cur="font"):
    FD["touched"].clear(); FD["called"].clear(); FD["cur_calls"] = 0
    def _cur():
        FD["cur_calls"] += 1
        return None if cur is None else FDFont()
    fl.CurrentFont = _cur
    if count == "missing":
        if hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
    elif isinstance(count, Exception):
        def _c(): raise count
        fl.CountFonts = _c
    else:
        fl.CountFonts = lambda: count
def fds(tag, path):
    c, d = call(path)
    print(tag, ":", c, {k: v for k, v in d.items() if k not in ("doc", "public_names")}, "| names", d.get("public_names") if "public_names" in d else None,
          "| doc len", len(d["doc"]) if isinstance(d.get("doc"), str) else d.get("doc"), "| touched", list(FD["touched"]), "| called", list(FD["called"]))
    return c, d
_fd_cf = getattr(fl, "CountFonts", None); _fd_cur = fl.CurrentFont
fd_setup(); c, d = fds("1010 dir                    ", "/debug/fontdir?stage=dir")
print("1010b no underscore name, no value:", not any(n.startswith("_") for n in d["public_names"]), "| private hidden:", "_private" not in d["public_names"], "| no 'value' key:", "value" not in d)
fd_setup(); fds("1011 default stage is dir     ", "/debug/fontdir")
fd_setup(); fds("1012 sub text                 ", "/debug/fontdir?stage=sub&attr=familyName")
fd_setup(); fds("1013 sub int                  ", "/debug/fontdir?stage=sub&attr=unitsPerEm")
fd_setup(); fds("1014 sub bool                 ", "/debug/fontdir?stage=sub&attr=flag")
fd_setup(); fds("1015 sub None                 ", "/debug/fontdir?stage=sub&attr=nothing")
fd_setup(); fds("1016 sub callable NOT called  ", "/debug/fontdir?stage=sub&attr=method")
fd_setup(); c, d = fds("1017 sub object: names, len, doc", "/debug/fontdir?stage=sub&attr=kerning")
print("1017b doc cut at 400 chars        :", len(d.get("doc") or ""), "| no member of the sub-object touched or called:", FD["touched"] == [] and FD["called"] == [])
fd_setup(); fds("1018 object without len       ", "/debug/fontdir?stage=sub&attr=nolen")
fd_setup(); fds("1019 len() raises             ", "/debug/fontdir?stage=sub&attr=lenboom")
fd_setup(); fds("1020 getattr raises           ", "/debug/fontdir?stage=sub&attr=boom")
fd_setup(); fds("1021 attr not in dir(font)    ", "/debug/fontdir?stage=sub&attr=zzz")
fd_setup(); fds("1022 underscore attr refused  ", "/debug/fontdir?stage=sub&attr=_private")
for bad in ("a.b", "kerning()", "1abc", "a%20b", "__class__", ""):
    fd_setup(); fds(f"1023 bad identifier {bad!r:14}", "/debug/fontdir?stage=sub&attr=" + bad)
fd_setup(); fds("1023b sub without attr        ", "/debug/fontdir?stage=sub")
fd_setup(); fds("1023c attr with spaces is trimmed", "/debug/fontdir?stage=sub&attr=%20familyName%20")
fd_setup(); fds("1024 bad stage                ", "/debug/fontdir?stage=call&attr=method")
fd_setup(count=0); c, d = fds("1025 CountFonts 0: not open  ", "/debug/fontdir?stage=dir")
print("1025b CurrentFont never asked      :", FD["cur_calls"] == 0)
fd_setup(cur=None); fds("1026 CurrentFont None        ", "/debug/fontdir?stage=dir")
fd_setup(count=RuntimeError("count boom")); fds("1027 CountFonts raises        ", "/debug/fontdir?stage=sub&attr=familyName")
fd_setup(count=True); fds("1028 CountFonts returns True ", "/debug/fontdir?stage=sub&attr=familyName")
fd_setup(count="1"); fds("1028b CountFonts returns '1'   ", "/debug/fontdir?stage=sub&attr=familyName")
fd_setup(count="missing"); fds("1029 module has no CountFonts", "/debug/fontdir?stage=sub&attr=familyName")
fd_setup(count=2); fds("1030 two fonts: count reported ", "/debug/fontdir?stage=dir")
_fd_real = ns["debug_font_dir"]
def _fd_boom(stage, attr, members=None, go=None): raise RuntimeError("probe boom")
ns["debug_font_dir"] = _fd_boom; fd_setup(); fds("1031 probe raises: HTTP 500     ", "/debug/fontdir?stage=dir"); ns["debug_font_dir"] = _fd_real
_fd_src = src[src.index("def debug_font_dir("):src.index("# /debug/tryfont (v0.83)")]
_fd_code = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _fd_src)
_fd_code = "\n".join(l.split("#")[0] for l in _fd_code.splitlines())
print("1032 static scan                 : forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|append|get|keys|values|items|assign\w*|replace\w*|delete\w*)\(", _fd_code),
      "| val() calls:", len(_re83.findall(r"\bval\(", _fd_code)), "| font.X( calls:", _re83.findall(r"\bfont\.\w+\(", _fd_code),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _fd_code) if s not in ("result", "d", "out", "entry")], "| len() calls:", _fd_code.count("len("), "| getattr(font,:", _fd_code.count("getattr(font,"), "| scanned chars > 1500:", len(_fd_src) > 1500)
print("1033 read-only but for the gated keys stage:", "go=yes" not in _fd_src[:_fd_src.index("def _fontdir_keys(")] and _fd_src.count('go != "yes"') == 1 and "/debug/fontdir" in src and src.count('path == "/debug/fontdir"') == 1)
# ---- v0.91: stage=member ----
def fdm(tag, path):
    c, d = call(path)
    print(tag, ":", c, {k: v for k, v in d.items() if k not in ("members",)}, "| touched", list(FD["touched"]), "| called", list(FD["called"]))
    for k, v in (d.get("members") or {}).items():
        print("      ", k, {kk: (vv if kk != "doc" else (len(vv) if isinstance(vv, str) else vv)) for kk, vv in v.items()})
    return c, d
fd_setup(); fdm("1034 members of kerning       ", "/debug/fontdir?stage=member&attr=kerning&members=get,hasGroupKerning,groups,sub,nolenobj,flagm")
fd_setup(); fdm("1035 a method is never called  ", "/debug/fontdir?stage=member&attr=kerning&members=get,hasGroupKerning")
fd_setup(); fdm("1036 spaces around names trimmed", "/debug/fontdir?stage=member&attr=kerning&members=%20get%20,%20groups")
fd_setup(); fdm("1037 unknown / private / bad name", "/debug/fontdir?stage=member&attr=kerning&members=zzz,_hid,a.b,get(),1x")
fd_setup(); fdm("1038 member getattr raises     ", "/debug/fontdir?stage=member&attr=kerning&members=bad,groups")
fd_setup(); fdm("1039 eight names allowed       ", "/debug/fontdir?stage=member&attr=kerning&members=get,hasGroupKerning,groups,sub,nolenobj,flagm,bad,zzz")
fd_setup(); fdm("1040 nine names refused        ", "/debug/fontdir?stage=member&attr=kerning&members=get,hasGroupKerning,groups,sub,nolenobj,flagm,bad,zzz,get")
fd_setup(); fdm("1041 members missing           ", "/debug/fontdir?stage=member&attr=kerning")
fd_setup(); fdm("1042 members empty             ", "/debug/fontdir?stage=member&attr=kerning&members=,%20,")
fd_setup(); fdm("1043 attr is a plain value     ", "/debug/fontdir?stage=member&attr=familyName&members=get")
fd_setup(); fdm("1044 attr is a callable        ", "/debug/fontdir?stage=member&attr=method&members=get")
fd_setup(); fdm("1045 attr is None              ", "/debug/fontdir?stage=member&attr=nothing&members=get")
fd_setup(); fdm("1046 attr missing in dir(font) ", "/debug/fontdir?stage=member&attr=zzz&members=get")
fd_setup(); fdm("1047 attr private              ", "/debug/fontdir?stage=member&attr=_private&members=get")
fd_setup(); fdm("1048 attr getattr raises       ", "/debug/fontdir?stage=member&attr=boom&members=get")
fd_setup(count=0); fdm("1049 no font open: member   ", "/debug/fontdir?stage=member&attr=kerning&members=get")
fd_setup(); c, d = fdm("1050 doc of a method cut at 400", "/debug/fontdir?stage=member&attr=kerning&members=get")
print("1050b doc length                   :", len(d["members"]["get"]["doc"]))
fd_setup(); fds("1051 sub stage unchanged       ", "/debug/fontdir?stage=sub&attr=kerning")
_fd_src2 = src[src.index("def debug_font_dir("):src.index("# /debug/tryfont (v0.83)")]
_fd_code2 = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _fd_src2).splitlines())
print("1053 static scan (member stage)  : mv() calls:", len(_re83.findall(r"\bmv\(", _fd_code2)), "| val() calls:", len(_re83.findall(r"\bval\(", _fd_code2)),
      "| getattr(val,:", _fd_code2.count("getattr(val,"), "| len() calls:", _fd_code2.count("len("), "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _fd_code2) if s not in ("result", "d", "out", "entry")],
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|append|get|keys|values|items|assign\w*|replace\w*|delete\w*)\(", _fd_code2))
fl.CurrentFont = _fd_cur
if _fd_cf is not None: fl.CountFonts = _fd_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")

# ================= v0.92: /debug/trykern (gated ONE-call probe: font.kerning.get((a, b)); faked kerning object with spies) =================
print("\n==== v0.92 /debug/trykern ====")
FK = {"pairs": [], "touched": [], "forbidden": [], "len": 1370, "len_after": None, "values": {("A", "V"): -152.0, ("V", "A"): -150.0, ("T", "o"): -111, ("A", "B"): 0.0},
      "get_mode": None, "len_raises": False, "all_touched": set(), "cur_calls": 0}
_FK_FORBIDDEN = ("set", "remove", "clear", "addGroup", "deleteGroup", "deleteAllGroups", "renameGroup", "scale", "setPlainPairs", "asDict", "getPlainPairs",
                 "getPlainPairsDict", "items", "keys", "values", "has_key", "hasGroupKerning", "groups")
class FKKern:
    def __getattribute__(self, n):
        if not n.startswith("__"):
            FK["touched"].append(n); FK["all_touched"].add(n)
            if n in _FK_FORBIDDEN:
                FK["forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self):
        if FK["len_raises"]: raise RuntimeError("len boom")
        return FK["len_after"] if (FK["len_after"] is not None and FK["pairs"]) else FK["len"]
    def get(self, pair):
        FK["pairs"].append((type(pair).__name__, pair, [type(x).__name__ for x in pair]))
        m = FK["get_mode"]
        if m == "raise": raise RuntimeError("get boom")
        if m == "str": return "text"
        if m == "bool": return True
        if m == "none": return None
        return FK["values"].get(tuple(pair), 0.0)
class FKGlyph:
    def __init__(self, n): self.name = n
class FKFont:
    glyphs = [FKGlyph(n) for n in ("A", "V", "T", "o", "B", "uni00E9", ".notdef")]
    kerning = FKKern()
def fk_setup(count=1, cur="font", kmode=None, calls=0):
    FK["pairs"].clear(); FK["touched"].clear(); FK["forbidden"].clear(); FK["len_after"] = None; FK["get_mode"] = kmode; FK["len_raises"] = False; FK["cur_calls"] = 0
    ns["_TRYKERN"]["calls"] = calls
    def _cur():
        FK["cur_calls"] += 1
        return None if cur is None else FKFont()
    fl.CurrentFont = _cur
    fl.CountFonts = (lambda: count) if not isinstance(count, Exception) else (lambda: (_ for _ in ()).throw(count))
def fkc(tag, path):
    c, d = call(path)
    print(tag, ":", c, {k: v for k, v in d.items() if k not in ("note",)}, "| get calls", [(p[0], p[1], p[2]) for p in FK["pairs"]], "| touched", list(FK["touched"]), "| forbidden", list(FK["forbidden"]))
    return c, d
_fk_cf = getattr(fl, "CountFonts", None); _fk_cur = fl.CurrentFont
fk_setup(); fkc("1060 no go: nothing runs        ", "/debug/trykern?a=A&b=V")
fk_setup(); fkc("1061 go=maybe: nothing runs     ", "/debug/trykern?a=A&b=V&go=maybe")
fk_setup(); c, d = fkc("1062 A + V                    ", "/debug/trykern?a=A&b=V&go=yes")
print("1062b note present, says group kerning unknown:", "NOT known yet" in d.get("note", ""))
fk_setup(); fkc("1063 V + A                    ", "/debug/trykern?a=V&b=A&go=yes")
fk_setup(); fkc("1064 T + o (int value)        ", "/debug/trykern?a=T&b=o&go=yes")
fk_setup(); fkc("1065 A + B (no kerning)       ", "/debug/trykern?a=A&b=B&go=yes")
fk_setup(); fkc("1066 same glyph twice         ", "/debug/trykern?a=A&b=A&go=yes")
fk_setup(); fkc("1067 name with dot / digits   ", "/debug/trykern?a=.notdef&b=uni00E9&go=yes")
fk_setup(kmode="str"); fkc("1068 get returns text         ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(kmode="bool"); fkc("1069 get returns True         ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(kmode="none"); fkc("1070 get returns None         ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(kmode="raise"); fkc("1071 get raises (counted)     ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(); FK["len_after"] = 1369; fkc("1072 length changes: side effect", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(); FK["len_raises"] = True; fkc("1073 len() raises              ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(); fkc("1074 unknown a                ", "/debug/trykern?a=Q&b=V&go=yes")
fk_setup(); fkc("1075 unknown b                ", "/debug/trykern?a=A&b=Q&go=yes")
fk_setup(); fkc("1076 both unknown             ", "/debug/trykern?a=Q&b=Z&go=yes")
fk_setup(); fkc("1077 group-like name refused  ", "/debug/trykern?a=_kern_A&b=V&go=yes")
for bad in ("", "A%20V", "A/V", "A*", "%C3%A9", "x" * 64, "A(", "A%00"):
    fk_setup(); fkc(f"1078 bad name {bad[:12]!r:14}", "/debug/trykern?a=" + bad + "&b=V&go=yes")
fk_setup(); fkc("1078b missing b               ", "/debug/trykern?a=A&go=yes")
fk_setup(count=0); fkc("1079 CountFonts 0: not open  ", "/debug/trykern?a=A&b=V&go=yes")
print("1079b CurrentFont never asked      :", FK["cur_calls"] == 0)
fk_setup(cur=None); fkc("1080 CurrentFont None        ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(count=RuntimeError("count boom")); fkc("1081 CountFonts raises        ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(count=True); fkc("1082 CountFonts True         ", "/debug/trykern?a=A&b=V&go=yes")
fk_setup(calls=19); fkc("1083 call number 20 allowed   ", "/debug/trykern?a=A&b=V&go=yes")
fkc("1084 call number 21 refused   ", "/debug/trykern?a=A&b=V&go=yes")
class FKNoKern:
    glyphs = FKFont.glyphs
    @property
    def kerning(self): raise RuntimeError("no kerning")
class FKBadGet:
    glyphs = FKFont.glyphs
    class _K:
        get = 5
    kerning = _K()
class FKNoGet:
    glyphs = FKFont.glyphs
    kerning = object()
for tag, fnt in (("1085 font.kerning raises", FKNoKern), ("1086 kerning.get not callable", FKBadGet), ("1087 kerning has no get", FKNoGet)):
    fk_setup(); fl.CurrentFont = (lambda f=fnt: f()); fkc(tag.ljust(32), "/debug/trykern?a=A&b=V&go=yes"); print("      calls so far:", ns["_TRYKERN"]["calls"])
fk_setup(); _fk_real = ns["debug_try_kern"]
def _fk_boom(a, b, go): raise RuntimeError("probe boom")
ns["debug_try_kern"] = _fk_boom; fkc("1088 probe raises: HTTP 500    ", "/debug/trykern?a=A&b=V&go=yes"); ns["debug_try_kern"] = _fk_real
print("1089 spy over all cases          : forbidden members touched:", FK["forbidden"], "| every member touched anywhere:", sorted(FK["all_touched"]))
_fk_src = src[src.index("def debug_try_kern("):src.index("_TRYGROUPS_TOKEN_CHARS = ")]
_fk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _fk_src).splitlines())
_fk_doc_stripped = _re83.sub(r'(?s)"""(.*?)"""', '', _fk_code, count=1)
print("1090 static scan                 : kerning members used:", sorted(set(_re83.findall(r"kerning\.(\w+)", _fk_doc_stripped))), "| getter( calls:", len(_re83.findall(r"\bgetter\(", _fk_doc_stripped)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|append|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|scale|rename\w*)\(", _fk_doc_stripped),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _fk_doc_stripped) if s != "_TRYKERN"], "| counter raised before the call:", _fk_doc_stripped.index('_TRYKERN[""] += 1') < _fk_doc_stripped.index("getter((a, b))"),
      "| scanned chars > 1500:", len(_fk_src) > 1500)
print("1091 gate and cap constants      :", "go != \"yes\"" in _fk_src, "| max calls", ns["_TRYKERN_MAX"], "| route registered once:", src.count('path == "/debug/trykern"') == 1)
fl.CurrentFont = _fk_cur
if _fk_cf is not None: fl.CountFonts = _fk_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
ns["_TRYKERN"]["calls"] = 0

# ================= v0.93: /debug/trygroups (gated ONE-call probe: font.groups.getCompiled(); faked groups object with spies) =================
print("\n==== v0.93 /debug/trygroups ====")
FG = {"touched": [], "forbidden": [], "calls": 0, "text": "", "mode": None, "len": 132, "len_after": None, "len_raises": False, "all_touched": set(), "cur_calls": 0}
_FG_FORBIDDEN = ("get", "keys", "values", "items", "asDict", "remove", "rename", "clear", "fromDict", "fromClassRecords", "getAsClassRecords", "has_key")
FG_TEXT = ("@Aring = [A Aacute Adieresis Aring];\n@W_c2sc2 = [W.c2sc W.c2sc2];\r\n@_35722 = [x y z];\n"
           + "@long = [" + "Q " * 200 + "Aacute];\n" + "".join(f"@g{i} = [Aacute g{i}];\n" for i in range(25)) + "@V = [V Vacute];\n" + "tail " * 200)
class FGGroups:
    def __getattribute__(self, n):
        if not n.startswith("__"):
            FG["touched"].append(n); FG["all_touched"].add(n)
            if n in _FG_FORBIDDEN:
                FG["forbidden"].append(n)
                raise SystemExit("FORBIDDEN groups member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self):
        if FG["len_raises"]: raise RuntimeError("len boom")
        return FG["len_after"] if (FG["len_after"] is not None and FG["calls"]) else FG["len"]
    def getCompiled(self):
        FG["calls"] += 1
        m = FG["mode"]
        if m == "raise": raise RuntimeError("compiled boom")
        if m == "none": return None
        if m == "int": return 5
        return FG["text"]
class FGFont:
    groups = FGGroups()
def fg_setup(count=1, cur="font", mode=None, calls=0, text=FG_TEXT):
    FG["touched"].clear(); FG["forbidden"].clear(); FG["calls"] = 0; FG["mode"] = mode; FG["len_after"] = None; FG["len_raises"] = False; FG["cur_calls"] = 0; FG["text"] = text
    ns["_TRYGROUPS"]["calls"] = calls
    def _cur():
        FG["cur_calls"] += 1
        return None if cur is None else FGFont()
    fl.CurrentFont = _cur
    fl.CountFonts = (lambda: count) if not isinstance(count, Exception) else (lambda: (_ for _ in ()).throw(count))
def fgc(tag, path, full=False):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k not in ("note", "matches", "head")}
    print(tag, ":", c, shown, "| head len", len(d["head"]) if "head" in d else None, "| touched", list(FG["touched"]), "| forbidden", list(FG["forbidden"]), "| real calls", FG["calls"])
    for tok, segs in (d.get("matches") or {}).items():
        print("      ", repr(tok), len(segs), "segments; lengths", [len(s) for s in segs][:6], "| first:", (segs[0][:60] if segs else None), "| cut flagged:", sum(1 for s in segs if s.endswith("...[cut]")))
    return c, d
_fg_cf = getattr(fl, "CountFonts", None); _fg_cur = fl.CurrentFont
fg_setup(); fgc("1100 no go: nothing runs        ", "/debug/trygroups")
fg_setup(); fgc("1101 go=maybe: nothing runs     ", "/debug/trygroups?go=maybe")
fg_setup(); c, d = fgc("1102 go=yes, no token: head    ", "/debug/trygroups?go=yes")
print("1102b head is the first 500 chars   :", d.get("head") == FG_TEXT[:500], "| chars", d.get("chars") == len(FG_TEXT), "| lines", d.get("lines") == len(FG_TEXT.splitlines()), "| no matches key:", "matches" not in d, "| note present:", "note" in d)
fg_setup(); fgc("1103 empty contains = head mode ", "/debug/trygroups?go=yes&contains=")
fg_setup(); fgc("1104 contains Aring             ", "/debug/trygroups?go=yes&contains=Aring")
fg_setup(); c, d = fgc("1105 contains Aacute (many hits) ", "/debug/trygroups?go=yes&contains=Aacute")
print("1105b count vs returned             :", d["match_counts"], "| returned", {k: len(v) for k, v in d["matches"].items()}, "| head absent:", "head" not in d)
fg_setup(); fgc("1106 two names                  ", "/debug/trygroups?go=yes&contains=V,%20W.c2sc2")
fg_setup(); fgc("1107 whole word only (A vs Aacute)", "/debug/trygroups?go=yes&contains=A")
fg_setup(); fgc("1108 name with dot / underscore / @ ", "/debug/trygroups?go=yes&contains=_35722,@V,W.c2sc")
fg_setup(); fgc("1109 name not present           ", "/debug/trygroups?go=yes&contains=Zzz")
fg_setup(); fgc("1110 four names refused         ", "/debug/trygroups?go=yes&contains=A,B,C,D")
for bad in ("a%20b", "x/y", "A(", "A%3Bb", "%C3%A9", "x" * 64, "A%00"):
    fg_setup(); fgc(f"1111 bad name {bad[:12]!r:14}", "/debug/trygroups?go=yes&contains=" + bad)
fg_setup(mode="none"); fgc("1112 getCompiled returns None   ", "/debug/trygroups?go=yes&contains=A")
fg_setup(mode="int"); fgc("1113 getCompiled returns int    ", "/debug/trygroups?go=yes")
fg_setup(mode="raise"); fgc("1114 getCompiled raises (counted)", "/debug/trygroups?go=yes")
fg_setup(); FG["len_after"] = 131; fgc("1115 length changes: side effect", "/debug/trygroups?go=yes")
fg_setup(); FG["len_raises"] = True; fgc("1116 len() raises              ", "/debug/trygroups?go=yes")
fg_setup(text=""); fgc("1117 empty text                ", "/debug/trygroups?go=yes&contains=A")
fg_setup(count=0); fgc("1118 CountFonts 0: not open   ", "/debug/trygroups?go=yes")
print("1118b CurrentFont never asked      :", FG["cur_calls"] == 0)
fg_setup(cur=None); fgc("1119 CurrentFont None        ", "/debug/trygroups?go=yes")
fg_setup(count=RuntimeError("count boom")); fgc("1120 CountFonts raises        ", "/debug/trygroups?go=yes")
fg_setup(count=True); fgc("1121 CountFonts True         ", "/debug/trygroups?go=yes")
fg_setup(calls=9); fgc("1122 call number 10 allowed   ", "/debug/trygroups?go=yes")
fgc("1123 call number 11 refused   ", "/debug/trygroups?go=yes")
class FGNoGroups:
    @property
    def groups(self): raise RuntimeError("no groups")
class FGBad:
    class _G:
        getCompiled = 5
    groups = _G()
class FGNoGet:
    groups = object()
for tag, fnt in (("1124 font.groups raises", FGNoGroups), ("1125 getCompiled not callable", FGBad), ("1126 groups has no getCompiled", FGNoGet)):
    fg_setup(); fl.CurrentFont = (lambda f=fnt: f()); fgc(tag.ljust(32), "/debug/trygroups?go=yes"); print("      calls so far:", ns["_TRYGROUPS"]["calls"])
fg_setup(); _fg_real = ns["debug_try_groups"]
def _fg_boom(go, contains): raise RuntimeError("probe boom")
ns["debug_try_groups"] = _fg_boom; fgc("1127 probe raises: HTTP 500    ", "/debug/trygroups?go=yes"); ns["debug_try_groups"] = _fg_real
print("1128 spy over all cases          : forbidden members touched:", FG["forbidden"], "| every member touched anywhere:", sorted(FG["all_touched"]))
_fg_src = src[src.index("def debug_try_groups("):src.index("def debug_layer_item(")]
_fg_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _fg_src).splitlines())
_fg_body = _re83.sub(r'(?s)"""(.*?)"""', '', _fg_code, count=1)
print("1129 static scan                 : groups members used:", sorted(set(_re83.findall(r"groups\.(\w+)", _fg_body))), "| getter( calls:", len(_re83.findall(r"\bgetter\(", _fg_body)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|append|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getAs\w*|from\w*|rename\w*)\(", _fg_body),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _fg_body) if s not in ("_TRYGROUPS", "value", "found", "counts", "out", "hits", "h")],
      "| counter raised before the call:", _fg_body.index('_TRYGROUPS[""] += 1') < _fg_body.index("getter()"), "| scanned chars > 2000:", len(_fg_src) > 2000)
print("1130 gate, cap, route            :", "go != \"yes\"" in _fg_src, "| max calls", ns["_TRYGROUPS_MAX"], "| route registered once:", src.count('path == "/debug/trygroups"') == 1)
fl.CurrentFont = _fg_cur
if _fg_cf is not None: fl.CountFonts = _fg_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
ns["_TRYGROUPS"]["calls"] = 0


# ================= v0.94 / v0.104: GET /kerning/pairs (read-only; the master's table through flPackage, explicit keys; spies) =================
print("\n==== v0.94 /kerning/pairs (v0.104: the master's table, explicit keys) ====")
KP = {"touched": [], "forbidden": [], "gets": [], "mode": {}, "len": 1370, "len_after": None, "len_raises": False, "all_touched": set(), "cur_calls": 0, "glyph_boom": False,
      "groups_calls": 0, "kerning_args": [], "cfg": {}, "ever": [], "pkg_path_reads": 0}
_KP_FORBIDDEN = ("set", "remove", "clear", "addGroup", "deleteGroup", "deleteAllGroups", "renameGroup", "scale", "setPlainPairs", "asDict", "getPlainPairs",
                 "getPlainPairsDict", "items", "keys", "values", "has_key", "hasGroupKerning", "groups")
_KP_LEFT = {"Aring": (101, ("Aacute", "Atilde", "Aring"))}               # left classes: name -> (id, members); the glyph's kerningLeft holds the id
_KP_RIGHT = {"W": (201, ("W.c2sc", "Wgrave.c2sc")), "Y": (202, ("Ydieresis.c2sc",))}
_KP_TABLE = {(("A", False), ("V", False)): -152.0, (("V", False), ("A", False)): -152.0, (("T", False), ("o", False)): -227.0,
             (("A", False), ("W", True)): -76.0, (("Aring", True), ("W", True)): -76.0, (("Aring", True), ("Y", True)): -152.0,
             (("A", False), ("Tbar.c2sc", False)): -80.0, (("Aring", True), ("Tbar.c2sc", False)): -80.0, (("o", False), ("o", False)): 0.0,
             (("A", False), ("space", False)): -113.0, (("space", False), ("V", False)): -37.0}
def _kp_groups_default():
    return [(True, name, gid, 0, list(members)) for name, (gid, members) in list(_KP_LEFT.items()) + list(_KP_RIGHT.items())] + [(False, "fea", 300, 0, ["A"])]
class KPKern:
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KP["touched"].append(n); KP["all_touched"].add(n)
            if n in _KP_FORBIDDEN:
                KP["forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "get" and KP["cfg"].get("get_attr") == "not_callable": return 5
        return object.__getattribute__(self, n)
    def __len__(self):
        if KP["len_raises"]: raise RuntimeError("len boom")
        return KP["len_after"] if (KP["len_after"] is not None and KP["gets"]) else KP["len"]
    def get(self, pair):
        KP["gets"].append(pair)
        flagged = isinstance(pair, tuple) and len(pair) == 2 and all(isinstance(p, tuple) and len(p) == 2 and isinstance(p[1], bool) for p in pair)
        if not flagged:
            KP["forbidden"].append("plain key " + repr(pair)); KP["ever"].append("plain key " + repr(pair)); return -999.0
        (a, fa), (b, fb) = pair
        m = KP["mode"].get(pair)
        if m is None and not (fa or fb): m = KP["mode"].get((a, b))
        if m == "raise": raise RuntimeError("get boom")
        if m == "str": return "text"
        if m == "bool": return True
        if m == "nan": return float("nan")
        if m == "inf": return float("inf")
        if m == "-inf": return float("-inf")
        if m == "zero": return 0.0
        if isinstance(m, float): return m
        return _KP_TABLE.get(pair)
class KPGlyph:
    def __init__(self, n, u=None, boom=False): self.name = n; self._u = u; self._boom = boom
    @property
    def unicode(self):
        if self._boom: raise RuntimeError("unicode boom")
        return self._u
    def _ids(self):
        over = KP["cfg"].get("ids", {}).get(self.name)
        if over is not None: return over
        left = next((gid for gid, members in _KP_LEFT.values() if self.name in members), 0)
        right = next((gid for gid, members in _KP_RIGHT.values() if self.name in members), 0)
        return (left, right)
    @property
    def kerningLeft(self):
        v = self._ids()[0]
        if isinstance(v, Exception): raise v
        return v
    @property
    def kerningRight(self):
        v = self._ids()[1]
        if isinstance(v, Exception): raise v
        return v
_KP_GLYPHS = [KPGlyph(n, u) for n, u in (("A", 65), ("V", 86), ("T", 84), ("o", 111), ("B", 66), ("space", 32), ("Aacute", 193), ("eacute", 233), ("Atilde", 195), ("Aring", 197),
              ("W.c2sc", None), ("Wgrave.c2sc", None), ("Ydieresis.c2sc", None), ("Tbar.c2sc", None), ("x", 120), ("x.alt2", 120), ("y", 121), ("y.1", 121), ("y.2", 121), ("y.3", 121), ("y.4", 121), ("y.5", 121), ("y.6", 121), ("zero", 0), (".notdef", None))]
class KPInfo:
    unitsPerEm = 2048.0
    familyName = "Kern Test"
class KPFont:
    info = KPInfo()
    @property
    def path(self):
        v = KP["cfg"].get("font_path", "C:/fonts/kern.vfc")
        if isinstance(v, Exception): raise v
        return v
    @property
    def kerning(self):
        KP["forbidden"].append("font.kerning (the legacy table)"); KP["ever"].append("font.kerning")
        raise SystemExit("FORBIDDEN: the legacy font.kerning was read")
    @property
    def glyphs(self):
        if KP["glyph_boom"]: raise RuntimeError("glyph list boom")
        return list(_KP_GLYPHS)
_KP_PKG_OK = ("isNull", "masters", "master", "kerning", "getAllGroups", "path", "upm")
class KPPackage:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            KP["all_touched"].add("package." + n)
            if n not in _KP_PKG_OK:
                KP["forbidden"].append("package." + n); raise SystemExit("FORBIDDEN package member touched: " + n)
        return object.__getattribute__(self, n)
    def isNull(self): return KP["cfg"].get("is_null", False)
    @property
    def path(self):
        KP["pkg_path_reads"] += 1
        v = KP["cfg"].get("pkg_path", "C:/fonts/kern.vfc")
        if isinstance(v, Exception): raise v
        return v
    @property
    def masters(self):
        v = KP["cfg"].get("masters", ["Regular"])
        if isinstance(v, Exception): raise v
        return v
    @property
    def master(self):
        v = KP["cfg"].get("master", "Regular")
        if isinstance(v, Exception): raise v
        return v
    @property
    def kerning(self):
        v = KP["cfg"].get("kerning_attr")
        if isinstance(v, Exception): raise v
        if v == "not_callable": return 5
        def _kerning(*args):
            KP["kerning_args"].append(args)
            m = KP["cfg"].get("kerning_call")
            if isinstance(m, Exception): raise m
            if m == "no_get": return object()
            return KP["cfg"].get("kern_factory", KPKern)()      # v0.124: KSKern for the /kerning/set cases
        return _kerning
    @property
    def upm(self):
        v = KP["cfg"].get("upm", 2048.0)
        if isinstance(v, Exception): raise v
        return v
    @property
    def getAllGroups(self):
        v = KP["cfg"].get("getall_attr")
        if v == "not_callable": return 7
        def _all():
            KP["groups_calls"] += 1
            g = KP["cfg"].get("groups", "default")
            if isinstance(g, Exception): raise g
            return _kp_groups_default() if g == "default" else g
        return _all
KP_PKG = KPPackage()
class KPWorkspace:
    @staticmethod
    def instance(): return KP_WS
    def packages(self): return [KP_PKG] * KP["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return KP_PKG
KP_WS = KPWorkspace()
def kp_setup(count=1, cur="font", mode=None, **cfg):
    KP["touched"].clear(); KP["forbidden"].clear(); KP["gets"].clear(); KP["mode"] = mode or {}; KP["len_after"] = None; KP["len_raises"] = False; KP["cur_calls"] = 0; KP["glyph_boom"] = False
    KP["groups_calls"] = 0; KP["kerning_args"].clear(); KP["cfg"] = dict(cfg); KP["pkg_path_reads"] = 0
    def _cur():
        KP["cur_calls"] += 1
        return None if cur is None else (cfg["font"]() if "font" in cfg else KPFont())
    fl.CurrentFont = _cur
    fl.CountFonts = (lambda: count) if not isinstance(count, Exception) else (lambda: (_ for _ in ()).throw(count))
    fl.flWorkspace = KPWorkspace
def kpc(tag, path, brief=False):
    c, d = call(path)
    head = {k: v for k, v in d.items() if k != "results"}
    print(tag, ":", c, head, "| gets", len(KP["gets"]), "| forbidden", list(KP["forbidden"]))
    rs = d.get("results") or []
    if len(rs) <= 8:
        for r in rs:
            print("      ", r)
    else:
        print("       (%d results; distinct:" % len(rs), sorted(set(str(r) for r in rs))[:4], ")")
    return c, d
_kp_cf = getattr(fl, "CountFonts", None); _kp_cur = fl.CurrentFont; _kp_ws = getattr(fl, "flWorkspace", None)
kp_setup(); kpc("1140 no parameter                ", "/kerning/pairs")
kp_setup(); kpc("1141 both parameters             ", "/kerning/pairs?pairs=A:V&text=AV")
kp_setup(); kpc("1142 pairs: direct pairs         ", "/kerning/pairs?pairs=A:V,V:A,T:o,A:B")
kp_setup(); kpc("1143 pairs: class kerning        ", "/kerning/pairs?pairs=A:Wgrave.c2sc,Aacute:Wgrave.c2sc,Atilde:Ydieresis.c2sc,A:Tbar.c2sc,Aacute:Tbar.c2sc")
kp_setup(); c, d = kpc("1144 pairs: get gets a tuple of str", "/kerning/pairs?pairs=A:V")
print("1144b keys passed to get           :", KP["gets"], "| touched only get:", sorted(set(KP["touched"])))
kp_setup(); kpc("1145 pairs: duplicates, spaces    ", "/kerning/pairs?pairs=A:V,%20A%20:%20V%20,A:V")
kp_setup(); kpc("1146 pairs: unknown glyph names   ", "/kerning/pairs?pairs=A:V,Q:V,A:Qq,Q:Qq")
kp_setup(mode={("A", "V"): "raise", ("V", "A"): "str", ("T", "o"): "bool", ("A", "B"): "nan", ("o", "o"): "inf"}); kpc("1147 get raises / odd values per pair", "/kerning/pairs?pairs=A:V,V:A,T:o,A:B,o:o,A:space")
kp_setup(mode={("o", "o"): "zero"}); kpc("1148 get returns 0.0 (not kerned)  ", "/kerning/pairs?pairs=o:o,A:V")
kp_setup(); kpc("1149 forty pairs allowed         ", "/kerning/pairs?pairs=" + ",".join(["A:V"] * 40))
kp_setup(); kpc("1150 300 pairs: no cap           ", "/kerning/pairs?pairs=" + ",".join(["A:V"] * 300))
for bad in ("A", "A:V:B", ":V", "A:", "A;V", "A%20V", "A:V,", ",A:V", "A/B:V", "A:" + "x" * 64, "%C3%A9:V", "A:V:", "::"):
    kp_setup(); kpc(f"1151 bad pairs {bad[:14]!r:17}", "/kerning/pairs?pairs=" + bad)
kp_setup(); kpc("1152 text: AV                    ", "/kerning/pairs?text=AV")
kp_setup(); kpc("1153 text: AVA o                 ", "/kerning/pairs?text=AVA%20T")
kp_setup(); kpc("1154 text: with space            ", "/kerning/pairs?text=A%20V")
kp_setup(); kpc("1155 text: unmapped letter       ", "/kerning/pairs?text=AZV")
kp_setup(); kpc("1156 text: ambiguous codepoint   ", "/kerning/pairs?text=Ax")
kp_setup(); kpc("1157 text: non-ASCII (UTF-8)     ", "/kerning/pairs?text=%C3%A9A")
kp_setup(); kpc("1157b text: 7 glyphs share a code", "/kerning/pairs?text=yA")
kp_setup(mode={("A", "V"): "-inf"}); kpc("1147b get returns -inf          ", "/kerning/pairs?pairs=A:V")
kp_setup(); kpc("1158 text: plus sign is a space  ", "/kerning/pairs?text=A+V")
kp_setup(); kpc("1159 text: one character         ", "/kerning/pairs?text=A")
kp_setup(); kpc("1160 text: 41 characters allowed ", "/kerning/pairs?text=" + "AV" * 20 + "A")
kp_setup(); kpc("1161 text: 300 characters: no cap", "/kerning/pairs?text=" + "AV" * 150)
kp_setup(); kpc("1162 text: control character     ", "/kerning/pairs?text=A%0AV")
kp_setup(); kpc("1162b text: DEL character        ", "/kerning/pairs?text=A%7FV")
kp_setup(); kpc("1162c text: C1 control U+0080    ", "/kerning/pairs?text=A%C2%80V")
kp_setup(); kpc("1162d text: U+00A0 is not control", "/kerning/pairs?text=A%C2%A0V")
kp_setup(); kpc("1163 text: tab and DEL           ", "/kerning/pairs?text=A%09V%7F")
_KP_GLYPHS.append(KPGlyph("broken", None, boom=True))
kp_setup(); kpc("1164 text: unreadable glyph exists, unmapped char ", "/kerning/pairs?text=AZ")
kp_setup(); kpc("1165 text: unreadable glyph, mapped chars still work", "/kerning/pairs?text=AV")
_KP_GLYPHS.pop()
kp_setup(); KP["len_after"] = 1369; kpc("1166 table size changes: side effect", "/kerning/pairs?pairs=A:V")
kp_setup(); KP["len_raises"] = True; kpc("1167 len() raises                 ", "/kerning/pairs?pairs=A:V")
kp_setup(); KP["glyph_boom"] = True; kpc("1168 glyph list unreadable         ", "/kerning/pairs?pairs=A:V")
class KPNoInfo(KPFont):
    @property
    def info(self): raise RuntimeError("no info")
class KPBoolInfo(KPFont):
    class _I:
        unitsPerEm = True
    info = _I()
class KPStrInfo(KPFont):
    class _I:
        unitsPerEm = "2048"
    info = _I()
kp_setup(kerning_attr=RuntimeError("no kerning")); kpc("1169 package kerning raises      ", "/kerning/pairs?pairs=A:V")
kp_setup(get_attr="not_callable"); kpc("1170 table get not callable      ", "/kerning/pairs?pairs=A:V")
kp_setup(kerning_call="no_get"); kpc("1171 table has no get            ", "/kerning/pairs?pairs=A:V")
for tag, fnt in (("1172 font.info unreadable", KPNoInfo), ("1172b unitsPerEm is True", KPBoolInfo), ("1172c unitsPerEm is a string", KPStrInfo)):
    kp_setup(font=fnt); kpc(tag.ljust(32), "/kerning/pairs?pairs=A:V")
kp_setup(count=0); kpc("1173 CountFonts 0: not open     ", "/kerning/pairs?pairs=A:V")
print("1173b CurrentFont never asked      :", KP["cur_calls"] == 0)
kp_setup(cur=None); kpc("1174 CurrentFont None          ", "/kerning/pairs?pairs=A:V")
kp_setup(count=RuntimeError("count boom")); kpc("1175 CountFonts raises          ", "/kerning/pairs?pairs=A:V")
kp_setup(count=True); kpc("1176 CountFonts True           ", "/kerning/pairs?pairs=A:V")
kp_setup(count=False); kpc("1176b CountFonts False         ", "/kerning/pairs?pairs=A:V")
kp_setup(); _kp_real = ns["get_kerning_pairs"]
def _kp_boom(pairs, text): raise RuntimeError("probe boom")
ns["get_kerning_pairs"] = _kp_boom; kpc("1177 function raises: HTTP 500   ", "/kerning/pairs?pairs=A:V"); ns["get_kerning_pairs"] = _kp_real
kp_setup(); [call("/kerning/pairs?pairs=A:V") for _ in range(60)]; c, d = call("/kerning/pairs?pairs=A:V"); print("1178 no per-run cap: 61st request  :", c, d.get("results"))
print("1179 spy over all cases          : forbidden members touched:", KP["forbidden"], "| every member touched anywhere:", sorted(KP["all_touched"]))
_kp_src = src[src.index("def _kern_class_id("):src.index("# /kerning/groups (v0.190, P1.6)")]     # v0.190: the groups read has its own scan (2631)
_kp_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _kp_src).splitlines())
_kp_body = _re83.sub(r'(?s)"""(.*?)"""', '', _kp_code)
print("1180 static scan                 : kerning members used:", sorted(set(_re83.findall(r"kerning\.(\w+)", _kp_body))), "| getter( calls:", len(_re83.findall(r"\bgetter\(", _kp_body)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|scale|rename\w*)\(", _kp_body.replace("entry.update(", "").replace("by_name.setdefault(", "").replace("twice.add(", "")),
      "| subscripts:", sorted(set(_re83.findall(r"\b(\w+)\[", _kp_body))), "| font members used:", sorted(set(_re83.findall(r"\bfont\.(\w+)", _kp_body))),
      "| pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _kp_body))), "| no gate needed (no go= in source):", "go" not in _re83.findall(r"\bgo\b", _kp_body), "| scanned chars > 3000:", len(_kp_src) > 3000)
print("1181 constants and routes        : cap constant gone:", "_KERN_MAX_PAIRS" not in ns, "| GET and POST routes registered:", src.count('if path == "/kerning/pairs":') == 2 and src.count('"/kerning/pairs"') >= 2)
def kpp(tag, payload, raw=False):
    body = payload if raw else json.dumps(payload).encode("utf-8")
    r = ns["_route"]("POST", "/kerning/pairs", body); h, _, b = r.partition(b"\r\n\r\n")
    c, d = h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
    head = {k: v for k, v in d.items() if k != "results"}
    print(tag, ":", c, head, "| gets", len(KP["gets"]), "| forbidden", list(KP["forbidden"]))
    rs = d.get("results") or []
    if len(rs) <= 8:
        for r_ in rs: print("      ", r_)
    else: print("       (%d results; distinct:" % len(rs), sorted(set(str(x) for x in rs))[:4], ")")
    return c, d
kp_setup(); kpp("1182 POST pairs: class kerning   ", {"pairs": [["A", "V"], ["Aacute", "Wgrave.c2sc"], ["A", "Tbar.c2sc"], ["T", "o"], ["A", "B"]]})
kp_setup(); kpp("1183 POST text                   ", {"text": "AVA T"})
kp_setup(); kpp("1184 POST names are stripped      ", {"pairs": [[" A ", " V "]]})
kp_setup(); kpp("1185 POST 5000 pairs: no cap      ", {"pairs": [["A", "V"]] * 5000}); print("1185b gets made                    :", len(KP["gets"]))
kp_setup(); kpp("1186 POST 3000 characters of text ", {"text": "AV" * 1500}); print("1186b gets made                    :", len(KP["gets"]))
kp_setup(); c1, d1 = call("/kerning/pairs?pairs=A:V,T:o,A:Wgrave.c2sc"); kp_setup(); c2, d2 = kpp("1187 POST equals GET            ", {"pairs": [["A", "V"], ["T", "o"], ["A", "Wgrave.c2sc"]]}); print("1187b same reply                   :", d1 == d2)
kp_setup(); kpp("1188 POST neither                ", {})
kp_setup(); kpp("1189 POST both                   ", {"pairs": [["A", "V"]], "text": "AV"})
kp_setup(); kpp("1190 POST empty pairs list       ", {"pairs": []})
kp_setup(); kpp("1191 POST empty text             ", {"text": ""})
kp_setup(); kpp("1192 POST text one character     ", {"text": "A"})
kp_setup(); kpp("1193 POST text control character ", {"text": "A\nV"})
for tag, pl in (("1194 pairs is a string", {"pairs": "A:V"}), ("1195 text is a number", {"text": 5}), ("1196 extra key", {"pairs": [["A", "V"]], "go": "yes"}), ("1197 body is a list", [["A", "V"]]),
                ("1198 pairs is null, text null", {"pairs": None, "text": None}), ("1199 item is a string", {"pairs": ["AV"]}), ("1200 item has 3 names", {"pairs": [["A", "V", "T"]]}),
                ("1201 item has 1 name", {"pairs": [["A"]]}), ("1202 name is a number", {"pairs": [["A", 5]]}), ("1203 name is null", {"pairs": [["A", None]]}), ("1204 name empty", {"pairs": [["A", ""]]}),
                ("1205 name blank", {"pairs": [["A", "  "]]}), ("1206 name with colon", {"pairs": [["A:V", "B"]]}), ("1207 name with comma", {"pairs": [["A,V", "B"]]}),
                ("1208 name 64 long", {"pairs": [["A", "x" * 64]]}), ("1209 name non-ASCII", {"pairs": [["A", "é"]]}), ("1210 item is a dict", {"pairs": [{"left": "A", "right": "V"}]}),
                ("1211 item is nested list", {"pairs": [[["A"], "V"]]}), ("1212 good pair then bad pair", {"pairs": [["A", "V"], ["A"]]})):
    kp_setup(); kpp(tag.ljust(32), pl)
kp_setup(); kpp("1213 POST body not JSON          ", b"not json", raw=True)
kp_setup(); kpp("1214 POST body not UTF-8         ", b"\xff\xfe", raw=True)
kp_setup(); kpp("1215 POST empty body             ", b"", raw=True)
kp_setup(); kpp("1216 POST unknown glyph          ", {"pairs": [["A", "V"], ["Q", "V"]]})
kp_setup(count=0); kpp("1217 POST no font open          ", {"pairs": [["A", "V"]]})
kp_setup(); KP["len_after"] = 1369; kpp("1218 POST side effect flagged   ", {"pairs": [["A", "V"]]})
kp_setup(); ns["get_kerning_pairs"] = _kp_boom; kpp("1219 POST function raises: 500  ", {"pairs": [["A", "V"]]}); ns["get_kerning_pairs"] = _kp_real
kp_setup()
for _tag, _a, _b in (("1221 direct: pairs is a number", 5, None), ("1222 direct: pairs is a dict", {"A": "V"}, None), ("1223 direct: text is a number", None, 5), ("1224 direct: text is a list", None, ["AV"]), ("1225 direct: text is a tuple of 2", None, ("A", "V"))):
    print(_tag.ljust(34), ":", ns["get_kerning_pairs"](_a, _b), "| gets", len(KP["gets"]))
print("1220 POST route registered once   :", src.count('if path == "/kerning/pairs":') == 2, "| spy: forbidden members touched:", KP["forbidden"], "| members touched anywhere:", sorted(KP["all_touched"]))

# ---- v0.104: classes from the glyphs' group ids, FontLab's order of entries, the master, and the one-font rule (cases 1430-1462).
print("\n==== v0.104 /kerning/pairs: classes, order of entries, master, one font ====")
_KPQ = "/kerning/pairs?pairs="
_KP_ALL4 = {(("Aacute", False), ("Wgrave.c2sc", False)): -10.0, (("Aacute", False), ("W", True)): -20.0, (("Aring", True), ("Wgrave.c2sc", False)): -30.0}
kp_setup(mode=dict(_KP_ALL4)); kpc("1430 four entries: glyph : glyph", _KPQ + "Aacute:Wgrave.c2sc")
print("1430b keys asked, in order         :", KP["gets"])
kp_setup(mode={k: v for k, v in _KP_ALL4.items() if k[0][1] or k[1][1]}); kpc("1431 then glyph : class wins    ", _KPQ + "Aacute:Wgrave.c2sc")
kp_setup(mode={(("Aring", True), ("Wgrave.c2sc", False)): -30.0}); kpc("1432 then class : glyph wins    ", _KPQ + "Aacute:Wgrave.c2sc")
kp_setup(); kpc("1433 class : class only          ", _KPQ + "Aacute:Wgrave.c2sc")
print("1433b keys asked, in order         :", KP["gets"])
kp_setup(mode={(("Aring", False), ("W", True)): -30.0}); kpc("1434 defect B: glyph Aring is also a class name", _KPQ + "Aring:Wgrave.c2sc,Aring:W.c2sc")
kp_setup(mode={(("Aacute", False), ("W", True)): "zero"}); kpc("1435 explicit 0 exception wins over -76", _KPQ + "Aacute:Wgrave.c2sc")
kp_setup(ids={"x": (400, 400)}, groups=_kp_groups_default() + [(True, "xboth", 400, 0, ["x"])], mode={(("xboth", True), ("xboth", True)): -40.0})
kpc("1436 a Both class on both sides  ", _KPQ + "x:x,A:x,x:A")
kp_setup(ids={"A": (999, 0)}); kpc("1437 id missing from the list   ", _KPQ + "A:V,T:o")
kp_setup(groups=_kp_groups_default() + [(True, "W2", 201, 0, ["W.c2sc"])]); kpc("1438 id listed twice            ", _KPQ + "A:Wgrave.c2sc,T:o")
for _tag, _v in (("1439 kerningLeft is True     ", True), ("1439b kerningLeft is a string ", "101"), ("1439c kerningLeft is 101.0    ", 101.0), ("1439d kerningLeft is None     ", None)):
    kp_setup(ids={"Aacute": (_v, 0)}); kpc(_tag, _KPQ + "Aacute:V")
kp_setup(ids={"Aacute": (RuntimeError("left boom"), 0), "V": (0, RuntimeError("right boom"))}); kpc("1440 kerningLeft and kerningRight raise", _KPQ + "Aacute:V,T:o")
kp_setup(groups=RuntimeError("groups boom")); kpc("1441 getAllGroups raises        ", _KPQ + "Aacute:V,T:o,A:Wgrave.c2sc")
print("1441b getAllGroups calls           :", KP["groups_calls"])
kp_setup(groups="not a list"); kpc("1442 getAllGroups not a list    ", _KPQ + "Aacute:V")
kp_setup(getall_attr="not_callable"); kpc("1443 getAllGroups not callable  ", _KPQ + "Aacute:V")
kp_setup(); call(_KPQ + ",".join(["Aacute:Wgrave.c2sc", "Atilde:Ydieresis.c2sc", "A:Wgrave.c2sc"] * 20)); print("1444 60 class pairs: getAllGroups calls:", KP["groups_calls"])
kp_setup(); call(_KPQ + "A:V,T:o,V:A"); print("1444b no class ids: getAllGroups calls :", KP["groups_calls"])
kp_setup(groups=[(False, "Aring", 101, 0, ["Aacute"])] + _kp_groups_default()[1:]); kpc("1445 the id only in a non-kerning group", _KPQ + "Aacute:V")
kp_setup(groups=[(True, "Aring", 101, 0), "Aring", (True, 101, 101, 0, []), (True, "Aring", "101", 0, []), (1, "Aring", 101, 0, [])] + _kp_groups_default()[1:])
kpc("1446 malformed entries skipped   ", _KPQ + "Aacute:V,A:Wgrave.c2sc")
kp_setup(count=2); kpc("1447 two fonts open             ", _KPQ + "A:V")
kp_setup(count=3); kpp("1447b POST, three fonts open     ", {"pairs": [["A", "V"]]})
kp_setup(packages=2); kpc("1448 two packages               ", _KPQ + "A:V")
kp_setup(groups=None); kpc("1448b getAllGroups None (v0.217)", _KPQ + "Aacute:V,A:V")
# v0.112: with several fonts open the current package is matched to the current font by path (T5)
print("1447c one font: package path reads :", (kp_setup(), call(_KPQ + "A:V"))[1][1].get("matched_by"), KP["pkg_path_reads"])
kp_setup(count=2); call(_KPQ + "A:V"); print("1447d two fonts: package path reads:", KP["pkg_path_reads"])
kp_setup(count=2, pkg_path="C:/fonts/other.vfc"); kpc("1447e two fonts, paths differ     ", _KPQ + "A:V")
kp_setup(count=2, font_path=""); kpc("1447f current font has no path    ", _KPQ + "A:V")
print("1447g   package path read          :", KP["pkg_path_reads"])
kp_setup(count=2, font_path=None); kpc("1447h font path is None           ", _KPQ + "A:V")
kp_setup(count=2, font_path=RuntimeError("path boom")); kpc("1447i font path raises            ", _KPQ + "A:V")
kp_setup(count=2, pkg_path=""); kpc("1447j package path empty          ", _KPQ + "A:V")
kp_setup(count=2, pkg_path=7); kpc("1447k package path not a string   ", _KPQ + "A:V")
kp_setup(count=2, pkg_path=RuntimeError("pkg path boom")); kpc("1447l package path raises         ", _KPQ + "A:V")
kp_setup(count=2, is_null=True); kpc("1447m package is null             ", _KPQ + "A:V")
kp_setup(count=2, is_null=None); kpc("1447n package null state unknown  ", _KPQ + "A:V")
kp_setup(count=-1); kpc("1447o CountFonts gives -1         ", _KPQ + "A:V")
kp_setup(count=2, packages=5); kpc("1447p two fonts, packages() not used", _KPQ + "A:V")
kp_setup(masters=["Regular", "Bold"], master="Bold"); kpc("1449 two masters, current Bold  ", _KPQ + "A:V")
print("1449b kerning() asked for          :", KP["kerning_args"])
kp_setup(master="Ghost"); kpc("1450 current master unlisted    ", _KPQ + "A:V")
kp_setup(masters="Regular"); kpc("1450b masters not a list        ", _KPQ + "A:V")
kp_setup(masters=RuntimeError("masters boom")); kpc("1450c masters raises           ", _KPQ + "A:V")
kp_setup(master=RuntimeError("master boom")); kpc("1450d master raises            ", _KPQ + "A:V")
kp_setup(kerning_attr="not_callable"); kpc("1451 package kerning not callable", _KPQ + "A:V")
kp_setup(kerning_call=RuntimeError("kerning() boom")); kpc("1451b kerning(master) raises    ", _KPQ + "A:V")
kp_setup(mode={(("Aacute", False), ("W", True)): "raise"}); kpc("1453 get raises on a class key   ", _KPQ + "Aacute:Wgrave.c2sc,A:V")
kp_setup(mode={(("Aring", True), ("W", True)): "str"}); kpc("1454 odd answer on a class key   ", _KPQ + "Aacute:Wgrave.c2sc")
kp_setup(mode={(("Aring", True), ("W", True)): "nan"}); kpc("1454b NaN on a class key        ", _KPQ + "Aacute:Wgrave.c2sc")
kp_setup(); kpc("1455 text: a class glyph         ", "/kerning/pairs?text=%C3%81V%C3%83A")
print("1455b keys asked, in order         :", KP["gets"])
kp_setup(); kpp("1456 POST: classes as in 1143    ", {"pairs": [["A", "Wgrave.c2sc"], ["Aacute", "Wgrave.c2sc"], ["Atilde", "Ydieresis.c2sc"], ["A", "Tbar.c2sc"], ["Aacute", "Tbar.c2sc"]]})
kp_setup(mode={(("Aacute", False), ("W", True)): -50.0, (("Aring", True), ("Wgrave.c2sc", False)): -101.0}); kpc("1457 the kc1 case: glyph : class over class : glyph", _KPQ + "Aacute:Wgrave.c2sc,Atilde:Wgrave.c2sc,Aacute:W.c2sc")
kp_setup(); kpc("1458 a class pair needs both ids  ", _KPQ + "Aacute:V,V:Wgrave.c2sc")
print("1459 no plain key, no legacy table : forbidden over 1140-1458:", KP["ever"])
fl.CurrentFont = _kp_cur
if _kp_cf is not None: fl.CountFonts = _kp_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
if _kp_ws is not None: fl.flWorkspace = _kp_ws
elif hasattr(fl, "flWorkspace"): delattr(fl, "flWorkspace")

# ================= v0.97: /debug/trypkgkern (gated research probe: flPackage.kerning(master).get((a, b)) next to font.kerning.get((a, b))) =================
print("\n==== v0.97 /debug/trypkgkern ====")
PK = {"cfg": {}, "kerning_args": [], "pkg_touched": [], "pkg_forbidden": [], "pkg_all": set(), "k_touched": [], "k_forbidden": [], "k_all": set(), "gets": []}
_PK_PKG_FORBIDDEN = ("autoKern", "deleteGroups", "getAllGroups", "findGroup", "update", "release", "remove", "clearMasters", "removeMaster", "renameMaster",
                     "setMaster", "addMaster", "deleteGlyph", "addGlyph", "kerningContainer", "resetPackage", "setUpm", "runActions")
class PKKern:
    def __init__(self, label, values, size): self._label, self._values, self._size, self._got = label, values, size, False
    def __getattribute__(self, n):
        if not n.startswith("_"):
            PK["k_touched"].append(object.__getattribute__(self, "_label") + "." + n); PK["k_all"].add(n)
            if n in _FK_FORBIDDEN:
                PK["k_forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "get" and PK["cfg"].get(object.__getattribute__(self, "_label") + "_get") == "not_callable": return 5
        return object.__getattribute__(self, n)
    def __len__(self):
        c = PK["cfg"]
        if c.get(self._label + "_len_raises"): raise RuntimeError("len boom")
        if self._got and c.get(self._label + "_len_after") is not None: return c[self._label + "_len_after"]
        return self._size
    def get(self, pair):
        PK["gets"].append((self._label, type(pair).__name__, tuple(pair)))
        self._got = True
        m = PK["cfg"].get(self._label + "_get")
        if m == "raise": raise RuntimeError(self._label + " get boom")
        if m == "bool": return True
        return self._values.get(tuple(pair))
class PKPackage:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            PK["pkg_touched"].append(n); PK["pkg_all"].add(n)
            if n in _PK_PKG_FORBIDDEN:
                PK["pkg_forbidden"].append(n)
                raise SystemExit("FORBIDDEN package member touched: " + n)
        return object.__getattribute__(self, n)
    def isNull(self):
        v = PK["cfg"].get("isNull", False)
        if isinstance(v, Exception): raise v
        return v
    @property
    def masters(self):
        v = PK["cfg"].get("masters", ["Regular"])
        if isinstance(v, Exception): raise v
        return (lambda: ["Regular", "Bold"]) if v == "method" else v
    @property
    def master(self):
        v = PK["cfg"].get("master", "Regular")
        if isinstance(v, Exception): raise v
        return v
    @property
    def kerning(self):
        v = PK["cfg"].get("kerning_attr")
        if isinstance(v, Exception): raise v
        if v == "not_callable": return 5
        def _kerning(*args):
            PK["kerning_args"].append(args)
            m = PK["cfg"].get("kerning_call")
            if m == "raise": raise RuntimeError("kerning() boom")
            if m == "none": return None
            return PKKern("package", {("kn1L", "kn1R"): -100.0, ("kn1L", "kn1S"): -100.0,
                                      (("kn1L", False), ("kn1R", False)): -50.0, (("kn1L", False), ("kn1R", True)): -100.0}, 1)
        return _kerning
class PKWorkspace:
    @staticmethod
    def instance(): return PK_WS
    def packages(self): return [PK_PKG] * PK["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return PK_PKG
PK_PKG = PKPackage(); PK_WS = PKWorkspace()
class PKGlyph:
    def __init__(self, n): self.name = n
class PKFont:
    glyphs = [PKGlyph(n) for n in ("kn1L", "kn1R", "kn1S", ".notdef")]
    @property
    def kerning(self):
        if PK["cfg"].get("legacy_raises"): raise RuntimeError("no legacy kerning")
        return PKKern("legacy", {}, 0)
_pk_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace")]
def pk_setup(calls=0, **cfg):
    PK["cfg"] = dict(cfg)
    for k in ("kerning_args", "pkg_touched", "pkg_forbidden", "k_touched", "k_forbidden", "gets"): PK[k].clear()
    ns["_TRYPKGKERN"]["calls"] = calls
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = PKWorkspace
        _m.CountFonts = (lambda: count) if not isinstance(count, Exception) else (lambda: (_ for _ in ()).throw(count))
        _m.CurrentFont = (lambda: None) if cfg.get("cur") == "none" else (lambda: PKFont())
def pkc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| kerning() args", PK["kerning_args"], "| gets", PK["gets"])
    return c, d
_PKQ = "/debug/trypkgkern?a=kn1L&b=kn1R"
pk_setup(); pkc("1230 no go: nothing runs        ", _PKQ)
pk_setup(); pkc("1231 go=maybe: nothing runs     ", _PKQ + "&go=maybe")
pk_setup(); c, d = pkc("1232 current master, kn1L:kn1R ", _PKQ + "&go=yes")
print("1232b note present                 :", "nothing is changed or saved" in d.get("note", ""))
pk_setup(); pkc("1233 class member kn1L:kn1S   ", "/debug/trypkgkern?a=kn1L&b=kn1S&go=yes", keys=("master_used", "package", "legacy"))
pk_setup(); pkc("1234 master given             ", _PKQ + "&master=Regular&go=yes", keys=("master_used", "master_source", "calls_so_far"))
pk_setup(); pkc("1235 master not in masters    ", _PKQ + "&master=Bold&go=yes")
pk_setup(); pkc("1236 master with control char ", _PKQ + "&master=Reg%01ular&go=yes")
pk_setup(); pkc("1236b master with U+0080      ", _PKQ + "&master=Reg%C2%80ular&go=yes")
pk_setup(); pkc("1237 master 64 characters     ", _PKQ + "&master=" + "M" * 64 + "&go=yes")
pk_setup(masters=["Regular", "M" * 63]); pkc("1238 master 63 characters     ", _PKQ + "&master=" + "M" * 63 + "&go=yes", keys=("master_used", "master_source"))
pk_setup(masters=["Light Italic"]); pkc("1239 master with a space     ", _PKQ + "&master=Light%20Italic&go=yes", keys=("masters", "master_used", "error"))
for bad in ("", "A%20V", "A:V", "%C3%A9", "x" * 64):
    pk_setup(); pkc(f"1240 bad name a {bad[:12]!r:14}", "/debug/trypkgkern?a=" + bad + "&b=kn1R&go=yes")
pk_setup(); pkc("1241 unknown glyph            ", "/debug/trypkgkern?a=kn1L&b=Q&go=yes")
pk_setup(cur="none"); pkc("1242 CurrentFont None         ", _PKQ + "&go=yes")
pk_setup(masters=("Regular",)); pkc("1243 masters is a tuple       ", _PKQ + "&go=yes", keys=("masters", "master_used"))
pk_setup(masters="method"); pkc("1244 masters is a method      ", _PKQ + "&master=Bold&go=yes", keys=("masters", "master_used"))
class PKNative: pass
pk_setup(masters=PKNative()); pkc("1245 masters not a plain list ", _PKQ + "&go=yes")
pk_setup(masters=["Regular", 5]); pkc("1246 masters not all names    ", _PKQ + "&go=yes")
pk_setup(masters=RuntimeError("masters boom")); pkc("1247 masters raises           ", _PKQ + "&go=yes")
pk_setup(master=RuntimeError("master boom")); pkc("1248 current master raises    ", _PKQ + "&go=yes")
pk_setup(master=RuntimeError("master boom")); pkc("1249 ... but master given     ", _PKQ + "&master=Regular&go=yes", keys=("current_master", "master_used", "master_source"))
pk_setup(master=PKNative()); pkc("1250 current master native    ", _PKQ + "&go=yes")
pk_setup(master="Ghost"); pkc("1251 current master unlisted  ", _PKQ + "&go=yes")
pk_setup(kerning_call="raise"); pkc("1252 kerning() raises (counted)", _PKQ + "&go=yes", keys=("package", "legacy", "calls_so_far"))
pk_setup(kerning_call="none"); pkc("1253 kerning() returns None  ", _PKQ + "&go=yes", keys=("package", "legacy", "calls_so_far"))
pk_setup(kerning_attr=RuntimeError("attr boom")); pkc("1254 kerning not reachable    ", _PKQ + "&go=yes")
pk_setup(kerning_attr="not_callable"); pkc("1255 kerning not callable     ", _PKQ + "&go=yes")
pk_setup(package_get="raise"); pkc("1256 package get raises       ", _PKQ + "&go=yes", keys=("package", "legacy"))
pk_setup(package_get="bool"); pkc("1257 package get returns True ", _PKQ + "&go=yes", keys=("package",))
pk_setup(package_len_after=2); pkc("1258 package len changes     ", _PKQ + "&go=yes", keys=("package",))
pk_setup(package_len_raises=True); pkc("1259 package len raises      ", _PKQ + "&go=yes", keys=("package",))
pk_setup(package_get="not_callable"); pkc("1259c package get not callable", _PKQ + "&go=yes", keys=("package", "legacy"))
pk_setup(legacy_raises=True); pkc("1260 font.kerning raises      ", _PKQ + "&go=yes", keys=("package", "legacy"))
pk_setup(legacy_get="raise"); pkc("1261 legacy get raises        ", _PKQ + "&go=yes", keys=("legacy",))
for tag, over in (("1262 no font open        ", dict(count=0)), ("1263 two fonts open      ", dict(count=2)), ("1264 CountFonts True     ", dict(count=True)),
                  ("1265 CountFonts raises   ", dict(count=RuntimeError("count boom"))), ("1266 two packages        ", dict(packages=2)),
                  ("1267 package is null     ", dict(isNull=True)), ("1268 isNull raises       ", dict(isNull=RuntimeError("null boom")))):
    pk_setup(**over); pkc(tag, _PKQ + "&go=yes")
pk_setup(calls=19); pkc("1269 request 20 allowed       ", _PKQ + "&go=yes", keys=("calls_so_far", "max_calls"))
PK["kerning_args"].clear(); PK["gets"].clear(); pkc("1270 request 21 refused       ", _PKQ + "&go=yes")
pk_setup(); _pk_real = ns["debug_try_pkg_kern"]
def _pk_boom(*a): raise RuntimeError("probe boom")
ns["debug_try_pkg_kern"] = _pk_boom; pkc("1271 probe raises: HTTP 500    ", _PKQ + "&go=yes"); ns["debug_try_pkg_kern"] = _pk_real
pk_setup()
for _tag, _master in (("1271b direct: master is a number", 5), ("1271c direct: master is a list", ["Regular"])):
    print(_tag.ljust(34), ":", ns["debug_try_pkg_kern"]("kn1L", "kn1R", _master, "yes"), "| kerning() args", PK["kerning_args"])
pk_setup()
for _p in (_PKQ, _PKQ + "&go=yes", _PKQ + "&master=Regular&go=yes", "/debug/trypkgkern?a=kn1L&b=kn1S&go=yes"): call(_p)
print("1272 spy over all cases          : forbidden package members:", PK["pkg_forbidden"], "| package members touched anywhere:", sorted(PK["pkg_all"]),
      "| forbidden kerning members:", PK["k_forbidden"], "| kerning members touched anywhere:", sorted(PK["k_all"]))
_pk_src = src[src.index("_TRYPKGKERN = {"):src.index("# /debug/trysetkern (v0.122)")]
_pk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _pk_src).splitlines())
print("1273 static scan                 : pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _pk_code))), "| kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _pk_code))),
      "| kerning_of( calls:", len(_re83.findall(r"\bkerning_of\(", _pk_code)), "| getter( calls:", len(_re83.findall(r"\bgetter\(", _pk_code)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|scale|rename\w*|autoKern|getAllGroups|findGroup)\(", _pk_code),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _pk_code) if s not in ("_TRYPKGKERN", "_TRYPKGKERN_FLAGS")],
      "| counter raised before the call:", _pk_code.index('_TRYPKGKERN[""] += 1') < _pk_code.index("kerning_of(master)"), "| scanned chars > 3000:", len(_pk_src) > 3000)
print("1274 gate, cap, route, docstring  :", "go != \"yes\"" in _pk_src, "| max requests", ns["_TRYPKGKERN_MAX"], "| route registered once:", src.count('path == "/debug/trypkgkern"') == 1,
      "| listed in the module docstring:", "/debug/trypkgkern" in src[:src.index('"""', 3)])
for _m, _a, _v in _pk_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYPKGKERN"]["calls"] = 0

# ================= v0.98: /debug/moddir (names only, in modules ALREADY loaded; never imports, constructs or calls) =================
print("\n==== v0.98 /debug/moddir ====")
MD = {"touched": []}
PK["k_all"].clear(); PK["pkg_all"].clear()
class MDKerningObjectPair:
    """fgKerningObjectPair(string left, string right [, int mode]) - FAKE docstring for the stub"""
    def __init__(self, *a, **k):
        MD["touched"].append("constructed fgKerningObjectPair"); raise SystemExit("FORBIDDEN: constructed")
    def isGroup(self):
        """bool isGroup(int side) - FAKE"""
        MD["touched"].append("called isGroup"); raise SystemExit("FORBIDDEN: called")
    left = "fake attribute"
def _md_boom(*a, **k):
    """boom() - FAKE module function that must never be called"""
    MD["touched"].append("called kernBoom"); raise SystemExit("FORBIDDEN: called")
_md_mod = types.ModuleType("fontgate")
_md_mod.fgKerningObjectPair = MDKerningObjectPair; _md_mod.fgKerning = type("fgKerning", (), {"__doc__": "fgKerning - FAKE"})
_md_mod.kernBoom = _md_boom; _md_mod.fgFont = object; _md_mod._hiddenKern = 1
_md_big = types.ModuleType("mdbig")
for _i in range(205): setattr(_md_big, "kern%03d" % _i, _i)
sys.modules["fontgate"] = _md_mod; sys.modules["mdbig"] = _md_big
for _i in range(105): sys.modules["zzmd%03d" % _i] = types.ModuleType("zzmd%03d" % _i)
_md_keys = set(sys.modules)
def mdc(tag, path, keys=None):
    c, d = call(path)
    shown = d if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| touched", MD["touched"])
    return c, d
mdc("1280 no parameters              ", "/debug/moddir")
mdc("1281 modules containing fontgate", "/debug/moddir?contains=fontgate")
mdc("1282 case-insensitive           ", "/debug/moddir?contains=FONTGATE,MDBIG")
mdc("1283 four tokens refused        ", "/debug/moddir?contains=a,b,c,d")
mdc("1284 token with a star refused  ", "/debug/moddir?contains=fo*t")
mdc("1285 105 modules: cut at 100    ", "/debug/moddir?contains=zzmd", keys=("count", "cut"))
print("1285b listed                       :", len(call("/debug/moddir?contains=zzmd")[1]["modules"]))
mdc("1286 module not loaded          ", "/debug/moddir?module=mdnotloaded&contains=kern")
print("1286b still not loaded             :", "mdnotloaded" not in sys.modules)
for bad in ("a..b", "1abc", "a-b", "a.", "m" * 65, "a%20b"):
    mdc(f"1287 bad module {bad[:10]!r:12}  ", "/debug/moddir?module=" + bad + "&contains=kern")
mdc("1288 module without a filter    ", "/debug/moddir?module=fontgate")
mdc("1289 names with kern or pair    ", "/debug/moddir?module=fontgate&contains=kern,pair")
mdc("1290 205 names: cut at 200      ", "/debug/moddir?module=mdbig&contains=kern", keys=("count", "cut"))
print("1290b listed                       :", len(call("/debug/moddir?module=mdbig&contains=kern")[1]["names"]))
mdc("1291 one entry                  ", "/debug/moddir?module=fontgate&name=fgKerningObjectPair&doc=80")
mdc("1292 entry with members         ", "/debug/moddir?module=fontgate&name=fgKerningObjectPair&doc=80&members=isGroup,left,nope,_x", keys=("member_docs",))
mdc("1293 a module function's doc    ", "/debug/moddir?module=fontgate&name=kernBoom&doc=80", keys=("type", "doc", "module"))
mdc("1294 entry not in the module    ", "/debug/moddir?module=fontgate&name=fgNope")
mdc("1295 name and contains together ", "/debug/moddir?module=fontgate&name=fgKerning&contains=kern")
mdc("1296 name without module        ", "/debug/moddir?name=fgKerning")
mdc("1297 members without name       ", "/debug/moddir?module=fontgate&contains=kern&members=get")
mdc("1298 members without module     ", "/debug/moddir?contains=kern&members=get")
mdc("1299 doc not a number           ", "/debug/moddir?module=fontgate&name=fgKerning&doc=x")
mdc("1300 unknown stage              ", "/debug/moddir?stage=bogus")
pk_setup(); mdc("1301 kerntype                   ", "/debug/moddir?stage=kerntype")
pk_setup(); mdc("1302 kerntype with module       ", "/debug/moddir?stage=kerntype&module=fontgate")
pk_setup(); mdc("1302b kerntype with contains    ", "/debug/moddir?stage=kerntype&contains=kern")
pk_setup(count=0); mdc("1303 kerntype, no font open     ", "/debug/moddir?stage=kerntype")
pk_setup(count=2); mdc("1304 kerntype, two fonts        ", "/debug/moddir?stage=kerntype")
pk_setup(cur="none"); mdc("1305 kerntype, CurrentFont None ", "/debug/moddir?stage=kerntype")
pk_setup(legacy_raises=True); mdc("1306 kerntype, kerning raises  ", "/debug/moddir?stage=kerntype")
_md_real = ns["debug_mod_dir"]
def _md_raise(*a): raise RuntimeError("probe boom")
ns["debug_mod_dir"] = _md_raise; mdc("1307 probe raises: HTTP 500     ", "/debug/moddir?contains=fontgate"); ns["debug_mod_dir"] = _md_real
print("1308 nothing called or constructed :", MD["touched"], "| sys.modules unchanged:", set(sys.modules) == _md_keys, "| kerning members touched:", sorted(PK["k_all"]), "| package members touched:", sorted(PK["pkg_all"]))
_md_src = src[src.index("_MODDIR_MAX_MODULES = "):src.index("# /debug/fontdir (v0.90)")]
_md_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _md_src).splitlines())
print("1309 static scan                 : import machinery:", _re83.findall(r"__import__|importlib|import_module|\bexec\(|\beval\(|\bcompile\(|__call__", _md_code),
      "| calls on a module object:", _re83.findall(r"\bmod\.\w+\s*\(", _md_code), "| getattr on the module:", _md_code.count("getattr(mod"),
      "| font members used:", sorted(set(_re83.findall(r"\bfont\.(\w+)", _md_code))), "| scanned chars > 2000:", len(_md_src) > 2000)
print("1310 route and docstring          :", src.count('path == "/debug/moddir"') == 1, "| listed in the module docstring:", "/debug/moddir" in src[:src.index('"""', 3)],
      "| classdir default label unchanged:", call("/debug/classdir?name=fgNope")[1])
for _k in ["fontgate", "mdbig"] + ["zzmd%03d" % _i for _i in range(105)]: sys.modules.pop(_k, None)

# ================= v0.100: /debug/trypkgkern &mode=flags (get(((a, flag), (b, flag))), the form fgKerning.get named in test 183) =================
print("\n==== v0.100 /debug/trypkgkern mode=flags ====")
def pfc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| gets", PK["gets"])
    return c, d
_PFQ = "/debug/trypkgkern?a=kn1L&b=kn1R&go=yes"
pk_setup(); pfc("1311 flags FF, kn1L:kn1R        ", _PFQ + "&mode=flags&flags=FF")
for fl_ in ("FT", "TF", "TT"):
    pk_setup(); pfc(f"1312 flags {fl_}, kn1L:kn1R        ", _PFQ + "&mode=flags&flags=" + fl_, keys=("mode", "flags", "package", "legacy"))
pk_setup(); pfc("1313 flags FF, kn1L:kn1S        ", "/debug/trypkgkern?a=kn1L&b=kn1S&go=yes&mode=flags&flags=FF", keys=("package",))
pk_setup(); pfc("1314 tuple mode named           ", _PFQ + "&mode=tuple", keys=("mode", "flags", "package"))
pk_setup(); pfc("1315 mode left out = tuple      ", _PFQ, keys=("mode", "flags", "package"))
for bad in ("bogus", "glyph", "FLAGS", "Tuple"):
    pk_setup(); pfc(f"1316 bad mode {bad!r:10}         ", _PFQ + "&mode=" + bad + "&flags=FF", keys=("error", "calls_so_far"))
for bad in ("ff", "F", "FFF", "FX", "01", "TrueFalse"):
    pk_setup(); pfc(f"1317 bad flags {bad!r:12}      ", _PFQ + "&mode=flags&flags=" + bad, keys=("error", "calls_so_far"))
pk_setup(); pfc("1318 mode=flags without flags   ", _PFQ + "&mode=flags", keys=("error", "calls_so_far"))
pk_setup(); pfc("1319 flags without mode=flags   ", _PFQ + "&flags=FF", keys=("error", "calls_so_far"))
pk_setup(); pfc("1320 flags without go           ", "/debug/trypkgkern?a=kn1L&b=kn1R&mode=flags&flags=FF")
pk_setup(count=0); pfc("1321 flags, no font open        ", _PFQ + "&mode=flags&flags=FF")
pk_setup(calls=20); pfc("1322 flags, cap used up         ", _PFQ + "&mode=flags&flags=FF")
pk_setup(); pfc("1323 flags, unknown glyph       ", "/debug/trypkgkern?a=kn1L&b=Q&go=yes&mode=flags&flags=FF")
pk_setup(package_get="raise"); pfc("1324 flags, package get raises  ", _PFQ + "&mode=flags&flags=FF", keys=("package", "legacy"))
pk_setup(kerning_call="raise"); pfc("1325 flags, kerning() raises    ", _PFQ + "&mode=flags&flags=FF", keys=("package", "legacy", "calls_so_far"))
pk_setup(); print("1326 direct call, flags given as a list:", ns["debug_try_pkg_kern"]("kn1L", "kn1R", None, "yes", "flags", ["F", "F"]), "| gets", PK["gets"])
_pf_src = src[src.index("_TRYPKGKERN = {"):src.index("# /debug/trysetkern (v0.122)")]
_pf_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _pf_src).splitlines())
print("1327 static scan                 : fontgate or import machinery:", _re83.findall(r"fontgate|__import__|importlib|import_module|fgKerningObjectPair", _pf_code),
      "| getter( calls:", len(_re83.findall(r"\bgetter\(", _pf_code)), "| flag table:", ns["_TRYPKGKERN_FLAGS"], "| modes:", ns["_TRYPKGKERN_MODES"])
for _m, _a, _v in _pk_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYPKGKERN"]["calls"] = 0


for _m in _tf_mods:
    for _a in ("Update", "UpdateAll", "UpdateGlyphRect", "UpdateActiveCanvas", "SetCurrentGlyph", "SetCurrentFont"):
        if hasattr(_m, _a): delattr(_m, _a)
    _m.flGlyph = P72Mod
del P72Layer.assignFgLayer; TS85_PKG = _TS85_PKG_ORIG; _fm.CurrentFont = lambda: TsFont(); ns["_confirm_deletion"] = _orig_confirm87; ns["_UNSYNCED_MAX"] = 500


# ---- v0.101: start(), the poll loop and /shutdown (cases 1328-1335). A /shutdown handled inside _poll's loop used to be
# followed by _sock.accept() on None (AttributeError in FontLab's OUTPUT panel, seen live 2026-11-01).
class PLConn:
    def __init__(self, raw): self.raw = raw; self.sent = b""; self.closed = False
    def settimeout(self, t): pass
    def recv(self, n):
        chunk, self.raw = self.raw[:n], self.raw[n:]
        return chunk
    def sendall(self, b): self.sent += b
    def close(self): self.closed = True
class PLSock:
    def __init__(self, conns): self.conns = list(conns); self.closed = False; self.accepts = 0
    def accept(self):
        self.accepts += 1
        if not self.conns: raise BlockingIOError()
        return self.conns.pop(0), ("127.0.0.1", 50000)
    def close(self): self.closed = True
class PLTimer:
    def __init__(self): self.stopped = False; self.started = False
    def setInterval(self, ms): self.ms = ms
    def connect(self, sig, fn): self.sig = sig
    def start(self): self.started = True
    def stop(self): self.stopped = True
def pl_get(path): return PLConn(("GET " + path + " HTTP/1.1\r\nHost: x\r\n\r\n").encode())
def pl_status(conn):
    return conn.sent.split(b"\r\n", 1)[0].decode()[9:12] + " " + conn.sent.partition(b"\r\n\r\n")[2].decode() if conn.sent else "(nothing sent)"
def pl_poll(tag, conns):
    sock, timer = PLSock(conns), PLTimer()
    ns["_sock"], ns["_timer"] = sock, timer
    try:
        ns["_poll"](); err = None
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
    print(tag, ": raised", err, "| accepts", sock.accepts, "| left", len(sock.conns), "| socket closed", sock.closed,
          "| timer stopped", timer.stopped, "| listener running", ns["_sock"] is not None)
    return sock
_pl_h, _pl_s, _pl_v = pl_get("/health"), pl_get("/shutdown"), pl_get("/version")
pl_poll("1328 poll: health, shutdown, version", [_pl_h, _pl_s, _pl_v])
print("1329 replies                       :", pl_status(_pl_h), "|", pl_status(_pl_s), "|", pl_status(_pl_v), "| closed", _pl_h.closed, _pl_s.closed)
_pl_v2 = pl_get("/version")
pl_poll("1330 poll: one request, then none", [_pl_v2])
print("1331 reply                         :", pl_status(_pl_v2))
ns["_sock"], ns["_timer"] = None, None
try:
    ns["_poll"](); print("1332 poll after stop()             : returns quietly")
except Exception as exc:
    print("1332 poll after stop()             : raised", type(exc).__name__, exc)
_pl_s2 = pl_get("/shutdown")
pl_poll("1333 poll: shutdown as 8th request", [pl_get("/version") for _ in range(7)] + [_pl_s2])
ns["_sock"], ns["_timer"] = None, None
_pl_socket_mod = ns["socket"]
ns["socket"] = types.SimpleNamespace(AF_INET=2, SOCK_STREAM=1, socket=lambda *a: types.SimpleNamespace(bind=lambda addr: None, listen=lambda n: None, setblocking=lambda b: None))
qc.QTimer = PLTimer
print("1334 start() prints:")
ns["start"]()
print("1334 start() result                :", "socket set", ns["_sock"] is not None, "| timer started", ns["_timer"].started, "| interval", ns["_timer"].ms, "| signal", ns["_timer"].sig)
print("1335 first /health after start():")
call("/health"); call("/health")
print("1335 (one line above, none for the second /health)")
ns["socket"] = _pl_socket_mod; del qc.QTimer
ns["_sock"], ns["_timer"] = None, None


# ---- v0.102: the activity log in FontLab's OUTPUT panel (cases 1336-1358). Fixed clock and time of day; replies are built
# with the listener's own _build_response in the shapes its write functions return (1357 checks those field names exist).
_al_saved = {k: ns[k] for k in ("_now_hms", "_clock", "_act_print", "_ACTIVITY_LOG")}
AL_CLOCK = [1000.0]
ns["_now_hms"] = lambda: "12:00:00"
ns["_clock"] = lambda: AL_CLOCK[0]
def al_reset(mode="normal"):
    ns["_ACTIVITY_LOG"] = mode
    ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
def al(method, path, body, code, reply):
    raw = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body or b"")
    ns["_activity_note"](method, path, raw, ns["_build_response"](code, reply))
def al_tick(advance):
    AL_CLOCK[0] += advance; ns["_activity_tick"]()
def al_case(tag): print(tag)
OK_W = {"open": True, "set": True, "name": "A", "route": "modern", "before": 500.0, "after": 600.0, "requested": 600, "synced_with_fontlab": True}

al_reset(); al_case("1336 create, verified / under another name / exists:")
al("POST", "/glyph/create", {"name": "kn2A"}, 200, {"open": True, "created": True, "before_count": 4651, "after_count": 4652})
al("POST", "/glyph/create", {"name": "kn 2B"}, 200, {"open": True, "created": False, "before_count": 4652, "after_count": 4653, "created_under_other_names": ["kn2B"], "reason": "createGlyph() did not raise, but FontLab created a glyph under a different name instead"})
al("POST", "/glyph/create", {"name": "A"}, 200, {"open": True, "created": False, "reason": "a glyph with this name already exists", "before_count": 3, "after_count": 3})
al_case("1337 delete, verified / declined / missing / removeGlyph raised:")
al("POST", "/glyph/delete", {"name": "kn2A"}, 200, {"open": True, "deleted": True, "before_count": 4653, "after_count": 4652})
al("POST", "/glyph/delete", {"name": "kn2B"}, 200, {"open": True, "deleted": False, "user_declined": True, "reason": "the deletion was not approved in FontLab (dialog answered No or closed)", "before_count": 4652, "after_count": 4652})
al("POST", "/glyph/delete", {"name": "Q"}, 200, {"open": True, "deleted": False, "reason": "no glyph with this name exists", "before_count": 3, "after_count": 3})
al("POST", "/glyph/delete", {"name": "kn2C"}, 200, {"open": True, "deleted": False, "call_error": "boom", "before_count": 3, "after_count": 3})
al_reset(); al_case("1338 six verified widths, then a unicode change (run of 3 shown, 3 counted, flushed by the new kind):")
for i, g in enumerate("ABCDEF"):
    al("POST", "/glyph/width", {"name": g, "width": 600 + i}, 200, dict(OK_W, name=g, before=500.0 + i, after=600.0 + i))
al("POST", "/glyph/unicode", {"name": "kn2A", "unicode": 0xE000}, 200, {"open": True, "set": True, "name": "kn2A", "before": None, "after": 0xE000, "requested": 0xE000})
al("POST", "/glyph/unicode", {"name": "A", "unicode": 0}, 200, {"open": True, "set": True, "name": "A", "before": 65, "after": None, "requested": 0})
al("POST", "/glyph/unicode", {"name": "Q", "unicode": 66}, 200, {"open": True, "set": False, "reason": "no glyph named 'Q'", "before": None, "after": None})
al_reset(); al_case("1339 a run broken by an unsynced width, a width with a warning, and a failed width:")
for g in "ABCD":
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al("POST", "/glyph/width", {"name": "E", "width": 612.5}, 200, dict(OK_W, name="E", after=612.5, synced_with_fontlab=False))
al("POST", "/glyph/width", {"name": "F", "width": 600}, 200, dict(OK_W, name="F", warning="the left sidebearing changed although only the advance width was set: the outline may have moved"))
al("POST", "/glyph/width", {"name": "G", "width": 600}, 200, {"open": True, "set": False, "name": "G", "before": 500.0, "after": 500.0, "requested": 600, "reason": "width did not change to the requested value after setting"})
al("POST", "/glyph/width", {"name": "H", "width": 600}, 200, {"open": True, "found": False, "set": False, "reason": "no glyph named 'H'", "before": None, "after": None})
al_case("1340 sidebearings, set / already so / refused:")
al("POST", "/glyph/sidebearings", {"name": "kn2A", "left": 50, "right": 40.25}, 200, {"open": True, "name": "kn2A", "set": True, "changed": True, "after": {"lsb": 50.0, "rsb": 40.25, "advance": 590.25}, "synced_with_fontlab": True})
al("POST", "/glyph/sidebearings", {"name": "kn2A", "left": 50, "right": 40.25}, 200, {"open": True, "name": "kn2A", "set": True, "changed": False, "after": {"lsb": 50.0, "rsb": 40.25, "advance": 590.25}})
al("POST", "/glyph/sidebearings", {"name": "kn2B", "left": 50, "right": 50}, 200, {"open": True, "name": "kn2B", "set": False, "reason": "this glyph has no outline, so it has no sidebearings to set: use set_glyph_width for its advance width"})
al_reset(); al_case("1341 draw, polygon / path with curves / failed after a change / not drawn:")
al("POST", "/glyph/polygon", {"name": "kn2A", "contours": [[[0, 0], [100, 0], [100, 100], [0, 100]], [[10, 10], [20, 10], [20, 20]]]}, 200, {"open": True, "name": "kn2A", "drawn": True, "route": "modern", "changed": True, "synced_with_fontlab": True})
al("POST", "/glyph/path", {"name": "kn2B", "contours": [[{"x": 0, "y": 0}, {"x": 100, "y": 0, "c1": {"x": 30, "y": 0}, "c2": {"x": 70, "y": 0}}, {"x": 50, "y": 80}]]}, 200, {"open": True, "name": "kn2B", "drawn": True, "nodes_match": True, "changed": True, "synced_with_fontlab": True})
al("POST", "/glyph/polygon", {"name": "kn2C", "points": [[0, 0], [100, 0], [50, 80]]}, 200, {"open": True, "name": "kn2C", "drawn": False, "changed": True, "reason": "after drawing, the layer reads 2 shape(s), 6 node(s) and 2 contour(s)"})
al("POST", "/glyph/path", {"name": "kn2D", "contours": [[{"x": 0, "y": 0}, {"x": 1, "y": 0}, {"x": 0, "y": 1}]]}, 200, {"open": True, "name": "kn2D", "drawn": False, "reason": "the glyph's layer is not KNOWN to be empty"})
al_case("1342 refused (400), failed (500), no font open, body not JSON, name missing, long texts cut:")
al("POST", "/glyph/width", {"name": "A", "width": -5}, 400, {"error": '"width" must not be negative'})
al("POST", "/glyph/unicode", {"name": "A", "unicode": 66}, 500, {"error": "RuntimeError: boom"})
al("POST", "/glyph/create", {"name": "kn2E"}, 200, {"open": False})
al("POST", "/glyph/create", b"{not json", 400, {"error": "request body was not valid JSON"})
al("POST", "/glyph/delete", {}, 400, {"error": '"name" must be a non-empty string'})
al("POST", "/glyph/create", {"name": "x" * 200}, 400, {"error": "e" * 300})
al_reset(); al_case("1343 .notdef note (v0.203: one OUTPUT line, no dialog): missing / empty early / empty mature / already noted / drawn (counted as a read):")
al("POST", "/font/notdef/warn", {}, 200, {"open": True, "status": "missing", "evidence": [], "noted": True, "already_noted": False})
al("POST", "/font/notdef/warn", {}, 200, {"open": True, "status": "empty", "evidence": [], "noted": True, "already_noted": False, "maturity": {"mature": False}})
al("POST", "/font/notdef/warn", {}, 200, {"open": True, "status": "empty", "evidence": [], "noted": True, "already_noted": False, "maturity": {"mature": True}})
al("POST", "/font/notdef/warn", {}, 200, {"open": True, "status": "empty", "evidence": [], "noted": False, "already_noted": True})
al("POST", "/font/notdef/warn", {}, 200, {"open": True, "status": "has_outline", "evidence": [], "noted": False, "already_noted": False})
print("1343 pending reads:", ns["_ACT"]["reads"])
al_case("1344 gated probes: answered / refused by the probe / HTTP error; a probe without go=yes is a read:")
al("GET", "/debug/trypkgkern?a=kn1L&b=kn1R&go=yes", None, 200, {"open": True, "package": {}, "legacy": {}})
al("GET", "/debug/trypkgkern?a=kn1L&b=kn1R&go=yes", None, 200, {"error": "refused: 20 calls per listener run are used up"})
al("GET", "/debug/trysync?go=yes", None, 500, {})
al("GET", "/debug/trypkgkern?a=kn1L&b=kn1R", None, 200, {"error": "refused: add &go=yes"})
print("1344 pending reads:", ns["_ACT"]["reads"])
al_reset(); al_case("1345 reads: counted, silent routes skipped, failures counted, nothing printed before the idle time:")
for p in ("/glyph/outline?name=A", "/glyph/outline?name=B", "/font/current", "/health", "/version", "/glyph/width?name=A", "/font/glyphs"):
    al("GET", p, None, 200, {"open": True})
al("GET", "/kerning/pairs?pairs=A:V,T:o", None, 200, {"open": True, "mode": "pairs", "count": 2})
al("POST", "/kerning/pairs", {"pairs": [["A", "V"], ["V", "A"], ["T", "o"]]}, 200, {"open": True, "mode": "pairs", "count": 3})
al("GET", "/kerning/pairs?text=AV", None, 400, {"error": "bad"})
al("GET", "/glyph/outline?name=Q", None, 404, {"error": "no glyph"})
al("GET", "/nowhere", None, 404, {"error": "unknown endpoint"})
al_tick(9.9); print("1345 after 9.9 s: (nothing above)")
al_tick(0.1); print("1345 after 10 s : reads line above; pending", ns["_ACT"]["pending"])
al_tick(30); print("1345 after 40 s : nothing new")
al_reset(); al_case("1346 an idle pause ends a run: 2 widths, 10 s idle (no summary: nothing was counted), 2 more widths shown again:")
for g in "AB":
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al_tick(10)
for g in "CD":
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al_reset(); al_case("1347 a reads summary waits during a run and comes before the next kind:")
for g in "ABCDE":
    al("GET", "/glyph/width?name=" + g, None, 200, {"open": True})
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al("POST", "/glyph/create", {"name": "kn2F"}, 200, {"open": True, "created": True, "before_count": 3, "after_count": 4})
al_reset(); al_case("1348 mode 'writes': changes printed, reads neither counted nor printed:")
ns["_ACTIVITY_LOG"] = "writes"
al("GET", "/glyph/outline?name=A", None, 200, {"open": True})
al("POST", "/glyph/create", {"name": "kn2G"}, 200, {"open": True, "created": True, "before_count": 4, "after_count": 5})
al_tick(10); print("1348 reads kept:", ns["_ACT"]["reads"])
al_reset("off"); al_case("1349 mode 'off': nothing at all:")
al("POST", "/glyph/create", {"name": "kn2H"}, 200, {"open": True, "created": True, "before_count": 5, "after_count": 6})
al("GET", "/glyph/outline?name=A", None, 200, {"open": True})
al_tick(10); print("1349 state:", ns["_ACT"]["reads"], ns["_ACT"]["kind"], ns["_ACT"]["pending"])
al_reset(); al_case("1350 numbers and code points:")
print("     ", [ns["_act_num"](v) for v in (600.0, 612.5, -0.25, 1e-9, -1e-9, 0.105, 3, True, None, "7")], [ns["_act_codepoint"](v) for v in (65, 0x1F600, None, True)])
al_reset(); al_case("1351 broken input never raises (the last reply cannot happen: the route refuses such a body):")
for args in (("POST", "/glyph/width", b"{}", b""), ("POST", "/glyph/width", b"{}", b"HTTP/1.1 abc"), ("GET", None, b"", b"x"),
             ("POST", "/glyph/polygon", b'{"name":"A","contours":7}', ns["_build_response"](200, {"open": True, "drawn": True}))):
    try:
        ns["_activity_note"](*args); print("      no exception")
    except Exception as exc:
        print("      RAISED", type(exc).__name__, exc)
al_reset(); al_case("1352 a print that raises: the reply is still sent unchanged, and the tick survives:")
def _al_boom(text): raise RuntimeError("OUTPUT gone")
ns["_act_print"] = _al_boom
_al_c = PLConn(b'POST /glyph/width HTTP/1.1\r\nContent-Length: 27\r\n\r\n{"name": "A", "width": -5}\n')
ns["_handle"](_al_c); print("1352 reply:", pl_status(_al_c))
ns["_ACT"].update(more=2, kind="width", pending=True)
try:
    al_tick(10); print("1352 tick: no exception")
except Exception as exc:
    print("1352 tick: RAISED", exc)
ns["_act_print"] = _al_saved["_act_print"]
al_reset(); al_case("1353 end to end through _handle: a refused width and a read:")
_al_c = PLConn(b'POST /glyph/width HTTP/1.1\r\nContent-Length: 27\r\n\r\n{"name": "A", "width": -5}\n')
ns["_handle"](_al_c); print("1353 reply:", pl_status(_al_c))
_al_c = pl_get("/font/glyphs"); ns["_handle"](_al_c); print("1353 reads pending:", ns["_ACT"]["reads"])
al_reset(); al_case("1354 the poll timer prints the summary once the listener is idle:")
al("GET", "/glyph/outline?name=A", None, 200, {"open": True})
AL_CLOCK[0] += 10
pl_poll("1354 poll, no requests", [])
al_reset(); al_case("1355 /shutdown prints what is pending before 'Listener stopped.':")
for g in "ABCDE":
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al("GET", "/glyph/outline?name=A", None, 200, {"open": True})
pl_poll("1355 poll: shutdown", [pl_get("/shutdown")])
al_reset(); al_case("1356 the gated-probe line for a /debug route with go=yes among other parameters:")
al("GET", "/debug/findnode?name=A&go=yes&index=1", None, 200, {"x": 1})
_al_src = src[:src.index("# Activity log in FontLab's OUTPUT panel (v0.102)")] + src[src.index("def _handle(conn):"):]
_al_keys = ("open", "created", "before_count", "after_count", "created_under_other_names", "reason", "call_error", "deleted",
            "user_declined", "set", "warning", "before", "after", "synced_with_fontlab", "changed", "drawn", "nodes_match",
            "dialog_shown", "dialog_error", "status", "count", "error", "lsb", "rsb")
print("1357 reply fields the log reads but the rest of the listener never writes:", [k for k in _al_keys if f'"{k}"' not in _al_src])
_al_block = src[src.index("# Activity log in FontLab's OUTPUT panel (v0.102)"):src.index("def _handle(conn):")]
_al_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _al_block).splitlines())
print("1358 static scan of the log block: fontlab calls:", _re83.findall(r"\bfl\.\w+|\bfontlab\b|CurrentFont|QMessageBox|(?<!_ACT)\.update\(", _al_code),
      "| entry points with try/except:", [f for f in ("_activity_note", "_activity_tick") if "try:" in _al_block.split("def " + f)[1].split("\ndef ")[0]])
for k, v in _al_saved.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"]); ns["_sock"], ns["_timer"] = None, None

# ---- v0.102 (continued): deletes never collapse; unsynced sidebearings and drawings are always shown (case 1359).
_al_saved2 = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
al_reset(); al_case("1359 four deletes; four sidebearings and four drawings, the second of each not synced:")
for g in "ABCD":
    al("POST", "/glyph/delete", {"name": g}, 200, {"open": True, "deleted": True, "before_count": 9, "after_count": 8})
for i, g in enumerate("ABCD"):
    al("POST", "/glyph/sidebearings", {"name": g, "left": 10, "right": 10}, 200, {"open": True, "name": g, "set": True, "changed": True, "after": {"lsb": 10.0, "rsb": 10.0, "advance": 300.0}, "synced_with_fontlab": i != 1})
for i, g in enumerate("ABCD"):
    al("POST", "/glyph/polygon", {"name": g, "points": [[0, 0], [10, 0], [0, 10]]}, 200, {"open": True, "name": g, "drawn": True, "changed": True, "synced_with_fontlab": i != 1})
al_tick(10)
for k, v in _al_saved2.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"])

# ---- v0.102 (continued): a warning inside a run is never swallowed; a create that raised is not a success (case 1360).
_al_saved3 = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
al_reset(); al_case("1360 four verified widths, a fifth with a warning, a sixth verified; then a create whose call raised:")
for g in "ABCD":
    al("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g))
al("POST", "/glyph/width", {"name": "E", "width": 600}, 200, dict(OK_W, name="E", warning="the left sidebearing changed although only the advance width was set: the outline may have moved"))
al("POST", "/glyph/width", {"name": "F", "width": 600}, 200, dict(OK_W, name="F"))
al("POST", "/glyph/create", {"name": "kn2J"}, 200, {"open": True, "created": False, "before_count": 9, "after_count": 9, "call_error": "RuntimeError: createGlyph failed"})
al_tick(10)
for k, v in _al_saved3.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"])

# ================= v0.103: /debug/trykerngroups (gated research probe: kerning group members and sides; allow-list spies) =================
print("\n==== v0.103 /debug/trykerngroups ====")
KG = {"cfg": {}, "forbidden": [], "all": set(), "calls": []}
class KGSpy:
    """A native-looking fake: every public member outside its allow-list aborts the run; subscripts and iteration are forbidden."""
    def __init__(self, label, allowed, attrs, length=None): object.__setattr__(self, "_kg", (label, allowed, attrs, length))
    def __getattribute__(self, n):
        if n.startswith("_"): return object.__getattribute__(self, n)
        label, allowed, attrs, _ = object.__getattribute__(self, "_kg")
        KG["all"].add(label + "." + n)
        if n not in allowed:
            KG["forbidden"].append(label + "." + n); raise SystemExit("FORBIDDEN member touched: " + label + "." + n)
        if n not in attrs: raise AttributeError(n)
        v = attrs[n]
        if isinstance(v, Exception): raise v
        return v
    def __len__(self):
        length = object.__getattribute__(self, "_kg")[3]
        if isinstance(length, Exception): raise length
        if callable(length): return length()
        if length is None: raise TypeError("object has no len()")
        return length
    def __getitem__(self, k):
        KG["forbidden"].append("subscript"); raise SystemExit("FORBIDDEN subscript on a native object")
    def __iter__(self):
        KG["forbidden"].append("iteration"); raise SystemExit("FORBIDDEN iteration of a native object")
_KG_GROUP_OK = ("name", "mode", "isLeft", "isRight", "isBoth", "isFeaGroup", "id")
def kg_group(name, mode, left, right, gid, **over):
    attrs = {"name": name, "mode": mode, "isLeft": left, "isRight": right, "isBoth": False, "isFeaGroup": False, "id": gid}
    attrs.update(over)
    return KGSpy("group", _KG_GROUP_OK, attrs)
def _kg_track(label, value):
    def _f(*args):
        KG["calls"].append((label,) + args)
        if isinstance(value, Exception): raise value
        return value() if callable(value) else value
    return _f
_KG_ALL_DEFAULT = [(True, "kc1A", 0, 0, ["kc1A", "kc1B"]), (True, "kc1rgt", 1, 0, ["kc1C", "kc1D"]), (False, "fea1", 2, 0, ["kc1A", "x"])]
def _kg_len_seq(first, later):
    seen = {"n": 0}
    def _f():
        seen["n"] += 1
        return first if seen["n"] == 1 else later
    return _f
def kg_build():
    c = KG["cfg"]
    values = c.get("values", lambda: [kg_group("kc1A", "KernLeftGroupMode", True, False, 0), kg_group("kc1rgt", "KernRightGroupMode", False, True, 1)])
    groups_len = c.get("groups_len", 2)
    if c.get("groups_len_after") is not None:
        groups_len = _kg_len_seq(groups_len, c["groups_len_after"])
    items = c.get("items", lambda: [("kgtL", (["kgt1", "kgt2"], "KernLeft")), ("kgtB", (["kgt5", "kgt6"], "KernBothSide")),
                                    ("kgtR", (["kgt3", "kgt4"], "KernRight"))])      # v0.189: the shape documented in test 1373
    container = c.get("groups", KGSpy("groups", ("values", "items"), {"values": c.get("values_attr", _kg_track("values", values)),
                                                                      "items": c.get("items_attr", _kg_track("items", items))}, groups_len))
    k_len = c.get("kerning_len", 2)
    if c.get("kerning_len_after") is not None:
        k_len = _kg_len_seq(k_len, c["kerning_len_after"])
    kerning = KGSpy("kerning", ("groups",), {"groups": container}, k_len)
    pkg_attrs = {"isNull": lambda: False, "masters": c.get("masters", ["Regular"]), "master": c.get("master", "Regular"),
                 "kerning": c.get("kerning_attr", _kg_track("kerning", c.get("kerning_call", kerning))),
                 "getAllGroups": c.get("getall_attr", _kg_track("getAllGroups", c.get("getall", _KG_ALL_DEFAULT)))}
    pkg = KGSpy("package", ("isNull", "masters", "master", "kerning", "getAllGroups"), pkg_attrs)
    glyphs = [KGSpy("glyph", ("name", "kerningLeft", "kerningRight"),
                    dict({"name": n, "kerningLeft": 1, "kerningRight": 0}, **(c.get("glyph_attrs", {}) if n == "kc1A" else {}))) for n in ("kc1A", "kc1B", "kc1C", "kc1D")]
    font = KGSpy("font", ("glyphs",), {"glyphs": glyphs})
    return pkg, font
class KGWorkspace:
    @staticmethod
    def instance(): return KG_WS
    def packages(self): return [KG["pkg"]] * KG["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return KG["pkg"]
KG_WS = KGWorkspace()
_kg_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace")]
def kg_setup(calls=0, **cfg):
    KG["cfg"] = dict(cfg); KG["calls"].clear()
    ns["_TRYKERNGROUPS"]["calls"] = calls
    KG["pkg"], font = kg_build()
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = KGWorkspace
        _m.CountFonts = (lambda: count)
        _m.CurrentFont = (lambda: None) if cfg.get("cur") == "none" else (lambda: font)
def kgc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| calls", KG["calls"])
    return c, d
_KGA = "/debug/trykerngroups?stage=all&contains=kc1A&go=yes"
_KGM = "/debug/trykerngroups?stage=modes&contains=kc1A,kc1rgt&go=yes"
_KGG = "/debug/trykerngroups?stage=glyph&name=kc1A&go=yes"
kg_setup(); kgc("1370 no go: nothing runs         ", "/debug/trykerngroups?stage=all&contains=kc1A")
kg_setup(); kgc("1371 go=maybe: nothing runs      ", "/debug/trykerngroups?stage=all&contains=kc1A&go=maybe")
kg_setup(); kgc("1372 unknown stage               ", "/debug/trykerngroups?stage=bogus&contains=kc1A&go=yes")
kg_setup(); kgc("1372b no stage                   ", "/debug/trykerngroups?contains=kc1A&go=yes")
kg_setup(); c, d = kgc("1373 all, contains kc1A          ", _KGA)
print("1373b note present                 :", "nothing is changed or saved" in d.get("note", ""))
kg_setup(); kgc("1374 all, a group name           ", "/debug/trykerngroups?stage=all&contains=kc1rgt&go=yes", keys=("count", "kern_groups", "matched", "entries"))
kg_setup(); kgc("1375 all, no match               ", "/debug/trykerngroups?stage=all&contains=zzz&go=yes", keys=("count", "matched", "entries", "cut"))
kg_setup(); kgc("1376 all, contains missing       ", "/debug/trykerngroups?stage=all&go=yes")
kg_setup(); kgc("1377 all, four tokens            ", "/debug/trykerngroups?stage=all&contains=a,b,c,d&go=yes")
for bad in ("A%20V", "%40kc1A", "A:V", "x" * 64, "%C3%A9"):
    kg_setup(); kgc(f"1378 bad token {bad[:10]!r:12}     ", "/debug/trykerngroups?stage=all&contains=" + bad + "&go=yes")
kg_setup(); kgc("1379 all with name               ", "/debug/trykerngroups?stage=all&contains=kc1A&name=kc1A&go=yes")
kg_setup(); kgc("1380 modes, kc1A and kc1rgt      ", _KGM)
kg_setup(values=lambda: [kg_group("kc1A", "KernLeftGroupMode", True, False, i) for i in range(25)])
kgc("1380b modes, 25 matches: cut     ", _KGM, keys=("count", "matched", "cut"))
print("1380c shown                        :", len(call(_KGM)[1]["entries"]))
kg_setup(values=lambda: [kg_group("kc1A", "KernLeftGroupMode", _kg_track("isLeft()", True), False, 0)])
kgc("1381 modes, isLeft is a method   ", _KGM, keys=("first_entry", "matched"))
kg_setup(values=lambda: [kg_group("kc1A", RuntimeError("mode boom"), True, False, 0)])
kgc("1382 modes, mode raises          ", _KGM, keys=("first_entry",))
kg_setup(values=lambda: [kg_group(_kg_track("name()", "kc1A"), "KernLeftGroupMode", True, False, 0)])
kgc("1382b modes, name is a method    ", _KGM, keys=("first_entry", "matched", "entries"))
kg_setup(values=lambda: KGSpy("valuesresult", (), {}, 2)); kgc("1383 modes, values not a list    ", _KGM, keys=("values_type", "note_modes", "count", "entries", "groups_len_before"))
kg_setup(values_attr=5); kgc("1384 modes, values not callable  ", _KGM, keys=("call_error", "groups_len_before", "groups_len_after", "side_effect_detected"))
kg_setup(values=RuntimeError("values boom")); kgc("1385 modes, values raises        ", _KGM, keys=("call_error", "groups_len_before", "groups_len_after", "side_effect_detected"))
kg_setup(groups=RuntimeError("groups boom")); kgc("1386 modes, groups raises        ", _KGM, keys=("call_error", "groups_type", "side_effect_detected"))
kg_setup(groups=_kg_track("groups()", [])); kgc("1387 modes, groups is callable   ", _KGM, keys=("call_error", "groups_type", "count"))
kg_setup(groups_len_after=3); kgc("1388 modes, groups len changes   ", _KGM, keys=("groups_len_before", "groups_len_after", "groups_side_effect_detected"))
kg_setup(groups_len=RuntimeError("len boom")); kgc("1388b modes, groups len raises  ", _KGM, keys=("groups_len_before", "groups_len_after", "groups_side_effect_detected", "matched"))
kg_setup(getall=KGSpy("allresult", (), {}, 3)); kgc("1389 all, not a list            ", _KGA, keys=("result_type", "note_all", "count", "entries"))
kg_setup(getall=RuntimeError("getAllGroups boom")); kgc("1390 all, getAllGroups raises   ", _KGA, keys=("call_error", "count", "side_effect_detected"))
kg_setup(getall_attr=5); kgc("1391 all, not callable           ", _KGA, keys=("call_error", "count"))
kg_setup(getall=[(True, "kc1A", 0, 0), (True, 5, 1, 0, ["kc1A"]), (True, "g", 1, 0, "kc1A"), "kc1A", (True, "kc1A", 0, 0, ("kc1A",))])
kgc("1392 all, malformed entries      ", _KGA, keys=("count", "first_entry_types", "kern_groups", "malformed", "matched", "entries"))
kg_setup(getall=[(True, "g1", 0, 0, [KGSpy("member", (), {}), "kc1B"]), (1, "g2", 1, 0, ["kc1A"])])
kgc("1393 all, native member, flag 1  ", _KGA, keys=("kern_groups", "matched", "entries"))
kg_setup(getall=[(True, "g%02d" % i, i, 0, ["kc1A"]) for i in range(25)]); kgc("1394 all, 25 matches: cut at 20  ", _KGA, keys=("count", "matched", "cut"))
print("1394b shown                        :", len(call(_KGA)[1]["entries"]))
kg_setup(getall=[]); kgc("1395 all, empty list            ", _KGA, keys=("count", "first_entry_types", "kern_groups", "matched"))
kg_setup(getall=[(True, "g1", 0, 0, ["kc1A"] * 60)]); kgc("1395b all, 60 members           ", _KGA, keys=("matched",))
print("1395c members shown                :", len(call(_KGA)[1]["entries"][0]["members"]))
kg_setup(kerning_len_after=3); kgc("1396 kerning len changes        ", _KGA, keys=("kerning_len_before", "kerning_len_after", "side_effect_detected"))
kg_setup(kerning_len=RuntimeError("len boom")); kgc("1396b kerning len raises       ", _KGA, keys=("kerning_len_before", "kerning_len_after", "side_effect_detected", "matched"))
kg_setup(kerning_call=RuntimeError("kerning() boom")); kgc("1397 kerning() raises (counted)  ", _KGA)
kg_setup(kerning_attr=5); kgc("1398 kerning not callable       ", _KGA)
kg_setup(kerning_attr=RuntimeError("attr boom")); kgc("1398b kerning not reachable    ", _KGA)
kg_setup(masters=KGSpy("masterlist", (), {})); kgc("1399 masters not a plain list   ", _KGA)
kg_setup(masters=["Regular", 5]); kgc("1399b masters not all names    ", _KGA)
kg_setup(masters=RuntimeError("masters boom")); kgc("1399c masters raises           ", _KGA)
kg_setup(master="Ghost"); kgc("1399d current master unlisted  ", _KGM)
kg_setup(master=RuntimeError("master boom")); kgc("1399e current master raises    ", _KGM)
kg_setup(); kgc("1400 glyph kc1A                  ", _KGG)
kg_setup(glyph_attrs={"kerningRight": _kg_track("kerningRight()", 7), "kerningLeft": RuntimeError("left boom")}); kgc("1401 glyph: method and raise     ", _KGG)
kg_setup(glyph_attrs={"kerningRight": KGSpy("native", (), {})}); kgc("1401b glyph: native value       ", _KGG, keys=("kerningLeft", "kerningRight"))
kg_setup(); kgc("1402 glyph unknown (not counted) ", "/debug/trykerngroups?stage=glyph&name=Q&go=yes")
kg_setup(); kgc("1403 glyph with contains         ", "/debug/trykerngroups?stage=glyph&name=kc1A&contains=kc1A&go=yes")
kg_setup(); kgc("1403b glyph without name         ", "/debug/trykerngroups?stage=glyph&go=yes")
kg_setup(); kgc("1403c glyph, bad name            ", "/debug/trykerngroups?stage=glyph&name=A%20V&go=yes")
for tag, over in (("1404 no font open         ", dict(count=0)), ("1404b two fonts open      ", dict(count=2)),
                  ("1404c two packages        ", dict(packages=2)), ("1404d CurrentFont None    ", dict(cur="none"))):
    kg_setup(**over); kgc(tag, _KGA)
kg_setup(calls=9); kgc("1405 request 10 allowed         ", _KGG, keys=("kerningLeft", "calls_so_far", "max_calls"))
KG["calls"].clear(); kgc("1405b request 11 refused        ", _KGG)
kg_setup(calls=10); kgc("1405c modes refused at the cap   ", _KGM)
kg_setup(); _kg_real = ns["debug_try_kern_groups"]
def _kg_boom(*a): raise RuntimeError("probe boom")
ns["debug_try_kern_groups"] = _kg_boom; kgc("1406 probe raises: HTTP 500     ", _KGA); ns["debug_try_kern_groups"] = _kg_real
kg_setup(); print("1407 direct: contains not a list  :", ns["debug_try_kern_groups"]("all", "kc1A", None, "yes"), "| calls", KG["calls"])
kg_setup()
for _p in (_KGA, _KGM, _KGG, "/debug/trykerngroups?stage=all&contains=kc1A"): call(_p)
print("1408 spy over all cases          : forbidden:", KG["forbidden"], "| members touched anywhere:", sorted(KG["all"]))
_kg_src = src[src.index("_TRYKERNGROUPS = {"):src.index("# /debug/features (v0.107)")]
_kg_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _kg_src).splitlines())
print("1409 static scan                 : method calls:", sorted(set(_re83.findall(r"\b(\w+\.\w+)\(", _kg_code))),
      "| subscripts:", sorted(set(_re83.findall(r"\b(\w+)\[", _kg_code))),
      "| forbidden names:", _re83.findall(r"\b(?:keys|asDict|has_key|clear|remove|rename|findGroup|deleteGroups|autoKern|save\w*|update)\b", _kg_code.replace("out.update(", "")),
      "| items only as container.items (v0.189):", _re83.findall(r"[\w.]*\bitems\b\(?", _kg_code),
      "| getter( / entries_of( / kerning_of( calls:", [len(_re83.findall(r"\b" + f + r"\(", _kg_code)) for f in ("getter", "entries_of", "kerning_of")],
      "| counted before the first native call:", _kg_code.index('_TRYKERNGROUPS[""] += 1') < _kg_code.index("_trykerngroups_attr(glyph"),
      _kg_code.rindex('_TRYKERNGROUPS[""] += 1') < _kg_code.index("kerning_of(current)"), "| scanned chars > 5000:", len(_kg_src) > 5000)
print("1410 gate, cap, route, docstring  :", "go != \"yes\"" in _kg_src, "| max requests", ns["_TRYKERNGROUPS_MAX"], "| shown", ns["_TRYKERNGROUPS_SHOWN"],
      "| route registered once:", src.count('path == "/debug/trykerngroups"') == 1, "| listed in the module docstring:", "/debug/trykerngroups" in src[:src.index('"""', 3)])
# ---- v0.188 (P1.6): stage=tuples reads the values() entries of the master's kerning groups as plain data (test 199: plain tuples)
print("\n==== v0.188 /debug/trykerngroups stage=tuples ====")
KG["forbidden"].clear(); KG["all"].clear()
_KGT = "/debug/trykerngroups?stage=tuples&contains=kc1A,kc1rgt&go=yes"
class _KGList(list): pass
class _KGTuple(tuple): pass
_KG_T_DEFAULT = lambda: [("kc1A", (["kc1A", "kc1B"], "KernLeftGroupMode")), ("kc1rgt", (["kc1C", "kc1D"], "KernRightGroupMode")),
                         ("fea1", (["x"], "FeaClassGroupMode"))]
kg_setup(values=_KG_T_DEFAULT); c, d = kgc("2585 tuples, two names           ", _KGT)
print("2585b note present                 :", "nothing is changed or saved" in d.get("note", ""))
kg_setup(values=lambda: [(["kc1A", "kc1B"], "KernLeftGroupMode", 8704), (["kc1C"], "KernRightGroupMode", 8709)])
kgc("2586 tuples, a member matches    ", "/debug/trykerngroups?stage=tuples&contains=kc1B&go=yes", keys=("count", "shapes", "matched", "entries"))
kg_setup(values=lambda: [(KGSpy("group", (), {}), ["kc1A"], KGSpy("pair", (), {}, 2))])
kgc("2587 tuples, native fields       ", _KGT, keys=("first_entry", "matched", "entries"))
kg_setup(values=lambda: [KGSpy("group", (), {}), KGSpy("group", (), {})])
kgc("2588 tuples, native entries      ", _KGT, keys=("count", "shapes", "first_entry", "matched"))
kg_setup(values=lambda: KGSpy("valuesresult", (), {}, 2)); kgc("2589 tuples, values not a list   ", _KGT, keys=("values_type", "note_tuples", "count", "entries"))
kg_setup(values=lambda: _KGList([("kc1A", 1)])); kgc("2589b tuples, a list subclass    ", _KGT, keys=("values_type", "note_tuples", "count"))
kg_setup(values=lambda: [_KGTuple(("kc1A", 1)), ["kc1A", _KGList(["kc1A"])]])
kgc("2589c tuples, subclass entries   ", "/debug/trykerngroups?stage=tuples&contains=kc1A&go=yes", keys=("shapes", "first_entry", "matched", "entries"))
kg_setup(values=lambda: [("kc1A", i) for i in range(25)]); kgc("2590 tuples, 25 matches: cut     ", _KGT, keys=("count", "shapes", "matched", "cut"))
print("2590b shown, positions             :", [e["position"] for e in call(_KGT)[1]["entries"]])
kg_setup(values=lambda: [("kc1A", ["m%02d" % i for i in range(60)], 1, 2, 3, 4, 5, 6, 7, 8)])
c, d = kgc("2591 tuples, 60 items, 10 fields ", _KGT, keys=("shapes", "matched"))
_kg_e = d["entries"][0]
print("2591b entry                        : length", _kg_e["length"], "fields", len(_kg_e["fields"]), "cut", _kg_e["cut"],
      "| field 1:", _kg_e["fields"][1]["type"], _kg_e["fields"][1]["length"], len(_kg_e["fields"][1]["values"]), _kg_e["fields"][1]["cut"],
      _kg_e["fields"][1]["values"][:3], "| last field shown:", _kg_e["fields"][-1])
kg_setup(values=lambda: [("kc1A", i) for i in range(20)]); kgc("2590c tuples, exactly 20: no cut   ", _KGT, keys=("matched", "cut"))
kg_setup(values=lambda: [("kc1A", ["m%02d" % i for i in range(50)], 1, 2, 3, 4, 5, 6)])
_kg_e = call(_KGT)[1]["entries"][0]
print("2591c exactly 8 fields, 50 elements: length", _kg_e["length"], "fields", len(_kg_e["fields"]), "cut", _kg_e["cut"],
      "| field 1:", _kg_e["fields"][1]["length"], len(_kg_e["fields"][1]["values"]), _kg_e["fields"][1]["cut"])
kg_setup(values=lambda: [("g1", [("kc1A",)]), ("g2", [["kc1A"]])])
kgc("2592b tuples, a token too deep   ", "/debug/trykerngroups?stage=tuples&contains=kc1A&go=yes", keys=("count", "matched", "entries"))
kg_setup(values=lambda: [("g1", [("kc1A", True)] + [list(range(15))], ([KGSpy("member", (), {})], "deep"))])
kgc("2592 tuples, nested sequences    ", "/debug/trykerngroups?stage=tuples&contains=kc1A,deep&go=yes", keys=("matched", "entries"))
kg_setup(values=lambda: []); kgc("2593 tuples, empty list          ", _KGT, keys=("count", "shapes", "first_entry", "matched", "entries", "cut"))
kg_setup(values=lambda: [("a", 1), ("b", 1, 2), "kc1A", 5, None]); kgc("2594 tuples, mixed shapes        ", _KGT, keys=("count", "shapes", "first_entry", "matched", "entries"))
kg_setup(values=RuntimeError("values boom")); kgc("2595 tuples, values raises       ", _KGT, keys=("call_error", "groups_len_before", "groups_len_after", "side_effect_detected"))
kg_setup(values=_KG_T_DEFAULT, groups_len_after=4, kerning_len_after=3)
kgc("2596 tuples, lengths change      ", _KGT, keys=("groups_len_before", "groups_len_after", "groups_side_effect_detected", "kerning_len_before",
                                                     "kerning_len_after", "side_effect_detected"))
kg_setup(values=_KG_T_DEFAULT); kgc("2597 tuples with name: refused   ", "/debug/trykerngroups?stage=tuples&contains=kc1A&name=kc1A&go=yes")
kg_setup(values=_KG_T_DEFAULT); kgc("2597b tuples, no contains       ", "/debug/trykerngroups?stage=tuples&go=yes")
kg_setup(values=_KG_T_DEFAULT); kgc("2597c tuples, no go: nothing runs", "/debug/trykerngroups?stage=tuples&contains=kc1A")
kg_setup(values=_KG_T_DEFAULT, calls=10); kgc("2598 tuples refused at the cap   ", _KGT)
kg_setup(values=_KG_T_DEFAULT, count=2); kgc("2598b tuples, two fonts open     ", _KGT)
print("2599 spy over the tuples cases    : forbidden:", KG["forbidden"], "| members touched anywhere:", sorted(KG["all"]))
print("2599b stages and caps             :", ns["_TRYKERNGROUPS_STAGES"], ns["_TRYKERNGROUPS_FIELDS"], ns["_TRYKERNGROUPS_ITEMS"],
      "| stage=tuples in the module docstring:", "stage=tuples (v0.188)" in src[:src.index('"""', 3)])
# ---- v0.189 (P1.6): stage=items reads groups.items(), documented (test 1373) as list(tuple('groupName', tuple(list('glyphName'), mode)))
print("\n==== v0.189 /debug/trykerngroups stage=items ====")
KG["forbidden"].clear(); KG["all"].clear()
_KGI = "/debug/trykerngroups?stage=items&contains=kgtL,kgtR&go=yes"
kg_setup(); c, d = kgc("2600 items, two group names      ", _KGI)
print("2600b note present                 :", "nothing is changed or saved" in d.get("note", ""))
kg_setup(); kgc("2601 items, a member matches     ", "/debug/trykerngroups?stage=items&contains=kgt5&go=yes", keys=("count", "shapes", "matched", "entries"))
kg_setup(items=lambda: [("g1", (["x", ["kgt9"]], "KernLeft")), ("g2", (["kgt9"], "KernRight"))])
kgc("2601b items, a token too deep    ", "/debug/trykerngroups?stage=items&contains=kgt9&go=yes", keys=("count", "matched", "entries"))
kg_setup(values=lambda: [("g1", (["kgt5"], "KernLeft"))])
kgc("2601c tuples keeps its depth     ", "/debug/trykerngroups?stage=tuples&contains=kgt5&go=yes", keys=("count", "matched"))
kg_setup(items=lambda: KGSpy("itemsresult", (), {}, 3)); kgc("2602 items, not a list           ", _KGI, keys=("items_type", "note_items", "values_type", "count", "entries"))
kg_setup(items=lambda: _KGList([("kgtL", (["kgt1"], "KernLeft"))])); kgc("2602b items, a list subclass     ", _KGI, keys=("items_type", "note_items", "count"))
kg_setup(items_attr=5); kgc("2603 items, not callable         ", _KGI, keys=("call_error", "groups_len_before", "groups_len_after", "side_effect_detected"))
kg_setup(items=RuntimeError("items boom")); kgc("2604 items, raises               ", _KGI, keys=("call_error", "groups_len_before", "groups_len_after", "side_effect_detected"))
kg_setup(items=lambda: [(KGSpy("name", (), {}), (["kgtL"], KGSpy("mode", (), {}))), KGSpy("entry", (), {})])
kgc("2605 items, native parts         ", _KGI, keys=("count", "shapes", "first_entry", "matched", "entries"))
kg_setup(items=lambda: [("kgtL", (["m%02d" % i for i in range(60)], "KernLeft")), ("kgtR", (["n%02d" % i for i in range(50)], "KernRight"))])
_kg_i = call(_KGI)[1]["entries"]
print("2605b items, 60 and 50 members     :", [(e["fields"][0], e["fields"][1]["values"][0]["length"], len(e["fields"][1]["values"][0]["values"]),
                                                 e["fields"][1]["values"][0]["cut"], e["fields"][1]["values"][0]["values"][-1]) for e in _kg_i])
kg_setup(groups_len_after=4, kerning_len_after=3)
kgc("2606 items, lengths change       ", _KGI, keys=("groups_len_before", "groups_len_after", "groups_side_effect_detected", "kerning_len_before",
                                                     "kerning_len_after", "side_effect_detected"))
kg_setup(); kgc("2607 items with name: refused    ", "/debug/trykerngroups?stage=items&contains=kgtL&name=kgt1&go=yes")
kg_setup(); kgc("2607b items, no go: nothing runs ", "/debug/trykerngroups?stage=items&contains=kgtL")
kg_setup(calls=10); kgc("2607c items refused at the cap    ", _KGI)
kg_setup(count=2); kgc("2607d items, two fonts open      ", _KGI)
kg_setup(); call("/debug/trykerngroups?stage=tuples&contains=kgt1&go=yes"); print("2608 tuples calls values only     :", KG["calls"])
kg_setup(); call(_KGI); print("2608b items calls items only      :", KG["calls"])
print("2609 spy over the items cases     : forbidden:", KG["forbidden"], "| members touched anywhere:", sorted(KG["all"]))
print("2609b stages                      :", ns["_TRYKERNGROUPS_STAGES"], "| stage=items in the module docstring:", "stage=items (v0.189)" in src[:src.index('"""', 3)])

# ================= v0.190 (P1.6): GET / POST /kerning/groups, the product read of kerning groups (allow-list spies) =================
print("\n==== v0.190 /kerning/groups ====")
KG["forbidden"].clear(); KG["all"].clear()
_KR_ITEMS = [("kgtL", (["kgt1", "kgt2"], "KernLeft")), ("kgtB", (["kgt5", "kgt6"], "KernBothSide")), ("kgtR", (["kgt3", "kgt4"], "KernRight"))]
_KR_ALL = [(True, "kgtL", 5121, 0, ["kgt1", "kgt2"]), (True, "kgtR", 5122, 0, ["kgt3", "kgt4"]), (True, "kgtB", 5123, 0, ["kgt5", "kgt6"]),
           (False, "kgtF", 5125, 0, ["kgt7", "kgt8"])]
KR = {"cfg": {}}
def kr_build():
    c = KR["cfg"]
    glen = c.get("groups_len", 3)
    if c.get("groups_len_after") is not None: glen = _kg_len_seq(glen, c["groups_len_after"])
    klen = c.get("kerning_len", 0)
    if c.get("kerning_len_after") is not None: klen = _kg_len_seq(klen, c["kerning_len_after"])
    container = c.get("groups", KGSpy("groups", ("items",), {"items": c.get("items_attr", _kg_track("items", c.get("items", lambda: list(_KR_ITEMS))))}, glen))
    kerning = KGSpy("kerning", ("groups", "get"), {"groups": container, "get": lambda *a: None}, klen)
    pkg = KGSpy("package", ("isNull", "masters", "master", "kerning", "getAllGroups", "path"),
                {"isNull": lambda: False, "masters": c.get("masters", ["Regular"]), "master": "Regular", "path": c.get("pkg_path", "C:/x/kg.vfc"),
                 "kerning": _kg_track("kerning", kerning), "getAllGroups": c.get("getall_attr", _kg_track("getAllGroups", c.get("getall", list(_KR_ALL))))})
    names = c.get("glyph_names", ["kgt%d" % i for i in range(1, 9)])
    glyphs = [KGSpy("glyph", ("name",), {"name": n}) for n in names]
    info = KGSpy("info", ("familyName", "styleName"), {"familyName": "Unnamed", "styleName": "Regular"})
    font = KGSpy("font", ("glyphs", "info", "path"), {"glyphs": glyphs, "info": info, "path": c.get("font_path", "C:/x/kg.vfc")})
    return pkg, font
def kr_setup(**cfg):
    KR["cfg"] = dict(cfg); KG["cfg"] = dict(cfg); KG["calls"].clear()       # KG["cfg"]: KGWorkspace.packages() reads "packages" there
    KG["pkg"], font = kr_build()
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = KGWorkspace
        _m.CountFonts = (lambda: count)
        _m.CurrentFont = (lambda: None) if cfg.get("cur") == "none" else (lambda: font)
def krc(tag, path, keys=None):
    c, d = call(path)
    shown = d if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| calls", [x[0] for x in KG["calls"]])
    return c, d
def krp(tag, payload, keys=None, raw=False):
    body = payload if raw else json.dumps(payload).encode("utf-8")
    r = ns["_route"]("POST", "/kerning/groups", body); h, _, b = r.partition(b"\r\n\r\n")
    c, d = h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
    shown = d if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| calls", [x[0] for x in KG["calls"]])
    return c, d
_KRG = ("groups", "glyphs", "errors", "member_names")
kr_setup(); krc("2610 GET all                      ", "/kerning/groups?all=yes")
kr_setup(); krc("2611 GET named groups, unknown    ", "/kerning/groups?groups=kgtL,kgtX,kgtF", keys=_KRG)
kr_setup(); krc("2612 GET glyphs                   ", "/kerning/groups?glyphs=kgt5,kgt7,Q", keys=_KRG)
kr_setup(); krc("2613 GET both, duplicates folded  ", "/kerning/groups?groups=kgtR,kgtR&glyphs=kgt1", keys=_KRG + ("mode",))
kr_setup(); krp("2614 POST named                   ", {"groups": ["kgtB"], "glyphs": ["kgt3"]}, keys=_KRG + ("mode", "cross_check"))
kr_setup(); krp("2614b POST all                    ", {"all_groups": True}, keys=("mode", "group_count", "member_names", "errors"))
for _tag, _q in (("2615 no names                     ", "/kerning/groups"), ("2615b all with names             ", "/kerning/groups?all=yes&groups=kgtL"),
                 ("2615c all=no                      ", "/kerning/groups?all=no"), ("2615d confirmed=1               ", "/kerning/groups?all=yes&confirmed=1"),
                 ("2615e bad name                    ", "/kerning/groups?groups=kgt%20L"), ("2615f 64 characters             ", "/kerning/groups?glyphs=" + "x" * 64)):
    kr_setup(); krc(_tag, _q)
for _tag, _p in (("2616 POST extra key               ", {"groups": ["kgtL"], "evil": 1}), ("2616b POST not an object         ", ["kgtL"]),
                 ("2616c POST groups a string        ", {"groups": "kgtL"}), ("2616d POST all_groups 1           ", {"all_groups": 1}),
                 ("2616e POST confirmed 'yes'        ", {"all_groups": True, "confirmed_large_read": "yes"}), ("2616f POST a name not text       ", {"glyphs": [5]}),
                 ("2616g POST empty object           ", {})):
    kr_setup(); krp(_tag, _p)
kr_setup(); krp("2616h POST invalid JSON           ", b"{nope", raw=True)
kr_setup(); krp("2616i POST not UTF-8              ", b'{"groups": ["\xff"]}', raw=True)
# the cross-check
kr_setup(getall=[(True, "kgtL", 5121, 0, ["kgt2", "kgt1"]), (True, "kgtR", 5122, 0, ["kgt3"]), (True, "kgtZ", 9, 0, ["kgt8"])])
krc("2617 members differ, order aside, list-only group", "/kerning/groups?all=yes", keys=("groups", "group_count", "member_names"))
kr_setup(getall=RuntimeError("list boom")); krc("2618 class list fails           ", "/kerning/groups?groups=kgtL&glyphs=kgt1", keys=("cross_check",) + _KRG)
kr_setup(getall_attr=5); krc("2618b class list not callable   ", "/kerning/groups?groups=kgtL", keys=("cross_check", "groups"))
kr_setup(getall=KGSpy("allresult", (), {}, 3)); krc("2618c class list not a list    ", "/kerning/groups?groups=kgtL", keys=("cross_check", "groups"))
kr_setup(getall=[(True, "kgtL", 5121, 0, ["kgt1", "kgt2"]), (True, "kgtL", 5130, 0, ["kgt1", "kgt2"]), (True, "kgtR", "x", 0, KGSpy("m", (), {})),
                 "junk", (True, 7, 1, 0, []), (True, "kgtB", 5123, 0, ["kgt5", "kgt6"])])
krc("2619 class list oddities        ", "/kerning/groups?all=yes", keys=("groups", "duplicate_names"))
kr_setup(items=lambda: [("kgtL", (["kgt1", "kgt2"], "KernTop")), ("kgtL", (["kgt1", "kgt2"], "KernLeft")), ("kgtB", ["kgt5"]), "junk",
                        ("kgtR", (["kgt3", KGSpy("m", (), {})], "KernRight")), ("kgtR", (["kgt3"], 5)), _KGTuple(("kgtX", (["a"], "KernLeft"))),
                        ("kgtB", (_KGList(["kgt5"]), "KernBothSide"))])
krc("2620 items oddities             ", "/kerning/groups?all=yes", keys=("groups", "group_count", "malformed_entries", "duplicate_names"))
kr_setup(items=lambda: [("kgtL", KGSpy("pair", (), {}, 2)), ("kgtB", _KGTuple((["kgt5", "kgt6"], "KernBothSide"))), ("kgtR", (["kgt3", "kgt4"], "KernRight"))],
         getall=[(True, "kgtL", 5121, 0), (True, "kgtB", 5123, 0, ["kgt5", "kgt6"], "x"), (True, "kgtR", 5122, 0, ["kgt3", "kgt4"])])
krc("2620c a native pair, a tuple subclass, entries of 4 and 6", "/kerning/groups?all=yes", keys=("groups", "group_count", "malformed_entries"))
kr_setup(items=lambda: [("kgtL", (["kgt1", "kgt2"], "KernTop"))], getall=[(True, "kgtL", 5121, 0, ["kgt1", "kgt2"])])
krc("2620b an unknown side           ", "/kerning/groups?groups=kgtL&glyphs=kgt1", keys=_KRG)
# items() failures: the whole read refused, with the sizes
kr_setup(items=RuntimeError("items boom")); krc("2621 items raises               ", "/kerning/groups?groups=kgtL")
kr_setup(items_attr=5); krc("2621b items not callable        ", "/kerning/groups?groups=kgtL", keys=("error",))
kr_setup(items=lambda: KGSpy("itemsresult", (), {}, 3)); krc("2621c items not a list          ", "/kerning/groups?groups=kgtL", keys=("error",))
kr_setup(items=lambda: _KGList(_KR_ITEMS)); krc("2621d items a list subclass     ", "/kerning/groups?groups=kgtL", keys=("error",))
kr_setup(groups=RuntimeError("groups boom")); krc("2622 groups attribute raises    ", "/kerning/groups?groups=kgtL", keys=("error",))
kr_setup(groups=_kg_track("groups()", [])); krc("2622b groups attribute callable ", "/kerning/groups?groups=kgtL", keys=("error",))
kr_setup(groups_len_after=4); krc("2623 groups size changes        ", "/kerning/groups?groups=kgtL", keys=("side_effect_detected", "table_size"))
kr_setup(kerning_len_after=1); krc("2623b table size changes        ", "/kerning/groups?groups=kgtL", keys=("side_effect_detected", "table_size"))
kr_setup(groups_len=RuntimeError("len boom")); krc("2623c a size unreadable          ", "/kerning/groups?groups=kgtL", keys=("side_effect_detected",))
# empty, threshold
kr_setup(items=lambda: [], getall=[], groups_len=0); krc("2624 no groups at all           ", "/kerning/groups?all=yes", keys=("group_count", "groups", "member_names", "errors"))
kr_setup(items=lambda: [], getall=[], groups_len=0); krc("2624b no groups, a glyph         ", "/kerning/groups?glyphs=kgt1", keys=("glyphs",))
# v0.217: FontLab's class list is None when the font has no group at all (GL 1531, AG2 1927): an empty list, so the cross-check runs
kr_setup(items=lambda: [], getall=None, groups_len=0)
krc("2624c no group, list None, glyph", "/kerning/groups?glyphs=kgt1", keys=("cross_check", "group_count", "glyphs", "errors", "unconfirmed"))
kr_setup(items=lambda: [], getall=None, groups_len=0); krp("2624d no group, list None, all  ", {"all_groups": True}, keys=("mode", "cross_check", "group_count", "groups"))
kr_setup(getall=None); krc("2624e items has groups, list None", "/kerning/groups?groups=kgtL", keys=("cross_check", "groups", "unconfirmed"))
_kr251 = [("g%03d" % i, (["kgt1"], "KernLeft")) for i in range(251)]
_kr251all = [(True, "g%03d" % i, i, 0, ["kgt1"]) for i in range(251)]
kr_setup(items=lambda: list(_kr251), getall=list(_kr251all)); krc("2625 251 groups: confirmation    ", "/kerning/groups?all=yes", keys=("group_count", "needs_confirmation", "groups", "mode"))
kr_setup(items=lambda: list(_kr251), getall=list(_kr251all)); c, d = call("/kerning/groups?all=yes&confirmed=yes")
print("2625b 251 confirmed               :", c, len(d["groups"]), d["member_names"], d.get("needs_confirmation"), all(e["confirmed"] for e in d["groups"]))
kr_setup(items=lambda: _kr251[:250], getall=_kr251all[:250]); c, d = call("/kerning/groups?all=yes")
print("2625c exactly 250, no flag        :", c, len(d["groups"]), d.get("needs_confirmation"))
kr_setup(items=lambda: list(_kr251), getall=list(_kr251all)); c, d = call("/kerning/groups?glyphs=kgt1")
print("2625d named: no threshold here    :", c, len(d["glyphs"][0]["kerning_groups"]), d.get("needs_confirmation"))
# fonts and gates
for _tag, _over in (("2626 no font open                ", dict(count=0)), ("2626b CurrentFont None          ", dict(cur="none")),
                    ("2626c two fonts, paths agree     ", dict(count=2)), ("2626d two fonts, paths differ    ", dict(count=2, pkg_path="C:/x/other.vfc")),
                    ("2626e two fonts, unsaved         ", dict(count=2, font_path="", pkg_path="")), ("2626f two packages, one font    ", dict(packages=2))):
    kr_setup(**_over); krc(_tag, "/kerning/groups?groups=kgtL", keys=("open", "error", "fonts_open", "matched_by", "groups"))
kr_setup(masters=["Regular", "Bold"]); krc("2627 two masters                ", "/kerning/groups?groups=kgtL", keys=("master", "master_count"))
kr_setup(glyph_names=["kgt1", "kgt1", "kgt2"]); krc("2627b a glyph name twice         ", "/kerning/groups?glyphs=kgt1", keys=("glyphs",))
kr_setup(); _kr_real = ns["get_kerning_groups"]
ns["get_kerning_groups"] = lambda *a: (_ for _ in ()).throw(RuntimeError("route boom")); krc("2628 function raises: HTTP 500  ", "/kerning/groups?groups=kgtL")
krp("2628b POST function raises: 500 ", {"groups": ["kgtL"]}); ns["get_kerning_groups"] = _kr_real
for _tag, _args in (("2629 direct: all_groups 'yes'    ", (None, None, "yes", False)), ("2629b direct: groups a string    ", ("kgtL", None, False, False)),
                    ("2629c direct: native list        ", (KGSpy("names", (), {}), None, False, False))):
    kr_setup(); print(_tag, ":", ns["get_kerning_groups"](*_args), "| calls", KG["calls"])
kr_setup()
for _p in ("/kerning/groups?all=yes", "/kerning/groups?groups=kgtL,kgtF&glyphs=kgt5"): call(_p)
print("2630 spy over the route cases     : forbidden:", KG["forbidden"], "| members touched anywhere:", sorted(KG["all"]))
_rag_src = src[src.index("def _read_all_groups("):src.index("def _kern_group_names(")]   # v0.217: the shared getAllGroups() reader is scanned with each caller
_kr_src = src[src.index("# /kerning/groups (v0.190, P1.6)"):src.index("def _other_glyphs_with_unicode")] + _rag_src
_kr_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _kr_src).splitlines())
print("2631 static scan                  : method calls:", sorted(set(_re83.findall(r"\b(\w+\.\w+)\(", _kr_code))),
      "| forbidden members:", _re83.findall(r"\.(?:keys|values|asDict|has_key|clear|remove|rename|set|save\w*|update|addGroup|deleteGroup\w*|autoKern)\b",
                                            _kr_code.replace("out.update(", "").replace("entry.update(", "")),
      "| items( / getter( calls:", [len(_re83.findall(r"\b" + f + r"\(", _kr_code)) for f in ("items_of", "getter")],
      "| subscripts:", sorted(set(_re83.findall(r"\b(\w+)\[", _kr_code))), "| scanned chars > 5000:", len(_kr_src) > 5000)
print("2632 route, docstring, activity    :", src.count('path == "/kerning/groups"') == 2, "/kerning/groups" in src[:src.index('"""', 3)],
      ns["_ACT_READS"].get("/kerning/groups"), "| threshold", ns["_KGR_CONFIRM_ABOVE"], "| sides", ns["_KGR_SIDES"])
for _m, _a, _v in _kg_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYKERNGROUPS"]["calls"] = 0

# ---- v0.103 (continued): /debug/trypkgkern mode=flags, a side flagged T may name a class (R2).
print("\n==== v0.103 /debug/trypkgkern class names on T sides ====")
_PK_GET_SAVED = PKKern.get
_PK_CLASS_VALUES = {(("kn1L", False), ("kn1grp", True)): -50.0, (("kn1L", True), ("kn1grp", True)): -100.0}
def _pk_get_with_classes(self, pair):
    PK["gets"].append((self._label, type(pair).__name__, tuple(pair)))
    self._got = True
    return _PK_CLASS_VALUES.get(tuple(pair), self._values.get(tuple(pair)))
PKKern.get = _pk_get_with_classes
_PCQ = "/debug/trypkgkern?go=yes&mode=flags"
pk_setup(); pfc("1411 FT, b is a class name        ", _PCQ + "&flags=FT&a=kn1L&b=kn1grp", keys=("flags", "package", "legacy", "class_names_not_checked", "error"))
pk_setup(); pfc("1412 TT, both class names         ", _PCQ + "&flags=TT&a=kn1L&b=kn1grp", keys=("flags", "package", "class_names_not_checked"))
pk_setup(); pfc("1413 TF, a is a class name        ", _PCQ + "&flags=TF&a=kn1grp&b=kn1R", keys=("flags", "package", "class_names_not_checked"))
pk_setup(); pfc("1414 FF, b is no glyph: refused   ", _PCQ + "&flags=FF&a=kn1L&b=kn1grp", keys=("error", "calls_so_far"))
pk_setup(); pfc("1415 tuple, b is no glyph: refused", "/debug/trypkgkern?go=yes&a=kn1L&b=kn1grp", keys=("error", "calls_so_far"))
pk_setup(); pfc("1416 FT, a unknown: only a named  ", _PCQ + "&flags=FT&a=Q&b=kn1grp", keys=("error", "calls_so_far"))
pk_setup(); pfc("1417 FT, b is a glyph: still noted", _PCQ + "&flags=FT&a=kn1L&b=kn1R", keys=("package", "class_names_not_checked"))
pk_setup(); pfc("1418 FF, both glyphs: no new field", _PCQ + "&flags=FF&a=kn1L&b=kn1R", keys=("package", "class_names_not_checked"))
pk_setup(); pfc("1419 TT, bad class name refused   ", _PCQ + "&flags=TT&a=kn1L&b=kn1%20grp", keys=("error", "calls_so_far"))
PKKern.get = _PK_GET_SAVED
for _m, _a, _v in _pk_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYPKGKERN"]["calls"] = 0

# ================= v0.105: "no font open" is CountFonts() == 0 on every product route (P0.2); the client name in the activity log =================
print("\n==== v0.105 no font open on every product route ====")
NF = {"cur_calls": 0, "touched": []}
class NFPlaceholder:
    """FontLab's placeholder font when no font is open: any use is recorded and refused."""
    def __getattr__(self, n):
        NF["touched"].append(n); raise RuntimeError("placeholder font touched: " + n)
def _nf_cur():
    NF["cur_calls"] += 1
    return NFPlaceholder()
_nf_saved = [(a, getattr(fl, a, None)) for a in ("CountFonts", "CurrentFont")]
def nf_setup(count=0):
    NF["cur_calls"] = 0; NF["touched"].clear()
    fl.CurrentFont = _nf_cur
    if count == "missing":
        if hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
    elif isinstance(count, Exception):
        def _boom(): raise count
        fl.CountFonts = _boom
    else:
        fl.CountFonts = count if count == "not callable" else (lambda: count)
def nf_restore():
    for a, v in _nf_saved:
        if v is None:
            if hasattr(fl, a): delattr(fl, a)
        else: setattr(fl, a, v)
def nf_post(path, payload):
    r = ns["_route"]("POST", path, json.dumps(payload).encode())
    h, _, b = r.partition(b"\r\n\r\n")
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
NF_GETS = ("/font/current", "/font/glyphs", "/font/nonempty", "/font/notdef", "/glyph/outline?name=A", "/glyph/width?name=A",
           "/glyph/sidebearings?name=A", "/glyph/unicode?name=A", "/glyph/nodes?name=A", "/kerning/pairs?pairs=A:V")
NF_POSTS = (("/glyph/create", {"name": "kn5A"}), ("/glyph/delete", {"name": "A"}), ("/glyph/width", {"name": "A", "width": 600}),
            ("/glyph/sidebearings", {"name": "A", "left": 10, "right": 10}), ("/glyph/unicode", {"name": "A", "unicode": 66}),
            ("/glyph/polygon", {"name": "A", "points": [[0, 0], [100, 0], [0, 100]]}),
            ("/glyph/path", {"name": "A", "contours": [[{"x": 0, "y": 0}, {"x": 100, "y": 0}, {"x": 0, "y": 100}]]}),
            ("/font/notdef/warn", {}))
for p in NF_GETS:
    nf_setup(0); c, d = call(p)
    print(f"1420 GET  {p:28}:", c, d, "| CurrentFont calls", NF["cur_calls"], "| placeholder touched", NF["touched"])
for p, body in NF_POSTS:
    nf_setup(0); c, d = nf_post(p, body)
    print(f"1421 POST {p:28}:", c, {k: d[k] for k in ("open", "set", "drawn", "created", "deleted") if k in d}, "| CurrentFont calls", NF["cur_calls"], "| placeholder touched", NF["touched"])
for tag, count in (("1 font", 1), ("2 fonts", 2), ("raises", RuntimeError("count boom")), ("True", True), ("'0'", "0"), ("0.0", 0.0),
                   ("None", None), ("missing", "missing"), ("not callable", "not callable")):
    nf_setup(count); got = ns["_open_font"]()
    print(f"1422 _open_font, CountFonts {tag:12}: font returned", isinstance(got, NFPlaceholder), "| CurrentFont calls", NF["cur_calls"])
nf_setup(0); print("1423 _open_font, CountFonts 0           : None", ns["_open_font"]() is None, "| CurrentFont calls", NF["cur_calls"])
nf_setup(1); c, d = call("/font/current"); print("1424 one font: the font is used          :", c, "| touched", NF["touched"][:2])
nf_restore()

print("\n==== v0.105 activity log: client name, no font open ====")
_nl_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
def nl(method, path, body, code, reply, client=None):
    raw = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body or b"")
    ns["_activity_note"](method, path, raw, ns["_build_response"](code, reply), client)
CREATED = {"open": True, "created": True, "before_count": 3, "after_count": 4}
al_reset(); al_case("1425 one change each from: claude-code, a percent-encoded UTF-8 name, control characters, a 60-character name:")
nl("POST", "/glyph/create", {"name": "kn5B"}, 200, CREATED, "claude-code")
nl("POST", "/glyph/create", {"name": "kn5C"}, 200, CREATED, "Test%20App%20%C3%A9")
nl("POST", "/glyph/create", {"name": "kn5D"}, 200, CREATED, "a%0Ab%09c%7Fd%20%20e")
nl("POST", "/glyph/create", {"name": "kn5E"}, 200, CREATED, "x" * 60)
al_reset(); al_case("1426 no name, an empty name, only spaces, broken percent-encoding, not text:")
for raw in (None, "", "%20%20", "bad%ZZname", 5):
    nl("POST", "/glyph/create", {"name": "kn5F"}, 200, CREATED, raw)
print("1426b broken UTF-8 becomes U+FFFD (escaped here):", ascii(ns["_act_client"]("ab%C3")))
al_reset(); al_case("1427 two clients take turns: the summary is printed when the client changes, never mixed:")
nl("GET", "/glyph/outline?name=A", None, 200, {"open": True}, "claude-code")
nl("GET", "/glyph/width?name=A", None, 200, {"open": True}, "claude-code")
nl("GET", "/glyph/outline?name=B", None, 200, {"open": True}, "claude-ai")
al_tick(10); print("1427 client kept after the idle summary:", ns["_ACT"]["client"])
al_reset(); al_case("1428 a run of widths is cut when another client writes:")
for g in "ABCDE":
    nl("POST", "/glyph/width", {"name": g, "width": 600}, 200, dict(OK_W, name=g), "claude-code")
nl("POST", "/glyph/width", {"name": "F", "width": 600}, 200, dict(OK_W, name="F"), "claude-ai")
al_tick(10)
al_reset(); al_case("1429 reads answered 'no font open' are listed apart (kerning adds no pairs):")
nl("GET", "/glyph/outline?name=A", None, 200, {"open": True}, "claude-code")
nl("GET", "/font/current", None, 200, {"open": False}, "claude-code")
nl("GET", "/glyph/width?name=A", None, 200, {"open": False}, "claude-code")
nl("GET", "/kerning/pairs?pairs=A:V", None, 200, {"open": False}, "claude-code")
nl("POST", "/kerning/pairs", {"pairs": [["A", "V"]]}, 200, {"open": False}, "claude-code")
nl("GET", "/kerning/pairs?pairs=T:o", None, 200, {"open": True, "count": 1}, "claude-code")
nl("GET", "/glyph/outline?name=Q", None, 500, {"error": "boom"}, "claude-code")
al_tick(10)
al_reset(); al_case("1430 only 'no font open' reads; a write refused for no font; a .notdef warning with no font:")
nl("GET", "/kerning/pairs?pairs=A:V", None, 200, {"open": False}, "claude-code")
nl("POST", "/glyph/width", {"name": "A", "width": 600}, 200, {"open": False}, "claude-code")
nl("POST", "/font/notdef/warn", {}, 200, {"open": False}, "claude-code")
al_tick(10)
al_reset(); al_case("1431 a long reply is not parsed for 'open' (a no-font reply is tiny); 'open' missing is a read:")
nl("GET", "/font/glyphs", None, 200, {"open": False, "names": ["g%04d" % i for i in range(1000)]}, "claude-code")
nl("GET", "/glyph/width?name=A", None, 200, {"width": 500}, "claude-code")
al_tick(10)
al_reset(); al_case("1432 end to end through _handle: the header names the client; no font open:")
nf_setup(0)
_nl_c = PLConn(b"GET /glyph/width?name=A HTTP/1.1\r\nX-Glyphbridge-Client: claude-code\r\n\r\n")
ns["_handle"](_nl_c); print("1432 reply:", pl_status(_nl_c), "| no_font", ns["_ACT"]["no_font"], "| client", ns["_ACT"]["client"], "| request client after", ns["_request_client"])
_nl_c = PLConn(b'POST /glyph/create HTTP/1.1\r\nx-glyphbridge-client: Test%20App\r\nContent-Length: 16\r\n\r\n{"name": "kn5G"}')
ns["_handle"](_nl_c); print("1432 reply:", pl_status(_nl_c), "| placeholder touched", NF["touched"])
al_tick(10)
nf_restore()
al_reset(); al_case("1433 the 'Connected' line names the client that sent the first /health, or says a local client:")
for raw in (b"X-Glyphbridge-Client: claude-code\r\n", b"", b"X-Glyphbridge-Client: %0A[evil]%0D\r\n"):
    ns["_connection_announced"] = False
    ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\n" + raw + b"\r\n"))
print("1433 request client after:", ns["_request_client"], "| announced", ns["_connection_announced"])
for k, v in _nl_saved.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"])

# ================= v0.106: the config entry name "glyphbridge-fontlab" is left out of the client name shown =================
print("\n==== v0.106 the shown client name leaves out glyphbridge-fontlab ====")
for raw in ("local-agent-mode-glyphbridge-fontlab", "Local-Agent-Mode-GlyphBridge-FontLab", "glyphbridge-fontlab", "glyphbridge-fontlab-beta",
            "a-glyphbridge-fontlab-b", "local-agent-mode_glyphbridge-fontlab", "x%20glyphbridge-fontlab", "claude-code", "glyphbridge --check",
            "glyphbridge", "glyphbridge-fontlab2", "y" * 50 + "-glyphbridge-fontlab"):
    print(f"1434 {raw[:44]!r:48}->", repr(ns["_act_client"](raw)))
_nl_saved6 = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
al_reset(); al_case("1435 the line live test 228 printed, as 0.106 prints it:")
ns["_activity_note"]("GET", "/kerning/pairs?pairs=A:V", b"", ns["_build_response"](200, {"open": True, "count": 13}), "local-agent-mode-glyphbridge-fontlab")
al_tick(10)
al_reset(); al_case("1436 the 'Connected' line with the same name:")
ns["_connection_announced"] = False
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\nX-Glyphbridge-Client: local-agent-mode-glyphbridge-fontlab\r\n\r\n"))
for k, v in _nl_saved6.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"])

# ================= v0.107: /debug/features (K11, gated research probe: font.features keys / has_key / get_feature; spies) =================
print("\n==== v0.107 /debug/features ====")
FT = {"touched": [], "forbidden": [], "calls": [], "keys": None, "has": True, "text": "", "len": 29, "len_after": None, "len_raises": False,
      "all_touched": set(), "cur_calls": 0}
_FT_FORBIDDEN = ("clear", "remove", "set_feature", "set_prefix", "get_prefix")
FT_TAGS = ["aalt", "c2sc", "case", "ccmp", "dlig", "dnom", "frac", "kern", "liga", "lnum", "locl", "mark", "mkmk", "numr", "onum",
           "ordn", "pnum", "salt", "sinf", "smcp", "ss01", "ss02", "subs", "sups", "tnum", "zero", "init", "medi", "fina"]
FT_TEXT = ("feature kern {\n  pos A V -152;\r\n  enum pos @Aring V -76;\n  # position comment\n  subpos x y 3;\n  lookup k1 {\n"
           "    pos T o -227;\n  } k1;\n} kern;\n")
class FTFeatures:
    def __getattribute__(self, n):
        if not n.startswith("__"):
            FT["touched"].append(n); FT["all_touched"].add(n)
            if n in _FT_FORBIDDEN:
                FT["forbidden"].append(n)
                raise SystemExit("FORBIDDEN features member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self):
        if FT["len_raises"]: raise RuntimeError("len boom")
        return FT["len_after"] if (FT["len_after"] is not None and FT["calls"]) else FT["len"]
    def keys(self):
        FT["calls"].append("keys")
        k = FT["keys"]
        if k == "raise": raise RuntimeError("keys boom")
        if k == "native": return FTNative()
        return list(FT_TAGS) if k is None else k
    def has_key(self, tag):
        FT["calls"].append(("has_key", tag))
        h = FT["has"]
        if h == "raise": raise RuntimeError("has_key boom")
        return h
    def get_feature(self, tag):
        FT["calls"].append(("get_feature", tag))
        t = FT["text"]
        if t == "raise": raise RuntimeError("get_feature boom")
        return t
    def clear(self): FT["calls"].append("clear")
    def remove(self, tag): FT["calls"].append("remove")
    def set_feature(self, tag, text): FT["calls"].append("set_feature")
    def set_prefix(self, text): FT["calls"].append("set_prefix")
    def get_prefix(self): FT["calls"].append("get_prefix"); return ""
class FTNative:
    """a native-like container: indexing or iterating it is a test failure"""
    def __getitem__(self, i): FT["forbidden"].append("native[]"); raise SystemExit("FORBIDDEN: native container indexed")
    def __iter__(self): FT["forbidden"].append("native iter"); raise SystemExit("FORBIDDEN: native container iterated")
    def __len__(self): return 29
class FTFont:
    features = FTFeatures()
def ft_setup(count=1, cur="font", keys=None, has=True, text=FT_TEXT, calls=0):
    FT["touched"].clear(); FT["forbidden"].clear(); FT["calls"].clear(); FT["keys"] = keys; FT["has"] = has; FT["text"] = text
    FT["len_after"] = None; FT["len_raises"] = False; FT["cur_calls"] = 0
    ns["_FEATURES"]["calls"] = calls
    def _cur():
        FT["cur_calls"] += 1
        return None if cur is None else FTFont()
    fl.CurrentFont = _cur
    if count == "missing":
        if hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
    elif isinstance(count, Exception):
        fl.CountFonts = lambda: (_ for _ in ()).throw(count)
    else:
        fl.CountFonts = lambda: count
def ftc(tag, path):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k not in ("note", "tags")}
    print(tag, ":", c, shown, "| tags", (len(d["tags"]), d["tags"][:3], d["tags"][-1:]) if isinstance(d.get("tags"), list) else None,
          "| touched", list(FT["touched"]), "| calls", list(FT["calls"]), "| forbidden", list(FT["forbidden"]))
    return c, d
_ft_cf = getattr(fl, "CountFonts", None); _ft_cur = fl.CurrentFont
ft_setup(); ftc("1440 no go: nothing runs          ", "/debug/features?stage=tags")
ft_setup(); ftc("1441 go=maybe: nothing runs       ", "/debug/features?stage=tags&go=maybe")
ft_setup(); ftc("1442 no stage                     ", "/debug/features?go=yes")
ft_setup(); ftc("1443 unknown stage                ", "/debug/features?stage=text&go=yes")
ft_setup(); ftc("1444 stage=tags takes no tag      ", "/debug/features?stage=tags&tag=kern&go=yes")
ft_setup(); ftc("1445 stage=size without tag       ", "/debug/features?stage=size&go=yes")
for bad in ("kerns", "ke%20n", "k%2Bn", "%C3%A9", "kern%00", "k_rn", "k.rn"):
    ft_setup(); ftc(f"1446 bad tag {bad!r:16}", "/debug/features?stage=size&tag=" + bad + "&go=yes")
ft_setup(); c, d = ftc("1447 tags: Arial-like, 29 tags    ", "/debug/features?stage=tags&go=yes")
print("1447b all tags, in order            :", d.get("tags") == FT_TAGS, "| has_key / get_feature untouched:", not any(n in FT["touched"] for n in ("has_key", "get_feature")), "| note present:", "note" in d)
ft_setup(); c, d = ftc("1448 size kern: the size only      ", "/debug/features?stage=size&tag=kern&go=yes")
_ft_vals = json.dumps(d)
print("1448b no text in the reply          :", "pos A V" not in _ft_vals and "feature kern" not in _ft_vals and "lookup" not in _ft_vals,
      "| chars", d.get("chars") == len(FT_TEXT), "| lines", d.get("lines") == len(FT_TEXT.splitlines()), "| pos_lines (pos, enum pos, pos in a lookup; not position / subpos):", d.get("pos_lines"))
ft_setup(); ftc("1449 size, tag not listed         ", "/debug/features?stage=size&tag=zzzz&go=yes")
ft_setup(); ftc("1449b size, case differs (Kern)    ", "/debug/features?stage=size&tag=Kern&go=yes")
ft_setup(has=False); ftc("1450 has_key False: no get_feature", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(has=1); ftc("1451 has_key 1 (not True)         ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(has=FTNative()); ftc("1451b has_key native object       ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(has="raise"); ftc("1452 has_key raises (counted)     ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(text="raise"); ftc("1453 get_feature raises           ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(text=None); ftc("1454 get_feature returns None     ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(text=b"pos A V -1;"); ftc("1454b get_feature returns bytes   ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(text=""); ftc("1454c get_feature returns ''      ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(keys="native"); ftc("1455 keys native: nothing read     ", "/debug/features?stage=tags&go=yes")
ft_setup(keys="native"); ftc("1455b keys native, size stage     ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(keys=["kern", 5]); ftc("1456 keys with a non-text entry   ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(keys="raise"); ftc("1457 keys raises (counted)        ", "/debug/features?stage=tags&go=yes")
ft_setup(keys=("kern", "kern", "x" * 40)); ftc("1458 tuple, duplicate, long tag cut", "/debug/features?stage=tags&go=yes")
ft_setup(keys=[f"t{i:03d}" for i in range(130)]); ftc("1458b 130 tags: 100 shown, cut   ", "/debug/features?stage=tags&go=yes")
ft_setup(keys=[]); ftc("1458c no tags at all              ", "/debug/features?stage=tags&go=yes")
ft_setup(); FT["len_after"] = 28; ftc("1459 length changes: side effect ", "/debug/features?stage=size&tag=kern&go=yes")
ft_setup(); FT["len_raises"] = True; ftc("1459b len() raises               ", "/debug/features?stage=tags&go=yes")
ft_setup(count=0); ftc("1460 CountFonts 0: not open       ", "/debug/features?stage=tags&go=yes")
print("1460b CurrentFont never asked      :", FT["cur_calls"] == 0)
for cnt, lbl in ((2, "two fonts"), (RuntimeError("count boom"), "CountFonts raises"), (True, "CountFonts True"), ("1", "CountFonts '1'"), ("missing", "no CountFonts")):
    ft_setup(count=cnt); ftc(f"1460c {lbl:27}", "/debug/features?stage=tags&go=yes"); print("      CurrentFont asked:", FT["cur_calls"])
ft_setup(cur=None); ftc("1461 CurrentFont None            ", "/debug/features?stage=tags&go=yes")
ft_setup(calls=9); ftc("1462 request number 10 allowed    ", "/debug/features?stage=tags&go=yes")
ftc("1462b request number 11 refused   ", "/debug/features?stage=size&tag=kern&go=yes")
class FTNoFeatures:
    @property
    def features(self): raise RuntimeError("no features")
class FTBadKeys:
    class _F:
        keys = 5
    features = _F()
class FTBadHas:
    class _F:
        def keys(self): FT["calls"].append("keys"); return ["kern"]
        has_key = "x"
        def get_feature(self, tag): FT["calls"].append("get_feature"); return ""
    features = _F()
class FTNoHas:
    class _F:
        def keys(self): FT["calls"].append("keys"); return ["kern"]
    features = _F()
for tag, fnt, path in (("1463 font.features raises", FTNoFeatures, "stage=tags"), ("1463b keys not callable", FTBadKeys, "stage=tags"),
                       ("1463c has_key not callable", FTBadHas, "stage=size&tag=kern"), ("1463d no has_key member", FTNoHas, "stage=size&tag=kern")):
    ft_setup(); fl.CurrentFont = (lambda f=fnt: f()); ftc(tag.ljust(34), "/debug/features?" + path + "&go=yes"); print("      calls so far:", ns["_FEATURES"]["calls"])
ft_setup(); _ft_real = ns["debug_features"]
def _ft_boom(stage, tag, go, contains=()): raise RuntimeError("probe boom")
ns["debug_features"] = _ft_boom; ftc("1464 probe raises: HTTP 500      ", "/debug/features?stage=tags&go=yes"); ns["debug_features"] = _ft_real
print("1465 spy over all cases            : forbidden members touched:", FT["forbidden"], "| every member touched anywhere:", sorted(FT["all_touched"]))
_ft_src = src[src.index("def debug_features("):src.index("# /debug/trypkgkern (v0.97)")]
_ft_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _ft_src).splitlines())
print("1466 static scan                   : features members used:", sorted(set(_re83.findall(r"features\.(\w+)", _ft_code))),
      "| calls of the native getters:", sorted(set(_re83.findall(r"\b(keys_of|has_of|get_of)\(", _ft_code))),
      "| forbidden syntax:", _re83.findall(r"(?<!out)\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|set\w*|add\w*|clear\w*|append|values|items|"
                                           r"assign\w*|replace\w*|delete\w*|get_prefix|rename\w*)\(", _ft_code),
      "| subscripts:", sorted(set(s for s in _re83.findall(r"\b(\w+)\[", _ft_code) if s not in ("_FEATURES", "out"))),
      "| counter raised before the first call:", _ft_code.index('_FEATURES[""] += 1') < _ft_code.index("keys_of()"), "| scanned chars > 3000:", len(_ft_src) > 3000)
print("1467 gate, cap, route, header      :", "go != \"yes\"" in _ft_src, "| max", ns["_FEATURES_MAX"], "| route registered once:", src.count('path == "/debug/features"') == 1,
      "| in the route list:", "/debug/features       stage=tags" in src[:src.index('"""', 10)])
_ft_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
al_reset(); al_case("1468 activity log: a go=yes request is one probe line, a refusal without go is a read-only probe:")
ns["_activity_note"]("GET", "/debug/features?stage=tags&go=yes", b"", ns["_build_response"](200, {"open": True, "tags_count": 29}), "claude-code")
ns["_activity_note"]("GET", "/debug/features?stage=size&tag=zzzz&go=yes", b"", ns["_build_response"](200, {"open": True, "error": "'zzzz' is not one of the tags"}), "claude-code")
ns["_activity_note"]("GET", "/debug/features?stage=tags", b"", ns["_build_response"](200, {"error": "add &go=yes"}), "claude-code")
al_tick(10)
for k, v in _ft_saved.items(): ns[k] = v
al_reset(_al_saved["_ACTIVITY_LOG"])

# ================= v0.108: /debug/features stage=shape (line counts by kind, the head) and stage=lines (lines naming a token) =================
print("\n==== v0.108 /debug/features shape and lines ====")
FT_TEXT2 = ("# kern feature, generated\nlanguagesystem DFLT dflt;\nfeature kern {\n  script latn;\n  language dflt;\n  lookupflag IgnoreMarks;\n"
            "  lookup kern1 {\n    pos A V -152;\r\n    pos Aacute V -10;\n    enum pos @Aring V -76;\n    pos @T_left o -227;\n    subtable;\n"
            "    pos [A Aacute] Vacute -5;\n  } kern1;\n  @kclass = [A B];\n  @k.c-2=[C];\n  pos V.sc A -3;\n  pos AV A 1;\n  pos A @V -9;\n"
            "  pos V " + "x" * 300 + ";\n" + "".join(f"  pos Q{i} V {i};\n" for i in range(25)) + "  lookup kern1;\n  enumpos X Y 1;\n} kern;\n")
def ftl(tag, path):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k not in ("note", "tags", "head", "matches")}
    print(tag, ":", c, shown, "| head", (len(d["head"]), d["head"] == FT["text"][:300]) if isinstance(d.get("head"), str) else None,
          "| calls", list(FT["calls"]), "| forbidden", list(FT["forbidden"]))
    for tok, segs in (d.get("matches") or {}).items():
        print("      ", repr(tok), len(segs), "lines; lengths", [len(s) for s in segs][:8], "| first:", (segs[0][:60] if segs else None), "| last:", (segs[-1][:60] if segs else None),
              "| cut flagged:", sum(1 for s in segs if s.endswith("...[cut]")))
    return c, d
ft_setup(text=FT_TEXT2); c, d = ftl("1470 shape: kinds and head        ", "/debug/features?stage=shape&tag=kern&go=yes")
print("1470b head is the first 300 chars   :", d.get("head") == FT_TEXT2[:300], "| no matches key:", "matches" not in d, "| reply shorter than the text:", len(json.dumps(d)) < len(FT_TEXT2))
ft_setup(text=FT_TEXT2); ftl("1471 shape with contains refused  ", "/debug/features?stage=shape&tag=kern&contains=V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1472 size with contains refused   ", "/debug/features?stage=size&tag=kern&contains=V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1472b tags with contains refused  ", "/debug/features?stage=tags&contains=V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1473 lines without contains       ", "/debug/features?stage=lines&tag=kern&go=yes")
ft_setup(text=FT_TEXT2); ftl("1473b lines, empty contains       ", "/debug/features?stage=lines&tag=kern&contains=,%20,&go=yes")
ft_setup(text=FT_TEXT2); ftl("1473c lines without tag           ", "/debug/features?stage=lines&contains=V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1474 four names refused           ", "/debug/features?stage=lines&tag=kern&contains=A,B,C,D&go=yes")
for bad in ("a%20b", "x/y", "A(", "A%3Bb", "%C3%A9", "x" * 64, "A%00"):
    ft_setup(text=FT_TEXT2); ftl(f"1474b bad name {bad[:12]!r:14}", "/debug/features?stage=lines&tag=kern&contains=" + bad + "&go=yes")
ft_setup(text=FT_TEXT2); c, d = ftl("1475 lines V: whole word only      ", "/debug/features?stage=lines&tag=kern&contains=V&go=yes")
print("1475b V matched in                  :", [s[:24] for s in d["matches"]["V"][:5]], "| never V.sc / AV / @V / Vacute alone:",
      not any(s.startswith(("pos V.sc", "pos AV ", "pos A @V", "pos [A Aacute] Vacute")) for s in d["matches"]["V"]), "| 63 chars + 300 x cut to 200 + marker:", len(d["matches"]["V"][3]))
ft_setup(text=FT_TEXT2); ftl("1476 names with @, dot, dash      ", "/debug/features?stage=lines&tag=kern&contains=Aacute,@Aring,@V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1476b class names as defined       ", "/debug/features?stage=lines&tag=kern&contains=@kclass,@k.c-2,V.sc&go=yes")
ft_setup(text=FT_TEXT2); ftl("1477 name not present             ", "/debug/features?stage=lines&tag=kern&contains=Zzz&go=yes")
ft_setup(text=FT_TEXT2); ftl("1477b spaces around names trimmed ", "/debug/features?stage=lines&tag=kern&contains=%20A%20,%20o&go=yes")
ft_setup(text=FT_TEXT2); ftl("1478 lines, tag not listed        ", "/debug/features?stage=lines&tag=zzzz&contains=V&go=yes")
ft_setup(text=None); ftl("1479 lines, get_feature None       ", "/debug/features?stage=lines&tag=kern&contains=V&go=yes")
ft_setup(text=""); ftl("1479b lines, empty text           ", "/debug/features?stage=lines&tag=kern&contains=V&go=yes")
ft_setup(text=""); ftl("1479c shape, empty text           ", "/debug/features?stage=shape&tag=kern&go=yes")
ft_setup(text=FT_TEXT2, has=False); ftl("1479d shape, has_key False       ", "/debug/features?stage=shape&tag=kern&go=yes")
ft_setup(text=FT_TEXT2, calls=9); ftl("1480 shape is request 10          ", "/debug/features?stage=shape&tag=kern&go=yes")
ftl("1480b lines is request 11: refused", "/debug/features?stage=lines&tag=kern&contains=V&go=yes")
ft_setup(text=FT_TEXT2, count=2); ftl("1481 lines, two fonts             ", "/debug/features?stage=lines&tag=kern&contains=V&go=yes")
ft_setup(text=FT_TEXT2); ftl("1482 lines without go             ", "/debug/features?stage=lines&tag=kern&contains=V")
print("1483 report helper on its own      :", ns["_features_text_report"]("pos A V 1;\npos A B 2;", "size", ["A"]),
      "| unknown stage gives the size only:", ns["_features_text_report"]("pos A V 1;", "other", ["A"]))
_ft2_src = src[src.index("def _features_text_report("):src.index("# /debug/trypkgkern (v0.97)")]
_ft2_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _ft2_src).splitlines())
print("1484 static scan of the helper     : method calls:", sorted(set(_re83.findall(r"\b(\w+\.\w+)\(", _ft2_code))),
      "| subscripts:", sorted(set(_re83.findall(r"\b(\w+)\[", _ft2_code))), "| scanned chars > 1000:", len(_ft2_src) > 1000)
print("1485 spy over all cases            : forbidden members touched:", FT["forbidden"], "| every member touched anywhere:", sorted(FT["all_touched"]))
fl.CurrentFont = _ft_cur
if _ft_cf is not None: fl.CountFonts = _ft_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
ns["_FEATURES"]["calls"] = 0

# ================= v0.109 / v0.110: no guessed client name; the launcher name (X-Glyphbridge-Launcher) in one line per new pair =================
print("\n==== v0.109 / v0.110 launcher name, no guessed client name ====")
_lc_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"], ns["_clock"] = (lambda: "12:00:00"), (lambda: AL_CLOCK[0])
def lc(path, reply, client=None, launcher=None, method="GET", code=200, body=b""):
    ns["_activity_note"](method, path, body, ns["_build_response"](code, reply), client, launcher)
def lc_fresh():
    ns["_announced_clients"].clear(); ns["_connection_announced"] = False; al_reset()
LC_CODE = "claude.exe"
LC_CHAT = "powershell.exe"
LC_NAME = "local-agent-mode-glyphbridge-fontlab"
for raw in (LC_CODE, "Claude.EXE", "Claude", "x.exe.exe", "node", "%C3%A9.exe", "stra%C3%9Fe", ".exe", " .exe", "app .exe", "exe",
            "claude.exe%20%3C%20explorer.exe", "claude.exe < explorer.exe", "%20%3C%20b.exe", "a%0Ab%09c%7Fd%20%20e", "z" * 100, "", "%20%20", None, 5,
            "bad%ZZname"):
    print(f"1490 launcher {str(raw)[:40]!r:44}->", repr(ns["_act_launcher"](raw)))
print("1490b broken UTF-8 becomes U+FFFD (escaped here):", ascii(ns["_act_launcher"]("ab%C3")))
lc_fresh(); al_case("1491 the first /health names client and launcher in 'Connected'; that pair gets no second line:")
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\nX-Glyphbridge-Client: " + LC_NAME.encode() + b"\r\nX-Glyphbridge-Launcher: " + LC_CODE.encode() + b"\r\n\r\n"))
lc("/font/current", {"open": True}, LC_NAME, LC_CODE)
print("1491 pairs:", sorted(ns["_announced_clients"]), "| request launcher after:", ns["_request_launcher"])
al_case("1491b a later request through _handle with a new launcher gets its 'New client' line:")
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\nX-Glyphbridge-Client: " + LC_NAME.encode() + b"\r\nX-Glyphbridge-Launcher: bash.exe\r\n\r\n"))
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\nX-Glyphbridge-Client: " + LC_NAME.encode() + b"\r\nX-Glyphbridge-Launcher: bash.exe\r\n\r\n"))
al_case("1492 the same name from another launcher: pending reads first, then one 'New client' line, never twice:")
lc("/glyph/width?name=A", {"open": True}, LC_NAME, LC_CHAT)
lc("/glyph/width?name=B", {"open": True}, LC_NAME, LC_CHAT)
lc("/glyph/width?name=C", {"open": True}, LC_NAME, LC_CODE)
al_tick(10)
lc_fresh(); al_case("1493 a launcher without a client name; then no launcher at all (curl, PowerShell): no line, prefix [Glyphbridge]:")
lc("/font/current", {"open": True}, None, LC_CHAT)
lc("/font/current", {"open": True}, None, None)
lc("/font/current", {"open": True}, "", "%20")
al_tick(10)
print("1493 pairs:", sorted(ns["_announced_clients"], key=str))
lc_fresh(); al_case("1494 a change from a client without a name has the [Glyphbridge] prefix:")
lc("/glyph/create", {"open": True, "created": True, "before_count": 3, "after_count": 4}, None, None, "POST", body=b'{"name": "lc1A"}')
lc_fresh(); al_case("1495 log mode off: the 'New client' line is still printed, nothing else:")
al_reset("off")
lc("/glyph/create", {"open": True, "created": True, "before_count": 3, "after_count": 4}, LC_NAME, LC_CODE, "POST", body=b'{"name": "lc1B"}')
lc("/font/current", {"open": True}, LC_NAME, LC_CODE)
al_tick(10)
lc_fresh(); al_case("1496 'Connected' with a launcher but no client name; with neither:")
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\nX-Glyphbridge-Launcher: " + LC_CHAT.encode() + b"\r\n\r\n"))
ns["_connection_announced"] = False
ns["_handle"](PLConn(b"GET /health HTTP/1.1\r\n\r\n"))
print("1496 pairs:", sorted(ns["_announced_clients"], key=str))
lc_fresh(); al_case("1497 an evil launcher value is one clean line; a long one is cut at 40 characters:")
lc("/font/current", {"open": True}, "claude-code", "x.exe%0A%5Bglyphbridge%5D%20fake%0D")
lc("/font/current", {"open": True}, "claude-code", "y" * 120)
print("1498 start() clears the pairs:", "_announced_clients.clear()" in src[src.index("def start("):],
      "| _handle resets the request launcher:", "_request_client = _request_launcher = None" in src[src.index("def _handle("):src.index("def _poll(")])
print("1499 .notdef notes end (v0.203: OUTPUT lines, no dialog):", [t[-40:] for t in ns["_NOTDEF_OUTPUT"].values()],
      "| 'AI agent' in the source:", "an AI agent read" in src)
for k, v in _lc_saved.items(): ns[k] = v
ns["_announced_clients"].clear(); ns["_connection_announced"] = False
al_reset(_al_saved["_ACTIVITY_LOG"])

from urllib.parse import unquote
# ================= v0.113: the font a request used, in three response headers =================
print("\n==== v0.113 font headers ====")
import hashlib as _hl113
_fh_saved = (fl.CurrentFont, getattr(fl, "CountFonts", None))
class FHInfo:
    def __init__(self, family, style): self._f, self._s = family, style
    @property
    def familyName(self):
        if isinstance(self._f, Exception): raise self._f
        return self._f
    @property
    def styleName(self):
        if isinstance(self._s, Exception): raise self._s
        return self._s
class FHFont:
    def __init__(self, family="Arial", style="Regular", path="C:/fonts/arial.vfc", info_raises=False):
        self._info, self._path, self._raise = FHInfo(family, style), path, info_raises
        self.glyphs = []
    @property
    def info(self):
        if self._raise: raise RuntimeError("info boom")
        return self._info
    @property
    def path(self):
        if isinstance(self._path, Exception): raise self._path
        return self._path
def fh_setup(font, count=1):
    fl.CurrentFont = lambda: font
    fl.CountFonts = (lambda: count) if count != "missing" else None
    if count == "missing": del fl.CountFonts
def fh_head(method, path, body=b""):
    raw = ns["_route"](method, path, body) if method == "GET" else ns["_route"](method, path, body)
    head = raw.partition(b"\r\n\r\n")[0].decode("ascii")
    return {k: v for k, v in (l.split(": ", 1) for l in head.split("\r\n")[1:]) if k.startswith("X-Glyphbridge") and k != "X-Glyphbridge-Run"}, head   # v0.204: the run ID is random (tested in create_unicode 51t)
fh_setup(FHFont(), 1); h, head = fh_head("GET", "/font/current")
print("1510 one font, /font/current         :", h)
print("1510b key is sha1(path)[:12]           :", h.get("X-Glyphbridge-Font-Key") == _hl113.sha1(b"C:/fonts/arial.vfc").hexdigest()[:12], "| path not in the head:", "arial.vfc" not in head and "C:/fonts" not in head)
h, _ = fh_head("GET", "/version"); print("1511 /version after it: no font headers:", h)
h, _ = fh_head("GET", "/health"); print("1511b /health: no font headers         :", h)
fh_setup(FHFont("testfont", "Regular", "C:/fonts/savedtestfont.vfc"), 2); h, _ = fh_head("GET", "/glyph/width?name=A")
print("1512 two fonts, a width read (glyph missing):", h)
fh_setup(FHFont("Ünïcode Sans/Pro", "Bold\nItalic", "C:/fonts/u.vfc"), 3); h, _ = fh_head("GET", "/font/current")
print("1513 non-ASCII, a slash and a control character:", h, "| decodes to:", [unquote(x) for x in h["X-Glyphbridge-Font"].split("/")])
fh_setup(FHFont("F" * 150, "S", "C:/fonts/long.vfc"), 1); h, _ = fh_head("GET", "/font/current")
print("1514 a long family name is cut at 100   :", len(unquote(h["X-Glyphbridge-Font"].split("/")[0])))
for tag, path in (("empty path   ", ""), ("path None    ", None), ("path raises  ", RuntimeError("path boom")), ("path not text", 7)):
    fh_setup(FHFont("Unnamed", "Regular", path), 2); h, _ = fh_head("GET", "/font/current")
    print(f"1515 {tag}                     :", h)
fh_setup(FHFont(info_raises=True), 1); h, _ = fh_head("GET", "/font/current"); print("1516 font.info raises                  :", h)
fh_setup(FHFont(family=RuntimeError("family boom"), style=5), 1); h, _ = fh_head("GET", "/font/current"); print("1516b familyName raises, styleName a number:", h)
fh_setup(FHFont(), 0); h, _ = fh_head("GET", "/font/current"); print("1517 no font open (CountFonts 0)       :", h)
fh_setup(FHFont(), "missing"); h, _ = fh_head("GET", "/font/current"); print("1517b no CountFonts: no count header    :", h)
fh_setup(FHFont("Arial", "Regular", ":/Arial: Normal"), 2); h, _ = fh_head("GET", "/kerning/pairs?pairs=A:V")
print("1518 the kerning route names its font   :", h)
fh_setup(FHFont(), 1); ns["_route"]("GET", "/font/current"); _r = ns["_build_response"](200, {"x": 1})
print("1519 _build_response keeps the font of the request until the next one:", b"X-Glyphbridge-Font:" in _r)
ns["_route"]("GET", "/version"); print("1519b the next request forgets it       :", b"X-Glyphbridge-Font" not in ns["_build_response"](200, {"x": 1}))
print("1519c _handle forgets it in finally     :", "_forget_request_font()" in src[src.index("def _handle("):src.index("def _poll(")])
fl.CurrentFont = _fh_saved[0]
if _fh_saved[1] is not None: fl.CountFonts = _fh_saved[1]
elif hasattr(fl, "CountFonts"): del fl.CountFonts
ns["_forget_request_font"]()

# ================= v0.114: the delete dialog names the client and the font of the request =================
print("\n==== v0.114 delete dialog text ====")
_dd_saved = (fl.CurrentFont, getattr(fl, "CountFonts", None), ns["QMessageBox"])
def dd(label, client, font, count, glyph="w6a_one"):
    fh_setup(font, count); ns["_forget_request_font"](); ns["_request_client"] = client
    ns["_open_font"]()
    print(label, ":", repr(ns["_deletion_text"](glyph)))
dd("1520 client, saved font, one font open  ", "local-agent-mode", FHFont("testfont", "Regular", "D:/fonts/savedtestfont-b.vfc"), 1)
dd("1521 client, unsaved font, two open     ", "local-agent-mode", FHFont("Unnamed", "Regular", ""), 2)
dd("1522 no client name, saved, three open  ", None, FHFont("Arial", "Regular", ":/Arial: Normal"), 3)
dd("1523 no family or style name            ", "claude-code", FHFont("", "", "C:/f/x.vfc"), 1)
dd("1524 a Windows path with backslashes    ", "claude-code", FHFont("Back", "Bold", "C:\\fonts\\back.vfc"), 2)
dd("1525 path None, no CountFonts           ", "claude-code", FHFont("Unnamed1", "Regular", None), "missing")
dd("1526 path raises                        ", "claude-code", FHFont("Raise", "Regular", RuntimeError("path boom")), 1)
dd("1526b path not text                     ", "claude-code", FHFont("Seven", "Regular", 7), 1)
dd("1527 a path ending in a slash           ", "claude-code", FHFont("Slash", "Regular", "C:/fonts/"), 1)
dd("1528 control characters, a long file    ", "claude-code", FHFont("Ctl\nFam", "Reg\tular", "C:/f/" + "n" * 150 + ".vfc"), 1)
dd("1528b control character in the file name", "claude-code", FHFont("Ctl", "Regular", "C:/f/a\nb.vfc"), 1)
print("1529 the client name is the log's cleaned name:", [ns["_act_client"](raw) for raw in ("local-agent-mode-glyphbridge-fontlab", "x%0A%5Bfake%5D", "c" * 80)])
ns["_forget_request_font"](); ns["_request_client"] = "claude-code"
print("1530 no font noted in this request     :", repr(ns["_deletion_text"]("w6a_one")))
class DDButton:
    def __init__(self, t): self.text = t
    def setText(self, t): self.text = t
class DDBox:                                  # recording QMessageBox (v0.203: the self-closing dialog's members too)
    Warning, Yes, No = "Warning", 16384, 65536
    seen = []
    answer = 16384
    def __init__(self, icon, title, text, buttons):
        DDBox.seen.append((icon, title, text, buttons)); self.btns = {16384: DDButton("&Yes"), 65536: DDButton("&No")}
    def setDefaultButton(self, b): DDBox.seen.append(("default", b))
    def button(self, which): return self.btns[which]
    def clickedButton(self): return self.btns[DDBox.answer]
    def exec_(self): return DDBox.answer
class DDTimer:                                # never fires: the person answers in time
    def __init__(self, parent): pass
    def setSingleShot(self, v): pass
    def setInterval(self, ms): pass
    def connect(self, *a): return True
    def start(self): pass
    def stop(self): pass
_dd_timer = getattr(ns["QtCore"], "QTimer", None)
ns["QMessageBox"] = DDBox; ns["QtCore"].QTimer = DDTimer
fh_setup(FHFont("Unnamed", "Regular", ""), 2); ns["_forget_request_font"](); ns["_request_client"] = "local-agent-mode"; ns["_open_font"]()
yes = ns["_confirm_deletion"]("w6a_one"); DDBox.answer = 65536; no = ns["_confirm_deletion"]("w6a_one")
print("1531 the dialog shows that text        :", DDBox.seen[0][1], "|", DDBox.seen[0][2].startswith(ns["_deletion_text"]("w6a_one")),
      "| default", DDBox.seen[1], "| Yes ->", yes["answer"], "| No ->", no["answer"], "| then:", DDBox.seen[0][2].split("\n\n")[-1])
DDBox.answer = 16384; DDBox.seen.clear(); ns["_confirm_deletion"](".notdef")
print("1531b .notdef gets its own warning      :", DDBox.seen[0][2].split("\n\n")[1])
if _dd_timer is None: del ns["QtCore"].QTimer
else: ns["QtCore"].QTimer = _dd_timer
fh_setup(FHFont("testfont", "Regular", "D:/fonts/savedtestfont-b.vfc"), 2); h, head = fh_head("GET", "/font/current")
print("1532 the file name never goes into a header:", "savedtestfont-b" not in head, "| headers:", h)
print("1533 no fixed agent name in the listener:", "Claude" not in src, "| _confirm_deletion uses _deletion_text:", "_deletion_text(name)" in src[src.index("def _confirm_deletion("):src.index("def delete_glyph(")],
      "| delete_glyph reads the font before the dialog:", src.index("_open_font()", src.index("def delete_glyph(")) < src.index("_confirm_deletion(name,", src.index("def delete_glyph(")))
fl.CurrentFont = _dd_saved[0]; ns["QMessageBox"] = _dd_saved[2]; ns["_request_client"] = None
if _dd_saved[1] is not None: fl.CountFonts = _dd_saved[1]
elif hasattr(fl, "CountFonts"): del fl.CountFonts
ns["_forget_request_font"]()

# ================= v0.115: /debug/fontdir stage=memberdir (one member of a sub-object, names only) =================
print("\n==== v0.115 /debug/fontdir stage=memberdir ====")
class FDInfoDict:
    """the member under test: records every non-dunder access and every container call (there must be none)."""
    __doc__ = "Font info dictionaries"
    def __getattribute__(self, n):
        if not n.startswith("__"): FD["touched"].append("dict." + n)
        return object.__getattribute__(self, n)
    def __len__(self): FD["called"].append("dict.len"); return 4
    def __iter__(self): FD["called"].append("dict.iter"); return iter(())
    def __getitem__(self, k): FD["called"].append("dict.getitem"); return 1
    def __contains__(self, k): FD["called"].append("dict.contains"); return True
    def keys(self): FD["called"].append("dict.keys"); return []
    def get(self, k): FD["called"].append("dict.get"); return 1
    def has_key(self, k): FD["called"].append("dict.has_key"); return True
class FDDirBoom:
    def __dir__(self): raise RuntimeError("dir boom")
class FDInfo:
    def __getattribute__(self, n):
        if not n.startswith("__"): FD["touched"].append("info." + n)
        return object.__getattribute__(self, n)
    dict = FDInfoDict(); familyName = "Unnamed1"; nothing = None; dirboom = FDDirBoom()
    def method(self): FD["called"].append("info.method"); return "called!"
    @property
    def bad(self): raise RuntimeError("member boom")
    _hid = "secret"
FDFont.info = FDInfo()
def fdd(tag, path):
    c, d = call(path)
    print(tag, ":", c, {k: (v if k != "member_doc" else (len(v) if isinstance(v, str) else v)) for k, v in d.items()}, "| touched", list(FD["touched"]), "| called", list(FD["called"]))
    return c, d
fd_setup(); c, d = fdd("1534 info.dict: type, doc, names   ", "/debug/fontdir?stage=memberdir&attr=info&members=dict")
print("1534b no len, iteration or key lookup on it:", not any(x.startswith("dict.") for x in FD["called"]), "| only 'dict' read on info:", [t for t in FD["touched"] if t.startswith("info.")] == ["info.dict"])
fd_setup(); fdd("1535 a method is never called      ", "/debug/fontdir?stage=memberdir&attr=info&members=method")
fd_setup(); fdd("1536 a plain value is not returned ", "/debug/fontdir?stage=memberdir&attr=info&members=familyName")
fd_setup(); fdd("1537 a None member                 ", "/debug/fontdir?stage=memberdir&attr=info&members=nothing")
fd_setup(); fdd("1538 member getattr raises         ", "/debug/fontdir?stage=memberdir&attr=info&members=bad")
fd_setup(); fdd("1539 dir() of the member raises    ", "/debug/fontdir?stage=memberdir&attr=info&members=dirboom")
for tag, q in (("1540 two names refused            ", "dict,method"), ("1540b no name refused            ", ""), ("1540c only spaces refused        ", "%20%20"),
               ("1540d spaces around a name trimmed", "%20dict%20"), ("1541 unknown member              ", "zzz"), ("1541b private member refused     ", "_hid"),
               ("1541c bad identifier refused      ", "a.b"), ("1541d a call is refused         ", "dict()")):
    fd_setup(); fdd(tag, "/debug/fontdir?stage=memberdir&attr=info&members=" + q)
fd_setup(); fdd("1542 no members parameter         ", "/debug/fontdir?stage=memberdir&attr=info")
fd_setup(); fdd("1543 attr is a plain value        ", "/debug/fontdir?stage=memberdir&attr=familyName&members=dict")
fd_setup(); fdd("1543b attr is a callable (not called)", "/debug/fontdir?stage=memberdir&attr=method&members=dict")
fd_setup(count=0); fdd("1544 CountFonts 0: not open       ", "/debug/fontdir?stage=memberdir&attr=info&members=dict")
fd_setup(); fdd("1545 bad stage names all four     ", "/debug/fontdir?stage=deeper&attr=info&members=dict")
_fdd_src = src[src.index('    if stage in ("memberdir", "keys"):'):src.index('    if stage == "member":')]
_fdd_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _fdd_src).splitlines())
print("1546 static scan of memberdir    : len() calls:", _fdd_code.count("len("), "| mv( calls:", _fdd_code.count("mv("), "| container syntax on mv:",
      _re83.findall(r"\bmv\s*\[|\bmv\.(?:get|keys|values|items|has_key)\b|\bin\s+mv\b|\biter\(|\blist\(mv|\bdict\(mv", _fdd_code), "| scanned chars > 800:", len(_fdd_code) > 800,
      "| still read-only:", "go=yes" not in _fdd_src)
del FDFont.info
fl.CurrentFont = _fd_cur
if _fd_cf is not None: fl.CountFonts = _fd_cf
elif hasattr(fl, "CountFonts"): del fl.CountFonts

# ================= v0.116: stage=memberdir takes a dotted path of up to 3 steps (names only) =================
print("\n==== v0.116 /debug/fontdir stage=memberdir, dotted path ====")
class FDSpy:
    """a node of the walk: records every non-dunder access and every container call (there must be none)."""
    def __init__(self, tag, **members):
        object.__setattr__(self, "_tag", tag)
        for k, v in members.items(): object.__setattr__(self, k, v)
    def __getattribute__(self, n):
        if not n.startswith("_"): FD["touched"].append(object.__getattribute__(self, "_tag") + "." + n)
        return object.__getattribute__(self, n)
    def __len__(self): FD["called"].append(self._tag + ".len"); return 2
    def __iter__(self): FD["called"].append(self._tag + ".iter"); return iter(())
    def __getitem__(self, k): FD["called"].append(self._tag + ".getitem"); return 1
    def __contains__(self, k): FD["called"].append(self._tag + ".contains"); return True
def _fdd_meth(): FD["called"].append("meth()"); return "called!"
class FDDeepBoom:
    @property
    def boom(self): raise RuntimeError("deep boom")
FDInfo.deep = FDSpy("deep", flags=FDSpy("flags", names=FDSpy("names", leaf=FDSpy("leaf"))), num=7, nothing=None, meth=_fdd_meth,
                    dirboom=FDDirBoom(), raiser=FDDeepBoom(), names=FDSpy("names2"))
FDFont.info = FDInfo()
for tag, q in (("1547 two steps: deep.flags              ", "deep.flags"),
               ("1548 three steps: deep.flags.names      ", "deep.flags.names"),
               ("1549 four steps refused                 ", "deep.flags.names.leaf"),
               ("1550 the last step a plain value        ", "deep.num"),
               ("1550b the last step None                ", "deep.nothing"),
               ("1551 the last step a callable, not called", "deep.meth"),
               ("1552 a plain value mid-path ends it     ", "deep.num.real"),
               ("1552b a callable mid-path ends it, not called", "deep.meth.x"),
               ("1553 an unknown second step             ", "deep.zzz"),
               ("1553b an unknown first step             ", "zzz.flags"),
               ("1554 an empty step refused              ", "deep..flags"),
               ("1554b a private step refused            ", "deep._tag"),
               ("1554c a call step refused               ", "deep.meth()"),
               ("1555 spaces around steps trimmed        ", "%20deep%20.%20flags%20"),
               ("1556 getattr of a deeper step raises    ", "deep.raiser.boom"),
               ("1557 dir() of a step raises             ", "deep.dirboom.x"),
               ("1558 a dotted path with a comma refused ", "deep.flags,deep.num"),
               ("1559 a single name is reported as before", "dict")):
    fd_setup(); fdd(tag, "/debug/fontdir?stage=memberdir&attr=info&members=" + q)
fd_setup(); fdd("1560 a method at the end: dict.has_key  ", "/debug/fontdir?stage=memberdir&attr=info&members=dict.has_key")
print("1561 no container call anywhere:", not any(x.endswith((".len", ".iter", ".getitem", ".contains")) for x in FD["called"]), "| meth never called:", "meth()" not in FD["called"])
_fdd_src2 = src[src.index('    if stage in ("memberdir", "keys"):'):src.index('    if stage == "member":')]
_fdd_code2 = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _fdd_src2).splitlines())
print("1562 static scan of the walk     : len() calls:", _fdd_code2.count("len("), "(the step count only:", _fdd_code2.count("len(steps)"), ") | obj( / mv( calls:", len(_re83.findall(r"\b(?:obj|mv)\(", _fdd_code2)),
      "| container syntax:", _re83.findall(r"\b(?:obj|mv|val)\s*\[|\b(?:obj|mv|val)\.(?:get|keys|values|items|has_key)\b|\bin\s+(?:obj|mv|val)\b|\biter\(|\blist\((?:obj|mv|val)", _fdd_code2),
      "| getattr(obj, s) once:", _fdd_code2.count("getattr(obj, s)") == 1, "| max steps", ns["_MEMBERDIR_MAX_STEPS"])
del FDFont.info; del FDInfo.deep
fl.CurrentFont = _fd_cur
if _fd_cf is not None: fl.CountFonts = _fd_cf
elif hasattr(fl, "CountFonts"): del fl.CountFonts

# ================= v0.117: /debug/fontdir stage=keys (ONE gated keys() call at the end of a memberdir path) =================
print("\n==== v0.117 /debug/fontdir stage=keys ====")
class FDKeyed:
    """an fgStringDict stand-in: records every call; only keys() may ever be called, and only once per request."""
    def __init__(self, result=None, raise_on_keys=False): self._r, self._raise = result, raise_on_keys
    def keys(self):
        FD["called"].append("keys")
        if self._raise: raise RuntimeError("keys boom")
        return self._r
    def has_key(self, k): FD["called"].append("has_key"); return True
    def value(self, k): FD["called"].append("value"); return "v"
    def asDict(self): FD["called"].append("asDict"); return {}
    def __len__(self): FD["called"].append("len"); return 1
    def __iter__(self): FD["called"].append("iter"); return iter(())
setattr(FDKeyed, "del", lambda self, k: FD["called"].append("del"))
class FDNative:
    """a result that is not a plain list: it must not be iterated."""
    def __iter__(self): FD["called"].append("result.iter"); return iter(("x",))
    def __len__(self): FD["called"].append("result.len"); return 1
class FDKeysAttr:
    keys = ["not", "callable"]
class FDNoKeys:
    def other(self): return 1
FDInfo.kd = FDSpy("kd", names=FDKeyed(["familyName", "styleName"]), tup=FDKeyed(("a", "b")), mixed=FDKeyed(["a", 7]),
                  native=FDKeyed(FDNative()), many=FDKeyed([f"k{i}" for i in range(250)]), boom=FDKeyed(raise_on_keys=True),
                  dirty=FDKeyed(["ok\nkey", "L" * 150]), attrkeys=FDKeysAttr(), nokeys=FDNoKeys(), num=5, meth=_fdd_meth, empty=FDKeyed([]))
FDFont.info = FDInfo()
def fdk(tag, q):
    fd_setup(); c, d = call("/debug/fontdir?stage=keys&attr=info&" + q)
    shown = {k: v for k, v in d.items() if k not in ("open", "count_fonts", "stage", "font_type", "attr", "value_type")}
    if isinstance(shown.get("keys"), list) and len(shown["keys"]) > 6: shown["keys"] = shown["keys"][:3] + ["..."] + shown["keys"][-2:]
    print(tag, ":", c, shown, "| called", list(FD["called"]))
fdk("1563 no go: says what it would call   ", "members=kd.names")
fdk("1563b go=no: not called               ", "members=kd.names&go=no")
fdk("1563c go=YES: not called (exact yes)  ", "members=kd.names&go=YES")
fdk("1564 go=yes: ONE keys() call          ", "members=kd.names&go=yes")
fdk("1564b an empty list                   ", "members=kd.empty&go=yes")
fdk("1565 a tuple of text                  ", "members=kd.tup&go=yes")
fdk("1566 a non-text entry: type only      ", "members=kd.mixed&go=yes")
fdk("1567 a native result: never iterated  ", "members=kd.native&go=yes")
fdk("1568 250 keys: 200 returned, cut      ", "members=kd.many&go=yes")
fdk("1569 control characters, a long key   ", "members=kd.dirty&go=yes")
fdk("1570 keys() raises                    ", "members=kd.boom&go=yes")
fdk("1571 keys is not callable             ", "members=kd.attrkeys&go=yes")
fdk("1572 no keys member                   ", "members=kd.nokeys&go=yes")
fdk("1573 the path ends at a plain value   ", "members=kd.num&go=yes")
fdk("1573b the path ends at a callable     ", "members=kd.meth&go=yes")
fdk("1574 the path rules apply: 4 steps    ", "members=kd.names.a.b&go=yes")
fdk("1574b no members                      ", "go=yes")
fd_setup(); c, d = call("/debug/fontdir?stage=keys&attr=familyName&members=x&go=yes"); print("1575 attr a plain value               :", c, d.get("error"), "| called", list(FD["called"]))
fd_setup(); c, d = call("/debug/fontdir?stage=what&attr=info"); print("1576 bad stage names all five          :", d)
_fk_src = src[src.index("def _fontdir_keys("):src.index("# /debug/tryfont (v0.83)")]
_fk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _fk_src).splitlines())
print("1577 static scan of _fontdir_keys: calls of the fetched member:", len(_re83.findall(r"\bcall\(\)", _fk_code)), "| go checked before the call:", _fk_src.index('go != "yes"') < _fk_src.index("got = call()"),
      "| members fetched by getattr:", _re83.findall(r'getattr\(obj, "(\w+)"\)', _fk_src), "| other calls:", _re83.findall(r"\.(?:has_key|asDict|value|del|get|items|values)\(", _fk_code),
      "| subscripts:", [x for x in _re83.findall(r"\b(\w+)\[", _fk_code) if x != "result"],
      "| got read only after the list/tuple check:", _fk_src.index("type(got) in (list, tuple)") < _fk_src.index("for k in got") < _fk_src.index("enumerate(got)"))
_fk_route = src[src.index('if path == "/debug/fontdir":'):src.index('if path == "/debug/tryfont":')]
print("1578 the route passes go             :", 'query.get("go")' in _fk_route and "members, go)" in _fk_route, "| keys stage listed in the docstring:", "stage=keys&...&go=yes" in src[:src.index('"""', 3)])
del FDFont.info; del FDInfo.kd
fl.CurrentFont = _fd_cur
if _fd_cf is not None: fl.CountFonts = _fd_cf
elif hasattr(fl, "CountFonts"): del fl.CountFonts

# ================= v0.118: /font/current also reads the names FontLab keeps in the font package =================
print("\n==== v0.118 /font/current package_names ====")
_pn_saved = (fl.CurrentFont, getattr(fl, "CountFonts", None), getattr(_fm, "flWorkspace", None))
PN = {"called": []}
class PNPkg:
    """a font package: only the five name attributes, path and isNull may be read; every call is recorded."""
    def __init__(self, path="", is_null=False, **names):
        self.path, self.isNull = path, is_null
        base = {"psn": "W6aTest-Regular", "ffn": "Unnamed1 Regular", "tfn": "Unnamed1", "tsn": "Regular", "sgn": "Unnamed1"}
        base.update(names)
        for k, v in base.items():
            setattr(self, k, v)
    def close(self): PN["called"].append("close")
    def store_font_info(self): PN["called"].append("store_font_info")
class PNRaising:
    def __get__(self, obj, owner): raise RuntimeError("psn boom")
class PNWs:
    def __init__(self, pkg, n): self.currentPackage, self._n = pkg, n
    def packages(self): return [self.currentPackage] * self._n
def pn_setup(font, count, pkg, npk=1, ws_raises=False):
    fl.CurrentFont = lambda: font
    if count == "missing":
        if hasattr(fl, "CountFonts"): del fl.CountFonts
    else:
        fl.CountFonts = lambda: count
    class _WS:
        @staticmethod
        def instance():
            if ws_raises: raise RuntimeError("workspace boom")
            return PNWs(pkg, npk)
    _fm.flWorkspace = _WS
    PN["called"].clear()
def pn(tag, font, count, pkg, **kw):
    pn_setup(font, count, pkg, **kw); c, d = call("/font/current")
    print(tag, ":", c, {k: v for k, v in d.items() if k.startswith("package") or k == "postscript_font_name"}, "| calls", PN["called"])
pn("1579 one unsaved font: names read        ", FHFont("Unnamed1", "Regular", ""), 1, PNPkg())
pn("1580 two fonts, same path: matched       ", FHFont("testfont", "Regular", "D:/f/a.vfc"), 2, PNPkg("D:/f/a.vfc", psn="testfont-Regular"))
pn("1581 two fonts, paths differ             ", FHFont("testfont", "Regular", "D:/f/a.vfc"), 2, PNPkg("D:/f/b.vfc"))
pn("1582 two unsaved fonts                   ", FHFont("Unnamed1", "Regular", ""), 2, PNPkg(""))
pn("1583 one font, but two packages          ", FHFont("Unnamed1", "Regular", ""), 1, PNPkg(), npk=2)
pn("1584 the workspace raises                ", FHFont("Unnamed1", "Regular", ""), 1, PNPkg(), ws_raises=True)
pn("1585 no CountFonts                       ", FHFont("Unnamed1", "Regular", ""), "missing", PNPkg())
pn("1585b CountFonts gives -1               ", FHFont("Unnamed1", "Regular", ""), -1, PNPkg())
pn("1586 the package is null                 ", FHFont("Unnamed1", "Regular", ""), 1, PNPkg(is_null=True))
_odd = PNPkg(ffn=7, tfn=lambda: PN["called"].append("tfn()"), sgn="Ctl" + chr(10) + "Group")
pn("1587 not text, a callable, control chars ", FHFont("Unnamed1", "Regular", ""), 1, _odd)
class PNPkgRaise(PNPkg):
    psn = PNRaising()
    def __init__(self):
        for k, v in {"path": "", "isNull": False, "ffn": "F", "tfn": "T", "tsn": "S", "sgn": "G"}.items(): object.__setattr__(self, k, v)
pn("1588 reading psn raises                  ", FHFont("Unnamed1", "Regular", ""), 1, PNPkgRaise())
_pn_src = src[src.index("def _package_names("):src.index("def get_glyph_names(")]
_pn_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\n]|\.)*"', '""', _pn_src).splitlines())
print("1589 static scan of _package_names: calls on pkg:", _re83.findall(r"\bpkg\.\w+\(|\bpkg\(|\bvalue\(", _pn_code), "| attributes read:", _re83.findall(r"getattr\((\w+), (\w+)\)", _pn_src),
      "| names read:", ns["_PACKAGE_NAME_FIELDS"], "| /font/current calls it:", "_package_names(font, _REQUEST_FONT[" in src[src.index("def get_current_font_info("):src.index("def _package_names(")])
fl.CurrentFont = _pn_saved[0]
if _pn_saved[1] is not None: fl.CountFonts = _pn_saved[1]
elif hasattr(fl, "CountFonts"): del fl.CountFonts
if _pn_saved[2] is not None: _fm.flWorkspace = _pn_saved[2]
ns["_forget_request_font"]()


# ================= v0.119: /debug/tryrefresh (F1: one fontlab.Update on the changed glyph instead of font.update(); gated experiment; faked font) =================
TR = {"font": None, "calls": [], "forbidden": [], "cfg": {}}
def _tr_spy(label):
    def f(self, *a, **k):
        TR["forbidden"].append(label); raise RuntimeError("FORBIDDEN CALL: " + label)
    return f
class TRGlyph:
    _next = [100]
    def __init__(self, n, u=None):
        self.name = n; TRGlyph._next[0] += 1; self.id = TRGlyph._next[0]; self._u = u
    @property
    def unicode(self):
        if TR["cfg"].get("unicode_read_raises"): raise RuntimeError("unicode unreadable")
        return self._u
    @unicode.setter
    def unicode(self, v):
        TR["calls"].append(("set unicode", self.name, v))
        if TR["cfg"].get("unicode_set_raises"): raise RuntimeError("unicode refused")
        if not TR["cfg"].get("unicode_set_noop"): self._u = v
for _n in ("update", "remove", "save", "release"):
    setattr(TRGlyph, _n, _tr_spy("glyph." + _n))
class TRFont:
    path = "D:/tr/test.vfc"
    def __init__(self, names): self.glyphs = [TRGlyph(n, 65 if n == "A" else None) for n in names]
    def createGlyph(self, name):
        TR["calls"].append(("createGlyph", name))
        if TR["cfg"].get("create_raises"): raise RuntimeError("createGlyph refused")
        if TR["cfg"].get("create_noop"): return None
        self.glyphs.append(TRGlyph(name.replace("-", "") if TR["cfg"].get("create_renames") else name))
        return object()
for _n in ("update", "removeGlyph", "remove", "delete", "deleteGlyph", "save", "close", "export", "exportFont", "release", "blockUpdate", "unblockUpdate", "addGlyph"):
    setattr(TRFont, _n, _tr_spy("font." + _n))
class TRModern:
    def __init__(self, glyph, font):
        TR["calls"].append(("flGlyph", glyph.name))
        if TR["cfg"].get("wrapper_raises"): raise RuntimeError("no modern glyph")
        self.name = glyph.name; self.fgGlyphId = glyph.id
    def isValid(self): return True
for _n in ("update", "assignFgLayer", "assignFontGateData", "fillFgData"):
    setattr(TRModern, _n, _tr_spy("flGlyph." + _n))
class TRNative: pass
def _tr_update(*a):
    TR["calls"].append(("Update", [getattr(x, "name", type(x).__name__) for x in a]))
    if TR["cfg"].get("update_raises"): raise RuntimeError("Update refused")
    return TR["cfg"].get("update_returns")
def _tr_update_all(*a):
    TR["forbidden"].append("UpdateAll"); raise RuntimeError("FORBIDDEN CALL: UpdateAll")
_tr_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace", "flGlyph", "Update", "UpdateAll")]
def tr_setup(names=(".notdef", "A"), ws=None, update=True, **cfg):
    ts85_setup(**(ws or {})); TR["calls"].clear(); TR["forbidden"].clear(); TR["cfg"] = dict(cfg); TR["font"] = TRFont(names)
    ns["_TRYREFRESH"].update(create_Update_flGlyph=0, create_none=0, unicode=0); ns["_MODERN_CACHE"].clear()
    for _m in _tf_mods:
        _m.CurrentFont = lambda: TR["font"]; _m.flGlyph = TRModern; _m.UpdateAll = _tr_update_all
        if update is None:
            if hasattr(_m, "Update"): del _m.Update
        else:
            _m.Update = _tr_update if update is True else update
def ttr(tag, query, keys=None):
    c, d = call("/debug/tryrefresh" + query)
    print(tag, ":", c, d if keys is None else {k: d.get(k) for k in keys}, "| names", [g.name for g in TR["font"].glyphs] if TR["font"] else None, "| calls", TR["calls"])
    return d
KEYSC = ("stage", "how", "name", "calls", "call_error", "refresh_error", "refresh_return", "before_count", "after_count", "present", "created", "calls_so_far", "created_under_other_names")
KEYSU = ("stage", "name", "value", "calls", "set_error", "refresh_error", "refresh_return", "unicode_before", "unicode_after", "matches", "calls_so_far")
tr_setup(); ttr("1590 create without go                ", "?stage=create&name=w1&how=none")
ttr("1591 go must be exactly yes           ", "?stage=create&name=w1&how=Update_flGlyph&go=maybe")
ttr("1592 unknown stage                    ", "?stage=bogus&name=w1&how=none&go=yes")
ttr("1593 stage missing                    ", "?name=w1&how=none&go=yes")
ttr("1594 unknown how                      ", "?stage=create&name=w1&how=Update_fgGlyph&go=yes")
ttr("1595 how missing                      ", "?stage=create&name=w1&go=yes")
for _tag, _nm in (("1596a empty name                    ", ""), ("1596b name of 41 characters        ", "N" * 41), ("1596c name with a space            ", "A%20B"),
                  ("1596d name with a slash            ", "A%2FB"), ("1596e non-ASCII name               ", "%C3%A4")):
    ttr(_tag, "?stage=create&name=" + _nm + "&how=none&go=yes", keys=("error", "calls_so_far"))
ttr("1597 name of 40 characters, accepted  ", "?stage=create&name=" + "N" * 40 + "&how=none&go=yes", keys=("created", "calls_so_far"))
tr_setup(); ttr("1598 create, how=none: createGlyph only", "?stage=create&name=w1&how=none&go=yes", keys=KEYSC)
ttr("1599 create, Update on the new glyph  ", "?stage=create&name=w2&how=Update_flGlyph&go=yes", keys=KEYSC)
ttr("1600a how=none a second time, refused ", "?stage=create&name=w3&how=none&go=yes", keys=("error", "calls_so_far"))
ttr("1600b Update_flGlyph again, refused   ", "?stage=create&name=w4&how=Update_flGlyph&go=yes", keys=("error", "calls_so_far"))
tr_setup(); ttr("1601 existing name refused, not counted", "?stage=create&name=A&how=Update_flGlyph&go=yes", keys=("error", "before_count", "calls_so_far"))
tr_setup(create_raises=1); ttr("1602 createGlyph raises              ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=KEYSC)
tr_setup(create_noop=1); ttr("1603 createGlyph does nothing         ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=KEYSC)
tr_setup(create_renames=1); ttr("1604 createGlyph renames             ", "?stage=create&name=w-1&how=Update_flGlyph&go=yes", keys=KEYSC)
tr_setup(wrapper_raises=1); ttr("1605 modern glyph unreachable        ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=KEYSC)
tr_setup(update_raises=1); ttr("1606 Update raises                   ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=KEYSC)
tr_setup(update_returns=TRNative()); ttr("1607 Update returns a native object ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=("refresh_return", "refresh_error"))
tr_setup(update=None); ttr("1608a no Update in the module        ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=("error", "calls_so_far"))
ttr("1608b how=none needs no Update        ", "?stage=create&name=w1&how=none&go=yes", keys=("created", "calls", "calls_so_far"))
tr_setup(update="not callable"); ttr("1608c Update not callable         ", "?stage=create&name=w1&how=Update_flGlyph&go=yes", keys=("error", "calls_so_far"))
tr_setup(); ttr("1609 unicode without go                ", "?stage=unicode&name=A&value=57346")
for _tag, _v in (("1609a value missing                  ", ""), ("1609b value 0                        ", "0"), ("1609c value 1114112                  ", "1114112"),
                 ("1609d value not a number             ", "abc"), ("1609e value of 8 digits              ", "00000065"), ("1609f negative value               ", "-5"),
                 ("1609g superscript digit              ", "%C2%B2"), ("1609h a fraction                   ", "6.5"), ("1609i hexadecimal                  ", "0x41")):
    ttr(_tag, "?stage=unicode&name=A&value=" + _v + "&go=yes", keys=("error", "calls_so_far"))
ttr("1609j value 1114111, accepted         ", "?stage=unicode&name=A&value=1114111&go=yes", keys=("matches", "unicode_after", "calls_so_far"))
tr_setup(); ttr("1610 unicode A = 57346, then Update   ", "?stage=unicode&name=A&value=57346&go=yes", keys=KEYSU)
ttr("1611 unicode a second time, refused   ", "?stage=unicode&name=A&value=65&go=yes", keys=("error", "calls_so_far"))
tr_setup(); ttr("1612 unicode, no such glyph, not counted", "?stage=unicode&name=Q&value=81&go=yes", keys=("error", "calls_so_far"))
tr_setup(unicode_set_raises=1); ttr("1613 the setter raises: no Update ", "?stage=unicode&name=A&value=57346&go=yes", keys=KEYSU)
tr_setup(unicode_set_noop=1); ttr("1614 the setter does nothing        ", "?stage=unicode&name=A&value=57346&go=yes", keys=KEYSU)
tr_setup(wrapper_raises=1); ttr("1615 modern glyph unreachable: nothing set", "?stage=unicode&name=A&value=57346&go=yes", keys=("error", "calls_so_far"))
tr_setup(update_raises=1); ttr("1616 Update raises                   ", "?stage=unicode&name=A&value=57346&go=yes", keys=KEYSU)
tr_setup(unicode_read_raises=1); ttr("1617 the value cannot be read        ", "?stage=unicode&name=A&value=57346&go=yes", keys=KEYSU)
tr_setup(update=None); ttr("1618 unicode needs Update: refused    ", "?stage=unicode&name=A&value=57346&go=yes", keys=("error", "calls_so_far"))
GATESTR = [("1619a no font counted             ", dict(count=0)), ("1619b two fonts open              ", dict(count=2)),
           ("1619c CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("1619d two packages               ", dict(packages=2)),
           ("1619e no current package          ", dict(cp=None)), ("1619f package is null             ", dict(isNull=True)),
           ("1619g isNull is 0 (falsy, no bool)", dict(isNull=0))]
for _tag, _over in GATESTR:
    tr_setup(ws=_over); rows = []
    for _q in ("?stage=create&name=w1&how=Update_flGlyph&go=yes", "?stage=create&name=w1&how=none&go=yes", "?stage=unicode&name=A&value=57346&go=yes"):
        c, d = call("/debug/tryrefresh" + _q); rows.append((c, (d.get("error") or "")[:60]))
    print(_tag, ":", rows, "| calls", TR["calls"], "| counters", ns["_TRYREFRESH"], "| names", [g.name for g in TR["font"].glyphs], "| A", TR["font"].glyphs[1]._u)
tr_setup()
for _m in _tf_mods: _m.CurrentFont = lambda: None
c, d = call("/debug/tryrefresh?stage=create&name=w1&how=none&go=yes"); print("1620 no current font object       :", c, d, "| counters", ns["_TRYREFRESH"])
tr_setup()
for _q in ("?stage=create&name=P1&how=none&go=yes", "?stage=create&name=P2&how=Update_flGlyph&go=yes", "?stage=unicode&name=A&value=57346&go=yes",
           "?stage=create&name=P3&how=none", "?stage=unicode&name=P1&value=66&go=maybe"):
    call("/debug/tryrefresh" + _q)
print("1621 forbidden members called    :", TR["forbidden"], "| calls", TR["calls"], "| names", [g.name for g in TR["font"].glyphs])
_src119 = src[src.index("# /debug/tryrefresh (v0.119)"):src.index("# /debug/trykerngroups (v0.103)")]
_code119 = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', "\n".join(l.split("#")[0] for l in _src119.splitlines()))
print("1622 static scan of the probe     : forbidden call syntax found:", _re83.findall(r"\.(?:update|Update\w*|assign\w*|fillFgData|replaceGlyph|deleteGlyph|delete\w*|removeGlyph|remove\w*|save\w*|close\w*|export\w*|release|blockUpdate|unblockUpdate|addGlyph|addPackage)\s*\(|\bUpdateAll\b", _code119),
      "| real calls: createGlyph", len(_re83.findall(r"(?m)^\s+font\.createGlyph\(name\)$", _code119)), "upd(w)", len(_re83.findall(r"\bupd\(w\)", _code119)),
      "unicode set", len(_re83.findall(r"(?m)^\s+glyph\.unicode = codepoint$", _code119)), "| scanned chars > 6000:", len(_src119) > 6000)
print("1623 no product route changed    : create_glyph still calls font.update():", "font.update()" in src[src.index("def create_glyph("):src.index("def _confirm_deletion(")],
      "| mentions of debug_try_refresh( (its def and its route):", src.count("debug_try_refresh("),
      "| route wired:", 'if path == "/debug/tryrefresh":' in src)
c, d = call("/version"); print("1624 version                      :", d)
for _m, _a, _v in _tr_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_MODERN_CACHE"].clear(); ns["_forget_request_font"]()


# ================= v0.120: F1 - glyphs with modern nodes are read and sync-checked without the legacy layer =================
# Live (332-496): touching glyph.layer or reading glyph.layers of a Power Brush glyph, then any font.update(), flattens it;
# glyph.width, glyph.components and the name are safe. The fake legacy glyph records every access to its layer members
# and legacy margins (SPY120), so each case can show that a read or a sync check never reached them.
print("\n==== v0.120 F1: modern-only reads, the light sync check, the box probe ====")
ns["_MODERN_FIRST"] = True
SPY120 = []
V120 = {"cfg": {}, "m": {}, "updates": []}
class V120LLayer(Layer):                                  # a legacy layer for the legacy route (4 nodes)
    name = "test_font"
    def countNodes(s): return 4
    def findNode(s, i):
        if i >= 4: return None
        n = Node(); n.kind = "Move" if i == 0 else "On"; n.smooth = False; return n
class V120Glyph:                                          # legacy fgGlyph: its layer members and legacy margins are spied
    def __init__(s, name, gid, width=639.0, layers=1):
        s.name, s.id, s.width, s._nl = name, gid, width, layers; s.components = []; s.unicode = None
    def _spy(s, what):
        SPY120.append(f"{s.name}.{what}")
    @property
    def layer(s): s._spy("layer"); return V120LLayer() if s._nl else None
    @property
    def layers(s): s._spy("layers"); return [V120LLayer()] * s._nl
    @property
    def bodyLayer(s): s._spy("bodyLayer"); return V120LLayer() if s._nl else None
    @property
    def bodyLayerStrict(s): s._spy("bodyLayerStrict"); return V120LLayer() if s._nl else None
    @property
    def activeLayer(s): s._spy("activeLayer"); return V120LLayer() if s._nl else None
    @property
    def leftMargin(s): s._spy("leftMargin"); return 0.0
    @property
    def rightMargin(s): s._spy("rightMargin"); return 0.0
class V120Font:
    path = "v120.vfc"; info = types.SimpleNamespace(familyName="testfont", styleName="Regular")
    def __init__(s): s.glyphs = V120["glyphs"]
class V120Node:
    def __init__(s, x, y): s.x, s.y = x, y; s.smooth = False
    def isOn(s): return True
    def isOff(s): return False
    def isCurve(s): return False
class V120Contour:
    def __init__(s, pts): s._n = [V120Node(x, y) for x, y in pts]
    def closed(s): return True
    def clockwise(s): return False
    def nodesCount(s): return len(s._n)
    def getNodeAt(s, i):
        if V120["cfg"].get("node_raises"): raise RuntimeError("getNodeAt boom")
        return s._n[i]
class V120Rect:
    def __init__(s, l, b, r, t): s._v = dict(left=l, right=r, top=t, bottom=b, width=r - l, height=t - b)
    def __getattr__(s, k):
        if k.startswith("_"): raise AttributeError(k)
        return lambda: s._v[k]
class V120Tr:
    def __init__(s, dx): s.m11, s.m12, s.m21, s.m22, s.dx, s.dy = 1.0, 0.0, 0.0, 1.0, dx, 0.0
    def isIdentity(s): return s.dx == 0.0
class V120Shape:
    shapeType = "brush"; contoursCount = 1; isComponent = False; isComposite = True
    def __init__(s, name): s._name = name
    @property
    def transform(s): return V120Tr(V120["m"][s._name]["dx"])
class V120MLayer:
    name = "test_font"
    def __init__(s, gname, pts): s._g, s._c = gname, [V120Contour(pts)] if pts else []; s.shapes = [V120Shape(gname)] if pts else []
    def nodesCount(s):
        if V120["cfg"].get("count_text"): return "many"
        return sum(c.nodesCount() for c in s._c)
    def shapesCount(s): return len(s.shapes)
    def componentsCount(s): return 0
    def getContours(s): return list(s._c)
    def boundingBox(s):
        if V120["cfg"].get("box_raises"): raise RuntimeError("boundingBox boom")
        return V120Rect(192.466, 0.0, 464.534, 700.0)
    def inkBox(s, tr=None): return None if V120["cfg"].get("ink_none") else V120Rect(192.466, 0.0, 464.534, 700.0)
class V120Mod:                                            # flGlyph(fgGlyph, fgFont); margins follow the element transform dx
    def __init__(s, g, f):
        if V120["cfg"].get("wrapper_raises"): raise RuntimeError("no modern glyph")
        s.name, s.fgGlyphId = g.name, g.id
        s.activeLayer = V120["layers"].get(g.name)
    def isValid(s): return True
    def _xs(s): return [n.x + V120["m"][s.name]["dx"] for c in s.activeLayer._c for n in c._n]
    @property
    def advanceWidth(s): return V120["m"][s.name]["adv"]
    @advanceWidth.setter
    def advanceWidth(s, v): V120["m"][s.name]["adv"] = float(v)
    def getLSB(s, tr): return min(s._xs())
    def getRSB(s, tr): return V120["m"][s.name]["adv"] - max(s._xs())
    def setSB(s, l, r, mg, al, tr):                       # like FontLab on a Power Brush shape: the element transform moves
        m = V120["m"][s.name]; raw = [x - m["dx"] for x in s._xs()]
        m["dx"] = float(l) - min(raw); m["adv"] = float(l) + (max(raw) - min(raw)) + float(r); return True
def _u120(w):                                             # fontlab.Update: a sync copies the modern advance to the legacy glyph
    V120["updates"].append(w.name)
    if V120["cfg"].get("sync", True):
        for g in V120["glyphs"]:
            if g.name == w.name: g.width = w.advanceWidth
A_PTS = [(192.466, 0.0), (464.534, 0.0), (328.5, 700.0)]
def v120_setup(**cfg):
    V120["cfg"] = dict(cfg); V120["updates"].clear(); SPY120.clear()
    V120["glyphs"] = [V120Glyph(".notdef", 1, 500.0, layers=0), V120Glyph("A", 2), V120Glyph("fresh", 3, 0.0, layers=0)]
    V120["layers"] = {"A": V120MLayer("A", A_PTS), "fresh": V120MLayer("fresh", [])}
    V120["m"] = {"A": {"dx": 0.0, "adv": 639.0}, "fresh": {"dx": 0.0, "adv": 0.0}, ".notdef": {"dx": 0.0, "adv": 500.0}}
    if cfg.get("notdef_drawn"):
        V120["layers"][".notdef"] = V120MLayer(".notdef", [(50.0, 0.0), (450.0, 0.0), (450.0, 700.0), (50.0, 700.0)])
        V120["glyphs"][0]._nl = 1
    for _m in _tf_mods:
        _m.flGlyph = V120Mod; _m.Update = _u120; _m.CountFonts = lambda: 1; _m.CurrentFont = lambda: V120Font()
    qg.QTransform = QTransformStub
    ns["_AUTO_SYNC"] = True; ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    ns["_UNSYNCED"]["glyphs"].clear(); ns["_UNSYNCED"]["overflow"] = False; ns["_UNSYNCED"]["font"] = None
_v120_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("flGlyph", "Update", "CountFonts", "CurrentFont")]
def post120(path, payload):
    r = ns["_route"]("POST", path, json.dumps(payload).encode()); h, _, b = r.partition(b"\r\n\r\n")
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
def o120(tag, q="", keys=("source", "node_count", "contour_count", "component_count", "shape_count", "layer_route", "error")):
    SPY120.clear(); c, d = call("/glyph/outline?name=" + q)
    print(tag, ":", c, {k: (d.get(k)[:70] if isinstance(d.get(k), str) and k == "error" else d.get(k)) for k in keys if k in d}, "| legacy members touched", SPY120)
    return d

v120_setup(); d = o120("1630 outline, modern nodes       ", "A")
mo = d["modern_outline"]; el = d["elements"]
print("1631 the reply                   : modern_outline available", mo["available"], "| nodes", [(n["x"], n["y"]) for n in mo["contours"][0]["nodes"]],
      "| margins", mo.get("margins"), "| elements", el["available"], el["shapes"][0]["is_composite"], el["shapes"][0]["matrix"]["dx"],
      "| no legacy fields:", not any(k in d for k in ("contours", "fontlab_bbox", "margins", "modern_check")))
v120_setup(); d = o120("1632 layer=active is modern too  ", "A&layer=active")
v120_setup(); d = o120("1633 modern=no: legacy (F1 risk) ", "A&modern=no", keys=("source", "node_count", "layer_route"))
v120_setup(); d = o120("1634 layer=strict: legacy        ", "A&layer=strict", keys=("source", "node_count", "layer_route"))
v120_setup(); d = o120("1635 no modern nodes: legacy     ", "fresh", keys=("source", "node_count", "layer_count", "contours"))
v120_setup(wrapper_raises=1); d = o120("1636 modern side unreachable: legacy", "A", keys=("source", "node_count", "elements"))
v120_setup(count_text=1); d = o120("1637 node count unreadable: error", "A")
v120_setup(node_raises=1); d = o120("1638 outline unreadable: error   ", "A")
v120_setup(); d = o120("1639 unknown glyph               ", "Q", keys=("open", "found", "reason"))
for _m in _tf_mods: _m.CountFonts = lambda: 0
SPY120.clear(); c, d = call("/glyph/outline?name=A"); print("1640 no font open               :", c, d, "| legacy members touched", SPY120)
ns["_MODERN_FIRST"] = False; v120_setup(); ns["_MODERN_FIRST"] = False
d = o120("1641 switch off: the legacy route ", "A", keys=("source", "node_count")); ns["_MODERN_FIRST"] = True
# ---- the .notdef check ----
def n120(tag):
    SPY120.clear(); c, d = call("/font/notdef")
    print(tag, ":", c, {k: d.get(k) for k in ("status", "source", "counts", "component_count", "layer_count", "evidence")}, "| legacy members touched", SPY120)
v120_setup(notdef_drawn=1); n120("1642 drawn .notdef: modern only   ")
v120_setup(); n120("1643 empty .notdef: legacy check ")
v120_setup(notdef_drawn=1, wrapper_raises=1); n120("1644 modern unreachable: legacy   ")
v120_setup(notdef_drawn=1, count_text=1); n120("1645 count unreadable: legacy     ")
ns["_MODERN_FIRST"] = False; v120_setup(notdef_drawn=1); n120("1646 switch off: legacy check     "); ns["_MODERN_FIRST"] = True
# ---- the sync check: width and sidebearing writes take the light check; drawings and new layers keep the full one ----
def w120(tag, path, payload, keys=("set", "route", "before", "after")):
    SPY120.clear(); c, d = post120(path, payload)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| fontlab_sync", d.get("fontlab_sync"), "| synced", d.get("synced_with_fontlab"),
          "| tracked", dict(ns["_guard_state"](V120Font())["glyphs"]), "| legacy members touched", SPY120)
v120_setup(); w120("1647 width on A, Update syncs     ", "/glyph/width", {"name": "A", "width": 700})
v120_setup(); w120("1648 sidebearings on A, syncs    ", "/glyph/sidebearings", {"name": "A", "left": 50, "right": 60}, keys=("set", "changed"))
print("1648b the element moved         : dx", V120["m"]["A"]["dx"], "| advance", V120["m"]["A"]["adv"], "| legacy width", V120["glyphs"][1].width)
v120_setup(sync=False); w120("1649 width, Update has no effect ", "/glyph/width", {"name": "A", "width": 700})
SPY120.clear(); allow, rep = ns["_guard_decide"](V120Font())
print("1650 the guard before an update  : allow", allow, "| report", {k: rep.get(k) for k in ("display_refresh", "display_refresh_skipped_to_protect")}, "| legacy members touched", SPY120)
V120["glyphs"][1].width = 700.0; SPY120.clear(); allow, rep = ns["_guard_decide"](V120Font())
print("1651 legacy width caught up      : allow", allow, "| report", rep, "| tracked", dict(ns["_guard_state"](V120Font())["glyphs"]), "| legacy members touched", SPY120)
v120_setup(); _f = V120Font(); _gs = ns["_guard_state"](_f)["glyphs"]
for _how in ("draw_polygon", "draw_path", "layer_created"):
    _gs.clear(); ns["_guard_register"](_f, "fresh", _how); SPY120.clear(); _v = ns["_guard_classify"](_f, "fresh")
    print("1652", f"{_how:13}", "             : light", ns["_guard_is_light"](_f, "fresh"), "| verdict", _v, "| entry", _gs.get("fresh"), "| legacy members touched", SPY120)
_gs.clear(); ns["_guard_register"](_f, "fresh", "layer_created"); ns["_guard_register"](_f, "fresh", "width")
print("1653 new layer, then width       : entry", _gs.get("fresh"), "| light", ns["_guard_is_light"](_f, "fresh"), "(must stay False: the full check)")
_gs.clear(); ns["_guard_register"](_f, "A", "width"); ns["_guard_register"](_f, "A", "sidebearings")
print("1654 width, then sidebearings    : entry", _gs.get("A"), "| light", ns["_guard_is_light"](_f, "A"))
_gs.clear(); ns["_guard_register"](_f, "A", "sidebearings"); ns["_guard_register"](_f, "A", "draw_path")
print("1655 sidebearings, then a drawing: entry", _gs.get("A"), "| light", ns["_guard_is_light"](_f, "A"))
_gs.clear(); print("1656 not remembered              : light", ns["_guard_is_light"](_f, "A"), "| unknown kind:", (ns["_guard_register"](_f, "A", "other"), ns["_guard_is_light"](_f, "A"))[1])
_gs.clear(); ns["_guard_register"](_f, "A", "width"); _real_gs = ns["_guard_state"]
def _gs_boom(f): raise RuntimeError("state boom")
ns["_guard_state"] = _gs_boom; print("1657 registry unreadable         : light", ns["_guard_is_light"](_f, "A"), "(the full check)"); ns["_guard_state"] = _real_gs
_gs.clear(); ns["_guard_register"](_f, "A", "width"); V120["glyphs"][1].width = "wide"; SPY120.clear()
print("1658 legacy width not a number   : verdict", ns["_guard_classify"](_f, "A"), "| legacy members touched", SPY120)
V120["glyphs"][1].width = 639.0; V120["layers"]["A"] = None; SPY120.clear(); ns["_MODERN_CACHE"].clear()
print("1659 modern layer gone           : verdict", ns["_guard_classify"](_f, "A"), "| legacy members touched", SPY120)
V120["glyphs"].pop(1); print("1660 glyph gone                  : verdict", ns["_guard_classify"](_f, "A"))
# ---- the gated box probe ----
def b120(tag, q):
    SPY120.clear(); c, d = call("/debug/readmodern?name=A&stage=box" + q)
    print(tag, ":", c, {k: d.get(k) for k in ("error", "boundingBox()", "inkBox()", "layer_state") if k in d}, "| legacy members touched", SPY120)
v120_setup(); b120("1661 box without go=yes          ", "")
v120_setup(); b120("1662 box, go=yes                 ", "&go=yes")
v120_setup(box_raises=1, ink_none=1); b120("1663 boundingBox raises, ink None", "&go=yes")
print("1664 rect helper                 :", ns["_rect_plain"](None), "|", ns["_rect_plain"](types.SimpleNamespace(left=lambda: "x")), "|",
      ns["_rect_plain"](types.SimpleNamespace(left=lambda: 1.0, right=lambda: 2.0, top=lambda: 3.0, bottom=lambda: 0.0, width=lambda: 1.0, height=lambda: 3.0)))
# ---- static scan: the modern-only code paths never name a legacy layer member ----
def _code120(a, b):                                      # the code only: docstrings, strings and comments removed
    s = _re83.sub(r'"""(?:.|\n)*?"""', '""', src[src.index(a):src.index(b)])
    return _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', "\n".join(l.split("#")[0] for l in s.splitlines()))
_scan120 = {"_modern_only_outline": _code120("def _modern_only_outline(", "_MODERN_FIRST = True"),
            "_notdef_modern_outline_counts": _code120("def _notdef_modern_outline_counts(", "def check_notdef("),
            "light part of _guard_classify": _code120("        if _guard_is_light(font, name):", "        legacy = _tryshape_state(glyph)"),
            "_guard_is_light": _code120("def _guard_is_light(", "def _guard_classify(")}
for _k, _c in _scan120.items():
    print("1665 static scan", f"{_k:30}", ": legacy members named:", _re83.findall(r"\.(?:layer|layers|bodyLayer|bodyLayerStrict|findNode|leftMargin|rightMargin|countNodes)\b|_get_body_layer|_get_layer_by_route|_glyph_layer_count|_tryshape_state|_glyph_margins", _c),
          "| scanned chars", len(_c) > 200)
print("1666 shipped switch              :", _re83.findall(r"(?m)^_MODERN_FIRST = (\w+)", src), "| full kinds", ns["_GUARD_FULL_KINDS"], "| light kinds", ns["_GUARD_LIGHT_KINDS"])
c, d = call("/version"); print("1667 version                     :", d)
# ================= v0.121: FontLab's own ink box (layer.inkBox()) on the modern-only outline read =================
# Live 519-530: inkBox() equalled the computed curve extents (cubic, quadratic, Power Brush, with element transforms), Qt's
# "top" being the lower y; no F1 after it (531-532). The fake below answers like FontLab (top = lower y) and records each call.
print("\n==== v0.121: fontlab_ink_box on the modern-only outline read ====")
INK121 = []
def _ink121(s, *a, **k):
    INK121.append((a, k)); cfg = V120["cfg"]
    if cfg.get("ink_raises"): raise RuntimeError("inkBox boom")
    if cfg.get("ink_none"): return None
    if cfg.get("ink_text"): return types.SimpleNamespace(left=lambda: "l", right=lambda: 1.0, top=lambda: 1.0, bottom=lambda: 0.0, width=lambda: 1.0, height=lambda: 1.0)
    return types.SimpleNamespace(left=lambda: 192.466, right=lambda: 464.534, top=lambda: 0.0, bottom=lambda: 700.0, width=lambda: 272.068, height=lambda: 700.0)
_ink120 = V120MLayer.inkBox; V120MLayer.inkBox = _ink121
def i121(tag, q="A", **cfg):
    v120_setup(**cfg); INK121.clear(); SPY120.clear(); c, d = call("/glyph/outline?name=" + q)
    print(tag, ":", c, "| source", d.get("source"), "| fontlab_ink_box", d.get("fontlab_ink_box"), "| inkBox calls", INK121,
          "| outline kept", isinstance(d.get("modern_outline"), dict) and d["modern_outline"].get("available"), "| legacy members touched", SPY120)
i121("1668 ink box, read once          ")
i121("1669 inkBox raises: outline kept ", ink_raises=1)
i121("1670 inkBox gives None           ", ink_none=1)
i121("1671 a getter is not a number    ", ink_text=1)
i121("1672 no modern nodes: legacy route", "fresh")
i121("1673 modern=no: legacy route     ", "A&modern=no")
i121("1674 node count unreadable: error", count_text=1)
V120MLayer.inkBox = _ink120
# static scan: inkBox() is called with no argument, only in the gated probe and in _modern_ink_box
_strip121 = _re83.sub(r'"""(?:.|\n)*?"""', '""', src)
_strip121 = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', "\n".join(l.split("#")[0] for l in _strip121.splitlines()))
_def121, _hits121 = None, []
for _l in _strip121.splitlines():
    _m121 = _re83.match(r"def (\w+)\(", _l)
    if _m121: _def121 = _m121.group(1)
    if "inkBox" in _l: _hits121.append((_def121, _re83.findall(r"\w+\.inkBox\([^)]*\)", _l)))
print("1675 every inkBox call            :", _hits121)
_code121 = _code120("def _modern_ink_box(", "_MODERN_FIRST = True")
print("1676 _modern_ink_box uses         :", sorted(set(_re83.findall(r"\blayer\.(\w+)", _code121))), "| legacy members named:",
      _re83.findall(r"\.(?:layer|layers|bodyLayer|bodyLayerStrict|findNode|leftMargin|rightMargin|countNodes)\b|_tryshape_state", _code121), "| scanned chars", len(_code121) > 100)
for _m, _a, _v in _v120_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_MODERN_CACHE"].clear(); ns["_forget_request_font"]()

# ================= v0.122: /debug/trysetkern (gated research probe that WRITES one pair: flPackage.kerning(master).set(key, value) once) =================
print("\n==== v0.122 /debug/trysetkern ====")
SK = {"cfg": {}, "kerning_args": [], "pkg_all": set(), "pkg_forbidden": [], "k_all": set(), "k_forbidden": [], "gets": [], "sets": [], "groups_calls": 0}
_SK_K_FORBIDDEN = tuple(n for n in _FK_FORBIDDEN if n != "set")
_SK_PKG_FORBIDDEN = tuple(n for n in _PK_PKG_FORBIDDEN if n != "getAllGroups")
def _sk_pair(key):
    # v0.193: entries are kept by their full key, so a class entry ((name, True), ...) and a glyph entry of the same names stay apart;
    # the documented (a, b) form means two glyphs, the same entry as ((a, False), (b, False))
    if isinstance(key, tuple) and len(key) == 2 and all(isinstance(s, tuple) for s in key): return (tuple(key[0]), tuple(key[1]))
    return ((key[0], False), (key[1], False))
class SKKern:
    def __init__(self): self._table = {_sk_pair(k): v for k, v in SK["cfg"].get("table", {}).items()}
    @property
    def groups(self):
        m = SK["cfg"].get("groups_attr")
        if m == "raise": raise RuntimeError("groups boom")
        if m == "callable": return lambda: None
        return SKGroups()
    def __getattribute__(self, n):
        if not n.startswith("_"):
            SK["k_all"].add(n)
            if n in SK["cfg"].get("k_forbid", _SK_K_FORBIDDEN):
                SK["k_forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self):
        if SK["cfg"].get("len_raises"): raise RuntimeError("len boom")
        return len(self._table)
    def get(self, key):
        SK["gets"].append(key)
        if SK["cfg"].get("get") == "raise": raise RuntimeError("get boom")
        if SK["cfg"].get("get") == "raise_after_remove" and SK.get("removes"): raise RuntimeError("get boom after remove")
        return self._table.get(_sk_pair(key))
    def set(self, key, value):
        SK["sets"].append((key, type(value).__name__, value))
        m = SK["cfg"].get("set")
        if m == "raise": raise TypeError("Argument type must be Tuple(string, string)!")
        if m == "ignore": return 0
        self._table[_sk_pair(key)] = value
        return 1
    def remove(self, key):
        SK.setdefault("removes", []).append(key)
        m = SK["cfg"].get("remove")
        if m == "raise": raise TypeError("Argument type must be fgKerningObjectPair!")
        if m == "pop_then_raise": self._table.pop(_sk_pair(key), None); raise RuntimeError("remove boom after removing")
        if m == "ignore": return None
        if m == "zero": self._table[_sk_pair(key)] = 0.0; return None
        if m == "two": self._table.pop(_sk_pair(key), None); self._table.pop(next(iter(self._table), None), None); return True
        self._table.pop(_sk_pair(key), None)
        return None
class SKGroups:
    # v0.193: the master's kerning group container; only items() (and len()) may be used
    def __getattribute__(self, n):
        if not n.startswith("_"):
            SK.setdefault("g_all", set()).add(n)
            if n != "items":
                SK.setdefault("g_forbidden", []).append(n)
                raise SystemExit("FORBIDDEN group container member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self):
        v = SK["cfg"].get("items", [])
        return len(v) if isinstance(v, list) else 0
    def items(self):
        v = SK["cfg"].get("items", [])
        if v == "raise": raise RuntimeError("items boom")
        return v
class SKPackage:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            SK["pkg_all"].add(n)
            if n in _SK_PKG_FORBIDDEN:
                SK["pkg_forbidden"].append(n)
                raise SystemExit("FORBIDDEN package member touched: " + n)
        return object.__getattribute__(self, n)
    def isNull(self): return False
    @property
    def masters(self): return SK["cfg"].get("masters", ["Regular"])
    @property
    def master(self): return SK["cfg"].get("master", "Regular")
    @property
    def upm(self):
        v = SK["cfg"].get("upm", 1000)
        if isinstance(v, Exception): raise v
        return v
    def getAllGroups(self):
        SK["groups_calls"] += 1
        v = SK["cfg"].get("groups", [])
        if v == "raise": raise RuntimeError("groups boom")
        return v
    @property
    def kerning(self):
        def _kerning(*args):
            SK["kerning_args"].append(args)
            if SK["cfg"].get("kerning_call") == "raise": raise RuntimeError("kerning() boom")
            return SKKern()
        return _kerning
class SKWorkspace:
    @staticmethod
    def instance(): return SK_WS
    def packages(self): return [SK_PKG] * SK["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return SK_PKG
SK_PKG = SKPackage(); SK_WS = SKWorkspace()
class SKFont:
    glyphs = [PKGlyph(n) for n in ("ks1L", "ks1R", "ks1S", ".notdef")]
_sk_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace")]
def sk_setup(calls=0, **cfg):
    SK["cfg"] = dict(cfg)
    for k in ("kerning_args", "gets", "sets"): SK[k].clear()
    SK["groups_calls"] = 0
    ns["_TRYSETKERN"]["calls"] = calls
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = SKWorkspace
        _m.CountFonts = lambda: count
        _m.CurrentFont = lambda: SKFont()
def skc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| kerning() args", SK["kerning_args"], "| sets", SK["sets"], "| getAllGroups calls", SK["groups_calls"])
    return c, d
_SKQ = "/debug/trysetkern?a=ks1L&b=ks1R&value=-100"
_SKR = ("set_error", "set_returned", "exact_before", "exact_after", "read_back_matches", "len_before", "len_after", "table_size_changed", "calls_so_far")
sk_setup(); skc("1677 no go: nothing runs        ", _SKQ)
sk_setup(); skc("1678 go=maybe: nothing runs     ", _SKQ + "&go=maybe")
sk_setup(); c, d = skc("1679 tuple form, -100           ", _SKQ + "&go=yes")
print("1679b note says what may change   :", "may have changed" in d.get("note", "") and "nothing is saved" in d.get("note", ""))
sk_setup(); skc("1680 flags form, ks1L:ks1S -50  ", "/debug/trysetkern?a=ks1L&b=ks1S&value=-50&form=flags&go=yes", keys=("call",) + _SKR)
sk_setup(table={("ks1L", "ks1R"): -100.0}); skc("1681 existing pair overwritten ", "/debug/trysetkern?a=ks1L&b=ks1R&value=-60&go=yes", keys=_SKR)
sk_setup(set="raise"); skc("1682 set raises (counted)       ", _SKQ + "&form=flags&go=yes", keys=_SKR)
sk_setup(set="ignore"); skc("1683 set stores nothing         ", _SKQ + "&go=yes", keys=_SKR)
sk_setup(); skc("1684 fractional value -12.5     ", "/debug/trysetkern?a=ks1L&b=ks1R&value=-12.5&go=yes", keys=("value_asked",) + _SKR)
sk_setup(); skc("1685 value 0                    ", "/debug/trysetkern?a=ks1L&b=ks1R&value=0&go=yes", keys=("value_asked", "set_returned", "exact_after", "read_back_matches"))
for bad in ("", "abc", "nan", "inf", "1e5", "1.5.2", "--1", "1" * 21):
    sk_setup(); skc(f"1686 bad value {bad[:10]!r:12}    ", "/debug/trysetkern?a=ks1L&b=ks1R&value=" + bad + "&go=yes", keys=("error",))
sk_setup(); skc("1687 -1000 at upm 1000: allowed ", "/debug/trysetkern?a=ks1L&b=ks1R&value=-1000&go=yes", keys=("value_asked", "read_back_matches"))
sk_setup(); skc("1688 1000.5 over upm: refused   ", "/debug/trysetkern?a=ks1L&b=ks1R&value=1000.5&go=yes")
for tag, over in (("1689 upm raises        ", dict(upm=RuntimeError("upm boom"))), ("1689 upm is a bool     ", dict(upm=True)),
                  ("1689 upm is 0          ", dict(upm=0)), ("1689 upm is text       ", dict(upm="1000"))):
    sk_setup(**over); skc(tag, _SKQ + "&go=yes")
for bad in ("", "A:V", "x" * 64):
    sk_setup(); skc(f"1690 bad name a {bad[:12]!r:14}", "/debug/trysetkern?a=" + bad + "&b=ks1R&value=-100&go=yes")
sk_setup(); skc("1691 unknown glyph            ", "/debug/trysetkern?a=ks1L&b=Q&value=-100&go=yes")
sk_setup(); skc("1692 bad form                 ", _SKQ + "&form=plain&go=yes")
_SKG = lambda name: [True, name, 8704, 0, ["ks1R", "ks1S"]]
sk_setup(groups=[_SKG("ks1R")]); skc("1693 b is also a group: refused", _SKQ + "&go=yes")
sk_setup(groups=[[False, "ks1L", 3, 0, ["ks1L"]]]); skc("1694 a names a non-kerning group", _SKQ + "&go=yes")
sk_setup(groups=[_SKG("ks1grp")]); skc("1695 other group: allowed      ", _SKQ + "&go=yes", keys=("read_back_matches", "calls_so_far"))
sk_setup(groups=None); skc("1696 getAllGroups None: allowed  ", _SKQ + "&go=yes", keys=("read_back_matches",))
for tag, over in (("1697 getAllGroups raises ", dict(groups="raise")), ("1697 getAllGroups a dict", dict(groups={"ks1R": 1})),
                  ("1697 an entry of 4 items ", dict(groups=[[True, "g", 1, 0]])), ("1697 a name not text     ", dict(groups=[[True, 5, 1, 0, []]]))):
    sk_setup(**over); skc(tag, _SKQ + "&go=yes")
sk_setup(masters=["Regular", 5]); skc("1698 masters not all names    ", _SKQ + "&go=yes")
sk_setup(master="Ghost"); skc("1699 current master unlisted  ", _SKQ + "&go=yes")
sk_setup(kerning_call="raise"); skc("1700 kerning() raises (counted)", _SKQ + "&go=yes")
sk_setup(get="raise"); skc("1701 get raises: set not called", _SKQ + "&go=yes", keys=_SKR)
sk_setup(len_raises=True); skc("1702 len raises               ", _SKQ + "&go=yes", keys=_SKR)
for tag, over in (("1703 no font open        ", dict(count=0)), ("1704 two fonts open      ", dict(count=2)), ("1705 two packages        ", dict(packages=2))):
    sk_setup(**over); skc(tag, _SKQ + "&go=yes")
sk_setup(calls=9); skc("1706 request 10 allowed       ", _SKQ + "&go=yes", keys=("calls_so_far", "max_calls"))
SK["kerning_args"].clear(); SK["sets"].clear(); SK["groups_calls"] = 0; skc("1707 request 11 refused       ", _SKQ + "&go=yes")
sk_setup(); _sk_real = ns["debug_try_set_kern"]
ns["debug_try_set_kern"] = _pk_boom; skc("1708 probe raises: HTTP 500    ", _SKQ + "&go=yes"); ns["debug_try_set_kern"] = _sk_real
sk_setup()
for _p in (_SKQ, _SKQ + "&go=yes", _SKQ + "&form=flags&go=yes"): call(_p)
print("1709 spy over all cases          : forbidden package members:", SK["pkg_forbidden"], "| package members touched anywhere:", sorted(SK["pkg_all"]),
      "| forbidden kerning members:", SK["k_forbidden"], "| kerning members touched anywhere:", sorted(SK["k_all"]))
_sk_src = src[src.index("_TRYSETKERN = {"):src.index("# /debug/trydelkern (v0.191)")]
_sk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _sk_src).splitlines())
print("1710 static scan                 : pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _sk_code))), "| kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _sk_code))),
      "| setter( calls:", len(_re83.findall(r"\bsetter\(", _sk_code)), "| kerning_of( calls:", len(_re83.findall(r"\bkerning_of\(", _sk_code)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|Update\w*|add\w*|clear\w*|keys|values|items|has_key|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*|autoKern|findGroup)\(", _sk_code),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _sk_code) if s not in ("_TRYSETKERN", "before", "after", "entry", "kern", "classes", "g", "_TRYKERN_SIDE_FITS")],
      "| counter raised before the first kerning call:", _sk_code.index('_TRYSETKERN[""] += 1') < _sk_code.index("kerning_of(current)") < _sk_code.index("setter(key"),
      "| scanned chars > 3000:", len(_sk_src) > 3000)
print("1711 gate, cap, route, docstring  :", "go != \"yes\"" in _sk_src, "| max requests", ns["_TRYSETKERN_MAX"], "| route registered once:", src.count('path == "/debug/trysetkern"') == 1,
      "| listed in the module docstring:", "/debug/trysetkern" in src[:src.index('"""', 3)])
ns["_TRYSETKERN"]["calls"] = 0

# ================= v0.191: /debug/trydelkern (gated research probe that WRITES: flPackage.kerning(master).remove(key) once) =================
print("\n==== v0.191 /debug/trydelkern ====")
_DK_K_FORBIDDEN = tuple(n for n in _FK_FORBIDDEN if n != "remove")
def dk_setup(calls=0, **cfg):
    sk_setup(k_forbid=_DK_K_FORBIDDEN, **cfg)
    SK["removes"] = []
    ns["_TRYDELKERN"]["calls"] = calls
def dkc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| kerning() args", SK["kerning_args"], "| removes", SK["removes"], "| sets", SK["sets"], "| getAllGroups calls", SK["groups_calls"])
    return c, d
_DKT = {("ks1L", "ks1R"): -100.0, ("ks1R", "ks1L"): 20.0}
_DKQ = "/debug/trydelkern?a=ks1L&b=ks1R"
_DKR = ("remove_called", "remove_error", "remove_returned", "exact_before", "exact_after", "removed", "len_before", "len_after", "table_size_changed", "calls_so_far")
dk_setup(table=_DKT); dkc("2633 no go: nothing runs        ", _DKQ)
dk_setup(table=_DKT); dkc("2634 go=maybe: nothing runs     ", _DKQ + "&go=maybe")
dk_setup(table=_DKT); c, d = dkc("2635 tuple form, existing pair  ", _DKQ + "&go=yes")
print("2635b note: may change, no mark, no save:", "may have changed" in d.get("note", "") and "not marked" in d.get("note", "") and "nothing is saved" in d.get("note", ""))
dk_setup(table=_DKT); dkc("2636 flags form, existing pair  ", _DKQ + "&form=flags&go=yes", keys=("call",) + _DKR)
dk_setup(table=_DKT); dkc("2637 pair with no entry          ", "/debug/trydelkern?a=ks1L&b=ks1S&form=flags&go=yes", keys=_DKR)
dk_setup(table=_DKT, remove="raise"); dkc("2638 remove raises (counted)    ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, remove="pop_then_raise"); dkc("2638b remove raises after removing", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, get="raise_after_remove"); dkc("2638c read after remove fails  ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, remove="ignore"); dkc("2639 remove changes nothing     ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, remove="zero"); dkc("2640 remove leaves a 0 entry    ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table={**_DKT, ("ks1S", "ks1S"): 5.0}, remove="two"); dkc("2641 remove takes two entries   ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, get="raise"); dkc("2642 get raises: remove not called", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT, len_raises=True); dkc("2643 len raises: not removed    ", _DKQ + "&go=yes", keys=_DKR)
dk_setup(table=_DKT); dkc("2644 bad form                   ", _DKQ + "&form=plain&go=yes")
for bad in ("", "A:V", "x" * 64):
    dk_setup(table=_DKT); dkc(f"2645 bad name b {bad[:12]!r:14}", "/debug/trydelkern?a=ks1L&b=" + bad + "&go=yes")
dk_setup(table=_DKT); dkc("2646 unknown glyph            ", "/debug/trydelkern?a=Q&b=ks1R&go=yes")
dk_setup(table=_DKT, groups=[_SKG("ks1R")]); dkc("2647 b is also a group: refused", _DKQ + "&go=yes")
dk_setup(table=_DKT, groups=[[False, "ks1L", 3, 0, ["ks1L"]]]); dkc("2648 a names a non-kerning group", _DKQ + "&go=yes")
dk_setup(table=_DKT, groups=[_SKG("ks1grp")]); dkc("2649 other group: allowed      ", _DKQ + "&go=yes", keys=("removed", "calls_so_far"))
for tag, over in (("2650 getAllGroups raises ", dict(groups="raise")), ("2650 getAllGroups a dict", dict(groups={"ks1R": 1}))):
    dk_setup(table=_DKT, **over); dkc(tag, _DKQ + "&go=yes")
dk_setup(table=_DKT, masters=["Regular", 5]); dkc("2651 masters not all names    ", _DKQ + "&go=yes")
dk_setup(table=_DKT, master="Ghost"); dkc("2652 current master unlisted  ", _DKQ + "&go=yes")
dk_setup(table=_DKT, kerning_call="raise"); dkc("2653 kerning() raises (counted)", _DKQ + "&go=yes")
for tag, over in (("2654 no font open        ", dict(count=0)), ("2655 two fonts open      ", dict(count=2)), ("2656 two packages        ", dict(packages=2))):
    dk_setup(table=_DKT, **over); dkc(tag, _DKQ + "&go=yes")
dk_setup(calls=9, table=_DKT); dkc("2657 request 10 allowed       ", _DKQ + "&go=yes", keys=("removed", "calls_so_far", "max_calls"))
SK["kerning_args"].clear(); SK["removes"].clear(); SK["groups_calls"] = 0; dkc("2658 request 11 refused       ", _DKQ + "&go=yes")
dk_setup(table=_DKT); _dk_real = ns["debug_try_del_kern"]
ns["debug_try_del_kern"] = _pk_boom; dkc("2659 probe raises: HTTP 500    ", _DKQ + "&go=yes"); ns["debug_try_del_kern"] = _dk_real
dk_setup(table=_DKT)
SK["pkg_all"].clear(); SK["k_all"].clear(); SK["pkg_forbidden"].clear(); SK["k_forbidden"].clear()
for _p in (_DKQ, _DKQ + "&go=yes", "/debug/trydelkern?a=ks1R&b=ks1L&form=flags&go=yes", "/debug/trydelkern?a=ks1L&b=ks1S&go=yes"): call(_p)
print("2660 spy over all cases          : forbidden package members:", SK["pkg_forbidden"], "| package members touched anywhere:", sorted(SK["pkg_all"]),
      "| forbidden kerning members:", SK["k_forbidden"], "| kerning members touched anywhere:", sorted(SK["k_all"]), "| sets", SK["sets"])
_dk_src = src[src.index("_TRYDELKERN = {"):src.index("# /debug/trykernrefresh (v0.123)")]
_dk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _dk_src).splitlines())
print("2661 static scan                 : pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _dk_code))), "| kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _dk_code))),
      "| remover( calls:", len(_re83.findall(r"\bremover\(", _dk_code)), "| kerning_of( calls:", len(_re83.findall(r"\bkerning_of\(", _dk_code)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|Update\w*|add\w*|clear\w*|keys|values|items|has_key|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*|autoKern|findGroup|set|notify\w*)\(", _dk_code),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _dk_code) if s not in ("_TRYDELKERN", "before", "after")],
      "| counter raised before the first kerning call:", _dk_code.index('_TRYDELKERN[""] += 1') < _dk_code.index("kerning_of(current)") < _dk_code.index("remover(key"),
      "| scanned chars > 3000:", len(_dk_src) > 3000)
print("2662 gate, cap, route, docstring  :", "go != \"yes\"" in _dk_src, "| max requests", ns["_TRYDELKERN_MAX"], "| route registered once:", src.count('path == "/debug/trydelkern"') == 1,
      "| listed in the module docstring:", "/debug/trydelkern" in src[:src.index('"""', 3)])
ns["_TRYDELKERN"]["calls"] = 0

# ================= v0.193: class sides in /debug/trysetkern and /debug/trydelkern (class-write research CW, gated, WRITES) =================
print("\n==== v0.193 class sides in /debug/trysetkern and /debug/trydelkern ====")
_CW_KF = tuple(n for n in _SK_K_FORBIDDEN if n != "groups")
_CW_DKF = tuple(n for n in _DK_K_FORBIDDEN if n != "groups")
_CWG = [[True, "cwL", 5121, 0, ["ks1L", "ks1S"]], [True, "cwR", 5122, 0, ["ks1R"]], [True, "cwB", 5123, 0, ["ks1S"]], [False, "cwF", 5125, 0, ["ks1L"]]]
_CWI = [("cwL", (["ks1L", "ks1S"], "KernLeft")), ("cwB", (["ks1S"], "KernBothSide")), ("cwR", (["ks1R"], "KernRight"))]
def cw_setup(calls=0, remove=False, **cfg):
    base = dict(groups=_CWG, items=_CWI, k_forbid=_CW_DKF if remove else _CW_KF)
    base.update(cfg)
    sk_setup(calls=calls, **base)
    SK["removes"] = []; SK["g_all"] = set(); SK["g_forbidden"] = []
    ns["_TRYDELKERN"]["calls"] = calls
def cwc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| kerning() args", SK["kerning_args"], "| sets", SK["sets"], "| removes", SK["removes"], "| getAllGroups calls", SK["groups_calls"],
          "| group container members", sorted(SK["g_all"]))
    return c, d
_CWS = "/debug/trysetkern?form=flags&go=yes"
_CWD = "/debug/trydelkern?form=flags&go=yes"
_CWR = ("call", "error", "left", "right", "classes", "exact_before", "exact_after", "read_back_matches", "len_before", "len_after", "groups_len_before", "groups_len_after", "calls_so_far")
_CWX = ("call", "error", "left", "right", "classes", "exact_before", "exact_after", "removed", "len_before", "len_after", "groups_len_before", "groups_len_after", "calls_so_far")
cw_setup(); cwc("2748 class : class cwL:cwR -80   ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(); cwc("2749 glyph : class ks1L:cwR -50  ", _CWS + "&a=ks1L&b=cwR&right=class&value=-50", keys=_CWR)
cw_setup(); cwc("2750 class : glyph cwL:ks1R -30  ", _CWS + "&a=cwL&b=ks1R&left=class&value=-30", keys=_CWR)
cw_setup(); cwc("2751 both class on both sides     ", _CWS + "&a=cwB&b=cwB&left=class&right=class&value=-20", keys=_CWR)
cw_setup(table={("ks1L", "ks1R"): -100.0}); cwc("2752 glyph pair of members kept apart", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(); cwc("2753 class side, form=tuple       ", "/debug/trysetkern?a=cwL&b=cwR&left=class&right=class&value=-80&go=yes")
cw_setup(); cwc("2754 left=group: refused          ", _CWS + "&a=cwL&b=cwR&left=group&right=class&value=-80")
cw_setup(); cwc("2755 unknown class name           ", _CWS + "&a=cwQ&b=cwR&left=class&right=class&value=-80")
cw_setup(); cwc("2756 an OpenType class            ", _CWS + "&a=cwF&b=cwR&left=class&right=class&value=-80")
cw_setup(); cwc("2757 right group on the left      ", _CWS + "&a=cwR&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(); cwc("2758 left group on the right      ", _CWS + "&a=ks1L&b=cwL&right=class&value=-80", keys=_CWR)
cw_setup(items=[e for e in _CWI if e[0] != "cwR"]); cwc("2759 class list only, not items()  ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(items=[("cwL", (["ks1L"], "KernLeft"))] + _CWI[1:]); cwc("2760 members differ               ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(groups=_CWG + [[True, "cwL", 5126, 0, ["ks1L", "ks1S"]]]); cwc("2761 class list names it twice    ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(items=[("cwL", (["ks1L", "ks1S"], "KernTop"))] + _CWI[1:]); cwc("2762 an unknown side word        ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(items="raise"); cwc("2763 items() raises               ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(groups_attr="raise"); cwc("2764 kerning.groups raises        ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(groups_attr="callable"); cwc("2765 kerning.groups callable      ", _CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", keys=_CWR)
cw_setup(groups=_CWG + [[True, "ks1S", 5127, 0, ["ks1S"]]], items=_CWI + [("ks1S", (["ks1S"], "KernBothSide"))])
cwc("2766 class named like a glyph      ", _CWS + "&a=cwL&b=ks1S&left=class&right=class&value=-10", keys=("call", "error", "read_back_matches", "calls_so_far"))
cw_setup(groups=_CWG + [[True, "ks1S", 5127, 0, ["ks1S"]]], items=_CWI + [("ks1S", (["ks1S"], "KernBothSide"))])
cwc("2766b the same name as a glyph side", _CWS + "&a=cwL&b=ks1S&left=class&value=-10")
cw_setup(); cwc("2767 a missing glyph on a glyph side", _CWS + "&a=cwL&b=Q&left=class&value=-10")
cw_setup(k_forbid=_SK_K_FORBIDDEN); cwc("2768 glyph pair: groups untouched ", _CWS + "&a=ks1L&b=ks1R&value=-10", keys=("call", "read_back_matches", "classes", "groups_len_before"))
_CWT = {(("cwL", True), ("cwR", True)): -80.0, ("ks1L", "ks1R"): -100.0, (("ks1L", False), ("cwR", True)): -50.0}
cw_setup(remove=True, table=_CWT); cwc("2769 remove class : class         ", _CWD + "&a=cwL&b=cwR&left=class&right=class", keys=_CWX)
cw_setup(remove=True, table=_CWT); cwc("2770 remove glyph : class         ", _CWD + "&a=ks1L&b=cwR&right=class", keys=_CWX)
cw_setup(remove=True, table=_CWT); cwc("2771 remove: no class entry       ", _CWD + "&a=cwB&b=cwB&left=class&right=class", keys=_CWX)
cw_setup(remove=True, table=_CWT); cwc("2772 remove: right group on left  ", _CWD + "&a=cwR&b=ks1R&left=class", keys=_CWX)
cw_setup(remove=True, table=_CWT); cwc("2773 remove: class with form=tuple", "/debug/trydelkern?a=cwL&b=cwR&left=class&right=class&go=yes")
cw_setup(remove=True, table=_CWT); cwc("2774 remove: an OpenType class    ", _CWD + "&a=cwF&b=cwR&left=class&right=class")
cw_setup(remove=True, table=_CWT, items="raise"); cwc("2775 remove: items() raises      ", _CWD + "&a=cwL&b=cwR&left=class&right=class", keys=_CWX)
cw_setup(); SK["pkg_all"].clear(); SK["k_all"].clear(); SK["pkg_forbidden"].clear(); SK["k_forbidden"].clear()
for _p in (_CWS + "&a=cwL&b=cwR&left=class&right=class&value=-80", _CWS + "&a=ks1L&b=cwR&right=class&value=-50", _CWS + "&a=cwR&b=cwR&left=class&right=class&value=-80"): call(_p)
SK["cfg"]["k_forbid"] = _CW_DKF
for _p in (_CWD + "&a=cwL&b=cwR&left=class&right=class", _CWD + "&a=ks1L&b=ks1R"): call(_p)
print("2776 spy over the class cases     : forbidden package members:", SK["pkg_forbidden"], "| package members touched anywhere:", sorted(SK["pkg_all"]),
      "| forbidden kerning members:", SK["k_forbidden"], "| kerning members touched anywhere:", sorted(SK["k_all"]),
      "| forbidden group container members:", SK["g_forbidden"], "| group container members touched:", sorted(SK["g_all"]))
_cw_src = src[src.index("_TRYKERN_KINDS = ("):src.index("def debug_try_set_kern(")] + _rag_src
_cw_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _cw_src).splitlines())
print("2777 static scan of the class checks: pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _cw_code))),
      "| kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _cw_code))), "| container members used:", sorted(set(_re83.findall(r"\bcontainer\.(\w+)", _cw_code))),
      "| getter( calls:", len(_re83.findall(r"\bgetter\(", _cw_code)), "| _kgr_from_items( calls:", len(_re83.findall(r"\b_kgr_from_items\(", _cw_code)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|Update\w*|add\w*|clear\w*|keys|values|items|has_key|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*|autoKern|findGroup|set|notify\w*)\(", _cw_code),
      "| .get( only on the plain dict g:", sorted(set(_re83.findall(r"\b(\w+)\.get\(", _cw_code))),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _cw_code) if s not in ("entry", "kern", "classes", "g", "_TRYKERN_SIDE_FITS")],
      "| scanned chars > 2000:", len(_cw_src) > 2000)
print("2778 routes and docstring        : left / right read in the routes:", src.count('(query.get("left") or ["glyph"])[0]'), src.count('(query.get("right") or ["glyph"])[0]'),
      "| class key built from the sides:", src.count('exact = ((a, left == "class"), (b, right == "class"))'),
      "| listed in the module docstring:", "&left=glyph|class&right=glyph|class" in src[:src.index('"""', 3)])
ns["_TRYSETKERN"]["calls"] = 0; ns["_TRYDELKERN"]["calls"] = 0
for _m, _a, _v in _sk_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYSETKERN"]["calls"] = 0

# ================= v0.123: /debug/trykernrefresh (gated research probe: flPackage.kerningContainer(), then fontlab.Update(container) or container.changed()) =================
print("\n==== v0.123 /debug/trykernrefresh ====")
RK = {"cfg": {}, "pkg_all": set(), "pkg_forbidden": [], "c_all": set(), "c_forbidden": [], "k_all": set(), "k_forbidden": [], "updates": [],
      "changed": 0, "container_calls": 0, "kerning_args": [], "mod_forbidden": []}
_RK_PKG_FORBIDDEN = tuple(n for n in _PK_PKG_FORBIDDEN if n != "kerningContainer") + ("setFlag", "clearFlag", "clearFlags", "restoreHistoryState",
                                                                                       "clearAboveHistory", "changed")
_RK_C_FORBIDDEN = ("update", "remove", "release", "removeChild", "setFlag", "clearFlag", "clearFlags", "restoreHistoryState", "clearAboveHistory",
                   "clone", "cloneObject", "createObject", "setProperty", "setPropertyFloat", "setPropertyInt")
class RKKern:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            RK["k_all"].add(n)
            RK["k_forbidden"].append(n)
            raise SystemExit("FORBIDDEN kerning member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self): return RK["cfg"].get("table_len", 2)
class RKContainer:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            RK["c_all"].add(n)
            if n in _RK_C_FORBIDDEN:
                RK["c_forbidden"].append(n)
                raise SystemExit("FORBIDDEN container member touched: " + n)
            if n == "changed" and RK["cfg"].get("changed") == "not_callable": return 5
        return object.__getattribute__(self, n)
    def isNull(self):
        v = RK["cfg"].get("c_isNull", False)
        if isinstance(v, Exception): raise v
        return v
    @property
    def id(self): return 77
    def name(self): return "kerning"
    @property
    def isChanged(self):
        if RK["cfg"].get("flags_raise"): raise RuntimeError("flag boom")
        return RK["changed"] > 0 or len(RK["updates"]) > 0
    @property
    def hasChanges(self): return False
    def changed(self):
        if RK["cfg"].get("changed") == "raise": raise RuntimeError("changed boom")
        RK["changed"] += 1
class RKPackage:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            RK["pkg_all"].add(n)
            if n in _RK_PKG_FORBIDDEN:
                RK["pkg_forbidden"].append(n)
                raise SystemExit("FORBIDDEN package member touched: " + n)
        return object.__getattribute__(self, n)
    def isNull(self): return False
    @property
    def masters(self): return RK["cfg"].get("masters", ["Regular"])
    @property
    def master(self): return "Regular"
    @property
    def isChanged(self): return True
    @property
    def hasChanges(self): return True
    @property
    def kerning(self):
        def _kerning(*args):
            RK["kerning_args"].append(args)
            if RK["cfg"].get("kerning_call") == "raise": raise RuntimeError("kerning() boom")
            return RKKern()
        return _kerning
    @property
    def kerningContainer(self):
        v = RK["cfg"].get("container_attr")
        if v == "not_callable": return 5
        def _container():
            RK["container_calls"] += 1
            m = RK["cfg"].get("container")
            if m == "raise": raise RuntimeError("container boom")
            if m == "none": return None
            return RK_C
        return _container
class RKWorkspace:
    @staticmethod
    def instance(): return RK_WS
    def packages(self): return [RK_PKG] * RK["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return RK_PKG
RK_PKG = RKPackage(); RK_WS = RKWorkspace(); RK_C = RKContainer()
def _rk_update(*args):
    RK["updates"].append(tuple(type(a).__name__ for a in args))
    if RK["cfg"].get("update") == "raise": raise RuntimeError("Update boom")
    return True
def _rk_forbidden(name):
    def _f(*a):
        RK["mod_forbidden"].append(name)
        raise SystemExit("FORBIDDEN module call: " + name)
    return _f
_rk_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace", "Update", "UpdateAll")]
def rk_setup(calls=0, **cfg):
    RK["cfg"] = dict(cfg)
    RK["updates"].clear(); RK["kerning_args"].clear(); RK["changed"] = 0; RK["container_calls"] = 0
    ns["_TRYKERNREFRESH"]["calls"] = calls
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = RKWorkspace
        _m.CountFonts = lambda: count
        _m.CurrentFont = lambda: SKFont()
        _m.UpdateAll = _rk_forbidden("UpdateAll")
        if cfg.get("no_update"):
            if hasattr(_m, "Update"): delattr(_m, "Update")
        else:
            _m.Update = _rk_update
def rkc(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k not in ("note", "container_public_names")} if keys is None else {k: d.get(k) for k in keys}
    print(tag, ":", c, shown, "| kerningContainer() calls", RK["container_calls"], "| Update args", RK["updates"], "| changed() calls", RK["changed"])
    return c, d
_RKQ = "/debug/trykernrefresh?stage="
_RKR = ("call", "call_error", "returned_type", "returned", "container_flags_before", "container_flags_after", "calls_so_far")
rk_setup(); rkc("1712 no go: nothing runs        ", _RKQ + "update")
rk_setup(); rkc("1713 bad stage                  ", _RKQ + "all&go=yes")
rk_setup(); c, d = rkc("1714 stage=container            ", _RKQ + "container&go=yes")
print("1714b public names reported       :", isinstance(d.get("container_public_names"), list) and "changed" in d["container_public_names"], "| note:",
      "nothing is saved" in d.get("note", ""))
rk_setup(); rkc("1715 stage=update               ", _RKQ + "update&go=yes")
rk_setup(); rkc("1716 stage=changed              ", _RKQ + "changed&go=yes", keys=_RKR)
rk_setup(update="raise"); rkc("1717 Update raises (counted)    ", _RKQ + "update&go=yes", keys=_RKR)
rk_setup(changed="raise"); rkc("1718 changed raises            ", _RKQ + "changed&go=yes", keys=_RKR)
rk_setup(changed="not_callable"); rkc("1718b changed not callable    ", _RKQ + "changed&go=yes", keys=_RKR)
rk_setup(c_isNull=True); rkc("1719 container null: not called ", _RKQ + "update&go=yes", keys=("container_isNull",) + _RKR)
rk_setup(c_isNull=RuntimeError("null boom")); rkc("1720 isNull raises: not called  ", _RKQ + "changed&go=yes", keys=("container_isNull",) + _RKR)
rk_setup(container="raise"); rkc("1721 kerningContainer raises    ", _RKQ + "update&go=yes")
rk_setup(container="none"); rkc("1722 kerningContainer None      ", _RKQ + "update&go=yes")
rk_setup(no_update=True); rkc("1723 no fontlab.Update: refused  ", _RKQ + "update&go=yes")
rk_setup(no_update=True); rkc("1723b ... not needed for changed", _RKQ + "changed&go=yes", keys=("call", "call_error", "calls_so_far"))
rk_setup(container_attr="not_callable"); rkc("1724 kerningContainer not callable", _RKQ + "update&go=yes")
rk_setup(kerning_call="raise"); rkc("1725 kerning() raises          ", _RKQ + "update&go=yes", keys=("kerning_error", "call", "call_error", "kerning_len_before", "table_size_changed"))
rk_setup(flags_raise=True); rkc("1726 a flag read raises         ", _RKQ + "update&go=yes", keys=("container_flags_before", "container_flags_after", "call_error"))
rk_setup(masters=["Regular", 5]); rkc("1727 masters not all names     ", _RKQ + "update&go=yes")
for tag, over in (("1728 no font open        ", dict(count=0)), ("1729 two fonts open      ", dict(count=2)), ("1730 two packages        ", dict(packages=2))):
    rk_setup(**over); rkc(tag, _RKQ + "update&go=yes")
rk_setup(calls=5); rkc("1731 request 6 allowed        ", _RKQ + "update&go=yes", keys=("calls_so_far", "max_calls"))
RK["updates"].clear(); RK["container_calls"] = 0; rkc("1732 request 7 refused        ", _RKQ + "update&go=yes")
rk_setup(); _rk_real = ns["debug_try_kern_refresh"]
ns["debug_try_kern_refresh"] = _pk_boom; rkc("1733 probe raises: HTTP 500    ", _RKQ + "update&go=yes"); ns["debug_try_kern_refresh"] = _rk_real
rk_setup()
for _p in (_RKQ + "update", _RKQ + "container&go=yes", _RKQ + "update&go=yes", _RKQ + "changed&go=yes"): call(_p)
print("1734 spy over all cases          : forbidden package members:", RK["pkg_forbidden"], "| package members touched:", sorted(RK["pkg_all"]),
      "| forbidden container members:", RK["c_forbidden"], "| container members touched:", sorted(RK["c_all"]),
      "| kerning members touched:", sorted(RK["k_all"]), "| forbidden module calls:", RK["mod_forbidden"])
_rk_src = src[src.index("_TRYKERNREFRESH = {"):src.index("# /debug/trykerngroupedit (v0.199)")]
_rk_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _rk_src).splitlines())
print("1735 static scan                 : pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _rk_code))), "| container members used:",
      sorted(set(_re83.findall(r"\bcontainer\.(\w+)", _rk_code))), "| updater( calls:", _re83.findall(r"\bupdater\([^)]*\)", _rk_code),
      "| mark( calls:", len(_re83.findall(r"\bmark\(", _rk_code)), "| container_of( calls:", len(_re83.findall(r"\bcontainer_of\(", _rk_code)),
      "| forbidden syntax:", _re83.findall(r"\b(?:UpdateAll|Update\(\)|save\w*\(|\.release\(|\.remove\w*\(|(?<!\bout)\.update\(|\.setFlag\(|\.clearFlag\w*\(|\.set\(|\.restoreHistoryState\(|\.clearAboveHistory\()", _rk_code),
      "| subscripts on other objects:", [s for s in _re83.findall(r"\b(\w+)\[", _rk_code) if s not in ("_TRYKERNREFRESH", "out")],
      "| counter raised before the first call:", _rk_code.index('_TRYKERNREFRESH[""] += 1') < _rk_code.index("kerning_of(current)") < _rk_code.index("container_of()"),
      "| scanned chars > 3000:", len(_rk_src) > 3000)
print("1736 gate, cap, route, docstring  :", "go != \"yes\"" in _rk_src, "| max requests", ns["_TRYKERNREFRESH_MAX"],
      "| route registered once:", src.count('path == "/debug/trykernrefresh"') == 1, "| listed in the module docstring:", "/debug/trykernrefresh" in src[:src.index('"""', 3)])
for _m, _a, _v in _rk_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
ns["_TRYKERNREFRESH"]["calls"] = 0

# ================= v0.124: POST /kerning/set (writes glyph : glyph pairs with the flags key; verified by re-reading; spies) =================
print("\n==== v0.124 POST /kerning/set ====")
# The /kerning/pairs fakes above (KP, KPFont, KPPackage, the glyph list and _KP_TABLE) with a kerning table that can be SET:
# KSKern allows set and nothing else that writes; every set key must be the flags form ((a, False), (b, False)).
KS = {"new": {}, "sets": [], "set_mode": None, "extra": 0, "after_set_get": None, "flaky": set()}
_KS_FORBIDDEN = tuple(n for n in _KP_FORBIDDEN if n != "set")
class KSKern(KPKern):
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KP["touched"].append(n); KP["all_touched"].add(n)
            if n in _KS_FORBIDDEN:
                KP["forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "set" and KS["set_mode"] == "not_callable": return 9
            if n == "set" and KS["set_mode"] == "no_attr": raise AttributeError("set is missing")
        return object.__getattribute__(self, n)
    def __len__(self):
        if KP["len_raises"]: raise RuntimeError("len boom")
        fresh = sum(1 for k in KS["new"] if _KP_TABLE.get(k) is None and not isinstance(KP["mode"].get(k), float))
        return KP["len"] + fresh + (KS["extra"] if KS["sets"] else 0)
    def get(self, pair):
        scripted = KS["script"].get(pair)
        if scripted:                       # answers for one key, one per get, in order: before (effective, exact), after (exact, effective)
            KP["gets"].append(pair); v = scripted.pop(0)
            if isinstance(v, Exception): raise v
            return v
        if KS["sets"] and KS["after_set_get"] == "raise" and pair in KS["new"]:
            KP["gets"].append(pair); raise RuntimeError("get boom after set")
        if pair in KS["flaky"]:
            KS["flaky"].discard(pair); KP["gets"].append(pair); return KS["new"].get(pair)
        if pair in KS["new"] and pair not in KS.get("hidden", ()):
            KP["gets"].append(pair); return KS["new"][pair]
        return KPKern.get(self, pair)
    def set(self, key, value):
        KS["sets"].append((key, value))
        flagged = (isinstance(key, tuple) and len(key) == 2 and all(isinstance(p, tuple) and len(p) == 2 and p[1] is False for p in key))
        if not flagged:
            KP["forbidden"].append("set with key " + repr(key)); KP["ever"].append("set key " + repr(key)); return None
        m = KS["set_mode"]
        if isinstance(m, dict): m = m.get((key[0][0], key[1][0]))
        if m == "raise": raise RuntimeError("set boom")
        if m == "ignore": return None
        if m == "round": value = float(round(value))
        if m == "flaky": KS["flaky"].add(key); KS.setdefault("hidden", set()).add(key)
        KS["new"][key] = value
        if m == "raise_after": raise RuntimeError("set boom after writing")
        return None
def ks_setup(set_mode=None, extra=0, after_set_get=None, script=None, **cfg):
    kp_setup(kern_factory=KSKern, **cfg)
    KS.update(new={}, sets=[], set_mode=set_mode, extra=extra, after_set_get=after_set_get, flaky=set(), hidden=set(),
              script={k: list(v) for k, v in (script or {}).items()})
def ksp(tag, payload, raw=False):
    body = payload if raw else json.dumps(payload).encode("utf-8")
    r = ns["_route"]("POST", "/kerning/set", body); h, _, b = r.partition(b"\r\n\r\n")
    c, d = h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
    print(tag, ":", c, {k: v for k, v in d.items() if k != "results"}, "| set calls", KS["sets"], "| forbidden", list(KP["forbidden"]))
    for r_ in d.get("results") or []:
        print("      ", r_)
    return c, d
_ks_cf = getattr(fl, "CountFonts", None); _ks_cur = fl.CurrentFont; _ks_ws = getattr(fl, "flWorkspace", None)
KP["ever"].clear()
ks_setup(); ksp("2000 a new pair                  ", {"pairs": [["A", "B", -60]]})
ks_setup(); ksp("2001 an existing pair changed    ", {"pairs": [["A", "V", -100]]})
ks_setup(); ksp("2002 the same value again        ", {"pairs": [["A", "V", -152]]})
ks_setup(); ksp("2003 over a class : class value  ", {"pairs": [["Aacute", "Wgrave.c2sc", -30]]})
print("2003b keys asked, in order        :", KP["gets"])
ks_setup(); ksp("2004 three pairs                 ", {"pairs": [["A", "B", -60], ["T", "o", -200], ["V", "A", 10.5]]})
ks_setup(); ksp("2005 zero: an explicit entry     ", {"pairs": [["A", "B", 0]]})
ks_setup(); ksp("2006 defect B: glyph Aring, class Aring exists", {"pairs": [["Aring", "V", -45]]})
ks_setup(upm=1000.0); ksp("2007 |value| = upm is allowed    ", {"pairs": [["A", "B", -1000]]})
ks_setup(count=2); ksp("2008 two fonts, matched by path  ", {"pairs": [["A", "B", -60]]})
print("--- refused before any write (set calls must stay empty)")
ks_setup(); ksp("2010 unknown glyphs              ", {"pairs": [["A", "B", -60], ["Q", "V", -10], ["A", "Zz", 5]]})
ks_setup(upm=1000.0); ksp("2011 a value above upm           ", {"pairs": [["A", "B", -60], ["T", "o", -1000.5]]})
for _tag, _u in (("2012 upm raises                 ", RuntimeError("upm boom")), ("2012b upm is 0                  ", 0), ("2012c upm is True               ", True), ("2012d upm is text               ", "1000")):
    ks_setup(upm=_u); ksp(_tag, {"pairs": [["A", "B", -60]]})
for _tag, _p in (("2013 pairs empty                ", []), ("2013b pairs not a list         ", {"A": "B"}), ("2013c an item of two           ", [["A", "B"]]),
                 ("2013d a name with a space       ", [["A B", "V", -10]]), ("2013e a value that is True     ", [["A", "V", True]]), ("2013f a value as text          ", [["A", "V", "-10"]]),
                 ("2013g a pair twice              ", [["A", "V", -10], ["T", "o", 5], ["A", "V", -12]]), ("2013h a tuple-like item       ", ["AV-10"]), ("2013i a value of null           ", [["A", "V", None]])):
    ks_setup(); ksp(_tag, {"pairs": _p})
ks_setup(); ksp("2013j NaN                        ", b'{"pairs": [["A", "V", NaN]]}', raw=True)
ks_setup(); ksp("2013k Infinity                   ", b'{"pairs": [["A", "V", -Infinity]]}', raw=True)
ks_setup(); ksp("2013l another key in the body    ", {"pairs": [["A", "V", -10]], "go": "yes"})
ks_setup(); ksp("2013m no pairs key              ", {"pair": [["A", "V", -10]]})
ks_setup(); ksp("2013n body not JSON              ", b"pairs=A:V:-10", raw=True)
ks_setup(); ksp("2013o body empty                 ", b"", raw=True)
ks_setup(count=0); ksp("2014 no font open (CountFonts 0)  ", {"pairs": [["A", "V", -10]]})
ks_setup(cur=None); ksp("2014b CurrentFont None          ", {"pairs": [["A", "V", -10]]})
ks_setup(count=None); ksp("2014c CountFonts gives None     ", {"pairs": [["A", "V", -10]]})
ks_setup(count=2, pkg_path="C:/fonts/other.vfc"); ksp("2015 two fonts, paths differ     ", {"pairs": [["A", "V", -10]]})
ks_setup(count=2, font_path=""); ksp("2015b two fonts, an unsaved one in front", {"pairs": [["A", "V", -10]]})
ks_setup(master="Ghost"); ksp("2016 current master unlisted     ", {"pairs": [["A", "V", -10]]})
ks_setup(kerning_call=RuntimeError("kerning() boom")); ksp("2016b kerning(master) raises   ", {"pairs": [["A", "V", -10]]})
ks_setup(set_mode="not_callable"); ksp("2017 set not callable            ", {"pairs": [["A", "V", -10]]})
ks_setup(set_mode="no_attr"); ksp("2017b set missing               ", {"pairs": [["A", "V", -10]]})
print("--- failures while writing: the request stops at the first pair not confirmed")
ks_setup(ids={"T": (RuntimeError("left boom"), 0)}); ksp("2018 value before unreadable     ", {"pairs": [["A", "B", -60], ["T", "o", -200], ["V", "A", -10]]})
ks_setup(mode={("T", "o"): "raise"}); ksp("2018b get raises before the write", {"pairs": [["T", "o", -200], ["A", "B", -60]]})
ks_setup(set_mode={("T", "o"): "raise"}); ksp("2020 set raises on pair 2 of 3   ", {"pairs": [["A", "B", -60], ["T", "o", -200], ["V", "A", -10]]})
ks_setup(set_mode="ignore"); ksp("2021 set does nothing            ", {"pairs": [["A", "B", -60]]})
ks_setup(set_mode="round"); ksp("2022 FontLab rounds the value    ", {"pairs": [["A", "B", -12.5]]})
ks_setup(set_mode="raise_after"); ksp("2023 set writes, then raises     ", {"pairs": [["A", "B", -60], ["T", "o", -200]]})
ks_setup(after_set_get="raise"); ksp("2024 read back raises            ", {"pairs": [["A", "B", -60]]})
ks_setup(set_mode="flaky"); ksp("2025 class value answers after   ", {"pairs": [["Aacute", "Wgrave.c2sc", -30]]})
_ks_aw, _ks_ab = (("Aacute", False), ("Wgrave.c2sc", False)), (("A", False), ("B", False))
ks_setup(script={_ks_aw: [None, None, -76.0, None]}); ksp("2025b a class gives the same value", {"pairs": [["Aacute", "Wgrave.c2sc", -76]]})
ks_setup(script={_ks_ab: [None, None, -61.0, -60.0]}); ksp("2025c the exact entry reads wrong", {"pairs": [["A", "B", -60]]})
ks_setup(script={_ks_ab: [None, "text"]}); ksp("2018c exact entry unreadable before", {"pairs": [["A", "B", -60], ["T", "o", -200]]})
ks_setup(extra=1); ksp("2026 table grew by one too many  ", {"pairs": [["A", "B", -60]]})
KP["len_raises"] = False; ks_setup(); KP["len_raises"] = True; ksp("2027 len() raises               ", {"pairs": [["A", "B", -60]]})
print("2030 spy over the set cases       : forbidden members touched:", [f for f in KP["ever"]], "| plain set keys: none above")
_ks_real = ns["set_kerning_pairs"]
def _ks_boom(pairs): raise RuntimeError("set boom in the route")
ns["set_kerning_pairs"] = _ks_boom; ks_setup(); ksp("2031 function raises: HTTP 500   ", {"pairs": [["A", "V", -10]]}); ns["set_kerning_pairs"] = _ks_real
# v0.134: the route hands its per-pair results to the mark once, after the writes, and the reply carries what the mark says (spy; stubs only)
def ks_mark(tag, payload, **setup):
    ks_setup(**setup); MS = []
    _keep = ns["_mark_font_changed_after_kerning"]
    ns["_mark_font_changed_after_kerning"] = lambda f, results: MS.append([(e["left"], e["right"], e.get("changed"), e.get("status")) for e in results]) or {"called": True, "via_glyph": "spy"}
    r = ns["_route"]("POST", "/kerning/set", json.dumps(payload).encode("utf-8")); h, _, b = r.partition(b"\r\n\r\n")
    ns["_mark_font_changed_after_kerning"] = _keep
    d = json.loads(b)
    print(tag, ":", h.split(b"\r\n")[0].decode()[9:12], "| mark", d.get("fontlab_changed_mark", "<no field>"), "| spy", MS, "| set calls", len(KS["sets"]))
ks_mark("2031a a new pair: marked once      ", {"pairs": [["A", "B", -60]]})
ks_mark("2031b the same value: results go in", {"pairs": [["A", "V", -152]]})
ks_mark("2031c three pairs: one mark call   ", {"pairs": [["A", "B", -60], ["T", "o", -200], ["V", "A", 10.5]]})
ks_mark("2031d stopped partway              ", {"pairs": [["A", "B", -60], ["T", "o", -200]]}, set_mode={("T", "o"): "ignore"})
ks_mark("2031e refused: no mark call        ", {"pairs": [["A", "nope", -60]]})
# v0.136: the route asks for the panel refresh once, after the mark, on the package the write used (spies; stubs only)
def ks_refresh(tag, payload, **setup):
    ks_setup(**setup); SEQ = []
    _keep = {k: ns[k] for k in ("_mark_font_changed_after_kerning", "_refresh_kerning_panel")}
    ns["_mark_font_changed_after_kerning"] = lambda f, results: SEQ.append("mark") or {"called": True, "via_glyph": "spy"}
    ns["_refresh_kerning_panel"] = lambda pkg, results: SEQ.append(("refresh", type(pkg).__name__, [(e["left"], e.get("changed")) for e in results])) or {"called": True}
    r = ns["_route"]("POST", "/kerning/set", json.dumps(payload).encode("utf-8")); h, _, b = r.partition(b"\r\n\r\n")
    ns.update(_keep)
    d = json.loads(b)
    print(tag, ":", h.split(b"\r\n")[0].decode()[9:12], "| refresh", d.get("fontlab_panel_refresh", "<no field>"), "| order", SEQ)
ks_refresh("2031f a new pair: mark, then refresh", {"pairs": [["A", "B", -60]]})
ks_refresh("2031g the same value: results go in ", {"pairs": [["A", "V", -152]]})
ks_refresh("2031h three pairs: one refresh call", {"pairs": [["A", "B", -60], ["T", "o", -200], ["V", "A", 10.5]]})
ks_refresh("2031i stopped partway              ", {"pairs": [["A", "B", -60], ["T", "o", -200]]}, set_mode={("T", "o"): "ignore"})
ks_refresh("2031j refused: no refresh call     ", {"pairs": [["A", "nope", -60]]})
print("2032 GET /kerning/set             :", call("/kerning/set?pairs=A:V:-10"))
_ks_src = src[src.index("_KERN_CLASS_SOURCES = "):src.index("\ndef ", src.index("def set_kerning_pairs(") + 10)]
_ks_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _ks_src).splitlines())
_ks_body = _re83.sub(r'(?s)"""(.*?)"""', '', _ks_code)
print("2033 static scan                  : kerning members used:", sorted(set(_re83.findall(r"kerning\.(\w+)", _ks_body))), "| setter( calls:", len(_re83.findall(r"\bsetter\(", _ks_body)),
      "| getter( calls:", len(_re83.findall(r"\bgetter\(", _ks_body)), "| set keys:", sorted(set(_re83.findall(r"setter\((\w+)", _ks_body))),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|add\w*|clear\w*|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|scale|rename\w*)\(", _ks_body.replace("entry.update(", "").replace("seen.add(", "")),
      "| Update(:", "Update(" in _ks_body, "| font members:", sorted(set(_re83.findall(r"\bfont\.(\w+)", _ks_body))), "| pkg members:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _ks_body))),
      "| gate go=:", "go" in _re83.findall(r"\bgo\b", _ks_body), "| scanned chars > 4000:", len(_ks_src) > 4000)
print("2034 the key is the flags form    :", 'key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))' in _ks_src, "| route registered once:", src.count('if path == "/kerning/set":') == 1,
      "| write log kind:", ns["_ACT_WRITES"].get("/kerning/set"), "| the read scan (1180) still ends before it:", src.index("def _other_glyphs_with_unicode(") < src.index("def set_kerning_pairs("))
fl.CurrentFont = _ks_cur
if _ks_cf is not None: fl.CountFonts = _ks_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
if _ks_ws is not None: fl.flWorkspace = _ks_ws
elif hasattr(fl, "flWorkspace"): delattr(fl, "flWorkspace")

print("--- the activity log line of /kerning/set")
_ks_al_saved = {k: ns[k] for k in ("_now_hms", "_clock", "_ACTIVITY_LOG")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
def ks_al(tag, body, code, reply):
    print(tag)
    ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
    raw = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body or b"")
    ns["_activity_note"]("POST", "/kerning/set", raw, ns["_build_response"](code, reply), "claude-code")
    ns["_act_flush"]()
_ks_one = {"left": "ks2L", "right": "ks2R", "requested": -50, "before": {"value": 0, "kerned": False, "source": "none"},
           "after": {"value": -50.0, "kerned": True, "source": "glyph : glyph"}, "status": "set", "set": True, "changed": True, "exception_over_class": False}
ks_al("2040 one pair, verified:", {"pairs": [["ks2L", "ks2R", -50]]}, 200, {"open": True, "set_count": 1, "stopped": False, "results": [_ks_one]})
ks_al("2041 three pairs, verified:", {"pairs": [["a", "b", 1], ["c", "d", 2], ["e", "f", 3]]}, 200, {"open": True, "results": [_ks_one] * 3})
ks_al("2042 stopped at pair 2:", {"pairs": [["a", "b", 1], ["T", "o", 2], ["e", "f", 3]]}, 200,
      {"open": True, "results": [_ks_one, {"left": "T", "right": "o", "status": "failed", "set": False, "reason": "kerning.set raised RuntimeError: set boom"}, {"left": "e", "right": "f", "status": "not attempted"}]})
ks_al("2043 refused by the listener:", {"pairs": [["A", "Q", -10]]}, 200, {"open": True, "error": "no glyph named 'Q' in the current font; nothing was set"})
ks_al("2044 bad request:", {"pairs": []}, 400, {"error": '"pairs" must be a non-empty list of [left, right, value]'})
ks_al("2045 no font open:", {"pairs": [["A", "V", -10]]}, 200, {"open": False})
ks_al("2046 HTTP 500:", {"pairs": [["A", "V", -10]]}, 500, {"error": "RuntimeError: boom"})
ks_al("2047 body unreadable:", b"\xff", 400, {"error": "request body was not valid JSON"})
for k, v in _ks_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)

# ================= v0.192: POST /kerning/remove (removes glyph : glyph entries with the flags key; verified by re-reading; spies) =================
print("\n==== v0.192 POST /kerning/remove ====")
# The /kerning/pairs fakes (KP, KPFont, the glyph list and _KP_TABLE) with a table that can REMOVE: KRKern allows remove and nothing
# else that writes; every remove key must be the flags form ((a, False), (b, False)).
KR = {"removed": set(), "extra": {}, "removes": [], "mode": None, "after_get": None, "drop": 0}
_KR_FORBIDDEN = tuple(n for n in _KP_FORBIDDEN if n != "remove")
class KRKern(KPKern):
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KP["touched"].append(n); KP["all_touched"].add(n)
            if n in _KR_FORBIDDEN:
                KP["forbidden"].append(n)
                raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "remove" and KR["mode"] == "not_callable": return 9
            if n == "remove" and KR["mode"] == "no_attr": raise AttributeError("remove is missing")
        return object.__getattribute__(self, n)
    def __len__(self):
        if KP["len_raises"]: raise RuntimeError("len boom")
        return KP["len"] + len(KR["extra"]) - len(KR["removed"]) - KR["drop"]
    def get(self, pair):
        if pair in KR["removed"]:
            KP["gets"].append(pair)
            if KR["after_get"] == "raise": raise RuntimeError("get boom after remove")
            return None
        if pair in KR["extra"]:
            KP["gets"].append(pair); return KR["extra"][pair]
        return KPKern.get(self, pair)
    def remove(self, key):
        KR["removes"].append(key)
        flagged = (isinstance(key, tuple) and len(key) == 2 and all(isinstance(p, tuple) and len(p) == 2 and p[1] is False for p in key))
        if not flagged:
            KP["forbidden"].append("remove with key " + repr(key)); KP["ever"].append("remove key " + repr(key)); return True
        m = KR["mode"]
        if isinstance(m, dict): m = m.get((key[0][0], key[1][0]))
        if m == "raise": raise RuntimeError("remove boom")
        if m == "ignore": return None
        if m == "other": KR["drop"] += 1; return None      # another entry went, this one stays: the size alone would look right
        if m == "zero": KR["extra"][key] = 0.0; KR["drop"] += 1; return None     # the entry stays, now 0: the table keeps its size
        KR["removed"].add(key)
        if key in KR["extra"]: KR["removed"].discard(key); del KR["extra"][key]
        if m == "two": KR["drop"] += 1
        if m == "raise_after": raise RuntimeError("remove boom after removing")
        return None
def kr_setup(mode=None, extra=None, after_get=None, **cfg):
    kp_setup(kern_factory=KRKern, **cfg)
    KR.update(removed=set(), extra=dict(extra or {}), removes=[], mode=mode, after_get=after_get, drop=0)
def krp(tag, payload, raw=False):
    body = payload if raw else json.dumps(payload).encode("utf-8")
    r = ns["_route"]("POST", "/kerning/remove", body); h, _, b = r.partition(b"\r\n\r\n")
    c, d = h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
    print(tag, ":", c, {k: v for k, v in d.items() if k != "results"}, "| remove calls", KR["removes"], "| forbidden", list(KP["forbidden"]))
    for r_ in d.get("results") or []:
        print("      ", r_)
    return c, d
_kr_cf = getattr(fl, "CountFonts", None); _kr_cur = fl.CurrentFont; _kr_ws = getattr(fl, "flWorkspace", None)
KP["ever"].clear()
_kr_exc = {(("Aacute", False), ("Tbar.c2sc", False)): -50.0}
kr_setup(); krp("2700 one pair removed            ", {"pairs": [["A", "V"]]})
kr_setup(); krp("2701 two pairs removed           ", {"pairs": [["A", "V"], ["T", "o"]]})
kr_setup(extra=_kr_exc); krp("2702 an exception over a class   ", {"pairs": [["Aacute", "Tbar.c2sc"]]})
kr_setup(); krp("2703 no entry, nothing kerns     ", {"pairs": [["A", "B"]]})
kr_setup(); krp("2704 no entry, a class kerns     ", {"pairs": [["Aacute", "Wgrave.c2sc"]]})
kr_setup(); krp("2705 removed, no entry, removed  ", {"pairs": [["A", "V"], ["A", "B"], ["T", "o"]]})
kr_setup(); krp("2706 defect B: glyph Aring       ", {"pairs": [["Aring", "W.c2sc"]]})
kr_setup(count=2); krp("2707 two fonts, matched by path  ", {"pairs": [["A", "V"]]})
print("--- refused before any removal (remove calls must stay empty)")
kr_setup(); krp("2710 unknown glyphs              ", {"pairs": [["A", "V"], ["Q", "V"], ["A", "Zz"]]})
for _tag, _p in (("2711 pairs empty                ", []), ("2711b pairs not a list         ", {"A": "V"}), ("2711c an item of three         ", [["A", "V", 0]]),
                 ("2711d an item of one           ", [["A"]]), ("2711e a name with a space       ", [["A B", "V"]]), ("2711f a name not text          ", [[5, "V"]]),
                 ("2711g a pair twice              ", [["A", "V"], ["T", "o"], ["A", "V"]]), ("2711h a string item            ", ["A:V"])):
    kr_setup(); krp(_tag, {"pairs": _p})
kr_setup(); krp("2712 another key in the body    ", {"pairs": [["A", "V"]], "go": "yes"})
kr_setup(); krp("2712b no pairs key              ", {"pair": [["A", "V"]]})
kr_setup(); krp("2712c body not JSON              ", b"pairs=A:V", raw=True)
kr_setup(); krp("2712d body empty                 ", b"", raw=True)
kr_setup(count=0); krp("2713 no font open (CountFonts 0)  ", {"pairs": [["A", "V"]]})
kr_setup(cur=None); krp("2713b CurrentFont None          ", {"pairs": [["A", "V"]]})
kr_setup(count=None); krp("2713c CountFonts gives None     ", {"pairs": [["A", "V"]]})
kr_setup(count=2, pkg_path="C:/fonts/other.vfc"); krp("2714 two fonts, paths differ     ", {"pairs": [["A", "V"]]})
kr_setup(master="Ghost"); krp("2715 current master unlisted     ", {"pairs": [["A", "V"]]})
kr_setup(mode="not_callable"); krp("2716 remove not callable         ", {"pairs": [["A", "V"]]})
kr_setup(mode="no_attr"); krp("2716b remove missing            ", {"pairs": [["A", "V"]]})
print("--- failures while removing: the request stops at the first pair not confirmed")
kr_setup(ids={"T": (RuntimeError("left boom"), 0)}); krp("2720 value before unreadable     ", {"pairs": [["A", "V"], ["T", "o"], ["V", "A"]]})
kr_setup(mode={("T", "o"): "raise"}); krp("2721 remove raises on pair 2 of 3", {"pairs": [["A", "V"], ["T", "o"], ["V", "A"]]})
kr_setup(mode="ignore"); krp("2722 remove does nothing         ", {"pairs": [["A", "V"]]})
kr_setup(mode="zero"); krp("2723 remove leaves a zero        ", {"pairs": [["A", "V"]]})
kr_setup(mode="other"); krp("2723b another entry went instead ", {"pairs": [["A", "V"]]})
kr_setup(mode="two"); krp("2724 two entries went            ", {"pairs": [["A", "V"], ["T", "o"]]})
kr_setup(mode="raise_after"); krp("2725 removed, then raises        ", {"pairs": [["A", "V"], ["T", "o"]]})
kr_setup(after_get="raise"); krp("2726 read back raises            ", {"pairs": [["A", "V"]]})
KP["len_raises"] = False; kr_setup(); KP["len_raises"] = True; krp("2727 len() raises               ", {"pairs": [["A", "V"]]})
print("2730 spy over the remove cases    : forbidden members touched:", [f for f in KP["ever"]], "| plain remove keys: none above")
_kr_real = ns["remove_kerning_pairs"]
def _kr_boom(pairs): raise RuntimeError("remove boom in the route")
ns["remove_kerning_pairs"] = _kr_boom; kr_setup(); krp("2731 function raises: HTTP 500   ", {"pairs": [["A", "V"]]}); ns["remove_kerning_pairs"] = _kr_real
def kr_seq(tag, payload, **setup):
    kr_setup(**setup); SEQ = []
    _keep = {k: ns[k] for k in ("_mark_font_changed_after_kerning", "_refresh_kerning_panel")}
    ns["_mark_font_changed_after_kerning"] = lambda f, results: SEQ.append(("mark", [(e["left"], e.get("changed"), e.get("status")) for e in results])) or {"called": True, "via_glyph": "spy"}
    ns["_refresh_kerning_panel"] = lambda pkg, results: SEQ.append(("refresh", type(pkg).__name__)) or {"called": True}
    r = ns["_route"]("POST", "/kerning/remove", json.dumps(payload).encode("utf-8")); h, _, b = r.partition(b"\r\n\r\n")
    ns.update(_keep)
    d = json.loads(b)
    print(tag, ":", h.split(b"\r\n")[0].decode()[9:12], "| mark", d.get("fontlab_changed_mark", "<no field>"), "| refresh", d.get("fontlab_panel_refresh", "<no field>"), "| order", SEQ)
kr_seq("2732 a removal: mark, then refresh", {"pairs": [["A", "V"]]})
kr_seq("2732b no entry: results go in     ", {"pairs": [["A", "B"]]})
kr_seq("2732c stopped partway             ", {"pairs": [["A", "V"], ["T", "o"]]}, mode={("T", "o"): "ignore"})
kr_seq("2732d refused: no calls           ", {"pairs": [["A", "nope"]]})
kr_setup(); KP["cfg"]["kern_factory"] = KRKern
_mk_keep = ns["_MARK_CHANGED"]; ns["_MARK_CHANGED"] = False; ns["_REFRESH_KERNING_PANEL"], _rf_keep = False, ns["_REFRESH_KERNING_PANEL"]
krp("2733 mark and refresh switched off", {"pairs": [["A", "V"]]})
ns["_MARK_CHANGED"] = _mk_keep; ns["_REFRESH_KERNING_PANEL"] = _rf_keep
print("2734 GET /kerning/remove          :", call("/kerning/remove?pairs=A:V"))
_kr_src = src[src.index("def remove_kerning_pairs("):src.index("\ndef ", src.index("def remove_kerning_pairs(") + 10)]
_kr_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _kr_src).splitlines())
_kr_body = _re83.sub(r'(?s)"""(.*?)"""', '', _kr_code)
print("2735 static scan                  : kerning members used:", sorted(set(_re83.findall(r"kerning\.(\w+)", _kr_body))), "| remover( calls:", len(_re83.findall(r"\bremover\(", _kr_body)),
      "| getter( calls:", len(_re83.findall(r"\bgetter\(", _kr_body)), "| remove keys:", sorted(set(_re83.findall(r"remover\((\w+)", _kr_body))),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|set|remove\w*|update\w*|add\w*|clear\w*|keys|values|items|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*)\(", _kr_body.replace("entry.update(", "").replace("seen.add(", "")),
      "| Update(:", "Update(" in _kr_body, "| font members:", sorted(set(_re83.findall(r"\bfont\.(\w+)", _kr_body))), "| pkg members:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _kr_body))),
      "| scanned chars > 4000:", len(_kr_src) > 4000)
print("2736 the key is the flags form    :", 'key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))' in _kr_src, "| route registered once:", src.count('if path == "/kerning/remove":') == 1,
      "| write log kind:", ns["_ACT_WRITES"].get("/kerning/remove"), "| in the module docstring:", "POST /kerning/remove" in src[:src.index('"""', 3)])

# ================= v0.194: class sides ('@name') in POST /kerning/set and POST /kerning/remove (class keys; a sample glyph pair; spies) =================
print("\n==== v0.194 class sides in /kerning/set and /kerning/remove ====")
# The KP fakes: left class Aring {Aacute, Atilde, Aring} (id 101), right classes W {W.c2sc, Wgrave.c2sc} (201) and Y {Ydieresis.c2sc} (202),
# an OpenType class 'fea'. KCSet / KCRem accept keys whose flags are booleans and expose the master's kerning groups (KCGroups: only items()).
KC = {"g_all": set(), "g_forbidden": []}
_KC_ITEMS = [("Aring", (["Aacute", "Atilde", "Aring"], "KernLeft")), ("W", (["W.c2sc", "Wgrave.c2sc"], "KernRight")), ("Y", (["Ydieresis.c2sc"], "KernRight"))]
class KCGroups:
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KC["g_all"].add(n)
            if n != "items":
                KC["g_forbidden"].append(n); raise SystemExit("FORBIDDEN group container member touched: " + n)
        return object.__getattribute__(self, n)
    def __len__(self): return 3
    def items(self):
        v = KP["cfg"].get("items", "default")
        if isinstance(v, Exception): raise v
        return [(n, (list(m), s)) for n, (m, s) in _KC_ITEMS] if v == "default" else v
def _kc_bool_key(key):
    return isinstance(key, tuple) and len(key) == 2 and all(isinstance(p, tuple) and len(p) == 2 and type(p[1]) is bool for p in key)
def _kc_groups_attr():
    m = KP["cfg"].get("groups_attr")
    if m == "raise": raise RuntimeError("groups boom")
    if m == "callable": return lambda: None
    return KCGroups()
_KC_SET_FORBIDDEN = tuple(n for n in _KS_FORBIDDEN if n != "groups")
_KC_REM_FORBIDDEN = tuple(n for n in _KR_FORBIDDEN if n != "groups")
class KCSet(KSKern):
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KP["touched"].append(n); KP["all_touched"].add(n)
            if n in _KC_SET_FORBIDDEN:
                KP["forbidden"].append(n); raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "groups": return _kc_groups_attr()
        return object.__getattribute__(self, n)
    def set(self, key, value):
        KS["sets"].append((key, value))
        if not _kc_bool_key(key):
            KP["forbidden"].append("set with key " + repr(key)); return None
        if KS["set_mode"] == "ignore": return None
        KS["new"][key] = value
        return None
class KCRem(KRKern):
    def __getattribute__(self, n):
        if not n.startswith("__"):
            KP["touched"].append(n); KP["all_touched"].add(n)
            if n in _KC_REM_FORBIDDEN:
                KP["forbidden"].append(n); raise SystemExit("FORBIDDEN kerning member touched: " + n)
            if n == "groups": return _kc_groups_attr()
        return object.__getattribute__(self, n)
    def remove(self, key):
        KR["removes"].append(key)
        if not _kc_bool_key(key):
            KP["forbidden"].append("remove with key " + repr(key)); return True
        KR["removed"].add(key)
        if key in KR["extra"]: KR["removed"].discard(key); del KR["extra"][key]
        return None
def kc_set_setup(set_mode=None, **cfg):
    kp_setup(kern_factory=KCSet, **cfg)
    KS.update(new={}, sets=[], set_mode=set_mode, extra=0, after_set_get=None, flaky=set(), hidden=set(), script={})
    KC.update(g_all=set(), g_forbidden=[])
def kc_rem_setup(extra=None, **cfg):
    kp_setup(kern_factory=KCRem, **cfg)
    KR.update(removed=set(), extra=dict(extra or {}), removes=[], mode=None, after_get=None, drop=0)
    KC.update(g_all=set(), g_forbidden=[])
def kcs(tag, payload):
    ksp(tag, payload); print("       group container members:", sorted(KC["g_all"]), "| getAllGroups calls", KP["groups_calls"])
def kcr(tag, payload):
    krp(tag, payload); print("       group container members:", sorted(KC["g_all"]), "| getAllGroups calls", KP["groups_calls"])
KP["ever"].clear()
kc_set_setup(); kcs("2780 class : class @Aring:@Y      ", {"pairs": [["@Aring", "@Y", -100]]})
kc_set_setup(); kcs("2781 glyph : class T:@W (new)     ", {"pairs": [["T", "@W", -40]]})
kc_set_setup(); kcs("2782 class : glyph @Aring:Tbar.c2sc", {"pairs": [["@Aring", "Tbar.c2sc", -90]]})
kc_set_setup(mode={(("Aacute", False), ("W.c2sc", False)): -10.0}); kcs("2783 sample covered by an exception", {"pairs": [["@Aring", "@W", -60]]})
kc_set_setup(); kcs("2784 glyph and class pairs mixed ", {"pairs": [["A", "B", -60], ["@Aring", "@Y", -100]]})
kc_set_setup(ids={"Aacute": (0, 0)}); kcs("2785 sample not reached: stops    ", {"pairs": [["@Aring", "@Y", -100], ["T", "@W", -40]]})
kc_set_setup(groups=[(True, "Aring", 101, 0, ["Zq"]), (True, "Y", 202, 0, ["Ydieresis.c2sc"])],
             items=[("Aring", (["Zq"], "KernLeft")), ("Y", (["Ydieresis.c2sc"], "KernRight"))]); kcs("2786 no member in the font: no sample", {"pairs": [["@Aring", "@Y", -100]]})
kc_set_setup(ids={"Aacute": (201, 0)}, mode={(("W", True), ("Y", True)): -100.0})
kcs("2785b sample in another class: stops", {"pairs": [["@Aring", "@Y", -100]]})
kc_set_setup(set_mode="ignore"); kcs("2787 set stores nothing: failed   ", {"pairs": [["@Aring", "@Y", -100]]})
kc_set_setup(groups=_kp_groups_default() + [(True, "B", 400, 0, ["V"])]); kcs("2788 glyph B, group B, no class id: no note", {"pairs": [["B", "o", -10]]})
print("--- refused before any write (set calls must stay empty)")
kc_set_setup(); kcs("2789 a right group on the left    ", {"pairs": [["@W", "V", -10]]})
kc_set_setup(); kcs("2790 a left group on the right    ", {"pairs": [["A", "@Aring", -10]]})
kc_set_setup(); kcs("2791 an OpenType class            ", {"pairs": [["@fea", "V", -10]]})
kc_set_setup(); kcs("2792 an unknown class             ", {"pairs": [["A", "B", -60], ["@nope", "V", -10]]})
kc_set_setup(items=[("Aring", (["Aacute"], "KernLeft"))] + _KC_ITEMS[1:]); kcs("2793 the sources' members differ  ", {"pairs": [["@Aring", "@Y", -10]]})
kc_set_setup(items=RuntimeError("items boom")); kcs("2794 items() raises               ", {"pairs": [["@Aring", "@Y", -10]]})
kc_set_setup(groups_attr="callable"); kcs("2795 kerning.groups callable      ", {"pairs": [["@Aring", "@Y", -10]]})
kc_set_setup(groups=RuntimeError("list boom")); kcs("2796 getAllGroups raises           ", {"pairs": [["@Aring", "@Y", -10]]})
for _bad in ("@", "@@Aring", "A@", "@A ring"):
    kc_set_setup(); kcs(f"2797 bad side {_bad!r:10}         ", {"pairs": [[_bad, "V", -10]]})
print("--- remove")
kc_rem_setup(); kcr("2798 remove class : class @Aring:@Y", {"pairs": [["@Aring", "@Y"]]})
kc_rem_setup(); kcr("2799 remove glyph : class A:@W    ", {"pairs": [["A", "@W"]]})
kc_rem_setup(); kcr("2800 no class entry: goes on      ", {"pairs": [["T", "@W"], ["@Aring", "@Y"]]})
kc_rem_setup(); kcr("2801 remove: right group on left ", {"pairs": [["@Y", "V"]]})
kc_rem_setup(); kcr("2802 remove: an OpenType class   ", {"pairs": [["A", "@fea"]]})
kc_set_setup(); KP["all_touched"].clear(); KC["g_all"].clear()
for _p in ({"pairs": [["@Aring", "@Y", -100]]}, {"pairs": [["T", "@W", -40]]}, {"pairs": [["A", "B", -60]]}):
    ns["_route"]("POST", "/kerning/set", json.dumps(_p).encode("utf-8"))
kc_rem_setup()
for _p in ({"pairs": [["@Aring", "@Y"]]}, {"pairs": [["A", "V"]]}):
    ns["_route"]("POST", "/kerning/remove", json.dumps(_p).encode("utf-8"))
print("2803 spy over the class cases     : forbidden:", list(KP["forbidden"]), "| ever:", list(KP["ever"]), "| kerning and package members touched:",
      sorted(n for n in KP["all_touched"]), "| group container members:", sorted(KC["g_all"]), "| forbidden there:", KC["g_forbidden"])
_kc_src = src[src.index("_KERN_KIND_RANK = {"):src.index("def set_kerning_pairs(")]
_kc_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _kc_src).splitlines())
_kc_body = _re83.sub(r'(?s)"""(.*?)"""', '', _kc_code)
print("2804 static scan of the class checks: kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _kc_body))),
      "| pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _kc_body))), "| container members used:", sorted(set(_re83.findall(r"\bcontainer\.(\w+)", _kc_body))),
      "| _kgr_from_items( calls:", len(_re83.findall(r"\b_kgr_from_items\(", _kc_body)), "| _trysetkern_group_names( calls:", len(_re83.findall(r"\b_trysetkern_group_names\(", _kc_body)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|set|remove\w*|update\w*|Update\w*|add\w*|clear\w*|keys|values|items|has_key|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*|notify\w*)\(", _kc_body),
      "| scanned chars > 3000:", len(_kc_src) > 3000)
_kc_mtf = ns["_mark_through_first"]
ns["_mark_through_first"] = lambda font, candidates, how: {"called": True, "via_glyph": candidates[0] if candidates else None, "candidates": list(candidates)}
kc_set_setup(); kcs("2806 the mark goes to sample glyphs ", {"pairs": [["@Aring", "@Y", -100], ["T", "@W", -40]]})
kc_set_setup(groups=[(True, "Aring", 101, 0, ["Zq"]), (True, "Y", 202, 0, ["Zr"])], items=[("Aring", (["Zq"], "KernLeft")), ("Y", (["Zr"], "KernRight"))])
kcs("2806b no sample: no class name marked", {"pairs": [["@Aring", "@Y", -100]]})
ns["_mark_through_first"] = _kc_mtf
print("2805 one key form in both routes  : set", _ks_src.count('key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))'),
      "| remove", _kr_src.count('key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))'),
      "| class checks in both:", _ks_src.count("_kern_class_targets(pkg, kerning, class_sides, by_name)"), _kr_src.count("_kern_class_targets(pkg, kerning, class_sides, by_name)"),
      "| documented:", "a side written '@name' is a kerning group" in src[:src.index('"""', 3)])
fl.CurrentFont = _kr_cur
if _kr_cf is not None: fl.CountFonts = _kr_cf
elif hasattr(fl, "CountFonts"): delattr(fl, "CountFonts")
if _kr_ws is not None: fl.flWorkspace = _kr_ws
elif hasattr(fl, "flWorkspace"): delattr(fl, "flWorkspace")
KP["len_raises"] = False

print("--- the activity log line of /kerning/remove")
_kr_al_saved = {k: ns[k] for k in ("_now_hms", "_clock", "_ACTIVITY_LOG")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
def kr_al(tag, body, code, reply):
    print(tag)
    ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
    raw = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body or b"")
    ns["_activity_note"]("POST", "/kerning/remove", raw, ns["_build_response"](code, reply), "claude-code")
    ns["_act_flush"]()
_kr_one = {"left": "kd1L", "right": "kd1R", "before": {"value": -50.0, "kerned": True, "source": "glyph : glyph"},
           "after": {"value": -80.0, "kerned": True, "source": "class : glyph", "left_class": "kdcL"}, "status": "removed", "removed": True, "changed": True}
_kr_none = {"left": "A", "right": "B", "before": {"value": 0, "kerned": False, "source": "none"}, "status": "no entry", "removed": False, "changed": False}
kr_al("2740 one pair, verified:", {"pairs": [["kd1L", "kd1R"]]}, 200, {"open": True, "results": [_kr_one]})
kr_al("2741 one pair, no entry:", {"pairs": [["A", "B"]]}, 200, {"open": True, "results": [_kr_none]})
kr_al("2742 three pairs, one with no entry:", {"pairs": [["a", "b"], ["A", "B"], ["e", "f"]]}, 200, {"open": True, "results": [_kr_one, _kr_none, _kr_one]})
kr_al("2743 stopped at pair 2:", {"pairs": [["a", "b"], ["T", "o"], ["e", "f"]]}, 200,
      {"open": True, "results": [_kr_one, {"left": "T", "right": "o", "status": "failed", "removed": False, "reason": "kerning.remove raised RuntimeError: remove boom"}, {"left": "e", "right": "f", "status": "not attempted"}]})
kr_al("2744 refused by the listener:", {"pairs": [["A", "Q"]]}, 200, {"open": True, "error": "no glyph named 'Q' in the current font; nothing was removed"})
kr_al("2745 bad request:", {"pairs": []}, 400, {"error": '"pairs" must be a non-empty list of [left, right]'})
kr_al("2746 no font open:", {"pairs": [["A", "V"]]}, 200, {"open": False})
kr_al("2747 HTTP 500:", {"pairs": [["A", "V"]]}, 500, {"error": "RuntimeError: boom"})
# v0.195: a pair with a class side and no entry names its own kind (CK 1430); an unknown kind falls back to glyph : glyph
kr_al("2747b a class : class pair, no entry:", {"pairs": [["@cwL", "@cwR"]]}, 200, {"open": True, "results": [dict(_kr_none, left="@cwL", right="@cwR", kind="class : class")]})
kr_al("2747c a glyph : class pair, no entry:", {"pairs": [["cw1a", "@cwB"]]}, 200, {"open": True, "results": [dict(_kr_none, left="cw1a", right="@cwB", kind="glyph : class")]})
kr_al("2747d an unknown kind, no entry:", {"pairs": [["A", "B"]]}, 200, {"open": True, "results": [dict(_kr_none, kind="bogus")]})
for k, v in _kr_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)

# ================= v0.125: /debug/tryopen (gated research probe for P2.1: ONE open contour, never closed, detached or drawn) =================
print("\n==== v0.125 /debug/tryopen ====")
# The /glyph/path fakes of v0.81 (P81Contour with convertToCurve, P72Shape, the layer created on demand) plus the one-font gate of
# /debug/trysync. TOContour records every assignment to `closed`; TOLayer can close the contour on attach (mode close_on_attach).
TO = {"count": 1, "packages": 1, "closed_sets": [], "vp": []}
class TOContour(P81Contour):
    def __init__(s, pts):
        P81Contour.__init__(s, pts)
        if P72["mode"].get("born_closed"): s._closed = True
    @property
    def closed(s): return s._closed
    @closed.setter
    def closed(s, v): TO["closed_sets"].append(v); s._closed = False if P72["mode"].get("noclose") else v
class TOLayer(P81Layer):
    def addShape(s, shape):
        P81Layer.addShape(s, shape)
        if P72["mode"].get("close_on_attach"):
            for c in shape.contours: c._closed = True
class TOPkg:
    isNull = False
class TOWs:
    def packages(s):
        v = TO["packages"]
        if isinstance(v, Exception): raise v
        return [object() for _ in range(v)]
    @property
    def currentPackage(s): return TOPkg()
    def updateActiveViewport(s): TO["vp"].append("updateActiveViewport")
TOWsCls = type("flWorkspace", (), {"instance": staticmethod(lambda: TOWs())})
def _to_count():
    v = TO["count"]
    if isinstance(v, Exception): raise v
    return v
_to_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "flWorkspace")]
def to_setup(mode=None, count=1, packages=1):
    p81_setup(mode=mode)
    _fm.flContour = TOContour
    for g in ("ocpa", "ocpb"): TS[g] = TsGlyph(g, [])
    real = P81["real_create"]
    def create(s, name, cs=None):
        r = real(s, name, cs); P72["layers"][s.name] = TOLayer(name); return P72["layers"][s.name]
    P72Mod.findLayerCreate = create
    TO.update(count=count, packages=packages, closed_sets=[], vp=[])
    for _m in _tf_mods:
        _m.CountFonts = _to_count; _m.flWorkspace = TOWsCls
    ns["_TRYOPEN"]["calls"] = 0
def to(tag, path, keys=("error", "calls_so_far")):
    c, d = call(path)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| addShape", P72["calls"].count("addShape"), "| closed set", TO["closed_sets"],
          "| layers", sorted(k for k in P72["layers"] if k.startswith("ocp")))
    return d
Q = "/debug/tryopen?"
to_setup()
to("2050 detached without go          ", Q + "stage=detached&name=ocpa&kind=line")
to("2051 draw without go              ", Q + "stage=draw&name=ocpa&kind=curve")
to("2052 go must be exactly yes       ", Q + "stage=draw&name=ocpa&kind=line&go=maybe")
to("2053 unknown stage                ", Q + "stage=close&name=ocpa&kind=line&go=yes")
to("2054 unknown kind                 ", Q + "stage=draw&name=ocpa&kind=circle&go=yes")
to("2055 name without the ocp prefix  ", Q + "stage=draw&name=fresh&kind=line&go=yes")
to("2056 name with a space            ", Q + "stage=draw&name=ocp%20a&kind=line&go=yes")
to("2057 name 'ocp' alone             ", Q + "stage=draw&name=ocp&kind=line&go=yes")
for tag, over in (("2058 two fonts open               ", dict(count=2)), ("2059 two packages                ", dict(packages=2)),
                  ("2060 CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("2061 no font open                ", dict(count=0))):
    to_setup(**over); to(tag, Q + "stage=draw&name=ocpa&kind=line&go=yes")
to_setup()
d = to("2062 detached line                ", Q + "stage=detached&name=ocpa&kind=line&go=yes", keys=("stage", "kind", "calls_so_far", "error"))
print("2063  detached read             :", d["detached"], "| expected", d["expected_nodes"])
d = to("2064 detached curve               ", Q + "stage=detached&name=ocpa&kind=curve&go=yes", keys=("stage", "kind", "calls_so_far", "error"))
print("2065  detached read             :", d["detached"], "| convertToCurve calls", P72["calls"].count("convertToCurve"))
d = to("2066 draw line                    ", Q + "stage=draw&name=ocpa&kind=line&go=yes",
       keys=("drawn", "layer_closed", "layer_mismatches", "changed", "state_before", "state_after", "layer_created", "calls_so_far", "error"))
print("2067  layer read back           :", d.get("layer_contours"), "| guard reply keys:", [k for k in ("synced_with_fontlab", "durability_note") if k in d],
      "| repainted", d.get("display_refreshed"), TO["vp"])
d = to("2068 draw curve                   ", Q + "stage=draw&name=ocpb&kind=curve&go=yes", keys=("drawn", "layer_closed", "layer_mismatches", "changed", "calls_so_far"))
print("2069  layer read back           :", d.get("layer_contours"))
to("2070 draw into a drawn glyph      ", Q + "stage=draw&name=ocpa&kind=line&go=yes", keys=("error", "state_before", "calls_so_far"))
to("2071 a glyph that does not exist  ", Q + "stage=draw&name=ocpzz&kind=line&go=yes", keys=("error", "calls_so_far"))
to("2072 the limit: call 7 is refused ", Q + "stage=detached&name=ocpa&kind=line&go=yes"); to("2072b             call 8 as well ", Q + "stage=detached&name=ocpa&kind=line&go=yes")
to_setup(mode={"close_on_attach": 1})
to("2073 FontLab closes it on attach  ", Q + "stage=draw&name=ocpa&kind=line&go=yes", keys=("drawn", "layer_closed", "layer_mismatches", "changed", "error"))
to_setup(mode={"attach_alter": 1})
to("2074 the layer reads another node ", Q + "stage=draw&name=ocpa&kind=line&go=yes", keys=("drawn", "layer_closed", "layer_mismatches", "changed"))
to_setup(mode={"add_raises": 1})
to("2075 addShape raises              ", Q + "stage=draw&name=ocpa&kind=line&go=yes", keys=("drawn", "error", "changed"))
to_setup(mode={"born_closed": 1})
to("2076 the detached contour is closed", Q + "stage=draw&name=ocpa&kind=line&go=yes", keys=("drawn", "error"))
print("2077  detached read             :", call(Q + "stage=detached&name=ocpa&kind=line&go=yes")[1].get("detached", {}).get("closed"))
to_setup(mode={"conv_false": 1})
to("2078 convertToCurve fails: counted", Q + "stage=draw&name=ocpa&kind=curve&go=yes", keys=("error", "calls_so_far"))
to_setup(mode={"round_place": 1})
to("2079 a handle placed off by one   ", Q + "stage=draw&name=ocpa&kind=curve&go=yes", keys=("drawn", "error"))
print("2080  mismatches            :", call(Q + "stage=detached&name=ocpa&kind=curve&go=yes")[1].get("detached", {}).get("mismatches"))
to_setup()
c, d = p72_post("/glyph/path", {"name": "fresh", "contours": [RRECT]})
print("2081 draw_path still closes      :", d["drawn"], "| closed set", TO["closed_sets"], "| layer contour closed", mo_get()["modern_outline"]["contours"][0]["closed"])
c, d = p72_post("/glyph/polygon", {"name": "ocpb", "points": TRI4})
print("2082 draw_polygon still closes   :", d["drawn"], "| closed set", TO["closed_sets"])
_src125 = "\n".join(l for l in src[src.index("# /debug/tryopen (v0.125)"):src.index("def get_glyph_unicode(")].split("\n") if not l.lstrip().startswith("#"))
print("2083 static scan of the probe (code lines):", len(_src125) > 3000, "| closed = True:", "closed = True" in _src125, "| closed=False:", "closed=False" in _src125, "| forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|remove\w*|removeShape|clearNodes|deleteContour)\s*\(", _src125),
      "| counter raised before the build:", _src125.index('_TRYOPEN["calls"] += 1') < _src125.index("_path_build_contour("))
print("2084 route documented            :", "/debug/tryopen        stage=detached|draw" in src)
_to_al_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
print("2085 activity log, go=yes:")
ns["_activity_note"]("GET", Q + "stage=draw&name=ocpa&kind=line&go=yes", b"", ns["_build_response"](200, {"stage": "draw", "drawn": True}), "claude-code")
ns["_act_flush"]()
for k, v in _to_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
for _m, _a, _v in _to_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.126: POST /glyph/path draws OPEN contours ({"points": [...], "closed": false}; live research 586-594) =================
print("\n==== v0.126 POST /glyph/path, open contours ====")
# The v0.81 /glyph/path fakes; TOContour (v0.125) records every assignment to `closed`; TOLayer can close a contour on attach.
def od_setup(mode=None):
    p81_setup(mode=mode); _fm.flContour = TOContour; TO["closed_sets"] = []
    real = P81["real_create"]
    def create(s, name, cs=None):
        r = real(s, name, cs); P72["layers"][s.name] = TOLayer(name); return P72["layers"][s.name]
    P72Mod.findLayerCreate = create
def od(tag, contours, mode=None, keys=("drawn", "nodes_match", "points", "segments_curved", "contour_sizes", "open_contours", "changed")):
    od_setup(mode); c, d = p72_post("/glyph/path", {"name": "fresh", "contours": contours})
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d} if str(c) == "200" else d, "| reason", (d.get("reason") or "")[:150], "| closed set", TO["closed_sets"],
          "| addShape", P72["calls"].count("addShape"))
    return c, d
def od_layer():
    m = mo_get()["modern_outline"]
    return [(c["closed"], [(n["x"], n["y"], "on" if n["isOn"] else "h") for n in c["nodes"]]) for c in m["contours"]]
OV = [pp(24, 482), pp(132, 69), pp(228, 462)]
OARCH = [pp(105, 104), pp(398, 104, (105, 280), (398, 255))]
SQ = [pp(0, 0), pp(100, 0), pp(100, 100), pp(0, 100)]
od("2090 open V                      ", [{"points": OV, "closed": False}]); print("2091  layer                    :", od_layer())
od("2092 open arch                   ", [{"points": OARCH, "closed": False}]); print("2093  layer                    :", od_layer())
od("2094 open V and a closed square  ", [{"points": OV, "closed": False}, SQ]); print("2095  layer                    :", od_layer())
od("2096 object with closed true     ", [{"points": SQ, "closed": True}]); print("2097  layer                    :", od_layer())
od("2098 object without closed       ", [{"points": SQ}])
od("2099 a plain list (as before)    ", [SQ])
SMOOTH_IN = [pp(0, 0), pp(100, 100, (0, 50), (50, 100), smooth=True), pp(200, 0, (150, 100), (200, 50))]
od("2100 open, smooth inner point    ", [{"points": SMOOTH_IN, "closed": False}]); print("2101  layer                    :", od_layer())
od("2102 open, two points            ", [{"points": [pp(0, 0), pp(300, 0)], "closed": False}])
# refusals by the route (HTTP 400) and by the request checks (nothing built)
for tag, cont in (("2103 object without points      ", [{"closed": False}]), ("2104 object with a stray key    ", [{"points": OV, "closed": False, "x": 1}]),
                  ("2105 closed is a string        ", [{"points": OV, "closed": "no"}]), ("2106 closed is 0               ", [{"points": OV, "closed": 0}]),
                  ("2107 open, one point           ", [{"points": [pp(0, 0)], "closed": False}]), ("2108 closed object, 2 points   ", [{"points": [pp(0, 0), pp(5, 5)], "closed": True}]),
                  ("2109 open, 501 points          ", [{"points": [pp(i, 0) for i in range(501)], "closed": False}]),
                  ("2110 points is not a list      ", [{"points": "OV", "closed": False}]),
                  ("2111 open, c1 on the first point", [{"points": [pp(0, 0, (10, 10), (20, 20)), pp(100, 0)], "closed": False}]),
                  ("2112 open, smooth first point  ", [{"points": [pp(0, 0, smooth=True), pp(50, 50), pp(100, 0)], "closed": False}]),
                  ("2113 open, smooth last point   ", [{"points": [pp(0, 0), pp(50, 50), pp(100, 0, smooth=True)], "closed": False}]),
                  ("2114 open, collapses by rounding", [{"points": [pp(0, 0), pp(0.4, 0.2)], "closed": False}]),
                  ("2115 open, inner smooth bent   ", [{"points": [pp(0, 0), pp(100, 0, smooth=True), pp(100, 100)], "closed": False}])):
    od(tag, cont, keys=("drawn", "open_contours", "changed"))
od_setup(); print("2116 a closed contour, smooth first point (wraps, as before):", p72_post("/glyph/path", {"name": "fresh", "contours": [[pp(0, 0, smooth=True), pp(100, 0), pp(100, 100), pp(0, 100)]]})[1].get("reason", "")[:150])
od("2117 FontLab closes it on attach ", [{"points": OV, "closed": False}], mode={"close_on_attach": 1}, keys=("drawn", "nodes_match", "changed", "open_contours"))
od("2118 the detached contour is closed", [{"points": OV, "closed": False}], mode={"born_closed": 1}, keys=("drawn", "changed"))
od("2119 a closed request, FontLab opens it", [SQ], mode={"noclose": 1}, keys=("drawn", "changed"))
od_setup(); _c, _d = p72_post("/glyph/path", {"name": "fresh", "contours": [{"points": [pp(0.5, 0), pp(10.49, 0, (3.2, 7.5), (7.5, 7.5))], "closed": False}]})
print("2120 rule B on an open contour   :", _d.get("drawn"), [(r["field"], r["requested"], r["used"]) for r in _d.get("coordinates_rounded", [])], "| layer", od_layer())
print("2121 activity log lines:")
_od_al_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
def od_al(body, reply):
    ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
    ns["_activity_note"]("POST", "/glyph/path", json.dumps(body).encode(), ns["_build_response"](200, reply), "claude-code")
    ns["_act_flush"]()
od_al({"name": "od2_mix", "contours": [{"points": OV, "closed": False}, SQ]}, {"open": True, "drawn": True, "nodes_match": True})
od_al({"name": "od2_arch", "contours": [{"points": OARCH, "closed": False}]}, {"open": True, "drawn": True, "nodes_match": True})
od_al({"name": "od2_sq", "contours": [{"points": SQ, "closed": True}]}, {"open": True, "drawn": True, "nodes_match": True})
for k, v in _od_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
print("2122 route documented            :", '{"points": [...], "closed": false} is drawn OPEN (v0.126)' in src)

# ================= v0.129: /debug/tryshapebox (gated, read only: one inkBox() per element, or one isUnbindedDependecies()) =================
print("\n==== v0.129 /debug/tryshapebox ====")
# Spy fakes: any member the probe should not touch lands in SBP["forbidden"]. The one-font gate is the fake of /debug/tryopen.
SBP = {"ink": [], "dep": 0, "forbidden": [], "mode": {}, "wrap": None, "layer": None}
class SBPSpy:
    def __getattr__(s, a):
        SBP["forbidden"].append(a); raise AttributeError(a)
class SBPRect:
    def __init__(s, l, r, t, b): s.v = (l, r, t, b)
    def left(s): return s.v[0]
    def right(s): return s.v[1]
    def top(s): return s.v[2]
    def bottom(s): return s.v[3]
    def width(s): return s.v[1] - s.v[0]
    def height(s): return s.v[3] - s.v[2]
class SBPShape(SBPSpy):
    def __init__(s, i, box): s.__dict__.update(i=i, box=box)
    def isComponent(s): return True       # v0.177: the layer's componentsCount equals its shape count, so each shape is a component
    def inkBox(s, *a):
        SBP["ink"].append((s.i, a)); m = SBP["mode"]
        if m.get("ink_raises") == s.i: raise RuntimeError("ink boom")
        if m.get("ink_none"): return None
        if m.get("mutates"): SBP["layer"].nodesCount = 99
        return s.box
class SBPLayer(SBPSpy):
    name = "Regular"
    def __init__(s, shapes): s.__dict__.update(_shapes=shapes, nodesCount=48, shapesCount=len(shapes), componentsCount=len(shapes))
    @property
    def shapes(s):
        m = SBP["mode"]
        if m.get("shapes_raises"): raise RuntimeError("shapes boom")
        return tuple(s._shapes) if m.get("shapes_tuple") else s._shapes
class SBPNoDep(SBPSpy):
    def __init__(s, layer): s.__dict__.update(activeLayer=layer, advanceWidth=700.0)
class SBPWrap(SBPNoDep):
    def isUnbindedDependecies(s):
        SBP["dep"] += 1; m = SBP["mode"]
        if m.get("dep_raises"): raise RuntimeError("dep boom")
        return m.get("dep_value", False)
_sb_mods = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "flWorkspace", "CurrentFont")]
_sb_ns = {k: ns[k] for k in ("_find_glyph", "_modern_wrapper")}
def sb_setup(mode=None, count=1, packages=1, shapes=2, wrap=SBPWrap, no_layer=False, font=True):
    boxes = [SBPRect(50, 650, 0, 700), SBPRect(220, 480, 780, 880)]
    SBP.update(ink=[], dep=0, forbidden=[], mode=mode or {})
    SBP["layer"] = None if no_layer else SBPLayer([SBPShape(i, boxes[i % 2]) for i in range(shapes)])
    SBP["wrap"] = wrap(SBP["layer"])
    def mw(g, f):
        if SBP["mode"].get("wrap_raises"): raise RuntimeError("wrap boom")
        return SBP["wrap"], "cached"
    ns["_find_glyph"] = lambda f, n: "G" if n == "sbg" else None
    ns["_modern_wrapper"] = mw
    TO.update(count=count, packages=packages)
    for _m in _tf_mods:
        _m.CountFonts = _to_count; _m.flWorkspace = TOWsCls; _m.CurrentFont = (lambda: object()) if font else (lambda: None)
    ns["_TRYSHAPEBOX"].update(shapebox=0, dependencies=0)
def sb(tag, path, keys=("error", "calls_so_far", "open")):
    c, d = call(path)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| inkBox", SBP["ink"], "| dep", SBP["dep"], "| forbidden", SBP["forbidden"])
    return d
Q = "/debug/tryshapebox?"
B = Q + "stage=shapebox&name=sbg&go=yes"; D = Q + "stage=dependencies&name=sbg&go=yes"
FULL = ("elements", "element_count", "unbound_dependencies", "error", "state_before", "state_after", "side_effect_detected", "calls_so_far")
sb_setup()
sb("2130 shapebox without go          ", Q + "stage=shapebox&name=sbg")
sb("2131 dependencies without go      ", Q + "stage=dependencies&name=sbg")
sb("2132 go must be exactly yes       ", Q + "stage=shapebox&name=sbg&go=maybe")
sb("2133 unknown stage                ", Q + "stage=bind&name=sbg&go=yes")
sb("2134 name with a space            ", Q + "stage=shapebox&name=sb%20g&go=yes")
sb("2135 no name                      ", Q + "stage=shapebox&go=yes")
sb("2136 a name of 41 characters      ", Q + "stage=shapebox&go=yes&name=" + "a" * 41)
for tag, over in (("2137 two fonts open               ", dict(count=2)), ("2138 two packages                ", dict(packages=2)),
                  ("2139 CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("2140 no font open                ", dict(count=0)),
                  ("2141 CurrentFont is None         ", dict(font=False))):
    sb_setup(**over); sb(tag, B)
sb_setup(); sb("2142 a glyph that does not exist  ", Q + "stage=shapebox&name=nope&go=yes")
sb_setup(mode={"wrap_raises": 1}); sb("2143 the wrapper raises           ", B)
sb_setup(no_layer=True); sb("2144 shapebox, no active layer    ", B, keys=("error", "state_before", "calls_so_far"))
sb_setup(); d = sb("2145 shapebox, two elements       ", B, keys=FULL); print("2146  note                     :", d["note"])
sb_setup(shapes=1); sb("2147 shapebox, one element        ", B, keys=("elements", "element_count", "side_effect_detected"))
sb_setup(shapes=0); sb("2148 shapebox, a real empty list  ", B, keys=("elements", "element_count", "error", "side_effect_detected"))
sb_setup(shapes=20); print("2149 shapebox, 20 elements        :", sb("     ", B, keys=("element_count",)).get("element_count"))
sb_setup(shapes=21); sb("2150 shapebox, 21 elements        ", B, keys=FULL[2:4] + ("calls_so_far", "side_effect_detected"))
sb_setup(mode={"shapes_tuple": 1}); sb("2151 layer.shapes is not a list   ", B, keys=("error", "elements", "calls_so_far"))
sb_setup(mode={"shapes_raises": 1}); sb("2152 layer.shapes raises          ", B, keys=("error", "elements", "calls_so_far"))
sb_setup(mode={"ink_raises": 1}); sb("2153 the second inkBox raises     ", B, keys=("elements", "error", "side_effect_detected"))
sb_setup(mode={"ink_none": 1}); sb("2154 inkBox returns None          ", B, keys=("elements", "error"))
sb_setup(mode={"mutates": 1}); sb("2155 a changed node count         ", B, keys=("state_before", "state_after", "side_effect_detected"))
sb_setup(no_layer=True); d = sb("2156 dependencies, no active layer", D, keys=FULL)
for tag, mode in (("2157 dependencies false           ", {}), ("2158 dependencies true            ", {"dep_value": True}), ("2159 it returns 1, not a bool     ", {"dep_value": 1}),
                  ("2160 it returns None             ", {"dep_value": None}), ("2161 it raises                   ", {"dep_raises": 1})):
    sb_setup(mode=mode); sb(tag, D, keys=("unbound_dependencies", "side_effect_detected", "calls_so_far"))
sb_setup(wrap=SBPNoDep); SBP["forbidden"].clear(); sb("2162 the member does not exist     ", D, keys=("unbound_dependencies", "calls_so_far"))
sb_setup()
for _i in range(12): call(B)
sb("2163 shapebox: request 13 refused ", B); print("2164  inkBox calls in 12 runs  :", len(SBP["ink"]))
sb("2165 the other stage still runs   ", D, keys=("unbound_dependencies", "calls_so_far"))
_src129 = "\n".join(l for l in src[src.index("# /debug/tryshapebox (v0.129)"):src.index("# /debug/trykerngroups (v0.103)")].split("\n") if not l.lstrip().startswith("#"))
print("2166 static scan of the probe (code lines):", len(_src129) > 3000, "| forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|remove\w*|bindDependencies|resetInkBox|changed|applyTransform|transform|setProperty\w*)\s*\(", _src129),
      "| subscripts of a native object:", _re83.findall(r"\b(?:shapes|layer|shape|w)\[", _src129),
      "| counter raised before the call:", _src129.index('_TRYSHAPEBOX[stage] += 1') < _src129.index("rows, err = _tryshapebox_boxes(layer)"))
print("2167 route documented            :", "/debug/tryshapebox    stage=shapebox|dependencies" in src)
_sb_al_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
print("2168 activity log, go=yes:")
ns["_activity_note"]("GET", B, b"", ns["_build_response"](200, {"stage": "shapebox", "elements": []}), "claude-code")
ns["_act_flush"]()
for k, v in _sb_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
for k, v in _sb_ns.items(): ns[k] = v
for _m, _a, _v in _sb_mods:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.131: /debug/trynotify (gated S1 research: flags and history positions, ONE flItems notification from a fixed list) =================
print("\n==== v0.131 /debug/trynotify ====")
# Spy fakes: any member the probe should not touch lands in NT["forbidden"]. NT["calls"] holds every notification made.
NT = {"calls": [], "forbidden": [], "mode": {}, "pkg": None, "ws": None, "wrap": None, "npk": 1}
class NTSpy:
    def __getattr__(s, a):
        NT["forbidden"].append(a); raise AttributeError(a)
class NTFlags(NTSpy):
    def __init__(s, **kw): s.__dict__.update(isChanged=False, hasChanges=False, hasHistoryStates=False, _cur=0); s.__dict__.update(kw)
    def currentHistoryState(s):
        m = NT["mode"]
        if m.get("hist_raises"): raise RuntimeError("history boom")
        if m.get("hist_native"): return object()
        return s._cur
    def initialHistoryState(s): return 0
class NTPkg(NTFlags):
    isNull = False
    def __init__(s, **kw): super().__init__(glyphsCount=3, id=77, fgId=5); s.__dict__.update(kw)
    def isEqual(s, other):
        NT["calls"].append(("package", "isEqual", (type(other).__name__,)))
        if NT["mode"].get("equal_raises"): raise RuntimeError("equal boom")
        return other is s
class NTWs(NTFlags):
    def packages(s): return [NT["pkg"]] * NT["npk"]
    currentPackage = property(lambda s: NT["pkg"])
    def findPackageId(s, i):
        NT["calls"].append(("workspace", "findPackageId", (i,)))
        m = NT["mode"]
        if m.get("find_marks"): NT["pkg"].__dict__.update(glyphsCount=4, hasChanges=True)
        if m.get("find_raises"): raise RuntimeError("find boom")
        if m.get("find_none"): return None
        if m.get("find_null"): return NTPkg(isNull=True)
        if m.get("find_badnull"): return NTPkg(isNull=lambda: (_ for _ in ()).throw(RuntimeError("null boom")))
        if m.get("find_other"): return NTPkg()
        return NT["pkg"]
class NTShape(NTSpy):                      # v0.177: the state read counts the shapes flagged isComponent; this one is plain
    def isComponent(s): return False
class NTLayer(NTSpy):
    name = "Regular"; nodesCount = 8; shapesCount = 1; componentsCount = 0; shapes = [NTShape()]
class NTGlyph(NTFlags):
    def __init__(s, **kw): super().__init__(activeLayer=NTLayer(), advanceWidth=500.0, id=9, fgGlyphId=6); s.__dict__.update(kw)
_NT_NAMES = ("notifyChangesApplied", "notifyWorkspaceHasChanges", "notifyPackageUpdated", "notifyPackageContentUpdated", "notifyGlyphUpdated", "notifyFontSelected")
def _nt_notify(where, name):
    def f(*a):
        NT["calls"].append((where, name, tuple(x if isinstance(x, (str, bool, int)) else type(x).__name__ for x in a)))
        m = NT["mode"]
        if m.get("raises"): raise RuntimeError("notify boom")
        if m.get("marks"): NT["pkg"].__dict__.update(hasChanges=True, _cur=1)
        if m.get("adds_glyph"): NT["pkg"].glyphsCount = 4
        return m.get("ret")
    return f
class NTInst(NTSpy): pass
class NTItems: pass
for _n in _NT_NAMES:
    setattr(NTInst, _n, (lambda _f: lambda s, *a: _f(*a))(_nt_notify("instance", _n)))
    setattr(NTItems, _n, staticmethod(_nt_notify("class", _n)))
def _nt_instance():
    if NT["mode"].get("inst_raises"): raise RuntimeError("instance boom")
    return NTInst()
NTItems.instance = staticmethod(_nt_instance)
NTWsCls = type("flWorkspace", (), {"instance": staticmethod(lambda: NT["ws"])})
_nt_mods = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "flWorkspace", "CurrentFont", "flItems")]
_nt_ns = {k: ns[k] for k in ("_find_glyph", "_modern_wrapper")}
def nt_setup(mode=None, count=1, npk=1, font=True, items=True, pkg_kw=None, glyph_kw=None):
    NT.update(calls=[], forbidden=[], mode=mode or {}, npk=npk, pkg=NTPkg(**(pkg_kw or {})), ws=NTWs(), wrap=NTGlyph(**(glyph_kw or {})))
    def mw(g, f):
        if NT["mode"].get("wrap_raises"): raise RuntimeError("wrap boom")
        return NT["wrap"], "cached"
    ns["_find_glyph"] = lambda f, n: "G" if n == "ntg" else None
    ns["_modern_wrapper"] = mw
    TO.update(count=count, packages=npk)
    for _m in _tf_mods:
        _m.CountFonts = _to_count; _m.flWorkspace = NTWsCls; _m.CurrentFont = (lambda: object()) if font else (lambda: None)
        if items: _m.flItems = NTItems
        elif hasattr(_m, "flItems"): delattr(_m, "flItems")
    for _k in ns["_TRYNOTIFY"]: ns["_TRYNOTIFY"][_k] = 0
def nt(tag, path, keys=("error", "calls_so_far", "open")):
    c, d = call(path)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| notify", NT["calls"], "| forbidden", NT["forbidden"])
    return d
Q = "/debug/trynotify?"
S = Q + "stage=state&name=ntg&go=yes"
C = lambda w, on="": Q + "stage=call&which=" + w + "&name=ntg&go=yes" + on
FULL = ("call", "return_value", "call_error", "changed_readings", "side_effect_detected", "calls_so_far")
nt_setup()
nt("2170 state without go             ", Q + "stage=state&name=ntg")
nt("2171 call without go              ", Q + "stage=call&which=changes_applied&name=ntg")
nt("2172 go must be exactly yes       ", Q + "stage=call&which=changes_applied&name=ntg&go=maybe")
nt("2173 unknown stage                ", Q + "stage=restore&name=ntg&go=yes")
nt("2174 which not on the list        ", C("project_saved"))
nt("2175 no which                     ", Q + "stage=call&name=ntg&go=yes")
nt("2176 on must be class or instance ", C("changes_applied", "&on=other"))
nt("2177 name with a space            ", Q + "stage=state&name=nt%20g&go=yes")
nt("2178 no name                      ", Q + "stage=state&go=yes")
nt("2179 a name of 41 characters      ", Q + "stage=state&go=yes&name=" + "a" * 41)
for tag, over in (("2180 two fonts open               ", dict(count=2)), ("2181 two packages                ", dict(npk=2)),
                  ("2182 CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("2183 no font open                ", dict(count=0)),
                  ("2184 CurrentFont is None         ", dict(font=False))):
    nt_setup(**over); nt(tag, C("changes_applied"))
nt_setup(); nt("2185 a glyph that does not exist  ", Q + "stage=call&which=changes_applied&name=nope&go=yes")
nt_setup(mode={"wrap_raises": 1}); nt("2186 the wrapper raises           ", C("changes_applied"))
nt_setup(items=False); nt("2187 the module has no flItems    ", C("changes_applied"))
nt_setup(items=False); print("2188 state does not need flItems :", "state" in nt("     ", S))
nt_setup(); d = nt("2189 state                        ", S, keys=("state", "calls_so_far")); print("2190  note                     :", d["note"])
nt_setup(mode={"hist_raises": 1}); nt("2191 a history getter raises      ", S, keys=("state",))
nt_setup(mode={"hist_native": 1}); nt("2192 a history getter gives a native object", S, keys=("state",))
for tag, w in (("2193 changes_applied              ", "changes_applied"), ("2194 workspace_has_changes        ", "workspace_has_changes"),
               ("2195 package_updated              ", "package_updated"), ("2196 package_content              ", "package_content"),
               ("2197 glyph_updated                ", "glyph_updated")):
    nt_setup(); nt(tag, C(w), keys=FULL)
nt_setup(); nt("2198 on=instance                  ", C("changes_applied", "&on=instance"), keys=FULL)
nt_setup(mode={"inst_raises": 1}); nt("2199 instance() raises            ", C("changes_applied", "&on=instance"), keys=FULL)
nt_setup(mode={"raises": 1}); nt("2200 the call raises              ", C("changes_applied"), keys=FULL + ("state_after",))
nt_setup(mode={"ret": object()}); nt("2201 it returns a native object   ", C("package_updated"), keys=("return_value", "call_error"))
nt_setup(mode={"marks": 1}); nt("2202 the package's state moves    ", C("changes_applied"), keys=FULL)
nt_setup(mode={"adds_glyph": 1}); nt("2203 a glyph appears              ", C("package_updated"), keys=FULL)
nt_setup(pkg_kw={"glyphsCount": "x"}); nt("2204 count not comparable         ", C("package_updated"), keys=("side_effect_detected",))
nt_setup(pkg_kw={"id": "77"}); nt("2205 package id not a number      ", C("package_content"))
nt_setup(pkg_kw={"id": True}); nt("2206 package id is a bool         ", C("glyph_updated"))
nt_setup(glyph_kw={"id": None}); nt("2207 glyph id is None             ", C("glyph_updated"))
nt_setup()
for _i in range(3): call(C("changes_applied"))
nt("2208 request 4 refused            ", C("changes_applied")); print("2209  calls made in 4 requests  :", len(NT["calls"]))
nt("2210 another call still runs      ", C("package_updated"), keys=("call", "calls_so_far"))
nt_setup()
for _i in range(20): call(S)
nt("2211 state: request 21 refused    ", S)
_src131 = "\n".join(l for l in src[src.index("# /debug/trynotify (v0.131)"):src.index("# /debug/trynames (v0.137)")].split("\n") if not l.lstrip().startswith("#"))   # v0.140: ends before /debug/trynames, which calls changed() on purpose
print("2212 static scan of the probe (code lines):", len(_src131) > 3000, "| forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close\w*|release|remove\w*|changed|restoreHistoryState|clearAboveHistory|historyStates|blockUpdate|unblockUpdate)\s*\(", _src131),
      "| subscripts of a native object:", _re83.findall(r"\b(?:pkg|ws|w|items|mod)\[", _src131),
      "| counter raised before the call:", _src131.rindex('_TRYNOTIFY[key] += 1') < _src131.index("before = _trynotify_snapshot"), _src131.index("before = _trynotify_snapshot") < _src131.index("make_call(items if"))
print("2213 route documented, registered once:", "/debug/trynotify      stage=state|call" in src, src.count('path == "/debug/trynotify"') == 1)
# v0.135: stage=ids, id_from, font_selected, and the guard that a number must fit a uint (live 731, 732: the object ids were refused by FontLab)
IDS = Q + "stage=ids&name=ntg&go=yes"
IK = ("reads", "lookups", "changed_readings", "side_effect_detected", "error", "calls_so_far")
FG = "&id_from=fg"
_NT_BIG = 1379668187344
_nt_boom = lambda: (_ for _ in ()).throw(RuntimeError("read boom"))
nt_setup(); nt("2213a ids without go              ", Q + "stage=ids&name=ntg")
nt_setup(); nt("2213b ids, all small              ", IDS, keys=IK)
nt_setup(pkg_kw={"id": _NT_BIG}); nt("2213c ids, the object id too large", IDS, keys=IK)
nt_setup(pkg_kw={"id": -1}); nt("2213d ids, a negative id           ", IDS, keys=IK)
nt_setup(pkg_kw={"fgId": _nt_boom}); nt("2213e ids, fgId cannot be read     ", IDS, keys=IK)
nt_setup(pkg_kw={"fgId": object()}); nt("2213f ids, fgId is a native object ", IDS, keys=IK)
nt_setup(glyph_kw={"fgGlyphId": object()}); nt("2213g ids, fgGlyphId is native     ", IDS, keys=IK)
nt_setup(mode={"find_raises": 1}); nt("2213h ids, findPackageId raises    ", IDS, keys=IK)
nt_setup(mode={"find_none": 1}); nt("2213i ids, findPackageId gives None", IDS, keys=IK)
nt_setup(mode={"find_null": 1}); nt("2213j ids, a null package: no isEqual", IDS, keys=IK)
nt_setup(mode={"find_other": 1}); nt("2213k ids, another package         ", IDS, keys=IK)
nt_setup(mode={"equal_raises": 1}); nt("2213l ids, isEqual raises          ", IDS, keys=IK)
nt_setup(mode={"adds_glyph": 0}, items=False); print("2213m ids does not need flItems    :", "reads" in nt("      ", IDS))
nt_setup(count=2); nt("2213n ids, two fonts open          ", IDS, keys=IK)
nt_setup()
for _i in range(3): call(IDS)
nt("2213o ids: request 4 refused       ", IDS, keys=IK); print("2213p  findPackageId calls in 4 requests:", sum(1 for c in NT["calls"] if c[1] == "findPackageId"))
for tag, w in (("2213q font_selected, object id     ", "font_selected"),):
    nt_setup(); nt(tag, C(w), keys=FULL)
for tag, w in (("2213r font_selected, fg            ", "font_selected"), ("2213s package_content, fg          ", "package_content"), ("2213t glyph_updated, fg            ", "glyph_updated")):
    nt_setup(); nt(tag, C(w, FG), keys=FULL)
nt_setup(); print("2213u the reply names id_from      :", call(C("font_selected", FG))[1].get("id_from"), call(C("package_updated"))[1].get("id_from"))
nt_setup(); nt("2213v id_from not on the list      ", C("font_selected", "&id_from=other"))
nt_setup(); nt("2213w id_from on a call with no id ", C("package_updated", FG))
for tag, kw, w, on in (("2213x the object id 731 refused    ", dict(pkg_kw={"id": _NT_BIG}), "package_content", ""), ("2213y font_selected, too large     ", dict(pkg_kw={"id": _NT_BIG}), "font_selected", ""),
                       ("2213z one above the largest uint   ", dict(pkg_kw={"fgId": 4294967296}), "font_selected", FG), ("2213aa a negative number           ", dict(pkg_kw={"fgId": -1}), "font_selected", FG),
                       ("2213ab the glyph id too large       ", dict(glyph_kw={"fgGlyphId": _NT_BIG}), "glyph_updated", FG), ("2213ac fgGlyphId a native object    ", dict(glyph_kw={"fgGlyphId": object()}), "glyph_updated", FG),
                       ("2213ad fgId cannot be read          ", dict(pkg_kw={"fgId": _nt_boom}), "package_content", FG), ("2213ae fgId is a bool               ", dict(pkg_kw={"fgId": True}), "font_selected", FG)):
    nt_setup(**kw); nt(tag, C(w, on))
for tag, v in (("2213af the largest uint is allowed   ", 4294967295), ("2213ag zero is allowed              ", 0)):
    nt_setup(pkg_kw={"fgId": v}); nt(tag, C("font_selected", FG), keys=FULL)
nt_setup()
for _i in range(3): call(C("font_selected", FG))
nt("2213ah font_selected: request 4 refused", C("font_selected", FG)); print("2213ai  calls made in 4 requests  :", len(NT["calls"]))
print("2213aj id_from and ids documented  :", "id_from=object|fg" in src, "stage=state|call|ids" in src, '"id_from"' in src)
nt_setup(mode={"find_marks": 1}); nt("2213ak ids, findPackageId changes the font", IDS, keys=("changed_readings", "side_effect_detected"))
nt_setup(mode={"find_badnull": 1}); nt("2213al ids, isNull cannot be read, no isEqual", IDS, keys=("lookups",))
_nt_al_saved = {k: ns[k] for k in ("_now_hms", "_clock")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
print("2214 activity log, go=yes:")
ns["_activity_note"]("GET", C("changes_applied"), b"", ns["_build_response"](200, {"stage": "call", "which": "changes_applied"}), "claude-code")
ns["_act_flush"]()
for k, v in _nt_al_saved.items(): ns[k] = v
ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
for k, v in _nt_ns.items(): ns[k] = v
for _m, _a, _v in _nt_mods:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.132: the changed mark after a verified, synced glyph write (live 657-667 are the reason; stubs only) =================
print("\n==== v0.132 the changed mark ====")
MK = {"calls": [], "seq": [], "mode": {}}
class MKW:
    @property
    def activeLayer(s):
        m = MK["mode"]
        if m.get("layer_raises"): raise RuntimeError("layer boom")
        return None if m.get("no_layer") else "L"
    @property
    def hasChanges(s):
        m = MK["mode"]
        if m.get("has_raises"): raise RuntimeError("has boom")
        return m.get("has", True)
class MKItems:
    @staticmethod
    def notifyChangesApplied(*a):
        MK["calls"].append(tuple(x if isinstance(x, (str, bool)) else type(x).__name__ for x in a)); MK["seq"].append("notify")
        if MK["mode"].get("raises"): raise RuntimeError("notify boom")
_mk_keys = ("_find_glyph", "_modern_wrapper", "_auto_sync", "_guard_register", "_guard_state", "_MARK_CHANGED", "_guard_mark", "_mark_font_changed", "_repaint_viewport",
            "_open_font", "_guard_decide", "_other_glyphs_with_unicode", "_one_master_problem", "_modern_edit_target")
_mk_ns = {k: ns[k] for k in _mk_keys}
_mk_mods = [(m, getattr(m, "flItems", None)) for m in _tf_mods]
def mk_setup(mode=None, items=True, sync=True):
    MK.update(calls=[], seq=[], mode=mode or {})
    for k, v in _mk_ns.items(): ns[k] = v
    def mw(g, f):
        if MK["mode"].get("wrap_raises"): raise RuntimeError("wrap boom")
        return MKW(), "cached"
    def auto(f, n):
        MK["seq"].append("sync")
        return {"attempted": True, "synced": sync, "verdict": "synced" if sync else "unsynced"}
    ns.update(_find_glyph=lambda f, n: None if n == "nope" else "G", _modern_wrapper=mw, _auto_sync=auto, _guard_register=lambda *a: None, _guard_state=lambda f: {"glyphs": {}})
    for _m in _tf_mods:
        if items: _m.flItems = MKItems
        elif hasattr(_m, "flItems"): delattr(_m, "flItems")
def mk(tag, how="width", name="g", no_mark=None):
    r = {}
    ns["_guard_mark"]("F", name, how, r, no_mark=no_mark)
    print(tag, ":", r.get("fontlab_changed_mark", "<no field>"), "| synced", r.get("synced_with_fontlab"), "| notify", MK["calls"], "| order", MK["seq"])
    return r
mk_setup(); mk("2220 width, synced                ")
for tag, how in (("2221 create                    ", "layer_created"), ("2222 sidebearings              ", "sidebearings"),
                 ("2223 polygon                   ", "draw_polygon"), ("2224 path                      ", "draw_path")):
    mk_setup(); mk(tag, how=how)
mk_setup(); mk("2225 a probe's write is not marked", how="tryopen")
mk_setup(); mk("2226 the caller's reason          ", no_mark="the width did not change")
mk_setup(sync=False); mk("2227 sync not confirmed            ")
mk_setup(); ns["_MARK_CHANGED"] = False; mk("2228 switched off                  ")
mk_setup(items=False); mk("2229 no flItems                    ")
mk_setup(); mk("2230 the glyph is gone             ", name="nope")
mk_setup(mode={"wrap_raises": 1}); mk("2231 the wrapper raises            ")
mk_setup(mode={"no_layer": 1}); mk("2232 no modern layer               ")
mk_setup(mode={"layer_raises": 1}); mk("2233 the layer read raises         ")
mk_setup(mode={"raises": 1}); mk("2234 the call raises               ")
mk_setup(mode={"has": False}); mk("2235 hasChanges false after the call")
mk_setup(mode={"has": "x"}); mk("2236 hasChanges is not a bool      ")
mk_setup(mode={"has_raises": 1}); mk("2237 hasChanges raises             ")
mk_setup()
def _mk_boom(*a): raise RuntimeError("mark boom")
ns["_mark_font_changed"] = _mk_boom
print("2238 a failure in the mark never fails the write:", sorted(mk("     ").keys()))
class MKAdv:
    def __init__(s, v, sticks=True): s.__dict__.update(v=v, sticks=sticks)
    advanceWidth = property(lambda s: s.v, lambda s, x: s.__dict__.update(v=x if s.sticks else s.v))
GM = []
def mk_width(tag, start, want, sticks=True):
    mk_setup(); GM.clear()
    ns["_guard_mark"] = lambda f, n, h, r, no_mark=None: GM.append((h, no_mark))
    ns["_repaint_viewport"] = lambda: True
    r = ns["_set_width_modern"]({"w": MKAdv(start, sticks), "tr": None, "font": "F"}, "g", want)
    print(tag, ": set", r.get("set"), "| guard_mark", GM)
mk_width("2239 width changes                 ", 400.0, 500)
mk_width("2240 width stays the same          ", 500.0, 500)
mk_width("2241 width not confirmed           ", 400.0, 500, sticks=False)
class MKLegacy:
    def __init__(s, **kw): s.__dict__.update(kw)
    def update(s): MK["seq"].append("update")
mk_setup(); ns["_guard_decide"] = lambda f: (True, {})
_mk_g = MKLegacy(name="g", width=0); ns["_find_glyph"] = lambda f, n: _mk_g
print("2242 legacy width route            :", ns["_set_width_legacy"](MKLegacy(), _mk_g, "g", 300).get("fontlab_changed_mark"), "| notify", MK["calls"])
print("2243 the other write sites         :", ['"sidebearings", result, no_mark=None if result["set"] else' in src, '"draw_polygon", result, no_mark=None if result["drawn"] else' in src, '"draw_path", result, no_mark=None if result["drawn"] else' in src])
def mk_uni(tag, start, want, guard_ok=True, raises=False):
    mk_setup()
    class G(MKLegacy):
        name = "g"
        def __setattr__(s, k, v):
            if raises and k == "unicode": raise RuntimeError("unicode boom")
            object.__setattr__(s, k, v)
    g = G(); object.__setattr__(g, "unicode", start)
    F = MKLegacy(glyphs=[g])
    MR = []
    ns.update(_open_font=lambda: F, _guard_decide=lambda f: (guard_ok, {}), _other_glyphs_with_unicode=lambda *a: {}, _find_glyph=lambda f, n: g,
              _mark_font_changed=lambda f, n, h: MR.append(h) or {"called": True})
    r = ns["set_glyph_unicode"]("g", want)
    print(tag, ": set", r.get("set"), "| mark", r.get("fontlab_changed_mark", "<no field>"), "| calls", MR)
mk_uni("2244 Unicode changes               ", None, 66)
mk_uni("2245 Unicode stays the same        ", 66, 66)
mk_uni("2246 Unicode cleared               ", 66, 0)
mk_uni("2247 another glyph unsynced        ", None, 66, guard_ok=False)
mk_uni("2248 the write raises              ", None, 66, raises=True)
def mk_create(tag, problem=None, ctx=None, refusal=None):
    mk_setup(); GM.clear()
    ns.update(_one_master_problem=lambda: problem, _modern_edit_target=lambda n, create_layer=False: (ctx, refusal))
    ns["_guard_mark"] = lambda f, n, h, r, no_mark=None: GM.append((h, no_mark))
    print(tag, ":", ns["_create_glyph_layer"]("g"), "| guard_mark", GM)
mk_create("2249 several masters               ", problem="two masters")
mk_create("2250 the layer cannot be made      ", refusal={"reason": "no name"})
mk_create("2251 the layer is made             ", ctx={"layer_created": "Regular", "layer_name_source": "package master", "font": "F"})
mk_create("2252 no layer made here            ", ctx={"font": "F"})
# v0.133: a verified delete is marked through one surviving glyph (live 684-687 are the reason; stubs only)
MD = []
def mkd_setup(no_layer=(), **kw):
    mk_setup(**kw); MD.clear()
    class W(MKW):
        def __init__(s, n): s.n = n
        activeLayer = property(lambda s: None if s.n in no_layer else "L")
    def mw(g, f):
        MD.append(g)
        return W(g), "cached"
    ns.update(_find_glyph=lambda f, n: n, _modern_wrapper=mw)
def mkd(tag, names, **kw):
    mkd_setup(**kw)
    print(tag, ":", ns["_mark_font_changed_after_delete"]("F", names), "| tried", MD, "| notify", MK["calls"])
mkd("2254 first ordinary glyph        ", [".notdef", "a", "b"])
mkd("2255 the first has no layer      ", [".notdef", "a", "b"], no_layer=("a",))
mkd("2256 only .notdef survives       ", [".notdef"])
mkd("2257 nothing survives            ", [])
mkd("2258 none has a layer            ", [".notdef", "a", "b"], no_layer=("a", "b"))
_mk25 = ["g%d" % i for i in range(25)]
mkd_setup(no_layer=tuple(_mk25)); _r = ns["_mark_font_changed_after_delete"]("F", _mk25)
print("2259 tries are capped            :", len(MD), "of", len(_mk25), "|", _r)
mkd("2260 the call raises: one call   ", ["a", "b"], mode={"raises": 1})
mkd_setup(); ns["_MARK_CHANGED"] = False
print("2261 switched off                :", ns["_mark_font_changed_after_delete"]("F", ["a"]), "| tried", MD)
mkd("2262 no flItems                  ", ["a"], items=False)
mkd_setup(); ns["_mark_font_changed"] = _mk_boom
print("2263 a failure never raises      :", ns["_mark_font_changed_after_delete"]("F", ["a"]))
_mk_confirm = ns["_confirm_deletion"]
def mk_delete(tag, names, target="b", confirm=True, removes=True, raises=False, guard_ok=True):
    mkd_setup()
    class F:
        def __init__(s): s.gl = [MKLegacy(name=n) for n in names]
        glyphs = property(lambda s: list(s.gl))
        def removeGlyph(s, n):
            MK["seq"].append("remove")
            if removes: s.gl = [g for g in s.gl if g.name != n]
            if raises: raise RuntimeError("remove boom")
        def update(s): MK["seq"].append("update")
    f = F()
    ns.update(_open_font=lambda: f, _guard_decide=lambda x: (guard_ok, {}),
              _confirm_deletion=lambda n, s=45: {"answer": "yes" if confirm else "no", "seconds": s})   # v0.203: the dialog's result
    r = ns["delete_glyph"](target)
    print(tag, ":", r.get("deleted"), "| mark", r.get("fontlab_changed_mark", "<no field>"), "| call_error", r.get("call_error"), "| order", MK["seq"])
mk_delete("2264 verified delete             ", [".notdef", "a", "b"])
mk_delete("2265 update skipped by the guard ", [".notdef", "a", "b"], guard_ok=False)
mk_delete("2266 declined                    ", [".notdef", "a", "b"], confirm=False)
mk_delete("2267 no such glyph               ", [".notdef", "a"])
mk_delete("2268 still there after the call  ", [".notdef", "a", "b"], removes=False)
mk_delete("2269 raised, still there         ", [".notdef", "a", "b"], removes=False, raises=True)
mk_delete("2270 raised, but gone            ", [".notdef", "a", "b"], raises=True)
mk_delete("2271 only .notdef survives       ", [".notdef", "b"])
ns["_confirm_deletion"] = _mk_confirm
# v0.134: a kerning write is marked through one glyph of a changed pair (research 713-717 is the reason; stubs only)
def _ke(left, right, changed=True): return {"left": left, "right": right, "changed": changed}
def mkk(tag, results, **kw):
    mkd_setup(**kw)
    print(tag, ":", ns["_mark_font_changed_after_kerning"]("F", results), "| tried", MD, "| notify", MK["calls"])
mkk("2272 the left glyph of the pair  ", [_ke("a", "b")])
mkk("2273 the same value: no call     ", [_ke("a", "b", False)])
mkk("2274 changed unknown: no call    ", [_ke("a", "b", None)])
mkk("2275 the first CHANGED pair      ", [_ke("a", "b", False), _ke("c", "d")])
mkk("2276 left has no layer: right    ", [_ke("a", "b")], no_layer=("a",))
mkk("2277 neither side: next changed  ", [_ke("a", "b"), _ke("c", "d")], no_layer=("a", "b"))
mkk("2278 unchanged pair's glyphs skipped", [_ke("x", "y", False), _ke("a", "b")], no_layer=("a", "b"))
mkk("2279 none can be notified        ", [_ke("a", "b")], no_layer=("a", "b"))
mkk("2280 .notdef on the left: right  ", [_ke(".notdef", "b")])
mkk("2281 only .notdef                ", [_ke(".notdef", ".notdef")])
mkk("2282 a glyph is tried once       ", [_ke("a", "a"), _ke("a", "b")], no_layer=("a",))
_mkk30 = [_ke("l%d" % i, "r%d" % i) for i in range(30)]
mkd_setup(no_layer=tuple("l%d" % i for i in range(30)) + tuple("r%d" % i for i in range(30))); _r = ns["_mark_font_changed_after_kerning"]("F", _mkk30)
print("2283 tries are capped            :", len(MD), "of 60 |", _r)
mkk("2284 the call raises: one call   ", [_ke("a", "b")], mode={"raises": 1})
mkk("2285 no results                  ", [])
mkd_setup(); ns["_MARK_CHANGED"] = False
print("2286 switched off                :", ns["_mark_font_changed_after_kerning"]("F", [_ke("a", "b")]), "| tried", MD)
mkk("2287 no flItems                  ", [_ke("a", "b")], items=False)
mkd_setup(); ns["_mark_font_changed"] = _mk_boom
print("2288 a failure never raises      :", ns["_mark_font_changed_after_kerning"]("F", [_ke("a", "b")]))
mkd_setup()
print("2289 not a list of dicts         :", ns["_mark_font_changed_after_kerning"]("F", [5]))
print("2290 the kerning title, two routes:", ns["_MARK_TITLES"].get("kerning"), "|", src.count("_mark_font_changed_after_kerning(font, results)"), "| the delete keeps its own target rule:", '_mark_through_first(font, candidates, "delete")' in src)
# v0.136: one notifyPackageContentUpdated(fgId) after a kerning write that changed an entry (live 738, 741-743 are the reason; stubs only)
MKR = []; _rk_forbid = []
def _mkr(*a):
    MKR.append(a)
    if MK["mode"].get("refresh_raises"): raise RuntimeError("refresh boom")
MKItems.notifyPackageContentUpdated = staticmethod(_mkr)
class RKPkg:
    def __init__(s, fg): s.__dict__["fgId"] = fg
    def __getattr__(s, a):
        _rk_forbid.append(a); raise AttributeError(a)
_rk_boom = lambda: (_ for _ in ()).throw(RuntimeError("fgId boom"))
def rk(tag, results, fg=1, **kw):
    mkd_setup(**kw); MKR.clear(); _rk_forbid.clear()
    print(tag, ":", ns["_refresh_kerning_panel"](RKPkg(fg), results), "| notify", MKR, "| forbidden", _rk_forbid)
rk("2291a one pair changed            ", [_ke("a", "b")])
rk("2291b the same value: no call     ", [_ke("a", "b", False)])
rk("2291c changed unknown: no call    ", [_ke("a", "b", None)])
rk("2291d no results                  ", [])
rk("2291e two changed: one call       ", [_ke("a", "b"), _ke("c", "d")])
rk("2291f a later pair changed        ", [_ke("a", "b", False), _ke("c", "d")])
rk("2291g stopped partway             ", [_ke("a", "b"), {"left": "c", "right": "d", "status": "not attempted"}])
rk("2291h the object id is refused    ", [_ke("a", "b")], fg=1379668187344)
rk("2291i the largest uint            ", [_ke("a", "b")], fg=4294967295)
rk("2291j one above it                ", [_ke("a", "b")], fg=4294967296)
rk("2291k zero                        ", [_ke("a", "b")], fg=0)
rk("2291l negative                    ", [_ke("a", "b")], fg=-1)
rk("2291m a bool                      ", [_ke("a", "b")], fg=True)
rk("2291n text                        ", [_ke("a", "b")], fg="1")
rk("2291o None                        ", [_ke("a", "b")], fg=None)
rk("2291p a native object             ", [_ke("a", "b")], fg=object())
rk("2291q fgId cannot be read         ", [_ke("a", "b")], fg=_rk_boom)
rk("2291r the call raises             ", [_ke("a", "b")], mode={"refresh_raises": 1})
rk("2291s no flItems                  ", [_ke("a", "b")], items=False)
_rk_sw = ns["_REFRESH_KERNING_PANEL"]; ns["_REFRESH_KERNING_PANEL"] = False
rk("2291t switched off                ", [_ke("a", "b")]); ns["_REFRESH_KERNING_PANEL"] = _rk_sw
rk("2291u not a list of dicts         ", [5])
print("2291v the call in the source      :", src.count("items.notifyPackageContentUpdated(pid)") == 1, "| switch on:", _rk_sw is True, "| the two kerning routes ask once each:", src.count("refresh = _refresh_kerning_panel(pkg, results)") == 2,
      "| the mark first:", src.index("mark = _mark_font_changed_after_kerning(font, results)") < src.index("refresh = _refresh_kerning_panel(pkg, results)"))
del MKItems.notifyPackageContentUpdated
print("2253 the call in the source        :", src.count("items.notifyChangesApplied(_MARK_TITLES[how], w, False)") == 1, "| switch on:", ns["_MARK_CHANGED"] is True or _mk_ns["_MARK_CHANGED"] is True)
for k, v in _mk_ns.items(): ns[k] = v
for _m, _v in _mk_mods:
    if _v is None:
        if hasattr(_m, "flItems"): delattr(_m, "flItems")
    else:
        _m.flItems = _v

# ================= v0.137: /debug/trynames (P0.4 research: write one package name; gated; faked package, font and flItems) =================
print("\n==== v0.137 /debug/trynames ====")
_tn_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace", "flItems")]
TN = {"calls": [], "set_raises": False, "notify": [], "notify_raises": False}
class TNPInfo:
    """v0.143: a package's info object: the two Preferred names; an assignment is recorded and can raise."""
    openTypeNamePreferredFamilyName, openTypeNamePreferredSubfamilyName = "Unnamed", "Regular"
    def __setattr__(s, a, v):
        TN["calls"].append(f"info {a}={v!r}")
        if TN.get("info_raises"): raise RuntimeError("info read-only")
        object.__setattr__(s, a, v)
class TNPkg:
    """a font package: the names, fileName, isNull and fgId may be read; every other read and every assignment is recorded."""
    def __repr__(s): return "<TNPkg>"                  # v0.140: printed when passed to notifyPropertiesChanged; no memory address
    def __init__(s, **kw):
        d = {"psn": "Unnamed-Regular", "ffn": "Unnamed Regular", "tfn": "Unnamed", "tsn": "Regular", "sgn": "Unnamed",
             "fileName": "Unnamed Regular.xfo", "isNull": False, "fgId": 7, "info": TNPInfo(), "elidedName": "Unnamed Regular"}   # v0.144: elidedName
        d.update(kw); object.__setattr__(s, "_d", d)
    def __getattr__(s, a):
        d = object.__getattribute__(s, "_d")
        if a in d: return d[a]
        TN["calls"].append("read " + a); raise AttributeError(a)
    def __setattr__(s, a, v):
        TN["calls"].append(f"set {a}={v!r}")
        if TN["set_raises"]: raise RuntimeError("read-only property")
        object.__getattribute__(s, "_d")[a] = v
class TNInfo:
    familyName, styleName, postscriptFullName, postscriptFontName = "Unnamed", "Regular", "Unnamed Regular", "Unnamed-Regular"
    def __setattr__(s, a, v):                       # v0.139: a legacy setter is recorded, and can raise
        TN["calls"].append(f"legacy {a}={v!r}")
        if TN.get("legacy_raises"): raise RuntimeError("legacy read-only")
        object.__setattr__(s, a, v)
class TNFont:
    def __init__(s, info_raises=False): s._r, s._info = info_raises, TNInfo()
    @property
    def info(s):
        if s._r: raise RuntimeError("info boom")
        return s._info
def _tn_notify(name):
    def f(*a):
        TN["notify"].append((name,) + a)
        if TN["notify_raises"]: raise RuntimeError("notify boom")
    return staticmethod(f)
class TNItems:
    notifyPackageContentUpdated = _tn_notify("content")
    notifyPackageUpdated = _tn_notify("package")         # v0.138
    notifyPackagesUpdated = _tn_notify("packages")       # v0.138
    notifyModelChanged = _tn_notify("model")             # v0.140
    notifyPropertiesChanged = _tn_notify("properties")   # v0.140
    notifyChangesApplied = _tn_notify("applied")         # v0.141
    notifyPackageReaded = _tn_notify("readed")           # v0.141
    notifyPackageAdded = _tn_notify("added")             # v0.141
def tn_setup(pkg=None, count=1, npk=1, items=True, font=None):
    pkg = pkg if pkg is not None else TNPkg()
    class _WS:
        @staticmethod
        def instance():
            return type("TNWs", (), {"currentPackage": pkg, "packages": lambda s: [pkg] * npk})()
    for _m in _tf_mods:
        _m.CountFonts = lambda: count
        _m.CurrentFont = lambda f=font or TNFont(): f
        _m.flWorkspace = _WS
        if items: _m.flItems = TNItems
        elif hasattr(_m, "flItems"): delattr(_m, "flItems")
    TN.update(calls=[], set_raises=False, notify=[], notify_raises=False, legacy_raises=False, info_raises=False)
    return pkg
def tn(tag, query, keys=("error",), **kw):
    tn_setup(**kw); c, d = call("/debug/trynames?" + query)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", TN["calls"], "| notify", TN["notify"])
    return d
def tn_reset(): ns["_TRYNAMES"].update(set=0, content=0, package=0, packages=0, model=0, properties=0, changed=0, applied=0, readed=0, added=0,
                                       store=0, legacy_set=0, info_set=0, title=0)
tn_reset()
tn("2292a no stage                        ", "")
tn("2292b state, one font                 ", "stage=state", keys=("state", "calls_so_far"))
tn("2292c state, two fonts: refused       ", "stage=state", count=2)
tn("2292d state, one font, two packages   ", "stage=state", npk=2)
tn("2292e state, no font open             ", "stage=state", count=0)
tn("2292f set without go                  ", "stage=set&field=tfn&value=Nm%20Api")
tn("2292g set, unknown field              ", "stage=set&field=fileName&value=x&go=yes")
tn("2292h set, empty value                ", "stage=set&field=tfn&value=&go=yes")
tn("2292i set, 64 characters              ", "stage=set&field=tfn&value=" + "a" * 64 + "&go=yes")
tn("2292j set, 63 characters              ", "stage=set&field=tfn&value=" + "a" * 63 + "&go=yes", keys=("error", "read_back_equal"))
tn("2292k set, not ASCII                  ", "stage=set&field=tfn&value=Nm%C3%A9&go=yes")
tn("2292l set, a control character        ", "stage=set&field=tfn&value=Nm%0ATest&go=yes")
tn("2292m set, a leading space            ", "stage=set&field=tfn&value=%20Nm&go=yes")
tn("2292n set, psn with a space           ", "stage=set&field=psn&value=Nm%20Api-Regular&go=yes")
tn_reset()
_d = tn("2292o set tfn                        ", "stage=set&field=tfn&value=Nm%20Api&go=yes", keys=("call", "call_error", "read_back_equal", "changed_readings", "calls_so_far"))
print("2292p before / after               :", _d["state_before"]["package"]["tfn"], "->", _d["state_after"]["package"]["tfn"], "| legacy family", _d["state_after"]["legacy"]["familyName"],
      "| fileName", _d["state_after"]["package"]["fileName"])
tn("2292q set psn without a space         ", "stage=set&field=psn&value=NmApi-Regular&go=yes", keys=("call", "read_back_equal", "changed_readings"))
_tnp = TNPkg(); tn_setup(pkg=_tnp); TN["set_raises"] = True; _c, _d = call("/debug/trynames?stage=set&field=ffn&value=Nm%20Api%20Regular&go=yes")
print("2292r the setter raises            :", _c, _d.get("call_error"), "| read back", _d.get("read_back_equal"), "| changed", _d.get("changed_readings"), "| calls", TN["calls"])
tn("2292s a name that is not text       ", "stage=state", keys=("state",), pkg=TNPkg(sgn=5, ffn=lambda: TN["calls"].append("ffn()")))
tn("2292t font.info raises              ", "stage=state", keys=("state",), font=TNFont(info_raises=True))
tn_reset(); ns["_TRYNAMES"]["set"] = 10
tn("2292u set: the limit is used up    ", "stage=set&field=tfn&value=Nm&go=yes", keys=("error", "calls_so_far"))
tn_reset()
tn("2292v refresh without go            ", "stage=refresh")
tn("2292w refresh                       ", "stage=refresh&go=yes", keys=("call", "call_error", "changed_readings", "calls_so_far"))
tn("2292x refresh, fgId too large       ", "stage=refresh&go=yes", pkg=TNPkg(fgId=1379668187344))
tn("2292y refresh, fgId not a number    ", "stage=refresh&go=yes", pkg=TNPkg(fgId="7"))
tn("2292z refresh, no flItems           ", "stage=refresh&go=yes", items=False)
tn_setup(); TN["notify_raises"] = True; _c, _d = call("/debug/trynames?stage=refresh&go=yes")
print("2293a the refresh raises           :", _c, _d.get("call_error"), "| notify", TN["notify"])
tn_reset(); ns["_TRYNAMES"]["content"] = 3
tn("2293b refresh: the limit is used up", "stage=refresh&go=yes", keys=("error", "calls_so_far"))
tn_reset()
tn("2293c set refused: nothing counted  ", "stage=set&field=tfn&value=%20x&go=yes", keys=("error",))
print("2293d counters after a refusal     :", dict(ns["_TRYNAMES"]))
_tn_src = src[src.index("def debug_try_names("):src.index("# /debug/tryshapebox (v0.129)")]
_tn_code = "\n".join(l.split("#")[0] for l in _tn_src.splitlines())     # comments dropped; its strings hold no call text
print("2293e static scan: setattr calls:", _re83.findall(r"setattr\([^)]*\)", _tn_code), "| calls on pkg:", _re83.findall(r"\bpkg\.\w+\(", _tn_code),
      "| forbidden names:", [n for n in ("collectNames", ".update(", ".save(", ".close(", "export") if n in _tn_code],    # v0.144: title_name is called once, in stage=title (2300)
      "| store_font_info fetched once:", _tn_code.count('getattr(pkg, "store_font_info", None)') == 1,
      "| route passes field and value:", 'debug_try_names((query.get("stage")' in src and '(query.get("value") or [""])[0]' in src,
      "| listed in the docstring:", "/debug/trynames" in src[:src.index('"""', 3)], "| product refresh text once:", src.count("items.notifyPackageContentUpdated(pid)") == 1)
# v0.138: stage=refresh&which=content|package|packages, 3 per which and listener run (856-861: the first refresh call left the FONTS panel stale)
tn_reset()
tn("2294a which=packages                ", "stage=refresh&which=packages&go=yes", keys=("which", "call", "call_error", "changed_readings", "calls_so_far"))
tn("2294b which=package                 ", "stage=refresh&which=package&go=yes", keys=("which", "call", "call_error", "calls_so_far"))
tn("2294c which=content, named          ", "stage=refresh&which=content&go=yes", keys=("which", "call", "calls_so_far"))
tn("2294d unknown which                 ", "stage=refresh&which=all&go=yes")
tn("2294e unknown which, no go          ", "stage=refresh&which=all")
tn("2294f packages without go           ", "stage=refresh&which=packages")
tn("2294g package without go            ", "stage=refresh&which=package")
tn("2294h package, fgId too large       ", "stage=refresh&which=package&go=yes", pkg=TNPkg(fgId=1379668187344))
tn("2294i packages needs no fgId        ", "stage=refresh&which=packages&go=yes", keys=("call", "call_error"), pkg=TNPkg(fgId="7"))
tn("2294j packages, no flItems          ", "stage=refresh&which=packages&go=yes", items=False)
tn_reset(); ns["_TRYNAMES"]["packages"] = 3
tn("2294k packages used up              ", "stage=refresh&which=packages&go=yes", keys=("error", "calls_so_far"))
tn("2294l package still allowed         ", "stage=refresh&which=package&go=yes", keys=("call", "calls_so_far"))
tn_reset(); ns["_TRYNAMES"]["package"] = 3
tn("2294m package used up               ", "stage=refresh&which=package&go=yes", keys=("error", "calls_so_far"))
tn_reset()
tn("2294n which ignored for set         ", "stage=set&field=tsn&value=Bold&which=all&go=yes", keys=("call", "read_back_equal", "calls_so_far"))
tn_setup(); TN["notify_raises"] = True; _c, _d = call("/debug/trynames?stage=refresh&which=packages&go=yes")
print("2294o packages raises             :", _c, _d.get("call_error"), "| notify", TN["notify"], "| counted", ns["_TRYNAMES"]["packages"])
print("2294p limits and route            :", ns["_TRYNAMES_MAX_REFRESH"], sorted(ns["_TRYNAMES_REFRESH"]), "| route passes which:", '(query.get("which") or ["content"])[0]' in src)
# v0.139: stage=store (one flPackage.store_font_info(fgPackage)) and stage=legacy_set (one font.info.familyName = V), 3 each (856-863 found no redraw)
class TNFg: pass
def _tn_store(copy_family=None, raises=False):
    def f(fg):
        TN["calls"].append(f"store_font_info({type(fg).__name__})")
        if raises: raise RuntimeError("store boom")
        if copy_family is not None: copy_family()
    return f
def tn_pkg_store(**kw):
    return TNPkg(fgPackage=kw.pop("fg", TNFg()), store_font_info=kw.pop("store", _tn_store()), **kw)
tn_reset()
tn("2295a store without go              ", "stage=store", pkg=tn_pkg_store())
tn("2295b store                         ", "stage=store&go=yes", keys=("call", "call_error", "changed_readings", "calls_so_far"), pkg=tn_pkg_store())
_tnp = tn_pkg_store(tfn="Nm Api"); _tnp._d["store_font_info"] = _tn_store(copy_family=lambda: _tnp._d.__setitem__("tfn", "Unnamed"))
tn("2295c store copies legacy -> package ", "stage=store&go=yes", keys=("call", "changed_readings"), pkg=_tnp)
tn("2295d store_font_info missing       ", "stage=store&go=yes", pkg=TNPkg(fgPackage=TNFg()))
tn("2295e fgPackage is None             ", "stage=store&go=yes", pkg=tn_pkg_store(fg=None))
tn("2295f fgPackage is text             ", "stage=store&go=yes", pkg=tn_pkg_store(fg="x"))
tn("2295g fgPackage cannot be read      ", "stage=store&go=yes", pkg=TNPkg(store_font_info=_tn_store()))
tn("2295h store raises                  ", "stage=store&go=yes", keys=("call", "call_error", "calls_so_far"), pkg=tn_pkg_store(store=_tn_store(raises=True)))
tn_reset(); ns["_TRYNAMES"]["store"] = 3
tn("2295i store used up                 ", "stage=store&go=yes", keys=("error", "calls_so_far"), pkg=tn_pkg_store())
tn_reset()
tn("2295j legacy_set without go         ", "stage=legacy_set&field=familyName&value=Nm%20Api")
tn("2295k legacy_set, psn refused       ", "stage=legacy_set&field=postscriptFontName&value=NmApi-Regular&go=yes")
tn("2295l legacy_set, package field     ", "stage=legacy_set&field=tfn&value=Nm&go=yes")
tn("2295m legacy_set, a leading space   ", "stage=legacy_set&field=familyName&value=%20Nm&go=yes")
tn("2295n legacy_set                    ", "stage=legacy_set&field=familyName&value=Nm%20Api&go=yes", keys=("call", "call_error", "read_back_equal", "changed_readings", "calls_so_far"))
tn_setup(); TN["legacy_raises"] = True; _c, _d = call("/debug/trynames?stage=legacy_set&field=familyName&value=Nm&go=yes")
print("2295o legacy setter raises       :", _c, _d.get("call_error"), "| read back", _d.get("read_back_equal"), "| calls", TN["calls"])
tn_reset()
tn("2295p legacy_set, font.info raises  ", "stage=legacy_set&field=familyName&value=Nm&go=yes", keys=("error", "calls_so_far"), font=TNFont(info_raises=True))
tn_reset(); ns["_TRYNAMES"]["legacy_set"] = 3
tn("2295q legacy_set used up            ", "stage=legacy_set&field=familyName&value=Nm&go=yes", keys=("error", "calls_so_far"))
tn_reset()
tn("2295r unknown stage                 ", "stage=build&go=yes")
_tn_code = "\n".join(l.split("#")[0] for l in src[src.index("def debug_try_names("):src.index("# /debug/tryshapebox (v0.129)")].splitlines())
print("2295s static scan: setattr calls:", _re83.findall(r"setattr\([^)]*\)", _tn_code), "| store called once:", _tn_code.count("store(fg)") == 1, "| limits", ns["_TRYNAMES_MAX_OTHER"], ns["_TRYNAMES_LEGACY_SET_FIELDS"])
# v0.140: refresh which=model (notifyModelChanged()), properties (notifyPropertiesChanged(<flPackage>)), changed (flPackage.changed()); none of 856-866 redrew the FONTS panel
def _tn_changed(raises=False):
    def f():
        TN["calls"].append("changed()")
        if raises: raise RuntimeError("changed boom")
    return f
tn_reset()
tn("2296a which=model                   ", "stage=refresh&which=model&go=yes", keys=("which", "call", "call_error", "changed_readings", "calls_so_far"))
_d = tn("2296b which=properties              ", "stage=refresh&which=properties&go=yes", keys=("which", "call", "call_error", "calls_so_far"))
print("2296c properties passes the package :", [type(a[1]).__name__ for a in TN["notify"]])
tn("2296d which=changed                 ", "stage=refresh&which=changed&go=yes", keys=("which", "call", "call_error", "calls_so_far"), pkg=TNPkg(changed=_tn_changed()))
tn("2296e changed needs no flItems      ", "stage=refresh&which=changed&go=yes", keys=("call", "call_error"), items=False, pkg=TNPkg(changed=_tn_changed()))
tn("2296f changed missing               ", "stage=refresh&which=changed&go=yes")
tn("2296g changed raises                ", "stage=refresh&which=changed&go=yes", keys=("call", "call_error"), pkg=TNPkg(changed=_tn_changed(raises=True)))
tn("2296h model, no flItems             ", "stage=refresh&which=model&go=yes", items=False)
tn("2296i properties needs no fgId      ", "stage=refresh&which=properties&go=yes", keys=("call", "call_error"), pkg=TNPkg(fgId="7"))
tn("2296j model without go              ", "stage=refresh&which=model")
tn("2296k properties without go         ", "stage=refresh&which=properties")
tn("2296l changed without go            ", "stage=refresh&which=changed")
tn_reset(); ns["_TRYNAMES"]["model"] = 3
tn("2296m model used up                 ", "stage=refresh&which=model&go=yes", keys=("error", "calls_so_far"))
tn("2296n properties still allowed      ", "stage=refresh&which=properties&go=yes", keys=("call", "calls_so_far"))
tn_reset(); ns["_TRYNAMES"]["changed"] = 3
tn("2296o changed used up               ", "stage=refresh&which=changed&go=yes", keys=("error",), pkg=TNPkg(changed=_tn_changed()))
tn_reset()
print("2296p the refresh list           :", sorted(ns["_TRYNAMES_REFRESH"]))
# v0.141: refresh which=applied (notifyChangesApplied(title, <flPackage>, False)), readed, added (871: the panel rebuilds when a font is added)
tn_reset()
tn("2297a which=applied                 ", "stage=refresh&which=applied&go=yes", keys=("which", "call", "call_error", "changed_readings"))
tn("2297b which=readed                  ", "stage=refresh&which=readed&go=yes", keys=("which", "call", "call_error"))
tn("2297c which=added                   ", "stage=refresh&which=added&go=yes", keys=("which", "call", "call_error", "calls_so_far"))
tn("2297d applied needs no fgId         ", "stage=refresh&which=applied&go=yes", keys=("call", "call_error"), pkg=TNPkg(fgId="7"))
tn("2297e added, no flItems             ", "stage=refresh&which=added&go=yes", items=False)
tn("2297f applied without go            ", "stage=refresh&which=applied")
tn("2297g readed without go             ", "stage=refresh&which=readed")
tn("2297h added without go              ", "stage=refresh&which=added")
tn_reset(); ns["_TRYNAMES"]["added"] = 3
tn("2297i added used up                 ", "stage=refresh&which=added&go=yes", keys=("error",))
tn("2297j applied still allowed         ", "stage=refresh&which=applied&go=yes", keys=("call",))
tn_setup(); TN["notify_raises"] = True; _c, _d = call("/debug/trynames?stage=refresh&which=readed&go=yes")
print("2297k readed raises              :", _c, _d.get("call_error"), "| notify", TN["notify"])
print("2297l product mark text still once:", src.count("items.notifyChangesApplied(_MARK_TITLES[how], w, False)") == 1, "| refresh list", sorted(ns["_TRYNAMES_REFRESH"]))
# v0.143: stage=info_set (ONE flPackage.info.F = V for the Preferred family or subfamily); 879: the panel grouped a renamed font under "Unnamed"
tn_reset()
tn("2299a info_set without go           ", "stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm%20Three")
tn("2299b info_set, a package field     ", "stage=info_set&field=tfn&value=Nm&go=yes")
tn("2299c info_set, another info field  ", "stage=info_set&field=familyName&value=Nm&go=yes")
tn("2299d info_set, a trailing space    ", "stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm%20&go=yes")
_d = tn("2299e info_set Preferred family    ", "stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm%20Three&go=yes",
        keys=("call", "call_error", "read_back_equal", "changed_readings"))
print("2299f the info part after          :", _d["state_after"].get("info"), "| package tfn", _d["state_after"]["package"]["tfn"])
tn("2299g info_set Preferred subfamily  ", "stage=info_set&field=openTypeNamePreferredSubfamilyName&value=Bold&go=yes", keys=("call", "read_back_equal"))
tn_setup(); TN["info_raises"] = True; _c, _d = call("/debug/trynames?stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm&go=yes")
print("2299h the info setter raises     :", _c, _d.get("call_error"), "| read back", _d.get("read_back_equal"), "| calls", TN["calls"])
tn_reset()
tn("2299i no info object               ", "stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm&go=yes", keys=("error", "calls_so_far"), pkg=TNPkg(info=None))
tn("2299j state, no info object        ", "stage=state", keys=("state",), pkg=TNPkg(info="x"))
tn_reset(); ns["_TRYNAMES"]["info_set"] = 3
tn("2299k info_set used up             ", "stage=info_set&field=openTypeNamePreferredFamilyName&value=Nm&go=yes", keys=("error",))
tn_reset()
print("2299l the info fields             :", ns["_TRYNAMES_INFO"], "| stages", ns["_TRYNAMES_STAGES"])
tn_reset()
# v0.144: stage=title (ONE flPackage.title_name(True|False), 3 per run) and elidedName in stage=state; 902: a Full name typed in Font Info changed the tab's title, API writes never did
def _tn_title(ret="Unnamed Regular", raises=False):
    def f(full):
        TN["calls"].append(f"title_name({full})")
        if raises: raise RuntimeError("title boom")
        return ret
    return f
_tn_tk = ("call", "call_error", "returned", "full", "elided_name_before", "elided_name_after", "calls_so_far")
tn("2300a title without go              ", "stage=title", pkg=TNPkg(title_name=_tn_title()))
tn("2300b title, full not yes or no     ", "stage=title&full=maybe&go=yes", pkg=TNPkg(title_name=_tn_title()))
tn("2300c title                         ", "stage=title&go=yes", keys=_tn_tk, pkg=TNPkg(title_name=_tn_title()))
tn("2300d title, full=no                ", "stage=title&full=no&go=yes", keys=("call", "returned", "full"), pkg=TNPkg(title_name=_tn_title("Unnamed")))
tn("2300e title returns a number        ", "stage=title&go=yes", keys=("returned", "call_error"), pkg=TNPkg(title_name=_tn_title(5)))
tn_reset()
tn("2300f title returns control chars   ", "stage=title&go=yes", keys=("returned",), pkg=TNPkg(title_name=_tn_title("Nm\nTitle")))
tn("2300g title returns nothing         ", "stage=title&go=yes", keys=("returned", "call_error"), pkg=TNPkg(title_name=_tn_title(None)))
tn("2300h title raises                  ", "stage=title&go=yes", keys=("call_error", "returned", "calls_so_far"), pkg=TNPkg(title_name=_tn_title(raises=True)))
tn_reset()
tn("2300i title_name missing            ", "stage=title&go=yes")
tn("2300j title, two fonts: refused     ", "stage=title&go=yes", count=2, pkg=TNPkg(title_name=_tn_title()))
tn_reset(); ns["_TRYNAMES"]["title"] = 3
tn("2300k title used up                 ", "stage=title&go=yes", keys=("error", "calls_so_far"), pkg=TNPkg(title_name=_tn_title()))
tn_reset()
tn("2300l state reads elidedName        ", "stage=state", keys=("elided_name", "calls_so_far"))
_tnp = TNPkg(); _tnp._d.pop("elidedName")
tn("2300m state, elidedName unreadable  ", "stage=state", keys=("elided_name",), pkg=_tnp)
tn("2300n changed_readings unchanged    ", "stage=title&go=yes", keys=("changed_readings",), pkg=TNPkg(title_name=_tn_title()))
tn_reset()
tn("2300o a refused title counts nothing", "stage=title&full=x&go=yes", keys=("error",), pkg=TNPkg(title_name=_tn_title()))
print("2300p counters after a refusal     :", dict(ns["_TRYNAMES"]))
_tn_code = "\n".join(l.split("#")[0] for l in src[src.index("def debug_try_names("):src.index("# /debug/tryshapebox (v0.129)")].splitlines())
print("2300q static scan: title_name fetched once:", _tn_code.count('getattr(pkg, "title_name", None)') == 1, "| called once:", _tn_code.count("title_name(full") == 1,
      "| elidedName read by getattr only:", _tn_code.count('_trynames_read(pkg, "elidedName")') == 3, "| route passes full:", '(query.get("full") or ["yes"])[0]' in src,
      "| limit", ns["_TRYNAMES_MAX_OTHER"], "| stages", ns["_TRYNAMES_STAGES"])
tn_reset()
for _m, _a, _v in _tn_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.142: /debug/tryfont?stage=construct_named (P0.4: name a new font in the same request; faked flPackage / flWorkspace) =================
print("\n==== v0.142 /debug/tryfont construct_named ====")
_cn_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flPackage", "flWorkspace", "flItems")]   # v0.145: flItems
CN = {"made": [], "calls": [], "ctor_raises": False, "set_raises": (), "no_items": False, "mark_raises": False}
class CNPkg:
    def __repr__(s): return "<CNPkg>"
    def __init__(s):
        if CN["ctor_raises"]: raise RuntimeError("ctor boom")
        object.__setattr__(s, "_d", {"psn": "Unnamed-Regular", "ffn": "Unnamed Regular", "tfn": "Unnamed", "tsn": "Regular", "sgn": "Unnamed",
                                     "name": "", "upm": 1000.0, "mastersCount": 1, "defaultMaster": "Regular", "glyphsCount": 1,
                                     "isNull": False, "path": "", "fileName": "Unnamed Regular.xfo", "fgPackage": None})
        CN["made"].append(s)
    def __getattr__(s, a):
        d = object.__getattribute__(s, "_d")
        if a in d: return d[a]
        CN["calls"].append("read " + a); raise AttributeError(a)
    def __setattr__(s, a, v):
        CN["calls"].append(f"set {a}={v!r}")
        if a in CN["set_raises"]: raise RuntimeError(a + " read-only")
        object.__getattribute__(s, "_d")[a] = v
class CNWs:
    def packages(s): return list(CN["made"])
    @property
    def currentPackage(s): return CN["made"][-1] if CN["made"] else None
    def hasPackage(s, p): return p in CN["made"]
class CNItems:
    """v0.145: the mark call is recorded with the type of what it was given, and can raise."""
    @staticmethod
    def notifyChangesApplied(title, pkg, flag):
        CN["calls"].append(f"applied({title!r}, {type(pkg).__name__}, {flag})")
        if CN["mark_raises"]: raise RuntimeError("mark boom")
def cn_setup(**kw):
    CN.update(made=[], calls=[], ctor_raises=False, set_raises=(), no_items=False, mark_raises=False)
    CN.update(kw)
    ns["_TRYFONT"].update(package=None, constructed=False, attached=False)
    for _m in _tf_mods:
        _m.flPackage = CNPkg
        _m.CountFonts = lambda: len(CN["made"])
        _m.CurrentFont = lambda: None
        _m.flWorkspace = type("CNW", (), {"instance": staticmethod(lambda: CNWs())})
        if CN["no_items"]:
            if hasattr(_m, "flItems"): delattr(_m, "flItems")
        else:
            _m.flItems = CNItems
def cn(tag, query, keys=("error",)):
    c, d = call("/debug/tryfont?" + query)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| made", len(CN["made"]), "| calls", CN["calls"])
    return d
cn_setup()
cn("2298a without go                      ", "stage=construct_named&family=Nm%20Three")
cn("2298b no family                       ", "stage=construct_named&go=yes")
cn("2298c 56 without spaces (psn 64)     ", "stage=construct_named&family=" + "a" * 56 + "&go=yes")
cn("2298d 55 characters, no go            ", "stage=construct_named&family=" + "a" * 55)
cn("2298r a forbidden character          ", "stage=construct_named&family=Nm%2FTwo&go=yes")
cn("2298s 58 characters (psn 66, was let through)", "stage=construct_named&family=" + "a" * 58 + "&go=yes")
cn("2298e a leading space                 ", "stage=construct_named&family=%20Nm&go=yes")
cn("2298f not ASCII                       ", "stage=construct_named&family=Nm%C3%A9&go=yes")
_d = cn("2298g named                           ", "stage=construct_named&family=Nm%20Three&go=yes", keys=("constructed", "family", "names_before", "all_equal"))
print("2298h assignments                     :", [(e["field"], e["value"], e.get("call_error"), e["read_back_equal"]) for e in _d["assignments"]])
print("2298i workspace after                 :", _d["workspace_after"].get("CountFonts"), _d["workspace_after"].get("packages_len"), "| reads fileName", _d["reads"].get("fileName"))
cn("2298j a second construct_named        ", "stage=construct_named&family=Nm%20Four&go=yes")
cn("2298k construct after it              ", "stage=construct&go=yes")
cn_setup(ctor_raises=True)
cn("2298l the constructor raises          ", "stage=construct_named&family=Nm&go=yes")
print("2298m no second try after a failure  :", ns["_TRYFONT"]["constructed"])
cn_setup(set_raises=("psn",))
_d = cn("2298n the psn setter raises          ", "stage=construct_named&family=Nm%20Three&go=yes", keys=("all_equal",))
print("2298o per field                        :", [(e["field"], e.get("call_error"), e["read_back"]) for e in _d["assignments"]])
cn_setup()
cn("2298p an unknown stage               ", "stage=named&go=yes")
print("2298q the built names                 :", ns["_tryfont_built_names"]("Nm Three"), "| route passes family:", '(query.get("family") or [""])[0]' in src)
# v0.145: construct_named&mark=yes (ONE flItems.notifyChangesApplied on the package just made); 912, 913 ran with one font open only
cn_setup()
cn("2301a mark, without go                 ", "stage=construct_named&family=Nm%20Five&mark=yes")
cn("2301b mark=maybe                       ", "stage=construct_named&family=Nm%20Five&mark=maybe&go=yes")
cn("2301c mark off by default              ", "stage=construct_named&family=Nm%20Five&go=yes", keys=("constructed", "all_equal", "mark"))
cn_setup()
_d = cn("2301d mark=yes                        ", "stage=construct_named&family=Nm%20Five&mark=yes&go=yes", keys=("constructed", "all_equal", "mark"))
print("2301e the mark call                    :", _d["mark"].get("call"), "| the package it got is the one made:", CN["calls"][-1].split(", ")[1] == "CNPkg", "| made", len(CN["made"]))
cn("2301f a second construct_named refused  ", "stage=construct_named&family=Nm%20Six&mark=yes&go=yes")
cn_setup(set_raises=("psn",))
cn("2301g a name fails: no mark             ", "stage=construct_named&family=Nm%20Five&mark=yes&go=yes", keys=("all_equal", "mark"))
cn_setup(no_items=True)
cn("2301h no flItems: no mark               ", "stage=construct_named&family=Nm%20Five&mark=yes&go=yes", keys=("all_equal", "mark"))
cn_setup(mark_raises=True)
cn("2301i the mark raises                   ", "stage=construct_named&family=Nm%20Five&mark=yes&go=yes", keys=("constructed", "all_equal", "mark"))
print("2301j no second try after a mark error:", ns["_TRYFONT"]["constructed"])
cn_setup(ctor_raises=True)
cn("2301k the constructor raises, mark=yes  ", "stage=construct_named&family=Nm&mark=yes&go=yes")
cn_setup()
cn("2301l mark ignored for construct        ", "stage=construct&mark=yes&go=yes", keys=("constructed",))
_mk_code = "\n".join(l.split("#")[0] for l in src[src.index("def _tryfont_mark("):src.index("def debug_try_font(")].splitlines())
_df_code = "\n".join(l.split("#")[0] for l in src[src.index("def debug_try_font("):src.index("def debug_try_font(") + 7000].splitlines())   # the function is about 6000 characters
print("2301m static scan: mark call once:", _mk_code.count("marker.notifyChangesApplied(") == 1, "| helper called once, only when mark is yes:",
      _df_code.count("_tryfont_mark(mod, pkg, all_equal)") == 1 and 'if mark == "yes" else None' in _df_code,
      "| route passes mark:", '(query.get("mark") or [""])[0]' in src, "| title text shared:", "_TRYNOTIFY_TITLE" in _mk_code)
ns["_TRYFONT"].update(package=None, constructed=False, attached=False)
for _m, _a, _v in _cn_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)


# ================= v0.146: POST /font/create (P0.3 / P0.4; faked flPackage / flWorkspace / flItems / CurrentFont) =================
print("\n==== v0.146 POST /font/create ====")
_fc_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flPackage", "flWorkspace", "flItems")]
_fc_mark_saved = ns["_MARK_CHANGED"]
FC = {"open": [], "calls": [], "mode": {}, "counts": []}
class FCInfo:
    """The legacy font.info of one font: familyName can be written, raise, or ignore the write."""
    def __init__(s, fam): s._fam = fam; s.styleName = "Regular"
    @property
    def familyName(s): return s._fam
    @familyName.setter
    def familyName(s, v):
        FC["calls"].append(f"legacy familyName={v!r}")
        if FC["mode"].get("legacy_raises"): raise RuntimeError("legacy boom")
        if FC["mode"].get("legacy_ignored"): return
        s._fam = v
class FCOther:
    """A font that was already open (saved)."""
    def __init__(s, fam="Saved"):
        s._legacy = FCInfo(fam); s.isNull = False; s.path = "C:/fonts/" + fam + ".vfc"; s.fgId = 100 + len(FC["open"])     # v0.150: fgId identifies a package
class FCPkg:
    def __repr__(s): return "<FCPkg>"
    def __init__(s):
        FC["calls"].append("flPackage()")
        m = FC["mode"]
        if m.get("ctor_raises"): raise RuntimeError("ctor boom")
        n = sum(1 for p in FC["open"] if isinstance(p, FCPkg))       # FontLab numbers new fonts: Unnamed, Unnamed1, ...
        fam = "Unnamed" + (str(n) if n else "")
        object.__setattr__(s, "_d", {"psn": fam + "-Regular", "ffn": fam + " Regular", "tfn": fam, "tsn": "Regular", "sgn": fam,
                                     "upm": 1000.0, "mastersCount": 1, "defaultMaster": "Regular", "glyphsCount": 1, "isNull": False,
                                     "path": "", "fileName": fam + " Regular.xfo", "fgId": m.get("fgid", 7)})
        object.__setattr__(s, "_legacy", FCInfo(m.get("legacy_start", fam)))
        if m.get("not_registered"): return
        if m.get("not_in_front"): FC["open"].insert(0, s)
        else: FC["open"].append(s)
    def __getattr__(s, a):
        d = object.__getattribute__(s, "_d")
        if a in d and isinstance(d[a], Exception): raise d[a]
        if a in d: return d[a]
        raise AttributeError(a)
    def __setattr__(s, a, v):
        FC["calls"].append(f"set {a}={v!r}")
        if a in FC["mode"].get("set_raises", ()): raise RuntimeError(a + " read-only")
        if a in FC["mode"].get("set_ignored", ()): return
        object.__getattribute__(s, "_d")[a] = v
    def isEqual(s, other):
        FC["calls"].append("isEqual")
        if FC["mode"].get("isequal_raises"): raise RuntimeError("isEqual boom")
        if "isequal_returns" in FC["mode"]: return FC["mode"]["isequal_returns"]
        return s is other
for _n in ("release", "remove", "close", "save", "update", "changed", "addGlyph", "setUpm", "addMaster"):
    setattr(FCPkg, _n, _tf_spy("flPackage." + _n))
class FCWs:
    def packages(s): return list(FC["open"])
    @property
    def currentPackage(s):
        if FC["mode"].get("no_current"): return None
        return FC["open"][-1] if FC["open"] else None
for _n in ("addPackage", "closePackage", "saveProject", "exportFont", "release", "remove", "update"):
    setattr(FCWs, _n, _tf_spy("flWorkspace." + _n))
class FCFont:
    def __init__(s, pkg): s.info = pkg._legacy; s.path = pkg.path; s.glyphs = []
class FCItems:
    @staticmethod
    def notifyChangesApplied(title, pkg, flag):
        FC["calls"].append(f"applied({title!r}, {type(pkg).__name__}, {flag})")
        if FC["mode"].get("mark_raises"): raise RuntimeError("mark boom")
def _fc_count():
    if FC["counts"]:
        v = FC["counts"].pop(0)
        if isinstance(v, Exception): raise v
        return v
    return len(FC["open"])
def fc_setup(others=0, counts=(), **mode):
    FC.update(open=[FCOther("Saved" + str(i)) for i in range(others)], calls=[], mode=dict(mode), counts=list(counts))
    TF["forbidden"].clear()
    ns["_MARK_CHANGED"] = True
    for _m in _tf_mods:
        _m.flPackage = FCPkg
        _m.CountFonts = _fc_count
        _m.CurrentFont = lambda: FCFont(FC["open"][-1]) if FC["open"] else None
        _m.flWorkspace = type("FCW", (), {"instance": staticmethod(lambda: FCWs())})
        if mode.get("no_items"):
            if hasattr(_m, "flItems"): delattr(_m, "flItems")
        else:
            _m.flItems = FCItems
def fc_post(body):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode()
    r = ns["_route"]("POST", "/font/create", raw); h, _, b = r.partition(b"\r\n\r\n")
    hdr = [l for l in h.decode().split("\r\n") if l.startswith("X-Glyphbridge-Font")]
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b), hdr
FC_KEYS = ("created", "reason", "fonts_open_before", "fonts_open_after", "in_front", "names_set", "legacy_family_set", "fontlab_changed_mark", "error")
def fc(tag, body, keys=FC_KEYS):
    c, d, hdr = fc_post(body)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| open", len(FC["open"]), "| calls", FC["calls"], "| forbidden", TF["forbidden"])
    return d, hdr

print("--- made, verified")
fc_setup()
d, hdr = fc("2302a unnamed, no font open        ", {})
print("2302b names before / after           :", d.get("names_before"), "|", d.get("names_after") == d.get("names_before"))
print("2302c package                         :", d.get("package"), "| family_requested", d.get("family_requested"), "| header", hdr)
print("2302d notes                           :", d.get("notes"))
d, hdr = fc("2302e a second one, same listener run", {"family": None})
print("2302f it is Unnamed1                  :", (d.get("names_after") or {}).get("ffn"), "| header", hdr)
fc("2302g a third one                     ", b"")
fc_setup(others=2)
d, hdr = fc("2302h named, two other fonts open   ", {"family": "Nm Test"})
print("2302i assignments                     :", [(e["field"], e["value"], e.get("call_error"), e["read_back_equal"]) for e in d["assignments"]])
print("2302j legacy family                   :", d.get("legacy_family"))
print("2302k the mark went to the new package:", FC["calls"][-1], "| header", hdr)
print("2302l notes                           :")
for _n in d.get("notes") or []: print("        ", _n)
fc_setup()
d, _ = fc("2302m named, nothing else open       ", {"family": "A"})
print("2302n notes (no other fonts)          :", len(d.get("notes") or []), [n[:40] for n in d.get("notes") or []])
fc_setup()
fc("2302o 55 characters without spaces   ", {"family": "a" * 55}, keys=("created", "names_set"))
fc_setup()
fc("2302p 62 with spaces, psn 63         ", {"family": "aaaaaaa " * 7 + "aaaaaa"}, keys=("created", "names_set", "error"))

print("--- refused before anything is called")
fc_setup()
for _tag, _body in (("2303a bad JSON                       ", b"{bad"), ("2303b a list                         ", [1]),
                    ("2303c another key                    ", {"family": "Nm", "style": "Bold"}), ("2303d family a number              ", {"family": 5}),
                    ("2303e family empty                   ", {"family": ""}), ("2303f a leading space               ", {"family": " Nm"}),
                    ("2303g not ASCII                      ", {"family": "Nm\u00e9"}), ("2303h 56 without spaces             ", {"family": "a" * 56}),
                    ("2303i 64 characters                  ", {"family": "a " * 31 + "aa"}), ("2303j a slash                      ", {"family": "Nm/Two"}),
                    ("2303k a percent sign                 ", {"family": "Nm%"}), ("2303l a tab                          ", {"family": "Nm\tTwo"})):
    fc(_tag, _body, keys=("error",))

print("--- not made, or not confirmed")
fc_setup(ctor_raises=True); fc("2304a the constructor raises          ", {"family": "Nm"})
fc_setup(); [setattr(_m, "flPackage", None) or delattr(_m, "flPackage") for _m in _tf_mods]
fc("2304b no flPackage class              ", {})
fc_setup(counts=[RuntimeError("count boom")]); fc("2304c CountFonts raises before      ", {})
fc_setup(counts=[True]); fc("2304d CountFonts returns True       ", {})
fc_setup(not_registered=True); fc("2304e the count did not go up        ", {"family": "Nm"})
fc_setup(counts=[0, RuntimeError("count boom")]); fc("2304f CountFonts raises after       ", {"family": "Nm"})
fc_setup(counts=[1, 3]); fc("2304g the count went up by two       ", {"family": "Nm"})
fc_setup(others=1, not_in_front=True); fc("2304h made, but not in front        ", {"family": "Nm"})
fc_setup(fgid=RuntimeError("fgId boom")); fc("2304i v0.150 fgId cannot be read      ", {"family": "Nm"})
fc_setup(fgid=True); fc("2304j v0.150 fgId is a bool          ", {"family": "Nm"})
fc_setup(no_current=True); fc("2304k no current package            ", {"family": "Nm"})

print("--- names that do not all hold")
fc_setup(set_raises=("psn",)); d, _ = fc("2305a the psn setter raises          ", {"family": "Nm"})
print("2305b per field                       :", [(e["field"], e.get("call_error"), e["read_back"]) for e in d["assignments"]], "| notes", len(d["notes"]), d["notes"][-1][:60])
fc_setup(set_ignored=("ffn",)); fc("2305c the ffn write is ignored       ", {"family": "Nm"})
fc_setup(legacy_raises=True); d, _ = fc("2305d the legacy write raises       ", {"family": "Nm"})
print("2305e legacy family                   :", d.get("legacy_family"))
fc_setup(legacy_ignored=True); d, _ = fc("2305f the legacy write is ignored   ", {"family": "Nm"})
print("2305g legacy family                   :", d.get("legacy_family"))
fc_setup(legacy_start="Other"); d, _ = fc("2305h the font in front reads another family", {"family": "Nm"})
print("2305i legacy family                   :", d.get("legacy_family"))

print("--- the changed mark")
fc_setup(no_items=True); fc("2306a no flItems                     ", {"family": "Nm"})
fc_setup(mark_raises=True); fc("2306b the mark raises                ", {"family": "Nm"})
fc_setup(); ns["_MARK_CHANGED"] = False; fc("2306c switched off                  ", {"family": "Nm"})
fc_setup(); fc("2306d unnamed: never marked           ", {})

print("--- the activity log lines of /font/create")
_fc_al_saved = {k: ns[k] for k in ("_now_hms", "_clock", "_ACTIVITY_LOG")}
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0; ns["_ACTIVITY_LOG"] = "normal"
def fc_al(tag, body, code, reply):
    print(tag)
    ns["_ACT"].update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, last=0.0, pending=False, client=None)
    raw = json.dumps(body).encode() if isinstance(body, (dict, list)) else (body or b"")
    ns["_activity_note"]("POST", "/font/create", raw, ns["_build_response"](code, reply), "claude-code")
    ns["_act_flush"]()
fc_setup(); _d0 = fc_post({})[1]
fc_al("2307a unnamed, verified:", {}, 200, _d0)
fc_setup(others=2); _d1 = fc_post({"family": "Nm Test"})[1]
fc_al("2307b named, two other fonts open:", {"family": "Nm Test"}, 200, _d1)
fc_setup(set_raises=("psn",)); _d2 = fc_post({"family": "Nm"})[1]
fc_al("2307c a name failed:", {"family": "Nm"}, 200, _d2)
fc_setup(others=1, not_in_front=True); _d3 = fc_post({"family": "Nm"})[1]
fc_al("2307d made, not in front (no notes):", {"family": "Nm"}, 200, _d3)
fc_al("2307e refused:", {"family": "Nm/Two"}, 400, {"error": "family: it becomes part of the PostScript name; no font was made"})
fc_al("2307f failed:", {}, 500, {"error": "RuntimeError: x"})
fc_al("2307g a note that is too long is cut:", {}, 200, dict(_d0, notes=["x" * 500, 7, " "]))
for _k, _v in _fc_al_saved.items(): ns[_k] = _v

print("--- static checks")
_fc_code = "\n".join(l.split("#")[0] for l in src[src.index("# POST /font/create (v0.146"):src.index("# HTTP plumbing")].splitlines())
_fc_code_nostr = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _fc_code)
print("2308a forbidden call syntax           :", _re83.findall(r"(?<!out)\.(?:addPackage|createNewProject|closePackage|closeProject|saveProject|readProject|export\w*|save\w*|release|remove\w*|close\w*|update\w*|changed|generate\w*|delete\w*)\s*\(", _fc_code_nostr),
      "| scanned chars > 6000:", len(_fc_code) > 6000)
print("2308b one construction, one mark      :", _fc_code.count("cls()") == 1, _fc_code.count("items.notifyChangesApplied(") == 1, "| no per-run counter:", "_TRYFONT" not in _fc_code)
print("2308c route registered once, documented:", src.count('if path == "/font/create":') == 1, "POST /font/create" in src[:src.index('"""', 3)],
      "| in the activity writes:", ns["_ACT_WRITES"].get("/font/create"), "| version", ns["VERSION"])
_fc_probe = "\n".join(l.split("#")[0] for l in src[src.index("def debug_try_font("):src.index("def debug_try_font(") + 7000].splitlines())
print("2308d one shared family check        :", "_TRYFONT_FAMILY_MAX" not in ns, "| probe uses it:", "why = _family_name_error(family)" in _fc_probe,
      "| route uses it:", "why = _family_name_error(family)" in _fc_code, "| psn limit", ns["_CREATE_FONT_PSN_MAX"], "| forbidden", ns["_CREATE_FONT_PSN_FORBIDDEN"])

ns["_MARK_CHANGED"] = _fc_mark_saved
for _m, _a, _v in _fc_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.148: /debug/trypackage (P0.9 research, read only: does a glyph's wrapper name its own package?) =================
print("\n==== v0.148 /debug/trypackage ====")
# Spy fakes: any member the probe should not touch lands in TP["forbidden"]; TP["calls"] holds every isEqual.
TP = {"calls": [], "forbidden": [], "mode": {}, "count": 1, "npk": 1, "cur": None, "wrap": None, "font": None}
class TPSpy:
    def __getattr__(s, a):
        TP["forbidden"].append(a); raise AttributeError(a)
class TPPkg(TPSpy):
    def __init__(s, **kw):
        s.__dict__.update(isNull=False, fgId=1, path="", mastersCount=1, defaultMaster="Regular", master="Regular", masters=["Regular"],
                          glyphsCount=1, upm=1000); s.__dict__.update(kw)
    def isEqual(s, other):
        TP["calls"].append(("isEqual", type(other).__name__))
        m = TP["mode"]
        if m.get("equal_raises"): raise RuntimeError("equal boom")
        if m.get("equal_adds_font"): TP["count"] += 1
        if m.get("equal_native"): return object()
        return other is s
class TPWs(TPSpy):
    def packages(s): return [object()] * TP["npk"]
    currentPackage = property(lambda s: TP["cur"])
class TPGlyph(TPSpy): pass
class TPInfo(TPSpy): unitsPerEm = 1000; familyName = "Unnamed1"; styleName = "Regular"     # the family and style go to the font headers
class TPFont(TPSpy):
    def __init__(s, glyphs=1, path=""): s.__dict__.update(glyphs=["g"] * glyphs, path=path, info=TPInfo())
def _tp_count():
    v = TP["count"]
    if isinstance(v, Exception): raise v
    return v
TPWsCls = type("flWorkspace", (), {"instance": staticmethod(lambda: TPWs())})
_tp_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "flWorkspace", "CurrentFont")]
_tp_ns = {k: ns[k] for k in ("_find_glyph", "_modern_wrapper")}
def tp_setup(mode=None, count=1, npk=1, glyph_pkg="same", cur_kw=None, glyph_pkg_kw=None, font_kw=None):
    """glyph_pkg: "same" (the current package), "other" (another package), "none", "raises", "method" (a zero-argument callable)."""
    cur = TPPkg(**(cur_kw or {}))
    other = TPPkg(**dict({"glyphsCount": 5, "path": "C:/fonts/Other.vfc"}, **(glyph_pkg_kw or {})))
    w = TPGlyph()
    if glyph_pkg == "same":
        if glyph_pkg_kw: cur.__dict__.update(glyph_pkg_kw)
        w.__dict__["package"] = cur
    elif glyph_pkg == "other": w.__dict__["package"] = other
    elif glyph_pkg == "none": w.__dict__["package"] = None
    elif glyph_pkg == "method": w.__dict__["package"] = lambda: cur
    elif glyph_pkg == "raises": w.__dict__["package"] = lambda: (_ for _ in ()).throw(RuntimeError("package boom"))
    TP.update(calls=[], forbidden=[], mode=mode or {}, count=count, npk=npk, cur=cur, wrap=w, font=TPFont(**(font_kw or {})))
    def mw(g, f):
        if TP["mode"].get("wrap_raises"): raise RuntimeError("wrap boom")
        return TP["wrap"], "built"
    ns["_find_glyph"] = lambda f, n: "G" if n in ("tpg", ".notdef") else None
    ns["_modern_wrapper"] = mw
    for _m in _tf_mods:
        _m.CountFonts = _tp_count; _m.flWorkspace = TPWsCls; _m.CurrentFont = lambda: TP["font"]
    ns["_TRYPACKAGE"]["runs"] = 0
TK = ("error", "open", "wrapper", "glyph_package", "current_package", "same_as_current", "same_reason", "glyph_package_matches_front",
      "font_in_front", "fonts_before", "fonts_after", "side_effect_detected", "runs_so_far")
def tp(tag, path, keys=TK):
    c, d = call(path)
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| isEqual", TP["calls"], "| forbidden", TP["forbidden"])
    return d
P = "/debug/trypackage?name=tpg&go=yes"
tp_setup()
tp("2309a without go                  ", "/debug/trypackage?name=tpg")
tp("2309b go must be exactly yes      ", "/debug/trypackage?name=tpg&go=Yes")
tp("2309c no name                     ", "/debug/trypackage?go=yes")
tp("2309d a name with a space         ", "/debug/trypackage?name=t%20pg&go=yes")
tp("2309e a name of 41 characters     ", "/debug/trypackage?go=yes&name=" + "a" * 41)
tp_setup(count=0); tp("2309f no font open                ", P)
tp_setup(); tp("2309g a glyph that does not exist  ", "/debug/trypackage?name=nope&go=yes")
tp_setup(mode={"wrap_raises": 1}); tp("2309h the wrapper raises           ", P)
tp_setup(); d = tp("2309i one font, its own package    ", P); print("2309j  note                     :", d["note"])
tp_setup(); tp("2309k .notdef is a valid name      ", "/debug/trypackage?name=.notdef&go=yes", keys=("same_as_current", "runs_so_far"))
tp_setup(count=2, npk=2); tp("2309l two fonts, its own package   ", P)
tp_setup(count=2, npk=2, glyph_pkg="other"); tp("2309m two fonts, another package   ", P)
tp_setup(count=2, npk=2, cur_kw={"path": "C:/fonts/A.vfc"}, font_kw={"path": "C:/fonts/A.vfc"}); tp("2309n a saved font, paths agree    ", P, keys=("same_as_current", "glyph_package_matches_front"))
tp_setup(glyph_pkg="method"); tp("2309o package is a method, called once", P, keys=("same_as_current", "glyph_package"))
tp_setup(glyph_pkg="raises"); tp("2309p package cannot be read       ", P)
tp_setup(glyph_pkg="none"); tp("2309q package is None             ", P)
tp_setup(glyph_pkg_kw={"isNull": True}); tp("2309r the glyph's package is null  ", P)
tp_setup(glyph_pkg_kw={"isNull": lambda: (_ for _ in ()).throw(RuntimeError("null boom"))}); tp("2309s isNull cannot be read        ", P)
tp_setup(glyph_pkg_kw={"isNull": 0}); tp("2309t isNull is not a bool        ", P, keys=("glyph_package", "same_as_current", "same_reason"))
tp_setup(glyph_pkg="other", glyph_pkg_kw={}, cur_kw={"isNull": True}); tp("2309u the current package is null  ", P, keys=("current_package", "same_as_current", "same_reason"))
tp_setup(mode={"equal_raises": 1}); tp("2309v isEqual raises              ", P, keys=("same_as_current",))
tp_setup(mode={"equal_native": 1}); tp("2309w isEqual returns an object    ", P, keys=("same_as_current",))
tp_setup(glyph_pkg_kw={"masters": [object()]}); tp("2309x masters are not text        ", P, keys=("glyph_package",))
tp_setup(glyph_pkg_kw={"mastersCount": lambda: (_ for _ in ()).throw(RuntimeError("count boom")), "upm": "x"}); tp("2309y a read fails, upm not a number", P, keys=("glyph_package", "glyph_package_matches_front"))
tp_setup(mode={"equal_adds_font": 1}); tp("2309z a font appears during the probe", P, keys=("fonts_before", "fonts_after", "side_effect_detected"))
tp_setup(count=RuntimeError("count boom")); tp("2309aa CountFonts raises           ", P)
tp_setup()
for _i in range(20): call(P)
tp("2309ab request 21 refused          ", P, keys=("error", "runs_so_far")); print("2309ac  isEqual calls in 21 requests:", len(TP["calls"]))
_tp_code = "\n".join(l.split("#")[0] for l in src[src.index("# /debug/trypackage (v0.148)"):src.index("# POST /font/create (v0.146")].splitlines())
_tp_code_nostr = _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _tp_code)
print("2309ad static scan of the probe   : forbidden call syntax:",
      _re83.findall(r"\.(?:update\w*|save\w*|export\w*|close\w*|release|remove\w*|changed|notify\w*|set\w*|add\w*|find\w*|activate\w*|title_name|store\w*)\s*\(", _tp_code_nostr),
      "| fgPackage:", "fgPackage" in _tp_code_nostr, "| subscripts of a native object:", _re83.findall(r"\b(?:gp|cp|w|mod|font)\[", _tp_code_nostr),
      "| one isEqual per stage:", _tp_code_nostr.count(".isEqual(") == 2, "| counter before the first read:", all(_tpf.index('_TRYPACKAGE["runs"] += 1') < _tpf.index("_trypackage_current(mod)") and _tpf.rindex('_TRYPACKAGE["runs"] += 1') < _tpf.index('_pkg_get(w, "package")')
                                               for _tpf in [_tp_code[_tp_code.index("def debug_try_package("):]]),
      "| scanned chars > 4000:", len(_tp_code) > 4000)
print("2309ae route documented, registered once:", "/debug/trypackage     name=X&go=yes" in src[:src.index('"""', 3)], src.count('path == "/debug/trypackage"') == 1, "| version", ns["VERSION"])
# v0.149: stage=cached reads the wrappers ALREADY in the listener's cache (none is built), each checked against its key and isValid first
print("--- v0.149 stage=cached")
_tp_cache_saved = (dict(ns["_MODERN_CACHE"]), list(ns["_MODERN_CACHE_FONT"]))
class TPWrap(TPSpy):
    def __init__(s, name, gid, pkg, valid=True): s.__dict__.update(name=name, fgGlyphId=gid, package=pkg, isValid=valid)
def tp_cache(*wraps, key=""):
    ns["_MODERN_CACHE"].clear()
    for lid, w in wraps: ns["_MODERN_CACHE"][lid] = w
    ns["_MODERN_CACHE_FONT"][0] = key
CK = ("error", "open", "stage", "cache_key_is_empty_path", "cached_wrappers", "cut", "current_package", "wrappers", "side_effect_detected", "runs_so_far")
PC = "/debug/trypackage?stage=cached&go=yes"
tp_setup(); tp("2310a cached without go           ", "/debug/trypackage?stage=cached", keys=CK)
tp_setup(); tp("2310b cached with a name          ", "/debug/trypackage?stage=cached&name=tpg&go=yes", keys=CK)
tp_setup(); tp("2310c an unknown stage            ", "/debug/trypackage?stage=all&go=yes", keys=CK)
tp_setup(count=0); tp_cache(); tp("2310d no font open                ", PC, keys=CK)
tp_setup(); tp_cache(); tp("2310e an empty cache              ", PC, keys=CK)
tp_setup(count=2, npk=2); _tp_other = TPPkg(fgId=8, glyphsCount=1)
tp_cache((11, TPWrap(".notdef", 11, TP["cur"])), (14, TPWrap(".notdef", 14, _tp_other)))
tp("2310f two fonts: own and other package", PC, keys=CK)
tp_setup(count=2, npk=2); tp_cache((11, TPWrap(".notdef", 11, TP["cur"])), (14, TPWrap(".notdef", 14, TP["cur"])))
tp("2310g both report the current one ", PC, keys=("wrappers",))
tp_setup(); tp_cache((11, TPWrap("a", 12, TP["cur"])), (13, TPWrap("b", 13, TP["cur"], valid=False)),
                     (15, TPWrap("c", lambda: (_ for _ in ()).throw(RuntimeError("id boom")), TP["cur"])),
                     (16, TPWrap("d", 16, TP["cur"], valid=lambda: (_ for _ in ()).throw(RuntimeError("valid boom")))))
tp("2310h key, isValid and id checks skip", PC, keys=("wrappers",))
tp_setup(); _tp_bad = TPWrap("e", 17, None); _tp_bad.__dict__["package"] = lambda: (_ for _ in ()).throw(RuntimeError("package boom"))
tp_cache((17, _tp_bad), (18, TPWrap("f", 18, None)), (19, TPWrap("g", 19, TPPkg(isNull=True))))
tp("2310i package unreadable, None, null", PC, keys=("wrappers",))
tp_setup(cur_kw={"isNull": True}); tp_cache((11, TPWrap(".notdef", 11, TPPkg())))
tp("2310j the current package is null ", PC, keys=("current_package", "wrappers"))
tp_setup(mode={"equal_raises": 1}); tp_cache((11, TPWrap(".notdef", 11, TP["cur"])))
tp("2310k isEqual raises              ", PC, keys=("wrappers",))
tp_setup(); tp_cache(*[(i, TPWrap("n%d" % i, i, TP["cur"])) for i in range(25, 0, -1)], key="C:/fonts/A.vfc")
_d = tp("2310l 25 cached: 20 read, in key order", PC, keys=("cache_key_is_empty_path", "cached_wrappers", "cut"))
print("2310m  keys read:", [e["key"] for e in _d["wrappers"]], "| isEqual calls:", len(TP["calls"]))
tp_setup(); tp_cache((11, TPWrap(".notdef", 11, TP["cur"])))
for _i in range(20): call(P)
tp("2310n cached shares the run counter: request 21 refused", PC, keys=("error", "runs_so_far"))
print("2310o no wrapper built by stage=cached:", "_modern_wrapper" not in src[src.index('    if stage == "cached":\n        entries'):src.index("    glyph = _find_glyph(font, name)", src.index('    if stage == "cached":\n        entries'))])
ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE"].update(_tp_cache_saved[0]); ns["_MODERN_CACHE_FONT"][:] = _tp_cache_saved[1]
for _k, _v in _tp_ns.items(): ns[_k] = _v
for _m, _a, _v in _tp_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.151: /debug/tryedit (gated research probe for P2.2: ONE edit of a plain drawn glyph per call) =================
print("\n==== v0.151 /debug/tryedit ====")
# The /glyph/path fakes of v0.81 (P72Mod, P81Node rows) plus the one-font gate of /debug/tryopen. TE fakes are spies: a member they do
# not define, a subscript or an iteration lands in TE["forbidden"]. TELayer holds real shapes; its counts are computed, not stored.
TE = {"forbidden": [], "calls": [], "mode": {}, "updates": [], "marks": [], "broken": False}
def _te_forbid(label):
    TE["forbidden"].append(label); raise RuntimeError("FORBIDDEN: " + label)
class TESpy:
    def __getattr__(s, a):
        if a.startswith("__"): raise AttributeError(a)
        _te_forbid(type(s).__name__ + "." + a)
    def __getitem__(s, i): _te_forbid(type(s).__name__ + "[]")
    def __iter__(s): _te_forbid(type(s).__name__ + " iterated")
class TENode(P81Node, TESpy):
    @property
    def x(s): return s._r["x"]
    @x.setter
    def x(s, v):
        TE["calls"].append(("x", v))
        if TE["mode"].get("set_raises"): raise RuntimeError("x boom")
        if TE["mode"].get("move_ignored"): return
        s._r["x"] = float(v)
        if TE["mode"].get("move_smooth"): s._r["smooth"] = True
    @property
    def y(s): return s._r["y"]
    @y.setter
    def y(s, v): TE["calls"].append(("y", v)); s._r["y"] = float(v)
class TEContour(P81Contour, TESpy):
    def getNodeAt(s, i):
        if TE["mode"].get("node_raises"): raise RuntimeError("getNodeAt boom")
        return TENode(s, s.rows[i])
class TEShapeData(TESpy):
    def __init__(s, shape): s._shape = shape
    def addContour(s, c):
        TE["calls"].append("addContour")
        if TE["mode"].get("add_raises"): raise RuntimeError("addContour boom")
        if TE["mode"].get("break_on_edit"): TE["broken"] = True
        if TE["mode"].get("add_first") and s._shape._contours: s._shape._contours.insert(0, c)
        else: s._shape._contours.append(c)
        if TE["mode"].get("glyph_added"): TS["edpnew"] = TsGlyph("edpnew", [])
    def removeContour(s, c):
        TE["calls"].append("removeContour")
        if TE["mode"].get("remove_noop"): return
        s._shape._contours = [k for k in s._shape._contours if k is not c]
class TEShape(TESpy):
    def __init__(s, contours=None, composite=False, component=False):
        s._contours = list(contours or []); s._composite = composite; s._component = component; s.shapeData = TEShapeData(s)
    def isComposite(s):
        if TE["mode"].get("composite_raises"): raise RuntimeError("isComposite boom")
        return s._composite
    def isComponent(s): return s._component
class TELayer(TESpy):
    def __init__(s, name, shapes): s.name = name; s._shapes = list(shapes)
    @property
    def shapes(s): return tuple(s._shapes) if TE["mode"].get("shapes_tuple") else list(s._shapes)
    def getContours(s):
        if TE["broken"]: raise RuntimeError("getContours boom")
        return [c for sh in s._shapes for c in sh._contours]
    def shapesCount(s): return len(s._shapes)
    def nodesCount(s):
        if TE["mode"].get("nodes_unreadable"): return "n/a"     # v0.208: a count that is not a number
        return sum(c.nodesCount() for c in s.getContours()) + TE["mode"].get("nodes_extra", 0)     # v0.208: a disagreeing count
    def componentsCount(s): return TE["mode"].get("components", 0)
    def replaceShape(s, old, new):
        TE["calls"].append("replaceShape")
        if TE["mode"].get("replace_raises"): raise RuntimeError("replaceShape boom")
        s._shapes = [new if k is old else k for k in s._shapes]
    def removeShape(s, shape, recursive):     # v0.208 (stage=removeshape)
        TE["calls"].append(("removeShape", recursive))
        if TE["mode"].get("removeshape_raises"): raise RuntimeError("removeShape boom")
        if TE["mode"].get("removeshape_noop"): return
        s._shapes = [k for k in s._shapes if k is not shape]
class TEItems:
    @staticmethod
    def notifyChangesApplied(title, obj, flag): TE["marks"].append((title, type(obj).__name__, flag))
def _te_update(*a):
    TE["updates"].append(tuple(type(x).__name__ for x in a))
    _tcm = TC.get("mode", {}) if isinstance(globals().get("TC"), dict) else {}
    if TE["mode"].get("sync_drops_empty") or _tcm.get("sync_drops_empty"):     # v0.209: a sync that drops every empty shape (ED7 1715, 1717)
        for _L in P72["layers"].values():
            if isinstance(_L, TELayer): _L._shapes = [k for k in _L._shapes if k._contours or getattr(k, "_component", False)]
TE_SQ = [(0, 0), (400, 0), (400, 300), (0, 300)]
TE_TRI = [(50, 50), (150, 50), (100, 150)]
def te_contour(pts):
    c = TEContour([P72Pt(x, y) for x, y in pts]); c._closed = True; return c
_te_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "flWorkspace", "Update", "flItems")]
def te_setup(mode=None, count=1, packages=1, reset_calls=True):
    p81_setup()
    TE.update(forbidden=[], calls=[], mode=dict(mode or {}), updates=[], marks=[], broken=False)
    _fm.flContour = TEContour; _fm.flShape = TEShape
    for g in ("edpa", "edpb", "edpbrush", "edpcomp", "edptwo", "edpnone"): TS[g] = TsGlyph(g, [TsLayer(1, 4)])
    P72["layers"]["edpa"] = TELayer("test_font", [TEShape([te_contour(TE_SQ), te_contour(TE_TRI)])])
    P72["layers"]["edpb"] = TELayer("test_font", [TEShape([te_contour(TE_SQ)])])
    P72["layers"]["edpbrush"] = TELayer("test_font", [TEShape([te_contour(TE_SQ)], composite=True)])
    P72["layers"]["edpcomp"] = TELayer("test_font", [TEShape([te_contour(TE_SQ)], component=True)])
    P72["layers"]["edptwo"] = TELayer("test_font", [TEShape([te_contour(TE_SQ)]), TEShape([te_contour(TE_TRI)])])
    P72["layers"]["edpnone"] = TELayer("test_font", [])
    TO.update(count=count, packages=packages, closed_sets=[], vp=[])
    for _m in _tf_mods:
        _m.CountFonts = _to_count; _m.flWorkspace = TOWsCls; _m.Update = _te_update; _m.flItems = TEItems
    if reset_calls: ns["_TRYEDIT"]["calls"] = 0
TE_ALL_FORBIDDEN = []
def te_outline(d, key):
    snap = d.get(key) or {}
    if "error" in snap: return snap
    return [("closed" if c["closed"] else "open", [(n["x"], n["y"], n["kind"][0], n["smooth"]) for n in c["nodes"]]) for c in snap.get("contours", [])]
def te(tag, path, keys=("error", "calls_so_far")):
    c, d = call(path)
    TE_ALL_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| edit calls", TE["calls"], "| Update", TE["updates"], "| marks", TE["marks"])
    return d
EK = ("edited", "changed", "mismatches", "smooth_changed", "side_effect_detected", "glyph_count_before", "glyph_count_after", "error", "calls_so_far")
QE = "/debug/tryedit?"
MV = QE + "stage=movenode&name=edpa&contour=0&node=2&dx=10&dy=-20"
te_setup()
te("2311a movenode without go          ", MV)
te("2311b go must be exactly yes       ", MV + "&go=maybe")
te("2311c unknown stage                ", QE + "stage=movecontour&name=edpa&go=yes")
te("2311d name without the edp prefix  ", QE + "stage=replace&name=fresh&go=yes")
te("2311e name with a space            ", QE + "stage=replace&name=edp%20a&go=yes")
te("2311f name 'edp' alone             ", QE + "stage=replace&name=edp&go=yes")
te("2311g movenode without contour     ", QE + "stage=movenode&name=edpa&node=2&dx=10&dy=0&go=yes")
te("2311h node is not a number         ", QE + "stage=movenode&name=edpa&contour=0&node=two&dx=10&dy=0&go=yes")
te("2311i dx 201                       ", QE + "stage=movenode&name=edpa&contour=0&node=2&dx=201&dy=0&go=yes")
te("2311j dx and dy both 0             ", QE + "stage=movenode&name=edpa&contour=0&node=2&dx=0&dy=0&go=yes")
te("2311k removecontour without contour", QE + "stage=removecontour&name=edpa&go=yes")
te("2311l a negative contour           ", QE + "stage=removecontour&name=edpa&contour=-1&go=yes")
for tag, over in (("2311m two fonts open               ", dict(count=2)), ("2311n two packages                ", dict(packages=2)),
                  ("2311o CountFonts raises           ", dict(count=RuntimeError("count boom"))), ("2311p no font open                ", dict(count=0))):
    te_setup(**over); te(tag, MV + "&go=yes")
te_setup()
d = te("2312 movenode                     ", MV + "&go=yes", keys=EK)
print("2312a  before                   :", te_outline(d, "before"))
print("2312b  after                    :", te_outline(d, "after"))
print("2312c  call, args, sync, mark   :", d.get("call"), {k: d.get(k) for k in ("contour", "node", "dx", "dy")}, "| synced", d.get("synced_with_fontlab"),
      "| fontlab_sync", (d.get("fontlab_sync") or {}).get("verdict"), "| changed mark", d.get("fontlab_changed_mark"), "| repainted", d.get("display_refreshed"), TO["vp"])
te_setup(); P72["widths"]["edpb"] = 500.0
d = te("2312d movenode, the legacy view agrees", QE + "stage=movenode&name=edpb&contour=0&node=1&dx=5&dy=5&go=yes", keys=("edited", "synced_with_fontlab", "fontlab_changed_mark"))
te_setup()
d = te("2313 addcontour                  ", QE + "stage=addcontour&name=edpb&go=yes", keys=EK)
print("2313a  after                    :", te_outline(d, "after"), "| flContour built:", P72["calls"].count("flContour"))
te_setup()
d = te("2314 removecontour 1              ", QE + "stage=removecontour&name=edpa&contour=1&go=yes", keys=EK)
print("2314a  after                    :", te_outline(d, "after"))
te_setup()
d = te("2315 replace                      ", QE + "stage=replace&name=edpa&go=yes", keys=EK)
print("2315a  after                    :", te_outline(d, "after"), "| shapes after", d.get("state_after", {}).get("shapes"))
te_setup()
te("2316a a Power Brush shape          ", QE + "stage=replace&name=edpbrush&go=yes")
te("2316b a component                  ", QE + "stage=replace&name=edpcomp&go=yes")
te("2316c two shapes                   ", QE + "stage=replace&name=edptwo&go=yes")
te("2316d no shape                     ", QE + "stage=addcontour&name=edpnone&go=yes")
te("2316e a glyph that does not exist  ", QE + "stage=replace&name=edpzz&go=yes")
te("2316f contour 2 of 2               ", QE + "stage=removecontour&name=edpa&contour=2&go=yes")
te("2316g node 4 of 4                  ", QE + "stage=movenode&name=edpa&contour=0&node=4&dx=1&dy=0&go=yes")
te_setup(mode={"composite_raises": 1}); te("2316i isComposite raises         ", QE + "stage=replace&name=edpa&go=yes")
te_setup(mode={"components": 1}); te("2316j the layer counts a component", QE + "stage=replace&name=edpa&go=yes")
te_setup(mode={"shapes_tuple": 1}); te("2316k layer.shapes is a tuple      ", QE + "stage=replace&name=edpa&go=yes")
te_setup(mode={"node_raises": 1}); te("2316l getNodeAt raises           ", MV + "&go=yes", keys=EK)
te_setup(mode={"set_raises": 1}); te("2317a node.x raises              ", MV + "&go=yes", keys=EK)
te_setup(mode={"move_ignored": 1}); te("2317b node.x is ignored          ", MV + "&go=yes", keys=EK)
te_setup(mode={"move_smooth": 1}); d = te("2317c moving sets smooth         ", MV + "&go=yes", keys=EK); print("2317d  mark reason              :", d.get("fontlab_changed_mark"))
te_setup(mode={"add_first": 1}); te("2317e the contour lands first     ", QE + "stage=addcontour&name=edpa&go=yes", keys=EK)
te_setup(mode={"add_raises": 1}); te("2317f addContour raises          ", QE + "stage=addcontour&name=edpa&go=yes", keys=EK)
te_setup(mode={"remove_noop": 1}); te("2317g removeContour does nothing ", QE + "stage=removecontour&name=edpa&contour=0&go=yes", keys=EK)
te_setup(mode={"replace_raises": 1}); te("2317h replaceShape raises        ", QE + "stage=replace&name=edpa&go=yes", keys=EK)
te_setup(mode={"glyph_added": 1}); te("2317i a glyph appears            ", QE + "stage=addcontour&name=edpb&go=yes", keys=EK)
te_setup(mode={"break_on_edit": 1}); d = te("2317j unreadable after the edit   ", QE + "stage=addcontour&name=edpb&go=yes", keys=EK); print("2317k  after                    :", d.get("after"))
te_setup()
for _i in range(8): call(MV + "&go=yes")
te("2318 the limit: call 9 is refused ", MV + "&go=yes")
_src151 = "\n".join(l for l in src[src.index("# /debug/tryedit (v0.151)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("2319 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
print("2319a static scan of the probe (code lines):", len(_src151) > 6000, "| forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeAllShapes|clearContours|smartMove|smartSetXY|moveBy|decomposite|ejectTo|activateBuilder)\s*\(|shapeBuilder|font\.update", _src151),
      "| counter raised before the glyph is read:", _src151.index('_TRYEDIT["calls"] += 1') < _src151.index("_modern_edit_target(name)"))
# v0.208: removeShape is allowed in this probe only as ONE call statement, in the stage=removeshape branch (it was in the forbidden list above)
_rs208 = [l.strip() for l in _src151.split("\n") if _re83.match(r"\s*\w+\.removeShape\(", l)]
print("2319c removeShape call statements:", _rs208, "| inside the removeshape branch:",
      _src151.index('elif stage == "removeshape":') < _src151.index("layer.removeShape(shape, False)\n") < _src151.index("cur_shape = None"))
print("2319b route documented: ", "/debug/tryedit        stage=movenode|addcontour|removecontour|removeshape|replace" in src, "| mark title:", ns["_MARK_TITLES"].get("tryedit"),
      "| dispatched:", 'if path == "/debug/tryedit":' in src)
te_setup()
print("2320 draw_path still refuses a drawn glyph:", p72_post("/glyph/path", {"name": "edpb", "contours": [RRECT]})[1].get("reason", "")[:90].rstrip())

# ---- v0.206: stage=addcontour&kind=square|cubic|open (a curved and an open contour added to an existing shape; square stays the default)
print("\n==== v0.206 /debug/tryedit addcontour kinds ====")
QA = QE + "stage=addcontour&name=edpb"
EKK = ("kind",) + EK
te_setup()
te("2930a kind with stage=movenode     ", MV + "&kind=cubic&go=yes")
te("2930b unknown kind                 ", QA + "&kind=circle&go=yes")
te("2930c cubic without go             ", QA + "&kind=cubic")
te("2930d open without go              ", QA + "&kind=open")
te("2930e square without go            ", QA)
print("2930f refusals counted no call      :", ns["_TRYEDIT"]["calls"])
te_setup()
d = te("2931 cubic beside a straight outline", QA + "&kind=cubic&go=yes", keys=EKK)
print("2931a  after                    :", te_outline(d, "after"))
print("2931b  sync, mark               :", d.get("synced_with_fontlab"), "| changed mark", d.get("fontlab_changed_mark"))
te_setup()
d = te("2932 open beside a straight outline", QA + "&kind=open&go=yes", keys=EKK)
print("2932a  after                    :", te_outline(d, "after"))
te_setup()
call(QA + "&kind=cubic&go=yes")
d = te("2933 open beside square + circle  ", QA + "&kind=open&go=yes", keys=EKK)
print("2933a  before                   :", te_outline(d, "before"))
print("2933b  after                    :", te_outline(d, "after"))
print("2933c  old contours unchanged   :", (d.get("after") or {}).get("contours", [])[:2] == (d.get("before") or {}).get("contours"))
te_setup()
call(QA + "&kind=cubic&go=yes")
d = te("2934 cubic beside square + circle ", QA + "&kind=cubic&go=yes", keys=EKK)
print("2934a  contours after           :", len((d.get("after") or {}).get("contours", [])))
te_setup(); d1 = call(QA + "&go=yes")[1]
te_setup(); d2 = call(QA + "&kind=square&go=yes")[1]
print("2935 default is square            :", d1.get("kind"), d2.get("kind"), "| same outline after:", d1.get("after") == d2.get("after"), "| edited", d1.get("edited"), d2.get("edited"))
te_setup(); P72["mode"]["contour_raises"] = 1
te("2936a builder raises (cubic)       ", QA + "&kind=cubic&go=yes", keys=EKK)
te_setup(); P72["mode"]["smooth_ignored"] = 1
te("2936b smooth not kept detached     ", QA + "&kind=cubic&go=yes", keys=EKK)
te_setup(); P72["mode"]["noclose"] = 1
te("2936c circle does not close detached", QA + "&kind=cubic&go=yes", keys=EKK)
te_setup(mode={"add_first": 1})
te("2936d the open arch lands first    ", QE + "stage=addcontour&name=edpa&kind=open&go=yes", keys=EKK)
print("2937 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)

# ---- v0.208: stage=removeshape (option C of the remove-contour design: the EMPTY shape that removing the last contour leaves, ED5 1699)
print("\n==== v0.208 /debug/tryedit removeshape ====")
QR = QE + "stage=removeshape&name="
EKR = ("shapes_before", "shapes_after") + EK
def te_empty_setup(mode=None):
    te_setup(mode=mode)
    TS["edpempty"] = TsGlyph("edpempty", [TsLayer(0, 0)])     # the legacy view of an empty glyph: 0 contours, 0 nodes
    P72["layers"]["edpempty"] = TELayer("test_font", [TEShape([])])
te_empty_setup()
te("2940a removeshape without go       ", QR + "edpempty")
te("2940b with contour=0               ", QR + "edpempty&contour=0&go=yes")
te("2940c with kind=square             ", QR + "edpempty&kind=square&go=yes")
te("2940d with refresh=layer.update    ", QR + "edpempty&refresh=layer.update&go=yes")
print("2940e refusals counted no call      :", ns["_TRYEDIT"]["calls"])
d = te("2941 removeshape on an empty shape", QR + "edpempty&go=yes", keys=EKR)
print("2941a  call, after, state       :", d.get("call"), "| after", te_outline(d, "after"), "| state_after shapes", (d.get("state_after") or {}).get("shapes"),
      "| nodes", (d.get("state_after") or {}).get("nodes"))
print("2941b  sync, mark               :", d.get("synced_with_fontlab"), "| changed mark", d.get("fontlab_changed_mark"), "| repainted", d.get("display_refreshed"))
te_empty_setup(); P72["widths"]["edpempty"] = 500.0     # as 2312d: the legacy view agrees, so the sync is confirmed and the mark made
te("2941c removeshape, the legacy view agrees", QR + "edpempty&go=yes", keys=("edited", "changed", "synced_with_fontlab", "fontlab_changed_mark"))
te_empty_setup()
d = te("2942 a shape holding a contour    ", QR + "edpb&go=yes", keys=EKR)
print("2942a  outline unchanged        :", te_outline(d, "before") if "before" in d else None, "| layer shapes", len(P72["layers"]["edpb"]._shapes))
te_empty_setup()
te("2942b a shape holding 2 contours   ", QR + "edpa&go=yes", keys=EKR)
te("2942c two shapes                   ", QR + "edptwo&go=yes", keys=EKR)
te("2942d no shape                     ", QR + "edpnone&go=yes", keys=EKR)
te("2942e a Power Brush shape          ", QR + "edpbrush&go=yes", keys=EKR)
te_empty_setup(mode={"nodes_extra": 3})
te("2942f 0 contours but 3 nodes read  ", QR + "edpempty&go=yes", keys=EKR)
print("2942g  shape kept               :", len(P72["layers"]["edpempty"]._shapes))
te_empty_setup(mode={"nodes_unreadable": 1})
te("2942h the node count is unreadable ", QR + "edpempty&go=yes", keys=EKR)
print("2942i  shape kept               :", len(P72["layers"]["edpempty"]._shapes))
te_empty_setup()
P72["layers"]["edpempty"] = TELayer("test_font", [TEShape([te_contour([])])])     # one contour with no node: 0 nodes, but not 0 contours
te("2942j a contour with no node       ", QR + "edpempty&go=yes", keys=EKR)
print("2942k  shape kept               :", len(P72["layers"]["edpempty"]._shapes))
te_empty_setup(mode={"removeshape_raises": 1})
te("2943a removeShape raises           ", QR + "edpempty&go=yes", keys=EKR)
te_empty_setup(mode={"removeshape_noop": 1})
d = te("2943b removeShape does nothing    ", QR + "edpempty&go=yes", keys=EKR)
print("2943c  mark                     :", d.get("fontlab_changed_mark"))
print("2944 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
TS.pop("edpempty", None); P72["layers"].pop("edpempty", None); P72["widths"].pop("edpempty", None)     # the later blocks see the glyph set they saw before v0.208

# ---- v0.209: state_after_sync (read after _guard_mark) and &mark=no (the sync without the changed mark); ED6 1707-1712
print("\n==== v0.209 /debug/tryedit state_after_sync and mark=no ====")
def te_sync(tag, path):
    c, d = call(path)
    TE_ALL_FORBIDDEN.extend(TE["forbidden"])
    sh = lambda k: (d.get(k) or {}).get("shapes") if k in d else "absent"
    print(tag, ":", c, "| shapes after / after sync:", sh("state_after"), "/", sh("state_after_sync"), "| synced_before_read", d.get("synced_before_read", "absent"),
          "| synced", d.get("synced_with_fontlab"), "| mark", d.get("fontlab_changed_mark"), "| edited", d.get("edited"), "| error", d.get("error"),
          "| Update", TE["updates"], "| marks", TE["marks"])
    return d
te_setup()
te("2950a mark=yes                     ", QE + "stage=addcontour&name=edpb&mark=yes&go=yes")
te("2950b mark=no without go           ", QE + "stage=addcontour&name=edpb&mark=no")
print("2950c refusals counted no call      :", ns["_TRYEDIT"]["calls"])
te_setup(); P72["widths"]["edpb"] = 500.0     # as 2312d: the legacy view agrees, so the sync is confirmed
te_sync("2951 movenode, default mark      ", QE + "stage=movenode&name=edpb&contour=0&node=1&dx=5&dy=5&go=yes")
te_setup(); P72["widths"]["edpb"] = 500.0
te_sync("2952 movenode, mark=no           ", QE + "stage=movenode&name=edpb&contour=0&node=1&dx=5&dy=5&mark=no&go=yes")
te_setup(mode={"sync_drops_empty": 1})
te_sync("2953a last contour, the sync drops the empty shape", QE + "stage=removecontour&name=edpb&contour=0&go=yes")
te_setup(mode={"sync_drops_empty": 1})
te_sync("2953b the same with mark=no      ", QE + "stage=removecontour&name=edpb&contour=0&mark=no&go=yes")
te_setup()
te_sync("2953c last contour, the sync keeps it", QE + "stage=removecontour&name=edpb&contour=0&go=yes")
te_setup(mode={"sync_drops_empty": 1})
te_sync("2953d one of two contours (control)", QE + "stage=removecontour&name=edpa&contour=0&go=yes")
te_setup(mode={"remove_noop": 1})
te_sync("2954 nothing changed: no sync    ", QE + "stage=removecontour&name=edpa&contour=0&go=yes")
te_setup()
te_sync("2955 refused early (two shapes)  ", QE + "stage=removecontour&name=edptwo&contour=0&go=yes")
print("2956 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
P72["widths"].pop("edpb", None)

# ---- v0.213: &shape=I, shape I of a glyph with several shapes (P2.2; names only 1807). The TE fakes with shapes that have a transform,
# contoursCount, getContours() and component shape data. A component shape shares its source's contour LIST, as in FontLab (live 606):
# layer.getContours() then gives the source's own contour objects, so an edit through them would change the source.
print("\n==== v0.213 /debug/tryedit shape= ====")
SH = {}
class SHQT(TESpy):
    def __init__(s, m=(1, 0, 0, 1, 0, 0)): s._m = tuple(float(v) for v in m)
    def m11(s): return s._m[0]
    def m12(s): return s._m[1]
    def m21(s): return s._m[2]
    def m22(s): return s._m[3]
    def dx(s): return s._m[4]
    def dy(s): return s._m[5]
class SHShapeData(TEShapeData):
    def __init__(s, shape, glyph=""): TEShapeData.__init__(s, shape); s._glyph = glyph
    def componentGlyph(s): return s._glyph
    def componentLayer(s): return "test_font" if s._glyph else ""
    def referenceCount(s): return 2 if s._glyph else 1
    def addContour(s, c):
        m = TE["mode"]
        if m.get("sh_add_into_component"): SH["comp"]._contours.append(c); TE["calls"].append("addContour"); return
        TEShapeData.addContour(s, c)
        if m.get("sh_add_touches_source"): SH["src"]._contours[0].rows[0]["x"] += 1.0
        if m.get("sh_tx_moves"): SH["comp"]._tx = SHQT((1, 0, 0, 1, 201, 0))
class SHShape(TEShape):
    def __init__(s, contours=None, component="", composite=False, m=(1, 0, 0, 1, 0, 0), shared=None):
        TEShape.__init__(s, contours, composite=composite, component=bool(component))
        if shared is not None: s._contours = shared
        s.shapeData = SHShapeData(s, component); s._tx = SHQT(m)
    @property
    def transform(s): return s._tx
    def contoursCount(s): return len(s._contours) + (1 if TE["mode"].get("sh_count_wrong") and not s._component else 0)
    def getContours(s):
        m = TE["mode"]
        TE["calls"].append(("shape.getContours", len(s._contours)))
        if m.get("sh_gc_raises"): raise RuntimeError("getContours boom")
        if m.get("sh_gc_dict"): return {}
        if m.get("sh_gc_disagree"): return list(reversed(s._contours))
        return list(s._contours)
def sh_setup(mode=None):
    te_setup(mode=mode)
    src = SHShape([te_contour([(0, 0), (50, 0), (50, 50), (0, 50)])])
    SH["src"] = src
    TS["edpssrc"] = TsGlyph("edpssrc", [TsLayer(1, 4)]); P72["layers"]["edpssrc"] = TELayer("test_font", [src])
    comp = SHShape(component="edpssrc", shared=src._contours, m=(1, 0, 0, 1, 200, 0))
    SH["comp"] = comp
    for g, shapes in (("edpsa", [SHShape([te_contour(TE_SQ), te_contour(TE_TRI)]), comp]),
                      ("edpsb", [SHShape(component="edpssrc", shared=src._contours, m=(1, 0, 0, 1, 200, 0)), SHShape([te_contour(TE_SQ), te_contour(TE_TRI)])]),
                      ("edpsbrush", [SHShape([te_contour(TE_SQ)]), SHShape([te_contour(TE_TRI)], composite=True)]),
                      ("edpstx", [SHShape([te_contour(TE_SQ)], m=(1, 0, 0, 1, 10, 0)), SHShape(component="edpssrc", shared=src._contours)]),
                      ("edpstwo", [SHShape([te_contour(TE_SQ)]), SHShape([te_contour(TE_TRI)])])):
        TS[g] = TsGlyph(g, [TsLayer(1, 4)]); P72["layers"][g] = TELayer("test_font", shapes)
EKS = ("edited", "changed", "mismatches", "side_effect_detected", "other_shapes_unchanged", "sources_unchanged", "contour_counts_before",
       "contour_counts_after", "contour_counts_expected", "shape_contours_offset", "shape", "error", "calls_so_far")
def sh_show(tag, d):
    print(tag, " before:", te_outline(d, "before"))
    print(tag, " after :", te_outline(d, "after"))
    print(tag, " elements after:", [(e["index"], e["is_component"], e["component_glyph"], (e.get("matrix") or {}).get("dx")) for e in d.get("elements_after") or []],
          "| source now:", [[(r["x"], r["y"]) for r in c.rows] for c in SH["src"]._contours], "| sync", (d.get("fontlab_sync") or {}).get("verdict"))
QS = QE + "stage="
sh_setup()
te("2980a shape with stage=replace     ", QS + "replace&name=edpsa&shape=0&go=yes")
te("2980b shape with stage=removeshape ", QS + "removeshape&name=edpsa&shape=0&go=yes")
te("2980c shape 20                     ", QS + "addcontour&name=edpsa&shape=20&go=yes")
te("2980d shape is not a number        ", QS + "addcontour&name=edpsa&shape=one&go=yes")
te("2980e shape with refresh           ", QS + "movenode&name=edpsa&shape=0&contour=0&node=1&dx=5&dy=0&refresh=layer.update&go=yes")
te("2980f movenode with shape, no go   ", QS + "movenode&name=edpsa&shape=0&contour=0&node=1&dx=5&dy=0")
te("2980g addcontour with shape, no go ", QS + "addcontour&name=edpsa&shape=0&kind=cubic")
te("2980h removecontour with shape, no go", QS + "removecontour&name=edpsa&shape=0&contour=1")
print("2980j refusals counted no call      :", ns["_TRYEDIT"]["calls"])
te("2980i an empty shape= is left out  ", QS + "replace&name=edpsa&shape=&go=yes")
sh_setup()
d = te("2981 movenode, plain shape first  ", QS + "movenode&name=edpsa&shape=0&contour=0&node=2&dx=10&dy=-20&go=yes", keys=EKS); sh_show("2981a", d)
sh_setup()
d = te("2982 addcontour, plain shape first", QS + "addcontour&name=edpsa&shape=0&go=yes", keys=EKS); sh_show("2982a", d)
sh_setup()
d = te("2983 removecontour 1, plain first ", QS + "removecontour&name=edpsa&shape=0&contour=1&go=yes", keys=EKS); sh_show("2983a", d)
sh_setup()
d = te("2984 movenode, component first    ", QS + "movenode&name=edpsb&shape=1&contour=0&node=1&dx=5&dy=5&go=yes", keys=EKS); sh_show("2984a", d)
sh_setup()
d = te("2984b addcontour, component first ", QS + "addcontour&name=edpsb&shape=1&kind=open&go=yes", keys=EKS); sh_show("2984c", d)
sh_setup()
d = te("2984d removecontour 0, component first", QS + "removecontour&name=edpsb&shape=1&contour=0&go=yes", keys=EKS); sh_show("2984e", d)
sh_setup()
d = te("2984f two plain shapes, the second", QS + "addcontour&name=edpstwo&shape=1&go=yes", keys=EKS); sh_show("2984g", d)
sh_setup()
te("2985a shape 1 is the component     ", QS + "movenode&name=edpsa&shape=1&contour=0&node=0&dx=1&dy=0&go=yes")
te("2985b shape 0 is the component     ", QS + "removecontour&name=edpsb&shape=0&contour=0&go=yes")
te("2985c a Power Brush shape beside   ", QS + "addcontour&name=edpsbrush&shape=0&go=yes")
te("2985d shape 0 has a transform      ", QS + "addcontour&name=edpstx&shape=0&go=yes")
te("2985e shape 2 of 2                 ", QS + "addcontour&name=edpsa&shape=2&go=yes")
te("2985f contour 2 of shape 0 (2)     ", QS + "removecontour&name=edpsa&shape=0&contour=2&go=yes")
te("2985g node 3 of a triangle         ", QS + "movenode&name=edpsa&shape=0&contour=1&node=3&dx=1&dy=0&go=yes")
te("2985h no shape= on two shapes      ", QS + "addcontour&name=edpsa&go=yes")
print("2985i source untouched by refusals  :", [[(r["x"], r["y"]) for r in c.rows] for c in SH["src"]._contours], "| edit calls", TE["calls"])
for tag, mode in (("2986a contoursCount disagrees      ", {"sh_count_wrong": 1}), ("2986b shape.getContours() raises   ", {"sh_gc_raises": 1}),
                  ("2986c shape.getContours() a dict   ", {"sh_gc_dict": 1}), ("2986d the two reads disagree      ", {"sh_gc_disagree": 1}),
                  ("2986e isComposite raises         ", {"composite_raises": 1}), ("2986f layer.shapes is a tuple      ", {"shapes_tuple": 1})):
    sh_setup(mode=mode); te(tag, QS + "addcontour&name=edpsa&shape=0&go=yes")
    print("       nothing touched              :", [c for c in TE["calls"] if c in ("addContour", "removeContour")] == [], "| marks", TE["marks"])
sh_setup(mode={"sh_add_touches_source": 1})
d = te("2987a the add also moves the source", QS + "addcontour&name=edpsa&shape=0&go=yes", keys=EKS); sh_show("2987b", d); print("2987c  mark:", d.get("fontlab_changed_mark"))
sh_setup(mode={"sh_tx_moves": 1})
d = te("2987d the add moves the component ", QS + "addcontour&name=edpsa&shape=0&go=yes", keys=EKS); sh_show("2987e", d)
sh_setup(mode={"sh_add_into_component": 1})
d = te("2987f the contour lands in the component", QS + "addcontour&name=edpsa&shape=0&go=yes", keys=EKS); sh_show("2987g", d)
sh_setup(mode={"add_first": 1})
d = te("2987h the contour lands first in shape 0", QS + "addcontour&name=edpsa&shape=0&go=yes", keys=EKS); sh_show("2987i", d)
sh_setup(mode={"remove_noop": 1})
te("2987j removeContour does nothing   ", QS + "removecontour&name=edpsa&shape=0&contour=0&go=yes", keys=EKS)
sh_setup()
for _i in range(8): call(QS + "movenode&name=edpsa&shape=0&contour=0&node=0&dx=1&dy=0&go=yes")
te("2988 the limit holds with shape=   ", QS + "movenode&name=edpsa&shape=0&contour=0&node=0&dx=1&dy=0&go=yes")
print("2989 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
_src213 = "\n".join(l for l in src[src.index("# /debug/tryedit (v0.151)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("2989a getContours() call sites in the probe:", sorted(set(_re83.findall(r"\b\w+\.getContours\(\)", _src213))),
      "| shape= dispatched:", '(query.get("shape") or [None])[0]' in src, "| route documented:", "&shape=I edits shape I of a glyph" in src)

# ---- v0.214: stage=addshape (design question 5, research first: a NEW plain shape beside existing shapes, e.g. a glyph of components only)
print("\n==== v0.214 /debug/tryedit addshape ====")
class SHLayer(TELayer):
    def addShape(s, shape):
        m = TE["mode"]
        TE["calls"].append(("addShape", len(shape._contours)))
        if m.get("as_add_raises"): raise RuntimeError("addShape boom")
        if m.get("as_add_noop"): return shape
        if m.get("as_flshape_tx"): shape._tx = SHQT((1, 0, 0, 1, 5, 0))
        if m.get("as_add_touches_source"): SH["src"]._contours[0].rows[0]["x"] += 1.0
        if m.get("as_add_first"): s._shapes.insert(0, shape)
        else: s._shapes.append(shape)
        return shape
def as_setup(mode=None):
    sh_setup(mode=mode)
    _fm.flShape = SHShape
    src = SH["src"]
    for g, shapes in (("edpak", [SHShape(component="edpssrc", shared=src._contours, m=(1, 0, 0, 1, 300, 0))]),
                      ("edpakp", [SHShape([te_contour(TE_SQ)]), SHShape(component="edpssrc", shared=src._contours, m=(1, 0, 0, 1, 300, 0))]),
                      ("edpak2", [SHShape([te_contour(TE_SQ)]), SHShape([te_contour(TE_TRI)])]),
                      ("edpaktx", [SHShape(component="edpssrc", shared=src._contours, m=(2, 0, 0, 1, 300, 0))]),
                      ("edpakrot", [SHShape(component="edpssrc", shared=src._contours, m=(0, 1, -1, 0, 0, 0))]),
                      ("edpakpt", [SHShape([te_contour(TE_SQ)], m=(1, 0, 0, 1, 10, 0)), SHShape(component="edpssrc", shared=src._contours)]),
                      ("edpakbr", [SHShape(component="edpssrc", shared=src._contours), SHShape([te_contour(TE_TRI)], composite=True)]),
                      ("edpakempty", [])):
        TS[g] = TsGlyph(g, [TsLayer(1, 4)]); P72["layers"][g] = SHLayer("test_font", shapes)
EKA = ("edited", "changed", "mismatches", "side_effect_detected", "new_shape_ok", "other_shapes_unchanged", "sources_unchanged",
       "contour_counts_before", "contour_counts_after", "contour_counts_expected", "error", "calls_so_far")
QAS = QE + "stage=addshape&name="
as_setup()
te("2990a addshape without go           ", QAS + "edpak")
te("2990b with contour=0                ", QAS + "edpak&contour=0&go=yes")
te("2990c with refresh=layer.update     ", QAS + "edpak&refresh=layer.update&go=yes")
te("2990d with shape=0                  ", QAS + "edpak&shape=0&go=yes")
te("2990e with kind=square              ", QAS + "edpak&kind=square&go=yes")
print("2990f refusals counted no call      :", ns["_TRYEDIT"]["calls"])
as_setup()
d = te("2991 a glyph of one component     ", QAS + "edpak&go=yes", keys=EKA); sh_show("2991a", d)
print("2991b  call, new shape, sync     :", d.get("call"), "| state after sync:", {k: (d.get("state_after_sync") or {}).get(k) for k in ("shapes", "components")},
      "| synced_before_read", d.get("synced_before_read"))
as_setup()
d = te("2992 a plain shape and a component", QAS + "edpakp&go=yes", keys=EKA); sh_show("2992a", d)
as_setup()
d = te("2993 two plain shapes            ", QAS + "edpak2&go=yes", keys=EKA); sh_show("2993a", d)
as_setup()
te("2994a a scaled component          ", QAS + "edpaktx&go=yes")
te("2994b a rotated component         ", QAS + "edpakrot&go=yes")
te("2994c a plain shape with a transform", QAS + "edpakpt&go=yes")
te("2994d a Power Brush shape         ", QAS + "edpakbr&go=yes")
te("2994e an empty glyph (no shape)   ", QAS + "edpakempty&go=yes")
print("2994f nothing added by refusals    :", [c for c in TE["calls"] if isinstance(c, tuple) and c[0] == "addShape"], "| marks", TE["marks"])
for tag, mode in (("2995a isComposite raises          ", {"composite_raises": 1}), ("2995b contoursCount disagrees      ", {"sh_count_wrong": 1}),
                  ("2995c layer.shapes is a tuple       ", {"shapes_tuple": 1})):
    as_setup(mode=mode); te(tag, QAS + "edpakp&go=yes")
    print("       nothing added                :", [c for c in TE["calls"] if isinstance(c, tuple) and c[0] == "addShape"] == [])
as_setup(mode={"as_add_raises": 1})
te("2996a addShape raises             ", QAS + "edpak&go=yes", keys=EKA)
as_setup(mode={"as_add_noop": 1})
d = te("2996b addShape adds nothing       ", QAS + "edpak&go=yes", keys=EKA); print("2996c  mark:", d.get("fontlab_changed_mark"), "| synced_before_read", d.get("synced_before_read"))
as_setup(mode={"as_add_first": 1})
d = te("2996d the new shape lands first    ", QAS + "edpakp&go=yes", keys=EKA); sh_show("2996e", d)
as_setup(mode={"as_flshape_tx": 1})
te("2996f the new shape gets an offset ", QAS + "edpak&go=yes", keys=EKA)
as_setup(mode={"as_add_touches_source": 1})
d = te("2996g the add moves the source     ", QAS + "edpak&go=yes", keys=EKA); print("2996h  mark:", d.get("fontlab_changed_mark"))
as_setup(); P72["mode"]["contour_raises"] = 1
te("2996i the square cannot be built   ", QAS + "edpak&go=yes", keys=EKA)
as_setup()
for _i in range(8): call(QAS + "edpak2&go=yes")
te("2997 the limit holds              ", QAS + "edpak&go=yes")
print("2998 spies over all cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
_src214 = "\n".join(l for l in src[src.index("# /debug/tryedit (v0.151)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("2998a addShape call statements:", [l.strip() for l in _src214.split("\n") if _re83.match(r"\s*\w+\.addShape\(", l)],
      "| forbidden call syntax:", _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeAllShapes|clearContours|smartMove|smartSetXY|moveBy|decomposite|ejectTo|activateBuilder)\s*\(|shapeBuilder|font\.update", _src214),
      "| route documented:", "stage=addshape adds one new plain shape" in src)
for _g in ("edpak", "edpakp", "edpak2", "edpaktx", "edpakrot", "edpakpt", "edpakbr", "edpakempty"): TS.pop(_g, None); P72["layers"].pop(_g, None)
for _g in ("edpssrc", "edpsa", "edpsb", "edpsbrush", "edpstx", "edpstwo"): TS.pop(_g, None); P72["layers"].pop(_g, None)     # later blocks see the glyph set they saw before v0.213

# ---- v0.152: &refresh=R. The fake sidebearings stay stale after an edit (as live 968, 974, 980) until the ONE member named in
# TE["mode"]["refresh_works"] is called; every refresh member logs into TE["refresh"].
print("\n==== v0.152 /debug/tryedit refresh ====")
def _te_refresh(label, obj):
    TE.setdefault("refresh", []).append(label if not isinstance(obj, TEShape) else (label, len(obj._contours)))
    m = TE["mode"]
    if m.get("refresh_raises"): raise RuntimeError("refresh boom")
    if m.get("refresh_moves"):
        for lay in P72["layers"].values():
            if isinstance(lay, TELayer) and lay._shapes and lay._shapes[0]._contours: lay._shapes[0]._contours[0].rows[0]["x"] += 1.0; break
    if m.get("refresh_works") == label:
        for gname in list(TE.get("metrics", {})): te_recompute(gname)
    return m.get("refresh_returns")
TEContour.update = lambda s: _te_refresh("contour.update", s)
TEShape.update = lambda s: _te_refresh("shape.update", s)
TEShape.changed = lambda s: _te_refresh("shape.changed", s)
TEShapeData.update = lambda s: _te_refresh("shapedata.update", s)
TELayer.update = lambda s: _te_refresh("layer.update", s)
TELayer.changed = lambda s: _te_refresh("layer.changed", s)
TELayer.resetInkBox = lambda s: _te_refresh("layer.resetinkbox", s)
_te_p72_saved = {a: P72Mod.__dict__.get(a) for a in ("getLSB", "getRSB", "update")}
def te_recompute(gname):
    lay = P72["layers"].get(gname)
    xs = [r["x"] for c in (lay.getContours() if lay is not None else []) for r in c.rows]
    adv = P72.get("widths", {}).get(gname, 0.0)
    TE["metrics"][gname] = (min(xs), adv - max(xs)) if xs else (0.0, 0.0)
def te2_setup(mode=None):
    te_setup(mode=mode); TE["refresh"] = []; TE["metrics"] = {}
    P72Mod.getLSB = lambda s, tr: TE["metrics"].get(s.name, (0.0, 0.0))[0]
    P72Mod.getRSB = lambda s, tr: TE["metrics"].get(s.name, (0.0, 0.0))[1]
    P72Mod.update = lambda s: _te_refresh("glyph.update", s)
    for g in ("edpa", "edpb"): te_recompute(g)
RK = ("refresh", "refresh_call", "refresh_returned", "refresh_error", "margins_before_refresh", "margins_after_refresh", "margins_expected",
      "margins_current_before_refresh", "margins_current_after_refresh", "refresh_changed_outline", "edited", "side_effect_detected", "error")
def te2(tag, path, keys=RK):
    d = te(tag, path, keys=keys)
    print("      refresh log:", TE["refresh"])
    return d
te2_setup()
te2("2321a an unknown refresh            ", MV + "&refresh=font.update&go=yes", keys=("error", "calls_so_far"))
te2("2321b resetMetricsLeft is not listed", MV + "&refresh=layer.resetmetricsleft&go=yes", keys=("error", "calls_so_far"))
te2("2321c contour.update needs movenode ", QE + "stage=addcontour&name=edpb&refresh=contour.update&go=yes", keys=("error", "calls_so_far"))
te2("2321d refresh without go            ", MV + "&refresh=layer.update", keys=("error", "calls_so_far"))
te2("2321e an empty refresh = none       ", MV + "&refresh=&go=yes", keys=("edited", "refresh", "refresh_error", "margins_before_refresh"))
for r in ("contour.update", "shape.update", "shapedata.update", "layer.update", "glyph.update", "layer.changed", "shape.changed", "layer.resetinkbox"):
    te2_setup(mode={"refresh_works": r})
    te2("2322 refresh=%-18s works" % r, MV + "&refresh=" + r + "&go=yes")
te2_setup(mode={"refresh_works": "layer.update"})
te2("2323 shape.update, which does not refresh", MV + "&refresh=shape.update&go=yes")
te2_setup(mode={"refresh_works": "shape.update", "refresh_returns": True})
te2("2324 a refresh returning True       ", MV + "&refresh=shape.update&go=yes", keys=("refresh_returned", "margins_current_after_refresh"))
te2_setup(mode={"refresh_raises": 1})
te2("2325 a refresh that raises          ", MV + "&refresh=layer.update&go=yes")
te2_setup(mode={"refresh_moves": 1})
te2("2326 a refresh that moves a node    ", MV + "&refresh=layer.update&go=yes", keys=("refresh_changed_outline", "edited", "side_effect_detected", "mismatches"))
te2_setup(mode={"set_raises": 1})
te2("2327 the edit failed: no refresh    ", MV + "&refresh=layer.update&go=yes", keys=("refresh", "refresh_error", "edited", "error"))
te2_setup(mode={"refresh_works": "shape.update"})
te2("2328 replace: the NEW shape updated ", QE + "stage=replace&name=edpa&refresh=shape.update&go=yes")
te2_setup(mode={"refresh_works": "layer.update"})
P72["layers"]["edpb"].getContours()[0].rows[1]["on"] = False
te2("2329 a curve: no expected margins   ", QE + "stage=addcontour&name=edpb&refresh=layer.update&go=yes", keys=("margins_expected", "margins_current_after_refresh", "edited"))
te2_setup(mode={"refresh_works": "layer.update"}); ns["_trymetrics_transform"], _te_tm = (lambda: (None, "no QTransform here")), ns["_trymetrics_transform"]
te2("2330 no QTransform: margins unknown ", MV + "&refresh=layer.update&go=yes", keys=("margins_before_refresh", "margins_after_refresh", "margins_expected", "refresh_call", "edited"))
ns["_trymetrics_transform"] = _te_tm
print("2331 spies over the refresh cases:", TE_ALL_FORBIDDEN, "| refresh table:", ns["_TRYEDIT_REFRESH"])
_src152 = "\n".join(l for l in src[src.index("# /debug/tryedit (v0.151)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("2331a static scan: forbidden call syntax:", _re83.findall(r"\.(?:update|save\w*|removeGlyph|smartMove|moveBy|decomposite|ejectTo|activateBuilder|resetMetrics\w*)\s*\(|resetMetrics|font\.update", _src152),
      "| getattr calls:", _re83.findall(r"getattr\([^)]*\)", _src152), "| route documented:", "[&refresh=R]:\n                          ONE edit" in src)

# ================= v0.153: POST /glyph/move (move_nodes, the first product edit of an existing outline, P2.2) =================
# The /debug/tryedit fakes above (TE spies, te2_setup: the sidebearings stay stale until the refresh named in "refresh_works" runs).
# The shape's transform is a plain fake whose six values come from TE["mode"]["tx"]; "tx_raises" makes reading it fail.
print("\n==== v0.153 POST /glyph/move (move_nodes) ====")
class MvTr:
    def __init__(s, vals): s._v = vals
    def m11(s): return s._v.get("m11", 1.0)
    def m12(s): return s._v.get("m12", 0.0)
    def m21(s): return s._v.get("m21", 0.0)
    def m22(s): return s._v.get("m22", 1.0)
    def dx(s): return s._v.get("dx", 0.0)
    def dy(s): return s._v.get("dy", 0.0)
def _mv_transform(s):
    if TE["mode"].get("tx_raises"): raise RuntimeError("transform boom")
    return MvTr(TE["mode"].get("tx", {}))
TEShape.transform = property(_mv_transform)
# v0.215: several shapes read each shape's contoursCount and getContours() and, through _trycomp_elements, its shape data's component
# fields, as FontLab's objects have them (a plain shape: componentGlyph ""); the counts follow the shape's own list.
TEShape.contoursCount = lambda s: len(s._contours)
TEShape.getContours = lambda s: list(s._contours)
TEShapeData.componentGlyph = lambda s: ""
TEShapeData.componentLayer = lambda s: ""
TEShapeData.referenceCount = lambda s: 1
MVK =("moved", "nodes_match", "changed", "mismatches", "reason", "coordinates_rounded", "ink_box_refresh", "margins", "synced_with_fontlab", "fontlab_changed_mark")
def mv_setup(mode=None):
    te2_setup(mode=dict({"refresh_works": "layer.resetinkbox"}, **(mode or {})))
    P72["widths"]["edpb"] = 500.0; P72["widths"]["edpa"] = 500.0; P72["widths"]["edps"] = 500.0
    for g in ("edpb", "edpa"): te_recompute(g)
def mv(tag, payload, keys=MVK):
    c, d = sbpost("/glyph/move", payload)
    TE_ALL_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| edit calls", TE["calls"], "| Update", TE["updates"], "| marks", TE["marks"], "| refresh", TE.get("refresh"))
    return d
def M(c, n, f, t): return {"contour": c, "node": n, "from": {"x": f[0], "y": f[1]}, "to": {"x": t[0], "y": t[1]}}
B1 = M(0, 1, (400, 0), (450, 0))
mv_setup()
for tag, body in (("2332a name missing                ", {"moves": [B1]}), ("2332b moves not a list            ", {"name": "edpb", "moves": B1}),
                  ("2332c no moves                     ", {"name": "edpb", "moves": []}), ("2332d 201 moves                    ", {"name": "edpb", "moves": [B1] * 201}),
                  ("2332e a move without to            ", {"name": "edpb", "moves": [{"contour": 0, "node": 1, "from": {"x": 400, "y": 0}}]}),
                  ("2332f a move with an extra key     ", {"name": "edpb", "moves": [dict(B1, dx=5)]}),
                  ("2332g contour is a bool            ", {"name": "edpb", "moves": [dict(B1, contour=True)]}),
                  ("2332h node -1                      ", {"name": "edpb", "moves": [dict(B1, node=-1)]}),
                  ("2332i node 5001                    ", {"name": "edpb", "moves": [dict(B1, node=5001)]}),
                  ("2332j contour 1.0                  ", {"name": "edpb", "moves": [dict(B1, contour=1.0)]}),
                  ("2332k from is a list               ", {"name": "edpb", "moves": [dict(B1, **{"from": [400, 0]})]}),
                  ("2332l to has an extra key          ", {"name": "edpb", "moves": [dict(B1, to={"x": 1, "y": 2, "z": 3})]}),
                  ("2332m to.x is text                 ", {"name": "edpb", "moves": [dict(B1, to={"x": "450", "y": 0})]}),
                  ("2332n to.y 20001                   ", {"name": "edpb", "moves": [dict(B1, to={"x": 450, "y": 20001})]}),
                  ("2332o the same node twice          ", {"name": "edpb", "moves": [B1, M(0, 1, (400, 0), (460, 0))]}),
                  ("2332p to equals from after rounding", {"name": "edpb", "moves": [M(0, 1, (400, 0), (400.4, -0.5))]})):
    mv(tag, body, keys=("error",))
c, d = ns["_route"]("POST", "/glyph/move", b"{not json").partition(b"\r\n\r\n")[0][9:12], None
print("2332q not JSON                     :", c.decode())
mv_setup()
d = mv("2333 one straight move            ", {"name": "edpb", "moves": [B1]})
print("2333a  after, margins, ink width   :", te_outline({"after": {"contours": d.get("after")}}, "after"), d.get("margins"), d.get("ink_width"), "| repainted", d.get("display_refreshed"))
print("2333b  no before / expected on success:", "before" not in d, "expected_after" not in d, "| guard kind", ns["_guard_state"](ns["_open_font"]())["glyphs"].get("edpb"))
mv_setup(mode={"refresh_works": None})
d = mv("2333c v0.154 no refresh: margins as read", {"name": "edpb", "moves": [B1]}, keys=("moved", "margins", "ink_box_refresh"))
mv_setup()
d = mv("2333d rule B on to                ", {"name": "edpb", "moves": [M(0, 1, (400, 0), (450.5, -0.4))]})
mv_setup()
d = mv("2333e two moves in two contours   ", {"name": "edpa", "moves": [M(0, 2, (400, 300), (420, 310)), M(1, 0, (50, 50), (40, 40))]}, keys=MVK + ("moves_requested",))
print("2333f  after                       :", te_outline({"after": {"contours": d.get("after")}}, "after"))
mv_setup()
for tag, body in (("2334a a stale from refuses all    ", {"name": "edpb", "moves": [B1, M(0, 2, (400, 301), (450, 300))]}),
                  ("2334b contour 1 of 1              ", {"name": "edpb", "moves": [M(1, 0, (0, 0), (5, 5))]}),
                  ("2334c node 4 of 4                 ", {"name": "edpb", "moves": [M(0, 4, (0, 0), (5, 5))]}),
                  ("2334d from off by 0.002           ", {"name": "edpb", "moves": [M(0, 1, (400.002, 0), (450, 0))]}),
                  ("2334e from off by 0.0005: accepted", {"name": "edpb", "moves": [M(0, 1, (400.0005, 0), (450, 0))]})):
    mv_setup(); _mvh = mv(tag, body)
    if not tag.startswith("2334e"):
        print("2334h  v0.211 hint at the end, once:", _mvh.get("reason", "").endswith("Read the glyph again with get_glyph_outline.")
              and _mvh.get("reason", "").count("get_glyph_outline") == 1)
mv_setup(); P72["layers"]["edpb"].getContours()[0].rows[1]["y"] = -0.0
mv("2334f v0.154 a -0.0 prints as 0      ", {"name": "edpb", "moves": [M(0, 1, (401, 0), (450, 0))]}, keys=("moved", "reason"))
mv_setup()
for tag, g in (("2335a a Power Brush shape        ", "edpbrush"), ("2335b a component              ", "edpcomp"), ("2335c two shapes                ", "edptwo"),
               ("2335d no shape                   ", "edpnone"), ("2335e a glyph that does not exist", "edpzz")):
    mv_setup()     # v0.215: each case on fresh fakes (two shapes are moved now)
    mv(tag, {"name": g, "moves": [M(0, 0, (0, 0), (5, 5))]}, keys=("moved", "reason", "shapes", "found"))
for tag, mode in (("2335f isComposite raises         ", {"composite_raises": 1}), ("2335g the layer counts a component", {"components": 1}),
                  ("2335h layer.shapes is a tuple     ", {"shapes_tuple": 1}), ("2335i an element offset (dx 10)   ", {"tx": {"dx": 10.0}}),
                  ("2335j a scale (m11 2)             ", {"tx": {"m11": 2.0}}), ("2335k the transform raises        ", {"tx_raises": 1}),
                  ("2335l a transform value is text   ", {"tx": {"dy": "0"}}), ("2335m getNodeAt raises           ", {"node_raises": 1})):
    mv_setup(mode=mode); mv(tag, {"name": "edpb", "moves": [B1]}, keys=("moved", "reason"))
mv_setup(); _fm_cf = _fm.CurrentFont; _fm.CurrentFont = lambda: None
mv("2335n no font open               ", {"name": "edpb", "moves": [B1]}, keys=("open", "moved"))
_fm.CurrentFont = _fm_cf
# smooth nodes: contour On (0,0) | On smooth (200,0) | Curve (300,0) | Curve (400,100) | On (400,200) | On (0,200)
def mv_smooth(extra_smooth=()):
    mv_setup()
    rows = [P81Row(x=0.0, y=0.0, on=True, smooth=False), P81Row(x=200.0, y=0.0, on=True, smooth=True), P81Row(x=300.0, y=0.0, on=False, smooth=False),
            P81Row(x=400.0, y=100.0, on=False, smooth=False), P81Row(x=400.0, y=200.0, on=True, smooth=False), P81Row(x=0.0, y=200.0, on=True, smooth=False)]
    for k in extra_smooth: rows[k]["smooth"] = True
    ct = te_contour([(0, 0)]); ct.rows = rows
    P72["layers"]["edps"] = TELayer("test_font", [TEShape([ct])]); TS["edps"] = TsGlyph("edps", [TsLayer(1, 6)])
mv_smooth(); mv("2336a the smooth node alone, off its line", {"name": "edps", "moves": [M(0, 1, (200, 0), (200, 50))]}, keys=("moved", "reason", "problems"))
mv_smooth(); mv("2336b a handle, off the line        ", {"name": "edps", "moves": [M(0, 2, (300, 0), (300, 50))]}, keys=("moved", "reason"))
mv_smooth(); d = mv("2336c along its own line: accepted ", {"name": "edps", "moves": [M(0, 1, (200, 0), (250, 0))]}, keys=("moved", "nodes_match"))
mv_smooth(); d = mv("2336d with both neighbours       ", {"name": "edps", "moves": [M(0, 0, (0, 0), (0, 50)), M(0, 1, (200, 0), (200, 50)), M(0, 2, (300, 0), (300, 50))]}, keys=("moved", "nodes_match"))
print("2336e  after                       :", te_outline({"after": {"contours": d.get("after")}}, "after"))
mv_smooth(extra_smooth=(4,)); mv("2336f a smooth node already off its line", {"name": "edps", "moves": [M(0, 5, (0, 200), (0, 250))]}, keys=("moved", "nodes_match"))
mv_smooth(extra_smooth=(4,)); mv("2336g ... moved itself, still off ", {"name": "edps", "moves": [M(0, 4, (400, 200), (410, 200))]}, keys=("moved", "nodes_match"))
mv_smooth(); mv("2336h a smooth node made bad by its neighbour", {"name": "edps", "moves": [M(0, 0, (0, 0), (0, 50))]}, keys=("moved", "reason"))
for tag, mode, body in (("2337a node.x raises              ", {"set_raises": 1}, [B1]),
                        ("2337b node.x is ignored          ", {"move_ignored": 1}, [M(0, 1, (400, 0), (450, 10))]),
                        ("2337c moving sets smooth         ", {"move_smooth": 1}, [B1]),
                        ("2337d v0.154 resetInkBox never called", {"refresh_raises": 1}, [B1]),
                        ("2337e v0.154 no refresh: node 0 stays", {"refresh_moves": 1}, [M(0, 2, (400, 300), (420, 300))])):
    mv_setup(mode=mode); d = mv(tag, {"name": "edpa" if "refresh moves" in tag else "edpb", "moves": body})
    if not d.get("moved"):
        print("       before / expected / after  :", te_outline({"x": {"contours": d.get("before")}}, "x"), "|", te_outline({"x": {"contours": d.get("expected_after")}}, "x"), "|", te_outline({"x": {"contours": d.get("after")}}, "x"))
mv_setup(); _te_rk = TELayer.__dict__["resetInkBox"]; del TELayer.resetInkBox
d = mv("2337f v0.154 a layer without resetInkBox", {"name": "edpb", "moves": [B1]}, keys=("moved", "ink_box_refresh"))
TELayer.resetInkBox = _te_rk
TE_ALL_FORBIDDEN[:] = [f for f in TE_ALL_FORBIDDEN if f != "TELayer.resetInkBox"]     # expected in 2337f only: that case removed the member
mv_setup(); TS["edpb"] = TsGlyph("edpb", [TsLayer(1, 3)])
mv("2337g the legacy view lags: not synced", {"name": "edpb", "moves": [B1]}, keys=("moved", "synced_with_fontlab", "fontlab_changed_mark"))
_srcmv = "\n".join(l for l in src[src.index("# POST /glyph/move (v0.153)"):src.index("# POST /glyph/contours/add (v0.207)")].split("\n") if not l.lstrip().startswith("#"))
print("2338 spies over the move cases: forbidden members, subscripts, iterations:", TE_ALL_FORBIDDEN)
print("2338a static scan of move_nodes: forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeShape|removeAllShapes|clearContours|smartMove|smartSetXY|moveBy|decomposite|ejectTo|activateBuilder|resetMetrics\w*|applyTransform|replaceShape|addContour|removeContour)\s*\(|shapeBuilder|font\.update|getattr\(|resetInkBox", _srcmv),
      "| every check before the first node.x:", max(_srcmv.index(s) for s in ("problems.append", '_edit_case_check("move_nodes"', "_move_smooth_bad(", "getNodeAt(ni)")) < _srcmv.index("nd.x = float(tx)"))
print("2338b route documented:", "POST /glyph/move" in src, "| dispatched:", 'if path == "/glyph/move":' in src, "| mark title:", ns["_MARK_TITLES"].get("move_nodes"),
      "| guard kind full:", "move_nodes" in ns["_GUARD_FULL_KINDS"], "| activity kind:", ns["_ACT_WRITES"].get("/glyph/move"))
_ok_reply = {"open": True, "moved": True, "nodes_match": True, "synced_with_fontlab": True}
for tag, code, reply in (("2338c log, moved           ", 200, _ok_reply), ("2338d log, moved, not synced", 200, dict(_ok_reply, synced_with_fontlab=False)),
                         ("2338e log, refused         ", 200, {"open": True, "moved": False, "changed": False, "reason": "the request does not match the glyph"}),
                         ("2338f log, changed, not confirmed", 200, {"open": True, "moved": False, "changed": True, "reason": "the re-read outline does not match the request"}),
                         ("2338g log, outcome unknown ", 200, {"open": True, "moved": False, "changed": "unknown", "reason": "x"}),
                         ("2338h log, HTTP 400        ", 400, {"error": "move 0: to equals from"}), ("2338i log, no font open   ", 200, {"open": False})):
    print(tag, ":", ns["_act_describe_write"]("/glyph/move", {"name": "edpb", "moves": [B1, B1]}, code, reply))
print("2338j log, one node        :", ns["_act_describe_write"]("/glyph/move", {"name": "edpb", "moves": [B1]}, 200, _ok_reply))

# ================= v0.155: /debug/trycomponent (gated research probe for P2.7: ONE placement of a component per call) =================
print("\n==== v0.155 /debug/trycomponent ====")
# The /debug/tryedit fakes (TE spies, the one-font gate) with component-aware shapes. TCShape and TCShapeData are spies too; a component
# shape shares its source's contour objects, so layer.getContours() gives the source's nodes untransformed, as live 606 read them.
TC = {"calls": [], "mode": {}}
TC_FORBIDDEN = []
class TCQT:
    def __init__(s, *a):
        TC["calls"].append(("QTransform", a))
        if a and TC["mode"].get("qt_bad"): a = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        s._m = tuple(float(v) for v in a) if a else (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    def m11(s): return s._m[0]
    def m12(s): return s._m[1]
    def m21(s): return s._m[2]
    def m22(s): return s._m[3]
    def dx(s): return s._m[4]
    def dy(s): return s._m[5]
class TCShapeData(TESpy):
    def __init__(s, glyph="", refs=1, contours=None, owner=None): s._glyph = glyph; s._refs = refs; s._contours = contours; s._owner = owner
    def componentGlyph(s): return s._glyph
    def componentLayer(s): return "test_font" if s._glyph else ""
    def referenceCount(s): return s._refs
class TCShape(TESpy):
    def __init__(s, contours=None, component=None, composite=False):
        s._tx = TCQT(); s._composite = composite
        if isinstance(contours, TCShapeData):          # flShape(flShapeData), the second route
            sd = contours; TC["calls"].append("flShape(shapeData)"); sd._refs += 1
            s._contours = sd._contours; s._component = bool(TC["mode"].get("shapedata_component"))
            s.shapeData = TCShapeData(sd._owner, sd._refs, sd._contours) if s._component else sd
            return
        s._contours = list(contours or []); s._component = component is not None
        s.shapeData = TCShapeData(component or "", 1, s._contours)
    def isComponent(s): return s._component
    def isComposite(s): return s._composite
    @property
    def transform(s): return s._tx
    @transform.setter
    def transform(s, v):
        TC["calls"].append("shape.transform=")
        if not TC["mode"].get("tx_ignored"): s._tx = v
class TCGlyphComponent(TESpy):
    def __init__(s, name): TC["calls"].append(("GlyphComponent", name)); s._name = name; s._tx = TCQT()
    @property
    def transform(s): return s._tx
    @transform.setter
    def transform(s, v):
        TC["calls"].append("gc.transform=")
        if not TC["mode"].get("gc_tx_ignored"): s._tx = v
    @property
    def name_id(s): return 7
    @property
    def width_scale(s): return 1.0
    @property
    def use_anchors(s): return False
class TCLayer(TELayer):
    def __init__(s, name, shapes, glyph): TELayer.__init__(s, name, shapes); s._glyph = glyph
    def componentsCount(s): return sum(1 for sh in s._shapes if sh._component)
    def setGlyphComponents(s, comps, width, pkg, colorize, flags):
        TC["calls"].append(("setGlyphComponents", len(comps), width, type(pkg).__name__, colorize, flags))
        m = TC["mode"]
        if m.get("set_raises"): raise RuntimeError("setGlyphComponents boom")
        if m.get("set_noop"): return False
        new = []
        for gc in comps:
            sh = TCShape(TCSRC[gc._name]._contours, component=gc._name)
            sh._tx = TCQT() if m.get("set_drops_offset") else gc._tx
            new.append(sh)
        s._shapes = new if m.get("set_replaces") else s._shapes + new
        if m.get("set_width"): P72["widths"][s._glyph] = float(width) + 10.0
        if m.get("touch_source"): TCSRC[comps[0]._name]._contours[0].rows[0]["x"] += 1.0
        if m.get("glyph_added"): TS["cppnew"] = TsGlyph("cppnew", [])
        return True
    def addShape(s, shape):
        TC["calls"].append("addShape")
        if TC["mode"].get("add_raises"): raise RuntimeError("addShape boom")
        s._shapes.append(shape)
        return shape
TCSRC = {}
_tc_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("GlyphComponent",)]
def tc_setup(mode=None, count=1, packages=1, reset_calls=True, no_gc=False):
    te_setup(count=count, packages=packages)
    TC.update(calls=[], mode=dict(mode or {}))
    for _m in _tf_mods:
        _m.flShape = TCShape
        if no_gc:
            if hasattr(_m, "GlyphComponent"): delattr(_m, "GlyphComponent")
        else:
            _m.GlyphComponent = TCGlyphComponent
    qg.QTransform = None if TC["mode"].get("no_qt") else TCQT
    for g in ("cppsrc", "cppbase", "cppempty", "cppbrush", "cppcomp", "cpptwo", "cppbare"): TS[g] = TsGlyph(g, [TsLayer(1, 4)])
    TS["cppnolayer"] = TsGlyph("cppnolayer", [])
    src = TCShape([te_contour(TE_TRI)]); src.shapeData._owner = "cppsrc"
    TCSRC.clear(); TCSRC["cppsrc"] = src
    for g, shapes in (("cppsrc", [src]), ("cppbase", [TCShape([te_contour(TE_SQ)])]), ("cppempty", []),
                      ("cppbrush", [TCShape([te_contour(TE_SQ)], composite=True)]), ("cppcomp", [TCShape([te_contour(TE_TRI)], component="cppsrc")]),
                      ("cpptwo", [TCShape([te_contour(TE_SQ)]), TCShape([te_contour(TE_TRI)])]), ("cppbare", [TCShape([])])):
        P72["layers"][g] = TCLayer("test_font", shapes, g); P72["widths"][g] = 500.0
    if reset_calls: ns["_TRYCOMP"]["calls"] = 0
TCK = ("placed", "existing_kept", "source_contours_in_outline", "component_placed", "changed", "side_effect_detected", "width_changed",
       "source_changed", "error", "calls_so_far")
def tc(tag, path, keys=("error", "calls_so_far")):
    c, d = call(path)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform" and not x[1])],
          "| Update", TE["updates"], "| marks", TE["marks"])
    return d
def tc_elements(d, key):
    els = d.get(key)
    if not isinstance(els, list): return els
    return [(e.get("is_component"), e.get("is_composite"), e.get("component_glyph"), e.get("reference_count"),
             None if "error" in (e.get("matrix") or {}) else tuple(e["matrix"][k] for k in ("m11", "m12", "m21", "m22", "dx", "dy"))) for e in els]
QC = "/debug/trycomponent?"
GC = QC + "stage=glyphcomponents&target=cppempty&source=cppsrc&dx=100&dy=200"
tc_setup()
tc("2340a glyphcomponents without go    ", GC)
tc("2340b go must be exactly yes        ", GC + "&go=Yes")
tc("2340c unknown stage                 ", QC + "stage=addcomponent&target=cppempty&source=cppsrc&dx=0&dy=0&go=yes")
tc("2340d target without the prefix     ", QC + "stage=glyphcomponents&target=fresh&source=cppsrc&dx=0&dy=0&go=yes")
tc("2340e source without the prefix     ", QC + "stage=glyphcomponents&target=cppempty&source=A&dx=0&dy=0&go=yes")
tc("2340f target and source the same    ", QC + "stage=glyphcomponents&target=cppsrc&source=cppsrc&dx=0&dy=0&go=yes")
tc("2340g dx missing                    ", QC + "stage=glyphcomponents&target=cppempty&source=cppsrc&dy=0&go=yes")
tc("2340h dx 1001                       ", QC + "stage=glyphcomponents&target=cppempty&source=cppsrc&dx=1001&dy=0&go=yes")
tc("2340i dy is text                    ", QC + "stage=glyphcomponents&target=cppempty&source=cppsrc&dx=0&dy=ten&go=yes")
tc("2340j shapedata without go          ", QC + "stage=shapedata&target=cppempty&source=cppsrc&dx=-5&dy=0")
for tag, over in (("2340k two fonts open                ", dict(count=2)), ("2340l two packages                 ", dict(packages=2)),
                  ("2340m CountFonts raises            ", dict(count=RuntimeError("count boom"))), ("2340n no font open                 ", dict(count=0))):
    tc_setup(**over); tc(tag, GC + "&go=yes")
tc_setup(no_gc=True); tc("2340o no GlyphComponent: not counted", GC + "&go=yes")
tc_setup(mode={"no_qt": 1}); _fq = [(m, getattr(m, "QTransform", None)) for m in _tf_mods]
for _m in _tf_mods:
    if hasattr(_m, "QTransform"): delattr(_m, "QTransform")
tc("2340p no QTransform: not counted    ", GC + "&go=yes")
for _m, _v in _fq:
    if _v is not None: setattr(_m, "QTransform", _v)
tc_setup()
d = tc("2341 glyphcomponents into an empty glyph", GC + "&go=yes", keys=TCK)
print("2341a  elements before / after   :", tc_elements(d, "target_elements_before"), "/", tc_elements(d, "target_elements_after"))
print("2341b  outline after            :", te_outline(d, "target_after"), "| counts", {k: d.get("target_state_after", {}).get(k) for k in ("shapes", "nodes", "components")})
print("2341c  source refs before/after :", tc_elements(d, "source_elements_before")[0][3], tc_elements(d, "source_elements_after")[0][3],
      "| built", d.get("built_matrix"), "| detached", d.get("detached_matrix"), "| name_id", d.get("glyph_component_name_id"), "| returned", d.get("call_returned"))
print("2341d  call, widths, counts, sync, mark:", d.get("call"), d.get("advance_width_before"), d.get("advance_width_after"), d.get("glyph_count_before"),
      d.get("glyph_count_after"), "| synced", d.get("synced_with_fontlab"), "| mark", d.get("fontlab_changed_mark"), "| repainted", d.get("display_refreshed"), "| qt", d.get("qtransform"))
tc_setup(); TS["cppempty"] = TsGlyph("cppempty", [TsLayer(1, 3)])
d = tc("2341e the legacy view agrees: synced, marked", GC + "&go=yes", keys=("component_placed", "synced_with_fontlab", "fontlab_changed_mark"))
tc_setup()
d = tc("2342 glyphcomponents beside a contour", QC + "stage=glyphcomponents&target=cppbase&source=cppsrc&dx=-30&dy=0&go=yes", keys=TCK)
print("2342a  outline after            :", te_outline(d, "target_after"), "| elements after", tc_elements(d, "target_elements_after"))
tc_setup(mode={"set_replaces": 1})
d = tc("2343 the call replaces the contour", QC + "stage=glyphcomponents&target=cppbase&source=cppsrc&dx=-30&dy=0&go=yes", keys=TCK)
print("2343a  mark                     :", d.get("fontlab_changed_mark"))
tc_setup()
d = tc("2344 shapedata: a shared plain shape", QC + "stage=shapedata&target=cppempty&source=cppsrc&dx=100&dy=200&go=yes", keys=TCK)
print("2344a  elements after / source  :", tc_elements(d, "target_elements_after"), "/", tc_elements(d, "source_elements_after"), "| mark", d.get("fontlab_changed_mark"))
tc_setup(mode={"shapedata_component": 1})
d = tc("2345 shapedata: a component      ", QC + "stage=shapedata&target=cppbase&source=cppsrc&dx=100&dy=200&go=yes", keys=TCK)
print("2345a  elements after           :", tc_elements(d, "target_elements_after"), "| detached", d.get("detached_matrix"))
tc_setup()
for tag, tgt, srcn in (("2346a target with a Power Brush shape", "cppbrush", "cppsrc"), ("2346b target with a component      ", "cppcomp", "cppsrc"),
                       ("2346c target with two shapes        ", "cpptwo", "cppsrc"), ("2346d target with no layer         ", "cppnolayer", "cppsrc"),
                       ("2346e target that does not exist    ", "cppzz", "cppsrc"), ("2346f source with two shapes        ", "cppempty", "cpptwo"),
                       ("2346g source is a component         ", "cppempty", "cppcomp"), ("2346h source is a Power Brush shape  ", "cppempty", "cppbrush"),
                       ("2346i source with no nodes          ", "cppempty", "cppbare"), ("2346j source with no shape          ", "cppbase", "cppempty"),
                       ("2346k source that does not exist    ", "cppempty", "cppzz")):
    tc_setup(); d = tc(tag, QC + f"stage=glyphcomponents&target={tgt}&source={srcn}&dx=10&dy=10&go=yes")
print("2346l  a refusal reads nothing after it:", "target_after" in d, "| no call made:", [x for x in TC["calls"] if x in ("addShape", "gc.transform=") or (isinstance(x, tuple) and x[0] == "setGlyphComponents")])
for tag, mode, path in (("2347a the QTransform reads wrong     ", {"qt_bad": 1}, GC + "&go=yes"),
                        ("2347b gc.transform is ignored       ", {"gc_tx_ignored": 1}, GC + "&go=yes"),
                        ("2347c setGlyphComponents raises     ", {"set_raises": 1}, GC + "&go=yes"),
                        ("2347d setGlyphComponents does nothing", {"set_noop": 1}, GC + "&go=yes"),
                        ("2347e the offset is dropped         ", {"set_drops_offset": 1}, GC + "&go=yes"),
                        ("2347f the advance width changes     ", {"set_width": 1}, GC + "&go=yes"),
                        ("2347g the source changes            ", {"touch_source": 1}, GC + "&go=yes"),
                        ("2347h a glyph appears               ", {"glyph_added": 1}, GC + "&go=yes"),
                        ("2347i shape.transform is ignored    ", {"tx_ignored": 1}, QC + "stage=shapedata&target=cppempty&source=cppsrc&dx=1&dy=1&go=yes"),
                        ("2347j addShape raises               ", {"add_raises": 1}, QC + "stage=shapedata&target=cppempty&source=cppsrc&dx=1&dy=1&go=yes")):
    tc_setup(mode=mode); d = tc(tag, path, keys=TCK)
    if "fontlab_changed_mark" in d: print("      mark:", d["fontlab_changed_mark"])
tc_setup()
for _i in range(6): call(GC + "&go=yes")
tc("2348 the limit: call 7 is refused   ", GC + "&go=yes")
_src155 = "\n".join(l for l in src[src.index("# /debug/trycomponent (v0.155)"):src.index("# /debug/tryshape (v0.52)")].split("\n") if not l.lstrip().startswith("#"))
print("2349 spies over all cases: forbidden members, subscripts, iterations:", TC_FORBIDDEN)
print("2349a static scan of the probe (code lines):", len(_src155) > 6000, "| forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeShape|removeAllShapes|replaceShape|addComponent|clearComponents|decomposite|mergeTopComposite|ejectTo|findLayerCreate)\s*\(|font\.update|_ensure_modern_layer|create_layer=True", _src155),
      "| counter raised before either glyph is read:", (lambda f: f.rindex('_TRYCOMP["calls"] += 1') < f.index("_modern_edit_target(source)") < f.index("_modern_edit_target(target)"))(
          _src155[_src155.index("def debug_try_component("):]),
      "| one call per request:", _src155.count("= layer.setGlyphComponents("), _src155.count("= layer.addShape("))
print("2349b route documented:", "/debug/trycomponent   stage=glyphcomponents|shapedata" in src, "| dispatched:", 'if path == "/debug/trycomponent":' in src,
      "| mark title:", ns["_MARK_TITLES"].get("trycomponent"), "| guard kind full:", "trycomponent" in ns["_GUARD_FULL_KINDS"])

# ---- v0.156: stage=readcomponents, ONE read of layer.components on a glyph that holds a component. TCLayer.components answers by mode.
print("\n==== v0.156 /debug/trycomponent stage=readcomponents ====")
class TCNative(TESpy):
    pass
def _tc_components(s):
    m = TC["mode"]
    TC["calls"].append("layer.components")
    if m.get("comps_raises"): raise RuntimeError("components boom")
    if m.get("comps_native"): return TCNative()
    comps = [sh for sh in s._shapes if sh._component]
    if m.get("comps_gc"):
        items = []
        for sh in comps:
            gc = TCGlyphComponent(sh.shapeData._glyph); gc._tx = sh._tx; items.append(gc)
    elif m.get("comps_odd"):
        items = [object(), ("cppsrc",), ["cppsrc", TCQT(1, 0, 0, 1, 5, 6), 3]]
    else:
        items = [(sh.shapeData._glyph, sh._tx) for sh in comps]
    if m.get("comps_many"): items = items * 25
    if m.get("comps_callable"): return lambda: items
    return tuple(items) if m.get("comps_tuple") else items
TCLayer.components = property(_tc_components)
def tc_comp_setup(mode=None, **kw):
    tc_setup(mode=mode, **kw)
    sh = TCShape([te_contour(TE_TRI)], component="cppsrc"); sh._tx = TCQT(1, 0, 0, 1, 100, 200)
    P72["layers"]["cppcomp"] = TCLayer("test_font", [sh], "cppcomp")
RCK = ("components_type", "components_len", "components", "components_called", "components_note", "components_error",
       "components_truncated", "side_effect_detected", "error", "calls_so_far")
RC = QC + "stage=readcomponents&target=cppcomp"
tc_comp_setup()
tc("2350a readcomponents without go (no source, no offset)", RC)
tc("2350b target without the prefix     ", QC + "stage=readcomponents&target=src&go=yes")
tc_comp_setup(count=2); tc("2350c two fonts open                ", RC + "&go=yes")
tc_comp_setup()
d = tc("2351 a list of (name, transform) pairs", RC + "&go=yes", keys=RCK)
print("2351a  elements, state          :", tc_elements(d, "target_elements"), [e.get("shape_data_type") for e in d.get("target_elements") or []],
      {k: d.get("target_state", {}).get(k) for k in ("shapes", "nodes", "components")}, "| glyph count", d.get("glyph_count"), "| Update / marks", TE["updates"], TE["marks"])
for tag, mode in (("2352a a tuple                       ", {"comps_tuple": 1}), ("2352b GlyphComponent items         ", {"comps_gc": 1}),
                  ("2352c a callable                    ", {"comps_callable": 1}), ("2352d a native object: not iterated", {"comps_native": 1}),
                  ("2352e the read raises             ", {"comps_raises": 1}), ("2352f 25 items: 20 described      ", {"comps_many": 1}),
                  ("2352g other item kinds            ", {"comps_odd": 1})):
    tc_comp_setup(mode=mode); d = tc(tag, RC + "&go=yes", keys=tuple(k for k in RCK if not (mode.get("comps_many") and k == "components")))
    if mode.get("comps_many"): print("      described:", len(d.get("components") or []), "| all the same as the first:", all(c == d["components"][0] for c in d["components"]))
tc_comp_setup()
tc("2353a a plain glyph reads an empty list", QC + "stage=readcomponents&target=cppbase&go=yes", keys=RCK)
tc("2353b a glyph with no layer          ", QC + "stage=readcomponents&target=cppnolayer&go=yes", keys=RCK)
tc_comp_setup()
for _i in range(6): call(RC + "&go=yes")
tc("2354 the limit: call 7 is refused   ", RC + "&go=yes")
_src156 = "\n".join(l for l in src[src.index("def _trycomp_is("):src.index("def _trycomp_name_ok(")].split("\n") if not l.lstrip().startswith("#"))
print("2355 spies over the read cases:", TC_FORBIDDEN, "| static scan of the read stage:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|addComponent|clearComponents|removeShape|replaceShape)\s*\(|_guard_mark|_mark_font_changed|for \w+ in comps\s*:|comps\[\d", _src156),
      "| counter before the read:", src.index('if reading:\n        _TRYCOMP["calls"] += 1') < src.index("return _trycomp_read_components("),
      "| route documented:", "stage=readcomponents&target=cpp...: read only" in src)

# ---- v0.157: stage=generate / setgenerated. TOPkg.generateGlyph and fontlab.FontMetrics are fakes; generateGlyph answers by mode.
print("\n==== v0.157 /debug/trycomponent stage=generate / setgenerated ====")
class TCNativeList(TESpy):
    def __init__(s, items): s._items = items
class TCMetrics(TESpy):
    def __init__(s, pkg, layer_name):
        TC["calls"].append(("FontMetrics", type(pkg).__name__, layer_name))
        if TC["mode"].get("metrics_raises"): raise TypeError("FontMetrics boom")
def _tc_generate(self, recipe, layer_name, metrics, rtl):
    m = TC["mode"]
    TC["calls"].append(("generateGlyph", recipe, layer_name, type(metrics).__name__, rtl))
    if m.get("gen_raises"): raise RuntimeError("generateGlyph boom")
    if m.get("gen_none"): return None
    if m.get("gen_adds_glyph"): TS["cppnew"] = TsGlyph("cppnew", [])
    if m.get("gen_changes_target"): P72["layers"]["cpp1"]._shapes.append(TCShape([te_contour(TE_SQ)]))
    if m.get("gen_empty"): return ([], 0.0)
    items = [TCGlyphComponent(p) for p in recipe.split("+")]
    if m.get("gen_offset"): items[0]._tx = TCQT(1, 0, 0, 1, 40, 0)
    width = "wide" if m.get("gen_bad_width") else 300.0
    if m.get("gen_native"): return (TCNativeList(items), width)
    if m.get("gen_three"): return (items, width, 1)
    if m.get("gen_one_gc"): return [items[0]]                 # v0.158 cases: live 1030 returned a list of one item
    if m.get("gen_one_pair"): return [(items, width)]
    if m.get("gen_one_native"): return [TCNative()]
    if m.get("gen_list"): return items                        # v0.159 cases: live 1032 returned a list of GlyphComponent, no width
    if m.get("gen_list_mixed"): return items + [object()]
    return (items, width)
_tc_set_orig = TCLayer.setGlyphComponents
def _tc_set(s, comps, width, *rest):
    TC.setdefault("argcounts", []).append(2 + len(rest))         # v0.160: args=N; "need_args" rejects every other count as live 1026
    need = TC["mode"].get("need_args")
    if need is not None and 2 + len(rest) != need: raise IndexError("Unexpected SeqBase<T> length.")
    if TC["mode"].get("third_int") and (not rest or type(rest[0]) is not int): raise TypeError("argument type must be Int!")   # v0.161, as 1033
    if TC["mode"].get("fontlab_like"):     # v0.163: answers as live 1031, 1033, 1034 and 1035, checked in this order
        if 2 + len(rest) != 4: raise IndexError("Unexpected SeqBase<T> length.")
        if not isinstance(rest[0], TOPkg): raise TypeError("Wrong argument type. flPackage expected.")
        if type(rest[1]) is not bool: raise TypeError("argument type must be Boolean!")
        if TC["mode"].get("width_must_be_int") and type(width) is not int: raise TypeError("argument type must be Int!")
        if TC["mode"].get("items_must_be_int") and any(type(x) is not int for x in (comps._items if isinstance(comps, TCNativeList) else comps)):
            raise TypeError("argument type must be Int!")      # v0.164: one reading of live 1036 (whole width, GlyphComponent items)
    if type(comps) is list and comps and all(type(x) is int for x in comps):
        comps = [TCGlyphComponent("cppsrc") for _ in comps]    # v0.164: the fake turns name_ids back into components of cppsrc
    pkg, colorize, flags = (list(rest) + [None, False, 0][len(rest):])[:3]
    if isinstance(comps, TCNativeList): comps = comps._items
    r = _tc_set_orig(s, comps, width, pkg, colorize, flags)
    if TC["mode"].get("set_applies_width"): P72["widths"][s._glyph] = float(width)
    return r
TCLayer.setGlyphComponents = _tc_set
_tc_gen_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("FontMetrics",)]
def tc_gen_setup(mode=None, **kw):
    tc_setup(mode=mode, **kw)
    TOPkg.generateGlyph = _tc_generate
    for _m in _tf_mods:
        if TC["mode"].get("no_metrics"):
            if hasattr(_m, "FontMetrics"): delattr(_m, "FontMetrics")
        else:
            _m.FontMetrics = TCMetrics
    src2 = TCShape([te_contour(TE_SQ)]); src2.shapeData._owner = "cppsrc2"; TCSRC["cppsrc2"] = src2
    TS["cppsrc2"] = TsGlyph("cppsrc2", [TsLayer(1, 4)]); P72["layers"]["cppsrc2"] = TCLayer("test_font", [src2], "cppsrc2")
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); P72["layers"]["cpp1"] = TCLayer("test_font", [], "cpp1"); P72["widths"]["cpp1"] = 0.0
GK = ("generate_returned_type", "generated_width", "generated_list_type", "generated_len", "generated", "generated_note", "generate_returned",
      "call_returned", "placed", "existing_kept", "component_placed", "changed", "width_changed", "source_changed", "side_effect_detected",
      "error", "calls_so_far")
QG = QC + "stage=generate&target=cpp1&recipe=cppsrc"
QS = QC + "stage=setgenerated&target=cpp1&recipe=cppsrc"
tc_gen_setup()
tc("2360a generate without go          ", QG)
tc("2360b setgenerated without go      ", QS)
tc("2360c no recipe                    ", QC + "stage=generate&target=cpp1&go=yes")
tc("2360d recipe with @                ", QC + "stage=generate&target=cpp1&recipe=cppsrc@top&go=yes")
tc("2360e recipe of three glyphs       ", QC + "stage=generate&target=cpp1&recipe=cppsrc%2Bcppsrc2%2Bcppbase&go=yes")
tc("2360f recipe glyph without the prefix", QC + "stage=generate&target=cpp1&recipe=A&go=yes")
tc("2360g recipe names the target      ", QC + "stage=generate&target=cpp1&recipe=cppsrc%2Bcpp1&go=yes")
tc("2360k a plain + arrives as a space ", QC + "stage=generate&target=cpp1&recipe=cppsrc+cppsrc2&go=yes")
tc("2360h empty part (cppsrc+)         ", QC + "stage=generate&target=cpp1&recipe=cppsrc%2B&go=yes")
tc_gen_setup(count=2); tc("2360i two fonts open                ", QG + "&go=yes")
tc_gen_setup(mode={"no_metrics": 1}); tc("2360j no FontMetrics: not counted ", QG + "&go=yes")
tc_gen_setup()
d = tc("2361 generate                       ", QG + "&go=yes", keys=GK)
print("2361a  target before / after   :", tc_elements(d, "target_elements_before"), tc_elements(d, "target_elements_after"), "| layer", d.get("layer_name"),
      "| widths", d.get("advance_width_before"), d.get("advance_width_after"), "| glyphs", d.get("glyph_count_before"), d.get("glyph_count_after"))
tc_gen_setup()
d = tc("2362 setgenerated                   ", QS + "&go=yes", keys=GK)
print("2362a  elements after / outline :", tc_elements(d, "target_elements_after"), te_outline(d, "target_after"), "| sync", d.get("synced_with_fontlab"),
      "| mark", d.get("fontlab_changed_mark"))
tc_gen_setup(mode={"set_applies_width": 1}); TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 300.0
d = tc("2363 setgenerated takes the returned width", QS + "&go=yes", keys=GK); print("      widths:", d.get("advance_width_before"), d.get("advance_width_after"), "| mark", d.get("fontlab_changed_mark"))
tc_gen_setup()
d = tc("2364 two-glyph recipe beside a contour", QC + "stage=setgenerated&target=cppbase&recipe=cppsrc%2Bcppsrc2&go=yes", keys=GK)
print("2364a  elements after           :", tc_elements(d, "target_elements_after"))
for tag, mode, path in (("2365a FontMetrics raises           ", {"metrics_raises": 1}, QS),
                        ("2365b generateGlyph raises         ", {"gen_raises": 1}, QS),
                        ("2365c generateGlyph returns None   ", {"gen_none": 1}, QS),
                        ("2365d an empty list                ", {"gen_empty": 1}, QS),
                        ("2365e a native list, generate      ", {"gen_native": 1}, QG),
                        ("2365f a native list, setgenerated  ", {"gen_native": 1}, QS),
                        ("2365g a width that is not a number ", {"gen_bad_width": 1}, QS),
                        ("2365h three items returned         ", {"gen_three": 1}, QS),
                        ("2365i generate adds a glyph        ", {"gen_adds_glyph": 1}, QG),
                        ("2365j generate changes the target  ", {"gen_changes_target": 1}, QG),
                        ("2365k an offset in the result      ", {"gen_offset": 1}, QS),
                        ("2365l the call replaces the contour", {"set_replaces": 1}, QC + "stage=setgenerated&target=cppbase&recipe=cppsrc&go=yes"),
                        ("2365m setGlyphComponents raises    ", {"set_raises": 1}, QS),
                        ("2365n the width moves elsewhere    ", {"set_width": 1}, QS)):
    tc_gen_setup(mode=mode); d = tc(tag, path if path.endswith("go=yes") else path + "&go=yes", keys=GK)
    if "fontlab_changed_mark" in d: print("      mark:", d["fontlab_changed_mark"])
tc_gen_setup()
for tag, tgt in (("2366a setgenerated: target with a component", "cppcomp"), ("2366b setgenerated: target with two shapes", "cpptwo"),
                 ("2366c target with no layer          ", "cppnolayer")):
    tc(tag, QC + f"stage=setgenerated&target={tgt}&recipe=cppsrc&go=yes")
tc("2366d generate on a target with a component (read only)", QC + "stage=generate&target=cppcomp&recipe=cppsrc&go=yes", keys=("side_effect_detected", "error"))
tc("2366e a recipe glyph that does not exist", QC + "stage=generate&target=cpp1&recipe=cppzz&go=yes")
tc_gen_setup()
for _i in range(6): call(QG + "&go=yes")
tc("2367 the limit: call 7 is refused   ", QG + "&go=yes")
_src157 = "\n".join(l for l in src[src.index("def _trycomp_recipe("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2368 spies over the generate cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|addComponent|clearComponents|removeShape|replaceShape|addShape|addGlyph|deleteGlyph|replaceGlyph|replaceShapeWithReference)\s*\(|font\.update|for \w+ in comps\s*:", _src157),
      "| one call each:", _src157.count("= pkg.generateGlyph("), _src157.count("= layer.setGlyphComponents("),
      "| counter before any read:", src.index('_TRYCOMP["calls"] += 1     # counted BEFORE any glyph is read') < src.index("return _trycomp_generate("),
      "| route documented:", "stage=generate|setgenerated&target=cpp...&recipe=cpp...[+cpp...]" in src, "| dispatched with recipe:", '(query.get("recipe") or [None])[0]' in src)
print("\n==== v0.158 generateGlyph returns something other than a pair ====")
GK8 = ("generate_returned_type", "generate_returned", "generate_returned_items", "call_returned", "changed", "side_effect_detected", "error", "calls_so_far")
for tag, mode in (("2370a a list of one GlyphComponent ", {"gen_one_gc": 1}), ("2370b a list of one (list, width)  ", {"gen_one_pair": 1}),
                  ("2370c a list of one native object  ", {"gen_one_native": 1})):
    tc_gen_setup(mode=mode); tc(tag + ", generate    ", QG + "&go=yes", keys=GK8)
    tc_gen_setup(mode=mode); tc(tag + ", setgenerated", QS + "&go=yes", keys=GK8)
tc_gen_setup(mode={"gen_three": 1}); tc("2370d a tuple of three: items described", QG + "&go=yes", keys=GK8)
print("2370e spies over the cases:", TC_FORBIDDEN)
print("\n==== v0.159 setgenerated with a list of GlyphComponent (the form of live 1032) ====")
GK9 = ("width_source", "call_returned", "placed", "existing_kept", "component_placed", "changed", "width_changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1}); TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 250.0; P72["widths"]["cpp1"] = 250.0
d = tc("2371a the 1032 form, setgenerated    ", QS + "&go=yes", keys=GK9)
print("2371b  width passed, elements after, mark:", [c[2] for c in TC["calls"] if isinstance(c, tuple) and c[0] == "setGlyphComponents"],
      tc_elements(d, "target_elements_after"), d.get("fontlab_changed_mark"))
tc_gen_setup(mode={"gen_list": 1}); tc("2371c the 1032 form, generate: nothing called", QG + "&go=yes", keys=GK9)
tc_gen_setup(mode={"gen_list_mixed": 1}); tc("2371d a list with a non-GlyphComponent item", QS + "&go=yes", keys=GK9)
tc_gen_setup(mode={"gen_list": 1})
d = tc("2371e two glyphs, two GlyphComponent: not a pair", QC + "stage=setgenerated&target=cpp1&recipe=cppsrc%2Bcppsrc2&go=yes", keys=GK9)
print("2371f  elements after           :", tc_elements(d, "target_elements_after"))
tc_gen_setup(mode={"gen_list": 1}); P72["widths"]["cpp1"] = "x"
tc("2371g the target's width unreadable", QS + "&go=yes", keys=GK9)
print("2371h spies over the cases:", TC_FORBIDDEN)
print("\n==== v0.160 setgenerated&args=N ====")
GK10 = ("args", "call_made", "call_returned", "placed", "component_placed", "changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1})
for tag, q in (("2372a args=1                       ", "&args=1"), ("2372b args=6                       ", "&args=6"), ("2372c args=two                     ", "&args=two")):
    tc(tag, QS + q + "&go=yes", keys=GK10)
tc("2372d args with stage=generate     ", QG + "&args=3&go=yes", keys=GK10)
tc("2372e args shown before go          ", QS + "&args=3", keys=GK10)
for n in (2, 3, 4, 5):
    tc_gen_setup(mode={"gen_list": 1, "need_args": 3}); TC["argcounts"] = []
    d = tc(f"2373 args={n}, the fake takes only 3", QS + f"&args={n}&go=yes", keys=GK10)
    print("      counts passed:", TC["argcounts"], "| mark", d.get("fontlab_changed_mark"))
tc_gen_setup(mode={"gen_list": 1}); TC["argcounts"] = []
d = tc("2374 no args: five, as 1026 and 1031", QS + "&go=yes", keys=GK10); print("      counts passed:", TC["argcounts"])
print("2375 spies over the cases:", TC_FORBIDDEN, "| route documented:", "setgenerated&args=2..5" in src, "| dispatched:", '(query.get("args") or [None])[0]' in src)
print("\n==== v0.161 setgenerated&pkg=id ====")
GK11 = ("args", "pkg", "package_fgid", "call_made", "call_returned", "placed", "component_placed", "changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1})
tc("2376a pkg=yes                       ", QS + "&args=4&pkg=yes&go=yes", keys=GK11)
tc("2376b pkg=id with stage=generate   ", QG + "&pkg=id&go=yes", keys=GK11)
tc("2376c pkg=id shown before go        ", QS + "&args=4&pkg=id", keys=GK11)
for tag, mode, fgid in (("2377a args=4, pkg=id, the fake wants an Int third", {"gen_list": 1, "need_args": 4, "third_int": 1}, 77),
                        ("2377b args=4 without pkg=id: the 1033 error      ", {"gen_list": 1, "need_args": 4, "third_int": 1}, 77),
                        ("2377c fgId is text: refused before the call      ", {"gen_list": 1, "need_args": 4, "third_int": 1}, "77"),
                        ("2377d fgId is a bool: refused                    ", {"gen_list": 1, "need_args": 4, "third_int": 1}, True),
                        ("2377e fgId above a uint: refused                 ", {"gen_list": 1, "need_args": 4, "third_int": 1}, 4294967296)):
    tc_gen_setup(mode=mode); TOPkg.fgId = fgid
    d = tc(tag, QS + ("&args=4&go=yes" if "without" in tag else "&args=4&pkg=id&go=yes"), keys=GK11)
    print("      mark:", d.get("fontlab_changed_mark"))
tc_gen_setup(mode={"gen_list": 1}); TOPkg.fgId = 77
tc("2377f pkg=id with all five arguments", QS + "&pkg=id&go=yes", keys=GK11)
if "fgId" in TOPkg.__dict__: del TOPkg.fgId
tc_gen_setup(mode={"gen_list": 1}); tc("2377g the package has no fgId     ", QS + "&args=4&pkg=id&go=yes", keys=GK11)
print("2378 spies over the cases:", TC_FORBIDDEN, "| route documented:", "&pkg=id: the package's" in src, "| dispatched:", '(query.get("pkg") or [None])[0]' in src)
print("\n==== v0.162 setgenerated&int=yes ====")
GK12 = ("args", "pkg", "int", "call_made", "call_returned", "placed", "component_placed", "changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1})
tc("2380a int=true                      ", QS + "&args=4&int=true&go=yes", keys=GK12)
tc("2380b int=yes with stage=generate  ", QG + "&int=yes&go=yes", keys=GK12)
tc("2380c int=yes shown before go       ", QS + "&args=4&int=yes", keys=GK12)
TOPkg.fgId = 5
for tag, q in (("2381a as 1031: five arguments         ", ""), ("2381b as 1033: four, False fourth    ", "&args=4"),
               ("2381c as 1034: four, fgId third       ", "&args=4&pkg=id"), ("2381d four, 0 fourth (test 1035)     ", "&args=4&int=yes"),
               ("2381e five, 0 fourth                 ", "&int=yes"), ("2381f four, fgId third, 0 fourth   ", "&args=4&pkg=id&int=yes")):
    tc_gen_setup(mode={"gen_list": 1, "fontlab_like": 1, "width_must_be_int": 1}); TOPkg.fgId = 5
    d = tc(tag, QS + q + "&go=yes", keys=GK12)
    print("      mark:", d.get("fontlab_changed_mark"))
if "fgId" in TOPkg.__dict__: del TOPkg.fgId
print("2382 spies over the cases:", TC_FORBIDDEN, "| route documented:", "&int=yes: 0 in place of False" in src, "| dispatched:", '(query.get("int") or [None])[0]' in src)
print("\n==== v0.163 setgenerated&width=int ====")
GK13 = ("args", "pkg", "int", "width", "call_made", "call_returned", "placed", "component_placed", "changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1})
tc("2383a width=round                   ", QS + "&args=4&width=round&go=yes", keys=GK13)
tc("2383b width=int with stage=generate", QG + "&width=int&go=yes", keys=GK13)
tc("2383c width=int shown before go     ", QS + "&args=4&width=int", keys=GK13)
for tag, q, w in (("2384a as 1035: 0 fourth                ", "&args=4&int=yes", 0.0), ("2384b four, whole-number width (1036)  ", "&args=4&width=int", 0.0),
                  ("2384c the same, width 500              ", "&args=4&width=int", 500.0), ("2384d a width of 500.5: refused        ", "&args=4&width=int", 500.5),
                  ("2384e whole width and 0 fourth          ", "&args=4&width=int&int=yes", 0.0)):
    tc_gen_setup(mode={"gen_list": 1, "fontlab_like": 1, "width_must_be_int": 1}); P72["widths"]["cpp1"] = w
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = w
    d = tc(tag, QS + q + "&go=yes", keys=GK13)
    print("      mark:", d.get("fontlab_changed_mark"))
print("2385 spies over the cases:", TC_FORBIDDEN, "| route documented:", "&width=int: the" in src, "| dispatched:", '(query.get("width") or [None])[0]' in src)
print("\n==== v0.164 setgenerated&items=id ====")
GK14 = ("args", "items", "items_passed", "call_made", "call_returned", "placed", "component_placed", "changed", "side_effect_detected", "error", "calls_so_far")
tc_gen_setup(mode={"gen_list": 1})
tc("2386a items=name                    ", QS + "&args=4&items=name&go=yes", keys=GK14)
tc("2386b items=id with stage=generate ", QG + "&items=id&go=yes", keys=GK14)
tc("2386c items=id shown before go      ", QS + "&args=4&items=id", keys=GK14)
FL164 = {"gen_list": 1, "fontlab_like": 1, "items_must_be_int": 1}     # the reading of live 1036 tested next: the items must be whole numbers
for tag, q in (("2387a as 1033: GlyphComponent items    ", "&args=4"), ("2387b as 1036: whole width too          ", "&args=4&width=int"),
               ("2387c name_id items (test 1037)        ", "&args=4&items=id"), ("2387d name_id items, whole width       ", "&args=4&items=id&width=int")):
    tc_gen_setup(mode=FL164)
    d = tc(tag, QS + q + "&go=yes", keys=GK14)
    print("      mark:", d.get("fontlab_changed_mark"))
for tag, mode in (("2388a items=id on the pair form (native list): refused", {"gen_native": 1}),
                  ("2388b items=id on a real pair list: name_ids passed   ", {})):
    tc_gen_setup(mode=mode); tc(tag, QS + "&args=4&items=id&go=yes", keys=GK14)
_tc_gc_nid = TCGlyphComponent.name_id
TCGlyphComponent.name_id = property(lambda s: "seven")
tc_gen_setup(mode={"gen_list": 1}); tc("2388c a name_id that is text: refused", QS + "&args=4&items=id&go=yes", keys=GK14)
TCGlyphComponent.name_id = _tc_gc_nid
print("2389 spies over the cases:", TC_FORBIDDEN, "| route documented:", "&items=id: each component's name_id" in src, "| dispatched:", '(query.get("items") or [None])[0]' in src)

# ---- v0.165: stage=auto. TCLayer gets recipe / autoLayer (stored per layer) and buildAuto(), which answer by TC["mode"].
print("\n==== v0.165 /debug/trycomponent stage=auto ====")
def _tc_get_recipe(s):
    if TC["mode"].get("recipe_unreadable"): raise RuntimeError("recipe boom")
    return s.__dict__.get("_recipe", "")
def _tc_set_recipe(s, v):
    TC["calls"].append(("recipe=", v))
    if not TC["mode"].get("recipe_ignored"): s.__dict__["_recipe"] = v
    if TC["mode"].get("recipe_sets_auto"): s.__dict__["_auto"] = True
def _tc_get_auto(s): return s.__dict__.get("_auto", False)
def _tc_set_auto(s, v):
    TC["calls"].append(("autoLayer=", v))
    if not TC["mode"].get("auto_ignored") and not (v is False and TC["mode"].get("auto_off_ignored")): s.__dict__["_auto"] = v
    if v is False and TC["mode"].get("unauto_clears"): s._shapes = []          # v0.166 cases
def _tc_build(s):
    m = TC["mode"]
    TC["calls"].append("buildAuto")
    if m.get("build_raises"): raise RuntimeError("buildAuto boom")
    if m.get("build_needs_auto") and not s.__dict__.get("_auto", False): return False
    if m.get("build_false"): return False
    for name in s.__dict__.get("_recipe", "").split("+"):
        sh = TCShape(TCSRC[name]._contours, component="cppsrc2" if m.get("build_other_name") else name)     # v0.169 case
        if m.get("build_other_name"): sh.shapeData._owner = "cppsrc2"
        if m.get("build_offset"): sh._tx = TCQT(1, 0, 0, 1, 30, 0)
        s._shapes.append(sh)
    if m.get("build_width"): P72["widths"][s._glyph] = 250.0
    if m.get("build_plain"): s._shapes.append(TCShape([te_contour(TE_SQ)]))
    if m.get("build_adds_glyph"): TS["cppnew"] = TsGlyph("cppnew", [])
    if m.get("build_none"): return None          # v0.169 case: placed, but not the documented True
    return True
TCLayer.recipe = property(_tc_get_recipe, _tc_set_recipe)
TCLayer.autoLayer = property(_tc_get_auto, _tc_set_auto)
TCLayer.buildAuto = _tc_build
AK = ("step", "recipe", "auto_before", "auto_after", "step_took_effect", "call_returned", "outline_changed", "placed", "component_placed",
      "side_effect_detected", "error", "calls_so_far")
QA = QC + "stage=auto&target=cpp1"
def tca(tag, q, mode=None, recipe=None, auto=None, keys=AK):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    if recipe is not None: P72["layers"]["cpp1"].__dict__["_recipe"] = recipe
    if auto is not None: P72["layers"]["cpp1"].__dict__["_auto"] = auto
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 0.0
    d = tc(tag, QA + q, keys=keys)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
tca("2390a no step                       ", "&go=yes")
tca("2390b step=make                     ", "&step=make&go=yes")
tca("2390c setrecipe without a recipe     ", "&step=setrecipe&go=yes")
tca("2390d read with a recipe             ", "&step=read&recipe=cppsrc&go=yes")
tc_gen_setup(); tc("2390e step with stage=generate     ", QG + "&step=read&go=yes")
tca("2390f setrecipe shown before go      ", "&step=setrecipe&recipe=cppsrc")
tca("2390g a two-glyph recipe, plain +    ", "&step=setrecipe&recipe=cppsrc+cppsrc2&go=yes")
tca("2391 read                           ", "&step=read&go=yes")
tca("2392 setrecipe cppsrc               ", "&step=setrecipe&recipe=cppsrc&go=yes")
tca("2393 build with the recipe set      ", "&step=build&recipe=cppsrc&go=yes", recipe="cppsrc")
tca("2394 build when the recipe differs  ", "&step=build&recipe=cppsrc&go=yes", recipe="")
tca("2395 setauto                        ", "&step=setauto&go=yes")
tca("2396a build needs autoLayer: off     ", "&step=build&recipe=cppsrc&go=yes", mode={"build_needs_auto": 1}, recipe="cppsrc")
tca("2396b build needs autoLayer: on      ", "&step=build&recipe=cppsrc&go=yes", mode={"build_needs_auto": 1}, recipe="cppsrc", auto=True)
tca("2396c two-glyph recipe              ", "&step=build&recipe=cppsrc%2Bcppsrc2&go=yes", recipe="cppsrc+cppsrc2")
for tag, mode, q, rec in (("2397a recipe ignored                ", {"recipe_ignored": 1}, "&step=setrecipe&recipe=cppsrc", None),
                          ("2397b recipe also sets autoLayer    ", {"recipe_sets_auto": 1}, "&step=setrecipe&recipe=cppsrc", None),
                          ("2397c autoLayer ignored             ", {"auto_ignored": 1}, "&step=setauto", None),
                          ("2397d recipe unreadable: build refused", {"recipe_unreadable": 1}, "&step=build&recipe=cppsrc", None),
                          ("2397e buildAuto raises              ", {"build_raises": 1}, "&step=build&recipe=cppsrc", "cppsrc"),
                          ("2397f buildAuto returns False       ", {"build_false": 1}, "&step=build&recipe=cppsrc", "cppsrc"),
                          ("2397g an offset component           ", {"build_offset": 1}, "&step=build&recipe=cppsrc", "cppsrc"),
                          ("2397h the width changes             ", {"build_width": 1}, "&step=build&recipe=cppsrc", "cppsrc"),
                          ("2397i a plain shape too             ", {"build_plain": 1}, "&step=build&recipe=cppsrc", "cppsrc"),
                          ("2397j a glyph appears               ", {"build_adds_glyph": 1}, "&step=build&recipe=cppsrc", "cppsrc")):
    tca(tag, q + "&go=yes", mode=mode, recipe=rec)
tc_gen_setup()
for tag, tgt in (("2398a target with a contour: refused", "cppbase"), ("2398b target with a component: refused", "cppcomp"),
                 ("2398c target with no layer          ", "cppnolayer")):
    tc(tag, QC + f"stage=auto&target={tgt}&step=setauto&go=yes")
tc("2398d read on a target with a component", QC + "stage=auto&target=cppcomp&step=read&go=yes", keys=("auto_before", "side_effect_detected", "error"))
tc_gen_setup()
for _i in range(6): call(QA + "&step=read&go=yes")
tc("2399 the limit: call 7 is refused   ", QA + "&step=read&go=yes")
_src165 = "\n".join(l for l in src[src.index("def _trycomp_auto_state("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2399a spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|addComponent|clearComponents|removeShape|replaceShape)\s*\(|font\.update|_mark_font_changed", _src165),
      "| one call each:", [len(_re83.findall(r"(?m)^\s+(?:ret = )?layer\." + c, _src165)) for c in (r'recipe = "\+"', r"autoLayer = True", r"buildAuto\(\)")],
      "| counter before the read:", src.index('    if auto:\n        _TRYCOMP["calls"] += 1') < src.index("return _trycomp_auto("),
      "| route documented:", "stage=auto&target=cpp...&step=read|setrecipe|setauto|build" in src, "| dispatched:", '(query.get("step") or [None])[0]' in src)

# ---- v0.166: step=unauto / killauto on a layer buildAuto() filled. TCLayer.killAuto answers by TC["mode"].
print("\n==== v0.166 stage=auto step=unauto / killauto ====")
def _tc_kill(s):
    m = TC["mode"]
    TC["calls"].append("killAuto")
    if m.get("kill_raises"): raise RuntimeError("killAuto boom")
    if not m.get("kill_keeps_auto"): s.__dict__["_auto"] = False
    if m.get("kill_clears_recipe"): s.__dict__["_recipe"] = ""
    if m.get("kill_clears"): s._shapes = []
    if m.get("kill_decomposes"): s._shapes = [TCShape(sh._contours) for sh in s._shapes]
    return None
TCLayer.killAuto = _tc_kill
AK6 = ("step", "auto_before", "auto_after", "step_took_effect", "call_returned", "outline_changed", "component_kept", "component_normal",
       "side_effect_detected", "error", "calls_so_far")
def tcb(tag, q, mode=None, auto=True, recipe="cppsrc", shapes=None, keys=AK6):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = recipe; lay.__dict__["_auto"] = auto
    lay._shapes = shapes if shapes is not None else [TCShape(TCSRC["cppsrc"]._contours, component="cppsrc")]
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 0.0
    d = tc(tag, QA + q, keys=keys)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
tcb("2400a unauto with a recipe          ", "&step=unauto&recipe=cppsrc&go=yes")
tcb("2400b unauto shown before go         ", "&step=unauto")
tcb("2400c unauto, autoLayer already off  ", "&step=unauto&go=yes", auto=False)
tcb("2400d unauto on an empty layer       ", "&step=unauto&go=yes", shapes=[])
tcb("2400e killauto on a plain contour    ", "&step=killauto&go=yes", shapes=[TCShape([te_contour(TE_SQ)])])
tcb("2401 unauto (test 1042)             ", "&step=unauto&go=yes")
tcb("2402 killauto                       ", "&step=killauto&go=yes")
for tag, q, mode in (("2403a unauto clears the layer       ", "&step=unauto", {"unauto_clears": 1}),
                     ("2403b unauto is ignored             ", "&step=unauto", {"auto_ignored": 1}),
                     ("2403c killauto clears the layer     ", "&step=killauto", {"kill_clears": 1}),
                     ("2403d killauto decomposes           ", "&step=killauto", {"kill_decomposes": 1}),
                     ("2403e killauto clears the recipe    ", "&step=killauto", {"kill_clears_recipe": 1}),
                     ("2403f killauto leaves autoLayer on  ", "&step=killauto", {"kill_keeps_auto": 1}),
                     ("2403g killauto raises               ", "&step=killauto", {"kill_raises": 1})):
    tcb(tag, q + "&go=yes", mode=mode)
_src166 = "\n".join(l for l in src[src.index("def _trycomp_auto("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2404 spies over the cases:", TC_FORBIDDEN, "| one call each:", [len(_re83.findall(r"(?m)^\s+(?:ret = )?layer\." + c, _src166)) for c in (r"autoLayer = False", r"killAuto\(\)")],
      "| route documented:", "step=unauto|killauto: autoLayer = False, or ONE killAuto()" in src)

# ---- v0.167: stage=offset on a layer holding one component at identity, autoLayer False (as after live 1042). TCShape gets inkBox()
# (the contours' box moved by the shape's offset, "top" the lower y as live 644) and applyTransform(); both answer by TC["mode"].
print("\n==== v0.167 /debug/trycomponent stage=offset ====")
class TCRect:
    def __init__(s, l, b, r, t): s._v = dict(left=l, right=r, top=b, bottom=t, width=r - l, height=t - b)
    def left(s): return s._v["left"]
    def right(s): return s._v["right"]
    def top(s): return s._v["top"]
    def bottom(s): return s._v["bottom"]
    def width(s): return s._v["width"]
    def height(s): return s._v["height"]
def _tc_inkbox(s):
    TC["calls"].append("inkBox")
    if TC["mode"].get("box_raises"): raise RuntimeError("inkBox boom")
    xs = [r["x"] for c in s._contours for r in c.rows]; ys = [r["y"] for c in s._contours for r in c.rows]
    if TC["mode"].get("box_from_source"):
        xs = [r["x"] for c in TCSRC["cppsrc"]._contours for r in c.rows]; ys = [r["y"] for c in TCSRC["cppsrc"]._contours for r in c.rows]
    btx = s.__dict__.get("_boxtx", s._tx)
    ox, oy = (0.0, 0.0) if TC["mode"].get("box_stale") else (btx.dx(), btx.dy())
    return TCRect(min(xs) + ox, min(ys) + oy, max(xs) + ox, max(ys) + oy)
def _tc_offset_effects(s, dx, dy):
    m = TC["mode"]
    if m.get("moves_nodes"): s._contours = [te_contour([(r["x"] + dx, r["y"] + dy) for r in c.rows]) for c in s._contours]
    if m.get("nodes_jitter"): s._contours = [te_contour([(r["x"] + 1, r["y"]) for r in c.rows]) for c in s._contours]
    if m.get("offset_width"): P72["widths"]["cpp1"] = 40.0
    if m.get("offset_source"): TCSRC["cppsrc"]._contours[0].rows[0]["x"] += 1.0
    if m.get("offset_auto"): P72["layers"]["cpp1"].__dict__["_auto"] = True
def _tc_apply(s, tx):
    m = TC["mode"]
    TC["calls"].append(("applyTransform", tx.dx(), tx.dy()))
    if m.get("apply_raises"): raise RuntimeError("applyTransform boom")
    if m.get("apply_ignored"): return None
    k = 2 if m.get("apply_doubles") else 1
    s._tx = TCQT(1, 0, 0, 1, s._tx.dx() + k * tx.dx(), s._tx.dy() + k * tx.dy())
    _tc_offset_effects(s, tx.dx(), tx.dy())
    return None
_tc_tx_prop = TCShape.__dict__["transform"]
def _tc_set_tx(s, v):
    TC["calls"].append("shape.transform=")
    if TC["mode"].get("tx_raises"): raise RuntimeError("transform boom")
    if TC["mode"].get("tx_ignored"): return
    if TC["mode"].get("tx_hidden"): s.__dict__["_boxtx"] = v; return       # drawn moved, but the matrix still reads identity
    s._tx = v
    _tc_offset_effects(s, v.dx(), v.dy())
TCShape.inkBox = _tc_inkbox
TCShape.applyTransform = _tc_apply
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx)
OK7 = ("how", "source", "call_returned", "matrix_reads_offset", "ink_box_moved", "raw_nodes", "changed", "side_effect_detected",
       "offset_placed", "error", "calls_so_far")
QO = QC + "stage=offset&target=cpp1"
def tco(tag, q, mode=None, auto=False, shapes=None, keys=OK7):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = "cppsrc"; lay.__dict__["_auto"] = auto
    lay._shapes = shapes if shapes is not None else [TCShape(TCSRC["cppsrc"]._contours, component="cppsrc")]
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 0.0
    d = tc(tag, QO + q, keys=keys)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| boxes:", {k: (d.get(k) or {}).get("left") for k in ("ink_box_before", "ink_box_after")},
          "| mark:", d.get("fontlab_changed_mark"))
    return d
tco("2405a offset shown before go         ", "&how=assign&dx=100&dy=50")
tco("2405b how missing                    ", "&dx=100&dy=50&go=yes")
tco("2405c how=move                       ", "&how=move&dx=100&dy=50&go=yes")
tc_gen_setup(); tc("2405d how with stage=auto           ", QA + "&step=read&how=assign&go=yes")
tco("2405e a source given                 ", "&how=assign&source=cppsrc&dx=100&dy=50&go=yes")
tco("2405f dx and dy both 0               ", "&how=apply&dx=0&dy=0&go=yes")
tco("2405g dy missing                     ", "&how=assign&dx=100&go=yes")
tco("2405h a recipe given                 ", "&how=assign&recipe=cppsrc&dx=100&dy=50&go=yes")
d = tco("2406 assign (test 1043)             ", "&how=assign&dx=100&dy=50&go=yes")
print("2406a  matrix, boxes, outline, auto :", tc_elements(d, "target_elements_after"), d.get("ink_box_before"), d.get("ink_box_after"),
      te_outline(d, "target_after"), d.get("auto_before"), d.get("auto_after"), "| synced", d.get("synced_with_fontlab"), "| qt", d.get("qtransform"))
tco("2407 apply                          ", "&how=apply&dx=-30&dy=0&go=yes")
for tag, kw in (("2408a autoLayer on                   ", dict(auto=True)),
                ("2408b an empty layer                 ", dict(shapes=[])),
                ("2408c a plain contour                ", dict(shapes=[TCShape([te_contour(TE_SQ)])])),
                ("2408d two components                 ", dict(shapes=[TCShape([te_contour(TE_TRI)], component="cppsrc"), TCShape([te_contour(TE_TRI)], component="cppsrc")])),
                ("2408f a component of a non-cpp glyph ", dict(shapes=[TCShape([te_contour(TE_TRI)], component="A")]))):
    tco(tag, "&how=assign&dx=10&dy=10&go=yes", **kw)
_sh = TCShape(TCSRC.get("cppsrc")._contours if TCSRC.get("cppsrc") else [te_contour(TE_TRI)], component="cppsrc"); _sh._tx = TCQT(1, 0, 0, 1, 5, 0)
tco("2408e already offset                 ", "&how=assign&dx=10&dy=10&go=yes", shapes=[_sh])
tc_gen_setup(); tc("2408g target with no layer         ", QC + "stage=offset&target=cppnolayer&how=assign&dx=10&dy=10&go=yes")
print("2408h  no offset call in the refusals:", [x for x in TC["calls"] if x == "shape.transform=" or (isinstance(x, tuple) and x[0] == "applyTransform")])
for tag, how, mode in (("2409a assignment ignored            ", "assign", {"tx_ignored": 1}),
                       ("2409b assignment raises             ", "assign", {"tx_raises": 1}),
                       ("2409c applyTransform ignored        ", "apply", {"apply_ignored": 1}),
                       ("2409d applyTransform raises         ", "apply", {"apply_raises": 1}),
                       ("2409e applyTransform doubles        ", "apply", {"apply_doubles": 1}),
                       ("2409f nodes AND transform move: twice", "assign", {"moves_nodes": 1}),
                       ("2409m raw nodes read moved, box once", "assign", {"moves_nodes": 1, "box_stale": 1}),
                       ("2409n raw nodes moved by (1, 0) only", "assign", {"nodes_jitter": 1, "box_from_source": 1}),
                       ("2409o box moved, matrix still identity", "assign", {"tx_hidden": 1}),
                       ("2409g ink box stays put             ", "assign", {"box_stale": 1}),
                       ("2409h ink box unreadable: refused   ", "assign", {"box_raises": 1}),
                       ("2409i the width changes             ", "assign", {"offset_width": 1}),
                       ("2409j the source changes            ", "assign", {"offset_source": 1}),
                       ("2409k autoLayer turns on            ", "apply", {"offset_auto": 1}),
                       ("2409l the QTransform reads wrong    ", "assign", {"qt_bad": 1})):
    tco(tag, f"&how={how}&dx=100&dy=50&go=yes", mode=mode)
tc_gen_setup()
for _i in range(6): call(QO + "&how=assign&dx=1&dy=1&go=yes")
tc("2410 the limit: call 7 is refused   ", QO + "&how=assign&dx=1&dy=1&go=yes")
_src167 = "\n".join(l for l in src[src.index("def _trycomp_first_box("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2410a spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|addComponent|clearComponents|removeShape|replaceShape|decomposite|killAuto|buildAuto)\s*\(|font\.update|_mark_font_changed|autoLayer =|recipe =", _src167),
      "| one call each:", [len(_re83.findall(r"(?m)^\s+(?:ret = )?shape\." + c, _src167)) for c in (r"transform = tx", r"applyTransform\(tx\)")],
      "| counter before the read:", src.index('    if offset:\n        oqt_cls') < src.index('_TRYCOMP["calls"] += 1     # counted BEFORE the glyph is read\n        return _trycomp_offset('),
      "| route documented:", "stage=offset&target=cpp...&how=assign|apply&dx=DX&dy=DY" in src, "| dispatched:", '(query.get("how") or [None])[0]' in src)
TCShape.transform = _tc_tx_prop
for _a in ("inkBox", "applyTransform"):
    if _a in TCShape.__dict__: delattr(TCShape, _a)

# ---- v0.168: stage=auto&step=clearrecipe on a normal component layer (autoLayer off, as after live 1042 and 1050). The recipe setter
# answers the new modes below, then the v0.165 fake.
print("\n==== v0.168 stage=auto step=clearrecipe ====")
def _tc_set_recipe168(s, v):
    m = TC["mode"]
    if v == "" and m.get("clear_raises"): TC["calls"].append(("recipe=", v)); raise RuntimeError("recipe boom")
    _tc_set_recipe(s, v)
    if v == "" and m.get("clear_raises_after"): raise RuntimeError("recipe cleared, then boom")     # v0.169 case
    if v == "":
        if m.get("clear_drops"): s._shapes = []
        if m.get("clear_resets_offset"):
            for sh in s._shapes: sh._tx = TCQT()
        if m.get("clear_width"): P72["widths"]["cpp1"] = 500.0
        if m.get("clear_sets_auto"): s.__dict__["_auto"] = True
TCLayer.recipe = property(_tc_get_recipe, _tc_set_recipe168)
CK8 = ("step", "auto_before", "auto_after", "step_took_effect", "outline_changed", "component_kept", "recipe_cleared",
       "side_effect_detected", "error", "calls_so_far")
def _tc_comp(name, dx=0, dy=0):
    sh = TCShape(TCSRC[name]._contours, component=name)
    if dx or dy: sh._tx = TCQT(1, 0, 0, 1, dx, dy)
    return sh
def tcc(tag, q, mode=None, auto=False, recipe="cppsrc", shapes=None, legacy_nodes=3):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = recipe; lay.__dict__["_auto"] = auto
    lay._shapes = shapes if shapes is not None else [_tc_comp("cppsrc", 100, 50)]
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0     # the legacy view agrees with the modern one
    d = tc(tag, QA + q, keys=CK8)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
tcc("2411a clearrecipe shown before go    ", "&step=clearrecipe")
tcc("2411b clearrecipe with a recipe      ", "&step=clearrecipe&recipe=cppsrc&go=yes")
tcc("2411c autoLayer on: refused          ", "&step=clearrecipe&go=yes", auto=True)
tcc("2411d recipe already empty: refused  ", "&step=clearrecipe&go=yes", recipe="")
tcc("2411e recipe unreadable: refused     ", "&step=clearrecipe&go=yes", mode={"recipe_unreadable": 1})
tcc("2411f an empty layer: refused        ", "&step=clearrecipe&go=yes", shapes=[])
tcc("2411g a plain contour: refused       ", "&step=clearrecipe&go=yes", shapes=[TCShape([te_contour(TE_SQ)])])
print("2411h  no recipe write in the refusals:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] == "recipe="])
d = tcc("2412 one component at (100, 50) (test 1058)", "&step=clearrecipe&go=yes")
print("2412a  matrices before / after, widths, sync:", tc_elements(d, "target_elements_before"), "/", tc_elements(d, "target_elements_after"),
      d.get("advance_width_before"), d.get("advance_width_after"), "| synced", d.get("synced_with_fontlab"))
tcc("2413 two components (test 1059)    ", "&step=clearrecipe&go=yes", recipe="cppsrc+cppsrc2",
    shapes=[_tc_comp("cppsrc"), _tc_comp("cppsrc2", -200, 0)], legacy_nodes=7)
for tag, mode in (("2414a the assignment is ignored     ", {"recipe_ignored": 1}),
                  ("2414b the assignment raises         ", {"clear_raises": 1}),
                  ("2414c the components are dropped    ", {"clear_drops": 1}),
                  ("2414d the offset is reset           ", {"clear_resets_offset": 1}),
                  ("2414e the width changes             ", {"clear_width": 1}),
                  ("2414f autoLayer turns on            ", {"clear_sets_auto": 1})):
    tcc(tag, "&step=clearrecipe&go=yes", mode=mode)
_src168 = "\n".join(l for l in src[src.index("def _trycomp_auto("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2415 spies over the cases:", TC_FORBIDDEN, "| one clearing write:", len(_re83.findall(r'(?m)^\s+layer\.recipe = ""$', _src168)),
      "| route documented:", 'stage=auto&step=clearrecipe: layer.recipe = ""' in src)

# ================= v0.169: POST /glyph/component (add_component, the placing tool; the trycomponent fakes) =================
print("\n==== v0.169 POST /glyph/component (add_component) ====")
TCShape.inkBox = _tc_inkbox
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx)
TOPkg.mastersCount = property(lambda s: TC["mode"].get("masters", 1))
ACK = ("placed", "verified", "changed", "steps_done", "build_returned", "checks", "auto_layer_set_back", "reason", "error", "component_found")
def ac_setup(mode=None, auto=False, recipe=""):
    tc_gen_setup(mode=dict({"gen_list": 1, "build_needs_auto": 1}, **(mode or {})))
    lay = P72["layers"]["cpp1"]; lay.__dict__["_recipe"] = recipe; lay.__dict__["_auto"] = auto
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 0.0
def ac(tag, payload, mode=None, auto=False, recipe="", keys=ACK, legacy_nodes=3):
    ac_setup(mode, auto, recipe)
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    c, d = sbpost("/glyph/component", payload)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform")],
          "| Update", TE["updates"], "| marks", TE["marks"])
    if isinstance(d.get("elements_after"), list):
        print("      elements after:", tc_elements(d, "elements_after"), "| auto after:", d.get("auto_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
P0 = {"name": "cpp1", "component": "cppsrc", "x": 0, "y": 0}
for tag, payload in (("2420a no x                         ", {"name": "cpp1", "component": "cppsrc", "y": 0}),
                     ("2420b an extra key                 ", dict(P0, scale=1)),
                     ("2420c empty name                   ", dict(P0, name=" ")),
                     ("2420d component not a string       ", dict(P0, component=5)),
                     ("2420e the glyph itself             ", dict(P0, component="cpp1")),
                     ("2420f x 1.5                        ", dict(P0, x=1.5)),
                     ("2420g y a bool                     ", dict(P0, y=True)),
                     ("2420h x 10001                      ", dict(P0, x=10001))):
    ac(tag, payload)
d = ac("2421 at (0, 0)                      ", P0)
print("2421a  ink box, expected, widths, counts, sync:", d.get("ink_box"), d.get("ink_box_expected"), d.get("advance_width_before"), d.get("advance_width_after"),
      d.get("glyph_count_before"), d.get("glyph_count_after"), "| synced", d.get("synced_with_fontlab"), "| repainted", d.get("display_refreshed"))
d = ac("2422 at (100, 50)                   ", dict(P0, x=100, y=50))
print("2422a  ink box / expected        :", d.get("ink_box"), "/", d.get("ink_box_expected"))
ac("2422b a leftover recipe on an empty layer", dict(P0, x=-30, y=0), recipe="cppsrc2")
ac("2422c a second source, cppsrc2   ", dict(P0, component="cppsrc2", x=10, y=0), legacy_nodes=4)
for tag, payload, kw in (("2423a no font open                 ", P0, dict(mode={})),
                         ("2423b target does not exist        ", dict(P0, name="cppzz"), {}),
                         ("2423c target has no layer          ", dict(P0, name="cppnolayer"), {}),
                         ("2423d target holds a contour       ", dict(P0, name="cppbase"), {}),
                         ("2423e target holds a component     ", dict(P0, name="cppcomp"), {}),
                         ("2423f autoLayer on                 ", P0, dict(auto=True)),
                         ("2423g recipe unreadable            ", P0, dict(mode={"recipe_unreadable": 1})),
                         ("2423h source does not exist        ", dict(P0, component="cppzz"), {}),
                         ("2423i source is a Power Brush shape", dict(P0, component="cppbrush"), {}),
                         ("2423j source holds a component     ", dict(P0, component="cppcomp"), {}),
                         ("2423k source has no nodes          ", dict(P0, component="cppbare"), {}),
                         ("2423l source is empty              ", dict(P0, component="cppempty"), {}),
                         ("2423m two masters                  ", P0, dict(mode={"masters": 2})),
                         ("2423n box unreadable               ", P0, dict(mode={"box_raises": 1}))):
    P72["layers_unreadable"] = {"cppbase", "cppcomp"} if tag.startswith(("2423d", "2423e")) else set()     # v0.187: as before the v0.181 fakes
    if tag.startswith("2423a"):
        ac_setup(); TO["count"] = 0
        c, d = sbpost("/glyph/component", payload); print(tag, ":", c, d)
        continue
    ac(tag, payload, **kw)
print("2423o  no write in the refusals :", [x for x in TC["calls"] if x in ("buildAuto", "shape.transform=") or (isinstance(x, tuple) and x[0] in ("recipe=", "autoLayer="))])
for tag, payload, mode in (("2424a buildAuto returns False: set back", P0, {"build_false": 1}),
                           ("2424b buildAuto raises: set back   ", P0, {"build_raises": 1}),
                           ("2424c autoLayer writes ignored: build False", P0, {"auto_ignored": 1}),
                           ("2424d the offset is ignored        ", dict(P0, x=100, y=50), {"tx_ignored": 1}),
                           ("2424e the offset raises            ", dict(P0, x=100, y=50), {"tx_raises": 1}),
                           ("2424f clearing the recipe raises   ", P0, {"clear_raises": 1}),
                           ("2424g FontLab places it at (30, 0) ", P0, {"build_offset": 1}),
                           ("2424h the width changes            ", P0, {"build_width": 1}),
                           ("2424i a plain shape comes too      ", P0, {"build_plain": 1}),
                           ("2424j a glyph appears              ", P0, {"build_adds_glyph": 1}),
                           ("2424k the source changes           ", dict(P0, x=100, y=50), {"offset_source": 1}),
                           ("2424l the box stays put            ", dict(P0, x=100, y=50), {"box_stale": 1}),
                           ("2424m buildAuto places, returns None", P0, {"build_none": 1}),
                           ("2424n a component of another glyph ", P0, {"build_other_name": 1}),
                           ("2424o autoLayer=False ignored      ", P0, {"auto_off_ignored": 1}),
                           ("2424p an error after the last write", P0, {"clear_raises_after": 1})):
    ac(tag, payload, mode=mode)
ac_setup()
print("2424q  the function itself refuses the glyph as its own component:", ns["add_component"]("cpp1", "cpp1", 0, 0),
      "| calls", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform")])
_srcac = "\n".join(l for l in src[src.index("# POST /glyph/component (v0.169)"):src.index('# POST /glyph/component with "components" (v0.174)')].split("\n") if not l.lstrip().startswith("#"))
_acf = _srcac[_srcac.index("def add_component("):]
print("2425 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addComponent|clearComponents|killAuto|decomposite|removeShape|replaceShape|addShape|applyTransform)\s*\(|font\.update|_ensure_modern_layer|create_layer=True", _srcac),
      "| every refusal before the first write:", _acf.rindex("nothing was changed") < _acf.index("layer.recipe = component"),
      "| write statements:", [len(_re83.findall(r"(?m)^\s+" + s, _acf)) for s in (r"layer\.recipe = component$", r"layer\.autoLayer = True$", r"ret = layer\.buildAuto\(\)$",
                                                                                  r"layer\.autoLayer = False$", r"shapes\[0\]\.transform = ", r'layer\.recipe = ""$')])
print("2425a route documented:", "POST /glyph/component" in src, "| dispatched:", 'if path == "/glyph/component":' in src, "| mark title:", ns["_MARK_TITLES"].get("add_component"),
      "| guard kind full:", "add_component" in ns["_GUARD_FULL_KINDS"], "| activity kind:", ns["_ACT_WRITES"].get("/glyph/component"))
_acr = {"open": True, "placed": True, "synced_with_fontlab": True}
for tag, code, reply in (("2425b log, placed            ", 200, _acr), ("2425c log, placed, not synced", 200, dict(_acr, synced_with_fontlab=False)),
                         ("2425d log, refused           ", 200, {"open": True, "placed": False, "reason": "the glyph is not empty"}),
                         ("2425e log, changed, set back ", 200, {"open": True, "placed": False, "changed": True, "auto_layer_set_back": True, "reason": "layer.buildAuto() failed"}),
                         ("2425f log, bad request       ", 400, {"error": "x"})):
    print(tag, ":", ns["_act_describe_write"]("/glyph/component", dict(P0, x=100, y=50), code, reply))
# ---- v0.170: GET /debug/markswitch (S1 research): the listener's changed mark off / on for this run, shown on an add_component write
print("\n==== v0.170 /debug/markswitch ====")
QM = "/debug/markswitch"
for tag, q in (("2430a read only                     ", ""), ("2430b on=2                          ", "?on=2&go=yes"),
               ("2430c on=0 without go               ", "?on=0"), ("2430d on=0, go=Yes                 ", "?on=0&go=Yes")):
    print(tag, ":", call(QM + q), "| switch", ns["_MARK_CHANGED"])
print("2430f a blank on, called directly: read only:", ns["debug_mark_switch"]("  ", "yes"), "| switch", ns["_MARK_CHANGED"])
print("2430e switched off                     :", call(QM + "?on=0&go=yes"), "| switch", ns["_MARK_CHANGED"])
d = ac("2431 add_component while it is off  ", P0, keys=("placed", "verified"))
print("2431a  the reply says why               :", d.get("fontlab_changed_mark"), "| synced", d.get("synced_with_fontlab"))
print("2431b off again: no second notice      :", call(QM + "?on=0&go=yes"))
print("2432 switched on again                 :", call(QM + "?on=1&go=yes"), "| switch", ns["_MARK_CHANGED"])
d = ac("2432a add_component, marked again   ", P0, keys=("placed", "verified"))
print("2432b  mark                             :", d.get("fontlab_changed_mark"))
_srcms = src[src.index("def debug_mark_switch("):src.index("def debug_try_component(")]
print("2433 the switch touches nothing else   :", _re83.findall(r"\bfl\.|fontlab\.|flItems|notify\w*\(|CurrentFont|_open_font", _srcms),
      "| route documented:", "/debug/markswitch     [on=0|1&go=yes]" in src, "| dispatched:", 'if path == "/debug/markswitch":' in src,
      "| shipped on:", "_MARK_CHANGED = True    # v0.132" in src)
ns["_MARK_CHANGED"] = True

# ---- v0.171: several components (the user's choice of 2026-11-17). stage=auto takes recipes of up to three glyphs; stage=offset&element=I
# sets the offset of ONE component among 2 or 3 (as after live 1049: cppsrc at identity, cppsrc2 at (-200, 0)). The transform setter of
# v0.167 answers the new mode "other_moves" (every other component moves by (5, 0) too); TCShapeDataFlip names another glyph once the
# ink boxes were read (the shape at I changed between the read and the write).
print("\n==== v0.171 /debug/trycomponent: several components ====")
def _tc_set_tx171(s, v):
    _tc_set_tx(s, v)
    if TC["mode"].get("other_moves"):
        for sh in P72["layers"]["cpp1"]._shapes:
            if sh is not s: sh._tx = TCQT(1, 0, 0, 1, sh._tx.dx() + 5, sh._tx.dy())
    if TC["mode"].get("other_matrix_only"):     # another component's matrix reads changed, its box does not
        for sh in P72["layers"]["cpp1"]._shapes:
            if sh is not s: sh.__dict__["_boxtx"] = sh._tx; sh._tx = TCQT(1, 0, 0, 1, sh._tx.dx() + 5, sh._tx.dy())
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx171)
class TCShapeDataFlip(TCShapeData):
    def componentGlyph(s):
        if "inkBox" not in TC["calls"]: return s._glyph
        if TC["mode"].get("flip_raises"): raise RuntimeError("componentGlyph boom")
        return "cppother"
def _tc_src3():
    src3 = TCShape([te_contour([(0, 400), (100, 400), (100, 500), (0, 500)])]); src3.shapeData._owner = "cppsrc3"; TCSRC["cppsrc3"] = src3
    TS["cppsrc3"] = TsGlyph("cppsrc3", [TsLayer(1, 4)]); P72["layers"]["cppsrc3"] = TCLayer("test_font", [src3], "cppsrc3"); P72["widths"]["cppsrc3"] = 100.0
def _tc_two():
    return [_tc_comp("cppsrc"), _tc_comp("cppsrc2", -200, 0)]
OK71 = ("how", "element", "source", "offset_before", "matrix_reads_offset", "ink_box_moved", "raw_nodes", "others_kept", "changed",
        "side_effect_detected", "offset_placed", "error", "calls_so_far")
def tce(tag, q, mode=None, auto=False, shapes=None, legacy_nodes=7):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    _tc_src3()
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = ""; lay.__dict__["_auto"] = auto
    lay._shapes = shapes() if callable(shapes) else (shapes if shapes is not None else _tc_two())
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    d = tc(tag, QO + q, keys=OK71)
    lefts = lambda k: [b.get("left") for b in d[k]] if isinstance(d.get(k), list) else d.get(k)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| lefts:", lefts("ink_boxes_before"), "->", lefts("ink_boxes_after"),
          "| mark:", d.get("fontlab_changed_mark"))
    return d
E1 = "&how=assign&element=1&dx=0&dy=0"
tce("2440a element shown before go       ", E1)
tce("2440b element with how=apply        ", "&how=apply&element=1&dx=0&dy=0&go=yes")
tc_gen_setup(); tc("2440c element with stage=auto      ", QA + "&step=read&element=1&go=yes")
tce("2440d element 30 (v0.173: 0 to 29)  ", "&how=assign&element=30&dx=0&dy=0&go=yes")
tce("2440e element x                     ", "&how=assign&element=x&dx=0&dy=0&go=yes")
tce("2440f element -1                    ", "&how=assign&element=-1&dx=0&dy=0&go=yes")
d = tce("2441 cppsrc2 from (-200, 0) to (0, 0) (after 1049)", E1 + "&go=yes")
print("2441a  boxes, outline, width, sync    :", d.get("ink_boxes_after"), te_outline(d, "target_after"), d.get("advance_width_before"),
      d.get("advance_width_after"), "| synced", d.get("synced_with_fontlab"))
tce("2441b element 0 to (50, 0)          ", "&how=assign&element=0&dx=50&dy=0&go=yes")
tce("2441c three: element 2 to (300, -20)", "&how=assign&element=2&dx=300&dy=-20&go=yes",
    shapes=lambda: _tc_two() + [_tc_comp("cppsrc3")], legacy_nodes=11)
tce("2441d one source twice, element 1   ", "&how=assign&element=1&dx=-100&dy=0&go=yes",
    shapes=lambda: [_tc_comp("cppsrc"), _tc_comp("cppsrc", 300, 0)], legacy_nodes=6)
def _flip(raises=False):
    sh = _tc_comp("cppsrc2", -200, 0); sh.shapeData = TCShapeDataFlip("cppsrc2", 1, sh._contours); return [_tc_comp("cppsrc"), sh]
for tag, kw in (("2442a element 2 of two                ", dict(q="&how=assign&element=2&dx=0&dy=0&go=yes")),
                ("2442b one component only             ", dict(shapes=lambda: [_tc_comp("cppsrc2", -200, 0)], legacy_nodes=4)),
                ("2442c 31 components (v0.173)         ", dict(shapes=lambda: _tc_two() + [_tc_comp("cppsrc", 10 * k, 0) for k in range(1, 30)],
                                                               legacy_nodes=7 + 3 * 29)),
                ("2442d a plain contour among them     ", dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)])])),
                ("2442e a component of a non-cpp glyph ", dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)], component="A")])),
                ("2442f a scaled component             ", dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape(TCSRC["cppsrc2"]._contours, component="cppsrc2")],
                                                               scale=True)),
                ("2442g already at (0, 0)              ", dict(q="&how=assign&element=0&dx=0&dy=0&go=yes")),
                ("2442h autoLayer on                   ", dict(auto=True)),
                ("2442i the shape at 1 names another   ", dict(shapes=lambda: _flip())),
                ("2442j the shape at 1 cannot be checked", dict(shapes=lambda: _flip(), mode={"flip_raises": 1})),
                ("2442k an ink box unreadable          ", dict(mode={"box_raises": 1}))):
    q = kw.pop("q", E1 + "&go=yes")
    if kw.pop("scale", False):
        _shp = kw["shapes"]
        def _scaled(_shp=_shp):
            out = _shp(); out[1]._tx = TCQT(2, 0, 0, 1, -200, 0); return out
        kw["shapes"] = _scaled
    tce(tag, q, **kw)
print("2442l  no offset write in the refusals:", [x for x in TC["calls"] if x == "shape.transform="])
for tag, mode in (("2443a the assignment is ignored     ", {"tx_ignored": 1}),
                  ("2443b the other component moves too ", {"other_moves": 1}),
                  ("2443c the width changes             ", {"offset_width": 1}),
                  ("2443d a source changes              ", {"offset_source": 1}),
                  ("2443e autoLayer turns on            ", {"offset_auto": 1}),
                  ("2443f the ink boxes stay put        ", {"box_stale": 1}),
                  ("2443h the assignment raises         ", {"tx_raises": 1}),
                  ("2443i another matrix changes, not its box", {"other_matrix_only": 1})):
    tce(tag, E1 + "&go=yes", mode=mode)
# recipes of three glyphs (stage=auto only)
def tca3(tag, q, recipe=None, auto=None, legacy_nodes=3):
    tc_gen_setup(mode={"gen_list": 1})
    _tc_src3()
    if recipe is not None: P72["layers"]["cpp1"].__dict__["_recipe"] = recipe
    if auto is not None: P72["layers"]["cpp1"].__dict__["_auto"] = auto
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    d = tc(tag, QA + q, keys=AK)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
R3 = "cppsrc%2Bcppsrc2%2Bcppsrc3"
tca3("2445a setrecipe of three glyphs     ", "&step=setrecipe&recipe=" + R3 + "&go=yes")
tca3("2445b build of three glyphs         ", "&step=build&recipe=" + R3 + "&go=yes", recipe="cppsrc+cppsrc2+cppsrc3", auto=True, legacy_nodes=11)
tca3("2445c a recipe of 31 glyphs (v0.173)", "&step=setrecipe&recipe=" + "%2B".join([R3] * 10) + "%2Bcppsrc&go=yes")
tca3("2445d three, one names the target   ", "&step=setrecipe&recipe=cppsrc%2Bcppsrc2%2Bcpp1&go=yes")
tc_gen_setup(); _tc_src3(); tc("2445e generate keeps two           ", QC + "stage=generate&target=cpp1&recipe=" + R3 + "&go=yes")
_src171 = "\n".join(l for l in src[src.index("def _trycomp_first_box("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2446 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|addComponent|clearComponents|removeShape|replaceShape|decomposite|killAuto|buildAuto)\s*\(|font\.update|_mark_font_changed|autoLayer =|recipe =", _src171),
      "| one assignment:", len(_re83.findall(r"(?m)^\s+shape\.transform = tx$", _src171)),
      "| route documented:", "stage=offset&how=assign&element=I&dx=DX&dy=DY" in src, "| dispatched:", '(query.get("element") or [None])[0]' in src,
      "| more only for auto:", src.count("_trycomp_recipe(recipe, target, most=_TRYCOMP_AUTO_PARTS_MAX)"))
# ---- v0.172: four and five glyphs (the user's choice of 2026-11-17, before the tool's list limit is set). Two more sources: cppsrc4, a
# wide bar, and cppsrc5, a small square.
print("\n==== v0.172 /debug/trycomponent: four and five components ====")
def _tc_src45():
    _tc_src3()
    for name, pts, w in (("cppsrc4", [(0, -100), (600, -100), (600, -50), (0, -50)], 600.0), ("cppsrc5", [(0, 600), (50, 600), (50, 650), (0, 650)], 50.0)):
        sh = TCShape([te_contour(pts)]); sh.shapeData._owner = name; TCSRC[name] = sh
        TS[name] = TsGlyph(name, [TsLayer(1, 4)]); P72["layers"][name] = TCLayer("test_font", [sh], name); P72["widths"][name] = w
def tca5(tag, q, recipe=None, auto=None, legacy_nodes=3):
    tc_gen_setup(mode={"gen_list": 1})
    _tc_src45()
    if recipe is not None: P72["layers"]["cpp1"].__dict__["_recipe"] = recipe
    if auto is not None: P72["layers"]["cpp1"].__dict__["_auto"] = auto
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    d = tc(tag, QA + q, keys=AK)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
R4, R5 = R3 + "%2Bcppsrc4", R3 + "%2Bcppsrc4%2Bcppsrc5"
tca5("2447a setrecipe of five glyphs      ", "&step=setrecipe&recipe=" + R5 + "&go=yes")
tca5("2447b build of four glyphs          ", "&step=build&recipe=" + R4 + "&go=yes", recipe="cppsrc+cppsrc2+cppsrc3+cppsrc4", auto=True, legacy_nodes=15)
tca5("2447c build of five glyphs          ", "&step=build&recipe=" + R5 + "&go=yes", recipe="cppsrc+cppsrc2+cppsrc3+cppsrc4+cppsrc5", auto=True, legacy_nodes=19)
def tce5(tag, q, shapes, legacy_nodes):
    tc_gen_setup(mode={"gen_list": 1})
    _tc_src45()
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = ""; lay.__dict__["_auto"] = False
    lay._shapes = shapes()
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    d = tc(tag, QO + q, keys=OK71)
    lefts = lambda k: [b.get("left") for b in d[k]] if isinstance(d.get(k), list) else d.get(k)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| lefts:", lefts("ink_boxes_before"), "->", lefts("ink_boxes_after"),
          "| mark:", d.get("fontlab_changed_mark"))
    return d
_four = lambda: _tc_two() + [_tc_comp("cppsrc3", -50, 0), _tc_comp("cppsrc4", -300, 0)]
_five = lambda: _four() + [_tc_comp("cppsrc5", -25, 0)]
tce5("2448a four: element 3 to (0, 0)     ", "&how=assign&element=3&dx=0&dy=0&go=yes", _four, 15)
tce5("2448b five: element 4 to (175, 0)   ", "&how=assign&element=4&dx=175&dy=0&go=yes", _five, 19)
tce5("2448c four: element 4 does not exist", "&how=assign&element=4&dx=0&dy=0&go=yes", _four, 15)
print("2449 limits:", ns["_TRYCOMP_SEVERAL_MAX"], ns["_TRYCOMP_AUTO_PARTS_MAX"], "| route documented:", "stage=auto recipes of up to 30 glyphs (v0.173" in src,
      "| spies:", TC_FORBIDDEN)
# ---- v0.173: 30 glyphs (the user's choice of 2026-11-17, CJK in mind; 15 as the middle control live). The probe reads up to 30 ink boxes
# through its own limit; the shared _TRYSHAPEBOX_MAX_SHAPES stays 20. Timing keys are checked for presence and type only (their values vary).
print("\n==== v0.173 /debug/trycomponent: 30 components, the probe's own box limit, timing ====")
R30 = "%2B".join([R3] * 10)
d = tca5("2450a build of 30 glyphs            ", "&step=build&recipe=" + R30 + "&go=yes", recipe="+".join(["cppsrc+cppsrc2+cppsrc3"] * 10), auto=True,
         legacy_nodes=110)
print("2450b  components, timing keys       :", len(d.get("target_elements_after") or []), type(d.get("build_seconds")).__name__,
      type(d.get("elapsed_seconds")).__name__, d.get("build_seconds", -1) >= 0, d.get("elapsed_seconds", -1) >= d.get("build_seconds", 0))
_thirty = lambda: [_tc_comp("cppsrc")] + [_tc_comp("cppsrc", 10 * k, 0) for k in range(1, 30)]
d = tce5("2451a 30: element 29 to (0, 50)     ", "&how=assign&element=29&dx=0&dy=50&go=yes", _thirty, 90)
print("2451b  boxes read, timing key        :", len(d.get("ink_boxes_before") or []), len(d.get("ink_boxes_after") or []),
      type(d.get("elapsed_seconds")).__name__, "| no build_seconds on an offset:", "build_seconds" not in d)
tce5("2451c 30: element 0 to (5, 0)       ", "&how=assign&element=0&dx=5&dy=0&go=yes", _thirty, 90)
d = tce5("2451d a refusal is timed too        ", "&how=assign&element=29&dx=0&dy=0&go=yes", lambda: _tc_two(), 7)
print("2451e  timing key on a refusal       :", type(d.get("elapsed_seconds")).__name__)
class _TC21:
    def __init__(s, n): s.shapes = [_tc_comp("cppsrc", k, 0) for k in range(n)]
_r21, _w21 = ns["_tryshapebox_boxes"](_TC21(21))
_r31 = ns["_trycomp_all_boxes"](_TC21(31))
print("2452 v0.174: the shared reader has no limit:", len(_r21 or []), _w21, "| 31 for the probe:", len(_r31) if isinstance(_r31, list) else _r31,
      "| caps gone:", "_TRYSHAPEBOX_MAX_SHAPES" not in ns, "_COMPONENT_BOX_MAX" not in ns, "max_shapes" not in src.split("def _tryshapebox_boxes(")[1][:400])
# ---- v0.174: add_component's list form (POST /glyph/component with "components"; the user's design of 2026-11-17). The build fake of
# v0.165 places every recipe glyph at identity (build_offset: at (30, 0)); here the transform setter can fail at its N-th call
# (tx_fail_at), the build can return the list reversed (build_reverse), and the width write-back can fail (width_set_raises).
print("\n==== v0.174 add_component: the components list ====")
_tc_build165 = TCLayer.buildAuto
def _tc_build174(s):
    r = _tc_build165(s)
    if TC["mode"].get("build_reverse"): s._shapes.reverse()
    if "build_drop" in TC["mode"]: s._shapes.pop(TC["mode"]["build_drop"])      # v0.175: FontLab drops one entry (AC2 1200-1208)
    return r
TCLayer.buildAuto = _tc_build174
def _tc_set_tx174(s, v):
    TC["tx_calls"] = TC.get("tx_calls", 0) + 1
    if TC["mode"].get("tx_fail_at") == TC["tx_calls"]: TC["calls"].append("shape.transform="); raise RuntimeError("transform boom")
    _tc_set_tx(s, v)
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx174)
_p72_adv = P72Mod.__dict__["advanceWidth"]
def _p72_adv_set174(s, v):
    if TC["mode"].get("width_set_raises"): P72["calls"].append(("advanceWidth", s.name, v)); raise RuntimeError("width boom")
    _p72_adv.fset(s, v)
P72Mod.advanceWidth = property(_p72_adv.fget, _p72_adv_set174)
LK = ("form", "component_count", "placed", "verified", "changed", "steps_done", "build_returned", "cleanup", "checks", "untested_size",
      "untested_size_note", "reason", "error", "component_found")
def acl(tag, payload, mode=None, auto=False, recipe="", legacy_nodes=3, keys=LK):
    ac_setup(mode, auto, recipe)
    _tc_src45(); TC["tx_calls"] = 0
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    c, d = sbpost("/glyph/component", payload)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform")],
          "| widths", [x for x in P72["calls"] if x[0] == "advanceWidth"], "| marks", TE["marks"])
    if isinstance(d.get("component_states"), list):
        print("      states:", [(x["component"], x["x"], x["y"], x["state"]) for x in d["component_states"]], "| timing keys:",
              type(d.get("elapsed_seconds")).__name__, type(d.get("build_seconds")).__name__)
    return d
def L(*items): return {"name": "cpp1", "components": [{"component": c, "x": x, "y": y} for c, x, y in items]}
L2 = L(("cppsrc", 0, 0), ("cppsrc2", 0, 0))
for tag, payload in (("2460a an empty list                ", {"name": "cpp1", "components": []}),
                     ("2460b components not a list        ", {"name": "cpp1", "components": "cppsrc"}),
                     ("2460c both forms                   ", dict(L2, component="cppsrc")),
                     ("2460d an entry without y           ", {"name": "cpp1", "components": [{"component": "cppsrc", "x": 0}]}),
                     ("2460e an entry x 1.5               ", L(("cppsrc", 1.5, 0))),
                     ("2460f an entry x 10001             ", L(("cppsrc", 10001, 0))),
                     ("2460g a name with +                ", L(("cppsrc+cppsrc2", 0, 0))),
                     ("2460h confirmed not a bool         ", dict(L2, confirmed_untested_size="yes")),
                     ("2460i the target in the list       ", L(("cppsrc", 0, 0), ("cpp1", 0, 0)))):
    acl(tag, payload)
acl("2460j a missing source              ", L(("cppsrc", 0, 0), ("cppnone", 0, 0)))
acl("2460k a source with a component     ", L(("cppsrc", 0, 0), ("cppcomp", 0, 0)))
d = acl("2461 two at (0, 0)                  ", L2, legacy_nodes=7)
print("2461a  elements, width, count, sync:", tc_elements(d, "elements_after"), d.get("advance_width_before"), d.get("advance_width_after"),
      d.get("glyph_count_before"), d.get("glyph_count_after"), "| synced", d.get("synced_with_fontlab"))
acl("2461b FontLab offsets them (30, 0)  ", L(("cppsrc", 0, 0), ("cppsrc2", 120, 40)), mode={"build_offset": 1}, legacy_nodes=7)
acl("2461c FontLab sets the width 250    ", L2, mode={"build_width": 1}, legacy_nodes=7)
acl("2461d a repeated source, three      ", L(("cppsrc", 0, 0), ("cppsrc", 150, 0), ("cppsrc", -200, 0)), mode={"build_offset": 1}, legacy_nodes=9)
d = acl("2461e 30 entries                    ", L(*[("cppsrc", 10 * k, 0) for k in range(30)]), legacy_nodes=90)
print("2461f  30: placed, states:", d.get("placed"), len(d.get("component_states") or []), "| boxes read for the check:", TC["calls"].count("inkBox"))
acl("2462a 31 entries, not confirmed     ", L(*[("cppsrc", 10 * k, 0) for k in range(31)]))
d = acl("2462b 31 entries, confirmed         ", dict(L(*[("cppsrc", 10 * k, 0) for k in range(31)]), confirmed_untested_size=True), legacy_nodes=93)
acl("2462c 30 entries, confirmed anyway  ", dict(L(*[("cppsrc", 10 * k, 0) for k in range(30)]), confirmed_untested_size=True), legacy_nodes=90)
L3 = L(("cppsrc", 0, 0), ("cppsrc2", 0, 0), ("cppsrc3", 0, 0))
for tag, pl, mode in (("2463a buildAuto returns False       ", L2, {"build_false": 1}),
                      ("2463b buildAuto raises              ", L2, {"build_raises": 1}),
                      ("2463c the built order differs       ", L2, {"build_reverse": 1}),
                      ("2463d offset 1 of 2 fails           ", L2, {"build_offset": 1, "tx_fail_at": 2}),
                      ("2463e offset 1 of 3 fails, 2 not reached", L3, {"build_offset": 1, "tx_fail_at": 2}),
                      ("2463f the width write-back fails    ", L2, {"build_width": 1, "width_set_raises": 1}),
                      ("2463g offset 0 and the width fail   ", L2, {"build_width": 1, "build_offset": 1, "tx_fail_at": 1, "width_set_raises": 1}),
                      ("2463h clearing the recipe fails     ", L2, {"clear_raises": 1}),
                      ("2463i a box not where its matrix says", L(("cppsrc", 0, 0), ("cppsrc2", 120, 40)), {"build_offset": 1, "box_stale": 1}),
                      ("2463j a source changes with the offset", L(("cppsrc", 0, 0), ("cppsrc2", 120, 40)), {"build_offset": 1, "offset_source": 1})):
    acl(tag, pl, mode=mode, legacy_nodes=11 if pl is L3 else 7)
ac_setup(); _tc_src45(); P72["layers"]["cpp1"]._shapes = [TCShape([te_contour(TE_SQ)])]; P72["layers_unreadable"] = {"cpp1"}     # v0.187: as before
c, d = sbpost("/glyph/component", L2); print("2464 a target that is not empty   :", c, d.get("placed"), d.get("reason"), "| writes", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform") and x != "inkBox"])
P72["layers_unreadable"] = set()
ac_setup(auto=True); _tc_src45()
c, d = sbpost("/glyph/component", L2); print("2464b autoLayer on                 :", c, d.get("placed"), d.get("reason"), "| writes", [x for x in TC["calls"] if not (isinstance(x, tuple) and x[0] == "QTransform") and x != "inkBox"])
class _OW:
    def __init__(s, n): s.activeLayer = type("L", (), {})(); s.activeLayer.shapes = [_tc_comp("cppsrc", k, 0) for k in range(n)]
ac_setup(); _tc_src45()
_ents = [{"is_component": True, "component_glyph": "cppsrc", "component_layer": "test_font"} for _k in range(21)]
_secs = ns["_add_component_boxes"](_OW(21), None, _ents)
print("2464c outline boxes, 21 components:", sum(1 for e in _ents if "error" not in e.get("ink_box", {"error": 1})), "of 21 boxed | lefts", [e["ink_box"].get("left") for e in _ents][:3],
      "| seconds a float:", type(_secs).__name__, "| none for no component:", ns["_add_component_boxes"](_OW(0), None, []))
_srcl = "\n".join(l for l in src[src.index('# POST /glyph/component with "components" (v0.174)'):src.index("# add_component into a glyph that is NOT empty (v0.186")].split("\n")
                  if not l.lstrip().startswith("#"))     # v0.186: up to the temporary-layer route, which has its own scan (2590)
_acl = _srcl[_srcl.index("def add_components("):]
print("2465 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addComponent|clearComponents|killAuto|decomposite|removeShape|replaceShape|addShape|applyTransform)\s*\(|font\.update|_ensure_modern_layer|create_layer=True", _srcl),
      "| every refusal before the first write:", _acl.rindex("nothing was changed") < _acl.index('layer.recipe = "+".join(names)'),
      "| write statements:", [len(_re83.findall(r"(?m)^\s+" + x, _acl)) for x in (r'layer\.recipe = "\+"\.join\(names\)$', r"layer\.autoLayer = True$",
                                                                                 r"ret = layer\.buildAuto\(\)$", r"layer\.autoLayer = False$",
                                                                                 r"shapes\[i\]\.transform = ", r'layer\.recipe = ""$', r"w\.advanceWidth = width_before$")],
      "| soft limit:", ns["_COMP_SOFT_LIMIT"], "| route documented:", '"components": [{"component", "x", "y"}, ...], "confirmed_untested_size"' in src)
# ---- v0.175: an underscore name is refused before anything is touched (FontLab reads "a_b" as a ligature, AC2u 1216-1235), states by
# source name when the build leaves a different number of elements (build_drop: the fake drops the element at that index), components_after.
print("\n==== v0.175 add_component: underscore names, states after a dropped entry, components_after ====")
LK175 = LK + ("underscore_refused", "components_after")
for tag, pl in (("2466a an underscore in the middle   ", L(("cppsrc", 0, 0), ("cpp_x", 0, 0))),
                ("2466b a leading underscore          ", L(("cppsrc", 0, 0), ("_cppx", 0, 0))),
                ("2466c a trailing underscore, first  ", L(("cppx_", 0, 0), ("cppsrc", 0, 0))),
                ("2466d one entry with an underscore  ", L(("cpp_x", 0, 0)))):
    acl(tag, pl, keys=LK175)
acl("2466e 31 entries, one with _, unconfirmed", L(*([("cppsrc", 10 * k, 0) for k in range(30)] + [("cpp_x", 0, 0)])), keys=LK175)
d = acl("2467a two, the build drops the second", L(("cppsrc", 0, 0), ("cppsrc2", 500, 0)), mode={"build_drop": 1}, legacy_nodes=7, keys=LK175)
d = acl("2467b two, the build drops the first ", L(("cppsrc2", 500, 0), ("cppsrc", 0, 0)), mode={"build_drop": 0}, legacy_nodes=7, keys=LK175)
d = acl("2467c three, the middle one dropped ", L3, mode={"build_drop": 1}, legacy_nodes=11, keys=LK175)
d = acl("2467d a repeat, one copy dropped    ", L(("cppsrc", 0, 0), ("cppsrc", 150, 0), ("cppsrc2", 0, 0)), mode={"build_drop": 0, "build_offset": 1},
        legacy_nodes=11, keys=LK175)
d = acl("2467e placed: no components_after  ", L2, legacy_nodes=7, keys=LK175)
_ca = ns["_comp_after"]
print("2467f components_after directly:", _ca({"error": "boom"}), "|", _ca({}), "|",
      _ca([{"is_component": False}, {"is_component": "<error: x>", "component_glyph": "a"}, {"is_component": True, "component_glyph": "<error: y>"},
           {"is_component": True, "component_glyph": "g", "matrix": {"error": "no"}},
           {"is_component": True, "component_glyph": "g", "matrix": {"m11": 2.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 5.0, "dy": -3.0}},
           {"is_component": True, "component_glyph": "g", "matrix": {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 5, "dy": 0.0}}]))
_srcl175 = "\n".join(l for l in src[src.index('# POST /glyph/component with "components" (v0.174)'):src.index("# /debug/tryedit (v0.151)")].split("\n")
                     if not l.lstrip().startswith("#"))
_acl175 = _srcl175[_srcl175.index("def add_components("):]
print("2468 underscore refusal before the limit and every read:", _acl175.index('if "_" in n') < _acl175.index("_COMP_SOFT_LIMIT") < _acl175.index("_modern_edit_target(name)"),
      "| spies:", TC_FORBIDDEN, "| route documented:", 'a name with "_" is refused (v0.175)' in src)
TCLayer.buildAuto = _tc_build165
P72Mod.advanceWidth = _p72_adv
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx)
TCShape.transform = property(_tc_tx_prop.fget, _tc_set_tx)
# ---- v0.176: the remove stages of /debug/trycomponent (research for removing a component, the user's choice of 2026-11-17). The fake
# layer's removeShape drops the shape it is given and clearComponents every component; the modes below add what could go wrong.
print("\n==== v0.176 /debug/trycomponent: removeshape and clearcomponents ====")
def _tc_rm_effects(s):
    m = TC["mode"]
    if m.get("rm_other") and s._shapes: s._shapes = s._shapes[1:]
    if m.get("rm_moves_other") and s._shapes: s._shapes[0]._tx = TCQT(1, 0, 0, 1, s._shapes[0]._tx.dx() + 5, s._shapes[0]._tx.dy())
    if m.get("rm_source"): TCSRC["cppsrc"]._contours[0].rows[0]["x"] += 1.0
    if m.get("rm_width"): P72["widths"]["cpp1"] = 500.0
    if m.get("rm_glyph"): TS["cppnew"] = TsGlyph("cppnew", [])
    if m.get("rm_auto"): s.__dict__["_auto"] = True
    if m.get("rm_drops_layer"): P72["layers"].pop(s._glyph, None)
    if not m.get("rm_legacy_stale"):     # the legacy view follows, as after FontLab's own sync
        _w = TS[s._glyph].width; TS[s._glyph] = TsGlyph(s._glyph, [TsLayer(1, sum(len(c.rows) for k in s._shapes for c in k._contours))])
        TS[s._glyph].width = _w
def _tc_remove_shape(s, shape, recursive=True):
    m = TC["mode"]
    TC["calls"].append(("removeShape", type(shape).__name__, recursive))
    if m.get("rm_raises"): raise RuntimeError("removeShape boom")
    if m.get("rm_ignored"): return None
    s._shapes = [k for k in s._shapes if k is not shape]
    _tc_rm_effects(s)
    return True if m.get("rm_true") else None
def _tc_clear_components(s):
    m = TC["mode"]
    TC["calls"].append("clearComponents")
    if m.get("rm_raises"): raise RuntimeError("clearComponents boom")
    if m.get("rm_ignored"): return None
    s._shapes = [k for k in s._shapes if not k._component]
    _tc_rm_effects(s)
    return None
TCLayer.removeShape = _tc_remove_shape
TCLayer.clearComponents = _tc_clear_components
RK = ("element", "recursive", "call_returned", "layer_kept", "elements_as_expected", "others_kept", "empty_after", "source_changed",
      "changed", "side_effect_detected", "removed", "error", "calls_so_far")
QR = QC + "stage=removeshape&target=cpp1"
QX = QC + "stage=clearcomponents&target=cpp1"
def tcr(tag, q, mode=None, auto=False, shapes=None, legacy_nodes=7):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {})))
    _tc_src3()
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = ""; lay.__dict__["_auto"] = auto
    lay._shapes = shapes() if callable(shapes) else (shapes if shapes is not None else _tc_two())
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    d = tc(tag, q, keys=RK)
    lefts = lambda k: [b.get("left") for b in d[k]] if isinstance(d.get(k), list) else d.get(k)
    print("      elements after:", tc_elements(d, "target_elements_after"), "| lefts:", lefts("ink_boxes_before"), "->", lefts("ink_boxes_after"),
          "| widths:", d.get("advance_width_before"), d.get("advance_width_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
R1 = "&element=1&recursive=0"
for tag, q in (("2470a removeshape shown before go   ", QR + R1),
               ("2470b no element                   ", QR + "&recursive=0&go=yes"),
               ("2470c no recursive                 ", QR + "&element=1&go=yes"),
               ("2470d recursive=2                  ", QR + "&element=1&recursive=2&go=yes"),
               ("2470e element 30                   ", QR + "&element=30&recursive=0&go=yes"),
               ("2470f element -1                   ", QR + "&element=-1&recursive=0&go=yes"),
               ("2470g clearcomponents shown before go", QX),
               ("2470h clearcomponents with element ", QX + "&element=0&go=yes"),
               ("2470i clearcomponents with recursive", QX + "&recursive=1&go=yes"),
               ("2470j a source given               ", QR + R1 + "&source=cppsrc&go=yes"),
               ("2470k dx given                     ", QR + R1 + "&dx=5&go=yes"),
               ("2470l how given                    ", QX + "&how=assign&go=yes"),
               ("2470m target not a cpp glyph       ", QC + "stage=removeshape&target=A&element=0&recursive=0&go=yes"),
               ("2470n an unknown stage             ", QC + "stage=remove&target=cpp1&go=yes")):
    tcr(tag, q)
tc_gen_setup(); tc("2470o recursive with stage=offset ", QO + "&how=assign&dx=1&dy=1&recursive=1&go=yes")
d = tcr("2471 the second of two, recursive 0 (plan 1241)", QR + R1 + "&go=yes")
print("2471a  outline, sources kept, sync, timing:", te_outline(d, "target_after"), d.get("source_changed"), "| synced", d.get("synced_with_fontlab"),
      "| state", {k: d.get("target_state_after", {}).get(k) for k in ("shapes", "components")}, "| timing a float:", type(d.get("elapsed_seconds")).__name__)
tcr("2471b the first of two, recursive 1 (plan 1243)", QR + "&element=0&recursive=1&go=yes")
tcr("2471c one source twice, the first (plan 1244)", QR + "&element=0&recursive=0&go=yes",
    shapes=lambda: [_tc_comp("cppsrc"), _tc_comp("cppsrc", 300, 0)], legacy_nodes=6)
tcr("2471d the only component (plan 1245)", QR + "&element=0&recursive=0&go=yes", shapes=lambda: [_tc_comp("cppsrc2", -200, 0)], legacy_nodes=4)
tcr("2471e three, the middle one        ", QR + R1 + "&go=yes", shapes=lambda: _tc_two() + [_tc_comp("cppsrc3")], legacy_nodes=11)
tcr("2472 clearcomponents, three (plan 1246)", QX + "&go=yes", shapes=lambda: _tc_two() + [_tc_comp("cppsrc3")], legacy_nodes=11)
for tag, q, kw in (("2473a autoLayer on                  ", QR + R1 + "&go=yes", dict(auto=True)),
                   ("2473b a plain contour among them    ", QR + R1 + "&go=yes", dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)])])),
                   ("2473c a component of a non-cpp glyph", QX + "&go=yes", dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)], component="A")])),
                   ("2473d element 2 of two              ", QR + "&element=2&recursive=0&go=yes", {}),
                   ("2473e the shape at 1 names another  ", QR + R1 + "&go=yes", dict(shapes=lambda: _flip())),
                   ("2473f an empty layer                ", QX + "&go=yes", dict(shapes=[])),
                   ("2473g 31 components                 ", QX + "&go=yes", dict(shapes=lambda: _tc_two() + [_tc_comp("cppsrc", 10 * k, 0) for k in range(1, 30)],
                                                                                legacy_nodes=7 + 3 * 29)),
                   ("2473h an ink box unreadable         ", QR + R1 + "&go=yes", dict(mode={"box_raises": 1}))):
    tcr(tag, q, **kw)
tc_gen_setup(); tc("2473i target with no layer          ", QC + "stage=removeshape&target=cppnolayer&element=0&recursive=0&go=yes")
tc_gen_setup(count=2); tc("2473j two fonts open               ", QR + R1 + "&go=yes")
print("2473k  no remove call in the refusals:", [x for x in TC["calls"] if x == "clearComponents" or (isinstance(x, tuple) and x[0] == "removeShape")])
for tag, q, mode in (("2474a removeShape ignored           ", QR + R1 + "&go=yes", {"rm_ignored": 1}),
                     ("2474b removeShape raises            ", QR + R1 + "&go=yes", {"rm_raises": 1}),
                     ("2474c another component goes too    ", QR + R1 + "&go=yes", {"rm_other": 1}),
                     ("2474d the other component moves     ", QR + R1 + "&go=yes", {"rm_moves_other": 1}),
                     ("2474e a source changes              ", QR + R1 + "&go=yes", {"rm_source": 1}),
                     ("2474f the width changes             ", QR + R1 + "&go=yes", {"rm_width": 1}),
                     ("2474g a glyph appears               ", QR + R1 + "&go=yes", {"rm_glyph": 1}),
                     ("2474h autoLayer turns on            ", QR + R1 + "&go=yes", {"rm_auto": 1}),
                     ("2474i removeShape returns True      ", QR + R1 + "&go=yes", {"rm_true": 1}),
                     ("2474j clearComponents ignored       ", QX + "&go=yes", {"rm_ignored": 1}),
                     ("2474k clearComponents raises        ", QX + "&go=yes", {"rm_raises": 1}),
                     ("2474l clearComponents, a source changes", QX + "&go=yes", {"rm_source": 1}),
                     ("2474m the legacy view stays behind  ", QR + R1 + "&go=yes", {"rm_legacy_stale": 1}),
                     ("2474n the layer disappears          ", QX + "&go=yes", {"rm_drops_layer": 1})):
    tcr(tag, q, mode=mode)
tc_gen_setup()
for _i in range(6): call(QC + "stage=removeshape&target=cppnolayer&element=0&recursive=0&go=yes")
tc("2475 the limit: call 7 is refused   ", QX + "&go=yes")
_srcrm = "\n".join(l for l in src[src.index("# /debug/trycomponent remove stages (v0.176)"):src.index("# /debug/trycomponent (v0.155)")].split("\n")
                   if not l.lstrip().startswith("#"))
print("2476 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|removeAllShapes|decomposite|replaceShape|addShape|addComponent|setGlyphComponents|applyTransform|buildAuto|killAuto|remove)\s*\(|font\.update|autoLayer =|recipe =|transform =", _srcrm),
      "| one call each:", [len(_re83.findall(r"(?m)^\s+ret = layer\." + c + "$", _srcrm)) for c in (r"removeShape\(shape, recursive\)", r"clearComponents\(\)")],
      "| counter before the read:", _srcrm.index('_TRYCOMP["calls"] += 1') < _srcrm.index("return _trycomp_remove("),
      "| every refusal before the call:", _srcrm.rindex("nothing was touched") < _srcrm.index("ret = layer.removeShape("),
      "| route documented:", "stage=removeshape&target=cpp...&element=I&recursive=0|1" in src, "| dispatched:", '(query.get("recursive") or [None])[0]' in src)
# ---- v0.177: the modern state counts the shapes flagged isComponent ("components"); FontLab's componentsCount() is kept apart as
# "fontlab_components_count", information and a guard (it read 0 on glyphs holding components, RM 1241-1246). TCLayer0 answers
# componentsCount() with 0, as FontLab did.
print("\n==== v0.177 the component count of a modern state ====")
class _W177:
    def __init__(s, layer): s.activeLayer = layer
class TCLayer0(TCLayer):
    def componentsCount(s): return 0
class TCLayerNoCount(TCLayer):
    def componentsCount(s): raise RuntimeError("count boom")
class TCLayerShapesSpy(TCLayer0):
    @property
    def shapes(s): TC["calls"].append("layer.shapes"); raise RuntimeError("shapes boom")
class TCLayerTwo(TCLayer):
    def componentsCount(s): return 2
class TCShapeBadFlag(TCShape):
    def isComponent(s):
        if TC["mode"].get("flag_int"): return 1
        raise RuntimeError("flag boom")
def st177(tag, shapes, layer_cls=TCLayer0, te_mode=None, tc_mode=None):
    tc_gen_setup(); _tc_src3()
    TE["mode"].update(te_mode or {}); TC["mode"].update(tc_mode or {})
    st, _layer = ns["_tryshape_modern_state"](_W177(layer_cls("test_font", shapes() if callable(shapes) else shapes, "cpp1")))
    print(tag, ":", {k: st.get(k) for k in ("shapes", "fontlab_components_count", "fontlab_components_count_error", "components") if k in st},
          "| has components:", ns["_state_has_components"](st), "| known empty:", ns["_tryshape_modern_known_empty"](st),
          "| layer.shapes read:", "layer.shapes" in TC["calls"])
    return st
st177("2480a two component shapes, FontLab reads 0", lambda: [_tc_comp("cppsrc"), _tc_comp("cppsrc2", 500, 0)])
st177("2480b one plain shape                   ", lambda: [TCShape([te_contour(TE_SQ)])])
st177("2480c a component among plain shapes    ", lambda: [TCShape([te_contour(TE_SQ)]), _tc_comp("cppsrc3")])
st177("2480d no shape: layer.shapes not read   ", [], layer_cls=TCLayerShapesSpy)
st177("2480e layer.shapes raises (one shape)   ", lambda: [TCShape([te_contour(TE_SQ)])], layer_cls=TCLayerShapesSpy)
st177("2480f layer.shapes a tuple              ", lambda: [TCShape([te_contour(TE_SQ)])], te_mode={"shapes_tuple": 1})
st177("2480g isComponent raises                ", lambda: [TCShape([te_contour(TE_SQ)]), TCShapeBadFlag([te_contour(TE_SQ)])])
st177("2480h isComponent returns 1, not a bool ", lambda: [TCShapeBadFlag([te_contour(TE_SQ)])], tc_mode={"flag_int": 1})
st177("2480i FontLab's count raises            ", lambda: [TCShape([te_contour(TE_SQ)])], layer_cls=TCLayerNoCount)
st177("2480j FontLab counts 2, no shape flagged", lambda: [TCShape([te_contour(TE_SQ)]), TCShape([te_contour(TE_SQ)])], layer_cls=TCLayerTwo)
_hc = ns["_state_has_components"]
print("2481 the guard: both 0", _hc({"components": 0, "fontlab_components_count": 0}), "| shapes 1", _hc({"components": 1, "fontlab_components_count": 0}),
      "| FontLab 1", _hc({"components": 0, "fontlab_components_count": 1}), "| a count missing", _hc({"components": 0}),
      "| unreadable", _hc({"components": "not readable: x", "fontlab_components_count": 0}))
print("2481a refusal text:", ns["_state_components_text"]({"components": 2, "fontlab_components_count": 0}), "|",
      ns["_state_components_text"]({"components": 0, "fontlab_components_count_error": "RuntimeError: count boom"}))
_src177 = "\n".join(l.split("#")[0] for l in src.splitlines())
print("2482 static: guards on the old count:", len(_re83.findall(r'\b(?:state|sstate|after_state)\.get\("components"\) != 0', _src177)),
      "| componentsCount() read only by the state loop:", _re83.findall(r'"componentsCount"\)', _src177),
      "| guards through the helper:", len(_re83.findall(r"_state_has_components\(", _src177)) - 1,
      "| outline reply uses the state count:", "component_count=state.get(\"components\")" in _src177)
# ---- v0.178: add_component's single form gets the list form's clean-up (the width written back, a leftover recipe cleared); both forms
# report width_set_by_build (live 1250: the single form left .notdef at width 0 after FontLab's build, not 500).
print("\n==== v0.178 add_component: the single form writes the width back; width_set_by_build ====")
P72Mod.advanceWidth = property(_p72_adv.fget, _p72_adv_set174)
AK178 = ("placed", "verified", "changed", "steps_done", "width_set_by_build", "cleanup", "checks", "reason")
d = ac("2490a FontLab sets the width 250     ", P0, mode={"build_width": 1}, keys=AK178)
print("      width before / after:", d.get("advance_width_before"), d.get("advance_width_after"))
ac("2490b ... and the write-back fails   ", P0, mode={"build_width": 1, "width_set_raises": 1}, keys=AK178)
ac("2490c buildAuto raises: recipe cleared", P0, mode={"build_raises": 1}, keys=AK178)
ac("2490d clearing the recipe raises twice", P0, mode={"clear_raises": 1}, keys=AK178)
ac("2490e the width unchanged: no field  ", P0, keys=AK178)
ac("2490f an offset, FontLab sets 250    ", dict(P0, x=100, y=50), mode={"build_width": 1}, keys=AK178)
acl("2491a list: FontLab sets 250        ", L2, mode={"build_width": 1}, legacy_nodes=7, keys=LK + ("width_set_by_build",))
acl("2491b list: the width unchanged     ", L2, legacy_nodes=7, keys=LK + ("width_set_by_build",))
P72Mod.advanceWidth = _p72_adv
_srcac178 = "\n".join(l for l in src[src.index("# POST /glyph/component (v0.169)"):src.index('# POST /glyph/component with "components" (v0.174)')].split("\n")
                      if not l.lstrip().startswith("#"))
_acf178 = _srcac178[_srcac178.index("def add_component("):]
print("2492 single form: the write-back before the re-read:", _acf178.index("w.advanceWidth = width_before") < _acf178.index("width_after = _trycomp_width(w)"),
      "| only when the recipe was set:", 'if "recipe" in done and width_now != width_before:' in _acf178,
      "| width_unchanged still checked:", '"width_unchanged": width_after == width_before' in _acf178,
      "| spies:", TC_FORBIDDEN)
# ---- v0.179: POST /glyph/component/remove (remove_component; the user's design of 2026-11-18). The removeShape fake of v0.176 and its
# rm_* modes stay; TCShape gains contoursCount (cc_raises, cc_off), and rm_fail_at makes the n-th removeShape call raise.
print("\n==== v0.179 POST /glyph/component/remove (remove_component) ====")
def _tc_ccount(s):
    if TC["mode"].get("cc_raises"): raise RuntimeError("contoursCount boom")
    return len(s._contours) + (1 if TC["mode"].get("cc_off") else 0)
TCShape.contoursCount = _tc_ccount
def _tc_remove_shape179(s, shape, recursive=True):
    TC["rm_calls"] = TC.get("rm_calls", 0) + 1
    if TC["mode"].get("rm_fail_at") == TC["rm_calls"]:
        TC["calls"].append(("removeShape", type(shape).__name__, recursive)); raise RuntimeError("removeShape boom")
    return _tc_remove_shape(s, shape, recursive)
TCLayer.removeShape = _tc_remove_shape179
P72Mod.advanceWidth = property(_p72_adv.fget, _p72_adv_set174)
RMK = ("form", "removed", "verified", "changed", "removal_order", "removed_calls", "calls_returned", "entry_states", "checks", "recipe_kept",
       "width_changed_by_removal", "cleanup", "empty_after", "failed_index", "reason", "error")
def rmc(tag, payload, mode=None, auto=False, recipe="", shapes=None, legacy_nodes=7, keys=RMK):
    tc_gen_setup(mode=dict(mode or {})); _tc_src3(); TC["rm_calls"] = 0
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = recipe; lay.__dict__["_auto"] = auto
    lay._shapes = shapes() if callable(shapes) else (shapes if shapes is not None else _tc_two())
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, legacy_nodes)]); TS["cpp1"].width = 0.0
    c, d = sbpost("/glyph/component/remove", payload)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d},
          "| calls", [x for x in TC["calls"] if x == "clearComponents" or (isinstance(x, tuple) and x[0] in ("removeShape", "recipe=", "autoLayer="))],
          "| Update", TE["updates"], "| marks", TE["marks"])
    if "components_after" in d:
        print("      after:", d.get("components_after"), "| widths:", d.get("advance_width_before"), d.get("advance_width_after"),
              "| timing a float:", type(d.get("elapsed_seconds")).__name__)
    return d
R0 = {"name": "cpp1", "index": 1, "component": "cppsrc2", "x": -200, "y": 0}
RL = {"name": "cpp1", "components": [{"index": 0, "component": "cppsrc", "x": 0, "y": 0}, {"index": 1, "component": "cppsrc2", "x": -200, "y": 0}]}
_e = lambda i, c, x=0, y=0: {"index": i, "component": c, "x": x, "y": y}
for tag, payload in (("2500a no index                     ", {k: v for k, v in R0.items() if k != "index"}),
                     ("2500b an extra key                 ", dict(R0, recursive=1)),
                     ("2500c index -1                     ", dict(R0, index=-1)),
                     ("2500d index a bool                 ", dict(R0, index=True)),
                     ("2500e index 1.0                    ", dict(R0, index=1.0)),
                     ("2500f component empty              ", dict(R0, component=" ")),
                     ("2500g x a string                   ", dict(R0, x="0")),
                     ("2500h x 20001                      ", dict(R0, x=20001)),
                     ("2500i empty name                   ", dict(R0, name="")),
                     ("2500j an empty list                ", {"name": "cpp1", "components": []}),
                     ("2500k list and index together      ", dict(RL, index=0)),
                     ("2500l an index twice               ", {"name": "cpp1", "components": [_e(0, "cppsrc"), _e(0, "cppsrc")]}),
                     ("2500m an entry without y           ", {"name": "cpp1", "components": [{"index": 0, "component": "cppsrc", "x": 0}]}),
                     ("2500n the list not a list          ", {"name": "cpp1", "components": {"index": 0}})):
    rmc(tag, payload)
c, d = ns["_route"]("POST", "/glyph/component/remove", b"{not json").partition(b"\r\n\r\n")[0][9:12], None
print("2500o not JSON                     :", c)
d = rmc("2501 single: the second of two      ", R0, legacy_nodes=7)
print("2501a  shapes after, sync, recipe_kept present, mark:", d.get("state_after", {}).get("shapes"),
      d.get("synced_with_fontlab"), "recipe_kept" in d, "|", d.get("fontlab_changed_mark"))
rmc("2501b single: the first, (0, 0)     ", dict(R0, index=0, component="cppsrc", x=0))
rmc("2501c a fractional offset           ", dict(R0, x=-199.5), shapes=lambda: [_tc_comp("cppsrc"), _tc_comp("cppsrc2", -199.5, 0)])
d = rmc("2502 list: 0 and 2 of three          ", {"name": "cpp1", "components": [_e(0, "cppsrc"), _e(2, "cppsrc3")]},
        shapes=lambda: _tc_two() + [_tc_comp("cppsrc3")], legacy_nodes=11)
rmc("2502a list: both of two            ", RL)
rmc("2502b list given 1 then 0           ", {"name": "cpp1", "components": list(reversed(RL["components"]))})
rmc("2502c one source twice, the second  ", dict(R0, component="cppsrc", x=300), shapes=lambda: [_tc_comp("cppsrc"), _tc_comp("cppsrc", 300, 0)], legacy_nodes=6)
rmc("2503 mixed: the component, contour kept", dict(R0, index=0, component="cppsrc", x=0), shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)])])
rmc("2503a mixed: contour first          ", dict(R0, index=1, component="cppsrc", x=0), shapes=lambda: [TCShape([te_contour(TE_SQ)]), _tc_comp("cppsrc")])
rmc("2504 a leftover recipe is kept      ", R0, recipe="cppsrc+cppsrc2")
d = rmc("2505 31 components, all in one call  ", {"name": "cpp1", "components": [_e(0, "cppsrc"), _e(1, "cppsrc2", -200)] + [_e(k + 1, "cppsrc", 10 * k) for k in range(1, 30)]},
        shapes=lambda: _tc_two() + [_tc_comp("cppsrc", 10 * k, 0) for k in range(1, 30)], legacy_nodes=7 + 3 * 29, keys=("removed", "empty_after", "checks"))
print("2505a  removal order starts / ends:", d.get("removal_order", [None])[:3], d.get("removal_order", [None])[-2:], "| calls", TC.get("rm_calls"))
for tag, payload, kw in (("2506a the source at 1 differs      ", dict(R0, component="cppsrc"), {}),
                         ("2506b the offset at 1 differs      ", dict(R0, x=-199), {}),
                         ("2506c index 2 of two              ", dict(R0, index=2), {}),
                         ("2506d the index holds a contour    ", dict(R0, index=1, component="cppsrc"), dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)])])),
                         ("2506e autoLayer on                 ", R0, dict(auto=True)),
                         ("2506f recipe unreadable            ", R0, dict(mode={"recipe_unreadable": 1})),
                         ("2506g a Power Brush shape among them", dict(R0, index=0, component="cppsrc", x=0),
                          dict(shapes=lambda: [_tc_comp("cppsrc"), TCShape([te_contour(TE_SQ)], composite=True)])),
                         ("2506h target does not exist        ", dict(R0, name="cppzz"), {}),
                         ("2506i target has no layer          ", dict(R0, name="cppnolayer"), {}),
                         ("2506j two masters                  ", R0, dict(mode={"masters": 2})),
                         ("2506k contoursCount raises         ", R0, dict(mode={"cc_raises": 1})),
                         ("2506l contour counts do not add up ", R0, dict(mode={"cc_off": 1})),
                         ("2506m an ink box unreadable        ", R0, dict(mode={"box_raises": 1})),
                         ("2506n the shape names another at the call", R0, dict(shapes=lambda: _flip())),
                         ("2506o one entry of two is wrong    ", {"name": "cpp1", "components": [_e(0, "cppsrc"), _e(1, "cppsrc2", -199)]}, {})):
    rmc(tag, payload, **kw)
tc_gen_setup(); TO["count"] = 0
c, d = sbpost("/glyph/component/remove", R0); print("2506p no font open                 :", c, d)
print("2506q  no remove call in the refusals:", [x for x in TC["calls"] if x == "clearComponents" or (isinstance(x, tuple) and x[0] == "removeShape")])
for tag, payload, mode in (("2507a removeShape ignored           ", R0, {"rm_ignored": 1}),
                           ("2507b removeShape raises            ", R0, {"rm_raises": 1}),
                           ("2507c the second call raises        ", RL, {"rm_fail_at": 2}),
                           ("2507d another component goes too    ", R0, {"rm_other": 1}),
                           ("2507e the other component moves     ", R0, {"rm_moves_other": 1}),
                           ("2507f a source changes              ", R0, {"rm_source": 1}),
                           ("2507g FontLab sets the width 500    ", R0, {"rm_width": 1}),
                           ("2507h ... and the write-back fails  ", R0, {"rm_width": 1, "width_set_raises": 1}),
                           ("2507i a glyph appears               ", R0, {"rm_glyph": 1}),
                           ("2507j autoLayer turns on            ", R0, {"rm_auto": 1}),
                           ("2507k the layer disappears          ", R0, {"rm_drops_layer": 1}),
                           ("2507l the legacy view stays behind  ", R0, {"rm_legacy_stale": 1}),
                           ("2507m removeShape returns True      ", R0, {"rm_true": 1})):
    rmc(tag, payload, mode=mode)
rmc("2507n three, the second call raises: the third not reached", {"name": "cpp1", "components": [_e(0, "cppsrc"), _e(1, "cppsrc2", -200), _e(2, "cppsrc3")]},
    mode={"rm_fail_at": 2}, shapes=lambda: _tc_two() + [_tc_comp("cppsrc3")], legacy_nodes=11,
    keys=("removed", "changed", "removal_order", "removed_calls", "entry_states", "failed_index"))
tc_gen_setup()
print("2508 the function itself, an index past the end:", {k: v for k, v in ns["remove_components"]("cpp1", [_e(5, "cppsrc")], "single").items()
                                                          if k in ("removed", "reason")})
_ok179 = {"open": True, "removed": True, "changed": True, "synced_with_fontlab": True}
for tag, payload, code, reply in (("2509a log, one                ", R0, 200, _ok179),
                                  ("2509b log, a list of two      ", RL, 200, _ok179),
                                  ("2509c log, not done, changed  ", RL, 200, {"open": True, "removed": False, "changed": True, "reason": "x"}),
                                  ("2509d log, refused            ", R0, 400, {"error": "bad"})):
    print(tag, ":", ns["_act_describe_write"]("/glyph/component/remove", payload, code, reply))
_src179 = "\n".join(l for l in src[src.index("# POST /glyph/component/remove (v0.179)"):src.index("# POST /glyph/move (v0.153)")].split("\n")
                    if not l.lstrip().startswith("#"))
print("2510 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|clearComponents|removeAllShapes|decomposite|replaceShape|addShape|addComponent|setGlyphComponents|applyTransform|buildAuto|killAuto)\s*\(|font\.update|autoLayer =|recipe =|transform =", _src179),
      "| one call:", len(_re83.findall(r"= layer\.removeShape\(shapes\[i\], False\)", _src179)), "| no other removeShape call:",
      len(_re83.findall(r"(?m)^[^\"'#]*\blayer\.removeShape\(", _src179)) == 1,
      "| every refusal before the call:", _src179.rindex("nothing was changed") < _src179.index("layer.removeShape("),
      "| highest first:", "sorted((e[\"index\"] for e in entries), reverse=True)" in _src179)
print("2510a route documented:", "POST /glyph/component/remove" in src, "| dispatched:", 'if path == "/glyph/component/remove":' in src,
      "| mark title:", ns["_MARK_TITLES"].get("remove_component"), "| guard kind full:", "remove_component" in ns["_GUARD_FULL_KINDS"],
      "| activity kind:", ns["_ACT_WRITES"].get("/glyph/component/remove"))

# ---- v0.180: stage=auto&nonempty=yes (research for placing components into a glyph that already holds contours, components or both;
# the user's choice of 2026-11-18, route "build in place"). The build fake of v0.165 adds to what the layer holds; build_replaces makes
# it clear the layer first, build_moves_existing moves the first element by 5 units.
print("\n==== v0.180 /debug/trycomponent stage=auto&nonempty=yes ====")
def _tc_build180(s):
    m = TC["mode"]
    if m.get("build_replaces"): s._shapes = []
    r = _tc_build165(s)
    if m.get("build_moves_existing") and s._shapes: s._shapes[0]._tx = TCQT(1, 0, 0, 1, s._shapes[0]._tx.dx() + 5, s._shapes[0]._tx.dy())
    return r
TCLayer.buildAuto = _tc_build180
NK = ("nonempty", "step_took_effect", "outline_changed", "existing_kept", "existing_contours_in_outline", "placed", "component_placed",
      "component_kept", "component_normal", "recipe_cleared", "width_changed_by_build", "side_effect_detected", "existing_note", "error",
      "calls_so_far")
QN = QA + "&nonempty=yes"
def _nk_rows(rows):
    if not isinstance(rows, list): return rows
    return [(r.get("is_component"), r.get("component_glyph"), None if not isinstance(r.get("matrix"), dict) or "error" in r["matrix"]
             else (r["matrix"].get("dx"), r["matrix"].get("dy"))) for r in rows]
def nks(shapes, mode=None, auto=False, recipe="", clear_baseline=True):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {}))); _tc_src3()
    if clear_baseline: ns["_TRYCOMP_BASELINE"].clear()
    lay = P72["layers"]["cpp1"]
    lay.__dict__["_recipe"] = recipe; lay.__dict__["_auto"] = auto
    lay._shapes = shapes()
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, 3)]); TS["cpp1"].width = 0.0
def nk_legacy(nodes, width=0.0):     # the legacy view as FontLab would show it after the build
    TS["cpp1"] = TsGlyph("cpp1", [TsLayer(1, nodes)]); TS["cpp1"].width = width
def nk(tag, q, keys=NK):
    d = tc(tag, QN + q, keys=keys)
    print("      before:", _nk_rows(d.get("existing_before")), "| missing:", _nk_rows(d.get("existing_missing")), "| new:",
          _nk_rows(d.get("new_elements")), "| auto_after:", d.get("auto_after"), "| mark:", d.get("fontlab_changed_mark"))
    return d
_contour = lambda: TCShape([te_contour(TE_SQ)])
nks(lambda: [_contour()])
tc("2520a nonempty with stage=offset     ", QC + "stage=offset&target=cpp1&how=assign&dx=5&dy=0&nonempty=yes&go=yes")
tc("2520b nonempty=Yes                   ", QA + "&step=setrecipe&recipe=cppsrc&nonempty=Yes&go=yes")
tc("2520c nonempty with step=read        ", QA + "&step=read&nonempty=yes&go=yes")
tc("2520d nonempty with step=killauto    ", QA + "&step=killauto&nonempty=yes&go=yes")
tc("2520e shown before go                ", QN + "&step=setrecipe&recipe=cppsrc")
for tag, shapes, mode in (("2520f an empty target               ", lambda: [], None),
                          ("2520g a Power Brush shape           ", lambda: [_contour(), TCShape([te_contour(TE_SQ)], composite=True)], None),
                          ("2520h a component of a non-cpp glyph ", lambda: [_contour(), TCShape([te_contour(TE_SQ)], component="A")], None),
                          ("2520i an ink box unreadable         ", lambda: [_contour()], {"box_raises": 1})):
    nks(shapes, mode=mode); nk(tag, "&step=setrecipe&recipe=cppsrc&go=yes")
print("2520j  no recipe set in the refusals:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] in ("recipe=", "autoLayer=")])
tc("2520k without nonempty a contour is still refused", QA + "&step=setrecipe&recipe=cppsrc&go=yes")
# a contour, the component added beside it: the whole series in one listener run
nks(lambda: [_contour()])
nk("2521a contour: setrecipe            ", "&step=setrecipe&recipe=cppsrc&go=yes")
print("      baseline recorded:", _nk_rows(ns["_TRYCOMP_BASELINE"].get("cpp1", {}).get("elements")))
nk("2521b contour: setauto              ", "&step=setauto&go=yes")
nk_legacy(7)
nk("2521c contour: build, kept          ", "&step=build&recipe=cppsrc&go=yes")
nk("2521d contour: unauto               ", "&step=unauto&go=yes")
nk("2521e contour: clearrecipe          ", "&step=clearrecipe&go=yes")
# the build replaces what was there
nks(lambda: [_contour()], mode={"build_replaces": 1})
nk("2522a replaces: setrecipe           ", "&step=setrecipe&recipe=cppsrc&go=yes")
nk("2522b replaces: setauto             ", "&step=setauto&go=yes")
nk("2522c replaces: build, contour gone ", "&step=build&recipe=cppsrc&go=yes")
nk("2522d replaces: unauto, not marked  ", "&step=unauto&go=yes")
# a component, then a contour and a component with the existing one moved by the build
nks(lambda: [_tc_comp("cppsrc2", -200, 0)])
nk("2523a component: setrecipe          ", "&step=setrecipe&recipe=cppsrc&go=yes")
nk("2523b component: setauto            ", "&step=setauto&go=yes")
nk_legacy(7)
nk("2523c component: build, kept        ", "&step=build&recipe=cppsrc&go=yes")
nks(lambda: [_contour(), _tc_comp("cppsrc2", -200, 0)], mode={"build_moves_existing": 1})
nk("2524a mixed: setrecipe              ", "&step=setrecipe&recipe=cppsrc&go=yes")
nk("2524b mixed: setauto                ", "&step=setauto&go=yes")
nk("2524c mixed: build moves the contour", "&step=build&recipe=cppsrc&go=yes")
# the width FontLab sets is reported, not counted; no baseline; a recipe naming the existing component too
nks(lambda: [_contour()], mode={"build_width": 1}, auto=True, recipe="cppsrc")
ns["_TRYCOMP_BASELINE"]["cpp1"] = {"elements": ns["_trycomp_existing"](P72["layers"]["cpp1"], ns["_trycomp_elements"](P72["layers"]["cpp1"])),
                                   "contours": ns["_tryedit_snapshot"]("cpp1")["contours"]}
nk_legacy(7, 250.0)
d = nk("2525 build sets the width 250      ", "&step=build&recipe=cppsrc&go=yes")
print("      widths:", d.get("advance_width_before"), d.get("advance_width_after"))
nks(lambda: [_contour()], auto=True, recipe="cppsrc")
nk("2526 build with no baseline         ", "&step=build&recipe=cppsrc&go=yes")
nks(lambda: [_tc_comp("cppsrc2", -200, 0)], auto=True, recipe="cppsrc2+cppsrc", clear_baseline=False)
ns["_TRYCOMP_BASELINE"]["cpp1"] = {"elements": ns["_trycomp_existing"](P72["layers"]["cpp1"], ns["_trycomp_elements"](P72["layers"]["cpp1"])),
                                   "contours": ns["_tryedit_snapshot"]("cpp1")["contours"]}
nk_legacy(11)
nk("2527 recipe names the existing too  ", "&step=build&recipe=cppsrc2%2Bcppsrc&go=yes")
nks(lambda: [_contour(), _tc_comp("cppsrc2", -200, 0)], auto=True, recipe="cppsrc")
nk("2528 unauto with a contour present  ", "&step=unauto&go=yes")
nks(lambda: [_contour(), _tc_comp("cppsrc2", -200, 0)], auto=True, recipe="cppsrc")
tc("2528a the same without nonempty      ", QA + "&step=unauto&go=yes")
_src180 = "\n".join(l for l in src[src.index("def _trycomp_auto_state("):src.index("def debug_try_component(")].split("\n") if not l.lstrip().startswith("#"))
print("2529 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|addComponent|clearComponents|removeShape|replaceShape)\s*\(|font\.update", _src180),
      "| baseline written once:", _src180.count("_TRYCOMP_BASELINE[target] ="), "| only at setrecipe:", 'if nonempty and step == "setrecipe":' in _src180,
      "| route documented:", "&nonempty=yes: the same steps on a target" in src, "| dispatched:", '(query.get("nonempty") or [None])[0]' in src)

# ---- v0.181: stage=templayer (research: a temporary layer in the target glyph; the user's route order of 2026-11-18). The modern glyph
# fake gains layers (the working layer plus P72["extra"]), addLayer and removeLayer; flLayer(title) makes an empty TCLayer. Modes:
# add_activates (the new layer becomes active), addlayer_raises / _ignored / _touches, layers_tuple, removelayer_raises / _ignored,
# remove_takes_shapes (removing the layer also removes its shape objects from the working layer: a shared object), addshape_moves
# (addShape takes the shape off the temporary layer), build_working (the build also adds a shape to the working layer).
print("\n==== v0.181 /debug/trycomponent stage=templayer ====")
_p72_active = P72Mod.__dict__["activeLayer"]
def _tl_active_fake(s):
    chosen = P72.get("active_of", {}).get(s.name)          # v0.182: set by the setActive fake
    if chosen is not None and any(chosen is l for l in _tl_layers_fake(s)): return chosen
    ex = P72.get("extra", {}).get(s.name) or []
    if TC["mode"].get("add_activates") and ex: return ex[-1]
    return _p72_active.fget(s)
def _tl_layers_fake(s):
    main = P72["layers"].get(s.name)
    out = ([main] if main is not None else []) + list(P72.get("extra", {}).get(s.name) or [])
    if TC["mode"].get("layers_other_only"): out = list(P72.get("extra", {}).get(s.name) or [])      # v0.187: one layer, not the active one
    return tuple(out) if TC["mode"].get("layers_tuple") else out
def _tl_add_fake(s, layer, back=False):
    TC["calls"].append(("addLayer", layer.name))
    m = TC["mode"]
    if m.get("addlayer_raises"): raise RuntimeError("addLayer boom")
    if m.get("addlayer_ignored"): return None
    if m.get("addlayer_touches"): P72["layers"][s.name]._shapes.append(TCShape([te_contour(TE_TRI)]))
    P72.setdefault("extra", {}).setdefault(s.name, []).append(layer)
    return None
def _tl_remove_fake(s, layer):
    TC["calls"].append(("removeLayer", layer.name))
    m = TC["mode"]
    if m.get("removelayer_raises"): raise RuntimeError("removeLayer boom")
    if m.get("removelayer_ignored"): return None
    P72["extra"][s.name] = [l for l in P72.get("extra", {}).get(s.name) or [] if l is not layer]
    if m.get("remove_takes_shapes"):
        main = P72["layers"][s.name]; main._shapes = [sh for sh in main._shapes if all(sh is not t for t in layer._shapes)]
    return None
P72Mod.activeLayer = property(_tl_active_fake); P72Mod.layers = property(_tl_layers_fake)
P72Mod.addLayer = _tl_add_fake; P72Mod.removeLayer = _tl_remove_fake
class TCTempLayer(TCLayer):
    def __init__(s, title): TC["calls"].append(("flLayer", title)); TCLayer.__init__(s, title, [], None)
TCLayer.advanceWidth = property(lambda s: P72["widths"].get(s._glyph, 0.0))
_tl_saved = [(m, getattr(m, "flLayer", None)) for m in _tf_mods]
for _m in _tf_mods: _m.flLayer = TCTempLayer
def _tc_build181(s):
    r = _tc_build180(s)
    if TC["mode"].get("build_working"): P72["layers"]["cpp1"]._shapes.append(TCShape([te_contour(TE_TRI)]))
    return r
TCLayer.buildAuto = _tc_build181
_tc_add_orig = TCLayer.addShape
def _tc_add181(s, shape):
    r = _tc_add_orig(s, shape)
    if TC["mode"].get("addshape_moves"):
        for l in P72.get("extra", {}).get("cpp1") or []: l._shapes = [x for x in l._shapes if x is not shape]
    return r
TCLayer.addShape = _tc_add181
QT = QC + "stage=templayer&target=cpp1"
TLK = ("layers_before", "layers_after", "active_layer_after", "active_layer_kept", "layer_added", "built", "moved", "same_as_temp_component",
       "temp_still_holds_it", "layer_removed", "temp_layer_gone", "component_survived", "placed_beside", "width_changed", "side_effect_detected",
       "error", "calls_so_far")
def tls(shapes, mode=None, auto=False, legacy=4, extra=None):
    tc_gen_setup(mode=dict({"gen_list": 1}, **(mode or {}))); _tc_src3()
    ns["_TRYCOMP_TL_BASE"].clear(); ns["_TRYCOMP_TL"]["calls"] = 0; P72["extra"] = {"cpp1": list(extra or [])}; P72["active_of"] = {}
    if "_TRYCOMP_FL" in ns: ns["_TRYCOMP_FL"]["calls"] = 0     # v0.183
    lay = P72["layers"]["cpp1"]; lay.__dict__["_recipe"] = ""; lay.__dict__["_auto"] = auto; lay._shapes = shapes()
    nk_legacy(legacy)
def tl(tag, q, keys=TLK):
    d = tc(tag, QT + q, keys=keys)
    wa, ta = d.get("working_after"), d.get("temp_after")
    print("      working:", _nk_rows(wa.get("elements")) if isinstance(wa, dict) else wa, "| temp:",
          _nk_rows(ta.get("elements")) if isinstance(ta, dict) else ta, "| substeps:", [(x["call"], x["ok"]) for x in d.get("substeps") or []],
          "| mark:", d.get("fontlab_changed_mark"))
    return d
def tl_series(tag, shapes, mode=None, legacy_end=7, steps=("addlayer", "build", "move", "removelayer"), recipe="cppsrc"):
    tls(shapes, mode=mode)
    out = {}
    for st in steps:
        if st == "move": nk_legacy(legacy_end)
        out[st] = tl(f"{tag} {st:<12}", f"&step={st}" + (f"&recipe={recipe}" if st == "build" else "") + "&go=yes")
    return out
tls(lambda: [_contour()])
for tag, q in (("2530a no step                       ", "&go=yes"),
               ("2530b step=make                     ", "&step=make&go=yes"),
               ("2530c addlayer with a recipe        ", "&step=addlayer&recipe=cppsrc&go=yes"),
               ("2530d build without a recipe        ", "&step=build&go=yes"),
               ("2530e build, recipe of two          ", "&step=build&recipe=cppsrc%2Bcppsrc2&go=yes"),
               ("2530f build, recipe names the target ", "&step=build&recipe=cpp1&go=yes"),
               ("2530g with nonempty                 ", "&step=addlayer&nonempty=yes&go=yes"),
               ("2530h with element                  ", "&step=move&element=0&go=yes"),
               ("2530i shown before go               ", "&step=addlayer"),
               ("2530j build shown before go         ", "&step=build&recipe=cppsrc")):
    tc(tag, QT + q)
tc("2530k target without the prefix     ", QC + "stage=templayer&target=A&step=addlayer&go=yes")
for tag, kw in (("2531a an empty target               ", dict(shapes=lambda: [])),
                ("2531b a Power Brush shape           ", dict(shapes=lambda: [_contour(), TCShape([te_contour(TE_SQ)], composite=True)])),
                ("2531c a component of a non-cpp glyph ", dict(shapes=lambda: [_contour(), TCShape([te_contour(TE_SQ)], component="A")])),
                ("2531d autoLayer on                  ", dict(shapes=lambda: [_contour()], auto=True)),
                ("2531e a second layer already        ", dict(shapes=lambda: [_contour()], extra=[TCTempLayer("other")])),
                ("2531f w.layers not a list           ", dict(shapes=lambda: [_contour()], mode={"layers_tuple": 1})),
                ("2531g two masters                   ", dict(shapes=lambda: [_contour()], mode={"masters": 2})),
                ("2531h an ink box unreadable         ", dict(shapes=lambda: [_contour()], mode={"box_raises": 1}))):
    tls(**kw); tl(tag, "&step=addlayer&go=yes")
tls(lambda: [_contour()])
for st, q in (("build", "&recipe=cppsrc"), ("move", ""), ("removelayer", "")):
    tl(f"2531i {st} with no baseline     ", f"&step={st}{q}&go=yes")
print("2531j  no layer call in the refusals:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] in ("addLayer", "removeLayer", "flLayer", "recipe=")])
r = tl_series("2532 contour:", lambda: [_contour()])
print("      final working contours held, new:", r["removelayer"].get("working_vs_baseline", {}).get("contours_held"),
      _nk_rows(r["removelayer"].get("working_vs_baseline", {}).get("new")), "| baseline cleared:", "cpp1" not in ns["_TRYCOMP_TL_BASE"])
tl_series("2533 component:", lambda: [_tc_comp("cppsrc2", -200, 0)], legacy_end=7)
tl_series("2534 mixed:", lambda: [_contour(), _tc_comp("cppsrc2", -200, 0)], legacy_end=11)
tl_series("2535 shared object lost at removeLayer:", lambda: [_contour()], mode={"remove_takes_shapes": 1})
tl_series("2536 addShape moves it:", lambda: [_contour()], mode={"addshape_moves": 1})
tl_series("2537 addLayer makes it active:", lambda: [_contour()], mode={"add_activates": 1}, steps=("addlayer",))
for tag, mode in (("2538a addLayer raises                ", {"addlayer_raises": 1}), ("2538b addLayer ignored               ", {"addlayer_ignored": 1}),
                  ("2538c addLayer touches the working layer", {"addlayer_touches": 1})):
    tl_series(tag, lambda: [_contour()], mode=mode, steps=("addlayer",))
for tag, mode in (("2539a buildAuto returns False         ", {"build_false": 1}), ("2539b the recipe is ignored           ", {"recipe_ignored": 1}),
                  ("2539c the build hits the working layer", {"build_working": 1}), ("2539d buildAuto raises               ", {"build_raises": 1}),
                  ("2539e the build sets the width        ", {"build_width": 1})):
    tl_series(tag, lambda: [_contour()], mode=mode, steps=("addlayer", "build"))
tl_series("2540a addShape raises                 ", lambda: [_contour()], mode={"add_raises": 1}, steps=("addlayer", "build", "move"))
tl_series("2540b removeLayer raises              ", lambda: [_contour()], mode={"removelayer_raises": 1})
tl_series("2540c removeLayer ignored             ", lambda: [_contour()], mode={"removelayer_ignored": 1})
tl_series("2540d clean-up: removelayer after addlayer", lambda: [_contour()], steps=("addlayer", "removelayer"))
tls(lambda: [_contour()]); tl("2541a addlayer                ", "&step=addlayer&go=yes")
P72["layers"]["cpp1"]._shapes.append(TCShape([te_contour(TE_TRI)]))
tl("2541b the working layer changed: build refused", "&step=build&recipe=cppsrc&go=yes")
tls(lambda: [_contour()]); tl("2541c addlayer                ", "&step=addlayer&go=yes")
tl("2541d move on an empty temporary layer", "&step=move&go=yes")
tl("2541e build, the recipe names the target", "&step=build&recipe=cpp1&go=yes")
P72["layers"]["cppsrc2"]._shapes = [_tc_comp("cppsrc")]
tl("2541f build with a source holding a component", "&step=build&recipe=cppsrc2&go=yes")
tls(lambda: [_contour()])
for _i in range(ns["_TRYCOMP_TL_MAX"]): call(QT + "&step=addlayer&go=yes")     # v0.185: 20 (10 before)
tc(f"2542 the limit: call {ns['_TRYCOMP_TL_MAX'] + 1} is refused  ", QT + "&step=addlayer&go=yes")
_src181 = "\n".join(l for l in src[src.index("# /debug/trycomponent stage=templayer (v0.181)"):src.index("# /debug/tryshape (v0.52)")].split("\n")
                    if not l.lstrip().startswith("#"))
print("2543 spies over the cases:", TC_FORBIDDEN, "| static scan:",
      _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addComponent|clearComponents|removeShape|replaceShape|killAuto|decomposite)\s*\(|font\.update", _src181),
      "| one call each:", [len(_re83.findall(p, _src181)) for p in (r"(?m)^\s+w\.addLayer\(", r"(?m)^\s+ret = w\.removeLayer\(", r"(?m)^\s+ret = wl\.addShape\(", r"(?m)^\s+ret = tl\.buildAuto\(\)")],
      "| baseline written once:", _src181.count("_TRYCOMP_TL_BASE[target] ="), "| marked only at removelayer:",
      'if step == "removelayer" and result["placed_beside"]:' in _src181,
      "| counter before the read:", _src181.index('_TRYCOMP_TL["calls"] += 1') < _src181.index("return _trycomp_timed(_trycomp_templayer_run"),
      "| route documented:", "stage=templayer&target=cpp...&step=addlayer|build|move|removelayer" in src)
# ---- v0.182: step=activate (live TL 1272: addLayer made the new layer the active one). TCLayer gains setActive (it makes the layer the
# active one of cpp1) and isActive; modes setactive_raises / _ignored / _touches (adds a contour to the layer), isactive_raises.
print("\n==== v0.182 /debug/trycomponent stage=templayer&step=activate ====")
def _tc_set_active(s):
    TC["calls"].append(("setActive", s.name))
    m = TC["mode"]
    if m.get("setactive_raises"): raise RuntimeError("setActive boom")
    if m.get("setactive_touches"): s._shapes.append(TCShape([te_contour(TE_TRI)]))
    if m.get("setactive_ignored"): return None
    P72.setdefault("active_of", {})["cpp1"] = s
    return None
def _tc_is_active(s):
    if TC["mode"].get("isactive_raises"): raise RuntimeError("isActive boom")
    if TC["mode"].get("isactive_lies"): return s.name != "gb_temp_component"     # disagrees with the glyph's activeLayer
    return _tl_active_fake(P72Mod(TS["cpp1"], None)) is s
TCLayer.setActive = _tc_set_active; TCLayer.isActive = _tc_is_active
TLK2 = ("active_layer_before", "active_layer_after", "is_active", "layers_unchanged", "working_active", "layer_added", "built", "moved",
        "temp_still_holds_it", "component_survived", "placed_beside", "side_effect_detected", "error", "calls_so_far")
tls(lambda: [_contour()])
tl("2544a activate with a recipe         ", "&step=activate&recipe=cppsrc&go=yes", keys=TLK2)
tl("2544b activate with no baseline      ", "&step=activate&go=yes", keys=TLK2)
tc("2544c activate shown before go       ", QT + "&step=activate")
def tl_series2(tag, shapes, mode=None, steps=("addlayer", "activate", "build", "move", "removelayer"), legacy_end=7):
    tls(shapes, mode=mode)
    for st in steps:
        if st == "move": nk_legacy(legacy_end)
        tl(f"{tag} {st:<12}", f"&step={st}" + ("&recipe=cppsrc" if st == "build" else "") + "&go=yes", keys=TLK2)
tl_series2("2545 addLayer activates, contour:", lambda: [_contour()], mode={"add_activates": 1})
tl_series2("2546 addLayer activates, component:", lambda: [_tc_comp("cppsrc2", -200, 0)], mode={"add_activates": 1})
tl_series2("2547 already active:", lambda: [_contour()], steps=("addlayer", "activate"))
for tag, mode in (("2548a setActive raises              ", {"setactive_raises": 1}), ("2548b setActive ignored             ", {"setactive_ignored": 1}),
                  ("2548c setActive adds to the layer    ", {"setactive_touches": 1}), ("2548d isActive raises               ", {"isactive_raises": 1}),
                  ("2548e ignored, isActive disagrees    ", {"setactive_ignored": 1, "isactive_lies": 1})):
    tl_series2(tag, lambda: [_contour()], mode=dict(mode, add_activates=1), steps=("addlayer", "activate"))
_src182 = "\n".join(l for l in src[src.index("# /debug/trycomponent stage=templayer (v0.181)"):src.index("# /debug/tryshape (v0.52)")].split("\n")
                    if not l.lstrip().startswith("#"))
print("2549 one setActive call:", len(_re83.findall(r"(?m)^\s+ret = wl\.setActive\(\)", _src182)), "| no updateActiveLayer:", "updateActiveLayer" not in _src182,
      "| route documented:", "step=activate: ONE working_layer.setActive() (v0.182)" in src)
# ---- v0.183: stage=fixlayer, and component_layer_matches in stage=templayer (live 1283a / 1283b: the built component names the temporary
# layer). TCShapeData.componentLayer becomes a property that can be set; build_names_layer makes the build fake name the layer it built
# on. Modes: cl_raises, cl_ignored, cl_moves (the component's offset moves by 5), cl_touches_source.
print("\n==== v0.183 /debug/trycomponent stage=fixlayer; templayer component_layer_matches ====")
_tcsd_layer_orig = TCShapeData.__dict__["componentLayer"]
def _sd_get_layer(s): return s.__dict__.get("_layer", "test_font" if s._glyph else "")
def _sd_set_layer(s, v):
    TC["calls"].append(("componentLayer=", v))
    m = TC["mode"]
    if m.get("cl_raises"): raise AttributeError("can't set attribute")
    if m.get("cl_ignored"): return
    s.__dict__["_layer"] = v
    if m.get("cl_moves") and s.__dict__.get("_shape") is not None:
        sh = s.__dict__["_shape"]; sh._tx = TCQT(1, 0, 0, 1, sh._tx.dx() + 5, sh._tx.dy())
    if m.get("cl_touches_source"): TCSRC["cppsrc"]._contours[0].rows[0]["x"] += 1.0
TCShapeData.componentLayer = property(_sd_get_layer, _sd_set_layer)
def _tc_build183(s):
    r = _tc_build181(s)
    if TC["mode"].get("build_names_layer"):
        for sh in s._shapes:
            if sh._component and "_layer" not in sh.shapeData.__dict__:
                sh.shapeData.__dict__["_layer"] = s.name; sh.shapeData.__dict__["_shape"] = sh     # v0.184: cl_moves reaches it
    return r
TCLayer.buildAuto = _tc_build183
def _tc_tmpcomp(name="cppsrc", layer="gb_temp_component"):
    sh = _tc_comp(name); sh.shapeData.__dict__["_layer"] = layer; sh.shapeData.__dict__["_shape"] = sh; return sh
QF = QC + "stage=fixlayer&target=cpp1"
FLK = ("layers", "component_layer_before", "component_layer_after", "component_kept", "others_kept", "outline_kept", "side_effect_detected",
       "layer_set", "error", "calls_so_far")
def fl(tag, q, keys=FLK):
    d = tc(tag, QF + q, keys=keys)
    ta = d.get("target_after")
    print("      after:", [(r.get("is_component"), r.get("component_glyph"), r.get("component_layer")) for r in ta["elements"]]
          if isinstance(ta, dict) and isinstance(ta.get("elements"), list) else ta, "| mark:", d.get("fontlab_changed_mark"))
    return d
tls(lambda: [_contour(), _tc_tmpcomp()], legacy=7)
for tag, q in (("2550a no element                    ", "&go=yes"), ("2550b element is text              ", "&element=one&go=yes"),
               ("2550c with a step                   ", "&element=1&step=move&go=yes"), ("2550d shown before go             ", "&element=1")):
    fl(tag, q)
tc("2550e target without the prefix     ", QC + "stage=fixlayer&target=A&element=0&go=yes")
for tag, kw, q in (("2551a the element is a contour      ", {}, "&element=0&go=yes"),
                   ("2551b element 2 of two              ", {}, "&element=2&go=yes"),
                   ("2551c already names the layer       ", dict(shapes=lambda: [_contour(), _tc_comp("cppsrc")]), "&element=1&go=yes"),
                   ("2551d a second layer                ", dict(extra=[TCTempLayer("other")]), "&element=1&go=yes"),
                   ("2551e autoLayer on                  ", dict(auto=True), "&element=1&go=yes"),
                   ("2551f a Power Brush shape           ", dict(shapes=lambda: [TCShape([te_contour(TE_SQ)], composite=True), _tc_tmpcomp()]), "&element=1&go=yes"),
                   ("2551g a component of a non-cpp glyph ", dict(shapes=lambda: [TCShape([te_contour(TE_SQ)], component="A"), _tc_tmpcomp()]), "&element=1&go=yes")):
    tls(kw.get("shapes", lambda: [_contour(), _tc_tmpcomp()]), auto=kw.get("auto", False), extra=kw.get("extra"), legacy=7)
    fl(tag, q)
print("2551h  no componentLayer= in the refusals:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] == "componentLayer="])
tls(lambda: [_contour(), _tc_tmpcomp()], legacy=7); fl("2552 contour + a temp-layer component", "&element=1&go=yes")
tls(lambda: [_tc_comp("cppsrc2", -200, 0), _tc_tmpcomp()], legacy=7); fl("2552a component + a temp-layer component", "&element=1&go=yes")
for tag, mode in (("2553a the assignment raises          ", {"cl_raises": 1}), ("2553b the assignment is ignored      ", {"cl_ignored": 1}),
                  ("2553c the component moves           ", {"cl_moves": 1}), ("2553d the source changes            ", {"cl_touches_source": 1})):
    tls(lambda: [_contour(), _tc_tmpcomp()], mode=mode, legacy=7); fl(tag, "&element=1&go=yes")
tls(lambda: [_contour(), _tc_tmpcomp()], legacy=7)
for _i in range(6): call(QF + "&element=1&go=yes")
tc("2554 the limit: call 7 is refused   ", QF + "&element=1&go=yes")
TLK3 = ("moved", "component_layer_matches", "layer_removed", "component_survived", "placed_beside", "error")
tls(lambda: [_contour()], mode={"build_names_layer": 1, "add_activates": 1})
for st in ("addlayer", "activate", "build", "move", "removelayer"):
    if st == "move": nk_legacy(7)
    tl(f"2555 build names its layer: {st:<12}", f"&step={st}" + ("&recipe=cppsrc" if st == "build" else "") + "&go=yes", keys=TLK3)
_src183 = "\n".join(l for l in src[src.index("# /debug/trycomponent stage=fixlayer (v0.183)"):src.index("# /debug/tryshape (v0.52)")].split("\n")
                    if not l.lstrip().startswith("#"))
print("2556 static scan:", _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addShape|removeShape|addLayer|removeLayer|buildAuto|killAuto)\s*\(|font\.update", _src183),
      "| one assignment:", len(_re83.findall(r"(?m)^\s+sd\.componentLayer = name$", _src183)),
      "| route documented:", "stage=fixlayer&target=cpp...&element=I: ONE shapeData.componentLayer" in src,
      "| placed_beside needs the layer:", 'and result["component_layer_matches"])' in src)
# ---- v0.184: stage=templayer step=setlayer (the source-layer fix before the move) and step=droptemp (clean-up of an empty temporary
# layer left behind). The v0.183 fakes stay: componentLayer can be set; build_names_layer names the layer the build ran on.
print("\n==== v0.184 /debug/trycomponent stage=templayer: setlayer, droptemp ====")
TLK4 = ("active_layer_after", "temp_component_layer_after", "temp_layer_set", "moved", "component_layer_matches", "component_survived",
        "placed_beside", "layers_after", "calls", "working_kept", "temp_dropped", "side_effect_detected", "error", "calls_so_far")
def tl4(tag, q):
    d = tl(tag, q, keys=TLK4)
    return d
tls(lambda: [_contour()])
tl4("2560a setlayer with no baseline     ", "&step=setlayer&go=yes")
tc("2560b setlayer with a recipe        ", QT + "&step=setlayer&recipe=cppsrc&go=yes")
tc("2560c droptemp with a recipe        ", QT + "&step=droptemp&recipe=cppsrc&go=yes")
tc("2560d droptemp shown before go      ", QT + "&step=droptemp")
def tl_route(tag, mode, steps=("addlayer", "activate", "build", "setlayer", "move", "removelayer"), shapes=None):
    tls(shapes or (lambda: [_contour()]), mode=dict({"build_names_layer": 1, "add_activates": 1}, **(mode or {})))
    for st in steps:
        if st == "move": nk_legacy(7)
        tl4(f"{tag} {st:<12}", f"&step={st}" + ("&recipe=cppsrc" if st == "build" else "") + "&go=yes")
tl_route("2561 the full route, contour:", {})
tl_route("2561a the full route, component:", {}, shapes=lambda: [_tc_comp("cppsrc2", -200, 0)])
tl_route("2562a setlayer on an empty temporary layer:", {}, steps=("addlayer", "activate", "setlayer"))
tl_route("2562b setlayer, already the working layer:", {"build_names_layer": 0}, steps=("addlayer", "activate", "build", "setlayer"))
for tag, mode in (("2562c the assignment raises:", {"cl_raises": 1}), ("2562d the assignment is ignored:", {"cl_ignored": 1}),
                  ("2562e the component moves:", {"cl_moves": 1})):
    tl_route(tag, mode, steps=("addlayer", "activate", "build", "setlayer"))
def dt(tag, mode=None, extra=None, shapes=None, active_temp=True):
    tls(shapes or (lambda: [_tc_comp("cppsrc2", -200, 0)]), mode=dict({"add_activates": 1} if active_temp else {}, **(mode or {})),
        extra=extra if extra is not None else [TCTempLayer("gb_temp_component")], legacy=4)
    d = tl4(tag, "&step=droptemp&go=yes")
    print("      layer calls:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] in ("setActive", "removeLayer")])
    return d
dt("2563 droptemp, the temporary layer active")
dt("2563a droptemp, the working layer active ", active_temp=False)
dt("2563b droptemp, an empty working layer   ", shapes=lambda: [])
def _nonempty_temp():
    t = TCTempLayer("gb_temp_component"); t._shapes = [_tc_comp("cppsrc")]; return [t]
for tag, kw in (("2564a the temporary layer holds a component", dict(extra=_nonempty_temp())),
                ("2564b one layer only                      ", dict(extra=[])),
                ("2564c three layers                        ", dict(extra=[TCTempLayer("gb_temp_component"), TCTempLayer("other")])),
                ("2564d the other layer is not named        ", dict(extra=[TCTempLayer("other")])),
                ("2564e a Power Brush shape in the other    ", dict(shapes=lambda: [TCShape([te_contour(TE_SQ)], composite=True)])),
                ("2564f setActive ignored: no removeLayer   ", dict(mode={"setactive_ignored": 1})),
                ("2564g setActive raises                    ", dict(mode={"setactive_raises": 1})),
                ("2564h removeLayer raises                  ", dict(mode={"removelayer_raises": 1})),
                ("2564i removeLayer ignored                 ", dict(mode={"removelayer_ignored": 1})),
                ("2564j setActive adds to the working layer ", dict(mode={"setactive_touches": 1}))):
    dt(tag, **kw)
_src184 = "\n".join(l for l in src[src.index("# /debug/trycomponent stage=templayer (v0.181)"):src.index("# /debug/tryshape (v0.52)")].split("\n")
                    if not l.lstrip().startswith("#"))
print("2565 one setlayer assignment:", len(_re83.findall(r'(?m)^\s+sd\.componentLayer = bl\["working"\]$', _src184)),
      "| removeLayer statements (removelayer, droptemp):", len(_re83.findall(r"(?m)^\s+ret = w\.removeLayer\(tl\)$", _src184)),
      "| droptemp refuses a non-empty layer:", 'if not _tl_ok(tview) or tview["elements"] or tview["contours"]:' in _src184,
      "| route documented:", "step=droptemp: an EMPTY gb_temp_component left behind removed (v0.184)" in src)
# ---- v0.185: stage=templayer brush=yes (a working layer that also holds Power Brush shapes) and sync=light|full (the user's choice of
# 2026-11-18: research Power Brush targets before the tool). The legacy glyph of cpp1 records every read of its layer members (F1:
# glyph.layer / glyph.layers arm a Power Brush glyph); TCBrush is a composite shape that records an inkBox() call on itself.
print("\n==== v0.185 /debug/trycomponent stage=templayer: brush=yes, sync=light|full ====")
SPY185 = []
class TsSpy185(TsGlyph):
    @property
    def layers(self): SPY185.append("layers"); return self._layers
    @property
    def layer(self): SPY185.append("layer"); return self._layers[0] if self._layers else None
    @property
    def bodyLayer(self): SPY185.append("bodyLayer"); return self._layers[0] if self._layers else None
    @property
    def activeLayer(self): SPY185.append("activeLayer"); return self._layers[0] if self._layers else None
def spy_legacy(nodes, width=0.0):
    TS["cpp1"] = TsSpy185("cpp1", [TsLayer(1, nodes)]); TS["cpp1"].width = width
class TCBrush(TCShape):
    def __init__(s): TCShape.__init__(s, [te_contour(TE_SQ)], composite=True)
    def inkBox(s): TC["calls"].append("inkBox on the brush"); return _tc_inkbox(s)
tls(lambda: [TCBrush()])
for tag, q in (("2570a brush=no                      ", "&step=addlayer&brush=no&go=yes"),
               ("2570b sync=fast                     ", "&step=addlayer&sync=fast&go=yes"),
               ("2570c shown before go, brush, light ", "&step=addlayer&brush=yes&sync=light"),
               ("2570d brush=Yes                     ", "&step=addlayer&brush=Yes&go=yes")):
    tc(tag, QT + q)
tc("2570e brush on stage=fixlayer       ", QC + "stage=fixlayer&target=cpp1&element=0&brush=yes&go=yes")
tc("2570f sync on stage=offset          ", QC + "stage=offset&target=cpp1&how=assign&dx=5&dy=0&sync=light&go=yes")
tls(lambda: [TCBrush()]); tl("2571a a brush target without brush=yes", "&step=addlayer&sync=light&go=yes")
print("2571b  no layer call in the refusal:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] in ("addLayer", "flLayer")])
def tl_brush(tag, sync, shapes, steps=("addlayer", "activate", "build", "setlayer", "move", "removelayer")):
    tls(shapes, mode={"build_names_layer": 1, "add_activates": 1})
    out = {}
    for st in steps:
        spy_legacy(7 if st in ("move", "removelayer") else 4)
        SPY185.clear()
        d = tl4(f"{tag} {st:<12}", f"&step={st}" + ("&recipe=cppsrc" if st == "build" else "") + f"&brush=yes&sync={sync}&go=yes")
        wa = d.get("working_after")
        print("      legacy layer reads:", list(SPY185), "| sync verdict:", (d.get("fontlab_sync") or {}).get("verdict"), "| brush/sync:",
              d.get("brush"), d.get("sync"), "| brush rows:", [r.get("ink_box") == ns["_TL_BOX_NOT_READ"] for r in (wa.get("elements") or [])
                                                                 if isinstance(r, dict)] if isinstance(wa, dict) and isinstance(wa.get("elements"), list) else wa,
              "| inkBox on the brush:", TC["calls"].count("inkBox on the brush"))
        out[st] = d
    return out
r185 = tl_brush("2572 brush, sync=light:", "light", lambda: [TCBrush()])
print("2572a  placed_beside:", r185["removelayer"].get("placed_beside"), "| guard entry left:", ns["_guard_state"](ns["_open_font"]())["glyphs"].get("cpp1"))
r185 = tl_brush("2573 brush, sync=full:", "full", lambda: [TCBrush()])
print("2573a  placed_beside:", r185["removelayer"].get("placed_beside"))
tl_brush("2574 brush + contour, sync=light:", "light", lambda: [TCBrush(), _contour()], steps=("addlayer", "activate", "build"))
tl_brush("2575 contour only, brush=yes, sync=light:", "light", lambda: [_contour()], steps=("addlayer", "activate", "build", "setlayer", "move", "removelayer"))
tls(lambda: [TCBrush()], mode={"build_names_layer": 1, "add_activates": 1}); spy_legacy(4)
tl4("2576a addlayer, brush, light       ", "&step=addlayer&brush=yes&sync=light&go=yes")
P72["layers"]["cpp1"]._shapes[0]._tx = TCQT(1, 0, 0, 1, 5, 0)
tl4("2576b the brush moved: build refused", "&step=build&recipe=cppsrc&brush=yes&sync=light&go=yes")
tls(lambda: [TCBrush()], mode={"build_names_layer": 1, "add_activates": 1}); spy_legacy(4)
tl4("2576c addlayer, brush, light       ", "&step=addlayer&brush=yes&sync=light&go=yes")
P72["layers"]["cpp1"]._shapes[0] = _contour()     # the same square and matrix, but a plain shape: no longer the brush recorded
tl4("2576d the brush became plain: build refused", "&step=build&recipe=cppsrc&brush=yes&sync=light&go=yes")
def dt185(tag, sync, mode=None):
    tls(lambda: [TCBrush()], mode=dict({"add_activates": 1}, **(mode or {})), extra=[TCTempLayer("gb_temp_component")], legacy=4)
    spy_legacy(4); SPY185.clear()
    d = tl4(tag, f"&step=droptemp&brush=yes&sync={sync}&go=yes")
    print("      legacy layer reads:", list(SPY185), "| sync verdict:", (d.get("fontlab_sync") or {}).get("verdict"),
          "| layer calls:", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] in ("setActive", "removeLayer")])
    return d
dt185("2577a droptemp, brush, sync=light  ", "light")
dt185("2577b droptemp, brush, sync=full   ", "full")
tls(lambda: [TCBrush()], extra=[TCTempLayer("gb_temp_component")]); tl4("2577c droptemp, brush, no brush=yes ", "&step=droptemp&sync=light&go=yes")
_src185 = "\n".join(l for l in src[src.index("# /debug/trycomponent stage=templayer (v0.181)"):src.index("# /debug/tryshape (v0.52)")].split("\n")
                    if not l.lstrip().startswith("#"))
def _fn185(name):
    body = _src185[_src185.index(f"def {name}("):]
    return body[:body.index("\ndef ", 5)]
print("2578 light kind:", "trycomponent_light" in ns["_GUARD_LIGHT_KINDS"], "| marked as a component:", ns["_MARK_TITLES"].get("trycomponent_light"),
      "| guard calls through _tl_guard_how:", _src185.count("_guard_mark(font, target, _tl_guard_how(sync_mode), result"),
      "| a plain \"trycomponent\" guard call left in templayer:", len(_re83.findall(r'_guard_mark\(font, target, "trycomponent"', _src185[_src185.index("def _trycomp_templayer_gate"):_src185.index("def _trycomp_fixlayer_gate")])),
      "| kind check before the first view (run, droptemp):", [_fn185(f).index("why = _tl_plain_elements_problem(wtel,") < _fn185(f).index("wview = _tl_view(wl, brush)")
                                                               for f in ("_trycomp_templayer_run", "_trycomp_droptemp_run")],
      "| limit:", ns["_TRYCOMP_TL_MAX"], "| route documented:", "stage=templayer&brush=yes: the working layer may also hold Power Brush shapes" in src)
# ---- v0.186: add_component into a glyph that is NOT empty: the temporary-layer route inside ONE request (the user's design of
# 2026-11-18), both forms; a failure partway restores the glyph. The v0.181-v0.185 fakes stay: layers, addLayer / removeLayer,
# setActive, a settable componentLayer, build_names_layer (the build names the temporary layer), TCBrush (records inkBox on itself).
print("\n==== v0.186 POST /glyph/component: a glyph that is not empty ====")
AB = ("placement", "placed", "verified", "existing_kept", "changed", "steps_done", "component_states", "checks", "layers_after",
      "active_layer_after", "restore", "width_set_by_build", "cleanup", "components_after", "reason", "error")
def ab(tag, payload, shapes, mode=None, legacy=7, auto=False, extra=None, prep=None, activates=True):
    tls(shapes, mode=dict({"build_names_layer": 1, "add_activates": 1 if activates else 0}, **(mode or {})), auto=auto, extra=extra, legacy=legacy)
    TC["rm_calls"] = 0
    if prep: prep()
    c, d = sbpost("/glyph/component", payload)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in AB if k in d})
    lay = P72["layers"]["cpp1"]
    print("      calls:", [x if isinstance(x, str) else x[0] for x in TC["calls"] if x != "inkBox" and not (isinstance(x, tuple) and x[0] == "QTransform")],
          "| Update", TE["updates"], "| marks", TE["marks"], "| inkBox on the brush:", TC["calls"].count("inkBox on the brush"),
          "| working now:", [("comp", sh.shapeData.componentGlyph(), sh.shapeData.componentLayer, sh._tx.dx(), sh._tx.dy()) if sh._component
                             else ("brush" if sh._composite else "plain") for sh in lay._shapes],
          "| other layers:", [l.name for l in P72.get("extra", {}).get("cpp1") or []])
    return d
PB0 = {"name": "cpp1", "component": "cppsrc", "x": 0, "y": 0}
ab("2580a one, onto a contour         ", PB0, lambda: [_contour()])
ab("2580b one at (120, -40), onto a component", dict(PB0, x=120, y=-40), lambda: [_tc_comp("cppsrc2", -200, 0)])
ab("2580c one, onto a Power Brush shape", PB0, lambda: [TCBrush()])
ab("2580d a list of three, onto a brush and a contour", {"name": "cpp1", "components": [{"component": "cppsrc", "x": 0, "y": 0},
   {"component": "cppsrc3", "x": 300, "y": 0}, {"component": "cppsrc", "x": 500, "y": 0}]}, lambda: [TCBrush(), _contour()], legacy=18)
ab("2580e addLayer leaves the working layer active", PB0, lambda: [_contour()], activates=False)
class TCTempLayerG(TCTempLayer):      # a temporary layer whose build changes the glyph's width (build_width writes P72["widths"][_glyph])
    def __init__(s, title): TCTempLayer.__init__(s, title); s._glyph = "cpp1"
for _m in _tf_mods: _m.flLayer = TCTempLayerG
ab("2580f the build sets the width     ", PB0, lambda: [_contour()], mode={"build_width": 1})
ab("2580g the width write-back fails   ", PB0, lambda: [_contour()], mode={"build_width": 1, "width_set_raises": 1})
for _m in _tf_mods: _m.flLayer = TCTempLayer
ab("2581a a second layer already       ", PB0, lambda: [_contour()], extra=[TCTempLayer("other")], activates=False)
ab("2581b autoLayer on                 ", PB0, lambda: [_contour()], auto=True)
def _src2_comp(): P72["layers"]["cppsrc2"]._shapes = [_tc_comp("cppsrc")]
ab("2581c a source holding a component ", dict(PB0, component="cppsrc2"), lambda: [_contour()], prep=_src2_comp)
ab("2581d an empty glyph keeps its route", PB0, lambda: [], legacy=3)
for tag, mode in (("2582a buildAuto returns False      ", {"build_false": 1}), ("2582b addShape raises              ", {"add_raises": 1}),
                  ("2582c componentLayer cannot be set  ", {"cl_raises": 1}), ("2582d setActive ignored             ", {"setactive_ignored": 1}),
                  ("2582e removeLayer raises: restore incomplete", {"removelayer_raises": 1}), ("2582f the build hits the working layer", {"build_working": 1})):
    ab(tag, PB0, lambda: [_contour()], mode=mode)
ab("2582h the source-layer assignment is ignored", PB0, lambda: [_contour()], mode={"cl_ignored": 1})
class TCOdd(TCShape):
    def isComponent(s): raise RuntimeError("isComponent boom")
ab("2581e an element that cannot be read", PB0, lambda: [_contour(), TCOdd([te_contour(TE_SQ)])])
_tc_add186_orig = TCLayer.addShape
def _tc_add186(s, shape):      # moves the working layer's first element by 5 while adding (an existing element changed by the call)
    r = _tc_add186_orig(s, shape)
    if TC["mode"].get("add_moves_existing") and s._shapes: s._shapes[0]._tx = TCQT(1, 0, 0, 1, s._shapes[0]._tx.dx() + 5, s._shapes[0]._tx.dy())
    return r
TCLayer.addShape = _tc_add186
ab("2582i the move shifts an existing element", PB0, lambda: [_tc_comp("cppsrc2", -200, 0)], mode={"add_moves_existing": 1})
TCLayer.addShape = _tc_add186_orig
ab("2582g a list fails at addShape     ", {"name": "cpp1", "components": [{"component": "cppsrc", "x": 0, "y": 0},
   {"component": "cppsrc3", "x": 300, "y": 0}]}, lambda: [_contour()], mode={"add_raises": 1})
# ---- v0.187: both routes, both forms, need exactly one layer, the active one (rule A, the user's choice after NB 1353: an empty active
# layer beside a full one took the empty route, and the build named that layer as the source's layer); source_layer is its own check.
print("\n==== v0.187 POST /glyph/component: one layer, the active one, in both routes ====")
PL2 = {"name": "cpp1", "components": [{"component": "cppsrc", "x": 0, "y": 0}, {"component": "cppsrc3", "x": 300, "y": 0}]}
ab("2584a an empty layer active beside a full one (NB 1353)", PB0, lambda: [_contour()], extra=[TCTempLayer("New Layer")])
ab("2584b an empty glyph with a second layer, master active", PB0, lambda: [], extra=[TCTempLayer("other")], activates=False, legacy=3)
ab("2584c the list form, an empty layer active beside a full one", PL2, lambda: [_contour()], extra=[TCTempLayer("New Layer")])
ab("2584d the list form, an empty glyph with a second layer", PL2, lambda: [], extra=[TCTempLayer("other")], activates=False, legacy=3)
ab("2584e the layers cannot be read    ", PB0, lambda: [], mode={"layers_tuple": 1}, legacy=3)
def _rename_working(): P72["layers"]["cpp1"].name = "master2"
d = ab("2584f the build names another layer: source_layer fails", PB0, lambda: [], prep=_rename_working, legacy=3)
print("      checks:", d.get("checks"), "| elements after:", [(e.get("component_glyph"), e.get("component_layer")) for e in d.get("elements_after") or []])
def _rename_temp(): P72["layers"]["cpp1"].name = "gb_temp_component"
ab("2584h the only layer is a leftover temporary layer", PB0, lambda: [_contour()], prep=_rename_temp)
ab("2584i one layer listed, not the active one", PB0, lambda: [_contour()], extra=[TCTempLayer("other")], activates=False,
   mode={"layers_other_only": 1})
_s187 =src[src.index("def add_component(name, component, x, y):"):src.index("def _comp_one_layer_problem(")]
print("2584g asked in both forms before the route:", _s187.count("why = _comp_one_layer_problem(w, state)"),
      [_s187.index("why = _comp_one_layer_problem(w, state)", _s187.index(f)) < _s187.index("if tel:", _s187.index(f))
       for f in ("def add_component(name", "def add_components(name")],
      "| route documented:", "v0.187: both routes, both forms, need exactly one layer, the active one" in src)
_srcb ="\n".join(l for l in src[src.index("# add_component into a glyph that is NOT empty (v0.186"):src.index("# /debug/tryedit (v0.151)")].split("\n")
                  if not l.lstrip().startswith("#"))
_ab = _srcb[_srcb.index("def _add_beside("):]
print("2583 static scan:", _re83.findall(r"\.(?:update|save\w*|setGlyphComponents|addComponent|clearComponents|killAuto|decomposite|replaceShape|applyTransform)\s*\(|font\.update", _srcb),
      "| every refusal before the first write:", _ab.rindex("nothing was changed") < _ab.index("w.addLayer(layer_cls(_TL_TEMP_NAME))"),
      "| addLayer( texts (the call and its step label), removeLayer( calls (route, restore) and its label:", len(_re83.findall(r"\.addLayer\(", _srcb)), len(_re83.findall(r"\.removeLayer\(", _srcb)),
      "| removeShape only in the restore:", "removeShape" not in _ab and _srcb.count("wl.removeShape(shapes[j], False)") == 1,
      "| restore only after an error:", 'if "error" in result and done:' in _ab, "| full check:", '_guard_mark(font, name, "add_component", result,' in _ab,
      "| hooked in both forms:", src.count("return _add_beside(base, name, ctx, state, layer, tel,"), src.count("return _done(_add_beside(base, name, ctx, state, layer, tel,"),
      "| route documented:", 'temporary-layer route in the same request (placement "temporary layer")' in src)
# ================= v0.207: POST /glyph/contours/add (add_contours) and the _EDIT_ACCEPTS grid =================
# The v0.186 fakes above (tls: the glyph cpp1 holds the shapes given; nk_legacy: the legacy view's node count, which the sync check
# compares). TCShapeData gains addContour, which appends to the shape's own contour list; modes break it: addc_raises, addc_drops,
# addc_first (the new contour lands first), addc_moves_old (an old node moves by 5), addc_extra_shape (an empty shape appears as well).
print("\n==== v0.207 POST /glyph/contours/add (add_contours) ====")
def _tcsd_addc(s, c):
    TC["calls"].append("addContour")
    m = TC["mode"]
    if m.get("addc_raises"): raise RuntimeError("addContour boom")
    if m.get("addc_drops"): return
    if m.get("addc_moves_old") and s._contours: s._contours[0].rows[0]["x"] += 5.0
    if m.get("addc_first"): s._contours.insert(0, c); return
    if m.get("addc_extra_shape"): P72["layers"]["cpp1"]._shapes.append(TCShape([]))
    s._contours.append(c)
TCShapeData.addContour = _tcsd_addc
TCShape.getContours = lambda s: list(s._contours)     # v0.215: a shape's own contours, as FontLab's flShape.getContours() (1807, ED8)
AK =("added", "nodes_match", "changed", "mismatches", "reason", "edit_case", "contours_found", "coordinates_rounded", "contour_sizes",
      "nodes_before", "open_contours", "synced_with_fontlab", "fontlab_changed_mark", "error")
def adc(tag, body, shapes=lambda: [_contour()], mode=None, keys=AK, legacy=8):
    tls(shapes, mode=mode, legacy=legacy)
    c, d = sbpost("/glyph/contours/add", body)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", [x for x in TC["calls"] if x in ("addContour", "addShape")],
          "| Update", TE["updates"], "| marks", TE["marks"])
    return d
def adc_after(d, key="after"):
    return [("closed" if c["closed"] else "open", [(n["x"], n["y"], n["kind"][0], n["smooth"]) for n in c["nodes"]]) for c in d.get(key) or []]
SQ_IN = [{"x": 100, "y": 100}, {"x": 100, "y": 200}, {"x": 200, "y": 200}, {"x": 200, "y": 100}]      # a clockwise counter inside TE_SQ
ARCH = {"points": [{"x": 105, "y": 104}, {"x": 398, "y": 104, "c1": {"x": 105, "y": 280}, "c2": {"x": 398, "y": 255}}], "closed": False}
A0 = {"name": "cpp1", "expected_contours": 1, "contours": [SQ_IN]}
for tag, body in (("2910a no expected_contours        ", {"name": "cpp1", "contours": [SQ_IN]}),
                  ("2910b an extra key                ", dict(A0, closed=True)),
                  ("2910c expected_contours 0         ", dict(A0, expected_contours=0)),
                  ("2910d expected_contours a bool    ", dict(A0, expected_contours=True)),
                  ("2910e expected_contours 1.0       ", dict(A0, expected_contours=1.0)),
                  ("2910f expected_contours 5001      ", dict(A0, expected_contours=5001)),
                  ("2910g empty name                  ", dict(A0, name=" ")),
                  ("2910h no contours                 ", dict(A0, contours=[])),
                  ("2910i a point without y           ", dict(A0, contours=[[{"x": 1}, {"x": 2, "y": 2}, {"x": 3, "y": 0}]])),
                  ("2910j c1 without c2               ", dict(A0, contours=[[{"x": 0, "y": 0}, {"x": 9, "y": 0, "c1": {"x": 1, "y": 1}}, {"x": 9, "y": 9}]])),
                  ("2910k 21 contours                 ", dict(A0, contours=[SQ_IN] * 21))):
    adc(tag, body, keys=("error",))
c, d = ns["_route"]("POST", "/glyph/contours/add", b"{not json").partition(b"\r\n\r\n")[0][9:12], None
print("2910l not JSON                     :", c.decode())
d = adc("2911 a straight counter           ", A0)
print("2911a  after                       :", adc_after(d), "| margins", d.get("margins"), "| repainted", d.get("display_refreshed"))
print("2911b  no before / expected on success:", "before" not in d, "expected_after" not in d, "| guard kind", ns["_guard_state"](ns["_open_font"]())["glyphs"].get("cpp1"))
d = adc("2912 a cubic circle beside       ", dict(A0, contours=[CIRC]), legacy=16)
print("2912a  new contour                 :", adc_after(d)[1:])
d = adc("2913 an open arch beside         ", dict(A0, contours=[ARCH]))
print("2913a  new contour                 :", adc_after(d)[1:])
d = adc("2914 a counter and an arch at once", dict(A0, contours=[SQ_IN, ARCH]), legacy=12)
print("2914a  order after                 :", [(c[0], len(c[1])) for c in adc_after(d)])
d = adc("2915 rule B                       ", dict(A0, contours=[[{"x": 100.5, "y": 100}, {"x": 100, "y": 200.4}, {"x": 200, "y": 200}, {"x": 200, "y": 100}]]))
print("2915a  new contour                 :", adc_after(d)[1:])
d = adc("2916a a stale expected_contours   ", dict(A0, expected_contours=2))
for tag, shapes in (("2916b an empty layer             ", lambda: []),
                    ("2916c two shapes                 ", lambda: [_contour(), TCShape([te_contour(TE_TRI)])]),
                    ("2916d a component                ", lambda: [_tc_comp("cppsrc")]),
                    ("2916e a Power Brush shape        ", lambda: [TCBrush()])):
    adc(tag, A0, shapes=shapes)
def _tx_contour(dx=10.0, m11=1.0):
    sh = _contour(); sh._tx = TCQT(m11, 0, 0, 1, dx, 0); return sh
adc("2916f an element offset           ", A0, shapes=lambda: [_tx_contour()])
adc("2916g a scale                     ", A0, shapes=lambda: [_tx_contour(0.0, 2.0)])
adc("2916h 1995 nodes + 4 new: allowed  ", A0, shapes=lambda: [TCShape([te_contour([(i, (i % 2) * 10) for i in range(1995)])])], legacy=1999)
adc("2916i 1997 nodes + 4 new: refused  ", A0, shapes=lambda: [TCShape([te_contour([(i, (i % 2) * 10) for i in range(1997)])])])
adc("2916j a smooth point off its line ", dict(A0, contours=[[{"x": 100, "y": 100}, {"x": 150, "y": 150, "smooth": True}, {"x": 200, "y": 100}]]))
adc("2916k a glyph that does not exist ", dict(A0, name="cppzz"))
adc("2916l an empty glyph without a layer", dict(A0, name="cppnolayer"), keys=AK + ("found",))
class TCOddComposite(TCShape):
    def isComposite(s): raise RuntimeError("isComposite boom")
adc("2916m isComposite unreadable      ", A0, shapes=lambda: [TCOddComposite([te_contour(TE_SQ)])])
for tag, mode in (("2917a addContour raises          ", {"addc_raises": 1}), ("2917b addContour does nothing     ", {"addc_drops": 1}),
                  ("2917c the new contour lands first  ", {"addc_first": 1}), ("2917d an old node moves          ", {"addc_moves_old": 1})):
    d = adc(tag, A0, mode=mode)
    if not d.get("added"):
        print("       before / expected / after  :", adc_after(d, "before"), "|", adc_after(d, "expected_after"), "|", adc_after(d))
adc("2917e the legacy view lags: not synced", A0, legacy=4)
adc("2917f an empty shape appears too  ", A0, mode={"addc_extra_shape": 1})
tls(lambda: [_contour()], legacy=8); P72["mode"]["noclose"] = 1
c, d = sbpost("/glyph/contours/add", A0)
print("2917g a closed contour stays open detached:", c, {k: d.get(k) for k in ("added", "changed", "reason")}, "| addContour calls:", TC["calls"].count("addContour"))
_srcac = "\n".join(l for l in src[src.index("# POST /glyph/contours/add (v0.207)"):src.index("# POST /glyph/contours/remove (v0.210)")].split("\n") if not l.lstrip().startswith("#"))
print("2918 static scan of add_contours: forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeShape|removeAllShapes|clearContours|replaceShape|removeContour|decomposite|ejectTo|activateBuilder|resetMetrics\w*|applyTransform)\s*\(|shapeBuilder|font\.update|resetInkBox", _srcac.replace("base.update(", "")),
      "| every refusal before the first addContour:", _srcac.rindex("nothing was added") < _srcac.index("sd.addContour(contour)"),
      "| one addContour call:", _srcac.count("sd.addContour(") == 1 and _srcac.count(".addContour(") == 2,
      "| v0.215 addShape call statements:", [l.strip() for l in _srcac.split("\n") if _re83.match(r"\s*\w+\.addShape\(", l)],
      "| after the addContour calls:", _srcac.index("sd.addContour(contour)") < _srcac.index("layer.addShape(new_shape)"))
print("2918a route documented:", "POST /glyph/contours/add" in src, "| dispatched:", 'if path == "/glyph/contours/add":' in src, "| mark title:",
      ns["_MARK_TITLES"].get("add_contours"), "| guard kind full:", "add_contours" in ns["_GUARD_FULL_KINDS"], "| activity kind:", ns["_ACT_WRITES"].get("/glyph/contours/add"),
      "| /glyph/path parses through the shared helper:", src.count("_route_path_contours(") == 3)
_ok_add = {"open": True, "added": True, "nodes_match": True, "changed": True, "synced_with_fontlab": True}
for tag, code, reply in (("2918b log, added              ", 200, _ok_add), ("2918c log, added, not synced  ", 200, dict(_ok_add, synced_with_fontlab=False)),
                         ("2918d log, refused            ", 200, {"open": True, "added": False, "reason": "the glyph holds 2 contour(s), not the expected 1"}),
                         ("2918e log, changed, not confirmed", 200, {"open": True, "added": False, "changed": True, "reason": "the re-read outline does not match the request"}),
                         ("2918f log, HTTP 400           ", 400, {"error": '"expected_contours" must be a whole number from 1 to 5000'})):
    print(tag, ":", ns["_act_describe_write"]("/glyph/contours/add", {"name": "cpp1", "expected_contours": 1, "contours": [SQ_IN, ARCH]}, code, reply),
          "| change verdict:", ns["_change_verdict"]("/glyph/contours/add", code, reply))
print("2918g log, one contour         :", ns["_act_describe_write"]("/glyph/contours/add", A0, 200, _ok_add))
print("2919 spies over the add_contours cases:", TC_FORBIDDEN)

# ================= v0.210: POST /glyph/contours/remove (remove_contours) =================
# The v0.207 fakes (tls, the glyph cpp1). TCShapeData gains removeContour, which removes that contour object from the shape's own list
# (the layer's getContours sees the same list); modes: remc_raises, remc_drops (does nothing), remc_wrong (removes the first contour
# instead), remc_extra_shape (an empty shape appears as well). _ask_yes_no is replaced by RCD: the answer it gives, and an optional edit of the glyph while the question is open.
# sync_drops_empty: the fake sync drops a shape left with no contour, as FontLab's does (ED7 1715, 1717).
print("\n==== v0.210 POST /glyph/contours/remove (remove_contours) ====")
def _tcsd_remc(s, c):
    idx = next((i for i, k in enumerate(s._contours) if k is c), None)
    TC["calls"].append(("removeContour", idx))
    m = TC["mode"]
    if m.get("remc_raises"): raise RuntimeError("removeContour boom")
    if m.get("remc_drops"): return
    if m.get("remc_wrong"): del s._contours[0]; return
    if m.get("remc_extra_shape"): P72["layers"]["cpp1"]._shapes.append(TCShape([]))     # an empty extra shape, which no contour check sees
    s._contours[:] = [k for k in s._contours if k is not c]
TCShapeData.removeContour = _tcsd_remc
RCD = {"answer": "yes", "seen": [], "during": None}
def _rcd_ask(title, text, seconds, outcome):
    RCD["seen"].append((title, text, seconds, outcome))
    if RCD["during"]: RCD["during"]()
    a = RCD["answer"]
    out = {"answer": a, "seconds": seconds}
    if a == "not_shown": out["error"] = "the dialog could not be set up to close by itself (boom); no dialog was shown"
    return out
_rcd_saved = ns["_ask_yes_no"]; ns["_ask_yes_no"] = _rcd_ask
RK = ("removed", "nodes_match", "changed", "glyph_empty", "shapes_after_sync", "contours_now", "mismatches", "reason", "edit_case",
      "contours_found", "user_declined", "not_answered", "dialog_error", "synced_with_fontlab", "fontlab_changed_mark", "error")
_sq_tri = lambda: [TCShape([te_contour(TE_SQ), te_contour(TE_TRI)])]
def E(i, n, x, y): return {"index": i, "node_count": n, "start": {"x": x, "y": y}}
R0 = {"name": "cpp1", "expected_contours": 2, "contours": [E(1, 3, 50, 50)]}
def rmc(tag, body, shapes=_sq_tri, mode=None, keys=RK, legacy=4, answer="yes", during=None, legacy_empty=False):
    tls(shapes, mode=mode, legacy=legacy)
    if legacy_empty: TS["cpp1"] = TsGlyph("cpp1", [TsLayer(0, 0)])
    RCD.update(answer=answer, seen=[], during=during)
    c, d = sbpost("/glyph/contours/remove", body)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| calls", [x for x in TC["calls"] if isinstance(x, tuple) and x[0] == "removeContour"],
          "| asked", len(RCD["seen"]), "| Update", TE["updates"], "| marks", TE["marks"])
    return d
for tag, body in (("2960a no expected_contours        ", {"name": "cpp1", "contours": [E(1, 3, 50, 50)]}),
                  ("2960b an extra key                ", dict(R0, force=True)),
                  ("2960c expected_contours 0         ", dict(R0, expected_contours=0)),
                  ("2960d no entry                    ", dict(R0, contours=[])),
                  ("2960e more entries than contours  ", dict(R0, contours=[E(0, 4, 0, 0), E(1, 3, 50, 50), E(1, 3, 50, 50)])),
                  ("2960f an entry without start      ", dict(R0, contours=[{"index": 1, "node_count": 3}])),
                  ("2960g index a bool                ", dict(R0, contours=[E(True, 3, 50, 50)])),
                  ("2960h node_count 0                ", dict(R0, contours=[E(1, 0, 50, 50)])),
                  ("2960i start out of range          ", dict(R0, contours=[E(1, 3, 50, 20001)])),
                  ("2960j the same contour twice      ", dict(R0, contours=[E(1, 3, 50, 50), E(1, 3, 50, 50)])),
                  ("2960k dialog_seconds 4.5          ", dict(R0, dialog_seconds=4.5)),
                  ("2960l empty name                  ", dict(R0, name=" "))):
    rmc(tag, body, keys=("error",))
c = ns["_route"]("POST", "/glyph/contours/remove", b"{not json").partition(b"\r\n\r\n")[0][9:12]
print("2960m not JSON                     :", c.decode())
d = rmc("2961 the triangle (contour 1)     ", R0)
print("2961a  after / removed / requested :", adc_after(d), "|", adc_after(d, "removed_contours"), "|", d.get("contours_requested"))
print("2961b  the question                :", RCD["seen"][0][0], "|", RCD["seen"][0][2], RCD["seen"][0][3], "|", RCD["seen"][0][1].replace("\n", " / "))
print("2961c  margins, no before on success:", d.get("margins"), "|", "before" not in d, "expected_after" not in d, "| guard kind",
      ns["_guard_state"](ns["_open_font"]())["glyphs"].get("cpp1"))
d = rmc("2962 the square (contour 0)       ", dict(R0, contours=[E(0, 4, 0, 0)]), legacy=3)
print("2962a  after                       :", adc_after(d))
d = rmc("2963 both, the sync drops the shape", dict(R0, contours=[E(0, 4, 0, 0), E(1, 3, 50, 50)]), mode={"sync_drops_empty": 1}, legacy_empty=True)
print("2963a  after / sync state / question:", adc_after(d), "|", d.get("state_after_sync"), "|", RCD["seen"][0][1].split("\n\n")[1])
rmc("2963b both, an empty shape stays   ", dict(R0, contours=[E(0, 4, 0, 0), E(1, 3, 50, 50)]), legacy_empty=True)
d = rmc("2963c one contour, the only one   ", {"name": "cpp1", "expected_contours": 1, "contours": [E(0, 4, 0, 0)]}, shapes=lambda: [_contour()],
        mode={"sync_drops_empty": 1}, legacy_empty=True)
print("2963d  margins absent when empty   :", "margins" not in d, "| removed_contours", adc_after(d, "removed_contours"))
rmc("2964a answered No                ", R0, answer="no")
d = rmc("2964b not answered in time         ", R0, answer="not_answered")
print("2964c  dialog                      :", d.get("dialog"))
rmc("2964d no dialog could be shown     ", R0, answer="not_shown")
rmc("2964e unclear                      ", R0, answer="unclear")
_rch = []   # v0.211: every "does not match the glyph" refusal ends once with the read-again hint
_rch.append(rmc("2965a a stale expected_contours    ", dict(R0, expected_contours=3)))
_rch.append(rmc("2965b a wrong node_count           ", dict(R0, contours=[E(1, 4, 50, 50)])))
_rch.append(rmc("2965c a wrong start                ", dict(R0, contours=[E(1, 3, 50, 51)])))
_rch.append(rmc("2965d an index past the end        ", dict(R0, contours=[E(2, 3, 50, 50)])))
_rch.append(rmc("2965e one good, one stale entry    ", dict(R0, contours=[E(0, 4, 0, 0), E(1, 3, 60, 50)])))
def _rcd_edit(): P72["layers"]["cpp1"]._shapes[0]._contours[1].rows[0]["x"] += 7.0
_rch.append(rmc("2966a the glyph is edited during the question", R0, during=_rcd_edit))
def _rcd_add(): P72["layers"]["cpp1"]._shapes[0]._contours.append(te_contour([(600, 600), (700, 600), (700, 700)]))
_rch.append(rmc("2966b a contour is added during it ", R0, during=_rcd_add))
_hint = "Read the glyph again with get_glyph_outline."
print("2966d v0.211 hint at the end, once:", [d.get("reason", "").endswith(_hint) and d.get("reason", "").count("get_glyph_outline") == 1 for d in _rch],
      "| not in problems:", not any("get_glyph_outline" in p for d in _rch for p in d.get("problems") or []))
def _rcd_shape(): P72["layers"]["cpp1"]._shapes.append(TCShape([te_contour(TE_TRI)]))
rmc("2966c a shape is added during it   ", R0, during=_rcd_shape)
for tag, shapes in (("2967a an empty layer             ", lambda: []),
                    ("2967b two shapes                 ", lambda: [_contour(), TCShape([te_contour(TE_TRI)])]),
                    ("2967c a component                ", lambda: [_tc_comp("cppsrc")]),
                    ("2967d a Power Brush shape        ", lambda: [TCBrush()]),
                    ("2967e an element offset          ", lambda: [_tx_contour()])):
    rmc(tag, R0, shapes=shapes)
rmc("2967f a glyph that does not exist ", dict(R0, name="cppzz"), keys=RK + ("found",))
rmc("2967g an empty glyph without a layer", dict(R0, name="cppnolayer"), keys=RK + ("found",))
for tag, mode in (("2968a removeContour raises       ", {"remc_raises": 1}), ("2968b removeContour does nothing  ", {"remc_drops": 1}),
                  ("2968c the wrong contour goes      ", {"remc_wrong": 1})):
    d = rmc(tag, R0, mode=mode)
    print("       before / expected / after  :", adc_after(d, "before"), "|", adc_after(d, "expected_after"), "|", adc_after(d))
rmc("2968d the legacy view lags: not synced", R0, legacy=7)
rmc("2968e an empty extra shape appears", R0, mode={"remc_extra_shape": 1})
_srcrc = "\n".join(l for l in src[src.index("# POST /glyph/contours/remove (v0.210)"):src.index("# POST /glyph/component (v0.169)")].split("\n") if not l.lstrip().startswith("#"))
_rcf = _srcrc[_srcrc.index("def remove_contours("):]
print("2969 static scan of remove_contours: forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeShape|removeAllShapes|clearContours|addShape|addContour|replaceShape|decomposite|ejectTo|activateBuilder|resetMetrics\w*|applyTransform)\s*\(|shapeBuilder|font\.update|resetInkBox", _srcrc.replace("base.update(", "")),
      "| one removeContour call:", _srcrc.count("sd.removeContour(") == 1 and _srcrc.count(".removeContour(") == 2, "| the question before it:", _rcf.index("_ask_yes_no(") < _rcf.index("sd.removeContour("),
      "| read again after the Yes:", _rcf.count("_remove_contours_read(name, w,") == 2 and _rcf.count("_remove_contours_problems(before,") == 2,
      "| highest index first:", "gone = sorted({p[\"index\"] for p in picks}, reverse=True)" in _rcf)
print("2969a route documented:", "POST /glyph/contours/remove" in src, "| dispatched:", 'if path == "/glyph/contours/remove":' in src, "| mark title:",
      ns["_MARK_TITLES"].get("remove_contours"), "| guard kind full:", "remove_contours" in ns["_GUARD_FULL_KINDS"], "| activity kind:",
      ns["_ACT_WRITES"].get("/glyph/contours/remove"), "| the delete question unchanged:", repr(ns["_deletion_text"]("x"))[:60])
_ok_rm = {"open": True, "removed": True, "nodes_match": True, "changed": True, "synced_with_fontlab": True, "dialog": {"answer": "yes", "seconds": 45}}
RB = {"name": "cpp1", "expected_contours": 2, "contours": [E(0, 4, 0, 0), E(1, 3, 50, 50)]}
for tag, code, reply in (("2969b log, removed            ", 200, _ok_rm), ("2969c log, removed, empty     ", 200, dict(_ok_rm, glyph_empty=True)),
                         ("2969d log, No                 ", 200, {"open": True, "removed": False, "changed": False, "user_declined": True, "reason": "the removal was not approved in FontLab (answered No)"}),
                         ("2969e log, not answered       ", 200, {"open": True, "removed": False, "changed": False, "not_answered": True, "dialog": {"answer": "not_answered", "seconds": 45}, "reason": "nobody answered"}),
                         ("2969f log, refused            ", 200, {"open": True, "removed": False, "changed": False, "reason": "the glyph holds 3 contour(s), not the expected 2"}),
                         ("2969g log, changed, not confirmed", 200, {"open": True, "removed": False, "changed": True, "reason": "the re-read outline does not match the request"}),
                         ("2969h log, HTTP 400           ", 400, {"error": "entry 0: contour 1 is named twice in this request"})):
    print(tag, ":", ns["_act_describe_write"]("/glyph/contours/remove", RB, code, reply), "| change verdict:", ns["_change_verdict"]("/glyph/contours/remove", code, reply))
print("2970 spies over the remove_contours cases:", TC_FORBIDDEN)

# ---- v0.207: the _EDIT_ACCEPTS grid. Every tool in the table runs against a glyph of every case (remove_component: the case's shapes
# plus the component it removes); a cell reads H (the tool reported success), R (refused, nothing changed) or X (anything else).
# A cell that departs from the table is listed with the tool's reason.
print("\n==== v0.207 the _EDIT_ACCEPTS grid: every edit tool against every case ====")
def _tc_comp_scaled():     # v0.215: a component scaled 200 % horizontally (component_transform)
    sh = _tc_comp("cppsrc"); sh._tx = TCQT(2, 0, 0, 1, 0, 0); return sh
GRID_CASES = {"empty": lambda: [], "one_plain_shape": lambda: [_contour()], "several_shapes": lambda: [_contour(), TCShape([te_contour(TE_TRI)])],
              "component": lambda: [_tc_comp("cppsrc")], "composite": lambda: [TCBrush()], "shape_transform": lambda: [_tx_contour()],
              "component_transform": lambda: [_tc_comp_scaled()]}
# v0.215: each body gets (shapes, contours, case): the glyph-wide contour count is the expected one, and add_contours names shape 0 where
# the glyph has two plain shapes (several_shapes here)
GRID_CALLS = {"draw_polygon": ("/glyph/polygon", "drawn", lambda n, nc=1, case="": {"name": "cpp1", "points": [[600, 600], [700, 600], [700, 700]]}),
              "draw_path": ("/glyph/path", "drawn", lambda n, nc=1, case="": {"name": "cpp1", "contours": [SQ_IN]}),
              "move_nodes": ("/glyph/move", "moved", lambda n, nc=1, case="": {"name": "cpp1", "moves": [M(0, 1, (400, 0), (450, 0))]}),
              "add_contours": ("/glyph/contours/add", "added", lambda n, nc=1, case="": dict(A0, expected_contours=max(nc, 1),
                                                                                                  **({"shape": 0} if case == "several_shapes" else {}))),
              "remove_contours": ("/glyph/contours/remove", "removed", lambda n, nc=1, case="": {"name": "cpp1", "expected_contours": max(nc, 1),
                                                                                                    "contours": [E(0, 4, 0, 0)]}),
              "add_component": ("/glyph/component", "placed", lambda n, nc=1, case="": PB0),
              "remove_component": ("/glyph/component/remove", "removed", lambda n, nc=1, case="": {"name": "cpp1", "index": n, "component": "cppsrc", "x": 0, "y": 0})}
print("grid tools match the table:", sorted(GRID_CALLS) == sorted(ns["_EDIT_ACCEPTS"]), "| cases match:", tuple(GRID_CASES) == ns["_EDIT_CASES"])
grid_departures = []
for tool, (route, flag, body) in GRID_CALLS.items():
    cells = []
    for case, shapes in GRID_CASES.items():
        made = (lambda s=shapes: s() + [_tc_comp("cppsrc")]) if tool == "remove_component" else shapes
        n = len(shapes())
        nc = sum(len(sh._contours) for sh in shapes())
        tls(made, mode=dict({"build_names_layer": 1, "add_activates": 1}, **({"sync_drops_empty": 1} if tool == "remove_contours" else {})),
            legacy=3 if case == "empty" and tool != "remove_component" else 7)
        RCD.update(answer="yes", seen=[], during=None)     # v0.210: remove_contours' question answered Yes
        TC["rm_calls"] = 0
        c, d = sbpost(route, body(n, nc, case))
        TC_FORBIDDEN.extend(TE["forbidden"])
        cell = "H" if d.get(flag) is True else ("R" if c == "200" and d.get("changed") in (None, False) and d.get(flag) is False else "X")
        cells.append(f"{case}={cell}")
        if (cell == "H") != ns["_EDIT_ACCEPTS"][tool][case]:
            grid_departures.append((tool, case, cell, str(d.get("reason") or d.get("error"))[:110]))
    print(f"{tool:17s}:", " ".join(cells))
print("departures from _EDIT_ACCEPTS:", grid_departures)
print("2920 spies over the grid:", TC_FORBIDDEN)

# ---- v0.212: the several-shapes refusal of the three edit tools says how many of the shapes are components (RX4 1791).
# v0.215: the three tools handle these glyphs now; the block shows each outcome (the request: the glyph-wide contour count, shape 0).
print("\n==== v0.212 the several-shapes refusal names the components (v0.215: handled) ====")
class TCOddComponent(TCShape):
    def isComponent(s): raise RuntimeError("isComponent boom")
SC_CASES = (("a plain shape and 1 component  ", lambda: [_contour(), _tc_comp("cppsrc")]),
            ("a plain shape and 2 components ", lambda: [_contour(), _tc_comp("cppsrc"), _tc_comp("cppsrc", 200, 0)]),
            ("isComponent unreadable         ", lambda: [_contour(), TCOddComponent([te_contour(TE_TRI)])]),
            ("two plain shapes (no component)", lambda: [_contour(), TCShape([te_contour(TE_TRI)])]))
for i, tool in enumerate(("move_nodes", "add_contours", "remove_contours")):
    route, flag, body = GRID_CALLS[tool]
    for j, (label, shapes) in enumerate(SC_CASES):
        tls(shapes, mode=dict({"build_names_layer": 1, "add_activates": 1}, **({"sync_drops_empty": 1} if tool == "remove_contours" else {})), legacy=7)
        RCD.update(answer="yes", seen=[], during=None)
        TC["rm_calls"] = 0
        c, d = sbpost(route, body(len(shapes()), sum(len(sh._contours) for sh in shapes()), "several_shapes"))
        TC_FORBIDDEN.extend(TE["forbidden"])
        print(f"2971{'abc'[i]}{j + 1} {tool:15s} {label}:", c, {k: d.get(k) for k in (flag, "reason", "edit_case", "shapes", "component_shapes",
                                                                                       "other_shapes_unchanged", "sources_unchanged") if k in d},
              "| asked", len(RCD["seen"]), "| Update", TE["updates"], "| marks", TE["marks"])
_sst = ns["_several_shapes_text"]
print("2971d _several_shapes_text:", [_sst(2, v) for v in (0, 1, 3, "not readable: x", None, True)])
print("2971e spies:", TC_FORBIDDEN)
# ---- v0.215: several shapes in move_nodes, add_contours and remove_contours (the user's design of 2026-11-25/26; research ED8-ED10).
# The v0.207 / v0.210 fakes (tls, the glyph cpp1); cppsrc is the triangle (50, 50) (150, 50) (100, 150), and a component of it shares its
# contour LIST (layer.getContours() gives the source's own contours, untransformed, as live ED8 1815). Extra modes, set here:
# ms_touch_src (an edit also moves a node of the source), ms_move_comp (an edit also moves the component's offset), ms_count_wrong (the
# first shape's contoursCount reads one more), ms_gc_disagree (a plain shape's getContours() gives its contours reversed).
print("\n==== v0.215 several shapes in the three edit tools ====")
_ms_addc_prev, _ms_remc_prev = TCShapeData.addContour, TCShapeData.removeContour
def _ms_side(s):
    m = TC["mode"]
    if m.get("ms_touch_src"): TCSRC["cppsrc"]._contours[0].rows[0]["x"] += 1.0
    if m.get("ms_move_comp"):
        for sh in P72["layers"]["cpp1"]._shapes:
            if sh._component: sh._tx = TCQT(1, 0, 0, 1, 999, 0)
def _ms_addc(s, c): _ms_addc_prev(s, c); _ms_side(s)
def _ms_remc(s, c): _ms_remc_prev(s, c); _ms_side(s)
TCShapeData.addContour, TCShapeData.removeContour = _ms_addc, _ms_remc
_ms_cc_prev = TCShape.contoursCount
def _ms_cc(s):
    n = _ms_cc_prev(s) if callable(_ms_cc_prev) else len(s._contours)
    shapes = P72["layers"]["cpp1"]._shapes
    return n + 1 if (TC["mode"].get("ms_count_wrong") and shapes and s is shapes[0]) else n
TCShape.contoursCount = _ms_cc
def _ms_gc(s):
    return list(reversed(s._contours)) if (TC["mode"].get("ms_gc_disagree") and not s._component) else list(s._contours)
TCShape.getContours = _ms_gc
MSK = ("moved", "added", "removed", "nodes_match", "changed", "edit_case", "shape", "plain_shapes", "new_contour_indices", "shapes_emptied",
       "glyph_empty", "other_shapes_unchanged", "sources_unchanged", "contour_counts_after", "mismatches", "reason", "problems", "error")
def ms(tag, route, body, shapes, mode=None, legacy=7, answer="yes"):
    tls(shapes, mode=dict({"build_names_layer": 1, "add_activates": 1, "sync_drops_empty": 1}, **(mode or {})), legacy=legacy)
    RCD.update(answer=answer, seen=[], during=None); TC["rm_calls"] = 0
    c, d = sbpost(route, body)
    TC_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in MSK if k in d}, "| calls", [x for x in TC["calls"] if x in ("addContour", "addShape") or (isinstance(x, tuple) and x[0] == "removeContour")],
          "| asked", len(RCD["seen"]), "| marks", len(TE["marks"]))
    return d
def ms_view(d, key="after"):
    return [[(n["x"], n["y"]) for n in c["nodes"]] for c in d.get(key) or []]
_pc = lambda: [_contour(), _tc_comp("cppsrc", 300, 0)]                    # a plain square, then a component at (300, 0)
_cp = lambda: [_tc_comp("cppsrc", 300, 0), _contour()]                    # the component first
_pp = lambda: [_contour(), TCShape([te_contour(TE_TRI)])]                 # two plain shapes
_pcc = lambda: [TCShape([te_contour(TE_SQ), te_contour([(500, 0), (600, 0), (550, 80)])]), _tc_comp("cppsrc", 300, 0)]   # 2 contours, a component
_cc = lambda: [_tc_comp("cppsrc", 300, 0), _tc_comp("cppsrc", 0, 400)]    # components only
MV_, AD_, RM_ = "/glyph/move", "/glyph/contours/add", "/glyph/contours/remove"
# move_nodes
d = ms("3001a move: plain shape, then a component", MV_, {"name": "cpp1", "moves": [M(0, 1, (400, 0), (450, 0))]}, _pc)
print("3001b  after (components at their offset):", ms_view(d), "| source now:", [(r["x"], r["y"]) for r in TCSRC["cppsrc"]._contours[0].rows])
d = ms("3001c move: the component first       ", MV_, {"name": "cpp1", "moves": [M(1, 1, (400, 0), (450, 0))]}, _cp)
print("3001d  after                         :", ms_view(d))
ms("3001e move: the component's contour     ", MV_, {"name": "cpp1", "moves": [M(1, 0, (50, 50), (60, 50))]}, _pc)
ms("3001f move: the component's contour, at its drawn place", MV_, {"name": "cpp1", "moves": [M(1, 0, (350, 50), (360, 50))]}, _pc)
d = ms("3001g move: two plain shapes in one call", MV_, {"name": "cpp1", "moves": [M(0, 1, (400, 0), (450, 0)), M(1, 0, (50, 50), (40, 40))]}, _pp)
print("3001h  after                         :", ms_view(d))
# add_contours
d = ms("3002a add: into the plain shape beside a component", AD_, dict(A0, expected_contours=2), _pc)
print("3002b  after                         :", ms_view(d))
d = ms("3002c add: component first, plain shape second", AD_, dict(A0, expected_contours=2), _cp)
print("3002d  after                         :", ms_view(d))
d = ms("3002e add: a plain shape of 2 contours, then a component", AD_, dict(A0, expected_contours=3), _pcc)
print("3002f  new contour index 2, the component's contour last:", d.get("new_contour_indices"), ms_view(d)[2:])
ms("3002g add: two plain shapes, no shape  ", AD_, dict(A0, expected_contours=2), _pp)
d = ms("3002h add: two plain shapes, shape 1   ", AD_, dict(A0, expected_contours=2, shape=1), _pp)
print("3002i  after                         :", ms_view(d))
ms("3002j add: shape names the component   ", AD_, dict(A0, expected_contours=2, shape=1), _pc)
ms("3002k add: shape 5 of 2                ", AD_, dict(A0, expected_contours=2, shape=5), _pc)
ms("3002l add: shape 0 on one plain shape  ", AD_, dict(A0, shape=0), lambda: [_contour()])
ms("3002m add: shape 1 on one plain shape  ", AD_, dict(A0, shape=1), lambda: [_contour()])
d = ms("3002n add: components only: a new shape", AD_, dict(A0, expected_contours=2), _cc)
print("3002o  after / new shape last, plain :", ms_view(d), "|", [(type(sh).__name__, sh._component) for sh in P72["layers"]["cpp1"]._shapes])
ms("3002p add: components only, with shape   ", AD_, dict(A0, expected_contours=2, shape=0), _cc)
ms("3002q add: the add moves the component ", AD_, dict(A0, expected_contours=2), _pc, mode={"ms_move_comp": 1})
ms("3002r add: shape is a bool             ", AD_, dict(A0, expected_contours=2, shape=True), _pc)
ms("3002s add: shape -1                    ", AD_, dict(A0, expected_contours=2, shape=-1), _pc)
# remove_contours
d = ms("3003a remove: a contour of a plain shape beside a component", RM_, {"name": "cpp1", "expected_contours": 3, "contours": [E(1, 3, 500, 0)]}, _pcc)
print("3003b  after / question             :", ms_view(d), "|", RCD["seen"][0][1].split("\n")[1] if RCD["seen"] else None)
ms("3003c remove: the component's contour   ", RM_, {"name": "cpp1", "expected_contours": 2, "contours": [E(1, 3, 50, 50)]}, _pc)
d = ms("3003d remove: empties the plain shape beside a component", RM_, {"name": "cpp1", "expected_contours": 2, "contours": [E(0, 4, 0, 0)]}, _pc)
print("3003e  after, shapes left            :", ms_view(d), "|", [sh._component for sh in P72["layers"]["cpp1"]._shapes])
ms("3003f remove: emptied shape stays (no sync drop)", RM_, {"name": "cpp1", "expected_contours": 2, "contours": [E(0, 4, 0, 0)]}, _pc,
   mode={"sync_drops_empty": 0})
d = ms("3003g remove: one contour from each of two plain shapes", RM_, {"name": "cpp1", "expected_contours": 2, "contours": [E(0, 4, 0, 0), E(1, 3, 50, 50)]}, _pp)
print("3003h  glyph empty, question         :", d.get("glyph_empty"), "|", RCD["seen"][0][1].split("\n\n")[1] if RCD["seen"] else None)
ms("3003i remove: the removal moves the source", RM_, {"name": "cpp1", "expected_contours": 3, "contours": [E(1, 3, 500, 0)]}, _pcc, mode={"ms_touch_src": 1})
ms("3003j remove: answered No              ", RM_, {"name": "cpp1", "expected_contours": 3, "contours": [E(1, 3, 500, 0)]}, _pcc, answer="no")
# refusals and unreadable states, before anything changes
for tag, shapes in (("3004a a scaled component beside      ", lambda: [_contour(), _tc_comp_scaled()]),
                    ("3004b a plain shape with an offset beside a component", lambda: [_contour(), _tc_comp("cppsrc", 300, 0), _tx_contour()]),
                    ("3004c a Power Brush shape beside     ", lambda: [_contour(), TCBrush()]),
                    ("3004d a lone scaled component        ", lambda: [_tc_comp_scaled()])):
    for route, body in ((MV_, {"name": "cpp1", "moves": [M(0, 1, (400, 0), (450, 0))]}), (AD_, dict(A0, expected_contours=2, shape=0)),
                        (RM_, {"name": "cpp1", "expected_contours": 2, "contours": [E(0, 4, 0, 0)]})):
        ms(tag + " " + route.split("/")[-1], route, body, shapes)
for tag, mode in (("3005a contoursCount disagrees      ", {"ms_count_wrong": 1}), ("3005b getContours() disagrees      ", {"ms_gc_disagree": 1})):
    ms(tag, MV_, {"name": "cpp1", "moves": [M(0, 1, (400, 0), (450, 0))]}, _pcc, mode=mode)
ms("3005c isComponent unreadable (add)    ", AD_, dict(A0, expected_contours=2), lambda: [_contour(), TCOddComponent([te_contour(TE_TRI)])])
_srcms = "\n".join(l for l in src[src.index("# v0.215: several shapes in the three edit tools"):src.index("def _several_shapes_text(")].split("\n") if not l.lstrip().startswith("#"))
print("3006 static scan of the shared helpers: forbidden call syntax:",
      _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|removeShape|removeAllShapes|clearContours|addShape|addContour|removeContour|replaceShape|decomposite|ejectTo|activateBuilder|resetMetrics\w*|applyTransform)\s*\(|shapeBuilder|font\.update|resetInkBox", _srcms),
      "| getContours() call sites:", sorted(set(_re83.findall(r"\b\w+\.getContours\(\)", _srcms))))
print("3006a the remove route: removeContour calls:", _srcrc.count("sd.removeContour("), "| the add route: addShape calls:", _srcac.count(".addShape("),
      [l.strip()[:70] for l in _srcac.split("\n") if ".addShape(" in l])
# v0.216 (MS 1870, 1871): a component's contour refused on its own path, before the stale checks; add_contours names the shape it added to
d = ms("3008a move: a component's contour and a stale from", MV_, {"name": "cpp1", "moves": [M(0, 1, (999, 0), (450, 0)), M(1, 0, (50, 50), (60, 50))]}, _pc)
print("3008b  read-again hint in it         :", "Read the glyph again" in (d.get("reason") or ""), "| stale move named:", "999" in (d.get("reason") or ""))
d = ms("3008c move: two components' contours", MV_, {"name": "cpp1", "moves": [M(1, 0, (50, 50), (60, 50)), M(2, 0, (50, 50), (60, 50))]},
       lambda: [_contour(), _tc_comp("cppsrc", 300, 0), _tc_comp("cppsrc", 0, 400)])
print("3008d  problems                      :", d.get("problems"))
ms("3008e move: a stale from alone, beside a component", MV_, {"name": "cpp1", "moves": [M(0, 1, (999, 0), (450, 0))]}, _pc)
ms("3008f add: one plain shape, no shape    ", AD_, dict(A0), lambda: [_contour()])
ms("3008g add: refused, shape left out      ", AD_, dict(A0, expected_contours=2), _pp)
ms("3008h add: one plain shape beside 2 components, the new contour goes to shape 1", AD_, dict(A0, expected_contours=3),
   lambda: [_tc_comp("cppsrc", 300, 0), _contour(), _tc_comp("cppsrc", 0, 400)])
ms("3008i add: not confirmed (the component moved): no shape", AD_, dict(A0, expected_contours=2), _pc, mode={"ms_move_comp": 1})
print("3007 spies:", TC_FORBIDDEN)
TCShapeData.addContour, TCShapeData.removeContour = _ms_addc_prev, _ms_remc_prev
TCShape.contoursCount = _ms_cc_prev
ns["_ask_yes_no"] = _rcd_saved; del TCShapeData.removeContour     # v0.210: the real dialog and the plain fake again
del TCShape.getContours     # v0.215
TCShapeData.componentLayer = _tcsd_layer_orig
TCLayer.buildAuto = _tc_build181
del TCLayer.setActive; del TCLayer.isActive
TCLayer.addShape = _tc_add_orig
del TCLayer.advanceWidth
for _m, _v in _tl_saved:
    if _v is None:
        if hasattr(_m, "flLayer"): delattr(_m, "flLayer")
    else:
        _m.flLayer = _v
P72Mod.activeLayer = _p72_active
for _a in ("layers", "addLayer", "removeLayer"):
    if _a in P72Mod.__dict__: delattr(P72Mod, _a)
TCLayer.buildAuto = _tc_build165
del TCShape.contoursCount
TCLayer.removeShape = _tc_remove_shape
P72Mod.advanceWidth = _p72_adv
for _a in ("removeShape", "clearComponents"):
    if _a in TCLayer.__dict__: delattr(TCLayer, _a)
TCShape.transform = _tc_tx_prop
for _a in ("inkBox",):
    if _a in TCShape.__dict__: delattr(TCShape, _a)
del TOPkg.mastersCount
for _a in ("recipe", "autoLayer", "buildAuto", "killAuto"):
    if _a in TCLayer.__dict__: delattr(TCLayer, _a)
TCLayer.setGlyphComponents = _tc_set_orig
if "generateGlyph" in TOPkg.__dict__: del TOPkg.generateGlyph
for _m, _a, _v in _tc_gen_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)
qg.QTransform = QTransformStub
for _m, _a, _v in _tc_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)
for _a in ("transform",):
    if _a in TEShape.__dict__: delattr(TEShape, _a)
for _a, _v in _te_p72_saved.items():
    if _v is None:
        if _a in P72Mod.__dict__: delattr(P72Mod, _a)
    else:
        setattr(P72Mod, _a, _v)
for _m, _a, _v in _te_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else:
        setattr(_m, _a, _v)

# ================= v0.196: one gated flGlyph.advanceWidth read =================
print("\n==== v0.196 /debug/tryadvancewidth: names-only, then one gated read ====")
class AdvanceWidthModern:
    reads = 0
    def __init__(s, glyph, font): s.g = glyph; s.name = glyph.name; s.fgGlyphId = glyph.id
    def isValid(s): return True
    @property
    def advanceWidth(s):
        type(s).reads += 1
        return 512.0
_aw_old_cf = getattr(_fm, "CountFonts", None)
_aw_old_cur = _fm.CurrentFont
_aw_old_cls = getattr(_fm, "flGlyph", None)
_fm.CountFonts = lambda: 1
_fm.CurrentFont = lambda: TsFont()
_fm.flGlyph = AdvanceWidthModern
ts_reset(); ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
ns["_TRYADVANCEWIDTH"]["calls"] = 0; AdvanceWidthModern.reads = 0
c, d = call("/debug/tryadvancewidth?name=tri&stage=names")
print("2590 names-only         :", c, d.get("advance_width_listed"), "| read", d.get("read_performed"), "| calls", AdvanceWidthModern.reads)
c, d = call("/debug/tryadvancewidth?name=tri&stage=read")
print("2591 read without go    :", c, d.get("error"), "| calls", AdvanceWidthModern.reads, "| budget", ns["_TRYADVANCEWIDTH"]["calls"])
c, d = call("/debug/tryadvancewidth?name=tri&stage=read&go=yes")
print("2592 gated read         :", c, d.get("advance_width"), "| wrapper", d.get("wrapper"), "| count", d.get("glyph_count_before"), d.get("glyph_count_after"),
      "| side effect", d.get("side_effect_detected"), "| calls", AdvanceWidthModern.reads, d.get("calls_so_far"))
_fm.CurrentFont = _aw_old_cur
if _aw_old_cf is None:
    if hasattr(_fm, "CountFonts"): delattr(_fm, "CountFonts")
else: _fm.CountFonts = _aw_old_cf
if _aw_old_cls is None:
    if hasattr(_fm, "flGlyph"): delattr(_fm, "flGlyph")
else: _fm.flGlyph = _aw_old_cls

# ================= v0.198: get_glyph_width reads advanceWidth, the legacy glyph.width as a cross-check (AW4 1470-1489) =================
print("\n==== v0.198 /glyph/width: modern advanceWidth, legacy cross-check, legacy fallback ====")
class GwSpyGlyph(TsGlyph):
    touched = []
    def __getattribute__(s, a):
        if a in ("layer", "layers", "bodyLayer"): type(s).touched.append(a)
        return object.__getattribute__(s, a)
class GwBadGlyph(GwSpyGlyph):
    @property
    def width(s): raise RuntimeError("legacy boom")
    @width.setter
    def width(s, v): pass
class GwModern:
    mode = "ok"; adv = 500.0; reads = 0
    def __init__(s, glyph, font):
        if type(s).mode == "wrapper": raise RuntimeError("no wrapper")
        s.name = glyph.name; s.fgGlyphId = glyph.id
    def isValid(s): return True
    @property
    def activeLayer(s):
        if type(s).mode == "layer_raises": raise RuntimeError("layer boom")
        return None if type(s).mode == "nolayer" else object()
    @property
    def advanceWidth(s):
        type(s).reads += 1
        if type(s).mode == "adv_raises": raise RuntimeError("adv boom")
        return "x" if type(s).mode == "adv_nan" else type(s).adv
_gw_old_cf = getattr(_fm, "CountFonts", None); _gw_old_cur = _fm.CurrentFont; _gw_old_cls = getattr(_fm, "flGlyph", None)
_fm.CountFonts = lambda: 1; _fm.CurrentFont = lambda: TsFont(); _fm.flGlyph = GwModern
def gw(mode="ok", adv=500.0, legacy=500.0, name="g1"):
    TS.clear(); g = (GwBadGlyph if legacy == "raises" else GwSpyGlyph)(name, [TsLayer(1, 3)])
    if legacy != "raises": g.width = legacy
    TS[name] = g; ns["_MODERN_CACHE"].clear(); ns["_MODERN_CACHE_FONT"][0] = None
    GwModern.mode = mode; GwModern.adv = adv; GwModern.reads = 0; GwSpyGlyph.touched = []
    c, d = call("/glyph/width?name=" + name)
    return c, {k: d.get(k) for k in ("width", "source", "advance_width", "legacy_width", "modern_reason", "legacy_error", "readable", "reason") if k in d}
for lbl, kw in (("2600 both equal         ", {}), ("2601 disagree 438/437.5 ", {"adv": 438.0, "legacy": 437.5}),
                ("2602 no active layer    ", {"mode": "nolayer"}), ("2603 wrapper raises     ", {"mode": "wrapper"}),
                ("2604 activeLayer raises ", {"mode": "layer_raises"}), ("2605 advanceWidth raises", {"mode": "adv_raises"}),
                ("2606 advanceWidth no num", {"mode": "adv_nan"}), ("2607 legacy raises      ", {"legacy": "raises"}),
                ("2608 both fail          ", {"mode": "adv_raises", "legacy": "raises"})):
    c, d = gw(**kw)
    print(lbl, ":", c, d, "| advanceWidth reads", GwModern.reads, "| legacy layer touched", GwSpyGlyph.touched)
c, d = call("/glyph/width?name=nosuch"); print("2609 unknown glyph      :", c, d)
_fm.CurrentFont = _gw_old_cur
if _gw_old_cf is None:
    if hasattr(_fm, "CountFonts"): delattr(_fm, "CountFonts")
else: _fm.CountFonts = _gw_old_cf
if _gw_old_cls is None:
    if hasattr(_fm, "flGlyph"): delattr(_fm, "flGlyph")
else: _fm.flGlyph = _gw_old_cls

# ================= v0.199: /debug/trykerngroupedit (gated research probe that WRITES: rename or remove ONE kerning group) =================
print("\n==== v0.199 /debug/trykerngroupedit ====")
GE = {"cfg": {}, "groups": {}, "table": {}, "renames": [], "removes": [], "gets": [], "groups_calls": 0, "kerning_args": [],
      "pkg_all": set(), "pkg_forbidden": [], "k_all": set(), "k_forbidden": [], "g_all": set(), "g_forbidden": []}
_GE_K_FORBIDDEN = tuple(n for n in _FK_FORBIDDEN if n != "groups")
_GE_PKG_FORBIDDEN = tuple(n for n in _PK_PKG_FORBIDDEN if n != "getAllGroups")
_GE_G_ALLOWED = ("items", "rename", "remove")
_GE_MODES = {"left": "KernLeft", "right": "KernRight", "both": "KernBothSide"}
def _ge_forbid(where, n):
    GE[where + "_forbidden"].append(n)
    raise SystemExit("FORBIDDEN " + where + " member touched: " + n)
class GEGroups:
    # the master's kerning group container: only items(), rename() and remove() (and len()) may be used; no subscript, no iteration
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GE["g_all"].add(n)
            if n not in _GE_G_ALLOWED: _ge_forbid("g", n)
        return object.__getattribute__(self, n)
    def __getitem__(self, k): _ge_forbid("g", "__getitem__")
    def __setitem__(self, k, v): _ge_forbid("g", "__setitem__")
    def __delitem__(self, k): _ge_forbid("g", "__delitem__")
    def __iter__(self): _ge_forbid("g", "__iter__")
    def __len__(self): return 3 if GE["cfg"].get("len_stale") else sum(1 for g in GE["groups"].values() if g["kern"])
    def items(self):
        GE["items_calls"] = GE.get("items_calls", 0) + 1
        m = GE["cfg"].get("items")
        if m == "raise" or (m == "raise_after" and GE["renames"] + GE["removes"]): raise RuntimeError("items boom")
        out = [(n, (list(g["members"]), _GE_MODES[g["side"]])) for n, g in GE["groups"].items() if g["kern"] and n not in GE["cfg"].get("hide_items", ())]
        return out + [(n, (list(GE["groups"][n]["members"]), _GE_MODES[GE["groups"][n]["side"]])) for n in GE["cfg"].get("items_twice", ())]
    def rename(self, old, new):
        GE["renames"].append((old, new))
        m = GE["cfg"].get("rename", "ok")
        if m == "raise": raise RuntimeError("rename boom")
        if m == "false": return False
        if m == "list_keeps_old": GE["stale_list"].append([True, old, GE["groups"][old]["id"], 0, list(GE["groups"][old]["members"])])
        if m == "ignore": return None
        g = dict(GE["groups"][old])
        if m == "lose_member": g["members"] = g["members"][:-1] or ["ge4"]
        if m == "new_id": g["id"] = g["id"] + 100
        if m != "copy": del GE["groups"][old]
        GE["groups"][new] = g
        if GE["cfg"].get("move_entries", True):
            for key in [k for k in GE["table"] if (old, True) in k]:
                value = GE["table"][key] if GE["cfg"].get("move_entries") == "copy" else GE["table"].pop(key)
                GE["table"][tuple((new, True) if s == (old, True) else s for s in key)] = value
        if m == "then_raise": raise RuntimeError("rename boom after renaming")
        return True
    def remove(self, name, *more):
        GE["removes"].append((name,) + more)
        m = GE["cfg"].get("remove", "ok")
        if m == "raise": raise RuntimeError("remove boom")
        if m == "ignore": return None
        GE["groups"].pop(name, None)
        if more and more[0] is True:
            for key in [k for k in GE["table"] if (name, True) in k]: GE["table"].pop(key)
        if m == "then_raise": raise RuntimeError("remove boom after removing")
        return None
GE_GROUPS = GEGroups()
class GEKern:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GE["k_all"].add(n)
            if n in _GE_K_FORBIDDEN: _ge_forbid("k", n)
        return object.__getattribute__(self, n)
    def __getitem__(self, k): _ge_forbid("k", "__getitem__")
    def __len__(self): return len(GE["table"])
    @property
    def groups(self):
        m = GE["cfg"].get("groups_attr")
        if m == "raise": raise RuntimeError("groups boom")
        if m == "callable": return lambda: None
        return GE_GROUPS
    def get(self, key):
        GE["gets"].append(key)
        return GE["table"].get(key)
class GEPackage:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GE["pkg_all"].add(n)
            if n in _GE_PKG_FORBIDDEN: _ge_forbid("pkg", n)
        return object.__getattribute__(self, n)
    def isNull(self): return False
    @property
    def masters(self): return GE["cfg"].get("masters", ["Regular"])
    @property
    def master(self): return GE["cfg"].get("master", "Regular")
    def getAllGroups(self):
        GE["groups_calls"] += 1
        m = GE["cfg"].get("all_groups")
        if m == "raise" or (m == "raise_after" and GE["renames"] + GE["removes"]): raise RuntimeError("getAllGroups boom")
        out = [[g["kern"], n, g["id"], 0, list(g["members"])] for n, g in GE["groups"].items() if n not in GE["cfg"].get("hide_list", ())]
        return out + [[True, n, GE["groups"][n]["id"] + 1, 0, list(GE["groups"][n]["members"])] for n in GE["cfg"].get("list_twice", ())] + GE["stale_list"]
    @property
    def kerning(self):
        def _kerning(*args):
            GE["kerning_args"].append(args)
            if GE["cfg"].get("kerning_call") == "raise": raise RuntimeError("kerning() boom")
            return GEKern()
        return _kerning
class GEWorkspace:
    @staticmethod
    def instance(): return GE_WS
    def packages(self): return [GE_PKG] * GE["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return GE_PKG
GE_PKG = GEPackage(); GE_WS = GEWorkspace()
class GEFont:
    glyphs = [PKGlyph(n) for n in ("ge1", "ge2", "ge3", "ge4", ".notdef")]
_ge_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace")]
def ge_setup(calls=0, **cfg):
    GE["cfg"] = dict(cfg)
    GE["groups"] = {"geL": {"kern": True, "id": 5121, "members": ["ge1", "ge2"], "side": "left"},
                    "geR": {"kern": True, "id": 5122, "members": ["ge3"], "side": "right"},
                    "geB": {"kern": True, "id": 5123, "members": ["ge4"], "side": "both"},
                    "geF": {"kern": False, "id": 5125, "members": ["ge1"], "side": "left"}}
    if cfg.get("members_differ"): GE["cfg"]["hide_items"] = ("geL",); GE["cfg"]["items_twice"] = ()
    GE["table"] = {(("geL", True), ("ge4", False)): -60.0, (("ge1", False), ("geR", True)): -40.0, (("ge1", False), ("ge4", False)): -10.0}
    for k in ("renames", "removes", "gets", "kerning_args", "stale_list"): GE[k] = []
    GE["groups_calls"] = 0; GE["items_calls"] = 0
    ns["_TRYKGEDIT"]["calls"] = calls
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = GEWorkspace
        _m.CountFonts = lambda: count
        _m.CurrentFont = lambda: GEFont()
_GEQ = "/debug/trykerngroupedit?go=yes"
_GER = ("error", "call", "called", "call_error", "returned", "renamed", "old_name_gone", "new_name_in_items", "new_name_in_class_list", "group_after", "table_len_before", "table_len_after",
        "groups_len_before", "groups_len_after", "entry_before", "entry_after_old_name", "entry_after_new_name", "entry_followed", "calls_so_far")
_GEX = ("error", "call", "called", "call_error", "removed", "old_name_gone", "still_in_items", "still_in_class_list", "table_entries_removed",
        "groups_len_before", "groups_len_after", "entry_before", "entry_after_old_name", "entry_gone", "calls_so_far")
def gec(tag, path, keys=None):
    c, d = call(path)
    shown = {k: v for k, v in d.items() if k != "note"} if keys is None else {k: d.get(k) for k in keys if k in d}
    print(tag, ":", c, shown, "| kerning() args", GE["kerning_args"], "| renames", GE["renames"], "| removes", GE["removes"],
          "| getAllGroups calls", GE["groups_calls"], "| items calls", GE["items_calls"])
    return c, d
ge_setup(); gec("2807 no go: nothing runs        ", "/debug/trykerngroupedit?op=rename&name=geL&new=geL2")
ge_setup(); gec("2808 go=maybe: nothing runs     ", "/debug/trykerngroupedit?op=rename&name=geL&new=geL2&go=maybe")
ge_setup(); c, d = gec("2809 rename left geL, glyph ge4  ", _GEQ + "&op=rename&name=geL&new=geL2&glyph=ge4", keys=_GER)
print("2809b note: may change, no mark, no save:", "may have changed" in d.get("note", "") and "not marked" in d.get("note", "") and "nothing is saved" in d.get("note", ""),
      "| group_before", d.get("group_before"), "| entry key side", d.get("entry_key_side"), "| gets", GE["gets"])
ge_setup(); gec("2810 rename right geR, glyph ge1 ", _GEQ + "&op=rename&name=geR&new=geR2&glyph=ge1", keys=_GER); print("2810b gets:", GE["gets"])
ge_setup(); gec("2811 rename both geB, no glyph   ", _GEQ + "&op=rename&name=geB&new=geB2", keys=_GER); print("2811b gets:", GE["gets"])
ge_setup(move_entries=False); gec("2812 rename: entries stay behind ", _GEQ + "&op=rename&name=geL&new=geL2&glyph=ge4", keys=_GER)
ge_setup(); gec("2812b rename: no entry before    ", _GEQ + "&op=rename&name=geL&new=geL2&glyph=ge3", keys=("renamed", "entry_before", "entry_followed"))
ge_setup(move_entries="copy"); gec("2812c rename: entries copied     ", _GEQ + "&op=rename&name=geL&new=geL2&glyph=ge4", keys=("renamed", "entry_after_old_name", "entry_after_new_name", "entry_followed"))
ge_setup(rename="false"); gec("2813 rename returns False       ", _GEQ + "&op=rename&name=geL&new=geL2&glyph=ge4", keys=_GER)
ge_setup(rename="ignore"); gec("2813b rename changes nothing     ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER)
ge_setup(rename="raise"); gec("2814 rename raises (counted)    ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER)
ge_setup(rename="then_raise"); gec("2814b rename raises after renaming", _GEQ + "&op=rename&name=geL&new=geL2", keys=("call_error", "renamed", "old_name_gone", "group_after"))
ge_setup(rename="copy"); gec("2815 rename keeps the old name   ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER)
ge_setup(rename="list_keeps_old"); gec("2815b class list still names the old", _GEQ + "&op=rename&name=geL&new=geL2", keys=("renamed", "old_name_gone", "groups_len_before", "groups_len_after", "kerning_groups_listed_after"))
ge_setup(rename="lose_member"); gec("2816 rename loses a member       ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER)
ge_setup(rename="new_id"); gec("2817 rename changes the id       ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER)
ge_setup(); gec("2818 remove geR, pairs=keep      ", _GEQ + "&op=remove&name=geR&pairs=keep&glyph=ge1", keys=_GEX)
ge_setup(); gec("2819 remove geL, pairs=delete    ", _GEQ + "&op=remove&name=geL&pairs=delete&glyph=ge4", keys=_GEX)
ge_setup(); gec("2819b remove geB, no entry, keep  ", _GEQ + "&op=remove&name=geB&pairs=keep&glyph=ge1", keys=("removed", "entry_before", "entry_gone", "table_entries_removed"))
ge_setup(remove="ignore"); gec("2820 remove changes nothing     ", _GEQ + "&op=remove&name=geR&pairs=keep", keys=_GEX)
ge_setup(remove="raise"); gec("2821 remove raises (counted)    ", _GEQ + "&op=remove&name=geR&pairs=delete", keys=_GEX)
ge_setup(remove="then_raise"); gec("2821b remove raises after removing", _GEQ + "&op=remove&name=geR&pairs=keep", keys=("call_error", "removed", "old_name_gone", "groups_len_after"))
ge_setup(len_stale=True); gec("2821c group count does not drop   ", _GEQ + "&op=remove&name=geR&pairs=keep", keys=("removed", "old_name_gone", "groups_len_before", "groups_len_after"))
for tag, q in (("2822a unknown op               ", "&op=copy&name=geL&new=geL2"), ("2822b bad name                 ", "&op=rename&name=ge:L&new=geL2"),
               ("2822c new the same as name     ", "&op=rename&name=geL&new=geL"), ("2822d rename without new       ", "&op=rename&name=geL"),
               ("2822e bad new                  ", "&op=rename&name=geL&new=" + "x" * 64), ("2822f rename with pairs        ", "&op=rename&name=geL&new=geL2&pairs=keep"),
               ("2822g remove with new          ", "&op=remove&name=geL&new=geL2&pairs=keep"), ("2822h remove without pairs     ", "&op=remove&name=geL"),
               ("2822i remove pairs=all         ", "&op=remove&name=geL&pairs=all"), ("2822j bad glyph name           ", "&op=remove&name=geL&pairs=keep&glyph=g%20h"),
               ("2822k glyph not in the font    ", "&op=remove&name=geL&pairs=keep&glyph=Q"), ("2822l new is a glyph name      ", "&op=rename&name=geL&new=ge3"),
               ("2822m new is a kerning group   ", "&op=rename&name=geL&new=geR"), ("2822n new is an OpenType class  ", "&op=rename&name=geL&new=geF"),
               ("2822o unknown group           ", "&op=remove&name=geQ&pairs=keep"), ("2822p an OpenType class        ", "&op=remove&name=geF&pairs=keep"),
               ("2822q a glyph, not a group     ", "&op=remove&name=ge1&pairs=keep")):
    ge_setup(); gec(tag, _GEQ + q, keys=("error", "group_before", "calls_so_far"))
ge_setup(hide_items=("geL",)); gec("2822r class list only, not items()", _GEQ + "&op=rename&name=geL&new=geL2", keys=("error", "group_before", "calls_so_far"))
ge_setup(hide_list=("geL",)); gec("2822s items() only, not class list", _GEQ + "&op=rename&name=geL&new=geL2", keys=("error", "group_before", "calls_so_far"))
ge_setup(list_twice=("geL",)); gec("2822t class list names it twice   ", _GEQ + "&op=remove&name=geL&pairs=keep", keys=("error", "group_before", "calls_so_far"))
ge_setup(items_twice=("geL",)); gec("2822u items() names it twice      ", _GEQ + "&op=remove&name=geL&pairs=keep", keys=("error", "group_before", "calls_so_far"))
for tag, over in (("2823a getAllGroups raises  ", dict(all_groups="raise")), ("2823b items() raises       ", dict(items="raise")),
                  ("2823c kerning.groups raises ", dict(groups_attr="raise")), ("2823d kerning.groups callable", dict(groups_attr="callable")),
                  ("2823e kerning() raises (counted)", dict(kerning_call="raise"))):
    ge_setup(**over); gec(tag, _GEQ + "&op=rename&name=geL&new=geL2", keys=("error", "calls_so_far"))
ge_setup(items="raise_after"); gec("2824a items() fails after rename ", _GEQ + "&op=rename&name=geL&new=geL2", keys=_GER + ("items_error_after", "new_name_in_items", "new_name_in_class_list"))
ge_setup(all_groups="raise_after"); gec("2824b class list fails after remove", _GEQ + "&op=remove&name=geR&pairs=keep", keys=_GEX + ("class_list_error_after",))
for tag, over in (("2825a no font open        ", dict(count=0)), ("2825b two fonts open      ", dict(count=2)), ("2825c two packages        ", dict(packages=2)),
                  ("2825d masters not all names", dict(masters=["Regular", 5])), ("2825e current master unlisted", dict(master="Ghost"))):
    ge_setup(**over); gec(tag, _GEQ + "&op=rename&name=geL&new=geL2", keys=("open", "error", "calls_so_far"))
ge_setup(calls=9); gec("2826 request 10 allowed       ", _GEQ + "&op=rename&name=geL&new=geL2", keys=("renamed", "calls_so_far", "max_calls"))
GE["renames"].clear(); GE["kerning_args"].clear(); GE["groups_calls"] = 0; GE["items_calls"] = 0
gec("2826b request 11 refused      ", _GEQ + "&op=rename&name=geB&new=geB2", keys=("error", "calls_so_far", "max_calls"))
ge_setup(); _ge_real = ns["debug_try_kern_group_edit"]
ns["debug_try_kern_group_edit"] = _pk_boom; gec("2827 probe raises: HTTP 500    ", _GEQ + "&op=rename&name=geL&new=geL2"); ns["debug_try_kern_group_edit"] = _ge_real
for k in ("pkg_all", "k_all", "g_all"): GE[k] = set()
for k in ("pkg_forbidden", "k_forbidden", "g_forbidden"): GE[k] = []
for _q in ("&op=rename&name=geL&new=geL2&glyph=ge4", "&op=rename&name=geR&new=geR2&glyph=ge1", "&op=remove&name=geB&pairs=keep&glyph=ge1",
           "&op=remove&name=geL&pairs=delete&glyph=ge4", "&op=rename&name=geF&new=geF2", "&op=remove&name=geQ&pairs=keep"):
    ge_setup(); call(_GEQ + _q)
print("2828 spy over all cases          : forbidden package members:", GE["pkg_forbidden"], "| package members touched anywhere:", sorted(GE["pkg_all"]),
      "| forbidden kerning members:", GE["k_forbidden"], "| kerning members touched anywhere:", sorted(GE["k_all"]),
      "| forbidden group container members:", GE["g_forbidden"], "| group container members touched:", sorted(GE["g_all"]))
_ge_src = src[src.index("_TRYKGEDIT = {"):src.index("# /debug/trymodern (v0.88)")]
_ge_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _ge_src).splitlines())
print("2829 static scan                 : pkg members used:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _ge_code))),
      "| kerning members used:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _ge_code))), "| container members used:", sorted(set(_re83.findall(r"\bcontainer\.(\w+)", _ge_code))),
      "| editor( calls:", len(_re83.findall(r"\beditor\(", _ge_code)), "| kerning_of( calls:", len(_re83.findall(r"\bkerning_of\(", _ge_code)),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|remove\w*|update\w*|Update\w*|add\w*|clear\w*|keys|values|items|has_key|assign\w*|replace\w*|delete\w*|asDict|getPlain\w*|setPlain\w*|scale|rename\w*|autoKern|findGroup|set|notify\w*)\(", _ge_code),
      "| del statements:", len(_re83.findall(r"\bdel\b", _ge_code)),
      "| subscripts on other objects:", sorted(set(s for s in _re83.findall(r"\b(\w+)\[", _ge_code) if s not in ("_TRYKGEDIT", "r", "out"))),
      "| counter raised before the first kerning call:", _ge_code.index('_TRYKGEDIT[""] += 1') < _ge_code.index("kerning_of(current)") < _ge_code.index("editor(name"),
      "| scanned chars > 6000:", len(_ge_src) > 6000)
print("2830 gate, cap, route, docstring  :", "go != \"yes\"" in _ge_src, "| max requests", ns["_TRYKGEDIT_MAX"], "| route registered once:", src.count('path == "/debug/trykerngroupedit"') == 1,
      "| listed in the module docstring:", "/debug/trykerngroupedit" in src[:src.index('"""', 3)])
ns["_TRYKGEDIT"]["calls"] = 0
for _m, _a, _v in _ge_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)

# ================= v0.200: POST /kerning/group/rename and /kerning/group/remove (product routes; fakes with spies) =================
print("\n==== v0.200 /kerning/group/rename and /kerning/group/remove ====")
# Fakes: the master's group container (only items, rename, remove and len; any other member, a subscript or an iteration aborts), the
# table (get, len, groups), the package (getAllGroups returns None when no group is left, as FontLab did in GL 1531), and glyphs whose
# legacy kerningLeft / kerningRight lag behind an edit until notifyPackageContentUpdated (GE 1512, GR 1528). The mark and the dialog are
# recorders; the refresh is the real _refresh_kerning_panel with a fake flItems.
GP = {"cfg": {}, "groups": {}, "table": {}, "glyph_ids": {}, "renames": [], "removes": [], "dialogs": [], "marks": [], "refreshes": [],
      "order": [], "groups_calls": 0, "items_calls": 0, "pkg_all": set(), "pkg_forbidden": [], "k_all": set(), "k_forbidden": [],
      "g_all": set(), "g_forbidden": []}
_GP_K_FORBIDDEN = tuple(n for n in _FK_FORBIDDEN if n != "groups")
_GP_PKG_FORBIDDEN = tuple(n for n in _PK_PKG_FORBIDDEN if n != "getAllGroups")
_GP_G_ALLOWED = ("items", "rename", "remove")
_GP_MODES = {"left": "KernLeft", "right": "KernRight", "both": "KernBothSide"}
def _gp_forbid(where, n):
    GP[where + "_forbidden"].append(n)
    raise SystemExit("FORBIDDEN " + where + " member touched: " + n)
def _gp_ids_now():
    ids = {}
    for name, g in GP["groups"].items():
        if not g["kern"]: continue
        for m in g["members"]:
            left, right = ids.get(m, (0, 0))
            if g["side"] in ("left", "both"): left = g["id"]
            if g["side"] in ("right", "both"): right = g["id"]
            ids[m] = (left, right)
    return ids
class GPGroups:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GP["g_all"].add(n)
            if n not in _GP_G_ALLOWED: _gp_forbid("g", n)
        return object.__getattribute__(self, n)
    def __getitem__(self, k): _gp_forbid("g", "__getitem__")
    def __setitem__(self, k, v): _gp_forbid("g", "__setitem__")
    def __delitem__(self, k): _gp_forbid("g", "__delitem__")
    def __iter__(self): _gp_forbid("g", "__iter__")
    def __len__(self):
        if GP["cfg"].get("len_stale"): return GP["cfg"]["len_stale"]
        return sum(1 for g in GP["groups"].values() if g["kern"])
    def items(self):
        GP["items_calls"] += 1
        if GP["cfg"].get("items") == "raise" or (GP["cfg"].get("items") == "raise_after" and GP["renames"] + GP["removes"]): raise RuntimeError("items boom")
        hide = GP["cfg"].get("hide_items", ())
        return [(n, (list(g["members"][:-1] if n in GP["cfg"].get("short_items", ()) else g["members"]), _GP_MODES[g["side"]]))
                for n, g in GP["groups"].items() if g["kern"] and n not in hide]
    def rename(self, old, new):
        GP["renames"].append((old, new)); GP["order"].append("rename")
        m = GP["cfg"].get("rename", "ok")
        if m == "raise": raise RuntimeError("rename boom")
        if m == "false": return False
        g = dict(GP["groups"][old])
        g["id"] = g["id"] + 2                                   # FontLab gave the renamed group a new id (GE 1511: 5140 -> 5142)
        if m == "lose_member": g["members"] = g["members"][:-1]
        if m != "copy": del GP["groups"][old]
        GP["groups"][new] = g
        for key in [k for k in GP["table"] if (old, True) in k]:
            GP["table"][tuple((new, True) if s == (old, True) else s for s in key)] = GP["table"].pop(key)
        if m == "drop_entry": GP["table"].pop(next(iter(GP["table"])))
        if m == "list_keeps_old": GP["stale_list"].append([True, old, g["id"] - 2, 0, list(g["members"])])
        if m == "then_raise": raise RuntimeError("rename boom after renaming")
        return True
    def remove(self, name, *more):
        GP["removes"].append((name,) + more); GP["order"].append("remove")
        m = GP["cfg"].get("remove", "ok")
        if m == "raise": raise RuntimeError("remove boom")
        if m == "ignore": return None
        GP["groups"].pop(name, None)
        if more and more[0] is True:
            for key in [k for k in GP["table"] if (name, True) in k]: GP["table"].pop(key)
        if m == "then_raise": raise RuntimeError("remove boom after removing")
        return None
GP_GROUPS = GPGroups()
class GPKern:
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GP["k_all"].add(n)
            if n in _GP_K_FORBIDDEN: _gp_forbid("k", n)
        return object.__getattribute__(self, n)
    def __getitem__(self, k): _gp_forbid("k", "__getitem__")
    def __len__(self): return len(GP["table"])
    @property
    def groups(self):
        m = GP["cfg"].get("groups_attr")
        if m == "raise": raise RuntimeError("groups boom")
        if m == "callable": return lambda: None
        return GP_GROUPS
    def get(self, key): return GP["table"].get(key)
class GPPackage:
    fgId = 4186
    def __getattribute__(self, n):
        if not n.startswith("_"):
            GP["pkg_all"].add(n)
            if n in _GP_PKG_FORBIDDEN: _gp_forbid("pkg", n)
        return object.__getattribute__(self, n)
    def isNull(self): return False
    @property
    def path(self): return GP["cfg"].get("pkg_path", "")
    @property
    def masters(self): return GP["cfg"].get("masters", ["Regular"])
    @property
    def master(self): return GP["cfg"].get("master", "Regular")
    def getAllGroups(self):
        GP["groups_calls"] += 1
        m = GP["cfg"].get("all_groups")
        if m == "raise" or (m == "raise_after" and GP["renames"] + GP["removes"]): raise RuntimeError("getAllGroups boom")
        out = [[g["kern"], n, g["id"], 0, list(g["members"])] for n, g in GP["groups"].items() if n not in GP["cfg"].get("hide_list", ())]
        out += [[True, n, GP["groups"][n]["id"] + 1, 0, list(GP["groups"][n]["members"])] for n in GP["cfg"].get("list_twice", ())]
        out += GP["stale_list"]
        return out or None                                      # ".../Nothing" when no group is left (GL 1531)
    @property
    def kerning(self):
        def _kerning(*args):
            if GP["cfg"].get("kerning_call") == "raise": raise RuntimeError("kerning() boom")
            return GPKern()
        return _kerning
class GPWorkspace:
    @staticmethod
    def instance(): return GP_WS
    def packages(self): return [GP_PKG] * GP["cfg"].get("packages", 1)
    @property
    def currentPackage(self): return GP_PKG
GP_PKG = GPPackage(); GP_WS = GPWorkspace()
class GPGlyph:
    def __init__(self, n): self.name = n
    @property
    def kerningLeft(self):
        if GP["cfg"].get("ids") == "raise": raise RuntimeError("ids boom")
        return GP["glyph_ids"].get(self.name, (0, 0))[0]
    @property
    def kerningRight(self): return GP["glyph_ids"].get(self.name, (0, 0))[1]
class GPInfo:
    familyName = "Group Test"; styleName = "Regular"
class GPFont:
    info = GPInfo()
    glyphs = [GPGlyph(n) for n in ("ge1", "ge2", "ge3", "ge4", "ge5", ".notdef")]
    @property
    def path(self): return GP["cfg"].get("font_path", "")
class GPItems:
    @staticmethod
    def notifyPackageContentUpdated(pid):
        GP["refreshes"].append(pid); GP["order"].append("refresh")
        if GP["cfg"].get("refresh_works", True): GP["glyph_ids"] = _gp_ids_now()
_gp_saved = [(m, a, getattr(m, a, None)) for m in _tf_mods for a in ("CountFonts", "CurrentFont", "flWorkspace", "flItems")]
_gp_keep = {k: ns[k] for k in ("_confirm_group_removal", "_mark_through_first")}
def _gp_mark(font, candidates, how):
    GP["marks"].append((list(candidates), how)); GP["order"].append("mark")
    return {"called": True, "via_glyph": candidates[0] if candidates else None, "glyph_has_changes": True}
def _gp_dialog(text, seconds=45):
    GP["dialogs"].append(text); GP["order"].append("dialog"); GP["dialog_seconds"] = seconds
    answer = GP["cfg"].get("answer", True)          # v0.203: the dialog's result; True / False are Yes / No
    answer = {True: "yes", False: "no"}.get(answer, answer)
    return {"answer": answer, "seconds": seconds} if answer != "not_shown" else {"answer": answer, "seconds": seconds, "error": "set-up boom"}
def gp_setup(**cfg):
    GP["cfg"] = dict(cfg)
    GP["groups"] = {"geL": {"kern": True, "id": 5140, "members": ["ge1", "ge2"], "side": "left"},
                    "geR": {"kern": True, "id": 5141, "members": ["ge3", "ge4"], "side": "right"},
                    "geB": {"kern": True, "id": 5148, "members": ["ge5"], "side": "both"},
                    "geF": {"kern": False, "id": 5150, "members": ["ge1"], "side": "left"}}
    for n in cfg.get("only", ()) and [k for k in list(GP["groups"]) if k not in cfg["only"]]: del GP["groups"][n]
    GP["table"] = {(("geL", True), ("ge4", False)): -60.0, (("ge1", False), ("geR", True)): -40.0, (("ge1", False), ("ge4", False)): -10.0}
    GP["glyph_ids"] = _gp_ids_now()
    for k in ("renames", "removes", "dialogs", "marks", "refreshes", "order", "stale_list"): GP[k] = []
    GP["groups_calls"] = GP["items_calls"] = 0
    count = cfg.get("count", 1)
    for _m in _tf_mods:
        _m.flWorkspace = GPWorkspace; _m.CountFonts = lambda: count; _m.CurrentFont = lambda: (None if cfg.get("no_current") else GPFont())
        _m.flItems = GPItems
    ns["_confirm_group_removal"] = _gp_dialog; ns["_mark_through_first"] = _gp_mark
def gpp(tag, path, payload, keys=None, raw=False):
    body = payload if raw else json.dumps(payload).encode("utf-8")
    r = ns["_route"]("POST", path, body); h, _, b = r.partition(b"\r\n\r\n")
    d = json.loads(b)
    shown = d if keys is None else {k: d.get(k) for k in keys if k in d}
    print(tag, ":", h.split(b"\r\n")[0].decode()[9:12], shown, "| renames", GP["renames"], "| removes", GP["removes"], "| dialogs", len(GP["dialogs"]),
          "| order", GP["order"])
    return d
_RN, _RM = "/kerning/group/rename", "/kerning/group/remove"
_GPK = ("error", "renamed", "removed", "changed", "user_declined", "returned", "id_before", "id_after", "same_name_glyph", "group_after",
        "table_size_before", "table_size_after", "groups_before", "groups_after", "still_in_items", "still_in_class_list", "reason", "call_error",
        "fontlab_changed_mark", "fontlab_panel_refresh", "fontlab_caught_up")
print("--- rename")
gp_setup(); d = gpp("2831 rename geL -> geL2           ", _RN, {"group": "geL", "new_name": "geL2"})
print("2831b marked through members      :", GP["marks"], "| refreshed with fgId:", GP["refreshes"], "| table keys follow:", sorted(k[0][0] for k in GP["table"] if k[0][1]))
gp_setup(); gpp("2832 rename to a glyph's name ge3", _RN, {"group": "geL", "new_name": "ge3"}, keys=("renamed", "same_name_glyph", "id_after", "fontlab_caught_up"))
gp_setup(); gpp("2832b rename the right group geR  ", _RN, {"group": "geR", "new_name": "geR2"}, keys=("renamed", "fontlab_caught_up"))
gp_setup(); gpp("2832c rename the both group geB   ", _RN, {"group": "geB", "new_name": "geB2"}, keys=("renamed", "fontlab_caught_up"))
gp_setup(refresh_works=False); gpp("2833 FontLab does not catch up   ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "fontlab_caught_up"))
gp_setup(ids="raise"); gpp("2833b the member's id unreadable ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "fontlab_caught_up"))
gp_setup(rename="false"); gpp("2834 rename returns False        ", _RN, {"group": "geL", "new_name": "geL2"}, keys=_GPK)
gp_setup(rename="raise"); gpp("2834b rename raises              ", _RN, {"group": "geL", "new_name": "geL2"}, keys=_GPK)
gp_setup(rename="then_raise"); gpp("2835 renamed, then raises        ", _RN, {"group": "geL", "new_name": "geL2"}, keys=_GPK)
gp_setup(rename="copy"); gpp("2836 the old name stays too      ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "changed", "reason", "fontlab_changed_mark"))
gp_setup(rename="lose_member"); gpp("2837 a member lost               ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "changed", "reason"))
gp_setup(rename="list_keeps_old"); gpp("2837b the class list keeps the old name", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "changed", "reason", "groups_before", "groups_after"))
gp_setup(rename="drop_entry"); gpp("2837c a kerning entry went too    ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "changed", "reason", "table_size_before", "table_size_after"))
gp_setup(items="raise_after"); gpp("2838 items() fails after the call", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "changed", "reason", "fontlab_changed_mark"))
print("--- rename refused before any change")
for tag, body in (("2839a new name is a kerning group ", {"group": "geL", "new_name": "geR"}), ("2839b new name is an OpenType class", {"group": "geL", "new_name": "geF"}),
                  ("2839c the same name               ", {"group": "geL", "new_name": "geL"}), ("2839d a bad group name           ", {"group": "ge L", "new_name": "x"}),
                  ("2839e a bad new name             ", {"group": "geL", "new_name": "x" * 64}), ("2839f an unknown group           ", {"group": "geQ", "new_name": "x"}),
                  ("2839g an OpenType class as group ", {"group": "geF", "new_name": "x"}), ("2839h a glyph, not a group       ", {"group": "ge1", "new_name": "x"}),
                  ("2839i another key in the body    ", {"group": "geL", "new_name": "x", "go": "yes"}), ("2839j new_name missing           ", {"group": "geL"}),
                  ("2839k a number as name           ", {"group": 5, "new_name": "x"})):
    gp_setup(); gpp(tag, _RN, body, keys=("error", "group_before"))
gp_setup(); gpp("2839l body not JSON              ", _RN, b"group=geL", raw=True)
gp_setup(short_items=("geL",)); gpp("2839m the sources' members differ ", _RN, {"group": "geL", "new_name": "x"}, keys=("error", "group_before"))
gp_setup(list_twice=("geL",)); gpp("2839n the class list names it twice", _RN, {"group": "geL", "new_name": "x"}, keys=("error",))
gp_setup(all_groups="raise"); gpp("2839o getAllGroups raises        ", _RN, {"group": "geL", "new_name": "x"}, keys=("error",))
gp_setup(groups_attr="callable"); gpp("2839p kerning.groups callable    ", _RN, {"group": "geL", "new_name": "x"}, keys=("error",))
gp_setup(count=0); gpp("2840a no font open               ", _RN, {"group": "geL", "new_name": "x"})
gp_setup(count=2); gpp("2840b two fonts, unsaved         ", _RN, {"group": "geL", "new_name": "x"}, keys=("error",))
gp_setup(count=2, font_path="C:/f/a.vfc", pkg_path="C:/f/a.vfc"); gpp("2840c two fonts, matched by path  ", _RN, {"group": "geL", "new_name": "x"}, keys=("renamed", "matched_by", "fonts_open"))
gp_setup(master="Ghost"); gpp("2840d current master unlisted   ", _RN, {"group": "geL", "new_name": "x"}, keys=("error",))
print("--- remove")
gp_setup(); d = gpp("2841 remove geR, keep, Yes        ", _RM, {"group": "geR", "pairs": "keep"})
print("2841b the dialog's text           :", GP["dialogs"][0].replace("\n", " / "))
gp_setup(); gpp("2842 remove geL, delete, Yes      ", _RM, {"group": "geL", "pairs": "delete"}, keys=("removed", "table_size_before", "table_size_after", "fontlab_caught_up"))
print("2842b the dialog's text           :", GP["dialogs"][0].replace("\n", " / "))
gp_setup(answer=False); gpp("2843 answered No                 ", _RM, {"group": "geR", "pairs": "keep"}, keys=_GPK)
gp_setup(only=("geR",)); gpp("2844 the last group (list None after)", _RM, {"group": "geR", "pairs": "delete"}, keys=("removed", "still_in_class_list", "groups_after", "fontlab_caught_up"))
gp_setup(remove="raise"); gpp("2845 remove raises               ", _RM, {"group": "geR", "pairs": "keep"}, keys=_GPK)
gp_setup(remove="ignore"); gpp("2845b remove changes nothing      ", _RM, {"group": "geR", "pairs": "keep"}, keys=_GPK)
gp_setup(remove="then_raise"); gpp("2845c removed, then raises        ", _RM, {"group": "geR", "pairs": "keep"}, keys=("removed", "changed", "call_error", "fontlab_changed_mark"))
gp_setup(len_stale=3); gpp("2845d group count does not drop   ", _RM, {"group": "geR", "pairs": "keep"}, keys=("removed", "changed", "reason"))
gp_setup(all_groups="raise_after"); gpp("2845e class list fails after   ", _RM, {"group": "geR", "pairs": "keep"}, keys=("removed", "changed", "reason", "fontlab_changed_mark"))
gp_setup(refresh_works=False); gpp("2845f FontLab does not catch up   ", _RM, {"group": "geB", "pairs": "keep"}, keys=("removed", "fontlab_caught_up"))
print("--- remove refused before the dialog (dialogs must stay 0)")
for tag, body in (("2846a an unknown group            ", {"group": "geQ", "pairs": "keep"}), ("2846b an OpenType class          ", {"group": "geF", "pairs": "keep"}),
                  ("2846c pairs missing              ", {"group": "geR"}), ("2846d pairs 'all'                ", {"group": "geR", "pairs": "all"}),
                  ("2846e pairs true                 ", {"group": "geR", "pairs": True}), ("2846f a bad name                 ", {"group": "", "pairs": "keep"})):
    gp_setup(); gpp(tag, _RM, body, keys=("error",))
gp_setup(); GP["groups"]["geR"]["members"] = ["ge3"] + [f"m{i}" for i in range(11)]; GP["glyph_ids"] = _gp_ids_now()
gpp("2847 twelve members              ", _RM, {"group": "geR", "pairs": "keep"}, keys=("removed",)); print("2847b dialog:", GP["dialogs"][0].replace("\n", " / "))
_mk = ns["_MARK_CHANGED"]; ns["_MARK_CHANGED"] = False
gp_setup(); gpp("2848 the mark switched off       ", _RN, {"group": "geL", "new_name": "geL2"}, keys=("renamed", "fontlab_changed_mark"))
ns["_MARK_CHANGED"] = _mk
print("--- the OUTPUT lines")
_aw = ns["_act_describe_write"]
for tag, path, body, reply in (
        ("2849a renamed            ", _RN, {"group": "geL", "new_name": "geL2"}, {"open": True, "renamed": True, "new_name": "geL2", "id_before": 5140, "id_after": 5142, "fontlab_caught_up": {"caught_up": True}}),
        ("2849b renamed, lags      ", _RN, {"group": "geL", "new_name": "geL2"}, {"open": True, "renamed": True, "new_name": "geL2", "id_before": 5140, "id_after": 5142, "fontlab_caught_up": {"checked": False}}),
        ("2849c refused            ", _RN, {"group": "geL", "new_name": "geR"}, {"open": True, "error": "'geR' is already the name of a kerning group in this font; nothing was renamed"}),
        ("2849d not confirmed      ", _RN, {"group": "geL", "new_name": "x"}, {"open": True, "renamed": False, "reason": "the re-read does not confirm the rename: the old name is still listed"}),
        ("2849e removed, keep      ", _RM, {"group": "geR", "pairs": "keep"}, {"open": True, "removed": True, "pairs": "keep", "table_size_before": 3, "table_size_after": 4, "fontlab_caught_up": {"caught_up": True}}),
        ("2849f removed, delete    ", _RM, {"group": "geL", "pairs": "delete"}, {"open": True, "removed": True, "pairs": "delete", "table_size_before": 3, "table_size_after": 2, "fontlab_caught_up": {"caught_up": True}}),
        ("2849g answered No        ", _RM, {"group": "geR", "pairs": "keep"}, {"open": True, "removed": False, "user_declined": True}),
        ("2849h HTTP 400           ", _RM, {"group": "geR"}, {"error": "the body must be a JSON object with \"group\" and \"pairs\" and nothing else"}),
        ("2849i no font            ", _RM, {"group": "geR", "pairs": "keep"}, {"open": False})):
    print(tag, ":", _aw(path, body, 400 if "2849h" in tag else 200, reply))
print("--- spies and scans")
for k in ("pkg_all", "k_all", "g_all"): GP[k] = set()
for k in ("pkg_forbidden", "k_forbidden", "g_forbidden"): GP[k] = []
for _p, _b in ((_RN, {"group": "geL", "new_name": "geL2"}), (_RN, {"group": "geL", "new_name": "geR"}), (_RM, {"group": "geR", "pairs": "keep"}),
               (_RM, {"group": "geL", "pairs": "delete"}), (_RM, {"group": "geQ", "pairs": "keep"})):
    gp_setup(); ns["_route"]("POST", _p, json.dumps(_b).encode("utf-8"))
print("2850 spy over all cases          : forbidden package members:", GP["pkg_forbidden"], "| package members touched:", sorted(GP["pkg_all"]),
      "| forbidden kerning members:", GP["k_forbidden"], "| kerning members touched:", sorted(GP["k_all"]),
      "| forbidden group container members:", GP["g_forbidden"], "| group container members touched:", sorted(GP["g_all"]))
_gp_src = src[src.index("def _confirm_group_removal("):src.index("def set_glyph_unicode(")] + _rag_src
_gp_code = "\n".join(l.split("#")[0] for l in _re83.sub(r'"(?:[^"\\\n]|\\.)*"', '""', _gp_src).splitlines())
_gp_body = _re83.sub(r'(?s)"""(.*?)"""', '', _gp_code)
_gp_plain = "\n".join(l for l in _re83.sub(r'(?s)"""(.*?)"""', '', _gp_src).splitlines() if not l.lstrip().startswith("#"))
print("2851 static scan                 : container members used:", sorted(set(_re83.findall(r'(?:\["container"\]|\bcontainer)\.(\w+)', _gp_plain))),
      "| renamer( calls:", len(_re83.findall(r"\brenamer\(", _gp_body)), "| remover( calls:", len(_re83.findall(r"\bremover\(", _gp_body)),
      "| pkg members:", sorted(set(_re83.findall(r"\bpkg\.(\w+)", _gp_body))), "| kerning members:", sorted(set(_re83.findall(r"\bkerning\.(\w+)", _gp_body))),
      "| forbidden syntax:", _re83.findall(r"\.(?:save\w*|close|export\w*|release|set|update\w*|Update\w*|add\w*|clear\w*|keys|values|assign\w*|replace\w*|delete\w*|deleteGroups|asDict|getPlain\w*|setPlain\w*|scale|renameGroup|addGroup|deleteGroup)\(",
                                         _gp_body.replace("out.update(", "").replace("check.update(", "").replace("twice.add(", "").replace("other.add(", "")
                                         .replace("refused.update(", "")),
      "| del statements:", len(_re83.findall(r"\bdel\b", _gp_body)),
      "| names subscripted:", sorted(set(_re83.findall(r"\b(\w+)\[", _gp_body))),
      "| scanned chars > 9000:", len(_gp_src) > 9000)
print("2852 routes, docstring, log, mark:", src.count('if path in ("/kerning/group/rename", "/kerning/group/remove"):') == 1,
      "| in the module docstring:", all(p in src[:src.index('"""', 3)] for p in ("POST /kerning/group/rename", "POST /kerning/group/remove")),
      "| write log kinds:", ns["_ACT_WRITES"].get(_RN), "/", ns["_ACT_WRITES"].get(_RM), "| mark title:", ns["_MARK_TITLES"].get("kerning_group"),
      "| the dialog is the self-closing one:", "_ask_yes_no(" in src[src.index("def _confirm_group_removal("):src.index("# v0.200 - renaming")],
      "| its default No:", "box.setDefaultButton(QMessageBox.No)" in src[src.index("def _ask_yes_no("):src.index("def _confirm_deletion(")])
ns.update(_gp_keep)
for _m, _a, _v in _gp_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)

# ================= v0.201: /debug/trydialogtimeout (gated research probe, UI only: a dialog that closes itself) =================
print("\n==== v0.201 /debug/trydialogtimeout ====")
DT = {"boxes": [], "timers": [], "mode": "timeout", "connect": "ok", "exec": "ok", "open_font_calls": 0,
      "button": "ok", "connect_tick": "ok", "ticks_before_click": 0}
class DTButton:                               # as in PythonQt (SC 1591, 1592): text is a property, setText a method
    def __init__(s, t): s.text = t; s.sets = []
    def setText(s, t):
        s.sets.append(t)
        if DT["button"] == "raise_set" or (DT["button"] == "raise_set_late" and len(s.sets) == 3) or \
                (DT["button"] == "raise_set_from3" and len(s.sets) >= 3): raise RuntimeError("setText boom " + str(len(s.sets)))
        s.text = t
class DTButtonM:                              # a binding where text is a method
    def __init__(s, t): s._t = t; s.sets = []
    def text(s): return s._t
    def setText(s, t): s.sets.append(t); s._t = t
class DTBox:                                  # recording QMessageBox: the timer's reject() or a click ends exec_()
    Question, Yes, No = "Question", 16384, 65536
    def __init__(s, icon, title, text, buttons):
        s.icon, s.title, s.text, s.buttons = icon, title, text, buttons
        s.default = None; s.rejected = 0; s.clicked = None; s.res = None; s.execs = 0
        kind = DTButtonM if DT["button"] == "method" else DTButton
        s.btns = {DTBox.Yes: kind("&Yes"), DTBox.No: kind("&No")}
        DT["boxes"].append(s)
    def setDefaultButton(s, b): s.default = b
    def reject(s): s.rejected += 1; s.res = 0
    def clickedButton(s): return s.clicked
    def result(s): return s.res
    def button(s, which): return None if DT["button"] == "none" else s.btns.get(which)
    def exec_(s):
        s.execs += 1
        if DT["exec"] == "raise": raise RuntimeError("exec boom")
        close = [t for t in DT["timers"] if t.single is True][-1]
        n = close.interval // 1000 - (0 if DT.get("tick_at_close") else 1) if DT["mode"] == "timeout" else DT["ticks_before_click"]
        for t in [t for t in DT["timers"] if t.single is False]:
            for _ in range(n): t.fire()
        if DT["mode"] == "timeout":
            close.fire()
            return 0 if s.rejected else -1
        s.clicked = s.btns[DTBox.Yes if DT["mode"] == "yes" else DTBox.No]; s.res = DTBox.Yes if DT["mode"] == "yes" else DTBox.No
        return s.res
class DTTimer:                                # recording QtCore.QTimer
    def __init__(s, parent):
        s.parent = parent; s.single = None; s.interval = None; s.active = False; s.signal = None; s.target = None; s.stops = 0
        s.starts = 0; s.fired = 0
        DT["timers"].append(s)
    def setSingleShot(s, v): s.single = v
    def setInterval(s, ms): s.interval = ms
    def connect(s, signal, *target):
        if DT["connect"] == "raise": raise TypeError("connect boom")
        if DT["connect"] == "false": return False
        if s.single is False and DT["connect_tick"] == "false": return False
        s.signal, s.target = signal, target
        return True
    def start(s): s.active = True; s.starts += 1
    def stop(s): s.active = False; s.stops += 1
    def isActive(s): return s.active
    def fire(s):
        if not s.active: return
        if s.single: s.active = False
        s.fired += 1
        if len(s.target) == 2:
            if s.target[1] == "reject()": s.target[0].reject()
        else:
            s.target[0]()
_dt_saved = (ns["QMessageBox"], getattr(ns["QtCore"], "QTimer", None), ns["_open_font"])
def _dt_open_font(*a, **k):
    DT["open_font_calls"] += 1
    return _dt_saved[2](*a, **k)
ns["QMessageBox"] = DTBox; ns["QtCore"].QTimer = DTTimer; ns["_open_font"] = _dt_open_font
def dt(q, mode="timeout", connect="ok", exec_="ok", button="ok", connect_tick="ok", ticks_before_click=0):
    DT.update(mode=mode, connect=connect, exec=exec_, button=button, connect_tick=connect_tick, ticks_before_click=ticks_before_click)
    DT["boxes"].clear(); DT["timers"].clear()
    return call("/debug/trydialogtimeout?" + q)
def _dt_keys(d, *keys): return {k: d.get(k) for k in keys}
ns["_TRYDIALOGTIMEOUT"]["calls"] = 0
c, d = dt("how=slot&seconds=10")
print("2853 without go              :", c, "| dialog_started", d["dialog_started"], "| plan:", d.get("plan"), "| dialogs made", len(DT["boxes"]),
      "| calls", d["calls_so_far"], "/", d["max_calls"])
_dt_bad = []
for q in ("how=bogus&seconds=10&go=yes", "how=&seconds=10&go=yes", "how=slot&seconds=2&go=yes", "how=slot&seconds=51&go=yes",
          "how=slot&seconds=abc&go=yes", "how=slot&go=yes", "how=slot&seconds=%EF%BC%91%EF%BC%90&go=yes", "how=slot&seconds=010&go=yes",
          "how=python&seconds=-5&go=yes"):
    c, d = dt(q); _dt_bad.append((q.replace("&go=yes", ""), c, d.get("error")))
print("2854 refusals                :", _dt_bad, "| dialogs made", len(DT["boxes"]), "| calls", ns["_TRYDIALOGTIMEOUT"]["calls"])
c, d = dt("how=slot&seconds=10&go=yes")
b, t = DT["boxes"][0], DT["timers"][0]
print("2855 slot, no click          :", c, _dt_keys(d, "dialog_started", "connected", "exec_result", "result_is_yes", "clicked_button",
      "closed_without_click", "dialog_result", "timer_active_after", "calls_so_far", "font_touched"),
      "| elapsed is a number:", isinstance(d.get("elapsed_s"), float), "| timer_fired in the reply:", "timer_fired" in d)
print("2856 the dialog and its timer:", b.icon, "|", b.title, "|", b.text.splitlines()[0], "|", b.text.splitlines()[-1], "| buttons", b.buttons,
      "| default", b.default, "| timer owned by the dialog:", t.parent is b, "| single shot", t.single, "| interval", t.interval,
      "| connected", t.signal, "to the dialog:", t.target[0] is b, t.target[1], "| stopped", t.stops, "| rejected", b.rejected, "| exec_", b.execs)
c, d = dt("how=slot&seconds=20&go=yes", mode="yes")
print("2857 slot, Yes clicked       :", c, _dt_keys(d, "exec_result", "result_is_yes", "clicked_button", "closed_without_click", "dialog_result",
      "timer_active_after"), "| stopped", DT["timers"][0].stops, "| rejected", DT["boxes"][0].rejected)
c, d = dt("how=python&seconds=10&go=yes")
t = DT["timers"][0]
print("2858 python, no click        :", c, _dt_keys(d, "connected", "exec_result", "result_is_yes", "clicked_button", "closed_without_click",
      "timer_fired", "timer_active_after"), "| fired after is a number:", isinstance(d.get("timer_fired_after_s"), float),
      "| connected to a Python function:", len(t.target) == 1 and callable(t.target[0]), t.signal, "| rejected", DT["boxes"][0].rejected)
c, d = dt("how=python&seconds=20&go=yes", mode="no")
print("2859 python, No clicked      :", c, _dt_keys(d, "exec_result", "result_is_yes", "clicked_button", "closed_without_click", "timer_fired",
      "timer_fired_after_s", "timer_active_after"), "| stopped", DT["timers"][0].stops)
c, d = dt("how=slot&seconds=10&go=yes", connect="false")
print("2860 connect returns False   :", c, _dt_keys(d, "connected", "dialog_started", "error", "calls_so_far"), "| exec_", DT["boxes"][0].execs)
c, d = dt("how=python&seconds=10&go=yes", connect="raise")
print("2861 connect raises          :", c, _dt_keys(d, "dialog_started", "error", "calls_so_far"), "| exec_", DT["boxes"][0].execs)
c, d = dt("how=slot&seconds=10&go=yes", exec_="raise")
print("2862 the dialog raises       :", c, _dt_keys(d, "dialog_started", "error", "calls_so_far", "font_touched"), "| stopped", DT["timers"][0].stops)
_dt_calls = ns["_TRYDIALOGTIMEOUT"]["calls"]
ns["_TRYDIALOGTIMEOUT"]["calls"] = 10
c, d = dt("how=slot&seconds=10&go=yes")
print("2863 the cap                 : calls counted before the dialog, also for a failed one:", _dt_calls, "| at 10:", c,
      _dt_keys(d, "refused", "error", "dialog_started", "calls_so_far"), "| dialogs made", len(DT["boxes"]))
_dt_src = src[src.index("# /debug/trydialogtimeout (v0.201)"):src.index("def _read_elements(")]
_dt_body = "\n".join(l.split("#")[0] for l in _re83.sub(r'(?s)"""(.*?)"""', '', _dt_src).splitlines()).replace("out.update(", "")
print("2864 no font call            : _open_font calls", DT["open_font_calls"], "| font names in the code:",
      _re83.findall(r"\bfl\.\w+|\bfontlab\b|CurrentFont|CountFonts|_open_font|_REQUEST_FONT|\.save\w*\(|\.update\(", _dt_body),
      "| route dispatched once:", src.count('if path == "/debug/trydialogtimeout":') == 1,
      "| in the module docstring:", "/debug/trydialogtimeout" in src[:src.index('"""', 3)], "| default No:", "box.setDefaultButton(QMessageBox.No)" in _dt_src)
# v0.202: the countdown on the No button (visual only), and the clicked button's label read as a property
print("\n==== v0.202 /debug/trydialogtimeout countdown ====")
ns["_TRYDIALOGTIMEOUT"]["calls"] = 0
c, d = dt("how=slot&seconds=10&countdown=yes")
print("2865 countdown without go    :", c, "| plan:", d.get("plan"), "| countdown", d["countdown"], "| dialogs made", len(DT["boxes"]))
c, d = dt("how=slot&seconds=10&countdown=maybe&go=yes")
print("2866 countdown=maybe         :", c, d.get("error"), "| dialogs made", len(DT["boxes"]), "| calls", ns["_TRYDIALOGTIMEOUT"]["calls"])
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes")
b = DT["boxes"][0]; close = [t for t in DT["timers"] if t.single is True]; tick = [t for t in DT["timers"] if t.single is False]
print("2867 slot, countdown, no click:", c, _dt_keys(d, "countdown", "countdown_ticks", "countdown_last_label", "countdown_label_after", "countdown_error",
      "closed_without_click", "result_is_yes", "exec_result", "calls_so_far"))
print("2868 the countdown timer     : No labels set", b.btns[DTBox.No].sets, "| Yes untouched:", b.btns[DTBox.Yes].sets == [],
      "| timers: closing", len(close), "countdown", len(tick), "| owned by the dialog:", tick[0].parent is b, "| interval", tick[0].interval,
      "| connected to a Python function:", len(tick[0].target) == 1 and callable(tick[0].target[0]), "| started", tick[0].starts, "| stopped", tick[0].stops,
      "| the closing still a Qt connection:", close[0].target[0] is b, close[0].target[1])
c, d = dt("how=slot&seconds=20&countdown=yes&go=yes", mode="no", ticks_before_click=5)
print("2869 countdown, No clicked   :", c, _dt_keys(d, "result_is_yes", "exec_result", "clicked_button", "closed_without_click", "countdown_ticks",
      "countdown_last_label", "countdown_label_after", "countdown_error"), "| countdown stopped", [t.stops for t in DT["timers"] if t.single is False])
c, d = dt("how=slot&seconds=20&countdown=yes&go=yes", mode="yes", ticks_before_click=3)
print("2870 countdown, Yes clicked  :", c, _dt_keys(d, "result_is_yes", "exec_result", "clicked_button", "countdown_ticks", "countdown_last_label",
      "countdown_error"))
c, d = dt("how=python&seconds=10&countdown=yes&go=yes")
print("2871 python, countdown       :", c, _dt_keys(d, "timer_fired", "countdown_ticks", "countdown_last_label", "closed_without_click", "countdown_error"))
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", button="none")
print("2872 no No button            :", c, _dt_keys(d, "dialog_started", "closed_without_click", "countdown_ticks", "countdown_last_label", "countdown_error",
      "countdown_label_after_error"), "| countdown timers made", len([t for t in DT["timers"] if t.single is False]))
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", button="raise_set_late")
print("2873 relabel fails at tick 2 :", c, _dt_keys(d, "closed_without_click", "countdown_ticks", "countdown_last_label", "countdown_error"),
      "| labels tried", DT["boxes"][0].btns[DTBox.No].sets)
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", button="raise_set")
print("2874 first relabel fails     :", c, _dt_keys(d, "dialog_started", "closed_without_click", "countdown_ticks", "countdown_last_label", "countdown_error"),
      "| countdown timers made", len([t for t in DT["timers"] if t.single is False]))
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", connect_tick="false")
print("2875 countdown connect False :", c, _dt_keys(d, "dialog_started", "closed_without_click", "countdown_ticks", "countdown_last_label", "countdown_error"),
      "| countdown timer started", [t.starts for t in DT["timers"] if t.single is False])
c, d = dt("how=slot&seconds=20&go=yes", mode="yes", button="method")
print("2876 label as a method       :", c, _dt_keys(d, "clicked_button", "result_is_yes", "countdown"), "| countdown fields:",
      sorted(k for k in d if k.startswith("countdown_")), "| timers", len(DT["timers"]))
c, d = dt("how=slot&seconds=10&countdown=no&go=yes")
print("2877 countdown=no            :", c, _dt_keys(d, "countdown", "closed_without_click"), "| countdown fields:", sorted(k for k in d if k.startswith("countdown_")),
      "| timers", len(DT["timers"]), "| labels set", DT["boxes"][0].btns[DTBox.No].sets, "| calls", d["calls_so_far"])
ns["_TRYDIALOGTIMEOUT"]["calls"] = 0
DT["tick_at_close"] = True                    # the last tick comes just before the closing timer, both at 10 s
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes")
DT["tick_at_close"] = False
print("2880 a tick at the closing   :", c, _dt_keys(d, "countdown_ticks", "countdown_last_label", "countdown_label_after", "closed_without_click"),
      "| labels set", DT["boxes"][0].btns[DTBox.No].sets[-2:])
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", button="raise_set_from3")
print("2881 relabels fail from tick 2:", c, _dt_keys(d, "countdown_ticks", "countdown_last_label", "countdown_error", "closed_without_click"))
c, d = dt("how=slot&seconds=10&countdown=yes&go=yes", exec_="raise")
print("2878 dialog raises, countdown:", c, _dt_keys(d, "dialog_started", "error"), "| both timers stopped", [t.stops for t in DT["timers"]])
_dt_src2 = src[src.index("# /debug/trydialogtimeout (v0.201)"):src.index("def _read_elements(")]
_dt_body2 = "\n".join(l.split("#")[0] for l in _re83.sub(r'(?s)"""(.*?)"""', '', _dt_src2).splitlines()).replace("out.update(", "")
print("2879 static scan             : font names in the code:",
      _re83.findall(r"\bfl\.\w+|\bfontlab\b|CurrentFont|CountFonts|_open_font|_REQUEST_FONT|\.save\w*\(|\.update\(", _dt_body2),
      "| _open_font calls", DT["open_font_calls"], "| .text() calls:", len(_re83.findall(r"\.text\(\)", _dt_body2)),
      "| countdown in the docstring:", "&countdown=yes" in src[:src.index('"""', 3)], "| version", ns["VERSION"])
ns["_TRYDIALOGTIMEOUT"]["calls"] = 0
ns["QMessageBox"], ns["_open_font"] = _dt_saved[0], _dt_saved[2]
if _dt_saved[1] is None:
    if hasattr(ns["QtCore"], "QTimer"): delattr(ns["QtCore"], "QTimer")
else: ns["QtCore"].QTimer = _dt_saved[1]

# ================= v0.203: self-closing Yes/No dialogs in delete_glyph and remove_kerning_group =================
print("\n==== v0.203 self-closing Yes/No dialogs ====")
_sc_saved = {k: ns[k] for k in ("QMessageBox", "_open_font", "_guard_decide", "_mark_font_changed_after_delete", "_confirm_group_removal",
                                "_mark_through_first", "_now_hms", "_clock")}
_sc_timer = getattr(ns["QtCore"], "QTimer", None)
ns["QMessageBox"] = DTBox; ns["QtCore"].QTimer = DTTimer
DTBox.Warning = "Warning"                     # the product dialogs' icon
DT["clicked_raises"] = False
_dtbox_clicked = DTBox.clickedButton
def _sc_clicked(s):
    if DT["clicked_raises"]: raise RuntimeError("clickedButton boom")
    return _dtbox_clicked(s)
DTBox.clickedButton = _sc_clicked
def ask(mode="timeout", seconds=12, button="ok", connect="ok", connect_tick="ok", exec_="ok", ticks_before_click=0, clicked_raises=False):
    DT.update(mode=mode, connect=connect, exec=exec_, button=button, connect_tick=connect_tick, ticks_before_click=ticks_before_click,
              clicked_raises=clicked_raises)
    DT["boxes"].clear(); DT["timers"].clear()
    r = ns["_ask_yes_no"]("T", "Question?", seconds, "deleted")
    return {k: v for k, v in r.items() if k != "elapsed_s"}, ("elapsed_s" in r)
print("2882 dialog_seconds          :", [ns["_dialog_seconds"](v) for v in (None, 30, 5, 99, True, "45", 45.0)])
r, el = ask()
b = DT["boxes"][0]; close = [t for t in DT["timers"] if t.single is True][0]; tick = [t for t in DT["timers"] if t.single is False][0]
print("2883 no answer               :", r, "| elapsed measured:", el, "| text ends:", b.text.split("\n\n")[-1], "| default", b.default)
# v0.211: each product dialog's last line, with the outcome its call passes (the countdown on No shows the time, RX 1728-1752)
_sc_calls = _re83.findall(r'_ask_yes_no\("(Glyphbridge: Confirm [^"]+)",[^\n]*?, seconds, "(\w+)"\)', src)
for _sc_title, _sc_outcome in _sc_calls:
    DT.update(mode="timeout", connect="ok", exec="ok", button="ok", connect_tick="ok", ticks_before_click=0, clicked_raises=False)
    DT["boxes"].clear(); DT["timers"].clear()
    ns["_ask_yes_no"](_sc_title, "Question?", 45, _sc_outcome)
    print("2883a last line              :", _sc_title, "->", DT["boxes"][0].text.split("\n\n")[-1], "| no seconds in the text:",
          "45" not in DT["boxes"][0].text, "| No button:", DT["boxes"][0].btns[DTBox.No].sets[:1])
print("2883b product dialogs found  :", len(_sc_calls))
print("2884 its timers              : closing owned by the dialog:", close.parent is b, "| single", close.single, "| interval", close.interval,
      "| to the dialog's", close.target[1], "| countdown interval", tick.interval, "| labels", b.btns[DTBox.No].sets[:3], "...", b.btns[DTBox.No].sets[-1],
      "| both stopped:", close.stops, tick.stops)
print("2884b both timers started    :", close.starts, tick.starts)
DT["tick_at_close"] = True
r, _ = ask(seconds=3)
print("2884c a tick lands at the close: labels", DT["boxes"][0].btns[DTBox.No].sets, "| no 'No (0)':", "No (0)" not in DT["boxes"][0].btns[DTBox.No].sets, "|", r)
DT["tick_at_close"] = False
print("2885 Yes in time             :", ask("yes", ticks_before_click=2)[0])
print("2886 No in time              :", ask("no", ticks_before_click=4)[0])
r, _ = ask(connect="false")
print("2887 closing timer not connected:", r, "| exec_ calls:", DT["boxes"][0].execs)
r, _ = ask(connect="raise")
print("2888 connect raises          :", r, "| exec_ calls:", DT["boxes"][0].execs)
print("2889 the dialog raises       :", ask(exec_="raise")[0])
print("2890 no No button (countdown off), Yes:", ask("yes", button="none")[0])
print("2891 countdown connect False, no answer:", ask(connect_tick="false")[0])
print("2892 click unreadable        :", ask("no", clicked_raises=True)[0])
# delete_glyph and its route
class SCFont:
    def __init__(s, names): s.gl = [types.SimpleNamespace(name=n) for n in names]; s.removed = []
    glyphs = property(lambda s: list(s.gl))
    def removeGlyph(s, n): s.removed.append(n); s.gl = [g for g in s.gl if g.name != n]
    def update(s): pass
SC = {"font": None}
ns.update(_open_font=lambda: SC["font"], _guard_decide=lambda f: (True, {}),
          _mark_font_changed_after_delete=lambda f, after: {"called": True, "via_glyph": after[0] if after else None})
def scdel(payload, mode="timeout", names=(".notdef", "a", "b"), **kw):
    SC["font"] = SCFont(names)
    DT.update(mode=mode, connect="ok", exec="ok", button="ok", connect_tick="ok", ticks_before_click=1, clicked_raises=False); DT.update(kw)
    DT["boxes"].clear(); DT["timers"].clear()
    h, _, body = ns["_route"]("POST", "/glyph/delete", json.dumps(payload).encode()).partition(b"\r\n\r\n")
    d = json.loads(body)
    if isinstance(d.get("dialog"), dict): d["dialog"].pop("elapsed_s", None)
    return h.split(b"\r\n")[0].decode()[9:12], d, SC["font"].removed
_SCK = ("deleted", "user_declined", "not_answered", "dialog_error", "reason", "dialog", "notdef_deleted", "before_count", "after_count", "error")
def scshow(tag, res): c, d, removed = res; print(tag, ":", c, {k: d[k] for k in _SCK if k in d}, "| removed", removed)
scshow("2893 delete, no answer      ", scdel({"name": "a", "dialog_seconds": 12}))
scshow("2894 delete, Yes            ", scdel({"name": "a", "dialog_seconds": 12}, mode="yes"))
scshow("2895 delete, No             ", scdel({"name": "a"}, mode="no"))
scshow("2896 dialog_seconds 99 -> 50", scdel({"name": "a", "dialog_seconds": 99}, mode="no"))
scshow("2897 dialog_seconds '45'    ", scdel({"name": "a", "dialog_seconds": "45"}))
scshow("2898 no dialog could be shown", scdel({"name": "a"}, connect="false"))
scshow("2898b click unreadable: declined, not 'no answer'", scdel({"name": "a"}, mode="no", clicked_raises=True))
scshow("2899 delete .notdef, Yes    ", scdel({"name": ".notdef"}, mode="yes"))
c, d, _ = scdel({"name": ".notdef"}, mode="no")
print("2900 the .notdef dialog text :", DT["boxes"][0].text.split("\n\n")[1][:60], "| default", DT["boxes"][0].default, "| title", DT["boxes"][0].title)
# remove_kerning_group through its route (the GP fixture of the v0.200 section)
_sc_gp_saved = [(_m, _a, getattr(_m, _a, None)) for _m in _tf_mods for _a in ("flWorkspace", "CountFonts", "CurrentFont", "flItems")]
for tag, answer in (("2901 removal, no answer     ", "not_answered"), ("2902 removal, No           ", False),
                    ("2903 removal, no dialog     ", "not_shown"), ("2904 removal, Yes          ", True)):
    gp_setup(answer=answer)
    d = gpp(tag, _RM, {"group": "geR", "pairs": "keep", "dialog_seconds": 20},
            keys=("error", "removed", "changed", "user_declined", "not_answered", "dialog_error", "reason", "dialog"))
print("2905 the seconds reach the dialog:", GP["dialog_seconds"], "| dialog_seconds 'x' ->",
      gpp("     ", _RM, {"group": "geR", "pairs": "keep", "dialog_seconds": "x"}, keys=("error",)).get("error"))
for _m, _a, _v in _sc_gp_saved:
    if _v is None:
        if hasattr(_m, _a): delattr(_m, _a)
    else: setattr(_m, _a, _v)
# the OUTPUT lines
ns["_now_hms"] = lambda: "12:00:00"; ns["_clock"] = lambda: 1000.0
al_reset(); al_case("2906 OUTPUT lines: not answered / no dialog (delete, group removal):")
al("POST", "/glyph/delete", {"name": "a"}, 200, {"open": True, "deleted": False, "not_answered": True, "dialog": {"answer": "not_answered", "seconds": 45},
                                                  "reason": "nobody answered", "before_count": 3, "after_count": 3})
al("POST", "/glyph/delete", {"name": "a"}, 200, {"open": True, "deleted": False, "dialog_error": "boom", "reason": "no dialog could be shown, so nothing was deleted",
                                                  "before_count": 3, "after_count": 3})
al("POST", "/kerning/group/remove", {"group": "geR", "pairs": "keep"}, 200, {"open": True, "group": "geR", "pairs": "keep", "removed": False,
                                                                             "not_answered": True, "dialog": {"answer": "not_answered", "seconds": 45}})
al("POST", "/kerning/group/remove", {"group": "geR", "pairs": "keep"}, 200, {"open": True, "group": "geR", "pairs": "keep", "removed": False,
                                                                             "error": "set-up boom; nothing was removed"})
ns["_activity_tick"]()
_sc_src = src[src.index("def _ask_yes_no("):src.index("def _confirm_deletion(")]
print("2907 static scan             : font names in the dialog:", _re83.findall(r"\bfl\.\w+|\bfontlab\b|CurrentFont|_open_font", _sc_src),
      "| exec_ calls:", _sc_src.count(".exec_()"), "| the closing timer is a Qt connection:", 'closer.connect("timeout()", box, "reject()")' in _sc_src,
      "| no other QMessageBox in the listener:", src.count("QMessageBox(") - src.count("QMessageBox(QMessageBox.Question, _TRYDIALOGTIMEOUT_TITLE") == 1,
      "| version", ns["VERSION"])
DTBox.clickedButton = _dtbox_clicked
ns.update(_sc_saved)
if _sc_timer is None:
    if hasattr(ns["QtCore"], "QTimer"): delattr(ns["QtCore"], "QTimer")
else: ns["QtCore"].QTimer = _sc_timer

# ================= v0.218: /debug/tryexpand (gated research probe: ONE shape.applyTransform per call) =================
print("\n==== v0.218 /debug/tryexpand ====")
# The v0.213 SH fakes (spies) plus inkBox() and applyTransform(). By default applyTransform() with no argument expands (nodes mapped by
# the shape's matrix, matrix to identity, as the GUI did live 1956); with a transform it maps the nodes by it and keeps the matrix.
XT = {"mode": {}}
XT_FORBIDDEN = []
class XTRect:
    def __init__(s, l, b, r, t): s._v = dict(left=l, right=r, top=b, bottom=t, width=r - l, height=t - b)
    def left(s): return s._v["left"]
    def right(s): return s._v["right"]
    def top(s): return s._v["top"]
    def bottom(s): return s._v["bottom"]
    def width(s): return s._v["width"]
    def height(s): return s._v["height"]
def _xt_pt(m, x, y): return (m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5])
def _xt_twice(m): return (m[0] * m[0] + m[1] * m[2], m[0] * m[1] + m[1] * m[3], m[2] * m[0] + m[3] * m[2], m[2] * m[1] + m[3] * m[3],
                          m[4] * m[0] + m[5] * m[2] + m[4], m[4] * m[1] + m[5] * m[3] + m[5])
class XTShape(SHShape):
    def inkBox(s):
        if XT["mode"].get("box_raises"): raise RuntimeError("inkBox boom")
        pts = [_xt_pt(s._tx._m, r["x"], r["y"]) for c in s._contours for r in c.rows]
        if not pts: return XTRect(0.0, 0.0, 0.0, 0.0)
        k = 1.0 if s.__dict__.get("_box_off") else 0.0     # box_moves: FontLab's box off by 1 after the call, the nodes right
        return XTRect(min(p[0] for p in pts) + k, min(p[1] for p in pts), max(p[0] for p in pts) + k, max(p[1] for p in pts))
    def applyTransform(s, *a):
        mode = XT["mode"]
        TE["calls"].append(("applyTransform", len(a)))
        if mode.get("raises"): raise RuntimeError("applyTransform boom")
        if mode.get("ignored"): return None
        m = a[0]._m if a else s._tx._m
        if mode.get("compose"):
            s._tx = SHQT(_xt_twice(m)); return None
        rnd = (lambda v: float(round(v))) if mode.get("rounds") else (lambda v: v)
        s._contours = [te_contour([tuple(rnd(v) for v in _xt_pt(m, r["x"], r["y"])) for r in c.rows]) for c in s._contours]
        if not a and not mode.get("keeps_matrix"): s._tx = SHQT()
        if mode.get("touch_other"): XT["other"]._contours[0].rows[0]["x"] += 1.0
        if mode.get("touch_source"): XT["src"]._contours[0].rows[0]["x"] += 1.0
        if mode.get("change_next") and "xt1g" in P72["layers"]: P72["layers"]["xt1g"]._shapes[0]._tx = SHQT((1.4, 0, 0, 1, 0, 0))     # v0.221 tests
        if mode.get("box_moves"): s.__dict__["_box_off"] = True
        return True if mode.get("returns") else None
class XTLayer(TELayer):
    def autoLayer(s): return XT["mode"].get("auto", False)
    def recipe(s): return ""
XT_S = (1.5, 0, 0, 1, 0, 0)     # live 1955: 150% horizontally, from x = 0
XT_ODD = (0.5, 0.2, -0.3, 2, 10.25, -20)     # dx 10.25: the expanded nodes hold fractions
XT_LEGACY = {"xt1c": (3, 11)}     # the legacy view's (contours, nodes), so the stub sync can confirm a glyph of several shapes
def xt_setup(mode=None, count=1):
    te_setup(count=count)
    XT["mode"] = dict(mode or {})
    src = SHShape([te_contour([(0, 0), (50, 0), (50, 50), (0, 50)])]); XT["src"] = src
    TS["xt9src"] = TsGlyph("xt9src", [TsLayer(1, 4)]); P72["layers"]["xt9src"] = TELayer("test_font", [src])
    other = XTShape([te_contour(TE_TRI)]); XT["other"] = other
    for g, shapes in (("xt1a", [XTShape([te_contour([(100, 0), (300, 0), (300, 200), (100, 200)])], m=XT_S)]),
                      ("xt1b", [XTShape([te_contour(TE_SQ)])]),
                      ("xt1c", [XTShape(component="xt9src", shared=src._contours, m=(1, 0, 0, 1, 200, 0)), XTShape([te_contour(TE_SQ)], m=XT_ODD), other]),
                      ("xt1d", [XTShape([te_contour(TE_SQ)], m=XT_S), XTShape([te_contour(TE_TRI)], composite=True)]),
                      ("xt1e", [XTShape(component="xt9src", shared=src._contours, m=XT_S)]),
                      ("xt1f", []),
                      ("xt1g", [XTShape([te_contour(TE_SQ), te_contour(TE_TRI)], m=XT_S)])):
        TS[g] = TsGlyph(g, [TsLayer(*XT_LEGACY.get(g, (1, 4)))]); P72["layers"][g] = XTLayer("test_font", shapes); P72["widths"][g] = 500.0
    ns["_TRYEXPAND"]["calls"] = 0
XK = ("outcome", "expanded", "changed", "drawn_outline_kept", "ink_boxes_kept", "margins_kept", "other_shapes_unchanged", "contour_counts_kept",
      "other_contours_unchanged", "sources_unchanged", "advance_width_kept", "side_effect_detected", "call_returned", "outcome_after_sync", "error", "calls_so_far")
QX = "/debug/tryexpand?"
def xt(tag, q, keys=("error", "calls_so_far")):
    c, d = call(QX + q)
    XT_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| applyTransform", [x for x in TE["calls"] if isinstance(x, tuple) and x[0] == "applyTransform"],
          "| Update", TE["updates"], "| marks", TE["marks"])
    return d
def _xt_raw(r):
    v = (r or {}).get("shape_raw")
    return v if not isinstance(v, list) else [[(n["x"], n["y"]) for n in c["nodes"]] for c in v]
def _xt_m(r):
    v = (r or {}).get("shape_matrix") or {}
    return v if "error" in v else tuple(v.get(k) for k in ("m11", "m12", "m21", "m22", "dx", "dy"))
def xt_show(tag, d):
    print(tag, " raw before / after / after sync:", _xt_raw(d.get("before")), "/", _xt_raw(d.get("after")), "/", _xt_raw(d.get("after_sync")))
    print(tag, " matrix before / after:", _xt_m(d.get("before")), "/", _xt_m(d.get("after")), "| deviations", d.get("deviations"),
          "| ink boxes after:", [(b.get("left"), b.get("right")) for b in (d.get("after") or {}).get("ink_boxes") or [] if isinstance(b, dict)])
xt_setup()
xt("3000a without go                    ", "name=xt1a&shape=0&how=noarg")
xt("3000b go must be exactly yes        ", "name=xt1a&shape=0&how=noarg&go=Yes")
xt("3000c name without the prefix       ", "name=edpa&shape=0&how=noarg&go=yes")
xt("3000d xt without a digit            ", "name=xtA1&shape=0&how=noarg&go=yes")
xt("3000e shape missing                 ", "name=xt1a&how=noarg&go=yes")
xt("3000f shape 20                      ", "name=xt1a&shape=20&how=noarg&go=yes")
xt("3000g how missing                   ", "name=xt1a&shape=0&go=yes")
xt("3000h how=apply                     ", "name=xt1a&shape=0&how=apply&go=yes")
print("3000i refusals counted no call      :", ns["_TRYEXPAND"]["calls"])
for tag, over in (("3001a two fonts open                ", dict(count=2)), ("3001b no font open                  ", dict(count=0))):
    xt_setup(**over); xt(tag, "name=xt1a&shape=0&how=noarg&go=yes")
xt_setup()
d = xt("3002 noarg expands (as the GUI, 1956)", "name=xt1a&shape=0&how=noarg&go=yes", keys=XK); xt_show("3002a", d)
print("3002b  call, returned, sync     :", d.get("call"), d.get("call_returned"), "| synced_before_read", d.get("synced_before_read"),
      "| mark", d.get("fontlab_changed_mark"), "| after sync", d.get("after_sync_verdicts", {}).get("drawn_outline_kept"))
xt_setup()
d = xt("3003 own: nodes mapped, matrix kept ", "name=xt1a&shape=0&how=own&go=yes", keys=XK); xt_show("3003a", d)
for tag, q, mode in (("3004 the matrix doubles            ", "name=xt1a&shape=0&how=noarg&go=yes", {"compose": 1}),
                     ("3005 nothing happens               ", "name=xt1a&shape=0&how=noarg&go=yes", {"ignored": 1}),
                     ("3006 applyTransform raises         ", "name=xt1a&shape=0&how=noarg&go=yes", {"raises": 1}),
                     ("3007 nodes mapped, matrix kept (noarg)", "name=xt1a&shape=0&how=noarg&go=yes", {"keeps_matrix": 1}),
                     ("3008 it returns True               ", "name=xt1a&shape=0&how=noarg&go=yes", {"returns": 1}),
                     ("3009 ink boxes unreadable          ", "name=xt1a&shape=0&how=noarg&go=yes", {"box_raises": 1}),
                     ("3009b only FontLab's ink box moves  ", "name=xt1a&shape=0&how=noarg&go=yes", {"box_moves": 1})):
    xt_setup(mode=mode); d = xt(tag, q, keys=XK)
    if tag.startswith("3004"): xt_show("3004a", d)
xt_setup()
d = xt("3010 a skewed shape beside a component and a plain shape", "name=xt1c&shape=1&how=noarg&go=yes", keys=XK); xt_show("3010a", d)
print("3010b  mark, sync               :", d.get("fontlab_changed_mark"), (d.get("fontlab_sync") or {}).get("verdict"))
xt_setup(mode={"rounds": 1})
d = xt("3011 FontLab rounds the new nodes   ", "name=xt1c&shape=1&how=noarg&go=yes", keys=XK); xt_show("3011a", d)
xt_setup(mode={"touch_other": 1})
xt("3012 the other plain shape moves    ", "name=xt1c&shape=1&how=noarg&go=yes", keys=XK)
xt_setup(mode={"touch_source": 1})
xt("3013 the component's source moves   ", "name=xt1c&shape=1&how=noarg&go=yes", keys=XK)
for tag, q in (("3014a no transform (identity)       ", "name=xt1b&shape=0"), ("3014b a Power Brush shape beside    ", "name=xt1d&shape=0"),
               ("3014c the shape is a component      ", "name=xt1e&shape=0"), ("3014d a component in the glyph, shape 0", "name=xt1c&shape=0"),
               ("3014e no shape at all               ", "name=xt1f&shape=0"), ("3014f shape 3 of three              ", "name=xt1c&shape=3"),
               ("3014g no such glyph                 ", "name=xt1z&shape=0")):
    xt_setup(); xt(tag, q + "&how=noarg&go=yes")
xt_setup(mode={"auto": True}); xt("3014h autoLayer on                  ", "name=xt1a&shape=0&how=noarg&go=yes")
for tag, q, mode in (("3014i isComposite raises            ", "name=xt1c&shape=1", {"composite_raises": 1}),
                     ("3014j contoursCount disagrees        ", "name=xt1c&shape=1", {"sh_count_wrong": 1}),
                     ("3014k shape.getContours disagrees     ", "name=xt1g&shape=0", {"sh_gc_disagree": 1}),
                     ("3014l layer.shapes is a tuple        ", "name=xt1c&shape=1", {"shapes_tuple": 1})):
    xt_setup(mode=mode); TE["mode"].update(mode); xt(tag, q + "&how=noarg&go=yes")
print("3014m no applyTransform in any refusal:", [x for x in TE["calls"] if isinstance(x, tuple) and x[0] == "applyTransform"], "| marks", TE["marks"])
xt_setup()
d = xt("3014n two contours in the shape     ", "name=xt1g&shape=0&how=noarg&go=yes", keys=XK); xt_show("3014o", d)
xt_setup()
for _i in range(6): call(QX + "name=xt1a&shape=0&how=own&go=yes")
xt("3015 the limit: call 7 is refused   ", "name=xt1a&shape=0&how=noarg&go=yes")
print("3016 spies over all cases: forbidden members, subscripts, iterations:", XT_FORBIDDEN)
_src218 = "\n".join(l for l in src[src.index("# /debug/tryexpand (v0.218)"):src.index("def debug_try_expand(")].split("\n") if not l.lstrip().startswith("#"))
_src218 += "\n".join(l for l in src[src.index("def debug_try_expand("):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("3016a applyTransform statements:", [l.strip() for l in _src218.split("\n") if "applyTransform(" in l and not l.strip().startswith(("return", "\"", "'", "_TRY", "step"))],
      "| forbidden call syntax:", _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|decomposite|ejectTo|eject|prepareTransformationData|resetTransformationData|restoreHistoryState|clearAboveHistory|historyStates)\s*\(|font\.update|\.transform\s*=[^=]", _src218),
      "| counter before the read:", _src218.index('_TRYEXPAND["calls"] += 1') < _src218.index("_modern_edit_target(name)"),
      "| route documented:", "/debug/tryexpand      name=xt...&shape=I&how=noarg|own" in src, "| dispatched:", 'if path == "/debug/tryexpand":' in src,
      "| mark title:", ns["_MARK_TITLES"].get("tryexpand"), "| version", ns["VERSION"])
for _g in ("xt1a", "xt1b", "xt1c", "xt1d", "xt1e", "xt1f", "xt1g", "xt9src"): TS.pop(_g, None); P72["layers"].pop(_g, None); P72["widths"].pop(_g, None)

# ================= v0.219: /debug/tryhistory, /debug/tryexpand &history=yes / &bracket=yes (Undo research) =================
print("\n==== v0.219 /debug/tryhistory and the tryexpand bracket ====")
# History members on the v0.218 fakes: the glyph answers plain values and real lists, the layer a native-like object (described by
# type only: a spy, so iterating or indexing it would land in TE["forbidden"]), the shape a plain attribute and a raising member.
# flItems gets notifyEditActionStarted / Finished; each logs into TE["calls"] with how many syncs and marks came before it.
class XTNative(TESpy):
    pass
def _xh_glyph(s, key):
    m = XT["mode"]
    TE["calls"].append(("glyph." + key,))
    if m.get("hist_raises"): raise RuntimeError("history boom")
    return {"has": True, "cur": 2 + XT.get("hist_bump", 0), "ini": 0}[key]
P72Mod.hasHistoryStates = lambda s: _xh_glyph(s, "has")
P72Mod.currentHistoryState = lambda s: _xh_glyph(s, "cur")
P72Mod.initialHistoryState = lambda s: _xh_glyph(s, "ini")
P72Mod.historyStates = lambda s, accepted: (TE["calls"].append(("glyph.historyStates", accepted)),
                                            [0, 1, 2] if accepted else (0, 1, 2, "x" * 70, XTNative()))[1]
XTLayer.hasHistoryStates = lambda s: False
XTLayer.currentHistoryState = lambda s: 0
XTLayer.initialHistoryState = lambda s: 0
XTLayer.historyStates = lambda s, accepted: XTNative()
XTShape.hasHistoryStates = True                     # a plain attribute, read as it is
def _xh_shape_cur(s): raise RuntimeError("currentHistoryState boom")
XTShape.currentHistoryState = _xh_shape_cur
XTShape.initialHistoryState = lambda s: 1
XTShape.historyStates = "not callable"
def _xh_started():
    TE["calls"].append(("Started", len(TE["updates"]), len(TE["marks"])))
    if XT["mode"].get("started_raises"): raise RuntimeError("Started boom")
    return None
def _xh_finished():
    TE["calls"].append(("Finished", len(TE["updates"]), len(TE["marks"])))
    if XT["mode"].get("finished_raises"): raise RuntimeError("Finished boom")
    if XT["mode"].get("finished_bumps"): XT["hist_bump"] = 1
    return True
TEItems.notifyEditActionStarted = staticmethod(_xh_started)
TEItems.notifyEditActionFinished = staticmethod(_xh_finished)
XH_TRACE = lambda: [x for x in TE["calls"] if isinstance(x, tuple) and x[0] in ("Started", "Finished", "applyTransform")]
QH = "/debug/tryhistory?"
def xh(tag, q, keys=("error", "calls_so_far")):
    c, d = call(QH + q)
    XT_FORBIDDEN.extend(TE["forbidden"])
    print(tag, ":", c, {k: d.get(k) for k in keys if k in d}, "| edits", XH_TRACE(), "| Update", TE["updates"], "| marks", TE["marks"])
    return d
def xh_reset(mode=None):
    xt_setup(mode=mode); XT.pop("hist_bump", None); ns["_TRYHIST"]["calls"] = 0
xh_reset()
xh("3020a without go                    ", "name=xt1a&shape=0")
xh("3020b name without the prefix       ", "name=edpa&shape=0&go=yes")
xh("3020c shape missing                 ", "name=xt1a&go=yes")
print("3020d refusals counted no call      :", ns["_TRYHIST"]["calls"])
for tag, over in (("3021a two fonts open                ", dict(count=2)), ("3021b no font open                  ", dict(count=0))):
    xt_setup(**over); ns["_TRYHIST"]["calls"] = 0; xh(tag, "name=xt1a&shape=0&go=yes")
xh_reset()
d = xh("3022 read on a scaled square        ", "name=xt1a&shape=0&go=yes")
for part in ("glyph", "layer", "shape"): print("3022a ", part, ":", (d.get("history") or {}).get(part))
print("3022b  nothing changed: state before == after", d.get("state_before") == d.get("state_after"), "| elements", d.get("elements"))
xh_reset(); xh("3023a a Power Brush shape in the glyph", "name=xt1d&shape=0&go=yes")
xh_reset(); xh("3023b shape 3 of three              ", "name=xt1c&shape=3&go=yes")
xh_reset(); xh("3023c no such glyph                 ", "name=xt1z&shape=0&go=yes")
xh_reset(); d = xh("3023d an identity shape is read too  ", "name=xt1b&shape=0&go=yes"); print("3023e  glyph part:", (d.get("history") or {}).get("glyph"))
xh_reset(mode={"hist_raises": 1}); d = xh("3023f the glyph's members raise     ", "name=xt1a&shape=0&go=yes"); print("3023g  glyph part:", (d.get("history") or {}).get("glyph"))
xh_reset()
for _i in range(10): call(QH + "name=xt1a&shape=0&go=yes")
xh("3024 the limit: call 11 is refused  ", "name=xt1a&shape=0&go=yes")
# tryexpand with the new options
XKB = ("outcome", "expanded", "changed", "history", "bracket", "bracket_calls", "fontlab_changed_mark", "error", "calls_so_far")
xh_reset()
xt("3025a history=no                    ", "name=xt1a&shape=0&how=noarg&history=no&go=yes")
xt("3025b bracket=1                     ", "name=xt1a&shape=0&how=noarg&bracket=1&go=yes")
xt("3025c both shown before go          ", "name=xt1a&shape=0&how=noarg&history=yes&bracket=yes")
print("3025d refusals counted no call      :", ns["_TRYEXPAND"]["calls"])
xh_reset()
d = xt("3026 history=yes, no bracket        ", "name=xt1a&shape=0&how=noarg&history=yes&go=yes", keys=XKB)
print("3026a  glyph before / after / after sync:", [(d.get(k) or {}).get("glyph", {}).get("currentHistoryState()") for k in ("history_before", "history_after", "history_after_sync")],
      "| no bracket call:", XH_TRACE())
xh_reset(mode={"finished_bumps": 1})
d = xt("3027 bracket=yes                    ", "name=xt1a&shape=0&how=noarg&history=yes&bracket=yes&go=yes", keys=XKB)
print("3027a  order (Started/Finished with syncs and marks before them):", XH_TRACE(), "| Update", TE["updates"], "| marks", TE["marks"])
print("3027b  glyph current before / after:", [(d.get(k) or {}).get("glyph", {}).get("currentHistoryState()") for k in ("history_before", "history_after")])
xh_reset(mode={"started_raises": 1})
d = xt("3028 Started raises: nothing else   ", "name=xt1a&shape=0&how=noarg&bracket=yes&go=yes", keys=XKB); print("3028a  trace:", XH_TRACE())
xh_reset(mode={"raises": 1})
d = xt("3029 the expansion raises: Finished still called", "name=xt1a&shape=0&how=noarg&bracket=yes&go=yes", keys=XKB); print("3029a  trace:", XH_TRACE())
xh_reset(mode={"finished_raises": 1})
d = xt("3030 Finished raises                ", "name=xt1a&shape=0&how=noarg&bracket=yes&go=yes", keys=XKB); print("3030a  trace:", XH_TRACE())
xh_reset()
_fi = [(m, getattr(m, "flItems", None)) for m in _tf_mods]
for _m in _tf_mods: _m.flItems = None
xt("3031 no flItems: not counted        ", "name=xt1a&shape=0&how=noarg&bracket=yes&go=yes")
for _m, _v in _fi: _m.flItems = _v
print("3032 spies over all cases: forbidden members, subscripts, iterations:", XT_FORBIDDEN)
_src219 = "\n".join(l for l in src[src.index("# /debug/tryexpand (v0.218)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("3032a never called:", _re83.findall(r"restoreHistoryState|clearAboveHistory|checkInitHistoryState|hasHistoryState\b|requestCheckHistoryInitIndex|notifyHistoryChanged|notifyUpdateHistory", _src219),
      "| bracket call statements:", [l.strip() for l in _src219.split("\n") if "items.notifyEditAction" in l and "=" in l],
      "| Finished guarded by started:", "    if started:\n        try:\n            ret = items.notifyEditActionFinished()" in _src219,
      "| routes documented:", "/debug/tryhistory     name=xt...&shape=I" in src, "&bracket=yes wraps the call" in src,
      "| dispatched:", 'if path == "/debug/tryhistory":' in src, '(query.get("bracket") or [None])[0]' in src, "| version", ns["VERSION"])
for _a in ("hasHistoryStates", "currentHistoryState", "initialHistoryState", "historyStates"):
    for _c in (P72Mod, XTLayer, XTShape):
        if _a in _c.__dict__: delattr(_c, _a)
for _a in ("notifyEditActionStarted", "notifyEditActionFinished"):
    if _a in TEItems.__dict__: delattr(TEItems, _a)
for _g in ("xt1a", "xt1b", "xt1c", "xt1d", "xt1e", "xt1f", "xt1g", "xt9src"): TS.pop(_g, None); P72["layers"].pop(_g, None); P72["widths"].pop(_g, None)

# ================= v0.220: /debug/tryexpand &mark=recursive|shape (Undo research: where the change mark records) =================
print("\n==== v0.220 /debug/tryexpand mark variants ====")
# The v0.218 fakes again (their glyphs were removed at the end of the v0.219 section). TEItems.notifyChangesApplied logs
# (title, type of the object, recursive flag) into TE["marks"]; XT["mode"]["mark_raises"] makes it raise.
_xm_saved = TEItems.__dict__["notifyChangesApplied"]
def _xm_notify(title, obj, flag):
    TE["marks"].append((title, type(obj).__name__, flag))
    if XT["mode"].get("mark_raises"): raise RuntimeError("notifyChangesApplied boom")
TEItems.notifyChangesApplied = staticmethod(_xm_notify)
XKM = ("outcome", "expanded", "mark", "variant_mark", "fontlab_changed_mark", "synced_with_fontlab", "error", "calls_so_far")
xt_setup()
xt("3040a mark=glyph                    ", "name=xt1a&shape=0&how=noarg&mark=glyph&go=yes")
xt("3040b mark=shape shown before go    ", "name=xt1a&shape=0&how=noarg&mark=shape")
xt("3040c mark=recursive shown before go", "name=xt1a&shape=0&how=noarg&mark=recursive")
print("3040d refusals counted no call      :", ns["_TRYEXPAND"]["calls"])
xt_setup()
d = xt("3041 mark=recursive                 ", "name=xt1a&shape=0&how=noarg&mark=recursive&go=yes", keys=XKM)
xt_setup()
d = xt("3042 mark=shape                     ", "name=xt1c&shape=1&how=noarg&mark=shape&go=yes", keys=XKM)
xt_setup()
d = xt("3043 standard mark (no option)      ", "name=xt1a&shape=0&how=noarg&go=yes", keys=XKM)
xt_setup(mode={"keeps_matrix": 1})
xt("3044 expansion not confirmed: no mark", "name=xt1a&shape=0&how=noarg&mark=shape&go=yes", keys=XKM)
xt_setup()
xt("3045 sync not confirmed: no mark    ", "name=xt1g&shape=0&how=noarg&mark=recursive&go=yes", keys=XKM)
xt_setup(mode={"mark_raises": 1})
xt("3046 the variant mark raises        ", "name=xt1a&shape=0&how=noarg&mark=shape&go=yes", keys=XKM)
xt_setup(mode={"ignored": 1})
xt("3047 nothing changed: no mark       ", "name=xt1a&shape=0&how=noarg&mark=recursive&go=yes", keys=XKM)
print("3048 spies over all cases: forbidden members, subscripts, iterations:", XT_FORBIDDEN)
_src220 = "\n".join(l for l in src[src.index("# /debug/tryexpand (v0.218)"):src.index("# /debug/tryopen (v0.125)")].split("\n") if not l.lstrip().startswith("#"))
print("3048a notifyChangesApplied call statements:", [l.strip() for l in _src220.split("\n") if "notifyChangesApplied(" in l and "=" in l and '"' not in l.split("notifyChangesApplied(")[0]],
      "| never called:", _re83.findall(r"restoreHistoryState|clearAboveHistory|checkInitHistoryState|requestCheckHistoryInitIndex|notifyHistoryChanged|notifyUpdateHistory", _src220),
      "| route documented:", "&mark=recursive|shape replaces the standard mark" in src, "| dispatched:", '(query.get("mark") or [None])[0]))' in src,
      "| version", ns["VERSION"])
TEItems.notifyChangesApplied = _xm_saved
for _g in ("xt1a", "xt1b", "xt1c", "xt1d", "xt1e", "xt1f", "xt1g", "xt9src"): TS.pop(_g, None); P72["layers"].pop(_g, None); P72["widths"].pop(_g, None)

# ================= v0.221: POST /glyph/expand (expand_transformation, the user's design of 2026-11-26/27) =================
print("\n==== v0.221 POST /glyph/expand ====")
# The v0.218 fakes (XTShape, XTLayer, xt_setup). By default XTShape.applyTransform() keeps fractions; mode "rounds" rounds as FontLab
# did live (1975, 1981; the stub uses Python's round, so a half may go down, as FontLab might). xt1h: a square whose expansion by
# 150 % lands on half units (103 -> 154.5, 301 -> 451.5).
XT_LEGACY["xt1h"] = (1, 4)
def xe_setup(mode=None):
    xt_setup(mode=mode)
    TS["xt1h"] = TsGlyph("xt1h", [TsLayer(1, 4)])
    P72["layers"]["xt1h"] = XTLayer("test_font", [XTShape([te_contour([(103, 0), (301, 0), (301, 200), (103, 200)])], m=XT_S)])
    P72["widths"]["xt1h"] = 500.0
    TS["xt1i"] = TsGlyph("xt1i", [TsLayer(2, 8)])
    P72["layers"]["xt1i"] = XTLayer("test_font", [XTShape([te_contour(TE_SQ)], m=XT_S), XTShape(component="xt9src", shared=XT["src"]._contours, m=XT_S)])
def xm(m): return {k: float(v) for k, v in zip(("m11", "m12", "m21", "m22", "dx", "dy"), m)}
def xpost(payload):
    return sbpost("/glyph/expand", payload)
def xraw(body):
    r = ns["_route"]("POST", "/glyph/expand", body); h, _, b = r.partition(b"\r\n\r\n")
    return h.split(b"\r\n")[0].decode()[9:12], json.loads(b)
XEK = ("expanded", "verified", "changed", "reason", "error", "stopped_at", "refused", "preview", "verified_after_sync")
def xe(tag, payload, keys=XEK, mode=None, setup=True):
    if setup:
        xe_setup(mode=mode)
    c, d = xpost(payload)
    XT_FORBIDDEN.extend(TE["forbidden"])
    res = d.get("results") if isinstance(d, dict) else None
    top = {k: d.get(k) for k in keys if isinstance(d, dict) and k in d}
    per = [{k: r.get(k) for k in keys if k in r} for r in res] if isinstance(res, list) else None
    print(tag, ":", c, top, "| per glyph", per, "| applyTransform", [x for x in TE["calls"] if isinstance(x, tuple) and x[0] == "applyTransform"],
          "| Update", len(TE["updates"]), "| marks", TE["marks"])
    return d
def xe_shapes(tag, d):
    for r in (d.get("results") or []):
        for s in r.get("shapes") or []:
            print(tag, r.get("name"), "shape", s["index"], "| shift", s["largest_rounding_shift"], "| rounded", s["rounded_nodes_count"],
                  s["rounded_nodes"][:2], "| halves", s["half_cases"], "| contours", s["contours"],
                  "| expected", [[(n["x"], n["y"]) for n in c["nodes"]] for c in s["expected"]])
G = lambda name, *shapes: {"name": name, "shapes": [{"index": i, "matrix": xm(m)} for i, m in shapes]} if shapes else {"name": name}
# the request's form
for tag, body in (("3060a not JSON                     ", None), ("3060b glyphs missing                ", {"preview": True}),
                  ("3060c an unknown key                ", {"glyphs": [G("xt1a")], "preview": True, "go": 1}),
                  ("3060d preview not a bool            ", {"glyphs": [G("xt1a")], "preview": "yes"}),
                  ("3060e 11 glyphs                     ", {"glyphs": [G(f"g{i}") for i in range(11)], "preview": True}),
                  ("3060f a name twice                  ", {"glyphs": [G("xt1a"), G("xt1a")], "preview": True}),
                  ("3060g a write without shapes        ", {"glyphs": [G("xt1a")]}),
                  ("3060h a matrix without dy           ", {"glyphs": [{"name": "xt1a", "shapes": [{"index": 0, "matrix": {"m11": 1.5, "m12": 0, "m21": 0, "m22": 1, "dx": 0}}]}]}),
                  ("3060i index 20                      ", {"glyphs": [G("xt1a", (20, XT_S))]}),
                  ("3060j an index twice                ", {"glyphs": [G("xt1a", (0, XT_S), (0, XT_S))]})):
    xe_setup()
    c, d = xpost(body) if body is not None else xraw(b"{oops")
    print(tag, ":", c, d.get("error") if isinstance(d, dict) else d)
print("3060k nothing touched by the form refusals:", [x for x in TE["calls"] if isinstance(x, tuple) and x[0] == "applyTransform"], TE["marks"])
# previews
d = xe("3061 preview, the scaled square (150 %)", {"glyphs": [G("xt1a")], "preview": True}); xe_shapes("3061a", d)
d = xe("3062 preview, xt1c: shapes found by themselves", {"glyphs": [G("xt1c")], "preview": True}); xe_shapes("3062a", d)
d = xe("3062b preview, the half-unit square        ", {"glyphs": [G("xt1h")], "preview": True}); xe_shapes("3062c", d)
d = xe("3062d preview, a glyph with no transform     ", {"glyphs": [G("xt1b")], "preview": True})
# writes
d = xe("3063 write xt1a                     ", {"glyphs": [G("xt1a", (0, XT_S))]})
print("3063a  mark, sync                 :", d["results"][0].get("fontlab_changed_mark"), (d["results"][0].get("fontlab_sync") or {}).get("verdict"),
      "| outline now", [[(r["x"], r["y"]) for r in c.rows] for c in P72["layers"]["xt1a"]._shapes[0]._contours], "| matrix", P72["layers"]["xt1a"]._shapes[0]._tx._m)
xe("3064 a transform changed since the read", {"glyphs": [G("xt1a", (0, (1.4, 0, 0, 1, 0, 0)))]})
xe("3065 a component as the target      ", {"glyphs": [G("xt1e", (0, XT_S))]})
xe("3065b a scaled component beside      ", {"glyphs": [G("xt1i", (0, XT_S))]})
xe("3066 a Power Brush shape in the glyph", {"glyphs": [G("xt1d", (0, XT_S))]})
xe("3067 autoLayer on                   ", {"glyphs": [G("xt1a", (0, XT_S))]}, mode={"auto": True})
xe("3067b a shape with no transform     ", {"glyphs": [G("xt1c", (2, (1, 0, 0, 1, 0, 0)))]})
xe("3067c shape 5 does not exist        ", {"glyphs": [G("xt1c", (5, XT_ODD))]})
xe("3067d no such glyph                 ", {"glyphs": [G("xt1z", (0, XT_S))]})
d = xe("3068 xt1c shape 1, FontLab rounds  ", {"glyphs": [G("xt1c", (1, XT_ODD))]}, mode={"rounds": 1}); xe_shapes("3068a", d)
d = xe("3069 xt1c shape 1, fractions kept (not as FontLab)", {"glyphs": [G("xt1c", (1, XT_ODD))]})
print("3069a  mismatches, mark           :", (d["results"][0].get("mismatches") or [])[:2], d["results"][0].get("fontlab_changed_mark"))
d = xe("3070 the half-unit square, rounds (one half down)", {"glyphs": [G("xt1h", (0, XT_S))]}, mode={"rounds": 1}); xe_shapes("3070a", d)
d = xe("3071 two glyphs, both verified      ", {"glyphs": [G("xt1a", (0, XT_S)), G("xt1g", (0, XT_S))]})
d = xe("3072 the second glyph is refused: nothing", {"glyphs": [G("xt1a", (0, XT_S)), G("xt1e", (0, XT_S))]})
d = xe("3073 another plain shape moves       ", {"glyphs": [G("xt1c", (1, XT_ODD)), G("xt1a", (0, XT_S))]}, mode={"rounds": 1, "touch_other": 1})
d = xe("3074 the component's source moves    ", {"glyphs": [G("xt1c", (1, XT_ODD))]}, mode={"rounds": 1, "touch_source": 1})
d = xe("3075 applyTransform raises            ", {"glyphs": [G("xt1a", (0, XT_S)), G("xt1g", (0, XT_S))]}, mode={"raises": 1})
d = xe("3076 applyTransform does nothing      ", {"glyphs": [G("xt1a", (0, XT_S))]}, mode={"ignored": 1})
d = xe("3077 the matrix doubles               ", {"glyphs": [G("xt1a", (0, XT_S))]}, mode={"compose": 1})
d = xe("3077b nodes mapped, the transform kept ", {"glyphs": [G("xt1a", (0, XT_S))]}, mode={"keeps_matrix": 1})
print("3077c  mismatches                 :", (d["results"][0].get("mismatches") or [])[:2])
d = xe("3077d the next glyph changes meanwhile", {"glyphs": [G("xt1a", (0, XT_S)), G("xt1g", (0, XT_S))]}, mode={"change_next": 1})
# the activity line and the change log's verdict
_xp = {"glyphs": [G("xt1a")], "preview": True}
xe_setup(); _c, _d = xpost(_xp)
print("3078 OUTPUT line, preview      :", ns["_act_describe_write"]("/glyph/expand", _xp, 200, _d), "| change verdict:", ns["_change_verdict"]("/glyph/expand", 200, _d))
_xw = {"glyphs": [G("xt1a", (0, XT_S))]}
xe_setup(); _c, _d = xpost(_xw)
print("3078a OUTPUT line, write       :", ns["_act_describe_write"]("/glyph/expand", _xw, 200, _d), "| change verdict:", ns["_change_verdict"]("/glyph/expand", 200, _d))
_xr = {"glyphs": [G("xt1e", (0, XT_S))]}
xe_setup(); _c, _d = xpost(_xr)
print("3078b OUTPUT line, refused     :", ns["_act_describe_write"]("/glyph/expand", _xr, 200, _d)[0][:110], "| change verdict:", ns["_change_verdict"]("/glyph/expand", 200, _d))
print("3079 spies over all cases: forbidden members, subscripts, iterations:", XT_FORBIDDEN)
_src221 = "\n".join(l for l in src[src.index("# POST /glyph/expand (v0.221)"):src.index("# ---- v0.204: the change log")].split("\n") if not l.lstrip().startswith("#"))
print("3079a applyTransform statements:", [l.strip() for l in _src221.split("\n") if "applyTransform(" in l],
      "| forbidden call syntax:", _re83.findall(r"\.(?:update|save\w*|export\w*|close|release|removeGlyph|decomposite|ejectTo|eject|prepareTransformationData|resetTransformationData|restoreHistoryState|clearAboveHistory|historyStates|checkInitHistoryState)\s*\(|font\.update|\.transform\s*=[^=]", _src221),
      "| recursive mark:", ns["_MARK_RECURSIVE"], src.count("items.notifyChangesApplied(_MARK_TITLES[how], w, True)"), "| title:", ns["_MARK_TITLES"].get("expand"),
      "| guard full:", "expand" in ns["_GUARD_FULL_KINDS"], "| activity:", ns["_ACT_WRITES"].get("/glyph/expand"),
      "| route documented:", 'POST /glyph/expand          {"glyphs"' in src, "| dispatched:", 'if path == "/glyph/expand":' in src, "| version", ns["VERSION"])
for _g in ("xt1a", "xt1b", "xt1c", "xt1d", "xt1e", "xt1f", "xt1g", "xt1h", "xt1i", "xt9src"): TS.pop(_g, None); P72["layers"].pop(_g, None); P72["widths"].pop(_g, None)
