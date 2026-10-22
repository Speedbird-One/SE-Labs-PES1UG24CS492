# Lab 5 – Static Code Analysis: Issues Table

File analysed: `gym_system.py`
Line numbers refer to the **original** file.

Baseline: Pylint 6.60/10 · Bandit 1 High · Flake8 10 findings.

## Bandit (security) – commit 1

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Shell command injection (B605, CWE-78, High/High) | Security | 36 | `os.system("rm -f " + prefix + "*.json")` builds a shell command from the `prefix` argument, so a crafted prefix (e.g. `x; rm -rf ~ #`) runs arbitrary commands. | Removed the shell entirely: `glob.glob(prefix + "*.json")` plus `os.remove(path)` for each match. Added `import glob`. |

## Pylint (code quality) – commit 2

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Mutable default arg (W0102) | Bug | 8 | `attendance_log=[]` is created once and shared across every call. | Default changed to `None`; a new list is created inside the function when `None`. |
| Bare except (W0702) | Bug / Style | 21 | `except:` swallows every error (including `KeyboardInterrupt`) and hides real bugs. | Catch only `(KeyError, ValueError)` (unknown class / member not on roster); function now returns `True`/`False`. |
| Resource not closed (R1732) | Bug | 32 | `f = open(...)` is never closed, so data may not be flushed to disk. | Use `with open(...) as handle`. |
| No file encoding (W1514) | Portability | 32 | `open()` without `encoding` depends on the platform default. | Added `encoding="utf-8"`. |
| Naming convention (C0103) | Style | 27 | `addMembers` is camelCase, not snake_case. | Renamed to `add_members` and updated both call sites in `main()`. |
| Old-style string formatting (C0209) | Style | 15 | `"%s -> %s" % (...)` could be an f-string. | Replaced with `f"{member_id} -> {class_name}"`. |
| Iterate dict with `.items()` (C0206) | Style | 39 | `for c in rosters` then `rosters[c]` does a needless lookup. | `for class_name, members in rosters.items()`. |
| Missing module docstring (C0114) | Docs | 1 | No module-level description. | Added a module docstring. |
| Missing function docstrings (C0116) | Docs | 8, 18, 24, 27, 31, 35, 38, 42 | Eight functions have no docstring. | Added a docstring to every function. |
| Off-by-one capacity check | Bug (logic) | 11 | `len(...) > capacity` lets one extra person in (Yoga capacity 3 accepted 4 members). Unknown classes (capacity 0) such as `Pilates` also accepted the first booking. | Changed to `>=`, and the roster is only created once a booking succeeds. |
| Negative capacity accepted | Bug (logic) | 24-25 | `set_capacity("Spin", -2)` silently made the class unbookable. | `set_capacity` rejects negative values, prints a message and returns `False`. |
| Duplicate bookings | Bug (logic) | 8-16 | The same member could be booked into a class twice. | `book_class` refuses a member already on the roster. |
| Guest IDs restart at 0 | Bug (logic) | 27-29 | Calling `addMembers` twice on one class would reuse `GUEST-0…`, colliding with the duplicate check. | `add_members` continues numbering after existing guests. |
| Unvalidated user input | Bug (robustness) | 52-53 | `int(n)` crashes with `ValueError` on non-numeric input. | `try/except ValueError`, falls back to 1 guest with a message. |
| Code runs on import | Design | 58 | `main()` was called at module level. | Wrapped in `if __name__ == "__main__":`. |

## Flake8 (style) – commit 3

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| E302 expected 2 blank lines | Style | 8, 18, 24, 27, 31, 35, 38, 42 | Top-level functions were separated by one blank line. | Two blank lines between all top-level definitions. |
| E305 expected 2 blank lines after function | Style | 58 | `main()` call directly after a function with one blank line. | Two blank lines before the `if __name__ == "__main__":` block. |
| E722 bare except | Bug / Style | 21 | Same finding as Pylint W0702. | Already fixed in commit 2 (typed exceptions). |

## Verification status

| Tool | Before | After |
|------|--------|-------|
| Bandit | 1 High (B605) | The vulnerable call is removed; **re-run to confirm** (Bandit could not be installed in my sandbox). |
| Pylint | 6.60/10 | **Re-run to confirm** the score is above 9.5 (Pylint could not be installed in my sandbox). Every reported message has been addressed. |
| Flake8 | 10 findings | 0 findings (verified, `reports/after/flake8_report.txt` is empty). |

## Reflection prompts (short notes)

- **Which issues were easiest to fix?** Flake8 blank-line errors and the Pylint docstring and f-string messages: they are mechanical.
- **Which false positives did I see?** None. Every message pointed at something worth changing, although missing docstrings are a documentation preference rather than a bug.
- **How would I integrate this into a workflow?** Run all three tools in CI (or a pre-commit hook) and fail the build on any Bandit finding, a Pylint score under 9.5 or any Flake8 error.
- **Tangible improvements?** The shell-injection hole is closed, the shared-list bug is gone, files are closed properly, and the capacity logic now behaves as the demo intends.
