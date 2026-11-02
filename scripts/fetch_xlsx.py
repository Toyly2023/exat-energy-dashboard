# -*- coding: utf-8 -*-
"""Download an Excel file from a OneDrive/SharePoint/Google 'anyone with the link' share URL."""
import base64, sys, urllib.request, zipfile, io

def candidates(url):
    u = url.strip()
    if "docs.google.com/spreadsheets" in u:
        key = u.split("/d/")[1].split("/")[0]
        yield f"https://docs.google.com/spreadsheets/d/{key}/export?format=xlsx"
        return
    enc = base64.b64encode(u.encode()).decode().rstrip("=").replace("/", "_").replace("+", "-")
    yield f"https://api.onedrive.com/v1.0/shares/u!{enc}/root/content"
    sep = "&" if "?" in u else "?"
    yield u + sep + "download=1"
    yield u

def main(url, out):
    for c in candidates(url):
        try:
            req = urllib.request.Request(c, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=60).read()
            zipfile.ZipFile(io.BytesIO(data)).namelist()  # must be a real .xlsx
            open(out, "wb").write(data)
            print("downloaded", len(data), "bytes via", c.split("?")[0][:60])
            return 0
        except Exception as e:
            print("try failed:", c[:60], type(e).__name__)
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
