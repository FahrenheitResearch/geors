//! Geodesic capability bit masks.
//! Direct port of geographiclib's geodesiccapability.py.

pub const CAP_NONE: u32 = 0;
pub const CAP_C1: u32 = 1;
pub const CAP_C1P: u32 = 1 << 1;
pub const CAP_C2: u32 = 1 << 2;
pub const CAP_C3: u32 = 1 << 3;
pub const CAP_C4: u32 = 1 << 4;
pub const CAP_ALL: u32 = 0x1F;
pub const CAP_MASK: u32 = CAP_ALL;
pub const OUT_ALL: u32 = 0x7F80;
pub const OUT_MASK: u32 = 0xFF80;

pub const EMPTY: u32 = 0;
pub const LATITUDE: u32 = (1 << 7) | CAP_NONE;
pub const LONGITUDE: u32 = (1 << 8) | CAP_C3;
pub const AZIMUTH: u32 = (1 << 9) | CAP_NONE;
pub const DISTANCE: u32 = (1 << 10) | CAP_C1;
pub const STANDARD: u32 = LATITUDE | LONGITUDE | AZIMUTH | DISTANCE;
pub const DISTANCE_IN: u32 = (1 << 11) | CAP_C1 | CAP_C1P;
pub const REDUCEDLENGTH: u32 = (1 << 12) | CAP_C1 | CAP_C2;
pub const GEODESICSCALE: u32 = (1 << 13) | CAP_C1 | CAP_C2;
pub const AREA: u32 = (1 << 14) | CAP_C4;
pub const LONG_UNROLL: u32 = 1 << 15;
pub const ALL: u32 = OUT_ALL | CAP_ALL;
