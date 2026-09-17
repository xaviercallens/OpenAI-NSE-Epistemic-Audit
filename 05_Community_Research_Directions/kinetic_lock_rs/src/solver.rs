//! Discrete-velocity BGK on the periodic square [0, 2 pi)^2.
//!
//! Storage is velocity-first: f[m * N^2 + p], m = i*Q + j, p = iy*N + ix, so streaming
//! (one velocity at a time) is contiguous; the pointwise collision works on one grid row
//! at a time, gathered into a cache-sized block.
//! One Strang step of length h:   A(h/2, g(t)) · S(h) · A(h/2, g(t+h)),
//! where S is exact Fourier streaming (separable shift by v h per axis) and
//! A(s, g) is exact BGK relaxation exp(-s/tau) with the exact-difference force
//! u -> u + g s (see `collide_force_point`). Consecutive half-steps may be merged.

use crate::lattice::{collide_force_point_with, Lattice, PointScratch};
use num_complex::Complex64 as C;
use rayon::prelude::*;
use rustfft::{Fft, FftPlanner};
use std::sync::Arc;

#[derive(Clone, Copy)]
struct SendPtr(*mut f64);
unsafe impl Send for SendPtr {}
unsafe impl Sync for SendPtr {}
impl SendPtr {
    #[inline]
    fn get(&self) -> *mut f64 {
        self.0
    }
}

pub struct Kinetic {
    pub lat: Lattice,
    pub n: usize,
    pub tau: f64,
    /// true: tau_local = tau / rho (physical gas, mu independent of density; rho_ref = 1).
    pub tau_inv_rho: bool,
    /// true: forcing is a force per unit volume (increment du / rho) instead of per unit mass.
    pub force_per_volume: bool,
    pub f: Vec<f64>,
    fwd: Arc<dyn Fft<f64>>,
    inv: Arc<dyn Fft<f64>>,
    kgrid: Vec<f64>,
    phase_dt: f64,
    phase: Vec<Vec<C>>,
}

/// Global sums from one diagnostics pass.
#[derive(Clone, Copy, Debug, Default)]
pub struct Sums {
    pub mass: f64,
    pub px: f64,
    pub py: f64,
    pub negative_mass: f64,
    pub min_f: f64,
    pub h: f64,
    pub noneq_l1: f64,
    pub abs_l1: f64,
    pub max_drho: f64,
    pub max_speed: f64,
}

impl Sums {
    fn empty() -> Self {
        Sums { min_f: f64::INFINITY, ..Default::default() }
    }
    fn merge(a: Sums, b: Sums) -> Sums {
        Sums {
            mass: a.mass + b.mass,
            px: a.px + b.px,
            py: a.py + b.py,
            negative_mass: a.negative_mass + b.negative_mass,
            min_f: a.min_f.min(b.min_f),
            h: a.h + b.h,
            noneq_l1: a.noneq_l1 + b.noneq_l1,
            abs_l1: a.abs_l1 + b.abs_l1,
            max_drho: a.max_drho.max(b.max_drho),
            max_speed: a.max_speed.max(b.max_speed),
        }
    }
}

impl Kinetic {
    pub fn new(q: usize, n: usize, tau: f64) -> Self {
        assert!(n % 2 == 0);
        let lat = Lattice::new(q);
        let mut planner = FftPlanner::new();
        let fwd = planner.plan_fft_forward(n);
        let inv = planner.plan_fft_inverse(n);
        let kgrid = (0..n).map(|i| if i < n / 2 { i as f64 } else { i as f64 - n as f64 }).collect();
        let f = vec![0.0; n * n * q * q];
        Kinetic { lat, n, tau, tau_inv_rho: false, force_per_volume: false, f, fwd, inv, kgrid, phase_dt: f64::NAN, phase: vec![] }
    }

    pub fn npts(&self) -> usize {
        self.n * self.n
    }

