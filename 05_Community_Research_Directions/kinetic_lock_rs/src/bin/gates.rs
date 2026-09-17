//! Validation gates G1–G5. Writes experiments/results/kinetic_lock_gates.json.
//! Usage: gates [--dt-over-tau 0.1] [--out path]

use kinetic_lock_rs::dispersion::{discrete_termination, lattice_least_damped, lattice_termination, m1_rate, strang_least_damped, strang_propagator};
use nalgebra::{DMatrix, DVector};
use kinetic_lock_rs::lattice::{collide_force_point, entropic_newton_1d, GaussHermite, Lattice, PointScratch};
use kinetic_lock_rs::solver::Kinetic;
use num_complex::Complex64 as C;
use serde_json::{json, Value};
use std::f64::consts::PI;

const QS: [usize; 3] = [12, 16, 24];
const G4_Q: [f64; 8] = [0.05, 0.2, 0.5, 0.8, 1.0, 1.2, 1.5, 2.0];

fn arg(name: &str, default: &str) -> String {
    let a: Vec<String> = std::env::args().collect();
    a.iter().position(|x| x == name).map(|i| a[i + 1].clone()).unwrap_or(default.to_string())
}

fn lcg(state: &mut u64) -> f64 {
    *state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
    (*state >> 11) as f64 / (1u64 << 53) as f64
}

fn g1() -> Value {
    let us: Vec<f64> = vec![0.01, 0.1, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0];
    let mut per_q = vec![];
    let mut worst_moment = 0.0f64;
    let mut b_err_table: Vec<Vec<f64>> = vec![];
    for q in QS {
        let lat = Lattice::new(q);
        let mut feq = vec![0.0; q * q];
        let mut max_res = 0.0f64;
        let mut max_iters = 0;
        for &ux in &us {
            for &uy in &us {
                for &rho in &[0.5, 1.0, 1.7] {
                    for sgn in [1.0, -1.0] {
                        let (nx, ny) = lat.equilibrium(rho, sgn * ux, uy, &mut feq);
                        let (r, jx, jy) = lat.moments(&feq);
                        let res = ((r - rho).abs().max((jx - rho * sgn * ux).abs()).max((jy - rho * uy).abs())) / rho;
                        max_res = max_res.max(res);
                        max_iters = max_iters.max(nx.iters.max(ny.iters));
                    }
                }
            }
        }
        worst_moment = worst_moment.max(max_res);
        let gh = GaussHermite::new(q);
        let mut e = vec![0.0; q];
        let b_err: Vec<f64> = us.iter().map(|&u| (entropic_newton_1d(&gh, u, &mut e).b - u).abs()).collect();
        b_err_table.push(b_err.clone());
        per_q.push(json!({"Q": q, "max_relative_moment_residual": max_res, "max_newton_iters": max_iters,
                          "u": us, "abs_b_minus_u": b_err}));
    }
    // b -> u: |b-u| non-increasing in Q for every u (to roundoff), and small at Q=24 for |u|<=1
    let monotone = (0..us.len()).all(|i| b_err_table[1][i] <= b_err_table[0][i] + 1e-15 && b_err_table[2][i] <= b_err_table[1][i] + 1e-15);
    let q24_small = us.iter().zip(&b_err_table[2]).filter(|(u, _)| **u <= 1.0).all(|(_, e)| *e < 1e-8);
    let pass = worst_moment <= 1e-13 && monotone && q24_small;
    json!({"pass": pass, "threshold_moment": 1e-13, "worst_relative_moment_residual": worst_moment,
           "b_to_u_monotone_in_Q": monotone, "b_minus_u_below_1e-8_at_Q24_for_u_le_1": q24_small, "per_Q": per_q})
}

