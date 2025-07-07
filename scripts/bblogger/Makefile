# Configurable variables (can be overridden from the command line or in config.mk)
# DRIO_INC: Directory for DRIO include files (default: ../drio-10/include)
# DRIO_LIB: Directory for DRIO library files (default: ../drio-10/lib64)
# CC: The C compiler to use (default: gcc)
# ALL: Set to enable additional compilation flags (-DVERBOSE -DFULL)

# Change these
DRIO_INC ?= ./drio-11/include
DRIO_LIB ?= ./drio-11/lib64

CC     = gcc
CFLAGS = -Wall -Wextra -shared -fPIC -DLINUX -DX86_64
ifdef FULL
    CFLAGS += -DVERBOSE -DALL
endif

all: bblogger.so

bblogger.so: bblogger.c clean
	$(CC) $(CFLAGS) -o $@ $< -I $(DRIO_INC) -L $(DRIO_LIB)

clean:
	@rm -f bblogger.so

# Help target to explain usage
help:
	@echo "Makefile for building bblogger.so"
	@echo "Usage:"
	@echo "  make [target] [VARIABLE=value]"
	@echo ""
	@echo "Targets:"
	@echo "  all       Build the shared object"
	@echo "  clean     Remove built files"
	@echo "  help      Display this help message"
	@echo ""
	@echo "Configurable variables:"
	@echo "  DRIO_INC  Directory for DRIO include files (default: ../drio-10/include)"
	@echo "  DRIO_LIB  Directory for DRIO library files (default: ../drio-10/lib64)"
	@echo "  CC        C compiler (default: gcc)"
	@echo "  ALL       Set to enable additional compilation flags (-DVERBOSE -DFULL)"

.PHONY: all clean help
