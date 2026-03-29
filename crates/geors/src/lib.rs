//! Pure Rust geodesic calculations.
//!
//! Drop-in computational replacement for geographiclib + geopy.distance.
//! Implements Karney's algorithm for the geodesic problem on an ellipsoid,
//! great-circle distance (Haversine), and geodesic polygon area.

pub mod constants;
pub mod capability;
pub mod geodesic;
pub mod geodesic_line;
pub mod great_circle;
pub mod polygon_area;

pub use constants::*;
pub use geodesic::Geodesic;
pub use geodesic_line::GeodesicLine;
pub use great_circle::{great_circle_distance, great_circle_destination};
pub use polygon_area::PolygonArea;
