//! Forced collapsing core (the target of experiments/forced_core.py, in 2D) driven through
//! the kinetic solver and through a 2D Navier–Stokes control.
//!
//! Target: omega(r,t) = Gamma/(pi l^2) exp(-r^2/l^2), l^2 = nu (T - t), T = l0^2/nu,
//! Gamma = 2 pi nu Re_core / 0.63817, centred at (pi, pi) on [0, 2 pi)^2, mean removed.
//! It is built spectrally (Nyquist-truncated), so it is defined for every l >= 0:
//!   omega_hat(k) = N^2 Gamma/L^2 exp(-k^2 l^2/4) (-1)^(kx+ky),  k != 0.
//! Forcing (per unit mass): the residual of the target under incompressible NSE; for the
//! axisymmetric column the advection is a pure gradient, so in vorticity form
//!   g_omega_hat = d_t omega_hat + nu k^2 omega_hat = (5/4) nu k^2 omega_hat.
//! Kinetic units: v_th = c_s = 1, nu = tau = lambda.

use crate::solver::Kinetic;
use crate::spectral::Spectral2D;
use num_complex::Complex64 as C;
use rayon::prelude::*;
use serde_json::{json, Value};
use std::f64::consts::PI;
use std::time::Instant;

pub const LAMB_OSEEN_PEAK_FACTOR: f64 = 0.63817;

#[derive(Clone, Copy, Debug)]
pub struct Target {
    pub nu: f64,
    pub l0: f64,
    pub re_core: f64,
    pub t_blowup: f64,
    pub gamma: f64,
}

impl Target {
    pub fn new(nu: f64, l0: f64, re_core: f64) -> Self {
        Target { nu, l0, re_core, t_blowup: l0 * l0 / nu, gamma: 2.0 * PI * nu * re_core / LAMB_OSEEN_PEAK_FACTOR }
    }
    pub fn ell(&self, t: f64) -> f64 {
        (self.nu * (self.t_blowup - t).max(0.0)).sqrt()
    }
    pub fn omega_hat(&self, sp: &Spectral2D, t: f64) -> Vec<C> {
        let n = sp.n;
        let l2 = self.ell(t).powi(2);
        let amp = (n * n) as f64 * self.gamma / (4.0 * PI * PI);
        let mut w = vec![C::new(0.0, 0.0); n * n];
        for iy in 0..n {
            for ix in 0..n {
                if sp.is_nyquist(ix, iy) || (ix == 0 && iy == 0) {
                    continue;
                }
                let (kx, ky) = (sp.k[ix], sp.k[iy]);
                let sign = if (ix + iy) % 2 == 0 { 1.0 } else { -1.0 };
                w[iy * n + ix] = C::new(amp * sign * (-(kx * kx + ky * ky) * l2 / 4.0).exp(), 0.0);
            }
        }
        w
    }
    /// Forcing vorticity spectrum (5/4) nu k^2 omega_hat.
    pub fn forcing_omega_hat(&self, sp: &Spectral2D, t: f64) -> Vec<C> {
        let n = sp.n;
        let mut w = self.omega_hat(sp, t);
        for iy in 0..n {
            for ix in 0..n {
                let k2 = sp.k[ix] * sp.k[ix] + sp.k[iy] * sp.k[iy];
                w[iy * n + ix] *= 1.25 * self.nu * k2;
            }
        }
        w
    }
    /// Forcing velocity field (gx, gy) on the grid.
    pub fn forcing_velocity(&self, sp: &Spectral2D, t: f64) -> (Vec<f64>, Vec<f64>) {
        let (gx, gy) = sp.velocity_from_vorticity_hat(&self.forcing_omega_hat(sp, t));
        (sp.inverse(&gx), sp.inverse(&gy))
    }
}

/// Enstrophy-weighted second moment l = sqrt(2 sum w^2 r^2 / sum w^2), with the uniform
/// periodisation floor Gamma/L^2 added back (forced_core.py `ell_from_moment`).
pub fn ell_moment(sp: &Spectral2D, omega: &[f64], gamma: f64) -> f64 {
    let n = sp.n;
    let floor = gamma / (4.0 * PI * PI);
    let (mut num, mut den) = (0.0, 0.0);
    for iy in 0..n {
        let y = iy as f64 * sp.dx - PI;
        for ix in 0..n {
            let x = ix as f64 * sp.dx - PI;
            let w = omega[iy * n + ix] + floor;
            num += w * w * (x * x + y * y);
            den += w * w;
        }
    }
    (2.0 * num / den).sqrt()
}

