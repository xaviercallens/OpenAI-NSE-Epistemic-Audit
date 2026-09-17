//! Least-squares helpers and the matrix-pencil rate estimator.

use nalgebra::{DMatrix, DVector};
use num_complex::Complex64 as C;

/// Two-sided 95% Student t critical values, df = 1..30.
pub fn t_crit_95(df: usize) -> f64 {
    const T: [f64; 30] = [
        12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
        2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042,
    ];
    if df == 0 { f64::NAN } else if df <= 30 { T[df - 1] } else { 1.96 }
}

/// OLS of y on columns of x (with the design passed in full). Returns (beta, se, dof).
pub fn ols(x: &DMatrix<f64>, y: &DVector<f64>) -> (DVector<f64>, DVector<f64>, usize) {
    let n = x.nrows();
    let p = x.ncols();
    let xtx = x.transpose() * x;
    let inv = xtx.clone().try_inverse().expect("singular design");
    let beta = &inv * x.transpose() * y;
    let r = y - x * &beta;
    let dof = n - p;
    let s2 = if dof > 0 { r.norm_squared() / dof as f64 } else { f64::NAN };
    let se = DVector::from_iterator(p, (0..p).map(|i| (s2 * inv[(i, i)]).sqrt()));
    (beta, se, dof)
}

/// Matrix-pencil (Hua–Sarkar) estimate of the exponents s_i in y_n = sum c_i exp(s_i n dt).
/// Returns (s_i, |c_i|) for the retained modes, most slowly decaying first.
pub fn matrix_pencil(y: &[f64], dt: f64, rel_tol: f64, max_modes: usize) -> Vec<(C, f64)> {
    let m = y.len();
    let l = m / 3;
    let rows = m - l;
    let ymat = DMatrix::from_fn(rows, l + 1, |i, j| y[i + j]);
    let svd = ymat.svd(false, true);
    let sv = &svd.singular_values;
    let k = sv.iter().take_while(|&&s| s > rel_tol * sv[0]).count().min(max_modes).max(1);
    let vt = svd.v_t.unwrap(); // (min) x (l+1)
    let v = vt.rows(0, k).transpose(); // (l+1) x k
    let v1 = v.rows(0, l).into_owned();
    let v2 = v.rows(1, l).into_owned();
    let p = v1.clone().pseudo_inverse(1e-14).unwrap() * v2;
    let z = p.complex_eigenvalues();
    // amplitudes by complex least squares
    let a = DMatrix::from_fn(m, k, |n, i| z[i].powu(n as u32));
    let yc = DVector::from_iterator(m, y.iter().map(|&x| C::new(x, 0.0)));
    let c = a.svd(true, true).solve(&yc, 1e-14).unwrap();
    let mut out: Vec<(C, f64)> = (0..k).map(|i| (z[i].ln() / dt, c[i].norm())).collect();
    out.sort_by(|a, b| b.0.re.partial_cmp(&a.0.re).unwrap());
    out
}
