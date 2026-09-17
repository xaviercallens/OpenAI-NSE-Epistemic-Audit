//! Aggregate forced-collapse runs into experiments/results/kinetic_lock_collapse.json.
//! Usage: collapse_analyze --main a.json ... [--fine b.json ...] [--fixn c.json ...] [--extra d.json ...]
//!                         [--gates gates.json] --out file
//! Every verdict below is computed from the run arrays; nothing is hardcoded except the
//! directive's thresholds (lag > 10%, negativity <= 1e-6 of mass) and sqrt(pi/2).

use kinetic_lock_rs::stats::{ols, t_crit_95};
use nalgebra::{DMatrix, DVector};
use serde_json::{json, Value};
use std::f64::consts::PI;

const LAG_ARREST: f64 = 0.10;
const NEG_TOL: f64 = 1e-6;

fn arr(v: &Value, k: &str) -> Vec<f64> {
    v[k].as_array().unwrap_or_else(|| panic!("missing series {k}")).iter().map(|x| x.as_f64().unwrap_or(f64::NAN)).collect()
}

fn collect_args(flag: &str) -> Vec<String> {
    let a: Vec<String> = std::env::args().collect();
    let Some(i) = a.iter().position(|x| x == flag) else { return vec![] };
    a[i + 1..].iter().take_while(|x| !x.starts_with("--")).cloned().collect()
}

fn interp(ts: &[f64], ys: &[f64], t: f64) -> f64 {
    if t <= ts[0] {
        return ys[0];
    }
    for i in 1..ts.len() {
        if ts[i] >= t {
            let a = (t - ts[i - 1]) / (ts[i] - ts[i - 1]);
            return ys[i - 1] + a * (ys[i] - ys[i - 1]);
        }
    }
    *ys.last().unwrap()
}

