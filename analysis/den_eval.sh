#!/bin/bash

for i in $(seq -w 00 23); do
    python den_eval.py $i
    echo "Done with $i"
done