from models import TemperatureRadiator
from pySimplePID import PID


class ManualClock:
    def __init__(self) -> None:
        self.current_time = 0.0

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def main() -> None:
    target_temperature = 22.0
    clock = ManualClock()
    pid = PID(
        kp=30.0,
        ki=0.2,
        kd=0.0,
        target=target_temperature,
        time_function=clock.now,
    )
    radiator = TemperatureRadiator(
        initial_temperature=16.0,
        ambient_temperature=12.0,
        heat_capacity=120.0,
        heat_loss_coefficient=2.0,
        max_power=100.0,
    )

    print("time,temperature,target,thermal_output")
    for second in range(180):
        clock.advance(1.0)
        thermal_output = pid.update(radiator.current_temperature)
        temperature = radiator.step(thermal_output, dt=1.0)
        print(
            f"{second},{temperature:.3f},{target_temperature:.3f},{thermal_output:.3f}"
        )


if __name__ == "__main__":
    main()
