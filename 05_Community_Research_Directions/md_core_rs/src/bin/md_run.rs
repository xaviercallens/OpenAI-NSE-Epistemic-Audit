//! md_run --mode equil|vortex [options] --out file.json
//!
//! equil : global Langevin equilibration, then NVE measurement (gates M1, M2).
//! vortex: equilibrate, superimpose the Lamb-Oseen target at l_start, then run with the Langevin buffer
//!         outside R_b; --force on = forced collapse (l^2 = l_s^2 - nu t, stops at l_end),
//!         --force off = free decay / buffer test for --t-run (gates M4, M5).
use md_core_rs::md::{langevin, System};
use md_core_rs::vortex::{smoothstep, Target};
use serde_json::json;
use std::f64::consts::PI;
use std::time::Instant;

fn arg(name: &str) -> Option<String> {
    let a: Vec<String> = std::env::args().collect();
    a.iter().position(|x| x == name).map(|i| a.get(i + 1).cloned().unwrap_or_default())
}
fn argf(name: &str, d: f64) -> f64 {
    arg(name).map(|x| x.parse().unwrap()).unwrap_or(d)
}
fn argu(name: &str, d: usize) -> usize {
    arg(name).map(|x| x.parse().unwrap()).unwrap_or(d)
}

/// radial bin edges: 1 sigma to 30, 2 sigma to 60, 5 sigma beyond, up to L/2
fn bin_edges(rmax: f64) -> Vec<f64> {
    let mut e = vec![0.0];
    let mut r = 0.0;
    while r < rmax - 1e-9 {
        r += if r < 30.0 - 1e-9 { 1.0 } else if r < 60.0 - 1e-9 { 2.0 } else { 5.0 };
        e.push(r.min(rmax));
    }
    e
}

