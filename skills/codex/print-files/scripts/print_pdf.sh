#!/bin/bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: print_pdf.sh --file /absolute/path/file.pdf [options]

Options:
  --printer NAME       CUPS printer queue; defaults to the system printer
  --copies N           Number of copies (default: 1)
  --paper VALUE        PageSize value (default: A4)
  --color VALUE        ColorModel value (default: RGB)
  --duplex VALUE       Duplex value (default: None)
  --title TEXT         Print job title; defaults to the PDF filename
  --wait-seconds N     Monitor for 0-60 seconds (default: 60)
  --expected-size-points WIDTHxHEIGHT
                       Expected PDF page size for an uncommon PageSize value
  --dry-run            Validate and show settings without submitting
  -h, --help           Show this help
EOF
}

die() {
  printf 'ERROR=%s\n' "$*" >&2
  exit 1
}

pdf=''
printer=''
copies='1'
paper='A4'
color='RGB'
duplex='None'
title=''
wait_seconds='60'
expected_size_points=''
dry_run='false'

while [ "$#" -gt 0 ]; do
  case "$1" in
    --file|--printer|--copies|--paper|--color|--duplex|--title|--wait-seconds|--expected-size-points)
      [ "$#" -ge 2 ] || die "missing value for $1"
      option="$1"
      value="$2"
      shift 2
      case "$option" in
        --file) pdf="$value" ;;
        --printer) printer="$value" ;;
        --copies) copies="$value" ;;
        --paper) paper="$value" ;;
        --color) color="$value" ;;
        --duplex) duplex="$value" ;;
        --title) title="$value" ;;
        --wait-seconds) wait_seconds="$value" ;;
        --expected-size-points) expected_size_points="$value" ;;
      esac
      ;;
    --dry-run)
      dry_run='true'
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[ -n "$pdf" ] || die '--file is required'
[[ "$pdf" = /* ]] || die '--file must be an absolute path'
[ -f "$pdf" ] || die "PDF not found: $pdf"
[ "$(file -b --mime-type "$pdf")" = 'application/pdf' ] || die "input is not a PDF: $pdf"
[[ "$copies" =~ ^[1-9][0-9]*$ ]] || die '--copies must be a positive integer'
[[ "$wait_seconds" =~ ^[0-9]+$ ]] || die '--wait-seconds must be an integer from 0 to 60'
[ "$wait_seconds" -le 60 ] || die '--wait-seconds cannot exceed 60'
[[ "$paper" =~ ^[A-Za-z0-9._-]+$ ]] || die 'unsafe or invalid --paper value'
[[ "$color" =~ ^[A-Za-z0-9._-]+$ ]] || die 'unsafe or invalid --color value'
[[ "$duplex" =~ ^[A-Za-z0-9._-]+$ ]] || die 'unsafe or invalid --duplex value'

command -v pdfinfo >/dev/null 2>&1 || die 'pdfinfo is required; load the PDF workspace dependencies first'

if [ -n "$expected_size_points" ]; then
  [[ "$expected_size_points" =~ ^[0-9]+([.][0-9]+)?x[0-9]+([.][0-9]+)?$ ]] || die '--expected-size-points must be WIDTHxHEIGHT'
  expected_width=${expected_size_points%x*}
  expected_height=${expected_size_points#*x}
else
  case "$paper" in
    A3|A3.Fullbleed) expected_width='841.890'; expected_height='1190.551' ;;
    A4|A4.Fullbleed) expected_width='595.276'; expected_height='841.890' ;;
    A5) expected_width='419.528'; expected_height='595.276' ;;
    A6|A6.Fullbleed) expected_width='297.638'; expected_height='419.528' ;;
    B5) expected_width='515.906'; expected_height='728.504' ;;
    B6) expected_width='362.835'; expected_height='515.906' ;;
    Letter|Letter.Fullbleed) expected_width='612'; expected_height='792' ;;
    Legal) expected_width='612'; expected_height='1008' ;;
    Executive) expected_width='522'; expected_height='756' ;;
    [0-9]*x[0-9]*mm)
      dimensions_mm=${paper%mm}
      width_mm=${dimensions_mm%x*}
      height_mm=${dimensions_mm#*x}
      expected_width=$(awk -v mm="$width_mm" 'BEGIN { printf "%.3f", mm * 72 / 25.4 }')
      expected_height=$(awk -v mm="$height_mm" 'BEGIN { printf "%.3f", mm * 72 / 25.4 }')
      ;;
    *) die "no page-dimension map for PageSize=$paper; pass --expected-size-points WIDTHxHEIGHT" ;;
  esac
fi

pdf_details=$(pdfinfo -f 1 -l 100000 "$pdf" 2>&1) || die "pdfinfo could not inspect: $pdf"
page_sizes=$(printf '%s\n' "$pdf_details" | awk '
  /^Page +[0-9]+ size:/ {
    for (i = 1; i <= NF; i++) {
      if ($i == "size:") {
        print $2, $(i + 1), $(i + 3)
        break
      }
    }
  }
')
[ -n "$page_sizes" ] || die 'pdfinfo returned no page dimensions'

size_mismatches=$(printf '%s\n' "$page_sizes" | awk -v ew="$expected_width" -v eh="$expected_height" '
  function abs(value) { return value < 0 ? -value : value }
  {
    portrait = abs($2 - ew) <= 2.5 && abs($3 - eh) <= 2.5
    landscape = abs($2 - eh) <= 2.5 && abs($3 - ew) <= 2.5
    if (!portrait && !landscape) {
      printf "page %s is %s x %s pt", $1, $2, $3
      if (!portrait && !landscape) printf "; expected %.3f x %.3f pt", ew, eh
      printf "\n"
    }
  }
')
[ -z "$size_mismatches" ] || die "PDF page size does not match PageSize=$paper: $size_mismatches"

if [ -z "$printer" ]; then
  default_output=$(lpstat -d 2>/dev/null) || die 'no system default printer'
  printer=$(printf '%s\n' "$default_output" | sed -E 's/^.*[:：][[:space:]]*//')
  [ -n "$printer" ] || die 'could not parse the system default printer'
fi

lpstat -p "$printer" >/dev/null 2>&1 || die "printer not found: $printer"
printer_options=$(lpoptions -p "$printer" 2>/dev/null) || die "could not read printer state: $printer"
case " $printer_options " in
  *' printer-is-accepting-jobs=true '*) ;;
  *) die "printer is not accepting jobs: $printer" ;;
