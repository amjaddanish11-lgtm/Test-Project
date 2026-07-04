# BUILD SPEC — build_cockpit.py (RS_Command_Center.xlsx)

Authoritative spec for the build script. Implement EXACTLY. If anything is ambiguous, STOP and report — do not improvise. The script must be a single re-runnable file `build_cockpit.py` (openpyxl, .xlsx, NO macros) that writes `RS_Command_Center.xlsx` into its own directory.

**Dummy data source:** read `rs_checks.json` (same directory) → `dataset` key. Do NOT hard-code the rows; load them. Dates in the JSON are ISO; write them to cells as Python `datetime.date` objects with number format `DD/MM/YYYY`.

## 0. Global house style (every sheet)

- Font Arial everywhere (set explicitly on every styled cell; also set workbook default via a named style or by styling all touched cells).
- `ws.sheet_view.showGridLines = False` on EVERY sheet.
- Column A width 3 on every sheet (gutter). Content starts in column B.
- Palette (ARGB): NAVY `FF1F2A44`, GOLD `FFC9A227`, BEIGE `FFE8E2D4`, CREAM `FFF4F1EA`, BLUE_INPUT font `FF0000FF`, GRAY `FF666666`, RED `FFCC0000`, GREEN `FF38761D`, AMBER `FFB45309`, WHITE `FFFFFFFF`.
- **Row 1 = nav row** on every sheet: labels in every other column — B1 "Start", D1 "Dashboard", F1 "Pipeline", H1 "Jobs", J1 "Invoices", L1 "Settings". Each is a hyperlink OBJECT (not a formula): `cell.hyperlink = Hyperlink(ref=cell.coordinate, location="'<Sheet Name>'!A1")` — or simply set `cell.hyperlink = "#'<Sheet Name>'!A1"`? NO — use `from openpyxl.worksheet.hyperlink import Hyperlink` with `location="'Start Here'!A1"` and empty target: assign via `ws['B1'].hyperlink = Hyperlink(ref='B1', location="'Start Here'!A1")`. Font Arial 8; the label pointing at the CURRENT sheet navy bold `FF1F2A44`, the others gray `FF8A8578`. Row 1 height 15.
- **Row 2 = title banner**: navy fill, white bold, MERGED full content width (per-sheet width below). Title string starts with 2 leading spaces. Font size 14 (16 on Start Here). Row height 24.
- **Row 3 = subtitle ribbon**: gold fill `FFC9A227`, navy bold 9, merged same width as banner, text starts with 2 leading spaces. Row height 16.
- Input cells: CREAM fill + BLUE font. Formula/locked display cells: no fill (or as specified), navy/dark text `FF222222`.
- Number formats: money `#,##0.00` · percent `0.0%` · dates `DD/MM/YYYY` · counts `0`.
- Every data-row formula wrapped in an IF-blank guard so empty rows show "".
- Sheet protection ON every sheet, NO password: `ws.protection.sheet = True`, `ws.protection.autoFilter = False` (so filters stay usable), `ws.protection.sort = False`. Input cells get `protection=Protection(locked=False)`; everything else stays locked.
- DataValidation `formula1` must NOT start with `=` (e.g. `"Settings!$G$10:$G$15"`), `allow_blank=True`, `showDropDown` left default.
- Freeze panes `A5` + `ws.auto_filter.ref` on the three data tabs (Pipeline, Jobs, Invoices) as specified below. No freeze/filter on Start Here, Dashboard, Settings.

Sheet order: `Start Here`, `Dashboard`, `Pipeline`, `Jobs`, `Invoices`, `Settings` (exact names).

## 1. Settings (build this sheet's content first conceptually — everything references it)

Banner/ribbon merged B2:K2, B3:K3. Title "  SETTINGS". Ribbon "  Rename lists here — dropdowns and formulas follow automatically."
- B5 label "Currency label" (gray 9), C5 input `AED`.
- B6 label "VAT note" (gray 9), C6 input `VAT 5% — prices exclude VAT unless stated`.
- C9 header "Business lines" (beige fill, navy bold 10). C10:C13 inputs: Signage, Neon, Fitout, Website.
- E9 header "Lead sources" (beige). E10:E15 inputs: Google Ads, Instagram, Referral, Walk-in, Existing client, Designer partner.
- G9 header "Stage" (beige), H9 header "Probability" (beige). G10:G15 inputs: New, Contacted, Quote sent, Negotiating, Won, Lost. H10:H15 inputs: 0.10, 0.25, 0.40, 0.60, 1.00, 0.00 — format `0.0%`. **Won is G14, Lost is G15** — formulas below depend on these exact rows.
- J9 header "Job status" (beige). J10:J11 inputs: In progress, Done.
- B17 gray hint (Arial 8 gray): "Stages Won and Lost count as closed. A lead in any other stage is open pipeline."
- Unlocked cells: C5, C6, C10:C13, E10:E15, G10:H15, J10:J11. All styled cream+blue.
- Column widths: B 18, C 22, D 3, E 22, F 3, G 16, H 12, I 3, J 14, K 10.

