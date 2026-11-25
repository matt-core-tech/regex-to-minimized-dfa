"""
Automated Test Suite for Regex-to-Minimized-DFA Engine

Executes tests for:
- Explicit concatenation insertion
- Infix-to-postfix conversion via Shunting-Yard
- Mismatched parentheses and syntax error handling
- Thompson's NFA state construction
- Subset construction (NFA to DFA)
- Hopcroft's minimization (DFA to Minimized DFA)
- Language recognition and boundary condition tests
"""

import unittest
import sys
import os

# Add parent directory to sys.path to enable direct importing of automata
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from automata import (
    add_concat,
    to_postfix,
    thompson,
    nfa_to_dfa,
    hopcroft_minimize,
    simulate_dfa,
    compile_regex,
    State
)


class TestShuntingYard(unittest.TestCase):
    """Tests for regex parsing and infix-to-postfix conversion."""

    def test_explicit_concatenation(self):
        self.assertEqual(add_concat("ab"), "a.b")
        self.assertEqual(add_concat("abc"), "a.b.c")
        self.assertEqual(add_concat("a*b"), "a*.b")
        self.assertEqual(add_concat("a+b"), "a+.b")
        self.assertEqual(add_concat("a?b"), "a?.b")
        self.assertEqual(add_concat("(a)b"), "(a).b")
        self.assertEqual(add_concat("a(b)"), "a.(b)")
        self.assertEqual(add_concat("(a)(b)"), "(a).(b)")
        self.assertEqual(add_concat("(a|b)*abb"), "(a|b)*.a.b.b")

    def test_to_postfix(self):
        self.assertEqual(to_postfix("a.b"), "ab.")
        self.assertEqual(to_postfix("a|b"), "ab|")
        self.assertEqual(to_postfix("a*.b"), "a*b.")
        self.assertEqual(to_postfix("(a|b)*.c"), "ab|*c.")
        self.assertEqual(to_postfix("a.b|c"), "ab.c|")

    def test_mismatched_parentheses(self):
        with self.assertRaises(ValueError):
            to_postfix("(a|b")
        with self.assertRaises(ValueError):
            to_postfix("a|b)")
        with self.assertRaises(ValueError):
            to_postfix("((a|b)")

    def test_unsupported_operators(self):
        with self.assertRaises(ValueError):
            to_postfix("a^b")
        with self.assertRaises(ValueError):
            to_postfix("a&b")


class TestAutomataPipeline(unittest.TestCase):
    """Tests for NFA, DFA, and Hopcroft transformation pipeline."""

    def setUp(self):
        State.reset_counter()

    def test_single_symbol(self):
        _, _, min_dfa = compile_regex("a")
        self.assertTrue(simulate_dfa(min_dfa, "a"))
        self.assertFalse(simulate_dfa(min_dfa, ""))
        self.assertFalse(simulate_dfa(min_dfa, "aa"))
        self.assertFalse(simulate_dfa(min_dfa, "b"))

    def test_alternation(self):
        _, _, min_dfa = compile_regex("a|b")
        self.assertTrue(simulate_dfa(min_dfa, "a"))
        self.assertTrue(simulate_dfa(min_dfa, "b"))
        self.assertFalse(simulate_dfa(min_dfa, ""))
        self.assertFalse(simulate_dfa(min_dfa, "ab"))
        self.assertFalse(simulate_dfa(min_dfa, "ba"))

    def test_concatenation(self):
        _, _, min_dfa = compile_regex("ab")
        self.assertTrue(simulate_dfa(min_dfa, "ab"))
        self.assertFalse(simulate_dfa(min_dfa, "a"))
        self.assertFalse(simulate_dfa(min_dfa, "b"))
        self.assertFalse(simulate_dfa(min_dfa, "aba"))
        self.assertFalse(simulate_dfa(min_dfa, ""))

    def test_kleene_star(self):
        _, _, min_dfa = compile_regex("a*")
        self.assertTrue(simulate_dfa(min_dfa, ""))
        self.assertTrue(simulate_dfa(min_dfa, "a"))
        self.assertTrue(simulate_dfa(min_dfa, "aa"))
        self.assertTrue(simulate_dfa(min_dfa, "aaaaa"))
        self.assertFalse(simulate_dfa(min_dfa, "b"))
        self.assertFalse(simulate_dfa(min_dfa, "ab"))

    def test_one_or_more_plus(self):
        _, _, min_dfa = compile_regex("a+")
        self.assertFalse(simulate_dfa(min_dfa, ""))
        self.assertTrue(simulate_dfa(min_dfa, "a"))
        self.assertTrue(simulate_dfa(min_dfa, "aaaa"))
        self.assertFalse(simulate_dfa(min_dfa, "b"))

    def test_zero_or_one_question(self):
        _, _, min_dfa = compile_regex("a?")
        self.assertTrue(simulate_dfa(min_dfa, ""))
        self.assertTrue(simulate_dfa(min_dfa, "a"))
        self.assertFalse(simulate_dfa(min_dfa, "aa"))
        self.assertFalse(simulate_dfa(min_dfa, "b"))


