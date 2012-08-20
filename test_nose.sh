#!/bin/sh

nosetests3 -w src/py3/ \
	--logging-format \
	"%(message)s
  %(asctime)s %(name)s:%(lineno)s %(levelname)s %(threadName)s:%(thread)d" \
	--logging-datefmt "%H:%M:%S" --with-coverage \
	--cover-package bytestag
