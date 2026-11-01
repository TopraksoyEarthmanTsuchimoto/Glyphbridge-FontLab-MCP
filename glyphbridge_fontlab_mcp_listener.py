"""
Glyphbridge-FontLab-MCP  -  FontLab-side listener (v0.96)
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
by the listener waits for a click, no other request is served.

No route ever saves, closes, exports or generates a font. Every write is verified by re-reading
before success is reported.

Routes (GET unless marked POST):

  Status and font
    /health                     {"status": "ok"}
    /version                    {"version": VERSION}
    /font/current               live info about the current font
    /font/glyphs                glyph names of the current font
    /font/nonempty              which glyphs hold outline data; layerless glyphs (an empty .notdef) are
                                listed as unreadable here, while /font/notdef and /glyph/outline call
                                them empty (a known inconsistency)
    /font/notdef                read-only .notdef check: missing / empty / has_outline / unknown
    POST /font/notdef/warn      re-checks, then shows ONE information dialog per font and listener run,
                                only when .notdef is missing or empty; {"force": true} shows it again
    /shutdown, POST /shutdown   stops the listener; FontLab keeps running

  Reading glyphs
    /glyph/outline?name=X[&layer=body|active|strict|glayer][&modern=no]
                                THE main read: contours (kind, smooth, x, y), fontlab_bbox, margins,
                                component_count, shape_count, layer_name, elements (true element
                                transforms through the cached modern wrapper), modern_check, and
                                modern_outline when the legacy view disagrees with the modern layer
    /glyph/width?name=X         advance width
    /glyph/sidebearings?name=X  modern lsb, rsb, advance and ink width
    /glyph/unicode?name=X       raw primary codepoint (no standard checks here: the server does that)
    /glyph/nodes?name=X[&attrs=a,b][&calls=c,d]
                                older bulk node read, superseded by /glyph/outline

  Writing glyphs
    POST /glyph/create          {"name", "scan_unicode"?}: one empty glyph; reports unicode and
                                unicode_status, duplicate_check, and created_under_other_names when
                                FontLab altered the name
    POST /glyph/delete          {"name"}: deletes one glyph after a Yes/No dialog in FontLab (default No)
    POST /glyph/width           {"name", "width"}: advance width through the modern API
    POST /glyph/sidebearings    {"name", "left", "right"}: moves the outline so LSB = left, RSB = right
    POST /glyph/unicode         {"name", "unicode"}: sets the primary codepoint (0 removes it);
                                reports duplicate_check
    POST /glyph/polygon         {"name", "points" | "contours"}: closed straight contours as ONE shape
                                into an empty glyph; whole units (coordinates_rounded)
    POST /glyph/path            {"name", "contours"}: closed contours with cubic curves (c1 / c2,
                                smooth) into an empty glyph; whole units; verified node by node

  Kerning (pure reads; never the whole table)
    /kerning/pairs?pairs=A:V,T:o  or  ?text=AVATAR
                                FontLab's effective kerning per pair, class kerning included
    POST /kerning/pairs         {"pairs": [[left, right], ...]} or {"text": "..."}: the same for large
                                reads (body read up to 1,000,000 bytes)

  Debug probes that only read (development only; not used by the MCP server)
    /debug/font, /debug/glyph?name=X       everything the font / one glyph object exposes
    /debug/layerstats?name=X               layer counts (needs the glyph.layer warm-up)
    /debug/findnode?name=X&index=N&stage=fetch|dir|read
    /debug/objdir?name=X&target=...&stage=dir|read
    /debug/walk?path=...                   restricted modern-API walker (_WALK_CALL_OK whitelist)
    /debug/layerbbox?name=X&stage=...      staged probe of layer.boundingBox()
    /debug/readmodern?name=X&stage=layer|contour|node
    /debug/classdir?name=CLASS[&members=a,b]   names and docstrings of one class; nothing is called
    /debug/fldir?contains=a,b              names in the fontlab module
    /debug/fontdir?stage=dir|sub|member    names-only probe of the font object (kerning research)
    /debug/currentshapes                   modern shapes of the glyph open in the editor

  Gated debug probes (their changing stages refuse without go=yes; see the comment above each function)
    /debug/buildglyph     constructs a modern flGlyph wrapper and reads it
    /debug/trylayer       modern layer state; one layer-creation call on an empty glyph
    /debug/trymetrics     width and sidebearing experiments (glyph names starting with "tri")
    /debug/tryshape       shape-building experiments (pen, modern and curve variants); superseded
                          by /glyph/polygon and /glyph/path
    /debug/tryfont        a new font through flPackage(), once per listener run
    /debug/trysync        flPackage.update() / flWorkspace.update() (both change nothing)
    /debug/trycreate      createGlyph with and without font.update()
    /debug/trymodern      sync candidates and modern glyph creation
    /debug/trykern        one font.kerning.get((a, b)) call, 20 per listener run
    /debug/trygroups      one font.groups.getCompiled() call, 10 per listener run
    /debug/setcurrent     changes which glyph FontLab displays (no use for the modern API)

  Dead ends, kept as history: /debug/contours and /debug/drawpen (the pen protocol returns
  nothing), /debug/box, /debug/shapecount. /debug/layeritem is DISABLED: layer[N] subscript access
  crashed FontLab; the route only answers an error and must never be revived.
"""

