#!/bin/sh

scpython eventclient.py --debug -u eventwatch -H proc 2>&1 |
tee -a eventwatch.txt
