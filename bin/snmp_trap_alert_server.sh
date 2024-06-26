#!/usr/bin/env sh

cd $(dirname "$0")/..
project_root=$(pwd)
echo "当前项目目录: $project_root"

export PYTHONPATH=$project_root/src:$PYTHONPATH
# 环境变量
export LOG_HEADER="snmp"

pip freeze | sort
exec python3 $project_root/src/alert_server.py
