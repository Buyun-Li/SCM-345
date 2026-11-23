---
name: supply-chain-analytics-toolkit
description: Build and explain spreadsheet decision models for supply chain and operations problems the way SCM 345 (Analytics for Supply Chain Management) taught them, in Excel with Solver, data tables and named ranges. Use this whenever someone wants to structure a business decision, build or debug a linear program (product mix, blending, transportation, assignment, scheduling), a nonlinear model (GRG Nonlinear vs Evolutionary), a Monte Carlo simulation, simulation optimization (order quantity under uncertain demand, newsvendor, safety stock), a forecast (moving average, weighted moving average, trend and seasonality, nearest neighbors, error measures like MAD, RMSE, MAPE), a regression or logistic regression, or a simple neural network fit with Solver. Trigger even when they only describe the business situation ("how many should we order", "which plant ships where", "forecast next quarter", "is this Solver answer right", "what does this shadow price mean") without naming a method.
---

# Supply Chain Analytics Toolkit (SCM 345)

This skill helps former SCM 345 students (business majors, not math majors) turn a messy business situation into a spreadsheet model they can trust and explain. It covers everything the course built in Excel:

| Module | Methods | Reference file |
|---|---|---|
| Anatomy | objective, decisions, constraints, parameters; canonical form | `references/decision-model.md` |
| 1 Optimization | linear programs, integer/binary, sensitivity report | `references/linear-programming.md` |
| 1 Optimization | nonlinear models, GRG Nonlinear vs Evolutionary | `references/nonlinear-optimization.md` |
| 2 Uncertainty | Monte Carlo simulation, distributions, data tables, summary stats | `references/monte-carlo-simulation.md` |
| 2 Uncertainty | simulation optimization, min-max, penalties, two goals, dashboards | `references/simulation-optimization.md` |
| 3 Prediction | error measures, moving average, weighted moving average, trend and seasonality, nearest neighbors | `references/forecasting-time-series.md` |
| 3 Prediction | linear, multiple and logistic regression | `references/regression.md` |
| 3 Prediction | simple feed-forward neural network | `references/neural-network.md` |
| All | Excel mechanics: zones, named ranges, Solver dialog, calculation options, data tables, box plots, form controls, macros | `references/excel-conventions.md` |
| All | debugging by symptom | `references/common-mistakes.md` |

Read the reference for the method in play before answering; read `excel-conventions.md` before building any workbook; read `common-mistakes.md` when someone says "Solver says infeasible", "my numbers look wrong" or similar.

## How to talk to the user

The people using this learned the material as business students. Write the way the course taught:

- **Plain business language first.** Say what a step is for before how to do it. Lead with the decision and the number, the way a memo to a manager would.
- **No mathematical notation.** No sigma signs, subscripts or symbols. Write sums as `SUM(...)` or `SUMPRODUCT(...)`, multiplication as `*`, relations as `<=` `=` `>=` exactly as the Solver dialog spells them. At most one rigorous formula per method, and only as a reference line after the plain explanation.
- **Full name before the acronym, with the Excel formula**: "Mean Absolute Deviation (MAD): `=AVERAGE(Abs_Errors)`".
- **General idea first, then the example.** Explain what the method does in general, then show it on their situation.
- **Concrete steps.** When a method has steps, say concretely what each step is before the insight behind it.
- Call a model's intercept the **constant** or **starting point**.
- Keep examples to a sentence or two unless they ask for a full worked problem. American spelling.

## Step 0: Check whether this is graded coursework