/// Same estimator restricted to r < rmax (insensitive to far-field acoustic/grid vorticity).
pub fn ell_moment_window(sp: &Spectral2D, omega: &[f64], gamma: f64, rmax: f64) -> f64 {
    let n = sp.n;
    let floor = gamma / (4.0 * PI * PI);
    let (mut num, mut den) = (0.0, 0.0);
    for iy in 0..n {
        let y = iy as f64 * sp.dx - PI;
        for ix in 0..n {
            let x = ix as f64 * sp.dx - PI;
            let r2 = x * x + y * y;
            if r2 < rmax * rmax {
                let w = omega[iy * n + ix] + floor;
                num += w * w * r2;
                den += w * w;
            }
        }
    }
    (2.0 * num / den).sqrt()
}

/// Isothermal cyclostrophic density: grad ln rho = -(u.grad)u (gradient part), mean rho = 1.
pub fn balanced_density(sp: &Spectral2D, ux: &[f64], uy: &[f64]) -> Vec<f64> {
    let n = sp.n;
    let ax_h = sp.forward(ux);
    let ay_h = sp.forward(uy);
    let deriv = |a: &[C], dir: usize| -> Vec<f64> {
        let mut d = vec![C::new(0.0, 0.0); n * n];
        for iy in 0..n {
            for ix in 0..n {
                if sp.is_nyquist(ix, iy) {
                    continue;
                }
                let k = if dir == 0 { sp.k[ix] } else { sp.k[iy] };
                d[iy * n + ix] = C::new(0.0, k) * a[iy * n + ix];
            }
        }
        sp.inverse(&d)
    };
    let (uxx, uxy, uyx, uyy) = (deriv(&ax_h, 0), deriv(&ax_h, 1), deriv(&ay_h, 0), deriv(&ay_h, 1));
    let acc_x: Vec<f64> = (0..n * n).map(|p| -(ux[p] * uxx[p] + uy[p] * uxy[p])).collect();
    let acc_y: Vec<f64> = (0..n * n).map(|p| -(ux[p] * uyx[p] + uy[p] * uyy[p])).collect();
    let (axh, ayh) = (sp.forward(&acc_x), sp.forward(&acc_y));
    let mut lr = vec![C::new(0.0, 0.0); n * n];
    for iy in 0..n {
        for ix in 0..n {
            if sp.is_nyquist(ix, iy) || (ix == 0 && iy == 0) {
                continue;
            }
            let p = iy * n + ix;
            let (kx, ky) = (sp.k[ix], sp.k[iy]);
            lr[p] = -C::new(0.0, 1.0) * (kx * axh[p] + ky * ayh[p]) / (kx * kx + ky * ky);
        }
    }
    let mut rho: Vec<f64> = sp.inverse(&lr).iter().map(|x| x.exp()).collect();
    let mean = rho.iter().sum::<f64>() / (n * n) as f64;
    rho.iter_mut().for_each(|r| *r /= mean);
    rho
}

#[derive(Clone, Copy, Debug)]
pub struct CollapseConfig {
    pub lambda: f64,
    pub re_core: f64,
    pub q: usize,
    pub n: usize,
    pub l0: f64,
    /// start on the target trajectory at l_start = min(l0, lstart_over_lambda * lambda)
    pub lstart_over_lambda: f64,
    pub dt_over_tau: f64,
    pub sample_every: usize,
}

/// Even 2^a 3^b (fast rustfft lengths) nearest to x in log distance.
pub fn fast_size(x: f64) -> usize {
    let mut best = 2usize;
    let mut a = 2usize;
    while a < 1 << 16 {
        let mut b = a;
        while b < 1 << 16 {
            if ((b as f64) / x).ln().abs() < ((best as f64) / x).ln().abs() {
                best = b;
            }
            b *= 3;
        }
        a *= 2;
    }
    best
}

fn series_push(map: &mut serde_json::Map<String, Value>, key: &str, x: f64) {
    map.entry(key.to_string()).or_insert_with(|| json!([])).as_array_mut().unwrap().push(json!(x));
}

