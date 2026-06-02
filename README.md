# pySimplePID

A small deterministic PID controller library for Python.

## Usage

```python
from pySimplePID import PID

pid = PID(kp=2.0, ki=0.1, target=22.0)

thermal_output = pid.update(current_value=20.5)
pid.set_target(24.0)
```

`kp` is required. `ki` and `kd` default to `0.0`; any component with a gain of
zero is disabled. Output is capped between `-100` and `100` by default, where
positive values heat and negative values cool.

Elapsed time is measured internally between calls to `update()`. Tests and
simulations can inject a custom clock with `time_function`.

## PID Output Limits for Heating and Cooling

The PID output sign is conventional:

```text
positive output -> heat
negative output -> cool
```

Use `output_min` and `output_max` to match the actuators available in your
system.

| System type | `output_min` | `output_max` | Meaning |
| --- | ---: | ---: | --- |
| Heating only | `0.0` | `100.0` | Output can only add heat |
| Cooling only | `-100.0` | `0.0` | Output can only remove heat |
| Heating and cooling | `-100.0` | `100.0` | Positive heats, negative cools |

### Heating Only

Use this when the system can add heat but cannot actively cool:

```python
pid = PID(
    kp=2.0,
    ki=0.1,
    target=22.0,
    output_min=0.0,
    output_max=100.0,
)
```

Output range:

```text
0% ... 100%
```

### Cooling Only

Use this when the system can remove heat but cannot actively heat, such as a
Peltier used only for cooling:

```python
pid = PID(
    kp=2.0,
    ki=0.1,
    target=5.0,
    output_min=-100.0,
    output_max=0.0,
)
```

Output range:

```text
-100% ... 0%
```

For a cooling actuator that expects a positive drive value, invert the sign:

```python
cooling_drive = max(0.0, -pid.update(current_temperature))
```

### Heating and Cooling

Use this when the system has both actuators, or one bidirectional actuator:

```python
pid = PID(
    kp=2.0,
    ki=0.1,
    target=22.0,
    output_min=-100.0,
    output_max=100.0,
)
```

Output range:

```text
-100% ... 100%
```

Then split the output by sign:

```python
output = pid.update(current_temperature)
heating_drive = max(0.0, output)
cooling_drive = max(0.0, -output)
```

## Temperature Simulation

The examples include a minimal first-order radiator model in
`examples/models.py`. It is intentionally not part of the library API:

```python
from models import TemperatureRadiator
from pySimplePID import PID

pid = PID(kp=30.0, ki=0.2, target=22.0)
radiator = TemperatureRadiator(
    initial_temperature=16.0,
    ambient_temperature=12.0,
    heat_capacity=120.0,
    heat_loss_coefficient=2.0,
)

thermal_output = pid.update(radiator.current_temperature)
temperature = radiator.step(thermal_output, dt=1.0)
```

The model uses:

```text
temperature += (thermal_power - heat_loss_coefficient * (temperature - ambient))
               / heat_capacity
               * dt
```

## Examples

```bash
PYTHONPATH=src python3 examples/basic_pid.py
PYTHONPATH=src python3 examples/temperature_radiator.py
```

The temperature example prints CSV-style data:

```text
time,temperature,target,thermal_output
```

There is also an optional Qt example with live charts and editable PID
parameters. Its PID interval control changes how often the controller is
sampled while the radiator model continues to run on a fixed fast timestep.
Heating and cooling power fields convert PID output percentage into watts:
for example, `10 %` output with `5 W` heating power applies `0.5 W`.

```bash
python3 -m pip install '.[gui]'
PYTHONPATH=src python3 examples/temperature_radiator_qt.py
```

The SiPM/Peltier Qt example uses a thin aluminium thermal mass, a small SiPM
heat load, ambient exchange, and Peltier cooling:

```bash
PYTHONPATH=src python3 examples/sipm_qt.py
```

## Tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
