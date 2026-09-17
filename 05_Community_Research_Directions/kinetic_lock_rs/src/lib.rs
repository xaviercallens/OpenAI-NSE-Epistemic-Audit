//! kinetic_lock_rs: isothermal 2D-2V discrete-velocity BGK for the kinetic-lock test.
pub mod dispersion;
pub mod forced;
pub mod lattice;
pub mod solver;
pub mod spectral;
pub mod stats;

pub use lattice::{GaussHermite, Lattice};
pub use solver::Kinetic;
