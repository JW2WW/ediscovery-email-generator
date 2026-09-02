"""
Generates realistic office document attachments using only the Python standard library.
"""
import io
import os
import random
import re
import struct
import time
import zipfile
from xml.sax.saxutils import escape

SAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")

FILENAME_STEMS = [
    "Q{q}_{year}_Budget_Forecast", "Invoice_{num}_Acme_Corp", "Meeting_Notes_{date}",
    "Project_Status_Report_{date}", "Vendor_Quote_{num}", "Expense_Report_{initials}_{date}",
    "Contract_Amendment_Draft_v{ver}", "Sales_Pipeline_{quarter}", "Board_Presentation_{date}",
    "Annual_Review_{year}", "Client_Proposal_{client}", "Timesheet_{month}_{year}",
    "Purchase_Order_{num}", "Compliance_Checklist_{year}",
]
CLIENTS = ["Meridian", "Northgate", "Summit", "Pinnacle", "Harbor", "Atlas", "Vertex"]
TOPICS = ["Onboarding", "Security", "QBR", "Renewal", "Migration", "Audit"]
INITIALS = ["JW", "MR", "KL", "TS", "AP", "RB", "NC", "DH"]

def _random_filename_stem():
    now = time.localtime()
    year, quarter = now.tm_year, (now.tm_mon - 1) // 3 + 1
    return random.choice(FILENAME_STEMS).format(
        q=quarter, year=year, num=random.randint(1000, 9999), date=time.strftime("%Y%m%d"),
        initials=random.choice(INITIALS), ver=random.randint(1, 4),
        quarter=f"Q{quarter}_{year}", client=random.choice(CLIENTS),
        topic=random.choice(TOPICS), month=time.strftime("%B"))

def _ensure_samples_dir():
    os.makedirs(SAMPLES_DIR, exist_ok=True)

def _write_sample(path, data):
    _ensure_samples_dir()
    with open(path, "wb") as f:
        f.write(data)
    return path

def _paragraphs_from_text(text, count=5):
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if len(s.strip()) > 20]
    if not sentences:
        sentences = [text.strip() or "Please review the attached document at your earliest convenience."]
    random.shuffle(sentences)
    return sentences[:count]

def generate_pdf(subject, body_text):
    lines = [subject[:80], ""] + [l[:120] for l in _paragraphs_from_text(body_text, 8)]
    content_lines = ["BT", "/F1 11 Tf", "50 750 Td", "14 TL"]
    for i, line in enumerate(lines):
        safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_lines.append(("" if i == 0 else "T* ") + f"({safe}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream\nendobj\n",
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]
    pdf = io.BytesIO(); pdf.write(b"%PDF-1.4\n"); offsets = [0]
    for obj in objects:
        offsets.append(pdf.tell()); pdf.write(obj)
    xref_start = pdf.tell()
    pdf.write(f"xref\n0 {len(offsets)}\n".encode()); pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode())
    pdf.write(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode())
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.pdf"), pdf.getvalue())

def _xlsx_shared_strings(strings):
    items = "".join(f"<si><t>{escape(s)}</t></si>" for s in strings)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        f'count="{len(strings)}" uniqueCount="{len(strings)}">{items}</sst>')

def _xlsx_sheet_xml(headers, rows):
    def cell(col, row, val, str_index):
        ref = f"{col}{row}"
        if isinstance(val, (int, float)):
            return f'<c r="{ref}"><v>{val}</v></c>'
        return f'<c r="{ref}" t="s"><v>{str_index[val]}</v></c>'
    strings = list(headers)
    for row in rows:
        for val in row:
            if isinstance(val, str) and val not in strings:
                strings.append(val)
    str_index = {s: i for i, s in enumerate(strings)}
    sheet_rows = []
    sheet_rows.append(f'<row r="1">{"".join(cell(chr(65+i),1,h,str_index) for i,h in enumerate(headers))}</row>')
    for r_idx, row in enumerate(rows, start=2):
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cell(chr(65+c),r_idx,v,str_index) for c,v in enumerate(row))}</row>')
    sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>')
    return strings, sheet

