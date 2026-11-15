//! The `OS/2` table: weight and width classes, style flags, PANOSE, vertical metrics, and the Unicode range and
//! code page bits computed from the character map.

use write_fonts::tables::os2::{Os2, SelectionFlags};
use write_fonts::types::Tag;

use crate::{Built, Family, Style, meta};

/// The Unicode blocks and their `ulUnicodeRange` bits, after the OpenType specification's table.
const UNICODE_RANGES: &[(u8, u32, u32)] = &[
    (0, 0x0000, 0x007F),     // Basic Latin
    (1, 0x0080, 0x00FF),     // Latin-1 Supplement
    (2, 0x0100, 0x017F),     // Latin Extended-A
    (3, 0x0180, 0x024F),     // Latin Extended-B
    (4, 0x0250, 0x02AF),     // IPA Extensions
    (4, 0x1D00, 0x1DBF),     // Phonetic Extensions (and Supplement)
    (5, 0x02B0, 0x02FF),     // Spacing Modifier Letters
    (5, 0xA700, 0xA71F),     // Modifier Tone Letters
    (6, 0x0300, 0x036F),     // Combining Diacritical Marks
    (6, 0x1DC0, 0x1DFF),     // Combining Diacritical Marks Supplement
    (7, 0x0370, 0x03FF),     // Greek and Coptic
    (9, 0x0400, 0x052F),     // Cyrillic (and Supplement)
    (29, 0x1E00, 0x1EFF),    // Latin Extended Additional
    (29, 0x2C60, 0x2C7F),    // Latin Extended-C
    (29, 0xA720, 0xA7FF),    // Latin Extended-D
    (30, 0x1F00, 0x1FFF),    // Greek Extended
    (31, 0x2000, 0x206F),    // General Punctuation
    (31, 0x2E00, 0x2E7F),    // Supplemental Punctuation
    (32, 0x2070, 0x209F),    // Superscripts And Subscripts
    (33, 0x20A0, 0x20CF),    // Currency Symbols
    (34, 0x20D0, 0x20FF),    // Combining Diacritical Marks For Symbols
    (35, 0x2100, 0x214F),    // Letterlike Symbols
    (36, 0x2150, 0x218F),    // Number Forms
    (37, 0x2190, 0x21FF),    // Arrows
    (37, 0x27F0, 0x27FF),    // Supplemental Arrows-A
    (37, 0x2900, 0x297F),    // Supplemental Arrows-B
    (37, 0x2B00, 0x2BFF),    // Miscellaneous Symbols and Arrows
    (38, 0x2200, 0x22FF),    // Mathematical Operators
    (38, 0x27C0, 0x27EF),    // Miscellaneous Mathematical Symbols-A
    (38, 0x2980, 0x29FF),    // Miscellaneous Mathematical Symbols-B
    (38, 0x2A00, 0x2AFF),    // Supplemental Mathematical Operators
    (39, 0x2300, 0x23FF),    // Miscellaneous Technical
    (40, 0x2400, 0x243F),    // Control Pictures
    (41, 0x2440, 0x245F),    // Optical Character Recognition
    (42, 0x2460, 0x24FF),    // Enclosed Alphanumerics
    (43, 0x2500, 0x257F),    // Box Drawing
    (44, 0x2580, 0x259F),    // Block Elements
    (45, 0x25A0, 0x25FF),    // Geometric Shapes
    (46, 0x2600, 0x26FF),    // Miscellaneous Symbols
    (47, 0x2700, 0x27BF),    // Dingbats
    (48, 0x3000, 0x303F),    // CJK Symbols And Punctuation
    (60, 0xE000, 0xF8FF),    // Private Use Area (plane 0)
    (65, 0xFE20, 0xFE2F),    // Combining Half Marks
    (69, 0xFFF0, 0xFFFF),    // Specials
    (82, 0x2800, 0x28FF),    // Braille Patterns
    (89, 0x1D400, 0x1D7FF),  // Mathematical Alphanumeric Symbols
    (90, 0xF0000, 0x10FFFF), // Private Use (planes 15 and 16)
];

