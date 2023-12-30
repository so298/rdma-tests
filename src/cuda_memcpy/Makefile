cc:=$(wildcard *.cc)
cu:=$(wildcard *.cu)
exe:=$(patsubst %.cc,%.exe,$(cc))
mpi_dir:=/usr/local/openmpi-4.1.5

all : $(exe)

$(exe) : %.exe : %.cc
	nvcc -I$(mpi_dir)/include -O3 -x cu $< -o $@ -L$(mpi_dir)/lib -lmpi


