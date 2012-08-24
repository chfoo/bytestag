# bytestagd configuration script
# This file is a shell script fragment

CACHE_DIR=/var/cache/bytestag/
RUNTIME_LIB_DIR=/var/lib/bytestag/
NODE_ID_FILE=$RUNTIME_LIB_DIR/node_id

mkdir -pv $CACHE_DIR
mkdir -pv $RUNTIME_LIB_DIR

if [ -e $NODE_ID_FILE ]; then
    NODE_ID=`cat $NODE_ID_FILE`
else
    NODE_ID=`python3 -c 'import os, base64; print(base64.b32encode(os.urandom(20)).decode())'`
    echo $NODE_ID > $NODE_ID_FILE
fi

DAEMON_ARGS="--cache-dir $CACHE_DIR --host 0.0.0.0 --port 38664 --node-id $NODE_ID"

