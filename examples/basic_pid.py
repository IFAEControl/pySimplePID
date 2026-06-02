from pySimplePID import PID


class ManualClock:
    def __init__(self) -> None:
        self.current_time = 0.0

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


def main() -> None:
    # Use a custom clock so the example can simulate elapsed time without
    # waiting for real time to pass between PID updates.
    # for standard use in a real system, you can omit the time_function argument and it will default to using time.time()
    clock = ManualClock()
    pid = PID(kp=2.0, ki=0.1, kd=0.0, target=10.0, time_function=clock.now)

    for value in [6.0, 7.5, 8.5, 9.2, 9.8, 10.1]:
        clock.advance(1.0)
        output = pid.update(current_value=value)
        print(f"value={value:.2f}, output={output:.2f}")


if __name__ == "__main__":
    main()
