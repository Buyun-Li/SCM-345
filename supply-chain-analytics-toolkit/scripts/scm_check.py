"""
scm_check.py - independent Python checks for SCM-345-style Excel models.

Use these to produce a CHECK FIGURE before handing a workbook to the user:
solve the same model in Python, then tell the user what Solver should return.
Every function mirrors what the Excel model does, using Excel's conventions.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from scm_check import *
"""
import math
import numpy as np


# ------------------------------------------------------------------ LP / IP
def solve_lp(objective, constraints, sense="max", bounds=None, integer=None,
             names=None, cons_names=None):
    """Solve a linear (or integer) program the way Solver's Simplex LP would.

    objective:   list of coefficients, one per decision variable
    constraints: list of (coefficients, relation, rhs) with relation in
                 '<=', '>=', '='
    sense:       'max' or 'min'
    bounds:      list of (low, high) per variable; default (0, None) = Solver's
                 "Make Unconstrained Variables Non-Negative"
    integer:     list of True/False per variable (or True for all)

    Returns dict with x, objective, and for an LP (no integers) the
    Sensitivity-Report numbers in EXCEL'S sign convention:
        shadow_price[i] = change in objective per +1 unit of constraint i's rhs
        reduced_cost[j] = change in objective per unit of variable j forced in
    """
    from scipy.optimize import linprog, milp, LinearConstraint, Bounds
    c = np.asarray(objective, float)
    n = len(c)
    sgn = -1.0 if sense == "max" else 1.0
    bounds = bounds or [(0, None)] * n
    A_ub, b_ub, A_eq, b_eq, kinds = [], [], [], [], []
    for coefs, rel, rhs in constraints:
        coefs = np.asarray(coefs, float)
        if rel == "<=":
            A_ub.append(coefs); b_ub.append(rhs); kinds.append(("ub", len(A_ub) - 1, 1.0))
        elif rel == ">=":
            A_ub.append(-coefs); b_ub.append(-rhs); kinds.append(("ub", len(A_ub) - 1, -1.0))
        elif rel == "=":
            A_eq.append(coefs); b_eq.append(rhs); kinds.append(("eq", len(A_eq) - 1, 1.0))
        else:
            raise ValueError(rel)
    if integer is True:
        integer = [True] * n
    out = {"names": names, "constraint_names": cons_names}
    if integer and any(integer):
        lo = np.array([b[0] if b[0] is not None else -np.inf for b in bounds])
        hi = np.array([b[1] if b[1] is not None else np.inf for b in bounds])
        cons = []
        if A_ub:
            cons.append(LinearConstraint(np.array(A_ub), -np.inf, np.array(b_ub)))
        if A_eq:
            cons.append(LinearConstraint(np.array(A_eq), np.array(b_eq), np.array(b_eq)))
        r = milp(sgn * c, constraints=cons, integrality=np.array(integer, int),
                 bounds=Bounds(lo, hi))
        out.update(status=r.message, x=r.x, objective=None if r.x is None else float(c @ r.x))
        out["note"] = "Integer model: Excel gives NO Sensitivity Report. Re-solve to price a change."
        return out
    r = linprog(sgn * c, A_ub=np.array(A_ub) if A_ub else None, b_ub=b_ub or None,
                A_eq=np.array(A_eq) if A_eq else None, b_eq=b_eq or None,
                bounds=bounds, method="highs")
    out.update(status=r.message, x=r.x)
    if r.status != 0:
        out["objective"] = None
        out["diagnosis"] = {2: "INFEASIBLE - no plan satisfies every constraint",
                            3: "UNBOUNDED - a constraint is missing"}.get(r.status, r.message)
        return out
    out["objective"] = float(c @ r.x)
    sp = []
    for kind, idx, flip in kinds:
        m = r.ineqlin.marginals[idx] if kind == "ub" else r.eqlin.marginals[idx]
        sp.append(float(sgn * m * flip))     # back to Excel sign convention
    out["shadow_price"] = sp
    used = []
    for coefs, rel, rhs in constraints:
        used.append(float(np.dot(coefs, r.x)))
    out["used"] = used
    out["slack"] = [abs(rhs - u) for (_, _, rhs), u in zip(constraints, used)]
    out["binding"] = [s < 1e-7 for s in out["slack"]]
    # reduced cost: (objective coef) - (resources it uses priced at shadow prices)
    A = np.array([np.asarray(co, float) for co, _, _ in constraints])
    out["reduced_cost"] = [float(c[j] - np.dot(A[:, j], sp)) if abs(r.x[j]) < 1e-9 else 0.0
                           for j in range(n)]
    return out


