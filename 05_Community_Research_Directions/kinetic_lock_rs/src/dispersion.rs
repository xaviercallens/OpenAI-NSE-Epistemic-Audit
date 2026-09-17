//! Linear transverse (shear) spectrum of isothermal BGK, continuous (M1) and on a
//! Q-node Gauss–Hermite lattice (M2(Q)). Units tau = 1, q = k lambda, z = 1 + s tau.
//!
//! A transverse perturbation d f = w(v_y) v_y h(v_x) e^{ikx} obeys
//!   dh/dt = -i k v_x h - (h - w <h>)/tau,
//! whose eigenvalues satisfy  sum_j w_j z/(z^2 + q^2 v_j^2) = 1  (symmetric nodes) and,
//! for the continuous Maxwellian,  sqrt(pi/2)/q * erfcx(z/(sqrt 2 q)) = 1.
//! The hydrodynamic (least-damped real) root has rate Gamma tau = 1 - z.

use num_complex::Complex64 as C;

const SQRT_PI: f64 = 1.772_453_850_905_516;

/// Scaled complementary error function erfcx(x) = exp(x^2) erfc(x), x >= 0.
pub fn erfcx(x: f64) -> f64 {
    assert!(x >= 0.0);
    if x < 2.5 {
        // exp(x^2) - (2/sqrt pi) sum 2^n x^(2n+1)/(2n+1)!!   (all terms positive)
        let mut term = x;
        let mut sum = x;
        let x2 = x * x;
        let mut n = 0.0;
        while term > 1e-17 * sum {
            n += 1.0;
            term *= 2.0 * x2 / (2.0 * n + 1.0);
            sum += term;
        }
        x2.exp() - 2.0 / SQRT_PI * sum
    } else {
        // Laplace continued fraction, evaluated backward.
        let mut t = x;
        for n in (1..=400).rev() {
            t = x + (n as f64 * 0.5) / t;
        }
        1.0 / (SQRT_PI * t)
    }
}

pub fn m1_function(q: f64, z: f64) -> f64 {
    (std::f64::consts::PI / 2.0).sqrt() / q * erfcx(z / (std::f64::consts::SQRT_2 * q)) - 1.0
}

pub fn discrete_function(v: &[f64], w: &[f64], q: f64, z: f64) -> f64 {
    v.iter().zip(w).map(|(&vj, &wj)| wj * z / (z * z + q * q * vj * vj)).sum::<f64>() - 1.0
}

/// Largest root z in (0,1) of a real function with g(1) < 0, found by scanning down
/// from z = 1 and bisecting the first sign change. None if there is no real root.
fn largest_root(g: impl Fn(f64) -> f64) -> Option<f64> {
    let mut grid: Vec<f64> = (0..=4000).map(|k| 1.0 - k as f64 / 4000.0).collect();
    grid.pop(); // drop z = 0
    let mut zz = 2.5e-4;
    while zz > 1e-14 {
        zz *= 0.5;
        grid.push(zz);
    }
    let mut hi = grid[0];
    let mut ghi = g(hi);
    for &lo in &grid[1..] {
        let glo = g(lo);
        if glo.is_finite() && ghi.is_finite() && glo * ghi <= 0.0 {
            let (mut a, mut b) = (lo, hi); // g(a) >= 0 > g(b)
            for _ in 0..200 {
                let m = 0.5 * (a + b);
                if g(m) >= 0.0 { a = m } else { b = m }
                if b - a < 1e-16 {
                    break;
                }
            }
            return Some(0.5 * (a + b));
        }
        hi = lo;
        ghi = glo;
    }
    None
}

/// Exact BGK hydrodynamic shear rate Gamma*tau at q = k lambda, None above sqrt(pi/2).
pub fn m1_rate(q: f64) -> Option<f64> {
    largest_root(|z| m1_function(q, z)).map(|z| 1.0 - z)
}

/// Q-node lattice hydrodynamic rate if the least-damped root is real.
pub fn discrete_real_rate(v: &[f64], w: &[f64], q: f64) -> Option<f64> {
    largest_root(|z| discrete_function(v, w, q, z)).map(|z| 1.0 - z)
}

/// Complex Newton on the lattice dispersion relation from z0; returns s tau = z - 1.
pub fn discrete_root_newton(v: &[f64], w: &[f64], q: f64, z0: C) -> Option<C> {
    let mut z = z0;
    for _ in 0..200 {
        let mut fz = C::new(-1.0, 0.0);
        let mut dfz = C::new(0.0, 0.0);
        for (&vj, &wj) in v.iter().zip(w) {
            let d = z * z + q * q * vj * vj;
            fz += wj * z / d;
            dfz += wj * (q * q * vj * vj - z * z) / (d * d);
        }
        let dz = fz / dfz;
        z -= dz;
        if !z.re.is_finite() {
            return None;
        }
        if dz.norm() < 1e-15 * z.norm().max(1e-3) {
            return Some(z - 1.0);
        }
    }
    None
}

