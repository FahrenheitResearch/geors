//! Mathematical utilities for geodesic calculations.
//!
//! Direct port of geographiclib's geomath.py — error-free sums,
//! high-precision trig in degrees, polynomial evaluation, etc.

use std::f64::consts::PI;

/// Square a number.
#[inline(always)]
pub fn sq(x: f64) -> f64 {
    x * x
}

/// Real cube root.
#[inline]
pub fn cbrt(x: f64) -> f64 {
    x.cbrt()
}

/// Normalize a 2-vector so its magnitude is 1.
/// Returns (x/r, y/r).
#[inline]
pub fn norm(x: f64, y: f64) -> (f64, f64) {
    let r = x.hypot(y);
    (x / r, y / r)
}

/// Error-free transformation of a sum.
/// Returns (s, t) where s = round(u + v) and t = u + v - s.
/// Note that t can be the same as one of the first two arguments.
#[inline]
pub fn two_sum(u: f64, v: f64) -> (f64, f64) {
    let s = u + v;
    let up = s - v;
    let vpp = s - up;
    let up = u - up;
    let vpp = v - vpp;
    let t = up + vpp;
    (s, t)
}

/// Evaluate a polynomial using Horner's method.
/// Evaluates sum(p[s+i] * x^(N-i), i=0..N).
#[inline]
pub fn polyval(n: usize, p: &[f64], s: usize, x: f64) -> f64 {
    let mut y = if n > 0 { p[s] } else { 0.0 };
    for i in 1..=n {
        y = y * x + p[s + i];
    }
    y
}

/// Round angle x (in degrees) to avoid issues with underflow.
/// The gap between representable values is approximately 2^-57.
#[inline]
pub fn ang_round(x: f64) -> f64 {
    const Z: f64 = 1.0 / 16.0;
    let y = x.abs();
    if y < Z {
        // underflow guard
        let y = Z - y;
        let y = Z - y; // restore
        if y == 0.0 { 0.0 } else { x.signum() * y }
    } else {
        x
    }
}

/// Remainder of x / y in the range [-y/2, y/2].
#[inline]
pub fn remainder(x: f64, y: f64) -> f64 {
    // Rust's f64::rem_euclid doesn't do what we want; use IEEE remainder
    let r = x % y;
    if r.abs() > y / 2.0 {
        r - y.copysign(r)
    } else {
        r
    }
}

/// Reduce angle to [-180, 180].
#[inline]
pub fn ang_normalize(x: f64) -> f64 {
    let y = remainder(x, 360.0);
    if y.abs() == 180.0 {
        180.0_f64.copysign(x)
    } else {
        y
    }
}

/// Replace out-of-range latitudes with NaN.
#[inline]
pub fn lat_fix(x: f64) -> f64 {
    if x.abs() > 90.0 {
        f64::NAN
    } else {
        x
    }
}

/// Compute the exact difference y - x, reduced to [-180, 180].
/// Returns (d, e) where d + e = y - x exactly.
#[inline]
pub fn ang_diff(x: f64, y: f64) -> (f64, f64) {
    let (d, t) = two_sum(ang_normalize(-x), ang_normalize(y));
    let d = ang_normalize(d);
    let (d, t) = two_sum(
        if d == 180.0 && t > 0.0 { -180.0 } else { d },
        t,
    );
    (d, t)
}

/// Sine and cosine of angle in degrees. Exact for multiples of 90.
pub fn sincosd(x: f64) -> (f64, f64) {
    let mut r = x % 360.0;
    let mut q = if r.is_nan() { 0 } else { (r / 90.0).round() as i64 };
    r -= 90.0 * q as f64;
    let r = r.to_radians();
    let (mut sinr, mut cosr) = r.sin_cos();
    // Normalize quadrant
    q = ((q % 4) + 4) % 4;
    match q {
        0 => {} // no change
        1 => {
            let t = sinr;
            sinr = cosr;
            cosr = -t;
        }
        2 => {
            sinr = -sinr;
            cosr = -cosr;
        }
        3 => {
            let t = sinr;
            sinr = -cosr;
            cosr = t;
        }
        _ => unreachable!(),
    }
    // Clean up -0.0
    if sinr == 0.0 {
        sinr = 0.0_f64.copysign(x);
    }
    (sinr, cosr)
}

