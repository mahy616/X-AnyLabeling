import os
import glob
import sys
import subprocess
import shutil

def find_executable(name):
    """Finds an executable in the current Python environment or PATH."""
    exts = [".exe", ""] if sys.platform == "win32" else [""]
    for ext in exts:
        # Check Scripts (standard pip)
        path = os.path.join(sys.prefix, "Scripts", name + ext)
        if os.path.exists(path):
            return path
        # Check Library/bin (Conda)
        path = os.path.join(sys.prefix, "Library", "bin", name + ext)
        if os.path.exists(path):
            return path
            
    # Fallback for lrelease: check base Anaconda environment
    if name == "lrelease":
        # Try to deduce base path from current env path if it follows standard conda structure
        # e.g., .../anaconda3/envs/myenv -> .../anaconda3
        base_anaconda = os.path.abspath(os.path.join(sys.prefix, "..", ".."))
        path = os.path.join(base_anaconda, "Library", "bin", name + ext)
        if os.path.exists(path):
            return path
        
        # Hardcoded fallback based on user's system
        path = r"C:\ProgramData\anaconda3\Library\bin\lrelease.exe"
        if os.path.exists(path):
            return path

    return shutil.which(name)

def run_command(cmd, description):
    print(f"--- {description} ---")
    try:
        subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error: {description} failed. {e}")
        return False
    return True

# 1. Configuration
supported_languages = ["en_US", "zh_CN"]
translations_dir = "anylabeling/resources/translations"
# We use module for pylupdate to avoid broken wrappers
pylupdate_cmd = [sys.executable, "-m", "PyQt5.pylupdate_main"]
lrelease = find_executable("lrelease")

# 2. Compile UI files
print("Step 1: Compiling UI files...")
ui_files = glob.glob(os.path.join("anylabeling", "**", "*.ui"), recursive=True)
for ui_file in ui_files:
    py_file = os.path.splitext(ui_file)[0] + "_ui.py"
    # Using -m ensures we use the current environment's PyQt5
    cmd = [sys.executable, "-m", "PyQt5.uic.pyuic", "-x", ui_file, "-o", py_file]
    run_command(cmd, f"UI -> PY: {ui_file}")

# 3. Update Translation source files (.ts)
print("\nStep 2: Updating .ts files...")
# Use a .pro file to avoid "Command line too long" error on Windows
py_files = glob.glob(os.path.join("anylabeling", "**", "*.py"), recursive=True)
# Filter out generated files to avoid noise if desired, but usually okay
py_files = [f.replace("\\", "/") for f in py_files] # Normalize for Qt

pro_content = "SOURCES = \\\n    " + " \\\n    ".join(py_files) + "\n\n"
pro_content += "TRANSLATIONS = \\\n    " + " \\\n    ".join([f"{translations_dir}/{lang}.ts" for lang in supported_languages])

pro_file = "temp_project.pro"
with open(pro_file, "w", encoding="utf-8") as f:
    f.write(pro_content)

# Run pylupdate via python module
cmd = pylupdate_cmd + ["-noobsolete", pro_file]
if run_command(cmd, "Updating translations via .pro file"):
    if os.path.exists(pro_file):
        os.remove(pro_file)
else:
    print("Warning: pylupdate failed. Check if PyQt5 is installed correctly.")

# 4. Compile .ts to .qm
if lrelease:
    print("\nStep 3: Compiling .ts to .qm...")
    for lang in supported_languages:
        ts_path = os.path.join(translations_dir, f"{lang}.ts")
        if os.path.exists(ts_path):
            run_command([lrelease, ts_path], f"Compiling {lang}.ts")
else:
    print("\nWarning: lrelease not found. Skipping .qm compilation.")

# 5. Generate Resource file
print("\nStep 4: Generating resources.py...")
qrc_path = "anylabeling/resources/resources.qrc"
res_py_path = "anylabeling/resources/resources.py"
if os.path.exists(qrc_path):
    # Try module first
    cmd = [sys.executable, "-m", "PyQt5.pyrcc_main", "-o", res_py_path, qrc_path]
    run_command(cmd, "Compiling resources (module)")
else:
    print(f"Error: {qrc_path} not found.")

print("\nAll tasks completed.")