/// `ulUnicodeRange` bit 57: the font has characters beyond the Basic Multilingual Plane.
const NON_PLANE_0: u8 = 57;

/// Windows code pages, as (`ulCodePageRange` bit, the characters of the code page's bytes 0x80..=0xFF). A code
/// page's bit is set when the font has every one of these and all of printable ASCII.
const CODE_PAGES: &[(u8, &[u32])] = &[
    // Windows code page 1252: the characters of bytes 0x80..=0xFF (123)
    (
        0,
        &[
            0x20AC, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x017D,
            0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x017E,
            0x0178, 0x00A0, 0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00AA, 0x00AB,
            0x00AC, 0x00AD, 0x00AE, 0x00AF, 0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8,
            0x00B9, 0x00BA, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF, 0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C4, 0x00C5,
            0x00C6, 0x00C7, 0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x00CC, 0x00CD, 0x00CE, 0x00CF, 0x00D0, 0x00D1, 0x00D2,
            0x00D3, 0x00D4, 0x00D5, 0x00D6, 0x00D7, 0x00D8, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x00DD, 0x00DE, 0x00DF,
            0x00E0, 0x00E1, 0x00E2, 0x00E3, 0x00E4, 0x00E5, 0x00E6, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC,
            0x00ED, 0x00EE, 0x00EF, 0x00F0, 0x00F1, 0x00F2, 0x00F3, 0x00F4, 0x00F5, 0x00F6, 0x00F7, 0x00F8, 0x00F9,
            0x00FA, 0x00FB, 0x00FC, 0x00FD, 0x00FE, 0x00FF,
        ],
    ),
    // Windows code page 1250: the characters of bytes 0x80..=0xFF (123)
    (
        1,
        &[
            0x20AC, 0x201A, 0x201E, 0x2026, 0x2020, 0x2021, 0x2030, 0x0160, 0x2039, 0x015A, 0x0164, 0x017D, 0x0179,
            0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x2122, 0x0161, 0x203A, 0x015B, 0x0165, 0x017E,
            0x017A, 0x00A0, 0x02C7, 0x02D8, 0x0141, 0x00A4, 0x0104, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x015E, 0x00AB,
            0x00AC, 0x00AD, 0x00AE, 0x017B, 0x00B0, 0x00B1, 0x02DB, 0x0142, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8,
            0x0105, 0x015F, 0x00BB, 0x013D, 0x02DD, 0x013E, 0x017C, 0x0154, 0x00C1, 0x00C2, 0x0102, 0x00C4, 0x0139,
            0x0106, 0x00C7, 0x010C, 0x00C9, 0x0118, 0x00CB, 0x011A, 0x00CD, 0x00CE, 0x010E, 0x0110, 0x0143, 0x0147,
            0x00D3, 0x00D4, 0x0150, 0x00D6, 0x00D7, 0x0158, 0x016E, 0x00DA, 0x0170, 0x00DC, 0x00DD, 0x0162, 0x00DF,
            0x0155, 0x00E1, 0x00E2, 0x0103, 0x00E4, 0x013A, 0x0107, 0x00E7, 0x010D, 0x00E9, 0x0119, 0x00EB, 0x011B,
            0x00ED, 0x00EE, 0x010F, 0x0111, 0x0144, 0x0148, 0x00F3, 0x00F4, 0x0151, 0x00F6, 0x00F7, 0x0159, 0x016F,
            0x00FA, 0x0171, 0x00FC, 0x00FD, 0x0163, 0x02D9,
        ],
    ),
    // Windows code page 1253: the characters of bytes 0x80..=0xFF (111)
    (
        3,
        &[
            0x20AC, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x2030, 0x2039, 0x2018, 0x2019, 0x201C, 0x201D,
            0x2022, 0x2013, 0x2014, 0x2122, 0x203A, 0x00A0, 0x0385, 0x0386, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7,
            0x00A8, 0x00A9, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x2015, 0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x0384, 0x00B5,
            0x00B6, 0x00B7, 0x0388, 0x0389, 0x038A, 0x00BB, 0x038C, 0x00BD, 0x038E, 0x038F, 0x0390, 0x0391, 0x0392,
            0x0393, 0x0394, 0x0395, 0x0396, 0x0397, 0x0398, 0x0399, 0x039A, 0x039B, 0x039C, 0x039D, 0x039E, 0x039F,
            0x03A0, 0x03A1, 0x03A3, 0x03A4, 0x03A5, 0x03A6, 0x03A7, 0x03A8, 0x03A9, 0x03AA, 0x03AB, 0x03AC, 0x03AD,
            0x03AE, 0x03AF, 0x03B0, 0x03B1, 0x03B2, 0x03B3, 0x03B4, 0x03B5, 0x03B6, 0x03B7, 0x03B8, 0x03B9, 0x03BA,
            0x03BB, 0x03BC, 0x03BD, 0x03BE, 0x03BF, 0x03C0, 0x03C1, 0x03C2, 0x03C3, 0x03C4, 0x03C5, 0x03C6, 0x03C7,
            0x03C8, 0x03C9, 0x03CA, 0x03CB, 0x03CC, 0x03CD, 0x03CE,
        ],
    ),
    // Windows code page 1254: the characters of bytes 0x80..=0xFF (121)
    (
        4,
        &[
            0x20AC, 0x201A, 0x0192, 0x201E, 0x2026, 0x2020, 0x2021, 0x02C6, 0x2030, 0x0160, 0x2039, 0x0152, 0x2018,
            0x2019, 0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x02DC, 0x2122, 0x0161, 0x203A, 0x0153, 0x0178, 0x00A0,
            0x00A1, 0x00A2, 0x00A3, 0x00A4, 0x00A5, 0x00A6, 0x00A7, 0x00A8, 0x00A9, 0x00AA, 0x00AB, 0x00AC, 0x00AD,
            0x00AE, 0x00AF, 0x00B0, 0x00B1, 0x00B2, 0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00B8, 0x00B9, 0x00BA,
            0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00BF, 0x00C0, 0x00C1, 0x00C2, 0x00C3, 0x00C4, 0x00C5, 0x00C6, 0x00C7,
            0x00C8, 0x00C9, 0x00CA, 0x00CB, 0x00CC, 0x00CD, 0x00CE, 0x00CF, 0x011E, 0x00D1, 0x00D2, 0x00D3, 0x00D4,
            0x00D5, 0x00D6, 0x00D7, 0x00D8, 0x00D9, 0x00DA, 0x00DB, 0x00DC, 0x0130, 0x015E, 0x00DF, 0x00E0, 0x00E1,
            0x00E2, 0x00E3, 0x00E4, 0x00E5, 0x00E6, 0x00E7, 0x00E8, 0x00E9, 0x00EA, 0x00EB, 0x00EC, 0x00ED, 0x00EE,
            0x00EF, 0x011F, 0x00F1, 0x00F2, 0x00F3, 0x00F4, 0x00F5, 0x00F6, 0x00F7, 0x00F8, 0x00F9, 0x00FA, 0x00FB,
            0x00FC, 0x0131, 0x015F, 0x00FF,
        ],
    ),
    // Windows code page 1257: the characters of bytes 0x80..=0xFF (116)
    (
        7,
        &[
            0x20AC, 0x201A, 0x201E, 0x2026, 0x2020, 0x2021, 0x2030, 0x2039, 0x00A8, 0x02C7, 0x00B8, 0x2018, 0x2019,
            0x201C, 0x201D, 0x2022, 0x2013, 0x2014, 0x2122, 0x203A, 0x00AF, 0x02DB, 0x00A0, 0x00A2, 0x00A3, 0x00A4,
            0x00A6, 0x00A7, 0x00D8, 0x00A9, 0x0156, 0x00AB, 0x00AC, 0x00AD, 0x00AE, 0x00C6, 0x00B0, 0x00B1, 0x00B2,
            0x00B3, 0x00B4, 0x00B5, 0x00B6, 0x00B7, 0x00F8, 0x00B9, 0x0157, 0x00BB, 0x00BC, 0x00BD, 0x00BE, 0x00E6,
            0x0104, 0x012E, 0x0100, 0x0106, 0x00C4, 0x00C5, 0x0118, 0x0112, 0x010C, 0x00C9, 0x0179, 0x0116, 0x0122,
            0x0136, 0x012A, 0x013B, 0x0160, 0x0143, 0x0145, 0x00D3, 0x014C, 0x00D5, 0x00D6, 0x00D7, 0x0172, 0x0141,
            0x015A, 0x016A, 0x00DC, 0x017B, 0x017D, 0x00DF, 0x0105, 0x012F, 0x0101, 0x0107, 0x00E4, 0x00E5, 0x0119,
            0x0113, 0x010D, 0x00E9, 0x017A, 0x0117, 0x0123, 0x0137, 0x012B, 0x013C, 0x0161, 0x0144, 0x0146, 0x00F3,
            0x014D, 0x00F5, 0x00F6, 0x00F7, 0x0173, 0x0142, 0x015B, 0x016B, 0x00FC, 0x017C, 0x017E, 0x02D9,
        ],
    ),
];

