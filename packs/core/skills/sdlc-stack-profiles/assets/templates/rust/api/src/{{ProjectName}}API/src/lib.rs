//! Library crate for the {{ProjectName}} API: the layered modules the
//! binary composes. Layers depend in one direction — web -> service ->
//! model — and `main.rs` is the composition root that wires them.

pub mod model;
pub mod service;
pub mod web;
