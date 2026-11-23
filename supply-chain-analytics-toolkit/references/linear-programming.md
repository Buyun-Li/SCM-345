# Linear programs (Simplex LP)

## Contents
1. Is it linear? The one test
2. Three outcomes and what they mean
3. Three properties worth knowing
4. The classic shapes: product mix, blending, transportation, assignment, scheduling, multiperiod
5. Whole numbers (int and bin)
6. Reading the Sensitivity Report
7. Writing the recommendation

---

## 1. Is it linear?

**Could you build every formula with only multiply-by-a-number and add?** Each term must be a parameter times a decision, added up. If any formula multiplies a decision by a decision (price x quantity), divides by a decision, or uses IF, MAX, MIN, ABS, ROUND or a lookup on a decision, it is not linear: see nonlinear-optimization.md.

Linear means Solver's **Simplex LP** engine applies, and it comes with a guarantee: the answer it reports is the best possible, and it always finishes, fast.

## 2. Three outcomes

| Solver says | Meaning | Usual cause |
|---|---|---|
| Solver found a solution. All constraints and optimality conditions are satisfied. | Optimal | |
| Solver could not find a feasible solution. | Infeasible: the rules contradict each other | A sign pointing the wrong way; `=` where `<=` belongs (supply bigger than demand); a requirement larger than capacity. The business finding may be real: "the contract cannot be met." |
| The Objective Cell values do not converge. | Unbounded: profit can grow forever | A missing limit, usually a capacity constraint left out of the dialog |

## 3. Three properties

- **The answer sits on a corner** of the region of allowed plans. With two decisions you can draw it: each constraint is a line, the allowed region is where all are satisfied, and the best plan is a corner.
- **Something is always binding.** At least one constraint is used to the limit; that is the bottleneck. Others have slack (unused capacity).
- **Ties happen.** When two products earn the same per unit of the bottleneck, many plans give the same best profit. Compare the objective value, not the plan.

The yardstick for which product wins is **margin per unit of the scarce resource**, not margin per unit. (Desk $90 / 16 bd-ft = $5.625; table $45 / 8 = $5.625: a tie.)

## 4. The classic shapes

### Product mix (maximize profit, products compete for shared resources)
- Decisions: units of each product.
- Constraints: SUMPRODUCT(resource per unit, Build) <= available, one per resource; Build <= demand ceiling; contracts as >=.
- Example (Blue Mountain Outfitters): daypack $35, duffel $32, vest $18; cutting 0.4/0.3/0.8 hr of 400; sewing 1.4/0.8/1.0 of 900; fabric 2.1/2.2/2.0 yd of 1,600. Answer 500 daypacks, 250 duffels, 0 vests, $25,500.

### Blending (minimize cost of a mix that meets specs)
- Decisions: amount of each ingredient or supplier.
- Spec constraints are written as **totals**, not averages: "average body at least 6.4 across 1,000 lb" becomes `SUMPRODUCT(Body_Score, Pounds) >= 6400`.
- **The ratio trap.** "No supplier above 40% of the order" written as `one supplier / total <= 0.40` divides by decisions and is not linear. Multiply through: `one supplier <= 0.40 * total`. With a fixed total of 40,000 that is simply `<= 16,000`.
- Example (Keystone Grounds): GreenStart $18/bag (N 20, P 5, K 2), RootBuilder $12/bag (N 10, P 10, K 6); need N >= 120, P >= 60, K >= 20. Answer 4 and 4 bags, $120; potassium never binds (relaxing it is worth nothing).

### Transportation (ship from sources to destinations at least cost)
- Decision is a **grid**: rows = sources, columns = destinations, same shape as the cost grid. Total cost = `SUMPRODUCT(Cost, Ship)`.
- Row totals (shipped out of each source) `<= Supply`; column totals (received at each destination) `= Demand` (or `>=`).
- **If supply exceeds demand, supply rows must be `<=`.** Writing them as `=` is infeasible.
- Two constraint lines in Solver, not seven: `Shipped_Out <= Supply`, `Received = Demand`.
- Expect a sparse answer (about sources + destinations - 1 lanes used), destinations split across sources, and the cheapest single lane sometimes unused: a source's capacity goes where its advantage over the next-best source is largest.
- **Transshipment:** add the middle layer; each middle node gets a flow-balance constraint, "what comes in must go out."

