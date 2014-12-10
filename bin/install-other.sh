#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
sudo pip install virtualenv
virtualenv $DIR/../piautomatorenv
source $DIR/../piautomatorenv/bin/activate
pip install -r $DIR/../conf/requirements.txt