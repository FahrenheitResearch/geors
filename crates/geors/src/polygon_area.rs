//! Geodesic polygon area computation.
//!
//! Wraps geographiclib_rs::PolygonArea.

use crate::geodesic::Geodesic;
use geographiclib_rs::{PolygonArea as PolyInner, Winding};

/// Compute the perimeter and area of a geodesic polygon.
pub struct PolygonArea<'a> {
    inner: PolyInner<'a>,
    geod: &'a geographiclib_rs::Geodesic,
    num: usize,
    polyline: bool,
    // Store points to allow non-consuming compute
    points: Vec<(f64, f64)>,
    edges: Vec<(f64, f64)>,
}

impl<'a> PolygonArea<'a> {
    /// Create a new polygon area calculator.
    pub fn new(earth: &'a Geodesic, polyline: bool) -> Self {
        let geod = earth.inner();
        let winding = Winding::CounterClockwise;
        let inner = PolyInner::new(geod, winding);
        PolygonArea {
            inner,
            geod,
            num: 0,
            polyline,
            points: Vec::new(),
            edges: Vec::new(),
        }
    }

    /// Add a vertex to the polygon.
    pub fn add_point(&mut self, lat: f64, lon: f64) {
        self.inner.add_point(lat, lon);
        self.points.push((lat, lon));
        self.num += 1;
    }

    /// Add an edge specified by azimuth and distance.
    pub fn add_edge(&mut self, azi: f64, s: f64) {
        self.inner.add_edge(azi, s);
        self.edges.push((azi, s));
        self.num += 1;
    }

    /// Compute the polygon properties.
    /// Returns `(num_vertices, perimeter_meters, area_m2)`.
    pub fn compute(&self, _reverse: bool, sign: bool) -> (usize, f64, f64) {
        // PolygonArea::compute consumes self, so rebuild
        let mut pa = PolyInner::new(self.geod, Winding::CounterClockwise);
        for &(lat, lon) in &self.points {
            pa.add_point(lat, lon);
        }
        for &(azi, s) in &self.edges {
            pa.add_edge(azi, s);
        }
        let (perim, area, n) = pa.compute(sign);
        (n, perim, area)
    }

    /// Number of points added.
    pub fn num(&self) -> usize {
        self.num
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::geodesic::wgs84;

    #[test]
    fn test_polygon_triangle() {
        let g = wgs84();
        let mut poly = PolygonArea::new(g, false);
        poly.add_point(0.0, 0.0);
        poly.add_point(1.0, 0.0);
        poly.add_point(0.5, 1.0);
        let (n, perim, area) = poly.compute(false, true);
        assert_eq!(n, 3);
        assert!(perim > 0.0);
        assert!(area.abs() > 0.0, "area = {}", area);
    }
}
