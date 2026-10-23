part "heat_sink_base" {
    geometry: box(50, 30, 5)
    material: aluminum
    constraint stress {
        max_von_mises < 200 MPa
    }
}

part "mounting_pin" {
    geometry: cylinder (2, 10)
    material: copper
}

interface "MoS2_Al2O3_gate" {
    layers: [MoS2(5 nm), Al2O3(10 nm)]
    physics: coupled_poisson_schrodinger
    thermal: transient_heat_flux(1e6 W/cm2)
}