    /// Apply `op(iy, block)` to every grid row in parallel, where block[ix * Q^2 + m] is a
    /// point-first copy of the row; if `write` the block is scattered back.
    fn for_rows<T: Send, Init: Fn() -> S + Sync + Send, S>(
        &self,
        ptr: SendPtr,
        write: bool,
        init: Init,
        op: impl Fn(&mut S, usize, &mut [f64]) -> T + Sync,
        identity: impl Fn() -> T + Sync + Send,
        reduce: impl Fn(T, T) -> T + Sync + Send,
    ) -> T {
        let n = self.n;
        let nq2 = self.lat.nq2();
        let npts = n * n;
        (0..n)
            .into_par_iter()
            .map_init(
                || (vec![0.0; n * nq2], init()),
                |(block, st), iy| {
                    let base = ptr.get();
                    // SAFETY: rows are disjoint index sets; each task reads/writes only row iy.
                    for m in 0..nq2 {
                        let src = unsafe { std::slice::from_raw_parts(base.add(m * npts + iy * n), n) };
                        for ix in 0..n {
                            block[ix * nq2 + m] = src[ix];
                        }
                    }
                    let r = op(st, iy, block);
                    if write {
                        for m in 0..nq2 {
                            let dst = unsafe { std::slice::from_raw_parts_mut(base.add(m * npts + iy * n), n) };
                            for ix in 0..n {
                                dst[ix] = block[ix * nq2 + m];
                            }
                        }
                    }
                    r
                },
            )
            .reduce(identity, reduce)
    }

    /// Set f to the entropic equilibrium of the given moment fields.
    pub fn set_equilibrium(&mut self, rho: &[f64], ux: &[f64], uy: &[f64]) {
        let n = self.n;
        let nq2 = self.lat.nq2();
        let lat = self.lat.clone();
        let ptr = SendPtr(self.f.as_mut_ptr());
        self.for_rows(
            ptr,
            true,
            || (),
            |_, iy, block| {
                for ix in 0..n {
                    let p = iy * n + ix;
                    lat.equilibrium(rho[p], ux[p], uy[p], &mut block[ix * nq2..(ix + 1) * nq2]);
                }
            },
            || (),
            |_, _| (),
        );
    }

    fn ensure_phase(&mut self, h: f64) {
        if self.phase_dt == h {
            return;
        }
        let n = self.n;
        self.phase = self
            .lat
            .gh
            .v
            .iter()
            .map(|&v| {
                (0..n)
                    .map(|ix| {
                        let a = self.kgrid[ix] * v * h;
                        // Nyquist: keep the real (cosine) part so real fields stay real.
                        if ix == n / 2 { C::new(a.cos(), 0.0) } else { C::from_polar(1.0, -a) }
                    })
                    .collect()
            })
            .collect();
        self.phase_dt = h;
    }

    /// Exact spectral free streaming f(x) <- f(x - v h), separable in x and y.
    pub fn stream(&mut self, h: f64) {
        self.ensure_phase(h);
        let n = self.n;
        let q = self.lat.q;
        let npts = n * n;
        let (fwd, inv, phase) = (&self.fwd, &self.inv, &self.phase);
        let scratch_len = fwd.get_inplace_scratch_len().max(inv.get_inplace_scratch_len());
        let norm = 1.0 / n as f64;
        self.f.par_chunks_mut(npts).enumerate().for_each_init(
            || (vec![C::new(0.0, 0.0); n], vec![C::new(0.0, 0.0); scratch_len]),
            |(buf, scr), (m, field)| {
                let phx = &phase[m / q];
                let phy = &phase[m % q];
                for row in field.chunks_mut(n) {
                    for (b, &x) in buf.iter_mut().zip(row.iter()) {
                        *b = C::new(x, 0.0);
                    }
                    fwd.process_with_scratch(buf, scr);
                    for (c, ph) in buf.iter_mut().zip(phx) {
                        *c *= ph;
                    }
                    inv.process_with_scratch(buf, scr);
                    for (x, b) in row.iter_mut().zip(buf.iter()) {
                        *x = b.re * norm;
                    }
                }
                for ix in 0..n {
                    for iy in 0..n {
                        buf[iy] = C::new(field[iy * n + ix], 0.0);
                    }
                    fwd.process_with_scratch(buf, scr);
                    for (c, ph) in buf.iter_mut().zip(phy) {
                        *c *= ph;
                    }
                    inv.process_with_scratch(buf, scr);
                    for iy in 0..n {
                        field[iy * n + ix] = buf[iy].re * norm;
                    }
                }
            },
        );
    }

