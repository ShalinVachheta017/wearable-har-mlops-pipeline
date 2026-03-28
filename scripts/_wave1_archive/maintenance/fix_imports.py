#!/usr/bin/env python3
"""Remove unused imports from Python files using flake8 analysis."""

import re
import subprocess
import sys
from pathlib import Path

def get_flake8_errors():
    """Get all F401 (unused import) errors from flake8."""
    result = subprocess.run(
        ["flake8", "src/", "--select=F401"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    return result.stdout

def parse_flake8_output(output):
    """Parse flake8 output into a dict of {file: [(line_num, import_name), ...]}."""
    errors = {}
    pattern = r"^([^:]+):(\d+):\d+: F401 '([^']+)' imported but unused"
    
    for line in output.split("\n"):
        if not line.strip():
            continue
        match = re.match(pattern, line)
        if match:
            file_path, line_num, import_name = match.groups()
            line_num = int(line_num)
            if file_path not in errors:
                errors[file_path] = []
            errors[file_path].append((line_num, import_name))
    
    return errors

def remove_import_from_line(line, import_name):
    """Remove a specific import from an import statement."""
    # Handle 'from X import Y' style
    from_match = re.match(r"^(\s*from\s+[\w.]+\s+import\s+)(.*)", line)
    if from_match:
        prefix = from_match.group(1)
        imports = from_match.group(2)
        # Split by comma and filter out the unwanted import
        import_list = [i.strip() for i in imports.split(",")]
        # Extract just the name (handles 'as' aliases)
        import_names = []
        for imp in import_list:
            name = imp.split()[0]  # Get the part before 'as'
            if name != import_name.split()[0]:
                import_names.append(imp)
        
        if import_names:
            return prefix + ", ".join(import_names) + "\n"
        else:
            return ""  # Remove entire line if no imports left
    
    # Handle 'import X' style
    import_match = re.match(r"^(\s*import\s+)(.*)", line)
    if import_match:
        prefix = import_match.group(1)
        imports = import_match.group(2)
        import_list = [i.strip() for i in imports.split(",")]
        import_names = [i for i in import_list if i.split()[0] != import_name.split()[0]]
        
        if import_names:
            return prefix + ", ".join(import_names) + "\n"
        else:
            return ""
    
    return line

def fix_file(file_path, errors):
    """Remove unused imports from a file."""
    if not Path(file_path).exists():
        print(f"  ⚠️  File not found: {file_path}")
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    modified = False
    for line_num, import_name in sorted(errors, reverse=True):  # Process in reverse order
        line_idx = line_num - 1  # Convert to 0-indexed
        if line_idx < len(lines):
            original = lines[line_idx]
            modified_line = remove_import_from_line(original, import_name)
            if modified_line != original:
                if modified_line.strip():  # Keep the line if there are still imports
                    lines[line_idx] = modified_line
                else:  # Remove the line entirely
                    lines.pop(line_idx)
                modified = True
                print(f"  ✓ Removed '{import_name}' from line {line_num}")
    
    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return True
    return False

def main():
    print("🔍 Scanning for unused imports...")
    output = get_flake8_errors()
    errors = parse_flake8_output(output)
    
    if not errors:
        print("✅ No unused imports found!")
        return 0
    
    print(f"Found {sum(len(e) for e in errors.values())} unused imports in {len(errors)} files\n")
    
    total_fixed = 0
    for file_path in sorted(errors.keys()):
        print(f"📝 {file_path}")
        fixed = fix_file(file_path, errors[file_path])
        if fixed:
            total_fixed += 1
    
    print(f"\n✅ Fixed {total_fixed} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
