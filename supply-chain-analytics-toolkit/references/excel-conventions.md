# Excel conventions used in every model

These are the house rules from SCM 345. They exist because a model nobody can read is a model nobody can trust, including the person who built it.

## Contents
1. Setup (Solver, Analysis ToolPak, desktop Excel)
2. The four color zones
3. Named ranges
4. The Solver dialog, field by field
5. Solver Options that matter
6. Calculation options (freezing random numbers)
7. Data tables (one-way and two-way)
8. Box and whisker charts
9. Form controls and a recorded macro (dashboards)
10. Habits that prevent silent errors

---

## 1. Setup

- Use **desktop Excel** (Windows or Mac). Excel for the web has no Solver.
- Turn on two free add-ins: **Solver** and **Analysis ToolPak**.
  - Windows: File > Options > Add-ins > Manage: Excel Add-ins > Go > tick both.
  - Mac: Tools > Excel Add-ins > tick both.
- Google Sheets and LibreOffice can open the files but cannot run Excel Solver or data tables the same way.

## 2. The four color zones

Lay every model out so a stranger can see what is given, what is chosen and what is computed.

| Zone | Color | What goes in it | Maps to |
|---|---|---|---|
| Inputs | grey | Numbers you were given (costs, capacities, demand) | Parameters |
| Decisions | yellow | Cells Solver will change (start them at 0 or a sensible guess) | Decision variables |
| Calculations | green | Formulas: resources used, totals, cost columns | Left-hand sides of constraints |
| Outputs | cream | The number being maximized or minimized, plus results to report | Objective |

Keep inputs in cells, never typed inside formulas. If the lumber limit is 900, the constraint points at the cell holding 900. Then a what-if is one cell edit, and the model cannot quietly disagree with itself.

## 3. Named ranges

Every reference Solver can see gets a name: the objective cell, the changing cells, and both sides of every constraint. So does every SUMPRODUCT range. Ordinary row and column totals may use plain cell references.

Why: `Shipped_Out <= Supply` is a sentence you can check; `$G$14:$G$16 <= $H$14:$H$16` is not. Names also follow their block when you insert a row; typed addresses do not, and that failure is silent.

Three ways to make one (all on Formulas > Defined Names):

| Tool | What it does | When to use it |
|---|---|---|
| **Name Box** (left of the formula bar) | Select block, click Name Box, type name, Enter | The blocks Solver reads: `Build`, `Total_Cost` |
| **Create from Selection** | Select a labeled table, tick Top row / Left column | Names every row and column at once. It never names the whole rectangle. |
| **Name Manager** | Lists, edits and deletes names | When Solver returns something you cannot explain |

Rules: no spaces (use `Total_Cost`), must start with a letter or underscore, and cannot look like a cell address (`Q1`, `C4`, `R2` are rejected).

## 4. The Solver dialog, field by field

| Solver field | Model part | Example |
|---|---|---|
| Set Objective | the objective cell (cream) | `Total_Profit` |
| To: Max / Min / Value Of | which way | Max |
| By Changing Variable Cells | the decision block (yellow) | `Build` |
| Subject to the Constraints | one line per constraint FAMILY; a block on each side expands to many | `Used <= Available` |
| Make Unconstrained Variables Non-Negative | tick for quantities; clear when a value may be negative (regression rates, neural-network weights) | |
| Select a Solving Method | Simplex LP (linear), GRG Nonlinear (smooth curves), Evolutionary (cliffs and jumps) | Simplex LP |

- **Integer and binary:** in Add Constraint, pick `int` or `bin` from the middle drop-down (it fills "integer"/"binary" in itself). Do not type it.
- **Reset All** before solving a different question in the same workbook. Old constraints stay in the dialog and ride along silently.
- After Solve: **Keep Solver Solution**. For a linear model, tick **Answer** and **Sensitivity** in the Reports list before clicking OK. Integer/binary models never offer a Sensitivity Report.
- The three outcome messages: "Solver found a solution" (optimal), "could not find a feasible solution" (infeasible: rules contradict each other, often a sign pointing the wrong way or an `=` that should be `<=`), "Objective Cell values do not converge" (unbounded: a limit is missing).

## 5. Solver Options that matter

- **Use Automatic Scaling**: tick it whenever the decisions differ wildly in size (a regression rate of 0.002 next to a constant of 5).
- **Make Unconstrained Variables Non-Negative**: clear it for regression, logistic and neural-network fits, because rates and weights can be negative.
- **GRG Nonlinear > Use Multistart**: tries many starting points; needs upper and lower bounds on every decision cell. The manual version: solve, type a different starting value, solve again, compare.
- **Evolutionary**: needs upper and lower bounds on every decision cell. Slower; can be re-run for a better answer.
- Neither GRG nor Evolutionary guarantees the best possible answer. Simplex LP does, for a linear model.