def resolve_change(objective, constraints, which, delta, **kw):
    """Re-solve with constraint `which` rhs moved by delta; return objective change.
    This is the experiment a shadow price summarizes (and the honest check
    when a change falls outside the allowable range)."""
    base = solve_lp(objective, constraints, **kw)["objective"]
    cons = [list(t) for t in constraints]
    cons[which][2] = cons[which][2] + delta
    new = solve_lp(objective, [tuple(t) for t in cons], **kw)["objective"]
    return None if (base is None or new is None) else new - base


def allowable_range(objective, constraints, which, step=1.0, max_steps=10000, **kw):
    """Find how far a constraint's rhs can move before its shadow price changes
    (Allowable Increase / Decrease), by repeated re-solves."""
    sp0 = solve_lp(objective, constraints, **kw)["shadow_price"][which]

    def sp_at(d):
        cons = [list(t) for t in constraints]
        cons[which][2] += d
        r = solve_lp(objective, [tuple(t) for t in cons], **kw)
        return None if r["objective"] is None else r["shadow_price"][which]

    res = {}
    for direction, key in ((1, "allowable_increase"), (-1, "allowable_decrease")):
        lo, hi = 0.0, None
        d = step
        for _ in range(max_steps):
            s = sp_at(direction * d)
            if s is None or abs(s - sp0) > 1e-7:
                hi = d
                break
            lo = d
            d *= 2
        if hi is None:
            res[key] = math.inf
            continue
        for _ in range(60):
            mid = (lo + hi) / 2
            s = sp_at(direction * mid)
            if s is not None and abs(s - sp0) <= 1e-7:
                lo = mid
            else:
                hi = mid
        res[key] = round(lo, 4)
    return res


# ------------------------------------------------------------ simulation
def excel_skew(x):
    """Excel's SKEW (sample-adjusted)."""
    x = np.asarray(x, float)
    n = len(x)
    s = x.std(ddof=1)
    if n < 3 or s == 0:
        return 0.0
    return float(n / ((n - 1) * (n - 2)) * np.sum(((x - x.mean()) / s) ** 3))


def summary(values, below=None, above=None, budget=None):
    """The course's summary block for a column of simulated outcomes.
    Returns AVERAGE, MEDIAN, STDEV.S, SKEW, PERCENTILE.INC 5% and 95%, the
    chance of a loss (value < 0), optional chances below/above thresholds,
    and the report rule: skewness outside -1.5..1.5 -> report the median."""
    v = np.asarray(values, float)
    sk = excel_skew(v)
    out = {
        "average": float(v.mean()),
        "median": float(np.median(v)),
        "stdev": float(v.std(ddof=1)),
        "skewness": sk,
        "p5": float(np.percentile(v, 5)),      # numpy 'linear' == PERCENTILE.INC
        "p95": float(np.percentile(v, 95)),
        "chance_below_0": float(np.mean(v < 0)),
        "report": "Median" if (sk > 1.5 or sk < -1.5) else "Average",
    }
    if below is not None:
        out[f"chance_below_{below}"] = float(np.mean(v < below))
    if above is not None:
        out[f"chance_above_{above}"] = float(np.mean(v > above))
    if budget is not None:
        out["chance_over_budget"] = float(np.mean(v > budget))
    return out


def discrete_sampler(values, chances, rng):
    """Mirror of VLOOKUP(RAND(), table_with_'Starts at'_column, 2, TRUE)."""
    starts = np.concatenate([[0.0], np.cumsum(chances)[:-1]])
    def draw(size):
        u = rng.random(size)
        idx = np.searchsorted(starts, u, side="right") - 1
        return np.asarray(values)[idx]
    return draw


def normal_whole(rng, mean, sd, size):
    """Mirror of MAX(0, ROUND(NORM.INV(RAND(), mean, sd), 0))."""
    return np.maximum(0, np.round(rng.normal(mean, sd, size)))


def critical_ratio(cost_short, cost_long):
    """Newsvendor shortcut: order at this percentile of demand.
    cost_short = what one unit too few costs; cost_long = one unit too many."""
    return cost_short / (cost_short + cost_long)


def sim_optimize(cost_fn, sample, lo, hi, integer=True):
    """Simulation optimization on FROZEN sample paths: the decision minimizing
    average cost_fn(decision, sample). Scans then refines (cost curves here
    are piecewise-flat, so a scan is more reliable than a gradient search)."""
    grid = np.linspace(lo, hi, 401)
    vals = [np.mean(cost_fn(q, sample)) for q in grid]
    k = int(np.argmin(vals))
    a, b = grid[max(k - 1, 0)], grid[min(k + 1, len(grid) - 1)]
    fine = np.arange(math.floor(a), math.ceil(b) + 1) if integer else np.linspace(a, b, 2001)
    fv = [np.mean(cost_fn(q, sample)) for q in fine]
    j = int(np.argmin(fv))
    return float(fine[j]), float(fv[j])


