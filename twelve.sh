#!/usr/bin/env bash
for i in {1..12}; do
  python3 client.py -p 5555 -n pollo &
done
wait
