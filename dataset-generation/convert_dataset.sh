#!/usr/bin/env bash

if [ $# -lt 2 -o $# -gt 3 ]; then
  echo "Invalid syntax" 
  echo "usage: convert_dataset <input_file> <output_file> [skip-header]"
  exit 1
fi

SKIP_HEADER=true
if [ $# -eq 3 ]; then
  SKIP_HEADER=$3
fi

DATASET=$1
OUTFILE=$2
ENGINE=../NapoleonPP

coproc $ENGINE

LINES=$(wc -l < $DATASET)
COUNT=0

read -u ${COPROC[0]} -r line # discard first line of the engine's output (logo)

while IFS= read -r entry; do
  COUNT=$((COUNT+1))
  if [ $SKIP_HEADER = true ] && [ $COUNT -eq 1 ]; then
    echo "Skipping header"
    echo $entry
    continue
  fi
  fen=$(echo $entry | cut -d, -f1) # first field of the csv entry is a fen string
  depth=$(echo $entry | cut -d, -f2) # second field of the csv entry is the depth
  score=$(echo $entry | cut -d, -f3) # third field of the csv entry is the score

  echo "$COUNT/$LINES)"
  echo "position fen $fen" >& ${COPROC[1]}
  echo "csv" >& ${COPROC[1]}

  read -u ${COPROC[0]} -r line
  echo "$line,$depth,$score" >> $OUTFILE

done < $DATASET

echo "quit" >& ${COPROC[1]}
wait $COPROC_PID