# ------------------------------------------------------------ forecasting
def error_measures(actual, forecast):
    """Course convention: error = forecast - actual (positive = forecast too high).
    MAPE divides by ACTUAL. Pairs where either value is missing are skipped."""
    a = np.asarray(actual, float)
    f = np.asarray(forecast, float)
    ok = ~(np.isnan(a) | np.isnan(f))
    a, f = a[ok], f[ok]
    e = f - a
    return {
        "n": int(len(e)),
        "ME_bias": float(e.mean()),
        "MAD": float(np.abs(e).mean()),
        "MSE": float((e ** 2).mean()),
        "RMSE": float(math.sqrt((e ** 2).mean())),
        "MAPE": float((np.abs(e) / a).mean()),
        "SSE": float((e ** 2).sum()),
    }


def moving_average(y, window):
    """Forecast for period t = average of the `window` periods before t.
    First `window` periods have no forecast (NaN), like the empty top rows."""
    y = np.asarray(y, float)
    f = np.full(len(y), np.nan)
    for t in range(window, len(y)):
        f[t] = y[t - window:t].mean()
    return f


def wma_trend_season_forecast(y, weights, trend, indices, season_of):
    """forecast(t) = (SUMPRODUCT(weights, last k actuals) + trend) * index(season of t)
    weights[0] applies to the OLDEST period in the window (k periods back),
    weights[-1] to the most recent - same left-to-right order as the
    SUMPRODUCT over the rows just above t."""
    y = np.asarray(y, float)
    k = len(weights)
    f = np.full(len(y), np.nan)
    for t in range(k, len(y)):
        base = float(np.dot(weights, y[t - k:t]))
        f[t] = (base + trend) * indices[season_of[t]]
    return f


def fit_wma_trend_season(y, k, n_seasons, season_of, score_from=None,
                         index_floor=0.2, trend_start=None, starts=12, seed=0):
    """Mirror the course Solver run: minimize RMSE by changing k weights,
    one trend term and n_seasons indices, subject to weights >= 0 summing
    to 1 and indices >= index_floor summing to n_seasons (GRG Nonlinear).
    Uses several starting points, because the surface has local minima."""
    from scipy.optimize import minimize
    y = np.asarray(y, float)
    score_from = k if score_from is None else score_from
    rng = np.random.default_rng(seed)

    def rmse(p):
        w, tr, idx = p[:k], p[k], p[k + 1:]
        f = wma_trend_season_forecast(y, w, tr, idx, season_of)
        e = f[score_from:] - y[score_from:]
        return math.sqrt(np.nanmean(e ** 2))

    if trend_start is None:
        # lag of an equal-weight window ((k+1)/2 periods) x average growth per period
        trend_start = (k + 1) / 2 * (y[-1] - y[0]) / (len(y) - 1)
    cons = [{"type": "eq", "fun": lambda p: p[:k].sum() - 1},
            {"type": "eq", "fun": lambda p: p[k + 1:].sum() - n_seasons}]
    bnds = [(0, 1)] * k + [(None, None)] + [(index_floor, None)] * n_seasons
    best = None
    for s in range(starts):
        w0 = np.full(k, 1 / k) if s == 0 else rng.dirichlet(np.ones(k))
        i0 = np.ones(n_seasons) if s == 0 else rng.uniform(0.8, 1.2, n_seasons)
        i0 = i0 * n_seasons / i0.sum()
        p0 = np.concatenate([w0, [trend_start], i0])
        r = minimize(rmse, p0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 2000, "ftol": 1e-12})
        if best is None or r.fun < best.fun:
            best = r
    p = best.x
    return {"weights": p[:k], "trend": float(p[k]), "indices": p[k + 1:], "rmse": float(best.fun)}


# ------------------------------------------------------------ regression
def fit_linear(X, y):
    """Least squares: the numbers Solver should find when it minimizes the
    sum of squared misses. Returns constant (starting point), rates, SSE,
    typical miss (RMSE) and R-squared = 1 - SSE / DEVSQ(actual)."""
    X = np.atleast_2d(np.asarray(X, float))
    if X.shape[0] != len(y):
        X = X.T
    y = np.asarray(y, float)
    A = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    pred = A @ beta
    sse = float(((y - pred) ** 2).sum())
    devsq = float(((y - y.mean()) ** 2).sum())
    return {"constant": float(beta[0]), "rates": beta[1:].tolist(), "SSE": sse,
            "typical_miss_RMSE": math.sqrt(sse / len(y)), "R2": 1 - sse / devsq,
            "predicted": pred}


