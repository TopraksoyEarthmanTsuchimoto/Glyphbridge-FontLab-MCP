"""Tests of the server-side outline analysis (analyze_outline and friends) against REAL data captured from
FontLab 8: testglyph1 (element scale + offset), testglyph4 (10 degree slant), identity glyphs, the Power Brush
glyph A, plus simulated mirror / two-element / fallback / failure cases. The MCP SDK is stubbed, so only the
standard library is needed. PRINT based; compare with expected_server_output.txt (run_all.py does that)."""
import sys, types, json, math
import os
HERE = os.path.dirname(os.path.abspath(__file__))
def _find(name):
    """Locate a project file: next to this script, one folder up, or in the current folder."""
    for d in (os.path.join(HERE, ".."), HERE, os.getcwd()):
        p = os.path.join(d, name)
        if os.path.exists(p):
            return p
    raise SystemExit("cannot find " + name + ": put the tests folder inside the project folder (next to it), or run from there")
# stub the MCP SDK so the server module can be imported
m1=types.ModuleType("mcp"); m2=types.ModuleType("mcp.server"); m3=types.ModuleType("mcp.server.mcpserver"); m4=types.ModuleType("mcp.server.mcpserver.exceptions")
class ToolError(Exception): pass
m4.ToolError=ToolError
class MCPServer:
    def __init__(self,*a,**k): pass
    def tool(self): return lambda f: f
m2.MCPServer=MCPServer
m3.Context=type("Context",(),{})  # server v0.34 imports it for the tools' ctx parameter
sys.modules.update({"mcp":m1,"mcp.server":m2,"mcp.server.mcpserver":m3,"mcp.server.mcpserver.exceptions":m4})
import importlib.util
spec=importlib.util.spec_from_file_location("srv",_find("glyphbridge_mcp_server.py")); srv=importlib.util.module_from_spec(spec); spec.loader.exec_module(srv)

def mk(name,nodes,bbox,margins,comp=0):
    contours=[]; cur=None
    for i,(x,y,kind,sm) in enumerate(nodes):
        if kind=="Move": cur=[]; contours.append(cur)
        cur.append({"index":i,"x":float(x),"y":float(y),"kind":kind,"smooth":sm})
    return {"open":True,"found":True,"name":name,"layer_route":"body","layer_name":"test_font","node_count":len(nodes),
            "contour_count_reported":len(contours),"contour_count_grouped":len(contours),
            "contours":[{"node_count":len(c),"nodes":c} for c in contours],
            "fontlab_bbox":bbox,"margins":margins,"component_count":comp}
def bb(l,r,b,t): return {"left":l,"right":r,"bottom":b,"top":t}

# ---- testglyph1 (the odd one), real captured data ----
# (x, y, on-curve flag) of every node, captured from FontLab 8 and embedded here so that no data files are needed
P=[
    (82, 378, 1), (99, 416, 0), (167, 430, 0), (201, 418, 1), (218, 412, 0), (243, 385, 0), (257, 350, 0), (255, 314,
    0), (245, 299, 1), (235, 284, 0), (214, 251, 0), (191, 223, 0), (169, 206, 0), (157, 207, 1), (145, 208, 0), (122,
    208, 0), (100, 214, 0), (82, 230, 0), (76, 248, 1), (64, 283, 0), (72, 355, 0), (167, 159, 1), (152, 153, 0),
    (127, 139, 0), (113, 123, 0), (113, 106, 0), (125, 97, 1), (137, 88, 0), (160, 70, 0), (183, 61, 0), (203, 63, 0),
    (212, 72, 1), (221, 81, 0), (237, 101, 0), (247, 120, 0), (247, 138, 0), (239, 146, 1), (223, 163, 0), (184, 167,
    0)]
n1=[(x,y,("Move" if i in (0,21) else "On" if on else "Off"),bool(on)) for i,(x,y,on) in enumerate(P)]
g1=mk("testglyph1",n1,bb(75.89375305175781,259.52647709846497,83.08723449707031,440.5165710449219),
      {"left":78.74814772605895,"right":74.30605468153954,"width":333.0})
