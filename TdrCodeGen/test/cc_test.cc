#include <unistd.h>
#include <stdio.h>
#include <sys/time.h>
#include <string.h>
#include <assert.h>
#include "demo.h"

using namespace demo;

static inline double WalltimeNow() {
  timeval tv = {0};
  gettimeofday(&tv, NULL);
  return (tv.tv_sec + tv.tv_usec / 1000000.0);
}

template <typename MsgType>
const char* TdrMsgString(const MsgType &msg, char *buf, size_t size, char sep = '\n') {
  return msg.visualize_ex(buf, size, NULL, 0, sep);
}

template <typename MsgType>
static inline const char* TdrMsgString(const MsgType &msg,
                                       char sep = '\n') {
  static char buf[4096*100] ;
  buf[0]=buf[sizeof(buf)-1]=0;
  return TdrMsgString<MsgType>(msg, buf, sizeof(buf), sep);
}


void test_pack(const char *filename="test.dat") {
  Test1 m;
  m.construct();

  char buf[1024] = {0};
  size_t used = 0;
  m.pack(buf, sizeof(buf), &used);

  FILE *f = fopen(filename, "wb");
  fwrite(buf, 1, used, f);
  fclose(f);

  printf("data=%s\n", TdrMsgString(m));
  printf("size=%lu\n", used);
}

void test_unpack(const char *filename="test.dat") {
  Test1 m;
  FILE *f = fopen(filename, "rb");
  assert(f != NULL);

  char buf[1024];
  size_t num = fread(buf, 1, sizeof(buf), f);
  fclose(f);

  size_t used = 0;
  int ret = m.unpack(buf, num, &used);
  assert(ret == 0);

  printf("data=%s\n", TdrMsgString(m));
  printf("size=%lu\n", used);
}

void perf_test() {
  int num = 100000;
  char buf[1024];
  size_t pack_size = 0;

  Test1 m;
  m.pack(buf, sizeof(buf), &pack_size);

  double t0 = WalltimeNow();
  size_t used = 0;
  for (int i = 0; i < num; ++i) {
    m.pack(buf, sizeof(buf), &used);
  }

  double t1 = WalltimeNow();
  printf("pack:num=%d,time=%.6fms,qps=%d\n", num, (t1-t0)*1000,
         int(num/(t1-t0)));

  t0 = WalltimeNow();
  for (int i = 0; i < num; ++i) {
    m.unpack(buf, pack_size, &used);
  }
  t1 = WalltimeNow();
  printf("unpack:num=%d,time=%.6fms,qps=%d\n", num, (t1-t0)*1000,
         int(num/(t1-t0)));
}

int main(int argc, char **argv) {
  if (argc < 2) {
    printf("usage: ./cc_test action\n");
    printf("  action test_pack|test_unpack|perf_test\n");
    exit(-1);
  }

  char *action = argv[1];
  if (strcmp(action, "test_pack") == 0) {
    test_pack();
  } else if (strcmp(action, "test_unpack") == 0) {
    test_unpack();
  } else if (strcmp(action, "perf_test") == 0) {
    perf_test();
  } else {
    printf("wrong action:%s\n", action);
  }

  return 0;
}
