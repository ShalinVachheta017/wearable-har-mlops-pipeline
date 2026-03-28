#!/usr/bin/env python3
"""Clean up code violations: F541 (f-string), W293 (blank line whitespace), and more."""

import subprocess
import re
from pathlib import Path

def fix_fstrings_and_whitespace():
    """Fix f-strings without placeholders and blank line whitespace."""
    
    py_files = list(Path("src").rglob("*.py"))
    total_fixed = 0
    
    for py_file in py_files:
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except:
            continue
        
        modified = False
        
        for i, line in enumerate(lines):
            # Fix W293: blank lines with whitespace -> remove it completely
            if line.strip() == "" and len(line) > 1:
                lines[i] = "\n"
                modified = True
            
            # Fix F541: f-strings without variables -> convert to regular string
            # Pattern: f"..." or f'...' with no {variables}
            match = re.search(r"f(['\"])([^'\"]*)\1", line)
            if match and "{" not in match.group(2):  # No variables inside
                quote = match.group(1)
                content = match.group(2)
                # Replace f"..." with "..."
                lines[i] = line.replace(match.group(0), f"{quote}{content}{quote}")
                modified = True
        
        if modified:
            with open(py_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"✓ Fixed {py_file}")
            total_fixed += 1
    
    return total_fixed

def main():
    print("🔧 Fixing f-strings and whitespace issues...\n")
    fixed = fix_fstrings_and_whitespace()
    print(f"\n✅ Fixed {fixed} files")

if __name__ == "__main__":
    main()
