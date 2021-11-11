# make file for cc_test

CC_FLAGS = -Idemo -Wall -O2 -fno-strict-aliasing
TDR_FILES = demo/common.cpp demo/demo.cpp demo/TdrBuf.cpp demo/TdrBufUtil.cpp demo/TdrError.cpp \
	demo/TdrPal.cpp demo/TdrThirdParty.cpp demo/TdrTime.cpp demo/TdrTypeUtil.cpp

all : cc_test

cc_test : cc_test.cc tdr_compile
	g++ $(CC_FLAGS) -o $@ cc_test.cc $(TDR_FILES)

tdr_compile : demo.xml
	./tdr -pPl demo.xml common.xml
	python ../tdr2x.py demo.xml

clean:
	rm -rf cc_test demo test.dat
