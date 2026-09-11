---
name: print-files
compat: [codex]
description: Safely print local files through a physical macOS printer using CUPS, with print-ready PDF conversion, page-size and visual validation, printer capability checks, one-time job submission, and completion tracking. Use when the user asks to print, 列印, 印出, or send HTML, PDF, DOCX, images, spreadsheets, slides, or other local content to a printer, or asks to inspect printer status, queues, media, color, duplex, or completed jobs.
---

# Print Files

Turn the requested source into a visually verified PDF, submit it exactly once, and track the resulting CUPS job.

## Safety contract

- Treat an explicit request to print as authorization for one physical copy using safe defaults: the default printer, A4, color, and one-sided output.
- Follow explicit printer, paper, color, duplex, orientation, or copy-count instructions instead of the defaults.
- Ask only when no usable default printer exists or a missing choice would materially change the result.
- Never submit a second job because monitoring or status parsing failed. Once `lp` returns a request ID, investigate that ID instead.
- Never submit a PDF whose page dimensions materially differ from the selected paper size without first resolving the scaling policy.
- Preserve the source file. Delete only intermediates created during this task, using exact paths.

## Workflow

1. Resolve the exact source path and confirm the file exists.
2. Inspect printers before authoring or printing:

   ```bash
   lpstat -d
   lpstat -p
   lpstat -a
   lpoptions
   ```

   Stop if the chosen printer is unavailable, not accepting jobs, out of paper, or reporting an actionable error. A busy but accepting printer may be queued with a brief notice.

3. Produce a print-ready PDF without modifying the source:
   - PDF: use it directly only when its pages already match the requested paper size. Otherwise create a new target-size PDF that centers each source page and scales it proportionally inside explicit margins. Ask before choosing between actual size, fit, fill/crop, or poster tiling when the choice would materially change the output.
   - HTML: load the `pdf` skill, print through Chromium/Chrome so `@page` and print CSS apply, then follow that skill's PDF validation workflow.
   - DOCX, spreadsheet, or slides: load the matching document skill and export to PDF using the application or its supported renderer.
   - Images: create a PDF that fits each image inside the requested paper without cropping unless the user explicitly asks for a crop.
   - Unsupported source: stop and explain what conversion capability is missing; do not hand the unknown format directly to CUPS.

4. Validate the latest PDF:
   - Confirm page count and physical dimensions with `pdfinfo`.
   - Render pages with `pdftoppm` and inspect them for clipping, overlaps, missing glyphs, unintended blank pages, and wrong orientation.
   - Use A4 unless the user specifies another paper size or the source clearly requires a different supported size.
   - Require the final PDF page dimensions to match the selected paper. Do not rely on implicit CUPS scaling.

5. Inspect the selected printer's supported options:

   ```bash
   lpoptions -p "PRINTER" -l
   ```

   Map requested settings to the printer's exact `PageSize`, `ColorModel`, and `Duplex` values. Do not silently substitute unsupported settings.

6. Submit and monitor the verified PDF with the bundled script:

   ```bash
   bash scripts/print_pdf.sh \
     --file "/absolute/path/to/verified.pdf" \
     --paper A4 \
     --color RGB \
     --duplex None \
     --copies 1
   ```

   Add `--printer NAME` only when not using the system default. Use `--dry-run` while testing the script or settings; it never submits a job.

7. Report the printer, paper, color mode, sidedness, copy count, request ID, and the strongest confirmed status:
   - `completed`: CUPS moved the job into completed history.
   - `still-active`: the job remains queued or printing; continue monitoring the same ID.
   - `left-queue`: the job disappeared but was not found in completed history; report the uncertainty and inspect printer state without resubmitting.

## Script guarantees

`scripts/print_pdf.sh` accepts only absolute PDF paths, validates all option values before calling `lp`, limits its internal wait to 60 seconds, emits machine-readable `JOB_ID=` and `STATUS=` lines, and never retries submission.
It also requires `pdfinfo` and rejects PDFs whose page dimensions do not match the selected paper. For an uncommon printer paper name, pass `--expected-size-points WIDTHxHEIGHT` only after independently confirming that paper's physical dimensions.
