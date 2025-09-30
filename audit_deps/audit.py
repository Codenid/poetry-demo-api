import os
import re

SRC_DIR = "src"
REQUIREMENTS_FILE = "requirements.txt"

def get_imports_from_source():
    imports = set()
    for root, _, files in os.walk(SRC_DIR):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), encoding="utf-8") as f:
                    for line in f:
                        match = re.match(r"^\s*(?:from|import)\s+([a-zA-Z0-9_\.]+)", line)
                        if match:
                            imports.add(match.group(1).split('.')[0])
    return imports

def get_requirements():
    with open(REQUIREMENTS_FILE, encoding="utf-8") as f:
        return {line.split("==")[0].strip().lower() for line in f if "==" in line}

def main():
    used = get_imports_from_source()
    declared = get_requirements()

    print("\n🔍 Dependencias declaradas en requirements.txt:")
    for dep in sorted(declared):
        status = "✅ usada" if dep in used else "⚠️ no detectada"
        print(f" - {dep}: {status}")

    unused = declared - used
    if unused:
        print("\n⚠️ Posibles dependencias innecesarias:")
        for dep in sorted(unused):
            print(f" - {dep}")

if __name__ == "__main__":
    main()