fn g2() -> Value {
    let mut st = 11u64;
    let mut out = vec![];
    let (mut worst_cons, mut worst_h_increase, mut worst_force) = (0.0f64, f64::NEG_INFINITY, 0.0f64);
    for q in QS {
        let lat = Lattice::new(q);
        let mut s = PointScratch::new(q);
        let (mut cons, mut hinc, mut fres) = (0.0f64, f64::NEG_INFINITY, 0.0f64);
        for trial in 0..200 {
            let drift = 0.8 * (lcg(&mut st) - 0.5);
            let mut f: Vec<f64> = (0..q * q)
                .map(|m| lat.w[m] * (0.1 + 2.0 * lcg(&mut st)) * (1.0 + drift * lat.vx[m] + 0.3 * drift * lat.vy[m]).max(0.02))
                .collect();
            let (r0, jx0, jy0) = lat.moments(&f);
            let mut hp = lat.h_function(&f);
            for k in 0..30 {
                let a = (-(0.01 + 0.2 * lcg(&mut st))).exp();
                if trial % 2 == 0 {
                    collide_force_point(&lat, &mut f, a, [0.0, 0.0], &mut s);
                    let (r, jx, jy) = lat.moments(&f);
                    cons = cons.max(((r - r0).abs().max((jx - jx0).abs()).max((jy - jy0).abs())) / r0);
                    let h = lat.h_function(&f);
                    hinc = hinc.max((h - hp) / hp.abs().max(1.0));
                    hp = h;
                } else {
                    let du = [0.02 * (lcg(&mut st) - 0.5), 0.02 * (lcg(&mut st) - 0.5)];
                    let (r1, jx1, jy1) = lat.moments(&f);
                    collide_force_point(&lat, &mut f, a, du, &mut s);
                    let (r, jx, jy) = lat.moments(&f);
                    fres = fres.max(((r - r1).abs().max((jx - jx1 - r1 * du[0]).abs()).max((jy - jy1 - r1 * du[1]).abs())) / r1);
                    let _ = k;
                }
            }
        }
        worst_cons = worst_cons.max(cons);
        worst_h_increase = worst_h_increase.max(hinc);
        worst_force = worst_force.max(fres);
        out.push(json!({"Q": q, "max_relative_mass_momentum_change": cons, "max_relative_H_increase": hinc,
                        "max_relative_force_momentum_residual": fres}));
    }
    let pass = worst_cons <= 1e-13 && worst_h_increase <= 1e-14 && worst_force <= 1e-13;
    json!({"pass": pass, "threshold_conservation": 1e-13, "H_tolerance_roundoff": 1e-14,
           "worst_conservation": worst_cons, "worst_H_increase": worst_h_increase,
           "worst_force_momentum_residual": worst_force, "per_Q": out})
}

/// Transverse shear wave u_y = eps sin(x) on N=8, tau = q (k = 1). Returns sin-amplitude of j_y
/// sampled every `stride` steps, the sample times, and the max negative-mass fraction.
fn shear_wave(qn: usize, qk: f64, dt_over_tau: f64, eps: f64, t_end_tau: f64, stride: usize) -> (Vec<f64>, Vec<f64>, f64, f64) {
    let n = 8;
    let tau = qk;
    let mut kin = Kinetic::new(qn, n, tau);
    let dx = 2.0 * PI / n as f64;
    let rho = vec![1.0; n * n];
    let ux = vec![0.0; n * n];
    let uy: Vec<f64> = (0..n * n).map(|p| eps * ((p % n) as f64 * dx).sin()).collect();
    kin.set_equilibrium(&rho, &ux, &uy);
    let h = dt_over_tau * tau;
    let nsteps = (t_end_tau / dt_over_tau).round() as usize;
    let amp = |kin: &Kinetic| {
        let (r, _, uy) = kin.fields();
        (0..n * n).map(|p| r[p] * uy[p] * ((p % n) as f64 * dx).sin()).sum::<f64>() * 2.0 / (n * n) as f64
    };
    let (mut a, mut t) = (vec![amp(&kin)], vec![0.0]);
    let mut neg = 0.0f64;
    for s in 0..nsteps {
        let _ = kin.collide_force(0.5 * h, None, 0.0);
        kin.stream(h);
        let _ = kin.collide_force(0.5 * h, None, 0.0);
        if (s + 1) % stride == 0 {
            a.push(amp(&kin));
            t.push((s + 1) as f64 * h);
            let sm = kin.sums();
            neg = neg.max(sm.negative_mass / sm.mass);
        }
    }
    let mass = kin.sums().mass;
    (t, a, neg, mass)
}

