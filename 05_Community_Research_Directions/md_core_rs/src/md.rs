//! Core MD engine: cell-sorted structure-of-arrays, truncated-shifted LJ, velocity Verlet.
use crate::rng::normal2;
use rayon::prelude::*;

pub const RC: f64 = 2.5;

pub struct System {
    pub n: usize,
    pub l: f64,
    pub lz: f64,
    pub x: Vec<f64>,
    pub y: Vec<f64>,
    pub z: Vec<f64>,
    pub vx: Vec<f64>,
    pub vy: Vec<f64>,
    pub vz: Vec<f64>,
    pub fx: Vec<f64>,
    pub fy: Vec<f64>,
    pub fz: Vec<f64>,
    ncx: usize,
    ncz: usize,
    cell_start: Vec<usize>,
    scratch: Vec<f64>,
    cell_of: Vec<u32>,
    order: Vec<u32>,
    pub pe: f64,
    pub virial: f64,
    /// per-particle virial tensor shares (1/2 sum_j F_ij,a r_ij,b) when `stress` is on
    pub stress: bool,
    pub wxx: Vec<f64>,
    pub wxy: Vec<f64>,
    pub wyy: Vec<f64>,
    pub wzz: Vec<f64>,
    e_shift: f64,
    // Verlet list (rebuilt when any particle has moved more than skin/2); positions are wrapped only at rebuilds
    pub skin: f64,
    nl_off: Vec<usize>,
    nl_j: Vec<u32>,
    nl_s: Vec<u8>,
    x0: Vec<f64>,
    y0: Vec<f64>,
    z0: Vec<f64>,
    pub rebuilds: usize,
    pub t_force: f64,
    pub t_rebuild: f64,
    pub t_other: f64,
}

impl System {
    /// Simple-cubic start at the requested density (actual density = n / volume is reported by caller).
    pub fn new_lattice(rho: f64, l: f64, lz: f64, temp: f64, seed: u64) -> Self {
        // lattice dimensions chosen so that N / V matches the requested density to better than 1%
        let a = rho.powf(-1.0 / 3.0);
        let nz = (lz / a).round().max(1.0) as usize;
        let nx = ((rho * l * l * lz / nz as f64).sqrt()).round().max(1.0) as usize;
        let n = nx * nx * nz;
        let (ax, az) = (l / nx as f64, lz / nz as f64);
        let mut s = System {
            n, l, lz,
            x: vec![0.0; n], y: vec![0.0; n], z: vec![0.0; n],
            vx: vec![0.0; n], vy: vec![0.0; n], vz: vec![0.0; n],
            fx: vec![0.0; n], fy: vec![0.0; n], fz: vec![0.0; n],
            ncx: ((l / (RC + 1.0)).floor() as usize).max(3), ncz: ((lz / (RC + 1.0)).floor() as usize).max(2),
            cell_start: vec![], scratch: vec![0.0; n], cell_of: vec![0; n], order: vec![0; n],
            pe: 0.0, virial: 0.0, stress: false, wxx: vec![], wxy: vec![], wyy: vec![], wzz: vec![],
            e_shift: 4.0 * (RC.powi(-12) - RC.powi(-6)),
            skin: 0.5, nl_off: vec![], nl_j: vec![], nl_s: vec![], x0: vec![0.0; n], y0: vec![0.0; n], z0: vec![0.0; n], rebuilds: 0, t_force: 0.0, t_rebuild: 0.0, t_other: 0.0,
        };
        assert!(l / s.ncx as f64 >= RC + 1.0 && lz >= 2.0 * (RC + 1.0), "box too small for r_c + skin (skin <= 1)");
        let mut p = 0;
        for iz in 0..nz {
            for iy in 0..nx {
                for ix in 0..nx {
                    s.x[p] = (ix as f64 + 0.5) * ax;
                    s.y[p] = (iy as f64 + 0.5) * ax;
                    s.z[p] = (iz as f64 + 0.5) * az;
                    let (g1, g2) = normal2(seed, 0, p as u64, 0);
                    let (g3, _) = normal2(seed, 0, p as u64, 2);
                    let sd = temp.sqrt();
                    s.vx[p] = sd * g1;
                    s.vy[p] = sd * g2;
                    s.vz[p] = sd * g3;
                    p += 1;
                }
            }
        }
        s.zero_momentum();
        s.rebuild();
        s.compute_forces();
        s
    }

    pub fn zero_momentum(&mut self) {
        let n = self.n as f64;
        for v in [&mut self.vx, &mut self.vy, &mut self.vz] {
            let m = v.iter().sum::<f64>() / n;
            v.iter_mut().for_each(|a| *a -= m);
        }
    }

