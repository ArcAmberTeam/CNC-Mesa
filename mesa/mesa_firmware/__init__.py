"""Read-only inspection of Xilinx .bit containers; no device access."""

from ._bitstream import Bitstream, parse_bitstream

__all__ = ["Bitstream", "parse_bitstream"]
