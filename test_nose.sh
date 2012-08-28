#!/bin/sh

nosetests3 src/py3/bytestag \
	--logging-format \
	"%(message)s
  %(asctime)s %(name)s:%(lineno)s %(levelname)s %(threadName)s:%(thread)d" \
	--logging-datefmt "%H:%M:%S" #--with-coverage \
#	--cover-package bytestag
