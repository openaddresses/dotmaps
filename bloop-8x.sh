#!/bin/sh -ex

python serve-tiles.py &
TILES_PID=$!

python fuse-sample.py /tmp/dotmaps &
FUSE_PID=$!

sleep 2
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/12/656/1582.mvt" &
CURL1_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/14/2809/6541.mvt" &
CURL2_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/12/656/1583.mvt" &
CURL3_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/14/2809/6542.mvt" &
CURL4_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/12/657/1582.mvt" &
CURL5_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/14/2810/6541.mvt" &
CURL6_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/12/657/1583.mvt" &
CURL7_PID=$!
curl -w "@format.txt" -o /dev/null -s "http://127.0.0.1:5000/14/2810/6542.mvt" &
CURL8_PID=$!

wait $CURL1_PID $CURL2_PID $CURL3_PID $CURL4_PID $CURL5_PID $CURL6_PID $CURL7_PID $CURL8_PID

kill $FUSE_PID $TILES_PID
sleep 1