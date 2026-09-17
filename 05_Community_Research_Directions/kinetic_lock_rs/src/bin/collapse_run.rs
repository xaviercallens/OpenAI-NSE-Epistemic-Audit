//! One forced-collapse run (kinetic + NSE control). Writes a JSON file.
//! Usage: collapse_run --lambda 0.045 --re 1 [--q 24] [--n auto] [--dx-over-lambda 0.667]
//!                     [--dt-over-tau 0.05] [--lstart 20] [--l0 0.8] [--sample-every 10] --out file
//!        collapse_run --bench --n 480 --q 24   (timing only)

use kinetic_lock_rs::forced::{fast_size, run_collapse, CollapseConfig};
use kinetic_lock_rs::solver::Kinetic;
use std::f64::consts::PI;
use std::time::Instant;

fn arg(name: &str) -> Option<String> {
    let a: Vec<String> = std::env::args().collect();
    a.iter().position(|x| x == name).map(|i| a.get(i + 1).cloned().unwrap_or_default())
}

fn main() {
    let q: usize = arg("--q").map(|x| x.parse().unwrap()).unwrap_or(24);
    if arg("--bench").is_some() {
        let n: usize = arg("--n").unwrap().parse().unwrap();
        let mut kin = Kinetic::new(q, n, 0.05);
        let rho = vec![1.0; n * n];
        let ux: Vec<f64> = (0..n * n).map(|p| 0.1 * ((p % n) as f64 * 2.0 * PI / n as f64).sin()).collect();
        let uy = vec![0.0; n * n];
        kin.set_equilibrium(&rho, &ux, &uy);
        let t = Instant::now();
        for _ in 0..3 {
            kin.stream(0.01);
        }
        let ts = t.elapsed().as_secs_f64() / 3.0;
        let t = Instant::now();
        for _ in 0..3 {
            kin.collide_force(0.01, None, 0.0);
        }
        let tc = t.elapsed().as_secs_f64() / 3.0;
        let t = Instant::now();
        let _ = kin.sums();
        let td = t.elapsed().as_secs_f64();
        println!("N={n} Q={q}: stream {ts:.3}s collide {tc:.3}s sums {td:.3}s per call");
        return;
    }
    let lambda: f64 = arg("--lambda").unwrap().parse().unwrap();
    let re: f64 = arg("--re").unwrap().parse().unwrap();
    let dx_over_lambda: f64 = arg("--dx-over-lambda").map(|x| x.parse().unwrap()).unwrap_or(1.0 / 1.5);
    let n: usize = arg("--n").map(|x| x.parse().unwrap()).unwrap_or_else(|| fast_size(2.0 * PI / (dx_over_lambda * lambda)));
    let cfg = CollapseConfig {
        lambda,
        re_core: re,
        q,
        n,
        l0: arg("--l0").map(|x| x.parse().unwrap()).unwrap_or(0.8),
        lstart_over_lambda: arg("--lstart").map(|x| x.parse().unwrap()).unwrap_or(20.0),
        dt_over_tau: arg("--dt-over-tau").map(|x| x.parse().unwrap()).unwrap_or(0.05),
        sample_every: arg("--sample-every").map(|x| x.parse().unwrap()).unwrap_or(10),
    };
    let out = arg("--out").expect("--out");
    eprintln!("collapse_run {cfg:?}");
    let doc = run_collapse(cfg, true);
    std::fs::write(&out, serde_json::to_string(&doc).unwrap()).unwrap();
    eprintln!("wrote {out}");
}
