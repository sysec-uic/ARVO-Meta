#include "pin.H"
#include <iostream>
#include <fstream>

KNOB<std::string> KnobTargetModule(KNOB_MODE_WRITEONCE, "pintool", "mod", \
				   "xslt", "Target module name to trace");

std::ofstream TraceFile;

VOID RecordBB(ADDRINT addr) {
    PIN_LockClient();
    IMG img = IMG_FindByAddress(addr);

    if (IMG_Valid(img)) {
        TraceFile << std::hex << addr << std::endl;
    } else {
        TraceFile << std::hex << addr << ": " << "UNKNOWN IMG" << std::endl;
    }
    PIN_UnlockClient();
}


// Instrument each basic block, but only for the xsltproc module
VOID Trace(TRACE trace, VOID *v) {
    for (BBL bbl = TRACE_BblHead(trace); BBL_Valid(bbl); bbl = BBL_Next(bbl)) {
        ADDRINT addr = BBL_Address(bbl);

        IMG img = IMG_FindByAddress(addr);
        if (!IMG_Valid(img))
            continue;

        std::string img_name = IMG_Name(img);

        // Only record basic blocks from the main executable (e.g., xslt)
        if (img_name.find(KnobTargetModule.Value()) == std::string::npos)
            continue;

        BBL_InsertCall(bbl, IPOINT_ANYWHERE, (AFUNPTR)RecordBB,
                       IARG_ADDRINT, addr,
                       IARG_END);
    }
}

VOID Fini(INT32 code, VOID *v) {
    TraceFile.close();
}

int main(int argc, char *argv[]) {
    PIN_Init(argc, argv);
    std::cout << "Tracing module: " << KnobTargetModule.Value() << std::endl;
    TraceFile.open("pin_bbtrace.log");

    TRACE_AddInstrumentFunction(Trace, 0);
    PIN_AddFiniFunction(Fini, 0);

    PIN_StartProgram();
    return 0;
}