def generate_xlsx(subject, body_text):
    headers = ["Line Item", "Department", "Amount", "Status", "Notes"]
    departments = ["Engineering", "Sales", "Marketing", "Operations", "Finance", "HR"]
    statuses = ["Approved", "Pending", "Submitted", "Under Review"]
    topic = " ".join(body_text.split()[:6]) or subject
    rows = []
    for i in range(random.randint(8, 18)):
        dept = random.choice(departments)
        rows.append([f"{dept} - Item {i+1}", dept, round(random.uniform(1200, 85000), 2),
                     random.choice(statuses), f"Related to: {topic[:40]}"])
    strings, sheet_xml = _xlsx_sheet_xml(headers, rows)
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>')
    workbook = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Summary" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wb_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        '</Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        zf.writestr("xl/sharedStrings.xml", _xlsx_shared_strings(strings))
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.xlsx"), buf.getvalue())

def _pack_ole_workbook(biff_data):
    sector_size = 512
    stream = biff_data + b"\x00" * ((sector_size - len(biff_data) % sector_size) % sector_size)
    def dir_entry(name, obj_type, start_sector, size):
        entry = bytearray(128)
        nu = name.encode("utf-16-le")[:62]
        entry[0:len(nu)] = nu
        entry[0x40:0x42] = struct.pack("<H", len(name))
        entry[0x42] = obj_type
        entry[0x43] = 0x01 if obj_type == 5 else 0x00
        entry[0x74:0x78] = struct.pack("<I", start_sector)
        entry[0x78:0x7C] = struct.pack("<I", size)
        return bytes(entry)
    n = len(stream) // sector_size
    fat = [0xFFFFFFFD, 0xFFFFFFFE] + [0xFFFFFFFE if s == n-1 else 2+s+1 for s in range(n)]
    while len(fat) < sector_size // 4:
        fat.append(0xFFFFFFFF)
    fat_sector = struct.pack("<" + "I" * (sector_size // 4), *fat[:sector_size//4])
    dir_sector = dir_entry("Root Entry", 5, 0xFFFFFFFF, 0) + dir_entry("Workbook", 2, 2, len(biff_data)) + b"\x00" * (sector_size - 256)
    header = bytearray(512)
    header[0:8] = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
    header[0x18:0x1A] = struct.pack("<H", 0x003E)
    header[0x1A:0x1C] = struct.pack("<H", 0x0003)
    header[0x1C:0x1E] = struct.pack("<H", 0xFFFE)
    header[0x1E] = 9; header[0x20] = 6
    header[0x28:0x2C] = struct.pack("<I", 1)
    header[0x2C:0x30] = struct.pack("<I", 1)
    header[0x30:0x34] = struct.pack("<I", 1)
    header[0x38:0x3C] = struct.pack("<I", 0x1000)
    return bytes(header) + fat_sector + dir_sector + stream

def generate_xls(subject, body_text):
    def record(rec_type, payload):
        return struct.pack("<HH", len(payload), rec_type) + payload
    def label(row, col, text):
        enc = text.encode("utf-8", errors="replace")[:255]
        return record(0x0204, struct.pack("<HH", row, col) + struct.pack("<B", len(enc)) + enc)
    def rk_number(row, col, value):
        ival = int(value * 100)
        return record(0x027E, struct.pack("<HHI", row, col, ((ival << 2) | 0x02) & 0xFFFFFFFF))
    biff = record(0x0809, struct.pack("<HH", 0x0600, 0x0010))
    biff += label(0, 0, subject[:40]) + label(0, 1, time.strftime("%Y-%m-%d"))
    biff += label(2, 0, "Category") + label(2, 1, "Budget") + label(2, 2, "Actual")
    for i, cat in enumerate(["Personnel", "Travel", "Software", "Hardware", "Consulting"]):
        budget = random.randint(5000, 80000)
        actual = int(budget * random.uniform(0.6, 1.15))
        biff += label(i+3, 0, cat) + rk_number(i+3, 1, budget) + rk_number(i+3, 2, actual)
    biff += label(9, 0, body_text[:80]) + record(0x000A, b"")
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.xls"), _pack_ole_workbook(biff))

def _rtf_escape(text):
    out = []
    for ch in text:
        if ch in "\\{}":
            out.append("\\" + ch)
        elif ord(ch) > 127:
            out.append(f"\\u{ord(ch)}?")
        else:
            out.append(ch)
    return "".join(out)

def generate_docx(subject, body_text):
    paragraphs = _paragraphs_from_text(body_text, random.randint(4, 8))
    body_xml = "".join(f"<w:p><w:r><w:t>{escape(p)}</w:t></w:r></w:p>" for p in paragraphs)
    heading = f"<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>{escape(subject)}</w:t></w:r></w:p>"
    document_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{heading}{body_xml}</w:body></w:document>")
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '</Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.docx"), buf.getvalue())

def generate_doc(subject, body_text):
    rtf = [r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Arial;}}", r"\f0\fs24",
           r"\b " + _rtf_escape(subject[:100]) + r"\b0\par"]
    for p in _paragraphs_from_text(body_text, 6):
        rtf.append(_rtf_escape(p) + r"\par")
    rtf.append("}")
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.doc"), "".join(rtf).encode("utf-8"))

