from datetime import date
from pathlib import Path

from openpyxl import Workbook

from app.services.document_processor import DocumentProcessor


def test_xlsx_extraction_preserves_sheets_headers_values_and_formulas(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sales.xlsx"
    workbook = Workbook()
    sales = workbook.active
    sales.title = "Sales 2026"
    sales.append(["Product", "Revenue", "Close date"])
    sales.append(["Contexta Pro", 12500, date(2026, 9, 18)])
    sales.append(["Contexta Team", "=SUM(B2*2)", None])
    notes = workbook.create_sheet("Notes")
    notes.append(["Owner", "Comment"])
    notes.append(["Ahmed", "Renewal discussion"])
    workbook.save(source)

    document = DocumentProcessor().process(source)

    assert document.extension == ".xlsx"
    assert "Worksheet: Sales 2026" in document.content
    assert "Product=Contexta Pro" in document.content
    assert "Revenue=12500" in document.content
    assert "Close date=2026-09-18T00:00:00" in document.content
    assert "Revenue=formula: =SUM(B2*2)" in document.content
    assert "Worksheet: Notes" in document.content
    assert "Owner=Ahmed" in document.content
