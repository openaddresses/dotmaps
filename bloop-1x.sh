#!/bin/sh -ex

python serve-tiles.py &
TILES_PID=$!

python fuse-sample.py /tmp/dotmaps &
FUSE_PID=$!

sleep 2
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/12/656/1582.mvt"

kill $FUSE_PID $TILES_PID
sleep 1