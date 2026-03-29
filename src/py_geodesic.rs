use geors::geodesic::{self, Geodesic};
use pyo3::prelude::*;

/// Register low-level geodesic functions.
pub fn register(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(inverse, m)?)?;
    m.add_function(wrap_pyfunction!(direct, m)?)?;
    m.add_function(wrap_pyfunction!(wgs84_a, m)?)?;
    m.add_function(wrap_pyfunction!(wgs84_f, m)?)?;
    Ok(())
}

/// Full inverse geodesic problem on WGS84.
/// Returns dict with lat1, lon1, lat2, lon2, s12, azi1, azi2, a12, m12, M12, M21, S12.
#[pyfunction]
fn inverse(py: Python, lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> PyResult<PyObject> {
    let g = geodesic::wgs84();
    let r = g.inverse_full(lat1, lon1, lat2, lon2);
    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("lat1", r.lat1)?;
    dict.set_item("lon1", r.lon1)?;
    dict.set_item("lat2", r.lat2)?;
    dict.set_item("lon2", r.lon2)?;
    dict.set_item("s12", r.s12)?;
    dict.set_item("azi1", r.azi1)?;
    dict.set_item("azi2", r.azi2)?;
    dict.set_item("a12", r.a12)?;
    dict.set_item("m12", r.m12)?;
    dict.set_item("M12", r.m_12)?;
    dict.set_item("M21", r.m_21)?;
    dict.set_item("S12", r.s12_area)?;
    Ok(dict.into())
}

/// Full direct geodesic problem on WGS84.
#[pyfunction]
fn direct(
    py: Python,
    lat1: f64,
    lon1: f64,
    azi1: f64,
    s12: f64,
) -> PyResult<PyObject> {
    let g = geodesic::wgs84();
    let r = g.direct(lat1, lon1, azi1, s12);
    let dict = pyo3::types::PyDict::new(py);
    dict.set_item("lat1", r.lat1)?;
    dict.set_item("lon1", r.lon1)?;
    dict.set_item("lat2", r.lat2)?;
    dict.set_item("lon2", r.lon2)?;
    dict.set_item("s12", r.s12)?;
    dict.set_item("azi1", r.azi1)?;
    dict.set_item("azi2", r.azi2)?;
    dict.set_item("a12", r.a12)?;
    Ok(dict.into())
}

/// WGS84 equatorial radius in meters.
#[pyfunction]
fn wgs84_a() -> f64 {
    geors::WGS84_A
}

/// WGS84 flattening.
#[pyfunction]
fn wgs84_f() -> f64 {
    geors::WGS84_F
}