struct Bins {
    edges: Vec<f64>,
    cnt: Vec<f64>,
    st: Vec<f64>,
    sr: Vec<f64>,
    sz: Vec<f64>,
    s2: Vec<f64>,
    srr: Vec<f64>,
    wrr: Vec<f64>,
    wtr: Vec<f64>,
    samples: usize,
}
impl Bins {
    fn new(edges: Vec<f64>) -> Self {
        let n = edges.len() - 1;
        Bins { edges, cnt: vec![0.0; n], st: vec![0.0; n], sr: vec![0.0; n], sz: vec![0.0; n], s2: vec![0.0; n], srr: vec![0.0; n], wrr: vec![0.0; n], wtr: vec![0.0; n], samples: 0 }
    }
    fn clear(&mut self) {
        for v in [&mut self.cnt, &mut self.st, &mut self.sr, &mut self.sz, &mut self.s2, &mut self.srr, &mut self.wrr, &mut self.wtr] {
            v.iter_mut().for_each(|a| *a = 0.0);
        }
        self.samples = 0;
    }
    fn index(&self, r: f64) -> Option<usize> {
        if r >= *self.edges.last().unwrap() {
            return None;
        }
        let b = if r < 30.0 { r as usize } else if r < 60.0 { 30 + ((r - 30.0) / 2.0) as usize } else { 45 + ((r - 60.0) / 5.0) as usize };
        Some(b.min(self.cnt.len() - 1))
    }
    fn sample(&mut self, s: &System) {
        let c = 0.5 * s.l;
        for i in 0..s.n {
            let (dx, dy) = (s.x[i] - c, s.y[i] - c);
            let r = (dx * dx + dy * dy).sqrt();
            if let Some(b) = self.index(r) {
                let (er_x, er_y) = if r > 1e-12 { (dx / r, dy / r) } else { (1.0, 0.0) };
                let vr = s.vx[i] * er_x + s.vy[i] * er_y;
                let vt = -s.vx[i] * er_y + s.vy[i] * er_x;
                self.cnt[b] += 1.0;
                self.st[b] += vt;
                self.sr[b] += vr;
                self.sz[b] += s.vz[i];
                self.s2[b] += s.vx[i] * s.vx[i] + s.vy[i] * s.vy[i] + s.vz[i] * s.vz[i];
                if s.stress {
                    self.srr[b] += vr * vr;
                    self.wrr[b] += er_x * er_x * s.wxx[i] + 2.0 * er_x * er_y * s.wxy[i] + er_y * er_y * s.wyy[i];
                    self.wtr[b] += s.wxx[i] + s.wyy[i] + s.wzz[i];
                }
            }
        }
        self.samples += 1;
    }
    /// window record: mean count per sample, density, u_theta, u_r, temperature of peculiar motion
    fn record(&self, lz: f64) -> serde_json::Value {
        let nb = self.cnt.len();
        let (mut n, mut rho, mut ut, mut ur, mut tt) = (vec![], vec![], vec![], vec![], vec![]);
        let (mut prr, mut piso) = (vec![], vec![]);
        let with_stress = self.wtr.iter().any(|w| *w != 0.0);
        for b in 0..nb {
            let c = self.cnt[b];
            let vol = PI * (self.edges[b + 1].powi(2) - self.edges[b].powi(2)) * lz;
            n.push(c / self.samples.max(1) as f64);
            rho.push(c / self.samples.max(1) as f64 / vol);
            if c > 1.5 {
                let (mt, mr, mz) = (self.st[b] / c, self.sr[b] / c, self.sz[b] / c);
                ut.push(mt);
                ur.push(mr);
                // unbiased-ish: (c/(c-1)) corrects for subtracting the bin mean
                tt.push((self.s2[b] / c - mt * mt - mr * mr - mz * mz) / 3.0 * c / (c - 1.0));
                if with_stress {
                    // local pressure per unit volume: kinetic part of peculiar motion + per-particle virial share
                    let vs = vol * self.samples.max(1) as f64;
                    prr.push(((self.srr[b] - c * mr * mr) + self.wrr[b]) / vs);
                    piso.push(((self.s2[b] - c * (mt * mt + mr * mr + mz * mz)) + self.wtr[b]) / (3.0 * vs));
                }
            } else {
                if with_stress {
                    prr.push(f64::NAN);
                    piso.push(f64::NAN);
                }
                ut.push(f64::NAN);
                ur.push(f64::NAN);
                tt.push(f64::NAN);
            }
        }
        let clean = |v: Vec<f64>| v.into_iter().map(|a| if a.is_finite() { json!(a) } else { json!(null) }).collect::<Vec<_>>();
        let mut rec = json!({"samples": self.samples, "n_per_sample": n, "rho": rho, "u_theta": clean(ut), "u_r": clean(ur), "T": clean(tt)});
        if with_stress {
            rec["p_rr"] = json!(clean(prr));
            rec["p_iso"] = json!(clean(piso));
        }
        rec
    }
}

fn kurtosis(s: &System) -> f64 {
    let mut m2 = 0.0;
    let mut m4 = 0.0;
    for v in [&s.vx, &s.vy, &s.vz] {
        for a in v.iter() {
            m2 += a * a;
            m4 += a * a * a * a;
        }
    }
    let n = 3.0 * s.n as f64;
    (m4 / n) / (m2 / n).powi(2)
}

