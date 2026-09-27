import unittest

from calculators import loan_emi, simple_interest


class CalculatorTests(unittest.TestCase):
    def test_simple_interest(self):
        self.assertEqual(simple_interest(1000, 5, 2), (100.0, 1100.0))

    def test_loan_emi_with_zero_rate(self):
        self.assertEqual(loan_emi(1200, 0, 12), 100.0)

    def test_loan_emi_with_interest(self):
        self.assertAlmostEqual(loan_emi(100000, 12, 12), 8884.8789, places=3)

    def test_invalid_calculator_inputs(self):
        with self.assertRaises(ValueError):
            simple_interest("nan", 5, 2)
        with self.assertRaisesRegex(ValueError, "whole number"):
            loan_emi(1000, 5, 2.5)


if __name__ == "__main__":
    unittest.main()
