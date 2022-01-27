#!/bin/bash

if [ $# != 1 ]; then
  echo "Invalid syntax" 
  echo "usage: convert_dataset <file>"
  exit 1
fi

DATASET=$1
ENGINE=../NapoleonPP

coproc $ENGINE

LINES=$(wc -l < $DATASET)
COUNT=1

read -u ${COPROC[0]} -r line # discard first line of the engine's output (logo)

while IFS= read -r entry; do
  fen=$(echo $entry | cut -d, -f1) # first field of the csv entry is a fen string
  depth=$(echo $entry | cut -d, -f2) # second field of the csv entry is the depth
  score=$(echo $entry | cut -d, -f3) # third field of the csv entry is the score

  echo "$COUNT/$LINES)"
  echo "position fen $fen" >& ${COPROC[1]}
  echo "csv" >& ${COPROC[1]}

  read -u ${COPROC[0]} -r line
  echo "$line,$depth,$score" >> converted.csv

  COUNT=$((COUNT+1))
done < $DATASET

echo "quit" >& ${COPROC[1]}
wait $COPROC_PID
