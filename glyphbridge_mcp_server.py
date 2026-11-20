"""
Glyphbridge-FontLab-MCP  -  MCP server (v0.82)
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
SERVER_VERSION = "0.82"   # keep identical to the header line "MCP server (vX.YY)" (a test compares them)
MIN_LISTENER_VERSION = (0, 82)     # oldest listener this server's features fully work with
# v0.40: the save shortcut is read from the system the server runs on, which is FontLab's (the listener answers on 127.0.0.1 only)
SAVE_SHORTCUT = "Cmd+S" if sys.platform == "darwin" else "Ctrl+S"
SAVE_REMINDER = f"**You must save if you want to keep these changes: use the File menu or press {SAVE_SHORTCUT} in FontLab.**"   # shown in CHAT only, never as a FontLab dialog
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


_SAVE_QUESTION_NOTE = ("FontLab may not count this change as unsaved, so closing the font may ask no save question and lose it silently (see "
                       "fontlab_changed_mark). Tell the person if they may close the font before saving.")


def _mark_modified(result: dict, modified: bool) -> None:
    """Add font_modified to a write reply; a real change is counted and the agent is told how to remind the person ONCE. v0.51: a write
    the listener could not mark gets save_question_note; a listener or a tool without the mark adds nothing. v0.52: the note depends only
    on the call being made without an error; glyph_has_changes stays in the reply as information, since it read false while the mark worked."""
    result["font_modified"] = bool(modified)
    if modified:
        _note_change()
        existing = result.get("agent_instruction")
        result["agent_instruction"] = (existing + " " + _SAVE_INSTRUCTION) if existing else _SAVE_INSTRUCTION
        mark = result.get("fontlab_changed_mark")
        if isinstance(mark, dict) and not (mark.get("called") is True and not mark.get("call_error")):
            result["save_question_note"] = _SAVE_QUESTION_NOTE


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


# v0.41 (listener 0.118): the PostScript names come from the font package, where FontLab keeps what Font Info shows. The legacy
# font.info can disagree (test 298: Font Info W6aTest-Regular, font.info Unnamed1-Regular, package psn W6aTest-Regular, test 300).
# No name is reported as "not set" any more: whether FontLab derived a name or a person typed it cannot be read.
_PACKAGE_FIELDS = ("package_names", "package_matched_by", "package_names_unavailable", "package_name_errors")
_PS_FROM_PACKAGE = (("postscript_font_name", "psn"), ("postscript_full_name", "ffn"))


def _clean_font(data: dict) -> dict:
    """Normalise the listener's font info for the agent: the PostScript names as FontLab's Font Info shows them, with their source."""
    font = {k: _tidy_number(v) for k, v in data.items() if k != "open" and k not in _PACKAGE_FIELDS}
    notes = []

    package = data.get("package_names")
    if isinstance(package, dict):
        font["postscript_names_source"] = "font package (as FontLab's Font Info shows them)"
        for key, attr in _PS_FROM_PACKAGE:
            value, legacy = package.get(attr), font.get(key)
            if not isinstance(value, str):
                notes.append(f"{key} could not be read from the font package, so it comes from FontLab's older font-info view, "
                             "which can lag behind what Font Info shows.")
                continue
            font[key] = value
            if legacy != value:
                font["legacy_" + key] = legacy
                notes.append(f"{key} {value!r} is what FontLab's Font Info shows; FontLab's older font-info view reads {legacy!r} instead.")
        errors = data.get("package_name_errors")
        if isinstance(errors, list) and errors:
            notes.append("Some names of the font package could not be read: " + "; ".join(str(e) for e in errors))
    else:
        reason = data.get("package_names_unavailable")
        font["postscript_names_source"] = "older font-info view"
        notes.append("postscript_font_name and postscript_full_name come from FontLab's older font-info view, which can lag behind what "
                     "Font Info shows" + (f" (the font package could not be used: {reason})." if isinstance(reason, str) and reason
                                          else " (this listener does not read the font package; listener 0.118 does)."))

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
                               f"anything is unsaved now. Glyphbridge never saves: the person saves with the File menu or {SAVE_SHORTCUT}.")
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
        mark = data.get("fontlab_changed_mark")          # v0.51 (listener 0.132); never claims FontLab's icon or that it will ask
        if isinstance(mark, dict) and isinstance(mark.get("called"), bool):
            fwd = {"called": mark["called"]}
            for key in ("reason", "call_error", "via_glyph"):     # via_glyph (v0.53, listener 0.133): the surviving glyph a delete's mark went to
                if isinstance(mark.get(key), str) and mark[key]:
                    fwd[key] = mark[key]
            has = mark.get("glyph_has_changes")
            if isinstance(has, bool) or has == "unknown":
                fwd["glyph_has_changes"] = has
            result["fontlab_changed_mark"] = fwd
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
    if isinstance(data.get("layer_created"), str) and data["layer_created"]:      # v0.48 (listener 0.127)
        result["layer_created"] = data["layer_created"]
        if isinstance(data.get("layer_name_source"), str) and data["layer_name_source"]:
            result["layer_name_source"] = data["layer_name_source"]
    if isinstance(data.get("layer_note"), str) and data["layer_note"]:
        result["layer_note"] = data["layer_note"]
        instruction += (" The glyph WAS created but has no layer (see layer_note). Tell the person not to use Glyph > Add Component on it "
                        "until it has one: FontLab crashed on such glyphs in testing, which loses unsaved work.")
    result["agent_instruction"] = instruction
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


_FONT_PSN_MAX = 63               # v0.60: the PostScript name (family without spaces + "-Regular") stays within 63 characters
_FONT_PSN_FORBIDDEN = "[](){}<>/%"   # characters a PostScript name may not hold (the listener refuses them too)
_FONT_NAMES_INSTRUCTION = (
    "Font names came up: ask the person whether they want the fields of Font Info's Names page explained, and explain them only if "
    "they say yes. What is known: Build Names sets Full name = family + ' ' + style, PostScript name = family without spaces + '-' + "
    "style, and Style group = family; this tool set them so for the style Regular. Do not guess about the other fields.")
_OUTPUT_PANEL_INSTRUCTION = (   # v0.61: a person who never opens the OUTPUT panel misses its notes
    "If you have not yet done so in this conversation, also tell the person that FontLab's OUTPUT panel lists every change "
    "Glyphbridge makes, with its warnings, and is worth keeping open.")


def _check_font_family(family: Any) -> None:
    """Refuse a family name the listener would refuse, before anything is sent."""
    if not isinstance(family, str):
        raise ToolError("family must be text, or left out to let FontLab name the font. No font was made.")
    if not family.strip():
        raise ToolError("family must not be empty: leave it out to let FontLab name the font (Unnamed, Unnamed1, ...), as File > "
                        "New Font does. No font was made.")
    problems = []
    if family != family.strip(" "):
        problems.append("it must not start or end with a space")
    psn = family.replace(" ", "") + "-Regular"
    if len(psn) > _FONT_PSN_MAX:
        problems.append(f"the PostScript name it gives, {psn!r}, has {len(psn)} characters; at most {_FONT_PSN_MAX} are allowed, so the "
                        f"family may have at most {_FONT_PSN_MAX - len('-Regular')} characters without its spaces")
    if len(family) > _FONT_PSN_MAX:
        problems.append(f"it has {len(family)} characters; at most {_FONT_PSN_MAX} are allowed")
    if any(not (32 <= ord(ch) <= 126) for ch in family):
        problems.append("it may hold printable ASCII characters only (no accented letters, no tabs)")
    if any(ch in _FONT_PSN_FORBIDDEN for ch in family):
        problems.append(f"it becomes part of the PostScript name, which may not hold any of {_FONT_PSN_FORBIDDEN}")
    if problems:
        raise ToolError(f"family {family!a} was not sent to FontLab: " + "; ".join(problems) + ". No font was made.")


def create_new_font(family: Any = None) -> dict:
    if family is not None:
        _check_font_family(family)
    _require_listener((0, 146), "create_font")
    data = _write_post("/font/create", {} if family is None else {"family": family})
    before, after = data.get("fonts_open_before"), data.get("fonts_open_after")
    if data.get("created") is not True:
        reason = data.get("reason") or "unknown reason"
        made = type(before) is int and type(after) is int and after > before
        if made:
            _note_change()
            raise ToolError(f"A new font WAS made in FontLab, but it was not confirmed: {reason}. Tell the person: a new, unsaved font "
                            f"may be open that they did not see coming; look at FontLab's FONTS panel. {_CHANGED_BY_ERROR_NOTE}")
        if "names_before" in data and type(after) is not int:
            _note_change(sure=False)
            raise ToolError(f"It is not known whether a new font was made: {reason}. Ask the person to look at FontLab's FONTS panel. "
                            f"{_UNSURE_NOTE}")
        if "no font was made" in reason:
            raise ToolError(reason[:1].upper() + reason[1:] + ".")
        raise ToolError(f"No font was made: {reason}.")
    names = data.get("names_after") if isinstance(data.get("names_after"), dict) else {}
    pkg = data.get("package") if isinstance(data.get("package"), dict) else {}
    result = {
        "created": True,
        "saved": False,
        "full_name": names.get("ffn"),
        "family_name": names.get("tfn"),
        "style_name": names.get("tsn"),
        "postscript_name": names.get("psn"),
        "style_group": names.get("sgn"),
        "named_by": "FontLab, as File > New Font" if family is None else "Glyphbridge, as Font Info's Build Names would",
        "fonts_open_before": before,
        "fonts_open_after": after,
        "units_per_em": _tidy_number(pkg.get("upm")),
        "masters": pkg.get("mastersCount"),
        "default_master": pkg.get("defaultMaster"),
        "glyph_count": pkg.get("glyphsCount"),
    }
    instruction = ("A new, unsaved font was made in FontLab and is now the font in front. Tell the person every item of person_notes, "
                   "in your own words but leaving none out (FontLab's OUTPUT panel shows them too). " + _OUTPUT_PANEL_INSTRUCTION)
    if family is not None:
        result["family_requested"] = family
        result["names_set"] = data.get("names_set") is True
        result["legacy_family_set"] = data.get("legacy_family_set") is True
        problems = [f"{e.get('field')}: wanted {e.get('value')!r}, read back {e.get('read_back')!r}"
                    + (f" ({e['call_error']})" if e.get("call_error") else "")
                    for e in data.get("assignments") or [] if isinstance(e, dict) and e.get("read_back_equal") is not True]
        legacy = data.get("legacy_family") if isinstance(data.get("legacy_family"), dict) else {}
        if legacy.get("read_back_equal") is not True:
            problems.append("legacy family: " + (legacy.get("reason") or legacy.get("call_error")
                                                 or f"wanted {family!r}, read back {legacy.get('read_back')!r}"))
        if problems:
            result["name_problems"] = problems
            instruction += (" Not every name was set (name_problems): tell the person which, and that Glyphbridge's later replies may "
                            "name the font by FontLab's own name.")
        instruction += " " + _FONT_NAMES_INSTRUCTION
    mark = data.get("fontlab_changed_mark")
    if isinstance(mark, dict):
        result["fontlab_changed_mark"] = mark
    notes = data.get("notes")
    result["person_notes"] = [n for n in notes if isinstance(n, str) and n.strip()] if isinstance(notes, list) else []
    result["agent_instruction"] = instruction
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

    # v0.81 (AW4 1470-1489): listener 0.198 reads FontLab's modern advanceWidth and the legacy glyph.width as a cross-check
    if "source" not in data:
        return {"name": clean, "width": _tidy_number(data.get("width")), "width_source": "legacy",
                "width_note": ("This listener is older than 0.198: the width comes from FontLab's older (legacy) view and was not "
                               "cross-checked with the modern advance width.")}
    source = data.get("source")
    if source not in ("modern", "legacy") or not isinstance(data.get("width"), (int, float)) or isinstance(data.get("width"), bool):
        raise ToolError(f"The width of glyph '{clean}' could not be read: {data.get('reason') or 'the listener gave no width'}. "
                        "This is not a width of 0.")
    out = {"name": clean, "width": _tidy_number(data["width"]), "width_source": source}
    adv, leg = data.get("advance_width"), data.get("legacy_width")
    if source == "legacy":
        out["width_note"] = (f"FontLab's modern advance width could not be read ({data.get('modern_reason') or 'no reason given'}), "
                             "so this width comes from FontLab's older (legacy) view and was not cross-checked.")
        return out
    numbers = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (adv, leg))
    if numbers and abs(float(adv) - float(leg)) >= 0.01:
        out["legacy_width"] = _tidy_number(leg)
        out["widths_disagree"] = True
        out["width_note"] = (f"FontLab holds two values for this glyph's width: {_tidy_number(adv)} in its modern view (the value its "
                             f"width field and tooltip show) and {_tidy_number(leg)} in its older view. Which one FontLab saves "
                             "and exports is not known.")
        out["agent_instruction"] = ("Tell the person both width values and that FontLab's two views disagree; do not choose one "
                                    "for them.")
    elif not numbers:
        out["width_note"] = ("The width is FontLab's modern advance width; the cross-check with FontLab's older view could not be "
                             f"made ({data.get('legacy_error') or 'no legacy width given'}).")
    return out


def write_glyph_width(name: str, width: float) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    if isinstance(width, bool) or not isinstance(width, (int, float)):
        raise ToolError("Width must be a number.")
    if width < 0:
        raise ToolError("Width must not be negative.")
    # v0.80: whole units, rule B (a half rounds up), as FontLab's own width field does (AW2 1456); also with an older listener
    target = _tidy_number(_rule_b(width))
    rounded = float(width) != float(target)
    asked = f"{_tidy_number(width)}, rounded to {target}" if rounded else f"{target}"

    data = _write_post("/glyph/width", {"name": clean, "width": target})

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
        before, after = data.get("before"), data.get("after")
        moved = (isinstance(before, (int, float)) and isinstance(after, (int, float)) and not isinstance(before, bool)
                 and not isinstance(after, bool) and abs(after - before) >= 0.01)
        if data.get("changed") is True or moved:
            # v0.80 (AW 1449): the width moved, but not to the request; the font HAS changed, so never "NOT changed"
            _note_change()
            layer = (f" A layer named '{data['layer_created']}' was also created for the glyph." if data.get("layer_created") else "")
            raise ToolError(f"Width of glyph '{clean}' was changed to {_tidy_number(after)} (was {_tidy_number(before)}), but not to the "
                            f"requested {asked}: {detail}.{layer} {_CHANGED_BY_ERROR_NOTE}")
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
    if rounded:
        result["width_rounded"] = {"requested": _tidy_number(width), "written": target}
        result["rounding_note"] = _WIDTH_ROUNDING_NOTE
    for key in ("route", "outline_untouched", "warning", "display_note", "layer_created", "layer_create_note"):
        if data.get(key) is not None:
            result[key] = data[key]
    _add_guard_fields(result, data)
    _mark_modified(result, result["width_before"] != result["width_after"] or bool(data.get("layer_created")))
    return result


_WIDTH_ROUNDING_NOTE = ("FontLab keeps advance widths in whole units, as its own width field does (seen live: a typed 437.5 became 438), so "
                        "the requested width was rounded to the nearest whole unit (a half rounds up): tell the person the width written.")


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
            # v0.59: FontLab's panels round these DOWN to whole units (live: 61.75 -> 61, -38.25 -> -39)
            "note": ("Left, right and advance width are FontLab's exact values; ink_width = advance - left - right. "
                     "FontLab's editor panel and font grid bar show sidebearings rounded DOWN to whole units "
                     "(61.75 shows as 61, -38.25 as -39), so a value with a fraction looks lower on screen.")}


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

# v0.78 (listener 0.194): class sides in set_kerning and remove_kerning, the design of 2026-11-20 (DECISIONS.md; research CW 1409-1417).
# A side written '@name' (the plain ASCII @) names a kerning group; any other side is a glyph, as before.
_KERN_CLASS_RE = re.compile(r"^@[A-Za-z0-9._-]{1,63}$")
_KERN_KIND_RANK = {"glyph : glyph": 0, "glyph : class": 1, "class : glyph": 2, "class : class": 3}     # FontLab's order (topics/kerning.md 9.9)
_KERN_SIDE_HINT = ("A side is a glyph name of 1 to 63 characters from A-Z a-z 0-9 . _ -, or '@' (the plain ASCII @) followed by a "
                   "kerning group's name, for example \"@O\" for the kerning group O.")


def _kern_side_name(n: Any) -> str | None:
    """A pair side, stripped: a glyph name, or '@' and a kerning group name; None when it is neither."""
    if not isinstance(n, str):
        return None
    s = n.strip()
    return s if (_KERN_NAME_RE.match(s or "!") or _KERN_CLASS_RE.match(s)) else None


def _kern_kind(left: str, right: str) -> str:
    return ("class" if left.startswith("@") else "glyph") + " : " + ("class" if right.startswith("@") else "glyph")


def _kern_class_fields(raw: dict, left: str, right: str) -> tuple:
    """(entry fields, sample (left, right) or None, problem text or None) from the listener's answer for a pair with a class side, type-checked."""
    fields: dict = {}
    problem = None
    want = sorted(set(nm[1:] for nm in (left, right) if nm.startswith("@")))
    classes = raw.get("classes")
    if (not isinstance(classes, dict) or sorted(classes) != want
            or not all(isinstance(v, dict) and v.get("side") in ("left", "right", "both") and isinstance(v.get("member_count"), int)
                       and not isinstance(v.get("member_count"), bool) and v["member_count"] >= 0 for v in classes.values())):
        problem = "the listener did not describe the classes of this pair"
    else:
        fields["classes"] = {k: {"side": classes[k]["side"], "member_count": classes[k]["member_count"]} for k in want}
    sample, pair = raw.get("sample"), None
    if isinstance(sample, dict) and all(isinstance(sample.get(k), str) and _KERN_NAME_RE.match(sample[k]) for k in ("left", "right")):
        pair = (sample["left"], sample["right"])
        if (not left.startswith("@") and pair[0] != left) or (not right.startswith("@") and pair[1] != right):
            pair, problem = None, problem or "the listener's sample pair does not keep this pair's glyph side"
        else:
            fields["sample"] = {"left": pair[0], "right": pair[1]}
    elif sample is None and "sample" in raw:
        fields["sample"] = None
    else:
        problem = problem or "the listener named no usable sample pair"
    eb = raw.get("entry_before", False)
    if eb is None or (isinstance(eb, (int, float)) and not isinstance(eb, bool) and eb == eb and abs(eb) != float("inf")):
        fields["entry_before"] = None if eb is None else _tidy_number(eb)
    return fields, pair, problem


def _kern_sample_ok(kind: str, left: str, right: str, value: Any, after: Any, verdict: Any) -> bool:
    """Whether a class pair's checked sample supports the listener's verdict: 'applied' (the sample takes value from the new entry, of
    this kind and these classes) or 'covered' (an entry of higher rank, the sample's own exception, answers for it)."""
    if not isinstance(after, dict) or "error" in after:
        return False
    if verdict == "applied":
        return (after.get("source") == kind and after.get("value") == value
                and (not left.startswith("@") or after.get("left_class") == left[1:]) and (not right.startswith("@") or after.get("right_class") == right[1:]))
    if verdict == "covered":
        return _KERN_KIND_RANK.get(after.get("source"), 9) < _KERN_KIND_RANK[kind]
    return False


def _kern_same_name_note(raw: dict, left: str, right: str, verb: str) -> str | None:
    """The note for a glyph side whose name is also a kerning group's name (listener same_name_group), or None."""
    same = raw.get("same_name_group")
    if not isinstance(same, list) or not same or not all(s in ("left", "right") for s in same):
        return None
    names = [nm for nm in dict.fromkeys(left if s == "left" else right for s in same) if not nm.startswith("@")]
    if not names:
        return None
    return " ".join(f"{n} was {verb} as the glyph {n}; the font also has a kerning group named {n}. To {'kern' if verb == 'written' else 'remove kerning of'} "
                    f"the group, write @{n}." for n in names)


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
        reason = data["error"][:600].rstrip()
        raise ToolError(f"Kerning could not be read: {reason}" + ("" if reason.endswith((".", "!", "?")) else "."))
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


_KGR_SIDES = ("left", "right", "both", "unknown")
_KGR_INSTRUCTION = (
    "These are the kerning groups (FontLab's kerning classes) of the current master (master names it), read from FontLab: side 'left' means the "
    "group's glyphs are kerned as the LEFT glyph of a pair (FontLab's Kerning Left), 'right' as the RIGHT glyph (Kerning Right), 'both' on either "
    "side (Kerning both); fontlab_side gives FontLab's own word. 'confirmed' true means two FontLab sources agree on the group (the master's "
    "kerning groups and FontLab's class list, which also gives the id). A group with confirmed false is NOT settled: report it with its "
    "mismatch (and class_list_members when given) and never pick one version yourself. An entry with an 'error' was not read; a glyph whose "
    "kerning_groups list is empty is in no kerning group on either side, which is a fact, not an error. OpenType classes and Glyph tags are "
    "not kerning groups and are not read by this tool. Other masters are not covered."
)


