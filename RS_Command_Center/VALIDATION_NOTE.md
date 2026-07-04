# VALIDATION NOTE — RS_Command_Center.xlsx

Built 04/07/2026. Dummy data only — no real client information anywhere in the file.

## What was verified here (254 automated checks, all passing — `post_check.py`)

- **Expected values were locked in first.** Every Dashboard number was hand-computed from the dummy dataset and written to `rs_checks.json` *before* the build script existed. An independent script (`post_check.py`, written separately from the build script) recomputes all of them in pure Python and agrees exactly: open pipeline 8 leads / AED 257,000.00 / weighted AED 110,110.00, win rate 50.0%, total outstanding AED 81,900.00, per-line and per-invoice figures, job margins.
- **Every Settings reference in every formula was label-checked** against the cell it points at (Won = Settings!G14, Lost = G15, stage lookup G10:H15, business lines C10:C13, sources E10:E15, job statuses J10:J11). No off-by-one references.
- **Formula logic parsed and checked in the written file:** Overdue beats Partial (and an invoice due *today* is not overdue); divide-by-zero guards on win rate, margin % and the bar chart's REPT scale; every formula column blank-guarded so empty rows show nothing, all the way to the last row (Pipeline row 304, Jobs/Invoices row 204).
- **Structure:** 6 tabs in order, gridlines off, Arial throughout, navy/gold/beige/cream house palette, merged title banners, nav links row on every sheet, freeze panes A5 + filter dropdowns on Pipeline/Jobs/Invoices, DD/MM/YYYY dates, `#,##0.00` money, dropdowns fed from Settings, all sheets protected with **no password** and only the blue input cells unlocked, red/green conditional formatting on invoices and the two red-alert dashboard tiles. No macros (.xlsx).
- **Independent audit pass:** a fresh-eyes review of the build script and formulas found one styling defect (computed columns falling back to Calibri) — fixed and now regression-checked — and confirmed the Settings wiring, guards and status ordering.

## What could NOT be verified here

- This environment has no Excel, so **formulas were never live-recalculated**. The formula strings, references and cell values are verified; the actual calculation happens the first time Excel opens the file. `post_check.py` automatically compares the recalculated Dashboard values against `rs_checks.json` once the file has been opened and saved by real Excel.
- Visual rendering (column widths vs. real font metrics, chart appearance) — checked structurally, not by eye.

## Two small design decisions (both on purpose)

- The brief's "Invoiced this month" and "Collected this month" tiles need dates the brief's Invoices column list didn't include, so the Invoices tab has two extra columns: **Invoice date** and **Paid date**.
- "Jobs won this month" counts jobs by their **Start date** on the Jobs tab (the Pipeline has no won-date column); the win-rate tile is all-time Won ÷ (Won + Lost).

## Instruction for Dan's local Claude

> "Validate `Desktop\RS_Command_Center\RS_Command_Center.xlsx` via Excel COM: open, full recalc, zero error cells anywhere, compare Dashboard values against rs_checks.json via post_check.py, Excel-native save. Then help me replace the dummy rows with my real leads, jobs and invoices."
