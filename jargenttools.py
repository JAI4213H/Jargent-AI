
import os
import base64
from io import BytesIO
from openai import OpenAI
import subprocess
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from PIL import ImageGrab
import uuid
from PIL import Image ##make image resize to atleast 32 pixels
import json
import re
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from pathlib import Path
from openpyxl.utils import get_column_letter



client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)
@tool
def vision(file_name, prompt="Describe this image."):
    """Use this tool to analyze an image or screenshot and answer
    the user's questions about its contents. It can identify UI elements,
    read visible text, describe objects, and extract relevant visual details.
    Images smaller than 32 pixels in either dimension are enlarged in memory.
    """

    with Image.open(fr"{file_name}") as source:
        width, height = source.size
        if width < 32 or height < 32:
            source = source.resize((max(width, 32), max(height, 32)))

        buffer = BytesIO()
        source.save(buffer, format="PNG")
        image = base64.b64encode(buffer.getvalue()).decode("utf-8")

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{prompt}. Tell what is asked under 100 words and make sure the asked information is there."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image}"
                        }
                    }
                ]
            }
        ],
        max_tokens=500
    )

    return response.choices[0].message.content


import subprocess
import time
from langchain_core.tools import tool


@tool
def systemfile_tool(a: str, status: str) -> str:
    """
    Execute a CMD or PowerShell command for system operations.
    'a' is the command to execute.
    'status' briefly describes the operation.
    Return concise output to the model.
    """
    print(f"[JARGENT] {status}")
    start = time.perf_counter()

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                a
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        elapsed = time.perf_counter() - start
        output = (result.stdout or "").strip()
        error = (result.stderr or "").strip()

        if result.returncode != 0:
            return (
                f"FAILED (exit code {result.returncode})\n"
                f"{error[-2000:] or output[-2000:]}"
            )

        print(f"[JARGENT] Completed in {elapsed:.2f}s")

        return (
            f"SUCCESS: {status}\n"
            f"{output[-3000:] if output else 'Command completed with no output.'}"
        )

    except subprocess.TimeoutExpired:
        return (
            f"TIMEOUT: {status}. Command exceeded 30 seconds. "
            "Check whether it is blocked or still running."
        )

    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"



@tool
def take_screenshot():
    """Capture the current screen and save it as a uniquely named PNG image."""
    screenshot = ImageGrab.grab()
    name = f"{uuid.uuid4().hex}.png"
    screenshot.save(name)
    return name



