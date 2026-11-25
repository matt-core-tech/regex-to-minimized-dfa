#!/usr/bin/env python3
"""
Interactive CLI & Pipeline Driver for Regex-to-Minimized-DFA Engine

Usage:
  Interactive Mode:
    python main.py

  Single-Command Evaluation:
    python main.py "(a|b)*abb" --test aabb ababb ab ba
"""

import sys
import argparse
from automata import compile_regex, simulate_dfa


def print_divider(title: str = ""):
    line = "=" * 64
    if title:
        print(f"\n{line}\n  {title}\n{line}")
    else:
        print(line)


def run_pipeline(regex: str):
    print_divider(f"COMPILING REGULAR EXPRESSION: {regex}")

    try:
        nfa, dfa, min_dfa = compile_regex(regex)
    except Exception as e:
        print(f"Error during compilation: {e}")
        return None

    print("\n--- 1. Thompson NFA ---")
    nfa.display()

    print("\n--- 2. Subset Construction DFA ---")
    dfa.display()

    print("\n--- 3. Hopcroft Minimized DFA ---")
    min_dfa.display()

    print(f"\nState Reduction: {len(dfa.states)} states -> {len(min_dfa.states)} states")
    print_divider()
    return min_dfa


def interactive_repl():
    print_divider("REGULAR EXPRESSION TO MINIMIZED DFA COMPILER")
    print("Supported syntax: [a-zA-Z0-9], Concatenation (ab), Alternation (a|b),")
    print("                  Kleene Star (*), One-or-More (+), Optional (?), Parentheses ()")
    print("Commands: 'exit' or 'quit' to quit, 'done' to return to regex prompt.")
    print_divider()

    while True:
        try:
            user_regex = input("\nEnter regular expression (or 'quit'): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not user_regex:
            continue
        if user_regex.lower() in ("exit", "quit"):
            print("Exiting.")
            break

        min_dfa = run_pipeline(user_regex)
        if min_dfa is None:
            continue

        print(f"\n[Alphabet: {sorted(min_dfa.alphabet)}]")
        print("Test candidate strings against the generated Minimized DFA:")
        print("(Enter string, or type 'done' to enter a new regex)")

        while True:
            try:
                test_str = input("  string> ").strip()
            except (KeyboardInterrupt, EOFError):
                return

            if test_str.lower() in ("done", "exit", "quit"):
                break

            accepted = simulate_dfa(min_dfa, test_str)
            status = "ACCEPT" if accepted else "REJECT"
            symbol = "✓" if accepted else "✗"
            print(f"    [{symbol} {status}] string='{test_str}'")


def main():
    parser = argparse.ArgumentParser(
        description="Compile a regular expression into Thompson NFA, DFA, and Hopcroft Minimized DFA."
    )
    parser.add_argument("regex", nargs="?", help="Regular expression string to compile (e.g. '(a|b)*abb')")
    parser.add_argument("--test", nargs="*", help="Optional candidate strings to test against the compiled DFA")

    args = parser.parse_args()

    if args.regex:
        min_dfa = run_pipeline(args.regex)
        if min_dfa and args.test is not None:
            print("\nCandidate String Evaluation:")
            for s in args.test:
                accepted = simulate_dfa(min_dfa, s)
                status = "ACCEPT" if accepted else "REJECT"
                symbol = "✓" if accepted else "✗"
                print(f"  [{symbol} {status}] '{s}'")
    else:
        interactive_repl()


if __name__ == "__main__":
    main()
