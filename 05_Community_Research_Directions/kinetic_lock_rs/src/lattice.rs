//! Tensor Gauss–Hermite velocity lattice and the entropic discrete Maxwellian.
//!
//! Units: v_th = 1 (isothermal, RT = 1), so the continuous Maxwellian is
//! phi(v) = exp(-|v|^2/2)/(2 pi). The 1D rule integrates polynomials of degree
//! 2Q-1 against exp(-v^2/2)/sqrt(2 pi); weights are normalised to sum 1.
//!
//! The entropic equilibrium minimises H = sum f ln(f/w) under the collision
//! invariants of isothermal BGK (mass, momentum). Its form is
//! feq_m = rho * w_m exp(b . v_m) / Z(b), which FACTORISES over the tensor lattice,
//! so each component is an independent, strictly monotone 1D Newton solve.

/// 1D Gauss–Hermite rule for the probabilists' weight, normalised to sum 1.
#[derive(Clone, Debug)]
pub struct GaussHermite {
    pub v: Vec<f64>,
    pub w: Vec<f64>,
    /// Warm-start table of the converged tilt b(u) and db/du on a uniform u grid
    /// (cubic Hermite interpolation); only an initial guess, Newton still converges.
    btab: Vec<(f64, f64)>,
    btab_umax: f64,
    btab_du: f64,
}

/// Orthonormal probabilists' Hermite polynomials h_n = He_n/sqrt(n!) at x:
/// returns (h_{q-1}(x), h_q(x)).
fn hermite_pair(q: usize, x: f64) -> (f64, f64) {
    let mut hm1 = 0.0;
    let mut h = 1.0;
    for n in 0..q {
        let hn1 = (x * h - (n as f64).sqrt() * hm1) / ((n + 1) as f64).sqrt();
        hm1 = h;
        h = hn1;
    }
    (hm1, h)
}

/// Symmetric tridiagonal eigenvalues (implicit QL, Numerical Recipes tqli without vectors).
fn tridiag_eigenvalues(mut d: Vec<f64>, mut e: Vec<f64>) -> Vec<f64> {
    let n = d.len();
    e.push(0.0);
    for l in 0..n {
        let mut iter = 0;
        loop {
            let mut m = l;
            while m + 1 < n {
                let dd = d[m].abs() + d[m + 1].abs();
                if e[m].abs() <= f64::EPSILON * dd {
                    break;
                }
                m += 1;
            }
            if m == l {
                break;
            }
            iter += 1;
            assert!(iter < 200, "tqli: no convergence");
            let mut g = (d[l + 1] - d[l]) / (2.0 * e[l]);
            let mut r = g.hypot(1.0);
            g = d[m] - d[l] + e[l] / (g + r.copysign(g));
            let (mut s, mut c, mut p) = (1.0, 1.0, 0.0);
            let mut i = m;
            let mut underflow = false;
            while i > l {
                i -= 1;
                let f = s * e[i];
                let b = c * e[i];
                r = f.hypot(g);
                e[i + 1] = r;
                if r == 0.0 {
                    d[i + 1] -= p;
                    e[m] = 0.0;
                    underflow = true;
                    break;
                }
                s = f / r;
                c = g / r;
                g = d[i + 1] - p;
                r = (d[i] - g) * s + 2.0 * c * b;
                p = s * r;
                d[i + 1] = g + p;
                g = c * r - b;
            }
            if underflow {
                continue;
            }
            d[l] -= p;
            e[l] = g;
            e[m] = 0.0;
        }
    }
    d.sort_by(|a, b| a.partial_cmp(b).unwrap());
    d
}