@tool
def excel_tool(path: str, operations_json: str) -> dict:
    """
    Use this tool for ALL operations involving Excel workbooks.

    Use it to inspect workbook sheets and headers, read data,
    create or edit columns, calculate values, apply formulas,
    sort rows, format cells, create charts, and save changes.

    If the workbook path is known, call excel_tool directly. If the path is
    unknown, systemfile_tool may only locate the file; it must never inspect
    or edit the workbook.

    For an unknown sheet or column, first use action "find_columns" with a
    short query and omit "sheet" to search all sheets. It returns only
    matching sheet and column names, never the full header list. Then batch
    the edits into one excel_tool call.

    In formulas, never guess Excel column letters. Use the exact header inside
    {col:Header Name}, including spaces or symbols, with {row}. For example,
    =IF({col:Marks / 100}{row}<33,"Fail","Pass") is valid.

    operations_json is a JSON list. Supported actions include:
    find_columns, add_column, set_formula, set_cell, rename_header,
    sort_rows, delete_rows, delete_columns, remove_duplicates,
    style_header, and autofit_columns. Do not ask the user for action names;
    use this schema directly.
    """
    file_path = Path(path).expanduser()

    if not file_path.is_file():
        return {"status": "error", "message": "Excel file not found."}

    if file_path.suffix.lower() not in (".xlsx", ".xlsm"):
        return {
            "status": "error",
            "message": "Only .xlsx and .xlsm files are supported."
        }

    try:
        operations = json.loads(operations_json)

        if not isinstance(operations, list):
            raise ValueError("Operations must be a JSON list.")

        if not operations:
            raise ValueError("No operations supplied.")

        if not all(isinstance(op, dict) for op in operations):
            raise ValueError("Each operation must be a JSON object.")

        inspection_only = all(
            op.get("action") == "find_columns"
            for op in operations
        )

        # Use read-only mode when the model only needs targeted column matches.
        wb = load_workbook(
            file_path,
            read_only=inspection_only,
            keep_vba=file_path.suffix.lower() == ".xlsm"
        )

        results = []

        def get_sheet(op):
            name = op.get("sheet")
            if name is None:
                return wb.active
            if name not in wb.sheetnames:
                raise ValueError(f"Sheet not found: {name}")
            return wb[name]

        def get_column(ws, column):
            # Accept either a header name or Excel column letter.
            if isinstance(column, str):
                for cell in ws[1]:
                    if str(cell.value).strip().lower() == column.strip().lower():
                        return cell.column

                if column.isalpha() and column.isupper():
                    from openpyxl.utils.cell import column_index_from_string
                    return column_index_from_string(column)

                raise ValueError(f"Column not found: {column}")

            if isinstance(column, int) and column > 0:
                return column

            raise ValueError(f"Invalid column: {column}")

        def find_columns(ws, query, limit=5):
            query_parts = str(query or "").strip().lower().split()
            if not query_parts:
                raise ValueError("A column search query is required.")

            headers = next(
                ws.iter_rows(min_row=1, max_row=1, values_only=True),
                ()
            )
            matches = []

            for index, value in enumerate(headers, start=1):
                header = str(value or "").strip()
                if header and all(
                    part in header.lower() for part in query_parts
                ):
                    matches.append({"column": header, "index": index})
                    if len(matches) >= limit:
                        break

            return matches

        for op in operations:
            action = op.get("action")

            if action == "find_columns":
                limit = op.get("limit", 5)
                sheets = (
                    [get_sheet(op)]
                    if op.get("sheet")
                    else wb.worksheets
                )
                matches = []

                for sheet in sheets:
                    for match in find_columns(
                        sheet,
                        op.get("query"),
                        limit - len(matches)
                    ):
                        matches.append({
                            "sheet": sheet.title,
                            **match
                        })
                        if len(matches) >= limit:
                            break
                    if len(matches) >= limit:
                        break

                results.append({
                    "query": op.get("query"),
                    "matches": matches
                })
                continue

            # Create a worksheet.
            if action == "create_sheet":
                name = op["name"]
                if name in wb.sheetnames:
                    raise ValueError(f"Sheet already exists: {name}")
                wb.create_sheet(name)
                results.append(f"Created sheet: {name}")

            # Rename a worksheet.
            elif action == "rename_sheet":
                ws = get_sheet(op)
                new_name = op["new_name"]

                if new_name in wb.sheetnames and new_name != ws.title:
                    raise ValueError(f"Sheet already exists: {new_name}")

                ws.title = new_name
                results.append(f"Renamed sheet to: {new_name}")

            else:
                ws = get_sheet(op)

                # Change one cell.
                if action == "set_cell":
                    ws[op["cell"]] = op.get("value")
                    results.append(f"Updated cell {op['cell']}")

                # Add a column, optionally with values.
                elif action == "add_column":
                    name = op["name"]
                    values = op.get("values", [])
                    position = op.get("position", ws.max_column + 1)

                    if not 1 <= position <= ws.max_column + 1:
                        raise ValueError("Invalid column position.")

                    ws.insert_cols(position)
                    ws.cell(1, position, name)

                    for row, value in enumerate(values, start=2):
                        ws.cell(row, position, value)

                    results.append(f"Added column: {name}")

                # Fill a column with an Excel formula.
                elif action == "set_formula":
                    col = get_column(ws, op["column"])
                    start = op.get("start_row", 2)
                    end = op.get("end_row", ws.max_row)
                    formula = op["formula"]

                    def resolve_column(match):
                        header = match.group(1).strip()
                        return get_column_letter(get_column(ws, header))

                    formula = re.sub(
                        r"\{col:([^}]+)\}",
                        resolve_column,
                        formula
                    )

                    for row in range(start, end + 1):
                        ws.cell(
                            row, col,
                            formula.replace("{row}", str(row))
                        )

                    results.append(f"Filled formulas in column {col}")

                # Rename a header.
                elif action == "rename_header":
                    col = get_column(ws, op["column"])
                    ws.cell(1, col, op["new_name"])
                    results.append(f"Renamed header to {op['new_name']}")

                # Sort data rows by a column.
                elif action == "sort_rows":
                    col = get_column(ws, op["column"])
                    reverse = op.get("order", "asc").lower() == "desc"

                    rows = list(
                        ws.iter_rows(
                            min_row=2,
                            max_row=ws.max_row,
                            max_col=ws.max_column,
                            values_only=True
                        )
                    )

                    rows.sort(
                        key=lambda row: (
                            row[col - 1] is None,
                            row[col - 1]
                            if isinstance(row[col - 1], (int, float, str))
                            else str(row[col - 1])
                        ),
                        reverse=reverse
                    )

                    for row_num, row_data in enumerate(rows, start=2):
                        for col_num, value in enumerate(row_data, start=1):
                            ws.cell(row_num, col_num, value)

                    results.append("Sorted data rows")

                elif action == "delete_rows":
                    ws.delete_rows(op["start"], op.get("count", 1))
                    results.append("Deleted rows")

                elif action == "delete_columns":
                    col = get_column(ws, op["column"])
                    ws.delete_cols(col, op.get("count", 1))
                    results.append("Deleted columns")

                elif action == "remove_duplicates":
                    columns = op.get("columns")
                    indices = (
                        [get_column(ws, c) for c in columns]
                        if columns
                        else list(range(1, ws.max_column + 1))
                    )

                    seen = set()
                    duplicates = []

                    for row in range(2, ws.max_row + 1):
                        key = tuple(
                            ws.cell(row, col).value for col in indices
                        )
                        if key in seen:
                            duplicates.append(row)
                        else:
                            seen.add(key)

                    for row in reversed(duplicates):
                        ws.delete_rows(row)

                    results.append(
                        f"Removed {len(duplicates)} duplicate rows"
                    )

                elif action == "style_header":
                    fill = PatternFill(
                        fill_type="solid",
                        fgColor=op.get("color", "1F4E78")
                    )
                    font = Font(
                        bold=True,
                        color=op.get("font_color", "FFFFFF")
                    )

                    for cell in ws[1]:
                        cell.fill = fill
                        cell.font = font
                        cell.alignment = Alignment(horizontal="center")

                    results.append("Formatted header row")

                elif action == "autofit_columns":
                    for column_cells in ws.columns:
                        letter = column_cells[0].column_letter
                        longest = max(
                            (
                                len(str(cell.value))
                                for cell in column_cells
                                if cell.value is not None
                            ),
                            default=0
                        )
                        ws.column_dimensions[letter].width = min(
                            longest + 2, 60
                        )

                    results.append("Adjusted column widths")

                else:
                    raise ValueError(f"Unsupported action: {action}")

        if not inspection_only:
            wb.save(file_path)
        wb.close()

        return {
            "status": "success",
            "file": str(file_path),
            "operations_completed": results
        }

    except Exception as exc:
        try:
            wb.close()
        except Exception:
            pass

        return {
            "status": "error",
            "message": str(exc),
            "hint": "Check the operation parameters and workbook path."
        }

def clean_tool_name(name: str) -> str:
    """
    Removes GPT-OSS Harmony channel text from malformed tool names.
    Example:
    excel_tool<|channel|>commentary → excel_tool
    """
    name = name.split("<|channel|>", 1)[0]
    name = name.removeprefix("functions.")
    return name.strip()







tool = [vision, systemfile_tool, take_screenshot, excel_tool]

def get_tools():
    global tool
    tools = []
    tool_dir = {}

    for item in tool:
        name = getattr(item, "name", getattr(item, "__name__", None))
        if not name:
            raise ValueError(f"Tool has no name: {item!r}")

        schema = convert_to_openai_tool(item)
        schema["function"]["name"] = name
        tools.append(schema)
        tool_dir[name] = item

    return tools, tool_dir


