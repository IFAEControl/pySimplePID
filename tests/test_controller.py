import unittest

from pySimplePID import PID


class ManualClock:
    def __init__(self) -> None:
        self.current_time = 0.0

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


class PIDTests(unittest.TestCase):
    def test_proportional_output_uses_target_error(self):
        pid = PID(kp=2.0, target=10.0)

        self.assertEqual(pid.update(current_value=7.0), 6.0)

    def test_ki_defaults_to_disabled(self):
        pid = PID(kp=0.0, target=10.0)

        pid.update(current_value=8.0)
        pid.update(current_value=8.0)

        self.assertEqual(pid.integral, 0.0)

    def test_integral_component_accumulates_when_enabled(self):
        clock = ManualClock()
        pid = PID(kp=0.0, ki=0.5, target=10.0, time_function=clock.now)

        clock.advance(2.0)
        self.assertEqual(pid.update(current_value=8.0), 2.0)
        clock.advance(2.0)
        self.assertEqual(pid.update(current_value=8.0), 4.0)

    def test_derivative_component_reacts_to_error_change(self):
        clock = ManualClock()
        pid = PID(kp=0.0, kd=1.5, target=10.0, time_function=clock.now)

        clock.advance(1.0)
        self.assertEqual(pid.update(current_value=8.0), 0.0)
        clock.advance(1.0)
        self.assertEqual(pid.update(current_value=9.0), -1.5)
        clock.advance(1.0)
        self.assertEqual(pid.update(current_value=7.0), 3.0)

    def test_last_pid_terms_are_available_after_update(self):
        clock = ManualClock()
        pid = PID(kp=2.0, ki=0.5, kd=1.5, target=10.0, time_function=clock.now)

        clock.advance(2.0)
        self.assertEqual(pid.update(current_value=8.0), 6.0)
        self.assertEqual(pid.proportional_value, 4.0)
        self.assertEqual(pid.integral_value, 2.0)
        self.assertEqual(pid.derivative_value, 0.0)
        self.assertEqual(pid.output_value, 6.0)

    def test_output_is_capped_between_minus_one_hundred_and_one_hundred(self):
        high_pid = PID(kp=100.0, target=10.0)
        low_pid = PID(kp=100.0, target=0.0)

        self.assertEqual(high_pid.update(current_value=0.0), 100.0)
        self.assertEqual(low_pid.update(current_value=10.0), -100.0)

    def test_output_limits_can_be_restricted_to_heating_only(self):
        pid = PID(kp=100.0, target=0.0, output_min=0.0)

        self.assertEqual(pid.update(current_value=10.0), 0.0)

    def test_target_can_be_updated(self):
        pid = PID(kp=2.0, target=10.0)

        self.assertEqual(pid.update(current_value=8.0), 4.0)
        pid.set_target(12.0)

        self.assertEqual(pid.update(current_value=8.0), 8.0)

    def test_reset_clears_state(self):
        clock = ManualClock()
        pid = PID(kp=0.0, ki=1.0, kd=1.0, target=10.0, time_function=clock.now)

        clock.advance(1.0)
        pid.update(current_value=8.0)
        clock.advance(1.0)
        pid.update(current_value=9.0)
        pid.reset()
        clock.advance(1.0)

        self.assertEqual(pid.integral, 0.0)
        self.assertEqual(pid.update(current_value=9.0), 1.0)

    def test_clock_must_not_go_backwards(self):
        clock = ManualClock()
        pid = PID(kp=1.0, time_function=clock.now)

        clock.advance(-1.0)
        with self.assertRaises(ValueError):
            pid.update(current_value=0.0)


if __name__ == "__main__":
    unittest.main()