    pub fn density(&self) -> f64 {
        self.n as f64 / (self.l * self.l * self.lz)
    }

    fn permute(buf: &mut Vec<f64>, scratch: &mut Vec<f64>, order: &[u32]) {
        {
            let src: &Vec<f64> = buf;
            scratch.par_iter_mut().zip(order.par_iter()).with_min_len(8192).for_each(|(d, &o)| *d = src[o as usize]);
        }
        std::mem::swap(buf, scratch);
    }

    /// Counting sort of all particle arrays by cell index.
    pub fn sort_cells(&mut self) {
        let (ncx, ncz) = (self.ncx, self.ncz);
        let (cx, cz) = (self.l / ncx as f64, self.lz / ncz as f64);
        let ncell = ncx * ncx * ncz;
        let mut count = vec![0usize; ncell + 1];
        {
            let (x, y, z) = (&self.x, &self.y, &self.z);
            self.cell_of.par_iter_mut().enumerate().with_min_len(8192).for_each(|(i, c)| {
                let ix = ((x[i] / cx) as usize).min(ncx - 1);
                let iy = ((y[i] / cx) as usize).min(ncx - 1);
                let iz = ((z[i] / cz) as usize).min(ncz - 1);
                *c = ((iz * ncx + iy) * ncx + ix) as u32;
            });
        }
        for i in 0..self.n {
            count[self.cell_of[i] as usize + 1] += 1;
        }
        for c in 0..ncell {
            count[c + 1] += count[c];
        }
        let mut fill = count.clone();
        for i in 0..self.n {
            let c = self.cell_of[i] as usize;
            self.order[fill[c]] = i as u32;
            fill[c] += 1;
        }
        let order = std::mem::take(&mut self.order);
        let mut scratch = std::mem::take(&mut self.scratch);
        Self::permute(&mut self.x, &mut scratch, &order);
        Self::permute(&mut self.y, &mut scratch, &order);
        Self::permute(&mut self.z, &mut scratch, &order);
        Self::permute(&mut self.vx, &mut scratch, &order);
        Self::permute(&mut self.vy, &mut scratch, &order);
        Self::permute(&mut self.vz, &mut scratch, &order);
        Self::permute(&mut self.fx, &mut scratch, &order);
        Self::permute(&mut self.fy, &mut scratch, &order);
        Self::permute(&mut self.fz, &mut scratch, &order);
        self.order = order;
        self.scratch = scratch;
        self.cell_start = count;
    }

    /// Wrap positions, cell-sort, and build the Verlet list (full list: every pair stored twice).
    pub fn rebuild(&mut self) {
        let (l, lz) = (self.l, self.lz);
        self.x.par_iter_mut().for_each(|a| *a = a.rem_euclid(l));
        self.y.par_iter_mut().for_each(|a| *a = a.rem_euclid(l));
        self.z.par_iter_mut().for_each(|a| *a = a.rem_euclid(lz));
        self.sort_cells();
        let (ncx, ncz) = (self.ncx as isize, self.ncz as isize);
        let rl2 = (RC + self.skin) * (RC + self.skin);
        let (x, y, z) = (&self.x, &self.y, &self.z);
        let cs = &self.cell_start;
        let ncell = (ncx * ncx * ncz) as usize;
        // z may have only 2 cells: visit each distinct neighbour cell once, choosing the nearer image per pair
        let zspan: Vec<isize> = if ncz >= 3 { vec![-1, 0, 1] } else { vec![0, 1] };
        let per_cell: Vec<(Vec<u32>, Vec<u32>, Vec<u8>)> = (0..ncell)
            .into_par_iter()
            .with_min_len(32)
            .map(|c| {
                let (i0, i1) = (cs[c], cs[c + 1]);
                let (mut cnt, mut js, mut ss) = (Vec::with_capacity(i1 - i0), Vec::new(), Vec::new());
                let ci = c as isize;
                let (ix, iy, iz) = (ci % ncx, (ci / ncx) % ncx, ci / (ncx * ncx));
                for i in i0..i1 {
                    let (xi, yi, zi) = (x[i], y[i], z[i]);
                    let mut k = 0u32;
                    for &dz in zspan.iter() {
                        for dy in -1..=1isize {
                            for dx in -1..=1isize {
                                let (jx, jy, jz) = ((ix + dx).rem_euclid(ncx), (iy + dy).rem_euclid(ncx), (iz + dz).rem_euclid(ncz));
                                let cj = ((jz * ncx + jy) * ncx + jx) as usize;
                                for j in cs[cj]..cs[cj + 1] {
                                    if j == i {
                                        continue;
                                    }
                                    let (mut ddx, mut ddy, mut ddz) = (x[j] - xi, y[j] - yi, z[j] - zi);
                                    let (mut sx, mut sy, mut sz) = (1u8, 1u8, 1u8);
                                    if ddx > 0.5 * l { ddx -= l; sx = 0; } else if ddx < -0.5 * l { ddx += l; sx = 2; }
                                    if ddy > 0.5 * l { ddy -= l; sy = 0; } else if ddy < -0.5 * l { ddy += l; sy = 2; }
                                    if ddz > 0.5 * lz { ddz -= lz; sz = 0; } else if ddz < -0.5 * lz { ddz += lz; sz = 2; }
                                    if ddx * ddx + ddy * ddy + ddz * ddz < rl2 {
                                        js.push(j as u32);
                                        ss.push(sx + 3 * sy + 9 * sz);
                                        k += 1;
                                    }
                                }
                            }
                        }
                    }
                    cnt.push(k);
                }
                (cnt, js, ss)
            })
            .collect();
        self.nl_off.clear();
        self.nl_j.clear();
        self.nl_s.clear();
        self.nl_off.push(0);
        for (cnt, js, ss) in per_cell.iter() {
            for &k in cnt {
                let last = *self.nl_off.last().unwrap();
                self.nl_off.push(last + k as usize);
            }
            self.nl_j.extend_from_slice(js);
            self.nl_s.extend_from_slice(ss);
        }
        self.x0.copy_from_slice(&self.x);
        self.y0.copy_from_slice(&self.y);
        self.z0.copy_from_slice(&self.z);
        self.rebuilds += 1;
    }

