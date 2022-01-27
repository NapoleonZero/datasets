#!/bin/bash

if [ $# -le 2 ]; then
  echo "Invalid syntax" 
  echo "usage: generate_dataset <file> <depth> [is_main_thread]"
  exit 1
fi

MAIN_THREAD=false

if [ $# == 3 ]; then
  MAIN_THREAD=$3
fi

POSITIONS=$1
DEPTH=$2
ENGINE=../NapoleonPP
COLS=$(tput cols)

function progress() {
  p=$1
  str=" $p%\r"
  for i in $( seq 0 $(( COLS * p / 100 - ${#str} )) ); do
    echo -n "█"
  done
  echo -ne "$str"
}

coproc $ENGINE
# echo "FD in: ${COPROC[0]}"
# echo "FD out: ${COPROC[1]}"

trap ctrl_c INT SIGTERM
function ctrl_c() {
  echo "Stopping dataset generation..."
  echo "quit" >& ${COPROC[1]}
  wait $COPROC_PID
  exit 0
}


read -t 5 -u ${COPROC[0]} -r line || echo "Engine timed-out during initialization"
echo "setoption Record" >& ${COPROC[1]} # Tell the engine to record the evaluations in a csv file
LINES=$(wc -l < $POSITIONS)
COUNT=1

function restart() {
  echo "Restoring failed coprocess...";
  wait $COPROC_PID;
  coproc $ENGINE;
  read -t 5 -u ${COPROC[0]} -r line || echo "Engine timed-out upon restart"
  echo "setoption Record" >& ${COPROC[1]};
  echo "Coprocess restored...";
}

function isready() {
  echo "isready" >& ${COPROC[1]}
  IFS= read -t 5 -u ${COPROC[0]} -r ready
  return [[ $ready == readyok* ]]
}

while IFS= read -r fen; do
  echo "position fen $fen" >& ${COPROC[1]}

  # if [[ isready ]]; then
  #   echo "Engine not ready: $fen"
  # fi

  # print a progress bar if this is the main thread
  if [[ $MAIN_THREAD == true ]] && ((  $COUNT % 100 == 0 )) ; then
    progress $((100 * COUNT / LINES))
  fi

  echo "go depth $DEPTH" >& ${COPROC[1]}
  while ! read -t 0.5 -u ${COPROC[0]} -r line; do
    echo "Sending go command again: $fen"
    echo "go depth $DEPTH" >& ${COPROC[1]}
  done

  # while IFS= read -t 5 -u ${COPROC[0]} -r line || echo "Timed-out after go command: $fen"; do
  while : ; do
    if [[ $line == bestmove* ]]; then # Done searching
      break
    elif [[ $line == Position* ]]; then # Error in the position
      restart
      break
    elif [[ $line != info* ]]; then
      echo "Unexpected output with position $fen: $line"
      break
    else 
      read -u ${COPROC[0]} -r line || break
    fi
  done 
  COUNT=$((COUNT+1))

done < $POSITIONS

echo "quit" >& ${COPROC[1]}
# wait $COPROC_PID
