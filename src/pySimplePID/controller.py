from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass
class PID:
    """Simple PID controller with internal elapsed-time tracking.

    ``kp`` is mandatory. ``ki`` and ``kd`` default to zero, which disables the
    integral and derivative components. Controller output is clamped to
    -100..100 by default so positive values can heat and negative values can
    cool. Elapsed time is measured internally between calls to ``update``.
    """

    kp: float
    ki: float = 0.0
    kd: float = 0.0
    target: float = 0.0
    output_min: float = -100.0
    output_max: float = 100.0
    time_function: Callable[[], float] = field(
        default=time.monotonic,
        repr=False,
        compare=False,
    )
    _integral: float = field(default=0.0, init=False, repr=False)
    _previous_error: float | None = field(default=None, init=False, repr=False)
    _previous_update_time: float = field(default=0.0, init=False, repr=False)
    _last_proportional: float = field(default=0.0, init=False, repr=False)
    _last_integral: float = field(default=0.0, init=False, repr=False)
    _last_derivative: float = field(default=0.0, init=False, repr=False)
    _last_output: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.output_min > self.output_max:
            raise ValueError("output_min must be less than or equal to output_max")
        self._previous_update_time = self.time_function()

    @property
    def integral(self) -> float:
        return self._integral

    @property
    def proportional_value(self) -> float:
        return self._last_proportional

    @property
    def integral_value(self) -> float:
        return self._last_integral

    @property
    def derivative_value(self) -> float:
        return self._last_derivative

    @property
    def output_value(self) -> float:
        return self._last_output

    def set_target(self, target: float) -> None:
        self.target = target

    def reset(self) -> None:
        self._integral = 0.0
        self._previous_error = None
        self._previous_update_time = self.time_function()
        self._last_proportional = 0.0
        self._last_integral = 0.0
        self._last_derivative = 0.0
        self._last_output = 0.0

    def update(self, current_value: float) -> float:
        now = self.time_function()
        elapsed_time = now - self._previous_update_time
        if elapsed_time < 0:
            raise ValueError("time_function must not go backwards")

        error = self.target - current_value

        proportional = self.kp * error

        derivative = 0.0
        if self.kd != 0 and self._previous_error is not None and elapsed_time > 0:
            derivative = self.kd * (error - self._previous_error) / elapsed_time

        integral_candidate = self._integral
        if self.ki != 0 and elapsed_time > 0:
            integral_candidate += error * elapsed_time

        output_unsat = (
            proportional
            + self.ki * integral_candidate
            + derivative
        )

        output = min(max(output_unsat, self.output_min), self.output_max)

        # Anti-windup: only accept the new integral if not saturated,
        # or if the error would drive the controller back out of saturation.
        saturated_high = output >= self.output_max
        saturated_low = output <= self.output_min

        if (
            output == output_unsat
            or (saturated_high and error < 0)
            or (saturated_low and error > 0)
        ):
            self._integral = integral_candidate

        self._last_proportional = proportional
        self._last_integral = self.ki * integral_candidate
        self._last_derivative = derivative
        self._last_output = output
        self._previous_error = error
        self._previous_update_time = now

        return output
