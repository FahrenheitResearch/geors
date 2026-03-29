//! WGS84 ellipsoid constants and unit conversions.

/// WGS84 equatorial radius in meters.
pub const WGS84_A: f64 = 6_378_137.0;

/// WGS84 flattening.
pub const WGS84_F: f64 = 1.0 / 298.257_223_563;

/// Mean earth radius in km (for great-circle).
pub const EARTH_RADIUS_KM: f64 = 6_371.0088;

// Unit conversion constants
pub const KM_PER_MILE: f64 = 1.609344;
pub const KM_PER_NM: f64 = 1.852;
pub const M_PER_FT: f64 = 0.3048;

/// Convert meters to kilometers.
#[inline(always)]
pub fn m_to_km(m: f64) -> f64 {
    m / 1000.0
}

/// Convert kilometers to meters.
#[inline(always)]
pub fn km_to_m(km: f64) -> f64 {
    km * 1000.0
}

/// Convert kilometers to miles.
#[inline(always)]
pub fn km_to_mi(km: f64) -> f64 {
    km / KM_PER_MILE
}

/// Convert miles to kilometers.
#[inline(always)]
pub fn mi_to_km(mi: f64) -> f64 {
    mi * KM_PER_MILE
}

/// Convert kilometers to nautical miles.
#[inline(always)]
pub fn km_to_nm(km: f64) -> f64 {
    km / KM_PER_NM
}

/// Convert nautical miles to kilometers.
#[inline(always)]
pub fn nm_to_km(nm: f64) -> f64 {
    nm * KM_PER_NM
}

/// Convert meters to feet.
#[inline(always)]
pub fn m_to_ft(m: f64) -> f64 {
    m / M_PER_FT
}

/// Convert feet to meters.
#[inline(always)]
pub fn ft_to_m(ft: f64) -> f64 {
    ft * M_PER_FT
}

/// Convert degrees to radians.
#[inline(always)]
pub fn deg_to_rad(d: f64) -> f64 {
    d.to_radians()
}

/// Convert radians to degrees.
#[inline(always)]
pub fn rad_to_deg(r: f64) -> f64 {
    r.to_degrees()
}

/// Convert degrees, arcminutes, arcseconds to decimal degrees.
#[inline]
pub fn dms_to_deg(degrees: f64, arcminutes: f64, arcseconds: f64) -> f64 {
    degrees + arcminutes / 60.0 + arcseconds / 3600.0
}

/// Convert decimal degrees to (degrees, arcminutes, arcseconds).
#[inline]
pub fn deg_to_dms(dd: f64) -> (f64, f64, f64) {
    let d = dd.trunc();
    let rem = (dd - d).abs() * 60.0;
    let m = rem.trunc();
    let s = (rem - m) * 60.0;
    (d, m, s)
}