r=srv.analyze_outline(g1); v=r["verification"]
print("testglyph1:",v["status"],v.get("calibration"))
n4=r["contours"][0]["nodes"][4]; print("  node 4:",n4["x"],n4["y"],"(FontLab readout 222.4, 423.1) raw",n4["raw_x"],n4["raw_y"])
print("  margins rebuilt:",v["margin_check"]["reconstructed_left_margin"],v["margin_check"]["reconstructed_right_margin"],"vs FontLab 78.748 / 74.306")
print("  ink_bbox:",r["ink_bbox"])

# ---- testglyph3 (after one TT conversion) ----
k3=["Move","On","Off","Off","Off","Off","On","Off","Off","Off","Off"]
xy3=[(128,414),(383,274),(357,267),(307,235),(255,208),(202,200),(173,217),(144,234),(110,281),(99,334),(111,389)]
n3=[(x,y,k,k in("Move","On")) for (x,y),k in zip(xy3,k3)]
g3=mk("testglyph3",n3,bb(99,383,200,414),{"left":101.86956521739131,"right":117.0,"width":500.0})
r=srv.analyze_outline(g3); print("testglyph3:",r["verification"]["status"],"| ink",r["ink_bbox"],"| curve type",r["contours"][0]["curve_type"])

# ---- testglyph2 (Pen, cubic, has a straight edge) ----
k2=[(128,414,"Move"),(383,274,"On"),(314,255,"Curve"),(250,172,"Curve"),(173,217,"On"),(96,262,"Curve"),(83,347,"Curve")]
n2=[(x,y,k,k in("Move","On")) for x,y,k in k2]
g2=mk("testglyph2",n2,bb(83,383,172,414),{"left":102.0,"right":117.0,"width":500.0})
r=srv.analyze_outline(g2); mc=r["verification"]["margin_check"]
print("testglyph2 rebuilt margins:",mc["reconstructed_left_margin"],mc["reconstructed_right_margin"],"| FontLab shows LSB 102, RSB 117 (displayed truncated)")
print("  svg:",r["contours"][0]["svg_path"])
g2["margins"]={"left":mc["reconstructed_left_margin"],"right":mc["reconstructed_right_margin"],"width":500.0}
print("  status when margins agree:",srv.analyze_outline(g2)["verification"]["status"])

# ---- A (Brush, 54 nodes cubic), real captured data ----
# (x, y, kind, smooth) of all 54 nodes, captured from FontLab 8 and embedded here (it used to be data/glyph_A.json)
nA=[
    (328.23883887862866, 366.2305774670247, 'Move', False), (345.46727382225595, 317.9526819282356, 'Curve', False),
    (356.767469245017, 267.6658039408988, 'Curve', False), (376.306807013645, 220.19451060675675, 'On', True),
    (387.5974254951141, 192.76368013520087, 'Curve', False), (402.17304066820077, 166.89093232081277, 'Curve', False),
    (415.6330506323567, 140.5050257220584, 'On', True), (421.624448768825, 128.75997708942037, 'Curve', False),
    (426.6192506934422, 116.50185143315981, 'Curve', False), (432.55136558110087, 104.79268386205109, 'On', True),
    (433.77519456295744, 102.37701611145674, 'Curve', False), (435.85110368202885, 100.46947337466405, 'Curve',
    False), (438.7277255219118, 100.46947337466405, 'On', True), (452.48414996349163, 100.46947337466405, 'Curve',
    False), (464.5339355293175, 123.57894148534155, 'Curve', False), (464.5339355293175, 135.5679261436826, 'On',
    True), (464.5339355293175, 137.28412428753188, 'Curve', False), (464.33230654185945, 139.00599235279572, 'Curve',
    False), (463.691163831836, 140.61080717749982, 'On', True), (449.0971513065585, 177.14040860059768, 'Curve',
    False), (427.34351794152894, 210.7122935774305, 'Curve', False), (411.4108268387242, 246.714814680223, 'On',
    True), (396.3062834284004, 280.84600064054683, 'Curve', False), (386.20826721059365, 316.8648455041332, 'Curve',
    False), (375.397281948539, 352.5052531787663, 'On', True), (372.2983246716432, 362.7215376373622, 'Curve', False),
    (357.6716880779047, 411.4046719982442, 'Curve', False), (353.54672763969535, 416.78468100736626, 'On', True),
    (352.1070449907513, 418.66239734855804, 'Curve', False), (349.9972617396382, 419.5279889310966, 'Curve', False),
    (347.6662261164027, 419.5279889310966, 'On', True), (326.18534780222524, 419.5279889310966, 'Curve', False),
    (283.52027910634206, 342.36503771087894, 'Curve', False), (273.15594822030636, 323.1828985725723, 'On', True),
    (258.9314101965357, 296.8563493191386, 'Curve', False), (241.41009652996118, 272.1059715102761, 'Curve', False),
    (230.4165130066987, 244.13170193069394, 'On', True), (213.42360402730668, 200.89155046189023, 'Curve', False),
    (209.33635635518328, 153.59783126156594, 'Curve', False), (194.55227719156198, 109.46812556176133, 'On', True),
    (193.3446264681785, 105.86335109990596, 'Curve', False), (192.46606447068254, 102.26183469417194, 'Curve', False),
    (192.46606447068254, 98.43207385631742, 'On', True), (192.46606447068254, 93.56611748525249, 'Curve', False),
    (194.5974180734857, 88.47201106890337, 'Curve', False), (200.3337738835973, 88.47201106890337, 'On', True),
    (210.68356740217916, 88.47201106890337, 'Curve', False), (220.18116225778962, 104.10291921716298, 'Curve', False),
    (223.44772280843802, 112.53187443823866, 'On', True), (243.40155224263856, 164.02026174410787, 'Curve', False),
    (241.30086252343926, 220.7889645625298, 'Curve', False), (271.3587168844717, 269.02879757237304, 'On', True),
    (291.1603464904365, 300.8084214284553, 'Curve', False), (304.80745431048996, 336.8400693737857, 'Curve', False)]
