#!/bin/sh

if [ ! -f cc_test ]; then
    make
fi


echo "cc_test: pack data"
./cc_test test_pack

echo "py_test: unpack data packed by cc_test"
python py_test.py test_unpack


echo "py_test: pack data"
python py_test.py test_pack

echo "cc_test: unpack data packed by py_test"
./cc_test test_unpack


echo "py_test: test array member"
python py_test.py test_array

echo "py_test: test version cutting"
python py_test.py  test_version_cut

echo "py_test: test performance"
python py_test.py perf_test

echo "cc_test: test performance"
./cc_test perf_test
