import csv
import json
import sys
import re
import requests
from pathlib import Path
from io import StringIO


CSV_URL = "https://raw.githubusercontent.com/wiz-sec-public/wiz-research-iocs/main/reports/shai-hulud-2-packages.csv"


def download_csv(url: str) -> str:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.text


def load_csv_packages_from_text(csv_text: str):
    packages = []

    sample = csv_text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample)
    except csv.Error:
        dialect = csv.excel

    reader = csv.reader(StringIO(csv_text), dialect)
    header = next(reader, None)
    if header is None:
        return packages

    norm_header = [h.strip().lower() for h in header]

    def find_index(candidates, default=None):
        for cand in candidates:
            if cand in norm_header:
                return norm_header.index(cand)
        return default

    pkg_idx = find_index(["package", "package_name", "name", "pkg", "pkg_name"], default=0)
    ver_idx = find_index(["version", "pkg_version", "package_version", "ver"], default=None)

    if ver_idx is None and len(header) > 1:
        ver_idx = 1

    for row in reader:
        if not row:
            continue
        if row[0].lstrip().startswith("#"):
            continue

        max_idx = max(i for i in [pkg_idx, ver_idx] if i is not None)
        if len(row) <= max_idx:
            row = list(row) + [""] * (max_idx + 1 - len(row))

        pkg = row[pkg_idx].strip() if pkg_idx is not None else ""
        ver = row[ver_idx].strip() if ver_idx is not None else None

        if pkg:
            packages.append((pkg, ver if ver else None))

    return packages


def load_package_lock(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    deps = data.get("dependencies", {})
    result = {}

    def collect_deps(dep_dict):
        for name, info in dep_dict.items():
            version = info.get("version")
            if version:
                result[name] = version
            nested = info.get("dependencies")
            if isinstance(nested, dict):
                collect_deps(nested)

    collect_deps(deps)
    return result


def load_yarn_lock(file_path: Path):
    content = file_path.read_text(encoding="utf-8", errors="replace")
    entries = {}

    blocks = re.split(r"\n(?=\S)", content)

    for block in blocks:
        header_match = re.match(r'^([^\n:]+):', block)
        if not header_match:
            continue

        header = header_match.group(1)
        names = [n.strip().strip('"').strip("'") for n in header.split(",")]

        version_match = re.search(r'\n\s*version\s+"([^"]+)"', block)
        if not version_match:
            continue

        version = version_match.group(1)

        for pkg_entry in names:
            if pkg_entry.startswith("@"):
                at_pos = pkg_entry.rfind("@")
                if at_pos > 0:
                    clean_name = pkg_entry[:at_pos]
                else:
                    clean_name = pkg_entry
            else:
                clean_name = pkg_entry.split("@", 1)[0]

            entries[clean_name] = version

    return entries


def check_packages(packages, lock_data):
    results = []
    for pkg, expected_version in packages:
        found_version = lock_data.get(pkg)
        if found_version is None:
            results.append((pkg, None, expected_version))
        else:
            results.append((pkg, found_version, expected_version))
    return results


def main(lockfile_path: str):
    lock_file = Path(lockfile_path)

    csv_text = download_csv(CSV_URL)
    packages = load_csv_packages_from_text(csv_text)

    if lock_file.name == "package-lock.json":
        lock_data = load_package_lock(lock_file)
    elif lock_file.name == "yarn.lock":
        lock_data = load_yarn_lock(lock_file)
    else:
        print("Please provide a package-lock.json or yarn.lock file.")
        sys.exit(1)

    results = check_packages(packages, lock_data)

    found_anything = False

    for pkg, found, expected in results:
        if found is None:
            continue

        if expected and expected != found:
            print(f"{pkg}: match found, version mismatch (CSV: {expected}, Lockfile: {found})")
        else:
            print(f"{pkg}: match found (version: {found})")
            found_anything = True

    if not found_anything:
        print("No matches found in the lock file.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_packages.py <package-lock.json|yarn.lock>")
        sys.exit(1)

    main(sys.argv[1])
