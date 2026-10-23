# include <stdio.h>

// A simple explicit finite difference step for 2D heat diffusion.
void thermal_step_2d(
    const double* temp_in,
    double* temp_out,
    const double* alpha,
    size_t nx,
    size_t ny,
    double dt,
    double dx
) {
    for (size_t j = 1; j < ny - 1; ++j) {
        for (size_t i = 1; i < nx -1; ++i) {
            size_t idx = j * nx + i;
            double laplacian = (temp_in[idx - 1] + temp_in[idx + 1]
                                + temp_in[idx - nx] + temp_in[idx + nx]
                                - 4.0 * temp_in[idx]) / (dx * dx);
            temp_out[idx] = temp_in[idx] + dt * alpha[idx] * laplacian;
        }
    }
}