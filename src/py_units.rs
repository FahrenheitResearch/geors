use pyo3::prelude::*;
use geors::constants;

/// Register unit conversion functions.
pub fn register(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(km_to_mi, m)?)?;
    m.add_function(wrap_pyfunction!(mi_to_km, m)?)?;
    m.add_function(wrap_pyfunction!(km_to_nm, m)?)?;
    m.add_function(wrap_pyfunction!(nm_to_km, m)?)?;
    m.add_function(wrap_pyfunction!(m_to_ft, m)?)?;
    m.add_function(wrap_pyfunction!(ft_to_m, m)?)?;
    m.add_function(wrap_pyfunction!(m_to_km, m)?)?;
    m.add_function(wrap_pyfunction!(km_to_m, m)?)?;
    m.add_function(wrap_pyfunction!(deg_to_rad, m)?)?;
    m.add_function(wrap_pyfunction!(rad_to_deg, m)?)?;
    m.add_function(wrap_pyfunction!(dms_to_deg, m)?)?;
    m.add_function(wrap_pyfunction!(deg_to_dms, m)?)?;
    Ok(())
}

#[pyfunction]
fn km_to_mi(km: f64) -> f64 { constants::km_to_mi(km) }

#[pyfunction]
fn mi_to_km(mi: f64) -> f64 { constants::mi_to_km(mi) }

#[pyfunction]
fn km_to_nm(km: f64) -> f64 { constants::km_to_nm(km) }

#[pyfunction]
fn nm_to_km(nm: f64) -> f64 { constants::nm_to_km(nm) }

#[pyfunction]
fn m_to_ft(m: f64) -> f64 { constants::m_to_ft(m) }

#[pyfunction]
fn ft_to_m(ft: f64) -> f64 { constants::ft_to_m(ft) }

#[pyfunction]
fn m_to_km(m: f64) -> f64 { constants::m_to_km(m) }

#[pyfunction]
fn km_to_m(km: f64) -> f64 { constants::km_to_m(km) }

#[pyfunction]
fn deg_to_rad(d: f64) -> f64 { constants::deg_to_rad(d) }

#[pyfunction]
fn rad_to_deg(r: f64) -> f64 { constants::rad_to_deg(r) }

#[pyfunction]
fn dms_to_deg(degrees: f64, arcminutes: f64, arcseconds: f64) -> f64 {
    constants::dms_to_deg(degrees, arcminutes, arcseconds)
}

#[pyfunction]
fn deg_to_dms(dd: f64) -> (f64, f64, f64) {
    constants::deg_to_dms(dd)
}
