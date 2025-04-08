#!/usr/bin/env bash

if [ $# != 3 ]; then
  echo "Invalid syntax" 
  echo "usage: parallel_generation <file> <depth> <threads>"
  exit 1
fi

trap ctrl_c SIGINT SIGTERM
function ctrl_c() {
  echo -e "\nStopping background processes..."
  kill $(jobs -p)
  rm -f x*.part
  tput cnorm # restore the cursor
  exit 0
}

POSITIONS=$1
DEPTH=$2
THREADS=$3

# split a file in $THREAD_POSITIONS chunks without breaking lines (l/N)
split -d -n l/$THREADS $POSITIONS x --additional-suffix=.part

PIDS=()

# hide cursor to better show the progress bar
tput civis

PREFIX="x0"

if [ $THREADS -gt 100 ]; then
  PREFIX=$PREFIX"0"
fi

PREFIX_WIDTH=$(( ${#THREADS} < 2 ? 2 : ${#THREADS} )) # length of the THREADS string (min value is 2)

#TODO: if $THREADS > 100, use suffixes of length > 1
MAIN_THREAD=true
for i in $( seq 0 $(( THREADS - 1 ))); do
  printf -v PREFIX "x%0*d" "$PREFIX_WIDTH" $i
  # ./generate_dataset.sh "$PREFIX.part" $DEPTH $MAIN_THREAD &
  ./generate_dataset.py "$PREFIX.part" $DEPTH $MAIN_THREAD &
  PIDS[${i}]=$!
  MAIN_THREAD=false
done

# wait for all started processes
for pid in ${PIDS[*]}; do
  wait $pid
done

# restore the cursor
tput cnorm


rm -f x*.part
