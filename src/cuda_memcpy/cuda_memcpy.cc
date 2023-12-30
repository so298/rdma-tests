/* an CUDA program that allocates a large amount of GPU memory 
    and move data back and forth between host and device.
    the size of the memory is customizable via a command line option */

#include <assert.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <cuda_runtime.h>

void cuda_kernel_checked_(const char * expr, const char * file, int line) {
  cudaError_t e = cudaGetLastError();
  if (e != cudaSuccess) {
    printf("%s:%d: error: %s %s\n", file, line, expr, cudaGetErrorString(e));
    exit(EXIT_FAILURE);
  }
}

#define cuda_kernel_checked(e) do { e; cuda_kernel_checked_(#e, __FILE__, __LINE__); } while(0)

/* a macro that executes cuda API call e, check if there is an error, and if there is,
    prints an error message and exit */

void cuda_api_checked_(cudaError_t e, const char * expr, const char * file, int line) {
  if (e != cudaSuccess) {
    printf("%s:%d: error: %s %s\n", file, line, expr, cudaGetErrorString(e));
    exit(EXIT_FAILURE);
  }
}

#define cuda_api_checked(e) cuda_api_checked_(e, #e, __FILE__, __LINE__)

void * cuda_malloc_checked(size_t size) {
  void * d;
  cuda_api_checked(cudaMalloc(&d, size));
  return d;
}

typedef struct {
  void * h;
  void * d;
  size_t size;
} dual_ptr_t;

dual_ptr_t alloc_dual(size_t size) {
  void * h = malloc(size);
  if (!h) { err(EXIT_FAILURE, "malloc"); }
  void * d = cuda_malloc_checked(size);
  dual_ptr_t ptr;
  ptr.h = h;
  ptr.d = d;
  ptr.size = size;
  return ptr;
}

void free_dual(dual_ptr_t ptr) {
  cuda_api_checked(cudaFree(ptr.d));
  free(ptr.h);
}

void to_host(dual_ptr_t ptr) {
  cuda_api_checked(cudaMemcpy(ptr.h, ptr.d, ptr.size, cudaMemcpyDeviceToHost));
}

void to_device(dual_ptr_t ptr) {
  cuda_api_checked(cudaMemcpy(ptr.d, ptr.h, ptr.size, cudaMemcpyHostToDevice));
}

__global__ void add_dev(dual_ptr_t a, unsigned char dx) {
  int tid = threadIdx.x + blockIdx.x * blockDim.x;
  size_t n = a.size;
  unsigned char * d = (unsigned char *)a.d;
  if (tid < n) {
    d[tid] += dx;
  }
}

void add(dual_ptr_t a, char dx) {
  int block_sz = 1024;
  int grid_sz = (a.size + block_sz - 1) / block_sz;
  // launch add kernel and check for errors
  cuda_kernel_checked((add_dev<<<grid_sz, block_sz>>>(a, dx)));
  cuda_api_checked(cudaDeviceSynchronize());
}

void init_array_random(dual_ptr_t a, long seed) {
  unsigned short rg[3] = {
    (unsigned short)((seed >>  0) & 0xFFFF),
    (unsigned short)((seed >> 16) & 0xFFFF),
    (unsigned short)((seed >> 32) & 0xFFFF)
  };
  long n = a.size;
  unsigned char * h = (unsigned char * )a.h;
  for (int i = 0; i < n; i++) {
    h[i] = nrand48(rg) % 256;
  }
}

void check(dual_ptr_t a, unsigned char dx, long seed) {
  unsigned short rg[3] = {
    (unsigned short)((seed >>  0) & 0xFFFF),
    (unsigned short)((seed >> 16) & 0xFFFF),
    (unsigned short)((seed >> 32) & 0xFFFF)
  };
  long n = a.size;
  unsigned char * h = (unsigned char * )a.h;
  for (int i = 0; i < n; i++) {
    unsigned char x = nrand48(rg) % 256;
    assert(h[i] == (unsigned char)(x + dx));
  }
}

long cur_time() {
  struct timespec ts[1];
  int e = clock_gettime(CLOCK_REALTIME, ts);
  if (e) err(EXIT_FAILURE, "clock_gettime");
  return ts->tv_sec * 1000000000L + ts->tv_nsec;
}

long show_time(long t0, long t1, const char * stmt) {
  printf("%12s : %f sec\n", stmt, (t1 - t0) * 1e-9);
  return t1 - t0;
}

#define time_it(e) ({ long t0 = cur_time(); e; long t1 = cur_time(); show_time(t0, t1, #e); })

int main(int argc, char ** argv) {
  int i = 1;
  long n    = (i < argc ? atol(argv[i]) : 1L << 20); i++;
  long m    = (i < argc ? atol(argv[i]) : 5);        i++;
  long seed = (i < argc ? atol(argv[i]) : 768);      i++;
  dual_ptr_t a = alloc_dual(n);
  unsigned char dx = 1;
  time_it(init_array_random(a, seed));
  for (int i = 0; i < m; i++) {
    long dt0 = time_it(to_device(a));
    printf("host -> dev %f GB/sec\n", n / (double)dt0);
    long dt1 = time_it(add(a, dx));
    long dt2 = time_it(to_host(a));
    printf("host <- dev %f GB/sec\n", n / (double)dt2);
  }
  time_it(check(a, dx * m, seed));
  printf("OK\n");
  return 0;
}
