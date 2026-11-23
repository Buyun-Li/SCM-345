# Regression: using factors to predict an outcome

## Contents
1. The frame: outcome, factors, and the numbers on the arrows
2. Linear regression, built in four steps and fitted with Solver
3. Reading a rate
4. More than one factor (multiple regression), dummies and trend
5. The checklist to run after you fit
6. Logistic regression: when the outcome is yes or no
7. Cross-check with the Analysis ToolPak
8. Worked example numbers

---

## 1. The frame

Name the **outcome** you want to know, the **factors** you already know, and draw an arrow from each factor to the outcome. On each arrow sits a number: how much that factor moves the outcome (the **rate**). There is also a **starting point** (the constant): the prediction when every factor is zero. Those numbers are the only unknowns, and fitting the model means finding them.

Regression fills in the frame when the outcome is a number (a price, minutes, units). Logistic regression fills in the same frame when the outcome is yes/no. Same factors, same Solver.

One formula, for reference (the translation, not the teaching):
`outcome = starting point + rate1 x factor1 + rate2 x factor2 + ... + leftover miss`

## 2. Linear regression in four steps

Layout: data rows (one per month/order), factor columns, actual outcome column; yellow cells for `Price_Start` (the constant) and the rates (name the block, e.g. `Price_Rates` covering the constant and all rates).

1. **Predicted column:** `=Price_Start + Price_Steel*B17 + Price_Aluminum*C17 + Price_Gas*D17` (or `=Constant + SUMPRODUCT(Rates, B17:D17)` with the rates in a row), filled down.
2. **Miss column (squared):** `=(E17 - F17)^2`. Squaring does two jobs: a miss above cannot cancel a miss below, and a miss of 2 costs four times a miss of 1.
3. **One total:** `Total_Squares =SUM(Miss_Squared)`.
4. **Solver:** Set Objective `Total_Squares`, **Min**, By Changing `Price_Rates` (constant + rates), no constraints, **GRG Nonlinear**. Options: **tick Use Automatic Scaling** (rates can differ by thousands of times), **clear Make Unconstrained Variables Non-Negative** (a rate may be negative). Start the cells at rough guesses rather than all zero.

Then report:
- Typical miss: `=SQRT(Total_Squares/COUNT(Actual))` (RMSE, in the outcome's units).
- R-squared: `=1 - Total_Squares/DEVSQ(Actual)`. DEVSQ adds up each actual's squared distance from the average actual, so R-squared is "the share of the ups and downs the model explains" (0.98 = 98%).

## 3. Reading a rate

A rate is a business sentence: "Each $100 a ton more steel puts about $1.51 on the bracket price, holding aluminum and gas fixed." Always say the units of both the factor and the outcome. Only trust it inside the range of factor values you actually observed; do not extrapolate.

## 4. More than one factor

- Each extra factor gets its own column and rate. The rate means the effect of that factor **holding the others fixed**.
- **Dummy (yes/no) factors:** a 0/1 column (promotion week = 1). Its rate is the lift when it is on. For seasons, use one 0/1 column per season except one (the left-out season is the baseline).
- **Trend:** a period-number column (1, 2, 3...); its rate is growth per period.
- **Overfitting:** more factors always fit history better. Judge on held-out periods (forecasting-time-series.md section 4), and drop factors that do not improve held-out error.
- Two factors that move together (strongly correlated) confuse the model: their individual rates become unstable even when predictions are fine.

## 5. Checklist after you fit

Plot the misses (actual - predicted) and look for:
1. **Straight-line shape:** misses show no curve against any factor. (A curve means a nonlinear relationship: try a transformed factor, or a neural network.)
2. **No pattern over time:** misses do not run in long streaks above or below zero.
3. **Even spread:** misses are about the same size for small and large predictions.
4. **Factors not too related to each other:** check `=CORREL` between factor columns; very high values (above about 0.8) make rates unreliable.

## 6. Logistic regression (yes/no outcome)

A straight line can predict below 0% or above 100% and has the wrong shape in the middle. Wrap the same linear piece in an S curve that always lands between 0 and 1.

1. **Linear piece:** `=Hike_Start + Hike_Inflation*B17 + Hike_Unemployment*C17`.
2. **Chance of "yes":** `=1/(1+EXP(-E17))` (the logistic curve).
3. **Chance of what actually happened:** `=IF(D17=1, F17, 1-F17)` where D holds 1 for yes, 0 for no. This flip is where most people get stuck.
4. **Log score:** `=LN(G17)`. A confident wrong call (0.12 on something that happened) scores very badly (-2.12); squared error would not punish it enough.
5. **Total:** `Total_Logs =SUM(Log_Column)`.
6. **Solver:** **Max** `Total_Logs`, changing the constant and rates, GRG Nonlinear, Automatic Scaling ticked, Non-Negative cleared. (Left on Min by mistake, the total comes out worse than a coin flip.)

Judge it:
- Compare with a coin flip: every row at 0.5 scores `=COUNT(...)*LN(0.5)`. The model must beat that clearly.
- "Called right" counts (chance >= 0.5 and yes happened, or < 0.5 and no) can mislead; compare with always guessing the most common answer.
- Reading a logistic rate: its SIGN tells direction (higher inflation -> more likely to hike) and its size relative to others tells strength; it is not "adds 1.22 percent". To talk in chances, plug two scenarios into the predictor and compare: "at inflation 4.2 and unemployment 4.5, about a 76% chance; at 2.1 and 6.2, about 10%."

Formula for reference: `chance of yes = 1 / (1 + EXP(-(starting point + rate1 x factor1 + ...)))`

## 7. Cross-check with the Analysis ToolPak

Data > Data Analysis > Regression: Input Y = the outcome column, Input X = the factor columns (adjacent), Labels if headers are included. The Coefficients column must match Solver's starting point and rates (to rounding). The ToolPak also reports R Square, standard errors and p-values; a p-value says how surprising the estimated rate would be if the factor truly had no effect, not how important the factor is to the business.

## 8. Worked example numbers

Nazareth Precision (60 months; bracket price vs steel $/ton, aluminum $/ton, gas $/MMBtu): starting point 5.4868; steel 0.015119; aluminum 0.002187; gas 0.41991; total squared miss 2.30; typical miss about $0.20.

Rate decision (60 meetings; hike yes/no vs inflation and unemployment): starting point -1.9432; inflation 1.2225; unemployment -0.4483; total log -27.76 vs coin flip -41.59; 49 of 60 called right vs 31 for always guessing no.
