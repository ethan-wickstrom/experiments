"""Input decoding, text layout, the editor, and the diffing renderer."""

import unittest

from frond.tui.editor import Editor
from frond.tui.keys import Decoder, Focus, Key, Mouse, Paste
from frond.tui.screen import Buffer, Renderer
from frond.tui.style import Style, make_theme, parse_osc_color, rgb_to_256, sgr
from frond.tui.text import Span, char_width, line_text, line_width, str_width, truncate, wrap


def decode(*chunks: bytes, flush: bool = False):
    d = Decoder()
    out = []
    for c in chunks:
        out += d.feed(c)
    if flush:
        out += d.flush()
    return out


class DecoderTest(unittest.TestCase):
    def test_printable_and_utf8_split_across_reads(self):
        events = decode(b"a\xc3", b"\xa9\xe2\x82", b"\xac")
        self.assertEqual(events, [Key("a"), Key("é"), Key("€")])

    def test_control_keys(self):
        self.assertEqual(
            decode(b"\r\t\x7f\x01\n"),
            [Key("enter"), Key("tab"), Key("backspace"), Key("a", ctrl=True), Key("j", ctrl=True)],
        )

    def test_csi_and_ss3_navigation_with_modifiers(self):
        self.assertEqual(
            decode(b"\x1b[A\x1bOB\x1b[1;5C\x1b[5~\x1b[3;2~"),
            [Key("up"), Key("down"), Key("right", ctrl=True), Key("pageup"), Key("delete", shift=True)],
        )

    def test_kitty_protocol_keys(self):
        self.assertEqual(
            decode(b"\x1b[13;2u\x1b[27u\x1b[99;5u"), [Key("enter", shift=True), Key("escape"), Key("c", ctrl=True)]
        )

    def test_lone_escape_needs_flush_and_alt_keys(self):
        d = Decoder()
        self.assertEqual(d.feed(b"\x1b"), [])
        self.assertTrue(d.pending())
        self.assertEqual(d.flush(), [Key("escape")])
        self.assertEqual(decode(b"\x1bb\x1b\r"), [Key("b", alt=True), Key("enter", alt=True)])

    def test_bracketed_paste_across_reads(self):
        events = decode(b"\x1b[200~line one\r\nline", b" two\x1b[20", b"1~x")
        self.assertEqual(events, [Paste("line one\nline two"), Key("x")])

    def test_sgr_mouse(self):
        events = decode(b"\x1b[<64;10;5M\x1b[<65;10;5M\x1b[<0;3;4M\x1b[<0;3;4m")
        self.assertEqual(
            events,
            [Mouse("wheel_up", 9, 4), Mouse("wheel_down", 9, 4), Mouse("press", 2, 3, 0), Mouse("release", 2, 3, 0)],
        )

    def test_focus_and_osc_replies_are_handled(self):
        self.assertEqual(decode(b"\x1b[I\x1b]11;rgb:1e1e/1e1e/2020\x07\x1b[O"), [Focus(True), Focus(False)])

    def test_incomplete_sequence_waits(self):
        d = Decoder()
        self.assertEqual(d.feed(b"\x1b[1;"), [])
        self.assertEqual(d.feed(b"5D"), [Key("left", ctrl=True)])


class TextTest(unittest.TestCase):
    def test_widths(self):
        self.assertEqual(char_width("a"), 1)
        self.assertEqual(char_width("界"), 2)
        self.assertEqual(char_width("́"), 0)
        self.assertEqual(str_width("é界"), 3)

    def test_wrap_preserves_styles_and_respects_width(self):
        bold = Style(bold=True)
        line = [Span("hello ", bold), Span("wonderful world of terminals")]
        rows = wrap(line, 12, prefix=[Span("> ")], continuation=[Span("  ")])
        self.assertTrue(all(line_width(r) <= 12 for r in rows))
        self.assertEqual(line_text(rows[0]), "> hello")
        self.assertEqual(rows[0][1].style, bold)
        self.assertEqual(
            " ".join(line_text(r).strip() for r in rows).replace(">", "").split(),
            ["hello", "wonderful", "world", "of", "terminals"],
        )

    def test_wrap_splits_long_words_and_wide_chars(self):
        rows = wrap([Span("x" * 25)], 10)
        self.assertEqual([line_width(r) for r in rows], [10, 10, 5])
        rows = wrap([Span("界" * 7)], 5)
        self.assertTrue(all(line_width(r) <= 5 for r in rows))

    def test_truncate(self):
        self.assertEqual(line_text(truncate([Span("abcdefgh")], 5)), "abcd…")
        self.assertEqual(line_text(truncate([Span("abc")], 5)), "abc")


