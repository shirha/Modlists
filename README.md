# Wabbajack Modlist Archive App

A Flask-based tool for indexing, analyzing, and browsing Wabbajack modlists using `.wabbajack.metadata` and `.json` files.

---

## Features

- Summary table of all modlist versions
- Archive-level detail view with search/filtering
- Automatic version matching between metadata and JSON
- Profile detection from local installs
- Game.exe version detection (Stock Game awareness)
- Nexus linking for mod archives
- Regex-based search across all views

---

## Core Rules

### 1. Metadata drives everything
- Every `.wabbajack.metadata` file becomes **one row**
- Each version is treated independently

### 2. Summary uses local version data
- MO2 version
- Game.exe version
- Profiles

### 3. Only the most current matched JSON is used

- JSON must exist in metadata
- Only the **highest shared version** is used
- Exactly **one JSON per modlist**

### 4. Multiple backups must include version
- Version must be preserved
- Prevents ambiguity

---

## Important Behavior

### Stock Game Detection

If:
- A profile exists  
- But **game.exe version is missing**

➡️ The modlist is **NOT using a Stock Game folder**

---

## How I Use This (Workflow)

### Step 1 — Download

Copy from Wabbajack:

    *.wabbajack
    *.wabbajack.metadata

To:

    O:\Wabbajack\4.1.0.0\downloaded_mod_lists

---

### Step 2 — Run read_meta.py

    python read_meta.py

Choose:

    m (move-metadata)

This will:
- Fetch GitHub status.json
- Save JSON
- Move all files to Archive

---

### Step 3 — Fix Version Mismatches

If versions don’t match:

    metadata: 3.2.5
    json:     3.2.4  ❌

Rename JSON:

    → 3.2.5.json

Otherwise it will be ignored.

---

### Step 4 — Archive Structure

Example:

    Ash_Lotus_AshLotus 1.2.3.json
    Ash_Lotus_AshLotus 1.2.3.wabbajack
    Ash_Lotus_AshLotus 1.2.3.wabbajack.metadata

---

### Step 5 — Run App

    python app3.py

Open:

    http://127.0.0.1:5000

---

### Step 6 — Interpret Results

Only matching versions are used.

Example:

    Alpyne 1.5.1 meta
    Alpyne 1.5.1 json
    Alpyne 1.6.1 json (ignored)

---

## UI Views

### Summary
- One row per metadata version

### Details
- Archive-level view

### Report
- Validation output from simple_report

---

## Routes

- `/` → main UI
- `/toggle_game` → switch game
- `/modlist/<name>` → details
- `/json/<name@version>` → metadata
- `/image/<name@version>` → banner

---

## Output Files

- `bkup_scan.json`
- `simple_report.txt`
- `/logs/*.log`

---

## Design Philosophy

- Metadata is the source of truth
- JSON must match metadata
- Deterministic behavior over convenience

---

## Future Improvements

- Caching
- Incremental updates
- Better filtering
