import json
import tempfile
from pathlib import Path
from scanner import (
    load_csv_packages_from_text,
    check_packages,
    load_package_lock,
)


def test_csv_parser():
    csv_text = "package,version\nreact,18.2.0\nexpress,4.18.2\n"
    pkgs = load_csv_packages_from_text(csv_text)
    assert pkgs == [("react", "18.2.0"), ("express", "4.18.2")]


def test_check_packages_hit():
    packages = [("react", "18.2.0")]
    lock = {"react": "18.2.0"}
    result = check_packages(packages, lock)
    assert result == [("react", "18.2.0", "18.2.0")]


def test_check_packages_miss():
    packages = [("react", "18.2.0")]
    lock = {"lodash": "4.17.21"}
    result = check_packages(packages, lock)
    assert result == [("react", None, "18.2.0")]


def test_package_lock_parser():
    data = {
        "dependencies": {
            "react": {"version": "18.2.0"},
            "nested": {
                "version": "1.0.0",
                "dependencies": {
                    "express": {"version": "4.18.2"}
                }
            },
        }
    }

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "package-lock.json"
        p.write_text(json.dumps(data), encoding="utf-8")

        result = load_package_lock(p)

    assert result == {"react": "18.2.0", "nested": "1.0.0", "express": "4.18.2"}