    fn needs_rebuild(&self) -> bool {
        let lim = 0.25 * self.skin * self.skin;
        let (x, y, z, x0, y0, z0) = (&self.x, &self.y, &self.z, &self.x0, &self.y0, &self.z0);
        (0..self.n).into_par_iter().with_min_len(8192).any(|i| {
            let (a, b, c) = (x[i] - x0[i], y[i] - y0[i], z[i] - z0[i]);
            a * a + b * b + c * c > lim
        })
    }

    /// Forces, potential energy and virial (sum over pairs of r.f) from the Verlet list.
    pub fn compute_forces(&mut self) {
        let (l, lz) = (self.l, self.lz);
        let rc2 = RC * RC;
        let e_shift = self.e_shift;
        let pos: Vec<[f64; 3]> = (0..self.n).into_par_iter().with_min_len(8192).map(|i| [self.x[i], self.y[i], self.z[i]]).collect();
        let pos = &pos;
        let (off, nj, ns) = (&self.nl_off, &self.nl_j, &self.nl_s);
        let mut sh = [[0.0f64; 3]; 27];
        for s in 0..27 {
            sh[s] = [(s % 3) as f64 * l - l, ((s / 3) % 3) as f64 * l - l, (s / 9) as f64 * lz - lz];
        }
        let stress = self.stress;
        // always sized to n: the arrays are zipped with the force arrays below (an empty one would truncate the loop)
        if self.wxx.len() != self.n {
            self.wxx = vec![0.0; self.n];
            self.wxy = vec![0.0; self.n];
            self.wyy = vec![0.0; self.n];
            self.wzz = vec![0.0; self.n];
        }
        let (pe, vir) = (self.fx.par_iter_mut(), self.fy.par_iter_mut(), self.fz.par_iter_mut(),
                         self.wxx.par_iter_mut(), self.wxy.par_iter_mut(), self.wyy.par_iter_mut(), self.wzz.par_iter_mut())
            .into_par_iter()
            .enumerate()
            .with_min_len(1024)
            .map(|(i, (fx, fy, fz, wxx, wxy, wyy, wzz))| {
                let [xi, yi, zi] = pos[i];
                let (mut ax, mut ay, mut az, mut pe, mut vir) = (0.0, 0.0, 0.0, 0.0, 0.0);
                let (mut sxx, mut sxy, mut syy, mut szz) = (0.0, 0.0, 0.0, 0.0);
                for k in off[i]..off[i + 1] {
                    let pj = pos[nj[k] as usize];
                    let s = sh[ns[k] as usize];
                    let dx = pj[0] + s[0] - xi;
                    let dy = pj[1] + s[1] - yi;
                    let dz = pj[2] + s[2] - zi;
                    let r2 = dx * dx + dy * dy + dz * dz;
                    if r2 < rc2 {
                        let inv2 = 1.0 / r2;
                        let inv6 = inv2 * inv2 * inv2;
                        let ff = 24.0 * inv2 * inv6 * (2.0 * inv6 - 1.0);
                        ax -= ff * dx;
                        ay -= ff * dy;
                        az -= ff * dz;
                        pe += 4.0 * inv6 * (inv6 - 1.0) - e_shift;
                        vir += ff * r2;
                        if stress {
                            sxx += ff * dx * dx;
                            sxy += ff * dx * dy;
                            syy += ff * dy * dy;
                            szz += ff * dz * dz;
                        }
                    }
                }
                *fx = ax;
                *fy = ay;
                *fz = az;
                if stress {
                    *wxx = 0.5 * sxx;
                    *wxy = 0.5 * sxy;
                    *wyy = 0.5 * syy;
                    *wzz = 0.5 * szz;
                }
                (0.5 * pe, 0.5 * vir)
            })
            .reduce(|| (0.0, 0.0), |a, b| (a.0 + b.0, a.1 + b.1));
        self.pe = pe;
        self.virial = vir;
    }

