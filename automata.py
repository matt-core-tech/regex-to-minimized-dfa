"""
Regular Expression to Minimized DFA Compiler & Automata Engine

Implements the classic compiler theory transformation pipeline:
1. Infix Regular Expression with implicit concatenation
2. Explicit Concatenation Insertion
3. Postfix Conversion via Dijkstra's Shunting-Yard Algorithm
4. Non-Deterministic Finite Automaton (NFA) via Thompson's Construction
5. Deterministic Finite Automaton (DFA) via Subset Construction & Epsilon Closure
6. Minimized DFA via Hopcroft's Partition Refinement Algorithm
7. Interactive String Simulation & Language Recognition

Zero external dependencies - implemented using Python standard library.
"""

from collections import defaultdict, deque
from typing import Set, Dict, List, FrozenSet, Optional, Tuple

EPSILON = 'ε'  # Epsilon transition symbol


# ---------------------- STATE CLASS ----------------------

class State:
    """Represents a state in a Non-Deterministic Finite Automaton (NFA)."""
    _id_counter = 0

    def __init__(self):
        self.id = State._id_counter
        State._id_counter += 1
        self.transitions: Dict[str, Set['State']] = defaultdict(set)

    def add_transition(self, symbol: str, state: 'State'):
        """Add a transition on symbol to target state."""
        self.transitions[symbol].add(state)

    def __repr__(self):
        return f"S{self.id}"

    @classmethod
    def reset_counter(cls):
        """Reset the internal ID counter (useful for reproducible test runs)."""
        cls._id_counter = 0


# ---------------------- NFA CLASS ----------------------

class NFA:
    """Represents a Non-Deterministic Finite Automaton with a single start and accept state."""

    def __init__(self, start: State, accept: State, states: Optional[Set[State]] = None):
        self.start = start
        self.accept = accept
        self.states = states or self._collect_states()

    def _collect_states(self) -> Set[State]:
        """Traverse the state graph from start state and collect all reachable states."""
        visited = set()
        stack = [self.start]
        while stack:
            s = stack.pop()
            if s in visited:
                continue
            visited.add(s)
            for targets in s.transitions.values():
                for t in targets:
                    stack.append(t)
        return visited

    def display(self):
        """Print the NFA states, start/accept markers, and transition table."""
        sorted_states = sorted(self.states, key=lambda x: x.id)
        print("NFA STATES:", sorted_states)
        print(f"Start: {self.start}, Accept: {self.accept}")
        print("Transitions:")
        for s in sorted_states:
            for sym, tgts in s.transitions.items():
                for t in sorted(tgts, key=lambda x: x.id):
                    print(f"  {s} -[{sym}]-> {t}")


# ---------------------- REGEX PARSER ----------------------

def add_concat(regex: str) -> str:
    """
    Insert explicit concatenation operator '.' into an infix regular expression.
    
    A concatenation is inserted between:
    - An operand or postfix operator (*, +, ?) and an operand
    - An operand or postfix operator and an opening parenthesis '('
    - A closing parenthesis ')' and an operand or '('
    """
    if not regex:
        return ""

    res = []
    for i in range(len(regex) - 1):
        a, b = regex[i], regex[i + 1]
        res.append(a)
        if (a in ")*+?" or a.isalnum()) and (b.isalnum() or b == '('):
            res.append('.')
    res.append(regex[-1])
    return ''.join(res)


def to_postfix(regex: str) -> str:
    """
    Convert an infix regular expression with explicit '.' operators
    into postfix (Reverse Polish) notation using Dijkstra's Shunting-Yard algorithm.
    """
    if not regex:
        return ""

    prec = {'*': 3, '+': 3, '?': 3, '.': 2, '|': 1}
    output = []
    stack = []

    for ch in regex:
        if ch.isalnum():
            output.append(ch)
        elif ch == '(':
            stack.append(ch)
        elif ch == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if not stack:
                raise ValueError("Mismatched parentheses: unexpected ')' in regular expression.")
            stack.pop()  # Discard '('
        else:
            if ch not in prec:
                raise ValueError(f"Unsupported regular expression operator: '{ch}'")
            while stack and stack[-1] != '(' and prec.get(stack[-1], 0) >= prec[ch]:
                output.append(stack.pop())
            stack.append(ch)

    while stack:
        op = stack.pop()
        if op == '(':
            raise ValueError("Mismatched parentheses: unclosed '(' in regular expression.")
        output.append(op)

    return ''.join(output)


# ---------------------- THOMPSON'S CONSTRUCTION ----------------------

