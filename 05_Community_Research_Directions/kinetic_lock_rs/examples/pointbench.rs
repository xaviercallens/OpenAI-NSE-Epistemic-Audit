use kinetic_lock_rs::lattice::{collide_force_point, entropic_newton_1d, Lattice, PointScratch};
use std::time::Instant;
fn main() {
    let q = 24;
    let lat = Lattice::new(q);
    let mut s = PointScratch::new(q);
    let mut f = vec![0.0; q * q];
    lat.equilibrium(1.0, 0.3, -0.2, &mut f);
    let reps = 200000;
    let t = Instant::now();
    for k in 0..reps {
        collide_force_point(&lat, &mut f, 0.9, [1e-4 * ((k % 3) as f64 - 1.0), 0.0], &mut s);
    }
    println!("collide_force_point: {:.2} us", t.elapsed().as_secs_f64() / reps as f64 * 1e6);
    let mut e = vec![0.0; q];
    let t = Instant::now();
    let mut it = 0;
    for k in 0..reps {
        it += entropic_newton_1d(&lat.gh, 0.3 + 1e-6 * k as f64, &mut e).iters;
    }
    println!("newton: {:.3} us, mean iters {:.2}", t.elapsed().as_secs_f64() / reps as f64 * 1e6, it as f64 / reps as f64);
}
