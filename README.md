# SCM 345 Supply Chain Analytics Toolkit (a Claude skill)

A Claude skill for students of **SCM 345: Analytics for Supply Chain Management** (Lehigh University, Fall 2026). It helps you build and explain the spreadsheet models from the course, in Excel, the same way we built them in class.

## What it can help with

| Module | Models |
|---|---|
| Decision models | objective, decision variables, constraints, parameters; the canonical form |
| 1 Optimization | linear programs (product mix, blending, transportation, assignment, scheduling), integer and binary models, sensitivity reports, nonlinear models (GRG Nonlinear vs Evolutionary) |
| 2 Uncertainty | Monte Carlo simulation, data tables, summary statistics, simulation optimization, min-max, pricing a rule you cannot keep, two goals, dashboards with a recorded macro |
| 3 Prediction | error measures (bias, MAD, RMSE, MAPE), moving average, weighted moving average, with trend and seasonality, nearest neighbors, linear and logistic regression, a simple neural network |

The first time you ask for help, it asks whether you want to be **coached** (you build it yourself, step by step) or want it to **build** a finished, checked Excel workbook for you.

## Install

1. Download [`dist/supply-chain-analytics-toolkit.zip`](dist/supply-chain-analytics-toolkit.zip).
2. In Claude, open Settings and find the Skills section, then upload the zip. (Code execution needs to be turned on for Claude to build workbooks.)
3. Ask a question in plain words, for example: *"We have three plants and four warehouses; help me find the cheapest shipping plan"* or *"Forecast next quarter's orders from these 12 quarters of history."*

The source for the skill is in [`supply-chain-analytics-toolkit/`](supply-chain-analytics-toolkit/): `SKILL.md` is the main instruction file, `references/` holds one guide per method, and `scripts/` holds the helpers Claude uses to check answers and build workbooks.

## Academic integrity

If you are taking a course whose AI policy does not allow giving an assignment file to an AI tool, follow that policy. Describe the problem in your own words, and the skill will coach you rather than build the deliverable. Disclose any AI help your course asks you to disclose.

## License

MIT, see [LICENSE](LICENSE).
