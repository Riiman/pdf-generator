## LetterGen (Offline PDF & DOCX Letter Generator)

LetterGen is a small, offline Windows application to generate appointment/placement letters one-by-one or in bulk from an HTML template and a CSV/XLSX data file. It outputs both PDF and DOCX for each record, preserves fonts/margins, and never transmits data.

### Features
- Offline, no login or network required
- Single or bulk generation from one template
- Outputs two files per record: PDF and DOCX
- Automatic file naming from a selected field
- Supports images (e.g., company logo) referenced relatively next to the template

### Quick Start (User)
1. Launch `LetterGen.exe`.
2. Template: Click Browse and select an HTML file (e.g., `assets/template_letter.html`).
3. Data: Select your CSV or XLSX (e.g., `assets/sample_data.csv`).
4. Output Folder: Choose a target folder.
5. Filename Field: Pick a field that will name each file (e.g., `filename`).
6. Generate Batch: Produces PDF and DOCX per row. Or use Generate One for a single letter by entering field values.

Notes:
- To include a logo, place the image file (PNG/JPG) in the same folder as the template and reference it relatively: `<img src="logo.png" height="40" />`.
- Fonts are resolved from the local Windows installation. If you need a specific font, install it on Windows or embed via `@font-face` using a local file path.

### Data Format
- CSV: UTF-8 (or UTF-8 with BOM), first row as headers.
- XLSX: First sheet is read. Ensure headers in first row.

Sample headers used by the sample template:
`company_name, company_address_line1, company_address_line2, company_phone, letter_date, full_name, address_line1, address_line2, position_title, start_date, employee_id, compensation, signer_name, signer_title, filename`

### Template Authoring (HTML + Jinja2)
Use double curly braces for fields, e.g. `{{ full_name }}`. See `assets/template_letter.html` for a working example. The same HTML is used to create both PDF and DOCX.

### Performance Tips
- Use a reasonable number of Parallel Workers (default ~CPU cores).
- Keep images optimized and hosted next to the template.
- Avoid extremely heavy CSS for fastest PDF conversion.

### Build (Developer, on Windows)
Prerequisites: Python 3.11+, Visual C++ Build Tools recommended.

1. Download wkhtmltopdf (Windows x64) and copy `wkhtmltopdf.exe` to `third_party/wkhtmltopdf/wkhtmltopdf.exe`.
2. Open `cmd` in the project root and run:
```
build_windows.bat
```
3. Result: `dist/LetterGen/LetterGen.exe` (portable folder). You can zip the folder as a single distributable.

To make a single file exe, you may switch to `--onefile` in the spec, but bundling `wkhtmltopdf.exe` is typically simpler with the folder-based build.

### Acceptance Considerations
- App runs fully offline; no network calls.
- PDF and DOCX are generated from the same HTML template for consistent formatting.
- Batch of 500: On an average laptop with 6–8 workers, expect completion near a couple of minutes depending on template complexity and images.

### Security & Privacy
- No data leaves the machine.
- Temporary files are minimized; outputs go only to your chosen folder.

### License
For evaluation/sample purposes. Ensure compliance with `wkhtmltopdf` license when redistributing its binary.
# pdf-generator
# pdf-generator