gA=mk("A",nA,bb(192.46606447068254,464.5339355293175,88.47201106890337,419.5279889310966),{"left":192.5,"right":174.5,"width":639.0})
r=srv.analyze_outline(gA); mc=r["verification"]["margin_check"]
print("A rebuilt margins:",mc["reconstructed_left_margin"],mc["reconstructed_right_margin"],"| FontLab shows LSB 192, RSB 174 -> expect [192,193) and [174,175)")
print("  A curve type",r["contours"][0]["curve_type"],"| contours",r["contour_count"],"| path pieces:",r["contours"][0]["svg_path"].count("C"),"cubics")

# ---- negative / edge cases ----
bad=json.loads(json.dumps(g3)); bad["margins"]["left"]=95.0
print("tampered margin ->",srv.analyze_outline(bad)["verification"]["status"])
nb=json.loads(json.dumps(g3)); nb["fontlab_bbox"]={"error":"boundingBox raised: x"}
print("no FontLab bbox ->",srv.analyze_outline(nb)["verification"]["status"])
cm=json.loads(json.dumps(g3)); cm["component_count"]=2
print("components note present:",any("component" in n for n in srv.analyze_outline(cm)["notes"]))
od=json.loads(json.dumps(g2)); od["contours"][0]["nodes"][2]["kind"]="Off"
ro=srv.analyze_outline(od); print("mixed handle kinds ->",ro["verification"]["status"],"|",ro["contours"][0].get("reconstruction_error"))
cb=json.loads(json.dumps(g2)); cb["contours"][0]["nodes"][3]["kind"]="Weird"
rb=srv.analyze_outline(cb); print("unknown kind ->",rb["verification"]["status"],"|",rb["contours"][0].get("reconstruction_error"))
nm=json.loads(json.dumps(g2)); nm["contours"][0]["nodes"][0]["kind"]="On"
rn=srv.analyze_outline(nm); print("no Move start ->",rn["verification"]["status"],"|",rn["contours"][0].get("reconstruction_error"))

