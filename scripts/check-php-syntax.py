#!/usr/bin/env python3
"""A structural sanity check for the plugin and theme PHP.

There is no PHP runtime in this environment, so `php -l` is not available.
This walks the files as a tokeniser would — tracking strings, heredocs and
comments — and reports unterminated literals or unbalanced brackets, which
covers the ways hand-edited PHP usually breaks.
"""

import os
import re
import sys

PAIRS = {"{": "}", "(": ")", "[": "]"}
CLOSERS = {v: k for k, v in PAIRS.items()}


def check(path):
    src = open(path, encoding="utf-8").read()
    errors = []
    stack = []
    i = 0
    line = 1
    n = len(src)
    in_php = False

    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            i += 1
            continue

        if not in_php:
            if src.startswith("<?php", i):
                in_php = True
                i += 5
                continue
            i += 1
            continue

        if src.startswith("?>", i):
            in_php = False
            i += 2
            continue

        # Comments
        if src.startswith("//", i) or ch == "#":
            end = src.find("\n", i)
            i = n if end == -1 else end
            continue
        if src.startswith("/*", i):
            end = src.find("*/", i + 2)
            if end == -1:
                errors.append(f"{path}:{line}: unterminated block comment")
                break
            line += src.count("\n", i, end)
            i = end + 2
            continue

        # Heredoc / nowdoc
        m = re.match(r"<<<\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1\r?\n", src[i:])
        if m:
            label = m.group(2)
            body_start = i + m.end()
            close = re.search(rf"^\s*{label}\b", src[body_start:], re.MULTILINE)
            if not close:
                errors.append(f"{path}:{line}: unterminated heredoc {label}")
                break
            end = body_start + close.end()
            line += src.count("\n", i, end)
            i = end
            continue

        # Quoted strings
        if ch in "'\"":
            j = i + 1
            while j < n:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == ch:
                    break
                j += 1
            if j >= n:
                errors.append(f"{path}:{line}: unterminated {ch} string")
                break
            line += src.count("\n", i, j)
            i = j + 1
            continue

        if ch in PAIRS:
            stack.append((ch, line))
            i += 1
            continue

        if ch in CLOSERS:
            if not stack:
                errors.append(f"{path}:{line}: stray '{ch}'")
            elif stack[-1][0] != CLOSERS[ch]:
                opener, opened_at = stack[-1]
                errors.append(
                    f"{path}:{line}: '{ch}' closes '{opener}' opened on line {opened_at}")
                stack.pop()
            else:
                stack.pop()
            i += 1
            continue

        i += 1

    for opener, opened_at in stack:
        errors.append(f"{path}:{opened_at}: '{opener}' is never closed")

    return errors


def main(roots):
    files = []
    for root in roots:
        for dirpath, _dirs, names in os.walk(root):
            files.extend(os.path.join(dirpath, f) for f in names if f.endswith(".php"))

    failures = []
    for path in sorted(files):
        errors = check(path)
        status = "ok" if not errors else "FAIL"
        print(f"{status:4} {path}")
        failures.extend(errors)

    for err in failures:
        print("  " + err)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["wordpress"]))
