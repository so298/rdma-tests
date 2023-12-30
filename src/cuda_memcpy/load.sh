#!/bin/bash

db=a.sqlite
table=a
./txt2sql ${db} --table ${table} \
          -r '0 : cpu (?P<cpu>\d+) (?P<dir>..) gpu (?P<gpu>\d+) (?P<bw>.*?) GB/sec' \
          output/out_*.txt
