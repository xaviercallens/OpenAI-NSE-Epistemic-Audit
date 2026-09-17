//! Unit tests for gates G1 (entropic Newton equilibrium) and G2 (exact collision).

use kinetic_lock_rs::dispersion::erfcx;
use kinetic_lock_rs::lattice::{collide_force_point, entropic_newton_1d, GaussHermite, Lattice, PointScratch};

const QS: [usize; 3] = [12, 16, 24];

/// Deterministic pseudo-random numbers in [0, 1).
fn lcg(state: &mut u64) -> f64 {
    *state = state.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
    (*state >> 11) as f64 / (1u64 << 53) as f64
}

fn double_factorial_odd(n: usize) -> f64 {
    // (n-1)!! for even n: E[v^n] of a unit Gaussian
    (1..n).step_by(2).map(|k| k as f64).product()
}

#[test]
fn gauss_hermite_moments_exact() {
    for q in QS {
        let gh = GaussHermite::new(q);
        for p in 0..2 * q {
            let m: f64 = gh.v.iter().zip(&gh.w).map(|(v, w)| w * v.powi(p as i32)).sum();
            let scale: f64 = gh.v.iter().zip(&gh.w).map(|(v, w)| w * v.abs().powi(p as i32)).sum();
            let exact = if p % 2 == 1 { 0.0 } else { double_factorial_odd(p) };
            assert!((m - exact).abs() <= 1e-12 * scale.max(1.0), "Q={q} p={p}: {m} vs {exact}");
        }
    }
}

#[test]
fn g1_newton_moments_exact_and_b_to_u() {
    let us = [0.0, 0.05, -0.2, 0.5, -0.8, 1.0, 1.5];
    let mut prev: Vec<f64> = vec![f64::INFINITY; us.len()];
    for q in QS {
        let lat = Lattice::new(q);
        let mut feq = vec![0.0; q * q];
        for (iu, &ux) in us.iter().enumerate() {
            for &uy in &us {
                let rho = 0.7 + 0.1 * (iu as f64);
                let (nx, ny) = lat.equilibrium(rho, ux, uy, &mut feq);
                let (r, jx, jy) = lat.moments(&feq);
                let scale = rho * (1.0 + ux.abs() + uy.abs());
                assert!((r - rho).abs() <= 1e-13 * scale, "Q={q} mass");
                assert!((jx - rho * ux).abs() <= 1e-13 * scale, "Q={q} ux={ux} jx err {}", (jx - rho * ux).abs());
                assert!((jy - rho * uy).abs() <= 1e-13 * scale, "Q={q} uy={uy}");
                assert!(nx.iters <= 20 && ny.iters <= 20);
                assert!(feq.iter().all(|&x| x > 0.0));
            }
            // b -> u: the tilt parameter converges to the continuum value as Q grows
            let gh = GaussHermite::new(q);
            let mut e = vec![0.0; q];
            let sol = entropic_newton_1d(&gh, ux, &mut e);
            let err = (sol.b - ux).abs();
            assert!(err <= prev[iu] + 1e-15, "Q={q} u={ux}: |b-u|={err} not <= previous {}", prev[iu]);
            prev[iu] = err;
        }
    }
    // at Q=24 the discrete tilt equals the continuum one closely for |u| <= 1
    for (iu, &u) in us.iter().enumerate() {
        if u.abs() <= 1.0 {
            assert!(prev[iu] < 1e-8, "Q=24 u={u}: |b-u|={}", prev[iu]);
        }
    }
}

#[test]
fn g2_collision_conserves_and_h_nonincreasing() {
    let mut st = 7u64;
    for q in QS {
        let lat = Lattice::new(q);
        let mut s = PointScratch::new(q);
        for trial in 0..20 {
            // far-from-equilibrium positive distribution with a drift
            let mut f: Vec<f64> = (0..q * q)
                .map(|m| lat.w[m] * (0.2 + 1.6 * lcg(&mut st)) * (1.0 + 0.4 * lat.vx[m] * (trial as f64 / 20.0)).max(0.05))
                .collect();
            let (r0, jx0, jy0) = lat.moments(&f);
            let mut h_prev = lat.h_function(&f);
            for k in 0..40 {
                let a = (-(0.05 + 0.1 * k as f64)).exp();
                collide_force_point(&lat, &mut f, a, [0.0, 0.0], &mut s);
                let (r, jx, jy) = lat.moments(&f);
                assert!((r - r0).abs() <= 1e-13 * r0, "Q={q} mass drift {}", (r - r0).abs() / r0);
                assert!((jx - jx0).abs() <= 1e-13 * r0 && (jy - jy0).abs() <= 1e-13 * r0, "Q={q} momentum");
                let h = lat.h_function(&f);
                assert!(h <= h_prev + 1e-14 * h_prev.abs().max(1.0), "Q={q} H increased {h_prev} -> {h}");
                h_prev = h;
            }
        }
    }
}

#[test]
fn g2_exact_difference_force_adds_rho_du() {
    let q = 16;
    let lat = Lattice::new(q);
    let mut s = PointScratch::new(q);
    let mut f = vec![0.0; q * q];
    lat.equilibrium(1.3, 0.2, -0.1, &mut f);
    let du = [0.03, -0.07];
    let (r0, jx0, jy0) = lat.moments(&f);
    collide_force_point(&lat, &mut f, 0.6, du, &mut s);
    let (r, jx, jy) = lat.moments(&f);
    assert!((r - r0).abs() <= 1e-13 * r0);
    assert!((jx - jx0 - r0 * du[0]).abs() <= 1e-13 * r0);
    assert!((jy - jy0 - r0 * du[1]).abs() <= 1e-13 * r0);
}

#[test]
fn erfcx_branches_agree() {
    // series (x < 2.5) vs continued fraction near the switch, and known values
    assert!((erfcx(0.0) - 1.0).abs() < 1e-15);
    assert!((erfcx(1.0) - 0.427_583_576_155_807).abs() < 1e-13);
    assert!((erfcx(2.4999999) - erfcx(2.5)).abs() < 1e-8);
    assert!((erfcx(5.0) - 0.110_704_637_733_069).abs() < 1e-13);
}
