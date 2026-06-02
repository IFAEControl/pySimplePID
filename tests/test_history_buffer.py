import sys
import unittest
from dataclasses import dataclass
from pathlib import Path


EXAMPLES_PATH = Path(__file__).resolve().parents[1] / "examples"
sys.path.insert(0, str(EXAMPLES_PATH))

from history_buffer import HistoryBuffer  # noqa: E402


@dataclass(frozen=True)
class Sample:
    time: float
    value: float


class HistoryBufferTests(unittest.TestCase):
    def test_history_is_bounded_and_chronological(self):
        history = HistoryBuffer(
            raw_limit=10,
            level_limit=10,
            chunk_size=5,
            max_levels=3,
        )

        for index in range(500):
            history.add(Sample(time=float(index), value=float(index)))

        points = history.visible_points(max_points=50)

        self.assertLessEqual(len(points), 50)
        self.assertGreater(points[-1].time, points[0].time)
        self.assertTrue(
            all(
                current.time <= next_point.time
                for current, next_point in zip(points, points[1:])
            )
        )

    def test_history_aggregates_numeric_fields(self):
        history = HistoryBuffer(raw_limit=2, level_limit=10, chunk_size=2)

        history.add(Sample(time=0.0, value=10.0))
        history.add(Sample(time=1.0, value=20.0))
        history.add(Sample(time=2.0, value=30.0))

        points = history.visible_points()

        self.assertEqual(points[0], Sample(time=0.5, value=15.0))
        self.assertEqual(points[-1], Sample(time=2.0, value=30.0))

    def test_visible_points_handles_small_limits(self):
        history = HistoryBuffer()
        history.add(Sample(time=0.0, value=1.0))
        history.add(Sample(time=1.0, value=2.0))

        self.assertEqual(history.visible_points(max_points=0), [])
        self.assertEqual(history.visible_points(max_points=1), [Sample(1.0, 2.0)])


if __name__ == "__main__":
    unittest.main()
