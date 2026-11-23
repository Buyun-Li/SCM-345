# Common mistakes, by symptom

Collected from what actually went wrong in SCM 345 homework and projects. Use it to debug a model someone describes, and to check your own build before handing it over.

## Solver results that look wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| "Could not find a feasible solution" | `=` where `<=` belongs (supply bigger than demand; more people than seats); a minimum written as `<=` or a capacity as `>=`; a requirement larger than capacity | Re-read each sign in words. If the rules genuinely conflict, that is the business finding (or price the rule: simulation-optimization.md section 6) |
| "Objective Cell values do not converge" | A capacity constraint left out of the dialog | Compare the dialog against the canonical form line by line |
| Answer looks too good | A "rule nobody writes down" is missing (one job per person), or a contract `>=` typed as `<=` (profit goes UP) | Add the rule; check signs |
| Two people get different plans, same objective | Multiple optima (a tie) | Both right. Compare the objective, not the plan |
| Different answer every time you solve a simulation | Calculation on Automatic, so the sample redraws during the search | Formulas > Calculation Options > Automatic Except for Data Tables (Partial) |
| Answer on screen does not match the sample on screen | F9 pressed after solving | Re-solve; make the macro's last step the solve |
| Solver returns exactly the upper bound | Bound too tight | Raise the bound and re-solve |
| GRG returns a poor answer that "Solver found" | Local optimum, bad starting values (trend started at 0, all weights 0) | Re-solve from sensible starts; multistart; Evolutionary with bounds |
| A regression or network fit will not budge | Non-Negative still ticked, Automatic Scaling off, or weights started at zero | Clear Non-Negative, tick Automatic Scaling, use spread-out starts |
| Logistic total worse than a coin flip | Solver left on Min | Max |
| A Solver run that used to work now fails | Constraints left from an earlier run | Reset All, re-enter |
| No Sensitivity Report offered | Model has `int` or `bin` | Expected. Solve as an LP for the economics, or re-solve to price a change |
| Macro error "Sub or Function not defined" | Solver reference missing in VBA | Developer > Visual Basic > Tools > References > tick SOLVER |

## Modeling errors that give a plausible number

- **Typed numbers inside formulas** instead of links to the input cells (`<= 900` typed): the model and the inputs silently disagree after a change.
- **Raw cell addresses in Solver** or in SUMPRODUCT ranges: hard to audit and breaks when rows are inserted. Name them.
- **Missing `$`** when filling down a formula that points at an input.
- **Averages vs totals** in blending: a spec of "average 6.4 across 1,000 lb" must be `>= 6,400` points.
- **A ratio with decisions in the denominator** (`supplier / total <= 40%`): multiply through.
- **Benchmark treated as a constraint** (a profit target when profit is the objective).
- **Fixed cost added per unit** (a $600 delivery fee charged per tree), or leftover valued at the full price instead of the salvage price.
- **Revenue capped at quantity made** when shortages are actually reprinted/expedited and still sold.
- **Profit subtracting unit costs instead of total costs** (forgot to multiply by quantity).
- **Demand not rounded or not floored at zero:** use `MAX(0, ROUND(NORM.INV(RAND(), Avg, SD), 0))`. RAND() goes FIRST in NORM.INV and LAST in BINOM.INV.
- **VLOOKUP without TRUE** on a "Starts at" table, or pointed at the wrong columns.
- **Ordering average demand** instead of minimizing average cost.
- **Service level built upside down** (demand / order instead of share supplied from the contract).

## Simulation output errors

- **Data table column input pointing at a model cell** (e.g., Demand): the table fills with nonsense. It must be an empty cell.
- **Row and column inputs swapped** in a two-way table.
- **Box plot built from the summary cells** or including the trial-number column: select only the outcome values.
- **"Average or median" typed as text** instead of a formula testing SKEW.
- **Reading a capped number as exceedable:** if profit cannot exceed the sell-out level, the 95th percentile may sit exactly at that ceiling.

## Forecasting errors

- **Sign of the error flipped** (actual - forecast): only the bias changes sign; say which convention you use.
- **Percent error divided by the forecast** instead of the actual.
- **Scoring methods on different stretches** of history: align them (AVERAGEIF on the period number).
- **Fitting and grading on the same data** and calling it skill: hold periods out.
- **Seasonal indices that do not sum to the number of seasons**, or weights that do not sum to 1 (a rounded total of 1.000001 against a constraint of exactly 1 can also trip Solver: round the starting values).
- **Starting values cleaned up to zero** (trend 0, indices 1, equal weights is fine; trend 0 is not).
- **KNN distance divided by the peer's value** instead of your own; **all columns switched on** (irrelevant columns outvote relevant ones).

## Reporting errors

- Recommendation buried below the method. Lead with the decision and the number.
- A shadow price used outside its allowable range (check the range, or re-solve).
- Too many digits: a simulated optimum of 3,162 is "about 3,150"; say why (sample-to-sample scatter).
- An average reported for a heavily skewed outcome without the median.
- Fit error (typical miss on known periods) presented as the uncertainty of next period, when the inputs themselves are uncertain.
