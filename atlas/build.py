#!/usr/bin/env python3
"""Build atlas/index.html from atlas/pages/*.html fragments (stdlib only).

Each fragment starts with a comment line:  <!-- id: overview | nav: 总览 | group: 系统 -->
The order of PAGES below is the order in the sidebar. Run:  python3 atlas/build.py
"""
from __future__ import annotations
import re, html, pathlib, datetime

HERE = pathlib.Path(__file__).resolve().parent
PAGES = ["overview", "concepts", "flows",
         "core", "mem", "mail", "ime", "agent", "search",
         "ref-api", "ref-manifest", "ref-mem", "ref-tasks", "ref-prompts", "ref-files",
         "ops",
         "decisions", "open", "glossary", "changelog"]
META = re.compile(r"<!--\s*id:\s*(\S+)\s*\|\s*nav:\s*([^|]+?)\s*\|\s*group:\s*([^>]+?)\s*-->")


def main() -> None:
    nav, bodies, group_order = {}, [], []
    for pid in PAGES:
        src = (HERE / "pages" / f"{pid}.html").read_text(encoding="utf-8")
        m = META.search(src)
        if not m:
            raise SystemExit(f"{pid}.html: missing meta comment")
        _, label, group = m.groups()
        if group not in nav:
            nav[group] = []
            group_order.append(group)
        nav[group].append((pid, label))
        bodies.append(f'<section class="page" id="{pid}" data-title="{html.escape(label)}">\n{src[m.end():].strip()}\n</section>')
    navhtml = "\n".join(
        f'<div class="navgroup"><div class="navlabel">{html.escape(g)}</div>'
        + "".join(f'<a href="#{pid}" data-page="{pid}">{html.escape(lbl)}</a>' for pid, lbl in nav[g]) + "</div>"
        for g in group_order)
    options = "".join(f'<option value="{pid}">{html.escape(g)} · {html.escape(lbl)}</option>'
                      for g in group_order for pid, lbl in nav[g])
    shell = (HERE / "shell.html").read_text(encoding="utf-8")
    out = (shell.replace("{{NAV}}", navhtml).replace("{{OPTIONS}}", options)
           .replace("{{PAGES}}", "\n".join(bodies))
           .replace("{{BUILT}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
    (HERE / "index.html").write_text(out, encoding="utf-8")
    # a full document for GitHub Pages (the Artifact host adds its own skeleton)
    head, body = out.split('<div class="wrap">', 1)
    site = ('<!doctype html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + head + '</head>\n<body>\n<div class="wrap">' + body + '\n</body>\n</html>\n')
    (HERE / "site").mkdir(exist_ok=True)
    (HERE / "site" / "index.html").write_text(site, encoding="utf-8")
    (HERE / "site" / ".nojekyll").write_text("", encoding="utf-8")
    print(f"atlas/index.html + site/index.html: {len(PAGES)} pages, {len(out)//1024} KB")


if __name__ == "__main__":
    main()
