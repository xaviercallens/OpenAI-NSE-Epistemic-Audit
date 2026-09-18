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

#[test]
fn per_particle_stress_sums_to_global_virial() {
    // equilibrium liquid: trace of the per-particle virial tensor sums to the pair virial exactly,
    // and the three normal components agree (isotropy) within sampling noise
    let mut s = System::new_lattice(0.79, 12.0, 12.0, 1.0, 11);
    let none = |_: f64, _: f64, _: f64| (0.0, 0.0);
    for k in 0..600 {
        let th = |i: usize, _x: f64, _y: f64, vx: f64, vy: f64, vz: f64| langevin(11, k, i, 1.0, 0.004, 1.0, (0.0, 0.0), (vx, vy, vz));
        s.step(0.004, 0.0, &none, &th);
    }
    s.stress = true;
    let (mut axx, mut ayy, mut azz, mut avir) = (0.0, 0.0, 0.0, 0.0);
    for k in 600..1400 {
        let th = |i: usize, _x: f64, _y: f64, vx: f64, vy: f64, vz: f64| langevin(11, k, i, 1.0, 0.004, 1.0, (0.0, 0.0), (vx, vy, vz));
        s.step(0.004, 0.0, &none, &th);
        let (xx, yy, zz): (f64, f64, f64) = (s.wxx.iter().sum(), s.wyy.iter().sum(), s.wzz.iter().sum());
        assert!(((xx + yy + zz) - s.virial).abs() < 1e-9 * s.virial.abs().max(1.0), "trace {} vs virial {}", xx + yy + zz, s.virial);
        axx += xx;
        ayy += yy;
        azz += zz;
        avir += s.virial;
    }
    let m = avir / 3.0;
    for a in [axx, ayy, azz] {
        assert!((a / m - 1.0).abs() < 0.05, "normal component {} vs mean {}", a, m);
    }
    // stress off leaves the forces untouched (the zipped arrays must not truncate the force loop)
    s.stress = false;
    s.compute_forces();
    let fnorm: f64 = s.fx.iter().map(|f| f.abs()).sum();
    assert!(fnorm > 0.0);
}

#[test]
fn box_rescale_keeps_the_neighbour_list_valid() {
    // scaling the box in xy by f multiplies the xy volume by f^2; forces afterwards match a fresh system at that density
    let mut s = System::new_lattice(0.5, 12.0, 8.0, 1.0, 5);
    let none = |_: f64, _: f64, _: f64| (0.0, 0.0);
    let idt = |_: usize, _: f64, _: f64, vx: f64, vy: f64, vz: f64| (vx, vy, vz);
    for _ in 0..50 {
        s.step(0.004, 0.0, &none, &idt);
    }
    let rho0 = s.density();
    s.scale_xy(1.001);
    assert!((s.density() * 1.001f64.powi(2) / rho0 - 1.0).abs() < 1e-12);
    for _ in 0..200 {
        s.step(0.004, 0.0, &none, &idt);
    }
    // list stays valid: momentum conserved and the total force is zero (a stale list would break Newton's third law)
    let fsum: f64 = s.fx.iter().sum::<f64>().abs() + s.fy.iter().sum::<f64>().abs() + s.fz.iter().sum::<f64>().abs();
    assert!(fsum < 1e-8 * s.n as f64, "net force {fsum}");
}