## 6. Calculation options (freezing random numbers)

Formulas > Calculation Options has three settings:

| Setting | What recalculates | Use it when |
|---|---|---|
| Automatic | everything, including every RAND() | Normal modeling with no simulation |
| **Automatic Except for Data Tables** (labeled **Partial** on the Mac three-button control) | ordinary formulas yes, data tables no | Simulation optimization: the 1,000 sample paths stay still while Solver searches |
| Manual | nothing until you press F9 | Freezes everything, but the summary goes stale too |

With Partial, **F9 is the redraw button**: press it to get a new sample, never right after solving (the answer on screen would then belong to the old sample).

Fallback if a data table still moves: select the whole data table body and Copy > Paste Special > Values.

## 7. Data tables

A data table recalculates a model many times and records an output each time. This is how every simulation in the course is replicated.

**One-way (1,000 trials of one output):**
1. In the column next to an EMPTY cell (say A29 empty, B29 `=Profit`), list trial numbers 1 to 1,000 below (A30:A1029).
2. Select A29:B1029.
3. Data > What-If Analysis > Data Table.
4. Row input cell: leave empty. Column input cell: any empty cell off to the side (e.g., D29). Excel writes each trial number there; nothing reads it, but it forces a fresh recalculation per row.
5. OK. Each row is now an independent random outcome.

To record several outputs per trial, put several formulas across the top row (`=Storms`, `=Tons_Per_Storm`) and select the wider block.

**Two-way (several decision options, 1,000 trials each):**
1. Corner cell: `=Profit`. Across the top row: the decision values to try (100, 125, 150...). Down the left column: trial numbers 1 to 1,000.
2. Select the whole block. Data Table: **Row input cell = the decision cell** (e.g., `Order_Qty`), **Column input cell = an empty cell**.
3. Every cell is its own random trial, so columns are NOT compared on the same futures. (For a fair head-to-head, freeze one set of sample paths and evaluate every option on it; see simulation-optimization.md.)

Common mistakes: column input pointing at a model cell such as Demand; row and column inputs swapped; building the table before the trial formulas are filled in.

## 8. Box and whisker charts

Select the outcome VALUES only (not the trial-number column, not the header row of quantities), then Insert > Charts > Statistic Chart > Box and Whisker. Reading one: line = median, X = average, box = middle half of outcomes, whiskers = typical range, dots = unusual outcomes.

## 9. Form controls and a recorded macro (dashboards)

Turn on the Developer tab: File > Options > Customize Ribbon > tick Developer. Save as **.xlsm** before recording anything.

Every form control does one thing: it writes a number into its **cell link**.

| Control | Good for | Format Control settings |
|---|---|---|
| Spin button | a number in a range | min, max, step, cell link |
| Combo box | pick from a list | input range (the list of names), cell link (gets 1, 2, 3...; turn it into a value with `=INDEX(list, link)`) |
| Check box | show/hide | cell link (TRUE/FALSE); use `=IF(Show_Check, value, "")` |
| Button | run a macro | Assign Macro |

Recording a "re-run" macro:
1. Developer > Visual Basic > Tools > References > tick **SOLVER** (once per workbook), close the editor.
2. Developer > Record Macro, name it `RunSimulation`, store in This Workbook.
3. Formulas > Calculate Now (F9), to redraw.
4. Data > Solver > **Reset All**, then fill every field and Solve > Keep Solver Solution.
5. Developer > Stop Recording. Right-click the button > Assign Macro.

"Sub or Function not defined" when the macro runs means the SOLVER reference in step 1 is missing.

A freshness check is worth adding: compare the average of the frozen sample with what the controls now say, and show STALE when they disagree, e.g.
`=IF(AND(ABS(AVERAGE(Storms_Trials)-Dash_Storms)<=0.6, ABS(AVERAGE(Tons_Trials)-Dash_Tons)<=6), "UP TO DATE", "STALE - click Run Simulation")`

## 10. Habits that prevent silent errors

- Write the model in words (canonical form) before typing a formula.
- Lock references with `$` when filling a formula down, or better, use names.
- Check units on both sides of every constraint.
- Put a check figure next to the answer (a hand calculation of one case).
- Change an input in the direction you understand (raise a cost) and confirm the answer moves the way it should.
- When two people get different plans with the same objective value, both may be right: compare the objective, not the plan.
