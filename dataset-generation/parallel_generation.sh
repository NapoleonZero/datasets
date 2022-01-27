#!/bin/bash

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

#TODO: if $THREADS > 10, use suffixes of length > 2
MAIN_THREAD=true
for i in $( seq 0 $(( THREADS - 1 ))); do
  ./generate_dataset.sh "x0$i.part" $DEPTH $MAIN_THREAD &
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