def thompson(postfix: str) -> NFA:
    """
    Construct an NFA from a postfix regular expression using Thompson's Construction.
    
    Guarantees:
    - Single start state with no incoming transitions
    - Single accept state with no outgoing transitions
    - Compositional construction for concatenation (.), alternation (|),
      Kleene star (*), one-or-more (+), and optionality (?).
    """
    if not postfix:
        raise ValueError("Cannot construct NFA from empty postfix expression.")

    stack: List[NFA] = []

    for ch in postfix:
        if ch.isalnum():  # Single symbol operand
            s1, s2 = State(), State()
            s1.add_transition(ch, s2)
            stack.append(NFA(s1, s2, {s1, s2}))

        elif ch == '.':  # Concatenation
            if len(stack) < 2:
                raise ValueError("Malformed postfix expression: insufficient operands for concatenation.")
            n2 = stack.pop()
            n1 = stack.pop()
            n1.accept.add_transition(EPSILON, n2.start)
            stack.append(NFA(n1.start, n2.accept, n1.states | n2.states))

        elif ch == '|':  # Alternation (Union)
            if len(stack) < 2:
                raise ValueError("Malformed postfix expression: insufficient operands for alternation.")
            n2 = stack.pop()
            n1 = stack.pop()
            s, a = State(), State()
            s.add_transition(EPSILON, n1.start)
            s.add_transition(EPSILON, n2.start)
            n1.accept.add_transition(EPSILON, a)
            n2.accept.add_transition(EPSILON, a)
            stack.append(NFA(s, a, n1.states | n2.states | {s, a}))

        elif ch == '*':  # Kleene star (0 or more)
            if len(stack) < 1:
                raise ValueError("Malformed postfix expression: insufficient operands for '*'.")
            n = stack.pop()
            s, a = State(), State()
            s.add_transition(EPSILON, n.start)
            s.add_transition(EPSILON, a)
            n.accept.add_transition(EPSILON, n.start)
            n.accept.add_transition(EPSILON, a)
            stack.append(NFA(s, a, n.states | {s, a}))

        elif ch == '+':  # One or more (Positive closure)
            if len(stack) < 1:
                raise ValueError("Malformed postfix expression: insufficient operands for '+'.")
            n = stack.pop()
            s, a = State(), State()
            s.add_transition(EPSILON, n.start)
            n.accept.add_transition(EPSILON, n.start)
            n.accept.add_transition(EPSILON, a)
            stack.append(NFA(s, a, n.states | {s, a}))

        elif ch == '?':  # Zero or one (Optional)
            if len(stack) < 1:
                raise ValueError("Malformed postfix expression: insufficient operands for '?'.")
            n = stack.pop()
            s, a = State(), State()
            s.add_transition(EPSILON, n.start)
            s.add_transition(EPSILON, a)
            n.accept.add_transition(EPSILON, a)
            stack.append(NFA(s, a, n.states | {s, a}))

    if len(stack) != 1:
        raise ValueError(f"Malformed postfix expression: stack imbalance with {len(stack)} fragments remaining.")

    return stack[0]


# ---------------------- NFA TO DFA (SUBSET CONSTRUCTION) ----------------------

def epsilon_closure(states: Set[State]) -> Set[State]:
    """Compute the epsilon closure of a set of NFA states via depth-first search."""
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for t in s.transitions.get(EPSILON, []):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return closure


def move(states: Set[State], symbol: str) -> Set[State]:
    """Compute the set of NFA states reachable from states on a given transition symbol."""
    res = set()
    for s in states:
        res |= s.transitions.get(symbol, set())
    return res


class DFA:
    """Represents a Deterministic Finite Automaton."""

    def __init__(
        self,
        start: FrozenSet[State],
        accepts: Set[FrozenSet[State]],
        trans: Dict[FrozenSet[State], Dict[str, FrozenSet[State]]],
        alphabet: Set[str]
    ):
        self.start = start
        self.accepts = accepts
        self.transitions = trans
        self.states = set(trans.keys())
        self.alphabet = alphabet

    def display(self):
        """Print DFA states and transitions."""
        print(f"DFA TOTAL STATES: {len(self.states)}")
        print("States:")
        for s in sorted(self.states, key=lambda st: sorted(x.id for x in st)):
            markers = []
            if s == self.start:
                markers.append("START")
            if s in self.accepts:
                markers.append("ACCEPT")
            marker_str = f" [{', '.join(markers)}]" if markers else ""
            state_label = [st.id for st in sorted(s, key=lambda x: x.id)]
            print(f"  {state_label}{marker_str}")

        print("Transitions:")
        for s in sorted(self.states, key=lambda st: sorted(x.id for x in st)):
            for sym in sorted(self.alphabet):
                tgt = self.transitions.get(s, {}).get(sym, frozenset())
                src_label = [st.id for st in sorted(s, key=lambda x: x.id)]
                tgt_label = [st.id for st in sorted(tgt, key=lambda x: x.id)] if tgt else "[DEAD/TRAP]"
                print(f"  {src_label} -[{sym}]-> {tgt_label}")


