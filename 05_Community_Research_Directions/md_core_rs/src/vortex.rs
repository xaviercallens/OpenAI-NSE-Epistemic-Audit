//! Forced-core target: time-reversed Lamb-Oseen column, l^2 = nu (T_blow - t), Gamma = 2 pi nu Re / PEAK.
use std::f64::consts::PI;
pub const PEAK: f64 = 0.6381726863389515;

#[derive(Clone, Debug)]
pub struct Target {
    pub nu: f64,
    pub re: f64,
    pub l_start: f64,
    pub gamma: f64,
    pub t_blow: f64,
    pub collapsing: bool,
}
impl Target {
    pub fn new(nu: f64, re: f64, l_start: f64, collapsing: bool) -> Self {
        Target { nu, re, l_start, gamma: 2.0 * PI * nu * re / PEAK, t_blow: l_start * l_start / nu, collapsing }
    }
    /// target core size: collapsing l^2 = l_s^2 - nu t ; free decay reference l^2 = l_s^2 + 4 nu t
    pub fn ell(&self, t: f64) -> f64 {
        if self.collapsing { (self.l_start * self.l_start - self.nu * t).max(1e-12).sqrt() } else { (self.l_start * self.l_start + 4.0 * self.nu * t).sqrt() }
    }
    pub fn u_theta(&self, r: f64, l: f64) -> f64 {
        if r < 1e-9 { return 0.0; }
        self.gamma / (2.0 * PI * r) * (-(-(r / l) * (r / l)).exp_m1())
    }
    /// per-unit-mass azimuthal force: residual of incompressible constant-nu NSE, f = 2.5 nu r omega / l^2
    pub fn force_theta(&self, r: f64, t: f64) -> f64 {
        let l = self.ell(t);
        let om = self.gamma / (PI * l * l) * (-(r / l) * (r / l)).exp();
        2.5 * self.nu * r * om / (l * l)
    }
}
#[inline]
pub fn smoothstep(x: f64) -> f64 {
    let x = x.clamp(0.0, 1.0);
    x * x * (3.0 - 2.0 * x)
}