fn main() {
    let mode = arg("--mode").unwrap_or_else(|| "equil".into());
    let rho = argf("--rho", 0.15);
    let temp = argf("--temp", 2.0);
    let l = argf("--l", 60.0);
    let lz = argf("--lz", 8.0);
    let dt = argf("--dt", 0.004);
    let seed = argu("--seed", 1) as u64;
    let n_eq = argu("--equil-steps", 5000);
    let out = arg("--out").expect("--out");
    let wall = Instant::now();
    let mut s = System::new_lattice(rho, l, lz, temp, seed);
    s.skin = argf("--skin", 1.0);
    s.rebuild();
    s.compute_forces();
    eprintln!("md_run mode={mode} N={} rho_actual={:.5} L={l} Lz={lz} dt={dt} seed={seed}", s.n, s.density());

    // ---- global Langevin equilibration
    let none = |_: f64, _: f64, _: f64| (0.0, 0.0);
    let g_eq = argf("--equil-gamma", 1.0);
    for k in 0..n_eq {
        let th = |i: usize, _x: f64, _y: f64, vx: f64, vy: f64, vz: f64| langevin(seed, k as u64, i, g_eq, dt, temp, (0.0, 0.0), (vx, vy, vz));
        s.step(dt, 0.0, &none, &th);
    }
    s.zero_momentum();
    eprintln!("  equilibrated: T={:.4} p={:.4} ({:.0}s)", s.temperature(), s.pressure(), wall.elapsed().as_secs_f64());

    if mode == "equil" {
        let n_meas = argu("--steps", 20000);
        let every = argu("--sample-every", 50);
        let idt = |_: usize, _: f64, _: f64, vx: f64, vy: f64, vz: f64| (vx, vy, vz);
        let e0 = s.kinetic() + s.pe;
        let (mut ts, mut ps, mut es, mut ku) = (vec![], vec![], vec![], vec![]);
        for k in 0..n_meas {
            s.step(dt, 0.0, &none, &idt);
            if (k + 1) % every == 0 {
                ts.push(s.temperature());
                ps.push(s.pressure());
                es.push((s.kinetic() + s.pe - e0) / s.n as f64);
                ku.push(kurtosis(&s));
            }
        }
        let mean = |v: &Vec<f64>| v.iter().sum::<f64>() / v.len() as f64;
        let ke_pp = 1.5 * mean(&ts);
        let drift = es.last().unwrap().abs().max(es.iter().fold(0.0f64, |a, b| a.max(b.abs())));
        let (px, py, pz) = s.momentum();
        let doc = json!({
            "mode": "equil", "N": s.n, "rho": s.density(), "T_target": temp, "L": l, "Lz": lz, "dt": dt, "seed": seed,
            "equil_steps": n_eq, "nve_steps": n_meas,
            "T_mean": mean(&ts), "p_mean": mean(&ps), "kurtosis_mean": mean(&ku),
            "energy_drift_per_particle_max_abs": drift, "energy_drift_over_KE": drift / ke_pp,
            "momentum_per_particle": [px / s.n as f64, py / s.n as f64, pz / s.n as f64],
            "series": {"T": ts, "p": ps, "dE_per_particle": es},
            "wall_s": wall.elapsed().as_secs_f64(), "rebuilds": s.rebuilds, "skin": s.skin, "t_force": s.t_force, "t_rebuild": s.t_rebuild,
        });
        std::fs::write(&out, serde_json::to_string(&doc).unwrap()).unwrap();
        eprintln!("  T={:.4} p={:.5} kurt={:.4} dE/KE={:.2e}", mean(&ts), mean(&ps), mean(&ku), drift / ke_pp);
        return;
    }

    if mode == "shear" {
        // transverse shear wave v_x = A sin(k y): purely solenoidal, decays as exp(-nu k^2 t) (no density coupling
        // at linear order), so it measures the kinematic viscosity without the compressible adjustment a vortex has.
        let amp = argf("--amp", 0.25);
        let harm = argf("--harmonic", 2.0);
        let k = 2.0 * PI * harm / l;
        let n_meas = argu("--steps", 20000);
        let every = argu("--sample-every", 20);
        for i in 0..s.n {
            s.vx[i] += amp * (k * s.y[i]).sin();
        }
        let idt = |_: usize, _: f64, _: f64, vx: f64, vy: f64, vz: f64| (vx, vy, vz);
        let (mut ts, mut a_s, mut a_c, mut temps) = (vec![], vec![], vec![], vec![]);
        for step in 0..n_meas {
            s.step(dt, 0.0, &none, &idt);
            if (step + 1) % every == 0 {
                let (mut ss, mut cc) = (0.0, 0.0);
                for i in 0..s.n {
                    ss += s.vx[i] * (k * s.y[i]).sin();
                    cc += s.vx[i] * (k * s.y[i]).cos();
                }
                ts.push((step + 1) as f64 * dt);
                a_s.push(2.0 * ss / s.n as f64);
                a_c.push(2.0 * cc / s.n as f64);
                temps.push(s.temperature());
            }
        }
        let doc = json!({"mode": "shear", "N": s.n, "rho": s.density(), "T_target": temp, "L": l, "Lz": lz, "dt": dt, "seed": seed,
            "k": k, "amp0": amp, "t": ts, "a_sin": a_s, "a_cos": a_c, "T_global": temps, "wall_s": wall.elapsed().as_secs_f64()});
        std::fs::write(&out, serde_json::to_string(&doc).unwrap()).unwrap();
        eprintln!("wrote {out}");
        return;
    }

    // ---- vortex modes
    let forced = arg("--force").map(|x| x == "on").unwrap_or(true);
    let nu = argf("--nu", 1.5);
    let re = argf("--re", 16.0);
    let l_start = argf("--l-start", 40.0);
    let l_end = argf("--l-end", 4.0);
    let tgt = Target::new(nu, re, l_start, forced);
    let r_b = argf("--rb", 3.2 * l_start);
    let ramp = argf("--buffer-ramp", 10.0);
    let g_buf = argf("--buffer-gamma", 0.5);
    let half = 0.5 * l;
    let mut hc = half; // vortex centre and box length; move together when the barostat is on
    let mut lc = l;
    let (r1, r2) = (r_b + ramp, half - 4.0); // potential-vortex target tapered to zero between r1 and r2
    assert!(r2 > r1 + 5.0, "box too small for the buffer: need L/2 - 4 > R_b + ramp + 5");
    let gamma_c = tgt.gamma;
    let u_buf = move |r: f64| gamma_c / (2.0 * PI * r.max(1e-9)) * (1.0 - smoothstep((r - r1) / (r2 - r1)));
    let t_run = if forced { (l_start * l_start - l_end * l_end) / nu } else { argf("--t-run", 100.0) };
    let nsteps = (t_run / dt).ceil() as usize;
    let every = argu("--sample-every", 60);
    let (w_min, w_frac) = (argf("--window-min", 2.0), argf("--window-frac", 0.04));
    let w_fixed = argf("--window", 5.0);

    // superimpose the target swirl (tapered like the buffer target so the periodic box is consistent)
    for i in 0..s.n {
        let (dx, dy) = (s.x[i] - half, s.y[i] - half);
        let r = (dx * dx + dy * dy).sqrt().max(1e-9);
        let taper = 1.0 - smoothstep((r - r1) / (r2 - r1));
        let u = tgt.u_theta(r, l_start) * taper;
        s.vx[i] += -u * dy / r;
        s.vy[i] += u * dx / r;
    }

    // Optional weak barostat on the box area: holds the far-ring pressure (0.8-1.0 R_b) at its early-run value, so the
    // ambient pressure does not rise as the emptied core displaces liquid in the closed box (`--baro auto`).
    let baro = arg("--baro").map(|x| x == "auto").unwrap_or(false);
    let (baro_tau, baro_k, baro_every, warm_updates) = (argf("--baro-tau", 10.0), argf("--baro-k", 14.0), 20usize, 25usize);
    s.stress = baro || arg("--stress").map(|x| x == "on").unwrap_or(false);
    let (mut p_sum, mut p_n, mut p_target, mut p_filt, mut baro_updates) = (0.0f64, 0usize, f64::NAN, f64::NAN, 0usize);
    let mut bins = Bins::new(bin_edges(half));
    let mut windows = vec![];
    // axial diagnostic (3D boxes): per z-slab core density and mass-centroid offset near the axis
    let nz_slab = argu("--axial-slabs", ((lz / 6.0).floor() as usize).max(1));
    let (mut ax_cnt, mut ax_sx, mut ax_sy, mut ax_ncore, mut ax_samples) =
        (vec![0.0f64; nz_slab], vec![0.0f64; nz_slab], vec![0.0f64; nz_slab], vec![0.0f64; nz_slab], 0usize);
    let (mut t_win0, mut e_mon) = (0.0, vec![]);
    let tg = tgt.clone();
    for k in 0..nsteps {
        let t = k as f64 * dt;
        let ext = |x: f64, y: f64, tt: f64| {
            if !forced {
                return (0.0, 0.0);
            }
            let (dx, dy) = (x - hc, y - hc);
            let r = (dx * dx + dy * dy).sqrt();
            if r < 1e-9 || r > r_b {
                return (0.0, 0.0);
            }
            let f = tg.force_theta(r, tt.min(tg.t_blow * (1.0 - 1e-9)));
            (-f * dy / r, f * dx / r)
        };
        let th = |i: usize, x: f64, y: f64, vx: f64, vy: f64, vz: f64| {
            let (dx, dy) = (x - hc, y - hc);
            let r = (dx * dx + dy * dy).sqrt();
            if r <= r_b {
                return (vx, vy, vz);
            }
            let g = g_buf * smoothstep((r - r_b) / ramp);
            let u = u_buf(r);
            langevin(seed.wrapping_add(7919), k as u64, i, g, dt, temp, (-u * dy / r, u * dx / r), (vx, vy, vz))
        };
        s.step(dt, t, &ext, &th);
        if baro && (k + 1) % baro_every == 0 {
            let (c, lcur) = (hc, lc);
            let (rin, rout) = (0.8 * r_b, r_b);
            let (mut ke, mut wv) = (0.0f64, 0.0f64);
            for i in 0..s.n {
                let (dx, dy) = (s.x[i].rem_euclid(lcur) - c, s.y[i].rem_euclid(lcur) - c);
                let r2 = dx * dx + dy * dy;
                if r2 < rin * rin || r2 >= rout * rout {
                    continue;
                }
                let r = r2.sqrt();
                let u = tgt.gamma / (2.0 * PI * r);
                let (px, py) = (s.vx[i] + u * dy / r, s.vy[i] - u * dx / r);
                ke += px * px + py * py + s.vz[i] * s.vz[i];
                wv += s.wxx[i] + s.wyy[i] + s.wzz[i];
            }
            let v_ring = PI * (rout * rout - rin * rin) * lz;
            let p_now = (ke + wv) / (3.0 * v_ring);
            p_filt = if p_filt.is_nan() { p_now } else { 0.9 * p_filt + 0.1 * p_now };
            baro_updates += 1;
            if baro_updates <= warm_updates {
                p_sum += p_now;
                p_n += 1;
                if baro_updates == warm_updates {
                    p_target = p_sum / p_n as f64;
                    eprintln!("  barostat target far-ring pressure = {p_target:.4} (mean of first {warm_updates} readings)");
                }
            } else {
                // Berendsen: dV/V = -(dt_b/tau)(p_target - p)/K, xy only so dL/L = dV/V / 2; clamped per update
                let dvv = -(baro_every as f64 * dt / baro_tau) * (p_target - p_filt) / baro_k;
                let eps = (0.5 * dvv).clamp(-5e-4, 5e-4);
                let f = 1.0 + eps;
                s.scale_xy(f);
                hc = 0.5 * s.l;
                lc = s.l;
            }
        }
        if (k + 1) % every == 0 {
            bins.sample(&s);
            let t_now = t + dt;
            if nz_slab > 1 {
                let lt = tgt.ell(t_now);
                let (r_core, r_cen) = ((0.5 * lt).max(2.0), (2.0 * lt).max(6.0));
                for i in 0..s.n {
                    let (dx, dy) = (s.x[i].rem_euclid(lc) - hc, s.y[i].rem_euclid(lc) - hc);
                    let r2 = dx * dx + dy * dy;
                    if r2 > r_cen * r_cen {
                        continue;
                    }
                    let iz = (((s.z[i].rem_euclid(lz)) / lz * nz_slab as f64) as usize).min(nz_slab - 1);
                    ax_cnt[iz] += 1.0;
                    ax_sx[iz] += dx;
                    ax_sy[iz] += dy;
                    if r2 < r_core * r_core {
                        ax_ncore[iz] += 1.0;
                    }
                }
                ax_samples += 1;
            }
            let w_len = if forced { w_min.max(w_frac * (tgt.t_blow - t_now)) } else { w_fixed };
            if t_now - t_win0 >= w_len || k + 1 == nsteps {
                let t_mid = 0.5 * (t_win0 + t_now);
                let mut rec = bins.record(lz);
                rec["t_mid"] = json!(t_mid);
                rec["t0"] = json!(t_win0);
                rec["t1"] = json!(t_now);
                rec["l_target"] = json!(tgt.ell(t_mid));
                if nz_slab > 1 && ax_samples > 0 {
                    let ns = ax_samples as f64;
                    let lt = tgt.ell(t_mid);
                    let (r_core, r_cen) = ((0.5 * lt).max(2.0), (2.0 * lt).max(6.0));
                    let vol_core = PI * r_core * r_core * lz / nz_slab as f64;
                    rec["axial"] = json!({
                        "slabs": nz_slab, "samples": ax_samples, "r_core": r_core, "r_centroid": r_cen,
                        "core_density": ax_ncore.iter().map(|c| c / ns / vol_core).collect::<Vec<f64>>(),
                        "n_centroid_per_sample": ax_cnt.iter().map(|c| c / ns).collect::<Vec<f64>>(),
                        "centroid_x": ax_sx.iter().zip(&ax_cnt).map(|(a, c)| if *c > 0.0 { a / c } else { 0.0 }).collect::<Vec<f64>>(),
                        "centroid_y": ax_sy.iter().zip(&ax_cnt).map(|(a, c)| if *c > 0.0 { a / c } else { 0.0 }).collect::<Vec<f64>>(),
                    });
                    for v in [&mut ax_cnt, &mut ax_sx, &mut ax_sy, &mut ax_ncore] {
                        v.iter_mut().for_each(|x| *x = 0.0);
                    }
                    ax_samples = 0;
                }
                windows.push(rec);
                e_mon.push(json!({"t": t_now, "L": s.l, "p_far_filtered": p_filt, "T_global": s.temperature(), "p_global": s.pressure(), "pe_per_particle": s.pe / s.n as f64}));
                bins.clear();
                t_win0 = t_now;
                if windows.len() % 10 == 0 {
                    eprintln!("  t={:.1}/{:.1} l_target={:.2} T_glob={:.3} wall={:.0}s", t_now, t_run, tgt.ell(t_now), s.temperature(), wall.elapsed().as_secs_f64());
                }
            }
        }
    }
    let edges = bins.edges.clone();
    let doc = json!({
        "mode": "vortex", "forced": forced, "N": s.n, "rho": s.density(), "T_inf": temp, "L": l, "Lz": lz, "dt": dt, "seed": seed,
        "nu_used": nu, "re": re, "l_start": l_start, "l_end": l_end, "Gamma": tgt.gamma, "t_blow": tgt.t_blow, "t_run": t_run,
        "R_b": r_b, "buffer": {"ramp": ramp, "gamma": g_buf, "swirl_taper_r1": r1, "swirl_taper_r2": r2},
        "sample_every_steps": every, "equil_steps": n_eq,
        "bin_edges": edges, "windows": windows, "monitor": e_mon, "L_end": s.l, "baro": baro, "baro_target_p": if baro { json!(p_target) } else { json!(null) }, "wall_s": wall.elapsed().as_secs_f64(),
    });
    std::fs::write(&out, serde_json::to_string(&doc).unwrap()).unwrap();
    eprintln!("wrote {out} ({:.0}s)", wall.elapsed().as_secs_f64());
}