/// Run the kinetic forced collapse and the NSE control on the same grid.
pub fn run_collapse(cfg: CollapseConfig, verbose: bool) -> Value {
    let tau = cfg.lambda;
    let nu = tau;
    let tgt = Target::new(nu, cfg.l0, cfg.re_core);
    let sp = Spectral2D::new(cfg.n);
    let n = cfg.n;
    let area = sp.dx * sp.dx;
    let l_start = cfg.l0.min(cfg.lstart_over_lambda * cfg.lambda);
    let t0 = tgt.t_blowup - l_start * l_start / nu;
    let t_end = tgt.t_blowup;
    let nsteps = ((t_end - t0) / (cfg.dt_over_tau * tau)).ceil() as usize;
    let h = (t_end - t0) / nsteps as f64;

    // ---- initial state: target velocity, cyclostrophic density, entropic equilibrium
    let (uxh, uyh) = sp.velocity_from_vorticity_hat(&tgt.omega_hat(&sp, t0));
    let (ux0, uy0) = (sp.inverse(&uxh), sp.inverse(&uyh));
    let rho0 = balanced_density(&sp, &ux0, &uy0);
    let mut kin = Kinetic::new(cfg.q, n, tau);
    kin.set_equilibrium(&rho0, &ux0, &uy0);
    let s0 = kin.sums();
    let vmax = kin.lat.gh.v[cfg.q - 1];

    let mut rec = serde_json::Map::new();
    let mut impulse = (0.0, 0.0);
    let wall = Instant::now();
    let sample = |kin: &Kinetic, t: f64, impulse: (f64, f64), rec: &mut serde_json::Map<String, Value>| {
        let (_rho, ux, uy) = kin.fields();
        let s = kin.sums();
        let w_hat = sp.vorticity_hat(&ux, &uy);
        let omega = sp.inverse(&w_hat);
        let ell_kin = ell_moment(&sp, &omega, tgt.gamma);
        let wt_hat = tgt.omega_hat(&sp, t);
        let omega_t = sp.inverse(&wt_hat);
        let ell_ref = ell_moment(&sp, &omega_t, tgt.gamma);
        let rw = 6.0 * cfg.lambda;
        let wmax = omega.iter().fold(0.0f64, |a, &b| a.max(b.abs()));
        series_push(rec, "ell_kin_window6", ell_moment_window(&sp, &omega, tgt.gamma, rw));
        series_push(rec, "ell_ref_window6", ell_moment_window(&sp, &omega_t, tgt.gamma, rw));
        series_push(rec, "ell_kin_peak", (tgt.gamma / (PI * wmax)).sqrt());
        let resid = ((s.px - s0.px - impulse.0).powi(2) + (s.py - s0.py - impulse.1).powi(2)).sqrt();
        series_push(rec, "t", t);
        series_push(rec, "ell_target", tgt.ell(t));
        series_push(rec, "ell_ref", ell_ref);
        series_push(rec, "ell_kin", ell_kin);
        series_push(rec, "lag", ell_kin / ell_ref - 1.0);
        series_push(rec, "k_omega", sp.k_omega(&w_hat));
        series_push(rec, "k_omega_ref", sp.k_omega(&wt_hat));
        series_push(rec, "omega_max", omega.iter().fold(0.0f64, |a, &b| a.max(b.abs())));
        series_push(rec, "mach", s.max_speed);
        series_push(rec, "kn", cfg.lambda / ell_kin);
        series_push(rec, "max_abs_rho_minus_1", s.max_drho);
        series_push(rec, "noneq_fraction", s.noneq_l1 / s.abs_l1);
        series_push(rec, "H", s.h * area);
        series_push(rec, "negative_mass_fraction", s.negative_mass / s.mass);
        series_push(rec, "mass_drift", (s.mass - s0.mass).abs() / s0.mass);
        series_push(rec, "momentum_balance_residual", resid / (s.mass * s.max_speed.max(1e-300)));
        (ell_kin, ell_ref, s.max_speed)
    };

    sample(&kin, t0, impulse, &mut rec);
    let (mut gx, mut gy) = tgt.forcing_velocity(&sp, t0);
    let add = |imp: &mut (f64, f64), d: (f64, f64)| {
        imp.0 += d.0;
        imp.1 += d.1;
    };
    // Validity limit: stop (keeping everything recorded so far) once the flow leaves the
    // range the Q-node lattice represents: sampled Mach >= 0.5 v_max, or any velocity clamp.
    let mach_stop = 0.5 * vmax;
    let mut termination = json!({"reason": "reached_blowup_time", "t": t_end});
    let (d, ncl) = kin.collide_force(0.5 * h, Some((&gx, &gy)), 0.5 * h);
    add(&mut impulse, d);
    let mut steps_done = 0;
    'outer: for step in 0..nsteps {
        if ncl > 0 {
            break;
        }
        kin.stream(h);
        let t = t0 + (step + 1) as f64 * h;
        let (fx, fy) = tgt.forcing_velocity(&sp, t);
        gx = fx;
        gy = fy;
        let last = step + 1 == nsteps;
        let near = tgt.ell(t) < 2.0 * cfg.lambda;
        let do_sample = last || near || (step + 1) % cfg.sample_every == 0;
        let mut ops: Vec<(f64, bool)> = vec![]; // (sub-step, sample after)
        if do_sample {
            ops.push((0.5 * h, true));
            if !last {
                ops.push((0.5 * h, false));
            }
        } else {
            ops.push((h, false));
        }
        for (sub, smp) in ops {
            let (d, nc) = kin.collide_force(sub, Some((&gx, &gy)), sub);
            add(&mut impulse, d);
            if nc > 0 {
                termination = json!({"reason": "velocity_left_lattice_span_clamped", "t": t, "points": nc,
                                     "ell_target_over_lambda": tgt.ell(t) / cfg.lambda});
                break 'outer;
            }
            if smp {
                let (lk, lr, ma) = sample(&kin, t, impulse, &mut rec);
                if verbose && ((step + 1) % (cfg.sample_every * 10) == 0 || last) {
                    eprintln!(
                        "  step {}/{} t={:.4} l_tgt={:.4} l_ref={:.4} l_kin={:.4} lag={:+.3} Ma={:.3} wall={:.0}s",
                        step + 1, nsteps, t, tgt.ell(t), lr, lk, lk / lr - 1.0, ma, wall.elapsed().as_secs_f64()
                    );
                }
                if ma >= mach_stop {
                    termination = json!({"reason": "mach_above_half_lattice_span", "t": t, "mach": ma,
                                         "ell_target_over_lambda": tgt.ell(t) / cfg.lambda});
                    if verbose {
                        eprintln!("  stop: Mach {ma:.3} >= {mach_stop:.3} at l_tgt/lambda={:.3}", tgt.ell(t) / cfg.lambda);
                    }
                    steps_done = step + 1;
                    break 'outer;
                }
            }
        }
        steps_done = step + 1;
    }
    let _ = ncl;
    let kin_wall = wall.elapsed().as_secs_f64();
    let nse = run_nse_control(&tgt, &sp, t0, h, cfg.lambda, cfg.sample_every);
    json!({
        "config": {
            "lambda": cfg.lambda, "tau": tau, "nu": nu, "re_core": cfg.re_core, "Q": cfg.q, "N": n,
            "dx": sp.dx, "dx_over_lambda": sp.dx / cfg.lambda, "l0": cfg.l0, "T": tgt.t_blowup,
            "gamma": tgt.gamma, "l_start": l_start, "t_start": t0, "dt": h, "dt_over_tau": h / tau,
            "steps": nsteps, "lattice_vmax": vmax, "wall_s": kin_wall,
            "nu_eff_strang_over_nu": (h / 2.0) / ((h / (2.0 * tau)).tanh()) / tau,
        },
        "kinetic": Value::Object(rec),
        "termination": termination,
        "steps_done": steps_done,
        "nse_control": nse,
    })
}

