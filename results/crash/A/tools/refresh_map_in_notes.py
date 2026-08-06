#!/usr/bin/env python3
"""Replace the fenced token map inside notes/A-length-vs-content.md with the
current results/crash/A/token_map.txt, so the write-up cannot drift from the data."""
import re

NOTES = "/workspace/nsfw-fix/notes/A-length-vs-content.md"
MAP = "/workspace/nsfw-fix/results/crash/A/token_map.txt"

s = open(NOTES).read()
m = open(MAP).read().strip()
start = s.index("### The pooled map")
a = s.index("```", start)
b = s.index("```", a + 3)
s = s[:a] + "```\n" + m + "\n" + s[b:]
open(NOTES, "w").write(s)
print("map refreshed:", len(m.splitlines()), "lines")