def generate_pptx(subject, body_text):
    slides = [subject] + _paragraphs_from_text(body_text, 4)
    slide_xmls = []
    for content in slides:
        slide_xmls.append(
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
            'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
            '<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/>'
            '<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/>'
            f'<p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
            f'<a:p><a:r><a:t>{escape(content[:200])}</a:t></a:r></a:p></p:txBody></p:sp>'
            '</p:spTree></p:cSld></p:sld>')
    sld_ids = "".join(f'<p:sldId id="{256+i}" r:id="rId{i+1}"/>' for i in range(len(slides)))
    presentation_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<p:sldIdLst>{sld_ids}</p:sldIdLst></p:presentation>')
    pres_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + "".join(f'<Relationship Id="rId{i+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>' for i in range(len(slides)))
        + '</Relationships>')
    content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
        + "".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(len(slides)))
        + '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
        '</Relationships>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("ppt/presentation.xml", presentation_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        for i, slide in enumerate(slide_xmls):
            zf.writestr(f"ppt/slides/slide{i+1}.xml", slide)
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.pptx"), buf.getvalue())

def generate_ppt(subject, body_text):
    rtf = [r"{\rtf1\ansi\deff0", r"{\fonttbl{\f0 Arial;}}", r"\f0\fs32",
           r"\b " + _rtf_escape(subject) + r"\b0\par\par"]
    for b in _paragraphs_from_text(body_text, 5):
        rtf.append(r"\bullet  " + _rtf_escape(b) + r"\par")
    rtf.append("}")
    return _write_sample(os.path.join(SAMPLES_DIR, f"{_random_filename_stem()}.ppt"), "".join(rtf).encode("utf-8"))

GENERATORS = {"pdf": generate_pdf, "xlsx": generate_xlsx, "xls": generate_xls,
              "docx": generate_docx, "doc": generate_doc, "pptx": generate_pptx, "ppt": generate_ppt}
OFFICE_EXTENSIONS = ["pdf", "xlsx", "xls", "docx", "doc", "pptx", "ppt"]

def generate_random_document(subject, body_text, ext=None):
    if ext is None:
        ext = random.choice(OFFICE_EXTENSIONS)
    return GENERATORS.get(ext, generate_pdf)(subject, body_text)

def ensure_document_variety(count=5):
    subject = "Quarterly Business Review"
    body = ("Please find attached the updated figures for this quarter. "
            "We need your sign-off by end of week. Let me know if you have questions.")
    exts = OFFICE_EXTENSIONS.copy()
    random.shuffle(exts)
    created = []
    for ext in exts[:count]:
        try:
            created.append(generate_random_document(subject, body, ext=ext))
        except Exception:
            pass
    return created
