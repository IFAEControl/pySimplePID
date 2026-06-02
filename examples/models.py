from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TemperatureRadiator:
    """First-order temperature model for heating and cooling simulations."""

    initial_temperature: float
    ambient_temperature: float
    heat_capacity: float
    heat_loss_coefficient: float
    max_power: float = 100.0
    max_heater_power: float | None = None
    current_temperature: float = field(init=False)

    def __post_init__(self) -> None:
        if self.max_heater_power is not None:
            self.max_power = self.max_heater_power
        if self.heat_capacity <= 0:
            raise ValueError("heat_capacity must be greater than zero")
        if self.heat_loss_coefficient < 0:
            raise ValueError("heat_loss_coefficient must be greater than or equal to zero")
        if self.max_power < 0:
            raise ValueError("max_power must be greater than or equal to zero")
        self.current_temperature = self.initial_temperature

    def reset(self) -> None:
        self.current_temperature = self.initial_temperature

    def step(
        self,
        thermal_power: float | None = None,
        dt: float = 1.0,
        *,
        heater_power: float | None = None,
    ) -> float:
        if dt <= 0:
            raise ValueError("dt must be greater than zero")
        if thermal_power is None and heater_power is None:
            raise TypeError("thermal_power is required")
        if thermal_power is not None and heater_power is not None:
            raise ValueError("use either thermal_power or heater_power, not both")
        if thermal_power is None:
            thermal_power = heater_power

        applied_power = min(max(thermal_power, -self.max_power), self.max_power)
        heat_loss = self.heat_loss_coefficient * (
            self.current_temperature - self.ambient_temperature
        )
        net_power = applied_power - heat_loss
        self.current_temperature += (net_power / self.heat_capacity) * dt
        return self.current_temperature


@dataclass
class SiPMModel:
    """Lumped SiPM-on-aluminium thermal model."""

    initial_temperature: float = 25.0
    ambient_temperature: float = 25.0
    aluminium_area: float = 0.0016
    aluminium_thickness: float = 0.002
    aluminium_density: float = 2700.0
    aluminium_specific_heat: float = 900.0
    sipm_heat_power: float = 0.03
    thermal_conductance_to_ambient: float = 0.15
    max_peltier_cooling_power: float = 5.0
    current_temperature: float = field(init=False)

    def __post_init__(self) -> None:
        self._validate()
        self.current_temperature = self.initial_temperature

    @property
    def aluminium_mass(self) -> float:
        return self.aluminium_area * self.aluminium_thickness * self.aluminium_density

    @property
    def heat_capacity(self) -> float:
        return self.aluminium_mass * self.aluminium_specific_heat

    def reset(self) -> None:
        self.current_temperature = self.initial_temperature

    def step(self, peltier_cooling_power: float, dt: float = 1.0) -> float:
        if dt <= 0:
            raise ValueError("dt must be greater than zero")
        self._validate()

        cooling_power = min(
            max(peltier_cooling_power, 0.0),
            self.max_peltier_cooling_power,
        )
        ambient_heat_flow = self.thermal_conductance_to_ambient * (
            self.ambient_temperature - self.current_temperature
        )
        net_power = self.sipm_heat_power + ambient_heat_flow - cooling_power
        self.current_temperature += (net_power / self.heat_capacity) * dt
        return self.current_temperature

    def _validate(self) -> None:
        if self.aluminium_area <= 0:
            raise ValueError("aluminium_area must be greater than zero")
        if self.aluminium_thickness <= 0:
            raise ValueError("aluminium_thickness must be greater than zero")
        if self.aluminium_density <= 0:
            raise ValueError("aluminium_density must be greater than zero")
        if self.aluminium_specific_heat <= 0:
            raise ValueError("aluminium_specific_heat must be greater than zero")
        if self.sipm_heat_power < 0:
            raise ValueError("sipm_heat_power must be greater than or equal to zero")
        if self.thermal_conductance_to_ambient < 0:
            raise ValueError(
                "thermal_conductance_to_ambient must be greater than or equal to zero"
            )
        if self.max_peltier_cooling_power < 0:
            raise ValueError(
                "max_peltier_cooling_power must be greater than or equal to zero"
            )
