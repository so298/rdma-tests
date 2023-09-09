MPICC ?= mpicc
MPICXX ?= mpicxx

CC = ${MPICC}

MPI_HOME ?= /usr/local/openmpi-4.1.5/
CFLAGS += -I${MPI_HOME}/include
LDFLAGS += -L${MPI_HOME}/lib

all: exe/main

exe/main: src/main.o
	mkdir -p exe
	${MPICC} -o $@ $^

src/main.o: src/main.c

.PHONY: clean
clean:
	rm -f src/*.o exe/main