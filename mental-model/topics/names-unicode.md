# Glyph creation, names and Unicode

**A new glyph's layer (listener 0.127 / server 0.48, live 620–623):** in a font with one master, `create_glyph` also creates the glyph's layer and syncs it; the reply gives `layer_created` and `layer_name_source`. When it cannot, the glyph is still created and `layer_note` gives the reason (stub-tested only). Why: [FONTLAB-API-RULES.md](../FONTLAB-API-RULES.md) §9. Older text below that says a new glyph has no layer describes earlier versions.

> Moved from milestone summary v11 (§8) on 2026-11-01, edited only where the chat-era workflow or a personal path no longer applies. The original section numbers are kept, so older cross-references such as "section 8p" still resolve: [MARKDOWN-MAP.md](../MARKDOWN-MAP.md) lists which file holds each section. Snapshot: [archive/milestone-summary-v11.md](../archive/milestone-summary-v11.md).

## 8. Glyph creation, names and Unicode (live-verified, test font; listener 0.50 / 0.51, server v0.13 to v0.16; server v0.17 and v0.18 are stub-tested only). Sections 8b to 8h below cover the geometry work of v0.52 to v0.82

**FontLab assigns the codepoint by itself from the name:** `B` 66, `C` 67, `D` 68, `eacute` 233, `uni00E9` 233, `uni0043` 67, `u1F600` 128512, and even LOWERCASE hex: `uni00e8` 232,
`uni00e7` 231. Made-up and suffixed names (`zzcontrol`, `B.alt`, `A.alt`, `m-n_o.p`, `9lives`, `.hidden`) get none. The codepoint is already readable inside the same create call.

**FontLab SKIPS the automatic codepoint when another glyph already holds it** (five observations): `B` created after `B.alt` was given 66; `C` after `uni0043` (67); `eacute` after `uni00E9` (233);
and, in the two early runs, `uni00E9` after `eacute` (233). The new glyph is created with no Unicode. **Lesson:** those two early runs were first read as "FontLab does not map uniXXXX names"
(wrong: `eacute` held 233). A negative live result must be checked for confounders, and a claim recorded only after a controlled run (here: `uni00E9` created on a font where nothing held 233).

**Duplicates by hand:** `set_glyph_unicode` accepts a codepoint another glyph holds, silently; both then report it. The v0.50+ reply names the other holders (`also_held_by`, `duplicate_warning`).

**Clearing:** setting a codepoint to 0 clears it (FontLab then reads back none). Until listener 0.51 the tool compared the re-read `None` with 0 and reported a failure although the codepoint HAD been cleared.

**FontLab keeps ONLY `A-Z a-z 0-9 . _ -` in a glyph name and silently strips everything else it is given, then creates THAT glyph:** non-ASCII letters, spaces, and `# / * : + @ ! $ % & ( ) ~ =` were all
stripped (a name ending in a non-ASCII e lost it; `a b` became `ab`; `a#b/c*d:e` became `abcde`; a lone non-ASCII letter became an EMPTY name, a glyph that no tool can address or delete because names must
not be empty). Accepted unchanged: `m-n_o.p`, a leading digit, a leading period, names of 64 and 130 characters (these stay hints in `name_warnings`: no leading digit, no leading period except `.notdef`,
at most 63 characters). Not probed: quotes, backslash, `[ ] { } < > , ; ? ^ |` and the backtick (refused by the safe-set rule anyway).

**What the tools do with this:** the server refuses any name with a character outside the safe set BEFORE calling FontLab, with a message that names the characters, says what FontLab would have created and
gives advice that fits (accented letter -> `eacute` / `uni00E9`; spaces -> `_` or `-`; punctuation -> leave out). The listener check `created_under_other_names` stays as a safety net (live: the error then says
that FontLab DID create a glyph, under which name). When a single-character or `uniXXXX` / `uXXXX` name comes back unencoded, the listener scans for holders (the server passes `scan_unicode`) and the
instruction tells the agent to ask the person, not to set it. For a plain multi-character name that comes back unencoded (it may be an Adobe Glyph List name FontLab skipped, e.g. `eacute`) the instruction
warns about the skip rule. Lowercase-hex names get a hint (convention says UPPERCASE; FontLab maps them anyway; other tools may not).

**Not tested / open:** secondary codepoints (`glyph.unicodes`; the scan reads only the primary `glyph.unicode`); standard Adobe Glyph List names that FontLab does not map at all (the server cannot tell them
from non-standard names); the stripped-character set beyond the list above; an older listener with a newer server (decided: no practical benefit; the `compatibility_note` and the `unknown` /
`unavailable` replies are stub-tested only); the `scan_error` / unreadable-glyph paths (stub-tested only).
