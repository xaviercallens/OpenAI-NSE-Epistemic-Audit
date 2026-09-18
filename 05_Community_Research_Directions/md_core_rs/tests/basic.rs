use md_core_rs::md::{langevin, System};
use md_core_rs::rng::normal2;
use md_core_rs::vortex::{Target, PEAK};

#[test]
fn rng_normal_moments() {
    let n = 200_000u64;
    let (mut m1, mut m2, mut m4) = (0.0, 0.0, 0.0);
    for i in 0..n {
        let (a, _) = normal2(42, 3, i, 0);
        m1 += a;
        m2 += a * a;
        m4 += a * a * a * a;
    }
    let nf = n as f64;
    assert!((m1 / nf).abs() < 0.01);
    assert!((m2 / nf - 1.0).abs() < 0.01);
    assert!(((m4 / nf) / (m2 / nf).powi(2) - 3.0).abs() < 0.05);
}

#[test]
fn forces_sum_to_zero_and_energy_is_conserved() {
    let mut s = System::new_lattice(0.3, 12.0, 8.0, 1.5, 7);
    let none = |_: f64, _: f64, _: f64| (0.0, 0.0);
    // short thermostatted melt, then NVE
    for k in 0..400 {
        let th = |i: usize, _x: f64, _y: f64, vx: f64, vy: f64, vz: f64| langevin(7, k, i, 1.0, 0.004, 1.5, (0.0, 0.0), (vx, vy, vz));
        s.step(0.004, 0.0, &none, &th);
    }
    let fsum: f64 = s.fx.iter().sum::<f64>().abs() + s.fy.iter().sum::<f64>().abs() + s.fz.iter().sum::<f64>().abs();
    assert!(fsum < 1e-8 * s.n as f64, "net force {fsum}");
    s.zero_momentum();
    let idt = |_: usize, _: f64, _: f64, vx: f64, vy: f64, vz: f64| (vx, vy, vz);
    let e0 = s.kinetic() + s.pe;
    for _ in 0..1500 {
        s.step(0.004, 0.0, &none, &idt);
    }
    let de = ((s.kinetic() + s.pe - e0) / s.n as f64).abs();
    assert!(de < 2e-4 * 1.5 * s.temperature(), "energy drift per particle {de}");
    let (px, py, pz) = s.momentum();
    assert!((px.abs() + py.abs() + pz.abs()) / (s.n as f64) < 1e-10);
}

#[test]
fn target_is_reynolds_number_re_core() {
    let t = Target::new(1.5, 16.0, 40.0, true);
    // peak of u_theta * l / nu equals Re
    let l = t.ell(100.0);
    let mut umax: f64 = 0.0;
    for k in 1..4000 {
        umax = umax.max(t.u_theta(k as f64 * 0.01 * l / 10.0, l));
    }
    assert!((umax * l / t.nu / 16.0 - 1.0).abs() < 1e-3, "{}", umax * l / t.nu);
    assert!((PEAK - 0.63817).abs() < 1e-4);
    assert!((t.ell(t.t_blow * 0.75) - 20.0).abs() < 1e-9);
}