class EditorTest(unittest.TestCase):
    def test_editing_and_kill_ring(self):
        e = Editor()
        e.insert("hello brave world")
        e.kill_word_left()
        self.assertEqual(e.text, "hello brave ")
        e.home()
        e.kill_to_end()
        self.assertEqual(e.text, "")
        e.yank()
        self.assertEqual(e.text, "hello brave ")
        e.undo()
        self.assertEqual(e.text, "")

    def test_layout_and_caret_never_overflow(self):
        e = Editor()
        e.insert("the quick brown fox jumps over the lazy dog\nsecond line")
        for width in range(6, 40):
            rows = e.layout(width)
            self.assertTrue(all(str_width(r.text) <= width for r in rows), width)
            for pos in range(len(e.text) + 1):
                e.cursor = pos
                col, row = e.caret(width)
                self.assertLess(col, width, (width, pos))
                self.assertLessEqual(row, len(rows), (width, pos))

    def test_vertical_movement_keeps_column(self):
        e = Editor()
        e.insert("abcdef\nab\nabcdef")
        e.cursor = 5
        self.assertTrue(e.move_vertical(1, 40))
        self.assertEqual(e.cursor, 9)  # end of "ab"
        self.assertTrue(e.move_vertical(1, 40))
        self.assertEqual(e.cursor, 15)  # back to column 5
        self.assertFalse(e.move_vertical(1, 40))

    def test_history_restores_draft(self):
        e = Editor()
        e.remember("first")
        e.remember("second")
        e.insert("draft")
        self.assertTrue(e.history_prev())
        self.assertEqual(e.text, "second")
        self.assertTrue(e.history_prev())
        self.assertEqual(e.text, "first")
        e.history_next()
        e.history_next()
        self.assertEqual(e.text, "draft")

    def test_completion_tokens(self):
        e = Editor()
        e.insert("look at @src/ma")
        token = e.token()
        assert token is not None
        self.assertEqual((token.kind, token.query, token.start), ("mention", "src/ma", 8))
        e.set("/he")
        token = e.token()
        assert token is not None
        self.assertEqual((token.kind, token.query), ("command", "he"))
        e.set("email me@example.com")
        self.assertIsNone(e.token())


class ScreenTest(unittest.TestCase):
    def test_wide_characters_and_overwrites(self):
        buf = Buffer(6, 1)
        buf.put(0, 0, "界a")
        self.assertEqual(buf.chars[0][:3], ["界", "", "a"])
        buf.put(1, 0, "b")  # writing over the tail of a wide char blanks its head
        self.assertEqual(buf.chars[0][:3], [" ", "b", "a"])
        x = buf.put(5, 0, "界")  # does not fit in the last column
        self.assertEqual((x, buf.chars[0][5]), (6, " "))

    def test_renderer_emits_only_changes(self):
        r = Renderer("truecolor")
        buf = Buffer(10, 3)
        buf.put(0, 1, "hello")
        first = r.render(buf)
        self.assertIn("hello", first)
        again = Buffer(10, 3)
        again.put(0, 1, "hello")
        self.assertNotIn("hello", r.render(again))
        changed = Buffer(10, 3)
        changed.put(0, 1, "help!")
        out = r.render(changed)
        self.assertIn("\x1b[2;4H", out)  # jumps straight to the first differing cell
        self.assertIn("p!", out)
        self.assertNotIn("hel", out)

    def test_styles_and_colors(self):
        self.assertEqual(sgr(Style(fg=(255, 0, 0), bold=True), "truecolor"), "\x1b[0;1;38;2;255;0;0m")
        self.assertEqual(rgb_to_256((255, 0, 0)), 196)
        self.assertEqual(parse_osc_color("\x1b]11;rgb:ffff/8080/0000\x07"), (255, 128, 0))
        dark, light = make_theme(dark=True), make_theme(dark=False)
        self.assertNotEqual(dark.panel, light.panel)


if __name__ == "__main__":
    unittest.main()