## 2. Start Here

Banner B2:K2 "  RELIABLE SOURCES — COMMAND CENTER" (white bold 16). Ribbon B3:K3 "  Who to chase today, what work is live, who owes you money — in under a minute."
Plain-English content, Arial 10 dark `FF222222`, labels bold navy where headed. Lay out one block per row group (single cells, no merges needed below row 3; keep lines short enough not to clip — put each sentence in its own row in column B, rows 5 onward):

- B5 bold navy 12: "The 5-Minute Morning Routine"
- B7: "1.  Open the Dashboard tab and read the tiles — they update themselves."
- B8: "2.  Check 'Follow-ups due' — call or WhatsApp each CALL TODAY lead in the Pipeline tab, update its stage, and set the next follow-up date."
- B9: "3.  Glance at overdue invoices on the Dashboard — chase the oldest one first."
- B10: "4.  New enquiry since yesterday? Log it in the Pipeline tab — one row, 30 seconds."
- B12 bold navy 12: "What each tab does"
- B13: "Dashboard — your morning read. All formulas, nothing to type."
- B14: "Pipeline — every enquiry and quote. Blue cells are yours to type; grey ones fill themselves."
- B15: "Jobs — won work only, with margin worked out for you."
- B16: "Invoices — what you've billed, what's been paid, what's overdue."
- B17: "Settings — rename business lines, sources and stages here without breaking anything."
- B19 bold RED 11: "The one rule: a lead without a next follow-up date is a lead you've decided to lose."
- B21 gray 8: "Blue writing on cream = type here. Everything else is locked so it can't break. Dummy data is loaded — replace it with your real pipeline."
Column B width 110. Protection on, nothing unlocked.

## 3. Pipeline

Banner B2:N2 "  PIPELINE — every enquiry lives here". Ribbon B3:N3 "  Blue cells are yours. Probability, weighted value and the CALL TODAY flag fill themselves."
Header row 4 (beige fill, navy bold 9, thin bottom border navy): B4 "Date in", C4 "Client", D4 "Contact", E4 "Business line", F4 "Source", G4 "What they want", H4 "Est. value AED", I4 "Stage", J4 "Probability %", K4 "Weighted AED", L4 "Next follow-up", M4 "Status flag", N4 "Notes".
Data rows 5–304 (300 rows). Load the 10 dummy pipeline rows from JSON into rows 5–14 (order as in JSON).

Formulas in ALL 300 rows (r = 5..304):
- J{r}: `=IF($I{r}="","",IFERROR(VLOOKUP($I{r},Settings!$G$10:$H$15,2,FALSE),""))` — format `0.0%`
- K{r}: `=IF(OR($H{r}="",$J{r}=""),"",$H{r}*$J{r})` — money format
- M{r}: `=IF(OR($I{r}="",$L{r}=""),"",IF(AND($L{r}<=TODAY(),$I{r}<>Settings!$G$14,$I{r}<>Settings!$G$15),"CALL TODAY",""))` — font Arial 9 bold RED (static red font is fine; the cell only ever shows CALL TODAY or blank)

Input columns (unlocked, cream+blue): B, C, D, E, F, G, H, I, L, N rows 5–304. B and L date format; H money.
Dropdowns (DataValidation, formula1 WITHOUT leading =): E5:E304 → `Settings!$C$10:$C$13`; F5:F304 → `Settings!$E$10:$E$15`; I5:I304 → `Settings!$G$10:$G$15`.
Freeze `A5`. `auto_filter.ref = "B4:N304"`.
Column widths: B 11, C 24, D 14, E 13, F 14, G 32, H 14, I 12, J 12, K 13, L 13, M 12, N 28.

## 4. Jobs