impl GaussHermite {
    pub fn new(q: usize) -> Self {
        assert!(q >= 2);
        // Golub–Welsch: Jacobi matrix of monic He_n has zero diagonal, off-diagonal sqrt(n).
        let d = vec![0.0; q];
        let e: Vec<f64> = (1..q).map(|n| (n as f64).sqrt()).collect();
        let mut v = tridiag_eigenvalues(d, e);
        // Newton polish on h_q (h_q' = sqrt(q) h_{q-1}); weights w = 1/(q h_{q-1}^2).
        let mut w = vec![0.0; q];
        for (x, wi) in v.iter_mut().zip(w.iter_mut()) {
            for _ in 0..6 {
                let (hm1, hq) = hermite_pair(q, *x);
                let dx = hq / ((q as f64).sqrt() * hm1);
                *x -= dx;
                if dx.abs() < 1e-16 * x.abs().max(1.0) {
                    break;
                }
            }
            let (hm1, _) = hermite_pair(q, *x);
            *wi = 1.0 / (q as f64 * hm1 * hm1);
        }
        // Enforce exact reflection symmetry and unit mass.
        for i in 0..q / 2 {
            let j = q - 1 - i;
            let a = 0.5 * (v[j] - v[i]);
            v[i] = -a;
            v[j] = a;
            let b = 0.5 * (w[i] + w[j]);
            w[i] = b;
            w[j] = b;
        }
        if q % 2 == 1 {
            v[q / 2] = 0.0;
        }
        let s: f64 = w.iter().sum();
        w.iter_mut().for_each(|x| *x /= s);
        let mut gh = GaussHermite { v, w, btab: vec![], btab_umax: 0.0, btab_du: 1e-3 };
        let umax = (0.35 * gh.v[q - 1]).min(2.5);
        let nt = (2.0 * umax / gh.btab_du).round() as usize;
        let mut e = vec![0.0; q];
        let tab: Vec<(f64, f64)> = (0..=nt)
            .map(|i| {
                let u = -umax + i as f64 * gh.btab_du;
                let r = entropic_newton_1d(&gh, u, &mut e);
                let (_, var) = tilt_1d(&gh, r.b, &mut e);
                (r.b, 1.0 / var)
            })
            .collect();
        gh.btab = tab;
        gh.btab_umax = umax;
        gh
    }

    /// Initial guess for the tilt b(u).
    #[inline]
    fn b_guess(&self, u: f64) -> f64 {
        if self.btab.is_empty() || u.abs() >= self.btab_umax {
            return u;
        }
        let x = (u + self.btab_umax) / self.btab_du;
        let i = (x.floor() as usize).min(self.btab.len() - 2);
        let t = x - i as f64;
        let (b0, d0) = self.btab[i];
        let (b1, d1) = self.btab[i + 1];
        let h = self.btab_du;
        let (t2, t3) = (t * t, t * t * t);
        (2.0 * t3 - 3.0 * t2 + 1.0) * b0 + (t3 - 2.0 * t2 + t) * h * d0 + (-2.0 * t3 + 3.0 * t2) * b1 + (t3 - t2) * h * d1
    }
}

/// Outcome of the 1D entropic Newton solve.
#[derive(Clone, Copy, Debug)]
pub struct Newton1D {
    pub b: f64,
    pub iters: usize,
    /// |sum v e / sum e - u| after convergence.
    pub residual: f64,
}

/// Fill e_j = w_j exp(b v_j)/Z(b) (sum 1) and return (mean, variance) of v under e.
/// Nodes are reflection-symmetric (v_{q-1-j} = -v_j), so one exponential serves each pair.
#[inline]
pub fn tilt_1d(gh: &GaussHermite, b: f64, e: &mut [f64]) -> (f64, f64) {
    let q = gh.v.len();
    let shift = b.abs() * gh.v[q - 1]; // max_j b v_j: keeps exponents <= 0
    let e2s = (-2.0 * shift).exp();
    let mut z = 0.0;
    for j in q / 2..q {
        let x = (b * gh.v[j] - shift).exp(); // exp(b v_j - s)
        let y = if x > 0.0 { e2s / x } else { (-b * gh.v[j] - shift).exp() }; // exp(-b v_j - s)
        e[j] = gh.w[j] * x;
        e[q - 1 - j] = gh.w[j] * y;
        z += e[j] + e[q - 1 - j];
    }
    if q % 2 == 1 {
        e[q / 2] = gh.w[q / 2] * (-shift).exp();
        z += e[q / 2];
    }
    let mut m1 = 0.0;
    let mut m2 = 0.0;
    for (ej, &vj) in e.iter_mut().zip(&gh.v) {
        *ej /= z;
        m1 += *ej * vj;
        m2 += *ej * vj * vj;
    }
    (m1, m2 - m1 * m1)
}