def _kgr_name_list(value: Any, label: str) -> list:
    """A list of names, stripped and checked, or a ToolError (before anything is sent)."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ToolError(f"{label} must be a list of names.")
    clean = []
    for n in value:
        if not isinstance(n, str) or not _KERN_NAME_RE.match(n.strip() or "!"):
            raise ToolError(f"Every name in {label} must be 1 to 63 characters from A-Z a-z 0-9 . _ - (got {n!r}).")
        clean.append(n.strip())
    return list(dict.fromkeys(clean))


def _kgr_text(value: Any, limit: int = 600) -> Any:
    return value[:limit] if isinstance(value, str) and value else None


def _kgr_plain_names(value: Any) -> Any:
    if not isinstance(value, list) or not all(isinstance(n, str) and n and n.isprintable() and len(n) <= 200 for n in value):
        return None
    return value


def _kgr_group_entry(raw: Any, expected: Any) -> dict:
    """One listener group entry as a clean, type-checked entry; anything unusable becomes an error entry."""
    out: dict = {"name": expected} if expected is not None else {}
    if not isinstance(raw, dict):
        out["error"] = "the listener's answer for this group was unusable, so it was not read"
        return out
    name = raw.get("name")
    if not isinstance(name, str) or not name.isprintable() or not 1 <= len(name) <= 200 or (expected is not None and name != expected):
        out["error"] = "the listener answered for a different or unnamed group, so it was not read"
        return out
    out["name"] = name
    if _kgr_text(raw.get("error")):
        out["error"] = _kgr_text(raw["error"])
        return out
    members = _kgr_plain_names(raw.get("members"))
    side = raw.get("side")
    confirmed = raw.get("confirmed")
    if members is None or side not in _KGR_SIDES or not isinstance(confirmed, bool):
        out["error"] = "the listener's answer for this group carried no usable members, side or confirmation, so it was not read"
        return out
    out.update(side=side, fontlab_side=_kgr_text(raw.get("fontlab_side"), 60), members=members, member_count=len(members))
    gid = raw.get("id")
    out["id"] = gid if isinstance(gid, int) and not isinstance(gid, bool) else None
    out["confirmed"] = confirmed and side != "unknown"
    if not out["confirmed"]:
        out["mismatch"] = (_kgr_text(raw.get("mismatch")) or ("FontLab gave a side this tool does not know (fontlab_side)" if side == "unknown"
                                                              else "the listener did not say why this group is not confirmed"))
        other = _kgr_plain_names(raw.get("class_list_members"))
        if other is not None:
            out["class_list_members"] = other
    return out


def _kgr_glyph_entry(raw: Any, expected: str) -> dict:
    out: dict = {"name": expected}
    if not isinstance(raw, dict) or raw.get("name") != expected:
        out["error"] = "the listener's answer for this glyph was unusable or for another glyph, so it was not read"
        return out
    if _kgr_text(raw.get("error")):
        out["error"] = _kgr_text(raw["error"])
        return out
    holders = raw.get("kerning_groups")
    if not isinstance(holders, list):
        out["error"] = "the listener's answer for this glyph carried no list of kerning groups, so it was not read"
        return out
    clean = []
    for h in holders:
        if (not isinstance(h, dict) or not isinstance(h.get("group"), str) or not h["group"].isprintable() or not 1 <= len(h["group"]) <= 200
                or h.get("side") not in _KGR_SIDES or not isinstance(h.get("confirmed"), bool)):
            out["error"] = "the listener's answer for this glyph named a kerning group in an unusable form, so it was not read"
            return out
        clean.append({"group": h["group"], "side": h["side"], "confirmed": h["confirmed"] and h["side"] != "unknown"})
    out["kerning_groups"] = clean
    if not clean:
        out["note"] = "in no kerning group on either side"
    return out


def read_kerning_groups(groups: Any = None, glyphs: Any = None, all_groups: Any = None, confirmed_large_read: Any = None) -> dict:
    """v0.75 (listener 0.190, P1.6): the current master's kerning groups through POST /kerning/groups."""
    for label, flag in (("all_groups", all_groups), ("confirmed_large_read", confirmed_large_read)):
        if flag is not None and not isinstance(flag, bool):
            raise ToolError(f"{label} must be true or false (or left out).")
    group_names = _kgr_name_list(groups, "groups")
    glyph_names = _kgr_name_list(glyphs, "glyphs")
    if all_groups is True and (group_names or glyph_names):
        raise ToolError("Give either all_groups=true alone, or names in groups and / or glyphs, not both.")
    if all_groups is not True and not group_names and not glyph_names:
        raise ToolError("Give all_groups=true, or at least one name in groups (kerning group names) or glyphs (glyph names).")
    named = len(group_names) + len(glyph_names)
    if named > _KERN_CONFIRM_ABOVE and confirmed_large_read is not True:
        raise ToolError(
            f"This request names {named} groups and glyphs, more than the {_KERN_CONFIRM_ABOVE} threshold, and nothing was read. "
            "Do NOT repeat the call yet. A large read costs many tokens: tell the person how many you want to read and why, and ask whether they approve. "
            "Only after they have said yes, call get_kerning_groups again with the same arguments and confirmed_large_read=true. Never set that flag without the person's approval.")
    _require_listener((0, 190), "get_kerning_groups")
    payload: dict = {"all_groups": True} if all_groups is True else {"groups": group_names, "glyphs": glyph_names}
    if confirmed_large_read is True:
        payload["confirmed_large_read"] = True
    data = _call_listener_post("/kerning/groups", payload, timeout=max(TIMEOUT_SECONDS, 5.0 + named / 50.0, 10.0 if all_groups else 0.0))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        reason = data["error"][:600].rstrip()
        raise ToolError(f"Kerning groups could not be read: {reason}" + ("" if reason.endswith((".", "!", "?")) else "."))
    count = data.get("group_count")
    count = count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None
    if all_groups is True and data.get("needs_confirmation") is True:
        raise ToolError(
            f"The current master has {count if count is not None else 'more than ' + str(_KERN_CONFIRM_ABOVE)} kerning groups, more than the "
            f"{_KERN_CONFIRM_ABOVE}-group threshold, and their members were not read. Do NOT repeat the call yet. Tell the person how many groups there are, "
            "that listing them all with their members costs many tokens, and ask whether they approve. Only after they have said yes, call get_kerning_groups "
            "again with all_groups=true and confirmed_large_read=true. Never set that flag without the person's approval.")
    raw_groups, raw_glyphs = data.get("groups"), data.get("glyphs")
    if (not isinstance(raw_groups, list) or not isinstance(raw_glyphs, list)
            or (all_groups is not True and (len(raw_groups) != len(group_names) or len(raw_glyphs) != len(glyph_names)))
            or (all_groups is True and raw_glyphs)):
        raise ToolError("Kerning groups could not be read: the listener's answer did not match the request. Nothing was changed.")
    if all_groups is True:
        clean_groups = [_kgr_group_entry(r, None) for r in raw_groups]
        large = len(clean_groups) > _KERN_CONFIRM_ABOVE
    else:
        clean_groups = [_kgr_group_entry(r, e) for r, e in zip(raw_groups, group_names)]
        large = named > _KERN_CONFIRM_ABOVE
    clean_glyphs = [_kgr_glyph_entry(r, e) for r, e in zip(raw_glyphs, glyph_names)]
    fonts_open, matched_by, family = data.get("fonts_open"), data.get("matched_by"), data.get("family_name")
    master, master_count, size = data.get("master"), data.get("master_count"), data.get("table_size")
    cross = data.get("cross_check")
    reply = {"mode": "all" if all_groups is True else "named",
             "fonts_open": fonts_open if isinstance(fonts_open, int) and not isinstance(fonts_open, bool) and fonts_open >= 1 else None,
             "matched_by": matched_by if matched_by in ("only font", "path") else None,
             "family_name": family if isinstance(family, str) and 1 <= len(family) <= 63 and family.isprintable() else None,
             "master": master if isinstance(master, str) and 1 <= len(master) <= 63 and master.isprintable() else None,
             "master_count": master_count if isinstance(master_count, int) and not isinstance(master_count, bool) and master_count >= 1 else None,
             "group_count": count,
             "cross_check": "done" if cross == "done" else (_kgr_text(cross) or "unknown"),
             "groups": clean_groups, "glyphs": clean_glyphs,
             "errors": sum(1 for e in clean_groups + clean_glyphs if "error" in e),
             "unconfirmed": sum(1 for e in clean_groups if e.get("confirmed") is False),
             "member_names": sum(e.get("member_count", 0) for e in clean_groups)}
    instruction = _KGR_INSTRUCTION
    if large:
        reply["large_read_confirmed"] = True
    if reply["cross_check"] != "done":
        instruction += " The cross-check with FontLab's class list did not run (cross_check says why), so no group is confirmed: say so."
    if reply["group_count"] == 0:
        instruction += " group_count is 0: the current master has no kerning groups at all."
    for key in ("malformed_entries", "duplicate_names"):
        got = data.get(key)
        if (key == "malformed_entries" and isinstance(got, int) and not isinstance(got, bool) and got > 0) or (key == "duplicate_names" and _kgr_plain_names(got)):
            reply[key] = got
            instruction += f" FontLab's answer had {key.replace('_', ' ')} ({got}): tell the person that some groups may be missing or doubtful."
    if reply["fonts_open"] is not None and reply["fonts_open"] > 1:
        which = f" ({reply['family_name']})" if reply["family_name"] else ""
        instruction += (f" {reply['fonts_open']} fonts are open in FontLab; this was read from the current one, the font whose window is in front{which}, "
                        "matched to its kerning table by its file path. Say which font when you report the groups.")
    if reply["master_count"] is not None and reply["master_count"] > 1:
        instruction += f" This font has {reply['master_count']} masters; only the current one was read. Say so when you report the groups."
    if data.get("side_effect_detected") is True:
        reply["side_effect_detected"] = True
        instruction += " WARNING: the size of the kerning table or of its groups changed while reading, which a read must never do. Tell the person."
    reply["agent_instruction"] = instruction
    return reply


_SIDEBEARINGS_COMPONENT_NOTE = ("If other glyphs use this glyph as a component, they may not follow this change (seen live): get_glyph_outline on such a "
                                "glyph says source_in_step. A real edit of this glyph in FontLab has brought them back in step.")


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
        "component_note": _SIDEBEARINGS_COMPONENT_NOTE,
    }
    if data.get("display_note"):
        result["display_note"] = data["display_note"]
    _add_guard_fields(result, data)
    _mark_modified(result, bool(data.get("changed")))
    return result


_POLY_LIMITS = (3, 500)


_KERN_NOT_MARKED = "(2) FontLab does not count it as a change: closing the font asks no save question and loses the pair silently."
# v0.54 (listener 0.134): says what was done, never that FontLab's icon changed or that it will ask (research 713-717)
_KERN_MARKED = ("(2) FontLab was told that the font changed, through one glyph of a changed pair, whose content did not change (fontlab_changed_mark, "
                "via_glyph); the pair is still lost if the font is closed without saving.")
_KERN_NO_CHANGE = "(2) This request changed no entry, so it adds nothing that needs saving."        # v0.55 (live 720)
# v0.55, the policy of 2026-11-10 (DECISIONS.md): FontLab's changed icon is not reliably immediate after a kerning write (719, 722, 723, 725, 726; blue at once
# only in 724), and no reading follows the icon. False retires the note, after the live test the policy names, with its own DECISIONS.md entry.
# v0.57: retired. With the panel refresh of listener 0.136 / server 0.56 five runs in a row were blue at once, new and changed pairs, the mouse outside FontLab (749-753).
_ICON_MAY_LAG_KERNING = False
_KERN_ICON_LAG = (" (4) FontLab's display can lag: the changed icon before the font's name may stay dark until the mouse moves near the font's title, "
                  "which can make FontLab redraw it. A dark icon does not mean the change failed. Tell the person this once per package of changes.")
_KERN_PANEL_STALE = ("(1) FontLab applies the value in text at once, but its KERNING panel does not show it "
                     "yet: a new pair is missing from the panel and a pair it already lists keeps its old value, until the person switches to "
                     "another open font and back (with one font open: File > New Font, then back to this font's tab; the new font can be closed "
                     "without saving) or saves and reopens the font.")
# v0.56 (listener 0.136): says what was done, never what the panel shows; no reading follows the panel (738, 741-743)
_KERN_PANEL_ASKED = ("(1) FontLab applies the value in text at once, and it was asked to refresh its KERNING panel (fontlab_panel_refresh). If the panel "
                     "does not show a new pair or a new value, switching to another open font and back (with one font open: File > New Font, then back "
                     "to this font's tab; the new font can be closed without saving) or saving and reopening the font makes it show them.")
_KERN_PANEL_NO_CHANGE = "(1) The value was already set, so FontLab was not asked to refresh its KERNING panel."        # v0.57 (live 746)
_KERN_SET_INSTRUCTION = (
    "Each pair marked set was written as a glyph : glyph entry in the current master's kerning table (master names it) and verified "
    "by re-reading it. 'before' is the value FontLab applied before, with its source; 'after' is the value now. exception_over_class "
    "true means the pair had a class value before: the new entry is an exception for these two glyphs only. Tell the person these "
    "facts about kerning written this way: {panel} {save} (3) Edit > Undo cannot take it back; to revert, if 'before' was a glyph : glyph "
    "entry call set_kerning again with that value; if it was 'none' or a class value, call remove_kerning to remove the new glyph : glyph "
    "entry and restore the prior state.{lag} Setting a pair to 0 leaves an explicit zero entry; remove_kerning removes the glyph : glyph entry. "
    "Other masters, classes and feature-based kerning were not changed."
)
_KERN_SET_CLASS_NOTE = (
    " A pair with 'kind' has a kerning class side ('@name'): its entry is of that kind, and FontLab applies the value to every glyph pair of "
    "the classes' members that has no exception of its own ('classes' gives each class's side and member_count; those glyph pairs were not "
    "read). For such a pair 'before' and 'after' belong to ONE sample glyph pair ('sample'): sample_verdict 'applied' means the sample now "
    "takes the new value; 'covered' means the sample has an exception of its own, which still applies to it, and the class entry itself was "
    "confirmed by re-reading it; 'no sample' means no member of a class is a glyph of the font, so only the entry itself was re-read. Tell the "
    "person how far a class value reaches. To revert a class entry: if entry_before is a number, call set_kerning with that value for the "
    "same '@' pair; if it is null, call remove_kerning for the same '@' pair."
)


def _kern_set_items(pairs: Any) -> list:
    """The pairs as a clean list of (left, right, value), or a ToolError (before anything is sent)."""
    if not isinstance(pairs, (list, tuple)) or len(pairs) < 1:
        raise ToolError("pairs must be a list of at least one [left, right, value] item, for example [[\"A\", \"V\", -60]].")
    clean, seen = [], set()
    for i, item in enumerate(pairs):
        if (not isinstance(item, (list, tuple)) or len(item) != 3
                or not all(_kern_side_name(n) is not None for n in item[:2])):
            raise ToolError(f"pair {i + 1} must be [left, right, value]: two sides and a number (got {item!r}). {_KERN_SIDE_HINT}")
        value = item[2]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or abs(value) == float("inf"):
            raise ToolError(f"pair {i + 1} ({item[0].strip()}:{item[1].strip()}): the value must be a number in font units.")
        if value != int(value):
            # v0.45: FontLab stores kerning in whole units, rounded to the nearest, halves away from zero (live 567-569)
            raise ToolError(f"pair {i + 1} ({item[0].strip()}:{item[1].strip()}): FontLab keeps kerning in whole font units, so {value} "
                            "would not be stored as given; give a whole number. Nothing was changed.")
        left, right = item[0].strip(), item[1].strip()
        if (left, right) in seen:
            raise ToolError(f"pair {i + 1} ({left}:{right}) is given more than once; give each pair once. Nothing was changed.")
        seen.add((left, right))
        clean.append((left, right, value))
    return clean


def _kern_set_side(raw: Any, left: str, right: str) -> dict:
    """A 'before' or 'after' value from the listener, checked like a read result: value, kerned, source and class names, or error."""
    entry = _kern_entry(dict(raw, left=left, right=right) if isinstance(raw, dict) else raw, (left, right))
    entry.pop("left", None)
    entry.pop("right", None)
    return entry


def write_kerning(pairs: Any, confirmed_large_write: Any = None) -> dict:
    if confirmed_large_write is not None and not isinstance(confirmed_large_write, bool):
        raise ToolError("confirmed_large_write must be true or false (or left out).")
    wanted = _kern_set_items(pairs)
    large = len(wanted) > _KERN_CONFIRM_ABOVE
    if large and confirmed_large_write is not True:
        raise ToolError(
            f"This request would set {len(wanted)} kerning pairs, more than the {_KERN_CONFIRM_ABOVE}-pair threshold, and nothing was changed. "
            "Do NOT repeat the call yet. Tell the person how many pairs you want to set and why, and ask whether they approve. "
            "Only after they have said yes, call set_kerning again with the same arguments and confirmed_large_write=true. Never set that flag without the person's approval.")
    if any(nm.startswith("@") for a, b, _v in wanted for nm in (a, b)):
        _require_listener((0, 194), "set_kerning with a kerning class side ('@name')")
    else:
        _require_listener((0, 124), "set_kerning")
    data = _write_post("/kerning/set", {"pairs": [[a, b, v] for a, b, v in wanted]}, timeout=max(TIMEOUT_SECONDS, 5.0 + len(wanted) / 25.0))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        refusal = data["error"][:600].rstrip(" .")
        raise ToolError(f"Kerning was NOT set: {refusal}." + ("" if refusal.endswith("nothing was set") else " Nothing was changed."))
    raw_results = data.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(wanted):
        _note_change(sure=False)
        raise ToolError(f"The listener's answer to set_kerning did not match the request, so it is not known which pairs were set. {_UNSURE_NOTE}")
    results, changed, unsure = [], False, False
    for raw, (left, right, value) in zip(raw_results, wanted):
        raw = raw if isinstance(raw, dict) else {}
        entry = {"left": left, "right": right, "requested": _tidy_number(value)}
        if raw.get("left") != left or raw.get("right") != right:
            unsure = True
            entry.update(status="unknown", reason="the listener answered for a different pair, so whether this pair was set is not known")
            results.append(entry)
            continue
        status = raw.get("status")
        if status == "not attempted":
            entry["status"] = status
            results.append(entry)
            continue
        kind, sample, problem = _kern_kind(left, right), (left, right), None
        if kind != "glyph : glyph":               # v0.78: 'before' and 'after' belong to the sample glyph pair
            entry["kind"] = kind
            fields, sample, problem = _kern_class_fields(raw, left, right)
            entry.update(fields)
        if sample is not None and "before" in raw:
            entry["before"] = _kern_set_side(raw.get("before"), *sample)
        if sample is not None and "after" in raw:
            entry["after"] = _kern_set_side(raw.get("after"), *sample)
        if kind == "glyph : glyph":
            verified = (raw.get("set") is True and status == "set" and raw.get("changed") in (True, False)
                        and isinstance(entry.get("after"), dict) and entry["after"].get("source") == "glyph : glyph" and entry["after"].get("value") == _tidy_number(value))
        else:
            verdict = raw.get("sample_verdict")
            sample_ok = ((verdict == "no sample" and "sample" in entry and entry["sample"] is None and "after" not in raw)
                         or (sample is not None and _kern_sample_ok(kind, left, right, _tidy_number(value), entry.get("after"), verdict)))
            verified = problem is None and raw.get("set") is True and status == "set" and raw.get("changed") in (True, False) and sample_ok
            if verdict in ("applied", "covered", "no sample"):
                entry["sample_verdict"] = verdict
        entry["status"] = "set" if verified else "failed"
        entry["changed"] = raw.get("changed") if raw.get("changed") in (True, False) else None
        if raw.get("exception_over_class") is True and verified:
            entry["exception_over_class"] = True
        if not verified:
            reason = raw.get("reason")
            entry["reason"] = (reason[:600] if isinstance(reason, str) and reason else
                               (problem or "the listener did not confirm this pair by re-reading it"))
            if isinstance(raw.get("call_error"), str):
                entry["call_error"] = raw["call_error"][:300]
        note = _kern_same_name_note(raw, left, right, "written")
        if note:
            entry["note"] = note
        if entry["changed"] is True:
            changed = True
        elif entry["changed"] is None and status != "not attempted" and "after" in raw:
            unsure = True
        results.append(entry)
    set_count = sum(1 for e in results if e["status"] == "set")
    upm, master, master_count = data.get("units_per_em"), data.get("master"), data.get("master_count")
    fonts_open, family, matched_by = data.get("fonts_open"), data.get("family_name"), data.get("matched_by")
    size_before, size_after = data.get("table_size_before"), data.get("table_size_after")
    reply = {"fonts_open": fonts_open if isinstance(fonts_open, int) and not isinstance(fonts_open, bool) and fonts_open >= 1 else None,
             "matched_by": matched_by if matched_by in ("only font", "path") else None,
             "family_name": family if isinstance(family, str) and 1 <= len(family) <= 63 and family.isprintable() else None,
             "master": master if isinstance(master, str) and 1 <= len(master) <= 63 and master.isprintable() else None,
             "master_count": master_count if isinstance(master_count, int) and not isinstance(master_count, bool) and master_count >= 1 else None,
             "units_per_em": _tidy_number(upm) if isinstance(upm, (int, float)) and not isinstance(upm, bool) else None,
             "count": len(results), "set_count": set_count,
             "table_size_before": size_before if isinstance(size_before, int) and not isinstance(size_before, bool) else None,
             "table_size_after": size_after if isinstance(size_after, int) and not isinstance(size_after, bool) else None,
             "results": results}
    if unsure:
        _note_change(sure=False)
    if set_count < len(results):
        done = ", ".join(f"{e['left']}:{e['right']}" for e in results if e["status"] == "set") or "none"
        failed = next((e for e in results if e["status"] in ("failed", "unknown")), None)
        holds = ""
        if failed and failed.get("changed") is True and isinstance(failed.get("after"), dict) and "value" in failed["after"]:
            if "kind" in failed and isinstance(failed.get("sample"), dict):        # v0.78: 'after' belongs to the sample glyph pair
                holds = f"; its sample pair {failed['sample']['left']}:{failed['sample']['right']} now kerns at {failed['after']['value']}"
            else:
                holds = f"; the entry now holds {failed['after']['value']}"
        where = f" It stopped at {failed['left']}:{failed['right']}: {failed.get('reason')}{holds}." if failed else ""
        skipped = sum(1 for e in results if e["status"] == "not attempted")
        tail = f" {skipped} pair(s) after it were not attempted." if skipped else ""
        if changed:
            _note_change()
            raise ToolError(f"Kerning was set for {set_count} of {len(results)} pairs (set: {done}).{where}{tail} The values that were set are "
                            f"listed by get_kerning. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Kerning was NOT set for all pairs (set: {done}).{where}{tail}" + (f" {_UNSURE_NOTE}" if unsure else " Nothing was changed."))
    _add_guard_fields(reply, data)        # v0.54: fontlab_changed_mark, type-checked; the old warning stays unless the mark was made
    mark = reply.get("fontlab_changed_mark")
    marked = isinstance(mark, dict) and mark.get("called") is True and not mark.get("call_error")
    point2 = _KERN_MARKED if marked else (_KERN_NOT_MARKED if changed else _KERN_NO_CHANGE)        # v0.55: reached only when every pair was verified, so changed is known
    panel = data.get("fontlab_panel_refresh")        # v0.56 (listener 0.136), type-checked; never claims what the panel shows
    if isinstance(panel, dict) and isinstance(panel.get("called"), bool):
        reply["fontlab_panel_refresh"] = {"called": panel["called"]}
        for key in ("reason", "call_error"):
            if isinstance(panel.get(key), str) and panel[key]:
                reply["fontlab_panel_refresh"][key] = panel[key]
    forwarded = reply.get("fontlab_panel_refresh")
    refreshed = isinstance(forwarded, dict) and forwarded.get("called") is True and not forwarded.get("call_error")
    point1 = _KERN_PANEL_ASKED if refreshed else (_KERN_PANEL_STALE if changed else _KERN_PANEL_NO_CHANGE)        # v0.57: reached only when every pair was verified
    instruction = (_KERN_SET_INSTRUCTION.replace("{panel}", point1).replace("{save}", point2)
                   .replace("{lag}", _KERN_ICON_LAG if marked and _ICON_MAY_LAG_KERNING else ""))
    if any("kind" in e for e in results):        # v0.78: a request with a kerning class side
        instruction = (instruction.replace("was written as a glyph : glyph entry", "was written as an entry of its kind (glyph : glyph unless 'kind' says otherwise)")
                       .replace("to revert, if 'before' was", "to revert a glyph pair, if 'before' was")        # v0.79: 'before' of a class pair is its sample's (CK 1421)
                       .replace("entry and restore the prior state.", "entry and restore the prior state; a class pair: see below.")
                       .replace("Other masters, classes and feature-based kerning were not changed.", "Other masters, other kerning entries and feature-based kerning were not changed.")
                       + _KERN_SET_CLASS_NOTE)
    if any("note" in e for e in results):
        instruction += " Pass on every pair's 'note' to the person."
    if reply["fonts_open"] is not None and reply["fonts_open"] > 1:
        which = f" ({reply['family_name']})" if reply["family_name"] else ""
        instruction += (f" {reply['fonts_open']} fonts are open in FontLab; this changed the current one, the font whose window is in front{which}, "
                        "matched to its kerning table by its file path. Say which font when you report it.")
    if reply["master_count"] is not None and reply["master_count"] > 1:
        instruction += f" This font has {reply['master_count']} masters; only the current one was changed. Say so."
    if data.get("table_size_as_expected") is False:
        reply["table_size_unexpected"] = True
        instruction += (" WARNING: the kerning table grew by a different number of entries than the pairs that were new. "
                        "Tell the person and do not make further kerning edits until they have looked.")
    if large:
        reply["large_write_confirmed"] = True
    reply["agent_instruction"] = instruction
    _mark_modified(reply, changed)
    return reply