/// 2D incompressible NSE in vorticity form with the same target forcing, IF-RK4,
/// 2/3 dealiasing, CFL-limited substeps within each kinetic step h.
pub fn run_nse_control(tgt: &Target, sp: &Spectral2D, t0: f64, h: f64, lambda: f64, sample_every: usize) -> Value {
    let n = sp.n;
    let kmax = n as f64 / 3.0;
    let k2: Vec<f64> = (0..n * n).map(|p| sp.k[p % n].powi(2) + sp.k[p / n].powi(2)).collect();
    let mask: Vec<f64> = (0..n * n)
        .map(|p| if sp.k[p % n].abs() < kmax && sp.k[p / n].abs() < kmax && !sp.is_nyquist(p % n, p / n) { 1.0 } else { 0.0 })
        .collect();
    let nu = tgt.nu;
    let rhs = |w: &[C], t: f64| -> Vec<C> {
        let (uxh, uyh) = sp.velocity_from_vorticity_hat(w);
        let mut wx = vec![C::new(0.0, 0.0); n * n];
        let mut wy = vec![C::new(0.0, 0.0); n * n];
        for p in 0..n * n {
            if !sp.is_nyquist(p % n, p / n) {
                wx[p] = C::new(0.0, sp.k[p % n]) * w[p];
                wy[p] = C::new(0.0, sp.k[p / n]) * w[p];
            }
        }
        let (ux, uy, dwx, dwy) = (sp.inverse(&uxh), sp.inverse(&uyh), sp.inverse(&wx), sp.inverse(&wy));
        let adv: Vec<f64> = (0..n * n).into_par_iter().map(|p| ux[p] * dwx[p] + uy[p] * dwy[p]).collect();
        let advh = sp.forward(&adv);
        let fh = tgt.forcing_omega_hat(sp, t);
        (0..n * n).map(|p| -advh[p] * mask[p] + fh[p]).collect()
    };
    let mut w = tgt.omega_hat(sp, t0);
    let mut rec = serde_json::Map::new();
    let t_end = tgt.t_blowup;
    let nsteps = ((t_end - t0) / h).round() as usize;
    let mut t = t0;
    for step in 0..nsteps {
        let t_next = t0 + (step + 1) as f64 * h;
        while t < t_next - 1e-12 * h {
            let (uxh, uyh) = sp.velocity_from_vorticity_hat(&w);
            let (ux, uy) = (sp.inverse(&uxh), sp.inverse(&uyh));
            let umax = ux.iter().zip(&uy).fold(0.0f64, |a, (x, y)| a.max(x.abs() + y.abs()));
            let hs = (t_next - t).min(0.5 * sp.dx / umax.max(1e-12));
            let e: Vec<f64> = k2.iter().map(|k| (-nu * k * hs).exp()).collect();
            let e2: Vec<f64> = k2.iter().map(|k| (-nu * k * hs / 2.0).exp()).collect();
            let a: Vec<C> = rhs(&w, t).iter().map(|x| x * hs).collect();
            let wb: Vec<C> = (0..n * n).map(|p| e2[p] * (w[p] + a[p] / 2.0)).collect();
            let b: Vec<C> = rhs(&wb, t + hs / 2.0).iter().map(|x| x * hs).collect();
            let wc: Vec<C> = (0..n * n).map(|p| e2[p] * w[p] + b[p] / 2.0).collect();
            let c: Vec<C> = rhs(&wc, t + hs / 2.0).iter().map(|x| x * hs).collect();
            let wd: Vec<C> = (0..n * n).map(|p| e[p] * w[p] + e2[p] * c[p]).collect();
            let d: Vec<C> = rhs(&wd, t + hs).iter().map(|x| x * hs).collect();
            w = (0..n * n).map(|p| e[p] * w[p] + (e[p] * a[p] + 2.0 * e2[p] * (b[p] + c[p]) + d[p]) / 6.0).collect();
            t += hs;
        }
        t = t_next;
        let last = step + 1 == nsteps;
        if last || tgt.ell(t) < 2.0 * lambda || (step + 1) % sample_every == 0 {
            let omega = sp.inverse(&w);
            let wt = tgt.omega_hat(sp, t);
            let ell = ell_moment(sp, &omega, tgt.gamma);
            let omega_t = sp.inverse(&wt);
            let ell_ref = ell_moment(sp, &omega_t, tgt.gamma);
            let wmax = omega.iter().fold(0.0f64, |a, &b| a.max(b.abs()));
            series_push(&mut rec, "ell_nse_window6", ell_moment_window(sp, &omega, tgt.gamma, 6.0 * lambda));
            series_push(&mut rec, "ell_ref_window6", ell_moment_window(sp, &omega_t, tgt.gamma, 6.0 * lambda));
            series_push(&mut rec, "ell_nse_peak", (tgt.gamma / (PI * wmax)).sqrt());
            let (uxh, uyh) = sp.velocity_from_vorticity_hat(&w);
            let (ux, uy) = (sp.inverse(&uxh), sp.inverse(&uyh));
            let umax = ux.iter().zip(&uy).fold(0.0f64, |a, (x, y)| a.max((x * x + y * y).sqrt()));
            series_push(&mut rec, "t", t);
            series_push(&mut rec, "ell_nse", ell);
            series_push(&mut rec, "ell_ref", ell_ref);
            series_push(&mut rec, "lag", ell / ell_ref - 1.0);
            series_push(&mut rec, "k_omega", sp.k_omega(&w));
            series_push(&mut rec, "u_max", umax);
        }
    }
    Value::Object(rec)
}
