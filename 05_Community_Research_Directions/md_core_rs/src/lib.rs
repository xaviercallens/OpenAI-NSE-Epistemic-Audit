//! Truncated-shifted Lennard-Jones MD (sigma = eps = m = 1, r_c = 2.5) in a periodic slab L x L x Lz,
//! with a per-unit-mass azimuthal body force (the forced-core target of forced_core.py), a Langevin
//! buffer outside R_b, and radial-bin diagnostics. No external RNG crate: counter-based splitmix64.
pub mod md;
pub mod rng;
pub mod vortex;