# v0.76 (listener 0.192): remove_kerning, the design of 2026-11-19 (DECISIONS.md; research KD 1380-1390, KDC 1391-1397)
_KERN_RM_PANEL_ASKED = ("(1) FontLab no longer applies the removed entries, and it was asked to refresh its KERNING panel (fontlab_panel_refresh). If the "
                        "panel still lists a removed pair, switching to another open font and back (with one font open: File > New Font, then back to "
                        "this font's tab; the new font can be closed without saving) or saving and reopening the font makes it drop it.")
_KERN_RM_PANEL_STALE = ("(1) FontLab no longer applies the removed entries, but its KERNING panel may still list them until the person switches to another "
                        "open font and back (with one font open: File > New Font, then back to this font's tab; the new font can be closed without "
                        "saving) or saves and reopens the font.")
_KERN_RM_PANEL_NO_CHANGE = "(1) Nothing was removed, so FontLab was not asked to refresh its KERNING panel."
_KERN_RM_MARKED = ("(2) FontLab was told that the font changed, through one glyph of a removed pair, whose content did not change (fontlab_changed_mark, "
                   "via_glyph); the removal is still lost if the font is closed without saving.")
_KERN_RM_NOT_MARKED = "(2) FontLab does not count it as a change: closing the font asks no save question and loses the removal silently."
_KERN_RM_INSTRUCTION = (
    "Each pair marked removed had a glyph : glyph entry in the current master's kerning table (master names it); the entry was removed and "
    "the removal verified by re-reading it (the entry is gone and the table holds one entry fewer). 'before' is the value FontLab applied "
    "before, with its source; 'after' is the value FontLab applies now, with its source. class_value_applies true means a kerning class "
    "still kerns the pair: it now kerns at that class value, NOT at 0; say so. A pair marked 'no entry' had no glyph : glyph entry, so "
    "nothing was removed for it; its note says whether a class still kerns it (this tool never removes class kerning). Tell the person "
    "these facts: {panel} {save} (3) Edit > Undo is not known to bring a removed pair back; to restore one, call set_kerning with its "
    "'before' value. Other masters, classes and feature-based kerning were not changed."
)
_KERN_RM_CLASS_NOTE = (
    " A pair with 'kind' has a kerning class side ('@name'): the entry removed was of that kind, and its value no longer applies to any glyph "
    "pair of the classes' members ('classes' gives each class's side and member_count; those glyph pairs were not read). For such a pair "
    "'before' and 'after' belong to ONE sample glyph pair ('sample'), so they show what applies to that pair now. To restore a removed class "
    "entry, call set_kerning with the same '@' pair and the value it held (entry_before when the reply gives it)."
)


def _kern_rm_items(pairs: Any) -> list:
    """The pairs as a clean list of (left, right), or a ToolError (before anything is sent)."""
    if not isinstance(pairs, (list, tuple)) or len(pairs) < 1:
        raise ToolError("pairs must be a list of at least one [left, right] item, for example [[\"A\", \"V\"]].")
    clean, seen = [], set()
    for i, item in enumerate(pairs):
        if (not isinstance(item, (list, tuple)) or len(item) != 2
                or not all(_kern_side_name(n) is not None for n in item)):
            raise ToolError(f"pair {i + 1} must be [left, right]: two sides (got {item!r}). {_KERN_SIDE_HINT} Nothing was changed.")
        left, right = item[0].strip(), item[1].strip()
        if (left, right) in seen:
            raise ToolError(f"pair {i + 1} ({left}:{right}) is given more than once; give each pair once. Nothing was changed.")
        seen.add((left, right))
        clean.append((left, right))
    return clean


def _kern_rm_note(before: dict) -> str:
    """The note of a pair with no glyph : glyph entry: what still kerns it, from its checked 'before' value."""
    source = before.get("source") if isinstance(before, dict) else None
    if source in ("glyph : class", "class : glyph", "class : class"):
        classes = " and ".join(before[k] for k in ("left_class", "right_class") if isinstance(before.get(k), str))
        return (f"no glyph : glyph entry, so nothing was removed; FontLab applies {before.get('value')} to this pair from the {source} entry "
                f"({classes}), which this tool does not remove")
    if source == "none":
        return "no glyph : glyph entry and no class kerns this pair, so there was nothing to remove"
    return "no glyph : glyph entry, so nothing was removed"


def _kern_rm_class_note(kind: str, left: str, right: str, sample: Any, before: Any) -> str:
    """v0.78: the note of a pair with a class side that has no entry of its kind: nothing removed, and what its sample pair kerns at."""
    text = f"no {kind} entry for {left}:{right}, so nothing was removed"
    if sample is not None and isinstance(before, dict) and "source" in before:
        text += f"; the sample pair {sample[0]}:{sample[1]} kerns at {before.get('value')} ({before.get('source')})"
    return text


def remove_kerning_write(pairs: Any, confirmed_large_write: Any = None) -> dict:
    if confirmed_large_write is not None and not isinstance(confirmed_large_write, bool):
        raise ToolError("confirmed_large_write must be true or false (or left out).")
    wanted = _kern_rm_items(pairs)
    large = len(wanted) > _KERN_CONFIRM_ABOVE
    if large and confirmed_large_write is not True:
        raise ToolError(
            f"This request would remove {len(wanted)} kerning pairs, more than the {_KERN_CONFIRM_ABOVE}-pair threshold, and nothing was changed. "
            "Do NOT repeat the call yet. Tell the person how many pairs you want to remove and why, and ask whether they approve. "
            "Only after they have said yes, call remove_kerning again with the same arguments and confirmed_large_write=true. Never set that flag without the person's approval.")
    if any(nm.startswith("@") for a, b in wanted for nm in (a, b)):
        _require_listener((0, 194), "remove_kerning with a kerning class side ('@name')")
    else:
        _require_listener((0, 192), "remove_kerning")
    data = _write_post("/kerning/remove", {"pairs": [[a, b] for a, b in wanted]}, timeout=max(TIMEOUT_SECONDS, 5.0 + len(wanted) / 25.0))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        refusal = data["error"][:600].rstrip(" .")
        raise ToolError(f"Kerning was NOT removed: {refusal}." + ("" if refusal.endswith("nothing was removed") else " Nothing was changed."))
    raw_results = data.get("results")
    if not isinstance(raw_results, list) or len(raw_results) != len(wanted):
        _note_change(sure=False)
        raise ToolError(f"The listener's answer to remove_kerning did not match the request, so it is not known which pairs were removed. {_UNSURE_NOTE}")
    results, changed, unsure = [], False, False
    for raw, (left, right) in zip(raw_results, wanted):
        raw = raw if isinstance(raw, dict) else {}
        entry = {"left": left, "right": right}
        if raw.get("left") != left or raw.get("right") != right:
            unsure = True
            entry.update(status="unknown", reason="the listener answered for a different pair, so whether this pair was removed is not known")
            results.append(entry)
            continue
        status = raw.get("status")
        if status == "not attempted":
            entry["status"] = status
            results.append(entry)
            continue
        kind, sample, problem = _kern_kind(left, right), (left, right), None
        if kind != "glyph : glyph":               # v0.78: 'before' and 'after' belong to the sample glyph pair
            entry["kind"] = kind
            fields, sample, problem = _kern_class_fields(raw, left, right)
            entry.update(fields)
        if sample is not None and "before" in raw:
            entry["before"] = _kern_set_side(raw.get("before"), *sample)
        if sample is not None and "after" in raw:
            entry["after"] = _kern_set_side(raw.get("after"), *sample)
        before, after = entry.get("before"), entry.get("after")
        same_name = _kern_same_name_note(raw, left, right, "taken")
        if kind == "glyph : glyph":
            no_entry = isinstance(before, dict) and "error" not in before and before.get("source") != "glyph : glyph"
        else:
            no_entry = problem is None and (sample is None or (isinstance(before, dict) and "error" not in before))
        if status == "no entry" and raw.get("removed") is False and raw.get("changed") is False and "after" not in raw and no_entry:
            note = _kern_rm_note(before) if kind == "glyph : glyph" else _kern_rm_class_note(kind, left, right, sample, before)
            entry.update(status="no entry", changed=False, note=note + (" " + same_name if same_name else ""))
            results.append(entry)
            continue
        if kind == "glyph : glyph":
            gone = isinstance(after, dict) and "error" not in after and after.get("source") != "glyph : glyph"
        else:
            gone = problem is None and ((sample is None and "after" not in raw) or (
                isinstance(after, dict) and "error" not in after and not (
                    after.get("source") == kind and (not left.startswith("@") or after.get("left_class") == left[1:])
                    and (not right.startswith("@") or after.get("right_class") == right[1:]))))
        verified = raw.get("removed") is True and status == "removed" and raw.get("changed") is True and gone
        entry["status"] = "removed" if verified else "failed"
        entry["changed"] = raw.get("changed") if raw.get("changed") in (True, False) else None
        if verified and isinstance(after, dict) and after.get("source") in ("glyph : class", "class : glyph", "class : class"):
            entry["class_value_applies"] = True
        if not verified:
            reason = raw.get("reason")
            entry["reason"] = (reason[:600] if isinstance(reason, str) and reason else
                               (problem or "the listener did not confirm this removal by re-reading it"))
            if isinstance(raw.get("call_error"), str):
                entry["call_error"] = raw["call_error"][:300]
        if same_name:
            entry["note"] = same_name
        if entry["changed"] is True:
            changed = True
        elif entry["changed"] is None and "after" in raw:
            unsure = True
        results.append(entry)
    removed_count = sum(1 for e in results if e["status"] == "removed")
    no_entry_count = sum(1 for e in results if e["status"] == "no entry")
    master, master_count = data.get("master"), data.get("master_count")
    fonts_open, family, matched_by = data.get("fonts_open"), data.get("family_name"), data.get("matched_by")
    size_before, size_after = data.get("table_size_before"), data.get("table_size_after")
    reply = {"fonts_open": fonts_open if isinstance(fonts_open, int) and not isinstance(fonts_open, bool) and fonts_open >= 1 else None,
             "matched_by": matched_by if matched_by in ("only font", "path") else None,
             "family_name": family if isinstance(family, str) and 1 <= len(family) <= 63 and family.isprintable() else None,
             "master": master if isinstance(master, str) and 1 <= len(master) <= 63 and master.isprintable() else None,
             "master_count": master_count if isinstance(master_count, int) and not isinstance(master_count, bool) and master_count >= 1 else None,
             "count": len(results), "removed_count": removed_count, "no_entry_count": no_entry_count,
             "table_size_before": size_before if isinstance(size_before, int) and not isinstance(size_before, bool) else None,
             "table_size_after": size_after if isinstance(size_after, int) and not isinstance(size_after, bool) else None,
             "results": results}
    if unsure:
        _note_change(sure=False)
    if removed_count + no_entry_count < len(results):
        done = ", ".join(f"{e['left']}:{e['right']}" for e in results if e["status"] == "removed") or "none"
        failed = next((e for e in results if e["status"] in ("failed", "unknown")), None)
        holds = ""
        if failed and isinstance(failed.get("after"), dict) and "value" in failed["after"]:
            holds = f"; FontLab now applies {failed['after']['value']} ({failed['after'].get('source')})"
            if "kind" in failed and isinstance(failed.get("sample"), dict):        # v0.78: 'after' belongs to the sample glyph pair
                holds = f"; its sample pair {failed['sample']['left']}:{failed['sample']['right']} now kerns at {failed['after']['value']} ({failed['after'].get('source')})"
        where = f" It stopped at {failed['left']}:{failed['right']}: {failed.get('reason')}{holds}." if failed else ""
        skipped = sum(1 for e in results if e["status"] == "not attempted")
        tail = f" {skipped} pair(s) after it were not attempted." if skipped else ""
        if changed:
            _note_change()
            raise ToolError(f"Kerning was removed for {removed_count} of {len(results)} pairs (removed: {done}).{where}{tail} Check the pairs with "
                            f"get_kerning. {_CHANGED_BY_ERROR_NOTE}")
        raise ToolError(f"Kerning was NOT removed for all pairs (removed: {done}).{where}{tail}" + (f" {_UNSURE_NOTE}" if unsure else " Nothing was changed."))
    _add_guard_fields(reply, data)
    mark = reply.get("fontlab_changed_mark")
    marked = isinstance(mark, dict) and mark.get("called") is True and not mark.get("call_error")
    point2 = _KERN_RM_MARKED if marked else (_KERN_RM_NOT_MARKED if changed else _KERN_NO_CHANGE)
    panel = data.get("fontlab_panel_refresh")
    if isinstance(panel, dict) and isinstance(panel.get("called"), bool):
        reply["fontlab_panel_refresh"] = {"called": panel["called"]}
        for key in ("reason", "call_error"):
            if isinstance(panel.get(key), str) and panel[key]:
                reply["fontlab_panel_refresh"][key] = panel[key]
    forwarded = reply.get("fontlab_panel_refresh")
    refreshed = isinstance(forwarded, dict) and forwarded.get("called") is True and not forwarded.get("call_error")
    point1 = _KERN_RM_PANEL_ASKED if refreshed else (_KERN_RM_PANEL_STALE if changed else _KERN_RM_PANEL_NO_CHANGE)
    instruction = _KERN_RM_INSTRUCTION.replace("{panel}", point1).replace("{save}", point2)
    if any("kind" in e for e in results):        # v0.78: a request with a kerning class side
        instruction = (instruction.replace("had a glyph : glyph entry", "had an entry of its kind (glyph : glyph unless 'kind' says otherwise)")
                       .replace("had no glyph : glyph entry, so", "had no entry of its kind, so")        # v0.79: CK 1430
                       .replace("to restore one, call set_kerning with its 'before' value.",
                                "to restore a glyph pair, call set_kerning with its 'before' value; a class pair: see below.")        # v0.79: CK 1429
                       .replace("(this tool never removes class kerning)", "(class kerning is removed only for a pair written with '@')")
                       .replace("Other masters, classes and feature-based kerning were not changed.", "Other masters, other kerning entries and feature-based kerning were not changed.")
                       + _KERN_RM_CLASS_NOTE)
    if any("note" in e and e["status"] != "no entry" for e in results):
        instruction += " Pass on every pair's 'note' to the person."
    if reply["fonts_open"] is not None and reply["fonts_open"] > 1:
        which = f" ({reply['family_name']})" if reply["family_name"] else ""
        instruction += (f" {reply['fonts_open']} fonts are open in FontLab; this changed the current one, the font whose window is in front{which}, "
                        "matched to its kerning table by its file path. Say which font when you report it.")
    if reply["master_count"] is not None and reply["master_count"] > 1:
        instruction += f" This font has {reply['master_count']} masters; only the current one was changed. Say so."
    if data.get("table_size_as_expected") is False:
        reply["table_size_unexpected"] = True
        instruction += (" WARNING: the kerning table shrank by a different number of entries than the pairs that were removed. "
                        "Tell the person and do not make further kerning edits until they have looked.")
    if large:
        reply["large_write_confirmed"] = True
    reply["agent_instruction"] = instruction
    _mark_modified(reply, changed)
    return reply


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


# v0.82 (listener 0.200): rename_kerning_group and remove_kerning_group, the design of 2026-11-20 (DECISIONS.md; research GE0 1499-1504,
# GE 1505-1522, GR 1523-1529, GL 1530-1534, GK 1535-1545, mental-model/topics/kerning.md section 18).

_KGE_COMMON = (
    "FontLab was told that the font changed through one member glyph, whose content did not change (fontlab_changed_mark), and asked to refresh "
    "its panels (fontlab_panel_refresh); fontlab_caught_up says whether one member glyph already carries the group's new state. If caught_up is "
    "not true, tell the person that FontLab's Classes and KERNING panels, and get_kerning for the group's members, may show the old state until "
    "they switch to another open font and back (with one font open: File > New Font, then back to this font's tab; the new font can be closed "
    "without saving). Whether FontLab asks to save after a group edit alone was not tested: do not promise it. Edit > Undo was not tested for "
    "this either. Only the current master's kerning groups are covered.")
_KGE_RENAME_INSTRUCTION = (
    "The kerning group was renamed in the current master (master names it) and verified by re-reading both of FontLab's sources: the same "
    "members and side under the new name. Its kerning entries follow the new name. FontLab gives a renamed group a NEW id (id_before, id_after): "
    "that is expected, not an error. To undo, rename it back. In set_kerning and remove_kerning the group is now '@' + new_name. " + _KGE_COMMON)
_KGE_SAME_NAME_GLYPH = (
    " new_name is also the name of a glyph of the font (same_name_glyph; FontLab itself names classes after a member): in set_kerning and "
    "remove_kerning '@{n}' means the group and '{n}' the glyph. Tell the person.")
_KGE_REMOVE_INSTRUCTION = (
    "The kerning group was removed from the current master (master names it) after the person answered Yes in FontLab, and verified by "
    "re-reading both of FontLab's sources. {fate} The kerning entries themselves were not read: table_size_before and table_size_after give "
    "the number of entries in the table. NO Glyphbridge tool can bring a removed group back (the person can make it again in FontLab's "
    "Classes panel, and its kerning would have to be set again). " + _KGE_COMMON)
_KGE_KEEP = (
    "pairs was 'keep': FontLab kept its kerning by turning each class entry into entries of its members, with the same values (seen live): a "
    "class : glyph or glyph : class entry became one glyph pair per member, a class : class entry became one class : glyph (or glyph : class) "
    "entry per member of the removed group, and member pairs that already had a glyph entry kept it. Tell the person that the kerning still "
    "applies, now as separate entries, so the table may have grown.")
_KGE_DELETE = "pairs was 'delete': the group's own kerning entries were deleted with it. Tell the person how many entries the table lost."


def _kge_name(value: Any, label: str) -> str:
    """A kerning group name, stripped, one leading '@' allowed (as in set_kerning); a ToolError before anything is sent otherwise."""
    if not isinstance(value, str):
        raise ToolError(f"{label} must be a kerning group name. Nothing was changed.")
    clean = value.strip()
    if clean.startswith("@"):
        clean = clean[1:]
    if not _KERN_NAME_RE.match(clean or "!"):
        raise ToolError(f"{label} must be 1 to 63 characters from A-Z a-z 0-9 . _ - (an optional leading '@' is allowed); got {value!r}. Nothing was changed.")
    return clean