fn g4(dt_over_tau: f64) -> Value {
    // For each (Q, q): (1) the solver's k=1 amplitude history must equal the exact Strang
    // propagator P^n applied to the initial Maxwellian perturbation (code check); (2) the
    // solver's decay rate is then the least-damped eigenvalue of P, compared with exact BGK
    // (M1) and with the continuous-time lattice operator (splitting error); (3) where one
    // real mode dominates, a model-free log-linear fit of the solver history is reported too.
    let mut rows = vec![];
    let mut pass = true;
    let mut worst_series = 0.0f64;
    let mut terminations = vec![];
    for qn in QS {
        let lat = Lattice::new(qn);
        let (v, w) = (&lat.gh.v, &lat.gh.w);
        terminations.push(json!({"Q": qn, "lattice_termination_q": lattice_termination(v, w),
                                 "bracketing_cross_check": discrete_termination(v, w)}));
        for &qk in &G4_Q {
            let window = (3.0 / (qk * qk)).clamp(12.0, 2000.0);
            let nsteps = (window / dt_over_tau).round() as usize;
            let stride = (nsteps / 450).max(1);
            let eps = 1e-6;
            let (t, a, neg, _) = shear_wave(qn, qk, dt_over_tau, eps, window, stride);
            // exact propagator history
            let (pre, pim) = strang_propagator(v, w, qk, dt_over_tau);
            let pc = DMatrix::from_fn(qn, qn, |i, j| C::new(pre[(i, j)], pim[(i, j)]));
            // propagator acts on y = h/w (relaxation toward sum_j w_j y_j); u_y-hat = sum_j w_j y_j
            let amp_of = |y: &DVector<C>| -2.0 * y.iter().zip(w.iter()).map(|(z, wj)| wj * z.im).sum::<f64>();
            let mut yvec = DVector::from_element(qn, C::new(0.0, -eps / 2.0));
            let mut pred = vec![amp_of(&yvec)];
            for s in 0..nsteps {
                yvec = &pc * yvec;
                if (s + 1) % stride == 0 {
                    pred.push(amp_of(&yvec));
                }
            }
            let series_err = a.iter().zip(&pred).map(|(x, y)| (x - y).abs()).fold(0.0, f64::max)
                / a.iter().fold(0.0f64, |m, x| m.max(x.abs()));
            worst_series = worst_series.max(series_err);
            let s_strang = strang_least_damped(v, w, qk, dt_over_tau);
            let s_lattice = lattice_least_damped(v, w, qk);
            let gamma = -s_strang.re;
            let m1 = m1_rate(qk);
            let m1_err = m1.map(|g| (gamma - g).abs() / g);
            // model-free fit over the last half of the history (only meaningful for a real mode)
            let half = a.len() / 2;
            let fit = if s_strang.im.abs() < 1e-9 && a[half..].iter().all(|x| x.abs() > 0.0 && x.signum() == a[half].signum()) {
                let xs: Vec<f64> = t[half..].iter().map(|x| x / qk).collect();
                let ys: Vec<f64> = a[half..].iter().map(|x| x.abs().ln()).collect();
                let xm = xs.iter().sum::<f64>() / xs.len() as f64;
                let ym = ys.iter().sum::<f64>() / ys.len() as f64;
                let sxy: f64 = xs.iter().zip(&ys).map(|(x, y)| (x - xm) * (y - ym)).sum();
                let sxx: f64 = xs.iter().map(|x| (x - xm).powi(2)).sum();
                Some(-sxy / sxx)
            } else { None };
            let gated = qn == 24 && qk <= 1.0 + 1e-12;
            let row_pass = !gated || (m1_err.map(|e| e <= 0.02).unwrap_or(false) && series_err <= 1e-8);
            pass &= row_pass;
            rows.push(json!({
                "Q": qn, "q": qk, "solver_gamma_tau": gamma, "solver_omega_tau": s_strang.im,
                "M1_gamma_tau": m1, "rel_err_vs_M1": m1_err,
                "lattice_continuous_s_tau": [s_lattice.re, s_lattice.im],
                "splitting_rel_shift": (gamma + s_lattice.re).abs() / s_lattice.re.abs(),
                "mode_is_complex": s_strang.im.abs() > 1e-7,
                "series_vs_propagator_max_rel_err": series_err, "loglinear_fit_gamma_tau": fit,
                "gated": gated, "row_pass": row_pass, "negative_mass_fraction": neg,
            }));
        }
    }
    json!({"pass": pass,
           "criterion": "Q=24, q<=1.0: |gamma_solver - gamma_M1|/gamma_M1 <= 0.02 and solver history equals the exact Strang propagator to 1e-8",
           "dt_over_tau": dt_over_tau, "worst_series_err": worst_series, "terminations": terminations, "rows": rows,
           "M1_termination_sqrt_pi_over_2": (PI / 2.0).sqrt()})
}