/// Solve  sum_j w_j v_j exp(b v_j) / sum_j w_j exp(b v_j) = u  for b (Newton; the map is
/// strictly increasing with derivative = variance > 0). `e` receives the tilted weights.
///
/// Once the Newton step d is below 1e-8 the last evaluation is updated to first order,
/// e_j <- e_j (1 - d (v_j - m)), instead of re-evaluating the exponentials. This keeps
/// sum e = 1 and sum e v = u EXACTLY (to roundoff) and departs from the exact entropic
/// tilt only at O(d^2) <= 1e-16.
pub fn entropic_newton_1d(gh: &GaussHermite, u: f64, e: &mut [f64]) -> Newton1D {
    let vmax = gh.v[gh.v.len() - 1];
    assert!(u.abs() < vmax, "velocity {u} outside the lattice span {vmax}");
    let mut b = gh.b_guess(u);
    let mut iters = 0;
    loop {
        let (m, var) = tilt_1d(gh, b, e);
        iters += 1;
        let d = (m - u) / var;
        if d.abs() <= 1e-8 || iters >= 60 {
            let mut m_new = 0.0;
            for (ej, &vj) in e.iter_mut().zip(&gh.v) {
                *ej *= 1.0 - d * (vj - m);
                m_new += *ej * vj;
            }
            return Newton1D { b: b - d, iters, residual: (m_new - u).abs() };
        }
        b -= d.clamp(-1.0, 1.0);
    }
}

/// Tensor lattice: node m = i*q + j has velocity (v_i, v_j) and weight w_i w_j.
#[derive(Clone, Debug)]
pub struct Lattice {
    pub q: usize,
    pub gh: GaussHermite,
    pub vx: Vec<f64>,
    pub vy: Vec<f64>,
    pub w: Vec<f64>,
}

impl Lattice {
    pub fn new(q: usize) -> Self {
        let gh = GaussHermite::new(q);
        let mut vx = Vec::with_capacity(q * q);
        let mut vy = Vec::with_capacity(q * q);
        let mut w = Vec::with_capacity(q * q);
        for i in 0..q {
            for j in 0..q {
                vx.push(gh.v[i]);
                vy.push(gh.v[j]);
                w.push(gh.w[i] * gh.w[j]);
            }
        }
        Lattice { q, gh, vx, vy, w }
    }

    pub fn nq2(&self) -> usize {
        self.q * self.q
    }

    /// (rho, jx, jy) of one point's distribution.
    #[inline]
    pub fn moments(&self, f: &[f64]) -> (f64, f64, f64) {
        let q = self.q;
        let (mut rho, mut jx, mut jy) = (0.0, 0.0, 0.0);
        for i in 0..q {
            let row = &f[i * q..(i + 1) * q];
            let mut s = 0.0;
            let mut sy = 0.0;
            for (fj, &vj) in row.iter().zip(&self.gh.v) {
                s += fj;
                sy += fj * vj;
            }
            rho += s;
            jx += s * self.gh.v[i];
            jy += sy;
        }
        (rho, jx, jy)
    }

    /// Entropic equilibrium factors for velocity (ux, uy): ex, ey (each sums to 1).
    #[inline]
    pub fn equilibrium_factors(&self, ux: f64, uy: f64, ex: &mut [f64], ey: &mut [f64]) -> (Newton1D, Newton1D) {
        (entropic_newton_1d(&self.gh, ux, ex), entropic_newton_1d(&self.gh, uy, ey))
    }

    /// Full equilibrium rho * ex_i * ey_j into `out`.
    pub fn equilibrium(&self, rho: f64, ux: f64, uy: f64, out: &mut [f64]) -> (Newton1D, Newton1D) {
        let q = self.q;
        let mut ex = vec![0.0; q];
        let mut ey = vec![0.0; q];
        let r = self.equilibrium_factors(ux, uy, &mut ex, &mut ey);
        for i in 0..q {
            for j in 0..q {
                out[i * q + j] = rho * ex[i] * ey[j];
            }
        }
        r
    }

