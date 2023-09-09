/**
 * recursive doubling algorithm by MPI_Send and MPI_Recv
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mpi.h>

#define NUM_LOOP 200000
#define DATA_SIZE 1 << 24

int alloc_memory(char **s_buf, char **r_buf, int size);
int touch_memory(char *s_buf, char *r_buf, int size);

int main(int argc, char *argv[]) {
    int myid, numprocs;
    int size = DATA_SIZE;
    char *s_buf, *r_buf;
    double t_start = 0.0, t_end = 0.0, t_elapsed = 0.0;
    int window_size = 64;

    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD, &myid);

    alloc_memory(&s_buf, &r_buf, size);

    for (int iter = 0; iter < NUM_LOOP; iter++) {
        touch_memory(s_buf, r_buf, size);

        // barrier
        MPI_Barrier(MPI_COMM_WORLD);
        t_start = MPI_Wtime();

        // if (my rank < np/2) send to my rank + np/2;
        // else recv from my rank - n/2
        if (myid < numprocs / 2) {

            // send data to myid + numprocs / 2
            MPI_Send(s_buf, size, MPI_CHAR, myid + numprocs / 2, 0, MPI_COMM_WORLD);

            // printf("%d -> %d, size: %d, time: %lf\n", myid, myid + numprocs / 2, size, t_elapsed);
        } else {
            // recv data from myid - numprocs / 2
            MPI_Recv(r_buf, size, MPI_CHAR, myid - numprocs / 2, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }

        // barrier
        MPI_Barrier(MPI_COMM_WORLD);
        t_end = MPI_Wtime();
        t_elapsed += t_end - t_start;

        if (iter % 1000 == 0 && myid == 0) {
            printf("%d -> %d, size: %d, time: %lf\n", myid, myid + numprocs / 2, size, t_elapsed);
        }
    }

    if (myid < numprocs / 2) {
        const double bw_mb = (double)NUM_LOOP * size * sizeof(char) / t_elapsed / 1e6;
        printf("%d -> %d, size: %d, elapsed: %lf, average time: %lf, bandwidth: %lf MB/sec\n", myid, myid + numprocs / 2, size, t_elapsed, t_elapsed / NUM_LOOP, bw_mb);
    }

    MPI_Finalize();
}

int alloc_memory(char **s_buf, char **r_buf, int size) {
    *s_buf = (char *)malloc(sizeof(char) * size);
    *r_buf = (char *)malloc(sizeof(char) * size);
    if (s_buf == NULL || r_buf == NULL) {
        printf("malloc failed\n");
        return 1;
    }
    return 0;
}

int touch_memory(char *s_buf, char *r_buf, int size) {
    memset(s_buf, 'a', size);
    memset(r_buf, 'b', size);
    return 0;
}
