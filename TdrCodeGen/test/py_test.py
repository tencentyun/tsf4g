#!/usr/bin/env python
# encoding: utf-8

import sys
from demo import demo

def test_pack(datafile = 'test.dat'):
    m = demo.Test1()
    buf = m.pack()
    open(datafile, 'wb').write(buf)
    print('data=%s' % m)
    print('size=%d' % len(buf))

def test_unpack(datafile = 'test.dat'):
    buf = open(datafile, 'rb').read()
    m = demo.Test1()
    size = m.unpack(buf)
    print('data=%s' % m)
    print('size=%d' % size)

def test_array():
    m1 = demo.Test2()
    m1.item_list = range(0, 100, 5)
    print('m1=%s' % m1)
    buf = m1.pack()
    m2 = demo.Test2()
    m2.unpack(buf)
    print('m2=%s' % m2)
    assert m1.item_list == m2.item_list
    assert m2.item_num == len(m2.item_list)

def test_version_cut():
    m1 = demo.Msg()
    m1.head.cmd = demo.CMD_END
    b2 = m1.body.body2
    b2.f1 = 300
    b2.f2 = 'Hellow world'
    buf = m1.pack(2) # f2 cutted
    m2 = demo.Msg()
    m2.unpack(buf)
    assert m2.head.version == 2
    assert m2.body.body2.f2 == 'BBB'
    print('m1=%s' % m1)
    print('m2=%s' % m2)


def perf_test(num = 1000000):
    from timeit import timeit

    m = demo.Test1()
    t = timeit(m.pack, number=num)
    print('pack:num=%d,time=%.6fms,qps=%d' % (
        num, t * 1000, num / t))

    buf = m.pack()
    t = timeit(lambda:m.unpack(buf), number=num)
    print('unpack:num=%d,time=%.6fms,qps=%d' % (
        num, t * 1000, num / t))

def main():
    '''usage: python py_test.py action
    action  test_pack|test_unpack|test_array|test_version_cut|perf_test
    '''
    argv = sys.argv[1:]
    if len(argv) < 1:
        print(main.__doc__)
        sys.exit(-1)

    action = argv[0]
    tests = {
        'test_pack':test_pack,
        'test_unpack':test_unpack,
        'test_array':test_array,
        'test_version_cut':test_version_cut,
        'perf_test':perf_test,
    }

    if action not in tests:
        print('wrong action:%s' % action)
        print(main.__doc__)
        sys.exit(-1)

    fun = tests[action]
    if action == 'perf_test':
        # pypy 预热
        perf_test(10)
    fun()

if __name__ == '__main__':
    main()
