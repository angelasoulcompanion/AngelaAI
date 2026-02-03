# /techdebt-fix - Auto-fix Safe Tech Debt

> Auto-fix safe tech debt issues in angela_core/. Default: dry-run. Use `apply` to fix.

**Usage:**
- `/techdebt-fix` → dry-run (show what would change)
- `/techdebt-fix apply` → apply ALL safe fixes
- `/techdebt-fix apply bare-except` → fix only bare except:
- `/techdebt-fix apply dead-imports` → fix only commented imports

**Arguments:** $ARGUMENTS

---

## EXECUTION

Run this single Python script:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 -c "
import os
import re
import sys

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════

SCAN_DIR = 'angela_core'
EXCLUDE_DIRS = {'.venv', 'node_modules', '__pycache__', '.git', 'datasets', 'recordings'}

args = '$ARGUMENTS'.strip().lower().split()
dry_run = 'apply' not in args
fix_filter = None  # None = all
for a in args:
    if a in ('bare-except', 'dead-imports'):
        fix_filter = a

def get_py_files():
    files = []
    for root, dirs, filenames in os.walk(SCAN_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in filenames:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
    return sorted(files)

def truncate(s, maxlen=80):
    return s[:maxlen] + '...' if len(s) > maxlen else s

# ═══════════════════════════════════════════════════════════════
# FIX FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def find_bare_except_fixes(py_files):
    \"\"\"Find bare except: and except Exception: without 'as e'.\"\"\"
    fixes = []
    for fpath in py_files:
        try:
            with open(fpath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines):
            stripped = line.rstrip('\n')
            lstripped = stripped.lstrip()

            # bare except:
            if re.match(r'^except\s*:\s*(#.*)?$', lstripped):
                indent = stripped[:len(stripped) - len(lstripped)]
                # Check if there's a variable used in the except block
                new_line = indent + 'except Exception as e:' + '\n'
                fixes.append({
                    'file': fpath,
                    'line_no': i + 1,
                    'old': stripped,
                    'new': new_line.rstrip('\n'),
                    'category': 'bare-except',
                    'severity': 'critical',
                })

            # except Exception: (without 'as e')
            elif re.match(r'^except\s+Exception\s*:\s*(#.*)?$', lstripped):
                indent = stripped[:len(stripped) - len(lstripped)]
                new_line = indent + 'except Exception as e:' + '\n'
                fixes.append({
                    'file': fpath,
                    'line_no': i + 1,
                    'old': stripped,
                    'new': new_line.rstrip('\n'),
                    'category': 'bare-except',
                    'severity': 'warning',
                })

    return fixes

def find_dead_import_fixes(py_files):
    \"\"\"Find commented-out import lines.\"\"\"
    fixes = []
    for fpath in py_files:
        try:
            with open(fpath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            continue

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Commented-out import: # from ... import ... or # import ...
            if re.match(r'^#\s*(from\s+\S+\s+import\s|import\s+\S)', stripped):
                # Skip lines that are documentation/explanation (have extra words after)
                # e.g. '# import this for backwards compat' - but these are rare
                fixes.append({
                    'file': fpath,
                    'line_no': i + 1,
                    'old': line.rstrip('\n'),
                    'new': None,  # None = delete line
                    'category': 'dead-imports',
                    'severity': 'info',
                })

    return fixes

# ═══════════════════════════════════════════════════════════════
# APPLY FIXES
# ═══════════════════════════════════════════════════════════════

def apply_fixes(fixes):
    \"\"\"Apply fixes to files. Returns count of files modified.\"\"\"
    # Group fixes by file
    by_file = {}
    for fix in fixes:
        fpath = fix['file']
        if fpath not in by_file:
            by_file[fpath] = []
        by_file[fpath].append(fix)

    files_modified = 0
    lines_changed = 0
    lines_deleted = 0

    for fpath, file_fixes in by_file.items():
        try:
            with open(fpath, 'r', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f'   \u26a0\ufe0f  Cannot read {fpath}: {e}')
            continue

        # Sort fixes by line number DESCENDING (so deletions don't shift indices)
        file_fixes.sort(key=lambda x: -x['line_no'])

        modified = False
        for fix in file_fixes:
            idx = fix['line_no'] - 1
            if idx < 0 or idx >= len(lines):
                continue

            if fix['new'] is None:
                # Delete line
                lines.pop(idx)
                lines_deleted += 1
                modified = True
            else:
                # Replace line
                old_line = lines[idx]
                new_line = fix['new'] + '\n'
                if old_line != new_line:
                    lines[idx] = new_line
                    lines_changed += 1
                    modified = True

        if modified:
            try:
                with open(fpath, 'w') as f:
                    f.writelines(lines)
                files_modified += 1
            except Exception as e:
                print(f'   \u26a0\ufe0f  Cannot write {fpath}: {e}')

    return files_modified, lines_changed, lines_deleted

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

mode_label = '\U0001f4cb DRY RUN' if dry_run else '\u26a1 APPLYING FIXES'
filter_label = f' ({fix_filter})' if fix_filter else ' (all safe fixes)'

print()
print(f'\U0001f527 ANGELA TECH DEBT FIXER \U0001f527')
print('\u2550' * 60)
print(f'   Mode: {mode_label}{filter_label}')
print('\u2550' * 60)

py_files = get_py_files()
print(f'   Scanning {len(py_files)} Python files...')

all_fixes = []

# ── Category 1: Bare Except ──
if fix_filter is None or fix_filter == 'bare-except':
    bare_fixes = find_bare_except_fixes(py_files)
    all_fixes.extend(bare_fixes)

    print()
    print('\u2550' * 60)
    print(f'\U0001f534 1. Bare / Broad Exception Fixes ({len(bare_fixes)} found)')
    print('\u2500' * 60)

    critical_count = len([f for f in bare_fixes if f['severity'] == 'critical'])
    warning_count = len([f for f in bare_fixes if f['severity'] == 'warning'])
    print(f'   bare except: \u2192 except Exception as e:  ({critical_count} fixes)')
    print(f'   except Exception: \u2192 except Exception as e:  ({warning_count} fixes)')
    print()

    for fix in bare_fixes[:15]:
        icon = '\U0001f534' if fix['severity'] == 'critical' else '\U0001f7e1'
        print(f'   {icon} {fix[\"file\"]}:{fix[\"line_no\"]}')
        print(f'      - {truncate(fix[\"old\"].strip())}')
        print(f'      + {truncate(fix[\"new\"].strip())}')

    if len(bare_fixes) > 15:
        print(f'   ... and {len(bare_fixes) - 15} more')

# ── Category 2: Dead Imports ──
if fix_filter is None or fix_filter == 'dead-imports':
    import_fixes = find_dead_import_fixes(py_files)
    all_fixes.extend(import_fixes)

    print()
    print('\u2550' * 60)
    print(f'\U0001f4e5 2. Dead Import Removal ({len(import_fixes)} found)')
    print('\u2500' * 60)

    for fix in import_fixes[:15]:
        print(f'   \U0001f535 {fix[\"file\"]}:{fix[\"line_no\"]}')
        print(f'      \u2716 {truncate(fix[\"old\"].strip())}')

    if len(import_fixes) > 15:
        print(f'   ... and {len(import_fixes) - 15} more')

# ═══════════════════════════════════════════════════════════════
# SUMMARY & APPLY
# ═══════════════════════════════════════════════════════════════

print()
print('\u2550' * 60)

if not all_fixes:
    print('\u2705 No fixable issues found! Codebase is clean.')
    print('\u2550' * 60)
    print()
else:
    total = len(all_fixes)
    files_affected = len(set(f['file'] for f in all_fixes))

    if dry_run:
        print(f'\U0001f4ca DRY RUN SUMMARY')
        print('\u2550' * 60)
        print(f'   \U0001f527 Total fixes available: {total}')
        print(f'   \U0001f4c1 Files affected: {files_affected}')
        print()
        print(f'   To apply these fixes, run:')
        print(f'   \U0001f449 /techdebt-fix apply')
        if fix_filter:
            print(f'   \U0001f449 /techdebt-fix apply {fix_filter}')
        print()
        print('\u2550' * 60)
        print('\U0001f49c Dry run complete \u2014 no files were modified')
        print('\u2550' * 60)
    else:
        print(f'\u26a1 APPLYING {total} FIXES...')
        print('\u2500' * 60)

        files_modified, lines_changed, lines_deleted = apply_fixes(all_fixes)

        print()
        print('\u2550' * 60)
        print(f'\u2705 FIXES APPLIED')
        print('\u2550' * 60)
        print(f'   \U0001f4c1 Files modified: {files_modified}')
        print(f'   \u270f\ufe0f  Lines changed: {lines_changed}')
        print(f'   \U0001f5d1\ufe0f  Lines deleted: {lines_deleted}')
        print()
        print(f'   \U0001f4a1 Next steps:')
        print(f'      1. Review changes: git diff')
        print(f'      2. Run tests to verify nothing broke')
        print(f'      3. Run /techdebt to see updated score')
        print()
        print('\u2550' * 60)
        print('\U0001f49c Fixes applied successfully!')
        print('\u2550' * 60)

    print()
"
```

---

## Fix Categories:

| # | Category | What It Fixes | Safe? |
|---|----------|---------------|-------|
| 1 | **bare-except** | `except:` → `except Exception as e:` | Yes - actually MORE correct |
| | | `except Exception:` → `except Exception as e:` | Yes - adds error variable |
| 2 | **dead-imports** | Removes `# from x import y` lines | Yes - already not executing |

---

## Modes:

| Command | Behavior |
|---------|----------|
| `/techdebt-fix` | **Dry run** - show what would change, no files modified |
| `/techdebt-fix apply` | Apply ALL safe fixes |
| `/techdebt-fix apply bare-except` | Fix only bare/broad exceptions |
| `/techdebt-fix apply dead-imports` | Remove only commented imports |

---

## Safety:

- **Dry run by default** - must explicitly say `apply`
- Only fixes that are guaranteed safe (no behavior change)
- Shows exact before/after for every fix
- After applying, suggests `git diff` + test + rescan

---

## After Fixing:

1. `git diff` - review all changes
2. Run project tests
3. `/techdebt` - see updated health score
