"""
Glyphbridge-FontLab-MCP  -  FontLab-side listener (v0.204)
=========================================================
Runs inside FontLab 8 and gives the Glyphbridge MCP server (glyphbridge_mcp_server.py, a separate
process) raw facts about the font open in FontLab over local HTTP (127.0.0.1:8765, never exposed).
It does not speak MCP itself: all interpretation lives in the server.

Documentation (repository folder mental-model/): version history in CHANGELOG.md, route details in
topics/server-and-endpoints.md, and the FontLab API rules every change must follow in
FONTLAB-API-RULES.md (several mistakes crash FontLab natively, beyond the reach of try/except).

MANUAL START ONLY: run this file from FontLab's Scripting panel once per FontLab session. It keeps
listening until FontLab is closed or /shutdown is called.

Runs entirely on FontLab's main thread: a QTimer polls a non-blocking socket every 25 ms, so every
fontlab API call happens on the main thread, which is the safe place for it. While a dialog opened
by the listener waits for a click, no other request is served; since v0.203 every such dialog closes by itself
(dialog_seconds, default 45 s), so it never outlasts an AI app's time limit.

No route ever saves, closes, exports or generates a font. Every write is verified by re-reading
before success is reported.

ACTIVITY LOG (v0.102): every change is reported in FontLab's OUTPUT panel as one short line, and reads
as one summary line (see _ACTIVITY_LOG). Since v0.105 each line starts with the name the client sent in the
X-Glyphbridge-Client header ("[claude-code > Glyphbridge]"), and reads answered "no font open" are listed apart.
Since v0.106 the config entry name "glyphbridge-fontlab" is left out of the name shown: the apps send
"local-agent-mode-glyphbridge-fontlab", which would repeat Glyphbridge ("[local-agent-mode > Glyphbridge]").
Since v0.109 a line without a client name starts with "[Glyphbridge]" (no guessed name), and the first time a client
name comes with a new X-Glyphbridge-Launcher value (the file name of the program that started the server, read by the
server from the operating system) one line names both ("[glyphbridge] local-agent-mode | CLAUDE"); the first pair is in
the "Connected" line. Since v0.110 the launcher is shown without ".exe" and in capitals, alike on Windows and macOS.

CHANGED MARK (v0.132): after a verified, synced glyph write, one flItems.notifyChangesApplied call makes FontLab count the
change, so it shows its blue icon and asks to save on close (live 657-667). The reply says what was done (fontlab_changed_mark).
Since v0.133 a verified delete is marked through one surviving glyph (live 684-687; via_glyph names it). Since v0.134 a kerning
write that changed an entry is marked through one glyph of a changed pair (research 713-717). Nothing is ever saved.
_MARK_CHANGED = False switches it off.

KERNING PANEL (v0.136): after a kerning write that changed an entry, and after its changed mark, one flItems.notifyPackageContentUpdated(<package fgId>)
makes FontLab's KERNING panel list the change at once (live 738, 741-743, one font, one master). The reply says what was done (fontlab_panel_refresh),
never what the panel shows. _REFRESH_KERNING_PANEL = False switches it off.

CHANGE LOG (v0.204): every product write that reaches the listener is judged from its own reply (changed: yes / no /
unknown, _change_verdict) and kept in a log of at most _CHANGE_LOG_MAX entries for this listener run, with the request's
X-Glyphbridge-Request-Id and X-Glyphbridge-Server-Run, the client, the font in front (package fgId) and one sequence number
per listener run; each font's running total is never trimmed. Every reply carries X-Glyphbridge-Run (this run's ID).
POST /changes answers the server's bookmark and unanswered IDs. Bookkeeping only: nothing here touches a glyph.

NO FONT OPEN (v0.105): every product route answers {"open": false} when CountFonts() is 0 (see _open_font):
with no font open, CurrentFont() still returns a placeholder font.

F1, POWER BRUSH GLYPHS (v0.120): touching the legacy glyph.layer or reading glyph.layers of a Power Brush glyph,
then any font.update(), writes a flattened copy of the glyph (live 332-496; glyph.width, glyph.components and the
name are safe). So /glyph/outline and /font/notdef read a glyph that has modern nodes from the modern layer only,
and the sync check after a width or sidebearing write compares only the legacy width (see _guard_classify).

Routes (GET unless marked POST):

  Status and font
    /health                     {"status": "ok"}
    /version                    {"version": VERSION}
    /font/current               live info about the current font; since v0.118 also the names FontLab keeps in the
                                font package (package_names: psn ffn tfn tsn sgn), when the package is matched to the font
    /font/glyphs                glyph names of the current font
    /font/nonempty              which glyphs hold outline data; layerless glyphs (an empty .notdef) are
                                listed as unreadable here, while /font/notdef and /glyph/outline call
                                them empty (a known inconsistency)
    /font/notdef                read-only .notdef check: missing / empty / has_outline / unknown
    POST /font/notdef/warn      re-checks; when .notdef is missing or empty, notes it ONCE per font (by its package fgId) and
                                listener run as one OUTPUT line; {"force": true} notes it again. Since v0.203 NO dialog; an empty
                                .notdef also gets the font's maturity (all 52 letters A-Z a-z present, one of them drawn)
    POST /font/create           {"family"?} (v0.146): ONE new font through flPackage(), also with other fonts open; with a family,
                                the four names Build Names gives and the legacy family, each read back, then ONE changed mark on
                                the new package; "notes" says what FontLab will not show (also printed in the OUTPUT panel)
    POST /changes               {"run"?, "since"?, "server_run"?, "ask_ids"?} (v0.204): the change log after "since" when "run" is
                                this run (else the whole run), grouped by font and by who sent it (this server_run or others),
                                entries dropped past the limit, each font's running total, and a verdict for each asked
                                request ID (changed / unchanged / unknown / not_seen / not_seen_or_dropped). Reads the log
                                only, never FontLab
    /shutdown, POST /shutdown   stops the listener; FontLab keeps running

  Reading glyphs
    /glyph/outline?name=X[&layer=body|active|strict|glayer][&modern=no]
                                THE main read. Since v0.120, a glyph with modern nodes is answered from the
                                modern layer only (source "modern": modern_outline, elements, component_count,
                                shape_count, and since v0.121 fontlab_ink_box from layer.inkBox()); the legacy
                                read below runs only for a glyph without modern nodes, for layer=strict|glayer
                                and for modern=no (F1 risk): contours (kind,
                                smooth, x, y), fontlab_bbox, margins, component_count, shape_count, layer_name,
                                elements, modern_check, and modern_outline when the legacy view is stale
    /glyph/width?name=X         advance width: modern advanceWidth (source "modern"), the legacy glyph.width as
                                legacy_width; the legacy width only when the modern side cannot be reached (v0.198)
    /glyph/sidebearings?name=X  modern lsb, rsb, advance and ink width
    /glyph/unicode?name=X       raw primary codepoint (no standard checks here: the server does that)
    /glyph/nodes?name=X[&attrs=a,b][&calls=c,d]
                                older bulk node read, superseded by /glyph/outline

  Writing glyphs
    POST /glyph/create          {"name", "scan_unicode"?}: one empty glyph; reports unicode and
                                unicode_status, duplicate_check, and created_under_other_names when
                                FontLab altered the name
    POST /glyph/delete          {"name", "dialog_seconds"?}: deletes one glyph after a Yes/No dialog in FontLab (default No);
                                since v0.203 the dialog closes by itself after dialog_seconds (10-50, default 45), counted as no
                                answer (not_answered); .notdef gets its own text
    POST /glyph/width           {"name", "width"}: advance width through the modern API
    POST /glyph/sidebearings    {"name", "left", "right"}: moves the outline so LSB = left, RSB = right
    POST /glyph/unicode         {"name", "unicode"}: sets the primary codepoint (0 removes it);
                                reports duplicate_check
    POST /glyph/polygon         {"name", "points" | "contours"}: closed straight contours as ONE shape
                                into an empty glyph; whole units (coordinates_rounded)
    POST /glyph/path            {"name", "contours"}: contours with cubic curves (c1 / c2, smooth) into an
                                empty glyph; whole units; verified node by node; a contour given as
                                {"points": [...], "closed": false} is drawn OPEN (v0.126)
    POST /glyph/move            {"name", "moves": [{"contour", "node", "from": {x, y}, "to": {x, y}}]} (v0.153):
                                moves existing nodes of a glyph with ONE plain shape; every "from" must
                                match first; whole units; verified node by node
    POST /glyph/component       {"name", "component", "x", "y"} (v0.169): ONE component of the glyph "component" into the
                                EMPTY glyph "name" at a whole-unit offset, through FontLab's recipe build; verified by re-reading;
                                {"name", "components": [{"component", "x", "y"}, ...], "confirmed_untested_size"} (v0.174): several,
                                in order, repeats allowed; more than 30 need confirmed_untested_size; the width is written back;
                                a name with "_" is refused (v0.175); a failure reply gives components_after
                                v0.186: a glyph that is NOT empty (contours, components, Power Brush shapes) gets the
                                temporary-layer route in the same request (placement "temporary layer"); a failure partway
                                restores the glyph (restore); an empty glyph keeps its route (placement "empty layer")
                                v0.187: both routes, both forms, need exactly one layer, the active one (NB 1353); the
                                single form's source-layer test is its own check (source_layer)
    POST /glyph/component/remove {"name", "index", "component", "x", "y"} or {"name", "components": [{"index", "component", "x",
                                "y"}, ...]} (v0.179): removes the components at those indices of layer.shapes, each checked first
                                against its expected source and offset; highest index first, layer.removeShape(shape, False);
                                verified by re-reading; autoLayer on and Power Brush shapes refused

  Kerning (never the whole table)
    POST /kerning/set           {"pairs": [[left, right, value], ...]} (v0.124): glyph : glyph pairs into the current
                                master's table, set(((left, False), (right, False)), value), each verified by re-reading;
                                all checks before the first write; stops at the first pair not confirmed. The KERNING panel
                                lists such pairs only after save and reopen; since v0.134 a write that changed an entry makes
                                one notification through a glyph of a changed pair (fontlab_changed_mark); since v0.136 it also
                                asks FontLab to refresh the KERNING panel (fontlab_panel_refresh)
    POST /kerning/remove        {"pairs": [[left, right], ...]} (v0.192): removes glyph : glyph entries of the current master's
                                table, remove(((left, False), (right, False))), each verified by re-reading (the entry gone,
                                len() one lower); a pair with no such entry is "no entry" and the request goes on; all checks
                                before the first removal; stops at the first pair not confirmed; then the mark and the panel
                                refresh of /kerning/set
                                Both (v0.194): a side written '@name' is a kerning group, confirmed by groups.items() and
                                getAllGroups() on a side that fits; key ((name, isClass), (name, isClass)); each class pair is
                                verified by its exact entry and one sample glyph pair (kind, classes, sample, sample_verdict);
                                a glyph side named like a kerning group gets same_name_group
    POST /kerning/group/rename  {"group", "new_name"} (v0.200): renames ONE kerning group of the current master, groups.rename(group,
                                new_name), confirmed by items() and getAllGroups() before and after (same members and side); a
                                new name of any group or class is refused, a glyph's name is allowed (same_name_glyph); the id
                                before and after (FontLab gives a renamed group a new id); then the mark, the panel refresh and
                                one member glyph's group id read (fontlab_caught_up)
    POST /kerning/group/remove  {"group", "pairs": "keep" | "delete", "dialog_seconds"?} (v0.200): removes ONE kerning group after a
                                Yes/No dialog in FontLab (default No; since v0.203 it closes by itself as /glyph/delete's does), groups.remove(group) or groups.remove(group, True); verified by re-reading
                                (gone from both sources, one group fewer); the table's size before and after; then the mark,
                                the refresh and the member check of the rename
    /kerning/pairs?pairs=A:V,T:o  or  ?text=AVATAR
                                FontLab's effective kerning per pair from the current master's table
                                (v0.104), class kerning included; source says which kind of entry
                                answered; with several fonts open the current one is matched to its
                                table by path (v0.112)
    POST /kerning/pairs         {"pairs": [[left, right], ...]} or {"text": "..."}: the same for large
                                reads (body read up to 1,000,000 bytes)
    /kerning/groups?groups=a,b&glyphs=c,d  or  ?all=yes[&confirmed=yes]
    POST /kerning/groups        {"groups": [...], "glyphs": [...]} or {"all_groups": true[, "confirmed_large_read": true]}
                                (v0.190): the current master's kerning groups with side, members and id, from ONE
                                groups.items() cross-checked with ONE getAllGroups() (confirmed); kerning groups only;
                                more than 250 groups in an all-groups read need confirmed

  Debug probes that only read (development only; not used by the MCP server)
    /debug/font, /debug/glyph?name=X       everything the font / one glyph object exposes
    /debug/layerstats?name=X               layer counts (needs the glyph.layer warm-up)
    /debug/findnode?name=X&index=N&stage=fetch|dir|read
    /debug/objdir?name=X&target=...&stage=dir|read
    /debug/walk?path=...                   restricted modern-API walker (_WALK_CALL_OK whitelist)
    /debug/layerbbox?name=X&stage=...      staged probe of layer.boundingBox()
    /debug/readmodern?name=X&stage=layer|contour|node   (stage=box&go=yes is GATED: layer.boundingBox(), layer.inkBox())
    /debug/classdir?name=CLASS[&members=a,b]   names and docstrings of one class; nothing is called
    /debug/fldir?contains=a,b              names in the fontlab module
    /debug/moddir?contains=a,b | module=M&contains=a,b | module=M&name=N | stage=kerntype
                                           names in modules ALREADY loaded (never imports); type of font.kerning
    /debug/fontdir?stage=dir|sub|member|memberdir    names-only probe of the font object (kerning and font-info research)
    /debug/fontdir?stage=keys&...&go=yes   GATED: ONE keys() call at the end of a memberdir path (font-info research)
    /debug/currentshapes                   modern shapes of the glyph open in the editor

  Gated debug probes (their changing stages refuse without go=yes; see the comment above each function)
    /debug/buildglyph     constructs a modern flGlyph wrapper and reads it
    /debug/trylayer       modern layer state; one layer-creation call on an empty glyph
    /debug/trymetrics     width and sidebearing experiments (glyph names starting with "tri")
    /debug/tryadvancewidth   names-only check, then one gated flGlyph.advanceWidth read (glyph names starting with "tri")
    /debug/trydialogtimeout  how=slot|python&seconds=3..50&go=yes: UI only, no font call: ONE test Yes/No dialog (default No)
                          with a single-shot QTimer owned by it, connected to the dialog's reject() slot (slot) or to a Python
                          function that calls reject() (python); elapsed time, result and clicked button; 10 per listener run (v0.201);
                          &countdown=yes: a second timer, every second, relabels the No button "No (N)" through a Python
                          function (button(No).setText); visual only, the closing is unchanged (v0.202)
    /debug/tryshape       shape-building experiments (pen, modern and curve variants); superseded
                          by /glyph/polygon and /glyph/path
    /debug/tryfont        a new font through flPackage(), once per listener run; stage=construct_named&family=F (v0.142) names it
                          in the same request as Build Names would (tfn, ffn, psn, sgn); &mark=yes (v0.145) then makes ONE
                          flItems.notifyChangesApplied(title, <that package>, False) on the package it just made
    /debug/trysync       flPackage.update() / flWorkspace.update() (both change nothing)
    /debug/trycreate      createGlyph with and without font.update()
    /debug/tryrefresh     F1: createGlyph or a Unicode value, then ONE fontlab.Update on that glyph; never font.update()
    /debug/trymodern      sync candidates and modern glyph creation
    /debug/trykern        one font.kerning.get((a, b)) call, 20 per listener run
    /debug/trygroups      one font.groups.getCompiled() call, 10 per listener run
    /debug/trypkgkern     one pair from flPackage.kerning(master) next to font.kerning, 20 per listener run;
                          &mode=flags&flags=FF|FT|TF|TT asks get(((a, flag), (b, flag))); a side flagged T may name a class
    /debug/trysetkern     WRITES: a=A&b=B&value=N&form=tuple|flags: ONE set() of one glyph pair on flPackage.kerning(master),
                          with get() before and after; glyph names only, no group of that name, |N| <= upm; 10 per listener run (v0.122);
                          &left=glyph|class&right=glyph|class (v0.193, class needs form=flags): a class side names a kerning group
                          confirmed by groups.items() and getAllGroups(), on a side that fits; set(((a, isClass), (b, isClass)), N)
    /debug/trydelkern     WRITES: a=A&b=B&form=tuple|flags: ONE remove() of one glyph pair on flPackage.kerning(master), with get()
                          and len() before and after; glyph names only, no group of that name; no mark, no refresh; 10 per run (v0.191);
                          &left / &right as /debug/trysetkern (v0.193): remove(((a, isClass), (b, isClass)))
    /debug/trykerngroupedit WRITES: op=rename&name=OLD&new=NEW or op=remove&name=N&pairs=keep|delete[&glyph=G]: ONE rename(OLD, NEW)
                          or remove(N[, True]) on the current master's kerning groups, a group confirmed by items() and getAllGroups();
                          both, len() of the table and the groups, and G's class entry before and after; no mark, no refresh;
                          10 per listener run (v0.199)
    /debug/trykernrefresh stage=container|update|changed: ONE flPackage.kerningContainer(), then fontlab.Update(container) or
                          container.changed(); flags and table size before and after; 6 per listener run (v0.123)
    /debug/trykerngroups  stage=all|modes|tuples|items&contains=a,b,c or stage=glyph&name=N: kerning group members and sides
                          (getAllGroups(), the master's groups.values(), a glyph's kerningLeft / kerningRight), 10 per listener run;
                          stage=tuples (v0.188) reads the values() entries as plain tuples, nothing in them called;
                          stage=items (v0.189) the same for groups.items(): (name, (members, side))
    /debug/features       stage=tags: font.features.keys(); stage=size&tag=T: has_key(T), get_feature(T), only the SIZE of that
                          feature's code is returned; stage=shape&tag=T: line counts by kind and the first 300 characters;
                          stage=lines&tag=T&contains=a,b,c: only the lines naming those names (v0.108); exactly one font open,
                          10 per listener run (v0.107, K11)
    /debug/tryopen        stage=detached|draw&name=ocp...&kind=line|curve: ONE open contour (never closed), detached or drawn into an
                          empty glyph and read back; 6 per listener run (v0.125, P2.1 research)
    /debug/tryedit        stage=movenode|addcontour|removecontour|replace&name=edp...[&contour=C&node=N&dx=DX&dy=DY][&refresh=R]: ONE edit
                          of a plain drawn glyph (one shape, no component, no Power Brush), outline before and after; refresh=R calls one
                          member of a fixed list after the edit, sidebearings before and after it (v0.152); exactly one font open,
                          8 per listener run (v0.151, P2.2 research)
    /debug/trycomponent   stage=glyphcomponents|shapedata&target=cpp...&source=cpp...&dx=DX&dy=DY: ONE placement of the source glyph
                          (one plain shape) in the target (an existing layer, at most one plain shape) at offset (dx, dy), elements
                          and outlines before and after; exactly one font open, 6 per listener run (v0.155, P2.7 research);
                          stage=readcomponents&target=cpp...: read only, ONE read of layer.components (v0.156);
                          stage=generate|setgenerated&target=cpp...&recipe=cpp...[+cpp...]: ONE package.generateGlyph, and for
                          setgenerated then ONE layer.setGlyphComponents with what it returned; send + as %2B (v0.157);
                          setgenerated&args=2..5: only the first N arguments of that call (v0.160); &pkg=id: the package's
                          fgId as its third argument (v0.161); &int=yes: 0 in place of False (v0.162); &width=int: the
                          width as a whole number (v0.163); &items=id: each component's name_id in place of it (v0.164);
                          stage=auto&target=cpp...&step=read|setrecipe|setauto|build[&recipe=R]: ONE step of the layer's own
                          recipe build (layer.recipe, layer.autoLayer, layer.buildAuto()) on an empty target (v0.165);
                          step=unauto|killauto: autoLayer = False, or ONE killAuto(), on an auto layer holding components (v0.166);
                          stage=offset&target=cpp...&how=assign|apply&dx=DX&dy=DY: ONE shape.transform = QTransform offset, or ONE
                          shape.applyTransform(QTransform), on a layer holding one component at identity, autoLayer off (v0.167);
                          stage=auto&step=clearrecipe: layer.recipe = "" on a layer of components, autoLayer off (v0.168)
                          stage=auto recipes of up to 30 glyphs (v0.173; five in v0.172, three in v0.171); stage=offset&how=assign&element=I&dx=DX&dy=DY: ONE
                          shape.transform = QTransform offset (absolute) on component I of a layer of 2 to 30 components, each at a
                          plain offset, autoLayer off; the others must stay as they are (v0.171)
                          stage=removeshape&target=cpp...&element=I&recursive=0|1: ONE layer.removeShape(<component I>, recursive);
                          stage=clearcomponents&target=cpp...: ONE layer.clearComponents(); on a layer of 1 to 30 components of cpp
                          glyphs, autoLayer off; elements, boxes, outline, width and sources before and after (v0.176)
                          stage=auto&step=setrecipe|setauto|build|unauto|clearrecipe&nonempty=yes: the same steps on a target that
                          already holds plain contours and / or components of cpp glyphs; existing_kept compares it with what
                          step=setrecipe found in this listener run (v0.180)
                          stage=templayer&target=cpp...&step=addlayer|build|move|removelayer[&recipe=cpp...]: ONE step of the
                          temporary-layer route (a layer gb_temp_component added to the target, the recipe build there, its
                          component added to the working layer, the layer removed); its own 10 calls per listener run (v0.181);
                          step=activate: ONE working_layer.setActive() (v0.182)
                          stage=fixlayer&target=cpp...&element=I: ONE shapeData.componentLayer = <the target's layer name> on
                          component I; its own 6 calls per listener run (v0.183)
                          stage=templayer&step=setlayer: the same assignment on the temporary layer's component, before
                          step=move; step=droptemp: an EMPTY gb_temp_component left behind removed (v0.184)
                          stage=templayer&brush=yes: the working layer may also hold Power Brush shapes (no inkBox() on them);
                          &sync=light: each step's sync check reads only glyph.width, never the legacy layer (F1);
                          sync=full (the default) keeps the full check; its own 20 calls per listener run (v0.185)
    /debug/markswitch     [on=0|1&go=yes]: S1 research (v0.170): without on, reads whether the changed mark (_MARK_CHANGED) is on; with
                          on=0 / on=1 and go=yes, switches it off / on for THIS listener run (a restart switches it on again); no
                          FontLab call is made
    /debug/tryshapebox    stage=shapebox|dependencies&name=X: read only; ONE shape.inkBox() per element, or ONE
                          flGlyph.isUnbindedDependecies(); exactly one font open; 12 per stage and listener run (v0.129, P1.1 research)
    /debug/trynotify      stage=state|call|ids&name=X[&which=W][&on=class|instance][&id_from=object|fg]: S1 and KERNING panel research; the changed
                          flags and history positions of the package, workspace and glyph; stage=call makes ONE flItems notification from a
                          fixed list (W), 3 per W and listener run; stage=ids reads the ids and asks findPackageId, 3 per listener run;
                          exactly one font open (v0.131, ids and id_from v0.135)
    /debug/trynames       stage=state|set|refresh|store|legacy_set[&field=F&value=V][&which=W]: P0.4 research; the five package names (psn ffn tfn tsn sgn),
                          fileName and the legacy font.info names; stage=set makes ONE assignment pkg.F = V, 10 per listener run; stage=refresh
                          ONE flItems call, W=content notifyPackageContentUpdated(fgId), package notifyPackageUpdated(fgId) or packages
                          notifyPackagesUpdated(), 3 per W and run (v0.138), model notifyModelChanged(), properties
                          notifyPropertiesChanged(<flPackage>), changed flPackage.changed() (v0.140), applied
                          notifyChangesApplied(title, <flPackage>, False), readed notifyPackageReaded(<flPackage>), added
                          notifyPackageAdded(<flPackage>) (v0.141); stage=store ONE flPackage.store_font_info(fgPackage) and
                          stage=legacy_set&field=familyName ONE font.info.familyName = V, 3 each per run (v0.139); stage=info_set
                          ONE flPackage.info.F = V for the Preferred family or subfamily, 3 per run, and every reply reads both (v0.143);
                          stage=title[&full=yes|no] ONE flPackage.title_name(True|False), 3 per run, and stage=state also reads elidedName
                          (v0.144); every stage but state needs go=yes; exactly one font open (v0.137)
    /debug/trypackage     name=X&go=yes: P0.9 research, read only, any number of fonts open; ONE read of flGlyph.package of a glyph of the
                          font in front, its reads, and ONE isEqual against the workspace's current package; 20 per listener run (v0.148);
                          stage=cached&go=yes: the same for the wrappers already cached (at most 20, none built), any font (v0.149)
    /debug/setcurrent    changes which glyph FontLab displays (no use for the modern API)

  Dead ends, kept as history: /debug/contours and /debug/drawpen (the pen protocol returns
  nothing), /debug/box, /debug/shapecount. /debug/layeritem is DISABLED: layer[N] subscript access
  crashed FontLab; the route only answers an error and must never be revived.
"""

import datetime
import hashlib
import json
import socket
import time
from urllib.parse import urlsplit, parse_qs, quote, unquote

import fontlab as fl
from PythonQt import QtCore

# QMessageBox lives under different submodules depending on the Qt
# binding version FontLab ships. Try both rather than guessing one.
try:
    from PythonQt.QtGui import QMessageBox
except ImportError:
    from PythonQt.QtWidgets import QMessageBox

HOST = "127.0.0.1"
PORT = 8765
POLL_MS = 25
VERSION = "0.204"
ENTRY_NAME = "glyphbridge-fontlab"  # the MCP config entry name: the apps put it into the client name they send (v0.106)

_REASONS = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}

_sock = None
_timer = None
_connection_announced = False
_request_client = None  # the cleaned X-Glyphbridge-Client name of the request being served (v0.105)
_request_launcher = None  # the X-Glyphbridge-Launcher value of the request being served, as shown (v0.109, v0.110)
_announced_clients = set()  # (client, launcher) pairs already named in this listener run (v0.109)


# --------------------------------------------------------------------------
# Read operations
# --------------------------------------------------------------------------

# Field name in our JSON -> attribute name on font.info (verified against
# a real FontLab 8.4 session via /debug/font).
_INFO_FIELDS = {
    "family_name": "familyName",
    "style_name": "styleName",
    "postscript_font_name": "postscriptFontName",
    "postscript_full_name": "postscriptFullName",
    "units_per_em": "unitsPerEm",
    "ascender": "ascender",
    "descender": "descender",
    "cap_height": "capHeight",
    "x_height": "xHeight",
    "weight_class": "openTypeOS2WeightClass",
}


def _open_font():
    """The current legacy font, or None when no font is open. "No font open" is CountFonts() == 0: with no font open
    CurrentFont() still returns a placeholder fgFont (empty path and family, one glyph "Paper"), which no route may read
    or change. When CountFonts() is missing or gives no plain number, CurrentFont() alone decides, as before v0.105."""
    try:
        counter = getattr(fl, "CountFonts", None)
        count = counter() if callable(counter) else None
    except Exception:
        count = None
    if type(count) is int and count == 0:
        return None
    font = fl.CurrentFont()
    if font is not None:
        _note_request_font(font, count)
    return font


# v0.113: the font a request used goes back in three response headers, so the server can name it in every reply and see a
# switched font window (goal 5 of PROJECT.md). The listener runs on FontLab's main thread, so the font cannot change between a
# route's work and its reply. The path itself never leaves the listener: only a short hash of it ("none" when it is empty).
# v0.114: the file name (the path's last part) is kept as well, for the delete dialog only; it is never sent in a header.
# "saved": True (a path), False (no path: None or empty, a font never saved) or None (the path could not be read).
_REQUEST_FONT = {"used": False, "family": "", "style": "", "key": "none", "saved": None, "file": "", "count": None}
_FONT_TEXT_MAX = 100


def _plain_text(value):
    """value without control characters, cut at _FONT_TEXT_MAX, or "" when it is not text. Never raises."""
    if not isinstance(value, str):
        return ""
    return "".join(ch for ch in value if not (ord(ch) < 32 or 127 <= ord(ch) <= 159))[:_FONT_TEXT_MAX]


def _font_text(info, attr):
    """A name field of font.info as plain text without control characters, or "" when unreadable. Never raises."""
    try:
        value = getattr(info, attr)
    except Exception:
        return ""
    return _plain_text(value)


def _note_request_font(font, count):
    """Remember the font this request uses (family, style, path hash, file name, CountFonts()). Never raises."""
    try:
        info = font.info
    except Exception:
        info = None
    try:
        path = font.path
        saved = bool(path) if path is None or isinstance(path, str) else None
    except Exception:
        path, saved = None, None
    key = hashlib.sha1(path.encode("utf-8")).hexdigest()[:12] if saved else "none"
    _REQUEST_FONT.update(used=True, family=_font_text(info, "familyName") if info is not None else "",
                         style=_font_text(info, "styleName") if info is not None else "", key=key, saved=saved,
                         file=_plain_text(path.replace("\\", "/").rsplit("/", 1)[-1]).strip() if saved else "",
                         count=count if type(count) is int else None)


def _forget_request_font():
    _REQUEST_FONT.update(used=False, family="", style="", key="none", saved=None, file="", count=None)


def _font_headers():
    """The three header lines for the font this request used, or "" when it used none."""
    if not _REQUEST_FONT["used"]:
        return ""
    lines = (f"X-Glyphbridge-Font: {quote(_REQUEST_FONT['family'], safe='')}/{quote(_REQUEST_FONT['style'], safe='')}\r\n"
             f"X-Glyphbridge-Font-Key: {_REQUEST_FONT['key']}\r\n")
    if _REQUEST_FONT["count"] is not None:
        lines += f"X-Glyphbridge-Fonts-Open: {_REQUEST_FONT['count']}\r\n"
    return lines


def get_current_font_info():
    """Real info about the font open in FontLab (fgFont -> font.info)."""
    font = _open_font()
    if font is None:
        return {"open": False}

    result = {"open": True, "path": font.path or None}

    try:
        result["glyph_count"] = len(font.glyphs)
    except Exception as exc:
        result["glyph_count"] = None
        result.setdefault("errors", []).append(f"glyph_count: {exc}")

    info = font.info
    for out_name, attr in _INFO_FIELDS.items():
        try:
            result[out_name] = getattr(info, attr)
        except Exception as exc:
            result[out_name] = None
            result.setdefault("errors", []).append(f"{out_name} ({attr}): {exc}")

    result.update(_package_names(font, _REQUEST_FONT["count"]))
    return result


# v0.118: FontLab keeps the names Font Info shows in the font's package; the legacy font.info can disagree. Test 298: after the
# PostScript field was set to W6aTest-Regular in Font Info, font.info.postscriptFontName still read Unnamed1-Regular, while
# flPackage.psn read W6aTest-Regular (test 300; ffn = Full name, tfn = Family name, tsn = Style name, sgn = Style group).
_PACKAGE_NAME_FIELDS = ("psn", "ffn", "tfn", "tsn", "sgn")


def _package_names(font, count):
    """{"package_names": {...}, "package_matched_by": ...} or {"package_names_unavailable": reason}. READ ONLY: the five name
    attributes of the workspace's current package, only when that package is proven to be this font: the only font open
    (_trysync_target), or, with several fonts, the same non-empty path (_kern_package_by_path). Each attribute is read once; a
    callable is never called, and a value that is not text is reported as None with the reason. Never raises."""
    try:
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        if type(count) is not int or count < 1:
            return {"package_names_unavailable": "the number of open fonts is unknown or not a positive number, so the font's package "
                                                 "cannot be matched to it"}
        if count == 1:
            ws, pkg, why = _trysync_target(mod)
            if ws is None:
                return {"package_names_unavailable": f"the font's package could not be reached: {why}"}
            matched_by = "only font"
        else:
            pkg, why = _kern_package_by_path(mod, font)
            if pkg is None:
                return {"package_names_unavailable": f"{count} fonts are open and this font's package could not be matched to it: {why}"}
            matched_by = "path"
        names, errors = {}, []
        for attr in _PACKAGE_NAME_FIELDS:
            try:
                value = getattr(pkg, attr)
            except Exception as exc:
                names[attr] = None
                errors.append(f"{attr} could not be read ({type(exc).__name__}: {exc})")
                continue
            if isinstance(value, str):
                names[attr] = _plain_text(value)
            else:
                names[attr] = None
                errors.append(f"{attr} is {'a callable (not called)' if callable(value) else 'not text'} ({type(value).__name__})")
        out = {"package_names": names, "package_matched_by": matched_by}
        if errors:
            out["package_name_errors"] = errors
        return out
    except Exception as exc:
        return {"package_names_unavailable": f"the font's package could not be read ({type(exc).__name__}: {exc})"}


def get_glyph_names():
    font = _open_font()
    if font is None:
        return {"open": False}
    names = [str(g.name) for g in font.glyphs]
    return {"open": True, "count": len(names), "names": names}


def _simple_attrs(obj):
    """Return {name: value} for public, non-callable attributes with simple values."""
    out = {}
    for name in dir(obj):
        if name.startswith("_"):
            continue
        try:
            val = getattr(obj, name)
        except Exception as exc:
            out[name] = f"<error: {exc}>"
            continue
        if callable(val):
            continue
        if isinstance(val, (str, int, float, bool)) or val is None:
            out[name] = val
        else:
            out[name] = f"<{type(val).__name__}>"
    return out


def debug_font_info():
    """Dump what the FontLab font object really exposes, so we stop guessing."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}

    report = {
        "type": type(font).__name__,
        "public_names": [n for n in dir(font) if not n.startswith("_")],
        "simple_values": _simple_attrs(font),
    }

    nested = {}
    for name in ("info", "fgFont", "fgPackage", "font", "names"):
        try:
            sub = getattr(font, name)
        except Exception:
            continue
        if sub is not None and not callable(sub):
            nested[name] = {
                "type": type(sub).__name__,
                "simple_values": _simple_attrs(sub),
            }
    report["nested"] = nested

    try:
        report["first_glyph_names"] = [
            str(getattr(g, "name", g)) for g in list(font.glyphs)[:10]
        ]
    except Exception as exc:
        report["first_glyph_names"] = f"<error: {exc}>"
    return report


# --------------------------------------------------------------------------
# Write operations
# --------------------------------------------------------------------------

def _unicode_after_create(font, name):
    """Unicode of a glyph this script has just created.

    This script never sets a codepoint at creation, so any value found here was
    assigned by FontLab itself from the glyph NAME (live: 'B' -> 66, 'eacute' ->
    233; a made-up name -> nothing). A failed read is reported as "unreadable",
    never as "none" - same rule as everywhere else: no evidence, no claim."""
    try:
        glyph = _find_glyph(font, name)
        if glyph is None:
            return {"unicode": None, "unicode_status": "unreadable",
                    "unicode_error": "the new glyph could not be found again"}
        raw = glyph.unicode
    except Exception as exc:
        return {"unicode": None, "unicode_status": "unreadable", "unicode_error": str(exc)}
    if raw in (None, 0):  # 0 and None both mean "no Unicode" in FontLab
        return {"unicode": None, "unicode_status": "none"}
    return {"unicode": raw, "unicode_status": "assigned"}


def _names_added(before, after):
    """Names that occur more often in `after` than in `before` (a multiset difference, so a second glyph with an
    EMPTY name is still seen when an empty-named one existed before)."""
    counts = {}
    for n in before:
        counts[n] = counts.get(n, 0) + 1
    added = []
    for n in after:
        if counts.get(n, 0) > 0:
            counts[n] -= 1
        else:
            added.append(n)
    return added


def _is_scan_codepoint(value):
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 0x10FFFF


# --------------------------------------------------------------------------
# v0.87 guard: do not run the legacy update calls while a drawn layer is unsynced
# --------------------------------------------------------------------------

_UNSYNCED = {"font": None, "glyphs": {}, "overflow": False}
_UNSYNCED_MAX = 500
_AUTO_SYNC = True       # v0.89: sync a glyph right after a modern write (fontlab.Update(flGlyph)); False restores the v0.88 behaviour
_MARK_CHANGED = True    # v0.132: tell FontLab that a verified, synced tool write changed the glyph (S1, live 657-667); False switches it off
_REFRESH_KERNING_PANEL = True    # v0.136: ask FontLab to refresh its KERNING panel after a kerning write that changed an entry (live 738, 741-743); False switches it off
_MARK_TITLES = {"layer_created": "Glyphbridge create", "width": "Glyphbridge width", "sidebearings": "Glyphbridge sidebearings",
                "draw_polygon": "Glyphbridge polygon", "draw_path": "Glyphbridge path", "unicode": "Glyphbridge Unicode", "delete": "Glyphbridge delete",
                "kerning": "Glyphbridge kerning", "tryedit": "Glyphbridge edit", "move_nodes": "Glyphbridge move nodes",
                "trycomponent": "Glyphbridge component", "trycomponent_light": "Glyphbridge component", "add_component": "Glyphbridge add component",
                "remove_component": "Glyphbridge remove component", "kerning_group": "Glyphbridge kerning group"}
_MARK_DELETE_MAX_TRIES = 20    # v0.133: how many surviving glyphs a delete's mark may try before it says none could be notified; v0.134: also a kerning write's mark
_SYNCED_NOTE = ("Glyphbridge asked FontLab to sync this glyph right after the change and FontLab's legacy view now matches the modern layer, so the "
                "change is durable against the display refresh of create_glyph, delete_glyph, set_glyph_unicode and the legacy width route. "
                "FontLab's own screen (editor numbers, grid thumbnail) may still repaint only at its next event.")
_UNSYNCED_NOTE = ("This change exists only in FontLab's modern layer and FontLab has not synced it yet. create_glyph, delete_glyph, "
                  "set_glyph_unicode and the legacy width route would remove it (their font.update() call throws such layers away), so "
                  "Glyphbridge skips that display refresh while the change is unsynced; the operation itself still runs. Opening the glyph "
                  "in an editor in FontLab and then sending any request makes FontLab sync it.")


def _guard_state(font):
    try:
        key = str(getattr(font, "path", ""))
    except Exception:
        key = ""
    if _UNSYNCED["font"] != key:            # another font: the remembered names do not apply
        _UNSYNCED["glyphs"].clear()
        _UNSYNCED["overflow"] = False
        _UNSYNCED["font"] = key
    return _UNSYNCED


def _guard_register(font, name, how):
    """Remember that `name` holds a change made through the modern API. Never raises. v0.120: a drawing or a new layer
    marks the glyph "full" for as long as it is remembered, so a later width write does not move it to the light check."""
    try:
        st = _guard_state(font)
        if name in st["glyphs"]:
            st["glyphs"][name]["how"] = how
        elif len(st["glyphs"]) >= _UNSYNCED_MAX:
            st["overflow"] = True
            return
        else:
            st["glyphs"][name] = {"how": how}
        if how in _GUARD_FULL_KINDS:
            st["glyphs"][name]["full"] = True
    except Exception:
        pass


def _auto_sync(font, name):
    """v0.89: ONE fontlab.Update(<modern glyph>) for `name`, then the guard classification. Returns the fontlab_sync block. Never raises."""
    out = {"attempted": False}
    try:
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        upd = getattr(mod, "Update", None)
        if not callable(upd):
            out["reason"] = "the fontlab module has no Update function"
            return out
        glyph = _find_glyph(font, name)
        if glyph is None:
            out["reason"] = "the glyph could not be found"
            return out
        w, _how = _modern_wrapper(glyph, font)
    except Exception as exc:
        out["reason"] = f"the modern glyph could not be reached ({type(exc).__name__}: {exc})"
        return out
    out["attempted"] = True
    try:
        upd(w)
    except Exception as exc:
        out["call_error"] = f"{type(exc).__name__}: {exc}"
    out["verdict"] = _guard_classify(font, name)
    out["synced"] = out["verdict"] == "synced"
    return out


def _mark_font_changed(font, name, how):
    """v0.132: ONE flItems.notifyChangesApplied(title, <flGlyph>, False) for a glyph that has a modern layer. Returns the
    fontlab_changed_mark block: "called", and "reason" when nothing was called, or "call_error" and "glyph_has_changes" (read after
    the call; true, false or "unknown"). No reading shows FontLab's icon or says it will ask, so the block never claims either."""
    try:
        if not _MARK_CHANGED:
            return {"called": False, "reason": "the changed mark is switched off in the listener"}
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        items = getattr(mod, "flItems", None)
        if items is None:
            return {"called": False, "reason": "the fontlab module has no flItems"}
        glyph = _find_glyph(font, name)
        if glyph is None:
            return {"called": False, "reason": "the glyph could not be found"}
        w, _how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"called": False, "reason": f"the modern glyph could not be reached ({type(exc).__name__}: {exc})"}
    layer, err = _tl_call(lambda: w.activeLayer)
    if err is not None:
        return {"called": False, "reason": f"the modern layer could not be read ({err})"}
    if layer is None:
        return {"called": False, "reason": "the glyph has no modern active layer"}
    mark = {"called": True}
    try:
        items.notifyChangesApplied(_MARK_TITLES[how], w, False)
    except Exception as exc:
        mark["call_error"] = f"{type(exc).__name__}: {exc}"
    value, err = _pkg_get(w, "hasChanges")
    mark["glyph_has_changes"] = value if err is None and type(value) is bool else "unknown"
    return mark


def _record_changed_mark(font, name, how, result, no_mark):
    """v0.132: put fontlab_changed_mark into a write reply. Only a confirmed change of a kind in _MARK_TITLES that FontLab has synced is
    marked: no_mark is the caller's reason why not. Never raises, so a verified write never fails here."""
    try:
        if how not in _MARK_TITLES:
            return
        if no_mark is not None:
            result["fontlab_changed_mark"] = {"called": False, "reason": no_mark}
        elif result.get("synced_with_fontlab") is not True:
            result["fontlab_changed_mark"] = {"called": False, "reason": "FontLab's sync of this glyph was not confirmed"}
        else:
            result["fontlab_changed_mark"] = _mark_font_changed(font, name, how)
    except Exception:
        pass


def _mark_font_changed_after_delete(font, names):
    """v0.133: a deleted glyph cannot be reported, so ONE notification goes to a surviving glyph (live 684-687: the icon turned blue
    and FontLab asked to save). names: the glyph list after the delete. The target is the first glyph that is not .notdef (untested as
    a target) and has a modern active layer, at most _MARK_DELETE_MAX_TRIES tried; "via_glyph" names it. Its content does not change.
    Never raises, so a verified delete never fails here."""
    try:
        if not _MARK_CHANGED:
            return {"called": False, "reason": "the changed mark is switched off in the listener"}
        candidates = [n for n in names if n != ".notdef"][:_MARK_DELETE_MAX_TRIES]
        if not candidates:
            return {"called": False, "reason": "no glyph other than .notdef is left to notify"}
        return _mark_through_first(font, candidates, "delete")
    except Exception as exc:
        return {"called": False, "reason": f"the mark failed ({type(exc).__name__}: {exc})"}


def _mark_through_first(font, candidates, how):
    """v0.134 (from v0.133's delete): ONE notification, to the first of candidates that can take it; "via_glyph" names it."""
    reason = None
    for name in candidates:
        mark = _mark_font_changed(font, name, how)
        if mark.get("called") is True:        # also when the call raised: one notification at most
            mark["via_glyph"] = name
            return mark
        reason = mark.get("reason")
    return {"called": False, "reason": f"none of the {len(candidates)} glyphs tried could be notified ({reason})"}


def _mark_font_changed_after_kerning(font, results):
    """v0.134: a kerning write has no glyph of its own to report, so ONE notification goes to a glyph of a pair whose entry changed (research
    713-717: blue icon, FontLab asked, the pair was saved at that question). results: the per-pair entries of set_kerning_pairs. Only an
    entry known to have changed counts, so re-setting the same value makes no call; a request that stopped partway still marks what changed.
    The target is the left glyph of the first changed pair, then its right glyph, then the sides of the later changed pairs, never .notdef
    (untested as a target), at most _MARK_DELETE_MAX_TRIES tried. The glyph's content does not change. Never raises, so a verified write never fails here."""
    try:
        if not _MARK_CHANGED:
            return {"called": False, "reason": "the changed mark is switched off in the listener"}
        changed = [e for e in results if e.get("changed") is True]
        if not changed:
            return {"called": False, "reason": "no kerning entry is known to have changed"}
        candidates, seen = [], set()
        for entry in changed:
            sample = entry.get("sample", False)      # v0.194: a pair with a class side is marked through its sample glyphs, never a class name
            names = (entry.get("left"), entry.get("right")) if sample is False else ((sample["left"], sample["right"]) if isinstance(sample, dict) else ())
            for name in names:
                if name != ".notdef" and name not in seen:
                    seen.add(name)
                    candidates.append(name)
        if not candidates:
            if any(e.get("sample", False) is None for e in changed):
                return {"called": False, "reason": "no glyph of a changed pair can take the mark: a changed class entry's group has no member "
                                                   "that is a glyph of the font, and the other glyphs are only .notdef"}
            return {"called": False, "reason": "the changed pairs name only .notdef, which is not used as a target"}
        return _mark_through_first(font, candidates[:_MARK_DELETE_MAX_TRIES], "kerning")
    except Exception as exc:
        return {"called": False, "reason": f"the mark failed ({type(exc).__name__}: {exc})"}


def _refresh_kerning_panel(pkg, results):
    """v0.136: ONE flItems.notifyPackageContentUpdated(<package fgId>) when at least one entry is known to have changed, also when the request stopped
    partway. It takes a uint: the package's object id does not fit and raises (731, 732), fgId is accepted (738). In testing FontLab's KERNING panel then
    listed new pairs and new values at once (738, 741-743); no reading shows the panel, so the block says only what was called. Never raises, so a verified write never fails here."""
    try:
        if not _REFRESH_KERNING_PANEL:
            return {"called": False, "reason": "the panel refresh is switched off in the listener"}
        if not any(e.get("changed") is True for e in results):
            return {"called": False, "reason": "no kerning entry is known to have changed"}
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        items = getattr(mod, "flItems", None)
        if items is None:
            return {"called": False, "reason": "the fontlab module has no flItems"}
        pid, err = _pkg_get(pkg, "fgId")
        if err is not None:
            return {"called": False, "reason": err}
        if type(pid) is not int:
            return {"called": False, "reason": f"the package's fgId is a {type(pid).__name__}, not a plain number"}
        if not 0 <= pid <= _TRYNOTIFY_UINT_MAX:
            return {"called": False, "reason": f"the package's fgId is {pid}, which does not fit a uint"}
    except Exception as exc:
        return {"called": False, "reason": f"the panel refresh failed ({type(exc).__name__}: {exc})"}
    refresh = {"called": True}
    try:
        items.notifyPackageContentUpdated(pid)
    except Exception as exc:
        refresh["call_error"] = f"{type(exc).__name__}: {exc}"
    return refresh


def _guard_mark(font, name, how, result, no_mark=None):
    """Register and say so in the reply; v0.89: then ask FontLab to sync the glyph (_AUTO_SYNC); v0.132: then the changed mark. Never raises."""
    _guard_register(font, name, how)
    try:
        result["synced_with_fontlab"] = False
        result["durability_note"] = _UNSYNCED_NOTE
    except Exception:
        pass
    if _AUTO_SYNC:
        try:
            sync = _auto_sync(font, name)
            result["fontlab_sync"] = sync
            if sync.get("synced") is True:
                _guard_state(font)["glyphs"].pop(name, None)
                result["synced_with_fontlab"] = True
                result["durability_note"] = _SYNCED_NOTE
        except Exception:
            pass
    _record_changed_mark(font, name, how, result, no_mark)


_GUARD_FULL_KINDS =("draw_polygon", "draw_path", "layer_created", "move_nodes", "add_component", "remove_component")   # v0.153: move_nodes keeps the node count, so the full check cannot see a lost move
_GUARD_LIGHT_KINDS = ("width", "sidebearings", "trycomponent_light")   # v0.185: the templayer probe with sync=light (Power Brush research, F1)


def _guard_is_light(font, name):
    """True when the remembered change of `name` is a width or sidebearing write and the glyph was never marked "full"."""
    try:
        entry = _guard_state(font)["glyphs"].get(name) or {}
    except Exception:
        return False
    return entry.get("how") in _GUARD_LIGHT_KINDS and not entry.get("full")


def _guard_classify(font, name):
    """'gone' | 'lost' | 'synced' | 'at_risk' | 'unknown' for one remembered glyph. Read only. Never raises.
    v0.120 (F1): after a width or sidebearing write, which can hit any glyph, a Power Brush one included, only the legacy
    glyph.width is compared with the modern advance width: touching glyph.layer or reading glyph.layers would arm F1
    (live 432-435, 490-492), glyph.width does not (486-488). Moving or widening a glyph never changes its node count.
    Drawings and new layers (an empty glyph before, so no brush) keep the full check."""
    try:
        glyph = _find_glyph(font, name)
        if glyph is None:
            return "gone"
        if _guard_is_light(font, name):
            w, _how = _modern_wrapper(glyph, font)
            modern, layer = _tryshape_modern_state(w)
            if layer is None:
                return "lost" if modern.get("active_layer") == "None" else "unknown"
            lw, mw = _num(glyph.width), _num(w.advanceWidth)
            if lw is None or mw is None:
                return "unknown"
            return "at_risk" if abs(lw - mw) > 0.01 else "synced"
        legacy = _tryshape_state(glyph)
        w, _how = _modern_wrapper(glyph, font)
        modern, layer = _tryshape_modern_state(w)
        if layer is None:
            return "lost" if modern.get("active_layer") == "None" else "unknown"
        mnodes = modern.get("nodes")
        if not isinstance(mnodes, int) or isinstance(mnodes, bool):
            return "unknown"
        llayers = legacy.get("layers")
        if not isinstance(llayers, int) or isinstance(llayers, bool):
            return "unknown"
        if llayers == 0:
            return "at_risk"
        lnodes = legacy.get("nodes")
        if not isinstance(lnodes, int) or isinstance(lnodes, bool):
            return "unknown"
        if lnodes != mnodes:
            return "at_risk"
        lw, mw = _num(glyph.width), _num(w.advanceWidth)
        if lw is not None and mw is not None and abs(lw - mw) > 0.01:
            return "at_risk"
        return "synced"
    except Exception:
        return "unknown"


def _guard_decide(font):
    """(allow, report): allow is True only when no remembered glyph is unsynced or unreadable. Forgets synced / gone / lost glyphs. Never raises."""
    try:
        st = _guard_state(font)
        at_risk, unknown, lost = [], [], []
        for name in list(st["glyphs"]):
            verdict = _guard_classify(font, name)
            if verdict in ("gone", "synced"):
                st["glyphs"].pop(name, None)
            elif verdict == "lost":
                st["glyphs"].pop(name, None)
                lost.append(name)
            elif verdict == "at_risk":
                at_risk.append(name)
            else:
                unknown.append(name)
        report = {}
        if lost:
            report["layers_missing_since_drawn"] = lost
        if st["overflow"]:
            report["display_refresh"] = "skipped"
            report["display_refresh_note"] = (f"more than {_UNSYNCED_MAX} glyphs were changed through the modern API in this run, so Glyphbridge can no longer "
                                              "tell which are unsynced; the legacy display refresh is skipped to be safe")
            return False, report
        if at_risk or unknown:
            report["display_refresh"] = "skipped"
            if at_risk:
                report["display_refresh_skipped_to_protect"] = at_risk
            if unknown:
                report["display_refresh_unreadable_glyphs"] = unknown
            report["display_refresh_note"] = ("The legacy display refresh (font.update()) was skipped because it would throw away the layers of "
                                              "glyphs FontLab has not synced yet, or because their state could not be read. The operation itself was done.")
            return False, report
        return True, report
    except Exception as exc:
        return False, {"display_refresh": "skipped", "display_refresh_note": f"the guard check failed ({type(exc).__name__}: {exc}); the legacy refresh was skipped to be safe"}


def create_glyph(name, scan_unicode=None):
    """Create one empty glyph and VERIFY it by re-reading font.glyphs.

    Never trusts createGlyph()'s return value alone: if the glyph isn't
    actually present afterward, this reports created=False with a reason,
    rather than a guessed success.
    """
    font = _open_font()
    if font is None:
        return {"open": False}

    before = [str(g.name) for g in font.glyphs]
    if name in before:
        return {
            "open": True,
            "created": False,
            "reason": "a glyph with this name already exists",
            "before_count": len(before),
            "after_count": len(before),
        }

    call_error = None
    try:
        font.createGlyph(name)
    except Exception as exc:
        call_error = str(exc)

    guard_ok, guard_report = _guard_decide(font)
    if guard_ok:
        try:
            font.update()
        except Exception:
            pass  # not fatal; the verification step below is what decides success

    after = [str(g.name) for g in font.glyphs]
    created = (name in after) and (len(after) == len(before) + 1)

    result = {
        "open": True,
        "created": created,
        "before_count": len(before),
        "after_count": len(after),
    }
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    if not created:
        # FontLab silently strips characters it does not accept from a name and creates THAT glyph (seen live), so a
        # failed create can still have changed the font: say so instead of "nothing happened".
        added = _names_added(before, after)
        if added:
            result["created_under_other_names"] = added
        if not call_error:
            result["reason"] = ("createGlyph() did not raise, but FontLab created a glyph under a different name instead"
                                if added else
                                "createGlyph() did not raise, but the glyph is not in font.glyphs afterward")
    if created:
        result.update(_unicode_after_create(font, name))
        if result.get("unicode_status") == "none" and _is_scan_codepoint(scan_unicode):
            result["duplicate_check"] = _other_glyphs_with_unicode(font, name, scan_unicode)
        result.update(_create_glyph_layer(name))        # v0.127: last, after the glyph is known to exist
    return result


def _one_master_problem():
    """None when the font in front has exactly one master, otherwise the reason. READ ONLY. flWorkspace.currentPackage follows the
    font window in front (live 262-264)."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    try:
        ws = mod.flWorkspace.instance()
    except Exception as exc:
        return f"the workspace could not be read ({type(exc).__name__}: {exc})"
    pkg, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return err
    if pkg is None:
        return "the workspace has no current package"
    masters_count, err = _pkg_get(pkg, "mastersCount")
    if err is not None:
        return err
    if type(masters_count) is not int or isinstance(masters_count, bool):
        return f"the number of masters is unknown (mastersCount is {masters_count!r})"
    if masters_count != 1:
        return f"this font has {masters_count} masters, and a layer at creation was tested only with one"
    return None


def _create_glyph_layer(name):
    """v0.127: give a glyph made by create_glyph its layer at once. Glyph > Add Component on a glyph without a layer crashes FontLab once
    the font holds a component (live 612-618); with a layer it did not (619). Returns the fields for the reply: layer_created when a
    layer was made, layer_note when the glyph has none, neither when it already had one. Never raises; the glyph stays created."""
    def no_layer(why):
        return {"layer_note": f"The glyph has no layer: {why}.", "fontlab_changed_mark": {"called": False, "reason": "the glyph has no layer"}}
    try:
        why = _one_master_problem()
        if why is not None:
            return no_layer(why)
        ctx, refusal = _modern_edit_target(name, create_layer=True)
        if ctx is None:
            return no_layer(str(refusal.get("reason") or "the layer could not be created"))
        out = {}
        if ctx.get("layer_created"):
            out["layer_created"] = ctx["layer_created"]
            out["layer_name_source"] = ctx.get("layer_name_source")
            _guard_mark(ctx["font"], name, "layer_created", out)
        else:
            out["fontlab_changed_mark"] = {"called": False, "reason": "no layer was created for the glyph here"}
        return out
    except Exception as exc:
        return no_layer(f"creating it failed ({type(exc).__name__}: {exc})")


def _deletion_text(name):
    """The question of the delete dialog, built only from facts of this request (v0.114): the name the client sent in
    X-Glyphbridge-Client, as the activity log shows it, and the font _open_font() noted (family and style, its file name or
    that it is not saved, and how many fonts are open). A missing client name stays missing: no agent name is guessed."""
    who = (f"{_request_client} (via Glyphbridge) is requesting to delete" if _request_client
           else "A request through Glyphbridge asks to delete")
    font = _REQUEST_FONT
    if font["used"]:
        title = " ".join(part for part in (font["family"], font["style"]) if part)
        where = f'from the font "{title}"' if title else "from a font without a name"
        details = []
        if font["saved"] is False:
            details.append("not saved to a file yet")
        elif font["saved"] is None:
            details.append("its file could not be read")
        elif font["file"]:
            details.append(f"file {font['file']}")
        if font["count"] is not None and font["count"] > 1:
            details.append(f"1 of {font['count']} open fonts, the one whose window is in front")
        if details:
            where += f" ({'; '.join(details)})"
    else:
        where = "from the font whose window is in front"
    if name == ".notdef":   # v0.203 (DECISIONS 2026-11-21): the one .notdef warning that stays a dialog
        return (f"{who} the glyph '{name}' {where}.\n\n{_NOTDEF_DELETION_WARNING}\n\nAllow this deletion?")
    return f"{who} the glyph '{name}' {where}.\n\nAllow this deletion?"


_NOTDEF_DELETION_WARNING = ("This is the .notdef glyph. Every font needs one as glyph 0: it is what shows when a character is missing "
                            "from the font. Deleting it leaves the font without one.")

# v0.203 - self-closing Yes/No dialogs (DECISIONS 2026-11-21; research SC 1588-1593, CD 1594-1598). The server sends its own
# dialog_seconds (45); the default serves an older server. Kept within 10-50 s, so a call with its dialog stays under the
# shortest AI-app time limit seen (60 s).
_DIALOG_SECONDS_DEFAULT = 45
_DIALOG_SECONDS_MIN, _DIALOG_SECONDS_MAX = 10, 50


def _dialog_seconds(value):
    """(seconds, None) or (None, error): the request's dialog_seconds kept within 10-50; missing -> 45. Not a whole number -> error."""
    if value is None:
        return _DIALOG_SECONDS_DEFAULT, None
    if type(value) is not int:
        return None, '"dialog_seconds" must be a whole number of seconds'
    return min(max(value, _DIALOG_SECONDS_MIN), _DIALOG_SECONDS_MAX), None


def _ask_yes_no(title, text, seconds, outcome):
    """v0.203 - ONE Yes/No dialog in FontLab (default No) that closes by itself after `seconds`, counted as no answer: a single-shot
    QTimer owned by the dialog, connected straight to its reject() slot (a pure Qt connection, SC 1590-1592). A second timer relabels
    the No button "No (N)" once a second through a Python function (CD 1596-1598); it is visual only, a failure is reported as
    countdown_error and the dialog still closes on time. Runs on the main thread like the whole listener.
    Returns {"answer": "yes" | "no" | "not_answered" | "unclear" | "not_shown", "seconds", "elapsed_s"?, "error"?, "countdown_error"?}.
    "not_shown": the closing timer could not be set up, so NO dialog was shown (a dialog that cannot close itself could be answered
    after the AI app gave up); "unclear": not Yes, but whether a button was clicked could not be read."""
    out = {"answer": "not_shown", "seconds": seconds}
    full = f"{text}\n\nIf you don't answer, this question closes by itself in {seconds} seconds and nothing is {outcome}."
    try:
        box = QMessageBox(QMessageBox.Warning, title, full, QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)  # Enter = No
        closer = QtCore.QTimer(box)           # owned by the dialog: it goes when the dialog goes
        closer.setSingleShot(True)
        closer.setInterval(seconds * 1000)
        if closer.connect("timeout()", box, "reject()") is False:
            raise RuntimeError("timer.connect returned False")
    except Exception as exc:
        out["error"] = f"the dialog could not be set up to close by itself ({type(exc).__name__}: {exc}); no dialog was shown"
        return out
    cd = {"ticks": 0, "error": None}
    held = {"box": box}  # emptied after the dialog, so the countdown function keeps no dialog alive

    def _tick():
        cd["ticks"] += 1
        left = seconds - cd["ticks"]
        if left < 1 or held["box"] is None:
            return  # the closing timer ends the dialog at 0; no "No (0)"
        try:
            held["box"].button(QMessageBox.No).setText(f"No ({left})")
        except Exception as exc:
            if cd["error"] is None:
                cd["error"] = f"relabel at tick {cd['ticks']}: {type(exc).__name__}: {exc}"

    ticker = None
    try:
        ticker = QtCore.QTimer(box)
        ticker.setSingleShot(False)
        ticker.setInterval(1000)
        if ticker.connect("timeout()", _tick) is False:
            raise RuntimeError("the countdown timer's connect returned False")
        box.button(QMessageBox.No).setText(f"No ({seconds})")  # only once the countdown can run
    except Exception as exc:
        cd["error"] = f"countdown setup: {type(exc).__name__}: {exc}"
        ticker = None
    started = time.monotonic()
    try:
        closer.start()
        if ticker is not None:
            ticker.start()
        answer = box.exec_()
    except Exception as exc:
        for t in (closer, ticker):
            try:
                if t is not None:
                    t.stop()
            except Exception:
                pass
        held["box"] = None
        out["error"] = f"the dialog failed ({type(exc).__name__}: {exc})"
        return out
    out["elapsed_s"] = round(time.monotonic() - started, 3)
    for t in (closer, ticker):
        try:
            if t is not None:
                t.stop()
        except Exception:
            pass
    if answer == QMessageBox.Yes:
        out["answer"] = "yes"
    else:
        try:
            clicked = box.clickedButton()
            out["answer"] = "not_answered" if clicked is None else "no"
        except Exception:
            out["answer"] = "unclear"
    if cd["error"]:
        out["countdown_error"] = cd["error"]
    held["box"] = None
    return out


def _confirm_deletion(name, seconds=_DIALOG_SECONDS_DEFAULT):
    """The delete question (v0.203: closes by itself after `seconds`); returns _ask_yes_no's result."""
    return _ask_yes_no("Glyphbridge: Confirm Deletion", _deletion_text(name), seconds, "deleted")


def _dialog_refusal(dialog, what):
    """v0.203 - the reply fields for a dialog that did not give a Yes. `what` is "deletion" or "removal"."""
    answer = dialog.get("answer")
    if answer == "no":
        return {"user_declined": True, "reason": f"the {what} was not approved in FontLab (answered No)"}
    if answer == "not_answered":
        return {"not_answered": True, "reason": f"nobody answered in FontLab within {dialog.get('seconds')} s; the question closed by itself"}
    if answer == "unclear":
        return {"user_declined": True, "reason": f"the {what} was not approved in FontLab (No, or no answer in time: which one could not be read)"}
    return {"dialog_error": str(dialog.get("error") or "the dialog could not be shown"),
            "reason": f"no dialog could be shown, so nothing was {'deleted' if what == 'deletion' else 'removed'}"}


def delete_glyph(name, seconds=_DIALOG_SECONDS_DEFAULT):
    """Delete one glyph, but only after a human confirms it in FontLab.

    Nothing is deleted unless (a) the glyph exists, (b) a Yes/No dialog
    was shown in FontLab and answered Yes, and (c) re-reading font.glyphs
    afterward confirms it is actually gone. Any other outcome is reported
    as deleted=False with a specific reason - never a guessed success.
    v0.203: the dialog closes by itself after `seconds` (not_answered); "dialog" says what happened.
    """
    font = _open_font()
    if font is None:
        return {"open": False}

    before = [str(g.name) for g in font.glyphs]
    if name not in before:
        return {
            "open": True,
            "deleted": False,
            "reason": "no glyph with this name exists",
            "before_count": len(before),
            "after_count": len(before),
        }

    dialog = _confirm_deletion(name, seconds)
    if dialog.get("answer") != "yes":
        refused = {"open": True, "deleted": False, "dialog": dialog, "before_count": len(before), "after_count": len(before)}
        refused.update(_dialog_refusal(dialog, "deletion"))
        return refused

    call_error = None
    try:
        font.removeGlyph(name)
    except Exception as exc:
        call_error = str(exc)

    guard_ok, guard_report = _guard_decide(font)
    if guard_ok:
        try:
            font.update()
        except Exception:
            pass

    after = [str(g.name) for g in font.glyphs]
    deleted = (name not in after) and (len(after) == len(before) - 1)

    result = {
        "open": True,
        "deleted": deleted,
        "before_count": len(before),
        "after_count": len(after),
        "dialog": dialog,
    }
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    if not deleted and not call_error:
        result["reason"] = "removeGlyph() did not raise, but the glyph is still in font.glyphs afterward"
    if deleted:
        result["fontlab_changed_mark"] = _mark_font_changed_after_delete(font, after)
        if name == ".notdef":
            result["notdef_deleted"] = True   # v0.203: the font now has no .notdef
    return result


def debug_glyph_info(name):
    """Dump what a single glyph object exposes, for developing new tools safely."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}

    glyph = next((g for g in font.glyphs if str(g.name) == name), None)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    report = {
        "open": True,
        "found": True,
        "type": type(glyph).__name__,
        "public_names": [n for n in dir(glyph) if not n.startswith("_")],
        "simple_values": _simple_attrs(glyph),
    }

    nested = {}
    for attr in ("layer", "layers", "advance", "advanceWidth", "metrics"):
        try:
            sub = getattr(glyph, attr)
        except Exception:
            continue
        if sub is not None and not callable(sub):
            nested[attr] = {
                "type": type(sub).__name__,
                "simple_values": _simple_attrs(sub) if not isinstance(sub, (str, int, float, bool)) else sub,
            }
    report["nested"] = nested
    return report


def _find_glyph(font, name):
    return next((g for g in font.glyphs if str(g.name) == name), None)


def get_glyph_width(name):
    """v0.198 (AW4 1470-1489): the width from the modern flGlyph.advanceWidth, with the legacy glyph.width as a cross-check;
    the legacy width is the answer only when the modern side cannot be reached. Raw facts only (the server compares them).
    Never touches the legacy layer (F1): only the wrapper, its activeLayer, advanceWidth and glyph.width are read."""
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    advance, modern_reason = None, None
    try:
        w, _how = _modern_wrapper(glyph, font)
    except Exception as exc:
        w, modern_reason = None, f"FontLab's modern glyph could not be reached ({exc})"
    if w is not None:
        try:
            layer = w.activeLayer
        except Exception as exc:
            layer, modern_reason = None, f"the modern active layer could not be read: {type(exc).__name__}: {exc}"
        if layer is None and modern_reason is None:
            modern_reason = "the glyph has no active modern layer"
        if layer is not None:
            try:
                advance = _num(w.advanceWidth)
                if advance is None:
                    modern_reason = "advanceWidth did not return a number"
            except Exception as exc:
                modern_reason = f"advanceWidth could not be read: {type(exc).__name__}: {exc}"
    legacy, legacy_error = None, None
    try:
        legacy = _num(glyph.width)
        if legacy is None:
            legacy_error = "glyph.width did not return a number"
    except Exception as exc:
        legacy_error = f"{type(exc).__name__}: {exc}"
    out = {"open": True, "found": True, "name": name, "advance_width": advance, "legacy_width": legacy}
    if advance is not None:
        out.update(width=advance, source="modern")
    elif legacy is not None:
        out.update(width=legacy, source="legacy", modern_reason=modern_reason)
    else:
        out.update(width=None, source=None, readable=False, modern_reason=modern_reason,
                   reason=f"neither width could be read: modern: {modern_reason}; legacy: {legacy_error}")
    if legacy_error is not None:
        out["legacy_error"] = legacy_error
    return out


_NO_MODERN_LAYER = ("this glyph has no editable layer yet: open it once in an editor tab in FontLab (double-click it in the glyph "
                    "overview), then try again.")
_DISPLAY_NOTE = ("Saved in FontLab's memory and read back correctly. The outline usually repaints at once; the numbers in the editor panel "
                 "and the central info box, the grey ghost fill and the grid thumbnail may show old values until you switch to the grid tab "
                 "and back, or close and reopen the glyph tab (FontLab refreshes them only on its own events).")
_EMPTY_NO_LAYER = ("this glyph is empty and has no layer yet, so it has no outline and no sidebearings: set_glyph_width and draw_polygon "
                   "create the layer by themselves.")


def _repaint_viewport():
    """Best effort: flWorkspace.instance().updateActiveViewport(). Live (v0.65 to v0.67 probes) it repaints the outline stroke and the
    slider numbers and nothing else. Never raises; True when the call went through."""
    try:
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        mod.flWorkspace.instance().updateActiveViewport()
        return True
    except Exception:
        return False


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _modern_margins_read(w, tr):
    """({"lsb", "rsb", "advance"}, None) from the modern getters, or (None, error text). Read only."""
    try:
        lsb, rsb, adv = _num(w.getLSB(tr)), _num(w.getRSB(tr)), _num(w.advanceWidth)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if lsb is None or rsb is None or adv is None:
        return None, "a modern margin getter did not return a number"
    return {"lsb": lsb, "rsb": rsb, "advance": adv}, None


def _derive_layer_name_from_glyphs(font, skip_name):
    """(layer name, None) or (None, reason). The name is read from the OTHER glyphs of the font that already have a modern layer; all of
    them must agree. font.master.name cannot be used (live v0.71: it is an empty string). At most 40 glyphs are examined and the scan
    stops after 5 glyphs with a layer."""
    try:
        glyphs = list(font.glyphs)
    except Exception as exc:
        return None, f"the glyph list could not be read ({type(exc).__name__}: {exc})"
    names, examined, with_layer = set(), 0, 0
    for g in glyphs:
        if examined >= 40 or with_layer >= 5:
            break
        try:
            gname = str(g.name)
        except Exception:
            continue
        if gname == skip_name:
            continue
        examined += 1
        try:
            gw, _how = _modern_wrapper(g, font)
            layer = gw.activeLayer
            if layer is None:
                continue
            lname = str(layer.name)
        except Exception:
            continue
        if not lname:
            continue
        with_layer += 1
        names.add(lname)
    if len(names) == 1:
        return next(iter(names)), None
    if not names:
        return None, ("no other glyph of the font has an editable layer to take the layer name from: open any glyph of this font once in "
                      "an editor tab in FontLab, then try again")
    return None, f"the glyphs of this font have different layer names ({sorted(names)}), so the right one cannot be chosen automatically"


_LAYER_NO_OTHER_GLYPH = "no other glyph of the font has an editable layer to take the layer name from"


def _pkg_get(obj, attr):
    """(value, None) or (None, error text): ONE read of a named attribute; a zero-argument callable is called once."""
    try:
        value = getattr(obj, attr)
        if callable(value):
            value = value()
        return value, None
    except Exception as exc:
        return None, f"{attr} could not be read ({type(exc).__name__}: {exc})"


def _package_fg_id(pkg, label):
    """(fgId, None) or (None, reason): the package's fgId as a plain whole number (not a bool). ONE read."""
    value, err = _pkg_get(pkg, "fgId")
    if err is not None:
        return None, f"{label}'s fgId could not be read ({err})"
    if type(value) is not int:
        return None, f"{label}'s fgId is a {type(value).__name__}, not a plain number"
    return value, None


def _package_layer_name(font, w=None):
    """(master name, None) or (None, reason). READ ONLY. The layer name of a font whose glyphs have no layer yet (a new font) is the
    name of its single master. v0.150 (ROADMAP P0.9): the package is the glyph's OWN, read from its modern wrapper (w.package), so any
    number of fonts may be open. 930 and 931 showed w.package naming the glyph's own font (fgId 8 with the font of fgId 5 in front),
    and flPackage.isEqual true for two different packages: isEqual is not used. The glyph comes from the font in front, so its
    package's fgId must equal the current package's; every check below must pass, otherwise nothing is guessed."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    if w is None:
        return None, "no modern glyph was given, so the glyph's own package could not be read"
    count_fonts = getattr(mod, "CountFonts", None)
    if count_fonts is None:
        return None, "the fontlab module has no CountFonts, so the number of open fonts is unknown"
    try:
        count = count_fonts()
    except Exception as exc:
        return None, f"CountFonts() failed ({type(exc).__name__}: {exc})"
    if type(count) is not int:
        return None, "CountFonts() did not return a whole number"
    if count < 1:
        return None, f"CountFonts() is {count}, so no font is open"
    try:
        ws = mod.flWorkspace.instance()
    except Exception as exc:
        return None, f"the workspace could not be reached ({type(exc).__name__}: {exc})"
    current, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return None, err
    if current is None:
        return None, "the workspace has no current package"
    is_null, err = _pkg_get(current, "isNull")
    if err is not None:
        return None, err
    if is_null is not False:
        return None, "the current package is null or its state is unknown"
    pkg, err = _pkg_get(w, "package")
    if err is not None:
        return None, f"the glyph's own package could not be read ({err})"
    if pkg is None:
        return None, "the glyph names no package of its own"
    is_null, err = _pkg_get(pkg, "isNull")
    if err is not None:
        return None, err
    if is_null is not False:
        return None, "the glyph's package is null or its state is unknown"
    own_id, err = _package_fg_id(pkg, "the glyph's package")
    if err is not None:
        return None, err
    current_id, err = _package_fg_id(current, "the current package")
    if err is not None:
        return None, err
    if own_id != current_id:
        return None, (f"the glyph's package (fgId {own_id}) is not the current package (fgId {current_id}), so the font in front and "
                      "the glyph may not belong together")
    masters_count, err = _pkg_get(pkg, "mastersCount")
    if err is not None:
        return None, err
    if type(masters_count) is not int or masters_count != 1:
        return None, f"the package does not have exactly one master (mastersCount is {masters_count!r})"
    default_master, err = _pkg_get(pkg, "defaultMaster")
    if err is not None:
        return None, err
    master, err = _pkg_get(pkg, "master")
    if err is not None:
        return None, err
    if (not isinstance(default_master, str) or not default_master.strip() or not default_master.isprintable()
            or len(default_master) > 100 or default_master != master):
        return None, f"defaultMaster ({default_master!r}) and master ({master!r}) are not the same usable name"
    masters, err = _pkg_get(pkg, "masters")
    if err is None and type(masters) in (list, tuple) and list(masters) != [default_master]:
        return None, f"the package's masters list ({list(masters)!r}) is not just {default_master!r}"
    glyphs_count, err = _pkg_get(pkg, "glyphsCount")
    if err is not None:
        return None, err
    try:
        font_glyphs = len(font.glyphs)
    except Exception as exc:
        return None, f"the font's glyph count could not be read ({type(exc).__name__}: {exc})"
    if _num(glyphs_count) is None or _num(glyphs_count) != float(font_glyphs):
        return None, f"the package has {glyphs_count!r} glyphs but the current font has {font_glyphs}, so they may not be the same font"
    upm, err = _pkg_get(pkg, "upm")
    if err is not None:
        return None, err
    try:
        font_upm = font.info.unitsPerEm
    except Exception as exc:
        return None, f"the font's unitsPerEm could not be read ({type(exc).__name__}: {exc})"
    if _num(upm) is None or _num(font_upm) is None or abs(_num(upm) - _num(font_upm)) > 1e-6:
        return None, f"the package's upm ({upm!r}) differs from the font's unitsPerEm ({font_upm!r}), so they may not be the same font"
    return default_master, None


def _derive_layer_name(font, skip_name, with_source=False, w=None):
    """(layer name, None) or (None, reason); with_source=True gives (name, None, source) or (None, reason, None). The name comes from the
    OTHER glyphs of the font that already have a modern layer (source 'other glyphs'). Only when none has one (a new font) the
    name of the font's single master is used (source 'package master'), after every check of _package_layer_name on the package of
    w, the glyph's modern wrapper (v0.150). A disagreement between glyphs, or an unreadable glyph list, is never overridden."""
    name, why = _derive_layer_name_from_glyphs(font, skip_name)
    source = "other glyphs" if name is not None else None
    if name is None and isinstance(why, str) and why.startswith(_LAYER_NO_OTHER_GLYPH):
        pname, pwhy = _package_layer_name(font, w)
        if pname is not None:
            name, why, source = pname, None, "package master"
        else:
            why = why + f" (the font's single master name was not used either: {pwhy})"
    return (name, why, source) if with_source else (name, why)


_EXISTING_LAYER_MAYBE = "the glyph may already have a layer"
_EXISTING_LAYER_FOUND = "the glyph already has a layer"
_EXISTING_LAYER_PREFIXES = (_EXISTING_LAYER_MAYBE, _EXISTING_LAYER_FOUND)


def _ensure_modern_layer(font, glyph, w, name):
    """Create the missing modern layer of a positively empty glyph. Returns ({"layer", "layer_name"}, None) or (None, reason)."""
    lname, why, lsource = _derive_layer_name(font, name, True, w)
    if lname is None:
        return None, why
    # v0.82: ask WITHOUT creating anything. findLayerCreate on an existing layer hands back an empty one (live v0.81: the drawn outline
    # was replaced), and right after a draw the wrapper can report no active layer while the layer exists.
    for how, args in (("getLayerByName", (lname, False)), ("findLayer", (lname,))):
        fn = getattr(w, how, None)
        if fn is None:
            return None, (f"{_EXISTING_LAYER_MAYBE} (the glyph has no {how} to ask with), so no layer was created")
        try:
            found = fn(*args)
        except Exception as exc:
            return None, (f"{_EXISTING_LAYER_MAYBE} ({how}({lname!r}) failed: {type(exc).__name__}: {exc}), "
                          "so no layer was created")
        if found is not None:
            return None, (f"{_EXISTING_LAYER_FOUND} named {lname!r}, which is not the glyph's active layer right now (it probably holds "
                          "a drawn outline): nothing was created and nothing was changed. Open the glyph in an editor tab (or switch to the grid "
                          "tab and back) so FontLab makes the layer active, then try again")
    try:
        w.findLayerCreate(lname)
    except Exception as exc:
        return None, f"findLayerCreate({lname!r}) failed: {type(exc).__name__}: {exc}"
    try:
        layer = w.activeLayer
    except Exception as exc:
        return None, f"the new layer could not be read back: {type(exc).__name__}: {exc}"
    if layer is None:
        return None, f"findLayerCreate({lname!r}) returned, but the glyph still has no active layer"
    try:
        made = str(layer.name)
    except Exception:
        made = lname
    return {"layer": layer, "layer_name": made, "layer_name_source": lsource}, None


def _modern_edit_target(name, create_layer=False):
    """What a modern metric edit needs. Returns (ctx, None) or (None, reply dict): ctx has font, glyph, w, tr and layer_nodes
    (None when unreadable). A glyph whose modern layer does not exist (not opened in an editor tab yet) is a refusal."""
    font = _open_font()
    if font is None:
        return None, {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return None, {"open": True, "found": False, "set": False, "reason": f"no glyph named {name!r}"}
    base = {"open": True, "found": True, "name": name, "set": False, "modern_layer": False}
    try:
        w, _how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return None, dict(base, reason=f"FontLab's modern glyph could not be reached ({exc})", glyph=glyph, font=font)
    try:
        layer = w.activeLayer
    except Exception:
        layer = None
    layer_created = None
    layer_source = None
    if layer is None:
        empty = _tryshape_known_empty(_tryshape_state(glyph))
        if create_layer and empty:
            made, info = _ensure_modern_layer(font, glyph, w, name)
            if made is not None:
                layer, layer_created = made["layer"], made["layer_name"]
                layer_source = made.get("layer_name_source")
                _guard_register(font, name, "layer_created")
            else:
                return None, dict(base, reason=(info if str(info).startswith(_EXISTING_LAYER_PREFIXES) else
                                                f"the glyph has no layer yet and one could not be created automatically: {info}"),
                                  create_layer_error=info, existing_layer=str(info).startswith(_EXISTING_LAYER_PREFIXES), glyph=glyph, font=font)
        else:
            return None, dict(base, reason=_EMPTY_NO_LAYER if empty else _NO_MODERN_LAYER, glyph=glyph, font=font)
    nodes = None
    try:
        n = layer.nodesCount
        nodes = int(n() if callable(n) else n)
    except Exception:
        nodes = None
    tr, tr_source = _trymetrics_transform()
    return {"font": font, "glyph": glyph, "w": w, "tr": tr, "tr_source": tr_source, "layer_nodes": nodes,
            "layer_created": layer_created, "layer_name_source": layer_source}, None


def _public_refusal(refusal):
    """The refusal dict without the internal glyph / font objects."""
    return {k: v for k, v in refusal.items() if k not in ("glyph", "font")}


def get_glyph_sidebearings(name):
    """Read only: modern LSB, RSB, advance width and ink width (= advance - LSB - RSB) of one glyph."""
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        return out
    if ctx["tr"] is None:
        return {"open": True, "found": True, "name": name, "modern_layer": True, "readable": False,
                "reason": ctx["tr_source"]}
    m, err = _modern_margins_read(ctx["w"], ctx["tr"])
    if m is None:
        return {"open": True, "found": True, "name": name, "modern_layer": True, "readable": False, "reason": err}
    return {"open": True, "found": True, "name": name, "modern_layer": True, "readable": True, "lsb": m["lsb"], "rsb": m["rsb"],
            "advance": m["advance"], "ink_width": m["advance"] - m["lsb"] - m["rsb"], "layer_nodes": ctx["layer_nodes"]}


def _set_width_modern(ctx, name, new_width):
    w, tr = ctx["w"], ctx["tr"]
    try:
        before = _num(w.advanceWidth)
    except Exception as exc:
        return {"open": True, "set": False, "name": name, "before": None, "after": None, "requested": new_width,
                "reason": f"the advance width could not be read: {type(exc).__name__}: {exc}"}
    m_before = _modern_margins_read(w, tr)[0] if tr is not None else None
    call_error = None
    try:
        w.advanceWidth = float(new_width)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    repainted = _repaint_viewport()
    try:
        after = _num(w.advanceWidth)
    except Exception:
        after = None
    success = (after is not None) and abs(after - float(new_width)) < 0.01
    result = {"open": True, "set": success, "name": name, "route": "modern", "before": before, "after": after,
              "requested": new_width, "display_refreshed": repainted, "display_note": _DISPLAY_NOTE}
    # v0.197 (AW 1449): a width that moved, but not to the request, is a change: say so, sync and mark it, never "not changed"
    changed_other = (not success) and after is not None and before is not None and abs(after - before) >= 0.01
    if success:
        _guard_mark(ctx["font"], name, "width", result, no_mark=None if abs(after - before) >= 0.01 else "the width did not change")
    elif changed_other:
        result["changed"] = True
        _guard_mark(ctx["font"], name, "width", result)
    if call_error:
        result["call_error"] = call_error
    if changed_other:
        result["reason"] = f"the width changed to {_act_num(after)}, not to the requested {_act_num(new_width)}"
    elif not success and not call_error:
        result["reason"] = "width did not change to the requested value after setting"
    m_after = _modern_margins_read(w, tr)[0] if tr is not None else None
    if m_before is not None and m_after is not None:
        result["outline_untouched"] = abs(m_before["lsb"] - m_after["lsb"]) < 0.01
        if not result["outline_untouched"]:
            result["warning"] = "the left sidebearing changed although only the advance width was set: the outline may have moved"
    return result


def _set_width_legacy(font, glyph, name, new_width):
    """The old legacy route; only for a glyph that is positively empty (no modern layer yet)."""
    before = glyph.width
    call_error = None
    try:
        glyph.width = new_width
    except Exception as exc:
        call_error = str(exc)
    guard_ok, guard_report = _guard_decide(font)
    if guard_ok:
        try:
            glyph.update()
        except Exception:
            pass
        try:
            font.update()
        except Exception:
            pass
    glyph_again = _find_glyph(font, name)
    after = glyph_again.width if glyph_again is not None else None
    success = (after is not None) and abs(after - float(new_width)) < 0.01
    result = {"open": True, "set": success, "name": name, "route": "legacy_empty_glyph", "before": before,
              "after": after, "requested": new_width,
              "fontlab_changed_mark": {"called": False, "reason": "the legacy width route is used only for a glyph with no modern layer"}}
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    changed_other = (not success) and _num(after) is not None and _num(before) is not None and abs(_num(after) - _num(before)) >= 0.01
    if changed_other:                     # v0.197: moved, but not to the request (no mark on this route, as before)
        result["changed"] = True
        result["reason"] = f"the width changed to {_act_num(after)}, not to the requested {_act_num(new_width)}"
    elif not success and not call_error:
        result["reason"] = "width did not change to the requested value after setting"
    return result


def _width_rounding(out, requested, target):
    """v0.197: report rule-B rounding of the requested width (FontLab's own width field rounds a typed 437.5 to 438, AW2 1456)."""
    if isinstance(out, dict) and float(requested) != target:
        out["requested"] = requested
        out["width_rounded"] = {"requested": requested, "written": target}
    return out


def set_glyph_width(name, new_width):
    """Set one glyph's advance width, verified by re-reading it afterward. With a modern layer the MODERN property
    flGlyph.advanceWidth is used (the outline is not touched); a glyph without one is written the legacy way only when it is
    positively empty, otherwise the request is refused (live finding: the legacy write lost work on glyphs with shapes).
    v0.197: the width is rounded to a whole unit first (rule B, a half rounds up): after advanceWidth = 437.5 FontLab's two
    views disagreed (legacy 437.5, advanceWidth 438.0, AW 1449), while its width field keeps whole units (AW2 1456)."""
    target = _round_half_up(new_width)
    ctx, refusal = _modern_edit_target(name, create_layer=True)
    if ctx is not None:
        out = _set_width_modern(ctx, name, target)
        if ctx.get("layer_created"):
            out["layer_created"] = ctx["layer_created"]
            out["layer_name_source"] = ctx.get("layer_name_source")
        return _width_rounding(out, new_width, target)
    if "glyph" not in refusal:            # no font, or no such glyph
        out = _public_refusal(refusal)
        if out.get("found") is False:
            out.update({"before": None, "after": None})
        return out
    font, glyph = refusal["font"], refusal["glyph"]
    if _tryshape_known_empty(_tryshape_state(glyph)) and not refusal.get("existing_layer"):
        out = _set_width_legacy(font, glyph, name, target)
        if refusal.get("create_layer_error"):
            out["layer_create_note"] = refusal["create_layer_error"]
        return _width_rounding(out, new_width, target)
    out = _public_refusal(refusal)
    out.update({"before": None, "after": None, "requested": new_width})
    return out


def set_glyph_sidebearings(name, left, right):
    """Move the outline so that LSB = left and RSB = right (modern flGlyph.setSB, identity transform); the advance width becomes
    LSB + ink + RSB. Refused when there is no modern layer or no outline. Verified by re-reading through the modern getters."""
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.update({"requested": {"left": left, "right": right}})
        return out
    w, tr = ctx["w"], ctx["tr"]
    base = {"open": True, "name": name, "set": False, "requested": {"left": left, "right": right}}
    if tr is None:
        return dict(base, reason=ctx["tr_source"])
    if ctx["layer_nodes"] == 0:
        return dict(base, reason="this glyph has no outline, so it has no sidebearings to set: use set_glyph_width for its advance width")
    before, err = _modern_margins_read(w, tr)
    if before is None:
        return dict(base, reason=f"the current margins could not be read: {err}")
    ink = before["advance"] - before["lsb"] - before["rsb"]
    if ink < -0.01:
        return dict(base, before=before, reason=f"the outline width read as negative ({ink}): nothing was changed")
    call_error, returned = None, None
    try:
        returned = repr(w.setSB(float(left), float(right), False, False, tr))
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    repainted = _repaint_viewport()
    after, err2 = _modern_margins_read(w, tr)
    result = dict(base, route="modern", before=before, after=after, ink_width=ink, setter_returned=returned,
                  display_refreshed=repainted, display_note=_DISPLAY_NOTE)
    if call_error:
        result["call_error"] = call_error
    if after is None:
        result["reason"] = f"the margins could not be re-read after the change: {err2}"
        return result
    expected = float(left) + ink + float(right)
    checks = {"lsb_ok": abs(after["lsb"] - float(left)) < 0.01, "rsb_ok": abs(after["rsb"] - float(right)) < 0.01,
              "advance_ok": abs(after["advance"] - expected) < 0.01}
    result["checks"] = checks
    result["expected_advance"] = expected
    result["changed"] = any(abs(after[k] - before[k]) > 0.001 for k in ("lsb", "rsb", "advance"))
    result["set"] = all(checks.values())
    if result["changed"]:
        _guard_mark(ctx["font"], name, "sidebearings", result, no_mark=None if result["set"] else "the new margins were not confirmed")
    if not result["set"]:
        mismatch = ", ".join(k for k, v in checks.items() if not v)
        result["reason"] = ("FontLab raised an error in setSB; the re-read margins differ from the request: " if call_error
                            else "the re-read margins do not match the request: ") + mismatch
    return result


_POLY_MIN_POINTS, _POLY_MAX_POINTS = 3, 500
_PATH_OPEN_MIN_POINTS = 2                  # v0.126: an open contour of draw_path (one straight or curved stroke at least)
_POLY_MAX_CONTOURS, _POLY_MAX_TOTAL = 20, 2000


def draw_polygon(name, contours, rounded=None):
    """Draw closed contours of straight segments (`contours`: a list of point lists) as ONE shape into a glyph whose modern layer is empty
    (creating the missing layer first when the glyph is empty). Everything is built detached first; only layer.addShape touches the glyph.
    Verified by re-reading the modern layer: 1 shape, as many nodes as points, as many contours as polygons. Never saves."""
    base = {"open": True, "name": name, "drawn": False, "route": "modern"}
    ctx, refusal = _modern_edit_target(name, create_layer=True)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["drawn"] = False
        return out
    w = ctx["w"]
    if ctx.get("layer_created"):
        base["layer_created"] = ctx["layer_created"]
        base["layer_name_source"] = ctx.get("layer_name_source")
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None or not _tryshape_modern_known_empty(state):
        return dict(base, reason=("the glyph's layer is not KNOWN to be empty (needs readable counts of 0 shapes, 0 nodes, 0 components), "
                                  "so nothing was drawn: draw_polygon only draws into an empty glyph"))
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    k = len(contours)
    sizes = [len(c) for c in contours]
    n = sum(sizes)
    step = "checking the classes"
    try:
        qp = getattr(QtCore, "QPointF", None)
        if qp is None or getattr(mod, "flContour", None) is None or getattr(mod, "flShape", None) is None:
            return dict(base, reason="QtCore.QPointF, fontlab.flContour or fontlab.flShape is missing: nothing was drawn")
        built = []
        for ci, pts in enumerate(contours):
            step = f"flContour(points) for contour {ci}"
            contour = mod.flContour([qp(float(x), float(y)) for x, y in pts])
            step = f"contour.closed = True for contour {ci}"
            contour.closed = True
            if contour.closed is not True or int(_call0(contour, "nodesCount")) != len(pts):
                return dict(base, reason=(f"the detached contour {ci} does not read closed with {len(pts)} nodes (closed={contour.closed!r}, "
                                          f"nodes={_call0(contour, 'nodesCount')!r}): nothing was attached"))
            built.append(contour)
        step = "flShape()"
        shape = mod.flShape()
        for ci, contour in enumerate(built):
            step = f"shape.shapeData.addContour(contour {ci})"
            shape.shapeData.addContour(contour)
        step = "layer.addShape(shape)"
        layer.addShape(shape)
    except Exception as exc:
        after, _l = _tryshape_modern_state(w)
        return dict(base, reason=f"{step} failed: {type(exc).__name__}: {exc}", state_after=after,
                    changed=(after.get("shapes") != 0 or after.get("nodes") != 0))
    repainted = _repaint_viewport()
    after, _l = _tryshape_modern_state(w)
    found_contours, cerr = _tl_call(lambda: layer.getContours())
    contours_ok = (len(found_contours) == k) if (cerr is None and type(found_contours) in (list, tuple)) else None
    result = dict(base, points=n, contours=k, contour_sizes=sizes, state_after=after, display_refreshed=repainted, display_note=_DISPLAY_NOTE)
    result["coordinates_rounded"] = list(rounded) if rounded else []
    result["checks"] = {"shapes_ok": after.get("shapes") == 1, "nodes_ok": after.get("nodes") == n, "contours_ok": contours_ok}
    result["drawn"] = all(v is not False for v in result["checks"].values()) and result["checks"]["shapes_ok"] and result["checks"]["nodes_ok"]
    result["changed"] = (after.get("shapes") != 0 or after.get("nodes") != 0)
    if result["changed"]:
        _guard_mark(ctx["font"], name, "draw_polygon", result, no_mark=None if result["drawn"] else "the drawing was not confirmed")
    if ctx["tr"] is not None:
        m, _err = _modern_margins_read(w, ctx["tr"])
        if m is not None:
            result["margins"] = m
            result["ink_width"] = m["advance"] - m["lsb"] - m["rsb"]
    if not result["drawn"]:
        got = len(found_contours) if contours_ok is not None else "an unreadable number of"
        result["reason"] = (f"after drawing, the layer reads {after.get('shapes')} shape(s), {after.get('nodes')} node(s) and {got} contour(s); "
                            f"expected 1, {n} and {k}")
    return result


_PATH_MAX_NODES = 6000
_PATH_SMOOTH_TOLERANCE_DEG = 2.0


def _round_half_up(v):
    """Rule B rounding: nearest whole unit, a half always rounds UP (2.5 -> 3, -2.5 -> -2), never banker's rounding."""
    import math as _math
    return float(_math.floor(float(v) + 0.5))


def _path_apply_rule_b(contours):
    """contours: lists of point dicts {x, y, c1, c2, smooth} (c1 / c2 are (x, y) tuples or None). Returns (new contours with whole-number
    coordinates, a list of every coordinate that changed: contour, point, field, requested, used)."""
    changes, out = [], []
    for ci, pts in enumerate(contours):
        new_pts = []
        for pi, p in enumerate(pts):
            q = {"smooth": bool(p.get("smooth")), "c1": None, "c2": None}
            for field in ("x", "y"):
                q[field] = _round_half_up(p[field])
                if q[field] != p[field]:
                    changes.append({"contour": ci, "point": pi, "field": field, "requested": p[field], "used": q[field]})
            for key in ("c1", "c2"):
                if p.get(key) is not None:
                    xy = []
                    for j, field in enumerate(("x", "y")):
                        used = _round_half_up(p[key][j])
                        xy.append(used)
                        if used != p[key][j]:
                            changes.append({"contour": ci, "point": pi, "field": f"{key}.{field}", "requested": p[key][j], "used": used})
                    q[key] = (xy[0], xy[1])
            new_pts.append(q)
        out.append(new_pts)
    return out, changes


def _path_layout(pts):
    """The node list FontLab must show for one contour (on-curve points p, curved segments by c1 / c2): a list of
    {x, y, on, smooth} in FontLab's order, and the index of every on-curve point in it. The handles of the segment that ends at point i
    (i >= 1) sit directly before it; those of the closing segment (point 0) are appended at the END (live-verified, v0.80)."""
    nodes, on_index = [], []
    for i, p in enumerate(pts):
        if i > 0 and p["c1"] is not None:
            for c in (p["c1"], p["c2"]):
                nodes.append({"x": c[0], "y": c[1], "on": False, "smooth": False})
        on_index.append(len(nodes))
        nodes.append({"x": p["x"], "y": p["y"], "on": True, "smooth": bool(p["smooth"])})
    if pts and pts[0]["c1"] is not None:
        for c in (pts[0]["c1"], pts[0]["c2"]):
            nodes.append({"x": c[0], "y": c[1], "on": False, "smooth": False})
    return nodes, on_index


def _path_smooth_problems(nodes, label, closed=True):
    """For every smooth on-curve node: the previous and the next node (a handle, or the neighbouring on-curve point) must lie on
    opposite sides of a straight line through it, within _PATH_SMOOTH_TOLERANCE_DEG; a neighbour on top of the node cannot define a
    direction. Returns a list of sentences (empty = fine). `nodes` are dicts with x, y, on, smooth. v0.126: closed=False (an open
    contour) has no wrap-around, so its first and last node, with one neighbour each, cannot be smooth."""
    import math as _math
    problems = []
    n = len(nodes)
    limit = _math.sin(_math.radians(_PATH_SMOOTH_TOLERANCE_DEG))
    for k, nd in enumerate(nodes):
        if not (nd.get("on") and nd.get("smooth")):
            continue
        if not closed and k in (0, n - 1):
            problems.append(f"{label}: the end point at ({nd['x']}, {nd['y']}) cannot be smooth: an end of an open contour has only one neighbour")
            continue
        a, b = nodes[(k - 1) % n], nodes[(k + 1) % n]
        ax, ay = a["x"] - nd["x"], a["y"] - nd["y"]
        bx, by = b["x"] - nd["x"], b["y"] - nd["y"]
        la, lb = _math.hypot(ax, ay), _math.hypot(bx, by)
        if la == 0 or lb == 0:
            problems.append(f"{label}: the smooth node at ({nd['x']}, {nd['y']}) has a neighbour on top of it, so no tangent direction exists")
            continue
        cross = (ax * by - ay * bx) / (la * lb)
        dot = (ax * bx + ay * by) / (la * lb)
        if dot >= 0 or abs(cross) > limit:
            problems.append(f"{label}: the smooth node at ({nd['x']}, {nd['y']}) is not smooth: the neighbours ({a['x']}, {a['y']}) and "
                            f"({b['x']}, {b['y']}) must lie on opposite sides of one straight line through it (within {_PATH_SMOOTH_TOLERANCE_DEG:g} degrees)")
    return problems


def _path_check_request(contours, closed_flags=None):
    """Pure checks on rounded contours; returns a list of sentences (empty = the request can be built). v0.126: closed_flags (one bool
    per contour, default all True); an open contour needs 2 different positions, no c1 / c2 on its first point, no smooth end."""
    problems = []
    flags = list(closed_flags) if closed_flags is not None else [True] * len(contours)
    for ci, pts in enumerate(contours):
        closed = flags[ci]
        if closed and len({(p["x"], p["y"]) for p in pts}) < 3:
            problems.append(f"contour {ci}: at least 3 different on-curve positions are needed (after rounding to whole units)")
        if not closed and len({(p["x"], p["y"]) for p in pts}) < _PATH_OPEN_MIN_POINTS:
            problems.append(f"contour {ci}: an open contour needs at least {_PATH_OPEN_MIN_POINTS} different on-curve positions (after rounding to whole units)")
        if not closed and pts and pts[0].get("c1") is not None:
            problems.append(f"contour {ci}: the first point of an open contour cannot have c1 / c2: an open contour has no closing segment")
            continue
        nodes, _idx = _path_layout(pts)
        problems.extend(_path_smooth_problems(nodes, f"contour {ci}", closed=closed))
    return problems


def _path_read_nodes(contour):
    """(rows, None) or (None, error): every node of a contour (x, y, isOn, isOff, isCurve, smooth) through getNodeAt after a range check."""
    count, err = _tl_call(lambda: _call0(contour, "nodesCount"))
    if err is not None or not isinstance(count, int) or isinstance(count, bool) or not (0 <= count <= _PATH_MAX_NODES):
        return None, f"nodesCount is not readable or not sane ({count!r}, {err})"
    rows = []
    for i in range(count):
        nd, err = _tl_call(lambda i=i: contour.getNodeAt(i))
        if err is not None or nd is None:
            return None, f"node {i}: getNodeAt failed: {err or 'returned None'}"
        rec = {"index": i}
        for label in ("x", "y", "isOn", "isOff", "isCurve", "smooth"):
            v, err = _tl_call(lambda a=label: _call0(nd, a))
            if err is not None:
                return None, f"node {i}: {label} could not be read: {err}"
            rec[label] = _rm_plain(v)
        if any(isinstance(rec[k], bool) or not isinstance(rec[k], (int, float)) for k in ("x", "y")):
            return None, f"node {i}: x / y are not numbers"
        rows.append(rec)
    return rows, None


def _path_mismatches(rows, expected, label):
    """Sentences for every node of `rows` that differs from `expected` (position, on-curve or handle, smooth flag of on-curve nodes)."""
    if len(rows) != len(expected):
        return [f"{label}: {len(rows)} nodes read, {len(expected)} expected"]
    bad = []
    for i, (r, e) in enumerate(zip(rows, expected)):
        why = []
        if abs(r["x"] - e["x"]) > 0.001 or abs(r["y"] - e["y"]) > 0.001:
            why.append(f"position ({r['x']}, {r['y']}) instead of ({e['x']}, {e['y']})")
        if e["on"]:
            if r.get("isOn") is not True or r.get("isCurve") is not False:
                why.append(f"should be an on-curve node but reads isOn={r.get('isOn')!r}, isCurve={r.get('isCurve')!r}")
            if bool(r.get("smooth")) != e["smooth"]:
                why.append(f"smooth reads {r.get('smooth')!r}, expected {e['smooth']}")
        elif r.get("isOn") is not False or r.get("isCurve") is not True:
            why.append(f"should be a curve handle but reads isOn={r.get('isOn')!r}, isCurve={r.get('isCurve')!r}")
        if why:
            bad.append(f"{label} node {i}: " + "; ".join(why))
    return bad


def _path_build_contour(mod, qp, pts, expected, on_index, closed=True):
    """Build ONE detached contour for the points `pts` and return it (the caller reads it back and judges it). Raises with the failing
    step in the message. v0.125: closed=False (only /debug/tryopen) leaves the contour as flContour(points) makes it: open (v0.57)."""
    m = len(pts)
    step = "flContour(points)"
    try:
        contour = mod.flContour([qp(p["x"], p["y"]) for p in pts])
        if closed:
            step = "contour.closed = True"
            contour.closed = True
        for i in range(m - 1, -1, -1):                      # descending: node 0 (the closing segment) LAST
            if pts[i]["c1"] is not None:
                step = f"convertToCurve(False) on node {i}"
                ret = contour.getNodeAt(i).convertToCurve(False)
                if ret is not True:
                    raise RuntimeError(f"it returned {ret!r}")
        for i, p in enumerate(pts):                         # smooth BEFORE the handles: setting it realigns handles
            if p["smooth"]:
                step = f"smooth = True on node {on_index[i]}"
                contour.getNodeAt(on_index[i]).smooth = True
        for idx, e in enumerate(expected):                  # handles LAST, by plain x / y assignment (keeps the value, no pairing)
            if not e["on"]:
                step = f"placing handle {idx}"
                nd = contour.getNodeAt(idx)
                nd.x = float(e["x"])
                nd.y = float(e["y"])
    except Exception as exc:
        raise RuntimeError(f"{step} failed: {type(exc).__name__}: {exc}")
    return contour


def draw_path(name, contours, rounded=None, closed_flags=None):
    """Draw contours with straight AND cubic segments as ONE shape into a glyph whose modern layer is empty. `contours`: lists of point
    dicts {x, y, c1, c2, smooth} with whole-number coordinates (rule B was applied by the caller; c1 / c2 are (x, y) or None). Everything is
    built and read back DETACHED first (node by node, and smooth collinearity); only layer.addShape touches the glyph, and the modern layer
    is read back afterwards and compared node by node. Never saves. v0.126: closed_flags (one bool per contour, default all True); an open
    contour is built without closed = True (live 589, 593: it stays open once attached), and its closed flag must read False both
    detached and on the layer."""
    flags = list(closed_flags) if closed_flags is not None else [True] * len(contours)
    base = {"open": True, "name": name, "drawn": False, "route": "modern"}
    if not all(flags):
        base["open_contours"] = [ci for ci, f in enumerate(flags) if not f]
    problems = _path_check_request(contours, flags)
    if problems:
        return dict(base, reason="the request cannot be drawn, nothing was changed: " + " | ".join(problems[:5]))
    ctx, refusal = _modern_edit_target(name, create_layer=True)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["drawn"] = False
        return out
    w = ctx["w"]
    if ctx.get("layer_created"):
        base["layer_created"] = ctx["layer_created"]
        base["layer_name_source"] = ctx.get("layer_name_source")
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None or not _tryshape_modern_known_empty(state):
        return dict(base, reason=("the glyph's layer is not KNOWN to be empty (needs readable counts of 0 shapes, 0 nodes, 0 components), "
                                  "so nothing was drawn: draw_path only draws into an empty glyph"))
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    if qp is None or getattr(mod, "flContour", None) is None or getattr(mod, "flShape", None) is None:
        return dict(base, reason="QtCore.QPointF, fontlab.flContour or fontlab.flShape is missing: nothing was drawn")
    k = len(contours)
    layouts = [_path_layout(pts) for pts in contours]
    sizes = [len(lay[0]) for lay in layouts]
    n = sum(sizes)
    on_points = sum(len(pts) for pts in contours)
    curved = sum(1 for pts in contours for p in pts if p["c1"] is not None)
    base.update({"points": on_points, "segments_curved": curved, "contours": k, "contour_sizes": sizes,
                 "coordinates_rounded": list(rounded) if rounded else []})
    built = []
    for ci, pts in enumerate(contours):
        expected, on_index = layouts[ci]
        try:
            contour = _path_build_contour(mod, qp, pts, expected, on_index, closed=flags[ci])
        except Exception as exc:
            return dict(base, reason=f"contour {ci} could not be built detached ({exc}): nothing was attached")
        rows, err = _path_read_nodes(contour)
        if rows is None:
            return dict(base, reason=f"the detached contour {ci} could not be read back ({err}): nothing was attached")
        closed, _e = _tl_call(lambda: contour.closed)
        bad = _path_mismatches(rows, expected, f"detached contour {ci}")
        if closed is not flags[ci]:
            bad.append(f"detached contour {ci}: closed reads {closed!r}" + ("" if flags[ci] else ", an open contour was requested"))
        bad.extend(_path_smooth_problems([{"x": r["x"], "y": r["y"], "on": e["on"], "smooth": e["smooth"]} for r, e in zip(rows, expected)],
                                         f"detached contour {ci}", closed=flags[ci]) if len(rows) == len(expected) else [])
        if bad:
            return dict(base, reason="the detached contour does not match the request, nothing was attached: " + " | ".join(bad[:6]))
        built.append(contour)
    step = "flShape()"
    try:
        shape = mod.flShape()
        for ci, contour in enumerate(built):
            step = f"shape.shapeData.addContour(contour {ci})"
            shape.shapeData.addContour(contour)
        step = "layer.addShape(shape)"
        layer.addShape(shape)
    except Exception as exc:
        after, _l = _tryshape_modern_state(w)
        return dict(base, reason=f"{step} failed: {type(exc).__name__}: {exc}", state_after=after,
                    changed=(after.get("shapes") != 0 or after.get("nodes") != 0))
    repainted = _repaint_viewport()
    after, _l = _tryshape_modern_state(w)
    result = dict(base, state_after=after, display_refreshed=repainted, display_note=_DISPLAY_NOTE)
    result["changed"] = (after.get("shapes") != 0 or after.get("nodes") != 0)
    modern = _read_modern_outline(name)
    mismatches, nodes_match = [], None
    if modern.get("available") is True:
        got = modern.get("contours") or []
        if len(got) != k:
            mismatches.append(f"the layer reads {len(got)} contour(s), {k} expected")
        else:
            for ci, entry in enumerate(got):
                if entry.get("closed") is not flags[ci]:
                    mismatches.append(f"layer contour {ci}: closed reads {entry.get('closed')!r}" + ("" if flags[ci] else ", an open contour was requested"))
                mismatches.extend(_path_mismatches(entry.get("nodes") or [], layouts[ci][0], f"layer contour {ci}"))
        nodes_match = not mismatches
    else:
        result["read_back_error"] = modern.get("error")
    result["checks"] = {"shapes_ok": after.get("shapes") == 1, "nodes_ok": after.get("nodes") == n, "nodes_match": nodes_match}
    result["nodes_match"] = nodes_match
    result["drawn"] = bool(result["checks"]["shapes_ok"] and result["checks"]["nodes_ok"] and nodes_match is True)
    if after.get("shapes") != 0 or after.get("nodes") != 0:
        _guard_mark(ctx["font"], name, "draw_path", result, no_mark=None if result["drawn"] else "the drawing was not confirmed")
    if ctx["tr"] is not None:
        m, _err = _modern_margins_read(w, ctx["tr"])
        if m is not None:
            result["margins"] = m
            result["ink_width"] = m["advance"] - m["lsb"] - m["rsb"]
    if not result["drawn"]:
        why = (f"after drawing, the layer reads {after.get('shapes')} shape(s) and {after.get('nodes')} node(s); expected 1 and {n}"
               if not (result["checks"]["shapes_ok"] and result["checks"]["nodes_ok"]) else "the layer does not match the request")
        if mismatches:
            why += ": " + " | ".join(mismatches[:6])
        elif nodes_match is None:
            why += f" (the outline could not be read back: {modern.get('error')})"
        result["reason"] = why
    return result


# --------------------------------------------------------------------------
# POST /glyph/component/remove (v0.179) - remove_component: remove components from a glyph (P2.7; the user's design of 2026-11-18,
# DECISIONS.md "removing components"). The call is the one proven with /debug/trycomponent stage=removeshape (RM 1241-1245, one
# run each): layer.removeShape(<the component from layer.shapes>, False); recursive 0 and 1 gave the same result, so False is
# always passed explicitly. layer.clearComponents() changed nothing (1246) and is never called.
# Each entry names the element by its index in layer.shapes (the numbering of get_glyph_outline's element list) and the source
# and offset expected there (dx, dy of its matrix, within 0.001; any other part of the matrix is accepted and not compared). In a
# list every index refers to the glyph as read before the call, and an index may appear once. One master only; the glyph needs a
# modern layer; autoLayer must read False (an auto layer is FontLab's to rebuild) and the recipe must be readable; a leftover
# recipe is kept and reported (recipe_kept). The other elements may be contours or components; a Power Brush or other composite
# shape that is not a component is refused (F1: the guard's full check after the write reads the legacy layer). EVERY check runs
# before the first removal, including each shape's source read again from the shape object itself.
# Removal runs from the highest index down (the lower indices do not shift), ONE removeShape per entry, and stops at the first
# exception. If FontLab changed the advance width, it is written back ONCE (width_changed_by_removal, cleanup.width_restored).
# Verified (removed) only when the re-read shows: the layer kept; exactly the elements read before minus the removed ones, in order,
# each with its kind, source, source layer and matrix; their ink boxes unchanged; the outline equal to the contours of the kept
# elements (layer.getContours() grouped by each shape's contoursCount, which must add up before the call); autoLayer and recipe
# unchanged; every component's source outline, the advance width and the glyph count unchanged. Whenever the glyph changed (also
# unconfirmed or "unknown") _guard_mark syncs and marks it, so FontLab asks to save (the user's design: as move_nodes).
# Nothing else is restored. Never called: clearComponents, removeAllShapes, decomposite, replaceShape, addShape, font.update(), save.
# --------------------------------------------------------------------------

_REMOVE_OFFSET_TOLERANCE = 0.001


def _remove_key(e):
    """What must stay the same for a kept element: kind, source, source layer and matrix."""
    return (e.get("is_component"), e.get("is_composite"), e.get("component_glyph"), e.get("component_layer"), e.get("matrix"))


def _remove_contour_counts(shapes):
    """[contoursCount of each shape] (whole numbers), or (None, sentence). Read only. Never raises."""
    counts = []
    for i, sh in enumerate(shapes):
        v, err = _tl_call(lambda s=sh: _call0(s, "contoursCount"))
        if err is not None or isinstance(v, bool) or not isinstance(v, int) or v < 0:
            return None, f"contoursCount of element {i} could not be read ({err or type(v).__name__})"
        counts.append(v)
    return counts, None


def remove_components(name, entries, form):
    """Remove the components named by `entries` ([{"index", "component", "x", "y"}]) from the glyph `name`. See the section comment.
    Never saves. Never raises out of the route's try."""
    t0 = time.perf_counter()
    base = {"open": True, "name": name, "form": form, "removed": False, "route": "modern",
            "entries": [{"index": e["index"], "component": e["component"], "x": e["x"], "y": e["y"]} for e in entries]}

    def _done(out):
        out["elapsed_seconds"] = round(time.perf_counter() - t0, 3)
        return out

    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["removed"] = False
        return _done(out)
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return _done(dict(base, reason=f"remove_component is proven only on a font with one master ({problem.split(', and a layer')[0]}): nothing was changed"))
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None:
        return _done(dict(base, reason="the glyph has no modern active layer: nothing was changed"))
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return _done(dict(base, reason=f"the glyph's elements could not be read ({tel['error']}): nothing was changed"))
    base["elements_before"] = _comp_after(tel)
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False or not isinstance(auto_before.get("recipe"), str) or auto_before["recipe"].startswith("<error"):
        return _done(dict(base, reason=(f"the glyph's layer reads autoLayer {auto_before.get('auto_layer')!r} and recipe {auto_before.get('recipe')!r}; "
                                        "remove_component needs autoLayer off and a readable recipe (an automatic layer is FontLab's to "
                                        "rebuild): nothing was changed")))
    for i, e in enumerate(tel):
        if e.get("is_component") is not True and e.get("is_composite") is not False:
            return _done(dict(base, reason=(f"element {i} is a Power Brush or other composite shape (or its kind cannot be read); "
                                            "remove_component does not change such a glyph, because the check after the write would "
                                            "read its legacy layer, which can flatten a Power Brush shape: nothing was changed")))
    for k, e in enumerate(entries):
        i = e["index"]
        label = f"entry {k} (index {i})"
        if i >= len(tel):
            return _done(dict(base, reason=f"{label}: the glyph has {len(tel)} element(s), numbered from 0: nothing was changed"))
        el = tel[i]
        if el.get("is_component") is not True:
            return _done(dict(base, reason=f"{label}: element {i} is not a component: nothing was changed"))
        if el.get("component_glyph") != e["component"]:
            return _done(dict(base, reason=(f"{label}: element {i} is a component of {el.get('component_glyph')!r}, not {e['component']!r} "
                                            "(read the glyph again with get_glyph_outline): nothing was changed")))
        m = el.get("matrix")
        if (not isinstance(m, dict) or not all(isinstance(m.get(a), float) for a in ("dx", "dy"))
                or abs(m["dx"] - float(e["x"])) > _REMOVE_OFFSET_TOLERANCE or abs(m["dy"] - float(e["y"])) > _REMOVE_OFFSET_TOLERANCE):
            found = f"({m['dx']}, {m['dy']})" if isinstance(m, dict) and all(isinstance(m.get(a), float) for a in ("dx", "dy")) else "unreadable"
            return _done(dict(base, reason=(f"{label}: the component of {e['component']!r} is at offset {found}, not ({e['x']}, {e['y']}) "
                                            "(read the glyph again with get_glyph_outline): nothing was changed")))
    boxes_before = _trycomp_all_boxes(layer)
    if isinstance(boxes_before, dict):
        return _done(dict(base, reason=f"the ink boxes of the glyph's elements could not be read ({boxes_before['error']}): nothing was changed"))
    bad_box = next((i for i, b in enumerate(boxes_before) if not isinstance(b, dict) or "error" in b), None)
    if bad_box is not None:
        why_box = boxes_before[bad_box].get("error") if isinstance(boxes_before[bad_box], dict) else type(boxes_before[bad_box]).__name__
        return _done(dict(base, reason=f"the ink box of element {bad_box} could not be read ({why_box}): nothing was changed"))
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list or len(shapes) != len(tel):
        return _done(dict(base, reason="layer.shapes is not a plain list matching the elements read: nothing was changed"))
    counts, why = _remove_contour_counts(shapes)
    if counts is None:
        return _done(dict(base, reason=f"{why}: nothing was changed"))
    snap_before = _tryedit_snapshot(name)
    if "error" in snap_before:
        return _done(dict(base, reason=f"the glyph's outline could not be read ({snap_before['error']}): nothing was changed"))
    if sum(counts) != len(snap_before["contours"]):
        return _done(dict(base, reason=(f"the elements' contour counts add up to {sum(counts)}, but the outline has "
                                        f"{len(snap_before['contours'])} contour(s), so the kept contours could not be checked: nothing was changed")))
    sources = {}
    for e in tel:
        src = e.get("component_glyph")
        if e.get("is_component") is True and src not in sources:
            snap = _tryedit_snapshot(src) if isinstance(src, str) and not src.startswith("<error") else {"error": "the source name is unreadable"}
            if "error" in snap:
                return _done(dict(base, reason=f"the outline of the component glyph {src!r} could not be read ({snap['error']}): nothing was changed"))
            sources[src] = snap
    width_before = _trycomp_width(w)
    count_before = _tryedit_glyph_count(font)
    base["advance_width_before"], base["glyph_count_before"] = width_before, count_before
    if not isinstance(width_before, float) or isinstance(count_before, str):
        return _done(dict(base, reason="the glyph's advance width or the font's glyph count could not be read: nothing was changed"))
    order = sorted((e["index"] for e in entries), reverse=True)
    for i in order:           # each shape object asked again, right before any removal
        sd, err = _tl_call(lambda s=shapes[i]: s.shapeData)
        named, err2 = (None, err or "shapeData is None") if (err is not None or sd is None) else _tl_call(lambda: _call0(sd, "componentGlyph"))
        if err2 is not None or named != tel[i].get("component_glyph"):
            return _done(dict(base, reason=(f"the shape at index {i} names {named!r}, not {tel[i].get('component_glyph')!r} as read before"
                                            if err2 is None else f"the shape at index {i} could not be checked ({err2})") + ": nothing was changed"))
    base["removal_order"] = order
    called, returned = [], []
    for i in order:
        try:
            ret = layer.removeShape(shapes[i], False)
            called.append(i)
            returned.append(ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>")
        except Exception as exc:
            base["error"] = f"layer.removeShape(element {i}, False) failed: {type(exc).__name__}: {exc}"
            base["failed_index"] = i
            break
    result = dict(base, removed_calls=list(called), calls_returned=returned)
    cleanup = {}
    width_now = _trycomp_width(w)
    if called and width_now != width_before:
        result["width_changed_by_removal"] = width_now
        try:
            w.advanceWidth = width_before
            cleanup["width_restored"] = True
        except Exception as exc:
            cleanup["width_restored"] = f"failed: {type(exc).__name__}: {exc}"
    result["cleanup"] = cleanup
    if called:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the glyph has no modern active layer after the call"}
    auto_after = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    result["auto_after"] = auto_after
    boxes2 = _trycomp_all_boxes(layer2)
    snap_after = _tryedit_snapshot(name)
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    removed_set = set(called)
    keep = [i for i in range(len(tel)) if i not in removed_set]
    starts = [sum(counts[:i]) for i in range(len(counts))]
    want_contours = [c for i in keep for c in snap_before["contours"][starts[i]:starts[i] + counts[i]]]
    checks = {
        "layer_kept": layer2 is not None,
        "elements": not isinstance(tel2, dict) and [_remove_key(e) for e in tel2] == [_remove_key(tel[i]) for i in keep],
        "ink_boxes": isinstance(boxes2, list) and boxes2 == [boxes_before[i] for i in keep],
        "outline_kept": "error" not in snap_after and snap_after["contours"] == want_contours,
        "auto_layer_and_recipe_unchanged": auto_after == auto_before,
        "sources_unchanged": all("error" not in (s2 := _tryedit_snapshot(src)) and s2["contours"] == sources[src]["contours"] for src in sources),
        "width_unchanged": width_after == width_before,
        "glyph_count_unchanged": result["glyph_count_after"] == count_before,
    }
    result["checks"] = checks
    ok = bool("error" not in result and len(called) == len(entries) and all(v is True for v in checks.values()))
    result["removed"] = ok
    result["verified"] = ok
    by_index = {}
    for i in order:
        by_index[i] = ("removed" if ok else "called, not confirmed" if i in removed_set else
                       "call failed" if i == result.get("failed_index") else "not reached")
    result["entry_states"] = [{"index": e["index"], "component": e["component"], "state": by_index[e["index"]]} for e in entries]
    result["components_after"] = _comp_after(tel2)
    result["empty_after"] = "unknown" if isinstance(tel2, dict) else len(tel2) == 0
    if auto_before.get("recipe"):
        result["recipe_kept"] = auto_after.get("recipe") if isinstance(auto_after.get("recipe"), str) else "unknown"
    result["changed"] = ("unknown" if (isinstance(tel2, dict) or "error" in snap_after) else
                         bool([_remove_key(e) for e in tel2] != [_remove_key(e) for e in tel] or snap_after["contours"] != snap_before["contours"]
                              or after_state != state or width_after != width_before or "width_changed_by_removal" in result))
    if not ok:
        failed = [k for k, v in checks.items() if v is not True]
        result["reason"] = (result.get("error") or "the re-read does not confirm the removal") + (
            ": failed checks: " + ", ".join(failed) if failed else "")
    if result["changed"] is not False:
        _guard_mark(font, name, "remove_component", result)
    return _done(result)


# --------------------------------------------------------------------------
# POST /glyph/move (v0.153) - move_nodes, the first edit of an EXISTING outline (P2.2, required by the user on 2026-11-14; research
# ED2 964-983 and B2 989-1000 with /debug/tryedit; design approved by the user on 2026-11-15). Each move names contour C and node N
# in the numbering of get_glyph_outline's modern-layer reply (layer.getContours(), getNodeAt; control points are nodes too), the
# position the node must have NOW ("from") and its new one ("to", rule B, applied by the route). The glyph must hold exactly ONE
# plain shape (isComponent False, isComposite False: no Power Brush, F1), no components, and that shape's transform must read the
# identity, so a stored node position is the position FontLab draws. EVERY check runs before the first node is touched: a "from"
# that differs from the node refuses the whole call, and so does a move that leaves a smooth on-curve node's two neighbours off one
# straight line (draw_path's 2-degree check; a smooth node that was already off it before the call does not count).
# Then node.x = to.x, node.y = to.y for every move (967), the re-read compared node by node with the expected outline (every other
# node, every kind and every smooth flag unchanged), and _guard_mark: Update(<flGlyph>), the sync check, the changed mark. By the
# user's decision the font is marked whenever the outline changed, confirmed or not, and nothing is restored automatically.
# v0.154: no refresh call any more. FontLab's own metrics (getLSB / getRSB and layer.inkBox()) lag after an API node move, and neither
# layer.resetInkBox() nor layer.update() brought them up to date in live 1003-1006 (993 and 997 did not reproduce); the "margins" in
# the reply are FontLab's values as read, and the server computes the sidebearings from the re-read nodes.
# Never called here: font.update(), save, moveBy, smartMove, smartSetXY, resetMetrics*, decomposite, ejectTo, shapeBuilder;
# no subscript or iteration of a native object.
# --------------------------------------------------------------------------

_MOVE_MAX = 200                 # moves per call
_MOVE_INDEX_MAX = 5000          # highest contour or node index accepted by the route
_MOVE_FROM_TOLERANCE = 0.001    # font units: "from" against the node's current position
_MOVE_IDENTITY = {"m11": 1.0, "m12": 0.0, "m21": 0.0, "m22": 1.0, "dx": 0.0, "dy": 0.0}


def _mv_text(v):
    """A coordinate for a message: -0.0 prints as 0 (v0.154; live 1002 printed (350, -0))."""
    return f"{float(v) + 0.0:g}"


def _move_snapshot(name):
    """{"contours": [{"closed", "nodes": [{x, y, kind, smooth}]}], "margins"?} of the modern layer, or {"error"}. Never raises."""
    modern = _read_modern_outline(name)
    if modern.get("available") is not True:
        return {"error": modern.get("error") or "the outline could not be read"}
    out = []
    for c in modern.get("contours") or []:
        out.append({"closed": c.get("closed"), "nodes": [{"x": n.get("x"), "y": n.get("y"), "kind": "On" if n.get("isOn") else (
            "Curve" if n.get("isCurve") else "Off"), "smooth": n.get("smooth")} for n in (c.get("nodes") or [])]})
    return {"contours": out}


def _move_shape_identity(shape):
    """None when the shape's transform reads the identity, otherwise the reason the glyph is refused. Never raises."""
    tr, err = _tl_call(lambda: shape.transform)
    if err is not None or tr is None:
        return f"the shape's transform could not be read ({err or 'None'}): nothing was moved"
    found = {}
    for key in _MOVE_IDENTITY:
        v, err = _tl_call(lambda k=key: _call0(tr, k))
        v = _rm_plain(v)
        if err is not None or isinstance(v, bool) or not isinstance(v, (int, float)):
            return f"the shape's transform could not be read ({key}: {err or repr(v)}): nothing was moved"
        found[key] = float(v)
    if any(abs(found[k] - want) > 1e-9 for k, want in _MOVE_IDENTITY.items()):
        return ("the glyph's shape carries an element transform (" + ", ".join(f"{k} {_mv_text(found[k])}" for k in _MOVE_IDENTITY) + "), so its stored "
                "node positions are not the positions FontLab draws; move_nodes does not support such a glyph yet: nothing was moved")
    return None


def _move_smooth_bad(nodes, closed):
    """The indices of the smooth on-curve nodes whose two neighbours do NOT lie on one straight line through them (draw_path's rule,
    _PATH_SMOOTH_TOLERANCE_DEG), a neighbour on top of the node included; the ends of an open contour count as bad when smooth."""
    import math as _math
    bad = set()
    n = len(nodes)
    limit = _math.sin(_math.radians(_PATH_SMOOTH_TOLERANCE_DEG))
    for k, nd in enumerate(nodes):
        if not (nd.get("kind") == "On" and nd.get("smooth")):
            continue
        if n < 3 or (closed is not True and k in (0, n - 1)):
            bad.add(k)
            continue
        a, b = nodes[(k - 1) % n], nodes[(k + 1) % n]
        ax, ay = a["x"] - nd["x"], a["y"] - nd["y"]
        bx, by = b["x"] - nd["x"], b["y"] - nd["y"]
        la, lb = _math.hypot(ax, ay), _math.hypot(bx, by)
        if la == 0 or lb == 0:
            bad.add(k)
            continue
        if (ax * bx + ay * by) / (la * lb) >= 0 or abs((ax * by - ay * bx) / (la * lb)) > limit:
            bad.add(k)
    return bad


def _move_compare(got, want):
    """Sentences for every difference between two snapshots: contour count, closed flags, node count, position, kind and smooth flag."""
    if len(got) != len(want):
        return [f"the layer reads {len(got)} contour(s), {len(want)} expected"]
    bad = []
    for ci, (g, e) in enumerate(zip(got, want)):
        if g.get("closed") is not e.get("closed"):
            bad.append(f"contour {ci}: closed reads {g.get('closed')!r}, expected {e.get('closed')!r}")
        gn, en = g.get("nodes") or [], e.get("nodes") or []
        if len(gn) != len(en):
            bad.append(f"contour {ci}: {len(gn)} nodes read, {len(en)} expected")
            continue
        for ni, (a, b) in enumerate(zip(gn, en)):
            if abs(a["x"] - b["x"]) > 0.001 or abs(a["y"] - b["y"]) > 0.001:
                bad.append(f"contour {ci} node {ni}: position ({a['x']}, {a['y']}) instead of ({b['x']}, {b['y']})")
            if a.get("kind") != b.get("kind"):
                bad.append(f"contour {ci} node {ni}: kind {a.get('kind')} instead of {b.get('kind')}")
            if bool(a.get("smooth")) != bool(b.get("smooth")):
                bad.append(f"contour {ci} node {ni}: smooth reads {a.get('smooth')!r}, was {b.get('smooth')!r}")
    return bad


def move_nodes(name, moves, rounded=None):
    """Move existing nodes of ONE plain glyph. `moves`: dicts {contour, node, from: (x, y), to: (x, y)} with whole-number "to" (rule B
    was applied by the route), no node twice. Every check runs before anything is touched; see the section comment. Never saves."""
    base = {"open": True, "name": name, "moved": False, "route": "modern", "moves_requested": len(moves),
            "coordinates_rounded": list(rounded) if rounded else []}
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["moved"] = False
        return out
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None:
        return dict(base, reason="the glyph has no modern active layer: nothing was moved")
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list:
        return dict(base, reason=f"layer.shapes is not a plain list ({err or type(shapes).__name__}): nothing was moved")
    if len(shapes) != 1:
        return dict(base, shapes=len(shapes), reason=(f"the glyph has {len(shapes)} shapes; move_nodes edits a glyph with exactly one plain "
                                                       "shape (several shapes are not supported yet): nothing was moved"))
    shape = shapes[0]
    for attr in ("isComponent", "isComposite"):
        v, err = _tl_call(lambda a=attr: _call0(shape, a))
        if err is not None or v is not False:
            return dict(base, reason=(f"the shape's {attr} reads {v!r}{' (' + err + ')' if err else ''}: only a plain shape is edited, never a "
                                      "component or a Power Brush or other composite shape: nothing was moved"))
    if _state_has_components(state):
        return dict(base, reason=f"the layer reads {_state_components_text(state)}: nothing was moved")
    why = _move_shape_identity(shape)
    if why is not None:
        return dict(base, reason=why)
    before = _move_snapshot(name)
    if "error" in before:
        return dict(base, reason=f"the outline could not be read before the move ({before['error']}): nothing was moved")
    contours, err = _tl_call(lambda: layer.getContours())
    if err is not None or type(contours) not in (list, tuple):
        return dict(base, reason=f"layer.getContours() is not a plain list ({err or type(contours).__name__}): nothing was moved")
    if len(contours) != len(before["contours"]):
        return dict(base, reason="layer.getContours() disagrees with the outline just read: nothing was moved")
    want = [dict(c, nodes=[dict(n) for n in c["nodes"]]) for c in before["contours"]]
    problems = []
    for i, mv in enumerate(moves):
        ci, ni = mv["contour"], mv["node"]
        if ci >= len(before["contours"]):
            problems.append(f"move {i}: contour {ci} does not exist (the glyph has {len(before['contours'])})")
            continue
        nodes = before["contours"][ci]["nodes"]
        if ni >= len(nodes):
            problems.append(f"move {i}: node {ni} does not exist (contour {ci} has {len(nodes)})")
            continue
        cur = nodes[ni]
        fx, fy = mv["from"]
        if abs(cur["x"] - fx) > _MOVE_FROM_TOLERANCE or abs(cur["y"] - fy) > _MOVE_FROM_TOLERANCE:
            problems.append(f"move {i}: contour {ci} node {ni} is at ({_mv_text(cur['x'])}, {_mv_text(cur['y'])}), not at the given from ({_mv_text(fx)}, {_mv_text(fy)})")
            continue
        want[ci]["nodes"][ni]["x"], want[ci]["nodes"][ni]["y"] = float(mv["to"][0]), float(mv["to"][1])
    if problems:
        return dict(base, problems=problems[:20], reason="the request does not match the glyph as it is now, nothing was moved: " + " | ".join(problems[:6]))
    for ci in sorted({mv["contour"] for mv in moves}):
        old_bad = _move_smooth_bad(before["contours"][ci]["nodes"], before["contours"][ci]["closed"])
        for k in sorted(_move_smooth_bad(want[ci]["nodes"], want[ci]["closed"]) - old_bad):
            nd = want[ci]["nodes"][k]
            problems.append(f"contour {ci} node {k}, a smooth node (at ({_mv_text(nd['x'])}, {_mv_text(nd['y'])}) after the moves), would have its two neighbours "
                            f"off one straight line through it (more than {_PATH_SMOOTH_TOLERANCE_DEG:g} degrees): move the node and its "
                            "neighbours together in the same call")
    if problems:
        return dict(base, problems=problems[:20], reason="the moves would break a smooth node, nothing was moved: " + " | ".join(problems[:6]))
    natives = []
    for i, mv in enumerate(moves):
        ci, ni = mv["contour"], mv["node"]
        target = contours[ci]
        count, err = _tl_call(lambda: _call0(target, "nodesCount"))
        if err is not None or not isinstance(count, int) or isinstance(count, bool) or count != len(before["contours"][ci]["nodes"]):
            return dict(base, reason=f"move {i}: nodesCount of contour {ci} reads {count!r}{' (' + err + ')' if err else ''}, not the count just read: nothing was moved")
        nd, err = _tl_call(lambda: target.getNodeAt(ni))
        if err is not None or nd is None:
            return dict(base, reason=f"move {i}: getNodeAt({ni}) failed ({err or 'returned None'}): nothing was moved")
        x0, ex = _tl_call(lambda: _rm_plain(_call0(nd, "x")))
        y0, ey = _tl_call(lambda: _rm_plain(_call0(nd, "y")))
        if ex is not None or ey is not None or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x0, y0)) or (
                abs(x0 - mv["from"][0]) > _MOVE_FROM_TOLERANCE or abs(y0 - mv["from"][1]) > _MOVE_FROM_TOLERANCE):
            return dict(base, reason=f"move {i}: the node object reads ({x0!r}, {y0!r}), not the given from: nothing was moved")
        natives.append((i, nd, mv["to"]))
    touched, step = False, "the first move"
    try:
        for i, nd, (tx, ty) in natives:
            step, touched = f"move {i}: node.x = {_mv_text(tx)}", True
            nd.x = float(tx)
            step = f"move {i}: node.y = {_mv_text(ty)}"
            nd.y = float(ty)
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    if touched:
        result["display_refreshed"] = _repaint_viewport()
        result["display_note"] = _DISPLAY_NOTE
    after_state, _l = _tryshape_modern_state(w)
    result["state_after"] = after_state
    after = _move_snapshot(name)
    if "error" in after:
        result["changed"] = "unknown" if touched else False
        result["mismatches"] = [f"the outline could not be read after the move ({after['error']})"]
    else:
        result["after"] = after["contours"]
        result["changed"] = after["contours"] != before["contours"]
        result["mismatches"] = _move_compare(after["contours"], want)
        if after_state.get("shapes") != 1:
            result["mismatches"].append(f"the layer reads {after_state.get('shapes')!r} shapes after the move, 1 expected")
    result["nodes_match"] = not result["mismatches"] and "error" not in result
    result["moved"] = bool(result["nodes_match"])
    if not result["moved"]:
        result["before"] = before["contours"]
        result["expected_after"] = want
        why = result.get("error") or "the re-read outline does not match the request"
        result["reason"] = why + (": " + " | ".join(result["mismatches"][:6]) if result["mismatches"] else "")
    if result["changed"] is not False:
        _guard_mark(font, name, "move_nodes", result, no_mark=None)
    if ctx["tr"] is not None:
        m, _err = _modern_margins_read(w, ctx["tr"])
        if m is not None:
            result["margins"] = m
            result["ink_width"] = m["advance"] - m["lsb"] - m["rsb"]
    return result


# --------------------------------------------------------------------------
# POST /glyph/component (v0.169) - add_component: ONE component into an existing, EMPTY glyph layer (P2.7; design of the user, 2026-11-17,
# DECISIONS.md "add_component, version 1"). The route is the one proven with /debug/trycomponent, one live run per step: layer.recipe =
# <source> (1039), layer.autoLayer = True (1041a), ONE layer.buildAuto() that must return True (1041b), layer.autoLayer = False (1042),
# shape.transform = QTransform(1, 0, 0, 1, x, y) only for an offset (1043), layer.recipe = "" (1058). One master only; the source holds
# only plain shapes (no component, no Power Brush or other composite shape) and at least one node; the target exists, has a layer, and
# that layer holds nothing, with autoLayer off. EVERY check runs before the first write.
# Verified (placed) only when the re-read shows exactly one element, a component of the source on the source's layer, matrix
# (1, 0, 0, 1, x, y), its inkBox() equal to the source's ink box moved by (x, y), recipe "" and autoLayer False, and the source's
# outline, the target's advance width and the glyph count unchanged. Then _guard_mark (Update, sync check, the changed mark).
# After a failure once autoLayer was set True, ONE autoLayer = False (the user's choice), read back; nothing else is restored, and
# nothing is marked. v0.178: as in the list form, a leftover recipe is also cleared, and whenever the recipe was set the width is
# read and, if FontLab's build changed it, written back (width_set_by_build, cleanup); "width unchanged" is checked after that. Never called: setGlyphComponents, addComponent, killAuto, decomposite, font.update(), save; no subscript or
# iteration of a native object (layer.shapes and the box rows are real lists).
# --------------------------------------------------------------------------

_COMP_OFFSET_MAX = 10000


def _comp_union_box(rows):
    """{left, right, top, bottom} over the ink boxes of `rows` (_tryshapebox_boxes), or None when one is not a plain box."""
    boxes = [r.get("ink_box") for r in rows]
    keys = ("left", "right", "top", "bottom")
    if not boxes or any(not isinstance(b, dict) or "error" in b or any(k not in b for k in keys) for b in boxes):
        return None
    return {"left": min(b["left"] for b in boxes), "right": max(b["right"] for b in boxes),
            "top": min(b["top"] for b in boxes), "bottom": max(b["bottom"] for b in boxes)}


def _comp_box_at(box, want):
    """True / False when `box` (one element's ink box) equals `want` within 0.001 on its four edges; "unknown" when unreadable."""
    keys = ("left", "right", "top", "bottom")
    if not isinstance(box, dict) or "error" in box or any(k not in box for k in keys) or want is None:
        return "unknown"
    return all(abs(box[k] - want[k]) <= 0.001 for k in keys)


def add_component(name, component, x, y):
    """Place the glyph `component` as ONE component in the empty glyph `name` at offset (x, y), whole units. See the section comment.
    Never saves."""
    base = {"open": True, "name": name, "component": component, "x": x, "y": y, "placed": False, "route": "modern"}
    if name == component:
        return dict(base, reason="a glyph cannot hold itself as a component: nothing was changed")
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["placed"] = False
        return out
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return dict(base, reason=f"add_component is proven only on a font with one master ({problem.split(', and a layer')[0]}): nothing was changed")
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None:
        return dict(base, reason="the glyph has no modern active layer: nothing was changed")
    why = _comp_one_layer_problem(w, state)      # v0.187: both routes, before the route is chosen (NB 1353)
    if why is not None:
        return dict(base, reason=why)
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, reason=f"the glyph's elements could not be read ({tel['error']}): nothing was changed")
    if tel:      # v0.186: a glyph that is not empty gets the temporary-layer route
        return _add_beside(base, name, ctx, state, layer, tel, [{"component": component, "x": x, "y": y}])
    if state.get("shapes") != 0 or _state_has_components(state):
        return dict(base, reason=("the glyph reads no element, but its shape or component count is not 0, so whether it is empty cannot be "
                                  "told: nothing was changed"))
    base["placement"] = "empty layer"     # v0.186
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False or str(auto_before.get("recipe")).startswith("<error"):
        return dict(base, reason=(f"the glyph's layer reads autoLayer {auto_before.get('auto_layer')!r} and recipe {auto_before.get('recipe')!r}; "
                                  "add_component needs a readable recipe and autoLayer off: nothing was changed"))
    # the source: plain shapes only, at least one node
    sctx, srefusal = _modern_edit_target(component)
    if sctx is None:
        out = _public_refusal(srefusal)
        why = out.get("reason") or "the glyph cannot be used"
        return dict(base, component_found=out.get("found", "unknown"), reason=f"the component glyph {component!r} cannot be used: {why}: nothing was changed")
    sstate, slayer = _tryshape_modern_state(sctx["w"])
    if slayer is None:
        return dict(base, reason=f"the component glyph {component!r} has no modern active layer: nothing was changed")
    sel = _trycomp_elements(slayer)
    if isinstance(sel, dict):
        return dict(base, reason=f"the elements of {component!r} could not be read ({sel['error']}): nothing was changed")
    snodes = sstate.get("nodes")
    if (not sel or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in sel)
            or _state_has_components(sstate) or not isinstance(snodes, int) or isinstance(snodes, bool) or snodes < 1):
        return dict(base, reason=(f"the component glyph {component!r} must hold only plain contours (no component, no Power Brush or other "
                                  "composite shape) and at least one node: nothing was changed"))
    source_layer = sstate.get("layer_name")
    src_rows, why = _tryshapebox_boxes(slayer)
    src_box = _comp_union_box(src_rows) if src_rows is not None else None
    if src_box is None:
        return dict(base, reason=f"the ink box of {component!r} could not be read ({why or 'an element box is not a plain box'}): nothing was changed")
    src_before = _tryedit_snapshot(component)
    if "error" in src_before:
        return dict(base, reason=f"the outline of {component!r} could not be read ({src_before['error']}): nothing was changed")
    width_before = _trycomp_width(w)
    count_before = _tryedit_glyph_count(font)
    base["advance_width_before"], base["glyph_count_before"] = width_before, count_before
    if not isinstance(width_before, float) or isinstance(count_before, str):
        return dict(base, reason="the glyph's advance width or the font's glyph count could not be read: nothing was changed")
    qt_cls = None
    if (x, y) != (0, 0):
        import sys as _sys
        qt_cls, qt_src = _trycomp_qtransform_class(_sys.modules.get("fontlab") or fl)
        if qt_cls is None:
            return dict(base, reason=f"{qt_src}: nothing was changed")
    want_box = {"left": src_box["left"] + x, "right": src_box["right"] + x, "top": src_box["top"] + y, "bottom": src_box["bottom"] + y}
    done, step = [], "layer.recipe = component"
    try:
        layer.recipe = component
        done.append("recipe")
        step = "layer.autoLayer = True"
        layer.autoLayer = True
        done.append("auto_on")
        step = "layer.buildAuto()"
        ret = layer.buildAuto()
        done.append("build")
        base["build_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        if ret is not True:
            raise RuntimeError(f"it returned {base['build_returned']!r}, not True")
        step = "layer.autoLayer = False"
        layer.autoLayer = False
        done.append("auto_off")
        if (x, y) != (0, 0):
            step = "reading the placed component"
            shapes, err = _tl_call(lambda: layer.shapes)
            if err is not None or type(shapes) is not list or len(shapes) != 1:
                raise RuntimeError(f"layer.shapes is not a plain list of one element ({err or (len(shapes) if type(shapes) is list else type(shapes).__name__)})")
            step = "shape.transform = QTransform(1, 0, 0, 1, x, y)"
            shapes[0].transform = qt_cls(1.0, 0.0, 0.0, 1.0, float(x), float(y))
            done.append("offset")
        step = 'layer.recipe = ""'
        layer.recipe = ""
        done.append("recipe_cleared")
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base, steps_done=list(done))
    # v0.178: the list form's clean-up (the tool's description promised the width written back for both forms): autoLayer off if still
    # on, a leftover recipe cleared, and the width written back when FontLab's build changed it (live 1250: 500 -> 0, one run)
    cleanup = {}
    if "auto_on" in done and "auto_off" not in done:        # the user's choice: never leave a locked auto layer behind
        try:
            layer.autoLayer = False
            cleanup["auto_layer_set_back"] = True
        except Exception as exc:
            cleanup["auto_layer_set_back"] = f"failed: {type(exc).__name__}: {exc}"
    if "recipe" in done and "recipe_cleared" not in done:
        try:
            layer.recipe = ""
            cleanup["recipe_cleared"] = True
        except Exception as exc:
            cleanup["recipe_cleared"] = f"failed: {type(exc).__name__}: {exc}"
    width_now = _trycomp_width(w)
    if "recipe" in done and width_now != width_before:
        result["width_set_by_build"] = width_now
        try:
            w.advanceWidth = width_before
            cleanup["width_restored"] = True
        except Exception as exc:
            cleanup["width_restored"] = f"failed: {type(exc).__name__}: {exc}"
    result["cleanup"] = cleanup
    if done:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the glyph has no modern active layer after the call"}
    result["elements_after"] = tel2
    auto_after = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    result["auto_after"] = auto_after
    box_after = _trycomp_first_box(layer2)
    result["ink_box"] = box_after
    result["ink_box_expected"] = want_box
    src_after = _tryedit_snapshot(component)
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    checks = {
        "one_component": (not isinstance(tel2, dict) and len(tel2) == 1 and tel2[0].get("is_component") is True
                          and tel2[0].get("component_glyph") == component),
        "source_layer": not isinstance(tel2, dict) and len(tel2) == 1 and tel2[0].get("component_layer") == source_layer,    # v0.187
        "offset": not isinstance(tel2, dict) and len(tel2) == 1 and _trycomp_offset_ok(tel2[0].get("matrix"), x, y),
        "ink_box": _comp_box_at(box_after, want_box) is True,
        "recipe_cleared": auto_after.get("recipe") == "",
        "auto_layer_off": auto_after.get("auto_layer") is False,
        "source_unchanged": "error" not in src_after and src_after["contours"] == src_before["contours"],
        "width_unchanged": width_after == width_before,
        "glyph_count_unchanged": result["glyph_count_after"] == count_before,
    }
    result["checks"] = checks
    result["placed"] = bool("error" not in result and all(v is True for v in checks.values()))
    result["verified"] = result["placed"]
    result["changed"] = ("unknown" if (isinstance(tel2, dict) or "error" in auto_after) else
                         bool(tel2 or after_state != state or auto_after != auto_before))
    if not result["placed"]:
        failed = [k for k, v in checks.items() if v is not True]
        result["reason"] = (result.get("error") or "the re-read does not confirm the component") + (
            ": failed checks: " + ", ".join(failed) if failed else "")
    if result["changed"] is not False:
        _guard_mark(font, name, "add_component", result, no_mark=None if result["placed"] else "the component was not confirmed")
    return result


# --------------------------------------------------------------------------
# POST /glyph/component with "components" (v0.174) - add_component, several components in ONE call (P2.7; the user's design of
# 2026-11-17, DECISIONS.md "add_component, several components"). The single form above is untouched. Route proven with the probe
# (PC2 / PC3 1102-1177): layer.recipe = "<a>+<b>+..." (repeats allowed, 1172), layer.autoLayer = True, ONE layer.buildAuto() that must
# return True, layer.autoLayer = False; FontLab places the first glyph at identity and moves each later one itself (ink centre onto 0)
# and sets the width to 500; then each element must name its entry's source, in list order (checked before any offset is set), and each
# element whose matrix is not its entry's offset gets ONE shape.transform = QTransform(1, 0, 0, 1, x, y).
# Clean-up, always (also after a failure, then placing stops at the first failure): autoLayer = False if it is still on,
# layer.recipe = "", the advance width written back to its value before the call. Nothing else is restored.
# More than _COMP_SOFT_LIMIT entries (30: tested 2-5, 15, 30) need confirmed_untested_size true; without it nothing is touched.
# Verified (placed) only when the re-read shows: the element count, each element a component of its entry's source on that source's
# layer at (x, y), its inkBox() equal to the source's ink box moved by (x, y), recipe "" and autoLayer False, every source's outline,
# the advance width and the glyph count unchanged. Then _guard_mark. Never called: setGlyphComponents, addComponent, killAuto,
# decomposite, font.update(), save.
# v0.175: a list with a source name holding "_" is refused before anything is read or touched (FontLab's recipe of several glyphs
# reads "a_b" as a ligature of a and b: AC2u 1216-1235). component_states: "not reached" only where buildAuto() was never called;
# on a wrong element count each entry is matched to an element of its source, in list order, each element once ("left by the
# build" / "missing after the build"). A failure reply also gives components_after, what the glyph holds.
# --------------------------------------------------------------------------

_COMP_SOFT_LIMIT = 30
_COMP_UNTESTED_NOTE = ("only up to 30 components in one call have been tested; anything above is unknown territory")


def add_components(name, entries, confirmed):
    """Place several components (entries: [{"component", "x", "y"}], in order) into the empty glyph `name`. See the section comment.
    Never saves. Never raises."""
    t0 = time.perf_counter()
    base = {"open": True, "name": name, "form": "list", "component_count": len(entries),
            "components": [{"component": e["component"], "x": e["x"], "y": e["y"]} for e in entries], "placed": False, "route": "modern"}

    def _done(out):
        out["elapsed_seconds"] = round(time.perf_counter() - t0, 3)
        return out

    names = [e["component"] for e in entries]
    under = [i for i, n in enumerate(names) if "_" in n]
    if under:       # v0.175: FontLab's recipe of several glyphs reads "a_b" as a ligature of a and b (AC2u 1216-1235, 1234)
        return _done(dict(base, underscore_refused=True, reason=(
            f"components[{under[0]}] {names[under[0]]!r} has an underscore, which FontLab's recipe build of several glyphs reads as a "
            "ligature of its parts (it drops the glyph or places the parts instead); the single form places such a glyph alone into an "
            "empty glyph: nothing was changed")))
    if len(entries) > _COMP_SOFT_LIMIT:
        base["untested_size_note"] = _COMP_UNTESTED_NOTE
        if confirmed is not True:
            return _done(dict(base, untested_size=True, reason=(f"{len(entries)} components: {_COMP_UNTESTED_NOTE}; the person must agree "
                                                               "first (confirmed_untested_size): nothing was changed")))
    if name in names:
        return _done(dict(base, reason="a glyph cannot hold itself as a component: nothing was changed"))
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        out = _public_refusal(refusal)
        out.pop("set", None)
        out["placed"] = False
        return _done(out)
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return _done(dict(base, reason=f"add_component is proven only on a font with one master ({problem.split(', and a layer')[0]}): nothing was changed"))
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None:
        return _done(dict(base, reason="the glyph has no modern active layer: nothing was changed"))
    why = _comp_one_layer_problem(w, state)      # v0.187: both routes, before the route is chosen (NB 1353)
    if why is not None:
        return _done(dict(base, reason=why))
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return _done(dict(base, reason=f"the glyph's elements could not be read ({tel['error']}): nothing was changed"))
    if tel:      # v0.186: a glyph that is not empty gets the temporary-layer route
        return _done(_add_beside(base, name, ctx, state, layer, tel, entries))
    if state.get("shapes") != 0 or _state_has_components(state):
        return _done(dict(base, reason=("the glyph reads no element, but its shape or component count is not 0, so whether it is empty "
                                        "cannot be told: nothing was changed")))
    base["placement"] = "empty layer"     # v0.186
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False or str(auto_before.get("recipe")).startswith("<error"):
        return _done(dict(base, reason=(f"the glyph's layer reads autoLayer {auto_before.get('auto_layer')!r} and recipe {auto_before.get('recipe')!r}; "
                                        "add_component needs a readable recipe and autoLayer off: nothing was changed")))
    sources = {}      # each distinct source, checked once, in list order
    for src in dict.fromkeys(names):
        sctx, srefusal = _modern_edit_target(src)
        if sctx is None:
            out = _public_refusal(srefusal)
            why = out.get("reason") or "the glyph cannot be used"
            return _done(dict(base, component_found=out.get("found", "unknown"),
                              reason=f"the component glyph {src!r} cannot be used: {why}: nothing was changed"))
        sstate, slayer = _tryshape_modern_state(sctx["w"])
        if slayer is None:
            return _done(dict(base, reason=f"the component glyph {src!r} has no modern active layer: nothing was changed"))
        sel = _trycomp_elements(slayer)
        if isinstance(sel, dict):
            return _done(dict(base, reason=f"the elements of {src!r} could not be read ({sel['error']}): nothing was changed"))
        snodes = sstate.get("nodes")
        if (not sel or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in sel)
                or _state_has_components(sstate) or not isinstance(snodes, int) or isinstance(snodes, bool) or snodes < 1):
            return _done(dict(base, reason=(f"the component glyph {src!r} must hold only plain contours (no component, no Power Brush or other "
                                            "composite shape) and at least one node: nothing was changed")))
        src_rows, why = _tryshapebox_boxes(slayer)
        src_box = _comp_union_box(src_rows) if src_rows is not None else None
        if src_box is None:
            return _done(dict(base, reason=f"the ink box of {src!r} could not be read ({why or 'an element box is not a plain box'}): nothing was changed"))
        snap = _tryedit_snapshot(src)
        if "error" in snap:
            return _done(dict(base, reason=f"the outline of {src!r} could not be read ({snap['error']}): nothing was changed"))
        sources[src] = {"layer": sstate.get("layer_name"), "box": src_box, "snapshot": snap}
    width_before = _trycomp_width(w)
    count_before = _tryedit_glyph_count(font)
    base["advance_width_before"], base["glyph_count_before"] = width_before, count_before
    if not isinstance(width_before, float) or isinstance(count_before, str):
        return _done(dict(base, reason="the glyph's advance width or the font's glyph count could not be read: nothing was changed"))
    import sys as _sys
    qt_cls, qt_src = _trycomp_qtransform_class(_sys.modules.get("fontlab") or fl)
    if qt_cls is None:
        return _done(dict(base, reason=f"{qt_src}: nothing was changed"))
    wants = [{"left": sources[e["component"]]["box"]["left"] + e["x"], "right": sources[e["component"]]["box"]["right"] + e["x"],
              "top": sources[e["component"]]["box"]["top"] + e["y"], "bottom": sources[e["component"]]["box"]["bottom"] + e["y"]}
             for e in entries]
    done, step = [], "layer.recipe = the components joined by +"
    try:
        layer.recipe = "+".join(names)
        done.append("recipe")
        step = "layer.autoLayer = True"
        layer.autoLayer = True
        done.append("auto_on")
        step = "layer.buildAuto()"
        t_build = time.perf_counter()
        ret = layer.buildAuto()
        base["build_seconds"] = round(time.perf_counter() - t_build, 3)
        done.append("build")
        base["build_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        if ret is not True:
            raise RuntimeError(f"it returned {base['build_returned']!r}, not True")
        step = "layer.autoLayer = False"
        layer.autoLayer = False
        done.append("auto_off")
        step = "checking the built components against the list"
        built = _trycomp_elements(layer)
        shapes, err = _tl_call(lambda: layer.shapes)
        if isinstance(built, dict) or err is not None or type(shapes) is not list or len(shapes) != len(entries) or len(built) != len(entries):
            raise RuntimeError(f"the layer does not hold {len(entries)} elements as a plain list after the build")
        wrong = [i for i, e in enumerate(built) if e.get("is_component") is not True or e.get("component_glyph") != names[i]]
        if wrong:
            raise RuntimeError(f"the built components are not the list in order (first difference at position {wrong[0]}: "
                               f"{built[wrong[0]].get('component_glyph')!r}, not {names[wrong[0]]!r})")
        done.append("order_checked")
        for i, e in enumerate(entries):
            if _trycomp_offset_ok(built[i].get("matrix"), e["x"], e["y"]):
                continue
            step = f"shape.transform = QTransform(1, 0, 0, 1, x, y) on component {i}"
            shapes[i].transform = qt_cls(1.0, 0.0, 0.0, 1.0, float(e["x"]), float(e["y"]))
        done.append("offsets")
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base, steps_done=list(done))
    cleanup = {}
    if "auto_on" in done and "auto_off" not in done:        # never leave a locked auto layer behind
        try:
            layer.autoLayer = False
            cleanup["auto_layer_set_back"] = True
        except Exception as exc:
            cleanup["auto_layer_set_back"] = f"failed: {type(exc).__name__}: {exc}"
    if "recipe" in done:
        try:
            layer.recipe = ""
            cleanup["recipe_cleared"] = True
        except Exception as exc:
            cleanup["recipe_cleared"] = f"failed: {type(exc).__name__}: {exc}"
    width_now = _trycomp_width(w)
    if "recipe" in done and width_now != width_before:
        result["width_set_by_build"] = width_now      # v0.178: what FontLab's build left, before the write-back
        try:
            w.advanceWidth = width_before
            cleanup["width_restored"] = True
        except Exception as exc:
            cleanup["width_restored"] = f"failed: {type(exc).__name__}: {exc}"
    result["cleanup"] = cleanup
    if done:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the glyph has no modern active layer after the call"}
    result["elements_after"] = tel2
    auto_after = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    result["auto_after"] = auto_after
    rows2, why2 = _tryshapebox_boxes(layer2) if layer2 is not None else (None, "no layer")
    boxes2 = [r["ink_box"] for r in rows2] if rows2 is not None else None
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    same_count = not isinstance(tel2, dict) and len(tel2) == len(entries)
    build_ran = "auto_on" in done      # buildAuto() is called right after autoLayer = True
    used = set()        # v0.175: on a wrong element count each entry is matched by source name, in list order, each element once
    per = []
    for i, e in enumerate(entries):
        if same_count:
            el = tel2[i]
            src_ok = bool(el.get("is_component") is True and el.get("component_glyph") == e["component"]
                          and el.get("component_layer") == sources[e["component"]]["layer"])
            off_ok = _trycomp_offset_ok(el.get("matrix"), e["x"], e["y"])
            box_ok = boxes2 is not None and len(boxes2) == len(entries) and _comp_box_at(boxes2[i], wants[i]) is True
            state_i = ("placed" if (src_ok and off_ok and box_ok) else "not reached" if not build_ran else
                       "at FontLab's position" if (src_ok and not off_ok) else "unknown")
        else:
            el = None
            if not build_ran:
                state_i = "not reached"
            elif isinstance(tel2, dict):
                state_i = "unknown"
            else:
                j = next((k for k, x in enumerate(tel2) if k not in used and x.get("is_component") is True
                          and x.get("component_glyph") == e["component"]), None)
                if j is None:
                    state_i = "missing after the build"
                else:
                    used.add(j)
                    el = tel2[j]
                    state_i = "left by the build"
        per.append({"component": e["component"], "x": e["x"], "y": e["y"], "state": state_i,
                    "matrix": el.get("matrix") if el else None})
    result["component_states"] = per
    checks = {
        "element_count": same_count,
        "components": same_count and all(p["state"] == "placed" for p in per),
        "recipe_cleared": auto_after.get("recipe") == "",
        "auto_layer_off": auto_after.get("auto_layer") is False,
        "sources_unchanged": all("error" not in (s2 := _tryedit_snapshot(src)) and s2["contours"] == sources[src]["snapshot"]["contours"]
                                 for src in sources),
        "width_unchanged": width_after == width_before,
        "glyph_count_unchanged": result["glyph_count_after"] == count_before,
    }
    if boxes2 is None:
        result["ink_boxes_error"] = why2
    result["checks"] = checks
    result["placed"] = bool("error" not in result and all(v is True for v in checks.values()))
    result["verified"] = result["placed"]
    result["changed"] = ("unknown" if (isinstance(tel2, dict) or "error" in auto_after) else
                         bool(tel2 or after_state != state or auto_after != auto_before or width_after != width_before))
    if not result["placed"]:
        failed = [k for k, v in checks.items() if v is not True]
        result["reason"] = (result.get("error") or "the re-read does not confirm the components") + (
            ": failed checks: " + ", ".join(failed) if failed else "")
        result["components_after"] = _comp_after(tel2)       # v0.175: what the glyph holds after the call
    if result["changed"] is not False:
        _guard_mark(font, name, "add_component", result, no_mark=None if result["placed"] else "the components were not confirmed")
    return _done(result)


def _comp_after(tel):
    """What a glyph holds, from _trycomp_elements: per element {"component", "x", "y", "plain_offset"}, "not a component" or
    "unreadable"; {"error"} when the elements could not be read (v0.175). Read only. Never raises."""
    if isinstance(tel, dict):
        return {"error": str(tel.get("error") or "the elements could not be read")}
    out = []
    for el in tel:
        g, m = el.get("component_glyph"), el.get("matrix")
        if el.get("is_component") is False:
            out.append("not a component")
        elif el.get("is_component") is not True or not isinstance(g, str) or g.startswith("<error"):
            out.append("unreadable")
        elif isinstance(m, dict) and all(isinstance(m.get(k), float) for k in _TRYCOMP_MATRIX_KEYS):
            out.append({"component": g, "x": m["dx"], "y": m["dy"],
                        "plain_offset": all(abs(m[k] - v) <= 0.001 for k, v in zip(_TRYCOMP_MATRIX_KEYS[:4], (1.0, 0.0, 0.0, 1.0)))})
        else:
            out.append({"component": g, "offset": "unreadable"})
    return out


# --------------------------------------------------------------------------
# add_component into a glyph that is NOT empty (v0.186; the user's design of 2026-11-18, DECISIONS.md): both forms, through the
# temporary-layer route proven with /debug/trycomponent stage=templayer (TL 1272-1300, PB 1331-1343), all inside this ONE request:
#   w.addLayer(flLayer(_TL_TEMP_NAME)); working_layer.setActive() when addLayer made the new layer the active one (1272); on the
#   temporary layer: recipe = "<a>+<b>+...", autoLayer = True, ONE buildAuto() that must return True, autoLayer = False, the built
#   components checked against the list in order; for each one the offset (shape.transform = QTransform(1, 0, 0, 1, x, y)) where it is
#   not the entry's, and shapeData.componentLayer = its source's layer name (the build names the temporary layer, 1283a; 1297);
#   recipe = ""; then working_layer.addShape(<each component>) in list order (1277, 1298); then w.removeLayer(<the temporary layer>)
#   (1278, 1299); the advance width written back if FontLab changed it.
# Checks before the first write: one master (the caller); the glyph has exactly ONE layer, the active one, autoLayer off and a readable
# recipe; every element is a plain contour shape, a component, or a Power Brush / other composite shape (never given an inkBox() call,
# F1); the sources as in the list form. Verified (placed) only when the re-read shows the one working layer, active; the elements
# before the call unchanged and first, then exactly the listed components in order, each naming its source and the source's layer, at
# its offset, drawn where the source's box moved by the offset says; the old contours held; autoLayer and recipe as before; every
# source, the advance width and the glyph count unchanged. Then _guard_mark with the FULL check (the user's choice, PB 1338-1345).
# A failure partway RESTORES the glyph (the user's choice): every component the call added to the working layer is removed with
# layer.removeShape(<it>, False) (RM 1241-1245, remove_component), the working layer made active, the temporary layer removed, the
# width written back; a re-read reports whether the glyph is as before (restore.restored). Never called: font.update(), save,
# decomposite, killAuto, setGlyphComponents, addComponent.
# --------------------------------------------------------------------------

def _comp_sources(names):
    """v0.186: the source checks of the list form for each distinct name, in list order. ({name: {"layer", "box", "snapshot"}}, None),
    or (None, (component_found, reason)). Read only. Never raises."""
    sources = {}
    for src in dict.fromkeys(names):
        sctx, srefusal = _modern_edit_target(src)
        if sctx is None:
            out = _public_refusal(srefusal)
            why = out.get("reason") or "the glyph cannot be used"
            return None, (out.get("found", "unknown"), f"the component glyph {src!r} cannot be used: {why}: nothing was changed")
        sstate, slayer = _tryshape_modern_state(sctx["w"])
        if slayer is None:
            return None, (True, f"the component glyph {src!r} has no modern active layer: nothing was changed")
        sel = _trycomp_elements(slayer)
        if isinstance(sel, dict):
            return None, (True, f"the elements of {src!r} could not be read ({sel['error']}): nothing was changed")
        snodes = sstate.get("nodes")
        if (not sel or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in sel)
                or _state_has_components(sstate) or not isinstance(snodes, int) or isinstance(snodes, bool) or snodes < 1):
            return None, (True, f"the component glyph {src!r} must hold only plain contours (no component, no Power Brush or other "
                                "composite shape) and at least one node: nothing was changed")
        src_rows, why = _tryshapebox_boxes(slayer)
        src_box = _comp_union_box(src_rows) if src_rows is not None else None
        if src_box is None:
            return None, (True, f"the ink box of {src!r} could not be read ({why or 'an element box is not a plain box'}): nothing was changed")
        snap = _tryedit_snapshot(src)
        if "error" in snap:
            return None, (True, f"the outline of {src!r} could not be read ({snap['error']}): nothing was changed")
        sources[src] = {"layer": sstate.get("layer_name"), "box": src_box, "snapshot": snap}
    return sources, None


def _beside_layers(w, working_name):
    """(all layer names, the working layer object or None, the temporary layer object or None, the active layer name), or None when
    w.layers cannot be read. Read only. Never raises."""
    lays = _tl_layers(w)
    if isinstance(lays, dict):
        return None
    works = [e for e in lays if e["name"] == working_name]
    temps = [e for e in lays if e["name"] == _TL_TEMP_NAME]
    st, _a = _tryshape_modern_state(w)
    return ([e["name"] for e in lays], works[0]["layer"] if len(works) == 1 else None, temps[0]["layer"] if len(temps) == 1 else None,
            st.get("layer_name"))


def _comp_one_layer_problem(w, state):
    """v0.187: None when the glyph has exactly one layer and it is the active one, otherwise the refusal reason. Both routes and both
    forms of add_component ask it before the route is chosen: in NB 1353 an empty active layer beside a full one took the empty route,
    and the build named that layer as the source's layer. The user's choice (rule A). Read only. Never raises."""
    working_name = state.get("layer_name")
    lay = _beside_layers(w, working_name)
    if lay is None:
        return "the glyph's layers could not be read: nothing was changed"
    if lay[0] != [working_name] or working_name == _TL_TEMP_NAME:     # working_name is the active layer's name (state)
        return f"add_component needs a glyph with exactly one layer, the active one (it has {lay[0]}, active {lay[3]!r}): nothing was changed"
    return None


def _beside_restore(w, working_name, existing, width_before):
    """v0.186: put the glyph back after a failure partway (the user's choice): the components the call added to the working layer
    removed, the working layer active, the temporary layer removed, the width written back. Each step is reported; restored is True
    only when the re-read shows the glyph as before. Never raises."""
    out = {}
    try:
        lay = _beside_layers(w, working_name)
        if lay is None:
            out["error"] = "the glyph's layers could not be read"
        else:
            names, wl, tl, active = lay
            if wl is None:
                out["components_removed"] = "not attempted: the working layer was not found"
            else:
                view = _tl_view(wl, True)
                if not _tl_ok(view):
                    out["components_removed"] = "not attempted: the working layer could not be read"
                else:
                    missing, new = _trycomp_match_existing(existing["elements"], view["elements"])
                    if missing or any(view["elements"][j].get("is_component") is not True for j in new):
                        out["components_removed"] = ("not attempted: the working layer lost an element or gained one that is not a "
                                                     "component, so it is not only the call's components")
                    else:
                        shapes, err = _tl_call(lambda: wl.shapes)
                        if err is not None or type(shapes) is not list or len(shapes) != len(view["elements"]):
                            out["components_removed"] = "not attempted: layer.shapes is not a plain list matching the elements"
                        else:
                            n = 0
                            for j in sorted(new, reverse=True):
                                wl.removeShape(shapes[j], False)
                                n += 1
                            out["components_removed"] = n
            if wl is not None and active != working_name:
                wl.setActive()
                out["working_layer_made_active"] = True
            if tl is not None:
                auto, err = _tl_call(lambda: _call0(tl, "autoLayer"))
                if auto is True:
                    tl.autoLayer = False
                    out["temp_auto_layer_off"] = True
                w.removeLayer(tl)
                out["temp_layer_removed"] = True
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    try:
        if _trycomp_width(w) != width_before:
            w.advanceWidth = width_before
            out["width_restored"] = True
    except Exception as exc:
        out["width_restored"] = f"failed: {type(exc).__name__}: {exc}"
    lay2 = _beside_layers(w, working_name)
    ok = False
    if lay2 is not None and lay2[0] == [working_name] and lay2[3] == working_name and lay2[1] is not None:
        view2 = _tl_view(lay2[1], True)
        ok = (_tl_ok(view2) and view2["contours"] == existing["contours"] and len(view2["elements"]) == len(existing["elements"])
              and not any(_trycomp_match_existing(existing["elements"], view2["elements"])) and _trycomp_width(w) == width_before)
    out["restored"] = bool(ok)
    return out


def _add_beside(base, name, ctx, state, layer, tel, entries):
    """v0.186: place `entries` ([{"component", "x", "y"}], in order) beside what the glyph `name` already holds. See the section comment.
    The caller has checked the names, the size and the master count. Never saves. Never raises."""
    w, font = ctx["w"], ctx["font"]
    names = [e["component"] for e in entries]
    base = dict(base, placement="temporary layer")
    working_name = state.get("layer_name")
    lay = _beside_layers(w, working_name)
    if lay is None:
        return dict(base, reason="the glyph's layers could not be read: nothing was changed")
    if lay[0] != [working_name] or working_name == _TL_TEMP_NAME or lay[3] != working_name:
        return dict(base, reason=(f"a glyph that is not empty needs exactly one layer, the active one (it has {lay[0]}, active "
                                  f"{lay[3]!r}): nothing was changed"))
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False or str(auto_before.get("recipe")).startswith("<error"):
        return dict(base, reason=(f"the glyph's layer reads autoLayer {auto_before.get('auto_layer')!r} and recipe {auto_before.get('recipe')!r}; "
                                  "add_component needs a readable recipe and autoLayer off: nothing was changed"))
    for e in tel:      # before any inkBox(): a Power Brush shape is never given one (F1)
        comp_ok = e.get("is_component") is True and isinstance(e.get("component_glyph"), str) and not e["component_glyph"].startswith("<error")
        if not comp_ok and not (e.get("is_component") is False and type(e.get("is_composite")) is bool):
            return dict(base, reason=(f"element {e.get('index')} of the glyph cannot be read as a contour shape, a component or a Power Brush "
                                      f"shape (is_component {e.get('is_component')!r}, is_composite {e.get('is_composite')!r}): nothing was changed"))
    existing = _tl_view(layer, True)
    base["existing_before"] = existing["elements"]
    if not _tl_ok(existing):
        return dict(base, reason="the glyph's elements or outline could not be read in full: nothing was changed")
    sources, bad = _comp_sources(names)
    if sources is None:
        return dict(base, component_found=bad[0], reason=bad[1])
    width_before = _trycomp_width(w)
    count_before = _tryedit_glyph_count(font)
    base["advance_width_before"], base["glyph_count_before"] = width_before, count_before
    if not isinstance(width_before, float) or isinstance(count_before, str):
        return dict(base, reason="the glyph's advance width or the font's glyph count could not be read: nothing was changed")
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qt_cls, qt_src = _trycomp_qtransform_class(mod)
    if qt_cls is None:
        return dict(base, reason=f"{qt_src}: nothing was changed")
    layer_cls = getattr(mod, "flLayer", None)
    if layer_cls is None:
        return dict(base, reason="the fontlab module has no flLayer class: nothing was changed")
    wants = [{"left": sources[e["component"]]["box"]["left"] + e["x"], "right": sources[e["component"]]["box"]["right"] + e["x"],
              "top": sources[e["component"]]["box"]["top"] + e["y"], "bottom": sources[e["component"]]["box"]["bottom"] + e["y"]}
             for e in entries]
    done, step = [], f"w.addLayer(flLayer({_TL_TEMP_NAME!r}))"
    try:
        w.addLayer(layer_cls(_TL_TEMP_NAME))
        done.append("temp_added")
        step = "finding the temporary layer"
        lay = _beside_layers(w, working_name)
        if lay is None or lay[1] is None or lay[2] is None or len(lay[0]) != 2:
            raise RuntimeError(f"the glyph holds the layers {lay[0] if lay else 'unreadable'} after addLayer")
        wl, tl = lay[1], lay[2]
        if lay[3] != working_name:
            step = "working_layer.setActive()"
            wl.setActive()
            lay = _beside_layers(w, working_name)
            if lay is None or lay[3] != working_name:
                raise RuntimeError(f"the active layer is {lay[3] if lay else 'unreadable'!r} after setActive()")
        done.append("working_active")
        step = "temporary layer: recipe = the components joined by +"
        tl.recipe = "+".join(names)
        done.append("recipe")
        step = "temporary layer: autoLayer = True"
        tl.autoLayer = True
        done.append("auto_on")
        step = "temporary layer: buildAuto()"
        t_build = time.perf_counter()
        ret = tl.buildAuto()
        base["build_seconds"] = round(time.perf_counter() - t_build, 3)
        done.append("build")
        base["build_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        if ret is not True:
            raise RuntimeError(f"it returned {base['build_returned']!r}, not True")
        step = "temporary layer: autoLayer = False"
        tl.autoLayer = False
        done.append("auto_off")
        step = "checking the built components against the list"
        built = _trycomp_elements(tl)
        shapes, err = _tl_call(lambda: tl.shapes)
        if isinstance(built, dict) or err is not None or type(shapes) is not list or len(shapes) != len(entries) or len(built) != len(entries):
            raise RuntimeError(f"the temporary layer does not hold {len(entries)} elements as a plain list after the build")
        wrong = [i for i, e in enumerate(built) if e.get("is_component") is not True or e.get("component_glyph") != names[i]]
        if wrong:
            raise RuntimeError(f"the built components are not the list in order (first difference at position {wrong[0]}: "
                               f"{built[wrong[0]].get('component_glyph')!r}, not {names[wrong[0]]!r})")
        done.append("order_checked")
        for i, e in enumerate(entries):
            if not _trycomp_offset_ok(built[i].get("matrix"), e["x"], e["y"]):
                step = f"shape.transform = QTransform(1, 0, 0, 1, x, y) on component {i}"
                shapes[i].transform = qt_cls(1.0, 0.0, 0.0, 1.0, float(e["x"]), float(e["y"]))
            step = f"shapeData.componentLayer on component {i}"
            sd, err = _tl_call(lambda s=shapes[i]: s.shapeData)
            if err is not None or sd is None:
                raise RuntimeError(f"its shapeData could not be read ({err or 'None'})")
            named, err = _tl_call(lambda: _call0(sd, "componentGlyph"))
            if err is not None or named != names[i]:
                raise RuntimeError(f"it names {named!r}, not {names[i]!r}")
            if built[i].get("component_layer") != sources[names[i]]["layer"]:
                sd.componentLayer = sources[names[i]]["layer"]
        done.append("offsets_and_layers")
        step = 'temporary layer: recipe = ""'
        tl.recipe = ""
        done.append("recipe_cleared")
        for i, sh in enumerate(shapes):
            step = f"working_layer.addShape(<component {i}>)"
            wl.addShape(sh)
        done.append("moved")
        step = "w.removeLayer(<the temporary layer>)"
        w.removeLayer(tl)
        done.append("temp_removed")
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base, steps_done=list(done))
    if "error" in result and done:
        result["restore"] = _beside_restore(w, working_name, existing, width_before)
    elif "error" not in result:
        width_now = _trycomp_width(w)
        if width_now != width_before:
            result["width_set_by_build"] = width_now
            try:
                w.advanceWidth = width_before
                result["cleanup"] = {"width_restored": True}
            except Exception as exc:
                result["cleanup"] = {"width_restored": f"failed: {type(exc).__name__}: {exc}"}
    if done:
        result["display_refreshed"] = _repaint_viewport()
    lay2 = _beside_layers(w, working_name)
    result["layers_after"] = lay2[0] if lay2 is not None else "unreadable"
    result["active_layer_after"] = lay2[3] if lay2 is not None else "unreadable"
    wl2 = lay2[1] if lay2 is not None else None
    view2 = _tl_view(wl2, True) if wl2 is not None else {"elements": {"error": "no working layer"}, "contours": {"error": "no working layer"}}
    rows2 = view2["elements"]
    tel2 = _trycomp_elements(wl2) if wl2 is not None else {"error": "no working layer"}
    auto_after = _trycomp_auto_state(wl2) if wl2 is not None else {"error": "no working layer"}
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    n0 = len(existing["elements"])
    readable = _tl_ok(view2)
    per = []
    for i, e in enumerate(entries):
        r = rows2[n0 + i] if (readable and len(rows2) > n0 + i) else None
        ok_i = bool(r is not None and r.get("is_component") is True and r.get("component_glyph") == e["component"]
                    and r.get("component_layer") == sources[e["component"]]["layer"] and _trycomp_offset_ok(r.get("matrix"), e["x"], e["y"])
                    and _comp_box_at(r.get("ink_box"), wants[i]) is True)
        per.append({"component": e["component"], "x": e["x"], "y": e["y"],
                    "state": "placed" if ok_i else ("not reached" if "moved" not in done else "unknown")})
    result["component_states"] = per
    checks = {
        "layers": lay2 is not None and lay2[0] == [working_name] and lay2[3] == working_name,
        "existing_kept": bool(readable and len(rows2) >= n0 and all(_trycomp_same_element(rows2[i], existing["elements"][i]) for i in range(n0))),
        "components": bool(readable and len(rows2) == n0 + len(entries) and all(p["state"] == "placed" for p in per)),
        "contours_held": bool(readable and _trycomp_holds(view2["contours"], existing["contours"])),
        "auto_layer_and_recipe_unchanged": auto_after == auto_before,
        "sources_unchanged": all("error" not in (s2 := _tryedit_snapshot(src)) and s2["contours"] == sources[src]["snapshot"]["contours"]
                                 for src in sources),
        "width_unchanged": width_after == width_before,
        "glyph_count_unchanged": result["glyph_count_after"] == count_before,
    }
    result["checks"] = checks
    result["existing_kept"] = checks["existing_kept"]
    result["placed"] = bool("error" not in result and all(v is True for v in checks.values()))
    result["verified"] = result["placed"]
    restored = (result.get("restore") or {}).get("restored") is True
    if not done:
        result["changed"] = False
    elif result["placed"] or not restored:
        result["changed"] = "unknown" if not readable else True
    else:
        result["changed"] = False      # restored: the re-read shows the glyph as before
    if not result["placed"]:
        failed = [k for k, v in checks.items() if v is not True]
        result["reason"] = (result.get("error") or "the re-read does not confirm the components") + (
            ": failed checks: " + ", ".join(failed) if failed else "")
        result["components_after"] = _comp_after(tel2)
    if done:
        _guard_mark(font, name, "add_component", result,
                    no_mark=None if result["placed"] else ("nothing was placed: the glyph was restored" if restored else
                                                           "the components were not confirmed"))
    return result


# --------------------------------------------------------------------------
# /debug/tryedit (v0.151) - RESEARCH for P2.2 (editing an existing outline, required by the user on 2026-11-14): ONE edit of a drawn
# glyph per call, read back from the modern layer before and after. Every stage needs go=yes and the one-font gate of /debug/trysync;
# glyph names starting with "edp" only; at most _TRYEDIT_MAX calls per listener run, counted BEFORE anything is read or touched. The
# glyph must be PLAIN: exactly one shape in layer.shapes (a real list) that reads isComponent False and isComposite False (a Power Brush
# shape reads isComposite True, F1), no components. Contours only through layer.getContours() (a real list), nodes only through
# getNodeAt(i) after a range check on nodesCount.
#   stage=movenode&contour=C&node=N&dx=DX&dy=DY  node.x = x + dx, then node.y = y + dy (whole numbers, |dx|, |dy| <= 200, not both 0)
#   stage=addcontour             a fixed closed square (600, 600) (650, 600) (650, 650) (600, 650), built and checked DETACHED as
#                                draw_path builds, then shape.shapeData.addContour(contour) into the glyph's existing shape
#   stage=removecontour&contour=C   shape.shapeData.removeContour(<contour C of layer.getContours()>)
#   stage=replace                a fixed closed triangle (100, 0) (300, 0) (200, 300) in a new flShape (built and checked detached),
#                                then layer.replaceShape(old_shape, new_shape)
# The reply has the outline before and after, the expected outline, mismatches, the glyph count before and after, and
# side_effect_detected. A change goes through _guard_mark (Update(<flGlyph>), the sync check, the changed mark), as every write does.
# v0.152 (step B2, live 968-983: the modern sidebearings lagged after an edit until a GUI event): &refresh=R, one name of
# _TRYEDIT_REFRESH, calls that ONE member once, right after a confirmed edit and before _guard_mark; the sidebearings are read before and
# after it and compared with the ones the edited nodes give (straight contours only), and the outline is compared before and after it
# (refresh_changed_outline). The member is looked up only from that fixed table; resetMetrics* is never in it.
# Never called by this probe: font.update(), save, removeGlyph, smartMove, smartSetXY, moveBy, decomposite, ejectTo, shapeBuilder,
# activateBuilder, resetMetricsLeft / Right / Width; no subscript or iteration of a native object.
# --------------------------------------------------------------------------

_TRYEDIT_MAX = 8
_TRYEDIT = {"calls": 0}
_TRYEDIT_STAGES = ("movenode", "addcontour", "removecontour", "replace")
_TRYEDIT_DELTA_MAX = 200
_TRYEDIT_INDEX_MAX = 5000
_TRYEDIT_CALLS = {"movenode": "node.x = x + dx, then node.y = y + dy", "addcontour": "shape.shapeData.addContour(contour)",
                  "removecontour": "shape.shapeData.removeContour(contour)", "replace": "layer.replaceShape(old_shape, new_shape)"}
_TRYEDIT_NOTE = ("RESEARCH: compare with get_glyph_outline and with FontLab's own view of the glyph; nothing is saved by Glyphbridge; "
                 "quit FontLab WITHOUT saving afterwards, or delete the edp glyphs")
_TRYEDIT_REFRESH = {"contour.update": ("contour", "update"), "shape.update": ("shape", "update"), "shapedata.update": ("shapedata", "update"),
                    "layer.update": ("layer", "update"), "glyph.update": ("glyph", "update"), "layer.changed": ("layer", "changed"),
                    "shape.changed": ("shape", "changed"), "layer.resetinkbox": ("layer", "resetInkBox")}
_TRYEDIT_MARGIN_TOLERANCE = 0.05


def _tryedit_point(x, y):
    return {"x": x, "y": y, "c1": None, "c2": None, "smooth": False}


_TRYEDIT_SQUARE = [_tryedit_point(600, 600), _tryedit_point(650, 600), _tryedit_point(650, 650), _tryedit_point(600, 650)]
_TRYEDIT_TRIANGLE = [_tryedit_point(100, 0), _tryedit_point(300, 0), _tryedit_point(200, 300)]


def _tryedit_int(raw, label, lo, hi):
    """(int, None) or (None, sentence) for one query value."""
    import re as _re
    if raw is None or not str(raw).strip():
        return None, f"{label} is required for this stage"
    s = str(raw).strip()
    if not _re.fullmatch(r"-?[0-9]{1,6}", s):
        return None, f"{label} must be a whole number"
    v = int(s)
    if not lo <= v <= hi:
        return None, f"{label} must be between {lo} and {hi}"
    return v, None


def _tryedit_snapshot(name):
    """{"contours": [{"closed", "nodes": [{x, y, kind, smooth}]}], "margins"} of the modern layer, or {"error"}. Never raises."""
    modern = _read_modern_outline(name)
    if modern.get("available") is not True:
        return {"error": modern.get("error") or "the outline could not be read"}
    out = []
    for c in modern.get("contours") or []:
        out.append({"closed": c.get("closed"), "nodes": [{"x": n.get("x"), "y": n.get("y"), "kind": "On" if n.get("isOn") else (
            "Curve" if n.get("isCurve") else "Off"), "smooth": n.get("smooth")} for n in (c.get("nodes") or [])]})
    snap = {"contours": out}
    if modern.get("margins") is not None:
        snap["margins"] = modern["margins"]
    return snap


def _tryedit_new_contour(pts):
    """The snapshot form of a closed contour built from `pts` (straight segments, no smooth node)."""
    return {"closed": True, "nodes": [{"x": p["x"], "y": p["y"], "kind": "On", "smooth": False} for p in pts]}


def _tryedit_compare(got, want):
    """(mismatches, smooth_changed): sentences for every difference in contour count, closed flags, node count, position and kind;
    smooth flags apart, as [contour, node] pairs."""
    bad, smooth = [], []
    if len(got) != len(want):
        return [f"the layer reads {len(got)} contour(s), {len(want)} expected"], smooth
    for ci, (g, e) in enumerate(zip(got, want)):
        if g.get("closed") is not e.get("closed"):
            bad.append(f"contour {ci}: closed reads {g.get('closed')!r}, expected {e.get('closed')!r}")
        gn, en = g.get("nodes") or [], e.get("nodes") or []
        if len(gn) != len(en):
            bad.append(f"contour {ci}: {len(gn)} nodes read, {len(en)} expected")
            continue
        for ni, (a, b) in enumerate(zip(gn, en)):
            if abs(a["x"] - b["x"]) > 0.001 or abs(a["y"] - b["y"]) > 0.001:
                bad.append(f"contour {ci} node {ni}: position ({a['x']}, {a['y']}) instead of ({b['x']}, {b['y']})")
            if a.get("kind") != b.get("kind"):
                bad.append(f"contour {ci} node {ni}: kind {a.get('kind')} instead of {b.get('kind')}")
            if bool(a.get("smooth")) != bool(b.get("smooth")):
                smooth.append([ci, ni])
    return bad, smooth


def _tryedit_glyph_count(font):
    """len(font.glyphs) (a real list, as delete_glyph reads it) or an "<error: ...>" string."""
    n, err = _tl_call(lambda: len(font.glyphs))
    return n if err is None else f"<error: {err}>"


def _tryedit_build(mod, qp, pts, label):
    """(contour, None) or (None, sentence): ONE closed contour built and checked DETACHED, as draw_path builds it."""
    expected, on_index = _path_layout(pts)
    try:
        contour = _path_build_contour(mod, qp, pts, expected, on_index, closed=True)
    except Exception as exc:
        return None, f"the {label} could not be built detached ({exc})"
    rows, err = _path_read_nodes(contour)
    if rows is None:
        return None, f"the detached {label} could not be read back ({err})"
    closed, _e = _tl_call(lambda: contour.closed)
    bad = _path_mismatches(rows, expected, f"detached {label}")
    if closed is not True:
        bad.append(f"detached {label}: closed reads {closed!r}")
    if bad:
        return None, "the detached " + label + " does not match: " + " | ".join(bad[:6])
    return contour, None


def _tryedit_expected_margins(want, advance):
    """({"lsb", "rsb", "advance"}, None) that the expected outline gives, or (None, reason). Straight contours only: their extent is the
    box of their nodes; a curve's is not."""
    nodes = [n for c in want for n in c.get("nodes") or []]
    if not nodes:
        return None, "the outline is empty"
    if any(n.get("kind") != "On" for n in nodes):
        return None, "the outline has curves, so its extent is not the box of its nodes"
    xs = [n["x"] for n in nodes]
    return {"lsb": min(xs), "rsb": advance - max(xs), "advance": advance}, None


def _tryedit_margins_current(m, exp):
    return all(abs(m[k] - exp[k]) <= _TRYEDIT_MARGIN_TOLERANCE for k in ("lsb", "rsb", "advance"))


def _tryedit_refresh(refresh, w, tr, layer, shape, contour, name, want):
    """v0.152: ONE call of the member _TRYEDIT_REFRESH names, with the sidebearings before and after it. Never raises; the outline read
    just before the call is returned under "_mid" for the caller's comparison."""
    out = {"refresh": refresh}
    def margins():
        if tr is None:
            return None, "no QTransform for the margin getters"
        return _modern_margins_read(w, tr)
    m0, err0 = margins()
    out["margins_before_refresh"] = m0 if m0 is not None else {"error": err0}
    out["_mid"] = _tryedit_snapshot(name)
    label, member = _TRYEDIT_REFRESH[refresh]
    obj, err = {"contour": (contour, None), "shape": (shape, None), "layer": (layer, None), "glyph": (w, None)}.get(label, (None, None))
    if label == "shapedata":
        obj, err = _tl_call(lambda: shape.shapeData)
    if err is not None or obj is None:
        out["refresh_error"] = f"there is no {label} to call {member}() on ({err or 'None'})"
    else:
        fn, err = _tl_call(lambda: getattr(obj, member))
        if err is not None or not callable(fn):
            out["refresh_error"] = f"{label}.{member} is not callable ({err or type(fn).__name__})"
        else:
            out["refresh_call"] = f"{label}.{member}()"
            ret, err = _tl_call(fn)
            if err is not None:
                out["refresh_error"] = err
            else:
                out["refresh_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else type(ret).__name__
    m1, err1 = margins()
    out["margins_after_refresh"] = m1 if m1 is not None else {"error": err1}
    exp, why = _tryedit_expected_margins(want, m0["advance"]) if m0 is not None else (None, "the margins could not be read")
    out["margins_expected"] = exp if exp is not None else {"error": why}
    if exp is not None:
        out["margins_current_before_refresh"] = _tryedit_margins_current(m0, exp)
        out["margins_current_after_refresh"] = _tryedit_margins_current(m1, exp) if m1 is not None else "unknown"
    return out


def debug_try_edit(stage, name, go, contour=None, node=None, dx=None, dy=None, refresh=None):
    import sys as _sys
    if stage not in _TRYEDIT_STAGES:
        return {"error": 'stage must be "movenode", "addcontour", "removecontour" or "replace"'}
    if (not isinstance(name, str) or not (4 <= len(name) <= 40) or not name.startswith("edp")
            or any(ch not in _TRYCREATE_NAME_CHARS for ch in name)):
        return {"error": 'name must start with "edp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
    args = {}
    if stage in ("movenode", "removecontour"):
        v, err = _tryedit_int(contour, "contour", 0, _TRYEDIT_INDEX_MAX)
        if err is not None:
            return {"error": err}
        args["contour"] = v
    if stage == "movenode":
        for label, raw, lo, hi in (("node", node, 0, _TRYEDIT_INDEX_MAX), ("dx", dx, -_TRYEDIT_DELTA_MAX, _TRYEDIT_DELTA_MAX),
                                   ("dy", dy, -_TRYEDIT_DELTA_MAX, _TRYEDIT_DELTA_MAX)):
            v, err = _tryedit_int(raw, label, lo, hi)
            if err is not None:
                return {"error": err}
            args[label] = v
        if args["dx"] == 0 and args["dy"] == 0:
            return {"error": "dx and dy are both 0: nothing would change"}
    refresh = str(refresh).strip() if refresh is not None and str(refresh).strip() else None
    if refresh is not None:
        if refresh not in _TRYEDIT_REFRESH:
            return {"error": "refresh must be one of: " + ", ".join(_TRYEDIT_REFRESH)}
        if refresh == "contour.update" and stage != "movenode":
            return {"error": "refresh=contour.update needs stage=movenode (the edited contour)"}
        args["refresh"] = refresh
    if go != "yes":
        what = {"movenode": "moves one node of the glyph by (dx, dy)", "addcontour": "adds a fixed square contour to the glyph's shape",
                "removecontour": "removes one contour from the glyph's shape", "replace": "replaces the glyph's shape with a fixed triangle"}[stage]
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": _TRYEDIT["calls"], "max_calls": _TRYEDIT_MAX}
    if _TRYEDIT["calls"] >= _TRYEDIT_MAX:
        return {"stage": stage, "error": f"the probe already ran {_TRYEDIT_MAX} times in this listener run; restart the listener to repeat it",
                "calls_so_far": _TRYEDIT["calls"], "max_calls": _TRYEDIT_MAX}
    qp = getattr(QtCore, "QPointF", None)
    if stage in ("addcontour", "replace") and (qp is None or getattr(mod, "flContour", None) is None or getattr(mod, "flShape", None) is None):
        return {"stage": stage, "error": "QtCore.QPointF, fontlab.flContour or fontlab.flShape is missing: nothing was touched",
                "calls_so_far": _TRYEDIT["calls"], "max_calls": _TRYEDIT_MAX}
    _TRYEDIT["calls"] += 1     # counted BEFORE the glyph is read or touched: whatever happens, it is on record
    base = dict({"stage": stage, "name": name, "call": _TRYEDIT_CALLS[stage], "calls_so_far": _TRYEDIT["calls"], "max_calls": _TRYEDIT_MAX,
                 "note": _TRYEDIT_NOTE}, **args)
    ctx, refusal = _modern_edit_target(name)
    if ctx is None:
        return dict(base, error="the glyph cannot be edited: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["state_before"] = state
    if layer is None:
        return dict(base, error="the glyph has no modern active layer: nothing was touched")
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list:
        return dict(base, error=f"layer.shapes is not a plain list ({err or type(shapes).__name__}): nothing was touched")
    if len(shapes) != 1:
        return dict(base, error=f"the glyph has {len(shapes)} shapes; the probe edits a glyph with exactly one: nothing was touched")
    shape = shapes[0]
    for attr in ("isComponent", "isComposite"):
        v, err = _tl_call(lambda a=attr: _call0(shape, a))
        if err is not None or v is not False:
            return dict(base, error=(f"the shape's {attr} reads {v!r}{' (' + err + ')' if err else ''}: only a plain shape is edited, never a "
                                     "component or a Power Brush or other composite shape: nothing was touched"))
    if _state_has_components(state):
        return dict(base, error=f"the layer reads {_state_components_text(state)}: nothing was touched")
    before = _tryedit_snapshot(name)
    if "error" in before:
        return dict(base, error=f"the outline could not be read before the edit ({before['error']}): nothing was touched")
    base["before"] = before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    contours, err = _tl_call(lambda: layer.getContours())
    if err is not None or type(contours) not in (list, tuple):
        return dict(base, error=f"layer.getContours() is not a plain list ({err or type(contours).__name__}): nothing was touched")
    if len(contours) != len(before["contours"]):
        return dict(base, error="layer.getContours() disagrees with the outline just read: nothing was touched")
    want = [dict(c, nodes=[dict(n) for n in c["nodes"]]) for c in before["contours"]]
    step, touched = "reading the target", False
    cur_shape, edited_contour = shape, None
    try:
        if stage == "movenode":
            ci, ni = args["contour"], args["node"]
            if ci >= len(contours):
                return dict(base, error=f"contour {ci} does not exist (the glyph has {len(contours)}): nothing was touched")
            target = contours[ci]
            edited_contour = target
            count, err = _tl_call(lambda: _call0(target, "nodesCount"))
            if err is not None or not isinstance(count, int) or isinstance(count, bool):
                return dict(base, error=f"nodesCount of contour {ci} is not readable ({err or count!r}): nothing was touched")
            if ni >= count:
                return dict(base, error=f"node {ni} does not exist (contour {ci} has {count}): nothing was touched")
            nd, err = _tl_call(lambda: target.getNodeAt(ni))
            if err is not None or nd is None:
                return dict(base, error=f"getNodeAt({ni}) failed ({err or 'returned None'}): nothing was touched")
            x0, y0 = _rm_plain(_call0(nd, "x")), _rm_plain(_call0(nd, "y"))
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in (x0, y0)):
                return dict(base, error="the node's x / y are not numbers: nothing was touched")
            want[ci]["nodes"][ni]["x"] = x0 + args["dx"]
            want[ci]["nodes"][ni]["y"] = y0 + args["dy"]
            step, touched = "node.x = x + dx", True
            nd.x = float(x0 + args["dx"])
            step = "node.y = y + dy"
            nd.y = float(y0 + args["dy"])
        elif stage == "removecontour":
            ci = args["contour"]
            if ci >= len(contours):
                return dict(base, error=f"contour {ci} does not exist (the glyph has {len(contours)}): nothing was touched")
            want.pop(ci)
            step = "shape.shapeData"
            sd = shape.shapeData
            step, touched = "shape.shapeData.removeContour(contour)", True
            sd.removeContour(contours[ci])
        else:
            pts = _TRYEDIT_SQUARE if stage == "addcontour" else _TRYEDIT_TRIANGLE
            label = "square" if stage == "addcontour" else "triangle"
            built, why = _tryedit_build(mod, qp, pts, label)
            if built is None:
                return dict(base, error=why + ": nothing was touched")
            if stage == "addcontour":
                want.append(_tryedit_new_contour(pts))
                step = "shape.shapeData"
                sd = shape.shapeData
                step, touched = "shape.shapeData.addContour(contour)", True
                sd.addContour(built)
            else:
                want = [_tryedit_new_contour(pts)]
                step = "flShape()"
                new_shape = mod.flShape()
                step = "new_shape.shapeData.addContour(contour)"
                new_shape.shapeData.addContour(built)
                step, touched = "layer.replaceShape(old_shape, new_shape)", True
                layer.replaceShape(shape, new_shape)
                cur_shape = new_shape
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    refresh_info = None
    if refresh is not None and touched and "error" not in base:
        refresh_info = _tryedit_refresh(refresh, w, ctx["tr"], layer, cur_shape, edited_contour, name, want)
    result = dict(base, expected_after=want)
    if refresh is not None and refresh_info is None:
        result["refresh_error"] = "not called: the edit was not made or failed"
    if touched:
        result["display_refreshed"] = _repaint_viewport()
    after_state, _l = _tryshape_modern_state(w)
    result["state_after"] = after_state
    after = _tryedit_snapshot(name)
    result["after"] = after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    if "error" in after:
        result["changed"] = "unknown"
        result["mismatches"] = [f"the outline could not be read after the edit ({after['error']})"]
        result["smooth_changed"] = []
    else:
        result["changed"] = after["contours"] != before["contours"]
        result["mismatches"], result["smooth_changed"] = _tryedit_compare(after["contours"], want)
    if refresh_info is not None:
        mid = refresh_info.pop("_mid")
        for k, v in refresh_info.items():
            result[k] = v
        result["refresh_changed_outline"] = ("unknown" if ("error" in mid or "error" in after) else mid["contours"] != after["contours"])
    result["side_effect_detected"] = bool(result["smooth_changed"] or result["glyph_count_after"] != result["glyph_count_before"]
                                          or after_state.get("shapes") != 1 or _state_has_components(after_state)
                                          or result.get("refresh_changed_outline") is True)
    result["edited"] = bool("error" not in result and not result["mismatches"] and not result["side_effect_detected"])
    if result["changed"] is not False:
        _guard_mark(font, name, "tryedit", result, no_mark=None if result["edited"] else "the edit was not confirmed")
    return result


# --------------------------------------------------------------------------
# /debug/tryopen (v0.125) - RESEARCH for P2.1 (drawing open contours): does a contour that is never closed stay open once it is
# attached? The read side is server 0.46 (live 579-585): FontLab's own open contours read closed False, an open curve On, Curve,
# Curve, On. Every stage needs go=yes and the one-font gate of /debug/trysync; glyph names starting with "ocp" only; at most
# _TRYOPEN_MAX calls per listener run, counted BEFORE anything is created or built. Fixed shapes, no input:
#   kind=line   the open V of live 581: (24, 482), (132, 69), (228, 462)
#   kind=curve  the open arch of live 583: (105, 104) to (398, 104), handles (105, 280) and (398, 255)
#   stage=detached  build the contour (_path_build_contour with closed=False) and read it back; the glyph is not touched
#   stage=draw      the same build into a glyph whose modern layer is KNOWN to be empty (a missing layer is created, as draw_path
#                   does), then flShape(), shape.shapeData.addContour(contour), layer.addShape(shape); the layer is read back and the
#                   glyph marked for the guard. Nothing is attached unless the detached contour reads closed False with the
#                   expected positions and node kinds (smooth flags are reported, not required)
# Never called by this probe: contour.closed = True, font.update(), save.
# --------------------------------------------------------------------------

_TRYOPEN_MAX = 6
_TRYOPEN = {"calls": 0}
_TRYOPEN_STAGES = ("detached", "draw")


def _tryopen_point(x, y, c1=None, c2=None):
    return {"x": x, "y": y, "c1": c1, "c2": c2, "smooth": False}


_TRYOPEN_SHAPES = {"line": [_tryopen_point(24, 482), _tryopen_point(132, 69), _tryopen_point(228, 462)],
                   "curve": [_tryopen_point(105, 104), _tryopen_point(398, 104, (105, 280), (398, 255))]}
_TRYOPEN_NOTE = ("RESEARCH: compare with get_glyph_outline (server 0.46) and with FontLab's own view of the glyph; nothing is saved by "
                 "Glyphbridge; quit FontLab WITHOUT saving afterwards, or delete the ocp glyphs")


def _tryopen_read(contour, expected, label):
    """What a contour reads: closed, its nodes, and the differences from `expected` (positions and node kinds; smooth flags apart)."""
    closed, cerr = _tl_call(lambda: contour.closed)
    rows, err = _path_read_nodes(contour)
    out = {"closed": _rm_plain(closed) if cerr is None else f"<error: {cerr}>"}
    if rows is None:
        return dict(out, read_error=err, mismatches=[f"{label}: the nodes could not be read ({err})"])
    out["nodes"] = [{"x": r["x"], "y": r["y"], "kind": "On" if r.get("isOn") else ("Curve" if r.get("isCurve") else "Off"),
                     "smooth": r.get("smooth")} for r in rows]
    same_smooth = ([dict(e, smooth=bool(r.get("smooth"))) for r, e in zip(rows, expected)] if len(rows) == len(expected) else expected)
    out["mismatches"] = _path_mismatches(rows, same_smooth, label)
    out["smooth_differs"] = [i for i, (r, e) in enumerate(zip(rows, expected)) if e["on"] and bool(r.get("smooth")) != e["smooth"]]
    return out


def debug_try_open(stage, name, kind, go):
    import sys as _sys
    if stage not in _TRYOPEN_STAGES:
        return {"error": 'stage must be "detached" or "draw"'}
    if kind not in _TRYOPEN_SHAPES:
        return {"error": 'kind must be "line" (the open V of test 581) or "curve" (the open arch of test 583)'}
    if (not isinstance(name, str) or not (4 <= len(name) <= 40) or not name.startswith("ocp")
            or any(ch not in _TRYCREATE_NAME_CHARS for ch in name)):
        return {"error": 'name must start with "ocp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
    if go != "yes":
        what = ("builds one open contour on detached objects and reads it back (the glyph is not touched)" if stage == "detached" else
                "draws one open contour into the empty glyph (a missing layer is created first)")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": _TRYOPEN["calls"]}
    if _TRYOPEN["calls"] >= _TRYOPEN_MAX:
        return {"stage": stage, "error": f"the probe already ran {_TRYOPEN_MAX} times in this listener run; restart the listener to repeat it",
                "calls_so_far": _TRYOPEN["calls"]}
    qp = getattr(QtCore, "QPointF", None)
    if qp is None or getattr(mod, "flContour", None) is None or getattr(mod, "flShape", None) is None:
        return {"stage": stage, "error": "QtCore.QPointF, fontlab.flContour or fontlab.flShape is missing: nothing was built",
                "calls_so_far": _TRYOPEN["calls"]}
    _TRYOPEN["calls"] += 1     # counted BEFORE anything is created or built: whatever happens, it is on record
    pts = _TRYOPEN_SHAPES[kind]
    expected, on_index = _path_layout(pts)
    base = {"stage": stage, "kind": kind, "name": name, "expected_nodes": [{"x": e["x"], "y": e["y"], "on": e["on"]} for e in expected],
            "calls_so_far": _TRYOPEN["calls"], "note": _TRYOPEN_NOTE}
    ctx, w, layer = None, None, None
    if stage == "draw":
        ctx, refusal = _modern_edit_target(name, create_layer=True)
        if ctx is None:
            return dict(base, error="the glyph is not drawable: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
        w = ctx["w"]
        if ctx.get("layer_created"):
            base["layer_created"] = ctx["layer_created"]
        state, layer = _tryshape_modern_state(w)
        base["state_before"] = state
        if layer is None or not _tryshape_modern_known_empty(state):
            return dict(base, error="the glyph's layer is not KNOWN to be empty (needs readable counts of 0 shapes, 0 nodes, 0 components), so nothing was drawn")
    try:
        contour = _path_build_contour(mod, qp, pts, expected, on_index, closed=False)
    except Exception as exc:
        return dict(base, error=f"the contour could not be built detached ({exc}): nothing was attached")
    detached = _tryopen_read(contour, expected, "detached contour")
    base["detached"] = detached
    if stage == "detached":
        return base
    if detached["closed"] is not False or detached["mismatches"]:
        return dict(base, error="the detached contour is not the expected open contour, so nothing was attached", drawn=False)
    step = "flShape()"
    try:
        shape = mod.flShape()
        step = "shape.shapeData.addContour(contour)"
        shape.shapeData.addContour(contour)
        step = "layer.addShape(shape)"
        layer.addShape(shape)
    except Exception as exc:
        after, _l = _tryshape_modern_state(w)
        return dict(base, error=f"{step} failed: {type(exc).__name__}: {exc}", state_after=after,
                    changed=(after.get("shapes") != 0 or after.get("nodes") != 0), drawn=False)
    result = dict(base, display_refreshed=_repaint_viewport())
    after, _l = _tryshape_modern_state(w)
    result["state_after"] = after
    result["changed"] = (after.get("shapes") != 0 or after.get("nodes") != 0)
    modern = _read_modern_outline(name)
    if modern.get("available") is True:
        got = modern.get("contours") or []
        result["layer_contours"] = [{"closed": c.get("closed"), "nodes": [{"x": n.get("x"), "y": n.get("y"), "kind": "On" if n.get("isOn") else (
            "Curve" if n.get("isCurve") else "Off"), "smooth": n.get("smooth")} for n in (c.get("nodes") or [])]} for c in got]
        mism = [] if len(got) == 1 else [f"the layer reads {len(got)} contour(s), 1 expected"]
        if len(got) == 1:
            rows = got[0].get("nodes") or []
            same = [dict(e, smooth=bool(r.get("smooth"))) for r, e in zip(rows, expected)] if len(rows) == len(expected) else expected
            mism.extend(_path_mismatches(rows, same, "layer contour"))
        result["layer_closed"] = got[0].get("closed") if len(got) == 1 else None
        result["layer_mismatches"] = mism
    else:
        result["read_back_error"] = modern.get("error")
    result["drawn"] = (after.get("shapes") == 1 and after.get("nodes") == len(expected) and not result.get("layer_mismatches", ["unread"])
                       and result.get("layer_closed") is False)
    if result["changed"]:
        _guard_mark(ctx["font"], name, "tryopen", result)
    if ctx["tr"] is not None:
        m, _err = _modern_margins_read(w, ctx["tr"])
        if m is not None:
            result["margins"] = m
    return result


def get_glyph_unicode(name):
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    raw = glyph.unicode
    # 0 and None both mean "no Unicode assigned" by FontLab's own convention
    # (codepoint 0 is the NULL control character, never a real glyph mapping).
    value = None if raw in (None, 0) else raw
    return {"open": True, "found": True, "name": name, "unicode": value}


def _kern_bad(message):
    return {"bad_request": message}


def _kern_name_ok(name):
    return isinstance(name, str) and 1 <= len(name) <= 63 and all(ch in _TRYCREATE_NAME_CHARS for ch in name)


def _kern_class_id(glyph, attr):
    """(id, None) or (None, error text): ONE attribute read of the glyph's kerning group id on one side (live, tests 200, 201, 215, 217:
    kerningLeft is the group of the glyph as LEFT member of a pair, kerningRight as RIGHT member, a "Kerning both" group is on both,
    0 means none). A callable is never called."""
    try:
        value = getattr(glyph, attr)
    except Exception as exc:
        return None, f"{attr} could not be read ({type(exc).__name__}: {exc})"
    if type(value) is not int:
        return None, f"{attr} is not a plain number ({type(value).__name__})"
    return value, None


def _kern_group_names(pkg):
    """(({id: name} of the KERNING groups, {ids listed twice}), None) or (None, error text), from ONE pkg.getAllGroups(), documented as
    list((bool kernGroup, string groupName, int id, int mark, list(string glyphName))) (live: tests 198, 214, 218). Only a real list or
    tuple is looked into; an entry of another shape, or not a kerning group, is skipped."""
    try:
        getter = pkg.getAllGroups
        if not callable(getter):
            return None, "flPackage.getAllGroups is not callable"
        groups = getter()
    except Exception as exc:
        return None, f"flPackage.getAllGroups() failed ({type(exc).__name__}: {exc})"
    if not isinstance(groups, (list, tuple)):
        return None, f"flPackage.getAllGroups() returned a {type(groups).__name__}, not a list"
    names, twice = {}, set()
    for entry in groups:
        if not isinstance(entry, (list, tuple)) or len(entry) != 5:
            continue
        flag, gname, gid, _mark, _members = entry
        if flag is not True or not isinstance(gname, str) or type(gid) is not int:
            continue
        if gid in names:
            twice.add(gid)
        names[gid] = gname
    return (names, twice), None


def _kern_package_by_path(mod, font):
    """(package, None) or (None, reason). READ ONLY. With several fonts open, the workspace's current package is taken for the current
    font only when both have the same, non-empty path (T5, tests 262-264: CurrentFont() and flWorkspace.currentPackage follow the font
    window in front together; the package name is empty, a new unsaved font has an empty path). packages() is never looked into."""
    try:
        font_path = font.path
    except Exception as exc:
        return None, f"the current font's path could not be read ({type(exc).__name__}: {exc})"
    if not isinstance(font_path, str) or not font_path:
        return None, "the current font has no file path (a new, unsaved font)"
    try:
        ws = mod.flWorkspace.instance()
    except Exception as exc:
        return None, f"the workspace could not be reached ({type(exc).__name__}: {exc})"
    pkg, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return None, err
    if pkg is None:
        return None, "the workspace has no current package"
    is_null, err = _pkg_get(pkg, "isNull")
    if err is not None:
        return None, err
    if is_null is not False:
        return None, "the current package is null or its state is unknown"
    pkg_path, err = _pkg_get(pkg, "path")
    if err is not None:
        return None, err
    if not isinstance(pkg_path, str) or not pkg_path:
        return None, "the current package has no path"
    if pkg_path != font_path:
        return None, "the current package's path differs from the current font's path (was another font window brought to the front?)"
    return pkg, None


def _kern_table_target(font, count):
    """(target, None) or (None, error text). READ ONLY. The current master's kerning table of the current font, matched as
    /kerning/pairs always did: with one font open the workspace's current package (v0.104), with several only by path
    (_kern_package_by_path, v0.112). target holds pkg, masters, master, kerning, getter (kerning.get), glyphs, by_name
    (first glyph of each name) and matched_by. Shared by the kerning read and, since v0.124, the kerning write."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    if count == 1:
        ws, pkg, why = _trysync_target(mod)
        if ws is None:
            return None, f"the kerning table could not be matched to the current font: {why}"
        matched_by = "only font"
    else:
        pkg, why = _kern_package_by_path(mod, font)
        if pkg is None:
            return None, (f"{count} fonts are open and the current font could not be matched to its kerning table: {why}. "
                          "Bring a saved font's window to the front, or close the other fonts (without saving them if they "
                          "are test fonts), and ask again")
        matched_by = "path"
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return None, f"the font's masters could not be read: {err}"
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return None, f"the font's masters are not a plain list of names ({type(masters).__name__})"
    master, err = _pkg_get(pkg, "master")
    if not isinstance(master, str) or master not in masters:
        return None, "the current master could not be read as one of the font's masters" + (f" ({err})" if err else "")
    try:
        kerning_of = pkg.kerning
        if not callable(kerning_of):
            raise TypeError("flPackage.kerning is not callable")
        kerning = kerning_of(master)
        getter = kerning.get
    except Exception as exc:
        return None, f"the kerning table of master {master!r} is not reachable: {type(exc).__name__}: {exc}"
    if not callable(getter):
        return None, "the kerning table's get is not callable"
    try:
        glyphs = list(font.glyphs)
        by_name = {}
        for g in glyphs:
            by_name.setdefault(str(g.name), g)
    except Exception as exc:
        return None, f"the glyph list could not be read: {type(exc).__name__}: {exc}"
    return {"pkg": pkg, "masters": masters, "master": master, "kerning": kerning, "getter": getter, "glyphs": glyphs,
            "by_name": by_name, "matched_by": matched_by}, None


def _kern_len(kerning):
    """len() of a kerning table as a plain int, or None."""
    try:
        n = len(kerning)
        return n if isinstance(n, int) and not isinstance(n, bool) else None
    except Exception:
        return None


def _kern_family(font):
    """The family name from the legacy font.info, or None (shown only to tell fonts apart)."""
    try:
        raw_family = font.info.familyName
        return raw_family if isinstance(raw_family, str) else None
    except Exception:
        return None


def _kern_value_ok(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and value not in (float("inf"), float("-inf"))


def _kern_effective(getter, by_name, pkg, groups, left, right):
    """The value FontLab applies to the glyph pair (left, right), as a dict to merge into a result entry: value, kerned, source
    and the class names, or error. The glyph's classes come from its kerningLeft / kerningRight group ids, named by ONE
    pkg.getAllGroups() per request (cached in groups) when an id is not 0. FontLab's order (tests 176, 192-213): glyph : glyph,
    glyph : class, class : glyph, class : class; the first entry that exists answers. No entry: value 0, kerned false, source none."""

    def _class_of(name, attr):
        gid, why = _kern_class_id(by_name[name], attr)
        if why is not None:
            return None, f"glyph {name!r}: {why}"
        if gid == 0:
            return None, None
        if "answer" not in groups:
            groups["answer"] = _kern_group_names(pkg)
        found, why = groups["answer"]
        if why is not None:
            return None, f"glyph {name!r} belongs to kerning class id {gid}, but the class names could not be read: {why}"
        names, twice = found
        if gid in twice:
            return None, f"glyph {name!r} belongs to kerning class id {gid}, which FontLab's class list names twice"
        if gid not in names:
            return None, f"glyph {name!r} belongs to kerning class id {gid}, which FontLab's class list does not contain"
        return names[gid], None

    left_class, left_err = _class_of(left, "kerningLeft")
    right_class, right_err = _class_of(right, "kerningRight")
    problems = [e for e in (left_err, right_err) if e]
    if problems:
        return {"error": "; ".join(problems)}
    keys = [("glyph : glyph", ((left, False), (right, False)), {})]
    if right_class is not None:
        keys.append(("glyph : class", ((left, False), (right_class, True)), {"right_class": right_class}))
    if left_class is not None:
        keys.append(("class : glyph", ((left_class, True), (right, False)), {"left_class": left_class}))
    if left_class is not None and right_class is not None:
        keys.append(("class : class", ((left_class, True), (right_class, True)), {"left_class": left_class, "right_class": right_class}))
    for source, key, classes in keys:
        try:
            value = getter(key)
        except Exception as exc:
            return {"error": f"kerning.get raised {type(exc).__name__}: {exc} (asking the {source} entry)"}
        if value is None:
            continue
        if _kern_value_ok(value):
            return dict(value=value, kerned=value != 0, source=source, **classes)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return {"error": f"kerning.get returned a number that is not finite (asking the {source} entry)"}
        return {"error": f"kerning.get returned an unexpected {type(value).__name__} (asking the {source} entry)"}
    return {"value": 0, "kerned": False, "source": "none"}


def get_kerning_pairs(pairs=None, text=None):
    """v0.104 - READ-ONLY kerning lookup in the table FontLab uses: flPackage.kerning(current master) (P0.8; live tests 191-218). The
    legacy font.kerning is never read: it misses kerning made in FontLab's GUI (defect A). Every pair is asked with explicit keys
    ((name, is_group), (name, is_group)), never with a plain name tuple, which reads a class whose name is also a glyph name as that
    class (defect B). A glyph's classes come from its kerningLeft / kerningRight group ids, named by ONE flPackage.getAllGroups() per
    request when any id is not 0. FontLab's order (tests 176, 192-213, both creation orders): glyph : glyph, glyph : class,
    class : glyph, class : class; the first entry that exists answers, and its kind is reported as source. No entry: value 0,
    kerned false, source "none". With one font open the workspace's current package is this font; with several (v0.112) the current
    package is used only when its path is not empty and equals the current font's path (_kern_package_by_path). The reply names
    fonts_open, matched_by ("only font" or "path") and family_name. Two input forms, exactly one of them:
      pairs  'A:V,T:o'  1 or more pairs of glyph names, no upper limit; the POST route sends a list of [left, right] lists (A-Z a-z 0-9 . _ -; ':' and ',' cannot occur in such names)
      text   2 or more characters; each character is mapped to the ONE glyph whose primary Unicode it is; the pairs are the neighbours.
    A name that is not a glyph, a character that maps to no glyph or to several, an unreadable or unnamed class id, a failed get() and
    a non-numeric answer become an 'error' entry for that pair: never a zero. The only member of the kerning table used is get;
    len() is read before and after the batch (side_effect_detected)."""
    have_pairs = bool(pairs)
    have_text = bool(text)
    if have_pairs == have_text:
        return _kern_bad("provide exactly one of pairs (GET: ?pairs=A:V,T:o; POST: a list of [left, right] glyph names) or text (2 or more characters)")
    wanted = []
    if have_pairs:
        if isinstance(pairs, str):
            raw_items = pairs.split(",")
            items = [item.strip().split(":") for item in raw_items]
        elif isinstance(pairs, list):
            raw_items = pairs
            items = pairs
        else:
            return _kern_bad("pairs must be a string like A:V,T:o or a list of [left, right] lists")
        for i, parts in enumerate(items):
            if (not isinstance(parts, list) or len(parts) != 2 or not _kern_name_ok(parts[0].strip() if isinstance(parts[0], str) else parts[0])
                    or not _kern_name_ok(parts[1].strip() if isinstance(parts[1], str) else parts[1])):
                return _kern_bad(f"pair {i + 1} ({raw_items[i]!r}) must look like NAME:NAME with glyph names of 1 to 63 characters from A-Z a-z 0-9 . _ -")
            wanted.append({"left": parts[0].strip(), "right": parts[1].strip()})
    else:
        if not isinstance(text, str) or len(text) < 2:
            return _kern_bad(f"text: at least 2 characters are needed (got {len(text) if isinstance(text, str) else type(text).__name__})")
        if any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in text):
            return _kern_bad("text must not contain control characters")
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    _note_request_font(font, count)
    if count is None:
        return {"open": True, "error": "the number of open fonts could not be read (CountFonts() gave no plain number), so the kerning table "
                                       "cannot be matched to the current font"}
    if count < 1:
        return {"open": True, "error": f"CountFonts() gave {count}, so the kerning table cannot be matched to the current font"}
    target, why = _kern_table_target(font, count)
    if target is None:
        return {"open": True, "error": why}
    pkg, masters, master, kerning = target["pkg"], target["masters"], target["master"], target["kerning"]
    getter, glyphs, by_name, matched_by = target["getter"], target["glyphs"], target["by_name"], target["matched_by"]
    if have_text:
        need = set(ord(ch) for ch in text)
        holders = dict((cp, []) for cp in need)
        unreadable = 0
        for g in glyphs:
            try:
                u = g.unicode
                gname = str(g.name)
            except Exception:
                unreadable += 1
                continue
            if isinstance(u, int) and not isinstance(u, bool) and u in holders:
                holders[u].append(gname)

        def _resolve(ch):
            cp = ord(ch)
            hit = holders[cp]
            label = f"character {ch!r} (U+{cp:04X})"
            if len(hit) == 1:
                return hit[0], None
            if not hit:
                extra = f"; {unreadable} glyphs could not be read, so this is no proof that none has it" if unreadable else ""
                return None, f"{label}: no glyph has this codepoint as its primary Unicode{extra}"
            return None, f"{label}: several glyphs have this codepoint ({', '.join(hit[:5])}), which one is meant is not known"

        for i in range(len(text) - 1):
            la, ea = _resolve(text[i])
            lb, eb = _resolve(text[i + 1])
            entry = {"chars": text[i] + text[i + 1], "left": la, "right": lb}
            problems = [e for e in (ea, eb) if e]
            if problems:
                entry["error"] = "; ".join(problems)
            wanted.append(entry)
    else:
        for entry in wanted:
            missing = [nm for nm in (entry["left"], entry["right"]) if nm not in by_name]
            if missing:
                entry["error"] = "no glyph named " + ", ".join(repr(m) for m in missing)
    groups = {}                                  # ONE getAllGroups() per request, and only when a class id is not 0
    len_before = _kern_len(kerning)
    for entry in wanted:
        if "error" in entry:
            continue
        entry.update(_kern_effective(getter, by_name, pkg, groups, entry["left"], entry["right"]))
    len_after = _kern_len(kerning)
    upm = None
    try:
        raw_upm = font.info.unitsPerEm
        if isinstance(raw_upm, (int, float)) and not isinstance(raw_upm, bool):
            upm = raw_upm
    except Exception:
        upm = None
    family = _kern_family(font)
    return {"open": True, "mode": "text" if have_text else "pairs", "fonts_open": count, "matched_by": matched_by, "family_name": family,
            "master": master, "master_count": len(masters), "units_per_em": upm, "count": len(wanted), "errors": sum(1 for e in wanted if "error" in e), "table_size": len_before,
            "side_effect_detected": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
            "results": wanted}


# --------------------------------------------------------------------------
# /kerning/groups (v0.190, P1.6) - READ ONLY: the kerning groups of the current master, with their members and sides. The user's design
# of 2026-11-19 (DECISIONS.md): a tool of its own; named groups or glyphs, or every group (approval above 250 groups); members always
# included; kerning groups only (OpenType classes and Glyph tags are not); every read cross-checked with getAllGroups(); an unknown
# name is an error for that name only. Exactly two FontLab calls per request (KG 1364-1375, topics/kerning.md section 9.10):
#   ONE flPackage.kerning(master).groups.items()  ->  [(name, (members, side))]  side KernLeft | KernRight | KernBothSide
#   ONE flPackage.getAllGroups()                  ->  [(kernGroup, name, id, mark, members)]  (OpenType classes: kernGroup False)
# A group is confirmed when both name it with the same members (order aside) and the flag is True. Only real lists and tuples are
# looked into (exact types); nothing in an entry is called; the table's and the container's sizes are read before and after.
# --------------------------------------------------------------------------

_KGR_SIDES = {"KernLeft": "left", "KernRight": "right", "KernBothSide": "both"}
_KGR_CONFIRM_ABOVE = 250     # more groups than this in an all-groups read need confirmed_large_read (the user's rule of 2026-10-27)


def _kgr_seq(value):
    """True only for a real Python list or tuple (exact type): a native object is never iterated."""
    return type(value) in (list, tuple)


def _kgr_names(value):
    """A real list or tuple of glyph names as a plain list, or None when it is not one or holds anything but text."""
    if not _kgr_seq(value):
        return None
    names = [n for n in value if type(n) is str]
    return names if len(names) == len(value) else None


def _kgr_from_items(container):
    """({name: {"side", "fontlab_side", "members"}}, duplicate names, malformed count, None) or (None, None, None, error text), from
    ONE items() on the master's kerning groups."""
    try:
        items_of = container.items
        if not callable(items_of):
            return None, None, None, "the kerning groups' items is not callable"
        entries = items_of()
    except Exception as exc:
        return None, None, None, f"the kerning groups' items() failed ({type(exc).__name__}: {exc})"
    if not _kgr_seq(entries):
        return None, None, None, f"the kerning groups' items() returned a {type(entries).__name__}, not a list"
    found, twice, malformed = {}, set(), 0
    for entry in entries:
        if not _kgr_seq(entry) or len(entry) != 2 or type(entry[0]) is not str or not _kgr_seq(entry[1]) or len(entry[1]) != 2:
            malformed += 1
            continue
        name, (members, mode) = entry[0], entry[1]
        names = _kgr_names(members)
        if names is None or type(mode) is not str:
            malformed += 1
            continue
        if name in found:
            twice.add(name)
        found[name] = {"side": _KGR_SIDES.get(mode, "unknown"), "fontlab_side": mode, "members": names}
    return found, twice, malformed, None


def _kgr_from_class_list(pkg):
    """({name: {"id", "members"}} of the KERNING groups, duplicate names, {names of other classes}, None) or (None, None, None, error
    text), from ONE getAllGroups() of the package."""
    try:
        getter = pkg.getAllGroups
        if not callable(getter):
            return None, None, None, "flPackage.getAllGroups is not callable"
        groups = getter()
    except Exception as exc:
        return None, None, None, f"flPackage.getAllGroups() failed ({type(exc).__name__}: {exc})"
    if not _kgr_seq(groups):
        return None, None, None, f"flPackage.getAllGroups() returned a {type(groups).__name__}, not a list"
    found, twice, other = {}, set(), set()
    for entry in groups:
        if not _kgr_seq(entry) or len(entry) != 5:
            continue
        flag, name, gid, _mark, members = entry
        if type(name) is not str:
            continue
        if flag is not True:
            other.add(name)
            continue
        if name in found:
            twice.add(name)
        found[name] = {"id": gid if type(gid) is int else None, "members": _kgr_names(members)}
    return found, twice, other, None


def _kgr_group(name, from_items, from_list, cross_error, twice=frozenset()):
    """One group's entry: its facts from items(), its id from the class list, and whether both sources agree (confirmed). A name
    that either source lists twice is never confirmed."""
    a, b = from_items.get(name), (from_list or {}).get(name)
    entry = {"name": name}
    if a is not None:
        entry.update(side=a["side"], fontlab_side=a["fontlab_side"], members=a["members"], member_count=len(a["members"]))
    elif b is not None and b["members"] is not None:
        entry.update(side="unknown", fontlab_side=None, members=b["members"], member_count=len(b["members"]))
    entry["id"] = b["id"] if b is not None else None
    if cross_error is not None:
        entry.update(confirmed=False, mismatch="the class list could not be read, so this group could not be cross-checked")
    elif name in twice:
        entry.update(confirmed=False, mismatch="FontLab lists this group name twice, so which entry is meant is not known")
    elif a is None:
        entry.update(confirmed=False, mismatch="FontLab's class list names this kerning group, but the master's kerning groups do not hold it")
    elif b is None:
        entry.update(confirmed=False, mismatch="the master's kerning groups hold this group, but FontLab's class list does not name it as a kerning group")
    elif b["members"] is None or sorted(b["members"]) != sorted(a["members"]):
        entry.update(confirmed=False, mismatch="the two sources list different members", class_list_members=b["members"])
    elif a["side"] == "unknown":
        entry.update(confirmed=False, mismatch=f"the side {a['fontlab_side']!r} is not one this listener knows")
    else:
        entry["confirmed"] = True
    return entry


def get_kerning_groups(groups=None, glyphs=None, all_groups=False, confirmed=False):
    """v0.190 - READ-ONLY kerning groups of the current master's kerning table of the current font, matched as /kerning/pairs matches
    it (_kern_table_target). Either all_groups alone, or names in groups and / or glyphs (A-Z a-z 0-9 . _ -, 1 to 63 characters).
    groups: each named kerning group with side, members, id, confirmed. glyphs: each named glyph's kerning groups with their sides.
    all_groups: every kerning group; more than _KGR_CONFIRM_ABOVE need confirmed, otherwise only the count comes back. An unknown
    name is an error for that name only. OpenType classes and Glyph tags are not kerning groups: a name of one says so."""
    groups = [] if groups is None else groups        # never a truth test: that would call len() on whatever was passed
    glyphs = [] if glyphs is None else glyphs
    if type(all_groups) is not bool or type(confirmed) is not bool:
        return _kern_bad("all_groups and confirmed must be true or false")
    if not _kgr_seq(groups) or not _kgr_seq(glyphs):
        return _kern_bad("groups and glyphs must be lists of names")
    if all_groups and (groups or glyphs):
        return _kern_bad("all_groups stands alone: give either all_groups, or groups and / or glyphs")
    if not all_groups and not groups and not glyphs:
        return _kern_bad("give all_groups, or at least one name in groups or glyphs")
    for kind, names in (("group", groups), ("glyph", glyphs)):
        for n in names:
            if not _kern_name_ok(n):
                return _kern_bad(f"{kind} name {n!r} must be 1 to 63 characters from A-Z a-z 0-9 . _ -")
    groups = list(dict.fromkeys(groups))
    glyphs = list(dict.fromkeys(glyphs))
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    _note_request_font(font, count)
    if count is None or count < 1:
        return {"open": True, "error": "the number of open fonts could not be read as a positive number, so the kerning groups cannot be "
                                       "matched to the current font"}
    target, why = _kern_table_target(font, count)
    if target is None:
        return {"open": True, "error": why}
    pkg, masters, master, kerning, by_name = target["pkg"], target["masters"], target["master"], target["kerning"], target["by_name"]
    try:
        container = kerning.groups
    except Exception as exc:
        return {"open": True, "error": f"the kerning groups of master {master!r} are not reachable: {type(exc).__name__}: {exc}"}
    if callable(container):
        return {"open": True, "error": "the master's kerning groups attribute is callable; it was not called"}
    len_before, groups_before = _kern_len(kerning), _kern_len(container)
    from_items, items_twice, malformed, items_error = _kgr_from_items(container)
    from_list, list_twice, other_classes, list_error = _kgr_from_class_list(pkg)
    len_after, groups_after = _kern_len(kerning), _kern_len(container)
    side_effect = None
    if None not in (len_before, len_after, groups_before, groups_after):
        side_effect = len_before != len_after or groups_before != groups_after
    out = {"open": True, "fonts_open": count, "matched_by": target["matched_by"], "family_name": _kern_family(font), "master": master,
           "master_count": len(masters), "table_size": len_before, "side_effect_detected": side_effect}
    if items_error is not None:
        out["error"] = f"the kerning groups could not be read: {items_error}"
        return out
    names_all = list(from_items) + [n for n in (from_list or {}) if n not in from_items]
    twice = items_twice | (list_twice or set())
    out.update(group_count=len(names_all), cross_check="done" if list_error is None else f"failed: {list_error}",
               malformed_entries=malformed, duplicate_names=sorted(twice))
    if all_groups:
        out["mode"] = "all"
        if len(names_all) > _KGR_CONFIRM_ABOVE and not confirmed:
            out["needs_confirmation"] = True
            return out
        out["groups"] = [_kgr_group(n, from_items, from_list, list_error, twice) for n in names_all]
        out["glyphs"] = []
    else:
        out["mode"] = "named"
        listed = []
        for n in groups:
            if n in from_items or n in (from_list or {}):
                listed.append(_kgr_group(n, from_items, from_list, list_error, twice))
            elif n in (other_classes or set()):
                listed.append({"name": n, "error": f"{n!r} is a class but not a kerning group (an OpenType class or a tag): this tool reads kerning groups only"})
            else:
                listed.append({"name": n, "error": f"no kerning group named {n!r} in the current master of this font"})
        out["groups"] = listed
        found = []
        for g in glyphs:
            if g not in by_name:
                found.append({"name": g, "error": f"no glyph named {g!r}"})
                continue
            holders = []
            for n in names_all:
                a, b = from_items.get(n), (from_list or {}).get(n)
                if (a is not None and g in a["members"]) or (b is not None and b["members"] is not None and g in b["members"]):
                    e = _kgr_group(n, from_items, from_list, list_error, twice)
                    holders.append({"group": n, "side": e.get("side", "unknown"), "confirmed": e["confirmed"]})
            item = {"name": g, "kerning_groups": holders}
            if not holders:
                item["note"] = "in no kerning group on either side"
            found.append(item)
        out["glyphs"] = found
    out["errors"] = sum(1 for e in out["groups"] + out["glyphs"] if "error" in e)
    out["member_names"] = sum(e.get("member_count", 0) for e in out["groups"])
    return out


def _other_glyphs_with_unicode(font, name, codepoint):
    """READ-ONLY scan: which glyphs OTHER than `name` have `codepoint` as their primary Unicode?

    FontLab accepts a second glyph with the same codepoint without complaint (seen live), so this is the only
    way an agent can learn about it. Glyphs that cannot be read are COUNTED ("unreadable"), never skipped
    silently: no evidence, no claim. Only glyph.unicode (the primary codepoint) is read; additional codepoints
    a glyph may carry are not looked at."""
    try:
        glyphs = list(font.glyphs)
    except Exception as exc:
        return {"scanned": 0, "also_held_by": [], "unreadable": 0, "scan_error": str(exc)}
    holders, scanned, unreadable = [], 0, 0
    for g in glyphs:
        try:
            gname = str(g.name)
            if gname == name:
                continue
            raw = g.unicode
        except Exception:
            unreadable += 1
            continue
        scanned += 1
        if raw == codepoint:
            holders.append(gname)
    return {"scanned": scanned, "also_held_by": holders, "unreadable": unreadable}


_KERN_CLASS_SOURCES = ("glyph : class", "class : glyph", "class : class")


def _kern_exact(getter, key):
    """(value, None) or (None, error text): ONE get of an exact entry; (None, None) means FontLab has no such entry."""
    try:
        value = getter(key)
    except Exception as exc:
        return None, f"kerning.get raised {type(exc).__name__}: {exc}"
    if value is None or _kern_value_ok(value):
        return value, None
    return None, f"kerning.get returned {type(value).__name__} {value!r}, not a finite number"


# --------------------------------------------------------------------------
# v0.194 - class sides in /kerning/set and /kerning/remove (the design of 2026-11-20, DECISIONS.md; research CW 1409-1417,
# topics/kerning.md section 17). A side written '@name' names a kerning group; any other side is a glyph, exactly as before, so a
# glyph-only request takes the same path, calls and reply. A request with a class side reads ONE getAllGroups() and ONE items() on
# the master's kerning groups before the first write; each class must be confirmed by both and stand on a side that fits. The key
# is ((name, isClass), (name, isClass)). Each class pair is verified by its exact entry and by ONE sample glyph pair (the first
# member of each class side that is a glyph of the font), read with _kern_effective before and after: the sample takes the value
# from the new entry ("applied"), or an entry of higher rank of its own answers it ("covered", an exception), else the pair fails.
# --------------------------------------------------------------------------

_KERN_KIND_RANK = {"glyph : glyph": 0, "glyph : class": 1, "class : glyph": 2, "class : class": 3}     # FontLab's order (section 9.9)


def _kern_side_ok(name):
    """A glyph name, or '@' and a kerning group name, each 1 to 63 characters from A-Z a-z 0-9 . _ - (v0.194)."""
    return isinstance(name, str) and (_kern_name_ok(name) or (name[:1] == "@" and _kern_name_ok(name[1:])))


def _kern_kind(left, right):
    """The kind of entry a pair names (v0.194)."""
    return ("class" if left[:1] == "@" else "glyph") + " : " + ("class" if right[:1] == "@" else "glyph")


def _kern_class_targets(pkg, kerning, sides, by_name):
    """({group name: {"side", "member_count", "sample"}}, None) or (None, error text), v0.194. sides: (side, '@name') of every class
    side of the request. ONE getAllGroups() (_trysetkern_group_names: any entry of an unknown shape refuses) and ONE items() on the
    master's kerning groups (_kgr_from_items, never called on the container itself); each group must be a kerning group of the class
    list, confirmed by both sources (_kgr_group) and of a side that fits the side it stands on. sample: its first member that is a
    glyph of the font, or None."""
    all_names, kern, list_twice, err = _trysetkern_group_names(pkg)
    if err is not None:
        return None, f"FontLab's class list could not be read ({err})"
    for side, raw in sides:
        if raw[1:] not in kern:
            what = "is a class of the font but not a kerning group" if raw[1:] in all_names else "is not the name of any kerning group of the font"
            return None, f"{raw!r} on the {side} side {what}"
    try:
        container = kerning.groups
    except Exception as exc:
        return None, f"the master's kerning groups are not reachable ({type(exc).__name__}: {exc})"
    if callable(container):
        return None, "the master's kerning groups attribute is callable; it was not called"
    from_items, items_twice, _malformed, err = _kgr_from_items(container)
    if err is not None:
        return None, err
    found = {}
    for side, raw in sides:
        g = _kgr_group(raw[1:], from_items, kern, None, items_twice | list_twice)
        if g.get("confirmed") is not True:
            return None, f"the kerning group {raw!r} is not confirmed by both of FontLab's sources ({g.get('mismatch')})"
        if g.get("side") not in _TRYKERN_SIDE_FITS[side]:
            return None, f"the kerning group {raw!r} is a {g.get('side')} group, so it cannot stand on the {side} side of a pair"
        members = g.get("members") or []
        found[raw[1:]] = {"side": g.get("side"), "member_count": len(members), "sample": next((m for m in members if m in by_name), None)}
    return found, None


def _kern_sample(left, right, classes):
    """The sample glyph pair of a pair with a class side (v0.194): a glyph side is itself, a class side its group's sample; None when
    a class has no member that is a glyph of the font."""
    a = classes[left[1:]]["sample"] if left[:1] == "@" else left
    b = classes[right[1:]]["sample"] if right[:1] == "@" else right
    return {"left": a, "right": b} if a is not None and b is not None else None


def _kern_sample_verdict(kind, left, right, value, after):
    """'applied' when the sample takes value from the new entry (its kind and its classes), 'covered' when an entry of higher rank
    answers for the sample (its own exception), otherwise None (v0.194)."""
    source = after.get("source")
    if (source == kind and after.get("value") == value and (left[:1] != "@" or after.get("left_class") == left[1:])
            and (right[:1] != "@" or after.get("right_class") == right[1:])):
        return "applied"
    if source in _KERN_KIND_RANK and _KERN_KIND_RANK[source] < _KERN_KIND_RANK[kind]:
        return "covered"
    return None


def _kern_same_name_notes(results, groups):
    """v0.194: a glyph side whose name is also a kerning group's name gets same_name_group (the reply's note: write '@name' to kern
    the group). Only the class list a request already read is used (groups, read by _kern_effective when a glyph of the request has a
    class id): no FontLab call is added, so a glyph in no kerning group gets no note."""
    found = groups.get("answer")
    if not found or found[1] is not None:
        return
    names = {found[0][0][gid] for gid in found[0][0]}
    for entry in results:
        hits = [side for side in ("left", "right") if entry.get(side, "@")[:1] != "@" and entry.get(side) in names]
        if hits:
            entry["same_name_group"] = hits


def set_kerning_pairs(pairs):
    """v0.124 - WRITES glyph : glyph kerning pairs into the current master's table of the current font (P2.9; research KW
    542-564, topics/kerning.md section 13). pairs: a list of [left, right, value], each pair once; since v0.194 a side written
    '@name' is a kerning group (the class-side block above _KERN_KIND_RANK); what follows describes a glyph : glyph pair. Every
    check runs before the first write, and a failed one refuses the whole request with nothing set: the font and its table are
    matched as /kerning/pairs matches them (_kern_table_target), both names are glyphs of the font, and |value| <= the
    package's upm. Then per pair, in order: the effective value before (_kern_effective, as /kerning/pairs reads it) and the
    exact entry, ONE set(((left, False), (right, False)), float(value)) - the flags form names both sides as glyphs, so a glyph
    named like a class never means that class (defect B; set accepts the form, test 564) - then the exact entry and the
    effective value again. A pair is "set" only when the call raised nothing, the exact entry equals the value and FontLab
    applies that value from the glyph : glyph entry. The first pair that is not set stops the request; the pairs after it are
    "not attempted". changed says whether the exact entry changed (None: it could not be read back). len() is read before and
    after; table_size_as_expected compares the growth with the new entries. Kerning members used: get, set (one per pair) and
    len(); never remove, clear, setPlainPairs, add*, delete*, rename*, scale or a whole-table read; no Update(),
    font.update() or save. FontLab's KERNING panel does not list such a pair by itself (557-560), so since v0.136 a write that changed an entry
    asks it to refresh (_refresh_kerning_panel, 738, 741-743); without a notification,
    closing the font asks no save question and loses it (561, 562), so since v0.134 a write that changed an entry makes one
    (_mark_font_changed_after_kerning, research 713-717); Edit > Undo does not take it back (563)."""
    if not isinstance(pairs, list) or not pairs:
        return _kern_bad('"pairs" must be a non-empty list of [left, right, value]')
    wanted, seen = [], set()
    for i, item in enumerate(pairs):
        if not isinstance(item, list) or len(item) != 3 or not _kern_side_ok(item[0]) or not _kern_side_ok(item[1]):
            return _kern_bad(f"pair {i + 1} must be [left, right, value] with two glyph names of 1 to 63 characters from A-Z a-z 0-9 . _ -")
        if not _kern_value_ok(item[2]):
            return _kern_bad(f"pair {i + 1} ({item[0]}:{item[1]}): the value must be a finite number")
        if (item[0], item[1]) in seen:
            return _kern_bad(f"pair {i + 1} ({item[0]}:{item[1]}) is asked more than once in this request")
        seen.add((item[0], item[1]))
        wanted.append((item[0], item[1], item[2]))
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    _note_request_font(font, count)
    if count is None or count < 1:
        return {"open": True, "error": "the number of open fonts could not be read as a positive number, so the kerning table cannot be "
                                       "matched to the current font; nothing was set"}
    target, why = _kern_table_target(font, count)
    if target is None:
        return {"open": True, "error": f"{why}; nothing was set"}
    pkg, master, kerning, getter, by_name = target["pkg"], target["master"], target["kerning"], target["getter"], target["by_name"]
    upm, err = _pkg_get(pkg, "upm")
    if err is not None or not _kern_value_ok(upm) or not upm > 0:
        return {"open": True, "error": "the font's units per em could not be read as a positive number, so the values cannot be checked; nothing was set"}
    missing = sorted(set(nm for a, b, _v in wanted for nm in (a, b) if nm[:1] != "@" and nm not in by_name))
    if missing:
        return {"open": True, "error": "no glyph named " + ", ".join(repr(m) for m in missing) + " in the current font; nothing was set"}
    too_big = [f"{a}:{b} {v}" for a, b, v in wanted if abs(v) > upm]
    if too_big:
        return {"open": True, "error": f"larger than the font's {upm:g} units per em, either way: " + ", ".join(too_big[:5]) + "; nothing was set"}
    class_sides = [(side, nm) for a, b, _v in wanted for side, nm in (("left", a), ("right", b)) if nm[:1] == "@"]
    classes = {}
    if class_sides:                              # v0.194: only a request with a class side reads the groups here
        classes, why = _kern_class_targets(pkg, kerning, class_sides, by_name)
        if classes is None:
            return {"open": True, "error": f"{why}; nothing was set"}
    try:
        setter = kerning.set
    except Exception as exc:
        return {"open": True, "error": f"the kerning table's set is not reachable ({type(exc).__name__}: {exc}); nothing was set"}
    if not callable(setter):
        return {"open": True, "error": "the kerning table's set is not callable; nothing was set"}
    groups = {}
    len_before = _kern_len(kerning)
    results, stopped, new_entries = [], False, 0
    for left, right, value in wanted:
        entry = {"left": left, "right": right, "requested": value}
        results.append(entry)
        if stopped:
            entry["status"] = "not attempted"
            continue
        kind = _kern_kind(left, right)
        key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))
        sample = {"left": left, "right": right}
        if kind != "glyph : glyph":                  # v0.194: a class side is checked through one sample glyph pair
            sample = _kern_sample(left, right, classes)
            entry.update(kind=kind, classes={nm[1:]: {k: classes[nm[1:]][k] for k in ("side", "member_count")} for nm in (left, right) if nm[:1] == "@"},
                         sample=sample)
        before = _kern_effective(getter, by_name, pkg, groups, sample["left"], sample["right"]) if sample else {}
        exact_before, err_before = _kern_exact(getter, key)
        if sample:
            entry["before"] = before
        if "error" in before or err_before is not None:
            entry.update(status="failed", set=False, changed=False,
                         reason="the value before could not be read, so nothing was set for this pair: " + (before.get("error") or err_before))
            stopped = True
            continue
        call_error = None
        try:
            setter(key, float(value))
        except Exception as exc:
            call_error = f"{type(exc).__name__}: {exc}"
        exact_after, err_after = _kern_exact(getter, key)
        after = _kern_effective(getter, by_name, pkg, groups, sample["left"], sample["right"]) if sample else {}
        if sample:
            entry["after"] = after
        if err_after is not None:
            new_entries = None                   # whether this pair added an entry is unknown, so the growth cannot be checked
        elif exact_before is None and exact_after is not None and new_entries is not None:
            new_entries += 1
        verdict = None
        if kind == "glyph : glyph":
            ok = (call_error is None and err_after is None and exact_after == value
                  and after.get("source") == "glyph : glyph" and after.get("value") == value)
        else:
            verdict = _kern_sample_verdict(kind, left, right, value, after) if sample else "no sample"
            entry["sample_verdict"] = verdict
            entry["entry_before"] = exact_before         # the class entry's own value before (None: no entry), for a revert
            ok = call_error is None and err_after is None and exact_after == value and verdict is not None
        entry.update(status="set" if ok else "failed", set=ok, changed=None if err_after is not None else exact_after != exact_before)
        if kind == "glyph : glyph":
            entry["exception_over_class"] = before.get("source") in _KERN_CLASS_SOURCES
        if call_error is not None:
            entry["call_error"] = call_error
        if not ok:
            if call_error is not None:
                why = f"kerning.set raised {call_error}"
            elif err_after is not None:
                why = f"the entry could not be read back: {err_after}"
            elif exact_after != value:
                why = f"the entry reads {exact_after!r} after setting, not {value}"
            elif "error" in after:
                why = f"the value FontLab applies could not be read back: {after['error']}"
            else:
                if kind == "glyph : glyph":
                    why = f"FontLab applies {after.get('value')} from the {after.get('source')} entry, not the new {kind} entry"
                else:
                    named = " : ".join(after[k] for k in ("left_class", "right_class") if isinstance(after.get(k), str))
                    why = (f"FontLab applies {after.get('value')} from the {after.get('source')} entry" + (f" of {named}" if named else "")
                           + f", not the new {kind} entry (sample pair {sample['left']}:{sample['right']})")
            entry["reason"] = why
            stopped = True
    len_after = _kern_len(kerning)
    _kern_same_name_notes(results, groups)
    mark = _mark_font_changed_after_kerning(font, results)
    refresh = _refresh_kerning_panel(pkg, results)      # after the mark, so that a repaint comes after FontLab has counted the change
    return {"open": True, "fonts_open": count, "matched_by": target["matched_by"], "family_name": _kern_family(font), "master": master,
            "master_count": len(target["masters"]), "units_per_em": upm, "count": len(results),
            "set_count": sum(1 for e in results if e.get("set") is True), "stopped": stopped,
            "table_size_before": len_before, "table_size_after": len_after,
            "table_size_as_expected": (len_after - len_before == new_entries) if None not in (len_before, len_after, new_entries) else None,
            "results": results, "fontlab_changed_mark": mark, "fontlab_panel_refresh": refresh}


def remove_kerning_pairs(pairs):
    """v0.192 - REMOVES glyph : glyph kerning entries from the current master's table of the current font (the design of 2026-11-19,
    DECISIONS.md; research KD 1380-1390, KDC 1391-1397, topics/kerning.md section 16). pairs: a list of [left, right], each pair once;
    since v0.194 a side written '@name' is a kerning group (the class-side block above _KERN_KIND_RANK); what follows describes a
    glyph : glyph pair. Every check runs before the first removal, and a failed one refuses the whole request with nothing removed: the font
    and its table are matched as /kerning/pairs matches them (_kern_table_target), both names are glyphs of the font, and remove is
    reachable. Then per pair, in order: the effective value before (_kern_effective) and the exact glyph : glyph entry. No such entry:
    "no entry", nothing called, and the request goes on (the class and value that still apply are in 'before'). Otherwise ONE
    remove(((left, False), (right, False))) - the flags form names both sides as glyphs (defect B); its return value says nothing about
    the outcome (True for the tuple form, None for this one, 1387 against 1390) and is ignored - then the exact entry, len() and the
    effective value again. A pair is "removed" only when the call raised nothing, the exact entry reads None and len() dropped by exactly
    one; class_value_applies says that a class value applies after it (KDC 1396). The first pair not confirmed stops the request; the
    pairs after it are "not attempted". Kerning members used: get, remove (one per pair with an entry) and len(); never set, clear,
    setPlainPairs, add*, delete*, rename*, scale or a whole-table read; no Update(), font.update() or save. After a removal that changed
    the table: the mark (_mark_font_changed_after_kerning) and the panel refresh (_refresh_kerning_panel), as set_kerning_pairs; the panel
    keeps a removed row without the refresh (1385, 1386). Edit > Undo is not known to take it back."""
    if not isinstance(pairs, list) or not pairs:
        return _kern_bad('"pairs" must be a non-empty list of [left, right]')
    wanted, seen = [], set()
    for i, item in enumerate(pairs):
        if not isinstance(item, list) or len(item) != 2 or not _kern_side_ok(item[0]) or not _kern_side_ok(item[1]):
            return _kern_bad(f"pair {i + 1} must be [left, right] with two glyph names of 1 to 63 characters from A-Z a-z 0-9 . _ -")
        if (item[0], item[1]) in seen:
            return _kern_bad(f"pair {i + 1} ({item[0]}:{item[1]}) is asked more than once in this request")
        seen.add((item[0], item[1]))
        wanted.append((item[0], item[1]))
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    _note_request_font(font, count)
    if count is None or count < 1:
        return {"open": True, "error": "the number of open fonts could not be read as a positive number, so the kerning table cannot be "
                                       "matched to the current font; nothing was removed"}
    target, why = _kern_table_target(font, count)
    if target is None:
        return {"open": True, "error": f"{why}; nothing was removed"}
    pkg, master, kerning, getter, by_name = target["pkg"], target["master"], target["kerning"], target["getter"], target["by_name"]
    missing = sorted(set(nm for a, b in wanted for nm in (a, b) if nm[:1] != "@" and nm not in by_name))
    if missing:
        return {"open": True, "error": "no glyph named " + ", ".join(repr(m) for m in missing) + " in the current font; nothing was removed"}
    class_sides = [(side, nm) for a, b in wanted for side, nm in (("left", a), ("right", b)) if nm[:1] == "@"]
    classes = {}
    if class_sides:                              # v0.194: only a request with a class side reads the groups here
        classes, why = _kern_class_targets(pkg, kerning, class_sides, by_name)
        if classes is None:
            return {"open": True, "error": f"{why}; nothing was removed"}
    try:
        remover = kerning.remove
    except Exception as exc:
        return {"open": True, "error": f"the kerning table's remove is not reachable ({type(exc).__name__}: {exc}); nothing was removed"}
    if not callable(remover):
        return {"open": True, "error": "the kerning table's remove is not callable; nothing was removed"}
    groups = {}
    len_before = _kern_len(kerning)
    results, stopped = [], False
    for left, right in wanted:
        entry = {"left": left, "right": right}
        results.append(entry)
        if stopped:
            entry["status"] = "not attempted"
            continue
        kind = _kern_kind(left, right)
        key = ((left.lstrip("@"), left[:1] == "@"), (right.lstrip("@"), right[:1] == "@"))
        sample = {"left": left, "right": right}
        if kind != "glyph : glyph":                  # v0.194: what applies after is shown on one sample glyph pair
            sample = _kern_sample(left, right, classes)
            entry.update(kind=kind, classes={nm[1:]: {k: classes[nm[1:]][k] for k in ("side", "member_count")} for nm in (left, right) if nm[:1] == "@"},
                         sample=sample)
        before = _kern_effective(getter, by_name, pkg, groups, sample["left"], sample["right"]) if sample else {}
        exact_before, err_before = _kern_exact(getter, key)
        if sample:
            entry["before"] = before
        if "error" in before or err_before is not None:
            entry.update(status="failed", removed=False, changed=False,
                         reason="the value before could not be read, so nothing was removed for this pair: " + (before.get("error") or err_before))
            stopped = True
            continue
        if exact_before is None:
            entry.update(status="no entry", removed=False, changed=False)
            continue
        if kind != "glyph : glyph":
            entry["entry_before"] = exact_before         # the class entry's own value, for a restore with /kerning/set
        size_before = _kern_len(kerning)
        call_error = None
        try:
            remover(key)
        except Exception as exc:
            call_error = f"{type(exc).__name__}: {exc}"
        exact_after, err_after = _kern_exact(getter, key)
        size_after = _kern_len(kerning)
        after = _kern_effective(getter, by_name, pkg, groups, sample["left"], sample["right"]) if sample else {}
        if sample:
            entry["after"] = after
        ok = (call_error is None and err_after is None and exact_after is None
              and type(size_before) is int and type(size_after) is int and size_after == size_before - 1)
        entry.update(status="removed" if ok else "failed", removed=ok, changed=None if err_after is not None else exact_after != exact_before,
                     class_value_applies=after.get("source") in _KERN_CLASS_SOURCES)
        if call_error is not None:
            entry["call_error"] = call_error
        if not ok:
            if call_error is not None:
                why = f"kerning.remove raised {call_error}"
            elif err_after is not None:
                why = f"the entry could not be read back: {err_after}"
            elif exact_after is not None:
                why = f"the entry still reads {exact_after!r} after removing it"
            elif type(size_before) is not int or type(size_after) is not int:
                why = "the size of the kerning table could not be read, so the removal of exactly one entry could not be confirmed"
            else:
                why = f"the kerning table went from {size_before} to {size_after} entries, not one fewer"
            entry["reason"] = why
            stopped = True
    len_after = _kern_len(kerning)
    removed_count = sum(1 for e in results if e.get("removed") is True)
    _kern_same_name_notes(results, groups)
    mark = _mark_font_changed_after_kerning(font, results)
    refresh = _refresh_kerning_panel(pkg, results)      # after the mark, as in set_kerning_pairs
    return {"open": True, "fonts_open": count, "matched_by": target["matched_by"], "family_name": _kern_family(font), "master": master,
            "master_count": len(target["masters"]), "count": len(results), "removed_count": removed_count,
            "no_entry_count": sum(1 for e in results if e.get("status") == "no entry"), "stopped": stopped,
            "table_size_before": len_before, "table_size_after": len_after,
            "table_size_as_expected": (len_before - len_after == removed_count) if None not in (len_before, len_after) else None,
            "results": results, "fontlab_changed_mark": mark, "fontlab_panel_refresh": refresh}


def _confirm_group_removal(text, seconds=_DIALOG_SECONDS_DEFAULT):
    """v0.200 - the Yes/No dialog in FontLab before a kerning group is removed (default No); since v0.203 _ask_yes_no's dialog, which
    closes by itself after `seconds`. Returns _ask_yes_no's result. The section below (remove_kerning_group) uses it."""
    return _ask_yes_no("Glyphbridge: Confirm Kerning Group Removal", text, seconds, "removed")


# v0.200 - renaming and removing ONE kerning group of the current master (the design of 2026-11-20, DECISIONS.md; research GE0 1499-1504,
# GE 1505-1522, GR 1523-1529, GL 1530-1534, GK 1535-1545, topics/kerning.md section 18). The font and its table are matched as /kerning/pairs
# matches them (_kern_table_target). The group must be a kerning group confirmed by ONE items() of the master's group container and ONE
# getAllGroups() (_kgr_group); then ONE call on the container: rename(group, new_name), or remove(group) / remove(group, True). The outcome
# comes from re-reading both sources and the sizes of the table and the container, never from the return value. After a change: the mark
# through one member glyph (_mark_through_first) and ONE notifyPackageContentUpdated(<package fgId>) (_refresh_kerning_panel; without it
# FontLab's panels and the glyphs' group ids lag until a font switch, GE 1512-1516; with it they caught up, GR 1528-1529, GL 1533, GK 1544).
# Then the catch-up check: ONE read of one member glyph's legacy kerningLeft / kerningRight (the read get_kerning makes), expected to name
# the new id after a rename and 0 after a removal. A rename gives the group a new id (GE 1511, GR 1525). getAllGroups() returns None when the
# font has no group left (documented ".../Nothing", seen GL 1531): here that is read as an empty list. Container members used: items, rename,
# remove; never a subscript, del, clear, the legacy addGroup / deleteGroup / renameGroup, flPackage.deleteGroups, a kerning setter, a
# whole-table read, Update() or a save.

_KGE_MEMBERS_SHOWN = 8          # members named in the removal dialog; the rest are counted


def _kge_class_list(pkg):
    """_kgr_from_class_list, except that None from getAllGroups() is an empty list (".../Nothing": the font has no group, GL 1531)."""
    try:
        getter = pkg.getAllGroups
        if not callable(getter):
            return None, None, None, "flPackage.getAllGroups is not callable"
        groups = getter()
    except Exception as exc:
        return None, None, None, f"flPackage.getAllGroups() failed ({type(exc).__name__}: {exc})"
    if groups is None:
        return {}, set(), set(), None
    if not _kgr_seq(groups):
        return None, None, None, f"flPackage.getAllGroups() returned a {type(groups).__name__}, not a list"
    found, twice, other = {}, set(), set()
    for entry in groups:
        if not _kgr_seq(entry) or len(entry) != 5:
            continue
        flag, gname, gid, _mark, members = entry
        if type(gname) is not str:
            continue
        if flag is not True:
            other.add(gname)
            continue
        if gname in found:
            twice.add(gname)
        found[gname] = {"id": gid if type(gid) is int else None, "members": _kgr_names(members)}
    return found, twice, other, None


def _kge_read(container, pkg):
    """Both group sources and the container's size: {"items", "items_twice", "items_error", "list", "list_twice", "other", "list_error"}."""
    items, items_twice, _malformed, items_error = _kgr_from_items(container)
    found, list_twice, other, list_error = _kge_class_list(pkg)
    return {"items": items, "items_twice": items_twice, "items_error": items_error, "list": found, "list_twice": list_twice,
            "other": other, "list_error": list_error}


def _kge_open(group, verb):
    """(context, None) or (None, reply): the checks shared by both edits, before any change. context: font, count, target, container,
    sizes and the confirmed group entry (before)."""
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return None, {"open": False}
    font = fl.CurrentFont()
    if font is None:
        return None, {"open": False}
    _note_request_font(font, count)
    if count is None or count < 1:
        return None, {"open": True, "error": "the number of open fonts could not be read as a positive number, so the kerning groups cannot be "
                                             f"matched to the current font; nothing was {verb}"}
    target, why = _kern_table_target(font, count)
    if target is None:
        return None, {"open": True, "error": f"{why}; nothing was {verb}"}
    kerning, master = target["kerning"], target["master"]
    try:
        container = kerning.groups
    except Exception as exc:
        return None, {"open": True, "error": f"the kerning groups of master {master!r} are not reachable ({type(exc).__name__}: {exc}); nothing was {verb}"}
    if callable(container):
        return None, {"open": True, "error": f"the master's kerning groups attribute is callable; it was not called; nothing was {verb}"}
    table_before, groups_before = _kern_len(kerning), _kern_len(container)
    read = _kge_read(container, target["pkg"])
    if read["items_error"] is not None or read["list_error"] is not None:
        return None, {"open": True, "error": f"the kerning groups could not be read ({read['items_error'] or read['list_error']}); nothing was {verb}"}
    if group not in read["items"] and group not in read["list"]:
        what = ("is a class of the font but not a kerning group (an OpenType class or a tag)" if group in read["other"]
                else "is not the name of a kerning group in the current master of this font")
        return None, {"open": True, "error": f"{group!r} {what}; nothing was {verb}"}
    before = _kgr_group(group, read["items"], read["list"], None, read["items_twice"] | read["list_twice"])
    if before.get("confirmed") is not True:
        return None, {"open": True, "group_before": before,
                      "error": f"the kerning group {group!r} is not confirmed by both of FontLab's sources ({before.get('mismatch')}); nothing was {verb}"}
    return {"font": font, "count": count, "target": target, "container": container, "read": read, "before": before,
            "table_before": table_before, "groups_before": groups_before}, None


def _kge_reply(ctx, extra):
    """The fields every reply of the two edits carries, then extra."""
    target, font = ctx["target"], ctx["font"]
    out = {"open": True, "fonts_open": ctx["count"], "matched_by": target["matched_by"], "family_name": _kern_family(font),
           "master": target["master"], "master_count": len(target["masters"]), "group_before": ctx["before"]}
    out.update(extra)
    return out


def _kge_after_change(ctx, member_names, side, expected_id):
    """The mark, the refresh and the catch-up check after a change (in that order). expected_id: the group id one member glyph should
    now carry on the group's side (the new id after a rename, 0 after a removal). Never raises."""
    font, pkg = ctx["font"], ctx["target"]["pkg"]
    candidates = [n for n in member_names if n != ".notdef"][:_MARK_DELETE_MAX_TRIES]
    try:
        mark = (_mark_through_first(font, candidates, "kerning_group") if _MARK_CHANGED and candidates else
                {"called": False, "reason": "the changed mark is switched off in the listener" if not _MARK_CHANGED
                 else "the group has no member other than .notdef to take the mark"})
    except Exception as exc:
        mark = {"called": False, "reason": f"the mark failed ({type(exc).__name__}: {exc})"}
    refresh = _refresh_kerning_panel(pkg, [{"changed": True}])
    check = {"checked": False}
    try:
        by_name = ctx["target"]["by_name"]
        glyph_name = next((n for n in member_names if n in by_name), None)
        if glyph_name is None:
            check["reason"] = "no member of the group is a glyph of the font"
        elif type(expected_id) is not int:
            check["reason"] = "the id to expect could not be read"
        else:
            attr = "kerningRight" if side == "right" else "kerningLeft"
            value, err = _kern_class_id(by_name[glyph_name], attr)
            if err is not None:
                check.update(glyph=glyph_name, reason=err)
            else:
                check = {"checked": True, "glyph": glyph_name, "side_attribute": attr, "group_id_read": value, "expected": expected_id,
                         "caught_up": value == expected_id}
    except Exception as exc:
        check = {"checked": False, "reason": f"the check failed ({type(exc).__name__}: {exc})"}
    return mark, refresh, check


def rename_kerning_group(group, new_name):
    """v0.200 - renames ONE kerning group of the current master: container.rename(group, new_name), verified by re-reading both
    sources (the old name gone, the new name confirmed with the same members and side, both sizes unchanged). Refused before any
    change: a bad name, the same name, a new name that is already any group's or class's name. A new name that is a glyph's name is
    allowed (the user's choice, 2026-11-20): same_name_glyph says so. The id before and after are reported: FontLab gives a renamed
    group a new id (GE 1511). No dialog: a rename is undone by renaming back."""
    if not _kern_name_ok(group) or not _kern_name_ok(new_name):
        return _kern_bad("group and new_name must each be 1 to 63 characters from A-Z a-z 0-9 . _ -")
    if group == new_name:
        return _kern_bad("new_name is the same as group; nothing to rename")
    ctx, refusal = _kge_open(group, "renamed")
    if ctx is None:
        return refusal
    read, before = ctx["read"], ctx["before"]
    if new_name in read["items"] or new_name in read["list"] or new_name in read["other"]:
        what = "a kerning group" if (new_name in read["items"] or new_name in read["list"]) else "a class (an OpenType class or a tag)"
        return _kge_reply(ctx, {"error": f"{new_name!r} is already the name of {what} in this font; nothing was renamed"})
    try:
        renamer = ctx["container"].rename
    except Exception as exc:
        return _kge_reply(ctx, {"error": f"the kerning groups' rename is not reachable ({type(exc).__name__}: {exc}); nothing was renamed"})
    if not callable(renamer):
        return _kge_reply(ctx, {"error": "the kerning groups' rename is not callable; nothing was renamed"})
    call_error, returned = None, None
    try:
        returned = renamer(group, new_name)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    kerning, container = ctx["target"]["kerning"], ctx["container"]
    table_after, groups_after = _kern_len(kerning), _kern_len(container)
    after_read = _kge_read(container, ctx["target"]["pkg"])
    readable = after_read["items_error"] is None and after_read["list_error"] is None
    old_gone = readable and group not in after_read["items"] and group not in after_read["list"]
    new_seen = readable and (new_name in after_read["items"] or new_name in after_read["list"])
    after = (_kgr_group(new_name, after_read["items"], after_read["list"], None, after_read["items_twice"] | after_read["list_twice"])
             if new_seen else None)
    sizes = all(type(n) is int for n in (ctx["table_before"], table_after, ctx["groups_before"], groups_after))
    renamed = (call_error is None and old_gone and after is not None and after.get("confirmed") is True
               and sorted(after.get("members") or []) == sorted(before.get("members") or []) and after.get("side") == before.get("side")
               and sizes and table_after == ctx["table_before"] and groups_after == ctx["groups_before"])
    changed = (old_gone or new_seen) if readable else None
    out = _kge_reply(ctx, {"group": group, "new_name": new_name, "renamed": renamed, "changed": changed,
                           "returned": _tryfont_plain(returned), "group_after": after,
                           "table_size_before": ctx["table_before"], "table_size_after": table_after,
                           "groups_before": ctx["groups_before"], "groups_after": groups_after,
                           "id_before": before.get("id"), "id_after": after.get("id") if after else None,
                           "same_name_glyph": new_name in ctx["target"]["by_name"]})
    if call_error is not None:
        out["call_error"] = call_error
    if not readable:
        out["reason"] = "the kerning groups could not be read back: " + str(after_read["items_error"] or after_read["list_error"])
    elif not renamed and call_error is not None:
        out["reason"] = (f"FontLab's rename raised an error ({call_error}); the re-read shows "
                         + ("the group under the new name" if old_gone and after is not None else
                            "the old name still listed" if not old_gone else "the old name gone, the new name not listed"))
    elif not renamed:
        same_group = (after is not None and after.get("confirmed") is True and after.get("side") == before.get("side")
                      and sorted(after.get("members") or []) == sorted(before.get("members") or []))
        out["reason"] = ("the re-read does not confirm the rename: " + ("the old name is still listed" if not old_gone else
                         "the new name is not listed" if after is None else
                         f"the group under the new name is not confirmed ({after.get('mismatch')})" if after.get("confirmed") is not True else
                         "the group under the new name differs from the group before" if not same_group else
                         f"the sizes changed (kerning entries {ctx['table_before']} -> {table_after}, groups {ctx['groups_before']} -> {groups_after})"))
    if changed is not False:
        side = (after or before).get("side")
        expected = after.get("id") if after else None
        out["fontlab_changed_mark"], out["fontlab_panel_refresh"], out["fontlab_caught_up"] = _kge_after_change(
            ctx, (after or before).get("members") or [], side, expected)
    else:
        out["fontlab_changed_mark"] = {"called": False, "reason": "nothing changed"}
        out["fontlab_panel_refresh"] = {"called": False, "reason": "nothing changed"}
    return out


def _kge_removal_text(group, before, pairs):
    """The question of the removal dialog, built only from facts of this request (as _deletion_text): the client's name, the font, the
    group, its side and members, and what happens to its kerning entries (GK 1539-1545)."""
    who = (f"{_request_client} (via Glyphbridge) is requesting to remove" if _request_client
           else "A request through Glyphbridge asks to remove")
    font = _REQUEST_FONT
    title = " ".join(part for part in (font.get("family"), font.get("style")) if part) if font.get("used") else ""
    where = f' from the font "{title}"' if title else ""
    members = before.get("members") or []
    shown = ", ".join(members[:_KGE_MEMBERS_SHOWN]) + (f" and {len(members) - _KGE_MEMBERS_SHOWN} more" if len(members) > _KGE_MEMBERS_SHOWN else "")
    side = {"left": "Kerning Left", "right": "Kerning Right", "both": "Kerning both"}.get(before.get("side"), "kerning")
    if pairs == "keep":
        fate = ("Its kerning is kept: each class entry becomes glyph pairs or class : glyph entries for its members, with the same values.")
    else:
        fate = "Its kerning entries are deleted with it."
    return (f"{who} the kerning group '{group}'{where} ({side}, {len(members)} member{'' if len(members) == 1 else 's'}: {shown}).\n\n"
            f"{fate}\n\nNo Glyphbridge tool can bring a removed group back.\n\nAllow this removal?")


def remove_kerning_group(group, pairs, seconds=_DIALOG_SECONDS_DEFAULT):
    """v0.200 - removes ONE kerning group of the current master after a Yes in a FontLab dialog (default No): container.remove(group)
    (pairs="keep": its class entries become glyph pairs or class : glyph entries of its members, GE 1518, GL 1530, GK 1539-1544) or
    container.remove(group, True) (pairs="delete": its entries go too, GE 1520). Verified by re-reading: the group gone from both sources,
    the container one smaller; the table's size before and after is reported, its entries are never read."""
    if not _kern_name_ok(group):
        return _kern_bad("group must be 1 to 63 characters from A-Z a-z 0-9 . _ -")
    if pairs not in ("keep", "delete"):
        return _kern_bad('pairs must be "keep" or "delete"')
    ctx, refusal = _kge_open(group, "removed")
    if ctx is None:
        return refusal
    before = ctx["before"]
    try:
        remover = ctx["container"].remove
    except Exception as exc:
        return _kge_reply(ctx, {"error": f"the kerning groups' remove is not reachable ({type(exc).__name__}: {exc}); nothing was removed"})
    if not callable(remover):
        return _kge_reply(ctx, {"error": "the kerning groups' remove is not callable; nothing was removed"})
    dialog = _confirm_group_removal(_kge_removal_text(group, before, pairs), seconds)
    if dialog.get("answer") != "yes":   # v0.203: No, no answer in time, or no dialog
        refused = {"group": group, "pairs": pairs, "removed": False, "changed": False, "dialog": dialog}
        refused.update(_dialog_refusal(dialog, "removal"))
        if "dialog_error" in refused:
            refused["error"] = f"{refused['dialog_error']}; nothing was removed"
        return _kge_reply(ctx, refused)
    call_error, returned = None, None
    try:
        returned = remover(group) if pairs == "keep" else remover(group, True)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    kerning, container = ctx["target"]["kerning"], ctx["container"]
    table_after, groups_after = _kern_len(kerning), _kern_len(container)
    after_read = _kge_read(container, ctx["target"]["pkg"])
    readable = after_read["items_error"] is None and after_read["list_error"] is None
    gone = readable and group not in after_read["items"] and group not in after_read["list"]
    sizes = all(type(n) is int for n in (ctx["groups_before"], groups_after))
    removed = call_error is None and gone and sizes and groups_after == ctx["groups_before"] - 1
    tables = type(ctx["table_before"]) is int and type(table_after) is int
    changed = (gone or (tables and table_after != ctx["table_before"]) or (sizes and groups_after != ctx["groups_before"])) if readable else None
    out = _kge_reply(ctx, {"group": group, "pairs": pairs, "removed": removed, "changed": changed, "returned": _tryfont_plain(returned),
                           "still_in_items": (group in after_read["items"]) if after_read["items_error"] is None else None,
                           "still_in_class_list": (group in after_read["list"]) if after_read["list_error"] is None else None,
                           "table_size_before": ctx["table_before"], "table_size_after": table_after,
                           "groups_before": ctx["groups_before"], "groups_after": groups_after})
    if call_error is not None:
        out["call_error"] = call_error
    if not readable:
        out["reason"] = "the kerning groups could not be read back: " + str(after_read["items_error"] or after_read["list_error"])
    elif not removed and call_error is not None:
        out["reason"] = (f"FontLab's remove raised an error ({call_error}); the re-read shows the group "
                         + ("gone" if gone else "still listed"))
    elif not removed:
        out["reason"] = ("the re-read does not confirm the removal: " + ("the group is still listed" if not gone else
                         "the number of kerning groups did not drop by one"))
    if changed is not False:
        out["fontlab_changed_mark"], out["fontlab_panel_refresh"], out["fontlab_caught_up"] = _kge_after_change(
            ctx, before.get("members") or [], before.get("side"), 0)
    else:
        out["fontlab_changed_mark"] = {"called": False, "reason": "nothing changed"}
        out["fontlab_panel_refresh"] = {"called": False, "reason": "nothing changed"}
    return out


def set_glyph_unicode(name, new_codepoint):
    """Set one glyph's Unicode codepoint, verified by re-reading it
    afterward - same discipline as set_glyph_width."""
    font = _open_font()
    if font is None:
        return {"open": False}

    glyph = _find_glyph(font, name)
    if glyph is None:
        return {
            "open": True, "set": False,
            "reason": f"no glyph named {name!r}",
            "before": None, "after": None,
        }

    before_raw = glyph.unicode
    before = None if before_raw in (None, 0) else before_raw

    call_error = None
    try:
        glyph.unicode = int(new_codepoint)
    except Exception as exc:
        call_error = str(exc)

    guard_ok, guard_report = _guard_decide(font)
    if guard_ok:
        try:
            glyph.update()
        except Exception:
            pass
        try:
            font.update()
        except Exception:
            pass

    glyph_again = _find_glyph(font, name)
    after_raw = glyph_again.unicode if glyph_again is not None else None
    after = None if after_raw in (None, 0) else after_raw
    # 0 means "remove the codepoint": FontLab then reads back as none, which is a SUCCESS (v0.51; before, None != 0 was
    # reported as a failure although the codepoint HAD been cleared - seen live)
    success = (after == int(new_codepoint)) or (int(new_codepoint) == 0 and after is None)

    result = {"open": True, "set": success, "name": name, "before": before,
              "after": after, "requested": new_codepoint}
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    if not success and not call_error:
        result["reason"] = "unicode did not change to the requested value after setting"
    if success and int(new_codepoint) != 0:
        result["duplicate_check"] = _other_glyphs_with_unicode(font, name, int(new_codepoint))
    if success and before != after:
        result["fontlab_changed_mark"] = (_mark_font_changed(font, name, "unicode") if guard_ok else
                                          {"called": False, "reason": "another glyph is still unsynced, so nothing further was called"})
    return result


class _RecordingPen:
    """Minimal pen implementing the standard font-tool pen protocol
    (moveTo/lineTo/curveTo/qCurveTo/closePath/endPath/addComponent).
    Just records whatever the glyph calls, unmodified - this is for
    verifying FontLab 8's draw() actually follows this convention before
    any real logic is built on top of it."""

    def __init__(self):
        self.contours = []
        self._current = None

    def moveTo(self, pt):
        self._current = {"closed": False, "points": [{"type": "move", "x": pt[0], "y": pt[1]}]}
        self.contours.append(self._current)

    def lineTo(self, pt):
        self._current["points"].append({"type": "line", "x": pt[0], "y": pt[1]})

    def curveTo(self, *pts):
        for i, pt in enumerate(pts):
            kind = "offcurve" if i < len(pts) - 1 else "curve"
            self._current["points"].append({"type": kind, "x": pt[0], "y": pt[1]})

    def qCurveTo(self, *pts):
        for i, pt in enumerate(pts):
            if pt is None:
                continue
            kind = "offcurve" if i < len(pts) - 1 else "qcurve"
            self._current["points"].append({"type": kind, "x": pt[0], "y": pt[1]})

    def closePath(self):
        if self._current is not None:
            self._current["closed"] = True
        self._current = None

    def endPath(self):
        self._current = None

    def addComponent(self, glyph_name, transformation):
        self.contours.append({"component": glyph_name, "transformation": list(transformation)})


def debug_glyph_contours(name):
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    pen = _RecordingPen()
    draw_error = None
    try:
        glyph.draw(pen)
    except Exception as exc:
        draw_error = str(exc)

    result = {
        "open": True, "found": True, "name": name,
        "contour_count": len(pen.contours),
        "contours": pen.contours,
    }
    if draw_error:
        result["draw_error"] = str(draw_error)
    return result


def debug_glyph_box(name):
    """Real box/fbox values. Only plain getattr calls - the same safe
    pattern debug_glyph_info already uses repeatedly - deliberately
    nothing map/dict-like, since that is the suspected cause of the
    earlier crash in the now-removed shapemap probe."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    report = {"open": True, "found": True, "name": name}

    try:
        box = glyph.box
        report["box"] = list(box) if box is not None else None
    except Exception as exc:
        report["box_error"] = str(exc)

    try:
        fbox = glyph.fbox
        report["fbox_simple_values"] = _simple_attrs(fbox)
        report["fbox_dir"] = [n for n in dir(fbox) if not n.startswith("_")]

        for corner in ("ll", "ur"):
            try:
                pt = getattr(fbox, corner)
                report[f"fbox_{corner}_xy"] = {"x": pt.x, "y": pt.y}
            except Exception as exc:
                report[f"fbox_{corner}_error"] = str(exc)

        for method_name in ("left", "right", "top", "bottom", "width", "height"):
            try:
                method = getattr(fbox, method_name)
                report[f"fbox_{method_name}()"] = method() if callable(method) else method
            except Exception as exc:
                report[f"fbox_{method_name}_error"] = str(exc)
    except Exception as exc:
        report["fbox_error"] = str(exc)

    return report


def debug_shape_count(name):
    """Exactly ONE operation: len(font.shapes). Deliberately isolated -
    v0.12's shapemap probe combined four different operations on this same
    object type in one call and crashed FontLab, so we no longer know which
    one was responsible. This tests only the single lowest-risk operation
    on it."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    try:
        shapes_obj = font.shapes
    except Exception as exc:
        return {"open": True, "found": True, "name": name, "shapes_attr_error": str(exc)}

    result = {"open": True, "found": True, "name": name, "glyph_id": glyph.id,
              "shapes_type": type(shapes_obj).__name__}
    try:
        result["shapes_len"] = len(shapes_obj)
    except Exception as exc:
        result["len_error"] = str(exc)
    return result


def debug_layer_stats(name):
    """Real counts via fgLayer's own documented methods - countContours(),
    countNodes(), countShapes(), and len(layer). Per FontLab's official
    Python API docs, these are exactly the methods behind the GUI's own
    'Shapes count'/'Contours count'/'Nodes count' tooltips.

    glyph.bodyLayer has been directly observed to be intermittently None
    even when a real layer exists (confirmed via repeated real tests), so
    this retries a few times rather than trusting a single attempt, and
    reports every attempt's result for transparency."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    # Two real tests suggest calling /debug/glyph (which touches
    # glyph.layer, not bodyLayer) right before layerstats made bodyLayer
    # resolve where it otherwise didn't. Testing that directly here: touch
    # glyph.layer first as a possible warm-up, discarding the result,
    # before attempting bodyLayer.
    warmup = "not attempted"
    try:
        _ = glyph.layer
        warmup = "touched glyph.layer, no error"
    except Exception as exc:
        warmup = f"touched glyph.layer, error: {exc}"

    attempts = [f"warmup: {warmup}"]
    layer = None
    for i in range(5):
        try:
            candidate = glyph.bodyLayer
        except Exception as exc:
            attempts.append(f"attempt {i}: error {exc}")
            continue
        attempts.append(f"attempt {i}: {'got layer' if candidate is not None else 'None'}")
        if candidate is not None:
            layer = candidate
            break

    result = {"open": True, "found": True, "name": name, "layer_fetch_attempts": attempts}

    if layer is None:
        result["layer_error"] = "bodyLayer was None on every attempt"
        return result

    try:
        result["layer_name"] = layer.name
    except Exception as exc:
        result["layer_name_error"] = str(exc)

    # Re-check each count method twice, a beat apart, in case the counts
    # themselves are also flaky rather than stably zero.
    for label, fn in (
        ("countContours", lambda: layer.countContours()),
        ("countNodes", lambda: layer.countNodes()),
        ("countShapes", lambda: layer.countShapes()),
        ("len_layer", lambda: len(layer)),
    ):
        readings = []
        for _ in range(2):
            try:
                readings.append(fn())
            except Exception as exc:
                readings.append(f"error: {exc}")
        result[label] = readings

    return result


# --------------------------------------------------------------------------
# /debug/trycomponent remove stages (v0.176) - RESEARCH for removing a component (the user's choice of 2026-11-17, after add_component:
# no tool removes a component, and Edit > Undo offered nothing after it, 1090). Names only (test 1240, /debug/classdir):
# flLayer.removeShape(flShape[, bool recursive=true]), flLayer.clearComponents(), flLayer.removeAllShapes([ShapeType]) and
# flShape.remove([flObject]); what "recursive" does is not documented, so it is always passed explicitly (0 or 1) and both are tried.
#   stage=removeshape&target=cpp...&element=I&recursive=0|1&go=yes  ONE layer.removeShape(<component I>, recursive)
#   stage=clearcomponents&target=cpp...&go=yes                       ONE layer.clearComponents()
# The target: a modern active layer of 1 to _TRYCOMP_SEVERAL_MAX elements, each a component of a cpp glyph, autoLayer off. Every
# check is made before the call; the call is counted in _TRYCOMP (the probe's 6 per listener run) BEFORE the glyph is read.
# The reply has the target's elements (source, layer, reference_count, matrix), ink boxes, outline, state, autoLayer and recipe,
# advance width and glyph count before and after, and every source's outline before and after. removed is true only when the
# elements left are exactly the ones expected, in order, with their matrices and ink boxes unchanged, the layer is still there, and
# nothing else changed (sources, width, glyph count, autoLayer and recipe). A change goes through _guard_mark (sync, changed mark).
# Never called here: removeAllShapes, remove, decomposite, replaceShape, font.update(), save; no subscript or iteration of a native
# object (layer.shapes is a real list).
# --------------------------------------------------------------------------

_TRYCOMP_REMOVE_STAGES = ("removeshape", "clearcomponents")
_TRYCOMP_REMOVE_CALLS = {"removeshape": "layer.removeShape(component, recursive)", "clearcomponents": "layer.clearComponents()"}


def _trycomp_remove_gate(stage, target, go, element, recursive):
    """v0.176: the parameters, the go gate, the one-font gate and the call counter of the remove stages; then _trycomp_remove."""
    import sys as _sys
    has_elem = element is not None and str(element).strip() != ""
    has_rec = recursive is not None and str(recursive).strip() != ""
    elem, rec = None, None
    if stage == "removeshape":
        if not has_elem:
            return {"error": "stage=removeshape needs element=I, the position of the component to remove (0 = the first)"}
        elem, err = _tryedit_int(element, "element", 0, _TRYCOMP_SEVERAL_MAX - 1)
        if err is not None:
            return {"error": err}
        rec_s = str(recursive or "").strip()
        if rec_s not in ("0", "1"):
            return {"error": 'stage=removeshape needs recursive=0 or recursive=1 (passed to removeShape as False / True)'}
        rec = rec_s == "1"
    elif has_elem or has_rec:
        return {"error": "stage=clearcomponents takes no element and no recursive: it removes every component of the target"}
    if go != "yes":
        if stage == "removeshape":
            return {"error": f"stage=removeshape calls {_TRYCOMP_REMOVE_CALLS[stage]} once on component {elem} of the target, recursive "
                             f"{rec}; the other components must stay as they are. Add &go=yes to run it."}
        return {"error": f"stage=clearcomponents calls {_TRYCOMP_REMOVE_CALLS[stage]} once on the target. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, _pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
    if _TRYCOMP["calls"] >= _TRYCOMP_MAX:
        return {"stage": stage, "error": f"the probe already ran {_TRYCOMP_MAX} times in this listener run; restart the listener to repeat it",
                "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
    _TRYCOMP["calls"] += 1     # counted BEFORE the glyph is read
    base = {"stage": stage, "target": target, "call": _TRYCOMP_REMOVE_CALLS[stage], "calls_so_far": _TRYCOMP["calls"],
            "max_calls": _TRYCOMP_MAX, "note": _TRYCOMP_NOTE}
    if stage == "removeshape":
        base["element"], base["recursive"] = elem, rec
    return _trycomp_remove(target, stage, elem, rec, base)


def _trycomp_remove(*args, **kwargs):
    """v0.176: _trycomp_remove_run, timed."""
    return _trycomp_timed(_trycomp_remove_run, *args, **kwargs)


def _trycomp_remove_run(target, stage, element, recursive, base):
    """v0.176: ONE layer.removeShape(<component `element`>, recursive) or ONE layer.clearComponents() on a layer of components. Read
    back. Never raises."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state_before"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer: nothing was touched")
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was touched")
    base["target_elements_before"] = tel
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False:
        return dict(base, error=f"the layer's autoLayer reads {auto_before.get('auto_layer')!r}, not False: nothing was touched")
    if not 1 <= len(tel) <= _TRYCOMP_SEVERAL_MAX or any(e.get("is_component") is not True or not _trycomp_name_ok(e.get("component_glyph"))
                                                        for e in tel):
        return dict(base, error=(f"the layer must hold 1 to {_TRYCOMP_SEVERAL_MAX} elements, each a component of a cpp glyph "
                                 f"(it holds {len(tel)}): nothing was touched"))
    if element is not None and element >= len(tel):
        return dict(base, error=f"element {element} does not exist: the layer holds {len(tel)} elements (0 to {len(tel) - 1}): nothing was touched")
    sources = []
    for e in tel:
        if e["component_glyph"] not in sources:
            sources.append(e["component_glyph"])
    src_before = {}
    for s in sources:
        snap = _tryedit_snapshot(s)
        if "error" in snap:
            return dict(base, error=f"the source {s!r} could not be read ({snap['error']}): nothing was touched")
        src_before[s] = snap
    base["sources_before"] = src_before
    before = _tryedit_snapshot(target)
    if "error" in before:
        return dict(base, error=f"the target's outline could not be read ({before['error']}): nothing was touched")
    base["target_before"] = before
    boxes_before = _trycomp_all_boxes(layer)
    base["ink_boxes_before"] = boxes_before
    if isinstance(boxes_before, dict) or len(boxes_before) != len(tel) or any("error" in b for b in boxes_before):
        return dict(base, error="the components' ink boxes could not all be read: nothing was touched")
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list or len(shapes) != len(tel):
        return dict(base, error=f"the target's layer.shapes is no longer a plain list of {len(tel)}: nothing was touched")
    shape = None
    if stage == "removeshape":
        shape = shapes[element]
        expected_name = tel[element]["component_glyph"]
        sd, err = _tl_call(lambda: shape.shapeData)
        named, err2 = (None, err or "shapeData is None") if (err is not None or sd is None) else _tl_call(lambda: _call0(sd, "componentGlyph"))
        if err2 is not None or named != expected_name:
            return dict(base, error=(f"the shape at position {element} names {named!r}, not {expected_name!r} as read before: nothing was touched"
                                     if err2 is None else f"the shape at position {element} could not be checked ({err2}): nothing was touched"))
    try:
        if stage == "removeshape":
            ret = layer.removeShape(shape, recursive)
        else:
            ret = layer.clearComponents()
        base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
    except Exception as exc:
        base["error"] = f"{_TRYCOMP_REMOVE_CALLS[stage]} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["target_state_after"] = after_state
    result["layer_kept"] = layer2 is not None
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the target has no modern active layer after the call"}
    result["target_elements_after"] = tel2
    result["auto_after"] = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    boxes_after = _trycomp_all_boxes(layer2)
    result["ink_boxes_after"] = boxes_after
    after = _tryedit_snapshot(target)
    result["target_after"] = after
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    src_after = {s: _tryedit_snapshot(s) for s in sources}
    result["sources_after"] = src_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    result["source_changed"] = ("unknown" if any("error" in src_after[s] for s in sources) else
                                any(src_after[s]["contours"] != src_before[s]["contours"] for s in sources))
    keep = [i for i in range(len(tel)) if stage == "removeshape" and i != element]

    def _key(e):
        return (e.get("is_component"), e.get("component_glyph"), e.get("component_layer"), e.get("matrix"))
    list_ok = not isinstance(tel2, dict) and [_key(e) for e in tel2] == [_key(tel[i]) for i in keep]
    boxes_ok = isinstance(boxes_after, list) and boxes_after == [boxes_before[i] for i in keep]
    result["elements_as_expected"] = list_ok
    result["others_kept"] = bool(list_ok and boxes_ok)
    result["empty_after"] = "unknown" if isinstance(tel2, dict) else len(tel2) == 0
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"]
                                          or result["source_changed"] is not False or width_after != width_before
                                          or result["auto_after"] != auto_before)
    result["changed"] = ("unknown" if isinstance(tel2, dict) else True if (tel2 != tel or after_state != state) else
                         "unknown" if "error" in after else after["contours"] != before["contours"])
    result["removed"] = bool("error" not in result and result["layer_kept"] and list_ok and boxes_ok and not result["side_effect_detected"])
    if result["changed"] is not False:
        _guard_mark(font, target, "trycomponent", result, no_mark=None if result["removed"] else "the removal was not confirmed")
    return result


# --------------------------------------------------------------------------
# /debug/trycomponent (v0.155) - RESEARCH for ROADMAP P2.7 (placing a component; no tool places one yet). Names only (2026-11-17,
# /debug/classdir, /debug/moddir): flLayer.addComponent takes an flComponent, which is not a public name, so it is NOT tried;
# flLayer.setGlyphComponents(QList<GlyphComponent> result, double width, flPackage package, bool colorize, uint flags) and
# fontlab.GlyphComponent(string name) are the first route; flShape(flShapeData) with layer.addShape is the second.
# Every stage needs go=yes and the one-font gate of /debug/trysync; target and source names start with "cpp" and differ; at most
# _TRYCOMP_MAX calls per listener run, counted BEFORE either glyph is read or touched.
# SOURCE: a modern active layer with exactly one plain shape (isComponent False, isComposite False), no components, at least one node.
# TARGET: a modern active layer that EXISTS (a glyph with no layer is refused, never given one: the Add Component crash,
# FONTLAB-API-RULES.md section 9), at most one shape, which must be plain; no components.
#   stage=glyphcomponents&dx=DX&dy=DY  gc = GlyphComponent(source); gc.transform = QTransform(1, 0, 0, 1, dx, dy), read back; then
#                                      ONE layer.setGlyphComponents([gc], <the target's advance width>, <current package>, False, 0)
#   stage=shapedata&dx=DX&dy=DY        s = flShape(<the source's shape>.shapeData); s.transform = the same QTransform, read back;
#                                      then ONE layer.addShape(s)
# The reply has the target's elements (is_component, component_glyph, component_layer, reference_count, matrix), counts, outline and
# advance width before and after, the source's elements and outline before and after, the glyph count, and placed, existing_kept and
# side_effect_detected. A change goes through _guard_mark (Update(<flGlyph>), the sync check, the changed mark), as every write does.
# Never called by this probe: addComponent, clearComponents, decomposite, mergeTopComposite, removeShape, replaceShape, font.update(),
# save; no subscript or iteration of a native object. (v0.176: the remove stages, in their own section above this one, call
# removeShape and clearComponents, one per request.)
# Live (v0.155, one run each): 1026 setGlyphComponents raised "IndexError: Unexpected SeqBase<T> length."; 1027 flShape(shapeData)
# raised "TypeError: Error creating object of type flShapeBuilder"; nothing changed either time.
# v0.156: stage=readcomponents&target=cpp... READ ONLY, for a component FontLab's own Glyph > Add Component made: ONE read of
# layer.components (documented "list(name, transform)"; called once with no argument if it is callable). Only a real Python list or
# tuple is indexed, at most _TRYCOMP_ITEMS_MAX items; each item is described by type: a tuple or list part by part (text as text, a
# transform as its matrix), a GlyphComponent by name_id, width_scale, use_anchors and its matrix, anything else by its type name.
# Every element listing also gives shape_data_type, the type name of shape.shapeData (1027).
# Live (v0.156, 1028-1029): on a component made by Glyph > Add Component, layer.components read an empty list and componentsCount 0.
# v0.157 (names only, 2026-11-17: flPackage.generateGlyph(string recipe, string layer_name, FontMetrics metrics, bool rtl) returns
# (QList<GlyphComponent>, double width), the first two arguments of setGlyphComponents; FontMetrics(flPackage p, string layer_name)):
#   stage=generate&target=cpp...&recipe=R      metrics = FontMetrics(package, <target's layer name>); ONE
#                                              package.generateGlyph(R, layer_name, metrics, False); what it returns is described (a
#                                              list only when it is a real one); the target, the recipe glyphs and the glyph count are
#                                              compared before and after (side_effect_detected)
#   stage=setgenerated&target=cpp...&recipe=R  the same generateGlyph call, then ONE layer.setGlyphComponents(<the returned list, as
#                                              is>, <the returned width>, package, False, 0); read back as the other write stages
# R is one or two glyph names starting with "cpp", joined by "+", none of them the target; nothing else (no "@" placement yet).
# Live 1030 (v0.157): generateGlyph returned a real list of ONE item, not a pair, and changed nothing. v0.158: a real list or tuple
# that is not a pair is described item by item (generate_returned_items); setGlyphComponents is still called only for a pair.
# Live 1032 (v0.158): a real list of ONE GlyphComponent (name_id 5113, identity), no width, nothing changed. v0.159: setgenerated also
# takes a real list whose items are all GlyphComponent (isinstance only), passed as is with the target's own advance width; a pair
# needs a number as its second item.
# Live 1031 (v0.159): with that list, setGlyphComponents(list, 0.0, package, False, 0) raised the same "IndexError: Unexpected SeqBase<T>
# length." as 1026, nothing changed; in this project that error meant a wrong argument count before (topics/geometry.md).
# v0.160: setgenerated&args=N (2 to 5, default 5) calls setGlyphComponents once with the first N of (list, width, package, False, 0);
# the reply names the call made (call_made).
# Live 1033 (v0.160): args=4 gave "TypeError: argument type must be Int!" instead, nothing changed. v0.161: setgenerated&pkg=id passes
# the package's fgId (a plain whole number up to a uint, read as the KERNING panel refresh reads it) as the third argument.
# Live 1034 (v0.161): "TypeError: Wrong argument type. flPackage expected." for the fgId, nothing changed: the package object is right,
# so 1033's Int error was the fourth argument, False. v0.162: setgenerated&int=yes passes the whole number 0 in place of False.
# Live 1035 (v0.162): 0 as the fourth gave "TypeError: argument type must be Boolean!", nothing changed: the fourth IS a bool, so
# 1033's "must be Int" came from the first two, most likely the width 0.0. v0.163: setgenerated&width=int passes the width as a whole
# number (refused before the call when it is not one).
# Live 1036 (v0.163): a whole-number width gave "must be Int!" too, nothing changed; FontLab's archived FontLab 7 reference gives
# "bool setGlyphComponents(QList result, double width, flPackage package, bool colorize)", so the list's contents are left.
# v0.164: setgenerated&items=id passes each GlyphComponent's name_id (a plain whole number) in place of the object.
# Live 1037 (v0.164): "Wrong argument type. GlyphComponent expected.", nothing changed: every argument of the four-argument form is
# right, so its "must be Int" most likely asks for the fifth (uint flags); the five-argument "SeqBase" of 1026 / 1031 is unexplained.
# v0.165 (names only: flLayer.recipe QString, flLayer.autoLayer bool, bool flLayer.buildAuto(), killAuto()): stage=auto&step=S, ONE
# step per request on an existing target layer that is empty for every step but read:
#   read       layer.recipe and layer.autoLayer, nothing changed
#   setrecipe  layer.recipe = R, read back (R as for generate)
#   setauto    layer.autoLayer = True, read back
#   build      layer.buildAuto() once, only when layer.recipe reads exactly R; placed = components naming R's glyphs, identity matrix
# Each reply has recipe / autoLayer, elements, outline, width, the recipe glyphs and the glyph count before and after. Only a confirmed
# component from build is marked; any other outline change is synced unmarked. Never called: killAuto().
# Live 1041b (v0.165): build placed one component of the recipe's glyph; FontLab shows the layer as an auto layer, its element greyed
# and locked (1041c). v0.166, on a layer whose autoLayer reads True and that holds only components of cpp glyphs:
#   unauto     layer.autoLayer = False, read back
#   killauto   ONE layer.killAuto() (what it does to the recipe is reported, not counted as a side effect)
# component_kept: the same components (source, layer, matrix) and outline after; component_normal: kept, autoLayer False, no side
# effect; only then is the font marked. Any other outline change is synced unmarked.
# Live 1042 (v0.166): unauto kept the component and FontLab showed a normal one (1042a, 1042b).
# v0.167 (names only, 2026-11-17: flShape.transform, docstring "transform"; flShape.applyTransform([QTransform transform]);
# no setTransform, translate or move): stage=offset&target=cpp...&how=assign|apply&dx=DX&dy=DY, ONE call per request on a layer
# that holds exactly ONE component of a cpp glyph at the identity matrix, autoLayer False (as after 1042), (dx, dy) not (0, 0):
#   how=assign  shape.transform = QTransform(1, 0, 0, 1, dx, dy)
#   how=apply   ONE shape.applyTransform(QTransform(1, 0, 0, 1, dx, dy))
# Read back: the element (source, layer, matrix), the element's ink box (shape.inkBox(), proven read only on components, 644-656),
# the raw nodes of layer.getContours() (for a component they may stay the source's own: both are accepted and reported), the
# source's outline, the width, recipe / autoLayer and the glyph count. offset_placed: the matrix reads the offset, the ink box moved
# by exactly (dx, dy), the raw nodes unchanged or moved by the offset, no side effect; only then is the font marked.
# Live 1043 (v0.167, assign): offset_placed. Live 1055 (v0.166 killauto): returned None, changed nothing read.
# v0.168 (the user's design choice of 2026-11-17: research clearing the leftover recipe before a placing tool is built):
#   stage=auto&step=clearrecipe  layer.recipe = "" on a layer whose autoLayer reads False, that holds only components of cpp glyphs
#                                and whose recipe reads a non-empty text; read back. recipe_cleared: the recipe reads "", the same
#                                components (source, layer, matrix) and outline, autoLayer still False, no side effect; only then
#                                is the font marked.
# v0.171 (the user's choice of 2026-11-17: several components in one glyph; live 1049: a two-glyph recipe put the second component
# at (-200, 0) and set the width 0 -> 500):
#   stage=auto recipes of one to three glyphs (generate / setgenerated keep two)
#   stage=offset&how=assign&element=I&dx=DX&dy=DY  on a layer of 2 or 3 components of cpp glyphs, each matrix a plain offset, autoLayer
#                                False: the shape at position I must name the source read at I; ONE shape.transform = QTransform(1, 0, 0,
#                                1, dx, dy) on it (absolute, different from its offset; (0, 0) allowed). offset_placed: I's matrix reads
#                                (dx, dy), its ink box moved by the difference, every other element (source, layer, matrix, ink box)
#                                unchanged, no side effect (width, sources, glyph count, recipe / autoLayer); only then is the font
#                                marked. The raw nodes are reported only. The width is put back with set_glyph_width, no probe call.
# Live PC2 1102-1128 (v0.171): every step as predicted. v0.172 (the user's choice of 2026-11-17: test four and five glyphs before the
# tool's list limit is set): stage=auto recipes of one to five glyphs; element= on a layer of 2 to 5 components (element 0 to 4).
# Live 1129-1151 (v0.172): four and five as predicted; the width 500 each time. v0.173 (the user's choice of 2026-11-17, with CJK in
# mind: test 30, with 15 as a middle control): recipes of one to 30 glyphs, element 0 to 29; the probe reads up to 30 ink boxes
# through its own limit (_TRYSHAPEBOX_MAX_SHAPES = 20 stays for /debug/tryshapebox and add_component); build_seconds times the
# buildAuto() call, elapsed_seconds each stage=auto / stage=offset request as a whole.
# v0.180 (the user's choice of 2026-11-18: placing components into a glyph that already holds contours, components or both; research
# route "build in place"): stage=auto&nonempty=yes, steps setrecipe / setauto / build / unauto / clearrecipe, on a target holding only
# plain contour shapes (isComponent and isComposite both False) and components of cpp glyphs, at least one element. step=setrecipe
# records the target's elements (kind, source, source layer, matrix, ink box) and outline for this listener run; every step then
# reports existing_kept: each recorded element found again (matrix and ink box within 0.001) and the recorded contours still in the
# outline, in order; existing_missing, new_elements. A build's width change is reported (width_changed_by_build), not a side effect.
# placed (build): existing_kept and the new elements exactly components of the recipe's glyphs, in order (any matrix: reported).
# Marked only when that is confirmed (component_placed, component_normal, recipe_cleared) AND existing_kept is true.
# --------------------------------------------------------------------------

_TRYCOMP_MAX = 6
_TRYCOMP = {"calls": 0}
_TRYCOMP_STAGES = ("glyphcomponents", "shapedata", "readcomponents", "generate", "setgenerated", "auto", "offset")
_TRYCOMP_OFFSET_HOWS = {"assign": "shape.transform = QTransform(1, 0, 0, 1, dx, dy)",
                        "apply": "shape.applyTransform(QTransform(1, 0, 0, 1, dx, dy))"}     # v0.167
_TRYCOMP_GEN_STAGES = ("generate", "setgenerated")
_TRYCOMP_AUTO_STEPS = {"read": "reads layer.recipe and layer.autoLayer and changes nothing",
                       "setrecipe": "sets layer.recipe to the recipe and reads it back",
                       "setauto": "sets layer.autoLayer to True and reads it back",
                       "build": "calls layer.buildAuto() once",
                       "unauto": "sets layer.autoLayer to False on a layer buildAuto() filled, and reads it back",
                       "killauto": "calls layer.killAuto() once on a layer buildAuto() filled",
                       "clearrecipe": "sets layer.recipe to \"\" on a layer of components whose autoLayer is off, and reads it back"}
_TRYCOMP_DELTA_MAX = 1000
_TRYCOMP_SEVERAL_MAX = 30    # v0.171: stage=offset&element=I works on a layer of 2 to N components (3 in v0.171, 5 in v0.172, 30 since v0.173)
_TRYCOMP_AUTO_PARTS_MAX = 30  # v0.172: stage=auto recipes of up to N glyphs (three in v0.171, five in v0.172, 30 since v0.173: the user's test size)
_TRYCOMP_ITEMS_MAX = 20
_TRYCOMP_ARG_LABELS = ("<returned list>", "<width>", "package", "False", "0")     # v0.160: setgenerated's args=N takes the first N
_TRYCOMP_CALLS = {"glyphcomponents": "layer.setGlyphComponents([GlyphComponent(source)], width, package, False, 0)",
                  "shapedata": "layer.addShape(flShape(source_shape.shapeData))", "readcomponents": "layer.components (read only)",
                  "generate": "package.generateGlyph(recipe, layer_name, FontMetrics(package, layer_name), False)",
                  "auto": "one step of the layer's own recipe build: layer.recipe, layer.autoLayer or layer.buildAuto()",
                  "setgenerated": ("package.generateGlyph(recipe, layer_name, FontMetrics(package, layer_name), False), then "
                                   "layer.setGlyphComponents(<returned list>, <returned width>, package, False, 0)")}
_TRYCOMP_NOTE = ("RESEARCH: compare with get_glyph_outline and with FontLab's Elements panel; nothing is saved by Glyphbridge; "
                 "quit FontLab WITHOUT saving afterwards, or delete the cpp glyphs")
_TRYCOMP_MATRIX_KEYS = ("m11", "m12", "m21", "m22", "dx", "dy")


def _trycomp_qtransform_class(mod):
    """(QTransform class, source) or (None, reason). Looked up at run time; nothing is constructed here."""
    tried = []
    try:
        from PythonQt.QtGui import QTransform as _QT
        if _QT is not None:
            return _QT, "PythonQt.QtGui.QTransform"
        tried.append("PythonQt.QtGui.QTransform is None")
    except Exception as exc:
        tried.append(f"PythonQt.QtGui: {type(exc).__name__}: {exc}")
    cls = getattr(mod, "QTransform", None)
    if cls is not None:
        return cls, "fontlab.QTransform"
    tried.append("fontlab module has no QTransform")
    return None, "no QTransform class found: " + " | ".join(tried)


def _trycomp_matrix(tr):
    """({m11, m12, m21, m22, dx, dy} as floats, None) from a QTransform, or (None, reason). Read only. Never raises."""
    if tr is None:
        return None, "the transform is None"
    m = {}
    for a in _TRYCOMP_MATRIX_KEYS:
        v, err = _tl_call(lambda k=a: _call0(tr, k))
        if err is not None:
            return None, f"{a} could not be read ({err})"
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None, f"{a} is not a number ({type(v).__name__})"
        m[a] = float(v)
    return m, None


def _trycomp_offset_ok(m, dx, dy):
    """True when `m` is the plain offset (dx, dy) within 0.001."""
    if not isinstance(m, dict) or any(k not in m for k in _TRYCOMP_MATRIX_KEYS):
        return False
    return all(abs(m[k] - v) <= 0.001 for k, v in zip(_TRYCOMP_MATRIX_KEYS, (1.0, 0.0, 0.0, 1.0, float(dx), float(dy))))


def _trycomp_elements(layer):
    """[{index, is_component, is_composite, component_glyph, component_layer, reference_count, matrix}] for layer.shapes (a real list),
    or {"error"}. A value that could not be read is "<error: ...>", never left out. Read only. Never raises."""
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list:
        return {"error": f"layer.shapes is not a plain list ({err or type(shapes).__name__})"}
    out = []
    for i, sh in enumerate(shapes):
        e = {"index": i}
        for key, attr in (("is_component", "isComponent"), ("is_composite", "isComposite")):
            v, err = _tl_call(lambda a=attr: _call0(sh, a))
            e[key] = v if (err is None and type(v) is bool) else f"<error: {err or type(v).__name__}>"
        sd, err = _tl_call(lambda: sh.shapeData)
        if err is not None or sd is None:
            e["shape_data_error"] = err or "shapeData is None"
        else:
            e["shape_data_type"] = type(sd).__name__
            for key, attr, kinds in (("component_glyph", "componentGlyph", (str,)), ("component_layer", "componentLayer", (str,)),
                                     ("reference_count", "referenceCount", (int,))):
                v, err = _tl_call(lambda a=attr: _call0(sd, a))
                e[key] = v if (err is None and isinstance(v, kinds) and not isinstance(v, bool)) else f"<error: {err or type(v).__name__}>"
        tr, err = _tl_call(lambda: sh.transform)
        m, why = _trycomp_matrix(tr) if err is None else (None, err)
        e["matrix"] = m if m is not None else {"error": why}
        out.append(e)
    return out


def _trycomp_width(w):
    """The modern advance width as a float, or an "<error: ...>" string."""
    v, err = _tl_call(lambda: _call0(w, "advanceWidth"))
    if err is not None:
        return f"<error: {err}>"
    n = _num(v)
    return n if n is not None else f"<error: not a number ({type(v).__name__})>"


def _trycomp_holds(seq, part):
    """True when the contours of `part` appear in `seq` in order (not necessarily next to each other)."""
    it = iter(seq)
    return all(any(c == p for c in it) for p in part)


def _trycomp_shift(contours, dx, dy):
    """`contours` (snapshot form) moved by (dx, dy)."""
    return [dict(c, nodes=[dict(n, x=n["x"] + dx, y=n["y"] + dy) for n in c.get("nodes") or []]) for c in contours]


def _trycomp_is(item, cls):
    """True when `cls` is a class and `item` an instance of it. isinstance() reads no member of the item. Never raises."""
    v, _err = _tl_call(lambda: cls is not None and isinstance(item, cls))
    return v is True


def _trycomp_item(item, gc_cls, qt_cls=None, depth=0):
    """v0.156: one value or item, described by its type: text, numbers, bools and None as they are; a QTransform (by isinstance only)
    as its matrix; a GlyphComponent by its documented members; a real tuple or list part by part, two levels deep at most (v0.158);
    anything else by its type name only, no member of it read. Only a real tuple or list is indexed. Never raises."""
    if item is None or isinstance(item, (bool, int, float, str)):
        return {"type": type(item).__name__, "value": item}
    out = {"type": type(item).__name__}
    if type(item) in (list, tuple):
        out["len"] = len(item)
        if depth < 2:
            out["parts"] = [_trycomp_item(p, gc_cls, qt_cls, depth + 1) for p in item[:_TRYCOMP_ITEMS_MAX]]
        return out
    if _trycomp_is(item, qt_cls):
        m, why = _trycomp_matrix(item)
        out["matrix"] = m if m is not None else {"error": why}
        return out
    if _trycomp_is(item, gc_cls) or out["type"] == "GlyphComponent":
        for key in ("name_id", "width_scale", "use_anchors"):
            v, err = _tl_call(lambda k=key: _call0(item, k))
            out[key] = _rm_plain(v) if err is None else f"<error: {err}>"
        tr, err = _tl_call(lambda: item.transform)
        m, why = _trycomp_matrix(tr) if err is None else (None, err)
        out["matrix"] = m if m is not None else {"error": why}
    return out


def _trycomp_read_components(mod, target, base):
    """v0.156, stage=readcomponents: ONE read of layer.components on the target. Changes nothing. Never raises."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be read: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer")
    base["target_elements"] = _trycomp_elements(layer)
    count_before = _tryedit_glyph_count(font)
    out = dict(base)
    comps, err = _tl_call(lambda: layer.components)
    if err is None and callable(comps) and type(comps) not in (list, tuple):
        out["components_called"] = True
        comps, err = _tl_call(comps)
    if err is not None:
        out["components_error"] = err
    else:
        out["components_type"] = type(comps).__name__
        if type(comps) not in (list, tuple):
            out["components_note"] = "not a real Python list or tuple, so it was neither indexed nor iterated"
        else:
            out["components_len"] = len(comps)
            gc_cls = getattr(mod, "GlyphComponent", None)
            qt_cls = _trycomp_qtransform_class(mod)[0]
            out["components"] = [_trycomp_item(it, gc_cls, qt_cls) for it in comps[:_TRYCOMP_ITEMS_MAX]]
            if len(comps) > _TRYCOMP_ITEMS_MAX:
                out["components_truncated"] = f"only the first {_TRYCOMP_ITEMS_MAX} items are described"
    state_after, _l = _tryshape_modern_state(w)
    out["glyph_count"] = count_before
    out["side_effect_detected"] = bool(state_after != state or _tryedit_glyph_count(font) != count_before)
    return out


def _trycomp_name_ok(nm):
    return (isinstance(nm, str) and 4 <= len(nm) <= 40 and nm.startswith("cpp") and all(ch in _TRYCREATE_NAME_CHARS for ch in nm))


_TRYCOMP_NUMBER_WORDS = {3: "three", 4: "four", 5: "five", 30: "thirty"}


def _trycomp_recipe(recipe, target, most=2):
    """(parts, None) or (None, sentence): one to `most` "cpp" glyph names joined by "+", none of them the target.
    v0.171: stage=auto takes more (three; five since v0.172, _TRYCOMP_AUTO_PARTS_MAX); the other stages keep two."""
    if not isinstance(recipe, str) or not recipe:
        return None, "recipe is required for this stage"
    parts = recipe.split("+")
    if not 1 <= len(parts) <= most or not all(_trycomp_name_ok(p) for p in parts):
        return None, (f'recipe must be one {"or two" if most == 2 else "to " + _TRYCOMP_NUMBER_WORDS.get(most, str(most))} glyph names starting with "cpp" '
                      '(A-Z a-z 0-9 . _ -), joined by "+"')
    if target in parts:
        return None, "the recipe must not name the target"
    return parts, None


def _trycomp_generate(mod, pkg, stage, target, parts, base):
    """v0.157: stage=generate / setgenerated. ONE package.generateGlyph call; for setgenerated then ONE layer.setGlyphComponents with
    what it returned. Read back as the other stages. Never raises."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error=("the target cannot be used: " + str(refusal.get("reason") or refusal) + " (a glyph with no layer is never "
                                 "given a component by this probe: the Add Component crash)"), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state_before"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer: nothing was called")
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was called")
    base["target_elements_before"] = tel
    if stage == "setgenerated":
        if len(tel) > 1 or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in tel):
            return dict(base, error="the target must have at most one shape, and a plain one: nothing was called")
        if _state_has_components(state):
            return dict(base, error=f"the target reads {_state_components_text(state)}: nothing was called")
    layer_name = state.get("layer_name")
    if not isinstance(layer_name, str) or not layer_name:
        return dict(base, error="the target's layer name could not be read: nothing was called")
    src_before = {}
    for p in parts:
        snap = _tryedit_snapshot(p)
        if "error" in snap:
            return dict(base, error=f"the recipe glyph {p!r} could not be read ({snap['error']}): nothing was called")
        src_before[p] = snap
    base["recipe_glyphs_before"] = src_before
    before = _tryedit_snapshot(target)
    if "error" in before:
        return dict(base, error=f"the target's outline could not be read ({before['error']}): nothing was called")
    base["target_before"] = before
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    base["layer_name"] = layer_name
    recipe = "+".join(parts)
    step, touched, gwidth = "FontMetrics(package, layer_name)", False, None
    try:
        metrics = mod.FontMetrics(pkg, layer_name)
        step = "package.generateGlyph(recipe, layer_name, metrics, False)"
        gen = pkg.generateGlyph(recipe, layer_name, metrics, False)
        base["generate_returned_type"] = type(gen).__name__
        comps = None
        gc_cls = getattr(mod, "GlyphComponent", None)
        if type(gen) in (tuple, list) and len(gen) == 2 and isinstance(gen[1], (int, float)) and not isinstance(gen[1], bool):
            comps, gwidth = gen[0], gen[1]
            base["generated_width"] = _rm_plain(gwidth)
            base["generated_list_type"] = type(comps).__name__
            if type(comps) in (list, tuple):
                base["generated_len"] = len(comps)
                base["generated"] = [_trycomp_item(it, getattr(mod, "GlyphComponent", None), _trycomp_qtransform_class(mod)[0])
                                     for it in comps[:_TRYCOMP_ITEMS_MAX]]
            else:
                base["generated_note"] = "the list is not a real Python list or tuple, so it was neither indexed nor iterated"
        elif type(gen) in (tuple, list):     # v0.158: live 1030 returned a list of one item; each item is described
            base["generate_returned"] = f"a {type(gen).__name__} of {len(gen)} items"
            base["generate_returned_items"] = [_trycomp_item(it, getattr(mod, "GlyphComponent", None), _trycomp_qtransform_class(mod)[0])
                                               for it in gen[:_TRYCOMP_ITEMS_MAX]]
            # v0.159: live 1032 returned a real list of GlyphComponent and no width; setgenerated passes that list as is, with the
            # target's own advance width
            if (stage == "setgenerated" and 0 < len(gen) <= _TRYCOMP_ITEMS_MAX and isinstance(width_before, float)
                    and all(_trycomp_is(it, gc_cls) for it in gen)):
                comps, gwidth = gen, width_before
                base["width_source"] = "the target's own advance width (generateGlyph returned none)"
        else:
            base["generate_returned"] = _rm_plain(gen)
        if stage == "setgenerated":
            if comps is None or isinstance(gwidth, bool) or not isinstance(gwidth, (int, float)):
                base["error"] = ("generateGlyph returned neither (list, width) nor a list of GlyphComponent: setGlyphComponents was not "
                                 "called")
            elif type(comps) in (list, tuple) and len(comps) == 0:
                base["error"] = "generateGlyph returned an empty list: setGlyphComponents was not called"
            else:
                n = base.get("args", 5)     # v0.160: the first n of the five documented arguments (live 1026, 1031: 5 gave SeqBase)
                third, labels = pkg, list(_TRYCOMP_ARG_LABELS)
                if base.get("pkg") == "id":     # v0.161: live 1033 (4 arguments): "argument type must be Int!"; the package's fgId instead
                    pid, perr = _pkg_get(pkg, "fgId")
                    if perr is not None or type(pid) is not int or not 0 <= pid <= _TRYNOTIFY_UINT_MAX:
                        base["error"] = (f"the package's fgId is not a plain whole number ({perr or repr(_rm_plain(pid))}): "
                                         "setGlyphComponents was not called")
                        third = None
                    else:
                        third, labels[2] = pid, f"package.fgId ({pid})"
                        base["package_fgid"] = pid
                fourth = False
                if base.get("int") == "yes":     # v0.162: live 1034 ("flPackage expected" for the fgId): 1033's Int error was the fourth, False
                    fourth, labels[3] = 0, "0"
                second = float(gwidth)
                if base.get("width") == "int":     # v0.163: live 1035 ("must be Boolean" for 0 fourth): 1033's Int error was an earlier one
                    if float(gwidth) != int(gwidth):
                        base["error"] = f"the width {gwidth!r} is not a whole number: setGlyphComponents was not called"
                    else:
                        second, labels[1] = int(gwidth), f"{int(gwidth)} (a whole number)"
                first = comps
                if base.get("items") == "id" and "error" not in base:     # v0.164: live 1036: "must be Int" with a whole width too
                    ids = []
                    if type(comps) not in (list, tuple):
                        base["error"] = "items=id needs a real Python list of GlyphComponent: setGlyphComponents was not called"
                    for it in (comps if type(comps) in (list, tuple) else []):
                        nid, nerr = _tl_call(lambda i=it: _call0(i, "name_id"))
                        if nerr is not None or type(nid) is not int or not 0 <= nid <= _TRYNOTIFY_UINT_MAX:
                            base["error"] = (f"a component's name_id is not a plain whole number ({nerr or repr(_rm_plain(nid))}): "
                                             "setGlyphComponents was not called")
                            break
                        ids.append(nid)
                    if "error" not in base:
                        first, labels[0] = ids, repr(ids)
                        base["items_passed"] = ids
                if "error" not in base:
                    call_args = (first, second, third, fourth, 0)[:n]
                    step, touched = "layer.setGlyphComponents(" + ", ".join(labels[:n]) + ")", True
                    base["call_made"] = step
                    ret = layer.setGlyphComponents(*call_args)
                    base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    if touched:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["target_state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the target has no modern active layer after the call"}
    result["target_elements_after"] = tel2
    after = _tryedit_snapshot(target)
    result["target_after"] = after
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    src_after = {p: _tryedit_snapshot(p) for p in parts}
    result["recipe_glyphs_after"] = src_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    result["source_changed"] = any("error" in src_after[p] or src_after[p]["contours"] != src_before[p]["contours"] for p in parts)
    result["changed"] = ("unknown" if ("error" in after or isinstance(tel2, dict)) else
                         (tel2 != tel or after["contours"] != before["contours"] or after_state != state))
    widths_ok = (width_before, float(gwidth)) if (stage == "setgenerated" and isinstance(gwidth, (int, float))
                                                  and not isinstance(gwidth, bool)) else (width_before,)
    result["width_changed"] = (width_after != width_before) if isinstance(width_after, float) else "unknown"
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"] or result["source_changed"]
                                          or width_after not in widths_ok
                                          or (stage == "generate" and result["changed"] is not False))
    if stage == "setgenerated":
        if isinstance(tel2, dict):
            result["placed"] = result["existing_kept"] = "unknown"
        else:
            comps2 = [e for e in tel2 if e.get("is_component") is True]
            plain = [e for e in tel2 if e.get("is_component") is False]
            result["placed"] = ([e.get("component_glyph") for e in comps2] == parts
                                and all(_trycomp_offset_ok(e.get("matrix"), 0, 0) for e in comps2))
            result["existing_kept"] = (len(plain) >= len(tel) and "error" not in after
                                       and _trycomp_holds(after.get("contours") or [], before["contours"]))
        result["component_placed"] = bool("error" not in result and result["placed"] is True and result["existing_kept"] is True
                                          and not result["side_effect_detected"])
    if result["changed"] is not False:
        _guard_mark(font, target, "trycomponent", result,
                    no_mark=None if result.get("component_placed") is True else
                    ("generateGlyph changed the target, which it was not asked to do" if stage == "generate" else "the component was not confirmed"))
    return result


def _trycomp_auto_state(layer):
    """v0.165: {"recipe", "auto_layer"} of a layer, each as read or "<error: ...>". Read only. Never raises."""
    out = {}
    for key, attr, kind in (("recipe", "recipe", str), ("auto_layer", "autoLayer", bool)):
        v, err = _tl_call(lambda a=attr: _call0(layer, a))
        out[key] = v if (err is None and type(v) is kind) else f"<error: {err or type(v).__name__}>"
    return out


def _trycomp_timed(fn, *args, **kwargs):
    """v0.173: fn's reply with elapsed_seconds, the whole request inside the listener (reads, the call, the read-back)."""
    t0 = time.perf_counter()
    out = fn(*args, **kwargs)
    if isinstance(out, dict):
        out["elapsed_seconds"] = round(time.perf_counter() - t0, 3)
    return out


def _trycomp_auto(*args, **kwargs):
    """v0.173: _trycomp_auto_run, timed."""
    return _trycomp_timed(_trycomp_auto_run, *args, **kwargs)


_TRYCOMP_NONEMPTY_STEPS = ("setrecipe", "setauto", "build", "unauto", "clearrecipe")     # v0.180
_TRYCOMP_BASELINE = {}     # v0.180: target -> what step=setrecipe&nonempty=yes found in it, for THIS listener run only


def _trycomp_existing(layer, tel):
    """v0.180: the elements `tel` of `layer` in a comparable form, one row each in layer order: {"index", "is_component",
    "component_glyph", "component_layer", "matrix", "ink_box"} (the glyph and layer only for a component), or {"error"}. ONE
    inkBox() per element, through _tryshapebox_boxes. Read only. Never raises."""
    rows, why = _tryshapebox_boxes(layer)
    if rows is None:
        return {"error": why}
    if len(rows) != len(tel):
        return {"error": f"{len(rows)} ink box(es) for {len(tel)} element(s)"}
    out = []
    for e, r in zip(tel, rows):
        box = r.get("ink_box")
        if not isinstance(box, dict) or "error" in box:
            return {"error": f"the ink box of element {e.get('index')} could not be read ({(box or {}).get('error') if isinstance(box, dict) else box})"}
        comp = e.get("is_component") is True
        out.append({"index": e.get("index"), "is_component": e.get("is_component"),
                    "component_glyph": e.get("component_glyph") if comp else None,
                    "component_layer": e.get("component_layer") if comp else None, "matrix": e.get("matrix"), "ink_box": box})
    return out


def _trycomp_same_element(a, b):
    """v0.180: True when two rows of _trycomp_existing are the same element: kind, source and source layer equal, the matrix and the
    ink box equal within 0.001."""
    if any(a.get(k) != b.get(k) for k in ("is_component", "component_glyph", "component_layer")):
        return False
    ma, mb = a.get("matrix"), b.get("matrix")
    if not all(isinstance(m, dict) and all(isinstance(m.get(k), (int, float)) for k in _TRYCOMP_MATRIX_KEYS) for m in (ma, mb)):
        return False
    if any(abs(ma[k] - mb[k]) > 0.001 for k in _TRYCOMP_MATRIX_KEYS):
        return False
    ba, bb = a.get("ink_box"), b.get("ink_box")
    if (isinstance(ba, dict) and "not_read" in ba) or (isinstance(bb, dict) and "not_read" in bb):     # v0.185: a brush shape, no inkBox()
        return isinstance(ba, dict) and isinstance(bb, dict) and "not_read" in ba and "not_read" in bb
    return _comp_box_at(ba, bb) is True


def _trycomp_match_existing(base_rows, now_rows):
    """v0.180: (missing, new): each row of `base_rows` is matched to the first unused equal row of `now_rows`; missing lists the
    base indices with no match, new the indices of `now_rows` left unmatched."""
    used, missing = set(), []
    for i, b in enumerate(base_rows):
        j = next((j for j, n in enumerate(now_rows) if j not in used and _trycomp_same_element(b, n)), None)
        if j is None:
            missing.append(i)
        else:
            used.add(j)
    return missing, [j for j in range(len(now_rows)) if j not in used]


def _trycomp_auto_run(mod, target, step, parts, base, nonempty=False):
    """v0.165, stage=auto: ONE step of the layer's own recipe build on an existing, empty target layer (read: nothing changed).
    v0.180, nonempty=True: the same steps on a target that already holds plain contours and / or components of cpp glyphs; what
    was there is compared with what step=setrecipe found (existing_kept). Read back as the other stages. Never raises."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error=("the target cannot be used: " + str(refusal.get("reason") or refusal) + " (a glyph with no layer is never "
                                 "touched by this probe: the Add Component crash)"), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state_before"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer: nothing was touched")
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was touched")
    base["target_elements_before"] = tel
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    leaving = step in ("unauto", "killauto")     # v0.166: on a layer buildAuto() filled (live 1041b)
    clearing = step == "clearrecipe"             # v0.168: on a normal component layer (as after 1042, 1050)
    existing = None
    if nonempty:     # v0.180: plain contours and components of cpp glyphs only; a Power Brush or unreadable shape is never touched (F1)
        if not tel:
            return dict(base, error=("the target holds no element: nonempty=yes is for a target that already holds contours or "
                                     "components (send the step without it): nothing was touched"))
        for e in tel:
            if e.get("is_component") is True:
                if not _trycomp_name_ok(e.get("component_glyph")):
                    return dict(base, error=(f"element {e.get('index')} is a component of {e.get('component_glyph')!r}, not of a cpp "
                                             "glyph: nothing was touched"))
            elif e.get("is_component") is not False or e.get("is_composite") is not False:
                return dict(base, error=(f"element {e.get('index')} is not a plain contour shape (is_component "
                                         f"{e.get('is_component')!r}, is_composite {e.get('is_composite')!r}): a Power Brush or "
                                         "unreadable shape is never touched by this probe, nothing was touched"))
        existing = _trycomp_existing(layer, tel)
        if isinstance(existing, dict):
            return dict(base, error=f"the target's elements could not be compared ({existing['error']}): nothing was touched")
        base["existing_before"] = existing
    if leaving or clearing:
        want_auto = not clearing
        if auto_before.get("auto_layer") is not want_auto:
            return dict(base, error=f"the layer's autoLayer reads {auto_before.get('auto_layer')!r}, not {want_auto}: nothing was touched")
        if nonempty:
            names = [e.get("component_glyph") for e in tel if e.get("is_component") is True]
            if not names:
                return dict(base, error="the layer holds no component for this step: nothing was touched")
        else:
            names = [e.get("component_glyph") for e in tel]
            if not tel or any(e.get("is_component") is not True for e in tel) or not all(_trycomp_name_ok(n) for n in names):
                return dict(base, error="the layer must hold only components of cpp glyphs for this step: nothing was touched")
        if clearing:
            rec = auto_before.get("recipe")
            if not isinstance(rec, str) or rec == "" or rec.startswith("<error"):
                return dict(base, error=f"the layer's recipe reads {rec!r}: there is no readable recipe to clear, nothing was touched")
        parts = list(dict.fromkeys(names)) if nonempty else names
    elif step != "read" and not nonempty and (len(tel) != 0 or _state_has_components(state)):
        return dict(base, error="the target must be empty (no shape, no component) for this step: nothing was touched")
    if step == "build" and auto_before.get("recipe") != "+".join(parts):
        return dict(base, error=f"the layer's recipe reads {auto_before.get('recipe')!r}, not {'+'.join(parts)!r}: buildAuto() was not called")
    src_before = {}
    for p in parts or []:
        snap = _tryedit_snapshot(p)
        if "error" in snap:
            return dict(base, error=f"the recipe glyph {p!r} could not be read ({snap['error']}): nothing was touched")
        src_before[p] = snap
    before = _tryedit_snapshot(target)
    if "error" in before:
        return dict(base, error=f"the target's outline could not be read ({before['error']}): nothing was touched")
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    if nonempty and step == "setrecipe":     # v0.180: the first step of a series records what the target holds
        _TRYCOMP_BASELINE[target] = {"elements": existing, "contours": before["contours"]}
    step_name, touched = "reading the layer", False
    try:
        if step == "setrecipe":
            step_name, touched = "layer.recipe = recipe", True
            layer.recipe = "+".join(parts)
        elif step == "setauto":
            step_name, touched = "layer.autoLayer = True", True
            layer.autoLayer = True
        elif step == "build":
            step_name, touched = "layer.buildAuto()", True
            t_build = time.perf_counter()     # v0.173: how long FontLab's build took
            ret = layer.buildAuto()
            base["build_seconds"] = round(time.perf_counter() - t_build, 3)
            base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        elif step == "unauto":
            step_name, touched = "layer.autoLayer = False", True
            layer.autoLayer = False
        elif step == "killauto":
            step_name, touched = "layer.killAuto()", True
            ret = layer.killAuto()
            base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        elif step == "clearrecipe":
            step_name, touched = 'layer.recipe = ""', True
            layer.recipe = ""
    except Exception as exc:
        base["error"] = f"{step_name} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    if touched:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["target_state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the target has no modern active layer after the step"}
    result["target_elements_after"] = tel2
    result["auto_after"] = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    after = _tryedit_snapshot(target)
    result["target_after"] = after
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    src_after = {p: _tryedit_snapshot(p) for p in parts or []}
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    result["source_changed"] = any("error" in src_after[p] or src_after[p]["contours"] != src_before[p]["contours"] for p in parts or [])
    shape_changed = ("unknown" if ("error" in after or isinstance(tel2, dict)) else
                     (tel2 != tel or after["contours"] != before["contours"] or after_state != state))
    result["outline_changed"] = shape_changed
    auto_after = result["auto_after"]
    expected_auto = dict(auto_before)
    if step == "setrecipe":
        expected_auto["recipe"] = "+".join(parts)
    elif step == "setauto":
        expected_auto["auto_layer"] = True
    elif clearing:
        expected_auto["recipe"] = ""
    elif leaving:
        expected_auto["auto_layer"] = False
        if step == "killauto":     # what killAuto() does to the recipe is not known: reported, not counted as a side effect
            expected_auto["recipe"] = auto_after.get("recipe")
    result["step_took_effect"] = ((auto_after == expected_auto) if step in ("setrecipe", "setauto", "clearrecipe") else
                                  (auto_after.get("auto_layer") is False) if leaving else "not applicable")
    unexpected_auto = {k: auto_after.get(k) for k in ("recipe", "auto_layer") if auto_after.get(k) != expected_auto.get(k)}
    if nonempty:     # v0.180: what the target held at step=setrecipe, found again after this step?
        bl = _TRYCOMP_BASELINE.get(target)
        rows2 = (_trycomp_existing(layer2, tel2) if (layer2 is not None and not isinstance(tel2, dict)) else
                 {"error": "the target's elements could not be read after the step"})
        result["existing_after"] = rows2
        if bl is None:
            result["existing_kept"] = "unknown"
            result["existing_note"] = ("no step=setrecipe&nonempty=yes on this target in this listener run, so there is nothing to "
                                       "compare with")
        elif isinstance(rows2, dict) or "error" in after:
            result["existing_kept"] = "unknown"
        else:
            missing, new = _trycomp_match_existing(bl["elements"], rows2)
            result["existing_missing"] = [bl["elements"][i] for i in missing]
            result["new_elements"] = [rows2[j] for j in new]
            result["existing_contours_in_outline"] = _trycomp_holds(after["contours"], bl["contours"])
            result["existing_kept"] = bool(not missing and result["existing_contours_in_outline"])
    width_counts = not (nonempty and step == "build")     # v0.180: a build's width is reported, not counted (FontLab sets it, 1254)
    if not width_counts:
        result["width_changed_by_build"] = width_after != width_before
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"] or result["source_changed"]
                                          or (width_counts and width_after != width_before) or unexpected_auto
                                          or (step != "build" and shape_changed is not False))
    if step == "build" and nonempty:
        nw = result.get("new_elements")
        result["placed"] = ("unknown" if (result.get("existing_kept") == "unknown" or nw is None) else
                            bool(result["existing_kept"] is True and all(r.get("is_component") is True for r in nw)
                                 and [r.get("component_glyph") for r in nw] == parts))
        result["component_placed"] = bool("error" not in result and result["placed"] is True and not result["side_effect_detected"])
    elif step == "build":
        if isinstance(tel2, dict):
            result["placed"] = "unknown"
        else:
            comps2 = [e for e in tel2 if e.get("is_component") is True]
            result["placed"] = (len(comps2) == len(tel2) and [e.get("component_glyph") for e in comps2] == parts
                                and all(_trycomp_offset_ok(e.get("matrix"), 0, 0) for e in comps2))
        result["component_placed"] = bool("error" not in result and result["placed"] is True and not result["side_effect_detected"])
    if leaving or clearing:
        def _key(els):
            return [(e.get("is_component"), e.get("component_glyph"), e.get("component_layer"), e.get("matrix")) for e in els]
        result["component_kept"] = (not isinstance(tel2, dict) and "error" not in after and _key(tel2) == _key(tel)
                                    and after["contours"] == before["contours"])
        if clearing:
            result["recipe_cleared"] = bool("error" not in result and result["component_kept"] is True
                                            and result["step_took_effect"] is True and not result["side_effect_detected"])
            confirmed = result["recipe_cleared"]
        else:
            result["component_normal"] = bool("error" not in result and result["component_kept"] is True
                                              and auto_after.get("auto_layer") is False and not result["side_effect_detected"])
            confirmed = result["component_normal"]
        if nonempty and result.get("existing_kept") is not True:     # v0.180: marked only when what was there is still there
            confirmed = False
        if confirmed:
            _guard_mark(font, target, "trycomponent", result)
        elif shape_changed is not False:
            _guard_mark(font, target, "trycomponent", result, no_mark="the component did not stay as it was")
        return result
    if shape_changed is not False:
        _guard_mark(font, target, "trycomponent", result,
                    no_mark=None if result.get("component_placed") is True else "the change was not a confirmed component")
    return result


def _trycomp_first_box(layer):
    """v0.167: the ink box of the layer's only element ({left, right, top, bottom, width, height}) or {"error"}. ONE inkBox()."""
    if layer is None:
        return {"error": "no layer"}
    rows, why = _tryshapebox_boxes(layer)
    if rows is None:
        return {"error": why}
    if len(rows) != 1:
        return {"error": f"the layer has {len(rows)} elements, not one: no box compared"}
    return rows[0]["ink_box"]


def _trycomp_box_moved(b0, b1, dx, dy):
    """v0.167: True / False when both boxes are plain numbers (left / right by dx, top / bottom by dy, width / height kept, within
    0.001); "unknown" otherwise."""
    shifts = (("left", dx), ("right", dx), ("top", dy), ("bottom", dy), ("width", 0), ("height", 0))
    if any("error" in b or any(k not in b for k, _s in shifts) for b in (b0, b1)):
        return "unknown"
    return all(abs(b1[k] - b0[k] - float(s)) <= 0.001 for k, s in shifts)


def _trycomp_plain_offset(m):
    """v0.171: (dx, dy) when `m` is a plain offset (no scale, slant or rotation, within 0.001), else None."""
    if not isinstance(m, dict) or any(k not in m for k in _TRYCOMP_MATRIX_KEYS):
        return None
    if not _trycomp_offset_ok(m, m["dx"], m["dy"]):
        return None
    return m["dx"], m["dy"]


def _trycomp_all_boxes(layer):
    """v0.171: the ink box of every element, in layer.shapes order ([{left, right, ...}, ...]), or {"error"}. ONE inkBox() each."""
    if layer is None:
        return {"error": "no layer"}
    rows, why = _tryshapebox_boxes(layer)     # v0.174: no element limit
    if rows is None:
        return {"error": why}
    return [r["ink_box"] for r in rows]


def _trycomp_offset(*args, **kwargs):
    """v0.173: _trycomp_offset_run, timed."""
    return _trycomp_timed(_trycomp_offset_run, *args, **kwargs)


def _trycomp_offset_run(target, how, dx, dy, qt_cls, base, element=None):
    """v0.167, stage=offset: ONE offset of the only component on the target's layer (identity before, autoLayer False), through
    shape.transform = QTransform (how=assign) or ONE shape.applyTransform(QTransform) (how=apply). Read back. Never raises.
    v0.171, element=I (how=assign only): on a layer of 2 to _TRYCOMP_SEVERAL_MAX (5 since v0.172) components of cpp glyphs, each at a plain offset, ONE assignment
    shape.transform = QTransform(1, 0, 0, 1, dx, dy) on element I only (absolute; it must differ from I's offset); the other
    elements must stay exactly as they were."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state_before"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer: nothing was touched")
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was touched")
    base["target_elements_before"] = tel
    auto_before = _trycomp_auto_state(layer)
    base["auto_before"] = auto_before
    if auto_before.get("auto_layer") is not False:
        return dict(base, error=f"the layer's autoLayer reads {auto_before.get('auto_layer')!r}, not False: nothing was touched")
    several = element is not None
    if several:
        if not 2 <= len(tel) <= _TRYCOMP_SEVERAL_MAX or any(e.get("is_component") is not True or not _trycomp_name_ok(e.get("component_glyph"))
                                                            for e in tel):
            return dict(base, error=(f"element= needs a layer of 2 to {_TRYCOMP_SEVERAL_MAX} elements, each a component of a cpp glyph: "
                                     "nothing was touched"))
        if element >= len(tel):
            return dict(base, error=f"element {element} does not exist: the layer holds {len(tel)} elements (0 to {len(tel) - 1}): nothing was touched")
        offsets = [_trycomp_plain_offset(e.get("matrix")) for e in tel]
        if any(o is None for o in offsets):
            return dict(base, error="every component's matrix must read as a plain offset (no scale, slant or rotation): nothing was touched")
        ox, oy = offsets[element]
        base["offset_before"] = {"dx": ox, "dy": oy}
        if abs(ox - dx) <= 0.001 and abs(oy - dy) <= 0.001:
            return dict(base, error=f"element {element} already reads the offset ({dx}, {dy}): nothing was touched")
        idx = element
    else:
        if len(tel) != 1 or tel[0].get("is_component") is not True or not _trycomp_name_ok(tel[0].get("component_glyph")):
            return dict(base, error="the layer must hold exactly one element, a component of a cpp glyph: nothing was touched")
        if not _trycomp_offset_ok(tel[0].get("matrix"), 0, 0):
            return dict(base, error="the component's matrix does not read as the identity: nothing was touched")
        ox, oy, idx = 0.0, 0.0, 0
    source = tel[idx]["component_glyph"]
    base["source"] = source
    sources = []
    for e in tel:
        if e["component_glyph"] not in sources:
            sources.append(e["component_glyph"])
    src_before = {}
    for s in sources:
        snap = _tryedit_snapshot(s)
        if "error" in snap:
            return dict(base, error=f"the source {s!r} could not be read ({snap['error']}): nothing was touched")
        src_before[s] = snap
    before = _tryedit_snapshot(target)
    if "error" in before:
        return dict(base, error=f"the target's outline could not be read ({before['error']}): nothing was touched")
    base["target_before"] = before
    if several:
        boxes_before = _trycomp_all_boxes(layer)
        base["ink_boxes_before"] = boxes_before
        if isinstance(boxes_before, dict) or len(boxes_before) != len(tel) or any("error" in b for b in boxes_before):
            return dict(base, error="the components' ink boxes could not all be read: nothing was touched")
    else:
        box_before = _trycomp_first_box(layer)
        base["ink_box_before"] = box_before
        if "error" in box_before:
            return dict(base, error=f"the component's ink box could not be read ({box_before['error']}): nothing was touched")
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list or len(shapes) != len(tel):
        return dict(base, error=f"the target's layer.shapes is no longer a plain list of {len(tel) if several else 'one'}: nothing was touched")
    shape = shapes[idx]
    if several:
        sd, err = _tl_call(lambda: shape.shapeData)
        named, err2 = (None, err or "shapeData is None") if (err is not None or sd is None) else _tl_call(lambda: _call0(sd, "componentGlyph"))
        if err2 is not None or named != source:
            return dict(base, error=(f"the shape at position {idx} names {named!r}, not {source!r} as read before: nothing was touched"
                                     if err2 is None else f"the shape at position {idx} could not be checked ({err2}): nothing was touched"))
    step, touched = "QTransform(1, 0, 0, 1, dx, dy)", False
    try:
        tx = qt_cls(1.0, 0.0, 0.0, 1.0, float(dx), float(dy))
        m, why = _trycomp_matrix(tx)
        base["built_matrix"] = m if m is not None else {"error": why}
        if not _trycomp_offset_ok(m, dx, dy):
            return dict(base, error="the QTransform built does not read as the offset asked for: nothing was touched")
        step, touched = _TRYCOMP_OFFSET_HOWS[how], True
        if how == "assign":
            shape.transform = tx
        else:
            ret = shape.applyTransform(tx)
            base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    if touched:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["target_state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the target has no modern active layer after the call"}
    result["target_elements_after"] = tel2
    result["auto_after"] = _trycomp_auto_state(layer2) if layer2 is not None else {"error": "no layer"}
    if several:
        boxes_after = _trycomp_all_boxes(layer2)
        result["ink_boxes_after"] = boxes_after
        box_ok = not isinstance(boxes_after, dict) and len(boxes_after) == len(tel)
        box_before, box_after = boxes_before[idx], (boxes_after[idx] if box_ok else {"error": "the boxes could not be read after"})
    else:
        box_after = _trycomp_first_box(layer2)
        result["ink_box_after"] = box_after
    after = _tryedit_snapshot(target)
    result["target_after"] = after
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    src_after = {s: _tryedit_snapshot(s) for s in sources}
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    result["source_changed"] = ("unknown" if any("error" in src_after[s] for s in sources) else
                                any(src_after[s]["contours"] != src_before[s]["contours"] for s in sources))
    same_count = not isinstance(tel2, dict) and len(tel2) == len(tel)
    result["matrix_reads_offset"] = (same_count and tel2[idx].get("is_component") is True
                                     and tel2[idx].get("component_glyph") == source
                                     and tel2[idx].get("component_layer") == tel[idx].get("component_layer")
                                     and _trycomp_offset_ok(tel2[idx].get("matrix"), dx, dy))
    result["ink_box_moved"] = _trycomp_box_moved(box_before, box_after, dx - ox, dy - oy)
    if "error" in after:
        result["raw_nodes"] = "unknown"
    elif several:     # which raw contours belong to which component is not known: reported only, not part of the verdict
        result["raw_nodes"] = "unchanged" if (after.get("contours") or []) == before["contours"] else "changed"
    else:
        got = after.get("contours") or []
        result["raw_nodes"] = ("unchanged" if got == before["contours"] else
                               "moved by the offset" if got == _trycomp_shift(before["contours"], dx, dy) else False)
    if several:
        def _key(e):
            return (e.get("is_component"), e.get("component_glyph"), e.get("component_layer"), e.get("matrix"))
        result["others_kept"] = bool(same_count and box_ok and all(_key(tel2[i]) == _key(tel[i]) and boxes_after[i] == boxes_before[i]
                                                                   for i in range(len(tel)) if i != idx))
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"]
                                          or result["source_changed"] is not False or width_after != width_before
                                          or result["auto_after"] != auto_before)
    result["changed"] = ("unknown" if ("error" in after or isinstance(tel2, dict) or "error" in box_after) else
                         (tel2 != tel or after["contours"] != before["contours"] or after_state != state or box_after != box_before
                          or (several and boxes_after != boxes_before)))
    raw_ok = result["raw_nodes"] in (("unchanged", "changed") if several else ("unchanged", "moved by the offset"))
    result["offset_placed"] = bool("error" not in result and result["matrix_reads_offset"] is True and result["ink_box_moved"] is True
                                   and raw_ok and not result["side_effect_detected"] and (not several or result["others_kept"]))
    if result["changed"] is not False:
        _guard_mark(font, target, "trycomponent", result, no_mark=None if result["offset_placed"] else "the offset was not confirmed")
    return result


# --------------------------------------------------------------------------
# /debug/markswitch (v0.170) - RESEARCH for S1 (the user's choice of 2026-11-17: make clear whether add_component alone brings FontLab's
# save question). Demo mode cannot save, so a font can never return to "unchanged", and every tool that sets up a test glyph marks the
# font. This switch lets a test set up glyphs UNMARKED (unmarked tool writes brought no question in 467 and 472), switch the mark on,
# make the one write under test, and close the font. Read only without "on"; with on=0 / on=1 it needs go=yes. It changes only the
# listener's own _MARK_CHANGED for this run (a listener restart sets it True again); no FontLab call, no font touched. While it is
# off, every write reply says so in fontlab_changed_mark ("switched off in the listener"), and the OUTPUT panel says it once.
# --------------------------------------------------------------------------

def debug_mark_switch(on, go):
    global _MARK_CHANGED
    before = _MARK_CHANGED
    if on is None or not str(on).strip():
        return {"mark_changed": before, "note": "read only; on=0 or on=1 with go=yes switches the changed mark for this listener run"}
    on = str(on).strip()
    if on not in ("0", "1"):
        return {"error": 'on must be "0" (off) or "1" (on)', "mark_changed": before}
    want = on == "1"
    if go != "yes":
        return {"error": (f"this switches the changed mark {'ON' if want else 'OFF'} for this listener run: verified writes "
                          f"{'tell' if want else 'no longer tell'} FontLab that the font changed. Add &go=yes to run it."), "mark_changed": before}
    _MARK_CHANGED = want
    if want != before:
        print(f"[glyphbridge] the changed mark is now {'ON' if want else 'OFF'}: verified writes "
              f"{'are' if want else 'are NOT'} marked as changes in FontLab until it is switched again or the listener restarts.")
    return {"mark_changed_before": before, "mark_changed": _MARK_CHANGED,
            "note": "for this listener run only; a listener restart switches the changed mark on again"}


def debug_try_component(stage, target, source, go, dx=None, dy=None, recipe=None, nargs=None, pkgmode=None, intmode=None,
                        widthmode=None, itemsmode=None, step=None, how=None, element=None, recursive=None, nonempty=None,
                        brush=None, sync=None):
    import sys as _sys
    if stage not in _TRYCOMP_STAGES + _TRYCOMP_REMOVE_STAGES + ("templayer", "fixlayer"):
        return {"error": "stage must be one of: " + ", ".join(_TRYCOMP_STAGES + _TRYCOMP_REMOVE_STAGES + ("templayer", "fixlayer"))}
    if stage != "templayer":     # v0.185: brush and sync belong to stage=templayer only
        for label, raw in (("brush", brush), ("sync", sync)):
            if raw is not None and str(raw).strip():
                return {"error": f"{label} is taken by stage=templayer only"}
    if stage == "fixlayer":     # v0.183: its own parameters, gate and counter
        if not _trycomp_name_ok(target):
            return {"error": 'target must start with "cpp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
        for label, raw in (("source", source), ("dx", dx), ("dy", dy), ("recipe", recipe), ("args", nargs), ("pkg", pkgmode),
                           ("int", intmode), ("width", widthmode), ("items", itemsmode), ("step", step), ("how", how),
                           ("recursive", recursive), ("nonempty", nonempty)):
            if raw is not None and str(raw).strip():
                return {"error": f"stage=fixlayer takes no {label}"}
        return _trycomp_fixlayer_gate(target, element, go)
    if stage == "templayer":     # v0.181: its own parameters, gate and counter
        if not _trycomp_name_ok(target):
            return {"error": 'target must start with "cpp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
        for label, raw in (("source", source), ("dx", dx), ("dy", dy), ("args", nargs), ("pkg", pkgmode), ("int", intmode),
                           ("width", widthmode), ("items", itemsmode), ("how", how), ("element", element), ("recursive", recursive),
                           ("nonempty", nonempty)):
            if raw is not None and str(raw).strip():
                return {"error": f"stage=templayer takes no {label}"}
        return _trycomp_templayer_gate(target, step, recipe, go, brush, sync)
    on_nonempty = False     # v0.180
    if nonempty is not None and str(nonempty).strip():
        if stage != "auto":
            return {"error": "nonempty is used only by stage=auto"}
        if str(nonempty).strip() != "yes":
            return {"error": 'nonempty must be "yes" (the steps on a target that already holds contours or components)'}
        if str(step or "").strip() not in _TRYCOMP_NONEMPTY_STEPS:
            return {"error": "nonempty=yes works with step=" + "|".join(_TRYCOMP_NONEMPTY_STEPS) + " only"}
        on_nonempty = True
    if stage in _TRYCOMP_REMOVE_STAGES:     # v0.176: the remove stages have their own parameters and gate
        if not _trycomp_name_ok(target):
            return {"error": 'target must start with "cpp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
        for label, raw in (("source", source), ("dx", dx), ("dy", dy), ("recipe", recipe), ("args", nargs), ("pkg", pkgmode), ("int", intmode),
                           ("width", widthmode), ("items", itemsmode), ("step", step), ("how", how)):
            if raw is not None and str(raw).strip():
                return {"error": f"stage={stage} takes no {label}"}
        return _trycomp_remove_gate(stage, target, go, element, recursive)
    if recursive is not None and str(recursive).strip():
        return {"error": "recursive is used only by stage=removeshape"}
    gen = stage in _TRYCOMP_GEN_STAGES
    auto = stage == "auto"
    offset = stage == "offset"     # v0.167
    for label, nm in ((("target", target),) if (stage == "readcomponents" or gen or auto or offset) else (("target", target), ("source", source))):
        if not _trycomp_name_ok(nm):
            return {"error": f'{label} must start with "cpp" and be 4 to 40 characters from A-Z a-z 0-9 . _ -'}
    if how is not None and str(how).strip() and not offset:
        return {"error": "how is used only by stage=offset"}
    if offset:
        how = str(how or "").strip()
        if how not in _TRYCOMP_OFFSET_HOWS:
            return {"error": "how must be one of: " + ", ".join(_TRYCOMP_OFFSET_HOWS)}
        if source is not None and str(source).strip():
            return {"error": "stage=offset takes no source: the component's own source glyph is used"}
        if recipe is not None and str(recipe).strip():
            return {"error": "stage=offset takes no recipe"}
    elem = None
    if element is not None and str(element).strip():     # v0.171
        if not offset:
            return {"error": "element is used only by stage=offset"}
        if how != "assign":
            return {"error": "element= works with how=assign only"}
        elem, err = _tryedit_int(element, "element", 0, _TRYCOMP_SEVERAL_MAX - 1)
        if err is not None:
            return {"error": err}
    parts = None
    if gen:
        parts, err = _trycomp_recipe(recipe, target)
        if err is not None:
            return {"error": err}
    if step is not None and str(step).strip() and not auto:
        return {"error": "step is used only by stage=auto"}
    if auto:
        step = str(step or "").strip()
        if step not in _TRYCOMP_AUTO_STEPS:
            return {"error": "step must be one of: " + ", ".join(_TRYCOMP_AUTO_STEPS)}
        if step in ("setrecipe", "build"):
            parts, err = _trycomp_recipe(recipe, target, most=_TRYCOMP_AUTO_PARTS_MAX)     # v0.171 / v0.172: up to five glyphs
            if err is not None:
                return {"error": err}
        elif recipe is not None and str(recipe).strip():
            return {"error": f"step={step} takes no recipe"}
    n_args = 5
    if nargs is not None and str(nargs).strip():
        if stage != "setgenerated":
            return {"error": "args is used only by stage=setgenerated"}
        n_args, err = _tryedit_int(nargs, "args", 2, 5)
        if err is not None:
            return {"error": err}
    pkg_id = False
    if pkgmode is not None and str(pkgmode).strip():
        if stage != "setgenerated":
            return {"error": "pkg is used only by stage=setgenerated"}
        if str(pkgmode).strip() != "id":
            return {"error": 'pkg must be "id" (the package\'s fgId as the third argument)'}
        pkg_id = True
    as_int = False
    if intmode is not None and str(intmode).strip():
        if stage != "setgenerated":
            return {"error": "int is used only by stage=setgenerated"}
        if str(intmode).strip() != "yes":
            return {"error": 'int must be "yes" (False passed as the whole number 0)'}
        as_int = True
    width_int = False
    if widthmode is not None and str(widthmode).strip():
        if stage != "setgenerated":
            return {"error": "width is used only by stage=setgenerated"}
        if str(widthmode).strip() != "int":
            return {"error": 'width must be "int" (the width passed as a whole number)'}
        width_int = True
    items_id = False
    if itemsmode is not None and str(itemsmode).strip():
        if stage != "setgenerated":
            return {"error": "items is used only by stage=setgenerated"}
        if str(itemsmode).strip() != "id":
            return {"error": 'items must be "id" (each component\'s name_id in place of the GlyphComponent)'}
        items_id = True
    reading = stage == "readcomponents"
    if not reading and not gen and not auto and not offset and target == source:
        return {"error": "target and source must be two different glyphs"}
    args = {}
    for label, raw in ((("dx", dx), ("dy", dy)) if not (reading or gen or auto) else ()):
        v, err = _tryedit_int(raw, label, -_TRYCOMP_DELTA_MAX, _TRYCOMP_DELTA_MAX)
        if err is not None:
            return {"error": err}
        args[label] = v
    if offset and elem is None and args["dx"] == 0 and args["dy"] == 0:
        return {"error": "dx and dy are both 0: there is no offset to set"}
    if go != "yes":
        if offset and elem is not None:
            return {"error": f"stage=offset&how=assign&element={elem} calls {_TRYCOMP_OFFSET_HOWS[how]} once on component {elem} of the "
                             f"target's components, offset ({args['dx']}, {args['dy']}) (absolute); the others must stay as they are. "
                             "Add &go=yes to run it."}
        if offset:
            return {"error": f"stage=offset&how={how} calls {_TRYCOMP_OFFSET_HOWS[how]} once on the target's only component, offset "
                             f"({args['dx']}, {args['dy']}). Add &go=yes to run it."}
        if reading:
            return {"error": "stage=readcomponents reads the target's layer.components once and changes nothing. Add &go=yes to run it."}
        if auto:
            with_recipe = f", recipe {'+'.join(parts)}" if parts else ""
            on_what = (", on a target that already holds contours and / or components (what it holds is compared with what "
                       "step=setrecipe found)" if on_nonempty else "")
            return {"error": f"stage=auto&step={step} {_TRYCOMP_AUTO_STEPS[step]}{with_recipe}{on_what}. Add &go=yes to run it."}
        if gen:
            what = ("asks FontLab's generateGlyph what the recipe gives (it is not asked to change anything)" if stage == "generate" else
                    "asks FontLab's generateGlyph for the recipe and puts what it returns into the target through layer.setGlyphComponents")
            with_args = (f", with the first {n_args} of its 5 arguments" + (", the package's fgId as the third" if pkg_id else "")
                         + (", 0 in place of False" if as_int else "") + (", the width as a whole number" if width_int else "")
                         + (", each component's name_id in place of the GlyphComponent" if items_id else "")
                         if stage == "setgenerated" else "")
            return {"error": f"stage={stage} {what}{with_args}, recipe {'+'.join(parts)}. Add &go=yes to run it."}
        what = {"glyphcomponents": "places the source glyph as a component in the target through layer.setGlyphComponents",
                "shapedata": "adds a new shape on the source's shape data to the target through layer.addShape"}[stage]
        return {"error": f"stage={stage} {what}, offset ({args['dx']}, {args['dy']}). Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
    if _TRYCOMP["calls"] >= _TRYCOMP_MAX:
        return {"stage": stage, "error": f"the probe already ran {_TRYCOMP_MAX} times in this listener run; restart the listener to repeat it",
                "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
    if auto:
        _TRYCOMP["calls"] += 1     # counted BEFORE the glyph is read
        abase = {"stage": stage, "step": step, "target": target, "call": _TRYCOMP_AUTO_STEPS[step], "calls_so_far": _TRYCOMP["calls"],
                 "max_calls": _TRYCOMP_MAX, "note": _TRYCOMP_NOTE}
        if parts:
            abase["recipe"] = "+".join(parts)
        if on_nonempty:
            abase["nonempty"] = True
        return _trycomp_auto(mod, target, step, parts, abase, nonempty=on_nonempty)
    if offset:
        oqt_cls, oqt_src = _trycomp_qtransform_class(mod)
        if oqt_cls is None:
            return {"stage": stage, "error": oqt_src + ": nothing was touched", "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
        _TRYCOMP["calls"] += 1     # counted BEFORE the glyph is read
        return _trycomp_offset(target, how, args["dx"], args["dy"], oqt_cls,
                               dict({"stage": stage, "how": how, "target": target, "dx": args["dx"], "dy": args["dy"],
                                     "call": _TRYCOMP_OFFSET_HOWS[how], "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX,
                                     "qtransform": oqt_src, "note": _TRYCOMP_NOTE}, **({"element": elem} if elem is not None else {})),
                               element=elem)
    if gen:
        if getattr(mod, "FontMetrics", None) is None:
            return {"stage": stage, "error": "fontlab.FontMetrics is missing: nothing was touched", "calls_so_far": _TRYCOMP["calls"],
                    "max_calls": _TRYCOMP_MAX}
        _TRYCOMP["calls"] += 1     # counted BEFORE any glyph is read
        gbase = {"stage": stage, "target": target, "recipe": "+".join(parts), "call": _TRYCOMP_CALLS[stage],
                 "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX, "note": _TRYCOMP_NOTE}
        if stage == "setgenerated":
            gbase["args"] = n_args
            if pkg_id:
                gbase["pkg"] = "id"
            if as_int:
                gbase["int"] = "yes"
            if width_int:
                gbase["width"] = "int"
            if items_id:
                gbase["items"] = "id"
        return _trycomp_generate(mod, pkg, stage, target, parts, gbase)
    if reading:
        _TRYCOMP["calls"] += 1     # counted BEFORE the glyph is read
        return _trycomp_read_components(mod, target, {"stage": stage, "target": target, "call": _TRYCOMP_CALLS[stage],
                                                      "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX})
    qt_cls, qt_src = _trycomp_qtransform_class(mod)
    needed = "GlyphComponent" if stage == "glyphcomponents" else "flShape"
    if qt_cls is None or getattr(mod, needed, None) is None:
        return {"stage": stage, "error": (qt_src if qt_cls is None else f"fontlab.{needed} is missing") + ": nothing was touched",
                "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX}
    _TRYCOMP["calls"] += 1     # counted BEFORE either glyph is read or touched: whatever happens, it is on record
    dx, dy = args["dx"], args["dy"]
    base = {"stage": stage, "target": target, "source": source, "dx": dx, "dy": dy, "call": _TRYCOMP_CALLS[stage],
            "calls_so_far": _TRYCOMP["calls"], "max_calls": _TRYCOMP_MAX, "qtransform": qt_src, "note": _TRYCOMP_NOTE}
    # the source: one plain shape, no components, at least one node
    sctx, refusal = _modern_edit_target(source)
    if sctx is None:
        return dict(base, error="the source cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    sstate, slayer = _tryshape_modern_state(sctx["w"])
    base["source_state_before"] = sstate
    if slayer is None:
        return dict(base, error="the source has no modern active layer: nothing was touched")
    sel = _trycomp_elements(slayer)
    if isinstance(sel, dict):
        return dict(base, error=f"the source's elements could not be read ({sel['error']}): nothing was touched")
    base["source_elements_before"] = sel
    if len(sel) != 1 or sel[0].get("is_component") is not False or sel[0].get("is_composite") is not False:
        return dict(base, error=("the source must have exactly one plain shape (no component, no Power Brush or other composite shape): "
                                 "nothing was touched"))
    snodes = sstate.get("nodes")
    if _state_has_components(sstate) or not isinstance(snodes, int) or isinstance(snodes, bool) or snodes < 1:
        return dict(base, error=f"the source reads {_state_components_text(sstate)} and {snodes!r} nodes: nothing was touched")
    src_before = _tryedit_snapshot(source)
    if "error" in src_before:
        return dict(base, error=f"the source's outline could not be read ({src_before['error']}): nothing was touched")
    base["source_before"] = src_before
    # the target: an existing layer (never created here), at most one plain shape, no components
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error=("the target cannot be used: " + str(refusal.get("reason") or refusal) + " (a glyph with no layer is never "
                                 "given a component by this probe: the Add Component crash)"), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    state, layer = _tryshape_modern_state(w)
    base["target_state_before"] = state
    if layer is None:
        return dict(base, error="the target has no modern active layer: nothing was touched")
    tel = _trycomp_elements(layer)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was touched")
    base["target_elements_before"] = tel
    if len(tel) > 1 or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in tel):
        return dict(base, error="the target must have at most one shape, and a plain one: nothing was touched")
    if _state_has_components(state):
        return dict(base, error=f"the target reads {_state_components_text(state)}: nothing was touched")
    before = _tryedit_snapshot(target)
    if "error" in before:
        return dict(base, error=f"the target's outline could not be read ({before['error']}): nothing was touched")
    base["target_before"] = before
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    if stage == "glyphcomponents" and not isinstance(width_before, float):
        return dict(base, error=f"the target's advance width is not readable ({width_before}): nothing was touched")
    step, touched = "QTransform(1, 0, 0, 1, dx, dy)", False
    try:
        tx = qt_cls(1.0, 0.0, 0.0, 1.0, float(dx), float(dy))
        m, why = _trycomp_matrix(tx)
        base["built_matrix"] = m if m is not None else {"error": why}
        if not _trycomp_offset_ok(m, dx, dy):
            return dict(base, error="the QTransform built does not read as the offset asked for: nothing was touched")
        if stage == "glyphcomponents":
            step = "GlyphComponent(source)"
            gc = mod.GlyphComponent(source)
            step = "gc.transform = tx"
            gc.transform = tx
            gm, why = _trycomp_matrix(_tl_call(lambda: gc.transform)[0])
            base["detached_matrix"] = gm if gm is not None else {"error": why}
            nid, err = _tl_call(lambda: _call0(gc, "name_id"))
            base["glyph_component_name_id"] = nid if (err is None and isinstance(nid, int) and not isinstance(nid, bool)) else (
                f"<error: {err or type(nid).__name__}>")
            if not _trycomp_offset_ok(gm, dx, dy):
                return dict(base, error="the GlyphComponent's transform does not read back as the offset: nothing was touched")
            step, touched = _TRYCOMP_CALLS[stage], True
            ret = layer.setGlyphComponents([gc], float(width_before), pkg, False, 0)
        else:
            sshapes, err = _tl_call(lambda: slayer.shapes)
            if err is not None or type(sshapes) is not list or len(sshapes) != 1:
                return dict(base, error="the source's layer.shapes is no longer a plain list of one: nothing was touched")
            step = "source_shape.shapeData"
            sd = sshapes[0].shapeData
            step = "flShape(shapeData)"
            new_shape = mod.flShape(sd)
            step = "new_shape.transform = tx"
            new_shape.transform = tx
            nm_, why = _trycomp_matrix(_tl_call(lambda: new_shape.transform)[0])
            base["detached_matrix"] = nm_ if nm_ is not None else {"error": why}
            if not _trycomp_offset_ok(nm_, dx, dy):
                return dict(base, error="the new shape's transform does not read back as the offset: nothing was touched")
            step, touched = _TRYCOMP_CALLS[stage], True
            ret = layer.addShape(new_shape)
        base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    if touched:
        result["display_refreshed"] = _repaint_viewport()
    after_state, layer2 = _tryshape_modern_state(w)
    result["target_state_after"] = after_state
    tel2 = _trycomp_elements(layer2) if layer2 is not None else {"error": "the target has no modern active layer after the call"}
    result["target_elements_after"] = tel2
    after = _tryedit_snapshot(target)
    result["target_after"] = after
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    sstate2, slayer2 = _tryshape_modern_state(sctx["w"])
    result["source_state_after"] = sstate2
    sel2 = _trycomp_elements(slayer2) if slayer2 is not None else {"error": "the source has no modern active layer after the call"}
    result["source_elements_after"] = sel2
    src_after = _tryedit_snapshot(source)
    result["source_after"] = src_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    if isinstance(tel2, dict):
        result["placed"] = result["existing_kept"] = "unknown"
    else:
        comps = [e for e in tel2 if e.get("is_component") is True]
        plain = [e for e in tel2 if e.get("is_component") is False]
        result["placed"] = (len(comps) == 1 and comps[0].get("component_glyph") == source
                            and _trycomp_offset_ok(comps[0].get("matrix"), dx, dy))
        result["existing_kept"] = (len(plain) >= len(tel) and "error" not in after
                                   and _trycomp_holds(after.get("contours") or [], before["contours"]))
    if "error" in after:
        result["source_contours_in_outline"] = "unknown"
    else:
        got, sc = after.get("contours") or [], src_before["contours"]
        result["source_contours_in_outline"] = ("raw" if _trycomp_holds(got, sc) else
                                                "moved by the offset" if _trycomp_holds(got, _trycomp_shift(sc, dx, dy)) else False)
    result["width_changed"] = (width_after != width_before) if isinstance(width_after, float) else "unknown"
    result["source_changed"] = ("unknown" if "error" in src_after else src_after["contours"] != src_before["contours"])
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"] or result["source_changed"] is not False
                                          or result["width_changed"] is not False or isinstance(sel2, dict) or len(sel2) != 1)
    result["changed"] = ("unknown" if ("error" in after or isinstance(tel2, dict)) else
                         (tel2 != tel or after["contours"] != before["contours"] or after_state != state))
    result["component_placed"] = bool("error" not in result and result["placed"] is True and result["existing_kept"] is True
                                      and not result["side_effect_detected"])
    if result["changed"] is not False:
        _guard_mark(font, target, "trycomponent", result,
                    no_mark=None if result["component_placed"] else "the component was not confirmed")
    return result


# --------------------------------------------------------------------------
# /debug/trycomponent stage=templayer (v0.181) - RESEARCH for placing a component into a glyph that is not empty (the user's choices of
# 2026-11-18: scope contours, components or both; the recipe build replaced the layer's contents, NE 1268; route order: a temporary
# layer in the target glyph first, then "set aside and put back", then a component shape made directly; a scratch glyph only last).
# Names only (2026-11-18, /debug/classdir): flLayer('title'); flGlyph.addLayer(flLayer[, bool back = false]),
# removeLayer(flLayer), layers "list(flLayer)"; flLayer.addShape "flShape addShape(flShape)". ONE step per request, go=yes, exactly
# one font open, one master, its own counter (_TRYCOMP_TL_MAX per listener run):
#   addlayer     on a target with exactly ONE layer (the active one), autoLayer off, holding 1 or more plain contour shapes and / or
#                components of cpp glyphs, and no layer named _TL_TEMP_NAME: ONE w.addLayer(flLayer(_TL_TEMP_NAME)). Records the
#                baseline (working layer's name, elements with ink boxes, contours, width, glyph count) for this listener run.
#   build        recipe=<one cpp glyph of plain contours>: on the temporary layer only (empty, autoLayer off), the proven sequence
#                recipe = R, autoLayer = True, buildAuto(), autoLayer = False, recipe = "", each read back; stops at the first failure.
#   move         ONE working_layer.addShape(<the temporary layer's only shape, a component of a cpp glyph>).
#   removelayer  ONE w.removeLayer(<the temporary layer>), found by its exact name (never by position).
#   activate     (v0.182; live TL 1272: addLayer made the new layer the active one) ONE working_layer.setActive(); working_active
#                needs the working layer active (isActive True, the temporary layer's False) and nothing else changed.
#   setlayer     (v0.184; live 1283a: the built component names the temporary layer; 1285a: the assignment corrects it) ONE
#                shapeData.componentLayer = <working layer name> on the temporary layer's only component; temp_layer_set.
#   droptemp     (v0.184; clean-up of 1272) needs no baseline: a glyph of exactly two layers, gb_temp_component EMPTY: ONE
#                working_layer.setActive() if the temporary layer is active, then ONE w.removeLayer; temp_dropped. Not marked.
# v0.185 (the user's choice of 2026-11-18: Power Brush targets researched before the tool is built), for every step:
#   brush=yes    the working layer may also hold Power Brush or other composite shapes that are not components. No inkBox() is
#                called on such a shape (untested, F1): its row says "not_read" and it is compared by kind and matrix, the layer's
#                contours in full (layer.getContours(), the modern read proven on Power Brush glyphs, V120).
#   sync=light   the glyph is registered as "trycomponent_light", a light kind: the sync check after the step, and the guard before a
#                later font.update(), read only glyph.width and the modern layer, never glyph.layer / glyph.layers (they arm F1).
#   sync=full    (the default) as before: the full check, which reads the legacy layers.
# Every reply reads back the glyph's layer names and the active one, both layers' elements (kind, source, matrix, ink box), contours,
# autoLayer / recipe and width, the glyph's width, the source and the glyph count. The working layer is found by the name recorded at
# addlayer, never by being active. Only removelayer can mark the font, and only when the temporary layer is gone and the working layer
# holds exactly the baseline plus ONE new component (placed_beside); every other change is synced unmarked.
# Never called: save, font.update(), killAuto, setGlyphComponents, decomposite; no subscript or iteration of a native object (w.layers,
# layer.shapes and layer.getContours() are checked to be real lists first).
# --------------------------------------------------------------------------

_TL_TEMP_NAME = "gb_temp_component"
_TRYCOMP_TL_MAX = 20     # v0.185: 10 before; two full routes (6 steps each) in one listener run, with no restart between them
_TL_BOX_NOT_READ = {"not_read": ("a Power Brush or other composite shape: inkBox() is untested on it (F1), so it is compared by kind and "
                                 "matrix, and the layer's contours in full")}
_TRYCOMP_TL = {"calls": 0}
_TRYCOMP_TL_BASE = {}     # target -> the baseline recorded by step=addlayer in this listener run
_TRYCOMP_TL_STEPS = {"addlayer": f"w.addLayer(flLayer({_TL_TEMP_NAME!r})) once, on a target with one layer",
                     "activate": "working_layer.setActive() once (v0.182: addLayer made the new layer active, TL 1272)",
                     "build": ("the recipe build on the temporary layer only: recipe = R, autoLayer = True, buildAuto(), autoLayer = False, "
                               "recipe = \"\", each read back"),
                     "move": "working_layer.addShape(<the temporary layer's only component>) once",
                     "removelayer": f"w.removeLayer(<the layer named {_TL_TEMP_NAME!r}>) once",
                     "setlayer": "shapeData.componentLayer = <the working layer's name> once, on the temporary layer's only component (v0.184)",
                     "droptemp": (f"clean-up of an EMPTY {_TL_TEMP_NAME!r} left behind: working_layer.setActive() if the temporary layer is "
                                  "active, then w.removeLayer(<it>), each once (v0.184)")}


def _tl_layers(w):
    """[{"name", "layer"}] of w.layers (a real list), or {"error"}. Read only. Never raises."""
    layers, err = _tl_call(lambda: w.layers)
    if err is not None or type(layers) is not list:
        return {"error": f"w.layers is not a plain list ({err or type(layers).__name__})"}
    out = []
    for i, lay in enumerate(layers):
        nm, err = _tl_call(lambda l=lay: _call0(l, "name"))
        out.append({"name": nm if (err is None and isinstance(nm, str)) else f"<error: {err or type(nm).__name__}>", "layer": lay})
    return out


def _tl_contours(layer):
    """The contours of ONE layer object in the _tryedit_snapshot form ([{"closed", "nodes": [{x, y, kind, smooth}]}]), or {"error"}.
    Only the calls of _read_modern_outline: layer.getContours() as a real list, contour.getNodeAt(i) after a range check."""
    contours, err = _tl_call(lambda: layer.getContours())
    if err is not None or type(contours) not in (list, tuple):
        return {"error": f"layer.getContours() is not a plain list ({err or type(contours).__name__})"}
    out = []
    for ci in range(len(contours)):
        c = contours[ci]
        closed, err1 = _tl_call(lambda: _call0(c, "closed"))
        count, err2 = _tl_call(lambda: _call0(c, "nodesCount"))
        if err1 is not None or err2 is not None or not isinstance(count, int) or isinstance(count, bool) or count < 0:
            return {"error": f"contour {ci} could not be read ({err1 or err2 or 'nodesCount is not a number'})"}
        nodes = []
        for ni in range(count):
            nd, err = _tl_call(lambda i=ni: c.getNodeAt(i))
            if err is not None or nd is None:
                return {"error": f"contour {ci} node {ni}: getNodeAt failed ({err or 'None'})"}
            rec = {}
            for label in ("x", "y", "isOn", "isCurve", "smooth"):
                v, err = _tl_call(lambda a=label: _call0(nd, a))
                if err is not None:
                    return {"error": f"contour {ci} node {ni}: {label} could not be read ({err})"}
                rec[label] = _rm_plain(v)
            if any(isinstance(rec[k], bool) or not isinstance(rec[k], (int, float)) for k in ("x", "y")):
                return {"error": f"contour {ci} node {ni}: x / y are not numbers"}
            nodes.append({"x": float(rec["x"]), "y": float(rec["y"]), "kind": "On" if rec["isOn"] else ("Curve" if rec["isCurve"] else "Off"),
                          "smooth": rec["smooth"]})
        out.append({"closed": _rm_plain(closed), "nodes": nodes})
    return out


def _tl_existing(layer, tel, brush=False):
    """_trycomp_existing, and v0.185 with brush=True: a shape that is not a component but reads is_composite True (a Power Brush or other
    composite shape) gets no inkBox() call; its "ink_box" is _TL_BOX_NOT_READ. Every other shape gets ONE inkBox(). Read only. Never raises."""
    if not brush:
        return _trycomp_existing(layer, tel)
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list:
        return {"error": f"layer.shapes is not a plain list ({err or type(shapes).__name__})"}
    if len(shapes) != len(tel):
        return {"error": f"{len(shapes)} shape(s) for {len(tel)} element(s)"}
    out = []
    for e, sh in zip(tel, shapes):
        if e.get("is_component") is False and e.get("is_composite") is True:
            box = dict(_TL_BOX_NOT_READ)
        else:
            rect, call_err = _tl_call(lambda s=sh: s.inkBox())
            box = {"error": call_err} if call_err is not None else _rect_plain(rect)
            if not isinstance(box, dict) or "error" in box:
                return {"error": f"the ink box of element {e.get('index')} could not be read ({(box or {}).get('error') if isinstance(box, dict) else box})"}
        comp = e.get("is_component") is True
        out.append({"index": e.get("index"), "is_component": e.get("is_component"),
                    "component_glyph": e.get("component_glyph") if comp else None,
                    "component_layer": e.get("component_layer") if comp else None, "matrix": e.get("matrix"), "ink_box": box})
    return out


def _tl_view(layer, brush=False):
    """{"elements": _tl_existing rows, "contours", "auto", "advance_width"} of ONE layer object; a part that cannot be read is
    {"error"}. Read only. Never raises."""
    tel = _trycomp_elements(layer)
    rows = tel if isinstance(tel, dict) else _tl_existing(layer, tel, brush)
    aw, err = _tl_call(lambda: _call0(layer, "advanceWidth"))
    return {"elements": rows, "contours": _tl_contours(layer), "auto": _trycomp_auto_state(layer),
            "advance_width": _num(aw) if (err is None and _num(aw) is not None) else f"<error: {err or type(aw).__name__}>"}


def _tl_ok(view):
    """True when every part of a _tl_view could be read."""
    return not isinstance(view.get("elements"), dict) and not isinstance(view.get("contours"), dict)


def _tl_plain_elements_problem(rows, allow_empty=False, brush=False):
    """None, or why the rows are not only plain contour shapes and components of cpp glyphs. Uses the is_composite of
    _trycomp_elements, kept in a side list by the caller. v0.185, brush=True: a shape reading is_component False and is_composite
    True (a Power Brush or other composite shape) is accepted too."""
    if not rows and not allow_empty:
        return "it holds no element"
    for r in rows:
        if r.get("is_component") is True:
            if not _trycomp_name_ok(r.get("component_glyph")):
                return f"element {r.get('index')} is a component of {r.get('component_glyph')!r}, not of a cpp glyph"
        elif brush and r.get("is_component") is False and r.get("is_composite") is True:
            continue
        elif r.get("is_component") is not False or r.get("is_composite") is not False:
            return (f"element {r.get('index')} is not a plain contour shape (is_component {r.get('is_component')!r}, is_composite "
                    f"{r.get('is_composite')!r}): a Power Brush or unreadable shape is never touched by this probe")
    return None


def _tl_compare(bl, view):
    """{"missing", "new", "contours_equal", "contours_held"} of a working-layer view against the baseline."""
    missing, new = _trycomp_match_existing(bl["elements"], view["elements"])
    return {"missing": [bl["elements"][i] for i in missing], "new": [view["elements"][j] for j in new],
            "contours_equal": view["contours"] == bl["contours"], "contours_held": _trycomp_holds(view["contours"], bl["contours"])}


def _trycomp_templayer_gate(target, step, recipe, go, brush=None, sync=None):
    """v0.181: the parameters, the go gate, the one-font gate and the counter of stage=templayer; then _trycomp_templayer.
    v0.185: brush=yes and sync=light|full (default full)."""
    import sys as _sys
    step = str(step or "").strip()
    if step not in _TRYCOMP_TL_STEPS:
        return {"error": "stage=templayer needs step=" + "|".join(_TRYCOMP_TL_STEPS)}
    brush_raw = str(brush if brush is not None else "").strip()
    if brush_raw not in ("", "yes"):
        return {"error": 'brush must be "yes" (the working layer may hold Power Brush shapes) or left out'}
    brush_on = brush_raw == "yes"
    sync_mode = str(sync if sync is not None else "").strip() or "full"
    if sync_mode not in ("light", "full"):
        return {"error": 'sync must be "light" (no legacy layer read, F1) or "full" (the default)'}
    has_recipe = recipe is not None and str(recipe).strip() != ""
    src = None
    if step == "build":
        src = str(recipe or "").strip()
        if not _trycomp_name_ok(src):
            return {"error": 'step=build needs recipe=<one glyph name starting with "cpp"> (4 to 40 characters from A-Z a-z 0-9 . _ -)'}
        if src == target:
            return {"error": "the recipe must not name the target"}
    elif has_recipe:
        return {"error": f"step={step} takes no recipe"}
    if go != "yes":
        what = (_TRYCOMP_TL_STEPS[step] + (f", recipe {src}" if src else "") + (", Power Brush shapes allowed" if brush_on else "")
                + f", sync check {sync_mode}")
        return {"error": f"stage=templayer&step={step}: {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, _pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": "templayer", "step": step, "error": why, "calls_so_far": _TRYCOMP_TL["calls"], "max_calls": _TRYCOMP_TL_MAX}
    if _TRYCOMP_TL["calls"] >= _TRYCOMP_TL_MAX:
        return {"stage": "templayer", "step": step, "calls_so_far": _TRYCOMP_TL["calls"], "max_calls": _TRYCOMP_TL_MAX,
                "error": f"stage=templayer already ran {_TRYCOMP_TL_MAX} times in this listener run; restart the listener to repeat it"}
    _TRYCOMP_TL["calls"] += 1     # counted BEFORE the glyph is read
    base = {"stage": "templayer", "step": step, "target": target, "call": _TRYCOMP_TL_STEPS[step], "temp_layer_name": _TL_TEMP_NAME,
            "calls_so_far": _TRYCOMP_TL["calls"], "max_calls": _TRYCOMP_TL_MAX, "note": _TRYCOMP_NOTE,
            "brush": brush_on, "sync": sync_mode}
    if src:
        base["recipe"] = src
    if step == "droptemp":     # v0.184: needs no baseline
        return _trycomp_timed(_trycomp_droptemp_run, target, base, brush_on, sync_mode)
    return _trycomp_timed(_trycomp_templayer_run, mod, target, step, src, base, brush_on, sync_mode)


def _tl_guard_how(sync_mode):
    """v0.185: the guard kind of a templayer step: light (glyph.width only, never the legacy layer) or the full check."""
    return "trycomponent_light" if sync_mode == "light" else "trycomponent"


def _trycomp_templayer_run(mod, target, step, src, base, brush=False, sync_mode="full"):
    """v0.181: ONE step of the temporary-layer route (see the section comment). Read back. Never raises. v0.185: brush, sync_mode."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return dict(base, error=f"this probe needs a font with one master ({problem}): nothing was touched")
    layers = _tl_layers(w)
    if isinstance(layers, dict):
        return dict(base, error=f"the glyph's layers could not be read ({layers['error']}): nothing was touched")
    base["layers_before"] = [e["name"] for e in layers]
    st, active = _tryshape_modern_state(w)
    active_name = st.get("layer_name")
    base["active_layer_before"] = active_name
    temps = [e for e in layers if e["name"] == _TL_TEMP_NAME]
    bl = _TRYCOMP_TL_BASE.get(target)
    if step == "addlayer":
        if len(layers) != 1 or active is None or layers[0]["name"] != active_name:
            return dict(base, error=(f"step=addlayer needs a glyph with exactly one layer, the active one (it has {len(layers)}: "
                                     f"{base['layers_before']}, active {active_name!r}): nothing was touched"))
        working = layers[0]
    else:
        if bl is None:
            return dict(base, error="no step=addlayer on this target in this listener run, so there is no baseline: nothing was touched")
        found = [e for e in layers if e["name"] == bl["working"]]
        if len(found) != 1 or len(temps) != 1 or len(layers) != 2:
            return dict(base, error=(f"the glyph must hold exactly the working layer {bl['working']!r} and one {_TL_TEMP_NAME!r} (it holds "
                                     f"{base['layers_before']}): nothing was touched"))
        working = found[0]
    wl = working["layer"]
    wtel = _trycomp_elements(wl)
    if isinstance(wtel, dict):
        return dict(base, error=f"the working layer's elements could not be read ({wtel['error']}): nothing was touched")
    why = _tl_plain_elements_problem(wtel, allow_empty=step != "addlayer", brush=brush)     # v0.185: before any inkBox() (F1)
    if why is not None:
        return dict(base, error=f"the working layer: {why}: nothing was touched")
    wview = _tl_view(wl, brush)
    base["working_before"] = wview
    if not _tl_ok(wview):
        return dict(base, error="the working layer could not be read in full: nothing was touched")
    if wview["auto"].get("auto_layer") is not False:
        return dict(base, error=f"the working layer's autoLayer reads {wview['auto'].get('auto_layer')!r}, not False: nothing was touched")
    tl, tview = None, None
    if step != "addlayer":
        tl = temps[0]["layer"]
        tview = _tl_view(tl, brush)
        base["temp_before"] = tview
        if not _tl_ok(tview):
            return dict(base, error="the temporary layer could not be read in full: nothing was touched")
        if step not in ("removelayer", "activate"):
            cmp0 = _tl_compare(bl, wview)
            if cmp0["missing"] or cmp0["new"] or not cmp0["contours_equal"]:
                return dict(base, error="the working layer is no longer as recorded at step=addlayer: nothing was touched", working_vs_baseline=cmp0)
    if step == "build":
        if tview["elements"] or tview["auto"].get("auto_layer") is not False or tview["auto"].get("recipe") != "":
            return dict(base, error=("step=build needs the temporary layer empty, autoLayer off and recipe \"\" (it reads "
                                     f"{len(tview['elements'])} element(s), {tview['auto']}): nothing was touched"))
    if step in ("move", "setlayer"):
        te = tview["elements"]
        if (len(te) != 1 or te[0].get("is_component") is not True or not _trycomp_name_ok(te[0].get("component_glyph"))
                or tview["auto"].get("auto_layer") is not False):
            return dict(base, error=(f"step={step} needs the temporary layer to hold exactly one component of a cpp glyph, autoLayer off: "
                                     "nothing was touched"))
        if step == "setlayer" and te[0].get("component_layer") == bl["working"]:     # v0.184
            return dict(base, error=(f"the temporary layer's component already names {bl['working']!r}: there is nothing to set, "
                                     "nothing was touched"))
    srcs = [src] if src else [r["component_glyph"] for r in (tview["elements"] if tview else []) if r.get("is_component") is True]
    src_before = {}
    for s in srcs:
        snap = _tryedit_snapshot(s)
        if "error" in snap:
            return dict(base, error=f"the source {s!r} could not be read ({snap.get('error')}): nothing was touched")
        src_before[s] = snap
    if step == "build":
        sctx, srefusal = _modern_edit_target(src)
        sstate, slayer = _tryshape_modern_state(sctx["w"]) if sctx is not None else ({}, None)
        stel = _trycomp_elements(slayer) if slayer is not None else {"error": "no layer"}
        if isinstance(stel, dict) or not stel or any(e.get("is_component") is not False or e.get("is_composite") is not False for e in stel):
            return dict(base, error=f"the source {src!r} must hold only plain contour shapes: nothing was touched")
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    if step == "addlayer":
        _TRYCOMP_TL_BASE[target] = {"working": working["name"], "elements": wview["elements"], "contours": wview["contours"]}
        bl = _TRYCOMP_TL_BASE[target]
    shape_moved = None
    substeps = []
    try:
        if step == "addlayer":
            cls = getattr(mod, "flLayer", None)
            if cls is None:
                return dict(base, error="the fontlab module has no flLayer class: nothing was touched")
            new_layer = cls(_TL_TEMP_NAME)
            w.addLayer(new_layer)
            base["call_returned"] = None
        elif step == "build":
            def _sub(label, fn, attr, want):
                fn()
                got = _trycomp_auto_state(tl).get(attr)
                substeps.append({"call": label, "read_back": got, "ok": got == want})
                return got == want
            if _sub(f"layer.recipe = {src!r}", lambda: setattr(tl, "recipe", src), "recipe", src) and \
                    _sub("layer.autoLayer = True", lambda: setattr(tl, "autoLayer", True), "auto_layer", True):
                ret = tl.buildAuto()
                ok = ret is True
                substeps.append({"call": "layer.buildAuto()", "returned": ret if (ret is None or isinstance(ret, (bool, int, float, str)))
                                 else f"<{type(ret).__name__}>", "ok": ok})
                if ok and _sub("layer.autoLayer = False", lambda: setattr(tl, "autoLayer", False), "auto_layer", False):
                    _sub('layer.recipe = ""', lambda: setattr(tl, "recipe", ""), "recipe", "")
        elif step == "move":
            shapes, err = _tl_call(lambda: tl.shapes)
            if err is not None or type(shapes) is not list or len(shapes) != 1:
                return dict(base, error=f"the temporary layer's shapes are no longer a plain list of one ({err or type(shapes).__name__}): nothing was touched")
            shape_moved = shapes[0]
            ret = wl.addShape(shape_moved)
            base["call_returned"] = ("None" if ret is None else "the same shape object" if ret is shape_moved else f"<{type(ret).__name__}>")
        elif step == "setlayer":     # v0.184: the source-layer fix of 1285a, before the move
            shapes, err = _tl_call(lambda: tl.shapes)
            if err is not None or type(shapes) is not list or len(shapes) != 1:
                return dict(base, error=f"the temporary layer's shapes are no longer a plain list of one ({err or type(shapes).__name__}): nothing was touched")
            sd, err = _tl_call(lambda: shapes[0].shapeData)
            named, err2 = (None, err or "shapeData is None") if (err is not None or sd is None) else _tl_call(lambda: _call0(sd, "componentGlyph"))
            if err2 is not None or named != tview["elements"][0].get("component_glyph"):
                return dict(base, error=f"the temporary layer's component could not be checked ({err2 or named!r}): nothing was touched")
            sd.componentLayer = bl["working"]
        elif step == "activate":     # v0.182
            ret = wl.setActive()
            base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
        elif step == "removelayer":
            ret = w.removeLayer(tl)
            base["call_returned"] = ret if (ret is None or isinstance(ret, (bool, int, float, str))) else f"<{type(ret).__name__}>"
    except Exception as exc:
        base["error"] = f"{step} failed: {type(exc).__name__}: {exc}"
    if substeps:
        base["substeps"] = substeps
    result = dict(base)
    result["display_refreshed"] = _repaint_viewport()
    layers2 = _tl_layers(w)
    result["layers_after"] = layers2 if isinstance(layers2, dict) else [e["name"] for e in layers2]
    st2, _a2 = _tryshape_modern_state(w)
    result["active_layer_after"] = st2.get("layer_name")
    result["active_layer_kept"] = st2.get("layer_name") == active_name
    w2 = [e for e in layers2 if e["name"] == bl["working"]] if not isinstance(layers2, dict) else []
    t2 = [e for e in layers2 if e["name"] == _TL_TEMP_NAME] if not isinstance(layers2, dict) else []
    wview2 = _tl_view(w2[0]["layer"], brush) if len(w2) == 1 else {"error": f"{len(w2)} layer(s) named {bl['working']!r}"}
    tview2 = _tl_view(t2[0]["layer"], brush) if len(t2) == 1 else None
    result["working_after"] = wview2
    result["temp_after"] = tview2 if tview2 is not None else f"{len(t2)} layer(s) named {_TL_TEMP_NAME!r}"
    width_after = _trycomp_width(w)
    result["advance_width_after"] = width_after
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    src_after = {s: _tryedit_snapshot(s) for s in srcs}
    result["source_changed"] = ("unknown" if any("error" in src_after[s] for s in srcs) else
                                any(src_after[s]["contours"] != src_before[s]["contours"] for s in srcs))
    readable = "error" not in wview2 and _tl_ok(wview2) and not isinstance(layers2, dict)
    cmp2 = _tl_compare(bl, wview2) if readable else None
    result["working_vs_baseline"] = cmp2 if cmp2 is not None else "unknown"
    working_kept = cmp2 is not None and not cmp2["missing"] and not cmp2["new"] and cmp2["contours_equal"]
    one_new = (cmp2 is not None and not cmp2["missing"] and cmp2["contours_held"] and len(cmp2["new"]) == 1
               and cmp2["new"][0].get("is_component") is True)
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"] or result["source_changed"] is not False
                                          or (step != "activate" and not result["active_layer_kept"]))
    result["width_changed"] = width_after != width_before
    if step == "setlayer":     # v0.184
        te0, te2 = tview["elements"][0], (tview2["elements"] if (tview2 is not None and _tl_ok(tview2)) else None)
        result["temp_component_layer_after"] = te2[0].get("component_layer") if (te2 and len(te2) == 1) else "unknown"
        result["temp_layer_set"] = bool("error" not in result and te2 is not None and len(te2) == 1
                                        and te2[0].get("component_layer") == bl["working"]
                                        and _trycomp_same_element(dict(te2[0], component_layer=None), dict(te0, component_layer=None))
                                        and working_kept and not result["side_effect_detected"] and not result["width_changed"])
        changed = True
    elif step == "activate":     # v0.182: the working layer active, nothing else changed (both layers compared with this step's own before)
        flags = {}
        for label, e in (("working", w2[0] if len(w2) == 1 else None), ("temp", t2[0] if len(t2) == 1 else None)):
            v, err = _tl_call(lambda l=(e or {}).get("layer"): _call0(l, "isActive")) if e is not None else (None, "no such layer")
            flags[label] = v if (err is None and type(v) is bool) else f"<error: {err or type(v).__name__}>"
        result["is_active"] = flags
        def _same(a, b):
            return (_tl_ok(a) and _tl_ok(b) and a["contours"] == b["contours"] and a["auto"] == b["auto"]
                    and not any(_trycomp_match_existing(a["elements"], b["elements"])))
        result["layers_unchanged"] = (not isinstance(layers2, dict) and [e["name"] for e in layers2] == base["layers_before"]
                                      and readable and tview2 is not None and _same(wview, wview2) and _same(tview, tview2))
        result["working_active"] = bool("error" not in result and result["active_layer_after"] == bl["working"]
                                        and flags["working"] is True and flags["temp"] is False and result["layers_unchanged"]
                                        and not result["side_effect_detected"] and not result["width_changed"])
        changed = True
    elif step == "addlayer":
        temp_ok = tview2 is not None and _tl_ok(tview2) and not tview2["elements"] and not tview2["contours"]
        result["layer_added"] = bool("error" not in result and len(t2) == 1 and len(layers2) == 2 and temp_ok and working_kept
                                     and not result["side_effect_detected"])
        changed = isinstance(layers2, dict) or len(layers2) != len(layers) or not working_kept
    elif step == "build":
        te2 = tview2["elements"] if (tview2 is not None and _tl_ok(tview2)) else None
        result["temp_component"] = te2
        result["built"] = bool("error" not in result and substeps and all(s.get("ok") for s in substeps) and len(substeps) == 5
                               and te2 is not None and len(te2) == 1 and te2[0].get("is_component") is True
                               and te2[0].get("component_glyph") == src and working_kept and not result["side_effect_detected"])
        changed = True
    elif step == "move":
        moved_row = tview["elements"][0]
        result["new_in_working"] = cmp2["new"] if cmp2 is not None else "unknown"
        result["same_as_temp_component"] = bool(one_new and _trycomp_same_element(dict(cmp2["new"][0], index=None), dict(moved_row, index=None)))
        result["temp_still_holds_it"] = ("unknown" if tview2 is None or not _tl_ok(tview2) else
                                         len(tview2["elements"]) == 1 and _trycomp_same_element(tview2["elements"][0], moved_row))
        result["moved"] = bool("error" not in result and result["same_as_temp_component"] and not result["side_effect_detected"])
        # v0.183: live 1283a / 1283b: the component built on the temporary layer names that layer as its source layer
        result["component_layer_matches"] = bool(one_new and cmp2["new"][0].get("component_layer") == bl["working"])
        changed = True
    else:
        result["temp_layer_gone"] = not isinstance(layers2, dict) and len(t2) == 0 and len(layers2) == 1
        result["layer_removed"] = bool("error" not in result and result["temp_layer_gone"] and not result["side_effect_detected"])
        before_new = _tl_compare(bl, wview)["new"]
        result["component_survived"] = ("not applicable (no new component before the call)" if len(before_new) != 1 else
                                        bool(one_new and _trycomp_same_element(dict(cmp2["new"][0], index=None), dict(before_new[0], index=None))))
        result["component_layer_matches"] = bool(one_new and cmp2["new"][0].get("component_layer") == bl["working"])     # v0.183
        result["placed_beside"] = bool(result["layer_removed"] and result["component_survived"] is True
                                       and result["component_layer_matches"])
        changed = True
    if changed:
        if step == "removelayer" and result["placed_beside"]:
            _guard_mark(font, target, _tl_guard_how(sync_mode), result)
            _TRYCOMP_TL_BASE.pop(target, None)
        else:
            _guard_mark(font, target, _tl_guard_how(sync_mode), result,
                        no_mark=("a research step: the font is marked only after step=removelayer leaves the baseline plus one "
                                 "new component" if step != "removelayer" else "the end state was not confirmed"))
    return result


def _trycomp_droptemp_run(target, base, brush=False, sync_mode="full"):
    """v0.184, stage=templayer&step=droptemp: remove an EMPTY gb_temp_component left behind (live 1272). Never raises. v0.185: brush, sync_mode."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return dict(base, error=f"this probe needs a font with one master ({problem}): nothing was touched")
    layers = _tl_layers(w)
    if isinstance(layers, dict):
        return dict(base, error=f"the glyph's layers could not be read ({layers['error']}): nothing was touched")
    base["layers_before"] = [e["name"] for e in layers]
    temps = [e for e in layers if e["name"] == _TL_TEMP_NAME]
    others = [e for e in layers if e["name"] != _TL_TEMP_NAME]
    if len(layers) != 2 or len(temps) != 1 or len(others) != 1:
        return dict(base, error=(f"step=droptemp needs a glyph of exactly two layers, one of them {_TL_TEMP_NAME!r} (it has "
                                 f"{base['layers_before']}): nothing was touched"))
    tl, wl, wname = temps[0]["layer"], others[0]["layer"], others[0]["name"]
    tview = _tl_view(tl, brush)
    base["temp_before"] = tview
    if not _tl_ok(tview) or tview["elements"] or tview["contours"]:
        return dict(base, error=f"the layer {_TL_TEMP_NAME!r} is not known to be empty: it is never removed then, nothing was touched")
    wtel = _trycomp_elements(wl)
    if isinstance(wtel, dict):
        return dict(base, error="the other layer could not be read in full: nothing was touched")
    why = _tl_plain_elements_problem(wtel, allow_empty=True, brush=brush)     # v0.185: before any inkBox() (F1)
    if why is not None:
        return dict(base, error=f"the other layer: {why}: nothing was touched")
    wview = _tl_view(wl, brush)
    base["working_before"] = wview
    if not _tl_ok(wview):
        return dict(base, error="the other layer could not be read in full: nothing was touched")
    st, _a = _tryshape_modern_state(w)
    active_name = st.get("layer_name")
    base["active_layer_before"] = active_name
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    calls = []
    try:
        go_on = True
        if active_name == _TL_TEMP_NAME:
            ret = wl.setActive()
            st1, _a1 = _tryshape_modern_state(w)
            go_on = st1.get("layer_name") == wname
            calls.append({"call": "working_layer.setActive()", "returned": ret if (ret is None or isinstance(ret, (bool, int, float, str)))
                          else f"<{type(ret).__name__}>", "active_after": st1.get("layer_name"), "ok": go_on})
        if go_on:
            ret = w.removeLayer(tl)
            calls.append({"call": f"w.removeLayer(<{_TL_TEMP_NAME}>)", "returned": ret if (ret is None or isinstance(ret, (bool, int, float, str)))
                          else f"<{type(ret).__name__}>"})
    except Exception as exc:
        base["error"] = f"droptemp failed: {type(exc).__name__}: {exc}"
    base["calls"] = calls
    result = dict(base)
    result["display_refreshed"] = _repaint_viewport()
    layers2 = _tl_layers(w)
    result["layers_after"] = layers2 if isinstance(layers2, dict) else [e["name"] for e in layers2]
    st2, _a2 = _tryshape_modern_state(w)
    result["active_layer_after"] = st2.get("layer_name")
    w2 = [e for e in layers2 if e["name"] == wname] if not isinstance(layers2, dict) else []
    wview2 = _tl_view(w2[0]["layer"], brush) if len(w2) == 1 else {"error": f"{len(w2)} layer(s) named {wname!r}"}
    result["working_after"] = wview2
    result["advance_width_after"] = _trycomp_width(w)
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    kept = ("error" not in wview2 and _tl_ok(wview2) and wview2["contours"] == wview["contours"]
            and not any(_trycomp_match_existing(wview["elements"], wview2["elements"])))
    result["working_kept"] = bool(kept)
    result["temp_dropped"] = bool("error" not in result and result["layers_after"] == [wname] and result["active_layer_after"] == wname
                                  and kept and result["advance_width_after"] == width_before
                                  and result["glyph_count_after"] == result["glyph_count_before"])
    if calls:
        _guard_mark(font, target, _tl_guard_how(sync_mode), result, no_mark="a clean-up step of the research probe")
    return result


# --------------------------------------------------------------------------
# /debug/trycomponent stage=fixlayer (v0.183) - RESEARCH: can a component's source-layer name be set? Live 1283a / 1283b: a component
# built on the temporary layer names that layer ("gb_temp_component") as its source layer, which its source glyph does not have; FontLab
# draws it all the same (1284). Names only: flShapeData.componentLayer, documented as "string" (no setter listed).
# stage=fixlayer&target=cpp...&element=I, go=yes, exactly one font open, one master, its own counter (_TRYCOMP_FL_MAX per listener
# run), on a target with exactly ONE layer (the active one), autoLayer off, holding only plain contour shapes and components of cpp
# glyphs, whose element I is a component of a cpp glyph naming a source layer OTHER than the target's layer name: ONE
# shape.shapeData.componentLayer = <the target's layer name>. Read back: every element (kind, source, source layer, matrix, ink box),
# the outline, the width, the source glyph and the glyph count. layer_set: element I names the target's layer, and nothing else
# changed (its source, matrix and ink box, every other element, the outline, width, source, glyph count). Marked only then.
# --------------------------------------------------------------------------

_TRYCOMP_FL_MAX = 6
_TRYCOMP_FL = {"calls": 0}


def _trycomp_fixlayer_gate(target, element, go):
    """v0.183: the parameters, the go gate, the one-font gate and the counter of stage=fixlayer; then _trycomp_fixlayer_run."""
    import sys as _sys
    if element is None or not str(element).strip():
        return {"error": "stage=fixlayer needs element=I, the position of the component in the target (0 = the first)"}
    elem, err = _tryedit_int(element, "element", 0, _TRYCOMP_SEVERAL_MAX - 1)
    if err is not None:
        return {"error": err}
    if go != "yes":
        return {"error": (f"stage=fixlayer sets shapeData.componentLayer of component {elem} of the target to the target's own layer "
                          "name, once. Add &go=yes to run it.")}
    mod = _sys.modules.get("fontlab") or fl
    ws, _pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": "fixlayer", "error": why, "calls_so_far": _TRYCOMP_FL["calls"], "max_calls": _TRYCOMP_FL_MAX}
    if _TRYCOMP_FL["calls"] >= _TRYCOMP_FL_MAX:
        return {"stage": "fixlayer", "calls_so_far": _TRYCOMP_FL["calls"], "max_calls": _TRYCOMP_FL_MAX,
                "error": f"stage=fixlayer already ran {_TRYCOMP_FL_MAX} times in this listener run; restart the listener to repeat it"}
    _TRYCOMP_FL["calls"] += 1     # counted BEFORE the glyph is read
    base = {"stage": "fixlayer", "target": target, "element": elem, "call": "shape.shapeData.componentLayer = <the target's layer name>",
            "calls_so_far": _TRYCOMP_FL["calls"], "max_calls": _TRYCOMP_FL_MAX, "note": _TRYCOMP_NOTE}
    return _trycomp_timed(_trycomp_fixlayer_run, target, elem, base)


def _trycomp_fixlayer_run(target, elem, base):
    """v0.183: ONE shapeData.componentLayer assignment (see the section comment). Read back. Never raises."""
    ctx, refusal = _modern_edit_target(target)
    if ctx is None:
        return dict(base, error="the target cannot be used: " + str(refusal.get("reason") or refusal), refusal=_public_refusal(refusal))
    w, font = ctx["w"], ctx["font"]
    problem = _one_master_problem()
    if problem is not None:
        return dict(base, error=f"this probe needs a font with one master ({problem}): nothing was touched")
    layers = _tl_layers(w)
    if isinstance(layers, dict):
        return dict(base, error=f"the glyph's layers could not be read ({layers['error']}): nothing was touched")
    st, active = _tryshape_modern_state(w)
    name = st.get("layer_name")
    base["layers"] = [e["name"] for e in layers]
    if len(layers) != 1 or active is None or layers[0]["name"] != name:
        return dict(base, error=(f"stage=fixlayer needs a glyph with exactly one layer, the active one (it has {base['layers']}, active "
                                 f"{name!r}): nothing was touched"))
    wl = layers[0]["layer"]
    tel = _trycomp_elements(wl)
    if isinstance(tel, dict):
        return dict(base, error=f"the target's elements could not be read ({tel['error']}): nothing was touched")
    view = _tl_view(wl)
    base["target_before"] = view
    if not _tl_ok(view):
        return dict(base, error="the target could not be read in full: nothing was touched")
    rows = view["elements"]
    why = _tl_plain_elements_problem([dict(r, is_composite=e.get("is_composite")) for r, e in zip(rows, tel)])
    if why is not None:
        return dict(base, error=f"the target: {why}: nothing was touched")
    if view["auto"].get("auto_layer") is not False:
        return dict(base, error=f"the target's autoLayer reads {view['auto'].get('auto_layer')!r}, not False: nothing was touched")
    if elem >= len(rows):
        return dict(base, error=f"element {elem} does not exist: the target holds {len(rows)} elements: nothing was touched")
    row = rows[elem]
    if row.get("is_component") is not True:
        return dict(base, error=f"element {elem} is not a component: nothing was touched")
    base["component_layer_before"] = row.get("component_layer")
    if row.get("component_layer") == name:
        return dict(base, error=f"element {elem} already names the layer {name!r}: there is nothing to set, nothing was touched")
    src = row["component_glyph"]
    src_before = _tryedit_snapshot(src)
    if "error" in src_before:
        return dict(base, error=f"the source {src!r} could not be read ({src_before['error']}): nothing was touched")
    width_before = _trycomp_width(w)
    base["advance_width_before"] = width_before
    base["glyph_count_before"] = _tryedit_glyph_count(font)
    shapes, err = _tl_call(lambda: wl.shapes)
    if err is not None or type(shapes) is not list or len(shapes) != len(rows):
        return dict(base, error=f"the target's layer.shapes is no longer a plain list of {len(rows)}: nothing was touched")
    sd, err = _tl_call(lambda: shapes[elem].shapeData)
    named, err2 = (None, err or "shapeData is None") if (err is not None or sd is None) else _tl_call(lambda: _call0(sd, "componentGlyph"))
    if err2 is not None or named != src:
        return dict(base, error=(f"the shape at position {elem} names {named!r}, not {src!r} as read before: nothing was touched"
                                 if err2 is None else f"the shape at position {elem} could not be checked ({err2}): nothing was touched"))
    try:
        sd.componentLayer = name
    except Exception as exc:
        base["error"] = f"shapeData.componentLayer = {name!r} failed: {type(exc).__name__}: {exc}"
    result = dict(base)
    result["layer_name"] = name
    result["display_refreshed"] = _repaint_viewport()
    layers2 = _tl_layers(w)
    view2 = (_tl_view(layers2[0]["layer"]) if (not isinstance(layers2, dict) and len(layers2) == 1)
             else {"error": "the glyph no longer has exactly one layer"})
    result["target_after"] = view2
    result["advance_width_after"] = _trycomp_width(w)
    result["glyph_count_after"] = _tryedit_glyph_count(font)
    src_after = _tryedit_snapshot(src)
    result["source_changed"] = "unknown" if "error" in src_after else src_after["contours"] != src_before["contours"]
    ok = "error" not in view2 and _tl_ok(view2) and len(view2["elements"]) == len(rows)
    rows2 = view2["elements"] if ok else None
    result["component_layer_after"] = rows2[elem].get("component_layer") if ok else "unknown"
    result["component_kept"] = bool(ok and _trycomp_same_element(dict(rows2[elem], component_layer=None), dict(row, component_layer=None)))
    result["others_kept"] = bool(ok and all(_trycomp_same_element(rows2[i], rows[i]) for i in range(len(rows)) if i != elem))
    result["outline_kept"] = bool(ok and view2["contours"] == view["contours"])
    result["side_effect_detected"] = bool(result["glyph_count_after"] != result["glyph_count_before"] or result["source_changed"] is not False
                                          or result["advance_width_after"] != width_before or view2.get("auto") != view["auto"])
    result["layer_set"] = bool("error" not in result and result["component_layer_after"] == name and result["component_kept"]
                               and result["others_kept"] and result["outline_kept"] and not result["side_effect_detected"])
    changed = not ok or rows2 != rows or view2["contours"] != view["contours"]
    if changed:
        _guard_mark(font, target, "trycomponent", result, no_mark=None if result["layer_set"] else "the new source layer was not confirmed")
    return result


# --------------------------------------------------------------------------
# /debug/tryshape (v0.52) - EXPERIMENT: can the legacy glyph.getPen() put a shape into a glyph that has NO layer yet?
# --------------------------------------------------------------------------
# Background (live, v0.51): a glyph made by font.createGlyph() has NO layer at all (len(glyph.layers) == 0, bodyLayer and
# activeLayer None), exactly like an empty .notdef, so there is nothing to add a shape to. The legacy fgGlyph exposes
# getPen(); the standard pen protocol (moveTo / lineTo / closePath) is the simplest write route and needs no guessing of
# method signatures. This probe WRITES, so it is gated (go=yes), works on ONE route and ONE stage per request, and refuses
# every glyph that is not positively known to be empty (reference glyphs can never be touched).
_TRYSHAPE_TRIANGLE = ((0.0, 0.0), (500.0, 0.0), (250.0, 500.0))


def _tryshape_state(glyph):
    """Read-only snapshot of a legacy glyph's outline data. Every read is guarded; a failure is reported, never
    turned into a number."""
    st = {}
    try:
        st["layers"] = len(glyph.layers)
    except Exception as exc:
        st["layers_error"] = f"{type(exc).__name__}: {exc}"
    try:
        st["components"] = len(glyph.components)
    except Exception as exc:
        st["components_error"] = f"{type(exc).__name__}: {exc}"
    try:
        _ = glyph.layer                    # warm-up, as everywhere else (section 10)
    except Exception:
        pass
    try:
        bl = glyph.bodyLayer
    except Exception as exc:
        st["body_layer"] = f"error: {type(exc).__name__}: {exc}"
        return st
    if bl is None:
        st["body_layer"] = "None"
        return st
    st["body_layer"] = "present"
    for label, fn in (("contours", lambda: bl.countContours()), ("nodes", lambda: bl.countNodes()),
                      ("shapes", lambda: bl.countShapes())):
        try:
            st[label] = fn()
        except Exception as exc:
            st[label + "_error"] = f"{type(exc).__name__}: {exc}"
    return st


def _tryshape_known_empty(st):
    """True only on POSITIVE evidence that the glyph holds nothing: no layers at all, or one readable layer with 0
    contours, nodes and shapes - and a readable component count of 0."""
    if st.get("components") != 0:
        return False
    if st.get("layers") == 0:
        return True
    return (st.get("body_layer") == "present" and st.get("contours") == 0
            and st.get("nodes") == 0 and st.get("shapes") == 0)


_TRYSHAPE_STAGES = {"pen": ("dir", "draw"), "modern": ("names", "build", "attach", "refresh")}


def _tryshape_read(obj, attrs):
    """Zero-argument reads of named attributes of a detached object; a failure is reported, never turned into a value."""
    out = {}
    for a in attrs:
        try:
            v = _call0(obj, a)
            out[a] = v if (v is None or isinstance(v, (bool, int, float, str))) else f"<{type(v).__name__}>"
        except Exception as exc:
            out[a + "_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _tryshape_modern_state(w):
    """(state dict, layer or None) of the MODERN active layer - the layer FontLab's editor draws."""
    st = {}
    try:
        layer = w.activeLayer
    except Exception as exc:
        st["active_layer"] = f"error: {type(exc).__name__}: {exc}"
        return st, None
    if layer is None:
        st["active_layer"] = "None"
        return st, None
    st["active_layer"] = "present"
    try:
        st["layer_name"] = str(_call0(layer, "name"))
    except Exception as exc:
        st["layer_name_error"] = f"{type(exc).__name__}: {exc}"
    # v0.177: FontLab's componentsCount() is kept as "fontlab_components_count", information and a guard only: it read 0 on every
    # glyph holding components (RM 1241-1246). "components" counts the shapes flagged isComponent (_layer_component_shapes); a layer
    # whose shapesCount() reads 0 holds no shape, so none is a component, and layer.shapes is not read.
    for label, attr in (("shapes", "shapesCount"), ("nodes", "nodesCount"), ("fontlab_components_count", "componentsCount")):
        try:
            v = _call0(layer, attr)
            st[label] = int(v) if (isinstance(v, (int, float)) and not isinstance(v, bool)) else f"not a plain number: {type(v).__name__}"
        except Exception as exc:
            st[label + "_error"] = f"{type(exc).__name__}: {exc}"
    st["components"] = 0 if st.get("shapes") == 0 else _layer_component_shapes(layer)
    return st, layer


def _layer_component_shapes(layer):
    """v0.177: how many of the layer's shapes are components, from layer.shapes (a real list) and each shape's isComponent, the
    check proven live (606, 610, 1016-1022, 1209-1213). A whole number, or a "not readable: ..." text (never a guess): every
    guard then refuses. Read only. Never raises."""
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None or type(shapes) is not list:
        return f"not readable: layer.shapes ({err or type(shapes).__name__})"
    n = 0
    for i, sh in enumerate(shapes):
        v, err = _tl_call(lambda s=sh: _call0(s, "isComponent"))
        if err is not None or type(v) is not bool:
            return f"not readable: isComponent of shape {i} ({err or type(v).__name__})"
        n += 1 if v else 0
    return n


def _state_has_components(st):
    """v0.177: True unless BOTH counts of a modern state read a plain 0: the shapes flagged isComponent ("components") and
    FontLab's componentsCount() ("fontlab_components_count"). A missing or unreadable count counts as components."""
    return st.get("components") != 0 or st.get("fontlab_components_count") != 0


def _state_components_text(st):
    """v0.177: both counts of a modern state, for a refusal."""
    return (f"{st.get('components')!r} component shape(s) (FontLab's componentsCount() reads "
            f"{st.get('fontlab_components_count', st.get('fontlab_components_count_error'))!r})")


def _tryshape_modern_known_empty(st):
    return (st.get("active_layer") == "present" and st.get("shapes") == 0 and st.get("nodes") == 0
            and not _state_has_components(st))


def _tryshape_enum_names():
    """Read-only (stage=names): member NAMES of the enums the point-based flContour constructor needs, and whether
    QtCore.QPointF exists. Only dir() is read; nothing is constructed or called."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    out = {"QtCore.QPointF": "available" if getattr(QtCore, "QPointF", None) is not None else "missing"}
    for label, owner, attr in (("flNode.NodeType", "flNode", "NodeType"), ("flNode.NodeKind", "flNode", "NodeKind"),
                               ("flContour.FigureType", "flContour", "FigureType")):
        try:
            o = getattr(getattr(mod, owner), attr)
            if type(o) is dict:          # live (v0.54): these "enums" are real Python dicts; a real dict is safe to read
                items = {}
                for k, v in list(o.items())[:60]:
                    items[str(k)] = v if (v is None or isinstance(v, (bool, int, float, str))) else f"<{type(v).__name__}>"
                out[label] = {"type": "dict", "length": len(o), "items": items}
            else:
                out[label] = {"type": type(o).__name__, "names": sorted(n for n in dir(o) if not n.startswith("_"))[:120]}
        except Exception as exc:
            out[label] = {"error": f"{type(exc).__name__}: {exc}"}
    try:
        out["flNode_direct_value_names"] = [n for n in dir(mod.flNode)
                                            if n in ("On", "Off", "Curve", "Line", "Move", "Corner", "Smooth", "Quad")]
    except Exception as exc:
        out["flNode_direct_value_names"] = f"error: {type(exc).__name__}: {exc}"
    return out


def _tryshape_ctor_probe():
    """Read-only (variant=probe, stage=build): try every plausible flContour constructor form on DETACHED objects and report
    each result (v0.55 live: flContour(points, On, True) answers "AttributeError: Incorrect # of args"; flContour(nodes, True)
    answers "QPointF expected"). Nothing here touches a glyph. Each form is independent: a failure is recorded, never fatal."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    fc = getattr(mod, "flContour", None)
    fnode = getattr(mod, "flNode", None)
    if qp is None or fc is None or fnode is None:
        return [{"error": "need QtCore.QPointF, fontlab.flContour and fontlab.flNode: "
                          f"QPointF {'ok' if qp is not None else 'missing'}, flContour {'ok' if fc is not None else 'missing'}, "
                          f"flNode {'ok' if fnode is not None else 'missing'}"}]
    def pts():
        return [qp(x, y) for x, y in _TRYSHAPE_TRIANGLE]
    on = None
    on_note = None
    try:
        enum = fnode.NodeType
        if type(enum) is dict:
            key = next((k for k in enum if str(k).lower() == "on"), None)
            if key is not None:
                on = enum[key]
        if on is None:
            on_note = "node type On not found in flNode.NodeType: the forms that need it are skipped"
    except Exception as exc:
        on_note = f"flNode.NodeType unreadable ({type(exc).__name__}: {exc}): the forms that need it are skipped"
    forms = [("flContour(points)", lambda: fc(pts())),
             ("flContour(points, True)", lambda: fc(pts(), True)),
             (f"flContour(points, On={on!r})", (lambda: fc(pts(), on)) if on is not None else None),
             (f"flContour(points, On={on!r}, True)", (lambda: fc(pts(), on, True)) if on is not None else None),
             ("flContour(points, 'on')", lambda: fc(pts(), "on")),
             ("flContour(points, 'on', True)", lambda: fc(pts(), "on", True)),
             ("flContour([flNode, ...])", lambda: fc([fnode(x, y) for x, y in _TRYSHAPE_TRIANGLE])),
             ("flContour()", lambda: fc())]
    out = []
    if on_note:
        out.append({"note": on_note})
    for label, fn in forms:
        if fn is None:
            out.append({"form": label, "skipped": True})
            continue
        try:
            c = fn()
            out.append({"form": label, "ok": True,
                        "read": _tryshape_read(c, ("nodesCount", "closed", "clockwise", "isComplete"))})
        except Exception as exc:
            out.append({"form": label, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    # v0.57: how can a contour be CLOSED? (every constructor form above answered closed=False.) Fresh detached contours only.
    close = []
    read_attrs = ("nodesCount", "closed", "clockwise", "isComplete")
    try:
        c = fc(pts())
        c.closed = True
        close.append({"step": "contour.closed = True", "ok": True, "read": _tryshape_read(c, read_attrs)})
    except Exception as exc:
        close.append({"step": "contour.closed = True", "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    try:
        close.append({"names_containing_clos": sorted(n for n in dir(fc(pts())) if "clos" in n.lower())})
    except Exception as exc:
        close.append({"names_containing_clos_error": f"{type(exc).__name__}: {exc}"})
    qr = getattr(QtCore, "QRectF", None)
    if qr is None:
        close.append({"step": "flContour(QRectF)", "skipped": True, "note": "QtCore has no QRectF"})
    else:
        try:
            c = fc(qr(0.0, 0.0, 500.0, 500.0))
            close.append({"step": "flContour(QRectF(0, 0, 500, 500))", "ok": True, "read": _tryshape_read(c, read_attrs)})
        except Exception as exc:
            close.append({"step": "flContour(QRectF(0, 0, 500, 500))", "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    out.append({"close_probe": close})
    # v0.58: live (v0.57) shape.addContour(contour) answers "IndexError: Unexpected SeqBase<T> length." - which call shape does
    # FontLab accept? Fresh DETACHED shapes and contours only; each form is independent.
    fs = getattr(mod, "flShape", None)
    sp = []
    if fs is None:
        sp.append({"error": "the fontlab module has no flShape"})
    else:
        def closed_c():
            c = fc(pts())
            c.closed = True
            return c
        def open_c():
            return fc(pts())
        def rect_c():
            return fc(qr(0.0, 0.0, 500.0, 500.0))
        def mk(fn):
            def run():
                s = fs()
                fn(s)
                return s
            return run
        forms = [("shape.addContour(closed contour)  [control]", mk(lambda s: s.addContour(closed_c()))),
                 ("shape.addContour(open contour)", mk(lambda s: s.addContour(open_c()))),
                 ("shape.addContours([closed contour])", mk(lambda s: s.addContours([closed_c()]))),
                 ("shape.addContours(closed contour)", mk(lambda s: s.addContours(closed_c()))),
                 ("flShape(closed contour)", lambda: fs(closed_c())),
                 ("flShape([closed contour])", lambda: fs([closed_c()]))]
        if qr is not None:
            forms += [("shape.addContour(QRectF contour)", mk(lambda s: s.addContour(rect_c()))),
                      ("shape.addContours([QRectF contour])", mk(lambda s: s.addContours([rect_c()])))]
        for label, fn in forms:
            try:
                s = fn()
                sp.append({"form": label, "ok": True, "read": _tryshape_read(s, ("contoursCount", "hasContours", "isEmpty"))})
            except Exception as exc:
                sp.append({"form": label, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    out.append({"shape_probe": sp})
    # v0.59: live (v0.58) EVERY shape.addContour / addContours form fails on a detached flShape() with "IndexError: Unexpected
    # SeqBase<T> length.", even with FontLab's own QRectF contour, so the detached shape itself looks uninitialised. flShapeData
    # (addContour, addContours, contours) and the documented constructor flShape(flShapeData) are the candidate route. Fresh
    # DETACHED objects only; each form is independent.
    dp = []
    fsd = getattr(mod, "flShapeData", None)
    if fs is None or fsd is None:
        dp.append({"error": f"need fontlab.flShape and fontlab.flShapeData: flShape {'ok' if fs is not None else 'missing'}, "
                            f"flShapeData {'ok' if fsd is not None else 'missing'}"})
    else:
        def len_of(obj, attr):
            try:
                return len(getattr(obj, attr))
            except Exception as exc:
                return f"error: {type(exc).__name__}: {exc}"
        shape_attrs = ("contoursCount", "hasContours", "isEmpty")
        for label, ctor in (("flShape()", fs), ("flShapeData()", fsd), ("flContour()", fc)):
            try:
                dp.append({"fresh": label, "read": _tryshape_read(ctor(), ("isNull", "isValid", "isPresent", "isEmpty"))})
            except Exception as exc:
                dp.append({"fresh": label, "error": f"{type(exc).__name__}: {exc}"})
        def f_data_add():
            sd = fsd()
            sd.addContour(closed_c())
            return {"data_contours_len": len_of(sd, "contours")}
        def f_data_adds():
            sd = fsd()
            sd.addContours([closed_c()])
            return {"data_contours_len": len_of(sd, "contours")}
        def f_shape_from_data():
            sd = fsd()
            sd.addContour(closed_c())
            s = fs(sd)
            return {"shape": _tryshape_read(s, shape_attrs), "data_contours_len": len_of(sd, "contours")}
        def f_shape_empty_data_then_add():
            s = fs(fsd())
            s.addContour(closed_c())
            return {"shape": _tryshape_read(s, shape_attrs)}
        def f_ensure_then_add():
            s = fs()
            s.ensurePaths()
            s.addContour(closed_c())
            return {"shape": _tryshape_read(s, shape_attrs)}
        def f_own_data():
            s = fs()
            sd = getattr(s, "shapeData")
            if callable(sd):
                sd = sd()
            info = {"shapeData_type": type(sd).__name__, "shapeData_is_none": sd is None}
            sd.addContour(closed_c())
            info["data_contours_len"] = len_of(sd, "contours")
            info["shape"] = _tryshape_read(s, shape_attrs)
            return info
        forms = [("flShapeData().addContour(closed contour)", f_data_add),
                 ("flShapeData().addContours([closed contour])", f_data_adds),
                 ("flShape(flShapeData with the contour)", f_shape_from_data),
                 ("flShape(flShapeData()).addContour(closed contour)", f_shape_empty_data_then_add),
                 ("flShape().ensurePaths(), then addContour(closed contour)", f_ensure_then_add),
                 ("flShape().shapeData.addContour(closed contour)", f_own_data)]
        if qr is not None:
            def f_data_rect():
                sd = fsd()
                sd.addContour(rect_c())
                return {"data_contours_len": len_of(sd, "contours")}
            forms.append(("flShapeData().addContour(QRectF contour)", f_data_rect))
        for label, fn in forms:
            try:
                dp.append({"form": label, "ok": True, "read": fn()})
            except Exception as exc:
                dp.append({"form": label, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    out.append({"data_probe": dp})
    return out


_TRYSHAPE_SQUARE = ((0.0, 0.0), (400.0, 0.0), (400.0, 400.0), (0.0, 400.0))
_CURVE_NODE_ATTRS = ("x", "y", "type", "isOn", "isOff", "isCurve", "smooth", "index")
_CURVE_PROBE_MAX_NODES = 50
_CURVE_PROBE_INDEX = 1


def _tryshape_contour_snapshot(contour):
    """Read-only snapshot of a DETACHED contour: nodesCount / closed / clockwise and, when nodesCount is a plain number in a
    sane range, every node through getNodeAt(i) (the index is range-checked against nodesCount first; nothing is subscripted).
    A failed read is reported per node and never turned into a value."""
    snap = _tryshape_read(contour, ("nodesCount", "closed", "clockwise"))
    n = snap.get("nodesCount")
    if not isinstance(n, int) or isinstance(n, bool):
        snap["nodes_note"] = "nodesCount is not a plain number: the nodes were not read"
        return snap
    if n < 0 or n > _CURVE_PROBE_MAX_NODES:
        snap["nodes_note"] = f"nodesCount {n} is outside 0..{_CURVE_PROBE_MAX_NODES}: the nodes were not read"
        return snap
    rows = []
    for i in range(n):
        row = {"asked": i}
        try:
            nd = contour.getNodeAt(i)
        except Exception as exc:
            row["error"] = f"getNodeAt raised {type(exc).__name__}: {exc}"
            rows.append(row)
            continue
        if nd is None:
            row["error"] = "getNodeAt returned None"
            rows.append(row)
            continue
        row.update(_tryshape_read(nd, _CURVE_NODE_ATTRS))
        rows.append(row)
    snap["nodes"] = rows
    snap["summary"] = [_curve_row_text(r) for r in rows]
    return snap


def _curve_row_text(row):
    if "error" in row:
        return f"{row.get('asked')}: {row['error']}"
    if row.get("isOn") is True:
        kind = "on"
    elif row.get("isOff") is True:
        kind = "off"
    elif row.get("isCurve") is True:
        kind = "handle"
    else:
        kind = "?"
    flags = "/".join(str(row.get(k)) for k in ("isOn", "isOff", "isCurve"))
    return f"{row.get('asked')}: ({row.get('x')}, {row.get('y')}) {kind} type={row.get('type')} flags(on/off/curve)={flags} smooth={row.get('smooth')}"


def _tryshape_curve_probe():
    """variant=curve, stage=build (read-only for the font: DETACHED objects only, nothing is attached). Build a closed square,
    read every node, call node.convertToCurve(False) ONCE on node index 1, read every node again. The reply answers: does the
    call work on a detached contour, what does it return, which segment changed, how many nodes were added and what they are."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    fc = getattr(mod, "flContour", None)
    out = {"square": [list(p) for p in _TRYSHAPE_SQUARE], "call": f"node(index {_CURVE_PROBE_INDEX}).convertToCurve(False)"}
    if qp is None or fc is None:
        out["error"] = (f"need QtCore.QPointF and fontlab.flContour: QPointF {'ok' if qp is not None else 'missing'}, "
                        f"flContour {'ok' if fc is not None else 'missing'}; nothing was called")
        return out
    try:
        contour = fc([qp(x, y) for x, y in _TRYSHAPE_SQUARE])
        contour.closed = True
    except Exception as exc:
        out["error"] = f"building the square failed: {type(exc).__name__}: {exc}; nothing else was called"
        return out
    before = _tryshape_contour_snapshot(contour)
    out["before"] = before
    n = before.get("nodesCount")
    if before.get("closed") is not True:
        out["error"] = f"the square does not read closed (closed = {before.get('closed')!r}); convertToCurve was NOT called"
        return out
    if not isinstance(n, int) or isinstance(n, bool) or n <= _CURVE_PROBE_INDEX:
        out["error"] = f"nodesCount is {n!r}, node {_CURVE_PROBE_INDEX} cannot be addressed; convertToCurve was NOT called"
        return out
    try:
        node = contour.getNodeAt(_CURVE_PROBE_INDEX)
    except Exception as exc:
        out["error"] = f"getNodeAt({_CURVE_PROBE_INDEX}) raised {type(exc).__name__}: {exc}; convertToCurve was NOT called"
        return out
    if node is None:
        out["error"] = f"getNodeAt({_CURVE_PROBE_INDEX}) returned None; convertToCurve was NOT called"
        return out
    try:
        rv = node.convertToCurve(False)
        out["returned"] = rv if (rv is None or isinstance(rv, (bool, int, float, str))) else f"<{type(rv).__name__}>"
    except Exception as exc:
        out["convert_error"] = f"{type(exc).__name__}: {exc}"
    after = _tryshape_contour_snapshot(contour)
    out["after"] = after
    n2 = after.get("nodesCount")
    if isinstance(n2, int) and not isinstance(n2, bool):
        out["nodes_added"] = n2 - n
    else:
        out["nodes_added"] = None
    return out


_CURVE2_TOL = 0.01


def _curve2_returned(rv):
    """A JSON-safe description of what a call returned (an flNode is described by its x, y, index and type)."""
    if rv is None or isinstance(rv, (bool, int, float, str)):
        return rv
    d = {"object": type(rv).__name__}
    d.update(_tryshape_read(rv, ("x", "y", "index", "type")))
    return d


def _curve2_check(snap, spec):
    """True when every (index, x, y, is_curve_handle) of spec matches the node read-back, False when one does not,
    None when the nodes could not be read."""
    rows = snap.get("nodes")
    if not isinstance(rows, list):
        return None
    for i, x, y, want_handle in spec:
        if i >= len(rows):
            return False
        r = rows[i]
        rx, ry = r.get("x"), r.get("y")
        if not (isinstance(rx, (int, float)) and isinstance(ry, (int, float))):
            return None
        if abs(rx - x) > _CURVE2_TOL or abs(ry - y) > _CURVE2_TOL:
            return False
        if bool(r.get("isCurve")) != bool(want_handle):
            return False
    return True


def _curve2_step(label, fn, contour, steps, spec=None):
    """Run ONE call, report what it returned or the exact error, then re-read the whole detached contour."""
    step = {"step": label}
    try:
        step["returned"] = _curve2_returned(fn())
    except Exception as exc:
        step["error"] = f"{type(exc).__name__}: {exc}"
    snap = _tryshape_contour_snapshot(contour)
    step["nodesCount"] = snap.get("nodesCount")
    step["closed"] = snap.get("closed")
    step["nodes"] = snap.get("summary") or snap.get("nodes_note")
    if spec is not None:
        step["as_expected"] = _curve2_check(snap, spec)
    steps.append(step)
    return step, snap


def _tryshape_curve2_probe():
    """variant=curve2, stage=build (DETACHED objects only; nothing is attached). Experiment A: convertToCurve, then place the two
    default handles with setPoint and moveBy. Experiment B: put two handle nodes into a plain square with contour.insert(index,
    flNode(x, y, "curve")). Each experiment has its own fresh square; a failing step is reported and does not stop the other one."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    fc = getattr(mod, "flContour", None)
    out = {"square": [list(p) for p in _TRYSHAPE_SQUARE]}
    if qp is None or fc is None:
        out["error"] = (f"need QtCore.QPointF and fontlab.flContour: QPointF {'ok' if qp is not None else 'missing'}, "
                        f"flContour {'ok' if fc is not None else 'missing'}; nothing was called")
        return out

    def new_square():
        c = fc([qp(x, y) for x, y in _TRYSHAPE_SQUARE])
        c.closed = True
        return c

    # ---- A: convertToCurve, then setPoint on the first handle and moveBy on the second ----
    a = {"plan": "convertToCurve(False) on node 1; setPoint(1, QPointF(100, 60)); getNodeAt(2).moveBy(-20, 60)",
         "expected_handles": [[100.0, 60.0], [248.0, 60.0]]}
    out["experiment_A"] = a
    steps = []
    a["steps"] = steps
    try:
        sq = new_square()
        before = _tryshape_contour_snapshot(sq)
        a["before"] = {"nodesCount": before.get("nodesCount"), "closed": before.get("closed"), "nodes": before.get("summary")}
        if before.get("closed") is not True or before.get("nodesCount") != 4:
            a["error"] = "the square does not read closed with 4 nodes; no call was made"
        else:
            def conv():
                return sq.getNodeAt(1).convertToCurve(False)
            st, snap = _curve2_step("getNodeAt(1).convertToCurve(False)", conv, sq, steps)
            if "error" in st or snap.get("nodesCount") != 6:
                a["note"] = "convertToCurve did not give 6 nodes; the placing steps were skipped"
            else:
                _curve2_step("setPoint(1, QPointF(100, 60))", lambda: sq.setPoint(1, qp(100.0, 60.0)), sq, steps,
                             [(1, 100.0, 60.0, True)])
                st3, snap3 = _curve2_step("getNodeAt(2).moveBy(-20, 60)", lambda: sq.getNodeAt(2).moveBy(-20.0, 60.0), sq, steps,
                                          [(2, 248.0, 60.0, True)])
                a["final_as_expected"] = _curve2_check(snap3, [(0, 0.0, 0.0, False), (1, 100.0, 60.0, True),
                                                               (2, 248.0, 60.0, True), (3, 400.0, 0.0, False)])
    except Exception as exc:
        a["error"] = f"{type(exc).__name__}: {exc}"

    # ---- B: insert two flNode(x, y, "curve") into a plain square ----
    b = {"plan": 'insert(1, flNode(132, 60, "curve")); insert(2, flNode(268, 60, "curve"))',
         "expected": "6 nodes: (0,0) on, (132,60) handle, (268,60) handle, (400,0) on, (400,400) on, (0,400) on"}
    out["experiment_B"] = b
    steps_b = []
    b["steps"] = steps_b
    fnode = getattr(mod, "flNode", None)
    if fnode is None:
        b["error"] = "the fontlab module has no flNode; nothing was called"
    else:
        try:
            sq2 = new_square()
            before = _tryshape_contour_snapshot(sq2)
            b["before"] = {"nodesCount": before.get("nodesCount"), "closed": before.get("closed"), "nodes": before.get("summary")}
            if before.get("closed") is not True or before.get("nodesCount") != 4:
                b["error"] = "the square does not read closed with 4 nodes; no call was made"
            else:
                st1, _s1 = _curve2_step('insert(1, flNode(132, 60, "curve"))',
                                        lambda: sq2.insert(1, fnode(132.0, 60.0, "curve")), sq2, steps_b, [(1, 132.0, 60.0, True)])
                if "error" in st1:
                    b["note"] = "the first insert failed; the second was skipped"
                else:
                    st2, snap2 = _curve2_step('insert(2, flNode(268, 60, "curve"))',
                                              lambda: sq2.insert(2, fnode(268.0, 60.0, "curve")), sq2, steps_b,
                                              [(2, 268.0, 60.0, True)])
                    ok = _curve2_check(snap2, [(0, 0.0, 0.0, False), (1, 132.0, 60.0, True), (2, 268.0, 60.0, True),
                                               (3, 400.0, 0.0, False), (4, 400.0, 400.0, False), (5, 0.0, 400.0, False)])
                    b["final_as_expected"] = ok if snap2.get("nodesCount") == 6 else False
        except Exception as exc:
            b["error"] = f"{type(exc).__name__}: {exc}"
    return out


_CURVE3_POINTS = ((0.0, 0.0), (300.0, 0.0), (400.0, 100.0), (400.0, 400.0), (0.0, 400.0))
_CURVE3_CONVERT_INDEX = 2
_CURVE3_HANDLES = ((2, 355.0, 0.0), (3, 400.0, 45.0))
_CURVE3_EXPECTED = ((0.0, 0.0, False), (300.0, 0.0, False), (355.0, 0.0, True), (400.0, 45.0, True),
                    (400.0, 100.0, False), (400.0, 400.0, False), (0.0, 400.0, False))
_CURVE3_NODES = 7


def _tryshape_curve3_contour(calls, cur, notes):
    """variant=curve3: build ONE closed contour with a rounded corner on DETACHED objects and require the read-back to show
    exactly _CURVE3_EXPECTED before the caller may attach anything. Raises RuntimeError (naming the call in cur[0]) otherwise."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    if qp is None:
        raise RuntimeError("QtCore has no QPointF")
    cur[0] = f"flContour([{len(_CURVE3_POINTS)} QPointF])"
    contour = mod.flContour([qp(x, y) for x, y in _CURVE3_POINTS])
    calls.append(cur[0])
    cur[0] = "contour.closed = True"
    contour.closed = True
    calls.append(cur[0])
    state = _tryshape_read(contour, ("closed", "nodesCount"))
    if state.get("closed") is not True or state.get("nodesCount") != len(_CURVE3_POINTS):
        raise RuntimeError(f"the detached contour reads {state} instead of closed with {len(_CURVE3_POINTS)} nodes; nothing was attached")
    cur[0] = f"getNodeAt({_CURVE3_CONVERT_INDEX}).convertToCurve(False)"
    node = contour.getNodeAt(_CURVE3_CONVERT_INDEX)
    if node is None:
        raise RuntimeError(f"getNodeAt({_CURVE3_CONVERT_INDEX}) returned None")
    rv = node.convertToCurve(False)
    calls.append(cur[0])
    if rv is not True:
        raise RuntimeError(f"convertToCurve returned {rv!r} instead of True; nothing was attached")
    for idx, x, y in _CURVE3_HANDLES:
        cur[0] = f"setPoint({idx}, QPointF({x}, {y}))"
        contour.setPoint(idx, qp(x, y))
        calls.append(cur[0])
    cur[0] = "reading the detached contour back"
    snap = _tryshape_contour_snapshot(contour)
    summary = snap.get("summary") or [snap.get("nodes_note")]
    notes.append("detached nodes before attach: " + " | ".join(str(t) for t in summary))
    ok = (snap.get("closed") is True and snap.get("nodesCount") == _CURVE3_NODES
          and _curve2_check(snap, [(i, x, y, h) for i, (x, y, h) in enumerate(_CURVE3_EXPECTED)]) is True)
    if not ok:
        raise RuntimeError("the detached contour does not read back as expected (7 nodes, closed, handles at "
                           "(355, 0) and (400, 45) flagged isCurve); nothing was attached")
    return contour


_CURVE4_FRACTION_POINTS = ((0.5, 0.5), (400.25, 0.5), (400.25, 400.75), (0.5, 400.75))
_CURVE4_TOL = 1e-6


def _tryshape_curve4_probe():
    """variant=curve4, stage=build (DETACHED objects only, the font is never touched). Does FontLab keep FRACTIONAL coordinates?
    (live v0.78: setPoint(2, QPointF(355.23, 0)) read back 355.0.) Each trial starts from a fresh closed square on which
    convertToCurve(False) was called on node 1 (6 nodes: handles at indices 1 and 2, corner (400, 400) at index 4), asks for a
    fractional coordinate by ONE route and reads the node back; a failing trial is reported and never stops the others."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    fc = getattr(mod, "flContour", None)
    out = {"purpose": "does FontLab keep FRACTIONAL coordinates? (live v0.78: setPoint(2, QPointF(355.23, 0)) read back 355.0)"}
    if qp is None or fc is None:
        out["error"] = (f"need QtCore.QPointF and fontlab.flContour: QPointF {'ok' if qp is not None else 'missing'}, "
                        f"flContour {'ok' if fc is not None else 'missing'}; nothing was called")
        return out

    def converted_square():
        c = fc([qp(x, y) for x, y in _TRYSHAPE_SQUARE])
        c.closed = True
        rv = c.getNodeAt(1).convertToCurve(False)
        n = _tryshape_read(c, ("nodesCount",)).get("nodesCount")
        if rv is not True or n != 6:
            raise RuntimeError(f"convertToCurve returned {rv!r} and the contour has {n!r} nodes instead of 6")
        return c

    def xy(c, i):
        r = _tryshape_read(c.getNodeAt(i), ("x", "y"))
        return [r.get("x"), r.get("y")]

    def kept(read, req):
        return all(isinstance(a, (int, float)) and not isinstance(a, bool) and abs(a - b) < _CURVE4_TOL for a, b in zip(read, req))

    def trial(label, idx, requested, call):
        """requested: [x, y] or a function of the node's coordinates before; call(contour, requested) performs the ONE route."""
        t = {"trial": label, "node_index": idx}
        try:
            c = converted_square()
            before = xy(c, idx)
        except Exception as exc:
            t["error"] = f"setup failed: {type(exc).__name__}: {exc}"
            return t
        t["before_xy"] = before
        req = requested(before) if callable(requested) else list(requested)
        t["requested_xy"] = req
        try:
            t["returned"] = _curve2_returned(call(c, req))
        except Exception as exc:
            t["call_error"] = f"{type(exc).__name__}: {exc}"
        try:
            after = xy(c, idx)
        except Exception as exc:
            t["read_error"] = f"{type(exc).__name__}: {exc}"
            return t
        t["read_xy"] = after
        t["changed"] = after != before
        t["kept_fraction"] = kept(after, req)
        return t

    def assign_xy(c, req):
        node = c.getNodeAt(1)
        node.x = req[0]
        node.y = req[1]

    def assign_position(c, req):
        c.getNodeAt(1).position = qp(req[0], req[1])

    def move_by(c, req):
        return c.getNodeAt(1).moveBy(0.25, 0.25)

    trials = [
        trial("setPoint(1, QPointF(100.37, 60.62)) on a handle", 1, [100.37, 60.62],
              lambda c, r: c.setPoint(1, qp(r[0], r[1]))),
        trial("handle.moveBy(0.25, 0.25)", 1, lambda b: [b[0] + 0.25, b[1] + 0.25], move_by),
        trial("handle.x = 100.37; handle.y = 60.62 (plain assignment)", 1, [100.37, 60.62], assign_xy),
        trial("handle.position = QPointF(100.37, 60.62)", 1, [100.37, 60.62], assign_position),
        trial("setPoint(4, QPointF(400.25, 399.75)) on an on-curve corner", 4, [400.25, 399.75],
              lambda c, r: c.setPoint(4, qp(r[0], r[1]))),
    ]
    t = {"trial": "flContour built directly from fractional QPointF points (no conversion)",
         "requested_points": [list(p) for p in _CURVE4_FRACTION_POINTS]}
    try:
        c = fc([qp(x, y) for x, y in _CURVE4_FRACTION_POINTS])
        c.closed = True
        n = _tryshape_read(c, ("nodesCount",)).get("nodesCount")
        t["nodesCount"] = n
        if n != len(_CURVE4_FRACTION_POINTS):
            raise RuntimeError(f"nodesCount is {n!r}")
        read = [xy(c, i) for i in range(n)]
        t["read_points"] = read
        t["kept_fraction"] = all(kept(r, list(p)) for r, p in zip(read, _CURVE4_FRACTION_POINTS))
    except Exception as exc:
        t["error"] = f"{type(exc).__name__}: {exc}"
    trials.append(t)
    out["trials"] = trials
    out["summary"] = {tr["trial"]: tr.get("kept_fraction", "no result: " + str(tr.get("error") or tr.get("call_error") or tr.get("read_error")))
                      for tr in trials}
    return out


def _curve5_collinear(rows, n, a, b):
    """Handle vectors a-n and b-n of the node at index n, from node read-back rows: cross product (0 = collinear) and whether
    the two handles lie on opposite sides of the node. A failed read is reported, never turned into a number."""
    try:
        px, py = rows[n]["x"], rows[n]["y"]
        ax, ay = rows[a]["x"] - px, rows[a]["y"] - py
        bx, by = rows[b]["x"] - px, rows[b]["y"] - py
        cross = ax * by - ay * bx
        dot = ax * bx + ay * by
        return {"cross": round(cross, 6), "collinear": abs(cross) < 1e-6, "opposite_sides": dot < 0}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def _tryshape_curve5_probe():
    """variant=curve5, stage=build (DETACHED objects only, the font is never touched). Five independent trials (see the v0.80
    header): the closing segment, convertToCurve(True), node.smooth = True, and whether a smooth node pairs its handles."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    qp = getattr(QtCore, "QPointF", None)
    fc = getattr(mod, "flContour", None)
    out = {"purpose": "what a real curve tool still needs: the closing segment, the smooth flag, handle pairing"}
    if qp is None or fc is None:
        out["error"] = (f"need QtCore.QPointF and fontlab.flContour: QPointF {'ok' if qp is not None else 'missing'}, "
                        f"flContour {'ok' if fc is not None else 'missing'}; nothing was called")
        return out

    def square():
        c = fc([qp(x, y) for x, y in _TRYSHAPE_SQUARE])
        c.closed = True
        return c

    def conv(c, idx, smooth):
        return c.getNodeAt(idx).convertToCurve(smooth)

    def two_curve_square():
        """Square with two curved segments (0 to 3 and 3 to 6): nodes 0 on, 1 and 2 handles, 3 on, 4 and 5 handles, 6 and 7 on."""
        c = square()
        r1 = conv(c, 1, False)
        r2 = conv(c, 4, False)
        n = _tryshape_read(c, ("nodesCount",)).get("nodesCount")
        if r1 is not True or r2 is not True or n != 8:
            raise RuntimeError(f"building the two-curve square failed: convertToCurve returned {r1!r} and {r2!r}, nodesCount {n!r} instead of 8")
        return c

    def rows(c):
        s = _tryshape_contour_snapshot(c)
        return s, (s.get("nodes") if isinstance(s.get("nodes"), list) else None)

    def smooth_flags(r):
        return [x.get("smooth") for x in r] if r else None

    def run(label, fn):
        t = {"trial": label}
        try:
            fn(t)
        except Exception as exc:
            t["error"] = f"{type(exc).__name__}: {exc}"
        return t

    def t1(t):
        c = square()
        b, _rb = rows(c)
        t["before"] = b.get("summary")
        try:
            t["returned"] = _curve2_returned(conv(c, 0, False))
        except Exception as exc:
            t["call_error"] = f"{type(exc).__name__}: {exc}"
        a, ra = rows(c)
        t["after"] = a.get("summary")
        t["nodesCount"] = a.get("nodesCount")
        t["closed"] = a.get("closed")
        t["handle_indices"] = [x.get("asked") for x in (ra or []) if x.get("isCurve") is True and x.get("isOn") is False]

    def t2a(t):
        c = square()
        try:
            t["returned"] = _curve2_returned(conv(c, 1, True))
        except Exception as exc:
            t["call_error"] = f"{type(exc).__name__}: {exc}"
        a, ra = rows(c)
        t["after"] = a.get("summary")
        t["smooth_flags"] = smooth_flags(ra)

    def set_smooth(c, t):
        try:
            c.getNodeAt(3).smooth = True
        except Exception as exc:
            t["smooth_set_error"] = f"{type(exc).__name__}: {exc}"

    def t2b(t):
        c = two_curve_square()
        b, rb = rows(c)
        t["smooth_before"] = smooth_flags(rb)
        set_smooth(c, t)
        a, ra = rows(c)
        t["smooth_after"] = smooth_flags(ra)
        t["after"] = a.get("summary")
        try:
            t["coords_changed"] = [(x.get("x"), x.get("y")) for x in (rb or [])] != [(x.get("x"), x.get("y")) for x in (ra or [])]
        except Exception as exc:
            t["coords_changed"] = f"unknown: {type(exc).__name__}: {exc}"

    def t3(t, with_smooth):
        c = two_curve_square()
        if with_smooth:
            set_smooth(c, t)
        b, rb = rows(c)
        t["before"] = b.get("summary")
        t["partner_before"] = [rb[4].get("x"), rb[4].get("y")] if rb else None
        try:
            node = c.getNodeAt(2)
            node.x = 250.0
            node.y = 40.0
        except Exception as exc:
            t["move_error"] = f"{type(exc).__name__}: {exc}"
        a, ra = rows(c)
        t["after"] = a.get("summary")
        t["moved_handle_after"] = [ra[2].get("x"), ra[2].get("y")] if ra else None
        t["partner_after"] = [ra[4].get("x"), ra[4].get("y")] if ra else None
        t["partner_moved"] = (t["partner_before"] != t["partner_after"]) if (ra and rb) else None
        t["handles_vs_node3"] = _curve5_collinear(ra, 3, 2, 4) if ra else None

    trials = [run("T1 closing segment: convertToCurve(False) on node 0 of a square", t1),
              run("T2a convertToCurve(True) on node 1 of a square", t2a),
              run("T2b node.smooth = True on node 3 of the two-curve square", t2b),
              run("T3a control: move handle 2 (x = 250, y = 40) WITHOUT smooth, read partner handle 4", lambda t: t3(t, False)),
              run("T3b move handle 2 (x = 250, y = 40) WITH node 3 smooth, read partner handle 4", lambda t: t3(t, True))]
    out["trials"] = trials
    out["summary"] = {
        "T1 handle indices after the closing conversion": trials[0].get("handle_indices", trials[0].get("error")),
        "T2a smooth flags after convertToCurve(True)": trials[1].get("smooth_flags", trials[1].get("error")),
        "T2b smooth flags after node.smooth = True": trials[2].get("smooth_after", trials[2].get("error")),
        "T3a partner moved without smooth": trials[3].get("partner_moved", trials[3].get("error")),
        "T3b partner moved with smooth": trials[4].get("partner_moved", trials[4].get("error")),
        "T3b handles collinear through node 3": (trials[4].get("handles_vs_node3") or {}).get("collinear", trials[4].get("error")),
    }
    return out


def _tryshape_build_objects(calls, cur, variant="single", notes=None, ontype="value"):
    """Build ONE detached triangle shape with the modern classes. variant=points (v0.54): 3 x QtCore.QPointF(x, y),
    flContour([points], <node type On>, True) - the documented point-based constructor, with On resolved at run time
    (flNode.NodeType.On, then flNode.On) and the choice reported in `notes` - then flShape() and shape.addContour.
    variant=nodes (v0.53, LIVE RESULT: FontLab answers "TypeError: Wrong argument type. QPointF expected"):
    3 x flNode(x, y), flContour([nodes], True). Nothing here touches a glyph. `cur[0]` always names the call in progress
    (so a failure names itself); `calls` lists the calls that succeeded."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    need = ("flContour", "flShape") if variant in ("single", "curve3") else ("flNode", "flContour", "flShape")
    missing = [n for n in need if getattr(mod, n, None) is None]
    if missing:
        raise RuntimeError("the fontlab module has no " + ", ".join(missing))
    if notes is None:
        notes = []
    if variant == "single":
        qp = getattr(QtCore, "QPointF", None)
        if qp is None:
            raise RuntimeError("QtCore has no QPointF")
        pts = []
        for x, y in _TRYSHAPE_TRIANGLE:
            cur[0] = f"QPointF({x}, {y})"
            pts.append(qp(x, y))
            calls.append(cur[0])
        cur[0] = "flContour([3 QPointF])"
        contour = mod.flContour(pts)
        calls.append(cur[0])
        cur[0] = "contour.closed = True"
        contour.closed = True
        calls.append(cur[0])
        state = _tryshape_read(contour, ("closed", "nodesCount"))
        notes.append(f"after closing, the detached contour reads {state}")
        if state.get("closed") is not True:
            raise RuntimeError(f"setting contour.closed = True did not close the contour (it reads {state.get('closed')!r}); "
                               "nothing was attached")
    elif variant == "curve3":
        contour = _tryshape_curve3_contour(calls, cur, notes)
    elif variant == "points":
        qp = getattr(QtCore, "QPointF", None)
        if qp is None:
            raise RuntimeError("QtCore has no QPointF")
        on = None
        tried = []
        try:
            enum = mod.flNode.NodeType
        except Exception as exc:
            enum = None
            tried.append(f"flNode.NodeType: {type(exc).__name__}: {exc}")
        if type(enum) is dict:           # live (v0.54): flNode.NodeType is a real dict, its keys are the enum names
            key = next((k for k in enum if str(k).lower() == "on"), None)
            if key is None:
                tried.append("flNode.NodeType is a dict without a key 'On'")
            else:
                on = key if ontype == "key" else enum[key]
                label = f"flNode.NodeType[{key!r}] (" + ("the key itself" if ontype == "key" else "its value " + repr(on)) + ")"
                notes.append("node type On resolved as " + label)
                calls.append("resolve node type On via " + label)
        if on is None:
            for label, getter in (("flNode.NodeType.On", lambda: mod.flNode.NodeType.On),
                                  ("flNode.On", lambda: mod.flNode.On)):
                try:
                    on = getter()
                    notes.append("node type On resolved as " + label)
                    calls.append("resolve node type On via " + label)
                    break
                except Exception as exc:
                    tried.append(f"{label}: {type(exc).__name__}: {exc}")
        if on is None:
            raise RuntimeError("could not resolve the node type On; tried: " + " | ".join(tried))
        pts = []
        for x, y in _TRYSHAPE_TRIANGLE:
            cur[0] = f"QPointF({x}, {y})"
            pts.append(qp(x, y))
            calls.append(cur[0])
        cur[0] = "flContour([3 QPointF], On, True)"
        contour = mod.flContour(pts, on, True)
        calls.append(cur[0])
    else:
        nodes = []
        for x, y in _TRYSHAPE_TRIANGLE:
            cur[0] = f"flNode({x}, {y})"
            nodes.append(mod.flNode(x, y))
            calls.append(cur[0])
        cur[0] = "flContour([3 nodes], True)"
        contour = mod.flContour(nodes, True)
        calls.append(cur[0])
    cur[0] = "flShape()"
    shape = mod.flShape()
    calls.append(cur[0])
    if variant in ("single", "curve3"):
        # v0.60, LIVE (v0.59 probe): shape.addContour(...) fails on a detached shape ("Unexpected SeqBase<T> length"), but
        # shape.shapeData.addContour(contour) works and the shape then reports the contour.
        cur[0] = "shape.shapeData"
        sd = shape.shapeData
        if callable(sd):
            sd = sd()
        calls.append(cur[0])
        cur[0] = "shapeData.addContour(contour)"
        sd.addContour(contour)
        calls.append(cur[0])
        cur[0] = "reading the detached shape back"
        st = _tryshape_read(shape, ("contoursCount", "hasContours", "isEmpty"))
        notes.append(f"after adding the contour, the detached shape reads {st}")
        if st.get("contoursCount") != 1 or st.get("hasContours") is not True:
            raise RuntimeError(f"the detached shape does not report the contour after shapeData.addContour (it reads {st}); "
                               "nothing was attached")
    else:
        cur[0] = "shape.addContour(contour)"
        shape.addContour(contour)
        calls.append(cur[0])
    return contour, shape


def _tryshape_modern(glyph, font, name, stage, what, variant="single", ontype="value"):
    """route=modern. stage=build: detached objects only (the font is not touched). stage=attach: the same objects, then
    layer.addShape(shape) on the glyph's MODERN active layer, only if that layer is positively empty. stage=refresh: one
    update() call (what=layer|glyph), no shape added. Every stage reports the modern layer before and after, and the
    calls that ran."""
    result = {"open": True, "found": True, "name": name, "route": "modern", "stage": stage}
    if stage == "names":
        result["names"] = _tryshape_enum_names()
        result["font_may_have_changed"] = False
        return result
    result["variant"] = variant
    if variant == "points":
        result["ontype"] = ontype
    if variant == "probe":
        if stage != "build":
            result["error"] = "variant=probe is read-only and exists for stage=build only; nothing was called"
            return result
        result["ctor_probe"] = _tryshape_ctor_probe()
        result["font_may_have_changed"] = False
        return result
    if variant == "curve":
        if stage != "build":
            result["error"] = "variant=curve is for stage=build only (detached objects, nothing attached); nothing was called"
            return result
        result["curve_probe"] = _tryshape_curve_probe()
        result["font_may_have_changed"] = False
        return result
    if variant == "curve5":
        if stage != "build":
            result["error"] = "variant=curve5 is for stage=build only (detached objects, nothing attached); nothing was called"
            return result
        result["curve5_probe"] = _tryshape_curve5_probe()
        result["font_may_have_changed"] = False
        return result
    if variant == "curve4":
        if stage != "build":
            result["error"] = "variant=curve4 is for stage=build only (detached objects, nothing attached); nothing was called"
            return result
        result["curve4_probe"] = _tryshape_curve4_probe()
        result["font_may_have_changed"] = False
        return result
    if variant == "curve2":
        if stage != "build":
            result["error"] = "variant=curve2 is for stage=build only (detached objects, nothing attached); nothing was called"
            return result
        result["curve2_probe"] = _tryshape_curve2_probe()
        result["font_may_have_changed"] = False
        return result
    calls = []
    cur = [None]
    notes = []
    result["calls"] = calls
    result["notes"] = notes
    try:
        w, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        result["modern_wrapper_error"] = f"{type(exc).__name__}: {exc}"
        result["error"] = "the modern glyph could not be built, so nothing was called"
        return result
    result["wrapper"] = how
    before, layer = _tryshape_modern_state(w)
    result["state_before"] = before
    if stage == "build" or stage == "attach":
        if stage == "attach" and not _tryshape_modern_known_empty(before):
            result["refused"] = True
            result["error"] = ("refused: the glyph's MODERN active layer is not KNOWN to be empty (needs: a layer, with 0 shapes, "
                               "0 nodes and 0 components, all readable). Nothing was called. A glyph that has never been opened "
                               "in the editor may have no modern layer yet.")
            return result
        try:
            contour, shape = _tryshape_build_objects(calls, cur, variant, notes, ontype)
        except Exception as exc:
            result["failed_at"] = cur[0] or "(before any call: building the objects)"
            result["error"] = f"{type(exc).__name__}: {exc}"
            return result
        result["built"] = {"contour": _tryshape_read(contour, ("nodesCount", "closed", "clockwise")),
                           "shape": _tryshape_read(shape, ("contoursCount", "isEmpty"))}
        if stage == "build":
            result["font_may_have_changed"] = False
            return result
        try:
            cur[0] = "layer.addShape(shape)"
            layer.addShape(shape)
            calls.append(cur[0])
        except Exception as exc:
            result["failed_at"] = cur[0]
            result["error"] = f"{type(exc).__name__}: {exc}"
    else:   # refresh
        if layer is None:
            result["error"] = "there is no modern active layer to refresh; nothing was called"
            return result
        try:
            if what == "glyph":
                cur[0] = "glyph.update()"
                w.update()
            else:
                cur[0] = "layer.update()"
                layer.update()
            calls.append(cur[0])
        except Exception as exc:
            result["failed_at"] = cur[0]
            result["error"] = f"{type(exc).__name__}: {exc}"
    after, _l2 = _tryshape_modern_state(w)
    result["state_after"] = after
    if stage == "attach":
        want_nodes = _CURVE3_NODES if variant == "curve3" else 3
        result["expected"] = {"shapes": 1, "nodes": want_nodes}
        result["counts_match_expected"] = (after.get("shapes") == 1 and after.get("nodes") == want_nodes)
    desc = {}
    try:
        _describe_modern_glyph(w, desc)
        result["modern_view_after"] = desc
    except Exception as exc:
        result["modern_view_after_error"] = f"{type(exc).__name__}: {exc}"
    try:
        result["legacy_state_after"] = _tryshape_state(glyph)
    except Exception as exc:
        result["legacy_state_after_error"] = f"{type(exc).__name__}: {exc}"
    result["font_may_have_changed"] = stage == "attach"
    return result


def debug_try_shape(name, go, route, stage=None, what="layer", variant="single", ontype="value"):
    """EXPERIMENT (WRITES when route=pen stage=draw, or route=modern stage=attach). route=pen (v0.52, legacy glyph.getPen()):
    DEAD END for real shapes - live result: the pen puts the triangle into a NEW stray layer named "Body" that FontLab's
    editor does not draw (the glyph looks blank) and the legacy reader still reports it. route=modern (v0.53): build the
    shape with flNode / flContour / flShape and attach it with layer.addShape on the glyph's MODERN active layer (see
    _tryshape_modern). Gated, refuses non-empty glyphs / layers, never saves.
    Original v0.52 text: route=pen only. stage=dir: call glyph.getPen() and report the pen's type and
    member names, without drawing; stage=draw: draw one closed triangle (0,0 / 500,0 / 250,500) with moveTo, lineTo,
    lineTo, closePath, then re-read the glyph. Both stages report the layer state before and after and list every call
    that ran, so the cause of any change is known. Never saves."""
    if go != "yes":
        return {"error": "refused: this probe can change the font (getPen / drawing). Repeat the request with &go=yes "
                         "(disposable test font only)."}
    if route not in ("pen", "modern"):
        return {"error": f"unknown route {route!r}: use route=pen or route=modern"}
    if not stage:
        stage = "dir" if route == "pen" else "build"
    if stage not in _TRYSHAPE_STAGES[route]:
        return {"error": f"unknown stage {stage!r} for route={route}: use " + " or ".join("stage=" + s for s in _TRYSHAPE_STAGES[route])}
    if what not in ("layer", "glyph"):
        return {"error": f"unknown what {what!r}: use what=layer or what=glyph"}
    if variant not in ("single", "points", "nodes", "probe", "curve", "curve2", "curve3", "curve4", "curve5"):
        return {"error": f"unknown variant {variant!r}: use variant=single, variant=points, variant=nodes, variant=probe, variant=curve, variant=curve2, variant=curve3, variant=curve4 or variant=curve5"}
    if ontype not in ("value", "key"):
        return {"error": f"unknown ontype {ontype!r}: use ontype=value or ontype=key"}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    if route == "modern":
        return _tryshape_modern(glyph, font, name, stage, what, variant, ontype)
    before = _tryshape_state(glyph)
    result = {"open": True, "found": True, "name": name, "route": route, "stage": stage, "state_before": before}
    if not _tryshape_known_empty(before):
        result["refused"] = True
        result["error"] = ("refused: this glyph is not KNOWN to be empty (needs: readable component count 0, and either "
                           "no layers or a readable layer with 0 contours, nodes and shapes). Nothing was called.")
        return result
    calls = []
    result["calls"] = calls
    try:
        calls.append("glyph.getPen()")
        pen = glyph.getPen()
    except Exception as exc:
        result["failed_at"] = "glyph.getPen()"
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["state_after"] = _tryshape_state(glyph)
        return result
    result["pen_is_none"] = pen is None
    result["pen_type"] = type(pen).__name__
    try:
        result["pen_names"] = sorted(n for n in dir(pen) if not n.startswith("_"))[:200]
    except Exception as exc:
        result["pen_names_error"] = f"{type(exc).__name__}: {exc}"
    if stage == "draw" and pen is not None:
        pts = _TRYSHAPE_TRIANGLE
        steps = (("moveTo", pts[0]), ("lineTo", pts[1]), ("lineTo", pts[2]), ("closePath", None))
        for meth, arg in steps:
            label = f"pen.{meth}({arg})" if arg is not None else f"pen.{meth}()"
            try:
                fn = getattr(pen, meth)
                if arg is None:
                    fn()
                else:
                    fn(arg)
                calls.append(label)
            except Exception as exc:
                result["failed_at"] = label
                result["error"] = f"{type(exc).__name__}: {exc}"
                break
        result["expected"] = {"contours": 1, "nodes": 3, "bbox": [0, 0, 500, 500]}
    after = _tryshape_state(glyph)
    result["state_after"] = after
    if stage == "draw":
        result["counts_match_expected"] = (after.get("contours") == 1 and after.get("nodes") == 3)
        try:
            result["outline_after"] = get_glyph_outline(name, "body", True)
        except Exception as exc:
            result["outline_after_error"] = f"{type(exc).__name__}: {exc}"
    result["font_may_have_changed"] = stage == "draw" or before.get("layers") != after.get("layers")
    return result



# /debug/trylayer (v0.70) - EXPERIMENT: can a glyph that was never opened in an editor tab get its modern layer through the API?
import re as _re_tl

_TRYLAYER_METHODS = ("findLayerCreate", "getLayerByName", "addLayer")


def _tl_call(fn):
    """(value, None) or (None, 'Type: message')."""
    try:
        return fn(), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _tl_describe(obj):
    """Short, safe description of a returned object: None, or its type and (if readable) its name."""
    if obj is None:
        return {"is_none": True}
    out = {"is_none": False, "type": type(obj).__name__}
    try:
        out["name"] = str(obj.name)
    except Exception as exc:
        out["name_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _tl_modern_state(w):
    """Read-only snapshot of the modern wrapper: every read guarded."""
    st = {}
    v, err = _tl_call(lambda: w.activeLayer)
    st["activeLayer"] = _tl_describe(v) if err is None else {"error": err}
    v, err = _tl_call(lambda: w.bodyLayer)
    st["bodyLayer"] = _tl_describe(v) if err is None else {"error": err}
    v, err = _tl_call(lambda: _call0(w, "hasBody"))
    st["hasBody"] = v if err is None else {"error": err}
    v, err = _tl_call(lambda: len(w.layers))
    st["layers_len"] = v if err is None else {"error": err}
    v, err = _tl_call(lambda: _num(w.advanceWidth))
    st["advanceWidth"] = v if err is None else {"error": err}
    return st


def _tl_font_master(font):
    """Read-only: what font.master is. Every read is guarded and reported as it came."""
    out = {}
    v, err = _tl_call(lambda: font.master)
    if err is not None:
        return {"error": err}
    out["is_none"] = v is None
    if v is None:
        return out
    out["type"] = type(v).__name__
    names, nerr = _tl_call(lambda: sorted(n for n in dir(v) if not n.startswith("_")))
    out["public_names"] = names if nerr is None else {"error": nerr}
    for attr in ("name", "id", "isMasterLayer", "isBodyLayer"):
        val, verr = _tl_call(lambda a=attr: _call0(v, a))
        if verr is not None:
            out[attr] = {"error": verr}
        elif val is None or isinstance(val, (bool, int, float, str)):
            out[attr] = val
        else:
            out[attr] = f"<{type(val).__name__}>"
    return out


def _rm_describe(value):
    """Type, and len() when it is a Python list / tuple; any other object by type name only (never indexed or iterated)."""
    out = {"type": type(value).__name__}
    if value is None:
        out["is_none"] = True
    elif type(value) in (list, tuple):
        out["python_sequence"] = True
        out["len"] = len(value)
    else:
        out["python_sequence"] = False
        try:
            out["len"] = len(value)
        except Exception as exc:
            out["len_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _rm_plain(value):
    return value if (value is None or isinstance(value, (bool, int, float, str))) else f"<{type(value).__name__}>"


def _rect_plain(rect):
    """{"left", "right", "top", "bottom", "width", "height"} of a QRectF through its zero-argument getters, or {"error"}."""
    if rect is None:
        return {"error": "returned None"}
    out = {"type": type(rect).__name__}
    for m in ("left", "right", "top", "bottom", "width", "height"):
        try:
            fn = getattr(rect, m)
            val = fn() if callable(fn) else fn
        except Exception as exc:
            return {"type": out["type"], "error": f"rect.{m} failed: {type(exc).__name__}: {exc}"}
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return {"type": out["type"], "error": f"rect.{m} was not a number ({type(val).__name__})"}
        out[m] = float(val)
    return out


def debug_read_modern(name, stage, index, node_index, via, go=""):
    """READ-ONLY. How can the outline be read back from the modern active layer? No native object is indexed or iterated: only
    getContours() results that are real Python lists / tuples are indexed. v0.120: stage=box (GATED, go=yes) calls
    layer.boundingBox() and layer.inkBox() once each, both never called live before (docstrings, test 484:
    "QRectF boundingBox()", "QRectF inkBox([QTransform tx = QTransform()])")."""
    if stage not in ("layer", "contour", "node", "box"):
        return {"error": 'stage must be "layer", "contour", "node" or "box"'}
    if stage == "box" and go != "yes":
        return {"error": "stage=box calls layer.boundingBox() and layer.inkBox() on the modern layer, never called live before. "
                         "Add &go=yes to run it."}
    if stage == "node" and via not in ("getNodeAt", "at"):
        return {"error": 'stage=node needs &via=getNodeAt or &via=at'}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    try:
        w, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"open": True, "found": True, "error": f"the modern glyph could not be reached: {exc}"}
    state, layer = _tryshape_modern_state(w)
    result = {"open": True, "found": True, "name": name, "stage": stage, "wrapper": how, "layer_state": state}
    if layer is None:
        result["error"] = "this glyph has no modern active layer, so there is nothing to read"
        return result
    if stage == "layer":
        for label, fn in (("getContours()", lambda: layer.getContours()), ("getShapes()", lambda: layer.getShapes()),
                          ("shapes", lambda: layer.shapes)):
            v, err = _tl_call(fn)
            result[label] = {"error": err} if err is not None else _rm_describe(v)
        v, err = _tl_call(lambda: _call0(layer, "shapesCount"))
        result["shapesCount"] = {"error": err} if err is not None else _rm_plain(v)
        return result
    if stage == "box":
        for label, fn in (("boundingBox()", lambda: layer.boundingBox()), ("inkBox()", lambda: layer.inkBox())):
            v, err = _tl_call(fn)
            result[label] = {"error": err} if err is not None else _rect_plain(v)
        return result
    contours, err = _tl_call(lambda: layer.getContours())
    if err is not None:
        result["error"] = f"getContours() failed: {err}"
        return result
    if type(contours) not in (list, tuple):
        result["error"] = (f"getContours() returned a {type(contours).__name__}, not a Python list or tuple: it is not indexed "
                           "(indexing native FontLab objects crashed FontLab before)")
        return result
    result["contours"] = len(contours)
    if not (0 <= index < len(contours)):
        result["error"] = f"index {index} is out of range: the layer has {len(contours)} contour(s)"
        return result
    contour = contours[index]
    for label in ("closed", "clockwise", "nodesCount"):
        v, err = _tl_call(lambda a=label: _call0(contour, a))
        result[label] = {"error": err} if err is not None else _rm_plain(v)
    v, err = _tl_call(lambda: contour.nodes)
    result["nodes"] = {"error": err} if err is not None else _rm_describe(v)
    if stage == "contour":
        return result
    count = result.get("nodesCount")
    if not isinstance(count, int) or isinstance(count, bool):
        result["error"] = "nodesCount could not be read, so no node is touched"
        return result
    if not (0 <= node_index < count):
        result["error"] = f"node {node_index} is out of range: the contour has {count} node(s)"
        return result
    result["via"] = via
    node, err = _tl_call(lambda: getattr(contour, via)(node_index))
    if err is not None:
        result["error"] = f"contour.{via}({node_index}) failed: {err}"
        return result
    if node is None:
        result["node"] = {"is_none": True}
        return result
    info = {"type": type(node).__name__}
    for label in ("x", "y", "isOn", "isOff", "isCurve", "smooth", "index"):
        v, err = _tl_call(lambda a=label: _call0(node, a))
        info[label] = {"error": err} if err is not None else _rm_plain(v)
    result["node"] = info
    return result


def debug_try_layer(name, stage, method, layer, ref, go):
    """EXPERIMENT. stage=state is read-only; stage=create WRITES (one creation call) and needs go=yes. Names are checked, the
    glyph must be positively empty and must have no modern layer. Never saves."""
    if stage not in ("state", "create"):
        return {"error": 'stage must be "state" or "create"'}
    if layer and not _re_tl.match(r"^[A-Za-z0-9 _.\-]{1,60}$", layer):
        return {"error": "layer must be 1-60 plain characters (letters, digits, space, _ . -)"}
    if ref and not _re_tl.match(r"^[A-Za-z0-9_.\-]{1,60}$", ref):
        return {"error": "ref must be a plain glyph name"}
    if stage == "create":
        if go != "yes":
            return {"error": "refused: stage=create can change the font. Repeat with &go=yes (disposable test font only)."}
        if method not in _TRYLAYER_METHODS:
            return {"error": "method must be one of " + ", ".join(_TRYLAYER_METHODS)}
        if not layer:
            return {"error": "stage=create needs &layer=NAME"}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        out = {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
        if stage == "state":
            out["font_master"] = _tl_font_master(font)
        return out
    result = {"open": True, "found": True, "name": name, "stage": stage}
    if stage == "state":
        result["font_master"] = _tl_font_master(font)
    legacy = _tryshape_state(glyph)
    result["legacy_state"] = legacy
    try:
        w, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        result["error"] = f"the modern glyph could not be reached: {exc}"
        return result
    result["wrapper"] = how
    before = _tl_modern_state(w)
    result["modern_before"] = before
    if stage == "state":
        names = []
        try:
            names = sorted(n for n in dir(font) if "master" in n.lower())
        except Exception as exc:
            names = [f"error: {exc}"]
        result["font_members_with_master"] = names
        if layer:
            v, err = _tl_call(lambda: w.findLayer(layer))
            result["findLayer"] = _tl_describe(v) if err is None else {"error": err}
            v, err = _tl_call(lambda: w.getLayerByName(layer, False))
            result["getLayerByName_no_create"] = _tl_describe(v) if err is None else {"error": err}
        if ref:
            rg = _find_glyph(font, ref)
            if rg is None:
                result["ref"] = {"found": False}
            else:
                try:
                    rw, rhow = _modern_wrapper(rg, font)
                    result["ref"] = {"found": True, "wrapper": rhow, "modern": _tl_modern_state(rw)}
                except Exception as exc:
                    result["ref"] = {"found": True, "error": str(exc)}
        return result
    # stage == create
    if not _tryshape_known_empty(legacy):
        result["refused"] = True
        result["error"] = "refused: this glyph is not KNOWN to be empty. Nothing was called."
        return result
    if before["activeLayer"].get("is_none") is not True:
        result["refused"] = True
        result["error"] = "refused: this glyph already has a modern layer (or it could not be read). Nothing was called."
        return result
    result["method"] = method
    result["layer_requested"] = layer
    if method == "findLayerCreate":
        label = f"w.findLayerCreate({layer!r})"
        ret, err = _tl_call(lambda: w.findLayerCreate(layer))
    elif method == "getLayerByName":
        label = f"w.getLayerByName({layer!r}, True)"
        ret, err = _tl_call(lambda: w.getLayerByName(layer, True))
    else:
        label = f"w.addLayer(flLayer({layer!r}))"
        import sys as _sys
        mod = _sys.modules.get("fontlab") or fl
        cls = getattr(mod, "flLayer", None)
        if cls is None:
            result["error"] = "the fontlab module has no flLayer class"
            return result
        def _add():
            nl = cls(layer)
            w.addLayer(nl)
            return nl
        ret, err = _tl_call(_add)
    result["call"] = label
    if err is not None:
        result["call_error"] = err
    else:
        result["returned"] = _tl_describe(ret)
    result["modern_after_same_wrapper"] = _tl_modern_state(w)
    tr, tr_source = _trymetrics_transform()
    if tr is not None:
        m, merr = _modern_margins_read(w, tr)
        result["margins_same_wrapper"] = m if m is not None else {"error": merr}
    # a freshly built wrapper: does the layer live in FontLab's data, or only on the old wrapper object?
    try:
        _MODERN_CACHE.pop(int(_call0(glyph, "id")), None)
        w2, how2 = _modern_wrapper(glyph, font)
        result["modern_after_rebuilt_wrapper"] = _tl_modern_state(w2)
        result["rebuilt_wrapper"] = how2
    except Exception as exc:
        result["rebuilt_wrapper_error"] = f"{type(exc).__name__}: {exc}"
    result["legacy_after"] = _tryshape_state(glyph)
    result["font_may_have_changed"] = True
    return result


# /debug/trymetrics (v0.61) - EXPERIMENT: how do advance width and sidebearings get set, and does the ink move?
_TRYMETRICS_WHAT = {"width": ("width", "advanceWidth"), "lsb": ("leftMargin", "setLSB"), "rsb": ("rightMargin", "setRSB"),
                    "sb": (None, "setSB")}
_TRYMETRICS_UPDATE_WORDS = ("update", "refresh", "invalidate", "notify", "changed", "modified", "repaint", "redraw")
_TRYMETRICS_POKE_ALLOWED = {"workspace": ("updateActiveViewport", "changed"), "glyph": ("updateActiveLayer", "updateFgGlyph", "changed"),
                            "layer": ("update", "changed"), "shape": ("update", "changed")}
_TRYMETRICS_POKE_ARG = {("glyph", "updateFgGlyph"): "auto", ("glyph", "updateActiveLayer"): "bool"}
_TRYMETRICS_WORDS = ("lsb", "rsb", "sb", "width", "advance", "metric", "margin", "bearing", "sidebearing")


def _trymetrics_transform():
    """(identity QTransform, source) or (None, reason). The class is looked up at run time; nothing is called without it."""
    import sys as _sys
    tried = []
    try:
        from PythonQt.QtGui import QTransform as _QT
        return _QT(), "PythonQt.QtGui.QTransform()"
    except Exception as exc:
        tried.append(f"PythonQt.QtGui: {type(exc).__name__}: {exc}")
    try:
        mod = _sys.modules.get("fontlab") or fl
        cls = getattr(mod, "QTransform", None)
        if cls is not None:
            return cls(), "fontlab.QTransform()"
        tried.append("fontlab module has no QTransform")
    except Exception as exc:
        tried.append(f"fontlab.QTransform: {type(exc).__name__}: {exc}")
    return None, "no QTransform class found: " + " | ".join(tried)


def _trymetrics_modern_margins(w, tr):
    """Read-only getLSB / getRSB / getSB with the identity transform; each failure is reported, never turned into a value."""
    out = {}
    for label, attr in (("lsb", "getLSB"), ("rsb", "getRSB"), ("sb", "getSB")):
        try:
            v = getattr(w, attr)(tr)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out[label] = float(v)
            elif isinstance(v, (tuple, list)) and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
                out[label] = [float(x) for x in v]
            else:
                out[label] = f"<{type(v).__name__}>"
        except Exception as exc:
            out[label + "_error"] = f"{type(exc).__name__}: {exc}"
    return out


def _trymetrics_state(glyph, w, name, tr=None):
    """Read-only snapshot: legacy margins, modern reads (zero-argument only), outline box and element transforms."""
    st = {"legacy": _glyph_margins(glyph)}
    if w is not None:
        st["modern"] = _tryshape_read(w, ("advanceWidth", "metricsLeft", "metricsRight", "metricsWidth"))
        if tr is not None:
            st["modern_margins"] = _trymetrics_modern_margins(w, tr)
        view = {}
        try:
            _describe_modern_glyph(w, view)
        except Exception as exc:
            view["error"] = f"{type(exc).__name__}: {exc}"
        st["modern_view"] = view
    st["legacy_layers"] = _tryshape_state(glyph)
    if w is not None:
        flags = {}
        flags["glyph"] = _tryshape_read(w, ("isChanged",))
        try:
            layer = w.activeLayer
            if layer is not None:
                flags["layer"] = _tryshape_read(layer, ("isChanged",))
                shapes = layer.shapes
                if type(shapes) is list and shapes:
                    flags["shape"] = _tryshape_read(shapes[0], ("isChanged",))
        except Exception as exc:
            flags["error"] = f"{type(exc).__name__}: {exc}"
        st["is_changed"] = flags
    try:
        o = get_glyph_outline(name, "body", True)
        st["outline"] = {"node_count": o.get("node_count"), "fontlab_bbox": o.get("fontlab_bbox"),
                         "elements": o.get("elements"), "layer_name": o.get("layer_name")}
    except Exception as exc:
        st["outline_error"] = f"{type(exc).__name__}: {exc}"
    return st


def _trymetrics_target(glyph, w, target):
    """(object, None) or (None, reason) for a poke / doc target. Reads only plain properties (activeLayer, shapes list)."""
    import sys as _sys
    try:
        if target == "legacy":
            return glyph, None
        if target == "workspace":
            mod = _sys.modules.get("fontlab") or fl
            return mod.flWorkspace.instance(), None
        if w is None:
            return None, "no modern wrapper for this glyph"
        if target == "glyph":
            return w, None
        layer = w.activeLayer
        if layer is None:
            return None, "no modern active layer"
        if target == "layer":
            return layer, None
        shapes = layer.shapes
        if type(shapes) is list and shapes:
            return shapes[0], None
        return None, "no shape (or layer.shapes is not a plain list)"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def debug_try_metrics(name, go, stage, what, route, value, value2, update="default", notify="no", target="", member="", members="", arg=""):
    """EXPERIMENT (WRITES only for stage=set with go=yes). Only glyph names starting with "tri" are accepted."""
    if not str(name).startswith("tri"):
        return {"error": "refused: this probe only accepts disposable glyphs whose name starts with 'tri'."}
    if stage not in ("names", "doc", "read", "set", "refresh", "poke"):
        return {"error": f"unknown stage {stage!r}: use stage=names, stage=doc, stage=read, stage=set, stage=refresh or stage=poke"}
    if target not in ("", "glyph", "layer", "shape", "workspace", "legacy"):
        return {"error": f"unknown target {target!r}: use target=glyph, layer, shape, workspace or legacy"}
    import re as _re
    member_list = [m.strip() for m in str(members).split(",") if m.strip()]
    for m in member_list + ([member] if member else []):
        if not _re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", m):
            return {"error": f"member name {m!r} is not a plain identifier"}
    for m in member_list:
        if not any(k in m.lower() for k in _TRYMETRICS_UPDATE_WORDS):
            return {"error": f"member {m!r} refused: only names containing " + " / ".join(_TRYMETRICS_UPDATE_WORDS) + " may be documented here"}
    if stage == "poke":
        if go != "yes":
            return {"error": "refused: stage=poke calls an update member in FontLab. Repeat with &go=yes (disposable test font only)."}
        if member not in _TRYMETRICS_POKE_ALLOWED.get(target, ()):
            return {"error": f"refused: {target or '(no target)'}.{member or '(no member)'} is not on the poke allowlist: " +
                    "; ".join(f"{t}.{'/'.join(ms)}" for t, ms in _TRYMETRICS_POKE_ALLOWED.items())}
        need = _TRYMETRICS_POKE_ARG.get((target, member))
        if need is None and arg:
            return {"error": f"refused: {target}.{member} takes no argument; remove &arg="}
        if need == "auto" and arg not in ("auto",):
            return {"error": f"{target}.{member}(uint id) needs &arg=auto (the glyph's own legacy id)"}
        if need == "bool" and arg not in ("yes", "no"):
            return {"error": f"{target}.{member}(bool) needs &arg=yes or &arg=no"}
    if notify not in ("no", "yes"):
        return {"error": f"unknown notify {notify!r}: use notify=no or notify=yes"}
    if update not in ("default", "none", "flglyph", "glyph", "both"):
        return {"error": f"unknown update {update!r}: use update=default, none, flglyph, glyph or both"}
    if what not in _TRYMETRICS_WHAT:
        return {"error": f"unknown what {what!r}: use what=width, lsb, rsb or sb"}
    if route not in ("legacy", "modern"):
        return {"error": f"unknown route {route!r}: use route=legacy or route=modern"}
    nums = []
    if stage == "refresh" and go != "yes":
        return {"error": "refused: stage=refresh asks FontLab to recalculate sidebearings. Repeat with &go=yes (disposable test font only)."}
    if stage == "set":
        if go != "yes":
            return {"error": "refused: stage=set changes the font. Repeat with &go=yes (disposable test font only)."}
        for label, raw in (("value", value), ("value2", value2)):
            if raw in (None, ""):
                if label == "value":
                    return {"error": "stage=set needs &value=<number>"}
                continue
            try:
                n = float(raw)
            except Exception:
                return {"error": f"{label} must be a number"}
            if n != n or abs(n) > 10000:
                return {"error": f"{label} out of range (-10000..10000)"}
            nums.append(n)
        if route == "legacy" and what == "sb":
            return {"error": "what=sb exists only on route=modern (setSB)"}
        if route == "legacy" and what in ("lsb", "rsb"):
            return {"refused": True, "error": "refused: the legacy setters glyph.leftMargin / glyph.rightMargin CRASHED FontLab (live, v0.61) "
                    "on a glyph whose shape was built through the modern API. Nothing was called. Use route=modern, or what=width."}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    result = {"open": True, "found": True, "name": name, "stage": stage}
    w = None
    try:
        w, how = _modern_wrapper(glyph, font)
        result["modern_wrapper"] = how
    except Exception as exc:
        result["modern_wrapper_error"] = str(exc)
    if stage == "doc" and target and member_list:
        obj, why = _trymetrics_target(glyph, w, target)
        if obj is None:
            result["error"] = f"target {target!r} unavailable: {why}"
            return result
        out = {}
        cls = type(obj)
        for m in member_list:
            try:
                try:
                    a = getattr(cls, m)
                except AttributeError:
                    if not m.startswith(("set", "get", "update", "refresh", "invalidate", "notify", "changed", "repaint", "redraw")):
                        raise
                    a = getattr(obj, m)            # a bound METHOD object only (never called)
                d = getattr(a, "__doc__", None)
                out[m] = {"type": type(a).__name__, "doc": (str(d)[:600] if d else None)}
            except Exception as exc:
                out[m] = {"error": f"{type(exc).__name__}: {exc}"}
        result["target"] = target
        result["member_docs"] = out
        return result
    if stage == "doc":
        def docs(obj, members):
            out = {}
            cls = type(obj)
            for m in members:
                try:
                    try:
                        a = getattr(cls, m)        # read from the CLASS: no getter runs, nothing is called
                    except AttributeError:
                        if not m.startswith(("set", "get", "update")):
                            raise                  # a property: reading it on the instance would run its getter
                        a = getattr(obj, m)        # a bound METHOD object only (never called)
                    d = getattr(a, "__doc__", None)
                    out[m] = {"type": type(a).__name__, "doc": (str(d)[:600] if d else None)}
                except Exception as exc:
                    out[m] = {"error": f"{type(exc).__name__}: {exc}"}
            return out
        result["legacy_docs"] = docs(glyph, ("metrics", "vsb", "leftMargin", "rightMargin", "width"))
        result["modern_docs"] = (docs(w, ("setLSB", "setRSB", "setSB", "getLSB", "getRSB", "getSB", "updateSidebearings", "advanceWidth",
                                          "leftMetric", "rightMetric", "metricsRect")) if w is not None else None)
        return result
    if stage == "names":
        def words(o):
            try:
                return sorted(n for n in dir(o) if not n.startswith("_") and any(k in n.lower() for k in _TRYMETRICS_WORDS))
            except Exception as exc:
                return f"error: {type(exc).__name__}: {exc}"
        result["legacy_names"] = words(glyph)
        result["modern_names"] = words(w) if w is not None else None
        def upd(o):
            try:
                return sorted(n for n in dir(o) if not n.startswith("_") and any(k in n.lower() for k in _TRYMETRICS_UPDATE_WORDS))
            except Exception as exc:
                return f"error: {type(exc).__name__}: {exc}"
        un = {"legacy_glyph": upd(glyph)}
        if w is not None:
            un["modern_glyph"] = upd(w)
            layer = None
            try:
                layer = w.activeLayer
            except Exception as exc:
                un["modern_layer"] = f"error: {type(exc).__name__}: {exc}"
            if layer is not None:
                un["modern_layer"] = upd(layer)
                try:
                    shapes = layer.shapes
                    un["modern_shape"] = upd(shapes[0]) if (type(shapes) is list and shapes) else "no shape (or shapes is not a plain list)"
                except Exception as exc:
                    un["modern_shape"] = f"error: {type(exc).__name__}: {exc}"
        try:
            import sys as _sys
            mod = _sys.modules.get("fontlab") or fl
            un["flWorkspace_instance"] = upd(mod.flWorkspace.instance())
        except Exception as exc:
            un["flWorkspace_instance"] = f"error: {type(exc).__name__}: {exc}"
        result["update_names"] = un
        return result
    tr, tr_source = _trymetrics_transform()
    result["transform_source"] = tr_source
    before = _trymetrics_state(glyph, w, name, tr)
    result["state_before"] = before
    if stage == "read":
        return result
    calls = []
    result["calls"] = calls
    if stage == "poke":
        obj, why = _trymetrics_target(glyph, w, target)
        if obj is None:
            result["error"] = f"target {target!r} unavailable: {why}"
            return result
        result["target"] = target
        result["member"] = member
        try:
            need = _TRYMETRICS_POKE_ARG.get((target, member))
            if need == "auto":
                gid = int(_call0(w, "fgGlyphId"))
                calls.append(f"{target}.{member}({gid})")
                result["returned"] = repr(getattr(obj, member)(gid))
            elif need == "bool":
                calls.append(f"{target}.{member}({arg == 'yes'})")
                result["returned"] = repr(getattr(obj, member)(arg == "yes"))
            else:
                calls.append(f"{target}.{member}()")
                result["returned"] = repr(getattr(obj, member)())
        except Exception as exc:
            result["failed_at"] = calls[-1]
            result["error"] = f"{type(exc).__name__}: {exc}"
        result["state_after"] = _trymetrics_state(glyph, w, name, tr)
        result["font_may_have_changed"] = True
        return result
    if stage == "refresh":
        try:
            if w is None:
                raise RuntimeError("no modern wrapper for this glyph")
            calls.append(f"flGlyph.updateSidebearings({notify == 'yes'})")
            result["returned"] = repr(w.updateSidebearings(notify == "yes"))
        except Exception as exc:
            result["failed_at"] = calls[-1] if calls else "setup"
            result["error"] = f"{type(exc).__name__}: {exc}"
        result["state_after"] = _trymetrics_state(glyph, w, name, tr)
        result["font_may_have_changed"] = True
        return result
    result["route"] = route
    result["what"] = what
    legacy_attr, modern_name = _TRYMETRICS_WHAT[what]
    try:
        if route == "legacy":
            calls.append(f"glyph.{legacy_attr} = {nums[0]}")
            setattr(glyph, legacy_attr, nums[0])
        else:
            if w is None:
                raise RuntimeError("no modern wrapper for this glyph")
            if what == "width":
                calls.append(f"flGlyph.advanceWidth = {nums[0]}")
                w.advanceWidth = nums[0]
            else:
                if tr is None:
                    raise RuntimeError("no QTransform available: " + tr_source)
                if what == "lsb":
                    label, fn_args = f"flGlyph.setLSB({nums[0]}, False, tr)", (nums[0], False, tr)
                elif what == "rsb":
                    label, fn_args = f"flGlyph.setRSB({nums[0]}, tr)", (nums[0], tr)
                else:
                    if len(nums) < 2:
                        raise RuntimeError("what=sb needs &value=<left>&value2=<right>")
                    label, fn_args = f"flGlyph.setSB({nums[0]}, {nums[1]}, False, False, tr)", (nums[0], nums[1], False, False, tr)
                calls.append(label)
                result["returned"] = repr(getattr(w, modern_name)(*fn_args))
    except Exception as exc:
        result["failed_at"] = calls[-1] if calls else "setup"
        result["error"] = f"{type(exc).__name__}: {exc}"
    mode = update if update != "default" else ("both" if route == "legacy" else "flglyph")
    result["update_mode"] = mode
    wanted = {"none": (), "flglyph": ("flGlyph.update()",), "glyph": ("glyph.update()",), "both": ("glyph.update()", "flGlyph.update()")}[mode]
    for label, obj in (("glyph.update()", glyph), ("flGlyph.update()", w)):
        if obj is None or label not in wanted:
            continue
        try:
            obj.update()
            calls.append(label)
        except Exception as exc:
            calls.append(f"{label} -> {type(exc).__name__}: {exc}")
    after = _trymetrics_state(glyph, w, name, tr)
    result["state_after"] = after
    def box(st):
        b = (st.get("outline") or {}).get("fontlab_bbox") or {}
        return b if isinstance(b, dict) else {}
    bb, ba = box(before), box(after)
    result["ink_moved"] = (bb.get("left") != ba.get("left")) or (bb.get("right") != ba.get("right"))
    mm = after.get("modern_margins") or {}
    try:
        adv = float((after.get("modern") or {})["advanceWidth"])
        total = float(mm["lsb"]) + (float(ba["right"]) - float(ba["left"])) + float(mm["rsb"])
        result["width_equals_lsb_ink_rsb"] = abs(total - adv) < 0.01
        result["lsb_plus_ink_plus_rsb"] = total
    except Exception as exc:
        result["width_equals_lsb_ink_rsb"] = None
        result["width_check_note"] = f"not computable from the modern numbers: {type(exc).__name__}: {exc}"
    result["font_may_have_changed"] = True
    return result


# Read-only, zero-argument fgNode predicates (names from a real dir() of an
# fgNode in v0.22). Setters (setG2, setSelected, ...) are deliberately NOT
# here so no probe can ever mutate the font.
_SAFE_NODE_CALLS = (
    "isOn", "isOff", "isCurve", "isCurveOff", "isG2",
    "isInterpolatedX", "isInterpolatedY", "isSelected",
)


def _call_node_predicate(node, method):
    """Call one whitelisted zero-arg method on a node. Never raises."""
    if method not in _SAFE_NODE_CALLS:
        return f"<refused: {method!r} is not a whitelisted read-only call>"
    try:
        fn = getattr(node, method)
        if not callable(fn):
            return f"<not callable: {type(fn).__name__}>"
        val = fn()
    except Exception as exc:
        return f"<error: {exc}>"
    if isinstance(val, (str, int, float, bool)) or val is None:
        return val
    return f"<{type(val).__name__}>"


def _get_body_layer(glyph):
    """Warm-up (touch glyph.layer) then fetch bodyLayer. Returns the layer
    or None. See v0.21 notes: the warm-up is REQUIRED."""
    try:
        _ = glyph.layer
    except Exception:
        pass
    for _i in range(5):
        try:
            candidate = glyph.bodyLayer
        except Exception:
            continue
        if candidate is not None:
            return candidate
    return None


_LAYER_ROUTES = {
    "body": "bodyLayer",
    "active": "activeLayer",
    "strict": "bodyLayerStrict",
    "glayer": "layer",
}


def _get_layer_by_route(glyph, route):
    """Same warm-up + retry discipline as _get_body_layer, but for any of the
    layer routes in _LAYER_ROUTES. Returns the layer object or None."""
    attr = _LAYER_ROUTES.get(route)
    if attr is None:
        return None
    try:
        _ = glyph.layer
    except Exception:
        pass
    for _i in range(5):
        try:
            candidate = getattr(glyph, attr)
        except Exception:
            continue
        if candidate is not None:
            return candidate
    return None


def debug_find_node(name, index, stage, attrs=None):
    """Staged, isolated probe of fgLayer.findNode(index). Each stage is a
    separate request so that if FontLab crashes, the last stage run is the
    culprit.
      fetch: call findNode(index), report ONLY the type / None-ness.
      dir:   as fetch, plus the node's public attribute NAMES (no values).
      point: as fetch, plus node.x/node.y beside the values of node.point
             (default attrs x,y) and its public attribute names.
      call:  as fetch, plus calls the whitelisted zero-arg predicates named
             in `attrs` (see _SAFE_NODE_CALLS). Nothing else is callable.
      read:  as fetch, plus getattr() on exactly the names in `attrs`.
             Callables are reported as '<callable>' and never invoked.
    The index is range-checked against countNodes() first, so we never ask
    the native side for a node that cannot exist."""
    if stage not in ("fetch", "dir", "read", "call", "point"):
        return {"error": 'stage must be "fetch", "dir", "read", "call" or "point"'}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}

    layer = _get_body_layer(glyph)
    if layer is None:
        return {"open": True, "found": True, "error": "bodyLayer was None on every attempt"}

    node_count = layer.countNodes()
    result = {"open": True, "found": True, "name": name, "stage": stage,
              "index": index, "node_count": node_count}
    if index < 0 or index >= node_count:
        result["error"] = f"index out of range (valid: 0..{node_count - 1})"
        return result

    node = layer.findNode(index)
    result["node_is_none"] = node is None
    result["node_type"] = type(node).__name__
    if node is None or stage == "fetch":
        return result

    if stage == "dir":
        result["public_names"] = [n for n in dir(node) if not n.startswith("_")]
        return result

    if stage == "read":
        values = {}
        for attr in (attrs or []):
            try:
                val = getattr(node, attr)
            except Exception as exc:
                values[attr] = f"<error: {exc}>"
                continue
            if callable(val):
                values[attr] = "<callable>"
            elif isinstance(val, (str, int, float, bool)) or val is None:
                values[attr] = val
            else:
                values[attr] = f"<{type(val).__name__}>"
        result["values"] = values
        return result

    if stage == "call":
        result["calls"] = {m: _call_node_predicate(node, m) for m in (attrs or [])}
        return result

    if stage == "point":
        # Compare node.x/node.y with the node's .point object (an fgPoint).
        # Only attribute reads; nothing is called.
        def _simple(obj, attr):
            try:
                val = getattr(obj, attr)
            except Exception as exc:
                return f"<error: {exc}>"
            if callable(val):
                return "<callable>"
            if isinstance(val, (str, int, float, bool)) or val is None:
                return val
            return f"<{type(val).__name__}>"
        result["node_x"] = _simple(node, "x")
        result["node_y"] = _simple(node, "y")
        try:
            pt = node.point
        except Exception as exc:
            result["point_error"] = str(exc)
            return result
        result["point_is_none"] = pt is None
        result["point_type"] = type(pt).__name__
        if pt is not None:
            result["point_names"] = [n for n in dir(pt) if not n.startswith("_")]
            wanted = attrs or ["x", "y"]
            result["point_values"] = {a: _simple(pt, a) for a in wanted}
        return result

    result["error"] = 'stage must be "fetch", "dir", "read", "call" or "point"'
    return result


def get_glyph_nodes(name, extra_attrs=None, calls=None):
    """All nodes of one glyph via layer.findNode(i) for i in 0..countNodes()-1.
    findNode(i) + reading x/y is CONFIRMED safe on a real glyph (v0.22).
    Always returns x and y; `extra_attrs` are read with the same
    getattr-only, never-invoke-callables rule as debug_find_node, and are
    UNCONFIRMED attributes (probe them with /debug/findnode first)."""
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    layer = _get_body_layer(glyph)
    if layer is None:
        return {"open": True, "found": True, "error": "bodyLayer was None on every attempt"}

    node_count = layer.countNodes()
    nodes = []
    problems = []
    for i in range(node_count):
        node = layer.findNode(i)
        if node is None:
            problems.append(f"node {i}: findNode returned None")
            continue
        entry = {"index": i}
        for attr in ["x", "y"] + list(extra_attrs or []):
            try:
                val = getattr(node, attr)
            except Exception as exc:
                entry[attr] = f"<error: {exc}>"
                continue
            if callable(val):
                entry[attr] = "<callable>"
            elif isinstance(val, (str, int, float, bool)) or val is None:
                entry[attr] = val
            else:
                entry[attr] = f"<{type(val).__name__}>"
        for method in (calls or []):
            entry[method] = _call_node_predicate(node, method)
        nodes.append(entry)

    result = {"open": True, "found": True, "name": name,
              "contour_count": layer.countContours(),
              "node_count": node_count, "nodes": nodes}
    if problems:
        result["problems"] = problems
    return result


def find_nonempty_glyphs():
    """Scan every glyph for outline data, using the confirmed warm-up
    pattern (touch glyph.layer, then bodyLayer) and countContours()/
    countNodes(). Reports glyphs with at least one node; also lists any
    glyph whose layer could not be read, so a skip is never silent."""
    font = _open_font()
    if font is None:
        return {"open": False}
    nonempty, unreadable, scanned = [], [], 0
    for glyph in font.glyphs:
        scanned += 1
        gname = str(glyph.name)
        try:
            layer = _get_body_layer(glyph)
            if layer is None:
                unreadable.append(gname)
                continue
            nodes = layer.countNodes()
            if nodes > 0:
                nonempty.append({"name": gname,
                                 "contours": layer.countContours(),
                                 "nodes": nodes})
        except Exception as exc:
            unreadable.append(f"{gname}: {exc}")
    return {"open": True, "scanned": scanned, "nonempty": nonempty,
            "unreadable": unreadable}


def _layer_bbox_dict(layer):
    """FontLab's own box of the layer: layer.boundingBox(layer.matrix), read
    through the zero-arg getters confirmed on a real session (v0.31). NOTE:
    this is the box around ALL nodes including off-curve handles, not the
    curve extremes. Never raises; failures come back as {"error": ...}."""
    try:
        rect = layer.boundingBox(layer.matrix)
    except Exception as exc:
        return {"error": f"boundingBox raised: {exc}"}
    if rect is None:
        return {"error": "boundingBox returned None"}
    out = {}
    for m in ("left", "right", "top", "bottom"):
        try:
            fn = getattr(rect, m)
            val = fn() if callable(fn) else fn
        except Exception as exc:
            return {"error": f"rect.{m} failed: {exc}"}
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            return {"error": f"rect.{m} was not a number ({type(val).__name__})"}
        out[m] = float(val)
    return out


def _glyph_margins(glyph):
    """glyph.leftMargin / rightMargin / width: FontLab's own numbers, computed
    from the CURVE extremes. Never raises."""
    out = {}
    for attr, key in (("leftMargin", "left"), ("rightMargin", "right"), ("width", "width")):
        try:
            val = getattr(glyph, attr)
        except Exception as exc:
            out[key] = None
            out["error"] = f"{attr} failed: {exc}"
            continue
        out[key] = float(val) if isinstance(val, (int, float)) and not isinstance(val, bool) else None
    return out


def _component_count(glyph):
    """len(glyph.components) only (len() has been safe; [] has not)."""
    try:
        return len(glyph.components)
    except Exception:
        return None


def _glyph_layer_count(glyph):
    """len(glyph.layers) only (len() has been safe; [] has not). None if unreadable.
    Real FontLab 8 values: A, testglyph1 and Arial's drawn .notdef -> 1; the empty .notdef of the test font -> 0."""
    try:
        return len(glyph.layers)
    except Exception:
        return None


# --- .notdef check and note (v0.46; since v0.203 an OUTPUT line, no dialog) -----
# Basis (real FontLab 8.4 session, read-only probes): the empty .notdef of the test font has len(glyph.layers) == 0 and
# bodyLayer/activeLayer None on every attempt; Arial's drawn .notdef has 1 layer, 2 contours, 8 nodes and reads normally.
# So "no layers" counts as "no outline data". A glyph whose layer cannot be reached although layers exist is 'unknown',
# NEVER 'empty': the note is made only on POSITIVE evidence (missing or empty), never because a read failed.
# v0.203 (DECISIONS 2026-11-21): no dialog any more; one OUTPUT line per font and listener run, remembered by the font's
# package fgId (all unsaved fonts shared the path "" before, so a second unsaved font was never noted).
_NOTDEF_NOTED = {}       # package fgId -> the status already noted for that font during this listener run
_NOTDEF_OUTPUT = {
    "missing": "this font has no glyph named .notdef; every font needs one as glyph 0: it shows when a character is missing",
    "empty": ".notdef is empty; it shows when a character is missing, usually as a rectangle, often with a ? or an X",
}
_NOTDEF_OUTPUT_MATURE = "; this font has every letter A-Z and a-z, so it may have been overlooked"
# v0.203 - maturity of a font whose .notdef is empty: all 52 English letters present (by primary Unicode) and at least one of them
# drawn. The drawn check reads the modern layer only (the count _notdef_modern_outline_counts makes) and stops at the first drawn letter.
_LETTER_CODEPOINTS = tuple(range(0x41, 0x5B)) + tuple(range(0x61, 0x7B))
_LETTERS_FIRST = (ord("n"), ord("o"), ord("H"), ord("O"))


def _notdef_modern_outline_counts(glyph, font):
    """v0.120 (F1). {"nodes", "shapes", "components"} of the glyph's modern active layer when it holds nodes or
    components, else None (no modern side, no modern layer, a count unreadable, or nothing in it: then the legacy check
    runs, which cannot flatten anything because there is no outline). Never raises."""
    try:
        w, _how = _modern_wrapper(glyph, font)
        state, layer = _tryshape_modern_state(w)
    except Exception:
        return None
    if layer is None:
        return None
    counts = {k: state.get(k) for k in ("nodes", "shapes", "components")}
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in counts.values()):
        return None
    return counts if (counts["nodes"] > 0 or counts["components"] > 0) else None


def check_notdef():
    """Read-only. Does the current font have a .notdef glyph, and does it hold any outline data?
    status: "missing"     no glyph named .notdef
            "empty"       exists, and FontLab holds no outline data for it (0 layers, or 1 layer with 0 nodes/shapes
                          and no components)
            "has_outline" exists and has nodes, shapes or components
            "unknown"     could not be determined (unreadable layer, several layers, a count failed): NO verdict.
    Never shows a dialog and never changes anything."""
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph, index, first_name, scanned = None, None, None, 0
    for i, g in enumerate(font.glyphs):
        scanned = i + 1
        gname = str(g.name)
        if i == 0:
            first_name = gname
        if gname == ".notdef":
            glyph, index = g, i
            break
    result = {"open": True, "exists": glyph is not None, "first_glyph_name": first_name}
    evidence, notes = [], []
    if glyph is None:
        result["status"] = "missing"
        result["evidence"] = [f"no glyph named '.notdef' among the {scanned} glyphs of this font (glyph 0 is named {first_name!r})"]
        return result
    result["index"] = index
    if index != 0:
        notes.append(f".notdef is glyph number {index}; the OpenType spec wants it to be glyph 0")
    modern = _notdef_modern_outline_counts(glyph, font) if _MODERN_FIRST else None
    if modern is not None:
        # v0.120 (F1): a .notdef with modern nodes is judged from the modern layer only; the legacy layer is not touched
        result.update({"source": "modern", "counts": {"nodes": modern["nodes"], "shapes": modern["shapes"]},
                       "component_count": modern["components"], "status": "has_outline",
                       "evidence": [f"FontLab's modern layer holds nodes {modern['nodes']}, shapes {modern['shapes']}, "
                                    f"components {modern['components']}"]})
        if notes:
            result["notes"] = notes
        return result
    layers = _glyph_layer_count(glyph)
    result["layer_count"] = layers
    status = "unknown"

    def _is_count(v):
        return isinstance(v, int) and not isinstance(v, bool)

    if layers is None:
        evidence.append("len(glyph.layers) could not be read")
    elif layers > 1:
        evidence.append(f"the glyph has {layers} layers; multi-layer glyphs are untested, so no verdict")
    elif layers == 0:
        comps = _component_count(glyph)
        result["component_count"] = comps
        if not _is_count(comps):
            evidence.append("FontLab holds 0 layers for the glyph, but its component count could not be read")
        elif comps > 0:
            status = "has_outline"
            evidence.append(f"FontLab holds 0 layers for the glyph, but it has {comps} component(s)")
        else:
            status = "empty"
            evidence.append("FontLab holds 0 layers for the glyph and it has no components: no outline data")
    else:   # exactly one layer
        layer = _get_body_layer(glyph)
        if layer is None:
            evidence.append("the glyph has 1 layer but bodyLayer was None on every attempt, so its contents were not read")
        else:
            try:
                counts = {"nodes": layer.countNodes(), "contours": layer.countContours(), "shapes": layer.countShapes()}
            except Exception as exc:
                counts = None
                evidence.append(f"the layer's counts could not be read: {exc}")
            if counts is not None:
                result["counts"] = counts
                comps = _component_count(glyph)
                result["component_count"] = comps
                if not all(_is_count(v) for v in counts.values()) or not _is_count(comps):
                    evidence.append("a count from FontLab was not a plain number, so no verdict")
                elif any(v > 0 for v in counts.values()) or comps > 0:
                    status = "has_outline"
                    evidence.append(f"nodes {counts['nodes']}, contours {counts['contours']}, shapes {counts['shapes']}, components {comps}")
                else:
                    status = "empty"
                    evidence.append("1 layer with 0 nodes, 0 contours, 0 shapes and no components")
    result["status"] = status
    result["evidence"] = evidence
    if notes:
        result["notes"] = notes
    if status == "empty":
        result["maturity"] = _font_maturity(font)   # v0.203
    return result


def _font_maturity(font):
    """v0.203 - READ-ONLY. Is the font mature, so that an empty .notdef is likely an oversight? Mature: all 52 English letters
    (U+0041-005A, U+0061-007A) are present as some glyph's primary Unicode, and at least one of those glyphs is drawn (a node or a
    component on its modern active layer). The codepoint scan is the one _other_glyphs_with_unicode makes; the drawn check starts
    with n o H O and stops at the first drawn letter. A glyph that cannot be read is counted ("unreadable"), never skipped
    silently: when letters are missing and some glyphs were unreadable, "mature" is None (unknown). Never raises."""
    try:
        glyphs = list(font.glyphs)
    except Exception as exc:
        return {"mature": None, "error": f"the glyph list could not be read ({type(exc).__name__}: {exc})"}
    wanted = set(_LETTER_CODEPOINTS)
    holders, unreadable = {}, 0
    for g in glyphs:
        try:
            cp = g.unicode
        except Exception:
            unreadable += 1
            continue
        if type(cp) is int and cp in wanted and cp not in holders:
            holders[cp] = g
    missing = [chr(cp) for cp in _LETTER_CODEPOINTS if cp not in holders]
    out = {"letters_present": len(_LETTER_CODEPOINTS) - len(missing), "letters_missing": "".join(missing), "unreadable": unreadable}
    if missing:
        out["mature"] = None if unreadable else False
        return out
    order = list(_LETTERS_FIRST) + [cp for cp in _LETTER_CODEPOINTS if cp not in _LETTERS_FIRST]
    checked = 0
    for cp in order:
        checked += 1
        if _notdef_modern_outline_counts(holders[cp], font) is not None:
            out.update(mature=True, drawn_letter=chr(cp), letters_checked_for_outline=checked)
            return out
    out.update(mature=False, drawn_letter=None, letters_checked_for_outline=checked)
    return out


def _notdef_font_key():
    """v0.203 - (the current package's fgId, None) or (None, reason). flWorkspace.currentPackage follows the font in front (T5)."""
    try:
        ws = fl.flWorkspace.instance()
    except Exception as exc:
        return None, f"the workspace could not be reached ({type(exc).__name__}: {exc})"
    pkg, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return None, err
    if pkg is None:
        return None, "the workspace has no current package"
    return _package_fg_id(pkg, "the current package")


def warn_notdef(force=False):
    """Re-check .notdef HERE (nothing is noted on the caller's say-so). v0.203: NO dialog. When .notdef is missing or empty and this
    font has not been noted for that status in this listener run (unless force), it is noted: the activity log prints one OUTPUT
    line. Remembered by the font's package fgId; when the fgId cannot be read nothing is remembered, so the note may repeat but
    is never wrongly held back. already_warned and dialog_shown stay in the reply for older servers."""
    font = _open_font()
    if font is None:
        return {"open": False}
    check = check_notdef()
    status = check.get("status")
    out = {"open": True, "status": status, "evidence": check.get("evidence", []),
           "noted": False, "already_noted": False, "already_warned": False, "dialog_shown": False}
    if "maturity" in check:
        out["maturity"] = check["maturity"]
    if status not in ("missing", "empty"):
        out["reason"] = ("no note needed: .notdef has an outline" if status == "has_outline"
                         else "could not be determined, so nothing was noted")
        return out
    key, key_error = _notdef_font_key()
    if key_error:
        out["memory_note"] = f"not remembered for this font: {key_error}"
    if not force and key is not None and _NOTDEF_NOTED.get(key) == status:
        out["already_noted"] = out["already_warned"] = True
        return out
    if key is not None:
        _NOTDEF_NOTED[key] = status
    out["noted"] = True
    return out


_READER_MARGIN_TOLERANCE = 0.05


def _reader_margins_compare(w, legacy_margins):
    """Never raises. Compares the MODERN left / right sidebearing and advance width with the legacy reader's margins (leftMargin,
    rightMargin, width). Returns {"margins_agree": True} / {"margins_agree": False, "margins_differ": [...], "legacy_margins": {...},
    "modern_margins": {...}} / {"margins_agree": None, "margins_note": why}. A failed read is never turned into a verdict."""
    try:
        tr, why = _trymetrics_transform()
        if tr is None:
            return {"margins_agree": None, "margins_note": f"the modern margins were not read: {why}"}
        m, err = _modern_margins_read(w, tr)
        if m is None:
            return {"margins_agree": None, "margins_note": f"the modern margins were not read: {err}"}
        leg = {"left": _num(legacy_margins.get("left")), "right": _num(legacy_margins.get("right")), "advance_width": _num(legacy_margins.get("width"))}
        if any(v is None for v in leg.values()):
            return {"margins_agree": None, "margins_note": "the legacy margins are not numbers, so they could not be compared"}
        mod = {"left": m["lsb"], "right": m["rsb"], "advance_width": m["advance"]}
        differs = [k for k in ("left", "right", "advance_width") if abs(leg[k] - mod[k]) > _READER_MARGIN_TOLERANCE]
        if not differs:
            return {"margins_agree": True}
        return {"margins_agree": False, "margins_differ": differs, "legacy_margins": leg, "modern_margins": mod}
    except Exception as exc:
        return {"margins_agree": None, "margins_note": f"the margins could not be compared ({type(exc).__name__}: {exc})"}


def _reader_modern_check(name, legacy_nodes, legacy_margins=None):
    """Never raises. Compares the node count of the MODERN active layer with the legacy reader's node count (the legacy view lags on
    glyphs changed through the API; v0.72). v0.88: when the counts agree and the legacy margins are given, the margins are compared too
    (a sidebearing or width change moves the nodes without changing their number, which is how the legacy view can be stale with equal counts)."""
    try:
        font = fl.CurrentFont()
        glyph = _find_glyph(font, name)
        w, _how = _modern_wrapper(glyph, font)
        state, layer = _tryshape_modern_state(w)
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    if layer is None:
        return {"available": True, "modern_layer": False}
    nodes, shapes = state.get("nodes"), state.get("shapes")
    out = {"available": True, "modern_layer": True, "modern_nodes": nodes, "modern_shapes": shapes}
    if isinstance(nodes, int) and isinstance(legacy_nodes, int):
        out["agree"] = nodes == legacy_nodes
    else:
        out["agree"] = None
    if out["agree"] is True and nodes > 0 and isinstance(legacy_margins, dict):
        out.update(_reader_margins_compare(w, legacy_margins))
    return out


_MODERN_OUTLINE_MAX_NODES = 5000


def _read_modern_outline(name):
    """Every contour and node of the MODERN active layer, or {"available": False, "error": ...} (never a partial outline, never raises).
    Only calls proven live (v0.73): layer.getContours() returning a plain list, contour.getNodeAt(i) after a range check."""
    try:
        font = fl.CurrentFont()
        glyph = _find_glyph(font, name)
        w, _how = _modern_wrapper(glyph, font)
        state, layer = _tryshape_modern_state(w)
    except Exception as exc:
        return {"available": False, "error": f"the modern glyph could not be reached: {type(exc).__name__}: {exc}"}
    if layer is None:
        return {"available": False, "error": "this glyph has no modern active layer"}
    total = state.get("nodes")
    if not isinstance(total, int) or isinstance(total, bool):
        return {"available": False, "error": "the modern node count is not readable"}
    if total > _MODERN_OUTLINE_MAX_NODES:
        return {"available": False, "error": f"the layer has {total} nodes, more than the {_MODERN_OUTLINE_MAX_NODES} that are read"}
    contours, err = _tl_call(lambda: layer.getContours())
    if err is not None:
        return {"available": False, "error": f"layer.getContours() failed: {err}"}
    if type(contours) not in (list, tuple):
        return {"available": False, "error": f"layer.getContours() returned a {type(contours).__name__}, not a plain list: it is not indexed"}
    out, read = [], 0
    for ci in range(len(contours)):
        contour = contours[ci]
        entry = {"index": ci}
        for attr in ("closed", "clockwise", "nodesCount"):
            v, err = _tl_call(lambda a=attr: _call0(contour, a))
            if err is not None:
                return {"available": False, "error": f"contour {ci}: {attr} could not be read: {err}"}
            entry[attr] = _rm_plain(v)
        count = entry["nodesCount"]
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            return {"available": False, "error": f"contour {ci}: nodesCount is not a number"}
        nodes = []
        for ni in range(count):
            nd, err = _tl_call(lambda i=ni: contour.getNodeAt(i))
            if err is not None or nd is None:
                return {"available": False, "error": f"contour {ci} node {ni}: getNodeAt failed: {err or 'returned None'}"}
            rec = {"index": ni}
            for label in ("x", "y", "isOn", "isOff", "isCurve", "smooth"):
                v, err = _tl_call(lambda a=label: _call0(nd, a))
                if err is not None:
                    return {"available": False, "error": f"contour {ci} node {ni}: {label} could not be read: {err}"}
                rec[label] = _rm_plain(v)
            if any(isinstance(rec[k], bool) or not isinstance(rec[k], (int, float)) for k in ("x", "y")):
                return {"available": False, "error": f"contour {ci} node {ni}: x / y are not numbers"}
            nodes.append(rec)
            read += 1
        entry["nodes"] = nodes
        out.append(entry)
    result = {"available": True, "contours": out, "node_count": read, "expected_node_count": total}
    if read != total:
        return {"available": False, "error": f"read {read} nodes but the layer reports {total}: the outline is not trusted"}
    tr, _src = _trymetrics_transform()
    if tr is not None:
        m, _err = _modern_margins_read(w, tr)
        if m is not None:
            result["margins"] = m
    return result


# v0.174: _COMPONENT_BOX_MAX (20, v0.130, no recorded reason) removed by the user's decision of 2026-11-17: every component gets its boxes,
# and the outline reply says how long they took (elements.boxes_seconds). 30 boxes took a few milliseconds live (1157, 1165).


def _component_source_read(font, name):
    """v0.130. {"layer_name", "box"} of a component's source glyph, or {"error"}: its modern active layer and ONE layer.inkBox()
    (live 519-530, no F1 after it). Modern objects only, so a Power Brush source is not armed. Never raises."""
    glyph, err = _tl_call(lambda: _find_glyph(font, name))
    if err is not None:
        return {"error": f"the source glyph could not be looked up ({err})"}
    if glyph is None:
        return {"error": f"no glyph named {name!r}"}
    pair, err = _tl_call(lambda: _modern_wrapper(glyph, font))
    if err is not None:
        return {"error": f"the source glyph's modern side could not be reached ({err})"}
    layer, err = _tl_call(lambda: pair[0].activeLayer)
    if err is not None or layer is None:
        return {"error": f"the source glyph has no readable modern active layer ({err or 'None'})"}
    layer_name, err = _tl_call(lambda: str(_call0(layer, "name")))
    if err is not None:
        return {"error": f"the source layer's name could not be read ({err})"}
    box = _modern_ink_box(layer)
    if "error" in box:
        return {"error": f"the source layer's ink box could not be read ({box['error']})"}
    return {"layer_name": layer_name, "box": box}


def _component_source_box(font, entry, cache):
    """v0.130. The ink box of the source layer this component names, or {"error"}; one read per source glyph and outline."""
    name = entry.get("component_glyph")
    if not isinstance(name, str) or not name:
        return {"error": "the name of the source glyph could not be read"}
    if name not in cache:
        cache[name] = _component_source_read(font, name)
    read = cache[name]
    if "error" in read:
        return {"error": read["error"]}
    if entry.get("component_layer") != read["layer_name"]:
        return {"error": f"the component names layer {entry.get('component_layer')!r}, the source glyph's active layer is {read['layer_name']!r}"}
    return read["box"]


def _add_component_boxes(w, font, entries):
    """v0.130. For every element that is a component (live 606, 610): "ink_box", ONE shape.inkBox() with its transforms applied
    (live 644-646, 650), and "source_ink_box", the box of the source layer it names. Components only: inkBox() on a Power Brush
    shape is untested (F1). layer.shapes must be a real list that still matches the element list. A box that could not be read
    is {"error"}, never missing or empty. Plain elements get no key. Never raises. v0.174: returns the seconds the reads took, or None."""
    wanted = [i for i, e in enumerate(entries) if e.get("is_component") is True]
    if not wanted:
        return None
    t0 = time.perf_counter()
    shapes, err = _tl_call(lambda: w.activeLayer.shapes)
    why = None
    if err is not None:
        why = f"layer.shapes could not be read ({err})"
    elif type(shapes) is not list or len(shapes) != len(entries):
        why = "layer.shapes is not a plain list matching the element list"
    sources = {}
    for i in wanted:
        entry = entries[i]
        if why is not None:
            entry["ink_box"], entry["source_ink_box"] = {"error": why}, {"error": why}
            continue
        shape = shapes[i]
        box, call_err = _tl_call(lambda: shape.inkBox())
        entry["ink_box"] = {"error": call_err} if call_err is not None else _rect_plain(box)
        entry["source_ink_box"] = _component_source_box(font, entry, sources)
    return round(time.perf_counter() - t0, 3)


def _modern_only_outline(name, route):
    """v0.120 (F1). The outline of a glyph that has modern nodes, read from the modern layer only: never glyph.layer,
    glyph.layers, bodyLayer, findNode or the legacy margins, which can flatten a Power Brush glyph at the next
    font.update(). Returns None when the legacy route must answer: the modern side cannot be reached, or the modern
    layer is missing or holds no nodes (then there is no outline to flatten). A modern layer whose node count is not
    readable, or whose outline cannot be read, gets an error and NO legacy fallback."""
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    try:
        w, how = _modern_wrapper(glyph, font)
        state, layer = _tryshape_modern_state(w)
    except Exception:
        return None
    if layer is None:
        return None
    nodes = state.get("nodes")
    base = {"open": True, "found": True, "name": name, "source": "modern", "layer_route": route,
            "layer_name": state.get("layer_name"), "wrapper": how}
    if not isinstance(nodes, int) or isinstance(nodes, bool):
        return dict(base, error=("the node count of FontLab's modern layer could not be read; the legacy layer was not "
                                 "read instead, because reading it can flatten a Power Brush glyph"))
    if nodes <= 0:
        return None
    mo = _read_modern_outline(name)
    if not mo.get("available"):
        return dict(base, error=(f"the outline could not be read from FontLab's modern layer ({mo.get('error')}); the legacy "
                                 "layer was not read instead, because reading it can flatten a Power Brush glyph"))
    desc = {}
    try:
        _describe_modern_glyph(w, desc)
    except Exception as exc:
        desc["shapes_error"] = f"{type(exc).__name__}: {exc}"
    if desc.get("shapes_error") or not isinstance(desc.get("shapes"), list):
        elements = {"available": False, "wrapper": how, "error": desc.get("shapes_error", "no shapes list")}
    else:
        boxes_seconds = _add_component_boxes(w, font, desc["shapes"])
        elements = {"available": True, "wrapper": how, "source": "flGlyph(fgGlyph, fgFont)",
                    "layer_name": desc.get("layer_name"), "shapes": desc["shapes"]}
        if boxes_seconds is not None:
            elements["boxes_seconds"] = boxes_seconds
    return dict(base, node_count=mo["node_count"], contour_count=len(mo["contours"]), modern_outline=mo,
                elements=elements, component_count=state.get("components"), shape_count=state.get("shapes"),
                fontlab_ink_box=_modern_ink_box(layer))


def _modern_ink_box(layer):
    """v0.121. FontLab's own ink box of the modern layer: layer.inkBox() called once, with no argument, as a zero-argument
    getter (live 519-530: equal to the computed curve extents with the element transform applied, cubic, quadratic and
    Power Brush; no F1 after it). The QRectF's getters are passed on raw (Qt names its sides y-down, so "top" was the
    lower y): the server interprets them. A failed call is {"error"}; the outline is answered all the same."""
    v, err = _tl_call(lambda: layer.inkBox())
    return {"error": err} if err is not None else _rect_plain(v)


_MODERN_FIRST = True   # v0.120 (F1); the stub tests switch it off to test the legacy reader


def get_glyph_outline(name, route="body", modern=True):
    if _MODERN_FIRST and modern and route in ("body", "active"):
        first = _modern_only_outline(name, route)
        if first is not None:
            return first
    result = _get_glyph_outline_legacy(name, route, modern)
    if modern and isinstance(result, dict) and result.get("found") is True and route in ("body", "active"):
        mc = _reader_modern_check(name, result.get("node_count"), result.get("margins"))
        result["modern_check"] = mc
        if (mc.get("modern_layer") and isinstance(mc.get("modern_nodes"), int) and mc["modern_nodes"] > 0
                and (mc.get("agree") is False or mc.get("margins_agree") is False)):
            result["modern_outline"] = _read_modern_outline(name)
    return result


def _get_glyph_outline_legacy(name, route="body", modern=True):
    """One glyph's nodes grouped into contours. A new contour starts at each
    node whose kind is 'Move' (CONFIRMED in v0.24 on a Pen-tool glyph). Raw
    kind/smooth values are passed through untouched so unfamiliar structures
    (e.g. other drawing tools) are visible rather than normalised away.
    Cross-checks the grouped contour count against countContours()."""
    font = _open_font()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    if route not in _LAYER_ROUTES:
        return {"error": "layer must be one of: " + ", ".join(sorted(_LAYER_ROUTES))}
    layer = _get_layer_by_route(glyph, route)
    if layer is None:
        layer_count = _glyph_layer_count(glyph)
        if layer_count == 0 and route in ("body", "active"):
            # v0.46: FontLab holds NO layer at all for this glyph (real example: the empty .notdef of the test font),
            # i.e. no outline data: an empty glyph, not a read failure.
            return {"open": True, "found": True, "name": name, "layer_route": route, "layer_name": None,
                    "layer_count": 0, "node_count": 0, "contour_count_reported": 0, "contour_count_grouped": 0,
                    "contours": [], "component_count": _component_count(glyph)}
        return {"open": True, "found": True, "layer_route": route, "layer_count": layer_count,
                "layer_unreachable": True,
                "error": f"layer route {route!r} was None on every attempt"}
    try:
        layer_name = layer.name
    except Exception as exc:
        layer_name = f"<error: {exc}>"

    node_count = layer.countNodes()
    expected = layer.countContours()
    contours, current, notes = [], None, []
    for i in range(node_count):
        node = layer.findNode(i)
        if node is None:
            notes.append(f"node {i}: findNode returned None")
            continue
        entry = {"index": i}
        for attr in ("x", "y", "kind", "smooth"):
            try:
                val = getattr(node, attr)
            except Exception as exc:
                entry[attr] = f"<error: {exc}>"
                continue
            if callable(val):
                entry[attr] = "<callable>"
            elif isinstance(val, (str, int, float, bool)) or val is None:
                entry[attr] = val
            else:
                entry[attr] = f"<{type(val).__name__}>"
        is_move = str(entry.get("kind")).lower() == "move"
        if is_move or current is None:
            if not is_move:
                notes.append(f"node {i}: first node is not kind 'Move'; started a contour anyway")
            current = []
            contours.append(current)
        current.append(entry)

    result = {"open": True, "found": True, "name": name,
              "layer_route": route, "layer_name": layer_name,
              "node_count": node_count, "contour_count_reported": expected,
              "contour_count_grouped": len(contours),
              "contours": [{"node_count": len(c), "nodes": c} for c in contours]}
    if expected != len(contours):
        notes.append(f"grouped {len(contours)} contours but countContours() says {expected}")
    if node_count > 0:
        result["fontlab_bbox"] = _layer_bbox_dict(layer)
        result["elements"] = (_read_elements(glyph, font, layer_name, node_count) if modern
                              else {"available": False, "error": "disabled (modern=no)"})
    result["margins"] = _glyph_margins(glyph)
    result["component_count"] = _component_count(glyph)
    try:
        result["shape_count"] = int(layer.countShapes())
    except Exception:
        result["shape_count"] = None
    if notes:
        result["notes"] = notes
    return result


# Container attributes for which a bare len() is reported (never indexed,
# never iterated). len() has been safe on fgLayer and font.shapes; [] has not.
_LEN_OK = ("components", "layers", "anchors", "guides", "hints")
# Identity getters that are called (zero arguments) if they turn out to be methods.
_OBJ_CALL_OK = ("id", "index")


def debug_obj_probe(name, target, stage, attrs=None):
    """Staged probe of one native object belonging to a glyph.
    target: "glyph", "layer" (bodyLayer, after the warm-up), "glayer"
    (glyph.layer), "layermatrix" (bodyLayer.matrix) or "strictlayer"
    (glyph.bodyLayerStrict). These two layer routes have disagreed before (.name was
    'test_font' vs 'Body'), so both are exposed for comparison.
      dir:  public attribute NAMES only. No values read, nothing called.
      read: getattr() on exactly the names in `attrs`; callables are
            reported as '<callable>' and never invoked; only simple values
            (str/int/float/bool/None) are returned, anything else by type name.
    No [] / .get() / .keys() is used anywhere."""
    if target not in ("glyph", "layer", "glayer", "layermatrix", "strictlayer", "layerref"):
        return {"error": 'target must be "glyph", "layer", "glayer", "layermatrix", "strictlayer" or "layerref"'}
    if stage not in ("dir", "read"):
        return {"error": 'stage must be "dir" or "read"'}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    if target == "glyph":
        obj = glyph
    elif target == "layer":
        obj = _get_body_layer(glyph)
    elif target == "layermatrix":
        layer = _get_body_layer(glyph)
        if layer is None:
            return {"open": True, "found": True, "error": "bodyLayer was None on every attempt"}
        try:
            obj = layer.matrix
        except Exception as exc:
            return {"open": True, "found": True, "error": f"layer.matrix raised: {exc}"}
    elif target == "layerref":
        layer = _get_body_layer(glyph)
        if layer is None:
            return {"open": True, "found": True, "error": "bodyLayer was None on every attempt"}
        try:
            obj = layer.reference
        except Exception as exc:
            return {"open": True, "found": True, "error": f"layer.reference raised: {exc}"}
    elif target == "strictlayer":
        try:
            _ = glyph.layer   # same warm-up as everywhere else
            obj = glyph.bodyLayerStrict
        except Exception as exc:
            return {"open": True, "found": True, "error": f"bodyLayerStrict raised: {exc}"}
    else:
        try:
            _ = glyph.layer   # first touch is the warm-up; second read is the real value
            obj = glyph.layer
        except Exception as exc:
            return {"open": True, "found": True, "error": f"glyph.layer raised: {exc}"}
    result = {"open": True, "found": True, "name": name, "target": target,
              "stage": stage, "object_is_none": obj is None,
              "object_type": type(obj).__name__}
    if obj is None:
        return result
    if stage == "dir":
        result["public_names"] = [n for n in dir(obj) if not n.startswith("_")]
        return result
    values = {}
    for attr in (attrs or []):
        try:
            val = getattr(obj, attr)
        except Exception as exc:
            values[attr] = f"<error: {exc}>"
            continue
        if callable(val) and attr in _OBJ_CALL_OK:
            try:
                got = val()
                values[attr] = got if isinstance(got, (str, int, float, bool)) or got is None else f"<{type(got).__name__}>"
            except Exception as exc:
                values[attr] = f"<call raised: {exc}>"
        elif callable(val):
            values[attr] = "<callable>"
        elif isinstance(val, (str, int, float, bool)) or val is None:
            values[attr] = val
        elif attr in _LEN_OK:
            try:
                values[attr] = f"<{type(val).__name__} len={len(val)}>"
            except Exception as exc:
                values[attr] = f"<{type(val).__name__}; len() failed: {exc}>"
        else:
            values[attr] = f"<{type(val).__name__}>"
    result["values"] = values
    return result


def debug_layer_bbox(name, stage, attrs=None):
    """Staged probe of fgLayer.boundingBox(matrix), the documented-but-untried
    way to ask FontLab for its OWN bounding box of a layer. The matrix
    argument is the layer's own matrix (identity on every glyph checked so
    far), so no foreign object has to be constructed. Nothing is written.
      call: call boundingBox(layer.matrix); report ONLY the result's type.
      dir:  as call, plus the result's public attribute NAMES.
      measure: as call, plus left/right/top/bottom/width/height (zero-arg
            getters) and the ll/ur corner points, from a fixed whitelist.
      read: as call, plus getattr() on exactly the names in `attrs`
            (callables are never invoked; simple values only)."""
    if stage not in ("call", "dir", "read", "measure"):
        return {"error": 'stage must be "call", "dir", "read" or "measure"'}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    layer = _get_body_layer(glyph)
    if layer is None:
        return {"open": True, "found": True, "error": "bodyLayer was None on every attempt"}
    result = {"open": True, "found": True, "name": name, "stage": stage}
    try:
        rect = layer.boundingBox(layer.matrix)
    except Exception as exc:
        result["error"] = f"boundingBox raised: {exc}"
        return result
    result["rect_is_none"] = rect is None
    result["rect_type"] = type(rect).__name__
    if rect is None or stage == "call":
        return result
    if stage == "dir":
        result["public_names"] = [n for n in dir(rect) if not n.startswith("_")]
        return result
    if stage == "measure":
        # Zero-argument getters on an fgRect (left()/width()/... were used on
        # glyph.fbox in earlier sessions without incident) and the ll/ur
        # corner points. Fixed whitelist; each read is individually guarded.
        def _num(v):
            return v if isinstance(v, (int, float, bool, str)) or v is None else f"<{type(v).__name__}>"
        measured = {}
        for m in ("left", "right", "top", "bottom", "width", "height"):
            try:
                fn = getattr(rect, m)
                measured[m] = _num(fn() if callable(fn) else fn)
            except Exception as exc:
                measured[m] = f"<error: {exc}>"
        for corner in ("ll", "ur"):
            try:
                pt = getattr(rect, corner)
                measured[corner] = {"x": _num(pt.x), "y": _num(pt.y)}
            except Exception as exc:
                measured[corner] = f"<error: {exc}>"
        result["measured"] = measured
        return result
    values = {}
    for attr in (attrs or []):
        try:
            val = getattr(rect, attr)
        except Exception as exc:
            values[attr] = f"<error: {exc}>"
            continue
        if callable(val):
            values[attr] = "<callable>"
        elif isinstance(val, (str, int, float, bool)) or val is None:
            values[attr] = val
        else:
            values[attr] = f"<{type(val).__name__}>"
    result["values"] = values
    return result


class _RecordingPen:
    """Records what glyph.draw(pen) emits. Implements the fontTools segment-pen
    protocol AND the point-pen protocol, because it is not known which one
    FontLab's draw() uses. Points are stored as plain float tuples; native
    point objects are read through .x/.y only (never indexed)."""

    def __init__(self):
        self.ops = []
        self.dropped = 0

    @staticmethod
    def _pt(p):
        try:
            if isinstance(p, (tuple, list)) and len(p) >= 2:
                return (float(p[0]), float(p[1]))
            return (float(p.x), float(p.y))
        except Exception:
            return f"<{type(p).__name__}>"

    def _rec(self, op, *pts, extra=None):
        if len(self.ops) >= 5000:
            self.dropped += 1
            return
        self.ops.append((op, tuple(self._pt(p) for p in pts), extra))

    # segment-pen protocol
    def moveTo(self, pt): self._rec("moveTo", pt)
    def lineTo(self, pt): self._rec("lineTo", pt)
    def curveTo(self, *pts): self._rec("curveTo", *pts)
    def qCurveTo(self, *pts): self._rec("qCurveTo", *pts)
    def closePath(self): self._rec("closePath")
    def endPath(self): self._rec("endPath")
    def addComponent(self, name, transform=None): self._rec("addComponent", extra=str(name))
    # point-pen protocol
    def beginPath(self, *a, **k): self._rec("beginPath")
    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kw):
        self._rec("addPoint", pt, extra=str(segmentType))


def debug_draw_pen(name, limit=60):
    """Retest of glyph.draw(pen), listed in the notes as a dead end BEFORE the
    glyph.layer warm-up was discovered. If it now works, it delivers the
    glyph's FINAL geometry (element transformations included) with no
    calibration needed. Read-only: draw() only reads. Reports what the pen
    received; compare the first point with /glyph/outline for the same glyph."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    layer = _get_body_layer(glyph)   # the warm-up (touches glyph.layer first)
    pen = _RecordingPen()
    result = {"open": True, "found": True, "name": name,
              "layer_found": layer is not None}
    try:
        returned = glyph.draw(pen)
    except Exception as exc:
        result["error"] = f"glyph.draw(pen) raised: {exc}"
        return result
    result["draw_returned"] = (returned if isinstance(returned, (str, int, float, bool)) or returned is None
                               else f"<{type(returned).__name__}>")
    counts = {}
    pts = []
    for op, points, _extra in pen.ops:
        counts[op] = counts.get(op, 0) + 1
        pts.extend(p for p in points if isinstance(p, tuple))
    result["op_counts"] = counts
    result["op_total"] = len(pen.ops)
    if pen.dropped:
        result["ops_dropped_after_5000"] = pen.dropped
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        result["points_box"] = {"left": min(xs), "right": max(xs), "bottom": min(ys), "top": max(ys)}
    result["first_ops"] = [
        {"op": op, "points": [list(p) if isinstance(p, tuple) else p for p in points], "extra": extra}
        for op, points, extra in pen.ops[:max(0, int(limit))]]
    return result


def debug_class_probe(name, doc_chars=600, members=None, module=None, module_label="fontlab"):
    """Names + docstrings of ONE entry of the fontlab module (or, from /debug/moddir, of another
    ALREADY loaded module), e.g. flShape, flTransform, flGlyph, flLayer. Only dir() and __doc__ are
    read: nothing is constructed, called or changed. The entry must exist in dir(module), so no
    arbitrary attribute path can be requested."""
    import re as _re
    import sys as _sys
    if not name or not _re.match(r"^[A-Za-z][A-Za-z0-9_<>]*$", name):
        return {"error": "name must look like a plain identifier, e.g. flShape"}
    mod = module if module is not None else (_sys.modules.get("fontlab") or fl)
    if name not in dir(mod):
        return {"error": f"{name!r} is not a name in the {module_label} module"}
    try:
        obj = getattr(mod, name)
    except Exception as exc:
        return {"error": f"getattr({name!r}) raised: {exc}"}

    def _doc(o):
        try:
            d = getattr(o, "__doc__", None)
        except Exception as exc:
            return f"<error: {exc}>"
        return d[:doc_chars] if isinstance(d, str) else None

    result = {"name": name, "type": type(obj).__name__,
              "public_names": [n for n in dir(obj) if not n.startswith("_")],
              "doc": _doc(obj)}
    try:
        init = getattr(obj, "__init__", None)
        result["init_doc"] = _doc(init) if init is not None else None
    except Exception as exc:
        result["init_doc"] = f"<error: {exc}>"
    if members:
        wanted = [m.strip() for m in members.split(",") if m.strip()]
        if len(wanted) > 12:
            return {"error": "members: at most 12 names"}
        public = set(result["public_names"])
        docs = {}
        for m in wanted:
            if not _re.match(r"^[A-Za-z][A-Za-z0-9_]*$", m):
                docs[m] = "<refused: not a plain identifier>"
            elif m not in public:
                docs[m] = "<not a public member of this class>"
            else:
                try:
                    docs[m] = _doc(getattr(obj, m))
                except Exception as exc:
                    docs[m] = f"<error: {exc}>"
        result["member_docs"] = docs
    return result


# --- /debug/walk -----------------------------------------------------------
# Follows a dotted path from fontlab.CurrentGlyph() through the modern API.
# Safety rules (all enforced in code, not by convention):
#   * the path MUST start with "CurrentGlyph()" (legacy fgGlyph of the glyph open
#     in the editor) or with "fl" (the module's own `fl` attribute, the modern
#     workspace object); starting points only READ, nothing is selected,
#     switched or changed;
#   * attribute names may not start with an underscore;
#   * a "()" call is ONLY allowed for names in _WALK_CALL_OK: zero-argument,
#     read-only getters. Everything else (set*, add*, remove*, apply*, clone,
#     update, release, ...) is refused;
#   * "[N]" indexing is ONLY allowed on a real Python list or tuple, never on
#     a native FontLab object (the hard crash rule from v0.12/v0.20).
_WALK_CALL_OK = frozenset({
    "CurrentGlyph", "shapesCount", "componentsCount", "nodesCount", "contoursCount",
    "getActiveShape", "getShapes", "isComponent", "isComposite", "isEmpty", "hasBody",
    "hasShape", "hasComponents", "hasContours", "isBodyLayer", "isMasterLayer",
    "isVisible", "isActive", "isLocked", "instanceType", "getProperties",
    "instance", "currentGlyph", "currentPackage", "glyphsCount",
    # navigation getters on the *Info wrappers and modern objects (read-only)
    "glyph", "layer", "shape", "glyphInfo", "bodyLayer", "activeLayer", "transform",
    "toGlyphTransform", "toCanvasTransform", "compositesTransform", "shapes",
    # pure getters of a QTransform-like value object (3x3 matrix); read-only
    "m11", "m12", "m13", "m21", "m22", "m23", "m31", "m32", "m33", "dx", "dy",
    "determinant", "isIdentity", "isAffine", "isScaling", "isRotating", "isTranslating", "type",
    # identity getters (read-only)
    "id", "fgGlyphId", "refCnt", "isValid", "isNull", "isPresent", "isReleased", "index",
})
# One-plain-name-argument read-only getters (the argument must match _WALK_ARG_RE).
_WALK_ARG_OK = frozenset({"getProperty", "getPropertyFloat", "getPropertyInt"})
_WALK_ARG_RE = r"^[A-Za-z0-9_.]{1,40}$"
_WALK_MAX_STEPS = 8


def _walk_value(val):
    def simple(v):
        return isinstance(v, (str, int, float, bool)) or v is None
    if simple(val):
        return val
    if type(val) in (list, tuple):
        if len(val) <= 80 and all(simple(v) for v in val):
            return list(val)
        return f"<{type(val).__name__} len={len(val)}>"
    if type(val) is dict:
        if len(val) <= 80 and all(isinstance(k, str) and simple(v) for k, v in val.items()):
            return dict(val)
        return f"<dict len={len(val)}>"
    return f"<{type(val).__name__}>"


def debug_walk(path, stage, attrs=None):
    import re as _re
    import sys as _sys
    if stage not in ("dir", "read"):
        return {"error": 'stage must be "dir" or "read"'}
    tokens = [t.strip() for t in (path or "").split(".") if t.strip()]
    if not tokens or tokens[0] not in ("CurrentGlyph()", "fl", "flWorkspace"):
        return {"error": 'path must start with "CurrentGlyph()", "fl" or "flWorkspace"'}
    if len(tokens) > _WALK_MAX_STEPS:
        return {"error": f"path too long (max {_WALK_MAX_STEPS} steps)"}
    mod = _sys.modules.get("fontlab") or fl
    pat = _re.compile(r"^([A-Za-z][A-Za-z0-9_]*)(\(([A-Za-z0-9_.]*)\))?(?:\[(\d{1,3})\])?$")
    trace = []
    try:
        obj = (mod.CurrentGlyph() if tokens[0] == "CurrentGlyph()"
               else getattr(mod, "fl") if tokens[0] == "fl" else getattr(mod, "flWorkspace"))
    except Exception as exc:
        return {"error": f"root {tokens[0]!r} failed: {exc}"}
    trace.append({"step": tokens[0], "type": type(obj).__name__, "is_none": obj is None})
    for tok in tokens[1:]:
        if obj is None:
            return {"error": f"cannot continue: the previous step was None", "trace": trace}
        m = pat.match(tok)
        if not m:
            return {"error": f"bad path step {tok!r}", "trace": trace}
        name, has_paren, arg, idx = m.group(1), m.group(2), m.group(3), m.group(4)
        try:
            obj = getattr(obj, name)
        except Exception as exc:
            return {"error": f"attribute {name!r} failed: {exc}", "trace": trace}
        if has_paren and arg:
            # single plain-name argument: only the read-only property getters
            if name not in _WALK_ARG_OK or not _re.match(_WALK_ARG_RE, arg):
                return {"error": f"call {name}({arg}) is not on the read-only whitelist", "trace": trace}
            if not callable(obj):
                return {"error": f"{name} is not callable", "trace": trace}
            try:
                obj = obj(arg)
            except Exception as exc:
                return {"error": f"{name}({arg}) raised: {exc}", "trace": trace}
        elif has_paren:
            if name not in _WALK_CALL_OK:
                return {"error": f"call {name}() is not on the read-only whitelist", "trace": trace}
            if not callable(obj):
                return {"error": f"{name} is not callable", "trace": trace}
            try:
                obj = obj()
            except Exception as exc:
                return {"error": f"{name}() raised: {exc}", "trace": trace}
        elif name in _WALK_CALL_OK and callable(obj):
            # whitelisted zero-arg getter named without "()": call it anyway
            # (some of these are properties, some methods; both read the same thing)
            try:
                obj = obj()
            except Exception as exc:
                return {"error": f"{name}() raised: {exc}", "trace": trace}
        if idx is not None:
            if type(obj) not in (list, tuple):
                return {"error": f"[{idx}] refused: {name} is a {type(obj).__name__}, not a plain list/tuple "
                                 "(indexing native objects can crash FontLab)", "trace": trace}
            i = int(idx)
            if i >= len(obj):
                return {"error": f"[{i}] out of range (len {len(obj)})", "trace": trace}
            obj = obj[i]
        trace.append({"step": tok, "type": type(obj).__name__, "is_none": obj is None})

    result = {"stage": stage, "path": path, "trace": trace,
              "final_type": type(obj).__name__, "final_is_none": obj is None}
    if obj is None:
        return result
    if stage == "dir":
        result["public_names"] = [n for n in dir(obj) if not n.startswith("_")]
        return result
    result["final_value"] = _walk_value(obj)
    values = {}
    for attr_spec in (attrs or []):
        am = _re.match(r"^([A-Za-z][A-Za-z0-9_]*)(?:\(([A-Za-z0-9_.]+)\))?$", attr_spec)
        if not am:
            values[attr_spec] = "<refused: bad attribute name>"
            continue
        attr, aarg = am.group(1), am.group(2)
        try:
            val = getattr(obj, attr)
        except Exception as exc:
            values[attr_spec] = f"<error: {exc}>"
            continue
        if aarg is not None:
            if attr not in _WALK_ARG_OK or not _re.match(_WALK_ARG_RE, aarg) or not callable(val):
                values[attr_spec] = "<refused: not an allowed one-argument getter>"
                continue
            try:
                values[attr_spec] = _walk_value(val(aarg))
            except Exception as exc:
                values[attr_spec] = f"<call raised: {exc}>"
            continue
        attr_key = attr_spec
        if callable(val):
            if attr in _WALK_CALL_OK:
                try:
                    values[attr_key] = _walk_value(val())
                except Exception as exc:
                    values[attr_key] = f"<call raised: {exc}>"
            else:
                values[attr_key] = "<callable (not on whitelist, not called)>"
        else:
            values[attr_key] = _walk_value(val)
    result["values"] = values
    return result


def _legacy_current_name():
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    try:
        g = mod.CurrentGlyph()
        return None if g is None else str(g.name)
    except Exception as exc:
        return f"<error: {exc}>"


def _describe_modern_glyph(g, out):
    """Fill `out` with the modern glyph's name, active layer name and, for every
    shape in layer.shapes (a real Python list), type, contour count and QTransform
    entries. Read-only. May raise; callers catch."""
    out["modern_glyph_name"] = str(g.name)
    layer = g.activeLayer
    out["layer_name"] = str(layer.name)
    try:
        _n = layer.nodesCount
        out["layer_nodes_count"] = int(_n() if callable(_n) else _n)
    except Exception:
        out["layer_nodes_count"] = None
    shapes = layer.shapes
    if type(shapes) is not list:
        out["shapes_error"] = f"layer.shapes is a {type(shapes).__name__}, not a plain list"
        return out
    out["shape_count"] = len(shapes)
    out["shapes"] = []
    for sh in shapes:
        entry = {"shape_type": None, "contours": None, "is_component": None, "is_composite": None,
                 "matrix": None}
        def _get(obj, attr):
            v = getattr(obj, attr)
            return v() if callable(v) else v
        for key, attr in (("shape_type", "shapeType"), ("contours", "contoursCount"),
                          ("is_component", "isComponent"), ("is_composite", "isComposite")):
            try:
                v = _get(sh, attr)
                entry[key] = v if isinstance(v, (int, float, bool)) or v is None else str(v)
            except Exception as exc:
                entry[key] = f"<error: {exc}>"
        if entry["is_component"] is True:           # v0.128: the component's source (live 609-611); a plain shape is not asked
            try:
                sd = sh.shapeData
                for key, attr in (("component_glyph", "componentGlyph"), ("component_layer", "componentLayer")):
                    v = _get(sd, attr)
                    if not isinstance(v, str) or (key == "component_glyph" and not v):
                        raise ValueError(f"{attr} read {v!r}")
                    entry[key] = v
            except Exception as exc:
                entry["component_error"] = f"{type(exc).__name__}: {exc}"
        try:
            tr = sh.transform
            m = {}
            for a in ("m11", "m12", "m21", "m22", "dx", "dy"):
                v = _get(tr, a)
                m[a] = float(v)
            try:
                m["isIdentity"] = bool(_get(tr, "isIdentity"))
            except Exception:
                pass
            entry["matrix"] = m
        except Exception as exc:
            entry["matrix_error"] = str(exc)
        out["shapes"].append(entry)


def _read_modern_shapes():
    """Read the modern view of the editor's CURRENT glyph: name, active layer
    name and, for every shape in layer.shapes (a real Python list), its type,
    contour count and QTransform entries. Read-only. Never raises."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    out = {}
    try:
        info = mod.flWorkspace.instance().currentGlyph
        g = info.glyph
        _describe_modern_glyph(g, out)
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def debug_set_current(name, go, phase="all"):
    """EXPERIMENT. Switch the editor's current glyph to `name`, read its
    shapes' transforms, and switch back to the glyph that was current. The
    only thing changed is which glyph FontLab displays (the same as clicking a
    glyph tab). Always attempts the restore, even if reading fails."""
    import sys as _sys
    if go != "yes":
        return {"error": "this experiment switches the glyph shown in FontLab's editor (and switches back). "
                         "Add &go=yes to run it."}
    if phase not in ("all", "set"):
        return {"error": 'phase must be "all" or "set"'}
    mod = _sys.modules.get("fontlab") or fl
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    target = _find_glyph(font, name)
    if target is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    result = {"open": True, "found": True, "name": name, "phase": phase}
    if phase == "set":
        # Switch ONLY and return at once, so FontLab's event loop can run before the next request.
        result["legacy_current_before"] = _legacy_current_name()
        try:
            mod.SetCurrentGlyph(target)
            result["set_current_called"] = True
        except Exception as exc:
            result["set_current_called"] = False
            result["set_current_error"] = f"{type(exc).__name__}: {exc}"
        result["legacy_current_after_in_same_request"] = _legacy_current_name()
        result["note"] = ("Switch requested; NOT restored by this request. Read the result with "
                          "/debug/currentshapes, and switch back with another phase=set request.")
        return result
    try:
        orig = mod.CurrentGlyph()
    except Exception as exc:
        orig = None
        result["original_error"] = str(exc)
    try:
        result["original_name"] = None if orig is None else str(orig.name)
    except Exception as exc:
        result["original_name"] = f"<error: {exc}>"
    result["before_switch"] = _read_modern_shapes()
    try:
        try:
            mod.SetCurrentGlyph(target)
            result["set_current_called"] = True
        except Exception as exc:
            result["set_current_called"] = False
            result["set_current_error"] = f"{type(exc).__name__}: {exc}"
        result["after_switch"] = _read_modern_shapes()
        result["legacy_current_after_switch"] = _legacy_current_name()
    finally:
        if orig is not None:
            try:
                mod.SetCurrentGlyph(orig)
                result["restore_called"] = True
            except Exception as exc:
                result["restore_called"] = False
                result["restore_error"] = f"{type(exc).__name__}: {exc}"
            after = _read_modern_shapes()
            result["after_restore_name"] = after.get("modern_glyph_name")
            result["restored_ok"] = after.get("modern_glyph_name") == result["original_name"]
        else:
            result["restore_called"] = False
            result["restore_note"] = "no original glyph was current, so nothing to restore"
    return result


# One modern flGlyph wrapper per legacy glyph id, kept alive on purpose: each construction leaks one native reference (mental-model/topics/reading.md, section 6).
_MODERN_CACHE = {}
_MODERN_CACHE_FONT = [None]


def _call0(obj, attr):
    v = getattr(obj, attr)
    return v() if callable(v) else v


def _modern_wrapper(glyph, font):
    """Return (flGlyph wrapper, "cached"|"built") for a legacy glyph, or raise
    RuntimeError(reason). A cached wrapper is validated (name, fgGlyphId, isValid)
    before every reuse and rebuilt if anything disagrees."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    cls = getattr(mod, "flGlyph", None)
    if cls is None:
        raise RuntimeError("the fontlab module has no flGlyph class")
    try:
        lid = int(_call0(glyph, "id"))
    except Exception as exc:
        raise RuntimeError(f"legacy glyph id unreadable: {exc}")
    gname = str(glyph.name)
    try:
        fkey = str(getattr(font, "path", ""))
    except Exception:
        fkey = ""
    if _MODERN_CACHE_FONT[0] != fkey:           # another font: ids are not comparable any more
        _MODERN_CACHE.clear()
        _MODERN_CACHE_FONT[0] = fkey
    w = _MODERN_CACHE.get(lid)
    if w is not None:
        ok = False
        try:
            ok = str(w.name) == gname and int(_call0(w, "fgGlyphId")) == lid
            if ok:
                try:
                    ok = bool(_call0(w, "isValid"))
                except Exception:
                    pass                        # no isValid on this object: name + id agreed
        except Exception:
            ok = False
        if ok:
            return w, "cached"
        _MODERN_CACHE.pop(lid, None)
    w = cls(glyph, font)
    try:
        if str(w.name) != gname or int(_call0(w, "fgGlyphId")) != lid:
            raise RuntimeError("the built glyph does not match the legacy glyph (name / fgGlyphId)")
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"the built glyph could not be read: {exc}")
    _MODERN_CACHE[lid] = w
    return w, "built"


_TRYADVANCEWIDTH_MAX = 10
_TRYADVANCEWIDTH = {"calls": 0}


def debug_try_advance_width(name, stage, go):
    """Names-only inspection, then one gated read of flGlyph.advanceWidth."""
    import math as _math

    result = {"name": name, "stage": stage, "call": "flGlyph.advanceWidth", "calls_so_far": _TRYADVANCEWIDTH["calls"],
              "max_calls": _TRYADVANCEWIDTH_MAX}
    if not isinstance(name, str) or not name or len(name) > 40 or not name.startswith("tri") or not all(
            ch.isascii() and (ch.isalnum() or ch in "._-") for ch in name):
        return dict(result, refused=True, error="name must be 1 to 40 ASCII letters, digits, dot, underscore or hyphen, starting with tri")
    if stage not in ("names", "read"):
        return dict(result, error="stage must be names or read")
    if stage == "read" and go != "yes":
        return dict(result, error="stage=read calls flGlyph.advanceWidth once; add &go=yes to run it")

    font = _open_font()
    if font is None:
        return dict(result, refused=True, open=False, error="no font open")
    if _REQUEST_FONT.get("count") != 1 or type(_REQUEST_FONT.get("count")) is not int:
        return dict(result, refused=True, open=True, font_count=_REQUEST_FONT.get("count"),
                    error="requires exactly one font counted by CountFonts()")

    try:
        glyphs_before = font.glyphs
        count_before = len(glyphs_before)
    except Exception as exc:
        return dict(result, refused=True, open=True, error=f"glyph count before read failed: {type(exc).__name__}: {exc}")
    try:
        glyph = next((item for item in glyphs_before if str(item.name) == name), None)
    except Exception as exc:
        return dict(result, refused=True, open=True, glyph_count_before=count_before,
                    error=f"glyph lookup failed: {type(exc).__name__}: {exc}")
    if glyph is None:
        return dict(result, refused=True, open=True, found=False, glyph_count_before=count_before,
                    error="no glyph with that name")
    try:
        wrapper, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return dict(result, refused=True, open=True, found=True, glyph_count_before=count_before,
                    error=f"modern wrapper failed: {type(exc).__name__}: {exc}")

    if stage == "names":
        try:
            members = sorted(set(dir(wrapper)))
        except Exception as exc:
            return dict(result, open=True, found=True, wrapper=how, glyph_count_before=count_before,
                        error=f"member names failed: {type(exc).__name__}: {exc}")
        try:
            count_after = len(font.glyphs)
        except Exception:
            count_after = None
        return dict(result, open=True, found=True, wrapper=how, member_names=members,
                    advance_width_listed="advanceWidth" in members, read_performed=False,
                    glyph_count_before=count_before, glyph_count_after=count_after,
                    side_effect_detected=None if count_after is None else count_after != count_before)

    if _TRYADVANCEWIDTH["calls"] >= _TRYADVANCEWIDTH_MAX:
        return dict(result, refused=True, open=True, found=True, wrapper=how, glyph_count_before=count_before,
                    error="per-listener-run call limit reached")
    _TRYADVANCEWIDTH["calls"] += 1  # counted before the one target-property read
    result["calls_so_far"] = _TRYADVANCEWIDTH["calls"]
    result["read_performed"] = True
    try:
        value = wrapper.advanceWidth  # exactly one read of the target property
        if type(value) not in (int, float) or isinstance(value, bool) or not _math.isfinite(value):
            result["call_error"] = "advanceWidth did not return a finite plain number"
        else:
            result["advance_width"] = value
    except Exception as exc:
        result["call_error"] = f"{type(exc).__name__}: {exc}"
    try:
        count_after = len(font.glyphs)
    except Exception:
        count_after = None
    result.update(open=True, found=True, wrapper=how, glyph_count_before=count_before, glyph_count_after=count_after,
                  side_effect_detected=None if count_after is None else count_after != count_before)
    return result


# /debug/trydialogtimeout (v0.201) - RESEARCH, UI ONLY: can a dialog of this listener close itself after N seconds while its
# exec_() waits? Option C of the client time-limit research (TO 1577-1582, TO2 1583-1587): a dialog that outlives an AI app's
# time limit is answered later without anyone being told. No FontLab font call at all. how=slot connects a single-shot QTimer
# owned by the dialog straight to the dialog's reject() slot (a pure Qt connection; 1588: QTimer.connect(signal, receiver, slot,
# type)); how=python connects it to a Python function that notes the firing and calls reject(). Qt does not fire a timer again
# while its own handler still runs, which is why the poll timer serves nothing during a dialog; a separate timer may fire.
# The dialog is the QMessageBox the product dialogs use (1589: PythonQt.QtGui). Gated by go=yes; 3 to 50 seconds; 10 per
# listener run, counted before the dialog.
_TRYDIALOGTIMEOUT_MAX = 10
_TRYDIALOGTIMEOUT = {"calls": 0}
_TRYDIALOGTIMEOUT_TITLE = "Glyphbridge test: self-closing question"


def debug_try_dialog_timeout(how, seconds, go, countdown=""):
    """Show ONE test Yes/No dialog that a QTimer closes after `seconds` unless the person answers first. No font is touched.
    countdown=yes (v0.202): a second timer owned by the dialog relabels the No button "No (N)" once a second through a
    Python function; it is visual only: the closing never depends on it, and a countdown that fails is reported."""
    result = {"how": how, "seconds": seconds, "call": "QMessageBox.exec_() with a single-shot QTimer owned by the dialog",
              "calls_so_far": _TRYDIALOGTIMEOUT["calls"], "max_calls": _TRYDIALOGTIMEOUT_MAX, "font_touched": False,
              "dialog_started": False, "countdown": countdown == "yes"}
    if how not in ("slot", "python"):
        return dict(result, error="how must be slot or python")
    if countdown not in ("", "no", "yes"):
        return dict(result, error="countdown must be yes or no")
    if not isinstance(seconds, str) or not (1 <= len(seconds) <= 2 and seconds.isascii() and seconds.isdigit()) \
            or not 3 <= int(seconds) <= 50:
        return dict(result, error="seconds must be a whole number from 3 to 50")
    secs = int(seconds)
    result["seconds"] = secs
    if go != "yes":
        return dict(result, plan=f"one test Yes/No dialog (default No) that closes by itself after {secs} s through how={how}"
                                 + ("; the No button counts down once a second" if countdown == "yes" else "")
                                 + "; no font is touched; add &go=yes to show it")
    if _TRYDIALOGTIMEOUT["calls"] >= _TRYDIALOGTIMEOUT_MAX:
        return dict(result, refused=True,
                    error=f"the {_TRYDIALOGTIMEOUT_MAX} calls of this listener run are used up; restart the listener for more")
    _TRYDIALOGTIMEOUT["calls"] += 1  # counted before the dialog
    result["calls_so_far"] = _TRYDIALOGTIMEOUT["calls"]
    text = (f"Glyphbridge test (listener probe): this question closes by itself in {secs} seconds.\n\n"
            "Nothing in any font changes, whatever you answer.")
    try:
        box = QMessageBox(QMessageBox.Question, _TRYDIALOGTIMEOUT_TITLE, text, QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)  # Enter / closing the dialog = No
        timer = QtCore.QTimer(box)            # owned by the dialog: it goes when the dialog goes
        timer.setSingleShot(True)
        timer.setInterval(secs * 1000)
    except Exception as exc:
        return dict(result, error=f"the dialog or its timer could not be made: {type(exc).__name__}: {exc}; no dialog was shown")
    fired = {"count": 0, "after_s": None}
    held = {"box": box, "started": None}  # emptied after the dialog, so the Python function keeps no dialog alive

    def _on_timeout():
        fired["count"] += 1
        if held["started"] is not None:
            fired["after_s"] = round(time.monotonic() - held["started"], 3)
        if held["box"] is not None:
            held["box"].reject()

    try:
        if how == "slot":
            connected = timer.connect("timeout()", box, "reject()")
        else:
            connected = timer.connect("timeout()", _on_timeout)
    except Exception as exc:
        held["box"] = None
        return dict(result, error=f"timer.connect failed: {type(exc).__name__}: {exc}; no dialog was shown")
    result["connected"] = connected if isinstance(connected, bool) else repr(connected)
    if connected is False:
        held["box"] = None
        return dict(result, error="timer.connect returned False; no dialog was shown, since nothing would close it")
    # v0.202: the countdown, visual only. A setup that fails leaves the dialog without it (countdown_error), never unshown.
    cd = {"ticks": 0, "last_label": None, "error": None}
    tick_timer = None

    def _on_tick():
        cd["ticks"] += 1
        remaining = secs - cd["ticks"]
        if remaining < 1 or held["box"] is None:
            return  # the closing timer ends the dialog at 0; no "No (0)"
        try:
            label = f"No ({remaining})"
            held["box"].button(QMessageBox.No).setText(label)
            cd["last_label"] = label
        except Exception as exc:
            if cd["error"] is None:
                cd["error"] = f"relabel at tick {cd['ticks']}: {type(exc).__name__}: {exc}"

    if countdown == "yes":
        try:
            tick_timer = QtCore.QTimer(box)  # owned by the dialog, like the closing timer
            tick_timer.setSingleShot(False)
            tick_timer.setInterval(1000)
            tick_connected = tick_timer.connect("timeout()", _on_tick)
            if tick_connected is False:
                raise RuntimeError("tick_timer.connect returned False")
            # the first label only once the countdown can run, so a failed setup never leaves a number standing
            first = f"No ({secs})"
            no_button = box.button(QMessageBox.No)
            if no_button is None:
                raise RuntimeError("button(QMessageBox.No) gave no button")
            no_button.setText(first)
            cd["last_label"] = first
        except Exception as exc:
            cd["error"] = f"countdown setup: {type(exc).__name__}: {exc}"
            tick_timer = None
    try:
        held["started"] = time.monotonic()
        timer.start()
        if tick_timer is not None:
            tick_timer.start()
        result["dialog_started"] = True
        answer = box.exec_()
        elapsed = time.monotonic() - held["started"]
    except Exception as exc:
        for t in (timer, tick_timer):
            try:
                if t is not None:
                    t.stop()
            except Exception:
                pass
        held["box"] = None
        return dict(result, error=f"the dialog failed: {type(exc).__name__}: {exc}")
    if tick_timer is not None:
        try:
            tick_timer.stop()
        except Exception as exc:
            if cd["error"] is None:
                cd["error"] = f"countdown stop: {type(exc).__name__}: {exc}"
    out = dict(result, elapsed_s=round(elapsed, 3), exec_result=answer if type(answer) is int else repr(answer),
               result_is_yes=answer == QMessageBox.Yes)
    try:
        out["timer_active_after"] = bool(timer.isActive())
        timer.stop()
    except Exception as exc:
        out["timer_stop_error"] = f"{type(exc).__name__}: {exc}"
    try:
        clicked = box.clickedButton()
        if clicked is None:
            out["clicked_button"] = None
        else:
            label = clicked.text  # a property in PythonQt, not a method (SC 1591, 1592); called only where it is one
            out["clicked_button"] = str(label() if callable(label) else label)
        out["closed_without_click"] = clicked is None
    except Exception as exc:
        out["clicked_button_error"] = f"{type(exc).__name__}: {exc}"
    try:
        code = box.result()
        out["dialog_result"] = code if type(code) is int else repr(code)
    except Exception as exc:
        out["dialog_result_error"] = f"{type(exc).__name__}: {exc}"
    if how == "python":
        out.update(timer_fired=fired["count"], timer_fired_after_s=fired["after_s"])
    if countdown == "yes":
        out.update(countdown_ticks=cd["ticks"], countdown_last_label=cd["last_label"], countdown_error=cd["error"])
        try:
            label = box.button(QMessageBox.No).text
            out["countdown_label_after"] = str(label() if callable(label) else label)
        except Exception as exc:
            out["countdown_label_after_error"] = f"{type(exc).__name__}: {exc}"
    held["box"] = None
    return out


def _read_elements(glyph, font, legacy_layer_name, legacy_node_count):
    """The true transform of every shape of this glyph. Never raises: problems come
    back as {"available": False, "error": ...} so the outline itself is unaffected."""
    try:
        w, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    desc = {}
    try:
        _describe_modern_glyph(w, desc)
    except Exception as exc:
        return {"available": False, "wrapper": how, "error": f"{type(exc).__name__}: {exc}"}
    if desc.get("shapes_error") or not isinstance(desc.get("shapes"), list):
        return {"available": False, "wrapper": how, "error": desc.get("shapes_error", "no shapes list")}
    if desc.get("layer_name") != legacy_layer_name or desc.get("layer_nodes_count") != legacy_node_count:
        return {"available": False, "wrapper": how,
                "error": (f"the modern active layer ({desc.get('layer_name')!r}, {desc.get('layer_nodes_count')} nodes) "
                          f"is not the legacy layer that was read ({legacy_layer_name!r}, {legacy_node_count} nodes)")}
    return {"available": True, "wrapper": how, "source": "flGlyph(fgGlyph, fgFont)",
            "layer_name": desc["layer_name"], "shapes": desc["shapes"]}


def debug_build_glyph(name, go, reads="full", gc_mode="no"):
    """EXPERIMENT. Build fontlab.flGlyph(fgGlyph, fgFont) for the named glyph
    and read it. Constructs ONE native wrapper object; afterwards only reads.
    Reports the built glyph's ids next to the legacy id and the live current
    glyph's modern id, so it is visible whether this is the same object."""
    import sys as _sys
    if go != "yes":
        return {"error": "this experiment constructs a native flGlyph object (read-only afterwards). "
                         "Add &go=yes to run it."}
    if reads not in ("none", "layer", "shapes", "full"):
        return {"error": 'reads must be "none", "layer", "shapes" or "full"'}
    if gc_mode not in ("yes", "no"):
        return {"error": 'gc must be "yes" or "no"'}
    import gc as _gc
    mod = _sys.modules.get("fontlab") or fl
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    cls = getattr(mod, "flGlyph", None)
    if cls is None:
        return {"open": True, "found": True, "error": "the fontlab module has no flGlyph class"}

    def _val(obj, attr):
        v = getattr(obj, attr)
        v = v() if callable(v) else v
        return v if isinstance(v, (str, int, float, bool)) or v is None else f"<{type(v).__name__}>"

    result = {"open": True, "found": True, "name": name}
    try:
        result["legacy_id"] = _val(glyph, "id")
    except Exception as exc:
        result["legacy_id"] = f"<error: {exc}>"
    try:
        info = mod.flWorkspace.instance().currentGlyph
        result["live_current_glyph_name"] = str(info.glyph.name)
        result["live_current_modern_id"] = _val(info.glyph, "id")
    except Exception as exc:
        result["live_current_error"] = f"{type(exc).__name__}: {exc}"
    result["reads"] = reads
    result["gc"] = gc_mode
    if gc_mode == "yes":
        result["gc_collected_before"] = _gc.collect()
    try:
        built = cls(glyph, font)
    except Exception as exc:
        result["construct_error"] = f"{type(exc).__name__}: {exc}"
        return result
    result["built_type"] = type(built).__name__
    # refCnt FIRST: sampled right after construction and before any other access, so a rise from one
    # call to the next is caused by what the PREVIOUS call did.
    for key, attr in (("built_refCnt", "refCnt"), ("built_name", "name"), ("built_fgGlyphId", "fgGlyphId"),
                      ("built_id", "id"), ("built_nodesCount", "nodesCount")):
        try:
            result[key] = _val(built, attr)
        except Exception as exc:
            result[key] = f"<error: {exc}>"
    if "live_current_modern_id" in result and "built_id" in result:
        result["same_object_as_live_current"] = (
            result["live_current_glyph_name"] == name and result["built_id"] == result["live_current_modern_id"]
            if result.get("live_current_glyph_name") == name else None)
    desc = {}
    try:
        if reads == "layer":
            _l = built.activeLayer
            desc["layer_name"] = str(_l.name)
            del _l
        elif reads == "shapes":
            _l = built.activeLayer
            _sh = _l.shapes
            desc["shape_count"] = len(_sh) if type(_sh) is list else None
            del _sh, _l
        elif reads == "full":
            _describe_modern_glyph(built, desc)
    except Exception as exc:
        desc["error"] = f"{type(exc).__name__}: {exc}"
    result["built_glyph"] = desc
    del built
    if gc_mode == "yes":
        result["gc_collected_after"] = _gc.collect()
    return result


def debug_fl_dir(contains):
    """Names only: dir() of the `fl` object and of the fontlab module,
    optionally filtered by case-insensitive substrings. Nothing is read or
    called, so it cannot change anything."""
    import sys as _sys
    wanted = [c.lower() for c in (contains or []) if c]

    def pick(obj):
        names = [n for n in dir(obj) if not n.startswith("_")]
        if wanted:
            names = [n for n in names if any(w in n.lower() for w in wanted)]
        return names

    mod = _sys.modules.get("fontlab")
    result = {"fl_type": type(fl).__name__, "fl_names": pick(fl)}
    if mod is not None and mod is not fl:
        result["fontlab_module_names"] = pick(mod)
    result["filter"] = wanted
    return result


# --------------------------------------------------------------------------
# /debug/moddir (v0.98) - NAMES ONLY, in modules FontLab has ALREADY loaded (kerning research, test 177: fgKerningObjectPair is not
# a name of the fontlab module). Read-only, no go=yes needed:
#   ?contains=a,b,c                          names of loaded modules (keys of sys.modules) that contain a token; at most 100
#   ?module=M&contains=a,b,c                 public names of loaded module M that contain a token; at most 200
#   ?module=M&name=N[&members=x,y][&doc=600] type, public names and docstrings of entry N of module M (as /debug/classdir)
#   ?stage=kerntype                          type name and __module__ of the legacy font.kerning object (one-font gate)
# Never imported, constructed or called: a module that is not already in sys.modules is refused; only dir(), type(), __doc__ and
# getattr of a listed name are read. 1 to 3 tokens of a-z 0-9 _ . (case-insensitive); a whole module or the whole module list is
# never returned.
# --------------------------------------------------------------------------

_MODDIR_MAX_MODULES = 100
_MODDIR_MAX_NAMES = 200
_MODDIR_TOKEN_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_.")


def debug_mod_dir(module, name, contains, members, doc_chars, stage):
    import re as _re
    import sys as _sys
    if stage is not None and stage != "kerntype":
        return {"error": 'stage must be "kerntype" (or left out)'}
    if stage == "kerntype":
        if module is not None or name is not None or contains or members is not None:
            return {"error": "stage=kerntype takes no other parameters"}
        ws, pkg, why = _trysync_target(_sys.modules.get("fontlab") or fl)
        if ws is None:
            return {"stage": "kerntype", "error": why}
        font = fl.CurrentFont()
        if font is None:
            return {"open": False}
        try:
            kind = type(font.kerning)
        except Exception as exc:
            return {"stage": "kerntype", "error": f"font.kerning not reachable: {type(exc).__name__}: {exc}"}
        return {"stage": "kerntype", "type": kind.__name__, "module": getattr(kind, "__module__", None)}
    tokens = [t.lower() for t in contains]
    if len(tokens) > 3:
        return {"error": "contains: at most 3 tokens"}
    if any(ch not in _MODDIR_TOKEN_CHARS for t in tokens for ch in t):
        return {"error": "contains: tokens of A-Z a-z 0-9 _ . only"}
    if module is None:
        if name is not None or members is not None:
            return {"error": "name and members need module=M"}
        if not tokens:
            return {"error": "give contains=a,b,c: the probe never lists every loaded module"}
        found = sorted(k for k in list(_sys.modules) if isinstance(k, str) and any(t in k.lower() for t in tokens))
        return {"modules": found[:_MODDIR_MAX_MODULES], "count": len(found), "cut": len(found) > _MODDIR_MAX_MODULES, "filter": tokens}
    if len(module) > 64 or not _re.match(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*$", module):
        return {"error": "module must be a dotted name of plain identifiers, at most 64 characters"}
    mod = _sys.modules.get(module)
    if mod is None:
        return {"error": f"{module!r} is not a loaded module; this probe never imports anything"}
    if name is None:
        if members is not None:
            return {"error": "members need name=N"}
        if not tokens:
            return {"error": "give contains=a,b,c or name=N: the probe never lists a whole module"}
        names = sorted(n for n in dir(mod) if not n.startswith("_") and any(t in n.lower() for t in tokens))
        return {"module": module, "names": names[:_MODDIR_MAX_NAMES], "count": len(names), "cut": len(names) > _MODDIR_MAX_NAMES, "filter": tokens}
    if tokens:
        return {"error": "give either contains or name, not both"}
    result = debug_class_probe(name, doc_chars, members, module=mod, module_label=repr(module))
    result["module"] = module
    return result


# --------------------------------------------------------------------------
# /debug/fontdir (v0.90) - names-only probe of the FONT object (kerning research). Read-only, no go=yes needed:
#   stage=dir                 public attribute NAMES of the current font object. No value is read, nothing is called.
#   stage=sub&attr=NAME       ONE attribute of the font: NAME must be a plain identifier (no leading underscore) that appears in
#                             dir(font). The attribute is READ once (getattr). A plain value (text / number / bool / None) is
#                             returned; a callable is NEVER called (reported as callable, with the start of its docstring); any
#                             other native object is reported by type name, with len() when it has one, the start of its
#                             docstring and its public attribute NAMES. No [] / .get() / .keys(), no member of the sub-object read.
#   stage=member&attr=NAME&members=a,b,c   (v0.91) the sub-object of attribute NAME (it must be an OBJECT: not a plain value, not a
#                             callable) and up to 8 of ITS public members, each a plain identifier without a leading underscore that
#                             appears in dir(sub-object). Per member: type name; callable true / false (a callable is NEVER called);
#                             the start of its docstring; for a non-callable member also len() when it has one. No value is returned.
#   stage=memberdir&attr=NAME&members=m   (v0.115) ONE public member m of the sub-object of attribute NAME (an OBJECT, as for
#                             stage=member), one level deeper: its type name, the start of its docstring and, when it is an object,
#                             its public attribute NAMES. A plain value is not returned; a callable is NEVER called; no len(), no
#                             [] / .get() / .keys() / iteration on it (container calls on native objects need proof, FONTLAB-API-RULES
#                             §10). Asked for font.info.dict (an fgFontInfoDict): does FontLab mark which info fields were set?
#                             v0.116: m may be a dotted path of up to 3 steps (members=dict.flags). Each step is a public plain
#                             identifier found in dir() of the step before and is read once (getattr); a step that is a plain value
#                             or a callable (never called) ends the walk with an error naming it. path_types lists the type of every
#                             step before the last. The last step is reported as for a single name.
#   stage=keys&attr=NAME&members=PATH&go=yes   (v0.117) GATED. The same path rules as memberdir; the object at the end of the
#                             path must have a public, callable member keys, which is called ONCE without arguments, and only
#                             with go=yes (without it the reply only says what would be called). A plain list or tuple of text is
#                             returned (at most _FONTDIR_KEYS_MAX entries, with the full count); anything else by its type only,
#                             never iterated. has_key / value / asDict / del are never called. keys() on a native object is a
#                             container call that needs proof per object and call form (FONTLAB-API-RULES §10).
# "A font is open" uses CountFonts() when it is a plain int (0 = the placeholder fgFont of section 8k, reported as open false).
# --------------------------------------------------------------------------

_FONTDIR_STAGES = ("dir", "sub", "member", "memberdir", "keys")
_MEMBERDIR_MAX_STEPS = 3      # v0.116: longest dotted path of stage=memberdir
_FONTDIR_KEYS_MAX = 200       # v0.117: most keys returned by stage=keys


def debug_font_dir(stage="dir", attr=None, members=None, go=None):
    import re as _re
    if stage not in _FONTDIR_STAGES:
        return {"error": 'stage must be "dir", "sub", "member", "memberdir" or "keys"'}
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False, "count_fonts": 0, "note": "CountFonts() is 0: no font is open (CurrentFont() would only return a placeholder)"}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    public = [n for n in dir(font) if not n.startswith("_")]
    result = {"open": True, "count_fonts": count, "stage": stage, "font_type": type(font).__name__}
    if stage == "dir":
        result["public_names"] = public
        return result
    if not attr or not _re.match(r"^[A-Za-z][A-Za-z0-9_]*$", attr):
        return {"error": "stage=sub and stage=member need attr=<plain identifier without a leading underscore>"}
    if attr not in public:
        return {"error": f"{attr!r} is not a public attribute of the font object (run stage=dir first)"}
    result["attr"] = attr
    try:
        val = getattr(font, attr)
    except Exception as exc:
        result["error"] = f"getattr raised: {type(exc).__name__}: {exc}"
        return result

    def _doc(o):
        try:
            d = getattr(o, "__doc__", None)
        except Exception as exc:
            return f"<error: {exc}>"
        return d[:400] if isinstance(d, str) else None

    result["value_type"] = type(val).__name__
    if stage in ("memberdir", "keys"):
        if val is None or isinstance(val, (str, int, float, bool)) or callable(val):
            result["error"] = f"stage={stage} needs an attribute that is an object (use stage=sub first)"
            return result
        m = (members or "").strip()
        if not m or "," in m:
            result["error"] = f"stage={stage} needs members=<exactly one name, or a dotted path of up to {_MEMBERDIR_MAX_STEPS} names>"
            return result
        steps = tuple(s.strip() for s in m.split("."))
        last = len(steps) - 1
        if last >= _MEMBERDIR_MAX_STEPS:
            result["error"] = f"members: at most {_MEMBERDIR_MAX_STEPS} steps in a dotted path"
            return result
        for s in steps:
            if not _re.match(r"^[A-Za-z][A-Za-z0-9_]*$", s):
                result["error"] = f"{s!r} is not a plain identifier without a leading underscore"
                return result
        obj, walked, path_types = val, (), ()          # tuples only: nothing here may look like a call on a FontLab object
        for i, s in enumerate(steps):
            before = ".".join(walked)
            try:
                public = [n for n in dir(obj) if not n.startswith("_")]
            except Exception as exc:
                result["error"] = f"dir() of {before or 'the sub-object'} failed: {type(exc).__name__}: {exc}"
                return result
            if s not in public:
                result["error"] = f"{s!r} is not a public member of {before or 'this object (run stage=sub first)'}"
                return result
            result["member"] = ".".join(steps)
            walked = walked + (s,)
            try:
                obj = getattr(obj, s)
            except Exception as exc:
                where = "the member" if last == 0 else repr(".".join(walked))
                result["error"] = f"getattr of {where} raised: {type(exc).__name__}: {exc}"
                return result
            if i < last:
                path_types = path_types + (type(obj).__name__,)
                result["path_types"] = list(path_types)
                if obj is None or isinstance(obj, (str, int, float, bool)) or callable(obj):
                    kind = "a callable (never called)" if callable(obj) else "a plain value"
                    result["error"] = f"the path stops at {'.'.join(walked)!r}: it is {kind} of type {type(obj).__name__}"
                    return result
        mv = obj
        if stage == "keys":
            return _fontdir_keys(mv, result, go)
        result["member_type"] = type(mv).__name__
        result["member_doc"] = _doc(mv)
        if mv is None or isinstance(mv, (str, int, float, bool)):
            result["member_is_plain_value"] = True       # names only: the value itself is not returned
            return result
        if callable(mv):
            result["callable"] = True
            result["called"] = False
            return result
        try:
            result["public_names"] = [n for n in dir(mv) if not n.startswith("_")]
        except Exception as exc:
            result["public_names"] = f"<dir failed: {type(exc).__name__}: {exc}>"
        return result
    if stage == "member":
        if val is None or isinstance(val, (str, int, float, bool)) or callable(val):
            result["error"] = "stage=member needs an attribute that is an object (use stage=sub first)"
            return result
        wanted = [m.strip() for m in (members or "").split(",") if m.strip()]
        if not wanted:
            result["error"] = "stage=member needs members=<name>[,<name>...] (1 to 8 names)"
            return result
        if len(wanted) > 8:
            result["error"] = "members: at most 8 names"
            return result
        try:
            sub_public = [n for n in dir(val) if not n.startswith("_")]
        except Exception as exc:
            result["error"] = f"dir() of the sub-object failed: {type(exc).__name__}: {exc}"
            return result
        out = {}
        for m in wanted:
            if not _re.match(r"^[A-Za-z][A-Za-z0-9_]*$", m):
                out[m] = {"error": "not a plain identifier without a leading underscore"}
                continue
            if m not in sub_public:
                out[m] = {"error": "not a public member of this object"}
                continue
            try:
                mv = getattr(val, m)
            except Exception as exc:
                out[m] = {"error": f"getattr raised: {type(exc).__name__}: {exc}"}
                continue
            entry = {"type": type(mv).__name__}
            if callable(mv):
                entry["callable"] = True
                entry["called"] = False
            else:
                entry["callable"] = False
                try:
                    entry["len"] = len(mv)
                except Exception as exc:
                    entry["len"] = f"<no len: {type(exc).__name__}>"
            entry["doc"] = _doc(mv)
            out[m] = entry
        result["members"] = out
        return result
    if val is None or isinstance(val, (str, int, float, bool)):
        result["value"] = val
        return result
    if callable(val):
        result["callable"] = True
        result["called"] = False
        result["doc"] = _doc(val)
        return result
    try:
        result["len"] = len(val)
    except Exception as exc:
        result["len"] = f"<no len: {type(exc).__name__}>"
    result["doc"] = _doc(val)
    try:
        result["public_names"] = [n for n in dir(val) if not n.startswith("_")]
    except Exception as exc:
        result["public_names"] = f"<dir failed: {type(exc).__name__}: {exc}>"
    return result


def _fontdir_keys(obj, result, go):
    """stage=keys (v0.117): ONE call of obj.keys() at the end of a memberdir path, only with go=yes. Nothing else of obj is called."""
    result["member_type"] = type(obj).__name__
    if obj is None or isinstance(obj, (str, int, float, bool)) or callable(obj):
        result["error"] = "stage=keys needs an object at the end of the path (not a plain value, not a callable)"
        return result
    try:
        public = [n for n in dir(obj) if not n.startswith("_")]
    except Exception as exc:
        result["error"] = f"dir() of {result['member']} failed: {type(exc).__name__}: {exc}"
        return result
    if "keys" not in public:
        result["error"] = f"{result['member']} has no public member named keys"
        return result
    try:
        call = getattr(obj, "keys")
    except Exception as exc:
        result["error"] = f"getattr of keys raised: {type(exc).__name__}: {exc}"
        return result
    if not callable(call):
        result["error"] = f"{result['member']}.keys is not callable (type {type(call).__name__})"
        return result
    result["would_call"] = f"{result['member']}.keys()"
    if go != "yes":
        result["called"] = False
        result["note"] = "a container call on a native FontLab object (FONTLAB-API-RULES §10): add go=yes to call it once"
        return result
    try:
        got = call()
    except Exception as exc:
        result["called"] = True
        result["error"] = f"keys() raised: {type(exc).__name__}: {exc}"
        return result
    result["called"] = True
    result["result_type"] = type(got).__name__
    if type(got) in (list, tuple) and all(isinstance(k, str) for k in got):
        result["count"] = len(got)
        result["keys"] = [_plain_text(k) for i, k in enumerate(got) if i < _FONTDIR_KEYS_MAX]
        result["cut"] = len(got) > _FONTDIR_KEYS_MAX
    else:
        result["note"] = "the result is not a plain list or tuple of text: reported by its type only, not read"
    return result


# --------------------------------------------------------------------------
# /debug/tryfont (v0.83) - EXPERIMENT: make a NEW, EMPTY font through the modern API
# (the equivalent of File > New Font / Ctrl+N). Three stages, one variable each:
#   state     read-only
#   construct go=yes   ONE detached flPackage(); never attached here
#   attach    go=yes   ONE flWorkspace.instance().addPackage(<that package>)
#   construct_named&family=F&go=yes   v0.142 (P0.4): the same ONE flPackage(), then in the same request, before FontLab handles
#             its next event, the names Build Names gives (845, 849): tfn = F, ffn = F + " Regular", psn = F without spaces +
#             "-Regular", sgn = F, one assignment each, every name read back. It shares the once-per-run limit of construct.
#             v0.146: F is checked as /font/create checks it (_family_name_error): psn at most 63 characters, none of [](){}<>/%.
#             Reason: no call redrew the FONTS panel after a later rename (856-876), but it lists a font as it is when added (871).
#   construct_named&family=F&mark=yes&go=yes   v0.145: after the four names read back equal, ONE flItems.notifyChangesApplied(
#             'Glyphbridge test', <the package just made>, False) on that package object (not a "current package"), in the same request.
#             Reason: 912 and 913 showed that this mark brings FontLab's save question back for a font named through the API, but both
#             ran with exactly one font open; with several open, which font the mark lands on is untested. No mark when a name
#             assignment failed or did not read back, none without flItems; the once-per-run limit of construct covers it.
# Not called, ever, by this probe: createNewProject, closePackage, closeProject, saveProject, export*, release, remove.
# --------------------------------------------------------------------------

_TRYFONT_STAGES = ("state", "construct", "attach", "construct_named")
_TRYFONT = {"package": None, "constructed": False, "attached": False}
_TRYFONT_PKG_READS = ("name", "upm", "mastersCount", "defaultMaster", "glyphsCount", "isNull", "path", "fileName", "fgPackage")


def _tryfont_plain(value):
    """Plain values pass through; any native object is reported by its type name only."""
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return f"<{type(value).__name__}>"


def _tryfont_read(obj, attr):
    """ONE read of a named attribute (the names come from the fixed list above). A zero-argument callable is
    called once; a failure is reported as text, never raised."""
    try:
        value = getattr(obj, attr)
        if callable(value):
            value = value()
        return _tryfont_plain(value)
    except Exception as exc:
        return f"<error: {type(exc).__name__}: {exc}>"


def _tryfont_workspace_state(mod, pkg=None):
    """Read-only look at the legacy and the modern view of 'which fonts are open'. Since v0.111 it also reads the current
    package's path and fileName (T5: its name is empty, so it cannot be told from another package by name) and the type
    name of what packages() returns, which is never iterated or indexed (an unproven container call)."""
    out = {}
    try:
        out["CountFonts"] = _tryfont_plain(mod.CountFonts())
    except Exception as exc:
        out["CountFonts"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        font = mod.CurrentFont()
        if font is None:
            out["CurrentFont"] = None
        else:
            cur = {"type": type(font).__name__}
            try:
                cur["path"] = _tryfont_plain(font.path)
            except Exception as exc:
                cur["path"] = f"<error: {exc}>"
            try:
                cur["familyName"] = _tryfont_plain(font.info.familyName)
            except Exception as exc:
                cur["familyName"] = f"<error: {exc}>"
            try:
                cur["glyph_count"] = len(font.glyphs)
            except Exception as exc:
                cur["glyph_count"] = f"<error: {exc}>"
            out["CurrentFont"] = cur
    except Exception as exc:
        out["CurrentFont"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        ws = mod.flWorkspace.instance()
    except Exception as exc:
        out["workspace"] = f"<error: {type(exc).__name__}: {exc}>"
        return out
    out["workspace"] = "ok"
    try:
        packages = ws.packages()
        out["packages_type"] = type(packages).__name__
        out["packages_len"] = len(packages)
    except Exception as exc:
        out["packages_len"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        cp = ws.currentPackage
        if callable(cp):
            cp = cp()
        if cp is None:
            out["currentPackage"] = None
        else:
            out["currentPackage"] = {"type": type(cp).__name__, "isNull": _tryfont_read(cp, "isNull"),
                                     "name": _tryfont_read(cp, "name"), "path": _tryfont_read(cp, "path"),
                                     "fileName": _tryfont_read(cp, "fileName")}
    except Exception as exc:
        out["currentPackage"] = f"<error: {type(exc).__name__}: {exc}>"
    if pkg is not None:
        try:
            out["hasPackage"] = _tryfont_plain(ws.hasPackage(pkg))
        except Exception as exc:
            out["hasPackage"] = f"<error: {type(exc).__name__}: {exc}>"
    return out


def _tryfont_built_names(family):
    """v0.142: the names Font Info's Build Names gives for family + style Regular (845, 849), in the order they are set."""
    return (("tfn", family), ("ffn", family + " Regular"), ("psn", family.replace(" ", "") + "-Regular"), ("sgn", family))


def _tryfont_mark(mod, pkg, all_equal):
    """v0.145: ONE flItems.notifyChangesApplied(title, pkg, False) on the package just made, or why it was not made. Never raises."""
    if not all_equal:
        return {"requested": True, "called": False, "skipped": "a name assignment failed or did not read back equal"}
    marker = getattr(mod, "flItems", None)
    if marker is None:
        return {"requested": True, "called": False, "skipped": "the fontlab module has no flItems"}
    out = {"requested": True, "call": f"flItems.notifyChangesApplied({_TRYNOTIFY_TITLE!r}, <flPackage>, False)", "called": True}
    try:
        marker.notifyChangesApplied(_TRYNOTIFY_TITLE, pkg, False)
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def debug_try_font(stage, go, family="", mark=""):
    import sys as _sys
    if stage not in _TRYFONT_STAGES:
        return {"error": "stage must be one of: " + ", ".join(_TRYFONT_STAGES)}
    if mark not in ("", "yes"):
        return {"error": "mark must be yes or empty; nothing was constructed"}
    mod = _sys.modules.get("fontlab") or fl
    flags = {"constructed": _TRYFONT["constructed"], "attached": _TRYFONT["attached"]}
    if stage == "state":
        return dict(flags, stage="state", workspace_state=_tryfont_workspace_state(mod, _TRYFONT["package"]))
    if stage == "construct_named":
        why = _family_name_error(family)      # v0.146: the check of /font/create (the old 58-character limit let psn reach 66)
        if why is not None:
            return {"error": "family: " + why + "; nothing was constructed"}
    if go != "yes":
        what = {"construct": "constructs ONE native flPackage object (it is not attached to anything)",
                "construct_named": f"constructs ONE flPackage and names it {family!r} as Build Names would (four assignments)"
                                   + (" and then marks it changed (ONE flItems.notifyChangesApplied)" if mark == "yes" else ""),
                }.get(stage, "attaches the constructed package to the workspace (the experiment that may open a new font)")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    if stage == "construct_named":
        if _TRYFONT["constructed"]:
            return dict(flags, error="a package was already constructed in this listener run (each construction leaves a "
                                     "native reference behind); restart the listener to repeat")
        cls = getattr(mod, "flPackage", None)
        if cls is None:
            return {"error": "the fontlab module has no flPackage class; nothing was constructed"}
        before = _tryfont_workspace_state(mod)
        _TRYFONT["constructed"] = True     # set BEFORE the call: whatever happens, there is never a second construction in this run
        try:
            pkg = cls()
        except Exception as exc:
            return {"error": f"flPackage() raised {type(exc).__name__}: {exc}; nothing was named", "workspace_before": before}
        _TRYFONT["package"] = pkg
        names_before = {attr: _trynames_read(pkg, attr) for attr in _TRYNAMES_FIELDS}
        assignments = []
        for attr, value in _tryfont_built_names(family):
            entry = {"field": attr, "value": value}
            try:
                setattr(pkg, attr, value)
            except Exception as exc:
                entry["call_error"] = f"{type(exc).__name__}: {exc}"
            entry["read_back"] = _trynames_read(pkg, attr)
            entry["read_back_equal"] = entry["read_back"] == value
            assignments.append(entry)
        all_equal = all(e["read_back_equal"] for e in assignments)
        marked = _tryfont_mark(mod, pkg, all_equal) if mark == "yes" else None
        out = {"stage": "construct_named", "constructed": True, "family": family, "names_before": names_before,
               "assignments": assignments, "all_equal": all_equal,
               "reads": {attr: _tryfont_read(pkg, attr) for attr in _TRYFONT_PKG_READS},
               "workspace_before": before, "workspace_after": _tryfont_workspace_state(mod, pkg),
               "note": "RESEARCH: look at the tab title (Full name) and the FONTS panel (Family name); nothing is saved by Glyphbridge"}
        if marked is not None:
            out["mark"] = marked
        return out
    if stage == "construct":
        if _TRYFONT["constructed"]:
            return dict(flags, error="a package was already constructed in this listener run (each construction leaves a "
                                     "native reference behind); restart the listener to repeat")
        cls = getattr(mod, "flPackage", None)
        if cls is None:
            return {"error": "the fontlab module has no flPackage class; nothing was constructed"}
        before = _tryfont_workspace_state(mod)
        try:
            pkg = cls()
        except Exception as exc:
            return {"error": f"flPackage() raised {type(exc).__name__}: {exc}; nothing was attached",
                    "workspace_before": before}
        _TRYFONT["package"] = pkg
        _TRYFONT["constructed"] = True
        reads = {attr: _tryfont_read(pkg, attr) for attr in _TRYFONT_PKG_READS}
        return {"stage": "construct", "constructed": True, "attached": _TRYFONT["attached"], "package_type": type(pkg).__name__,
                "reads": reads, "workspace_before": before, "workspace_after": _tryfont_workspace_state(mod, pkg),
                "note": "the package is detached unless workspace_after differs from workspace_before"}
    # stage == "attach"
    pkg = _TRYFONT["package"]
    if not _TRYFONT["constructed"] or pkg is None:
        return dict(flags, error="run stage=construct first (there is no package to attach)")
    if _TRYFONT["attached"]:
        return dict(flags, error="addPackage was already attempted in this listener run; restart the listener to repeat")
    before = _tryfont_workspace_state(mod, pkg)
    _TRYFONT["attached"] = True        # set BEFORE the call: whatever happens, there is never a second attempt
    returned, error = None, None
    try:
        returned = _tryfont_plain(mod.flWorkspace.instance().addPackage(pkg))
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"stage": "attach", "constructed": True, "attached": True, "call": "flWorkspace.instance().addPackage(package)",
            "return_value": returned, "call_error": error, "workspace_before": before,
            "workspace_after": _tryfont_workspace_state(mod, pkg),
            "note": "EXPERIMENT: nothing is saved by Glyphbridge; quit FontLab WITHOUT saving afterwards"}


# --------------------------------------------------------------------------
# /debug/trysync (v0.85) - EXPERIMENT: does a plain API call make FontLab sync the modern layers to the legacy glyphs (the sync that
# protects a drawn layer from the next create_glyph)? Candidates: flPackage.update() and flWorkspace.update(). Not called, ever, by
# this probe: blockUpdate, unblockUpdate, createNewProject, addPackage, closePackage, closeProject, saveProject, export*, release, remove.
# --------------------------------------------------------------------------

_TRYSYNC_STAGES = ("state", "package_update", "workspace_update")
_TRYSYNC = {"package_update": 0, "workspace_update": 0}


def _trysync_target(mod):
    """(workspace, package, None) or (None, None, reason). READ ONLY. Only when exactly one font is open, so that the workspace's
    current package must be this font; any failed check refuses."""
    count_fonts = getattr(mod, "CountFonts", None)
    if count_fonts is None:
        return None, None, "the fontlab module has no CountFonts, so the number of open fonts is unknown"
    try:
        count = count_fonts()
    except Exception as exc:
        return None, None, f"CountFonts() failed ({type(exc).__name__}: {exc})"
    if type(count) is not int or count != 1:
        return None, None, f"CountFonts() is {count!r}; the probe runs only when exactly one font is open"
    try:
        ws = mod.flWorkspace.instance()
        npk = len(ws.packages())
    except Exception as exc:
        return None, None, f"the workspace's packages could not be counted ({type(exc).__name__}: {exc})"
    if npk != 1:
        return None, None, f"the workspace holds {npk} packages, not exactly 1"
    pkg, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return None, None, err
    if pkg is None:
        return None, None, "the workspace has no current package"
    is_null, err = _pkg_get(pkg, "isNull")
    if err is not None:
        return None, None, err
    if is_null is not False:
        return None, None, "the current package is null or its state is unknown"
    return ws, pkg, None


def _trysync_snapshot(ws, pkg):
    """Read-only: isChanged of both objects and the package's glyphsCount; a failed read is reported as text."""
    snap = {}
    for label, obj, attr in (("package_isChanged", pkg, "isChanged"), ("workspace_isChanged", ws, "isChanged"),
                             ("package_glyphsCount", pkg, "glyphsCount")):
        value, err = _pkg_get(obj, attr)
        snap[label] = err if err is not None else _tryfont_plain(value)
    return snap


def debug_try_sync(stage, go):
    import sys as _sys
    if stage not in _TRYSYNC_STAGES:
        return {"error": 'stage must be "state", "package_update" or "workspace_update"'}
    if stage != "state" and go != "yes":
        what = ("calls flPackage.update() ONCE on the font's package" if stage == "package_update"
                else "calls flWorkspace.instance().update() ONCE")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYSYNC)}
    before = _trysync_snapshot(ws, pkg)
    if stage == "state":
        return {"stage": "state", "state": before, "calls_so_far": dict(_TRYSYNC)}
    label = "flPackage.update()" if stage == "package_update" else "flWorkspace.instance().update()"
    target = pkg if stage == "package_update" else ws
    _TRYSYNC[stage] += 1        # counted BEFORE the call: whatever happens, it is on record
    returned, error = None, None
    try:
        returned = _tryfont_plain(target.update())
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    return {"stage": stage, "call": label, "return_value": returned, "call_error": error, "before": before,
            "after": _trysync_snapshot(ws, pkg), "calls_so_far": dict(_TRYSYNC),
            "note": "EXPERIMENT: read /glyph/outline of a drawn glyph before and after (agree false to true = synced) and watch the grid "
                    "tiles; nothing is saved by Glyphbridge; quit FontLab WITHOUT saving afterwards"}


# --------------------------------------------------------------------------
# /debug/trycreate (v0.86) - EXPERIMENT: which part of create_glyph removes the layers of unsynced, API-drawn glyphs?
#   how=plain          font.createGlyph(name) ONLY
#   how=legacy_update  font.createGlyph(name), then font.update() (what create_glyph does today; the control)
# Not called, ever, by this probe: removeGlyph, save, close, export, release, remove, blockUpdate, unblockUpdate.
# --------------------------------------------------------------------------

_TRYCREATE_HOWS = ("plain", "legacy_update")
_TRYCREATE_NAME_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
_TRYCREATE = {"plain": 0, "legacy_update": 0}


def debug_try_create(name, how, go):
    import sys as _sys
    if how not in _TRYCREATE_HOWS:
        return {"error": 'how must be "plain" (createGlyph only) or "legacy_update" (createGlyph, then font.update())'}
    if go != "yes":
        what = ("calls font.createGlyph(name) ONLY and adds ONE glyph" if how == "plain"
                else "calls font.createGlyph(name) and then font.update() and adds ONE glyph")
        return {"error": f"how={how} {what}. Add &go=yes to run it."}
    if not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYCREATE_NAME_CHARS for ch in name):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"how": how, "error": why, "calls_so_far": dict(_TRYCREATE)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    before = [str(g.name) for g in font.glyphs]
    if name in before:
        return {"how": how, "error": "a glyph with this name already exists", "before_count": len(before), "calls_so_far": dict(_TRYCREATE)}
    _TRYCREATE[how] += 1        # counted BEFORE the calls: whatever happens, it is on record
    calls = ["font.createGlyph(name)"]
    call_error, update_error = None, None
    try:
        font.createGlyph(name)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    if how == "legacy_update":
        calls.append("font.update()")
        try:
            font.update()
        except Exception as exc:
            update_error = f"{type(exc).__name__}: {exc}"
    after = [str(g.name) for g in font.glyphs]
    present = name in after
    out = {"how": how, "name": name, "calls": calls, "call_error": call_error, "update_error": update_error,
           "before_count": len(before), "after_count": len(after), "present": present,
           "created": present and len(after) == len(before) + 1, "calls_so_far": dict(_TRYCREATE),
           "note": "EXPERIMENT: read the sidebearings or /glyph/outline of the glyphs drawn earlier (a lost layer says 'no layer yet'), "
                   "and look at the grid (does the new glyph show up?); nothing is saved by Glyphbridge; quit FontLab WITHOUT saving afterwards"}
    added = _names_added(before, after)
    if added and not out["created"]:
        out["created_under_other_names"] = added
    return out


def debug_try_kern(a, b, go):
    """v0.92 - GATED one-call probe for the kerning lookup. The ONLY call made on the kerning object is
    font.kerning.get((a, b)): documented by FontLab as 'float get(fgKerningObjectPair / tuple(name1, name2)) - get kerning value'.
    Gate: go=yes exactly; both names plain strings of the safe set that EXIST as glyph names (found by iterating font.glyphs);
    at most _TRYKERN_MAX calls per listener run, counted BEFORE the call. len(font.kerning) is read before and after (a difference
    is reported as side_effect_detected). Never called: set, remove, clear, add*, delete*, rename*, scale, setPlainPairs, asDict,
    getPlainPairs*, items, keys, values. Group names are not accepted (v0.92)."""
    if go != "yes":
        return {"error": "this probe calls font.kerning.get((a, b)) ONCE (a read); add &go=yes to run it", "calls_so_far": _TRYKERN["calls"], "max_calls": _TRYKERN_MAX}
    for label, nm in (("a", a), ("b", b)):
        if not isinstance(nm, str) or not (1 <= len(nm) <= 63) or any(ch not in _TRYCREATE_NAME_CHARS for ch in nm):
            return {"error": f"{label} must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False, "count_fonts": 0, "note": "CountFonts() is 0: no font is open"}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    names = set(str(g.name) for g in font.glyphs)
    missing = [nm for nm in (a, b) if nm not in names]
    if missing:
        return {"open": True, "error": "no glyph with this name in the current font (group names are not accepted yet): " + ", ".join(repr(m) for m in missing),
                "calls_so_far": _TRYKERN["calls"]}
    if _TRYKERN["calls"] >= _TRYKERN_MAX:
        return {"open": True, "error": f"the limit of {_TRYKERN_MAX} kerning calls per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYKERN["calls"], "max_calls": _TRYKERN_MAX}
    try:
        kerning = font.kerning
        getter = kerning.get
    except Exception as exc:
        return {"open": True, "error": f"font.kerning / kerning.get not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYKERN["calls"]}
    if not callable(getter):
        return {"open": True, "error": "kerning.get is not callable", "calls_so_far": _TRYKERN["calls"]}

    def _len():
        try:
            n = len(kerning)
            return n if isinstance(n, int) and not isinstance(n, bool) else None
        except Exception:
            return None

    len_before = _len()
    _TRYKERN["calls"] += 1        # counted BEFORE the call: whatever happens, it is on record
    value, call_error = None, None
    try:
        value = getter((a, b))
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    len_after = _len()
    plain = isinstance(value, (int, float)) and not isinstance(value, bool)
    return {"open": True, "count_fonts": count, "a": a, "b": b, "call": "font.kerning.get((a, b))", "call_error": call_error,
            "value_type": type(value).__name__, "value": value if plain else None,
            "len_before": len_before, "len_after": len_after,
            "side_effect_detected": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
            "calls_so_far": _TRYKERN["calls"], "max_calls": _TRYKERN_MAX,
            "note": "the value is what FontLab's kerning.get returns for exactly this pair of glyph names, in font units; whether it also resolves "
                    "group (class) kerning is NOT known yet: compare with FontLab's own kerning display before relying on it"}


_TRYGROUPS_TOKEN_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-@")


def debug_try_groups(go, contains):
    """v0.93 - GATED probe for the glyph groups. The ONLY call made on the groups object is the zero-argument getter
    font.groups.getCompiled(): documented by FontLab as 'string getCompiled()'. Gate: go=yes exactly; at most _TRYGROUPS_MAX calls per
    listener run, counted BEFORE the call. len(font.groups) is read before and after (a difference is reported as side_effect_detected).
    The text itself is never returned whole: without `contains` the reply has its length, its line count and its first 500 characters;
    with `contains` (1 to 3 names of A-Z a-z 0-9 . _ - @) only the segments (split at newlines and semicolons) that mention a name as a
    whole word, at most 20 per name, each cut at 300 characters. Never called: get, keys, values, items, asDict, remove, rename, clear,
    fromDict, fromClassRecords, getAsClassRecords, has_key."""
    import re as _re
    if go != "yes":
        return {"error": "this probe calls font.groups.getCompiled() ONCE (a read that returns text); add &go=yes to run it",
                "calls_so_far": _TRYGROUPS["calls"], "max_calls": _TRYGROUPS_MAX}
    tokens = [t.strip() for t in (contains or "").split(",") if t.strip()]
    if len(tokens) > 3:
        return {"error": "contains: at most 3 names"}
    for tok in tokens:
        if not (1 <= len(tok) <= 63) or any(ch not in _TRYGROUPS_TOKEN_CHARS for ch in tok):
            return {"error": "each name in contains must be 1 to 63 characters from A-Z a-z 0-9 . _ - @"}
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False, "count_fonts": 0, "note": "CountFonts() is 0: no font is open"}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if _TRYGROUPS["calls"] >= _TRYGROUPS_MAX:
        return {"open": True, "error": f"the limit of {_TRYGROUPS_MAX} groups calls per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYGROUPS["calls"], "max_calls": _TRYGROUPS_MAX}
    try:
        groups = font.groups
        getter = groups.getCompiled
    except Exception as exc:
        return {"open": True, "error": f"font.groups / groups.getCompiled not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYGROUPS["calls"]}
    if not callable(getter):
        return {"open": True, "error": "groups.getCompiled is not callable", "calls_so_far": _TRYGROUPS["calls"]}

    def _len():
        try:
            n = len(groups)
            return n if isinstance(n, int) and not isinstance(n, bool) else None
        except Exception:
            return None

    len_before = _len()
    _TRYGROUPS["calls"] += 1        # counted BEFORE the call: whatever happens, it is on record
    value, call_error = None, None
    try:
        value = getter()
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    len_after = _len()
    out = {"open": True, "count_fonts": count, "call": "font.groups.getCompiled()", "call_error": call_error, "value_type": type(value).__name__,
           "len_before": len_before, "len_after": len_after,
           "side_effect_detected": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
           "calls_so_far": _TRYGROUPS["calls"], "max_calls": _TRYGROUPS_MAX}
    if isinstance(value, str):
        segments = [s.strip() for s in _re.split(r"[\n;]", value) if s.strip()]
        out["chars"] = len(value)
        out["lines"] = len(value.splitlines())
        out["segments"] = len(segments)
        if not tokens:
            out["head"] = value[:500]
        else:
            found = {}
            counts = {}
            for tok in tokens:
                pat = _re.compile(r"(?<![A-Za-z0-9._@-])" + _re.escape(tok) + r"(?![A-Za-z0-9._@-])")
                hits = [s for s in segments if pat.search(s)]
                counts[tok] = len(hits)
                found[tok] = [(h[:300] + " ...[cut]") if len(h) > 300 else h for h in hits[:20]]
            out["match_counts"] = counts
            out["matches"] = found
    out["note"] = ("EXPERIMENT: the text is the compiled form of font.groups (all 132 groups of Arial, kerning and others); whether it names the "
                   "KERNING groups (font.kerning.groups) is checked by comparing with FontLab's KERNING panel")
    return out


def debug_layer_item(name, index=0):
    """REMOVED: this used layer[index] subscript access, which crashed
    FontLab. See the module docstring note on v0.21 - no [] subscript
    access on native FontLab container objects, even when documented."""
    raise NotImplementedError(
        "debug_layer_item used layer[] subscript access, which crashed "
        "FontLab, and has been removed rather than left callable."
    )


# --------------------------------------------------------------------------
# /debug/tryrefresh (v0.119) - EXPERIMENT for F1 (topics/fonts-and-sync.md, section 8l): can a refresh of ONE glyph replace the
# whole-font font.update() of the legacy writes? font.update() writes the legacy copy of a glyph whose legacy glyph.layer was touched
# back over its modern layer (a Power Brush glyph loses its brush: live 417-435). Every stage needs go=yes and the one-font gate of
# /debug/trysync; each mode runs ONCE per listener run, counted BEFORE the first change:
#   stage=create   name=N how=Update_flGlyph|none   font.createGlyph(N); with Update_flGlyph then ONE fontlab.Update(<modern glyph of N>)
#   stage=unicode  name=N value=V                    glyph.unicode = V on an existing glyph (1 to 1114111), then ONE
#                                                    fontlab.Update(<modern glyph of N>); the value is read back
# Not called, ever, by this probe: font.update(), glyph.update(), UpdateAll(), the assign family, removeGlyph, deleteGlyph, save,
# close, export, release, remove, blockUpdate, unblockUpdate.
# --------------------------------------------------------------------------

_TRYREFRESH_STAGES = ("create", "unicode")
_TRYREFRESH_HOWS = ("Update_flGlyph", "none")
_TRYREFRESH = {"create_Update_flGlyph": 0, "create_none": 0, "unicode": 0}
_TRYREFRESH_NOTE = ("EXPERIMENT: read the sidebearings of the Power Brush glyph (192.466 intact, 192 flattened), and look at the grid (does a "
                    "new glyph show up?); nothing is saved by Glyphbridge; quit FontLab WITHOUT saving afterwards")


def _tryrefresh_unicode_value(glyph):
    """The legacy glyph's unicode as a plain int, None when unset, or the type name of anything else. Never raises."""
    try:
        u = glyph.unicode
    except Exception as exc:
        return f"<error: {type(exc).__name__}: {exc}>"
    if u is None or (isinstance(u, int) and not isinstance(u, bool)):
        return u
    return f"<{type(u).__name__}>"


def debug_try_refresh(stage, name, how, value, go):
    import sys as _sys
    if stage not in _TRYREFRESH_STAGES:
        return {"error": 'stage must be "create" or "unicode"'}
    if not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYCREATE_NAME_CHARS for ch in name):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    codepoint = None
    if stage == "create":
        if how not in _TRYREFRESH_HOWS:
            return {"error": 'how must be "Update_flGlyph" (createGlyph, then one fontlab.Update on the new glyph) or "none" (createGlyph only)'}
        key = "create_" + how
    else:
        if not (isinstance(value, str) and 1 <= len(value) <= 7 and all(ch in "0123456789" for ch in value)) or not (1 <= int(value) <= 0x10FFFF):
            return {"error": "value must be a decimal codepoint from 1 to 1114111"}
        codepoint = int(value)
        key = "unicode"
    if go != "yes":
        what = ("calls font.createGlyph(name) and adds ONE glyph" + (", then ONE fontlab.Update on that glyph" if how == "Update_flGlyph" else " (no refresh)")
                if stage == "create" else "sets the Unicode value of ONE existing glyph, then ONE fontlab.Update on that glyph")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYREFRESH)}
    if _TRYREFRESH[key] >= 1:
        return {"stage": stage, "error": "this mode was already run once in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYREFRESH)}
    upd = getattr(mod, "Update", None)
    if (stage == "unicode" or how == "Update_flGlyph") and not callable(upd):
        return {"stage": stage, "error": "the fontlab module has no callable Update", "calls_so_far": dict(_TRYREFRESH)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if stage == "create":
        return _tryrefresh_create(upd, font, name, how, key)
    return _tryrefresh_unicode(upd, font, name, codepoint)


def _tryrefresh_create(upd, font, name, how, key):
    before = [str(g.name) for g in font.glyphs]
    if name in before:
        return {"stage": "create", "how": how, "error": "a glyph with this name already exists", "before_count": len(before),
                "calls_so_far": dict(_TRYREFRESH)}
    _TRYREFRESH[key] += 1       # counted BEFORE the calls: whatever happens, it is on record
    calls = ["font.createGlyph(name)"]
    call_error, refresh_error, returned = None, None, None
    try:
        font.createGlyph(name)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    if how == "Update_flGlyph":
        glyph = _find_glyph(font, name)
        if glyph is None:
            refresh_error = "the new glyph is not in font.glyphs, so nothing was refreshed"
        else:
            try:
                w, _wrapper_how = _modern_wrapper(glyph, font)
            except Exception as exc:
                w, refresh_error = None, f"the modern glyph could not be reached ({exc}); nothing was refreshed"
            if w is not None:
                calls.append("fontlab.Update(<modern glyph>)")
                try:
                    returned = _tryfont_plain(upd(w))
                except Exception as exc:
                    refresh_error = f"{type(exc).__name__}: {exc}"
    after = [str(g.name) for g in font.glyphs]
    present = name in after
    out = {"stage": "create", "how": how, "name": name, "calls": calls, "call_error": call_error, "refresh_error": refresh_error,
           "refresh_return": returned, "before_count": len(before), "after_count": len(after), "present": present,
           "created": present and len(after) == len(before) + 1, "calls_so_far": dict(_TRYREFRESH), "note": _TRYREFRESH_NOTE}
    added = _names_added(before, after)
    if added and not out["created"]:
        out["created_under_other_names"] = added
    return out


def _tryrefresh_unicode(upd, font, name, codepoint):
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"stage": "unicode", "error": f"no glyph named {name!r}", "calls_so_far": dict(_TRYREFRESH)}
    try:
        w, _wrapper_how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"stage": "unicode", "name": name, "error": f"the modern glyph could not be reached ({exc}); nothing was changed",
                "calls_so_far": dict(_TRYREFRESH)}
    before = _tryrefresh_unicode_value(glyph)
    _TRYREFRESH["unicode"] += 1     # counted BEFORE the change: whatever happens, it is on record
    calls = ["glyph.unicode = value"]
    set_error, refresh_error, returned = None, None, None
    try:
        glyph.unicode = codepoint
    except Exception as exc:
        set_error = f"{type(exc).__name__}: {exc}"
    if set_error is None:
        calls.append("fontlab.Update(<modern glyph>)")
        try:
            returned = _tryfont_plain(upd(w))
        except Exception as exc:
            refresh_error = f"{type(exc).__name__}: {exc}"
    again = _find_glyph(font, name)
    after = _tryrefresh_unicode_value(again) if again is not None else "<the glyph is gone>"
    return {"stage": "unicode", "name": name, "value": codepoint, "calls": calls, "set_error": set_error, "refresh_error": refresh_error,
            "refresh_return": returned, "unicode_before": before, "unicode_after": after, "matches": after == codepoint,
            "calls_so_far": dict(_TRYREFRESH), "note": _TRYREFRESH_NOTE}


# --------------------------------------------------------------------------
# /debug/trynotify (v0.131) - RESEARCH for S1: tool writes leave the blue "changed" icon dark (FontLab then asks no save question and
# offers no Undo), and the isChanged / hasChanges flags do not follow that icon (657-659). Can one of FontLab's own flItems notifications
# turn it blue? Are the history positions what it shows? Every stage needs go=yes and the one-font gate of /debug/trysync. The counter
# is raised BEFORE the first call under test, and a call that failed is an error here, never an empty result.
#   stage=state              reads isChanged, hasChanges, hasHistoryStates, currentHistoryState(), initialHistoryState() of the package,
#                            the workspace and one glyph; none of the history getters has been called live before
#   stage=call&which=W       those reads, ONE call from the fixed list below, the reads again. on=class calls it on the flItems class,
#                            on=instance on flItems.instance() (the docstrings do not say which is right)
#   stage=ids (v0.135)       RESEARCH for the KERNING panel: the object ids (id) were refused by the calls that take a uint (731, 732) and look like
#                            memory addresses. Reads id and fgId of the package, id and fgGlyphId of the glyph, then ONE
#                            flWorkspace.findPackageId(n) for each package number that fits a uint and, on an object that is not null, ONE isEqual
#   id_from=object|fg (v0.135)  which id a call that takes one passes: id, or fgId and fgGlyphId. A number that is not a plain integer fitting a uint
#                            is refused before anything is called
# Never called by this probe: restoreHistoryState, clearAboveHistory, historyStates, blockUpdate, unblockUpdate, release, remove, save, close,
# export, update, changed, font.update().
# --------------------------------------------------------------------------

_TRYNOTIFY_WHICH = ("changes_applied", "workspace_has_changes", "package_updated", "package_content", "glyph_updated", "font_selected")
_TRYNOTIFY_TAKES_ID = ("package_content", "glyph_updated", "font_selected")
_TRYNOTIFY_ID_FROM = {"object": ("id", "id"), "fg": ("fgId", "fgGlyphId")}     # (the package's member, the glyph's member)
_TRYNOTIFY_UINT_MAX = 4294967295
_TRYNOTIFY_ON = ("class", "instance")
_TRYNOTIFY_MAX_STATE = 20
_TRYNOTIFY_MAX_CALL = 3
_TRYNOTIFY_MAX_IDS = 3
_TRYNOTIFY = {"state": 0, "changes_applied": 0, "workspace_has_changes": 0, "package_updated": 0, "package_content": 0, "glyph_updated": 0,
              "font_selected": 0, "ids": 0}
_TRYNOTIFY_TITLE = "Glyphbridge test"
_TRYNOTIFY_READS = ("isChanged", "hasChanges", "hasHistoryStates", "currentHistoryState", "initialHistoryState")
_TRYNOTIFY_NOTE = ("RESEARCH: a notification may change FontLab's display or its history. Look at the icon before the font's name and at Edit > Undo; "
                   "a reading that could not be made is an <error> here, never an empty result; nothing is saved by Glyphbridge")


def _trynotify_read(obj, attr):
    """A plain value, the type name of a native object, or "<error: why>". ONE read; a zero-argument callable is called once."""
    value, err = _pkg_get(obj, attr)
    return f"<error: {err}>" if err is not None else _tryfont_plain(value)


def _trynotify_snapshot(ws, pkg, w):
    """Read only: the flags and history positions of the three objects, the glyph's content and the number of glyphs."""
    content, _layer = _tryshapebox_state(w)
    return {"package": {attr: _trynotify_read(pkg, attr) for attr in _TRYNOTIFY_READS},
            "workspace": {attr: _trynotify_read(ws, attr) for attr in _TRYNOTIFY_READS},
            "glyph": {attr: _trynotify_read(w, attr) for attr in _TRYNOTIFY_READS},
            "glyph_content": content, "package_glyphsCount": _trynotify_read(pkg, "glyphsCount")}


def _trynotify_changes(before, after):
    """One line per reading that differs between the two snapshots."""
    return [f"{part}.{attr}: {before[part][attr]!r} -> {after[part][attr]!r}" for part in ("package", "workspace", "glyph")
            for attr in _TRYNOTIFY_READS if before[part][attr] != after[part][attr]]


def _trynotify_side_effect(before, after):
    """True or False when the glyph's content and the number of glyphs can be compared; otherwise None (not comparable)."""
    content = _tryshapebox_compare(before["glyph_content"], after["glyph_content"])
    counts = before["package_glyphsCount"], after["package_glyphsCount"]
    if content is None or any(type(c) is not int for c in counts):
        return None
    return content or counts[0] != counts[1]


def _trynotify_id(obj, label, attr="id"):
    """(a plain number that fits FontLab's uint, None) or (None, reason). v0.135: a number too large for a uint is refused (731, 732)."""
    value, err = _pkg_get(obj, attr)
    if err is not None:
        return None, f"{label} {attr} could not be read ({err})"
    if type(value) is not int:
        return None, f"{label} {attr} is a {type(value).__name__}, not a plain number"
    if not 0 <= value <= _TRYNOTIFY_UINT_MAX:
        return None, f"{label} {attr} is {value}, which does not fit a uint (0 to {_TRYNOTIFY_UINT_MAX})"
    return value, None


def _trynotify_same(pkg, found):
    """v0.135: what findPackageId returned: its type, isNull and, only for an object that is not null, ONE pkg.isEqual(found)."""
    out = {"result": _tryfont_plain(found), "same_package": None}
    if found is None:
        return out
    null, err = _pkg_get(found, "isNull")
    if err is not None:
        out["same_package"] = f"<error: {err}>"
        return out
    out["is_null"] = _tryfont_plain(null)
    if null is not False:
        return out
    try:
        out["same_package"] = _tryfont_plain(pkg.isEqual(found))
    except Exception as exc:
        out["same_package"] = f"<error: {type(exc).__name__}: {exc}>"
    return out


def _trynotify_ids(ws, pkg, w):
    """v0.135, stage=ids: the four ids, each read once, and ONE findPackageId per package number that fits a uint. A failure is reported, never raised."""
    reads = {"package_id": _trynotify_read(pkg, "id"), "package_fgId": _trynotify_read(pkg, "fgId"),
             "glyph_id": _trynotify_read(w, "id"), "glyph_fgGlyphId": _trynotify_read(w, "fgGlyphId")}
    lookups = {}
    for label in ("package_id", "package_fgId"):
        value = reads[label]
        if type(value) is not int or not 0 <= value <= _TRYNOTIFY_UINT_MAX:
            lookups[label] = {"called": False, "reason": f"{value!r} is not a plain number that fits a uint"}
            continue
        try:
            found = ws.findPackageId(value)
        except Exception as exc:
            lookups[label] = {"called": True, "value": value, "call_error": f"{type(exc).__name__}: {exc}"}
            continue
        lookups[label] = {"called": True, "value": value, **_trynotify_same(pkg, found)}
    return reads, lookups


def _trynotify_plan(which, pkg, w, id_from="object"):
    """(function of the flItems target, text naming the call, None), or (None, None, reason) when nothing may be called."""
    if which == "changes_applied":
        return (lambda t: t.notifyChangesApplied(_TRYNOTIFY_TITLE, w, False)), f"notifyChangesApplied({_TRYNOTIFY_TITLE!r}, <flGlyph>, False)", None
    if which == "workspace_has_changes":
        return (lambda t: t.notifyWorkspaceHasChanges(True)), "notifyWorkspaceHasChanges(True)", None
    if which == "package_updated":
        return (lambda t: t.notifyPackageUpdated(pkg)), "notifyPackageUpdated(<flPackage>)", None
    pkg_attr, glyph_attr = _TRYNOTIFY_ID_FROM[id_from]
    pid, err = _trynotify_id(pkg, "the package's", pkg_attr)
    if err is not None:
        return None, None, err
    if which == "package_content":
        return (lambda t: t.notifyPackageContentUpdated(pid)), f"notifyPackageContentUpdated({pid})", None
    if which == "font_selected":
        return (lambda t: t.notifyFontSelected(pid)), f"notifyFontSelected({pid})", None
    gid, err = _trynotify_id(w, "the glyph's", glyph_attr)
    if err is not None:
        return None, None, err
    return (lambda t: t.notifyGlyphUpdated(pid, gid)), f"notifyGlyphUpdated({pid}, {gid})", None


def debug_try_notify(stage, which, on, name, go, id_from="object"):
    import sys as _sys
    if stage not in ("state", "ids", "call"):
        return {"error": 'stage must be "state", "ids" or "call"'}
    if stage == "call" and which not in _TRYNOTIFY_WHICH:
        return {"error": "which must be one of: " + ", ".join(_TRYNOTIFY_WHICH)}
    if stage == "call" and on not in _TRYNOTIFY_ON:
        return {"error": 'on must be "class" or "instance"'}
    if stage == "call" and id_from not in _TRYNOTIFY_ID_FROM:
        return {"error": 'id_from must be "object" or "fg"'}
    if stage == "call" and id_from != "object" and which not in _TRYNOTIFY_TAKES_ID:
        return {"error": f"{which} takes no id, so id_from does not apply to it"}
    if not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYCREATE_NAME_CHARS for ch in name):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    if go != "yes":
        what = {"state": "reads flags and history positions that have not been read live before",
                "ids": "reads the ids and asks findPackageId and isEqual, which have not been called live before"}.get(stage, f"makes ONE flItems call ({which})")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    key = stage if stage in ("state", "ids") else which
    limit = {"state": _TRYNOTIFY_MAX_STATE, "ids": _TRYNOTIFY_MAX_IDS}.get(stage, _TRYNOTIFY_MAX_CALL)
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYNOTIFY)}
    if _TRYNOTIFY[key] >= limit:
        return {"stage": stage, "error": f"{key} already ran {limit} times in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYNOTIFY)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"stage": stage, "error": f"no glyph named {name!r}", "calls_so_far": dict(_TRYNOTIFY)}
    try:
        w, _wrapper_how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"stage": stage, "name": name, "error": f"the modern glyph could not be reached ({exc}); nothing was called",
                "calls_so_far": dict(_TRYNOTIFY)}
    if stage == "state":
        _TRYNOTIFY[key] += 1     # counted BEFORE the first read under test: whatever happens, it is on record
        return {"stage": stage, "name": name, "state": _trynotify_snapshot(ws, pkg, w), "calls_so_far": dict(_TRYNOTIFY), "note": _TRYNOTIFY_NOTE}
    if stage == "ids":
        _TRYNOTIFY[key] += 1     # counted BEFORE the first read and call under test
        start = _trynotify_snapshot(ws, pkg, w)
        reads, lookups = _trynotify_ids(ws, pkg, w)
        end = _trynotify_snapshot(ws, pkg, w)
        return {"stage": stage, "name": name, "reads": reads, "lookups": lookups, "changed_readings": _trynotify_changes(start, end),
                "side_effect_detected": _trynotify_side_effect(start, end), "calls_so_far": dict(_TRYNOTIFY), "note": _TRYNOTIFY_NOTE}
    items = getattr(mod, "flItems", None)
    if items is None:
        return {"stage": stage, "which": which, "error": "the fontlab module has no flItems: nothing was called", "calls_so_far": dict(_TRYNOTIFY)}
    make_call, text, why_not = _trynotify_plan(which, pkg, w, id_from)
    if make_call is None:
        return {"stage": stage, "which": which, "error": why_not + ": nothing was called", "calls_so_far": dict(_TRYNOTIFY)}
    _TRYNOTIFY[key] += 1         # counted BEFORE the first read and the call under test: whatever happens, it is on record
    before = _trynotify_snapshot(ws, pkg, w)
    returned, call_error = None, None
    try:
        returned = _tryfont_plain(make_call(items if on == "class" else items.instance()))
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    after = _trynotify_snapshot(ws, pkg, w)
    return {"stage": stage, "which": which, "on": on, "id_from": id_from, "name": name, "call": ("flItems." if on == "class" else "flItems.instance().") + text,
            "return_value": returned, "call_error": call_error, "state_before": before, "state_after": after,
            "changed_readings": _trynotify_changes(before, after), "side_effect_detected": _trynotify_side_effect(before, after),
            "calls_so_far": dict(_TRYNOTIFY), "note": _TRYNOTIFY_NOTE}


# --------------------------------------------------------------------------
# /debug/trynames (v0.137) - RESEARCH for P0.4, a create_font that can be given a name. Can the names FontLab keeps in the font package
# (psn ffn tfn tsn sgn: the PostScript name, Full name, Family name, Style name and Style group that Font Info shows) be written through
# the API, and does FontLab's display follow? In Font Info, Build Names set Full name = family + " " + style, PostScript = family without
# spaces + "-" + style and Style group = family (845, 849, 850), while the legacy font.info kept its old Full and PostScript names.
# Exactly one font open (the gate of /debug/trysync), so the workspace's current package must be this font.
#   stage=state                        read only, no go needed: the five package names, fileName and four legacy font.info names
#   stage=set&field=F&value=V&go=yes   ONE assignment pkg.F = V, F one of psn ffn tfn tsn sgn: the one deliberate setter of this probe;
#                                      every name is read before and after; at most _TRYNAMES_MAX_SET per listener run
#   stage=refresh&which=W&go=yes       ONE flItems notification; every name read before and after; at most _TRYNAMES_MAX_REFRESH per W
#                                      and listener run. W=content (the default): notifyPackageContentUpdated(<package fgId>), the call
#                                      of the KERNING panel refresh (0.136, live 738-748), which did NOT redraw the FONTS panel (856-857);
#                                      v0.138: W=package: notifyPackageUpdated(<package fgId>) (its docstring takes flPackage | uint id);
#                                      W=packages: notifyPackagesUpdated(), no argument. Both seen by name only before 0.138.
#                                      v0.140, none of the six calls of 856-866 having redrawn the FONTS panel: W=model:
#                                      flItems.notifyModelChanged(); W=properties: flItems.notifyPropertiesChanged(<the flPackage itself>);
#                                      W=changed: flPackage.changed(), no flItems. All three seen by name only before 0.140.
#                                      v0.141, after test 871 showed that the FONTS panel rebuilds its list from the current names
#                                      when a font is added: W=applied: flItems.notifyChangesApplied('Glyphbridge test', <flPackage>,
#                                      False); W=readed: flItems.notifyPackageReaded(<flPackage>); W=added: flItems.notifyPackageAdded(
#                                      <flPackage>), which may list the font twice. Seen by name only before 0.141.
#   stage=store&go=yes                 v0.139: ONE flPackage.store_font_info(<the package's fgPackage>) (docstring: store_font_info(fg::Package
#                                      *package)); which way it copies names is unknown, so every name is read before and after
#   stage=legacy_set&field=familyName&value=V&go=yes   v0.139: ONE assignment font.info.familyName = V (the legacy view), the same
#                                      value checks as stage=set. Both at most _TRYNAMES_MAX_OTHER per listener run. Reason: no
#                                      refresh call redrew the FONTS panel after a package write (856-863); it may show the legacy family.
#   stage=info_set&field=F&value=V&go=yes   v0.143: ONE assignment flPackage.info.F = V, F = openTypeNamePreferredFamilyName or
#                                      openTypeNamePreferredSubfamilyName, 3 per listener run; every reply also reads both. Reason: after a
#                                      rebuild the FONTS panel grouped a font whose tfn, ffn, psn and sgn read Nm Three under "Unnamed" (879),
#                                      and its info.openTypeNamePreferredFamilyName, never written, read Unnamed (878, read only).
#   stage=title[&full=yes|no]&go=yes   v0.144: ONE flPackage.title_name(<True|False>) call (docstring: string title_name([bool force_full =
#                                      true]); never called before), 3 per listener run; the reply holds the returned text, and elidedName
#                                      (a plain string property, read with ONE getattr) before and after. Reason: a Full name typed in Font
#                                      Info changed the tab's title (902) and every API write left it as it was (896-901): is title_name what
#                                      the tab shows, and does a call to it change the tab? stage=state reads elidedName too (key elided_name).
# A counter is raised BEFORE the call under test. V is 1 to 63 printable ASCII characters (32-126) without a leading or trailing space;
# for psn no space at all. Every read is ONE getattr; a callable is never called. Never called by this probe: collectNames, title_name (outside stage=title),
# update, changed, font.update(), save, close, export, any setter of flPackage.info, any setter of font.info other than stage=legacy_set,
# and store_font_info outside stage=store.
# --------------------------------------------------------------------------

_TRYNAMES_STAGES = ("state", "set", "refresh", "store", "legacy_set", "info_set", "title")
_TRYNAMES_MAX_OTHER = 3            # v0.139: store and legacy_set, each per listener run; v0.143: info_set; v0.144: title
_TRYNAMES_LEGACY_SET_FIELDS = ("familyName",)
_TRYNAMES_INFO = ("openTypeNamePreferredFamilyName", "openTypeNamePreferredSubfamilyName")   # v0.143: flPackage.info, read and set
_TRYNAMES_FIELDS = _PACKAGE_NAME_FIELDS
_TRYNAMES_LEGACY = ("familyName", "styleName", "postscriptFullName", "postscriptFontName")
_TRYNAMES_MAX_SET = 10
_TRYNAMES_MAX_REFRESH = 3          # per which (v0.138; 6 for the one refresh call of v0.137)
_TRYNAMES_REFRESH = {"content": "notifyPackageContentUpdated(<package fgId>)", "package": "notifyPackageUpdated(<package fgId>)",
                     "packages": "notifyPackagesUpdated()", "model": "notifyModelChanged()",                  # v0.140: model,
                     "properties": "notifyPropertiesChanged(<flPackage>)", "changed": "flPackage.changed()",   # properties, changed
                     "applied": "notifyChangesApplied('Glyphbridge test', <flPackage>, False)",               # v0.141: applied,
                     "readed": "notifyPackageReaded(<flPackage>)", "added": "notifyPackageAdded(<flPackage>)"}  # readed, added
_TRYNAMES_VALUE_MAX = 63
_TRYNAMES = {"set": 0, "content": 0, "package": 0, "packages": 0, "model": 0, "properties": 0, "changed": 0, "applied": 0, "readed": 0, "added": 0,
             "store": 0, "legacy_set": 0, "info_set": 0, "title": 0}
_TRYNAMES_NOTE = ("RESEARCH: compare with FontLab's own display (the font's tab title shows the Full name, the FONTS panel the Family name, "
                  "Font Info the five fields); a reading that could not be made is an <error> here, never an empty result; nothing is saved by Glyphbridge")


def _trynames_read(obj, attr):
    """ONE getattr: text without control characters, "<callable, not called>", the type name of anything else, or "<error: why>"."""
    try:
        value = getattr(obj, attr)
    except Exception as exc:
        return f"<error: {type(exc).__name__}: {exc}>"
    if isinstance(value, str):
        return _plain_text(value)
    if callable(value):
        return "<callable, not called>"
    return f"<{type(value).__name__}>"


def _trynames_info(pkg):
    """v0.143: the package's info object (ONE getattr), and its two Preferred names, or "<error: why>"."""
    try:
        pinfo = getattr(pkg, "info")
    except Exception as exc:
        return None, f"<error: flPackage.info could not be read ({type(exc).__name__}: {exc})>"
    if pinfo is None or isinstance(pinfo, (str, int, float, bool)) or callable(pinfo):
        return None, f"<error: flPackage.info is {type(pinfo).__name__}, not an info object>"
    return pinfo, {attr: _trynames_read(pinfo, attr) for attr in _TRYNAMES_INFO}


def _trynames_snapshot(pkg, font):
    """Read only: the package's five names and fileName, its info's Preferred names (v0.143), and the legacy font.info names."""
    package = {attr: _trynames_read(pkg, attr) for attr in _TRYNAMES_FIELDS + ("fileName",)}
    info_names = _trynames_info(pkg)[1]
    try:
        info = font.info
    except Exception as exc:
        return {"package": package, "info": info_names, "legacy": f"<error: font.info could not be read ({type(exc).__name__}: {exc})>"}
    return {"package": package, "info": info_names, "legacy": {attr: _trynames_read(info, attr) for attr in _TRYNAMES_LEGACY}}


def _trynames_changes(before, after):
    """One line per reading that differs between the two snapshots."""
    out = []
    for part in ("package", "info", "legacy"):
        b, a = before.get(part), after.get(part)
        if not isinstance(b, dict) or not isinstance(a, dict):
            if b != a:
                out.append(f"{part}: {b!r} -> {a!r}")
            continue
        out.extend(f"{part}.{k}: {b.get(k)!r} -> {a.get(k)!r}" for k in b if b.get(k) != a.get(k))
    return out


def _trynames_value_error(field, value):
    """None, or why the value is refused before anything is called."""
    if not isinstance(value, str) or not (1 <= len(value) <= _TRYNAMES_VALUE_MAX):
        return f"value must be 1 to {_TRYNAMES_VALUE_MAX} characters"
    if any(not (32 <= ord(ch) <= 126) for ch in value):
        return "value must hold printable ASCII characters only (32 to 126)"
    if value != value.strip(" "):
        return "value must not start or end with a space"
    if field == "psn" and " " in value:
        return "a PostScript name (psn) must not contain a space"
    return None


def debug_try_names(stage, field, value, go, which="content", full="yes"):
    import sys as _sys
    if stage not in _TRYNAMES_STAGES:
        return {"error": "stage must be one of: " + ", ".join(_TRYNAMES_STAGES)}
    if stage == "title" and full not in ("yes", "no"):
        return {"error": "full must be yes or no; nothing was called"}
    if stage in ("set", "legacy_set", "info_set"):
        allowed = {"set": _TRYNAMES_FIELDS, "legacy_set": _TRYNAMES_LEGACY_SET_FIELDS}.get(stage, _TRYNAMES_INFO)
        if field not in allowed:
            return {"error": "field must be one of: " + ", ".join(allowed)}
        why = _trynames_value_error(field, value)
        if why is not None:
            return {"error": why + "; nothing was called"}
    if stage == "refresh" and which not in _TRYNAMES_REFRESH:
        return {"error": "which must be one of: " + ", ".join(_TRYNAMES_REFRESH) + "; nothing was called"}
    if stage != "state" and go != "yes":
        what = {"set": f"assigns {value!r} to the package's {field} (ONE setter)",
                "legacy_set": f"assigns {value!r} to the legacy font.info.{field} (ONE setter)",
                "info_set": f"assigns {value!r} to the package's info.{field} (ONE setter)",
                "store": "makes ONE flPackage.store_font_info(<the package's fgPackage>) call, whose direction is unknown",
                "title": f"makes ONE flPackage.title_name({full == 'yes'}) call, a method never called before",
                }.get(stage, "makes ONE " + ("" if _TRYNAMES_REFRESH[which].startswith("flPackage.") else "flItems.")
                      + f"{_TRYNAMES_REFRESH[which]} call")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYNAMES)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if stage == "state":
        return {"stage": stage, "state": _trynames_snapshot(pkg, font), "elided_name": _trynames_read(pkg, "elidedName"),
                "calls_so_far": dict(_TRYNAMES), "note": _TRYNAMES_NOTE}
    key = which if stage == "refresh" else stage
    limit = {"set": _TRYNAMES_MAX_SET, "refresh": _TRYNAMES_MAX_REFRESH}.get(stage, _TRYNAMES_MAX_OTHER)
    if _TRYNAMES[key] >= limit:
        return {"stage": stage, "error": f"{key} already ran {limit} times in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYNAMES)}
    if stage == "set":
        def make_call():
            setattr(pkg, field, value)
        text = f"flPackage.{field} = {value!r}"
    elif stage == "legacy_set":
        try:
            info = font.info
        except Exception as exc:
            return {"stage": stage, "error": f"font.info could not be read ({type(exc).__name__}: {exc}): nothing was called",
                    "calls_so_far": dict(_TRYNAMES)}
        def make_call():
            setattr(info, field, value)
        text = f"font.info.{field} = {value!r}"
    elif stage == "info_set":
        pinfo, why_not = _trynames_info(pkg)
        if pinfo is None:
            return {"stage": stage, "error": why_not + ": nothing was called", "calls_so_far": dict(_TRYNAMES)}
        def make_call():
            setattr(pinfo, field, value)
        text = f"flPackage.info.{field} = {value!r}"
    elif stage == "title":
        title_name = getattr(pkg, "title_name", None)
        if not callable(title_name):
            return {"stage": stage, "error": "flPackage.title_name is missing or not callable: nothing was called", "calls_so_far": dict(_TRYNAMES)}
        returned = []
        def make_call():
            returned.append(title_name(full == "yes"))
        text = f"flPackage.title_name({full == 'yes'})"
    elif stage == "store":
        store = getattr(pkg, "store_font_info", None)
        if not callable(store):
            return {"stage": stage, "error": "flPackage.store_font_info is missing or not callable: nothing was called", "calls_so_far": dict(_TRYNAMES)}
        fg, err = _pkg_get(pkg, "fgPackage")
        if err is not None:
            return {"stage": stage, "error": err + ": nothing was called", "calls_so_far": dict(_TRYNAMES)}
        if fg is None or isinstance(fg, (str, int, float, bool)):
            return {"stage": stage, "error": f"the package's fgPackage is {type(fg).__name__}, not a font object: nothing was called",
                    "calls_so_far": dict(_TRYNAMES)}
        def make_call():
            store(fg)
        text = f"flPackage.store_font_info(<{type(fg).__name__}>)"
    elif which == "changed":
        changed = getattr(pkg, "changed", None)
        if not callable(changed):
            return {"stage": stage, "which": which, "error": "flPackage.changed is missing or not callable: nothing was called", "calls_so_far": dict(_TRYNAMES)}
        def make_call():
            changed()
        text = "flPackage.changed()"
    else:
        notifier = getattr(mod, "flItems", None)        # not named "items": a test counts the product route's own call text
        if notifier is None:
            return {"stage": stage, "which": which, "error": "the fontlab module has no flItems: nothing was called", "calls_so_far": dict(_TRYNAMES)}
        if which == "packages":
            def make_call():
                notifier.notifyPackagesUpdated()
            text = "flItems.notifyPackagesUpdated()"
        elif which == "model":
            def make_call():
                notifier.notifyModelChanged()
            text = "flItems.notifyModelChanged()"
        elif which == "applied":
            def make_call():
                notifier.notifyChangesApplied(_TRYNOTIFY_TITLE, pkg, False)
            text = f"flItems.notifyChangesApplied({_TRYNOTIFY_TITLE!r}, <flPackage>, False)"
        elif which == "readed":
            def make_call():
                notifier.notifyPackageReaded(pkg)
            text = "flItems.notifyPackageReaded(<flPackage>)"
        elif which == "added":
            def make_call():
                notifier.notifyPackageAdded(pkg)
            text = "flItems.notifyPackageAdded(<flPackage>)"
        elif which == "properties":
            def make_call():
                notifier.notifyPropertiesChanged(pkg)
            text = "flItems.notifyPropertiesChanged(<flPackage>)"
        else:
            pid, err = _trynotify_id(pkg, "the package's", "fgId")
            if err is not None:
                return {"stage": stage, "which": which, "error": err + ": nothing was called", "calls_so_far": dict(_TRYNAMES)}
            if which == "package":
                def make_call():
                    notifier.notifyPackageUpdated(pid)
                text = f"flItems.notifyPackageUpdated({pid})"
            else:
                def make_call():
                    notifier.notifyPackageContentUpdated(pid)
                text = f"flItems.notifyPackageContentUpdated({pid})"
    _TRYNAMES[key] += 1          # counted BEFORE the first read and the call under test: whatever happens, it is on record
    before = _trynames_snapshot(pkg, font)
    elided_before = _trynames_read(pkg, "elidedName") if stage == "title" else None
    call_error = None
    try:
        make_call()
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    after = _trynames_snapshot(pkg, font)
    out = {"stage": stage, "call": text, "call_error": call_error, "state_before": before, "state_after": after,
           "changed_readings": _trynames_changes(before, after), "calls_so_far": dict(_TRYNAMES), "note": _TRYNAMES_NOTE}
    if stage == "set":
        out["field"], out["value"] = field, value
        out["read_back_equal"] = isinstance(after.get("package"), dict) and after["package"].get(field) == value
    elif stage == "legacy_set":
        out["field"], out["value"] = field, value
        out["read_back_equal"] = isinstance(after.get("legacy"), dict) and after["legacy"].get(field) == value
    elif stage == "info_set":
        out["field"], out["value"] = field, value
        out["read_back_equal"] = isinstance(after.get("info"), dict) and after["info"].get(field) == value
    elif stage == "refresh":
        out["which"] = which
    elif stage == "title":
        got = returned[0] if returned else None
        out["full"] = full
        out["returned"] = _plain_text(got) if isinstance(got, str) else (None if not returned else f"<{type(got).__name__}>")
        out["elided_name_before"], out["elided_name_after"] = elided_before, _trynames_read(pkg, "elidedName")
    return out


# --------------------------------------------------------------------------
# /debug/tryshapebox (v0.129) - RESEARCH for P1.1, read only. Two questions from live 633-643: can an accent inside its base be
# verified from a box per element, and does FontLab say when a composite is out of step with its source? Both calls were seen by
# name only (637, 641). Every stage needs go=yes and the one-font gate of /debug/trysync; at most _TRYSHAPEBOX_MAX requests per
# stage and listener run, counted BEFORE the first call under test:
#   stage=shapebox      layer.shapes of the modern active layer, only when it is a real list, then ONE shape.inkBox() per element, no
#                       argument, read through the zero-argument getters of the QRectF (any number of elements since v0.174)
#   stage=dependencies  ONE flGlyph.isUnbindedDependecies() (FontLab's spelling), no argument; only a real bool is passed on
# The layer's shape, node and component counts and the advance width are read before and after (side_effect_detected).
# Never called by this probe: bindDependencies, update, changed, resetInkBox, font.update(), save.
# --------------------------------------------------------------------------

_TRYSHAPEBOX_MAX = 12
_TRYSHAPEBOX = {"shapebox": 0, "dependencies": 0}
_TRYSHAPEBOX_STAGES = ("shapebox", "dependencies")
_TRYSHAPEBOX_NOTE = ("RESEARCH, read only: compare with get_glyph_outline and FontLab's own numbers; a box or flag that could not be read is an "
                     "error here, never an empty result; nothing is saved by Glyphbridge")


def _tryshapebox_state(w):
    """(snapshot, layer or None): the modern layer's counts and the advance width, for the side-effect check. Read only."""
    st, layer = _tryshape_modern_state(w)
    adv, err = _tl_call(lambda: _num(w.advanceWidth))
    st["advance_width"] = adv if err is None else f"<error: {err}>"
    return st, layer


def _tryshapebox_boxes(layer):
    """(rows, None), one row per element in layer.shapes order, or (None, reason) when no inkBox() was called. A real list only.
    v0.174: no element limit (the user's decision of 2026-11-17); the 20 of v0.129 and v0.173's max_shapes are gone."""
    shapes, err = _tl_call(lambda: layer.shapes)
    if err is not None:
        return None, f"layer.shapes could not be read ({err}): no inkBox() was called"
    if type(shapes) is not list:
        return None, f"layer.shapes is a {type(shapes).__name__}, not a plain list: it was not indexed and no inkBox() was called"
    rows = []
    for index, shape in enumerate(shapes):
        box, call_err = _tl_call(lambda: shape.inkBox())
        rows.append({"index": index, "ink_box": {"error": call_err} if call_err is not None else _rect_plain(box)})
    return rows, None


def _tryshapebox_unbound(w):
    """{"value": bool} from ONE w.isUnbindedDependecies(), or {"error": why}. Anything but a real bool is reported, not passed on."""
    fn, err = _tl_call(lambda: getattr(w, "isUnbindedDependecies", None))
    if err is not None:
        return {"error": f"the member could not be read ({err})"}
    if not callable(fn):
        return {"error": "the modern glyph has no callable isUnbindedDependecies"}
    value, call_err = _tl_call(fn)
    if call_err is not None:
        return {"error": call_err}
    if type(value) is not bool:
        return {"error": f"it returned type {type(value).__name__}, not a bool"}
    return {"value": value}


def _tryshapebox_compare(before, after):
    """True or False when both snapshots hold plain numbers for every count and the width; otherwise None (not comparable)."""
    keys = ("shapes", "nodes", "components", "advance_width")
    plain = all(isinstance(s.get(k), (int, float)) and not isinstance(s.get(k), bool) for s in (before, after) for k in keys)
    return any(before[k] != after[k] for k in keys) if plain else None


def debug_try_shapebox(stage, name, go):
    import sys as _sys
    if stage not in _TRYSHAPEBOX_STAGES:
        return {"error": 'stage must be "shapebox" or "dependencies"'}
    if not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYCREATE_NAME_CHARS for ch in name):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    if go != "yes":
        what = "calls shape.inkBox() once per element" if stage == "shapebox" else "calls isUnbindedDependecies() once on the modern glyph"
        return {"error": f"stage={stage} {what}; it changes nothing, but neither call has been made live before. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYSHAPEBOX)}
    if _TRYSHAPEBOX[stage] >= _TRYSHAPEBOX_MAX:
        return {"stage": stage, "error": f"this stage already ran {_TRYSHAPEBOX_MAX} times in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYSHAPEBOX)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"stage": stage, "error": f"no glyph named {name!r}", "calls_so_far": dict(_TRYSHAPEBOX)}
    try:
        w, _wrapper_how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"stage": stage, "name": name, "error": f"the modern glyph could not be reached ({exc}); nothing was called",
                "calls_so_far": dict(_TRYSHAPEBOX)}
    before, layer = _tryshapebox_state(w)
    if stage == "shapebox" and layer is None:
        return {"stage": stage, "name": name, "error": "the glyph has no modern active layer: no inkBox() was called", "state_before": before,
                "calls_so_far": dict(_TRYSHAPEBOX)}
    _TRYSHAPEBOX[stage] += 1     # counted BEFORE the call under test: whatever happens, it is on record
    result = {"stage": stage, "name": name, "calls_so_far": dict(_TRYSHAPEBOX), "note": _TRYSHAPEBOX_NOTE}
    if stage == "shapebox":
        rows, err = _tryshapebox_boxes(layer)
        if rows is None:
            result["error"] = err
        else:
            result["elements"], result["element_count"] = rows, len(rows)
    else:
        result["unbound_dependencies"] = _tryshapebox_unbound(w)
    after, _layer_after = _tryshapebox_state(w)
    result["state_before"], result["state_after"] = before, after
    result["side_effect_detected"] = _tryshapebox_compare(before, after)
    return result


# --------------------------------------------------------------------------
# /debug/trykerngroups (v0.103) - RESEARCH for P0.8: where does FontLab keep a kerning group's MEMBERS and its SIDE? R0 (/debug/moddir,
# names only, 2026-11-01): fontgate.fgGroup has id, isBoth, isFeaGroup, isLeft, isRight, mode, name (modes KernLeftGroupMode,
# KernRightGroupMode, KernBothSideGroupMode, FeaClassGroupMode) but no member names; fgKerningGroups ("Dictionary of kerning groups")
# offers asDict, clear, has_key, items, keys, remove, rename, values; flPackage.getAllGroups() is documented as
# list((bool kernGroup, string groupName, int id, int mark, list(string glyphName))). Every stage needs go=yes and the one-font gate
# of /debug/trysync; at most _TRYKERNGROUPS_MAX requests per listener run, counted BEFORE the first native call of the stage:
#   stage=all&contains=a,b,c     pkg.kerning(current master) once, then ONE pkg.getAllGroups(). Only when that returns a real list or
#                                tuple: its len, the field types of the first entry, and the entries whose group name or a member name
#                                equals a token (at most _TRYKERNGROUPS_SHOWN)
#   stage=modes&contains=a,b,c   pkg.kerning(current master) once, its attribute groups, len(groups) before and after, ONE
#                                groups.values(). Only when that returns a real list or tuple: the seven fgGroup members of the first
#                                entry and of the entries whose name equals a token, each read as an attribute; a callable is
#                                reported and NEVER called
#   stage=tuples&contains=a,b,c  (v0.188, P1.6) the same reads as stage=modes, ONE groups.values(), but for the plain tuples it
#                                returned in test 199: only when the answer is a real list or tuple (exact type), the shapes of all
#                                entries (type and length), the first entry and the entries holding a token as a text field or as a
#                                text item of a list field, each field as a plain value, a real list or tuple by its length and up to
#                                _TRYKERNGROUPS_ITEMS items, and any other object by its type name only: nothing in an entry is called
#   stage=items&contains=a,b,c   (v0.189, P1.6) as stage=tuples, but ONE groups.items() instead of values(), documented (test 1373)
#                                as list(tuple('groupName', tuple(list('glyphName'), mode))); a token also matches one level deeper
#                                (a member inside the (members, mode) field)
#   stage=glyph&name=N           the legacy glyph's kerningLeft and kerningRight, read as attributes (a callable is never called);
#                                hypothesis: they are group ids (section 8p: Arial's 'o' has kerningRight 84)
# len() of the master's kerning table is read before and after in stages all and modes (side_effect_detected). Never called, ever:
# keys, asDict, has_key, clear, remove, rename, findGroup, deleteGroups, autoKern, and any subscript of a native object (items:
# only in stage=items, since v0.189).
# --------------------------------------------------------------------------

_TRYKERNGROUPS = {"calls": 0}
_TRYKERNGROUPS_MAX = 10
_TRYKERNGROUPS_STAGES = ("all", "modes", "tuples", "items", "glyph")
_TRYKERNGROUPS_SHOWN = 20
_TRYKERNGROUPS_FIELDS = 8            # v0.188 stage=tuples: at most this many fields of one entry are described
_TRYKERNGROUPS_ITEMS = 50            # v0.188 stage=tuples: at most this many items of one list field are shown
_TRYKERNGROUPS_MEMBERS = ("name", "mode", "isLeft", "isRight", "isBoth", "isFeaGroup", "id")


def _trykerngroups_attr(obj, attr):
    """ONE attribute read for the report: a plain value passes through, a callable is reported and NEVER called, a native object is
    reported by its type name; a failure is reported as text, never raised."""
    try:
        value = getattr(obj, attr)
    except Exception as exc:
        return f"<unreadable: {type(exc).__name__}: {exc}>"
    if callable(value):
        return "<callable, not called>"
    return _tryfont_plain(value)


def _trykerngroups_all(groups, tokens):
    """The getAllGroups() answer, filtered by the tokens. Only a real list or tuple is looked into; each entry must be a real 5-item
    list or tuple (kernGroup, name, id, mark, members) with a str name and a real list or tuple of members, otherwise it is counted
    as malformed and not shown."""
    if not isinstance(groups, (list, tuple)):
        return {"result_type": type(groups).__name__, "note_all": "not a real list or tuple, so nothing in it was read"}
    wanted = set(tokens)
    first = next(iter(groups), None)
    out = {"result_type": type(groups).__name__, "count": len(groups),
           "first_entry_types": [type(f).__name__ for f in first] if isinstance(first, (list, tuple)) else type(first).__name__}
    kern_groups, malformed, matched = 0, 0, []
    for entry in groups:
        if not isinstance(entry, (list, tuple)) or len(entry) != 5:
            malformed += 1
            continue
        flag, gname, gid, mark, members = entry
        if not isinstance(gname, str) or not isinstance(members, (list, tuple)):
            malformed += 1
            continue
        if flag is True:
            kern_groups += 1
        names = [_tryfont_plain(m) for m in members]
        if gname in wanted or any(n in wanted for n in names if isinstance(n, str)):
            matched.append({"kern_group": _tryfont_plain(flag), "name": gname, "id": _tryfont_plain(gid), "mark": _tryfont_plain(mark),
                            "member_count": len(names), "members": names[:50]})
    out.update(kern_groups=kern_groups, malformed=malformed, matched=len(matched), entries=matched[:_TRYKERNGROUPS_SHOWN],
               cut=len(matched) > _TRYKERNGROUPS_SHOWN)
    return out


def _trykerngroups_modes(entries, tokens):
    """The answer of values() on the master's kerning groups: the seven fgGroup members of the first entry and of the entries named
    by a token. Only a real list or tuple is looked into."""
    if not isinstance(entries, (list, tuple)):
        return {"values_type": type(entries).__name__, "note_modes": "not a real list or tuple, so nothing in it was read"}
    wanted = set(tokens)
    out = {"values_type": type(entries).__name__, "count": len(entries)}
    first = next(iter(entries), None)
    if first is not None:
        out["first_entry"] = dict({m: _trykerngroups_attr(first, m) for m in _TRYKERNGROUPS_MEMBERS}, type=type(first).__name__)
    matched = []
    for item in entries:
        gname = _trykerngroups_attr(item, "name")
        if isinstance(gname, str) and gname in wanted:
            matched.append(dict({m: _trykerngroups_attr(item, m) for m in _TRYKERNGROUPS_MEMBERS}, type=type(item).__name__))
    out.update(matched=len(matched), entries=matched[:_TRYKERNGROUPS_SHOWN], cut=len(matched) > _TRYKERNGROUPS_SHOWN)
    return out


def _trykerngroups_real_seq(value):
    """v0.188: True only for a real Python list or tuple (the exact type): a native object is never iterated."""
    return type(value) in (list, tuple)


def _trykerngroups_plain_list(seq, cap):
    """v0.188: up to cap elements of a real list or tuple, each as a plain value or by its type name."""
    shown = []
    for item in seq:
        if len(shown) >= cap:
            break
        shown.append(_tryfont_plain(item))
    return shown


def _trykerngroups_field(value):
    """v0.188: one field of a values() entry, for the report. A plain value passes through; a real list or tuple gives its type,
    length and up to _TRYKERNGROUPS_ITEMS elements (a real list or tuple inside by its type, length, cut and, since v0.189, up to
    _TRYKERNGROUPS_ITEMS plain elements, the members of a name pair; before, 10; anything else plain or by its type name); any other
    object by its type name only. Nothing is called."""
    if not _trykerngroups_real_seq(value):
        return _tryfont_plain(value)
    shown = []
    for item in value:
        if len(shown) >= _TRYKERNGROUPS_ITEMS:
            break
        if _trykerngroups_real_seq(item):
            shown.append({"type": type(item).__name__, "length": len(item), "values": _trykerngroups_plain_list(item, _TRYKERNGROUPS_ITEMS),
                          "cut": len(item) > _TRYKERNGROUPS_ITEMS})
        else:
            shown.append(_tryfont_plain(item))
    return {"type": type(value).__name__, "length": len(value), "values": shown, "cut": len(value) > _TRYKERNGROUPS_ITEMS}


def _trykerngroups_entry(entry):
    """v0.188: one values() entry: a real list or tuple by its type, length and up to _TRYKERNGROUPS_FIELDS fields; anything else
    by its type and plain value (a native object by its type name only)."""
    if not _trykerngroups_real_seq(entry):
        return {"type": type(entry).__name__, "value": _tryfont_plain(entry)}
    fields = []
    for value in entry:
        if len(fields) >= _TRYKERNGROUPS_FIELDS:
            break
        fields.append(_trykerngroups_field(value))
    return {"type": type(entry).__name__, "length": len(entry), "fields": fields, "cut": len(entry) > _TRYKERNGROUPS_FIELDS}


def _trykerngroups_texts(value, depth=0, max_depth=2):
    """v0.188: the texts of an entry, for matching tokens: the entry itself if it is text, its text fields, and the text elements of
    its real list or tuple fields; nothing deeper, and nothing inside a native object. v0.189: max_depth 3 (the name-pairs stage)
    also looks one level deeper, into a real list or tuple inside a field: the members in (name, (members, side))."""
    if isinstance(value, str):
        return {value}
    if depth >= max_depth or not _trykerngroups_real_seq(value):
        return set()
    found = set()
    for item in value:
        found |= _trykerngroups_texts(item, depth + 1, max_depth)
    return found


def _trykerngroups_tuples(entries, tokens, max_depth=2, kind="values"):
    """v0.188: the answer of values() (v0.189: or of the other dictionary call, kind) on the master's kerning groups, read as plain
    data: the shapes of all entries, the first entry, and the entries holding a token (at most _TRYKERNGROUPS_SHOWN shown), matched
    to max_depth. Only a real list or tuple is looked into."""
    if not _trykerngroups_real_seq(entries):
        return {kind + "_type": type(entries).__name__,
                "note_tuples" if kind == "values" else "note_" + kind: "not a real list or tuple, so nothing in it was read"}
    wanted = set(tokens)
    out = {kind + "_type": type(entries).__name__, "count": len(entries)}
    shapes, matched, n_matched = {}, [], 0
    for position, entry in enumerate(entries):
        shape = type(entry).__name__ + (f"/{len(entry)}" if _trykerngroups_real_seq(entry) else "")
        shapes[shape] = shapes.get(shape, 0) + 1
        if position == 0:
            out["first_entry"] = _trykerngroups_entry(entry)
        if wanted & _trykerngroups_texts(entry, 0, max_depth):
            n_matched += 1
            if len(matched) < _TRYKERNGROUPS_SHOWN:
                matched.append(dict(_trykerngroups_entry(entry), position=position))
    out.update(shapes=shapes, matched=n_matched, entries=matched, cut=n_matched > _TRYKERNGROUPS_SHOWN)
    return out


def debug_try_kern_groups(stage, contains, name, go):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe calls flPackage.getAllGroups() or the master's kerning groups' values() or items(), or reads two attributes of one "
                         "glyph; add &go=yes to run it", "calls_so_far": _TRYKERNGROUPS["calls"], "max_calls": _TRYKERNGROUPS_MAX}
    if stage not in _TRYKERNGROUPS_STAGES:
        return {"error": 'stage must be "all", "modes", "tuples", "items" or "glyph"'}
    if not isinstance(contains, (list, tuple)):
        return {"error": "contains must be a list of names"}
    if stage == "glyph":
        if contains:
            return {"error": "stage=glyph takes name=N, not contains"}
        if not _kern_name_ok(name):
            return {"error": "name must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    else:
        if name is not None:
            return {"error": f"stage={stage} takes contains=a,b,c, not name"}
        if not (1 <= len(contains) <= 3) or not all(_kern_name_ok(t) for t in contains):
            return {"error": "contains: 1 to 3 glyph or group names of 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYKERNGROUPS["calls"], "max_calls": _TRYKERNGROUPS_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if _TRYKERNGROUPS["calls"] >= _TRYKERNGROUPS_MAX:
        return {"open": True, "error": f"the limit of {_TRYKERNGROUPS_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYKERNGROUPS["calls"], "max_calls": _TRYKERNGROUPS_MAX}
    out = {"open": True, "stage": stage}
    if stage == "glyph":
        glyph = _find_glyph(font, name)
        if glyph is None:
            return {"open": True, "error": f"no glyph named {name!r} in the current font", "calls_so_far": _TRYKERNGROUPS["calls"]}
        _TRYKERNGROUPS["calls"] += 1        # counted BEFORE the reads: whatever happens, it is on record
        out.update(name=name, kerningLeft=_trykerngroups_attr(glyph, "kerningLeft"), kerningRight=_trykerngroups_attr(glyph, "kerningRight"))
    else:
        masters, err = _pkg_get(pkg, "masters")
        if err is not None:
            return {"open": True, "error": err, "calls_so_far": _TRYKERNGROUPS["calls"]}
        if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
            return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                    "calls_so_far": _TRYKERNGROUPS["calls"]}
        current, err = _pkg_get(pkg, "master")
        if not isinstance(current, str) or current not in masters:
            return {"open": True, "error": "the package's current master could not be read as one of its masters" + (f" ({err})" if err else ""),
                    "masters": list(masters), "calls_so_far": _TRYKERNGROUPS["calls"]}
        try:
            kerning_of = pkg.kerning
        except Exception as exc:
            return {"open": True, "error": f"flPackage.kerning not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYKERNGROUPS["calls"]}
        if not callable(kerning_of):
            return {"open": True, "error": "flPackage.kerning is not callable", "calls_so_far": _TRYKERNGROUPS["calls"]}
        _TRYKERNGROUPS["calls"] += 1        # counted BEFORE the first native call
        try:
            kerning = kerning_of(current)
        except Exception as exc:
            return {"open": True, "error": f"flPackage.kerning(master) failed: {type(exc).__name__}: {exc}", "master_used": current,
                    "calls_so_far": _TRYKERNGROUPS["calls"], "max_calls": _TRYKERNGROUPS_MAX}
        len_before = _trypkgkern_len(kerning)
        if stage == "all":
            try:
                getter = pkg.getAllGroups
                if not callable(getter):
                    raise TypeError("getAllGroups is not callable")
                groups = getter()
            except Exception as exc:
                out["call_error"] = f"{type(exc).__name__}: {exc}"
            else:
                out.update(_trykerngroups_all(groups, contains))
        else:
            try:
                container = kerning.groups
            except Exception as exc:
                out["call_error"] = f"the master's kerning groups not reachable: {type(exc).__name__}: {exc}"
            else:
                out["groups_type"] = type(container).__name__
                if callable(container):
                    out["call_error"] = "the master's kerning groups attribute is callable; it was not called"
                else:
                    groups_len_before = _trypkgkern_len(container)
                    try:
                        entries_of = container.items if stage == "items" else container.values     # v0.189: stage=items
                        if not callable(entries_of):
                            raise TypeError(("items" if stage == "items" else "values") + " is not callable")
                        entries = entries_of()
                    except Exception as exc:
                        out["call_error"] = f"{type(exc).__name__}: {exc}"
                    else:
                        if stage == "modes":
                            out.update(_trykerngroups_modes(entries, contains))
                        elif stage == "items":
                            out.update(_trykerngroups_tuples(entries, contains, 3, "items"))
                        else:
                            out.update(_trykerngroups_tuples(entries, contains, 2, "values"))
                    groups_len_after = _trypkgkern_len(container)
                    out.update(groups_len_before=groups_len_before, groups_len_after=groups_len_after,
                               groups_side_effect_detected=(groups_len_before != groups_len_after)
                               if (groups_len_before is not None and groups_len_after is not None) else None)
        len_after = _trypkgkern_len(kerning)
        out.update(master_used=current, kerning_len_before=len_before, kerning_len_after=len_after,
                   side_effect_detected=(len_before != len_after) if (len_before is not None and len_after is not None) else None)
    out.update(calls_so_far=_TRYKERNGROUPS["calls"], max_calls=_TRYKERNGROUPS_MAX,
               note="RESEARCH: compare with FontLab's Classes panel; nothing is changed or saved by Glyphbridge")
    return out


# --------------------------------------------------------------------------
# /debug/features (v0.107) - K11: the font's OpenType feature code (font.features). Names-only tests 158 and 230 on Arial: an fgOTLayout,
# len 29, with keys() "list(string) keys() - list of feature tags", has_key() "bool has_key(string / numeric tag) - True if feature is
# present" and get_feature() "string get_feature(string / numeric tag) - get feature text". Every stage needs go=yes and exactly one open
# font (CountFonts() == 1); at most _FEATURES_MAX requests per listener run, counted BEFORE the first call of the stage:
#   stage=tags               ONE features.keys(). Only when that returns a real list or tuple of text: the tags and their count
#   stage=size&tag=TAG       ONE features.keys(); only when TAG is one of the tags, ONE has_key(TAG), and only when that is True, ONE
#                            get_feature(TAG). Only the SIZE of the text is returned (characters, lines, lines with the word "pos"),
#                            never the text itself (token rule)
#   stage=shape&tag=TAG      (v0.108) the same calls; the size, the number of lines that START with each kind in _FEATURES_KINDS
#                            (pos, enum pos, a pos with a class on the left, lookup, ...), and the first _FEATURES_HEAD characters
#   stage=lines&tag=TAG&contains=a,b,c   (v0.108) the same calls; the size, and only the lines that name a token (1 to 3 glyph or class
#                            names) as a whole word: at most _FEATURES_LINES_SHOWN per token, each cut at _FEATURES_LINE_CUT characters
# len(features) is read before and after (side_effect_detected). Never called, ever: clear, remove, set_feature, set_prefix (they change
# the font), get_prefix, and any subscript of a native object.
# --------------------------------------------------------------------------

_FEATURES = {"calls": 0}
_FEATURES_MAX = 10
_FEATURES_STAGES = ("tags", "size", "shape", "lines")
_FEATURES_SHOWN = 100
_FEATURES_TAG_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
_FEATURES_HEAD = 300
_FEATURES_LINES_SHOWN = 20
_FEATURES_LINE_CUT = 200
_FEATURES_KINDS = (("pos", r"pos\b"), ("enum_pos", r"enum\s+pos\b"), ("class_left_pos", r"(?:enum\s+)?pos\s+@"), ("lookup", r"lookup\b"),
                   ("lookupflag", r"lookupflag\b"), ("script", r"script\b"), ("language", r"language\b"), ("subtable", r"subtable\b"),
                   ("class_definition", r"@[A-Za-z0-9_.\-]+\s*="), ("comment", r"#"))


def debug_features(stage, tag, go, contains=()):
    if go != "yes":
        return {"error": "this probe calls font.features.keys() (stage=tags), then has_key(tag) and get_feature(tag) (stages size, shape and "
                         "lines); add &go=yes to run it", "calls_so_far": _FEATURES["calls"], "max_calls": _FEATURES_MAX}
    if stage not in _FEATURES_STAGES:
        return {"error": 'stage must be "tags", "size", "shape" or "lines"'}
    if not isinstance(contains, (list, tuple)):
        return {"error": "contains must be a list of names"}
    if stage == "tags":
        if tag is not None:
            return {"error": "stage=tags takes no tag"}
    elif not isinstance(tag, str) or not (1 <= len(tag) <= 4) or any(ch not in _FEATURES_TAG_CHARS for ch in tag):
        return {"error": f"stage={stage} needs tag=<1 to 4 characters from A-Z a-z 0-9>, one of the tags that stage=tags lists"}
    if stage != "lines" and contains:
        return {"error": f"stage={stage} takes no contains (only stage=lines does)"}
    if stage == "lines" and (not (1 <= len(contains) <= 3)
                             or not all(isinstance(t, str) and 1 <= len(t) <= 63 and all(ch in _TRYGROUPS_TOKEN_CHARS for ch in t) for t in contains)):
        return {"error": "stage=lines needs contains=<1 to 3 glyph or class names of 1 to 63 characters from A-Z a-z 0-9 . _ - @>"}
    count = None
    try:
        counter = getattr(fl, "CountFonts", None)
        if callable(counter):
            got = counter()
            if isinstance(got, int) and not isinstance(got, bool):
                count = got
    except Exception:
        count = None
    if count == 0:
        return {"open": False, "count_fonts": 0, "note": "CountFonts() is 0: no font is open"}
    if count != 1:
        why = f"CountFonts() is {count}" if count is not None else "the number of open fonts could not be read (CountFonts() gave no plain number)"
        return {"open": True, "error": why + "; the probe runs only when exactly one font is open",
                "calls_so_far": _FEATURES["calls"], "max_calls": _FEATURES_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if _FEATURES["calls"] >= _FEATURES_MAX:
        return {"open": True, "error": f"the limit of {_FEATURES_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _FEATURES["calls"], "max_calls": _FEATURES_MAX}
    try:
        features = font.features
        keys_of = features.keys
    except Exception as exc:
        return {"open": True, "error": f"font.features / features.keys not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _FEATURES["calls"]}
    if not callable(keys_of):
        return {"open": True, "error": "features.keys is not callable", "calls_so_far": _FEATURES["calls"]}

    def _len():
        try:
            n = len(features)
            return n if isinstance(n, int) and not isinstance(n, bool) else None
        except Exception:
            return None

    len_before = _len()
    _FEATURES["calls"] += 1        # counted BEFORE the first call: whatever happens, it is on record
    out = {"open": True, "count_fonts": count, "stage": stage, "features_type": type(features).__name__}
    tags = None
    try:
        keys = keys_of()
    except Exception as exc:
        out["keys_error"] = f"{type(exc).__name__}: {exc}"
    else:
        out["keys_type"] = type(keys).__name__
        if isinstance(keys, (list, tuple)) and all(isinstance(k, str) for k in keys):
            tags = list(keys)
            out["tags_count"] = len(tags)
        else:
            out["keys_note"] = "not a real list or tuple of text, so nothing in it was read"
    if tags is not None and stage == "tags":
        out.update(tags=[t[:16] for t in tags[:_FEATURES_SHOWN]], cut=len(tags) > _FEATURES_SHOWN, duplicates=len(tags) - len(set(tags)))
    elif tags is not None:
        out.update(tag=tag, tag_listed=tag in tags)
        if tag not in tags:
            out["error"] = f"{tag!r} is not one of the tags keys() returned; has_key and get_feature were not called"
        else:
            try:
                has_of = features.has_key
                get_of = features.get_feature
            except Exception as exc:
                has_of = get_of = None
                out["error"] = f"has_key / get_feature not reachable: {type(exc).__name__}: {exc}"
            if has_of is not None and not (callable(has_of) and callable(get_of)):
                out["error"] = "has_key or get_feature is not callable; neither was called"
            elif has_of is not None:
                present = None
                try:
                    present = has_of(tag)
                except Exception as exc:
                    out["has_key_error"] = f"{type(exc).__name__}: {exc}"
                out["has_key"] = _tryfont_plain(present)
                if present is True:
                    try:
                        text = get_of(tag)
                    except Exception as exc:
                        out["get_feature_error"] = f"{type(exc).__name__}: {exc}"
                    else:
                        out["text_type"] = type(text).__name__
                        if isinstance(text, str):
                            out.update(_features_text_report(text, stage, contains))
                elif "has_key_error" not in out:
                    out["note_size"] = "has_key did not answer True, so get_feature was not called"
    len_after = _len()
    out.update(len_before=len_before, len_after=len_after,
               side_effect_detected=(len_before != len_after) if (len_before is not None and len_after is not None) else None,
               calls_so_far=_FEATURES["calls"], max_calls=_FEATURES_MAX,
               note="RESEARCH (K11): what font.features answers; compare with FontLab's Features panel. The size alone does not show whether "
                    "the feature code holds kerning that the master's kerning table lacks; nothing is changed or saved by Glyphbridge")
    return out


def _features_text_report(text, stage, tokens):
    """The report on one feature's code (a plain str): its size in every stage; stage=shape adds the line counts by kind and the
    first _FEATURES_HEAD characters, stage=lines the lines that name a token as a whole word. The text is never returned whole."""
    import re as _re
    lines = text.splitlines()
    out = {"chars": len(text), "lines": len(lines), "pos_lines": sum(1 for ln in lines if _re.search(r"\bpos\b", ln))}
    if stage == "shape":
        stripped = [ln.strip() for ln in lines]
        out["line_starts"] = {kind: sum(1 for ln in stripped if _re.match(pat, ln)) for kind, pat in _FEATURES_KINDS}
        out["head"] = text[:_FEATURES_HEAD]
    elif stage == "lines":
        counts, found = {}, {}
        for tok in tokens:
            pat = _re.compile(r"(?<![A-Za-z0-9._@-])" + _re.escape(tok) + r"(?![A-Za-z0-9._@-])")
            hits = [ln.strip() for ln in lines if pat.search(ln)]
            counts[tok] = len(hits)
            found[tok] = [(h[:_FEATURES_LINE_CUT] + " ...[cut]") if len(h) > _FEATURES_LINE_CUT else h for h in hits[:_FEATURES_LINES_SHOWN]]
        out.update(match_counts=counts, matches=found)
    return out


# --------------------------------------------------------------------------
# /debug/trypkgkern (v0.97) - RESEARCH: where does kerning made in FontLab's GUI live? Live tests 169 and 170: a class pair made in
# the KERNING panel of a new font was applied by FontLab but invisible to font.kerning (len 0). Probe 171 (names only) found
# flPackage.kerning, documented as 'fgKerning kerning([string master_name])'. This probe compares, for ONE pair, the package's kerning
# of ONE master with the legacy font.kerning. Calls, all reads: pkg.masters, pkg.master, pkg.kerning(master) ONCE, and on each of the
# two kerning objects len() before and after and get((a, b)) ONCE. Same one-font gate as /debug/trysync; at most _TRYPKGKERN_MAX
# requests per listener run, counted BEFORE pkg.kerning(master) is called. Not called, ever: autoKern, deleteGroups, getAllGroups,
# findGroup, update, release, remove, and on a kerning object set, remove, clear, add*, delete*, rename*, scale, setPlainPairs, asDict,
# getPlainPairs*, items, keys, values.
# v0.100: &mode=flags&flags=FF|FT|TF|TT (default mode tuple) asks get(((a, flag), (b, flag))) with F = False, T = True: the form
# fgKerning.get named itself when it refused a fontgate.fgKerningObjectPair (test 183: "Argument type must be Tuple(Tuple(string,
# bool), Tuple(string, bool)) or Tuple(string, string)!"; defect B). What the flag means (group or glyph) is what the tests find out.
# The v0.99 mode=glyph (that pair object) is removed; no fontgate object is built.
# v0.103: in mode=flags a side flagged T ("is a group", tests 186-187) may name a CLASS: only the name rule is checked for it, not
# whether such a glyph or class exists, and the reply lists that side under class_names_not_checked (P0.8 step R2).
# --------------------------------------------------------------------------

_TRYPKGKERN = {"calls": 0}
_TRYPKGKERN_MAX = 20
_TRYPKGKERN_MODES = ("tuple", "flags")
_TRYPKGKERN_FLAGS = {"FF": (False, False), "FT": (False, True), "TF": (True, False), "TT": (True, True)}


def _trypkgkern_len(kerning):
    try:
        n = len(kerning)
        return n if isinstance(n, int) and not isinstance(n, bool) else None
    except Exception:
        return None


def _trypkgkern_get(kerning, key):
    """ONE get(key) on one kerning object (key: the (a, b) tuple or one pair object), with len() before and after; a failure is
    reported as text, never raised."""
    len_before = _trypkgkern_len(kerning)
    value, call_error = None, None
    try:
        getter = kerning.get
        if not callable(getter):
            raise TypeError("get is not callable")
        value = getter(key)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    len_after = _trypkgkern_len(kerning)
    plain = isinstance(value, (int, float)) and not isinstance(value, bool)
    return {"call_error": call_error, "value_type": type(value).__name__, "value": value if plain else None,
            "len_before": len_before, "len_after": len_after,
            "side_effect_detected": (len_before != len_after) if (len_before is not None and len_after is not None) else None}


def debug_try_pkg_kern(a, b, master, go, mode="tuple", flags=None):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe calls flPackage.kerning(master) ONCE, then get((a, b)) once on it and once on font.kerning (reads); add &go=yes to run it",
                "calls_so_far": _TRYPKGKERN["calls"], "max_calls": _TRYPKGKERN_MAX}
    for label, nm in (("a", a), ("b", b)):
        if not isinstance(nm, str) or not (1 <= len(nm) <= 63) or any(ch not in _TRYCREATE_NAME_CHARS for ch in nm):
            return {"error": f"{label} must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    if mode not in _TRYPKGKERN_MODES:
        return {"error": 'mode must be "tuple" (get((a, b))) or "flags" (get(((a, flag), (b, flag))), with flags=FF, FT, TF or TT)'}
    if mode == "flags" and (not isinstance(flags, str) or flags not in _TRYPKGKERN_FLAGS):
        return {"error": "mode=flags needs flags=FF, FT, TF or TT (F = False, T = True; first letter for a, second for b)"}
    if mode == "tuple" and flags is not None:
        return {"error": "flags need mode=flags"}
    if master is not None and (not isinstance(master, str) or not (1 <= len(master) <= 63)
                               or any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in master)):
        return {"error": "master must be 1 to 63 characters without control characters (or left out: the package's current master)"}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYPKGKERN["calls"], "max_calls": _TRYPKGKERN_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    names = set(str(g.name) for g in font.glyphs)
    class_sides = []
    if mode == "flags":
        class_sides = [label for label, flag in zip(("a", "b"), _TRYPKGKERN_FLAGS[flags]) if flag]
    missing = [nm for label, nm in (("a", a), ("b", b)) if label not in class_sides and nm not in names]
    if missing:
        return {"open": True, "error": "no glyph with this name in the current font: " + ", ".join(repr(m) for m in missing),
                "calls_so_far": _TRYPKGKERN["calls"]}
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return {"open": True, "error": err, "calls_so_far": _TRYPKGKERN["calls"]}
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                "calls_so_far": _TRYPKGKERN["calls"]}
    masters = list(masters)
    current, err = _pkg_get(pkg, "master")
    current = current if isinstance(current, str) else None
    if master is None:
        if current is None:
            return {"open": True, "error": "no master given and the package's current master could not be read as a name" + (f" ({err})" if err else ""),
                    "masters": masters, "calls_so_far": _TRYPKGKERN["calls"]}
        master, source = current, "package.master"
    else:
        source = "query"
    if master not in masters:
        return {"open": True, "error": f"master {master!r} is not one of the package's masters", "masters": masters,
                "calls_so_far": _TRYPKGKERN["calls"]}
    if _TRYPKGKERN["calls"] >= _TRYPKGKERN_MAX:
        return {"open": True, "error": f"the limit of {_TRYPKGKERN_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYPKGKERN["calls"], "max_calls": _TRYPKGKERN_MAX}
    try:
        kerning_of = pkg.kerning
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYPKGKERN["calls"]}
    if not callable(kerning_of):
        return {"open": True, "error": "flPackage.kerning is not callable", "calls_so_far": _TRYPKGKERN["calls"]}
    _TRYPKGKERN["calls"] += 1        # counted BEFORE the call: whatever happens, it is on record
    key, key_text = (a, b), "(a, b)"
    if mode == "flags":
        flag_a, flag_b = _TRYPKGKERN_FLAGS[flags]
        key, key_text = ((a, flag_a), (b, flag_b)), f"((a, {flag_a}), (b, {flag_b}))"
    package_kerning, kerning_error = None, None
    try:
        package_kerning = kerning_of(master)
    except Exception as exc:
        kerning_error = f"{type(exc).__name__}: {exc}"
    package = {"call": f"flPackage.kerning(master).get({key_text})", "kerning_call_error": kerning_error,
               "object_type": type(package_kerning).__name__ if package_kerning is not None else None}
    if kerning_error is None and package_kerning is not None:
        package = dict(package, **_trypkgkern_get(package_kerning, key))
    try:
        legacy_kerning = font.kerning
    except Exception as exc:
        legacy = {"kerning_call_error": f"{type(exc).__name__}: {exc}"}
    else:
        legacy = _trypkgkern_get(legacy_kerning, key)
    legacy = dict(legacy, call=f"font.kerning.get({key_text})")
    out = {"open": True, "a": a, "b": b, "mode": mode, "masters": masters, "current_master": current, "master_used": master, "master_source": source,
           "package": package, "legacy": legacy, "calls_so_far": _TRYPKGKERN["calls"], "max_calls": _TRYPKGKERN_MAX,
           "note": "RESEARCH: compare both values with FontLab's KERNING panel; nothing is changed or saved by Glyphbridge"}
    if mode == "flags":
        out = dict(out, flags=flags)
    if class_sides:
        out = dict(out, class_names_not_checked=class_sides)
    return out


# --------------------------------------------------------------------------
# /debug/trysetkern (v0.122) - RESEARCH, WRITES: can a kerning pair be set through the API? Names-only test 542: fgKerning.set is
# documented as "int set(fgKerningObjectPair / tuple('name1', 'name2'), double) - set kerning value"; remove, setPlainPairs, clear
# and addGroup have no docstring. GATED (go=yes); the same one-font gate as /debug/trysync; at most _TRYSETKERN_MAX requests per
# listener run, counted BEFORE the set call. Both names must be glyph names of the current font, and neither may be the name of any
# group that ONE pkg.getAllGroups() lists (defect B: a plain name tuple prefers a class of that name); an unreadable group list
# refuses. The value is a finite number with |value| <= the package's upm. Calls: pkg.masters, pkg.master, pkg.upm,
# pkg.getAllGroups() once, pkg.kerning(current master) once, on that table len() and get(((a, False), (b, False))) before and after,
# and set(key, value) ONCE:
#   &form=tuple    set((a, b), value), the documented form
#   &form=flags    set(((a, False), (b, False)), value), the form get accepts (186-188); not in set's docstring
# Not called, ever: remove, clear, setPlainPairs, add*, delete*, rename*, scale, asDict, getPlainPairs*, items, keys, values, has_key,
# font.update(), glyph.update(), fontlab.Update(); no save. Whether FontLab's KERNING panel shows the pair is what the live test checks.
# v0.193 (class-write research, CW): &left=glyph|class&right=glyph|class, default glyph. A class side needs form=flags and is sent as
# (name, True): set(((a, isClass), (b, isClass)), value); get() reads that same key before and after. Before the first kerning call it
# must name a kerning group of the ONE getAllGroups() (flag True); after it, the master's kerning groups (kerning.groups, never called)
# get len() and ONE items() (_kgr_from_items, the reader of /kerning/groups), and the group must be confirmed by both sources
# (_kgr_group) with a side that fits: KernLeft or KernBothSide on the left, KernRight or KernBothSide on the right. Anything else
# refuses with nothing set. The reply adds left, right, classes and the groups' len() before and after. A glyph side is checked as before.
# --------------------------------------------------------------------------

_TRYSETKERN = {"calls": 0}
_TRYSETKERN_MAX = 10
_TRYSETKERN_FORMS = ("tuple", "flags")


def _trysetkern_value(text):
    """(number, None) or (None, error text): the value from the query, a finite decimal number."""
    import math as _math
    if not isinstance(text, str) or not (1 <= len(text) <= 20) or any(ch not in "0123456789.-+" for ch in text):
        return None, "value must be a decimal number of 1 to 20 characters from 0-9 . - +"
    try:
        value = float(text)
    except ValueError:
        return None, f"value {text!r} is not a number"
    if not _math.isfinite(value):
        return None, "value must be a finite number"
    return (int(value) if value == int(value) else value), None


_TRYKERN_KINDS = ("glyph", "class")                                  # v0.193: what each side of a probe's pair names
_TRYKERN_SIDE_FITS = {"left": ("left", "both"), "right": ("right", "both")}   # the group sides that may stand on each side of a pair


def _trysetkern_group_names(pkg):
    """(set of every group name, {kerning group name: {"id", "members"}}, kerning group names listed twice, None) or (None, None, None,
    error text), from ONE pkg.getAllGroups(). Every group counts for the name set, kerning group or not: the probes refuse a glyph name
    that any group also carries. Only a real list or tuple of 5-item entries with a str name is accepted; any other shape refuses, since
    then a collision cannot be ruled out. The kerning groups (flag True, v0.193) are what a class side is checked against."""
    try:
        getter = pkg.getAllGroups
        if not callable(getter):
            return None, None, None, "flPackage.getAllGroups is not callable"
        groups = getter()
    except Exception as exc:
        return None, None, None, f"flPackage.getAllGroups() failed ({type(exc).__name__}: {exc})"
    if groups is None:
        return set(), {}, set(), None                # documented as ".../Nothing": a font without groups
    if not isinstance(groups, (list, tuple)):
        return None, None, None, f"flPackage.getAllGroups() returned a {type(groups).__name__}, not a list"
    for entry in groups:
        if not isinstance(entry, (list, tuple)) or len(entry) != 5 or not isinstance(entry[1], str):
            return None, None, None, "flPackage.getAllGroups() returned an entry of an unknown shape, so a name collision cannot be ruled out"
    kern, twice = {}, set()
    for entry in groups:
        if entry[0] is not True:
            continue
        if entry[1] in kern:
            twice |= {entry[1]}
        kern[entry[1]] = {"id": entry[2] if type(entry[2]) is int else None, "members": _kgr_names(entry[4])}
    return {entry[1] for entry in groups}, kern, twice, None


def _trykern_sides_ok(a, b, left, right, form, font_names, all_names, kern, verb):
    """None, or the error text that refuses a probe request before any kerning call (v0.193). A glyph side names a glyph of the font
    that no group carries (defect B); a class side names a kerning group of FontLab's class list and needs form=flags."""
    if left not in _TRYKERN_KINDS or right not in _TRYKERN_KINDS:
        return 'left and right must each be "glyph" or "class"'
    if form == "tuple" and "class" in (left, right):
        return "form=tuple names two glyphs; a class side needs form=flags"
    for side, nm, kind in (("left", a, left), ("right", b, right)):
        if kind == "glyph" and nm in all_names:
            return f"a group of the font has the same name as {nm!r} (defect B: a plain name pair may then mean the group); nothing was {verb}"
        if kind == "class" and nm not in kern:
            what = "is a class of the font but not a kerning group" if nm in all_names else "is not the name of any group of the font"
            return f"the {side} side {nm!r} {what}; nothing was {verb}"
    return None


def _trykern_confirm_classes(kerning, a, b, left, right, kern, list_twice):
    """(classes, container, groups len before, None) or (classes, container, groups len before, error text), v0.193. For the class
    sides of a probe request: the master's kerning groups (kerning.groups, never called), its len(), then ONE items() through
    _kgr_from_items; each class must be confirmed by both sources (_kgr_group) and its side must fit the side of the pair it stands on."""
    classes = {}
    try:
        container = kerning.groups
    except Exception as exc:
        return classes, None, None, f"the master's kerning groups are not reachable ({type(exc).__name__}: {exc})"
    if callable(container):
        return classes, None, None, "the master's kerning groups attribute is callable; it was not called"
    groups_len = _trypkgkern_len(container)
    from_items, items_twice, _malformed, err = _kgr_from_items(container)
    if err is not None:
        return classes, container, groups_len, err
    for side, nm, kind in (("left", a, left), ("right", b, right)):
        if kind != "class":
            continue
        g = _kgr_group(nm, from_items, kern, None, items_twice | list_twice)
        classes[side] = {k: g[k] for k in ("name", "side", "fontlab_side", "members", "id", "confirmed", "mismatch") if k in g}
        if g.get("confirmed") is not True:
            return classes, container, groups_len, f"the kerning group {nm!r} is not confirmed by both of FontLab's sources ({g.get('mismatch')})"
        if g.get("side") not in _TRYKERN_SIDE_FITS[side]:
            return classes, container, groups_len, f"the kerning group {nm!r} is a {g.get('side')} group, so it cannot stand on the {side} side of a pair"
    return classes, container, groups_len, None


def debug_try_set_kern(a, b, value, form, go, left="glyph", right="glyph"):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe WRITES one kerning pair: flPackage.kerning(master).set(key, value) ONCE, with get() before and after; "
                         "add &go=yes to run it", "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX}
    for label, nm in (("a", a), ("b", b)):
        if not _kern_name_ok(nm):
            return {"error": f"{label} must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    if form not in _TRYSETKERN_FORMS:
        return {"error": 'form must be "tuple" (set((a, b), value)) or "flags" (set(((a, isClass), (b, isClass)), value))'}
    if left not in _TRYKERN_KINDS or right not in _TRYKERN_KINDS or (form == "tuple" and "class" in (left, right)):
        return {"error": _trykern_sides_ok(a, b, left, right, form, set(), set(), {}, "set")}
    number, err = _trysetkern_value(value)
    if err is not None:
        return {"error": err}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    names = set(str(g.name) for g in font.glyphs)
    missing = [nm for nm, kind in ((a, left), (b, right)) if kind == "glyph" and nm not in names]
    if missing:
        return {"open": True, "error": "no glyph with this name in the current font: " + ", ".join(repr(m) for m in missing),
                "calls_so_far": _TRYSETKERN["calls"]}
    upm, err = _pkg_get(pkg, "upm")
    if err is not None or type(upm) not in (int, float) or not upm > 0:
        return {"open": True, "error": "the package's upm could not be read as a positive number" + (f" ({err})" if err else f" ({upm!r})"),
                "calls_so_far": _TRYSETKERN["calls"]}
    if abs(number) > upm:
        return {"open": True, "error": f"value {number} is larger than the font's {upm} units per em, either way; nothing was set",
                "calls_so_far": _TRYSETKERN["calls"]}
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return {"open": True, "error": err, "calls_so_far": _TRYSETKERN["calls"]}
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                "calls_so_far": _TRYSETKERN["calls"]}
    current, err = _pkg_get(pkg, "master")
    if not isinstance(current, str) or current not in masters:
        return {"open": True, "error": "the package's current master could not be read as one of its masters" + (f" ({err})" if err else ""),
                "masters": list(masters), "calls_so_far": _TRYSETKERN["calls"]}
    if _TRYSETKERN["calls"] >= _TRYSETKERN_MAX:
        return {"open": True, "error": f"the limit of {_TRYSETKERN_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX}
    groups, kern, kern_twice, err = _trysetkern_group_names(pkg)
    if err is not None:
        return {"open": True, "error": err + "; nothing was set", "calls_so_far": _TRYSETKERN["calls"]}
    why = _trykern_sides_ok(a, b, left, right, form, names, groups, kern, "set")
    if why is not None:
        return {"open": True, "error": why, "calls_so_far": _TRYSETKERN["calls"]}
    try:
        kerning_of = pkg.kerning
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYSETKERN["calls"]}
    if not callable(kerning_of):
        return {"open": True, "error": "flPackage.kerning is not callable", "calls_so_far": _TRYSETKERN["calls"]}
    _TRYSETKERN["calls"] += 1        # counted BEFORE the first kerning call: whatever happens, it is on record
    try:
        kerning = kerning_of(current)
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning(master) failed: {type(exc).__name__}: {exc}", "master_used": current,
                "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX}
    with_class = "class" in (left, right)
    classes, container, groups_len_before = {}, None, None
    if with_class:
        classes, container, groups_len_before, why = _trykern_confirm_classes(kerning, a, b, left, right, kern, kern_twice)
        if why is not None:
            return {"open": True, "error": why + "; nothing was set", "left": left, "right": right, "classes": classes, "master_used": current,
                    "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX}
    exact = ((a, left == "class"), (b, right == "class"))
    before = _trypkgkern_get(kerning, exact)
    key, key_text = ((a, b), "(a, b)") if form == "tuple" else (exact, f"((a, {left == 'class'}), (b, {right == 'class'}))")
    returned, set_error = None, None
    if before["call_error"] is not None:
        set_error = "not called: the read before it failed, so the result could not be checked"
    else:
        try:
            setter = kerning.set
            if not callable(setter):
                raise TypeError("set is not callable")
            returned = setter(key, float(number))
        except Exception as exc:
            set_error = f"{type(exc).__name__}: {exc}"
    after = _trypkgkern_get(kerning, exact)
    len_before, len_after = before["len_before"], after["len_after"]
    out = {"open": True, "a": a, "b": b, "form": form, "value_asked": number, "units_per_em": upm, "master_used": current,
           "masters": list(masters), "call": f"flPackage.kerning(master).set({key_text}, value)", "set_error": set_error,
           "set_returned_type": type(returned).__name__, "set_returned": _tryfont_plain(returned),
           "exact_before": {k: before[k] for k in ("call_error", "value_type", "value")},
           "exact_after": {k: after[k] for k in ("call_error", "value_type", "value")},
           "read_back_matches": set_error is None and after["call_error"] is None and after["value"] == number,
           "len_before": len_before, "len_after": len_after,
           "table_size_changed": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
           "calls_so_far": _TRYSETKERN["calls"], "max_calls": _TRYSETKERN_MAX,
           "note": "RESEARCH: the font in memory may have changed. Compare with FontLab's KERNING panel and a text line; nothing is saved by Glyphbridge"}
    if with_class:
        out = dict(out, left=left, right=right, classes=classes, groups_len_before=groups_len_before, groups_len_after=_trypkgkern_len(container))
    return out


# --------------------------------------------------------------------------
# /debug/trydelkern (v0.191) - RESEARCH, WRITES: can one kerning pair be removed through the API? Names-only test 1380: fgKerning.remove
# has no docstring; get and set are documented as taking an fgKerningObjectPair or a tuple('name1', 'name2'). GATED (go=yes); the same
# one-font gate, name checks, group-name refusal (defect B) and master reading as /debug/trysetkern; at most _TRYDELKERN_MAX requests per
# listener run, counted BEFORE the first kerning call. Calls: pkg.masters, pkg.master, pkg.getAllGroups() once, pkg.kerning(current
# master) once, on that table len() and get(((a, False), (b, False))) before and after, and remove(key) ONCE:
#   &form=tuple    remove((a, b))
#   &form=flags    remove(((a, False), (b, False))), the form get and set accept (186-188, 564)
# remove is not called when the read before it failed. 'removed' is true only when remove raised nothing, the entry was a number
# before, reads None after, and len() dropped by exactly 1. Not called, ever: set, clear, setPlainPairs, add*, delete*, rename*, scale,
# asDict, getPlainPairs*, items, keys, values, has_key, groups, font.update(), glyph.update(), fontlab.Update(), the mark
# (notifyChangesApplied) and the panel refresh (notifyPackageContentUpdated); no save.
# v0.193: &left / &right as /debug/trysetkern, with the same class checks: remove(((a, isClass), (b, isClass))), and get() of that key.
# --------------------------------------------------------------------------

_TRYDELKERN = {"calls": 0}
_TRYDELKERN_MAX = 10
_TRYDELKERN_FORMS = ("tuple", "flags")


def debug_try_del_kern(a, b, form, go, left="glyph", right="glyph"):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe WRITES: it removes one kerning pair, flPackage.kerning(master).remove(key) ONCE, with get() before and "
                         "after; add &go=yes to run it", "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX}
    for label, nm in (("a", a), ("b", b)):
        if not _kern_name_ok(nm):
            return {"error": f"{label} must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    if form not in _TRYDELKERN_FORMS:
        return {"error": 'form must be "tuple" (remove((a, b))) or "flags" (remove(((a, isClass), (b, isClass))))'}
    if left not in _TRYKERN_KINDS or right not in _TRYKERN_KINDS or (form == "tuple" and "class" in (left, right)):
        return {"error": _trykern_sides_ok(a, b, left, right, form, set(), set(), {}, "removed")}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    names = set(str(g.name) for g in font.glyphs)
    missing = [nm for nm, kind in ((a, left), (b, right)) if kind == "glyph" and nm not in names]
    if missing:
        return {"open": True, "error": "no glyph with this name in the current font: " + ", ".join(repr(m) for m in missing),
                "calls_so_far": _TRYDELKERN["calls"]}
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return {"open": True, "error": err, "calls_so_far": _TRYDELKERN["calls"]}
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                "calls_so_far": _TRYDELKERN["calls"]}
    current, err = _pkg_get(pkg, "master")
    if not isinstance(current, str) or current not in masters:
        return {"open": True, "error": "the package's current master could not be read as one of its masters" + (f" ({err})" if err else ""),
                "masters": list(masters), "calls_so_far": _TRYDELKERN["calls"]}
    if _TRYDELKERN["calls"] >= _TRYDELKERN_MAX:
        return {"open": True, "error": f"the limit of {_TRYDELKERN_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX}
    groups, kern, kern_twice, err = _trysetkern_group_names(pkg)
    if err is not None:
        return {"open": True, "error": err + "; nothing was removed", "calls_so_far": _TRYDELKERN["calls"]}
    why = _trykern_sides_ok(a, b, left, right, form, names, groups, kern, "removed")
    if why is not None:
        return {"open": True, "error": why, "calls_so_far": _TRYDELKERN["calls"]}
    try:
        kerning_of = pkg.kerning
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYDELKERN["calls"]}
    if not callable(kerning_of):
        return {"open": True, "error": "flPackage.kerning is not callable", "calls_so_far": _TRYDELKERN["calls"]}
    _TRYDELKERN["calls"] += 1        # counted BEFORE the first kerning call: whatever happens, it is on record
    try:
        kerning = kerning_of(current)
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning(master) failed: {type(exc).__name__}: {exc}", "master_used": current,
                "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX}
    with_class = "class" in (left, right)
    classes, container, groups_len_before = {}, None, None
    if with_class:
        classes, container, groups_len_before, why = _trykern_confirm_classes(kerning, a, b, left, right, kern, kern_twice)
        if why is not None:
            return {"open": True, "error": why + "; nothing was removed", "left": left, "right": right, "classes": classes, "master_used": current,
                    "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX}
    exact = ((a, left == "class"), (b, right == "class"))
    before = _trypkgkern_get(kerning, exact)
    key, key_text = ((a, b), "(a, b)") if form == "tuple" else (exact, f"((a, {left == 'class'}), (b, {right == 'class'}))")
    returned, remove_error, remove_called = None, None, False
    if before["call_error"] is not None:
        remove_error = "not called: the read before it failed, so the result could not be checked"
    else:
        try:
            remover = kerning.remove
            if not callable(remover):
                raise TypeError("remove is not callable")
            remove_called = True
            returned = remover(key)
        except Exception as exc:
            remove_error = f"{type(exc).__name__}: {exc}"
    after = _trypkgkern_get(kerning, exact)
    len_before, len_after = before["len_before"], after["len_after"]
    removed = (remove_error is None and before["value"] is not None and after["call_error"] is None and after["value_type"] == "NoneType"
               and type(len_before) is int and type(len_after) is int and len_after == len_before - 1)
    out = {"open": True, "a": a, "b": b, "form": form, "master_used": current, "masters": list(masters),
           "call": f"flPackage.kerning(master).remove({key_text})", "remove_called": remove_called, "remove_error": remove_error,
           "remove_returned_type": type(returned).__name__, "remove_returned": _tryfont_plain(returned),
           "exact_before": {k: before[k] for k in ("call_error", "value_type", "value")},
           "exact_after": {k: after[k] for k in ("call_error", "value_type", "value")},
           "removed": removed, "len_before": len_before, "len_after": len_after,
           "table_size_changed": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
           "calls_so_far": _TRYDELKERN["calls"], "max_calls": _TRYDELKERN_MAX,
           "note": "RESEARCH: the font in memory may have changed. Compare with FontLab's KERNING panel and a text line; the font is not "
                   "marked as changed and the panel is not asked to refresh; nothing is saved by Glyphbridge"}
    if with_class:
        out = dict(out, left=left, right=right, classes=classes, groups_len_before=groups_len_before, groups_len_after=_trypkgkern_len(container))
    return out


# --------------------------------------------------------------------------
# /debug/trykernrefresh (v0.123) - RESEARCH: can the KERNING panel be made to show a pair written by /debug/trysetkern? Live 544-551:
# FontLab applies such a pair in a text line, but the panel lists only pairs made in the GUI, also after it was reopened. Names-only
# test 552: fontlab.Update is documented as "Update object and it's visual representations ... Update([fgGlyph|fgFont|flObject
# object])", and flPackage.kerningContainer as "flObject kerningContainer()". GATED (go=yes); the same one-font gate as /debug/trysync;
# at most _TRYKERNREFRESH_MAX requests per listener run, counted BEFORE kerningContainer() is called. Every stage reads pkg.masters,
# pkg.master, len() of pkg.kerning(current master) and the isChanged / hasChanges flags of the package and the container, before and
# after, and calls pkg.kerningContainer() ONCE:
#   stage=container   nothing more: the container's type, isNull, id, name and public names
#   stage=update      then fontlab.Update(container) ONCE, with that one argument
#   stage=changed     then container.changed() ONCE
# Not called, ever: Update() without an argument, UpdateAll, Update with the font or the package, container.update, remove, release,
# setFlag, clearFlag*, the history calls, any kerning setter, font.update(), glyph.update(); no save.
# --------------------------------------------------------------------------

_TRYKERNREFRESH = {"calls": 0}
_TRYKERNREFRESH_MAX = 6
_TRYKERNREFRESH_STAGES = ("container", "update", "changed")


def _trykernrefresh_flags(obj):
    """The isChanged and hasChanges flags of one object, each read once; a failed read is reported as text."""
    out = {}
    for attr in ("isChanged", "hasChanges"):
        value, err = _pkg_get(obj, attr)
        out[attr] = err if err is not None else _tryfont_plain(value)
    return out


def debug_try_kern_refresh(stage, go):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe calls flPackage.kerningContainer() ONCE and, in stage=update, fontlab.Update(container) or, in "
                         "stage=changed, container.changed(); add &go=yes to run it",
                "calls_so_far": _TRYKERNREFRESH["calls"], "max_calls": _TRYKERNREFRESH_MAX}
    if stage not in _TRYKERNREFRESH_STAGES:
        return {"error": 'stage must be "container", "update" or "changed"'}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYKERNREFRESH["calls"], "max_calls": _TRYKERNREFRESH_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return {"open": True, "error": err, "calls_so_far": _TRYKERNREFRESH["calls"]}
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                "calls_so_far": _TRYKERNREFRESH["calls"]}
    current, err = _pkg_get(pkg, "master")
    if not isinstance(current, str) or current not in masters:
        return {"open": True, "error": "the package's current master could not be read as one of its masters" + (f" ({err})" if err else ""),
                "masters": list(masters), "calls_so_far": _TRYKERNREFRESH["calls"]}
    updater = None
    if stage == "update":
        updater = getattr(mod, "Update", None)
        if not callable(updater):
            return {"open": True, "error": "fontlab.Update is missing or not callable; nothing was called", "calls_so_far": _TRYKERNREFRESH["calls"]}
    if _TRYKERNREFRESH["calls"] >= _TRYKERNREFRESH_MAX:
        return {"open": True, "error": f"the limit of {_TRYKERNREFRESH_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYKERNREFRESH["calls"], "max_calls": _TRYKERNREFRESH_MAX}
    try:
        kerning_of = pkg.kerning
        container_of = pkg.kerningContainer
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning / kerningContainer not reachable: {type(exc).__name__}: {exc}",
                "calls_so_far": _TRYKERNREFRESH["calls"]}
    if not (callable(kerning_of) and callable(container_of)):
        return {"open": True, "error": "flPackage.kerning or kerningContainer is not callable; nothing was called", "calls_so_far": _TRYKERNREFRESH["calls"]}
    _TRYKERNREFRESH["calls"] += 1        # counted BEFORE the first call: whatever happens, it is on record
    out = {"open": True, "stage": stage, "master_used": current}
    try:
        kerning = kerning_of(current)
    except Exception as exc:
        kerning = None
        out["kerning_error"] = f"flPackage.kerning(master) failed: {type(exc).__name__}: {exc}"
    len_before = _trypkgkern_len(kerning) if kerning is not None else None
    out["package_flags_before"] = _trykernrefresh_flags(pkg)
    try:
        container = container_of()
    except Exception as exc:
        out.update(error=f"flPackage.kerningContainer() failed: {type(exc).__name__}: {exc}", calls_so_far=_TRYKERNREFRESH["calls"],
                   max_calls=_TRYKERNREFRESH_MAX)
        return out
    out["container_type"] = type(container).__name__
    if container is None:
        out.update(error="flPackage.kerningContainer() returned None; nothing more was called", calls_so_far=_TRYKERNREFRESH["calls"],
                   max_calls=_TRYKERNREFRESH_MAX)
        return out
    is_null, err = _pkg_get(container, "isNull")
    out["container_isNull"] = err if err is not None else _tryfont_plain(is_null)
    for attr in ("id", "name"):
        value, err = _pkg_get(container, attr)
        out["container_" + attr] = err if err is not None else _tryfont_plain(value)
    try:
        out["container_public_names"] = [n for n in dir(container) if not n.startswith("_")]
    except Exception as exc:
        out["container_public_names"] = f"<dir failed: {type(exc).__name__}: {exc}>"
    out["container_flags_before"] = _trykernrefresh_flags(container)
    if stage != "container":
        if is_null is not False:
            out["call_error"] = "not called: the container is null or its state is unknown"
        else:
            try:
                if stage == "update":
                    out["call"] = "fontlab.Update(container)"
                    returned = updater(container)
                else:
                    out["call"] = "container.changed()"
                    mark = container.changed
                    if not callable(mark):
                        raise TypeError("changed is not callable")
                    returned = mark()
            except Exception as exc:
                out["call_error"] = f"{type(exc).__name__}: {exc}"
            else:
                out.update(call_error=None, returned_type=type(returned).__name__, returned=_tryfont_plain(returned))
        out["container_flags_after"] = _trykernrefresh_flags(container)
    len_after = _trypkgkern_len(kerning) if kerning is not None else None
    out.update(package_flags_after=_trykernrefresh_flags(pkg), kerning_len_before=len_before, kerning_len_after=len_after,
               table_size_changed=(len_before != len_after) if (len_before is not None and len_after is not None) else None,
               calls_so_far=_TRYKERNREFRESH["calls"], max_calls=_TRYKERNREFRESH_MAX,
               note="RESEARCH: compare FontLab's KERNING panel before and after; nothing is saved by Glyphbridge")
    return out


# --------------------------------------------------------------------------
# /debug/trykerngroupedit (v0.199) - RESEARCH, WRITES: can a kerning group be renamed or removed through the modern API? Names-only
# tests 1499-1504: the master's kerning groups (flPackage.kerning(master).groups, an fgKerningGroups) document
# rename('oldGroupName', 'newGroupName') -> bool/Nothing and remove('groupName'[, deleteDependentKerningPairs = false]). GATED (go=yes);
# the one-font gate and master reading of /debug/trydelkern; at most _TRYKGEDIT_MAX requests per listener run, counted BEFORE the first
# kerning call.
#   &op=rename&name=OLD&new=NEW            container.rename(OLD, NEW) ONCE
#   &op=remove&name=N&pairs=keep|delete    container.remove(N) ONCE (keep), or container.remove(N, True) ONCE (delete)
#   &glyph=G (optional)                    the group's own class entry against glyph G, read with get() before and after: the group on
#                                          its side, ((N, True), (G, False)) for a left or both group, ((G, False), (N, True)) for a right
#                                          one; a rename reads it under the old name before and under both names after
# Refused before any kerning call: a bad name, an unknown op or pairs, NEW the same as OLD, NEW already the name of a glyph of the font
# (defect B) or of any group of the font, G not a glyph of the font. Refused before the edit: a group not confirmed by both items() and
# getAllGroups(). Calls: pkg.masters, pkg.master, pkg.getAllGroups() before and after, pkg.kerning(current master) once, kerning.groups
# (never called), len() of the table and of the container before and after, container.items() before and after, kerning.get(key) for
# the entries, and the ONE edit call. The verdicts come from the re-read only, never from the returned value. Not called, ever:
# subscripts or del on any native object, clear, the legacy addGroup / deleteGroup / deleteAllGroups / renameGroup,
# flPackage.deleteGroups, any kerning setter or remove, keys, values, has_key, asDict, font.update(), fontlab.Update(), the mark
# (notifyChangesApplied) and the panel refresh (notifyPackageContentUpdated); no save.
# --------------------------------------------------------------------------

_TRYKGEDIT = {"calls": 0}
_TRYKGEDIT_MAX = 10
_TRYKGEDIT_OPS = ("rename", "remove")
_TRYKGEDIT_PAIRS = ("keep", "delete")


def _trykgedit_key(name, glyph, side):
    """The exact class entry of group `name` against `glyph`: the group on the left for a left or both group, else on the right."""
    return ((name, True), (glyph, False)) if side in ("left", "both") else ((glyph, False), (name, True))


def _trykgedit_entry(kerning, key):
    """ONE get(key) on the table, as plain facts; a failure is reported as text, never raised."""
    r = _trypkgkern_get(kerning, key)
    return {k: r[k] for k in ("call_error", "value_type", "value")}


def debug_try_kern_group_edit(op, name, new, pairs, glyph, go):
    import sys as _sys
    if go != "yes":
        return {"error": "this probe WRITES: it renames or removes one kerning group, flPackage.kerning(master).groups.rename(old, new) or "
                         ".remove(name[, True]) ONCE, with items(), getAllGroups() and len() before and after; add &go=yes to run it",
                "calls_so_far": _TRYKGEDIT["calls"], "max_calls": _TRYKGEDIT_MAX}
    if op not in _TRYKGEDIT_OPS:
        return {"error": 'op must be "rename" or "remove"'}
    if not _kern_name_ok(name):
        return {"error": "name must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    verb = "renamed" if op == "rename" else "removed"
    if op == "rename":
        if pairs:
            return {"error": "pairs belongs to op=remove"}
        if not _kern_name_ok(new):
            return {"error": "new must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
        if new == name:
            return {"error": "new is the same as name; nothing to rename"}
    else:
        if new:
            return {"error": "new belongs to op=rename"}
        if pairs not in _TRYKGEDIT_PAIRS:
            return {"error": 'pairs must be "keep" (remove(name)) or "delete" (remove(name, True))'}
    if glyph and not _kern_name_ok(glyph):
        return {"error": "glyph must be 1 to 63 characters from A-Z a-z 0-9 . _ -"}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"error": why, "calls_so_far": _TRYKGEDIT["calls"], "max_calls": _TRYKGEDIT_MAX}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    names = set(str(g.name) for g in font.glyphs)
    if glyph and glyph not in names:
        return {"open": True, "error": f"no glyph with this name in the current font: {glyph!r}", "calls_so_far": _TRYKGEDIT["calls"]}
    if op == "rename" and new in names:
        return {"open": True, "error": f"new {new!r} is the name of a glyph of the font (defect B: a plain name pair may then mean the group); "
                                       "nothing was renamed", "calls_so_far": _TRYKGEDIT["calls"]}
    masters, err = _pkg_get(pkg, "masters")
    if err is not None:
        return {"open": True, "error": err, "calls_so_far": _TRYKGEDIT["calls"]}
    if not isinstance(masters, (list, tuple)) or not all(isinstance(m, str) for m in masters):
        return {"open": True, "error": f"the package's masters are not a plain list of names ({type(masters).__name__}); nothing was called",
                "calls_so_far": _TRYKGEDIT["calls"]}
    current, err = _pkg_get(pkg, "master")
    if not isinstance(current, str) or current not in masters:
        return {"open": True, "error": "the package's current master could not be read as one of its masters" + (f" ({err})" if err else ""),
                "masters": list(masters), "calls_so_far": _TRYKGEDIT["calls"]}
    if _TRYKGEDIT["calls"] >= _TRYKGEDIT_MAX:
        return {"open": True, "error": f"the limit of {_TRYKGEDIT_MAX} requests per listener run is used up; restart the listener to continue",
                "calls_so_far": _TRYKGEDIT["calls"], "max_calls": _TRYKGEDIT_MAX}
    all_before, kern_before, twice_before, err = _trysetkern_group_names(pkg)
    if err is not None:
        return {"open": True, "error": err + f"; nothing was {verb}", "calls_so_far": _TRYKGEDIT["calls"]}
    if op == "rename" and new in all_before:
        return {"open": True, "error": f"new {new!r} is already the name of a group of the font; nothing was renamed",
                "calls_so_far": _TRYKGEDIT["calls"]}
    try:
        kerning_of = pkg.kerning
    except Exception as exc:
        return {"open": True, "error": f"flPackage.kerning not reachable: {type(exc).__name__}: {exc}", "calls_so_far": _TRYKGEDIT["calls"]}
    if not callable(kerning_of):
        return {"open": True, "error": "flPackage.kerning is not callable", "calls_so_far": _TRYKGEDIT["calls"]}
    _TRYKGEDIT["calls"] += 1        # counted BEFORE the first kerning call: whatever happens, it is on record
    cnt = {"calls_so_far": _TRYKGEDIT["calls"], "max_calls": _TRYKGEDIT_MAX}
    try:
        kerning = kerning_of(current)
    except Exception as exc:
        return dict(cnt, open=True, error=f"flPackage.kerning(master) failed: {type(exc).__name__}: {exc}", master_used=current)
    try:
        container = kerning.groups
    except Exception as exc:
        return dict(cnt, open=True, error=f"the master's kerning groups are not reachable ({type(exc).__name__}: {exc}); nothing was {verb}",
                    master_used=current)
    if callable(container):
        return dict(cnt, open=True, error=f"the master's kerning groups attribute is callable; it was not called; nothing was {verb}",
                    master_used=current)
    table_len_before, groups_len_before = _trypkgkern_len(kerning), _trypkgkern_len(container)
    items_before, items_twice, _malformed, err = _kgr_from_items(container)
    if err is not None:
        return dict(cnt, open=True, error=err + f"; nothing was {verb}", master_used=current)
    group = _kgr_group(name, items_before, kern_before, None, items_twice | twice_before)
    if group.get("confirmed") is not True:
        why = group.get("mismatch") or "it is not a kerning group of the font"
        if name not in items_before and name not in kern_before:
            why = ("it is a class of the font but not a kerning group" if name in all_before else "it is not the name of any group of the font")
        return dict(cnt, open=True, error=f"the kerning group {name!r} is not confirmed by both of FontLab's sources ({why}); nothing was {verb}",
                    group_before=group if (name in items_before or name in kern_before) else None, master_used=current)
    side = group.get("side")
    entry_before = _trykgedit_entry(kerning, _trykgedit_key(name, glyph, side)) if glyph else None
    returned, call_error, called = None, None, False
    try:
        if op == "rename":
            editor = container.rename
            if not callable(editor):
                raise TypeError("rename is not callable")
            called = True
            returned = editor(name, new)
        else:
            editor = container.remove
            if not callable(editor):
                raise TypeError("remove is not callable")
            called = True
            returned = editor(name) if pairs == "keep" else editor(name, True)
    except Exception as exc:
        call_error = f"{type(exc).__name__}: {exc}"
    table_len_after, groups_len_after = _trypkgkern_len(kerning), _trypkgkern_len(container)
    items_after, items_twice_after, _malformed, items_err_after = _kgr_from_items(container)
    _all_after, kern_after, twice_after, list_err_after = _trysetkern_group_names(pkg)
    readable = items_after is not None and kern_after is not None
    old_gone = readable and name not in items_after and name not in kern_after
    ints = all(type(n) is int for n in (table_len_before, table_len_after, groups_len_before, groups_len_after))
    out = dict(open=True, op=op, name=name, master_used=current, masters=list(masters), called=called, call_error=call_error,
               returned_type=type(returned).__name__, returned=_tryfont_plain(returned), group_before=group,
               table_len_before=table_len_before, table_len_after=table_len_after,
               groups_len_before=groups_len_before, groups_len_after=groups_len_after,
               kerning_groups_listed_before=len(kern_before), kerning_groups_listed_after=len(kern_after) if kern_after is not None else None,
               items_error_after=items_err_after, class_list_error_after=list_err_after, old_name_gone=old_gone)
    if op == "rename":
        new_in_items = (new in items_after) if items_after is not None else None
        new_in_list = (new in kern_after) if kern_after is not None else None
        group_after = None
        if items_after is not None and (new_in_items or new_in_list):       # items() unreadable: no verdict on the new name's group
            group_after = _kgr_group(new, items_after, kern_after, list_err_after, (items_twice_after or set()) | (twice_after or set()))
        out = dict(out, new=new, call=f"flPackage.kerning(master).groups.rename({name!r}, {new!r})", new_name_in_items=new_in_items,
                   new_name_in_class_list=new_in_list, group_after=group_after)
        out["renamed"] = bool(call_error is None and old_gone and group_after is not None and group_after.get("confirmed") is True
                              and sorted(group_after.get("members") or []) == sorted(group.get("members") or [])
                              and group_after.get("side") == side and group_after.get("id") == group.get("id")
                              and ints and table_len_after == table_len_before and groups_len_after == groups_len_before)
    else:
        out = dict(out, pairs=pairs, call=f"flPackage.kerning(master).groups.remove({name!r}" + (")" if pairs == "keep" else ", True)"),
                   still_in_items=(name in items_after) if items_after is not None else None,
                   still_in_class_list=(name in kern_after) if kern_after is not None else None,
                   table_entries_removed=(table_len_before - table_len_after) if ints else None)
        out["removed"] = bool(call_error is None and old_gone and ints and groups_len_after == groups_len_before - 1)
    if glyph:
        out = dict(out, glyph=glyph, entry_key_side=side, entry_before=entry_before,
                   entry_after_old_name=_trykgedit_entry(kerning, _trykgedit_key(name, glyph, side)))
        before_value = entry_before.get("value")
        if op == "rename":
            after_new = _trykgedit_entry(kerning, _trykgedit_key(new, glyph, side))
            out["entry_after_new_name"] = after_new
            out["entry_followed"] = (None if before_value is None else
                                     bool(after_new.get("value") == before_value and out["entry_after_old_name"].get("value_type") == "NoneType"))
        else:
            out["entry_gone"] = None if before_value is None else out["entry_after_old_name"].get("value_type") == "NoneType"
    return dict(out, **cnt, note="RESEARCH: the font in memory may have changed. Compare with FontLab's Classes and KERNING panels; the font "
                                 "is not marked as changed and the panel is not asked to refresh; nothing is saved by Glyphbridge")


# --------------------------------------------------------------------------
# /debug/trymodern (v0.88) - EXPERIMENT: is there a modern route that keeps the two views of a glyph in step?
#   stage=state                  read only: legacy and modern state of ONE glyph, updatedFgGlyphs(), the guard registry's verdicts
#   stage=call  how=...  go=yes  ONE call per `how` per listener run, only on a glyph drawn or changed through the Glyphbridge tools in this run:
#       Update_fgGlyph           fontlab.Update(<legacy glyph>)
#       Update_flGlyph           fontlab.Update(<modern glyph>)
#       Update_all               fontlab.UpdateAll()
#       fillFgData               <modern glyph>.fillFgData(False, False)   (the returned object is only typed, never used)
#       prepareFontGateData      <package>.prepareFontGateData(False)
#   stage=create name=N go=yes   ONE modern glyph: flGlyph(), glyph.name = N, package.addGlyph(glyph); NO update call of any kind
# Not called, ever, by this probe: the assign family (assignFgLayer and assignFontGateData push LEGACY data into the modern layer, the
# suspected cause of the data loss), replaceGlyph, deleteGlyph, removeGlyph, save, close, export, release, remove, blockUpdate, unblockUpdate.
# Same one-font gate as /debug/trysync. Counters are raised BEFORE the call, whatever happens.
# --------------------------------------------------------------------------

_TRYKERN = {"calls": 0}
_TRYKERN_MAX = 20
_TRYGROUPS = {"calls": 0}
_TRYGROUPS_MAX = 10
_TRYMODERN_STAGES = ("state", "call", "create")
_TRYMODERN_HOWS = ("Update_fgGlyph", "Update_flGlyph", "Update_all", "fillFgData", "prepareFontGateData")
_TRYMODERN_NAME_CHARS = _TRYCREATE_NAME_CHARS
_TRYMODERN = {"Update_fgGlyph": 0, "Update_flGlyph": 0, "Update_all": 0, "fillFgData": 0, "prepareFontGateData": 0, "create": 0}
_TRYMODERN_IDS_MAX = 50


def _trymodern_ids(w):
    """updatedFgGlyphs() of a modern glyph: {"count", "ids"} for a plain list or tuple of ints; anything else by type name; a failure as text."""
    try:
        v = _call0(w, "updatedFgGlyphs")
    except Exception as exc:
        return f"<error: {type(exc).__name__}: {exc}>"
    if type(v) in (list, tuple) and all(type(x) is int for x in v):
        return {"count": len(v), "ids": list(v)[:_TRYMODERN_IDS_MAX]}
    return _tryfont_plain(v)


def _trymodern_registry(font):
    """{name: verdict} for every glyph the guard remembers (read only): 'gone', 'lost', 'synced', 'at_risk' or 'unknown'."""
    try:
        names = list(_guard_state(font)["glyphs"])
    except Exception as exc:
        return f"<error: {type(exc).__name__}: {exc}>"
    return {n: _guard_classify(font, n) for n in names}


def _trymodern_glyph(font, name):
    """Read-only snapshot of one glyph: legacy state, modern state, updatedFgGlyphs(), widths and the guard's verdict. Never raises."""
    try:
        glyph = _find_glyph(font, name)
    except Exception as exc:
        return {"found": None, "error": f"{type(exc).__name__}: {exc}"}
    if glyph is None:
        return {"found": False}
    st = {"found": True, "legacy": _tryshape_state(glyph)}
    try:
        w, _how = _modern_wrapper(glyph, font)
        modern, _layer = _tryshape_modern_state(w)
        st["modern"] = modern
        st["updated_fg_glyphs"] = _trymodern_ids(w)
        st["legacy_width"] = _num(glyph.width)
        st["modern_advance"] = _num(w.advanceWidth)
    except Exception as exc:
        st["modern_error"] = f"{type(exc).__name__}: {exc}"
    st["verdict"] = _guard_classify(font, name)
    return st


def _trymodern_layer_present(snapshot):
    """True / False when the snapshot says whether the modern active layer exists, None when that is unknown."""
    modern = snapshot.get("modern") if isinstance(snapshot, dict) else None
    if not isinstance(modern, dict):
        return None
    return modern.get("active_layer") == "present"


def debug_try_modern(stage, how, name, go):
    import sys as _sys
    if stage not in _TRYMODERN_STAGES:
        return {"error": 'stage must be "state", "call" or "create"'}
    if not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYMODERN_NAME_CHARS for ch in name):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    if stage == "call" and how not in _TRYMODERN_HOWS:
        return {"error": "how must be one of: " + ", ".join(_TRYMODERN_HOWS)}
    if stage != "state" and go != "yes":
        what = (f"makes ONE call ({how}) on a glyph that the Glyphbridge tools drew or changed in this listener run" if stage == "call"
                else "creates ONE glyph through flGlyph() and the package's addGlyph, with no update call")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
    mod = _sys.modules.get("fontlab") or fl
    ws, pkg, why = _trysync_target(mod)
    if ws is None:
        return {"stage": stage, "error": why, "calls_so_far": dict(_TRYMODERN)}
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    if stage == "state":
        return {"stage": "state", "name": name, "glyph": _trymodern_glyph(font, name), "registry": _trymodern_registry(font),
                "calls_so_far": dict(_TRYMODERN)}
    if stage == "call":
        return _trymodern_call(mod, pkg, font, name, how)
    return _trymodern_create(mod, pkg, font, name)


def _trymodern_call(mod, pkg, font, name, how):
    if _TRYMODERN[how] >= 1:
        return {"stage": "call", "how": how, "error": "this call was already made once in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYMODERN)}
    try:
        remembered = name in _guard_state(font)["glyphs"]
    except Exception as exc:
        return {"stage": "call", "how": how, "error": f"the guard registry could not be read ({type(exc).__name__}: {exc})", "calls_so_far": dict(_TRYMODERN)}
    if not remembered:
        return {"stage": "call", "how": how, "error": "the glyph was not drawn or changed through the Glyphbridge tools in this listener run (draw it first with "
                                                      "draw_polygon, draw_path or a width / sidebearing change; a listener restart forgets earlier work; since listener 0.89 a glyph is synced right after such a write and then leaves this registry, so only a glyph whose sync failed can still be tried)",
                "calls_so_far": dict(_TRYMODERN)}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"stage": "call", "how": how, "error": "no glyph with this name", "calls_so_far": dict(_TRYMODERN)}
    try:
        w, _wrapper_how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"stage": "call", "how": how, "error": f"the modern glyph could not be reached ({type(exc).__name__}: {exc})", "calls_so_far": dict(_TRYMODERN)}
    before = {"glyph": _trymodern_glyph(font, name), "registry": _trymodern_registry(font)}
    _TRYMODERN[how] += 1        # counted BEFORE the call: whatever happens, it is on record
    returned, error = None, None
    try:
        if how == "Update_fgGlyph":
            returned = _tryfont_plain(mod.Update(glyph))
        elif how == "Update_flGlyph":
            returned = _tryfont_plain(mod.Update(w))
        elif how == "Update_all":
            returned = _tryfont_plain(mod.UpdateAll())
        elif how == "fillFgData":
            returned = _tryfont_plain(w.fillFgData(False, False))
        else:
            returned = _tryfont_plain(pkg.prepareFontGateData(False))
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    after = {"glyph": _trymodern_glyph(font, name), "registry": _trymodern_registry(font)}
    was, now = _trymodern_layer_present(before["glyph"]), _trymodern_layer_present(after["glyph"])
    return {"stage": "call", "how": how, "name": name, "return_value": returned, "call_error": error, "before": before, "after": after,
            "layer_lost": (was is True and now is False), "synced_after": after["glyph"].get("verdict") == "synced",
            "calls_so_far": dict(_TRYMODERN),
            "note": "EXPERIMENT: 'synced_after' true with the drawing intact (layer_lost false) means this call syncs the glyph; layer_lost true means it "
                    "destroyed the modern layer. Read /glyph/outline of the glyph afterwards and look at the grid. Nothing is saved by Glyphbridge; "
                    "quit FontLab WITHOUT saving afterwards"}


def _trymodern_create(mod, pkg, font, name):
    if _TRYMODERN["create"] >= 1:
        return {"stage": "create", "error": "a glyph was already created this way in this listener run; restart the listener to repeat it",
                "calls_so_far": dict(_TRYMODERN)}
    before_names = [str(g.name) for g in font.glyphs]
    if name in before_names:
        return {"stage": "create", "error": "a glyph with this name already exists", "before_count": len(before_names), "calls_so_far": dict(_TRYMODERN)}
    registry_before = _trymodern_registry(font)
    count_before, count_err = _pkg_get(pkg, "glyphsCount")
    _TRYMODERN["create"] += 1   # counted BEFORE the calls: whatever happens, it is on record
    steps, error, readback, returned = [], None, None, None
    try:
        g = mod.flGlyph()
        steps.append("flGlyph()")
        g.name = name
        steps.append("glyph.name = name")
        readback = _tryfont_plain(_call0(g, "name"))
        if readback != name:
            error = f"the name read back as {readback!r}, so the glyph was NOT added to the package"
        else:
            returned = _tryfont_plain(pkg.addGlyph(g))
            steps.append("package.addGlyph(glyph)")
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    after_names = [str(g.name) for g in font.glyphs]
    present = name in after_names
    out = {"stage": "create", "name": name, "steps": steps, "name_read_back": readback, "return_value": returned, "call_error": error,
           "before_count": len(before_names), "after_count": len(after_names), "present_in_legacy_font": present,
           "created": present and len(after_names) == len(before_names) + 1,
           "package_glyphsCount_before": count_err if count_err is not None else _tryfont_plain(count_before)}
    count_after, count_err2 = _pkg_get(pkg, "glyphsCount")
    out["package_glyphsCount_after"] = count_err2 if count_err2 is not None else _tryfont_plain(count_after)
    try:
        found = pkg.findName(name)
        out["package_findName"] = {"type": type(found).__name__, "isNull": _tryfont_plain(_call0(found, "isNull")) if found is not None else None}
    except Exception as exc:
        out["package_findName"] = f"<error: {type(exc).__name__}: {exc}>"
    out["new_glyph"] = _trymodern_glyph(font, name) if present else None
    out["registry_before"], out["registry_after"] = registry_before, _trymodern_registry(font)
    added = _names_added(before_names, after_names)
    if added and not out["created"]:
        out["created_under_other_names"] = added
    out["calls_so_far"] = dict(_TRYMODERN)
    out["note"] = ("EXPERIMENT: no update call was made. If present_in_legacy_font is true, read /glyph/sidebearings and /glyph/outline of the new glyph, "
                   "then try draw_polygon on it; check the grid. A verdict 'lost' for the NEW glyph only means that it has no modern layer yet (a glyph made this way, like one "
                   "made by create_glyph, gets its layer from the first drawing or width tool). Nothing is saved by Glyphbridge; quit FontLab WITHOUT saving afterwards")
    return out


# --------------------------------------------------------------------------
# /debug/trypackage (v0.148) - RESEARCH for ROADMAP P0.9, read only: the first glyph of a new font cannot be drawn while other fonts
# are open, because _package_layer_name trusts the workspace's current package only when exactly one font is open (288, 691a).
# Names-only test 927 found flGlyph.package ("flObject"). Does the wrapper of a glyph of the font in front name ITS OWN package?
#   GET /debug/trypackage?name=X&go=yes   with any number of fonts open. The wrapper is taken as the write tools take it (_modern_wrapper).
# ONE read of w.package, then only if it is an object that is not null: the reads below, and ONE isEqual against the workspace's current
# package (isEqual proven in 736). The font in front's glyph count, unitsPerEm and path are read for comparison, and CountFonts() and the
# number of packages before and after. Never called: fgPackage (legacy), any write, update, notify, save or close. 20 per listener run.
#   GET /debug/trypackage?stage=cached&go=yes   (v0.149) 928 and 929 cannot tell "w.package is the glyph's own package" from "w.package is
# whatever package is current": both glyphs were in the font in front. This stage takes the wrappers ALREADY in the listener's cache (none is
# built; two unsaved fonts share the cache key "" so it keeps both), at most 20, in key order. Each must still agree with its cache key
# (fgGlyphId) and read isValid True; only then: ONE read of its package, that package's isNull, fgId and glyphsCount, and ONE isEqual against
# the current package. The same run counter as the glyph stage.
# --------------------------------------------------------------------------

_TRYPACKAGE = {"runs": 0}
_TRYPACKAGE_MAX = 20
_TRYPACKAGE_CACHED_MAX = 20
_TRYPACKAGE_STAGES = ("glyph", "cached")
_TRYPACKAGE_READS = ("fgId", "path", "mastersCount", "defaultMaster", "master", "glyphsCount", "upm")
_TRYPACKAGE_CURRENT_READS = ("fgId", "path", "glyphsCount", "upm")
_TRYPACKAGE_NOTE = ("RESEARCH, read only: nothing was written. 'same_as_current' is FontLab's own isEqual between the glyph's package and the "
                    "workspace's current package; compare 'glyph_package' with 'font_in_front' as well. Nothing is saved by Glyphbridge")


def _trypackage_count(mod):
    """CountFonts() and the number of workspace packages, each read once; a failure is reported as text."""
    out = {}
    try:
        out["CountFonts"] = _tryfont_plain(mod.CountFonts())
    except Exception as exc:
        out["CountFonts"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        out["packages"] = len(mod.flWorkspace.instance().packages())
    except Exception as exc:
        out["packages"] = f"<error: {type(exc).__name__}: {exc}>"
    return out


def _trypackage_masters(pkg):
    """The package's masters as a list of names when every entry is text; otherwise a type name or an error. ONE read."""
    value, err = _pkg_get(pkg, "masters")
    if err is not None:
        return f"<error: {err}>"
    if type(value) in (list, tuple) and all(isinstance(m, str) for m in value):
        return [_plain_text(m) for m in value][:20]
    return _tryfont_plain(value)


def _trypackage_object(obj):
    """(reads, null): the type, isNull and, only for an object that is not null, the fixed reads. null is True, False or None (unknown)."""
    out = {"type": type(obj).__name__}
    null, err = _pkg_get(obj, "isNull")
    out["isNull"] = f"<error: {err}>" if err is not None else _tryfont_plain(null)
    if err is not None or type(null) is not bool:
        return out, None
    return out, null


def _trypackage_front(font):
    """The font in front, read for comparison: its glyph count, unitsPerEm and path (the path stays in this reply only)."""
    out = {}
    try:
        out["glyphs"] = len(font.glyphs)
    except Exception as exc:
        out["glyphs"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        out["unitsPerEm"] = _tryfont_plain(font.info.unitsPerEm)
    except Exception as exc:
        out["unitsPerEm"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        out["path"] = _tryfont_plain(font.path)
    except Exception as exc:
        out["path"] = f"<error: {type(exc).__name__}: {exc}>"
    return out


def _trypackage_matches(gp, front):
    """True or False for each comparison both sides of which are plain values; None when one side is not."""
    def same(a, b, num):
        if num:
            a, b = _num(a), _num(b)
            return None if a is None or b is None else abs(a - b) <= 1e-6
        return a == b if isinstance(a, str) and isinstance(b, str) else None
    return {"glyphs": same(gp.get("glyphsCount"), front.get("glyphs"), True),
            "upm": same(gp.get("upm"), front.get("unitsPerEm"), True),
            "path": same(gp.get("path"), front.get("path"), False)}


def _trypackage_current(mod):
    """(reads, package, null) of the workspace's current package: its type, isNull and, when not null, the fixed reads."""
    try:
        cp, err = _pkg_get(mod.flWorkspace.instance(), "currentPackage")
    except Exception as exc:
        cp, err = None, f"the workspace could not be reached ({type(exc).__name__}: {exc})"
    if err is not None or cp is None:
        return ({"error": err} if err is not None else None), None, None
    reads, null = _trypackage_object(cp)
    if null is False:
        for attr in _TRYPACKAGE_CURRENT_READS:
            reads[attr] = _trynotify_read(cp, attr)
    return reads, cp, null


def _trypackage_cached_entry(lid, w, cp, cp_null):
    """v0.149: one cached wrapper. Its name, then its fgGlyphId against the cache key and isValid; only when both agree: ONE read of its
    package, that package's isNull, fgId and glyphsCount, and ONE isEqual against the current package. Never raises."""
    e = {"key": lid if type(lid) is int else _tryfont_plain(lid)}
    try:
        e["name"] = _plain_text(str(w.name))[:40]
    except Exception as exc:
        e["name"] = f"<error: {type(exc).__name__}: {exc}>"
    try:
        gid = int(_call0(w, "fgGlyphId"))
    except Exception as exc:
        e["skipped"] = f"its fgGlyphId could not be read ({type(exc).__name__}: {exc})"
        return e
    if gid != lid:
        e["skipped"] = f"its fgGlyphId {gid} differs from its cache key"
        return e
    valid, err = _pkg_get(w, "isValid")
    if err is not None or valid is not True:
        e["skipped"] = f"isValid is not true ({err if err is not None else _tryfont_plain(valid)!r})"
        return e
    gp, err = _pkg_get(w, "package")
    if err is not None or gp is None:
        e["package"] = {"error": err} if err is not None else None
        e["same_as_current"] = None
        return e
    e["package"], null = _trypackage_object(gp)
    if null is False:
        for attr in ("fgId", "glyphsCount"):
            e["package"][attr] = _trynotify_read(gp, attr)
    if null is False and cp_null is False:
        try:
            same = gp.isEqual(cp)
            e["same_as_current"] = same if type(same) is bool else f"<{type(same).__name__}>"
        except Exception as exc:
            e["same_as_current"] = f"<error: isEqual failed: {type(exc).__name__}: {exc}>"
    else:
        e["same_as_current"] = None
    return e


def _trypackage_finish(out, mod, before):
    after = _trypackage_count(mod)
    out["fonts_after"] = after
    out["side_effect_detected"] = (None if any(not isinstance(v, int) for v in list(before.values()) + list(after.values()))
                                   else before != after)
    out["runs_so_far"] = _TRYPACKAGE["runs"]
    out["note"] = _TRYPACKAGE_NOTE
    return out


def debug_try_package(name, go, stage="glyph"):
    import sys as _sys
    if stage not in _TRYPACKAGE_STAGES:
        return {"error": 'stage must be "glyph" or "cached"'}
    if stage == "glyph" and (not isinstance(name, str) or not (1 <= len(name) <= 40) or any(ch not in _TRYCREATE_NAME_CHARS for ch in name)):
        return {"error": "name must be 1 to 40 characters from A-Z a-z 0-9 . _ -"}
    if stage == "cached" and name:
        return {"error": "stage=cached takes no name: it reads the wrappers already in the listener's cache"}
    if go != "yes":
        return {"error": "reads flGlyph.package and calls isEqual on it, which have not been called live before. Add &go=yes to run it."}
    if _TRYPACKAGE["runs"] >= _TRYPACKAGE_MAX:
        return {"error": f"the probe already ran {_TRYPACKAGE_MAX} times in this listener run; restart the listener to repeat it",
                "runs_so_far": _TRYPACKAGE["runs"]}
    mod = _sys.modules.get("fontlab") or fl
    font = _open_font()
    if font is None:
        return {"open": False}
    if stage == "cached":
        entries = sorted(list(_MODERN_CACHE.items()), key=lambda kv: kv[0] if type(kv[0]) is int else -1)
        _TRYPACKAGE["runs"] += 1     # counted BEFORE the first read under test
        before = _trypackage_count(mod)
        out = {"stage": "cached", "fonts_before": before, "font_in_front": _trypackage_front(font),
               "cache_key_is_empty_path": _MODERN_CACHE_FONT[0] == "", "cached_wrappers": len(entries),
               "cut": len(entries) > _TRYPACKAGE_CACHED_MAX}
        out["current_package"], cp, cp_null = _trypackage_current(mod)
        out["wrappers"] = [_trypackage_cached_entry(lid, w, cp, cp_null) for lid, w in entries[:_TRYPACKAGE_CACHED_MAX]]
        return _trypackage_finish(out, mod, before)
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"name": name, "error": f"no glyph named {name!r} in the font in front; nothing was read", "runs_so_far": _TRYPACKAGE["runs"]}
    try:
        w, how = _modern_wrapper(glyph, font)
    except Exception as exc:
        return {"name": name, "error": f"the modern glyph could not be reached ({exc}); nothing was read", "runs_so_far": _TRYPACKAGE["runs"]}
    _TRYPACKAGE["runs"] += 1     # counted BEFORE the first read under test: whatever happens, it is on record
    before = _trypackage_count(mod)
    out = {"name": name, "wrapper": how, "fonts_before": before, "font_in_front": _trypackage_front(font)}
    gp, err = _pkg_get(w, "package")
    if err is not None or gp is None:
        out["glyph_package"] = {"error": err} if err is not None else None
        gp_null = None
    else:
        out["glyph_package"], gp_null = _trypackage_object(gp)
        if gp_null is False:
            for attr in _TRYPACKAGE_READS:
                out["glyph_package"][attr] = _trynotify_read(gp, attr)
            out["glyph_package"]["masters"] = _trypackage_masters(gp)
    out["current_package"], cp, cp_null = _trypackage_current(mod)
    if gp_null is False and cp_null is False:
        try:
            same = gp.isEqual(cp)
            out["same_as_current"] = same if type(same) is bool else f"<{type(same).__name__}>"
        except Exception as exc:
            out["same_as_current"] = f"<error: isEqual failed: {type(exc).__name__}: {exc}>"
    else:
        out["same_as_current"] = None
        out["same_reason"] = "isEqual was not called: the glyph's package or the current package is missing, null or of unknown state"
    if gp_null is False:
        out["glyph_package_matches_front"] = _trypackage_matches(out["glyph_package"], out["font_in_front"])
    return _trypackage_finish(out, mod, before)


# --------------------------------------------------------------------------
# POST /font/create (v0.146, ROADMAP P0.3 / P0.4): a new font, as File > New Font makes one. ONE flPackage() per request, also
# with other fonts open and more than once per listener run (the user's decisions of 2026-11-12; the native reference each
# construction leaves belongs to FontLab, and 834 / 835 made two fonts in one FontLab session). flPackage() registers the font
# and brings it to the front by itself, numbering its family as FontLab does (Unnamed, Unnamed1, ...; NF 831-835).
# Without a family nothing else is called. With one, only after the new font is confirmed in front: the four names Font Info's
# Build Names gives (tfn, ffn, psn, sgn; 845, 849), each read back; the legacy font.info.familyName (the server names a font
# from it, and the FONTS panel gave the font its own line only with it, 885), written only when the font in front still reads
# the new package's own family; then, only when all five read back equal, ONE flItems.notifyChangesApplied(title, <the
# package>, False) on the package just made, so FontLab asks to save on close (912-914). "notes" holds what FontLab cannot
# be made to show (the tab title and the FONTS panel lag, 896-914; since v0.147 one plain note, no workaround), printed in the
# OUTPUT panel too.
# Never called here: addPackage, save, close, export, release, remove, font.update().
# --------------------------------------------------------------------------
_CREATE_FONT_PSN_MAX = 63            # psn = family without spaces + "-Regular" must stay within 63 characters (PostScript's limit;
                                     # /debug/tryfont's old limit of 58 for the whole family let it reach 66)
_CREATE_FONT_PSN_FORBIDDEN = "[](){}<>/%"   # characters a PostScript name may not hold; refused in a family, which becomes part of it


def _family_name_error(family):
    """None, or why a family name is refused before anything is called. Shared by /font/create and /debug/tryfont construct_named
    (v0.146): the checks of _trynames_value_error, a PostScript name (Build Names, style Regular) of at most 63 characters, and none
    of the characters a PostScript name may not hold."""
    why = _trynames_value_error("tfn", family)
    if why is not None:
        return why
    psn = _tryfont_built_names(family)[2][1]
    if len(psn) > _CREATE_FONT_PSN_MAX:
        return (f"the PostScript name it gives, {psn!r}, has {len(psn)} characters; at most {_CREATE_FONT_PSN_MAX} are allowed, "
                f"so the family may have at most {_CREATE_FONT_PSN_MAX - len('-Regular')} characters without its spaces")
    if any(ch in _CREATE_FONT_PSN_FORBIDDEN for ch in family):
        return f"it becomes part of the PostScript name, which may not hold any of {_CREATE_FONT_PSN_FORBIDDEN}"
    return None
_CREATE_FONT_MARK_TITLE = "Glyphbridge create font"
_CREATE_FONT_PKG_READS = ("upm", "mastersCount", "defaultMaster", "glyphsCount", "path", "fileName")


def _create_font_count(mod):
    """(CountFonts() as a plain int, None) or (None, reason). Never raises."""
    counter = getattr(mod, "CountFonts", None)
    if not callable(counter):
        return None, "the fontlab module has no CountFonts"
    try:
        count = counter()
    except Exception as exc:
        return None, f"CountFonts() failed ({type(exc).__name__}: {exc})"
    if type(count) is not int:
        return None, f"CountFonts() returned {type(count).__name__}, not a plain number"
    return count, None


def _create_font_in_front(mod, pkg):
    """(True | False, None) or (None, reason): whether the workspace's current package is the package just made. v0.150: their
    fgId values are compared (one read each); isEqual is not used, because it returned true for two different packages (930, 931).
    Never raises."""
    try:
        ws = mod.flWorkspace.instance()
    except Exception as exc:
        return None, f"the workspace could not be reached ({type(exc).__name__}: {exc})"
    current, err = _pkg_get(ws, "currentPackage")
    if err is not None:
        return None, err
    if current is None:
        return None, "the workspace has no current package"
    is_null, err = _pkg_get(current, "isNull")
    if err is not None:
        return None, err
    if is_null is not False:
        return None, "the current package is null or its state is unknown"
    new_id, err = _package_fg_id(pkg, "the new package")
    if err is not None:
        return None, err
    current_id, err = _package_fg_id(current, "the current package")
    if err is not None:
        return None, err
    return new_id == current_id, None


def _create_font_legacy_family(family, own_family):
    """The legacy family write of a named font: written only when the font in front still reads own_family (the new package's
    family before the names were written), so that it can only be the new font. Never raises."""
    out = {"value": family}
    try:
        font = fl.CurrentFont()
        info = font.info
        before = info.familyName
    except Exception as exc:
        out.update(written=False, reason=f"the legacy font.info could not be read ({type(exc).__name__}: {exc})")
        return out
    out["before"] = _plain_text(before) if isinstance(before, str) else f"<{type(before).__name__}>"
    if not isinstance(before, str) or before != own_family:
        out.update(written=False, reason=f"the font in front reads the legacy family {out['before']!r}, not the new font's own "
                                         f"{own_family!r}, so it was not written (it might not be the new font)")
        return out
    out["written"] = True
    try:
        info.familyName = family
    except Exception as exc:
        out["call_error"] = f"{type(exc).__name__}: {exc}"
    try:
        back = info.familyName
        out["read_back"] = _plain_text(back) if isinstance(back, str) else f"<{type(back).__name__}>"
    except Exception as exc:
        out["read_back"] = f"<error: {type(exc).__name__}: {exc}>"
    out["read_back_equal"] = out["read_back"] == family
    return out


def _create_font_mark(mod, pkg):
    """ONE flItems.notifyChangesApplied(title, <the package just made>, False), or why not. Never raises."""
    if not _MARK_CHANGED:
        return {"called": False, "reason": "the changed mark is switched off in the listener"}
    items = getattr(mod, "flItems", None)
    if items is None:
        return {"called": False, "reason": "the fontlab module has no flItems"}
    mark = {"called": True}
    try:
        items.notifyChangesApplied(_CREATE_FONT_MARK_TITLE, pkg, False)
    except Exception as exc:
        mark["call_error"] = f"{type(exc).__name__}: {exc}"
    return mark


def _create_font_notes(out, family):
    """What the person must be told: plain sentences, built only from this reply; also printed in the OUTPUT panel."""
    notes = ["This font is not saved: save it from FontLab's File menu if you want to keep it."]     # v0.147: shorter
    before = out.get("names_before") if isinstance(out.get("names_before"), dict) else {}
    own_full, own_family = before.get("ffn"), before.get("tfn")
    if family is None:
        notes.append("It has no changes yet, so FontLab may close it without asking to save; once it is changed, FontLab normally asks.")
    else:
        # v0.147: one plain note, no Font Info chores (921, 922: no single step with unchanged values refreshes the display).
        # "should" on save and reopen: not yet tested (FontLab in Demo mode), ROADMAP P0.3.
        temp = own_family if isinstance(own_family, str) and own_family else own_full
        if isinstance(temp, str) and temp:
            notes.append(f"Right now FontLab may still show the temporary name \"{temp}\" in this font's tab and in the FONTS panel. "
                         "This is only a display delay: Font Info shows the font's actual names. "
                         "Saving and reopening the font should update FontLab's display.")
        if out.get("names_set") is not True or out.get("legacy_family_set") is not True:
            notes.append("Not every name could be set, so the font was not marked as changed: FontLab may close it without asking to save.")
    after = out.get("fonts_open_after")
    if type(after) is int and after > 1:     # v0.150: no double-click note any more (P0.9: the first glyph's layer comes from its own package)
        notes.append("Keep this font's window in front while an agent works on it: Glyphbridge cannot always tell two unsaved fonts apart.")
    return notes


def create_font(family=None):
    """POST /font/create: ONE new font, named as Build Names would when family is given. See the comment above."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    if family is not None:
        why = _family_name_error(family)
        if why is not None:
            return {"bad_request": "family: " + why + "; no font was made"}
    cls = getattr(mod, "flPackage", None)
    if cls is None:
        return {"created": False, "reason": "the fontlab module has no flPackage class; no font was made"}
    before, err = _create_font_count(mod)
    if err is not None:
        return {"created": False, "reason": f"the number of open fonts could not be read ({err}); no font was made"}
    out = {"created": False, "family_requested": family, "fonts_open_before": before}
    try:
        pkg = cls()
    except Exception as exc:
        out["reason"] = f"flPackage() raised {type(exc).__name__}: {exc}"
        out["fonts_open_after"] = _create_font_count(mod)[0]
        return out
    after, err = _create_font_count(mod)
    out["fonts_open_after"] = after
    out["names_before"] = {attr: _trynames_read(pkg, attr) for attr in _PACKAGE_NAME_FIELDS}
    in_front, why_front = _create_font_in_front(mod, pkg)
    out["in_front"] = in_front if why_front is None else "unknown"
    if err is not None or after != before + 1:
        out["reason"] = (f"the number of open fonts could not be read afterwards ({err})" if err is not None
                         else f"the number of open fonts went from {before} to {after}, not up by one")
    elif in_front is not True:
        out["reason"] = ("the new font is not the font in front" if in_front is False
                         else f"whether the new font is in front could not be checked ({why_front})")
    if "reason" in out:
        out["reason"] += "; nothing was named or marked"
        out["package"] = {attr: _tryfont_read(pkg, attr) for attr in _CREATE_FONT_PKG_READS}
        return out
    out["created"] = True
    if family is not None:
        assignments = []
        for attr, value in _tryfont_built_names(family):
            entry = {"field": attr, "value": value}
            try:
                setattr(pkg, attr, value)
            except Exception as exc:
                entry["call_error"] = f"{type(exc).__name__}: {exc}"
            entry["read_back"] = _trynames_read(pkg, attr)
            entry["read_back_equal"] = entry["read_back"] == value
            assignments.append(entry)
        out["assignments"] = assignments
        out["names_set"] = all(e["read_back_equal"] for e in assignments)
        legacy = _create_font_legacy_family(family, out["names_before"].get("tfn"))
        out["legacy_family"] = legacy
        out["legacy_family_set"] = legacy.get("read_back_equal") is True
        if out["names_set"] and out["legacy_family_set"]:
            out["fontlab_changed_mark"] = _create_font_mark(mod, pkg)
        else:
            out["fontlab_changed_mark"] = {"called": False, "reason": "not every name was set and read back"}
    else:
        out["fontlab_changed_mark"] = {"called": False, "reason": "no name was given, so nothing was changed after FontLab made the font"}
    out["names_after"] = {attr: _trynames_read(pkg, attr) for attr in _PACKAGE_NAME_FIELDS}
    out["package"] = {attr: _tryfont_read(pkg, attr) for attr in _CREATE_FONT_PKG_READS}
    out["notes"] = _create_font_notes(out, family)
    return out


# ---- v0.204: the change log (DECISIONS.md, 2026-11-24: both counts, through a change log). The listener judges each product write
# from its own reply and keeps the last _CHANGE_LOG_MAX entries of this listener run; each font's running total is never trimmed.
# Bookkeeping only: one read of the font in front (its package fgId and names) after a write that changed or may have changed it,
# nothing else is called on FontLab. The server asks through POST /changes; the five rules live in the server.
_CHANGE_LOG_MAX = 1000          # the user's choice (2026-11-24)
_CHANGE_ASK_MAX = 2000          # most request IDs one /changes request may ask about
_CHANGE_ID_MAX = 64             # longest request / server-run ID kept (the server sends 32 hex digits)
_CHANGE_RUN = None              # this listener run's ID, set below
_CHANGE_LOG = []                # entries, oldest first
_CHANGE_STATE = {"seq": 0, "dropped": 0, "dropped_upto": 0, "started": ""}
_CHANGE_TOTALS = {}             # font key -> {"font", "changed", "unknown"}; never trimmed
_CHANGE_EXCLUDED = ("/font/notdef/warn",)     # writes in _ACT_WRITES that never change the font


def _change_new_run():
    """A fresh, empty log with a new run ID (called once when the listener file runs)."""
    global _CHANGE_RUN
    _CHANGE_RUN = hashlib.sha1(f"{time.time()}-{id(_CHANGE_LOG)}-{time.perf_counter()}".encode("ascii")).hexdigest()[:16]
    del _CHANGE_LOG[:]
    _CHANGE_TOTALS.clear()
    _CHANGE_STATE["seq"] = _CHANGE_STATE["dropped"] = _CHANGE_STATE["dropped_upto"] = 0    # plain assignments: the static scans of
    _CHANGE_STATE["started"] = datetime.datetime.now().strftime("%H:%M:%S")                # nearby probes forbid any update call


_change_new_run()


def _change_same(before, after):
    """True when two read-back values are the same (numbers within 0.01). Never raises."""
    nb, na = _num(before), _num(after)
    if nb is not None and na is not None:
        return abs(nb - na) < 0.01
    return before == after


def _change_verdict(path, code, reply):
    """"yes", "no" or "unknown": did this write change the font? General rules, in order, from the route's own reply only:
    a refusal (HTTP 400) is no; another failure or an unreadable reply is unknown; no font, a No or no answer in a dialog is no;
    kerning entries decide by their own "changed" / "removed"; an explicit "changed" decides; a success flag of a change is yes;
    a glyph created under another name is yes; a re-read before / after decides (and a created layer is a change); a refusal
    with a reason is no; anything else is unknown, which counts on the safe side."""
    if code == 400:
        return "no"
    if code != 200 or not isinstance(reply, dict):
        return "unknown"
    if reply.get("open") is False or reply.get("user_declined") is True or reply.get("not_answered") is True:
        return "no"
    results = reply.get("results")
    if isinstance(results, list):
        entries = [e for e in results if isinstance(e, dict)]
        if any(e.get("changed") is True or e.get("removed") is True for e in entries):
            return "yes"
        if any(e.get("changed") == "unknown" for e in entries):
            return "unknown"
        return "no"
    changed = reply.get("changed")
    if changed is True:
        return "yes"
    if changed == "unknown":
        return "unknown"
    if changed is False:
        return "no"
    if any(reply.get(k) is True for k in ("created", "deleted", "drawn", "moved", "placed", "removed", "renamed")):
        return "yes"
    if reply.get("created_under_other_names"):
        return "yes"
    if reply.get("layer_created"):
        return "yes"
    if "before" in reply and "after" in reply:
        return "no" if _change_same(reply.get("before"), reply.get("after")) else "yes"
    if reply.get("reason") or reply.get("error") or reply.get("bad_request"):
        return "no"
    return "unknown"


def _change_id(raw):
    """A request or server-run ID as sent (printable ASCII, no spaces, at most _CHANGE_ID_MAX characters), or None."""
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    if not raw or len(raw) > _CHANGE_ID_MAX or any(not (33 <= ord(c) <= 126) for c in raw):
        return None
    return raw


def _change_font():
    """(key, name) of the font in front, read once: key is the package fgId as text ("fgId:5"), or the path hash when the
    fgId cannot be read, or None. Never raises."""
    try:
        counter = getattr(fl, "CountFonts", None)
        count = counter() if callable(counter) else None
        if type(count) is int and count == 0:
            return None, None
    except Exception:
        pass
    name = None
    try:
        font = fl.CurrentFont()
        info = font.info if font is not None else None
        if info is not None:
            name = " ".join(x for x in (_font_text(info, "familyName"), _font_text(info, "styleName")) if x) or None
    except Exception:
        font = None
    key, _err = _notdef_font_key()
    if key is not None:
        return f"fgId:{key}", name
    try:
        path = font.path if font is not None else None
        if isinstance(path, str) and path:
            return "path:" + hashlib.sha1(path.encode("utf-8")).hexdigest()[:12], name
    except Exception:
        pass
    return None, name


def _change_target(path, payload):
    """A short name for what the write addressed (a glyph, a group, the number of pairs), or None."""
    if not isinstance(payload, dict):
        return None
    for key in ("name", "group", "family"):
        if isinstance(payload.get(key), str) and payload[key].strip():
            return _act_text(payload[key].strip())
    pairs = payload.get("pairs")
    if isinstance(pairs, list):
        return f"{len(pairs)} pair{'' if len(pairs) == 1 else 's'}"
    return None


def _change_log_note(method, path, body, response, headers):
    """Log one served product write (called by _handle with the reply about to be sent). Never raises."""
    try:
        path = urlsplit(path).path
        if method != "POST" or path not in _ACT_WRITES or path in _CHANGE_EXCLUDED:
            return
        try:
            code = int(response[9:12])
        except Exception:
            code = 0
        try:
            reply = json.loads(response.partition(b"\r\n\r\n")[2].decode("utf-8"))
        except Exception:
            reply = None
        verdict = _change_verdict(path, code, reply)
        rid = _change_id(headers.get("x-glyphbridge-request-id")) if isinstance(headers, dict) else None
        if verdict == "no" and rid is None:
            return                                  # nothing to count and nobody can ask about it
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            payload = None
        key, name = _change_font() if verdict != "no" else (None, None)
        _CHANGE_STATE["seq"] += 1
        entry = {"seq": _CHANGE_STATE["seq"], "id": rid,
                 "server_run": _change_id(headers.get("x-glyphbridge-server-run")) if isinstance(headers, dict) else None,
                 "client": _act_client(headers.get("x-glyphbridge-client")) if isinstance(headers, dict) else None,
                 "kind": _ACT_WRITES[path], "target": _change_target(path, payload), "changed": verdict,
                 "font_key": key, "font": name, "time": datetime.datetime.now().strftime("%H:%M:%S")}
        _CHANGE_LOG.append(entry)
        if verdict != "no":
            total = _CHANGE_TOTALS.setdefault(key or "unknown font", {"font": name, "changed": 0, "unknown": 0})
            total["changed" if verdict == "yes" else "unknown"] += 1
            if name:
                total["font"] = name
        while len(_CHANGE_LOG) > _CHANGE_LOG_MAX:
            gone = _CHANGE_LOG.pop(0)
            _CHANGE_STATE["dropped"] += 1
            _CHANGE_STATE["dropped_upto"] = gone["seq"]
    except Exception:
        pass


def changes_report(run=None, since=None, server_run=None, ask_ids=None):
    """POST /changes (v0.204): what the log holds after the server's bookmark. Reads the log only, never FontLab."""
    if run is not None and not isinstance(run, str):
        return {"bad_request": '"run" must be a string'}
    if since is not None and (type(since) is not int or since < 0):
        return {"bad_request": '"since" must be a whole number of 0 or more'}
    if server_run is not None and not isinstance(server_run, str):
        return {"bad_request": '"server_run" must be a string'}
    if ask_ids is not None and (not isinstance(ask_ids, list) or len(ask_ids) > _CHANGE_ASK_MAX
                                or any(not isinstance(i, str) for i in ask_ids)):
        return {"bad_request": f'"ask_ids" must be a list of at most {_CHANGE_ASK_MAX} strings'}
    same_run = run is not None and run == _CHANGE_RUN
    since_used = since if (same_run and since is not None) else 0
    mine = _change_id(server_run)
    groups = {}
    for e in _CHANGE_LOG:
        if e["seq"] <= since_used or e["changed"] == "no":
            continue
        own = mine is not None and e.get("server_run") == mine
        gkey = (e.get("font_key"), "this server" if own else (e.get("server_run"), e.get("client")))
        g = groups.get(gkey)
        if g is None:
            g = groups[gkey] = {"font": e.get("font"), "font_key": e.get("font_key"), "by_this_server": own,
                                "client": e.get("client"), "changed": 0, "unknown": 0, "first": e["time"], "last": e["time"]}
        g["changed" if e["changed"] == "yes" else "unknown"] += 1
        g["last"] = e["time"]
        if e.get("font"):
            g["font"] = e["font"]
    asked = {}
    if ask_ids:
        by_id = {e["id"]: e for e in _CHANGE_LOG if e.get("id")}
        for rid in ask_ids:
            e = by_id.get(rid)
            if e is not None:
                asked[rid] = {"yes": "changed", "no": "unchanged"}.get(e["changed"], "unknown")
            else:
                asked[rid] = "not_seen_or_dropped" if _CHANGE_STATE["dropped"] else "not_seen"
    dropped_after = max(0, _CHANGE_STATE["dropped_upto"] - since_used)    # entries after the bookmark that the limit dropped
    return {"run": _CHANGE_RUN, "run_started": _CHANGE_STATE["started"], "same_run": same_run, "since_used": since_used,
            "newest": _CHANGE_STATE["seq"], "log_limit": _CHANGE_LOG_MAX, "entries_kept": len(_CHANGE_LOG),
            "dropped_after_since": dropped_after, "groups": list(groups.values()), "asked": asked,
            "totals": [dict(v, font_key=k) for k, v in _CHANGE_TOTALS.items()]}


# --------------------------------------------------------------------------
# HTTP plumbing (stdlib only; no background thread - see module docstring)
# --------------------------------------------------------------------------

def _build_response(status, payload):
    body = json.dumps(payload).encode("utf-8")
    head = (
        f"HTTP/1.1 {status} {_REASONS.get(status, 'Error')}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        + _font_headers() +
        f"X-Glyphbridge-Run: {_CHANGE_RUN}\r\n" +     # v0.204: this listener run, so the server can see a restart
        "Connection: close\r\n\r\n"
    )
    return head.encode("ascii") + body


def _route(method, full_path, body=b""):
    _forget_request_font()           # v0.113: each request names only the font it used itself
    split = urlsplit(full_path)
    path = split.path
    query = parse_qs(split.query)

    if method == "GET":
        if path == "/health":
            global _connection_announced
            if not _connection_announced:
                _connection_announced = True
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                # Any local client can send it (--check, a PowerShell call): the name is the client's own claim (v0.105).
                who = f'"{_request_client}"' if _request_client else "a local client"
                if _request_launcher:  # v0.109: the program that started the server; this pair needs no line of its own
                    who += f" | {_request_launcher}"
                    _announced_clients.add((_request_client, _request_launcher))
                print(f"[glyphbridge] Connected at {ts} - first request (GET /health) from {who}.")
            return _build_response(200, {"status": "ok"})

        if path == "/version":
            return _build_response(200, {"version": VERSION})

        if path == "/font/current":
            try:
                return _build_response(200, get_current_font_info())
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/font/notdef":
            try:
                return _build_response(200, check_notdef())
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/font/glyphs":
            try:
                return _build_response(200, get_glyph_names())
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/font":
            try:
                return _build_response(200, debug_font_info())
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/glyph":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, debug_glyph_info(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/contours":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, debug_glyph_contours(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/box":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, debug_glyph_box(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/shapecount":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, debug_shape_count(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/layerstats":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, debug_layer_stats(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/findnode":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                idx = int((query.get("index") or ["0"])[0])
            except ValueError:
                return _build_response(400, {"error": '"index" must be an integer'})
            stage = (query.get("stage") or ["fetch"])[0]
            attrs = [a for a in (query.get("attrs") or [""])[0].split(",") if a.strip()]
            try:
                return _build_response(200, debug_find_node(names[0].strip(), idx, stage, [a.strip() for a in attrs]))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/nodes":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            extra = [a.strip() for a in (query.get("attrs") or [""])[0].split(",") if a.strip()]
            try:
                calls = [a.strip() for a in (query.get("calls") or [""])[0].split(",") if a.strip()]
                return _build_response(200, get_glyph_nodes(names[0].strip(), extra, calls))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/font/nonempty":
            try:
                return _build_response(200, find_nonempty_glyphs())
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/outline":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                route = (query.get("layer") or ["body"])[0]
                modern = (query.get("modern") or ["yes"])[0] != "no"
                return _build_response(200, get_glyph_outline(names[0].strip(), route, modern))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/tryshape":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>&go=yes&route=pen&stage=dir|draw"})
            go = (query.get("go") or [""])[0]
            route = (query.get("route") or ["pen"])[0]
            stage = (query.get("stage") or [""])[0]
            what = (query.get("what") or ["layer"])[0]
            variant = (query.get("variant") or ["single"])[0]
            ontype = (query.get("ontype") or ["value"])[0]
            try:
                return _build_response(200, debug_try_shape(names[0].strip(), go, route, stage, what, variant, ontype))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/readmodern":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph>&stage=layer|contour|node|box[&index=K&node=I&via=getNodeAt|at][&go=yes]"})
            def _qr(key, default=""):
                return (query.get(key) or [default])[0]
            try:
                idx, nidx = int(_qr("index", "0")), int(_qr("node", "0"))
            except ValueError:
                return _build_response(400, {"error": '"index" and "node" must be integers'})
            if not (0 <= idx <= 9999 and 0 <= nidx <= 9999):
                return _build_response(400, {"error": '"index" and "node" must be between 0 and 9999'})
            try:
                return _build_response(200, debug_read_modern(names[0].strip(), _qr("stage", "layer"), idx, nidx, _qr("via"), _qr("go")))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trylayer":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph>&stage=state|create[&method=findLayerCreate|getLayerByName|addLayer&layer=NAME&ref=GLYPH&go=yes]"})
            def _ql(key, default=""):
                return (query.get(key) or [default])[0]
            try:
                return _build_response(200, debug_try_layer(names[0].strip(), _ql("stage", "state"), _ql("method"), _ql("layer"), _ql("ref"), _ql("go")))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trymetrics":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=tri...&stage=names|doc|read|set|refresh|poke[&go=yes&what=width|lsb|rsb|sb&route=legacy|modern&value=N&update=none|flglyph|glyph|both&notify=no|yes&target=glyph|layer|shape|workspace|legacy&member=NAME&members=a,b&arg=auto|yes|no]"})
            def _q(key, default=""):
                return (query.get(key) or [default])[0]
            try:
                return _build_response(200, debug_try_metrics(names[0].strip(), _q("go"), _q("stage", "read"), _q("what", "width"),
                                                             _q("route", "legacy"), _q("value"), _q("value2"), _q("update", "default"), _q("notify", "no"),
                                                             _q("target"), _q("member"), _q("members"), _q("arg")))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/tryadvancewidth":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=tri...&stage=names|read[&go=yes]"})
            def _qaw(key, default=""):
                return (query.get(key) or [default])[0]
            try:
                return _build_response(200, debug_try_advance_width(names[0].strip(), _qaw("stage", "names"), _qaw("go")))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trydialogtimeout":     # v0.201: a dialog that closes itself (research, UI only, gated)
            try:
                return _build_response(200, debug_try_dialog_timeout((query.get("how") or [""])[0], (query.get("seconds") or [""])[0],
                                                                     (query.get("go") or [""])[0], (query.get("countdown") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/objdir":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            target = (query.get("target") or ["glyph"])[0]
            stage = (query.get("stage") or ["dir"])[0]
            attrs = [a.strip() for a in (query.get("attrs") or [""])[0].split(",") if a.strip()]
            try:
                return _build_response(200, debug_obj_probe(names[0].strip(), target, stage, attrs))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/layerbbox":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            stage = (query.get("stage") or ["call"])[0]
            attrs = [a.strip() for a in (query.get("attrs") or [""])[0].split(",") if a.strip()]
            try:
                return _build_response(200, debug_layer_bbox(names[0].strip(), stage, attrs))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/drawpen":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                lim = int((query.get("limit") or ["60"])[0])
            except ValueError:
                return _build_response(400, {"error": '"limit" must be an integer'})
            try:
                return _build_response(200, debug_draw_pen(names[0].strip(), lim))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/classdir":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<class name in the fontlab module>"})
            try:
                dc = int((query.get("doc") or ["600"])[0])
            except ValueError:
                return _build_response(400, {"error": '"doc" must be an integer'})
            try:
                return _build_response(200, debug_class_probe(names[0].strip(), dc, (query.get("members") or [None])[0]))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/walk":
            wp = (query.get("path") or [""])[0]
            stage = (query.get("stage") or ["read"])[0]
            attrs = [a.strip() for a in (query.get("attrs") or [""])[0].split(",") if a.strip()]
            try:
                return _build_response(200, debug_walk(wp, stage, attrs))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/currentshapes":
            try:
                data = _read_modern_shapes()
                data["legacy_current_name"] = _legacy_current_name()
                return _build_response(200, data)
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/buildglyph":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>&go=yes"})
            go = (query.get("go") or [""])[0]
            reads = (query.get("reads") or ["full"])[0]
            gcm = (query.get("gc") or ["no"])[0]
            try:
                return _build_response(200, debug_build_glyph(names[0].strip(), go, reads, gcm))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/setcurrent":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>&go=yes"})
            go = (query.get("go") or [""])[0]
            phase = (query.get("phase") or ["all"])[0]
            try:
                return _build_response(200, debug_set_current(names[0].strip(), go, phase))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/fldir":
            contains = [c.strip() for c in (query.get("contains") or [""])[0].split(",") if c.strip()]
            try:
                return _build_response(200, debug_fl_dir(contains))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/moddir":
            contains = [c.strip() for c in (query.get("contains") or [""])[0].split(",") if c.strip()]
            try:
                dc = int((query.get("doc") or ["600"])[0])
            except ValueError:
                return _build_response(400, {"error": '"doc" must be an integer'})
            try:
                return _build_response(200, debug_mod_dir((query.get("module") or [None])[0], (query.get("name") or [None])[0], contains,
                                                          (query.get("members") or [None])[0], dc, (query.get("stage") or [None])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/fontdir":
            stage = (query.get("stage") or ["dir"])[0]
            attr = (query.get("attr") or [None])[0]
            members = (query.get("members") or [None])[0]
            go = (query.get("go") or [None])[0]
            try:
                return _build_response(200, debug_font_dir(stage, attr.strip() if attr else None, members, go))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/tryfont":
            try:
                return _build_response(200, debug_try_font((query.get("stage") or ["state"])[0], (query.get("go") or [""])[0],
                                                           (query.get("family") or [""])[0], (query.get("mark") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trysync":
            try:
                return _build_response(200, debug_try_sync((query.get("stage") or ["state"])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trycreate":
            try:
                return _build_response(200, debug_try_create((query.get("name") or [""])[0], (query.get("how") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/tryrefresh":
            try:
                return _build_response(200, debug_try_refresh((query.get("stage") or [""])[0], (query.get("name") or [""])[0], (query.get("how") or [""])[0],
                                                              (query.get("value") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trykern":
            try:
                return _build_response(200, debug_try_kern((query.get("a") or [""])[0], (query.get("b") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trypkgkern":
            try:
                return _build_response(200, debug_try_pkg_kern((query.get("a") or [""])[0], (query.get("b") or [""])[0],
                                                               (query.get("master") or [None])[0], (query.get("go") or [""])[0],
                                                               (query.get("mode") or ["tuple"])[0], (query.get("flags") or [None])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/tryopen":
            try:
                return _build_response(200, debug_try_open((query.get("stage") or [""])[0], (query.get("name") or [""])[0],
                                                           (query.get("kind") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/tryedit":
            try:
                return _build_response(200, debug_try_edit((query.get("stage") or [""])[0], (query.get("name") or [""])[0], (query.get("go") or [""])[0],
                                                           (query.get("contour") or [None])[0], (query.get("node") or [None])[0],
                                                           (query.get("dx") or [None])[0], (query.get("dy") or [None])[0],
                                                           (query.get("refresh") or [None])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/markswitch":      # v0.170: S1 research
            return _build_response(200, debug_mark_switch((query.get("on") or [None])[0], (query.get("go") or [""])[0]))

        if path == "/debug/trycomponent":
            try:
                return _build_response(200, debug_try_component((query.get("stage") or [""])[0], (query.get("target") or [""])[0],
                                                                (query.get("source") or [""])[0], (query.get("go") or [""])[0],
                                                                (query.get("dx") or [None])[0], (query.get("dy") or [None])[0],
                                                                (query.get("recipe") or [None])[0], (query.get("args") or [None])[0],
                                                                (query.get("pkg") or [None])[0], (query.get("int") or [None])[0],
                                                                (query.get("width") or [None])[0], (query.get("items") or [None])[0],
                                                                (query.get("step") or [None])[0], (query.get("how") or [None])[0],
                                                                (query.get("element") or [None])[0], (query.get("recursive") or [None])[0],
                                                                (query.get("nonempty") or [None])[0],
                                                                (query.get("brush") or [None])[0], (query.get("sync") or [None])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trynotify":
            try:
                return _build_response(200, debug_try_notify((query.get("stage") or [""])[0], (query.get("which") or [""])[0], (query.get("on") or ["class"])[0],
                                                             (query.get("name") or [""])[0], (query.get("go") or [""])[0], (query.get("id_from") or ["object"])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trypackage":
            try:
                return _build_response(200, debug_try_package((query.get("name") or [""])[0], (query.get("go") or [""])[0],
                                                              (query.get("stage") or ["glyph"])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trynames":
            try:
                return _build_response(200, debug_try_names((query.get("stage") or [""])[0], (query.get("field") or [""])[0],
                                                            (query.get("value") or [""])[0], (query.get("go") or [""])[0],
                                                            (query.get("which") or ["content"])[0], (query.get("full") or ["yes"])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/tryshapebox":
            try:
                return _build_response(200, debug_try_shapebox((query.get("stage") or [""])[0], (query.get("name") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trysetkern":
            try:
                return _build_response(200, debug_try_set_kern((query.get("a") or [""])[0], (query.get("b") or [""])[0], (query.get("value") or [""])[0],
                                                               (query.get("form") or ["tuple"])[0], (query.get("go") or [""])[0],
                                                               (query.get("left") or ["glyph"])[0], (query.get("right") or ["glyph"])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trydelkern":
            try:
                return _build_response(200, debug_try_del_kern((query.get("a") or [""])[0], (query.get("b") or [""])[0],
                                                               (query.get("form") or ["tuple"])[0], (query.get("go") or [""])[0],
                                                               (query.get("left") or ["glyph"])[0], (query.get("right") or ["glyph"])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trykerngroupedit":      # v0.199: rename or remove one kerning group (research, gated)
            try:
                return _build_response(200, debug_try_kern_group_edit((query.get("op") or [""])[0], (query.get("name") or [""])[0],
                                                                      (query.get("new") or [""])[0], (query.get("pairs") or [""])[0],
                                                                      (query.get("glyph") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trykernrefresh":
            try:
                return _build_response(200, debug_try_kern_refresh((query.get("stage") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trykerngroups":
            try:
                return _build_response(200, debug_try_kern_groups((query.get("stage") or [""])[0],
                                                                  [c.strip() for c in (query.get("contains") or [""])[0].split(",") if c.strip()],
                                                                  (query.get("name") or [None])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/features":
            try:
                return _build_response(200, debug_features((query.get("stage") or [""])[0], (query.get("tag") or [None])[0], (query.get("go") or [""])[0],
                                                           [c.strip() for c in (query.get("contains") or [""])[0].split(",") if c.strip()]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trygroups":
            try:
                return _build_response(200, debug_try_groups((query.get("go") or [""])[0], (query.get("contains") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/trymodern":
            try:
                return _build_response(200, debug_try_modern((query.get("stage") or ["state"])[0], (query.get("how") or [""])[0],
                                                             (query.get("name") or [""])[0], (query.get("go") or [""])[0]))
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/debug/layeritem":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            idx_list = query.get("index")
            try:
                idx = int(idx_list[0]) if idx_list else 0
            except ValueError:
                return _build_response(400, {"error": '"index" must be an integer'})
            try:
                return _build_response(200, debug_layer_item(names[0].strip(), idx))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/width":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, get_glyph_width(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/sidebearings":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, get_glyph_sidebearings(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/unicode":
            names = query.get("name")
            if not names or not names[0].strip():
                return _build_response(400, {"error": "provide ?name=<glyph name>"})
            try:
                return _build_response(200, get_glyph_unicode(names[0].strip()))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/kerning/pairs":
            try:
                result = get_kerning_pairs((query.get("pairs") or [None])[0], (query.get("text") or [None])[0])
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/kerning/groups":        # v0.190 (P1.6): ?groups=a,b&glyphs=c,d or ?all=yes[&confirmed=yes]
            flags = {}
            for key in ("all", "confirmed"):
                raw = (query.get(key) or [None])[0]
                if raw not in (None, "yes"):
                    return _build_response(400, {"error": f'"{key}" must be "yes" or left out'})
                flags[key] = raw == "yes"
            try:
                result = get_kerning_groups([n.strip() for n in (query.get("groups") or [""])[0].split(",") if n.strip()],
                                            [n.strip() for n in (query.get("glyphs") or [""])[0].split(",") if n.strip()],
                                            flags["all"], flags["confirmed"])
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/shutdown":
            return _build_response(200, {"status": "shutting down"})

        return _build_response(404, {"error": "unknown endpoint", "path": path})

    if method == "POST":
        if path == "/kerning/pairs":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) - {"pairs", "text"}:
                return _build_response(400, {"error": 'the body must be a JSON object with "pairs" (a list of [left, right]) or "text" (a string), and nothing else'})
            body_pairs, body_text = payload.get("pairs"), payload.get("text")
            if (body_pairs is not None and not isinstance(body_pairs, list)) or (body_text is not None and not isinstance(body_text, str)):
                return _build_response(400, {"error": '"pairs" must be a list of [left, right] lists and "text" must be a string'})
            try:
                result = get_kerning_pairs(body_pairs, body_text)
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/kerning/groups":        # v0.190 (P1.6)
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) - {"groups", "glyphs", "all_groups", "confirmed_large_read"}:
                return _build_response(400, {"error": 'the body must be a JSON object with "groups" and / or "glyphs" (lists of names), or '
                                                      '"all_groups": true, optionally "confirmed_large_read", and nothing else'})
            try:
                result = get_kerning_groups(payload.get("groups"), payload.get("glyphs"), payload.get("all_groups", False),
                                            payload.get("confirmed_large_read", False))
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/kerning/set":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) != {"pairs"}:
                return _build_response(400, {"error": 'the body must be a JSON object with "pairs" (a list of [left, right, value]) and nothing else'})
            try:
                result = set_kerning_pairs(payload["pairs"])
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/kerning/remove":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) != {"pairs"}:
                return _build_response(400, {"error": 'the body must be a JSON object with "pairs" (a list of [left, right]) and nothing else'})
            try:
                result = remove_kerning_pairs(payload["pairs"])
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path in ("/kerning/group/rename", "/kerning/group/remove"):      # v0.200
            rename = path == "/kerning/group/rename"
            keys = {"group", "new_name"} if rename else {"group", "pairs"}
            optional = set() if rename else {"dialog_seconds"}     # v0.203
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or not (keys <= set(payload) <= keys | optional):
                return _build_response(400, {"error": "the body must be a JSON object with " + " and ".join(f'"{k}"' for k in sorted(keys))
                                         + (' (and optionally "dialog_seconds")' if optional else "") + " and nothing else"})
            seconds, serr = _dialog_seconds(payload.get("dialog_seconds"))
            if serr:
                return _build_response(400, {"error": serr})
            try:
                result = (rename_kerning_group(payload["group"], payload["new_name"]) if rename
                          else remove_kerning_group(payload["group"], payload["pairs"], seconds))
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/changes":                 # v0.204: the change log (bookkeeping only; never touches FontLab)
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) - {"run", "since", "server_run", "ask_ids"}:
                return _build_response(400, {"error": 'the body must be a JSON object with optional "run", "since", "server_run" and '
                                                      '"ask_ids", and nothing else'})
            result = changes_report(payload.get("run"), payload.get("since"), payload.get("server_run"), payload.get("ask_ids"))
            if "bad_request" in result:
                return _build_response(400, {"error": result["bad_request"]})
            return _build_response(200, result)

        if path == "/font/notdef/warn":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict):
                return _build_response(400, {"error": "request body must be a JSON object"})
            try:
                return _build_response(200, warn_notdef(force=payload.get("force") is True))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/font/create":       # v0.146
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict) or set(payload) - {"family"}:
                return _build_response(400, {"error": 'the body must be a JSON object with an optional "family" (a string) and nothing else'})
            family = payload.get("family")
            if family is not None and not isinstance(family, str):
                return _build_response(400, {"error": '"family" must be a string, or left out for FontLab\'s own name'})
            try:
                result = create_font(family)
                if "bad_request" in result:
                    return _build_response(400, {"error": result["bad_request"]})
                _open_font()             # the reply names the font in front, the new one when it was made
                return _build_response(200, result)
            except Exception as exc:
                return _build_response(500, {"error": f"{type(exc).__name__}: {exc}"})

        if path == "/glyph/create":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            try:
                return _build_response(200, create_glyph(name.strip(), payload.get("scan_unicode")))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/delete":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            seconds, serr = _dialog_seconds(payload.get("dialog_seconds"))   # v0.203
            if serr:
                return _build_response(400, {"error": serr})
            try:
                return _build_response(200, delete_glyph(name.strip(), seconds))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/width":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            width = payload.get("width") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            if isinstance(width, bool) or not isinstance(width, (int, float)):
                return _build_response(400, {"error": '"width" must be a number'})
            if width < 0:
                return _build_response(400, {"error": '"width" must not be negative'})
            try:
                return _build_response(200, set_glyph_width(name.strip(), float(width)))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/polygon":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            points = payload.get("points") if isinstance(payload, dict) else None
            many = payload.get("contours") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            if (points is None) == (many is None):
                return _build_response(400, {"error": 'give exactly one of "points" (one contour) or "contours" (a list of point lists)'})
            lists = [points] if many is None else many
            if many is not None and (not isinstance(many, list) or not (1 <= len(many) <= _POLY_MAX_CONTOURS)):
                return _build_response(400, {"error": f'"contours" must be a list of 1 to {_POLY_MAX_CONTOURS} point lists'})
            label = '"points"' if many is None else 'every contour'
            clean_contours = []
            for plist in lists:
                if not isinstance(plist, list) or not (_POLY_MIN_POINTS <= len(plist) <= _POLY_MAX_POINTS):
                    return _build_response(400, {"error": f'{label} must be a list of {_POLY_MIN_POINTS} to {_POLY_MAX_POINTS} [x, y] pairs'})
                clean_points = []
                for pt in plist:
                    if (not isinstance(pt, (list, tuple)) or len(pt) != 2
                            or any(isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or abs(v) > 20000 for v in pt)):
                        return _build_response(400, {"error": 'every point must be [x, y] with numbers between -20000 and 20000'})
                    clean_points.append((float(pt[0]), float(pt[1])))
                if len(set(clean_points)) < 3:
                    return _build_response(400, {"error": "each contour must contain at least 3 different positions" if many is not None
                                                 else "the points must contain at least 3 different positions"})
                clean_contours.append(clean_points)
            if sum(len(c) for c in clean_contours) > _POLY_MAX_TOTAL:
                return _build_response(400, {"error": f"at most {_POLY_MAX_TOTAL} points in total"})
            rounded_contours, rounded_report = _path_apply_rule_b([[{"x": x, "y": y} for x, y in c] for c in clean_contours])
            clean_contours = [[(p["x"], p["y"]) for p in c] for c in rounded_contours]
            if any(len(set(c)) < 3 for c in clean_contours):
                return _build_response(400, {"error": "each contour must contain at least 3 different positions after rounding to whole units"})
            try:
                return _build_response(200, draw_polygon(name.strip(), clean_contours, rounded_report))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/path":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            many = payload.get("contours") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            if not isinstance(many, list) or not (1 <= len(many) <= _POLY_MAX_CONTOURS):
                return _build_response(400, {"error": f'"contours" must be a list of 1 to {_POLY_MAX_CONTOURS} point lists'})

            def _num(v):
                return not (isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or abs(v) > 20000)

            def _xy(d):
                if not isinstance(d, dict) or set(d) - {"x", "y"} or not _num(d.get("x")) or not _num(d.get("y")):
                    return None
                return (float(d["x"]), float(d["y"]))

            parsed, flags = [], []
            for ci, item in enumerate(many):
                plist, closed = item, True             # v0.126: a contour is a point list (closed) or {"points": [...], "closed": bool}
                if isinstance(item, dict):
                    if "points" not in item or set(item) - {"points", "closed"}:
                        return _build_response(400, {"error": f'contour {ci}: a contour object has "points" and optionally "closed"'})
                    plist, closed = item["points"], item.get("closed", True)
                    if not isinstance(closed, bool):
                        return _build_response(400, {"error": f"contour {ci}: closed must be true or false"})
                low = _POLY_MIN_POINTS if closed else _PATH_OPEN_MIN_POINTS
                if not isinstance(plist, list) or not (low <= len(plist) <= _POLY_MAX_POINTS):
                    return _build_response(400, {"error": f"contour {ci} must be a list of {low} to {_POLY_MAX_POINTS} points"
                                                          + ("" if closed else " (an open contour)")})
                flags.append(closed)
                pts = []
                for pi, pt in enumerate(plist):
                    where = f"contour {ci} point {pi}"
                    if not isinstance(pt, dict) or set(pt) - {"x", "y", "c1", "c2", "smooth"}:
                        return _build_response(400, {"error": f'{where}: a point is an object with x, y and optional c1, c2, smooth'})
                    if not _num(pt.get("x")) or not _num(pt.get("y")):
                        return _build_response(400, {"error": f"{where}: x and y must be numbers between -20000 and 20000"})
                    if (pt.get("c1") is None) != (pt.get("c2") is None):
                        return _build_response(400, {"error": f"{where}: c1 and c2 must be given together or not at all"})
                    c1 = c2 = None
                    if pt.get("c1") is not None:
                        c1, c2 = _xy(pt.get("c1")), _xy(pt.get("c2"))
                        if c1 is None or c2 is None:
                            return _build_response(400, {"error": f"{where}: c1 and c2 must be {{x, y}} objects with numbers between -20000 and 20000"})
                    smooth = pt.get("smooth", False)
                    if not isinstance(smooth, bool):
                        return _build_response(400, {"error": f"{where}: smooth must be true or false"})
                    pts.append({"x": float(pt["x"]), "y": float(pt["y"]), "c1": c1, "c2": c2, "smooth": smooth})
                parsed.append(pts)
            if sum(len(c) for c in parsed) + 2 * sum(1 for c in parsed for p in c if p["c1"] is not None) > _POLY_MAX_TOTAL:
                return _build_response(400, {"error": f"at most {_POLY_MAX_TOTAL} nodes in total (every curved segment counts its two handles)"})
            rounded_contours, rounded_report = _path_apply_rule_b(parsed)
            try:
                return _build_response(200, draw_path(name.strip(), rounded_contours, rounded_report, flags))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/component/remove":       # v0.179: remove_component
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if not isinstance(payload, dict):
                return _build_response(400, {"error": "the body must be a JSON object"})
            if "components" in payload:
                if set(payload) != {"name", "components"}:
                    return _build_response(400, {"error": 'the list form takes exactly "name" and "components"'})
                raw, form = payload["components"], "list"
                if not isinstance(raw, list) or not raw:
                    return _build_response(400, {"error": '"components" must be a non-empty list'})
            else:
                if set(payload) != {"name", "index", "component", "x", "y"}:
                    return _build_response(400, {"error": 'the body must be an object with exactly "name", "index", "component", "x" and "y", or "name" and "components"'})
                raw, form = [{k: payload[k] for k in ("index", "component", "x", "y")}], "single"
            name = payload["name"]
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            entries, seen = [], set()
            for i, c in enumerate(raw):
                where = f"components[{i}]" if form == "list" else "the request"
                if not isinstance(c, dict) or set(c) != {"index", "component", "x", "y"}:
                    return _build_response(400, {"error": f'{where} must be an object with exactly "index", "component", "x" and "y"'})
                idx, cn = c["index"], c["component"]
                if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
                    return _build_response(400, {"error": f'{where}: "index" must be a whole number from 0'})
                if idx in seen:
                    return _build_response(400, {"error": f'{where}: index {idx} appears twice; give each component once'})
                seen.add(idx)
                if not isinstance(cn, str) or not cn.strip():
                    return _build_response(400, {"error": f'{where}: "component" must be a non-empty glyph name'})
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or abs(v) > 2 * _COMP_OFFSET_MAX for v in (c["x"], c["y"])):
                    return _build_response(400, {"error": f'{where}: "x" and "y" must be numbers from -{2 * _COMP_OFFSET_MAX} to {2 * _COMP_OFFSET_MAX}'})
                entries.append({"index": idx, "component": cn.strip(), "x": c["x"], "y": c["y"]})
            try:
                return _build_response(200, remove_components(name.strip(), entries, form))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/component":       # v0.169: add_component
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            if isinstance(payload, dict) and "components" in payload:      # v0.174: several components in one call
                if not {"name", "components"} <= set(payload) <= {"name", "components", "confirmed_untested_size"}:
                    return _build_response(400, {"error": 'the list form takes exactly "name" and "components", and optionally "confirmed_untested_size"'})
                name, comps, conf = payload["name"], payload["components"], payload.get("confirmed_untested_size", False)
                if not isinstance(name, str) or not name.strip():
                    return _build_response(400, {"error": '"name" must be a non-empty string'})
                if not isinstance(conf, bool):
                    return _build_response(400, {"error": '"confirmed_untested_size" must be true or false'})
                if not isinstance(comps, list) or not comps:
                    return _build_response(400, {"error": '"components" must be a non-empty list'})
                entries = []
                for i, c in enumerate(comps):
                    if not isinstance(c, dict) or set(c) != {"component", "x", "y"}:
                        return _build_response(400, {"error": f'components[{i}] must be an object with exactly "component", "x" and "y"'})
                    cn = c["component"]
                    if not isinstance(cn, str) or not cn.strip() or "+" in cn:
                        return _build_response(400, {"error": f'components[{i}].component must be a non-empty glyph name without "+"'})
                    if any(isinstance(v, bool) or not isinstance(v, int) or abs(v) > _COMP_OFFSET_MAX for v in (c["x"], c["y"])):
                        return _build_response(400, {"error": f'components[{i}]: "x" and "y" must be whole numbers from -{_COMP_OFFSET_MAX} to {_COMP_OFFSET_MAX}'})
                    entries.append({"component": cn.strip(), "x": c["x"], "y": c["y"]})
                try:
                    return _build_response(200, add_components(name.strip(), entries, conf))
                except Exception as exc:
                    return _build_response(500, {"error": str(exc)})
            if not isinstance(payload, dict) or set(payload) != {"name", "component", "x", "y"}:
                return _build_response(400, {"error": 'the body must be an object with exactly "name", "component", "x" and "y"'})
            name, src = payload["name"], payload["component"]
            if not isinstance(name, str) or not name.strip() or not isinstance(src, str) or not src.strip():
                return _build_response(400, {"error": '"name" and "component" must be non-empty strings'})
            if name.strip() == src.strip():
                return _build_response(400, {"error": "a glyph cannot hold itself as a component"})
            ox, oy = payload["x"], payload["y"]
            if any(isinstance(v, bool) or not isinstance(v, int) or abs(v) > _COMP_OFFSET_MAX for v in (ox, oy)):
                return _build_response(400, {"error": f'"x" and "y" must be whole numbers from -{_COMP_OFFSET_MAX} to {_COMP_OFFSET_MAX}'})
            try:
                return _build_response(200, add_component(name.strip(), src.strip(), ox, oy))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/move":            # v0.153: move_nodes
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            moves = payload.get("moves") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            if not isinstance(moves, list) or not (1 <= len(moves) <= _MOVE_MAX):
                return _build_response(400, {"error": f'"moves" must be a list of 1 to {_MOVE_MAX} moves'})

            def _mv_num(v):
                return not (isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or abs(v) > 20000)

            def _mv_index(v):
                return isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= _MOVE_INDEX_MAX

            clean_moves, rounded, seen = [], [], set()
            for i, mv in enumerate(moves):
                if not isinstance(mv, dict) or set(mv) != {"contour", "node", "from", "to"}:
                    return _build_response(400, {"error": f'move {i}: a move is an object with exactly "contour", "node", "from" and "to"'})
                if not _mv_index(mv["contour"]) or not _mv_index(mv["node"]):
                    return _build_response(400, {"error": f"move {i}: contour and node must be whole numbers from 0 to {_MOVE_INDEX_MAX}"})
                pair = {}
                for key in ("from", "to"):
                    xy = mv[key]
                    if not isinstance(xy, dict) or set(xy) != {"x", "y"} or not _mv_num(xy["x"]) or not _mv_num(xy["y"]):
                        return _build_response(400, {"error": f"move {i}: {key} must be an {{x, y}} object with numbers between -20000 and 20000"})
                    pair[key] = (float(xy["x"]), float(xy["y"]))
                if (mv["contour"], mv["node"]) in seen:
                    return _build_response(400, {"error": f"move {i}: contour {mv['contour']} node {mv['node']} is moved twice in this request"})
                seen.add((mv["contour"], mv["node"]))
                to = []
                for j, field in enumerate(("x", "y")):
                    used = _round_half_up(pair["to"][j])
                    if used != pair["to"][j]:
                        rounded.append({"move": i, "field": "to." + field, "requested": pair["to"][j], "used": used})
                    to.append(used)
                if abs(to[0] - pair["from"][0]) <= _MOVE_FROM_TOLERANCE and abs(to[1] - pair["from"][1]) <= _MOVE_FROM_TOLERANCE:
                    return _build_response(400, {"error": f"move {i}: to equals from (after rounding to whole units): nothing would move"})
                clean_moves.append({"contour": mv["contour"], "node": mv["node"], "from": pair["from"], "to": (to[0], to[1])})
            try:
                return _build_response(200, move_nodes(name.strip(), clean_moves, rounded))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/sidebearings":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            left = payload.get("left") if isinstance(payload, dict) else None
            right = payload.get("right") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            for label, val in (("left", left), ("right", right)):
                if isinstance(val, bool) or not isinstance(val, (int, float)) or val != val or abs(val) > 10000:
                    return _build_response(400, {"error": f'"{label}" must be a number between -10000 and 10000'})
            try:
                return _build_response(200, set_glyph_sidebearings(name.strip(), float(left), float(right)))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/glyph/unicode":
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except (UnicodeDecodeError, json.JSONDecodeError):
                return _build_response(400, {"error": "request body was not valid JSON"})
            name = payload.get("name") if isinstance(payload, dict) else None
            codepoint = payload.get("unicode") if isinstance(payload, dict) else None
            if not isinstance(name, str) or not name.strip():
                return _build_response(400, {"error": '"name" must be a non-empty string'})
            if isinstance(codepoint, bool) or not isinstance(codepoint, int):
                return _build_response(400, {"error": '"unicode" must be an integer codepoint'})
            if codepoint < 0 or codepoint > 0x10FFFF:
                return _build_response(400, {"error": '"unicode" must be between 0 and 0x10FFFF'})
            try:
                return _build_response(200, set_glyph_unicode(name.strip(), codepoint))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        return _build_response(404, {"error": "unknown endpoint", "path": path})

    return _build_response(404, {"error": "unsupported method", "method": method})


def _parse_headers(head_bytes):
    headers = {}
    for line in head_bytes.decode("latin-1").split("\r\n")[1:]:
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        headers[k.strip().lower()] = v.strip()
    return headers


# --------------------------------------------------------------------------
# Activity log in FontLab's OUTPUT panel (v0.102). One short line per change, built ONLY from the request and the reply
# (never a fontlab call), so it says "verified" only where the reply's own re-read says so. Refusals, errors, declined
# deletes, unverified or unsynced results and gated probes (go=yes) are always printed. A run of the same verified change
# shows _ACTIVITY_RUN_SHOWN lines and then one "N more like this" line; reads are only counted and printed as one
# "reads:" line. Both summaries are printed when a different change starts, after _ACTIVITY_IDLE_S seconds without a
# request (checked by the poll timer), or at /shutdown. Every entry point swallows its own errors: logging can never
# change a reply. v0.105: every line names the client that sent the X-Glyphbridge-Client header (its own claim, not
# checked); the summaries are printed when the client changes, so one line never mixes two clients. A read answered
# {"open": false} is listed under "no font open" instead of as a read. v0.109: a line without a client name starts with
# "[Glyphbridge]" (no guessed name); a new (client, X-Glyphbridge-Launcher) pair gets one "[glyphbridge] <client> |
# <LAUNCHER>" line in every log mode, like the "Connected" line.
# --------------------------------------------------------------------------
_ACTIVITY_LOG = "normal"     # "normal" (changes and read summaries), "writes" (changes only) or "off"
_ACTIVITY_RUN_SHOWN = 3      # verified changes of one kind printed in a row before they are only counted
_ACTIVITY_IDLE_S = 10.0      # an agent's tool calls arrive seconds apart, so a shorter pause would split one run into many
_ACTIVITY_TEXT_MAX = 120     # longest reason or name quoted in a line
_ACTIVITY_CLIENT_MAX = 40    # longest client name shown
_ACTIVITY_LAUNCHER_MAX = 40  # longest launcher name shown (the server sends one file name of at most 40 characters)
_ACTIVITY_SHORT_REPLY = 4096  # only replies up to this size are parsed for "open": false (a no-font reply is tiny)

_ACT = {"kind": None, "shown": 0, "more": 0, "reads": {}, "no_font": {}, "kern_pairs": 0, "read_errors": 0, "last": 0.0,
        "pending": False, "client": None}

_ACT_WRITES = {"/glyph/create": "create", "/glyph/delete": "delete", "/glyph/width": "width",
               "/glyph/sidebearings": "sidebearings", "/glyph/unicode": "unicode", "/glyph/polygon": "draw",
               "/glyph/path": "draw", "/font/notdef/warn": ".notdef", "/kerning/set": "kerning", "/kerning/remove": "kerning remove", "/font/create": "create font",
               "/kerning/group/rename": "kerning group rename", "/kerning/group/remove": "kerning group remove",
               "/glyph/move": "move", "/glyph/component": "component", "/glyph/component/remove": "remove component"}
_ACT_READS = {"/glyph/outline": "outline", "/glyph/nodes": "nodes", "/glyph/width": "width",
              "/glyph/sidebearings": "sidebearings", "/glyph/unicode": "unicode", "/font/glyphs": "glyph list",
              "/font/current": "font info", "/font/notdef": ".notdef check", "/font/notdef/warn": ".notdef check",
              "/font/nonempty": "empty-glyph scan", "/kerning/pairs": "kerning", "/kerning/groups": "kerning groups",
              "/changes": "change log"}
_ACT_SILENT = ("/health", "/version", "/shutdown")


def _now_hms():
    return datetime.datetime.now().strftime("%H:%M:%S")


def _clock():
    return time.monotonic()


def _act_print(text):
    who = f"[{_ACT['client']} > Glyphbridge]" if _ACT["client"] else "[Glyphbridge]"
    print(f"{who} {_now_hms()} {text}")


def _act_client(raw):
    """The client name sent in the X-Glyphbridge-Client header (percent-encoded UTF-8), cleaned for one line, or None."""
    if not isinstance(raw, str):
        return None
    text = "".join(ch for ch in unquote(raw, errors="replace") if not (ord(ch) < 32 or 127 <= ord(ch) <= 159))
    name = " ".join(text.split())
    at = name.lower().find(ENTRY_NAME)
    end = at + len(ENTRY_NAME)
    if at >= 0 and (at == 0 or name[at - 1] in "-_. ") and (end == len(name) or name[end] in "-_. "):
        # leave out the config entry name (a whole word only), which only repeats Glyphbridge; keep the name if nothing else is left
        rest = " ".join(part for part in (name[:at].rstrip("-_. "), name[end:].lstrip("-_. ")) if part)
        name = rest or name
    return name[:_ACTIVITY_CLIENT_MAX] or None


def _act_launcher(raw):
    """The X-Glyphbridge-Launcher value (percent-encoded UTF-8, a file name such as "claude.exe") as shown, or None:
    cleaned for one line, only the first name when an older server sent "a < b" (v0.109), one final ".exe" removed and
    in capitals ("CLAUDE"; a macOS name has no extension, v0.110). The server's own reading, not checked here."""
    if not isinstance(raw, str):
        return None
    text = "".join(ch for ch in unquote(raw, errors="replace") if not (ord(ch) < 32 or 127 <= ord(ch) <= 159))
    name = " ".join(text.split()).split(" < ")[0].strip()
    if name.lower().endswith(".exe"):
        name = name[:-4].rstrip()
    return name.upper()[:_ACTIVITY_LAUNCHER_MAX] or None


def _act_announce(client, launcher):
    """Print one "[glyphbridge] <client> | <LAUNCHER>" line the first time a (client, launcher) pair comes in this
    listener run; the pending summaries go first. Without a launcher nothing is printed (v0.109, v0.110)."""
    if not launcher or (client, launcher) in _announced_clients:
        return
    _announced_clients.add((client, launcher))
    _act_flush()
    print(f"[glyphbridge] {client} | {launcher}" if client else f"[glyphbridge] {launcher}")


def _act_dialog_seconds(reply):
    """v0.203 - the seconds a self-closing dialog waited, from the reply's "dialog"; None when absent."""
    dialog = reply.get("dialog") if isinstance(reply.get("dialog"), dict) else {}
    return dialog.get("seconds")


def _act_text(value):
    text = " ".join(str(value).split())
    return text if len(text) <= _ACTIVITY_TEXT_MAX else text[:_ACTIVITY_TEXT_MAX - 3] + "..."


def _act_num(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "?"
    if float(value).is_integer():
        return str(int(value))
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("0", "-0") else text


def _act_codepoint(value):
    return f"U+{value:04X}" if isinstance(value, int) and not isinstance(value, bool) else "none"


def _act_flush():
    """Print the pending run summary, then the pending reads summary, and forget both."""
    if _ACT["more"]:
        _act_print(f"{_ACT['kind']}: {_ACT['more']} more like this, all verified")
    if _ACT["reads"] or _ACT["no_font"]:
        parts = [f"{label} {n} ({_ACT['kern_pairs']} pairs)" if label == "kerning" else f"{label} {n}"
                 for label, n in _ACT["reads"].items()]
        errors = f" ({_ACT['read_errors']} refused or failed)" if _ACT["read_errors"] else ""
        segments = [", ".join(parts) + errors] if parts else []
        if _ACT["no_font"]:
            segments.append("no font open: " + ", ".join(f"{label} {n}" for label, n in _ACT["no_font"].items()))
        _act_print("reads: " + "; ".join(segments))
    _ACT.update(kind=None, shown=0, more=0, reads={}, no_font={}, kern_pairs=0, read_errors=0, pending=False)


def _act_change(kind, text, collapsible):
    if collapsible and kind == _ACT["kind"]:
        if _ACT["shown"] < _ACTIVITY_RUN_SHOWN:
            _ACT["shown"] += 1
            _act_print(text)
        else:
            _ACT["more"] += 1
        return
    _act_flush()
    _act_print(text)
    if collapsible:
        _ACT.update(kind=kind, shown=1)


def _act_describe_write(path, payload, code, reply):
    """(line, collapsible) for one write request, or (None, False) for a .notdef warning request that showed no dialog."""
    kind = _ACT_WRITES[path]
    if kind == "kerning":
        return _act_describe_kerning(payload, code, reply)
    if kind == "kerning remove":
        return _act_describe_kerning_remove(payload, code, reply)
    if kind in ("kerning group rename", "kerning group remove"):
        return _act_describe_kerning_group(kind, payload, code, reply)
    if kind == "create font":
        return _act_describe_font(payload, code, reply)
    name = payload.get("name") if isinstance(payload, dict) else None
    head = f"{kind} {_act_text(name.strip())}" if isinstance(name, str) and name.strip() else (kind if kind == ".notdef" else f"{kind} ?")
    if code != 200 or not isinstance(reply, dict):
        error = reply.get("error") if isinstance(reply, dict) else None
        return f"{'REFUSED' if code == 400 else 'FAILED'} {head}: {_act_text(error or f'HTTP {code}')}", False
    if reply.get("open") is False:
        return f"REFUSED {head}: no font is open", False
    why = _act_text(reply.get("reason") or reply.get("call_error") or "not confirmed by the re-read")
    unsynced = reply.get("synced_with_fontlab") is False
    sync = ", NOT synced with FontLab" if unsynced else ""
    if kind == ".notdef":
        if reply.get("noted") is True and reply.get("status") in _NOTDEF_OUTPUT:   # v0.203: the note, no dialog
            maturity = reply.get("maturity") if isinstance(reply.get("maturity"), dict) else {}
            mature = _NOTDEF_OUTPUT_MATURE if reply["status"] == "empty" and maturity.get("mature") is True else ""
            return f"note: {_NOTDEF_OUTPUT[reply['status']]}{mature}", False
        return None, False
    if kind == "create":
        if reply.get("created") is True:
            return f"{head}: created (verified, glyphs {_act_num(reply.get('before_count'))} -> {_act_num(reply.get('after_count'))})", True
        others = reply.get("created_under_other_names")
        instead = f"; FontLab created {_act_text(', '.join(map(str, others)))} instead" if others else ""
        return f"NOT DONE {head}: {why}{instead}", False
    if kind == "delete":
        if reply.get("deleted") is True:
            return f"{head}: deleted after your Yes (verified, glyphs {_act_num(reply.get('before_count'))} -> {_act_num(reply.get('after_count'))})", False
        if reply.get("user_declined") is True:
            return f"{head}: you answered No in FontLab, nothing deleted", False
        if reply.get("not_answered") is True:   # v0.203
            return f"{head}: not answered within {_act_num(_act_dialog_seconds(reply))} s, nothing deleted", False
        return f"NOT DONE {head}: {why}", False
    if kind == "width":
        if reply.get("set") is True:
            warning = f"; WARNING: {_act_text(reply['warning'])}" if reply.get("warning") else ""
            rounded = reply.get("width_rounded")
            rnote = f"rounded from {_act_num(rounded.get('requested'))}, " if isinstance(rounded, dict) else ""   # v0.197
            line = f"{head}: {_act_num(reply.get('before'))} -> {_act_num(reply.get('after'))} ({rnote}verified{sync}){warning}"
            return line, not (warning or unsynced)
        if reply.get("changed") is True:  # v0.197 (AW 1449): the width moved, but not to the request; never "NOT DONE"
            return f"CHANGED, NOT AS ASKED {head}: {_act_num(reply.get('before'))} -> {_act_num(reply.get('after'))}: {why}", False
        return f"NOT DONE {head}: {why}", False
    if kind == "sidebearings":
        if reply.get("set") is True:
            after = reply.get("after") if isinstance(reply.get("after"), dict) else {}
            same = ", already so" if reply.get("changed") is False else ""
            return f"{head}: L {_act_num(after.get('lsb'))}, R {_act_num(after.get('rsb'))} (verified{same}{sync})", not unsynced
        return f"NOT DONE {head}: {why}", False
    if kind == "unicode":
        if reply.get("set") is True:
            return f"{head}: {_act_codepoint(reply.get('before'))} -> {_act_codepoint(reply.get('after'))} (verified)", True
        return f"NOT DONE {head}: {why}", False
    if kind == "move":            # v0.153: the count from the request, success from the reply
        moves = payload.get("moves") if isinstance(payload, dict) else None
        size = f"{len(moves)} node{'' if len(moves) == 1 else 's'}" if isinstance(moves, list) else "size unreadable"
        if reply.get("moved") is True:
            return f"{head}: {size} (verified, nodes match{sync})", not unsynced
        changed = "; the glyph DID change" if reply.get("changed") not in (False, None) else ""
        return f"NOT DONE {head}: {why}{changed}", False
    if kind == "component" and isinstance(payload, dict) and isinstance(payload.get("components"), list):     # v0.174: the list form
        n = len(payload["components"])
        what = f"{n} component{'' if n == 1 else 's'}"
        if reply.get("placed") is True:
            return f"{head}: {what} (verified{sync})", not unsynced
        changed = "; the glyph DID change" if reply.get("changed") not in (False, None) else ""
        if reply.get("untested_size") is True:
            return f"NOT DONE {head} ({what}): more than 30, waiting for the person's agreement", False
        return f"NOT DONE {head} ({what}): {why}{changed}", False
    if kind == "remove component":       # v0.179: how many from the request, success from the reply
        comps = payload.get("components") if isinstance(payload, dict) else None
        n = len(comps) if isinstance(comps, list) else 1 if isinstance(payload, dict) and "index" in payload else None
        what = f"{n} component{'' if n == 1 else 's'}" if n is not None else "size unreadable"
        if reply.get("removed") is True:
            return f"{head}: {what} (verified{sync})", not unsynced
        changed = "; the glyph DID change" if reply.get("changed") not in (False, None) else ""
        return f"NOT DONE {head} ({what}): {why}{changed}", False
    if kind == "component":       # v0.169: what from the request, success from the reply
        src = payload.get("component") if isinstance(payload, dict) else None
        at = f"({_act_num(payload.get('x'))}, {_act_num(payload.get('y'))})" if isinstance(payload, dict) else "(?)"
        what = f"{_act_text(src) if isinstance(src, str) else '?'} at {at}"
        if reply.get("placed") is True:
            return f"{head}: {what} (verified{sync})", not unsynced
        changed = "; the glyph DID change" if reply.get("changed") not in (False, None) else ""
        back = "; autoLayer set back to off" if reply.get("auto_layer_set_back") is True else ""
        return f"NOT DONE {head} ({what}): {why}{changed}{back}", False
    # draw (/glyph/polygon or /glyph/path): sizes from the request, success from the reply
    payload = payload if isinstance(payload, dict) else {}
    lists = payload.get("contours") if payload.get("contours") is not None else [payload.get("points")]
    lists = lists if isinstance(lists, list) else []
    n_open = sum(1 for c in lists if isinstance(c, dict) and c.get("closed") is False)      # v0.126: {"points": [...], "closed": false}
    lists = [c.get("points") if isinstance(c, dict) else c for c in lists]
    lists = [c for c in lists if isinstance(c, list)]
    points = sum(len(c) for c in lists)
    curved = sum(1 for c in lists for p in c if isinstance(p, dict) and p.get("c1") is not None)
    size = (f"{len(lists)} contour{'' if len(lists) == 1 else 's'}, {points} points" + (f", {curved} curved" if curved else "")
            + (f", {n_open} open" if n_open else "") if points else "size unreadable")
    if reply.get("drawn") is True:
        match = ", nodes match" if reply.get("nodes_match") is True else ""
        return f"{head}: {size} (verified{match}{sync})", not unsynced
    changed = "; the glyph DID change" if reply.get("changed") is True else ""
    return f"NOT DONE {head}: {why}{changed}", False


def _act_describe_kerning(payload, code, reply):
    """(line, collapsible) for one /kerning/set request (v0.124): one pair is named with its values, more are counted."""
    pairs = payload.get("pairs") if isinstance(payload, dict) else None
    n = len(pairs) if isinstance(pairs, list) else None
    head = f"kerning {n} pair{'' if n == 1 else 's'}" if n is not None else "kerning ?"
    if code != 200 or not isinstance(reply, dict):
        error = reply.get("error") if isinstance(reply, dict) else None
        return f"{'REFUSED' if code == 400 else 'FAILED'} {head}: {_act_text(error or f'HTTP {code}')}", False
    if reply.get("open") is False:
        return f"REFUSED {head}: no font is open", False
    if reply.get("error"):
        return f"REFUSED {head}: {_act_text(reply['error'])}", False
    results = [e for e in reply.get("results") or [] if isinstance(e, dict)] if isinstance(reply.get("results"), list) else []
    done = [e for e in results if e.get("set") is True]
    if results and len(done) == len(results):
        if len(done) == 1:
            e = done[0]
            before = e.get("before") if isinstance(e.get("before"), dict) else {}
            after = e.get("after") if isinstance(e.get("after"), dict) else {}
            pair = _act_text(f"{e.get('left')}:{e.get('right')}")
            return f"kerning {pair}: {_act_num(before.get('value'))} -> {_act_num(after.get('value'))} (verified)", True
        return f"{head}: all set (verified)", True
    failed = next((e for e in results if e.get("status") == "failed"), None)
    where = f", stopped at {_act_text(str(failed.get('left')) + ':' + str(failed.get('right')))}: {_act_text(failed.get('reason') or 'not confirmed by the re-read')}" if failed else ""
    return f"NOT DONE {head}: {len(done)} set{where}", False


def _act_describe_kerning_remove(payload, code, reply):
    """(line, collapsible) for one /kerning/remove request (v0.192): one pair is named with its values, more are counted."""
    pairs = payload.get("pairs") if isinstance(payload, dict) else None
    n = len(pairs) if isinstance(pairs, list) else None
    head = f"kerning remove {n} pair{'' if n == 1 else 's'}" if n is not None else "kerning remove ?"
    if code != 200 or not isinstance(reply, dict):
        error = reply.get("error") if isinstance(reply, dict) else None
        return f"{'REFUSED' if code == 400 else 'FAILED'} {head}: {_act_text(error or f'HTTP {code}')}", False
    if reply.get("open") is False:
        return f"REFUSED {head}: no font is open", False
    if reply.get("error"):
        return f"REFUSED {head}: {_act_text(reply['error'])}", False
    results = [e for e in reply.get("results") or [] if isinstance(e, dict)] if isinstance(reply.get("results"), list) else []
    done = [e for e in results if e.get("removed") is True]
    none = [e for e in results if e.get("status") == "no entry"]
    if results and len(done) + len(none) == len(results):
        if len(results) == 1:
            e = results[0]
            pair = _act_text(f"{e.get('left')}:{e.get('right')}")
            if e.get("status") == "no entry":
                kind = e.get("kind") if e.get("kind") in _KERN_KIND_RANK else "glyph : glyph"        # v0.195: a class pair names its kind (CK 1430)
                return f"kerning remove {pair}: no {kind} entry, nothing removed", True
            before = e.get("before") if isinstance(e.get("before"), dict) else {}
            after = e.get("after") if isinstance(e.get("after"), dict) else {}
            return f"kerning remove {pair}: {_act_num(before.get('value'))} -> {_act_num(after.get('value'))} (verified)", True
        extra = f", {len(none)} had no entry" if none else ""
        return f"{head}: {len(done)} removed{extra} (verified)", True
    failed = next((e for e in results if e.get("status") == "failed"), None)
    where = f", stopped at {_act_text(str(failed.get('left')) + ':' + str(failed.get('right')))}: {_act_text(failed.get('reason') or 'not confirmed by the re-read')}" if failed else ""
    return f"NOT DONE {head}: {len(done)} removed{where}", False


def _act_describe_kerning_group(kind, payload, code, reply):
    """(line, collapsible) for one /kerning/group/rename or /kerning/group/remove request (v0.200)."""
    group = payload.get("group") if isinstance(payload, dict) else None
    head = f"{kind} {_act_text(group)}" if isinstance(group, str) and group else f"{kind} ?"
    if code != 200 or not isinstance(reply, dict):
        error = reply.get("error") if isinstance(reply, dict) else None
        return f"{'REFUSED' if code == 400 else 'FAILED'} {head}: {_act_text(error or f'HTTP {code}')}", False
    if reply.get("open") is False:
        return f"REFUSED {head}: no font is open", False
    if reply.get("error"):
        return f"REFUSED {head}: {_act_text(reply['error'])}", False
    caught = reply.get("fontlab_caught_up") if isinstance(reply.get("fontlab_caught_up"), dict) else {}
    lag = "" if caught.get("caught_up") is True else "; FontLab's panels may lag until a font switch"
    if kind == "kerning group rename":
        if reply.get("renamed") is True:
            return (f"{head} -> {_act_text(reply.get('new_name'))}: renamed (verified, id {_act_num(reply.get('id_before'))} -> "
                    f"{_act_num(reply.get('id_after'))}{lag})"), False
        return f"NOT DONE {head}: {_act_text(reply.get('reason') or reply.get('call_error') or 'not confirmed by the re-read')}", False
    if reply.get("user_declined") is True:
        return f"{head}: you answered No in FontLab, nothing removed", False
    if reply.get("not_answered") is True:   # v0.203
        return f"{head}: not answered within {_act_num(_act_dialog_seconds(reply))} s, nothing removed", False
    if reply.get("removed") is True:
        what = "its kerning kept as entries of its members" if reply.get("pairs") == "keep" else "its kerning deleted"
        return (f"{head}: removed after your Yes, {what} (verified, kerning entries {_act_num(reply.get('table_size_before'))} -> "
                f"{_act_num(reply.get('table_size_after'))}{lag})"), False
    return f"NOT DONE {head}: {_act_text(reply.get('reason') or reply.get('call_error') or 'not confirmed by the re-read')}", False


_ACTIVITY_NOTE_MAX = 400     # v0.146: longest note line of /font/create (its notes are whole sentences for the person)


def _act_describe_font(payload, code, reply):
    """(line, collapsible) for one /font/create request (v0.146). The notes are printed after it by _activity_note."""
    family = payload.get("family") if isinstance(payload, dict) else None
    head = f"create font {_act_text(family)}" if isinstance(family, str) and family else "create font (FontLab's own name)"
    if code != 200 or not isinstance(reply, dict):
        error = reply.get("error") if isinstance(reply, dict) else None
        return f"{'REFUSED' if code == 400 else 'FAILED'} {head}: {_act_text(error or f'HTTP {code}')}", False
    before, after = reply.get("fonts_open_before"), reply.get("fonts_open_after")
    if reply.get("created") is True:
        names = reply.get("names_after") if isinstance(reply.get("names_after"), dict) else {}
        parts = [f"fonts {_act_num(before)} -> {_act_num(after)}", "unsaved"]
        if isinstance(family, str) and family:
            parts.append("names set" if reply.get("names_set") is True and reply.get("legacy_family_set") is True else "names NOT all set")
        mark = reply.get("fontlab_changed_mark")
        if isinstance(mark, dict) and mark.get("called") is True and not mark.get("call_error"):
            parts.append("marked as changed")
        return f"{head}: made \"{_act_text(names.get('ffn'))}\" (verified, {', '.join(parts)})", False
    made = ("; a font WAS made" if type(before) is int and type(after) is int and after > before else "")
    return f"NOT DONE {head}: {_act_text(reply.get('reason') or 'not confirmed')}{made}", False


def _act_font_notes(reply):
    """The /font/create notes as lines for the OUTPUT panel (v0.146)."""
    notes = reply.get("notes") if isinstance(reply, dict) and reply.get("created") is True else None
    if not isinstance(notes, list):
        return []
    lines = []
    for note in notes:
        if isinstance(note, str) and note.strip():
            text = " ".join(note.split())
            lines.append("  note: " + (text if len(text) <= _ACTIVITY_NOTE_MAX else text[:_ACTIVITY_NOTE_MAX - 3] + "..."))
    return lines


def _activity_note(method, raw_path, body, response, client=None, launcher=None):
    """Log one served request (called by _handle with the reply about to be sent and the raw X-Glyphbridge-Client
    and X-Glyphbridge-Launcher headers). Never raises."""
    try:
        client = _act_client(client)
        _act_announce(client, _act_launcher(launcher))
        if _ACTIVITY_LOG == "off":
            return
        if client != _ACT["client"]:
            _act_flush()  # the pending summaries belong to the previous client
            _ACT["client"] = client
        split = urlsplit(raw_path)
        path, query = split.path, parse_qs(split.query)
        code = int(response[9:12])

        def reply():
            try:
                return json.loads(response.partition(b"\r\n\r\n")[2].decode("utf-8"))
            except Exception:
                return None

        _ACT["last"], _ACT["pending"] = _clock(), True
        if method == "POST" and path in _ACT_WRITES:
            try:
                payload = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                payload = None
            answer = reply()
            line, collapsible = _act_describe_write(path, payload, code, answer)
            if line:
                _act_change(_ACT_WRITES[path], line, collapsible)
                if path == "/font/create" and code == 200:      # v0.146: what the person must know, in FontLab too
                    for note_line in _act_font_notes(answer):
                        _act_print(note_line)
                return
        elif method == "GET" and path.startswith("/debug/") and "yes" in query.get("go", []):
            answer = reply()
            error = answer.get("error") if isinstance(answer, dict) else None
            if not error and code != 200:
                error = f"HTTP {code}"
            _act_change("probe", f"probe {path} (go=yes): " + (f"error: {_act_text(error)}" if error else "answered"), False)
            return
        if path in _ACT_SILENT or _ACTIVITY_LOG == "writes":
            return
        label = _ACT_READS.get(path) or ("probe, read-only" if path.startswith("/debug/") else "other")
        answer = reply() if code == 200 and len(response) <= _ACTIVITY_SHORT_REPLY else None
        if isinstance(answer, dict) and answer.get("open") is False:
            _ACT["no_font"][label] = _ACT["no_font"].get(label, 0) + 1
            return
        _ACT["reads"][label] = _ACT["reads"].get(label, 0) + 1
        if code != 200:
            _ACT["read_errors"] += 1
        elif label == "kerning":
            answer = reply() if answer is None else answer
            count = answer.get("count") if isinstance(answer, dict) else None
            if isinstance(count, int) and not isinstance(count, bool):
                _ACT["kern_pairs"] += count
    except Exception:
        pass


def _activity_tick():
    """Called on every poll: print the summaries once no request came for _ACTIVITY_IDLE_S seconds. Never raises."""
    try:
        if _ACT["pending"] and _clock() - _ACT["last"] >= _ACTIVITY_IDLE_S:
            _act_flush()
    except Exception:
        pass


def _handle(conn):
    global _request_client, _request_launcher
    try:
        conn.settimeout(1.0)
        data = b""
        while b"\r\n\r\n" not in data and len(data) < 65536:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk

        if b"\r\n\r\n" not in data:
            conn.sendall(_build_response(400, {"error": "malformed request"}))
            return

        head, _, rest = data.partition(b"\r\n\r\n")
        request_line = head.split(b"\r\n", 1)[0].decode("latin-1")
        parts = request_line.split()
        method, path = (parts[0], parts[1]) if len(parts) >= 2 else ("", "")
        headers = _parse_headers(head)

        try:
            content_length = int(headers.get("content-length", "0"))
        except ValueError:
            content_length = 0

        body = rest
        while len(body) < content_length and len(body) < 1_000_000:
            chunk = conn.recv(4096)
            if not chunk:
                break
            body += chunk
        body = body[:content_length]

        _request_client = _act_client(headers.get("x-glyphbridge-client"))
        _request_launcher = _act_launcher(headers.get("x-glyphbridge-launcher"))
        response = _route(method, path, body)
        # before sending: a change is logged even if the client is gone
        _change_log_note(method, path, body, response, headers)     # v0.204; never raises
        _activity_note(method, path, body, response, headers.get("x-glyphbridge-client"), headers.get("x-glyphbridge-launcher"))
        conn.sendall(response)
        if method == "GET" and path == "/shutdown":
            stop()
    except Exception:
        pass
    finally:
        _request_client = _request_launcher = None
        _forget_request_font()
        try:
            conn.close()
        except Exception:
            pass


def _poll():
    _activity_tick()
    for _ in range(8):
        if _sock is None:  # a /shutdown handled earlier in this loop has closed the socket
            return
        try:
            conn, _addr = _sock.accept()
        except (BlockingIOError, InterruptedError):
            return
        except OSError:
            return
        _handle(conn)


def stop():
    global _sock, _timer
    if _timer is not None:
        _timer.stop()
        _timer = None
    if _sock is not None:
        try:
            _sock.close()
        except Exception:
            pass
        _sock = None
    try:
        _act_flush()  # the summaries still pending
    except Exception:
        pass
    print("[glyphbridge] Listener stopped.")


def start():
    global _sock, _timer, _connection_announced

    if _sock is not None:
        print(f"[glyphbridge] Listener already running on http://{HOST}:{PORT}")
        return

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(8)
        s.setblocking(False)
    except OSError as exc:
        print(f"[glyphbridge] Could not bind {HOST}:{PORT} -> {exc}")
        print("[glyphbridge] If an old listener is still running, close and reopen FontLab.")
        return

    _connection_announced = False  # a fresh listener session gets its own first-connect announcement
    _announced_clients.clear()     # and its own "New client" lines
    _sock = s
    _timer = QtCore.QTimer()
    _timer.setInterval(POLL_MS)
    _timer.connect("timeout()", _poll)
    _timer.start()

    print(f"[glyphbridge] glyphbridge_fontlab_mcp_listener.py v{VERSION}")
    print(f"[glyphbridge] Listener started on http://{HOST}:{PORT} (main-thread polling)")
    print("[glyphbridge] Try: GET /health, GET /version. All routes are listed at the top of glyphbridge_fontlab_mcp_listener.py.")


start()
