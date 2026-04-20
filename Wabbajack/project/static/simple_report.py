from packaging.version import Version

def run(parms, db, meta_store, token, rename_modlist):
    report = []
    
    # 1. Backups
    for game in parms:
        version_data = db[game].get('version_data', {})
        for base_path, versions in version_data.items():
            for version in versions:
                report.append([base_path, version, " bkup"])

    # 2. Metadata
    for base_path, versions in meta_store.items():
        for version, data in versions.items():
            repo = data["repositoryName"]
            title = rename_modlist.get(data["title"], data["title"])
            report.append([title, version, f" meta {repo}"])

    # 3. JSON Tokens
    for base_path, versions in token.items():
        title = base_path 
        if base_path in meta_store:
            first_meta = next(iter(meta_store[base_path].values()), {})
            raw_title = first_meta.get("title", base_path)
            title = rename_modlist.get(raw_title, raw_title)
            
        for version in versions:
            report.append([title, str(version), "·json"])

    # Sorting logic using Version objects
    def sort_key(row):
        try:
            return (row[0], Version(row[1]), row[2])
        except Exception:
            return (row[0], Version("0"), row[2])

    sorted_report = sorted(report, key=sort_key)

    # Calculate dynamic column widths
    # We find the longest string in the titles and versions
    width_title = max((len(str(row[0])) for row in sorted_report), default=27)
    width_version = max((len(str(row[1])) for row in sorted_report), default=7)
    # print("width_title =",width_title,"width_version =",width_version)

    output_lines = []
    save_title = None
    
    # Use dynamic widths in the f-string format
    for entry in sorted_report:
        title, version, row_type = entry
        
        if save_title != title:
            save_title = title
            output_lines.append("")
        
        clean_type = row_type.replace("·", " ")
        # Alignment: {title: <width} pads with spaces to the right
        output_lines.append(f"{title:<{width_title}} {version:<{width_version}} {clean_type}")

    return "\n".join(output_lines)