/// Sine and cosine of (x + t) in degrees, where x is in [-180, 180].
pub fn sincosde(x: f64, t: f64) -> (f64, f64) {
    let (sx, cx) = sincosd(x);
    let (st, ct) = sincosd(t);
    // sin(x+t) = sin(x)*cos(t) + cos(x)*sin(t)
    // cos(x+t) = cos(x)*cos(t) - sin(x)*sin(t)
    let sinxt = sx * ct + cx * st;
    let cosxt = cx * ct - sx * st;
    (sinxt, cosxt)
}

/// atan2(y, x) in degrees. Returns result in [-180, 180].
pub fn atan2d(y: f64, x: f64) -> f64 {
    let mut q = 0i32;
    let mut y = y;
    let mut x = x;
    // Rotate to first quadrant for precision
    if y.abs() > x.abs() {
        std::mem::swap(&mut x, &mut y);
        q = 2;
    }
    if x < 0.0 {
        x = -x;
        q += 1;
    }
    let mut ang = y.atan2(x).to_degrees();
    match q {
        0 => {}
        1 => ang = if y >= 0.0 { 180.0 - ang } else { -180.0 - ang },
        2 => ang = 90.0 - ang,
        3 => ang = -90.0 + ang,
        _ => unreachable!(),
    }
    ang
}

/// High-precision accumulator using Shewchuk's algorithm.
/// Maintains exact running sum as (s, t) pair.
#[derive(Clone, Debug)]
pub struct Accumulator {
    s: f64,
    t: f64,
}

impl Accumulator {
    pub fn new(y: f64) -> Self {
        Accumulator { s: y, t: 0.0 }
    }

    pub fn set(&mut self, y: f64) {
        self.s = y;
        self.t = 0.0;
    }

    pub fn set_from(&mut self, other: &Accumulator) {
        self.s = other.s;
        self.t = other.t;
    }

    /// Add a value with exact error tracking.
    pub fn add(&mut self, y: f64) {
        // Shewchuk: exact addition of [_s, _t, u]
        let (u, v) = two_sum(y, self.t);
        let (s, t) = two_sum(u, self.s);
        // Normalize so that s + t approximates the exact sum
        let t = if s == 0.0 { s } else { t + v };
        self.s = s + t;
        self.t = t - (self.s - s);
    }

    /// Return the accumulated sum, optionally adding y first.
    pub fn sum(&self, y: f64) -> f64 {
        if y == 0.0 {
            self.s
        } else {
            let mut tmp = self.clone();
            tmp.add(y);
            tmp.s
        }
    }

    pub fn negate(&mut self) {
        self.s = -self.s;
        self.t = -self.t;
    }

    pub fn remainder(&mut self, y: f64) {
        self.s = self.s % y;
        self.add(0.0); // renormalize
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sincosd_exact_90() {
        let (s, c) = sincosd(90.0);
        assert_eq!(s, 1.0);
        assert!(c.abs() < 1e-15);
    }

    #[test]
    fn test_sincosd_exact_180() {
        let (s, c) = sincosd(180.0);
        assert!(s.abs() < 1e-15);
        assert_eq!(c, -1.0);
    }

    #[test]
    fn test_sincosd_exact_270() {
        let (s, c) = sincosd(270.0);
        assert_eq!(s, -1.0);
        assert!(c.abs() < 1e-15);
    }

    #[test]
    fn test_two_sum() {
        let (s, t) = two_sum(1.0, 1e-16);
        assert_eq!(s + t, 1.0 + 1e-16);
    }

    #[test]
    fn test_ang_normalize() {
        assert!((ang_normalize(370.0) - 10.0).abs() < 1e-10);
        assert!((ang_normalize(-190.0) - 170.0).abs() < 1e-10);
    }

    #[test]
    fn test_polyval() {
        // 2x^2 + 3x + 1 at x=2 = 15
        let p = [2.0, 3.0, 1.0];
        assert_eq!(polyval(2, &p, 0, 2.0), 15.0);
    }

    #[test]
    fn test_accumulator() {
        let mut acc = Accumulator::new(0.0);
        for _ in 0..1000 {
            acc.add(1e-16);
        }
        assert!((acc.sum(0.0) - 1000e-16).abs() < 1e-28);
    }

    #[test]
    fn test_atan2d() {
        assert!((atan2d(1.0, 0.0) - 90.0).abs() < 1e-10);
        assert!((atan2d(0.0, 1.0)).abs() < 1e-10);
        assert!((atan2d(-1.0, 0.0) - (-90.0)).abs() < 1e-10);
    }
}
