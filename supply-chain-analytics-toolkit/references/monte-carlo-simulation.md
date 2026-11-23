# Monte Carlo simulation in Excel

## Contents
1. Why simulate: the flaw of averages
2. The five steps
3. Generating random inputs (the distribution toolkit)
4. Building one trial
5. Replicating with a data table
6. Summarizing: the numbers to report, and the median rule
7. Comparing decisions: two-way data table
8. Chained random numbers and adding uncertainties
9. Worked examples with check values

---

## 1. Why simulate: the flaw of averages

Plugging average demand into a model gives the profit at average demand, which is not the average profit. A cafe bakes 100 croissants ($1 each, sold at $3, leftovers thrown out); demand is 50 or 150, equally likely. The plan at average demand says $200. A slow day earns $50, a busy day $200 (sales are capped at 100), so the real average is $125.

Uncertainty lives at every stage of a supply chain: supply availability and material prices (procure), defect rate (manufacture), transportation capacity and transit time (deliver), customer demand (sell). Each one creates a trade-off between planning too high and planning too low.

We cannot list every possible future, so we draw a large sample of them and look at the whole distribution of outcomes.

## 2. The five steps

1. **Inputs:** grey cells with names (prices, costs, the decision).
2. **Uncertainty:** one cell per random input, using a formula from section 3.
3. **One trial:** the business logic for a single random future, ending in one output cell (Profit).
4. **Data table:** replicate the trial 1,000 times.
5. **Summarize:** average, median, spread, percentiles, chance of a bad outcome; box plot.

## 3. Generating random inputs

Every random function starts from `RAND()` (a number between 0 and 1, all values equally likely) and "reads the CDF backward": the chance of a value or less is turned back into the value.

| Distribution | Use it for | Excel |
|---|---|---|
| Uniform, whole numbers | any whole value in a range equally likely | `=RANDBETWEEN(3, 7)` |
| Uniform, continuous | any value in a range | `=40 + (55 - 40) * RAND()` |
| Normal | demand of an established product, usage per event | `=NORM.INV(RAND(), Avg, SD)`; for whole units never below zero: `=MAX(0, ROUND(NORM.INV(RAND(), Avg_Demand, SD_Demand), 0))` |
| Binomial | how many of N tries succeed/fail (defects in a lot, no-shows) | `=BINOM.INV(N, chance_of_yes, RAND())` (RAND last) |
| Poisson | counts of events in a period (arrivals per hour, storms per winter) | Build a table of values with `=POISSON.DIST(k, Avg, FALSE)` and use the lookup below; or Data > Data Analysis > Random Number Generation > Poisson (writes fixed numbers that F9 will not redraw) |
| General discrete / empirical | a table of outcomes with chances from history | `=VLOOKUP(RAND(), Demand_Table, 2, TRUE)` with a "Starts at" column |
| Triangular-style "min / most likely / max" | expert estimates | build as a general discrete table, or a uniform if no favorite |

**The "Starts at" column** for a discrete table: first row 0; each next row = previous start + previous chance. Example:

| Starts at | Demand | Chance |
|---|---|---|
| 0.00 | 0 | 0.10 |
| 0.10 | 25 | 0.10 |
| 0.20 | 50 | 0.15 |
| ... | ... | ... |

`Demand_Table` covers the Starts-at and Demand columns; `VLOOKUP(..., TRUE)` finds the last start at or below RAND(). Chances must add to 1.

Choosing a distribution: plot a histogram of history first, then pick the shape that matches, and be honest that it is a choice.

## 4. Building one trial

The common inventory-style trial:

| Cell | Formula |
|---|---|
| Demand | random draw (section 3) |
| Actual sale | `=MIN(Order_Qty, Demand)` |
| Leftover | `=Order_Qty - Actual_Sale` (or `=MAX(Order_Qty - Demand, 0)`) |
| Unfilled demand | `=Demand - Actual_Sale` |
| Unit cost with price breaks | `=VLOOKUP(Order_Qty, Price_Tiers, 2, TRUE)` (tiers table: "order at least" and price) |
| Revenue | `=Actual_Sale * Full_Price + Leftover * Salvage_Price` |
| Profit | `=Revenue - Unit_Cost * Order_Qty - Fixed_Cost` |