/// Arrest metrics of one run.
fn analyze_run(path: &str) -> Value {
    let d: Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    let c = &d["config"];
    let lam = c["lambda"].as_f64().unwrap();
    let k = &d["kinetic"];
    let (t, lt, lref, lkin, lag) = (arr(k, "t"), arr(k, "ell_target"), arr(k, "ell_ref"), arr(k, "ell_kin"), arr(k, "lag"));
    let (kw, kwr, ma, kn) = (arr(k, "k_omega"), arr(k, "k_omega_ref"), arr(k, "mach"), arr(k, "kn"));
    let (drho, noneq, h, neg) = (arr(k, "max_abs_rho_minus_1"), arr(k, "noneq_fraction"), arr(k, "H"), arr(k, "negative_mass_fraction"));
    let (mbal, mdrift) = (arr(k, "momentum_balance_residual"), arr(k, "mass_drift"));
    let lwin = arr(k, "ell_kin_window6");
    let lpeak = arr(k, "ell_kin_peak");
    let n = t.len();
    let i_min = (0..n).min_by(|&a, &b| lkin[a].partial_cmp(&lkin[b]).unwrap()).unwrap();
    let i_lag = (0..n).find(|&i| lag[i] > LAG_ARREST);
    let i_min_win = (0..n).min_by(|&a, &b| lwin[a].partial_cmp(&lwin[b]).unwrap()).unwrap();
    let i_min_peak = (0..n).min_by(|&a, &b| lpeak[a].partial_cmp(&lpeak[b]).unwrap()).unwrap();
    let i_most_ahead = (0..n).min_by(|&a, &b| lag[a].partial_cmp(&lag[b]).unwrap()).unwrap();
    let grid_floor = lref.iter().cloned().fold(f64::INFINITY, f64::min);
    let snap = |i: usize| {
        json!({
            "t": t[i], "ell_target_over_lambda": lt[i] / lam, "ell_ref_over_lambda": lref[i] / lam,
            "ell_kin_over_lambda": lkin[i] / lam, "lag": lag[i], "k_omega_lambda": kw[i] * lam,
            "k_omega_ref_lambda": kwr[i] * lam, "mach": ma[i], "kn": kn[i], "max_abs_rho_minus_1": drho[i],
            "noneq_fraction": noneq[i], "H": h[i], "negative_mass_fraction": neg[i],
            "ell_kin_window6_over_lambda": lwin[i] / lam, "ell_kin_peak_over_lambda": lpeak[i] / lam,
        })
    };
    // NSE control on the same grid and forcing
    let s = &d["nse_control"];
    let (ts, lag_nse, lnse) = (arr(s, "t"), arr(s, "lag"), arr(s, "ell_nse"));
    let kw_nse = arr(s, "k_omega");
    let t_arrest = t[i_lag.unwrap_or(i_min)];
    let nse_first_lag = (0..ts.len()).find(|&i| lag_nse[i] > LAG_ARREST);
    let nse_max_abs_lag_before_arrest =
        (0..ts.len()).filter(|&i| ts[i] <= t_arrest + 1e-12).map(|i| lag_nse[i].abs()).fold(0.0, f64::max);
    let max_neg_before_lag = (0..=i_lag.unwrap_or(n - 1)).map(|i| neg[i]).fold(0.0, f64::max);
    json!({
        "file": path, "lambda": lam, "re_core": c["re_core"], "Q": c["Q"], "N": c["N"],
        "dx_over_lambda": c["dx_over_lambda"], "l_start_over_lambda": c["l_start"].as_f64().unwrap() / lam,
        "dt_over_tau": c["dt_over_tau"], "wall_s": c["wall_s"],
        "ell_arrest": lkin[i_min], "ell_arrest_over_lambda": lkin[i_min] / lam,
        "min_at_last_sample": i_min == n - 1,
        "at_min_ell_kin": snap(i_min),
        "lag_gt_10pct_reached": i_lag.is_some(),
        "at_lag_crossing": i_lag.map(snap),
        "most_ahead": snap(i_most_ahead),
        "grid_floor_ell_ref_over_lambda": grid_floor / lam,
        "arrest_over_grid_floor": lkin[i_min] / grid_floor,
        "robust_estimators": {
            "min_ell_window6_over_lambda": lwin[i_min_win] / lam, "t_min_window6": t[i_min_win],
            "min_ell_peak_over_lambda": lpeak[i_min_peak] / lam, "t_min_peak": t[i_min_peak],
        },
        "positivity": {
            "max_negative_mass_fraction_up_to_lag_crossing": max_neg_before_lag,
            "within_G5_tolerance_up_to_lag_crossing": max_neg_before_lag <= NEG_TOL,
            "max_negative_mass_fraction_whole_run": neg.iter().cloned().fold(0.0, f64::max),
        },
        "conservation": {
            "max_momentum_balance_residual": mbal.iter().cloned().fold(0.0, f64::max),
            "max_mass_drift": mdrift.iter().cloned().fold(0.0, f64::max),
        },
        "series": {
            "ell_target_over_lambda": lt.iter().map(|x| x / lam).collect::<Vec<_>>(),
            "ell_ref_over_lambda": lref.iter().map(|x| x / lam).collect::<Vec<_>>(),
            "ell_kin_over_lambda": lkin.iter().map(|x| x / lam).collect::<Vec<_>>(),
            "ell_kin_window6_over_lambda": lwin.iter().map(|x| x / lam).collect::<Vec<_>>(),
            "lag": lag, "k_omega_lambda": kw.iter().map(|x| x * lam).collect::<Vec<_>>(),
            "mach": ma, "max_abs_rho_minus_1": drho, "noneq_fraction": noneq, "negative_mass_fraction": neg.clone(), "H": h,
            "nse_lag_on_kinetic_times": t.iter().map(|&x| interp(&ts, &lag_nse, x)).collect::<Vec<_>>(),
        },
        "nse_control": {
            "lag_at_kinetic_arrest_time": interp(&ts, &lag_nse, t_arrest),
            "max_abs_lag_up_to_kinetic_arrest": nse_max_abs_lag_before_arrest,
            "ever_lag_gt_10pct": nse_first_lag.is_some(),
            "ell_target_over_lambda_at_first_lag_gt_10pct": nse_first_lag.map(|i| interp(&t, &lt, ts[i]) / lam),
            "min_ell_nse_over_lambda": lnse.iter().cloned().fold(f64::INFINITY, f64::min) / lam,
            "k_omega_lambda_at_kinetic_arrest_time": interp(&ts, &kw_nse, t_arrest) * lam,
        },
    })
}