print("---- new in v0.8 ----")
import copy
g1a=copy.deepcopy(g1); g1a["shape_count"]=1
r=srv.analyze_outline(g1a); v=r["verification"]
print("shape_count=1 ->",v["status"],"| as_element_transform:",v["calibration"]["as_element_transform"])
g1b=copy.deepcopy(g1); g1b["shape_count"]=2
r=srv.analyze_outline(g1b); print("shape_count=2 ->",r["verification"]["status"],"|",[n for n in r["notes"] if "elements" in n][0][:90])
g1c=copy.deepcopy(g1); g1c["shape_count"]=None
r=srv.analyze_outline(g1c); print("shape_count=None ->",r["verification"]["status"],"| has 'could not be read' note:",any("could not be read" in n for n in r["notes"]))
# slant simulation: x' = x + 0.3*y applied to testglyph2's raw nodes, FontLab reports slanted bbox/margins.
# The single-axis calibration must NOT be allowed to claim success.
import math
k2=[(128,414,"Move"),(383,274,"On"),(314,255,"Curve"),(250,172,"Curve"),(173,217,"On"),(96,262,"Curve"),(83,347,"Curve")]
sl=[(x+0.3*y,y) for x,y,_ in k2]
nsl=[(x,y,k,k in("Move","On")) for (x,y),(_,_,k) in zip(sl,k2)]
# the "FontLab" truth for a slanted ELEMENT: slant applied to the raw (unslanted) nodes
raw=mk("slanted",[(x,y,k,k in("Move","On")) for x,y,k in k2],bb(0,0,0,0),{})
truth=[(x+0.3*y,y) for x,y,_ in k2]
tb=bb(min(p[0] for p in truth),max(p[0] for p in truth),min(p[1] for p in truth),max(p[1] for p in truth))
# FontLab's margins come from the true slanted CURVE extremes:
tr=srv.analyze_outline(mk("t",[(sx_,sy_,k,k in("Move","On")) for (sx_,sy_),(_,_,k) in zip(truth,k2)],tb,{"left":0,"right":0,"width":500}))
ink=tr["ink_bbox"]; margins={"left":ink["left"],"right":500-ink["right"],"width":500.0}
raw=mk("slanted",[(x,y,k,k in("Move","On")) for x,y,k in k2],tb,margins); raw["shape_count"]=1
r=srv.analyze_outline(raw); mc=r["verification"]["margin_check"]
print("slanted element (not modelled): status =",r["verification"]["status"],"| margin check agrees:",mc["agrees"],
      "| rebuilt L/R margin",mc["reconstructed_left_margin"],mc["reconstructed_right_margin"],"vs FontLab",round(margins["left"],3),round(margins["right"],3))

print("---- testglyph4 (real slant 10 deg case) ----")
k4=[(128,414,"Move"),(383,274,"On"),(314,255,"Curve"),(250,172,"Curve"),(173,217,"On"),(96,262,"Curve"),(83,347,"Curve")]
g4=mk("testglyph4",[(x,y,k,k in("Move","On")) for x,y,k in k4],
      bb(142.198,431.314,172,414),{"left":158.87538476707536,"right":68.68640728588059,"width":500.0})
g4["shape_count"]=1
r=srv.analyze_outline(g4)
print("status:",r["verification"]["status"])
print("coordinate_space:",r["coordinate_space"][:80],"...")
print("node 0 shown as:",r["contours"][0]["nodes"][0],"(raw expected: 128, 414; displayed is really ~201.0)")
print("has attempted_calibration_NOT_applied:","attempted_calibration_NOT_applied" in r["verification"],"| has 'calibration':","calibration" in r["verification"])
print("ink_bbox:",r["ink_bbox"])
print("explanatory note present:",any("rotation or slant" in n for n in r["notes"]))
# regression: coordinate_space for the other statuses
for nm,g in (("testglyph1",g1a),("testglyph3",g3)):
    rr=srv.analyze_outline(g); print(nm,rr["verification"]["status"],"|",rr["coordinate_space"][:60])

# ======================= v0.9: DIRECT route with real element matrices =======================
import copy, math
print("\n==== v0.9 direct route ====")
IDM=dict(m11=1.0,m12=0.0,m21=0.0,m22=1.0,dx=0.0,dy=0.0,isIdentity=True)
def els(*shapes,wrapper="cached"):
    return {"available":True,"wrapper":wrapper,"source":"flGlyph(fgGlyph, fgFont)","layer_name":"test_font","shapes":list(shapes)}
