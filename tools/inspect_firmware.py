import argparse
import json
from pathlib import Path
from mesa_firmware import parse_bitstream

parser = argparse.ArgumentParser(description="Read Xilinx .bit metadata without connecting to hardware")
parser.add_argument("bitstream", type=Path)
args = parser.parse_args()
print(json.dumps(parse_bitstream(args.bitstream.read_bytes()).metadata(), indent=2))