def fit_logistic(X, y):
    """Maximum likelihood logistic regression - what Solver finds when it
    MAXIMIZES the sum of LN(chance of what actually happened)."""
    from scipy.optimize import minimize
    X = np.atleast_2d(np.asarray(X, float))
    if X.shape[0] != len(y):
        X = X.T
    y = np.asarray(y, float)
    A = np.column_stack([np.ones(len(y)), X])

    def negll(b):
        z = A @ b
        p = 1 / (1 + np.exp(-z))
        p = np.clip(p, 1e-12, 1 - 1e-12)
        return -np.sum(np.where(y == 1, np.log(p), np.log(1 - p)))

    r = minimize(negll, np.zeros(A.shape[1]), method="BFGS")
    b = r.x
    p = 1 / (1 + np.exp(-(A @ b)))
    return {"constant": float(b[0]), "rates": b[1:].tolist(),
            "total_log": float(-r.fun),
            "coin_flip_total_log": float(len(y) * math.log(0.5)),
            "called_right": int(np.sum((p >= 0.5) == (y == 1))),
            "always_majority_right": int(max(y.sum(), len(y) - y.sum())),
            "chance": p}


# ------------------------------------------------------------ neural net
def softplus(z):
    return np.log1p(np.exp(-np.abs(z))) + np.maximum(z, 0)


def logistic(z):
    return 1 / (1 + np.exp(-z))


def fit_course_network(X, y, h1=2, h2_acts=("softplus", "softplus", "logistic"),
                       bound=5.0, starts=20, seed=0):
    """The class network: inputs -> h1 linear neurons -> len(h2_acts) neurons
    with the given activations -> one linear output. Hidden weights and
    constants bounded to +/-bound (as in the Solver set-up); output layer free.
    Minimizes the sum of squared misses from several starting points.
    X should already be rescaled (each column divided by a round number near
    its maximum)."""
    from scipy.optimize import minimize
    X = np.atleast_2d(np.asarray(X, float))
    if X.shape[0] != len(y):
        X = X.T
    y = np.asarray(y, float)
    n_in, h2 = X.shape[1], len(h2_acts)
    sizes = [(n_in + 1) * h1, (h1 + 1) * h2, h2 + 1]
    acts = {"softplus": softplus, "logistic": logistic, "linear": lambda z: z}

    def unpack(p):
        a = p[:sizes[0]].reshape(h1, n_in + 1)
        b = p[sizes[0]:sizes[0] + sizes[1]].reshape(h2, h1 + 1)
        c = p[sizes[0] + sizes[1]:]
        return a, b, c

    def predict(p, X=X):
        a, b, c = unpack(p)
        s = X @ a[:, :n_in].T + a[:, n_in]
        z = s @ b[:, :h1].T + b[:, h1]
        hz = np.column_stack([acts[h2_acts[k]](z[:, k]) for k in range(h2)])
        return hz @ c[:h2] + c[h2]

    def sse(p):
        return float(((y - predict(p)) ** 2).sum())

    rng = np.random.default_rng(seed)
    bnds = [(-bound, bound)] * (sizes[0] + sizes[1]) + [(None, None)] * sizes[2]
    best = None
    for _ in range(starts):
        p0 = np.concatenate([rng.uniform(-1, 1, sizes[0] + sizes[1]),
                             rng.normal(0, y.std() + 1e-9, sizes[2])])
        p0[-1] = y.mean()
        r = minimize(sse, p0, method="L-BFGS-B", bounds=bnds, options={"maxiter": 5000})
        if best is None or r.fun < best.fun:
            best = r
    lin = fit_linear(X, y)
    return {"SSE": float(best.fun), "params": best.x,
            "typical_miss": math.sqrt(best.fun / len(y)),
            "R2": 1 - best.fun / float(((y - y.mean()) ** 2).sum()),
            "straight_line_SSE": lin["SSE"], "n_weights": sizes,
            "predict": lambda Xn: predict(best.x, np.atleast_2d(np.asarray(Xn, float)))}


# ------------------------------------------------------------ KNN
def knn_forecast(target, peers, outcomes, include, k):
    """Scaled distance = SUMPRODUCT(Include, ((target - peer) / target)^2);
    forecast = average outcome of the k nearest peers."""
    t = np.asarray(target, float)
    P = np.asarray(peers, float)
    inc = np.asarray(include, float)
    d = (((t - P) / t) ** 2 * inc).sum(axis=1)
    order = np.argsort(d)
    nearest = order[:k]
    return {"distances": d, "nearest": nearest.tolist(),
            "forecast": float(np.asarray(outcomes, float)[nearest].mean()),
            "nearest_distance": float(d[order[0]])}


def correlations(columns, outcome):
    """CORREL of each candidate column with the outcome (step 2 screen)."""
    return [float(np.corrcoef(np.asarray(c, float), np.asarray(outcome, float))[0, 1])
            for c in columns]