/// The Unicode range bits of a set of code points, as the four `ulUnicodeRange` words.
pub(crate) fn unicode_ranges(cps: &[u32]) -> [u32; 4] {
    let mut bits = [0u32; 4];
    let mut set = |bit: u8| bits[usize::from(bit / 32)] |= 1 << (bit % 32);
    for &cp in cps {
        if let Some(&(bit, _, _)) = UNICODE_RANGES.iter().find(|&&(_, lo, hi)| lo <= cp && cp <= hi) {
            set(bit);
        }
        if cp > 0xFFFF {
            set(NON_PLANE_0);
        }
    }
    bits
}

/// The code page bits of a set of code points, as the two `ulCodePageRange` words.
pub(crate) fn code_pages(cps: &[u32]) -> [u32; 2] {
    let has = |c: u32| cps.binary_search(&c).is_ok();
    let ascii = (0x20..0x7F).all(has);
    let mut out = [0u32; 2];
    for &(bit, chars) in CODE_PAGES {
        if ascii && chars.iter().all(|&c| has(c)) {
            out[usize::from(bit / 32)] |= 1 << (bit % 32);
        }
    }
    out
}

/// PANOSE weight (`bWeight`) for a `usWeightClass`.
pub(crate) fn panose_weight(weight: u16) -> u8 {
    match weight {
        0..=149 => 2,
        150..=249 => 2,
        250..=349 => 3,
        350..=449 => 5,
        450..=549 => 6,
        550..=649 => 7,
        650..=749 => 8,
        750..=849 => 9,
        850..=949 => 10,
        _ => 11,
    }
}