def _kge_group_fields(raw: Any) -> dict:
    """The type-checked fields of one group entry from the listener (name, side, members, member_count, id, confirmed)."""
    if not isinstance(raw, dict):
        return {}
    out = {}
    if isinstance(raw.get("name"), str) and _KERN_NAME_RE.match(raw["name"]):
        out["name"] = raw["name"]
    if raw.get("side") in ("left", "right", "both", "unknown"):
        out["side"] = raw["side"]
    members = _kgr_plain_names(raw.get("members"))
    if members is not None:
        out["members"] = members
        out["member_count"] = len(members)
    if isinstance(raw.get("id"), int) and not isinstance(raw.get("id"), bool):
        out["id"] = raw["id"]
    if isinstance(raw.get("confirmed"), bool):
        out["confirmed"] = raw["confirmed"]
    return out


def _kge_common(data: dict) -> dict:
    """The font fields, the mark, the refresh and the catch-up check of a group edit's reply, type-checked."""
    master, master_count = data.get("master"), data.get("master_count")
    fonts_open, family, matched_by = data.get("fonts_open"), data.get("family_name"), data.get("matched_by")
    reply = {"fonts_open": fonts_open if isinstance(fonts_open, int) and not isinstance(fonts_open, bool) and fonts_open >= 1 else None,
             "matched_by": matched_by if matched_by in ("only font", "path") else None,
             "family_name": family if isinstance(family, str) and 1 <= len(family) <= 63 and family.isprintable() else None,
             "master": master if isinstance(master, str) and 1 <= len(master) <= 63 and master.isprintable() else None,
             "master_count": master_count if isinstance(master_count, int) and not isinstance(master_count, bool) and master_count >= 1 else None}
    for key in ("table_size_before", "table_size_after"):
        v = data.get(key)
        reply[key] = v if isinstance(v, int) and not isinstance(v, bool) else None
    _add_guard_fields(reply, data)
    panel = data.get("fontlab_panel_refresh")
    if isinstance(panel, dict) and isinstance(panel.get("called"), bool):
        reply["fontlab_panel_refresh"] = {"called": panel["called"]}
        for key in ("reason", "call_error"):
            if isinstance(panel.get(key), str) and panel[key]:
                reply["fontlab_panel_refresh"][key] = panel[key][:300]
    check = data.get("fontlab_caught_up")
    if isinstance(check, dict) and isinstance(check.get("checked"), bool):
        fwd: dict = {"checked": check["checked"]}
        if isinstance(check.get("caught_up"), bool):
            fwd["caught_up"] = check["caught_up"]
        if isinstance(check.get("glyph"), str) and _KERN_NAME_RE.match(check["glyph"]):
            fwd["glyph"] = check["glyph"]
        for key in ("group_id_read", "expected"):
            if isinstance(check.get(key), int) and not isinstance(check.get(key), bool):
                fwd[key] = check[key]
        if isinstance(check.get("reason"), str) and check["reason"]:
            fwd["reason"] = check["reason"][:300]
        reply["fontlab_caught_up"] = fwd
    else:
        reply["fontlab_caught_up"] = {"checked": False, "reason": "the listener did not report the check"}
    return reply


def _kge_instruction_tail(reply: dict) -> str:
    tail = ""
    if reply["fonts_open"] is not None and reply["fonts_open"] > 1:
        which = f" ({reply['family_name']})" if reply["family_name"] else ""
        tail += (f" {reply['fonts_open']} fonts are open in FontLab; this changed the current one, the font whose window is in front{which}, "
                 "matched to its kerning table by its file path. Say which font when you report it.")
    if reply["master_count"] is not None and reply["master_count"] > 1:
        tail += f" This font has {reply['master_count']} masters; only the current one was changed. Say so."
    return tail


def _kge_failed(data: dict, verb: str, noun: str) -> None:
    """Raise the ToolError for an edit that the re-read did not confirm, counting a change that did happen."""
    reason = _kgr_text(data.get("reason")) or "the listener did not confirm it by re-reading"
    call_error = _kgr_text(data.get("call_error"), 300)
    detail = reason.rstrip(".") + (f" (FontLab reported: {call_error})" if call_error and call_error not in reason else "")
    if data.get("changed") is True:
        _note_change()
        raise ToolError(f"The kerning group was changed, but the {noun} was NOT confirmed: {detail}. Read the groups with get_kerning_groups "
                        f"and tell the person what is there now. {_CHANGED_BY_ERROR_NOTE}")
    if data.get("changed") is False:
        raise ToolError(f"The kerning group was NOT {verb}d: {detail}. Nothing was changed.")
    _note_change(sure=False)
    raise ToolError(f"Whether the kerning group was {verb}d is not known: {detail}. {_UNSURE_NOTE}")


def rename_group_write(group: Any, new_name: Any) -> dict:
    old = _kge_name(group, "group")
    new = _kge_name(new_name, "new_name")
    if old == new:
        raise ToolError("new_name is the same as group: nothing to rename, and nothing was changed.")
    _require_listener((0, 200), "rename_kerning_group")
    data = _write_post("/kerning/group/rename", {"group": old, "new_name": new}, timeout=max(TIMEOUT_SECONDS, 10.0))
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        refusal = data["error"][:600].rstrip(" .")
        raise ToolError(f"The kerning group was NOT renamed: {refusal}." + ("" if refusal.endswith("nothing was renamed") else " Nothing was changed."))
    if data.get("group") != old or data.get("new_name") != new:
        _note_change(sure=False)
        raise ToolError(f"The listener's answer to rename_kerning_group did not match the request, so whether the group was renamed is not known. {_UNSURE_NOTE}")
    if data.get("renamed") is not True:
        _kge_failed(data, "rename", "rename")
    after = _kge_group_fields(data.get("group_after"))
    id_before, id_after = data.get("id_before"), data.get("id_after")
    id_before = id_before if isinstance(id_before, int) and not isinstance(id_before, bool) else None
    id_after = id_after if isinstance(id_after, int) and not isinstance(id_after, bool) else None
    reply = {"renamed": True, "group": old, "new_name": new, "side": after.get("side"), "member_count": after.get("member_count"),
             "members": after.get("members"), "id_before": id_before, "id_after": id_after,
             "id_changed": (id_before != id_after) if id_before is not None and id_after is not None else None,
             "same_name_glyph": data.get("same_name_glyph") is True}
    reply.update(_kge_common(data))
    instruction = _KGE_RENAME_INSTRUCTION
    if reply["same_name_glyph"]:
        instruction += _KGE_SAME_NAME_GLYPH.replace("{n}", new)
    reply["agent_instruction"] = instruction + _kge_instruction_tail(reply)
    _mark_modified(reply, True)
    return reply


def remove_group_write(group: Any, pairs: Any) -> dict:
    name = _kge_name(group, "group")
    if pairs not in ("keep", "delete"):
        raise ToolError('pairs is required and must be "keep" (the group\'s kerning stays, as entries of its members) or "delete" (its kerning '
                        'entries go with it). Ask the person which they want if they have not said. Nothing was changed.')
    _require_listener((0, 200), "remove_kerning_group")
    data = _write_post("/kerning/group/remove", {"group": name, "pairs": pairs}, timeout=DELETE_CONFIRM_TIMEOUT_SECONDS)
    if not data.get("open"):
        raise ToolError(NO_FONT)
    if isinstance(data.get("error"), str) and data["error"]:
        refusal = data["error"][:600].rstrip(" .")
        raise ToolError(f"The kerning group was NOT removed: {refusal}." + ("" if refusal.endswith("nothing was removed") else " Nothing was changed."))
    if data.get("group") != name or data.get("pairs") != pairs:
        _note_change(sure=False)
        raise ToolError(f"The listener's answer to remove_kerning_group did not match the request, so whether the group was removed is not known. {_UNSURE_NOTE}")
    if data.get("user_declined") is True and data.get("removed") is False:
        raise ToolError(f"Removal of the kerning group '{name}' was not approved in FontLab. A person needs to click Yes on the confirmation "
                        "dialog for this to proceed - this is expected behavior, not an error. Nothing was changed.")
    if data.get("removed") is not True:
        _kge_failed(data, "remove", "removal")
    before = _kge_group_fields(data.get("group_before"))
    reply = {"removed": True, "group": name, "pairs": pairs, "side": before.get("side"), "member_count": before.get("member_count"),
             "members": before.get("members"), "id": before.get("id")}
    reply.update(_kge_common(data))
    if reply["table_size_before"] is not None and reply["table_size_after"] is not None:
        reply["table_size_change"] = reply["table_size_after"] - reply["table_size_before"]
    reply["agent_instruction"] = (_KGE_REMOVE_INSTRUCTION.replace("{fate}", _KGE_KEEP if pairs == "keep" else _KGE_DELETE)
                                  + _kge_instruction_tail(reply))
    _mark_modified(reply, True)
    return reply


_POLY_MAX_CONTOURS, _POLY_MAX_TOTAL = 20, 2000
_PATH_OPEN_MIN_POINTS = 2                  # v0.47: an open contour of draw_path (listener 0.126)


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
    """The contours as clean lists of point dicts, or a ToolError (before anything is sent). v0.47: a contour given as
    {"points": [...], "closed": false} is OPEN and comes back in that form; a closed one comes back as a plain point list."""
    if not isinstance(contours, (list, tuple)) or not (1 <= len(contours) <= _POLY_MAX_CONTOURS):
        raise ToolError(f"contours must be a list of 1 to {_POLY_MAX_CONTOURS} point lists.")
    high = _POLY_LIMITS[1]
    clean, total = [], 0
    for ci, item in enumerate(contours):
        plist, closed = item, True
        if isinstance(item, dict):
            if "points" not in item or set(item) - {"points", "closed"}:
                raise ToolError(f'contour {ci}: a contour object has "points" and optionally "closed" (true or false).')
            plist, closed = item["points"], item.get("closed", True)
            if not isinstance(closed, bool):
                raise ToolError(f"contour {ci}: closed must be true or false.")
        low = _POLY_LIMITS[0] if closed else _PATH_OPEN_MIN_POINTS
        if not isinstance(plist, (list, tuple)) or not (low <= len(plist) <= high):
            raise ToolError(f"contour {ci} must be a list of {low} to {high} points" + ("." if closed else " (an open contour)."))
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
        if closed:
            if len({(p["x"], p["y"]) for p in pts}) < 3:
                raise ToolError(f"contour {ci} needs at least 3 different on-curve positions.")
            clean.append(pts)
            continue
        if len({(p["x"], p["y"]) for p in pts}) < _PATH_OPEN_MIN_POINTS:
            raise ToolError(f"contour {ci} (open) needs at least {_PATH_OPEN_MIN_POINTS} different on-curve positions.")
        if "c1" in pts[0]:
            raise ToolError(f"contour {ci} (open): the first point cannot have c1 / c2, because an open contour has no closing segment.")
        for pi in (0, len(pts) - 1):
            if pts[pi].get("smooth"):
                raise ToolError(f"contour {ci} (open) point {pi}: an end point cannot be smooth, because it has only one neighbour.")
        clean.append({"points": pts, "closed": False})
    if total > _POLY_MAX_TOTAL:
        raise ToolError(f"at most {_POLY_MAX_TOTAL} nodes in total (every curved segment adds its two control points).")
    return clean


def write_glyph_path(name: str, contours: Any) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    checked = _check_path_contours(contours)
    closed_flags = [not isinstance(c, dict) for c in checked]
    if all(closed_flags):
        _require_listener((0, 82), "draw_path")
    else:
        _require_listener((0, 126), "draw_path with open contours")

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
    if not all(closed_flags):
        open_idx = [ci for ci, f in enumerate(closed_flags) if not f]
        result["closed"] = closed_flags
        result["note"] = result["note"].replace("Closed contours of straight", "Contours of straight", 1)
        result["open_contours_note"] = (f"Contour(s) {open_idx} are OPEN (the listener read closed: false for them, before and after attaching): "
                                        "each runs from its first point to its last, with no closing segment, so it has no fill.")
        result["agent_instruction"] = _OPEN_CONTOUR_INSTRUCTION
    _add_rounding_note(result)
    for key in ("layer_created", "display_note"):
        if data.get(key) is not None:
            result[key] = data[key]
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    return result


_OPEN_CONTOUR_INSTRUCTION = ("Tell the person that the glyph has OPEN contours: they have no fill, so they are strokes or construction lines, "
                             "not filled shapes. Also tell them that in testing (FontLab 8.9.5, File > Export with the TrueType and the "
                             "OpenType PS profiles, default settings) FontLab dropped open contours from the generated font without a "
                             "warning: a glyph made only of open contours came out empty. To keep such a shape in a generated font, its "
                             "contours must be closed or turned into outlines in FontLab first. Other export settings were not tested.")

_UNI_NAME =re.compile(r"uni([0-9A-F]{4})")        # uniXXXX: exactly one codepoint, UPPERCASE hex
# ---- move_nodes (v0.63, listener 0.153): the first edit of an existing outline (P2.2; design approved by the user on 2026-11-15) ----
_MOVE_MAX = 200
_MOVE_INDEX_MAX = 5000
_MOVE_FROM_TOLERANCE = 0.001
_MOVE_UNCONFIRMED_INSTRUCTION = (
    "The re-read outline does NOT match the request, so the move is not confirmed, and the glyph may now be partly moved (see mismatches, "
    "before and after). Tell the person what happened. Do NOT move anything back on your own: only if the person agrees, call move_nodes "
    "again with the positions in 'after' as from and the ones in 'before' as to, and check that reply too.")
_MOVE_FONTLAB_LAG_NOTE = (
    "FontLab's own sidebearing numbers for this glyph may still show the old values for a while; the outline itself is moved, and the "
    "values given here are computed from its nodes.")
_MOVE_FONTLAB_LAG_INSTRUCTION = (
    "FontLab's own sidebearings and ink box for this glyph have not caught up with the move yet (fontlab_sidebearings_current is false; "
    "after an API node move they lag in FontLab 8.9.5, and no call was found that refreshes them). left, right and ink_width are computed "
    "from the re-read nodes. Tell the person person_note once, in plain words; give no steps to refresh FontLab's display.")
# v0.65 (live 1023): the mark puts the move on FontLab's undo list, but choosing Edit > Undo left the nodes moved.
_MOVE_UNDO_NOTE = (
    "FontLab's Edit > Undo lists this change as \"Glyphbridge Move Nodes\", but in testing choosing it did not move the nodes back. "
    "To take a move back, ask for the nodes to be moved back to where they were.")
_MOVE_UNDO_INSTRUCTION = "Tell the person undo_note once per conversation."


def _add_undo_note(result: dict) -> None:
    """v0.65: undo_note on a move_nodes reply whose outline changed, and one sentence at the end of its agent_instruction."""
    result["undo_note"] = _MOVE_UNDO_NOTE
    text = result.get("agent_instruction")
    result["agent_instruction"] = (text + " " + _MOVE_UNDO_INSTRUCTION) if isinstance(text, str) and text else _MOVE_UNDO_INSTRUCTION


def _rule_b(value: float) -> float:
    """Rule B, as the listener rounds: the nearest whole unit, a half always rounds up."""
    import math as _math
    return float(_math.floor(value + 0.5))


def _check_moves(moves: Any) -> list:
    """The moves as clean dicts {contour, node, from: {x, y}, to: {x, y}}, or a ToolError before anything is sent."""
    if not isinstance(moves, (list, tuple)) or not (1 <= len(moves) <= _MOVE_MAX):
        raise ToolError(f"moves must be a list of 1 to {_MOVE_MAX} moves.")
    clean, seen = [], set()
    for i, mv in enumerate(moves):
        if not isinstance(mv, dict) or set(mv) != {"contour", "node", "from", "to"}:
            raise ToolError(f'move {i} must be an object with exactly "contour", "node", "from" and "to".')
        for key in ("contour", "node"):
            v = mv[key]
            if isinstance(v, bool) or not isinstance(v, int) or not (0 <= v <= _MOVE_INDEX_MAX):
                raise ToolError(f"move {i}: {key} must be a whole number from 0 to {_MOVE_INDEX_MAX} (the numbering of get_glyph_outline).")
        frm = _check_path_xy(mv["from"], f"move {i} from")
        to = _check_path_xy(mv["to"], f"move {i} to")
        where = (mv["contour"], mv["node"])
        if where in seen:
            raise ToolError(f"move {i}: contour {where[0]} node {where[1]} appears twice; give each node once.")
        seen.add(where)
        if (abs(_rule_b(to["x"]) - frm["x"]) <= _MOVE_FROM_TOLERANCE and abs(_rule_b(to["y"]) - frm["y"]) <= _MOVE_FROM_TOLERANCE):
            raise ToolError(f"move {i}: to equals from (after rounding to whole units), so nothing would move.")
        clean.append({"contour": mv["contour"], "node": mv["node"], "from": frm, "to": to})
    return clean


def _moved_extent(contours: Any) -> tuple:
    """((left, right), None) of the re-read outline, exact curve extents included, or (None, reason)."""
    if not isinstance(contours, list):
        return None, "the outline after the move is not in the reply"
    xs = []
    for ci, c in enumerate(contours):
        nodes = c.get("nodes") if isinstance(c, dict) else None
        if not isinstance(nodes, list):
            return None, f"contour {ci} is not readable in the reply"
        xs.extend(n["x"] for n in nodes if n.get("kind") == "On")
        if any(n.get("kind") != "On" for n in nodes):
            parsed = _contour_pieces([{"x": n["x"], "y": n["y"], "on": n.get("kind") == "On", "curve": n.get("kind") == "Curve"} for n in nodes],
                                     c.get("closed"))
            if parsed is None:
                return None, f"contour {ci}: its curve segments could not be told apart, so its extent was not computed"
            for pc in parsed[1]:
                if pc[0] == "C":
                    xs.extend(p[0] for p in _cubic_extremes(pc[1], pc[2], pc[3], pc[4]))
                elif pc[0] == "Q":
                    xs.extend(p[0] for p in [pc[1], pc[3]] + _quad_extremes(pc[1], pc[2], pc[3]))
    if not xs:
        return None, "the outline has no on-curve node"
    return (min(xs), max(xs)), None


def _margin_number(margins: Any, key: str) -> Any:
    v = margins.get(key) if isinstance(margins, dict) else None
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _move_view(contours: Any) -> Any:
    """The listener's snapshot contours in the form get_glyph_outline uses (index, closed, node_list), or None."""
    if not isinstance(contours, list):
        return None
    out = []
    for ci, c in enumerate(contours):
        nodes = c.get("nodes") if isinstance(c, dict) else None
        if not isinstance(nodes, list):
            return None
        out.append({"index": ci, "closed": c.get("closed"),
                    "node_list": [{"x": _tidy_number(n.get("x")), "y": _tidy_number(n.get("y")), "kind": n.get("kind"),
                                   "smooth": bool(n.get("smooth"))} for n in nodes if isinstance(n, dict)]})
    return out


def write_glyph_moves(name: str, moves: Any) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("Glyph name must not be empty.")
    checked = _check_moves(moves)
    _require_listener((0, 153), "move_nodes")

    data = _write_post("/glyph/move", {"name": clean, "moves": checked})

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    changed = data.get("changed")
    rounded = _rounded_list(data.get("coordinates_rounded"))
    done = [{"contour": m["contour"], "node": m["node"], "from": {k: _tidy_number(v) for k, v in m["from"].items()},
             "to": {k: _tidy_number(_rule_b(v)) for k, v in m["to"].items()}} for m in checked]
    if not data.get("moved"):
        reason = data.get("reason") or "unknown reason"
        if changed is not True and changed != "unknown":
            raise ToolError(f"Glyph '{clean}': nothing was moved: {reason}")
        result = {"name": clean, "moved": False, "verified": False, "nodes_match": False, "changed": changed, "reason": reason,
                  "moves": done, "coordinates_rounded": rounded,
                  "mismatches": [m for m in data.get("mismatches") or [] if isinstance(m, str)][:20],
                  "before": _move_view(data.get("before")), "after": _move_view(data.get("after")),
                  "agent_instruction": _MOVE_UNCONFIRMED_INSTRUCTION}
        _add_rounding_note(result)
        _add_guard_fields(result, data)
        if changed is True:
            _mark_modified(result, True)
            _add_undo_note(result)
        else:
            _note_change(sure=False)
            result["font_modified"] = "unknown"
            result["agent_instruction"] += " " + _SAVE_INSTRUCTION
        return result

    # v0.64 (live 1001-1015): FontLab's own sidebearings and ink box lag after an API node move and no call refreshes them, so the
    # re-read nodes are the confirmation and the sidebearings are computed from them; FontLab's values are shown beside them.
    margins = data.get("margins")
    lsb, rsb, adv = (_margin_number(margins, k) for k in ("lsb", "rsb", "advance"))
    box, why = _moved_extent(data.get("after"))
    result = {
        "name": clean,
        "moved": True,
        "verified": data.get("nodes_match") is True,
        "nodes_match": data.get("nodes_match") is True,
        "moves": done,
        "coordinates_rounded": rounded,
        "left": None, "right": None, "advance_width": _tidy_number(adv), "ink_width": None,
        "sidebearings_source": "computed from the re-read nodes (exact curve extents) and FontLab's advance width",
        "fontlab_sidebearings": {"left": _tidy_number(lsb), "right": _tidy_number(rsb), "advance_width": _tidy_number(adv)},
        "fontlab_sidebearings_current": "unknown",
        "note": ("Every node of the re-read layer is where the request put it, and every other node, node kind and smooth flag is unchanged. "
                 "An on-curve node moved alone did NOT take its control points along. The advance width is unchanged; the left and right "
                 "sidebearings follow the outline."),
    }
    if box is None:
        result["sidebearings_note"] = f"The sidebearings could not be computed: {why}."
    else:
        tol = 0.01 if all(n.get("kind") == "On" for c in data["after"] for n in c["nodes"]) else _CURVE_BOX_TOLERANCE
        result["left"] = _tidy_number(round(box[0], 4))
        result["ink_width"] = _tidy_number(round(box[1] - box[0], 4))
        if adv is not None:
            result["right"] = _tidy_number(round(adv - box[1], 4))
        if lsb is not None and rsb is not None and adv is not None:
            current = abs(lsb - box[0]) < tol and abs((adv - rsb) - box[1]) < tol
            result["fontlab_sidebearings_current"] = current
            if not current:
                result["person_note"] = _MOVE_FONTLAB_LAG_NOTE
                result["agent_instruction"] = _MOVE_FONTLAB_LAG_INSTRUCTION
    # v0.65: the listener's display_note is not forwarded: it gives repaint steps (DECISIONS 2026-11-13); person_note covers the lag.
    _add_rounding_note(result)
    _add_guard_fields(result, data)
    _mark_modified(result, True)
    _add_undo_note(result)
    return result


