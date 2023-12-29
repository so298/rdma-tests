/**
 * recursive doubling algorithm by MPI_Send and MPI_Recv
*/

#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <mpi.h>

#define NUM_LOOP 500
#define DATA_SIZE (1L << 30)

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

int main(int argc, char *argv[]) {
    int size = DATA_SIZE;

    MPI_Init(&argc, &argv);

    int myid = -1, numprocs = -1;
    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD, &myid);

    char *s_buf, *r_buf;
    alloc_memory(&s_buf, &r_buf, size);

    double dt_total = 0.0;
    for (int iter = 0; iter < NUM_LOOP; iter++) {
        touch_memory(s_buf, r_buf, size);

        // barrier
        MPI_Barrier(MPI_COMM_WORLD);
        double t_start = MPI_Wtime();

        // if (my rank < np/2) send to my rank + np/2;
        // else recv from my rank - n/2
        if (myid < numprocs / 2) {
          MPI_Status status;
          // send data to myid + numprocs / 2
          MPI_Send(s_buf, size, MPI_CHAR, myid + numprocs / 2, 0, MPI_COMM_WORLD);
          MPI_Recv(r_buf,    1, MPI_CHAR, myid + numprocs / 2, 0, MPI_COMM_WORLD, &status);
          assert(r_buf[0] == 'a');
          // printf("%d -> %d, size: %d, time: %lf\n", myid, myid + numprocs / 2, size, t_elapsed);
        } else {
          // recv data from myid - numprocs / 2
          MPI_Status status;
          MPI_Recv(r_buf, size, MPI_CHAR, myid - numprocs / 2, 0, MPI_COMM_WORLD, &status);
          assert(r_buf[0] == 'a');
          MPI_Send(s_buf,    1, MPI_CHAR, myid - numprocs / 2, 0, MPI_COMM_WORLD);
        }
        double t_end = MPI_Wtime();
        double dt = t_end - t_start;
        // barrier
        MPI_Barrier(MPI_COMM_WORLD);
        dt_total += dt;

        if (myid < numprocs / 2) {
            printf("%d -> %d, size: %d, dt: %lf, bandwidth: %lf MB/sec\n",
                   myid, myid + numprocs / 2, size, dt, size / dt * 1e-6);
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);
    if (myid < numprocs / 2) {
        const double bw_mb = (double)NUM_LOOP * size * sizeof(char) / dt_total * 1e-6;
        printf("%d -> %d, size: %d, total dt: %lf, average dt: %lf, bandwidth: %lf MB/sec\n", myid, myid + numprocs / 2, size, dt_total, dt_total / NUM_LOOP, bw_mb);
    }

    MPI_Finalize();
}

