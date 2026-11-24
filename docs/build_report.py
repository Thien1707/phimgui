"""Build the project report from the supplied school DOCX template."""

import re
import shutil
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(r"C:\Users\Asus\Downloads\Mau_Bao_Cao_DoAn_LapTrinhPythonNangCao.docx")
OUTPUT = ROOT / "docs" / "Bao_Cao_Do_An_PHIMHAY.docx"
CONTENT = ROOT / "docs" / "BAO_CAO_DO_AN.md"


def set_cell_shading(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    shade = OxmlElement("w:shd")
    shade.set(qn("w:fill"), fill)
    props.append(shade)


def set_cell_margins(cell, top=100, start=120, bottom=100, end=120):
    props = cell._tc.get_or_add_tcPr()
    margins = OxmlElement("w:tcMar")
    for side, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")
        margins.append(node)
    props.append(margins)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "5")
        tag.set(qn("w:color"), "D9D9D9")
        borders.append(tag)
    tbl_pr.append(borders)


def add_rich_text(paragraph, text):
    chunks = re.split(r"(\*\*.*?\*\*|`[^`]+`|\*[^*]+\*)", text)
    for chunk in chunks:
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            run = paragraph.add_run(chunk[2:-2])
            run.bold = True
        elif chunk.startswith("*") and chunk.endswith("*"):
            run = paragraph.add_run(chunk[1:-1])
            run.italic = True
        elif chunk.startswith("`") and chunk.endswith("`"):
            run = paragraph.add_run(chunk[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(10)
        else:
            paragraph.add_run(chunk)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Không tìm thấy mẫu báo cáo: {SOURCE}")
    shutil.copy2(SOURCE, OUTPUT)
    doc = Document(OUTPUT)

    # Keep the supplied cover and its member table. Remove template instructions,
    # sample rubric, and placeholder chapters after the cover metadata.
    body = doc._element.body
    children = list(body)
    cut = None
    for index, child in enumerate(children):
        if child.tag == qn("w:p") and "NHẬN XÉT VÀ ĐÁNH GIÁ" in "".join(child.itertext()):
            cut = index
            break
    if cut is None:
        raise RuntimeError("Không tìm thấy vị trí bắt đầu phần nhận xét trong mẫu.")
    for child in children[cut:]:
        if child.tag != qn("w:sectPr"):
            body.remove(child)

    # Replace cover placeholders without inventing identity details.
    for paragraph in doc.paragraphs:
        if "Nhóm [....]" in paragraph.text:
            paragraph.text = "Nhóm [điền số nhóm] (tối đa 3 sinh viên)"
        elif "tháng [..] năm 20[..]" in paragraph.text:
            paragraph.text = "TP. Hồ Chí Minh, tháng [..] năm 20[..]"
    # Update sample member cells while retaining the template's member table.
    if doc.tables:
        members = doc.tables[0]
        for row_index in range(1, len(members.rows)):
            members.cell(row_index, 1).text = "[MSSV]"
            members.cell(row_index, 2).text = "[Họ và tên]"
            members.cell(row_index, 3).text = "[Nhiệm vụ chính]"

    doc.add_page_break()
    p = doc.add_paragraph("BÁO CÁO ĐỒ ÁN MÔN HỌC", style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("XÂY DỰNG ỨNG DỤNG XEM PHIM PHIMHAY BẰNG FLASK")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].bold = True
    p.runs[0].font.size = Pt(14)
    doc.add_heading("Mục lục", level=1)
    for line in (
        "1. Giới thiệu đề tài", "2. Phân tích và thiết kế hệ thống",
        "3. Xây dựng ứng dụng với Flask", "4. Kết quả và kiểm thử",
        "5. Kết luận và hướng phát triển", "Tài liệu tham khảo", "Phụ lục",
    ):
        doc.add_paragraph(line)
    doc.add_page_break()

    lines = CONTENT.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("## 1. Giới thiệu đề tài"))
    i = start
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith(">"):
            i += 1
            continue
        if line.startswith("```"):
            code = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.space_after = Pt(8)
            run = p.add_run("\n".join(code))
            run.font.name = "Consolas"
            run.font.size = Pt(9)
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            if rows:
                columns = max(map(len, rows))
                table = doc.add_table(rows=1, cols=columns)
                table.autofit = True
                for row_index, values in enumerate(rows):
                    cells = table.rows[0].cells if row_index == 0 else table.add_row().cells
                    for column, cell in enumerate(cells):
                        cell.text = values[column] if column < len(values) else ""
                        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                        set_cell_margins(cell)
                        for paragraph in cell.paragraphs:
                            paragraph.paragraph_format.space_after = Pt(2)
                            for run in paragraph.runs:
                                run.font.name = "Times New Roman"
                                run.font.size = Pt(9)
                                if row_index == 0:
                                    run.bold = True
                                    run.font.color.rgb = RGBColor(255, 255, 255)
                        if row_index == 0:
                            set_cell_shading(cell, "263A5A")
                        elif row_index % 2 == 0:
                            set_cell_shading(cell, "F1F5F9")
                set_repeat_table_header(table.rows[0])
                set_table_borders(table)
                doc.add_paragraph().paragraph_format.space_after = Pt(2)
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("# "):
            doc.add_heading(line[2:], level=1)
        elif line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_rich_text(p, line[2:])
        elif re.match(r"\d+\. ", line):
            p = doc.add_paragraph(style="List Number")
            add_rich_text(p, re.sub(r"^\d+\. ", "", line))
        else:
            p = doc.add_paragraph()
            add_rich_text(p, line)
        i += 1

    # Set the report's main text to the requested template typography.
    for paragraph in doc.paragraphs:
        if paragraph.style.name not in ("Title", "Heading 1", "Heading 2"):
            paragraph.paragraph_format.line_spacing = 1.5
            paragraph.paragraph_format.space_after = Pt(4)
        for run in paragraph.runs:
            if run.font.name != "Consolas":
                run.font.name = "Times New Roman"
                run._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
                if paragraph.style.name not in ("Title", "Heading 1", "Heading 2") and run.font.size is None:
                    run.font.size = Pt(13)
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        style.font.color.rgb = RGBColor(0, 0, 0)
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
