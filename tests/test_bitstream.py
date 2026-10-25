from pathlib import Path
import unittest

from mesa_firmware import parse_bitstream

ROOT = Path(__file__).resolve().parents[1]


class BitstreamTests(unittest.TestCase):
    def setUp(self):
        self.data = (ROOT / "mesa/firmware/original/TopEthernetHostMot2.bit").read_bytes()

    def test_supplied_firmware_identifies_device(self):
        bit = parse_bitstream(self.data)
        self.assertEqual(bit.part, "6slx9tqg144")
        self.assertIn("UserID=0x00007192", bit.design)
        self.assertEqual(len(bit.payload), 340884)

    def test_truncation_is_rejected(self):
        for size in (0, 1, 10, 20, 50, 100, len(self.data) - 1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                parse_bitstream(self.data[:size])

    def test_raw_binary_and_trailing_data_are_rejected(self):
        for data in (parse_bitstream(self.data).payload, self.data + b"extra"):
            with self.assertRaises(ValueError):
                parse_bitstream(data)

    def test_invalid_lengths_tags_and_sync_are_rejected(self):
        for data in (
            b"\xff\xff" + self.data[2:],
            self.data.replace(b"\x00\x01a", b"\x00\x01z", 1),
            self.data.replace(bytes.fromhex("aa995566"), b"\x00" * 4, 1),
        ):
            with self.assertRaises(ValueError):
                parse_bitstream(data)
