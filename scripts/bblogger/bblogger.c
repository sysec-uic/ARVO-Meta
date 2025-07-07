#include <dr_api.h>
#include <dr_modules.h>
#include <string.h>

static file_t log_file;
static void event_exit(void);

// callback function prototype for the basic block event
static dr_emit_flags_t
event_app_instruction(void *drcontext, void *tag, instrlist_t *bb,
                      bool for_trace, bool translating);

DR_EXPORT void
dr_client_main(__attribute__((unused)) client_id_t id,
               __attribute__((unused)) int argc,
               __attribute__((unused)) const char *argv[]) {
    dr_set_client_name("DrBblogger", "https://dynamorio.org");

    log_file = dr_open_file("bbtrace.log", DR_FILE_WRITE_OVERWRITE | DR_FILE_ALLOW_LARGE);
    DR_ASSERT(log_file != INVALID_FILE);

    dr_register_exit_event(event_exit);
    dr_register_bb_event(event_app_instruction);
}

static dr_emit_flags_t
event_app_instruction(__attribute__((unused)) void *drcontext, void *tag,
                      __attribute__((unused)) instrlist_t *bb,
                      __attribute__((unused)) bool for_trace,
                      __attribute__((unused)) bool translating) {
    app_pc start_pc = dr_fragment_app_pc(tag);
    module_data_t *mod = dr_lookup_module(start_pc);
    char addr_str[64];
    memset(addr_str, 0, 64); // ensure clean buffer

    if (mod != NULL) {
        int from_binary = 0;

        #ifdef ALL
            from_binary = 1;
        #else
            from_binary = mod->names.module_name == NULL;
        #endif

        if (from_binary) {
            #ifdef VERBOSE
                dr_snprintf(addr_str, sizeof(addr_str), "<%s> + %#lx\n", mod->names.file_name, start_pc);
            #else
                dr_snprintf(addr_str, sizeof(addr_str), "%#lx\n", start_pc);
            #endif
        }

        dr_write_file(log_file, addr_str, strlen(addr_str));
    }
    dr_free_module_data(mod);
    return DR_EMIT_DEFAULT;
}

static void event_exit(void) {
    dr_close_file(log_file);
}