import datetime
import json
import socket
from urllib.parse import urlsplit, parse_qs

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
VERSION = "0.96"

_REASONS = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}

_sock = None
_timer = None
_connection_announced = False


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


def get_current_font_info():
    """Real info about the font open in FontLab (fgFont -> font.info)."""
    font = fl.CurrentFont()
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

    return result


def get_glyph_names():
    font = fl.CurrentFont()
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
    """Remember that `name` holds a change made through the modern API. Never raises."""
    try:
        st = _guard_state(font)
        if name in st["glyphs"]:
            st["glyphs"][name]["how"] = how
        elif len(st["glyphs"]) >= _UNSYNCED_MAX:
            st["overflow"] = True
        else:
            st["glyphs"][name] = {"how": how}
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


def _guard_mark(font, name, how, result):
    """Register and say so in the reply; v0.89: then ask FontLab to sync the glyph (_AUTO_SYNC). Never raises."""
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


def _guard_classify(font, name):
    """'gone' | 'lost' | 'synced' | 'at_risk' | 'unknown' for one remembered glyph. Read only. Never raises."""
    try:
        glyph = _find_glyph(font, name)
        if glyph is None:
            return "gone"
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
    font = fl.CurrentFont()
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
    return result


def _confirm_deletion(name):
    """Blocking Yes/No dialog in FontLab. Runs on the main thread (this
    whole listener does), so it is safe to block here: FontLab's UI is
    simply waiting on the user, same as any other modal dialog."""
    box = QMessageBox(
        QMessageBox.Warning,
        "Glyphbridge: Confirm Deletion",
        f"Claude (via Glyphbridge) is requesting to delete the glyph "
        f"'{name}' from the current font.\n\nAllow this deletion?",
        QMessageBox.Yes | QMessageBox.No,
    )
    box.setDefaultButton(QMessageBox.No)  # Enter/closing the dialog = decline
    return box.exec_() == QMessageBox.Yes


def delete_glyph(name):
    """Delete one glyph, but only after a human confirms it in FontLab.

    Nothing is deleted unless (a) the glyph exists, (b) a Yes/No dialog
    was shown in FontLab and answered Yes, and (c) re-reading font.glyphs
    afterward confirms it is actually gone. Any other outcome is reported
    as deleted=False with a specific reason - never a guessed success.
    """
    font = fl.CurrentFont()
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

    if not _confirm_deletion(name):
        return {
            "open": True,
            "deleted": False,
            "user_declined": True,
            "reason": "the deletion was not approved in FontLab (dialog answered No or closed)",
            "before_count": len(before),
            "after_count": len(before),
        }

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
    }
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    if not deleted and not call_error:
        result["reason"] = "removeGlyph() did not raise, but the glyph is still in font.glyphs afterward"
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
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    glyph = _find_glyph(font, name)
    if glyph is None:
        return {"open": True, "found": False, "reason": f"no glyph named {name!r}"}
    return {"open": True, "found": True, "name": name, "width": glyph.width}


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