### Assignment (people to jobs, machines to orders)
- Decision grid of 0/1 values (`bin`).
- Coverage, for every job: column total `= Required` headcount.
- One job each, for every person: row total `= 1`, or `<= 1` when there are more people than seats.
- Maximize total skill (or minimize total cost) = `SUMPRODUCT(Skill, Assign)`.
- The answer is decided by **comparative advantage**: the gap to the next-best person, not who is best. Delete the one-job-each rule and Solver puts the star on every job at once.

### Shift scheduling (days off / coverage)
- Decision: how many people START each shift (or each day, for five-consecutive-days patterns).
- One coverage constraint per period: everyone whose shift includes that period, added up, `>= Required`. A single decision appears in several coverage rows; build each row's on-duty formula carefully.
- Integer. Several start patterns often tie; compare headcount and cost.

### Multiperiod production and inventory
- Decisions per month: production (regular, overtime), possibly ending inventory.
- The linking constraint: `ending inventory = starting inventory + production - demand`, month by month (last month's ending is this month's starting).
- Objective: production cost + overtime cost + holding cost on ending inventory.

## 5. Whole numbers

- Add `Build = integer` (pick `int` in the Add Constraint drop-down) or `Assign = binary` (`bin`). Keep Simplex LP selected.
- Rounding an LP answer can be infeasible (round up) or leave money on the table (round down). Woodshop: LP $5,062.50 at 56.25 desks; round up infeasible; round down $5,040; true whole-number best $5,055 with a completely different mix.
- Force whole numbers when a fraction is meaningless (trucks, crews, people), not when it is just untidy.
- Integer models are slower and **give no Sensitivity Report**. Working habit: solve as an LP first, read the economics, then add `int` for the buildable plan. To price a change in an integer model, re-solve.

## 6. Reading the Sensitivity Report

Tick Sensitivity in the Solver Results dialog before OK. Two tables:

**Variable Cells:** Final Value | Reduced Cost | Objective Coefficient | Allowable Increase | Allowable Decrease
**Constraints:** Final Value | Shadow Price | Constraint R.H. Side | Allowable Increase | Allowable Decrease

| Manager's question | Where the answer is |
|---|---|
| What is one more unit of this resource worth? | **Shadow price** of that constraint |
| What is the most I should pay for more? | The shadow price is the ceiling (above it, the deal loses money) |
| For how many extra units does that price hold? | **Allowable increase** of that constraint |
| Should we buy more of a resource we are not using up? | No: a non-binding constraint has shadow price 0 |
| Why don't we make product X, and what price would change that? | **Reduced cost** of X: it enters once its margin rises by that amount |
| How wrong can a profit estimate be before the plan changes? | Objective coefficient's allowable increase/decrease |

Key ideas, taught as experiments first:
- **A shadow price is a re-solve you did not have to do.** Raise the limit by 1, solve again, subtract. Woodshop lumber 900 -> 901 moves profit $5,062.50 -> $5,068.125: $5.625 per board-foot.
- **It only holds inside the allowable range.** Past the wall, re-solve: the rate usually drops (Blue Mountain fabric is worth $12/yd for 875 more yards; past that the extra yards earn nothing because sewing becomes the only bottleneck).
- **Free consistency checks:** a non-binding constraint has shadow price 0, allowable increase 1E+30 (infinity), and allowable decrease equal to its slack.
- **Negative shadow price on a minimum requirement** (a contract `>=`): each extra required unit costs that much profit. Ask the customer for at least that much more per unit.
- **Reduced cost** of a product not made is negative in a max problem: its margin minus the value of the resources it would consume. Bookcase reduced cost -$7.50 means it enters when its margin passes $60 + $7.50 = $67.50.
- **Zeros where you expected numbers** (reduced cost 0 on a product at 0, an allowable increase of 0) signal a tie: alternative optimal plans exist.
- The report answers **one change at a time**; for two simultaneous changes, re-solve.

## 7. Writing the recommendation

State the plan and the profit/cost first, then the bottleneck in money terms, then what not to buy. Example register: "Build 500 daypacks and 250 duffels for $25,500 a week. Sewing time is worth $7 an hour and fabric $12 a yard, so take the overtime offer at $5 an hour for up to about 167 hours; cutting has 125 idle hours, so do not add cutting capacity."