Adapt the logic to the story. If every customer is served by a reprint or expedite, revenue is `Price * Demand` and the shortage has its own cost (`MAX(Demand - Qty, 0) * Reprint_Cost`).

Test the trial by typing fixed demands in place of the random cell and checking a few profits by hand before replicating.

## 5. Replicating with a data table

Follow excel-conventions.md section 7: an empty corner cell, `=Profit` beside it, trial numbers 1..1,000 down the left, Data > What-If Analysis > Data Table, row input empty, column input an empty cell. Name the 1,000 results (`Profit_Trials`).

Press F9 to redraw everything. Numbers wobble a little each time: a simulation gives an estimate. More trials shrink the wobble; four times the trials halves it.

## 6. Summarizing

| Report | Excel |
|---|---|
| Average | `=AVERAGE(Profit_Trials)` |
| Median | `=MEDIAN(Profit_Trials)` |
| Standard deviation | `=STDEV.S(Profit_Trials)` |
| Skewness | `=SKEW(Profit_Trials)` |
| 5th and 95th percentile | `=PERCENTILE.INC(Profit_Trials, 0.05)`, `0.95` |
| Chance of a loss | `=COUNTIF(Profit_Trials, "<0")/1000` |
| Chance above a target | `=COUNTIF(Profit_Trials, ">"&Target)/1000` |
| Average or median? | `=IF(OR(SKEW(Profit_Trials)>1.5, SKEW(Profit_Trials)<-1.5), "Median", "Average")` |

**The median rule:** if skewness is outside -1.5 to 1.5, the outcomes have a long tail, so report the median as the typical result (alongside the average). Then add a box plot of the 1,000 values.

Say results in business terms: "Ordering 420 trees, a typical season earns about $10,000; most seasons land between about $2,000 and $13,680 (a sell-out); a loss happens in about 3% of seasons."

## 7. Comparing decisions: two-way data table

To compare order quantities: corner `=Profit`, quantities across the top, trial numbers down the side, row input = the decision cell, column input = an empty cell. Summarize each column with the section 6 block and draw one box plot per column.

Choose with both the average and the risk: the highest average may also have the fattest bad tail. If two averages differ by less than the run-to-run wobble, they are a tie; decide on risk. (For a precise best quantity, use simulation optimization.)

## 8. Chained random numbers and adding uncertainties

- A random number can feed another: trucks arriving today (random), then failed inspections among them `=BINOM.INV(Trucks_Today, 0.03, RAND())`.
- Adding independent uncertainties gives a total that is more spread out than either piece, but less than the sum of their spreads (variances add). If the pieces move together, the spreads add fully.
- **Bullwhip effect:** each stage of a supply chain that forecasts from the orders it receives (rather than real customer demand) adds variability, so order swings grow upstream. Sharing point-of-sale data, shorter lead times, smaller more frequent orders, steady prices and allocation by past sales calm it.
- Two uncertain quantities that happen in the same future must be drawn in the same row (storms x tons per storm), not simulated separately and averaged.

## 9. Worked examples with check values

**Rivalry T-shirts (discrete demand, price breaks).** $200 fixed order cost, sell $15.99 before the game, $5.00 after; at 150 shirts cost $5.35 + $1.25 printing = $6.60 each. Order 150, demand 75 -> profit $384.25. Exact best of the candidates is 145 shirts (just past a printing price break).

**Christmas tree lot (normal demand).** Delivery $600, sell $59, leftover mulch $4, tree $25 each at 420; demand normal(380, 110). Profit at demand 380 = $11,480; sell-out ceiling $13,680; average about $10,009; loss chance about 3%; the 95th percentile equals the ceiling because sales are capped.

**Valentine cards (shortage is reprinted, not lost).** Print $0.50, sell $4.00, dispose $0.20, reprint $0.75; demand normal(35,000, 5,000). Printing 30,000 with demand 35,000 -> $121,250. A short card costs $0.25 extra, a spare card wastes $0.70, so the best quantity sits BELOW average demand (about 32,000).
