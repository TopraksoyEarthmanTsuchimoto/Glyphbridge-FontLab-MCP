"""
Glyphbridge-FontLab-MCP  -  MCP server (v0.39)
===============================================
Version history: mental-model/CHANGELOG.md in the repository.

Runs in your normal venv (MCP SDK v2). Claude Desktop launches it over
stdio. It does NOT talk to FontLab directly: it asks the Glyphbridge
listener (glyphbridge_fontlab_mcp_listener.py, running inside FontLab) over
http://127.0.0.1:8765 and relays what comes back.

Design rule: a tool only returns data if the listener actually answered
with valid data. Anything else - FontLab closed, listener not started,
timeout, bad response, no font open - raises a ToolError with a plain
explanation. There is no code path that reports success without data.

Never print() to stdout in this file: on stdio, stdout IS the protocol.
Logging goes to stderr.

Self-check without Claude (listener must be running in FontLab):
    python glyphbridge_mcp_server.py --check
    python glyphbridge_mcp_server.py --check --outline A      (also dumps one glyph's analysed outline)
    python glyphbridge_mcp_server.py --check --notdef-warn    (also runs check_notdef: MAY SHOW the warning dialog in FontLab)
    python glyphbridge_mcp_server.py --check --with-write-test (creates, widens and deletes TEST glyphs: FontLab asks you to
                                                              confirm the deletions)
"""

import json
import logging
import math
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import quote, unquote
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

LISTENER_HOST = "127.0.0.1"
LISTENER_PORT = int(os.environ.get("GLYPHBRIDGE_PORT", "8765"))
TIMEOUT_SECONDS = 5.0
SERVER_VERSION = "0.39"          # keep identical to the header line "MCP server (vX.YY)" (a test compares them)
MIN_LISTENER_VERSION = (0, 82)     # oldest listener this server's features fully work with
SAVE_REMINDER = "**You must save if you want to keep these changes: use the File menu or press Ctrl+S in FontLab.**"   # shown in CHAT only, never as a FontLab dialog
DELETE_CONFIRM_TIMEOUT_SECONDS = 120.0  # time to let a human see and answer the FontLab dialog
NOTDEF_DIALOG_TIMEOUT_SECONDS = 120.0   # the .notdef warning dialog also waits for a person to click OK
BASE_URL = f"http://{LISTENER_HOST}:{LISTENER_PORT}"

logging.basicConfig(level=logging.INFO)  # default handler writes to stderr
log = logging.getLogger("glyphbridge")

# Bypass any system/browser proxy: this traffic never leaves the machine.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

# ---- client name (v0.34): the connected app's own name (clientInfo title, else name), sent to the listener in the
# X-Glyphbridge-Client header so FontLab's OUTPUT panel can say which app made each request. It is the app's claim, not
# checked, and names the app, not the model. One stdio client per server process; --check sends its own label. ----
_CLIENT = {"name": None}
CLIENT_NAME_MAX = 40


def _clean_client_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = "".join(ch for ch in value if not (ord(ch) < 32 or 127 <= ord(ch) <= 159))
    return " ".join(text.split())[:CLIENT_NAME_MAX] or None


def _note_client(ctx: Any) -> None:
    """Remember the client's name from the MCP session of a tool call. Never raises: a missing name only means none is sent."""
    if ctx is None:
        return
    try:
        info = ctx.session.client_params.client_info
        name = _clean_client_name(getattr(info, "title", None)) or _clean_client_name(getattr(info, "name", None))
    except Exception:
        return
    if name:
        _CLIENT["name"] = name


def _client_headers() -> dict:
    headers = {"X-Glyphbridge-Client": quote(_CLIENT["name"], safe="")} if _CLIENT["name"] else {}
    if _LAUNCHER["value"]:
        headers["X-Glyphbridge-Launcher"] = quote(_LAUNCHER["value"], safe="")
    return headers


# ---- launcher names (v0.35): the FILE NAME of the program that started this server process (two levels in v0.35,
# one since v0.36), read ONCE when the server starts and sent unchanged in the X-Glyphbridge-Launcher header
# ("claude.exe"; the listener shows it as "CLAUDE"). Privacy: file names only, never a path, an argument, an environment variable or a user
# name, and nothing leaves 127.0.0.1. Windows: one Toolhelp process snapshot plus each process's start time; macOS:
# libproc's proc_pidinfo (written and stub-tested, never run on a Mac); other systems: nothing. A parent that started
# after its child is a reused process id and ends the walk. Any failure sends no header: no guess. A file name is only
# a name: it does not prove what the program is, and it says nothing about the model. ----
_LAUNCHER = {"value": None}
LAUNCHER_LEVELS = 1  # v0.36: the second level only said how the app itself was opened (Explorer, launchd, a terminal)


def _clean_launcher_name(value: Any) -> str | None:
    """The file name part of a process name (any path dropped), cleaned like a client name, or None."""
    if not isinstance(value, str):
        return None
    return _clean_client_name(re.split(r"[\\/]", value)[-1])


def _walk_launchers(info: Any, pid: int, skip_own_launcher: bool) -> list[str]:
    """Up to LAUNCHER_LEVELS file names above process pid. info(pid) gives (name, parent pid, start) or None.
    skip_own_launcher: Windows runs a venv's Scripts\\python.exe as a launcher that starts the real interpreter, so
    one parent with this process's own file name is passed over, once."""
    me = info(pid)
    if not me or me[2] is None:
        return []
    names, child, skipped = [], me, False
    while len(names) < LAUNCHER_LEVELS:
        parent = info(child[1]) if child[1] else None
        if not parent or parent[2] is None or parent[2] > child[2]:
            break
        if skip_own_launcher and not skipped and not names and str(parent[0]).lower() == str(me[0]).lower():
            skipped = True
        else:
            name = _clean_launcher_name(parent[0])
            if not name:
                break
            names.append(name)
        child = parent
    return names


def _windows_process_info() -> Any:
    """info(pid) for _walk_launchers from one Toolhelp snapshot; the start time comes from GetProcessTimes."""
    import ctypes
    from ctypes import wintypes

    class _Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.Process32FirstW.argtypes = k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_Entry)]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = k32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if not snapshot or snapshot == ctypes.c_void_p(-1).value:
        raise OSError("no process snapshot")
    table = {}
    try:
        entry = _Entry()
        entry.dwSize = ctypes.sizeof(_Entry)
        ok = k32.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            table[entry.th32ProcessID] = (entry.szExeFile, entry.th32ParentProcessID)
            ok = k32.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        k32.CloseHandle(snapshot)

    def start_time(pid: int) -> int | None:
        handle = k32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return None
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not k32.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                return None
            return (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        finally:
            k32.CloseHandle(handle)

    def info(pid: int) -> Any:
        if pid not in table:
            return None
        name, parent = table[pid]
        return name, parent, start_time(pid)

    return info


def _mac_process_info(pid: int) -> Any:
    """info(pid) for _walk_launchers through libproc (PROC_PIDTBSDINFO). The structure also holds user and group ids:
    they are never read out of it."""
    import ctypes

    class _BsdInfo(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint32) for n in ("flags", "status", "xstatus", "pid", "ppid", "uid", "gid", "ruid",
                                                    "rgid", "svuid", "svgid", "rfu_1")] + \
                   [("comm", ctypes.c_char * 16), ("name", ctypes.c_char * 32)] + \
                   [(n, ctypes.c_uint32) for n in ("nfiles", "pgid", "pjobc", "tdev", "tpgid")] + \
                   [("nice", ctypes.c_int32), ("start_sec", ctypes.c_uint64), ("start_usec", ctypes.c_uint64)]

    lib = ctypes.CDLL("/usr/lib/libproc.dylib")
    data = _BsdInfo()
    if lib.proc_pidinfo(ctypes.c_int(pid), ctypes.c_int(3), ctypes.c_uint64(0), ctypes.byref(data),
                        ctypes.c_int(ctypes.sizeof(data))) != ctypes.sizeof(data):
        return None
    name = (data.name or data.comm).decode("utf-8", "replace")
    return name, data.ppid, (data.start_sec, data.start_usec)


def _read_launcher() -> str | None:
    """The launcher text for the header, or None. Never raises."""
    try:
        if os.name == "nt":
            info = _windows_process_info()
            names = _walk_launchers(info, os.getpid(), sys.prefix != sys.base_prefix)
        elif sys.platform == "darwin":
            names = _walk_launchers(_mac_process_info, os.getpid(), False)
        else:
            return None
    except Exception:
        return None
    return " < ".join(names) or None

NOT_REACHABLE = (
    f"Cannot reach the Glyphbridge listener at {BASE_URL}. Make sure FontLab 8 "
    "is running and that glyphbridge_fontlab_mcp_listener.py has been started from FontLab's "
    "Scripting panel (it must be started manually each FontLab session)."
)
NO_FONT = (
    "FontLab is running and the listener answered, but no font is open. "
    "Open a font in FontLab and try again."
)


class OutcomeUnknown(ToolError):
    """The listener may or may not have carried out the request (timeout, HTTP error, unusable reply). Reads treat it like any
    ToolError; writes use it to count an UNCERTAIN change for the save reminder. A refused connection is NOT this: nothing was sent."""


# ---- save policy (v0.18): Glyphbridge never saves; the person does. Counters live in this server process only. ----
_CHANGES = {"package": 0, "package_unsure": 0, "session": 0, "session_unsure": 0}

_SAVE_INSTRUCTION = ("The font was changed in FontLab's memory only: no Glyphbridge tool saves anything, saving is the person's job. "
                     "Do NOT remind the person after every step. When your whole task package is finished, call finish_changes ONCE "
                     "and show the person the save_reminder it returns, in bold, exactly as written.")
_UNSURE_NOTE = ("The request may or may not have been applied, so the font may have been modified: check its state before repeating "
                "the change, and when your task package is finished call finish_changes once so the person is reminded to save.")
_CHANGED_BY_ERROR_NOTE = ("The font HAS been modified by this, so it counts as a change: when your task package is finished, call "
                          "finish_changes once so the person is reminded to save.")


def _reset_change_tracking() -> None:
    for key in _CHANGES:
        _CHANGES[key] = 0


def _note_change(sure: bool = True) -> None:
    _CHANGES["package" if sure else "package_unsure"] += 1
    _CHANGES["session" if sure else "session_unsure"] += 1


def _mark_modified(result: dict, modified: bool) -> None:
    """Add font_modified to a write reply; a real change is counted and the agent is told how to remind the person ONCE."""
    result["font_modified"] = bool(modified)
    if modified:
        _note_change()
        existing = result.get("agent_instruction")
        result["agent_instruction"] = (existing + " " + _SAVE_INSTRUCTION) if existing else _SAVE_INSTRUCTION


def _write_post(path: str, payload: dict, timeout=None) -> dict:
    """POST a write to the listener; an outcome that cannot be known is counted as an uncertain change and said so."""
    try:
        if timeout is None:
            return _call_listener_post(path, payload)
        return _call_listener_post(path, payload, timeout=timeout)
    except OutcomeUnknown as exc:
        _note_change(sure=False)
        raise OutcomeUnknown(f"{exc} {_UNSURE_NOTE}") from exc


# --------------------------------------------------------------------------
# Talking to the listener (plain Python; no MCP SDK involved)
# --------------------------------------------------------------------------

def _timeout_message(path: str, timeout: float) -> str:
    return (
        f"The FontLab listener did not answer {path} within {timeout:g}s. "
        "This happens, for example, when a Glyphbridge dialog (the .notdef notice or a delete "
        "confirmation) is waiting for an answer in FontLab: answer or close it there. "
        "It can also mean FontLab is busy or frozen. "
        "If you asked for a change, it may or may not have been applied: "
        "check the font's current state before repeating it."
    )


def _do_request(req_or_url, path: str, timeout: float = TIMEOUT_SECONDS) -> dict:
    """Shared error handling for both GET and POST calls to the listener."""
    try:
        with _opener.open(req_or_url, timeout=timeout) as resp:
            raw = resp.read()
            _note_font_headers(getattr(resp, "headers", None))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            detail = "(no body)"
        raise OutcomeUnknown(
            f"The FontLab listener returned HTTP {exc.code} for {path}: {detail}"
        ) from exc
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise OutcomeUnknown(_timeout_message(path, timeout)) from exc
        raise ToolError(NOT_REACHABLE) from exc
    except TimeoutError as exc:
        raise OutcomeUnknown(_timeout_message(path, timeout)) from exc
    except OSError as exc:
        raise ToolError(f"{NOT_REACHABLE} (network error: {exc})") from exc

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OutcomeUnknown(
            f"The listener's reply to {path} was not valid JSON, so it was not trusted."
        ) from exc

    if not isinstance(data, dict):
        raise OutcomeUnknown(f"The listener's reply to {path} had an unexpected shape.")
    return data


# ---- which font a reply came from (v0.38, listener 0.113; goal 5 of PROJECT.md) ----
# The listener names the font each request used in three headers: family/style, a short hash of its path ("none" when the path
# is empty; the path itself is never sent) and CountFonts(). Each tool reply then gains font and fonts_open, and font_note when
# several fonts are open or the font in front changed; since v0.39 a ToolError gets the font_note appended to its message (test
# 277: a failed first call after a window switch hid the switch). An older listener sends no headers: nothing is added.
_FONT_CALLS: list = []                         # (name, key, fonts_open) of each listener reply in the current tool call
_FONT_SEEN = {"name": None, "key": None, "seen": False}   # the font of the previous tool call in this server process
_FONT_KEY_RE = re.compile(r"^[0-9a-f]{12}$")
FONT_NAME_MAX = 100


def _clean_font_text(value: str) -> str:
    text = "".join(ch for ch in value if not (ord(ch) < 32 or 127 <= ord(ch) <= 159))
    return " ".join(text.split())[:FONT_NAME_MAX]


def _note_font_headers(headers: Any) -> None:
    """Record the font a listener reply names. Never raises; a reply without the headers records nothing."""
    try:
        raw = headers.get("X-Glyphbridge-Font") if headers is not None else None
        if not isinstance(raw, str):
            return
        family, sep, style = raw.partition("/")
        name = " ".join(x for x in (_clean_font_text(unquote(family)), _clean_font_text(unquote(style)) if sep else "") if x) or None
        key = headers.get("X-Glyphbridge-Font-Key")
        key = key if isinstance(key, str) and _FONT_KEY_RE.match(key) else None
        count = headers.get("X-Glyphbridge-Fonts-Open")
        count = int(count) if isinstance(count, str) and count.isdigit() and len(count) <= 4 else None
        _FONT_CALLS.append((name, key, count))
    except Exception:
        pass


def _same_font(a: tuple, b: tuple) -> bool:
    """Two (name, key) identities: the path hashes decide when both exist, otherwise the names."""
    if a[1] is not None and b[1] is not None:
        return a[1] == b[1]
    return a[0] == b[0]


def _font_fields(calls: list, result: Any) -> dict:
    """The font fields for one tool call, and the remembered font for the next call."""
    if not calls:
        return {}
    name, key, count = calls[-1]
    fields: dict = {"font": name, "fonts_open": count}
    notes = []
    shown = name or "a font without a name"
    if count is not None and count > 1:
        notes.append(f"{count} fonts are open in FontLab; this call used {shown}, the font whose window is in front. Name it when you report.")
        if key is None:
            notes.append("This font has no file path (a new, unsaved font), so a switch to another unsaved font of the same name cannot be noticed.")
    if any(not _same_font((n, k), (name, key)) for n, k, _ in calls[:-1]):
        fields["font_changed_during_call"] = True
        notes.append("The font in front changed during this call, so its parts may have used different fonts.")
        if isinstance(result, dict) and result.get("font_modified") is True:
            fields["change_target_uncertain"] = True
            notes.append("Check in FontLab which font received this change before doing anything else.")
    if _FONT_SEEN["seen"] and not _same_font((_FONT_SEEN["name"], _FONT_SEEN["key"]), (name, key)):
        fields["font_changed"] = {"from": _FONT_SEEN["name"], "to": name}
        now = shown if _FONT_SEEN["name"] != name else f"another font with the same name, {shown}, from a different file"
        notes.append(f"The font in front changed since the previous Glyphbridge call (was {_FONT_SEEN['name'] or 'a font without a name'}, now {now}): "
                     "make sure this is the font the person means before any further change.")
    _FONT_SEEN.update(name=name, key=key, seen=True)
    if notes:
        fields["font_note"] = " ".join(notes)
    return fields


def _with_font(fn: Any, *args: Any) -> Any:
    """Run one tool's work and add the font fields to its reply. A refusal (an exception) still updates the remembered font, and a
    ToolError carries the font_note at the end of its message (the same exception object, so its class is kept)."""
    _FONT_CALLS.clear()
    result = None
    refusal = None
    try:
        result = fn(*args)
    except ToolError as exc:
        refusal = exc
        raise
    finally:
        calls = list(_FONT_CALLS)
        _FONT_CALLS.clear()
        fields = _font_fields(calls, result)
        if refusal is not None and fields.get("font_note"):
            refusal.args = (f"{refusal} {fields['font_note']}",) + refusal.args[1:]
    if isinstance(result, dict) and fields:
        result.update(fields)
    return result


def _call_listener(path: str) -> dict:
    """GET a listener endpoint and return its parsed JSON object, or raise ToolError."""
    return _do_request(urllib.request.Request(BASE_URL + path, headers=_client_headers()), path)