class TestComplexLanguages(unittest.TestCase):
    """Tests verifying classic regular language recognition benchmarks."""

    def test_ends_with_abb(self):
        """Language: Strings over {a, b} that end in 'abb'"""
        _, dfa, min_dfa = compile_regex("(a|b)*abb")

        # Hopcroft minimization should reduce or maintain state count
        self.assertLessEqual(len(min_dfa.states), len(dfa.states))

        accept_cases = ["abb", "aabb", "babb", "ababb", "bababb", "bbbbabb"]
        reject_cases = ["", "a", "b", "ab", "ba", "abba", "abbb", "bba"]

        for s in accept_cases:
            with self.subTest(string=s):
                self.assertTrue(simulate_dfa(min_dfa, s), f"Expected '{s}' to be accepted")
                # Ensure equivalence between unminimized DFA and minimized DFA
                self.assertEqual(simulate_dfa(dfa, s), simulate_dfa(min_dfa, s))

        for s in reject_cases:
            with self.subTest(string=s):
                self.assertFalse(simulate_dfa(min_dfa, s), f"Expected '{s}' to be rejected")
                self.assertEqual(simulate_dfa(dfa, s), simulate_dfa(min_dfa, s))

    def test_contains_00(self):
        """Language: Binary strings over {0, 1} containing '00' as a substring"""
        _, _, min_dfa = compile_regex("(0|1)*00(0|1)*")

        accept_cases = ["00", "000", "100", "001", "1001", "110011", "010010"]
        reject_cases = ["", "0", "1", "01", "10", "010", "101", "010101", "101010"]

        for s in accept_cases:
            with self.subTest(string=s):
                self.assertTrue(simulate_dfa(min_dfa, s))

        for s in reject_cases:
            with self.subTest(string=s):
                self.assertFalse(simulate_dfa(min_dfa, s))

    def test_optional_branch(self):
        """Language: a(b?)c -> matches 'ac' or 'abc'"""
        _, _, min_dfa = compile_regex("a(b?)c")

        self.assertTrue(simulate_dfa(min_dfa, "ac"))
        self.assertTrue(simulate_dfa(min_dfa, "abc"))
        self.assertFalse(simulate_dfa(min_dfa, "abbc"))
        self.assertFalse(simulate_dfa(min_dfa, "c"))
        self.assertFalse(simulate_dfa(min_dfa, "a"))


class TestEdgeCasesAndValidation(unittest.TestCase):
    """Tests for edge conditions, alphabet violations, and empty inputs."""

    def test_empty_regex(self):
        with self.assertRaises(ValueError):
            compile_regex("")

    def test_out_of_alphabet_characters(self):
        """Strings containing characters not in the regex alphabet must be rejected."""
        _, _, min_dfa = compile_regex("ab")
        self.assertFalse(simulate_dfa(min_dfa, "ac"))
        self.assertFalse(simulate_dfa(min_dfa, "abx"))
        self.assertFalse(simulate_dfa(min_dfa, "12"))

    def test_hopcroft_equivalence(self):
        """DFA and Minimized DFA must yield identical boolean results across multiple expressions."""
        test_expressions = [
            ("a*", ["", "a", "aa", "b"]),
            ("(a|b)+", ["", "a", "b", "ab", "ba", "c"]),
            ("a(b|c)*d", ["ad", "abd", "acd", "abbcd", "a", "d", "abc"]),
        ]

        for regex, test_strings in test_expressions:
            _, dfa, min_dfa = compile_regex(regex)
            for s in test_strings:
                self.assertEqual(
                    simulate_dfa(dfa, s),
                    simulate_dfa(min_dfa, s),
                    f"Mismatch for regex '{regex}' on string '{s}'"
                )


if __name__ == "__main__":
    unittest.main()
