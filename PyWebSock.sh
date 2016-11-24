#!/bin/bash
#PYWEB_DIR=/usr/local/src/PyWebSock
PYWEB_DIR=.

/usr/bin/python ${PYWEB_DIR}/server.py --root ${PYWEB_DIR}/html $*
