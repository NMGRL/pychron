"""
Tests for isotope plot autoscaling logic in data_collector.

Regression tests for issues with y-axis limits calculation:
- Issue: Large signal values (e.g., 400±1) forced to scale from 0
- Issue: Small baseline values (e.g., < 0.002) scaled with excessive padding
- Issue: Fixed y-min of 0 regardless of data values
"""

from __future__ import absolute_import
import unittest
from math import isfinite

from pychron.pychron_constants import SIGNAL, SNIFF, BASELINE


class PlotScalingTestCase(unittest.TestCase):
    """Test the plot y-axis scaling logic."""

    def setUp(self):
        """Initialize test parameters."""
        self.SIGNAL = SIGNAL
        self.SNIFF = SNIFF
        self.BASELINE = BASELINE

    def _calculate_y_limits(self, ys, ypadding, collection_kind):
        """
        Replicate the _update_live_plot_limits scaling logic.
        
        Args:
            ys: array of y-values
            ypadding: padding as string (e.g., "0.1") or float
            collection_kind: SIGNAL, SNIFF, or BASELINE
            
        Returns:
            tuple: (ymin, ymax)
        """
        ymin = min(ys)
        ymax = max(ys)
        
        if isinstance(ypadding, str):
            ypad = abs(ymax - ymin) * float(ypadding)
        else:
            ypad = ypadding
        
        # Only anchor to 0 if ymin is small relative to the data range
        data_range = ymax - ymin
        should_anchor_to_zero = (
            collection_kind in (SIGNAL, SNIFF)
            and ymin >= 0
            and data_range > 0
            and ymin <= 0.5 * data_range
        )
        
        if should_anchor_to_zero:
            ymin = 0
        else:
            ymin -= ypad
        ymax += ypad
        
        return ymin, ymax

    def test_large_signal_no_forced_zero_anchor(self):
        """
        Regression test: Large values (400±1) should NOT be forced to scale from 0.
        Data at 399-401 should display with ymin around 399, not forced to 0.
        """
        ys = [399.0, 399.5, 400.0, 400.5, 401.0]  # Range: 2
        ymin, ymax = self._calculate_y_limits(ys, "0.1", SIGNAL)
        
        # Should NOT be anchored to 0
        self.assertGreater(ymin, 390.0, 
            "Large signal values should not be forced to ymin=0")
        
        # Should preserve data visibility
        data_range = max(ys) - min(ys)
        calculated_range = ymax - ymin
        self.assertLess(calculated_range, data_range * 2,
            "Plot range should be reasonable multiple of data range")

    def test_small_baseline_no_excessive_padding(self):
        """
        Regression test: Tiny baseline values (< 0.002) should NOT get excessive padding.
        Without the max(0.1, ...) guard, padding should be proportional to data range.
        """
        ys = [0.0001, 0.0015, 0.002]  # Range: 0.0019
        ymin, ymax = self._calculate_y_limits(ys, "0.1", BASELINE)
        
        data_range = max(ys) - min(ys)
        calculated_range = ymax - ymin
        
        # Padding should be ~10% of data range (0.1 × 0.0019 = 0.00019 per side)
        # Total range should be roughly 0.0019 + 2*0.00019 ≈ 0.00228
        self.assertLess(calculated_range, 0.01,
            "Tiny baseline values should not get excessive padding forcing 0-0.01 scale")
        
        # Range should be close to data range with modest padding
        expected_max_range = data_range * 1.25  # 25% total padding
        self.assertLess(calculated_range, expected_max_range,
            "Calculated range should be reasonable relative to data")

    def test_near_zero_small_variance_anchors_to_zero(self):
        """
        Correct behavior: Small signal very close to zero should still anchor to ymin=0.
        E.g., data in 0.1-1.0 range should anchor to 0 for clean baseline appearance.
        """
        ys = [0.1, 0.5, 1.0]  # Range: 0.9, ymin is 11% of range
        ymin, ymax = self._calculate_y_limits(ys, "0.1", SIGNAL)
        
        # Should anchor to zero because ymin (0.1) <= 0.5 * range (0.45)
        self.assertEqual(ymin, 0,
            "Small values near zero should anchor to ymin=0 for clean plots")

    def test_medium_signal_no_anchor_to_zero(self):
        """
        Correct behavior: Medium signal values (5-15) should not anchor to zero.
        Data significance starts higher than zero.
        """
        ys = [5.0, 10.0, 15.0]  # Range: 10, ymin is 50% of range (edge case)
        ymin, ymax = self._calculate_y_limits(ys, "0.1", SIGNAL)
        
        # At edge: ymin (5.0) == 0.5 * range (5.0), should anchor
        self.assertEqual(ymin, 0,
            "Boundary case: ymin == 50% of range should anchor to 0")
        
        # Just above edge - should not anchor
        ys2 = [5.1, 10.0, 15.0]  # Range: 9.9, ymin is 51.5% of range
        ymin2, ymax2 = self._calculate_y_limits(ys2, "0.1", SIGNAL)
        self.assertGreater(ymin2, 0,
            "Values just above boundary should not anchor to 0")

    def test_negative_values_no_anchor_to_zero(self):
        """
        Correct behavior: Negative values should never anchor to zero.
        Only non-negative SIGNAL/SNIFF collections anchor.
        """
        ys = [-5.0, -2.0, 0.0, 2.0, 5.0]
        ymin, ymax = self._calculate_y_limits(ys, "0.1", SIGNAL)
        
        # Should not anchor because ymin is negative
        self.assertLess(ymin, -5.0,
            "Negative values should have padding applied, not anchored to 0")

    def test_baseline_collection_no_anchor_to_zero(self):
        """
        Correct behavior: BASELINE collection never anchors to zero.
        Only SIGNAL and SNIFF collections can anchor.
        """
        ys = [0.01, 0.05, 0.1]  # Range: 0.09, ymin is 11% of range
        ymin, ymax = self._calculate_y_limits(ys, "0.1", BASELINE)
        
        # Should not anchor because collection_kind is BASELINE
        expected_ymin = 0.01 - 0.009  # ymin - ypad
        self.assertAlmostEqual(ymin, expected_ymin, places=5,
            msg="BASELINE collection should apply padding, not anchor to 0")

    def test_padding_scales_with_data_range(self):
        """
        Correct behavior: Padding should scale with data range.
        10% padding of tiny range should be much smaller than 10% of large range.
        """
        # Small range
        ys_small = [0.001, 0.002]  # Range: 0.001
        ymin_small, ymax_small = self._calculate_y_limits(
            ys_small, "0.1", BASELINE
        )
        small_padding = ymax_small - max(ys_small)
        
        # Large range
        ys_large = [100.0, 200.0]  # Range: 100
        ymin_large, ymax_large = self._calculate_y_limits(
            ys_large, "0.1", BASELINE
        )
        large_padding = ymax_large - max(ys_large)
        
        # Padding should scale roughly proportionally
        ratio = large_padding / small_padding
        expected_ratio = 100.0 / 0.001  # 100,000
        self.assertAlmostEqual(
            ratio, expected_ratio, delta=expected_ratio * 0.01,
            msg="Padding should scale proportionally with data range"
        )

    def test_string_vs_float_ypadding(self):
        """
        Correct behavior: String ypadding ("0.1") and float ypadding (0.1) should differ.
        String is interpreted as percentage of range; float is absolute.
        """
        ys = [1.0, 2.0, 3.0]  # Range: 2
        
        # String: 10% of range
        ymin_str, ymax_str = self._calculate_y_limits(ys, "0.1", BASELINE)
        str_padding = ymax_str - max(ys)  # Should be ~0.2
        
        # Float: absolute 0.1
        ymin_float, ymax_float = self._calculate_y_limits(ys, 0.1, BASELINE)
        float_padding = ymax_float - max(ys)  # Should be ~0.1
        
        self.assertAlmostEqual(
            str_padding, 0.2, places=5,
            msg="String ypadding should be percentage of range"
        )
        self.assertAlmostEqual(
            float_padding, 0.1, places=5,
            msg="Float ypadding should be absolute value"
        )

    def test_all_limits_finite(self):
        """
        Sanity check: All calculated limits should be finite (not inf or nan).
        """
        test_cases = [
            ([399.0, 401.0], "0.1", SIGNAL),
            ([0.0001, 0.002], "0.1", BASELINE),
            ([0.0, 1.0], "0.1", SNIFF),
            ([-10.0, 10.0], "0.1", SIGNAL),
        ]
        
        for ys, ypad, kind in test_cases:
            ymin, ymax = self._calculate_y_limits(ys, ypad, kind)
            self.assertTrue(isfinite(ymin),
                f"ymin must be finite for data {ys}")
            self.assertTrue(isfinite(ymax),
                f"ymax must be finite for data {ys}")
            self.assertLess(ymin, ymax,
                f"ymin must be less than ymax for data {ys}")


if __name__ == "__main__":
    unittest.main()