def _call_listener_post(path: str, payload: dict, timeout: float = TIMEOUT_SECONDS) -> dict:
    """POST a JSON body to a listener endpoint and return its parsed JSON object."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path, data=body, method="POST",
        headers={"Content-Type": "application/json", **_client_headers()},
    )
    return _do_request(req, path, timeout=timeout)


def _tidy_number(value: Any) -> Any:
    """1000.0 -> 1000 (only when the float is exactly integral)."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _clean_font(data: dict) -> dict:
    """Normalise the listener's font info for Claude; flag unset names honestly."""
    font = {k: _tidy_number(v) for k, v in data.items() if k != "open"}
    notes = []

    # FontLab shows "Unnamed ..." when PostScript names were never set.
    for key in ("postscript_font_name", "postscript_full_name"):
        value = font.get(key)
        if isinstance(value, str) and value.startswith("Unnamed"):
            font[key] = None
            notes.append(
                f"{key} is not set in the font (FontLab's placeholder was ignored)."
            )

    if font.get("errors"):
        notes.append(
            "The listener could not read some fields: " + "; ".join(font.pop("errors"))
        )
    if notes:
        font["notes"] = notes
    return font


# --------------------------------------------------------------------------
# The three operations (plain functions, also used by --check)
# --------------------------------------------------------------------------

def check_status() -> dict:
    health = _call_listener("/health")
    if health.get("status") != "ok":
        raise ToolError("The listener answered /health but did not report status 'ok'.")

    font = _call_listener("/font/current")
    is_open = bool(font.get("open"))
    result = {"listener_reachable": True, "font_open": is_open, "server_version": SERVER_VERSION}
    try:
        reported = _call_listener("/version").get("version")
        result["listener_version"] = reported if isinstance(reported, str) and reported.strip() else "unknown"
    except ToolError:
        result["listener_version"] = "unknown (the listener did not answer /version)"
    try:
        listener = tuple(int(part) for part in result["listener_version"].split("."))
    except ValueError:
        listener = None                 # "unknown" or an unparseable string: say nothing about compatibility
    if listener is not None and listener < MIN_LISTENER_VERSION:
        needed = ".".join(str(n) for n in MIN_LISTENER_VERSION)
        result["compatibility_note"] = (
            f"This server expects listener v{needed} or newer (modern advance width and sidebearing tools, automatic layer creation, draw_polygon with several contours, draw_path with curves, whole-unit rounding reports, the layer guard (a second draw never replaces an outline) and reading API-drawn outlines, clearing a codepoint with 0, holders reported at creation, "
            f"glyphs created under another name); the running listener is v{result['listener_version']}. Copy the current "
            "listener file into FontLab's Scripts folder and restart it.")
    if is_open:
        result["family_name"] = font.get("family_name")
        result["style_name"] = font.get("style_name")
        result["path"] = font.get("path")
    if _CHANGES["session"] or _CHANGES["session_unsure"]:
        result["glyphbridge_changes_this_session"] = _CHANGES["session"]
        result["glyphbridge_uncertain_changes_this_session"] = _CHANGES["session_unsure"]
        result["save_note"] = ("These count the changes made through Glyphbridge since this server started, in whichever font was open "
                               "(not tracked per font). FontLab is not asked whether the font was saved, so this does not show whether "
                               "anything is unsaved now. Glyphbridge never saves: the person saves with the File menu or Ctrl+S.")
    return result


def read_current_font() -> dict:
    data = _call_listener("/font/current")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    return _clean_font(data)


def read_glyph_names() -> dict:
    data = _call_listener("/font/glyphs")
    if not data.get("open"):
        raise ToolError(NO_FONT)

    names = data.get("names")
    count = data.get("count")
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        raise ToolError("The listener's glyph list was malformed, so it was not trusted.")
    if count != len(names):
        raise ToolError(
            f"The listener's glyph list is inconsistent (count={count}, "
            f"names={len(names)}), so it was not trusted."
        )
    return {"count": len(names), "names": names}


def _name_warnings(name: str) -> list:
    """Non-blocking hints about a new glyph name; the glyph is created anyway.

    Only multi-character names are judged: a one-character name is a legitimate
    glyph name (it maps to that character). Rules = common glyph-naming
    conventions that FontLab nevertheless ACCEPTS (seen live): no leading digit;
    a leading '.' only for .notdef; at most 63 characters. Names with characters
    outside A-Z a-z 0-9 . _ - never get here: create_new_glyph refuses them."""
    if len(name) < 2:
        return []
    warnings = []
    if name[0] in "0123456789":
        warnings.append("The name starts with a digit. FontLab accepts it (seen live), but glyph names should not start with a "
                        "digit in a production font.")
    if name[0] == "." and name != ".notdef":
        warnings.append("The name starts with a period. FontLab accepts it (seen live), but only '.notdef' should in a "
                        "production font.")
    if len(name) > 63:
        warnings.append(f"The name is {len(name)} characters long. FontLab accepts it (seen live: 64 and 130 characters), but "
                        "glyph names should be at most 63 in a production font.")
    looks_like = re.fullmatch(r"uni[0-9A-Fa-f]+", name) or re.fullmatch(r"u[0-9A-Fa-f]{4,6}", name)
    is_valid = _UNI_SEQUENCE.fullmatch(name) or _U_NAME.fullmatch(name)
    if looks_like and not is_valid:
        fixed = name[:3] + name[3:].upper() if name.startswith("uni") else name[:1] + name[1:].upper()
        if _UNI_SEQUENCE.fullmatch(fixed) or _U_NAME.fullmatch(fixed):
            warnings.append(f"The name uses lowercase hex digits; the naming convention requires UPPERCASE (use {fixed!r}). "
                            "FontLab maps lowercase hex anyway (seen live: 'uni00e8' -> 232), but other tools may not.")
        else:
            warnings.append("The name looks like a uniXXXX / uXXXX name but does not follow the convention (uni needs 4 hex "
                            "digits per codepoint, u needs 4 to 6), so a codepoint most likely cannot be derived from it "
                            "(not tested in FontLab).")
    return warnings