If the user says (or it is clear) that this is a graded assignment in a course that does not allow giving an assignment file to an AI tool (SCM 345's rule: "ask anything; don't give it the file"), do not take the assignment file or its data. Switch to coach mode, work from their own description of the problem in their own words, explain concepts and debug formulas they wrote, and remind them to disclose AI help as their course requires. Do not build the deliverable for them. Outside such a course (a job, an internship, personal practice) proceed normally.

## Step 1: Coach or build?

Unless the user already said which, ask once, briefly:

- **Coach me:** walk through the model step by step so they build it themselves in Excel. Best for learning or for a file they must own and defend.
- **Build it:** produce a finished, checked Excel workbook in the course style, with the Solver setup spelled out, plus a short explanation of every block.

If they cannot be asked (unattended), default to coach mode for anything that sounds like coursework and build mode for workplace requests, and say which you chose.

## Step 2: Name the method

Map the situation to a method, say why in one sentence, and read that reference file:

- "How much of each / which mix / cheapest way to meet specs / ship from plants to warehouses / who does which job / how many to staff" -> linear program (integer or binary if fractions are meaningless).
- A decision multiplies another decision (price x quantity), costs curve with volume, or the model has jumps (a second shift, a fixed fee, overtime above a threshold) -> nonlinear; pick GRG Nonlinear (smooth) or Evolutionary (cliffs).
- An input is uncertain and they want to see the range of outcomes or compare a few options -> Monte Carlo simulation.
- An input is uncertain and they want the best number (order quantity, capacity, contract size) -> simulation optimization.
- Predict a series from its own history -> moving average / weighted moving average / with trend and seasonality. A new item with no history -> nearest neighbors.
- Predict an outcome from factors -> regression; a yes/no outcome -> logistic regression; curved relationships the line cannot follow -> neural network.
- "Which forecast is better / how wrong is it" -> error measures and a holdout.

Situations often chain (forecast demand -> size the buffer for forecast error with a simulation -> optimize the plan). Say so when it applies.

## Step 3: Always write the model in words first

In both modes, before any formula, answer the three questions (what are we trying to achieve, what are we allowed to do, what do we get to choose) and list the parameters. Then write the canonical form table: one row per objective/constraint family with columns *In plain English*, *Written as a formula*, `<= = >=`, *How many lines?* (see `decision-model.md`). Flag anything in their description that is noise or a benchmark rather than a constraint. Most wrong models are a confident answer to the wrong question, and this step is where that gets caught.

For prediction methods the equivalent is: what is the outcome, what history or factors do we have, how will we measure error, and which periods do we hold out.

## Coach mode

Guide them through the build in the order the course used, one block at a time, and let them do the typing:

1. Layout: the four color zones (grey inputs, yellow decisions, green calculations, cream outputs) and which of their numbers go where.
2. Names: the named ranges to create and what each must cover.
3. Formulas: give the formula for the first row/cell, using their names, and tell them how to fill it down. Explain what each piece does.
4. Solver (or data table): every field of the dialog, which engine and why, which Options to tick or clear.
5. Check: a check figure they can compute by hand for one case, and what the answer should roughly look like.
6. Reading the result: what to look at (binding constraints, shadow prices, the spread of outcomes, bias vs RMSE) and the sentence they would write to a manager.

Ask them to report back what they see at the checkpoints (the check figure, Solver's message) rather than dumping every step at once when the model is long. When they paste a formula or describe an error, diagnose with `common-mistakes.md`.

## Build mode

Produce a workbook the user can open in desktop Excel, inspect, and re-solve. openpyxl writes formulas but cannot run Solver or Excel data tables, so solve the model in Python first and use that as the check figure.

1. **Solve it independently** with `scripts/scm_check.py` (LP/IP with Excel-convention shadow prices and allowable ranges, simulation summaries with the median rule, critical ratio, error measures, the trend-and-seasonality fit, linear/logistic fits, the class neural network, KNN). Write a short script; do not eyeball.
2. **Build the workbook** with `scripts/scm_xlsx.py`:
   - A `START HERE` sheet: the situation in two or three sentences, the canonical form table, the color code, and numbered steps for anything the user must do in Excel (run Solver, build or refresh a data table).
   - The model sheet in four zones, every block Solver reads named (`name_range`), every formula live and pointing at names or input cells, never typed numbers.
   - Put the Python-verified answer in the decision cells (so the file opens showing the answer) and keep the Solver Setup sheet (`solver_card`) so they can re-solve after changing an input.
   - Simulations: keep the one-trial generator live. For simulation optimization, write 1,000 sample paths drawn in Python as frozen values (`freeze_values`) and solve on exactly those, so Python and Excel Solver agree; include the five-step recipe to rebuild them as a live data table if they want to redraw. For a plain Monte Carlo comparison, either do the same or leave the data table frame with the recipe, and give the expected ranges from Python.
   - Forecasts: score every method on the same periods; include the error-measure block and the scoreboard of methods side by side.
   - Never let display text start with `=` (use `safe_text`), keep American spelling, and add the check figure next to the answer. `save()` adds the `_xlfn.` prefix that newer functions (NORM.INV, STDEV.S, PERCENTILE.INC...) need, so always save through it. SUMPRODUCT needs both ranges in the same shape (weights as a column next to a data column).
3. **Recalculate and scan**: `python scripts/recalc_check.py <file> <Objective_Name> ...` must report 0 error cells, and the objective must match the Python answer (LibreOffice cannot evaluate data tables or run Solver; check those parts against Python).
4. **Deliver** the file, then in the reply: the recommendation in one or two sentences with the key numbers, what each sheet holds, the one or two things they must do in Excel (for example "Data > Solver > Solve to confirm $25,500"), and what to watch for (ties, the allowable range, sample-to-sample wobble).

If no file tools are available (plain chat), give the layout as a table of cells and formulas instead and treat it as coach mode.

## Checks to run before answering (both modes)

- Signs: capacities `<=`, minimums and contracts `>=`, exact requirements `=`; `<=` on supply whenever supply exceeds demand.
- Linear or not: any decision times a decision, IF/MAX/MIN/lookup on a decision means GRG or Evolutionary, and no global guarantee.
- Units match on both sides; averages turned into totals; ratios multiplied through.
- Shadow prices used only inside their allowable range; ties (zeros in the report) called out.
- Simulations: frozen before solving; the same 1,000 futures for every option compared; median reported when skewness is outside -1.5 to 1.5; answers rounded ("about 3,150").
- Forecasts: error convention stated (forecast minus actual), every method scored on the same periods, held-out error for any claim of accuracy, starting values not zeroed.
- Regression and networks: Non-Negative cleared, Automatic Scaling ticked, typical miss and R-squared compared with a simple baseline.

## Writing the recommendation

End with a short manager-ready paragraph: the decision and its number first; the bottleneck or risk in dollars ("lumber is worth up to $5.63 a board-foot; overtime buys nothing"); the honest caveat (the range a rate holds for, the chance of a bad outcome, how wrong the forecast tends to be); and what would change the answer. No formulas in that paragraph.
