#!/usr/bin/env python3
"""
pack_dataset.py: Convert a CSV of structured fields into a packed binary file.

Usage:
    pack_dataset.py -i INPUT -o OUTPUT

Example:
    pack_dataset.py -i data.csv -o out.bin

This script expects each CSV row to have exactly 16 fields in this order:
  - 12 unsigned 64-bit integers (Q)
  -  3 signed   8-bit integers (b)
  -  1 half-precision float   (e)

And packs them in big-endian order (`>QQQQQQQQQQQQbbbe`).
"""
import argparse
import csv
import struct
import sys

# Fixed struct format: 12×uint64, 3×int8, 1×float16
FMT = '>QQQQQQQQQQQQbbbe'

EXTRA_VALUES = [15] # depth is stored in position 15 in the CSV, we discard this one

def parse_args():
    parser = argparse.ArgumentParser(
        description="Pack CSV rows into a binary file using struct format",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-i', '--input', required=True,
                        help='Path to input CSV file')
    parser.add_argument('-o', '--output', required=True,
                        help='Path to output binary file')
    return parser.parse_args()


def pack_csv_to_bin(input_path: str, output_path: str) -> None:
    """
    Reads rows from input CSV and writes packed binary data to output.

    Each row must have exactly 16 fields matching the fixed struct format (+ extra unused fields).
    """
    record_size = struct.calcsize(FMT)
    # Count expected number of values from format: 12 Q's + 3 b's + 1 e
    field_count = FMT.count('Q') + FMT.count('b') + FMT.count('e') + len(EXTRA_VALUES)

    processed_count = 0
    with open(input_path, newline='') as csvfile, \
         open(output_path, 'wb') as binfile:
        reader = csv.reader(csvfile)
        for lineno, row in enumerate(reader, start=1):
            if len(row) != field_count:
                sys.exit(f"Error: Line {lineno} has {len(row)} fields; expected {field_count}")

            try:
                # Parse integers and float
                q_vals = [int(x, 2) for x in row[:12]]
                b_vals = [int(x)   for x in row[12:15]]
                extra_vals = [row[i] for i in EXTRA_VALUES] # discard this values (depth)
                e_val  = float(row[16]) / 100.0
            except ValueError as e:
                sys.exit(f"Error: Line {lineno} conversion failed: {e}")

            # Pack into binary according to the fixed format
            packed = struct.pack(FMT, *q_vals, *b_vals, e_val)
            if len(packed) != record_size:
                sys.exit(f"Error: Packed size {len(packed)} != expected {record_size}")

            binfile.write(packed)
            if processed_count % 1000 == 0:
                print(f"\rProcessed: {processed_count} rows", end='', flush=True)
            processed_count += 1


def main():
    args = parse_args()
    try:
        pack_csv_to_bin(args.input, args.output)
    except Exception as e:
        sys.exit(f"Fatal error: {e}")


if __name__ == '__main__':
    main()
