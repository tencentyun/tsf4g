#include <iostream>
#include <fstream>
#include <sstream>
#include "TdrBuf.h"
#include "demo.h"

using namespace std;
using namespace tsf4g_tdr;
using namespace foo;

void initMsg(LPMSG msg) {
    msg->stHead.dwMagic = 1234;
    msg->stHead.wCmd = CMD_START;

    msg->stBody.stBody1.iF1 = 5678;
    for (int i = 0; i < 10; i++) {
        strncpy(msg->stBody.stBody1.aszF2[i], "hello world", 64);
    }
}

int main()
{
    // Test1
    Test1 test;
    test.construct();
    cout << test.tFdate << endl;
    cout << test.tFtime << endl;
    cout << test.tFdatetime << endl;

    MSG msg;
    initMsg(&msg);

    char buffer[4096];
    char buffer2[4096];
    msg.visualize(buffer, sizeof(buffer));
    cout << "======> Msg: " << endl << buffer << endl;
    
    int cutVer = 1;
    size_t usedSize;

    
    TdrError::ErrorType ret = msg.pack(buffer, sizeof(buffer), &usedSize, cutVer);
    if (TdrError::TDR_NO_ERROR == ret) {
        cout << "pack succ, usedSize: " << usedSize << endl;
        /*
        char c;
        // print
        for(int i=0; i < usedSize; ++i) {
            c = buffer[i];
            for (int bit = 0; bit < 8; bit++) {
                printf("%i", (c & 0X80) >> 7);
                c <<= 1;
            }
            printf("\n");
        }
        */
        
        ofstream ofs;
        ofs.open("pack.data", ofstream::binary);
        ofs.write(buffer, usedSize);
        ofs.close();


        ifstream ifs;
        ifs.open("pack.data", ofstream::binary);
        ifs.read(buffer2, 4096);
        
        /*
        // print
        cout << "read from file: " << endl;
        for(int i=0; i < usedSize; ++i) {
            c = buffer2[i];
            for (int bit = 0; bit < 8; bit++) {
                printf("%i", (c & 0X80) >> 7);
                c <<= 1;
            }
            printf("\n");
        }
        */

        ifs.close();
    }
    return 0;
}

