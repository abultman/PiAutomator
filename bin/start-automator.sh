DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
virtualenv $DIR/../piautomatorenv
source $DIR/../piautomatorenv/bin/activate
pip install -r $DIR/../conf/requirements.txt
$DIR/start-automator.py