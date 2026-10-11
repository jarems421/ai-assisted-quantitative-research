from datetime import datetime, timezone
import unittest

from src.research.custom_exp002 import visible_value


class DisclosedVisibilityTests(unittest.TestCase):
    def test_backdated_observation_does_not_enter_before_publication(self):
        points=[dict(timestamp="2015-02-16T18:00:00Z",availableAt="2015-02-17T15:00:00Z",value=6)]
        self.assertIsNone(visible_value(points,datetime(2015,2,17,14,30,tzinfo=timezone.utc)))
        self.assertEqual(visible_value(points,datetime(2015,2,17,15,tzinfo=timezone.utc)),6)

    def test_future_prefix_and_ambiguous_points(self):
        point=dict(timestamp="2015-01-01T00:00:00Z",availableAt="2015-01-01T00:00:00Z",value=1)
        future=dict(timestamp="2016-01-01T00:00:00Z",availableAt="2016-01-01T00:00:00Z",value=9)
        at=datetime(2015,1,2,tzinfo=timezone.utc)
        self.assertEqual(visible_value([point,future],at),1)
        with self.assertRaises(ValueError):visible_value([point,dict(point,value=2)],at)

    def test_weekend_cutoff_and_delayed_observation(self):
        points=[dict(timestamp="2016-01-09T17:00:00Z",availableAt="2016-01-09T17:00:00Z",value=3),
                dict(timestamp="2016-01-11T01:30:00Z",availableAt="2016-01-11T03:00:00Z",value=4)]
        self.assertEqual(visible_value(points,datetime(2016,1,11,2,tzinfo=timezone.utc)),3)
        self.assertEqual(visible_value(points,datetime(2016,1,11,14,30,tzinfo=timezone.utc)),4)