/// Reference check of the M1 implementation against lock_k_kinetic_spectrum.json.
fn m1_vs_json(path: &str) -> Value {
    let Ok(txt) = std::fs::read_to_string(path) else { return json!({"available": false}) };
    let d: Value = serde_json::from_str(&txt).unwrap();
    let qs = d["series"]["q"].as_array().unwrap();
    let gs = d["series"]["gamma_tau_M1"].as_array().unwrap();
    let mut worst = 0.0f64;
    let mut count = 0;
    let mut null_mismatch = 0;
    for (q, g) in qs.iter().zip(gs) {
        let q = q.as_f64().unwrap();
        match (g.as_f64(), m1_rate(q)) {
            (Some(gj), Some(gr)) => {
                // near termination the root sits at z -> 0 where the bracket is tight
                worst = worst.max((gj - gr).abs() / gj);
                count += 1;
            }
            (None, None) => {}
            _ => null_mismatch += 1,
        }
    }
    json!({"available": true, "points": count, "max_rel_diff": worst, "existence_mismatches": null_mismatch})
}

fn g5(dt_over_tau: f64) -> Value {
    // Nonlinear Taylor–Green vortices at Mach up to 0.6 and Kn = tau k up to 0.1.
    let mut runs = vec![];
    let mut worst = 0.0f64;
    for &(u0, tau) in &[(0.3, 0.02), (0.6, 0.02), (0.6, 0.1)] {
        let n = 48;
        let q = 24;
        let mut kin = Kinetic::new(q, n, tau);
        let dx = 2.0 * PI / n as f64;
        let mut rho = vec![0.0; n * n];
        let mut ux = vec![0.0; n * n];
        let mut uy = vec![0.0; n * n];
        for iy in 0..n {
            for ix in 0..n {
                let (x, y) = (ix as f64 * dx, iy as f64 * dx);
                let p = iy * n + ix;
                ux[p] = u0 * x.sin() * y.cos();
                uy[p] = -u0 * x.cos() * y.sin();
                rho[p] = (-(u0 * u0 / 4.0) * ((2.0 * x).cos() + (2.0 * y).cos())).exp();
            }
        }
        kin.set_equilibrium(&rho, &ux, &uy);
        let s0 = kin.sums();
        let h = dt_over_tau * tau;
        let nsteps = ((1.0f64).max(20.0 * tau) / h).round() as usize;
        let mut neg = 0.0f64;
        let mut minf = f64::INFINITY;
        for s in 0..nsteps {
            let _ = kin.collide_force(0.5 * h, None, 0.0);
            kin.stream(h);
            let _ = kin.collide_force(0.5 * h, None, 0.0);
            if s % 5 == 4 || s + 1 == nsteps {
                let sm = kin.sums();
                neg = neg.max(sm.negative_mass / sm.mass);
                minf = minf.min(sm.min_f);
            }
        }
        let s1 = kin.sums();
        worst = worst.max(neg);
        runs.push(json!({"u0_mach": u0, "tau": tau, "N": n, "Q": q, "t_end": nsteps as f64 * h,
            "max_negative_mass_fraction": neg, "min_f": minf,
            "mass_drift": (s1.mass - s0.mass).abs() / s0.mass,
            "momentum_drift": ((s1.px - s0.px).abs() + (s1.py - s0.py).abs()) / s0.mass}));
    }
    json!({"pass": worst <= 1e-6, "threshold": 1e-6, "worst_negative_mass_fraction": worst, "runs": runs})
}