# ---- v0.66: add_component through POST /glyph/component (listener 0.169; design of the user, DECISIONS.md 2026-11-17) ----
_COMP_OFFSET_MAX = 10000
_COMP_CHECK_KEYS = ("one_component", "source_layer", "offset", "ink_box", "recipe_cleared", "auto_layer_off", "source_unchanged",
                    "width_unchanged", "glyph_count_unchanged")
_COMP_CHECKS_SINCE_187 = ("source_layer",)     # v0.74: listener 0.187 sends it; an older listener's one_component includes it


def _comp_checks_ok(checks: dict) -> bool:
    """v0.74: every single-form check True; a check a listener older than 0.187 does not send is not required."""
    return all(checks.get(k) is True for k in _COMP_CHECK_KEYS if k in checks or k not in _COMP_CHECKS_SINCE_187)


def _comp_refusal(clean: str, reason: str) -> ToolError:
    """v0.74: the ToolError for an add_component call that changed nothing, saying "nothing was changed" once (the listener's reason
    ends with it; live 1351 showed it twice)."""
    tail = ": nothing was changed"
    text = reason[:-len(tail)] if isinstance(reason, str) and reason.endswith(tail) else reason
    return ToolError(f"Glyph '{clean}': nothing was changed: {text}")
_COMP_NOTE = ("The glyph now holds one component of the named glyph at the given offset, read back from FontLab: the component, its "
              "offset and its drawn box are confirmed, FontLab's recipe for it was cleared, and the component glyph, the advance width and "
              "the glyph count are unchanged.")
_COMP_UNCONFIRMED_INSTRUCTION = (
    "The re-read does NOT confirm the component, and the glyph may now hold part of it (see steps_done, checks and elements_after). Tell "
    "the person what happened, in plain words. Do NOT repair or repeat it on your own: ask the person first.")


def _check_comp_offset(value: Any, label: str) -> int:
    """A whole number of font units from -10000 to 10000 (a whole float such as 120.0 is accepted), or a ToolError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value != value or value in (float("inf"), float("-inf")):
        raise ToolError(f"{label} must be a whole number of font units.")
    if float(value) != int(value):
        raise ToolError(f"{label} must be a whole number of font units (got {value}).")
    if abs(int(value)) > _COMP_OFFSET_MAX:
        raise ToolError(f"{label} must be between -{_COMP_OFFSET_MAX} and {_COMP_OFFSET_MAX}.")
    return int(value)


def write_glyph_component(name: str, component: str, x: Any = 0, y: Any = 0) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    src = component.strip() if isinstance(component, str) else ""
    if not clean or not src:
        raise ToolError("Both glyph names (name and component) must be non-empty.")
    if clean == src:
        raise ToolError(f"Glyph '{clean}' cannot hold itself as a component.")
    ox, oy = _check_comp_offset(x, "x"), _check_comp_offset(y, "y")
    _require_listener((0, 169), "add_component")

    data = _write_post("/glyph/component", {"name": clean, "component": src, "x": ox, "y": oy})

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if data.get("placement") == "temporary layer":      # v0.73: a glyph that is not empty (listener 0.186)
        return _comp_beside_reply(data, {"name": clean, "component": src, "x": ox, "y": oy}, 1)
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    if data.get("placed") is True and data.get("verified") is True and _comp_checks_ok(checks):
        result = {"name": clean, "component": src, "x": ox, "y": oy, "placed": True, "verified": True,
                  "advance_width": _tidy_number(data.get("advance_width_after")) if isinstance(data.get("advance_width_after"), (int, float)) else None,
                  "note": _COMP_NOTE}
        _comp_placement(result, data)
        _comp_width_fields(result, data, False)
        _add_guard_fields(result, data)
        _mark_modified(result, True)
        return result
    changed = data.get("changed")
    reason = data.get("reason") or "the re-read does not confirm the component"
    if changed is not True and changed != "unknown":
        raise _comp_refusal(clean, reason)
    elements = data.get("elements_after")
    view = [{"is_component": e.get("is_component"), "component_glyph": e.get("component_glyph"), "matrix": e.get("matrix")}
            for e in elements if isinstance(e, dict)] if isinstance(elements, list) else None
    result = {"name": clean, "component": src, "x": ox, "y": oy, "placed": False, "verified": False, "changed": changed, "reason": reason,
              "steps_done": [s for s in data.get("steps_done") or [] if isinstance(s, str)],
              "checks": {k: checks.get(k) for k in _COMP_CHECK_KEYS if k in checks}, "elements_after": view,
              "agent_instruction": _COMP_UNCONFIRMED_INSTRUCTION}
    _comp_placement(result, data)
    if "auto_layer_set_back" in data:                       # listeners 0.169-0.177; since 0.178 it is in cleanup
        result["auto_layer_set_back"] = data["auto_layer_set_back"]
    _comp_width_fields(result, data, "cleanup" in data)
    _add_guard_fields(result, data)
    if changed is True:
        _mark_modified(result, True)
    else:
        _note_change(sure=False)
        result["font_modified"] = "unknown"
        result["agent_instruction"] += " " + _SAVE_INSTRUCTION
    return result


# ---- v0.68: add_component with a components list (listener 0.174; the user's design, DECISIONS.md 2026-11-17 "several components") ----
_COMP_SOFT_LIMIT = 30         # tested at 2-5, 15 and 30 (PC2 / PC3 1102-1177); more needs the person's agreement (confirmed_untested_size)
_COMP_UNTESTED_NOTE = "Only up to 30 components in one call have been tested; anything above is unknown territory."
_COMP_LIST_CHECK_KEYS = ("element_count", "components", "recipe_cleared", "auto_layer_off", "sources_unchanged", "width_unchanged",
                         "glyph_count_unchanged")
_COMP_LIST_STATES = ("placed", "at FontLab's position", "left by the build", "missing after the build", "not reached", "unknown")
_COMP_LIST_NOTE = ("The glyph now holds the listed components, in order, each at its offset, read back from FontLab: every component, its "
                   "offset and its drawn box are confirmed, FontLab's recipe was cleared, the advance width is as before, and the component "
                   "glyphs and the glyph count are unchanged.")
_COMP_LIST_UNCONFIRMED_INSTRUCTION = (
    "The re-read does NOT confirm the components. Placing stopped at the first failure; then the automatic layer was switched off, the "
    "recipe cleared and the width written back where possible (see cleanup). component_states says for each entry whether it is placed, "
    "at FontLab's own position, left by the build (in the glyph, its offset not confirmed), missing after the build, not reached (the "
    "build never ran) or unknown. components_after lists what the glyph holds now. Tell the person, in plain words, what happened and "
    "which components are left in the glyph; any they do not want can be removed with remove_component (after reading the glyph with "
    "get_glyph_outline) or deleted in FontLab. Do NOT repair, remove or repeat anything on your own: ask the person first.")
_COMP_UNDERSCORE_NOTE = ("FontLab's recipe build of several glyphs reads a name with an underscore as a ligature of its parts (\"a_b\" as a "
                         "and b): it drops the glyph, or places the parts instead if they exist (seen live, 1234). Place such a glyph on "
                         "its own with component, x and y, into an empty glyph.")


def _comp_width_fields(result: dict, data: dict, with_cleanup: bool) -> None:
    """v0.71: pass on what FontLab's build set the width to (width_set_by_build, listener 0.178, a finite number only) and, when asked,
    the clean-up block (only its known keys, each True or a text)."""
    v = data.get("width_set_by_build")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v):
        result["width_set_by_build"] = _tidy_number(v)
    if with_cleanup:
        cleanup = data.get("cleanup") if isinstance(data.get("cleanup"), dict) else {}
        result["cleanup"] = {k: v for k, v in cleanup.items() if k in ("auto_layer_set_back", "recipe_cleared", "width_restored")
                             and (v is True or isinstance(v, str))}


def _comp_after_view(raw: Any) -> Any:
    """The listener's components_after (v0.175), with text cleaned and only the known fields kept; None when it is missing."""
    if isinstance(raw, dict):
        err = raw.get("error")
        return {"error": _clean_font_text(err) if isinstance(err, str) else "the elements could not be read"}
    if not isinstance(raw, list):
        return None
    out = []
    for el in raw:
        if el in ("not a component", "unreadable"):
            out.append(el)
        elif isinstance(el, dict) and isinstance(el.get("component"), str):
            row = {"component": _clean_font_text(el["component"])}
            if all(isinstance(el.get(k), (int, float)) and not isinstance(el.get(k), bool) and math.isfinite(el[k]) for k in ("x", "y")):
                row["x"], row["y"] = _tidy_number(el["x"]), _tidy_number(el["y"])
                if isinstance(el.get("plain_offset"), bool):
                    row["plain_offset"] = el["plain_offset"]
            else:
                row["offset"] = "unreadable"
            out.append(row)
        else:
            out.append("unreadable")
    return out


# ---- v0.73: add_component into a glyph that is NOT empty (listener 0.186; the user's design of 2026-11-18, DECISIONS.md) ----
_COMP_BESIDE_CHECK_KEYS = ("layers", "existing_kept", "components", "contours_held", "auto_layer_and_recipe_unchanged", "sources_unchanged",
                           "width_unchanged", "glyph_count_unchanged")
_COMP_BESIDE_NOTE = ("The glyph still holds everything it held before, unchanged and first, and after it the listed components, in order, "
                     "each at its offset, read back from FontLab: every component, its source and its drawn box are confirmed. The temporary "
                     "layer FontLab's build needed is gone again, and the advance width, the component glyphs and the glyph count are unchanged.")
_COMP_RESTORED_INSTRUCTION = (
    "Placing failed partway (see reason), and the glyph was put back as it was before the call: a re-read confirms it (restore.restored). "
    "Nothing was placed. Tell the person, in plain words, what failed. Do NOT repeat it on your own: ask the person first.")
_COMP_NOT_RESTORED_INSTRUCTION = (
    "Placing did NOT succeed, and the glyph could NOT be confirmed as it was before the call: it may hold some of the components, or a "
    "temporary layer named gb_temp_component (see restore, layers_after, component_states and components_after). Tell the person, in plain "
    "words, what happened and what the glyph holds now. Do NOT repair, remove or repeat anything on your own: ask the person first.")
_COMP_RESTORE_KEYS = ("restored", "components_removed", "working_layer_made_active", "temp_auto_layer_off", "temp_layer_removed",
                      "width_restored", "error")


def _comp_placement(result: dict, data: dict) -> None:
    """v0.73: pass on placement "empty layer" (listener 0.186) on the empty route; an older listener sends none, so none is added."""
    if data.get("placement") == "empty layer":
        result["placement"] = "empty layer"


def _comp_beside_reply(data: dict, head: dict, n: int) -> dict:
    """v0.73: the reply for the temporary-layer route (placement "temporary layer", listener 0.186), both forms. head holds the request's
    own fields (name and the component or the list). A refusal that changed nothing is a ToolError, as in the empty route."""
    clean = head["name"]
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    timing = {k: _tidy_number(data[k]) for k in ("build_seconds", "elapsed_seconds") if isinstance(data.get(k), (int, float))}
    if data.get("placed") is True and data.get("verified") is True and all(checks.get(k) is True for k in _COMP_BESIDE_CHECK_KEYS):
        result = dict(head, placement="temporary layer", placed=True, verified=True, existing_kept=True,
                      advance_width=_tidy_number(data.get("advance_width_after")) if isinstance(data.get("advance_width_after"), (int, float)) else None,
                      note=_COMP_BESIDE_NOTE, timing=timing)
        if n > _COMP_SOFT_LIMIT:
            result["untested_size_note"] = _COMP_UNTESTED_NOTE
        _comp_width_fields(result, data, False)
        _add_guard_fields(result, data)
        _mark_modified(result, True)
        return result
    changed = data.get("changed")
    reason = data.get("reason") or "the re-read does not confirm the components"
    raw_restore = data.get("restore")
    if changed is not True and changed != "unknown" and not isinstance(raw_restore, dict):
        raise _comp_refusal(clean, reason)
    restore = ({k: v for k, v in raw_restore.items() if k in _COMP_RESTORE_KEYS
                and (isinstance(v, bool) or (isinstance(v, int) and v >= 0) or isinstance(v, str))} if isinstance(raw_restore, dict) else None)
    if restore is not None and isinstance(restore.get("error"), str):
        restore["error"] = _clean_font_text(restore["error"])
    raw_states = data.get("component_states") if isinstance(data.get("component_states"), list) else []
    result = dict(head, placement="temporary layer", placed=False, verified=False, changed=changed, reason=reason,
                  steps_done=[s for s in data.get("steps_done") or [] if isinstance(s, str)],
                  checks={k: checks.get(k) for k in _COMP_BESIDE_CHECK_KEYS if k in checks},
                  component_states=[{"component": st.get("component"), "x": st.get("x"), "y": st.get("y"),
                                     "state": st.get("state") if st.get("state") in ("placed", "not reached", "unknown") else "unknown"}
                                    for st in raw_states if isinstance(st, dict)],
                  timing=timing)
    if restore is not None:
        result["restore"] = restore
    layers_after = data.get("layers_after")
    if isinstance(layers_after, list) and all(isinstance(v, str) for v in layers_after):
        result["layers_after"] = [_clean_font_text(v) for v in layers_after]
    after = _comp_after_view(data.get("components_after"))
    if after is not None:
        result["components_after"] = after
    restored = restore is not None and restore.get("restored") is True and changed is False
    result["agent_instruction"] = _COMP_RESTORED_INSTRUCTION if restored else _COMP_NOT_RESTORED_INSTRUCTION
    if n > _COMP_SOFT_LIMIT:
        result["untested_size_note"] = _COMP_UNTESTED_NOTE
    _comp_width_fields(result, data, False)
    _add_guard_fields(result, data)
    if changed is True:
        _mark_modified(result, True)
    elif restored:
        result["font_modified"] = False
    else:
        _note_change(sure=False)
        result["font_modified"] = "unknown"
        result["agent_instruction"] += " " + _SAVE_INSTRUCTION
    return result


def _comp_needs_confirmation(clean: str, n: int) -> dict:
    return {"name": clean, "component_count": n, "placed": False, "changed": False, "needs_confirmation": True,
            "untested_size_note": _COMP_UNTESTED_NOTE,
            "agent_instruction": (f"Nothing was changed. Tell the person that this would place {n} components in '{clean}', that only up to "
                                  f"{_COMP_SOFT_LIMIT} components in one call have been tested and anything above is unknown territory, and "
                                  "ask whether to go ahead. Only if they agree, call add_component again with the same components and "
                                  "confirmed_untested_size=true.")}


def write_glyph_components(name: str, components: Any, confirmed: Any = False) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("name must be a non-empty glyph name.")
    if not isinstance(confirmed, bool):
        raise ToolError("confirmed_untested_size must be true or false.")
    if not isinstance(components, list) or not components:
        raise ToolError("components must be a non-empty list of {\"component\", \"x\", \"y\"}.")
    entries = []
    for i, c in enumerate(components):
        if not isinstance(c, dict) or "component" not in c or not set(c) <= {"component", "x", "y"}:
            raise ToolError(f"components[{i}] must be an object with \"component\" and optionally \"x\" and \"y\".")
        src = c["component"].strip() if isinstance(c["component"], str) else ""
        if not src:
            raise ToolError(f"components[{i}].component must be a non-empty glyph name.")
        if "+" in src:
            raise ToolError(f"components[{i}].component must not contain '+' (FontLab's recipe joins the names with it).")
        if src == clean:
            raise ToolError(f"Glyph '{clean}' cannot hold itself as a component (components[{i}]).")
        if "_" in src:
            raise ToolError(f"components[{i}] '{src}' contains an underscore, so the list form cannot place it: nothing was changed. "
                            + _COMP_UNDERSCORE_NOTE)
        entries.append({"component": src, "x": _check_comp_offset(c.get("x", 0), f"components[{i}].x"),
                        "y": _check_comp_offset(c.get("y", 0), f"components[{i}].y")})
    n = len(entries)
    if n > _COMP_SOFT_LIMIT and confirmed is not True:
        return _comp_needs_confirmation(clean, n)
    _require_listener((0, 174), "add_component with a components list")
    payload = {"name": clean, "components": entries}
    if confirmed:
        payload["confirmed_untested_size"] = True

    data = _write_post("/glyph/component", payload)

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    if data.get("untested_size") is True:
        return _comp_needs_confirmation(clean, n)
    if data.get("placement") == "temporary layer":      # v0.73: a glyph that is not empty (listener 0.186)
        return _comp_beside_reply(data, {"name": clean, "component_count": n, "components": entries}, n)
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    timing = {k: _tidy_number(data[k]) for k in ("build_seconds", "elapsed_seconds") if isinstance(data.get(k), (int, float))}
    if data.get("placed") is True and data.get("verified") is True and all(checks.get(k) is True for k in _COMP_LIST_CHECK_KEYS):
        result = {"name": clean, "component_count": n, "components": entries, "placed": True, "verified": True,
                  "advance_width": _tidy_number(data.get("advance_width_after")) if isinstance(data.get("advance_width_after"), (int, float)) else None,
                  "note": _COMP_LIST_NOTE, "timing": timing}
        _comp_placement(result, data)
        if n > _COMP_SOFT_LIMIT:
            result["untested_size_note"] = _COMP_UNTESTED_NOTE
        _comp_width_fields(result, data, False)
        _add_guard_fields(result, data)
        _mark_modified(result, True)
        return result
    changed = data.get("changed")
    reason = data.get("reason") or "the re-read does not confirm the components"
    if changed is not True and changed != "unknown":
        raise _comp_refusal(clean, reason)
    raw_states = data.get("component_states") if isinstance(data.get("component_states"), list) else []
    states = [{"component": st.get("component"), "x": st.get("x"), "y": st.get("y"),
               "state": st.get("state") if st.get("state") in _COMP_LIST_STATES else "unknown"} for st in raw_states if isinstance(st, dict)]
    cleanup = data.get("cleanup") if isinstance(data.get("cleanup"), dict) else {}
    result = {"name": clean, "component_count": n, "placed": False, "verified": False, "changed": changed, "reason": reason,
              "steps_done": [x for x in data.get("steps_done") or [] if isinstance(x, str)],
              "cleanup": {k: v for k, v in cleanup.items() if k in ("auto_layer_set_back", "recipe_cleared", "width_restored")
                          and (v is True or isinstance(v, str))},
              "component_states": states, "checks": {k: checks.get(k) for k in _COMP_LIST_CHECK_KEYS if k in checks},
              "timing": timing, "agent_instruction": _COMP_LIST_UNCONFIRMED_INSTRUCTION}
    _comp_placement(result, data)
    after = _comp_after_view(data.get("components_after"))
    if after is not None:
        result["components_after"] = after
    _comp_width_fields(result, data, False)
    if n > _COMP_SOFT_LIMIT:
        result["untested_size_note"] = _COMP_UNTESTED_NOTE
    _add_guard_fields(result, data)
    if changed is True:
        _mark_modified(result, True)
    else:
        _note_change(sure=False)
        result["font_modified"] = "unknown"
        result["agent_instruction"] += " " + _SAVE_INSTRUCTION
    return result


# ---- v0.72: remove_component through POST /glyph/component/remove (listener 0.179; the user's design, DECISIONS.md 2026-11-18) ----
_REMOVE_OFFSET_MAX = 20000
_REMOVE_INDEX_MAX = 100000
_REMOVE_CHECK_KEYS = ("layer_kept", "elements", "ink_boxes", "outline_kept", "auto_layer_and_recipe_unchanged", "sources_unchanged",
                      "width_unchanged", "glyph_count_unchanged")
_REMOVE_STATES = ("removed", "called, not confirmed", "call failed", "not reached")
_REMOVE_NOTE = ("The named components were removed, read back from FontLab: every other element of the glyph (contours and components) "
                "is where and what it was, with the same drawn box and outline, and the component glyphs, the advance width and the "
                "glyph count are unchanged.")
_REMOVE_UNCONFIRMED_INSTRUCTION = (
    "The re-read does NOT confirm the removal. Removal stopped at the first failure (entry_states says, per entry: removed, called "
    "but not confirmed, call failed, or not reached); components_after lists what the glyph holds now. Tell the person, in plain "
    "words, what happened. Do NOT repair, remove or repeat anything on your own: ask the person first, and read the glyph again with "
    "get_glyph_outline before any new call, because the indices may have changed.")
_REMOVE_RECIPE_NOTE = ("FontLab still keeps a recipe on this glyph's layer (recipe_kept). remove_component leaves it as it is; it does "
                       "not rebuild anything while the automatic layer is off.")


