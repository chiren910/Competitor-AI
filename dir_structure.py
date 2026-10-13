import os

# List of directory names to ignore
IGNORE_DIRS = {'__pycache__', 'venv', '.git', '.idea', '.mypy_cache', '.pytest_cache', '.vscode', '.env'}

def print_directory_structure(start_path, indent=""):
    try:
        entries = sorted(os.listdir(start_path))
    except PermissionError:
        return

    for entry in entries:
        full_path = os.path.join(start_path, entry)
        if os.path.isdir(full_path):
            if entry in IGNORE_DIRS:
                continue
            print(f"{indent}📁 {entry}")
            print_directory_structure(full_path, indent + "    ")
        else:
            print(f"{indent}📄 {entry}")

if __name__ == "__main__":
    # Replace '.' with any path you want to start from
    root_path = '.'  
    print(f"Directory structure of: {os.path.abspath(root_path)}\n")
    print_directory_structure(root_path)