esac

capabilities=$(lpoptions -p "$printer" -l 2>/dev/null) || die "could not read printer capabilities: $printer"

supports_value() {
  keyword="$1"
  requested="$2"
  line=$(printf '%s\n' "$capabilities" | grep -E "^${keyword}/" | head -n 1 || true)
  [ -n "$line" ] || return 1
  printf '%s\n' "$line" | grep -Eq "(^|[[:space:]*])${requested}([[:space:]]|$)"
}

supports_value 'PageSize' "$paper" || die "unsupported PageSize=$paper on $printer"
supports_value 'ColorModel' "$color" || die "unsupported ColorModel=$color on $printer"
supports_value 'Duplex' "$duplex" || die "unsupported Duplex=$duplex on $printer"

[ -n "$title" ] || title=$(basename "$pdf" .pdf)

printf 'PRINTER=%s\n' "$printer"
printf 'FILE=%s\n' "$pdf"
printf 'COPIES=%s\n' "$copies"
printf 'PAPER=%s\n' "$paper"
printf 'COLOR=%s\n' "$color"
printf 'DUPLEX=%s\n' "$duplex"
printf 'EXPECTED_SIZE_POINTS=%sx%s\n' "$expected_width" "$expected_height"

if [ "$dry_run" = 'true' ]; then
  printf 'STATUS=dry-run\n'
  exit 0
fi

set +e
job_output=$(lp -d "$printer" -n "$copies" -o "PageSize=$paper" -o "ColorModel=$color" -o "Duplex=$duplex" -t "$title" "$pdf" 2>&1)
lp_status=$?
set -e
printf '%s\n' "$job_output"
[ "$lp_status" -eq 0 ] || die "lp failed with exit code $lp_status"

job_id=$(printf '%s\n' "$job_output" | grep -Eo '[[:alnum:]_.-]+-[0-9]+' | tail -n 1 || true)
if [ -z "$job_id" ]; then
  printf 'STATUS=submitted-id-unknown\n'
  printf 'ERROR=lp succeeded but the request ID could not be parsed; do not resubmit\n' >&2
  exit 2
fi

printf 'JOB_ID=%s\n' "$job_id"
elapsed=0
while [ "$elapsed" -lt "$wait_seconds" ]; do
  active=$(lpstat -W not-completed -o "$printer" 2>/dev/null || true)
  if ! printf '%s\n' "$active" | grep -Fq "$job_id"; then
    break
  fi
  sleep 2
  elapsed=$((elapsed + 2))
done

active=$(lpstat -W not-completed -o "$printer" 2>/dev/null || true)
if printf '%s\n' "$active" | grep -Fq "$job_id"; then
  printf 'STATUS=still-active\n'
  lpstat -p "$printer" -l 2>/dev/null || true
  exit 0
fi

completed=$(lpstat -W completed -o "$printer" 2>/dev/null || true)
if printf '%s\n' "$completed" | grep -Fq "$job_id"; then
  printf 'STATUS=completed\n'
else
  printf 'STATUS=left-queue\n'
fi
lpstat -p "$printer" -l 2>/dev/null || true