def _check_remove_entry(c: Any, label: str) -> dict:
    """One entry as a clean dict {index, component, x, y}, or a ToolError before anything is sent."""
    if not isinstance(c, dict) or not {"index", "component"} <= set(c) or not set(c) <= {"index", "component", "x", "y"}:
        raise ToolError(f'{label} must be an object with "index" and "component", and optionally "x" and "y".')
    idx = c["index"]
    if isinstance(idx, bool) or not isinstance(idx, int) or not (0 <= idx <= _REMOVE_INDEX_MAX):
        raise ToolError(f"{label}: index must be a whole number from 0 (the numbering of get_glyph_outline's elements).")
    src = c["component"].strip() if isinstance(c["component"], str) else ""
    if not src:
        raise ToolError(f"{label}: component must be a non-empty glyph name.")
    xy = []
    for key in ("x", "y"):
        v = c.get(key, 0)
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or abs(v) > _REMOVE_OFFSET_MAX:
            raise ToolError(f"{label}: {key} must be a number from -{_REMOVE_OFFSET_MAX} to {_REMOVE_OFFSET_MAX} (the offset get_glyph_outline shows).")
        xy.append(int(v) if float(v) == int(v) else float(v))
    return {"index": idx, "component": src, "x": xy[0], "y": xy[1]}


def write_glyph_remove_components(name: str, entries: list, form: str) -> dict:
    clean = name.strip() if isinstance(name, str) else ""
    if not clean:
        raise ToolError("name must be a non-empty glyph name.")
    seen = set()
    for e in entries:
        if e["index"] in seen:
            raise ToolError(f"index {e['index']} appears twice; give each component once.")
        seen.add(e["index"])
    _require_listener((0, 179), "remove_component")
    payload = {"name": clean, **entries[0]} if form == "single" else {"name": clean, "components": entries}

    data = _write_post("/glyph/component/remove", payload)

    if not data.get("open"):
        raise ToolError(NO_FONT)
    if data.get("found") is False:
        raise ToolError(f"No glyph named '{clean}' was found.")
    checks = data.get("checks") if isinstance(data.get("checks"), dict) else {}
    timing = {k: _tidy_number(data[k]) for k in ("elapsed_seconds",) if isinstance(data.get(k), (int, float)) and not isinstance(data.get(k), bool)}
    after = _comp_after_view(data.get("components_after"))
    width = data.get("width_changed_by_removal")
    cleanup = data.get("cleanup") if isinstance(data.get("cleanup"), dict) else {}
    extra = {}
    if isinstance(width, (int, float)) and not isinstance(width, bool) and math.isfinite(width):
        extra["width_changed_by_removal"] = _tidy_number(width)
        extra["cleanup"] = {k: v for k, v in cleanup.items() if k == "width_restored" and (v is True or isinstance(v, str))}
    if isinstance(data.get("recipe_kept"), str) and data["recipe_kept"]:
        extra["recipe_kept"] = _clean_font_text(data["recipe_kept"])
        extra["recipe_note"] = _REMOVE_RECIPE_NOTE
    if data.get("removed") is True and data.get("verified") is True and all(checks.get(k) is True for k in _REMOVE_CHECK_KEYS):
        result = {"name": clean, "removed": True, "verified": True, "entries": entries,
                  "empty_after": data.get("empty_after") if isinstance(data.get("empty_after"), bool) else "unknown",
                  "advance_width": _tidy_number(data.get("advance_width_after")) if isinstance(data.get("advance_width_after"), (int, float)) else None,
                  "note": _REMOVE_NOTE, "timing": timing, **extra}
        if after is not None:
            result["components_after"] = after
        _add_guard_fields(result, data)
        _mark_modified(result, True)
        return result
    changed = data.get("changed")
    reason = data.get("reason") or "the re-read does not confirm the removal"
    if changed is not True and changed != "unknown":
        raise ToolError(f"Glyph '{clean}': nothing was changed: {reason}")
    raw_states = data.get("entry_states") if isinstance(data.get("entry_states"), list) else []
    states = [{"index": st.get("index"), "component": st.get("component"),
               "state": st.get("state") if st.get("state") in _REMOVE_STATES else "unknown"} for st in raw_states if isinstance(st, dict)]
    result = {"name": clean, "removed": False, "verified": False, "changed": changed, "reason": reason, "entries": entries,
              "entry_states": states, "checks": {k: checks.get(k) for k in _REMOVE_CHECK_KEYS if k in checks},
              "timing": timing, "agent_instruction": _REMOVE_UNCONFIRMED_INSTRUCTION, **extra}
    if after is not None:
        result["components_after"] = after
    _add_guard_fields(result, data)
    if changed is True:
        _mark_modified(result, True)
    else:
        _note_change(sure=False)
        result["font_modified"] = "unknown"
        result["agent_instruction"] += " " + _SAVE_INSTRUCTION
    return result


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


def _svg_path(start_pt, pieces, closed: bool = True) -> str:
    """v0.46: an open contour (closed=False) gets no closing Z."""
    parts = [f"M {_fmt(start_pt[0])} {_fmt(start_pt[1])}"]
    for pc in pieces:
        if pc[0] == "L":
            parts.append(f"L {_fmt(pc[2][0])} {_fmt(pc[2][1])}")
        elif pc[0] == "C":
            parts.append("C " + " ".join(f"{_fmt(p[0])} {_fmt(p[1])}" for p in (pc[2], pc[3], pc[4])))
        else:
            parts.append("Q " + " ".join(f"{_fmt(p[0])} {_fmt(p[1])}" for p in (pc[2], pc[3])))
    if closed:
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
        parts.append(f"offset ({dx + 0.0:g}, {dy + 0.0:g})")        # + 0.0: FontLab stores -0.0, which would print as -0
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


_CURVE_BOX_TOLERANCE = 0.05       # font units: computed curve extents vs FontLab's own modern margins and ink box


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


def _quad_extremes(p0, c, p1) -> list:
    """v0.43. The points of one quadratic Bezier segment where x or y is extreme: t = (p0 - c) / (p0 - 2c + p1) per axis, inside 0 < t < 1."""
    out = []
    for axis in (0, 1):
        d = p0[axis] - 2 * c[axis] + p1[axis]
        if abs(d) < 1e-12:
            continue
        t = (p0[axis] - c[axis]) / d
        if 0.0 < t < 1.0:
            u = 1.0 - t
            out.append(tuple(u * u * p0[i] + 2 * u * t * c[i] + t * t * p1[i] for i in (0, 1)))
    return out


def _contour_pieces(nodes: list, closed: Any):
    """(start point, pieces) of ONE contour made of straight, cubic and quadratic segments, or None when it is anything else (a segment
    that mixes cubic and quadratic points, a run of cubic handles that is not exactly two, no on-curve node, a closed flag that is not a
    bool). nodes: dicts with x, y, on (bool), curve (bool); a point that is neither on-curve nor curve is a quadratic off-curve point. The
    closing segment may have its handles at the END of the list (how FontLab stores them). v0.43: a run of quadratic off-curve points gets
    an implied on-curve point halfway between each two (TrueType, as in _segment_pieces); before, a contour with quadratic points was not
    parsed. v0.46: an open contour (closed False) runs from its first node to its last, with no closing segment; both must be on-curve
    (live 583: FontLab's open arch reads On, Curve, Curve, On), otherwise None."""
    if not nodes:
        return None
    if closed is True:
        start_i = next((i for i, n in enumerate(nodes) if n["on"]), None)
        if start_i is None:
            return None
        seq = nodes[start_i:] + nodes[:start_i]
        walk = seq[1:] + [seq[0]]
    elif closed is False:
        if not (nodes[0]["on"] and nodes[-1]["on"]):
            return None
        seq = nodes
        walk = nodes[1:]
    else:
        return None
    start = (seq[0]["x"], seq[0]["y"])
    pieces, cur, pend, kinds = [], start, [], set()
    for nd in walk:
        pt = (nd["x"], nd["y"])
        if not nd["on"]:
            pend.append(pt)
            kinds.add("C" if nd["curve"] else "Q")
            continue
        if not pend:
            pieces.append(("L", cur, pt))
        elif kinds == {"C"}:
            if len(pend) != 2:
                return None
            pieces.append(("C", cur, pend[0], pend[1], pt))
        elif kinds == {"Q"}:
            a = cur
            for i, c in enumerate(pend):
                b = pt if i == len(pend) - 1 else _mid(c, pend[i + 1])
                pieces.append(("Q", a, c, b))
                a = b
        else:
            return None                        # one segment mixes cubic and quadratic points
        cur, pend, kinds = pt, [], set()
    return start, pieces


def _modern_outline_result(clean: str, mo: dict, mc: dict, data: dict, modern_first: bool = False) -> dict:
    """The outline as read from FontLab's modern layer (the legacy reader is blind or stale for this glyph, or, since
    v0.42 with modern_first, was deliberately not used: F1)."""
    stale_margins = isinstance(mc, dict) and mc.get("agree") is not False and mc.get("margins_agree") is False
    contours_out, on_points, notes = [], [], []
    has_curves, disagree, open_idx = False, [], []
    exact_ok, curve_problems, curve_boxes = True, [], []
    for c in mo["contours"]:
        is_open = c.get("closed") is False             # v0.46: open contours (live 581, 583)
        if is_open:
            open_idx.append(c.get("index"))
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
        flag = c.get("clockwise")
        if is_open:                                    # an open path has no inside, so no direction (live 581 gave one from the closed polygon)
            computed, inverted = "not applicable (open contour)", None
        else:
            area = _signed_area(pts) if len(pts) >= 3 else 0.0
            computed = "counterclockwise" if area > 0 else "clockwise" if area < 0 else "undetermined"
            # live (two glyphs, both ways round): FontLab's flag is True for a counterclockwise contour (y up) and False for a clockwise one
            inverted = None if computed == "undetermined" or not isinstance(flag, bool) else (flag == (computed == "counterclockwise"))
        if inverted is False:
            disagree.append(c.get("index"))
        entry = {"index": c.get("index"), "closed": c.get("closed"), "node_count": len(nodes), "curve_type": curve_type,
                 "clockwise_reported": flag, "direction_computed": computed, "flag_follows_known_inversion": inverted, "node_list": nodes}
        if not curved:
            if c.get("closed") in (True, False) and nodes:
                entry["svg_path"] = "M " + " L ".join(f"{n['x']} {n['y']}" for n in nodes) + ("" if is_open else " Z")
        elif curve_type in ("cubic", "quadratic"):
            parsed = _contour_pieces([{"x": n["x"], "y": n["y"], "on": bool(n.get("isOn")), "curve": bool(n.get("isCurve"))}
                                      for n in c["nodes"]], c.get("closed"))
            if parsed is None:
                exact_ok = False
                if is_open and not (c["nodes"][0].get("isOn") and c["nodes"][-1].get("isOn")):
                    why = "an open contour whose first or last node is not on-curve"
                elif c.get("closed") not in (True, False):
                    why = f"FontLab's closed flag reads {c.get('closed')!r}, not true or false"
                else:
                    why = "a run of cubic control points that is not exactly two, or no on-curve node"
                curve_problems.append(f"contour {c.get('index')}: the {curve_type} segments could not be told apart ({why})")
            else:
                entry["svg_path"] = _svg_path(parsed[0], parsed[1], closed=not is_open)
                curve_boxes.append(parsed)
        else:
            exact_ok = False
            curve_problems.append(f"contour {c.get('index')}: {curve_type} curve nodes; a contour that mixes cubic and quadratic points is not evaluated")
        contours_out.append(entry)
    notes.append("direction_computed is the geometric direction in y-up font units (counterclockwise = positive area). FontLab's own clockwise flag "
                 "(clockwise_reported) reads the opposite way round on the contours tested live (a counterclockwise contour shows true); it is "
                 "listed for reference only. In the cubic test font the outer contour of FontLab's own glyph A is counterclockwise.")
    if disagree:
        notes.append(f"WARNING: for contour(s) {disagree} FontLab's clockwise flag does NOT show the usual inversion: check the direction "
                     "before relying on direction_computed.")
    if open_idx:
        notes.append(f"Contour(s) {open_idx} are OPEN (closed: false): each runs from its first node to its last, with no closing segment, "
                     "so it has no fill and no direction, and its svg_path ends without Z.")
    if stale_margins:
        leg_m = mc.get("legacy_margins") if isinstance(mc.get("legacy_margins"), dict) else {}
        mod_m = mc.get("modern_margins") if isinstance(mc.get("modern_margins"), dict) else {}
        notes.append(f"STALE LEGACY VIEW, answered from the modern layer: the legacy reader gives margins {({k: _tidy_number(x) for k, x in leg_m.items()})} but "
                     f"FontLab's modern layer gives {({k: _tidy_number(x) for k, x in mod_m.items()})} (the glyph was probably changed through the API a moment ago). "
                     f"This outline was therefore read from the modern layer ({mo.get('node_count')} node(s)) and is current; no refresh is needed to trust it. "
                     "FontLab's legacy view itself refreshes only when the glyph's editor tab is closed (X) and the glyph reopened from the grid.")
    elif modern_first:
        notes.append(f"Read from FontLab's modern layer only ({mo.get('node_count')} node(s)). The glyph's legacy layer was deliberately not "
                     "read: reading it can make FontLab flatten a Power Brush glyph at its next refresh.")
    else:
        notes.append(f"The legacy reader sees {data.get('node_count')} node(s) for this glyph (it lags on glyphs changed through the API), so this "
                     f"outline was read from FontLab's modern layer ({mo.get('node_count')} node(s)).")
    # v0.70: this outline comes from the modern layer, which includes every component's contours, so the old note ("whose outlines
    # are not read by this tool") was wrong here; it was never shown only because the count read 0 (componentsCount, RM 1241-1246).
    comp = data.get("component_count")
    if isinstance(comp, int) and not isinstance(comp, bool) and comp > 0:
        notes.append(f"{comp} of the glyph's elements are components; their outlines are included in this reply (where 'elements' is "
                     "present, it names each component's source).")
    elif isinstance(comp, str) and comp.strip():
        notes.append("Whether the glyph holds components could not be read: " + _clean_font_text(comp) + ".")
    margins = mo.get("margins") if isinstance(mo.get("margins"), dict) else None
    box = None
    curves_exact = has_curves and exact_ok and bool(curve_boxes)
    if on_points:
        xs, ys = [p[0] for p in on_points], [p[1] for p in on_points]
        if curves_exact:                       # the real extents: on-curve points plus the extremes of every curve segment
            for start, pieces in curve_boxes:
                for pc in pieces:
                    if pc[0] == "C":
                        extra = _cubic_extremes(pc[1], pc[2], pc[3], pc[4])
                    elif pc[0] == "Q":         # v0.43: the implied on-curve points between two off-curve points lie on the curve too
                        extra = [pc[1], pc[3]] + _quad_extremes(pc[1], pc[2], pc[3])
                    else:
                        extra = []
                    for ex in extra:
                        xs.append(ex[0]); ys.append(ex[1])
        box = {"left": min(xs), "right": max(xs), "bottom": min(ys), "top": max(ys)}
    verification = {"status": "unverified"} if modern_first else {"status": "unverified", "modern_check": mc}
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


def _fontlab_ink_y(data: dict):
    """v0.43: (bottom, top, None), FontLab's own vertical ink extent in y-up font units from the listener's fontlab_ink_box
    (layer.inkBox(), listener 0.121), or (None, None, why not). Qt names the rectangle's sides y-down ("top" was the lower y in
    519-530), so the two sides are taken with min and max, never by their names."""
    if "fontlab_ink_box" not in data:
        return None, None, "the listener sent no FontLab ink box (listener 0.121 or newer sends one)"
    ib = data["fontlab_ink_box"]
    if not isinstance(ib, dict) or ib.get("error"):
        why = ib.get("error") if isinstance(ib, dict) else "the reply was malformed"
        return None, None, f"FontLab's ink box could not be read ({why})"
    a, b = ib.get("top"), ib.get("bottom")
    if not (_num(a) and _num(b)):
        return None, None, "FontLab's ink box had no numeric top and bottom"
    return min(a, b), max(a, b), None


def _y_extent_ok(res: dict, lo, hi):
    """v0.43: True / False when the computed box (exact: curve extents included) can be compared with FontLab's vertical ink
    extent lo..hi, else None."""
    b = res.get("ink_bbox")
    if lo is None or res.get("ink_bbox_exact") is not True or not isinstance(b, dict):
        return None
    return abs(b["bottom"] - lo) < _CURVE_BOX_TOLERANCE and abs(b["top"] - hi) < _CURVE_BOX_TOLERANCE


_COMPONENTS_UNKNOWN = " Whether this glyph contains components is therefore unknown."


def _element_component_fields(sh: dict) -> dict:
    """v0.49 (listener 0.128): what an element says about being a component. Nothing when the listener sent no flag at all."""
    if "is_component" not in sh:
        return {}
    flag = sh["is_component"]
    if flag is False:
        return {"is_component": False}
    if flag is not True:
        return {"is_component": "unknown"}
    out = {"is_component": True}
    for key in ("component_glyph", "component_layer"):
        value = sh.get(key)
        if isinstance(value, str) and value:
            out[key] = value
    return out


def _component_notes(shapes: list) -> list:
    """v0.49: one note per element that is a component, or whose state could not be read."""
    notes = []
    for index, sh in enumerate(shapes):
        fields = _element_component_fields(sh)
        flag = fields.get("is_component")
        if flag == "unknown":
            notes.append(f"Whether element {index} is a component could not be read.")
        elif flag is True:
            name = fields.get("component_glyph")
            if name:
                layer = fields.get("component_layer")
                where = f" (layer {layer!r})" if layer else ""
                notes.append(f"Element {index} is a component of {name!r}{where}. Its nodes are shown where FontLab draws them, but they are "
                             "that glyph's outline, not one of this glyph's own.")
            else:
                why = sh.get("component_error")
                why = why if isinstance(why, str) and why else "FontLab reported no name"
                notes.append(f"Element {index} is a component, but the name of its source glyph could not be read ({why}). Its nodes are shown "
                             "where FontLab draws them, but they are its source glyph's outline, not one of this glyph's own.")
    return notes


def _box_sides(box: Any):
    """v0.50: (left, right, bottom, top) in y-up font units from a box the listener sent, or None. Qt names its sides y-down
    ("top" is the lower y, live 644), so each pair is ordered by value, never trusted by name."""
    if not isinstance(box, dict) or box.get("error"):
        return None
    left, right, top, bottom = box.get("left"), box.get("right"), box.get("top"), box.get("bottom")
    if not all(_num(v) for v in (left, right, top, bottom)):
        return None
    return min(left, right), max(left, right), min(top, bottom), max(top, bottom)


def _same_box(a: tuple, b: tuple) -> bool:
    return all(abs(x - y) < _CURVE_BOX_TOLERANCE for x, y in zip(a, b))


def _box_text(b: tuple) -> str:
    return f"x {_tidy_number(round(b[0], 3))}..{_tidy_number(round(b[1], 3))}, y {_tidy_number(round(b[2], 3))}..{_tidy_number(round(b[3], 3))}"


def _box_problem(box: Any) -> str:
    return box["error"] if isinstance(box, dict) and isinstance(box.get("error"), str) and box["error"] else "it was missing or malformed"


def _contours_box(clean: str, mo: dict, contours: list):
    """v0.50: the exact (left, right, bottom, top) of these contours, curve extents included, or None."""
    res = _modern_outline_result(clean, dict(mo, contours=contours), None, {}, modern_first=True)
    b = res.get("ink_bbox")
    if res.get("ink_bbox_exact") is not True or not isinstance(b, dict):
        return None
    return b["left"], b["right"], b["bottom"], b["top"]


def _elements_settle(clean: str, mo: dict, moved: list, shapes: list, found: list, counts: list):
    """v0.50 (listener 0.130): a glyph whose outer box fits with and without its transforms (an accent inside its base, live 633, 636)
    is settled element by element: (True, None) only when each moved element's computed box equals FontLab's own box of that
    element and its box without the transform does not. (False, why) otherwise; why is None when the listener sent no boxes."""
    moved_elements = [i for i, m in enumerate(found) if not _is_identity(m)]
    if not any("ink_box" in shapes[i] for i in moved_elements):
        return False, None
    spans, start = [], 0
    for count in counts:
        spans.append((start, start + count))
        start += count
    for i in moved_elements:
        m = found[i]
        if abs(m[0] - 1) >= 1e-6 or abs(m[3] - 1) >= 1e-6 or abs(m[1]) >= 1e-6 or abs(m[2]) >= 1e-6:
            return False, f"element {i} is scaled, slanted, rotated or mirrored; the per-element check is proven for plain offsets only"
        fontlab = _box_sides(shapes[i].get("ink_box"))
        if fontlab is None:
            return False, f"FontLab's box of element {i} could not be used: {_box_problem(shapes[i].get('ink_box'))}"
        first, last = spans[i]
        applied, raw = _contours_box(clean, mo, moved[first:last]), _contours_box(clean, mo, mo["contours"][first:last])
        if applied is None or raw is None:
            return False, f"the exact box of element {i} could not be computed"
        if not _same_box(applied, fontlab):
            return False, f"element {i}: computed {_box_text(applied)}, FontLab {_box_text(fontlab)}"
        if _same_box(raw, fontlab):
            return False, f"element {i}: FontLab's box fits with and without the element's transform"
    return True, None


