use pyo3::prelude::*;

mod py_distance;
mod py_geodesic;
mod py_units;

/// The native Rust module exposed as geors._geors
#[pymodule]
fn _geors(py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // distance submodule
    let dist = PyModule::new(py, "distance")?;
    py_distance::register(py, &dist)?;
    m.add_submodule(&dist)?;

    // geodesic submodule (low-level)
    let geo = PyModule::new(py, "geodesic")?;
    py_geodesic::register(py, &geo)?;
    m.add_submodule(&geo)?;

    // units submodule
    let units = PyModule::new(py, "units")?;
    py_units::register(py, &units)?;
    m.add_submodule(&units)?;

    Ok(())
}
