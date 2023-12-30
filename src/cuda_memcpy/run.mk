
gpus:=$(shell seq 0 7)
# ncpus:=10
# cpus:=$(shell dd if=/dev/urandom bs=2 count=$(ncpus) 2> /dev/null | od -t u2 -A n -w2 | awk '{print $$1 % 144}' | sort -n)
cpus:=$(shell seq 0 143)
sz:=$(shell echo $$((1 << 27)))
repeat:=10

targets:=$(foreach cpu,$(cpus),$(foreach gpu,$(gpus),output/out_$(cpu)_$(gpu).txt))

all : $(targets)

define run
output/out_$(cpu)_$(gpu).txt : output
	mpirun -np 1 ./cuda_memcpy.sh $(cpu) $(gpu) $(sz) $(repeat) > $$@
endef

output :
	mkdir -p output
$(foreach cpu,$(cpus),$(foreach gpu,$(gpus),$(eval $(call run))))