def _modern_first_read(clean: str, data: dict) -> dict:
    """v0.42 (F1, listener 0.120): the listener read a glyph that has modern nodes from the modern layer only. The element
    transforms are applied by contour counts, as on the legacy route, and the result is checked against FontLab's modern
    left sidebearing and ink width. Live 608, 611 and 631 showed the modern node coordinates leave the element transform out;
    both readings are still checked, and only an unambiguous match is called verified.
    v0.43 (listener 0.121): the vertical extent is checked too, against FontLab's own ink box (layer.inkBox()): verified needs
    both, a vertical mismatch makes the result unverified, and the vertical check also decides between the two readings.
    Without that box (an older listener, a failed call, a box that is not the exact curve extents) the check stays
    horizontal, y_extent_checked is false and y_extent_note says why."""
    mo = data.get("modern_outline")
    if not (isinstance(mo, dict) and mo.get("available") and isinstance(mo.get("contours"), list)):
        raise ToolError("The listener's outline reply was malformed, so it was not trusted.")
    el = data.get("elements") if isinstance(data.get("elements"), dict) else {}
    shapes = el.get("shapes") if el.get("available") else None
    mats, elements, mapping_note = None, None, None
    if isinstance(shapes, list) and shapes:
        counts = [sh.get("contours") for sh in shapes]
        found = [_shape_matrix(sh) for sh in shapes]
        if (all(isinstance(c, int) and not isinstance(c, bool) and c >= 0 for c in counts)
                and all(m is not None for m in found) and sum(counts) == len(mo["contours"])):
            mats = [m for m, c in zip(found, counts) for _ in range(c)]
            elements = [{"index": si, "contours": counts[si], "shape_type": sh.get("shape_type"),
                         "is_composite": bool(sh.get("is_composite")), **_element_component_fields(sh),
                         "matrix": {k: _tidy_number(round(v, 6)) for k, v in zip(_MATRIX_KEYS, m)},
                         "description": _describe_matrix(m)} for si, (sh, m) in enumerate(zip(shapes, found))]
        else:
            mapping_note = ("FontLab's element list does not map onto the contours read (contour counts or matrices missing or "
                            "different), so no element transform was applied." + _COMPONENTS_UNKNOWN)
    else:
        mapping_note = f"FontLab's element transforms could not be read ({el.get('error') or 'no element list'}), so none was applied." + _COMPONENTS_UNKNOWN
    raw = _modern_outline_result(clean, mo, None, data, modern_first=True)
    result = raw
    lo, hi, y_why = _fontlab_ink_y(data)
    if mats is not None and not all(_is_identity(m) for m in mats):
        moved = []
        for ci, c in enumerate(mo["contours"]):
            nodes = []
            for n in c.get("nodes", []):
                x, y = _apply_matrix(mats[ci], n["x"], n["y"])
                nodes.append(dict(n, x=x, y=y))
            moved.append(dict(c, nodes=nodes))
        applied = _modern_outline_result(clean, dict(mo, contours=moved), None, data, modern_first=True)
        for c_out, c_in in zip(applied["contours"], mo["contours"]):
            for n_out, n_in in zip(c_out["node_list"], c_in.get("nodes", [])):
                n_out["raw_x"], n_out["raw_y"] = _tidy_number(n_in["x"]), _tidy_number(n_in["y"])
        y_applied, y_raw = _y_extent_ok(applied, lo, hi), _y_extent_ok(raw, lo, hi)
        ok_applied = applied["verification"]["status"] == "verified" and y_applied is not False
        ok_raw = raw["verification"]["status"] == "verified" and y_raw is not False
        if ok_raw and not ok_applied:
            result["coordinate_space"] = ("FontLab view (the modern layer's coordinates already include the element transform: they match "
                                          "FontLab's margins as read, and not with the transform applied again)")
        else:
            result = applied
            result["coordinate_space"] = ("FontLab view (FontLab's element transform, read directly, has been applied; raw_x / raw_y are the "
                                          "element's own values)")
            if ok_applied and ok_raw:
                settled, settle_note = _elements_settle(clean, mo, moved, shapes, found, counts)
                if settled:
                    result["verification"]["element_boxes_checked"] = True
                else:
                    result["verification"]["status"] = "unverified"
                    if settle_note:
                        result["verification"]["element_boxes_checked"] = False
                        result["verification"]["element_boxes_note"] = settle_note
                    if y_applied and y_raw:
                        result["verification"]["reason"] = ("the coordinates match FontLab's horizontal margins and its ink box both with and "
                                                             "without the element transform, so which reading is right cannot be told")
                    else:
                        result["verification"]["reason"] = ("the coordinates match FontLab's horizontal margins both with and without the element "
                                                             "transform, so the vertical placement cannot be confirmed on this route")
    if elements is not None:
        result["elements"] = elements
        result["notes"].extend(_component_notes(shapes))
    if mapping_note:
        result["notes"].append(mapping_note)
    v = result["verification"]
    y_ok = _y_extent_ok(result, lo, hi)
    if y_ok is None:
        v["y_extent_checked"] = False
        v["y_extent_note"] = y_why or "the computed box is not the exact curve extents, so it was not compared with FontLab's ink box"
        v["checked_against"] = ("FontLab's modern left sidebearing and ink width (horizontal only; the vertical extent was not checked, "
                                "see y_extent_note)")
        return result
    b = result["ink_bbox"]
    fl_lo, fl_hi = _tidy_number(round(lo, 3)), _tidy_number(round(hi, 3))
    v["y_extent_checked"] = True
    v["ink_box_vs_fontlab"] = {"box_bottom": b["bottom"], "box_top": b["top"], "fontlab_bottom": fl_lo, "fontlab_top": fl_hi, "y_ok": y_ok}
    v["checked_against"] = ("FontLab's modern left sidebearing and ink width, and FontLab's own ink box (layer.inkBox()) for the "
                            "vertical extent")
    if not y_ok and v["status"] == "verified":
        v["status"] = "unverified"
        v["reason"] = (f"the computed box matches FontLab's horizontal margins but not FontLab's own ink box vertically: computed y "
                       f"{b['bottom']}..{b['top']}, FontLab {fl_lo}..{fl_hi}")
    return result


def _source_step(sh: dict, m: dict):
    """v0.50 (listener 0.130): (True | False | "unknown", note). In step, a component's own box equals its source's box plus its offset
    (live 644-646); after a tool edit its source moved without it, it does not (live 650). Pure offsets only: nothing else was tested."""
    box, source = _box_sides(sh.get("ink_box")), _box_sides(sh.get("source_ink_box"))
    if box is None:
        return "unknown", f"FontLab's box of this element could not be used: {_box_problem(sh.get('ink_box'))}"
    if source is None:
        return "unknown", f"the box of its source glyph could not be used: {_box_problem(sh.get('source_ink_box'))}"
    if abs(m["m11"] - 1) >= 1e-6 or abs(m["m22"] - 1) >= 1e-6 or abs(m["m12"]) >= 1e-6 or abs(m["m21"]) >= 1e-6:
        return "unknown", "this element is scaled, slanted, rotated or mirrored; the comparison is proven for plain offsets only"
    expected = (source[0] + m["dx"], source[1] + m["dx"], source[2] + m["dy"], source[3] + m["dy"])
    if _same_box(box, expected):
        return True, None
    return False, f"FontLab holds this element at {_box_text(box)}; its source's box plus the element's offset gives {_box_text(expected)}"


def _apply_source_step(result: dict, data: dict) -> None:
    """v0.50: says for each component whether it is in step with its source, and makes the read unverified when one is not, whatever
    the box checks said: they compare with what FontLab holds for this glyph, which is then behind its source (live 638b, 640, 648)."""
    el = data.get("elements")
    if isinstance(el, dict) and isinstance(el.get("boxes_seconds"), (int, float)) and not isinstance(el.get("boxes_seconds"), bool):
        result["verification"]["element_boxes_seconds"] = _tidy_number(el["boxes_seconds"])      # v0.68 (listener 0.174): no element limit, timed
    shapes = el.get("shapes") if isinstance(el, dict) and el.get("available") else None
    rows = result.get("elements")
    if not isinstance(shapes, list) or not isinstance(rows, list) or len(shapes) != len(rows):
        return
    behind = []
    for index, (sh, row) in enumerate(zip(shapes, rows)):
        if sh.get("is_component") is not True or not ("ink_box" in sh or "source_ink_box" in sh):
            continue
        state, note = _source_step(sh, row["matrix"])
        row["source_in_step"] = state
        if note:
            row["source_in_step_note"] = note
        if state is False:
            behind.append((index, row.get("component_glyph") or "its source glyph", note))
    if not behind:
        return
    v = result["verification"]
    earlier = v.get("reason")
    detail = "; ".join(f"element {index} ({name}): {note}" for index, name, note in behind)
    v["status"] = "unverified"
    v["reason"] = f"out of step with its component source: {detail}" + (f". Also: {earlier}" if earlier else "")
    sources = ", ".join(dict.fromkeys(repr(name) for _index, name, _note in behind))
    result["agent_instruction"] = (f"Tell the person that glyph {result.get('name')!r} does not match the current state of {sources}: FontLab still holds "
                                   "the older position for the component. A real edit of the source glyph in FontLab has brought such glyphs back in step; "
                                   "a change made through a tool may not, and waiting or reopening the glyph did not.")


def _modern_first_result(clean: str, data: dict) -> dict:
    """v0.50: the modern-first read, then the check of each component against its source."""
    result = _modern_first_read(clean, data)
    _apply_source_step(result, data)
    return result


_STALE_MARGIN_TOLERANCE = 0.05   # font units: modern sidebearings / advance vs the legacy reader's margins


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
    if data.get("source") == "modern":
        return _modern_first_result(clean, data)
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
    if modern_off:
        result["notes"].append("GLYPHBRIDGE_MODERN=0: this outline was read through FontLab's legacy layer. If the glyph is a Power Brush "
                               "glyph, FontLab may now flatten it at its next refresh (the next create, delete or Unicode change); "
                               "do not save the font before checking it.")
    return result


# --------------------------------------------------------------------------
# MCP tools (thin wrappers)
# --------------------------------------------------------------------------

mcp = MCPServer("Glyphbridge FontLab")


def _tool():
    """mcp.tool() with SAVE_KEYS in the tool description replaced by this system's save shortcut (v0.40): descriptions are
    read once, when the tool is registered at startup."""
    register = mcp.tool()

    def decorate(fn: Any) -> Any:
        if fn.__doc__:
            fn.__doc__ = fn.__doc__.replace("SAVE_KEYS", SAVE_SHORTCUT)
        return register(fn)
    return decorate


@_tool()
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


@_tool()
def get_current_font(ctx: Context | None = None) -> dict[str, Any]:
    """Get live details about the font currently open in FontLab 8.

    Returns family and style name, file path, glyph count, and vertical
    metrics (units per em, ascender, descender, cap height, x-height).
    Fields that could not be read are returned as null and explained in 'notes'.
    The PostScript names are the ones FontLab's Font Info shows, read from the font package when it can be matched to this font
    (postscript_names_source says where they came from; legacy_* fields appear when FontLab's older view differs). Whether a
    name was typed by a person or filled in by FontLab is not known: do not call a name 'unset' or 'a placeholder'.

    Also checks the font's .notdef glyph (see check_notdef): the result has a 'notdef' entry, and if .notdef is missing or
    empty a warning dialog is shown to the person in FontLab (once per font per session). In that case this call can
    take up to two minutes while the dialog waits for a click; that is normal, not a hang.
    """
    _note_client(ctx)
    return _with_font(read_current_font_checked)


@_tool()
def list_glyphs(ctx: Context | None = None) -> dict[str, Any]:
    """List the names of all glyphs in the font currently open in FontLab 8.

    Every font has a '.notdef' glyph (normally the first one): expect it in this list. A brand-new font may contain
    nothing else, and its .notdef is empty at first; that is normal.
    """
    _note_client(ctx)
    return _with_font(read_glyph_names)


@_tool()
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
    exact work. A glyph that holds a component: on the modern route its nodes are returned where FontLab draws them, each element
    says is_component and names its source (component_glyph, component_layer), and a note says the nodes are that glyph's outline,
    not one of this glyph's own; the source glyph is not read separately. Each component also says source_in_step (needs listener 0.130): true, false, or
    "unknown" for anything but a plain offset. false means FontLab holds this glyph behind its source: the status is then 'unverified' and agent_instruction says what
    to tell the person. An accent placed inside its base does not change the glyph's outer box, so it is verified element by element (element_boxes_checked). On the older legacy route a composite glyph reports a note,
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
    advance_width. 'verified' there means the box (for curves: the exact extents of the cubic and quadratic segments, computed)
    equals FontLab's left sidebearing and ink width; contours that mix cubic and quadratic points, or are malformed, stay
    'unverified' with a reason. Since listener 0.121 the box is also compared with FontLab's own ink box vertically, and 'verified'
    needs both ('y_extent_checked': true, 'ink_box_vs_fontlab'); when that comparison was not possible, 'y_extent_checked' is false
    and 'y_extent_note' says why. An open contour ('closed': false) runs from its first node to its last with no closing segment:
    it is checked the same way, its direction_computed is 'not applicable (open contour)', its svg_path ends without Z, and a note
    names it.

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


@_tool()
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


