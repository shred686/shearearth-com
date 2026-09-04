#!/usr/bin/env python3
"""Validate the generated Divi layouts before they go anywhere near WordPress.

Checks that every layout's shortcode nests correctly, that every {{token}} the
layouts use has a handler in the importer plugin, and that every image the
layouts reference is actually bundled with the plugin.
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "wordpress/plugin/spe-site-importer")
LAYOUTS = sorted(glob.glob(os.path.join(PLUGIN, "layouts/*.txt")))


def check_nesting(problems):
    for path in LAYOUTS:
        content = open(path).read()
        stack = []
        for m in re.finditer(r"\[(/?)(et_pb_[a-z_]+)", content):
            closing, tag = m.group(1), m.group(2)
            if not closing:
                stack.append(tag)
            elif not stack or stack[-1] != tag:
                problems.append(f"{path}: unexpected [/{tag}] (open: {stack[-3:]})")
                break
            else:
                stack.pop()
        if stack:
            problems.append(f"{path}: never closed: {stack}")
        modules = len(re.findall(r"\[et_pb_", content))
        print(f"  {os.path.basename(path):14} {modules:3} module tags")


def layout_tokens():
    used = set()
    for path in LAYOUTS:
        used |= set(re.findall(r"\{\{([A-Z]+)", open(path).read()))
    return used


def check_tokens(problems):
    php = open(os.path.join(PLUGIN, "spe-site-importer.php")).read()
    # The plugin resolves tokens either as plain strings ('{{HOME}}') or as
    # escaped regex literals ('/\{\{URL:([^}]+)\}\}/').
    handled = set(re.findall(r"\\?\{\\?\{([A-Z]+)", php))
    missing = layout_tokens() - handled
    if missing:
        problems.append(f"importer has no handler for: {sorted(missing)}")
    print(f"  tokens: {len(layout_tokens())} used, all handled" if not missing
          else f"  tokens: missing {sorted(missing)}")


def check_media(problems):
    bundled = set(os.listdir(os.path.join(PLUGIN, "media")))
    referenced = set()
    for path in LAYOUTS:
        referenced |= set(re.findall(r"\{\{(?:URL|ID):([^}]+)\}\}", open(path).read()))

    php = open(os.path.join(PLUGIN, "spe-site-importer.php")).read()
    declared = set(re.findall(r"'([a-z-]+\.(?:jpg|png|mp4))'\s*=>", php))

    if referenced - bundled:
        problems.append(f"layouts reference missing images: {sorted(referenced - bundled)}")
    if declared - bundled:
        problems.append(f"importer declares missing images: {sorted(declared - bundled)}")
    if referenced - declared:
        problems.append(f"images used but never uploaded: {sorted(referenced - declared)}")
    print(f"  media: {len(referenced)} referenced, {len(bundled)} bundled")


def check_exports(problems):
    for path in sorted(glob.glob(os.path.join(ROOT, "wordpress/divi/**/*.json"), recursive=True)):
        try:
            data = json.load(open(path))
        except json.JSONDecodeError as exc:
            problems.append(f"{path}: invalid JSON — {exc}")
            continue
        if data.get("context") not in ("et_builder", "et_builder_layouts"):
            problems.append(f"{path}: unexpected context {data.get('context')!r}")
        if not data.get("data"):
            problems.append(f"{path}: empty data")
        leftover = set()
        for value in data["data"].values():
            body = value if isinstance(value, str) else value.get("post_content", "")
            leftover |= set(re.findall(r"\{\{[^}]+\}\}", body))
        if leftover:
            problems.append(f"{path}: unresolved tokens {sorted(leftover)}")
        print(f"  {os.path.relpath(path, ROOT):48} {data['context']} ({len(data['data'])})")


def main():
    problems = []
    print("shortcode nesting")
    check_nesting(problems)
    print("importer tokens")
    check_tokens(problems)
    print("bundled media")
    check_media(problems)
    print("divi exports")
    check_exports(problems)

    print()
    for problem in problems:
        print("FAIL " + problem)
    print("PASS" if not problems else f"{len(problems)} problem(s)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