def _package_layer_name(font):
    """(master name, None) or (None, reason). READ ONLY. The layer name of a font whose glyphs have no layer yet (a new font) is the
    name of its single master. Used only when exactly one font is open, so that flWorkspace.currentPackage must be this font; every
    check below must pass, otherwise nothing is guessed."""
    import sys as _sys
    mod = _sys.modules.get("fontlab") or fl
    count_fonts = getattr(mod, "CountFonts", None)
    if count_fonts is None:
        return None, "the fontlab module has no CountFonts, so the number of open fonts is unknown"
    try:
        count = count_fonts()
    except Exception as exc:
        return None, f"CountFonts() failed ({type(exc).__name__}: {exc})"
    if type(count) is not int:
        return None, "CountFonts() did not return a whole number"
    if count != 1:
        return None, f"{count} fonts are open, so the package that belongs to this font cannot be told apart from the others yet"
    try:
        ws = mod.flWorkspace.instance()
        npk = len(ws.packages())
    except Exception as exc:
        return None, f"the workspace's packages could not be counted ({type(exc).__name__}: {exc})"
    if npk != 1:
        return None, f"the workspace holds {npk} packages, not exactly 1"
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


def _derive_layer_name(font, skip_name, with_source=False):
    """(layer name, None) or (None, reason); with_source=True gives (name, None, source) or (None, reason, None). The name comes from the
    OTHER glyphs of the font that already have a modern layer (source 'other glyphs'). Only when none has one (a new font) the
    name of the font's single master is used (source 'package master'), after every check of _package_layer_name. A disagreement
    between glyphs, or an unreadable glyph list, is never overridden."""
    name, why = _derive_layer_name_from_glyphs(font, skip_name)
    source = "other glyphs" if name is not None else None
    if name is None and isinstance(why, str) and why.startswith(_LAYER_NO_OTHER_GLYPH):
        pname, pwhy = _package_layer_name(font)
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
    lname, why, lsource = _derive_layer_name(font, name, True)
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
    font = fl.CurrentFont()
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
    if success:
        _guard_mark(ctx["font"], name, "width", result)
    if call_error:
        result["call_error"] = call_error
    if not success and not call_error:
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
              "after": after, "requested": new_width}
    result.update(guard_report)
    if call_error:
        result["call_error"] = call_error
    if not success and not call_error:
        result["reason"] = "width did not change to the requested value after setting"
    return result


def set_glyph_width(name, new_width):
    """Set one glyph's advance width, verified by re-reading it afterward. With a modern layer the MODERN property
    flGlyph.advanceWidth is used (the outline is not touched); a glyph without one is written the legacy way only when it is
    positively empty, otherwise the request is refused (live finding: the legacy write lost work on glyphs with shapes)."""
    ctx, refusal = _modern_edit_target(name, create_layer=True)
    if ctx is not None:
        out = _set_width_modern(ctx, name, new_width)
        if ctx.get("layer_created"):
            out["layer_created"] = ctx["layer_created"]
            out["layer_name_source"] = ctx.get("layer_name_source")
        return out
    if "glyph" not in refusal:            # no font, or no such glyph
        out = _public_refusal(refusal)
        if out.get("found") is False:
            out.update({"before": None, "after": None})
        return out
    font, glyph = refusal["font"], refusal["glyph"]
    if _tryshape_known_empty(_tryshape_state(glyph)) and not refusal.get("existing_layer"):
        out = _set_width_legacy(font, glyph, name, new_width)
        if refusal.get("create_layer_error"):
            out["layer_create_note"] = refusal["create_layer_error"]
        return out
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
        _guard_mark(ctx["font"], name, "sidebearings", result)
    if not result["set"]:
        mismatch = ", ".join(k for k, v in checks.items() if not v)
        result["reason"] = ("FontLab raised an error in setSB; the re-read margins differ from the request: " if call_error
                            else "the re-read margins do not match the request: ") + mismatch
    return result


_POLY_MIN_POINTS, _POLY_MAX_POINTS = 3, 500
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
        _guard_mark(ctx["font"], name, "draw_polygon", result)
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


def _path_smooth_problems(nodes, label):
    """For every smooth on-curve node: the previous and the next node (a handle, or the neighbouring on-curve point) must lie on
    opposite sides of a straight line through it, within _PATH_SMOOTH_TOLERANCE_DEG; a neighbour on top of the node cannot define a
    direction. Returns a list of sentences (empty = fine). `nodes` are dicts with x, y, on, smooth (a closed contour)."""
    import math as _math
    problems = []
    n = len(nodes)
    limit = _math.sin(_math.radians(_PATH_SMOOTH_TOLERANCE_DEG))
    for k, nd in enumerate(nodes):
        if not (nd.get("on") and nd.get("smooth")):
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


