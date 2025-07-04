#!/usr/bin/env python3

import zstandard as zstd
import json
import numpy as np
import csv
import math

UNDEF_SCORE = 999999
QUEEN_SCORE = 1000
MATE_SCORE = QUEEN_SCORE * 3
# MATE_SCORE = 2**15 - 1 # 32767 = std::numeric_limits<short>::max in c++

def stream_jsonl_zst(filepath):
    with open(filepath, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            buffer = b''
            while True:
                chunk = reader.read(8192)
                if not chunk:
                    break
                buffer += chunk
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line.strip():  # skip empty lines
                        try:
                            yield json.loads(line.decode('utf-8'))
                        except json.JSONDecodeError as e:
                            print(f"JSON parse error: {e} — line: {line}")


def deepest_line(json) -> tuple[str, int, int, list[str]]:
    fen = json['fen']
    evals = json['evals']
    best_eval = evals[np.argmax(list(map(lambda x: x['depth'], evals)))]
    depth = best_eval['depth']
    pvs = best_eval['pvs'][0] # take first PV (the best one)
    moves = pvs["line"].split(' ')

    score = UNDEF_SCORE

    if 'cp' in pvs.keys():
        score = pvs['cp']
    if 'mate' in pvs.keys():
        # math.copysign(x, y) returns the magnitude of x * sign(y) (sign is not implemeted in math because of edgecases)
        sign = int(math.copysign(1, pvs['mate'])) # check if black is mating (mate = -depth)
        score = MATE_SCORE * sign # we ignore mate depth

    if score == UNDEF_SCORE:
        raise Exception(f'Undefined score for position {fen}: terminating')

    return (fen, depth, score, moves)

def count_lines_in_zst(filepath: str) -> int:
    count = 0
    with open(filepath, 'rb') as f:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            buffer = b''
            while True:
                chunk = reader.read(8192)
                if not chunk:
                    break
                buffer += chunk
                while b'\n' in buffer:
                    _, buffer = buffer.split(b'\n', 1)
                    count += 1
    return count

def main(input_path: str, output_path: str, pv_depth: int = 0):
    """
    Stream the input .jsonl.zst, process each JSON object and write results to CSV.
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # Write a header row if desired
        writer.writerow(["fen", "depth", "score"]);

        count = 0
        for obj in stream_jsonl_zst(input_path):
            try:
                fen, depth, score, moves = deepest_line(obj)
                count += 1

                if len(moves) < pv_depth:
                    moves += ["0000"] * (pv_depth - len(moves)) # UCI null-move

                if count % 100000 == 0:
                    print(f"\rProcessed: {count} rows", end='', flush=True)
                if pv_depth > 0:
                    writer.writerow([fen, depth, score, ' '.join(moves[:pv_depth]) ])
                else:
                    writer.writerow([fen, depth, score])
            except Exception as e:
                print(f"Error processing object {obj}: {e}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Stream a .jsonl.zst file, apply f(obj), and write to CSV"
    )
    parser.add_argument(
        'input', help='Path to input .jsonl.zst file',
    )
    parser.add_argument(
        'output', help='Path to output CSV file',
    )
    parser.add_argument(
        '--pv_depth',
        type=int,
        help='Number of moves to extract from the principal variation (default: 0). \
        Note that the lichess database only contains pv lines up to depth 10',
        default=0
    )
    args = parser.parse_args()
    main(args.input, args.output, args.pv_depth)