/// The `fsSelection` bits of a style: bit 0 italic, bit 5 bold, bit 6 regular, bit 7 use typo metrics.
pub(crate) fn fs_selection(style: &Style) -> u16 {
    let mut bits = 1 << 7;
    if style.italic {
        bits |= 1;
    }
    if style.bold {
        bits |= 1 << 5;
    }
    if !style.italic && !style.bold {
        bits |= 1 << 6;
    }
    bits
}

/// The `OS/2` table. `max_context` is the longest context a layout lookup reads (1 for single substitution, 2
/// for pair or mark positioning).
pub(crate) fn os2(family: &Family, built: &Built, style: &Style, max_context: u16) -> Os2 {
    let m = &family.metrics;
    let upm = f64::from(m.upm);
    let scaled = |f: f64| (upm * f + 0.5).floor() as i16;
    let mut cps: Vec<u32> = built.unicodes.iter().flatten().copied().collect();
    cps.sort_unstable();
    cps.dedup();
    let ranges = unicode_ranges(&cps);
    let pages = code_pages(&cps);
    let nonzero: Vec<u16> = built.advances.iter().copied().filter(|&a| a > 0).collect();
    let avg = if nonzero.is_empty() {
        0
    } else if m.fixed_pitch {
        // the specification's value for a monospaced font: the advance (marks have none)
        nonzero.iter().copied().max().unwrap_or(0) as i16
    } else {
        let sum: u64 = nonzero.iter().map(|&a| u64::from(a)).sum();
        ((sum as f64 / nonzero.len() as f64) + 0.5).floor() as i16
    };
    let slope = m.italic_angle.to_radians().tan();
    let sub_y_offset = scaled(0.075);
    let sup_y_offset = scaled(0.35);
    let mut panose = [2, 11, panose_weight(style.weight), 0, 0, 0, 0, 0, 0, 0];
    if m.fixed_pitch {
        panose[3] = 9;
    }
    let first = cps.first().map_or(0, |&c| c.min(0xFFFF) as u16);
    let last = cps.last().map_or(0, |&c| c.min(0xFFFF) as u16);
    Os2 {
        x_avg_char_width: avg,
        us_weight_class: style.weight,
        us_width_class: 5,
        fs_type: 0,
        y_subscript_x_size: scaled(0.65),
        y_subscript_y_size: scaled(0.6),
        y_subscript_x_offset: -((slope * f64::from(sub_y_offset) + 0.5).floor() as i16),
        y_subscript_y_offset: sub_y_offset,
        y_superscript_x_size: scaled(0.65),
        y_superscript_y_size: scaled(0.6),
        y_superscript_x_offset: (slope * f64::from(sup_y_offset) + 0.5).floor() as i16,
        y_superscript_y_offset: sup_y_offset,
        y_strikeout_size: m.strikeout_size,
        y_strikeout_position: m.strikeout_position,
        s_family_class: 0,
        panose_10: panose,
        ul_unicode_range_1: ranges[0],
        ul_unicode_range_2: ranges[1],
        ul_unicode_range_3: ranges[2],
        ul_unicode_range_4: ranges[3],
        ach_vend_id: Tag::new(meta::VENDOR),
        fs_selection: SelectionFlags::from_bits_truncate(fs_selection(style)),
        us_first_char_index: first,
        us_last_char_index: last,
        s_typo_ascender: m.ascender,
        s_typo_descender: m.descender,
        s_typo_line_gap: 0,
        us_win_ascent: m.ascender.max(0) as u16,
        us_win_descent: m.descender.unsigned_abs(),
        ul_code_page_range_1: Some(pages[0]),
        ul_code_page_range_2: Some(pages[1]),
        sx_height: Some(m.x_height),
        s_cap_height: Some(m.cap_height),
        us_default_char: Some(0),
        us_break_char: Some(32),
        us_max_context: Some(max_context),
        us_lower_optical_point_size: None,
        us_upper_optical_point_size: None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ranges_and_code_pages_follow_the_characters() {
        let cps = vec![0x41, 0x2500, 0x1D400];
        let r = unicode_ranges(&cps);
        assert_eq!(r[0], 1); // Basic Latin
        assert_eq!(r[1], (1 << (43 - 32)) | (1 << (57 - 32))); // Box Drawing, non-plane-0
        assert_eq!(r[2], 1 << (89 - 64)); // Mathematical Alphanumeric Symbols
        assert_eq!(code_pages(&cps), [0, 0]);
        let mut latin1: Vec<u32> = (0x20..0x7F).collect();
        latin1.extend(CODE_PAGES[0].1);
        latin1.sort_unstable();
        assert_eq!(code_pages(&latin1)[0] & 1, 1);
    }

    #[test]
    fn panose_weights_of_the_named_instances() {
        let got: Vec<u8> = [300, 400, 500, 600, 700].iter().map(|&w| panose_weight(w)).collect();
        assert_eq!(got, vec![3, 5, 6, 7, 8]);
    }
}
