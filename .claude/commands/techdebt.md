# /techdebt - Angela Tech Debt Scanner

> Scan AngelaAI codebase for technical debt, code smells, and areas needing improvement

---

## EXECUTION

Run this single Python script:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI && python3 -c "
import subprocess
import os
import re
from collections import defaultdict

SCAN_DIR = 'angela_core'
EXCLUDE_DIRS = {'.venv', 'node_modules', '__pycache__', '.git', 'datasets', 'recordings'}

# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def run_grep(pattern, file_glob='*.py', extra_args=None):
    \"\"\"Run grep and return list of (file, line_no, content) tuples.\"\"\"
    cmd = ['grep', '-rn', '--include=' + file_glob]
    for d in EXCLUDE_DIRS:
        cmd.extend(['--exclude-dir=' + d])
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend([pattern, SCAN_DIR])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        matches = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split(':', 2)
            if len(parts) >= 3:
                matches.append((parts[0], parts[1], parts[2].strip()))
        return matches
    except Exception:
        return []

def run_grep_count(pattern, file_glob='*.py'):
    \"\"\"Return count of grep matches.\"\"\"
    return len(run_grep(pattern, file_glob))

def get_py_files():
    \"\"\"Get all .py files under SCAN_DIR excluding unwanted dirs.\"\"\"
    files = []
    for root, dirs, filenames in os.walk(SCAN_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in filenames:
            if f.endswith('.py'):
                files.append(os.path.join(root, f))
    return files

def truncate(s, maxlen=80):
    return s[:maxlen] + '...' if len(s) > maxlen else s

# ═══════════════════════════════════════════════════════════════
# SCAN RESULTS
# ═══════════════════════════════════════════════════════════════

critical = 0
warning = 0
info = 0

print()
print('\U0001f527 ANGELA TECH DEBT SCANNER \U0001f527')
print('\u2550' * 60)

# ─────────────────────────────────────────────────────────────
# 1. TODO / FIXME / HACK / XXX
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f4cb 1. TODO / FIXME / HACK Comments')
print('\u2500' * 60)

todos = run_grep(r'#.*\bTODO\b', '*.py', ['-i'])
fixmes = run_grep(r'#.*\bFIXME\b', '*.py', ['-i'])
hacks = run_grep(r'#.*\bHACK\b', '*.py', ['-i'])
xxxs = run_grep(r'#.*\bXXX\b', '*.py', ['-i'])

all_markers = []
for items, tag in [(todos, 'TODO'), (fixmes, 'FIXME'), (hacks, 'HACK'), (xxxs, 'XXX')]:
    for f, ln, content in items:
        all_markers.append((tag, f, ln, content))

print(f'   TODO: {len(todos)} | FIXME: {len(fixmes)} | HACK: {len(hacks)} | XXX: {len(xxxs)}')
print(f'   Total: {len(all_markers)} markers')

# Show top items, prioritize FIXME/HACK first
priority_order = {'FIXME': 0, 'HACK': 1, 'XXX': 2, 'TODO': 3}
all_markers.sort(key=lambda x: priority_order.get(x[0], 99))

for tag, f, ln, content in all_markers[:10]:
    icon = '\U0001f534' if tag in ('FIXME', 'HACK') else '\U0001f535'
    print(f'   {icon} [{tag}] {f}:{ln}')
    print(f'      {truncate(content)}')

if len(all_markers) > 10:
    print(f'   ... and {len(all_markers) - 10} more')

critical += len(fixmes) + len(hacks)
info += len(todos) + len(xxxs)

# ─────────────────────────────────────────────────────────────
# 2. Deprecated Code
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\u26a0\ufe0f  2. Deprecated Code')
print('\u2500' * 60)

deprecated = run_grep(r'deprecated\|DEPRECATED', '*.py', ['-i'])
# Filter out false positives (like checking for deprecated in strings that aren't markers)
dep_filtered = [d for d in deprecated if any(kw in d[2].lower() for kw in ['deprecated', '# deprecated', 'is deprecated', 'was deprecated', '@deprecated'])]

print(f'   Found: {len(dep_filtered)} references')
for f, ln, content in dep_filtered[:10]:
    print(f'   \U0001f7e1 {f}:{ln}')
    print(f'      {truncate(content)}')

if len(dep_filtered) > 10:
    print(f'   ... and {len(dep_filtered) - 10} more')

warning += len(dep_filtered)

# ─────────────────────────────────────────────────────────────
# 3. Type Hint Compliance
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f3af 3. Type Hint Compliance')
print('\u2500' * 60)

# Find functions without return type hints
all_defs = run_grep(r'^\s*def \|^\s*async def ', '*.py')
defs_with_hints = run_grep(r'^\s*def .*->.*:\|^\s*async def .*->.*:', '*.py')

total_funcs = len(all_defs)
typed_funcs = len(defs_with_hints)
untyped_funcs = total_funcs - typed_funcs

if total_funcs > 0:
    compliance = typed_funcs / total_funcs * 100
    bar_filled = int(compliance / 5)
    bar = '\u2588' * bar_filled + '\u2591' * (20 - bar_filled)
    print(f'   [{bar}] {compliance:.1f}%')
    print(f'   Total functions: {total_funcs}')
    print(f'   With return type: {typed_funcs}')
    print(f'   Missing return type: {untyped_funcs}')

    # Show some untyped functions
    untyped = []
    typed_set = set()
    for f, ln, content in defs_with_hints:
        typed_set.add((f, ln))
    for f, ln, content in all_defs:
        if (f, ln) not in typed_set:
            # Skip __init__ and simple dunder methods
            func_name = content.strip()
            if '__init__' not in func_name and '__str__' not in func_name and '__repr__' not in func_name:
                untyped.append((f, ln, content))

    if untyped:
        print(f'\\n   Top untyped functions:')
        for f, ln, content in untyped[:8]:
            print(f'   \U0001f535 {f}:{ln}')
            print(f'      {truncate(content.strip())}')
        if len(untyped) > 8:
            print(f'   ... and {len(untyped) - 8} more')

    if compliance < 50:
        critical += 1
    elif compliance < 80:
        warning += 1
    else:
        info += 1
else:
    print('   No functions found')

# ─────────────────────────────────────────────────────────────
# 4. Generic Typing (Dict[str, Any], List[Any])
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f4e6 4. Generic / Lazy Typing')
print('\u2500' * 60)

any_dict = run_grep(r'Dict\[str,\s*Any\]', '*.py')
any_list = run_grep(r'List\[Any\]', '*.py')
bare_dict = run_grep(r':\s*dict\s*[,=)\n]', '*.py')
bare_list = run_grep(r':\s*list\s*[,=)\n]', '*.py')

print(f'   Dict[str, Any]: {len(any_dict)}')
print(f'   List[Any]: {len(any_list)}')
print(f'   Bare dict: {len(bare_dict)}')
print(f'   Bare list: {len(bare_list)}')
total_generic = len(any_dict) + len(any_list) + len(bare_dict) + len(bare_list)
print(f'   Total lazy types: {total_generic}')

for items, tag in [(any_dict, 'Dict[str,Any]'), (any_list, 'List[Any]')]:
    for f, ln, content in items[:3]:
        print(f'   \U0001f535 [{tag}] {f}:{ln}')
if total_generic > 6:
    print(f'   ... showing top matches only')

info += total_generic

# ─────────────────────────────────────────────────────────────
# 5. Large Files (>500 lines)
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f4c4 5. Large Files (>500 lines)')
print('\u2500' * 60)

py_files = get_py_files()
large_files = []
for fpath in py_files:
    try:
        with open(fpath, 'r', errors='ignore') as fobj:
            line_count = sum(1 for _ in fobj)
        if line_count > 500:
            large_files.append((fpath, line_count))
    except Exception:
        pass

large_files.sort(key=lambda x: -x[1])
print(f'   Found: {len(large_files)} files over 500 lines')
for fpath, lines in large_files[:10]:
    icon = '\U0001f534' if lines > 1000 else '\U0001f7e1' if lines > 700 else '\U0001f535'
    print(f'   {icon} {fpath}: {lines:,} lines')

if len(large_files) > 10:
    print(f'   ... and {len(large_files) - 10} more')

critical += len([f for f in large_files if f[1] > 1000])
warning += len([f for f in large_files if 500 < f[1] <= 1000])

# ─────────────────────────────────────────────────────────────
# 6. Broad Exception Handling
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\u26a1 6. Broad Exception Handling')
print('\u2500' * 60)

broad_except = run_grep(r'except\s\+Exception\s*:', '*.py')
bare_except = run_grep(r'except\s*:', '*.py')

print(f'   except Exception: {len(broad_except)}')
print(f'   bare except: {len(bare_except)}')
print(f'   Total broad catches: {len(broad_except) + len(bare_except)}')

for f, ln, content in (bare_except + broad_except)[:8]:
    icon = '\U0001f534' if 'except:' == content.strip() or 'except :' == content.strip() else '\U0001f7e1'
    print(f'   {icon} {f}:{ln}')
    print(f'      {truncate(content.strip())}')

if len(broad_except) + len(bare_except) > 8:
    print(f'   ... and {len(broad_except) + len(bare_except) - 8} more')

critical += len(bare_except)
warning += len(broad_except)

# ─────────────────────────────────────────────────────────────
# 7. SQL Safety (UPDATE/DELETE without WHERE)
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f6e1\ufe0f  7. SQL Safety Check')
print('\u2500' * 60)

# Look for actual SQL UPDATE/DELETE statements (in strings, not comments)
updates = run_grep(r'UPDATE\s\+\w', '*.py', ['-i'])
deletes = run_grep(r'DELETE\s\+FROM', '*.py', ['-i'])

unsafe_updates = []
unsafe_deletes = []

# Filter: only flag lines that look like actual SQL (contain quotes or triple-quotes)
# Skip: comments, ON CONFLICT DO UPDATE, variable names, print/log messages
skip_patterns = ['on conflict', 'do update', '# ', 'print(', 'log', 'warning:', 'failed to update', 'update task', 'update project', 'update_', '.update(']

for f, ln, content in updates:
    upper = content.upper()
    lower = content.lower()
    if 'WHERE' not in upper and 'UPDATE' in upper:
        # Skip non-SQL lines
        if any(skip in lower for skip in skip_patterns):
            continue
        # Must look like SQL (contains quote or starts SQL-like)
        if any(c in content for c in [\"'\", '\"', 'UPDATE ', 'update ']):
            stripped = content.strip().lstrip(\"'\").lstrip('\"').strip()
            if stripped.upper().startswith('UPDATE'):
                unsafe_updates.append((f, ln, content))

for f, ln, content in deletes:
    upper = content.upper()
    lower = content.lower()
    if 'WHERE' not in upper and 'DELETE' in upper:
        if any(skip in lower for skip in skip_patterns):
            continue
        if any(c in content for c in [\"'\", '\"', 'DELETE ', 'delete ']):
            stripped = content.strip().lstrip(\"'\").lstrip('\"').strip()
            if stripped.upper().startswith('DELETE'):
                unsafe_deletes.append((f, ln, content))

print(f'   Total UPDATE statements: {len(updates)}')
print(f'   Total DELETE statements: {len(deletes)}')
print(f'   Potentially unsafe UPDATE (no WHERE on same line): {len(unsafe_updates)}')
print(f'   Potentially unsafe DELETE (no WHERE on same line): {len(unsafe_deletes)}')

for f, ln, content in (unsafe_updates + unsafe_deletes)[:8]:
    print(f'   \U0001f7e1 {f}:{ln}')
    print(f'      {truncate(content.strip())}')

if len(unsafe_updates) + len(unsafe_deletes) > 8:
    print(f'   ... and {len(unsafe_updates) + len(unsafe_deletes) - 8} more')

print()
print('   \u2139\ufe0f  Note: Multi-line SQL may have WHERE on the next line.')
print('      Review flagged items manually.')

warning += len(unsafe_updates) + len(unsafe_deletes)

# ─────────────────────────────────────────────────────────────
# 8. Dead / Legacy Imports
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f4e5 8. Dead / Legacy Imports')
print('\u2500' * 60)

# Check for imports from backup/old/deprecated paths
legacy_patterns = [
    ('_backup', 'backup modules'),
    ('_old', 'old modules'),
    ('_deprecated', 'deprecated modules'),
    ('_legacy', 'legacy modules'),
]

legacy_imports = []
for pattern, label in legacy_patterns:
    matches = run_grep(r'from.*' + pattern + r'\|import.*' + pattern, '*.py')
    for f, ln, content in matches:
        legacy_imports.append((label, f, ln, content))

# Check for commented-out imports
commented_imports = run_grep(r'^\s*#\s*from \|^\s*#\s*import ', '*.py')

print(f'   Legacy/backup imports: {len(legacy_imports)}')
print(f'   Commented-out imports: {len(commented_imports)}')

for label, f, ln, content in legacy_imports[:5]:
    print(f'   \U0001f534 [{label}] {f}:{ln}')
    print(f'      {truncate(content.strip())}')

for f, ln, content in commented_imports[:5]:
    print(f'   \U0001f535 [commented] {f}:{ln}')
    print(f'      {truncate(content.strip())}')

total_dead = len(legacy_imports) + len(commented_imports)
if total_dead > 10:
    print(f'   ... and {total_dead - 10} more')

warning += len(legacy_imports)
info += len(commented_imports)

# ─────────────────────────────────────────────────────────────
# 9. DRY Violations (Duplicate Code)
# ─────────────────────────────────────────────────────────────
print()
print('\u2550' * 60)
print('\U0001f503 9. DRY Violations (Don\\'t Repeat Yourself)')
print('\u2500' * 60)

# 9a. Duplicate function names across files
func_locations = defaultdict(list)
for f, ln, content in all_defs:
    match = re.search(r'(?:async\s+)?def\s+(\w+)\s*\(', content)
    if match:
        fname = match.group(1)
        # Skip dunder, test, and trivial names
        if not fname.startswith('_') and fname not in ('setup', 'main', 'run', 'get', 'post', 'put', 'delete', 'create', 'update', 'start', 'stop', 'close', 'connect', 'disconnect', 'init', 'reset', 'load', 'save', 'process', 'handle', 'execute', 'validate', 'parse', 'format', 'render', 'build', 'check', 'test'):
            func_locations[fname].append((f, ln))

dup_funcs = {name: locs for name, locs in func_locations.items() if len(locs) >= 3}
dup_funcs_sorted = sorted(dup_funcs.items(), key=lambda x: -len(x[1]))

print(f'   Functions defined in 3+ files: {len(dup_funcs)}')
dry_total = 0

for fname, locs in dup_funcs_sorted[:8]:
    unique_files = set(f for f, _ in locs)
    count = len(unique_files)
    print(f'   \U0001f7e1 {fname}() \u2192 {count} files')
    for f, ln in locs[:3]:
        print(f'      {f}:{ln}')
    if len(locs) > 3:
        print(f'      ... and {len(locs) - 3} more')
    dry_total += count

if len(dup_funcs_sorted) > 8:
    print(f'   ... and {len(dup_funcs_sorted) - 8} more duplicate names')

# 9b. Repeated SQL patterns (same query template in multiple files)
sql_selects = run_grep(r'SELECT.*FROM\s\+\w', '*.py', ['-i'])
sql_patterns = defaultdict(list)
for f, ln, content in sql_selects:
    # Normalize: extract table name from SELECT...FROM <table>
    match = re.search(r'FROM\s+(\w+)', content, re.IGNORECASE)
    if match:
        table = match.group(1).lower()
        # Build a rough pattern: SELECT...FROM table (ignoring specifics)
        sql_patterns[table].append((f, ln, content))

dup_sql_tables = {t: locs for t, locs in sql_patterns.items() if len(locs) >= 5}
dup_sql_sorted = sorted(dup_sql_tables.items(), key=lambda x: -len(x[1]))

print()
print(f'   Tables queried from 5+ locations:')
for table, locs in dup_sql_sorted[:8]:
    unique_files = len(set(f for f, _, _ in locs))
    print(f'   \U0001f535 {table}: {len(locs)} queries across {unique_files} files')
    dry_total += len(locs) - 1  # excess queries beyond 1

if not dup_sql_sorted:
    print(f'   \u2705 No heavily repeated SQL patterns')

# 9c. Near-duplicate files (same prefix, similar size)
from itertools import groupby
file_basenames = defaultdict(list)
for fpath in py_files:
    basename = os.path.basename(fpath).replace('.py', '')
    # Group by meaningful prefix (first 2 words separated by _)
    parts = basename.split('_')
    if len(parts) >= 2 and not basename.startswith('__'):
        prefix = '_'.join(parts[:2])
        try:
            with open(fpath, 'r', errors='ignore') as fobj:
                lc = sum(1 for _ in fobj)
            file_basenames[prefix].append((fpath, lc))
        except Exception:
            pass

# Find prefixes with many files (potential consolidation candidates)
file_clusters = {p: fs for p, fs in file_basenames.items() if len(fs) >= 3}
file_clusters_sorted = sorted(file_clusters.items(), key=lambda x: -len(x[1]))

print()
print(f'   File clusters (same prefix, 3+ files):')
cluster_count = 0
for prefix, files in file_clusters_sorted[:6]:
    total_lines = sum(lc for _, lc in files)
    print(f'   \U0001f535 {prefix}_*.py: {len(files)} files, {total_lines:,} total lines')
    for fp, lc in sorted(files, key=lambda x: -x[1])[:3]:
        print(f'      {fp} ({lc} lines)')
    if len(files) > 3:
        print(f'      ... and {len(files) - 3} more')
    cluster_count += len(files)

if not file_clusters_sorted:
    print(f'   \u2705 No obvious file clusters')

if dry_total > 0:
    warning += min(dry_total, 50)  # Cap DRY warnings

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
total_issues = critical + warning + info

print()
print('\u2550' * 60)
print('\U0001f4ca TECH DEBT SUMMARY')
print('\u2550' * 60)
print(f'   \U0001f534 Critical: {critical}')
print(f'   \U0001f7e1 Warning:  {warning}')
print(f'   \U0001f535 Info:     {info}')
print(f'   \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500')
print(f'   Total:     {total_issues} issues')
print()

# Health score (weighted: critical=5, warning=2, info=0.5)
weighted = critical * 5 + warning * 2 + info * 0.5
# Scale: 0 weighted = 100, 500+ weighted = 20 (logarithmic feel)
import math
if total_issues == 0:
    score = 100
else:
    score = max(10, int(100 - 18 * math.log10(max(1, weighted))))

bar_filled = int(score / 5)
bar = '\u2588' * bar_filled + '\u2591' * (20 - bar_filled)
label = 'Excellent' if score >= 90 else 'Good' if score >= 70 else 'Needs Work' if score >= 50 else 'Critical'
print(f'   Code Health: [{bar}] {score}/100 ({label})')
print()

# Quick wins
print('\U0001f4a1 QUICK WINS:')
print('\u2500' * 60)
if len(fixmes) > 0:
    print(f'   1. Fix {len(fixmes)} FIXME comments (critical issues)')
if len(bare_except) > 0:
    print(f'   2. Replace {len(bare_except)} bare except: with specific exceptions')
if large_files and large_files[0][1] > 1000:
    print(f'   3. Split {large_files[0][0]} ({large_files[0][1]:,} lines)')
if total_funcs > 0 and compliance < 80:
    print(f'   4. Add return type hints ({compliance:.0f}% -> 80% target)')
if len(legacy_imports) > 0:
    print(f'   5. Remove {len(legacy_imports)} legacy/backup imports')
if dup_funcs_sorted:
    top_dup = dup_funcs_sorted[0]
    print(f'   6. DRY: Consolidate {top_dup[0]}() (defined in {len(top_dup[1])} places)')
if file_clusters_sorted:
    top_cluster = file_clusters_sorted[0]
    print(f'   7. DRY: Merge {top_cluster[0]}_*.py cluster ({len(top_cluster[1])} files)')
if not any([fixmes, bare_except, large_files, legacy_imports, dup_funcs_sorted]) and (total_funcs == 0 or compliance >= 80):
    print('   Codebase looks clean! Keep it up.')

print()
print('\u2550' * 60)
print('\U0001f49c Scanned: angela_core/ | \U0001f527 Tech Debt Scanner v1.1 (+DRY)')
print('\u2550' * 60)
print()
"
```

---

## What This Scans:

| # | Category | Severity | What It Finds |
|---|----------|----------|---------------|
| 1 | **TODO/FIXME/HACK** | FIXME/HACK=Critical, TODO=Info | Comment markers left in code |
| 2 | **Deprecated Code** | Warning | Functions/modules marked deprecated |
| 3 | **Type Hint Compliance** | Varies | Functions missing `->` return type |
| 4 | **Generic Typing** | Info | `Dict[str, Any]`, `List[Any]`, bare `dict`/`list` |
| 5 | **Large Files** | >1000=Critical, >500=Warning | Files that should be split |
| 6 | **Broad Exceptions** | bare=Critical, Exception=Warning | `except:` or `except Exception:` |
| 7 | **SQL Safety** | Warning | UPDATE/DELETE without WHERE on same line |
| 8 | **Dead Imports** | Legacy=Warning, Commented=Info | Imports from backup/old/deprecated modules |
| 9 | **DRY Violations** | Warning | Duplicate functions, repeated SQL, file clusters |

---

## Severity Levels:

| Level | Meaning |
|-------|---------|
| Critical | Should fix ASAP - potential bugs or violations |
| Warning | Should fix soon - code smells or risks |
| Info | Nice to fix - code quality improvements |

---

## Scope:

- Scans: `angela_core/` (main Python codebase)
- Excludes: `.venv/`, `node_modules/`, `__pycache__/`, `.git/`
- Uses: `grep` + `wc` (no extra dependencies)

---

## Health Score:

| Score | Label | Meaning |
|-------|-------|---------|
| 90-100 | Excellent | Minimal tech debt |
| 70-89 | Good | Some areas to improve |
| 50-69 | Needs Work | Significant tech debt |
| 0-49 | Critical | Urgent cleanup needed |
