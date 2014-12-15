#!/bin/bash
AUTO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd && echo x)"
AUTO_DIR=${AUTO_DIR%x}
AUTO_DIR="${AUTO_DIR%"${AUTO_DIR##*[![:space:]]}"}"
AUTO_DIR=$AUTO_DIR/..
. $AUTO_DIR/piautomatorenv/bin/activate
pip install -r $AUTO_DIR/conf/requirements.txt
START_UP="python $AUTO_DIR/bin/start-automator.py"
if [ -z ${PIDFILE+x} ]; 
then
  echo "Regular startup"
  $START_UP
else
  echo "Automated startup"
  $START_UP &
fi

