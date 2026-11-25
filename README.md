# Regular Expression to Minimized DFA Engine

An automata theory compiler and finite state machine simulator written in pure Python with zero external dependencies.

This project translates regular expressions into minimal deterministic finite automata through the classic theoretical pipeline: infix parsing with explicit concatenation, Dijkstra's Shunting-Yard postfix conversion, Thompson's NFA construction, subset construction with epsilon closure, and Hopcroft's partition refinement minimization.

---

## Architecture & Transformation Pipeline

```
Infix Regex (e.g. (a|b)*abb)
       │
       ▼ [1. Explicit Concatenation]
(a|b)*.a.b.b
       │
       ▼ [2. Shunting-Yard Algorithm]
Postfix: ab|*a.b.b.
       │
       ▼ [3. Thompson's Construction]
Non-Deterministic Finite Automaton (NFA with ε-transitions)
       │
       ▼ [4. Subset Construction & Epsilon Closure]
Deterministic Finite Automaton (DFA)
       │
       ▼ [5. Hopcroft's Partition Refinement Algorithm]
Unique Canonical Minimized DFA
       │
       ▼ [6. String Simulator]
Accept / Reject Evaluation
```

---

## Features

- **End-to-End Compiler Pipeline:** Step-by-step transformation from regular expression to minimal finite state machine.
- **Zero Third-Party Dependencies:** Uses exclusively Python standard library primitives (`collections`, `typing`).
- **Detailed State Inspection:** Visualizes transition tables, start states, and accept states across each stage.
- **Interactive REPL & CLI Interface:** Compile expressions interactively or test strings directly from terminal arguments.
- **Automated Test Suite:** Built-in `unittest` coverage verifying operator precedence, edge cases, and equivalence between unminimized and minimized automata.

---

## Supported Grammar & Operators

The engine supports alphanumeric symbols and the following operators:

| Operator | Notation | Precedence | Meaning |
| :--- | :--- | :--- | :--- |
| **Kleene Star** | `*` | 3 (Highest) | Zero or more occurrences |
| **One-or-More** | `+` | 3 | One or more occurrences |
| **Optional** | `?` | 3 | Zero or one occurrence |
| **Concatenation** | `ab` (implicit) | 2 | Sequence of characters |
| **Alternation** | `a \| b` | 1 (Lowest) | Union / logical OR |
| **Grouping** | `( ... )` | Overrides precedence | Subexpression grouping |

### Syntax Assumptions & Boundaries
- **Alphabet:** Alphanumeric characters (`[a-zA-Z0-9]`).
- **Whitespace:** Regular expressions should not contain raw whitespace (e.g., use `(a|b)*c` rather than `(a | b)* c`).
- **Character Classes & Escapes:** Character ranges (e.g. `[a-z]`) and backslash escapes (`\d`, `\w`) are not currently part of this academic grammar.

---

## Project Structure

```
regex-to-minimized-dfa/
├── automata.py          # Core engine (State, NFA, DFA, Hopcroft minimization)
├── main.py              # CLI driver with interactive REPL and argument parsing
├── tests/
│   └── test_automata.py # Comprehensive test cases across grammar and languages
├── .gitignore           # Git ignore rules for Python artifacts
└── README.md            # Technical documentation
```

---

## Installation & Requirements

- **Python 3.8+**
- No external packages required.

Clone or download the repository:

```bash
git clone https://github.com/<your-username>/regex-to-minimized-dfa.git
cd regex-to-minimized-dfa
```

---

## Usage

### 1. Interactive REPL Mode
Run without arguments to start the interactive evaluation shell:

```bash
python main.py
```

Example session:
```text
Enter regular expression (or 'quit'): (a|b)*abb

[Alphabet: ['a', 'b']]
Test candidate strings against the generated Minimized DFA:
(Enter string, or type 'done' to enter a new regex)
  string> aabb
    [✓ ACCEPT] string='aabb'
  string> bababb
    [✓ ACCEPT] string='bababb'
  string> aabba
    [✗ REJECT] string='aabba'
```

### 2. Command-Line Argument Mode
Evaluate specific candidate strings in a single command:

```bash
python main.py "(a|b)*abb" --test aabb ababb ab ba
```

Output:
```text
Candidate String Evaluation:
  [✓ ACCEPT] 'aabb'
  [✓ ACCEPT] 'ababb'
  [✗ REJECT] 'ab'
  [✗ REJECT] 'ba'
```

### 3. Programmatic Library Usage
Import the engine directly into your own Python scripts:

```python
from automata import compile_regex, simulate_dfa

# Compile regular expression through all 5 phases
nfa, dfa, min_dfa = compile_regex("(0|1)*00(0|1)*")

# Simulate string acceptance
print(simulate_dfa(min_dfa, "1001"))  # True
print(simulate_dfa(min_dfa, "0101"))  # False
```

---

## Running the Automated Test Suite

The test suite covers infix-to-postfix parsing, mismatched parenthesis detection, Thompson state wiring, and language acceptance across various grammar constructs:

```bash
python -m unittest discover tests
```

Output:
```text
................
----------------------------------------------------------------------
Ran 16 tests in 0.007s

OK
```

---

## Limitations & Potential Enhancements

- **Extended Character Classes:** Extending parser to support ranges such as `[a-z]` and negated sets `[^abc]`.
- **Epsilon in Input:** Currently, epsilon (`ε`) is an internal transition symbol rather than a user-input literal.
- **Graph Visualization:** Adding an optional Graphviz DOT export to visually render state machine transition diagrams.
