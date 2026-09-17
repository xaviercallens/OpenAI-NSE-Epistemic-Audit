//! 2D periodic spectral helpers on [0, L)^2 with L = 2 pi (integer wavenumbers).
//! Transforms are separable (rows then columns) with rustfft; forward is unnormalised,
//! `inverse` divides by N^2. Nyquist modes are zeroed wherever a derivative or a
//! spectrally defined target is built, so every constructed field is real.

use num_complex::Complex64 as C;
use rayon::prelude::*;
use rustfft::{Fft, FftPlanner};
use std::sync::Arc;

pub struct Spectral2D {
    pub n: usize,
    pub fwd: Arc<dyn Fft<f64>>,
    pub inv: Arc<dyn Fft<f64>>,
    /// signed integer wavenumber of index i (Nyquist index carries -n/2)
    pub k: Vec<f64>,
    pub dx: f64,
}

impl Spectral2D {
    pub fn new(n: usize) -> Self {
        assert!(n % 2 == 0);
        let mut planner = FftPlanner::new();
        let fwd = planner.plan_fft_forward(n);
        let inv = planner.plan_fft_inverse(n);
        let k = (0..n).map(|i| if i < n / 2 { i as f64 } else { i as f64 - n as f64 }).collect();
        Spectral2D { n, fwd, inv, k, dx: 2.0 * std::f64::consts::PI / n as f64 }
    }

    #[inline]
    pub fn is_nyquist(&self, ix: usize, iy: usize) -> bool {
        ix == self.n / 2 || iy == self.n / 2
    }

    fn transform(&self, a: &mut [C], plan: &Arc<dyn Fft<f64>>) {
        let n = self.n;
        // rows (x direction)
        a.par_chunks_mut(n).for_each_init(
            || vec![C::new(0.0, 0.0); plan.get_inplace_scratch_len()],
            |scr, row| plan.process_with_scratch(row, scr),
        );
        // columns (y direction)
        let cols: Vec<Vec<C>> = (0..n)
            .into_par_iter()
            .map_init(
                || vec![C::new(0.0, 0.0); plan.get_inplace_scratch_len()],
                |scr, ix| {
                    let mut col: Vec<C> = (0..n).map(|iy| a[iy * n + ix]).collect();
                    plan.process_with_scratch(&mut col, scr);
                    col
                },
            )
            .collect();
        for (ix, col) in cols.into_iter().enumerate() {
            for (iy, c) in col.into_iter().enumerate() {
                a[iy * n + ix] = c;
            }
        }
    }

    pub fn forward(&self, real: &[f64]) -> Vec<C> {
        let mut a: Vec<C> = real.iter().map(|&x| C::new(x, 0.0)).collect();
        self.transform(&mut a, &self.fwd);
        a
    }

    pub fn inverse(&self, spec: &[C]) -> Vec<f64> {
        let mut a = spec.to_vec();
        self.transform(&mut a, &self.inv);
        let s = 1.0 / (self.n * self.n) as f64;
        a.iter().map(|c| c.re * s).collect()
    }

    /// Vorticity spectrum from velocity: w = d_x u_y - d_y u_x.
    pub fn vorticity_hat(&self, ux: &[f64], uy: &[f64]) -> Vec<C> {
        let n = self.n;
        let ax = self.forward(ux);
        let ay = self.forward(uy);
        let mut w = vec![C::new(0.0, 0.0); n * n];
        for iy in 0..n {
            for ix in 0..n {
                if self.is_nyquist(ix, iy) {
                    continue;
                }
                let p = iy * n + ix;
                w[p] = C::new(0.0, self.k[ix]) * ay[p] - C::new(0.0, self.k[iy]) * ax[p];
            }
        }
        w
    }

    /// Velocity spectra (u_x, u_y) of the divergence-free field with vorticity w_hat
    /// (psi_hat = -w_hat/k^2, u = (-d_y psi, d_x psi)); the mean is zero.
    pub fn velocity_from_vorticity_hat(&self, w: &[C]) -> (Vec<C>, Vec<C>) {
        let n = self.n;
        let mut ux = vec![C::new(0.0, 0.0); n * n];
        let mut uy = vec![C::new(0.0, 0.0); n * n];
        for iy in 0..n {
            for ix in 0..n {
                if self.is_nyquist(ix, iy) || (ix == 0 && iy == 0) {
                    continue;
                }
                let p = iy * n + ix;
                let (kx, ky) = (self.k[ix], self.k[iy]);
                let psi = -w[p] / (kx * kx + ky * ky);
                ux[p] = -C::new(0.0, ky) * psi;
                uy[p] = C::new(0.0, kx) * psi;
            }
        }
        (ux, uy)
    }

    /// k_omega = sqrt(sum k^2 |w|^2 / sum |w|^2)  (= sqrt(2)/l for a Gaussian of width l).
    pub fn k_omega(&self, w: &[C]) -> f64 {
        let n = self.n;
        let (mut num, mut den) = (0.0, 0.0);
        for iy in 0..n {
            for ix in 0..n {
                let a = w[iy * n + ix].norm_sqr();
                num += (self.k[ix] * self.k[ix] + self.k[iy] * self.k[iy]) * a;
                den += a;
            }
        }
        if den > 0.0 { (num / den).sqrt() } else { f64::NAN }
    }
}
