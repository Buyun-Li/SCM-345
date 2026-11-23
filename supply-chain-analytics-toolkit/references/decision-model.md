# Building a decision model (the anatomy)

Every model in this toolkit, from a product mix to a neural network fit, answers three questions:

1. **What are we trying to achieve?** The objective: one number to maximize or minimize.
2. **What are we allowed to do?** The constraints: rules every plan must obey.
3. **What do we get to choose?** The decision variables: cells you (or Solver) change.

Plus the **parameters**: the given numbers that feed the other three.

Most bad business models are not bad arithmetic. They are a clear, confident answer to the wrong question. Ask these three before typing.

## Contents
1. Triage: pulling the model out of a messy description
2. Traps that catch most people
3. The canonical form (writing the model in words, then as formulas)
4. Three checks before Excel
5. From canonical form to spreadsheet
6. Worked example: the woodshop

---

## 1. Triage

Read the situation and sort every fact into one of five boxes: Objective, Decision variable, Constraint, Parameter, **Not in the model**. Real briefings are mostly noise (last year's revenue, a competitor's price, someone's preference, the reason a rule exists).

Tests:
- **Decision vs parameter:** could the decision-maker change it this period? If yes, it is a decision. If it arrives as a fact, it is a parameter. (Price is a decision when the company "has not settled on one".)
- **Constraint vs parameter:** a constraint is a RULE with a decision in it ("lumber used must not exceed 900"). The 900 by itself is a parameter. Same resource, two roles.
- **Objective vs constraint:** a requirement ("cover every shift") is a constraint; the thing that discriminates between plans that meet it (cost) is the objective. If coverage were the objective, every legal schedule would look equally good.
- **Not in the model:** facts that do not change with the decision. A fixed cost paid either way cannot change which plan is cheapest. A result of a past decision (last month's bill) is read by nothing.

## 2. Traps

- **The benchmark trap.** "The owner wants at least $4,000 profit" is not a constraint when profit is already being maximized. It is a benchmark to check the answer against. If the best plan makes less, that finding is the news.
- **Two objectives.** A model has exactly one objective. Every other goal becomes a constraint (or a priced penalty; see simulation-optimization.md section on two goals).
- **Direction of the sign.** Capacities are `<=`. Contracts and minimums are `>=`. "Exactly" is `=`. An `=` where `<=` belongs is the most expensive single error (it often makes the model infeasible).
- **Units.** "2 tank-weeks per thousand cases" must be converted. Averages must become totals (see blending in linear-programming.md).
- **The rule nobody writes down.** "One person, one job" or "each auditor takes at most one engagement" is obvious to a human and invisible to Solver. Leave it out and Solver will clone your best employee.

## 3. The canonical form

Fill this four-column table, the plain-English column first for every row, before writing any formula.

| Row | In plain English | Written as a formula | `<=` `=` `>=` | How many lines? |
|---|---|---|---|---|
| Objective | Maximize total profit for the month | `SUMPRODUCT(Unit_Profit, Build)` | max | 1 |
| Constraint 1 | Lumber used cannot exceed what is in the back | `SUMPRODUCT(Lumber_Per_Unit, Build)` vs `900` | <= | 1 |
| ... | | | | |

Column guidance:
- **In plain English:** one sentence a plant manager would nod at. No symbols.
- **Formula:** only names you defined. Decisions on the left of the sign, the limit on the right. Two accepted styles: "SUM of profit(j) * build(j) over all products j" or `SUMPRODUCT(profit, build)`. No sigma signs, no subscripts.
- **Sign:** allowed to use less? `<=`. Must deliver at least? `>=`. Must land exactly? `=`.
- **How many lines:** a line with a free index stands for one constraint per value ("for every plant" with 3 plants = 3 lines). This tells you how many rows the calculation block needs.

## 4. Three checks before Excel

1. Units match on both sides of every line.
2. Every decision the business actually makes appears somewhere.
3. No line without a decision variable in it. "We have 19,200 lb" is an input; "what we use is at most 19,200 lb" is a constraint.

## 5. From canonical form to spreadsheet

- Grey input block holds every parameter.
- Yellow decision block, same shape as the decision (a row for a product mix, a grid for shipping lanes or person-by-job).
- Green calculation block: one cell per constraint left-hand side (`=SUMPRODUCT(Lumber_Per_Unit, Build)`), next to its limit.
- Cream objective cell.
- Name everything Solver reads. Then the Solver dialog reads like the canonical form.

## 6. Worked example: the woodshop

A shop makes bookcases, desks and coffee tables. 900 board-feet of lumber and 300 labor hours this month. Per unit: bookcase 12 bd-ft, 3 hr, $60 profit; desk 16, 5, $90; table 8, 2, $45. A contract requires at least 10 desks; the market takes at most 30 tables. Owner wants at least $4,000 profit.

- Decisions: B, D, C = units of each to build.
- Objective: maximize 60B + 90D + 45C.
- Constraints: lumber 12B + 16D + 8C <= 900; labor 3B + 5D + 2C <= 300; D >= 10; C <= 30; all >= 0.
- Not a constraint: the $4,000 (benchmark).
- Answer: $5,062.50 (lumber binding, labor has 33.75 hours to spare). The plan is not unique: 56.25 desks, or 41.25 desks + 30 tables, both earn $5,062.50 because desks and tables earn the same $5.625 per board-foot. With whole numbers: $5,055 (for example 1 bookcase, 55 desks, 1 table).
- The sentence to the manager: "We clear the $4,000 target by about $1,060. We are short of wood, not people: overtime buys nothing, more lumber buys up to $5.63 a board-foot."