def _path_check_request(contours):
    """Pure checks on rounded contours; returns a list of sentences (empty = the request can be built)."""
    problems = []
    for ci, pts in enumerate(contours):
        if len({(p["x"], p["y"]) for p in pts}) < 3:
            problems.append(f"contour {ci}: at least 3 different on-curve positions are needed (after rounding to whole units)")
        nodes, _idx = _path_layout(pts)
        problems.extend(_path_smooth_problems(nodes, f"contour {ci}"))
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


def _path_build_contour(mod, qp, pts, expected, on_index):
    """Build ONE detached contour for the points `pts` and return it (the caller reads it back and judges it). Raises with the failing
    step in the message."""
    m = len(pts)
    step = "flContour(points)"
    try:
        contour = mod.flContour([qp(p["x"], p["y"]) for p in pts])
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


def draw_path(name, contours, rounded=None):
    """Draw closed contours with straight AND cubic segments as ONE shape into a glyph whose modern layer is empty. `contours`: lists of point
    dicts {x, y, c1, c2, smooth} with whole-number coordinates (rule B was applied by the caller; c1 / c2 are (x, y) or None). Everything is
    built and read back DETACHED first (node by node, and smooth collinearity); only layer.addShape touches the glyph, and the modern layer
    is read back afterwards and compared node by node. Never saves."""
    base = {"open": True, "name": name, "drawn": False, "route": "modern"}
    problems = _path_check_request(contours)
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
            contour = _path_build_contour(mod, qp, pts, expected, on_index)
        except Exception as exc:
            return dict(base, reason=f"contour {ci} could not be built detached ({exc}): nothing was attached")
        rows, err = _path_read_nodes(contour)
        if rows is None:
            return dict(base, reason=f"the detached contour {ci} could not be read back ({err}): nothing was attached")
        closed, _e = _tl_call(lambda: contour.closed)
        bad = _path_mismatches(rows, expected, f"detached contour {ci}")
        if closed is not True:
            bad.append(f"detached contour {ci}: closed reads {closed!r}")
        bad.extend(_path_smooth_problems([{"x": r["x"], "y": r["y"], "on": e["on"], "smooth": e["smooth"]} for r, e in zip(rows, expected)],
                                         f"detached contour {ci}") if len(rows) == len(expected) else [])
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
                if entry.get("closed") is not True:
                    mismatches.append(f"layer contour {ci}: closed reads {entry.get('closed')!r}")
                mismatches.extend(_path_mismatches(entry.get("nodes") or [], layouts[ci][0], f"layer contour {ci}"))
        nodes_match = not mismatches
    else:
        result["read_back_error"] = modern.get("error")
    result["checks"] = {"shapes_ok": after.get("shapes") == 1, "nodes_ok": after.get("nodes") == n, "nodes_match": nodes_match}
    result["nodes_match"] = nodes_match
    result["drawn"] = bool(result["checks"]["shapes_ok"] and result["checks"]["nodes_ok"] and nodes_match is True)
    if after.get("shapes") != 0 or after.get("nodes") != 0:
        _guard_mark(ctx["font"], name, "draw_path", result)
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


def get_glyph_unicode(name):
    font = fl.CurrentFont()
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


