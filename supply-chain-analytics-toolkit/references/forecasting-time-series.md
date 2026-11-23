# Forecasting from history: error measures, moving averages, weighted moving averages with trend and seasonality, nearest neighbors

## Contents
1. What a forecast is for
2. Plot first: level, trend, seasonality, noise
3. Measuring error (do this before choosing a method)
4. Fit is not skill: hold data out
5. Moving average
6. Weighted moving average (Solver picks the weights)
7. Weighted moving average with trend and seasonality
8. Nearest neighbors (KNN) for a product with no history
9. Reporting a forecast

---

## 1. What a forecast is for

The answer is a distribution, not a single number: a middle (the point forecast) and a spread (how wrong it tends to be). The spread is what sizes safety stock and feeds the simulations in Module 2. Every forecast must beat the **naive forecast** (next period = this period) to earn its keep.

Two families of method:
- **Non-parametric (history-based):** moving averages, weighted moving averages, nearest neighbors. Look at past values (or at similar cases) and average them.
- **Parametric (factor-based):** regression, logistic regression, neural networks. Fit numbers that say how much each factor moves the outcome. See regression.md and neural-network.md.

## 2. Plot first

Always chart the series before modeling. Ask: is there a **level**, a **trend** (does it climb?), **seasonality** (does a shape repeat every week/quarter/year?), and how big is the **noise**? The first three repeat and can be predicted; noise can only be measured.

## 3. Measuring error

Everything starts with one column. Course convention: **error = forecast - actual** (positive = forecast too high). State the convention you use, because both are used in industry.

| Column | Formula (row 9) |
|---|---|
| Error | `=Forecast - Actual` (e.g. `=E9-D9`) |
| Absolute error | `=ABS(F9)` |
| Squared error | `=F9^2` |
| Percent error | `=G9/D9` (absolute error divided by ACTUAL) |

| Measure (full name first) | What it tells you | Excel |
|---|---|---|
| Mean Error (ME), also called bias | Direction: does it run high or low? Can be near zero while every week is badly off | `=AVERAGE(Errors)` |
| Mean Absolute Deviation (MAD) | Typical size of a miss, in units | `=AVERAGE(Abs_Errors)` |
| Mean Squared Error (MSE) | Size with big misses punished hard (units squared) | `=AVERAGE(Sq_Errors)` |
| Root Mean Squared Error (RMSE) | Same as MSE but back in units; the default for fitting | `=SQRT(AVERAGE(Sq_Errors))` or `=SQRT(SUMPRODUCT(Errors,Errors)/COUNT(Errors))` |
| Mean Absolute Percentage Error (MAPE) | Size as a percent, to compare items of different scale | `=AVERAGE(Pct_Errors)` |

How they disagree, and why it matters:
- One huge miss dominates squared error, so RMSE much bigger than MAD means outlier periods. RMSE about equal to MAD means misses are even in size (a free diagnostic).
- MAPE divides by actual, so a big miss on a big week looks small, and anything near zero demand explodes MAPE.
- Bias is the only measure that shows direction. A forecast that runs high every week quietly overstocks the warehouse even if its MAD is small.
- **Choose the measure before you see the scores**, by what a miss costs: MAD if cost grows in proportion to the miss; RMSE if one bad week is far worse than several small ones (stockouts that stop a job site); MAPE to compare items of different sizes; always report bias too.

Score every method on the SAME periods (e.g., `=AVERAGEIF(Day, ">=111", Sq_Errors)`), because a long window cannot forecast its first periods.

## 4. Fit is not skill

A model that matches history perfectly has usually memorized it. Fair test: **hold out** the last stretch of periods, fit on the rest, and grade only on the held-out periods the model never saw. When choosing between methods or settings, compare their held-out errors.

## 5. Moving average

Forecast for period t = average of the last k actuals. In the first row that has a full window: `=AVERAGE(E10:E16)` for k = 7 at row 17, then fill down. The first k rows stay empty (no window yet), which is why the forecast columns form a staircase.

- The one dial is the window k. Short window: responds quickly but chases noise. Long window: smooth but **lags**.
- A moving average always lags a trend: a k-period window is centered (k+1)/2 periods back, so on a climbing series every forecast comes in low (negative bias that grows with k).
- With a repeating pattern, a window of exactly one cycle (7 for daily data with a weekly shape, 4 for quarters, 12 for months) contains one of each season and is not tilted by which days happen to be in it. That is why it often wins.
- More data is not the same as a better forecast.

## 6. Weighted moving average

Forecast = a x (1 period ago) + b x (2 periods ago) + ..., with the weights adding to 1.