    /// A(s, g): exact relaxation over `s_collide` with force velocity increment g * s_force.
    /// Returns the momentum added (sum over points of rho * du) and the number of points whose
    /// velocity had to be clamped to the lattice span (non-zero = invalid state).
    pub fn collide_force(&mut self, s_collide: f64, force: Option<(&[f64], &[f64])>, s_force: f64) -> ((f64, f64), usize) {
        let rate = s_collide / self.tau;
        let inv_rho = self.tau_inv_rho;
        let per_vol = self.force_per_volume;
        let n = self.n;
        let nq2 = self.lat.nq2();
        let q = self.lat.q;
        let lat = self.lat.clone();
        let ptr = SendPtr(self.f.as_mut_ptr());
        self.for_rows(
            ptr,
            true,
            || PointScratch::new(q),
            |s, iy, block| {
                let mut imp = ((0.0, 0.0), 0usize);
                for ix in 0..n {
                    let p = iy * n + ix;
                    let du = match force {
                        Some((gx, gy)) => [gx[p] * s_force, gy[p] * s_force],
                        None => [0.0, 0.0],
                    };
                    let (rho, _, _) = collide_force_point_with(&lat, &mut block[ix * nq2..(ix + 1) * nq2], |rho| if inv_rho { (-rate * rho).exp() } else { (-rate).exp() }, du, per_vol, s);
                    let w = if per_vol { 1.0 } else { rho };
                    imp.0 .0 += w * du[0];
                    imp.0 .1 += w * du[1];
                    imp.1 += s.clamped as usize;
                }
                imp
            },
            || ((0.0, 0.0), 0usize),
            |x, y| ((x.0 .0 + y.0 .0, x.0 .1 + y.0 .1), x.1 + y.1),
        )
    }

    /// Moment fields (rho, ux, uy).
    pub fn fields(&self) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
        let n = self.n;
        let nq2 = self.lat.nq2();
        let lat = self.lat.clone();
        // read-only pass: the pointer is never written through when write = false
        let ptr = SendPtr(self.f.as_ptr() as *mut f64);
        let mut rows: Vec<(usize, Vec<(f64, f64, f64)>)> = self.for_rows(
            ptr,
            false,
            || (),
            |_, iy, block| vec![(iy, (0..n).map(|ix| lat.moments(&block[ix * nq2..(ix + 1) * nq2])).collect())],
            Vec::new,
            |mut a, mut b| {
                a.append(&mut b);
                a
            },
        );
        rows.sort_by_key(|r| r.0);
        let m: Vec<(f64, f64, f64)> = rows.into_iter().flat_map(|r| r.1).collect();
        (
            m.iter().map(|x| x.0).collect(),
            m.iter().map(|x| x.1 / x.0).collect(),
            m.iter().map(|x| x.2 / x.0).collect(),
        )
    }

    /// Mass, momentum, negativity, H, non-equilibrium L1 fraction, max |rho-1|, max speed.
    pub fn sums(&self) -> Sums {
        let n = self.n;
        let nq2 = self.lat.nq2();
        let lat = self.lat.clone();
        let ptr = SendPtr(self.f.as_ptr() as *mut f64);
        self.for_rows(
            ptr,
            false,
            || vec![0.0; nq2],
            |eq, _iy, block| {
                let mut acc = Sums::empty();
                for ix in 0..n {
                    let fp = &block[ix * nq2..(ix + 1) * nq2];
                    let (rho, jx, jy) = lat.moments(fp);
                    let (ux, uy) = (jx / rho, jy / rho);
                    lat.equilibrium(rho, ux, uy, eq);
                    let mut s = Sums {
                        mass: rho,
                        px: jx,
                        py: jy,
                        min_f: f64::INFINITY,
                        h: lat.h_function(fp),
                        max_drho: (rho - 1.0).abs(),
                        max_speed: (ux * ux + uy * uy).sqrt(),
                        ..Default::default()
                    };
                    for (fm, em) in fp.iter().zip(eq.iter()) {
                        if *fm < 0.0 {
                            s.negative_mass -= fm;
                        }
                        s.min_f = s.min_f.min(*fm);
                        s.noneq_l1 += (fm - em).abs();
                        s.abs_l1 += fm.abs();
                    }
                    acc = Sums::merge(acc, s);
                }
                acc
            },
            Sums::empty,
            Sums::merge,
        )
    }
}
