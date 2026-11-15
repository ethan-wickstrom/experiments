//! The tables every TrueType font has: `head hhea maxp hmtx cmap loca glyf post gasp prep`.

use write_fonts::FontBuilder;
use write_fonts::tables::cmap::Cmap;
use write_fonts::tables::gasp::{Gasp, GaspRange, GaspRangeBehavior};
use write_fonts::tables::head::{Flags, Head, MacStyle};
use write_fonts::tables::hhea::Hhea;
use write_fonts::tables::hmtx::{Hmtx, LongMetric};
use write_fonts::tables::loca::LocaFormat;
use write_fonts::tables::maxp::Maxp;
use write_fonts::tables::post::Post;
use write_fonts::types::{FWord, Fixed, GlyphId, LongDateTime, Tag, UfWord};

use crate::{Built, Error, Family, Style, meta};

/// The `prep` program of an unhinted TrueType font: smart dropout control (`PUSHW 511 SCANCTRL PUSHB 4
/// SCANTYPE`).
pub const PREP: [u8; 7] = [0xB8, 0x01, 0xFF, 0x85, 0xB0, 0x04, 0x8D];

/// `head.flags` of the compiler's fonts: bit 0 (baseline at y = 0) and bit 1 (left sidebearing at x = 0).
/// `rachis build` adds bit 3 after hinting.
pub const HEAD_FLAGS: u16 = 0b11;

/// `gasp`: grid-fit and smooth, symmetrically, at every size.
pub const GASP_BEHAVIOR: u16 = 0x000F;

pub(crate) fn add<T>(builder: &mut FontBuilder, table: &T) -> Result<(), Error>
where
    T: write_fonts::FontWrite + write_fonts::validate::Validate + write_fonts::read::TopLevelTable,
{
    builder.add_table(table).map(|_| ()).map_err(|e| Error::Table(e.to_string()))
}

/// `macStyle` for a style: bit 0 bold, bit 1 italic.
pub(crate) fn mac_style(style: &Style) -> u16 {
    u16::from(style.bold) | (u16::from(style.italic) << 1)
}