/// Power-law exponent of y on lambda with 95% CI (OLS in logs).
fn exponent(runs: &[&Value], key: impl Fn(&Value) -> Option<f64>) -> Value {
    let pts: Vec<(f64, f64)> = runs.iter().filter_map(|r| key(r).map(|y| (r["lambda"].as_f64().unwrap(), y))).collect();
    if pts.len() < 3 {
        return json!({"n": pts.len(), "slope": null});
    }
    let x = DMatrix::from_fn(pts.len(), 2, |i, j| if j == 0 { 1.0 } else { pts[i].0.ln() });
    let y = DVector::from_iterator(pts.len(), pts.iter().map(|p| p.1.ln()));
    let (b, se, dof) = ols(&x, &y);
    let tc = t_crit_95(dof);
    json!({"n": pts.len(), "slope": b[1], "se": se[1], "ci95": [b[1] - tc * se[1], b[1] + tc * se[1]],
           "prefactor": b[0].exp(), "dof": dof, "points": pts})
}

fn mean_ci(xs: &[f64]) -> Value {
    let n = xs.len();
    if n == 0 {
        return json!({"n": 0});
    }
    let m = xs.iter().sum::<f64>() / n as f64;
    if n < 2 {
        return json!({"n": n, "mean": m});
    }
    let sd = (xs.iter().map(|x| (x - m).powi(2)).sum::<f64>() / (n - 1) as f64).sqrt();
    let h = t_crit_95(n - 1) * sd / (n as f64).sqrt();
    json!({"n": n, "mean": m, "sd": sd, "ci95": [m - h, m + h], "values": xs})
}

