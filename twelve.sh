#!/usr/bin/env bash
for i in {1..13}; do
  python3 client.py -p 4444 -n pollo &
done
wait