def nfa_to_dfa(nfa: NFA) -> DFA:
    """
    Convert an NFA to a DFA using the Subset Construction algorithm.
    Includes explicit dead/trap state for missing transitions.
    """
    alphabet = {sym for s in nfa.states for sym in s.transitions if sym != EPSILON}
    start_closure = frozenset(epsilon_closure({nfa.start}))
    queue = deque([start_closure])
    visited = {start_closure}
    transitions: Dict[FrozenSet[State], Dict[str, FrozenSet[State]]] = {}
    accepts: Set[FrozenSet[State]] = set()

    while queue:
        cur = queue.popleft()
        transitions[cur] = {}
        if nfa.accept in cur:
            accepts.add(cur)

        for sym in alphabet:
            tgt = frozenset(epsilon_closure(move(set(cur), sym)))
            if tgt:
                transitions[cur][sym] = tgt
                if tgt not in visited:
                    visited.add(tgt)
                    queue.append(tgt)

    # Add explicit trap/dead state for total transition function
    trap: FrozenSet[State] = frozenset()
    needs_trap = False

    for s in list(transitions.keys()):
        for sym in alphabet:
            if sym not in transitions[s]:
                transitions[s][sym] = trap
                needs_trap = True

    if needs_trap:
        transitions[trap] = {sym: trap for sym in alphabet}

    return DFA(start_closure, accepts, transitions, alphabet)


# ---------------------- DFA MINIMIZATION (HOPCROFT'S ALGORITHM) ----------------------

def hopcroft_minimize(dfa: DFA) -> DFA:
    """
    Minimize a DFA using Hopcroft's Partition Refinement Algorithm.
    
    Time Complexity: O(k * n * log n) where n is the number of states and k is alphabet size.
    Produces the unique minimal DFA (up to state isomorphism) recognizing the language.
    """
    symbols = sorted(dfa.alphabet)
    non_accepts = set(dfa.states) - dfa.accepts

    # Initial partition P: accepting states and non-accepting states
    # Filter out empty sets if all states are accepting or non-accepting
    P = [p for p in [dfa.accepts, non_accepts] if len(p) > 0]
    W = deque([p.copy() for p in P])

    while W:
        A = W.popleft()
        for c in symbols:
            # X = set of all states that have a transition on symbol c into set A
            X = {q for q in dfa.states if dfa.transitions.get(q, {}).get(c) in A}
            if not X:
                continue

            new_P = []
            for Y in P:
                inter = Y & X
                diff = Y - X
                if inter and diff:
                    new_P.extend([inter, diff])
                    if Y in W:
                        W.remove(Y)
                        W.extend([inter, diff])
                    else:
                        W.append(inter if len(inter) <= len(diff) else diff)
                else:
                    new_P.append(Y)
            P = new_P

    # Assign a representative state to each partition block
    rep = {}
    for block in P:
        canonical_state = next(iter(block))
        for q in block:
            rep[q] = canonical_state

    new_trans: Dict[FrozenSet[State], Dict[str, FrozenSet[State]]] = {
        rep[q]: {} for q in rep.values()
    }

    for q in rep:
        for c, t in dfa.transitions.get(q, {}).items():
            new_trans[rep[q]][c] = rep[t]

    new_start = rep[dfa.start]
    new_accepts = {rep[q] for q in dfa.accepts}

    return DFA(new_start, new_accepts, new_trans, dfa.alphabet)


# ---------------------- DFA SIMULATION ----------------------

def simulate_dfa(dfa: DFA, input_str: str) -> bool:
    """
    Simulate execution of the DFA on an input string.
    
    Returns:
    - True if the input string drives the automaton from start state to an accept state.
    - False if rejected or if input contains symbols outside the alphabet.
    """
    current = dfa.start
    for ch in input_str:
        if ch not in dfa.alphabet:
            return False
        current = dfa.transitions.get(current, {}).get(ch)
        if not current:
            return False
    return current in dfa.accepts


# ---------------------- HIGH-LEVEL PIPELINE API ----------------------

def compile_regex(regex: str) -> Tuple[NFA, DFA, DFA]:
    """
    Execute the complete transformation pipeline for a regular expression.
    
    Returns:
    - (nfa, dfa, minimized_dfa)
    """
    if not regex:
        raise ValueError("Cannot compile empty regular expression.")

    # Reset state ID counter for clean sequential state labeling
    State.reset_counter()

    # Step 1: Explicit concatenation insertion
    explicit_concat = add_concat(regex)

    # Step 2: Postfix conversion
    postfix = to_postfix(explicit_concat)

    # Step 3: Thompson's NFA construction
    nfa = thompson(postfix)

    # Step 4: Subset construction (NFA -> DFA)
    dfa = nfa_to_dfa(nfa)

    # Step 5: Hopcroft's minimization (DFA -> Minimized DFA)
    min_dfa = hopcroft_minimize(dfa)

    return nfa, dfa, min_dfa
