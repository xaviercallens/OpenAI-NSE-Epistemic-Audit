use num_complex::Complex64 as C;
use rustfft::FftPlanner;
use std::time::Instant;
fn main() {
    for n in [128usize, 150, 160, 216, 256, 320, 480, 500, 512] {
        let mut p = FftPlanner::new();
        let f = p.plan_fft_forward(n);
        let mut buf: Vec<C> = (0..n).map(|i| C::new((i as f64).sin(), 0.0)).collect();
        let mut scr = vec![C::new(0.0, 0.0); f.get_inplace_scratch_len()];
        let reps = 200000 / n * 10;
        let t = Instant::now();
        for _ in 0..reps { f.process_with_scratch(&mut buf, &mut scr); }
        let dt = t.elapsed().as_secs_f64() / reps as f64;
        println!("n={n} {:.2} us/fft  {:.2} ns/(n log2 n)", dt * 1e6, dt * 1e9 / (n as f64 * (n as f64).log2()));
    }
}
