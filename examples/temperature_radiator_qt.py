from __future__ import annotations

import sys
from dataclasses import dataclass

from history_buffer import HistoryBuffer
from models import TemperatureRadiator
from pySimplePID import PID

try:
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
    from PySide6.QtGui import QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QApplication,
        QDoubleSpinBox,
        QFormLayout,
        QFrame,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
except ModuleNotFoundError as exc:
    raise SystemExit(
        "PySide6 is required for this example. Install it with: "
        "python3 -m pip install '.[gui]'"
    ) from exc


@dataclass(frozen=True)
class Sample:
    time: float
    temperature: float
    target: float
    ambient_temperature: float
    error: float
    proportional: float
    integral: float
    derivative: float
    output: float
    thermal_output: float


class ManualClock:
    def __init__(self) -> None:
        self.current_time = 0.0

    def now(self) -> float:
        return self.current_time

    def advance(self, seconds: float) -> None:
        self.current_time += seconds


class SimulationChart(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.samples: list[Sample] = []
        self.setMinimumSize(760, 420)

    def set_samples(self, samples: list[Sample]) -> None:
        self.samples = samples
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#fafafa"))

        bounds = self.rect().adjusted(14, 14, -14, -14)
        gap = 12
        available_height = bounds.height() - 2 * gap
        system_rect = QRectF(
            bounds.left(),
            bounds.top(),
            bounds.width(),
            available_height * 0.70,
        )
        error_rect = QRectF(
            bounds.left(),
            system_rect.bottom() + gap,
            bounds.width(),
            available_height * 0.10,
        )
        pid_rect = QRectF(
            bounds.left(),
            error_rect.bottom() + gap,
            bounds.width(),
            available_height * 0.20,
        )
        time_min, time_max = self._time_range()

        self._draw_system_panel(painter, system_rect, time_min, time_max)
        self._draw_error_panel(painter, error_rect, time_min, time_max)
        self._draw_pid_panel(painter, pid_rect, time_min, time_max)

    def _draw_system_panel(
        self,
        painter: QPainter,
        rect: QRectF,
        time_min: float,
        time_max: float,
    ) -> None:
        values = (
            [sample.temperature for sample in self.samples]
            + [sample.target for sample in self.samples]
            + [sample.ambient_temperature for sample in self.samples]
        )
        min_value, max_value = self._data_range(values, fallback=(0.0, 1.0))

        self._draw_panel(
            painter,
            rect,
            "System",
            f"{min_value:.1f} C",
            f"{max_value:.1f} C",
            time_min,
            time_max,
            show_time_labels=False,
        )
        self._draw_line(
            painter,
            rect,
            [sample.temperature for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#1f77b4"),
        )
        self._draw_line(
            painter,
            rect,
            [sample.target for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#d62728"),
        )
        self._draw_line(
            painter,
            rect,
            [sample.ambient_temperature for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#777777"),
        )
        self._draw_legend(
            painter,
            rect,
            [
                ("temperature", QColor("#1f77b4")),
                ("target", QColor("#d62728")),
                ("ambient", QColor("#777777")),
            ],
        )

    def _draw_error_panel(
        self,
        painter: QPainter,
        rect: QRectF,
        time_min: float,
        time_max: float,
    ) -> None:
        values = [sample.error for sample in self.samples]
        min_value, max_value = self._data_range(values, fallback=(-1.0, 1.0))

        self._draw_panel(
            painter,
            rect,
            "Error",
            f"{min_value:.1f} C",
            f"{max_value:.1f} C",
            time_min,
            time_max,
            show_time_labels=False,
        )
        self._draw_line(
            painter,
            rect,
            values,
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#ff7f0e"),
        )

    def _draw_pid_panel(
        self,
        painter: QPainter,
        rect: QRectF,
        time_min: float,
        time_max: float,
    ) -> None:
        values = (
            [sample.proportional for sample in self.samples]
            + [sample.integral for sample in self.samples]
            + [sample.derivative for sample in self.samples]
            + [sample.output for sample in self.samples]
        )
        min_value, max_value = self._data_range(values, fallback=(-1.0, 1.0))

        self._draw_panel(
            painter,
            rect,
            "PID",
            f"{min_value:.1f} %",
            f"{max_value:.1f} %",
            time_min,
            time_max,
            show_time_labels=True,
        )
        self._draw_line(
            painter,
            rect,
            [sample.proportional for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#9467bd"),
        )
        self._draw_line(
            painter,
            rect,
            [sample.integral for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#8c564b"),
        )
        self._draw_line(
            painter,
            rect,
            [sample.derivative for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#17becf"),
        )
        self._draw_line(
            painter,
            rect,
            [sample.output for sample in self.samples],
            min_value,
            max_value,
            time_min,
            time_max,
            QColor("#2ca02c"),
        )
        self._draw_legend(
            painter,
            rect,
            [
                ("P", QColor("#9467bd")),
                ("I", QColor("#8c564b")),
                ("D", QColor("#17becf")),
                ("output", QColor("#2ca02c")),
            ],
        )

    def _draw_panel(
        self,
        painter: QPainter,
        rect: QRectF,
        title: str,
        low_label: str,
        high_label: str,
        time_min: float,
        time_max: float,
        show_time_labels: bool,
    ) -> None:
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.setBrush(QColor("#ffffff"))
        painter.drawRect(rect)

        painter.setPen(QPen(QColor("#eeeeee"), 1))
        plot_rect = self._plot_rect(rect)
        for index in range(1, 4):
            y = plot_rect.top() + plot_rect.height() * index / 4
            painter.drawLine(
                QPointF(plot_rect.left(), y),
                QPointF(plot_rect.right(), y),
            )
        for index in range(1, 5):
            x = plot_rect.left() + plot_rect.width() * index / 5
            painter.drawLine(
                QPointF(x, plot_rect.top()),
                QPointF(x, plot_rect.bottom()),
            )

        label_rect = rect.adjusted(8, 6, -8, -6)
        value_label_rect = rect.adjusted(
            8,
            6,
            -8,
            -24 if show_time_labels else -6,
        )
        painter.setPen(QColor("#333333"))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignTop, title)
        painter.setPen(QColor("#666666"))
        painter.drawText(
            value_label_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            high_label,
        )
        painter.drawText(
            value_label_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
            low_label,
        )
        if show_time_labels:
            time_label_rect = QRectF(
                plot_rect.left(),
                rect.bottom() - 20,
                plot_rect.width(),
                16,
            )
            painter.drawText(
                time_label_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                f"{time_min:.1f} s",
            )
            painter.drawText(
                time_label_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                "time",
            )
            painter.drawText(
                time_label_rect,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                f"{time_max:.1f} s",
            )

    def _draw_line(
        self,
        painter: QPainter,
        rect: QRectF,
        values: list[float],
        min_value: float,
        max_value: float,
        time_min: float,
        time_max: float,
        color: QColor,
    ) -> None:
        if len(values) < 2:
            return

        times = [sample.time for sample in self.samples]
        plot_rect = self._plot_rect(rect)
        scale = max_value - min_value
        time_scale = time_max - time_min
        points = []
        for sample_time, value in zip(times, values):
            x = (
                plot_rect.left()
                + plot_rect.width() * (sample_time - time_min) / time_scale
            )
            y = plot_rect.bottom() - plot_rect.height() * (value - min_value) / scale
            points.append(QPointF(x, y))

        painter.setPen(QPen(color, 2))
        for start, end in zip(points, points[1:]):
            painter.drawLine(start, end)

    def _draw_legend(
        self,
        painter: QPainter,
        rect: QRectF,
        entries: list[tuple[str, QColor]],
    ) -> None:
        x = rect.left() + 120
        y = rect.top() + 15
        for label, color in entries:
            painter.setPen(QPen(color, 3))
            painter.drawLine(QPointF(x, y), QPointF(x + 22, y))
            painter.setPen(QColor("#333333"))
            painter.drawText(QPointF(x + 30, y + 5), label)
            x += 130

    @staticmethod
    def _data_range(
        values: list[float],
        fallback: tuple[float, float],
    ) -> tuple[float, float]:
        if not values:
            return fallback

        min_value = min(values)
        max_value = max(values)
        if min_value == max_value:
            padding = max(abs(min_value) * 0.05, 1.0)
            return min_value - padding, max_value + padding

        padding = (max_value - min_value) * 0.05
        return min_value - padding, max_value + padding

    def _time_range(self) -> tuple[float, float]:
        if len(self.samples) < 2:
            return 0.0, 1.0
        time_min = self.samples[0].time
        time_max = self.samples[-1].time
        if time_max <= time_min:
            return time_min, time_min + 1.0
        return time_min, time_max

    @staticmethod
    def _plot_rect(rect: QRectF) -> QRectF:
        if rect.height() < 90:
            return rect.adjusted(54, 18, -58, -18)
        return rect.adjusted(54, 28, -58, -28)


class ValueCard(QFrame):
    def __init__(self, title: str) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            ValueCard {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
            }
            """
        )
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 11px; color: #666666;")
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(
            "font-size: 24px; font-weight: 600; color: #222222;"
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        self.setLayout(layout)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("pySimplePID temperature radiator")

        self.pid_clock = ManualClock()
        self.pid = PID(
            kp=30.0,
            ki=0.2,
            kd=0.0,
            target=22.0,
            time_function=self.pid_clock.now,
        )
        self.radiator = TemperatureRadiator(
            initial_temperature=16.0,
            ambient_temperature=12.0,
            heat_capacity=120.0,
            heat_loss_coefficient=2.0,
            max_power=100.0,
        )
        self.history = HistoryBuffer()
        self.time = 0.0
        self.model_dt = 0.1
        self.pid_elapsed = 0.0
        self.current_thermal_output = 0.0
        self.current_applied_power = 0.0

        self.chart = SimulationChart()
        self.temperature_card = ValueCard("System temperature")
        self.pid_output_card = ValueCard("PID output")
        self.applied_power_card = ValueCard("Applied power")
        self.error_card = ValueCard("Temp error")
        self.target_input = self._spin_box(0.0, 60.0, self.pid.target, 0.1)
        self.ambient_input = self._spin_box(
            -50.0,
            80.0,
            self.radiator.ambient_temperature,
            0.1,
        )
        self.heating_power_input = self._spin_box(0.0, 10000.0, 100.0, 1.0)
        self.cooling_power_input = self._spin_box(0.0, 10000.0, 100.0, 1.0)
        self.kp_input = self._spin_box(0.0, 200.0, self.pid.kp, 0.1)
        self.ki_input = self._spin_box(0.0, 20.0, self.pid.ki, 0.01)
        self.kd_input = self._spin_box(0.0, 300.0, self.pid.kd, 0.1)
        self.pid_interval_input = self._spin_box(0.1, 30.0, 1.0, 0.1)
        self.pid_elapsed = self.pid_interval_input.value()

        controls = QFormLayout()
        controls.addRow("Target", self.target_input)
        controls.addRow("Ambient", self.ambient_input)
        controls.addRow("Heating power (W)", self.heating_power_input)
        controls.addRow("Cooling power (W)", self.cooling_power_input)
        controls.addRow("Kp", self.kp_input)
        controls.addRow("Ki", self.ki_input)
        controls.addRow("Kd", self.kd_input)
        controls.addRow("PID interval (s)", self.pid_interval_input)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset)

        side_panel = QVBoxLayout()
        side_panel.addLayout(controls)
        side_panel.addSpacing(12)
        side_panel.addWidget(reset_button)
        side_panel.addSpacing(12)
        side_panel.addWidget(self.temperature_card)
        side_panel.addWidget(self.pid_output_card)
        side_panel.addWidget(self.applied_power_card)
        side_panel.addWidget(self.error_card)
        side_panel.addStretch()

        layout = QHBoxLayout()
        layout.addWidget(self.chart, 1)
        layout.addLayout(side_panel)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.target_input.valueChanged.connect(self._update_parameters)
        self.ambient_input.valueChanged.connect(self._update_parameters)
        self.heating_power_input.valueChanged.connect(self._update_parameters)
        self.cooling_power_input.valueChanged.connect(self._update_parameters)
        self.kp_input.valueChanged.connect(self._update_parameters)
        self.ki_input.valueChanged.connect(self._update_parameters)
        self.kd_input.valueChanged.connect(self._update_parameters)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.step)
        self.timer.start(50)

        self.step()

    def step(self) -> None:
        self._update_parameters()
        pid_interval = self.pid_interval_input.value()

        self.pid_clock.advance(self.model_dt)
        self.pid_elapsed += self.model_dt
        if self.pid_elapsed >= pid_interval:
            self.current_thermal_output = self.pid.update(
                self.radiator.current_temperature,
            )
            self.pid_elapsed = 0.0

        self.current_applied_power = self._applied_power(
            output_percent=self.current_thermal_output,
            heating_power=self.heating_power_input.value(),
            cooling_power=self.cooling_power_input.value(),
        )
        temperature = self.radiator.step(
            self.current_applied_power,
            dt=self.model_dt,
        )
        self.history.add(
            Sample(
                time=self.time,
                temperature=temperature,
                target=self.pid.target,
                ambient_temperature=self.radiator.ambient_temperature,
                error=self.pid.target - temperature,
                proportional=self.pid.proportional_value,
                integral=self.pid.integral_value,
                derivative=self.pid.derivative_value,
                output=self.pid.output_value,
                thermal_output=self.current_thermal_output,
            )
        )
        self.time += self.model_dt

        error = self.pid.target - temperature
        self.temperature_card.set_value(f"{temperature:.2f} C")
        self.pid_output_card.set_value(f"{self.current_thermal_output:.1f} %")
        self.applied_power_card.set_value(f"{self.current_applied_power:.2f} W")
        self.error_card.set_value(f"{error:.2f} C")
        self.chart.set_samples(self.history.visible_points())

    def reset(self) -> None:
        self.radiator.reset()
        self.history.clear()
        self.time = 0.0
        self.pid_clock.current_time = 0.0
        self.pid.reset()
        self.pid_elapsed = self.pid_interval_input.value()
        self.current_thermal_output = 0.0
        self.current_applied_power = 0.0
        self.temperature_card.set_value(
            f"{self.radiator.current_temperature:.2f} C"
        )
        self.pid_output_card.set_value("0.0 %")
        self.applied_power_card.set_value("0.00 W")
        reset_error = self.pid.target - self.radiator.current_temperature
        self.error_card.set_value(f"{reset_error:.2f} C")
        self.chart.set_samples([])

    def _update_parameters(self) -> None:
        self.pid.set_target(self.target_input.value())
        self.pid.kp = self.kp_input.value()
        self.pid.ki = self.ki_input.value()
        self.pid.kd = self.kd_input.value()
        self.radiator.ambient_temperature = self.ambient_input.value()
        self.radiator.max_power = max(
            self.heating_power_input.value(),
            self.cooling_power_input.value(),
        )

    @staticmethod
    def _applied_power(
        output_percent: float,
        heating_power: float,
        cooling_power: float,
    ) -> float:
        if output_percent >= 0:
            return output_percent * heating_power / 100.0
        return output_percent * cooling_power / 100.0

    @staticmethod
    def _spin_box(
        minimum: float,
        maximum: float,
        value: float,
        step: float,
    ) -> QDoubleSpinBox:
        spin_box = QDoubleSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setValue(value)
        spin_box.setSingleStep(step)
        spin_box.setDecimals(2)
        return spin_box


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1040, 520)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
