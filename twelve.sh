#!/usr/bin/env bash
for i in {1..13}; do
  python -m zappy_ai.client -p 4444 -n pollo &
done
wait