#[cfg(feature = "sundials")]
/// Integrate with CVODE, tightening tolerances only as far as the solver accepts:
/// tries rtol = 1e-11, 1e-10, ..., 1e-6 (BDF, then Adams) and returns the first success.
fn cvode_ladder<F, M>(make: M, y0: &[f64], atol_over_rtol: f64, touts: &[f64]) -> (Option<Vec<Vec<f64>>>, Value)
where
    M: Fn() -> F,
    F: FnMut(f64, &[f64], &mut [f64]) -> Result<(), String> + Send + Sync,
{
    use cvode::{Cvode, Method, Task};
    use nvector::SerialVector;
    let mut attempts = vec![];
    for method in [Method::Bdf, Method::Adams] {
        for e in 6..=11 {
            let rtol = 10f64.powi(-(17 - e));
            let name = if matches!(method, Method::Bdf) { "BDF" } else { "Adams" };
            let built = Cvode::builder(method).rtol(rtol).atol(rtol * atol_over_rtol).max_steps(2_000_000)
                .build(make(), 0.0, SerialVector::from_slice(y0));
            let Ok(mut cv) = built else {
                attempts.push(json!({"method": name, "rtol": rtol, "ok": false, "error": "build"}));
                continue;
            };
            let mut out = vec![];
            let mut err = None;
            for &t in touts {
                match cv.solve(t, Task::Normal) {
                    Ok((_, y)) => out.push(y.to_vec()),
                    Err(x) => {
                        err = Some(format!("{x:?}"));
                        break;
                    }
                }
            }
            let ok = err.is_none();
            attempts.push(json!({"method": name, "rtol": rtol, "ok": ok, "error": err, "steps": cv.num_steps()}));
            if ok {
                return (Some(out), json!(attempts));
            }
        }
    }
    (None, json!(attempts))
}

#[cfg(feature = "sundials")]
fn g3(dt_over_tau: f64) -> Value {
    // (i) homogeneous nonlinear BGK relaxation: CVODE on df/dt = (feq(f) - f)/tau
    let q = 16;
    let lat = Lattice::new(q);
    let mut st = 3u64;
    let f0: Vec<f64> = (0..q * q).map(|m| lat.w[m] * (0.2 + 1.6 * lcg(&mut st)) * (1.0 + 0.3 * lat.vx[m]).max(0.05)).collect();
    let tau = 0.37;
    let make = || {
        let lat2 = lat.clone();
        // state g = f/w (O(1) components, so CVODE's error weights are well scaled)
        move |_t: f64, y: &[f64], yd: &mut [f64]| -> Result<(), String> {
            let f: Vec<f64> = y.iter().zip(&lat2.w).map(|(g, w)| g * w).collect();
            let (r, jx, jy) = lat2.moments(&f);
            let mut eq = vec![0.0; y.len()];
            lat2.equilibrium(r, jx / r, jy / r, &mut eq);
            for m in 0..y.len() {
                yd[m] = (eq[m] / lat2.w[m] - y[m]) / tau;
            }
            Ok(())
        }
    };
    let g0: Vec<f64> = f0.iter().zip(&lat.w).map(|(f, w)| f / w).collect();
    let ts = [0.5, 1.0, 3.0];
    let touts: Vec<f64> = ts.iter().map(|x| x * tau).collect();
    let (sol, attempts_relax) = cvode_ladder(make, &g0, 1e-2, &touts);
    let (r0, jx0, jy0) = lat.moments(&f0);
    let mut eq0 = vec![0.0; q * q];
    lat.equilibrium(r0, jx0 / r0, jy0 / r0, &mut eq0);
    let gmax = g0.iter().cloned().fold(0.0, f64::max);
    let mut relax = vec![];
    let mut worst_relax = f64::NAN;
    if let Some(ys) = &sol {
        worst_relax = 0.0;
        for (tt, y) in ts.iter().zip(ys) {
            let a = (-tt).exp();
            let err = (0..q * q).map(|m| (y[m] - (eq0[m] + a * (f0[m] - eq0[m])) / lat.w[m]).abs()).fold(0.0, f64::max) / gmax;
            worst_relax = worst_relax.max(err);
            relax.push(json!({"t_over_tau": tt, "max_abs_err_over_max_g": err}));
        }
    }
    // (ii) linear shear wave: CVODE on the Q-node transverse ODE vs the full Strang solver
    let qn = 24;
    let gh = GaussHermite::new(qn);
    let qk = 0.5;
    let taul = qk;
    let eps = 1e-6;
    let make2 = || {
        let (v, w) = (gh.v.clone(), gh.w.clone());
        // y = [Re, Im] of h/w;  dh/dt = -i v h - (h - w sum h)/tau  (k = 1)
        move |_t: f64, y: &[f64], yd: &mut [f64]| -> Result<(), String> {
            let sr: f64 = (0..qn).map(|i| w[i] * y[i]).sum();
            let si: f64 = (0..qn).map(|i| w[i] * y[qn + i]).sum();
            for i in 0..qn {
                yd[i] = v[i] * y[qn + i] - (y[i] - sr) / taul;
                yd[qn + i] = -v[i] * y[i] - (y[qn + i] - si) / taul;
            }
            Ok(())
        }
    };
    let mut y0 = vec![0.0; 2 * qn];
    for i in 0..qn {
        y0[qn + i] = -eps / 2.0; // h = w eps/(2i), stored as h/w
    }
    let times = [1.0, 2.0, 5.0, 10.0];
    let touts2: Vec<f64> = times.iter().map(|x| x * taul).collect();
    let (sol2, attempts_shear) = cvode_ladder(make2, &y0, 1e-6, &touts2);
    let Some(ys2) = sol2 else {
        return json!({"built": true, "pass": false, "attempts_relaxation": attempts_relax, "attempts_shear": attempts_shear});
    };
    let ref_amp: Vec<f64> = ys2.iter().map(|y| -2.0 * (0..qn).map(|i| gh.w[i] * y[qn + i]).sum::<f64>()).collect();
    let mut conv = vec![];
    let mut errs = vec![];
    for &dtt in &[dt_over_tau, dt_over_tau / 2.0] {
        let spt = (1.0 / dtt).round() as usize; // steps per tau
        let (t, a, _, _) = shear_wave(qn, qk, dtt, eps, 10.0, spt);
        let e = times.iter().zip(&ref_amp).map(|(tt, r)| {
            let i = t.iter().position(|x| (x / taul - tt).abs() < 1e-9).unwrap();
            (a[i] - r).abs() / r.abs()
        }).fold(0.0, f64::max);
        errs.push(e);
        conv.push(json!({"dt_over_tau": dtt, "max_rel_err_vs_cvode": e}));
    }
    let order = (errs[0] / errs[1]).log2();
    let pass = worst_relax <= 1e-6 && order > 1.8 && order < 2.2 && errs[0] < 1e-2;
    json!({"built": true, "pass": pass, "attempts_relaxation": attempts_relax, "attempts_shear": attempts_shear,
           "criterion": "relaxation agrees with CVODE to 1e-6 (at the tightest tolerance CVODE accepts); Strang shear wave converges to CVODE at order 2 (1.8-2.2) with err < 1%",
           "relaxation": relax, "worst_relaxation_err": worst_relax,
           "shear_wave_q": qk, "shear_wave_Q": qn, "shear_wave_convergence": conv, "observed_order": order})
}