fn group_summary(runs_all: &[Value]) -> Value {
    let sqrt_pi_2 = (PI / 2.0).sqrt();
    let mut by_re = serde_json::Map::new();
    let mut kw_all: Vec<Vec<f64>> = vec![];
    let mut ell_lag_all: Vec<Vec<(f64, f64)>> = vec![];
    for re in [1.0, 0.25] {
        let runs: Vec<&Value> = runs_all.iter().filter(|r| (r["re_core"].as_f64().unwrap() - re).abs() < 1e-9).collect();
        if runs.is_empty() {
            continue;
        }
        let lam_of = |r: &Value| r["lambda"].as_f64().unwrap();
        let a_min = exponent(&runs, |r| r["ell_arrest"].as_f64());
        let a_lag = exponent(&runs, |r| r["at_lag_crossing"]["ell_kin_over_lambda"].as_f64().map(|x| x * lam_of(r)));
        let a_win = exponent(&runs, |r| r["robust_estimators"]["min_ell_window6_over_lambda"].as_f64().map(|x| x * lam_of(r)));
        let kw_min: Vec<f64> = runs.iter().map(|r| r["at_min_ell_kin"]["k_omega_lambda"].as_f64().unwrap()).collect();
        let kw_lag: Vec<f64> = runs.iter().filter_map(|r| r["at_lag_crossing"]["k_omega_lambda"].as_f64()).collect();
        let mach_lag: Vec<f64> = runs.iter().filter_map(|r| r["at_lag_crossing"]["mach"].as_f64()).collect();
        let ell_lag: Vec<f64> = runs.iter().filter_map(|r| r["at_lag_crossing"]["ell_kin_over_lambda"].as_f64()).collect();
        kw_all.push(kw_lag.clone());
        ell_lag_all.push(runs.iter().filter_map(|r| r["at_lag_crossing"]["ell_kin_over_lambda"].as_f64().map(|x| (lam_of(r), x))).collect());
        let mc_lag = mean_ci(&kw_lag);
        let mc_min = mean_ci(&kw_min);
        let contains = |v: &Value| v["ci95"].as_array().map(|c| c[0].as_f64().unwrap() <= sqrt_pi_2 && sqrt_pi_2 <= c[1].as_f64().unwrap());
        by_re.insert(format!("re_core_{re}"), json!({
            "runs": runs.len(),
            "lambdas": runs.iter().map(|r| lam_of(r)).collect::<Vec<_>>(),
            "a_exponent_min_ell_kin": a_min,
            "a_exponent_ell_kin_at_lag_crossing": a_lag,
            "a_exponent_min_windowed_ell": a_win,
            "ell_kin_over_lambda_at_lag_crossing": mean_ci(&ell_lag),
            "b_k_omega_lambda_at_lag_crossing": mc_lag.clone(),
            "b_k_omega_lambda_at_min_ell_kin": mc_min.clone(),
            "b_ratio_to_sqrt_pi_over_2_at_lag_crossing": mc_lag["mean"].as_f64().map(|m| m / sqrt_pi_2),
            "b_ci_contains_sqrt_pi_over_2_at_lag_crossing": contains(&mc_lag),
            "b_ci_contains_sqrt_pi_over_2_at_min": contains(&mc_min),
            "mach_at_lag_crossing": mean_ci(&mach_lag),
            "all_runs_reached_lag_gt_10pct": runs.iter().all(|r| r["lag_gt_10pct_reached"].as_bool().unwrap()),
            "any_min_at_last_sample": runs.iter().any(|r| r["min_at_last_sample"].as_bool().unwrap()),
            "positivity_within_G5_up_to_arrest_all_runs": runs.iter().all(|r| r["positivity"]["within_G5_tolerance_up_to_lag_crossing"].as_bool().unwrap()),
            "max_negative_mass_fraction_up_to_arrest": runs.iter().map(|r| r["positivity"]["max_negative_mass_fraction_up_to_lag_crossing"].as_f64().unwrap()).fold(0.0, f64::max),
            "arrest_over_grid_floor": runs.iter().map(|r| r["arrest_over_grid_floor"].as_f64().unwrap()).collect::<Vec<_>>(),
            "nse_control_never_lags_10pct": runs.iter().all(|r| !r["nse_control"]["ever_lag_gt_10pct"].as_bool().unwrap()),
            "nse_control_max_abs_lag_up_to_arrest": runs.iter().map(|r| r["nse_control"]["max_abs_lag_up_to_kinetic_arrest"].as_f64().unwrap()).fold(0.0, f64::max),
        }));
    }
    // same constant at both Re? difference of k_omega*lambda at the lag crossing (Welch-type CI)
    let same_re = if kw_all.len() == 2 && kw_all.iter().all(|v| v.len() >= 2) {
        let (a, b) = (&kw_all[0], &kw_all[1]);
        let m = |v: &Vec<f64>| v.iter().sum::<f64>() / v.len() as f64;
        let var = |v: &Vec<f64>| {
            let mm = m(v);
            v.iter().map(|x| (x - mm).powi(2)).sum::<f64>() / (v.len() - 1) as f64
        };
        let se = (var(a) / a.len() as f64 + var(b) / b.len() as f64).sqrt();
        let df = (a.len() + b.len() - 2).max(1);
        let diff = m(a) - m(b);
        let tc = t_crit_95(df);
        // paired by lambda: ratio of arrest lengths Re=1 / Re=0.25
        let ratios: Vec<f64> = ell_lag_all[0].iter().filter_map(|(l, x)| ell_lag_all[1].iter().find(|(l2, _)| (l2 - l).abs() < 1e-12).map(|(_, y)| x / y)).collect();
        json!({"quantity": "k_omega*lambda at lag crossing", "diff_re1_minus_re025": diff, "ci95": [diff - tc * se, diff + tc * se],
               "relative_diff": diff / (0.5 * (m(a) + m(b))), "ci_contains_zero": (diff - tc * se) <= 0.0 && 0.0 <= (diff + tc * se),
               "ell_arrest_ratio_re1_over_re025_paired_by_lambda": mean_ci(&ratios)})
    } else {
        json!(null)
    };
    json!({"by_re": Value::Object(by_re), "b_same_constant_at_both_re": same_re})
}

