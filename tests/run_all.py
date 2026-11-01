r"""Run the four stub test harnesses and compare their output with the saved expected output.

    python tests/run_all.py            # check (exit code 0 = everything as expected, 1 = something differs, 2 = a script was not found)
    python tests/run_all.py --update   # after REVIEWING a legitimate change, re-save the expected output

Only the standard library is needed; FontLab and the MCP SDK are stubbed.

Location: <repository folder>\tests, i.e. inside the project folder, next to venv\,
glyphbridge_mcp_server.py and a copy of glyphbridge_fontlab_mcp_listener.py (the harnesses read both from the PARENT of tests/ first).
The listener FontLab actually runs lives in ...\Documents\FontLab\FontLab 8\Scripts\ (override with the
GLYPHBRIDGE_FONTLAB_SCRIPTS environment variable); run_all.py prints which files it tested, warns if that copy differs, and warns if a file with a
pre-rename name (glyphbridge_listener.py / glyphbridge_server.py) still exists in the project or Scripts folder."""
import difflib, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_ENV = "GLYPHBRIDGE_FONTLAB_SCRIPTS"   # optional: folder FontLab runs the listener from (default: see report_files)
LISTENER_FILE = "glyphbridge_fontlab_mcp_listener.py"
SERVER_FILE = "glyphbridge_mcp_server.py"
OLD_FILES = ("glyphbridge_listener.py", "glyphbridge_server.py")   # names before v0.47 / v0.11: must not linger anywhere
JOBS = (("stub_listener_tests.py", "expected_listener_output.txt"),
        ("server_analysis_tests.py", "expected_server_output.txt"),
        ("notdef_tests.py", "expected_notdef_output.txt"),
        ("create_unicode_tests.py", "expected_create_unicode_output.txt"))


def locate(name):
    """Same rule as the harnesses: the project folder (the parent of tests/) first, then tests/ itself."""
    for d in (os.path.join(HERE, ".."), HERE):
        p = os.path.abspath(os.path.join(d, name))
        if os.path.exists(p):
            return p
    return None


LISTENER_VERSION = r'^VERSION = "([^"]+)"'
SERVER_VERSION = r"MCP server \(v([0-9.]+)\)"


def version_of(path, pattern):
    try:
        m = re.search(pattern, open(path, encoding="utf-8", errors="replace").read(), re.M)
        return m.group(1) if m else "?"
    except OSError:
        return "?"


def report_files():
    """Say which listener and server get tested; warn (never fail) if the listener copy FontLab runs differs, or if a file
    with a PRE-RENAME name still exists (a stale copy could be started by habit)."""
    print("python          :", sys.version.split()[0])
    listener, server = locate(LISTENER_FILE), locate(SERVER_FILE)
    for label, path, pattern in (("listener", listener, LISTENER_VERSION), ("server  ", server, SERVER_VERSION)):
        print(f"testing {label}:", f"{path} (v{version_of(path, pattern)})" if path else "NOT FOUND (expected in the project folder)")
    project = os.path.abspath(os.path.join(HERE, ".."))
    scripts = os.environ.get(SCRIPTS_ENV) or os.path.join(os.path.expanduser("~"), "Documents", "FontLab", "FontLab 8", "Scripts")
    for folder in dict.fromkeys((project, HERE, scripts)):
        for old in OLD_FILES:
            if os.path.exists(os.path.join(folder, old)):
                print(f"WARNING: old-named file still present: {os.path.join(folder, old)} - delete it (the project now uses "
                      f"{LISTENER_FILE} and {SERVER_FILE}); a stale copy could be started by habit.")
    if not listener:
        return
    deployed = os.path.join(scripts, LISTENER_FILE)
    if not os.path.exists(deployed):
        print("NOTE   : no listener copy at", deployed, "- cannot tell whether FontLab runs the file that was tested")
        return
    same = open(listener, "rb").read().replace(b"\r\n", b"\n") == open(deployed, "rb").read().replace(b"\r\n", b"\n")
    if same:
        print("deployed listener copy is identical:", deployed)
    else:
        print(f"WARNING: the listener FontLab runs ({deployed}, v{version_of(deployed, LISTENER_VERSION)}) DIFFERS from the one "
              f"tested (v{version_of(listener, LISTENER_VERSION)}). Copy the tested file there and restart the listener.")


def run(script):
    # -B / PYTHONDONTWRITEBYTECODE: do not litter the project folder with __pycache__ when a harness imports the server
    # PYTHONUTF8 / PYTHONIOENCODING: the harnesses print non-ASCII text (e.g. e-acute); on a Windows console with another code page
    # (cp1254 on a Turkish system) the child would write that code page while we decode UTF-8, and a correct run would show as FAIL
    p = subprocess.run([sys.executable, "-B", os.path.join(HERE, script)], cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
    out = (p.stdout + p.stderr).replace("\r\n", "\n")
    # the listener prints a wall-clock "Connected at HH:MM:SS" line on its first request: not part of the result
    out = re.sub(r"Connected at \d{2}:\d{2}:\d{2}", "Connected at HH:MM:SS", out)
    return p.returncode, out


def main():
    update = "--update" in sys.argv
    report_files()
    project = os.path.abspath(os.path.join(HERE, ".."))
    missing = [name for name in (LISTENER_FILE, SERVER_FILE) if not locate(name)]
    if missing:
        for name in missing:
            print(f"ERROR  : {name} was not found in the project folder ({project}).")
        print("         The tests read BOTH scripts from the project folder (the parent of tests\\). The listener that FontLab runs")
        print("         lives in its Scripts folder: copy it into the project folder (next to the server file), then run again.")
        print("         Nothing was tested.")
        sys.exit(2)
    failed = False
    for script, expected_name in JOBS:
        code, out = run(script)
        path = os.path.join(HERE, expected_name)
        if update:
            # never save a crash or an empty output as the new expectation: it would make a broken harness "pass"
            if code != 0 or not out.strip() or "Traceback" in out:
                failed = True
                print("REFUSED to update", expected_name, f"(exit code {code}, {len(out.splitlines())} lines"
                      + (", contains a Traceback" if "Traceback" in out else "") + "): the harness is broken, nothing was written")
                continue
            open(path, "w", encoding="utf-8", newline="\n").write(out)
            print("updated", expected_name, f"({len(out.splitlines())} lines)")
            continue
        exp = open(path, encoding="utf-8").read().replace("\r\n", "\n")
        if code == 0 and out.strip() and out == exp and "Traceback" not in out:
            print("PASS ", script, f"({len(out.splitlines())} lines identical to {expected_name})")
        else:
            failed = True
            print("FAIL ", script, f"(exit code {code})" + ("" if out.strip() else " - the harness produced NO output, an empty harness never passes"))
            if code != 0:
                print("      the harness said:", " | ".join(out.strip().splitlines()[-3:])[:300])
            for line in list(difflib.unified_diff(exp.splitlines(), out.splitlines(), expected_name, "now", lineterm=""))[:60]:
                print("     ", line)
    sys.exit(1 if failed else 0)


main()