def get_kerning_pairs(pairs=None, text=None):
    """v0.94 - READ-ONLY kerning lookup. The ONLY call made on the kerning object is font.kerning.get((left, right)) once per pair:
    FontLab's own value for that pair of glyph names, class (group) kerning included (probes 150 and 154b). A None answer means FontLab
    has no kerning entry for the pair: value 0, kerned false. Two input forms, exactly one of them:
      pairs  'A:V,T:o'  1 or more pairs of glyph names, no upper limit from v0.95; the POST route sends a list of [left, right] lists (A-Z a-z 0-9 . _ -; ':' and ',' cannot occur in such names)
      text   2 or more characters; each character is mapped to the ONE glyph whose primary Unicode it is; the pairs are the neighbours.
    A name that is not a glyph, a character that maps to no glyph or to several, a failed get() and a non-numeric answer become an
    'error' entry for that pair: never a zero. len(font.kerning) is read before and after the batch (side_effect_detected)."""
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
    try:
        kerning = font.kerning
        getter = kerning.get
    except Exception as exc:
        return {"open": True, "error": f"font.kerning / kerning.get not reachable: {type(exc).__name__}: {exc}"}
    if not callable(getter):
        return {"open": True, "error": "kerning.get is not callable"}
    try:
        glyphs = list(font.glyphs)
        known = set(str(g.name) for g in glyphs)
    except Exception as exc:
        return {"open": True, "error": f"the glyph list could not be read: {type(exc).__name__}: {exc}"}
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
            missing = [nm for nm in (entry["left"], entry["right"]) if nm not in known]
            if missing:
                entry["error"] = "no glyph named " + ", ".join(repr(m) for m in missing)

    def _len():
        try:
            n = len(kerning)
            return n if isinstance(n, int) and not isinstance(n, bool) else None
        except Exception:
            return None

    len_before = _len()
    for entry in wanted:
        if "error" in entry:
            continue
        try:
            value = getter((entry["left"], entry["right"]))
        except Exception as exc:
            entry["error"] = f"kerning.get raised {type(exc).__name__}: {exc}"
            continue
        if value is None:
            entry["value"] = 0
            entry["kerned"] = False
        elif isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and value not in (float("inf"), float("-inf")):
            entry["value"] = value
            entry["kerned"] = value != 0
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            entry["error"] = "kerning.get returned a number that is not finite"
        else:
            entry["error"] = f"kerning.get returned an unexpected {type(value).__name__}"
    len_after = _len()
    upm = None
    try:
        raw_upm = font.info.unitsPerEm
        if isinstance(raw_upm, (int, float)) and not isinstance(raw_upm, bool):
            upm = raw_upm
    except Exception:
        upm = None
    return {"open": True, "mode": "text" if have_text else "pairs", "units_per_em": upm, "count": len(wanted),
            "errors": sum(1 for e in wanted if "error" in e), "table_size": len_before,
            "side_effect_detected": (len_before != len_after) if (len_before is not None and len_after is not None) else None,
            "results": wanted}


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


def set_glyph_unicode(name, new_codepoint):
    """Set one glyph's Unicode codepoint, verified by re-reading it
    afterward - same discipline as set_glyph_width."""
    font = fl.CurrentFont()
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
    for label, attr in (("shapes", "shapesCount"), ("nodes", "nodesCount"), ("components", "componentsCount")):
        try:
            v = _call0(layer, attr)
            st[label] = int(v) if (isinstance(v, (int, float)) and not isinstance(v, bool)) else f"not a plain number: {type(v).__name__}"
        except Exception as exc:
            st[label + "_error"] = f"{type(exc).__name__}: {exc}"
    return st, layer


def _tryshape_modern_known_empty(st):
    return (st.get("active_layer") == "present" and st.get("shapes") == 0 and st.get("nodes") == 0
            and st.get("components") == 0)


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


def debug_read_modern(name, stage, index, node_index, via):
    """READ-ONLY. How can the outline be read back from the modern active layer? No native object is indexed or iterated: only
    getContours() results that are real Python lists / tuples are indexed."""
    if stage not in ("layer", "contour", "node"):
        return {"error": 'stage must be "layer", "contour" or "node"'}
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
    font = fl.CurrentFont()
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


# --- .notdef check and warning dialog (v0.46) ---------------------------------
# Basis (real FontLab 8.4 session, read-only probes): the empty .notdef of the test font has len(glyph.layers) == 0 and
# bodyLayer/activeLayer None on every attempt; Arial's drawn .notdef has 1 layer, 2 contours, 8 nodes and reads normally.
# So "no layers" counts as "no outline data". A glyph whose layer cannot be reached although layers exist is 'unknown',
# NEVER 'empty': the dialog appears only on POSITIVE evidence (missing or empty), never because a read failed.
_NOTDEF_WARNED = {}      # font path -> status the user was already warned about during this listener run
_NOTDEF_TITLE = "Glyphbridge: .notdef glyph"
_NOTDEF_EXPLAIN = (
    "The .notdef is the glyph that shows when your font doesn't contain a character that is being typed. "
    "It is usually drawn as a rectangle, often with a question mark or an X inside, as the OpenType "
    "specification recommends.\n\n(Shown once per font per session by Glyphbridge, because an AI agent read this font.)")
_NOTDEF_DIALOG_TEXT = {
    "empty": "It looks like you haven't created a proper .notdef glyph yet. " + _NOTDEF_EXPLAIN,
    "missing": "Your font has no glyph named .notdef. Every font needs one (it must be glyph 0). " + _NOTDEF_EXPLAIN,
}


