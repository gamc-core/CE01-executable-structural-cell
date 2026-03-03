#!/usr/bin/env python3

import sys
import os
import json
import uuid
import hashlib
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")

# ----------------------------
# UTILIDADES
# ----------------------------

def ensure_storage():
    os.makedirs(STORAGE_DIR, exist_ok=True)

def utc_now():
    return datetime.utcnow().isoformat()

def sha256_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def read_input(args):
    # Modo archivo
    if len(args) >= 3 and args[2] == "--file":
        if len(args) < 4:
            raise Exception("Missing file path after --file")
        file_path = args[3]
        if not os.path.exists(file_path):
            raise Exception("File not found.")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    # Modo texto directo
    if len(args) >= 3 and args[2] != "--file":
        return " ".join(args[2:])

    # Modo STDIN
    if not sys.stdin.isatty():
        return sys.stdin.read()

    raise Exception("No valid input provided.")

def list_cell_files():
    return [f for f in os.listdir(STORAGE_DIR) if f.endswith(".json")]

# ----------------------------
# LÓGICA CENTRAL
# ----------------------------

def create_cell(text):
    cell_id = str(uuid.uuid4())
    cell = {
        "id": cell_id,
        "timestamp": utc_now(),
        "raw_text": text,
        "length": len(text),
        "word_count": len(text.split()),
        "line_count": len(text.splitlines()),
        "hash": sha256_hash(text),
        "closed": True
    }

    file_path = os.path.join(STORAGE_DIR, f"{cell_id}.json")

    with open(file_path, "w") as f:
        json.dump(cell, f, indent=2)

    print("Cell created:")
    print(json.dumps(cell, indent=2))


def list_cells():
    files = list_cell_files()
    cells = []

    for filename in files:
        with open(os.path.join(STORAGE_DIR, filename), "r") as f:
            cells.append(json.load(f))

    print(json.dumps(cells, indent=2))


def status():
    files = list_cell_files()
    print("Total cells:", len(files))

def verify_cells():
    files = list_cell_files()
    corrupted = 0

    for filename in files:
        file_path = os.path.join(STORAGE_DIR, filename)

        with open(file_path, "r") as f:
            cell = json.load(f)

        recalculated_hash = sha256_hash(cell["raw_text"])

        if recalculated_hash != cell["hash"]:
            print(f"{filename}: CORRUPTED")
            corrupted += 1
        else:
            print(f"{filename}: VALID")

    print("\nTotal corrupted:", corrupted)


def freeze_check():
    # 1. Check storage exists
    if not os.path.exists(STORAGE_DIR):
        print("NOT_READY: storage directory missing.")
        return

    # 2. Check contract file exists
    contract_path = os.path.join(BASE_DIR, "CONTRACT.md")
    if not os.path.exists(contract_path):
        print("NOT_READY: CONTRACT.md missing.")
        return

    # 3. Check no corrupted cells
    files = list_cell_files()
    for filename in files:
        file_path = os.path.join(STORAGE_DIR, filename)
        with open(file_path, "r") as f:
            cell = json.load(f)
        recalculated_hash = sha256_hash(cell["raw_text"])
        if recalculated_hash != cell["hash"]:
            print(f"NOT_READY: corrupted cell detected ({filename})")
            return

    print("READY_TO_FREEZE")

# ----------------------------
# CLI
# ----------------------------

def main():
    ensure_storage()

    if len(sys.argv) < 2:
        print("Commands:")
        print("  create \"text\"")
        print("  list")
        print("  status")
        return

    cmd = sys.argv[1]

    if cmd == "create":
        try:
            text = read_input(sys.argv)
            if not text.strip():
                raise Exception("Empty input not allowed.")
            create_cell(text)
        except Exception as e:
            print("Error:", str(e))

    elif cmd == "list":
        list_cells()

    elif cmd == "status":
        status()

    elif cmd == "verify":
        verify_cells()

    elif cmd == "freeze_check":
        freeze_check()

    else:
        print("Unknown command.")

if __name__ == "__main__":
    main()