/// Smallest q at which the lattice hydrodynamic root stops being real (bisection).
pub fn discrete_termination(v: &[f64], w: &[f64]) -> f64 {
    let (mut a, mut b) = (0.05, 3.0);
    assert!(discrete_real_rate(v, w, a).is_some());
    if discrete_real_rate(v, w, b).is_some() {
        return f64::INFINITY;
    }
    for _ in 0..60 {
        let m = 0.5 * (a + b);
        if discrete_real_rate(v, w, m).is_some() { a = m } else { b = m }
    }
    0.5 * (a + b)
}

// ---------------------------------------------------------------------------------------
// Full lattice spectra by dense eigenvalues (no root bracketing), tau = 1, k = 1 scaling.

use nalgebra::DMatrix;

/// Eigenvalues of a complex matrix A = R + i I via its real 2n x 2n representation
/// [[R, -I], [I, R]] (spectrum(A) union conj(spectrum(A))).
fn complex_spectrum(re: &DMatrix<f64>, im: &DMatrix<f64>) -> Vec<C> {
    let n = re.nrows();
    let big = DMatrix::from_fn(2 * n, 2 * n, |i, j| match (i < n, j < n) {
        (true, true) => re[(i, j)],
        (true, false) => -im[(i, j - n)],
        (false, true) => im[(i - n, j)],
        (false, false) => re[(i - n, j - n)],
    });
    big.complex_eigenvalues().iter().cloned().collect()
}

fn max_re(z: &[C]) -> C {
    *z.iter().max_by(|a, b| a.re.partial_cmp(&b.re).unwrap()).unwrap()
}

/// Least-damped eigenvalue s tau of the continuous-time lattice operator
/// M = -i q diag(v) - I + 1 w^T  (in y = h/w; similar to the h-space operator).
pub fn lattice_least_damped(v: &[f64], w: &[f64], q: f64) -> C {
    let n = v.len();
    let re = DMatrix::from_fn(n, n, |i, j| w[j] - if i == j { 1.0 } else { 0.0 });
    let im = DMatrix::from_fn(n, n, |i, j| if i == j { -q * v[i] } else { 0.0 });
    let mut s = max_re(&complex_spectrum(&re, &im));
    s.im = s.im.abs();
    s
}

/// One Strang step P = E S E of the solver on the transverse k = 1 mode, in the scaled variable y = h/w,
/// with E = a I + (1-a) 1 w^T (relaxation toward sum_j w_j y_j), a = exp(-dt/(2 tau)), S = diag(exp(-i q v dt/tau)).
pub fn strang_propagator(v: &[f64], w: &[f64], q: f64, dt_over_tau: f64) -> (DMatrix<f64>, DMatrix<f64>) {
    let n = v.len();
    let a = (-dt_over_tau / 2.0).exp();
    let e = DMatrix::from_fn(n, n, |i, j| (1.0 - a) * w[j] + if i == j { a } else { 0.0 });
    let sre = DMatrix::from_fn(n, n, |i, j| if i == j { (q * v[i] * dt_over_tau).cos() } else { 0.0 });
    let sim = DMatrix::from_fn(n, n, |i, j| if i == j { -(q * v[i] * dt_over_tau).sin() } else { 0.0 });
    (&e * sre * &e, &e * sim * &e)
}

/// Least-damped effective exponent s tau = ln(mu)/dt of the Strang propagator.
pub fn strang_least_damped(v: &[f64], w: &[f64], q: f64, dt_over_tau: f64) -> C {
    let (re, im) = strang_propagator(v, w, q, dt_over_tau);
    let mu = *complex_spectrum(&re, &im).iter().max_by(|a, b| a.norm().partial_cmp(&b.norm()).unwrap()).unwrap();
    let mut s = mu.ln() / dt_over_tau;
    s.im = s.im.abs();
    s
}

/// Smallest q at which the lattice's least-damped eigenvalue leaves the real axis.
pub fn lattice_termination(v: &[f64], w: &[f64]) -> f64 {
    let complex = |q: f64| lattice_least_damped(v, w, q).im.abs() > 1e-7;
    let (mut a, mut b) = (0.05, 3.0);
    if complex(a) || !complex(b) {
        return f64::NAN;
    }
    for _ in 0..50 {
        let m = 0.5 * (a + b);
        if complex(m) { b = m } else { a = m }
    }
    0.5 * (a + b)
}
