# -*- coding: utf-8 -*-
"""Wrap template/dashboard.html (artifact body fragment) into a full standalone page at _site/index.html"""
import os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "template", "dashboard.html"), encoding="utf-8").read()
head_bits = []
for pat in (r"<title>.*?</title>", r'<meta name="claude:[^>]*>\s*', r'<link rel="preconnect"[^>]*>\s*', r'<link rel="stylesheet"[^>]*>\s*'):
    m = re.search(pat, src, re.S)
    if m:
        head_bits.append(m.group(0).strip())
        src = src.replace(m.group(0), "", 1)
head_bits = [b for b in head_bits if not b.startswith('<meta name="claude:')]
page = f"""<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="แดชบอร์ดพลังงาน อาคารศูนย์บริหารทางพิเศษ การทางพิเศษแห่งประเทศไทย">
<meta property="og:title" content="แดชบอร์ดพลังงาน อาคารศูนย์บริหารทางพิเศษ">
<meta property="og:description" content="ไฟฟ้าจากการไฟฟ้าและ Solar รายเดือน สัดส่วนการใช้พลังงาน และมาตรการอนุรักษ์พลังงาน">
<meta name="theme-color" content="#173a5e">
{chr(10).join(head_bits)}
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;font-size:14px}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
{src.strip()}
</body>
</html>
"""
os.makedirs(os.path.join(ROOT, "_site"), exist_ok=True)
open(os.path.join(ROOT, "_site", "index.html"), "w", encoding="utf-8").write(page)
open(os.path.join(ROOT, "_site", ".nojekyll"), "w").write("")
print("built _site/index.html", len(page))