    pub fn kinetic(&self) -> f64 {
        0.5 * (0..self.n).into_par_iter().map(|i| self.vx[i] * self.vx[i] + self.vy[i] * self.vy[i] + self.vz[i] * self.vz[i]).sum::<f64>()
    }
    pub fn temperature(&self) -> f64 {
        2.0 * self.kinetic() / (3.0 * self.n as f64)
    }
    /// virial pressure p = rho T + W / (3 V), W = sum_pairs r.f
    pub fn pressure(&self) -> f64 {
        let v = self.l * self.l * self.lz;
        self.density() * self.temperature() + self.virial / (3.0 * v)
    }
    pub fn momentum(&self) -> (f64, f64, f64) {
        (self.vx.iter().sum(), self.vy.iter().sum(), self.vz.iter().sum())
    }

    /// One velocity-Verlet step. `ext(x, y, t) -> (ax, ay)` is a per-unit-mass body force (may be None);
    /// `thermo(i, x, y, vx, vy, vz) -> (vx, vy, vz)` is applied after the step (Langevin buffer or global).
    pub fn step<E, T>(&mut self, dt: f64, t: f64, ext: &E, thermo: &T)
    where
        E: Fn(f64, f64, f64) -> (f64, f64) + Sync,
        T: Fn(usize, f64, f64, f64, f64, f64) -> (f64, f64, f64) + Sync,
    {
        let h = 0.5 * dt;
        {
            let (fx, fy, fz) = (&self.fx, &self.fy, &self.fz);
            (self.x.par_iter_mut(), self.y.par_iter_mut(), self.z.par_iter_mut(), self.vx.par_iter_mut(), self.vy.par_iter_mut(), self.vz.par_iter_mut())
                .into_par_iter()
                .enumerate()
                .with_min_len(4096)
                .for_each(|(i, (x, y, z, vx, vy, vz))| {
                    let (ex, ey) = ext(*x, *y, t);
                    *vx += h * (fx[i] + ex);
                    *vy += h * (fy[i] + ey);
                    *vz += h * fz[i];
                    *x += dt * *vx;
                    *y += dt * *vy;
                    *z += dt * *vz;
                });
        }
        let c0 = std::time::Instant::now();
        if self.needs_rebuild() {
            self.rebuild();
        }
        let c1 = std::time::Instant::now();
        self.compute_forces();
        let c2 = std::time::Instant::now();
        self.t_rebuild += (c1 - c0).as_secs_f64();
        self.t_force += (c2 - c1).as_secs_f64();
        let t1 = t + dt;
        let (fx, fy, fz) = (&self.fx, &self.fy, &self.fz);
        let (x, y) = (&self.x, &self.y);
        (self.vx.par_iter_mut(), self.vy.par_iter_mut(), self.vz.par_iter_mut())
            .into_par_iter()
            .enumerate()
            .with_min_len(4096)
            .for_each(|(i, (vx, vy, vz))| {
                let (ex, ey) = ext(x[i], y[i], t1);
                *vx += h * (fx[i] + ex);
                *vy += h * (fy[i] + ey);
                *vz += h * fz[i];
                let (a, b, c) = thermo(i, x[i], y[i], *vx, *vy, *vz);
                *vx = a;
                *vy = b;
                *vz = c;
            });
    }
}

/// Exact Ornstein-Uhlenbeck update of the peculiar velocity (v - u) at rate g and temperature temp.
#[inline]
pub fn langevin(seed: u64, step: u64, i: usize, g: f64, dt: f64, temp: f64, u: (f64, f64), v: (f64, f64, f64)) -> (f64, f64, f64) {
    if g <= 0.0 {
        return v;
    }
    let a = (-g * dt).exp();
    let s = (temp * (1.0 - a * a)).sqrt();
    let (n1, n2) = normal2(seed, step, i as u64, 0);
    let (n3, _) = normal2(seed, step, i as u64, 2);
    (u.0 + a * (v.0 - u.0) + s * n1, u.1 + a * (v.1 - u.1) + s * n2, a * v.2 + s * n3)
}