def _is_codepoint(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 0x10FFFF


def _new_glyph_unicode_fields(clean: str, data: dict) -> tuple:
    """(fields, instruction) describing the Unicode a just-created glyph has. The listener never sets a codepoint at
    creation, so 'assigned' means FontLab mapped the name by itself. A missing or failed read is NEVER reported as 'none'."""
    status, value = data.get("unicode_status"), data.get("unicode")
    expected, kind = _codepoint_from_name(clean)
    if status == "assigned" and _is_codepoint(value):
        matches = None if expected is None else (value == expected)
        fields = {"unicode": value, "unicode_status": "assigned", "unicode_assigned_by_fontlab": True,
                  "unicode_matches_standard": matches}
        if matches is False:
            instruction = (f"FontLab assigned Unicode {value} (U+{value:04X}), but the {kind} '{clean}' stands for "
                           f"{expected} (U+{expected:04X}). Tell the person; change it with "
                           "set_glyph_unicode only if they agree.")
        else:
            instruction = (f"FontLab already assigned Unicode {value} (U+{value:04X}) to '{clean}' from its name: do NOT call "
                           "set_glyph_unicode unless the person wants a different value.")
        return fields, instruction
    if status == "none":
        fields = {"unicode": None, "unicode_status": "none", "unicode_assigned_by_fontlab": False,
                  "unicode_matches_standard": None if expected is None else False}
        if expected is not None:
            check = data.get("duplicate_check")
            holders = [str(n) for n in (check.get("also_held_by") or [])] if isinstance(check, dict) else []
            if isinstance(check, dict):
                fields["also_held_by"] = holders
                fields["glyphs_scanned"] = check.get("scanned")
            if holders:
                verb = "holds" if len(holders) == 1 else "hold"
                instruction = (f"FontLab assigned no Unicode, most likely because {', '.join(holders)} already {verb} "
                               f"U+{expected:04X} (seen live: FontLab skips its automatic assignment when another glyph holds the "
                               f"codepoint). '{clean}' states {expected}. Setting it would create a duplicate: tell the person and "
                               "ask which glyph should keep the codepoint; do not set it on your own.")
                return fields, instruction
            instruction = (f"FontLab assigned no Unicode, but '{clean}' is a {kind} that states {expected} (U+{expected:04X}); "
                           "FontLab normally maps such names by itself (seen live).")
            if not isinstance(check, dict):
                instruction += " Could not check whether another glyph already holds it (is the listener older than v0.51?)."
            elif check.get("scan_error"):
                instruction += f" The scan for other holders failed ({check['scan_error']}), so a holder cannot be ruled out."
            elif check.get("unreadable"):
                instruction += f" {check['unreadable']} glyph(s) could not be read, so a holder among them cannot be ruled out."
            else:
                instruction += " No other glyph was found holding it."
            instruction += " You may set it with set_glyph_unicode and should tell the person."
        else:
            instruction = (f"FontLab assigned no Unicode to '{clean}'. That is normal for non-standard names (alternates such as "
                           "'A.alt', ligatures such as 'f_i', work glyphs): leave it unencoded.")
            if "." not in clean and "_" not in clean:
                instruction += (" BUT if it is a standard glyph name (for example an accented letter such as 'eacute'), FontLab "
                                "skips its automatic assignment when another glyph already holds that codepoint (seen live): "
                                "look for that glyph before treating this one as unencoded on purpose.")
            instruction += " Call set_glyph_unicode only if the person asks for a specific codepoint; never guess one."
        return fields, instruction
    fields = {"unicode": None, "unicode_assigned_by_fontlab": None, "unicode_matches_standard": None}
    if status == "unreadable":
        fields["unicode_status"] = "unreadable"
        why = data.get("unicode_error")
        instruction = ("The glyph's Unicode could not be read right after creation" + (f" ({why})" if why else "") +
                       "; call check_glyph_unicode to find out before using set_glyph_unicode.")
    elif status is None:
        fields["unicode_status"] = "unknown"
        instruction = ("The listener did not report a Unicode status (is it older than v0.49? restart it with the current "
                       "file); call check_glyph_unicode to find out before using set_glyph_unicode.")
    else:
        fields["unicode_status"] = "unknown"
        instruction = (f"The listener's Unicode report was not usable (status {status!r}, value {value!r}); call "
                       "check_glyph_unicode to find out before using set_glyph_unicode.")
    return fields, instruction


_NAME_SAFE = re.compile(r"[A-Za-z0-9._-]")


def _fontlab_safe_name(name: str) -> str:
    """The name with every character outside A-Z a-z 0-9 . _ - removed: what FontLab keeps (live probes: those survive;
    non-ASCII letters, spaces and # / * : + @ ! $ % & ( ) ~ = were all stripped silently)."""
    return "".join(c for c in name if _NAME_SAFE.fullmatch(c))


_GUARD_FLAG_KEYS = ("synced_with_fontlab",)
_SYNC_BOOL_KEYS = ("attempted", "synced")
_SYNC_TEXT_KEYS = ("verdict", "call_error", "reason")
_GUARD_TEXT_KEYS = ("durability_note", "display_refresh", "display_refresh_note")
_GUARD_LIST_KEYS = ("display_refresh_skipped_to_protect", "display_refresh_unreadable_glyphs", "layers_missing_since_drawn")
_GUARD_UNSYNCED_INSTRUCTION = ("The change is held only in FontLab's memory and FontLab has not synced it (synced_with_fontlab is false): the grid "
                               "thumbnail may stay blank, and create_glyph, delete_glyph and set_glyph_unicode skip FontLab's display refresh while it is "
                               "unsynced so that they do not throw it away. Tell the person once. Opening the glyph in an editor in FontLab and then "
                               "sending any request makes FontLab sync it.")
_GUARD_SYNC_FAILED_INSTRUCTION = ("Glyphbridge asked FontLab to sync this glyph right after the change, but the glyph did not read as synced afterwards "
                                 "(see fontlab_sync.verdict and call_error).")
_GUARD_SKIPPED_INSTRUCTION = ("The operation was done, but FontLab's display refresh was skipped on purpose (display_refresh is 'skipped') to protect "
                              "the unsynced drawings listed in display_refresh_skipped_to_protect; the grid may therefore not show the change at once. "
                              "Mention it to the person.")
_GUARD_MISSING_INSTRUCTION = ("layers_missing_since_drawn lists glyphs whose drawn layer was already gone when this was checked (it was lost "
                              "before this call). Tell the person and check those glyphs with get_glyph_outline.")


def _add_guard_fields(result: dict, data: dict) -> None:
    """Forward the listener's v0.87 guard fields (never anything else), type-checked; add short instructions. A listener without them adds nothing."""
    try:
        extra = []
        for key in _GUARD_FLAG_KEYS:
            if isinstance(data.get(key), bool):
                result[key] = data[key]
        for key in _GUARD_TEXT_KEYS:
            if isinstance(data.get(key), str) and data[key]:
                result[key] = data[key]
        for key in _GUARD_LIST_KEYS:
            v = data.get(key)
            if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
                result[key] = list(v)
        fs = data.get("fontlab_sync")
        if isinstance(fs, dict):
            fwd = {}
            for key in _SYNC_BOOL_KEYS:
                if isinstance(fs.get(key), bool):
                    fwd[key] = fs[key]
            for key in _SYNC_TEXT_KEYS:
                if isinstance(fs.get(key), str) and fs[key]:
                    fwd[key] = fs[key]
            if fwd:
                result["fontlab_sync"] = fwd
        if result.get("synced_with_fontlab") is False:
            if isinstance(result.get("fontlab_sync"), dict) and result["fontlab_sync"].get("attempted") is True:
                extra.append(_GUARD_SYNC_FAILED_INSTRUCTION)
            extra.append(_GUARD_UNSYNCED_INSTRUCTION)
        if result.get("display_refresh") == "skipped":
            extra.append(_GUARD_SKIPPED_INSTRUCTION)
        if result.get("layers_missing_since_drawn"):
            extra.append(_GUARD_MISSING_INSTRUCTION)
        if extra:
            existing = result.get("agent_instruction")
            result["agent_instruction"] = (existing + " " if existing else "") + " ".join(extra)
    except Exception:
        pass


def create_new_glyph(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    kept = _fontlab_safe_name(clean)
    if kept != clean:
        bad_chars = list(dict.fromkeys(c for c in clean if not _NAME_SAFE.fullmatch(c)))
        bad = " ".join(repr(c) for c in bad_chars[:8]) + (" ..." if len(bad_chars) > 8 else "")
        advice = []
        if any(ord(c) > 126 for c in clean):
            advice.append("for an accented letter use its standard ASCII name (for e-acute: 'eacute' or 'uni00E9')")
        if any(c.isspace() for c in clean):
            advice.append("use '_' or '-' instead of spaces")
        if any(33 <= ord(c) <= 126 and not _NAME_SAFE.fullmatch(c) for c in clean):
            advice.append("leave out punctuation such as # / * : + @ ! $ % & ( ) ~ = or replace it with '_'")
        raise ToolError(
            f"Glyph name {clean!r} was NOT sent to FontLab: it contains characters FontLab silently strips ({bad}). Seen live, "
            "FontLab keeps only A-Z a-z 0-9 . _ - : a name ending in a non-ASCII e lost that letter, 'a b' became 'ab', "
            "'a#b/c*d:e' became 'abcde', a lone non-ASCII letter became an EMPTY name. It would create a glyph under the "
            f"altered name, here {kept!r}" + (" (an EMPTY name)" if not kept else "") + ". Use only A-Z a-z 0-9 . _ -"
            + ("; " + "; ".join(advice) if advice else "") + ".")

    payload = {"name": clean}
    stated, _kind = _codepoint_from_name(clean)
    if stated is not None:
        payload["scan_unicode"] = stated    # lets the listener look for other holders if FontLab assigns nothing
    data = _write_post("/glyph/create", payload)

    if not data.get("open"):
        raise ToolError(NO_FONT)

    if not data.get("created"):
        other = data.get("created_under_other_names")
        if other:
            names = ", ".join(repr(n) if n else "an EMPTY name" for n in other)
            _note_change()
            raise ToolError(
                f"Glyph '{clean}' was NOT created, but FontLab DID create a glyph under a different name instead: {names}. It "
                "strips characters it does not accept from names. That glyph is now in the font: tell the person"
                + ("; a glyph with an empty name cannot be deleted with delete_glyph, which needs a name." if "" in other
                   else "; delete_glyph can remove it.") + " " + _CHANGED_BY_ERROR_NOTE)
        reason = data.get("reason")
        call_error = data.get("call_error")
        if reason and call_error:
            detail = f"{reason} (FontLab reported: {call_error})"
        elif call_error:
            detail = f"FontLab reported: {call_error}"
        else:
            detail = reason or "unknown reason"
        raise ToolError(f"Glyph '{clean}' was NOT created: {detail}")

    result = {
        "created": True,
        "name": clean,
        "glyph_count_before": data.get("before_count"),
        "glyph_count_after": data.get("after_count"),
    }
    fields, instruction = _new_glyph_unicode_fields(clean, data)
    result.update(fields)
    warnings = _name_warnings(clean)
    if warnings:
        result["name_warnings"] = warnings
        instruction += " The name_warnings are hints only (the glyph WAS created); mention them to the person."
    result["agent_instruction"] = instruction
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


def read_glyph_width(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")

    data = _call_listener(f"/glyph/width?name={quote(clean)}")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if not data.get("found"):
        raise ToolError(f"No glyph named '{clean}' was found.")

    return {"name": clean, "width": _tidy_number(data.get("width"))}


def write_glyph_width(name: str, width: float) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    if isinstance(width, bool) or not isinstance(width, (int, float)):
        raise ToolError("Width must be a number.")
    if width < 0:
        raise ToolError("Width must not be negative.")

    data = _write_post("/glyph/width", {"name": clean, "width": width})

    if not data.get("open"):
        raise ToolError(NO_FONT)

    if not data.get("set"):
        reason = data.get("reason")
        call_error = data.get("call_error")
        if reason and "no glyph named" in reason:
            raise ToolError(f"No glyph named '{clean}' was found.")
        if reason and call_error:
            detail = f"{reason} (FontLab reported: {call_error})"
        elif call_error:
            detail = f"FontLab reported: {call_error}"
        else:
            detail = reason or "unknown reason"
        if data.get("layer_created"):
            _note_change()
            raise ToolError(f"Width of glyph '{clean}' was NOT changed: {detail}. A layer named '{data['layer_created']}' WAS created "
                            f"for the glyph, so the font counts as changed. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Width of glyph '{clean}' was NOT changed: {detail}")

    result = {
        "name": clean,
        "width_before": _tidy_number(data.get("before")),
        "width_after": _tidy_number(data.get("after")),
    }
    for key in ("route", "outline_untouched", "warning", "display_note", "layer_created", "layer_create_note"):
        if data.get(key) is not None:
            result[key] = data[key]
    _add_guard_fields(result, data)
    _mark_modified(result, result["width_before"] != result["width_after"] or bool(data.get("layer_created")))
    return result


def _require_listener(minimum: tuple, feature: str) -> None:
    """Refuse BEFORE sending anything when the listener is known to be older than `minimum`. An unreadable version lets the call decide."""
    try:
        reported = _call_listener("/version").get("version")
        have = tuple(int(part) for part in str(reported).split("."))
    except Exception:
        return
    if have < minimum:
        raise ToolError(f"{feature} needs listener v{'.'.join(str(n) for n in minimum)} or newer; the running listener is v{reported}. "
                        "Copy the current listener file into FontLab's Scripts folder and restart it. Nothing was changed.")


def _check_margin_number(label: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ToolError(f"{label} must be a number.")
    if value != value or abs(value) > 10000:
        raise ToolError(f"{label} must be a number between -10000 and 10000.")


def read_glyph_sidebearings(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    _require_listener((0, 68), "get_glyph_sidebearings")
    data = _call_listener(f"/glyph/sidebearings?name={quote(clean)}")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if data.get("modern_layer") is False:
        raise ToolError(f"Sidebearings of glyph '{clean}' cannot be read: {data.get('reason') or 'no editable layer'}")
    if not data.get("readable"):
        raise ToolError(f"Sidebearings of glyph '{clean}' could not be read: {data.get('reason') or 'unknown reason'}")
    return {"name": clean, "left": _tidy_number(data.get("lsb")), "right": _tidy_number(data.get("rsb")),
            "advance_width": _tidy_number(data.get("advance")), "ink_width": _tidy_number(data.get("ink_width")),
            "note": "Left, right and advance width as FontLab's editor panel shows them; ink_width = advance - left - right."}


_KERN_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,63}$")
_KERN_CONFIRM_ABOVE = 250     # more pairs than this need the person's approval (confirmed_large_read=true); there is no upper limit
_KERN_INSTRUCTION = (
    "Values are in font units (units_per_em says how many per em); a NEGATIVE value moves the pair closer together, a positive one pushes it apart. "
    "They are FontLab's own numbers from the kerning table of the current master (master names it), class (group) kerning included. "
    "'source' says which kind of entry gave the value: 'glyph : glyph' (a direct pair), 'glyph : class' or 'class : glyph' (an exception against a class, "
    "with right_class or left_class naming it), 'class : class' (both classes named), or 'none' (FontLab has no entry: value 0, kerned false). "
    "Report the source as given; never guess whether a value comes from a class. An entry can hold 0 on purpose (kerned false, but a source other than 'none'). "
    "A result with an 'error' was NOT read: never treat it as zero kerning. Other masters, feature-based (GPOS lookup) and contextual kerning are NOT covered by this tool. "
    "Only the pairs you asked for were read; do not request the whole table."
)
_KERN_SOURCES = ("glyph : glyph", "glyph : class", "class : glyph", "class : class", "none")
_KERN_SOURCE_CLASSES = {"glyph : glyph": (), "glyph : class": ("right_class",), "class : glyph": ("left_class",),
                        "class : class": ("left_class", "right_class"), "none": ()}


def _kern_pair_names(pairs: Any) -> list:
    """The pairs as a clean list of (left, right) glyph-name tuples, or a ToolError (before anything is sent)."""
    if not isinstance(pairs, (list, tuple)) or len(pairs) < 1:
        raise ToolError("pairs must be a list of at least one [left, right] glyph-name pair.")
    clean = []
    for i, pair in enumerate(pairs):
        if (not isinstance(pair, (list, tuple)) or len(pair) != 2
                or not all(isinstance(n, str) and _KERN_NAME_RE.match(n.strip() or "!") for n in pair)):
            raise ToolError(f"pair {i + 1} must be [left, right], two glyph names of 1 to 63 characters from A-Z a-z 0-9 . _ - (got {pair!r}).")
        clean.append((pair[0].strip(), pair[1].strip()))
    return clean


def _kern_text(text: Any) -> str:
    if not isinstance(text, str) or len(text) < 2:
        raise ToolError("text must be a string of at least 2 characters.")
    if any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in text):
        raise ToolError("text must not contain control characters.")
    return text


def _kern_entry(raw: Any, expected: Any) -> dict:
    """One listener result as a clean, type-checked entry. Anything unusable becomes an error entry, never a zero."""
    out: dict = {}
    if isinstance(expected, tuple):
        out["left"], out["right"] = expected
    if not isinstance(raw, dict):
        out["error"] = "the listener's answer for this pair was unusable, so it was not read"
        return out
    for key in ("left", "right"):
        got = raw.get(key)
        if isinstance(got, str):
            if key in out and out[key] != got:
                out["error"] = "the listener answered for a different pair than the one asked, so it was not read"
                return out
            out[key] = got
        elif key not in out and got is None:
            out[key] = None
    if isinstance(raw.get("chars"), str):
        out["chars"] = raw["chars"]
    err = raw.get("error")
    if isinstance(err, str) and err:
        out["error"] = err[:600]
        return out
    value = raw.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or abs(value) == float("inf"):
        out["error"] = "the listener's answer for this pair carried no usable number, so it was not read"
        return out
    source = raw.get("source")
    if source not in _KERN_SOURCES:
        out["error"] = "the listener's answer for this pair carried no valid source, so it was not read"
        return out
    if source == "none" and value != 0:
        out["error"] = "the listener's answer for this pair said 'no entry' but carried a value, so it was not read"
        return out
    classes = {}
    for key in _KERN_SOURCE_CLASSES[source]:
        name = raw.get(key)
        if not isinstance(name, str) or not _KERN_NAME_RE.match(name):
            out["error"] = f"the listener's answer for this pair named no valid {key.replace('_', ' ')}, so it was not read"
            return out
        classes[key] = name
    out["value"] = _tidy_number(value)
    out["kerned"] = value != 0
    out["source"] = source
    out.update(classes)
    return out


def read_kerning(pairs: Any = None, text: Any = None, confirmed_large_read: Any = None) -> dict:
    if confirmed_large_read is not None and not isinstance(confirmed_large_read, bool):
        raise ToolError("confirmed_large_read must be true or false (or left out).")
    if (pairs is None) == (text is None):
        raise ToolError("Give exactly one of pairs (a list of [left, right] glyph names) or text (a short string).")
    if pairs is not None:
        expected = _kern_pair_names(pairs)
        payload = {"pairs": [[a, b] for a, b in expected]}
    else:
        clean_text = _kern_text(text)
        expected = [None] * (len(clean_text) - 1)
        payload = {"text": clean_text}
    large = len(expected) > _KERN_CONFIRM_ABOVE
    if large and confirmed_large_read is not True:
        raise ToolError(
            f"This request would read {len(expected)} kerning pairs, more than the {_KERN_CONFIRM_ABOVE}-pair threshold, and nothing was read. "
            "Do NOT repeat the call yet. A large read costs many tokens: tell the person how many pairs you want to read and why, and ask whether they approve. "
            "Only after they have said yes, call get_kerning again with the same arguments and confirmed_large_read=true. Never set that flag without the person's approval.")
    # v0.33: listener 0.104 reads the master's table with class-aware keys; older listeners can report false zeros and class values (P0.8)
    _require_listener((0, 104), "get_kerning")
    data = _call_listener_post("/kerning/pairs", payload, timeout=max(TIMEOUT_SECONDS, 5.0 + len(expected) / 50.0))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        raise ToolError(f"Kerning could not be read: {data['error'][:600]}")
    raw_results = data.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(expected):
        raise ToolError("Kerning could not be read: the listener's answer did not match the request. Nothing was changed.")
    results = [_kern_entry(r, e) for r, e in zip(raw_results, expected)]
    errors = sum(1 for r in results if "error" in r)
    size = data.get("table_size")
    upm = data.get("units_per_em")
    master = data.get("master")
    master_count = data.get("master_count")
    fonts_open = data.get("fonts_open")
    matched_by = data.get("matched_by")
    family = data.get("family_name")
    reply = {"mode": "pairs" if pairs is not None else "text",
             "fonts_open": fonts_open if isinstance(fonts_open, int) and not isinstance(fonts_open, bool) and fonts_open >= 1 else None,
             "matched_by": matched_by if matched_by in ("only font", "path") else None,
             "family_name": family if isinstance(family, str) and 1 <= len(family) <= 63 and family.isprintable() else None,
             "master": master if isinstance(master, str) and 1 <= len(master) <= 63 and master.isprintable() else None,
             "master_count": master_count if isinstance(master_count, int) and not isinstance(master_count, bool) and master_count >= 1 else None,
             "units_per_em": _tidy_number(upm) if isinstance(upm, (int, float)) and not isinstance(upm, bool) else None,
             "table_size": size if isinstance(size, int) and not isinstance(size, bool) else None,
             "count": len(results), "errors": errors, "results": results}
    instruction = _KERN_INSTRUCTION
    if large:
        reply["large_read_confirmed"] = True
    if reply["table_size"] == 0:
        instruction += " table_size is 0: the current master's kerning table is empty, so this master has no kerning at all."
    if reply["fonts_open"] is not None and reply["fonts_open"] > 1:
        which = f" ({reply['family_name']})" if reply["family_name"] else ""
        instruction += (f" {reply['fonts_open']} fonts are open in FontLab; this was read from the current one, the font whose window is in front{which}, "
                        "matched to its kerning table by its file path. Say which font when you report the values.")
    if reply["master_count"] is not None and reply["master_count"] > 1:
        instruction += f" This font has {reply['master_count']} masters; only the current one was read. Say so when you report the values."
    if data.get("side_effect_detected") is True:
        reply["side_effect_detected"] = True
        instruction += " WARNING: the size of the kerning table changed while reading, which a read must never do. Tell the person and do not trust further kerning edits until they have looked."
    reply["agent_instruction"] = instruction
    return reply


def write_glyph_sidebearings(name: str, left: float, right: Any = None) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    if right is None:
        right = left
    _check_margin_number("left", left)
    _check_margin_number("right", right)
    _require_listener((0, 68), "set_glyph_sidebearings")

    data = _write_post("/glyph/sidebearings", {"name": clean, "left": left, "right": right})

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if not data.get("set"):
        reason = data.get("reason") or "unknown reason"
        call_error = data.get("call_error")
        detail = f"{reason} (FontLab reported: {call_error})" if call_error else reason
        before, after = data.get("before"), data.get("after")
        if isinstance(before, dict) and isinstance(after, dict) and before != after:
            # FontLab was called and something moved although the re-read does not match the request: the font HAS changed.
            _note_change()
            raise ToolError(f"Sidebearings of glyph '{clean}' were changed, but {detail}. "
                            f"Now: left {_tidy_number(after.get('lsb'))}, right {_tidy_number(after.get('rsb'))}, "
                            f"advance width {_tidy_number(after.get('advance'))}. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Sidebearings of glyph '{clean}' were NOT changed: {detail}")

    before, after = data.get("before") or {}, data.get("after") or {}
    result = {
        "name": clean,
        "verified": True,
        "left_before": _tidy_number(before.get("lsb")), "left_after": _tidy_number(after.get("lsb")),
        "right_before": _tidy_number(before.get("rsb")), "right_after": _tidy_number(after.get("rsb")),
        "advance_width_before": _tidy_number(before.get("advance")), "advance_width_after": _tidy_number(after.get("advance")),
        "ink_width": _tidy_number(data.get("ink_width")),
        "note": "advance width = left + ink width + right; the outline moved, its shape did not change.",
    }
    if data.get("display_note"):
        result["display_note"] = data["display_note"]
    _add_guard_fields(result, data)
    _mark_modified(result, bool(data.get("changed")))
    return result


_POLY_LIMITS = (3, 500)


def _check_polygon_points(points: Any) -> list:
    """The points as a clean list of [x, y] floats, or a ToolError (before anything is sent)."""
    low, high = _POLY_LIMITS
    if not isinstance(points, (list, tuple)) or not (low <= len(points) <= high):
        raise ToolError(f"points must be a list of {low} to {high} [x, y] pairs.")
    clean = []
    for pt in points:
        if (not isinstance(pt, (list, tuple)) or len(pt) != 2
                or any(isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or abs(v) > 20000 for v in pt)):
            raise ToolError("every point must be [x, y] with numbers between -20000 and 20000.")
        clean.append([float(pt[0]), float(pt[1])])
    if len({(x, y) for x, y in clean}) < 3:
        raise ToolError("the points must contain at least 3 different positions.")
    return clean


_POLY_MAX_CONTOURS, _POLY_MAX_TOTAL = 20, 2000


def write_glyph_polygon(name: str, points: Any = None, contours: Any = None) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    if (points is None) == (contours is None):
        raise ToolError("Give exactly one of points (one contour) or contours (a list of point lists).")
    if contours is None:
        payload = {"name": clean, "points": _check_polygon_points(points)}
    else:
        if not isinstance(contours, (list, tuple)) or not (1 <= len(contours) <= _POLY_MAX_CONTOURS):
            raise ToolError(f"contours must be a list of 1 to {_POLY_MAX_CONTOURS} point lists.")
        checked = [_check_polygon_points(c) for c in contours]
        if sum(len(c) for c in checked) > _POLY_MAX_TOTAL:
            raise ToolError(f"at most {_POLY_MAX_TOTAL} points in total.")
        payload = {"name": clean, "contours": checked}
    _require_listener((0, 82), "draw_polygon")

    data = _write_post("/glyph/polygon", payload)

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if not data.get("drawn"):
        reason = data.get("reason") or "unknown reason"
        if data.get("changed"):
            _note_change()
            raise ToolError(f"Glyph '{clean}': something was drawn, but {reason}. {_CHANGED_BY_ERROR_NOTE}")
        if data.get("layer_created"):
            _note_change()
            raise ToolError(f"Glyph '{clean}' was NOT drawn: {reason}. A layer named '{data['layer_created']}' WAS created for it, "
                            f"so the font counts as changed. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Glyph '{clean}' was NOT drawn: {reason}")

    margins = data.get("margins") if isinstance(data.get("margins"), dict) else {}
    after = data.get("state_after") or {}
    result = {
        "name": clean,
        "drawn": True,
        "verified": True,
        "coordinates_rounded": _rounded_list(data.get("coordinates_rounded")),
        "points": data.get("points"),
        "contours": data.get("contours") if isinstance(data.get("contours"), int) else 1,
        "contour_sizes": data.get("contour_sizes") if isinstance(data.get("contour_sizes"), list) else [data.get("points")],
        "shapes": after.get("shapes"),
        "nodes": after.get("nodes"),
        "left": _tidy_number(margins.get("lsb")), "right": _tidy_number(margins.get("rsb")),
        "advance_width": _tidy_number(margins.get("advance")),
        "ink_width": _tidy_number(data.get("ink_width")),
        "note": ("Closed contours of straight segments, in one shape. The advance width is NOT changed by drawing: set it with set_glyph_width, "
                 "or place the outline and the width together with set_glyph_sidebearings."),
    }
    _add_rounding_note(result)
    for key in ("layer_created", "display_note"):
        if data.get(key) is not None:
            result[key] = data[key]
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


_ROUNDING_NOTE = ("Rule B: FontLab stores whole font units here, so every coordinate was rounded to the nearest whole unit (a half rounds up). "
                  "coordinates_rounded lists each coordinate that changed (requested value, value used). Give whole numbers to avoid this.")


def _rounded_list(value: Any) -> list:
    """The listener's coordinates_rounded list as plain entries (never raises; anything unusable becomes an empty list)."""
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, dict):
            out.append({k: (_tidy_number(v) if k in ("requested", "used") else v) for k, v in item.items()})
    return out


def _add_rounding_note(result: dict) -> None:
    if result.get("coordinates_rounded"):
        result["rounding_note"] = _ROUNDING_NOTE


def _check_path_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or abs(value) > 20000:
        raise ToolError(f"{where} must be a number between -20000 and 20000.")
    return float(value)


def _check_path_xy(value: Any, where: str) -> dict:
    if not isinstance(value, dict) or set(value) - {"x", "y"} or "x" not in value or "y" not in value:
        raise ToolError(f"{where} must be an object {{\"x\": number, \"y\": number}}.")
    return {"x": _check_path_number(value["x"], where + " x"), "y": _check_path_number(value["y"], where + " y")}


def _check_path_contours(contours: Any) -> list:
    """The contours as clean lists of point dicts, or a ToolError (before anything is sent)."""
    if not isinstance(contours, (list, tuple)) or not (1 <= len(contours) <= _POLY_MAX_CONTOURS):
        raise ToolError(f"contours must be a list of 1 to {_POLY_MAX_CONTOURS} point lists.")
    low, high = _POLY_LIMITS
    clean, total = [], 0
    for ci, plist in enumerate(contours):
        if not isinstance(plist, (list, tuple)) or not (low <= len(plist) <= high):
            raise ToolError(f"contour {ci} must be a list of {low} to {high} points.")
        pts = []
        for pi, pt in enumerate(plist):
            where = f"contour {ci} point {pi}"
            if not isinstance(pt, dict) or set(pt) - {"x", "y", "c1", "c2", "smooth"}:
                raise ToolError(f"{where} must be an object with x, y and optionally c1, c2, smooth.")
            if "x" not in pt or "y" not in pt:
                raise ToolError(f"{where} needs x and y.")
            item = _check_path_xy({"x": pt["x"], "y": pt["y"]}, where)
            if (pt.get("c1") is None) != (pt.get("c2") is None):
                raise ToolError(f"{where}: give c1 and c2 together (both control points of the curved segment) or neither.")
            if pt.get("c1") is not None:
                item["c1"] = _check_path_xy(pt["c1"], where + " c1")
                item["c2"] = _check_path_xy(pt["c2"], where + " c2")
                total += 2
            if "smooth" in pt:
                if not isinstance(pt["smooth"], bool):
                    raise ToolError(f"{where}: smooth must be true or false.")
                if pt["smooth"]:
                    item["smooth"] = True
            pts.append(item)
            total += 1
        if len({(p["x"], p["y"]) for p in pts}) < 3:
            raise ToolError(f"contour {ci} needs at least 3 different on-curve positions.")
        clean.append(pts)
    if total > _POLY_MAX_TOTAL:
        raise ToolError(f"at most {_POLY_MAX_TOTAL} nodes in total (every curved segment adds its two control points).")
    return clean


def write_glyph_path(name: str, contours: Any) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    checked = _check_path_contours(contours)
    _require_listener((0, 82), "draw_path")

    data = _write_post("/glyph/path", {"name": clean, "contours": checked})

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if not data.get("drawn"):
        reason = data.get("reason") or "unknown reason"
        if data.get("changed"):
            _note_change()
            raise ToolError(f"Glyph '{clean}': something was drawn, but {reason}. {_CHANGED_BY_ERROR_NOTE}")
        if data.get("layer_created"):
            _note_change()
            raise ToolError(f"Glyph '{clean}' was NOT drawn: {reason}. A layer named '{data['layer_created']}' WAS created for it, "
                            f"so the font counts as changed. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Glyph '{clean}' was NOT drawn: {reason}")

    margins = data.get("margins") if isinstance(data.get("margins"), dict) else {}
    after = data.get("state_after") or {}
    result = {
        "name": clean,
        "drawn": True,
        "verified": True,
        "nodes_match": data.get("nodes_match") is True,
        "coordinates_rounded": _rounded_list(data.get("coordinates_rounded")),
        "points": data.get("points"),
        "curved_segments": data.get("segments_curved"),
        "contours": data.get("contours") if isinstance(data.get("contours"), int) else len(checked),
        "contour_sizes": data.get("contour_sizes") if isinstance(data.get("contour_sizes"), list) else None,
        "shapes": after.get("shapes"),
        "nodes": after.get("nodes"),
        "left": _tidy_number(margins.get("lsb")), "right": _tidy_number(margins.get("rsb")),
        "advance_width": _tidy_number(margins.get("advance")),
        "ink_width": _tidy_number(data.get("ink_width")),
        "note": ("Closed contours of straight and cubic segments, in one shape; nodes counts the control points too. Every node of the "
                 "re-read layer matched the request. The advance width is NOT changed by drawing: set it with set_glyph_width, or place the "
                 "outline and the width together with set_glyph_sidebearings. Call get_glyph_outline to compare the curve extents with FontLab's own margins."),
    }
    _add_rounding_note(result)
    for key in ("layer_created", "display_note"):
        if data.get(key) is not None:
            result[key] = data[key]
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


_UNI_NAME = re.compile(r"uni([0-9A-F]{4})")        # uniXXXX: exactly one codepoint, UPPERCASE hex
_U_NAME = re.compile(r"u([0-9A-F]{4,6})")          # uXXXX .. uXXXXXX
_UNI_SEQUENCE = re.compile(r"uni(?:[0-9A-F]{4})+")  # uni00410042: valid, but a SEQUENCE (ligature), not one codepoint


def _codepoint_from_name(name: str):
    """(codepoint, kind) when the NAME itself states a codepoint, else (None, None). Unambiguous cases only:
    a one-character name (that character's own codepoint), uniXXXX and uXXXX[XX] (the glyph-naming convention;
    UPPERCASE hex, no surrogates, at most 10FFFF). Anything else (multi-character conventional names like
    "ampersand") needs the Adobe Glyph List, which isn't implemented here - return None rather than guess."""
    if len(name) == 1:
        return ord(name), "single-character name"
    m = _UNI_NAME.fullmatch(name) or _U_NAME.fullmatch(name)
    if m:
        value = int(m.group(1), 16)
        if value <= 0x10FFFF and not 0xD800 <= value <= 0xDFFF:
            return value, ("uniXXXX name" if name.startswith("uni") else "uXXXX name")
    return None, None


def _expected_unicode_for_name(name: str):
    """The codepoint the name itself states (see _codepoint_from_name), or None."""
    return _codepoint_from_name(name)[0]


def read_glyph_unicode(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")

    data = _call_listener(f"/glyph/unicode?name={quote(clean)}")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if not data.get("found"):
        raise ToolError(f"No glyph named '{clean}' was found.")

    current = data.get("unicode")
    expected = _expected_unicode_for_name(clean)

    result = {"name": clean, "unicode": current, "has_unicode": current is not None}
    if expected is not None:
        result["expected_unicode"] = expected
        result["matches_standard"] = (current == expected)
    else:
        result["expected_unicode"] = None
        result["matches_standard"] = None
        result["note"] = (
            "This glyph's name is not a single character and does not state a "
            "codepoint (uniXXXX / uXXXX), so the standard codepoint can't be "
            "determined automatically yet (only single-character names like "
            "'A' or '7' and uniXXXX / uXXXX names are checked directly "
            "against the Unicode standard)."
        )
    return result


def write_glyph_unicode(name: str, codepoint: int) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    if isinstance(codepoint, bool) or not isinstance(codepoint, int):
        raise ToolError("Codepoint must be a plain integer (e.g. 65 for 'A'), not text or a fraction.")
    if codepoint < 0 or codepoint > 0x10FFFF:
        raise ToolError("Codepoint must be between 0 and 0x10FFFF (the valid Unicode range).")

    data = _write_post("/glyph/unicode", {"name": clean, "unicode": codepoint})

    if not data.get("open"):
        raise ToolError(NO_FONT)

    if not data.get("set"):
        reason = data.get("reason")
        call_error = data.get("call_error")
        if reason and "no glyph named" in reason:
            raise ToolError(f"No glyph named '{clean}' was found.")
        if reason and call_error:
            detail = f"{reason} (FontLab reported: {call_error})"
        elif call_error:
            detail = f"FontLab reported: {call_error}"
        else:
            detail = reason or "unknown reason"
        raise ToolError(f"Unicode codepoint of glyph '{clean}' was NOT changed: {detail}")

    result = {
        "name": clean,
        "unicode_before": data.get("before"),
        "unicode_after": data.get("after"),
        "changed": data.get("before") != data.get("after"),
    }
    if not result["changed"]:
        if codepoint == 0:
            result["note"] = "Nothing changed: the glyph already had no Unicode."
        else:
            result["note"] = ("Nothing changed: the glyph already had this codepoint. FontLab assigns Unicode to standard glyph "
                              "names when the glyph is created (the create_glyph reply reports it), so this call was not needed.")
    if codepoint != 0:
        _add_duplicate_info(result, data.get("duplicate_check"), codepoint)
    _add_guard_fields(result, data)
    _mark_modified(result, result["changed"])
    return result


def _add_duplicate_info(result: dict, check, codepoint: int) -> None:
    """Report OTHER glyphs holding the same codepoint. Warning only: FontLab accepts duplicates silently, and moving a
    codepoint on purpose is legitimate, so nothing is blocked or undone. Missing or partial evidence is said, never hidden."""
    if not isinstance(check, dict):
        result["duplicate_check"] = "unavailable (the listener did not report it: is it older than v0.50?)"
        return
    holders = [str(n) for n in (check.get("also_held_by") or [])]
    result["also_held_by"] = holders
    result["glyphs_scanned"] = check.get("scanned")
    if holders:
        result["duplicate_warning"] = (
            f"U+{codepoint:04X} is now held by {len(holders) + 1} glyphs: this one and {', '.join(holders)}. FontLab accepted "
            "the duplicate silently. Two glyphs on one character is normally a mistake: tell the person and ask whether "
            "the other glyph(s) should lose the codepoint; nothing was changed automatically.")
    if check.get("scan_error"):
        result["duplicate_note"] = f"The duplicate scan failed ({check['scan_error']}), so duplicates cannot be ruled out."
    elif check.get("unreadable"):
        result["duplicate_note"] = (f"{check['unreadable']} glyph(s) could not be read, so a duplicate among them cannot be "
                                    "ruled out.")


def delete_existing_glyph(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")

    # This call blocks until a human answers a Yes/No dialog inside
    # FontLab, so it needs a much longer timeout than a normal request.
    data = _write_post("/glyph/delete", {"name": clean}, timeout=DELETE_CONFIRM_TIMEOUT_SECONDS)

    if not data.get("open"):
        raise ToolError(NO_FONT)

    if not data.get("deleted"):
        if data.get("user_declined"):
            raise ToolError(
                f"Deletion of glyph '{clean}' was not approved in FontLab. "
                "A person needs to click Yes on the confirmation dialog for this to proceed - "
                "this is expected behavior, not an error."
            )
        reason = data.get("reason")
        call_error = data.get("call_error")
        if reason and call_error:
            detail = f"{reason} (FontLab reported: {call_error})"
        elif call_error:
            detail = f"FontLab reported: {call_error}"
        else:
            detail = reason or "unknown reason"
        raise ToolError(f"Glyph '{clean}' was NOT deleted: {detail}")

    result = {
        "deleted": True,
        "name": clean,
        "glyph_count_before": data.get("before_count"),
        "glyph_count_after": data.get("after_count"),
    }
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


def finish_change_package() -> dict:
    """End of a task package: report how many changes were made since the last call and return the save reminder ONCE."""
    sure, unsure = _CHANGES["package"], _CHANGES["package_unsure"]
    _CHANGES["package"] = _CHANGES["package_unsure"] = 0
    if not sure and not unsure:
        result = {"changes_in_package": 0, "uncertain_changes_in_package": 0, "save_reminder": None,
                  "note": ("Nothing was changed through Glyphbridge since the last finish_changes call (or since the server started), so "
                           "no save reminder is due now. Do not invent one.")}
        if _CHANGES["session"] or _CHANGES["session_unsure"]:
            result["note"] += (" Changes from EARLIER packages in this session may still be unsaved: Glyphbridge cannot see whether the "
                               "person saved.")
        return result
    result = {"changes_in_package": sure, "uncertain_changes_in_package": unsure, "save_reminder": SAVE_REMINDER,
              "agent_instruction": ("Show the person save_reminder now, ONCE, in bold exactly as written (it already contains the bold markers), "
                                    "after your summary of what was done. Do not repeat it for single steps and do not call finish_changes "
                                    "again for the same package. Glyphbridge has not saved anything and cannot; no dialog is shown in FontLab.")}
    if unsure:
        result["uncertain_note"] = ("Some request(s) may not have been applied (timeout or unusable reply): say so, and check the font's "
                                    "state with a read before repeating a change.")
    return result


# --------------------------------------------------------------------------
# .notdef check and warning (v0.10)
#
# Every font must have a .notdef glyph as glyph 0; the OpenType spec recommends that it has a visible outline (a rectangle,
# with or without a question mark or an X), because otherwise a missing character shows as nothing, like a space. A NEW
# FontLab font starts with an EMPTY .notdef, so "empty" is a normal state of a font in progress, not an error.
# The listener decides on positive evidence only (missing / empty); an unreadable .notdef is "unknown", never "empty".
# Real-FontLab basis: an empty .notdef has 0 layers; Arial's drawn .notdef has 1 layer with 2 contours / 8 nodes.
# --------------------------------------------------------------------------

NOTDEF_MEANING = {
    "missing": ("The font has no glyph named .notdef. Every font must have one as glyph 0: it is the glyph shown "
                "when a character is not in the font."),
    "empty": ("The font's .notdef glyph exists but has no outline (no lines or shapes). An empty .notdef is technically "
              "valid but not recommended: a missing character then shows as nothing, like a space. The OpenType "
              "specification recommends a rectangle, with or without a question mark or an X inside."),
    "has_outline": "The font's .notdef glyph has an outline.",
    "unknown": "Whether .notdef is missing or empty could not be determined.",
}


def _notdef_auto_enabled() -> bool:
    """GLYPHBRIDGE_NOTDEF_WARN=0 switches off the AUTOMATIC checks inside get_current_font and get_glyph_outline."""
    return os.environ.get("GLYPHBRIDGE_NOTDEF_WARN", "1") != "0"


def _notdef_summary(data: dict) -> dict:
    status = data.get("status")
    if status not in NOTDEF_MEANING:
        raise ToolError("The listener's .notdef reply was malformed, so it was not trusted.")
    out = {"status": status, "meaning": NOTDEF_MEANING[status]}
    for key in ("evidence", "notes"):
        val = data.get(key)
        if isinstance(val, list) and val:
            out[key] = [str(v) for v in val]
    return out


def _notdef_instruction(out: dict):
    status = out.get("status")
    if status in ("missing", "empty"):
        what = "missing" if status == "missing" else "empty (it has no lines or shapes)"
        if out.get("dialog_shown"):
            return (f"A dialog explaining this was just shown to the user in FontLab. Also tell the user in your reply "
                    f"that the .notdef glyph is {what}, and what .notdef is for. Do not present it as an error.")
        if out.get("already_warned"):
            return ("The user was already shown the warning dialog earlier in this session (it is shown once per "
                    "font). Mention it again only if it is relevant.")
        if out.get("dialog_error"):
            return (f"The warning dialog could NOT be shown ({out['dialog_error']}). Tell the user in your reply that "
                    f"the .notdef glyph is {what}, and what .notdef is for.")
        return f"Tell the user in your reply that the .notdef glyph is {what}, and what .notdef is for."
    if status == "unknown":
        return ("Do not tell the user that .notdef is missing or empty: it could not be determined (see 'evidence').")
    return None


def read_notdef_status() -> dict:
    """Read-only .notdef check (GET). Never shows a dialog."""
    data = _call_listener("/font/notdef")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    return _notdef_summary(data)


def check_notdef_glyph() -> dict:
    """Check .notdef and, if it is missing or empty, make FontLab show the warning dialog (once per font per session)."""
    data = _call_listener("/font/notdef")
    if not data.get("open"):
        raise ToolError(NO_FONT)
    out = _notdef_summary(data)
    if out["status"] in ("missing", "empty"):
        # This call blocks until a person clicks OK in FontLab, so it needs the long timeout (like delete).
        warn = _call_listener_post("/font/notdef/warn", {}, timeout=NOTDEF_DIALOG_TIMEOUT_SECONDS)
        if not warn.get("open"):
            raise ToolError(NO_FONT)
        fresh = warn.get("status")
        if fresh in NOTDEF_MEANING and fresh != out["status"]:
            # the listener re-checks before showing anything; trust its fresh answer if .notdef changed in between
            out = _notdef_summary({"status": fresh, "evidence": warn.get("evidence")})
            out.setdefault("notes", []).append("The status changed between the two reads; the later one is reported.")
        out["dialog_shown"] = bool(warn.get("dialog_shown"))
        out["already_warned"] = bool(warn.get("already_warned"))
        if warn.get("dialog_error"):
            out["dialog_error"] = str(warn["dialog_error"])
    instruction = _notdef_instruction(out)
    if instruction:
        out["agent_instruction"] = instruction
    return out


def _notdef_check_best_effort() -> dict:
    """Used by the AUTOMATIC checks: a failure here must never make the tool that called it fail."""
    try:
        return check_notdef_glyph()
    except ToolError as exc:
        return {"status": "check_failed", "detail": str(exc),
                "agent_instruction": ("The automatic .notdef check did not complete, so nothing is known about .notdef. "
                                      "Do not claim it is missing or empty. You may call check_notdef to retry.")}


def read_current_font_checked() -> dict:
    """get_current_font: the font info, plus the automatic .notdef check (unless GLYPHBRIDGE_NOTDEF_WARN=0)."""
    font = read_current_font()
    if _notdef_auto_enabled():
        font["notdef"] = _notdef_check_best_effort()
    return font



# --------------------------------------------------------------------------
# Outline analysis (pure functions: no MCP SDK, no network - unit-testable)
#
# The listener reports raw FontLab facts: every node's x, y, kind, smooth,
# plus FontLab's OWN bounding box of the layer (box around all nodes,
# handles included), and its own left/right margins (computed from the CURVE
# extremes). This code interprets them. It never presents coordinates as
# trustworthy unless FontLab's own numbers agree with them.
#
# Facts confirmed against a real FontLab 8.4 session:
#   kind "Move"  = first (on-curve) node of a contour
#   kind "On"    = on-curve node; "On" right after an on-curve node = line
#   kind "Curve" = cubic handle; exactly two between on-curve nodes
#   kind "Off"   = quadratic (TrueType-style) off-curve point; runs of any
#                  length, with an implied on-curve point at the midpoint of
#                  each consecutive pair
#   A FontLab ELEMENT (shape) can carry its own transformation: position X/Y,
#   horizontal and vertical scale, rotation and slant (shown by the Element
#   selection tool; the Contour selection tool does not show it). Node
#   coordinates read through the node API are element-LOCAL, i.e. WITHOUT that
#   transformation, whereas FontLab's bounding box, margins and screen drawing
#   include it. (Found on testglyph1: element X 15, Y 24, scale 95% / 97%,
#   rotation 0, slant 0 -- exactly the offsets and scales that were inferred
#   from the bounding box.) This is NOT caused by curve-type conversions.
#   The calibration below can only model position and scale per axis; it does
#   NOT model rotation or slant, and assumes ONE transform for the whole glyph
#   (a single element). Both limits are enforced/declared in the verdict.
# --------------------------------------------------------------------------

BBOX_TOLERANCE = 0.05      # font units: raw node box vs FontLab's box
MARGIN_TOLERANCE = 0.05    # font units: reconstructed curve edge vs FontLab margin
_CURVE_SAMPLES = 400       # points per curve piece, for extremes and area


def _fmt(v: float) -> str:
    text = f"{v:.3f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _contour_segments(nodes: list) -> list:
    """Split one closed contour (first node kind 'Move') into
    (start_node, [off_nodes], end_node) triples, closing back to the start."""
    if not nodes or str(nodes[0].get("kind")).lower() != "move":
        raise ValueError("contour does not start with a 'Move' node")
    segments, cur, offs = [], nodes[0], []
    for node in nodes[1:]:
        kind = str(node.get("kind")).lower()
        if kind in ("on", "move"):
            segments.append((cur, offs, node))
            cur, offs = node, []
        elif kind in ("curve", "off"):
            offs.append(node)
        else:
            raise ValueError(f"unknown node kind {node.get('kind')!r} at node {node.get('index')}")
    segments.append((cur, offs, nodes[0]))   # closing segment back to the start
    return segments


def _segment_pieces(start, offs, end) -> list:
    """Turn one segment into drawing pieces: ('L',p0,p1), ('C',p0,c1,c2,p1)
    or ('Q',p0,c,p1). All points are (x, y) tuples in the nodes' own space."""
    p0 = (start["x"], start["y"])
    p1 = (end["x"], end["y"])
    if not offs:
        return [] if p0 == p1 else [("L", p0, p1)]
    kinds = {str(o.get("kind")).lower() for o in offs}
    pts = [(o["x"], o["y"]) for o in offs]
    if kinds == {"curve"}:
        if len(pts) != 2:
            raise ValueError(f"cubic segment with {len(pts)} handle(s) (expected 2) near node {start.get('index')}")
        return [("C", p0, pts[0], pts[1], p1)]
    if kinds == {"off"}:
        pieces = []
        a = p0
        for i, c in enumerate(pts):
            b = p1 if i == len(pts) - 1 else _mid(c, pts[i + 1])
            pieces.append(("Q", a, c, b))
            a = b
        return pieces
    raise ValueError(f"segment mixes cubic and quadratic handles near node {start.get('index')}")


def _sample_piece(piece) -> list:
    kind = piece[0]
    if kind == "L":
        return [piece[1], piece[2]]
    pts = []
    n = _CURVE_SAMPLES
    for i in range(n + 1):
        t = i / n
        u = 1.0 - t
        if kind == "C":
            _, p0, c1, c2, p1 = piece
            x = u**3 * p0[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t**3 * p1[0]
            y = u**3 * p0[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t**3 * p1[1]
        else:
            _, p0, c, p1 = piece
            x = u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0]
            y = u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1]
        pts.append((x, y))
    return pts


def _svg_path(start_pt, pieces) -> str:
    parts = [f"M {_fmt(start_pt[0])} {_fmt(start_pt[1])}"]
    for pc in pieces:
        if pc[0] == "L":
            parts.append(f"L {_fmt(pc[2][0])} {_fmt(pc[2][1])}")
        elif pc[0] == "C":
            parts.append("C " + " ".join(f"{_fmt(p[0])} {_fmt(p[1])}" for p in (pc[2], pc[3], pc[4])))
        else:
            parts.append("Q " + " ".join(f"{_fmt(p[0])} {_fmt(p[1])}" for p in (pc[2], pc[3])))
    parts.append("Z")
    return " ".join(parts)


def _box(points: list) -> dict:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {"left": min(xs), "right": max(xs), "bottom": min(ys), "top": max(ys)}


def _round_box(b: dict) -> dict:
    return {k: _tidy_number(round(v, 3)) for k, v in b.items()}


def _axis_calibration(raw_lo, raw_hi, fl_lo, fl_hi):
    """Per-axis map raw -> FontLab's view, from the two box edges. Returns
    (scale, offset, applied). Identity when the boxes already agree."""
    if abs(raw_lo - fl_lo) <= BBOX_TOLERANCE and abs(raw_hi - fl_hi) <= BBOX_TOLERANCE:
        return 1.0, 0.0, False
    span = raw_hi - raw_lo
    if abs(span) < 1e-9:
        return 1.0, fl_lo - raw_lo, True       # degenerate span: shift only
    scale = (fl_hi - fl_lo) / span
    return scale, fl_lo - scale * raw_lo, True



# --------------------------------------------------------------------------
# DIRECT route: the TRUE element transforms read from FontLab (listener >= 0.45)
#
# FontLab exposes each shape's transformation as a Qt matrix. Qt convention:
#     x' = m11*x + m21*y + dx        y' = m12*x + m22*y + dy
# (confirmed on real data: a 10 degree slant arrives as m21 = tan(10 deg) = 0.17633,
#  scale 95.1% / 96.9% with offset (15, 24) arrives as m11, m22, dx, dy).
# This handles everything the estimate cannot: rotation, slant, mirroring (a mirrored
# glyph keeps the same bounding box and margins, so only the matrix reveals it), and
# one transform per element. The result is still cross-checked against FontLab's own
# bounding box and margins; if anything disagrees we return None and the caller falls
# back to the estimating route, with a note that says why.
# --------------------------------------------------------------------------

_MATRIX_KEYS = ("m11", "m12", "m21", "m22", "dx", "dy")


def _shape_matrix(shape: dict):
    m = shape.get("matrix")
    if not isinstance(m, dict):
        return None
    try:
        return tuple(float(m[k]) for k in _MATRIX_KEYS)
    except (KeyError, TypeError, ValueError):
        return None


def _is_identity(mx, eps: float = 1e-9) -> bool:
    return (abs(mx[0] - 1) < eps and abs(mx[3] - 1) < eps and abs(mx[1]) < eps
            and abs(mx[2]) < eps and abs(mx[4]) < eps and abs(mx[5]) < eps)


def _describe_matrix(mx) -> str:
    m11, m12, m21, m22, dx, dy = mx
    eps = 1e-6
    if _is_identity(mx, eps):
        return "identity (no transformation)"
    parts = []
    if abs(m12) < eps and abs(m21) < eps:
        parts.append(f"scale {m11 * 100:.2f}% horizontally, {m22 * 100:.2f}% vertically")
        if m11 < 0:
            parts.append("MIRRORED horizontally")
        if m22 < 0:
            parts.append("MIRRORED vertically")
    elif abs(m12) < eps and abs(m11 - 1) < eps and abs(m22 - 1) < eps:
        parts.append(f"horizontal slant {math.degrees(math.atan(m21)):.2f} degrees (shear {m21:.5f})")
    else:
        parts.append(f"general transformation: rotation about {math.degrees(math.atan2(m12, m11)):.2f} degrees, "
                     f"matrix [{m11:.5f} {m12:.5f} {m21:.5f} {m22:.5f}]")
    if abs(dx) > eps or abs(dy) > eps:
        parts.append(f"offset ({dx:g}, {dy:g})")
    return "; ".join(parts)


def _apply_matrix(mx, x, y):
    return mx[0] * x + mx[2] * y + mx[4], mx[1] * x + mx[3] * y + mx[5]


def _build_contours_with_matrices(contours_in: list, matrices: list):
    """Like the estimating route's rebuild(), but every contour gets its OWN full
    matrix. Returns (contours, sampled_points, all_ok, notes)."""
    built, points, all_ok, local_notes = [], [], True, []
    for ci, c in enumerate(contours_in):
        mx = matrices[ci]
        ident = _is_identity(mx)
        raw_nodes = c.get("nodes", [])
        nodes, cal_nodes = [], []
        for n in raw_nodes:
            x, y = _apply_matrix(mx, n["x"], n["y"])
            entry = {"index": n.get("index"), "x": _tidy_number(round(x, 3)), "y": _tidy_number(round(y, 3)),
                     "kind": n.get("kind")}
            if str(n.get("kind")).lower() in ("move", "on"):
                entry["smooth"] = bool(n.get("smooth"))
            if not ident:
                entry["raw_x"] = _tidy_number(round(n["x"], 3))
                entry["raw_y"] = _tidy_number(round(n["y"], 3))
            nodes.append(entry)
            cal_nodes.append({"index": n.get("index"), "kind": n.get("kind"), "x": x, "y": y})
        kinds = {str(n.get("kind")).lower() for n in raw_nodes}
        curve_type = ("cubic" if "curve" in kinds and "off" not in kinds else
                      "quadratic" if "off" in kinds and "curve" not in kinds else
                      "mixed" if "off" in kinds and "curve" in kinds else "lines only")
        info = {"index": ci, "curve_type": curve_type, "nodes": nodes,
                "on_curve_count": sum(1 for n in raw_nodes if str(n.get("kind")).lower() in ("move", "on")),
                "off_curve_count": sum(1 for n in raw_nodes if str(n.get("kind")).lower() in ("curve", "off"))}
        try:
            pieces = []
            for st, offs, en in _contour_segments(cal_nodes):
                pieces.extend(_segment_pieces(st, offs, en))
            pts = []
            for pc in pieces:
                pts.extend(_sample_piece(pc))
            if not pts:
                raise ValueError("contour has no drawable segments")
            info["bbox"] = _round_box(_box(pts))
            area = 0.0
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                area += x1 * y2 - x2 * y1
            info["direction"] = "counterclockwise" if area > 0 else "clockwise" if area < 0 else "degenerate"
            info["svg_path"] = _svg_path((cal_nodes[0]["x"], cal_nodes[0]["y"]), pieces)
            points.extend(pts)
        except ValueError as exc:
            all_ok = False
            info["reconstruction_error"] = str(exc)
            local_notes.append(f"Contour {ci} could not be reconstructed: {exc}")
        built.append(info)
    return built, points, all_ok, local_notes


def _analyze_with_elements(data: dict):
    """Try the direct route. Returns (result, None) on success or (None, reason_or_None)
    when the caller must use the estimating route. reason is None when elements were
    simply not offered (older listener / modern API switched off)."""
    el = data.get("elements")
    if not isinstance(el, dict):
        return None, None
    if not el.get("available"):
        err = el.get("error")
        if err and "disabled" not in str(err):
            return None, (f"FontLab's element transforms could not be read ({err}); the transformation was "
                          "estimated from FontLab's bounding box instead.")
        return None, None
    shapes = el.get("shapes")
    contours_in = data.get("contours") or []
    if not isinstance(shapes, list) or not shapes or not contours_in:
        return None, "FontLab reported no usable element list; the transformation was estimated instead."
    if any(sh.get("is_component") for sh in shapes):
        return None, ("A shape is a component reference, which this tool does not follow; "
                      "the transformation was estimated instead.")
    counts = [sh.get("contours") for sh in shapes]
    mats = [_shape_matrix(sh) for sh in shapes]
    if not all(isinstance(c, int) and c >= 0 for c in counts) or any(m is None for m in mats):
        return None, "FontLab's element data was incomplete; the transformation was estimated instead."
    if sum(counts) != len(contours_in):
        return None, (f"FontLab lists {sum(counts)} contour(s) across its elements but {len(contours_in)} were read; "
                      "the contour-to-element mapping is unclear, so the transformation was estimated instead.")
    matrices = []
    for m, c in zip(mats, counts):
        matrices.extend([m] * c)

    fl_box = data.get("fontlab_bbox")
    margins = data.get("margins") or {}
    if not (isinstance(fl_box, dict) and "error" not in fl_box and
            all(isinstance(fl_box.get(k), (int, float)) for k in ("left", "right", "top", "bottom"))):
        return None, ("FontLab's bounding box was unavailable, so the element transforms could not be confirmed; "
                      "estimated instead.")
    if not all(isinstance(margins.get(k), (int, float)) for k in ("left", "right", "width")):
        return None, ("FontLab's margins were unavailable, so the element transforms could not be confirmed; "
                      "estimated instead.")

    out_contours, ink_points, ok, build_notes = _build_contours_with_matrices(contours_in, matrices)
    if not ok or not ink_points:
        return None, "The outline could not be rebuilt with FontLab's element transforms; estimated instead."

    transformed_nodes = [_apply_matrix(matrices[ci], n["x"], n["y"])
                         for ci, c in enumerate(contours_in) for n in c.get("nodes", [])]
    raw_box = _box([(n["x"], n["y"]) for c in contours_in for n in c.get("nodes", [])])
    tbox = _box(transformed_nodes)
    fbox = {k: float(fl_box[k]) for k in ("left", "right", "bottom", "top")}
    box_ok = all(abs(tbox[k] - fbox[k]) <= BBOX_TOLERANCE for k in ("left", "right", "bottom", "top"))
    ink_box = _box(ink_points)
    left_here = ink_box["left"]
    right_here = margins["width"] - ink_box["right"]
    margin_ok = (abs(left_here - margins["left"]) <= MARGIN_TOLERANCE
                 and abs(right_here - margins["right"]) <= MARGIN_TOLERANCE)
    if not (box_ok and margin_ok):
        return None, ("FontLab's element transforms were read but did not reproduce FontLab's own "
                      f"{'bounding box' if not box_ok else 'margins'}; the transformation was estimated instead.")

    elements = []
    for si, (sh, m) in enumerate(zip(shapes, mats)):
        elements.append({
            "index": si, "contours": counts[si], "shape_type": sh.get("shape_type"),
            "is_composite": bool(sh.get("is_composite")),
            "matrix": {k: _tidy_number(round(v, 6)) for k, v in zip(_MATRIX_KEYS, m)},
            "description": _describe_matrix(m),
        })
    notes = list(build_notes)
    notes.append("Contours are assumed closed (open contours have not been verified against FontLab).")
    comp = data.get("component_count")
    if comp:
        notes.append(f"This glyph contains {comp} component(s). Their outlines are NOT included here; "
                     "only the glyph's own contours were read.")
    if len(shapes) > 1:
        notes.append(f"This glyph has {len(shapes)} elements. Contours were assigned to elements in the order FontLab "
                     "lists them (the confirmation is that the combined result matches FontLab's own bounding box "
                     "and margins).")
    if any(e["is_composite"] for e in elements):
        notes.append("At least one element is flagged composite (for example a Power Brush stroke); only the glyph's "
                     "own contours were read, not any skeleton or stroke settings behind them.")
    if all(_is_identity(m) for m in mats):
        space = "FontLab view (FontLab reports no element transformation, so these are the raw node coordinates)"
    else:
        space = ("FontLab view (the real element transformation read from FontLab has been applied; matches what is "
                 "drawn on screen and FontLab's X/Y readouts). Original element-local values are in raw_x / raw_y.")
        notes.append("Non-identity element transformation: " + "; ".join(
            f"element {e['index']}: {e['description']}" for e in elements
            if e["description"] != "identity (no transformation)"))
    return {
        "name": data.get("name"),
        "advance_width": _tidy_number(margins.get("width")),
        "contour_count": len(contours_in),
        "node_count": sum(len(c.get("nodes", [])) for c in contours_in),
        "coordinate_space": space,
        "verification": {
            "status": "verified",
            "transform_source": "FontLab's own element transform, read directly (not estimated)",
            "bounding_box_check": {"raw_node_box": _round_box(raw_box), "transformed_node_box": _round_box(tbox),
                                   "fontlab_box": _round_box(fbox), "agrees": True},
            "margin_check": {"fontlab_left_margin": margins["left"], "fontlab_right_margin": margins["right"],
                             "advance_width": margins["width"],
                             "reconstructed_left_margin": round(left_here, 3),
                             "reconstructed_right_margin": round(right_here, 3), "agrees": True},
        },
        "elements": elements,
        "ink_bbox": _round_box(ink_box),
        "contours": out_contours,
        "notes": notes,
    }, None


def analyze_outline(data: dict) -> dict:
    """Interpret the listener's /glyph/outline reply. Never raises for
    odd-but-readable data; problems are reported in 'notes' and by a
    verification status of 'unverified'. Tries the DIRECT route first (FontLab's
    own element transforms); falls back to estimating the transform."""
    direct, direct_note = _analyze_with_elements(data)
    if direct is not None:
        return direct
    notes: list = [direct_note] if direct_note else []
    contours_in = data.get("contours") or []
    all_nodes = [n for c in contours_in for n in c.get("nodes", [])]
    name = data.get("name")

    if data.get("contour_count_reported") != data.get("contour_count_grouped"):
        notes.append(
            f"FontLab reports {data.get('contour_count_reported')} contour(s) but "
            f"{data.get('contour_count_grouped')} were found by 'Move' markers; treat the outline as unreliable."
        )
    shapes = data.get("shape_count")
    comp = data.get("component_count")
    if comp:
        notes.append(
            f"This glyph contains {comp} component(s). Their outlines are NOT included here; "
            "only the glyph's own contours were read."
        )
    notes.append("Contours are assumed closed (open contours have not been verified against FontLab).")

    raw_box = _box([(n["x"], n["y"]) for n in all_nodes])

    # ---- 1. compare the raw node box with FontLab's own box ----------------
    fl_box = data.get("fontlab_bbox")
    bbox_check: dict = {"raw_node_box": _round_box(raw_box)}
    sx = sy = 1.0
    bx = by = 0.0
    applied_x = applied_y = False
    bbox_ok_known = isinstance(fl_box, dict) and "error" not in fl_box and all(
        isinstance(fl_box.get(k), (int, float)) for k in ("left", "right", "top", "bottom"))
    if bbox_ok_known:
        bbox_check["fontlab_box"] = _round_box({k: float(fl_box[k]) for k in ("left", "right", "bottom", "top")})
        sx, bx, applied_x = _axis_calibration(raw_box["left"], raw_box["right"], fl_box["left"], fl_box["right"])
        sy, by, applied_y = _axis_calibration(raw_box["bottom"], raw_box["top"], fl_box["bottom"], fl_box["top"])
        bbox_check["agrees"] = not (applied_x or applied_y)
    else:
        bbox_check["agrees"] = None
        notes.append(
            "FontLab's own bounding box could not be read"
            + (f" ({fl_box.get('error')})" if isinstance(fl_box, dict) and fl_box.get("error") else "")
            + ", so the coordinates could not be checked against FontLab's geometry."
        )
    calibrated = applied_x or applied_y

    def rebuild(sx_, bx_, sy_, by_, annotate_raw):
        """Build the output contours with the given per-axis correction
        (identity = raw element-local coordinates). Returns
        (contours, sampled_points, all_ok, notes)."""
        def cal(x, y):
            return sx_ * x + bx_, sy_ * y + by_

        built: list = []
        points: list = []
        all_ok = True
        local_notes: list = []
        for ci, c in enumerate(contours_in):
            raw_nodes = c.get("nodes", [])
            nodes = []
            for n in raw_nodes:
                x, y = cal(n["x"], n["y"])
                entry = {"index": n.get("index"), "x": _tidy_number(round(x, 3)), "y": _tidy_number(round(y, 3)),
                         "kind": n.get("kind")}
                if str(n.get("kind")).lower() in ("move", "on"):
                    entry["smooth"] = bool(n.get("smooth"))
                if annotate_raw:
                    entry["raw_x"] = _tidy_number(round(n["x"], 3))
                    entry["raw_y"] = _tidy_number(round(n["y"], 3))
                nodes.append(entry)
            cal_nodes = [{"index": n.get("index"), "kind": n.get("kind"),
                          "x": cal(n["x"], n["y"])[0], "y": cal(n["x"], n["y"])[1]} for n in raw_nodes]
            kinds = {str(n.get("kind")).lower() for n in raw_nodes}
            curve_type = ("cubic" if "curve" in kinds and "off" not in kinds else
                          "quadratic" if "off" in kinds and "curve" not in kinds else
                          "mixed" if "off" in kinds and "curve" in kinds else "lines only")
            info = {"index": ci, "curve_type": curve_type, "nodes": nodes,
                    "on_curve_count": sum(1 for n in raw_nodes if str(n.get("kind")).lower() in ("move", "on")),
                    "off_curve_count": sum(1 for n in raw_nodes if str(n.get("kind")).lower() in ("curve", "off"))}
            try:
                pieces = []
                for st, offs, en in _contour_segments(cal_nodes):
                    pieces.extend(_segment_pieces(st, offs, en))
                pts = []
                for pc in pieces:
                    pts.extend(_sample_piece(pc))
                if not pts:
                    raise ValueError("contour has no drawable segments")
                info["bbox"] = _round_box(_box(pts))
                area = 0.0
                for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                    area += x1 * y2 - x2 * y1
                info["direction"] = "counterclockwise" if area > 0 else "clockwise" if area < 0 else "degenerate"
                info["svg_path"] = _svg_path((cal_nodes[0]["x"], cal_nodes[0]["y"]), pieces)
                points.extend(pts)
            except ValueError as exc:
                all_ok = False
                info["reconstruction_error"] = str(exc)
                local_notes.append(f"Contour {ci} could not be reconstructed: {exc}")
            built.append(info)
        return built, points, all_ok, local_notes

    # ---- 2. rebuild each contour in FontLab's view (tentatively calibrated) -
    out_contours, ink_points, reconstruct_ok, build_notes = rebuild(sx, bx, sy, by, calibrated)
    notes.extend(build_notes)

    ink_box = _box(ink_points) if ink_points and reconstruct_ok else None

    # ---- 3. check the rebuilt curve edges against FontLab's own margins ----
    margins = data.get("margins") or {}
    margin_check: dict = {"fontlab_left_margin": margins.get("left"), "fontlab_right_margin": margins.get("right"),
                          "advance_width": margins.get("width")}
    margin_ok = None
    if ink_box and all(isinstance(margins.get(k), (int, float)) for k in ("left", "right", "width")):
        left_here = ink_box["left"]
        right_here = margins["width"] - ink_box["right"]
        margin_check["reconstructed_left_margin"] = round(left_here, 3)
        margin_check["reconstructed_right_margin"] = round(right_here, 3)
        margin_ok = (abs(left_here - margins["left"]) <= MARGIN_TOLERANCE
                     and abs(right_here - margins["right"]) <= MARGIN_TOLERANCE)
        margin_check["agrees"] = margin_ok
    else:
        margin_check["agrees"] = None
        notes.append("The margin cross-check could not be done (missing margins or unreconstructable contour).")

    # ---- 4. verdict --------------------------------------------------------
    multi_element = isinstance(shapes, int) and shapes > 1
    if not bbox_ok_known or margin_ok is not True:
        status = "unverified"
        notes.append("Coordinates are NOT confirmed against FontLab's own geometry; do not rely on them for exact work.")
        if calibrated and margin_ok is False:
            notes.append(
                "FontLab's bounding box differs from the raw node box, and a plain per-axis scale-and-shift correction "
                "did not reproduce FontLab's own margins. The glyph's element probably carries a transformation this "
                "tool cannot model yet (for example rotation or slant). FontLab's Element selection tool shows it."
            )
    elif calibrated and multi_element:
        status = "unverified"
        notes.append(
            f"This glyph has {shapes} elements and its coordinates differ from FontLab's geometry. Each element can "
            "have its own transformation (position, scale, rotation, slant), but only one glyph-wide correction can "
            "be estimated, so the corrected coordinates are NOT trustworthy."
        )
    elif calibrated:
        status = "calibrated"
        notes.append(
            "FontLab applies a transformation to this glyph's element (position and scale; set with FontLab's "
            "Element selection tool) that the raw node coordinates do not include. Every coordinate below (x, y) has "
            "been mapped into FontLab's view, i.e. what is drawn on screen and shown in FontLab's X/Y readouts. "
            "Original element-local values are in raw_x / raw_y."
        )
        if shapes is None:
            notes.append("The number of elements could not be read; a single element transform was assumed.")
        notes.append(
            "The correction assumes the element has NO rotation or slant. If it does, the corrected coordinates "
            "would be wrong; the horizontal margin cross-check above passed, which makes that unlikely here."
        )
    else:
        status = "verified"
    if calibrated and applied_y:
        notes.append(
            "The vertical calibration comes from FontLab's bounding box only; FontLab offers no vertical "
            "margin to cross-check it (the horizontal one was cross-checked)."
        )
    if status == "unverified" and calibrated:
        # Do not present unconfirmed corrected numbers as the glyph's coordinates: fall back to the raw values.
        out_contours, ink_points, _ok, _n = rebuild(1.0, 0.0, 1.0, 0.0, False)
        ink_box = _box(ink_points) if ink_points and reconstruct_ok else None
        coordinate_space = ("element-local RAW coordinates (what the node API returns). They do NOT include the "
                            "element transformation FontLab applies, so they differ from FontLab's displayed positions.")
        notes.append(
            "x / y below are the RAW element-local values because the attempted correction could not be confirmed; "
            "FontLab's own box of the displayed glyph is in verification.bounding_box_check.fontlab_box."
        )
    elif status == "calibrated":
        coordinate_space = "FontLab view (calibrated from FontLab's bounding box; matches what is drawn on screen)"
    elif status == "verified":
        coordinate_space = "FontLab view (raw coordinates agree with FontLab's own geometry)"
    else:
        coordinate_space = "raw node coordinates, NOT confirmed against FontLab's geometry"
    verification = {"status": status, "bounding_box_check": bbox_check, "margin_check": margin_check}
    if calibrated:
        verification["calibration" if status == "calibrated" else "attempted_calibration_NOT_applied"] = {
            "x": {"scale": round(sx, 5), "offset": round(bx, 3), "applied": applied_x},
            "y": {"scale": round(sy, 5), "offset": round(by, 3), "applied": applied_y},
            "meaning": "FontLab_value = scale * raw_value + offset",
            "as_element_transform": {
                "position_x": round(bx, 3), "position_y": round(by, 3),
                "horizontal_scale_percent": round(sx * 100, 2), "vertical_scale_percent": round(sy * 100, 2),
                "rotation_and_slant": "assumed 0 (not measurable here)",
                "compare_with": "FontLab's Element selection tool transform bar",
            },
        }

    return {
        "name": name,
        "advance_width": _tidy_number(margins.get("width")) if margins.get("width") is not None else None,
        "contour_count": len(contours_in),
        "node_count": len(all_nodes),
        "coordinate_space": coordinate_space,
        "verification": verification,
        "ink_bbox": _round_box(ink_box) if ink_box else None,
        "contours": out_contours,
        "notes": notes,
    }


def _signed_area(points: list) -> float:
    """Shoelace sum / 2 for points in y-up font units: positive = counter-clockwise, negative = clockwise."""
    total = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        total += x1 * y2 - x2 * y1
    return total / 2.0


_CURVE_BOX_TOLERANCE = 0.05       # font units: computed cubic extents vs FontLab's own modern margins


def _cubic_extremes(p0, p1, p2, p3) -> list:
    """The points of one cubic Bezier segment where x or y is extreme (roots of the derivative inside 0 < t < 1)."""
    out = []
    for axis in (0, 1):
        a0, a1, a2, a3 = p0[axis], p1[axis], p2[axis], p3[axis]
        qa = (a1 - a0) - 2 * (a2 - a1) + (a3 - a2)
        qb = 2 * ((a2 - a1) - (a1 - a0))
        qc = a1 - a0
        roots = []
        if abs(qa) < 1e-12:
            if abs(qb) > 1e-12:
                roots.append(-qc / qb)
        else:
            disc = qb * qb - 4 * qa * qc
            if disc >= 0:
                sq = disc ** 0.5
                roots.extend(((-qb + sq) / (2 * qa), (-qb - sq) / (2 * qa)))
        for t in roots:
            if 0.0 < t < 1.0:
                u = 1.0 - t
                out.append(tuple(u ** 3 * p0[i] + 3 * u * u * t * p1[i] + 3 * u * t * t * p2[i] + t ** 3 * p3[i] for i in (0, 1)))
    return out


def _cubic_contour_pieces(nodes: list, closed: Any):
    """(start point, pieces) of ONE closed contour made of straight and cubic segments, or None when it is anything else (open, quadratic
    off-curve points, a run of handles that is not exactly two, no on-curve node). nodes: dicts with x, y, on (bool), curve (bool).
    The closing segment may have its handles at the END of the list (how FontLab stores them)."""
    if closed is not True or not nodes:
        return None
    start_i = next((i for i, n in enumerate(nodes) if n["on"]), None)
    if start_i is None:
        return None
    seq = nodes[start_i:] + nodes[:start_i]
    start = (seq[0]["x"], seq[0]["y"])
    pieces, cur, pend = [], start, []
    for nd in seq[1:] + [seq[0]]:
        pt = (nd["x"], nd["y"])
        if not nd["on"]:
            if not nd["curve"]:
                return None                    # quadratic off-curve point
            pend.append(pt)
            continue
        if not pend:
            pieces.append(("L", cur, pt))
        elif len(pend) == 2:
            pieces.append(("C", cur, pend[0], pend[1], pt))
        else:
            return None
        cur, pend = pt, []
    return start, pieces


def _modern_outline_result(clean: str, mo: dict, mc: dict, data: dict) -> dict:
    """The outline as read from FontLab's modern layer (the legacy reader is blind or stale for this glyph)."""
    stale_margins = isinstance(mc, dict) and mc.get("agree") is not False and mc.get("margins_agree") is False
    contours_out, on_points, notes = [], [], []
    has_curves, disagree = False, []
    exact_ok, curve_problems, curve_boxes = True, [], []
    for c in mo["contours"]:
        # kind: On = on-curve; Curve = cubic control point (FontLab: not on-curve, isCurve); Off = quadratic off-curve point
        nodes = [{"x": _tidy_number(n["x"]), "y": _tidy_number(n["y"]),
                  "kind": "On" if n.get("isOn") else ("Curve" if n.get("isCurve") else "Off"),
                  "curve": bool(n.get("isCurve")), "smooth": bool(n.get("smooth"))} for n in c["nodes"]]
        n_cubic = sum(1 for n in nodes if n["kind"] == "Curve")
        n_quad = sum(1 for n in nodes if n["kind"] == "Off")
        curve_type = "none" if not (n_cubic or n_quad) else "cubic" if not n_quad else "quadratic" if not n_cubic else "mixed"
        pts = [(n["x"], n["y"]) for n in c["nodes"] if n.get("isOn")]
        curved = any((not n.get("isOn")) or n.get("isCurve") for n in c["nodes"])
        has_curves = has_curves or curved
        on_points.extend(pts)
        area = _signed_area(pts) if len(pts) >= 3 else 0.0
        computed = "counterclockwise" if area > 0 else "clockwise" if area < 0 else "undetermined"
        flag = c.get("clockwise")
        # live (two glyphs, both ways round): FontLab's flag is True for a counterclockwise contour (y up) and False for a clockwise one
        inverted = None if computed == "undetermined" or not isinstance(flag, bool) else (flag == (computed == "counterclockwise"))
        if inverted is False:
            disagree.append(c.get("index"))
        entry = {"index": c.get("index"), "closed": c.get("closed"), "node_count": len(nodes), "curve_type": curve_type,
                 "clockwise_reported": flag, "direction_computed": computed, "flag_follows_known_inversion": inverted, "node_list": nodes}
        if not curved and c.get("closed") is True and nodes:
            entry["svg_path"] = "M " + " L ".join(f"{n['x']} {n['y']}" for n in nodes) + " Z"
        elif curve_type == "cubic":
            parsed = _cubic_contour_pieces([{"x": n["x"], "y": n["y"], "on": bool(n.get("isOn")), "curve": bool(n.get("isCurve"))}
                                            for n in c["nodes"]], c.get("closed"))
            if parsed is None:
                exact_ok = False
                curve_problems.append(f"contour {c.get('index')}: the cubic segments could not be told apart (a run of control points that is not exactly two, or an open contour)")
            else:
                entry["svg_path"] = _svg_path(parsed[0], parsed[1])
                curve_boxes.append(parsed)
        else:
            exact_ok = False
            curve_problems.append(f"contour {c.get('index')}: {curve_type} curve nodes; only cubic segments are evaluated")
        contours_out.append(entry)
    notes.append("direction_computed is the geometric direction in y-up font units (counterclockwise = positive area). FontLab's own clockwise flag "
                 "(clockwise_reported) reads the opposite way round on the contours tested live (a counterclockwise contour shows true); it is "
                 "listed for reference only. In the cubic test font the outer contour of FontLab's own glyph A is counterclockwise.")
    if disagree:
        notes.append(f"WARNING: for contour(s) {disagree} FontLab's clockwise flag does NOT show the usual inversion: check the direction "
                     "before relying on direction_computed.")
    if stale_margins:
        leg_m = mc.get("legacy_margins") if isinstance(mc.get("legacy_margins"), dict) else {}
        mod_m = mc.get("modern_margins") if isinstance(mc.get("modern_margins"), dict) else {}
        notes.append(f"STALE LEGACY VIEW, answered from the modern layer: the legacy reader gives margins {({k: _tidy_number(x) for k, x in leg_m.items()})} but "
                     f"FontLab's modern layer gives {({k: _tidy_number(x) for k, x in mod_m.items()})} (the glyph was probably changed through the API a moment ago). "
                     f"This outline was therefore read from the modern layer ({mo.get('node_count')} node(s)) and is current; no refresh is needed to trust it. "
                     "FontLab's legacy view itself refreshes only when the glyph's editor tab is closed (X) and the glyph reopened from the grid.")
    else:
        notes.append(f"The legacy reader sees {data.get('node_count')} node(s) for this glyph (it lags on glyphs changed through the API), so this "
                     f"outline was read from FontLab's modern layer ({mo.get('node_count')} node(s)).")
    if data.get("component_count"):
        notes.append(f"The glyph has {data['component_count']} component(s), whose outlines are not read by this tool.")
    margins = mo.get("margins") if isinstance(mo.get("margins"), dict) else None
    box = None
    curves_exact = has_curves and exact_ok and bool(curve_boxes)
    if on_points:
        xs, ys = [p[0] for p in on_points], [p[1] for p in on_points]
        if curves_exact:                       # the real extents: on-curve points plus the extremes of every cubic segment
            for start, pieces in curve_boxes:
                for pc in pieces:
                    if pc[0] == "C":
                        for ex in _cubic_extremes(pc[1], pc[2], pc[3], pc[4]):
                            xs.append(ex[0]); ys.append(ex[1])
        box = {"left": min(xs), "right": max(xs), "bottom": min(ys), "top": max(ys)}
    verification = {"status": "unverified", "modern_check": mc}
    if stale_margins:
        verification["legacy_margins_vs_modern"] = {"status": "mismatch", "differs": mc.get("margins_differ"), "legacy": mc.get("legacy_margins"), "modern": mc.get("modern_margins")}
    if margins is None:
        verification["reason"] = "the modern margins could not be read, so the bounding box could not be compared"
    elif box is None:
        verification["reason"] = "the outline has no on-curve points"
    elif has_curves and not curves_exact:
        verification["reason"] = ("the outline has curve nodes whose extents are not computed (" + "; ".join(curve_problems[:3]) +
                                  "); the box of the on-curve points is not the curve extents, so it cannot be compared with the margins")
    else:
        tol = _CURVE_BOX_TOLERANCE if curves_exact else 0.01
        ink = margins["advance"] - margins["lsb"] - margins["rsb"]
        left_ok = abs(box["left"] - margins["lsb"]) < tol
        width_ok = abs((box["right"] - box["left"]) - ink) < tol
        verification["bounding_box_vs_margins"] = {"box_left": _tidy_number(box["left"]), "lsb": _tidy_number(margins["lsb"]),
                                                   "box_width": _tidy_number(box["right"] - box["left"]), "ink_width": _tidy_number(ink),
                                                   "left_ok": left_ok, "width_ok": width_ok}
        if left_ok and width_ok:
            verification["status"] = "verified"
        else:
            verification["reason"] = ("the nodes' bounding box (curve extents included) does not match the modern left sidebearing and ink width"
                                      if curves_exact else "the nodes' bounding box does not match the modern left sidebearing and ink width")
    result = {
        "name": clean,
        "source": "modern layer",
        "coordinate_space": "FontLab view (read from the modern layer with an identity transform; same as FontLab's X/Y readouts, y up)",
        "contour_count": len(contours_out),
        "node_count": mo.get("node_count"),
        "verification": verification,
        "ink_bbox": _round_box(box) if box else None,
        "ink_bbox_exact": (curves_exact or not has_curves) if box else None,
        "contours": contours_out,
        "notes": notes,
    }
    if stale_margins:
        result["legacy_view_was_stale"] = True
    if margins is not None:
        result.update({"left": _tidy_number(margins["lsb"]), "right": _tidy_number(margins["rsb"]),
                       "advance_width": _tidy_number(margins["advance"]),
                       "ink_width": _tidy_number(margins["advance"] - margins["lsb"] - margins["rsb"])})
    return result


_STALE_MARGIN_TOLERANCE = 0.05    # font units: modern sidebearings / advance vs the legacy reader's margins


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v


def _stale_legacy_check(clean: str, data: dict, result: dict, mc: Any) -> None:
    """Legacy route only. The legacy view of a glyph can lag behind FontLab's modern layer after an API write, and its nodes were
    only ever checked against its own (equally stale) margins. Compare the MODERN left / right sidebearing and advance width
    (one extra read-only request) with the legacy margins; a difference means the legacy numbers are stale. Never raises."""
    v = result.get("verification")
    if not isinstance(v, dict) or v.get("status") not in ("verified", "calibrated"):
        return
    if not (isinstance(mc, dict) and mc.get("modern_layer") is True):
        return                                    # no modern layer: nothing to compare with
    try:
        sb = _call_listener(f"/glyph/sidebearings?name={quote(clean)}")
    except Exception as exc:                      # best effort: the main read already succeeded
        v["modern_margins_check"] = {"status": "not_checked", "reason": f"the modern sidebearings could not be read ({exc})"}
        result["notes"].append("Could not cross-check the nodes against FontLab's MODERN margins (that read failed): if the glyph was changed through "
                               "the API a moment ago the legacy numbers may be stale; call get_glyph_sidebearings for the current margins.")
        return
    legacy = data.get("margins") if isinstance(data.get("margins"), dict) else {}
    leg = {"left": legacy.get("left"), "right": legacy.get("right"), "advance_width": legacy.get("width")}
    mod = {"left": sb.get("lsb"), "right": sb.get("rsb"), "advance_width": sb.get("advance")}
    if not sb.get("readable") or not all(_num(x) for x in list(leg.values()) + list(mod.values())):
        why = sb.get("reason") or "the modern or legacy margins are not numbers"
        v["modern_margins_check"] = {"status": "not_checked", "reason": f"the margins could not be compared ({why})"}
        result["notes"].append("Could not cross-check the nodes against FontLab's MODERN margins (they were not readable): the legacy numbers "
                               "may be stale after a recent API change; call get_glyph_sidebearings for the current margins.")
        return
    off = [k for k in ("left", "right", "advance_width") if abs(leg[k] - mod[k]) > _STALE_MARGIN_TOLERANCE]
    tidy = lambda d: {k: _tidy_number(x) for k, x in d.items()}
    if not off:
        v["modern_margins_check"] = {"status": "agrees"}
        return
    v["status"] = "unverified"
    v["modern_margins_check"] = {"status": "mismatch", "differs": off, "legacy": tidy(leg), "modern": tidy(mod)}
    v["reason"] = ("FontLab's legacy view of this glyph disagrees with its modern layer (" + ", ".join(off) + "): the legacy view is stale, "
                   "so the nodes below were NOT confirmed")
    result["stale_legacy_view"] = True
    result["notes"].append(f"STALE LEGACY VIEW: the legacy reader gives margins {tidy(leg)} but FontLab's modern layer gives {tidy(mod)}. The glyph "
                           "was probably changed through the API a moment ago; the coordinates below come from the legacy view and are probably "
                           "OLD. get_glyph_sidebearings reports the current margins. FontLab refreshed its legacy view in a live test only after the glyph's "
                           "editor tab was CLOSED (X) and the glyph reopened from the grid (a plain switch to the grid tab and back did not do it); "
                           "then read the outline again.")


def read_glyph_outline(name: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    modern_off = os.environ.get("GLYPHBRIDGE_MODERN", "1") == "0"
    data = _call_listener(f"/glyph/outline?name={quote(clean)}" + ("&modern=no" if modern_off else ""))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if not data.get("found"):
        raise ToolError(f"No glyph named '{clean}' was found.")
    if data.get("error"):
        if data.get("layer_unreachable"):
            n = data.get("layer_count")
            count_txt = (f"FontLab reports {n} layer(s) for it" if isinstance(n, int)
                         else "FontLab's layer count for it could not be read")
            msg = (f"The outline of '{clean}' could not be read: FontLab did not hand over its layer through the API "
                   f"({data['error']}; {count_txt}). This does NOT mean the glyph is empty - its contents are simply unknown.")
            if clean == ".notdef":
                msg += (" .notdef is a mandatory glyph that every font has (glyph 0); do not report it as missing or empty "
                        "on this basis. Call check_notdef to check it a different way.")
            raise ToolError(msg)
        raise ToolError(f"The outline of '{clean}' could not be read: {data['error']}")
    if not isinstance(data.get("contours"), list) or not isinstance(data.get("node_count"), int):
        raise ToolError("The listener's outline reply was malformed, so it was not trusted.")
    mc = data.get("modern_check") if isinstance(data.get("modern_check"), dict) else None
    mo = data.get("modern_outline") if isinstance(data.get("modern_outline"), dict) else None
    if (mc and (mc.get("agree") is False or mc.get("margins_agree") is False) and mo and mo.get("available") and isinstance(mo.get("contours"), list)):
        return _modern_outline_result(clean, mo, mc, data)
    if data["node_count"] == 0 and mc and mc.get("modern_layer") and isinstance(mc.get("modern_nodes"), int) and mc["modern_nodes"] > 0:
        why = f" Reading it from the modern layer failed too: {mo.get('error')}." if mo and mo.get("error") else ""
        raise ToolError(f"The outline of '{clean}' cannot be read reliably: FontLab's modern view of the glyph holds {mc['modern_nodes']} node(s) "
                        f"in {mc.get('modern_shapes')} shape(s), but the legacy reader this tool uses sees none (it lags on glyphs changed "
                        f"through the API).{why} This does NOT mean the glyph is empty. get_glyph_sidebearings still reports its real margins.")
    if data["node_count"] == 0:
        comp = data.get("component_count")
        extra = (f" It has {comp} component(s), whose outlines are not read by this tool." if comp else "")
        notes = ["This glyph has no contours of its own." + extra]
        if data.get("layer_count") == 0:
            notes.append("FontLab holds no layer at all for this glyph, which means it has no outline data.")
        result = {"name": clean, "empty": True, "contour_count": 0, "node_count": 0, "notes": notes}
        if clean == ".notdef":
            notes.append(".notdef is the glyph shown when a character is missing from the font. An empty .notdef is valid "
                         "but not recommended; see check_notdef.")
            if _notdef_auto_enabled():
                result["notdef_check"] = _notdef_check_best_effort()
        return result
    result = analyze_outline(data)
    if mc and mc.get("agree") is False:
        result["verification"]["status"] = "unverified"
        result["verification"]["modern_check"] = mc
        result["notes"].append(f"FontLab's modern layer holds {mc.get('modern_nodes')} node(s) but the legacy reader found {data['node_count']}: "
                               "the legacy view is stale, so these numbers should not be relied on.")
    elif not modern_off:
        _stale_legacy_check(clean, data, result, mc)
    return result


# --------------------------------------------------------------------------
# MCP tools (thin wrappers)
# --------------------------------------------------------------------------

mcp = MCPServer("Glyphbridge FontLab")


@mcp.tool()
def fontlab_status(ctx: Context | None = None) -> dict[str, Any]:
    """Check whether the bridge to FontLab 8 is working, and whether a font is open.

    Call this first if anything else fails. It confirms the listener inside
    FontLab is reachable and reports the open font's name if there is one, plus
    server_version and listener_version (and a compatibility_note when the
    listener is older than this server expects). After changes it also counts the
    changes made through Glyphbridge in this session (see save_note: it cannot know whether the person saved).
    """
    _note_client(ctx)
    return _with_font(check_status)


@mcp.tool()
def get_current_font(ctx: Context | None = None) -> dict[str, Any]:
    """Get live details about the font currently open in FontLab 8.

    Returns family and style name, file path, glyph count, and vertical
    metrics (units per em, ascender, descender, cap height, x-height).
    Fields the font hasn't set are returned as null and explained in 'notes'.

    Also checks the font's .notdef glyph (see check_notdef): the result has a 'notdef' entry, and if .notdef is missing or
    empty a warning dialog is shown to the person in FontLab (once per font per session). In that case this call can
    take up to two minutes while the dialog waits for a click; that is normal, not a hang.
    """
    _note_client(ctx)
    return _with_font(read_current_font_checked)


@mcp.tool()
def list_glyphs(ctx: Context | None = None) -> dict[str, Any]:
    """List the names of all glyphs in the font currently open in FontLab 8.

    Every font has a '.notdef' glyph (normally the first one): expect it in this list. A brand-new font may contain
    nothing else, and its .notdef is empty at first; that is normal.
    """
    _note_client(ctx)
    return _with_font(read_glyph_names)


@mcp.tool()
def get_glyph_outline(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Read the actual outline (shape) of one glyph in the font open in FontLab 8.

    Returns every contour with its nodes (x, y, kind, smooth), the curve type
    (cubic or quadratic), the drawing direction, a bounding box, and an SVG
    path string per contour, plus the glyph's overall 'ink_bbox' (the real
    curve extents). Coordinates are font units, y up, in the same space as
    FontLab's X/Y readouts.

    Every result carries a verification status. 'verified' means the raw node
    coordinates agree with FontLab's own bounding box and margins.
    'calibrated' means they did not, because the glyph's element carries a
    transformation (position/scale, set with FontLab's Element selection tool)
    that the raw node data leaves out; x/y are then mapped into FontLab's view
    (what is drawn on screen) and the originals are kept as raw_x/raw_y.
    Calibration assumes one element and no rotation or slant; otherwise the
    status is 'unverified'. 'unverified' means the
    check could not be completed and the numbers should not be relied on for
    exact work. Components are not followed: a composite glyph reports a note,
    not the outlines it references.

    Preferred route: FontLab's own element transform (position, scale, rotation,
    slant, mirroring) is read directly and applied, then cross-checked against
    FontLab's bounding box and margins; the reply says 'transform_source' and lists
    each element's transform in 'elements'. Only if that cannot be read or does not
    reproduce FontLab's geometry does the tool fall back to the estimate described
    above.

    Glyphs drawn through the API (draw_polygon, draw_path): FontLab's older node view cannot see them. The tool then reads the nodes
    from FontLab's modern layer and says so ('source': 'modern layer'): every contour (closed, FontLab's clockwise flag and the
    direction computed from the points, y up, curve_type none / cubic / quadratic / mixed), every node (x, y, kind On / Curve / Off,
    curve, smooth; Curve = cubic control point, Off = quadratic off-curve point), the ink bounding box and left, right and
    advance_width. 'verified' there means the box (for cubic curves: the exact extents of the segments, computed) equals FontLab's
    left sidebearing and ink width; quadratic or malformed curves stay 'unverified' with a reason.

    Stale view: right after a change through the API (e.g. set_glyph_sidebearings) FontLab's older node view can still show the OLD
    geometry. The tool therefore compares the modern left / right sidebearing and advance width with the margins of the older view;
    if they differ the status is 'unverified', 'stale_legacy_view' is true and the notes say so: use get_glyph_sidebearings for the
    current margins, and ask the person to close the glyph's editor tab (X) and reopen the glyph from the grid before reading the
    outline again (in a live test a plain switch to the grid tab and back did not refresh the older view).

    Since listener 0.88 the stale case is answered from the modern layer: when the older view's margins differ from the modern ones, the
    tool reads the nodes from the modern layer instead ('source': 'modern layer', 'legacy_view_was_stale': true, with the margins of both views
    in verification.legacy_margins_vs_modern); that answer is current and needs no refresh. With an older listener the 'unverified' behaviour
    described above still applies.

    .notdef: this is the mandatory glyph shown when a character is missing from the font; it may legitimately be empty
    (an empty one comes back as empty: true, plus a warning dialog in FontLab). If a glyph's layer cannot be read at all,
    the tool raises an error that says so; that is NOT the same as the glyph being empty.
    """
    _note_client(ctx)
    return _with_font(read_glyph_outline, name)


@mcp.tool()
def check_notdef(ctx: Context | None = None) -> dict[str, Any]:
    """Check whether the open font has a proper .notdef glyph, and warn the person in FontLab if it does not.

    Every font must contain a .notdef glyph (glyph 0): it is what is shown when a character that is typed is not in
    the font. It should have a visible outline, usually a rectangle, often with a question mark or an X inside. A new
    FontLab font starts with an EMPTY .notdef, so an empty one is normal for a font in progress, but not recommended.

    Returns 'status': 'missing', 'empty' (exists but has no lines or shapes), 'has_outline', or 'unknown' (could not be
    determined; then say nothing about it being missing or empty). If it is missing or empty, a warning dialog is shown
    inside FontLab (once per font per session) and you should ALSO tell the person in your reply; follow
    'agent_instruction'. While the dialog waits for a click this call can take up to two minutes; that is normal.
    get_current_font runs this check automatically.
    """
    _note_client(ctx)
    return _with_font(check_notdef_glyph)


@mcp.tool()
def create_glyph(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Create one new, empty glyph in the font currently open in FontLab 8.

    The glyph has no contours yet - this only adds it to the font by name.
    Fails clearly (raises an error) if a glyph with that name already
    exists, or if FontLab did not actually add it. Success is only ever
    reported after re-checking the font's glyph list confirms the glyph
    is really there.

    FontLab assigns a Unicode value by itself when the name is a standard one
    ('B' -> 66, 'eacute' -> 233); other names (alternates like 'A.alt',
    ligatures, work glyphs) get none. The reply says which happened
    (unicode, unicode_status, unicode_assigned_by_fontlab) and
    'agent_instruction' says what to do next: when FontLab already assigned
    the value, do NOT call set_glyph_unicode. 'name_warnings' (only present when
    needed) are non-blocking naming hints, for example a typo that would leave
    the glyph unencoded. FontLab maps uniXXXX names too (seen live: 'uni00E9' ->
    233); if it assigned none, the reply points out which codepoint the name states.
    FontLab skips its automatic assignment when ANOTHER glyph already holds the
    codepoint (seen live: whichever of 'eacute' / 'uni00E9' is created second gets none).
    When FontLab assigned none to a single-character or uniXXXX name although the
    name states a codepoint, the reply says whether ANOTHER glyph already holds it
    (also_held_by; FontLab was seen to skip its automatic assignment then): do not
    set it on your own in that case, ask the person.

    Names containing any character outside A-Z a-z 0-9 . _ - are refused before
    FontLab is called: FontLab silently strips them (non-ASCII letters, spaces,
    # / * : + @ ! $ % & ( ) ~ = were all seen disappearing) and would create a
    glyph under a different name. For the letter e-acute use 'eacute' or 'uni00E9'.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(create_new_glyph, name)


@mcp.tool()
def get_glyph_width(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Get the advance width of one glyph in the font currently open in FontLab 8.

    Width is in font units, on the same scale as the font's units-per-em
    (for a 1000-upm font, typical letter widths run a few hundred units).
    """
    _note_client(ctx)
    return _with_font(read_glyph_width, name)


@mcp.tool()
def set_glyph_width(name: str, width: float, ctx: Context | None = None) -> dict[str, Any]:
    """Set the advance width of one glyph in the font currently open in FontLab 8.

    Width is in font units, same scale as get_glyph_width. This changes ONLY the advance width (the space the glyph takes when
    typed): the outline does not move, so the right sidebearing changes and the left one does not. To place the outline inside
    the width use set_glyph_sidebearings instead. A glyph that has an outline but no editable layer yet is refused: the person
    must open it once in an editor tab in FontLab. This does not
    require confirmation in FontLab, unlike delete_glyph, since it is a
    reversible value change rather than a destructive one. Success is only
    reported after re-reading the glyph confirms the new width took effect.
    The reply's display_note explains that parts of FontLab's screen (centre info box, grid thumbnail) refresh only when the
    person switches to the grid tab and back; the saved numbers are right.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_width, name, width)


@mcp.tool()
def get_glyph_sidebearings(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Read the left and right sidebearing, the advance width and the ink width of one glyph that has an outline.

    Values are in font units and are exactly what FontLab's editor panel shows: advance width = left + ink width + right.
    The glyph needs an editable layer (the person opens it once in an editor tab in FontLab); otherwise this answers with
    an error that says so. Reading changes nothing.
    """
    _note_client(ctx)
    return _with_font(read_glyph_sidebearings, name)


@mcp.tool()
def get_kerning(pairs: list[list[str]] | None = None, text: str | None = None, confirmed_large_read: bool | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Read FontLab's kerning for selected glyph pairs of the font currently open in FontLab 8. Reading changes nothing.

    Give exactly one of: pairs, a list of [left, right] glyph names such as [["A", "V"], ["T", "o"]], or text,
    a string of 2 or more characters such as "AVATAR" whose neighbouring characters are looked up (each character must map to
    exactly one glyph by its primary Unicode, otherwise that pair answers an error). Never ask for the whole kerning table: read only what the task needs.
    There is no upper limit, but more than 250 pairs (text: more than 251 characters) in one call is refused until the PERSON has approved it:
    warn them that a large read costs many tokens, say how many pairs and why, ask for approval, and only after they said yes repeat the call with
    confirmed_large_read=true. Never set confirmed_large_read=true on your own.
    Values are in font units and are the numbers FontLab applies, read from the kerning table of the current master, class (group) kerning
    included; negative = closer. Each result says its source: 'glyph : glyph', 'glyph : class', 'class : glyph' (with the class named),
    'class : class', or 'none' (no entry: value 0, kerned false). Report the source; never guess whether a value comes from a class.
    A pair that could not be read has an 'error' and is never a zero. It reads the current font, the one whose window is in front in
    FontLab; with several fonts open it refuses when that font cannot be matched to its kerning table (for example a new, unsaved font).
    Other masters, feature-based and contextual kerning are not covered. Needs listener v0.104 (several open fonts: v0.112).
    """
    _note_client(ctx)
    return _with_font(read_kerning, pairs, text, confirmed_large_read)


@mcp.tool()
def set_glyph_sidebearings(name: str, left: float, right: float | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Set the left and right sidebearing of one glyph, in font units, in the font currently open in FontLab 8.

    The OUTLINE is moved (its shape is unchanged) so that the left sidebearing equals `left` and the right one equals `right`;
    the advance width then becomes left + ink width + right, exactly as when a person drags the sidebearing lines in
    FontLab. `right` defaults to `left`, which gives equal sidebearings. Negative values are allowed (they pull the next
    glyph closer). Example: an outline 500 units wide with left 88 and right 77 gets an advance width of 665.
    Use set_glyph_width instead when only the advance width must change and the outline must stay where it is.
    Refused, with nothing changed: a glyph without an outline (an empty glyph has no sidebearings: draw it first with
    draw_polygon, or use set_glyph_width), and a glyph that has an outline but no editable layer (the person must open it
    once in an editor tab in FontLab). This tool never creates a layer. Success (verified: true) is only reported after re-reading left, right and the advance
    width confirms them; the reply gives the values before and after. The reply's display_note explains that parts of
    FontLab's screen (centre info box, ghost fill, grid thumbnail) refresh only when the person switches to the grid tab and
    back; the saved numbers are right.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_sidebearings, name, left, right)


@mcp.tool()
def draw_polygon(name: str, points: list[list[float]] | None = None,
                 contours: list[list[list[float]]] | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Draw closed contours of straight line segments into an EMPTY glyph in the font currently open in FontLab 8.

    Give exactly one of `points` (ONE contour: a list of 3 to 500 [x, y] pairs in font units, y up, in drawing order) or
    `contours` (SEVERAL contours: a list of 1 to 20 such point lists, at most 2000 points in all, drawn together as one shape, for
    example a letter with a counter). Each contour closes by itself from its last point back to its first, so do not repeat
    the first point. Example: a 400 by 300 rectangle is [[0, 0], [400, 0], [400, 300], [0, 300]]; an O-like ring is
    contours=[[[0,0],[300,0],[300,300],[0,300]], [[100,100],[100,200],[200,200],[200,100]]]. At least 3 different positions per
    contour. Straight segments only (no curves: use draw_path for those; no open paths); the glyph must hold nothing yet, otherwise the call is refused
    and nothing changes. Coordinates are rounded to whole units (rule B): the reply lists every changed coordinate in coordinates_rounded.

    Direction: this tool draws the points in the order given and never reorders them. In the cubic test font FontLab's own outer
    contour (glyph A) runs COUNTERCLOCKWISE in y-up units, so draw outer contours counterclockwise and counters (holes)
    clockwise; a quadratic (TrueType-flavoured) font uses the opposite convention. In the ring example above the outer
    rectangle runs counterclockwise and the hole clockwise.

    A glyph made by create_glyph has no editable layer. This tool creates it by itself (the reply says layer_created); nobody
    needs to open the glyph in an editor tab. If the layer cannot be created safely (no other glyph of the font shows the right layer
    name, or they disagree) the call is refused and says so.
    Success (verified: true) is only reported after re-reading the layer confirms 1 shape, one node per point and one contour per polygon; the reply
    also gives left, right, advance_width and ink_width. Drawing does NOT change the advance width: set it afterwards with
    set_glyph_width, or place the outline together with the width via set_glyph_sidebearings.
    The reply's display_note explains that parts of FontLab's screen (editor panel numbers, centre info box, grey ghost fill, grid
    thumbnail) may show old values until the person switches to the grid tab and back; the saved shape is right.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_polygon, name, points, contours)


@mcp.tool()
def draw_path(name: str, contours: list[list[dict[str, Any]]], ctx: Context | None = None) -> dict[str, Any]:
    """Draw closed contours with straight AND cubic curve segments into an EMPTY glyph in the font currently open in FontLab 8.

    `contours` is a list of 1 to 20 contours (at most 2000 nodes in all, control points included, drawn together as ONE shape). A
    contour is a list of 3 to 500 points in drawing order, font units, y up. Each point is an object {"x": number, "y": number}
    with up to three optional extras:
      - "c1" and "c2" (always both): the two control points ({"x","y"} each) of the CUBIC curve segment that ENDS at this point.
        c1 is the control point next to the previous point, c2 the one next to this point. Without them the segment from the previous
        point is straight. For the FIRST point they describe the closing segment, from the last point back to the first one.
      - "smooth": true marks the point as a smooth node. Its two neighbours (a control point, or the neighbouring point for a straight
        segment) must then lie on opposite sides of one straight line through it (within 2 degrees), otherwise the call is refused
        and nothing is drawn. Smooth is not computed for you: you give the control points, they are not moved.
    Each contour closes by itself; do not repeat the first point. Example: a 400 by 400 square whose right edge bulges out to x = 500:
    [[{"x":0,"y":0},{"x":400,"y":0},{"x":400,"y":400,"c1":{"x":500,"y":100},"c2":{"x":500,"y":300}},{"x":0,"y":400}]] (the segment from
    (400, 0) to (400, 400) is the curve). A circle of radius 200 around (200, 200), four smooth points, counterclockwise (control
    points at 55% of the radius along the tangents):
    [[{"x":400,"y":200,"smooth":true,"c1":{"x":310,"y":0},"c2":{"x":400,"y":90}},
      {"x":200,"y":400,"smooth":true,"c1":{"x":400,"y":310},"c2":{"x":310,"y":400}},
      {"x":0,"y":200,"smooth":true,"c1":{"x":90,"y":400},"c2":{"x":0,"y":310}},
      {"x":200,"y":0,"smooth":true,"c1":{"x":0,"y":90},"c2":{"x":90,"y":0}}]]
    (the first point's c1 / c2 are the closing segment from the bottom point back to the right point).
    Directions: outer contours counterclockwise, counters (holes) clockwise in a cubic (PostScript-flavoured) font; this tool never reorders points.

    RULE B (whole units): FontLab stores whole numbers here. Every coordinate is rounded to the nearest whole unit (a half rounds up)
    and the reply lists each coordinate that changed in coordinates_rounded (with a rounding_note); give whole numbers to avoid that.

    The glyph must hold nothing yet, otherwise the call is refused and nothing changes. A glyph made by create_glyph has no editable
    layer: the tool creates it by itself (the reply says layer_created). Success (verified: true) is only reported after the re-read layer
    matches your request node by node (nodes_match). get_glyph_outline computes the exact extents of cubic curves, so it reports
    such outlines as verified when the computed cubic extents equal FontLab's own margins; the node list is exact. Drawing does NOT change the advance width: use set_glyph_width or
    set_glyph_sidebearings afterwards. The reply's display_note explains that parts of FontLab's screen may show old values until the person
    switches to the grid tab and back.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_path, name, contours)


@mcp.tool()
def check_glyph_unicode(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Check a glyph's Unicode codepoint against the Unicode standard.

    For glyphs named with a single character (e.g. "A"), the correct
    codepoint is unambiguous - it is that character's own Unicode value -
    and this reports whether the glyph's current assignment matches it.
    The same holds for names that state their codepoint: uniXXXX (4
    UPPERCASE hex digits, e.g. uni00E9) and uXXXX to uXXXXXX.
    Getting this right is what makes the glyph actually appear when
    someone types that character, in any application, on any keyboard.

    For glyphs with longer conventional names (e.g. "ampersand", or
    ligatures), this cannot yet determine the standard value automatically
    (that requires the Adobe Glyph List, which is not implemented here) -
    it reports has_unicode and the current value, with matches_standard
    left as null and a note explaining why, rather than guessing.
    """
    _note_client(ctx)
    return _with_font(read_glyph_unicode, name)


@mcp.tool()
def set_glyph_unicode(name: str, codepoint: int, ctx: Context | None = None) -> dict[str, Any]:
    """Set the Unicode codepoint a glyph maps to, in the font open in FontLab 8.

    codepoint is a plain integer (e.g. 65 for 'A' - not "U+0041" or "0x41").
    Do not call this right after create_glyph when that reply shows FontLab
    already assigned the codepoint (unicode_status 'assigned'): use it only when
    the status is 'none' or 'unreadable' AND the person wants a codepoint, when
    the name states its codepoint (a single character, or uniXXXX / uXXXX) and
    FontLab assigned none, or to
    change a value the person asked to change. Never guess a codepoint for a
    non-standard name (alternates, ligatures, work glyphs): leave those unencoded
    unless the person gives one. The reply's 'changed' is false when the glyph
    already had that value. FontLab accepts a second glyph with the same
    codepoint silently, so the reply lists the OTHER glyphs holding it
    (also_held_by) and adds duplicate_warning when there are any: tell the
    person, nothing is changed automatically. Pass codepoint 0 to REMOVE the
    glyph's Unicode (needs listener v0.51 or newer to be reported as a success).

    This does not require confirmation in FontLab, since it is a reversible
    value change like set_glyph_width, not a destructive one like
    delete_glyph. Success is only reported after re-reading the glyph
    confirms the new mapping actually took effect.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_unicode, name, codepoint)


@mcp.tool()
def delete_glyph(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Delete one glyph from the font currently open in FontLab 8.

    This shows a Yes/No confirmation dialog inside FontLab itself, and only
    proceeds if a person clicks Yes there - this tool cannot delete anything
    on its own. Expect this call to take a while (up to two minutes) if the
    dialog is waiting on a response; that is normal, not a hang. Deletion is
    permanent for this editing session and cannot be undone through this
    bridge. Success is only ever reported after re-checking the font's
    glyph list confirms the glyph is really gone.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or Ctrl+S). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(delete_existing_glyph, name)


@mcp.tool()
def finish_changes(ctx: Context | None = None) -> dict[str, Any]:
    """Call this ONCE when you have finished a whole package of changes to the font (creations, width or Unicode edits,
    deletions), and never per step. It counts the changes made through Glyphbridge since the last call and returns
    'save_reminder': show it to the person in the chat in bold, exactly as written, after your summary. If nothing was
    changed, save_reminder is null and you say nothing about saving.

    Glyphbridge never saves the font and never opens a dialog for this: saving is the person's job (File menu or Ctrl+S),
    and the reminder appears only in the chat. This tool changes nothing in FontLab.
    """
    _note_client(ctx)
    return _with_font(finish_change_package)


# --------------------------------------------------------------------------

def _self_check() -> None:
    """Exercise the listener connection without Claude. Uses stdout: never runs as a server."""
    _CLIENT["name"] = "glyphbridge --check"
    for label, fn in (
        ("fontlab_status", check_status),
        ("get_current_font", read_current_font),
        ("list_glyphs", read_glyph_names),
        (".notdef status (read-only)", read_notdef_status),
    ):
        try:
            print(f"[OK]     {label}: {json.dumps(fn(), ensure_ascii=False)}")
        except ToolError as exc:
            print(f"[FAILED] {label}: {exc}")

    if "--outline" in sys.argv:
        idx = sys.argv.index("--outline")
        target = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""
        try:
            print(f"[OK]     get_glyph_outline({target!r}): "
                  f"{json.dumps(read_glyph_outline(target), ensure_ascii=False, indent=2)}")
        except ToolError as exc:
            print(f"[FAILED] get_glyph_outline({target!r}): {exc}")

    if "--notdef-warn" in sys.argv:
        try:
            print(f"[OK]     check_notdef (may show a dialog in FontLab): "
                  f"{json.dumps(check_notdef_glyph(), ensure_ascii=False, indent=2)}")
        except ToolError as exc:
            print(f"[FAILED] check_notdef: {exc}")

    if "--with-write-test" in sys.argv:
        import time
        probe_name = f"glyphbridge_probe_{int(time.time())}"
        try:
            out = create_new_glyph(probe_name)
            print(f"[OK]     create_glyph: {json.dumps(out, ensure_ascii=False)}")
        except ToolError as exc:
            print(f"[FAILED] create_glyph: {exc}")
        try:
            out = create_new_glyph(probe_name)  # duplicate on purpose
            print(f"[FAILED] duplicate create_glyph should have raised, got: {out}")
        except ToolError as exc:
            print(f"[OK]     duplicate create_glyph correctly rejected: {exc}")
        try:
            out = delete_existing_glyph(probe_name)
            print(f"[OK]     delete_glyph: {json.dumps(out, ensure_ascii=False)}")
        except ToolError as exc:
            print(f"[FAILED] delete_glyph: {exc}")
        try:
            probe2 = f"glyphbridge_width_probe_{int(time.time())}"
            create_new_glyph(probe2)
            before = read_glyph_width(probe2)
            written = write_glyph_width(probe2, before["width"] + 50)
            after = read_glyph_width(probe2)
            ok = after["width"] == written["width_after"] and after["width"] != before["width"]
            print(f"[{'OK' if ok else 'FAILED'}]     width round-trip: {before} -> {written} -> {after}")
            delete_existing_glyph(probe2)
        except ToolError as exc:
            print(f"[FAILED] width round-trip: {exc}")
        try:
            out = delete_existing_glyph(probe_name)  # already gone
            print(f"[FAILED] deleting already-gone glyph should have raised, got: {out}")
        except ToolError as exc:
            print(f"[OK]     deleting already-gone glyph correctly rejected: {exc}")
        print(f"[OK]     finish_changes (end of the write test): {json.dumps(finish_change_package(), ensure_ascii=False)}")


if __name__ == "__main__":
    _LAUNCHER["value"] = _read_launcher()  # once, at startup (v0.35); never when the file is imported by the tests
    if ("--check" in sys.argv or "--with-write-test" in sys.argv or "--outline" in sys.argv
            or "--notdef-warn" in sys.argv):
        _self_check()
    else:
        mcp.run()