def shp(contours,matrix,composite=False,component=False):
    return {"shape_type":"ShapeContours","contours":contours,"is_component":component,"is_composite":composite,"matrix":matrix}

# 1. testglyph1: real matrix, real FontLab box + margins
d=copy.deepcopy(g1); d["elements"]=els(shp(2,dict(m11=0.9514648914337158,m12=0.0,m21=0.0,m22=0.9686431884765625,dx=15.0,dy=24.0)))
r=srv.analyze_outline(d); v=r["verification"]
n0=r["contours"][0]["nodes"][0]; n4=r["contours"][0]["nodes"][4]
print("1 testglyph1:",v["status"],"|",v["transform_source"][:42],"| node0 (%s, %s) raw (%s, %s)"%(n0["x"],n0["y"],n0["raw_x"],n0["raw_y"]),"(FontLab shows 93, 390.1)")
print("   node4 (%s, %s) (FontLab 222.4, 423.1) | margins rebuilt %s / %s vs 78.748 / 74.306"%(n4["x"],n4["y"],v["margin_check"]["reconstructed_left_margin"],v["margin_check"]["reconstructed_right_margin"]))
print("   element:",r["elements"][0]["description"])

# 2. testglyph4: the 10 degree slant that the estimate had to REFUSE
d=copy.deepcopy(g4); d["elements"]=els(shp(1,dict(m11=1.0,m12=0.0,m21=0.17632697522640228,m22=1.0,dx=0.0,dy=0.0)))
r=srv.analyze_outline(d); v=r["verification"]; n0=r["contours"][0]["nodes"][0]
print("2 testglyph4:",v["status"],"(was 'unverified' before) | node0 x=%s (expected 128+0.17633*414 = 201.0)"%n0["x"],"| margins %s / %s vs FontLab 158.875 / 68.686"%(v["margin_check"]["reconstructed_left_margin"],v["margin_check"]["reconstructed_right_margin"]))
print("   element:",r["elements"][0]["description"])
print("   svg:",r["contours"][0]["svg_path"][:70],"...")

# 3. identity glyphs
for nm,g,sh in (("testglyph3",g3,shp(1,IDM)),("testglyph2",g2,shp(1,IDM)),("A",gA,shp(1,IDM,composite=True))):
    dd=copy.deepcopy(g); dd["elements"]=els(sh)
    if nm in("testglyph2","A"):   # their margins in the earlier tests were placeholders: take what the direct build reproduces
        tmp,_p,_ok,_n=srv._build_contours_with_matrices(dd["contours"],[(1,0,0,1,0,0)]*len(dd["contours"]))
        ib=srv._box(_p); dd["margins"]={"left":ib["left"],"right":dd["margins"]["width"]-ib["right"],"width":dd["margins"]["width"]}
    r=srv.analyze_outline(dd); print("3",nm,":",r["verification"]["status"],"|",r["elements"][0]["description"],"| composite note:",any("composite" in n for n in r["notes"]))

# 4. MIRROR: same bounding box and margins as the original, but the nodes are reversed. Estimate vs direct.
raw=[(128,414,"Move"),(383,274,"On"),(314,255,"Curve"),(250,172,"Curve"),(173,217,"On"),(96,262,"Curve"),(83,347,"Curve")]
mir=(-1.0,0.0,0.0,1.0,466.0,0.0)
dm=mk("mirrored",[(x,y,k,k in("Move","On")) for x,y,k in raw],bb(83,383,172,414),{"left":0,"right":0,"width":500.0}); dm["shape_count"]=1
_c,_p,_ok,_n=srv._build_contours_with_matrices(dm["contours"],[mir]); ib=srv._box(_p)
dm["margins"]={"left":ib["left"],"right":500.0-ib["right"],"width":500.0}
est=srv.analyze_outline(copy.deepcopy(dm))
dm["elements"]=els(shp(1,dict(m11=-1.0,m12=0.0,m21=0.0,m22=1.0,dx=466.0,dy=0.0)))
dr=srv.analyze_outline(dm)
print("4 mirrored glyph")
print("   WITHOUT the matrix (estimate only):",est["verification"]["status"],"| node0 x =",est["contours"][0]["nodes"][0]["x"],"<- raw, WRONG but 'verified'?" if est["verification"]["status"]=="verified" else "")
print("   WITH the real matrix              :",dr["verification"]["status"],"| node0 x =",dr["contours"][0]["nodes"][0]["x"],"(true mirrored position 466-128 = 338) |",dr["elements"][0]["description"])