#[cfg(not(feature = "sundials"))]
fn g3(_dt: f64) -> Value {
    json!({"built": false, "pass": null, "note": "build with --features sundials"})
}

fn main() {
    let dt_over_tau: f64 = arg("--dt-over-tau", "0.1").parse().unwrap();
    let out = arg("--out", "../experiments/results/kinetic_lock_gates.json");
    let spectrum = arg("--spectrum", "../experiments/results/lock_k_kinetic_spectrum.json");
    eprintln!("G1 ...");
    let r1 = g1();
    eprintln!("  pass={} worst={}", r1["pass"], r1["worst_relative_moment_residual"]);
    eprintln!("G2 ...");
    let r2 = g2();
    eprintln!("  pass={} cons={} dH={}", r2["pass"], r2["worst_conservation"], r2["worst_H_increase"]);
    eprintln!("G3 ...");
    let r3 = g3(dt_over_tau);
    eprintln!("  {}", r3);
    eprintln!("M1 reference check ...");
    let m1 = m1_vs_json(&spectrum);
    eprintln!("  {}", m1);
    eprintln!("G4 ...");
    let r4 = g4(dt_over_tau);
    for r in r4["rows"].as_array().unwrap() {
        eprintln!("  {}", r);
    }
    eprintln!("  pass={}", r4["pass"]);
    eprintln!("G5 ...");
    let r5 = g5(dt_over_tau);
    eprintln!("  {}", r5);
    let all = r1["pass"].as_bool().unwrap()
        && r2["pass"].as_bool().unwrap()
        && r3["pass"].as_bool().unwrap_or(false)
        && r4["pass"].as_bool().unwrap()
        && r5["pass"].as_bool().unwrap();
    let doc = json!({
        "units": "v_th = c_s = 1, nu = tau = lambda, q = k lambda",
        "all_gates_pass": all, "G1": r1, "G2": r2, "G3_cvode": r3, "M1_reference_check": m1, "G4": r4, "G5": r5,
    });
    std::fs::write(&out, serde_json::to_string_pretty(&doc).unwrap()).unwrap();
    eprintln!("ALL GATES PASS = {all}  -> {out}");
}
