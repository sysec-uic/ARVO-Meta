#include "pin.H"
#include <iostream>
#include <fstream>

std::ofstream TraceFile;

VOID RecordBB(ADDRINT addr) {
    PIN_LockClient();
    IMG img = IMG_FindByAddress(addr);

    if (IMG_Valid(img)) {
        ADDRINT base = IMG_LowAddress(img);
        std::string name = IMG_Name(img);
        ADDRINT offset = addr - base;

        TraceFile << std::hex << addr << ": " << name << " + 0x" << offset << std::endl;
    } else {
        TraceFile << std::hex << addr << ": " << "UNKNOWN + 0x" << std::hex << (addr) << std::endl;
    }
    PIN_UnlockClient();
}

// Instrument each basic block (BBL = basic block list)
VOID Trace(TRACE trace, VOID *v) {
    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl)) {
        BBL_InsertCall(bbl, IPOINT_ANYWHERE, (AFUNPTR)RecordBB,
                       IARG_ADDRINT, BBL_Address(bbl),
                       IARG_END);
    }
}

VOID Fini(INT32 code, VOID *v) {
    TraceFile.close();
}

int main(int argc, char *argv[]) {
    PIN_Init(argc, argv);
    TraceFile.open("pin_bbtrace.log");

    TRACE_AddInstrumentFunction(Trace, 0);
    PIN_AddFiniFunction(Fini, 0);

    PIN_StartProgram();
    return 0;
}
