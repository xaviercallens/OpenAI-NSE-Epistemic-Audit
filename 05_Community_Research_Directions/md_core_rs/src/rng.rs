//! Stateless counter-based normal deviates: hash(seed, step, index, stream) -> N(0,1).
#[inline]
pub fn splitmix64(mut z: u64) -> u64 {
    z = z.wrapping_add(0x9E37_79B9_7F4A_7C15);
    z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^ (z >> 31)
}
#[inline]
pub fn uniform(seed: u64, step: u64, idx: u64, stream: u64) -> f64 {
    let h = splitmix64(splitmix64(splitmix64(seed ^ 0xA5A5_5A5A_1234_5678).wrapping_add(step)).wrapping_add(idx.wrapping_mul(8).wrapping_add(stream)));
    ((h >> 11) as f64 + 0.5) / (1u64 << 53) as f64
}
/// Two independent standard normals (Box-Muller) from streams (s, s+1).
#[inline]
pub fn normal2(seed: u64, step: u64, idx: u64, stream: u64) -> (f64, f64) {
    let u1 = uniform(seed, step, idx, stream);
    let u2 = uniform(seed, step, idx, stream + 1);
    let r = (-2.0 * u1.ln()).sqrt();
    let a = 2.0 * std::f64::consts::PI * u2;
    (r * a.cos(), r * a.sin())
}