/// Add `head hhea maxp hmtx cmap loca glyf post gasp prep`.
pub(crate) fn add_basic_tables(
    builder: &mut FontBuilder,
    family: &Family,
    built: &Built,
    style: &Style,
) -> Result<(), Error> {
    let m = &family.metrics;
    let glyf = &built.glyf;

    // head
    let mut bbox: Option<(i16, i16, i16, i16)> = None;
    for b in glyf.bboxes.iter().flatten() {
        bbox = Some(match bbox {
            None => (b.x_min, b.y_min, b.x_max, b.y_max),
            Some((a, b0, c, d)) => (a.min(b.x_min), b0.min(b.y_min), c.max(b.x_max), d.max(b.y_max)),
        });
    }
    let (x_min, y_min, x_max, y_max) = bbox.unwrap_or_default();
    let stamp = LongDateTime::new(meta::EPOCH + meta::MAC_EPOCH_OFFSET);
    let revision = f64::from(meta::VERSION.0) + f64::from(meta::VERSION.1) / 1000.0;
    let mut head = Head::new(
        Fixed::from_f64(revision),
        0,
        Flags::from_bits_truncate(HEAD_FLAGS),
        m.upm,
        stamp,
        stamp,
        x_min,
        y_min,
        x_max,
        y_max,
        MacStyle::from_bits_truncate(mac_style(style)),
        6,
        match glyf.loca_format {
            LocaFormat::Short => 0,
            LocaFormat::Long => 1,
        },
    );
    head.font_direction_hint = 2;
    add(builder, &head)?;

    // hmtx and hhea
    let n = built.advances.len();
    let lsb = |i: usize| glyf.bboxes[i].map_or(0, |b| b.x_min);
    let mut long = n;
    while long > 1 && built.advances[long - 1] == built.advances[long - 2] {
        long -= 1;
    }
    let metrics: Vec<LongMetric> = (0..long).map(|i| LongMetric::new(built.advances[i], lsb(i))).collect();
    let lsbs: Vec<i16> = (long..n).map(lsb).collect();
    add(builder, &Hmtx::new(metrics, lsbs))?;

    let advance_max = built.advances.iter().copied().max().unwrap_or(0);
    let mut min_lsb = i16::MAX;
    let mut min_rsb = i16::MAX;
    let mut max_extent = i16::MIN;
    for (i, b) in glyf.bboxes.iter().enumerate() {
        let Some(b) = b else { continue };
        min_lsb = min_lsb.min(b.x_min);
        let rsb = i32::from(built.advances[i]) - i32::from(b.x_max);
        min_rsb = min_rsb.min(rsb.clamp(i32::from(i16::MIN), i32::from(i16::MAX)) as i16);
        max_extent = max_extent.max(b.x_max);
    }
    if max_extent == i16::MIN {
        (min_lsb, min_rsb, max_extent) = (0, 0, 0);
    }
    let (rise, run) = caret_slope(m.italic_angle, m.upm);
    let hhea = Hhea::new(
        FWord::new(m.ascender),
        FWord::new(m.descender),
        FWord::new(0),
        UfWord::new(advance_max),
        FWord::new(min_lsb),
        FWord::new(min_rsb),
        FWord::new(max_extent),
        rise,
        run,
        0,
        u16::try_from(long).map_err(|_| Error::Family("too many glyphs".into()))?,
    );
    add(builder, &hhea)?;

    // maxp
    let s = glyf.maxp;
    let mut maxp = Maxp::new(u16::try_from(n).map_err(|_| Error::Family("too many glyphs".into()))?);
    maxp.max_points = Some(s.points);
    maxp.max_contours = Some(s.contours);
    maxp.max_composite_points = Some(s.composite_points);
    maxp.max_composite_contours = Some(s.composite_contours);
    maxp.max_zones = Some(1);
    maxp.max_twilight_points = Some(0);
    maxp.max_storage = Some(0);
    maxp.max_function_defs = Some(0);
    maxp.max_instruction_defs = Some(0);
    maxp.max_stack_elements = Some(0);
    maxp.max_size_of_instructions = Some(0);
    maxp.max_component_elements = Some(s.component_elements);
    maxp.max_component_depth = Some(s.component_depth);
    add(builder, &maxp)?;

    // cmap
    let mut mappings = Vec::new();
    for (gid, cps) in built.unicodes.iter().enumerate() {
        for &cp in cps {
            let c = char::from_u32(cp).ok_or_else(|| Error::Glyph {
                glyph: built.names[gid].clone(),
                detail: format!("U+{cp:04X} is not a character"),
            })?;
            let g = u32::try_from(gid).map_err(|_| Error::Family("too many glyphs".into()))?;
            mappings.push((c, GlyphId::new(g)));
        }
    }
    let cmap = Cmap::from_mappings(mappings).map_err(|e| Error::Family(format!("cmap: {e}")))?;
    add(builder, &cmap)?;

    // glyf and loca
    add(builder, &glyf.glyf)?;
    add(builder, &glyf.loca)?;

    // post
    let mut post = Post::new_v2(built.names.iter().map(String::as_str));
    post.italic_angle = Fixed::from_f64(-m.italic_angle);
    post.underline_position = FWord::new(m.underline_position);
    post.underline_thickness = FWord::new(m.underline_thickness);
    post.is_fixed_pitch = u32::from(m.fixed_pitch);
    add(builder, &post)?;

    // gasp and prep
    let gasp = Gasp::new(1, 1, vec![GaspRange::new(0xFFFF, GaspRangeBehavior::from_bits_truncate(GASP_BEHAVIOR))]);
    add(builder, &gasp)?;
    builder.add_raw(Tag::new(b"prep"), PREP.to_vec());
    Ok(())
}

/// `hhea.caretSlopeRise` and `caretSlopeRun` for an italic angle in degrees (positive leans right): vertical
/// is 1/0; a slanted caret rises one em and runs tan(angle) em.
pub(crate) fn caret_slope(angle: f64, upm: u16) -> (i16, i16) {
    if angle == 0.0 {
        return (1, 0);
    }
    let run = (angle.to_radians().tan() * f64::from(upm) + 0.5).floor();
    (upm as i16, run as i16)
}