def check_notdef():
    """Read-only. Does the current font have a .notdef glyph, and does it hold any outline data?
    status: "missing"     no glyph named .notdef
            "empty"       exists, and FontLab holds no outline data for it (0 layers, or 1 layer with 0 nodes/shapes
                          and no components)
            "has_outline" exists and has nodes, shapes or components
            "unknown"     could not be determined (unreadable layer, several layers, a count failed): NO verdict.
    Never shows a dialog and never changes anything."""
    font = fl.CurrentFont()
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
    return result


def _show_notdef_dialog(status):
    """Blocking information dialog in FontLab (same pattern as _confirm_deletion): runs on the main thread, so the
    listener answers nothing else until the person clicks OK."""
    box = QMessageBox(QMessageBox.Information, _NOTDEF_TITLE, _NOTDEF_DIALOG_TEXT[status], QMessageBox.Ok)
    box.exec_()


def warn_notdef(force=False):
    """Re-check .notdef HERE (a dialog is never shown on the caller's say-so), then show the dialog if, and only if,
    .notdef is missing or empty and this font has not been warned about that status yet (unless force)."""
    font = fl.CurrentFont()
    if font is None:
        return {"open": False}
    check = check_notdef()
    status = check.get("status")
    out = {"open": True, "status": status, "evidence": check.get("evidence", []),
           "dialog_shown": False, "already_warned": False}
    if status not in ("missing", "empty"):
        out["reason"] = ("no warning needed: .notdef has an outline" if status == "has_outline"
                         else "could not be determined, so no warning was shown")
        return out
    key = str(font.path or "")
    if not force and _NOTDEF_WARNED.get(key) == status:
        out["already_warned"] = True
        return out
    try:
        _show_notdef_dialog(status)
    except Exception as exc:
        out["dialog_error"] = f"{type(exc).__name__}: {exc}"
        return out
    _NOTDEF_WARNED[key] = status
    out["dialog_shown"] = True
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


def get_glyph_outline(name, route="body", modern=True):
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
    font = fl.CurrentFont()
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


def debug_class_probe(name, doc_chars=600, members=None):
    """Names + docstrings of ONE entry of the fontlab module, e.g. flShape,
    flTransform, flGlyph, flLayer. Only dir() and __doc__ are read: nothing is
    constructed, called or changed. The entry must exist in dir(module), so no
    arbitrary attribute path can be requested."""
    import re as _re
    import sys as _sys
    if not name or not _re.match(r"^[A-Za-z][A-Za-z0-9_<>]*$", name):
        return {"error": "name must look like a plain identifier, e.g. flShape"}
    mod = _sys.modules.get("fontlab") or fl
    if name not in dir(mod):
        return {"error": f"{name!r} is not a name in the fontlab module"}
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
# "A font is open" uses CountFonts() when it is a plain int (0 = the placeholder fgFont of section 8k, reported as open false).
# --------------------------------------------------------------------------

_FONTDIR_STAGES = ("dir", "sub", "member")


def debug_font_dir(stage="dir", attr=None, members=None):
    import re as _re
    if stage not in _FONTDIR_STAGES:
        return {"error": 'stage must be "dir", "sub" or "member"'}
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


# --------------------------------------------------------------------------
# /debug/tryfont (v0.83) - EXPERIMENT: make a NEW, EMPTY font through the modern API
# (the equivalent of File > New Font / Ctrl+N). Three stages, one variable each:
#   state     read-only
#   construct go=yes   ONE detached flPackage(); never attached here
#   attach    go=yes   ONE flWorkspace.instance().addPackage(<that package>)
# Not called, ever, by this probe: createNewProject, closePackage, closeProject, saveProject, export*, release, remove.
# --------------------------------------------------------------------------

_TRYFONT_STAGES = ("state", "construct", "attach")
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
    """Read-only look at the legacy and the modern view of 'which fonts are open'."""
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
        out["packages_len"] = len(ws.packages())
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
                                     "name": _tryfont_read(cp, "name")}
    except Exception as exc:
        out["currentPackage"] = f"<error: {type(exc).__name__}: {exc}>"
    if pkg is not None:
        try:
            out["hasPackage"] = _tryfont_plain(ws.hasPackage(pkg))
        except Exception as exc:
            out["hasPackage"] = f"<error: {type(exc).__name__}: {exc}>"
    return out