@_tool()
def create_glyph(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Create one new, empty glyph in the font currently open in FontLab 8.

    The glyph has no contours yet - this only adds it to the font by name.
    Fails clearly (raises an error) if a glyph with that name already
    exists, or if FontLab did not actually add it. Success is only ever
    reported after re-checking the font's glyph list confirms the glyph
    is really there.

    In a font with one master the new glyph also gets its editable layer at once (the reply says layer_created). When it
    cannot, the glyph is still created, 'layer_note' says why, and the person must be told not to use Glyph > Add Component
    on that glyph: FontLab crashed on glyphs without a layer in testing.

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
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(create_new_glyph, name)


@_tool()
def create_font(family: str | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Make a new, empty, UNSAVED font in FontLab 8, like File > New Font. It works whether or not other fonts are open, and the
    new font becomes the font in front, so the next tools work on it.

    Without 'family' FontLab names the font itself, as File > New Font does: Unnamed, then Unnamed1, Unnamed2, ... (style
    Regular, 1000 units per em, one master, one empty .notdef). With 'family' (printable ASCII, no leading or trailing space, none of
    [](){}<>/%, at most 55 characters without its spaces) the font is named as Font Info's Build Names would name it, style Regular: Family name = family, Full name =
    family + " Regular", PostScript name = family without spaces + "-Regular", Style group = family. Each name is read back.

    What FontLab will NOT show, and other things the person must know, come back in 'person_notes' (they are also printed in
    FontLab's OUTPUT panel). Tell the person every one of them: FontLab's tab and FONTS panel may keep the temporary name for
    a while (a display delay; Font Info shows the real names). If you have not yet done so in this conversation, also tell the
    person that FontLab's OUTPUT panel lists every change Glyphbridge makes, with its warnings, and is worth keeping open.

    Success is reported only when FontLab's number of open fonts went up by one and the new font is the one in front.
    Like every Glyphbridge tool this NEVER saves: the font exists in FontLab's memory only, and the person saves it (File menu
    or SAVE_KEYS). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(create_new_font, family)


@_tool()
def get_glyph_width(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Get the advance width of one glyph in the font currently open in FontLab 8.

    Width is in font units, on the same scale as the font's units-per-em
    (for a 1000-upm font, typical letter widths run a few hundred units).
    The width is FontLab's modern advance width (width_source "modern"), cross-checked with FontLab's older view. When the two
    disagree, the reply adds legacy_width, widths_disagree and width_note: tell the person both values, and do not choose one,
    since which one FontLab saves is not known. When the modern width cannot be read, the older view's width is given instead
    (width_source "legacy", with a width_note saying why). Reading changes nothing.
    """
    _note_client(ctx)
    return _with_font(read_glyph_width, name)


@_tool()
def set_glyph_width(name: str, width: float, ctx: Context | None = None) -> dict[str, Any]:
    """Set the advance width of one glyph in the font currently open in FontLab 8.

    Width is in font units, same scale as get_glyph_width. This changes ONLY the advance width (the space the glyph takes when
    typed): the outline does not move, so the right sidebearing changes and the left one does not. To place the outline inside
    the width use set_glyph_sidebearings instead. A glyph that has an outline but no editable layer yet is refused: the person
    must open it once in an editor tab in FontLab. The width is rounded to a whole unit (a half rounds up), as FontLab's own
    width field does (seen live); the reply's width_rounded says when that happened. This does not
    require confirmation in FontLab, unlike delete_glyph, since it is a
    reversible value change rather than a destructive one. Success is only
    reported after re-reading the glyph confirms the new width took effect.
    The reply's display_note explains that parts of FontLab's screen (centre info box, grid thumbnail) refresh only when the
    person switches to the grid tab and back; the saved numbers are right.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_width, name, width)


@_tool()
def get_glyph_sidebearings(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Read the left and right sidebearing, the advance width and the ink width of one glyph that has an outline.

    Values are FontLab's exact values in font units: advance width = left + ink width + right. FontLab's editor panel and
    font grid bar show sidebearings rounded DOWN to whole units (seen live: 61.75 shows as 61, -38.25 as -39), so when a
    value has a fraction, give the person the exact value and say that FontLab's panel shows it rounded down.
    The glyph needs an editable layer (the person opens it once in an editor tab in FontLab); otherwise this answers with
    an error that says so. Reading changes nothing.
    """
    _note_client(ctx)
    return _with_font(read_glyph_sidebearings, name)


@_tool()
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


@_tool()
def get_kerning_groups(groups: list[str] | None = None, glyphs: list[str] | None = None, all_groups: bool | None = None,
                       confirmed_large_read: bool | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Read the kerning groups (FontLab's kerning classes) of the font currently open in FontLab 8: which glyphs each group holds,
    and on which side it kerns. Reading changes nothing.

    Give groups (kerning group names) and / or glyphs (glyph names), or all_groups=true alone to list every kerning group. Each group
    comes with its side ('left': its glyphs are kerned as the LEFT glyph of a pair, FontLab's Kerning Left; 'right': as the RIGHT glyph;
    'both'), its members, its id and 'confirmed'. Each glyph comes with the kerning groups that hold it and their sides; an empty list
    means it is in no kerning group, which is a fact, not an error. A name that does not exist is an 'error' for that name only.
    Every read is cross-checked between two FontLab sources: a group with confirmed false is not settled; report its mismatch, never
    pick a version yourself. Read only what the task needs. There is no upper limit, but more than 250 kerning groups in an all_groups
    read, or more than 250 names in one call, is refused until the PERSON has approved it: say how many and why, ask, and only after a
    yes repeat the call with confirmed_large_read=true. Never set confirmed_large_read=true on your own.
    Kerning groups only: OpenType classes and Glyph tags are not read by this tool. It reads the current master of the current font,
    the one whose window is in front; with several fonts open it refuses when that font cannot be matched to its kerning table (for
    example a new, unsaved font). Other masters are not covered. Needs listener v0.190.
    """
    _note_client(ctx)
    return _with_font(read_kerning_groups, groups, glyphs, all_groups, confirmed_large_read)


@_tool()
def set_kerning(pairs: list[list[Any]], confirmed_large_write: bool | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Set kerning for glyph pairs or kerning classes in the font currently open in FontLab 8: pairs is a list of [left, right, value]
    such as [["A", "V", -60], ["T", "@o", -40]], two sides and a value in font units (negative = closer).

    A side is a glyph name, or '@' (the plain ASCII @) followed by a kerning group's name (see get_kerning_groups): "@o" means the
    kerning group o, "o" the glyph o. Two glyphs give a glyph : glyph entry; a pair whose glyphs belong to classes then gets an
    exception for these two glyphs only (exception_over_class). With a class side the entry is glyph : class, class : glyph or
    class : class ('kind'), and FontLab applies it to every member pair that has no exception of its own: tell the person how far it
    reaches ('classes' gives each class's side and member_count). A class must be a kerning group on a side that fits: a left or
    both group on the left, a right or both group on the right; anything else (an OpenType class, an unknown name, a wrong side) is
    refused before any change. A class pair is verified by re-reading its entry and ONE sample glyph pair ('sample',
    sample_verdict); its 'before' and 'after' are the sample's, and entry_before is the class entry's own value before. When a glyph
    side's name is also a kerning group's name, the pair's 'note' says the glyph was meant and how to name the group. Every check runs
    before the first change, and every pair is verified by re-reading it; the reply gives 'before' (the value FontLab applied,
    with its source) and 'after'. If a pair cannot be confirmed the tool stops there and says which pairs were set.
    Read the pairs first with get_kerning when the task depends on their current values. More than 250 pairs in one call is
    refused until the PERSON has approved it: ask them, and only after a yes repeat the call with confirmed_large_write=true
    (a class pair counts as one pair). Never set confirmed_large_write=true on your own.
    Values must be whole numbers: FontLab keeps kerning in whole font units, so a fraction is refused.
    Since listener 0.136, after a write that changed an entry, FontLab is asked to refresh its KERNING panel (fontlab_panel_refresh).
    With an older listener, or when that call was not made or failed, tell the person: FontLab's KERNING panel shows such pairs (new ones,
    and new values of listed ones) only after switching to another open font and back, or after the font is saved and reopened; the
    reply says which applies. Unsaved they are lost when the font is closed. Since
    listener 0.134 the reply's fontlab_changed_mark says that FontLab was told of the change; with an older listener, or when the
    reply has save_question_note, FontLab asks no save question for them, so they are lost silently.
    Edit > Undo cannot take them back. To revert a glyph pair: if 'before' was a glyph : glyph entry, call set_kerning again with that
    value; if it was 'none' or a class value, call remove_kerning to remove the new glyph : glyph entry and restore the prior state.
    To revert a class pair: entry_before a number, set it again; entry_before null, remove_kerning for the same '@' pair.
    Setting a pair to 0 leaves an explicit zero entry. It changes the current font, the one whose window is in front; with several fonts
    open it refuses when that font cannot be matched to its kerning table (for example a new, unsaved font). Other masters, the
    entries not named and feature-based kerning are not changed. Needs listener v0.124; a class side needs listener v0.194.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_kerning, pairs, confirmed_large_write)


@_tool()
def remove_kerning(pairs: list[list[Any]], confirmed_large_write: bool | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Remove kerning pairs from the font currently open in FontLab 8: pairs is a list of [left, right] such as [["A", "V"], ["T", "@o"]],
    two sides each.

    A side is a glyph name, or '@' (the plain ASCII @) followed by a kerning group's name: "@o" means the kerning group o, "o" the
    glyph o. Each pair's entry of that kind is removed from the current master's kerning table: two glyphs remove the glyph : glyph
    entry only, never class kerning; a class side removes the glyph : class, class : glyph or class : class entry ('kind'), whose
    value then no longer applies to any member pair: tell the person. A class must be a kerning group on a side that fits (left or
    both on the left, right or both on the right); anything else is refused before any change. For a class pair 'before' and 'after'
    belong to ONE sample glyph pair ('sample'), and entry_before is the removed entry's own value. When a glyph side's name is also a
    kerning group's name, the pair's 'note' says the glyph was meant and how to name the group. Removing is not the same as setting 0:
    set_kerning with 0 keeps an explicit zero entry, this tool takes the entry away. When a kerning class also kerns a glyph pair, the
    pair then kerns at that class value, not at 0 (class_value_applies): tell the person. A pair with no entry of its kind is reported
    as 'no entry' with a note (nothing to remove; a class may still kern it), and the other pairs go on. Every check runs before the first change, and every removal is verified by re-reading it; the reply
    gives 'before' (the value FontLab applied, with its source) and 'after'. If a removal cannot be confirmed the tool stops there and
    says which pairs were removed. Read the pairs first with get_kerning when the task depends on their current values. More than 250
    pairs in one call is refused until the PERSON has approved it: ask them, and only after a yes repeat the call with
    confirmed_large_write=true. Never set confirmed_large_write=true on your own.
    After a removal FontLab is told that the font changed (fontlab_changed_mark) and asked to refresh its KERNING panel
    (fontlab_panel_refresh). Edit > Undo is not known to bring a removed pair back: to restore a glyph pair, call set_kerning with its
    'before' value; a class pair, with the same '@' pair and its entry_before. It changes the current font, the one whose window is in
    front; with several fonts open it refuses when that font cannot be matched to its kerning table (for example a new, unsaved font).
    Other masters and feature-based kerning are not changed. Needs listener v0.192; a class side needs listener v0.194.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(remove_kerning_write, pairs, confirmed_large_write)


@_tool()
def rename_kerning_group(group: str, new_name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Rename ONE kerning group (FontLab's kerning class) of the font currently open in FontLab 8, in its current master.

    group is the group's current name and new_name the new one; a leading '@' (as set_kerning writes classes) is allowed on either. Names
    are 1 to 63 characters from A-Z a-z 0-9 . _ -. Read the group first with get_kerning_groups when the task depends on it. Refused before
    any change: a group that is not a kerning group confirmed by both of FontLab's sources (an OpenType class, an unknown name), and a
    new_name that is already the name of a kerning group or of any other class of the font. A new_name that is also a glyph's name is
    allowed (FontLab itself names classes after a member; same_name_glyph says so): in set_kerning and remove_kerning '@name' then means the
    group. The rename is verified by re-reading both sources: the same members and side under the new name. The group's kerning entries
    follow the new name. FontLab gives a renamed group a NEW id (id_before, id_after): that is expected. No question is asked in FontLab: a
    rename is undone by renaming back. After the rename FontLab is told that the font changed (fontlab_changed_mark) and asked to refresh its
    panels (fontlab_panel_refresh); fontlab_caught_up says whether one member glyph already carries the new id - if not, FontLab's panels
    and get_kerning for the members may show the old state until the person switches to another font and back. Edit > Undo is not known to
    take it back. It changes the current font, the one whose window is in front; with several fonts open it refuses when that font cannot
    be matched to its kerning table (for example a new, unsaved font). Other masters are not changed. Needs listener v0.200.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(rename_group_write, group, new_name)


@_tool()
def remove_kerning_group(group: str, pairs: str, ctx: Context | None = None) -> dict[str, Any]:
    """Remove ONE kerning group (FontLab's kerning class) from the font currently open in FontLab 8, in its current master.

    group is the group's name (a leading '@' is allowed). pairs is REQUIRED and says what happens to the group's kerning: "keep" - the
    kerning stays, FontLab turns each class entry into entries of the members with the same values (a class : glyph or glyph : class
    entry becomes one glyph pair per member; a class : class entry becomes one class : glyph or glyph : class entry per member of the
    removed group), so the table may grow; "delete" - the group's own kerning entries are deleted with it. If the person has not said
    which, ask them; never choose for them. Read the group first with get_kerning_groups. A group that is not a kerning group confirmed by
    both of FontLab's sources is refused before anything is asked. Otherwise this shows a Yes/No question inside FontLab (default No) that
    names the group, its members and what happens to its kerning, and only proceeds if a person clicks Yes there: this tool cannot remove
    anything on its own. Expect the call to take a while (up to two minutes) while the question waits; that is normal, not a hang. The
    removal is verified by re-reading both of FontLab's sources; the kerning entries themselves are not read (table_size_before and
    table_size_after give the size of the table). No Glyphbridge tool can bring a removed group back. After the removal FontLab is told
    that the font changed (fontlab_changed_mark) and asked to refresh its panels (fontlab_panel_refresh); fontlab_caught_up says whether
    one member glyph already left the group - if not, FontLab's panels and get_kerning for the members may show the old state until the
    person switches to another font and back. Edit > Undo is not known to take it back. It changes the current font, the one whose window
    is in front; with several fonts open it refuses when that font cannot be matched to its kerning table (for example a new, unsaved font).
    Other masters are not changed. Needs listener v0.200.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(remove_group_write, group, pairs)


@_tool()
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
    back; the saved numbers are right. If other glyphs use this glyph as a component, they may not follow the change (the
    reply's component_note; get_glyph_outline on such a glyph says source_in_step).

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_sidebearings, name, left, right)


@_tool()
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

    A glyph without an editable layer (for example one in a multi-master font, or made by a listener older than 0.127) gets one from
    this tool (the reply then says layer_created); nobody needs to open the glyph in an editor tab. If the layer cannot be created safely (no other glyph of the font shows the right layer
    name, or they disagree) the call is refused and says so.
    Success (verified: true) is only reported after re-reading the layer confirms 1 shape, one node per point and one contour per polygon; the reply
    also gives left, right, advance_width and ink_width. Drawing does NOT change the advance width: set it afterwards with
    set_glyph_width, or place the outline together with the width via set_glyph_sidebearings.
    The reply's display_note explains that parts of FontLab's screen (editor panel numbers, centre info box, grey ghost fill, grid
    thumbnail) may show old values until the person switches to the grid tab and back; the saved shape is right.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_polygon, name, points, contours)


@_tool()
def draw_path(name: str, contours: list[list[dict[str, Any]] | dict[str, Any]], ctx: Context | None = None) -> dict[str, Any]:
    """Draw contours (closed, or open) with straight AND cubic curve segments into an EMPTY glyph in the font currently open in FontLab 8.

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

    OPEN contours: give a contour as {"points": [...], "closed": false} instead of a plain list. It runs from its first point to its
    last, with no closing segment, so it has no fill (a stroke or a construction line). It needs 2 to 500 points; its FIRST point
    cannot have c1 / c2 (there is no closing segment), and its first and last points cannot be smooth (one neighbour each). Open and
    closed contours can be mixed in one call. Needs listener 0.126. Example, an open arch from (105, 104) to (398, 104):
    [{"points":[{"x":105,"y":104},{"x":398,"y":104,"c1":{"x":105,"y":280},"c2":{"x":398,"y":255}}],"closed":false}].
    The reply then lists closed per contour and an agent_instruction: tell the person that open contours have no fill, and that
    FontLab's export dropped open contours without a warning in testing (TrueType and OpenType PS, default settings), so a glyph
    that must appear in a generated font needs closed contours.

    RULE B (whole units): FontLab stores whole numbers here. Every coordinate is rounded to the nearest whole unit (a half rounds up)
    and the reply lists each coordinate that changed in coordinates_rounded (with a rounding_note); give whole numbers to avoid that.

    The glyph must hold nothing yet, otherwise the call is refused and nothing changes. A glyph made by create_glyph has no editable
    layer: the tool creates it by itself (the reply says layer_created). Success (verified: true) is only reported after the re-read layer
    matches your request node by node (nodes_match). get_glyph_outline computes the exact extents of cubic curves, so it reports
    such outlines as verified when the computed cubic extents equal FontLab's own margins; the node list is exact. Drawing does NOT change the advance width: use set_glyph_width or
    set_glyph_sidebearings afterwards. The reply's display_note explains that parts of FontLab's screen may show old values until the person
    switches to the grid tab and back.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_path, name, contours)


@_tool()
def move_nodes(name: str, moves: list[dict[str, Any]], ctx: Context | None = None) -> dict[str, Any]:
    """Move existing nodes of one glyph in the font currently open in FontLab 8: on-curve points and curve control points alike.

    Read the glyph with get_glyph_outline FIRST: its contours[].index and the position of a node in node_list are the numbers used
    here (control points are nodes too, so they count). `moves` is a list of 1 to 200 moves, each
    {"contour": C, "node": N, "from": {"x": number, "y": number}, "to": {"x": number, "y": number}}:
      - "from" is where the node is NOW, exactly as get_glyph_outline reported it. If any node is somewhere else (the person may have
        edited the glyph since your last read), the whole call is refused and NOTHING moves: read the glyph again and retry.
      - "to" is its new position, in font units, y up. Each node may appear only once per call.
    Example: move the second node of contour 0 from (300, 0) to (350, 0):
    [{"contour": 0, "node": 1, "from": {"x": 300, "y": 0}, "to": {"x": 350, "y": 0}}]

    IMPORTANT: moving an on-curve node does NOT take its control points along (FontLab's mouse does, this tool does not). To move a
    curve point together with its handles, give the handles their own moves in the same call. A move that would leave a smooth node's
    two neighbours off one straight line through it (more than 2 degrees) is refused and nothing moves; move its handles in the same call.

    Only a glyph with exactly ONE plain shape is supported for now: a glyph with several shapes, a component, a Power Brush or other
    composite shape, or an element transform (position, scale, rotation set with FontLab's Element tool) is refused and nothing moves.

    Every check is made before the first node moves. Afterwards every node of the glyph is read back: success (moved: true,
    verified: true, nodes_match: true) means each moved node is at "to" and every other node, node kind and smooth flag is unchanged.
    The advance width is not changed. left, right and ink_width are COMPUTED from the re-read nodes (exact curve extents included)
    and FontLab's advance width: after a node move FontLab's own sidebearings and ink box lag for a while (seen live), so they are
    reported apart in fontlab_sidebearings with fontlab_sidebearings_current. When they lag, tell the person person_note once.

    RULE B (whole units): every "to" coordinate is rounded to the nearest whole unit (a half rounds up); the reply lists each changed one
    in coordinates_rounded. "from" is compared as given.

    If the re-read does NOT match (moved: false with mismatches, before and after), the glyph may be partly moved. Nothing is restored
    automatically: tell the person, and move nodes back only with their agreement.

    FontLab's Edit > Undo does not take a move back (seen live once); moving the nodes back with move_nodes does. When the outline
    changed, the reply's undo_note says so in plain words: tell the person once per conversation.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    Needs listener 0.153.
    """
    _note_client(ctx)
    return _with_font(write_glyph_moves, name, moves)


@_tool()
def add_component(name: str, component: str | None = None, x: int = 0, y: int = 0, components: list | None = None,
                  confirmed_untested_size: bool = False, ctx: Context | None = None) -> dict[str, Any]:
    """Place components in the glyph `name` of the font currently open in FontLab 8, an empty glyph or one that already holds contours,
    components or Power Brush shapes: ONE glyph `component` at offset (x, y), or SEVERAL at once with `components`, a list of
    {"component": glyph name, "x": whole number, "y": whole number} (x and y default to 0). Give one form or the other, never both.

    A component is a live reference: the glyph `name` then draws the component glyph's outline, moved by (x, y) font units (y up), and
    follows later edits of it. x and y must be whole numbers from -10000 to 10000; (0, 0) places a component exactly where its glyph is
    drawn. In the list the same glyph may appear more than once (for example a radical repeated in a CJK character); each entry becomes
    its own component, in list order.

    For now, only this is supported (anything else is refused and NOTHING changes):
      - `name` must exist with exactly ONE layer, the active one (create_glyph gives one in a font with one master; checked for every
        target since listener 0.187, before only for a glyph that is not empty); if it is not empty, its automatic layer must be off
        and it must hold only contours, components and Power Brush shapes (needs listener 0.186);
      - every component glyph must exist and hold only plain contours (no component of its own, no Power Brush or other composite shape);
      - the font must have exactly ONE master; no scale, rotation, mirroring or anchors; glyph names must not contain "+";
      - in the list form no component glyph name may contain an underscore ("_"): FontLab's recipe build of several glyphs reads it as
        a ligature of its parts and drops the glyph or places the parts instead (seen live). Place such a glyph with the single form.

    SIZE: up to 30 components in one call have been tested (2 to 5, 15 and 30). More than 30 is allowed but is unknown territory: the
    first call then changes nothing and returns needs_confirmation with an agent_instruction. Tell the person how many components it
    would place and that only up to 30 has been tested, and ask. Only after they agree, call again with confirmed_untested_size=true.
    There is no other limit than the size of one request (about 1,000,000 bytes, roughly 20,000 entries).

    How it works: FontLab's own recipe build places the components (FontLab puts each one where it likes and sets the width to 500);
    every offset is then set as asked, FontLab's recipe is cleared, and the advance width is written back to what it was. Every check is
    made before the first change. Afterwards the glyph is read back: success (placed: true, verified: true) means exactly the listed
    components, in order, each at its offset and drawn where expected, the recipe cleared, and the component glyphs, the advance width and
    the glyph count unchanged. The advance width is NOT changed: set it with set_glyph_width if the person wants one. The list form's
    reply gives timing in seconds.

    A glyph that is NOT empty (placement: "temporary layer"; an empty one says "empty layer"): FontLab's build would replace what the
    glyph holds (seen live), so within this one call the tool adds a temporary layer to the glyph, builds the components there, sets
    their offsets and source layers, adds them to the glyph's own layer after what it holds, and removes the temporary layer again.
    Success (placed: true, verified: true, existing_kept: true) means everything the glyph held before is unchanged and first, followed by
    exactly the listed components in order, each at its offset and drawn where expected; the glyph has its one layer again, and the
    advance width, the component glyphs and the glyph count are unchanged. If this route fails partway, the tool puts the glyph back as
    it was (it removes the components it added and the temporary layer, and writes the width back) and reads it again: restore.restored
    true means the glyph is confirmed as before and nothing was placed; otherwise the glyph may hold part of it or the temporary layer
    (see restore, layers_after, component_states, components_after).

    If the re-read of an EMPTY glyph does NOT confirm it (placed: false), the glyph may hold part of it. In the list form placing stops at the first failure;
    then the automatic layer is switched off, the recipe cleared and the width written back (cleanup says what worked);
    component_states says for each entry: placed, at FontLab's position, left by the build, missing after the build, not reached or
    unknown, and components_after lists what the glyph holds. Nothing else is restored automatically. Tell the person which
    components are left; repair or repeat only with their agreement.

    Limits seen in testing: FontLab's Edit > Undo offers nothing to take the component back (seen live once: Undo was greyed out).
    remove_component removes a component again (listener 0.179). In one unexplained run, two components
    placed by FontLab's recipe build later became plain contours with no request to change them; the reply can only confirm the moment of
    its own call. If it matters, read the glyph again later with get_glyph_outline. In research, components also became plain contours
    when a temporary layer stayed in a glyph while other calls ran (a create_glyph or a listener restart, then FontLab's next display
    refresh); this tool never leaves one behind on success, and its restore removes it after a failure. A glyph whose empty active layer
    sat beside a full one was once treated as empty, and the component was placed on that layer naming a layer its source does not have
    (seen live); listener 0.187 refuses any glyph with more than one layer instead.

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    Needs listener 0.169 (one component) or 0.174 (components; components_after since 0.175; the single form writes the width back
    since 0.178, and both forms report width_set_by_build, the width FontLab's build had set, when it differed); a glyph that is not
    empty needs listener 0.186 (an older one refuses it and changes nothing); the one-layer rule for every target needs listener 0.187.
    """
    _note_client(ctx)
    if components is not None:
        if component is not None or x != 0 or y != 0:
            raise ToolError("Give either component (with x and y) or components (a list), not both.")
        return _with_font(write_glyph_components, name, components, confirmed_untested_size)
    if component is None:
        raise ToolError("Give component (one glyph name) or components (a list of {\"component\", \"x\", \"y\"}).")
    if confirmed_untested_size is not False:
        raise ToolError("confirmed_untested_size belongs to the components list, not to a single component.")
    return _with_font(write_glyph_component, name, component, x, y)


@_tool()
def remove_component(name: str, index: int | None = None, component: str | None = None, x: float = 0, y: float = 0,
                     components: list | None = None, ctx: Context | None = None) -> dict[str, Any]:
    """Remove components from the glyph `name` of the font currently open in FontLab 8: ONE component with index, component, x and y,
    or SEVERAL at once with `components`, a list of {"index", "component", "x", "y"}. Give one form or the other, never both.

    First read the glyph with get_glyph_outline. Its element list numbers the glyph's elements from 0; a component element names its
    source (component_glyph) and its matrix gives its offset (dx, dy). For each component to remove, give that index and, as a check,
    the source and offset you read there. If the glyph does not hold exactly that at that index (it changed since you read it), the
    WHOLE call is refused and NOTHING changes: read the glyph again. In the list every index refers to the glyph as you read it before
    the call (the tool removes from the highest index down, so the others do not shift); give each index once. There is no size limit.

    For now, only this is supported (anything else is refused and NOTHING changes):
      - the font must have exactly ONE master, and the glyph its layer;
      - the glyph's automatic layer must be off (an automatic glyph is FontLab's to rebuild);
      - the other elements may be contours or components; a glyph holding a Power Brush or other composite shape is refused.
    A recipe FontLab keeps on the glyph's layer is left as it is and reported (recipe_kept).

    Afterwards the glyph is read back: success (removed: true, verified: true) means the named components are gone and every other
    element is exactly where and what it was (its source or contours, matrix and drawn box), and the component glyphs, the advance width
    and the glyph count are unchanged. Removing the last component leaves an empty glyph that keeps its layer (empty_after). If FontLab
    changed the advance width, it is written back and reported (width_changed_by_removal). The reply gives timing in seconds.

    If the re-read does NOT confirm it (removed: false), the glyph may have changed partly: removal stops at the first failure;
    entry_states says for each entry: removed, called, not confirmed, call failed or not reached, and components_after lists what the
    glyph holds. Nothing is restored automatically. Tell the person; repair or repeat only with their agreement.

    Limits seen in testing: FontLab's Edit > Undo offers nothing to take a removal back (seen live once: Undo was greyed out). To put
    a component back, use add_component (listener 0.186 places components also into a glyph that is not empty).

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). Do not remind the person after each step: call finish_changes ONCE when the whole task package is finished.
    Needs listener 0.179.
    """
    _note_client(ctx)
    if components is not None:
        if index is not None or component is not None or x != 0 or y != 0:
            raise ToolError("Give either index, component, x and y (one component) or components (a list), not both.")
        if not isinstance(components, list) or not components:
            raise ToolError("components must be a non-empty list of {\"index\", \"component\", \"x\", \"y\"}.")
        entries = [_check_remove_entry(c, f"components[{i}]") for i, c in enumerate(components)]
        return _with_font(write_glyph_remove_components, name, entries, "list")
    if index is None or component is None:
        raise ToolError("Give index and component (with x and y, as get_glyph_outline shows them), or components (a list).")
    entry = _check_remove_entry({"index": index, "component": component, "x": x, "y": y}, "the request")
    return _with_font(write_glyph_remove_components, name, [entry], "single")


@_tool()
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


@_tool()
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
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(write_glyph_unicode, name, codepoint)


@_tool()
def delete_glyph(name: str, ctx: Context | None = None) -> dict[str, Any]:
    """Delete one glyph from the font currently open in FontLab 8.

    This shows a Yes/No confirmation dialog inside FontLab itself, and only
    proceeds if a person clicks Yes there - this tool cannot delete anything
    on its own. Expect this call to take a while (up to two minutes) if the
    dialog is waiting on a response; that is normal, not a hang. Deletion is
    permanent for this editing session and cannot be undone through this
    bridge. Success is only ever reported after re-checking the font's
    glyph list confirms the glyph is really gone.

    A deleted glyph cannot be reported to FontLab as changed, so the listener tells FontLab through one surviving glyph, whose content
    does not change: fontlab_changed_mark says what was done and via_glyph names that glyph. save_question_note appears when this was
    not possible (for example when only .notdef is left).

    Like every Glyphbridge tool this changes the font in FontLab's memory only and NEVER saves it: the person saves
    (File menu or SAVE_KEYS). The reply's font_modified says whether the font really changed. Do not remind the person
    after each step: call finish_changes ONCE when the whole task package is finished.
    """
    _note_client(ctx)
    return _with_font(delete_existing_glyph, name)


@_tool()
def finish_changes(ctx: Context | None = None) -> dict[str, Any]:
    """Call this ONCE when you have finished a whole package of changes to the font (creations, width or Unicode edits,
    deletions), and never per step. It counts the changes made through Glyphbridge since the last call and returns
    'save_reminder': show it to the person in the chat in bold, exactly as written, after your summary. If nothing was
    changed, save_reminder is null and you say nothing about saving.

    Glyphbridge never saves the font and never opens a dialog for this: saving is the person's job (File menu or SAVE_KEYS),
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