# 5. two elements, each with its own transform
tw=copy.deepcopy(g1)
ms=[(1.0,0.0,0.0,1.0,0.0,0.0),(0.5,0.0,0.0,0.5,100.0,50.0)]
_c,_p,_ok,_n=srv._build_contours_with_matrices(tw["contours"],ms); ib=srv._box(_p)
allt=[srv._apply_matrix(ms[ci],n["x"],n["y"]) for ci,c in enumerate(tw["contours"]) for n in c["nodes"]]; tb=srv._box(allt)
tw["fontlab_bbox"]={"left":tb["left"],"right":tb["right"],"bottom":tb["bottom"],"top":tb["top"]}
tw["margins"]={"left":ib["left"],"right":333.0-ib["right"],"width":333.0}
tw["elements"]=els(shp(1,dict(m11=1.0,m12=0.0,m21=0.0,m22=1.0,dx=0.0,dy=0.0)),shp(1,dict(m11=0.5,m12=0.0,m21=0.0,m22=0.5,dx=100.0,dy=50.0)))
r=srv.analyze_outline(tw)
print("5 two elements:",r["verification"]["status"],"|",len(r["elements"]),"elements |",[e["description"][:30] for e in r["elements"]],"| mapping note:",any("2 elements" in n for n in r["notes"]))

# 6. fallbacks (the estimating route must still work, and say why)
d=copy.deepcopy(g4); d["elements"]={"available":False,"error":"RuntimeError: boom"}
r=srv.analyze_outline(d); print("6a unavailable    :",r["verification"]["status"],"| note:",[n for n in r["notes"] if "could not be read" in n][0][:60])
d=copy.deepcopy(g4); d["elements"]={"available":False,"error":"disabled (modern=no)"}
r=srv.analyze_outline(d); print("6b switched off   :",r["verification"]["status"],"| extra note:",any("element transforms" in n for n in r["notes"]))
d=copy.deepcopy(g1); d["shape_count"]=1; d["elements"]=els(shp(2,IDM))     # matrices contradict FontLab's box
r=srv.analyze_outline(d); print("6c matrix disagrees:",r["verification"]["status"],"(estimate takes over) | note:",[n for n in r["notes"] if "did not reproduce" in n][0][:70])
d=copy.deepcopy(g1); d["elements"]=els(shp(3,IDM))
r=srv.analyze_outline(d); print("6d contour mismatch:",any("mapping is unclear" in n for n in r["notes"]))
d=copy.deepcopy(g1); d["elements"]=els(shp(2,IDM,component=True))
r=srv.analyze_outline(d); print("6e component      :",any("component reference" in n for n in r["notes"]))
d=copy.deepcopy(g4); d["elements"]=els(shp(1,{"m11":1.0}))
r=srv.analyze_outline(d); print("6f incomplete matrix:",any("incomplete" in n for n in r["notes"]))
d=copy.deepcopy(g4); r=srv.analyze_outline(d); print("6g no 'elements' key (old listener):",r["verification"]["status"],"| no extra note:",not any("element transforms" in n for n in r["notes"]))
d=copy.deepcopy(g1); d["elements"]=els(shp(2,dict(m11=0.9514648914337158,m12=0.0,m21=0.0,m22=0.9686431884765625,dx=15.0,dy=24.0))); d["fontlab_bbox"]={"error":"boom"}
r=srv.analyze_outline(d); print("6h no FontLab bbox:",r["verification"]["status"],"| note:",any("unavailable" in n for n in r["notes"]))

# 7. matrix descriptions
for mx in ((1,0,0,1,0,0),(0.9514648914337158,0,0,0.9686431884765625,15,24),(1,0,0.17632697522640228,1,0,0),(-1,0,0,1,466,0),(math.cos(0.5),math.sin(0.5),-math.sin(0.5),math.cos(0.5),0,0)):
    print("7",srv._describe_matrix(mx))