/// Rows of runs that differ only in `vary` (sorted by it), for convergence/sensitivity tables.
fn ladder(runs: &[Value], vary: &str) -> Vec<Value> {
    let keys = ["lambda", "re_core", "Q", "N", "l_start_over_lambda"];
    let mut groups: Vec<(Vec<String>, Vec<&Value>)> = vec![];
    for r in runs {
        let sig: Vec<String> = keys.iter().filter(|k| **k != vary).map(|k| format!("{:.6}", r[*k].as_f64().unwrap())).collect();
        match groups.iter_mut().find(|g| g.0 == sig) {
            Some(g) => g.1.push(r),
            None => groups.push((sig, vec![r])),
        }
    }
    groups
        .into_iter()
        .filter(|g| g.1.len() >= 2)
        .map(|(_, mut g)| {
            g.sort_by(|a, b| a[vary].as_f64().unwrap().partial_cmp(&b[vary].as_f64().unwrap()).unwrap());
            let r0 = g[0];
            json!({
                "lambda": r0["lambda"], "re_core": r0["re_core"], "Q": r0["Q"], "N": r0["N"], "l_start_over_lambda": r0["l_start_over_lambda"],
                "varied": vary,
                "values": g.iter().map(|r| r[vary].clone()).collect::<Vec<_>>(),
                "dx_over_lambda": g.iter().map(|r| r["dx_over_lambda"].clone()).collect::<Vec<_>>(),
                "grid_floor_over_lambda": g.iter().map(|r| r["grid_floor_ell_ref_over_lambda"].clone()).collect::<Vec<_>>(),
                "ell_target_over_lambda_at_lag_crossing": g.iter().map(|r| r["at_lag_crossing"]["ell_target_over_lambda"].clone()).collect::<Vec<_>>(),
                "ell_kin_over_lambda_at_lag_crossing": g.iter().map(|r| r["at_lag_crossing"]["ell_kin_over_lambda"].clone()).collect::<Vec<_>>(),
                "k_omega_lambda_at_lag_crossing": g.iter().map(|r| r["at_lag_crossing"]["k_omega_lambda"].clone()).collect::<Vec<_>>(),
                "mach_at_lag_crossing": g.iter().map(|r| r["at_lag_crossing"]["mach"].clone()).collect::<Vec<_>>(),
                "ell_arrest_over_lambda_min": g.iter().map(|r| r["ell_arrest_over_lambda"].clone()).collect::<Vec<_>>(),
                "min_windowed_ell_over_lambda": g.iter().map(|r| r["robust_estimators"]["min_ell_window6_over_lambda"].clone()).collect::<Vec<_>>(),
                "most_ahead_lag": g.iter().map(|r| r["most_ahead"]["lag"].clone()).collect::<Vec<_>>(),
                "negative_mass_fraction_up_to_arrest": g.iter().map(|r| r["positivity"]["max_negative_mass_fraction_up_to_lag_crossing"].clone()).collect::<Vec<_>>(),
            })
        })
        .collect()
}

fn main() {
    let load = |flag: &str| -> Vec<Value> { collect_args(flag).iter().map(|f| analyze_run(f)).collect() };
    let main = load("--main");
    let fine = load("--fine");
    let fixn = load("--fixn");
    let extra = load("--extra");
    let out = collect_args("--out").first().cloned().expect("--out");
    let gates: Option<Value> = collect_args("--gates").first().map(|p| serde_json::from_str(&std::fs::read_to_string(p).unwrap()).unwrap());
    let sqrt_pi_2 = (PI / 2.0).sqrt();
    let mut all: Vec<Value> = main.clone();
    all.extend(fine.iter().cloned());
    all.extend(fixn.iter().cloned());
    all.extend(extra.iter().cloned());
    let doc = json!({
        "units": "v_th = c_s = 1, nu = tau = lambda; target = forced_core.py column (l0 = 0.8, Gamma = 2 pi nu Re/0.63817) on [0,2pi)^2",
        "definitions": {
            "ell_kin": "enstrophy-weighted second moment with the Gamma/4pi^2 floor (forced_core.py ell_from_moment)",
            "ell_ref": "same estimator on the Nyquist-truncated target at the same time (removes estimator/grid bias from lag)",
            "lag": "ell_kin/ell_ref - 1; arrest = first lag > 0.10; ell_arrest = min over the run of ell_kin",
            "k_omega": "sqrt(sum k^2|w_hat|^2 / sum |w_hat|^2)  (= sqrt(2)/l for a Gaussian)",
            "grid_floor": "min over the run of ell_ref (the estimator's floor on this grid)",
            "sqrt_pi_over_2": sqrt_pi_2,
        },
        "gates_all_pass": gates.as_ref().map(|g| g["all_gates_pass"].clone()),
        "main_sweep": group_summary(&main),
        "fine_sweep": group_summary(&fine),
        "fixed_grid_sweep": group_summary(&fixn),
        "resolution_ladders": ladder(&all, "N"),
        "lstart_sensitivity": ladder(&all, "l_start_over_lambda"),
        "q_dependence": ladder(&all, "Q"),
        "runs_main": main, "runs_fine": fine, "runs_fixed_grid": fixn, "runs_extra": extra,
    });
    std::fs::write(&out, serde_json::to_string_pretty(&doc).unwrap()).unwrap();
    eprintln!("wrote {out}");
    for k in ["main_sweep", "fine_sweep", "fixed_grid_sweep", "resolution_ladders", "lstart_sensitivity", "q_dependence"] {
        println!("== {k}\n{}", serde_json::to_string_pretty(&doc[k]).unwrap());
    }
}
