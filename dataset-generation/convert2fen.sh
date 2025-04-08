#!/usr/bin/env bash

if [ $# != 2 ]; then
  echo "Invalid syntax" 
  echo "usage: convert2fen <file> <threads>"
  exit 1
fi

FILE=$1
THREADS=$2

# split a file in $THREAD_POSITIONS chunks without breaking lines (l/N)
split -d -n l/$THREADS $FILE chunk_ --additional-suffix=.part

parallel "../pgn-extract/pgn-extract -Wfen --notags -D {} | sed '/^$/d' > {}.out" ::: chunk_*

cat *.out > ${FILE}.fen # merge the chunks and remove blank lines with sed

rm -f chunk_*.part*


