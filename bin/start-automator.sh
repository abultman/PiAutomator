#!/bin/sh
AUTO_DIR=/opt/homeautomation
echo $AUTO_DIR
. $AUTO_DIR/piautomatorenv/bin/activate
pip install -r $AUTO_DIR/conf/requirements.txt
which python
python $AUTO_DIR/bin/start-automator.py &
