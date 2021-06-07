#!/bin/bash

if [ -z ${PROJECT_ROOT+x} ]
then
    PROJECT_ROOT=$(pwd)
    echo "Setting PROJECT_ROOT to $PROJECT_ROOT"
else
    echo "PROJECT_ROOT is $PROJECT_ROOT"
fi


MARVIS_PATH=$PROJECT_ROOT/marvis

BASE_PATH_NS3=$PROJECT_ROOT/ns-3_c-v2x

export SUMO_HOME=/home/paul/Downloads/sumo-1.9.0    # <--- Change this setting to your local SUMO path

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$BASE_PATH_NS3/build/lib/
export PYTHONPATH=$BASE_PATH_NS3/build/bindings/python/:$MARVIS_PATH:$PYTHONPATH

export NS3_EXECUTABLE_PATH=$BASE_PATH_NS3/build/src/fd-net-device:$BASE_PATH_NS3/build/src/tap-bridge
export NS3_MODULE_PATH+=$BASE_PATH_NS3/build/lib

export PATH=$PATH:$BASE_PATH_NS3/build/src/fd-net-device:$BASE_PATH_NS3/build/src/tap-bridge

export COLOREDLOGS_DATE_FORMAT="%H:%M:%S"
export COLOREDLOGS_LOG_FORMAT="%(asctime)s %(name)-32s %(levelname)-8s %(message)s"
export COLOREDLOGS_LOG_LEVEL="DEBUG"
export COLOREDLOGS_LEVEL_STYLES="debug=cyan;warning=yellow;error=red;critical=red,bold" 
export COLOREDLOGS_AUTO_INSTALL="true"
export PYLXD_WARNINGS="none"

cd $PROJECT_ROOT/tdis
PYTHON_TO_USE=python3   # <--- Change this setting to use a specific Python
$PYTHON_TO_USE tdis.py