    /// Discrete H = sum f ln(f/w) over positive entries (negative entries are
    /// reported separately by the caller).
    pub fn h_function(&self, f: &[f64]) -> f64 {
        f.iter()
            .zip(&self.w)
            .filter(|(fm, _)| **fm > 0.0)
            .map(|(fm, wm)| fm * (fm / wm).ln())
            .sum()
    }
}

/// Scratch for the per-point collision operator.
pub struct PointScratch {
    /// set by `collide_force_point` when the velocity left the lattice span and was clamped
    pub clamped: bool,
    pub ex0: Vec<f64>,
    pub ey0: Vec<f64>,
    pub ex1: Vec<f64>,
    pub ey1: Vec<f64>,
}

impl PointScratch {
    pub fn new(q: usize) -> Self {
        PointScratch { clamped: false, ex0: vec![0.0; q], ey0: vec![0.0; q], ex1: vec![0.0; q], ey1: vec![0.0; q] }
    }
}

/// Exact BGK relaxation over a sub-step with decay factor `a = exp(-h/tau)`, combined with
/// the exact-difference force (velocity increment `du`):
///
///   f <- a (f - feq(rho,u)) + feq(rho, u + du).
///
/// This equals BOTH "collide then force" and "force then collide" (the collision leaves
/// rho,u unchanged and the forcing shifts u exactly), so the half-steps of a Strang
/// sequence can be merged. Returns (rho, u) before the update.
#[inline]
pub fn collide_force_point(lat: &Lattice, f: &mut [f64], a: f64, du: [f64; 2], s: &mut PointScratch) -> (f64, f64, f64) {
    collide_force_point_with(lat, f, |_| a, du, false, s)
}

/// As `collide_force_point`, with the relaxation factor a function of the local density. A
/// physical gas has collision time tau ~ 1/rho (viscosity mu = p tau independent of density),
/// i.e. a(rho) = exp(-s rho / (tau_ref rho_ref)); constant tau makes mu ~ rho and nu constant.
/// rho is a collision invariant, so the relaxation is still exact over the sub-step.
#[inline]
pub fn collide_force_point_with(lat: &Lattice, f: &mut [f64], a_of_rho: impl Fn(f64) -> f64, du: [f64; 2], du_per_volume: bool, s: &mut PointScratch) -> (f64, f64, f64) {
    let q = lat.q;
    let (rho, jx, jy) = lat.moments(f);
    let a = a_of_rho(rho);
    // du_per_volume: the prescribed field is a force per unit volume at rho_ref = 1, so the
    // velocity increment is du / rho; otherwise it is an acceleration (force per unit mass).
    let du = if du_per_volume { [du[0] / rho, du[1] / rho] } else { du };
    let lim = 0.95 * lat.gh.v[q - 1];
    let ux = jx / rho;
    let uy = jy / rho;
    // Outside the lattice span no entropic equilibrium exists: clamp and report (callers
    // must treat any clamp as the end of the valid run).
    let clamped = ux.abs() >= lim || uy.abs() >= lim || (ux + du[0]).abs() >= lim || (uy + du[1]).abs() >= lim;
    let cl = |x: f64| x.clamp(-lim, lim);
    lat.equilibrium_factors(cl(ux), cl(uy), &mut s.ex0, &mut s.ey0);
    let forced = du[0] != 0.0 || du[1] != 0.0;
    if forced {
        lat.equilibrium_factors(cl(ux + du[0]), cl(uy + du[1]), &mut s.ex1, &mut s.ey1);
    }
    s.clamped = clamped;
    for i in 0..q {
        let row = &mut f[i * q..(i + 1) * q];
        let e0 = rho * s.ex0[i];
        if forced {
            let e1 = rho * s.ex1[i];
            for j in 0..q {
                row[j] = a * (row[j] - e0 * s.ey0[j]) + e1 * s.ey1[j];
            }
        } else {
            for j in 0..q {
                let eq = e0 * s.ey0[j];
                row[j] = eq + a * (row[j] - eq);
            }
        }
    }
    (rho, ux, uy)
}
