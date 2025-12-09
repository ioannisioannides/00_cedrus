import os


def is_binary(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return False
    except UnicodeDecodeError:
        return True
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return True


ignore_dirs = {
    ".git",
    "__pycache__",
    "node_modules",
    "venv",
    "env",
    ".venv",
    "htmlcov",
    "media",
    "staticfiles",
    "static",
}
ignore_files = {"db.sqlite3", ".DS_Store"}

for root, dirs, files in os.walk("."):
    # Modify dirs in-place to skip ignored directories
    dirs[:] = [d for d in dirs if d not in ignore_dirs]

    for file in files:
        if file in ignore_files:
            continue
        if file.endswith(".pyc"):
            continue

        file_path = os.path.join(root, file)
        if is_binary(file_path):
            print(f"Non-UTF-8 file found: {file_path}")
