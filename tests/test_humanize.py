#!/usr/bin/env python3
"""End-to-end tests for the zero-dependency humanize package."""

import json
import os
import re
import subprocess
import sys
import tempfile


NIFT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "nift")
PACKAGE = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.dirname(os.path.abspath(__file__))
WORK_DIRECTORY = tempfile.TemporaryDirectory(prefix=".humanize-test-", dir=ROOT)
WORK = WORK_DIRECTORY.name
SOURCE = os.path.join(PACKAGE, "src", "humanize.f")


def run(script, cwd):
    path = os.path.join(cwd, "case.f")
    with open(path, "w", encoding="ascii") as output:
        output.write(script)
    return subprocess.run([NIFT, "case.f"], cwd=cwd, capture_output=True, text=True, timeout=20)


def expect_success(label, result, expected):
    actual = result.stdout.strip().splitlines()
    if result.returncode != 0 or actual != expected:
        raise AssertionError(
            f"{label}: rc={result.returncode} expected={expected!r} actual={actual!r} stderr={result.stderr!r}"
        )


def main():
    with open(os.path.join(PACKAGE, "manifest.json"), encoding="ascii") as manifest_file:
        manifest = json.load(manifest_file)
    assert manifest == {
        "name": "humanize",
        "version": "0.1.0",
        "entry": "src/humanize.f",
        "description": "Deterministic English integer humanization",
    }

    with open(SOURCE, encoding="ascii") as source_file:
        source = source_file.read()
    public = re.findall(r"^    fn\(([A-Za-z_][A-Za-z0-9_]*)\(", source, re.MULTILINE)
    private = re.findall(r"^    private fn\(([A-Za-z_][A-Za-z0-9_]*)\(", source, re.MULTILINE)
    assert public == ["integer", "bytes", "plural", "ordinal"], public
    assert private == ["decimal", "parts", "group", "at_least_1024", "divide_1024", "increment"], private
    assert "\nstruct(humanize) {\n" in source and "@struct(humanize)" not in source

    direct_result = subprocess.run(
        [NIFT, "direct.f"], cwd=ROOT, capture_output=True, text=True, timeout=20
    )
    expect_success("direct source import", direct_result, ["1,234,567", "1.5 KiB", "2 people", "23rd"])

    external = os.path.join(WORK, "external")
    os.makedirs(os.path.join(external, ".nift"))

    matrix = '''@import("humanize")
print(humanize.integer(0))
print(humanize.integer(1234567890))
print(humanize.integer(-9223372036854775808))
print(humanize.bytes(0))
print(humanize.bytes(1023))
print(humanize.bytes(1024))
print(humanize.bytes(1536))
print(humanize.bytes(1075))
print(humanize.bytes(1076))
print(humanize.bytes(1048575))
print(humanize.bytes(1048576))
print(humanize.bytes(-1536))
print(humanize.bytes(-1076))
print(humanize.bytes(1101004))
print(humanize.bytes(1101005))
print(humanize.bytes(-1101004))
print(humanize.bytes(-1101005))
print(humanize.bytes(1127428915))
print(humanize.bytes(1127428916))
print(humanize.bytes(-1127428915))
print(humanize.bytes(-1127428916))
print(humanize.bytes(1154487209164))
print(humanize.bytes(1154487209165))
print(humanize.bytes(-1154487209164))
print(humanize.bytes(-1154487209165))
print(humanize.bytes(1182194902184755))
print(humanize.bytes(1182194902184756))
print(humanize.bytes(-1182194902184755))
print(humanize.bytes(-1182194902184756))
print(humanize.bytes(1210567579837189324))
print(humanize.bytes(1210567579837189325))
print(humanize.bytes(-1210567579837189324))
print(humanize.bytes(-1210567579837189325))
print(humanize.bytes(9223372036854775807))
print(humanize.bytes(-9223372036854775808))
print(humanize.plural(1, "item"))
print(humanize.plural(0, "item"))
print(humanize.plural(-1, "person", "people"))
print(humanize.plural(2000, "category", "categories"))
print(humanize.ordinal(1))
print(humanize.ordinal(2))
print(humanize.ordinal(3))
print(humanize.ordinal(4))
print(humanize.ordinal(11))
print(humanize.ordinal(12))
print(humanize.ordinal(13))
print(humanize.ordinal(21))
print(humanize.ordinal(-1))
print(humanize.ordinal(-2))
print(humanize.ordinal(-3))
print(humanize.ordinal(-11))
print(humanize.ordinal(-12))
print(humanize.ordinal(-13))
print(humanize.ordinal(-21))
print(humanize.ordinal(-23))
print(humanize.ordinal(-112))
print(humanize.ordinal(9223372036854775807))
'''
    expected = [
        "0", "1,234,567,890", "-9,223,372,036,854,775,808",
        "0 B", "1023 B", "1 KiB", "1.5 KiB", "1 KiB", "1.1 KiB", "1 MiB", "1 MiB",
        "-1.5 KiB", "-1.1 KiB",
        "1 MiB", "1.1 MiB", "-1 MiB", "-1.1 MiB",
        "1 GiB", "1.1 GiB", "-1 GiB", "-1.1 GiB",
        "1 TiB", "1.1 TiB", "-1 TiB", "-1.1 TiB",
        "1 PiB", "1.1 PiB", "-1 PiB", "-1.1 PiB",
        "1 EiB", "1.1 EiB", "-1 EiB", "-1.1 EiB",
        "8 EiB", "-8 EiB",
        "1 item", "0 items", "-1 people", "2,000 categories",
        "1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st",
        "-1st", "-2nd", "-3rd", "-11th", "-12th", "-13th", "-21st", "-23rd", "-112th",
        "9,223,372,036,854,775,807th",
    ]
    # A separate consumer validates package add and locked external import.
    subprocess.run([NIFT, "add", PACKAGE], cwd=external, check=True, capture_output=True, text=True)
    external_result = run(matrix, external)
    expect_success("external import", external_result, expected)
    repeat_result = run(matrix, external)
    expect_success("deterministic repeat", repeat_result, expected)
    assert external_result.stdout == repeat_result.stdout

    malformed = [
        'humanize.integer("12")', "humanize.integer(1.5)", "humanize.integer(null)",
        "humanize.integer([])", "humanize.bytes(true)", "humanize.bytes({})",
        'humanize.plural(1.5, "item")', "humanize.plural(1, 4)",
        'humanize.plural(2, "person", "people", "persons")', 'humanize.ordinal("3")',
        "humanize.integer()", "humanize.bytes(1, 2)", "humanize.ordinal()",
    ]
    for expression in malformed:
        result = run(f'@import("humanize")\nprint({expression})\n', external)
        assert result.returncode != 0, f"malformed value accepted: {expression}: {result.stdout!r}"

    for helper in private:
        result = run(f'@import("humanize")\nhumanize.{helper}(1)\n', external)
        assert result.returncode != 0 and f"private struct method: {helper}" in result.stderr, (
            helper, result.stdout, result.stderr
        )

    result = run('@import("humanize")\nmember := humanize.integer\nprint(member(1))\n', external)
    assert result.returncode != 0, "facade method unexpectedly extractable"

    print("PASS humanize direct import")
    print("PASS humanize package add/external import")
    print("PASS humanize boundaries and rounding")
    print("PASS humanize malformed input and privacy")
    print("PASS humanize deterministic repeat")


if __name__ == "__main__":
    try:
        main()
    finally:
        WORK_DIRECTORY.cleanup()
