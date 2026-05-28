#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  render_docx.sh INPUT.docx OUTPUT_DIR

Renders a DOCX to PDF with LibreOffice headless, then renders PDF pages to PNG
with Poppler pdftoppm.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 2 ]]; then
  usage >&2
  exit 2
fi

input_docx=$1
output_dir=$2

if [[ ! -f "$input_docx" ]]; then
  echo "Input DOCX not found: $input_docx" >&2
  exit 1
fi

case "$input_docx" in
  *.docx|*.DOCX) ;;
  *)
    echo "Input must be a .docx file: $input_docx" >&2
    exit 1
    ;;
esac

find_soffice() {
  if command -v soffice >/dev/null 2>&1; then
    command -v soffice
    return 0
  fi
  if command -v libreoffice >/dev/null 2>&1; then
    command -v libreoffice
    return 0
  fi
  if [[ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ]]; then
    printf '%s\n' "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    return 0
  fi
  return 1
}

soffice_bin=$(find_soffice || true)
if [[ -z "$soffice_bin" ]]; then
  echo "LibreOffice soffice not found. Install LibreOffice or add soffice to PATH." >&2
  exit 127
fi

if ! command -v pdftoppm >/dev/null 2>&1; then
  echo "pdftoppm not found. Install Poppler." >&2
  exit 127
fi

mkdir -p "$output_dir/pdf" "$output_dir/png"

input_abs=$(cd "$(dirname "$input_docx")" && pwd)/$(basename "$input_docx")
stem=$(basename "$input_docx")
stem=${stem%.*}

"$soffice_bin" \
  --headless \
  --convert-to pdf \
  --outdir "$output_dir/pdf" \
  "$input_abs" >/dev/null

pdf_path="$output_dir/pdf/$stem.pdf"
if [[ ! -f "$pdf_path" ]]; then
  echo "LibreOffice did not produce expected PDF: $pdf_path" >&2
  exit 1
fi

pdftoppm -png -r 150 "$pdf_path" "$output_dir/png/${stem}-page" >/dev/null

if ! compgen -G "$output_dir/png/${stem}-page-*.png" >/dev/null; then
  echo "pdftoppm did not produce PNG pages in: $output_dir/png" >&2
  exit 1
fi

echo "PDF: $pdf_path"
echo "PNG: $output_dir/png/${stem}-page-*.png"