Banner B2:L2 "  JOBS — won work only". Ribbon B3:L3 "  Job ref and margin fill themselves. Type the rest."
Header row 4 (beige): B4 "Job ref", C4 "Client", D4 "Business line", E4 "Value AED", F4 "Est. cost AED", G4 "Margin AED", H4 "Margin %", I4 "Status", J4 "Start date", K4 "Handover date", L4 "Notes".
Data rows 5–204 (200 rows). Load the 5 dummy jobs into rows 5–9 (client, line, value, est_cost, status, start, handover, notes from JSON — do NOT write the ref, it's a formula).

Formulas in all 200 rows:
- B{r}: `=IF($C{r}="","","RS-"&TEXT(ROW()-4,"000"))` — navy bold 9
- G{r}: `=IF(OR($E{r}="",$F{r}=""),"",$E{r}-$F{r})` — money
- H{r}: `=IF(OR($E{r}="",$E{r}=0,$G{r}=""),"",$G{r}/$E{r})` — `0.0%`

Input (cream+blue, unlocked): C, D, E, F, I, J, K, L rows 5–204. J, K date format; E, F money.
Dropdowns: D5:D204 → `Settings!$C$10:$C$13`; I5:I204 → `Settings!$J$10:$J$11`.
Freeze `A5`. `auto_filter.ref = "B4:L204"`.
Widths: B 9, C 24, D 13, E 13, F 13, G 12, H 10, I 12, J 12, K 14, L 30.

## 5. Invoices

Banner B2:M2 "  INVOICES — who owes you money". Ribbon B3:M3 "  Balance, status and days overdue fill themselves. Overdue rows turn red, paid rows green."
Header row 4 (beige): B4 "Invoice #", C4 "Client", D4 "Job ref", E4 "Invoice date", F4 "Amount AED", G4 "Paid AED", H4 "Paid date", I4 "Balance AED", J4 "Due date", K4 "Status", L4 "Days overdue", M4 "Notes".
Data rows 5–204. Load the 6 dummy invoices into rows 5–10.

Formulas in all 200 rows:
- I{r}: `=IF($F{r}="","",$F{r}-N($G{r}))` — money
- K{r}: `=IF($F{r}="","",IF($I{r}<=0,"Paid",IF(AND($J{r}<>"",TODAY()>$J{r}),"Overdue",IF(N($G{r})>0,"Partial","Upcoming"))))` — note Overdue beats Partial by ordering
- L{r}: `=IF(OR($F{r}="",$I{r}<=0,$J{r}=""),"",IF(TODAY()>$J{r},TODAY()-$J{r},""))` — format `0`

Input (cream+blue, unlocked): B, C, D, E, F, G, H, J, M rows 5–204. E, H, J dates; F, G money.
No dropdowns on this sheet.
Conditional formatting over `B5:M204` (formula rules, stopIfTrue not needed):
1. `=$K5="Overdue"` → font RED `FFCC0000` bold.
2. `=$K5="Paid"` → font GREEN `FF38761D`.
(Apply in that order.)
Freeze `A5`. `auto_filter.ref = "B4:M204"`.
Widths: B 14, C 24, D 9, E 12, F 13, G 13, H 12, I 13, J 12, K 11, L 12, M 28.

## 6. Dashboard

Banner B2:M2 "  DASHBOARD — read it, don't type in it". Ribbon B3:M3 "  Updates itself from Pipeline, Jobs and Invoices. Amounts in AED."

**Tiles.** Pattern: label cell (Arial 9 gray `FF666666`, cream fill) directly LEFT of value cell (Arial 12 bold navy `FF1F2A44`, cream fill `FFF4F1EA`). Both cells in the pair get cream fill and a thin border (all four sides, color `FFD9D2C0`). Label in the given label cell; value formula in the given value cell. Row heights 20 for tile rows.

| Label cell | Value cell | Label text | Formula in value cell | Format |
|---|---|---|---|---|
| B5 | C5 | Follow-ups due today / overdue | `=COUNTIF(Pipeline!$M$5:$M$304,"CALL TODAY")` | `0` |
| B7 | C7 | Open pipeline (count) | `=COUNTIFS(Pipeline!$I$5:$I$304,"<>",Pipeline!$I$5:$I$304,"<>"&Settings!$G$14,Pipeline!$I$5:$I$304,"<>"&Settings!$G$15)` | `0` |
| E7 | F7 | Open pipeline AED | `=SUMIFS(Pipeline!$H$5:$H$304,Pipeline!$I$5:$I$304,"<>",Pipeline!$I$5:$I$304,"<>"&Settings!$G$14,Pipeline!$I$5:$I$304,"<>"&Settings!$G$15)` | money |
| H7 | I7 | Weighted pipeline AED | `=SUMIFS(Pipeline!$K$5:$K$304,Pipeline!$I$5:$I$304,"<>",Pipeline!$I$5:$I$304,"<>"&Settings!$G$14,Pipeline!$I$5:$I$304,"<>"&Settings!$G$15)` | money |
| B9 | C9 | New leads this month | `=COUNTIFS(Pipeline!$B$5:$B$304,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Pipeline!$B$5:$B$304,"<"&EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),1))` | `0` |
| E9 | F9 | Jobs won this month (count) | `=COUNTIFS(Jobs!$J$5:$J$204,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Jobs!$J$5:$J$204,"<"&EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),1))` | `0` |
| H9 | I9 | Jobs won this month AED | `=SUMIFS(Jobs!$E$5:$E$204,Jobs!$J$5:$J$204,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Jobs!$J$5:$J$204,"<"&EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),1))` | money |
| B11 | C11 | Win rate (won ÷ closed) | `=IF(COUNTIF(Pipeline!$I$5:$I$304,Settings!$G$14)+COUNTIF(Pipeline!$I$5:$I$304,Settings!$G$15)=0,0,COUNTIF(Pipeline!$I$5:$I$304,Settings!$G$14)/(COUNTIF(Pipeline!$I$5:$I$304,Settings!$G$14)+COUNTIF(Pipeline!$I$5:$I$304,Settings!$G$15)))` | `0.0%` |
| E11 | F11 | Invoiced this month AED | `=SUMIFS(Invoices!$F$5:$F$204,Invoices!$E$5:$E$204,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Invoices!$E$5:$E$204,"<"&EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),1))` | money |
| H11 | I11 | Collected this month AED | `=SUMIFS(Invoices!$G$5:$G$204,Invoices!$H$5:$H$204,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Invoices!$H$5:$H$204,"<"&EDATE(DATE(YEAR(TODAY()),MONTH(TODAY()),1),1))` | money |
| B13 | C13 | Total outstanding AED | `=SUM(Invoices!$I$5:$I$204)` | money |
| E13 | F13 | Overdue AED | `=SUMIFS(Invoices!$I$5:$I$204,Invoices!$K$5:$K$204,"Overdue")` | money |

Conditional formatting: C5 → `=$C$5>0` font RED bold. F13 → `=$F$13>0` font RED bold. (cellIs/expression rule, range exactly that one cell.)

**Per-line table.** Row 15: gold section bar merged B15:M15, navy bold 9, text "  PIPELINE BY BUSINESS LINE". Row 16 headers (beige): B16 "Business line", C16 "Open pipeline AED", D16 "Won this year AED", E16 "Open pipeline".
Rows 17–20 (r = 17..20 map to Settings rows 10..13, s = r - 7):
- B{r}: `=IF(Settings!$C${s}="","",Settings!$C${s})` — navy bold 10
- C{r}: `=IF($B{r}="","",SUMIFS(Pipeline!$H$5:$H$304,Pipeline!$E$5:$E$304,$B{r},Pipeline!$I$5:$I$304,"<>",Pipeline!$I$5:$I$304,"<>"&Settings!$G$14,Pipeline!$I$5:$I$304,"<>"&Settings!$G$15))` — money
- D{r}: `=IF($B{r}="","",SUMIFS(Jobs!$E$5:$E$204,Jobs!$D$5:$D$204,$B{r},Jobs!$J$5:$J$204,">="&DATE(YEAR(TODAY()),1,1),Jobs!$J$5:$J$204,"<"&DATE(YEAR(TODAY())+1,1,1)))` — money
- E{r}: `=IF(OR($B{r}="",MAX($C$17:$C$20)=0),"",REPT("█",ROUND($C{r}/MAX($C$17:$C$20)*20,0)))` — font Arial 10, GOLD color `FFC9A227`

**Chart.** BarChart (`type="bar"`? NO — vertical columns: `bar_chart.type = "col"`), anchored at `G16`, series values `Dashboard!$C$17:$C$20`, categories `Dashboard!$B$17:$B$20`, title "Pipeline value by business line", width 15, height 7.5, legend removed (`chart.legend = None`), series solid fill brass `C9A227` (openpyxl: `series.graphicalProperties.solidFill = "C9A227"`), gap width default.

Row 22: B22 gray 8 hint: "Red tile means pick up the phone. The chart and this table follow whatever names you give your business lines in Settings."
No unlocked cells on Dashboard. No freeze/filter.
Widths: B 26, C 15, D 3→ NO: widths: B 26, C 15, E 26, F 15, H 26, I 15; D and G width 2; J–M width 10. (Column E holds both tile labels and REPT bars — 26 wide is right.)

## 7. Save

`wb.save("RS_Command_Center.xlsx")` in the script's directory (use `pathlib.Path(__file__).parent`). Print a one-line summary: sheets written, rows loaded. Exit non-zero on any exception.
