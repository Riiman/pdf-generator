import io
import os
import sys
import csv
import base64
import tempfile
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Iterable, Optional, Tuple

import pandas as pd
from jinja2 import Environment, FileSystemLoader, meta, select_autoescape
from html2docx import html2docx

from .utils import find_wkhtmltopdf_path, ensure_directory, safe_filename, unique_path


@dataclass
class GenerationOptions:
    output_dir: str
    filename_field: str
    concurrency: int = max(1, min(os.cpu_count() or 4, 8))
    pdf_margins_mm: Tuple[int, int, int, int] = (15, 15, 15, 15)  # top, right, bottom, left


def _create_jinja_env(template_dir: str) -> Environment:
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    return env


def parse_template_fields(template_path: str) -> List[str]:
    template_dir = str(Path(template_path).parent)
    template_name = Path(template_path).name
    env = _create_jinja_env(template_dir)
    source = env.loader.get_source(env, template_name)[0]
    ast = env.parse(source)
    variables = sorted(meta.find_undeclared_variables(ast))
    return variables


def render_html_from_template(template_path: str, context: Dict[str, object], base_href: Optional[str] = None) -> str:
    template_dir = str(Path(template_path).parent)
    template_name = Path(template_path).name
    env = _create_jinja_env(template_dir)
    template = env.get_template(template_name)
    html = template.render(**context)
    if base_href:
        base_tag = f'<base href="{base_href}" />'
        if "<head>" in html:
            html = html.replace("<head>", f"<head>\n    {base_tag}")
        else:
            html = f"{base_tag}\n" + html
    return html


def _wk_cmd(wkhtmltopdf_path: str, margins_mm: Tuple[int, int, int, int]) -> List[str]:
    top, right, bottom, left = margins_mm
    return [
        wkhtmltopdf_path,
        "--quiet",
        "--enable-local-file-access",
        f"--margin-top", str(top),
        f"--margin-right", str(right),
        f"--margin-bottom", str(bottom),
        f"--margin-left", str(left),
        "-",
        "-",
    ]


def generate_pdf_from_html(html: str, output_pdf_path: str, margins_mm: Tuple[int, int, int, int]) -> None:
    wk = find_wkhtmltopdf_path()
    cmd = _wk_cmd(wk, margins_mm)
    try:
        proc = subprocess.run(cmd, input=html.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="ignore")
            raise RuntimeError(f"wkhtmltopdf failed: {err[:500]}")
        with open(output_pdf_path, "wb") as f:
            f.write(proc.stdout)
    except FileNotFoundError:
        raise FileNotFoundError("wkhtmltopdf executable not found. Ensure it is bundled next to the app.")


def generate_docx_from_html(html: str, output_docx_path: str, base_url: Optional[str] = None) -> None:
    document = html2docx(html, base_url=base_url)
    document.save(output_docx_path)


def load_data_records(data_path: str) -> List[Dict[str, object]]:
    ext = Path(data_path).suffix.lower()
    if ext in (".csv", ".txt"):
        # Read with pandas to handle utf-8-sig and auto-dtype
        df = pd.read_csv(data_path, dtype=str, keep_default_na=False)
    elif ext in (".xlsx", ".xlsm", ".xls"):
        df = pd.read_excel(data_path, dtype=str)
        df = df.fillna("")
    else:
        raise ValueError("Unsupported data file. Use CSV or XLSX.")
    records = df.to_dict(orient="records")
    return records


def _sanitize_row_keys(row: Dict[str, object]) -> Dict[str, object]:
    sanitized: Dict[str, object] = {}
    for key, value in row.items():
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        sanitized[str(key)] = "" if value is None else value
    return sanitized


def _generate_one(
    template_path: str,
    row: Dict[str, object],
    opts: GenerationOptions,
    base_href: str,
) -> Tuple[str, str]:
    row = _sanitize_row_keys(row)
    html = render_html_from_template(template_path, row, base_href=base_href)

    filename_value = str(row.get(opts.filename_field, "output")).strip()
    filename_value = safe_filename(filename_value)

    pdf_out = unique_path(opts.output_dir, filename_value, ".pdf")
    docx_out = unique_path(opts.output_dir, filename_value, ".docx")

    generate_pdf_from_html(html, pdf_out, opts.pdf_margins_mm)
    generate_docx_from_html(html, docx_out, base_url=base_href)

    return pdf_out, docx_out


def generate_bulk(
    template_path: str,
    data_path: str,
    opts: GenerationOptions,
) -> List[Tuple[str, str]]:
    ensure_directory(opts.output_dir)
    base_href = Path(template_path).parent.resolve().as_uri() + "/"
    rows = load_data_records(data_path)

    results: List[Tuple[str, str]] = []
    errors: List[str] = []

    with ThreadPoolExecutor(max_workers=max(1, opts.concurrency)) as executor:
        futures = [
            executor.submit(_generate_one, template_path, row, opts, base_href)
            for row in rows
        ]
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                errors.append(str(exc))

    if errors:
        raise RuntimeError(f"Completed with errors in {len(errors)} records. Example: {errors[0]}")

    return results


def generate_single(
    template_path: str,
    row: Dict[str, object],
    opts: GenerationOptions,
) -> Tuple[str, str]:
    ensure_directory(opts.output_dir)
    base_href = Path(template_path).parent.resolve().as_uri() + "/"
    return _generate_one(template_path, row, opts, base_href)