def debug_try_font(stage, go):
    import sys as _sys
    if stage not in _TRYFONT_STAGES:
        return {"error": 'stage must be "state", "construct" or "attach"'}
    mod = _sys.modules.get("fontlab") or fl
    flags = {"constructed": _TRYFONT["constructed"], "attached": _TRYFONT["attached"]}
    if stage == "state":
        return dict(flags, stage="state", workspace_state=_tryfont_workspace_state(mod, _TRYFONT["package"]))
    if go != "yes":
        what = ("constructs ONE native flPackage object (it is not attached to anything)" if stage == "construct"
                else "attaches the constructed package to the workspace (the experiment that may open a new font)")
        return {"error": f"stage={stage} {what}. Add &go=yes to run it."}
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
# HTTP plumbing (stdlib only; no background thread - see module docstring)
# --------------------------------------------------------------------------

def _build_response(status, payload):
    body = json.dumps(payload).encode("utf-8")
    head = (
        f"HTTP/1.1 {status} {_REASONS.get(status, 'Error')}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: close\r\n\r\n"
    )
    return head.encode("ascii") + body


def _route(method, full_path, body=b""):
    split = urlsplit(full_path)
    path = split.path
    query = parse_qs(split.query)

    if method == "GET":
        if path == "/health":
            global _connection_announced
            if not _connection_announced:
                _connection_announced = True
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[glyphbridge] Connected at {ts} - an AI agent (Claude) has checked in "
                      f"and is talking to this FontLab session.")
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
                return _build_response(400, {"error": "provide ?name=<glyph>&stage=layer|contour|node[&index=K&node=I&via=getNodeAt|at]"})
            def _qr(key, default=""):
                return (query.get(key) or [default])[0]
            try:
                idx, nidx = int(_qr("index", "0")), int(_qr("node", "0"))
            except ValueError:
                return _build_response(400, {"error": '"index" and "node" must be integers'})
            if not (0 <= idx <= 9999 and 0 <= nidx <= 9999):
                return _build_response(400, {"error": '"index" and "node" must be between 0 and 9999'})
            try:
                return _build_response(200, debug_read_modern(names[0].strip(), _qr("stage", "layer"), idx, nidx, _qr("via")))
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

        if path == "/debug/fontdir":
            stage = (query.get("stage") or ["dir"])[0]
            attr = (query.get("attr") or [None])[0]
            members = (query.get("members") or [None])[0]
            try:
                return _build_response(200, debug_font_dir(stage, attr.strip() if attr else None, members))
            except Exception as exc:
                return _build_response(500, {"error": str(exc)})

        if path == "/debug/tryfont":
            try:
                return _build_response(200, debug_try_font((query.get("stage") or ["state"])[0], (query.get("go") or [""])[0]))
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

        if path == "/debug/trykern":
            try:
                return _build_response(200, debug_try_kern((query.get("a") or [""])[0], (query.get("b") or [""])[0], (query.get("go") or [""])[0]))
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
            try:
                return _build_response(200, delete_glyph(name.strip()))
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

            parsed = []
            for ci, plist in enumerate(many):
                if not isinstance(plist, list) or not (_POLY_MIN_POINTS <= len(plist) <= _POLY_MAX_POINTS):
                    return _build_response(400, {"error": f"contour {ci} must be a list of {_POLY_MIN_POINTS} to {_POLY_MAX_POINTS} points"})
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
                return _build_response(200, draw_path(name.strip(), rounded_contours, rounded_report))
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


def _handle(conn):
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

        conn.sendall(_route(method, path, body))
        if method == "GET" and path == "/shutdown":
            stop()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _poll():
    for _ in range(8):
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
    _sock = s
    _timer = QtCore.QTimer()
    _timer.setInterval(POLL_MS)
    _timer.connect("timeout()", _poll)
    _timer.start()

    print(f"[glyphbridge] glyphbridge_fontlab_mcp_listener.py v{VERSION}")
    print(f"[glyphbridge] Listener started on http://{HOST}:{PORT} (main-thread polling)")
    print("[glyphbridge] Try: GET /health, GET /font/current, POST /glyph/create, POST /glyph/delete, POST /glyph/width, POST /glyph/sidebearings, POST /glyph/unicode")


start()
