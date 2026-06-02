import unittest
import sys
from pathlib import Path


EXAMPLES_PATH = Path(__file__).resolve().parents[1] / "examples"
sys.path.insert(0, str(EXAMPLES_PATH))

from models import TemperatureRadiator  # noqa: E402


class TemperatureRadiatorTests(unittest.TestCase):
    def test_heats_up_when_power_is_applied(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.1,
        )

        self.assertGreater(radiator.step(thermal_power=50.0), 20.0)

    def test_cools_down_when_negative_power_is_applied(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.1,
        )

        self.assertLess(radiator.step(thermal_power=-50.0), 20.0)

    def test_cools_toward_ambient_without_power(self):
        radiator = TemperatureRadiator(
            initial_temperature=30.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=1.0,
        )

        self.assertLess(radiator.step(thermal_power=0.0), 30.0)

    def test_thermal_power_is_capped_symmetrically(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.0,
            max_power=25.0,
        )

        self.assertEqual(radiator.step(thermal_power=100.0), 22.5)
        radiator.reset()
        self.assertEqual(radiator.step(thermal_power=-100.0), 17.5)

    def test_older_heater_power_names_still_work(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.0,
            max_heater_power=25.0,
        )

        self.assertEqual(radiator.step(heater_power=100.0), 22.5)

    def test_reset_restores_initial_temperature(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.0,
        )

        radiator.step(thermal_power=50.0)
        radiator.reset()

        self.assertEqual(radiator.current_temperature, 20.0)

    def test_dt_must_be_positive(self):
        radiator = TemperatureRadiator(
            initial_temperature=20.0,
            ambient_temperature=20.0,
            heat_capacity=10.0,
            heat_loss_coefficient=0.0,
        )

        with self.assertRaises(ValueError):
            radiator.step(thermal_power=10.0, dt=0.0)


if __name__ == "__main__":
    unittest.main()
