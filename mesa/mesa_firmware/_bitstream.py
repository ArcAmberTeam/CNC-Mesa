from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class Bitstream:
    design: str
    part: str
    date: str
    time: str
    payload: bytes

    def metadata(self) -> dict:
        return {
            "design": self.design,
            "part": self.part,
            "date": self.date,
            "time": self.time,
            "payload_bytes": len(self.payload),
            "payload_sha256": sha256(self.payload).hexdigest(),
        }


def parse_bitstream(data: bytes) -> Bitstream:
    """Parse tagged .bit metadata; reject raw .bin, truncation and trailing data.

    The payload is configuration data, not a recoverable VHDL/Verilog listing.
    Header values describe the build; they do not authenticate the hardware.
    """
    offset = 0

    def take(size: int) -> bytes:
        nonlocal offset
        if size > len(data) - offset:
            raise ValueError("Truncated Xilinx bitstream")
        chunk = data[offset:offset + size]
        offset += size
        return chunk

    def length(width: int = 2) -> int:
        return int.from_bytes(take(width), "big")

    if take(length()) != bytes.fromhex("0ff00ff00ff00ff000"):
        raise ValueError("Not a supported Xilinx .bit container")
    if length() != 1:
        raise ValueError("Invalid first tag length")
    values = []
    for tag in b"abcd":
        if take(1) != bytes([tag]):
            raise ValueError("Unexpected bitstream metadata tag")
        field = take(length())
        if not field.endswith(b"\0"):
            raise ValueError("Unterminated bitstream metadata")
        values.append(field[:-1].decode("ascii"))
    if take(1) != b"e":
        raise ValueError("Missing bitstream payload")
    payload = take(length(4))
    if offset != len(data):
        raise ValueError("Trailing data after bitstream payload")
    if bytes.fromhex("aa995566") not in payload[:64]:
        raise ValueError("Missing Xilinx configuration sync word")
    return Bitstream(*values, payload)
