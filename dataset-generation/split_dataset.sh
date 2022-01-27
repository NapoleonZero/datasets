#!/bin/bash


if [ $# != 2 ]; then
  echo "Invalid syntax" 
  echo "usage: split_dataset <file> <blocks>"
  exit 1
fi

FILE=$1
BLOCKS=$2

# split a file in $THREAD_POSITIONS chunks without breaking lines (l/N)
split -d -n l/$BLOCKS $FILE $FILE.part
