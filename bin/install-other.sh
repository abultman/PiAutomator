#!/bin/bash
DIR=$( cd "$( dirname $0 )" && pwd )
sudo pip install virtualenv
virtualenv --always-copy $DIR/../piautomatorenv
source $DIR/../piautomatorenv/bin/activate
pip install -r $DIR/../conf/requirements.txt
