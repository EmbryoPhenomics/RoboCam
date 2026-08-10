#!/bin/bash
cd /home/pi/LEC_software_V3
python app.py |& tee "$(ls -1q *stdout.txt | wc -l)_stdout.txt"


