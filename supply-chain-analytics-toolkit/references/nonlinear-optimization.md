# Nonlinear optimization (GRG Nonlinear and Evolutionary)

The goal here is choosing the right Solver engine and not trusting a single run, not optimization theory.

## Contents
1. When a model stops being linear
2. Smooth or not: the pen test
3. The two engines
4. Local vs global, and starting values
5. Example 1: price and quantity (smooth, GRG)
6. Example 2: a second shift and overtime (cliffs, Evolutionary)
7. The four-step choice and validation checklist

---

## 1. When a model stops being linear

Every LP term is a parameter times a decision. Three ways that breaks in business:
- **A decision times a decision.** Revenue = price x quantity sold, when both are chosen.
- **Curves.** Unit cost that climbs with volume (overtime, expediting), quantity discounts, octane that does not blend in a straight line, portfolio risk.
- **Jumps and kinks.** A second shift that costs a flat $22,000 the moment unit 401 is built (IF), overtime charged only above 700 units (MAX), fixed ordering costs, lookups.

Constraints can be nonlinear the same way.

## 2. Smooth or not: the pen test

**Could you draw the profit curve without lifting your pen and without a sharp corner?**
- Yes (smooth hill or valley): **GRG Nonlinear**.
- No (cliffs, steps, corners from IF, MAX, MIN, ABS, ROUND, VLOOKUP on a decision): **Evolutionary**, or GRG run from several starting points.

## 3. The two engines

| | GRG Nonlinear | Evolutionary |
|---|---|---|
| How it searches | Walks uphill from where you start, following the slope | Breeds a population of trial answers, keeps the better ones, mutates them |
| Best for | Smooth curves | Models with cliffs, steps, IF/MAX/lookups |
| Speed | Usually fast | Usually slower; can be re-run for a better answer |
| Needs | A sensible starting value | Upper and lower bounds on every decision cell |
| Guarantee of the best possible answer | **No** | **No** |

Treat the comparison as tendencies, not laws. GRG can return an answer on a non-smooth model; the question is which answer.

## 4. Local vs global, and starting values

A hill-climber stops at the top of whatever hill it starts on. That is a **local** best, which may not be the **global** best. Both runs report "Solver found a solution." So with GRG:
- Starting values are now part of the model. Start near a sensible guess.
- Solve from several starting points (or tick Use Multistart, which needs bounds). Same answer from all starts = more confidence.
- Compare against a quick table of the objective at several decision values (a sanity grid).

## 5. Example 1: Northampton Cycle Works (smooth, GRG)

Choose price and quantity. Demand: units = 3,000 - 2 x price. Unit cost = $500 + $0.50 x units. Fixed cost $150,000/month. Capacity 700 units; price at least $900.

- Objective: `=Price*Units - (500 + 0.5*Units)*Units - 150000`.
- Keep both price and units as decisions; link them with a constraint. Put the gap in one cell, `=Units - (3000 - 2*Price)`, and constrain `Demand_Gap = 0`. Easier to audit than typing the equation into the dialog.
- GRG Nonlinear. Answer: price $1,250, 500 units, $100,000 profit. Capacity and the price floor are NOT binding: the best answer is an interior peak, not a corner (new compared with LPs). Every starting point lands on the same answer: one smooth hill.

## 6. Example 2: Saucon Valley Fabricators (cliffs, Evolutionary)

One decision Q (units). Margin $85/unit. Regular shift $18,000 covers up to 400 units. Second shift: a flat $22,000 the moment Q exceeds 400. Overtime: $100 per unit above 700. Q between 250 and 900.

- Objective: `=85*Q - 18000 - IF(Q>400, 22000, 0) - 100*MAX(0, Q-700)`.
- Profit: 400 units -> $16,000 (local peak); 401 -> -$5,915 (the cliff); 700 -> $19,500 (global peak); 900 -> $16,500.
- GRG started at or below 400 stops at 400; started at 450+ reaches 700. Both report success. Evolutionary with bounds 250..900 finds 700.
- Break-even for opening the second shift is about 659 units. Solver never prints that; comparing the two peaks does. The model gives the answer; the analyst produces the insight.

## 7. The four-step choice and validation checklist

1. Is every formula a parameter times a decision, added up? -> Simplex LP.
2. Smooth curve? -> GRG Nonlinear, from several starts.
3. Cliffs, steps, IF/MAX/lookups on decisions? -> Evolutionary with bounds (or GRG multistart).
4. Whatever you pick, validate.

Validation checklist:
- Re-solve from at least two other starting values.
- Tabulate the objective over a range of decision values and plot it.
- Check the answer against common sense (does raising a cost lower profit?).
- Check constraints are actually met at the answer.
- Report the answer with appropriate rounding; nonlinear answers near a flat top are only good to a few significant digits.
- Say in the memo that a better answer is not ruled out unless the model is linear.