- Weights in a named yellow block `Weights` laid out as a COLUMN (same shape as the data column; SUMPRODUCT needs matching shapes), oldest at the top, most recent at the bottom, matching the rows above the forecast: `=SUMPRODUCT(Weights, E10:E16)` at row 17, fill down.
- Error columns and RMSE as in section 3.
- Solver: Min `RMSE` (on the scoring stretch), changing `Weights`, subject to `Weight_Total = 1` (a cell `=SUM(Weights)`), Weights >= 0 (Non-Negative ticked), GRG Nonlinear.
- What to look at: where Solver puts the weight. On daily data with a weekly shape it often puts almost all weight on the same weekday last week, because that is the only way to get the weekday right. That is a sign the next method is needed.

## 7. Weighted moving average with trend and seasonality

The model, in words: take the weighted average of the last k actuals (this sits behind the series and is not tilted by season if the window is one full cycle), add a **trend** term to catch up for the lag, then multiply by the **seasonal index** for the period being forecast.

```
base         = SUMPRODUCT(Weights, last k actuals)
forecast(t)  = (base + Trend) * index(season of t)

with   SUM(Weights) = 1,   Weights >= 0
       SUM(Season_Index) = number of seasons (7 for days of the week, 4 for quarters, 12 for months)
       each index >= 0.2 (keeps Solver away from nonsense)
```

Excel layout:
- A column with the season of each row (1..7 or Q1..Q4) and a small table of the indices, named `Season_Index` (yellow), plus `Weights` (yellow column, oldest at the top) and `Trend` (yellow cell).
- Forecast at the first full row, filled down: `=(SUMPRODUCT(Weights, E10:E16) + Trend) * INDEX(Season_Index, C17)` where C17 holds the season number of that row.
- Error columns, RMSE (and bias, MAD, MAPE) on the scoring stretch.
- Solver: Min `RMSE`; changing `Weights, Trend, Season_Index` (separate with commas); constraints `Weight_Total = 1`, `Index_Total = 7` (or 4, 12), `Season_Index >= 0.2`; Weights non-negative; GRG Nonlinear. (Ticking Make Unconstrained Variables Non-Negative also stops Trend going below zero. For a declining series, clear it and add `Weights >= 0` as a constraint instead.) Reset All first if another Solver model was set up in the workbook.

**Starting values matter (GRG walks uphill from where it starts).** Do not start Trend at 0:
- Weights equal (1/k each).
- Indices: 1 each, or better, ratio-to-moving-average: average of (actual / centered moving average) for each season, rescaled to sum to the number of seasons.
- **Trend start = how far back the average sits x growth per period.** For equal weights the window sits (k+1)/2 periods back (4 days for a 7-day window, 2.5 quarters for a 4-quarter window). Growth per period from the chart (e.g., last-year average minus first-year average, divided by the periods between). Example: 4 days x 13.9 cartons/day = about 56. In general the lag is 1 x (weight on the most recent period) + 2 x (weight on two periods back) + ... + k x (weight on k periods back).
- If Solver stops early (RMSE far above what the chart suggests), put the starting values back and solve again.

What to expect and say:
- Bias drops to about zero; RMSE falls sharply compared with the plain and weighted moving averages.
- Solver recovers the seasonal shape from the errors alone.
- **Index drift:** once the weights are unequal, the window is no longer one of each season, so the average itself carries a little seasonal tilt and the indices absorb it. The forecast stays good; just do not read an index as "what Q4 is really worth".
- The forecast for the next period uses the last k actuals, the fitted trend and the index of the next period's season.

## 8. Nearest neighbors (KNN) for a product with no history

Predict a new product, store or launch from the most similar existing ones.

Three steps; the judgment is in the first two:
1. **Find the benchmark set.** Err on the side of a longer list of comparable companies/products: a company that is unlike you will never be among the nearest few, so it does no harm.
2. **Identify the relevant measures.** Keep a column only if it drives the outcome. Plot outcome vs each column and compute `=CORREL(column, outcome)`; keep the strong ones. Here err SHORT: every irrelevant column gets a vote in every distance and can outvote the good ones.
3. **Scaled distance and the nearest k.** Scale each difference by your own value so units do not dominate:
   `Distance =SUMPRODUCT(Include, ((Target - D14:J14)/Target)^2)` (Include = 1/0 switches per column; Target = your own row). Fill down. `Rank =RANK(M14, Distance, 1)`. Forecast `=AVERAGEIF(Ranking, "<="&Neighbors, Outcome)` with Neighbors = k (3 to 5 is typical).

Diagnostics: a tiny nearest distance means genuinely similar peers; a large one means the columns or the peer list are wrong. If the k nearest outcomes agree closely, trust the average more. Test by leaving out one peer at a time and predicting it from the rest (a holdout). Divide by YOUR value, not the peer's.

## 9. Reporting a forecast

Give the number and how wrong it tends to be: "Q4 Towpath orders about 1,756 (typical miss about 20 bikes, no lean high or low)." Remember that fit error on known periods understates the uncertainty when the inputs themselves are uncertain next period.
