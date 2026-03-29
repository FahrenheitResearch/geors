use geors::{self as geo};
use numpy::{PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use rayon::prelude::*;

/// Register distance functions into the module.
pub fn register(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(geodesic_distance, m)?)?;
    m.add_function(wrap_pyfunction!(geodesic_destination, m)?)?;
    m.add_function(wrap_pyfunction!(great_circle_distance, m)?)?;
    m.add_function(wrap_pyfunction!(great_circle_destination, m)?)?;
    m.add_function(wrap_pyfunction!(geodesic_inverse, m)?)?;
    m.add_function(wrap_pyfunction!(geodesic_distance_batch, m)?)?;
    m.add_function(wrap_pyfunction!(great_circle_distance_batch, m)?)?;
    Ok(())
}

/// Geodesic (ellipsoidal) distance between two points. Returns meters.
#[pyfunction]
fn geodesic_distance(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    let g = geo::geodesic::wgs84();
    g.inverse(lat1, lon1, lat2, lon2).s12
}

/// Geodesic destination given start, azimuth (degrees), and distance (meters).
/// Returns (lat2, lon2).
#[pyfunction]
fn geodesic_destination(lat1: f64, lon1: f64, bearing: f64, distance: f64) -> (f64, f64) {
    let g = geo::geodesic::wgs84();
    let r = g.direct(lat1, lon1, bearing, distance);
    (r.lat2, r.lon2)
}

/// Full inverse geodesic result. Returns dict with s12, azi1, azi2, a12, etc.
#[pyfunction]
fn geodesic_inverse(py: Python, lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> PyResult<PyObject> {
    let g = geo::geodesic::wgs84();
    let r = g.inverse(lat1, lon1, lat2, lon2);
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

/// Great-circle (spherical) distance. Returns meters.
#[pyfunction]
fn great_circle_distance(lat1: f64, lon1: f64, lat2: f64, lon2: f64) -> f64 {
    geo::great_circle_distance(lat1, lon1, lat2, lon2)
}

/// Great-circle destination. Returns (lat2, lon2).
#[pyfunction]
fn great_circle_destination(
    lat1: f64,
    lon1: f64,
    bearing: f64,
    distance: f64,
) -> (f64, f64) {
    geo::great_circle_destination(lat1, lon1, bearing, distance)
}

/// Batch geodesic distance: arrays of (lat1, lon1, lat2, lon2) → array of distances (meters).
/// Uses rayon for parallel computation.
#[pyfunction]
fn geodesic_distance_batch<'py>(
    py: Python<'py>,
    lat1: PyReadonlyArray1<'py, f64>,
    lon1: PyReadonlyArray1<'py, f64>,
    lat2: PyReadonlyArray1<'py, f64>,
    lon2: PyReadonlyArray1<'py, f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let lat1 = lat1.as_slice()?;
    let lon1 = lon1.as_slice()?;
    let lat2 = lat2.as_slice()?;
    let lon2 = lon2.as_slice()?;
    let n = lat1.len();

    let g = geo::geodesic::wgs84();
    let result: Vec<f64> = (0..n)
        .into_par_iter()
        .map(|i| g.inverse(lat1[i], lon1[i], lat2[i], lon2[i]).s12)
        .collect();

    Ok(PyArray1::from_vec(py, result))
}

/// Batch great-circle distance: arrays → array of distances (meters).
#[pyfunction]
fn great_circle_distance_batch<'py>(
    py: Python<'py>,
    lat1: PyReadonlyArray1<'py, f64>,
    lon1: PyReadonlyArray1<'py, f64>,
    lat2: PyReadonlyArray1<'py, f64>,
    lon2: PyReadonlyArray1<'py, f64>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let lat1 = lat1.as_slice()?;
    let lon1 = lon1.as_slice()?;
    let lat2 = lat2.as_slice()?;
    let lon2 = lon2.as_slice()?;
    let n = lat1.len();

    let result: Vec<f64> = (0..n)
        .into_par_iter()
        .map(|i| geo::great_circle_distance(lat1[i], lon1[i], lat2[i], lon2[i]))
        .collect();

    Ok(PyArray1::from_vec(py, result))
}
