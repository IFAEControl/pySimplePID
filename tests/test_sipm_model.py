import unittest
import sys
from pathlib import Path


EXAMPLES_PATH = Path(__file__).resolve().parents[1] / "examples"
sys.path.insert(0, str(EXAMPLES_PATH))

from models import SiPMModel  # noqa: E402


class SiPMModelTests(unittest.TestCase):
    def test_default_heat_capacity_matches_small_aluminium_layer(self):
        model = SiPMModel()

        self.assertAlmostEqual(model.aluminium_mass, 0.00864)
        self.assertAlmostEqual(model.heat_capacity, 7.776)

    def test_sipm_heat_warms_layer_without_cooling_or_losses(self):
        model = SiPMModel(
            initial_temperature=25.0,
            ambient_temperature=25.0,
            sipm_heat_power=0.1,
            thermal_conductance_to_ambient=0.0,
            max_peltier_cooling_power=0.0,
        )

        self.assertGreater(model.step(peltier_cooling_power=0.0, dt=10.0), 25.0)

    def test_peltier_cools_layer(self):
        model = SiPMModel(
            initial_temperature=25.0,
            ambient_temperature=25.0,
            sipm_heat_power=0.0,
            thermal_conductance_to_ambient=0.0,
            max_peltier_cooling_power=5.0,
        )

        self.assertLess(model.step(peltier_cooling_power=1.0, dt=1.0), 25.0)

    def test_ambient_coupling_pulls_temperature_toward_ambient(self):
        cold_model = SiPMModel(
            initial_temperature=20.0,
            ambient_temperature=25.0,
            sipm_heat_power=0.0,
            thermal_conductance_to_ambient=0.2,
        )
        hot_model = SiPMModel(
            initial_temperature=30.0,
            ambient_temperature=25.0,
            sipm_heat_power=0.0,
            thermal_conductance_to_ambient=0.2,
        )

        self.assertGreater(cold_model.step(peltier_cooling_power=0.0), 20.0)
        self.assertLess(hot_model.step(peltier_cooling_power=0.0), 30.0)

    def test_peltier_power_is_capped(self):
        model = SiPMModel(
            initial_temperature=25.0,
            ambient_temperature=25.0,
            aluminium_area=1.0,
            aluminium_thickness=1.0,
            aluminium_density=1.0,
            aluminium_specific_heat=1.0,
            sipm_heat_power=0.0,
            thermal_conductance_to_ambient=0.0,
            max_peltier_cooling_power=2.0,
        )

        self.assertEqual(model.step(peltier_cooling_power=10.0), 23.0)

    def test_dt_must_be_positive(self):
        model = SiPMModel()

        with self.assertRaises(ValueError):
            model.step(peltier_cooling_power=0.0, dt=0.0)

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            SiPMModel(aluminium_thickness=0.0)


if __name__ == "__main__":
    unittest.main()
