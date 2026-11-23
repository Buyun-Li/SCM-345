# Simulation optimization (let Solver pick the number under uncertainty)

## Contents
1. The idea: sample paths and the swap
2. Why you cannot point Solver at a live simulation
3. The build: generate, freeze, cost columns, summarize, solve
4. Cross-checks: sanity grid and the critical ratio
5. Choosing what to optimize (average, percentile, worst case)
6. A rule you cannot keep: price it (relaxation)
7. Two goals in different units
8. Optional: a dashboard with a re-run button
9. Worked example: Blue Mountain salt order
10. Mistakes that quietly ruin the answer

---

## 1. The idea

The honest question, "which decision is best against every future that could happen?", has infinitely many futures. The swap: **"which decision is best on average against these 1,000 futures?"** You have not removed the uncertainty; you replaced an impossible question with a close one.

A **sample path** is one complete future written in one row: every uncertain quantity at the same time (storms AND tons per storm). Drawing them separately throws away the fact that a bad year is bad in several ways at once.

Solver finds the exact bottom of the curve you hand it; all the error lives in the curve, which comes from the sample. More sample paths -> a closer answer (four times the paths halves the scatter), never exact. So round the answer and say "about".

## 2. Why not a live model

If the random cells redraw while Solver is trying order quantities, the average jumps around by more than the differences Solver is trying to detect: a ruler that changes length every time you pick it up. Freeze the sample first.

## 3. The build

1. **One sample path.** Inputs in grey with names. One cell per random input, e.g. `Storms =VLOOKUP(RAND(), Storm_Table, 2, TRUE)` and `Tons_Per_Storm =MAX(0, ROUND(NORM.INV(RAND(), Avg_Tons, SD_Tons), 0))`.
2. **1,000 sample paths with a data table.** Top row of the table holds one formula per random input (`=Storms`, `=Tons_Per_Storm`); trial numbers 1..1,000 down the left; row input empty; column input an empty cell. Build this BEFORE the cost columns (otherwise every table pass recalculates a thousand rows of costs).
3. **Freeze.** Formulas > Calculation Options > **Automatic Except for Data Tables** (Mac: **Partial**). Test it: change the decision; the summary should move and the 1,000 rows should not.
4. **Cost columns** beside the frozen block, one row per path, all pointing at the named decision cell, e.g.
   - Used `=F6*G6`
   - Short `=MAX(H6-Order_Tons, 0)`
   - Leftover `=MAX(Order_Tons-H6, 0)`
   - Emergency cost `=I6*Spot_Price`
   - Carryover credit `=J6*Carry_Value`
   - Total cost `=Order_Tons*Contract_Price + K6 - L6`
   Fill down to row 1,005 and name the column (`Cost_Trials`).
5. **Summarize** (monte-carlo-simulation.md section 6), including the average cost cell `Avg_Cost =AVERAGE(Cost_Trials)` and the chance of running short `=COUNTIF(Short_Trials, ">0")/1000`.
6. **Solver:** Set Objective `Avg_Cost`, Min, By Changing `Order_Tons`, constraints `Order_Tons >= 0` and `Order_Tons <= ` a generous upper bound, **GRG Nonlinear** (the cost uses MAX, so if GRG stalls, try another start or Evolutionary with bounds). Integer if it must be whole.
7. **Stability check:** press F9 (new sample) and re-solve two or three times. The answers scatter a little; report a rounded value ("about 3,150 tons").

The frozen block never appears in the Solver dialog; it is just there.

## 4. Cross-checks

- **Sanity grid:** a small table of average cost at 6-8 candidate decisions (written out the long way, or a data table with the decision cell as column input). Solver's answer should sit near the bottom.
- **Critical ratio (newsvendor shortcut):** cost of one unit too few = Cu, cost of one unit too many = Co. The best order is the Cu / (Cu + Co) percentile of demand. Use it as a check, not a replacement: when demand is a product of random things (storms x tons) no formula gives that percentile, but the simulation does, and the two agree.
- **Order above or below average demand?** Above when running short hurts more than having leftovers (Cu > Co), below when leftovers hurt more.

## 5. Choosing what to optimize

The average is a choice. Change only the objective cell and re-solve:

| Objective cell | Excel | Protects against | Note |
|---|---|---|---|
| Average cost | `=AVERAGE(Cost_Trials)` | the long run | Default for a decision repeated every year |
| A percentile (e.g., 95th) | `=PERCENTILE.INC(Cost_Trials, 0.95)` | a bad year | Usually cheap insurance near the average optimum |
| Worst case (min-max) | `=MAX(Cost_Trials)` | the single worst path | Driven by ONE row; unstable from sample to sample; can backfire on ordinary bad years |
| Chance of breaking a promise | `=COUNTIF(Cost_Trials, ">"&Budget)/1000` | a covenant or budget | A step function; GRG struggles, use Evolutionary |

**Min-max** = the outer MIN is over what you control (you choose first), the inner MAX is over what you do not (the world answers with your worst future). **Max-min** is the mirror for profit: the best worst case. This is the payoff-table maximin idea with 1,000 columns.

If skewness says "Median", still minimize the average for a repeated decision (the average decides the total over many years) but report the median alongside it.

## 6. A rule you cannot keep: price it

If a hard constraint makes Solver report infeasible ("every season under $300,000"), move it into the objective with a price per unit of violation:
- Overrun column: `=MAX(Total_Cost - Covenant, 0)`; `Avg_Overrun =AVERAGE(Overrun_Trials)`.
- New objective: `=Avg_Cost + Penalty * Avg_Overrun`. Run a ladder of penalties ($0, $0.50, $1, $2, $5, $20).
- Read the ladder: violation reaches zero -> the rule was keepable; shrinks then **flattens** -> the rule is impossible, and the flat level is the best achievable; never moves -> the penalty is too small next to the other costs (start near ten times the unit cost the rule is about).
- The deliverable sentence: "We cannot promise X; the best we can do is Y, and it costs Z a season. Shall we rewrite the term or price it?" (This is called Lagrangian relaxation.)

## 7. Two goals in different units

Solver optimizes one cell. Two ways to combine cost (dollars) with service (percent):
- **Weighted sum:** `=Avg_Cost + Weight * 100 * (1 - Avg_Service)`. Weight = dollars per percentage point missed. Check units out loud: if they do not cancel to dollars, the number is meaningless. Run a sweep of weights and show the trade-off curve; nobody can state a weight in a meeting, but anyone can pick a point on a curve.
- **Promote one goal to a constraint:** minimize `Avg_Cost` subject to `Avg_Service >= 98%`. A sentence a manager can sign ("we promise 98%").
- Both walk the same curve. When the decision affects people (schedules, fairness), prefer the constraint form; it can be argued about in public.

## 8. Optional: a dashboard with a re-run button

Put form controls (spin button, combo box, check box) on a front sheet whose cell links drive the inputs, plus a box plot of `Cost_Trials`, plus a recorded macro that redraws (Calculate Now), Reset All, re-solves, keeps the solution. Steps and the freshness check are in excel-conventions.md section 9. Save as .xlsm first. The last thing to do before saving is click the button, so the answer on screen matches the sample on screen.

## 9. Worked example: Blue Mountain salt order

Contract salt $82/ton; leftover ton worth $62 next season; emergency salt $185/ton; storms Poisson average 14; tons per storm normal(172, 30); budget $300,000.
- Cu = 185 - 82 = $103; Co = 82 - 62 = $20; critical ratio 103/123 = 0.837.
- Average usage about 2,408 tons. Best order about **3,160 tons** (about 30% above average usage), average season cost about $223,000, short in about 16% of winters. Ordering the average costs about $12,400 a season more.
- Hand checks: order 3,000, winter of 16 storms x 180 tons = 2,880 used -> 120 leftover -> cost 3,000 x 82 - 120 x 62 = **$238,560**. Order 3,000, 18 x 195 = 3,510 used -> 510 short -> 246,000 + 510 x 185 = **$340,350**.
- Neighboring orders (3,000 vs 3,300) differ by about $150 a season: a 1,000-path data table cannot tell them apart; Solver on frozen paths can.

## 10. Mistakes that quietly ruin the answer

- Solving with calculation still on **Automatic**: the answer jumps every run (wild values like 900 or 5,800).
- Pressing F9 **after** solving: the answer on screen belongs to the old sample.
- Ordering the average instead of minimizing the average cost.
- Shortage charged at the full spot price without crediting the contract already paid, or carryover credit added instead of subtracted.
- Data table built before row 1 of the trial is complete (it copies blanks).
- Upper bound on the decision too low (Solver returns the bound, not the optimum).
- Leftover constraints from an earlier run: Reset All.
