# แดชบอร์ดพลังงาน อาคารศูนย์บริหารทางพิเศษ (กทพ.)

เว็บ: https://toyly2023.github.io/exat-energy-dashboard/

- `template/dashboard.html` — หน้าแดชบอร์ด (ข้อมูลอยู่ระหว่าง `/*DATA-START*/ … /*DATA-END*/`)
- `data/energy_monthly.xlsx` — สำเนาไฟล์ ข้อมูลพลังงานรายเดือน.xlsx
- `scripts/update_dashboard.py` — อ่าน Excel แล้วเขียนข้อมูลลงแดชบอร์ด
- `scripts/build_site.py` — สร้าง `_site/index.html` สำหรับ GitHub Pages
- `.github/workflows/deploy.yml` — ทุกชั่วโมง ดึง Excel ล่าสุดจากลิงก์แชร์ (ตัวแปร `XLSX_URL`) แล้ว deploy ใหม่

ตัวเลขรวมทั้งอาคารมาจากรายงาน EnMS ส่วนตัวเลขรายชั้นและผังห้องเป็นข้อมูลจำลอง
