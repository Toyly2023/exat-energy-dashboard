# -*- coding: utf-8 -*-
"""
อัปเดตแดชบอร์ดพลังงาน อาคารศูนย์บริหารทางพิเศษ จากไฟล์ ข้อมูลพลังงานรายเดือน.xlsx
วิธีใช้:  python3 update_dashboard.py
- อ่านไฟล์ Excel ในโฟลเดอร์เดียวกับสคริปต์
- เขียนข้อมูลลงระหว่าง /*DATA-START*/ ... /*DATA-END*/ ในไฟล์ HTML ในโฟลเดอร์เดียวกัน
- พิมพ์สรุปผลเป็น JSON บรรทัดสุดท้าย (changed = true/false)
"""
import json, os, re, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.environ.get("DASH_XLSX") or os.path.join(HERE, "ข้อมูลพลังงานรายเดือน.xlsx")
HTML = os.environ.get("DASH_HTML") or os.path.join(HERE, "infographic_อาคารศูนย์บริหารทางพิเศษ.html")
FLOOR_CODES = {"B1", "RF"} | {f"{i}F" for i in range(1, 29)} | {f"P{i}" for i in range(1, 6)}


def fail(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def num(v, where, allow_none=True):
    if v is None or (isinstance(v, str) and v.strip() == ""):
        if allow_none:
            return None
        fail(f"ช่องว่างที่ {where}")
    if isinstance(v, str):
        v = v.replace(",", "").strip()
    try:
        x = float(v)
    except (TypeError, ValueError):
        fail(f"ค่าไม่ใช่ตัวเลขที่ {where}: {v!r}")
    if x < 0:
        fail(f"ค่าติดลบที่ {where}: {x}")
    return int(round(x)) if abs(x - round(x)) < 1e-9 else round(x, 6)


def main():
    try:
        import openpyxl
    except ImportError:
        fail("ไม่พบ openpyxl (pip install openpyxl)")
    if not os.path.exists(XLSX):
        fail(f"ไม่พบไฟล์ {XLSX}")
    if not os.path.exists(HTML):
        fail(f"ไม่พบไฟล์ {HTML}")
    wb = openpyxl.load_workbook(XLSX, data_only=True, read_only=True)

    years = {}
    for name in wb.sheetnames:
        if not re.fullmatch(r"\d{4}", name.strip()):
            continue
        ws = wb[name]
        grid, solar = [], []
        for r in range(4, 16):
            g = num(ws.cell(r, 2).value, f"ชีต {name} แถว {r} คอลัมน์ B")
            s = num(ws.cell(r, 3).value, f"ชีต {name} แถว {r} คอลัมน์ C")
            if g is None and s is not None:
                fail(f"ชีต {name} แถว {r}: มีค่า Solar แต่ไม่มีค่าการไฟฟ้า")
            if g is not None and s is None:
                s = 0
            grid.append(g)
            solar.append(s)
        years[name.strip()] = {"grid": grid, "solar": solar, "share": None}

    if "สัดส่วนระบบ" in wb.sheetnames:
        ws = wb["สัดส่วนระบบ"]
        for r in range(4, 60):
            y = ws.cell(r, 1).value
            if y is None:
                continue
            y = str(int(y)) if isinstance(y, (int, float)) else str(y).strip()
            vals = [num(ws.cell(r, c).value, f"ชีต สัดส่วนระบบ แถว {r}") for c in range(2, 6)]
            if y in years and any(v is not None for v in vals):
                ac, split, light, other = [v or 0 for v in vals]
                src = ws.cell(r, 7).value or f"ชีต สัดส่วนระบบ ปี {y}"
                years[y]["share"] = {"ac": ac, "split": split, "light": light, "other": other, "src": str(src)}

    measures, meta = [], {}
    if "มาตรการ" in wb.sheetnames:
        ws = wb["มาตรการ"]
        for r in range(4, 200):
            y, n, t = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value
            if not t:
                continue
            y = str(int(y)) if isinstance(y, (int, float)) else str(y or "").strip()
            fl = str(ws.cell(r, 5).value or "").strip().upper()
            if fl not in FLOOR_CODES:
                fail(f"ชีต มาตรการ แถว {r}: ชั้น '{fl}' ไม่ถูกต้อง (ใช้ B1, 1F–28F, RF, P1–P5)")
            g = lambda c: num(ws.cell(r, c).value, f"ชีต มาตรการ แถว {r} คอลัมน์ {c}") or 0
            measures.append({
                "year": y, "n": int(n) if n else len([m for m in measures if m["year"] == y]) + 1,
                "t": str(t).strip(), "eq": str(ws.cell(r, 4).value or "").strip(), "floor": fl,
                "kw": [g(6), g(7)], "kwh": [g(8), g(9)], "baht": [g(10), g(11)],
                "status": str(ws.cell(r, 12).value or "ดำเนินการแล้ว").strip(),
            })
            m = meta.setdefault(y, {"period": str(ws.cell(r, 13).value or f"ปี {y}").strip(), "invest": 0})
            m["invest"] += g(14)

    tariff, ef = 4.51, 0.4999
    if "ค่าคงที่" in wb.sheetnames:
        ws = wb["ค่าคงที่"]
        tariff = num(ws.cell(3, 2).value, "ค่าคงที่ B3") or tariff
        ef = num(ws.cell(4, 2).value, "ค่าคงที่ B4") or ef

    with_data = [y for y, d in years.items() if any(v is not None for v in d["grid"])]
    if not with_data:
        fail("ไม่มีข้อมูลรายเดือนในชีตปีใดเลย")
    if not any(years[y]["share"] for y in with_data):
        fail("ต้องมีข้อมูลในชีต สัดส่วนระบบ อย่างน้อย 1 ปี")

    html = open(HTML, encoding="utf-8").read()
    m = re.search(r"/\*DATA-START\*/\nconst DATA = (.*?);\n/\*DATA-END\*/", html, re.S)
    if not m:
        fail("ไม่พบตำแหน่ง DATA-START/DATA-END ในไฟล์ HTML")
    old = json.loads(m.group(1))
    new = {"updated": old.get("updated"), "source": "ข้อมูลพลังงานรายเดือน.xlsx", "tariff": tariff, "ef": ef,
           "years": years, "measures": measures, "measMeta": meta}
    strip = lambda d: {k: v for k, v in d.items() if k not in ("updated", "source")}
    changed = strip(new) != strip(old)
    if changed:
        new["updated"] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).strftime("%Y-%m-%d")
        block = "/*DATA-START*/\nconst DATA = " + json.dumps(new, ensure_ascii=False, indent=1) + ";\n/*DATA-END*/"
        html = html[:m.start()] + block + html[m.end():]
        with open(HTML, "w", encoding="utf-8") as f:
            f.write(html)

    summary = {"ok": True, "changed": changed, "updated": new["updated"],
               "years": {y: {"months": sum(v is not None for v in years[y]["grid"]),
                             "grid_kwh": sum(v or 0 for v in years[y]["grid"]),
                             "solar_kwh": sum(v or 0 for v in years[y]["solar"]),
                             "share": "มี" if years[y]["share"] else "ประมาณ"} for y in sorted(years)},
               "measures": {y: sum(1 for x in measures if x["year"] == y) for y in sorted({x["year"] for x in measures})}}
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
