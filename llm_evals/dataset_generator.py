"""
Generate datasets to evaluate the quiz-grading service (grader-of-students).

Each row contains ONLY the inputs required by your grading service:
- question
- reference_solution
- student_answer

Your Opik evaluation task should call `eval_answer(question, reference_solution, student_answer)`
to produce `evaluator_output` (score + feedback), which Opik then scores using GEval/Hallucination/etc.

Outputs:
- datasets/grader_inputs_dev.csv   (30 rows)
- datasets/grader_inputs_full.csv  (200 rows)
- datasets/grader_inputs_hard.csv  (60 rows)
"""

import csv
import random
from pathlib import Path

SEED = 42
random.seed(SEED)

OUTDIR = Path("datasets")
OUTDIR.mkdir(exist_ok=True)

FIELDS = ["id", "topic", "difficulty", "question", "reference_solution", "student_answer"]


def make_row(i: int, topic: str, difficulty: str, q: str, ref: str, student: str) -> dict:
    return {
        "id": i,
        "topic": topic,
        "difficulty": difficulty,
        "question": q,
        "reference_solution": ref,
        "student_answer": student,
    }


# ---------------------------
# Template pool (calculus)
# ---------------------------
TEMPLATES = []

# Power rule derivatives
for n in [2, 3, 4, 5, 7, 8, 10]:
    q = f"Differentiate f(x)=x^{n}."
    ref = f"Using the power rule, f'(x)={n}x^{n-1}."
    variants = [
        f"{n}x^{n-1}",                 # correct
        f"x^{n-1}",                    # missing coefficient
        f"{n}x^{n}",                   # exponent not reduced
        f"{n-1}x^{n-1}",               # wrong coefficient
        "I don't know.",               # off-topic
    ]
    TEMPLATES.append(("derivatives_power", "easy", q, ref, variants))

# Trig/exp/log derivatives
TEMPLATES += [
    ("derivatives_trig", "easy", "Differentiate f(x)=sin(x).", "f'(x)=cos(x).",
     ["cos(x)", "-sin(x)", "sin(x)", "0", "I forgot."]),
    ("derivatives_trig", "easy", "Differentiate f(x)=cos(x).", "f'(x)=-sin(x).",
     ["-sin(x)", "sin(x)", "cos(x)", "0"]),
    ("derivatives_exp", "easy", "Differentiate f(x)=e^x.", "f'(x)=e^x.",
     ["e^x", "xe^x", "e^(x-1)", "0"]),
    ("derivatives_log", "medium", "Differentiate f(x)=ln(x).", "f'(x)=1/x (for x>0).",
     ["1/x", "ln(x)", "x", "1", "0"]),
    ("derivatives_log", "hard", "Differentiate f(x)=ln|x|.", "f'(x)=1/x for x≠0.",
     ["1/x", "1/|x|", "-1/x", "ln|x|"]),
]

# Chain + product rule
TEMPLATES += [
    ("derivatives_chain", "medium", "Differentiate f(x)=sin(3x).", "By chain rule: f'(x)=3cos(3x).",
     ["3cos(3x)", "cos(3x)", "3sin(3x)", "cos(x)"]),
    ("derivatives_chain", "hard", "Differentiate f(x)=(2x+1)^5.", "By chain rule: f'(x)=10(2x+1)^4.",
     ["10(2x+1)^4", "5(2x+1)^4", "10(2x+1)^5", "(2x+1)^4"]),
    ("derivatives_product", "medium", "Differentiate f(x)=x^2·sin(x).",
     "By product rule: f'(x)=2x·sin(x)+x^2·cos(x).",
     ["2x*sin(x) + x^2*cos(x)", "2x*sin(x)", "x^2*cos(x)", "2x*cos(x)", "x^2*sin(x)"]),
    ("derivatives_product", "hard", "Differentiate f(x)=x·e^x.", "Product rule: f'(x)=e^x(1+x).",
     ["e^x(1+x)", "e^x + x e^x", "xe^x", "e^x"]),
]

# Integrals
TEMPLATES += [
    ("integrals_power", "easy", "Compute ∫ 2x dx.", "∫2x dx = x^2 + C.",
     ["x^2 + C", "x^2", "2x^2 + C", "2x + C", "x + C"]),
    ("integrals_power", "medium", "Compute ∫ x^3 dx.", "∫x^3 dx = x^4/4 + C.",
     ["x^4/4 + C", "x^4/4", "x^4 + C", "3x^2 + C"]),
    ("integrals_log", "medium", "Compute ∫ 1/x dx.", "∫1/x dx = ln|x| + C.",
     ["ln|x| + C", "ln(x) + C", "ln|x|", "1/x^2 + C", "x + C"]),
    ("integrals_log", "hard", "Compute ∫ 1/(x-1) dx.", "∫1/(x-1) dx = ln|x-1| + C.",
     ["ln|x-1| + C", "ln|x| + C", "1/(x-1) + C", "ln(x-1)"]),
    ("integrals_trig", "easy", "Compute ∫ cos(x) dx.", "∫cos(x) dx = sin(x) + C.",
     ["sin(x) + C", "sin(x)", "-sin(x) + C", "cos(x) + C"]),
    ("integrals_trig", "medium", "Compute ∫ sin(x) dx.", "∫sin(x) dx = -cos(x) + C.",
     ["-cos(x) + C", "-cos(x)", "cos(x) + C", "sin(x) + C"]),
    ("integrals_exp", "easy", "Compute ∫ e^x dx.", "∫e^x dx = e^x + C.",
     ["e^x + C", "e^x", "xe^x + C", "e^(x-1) + C"]),
]

# Limits
TEMPLATES += [
    ("limits_trig", "easy", "Find lim_{x→0} sin(x)/x.", "The limit is 1.",
     ["1", "0", "Does not exist", "∞", "I don't know"]),
    ("limits_trig", "hard", "Find lim_{x→0} (1-cos x)/x^2.", "The limit is 1/2.",
     ["1/2", "1", "0", "Does not exist"]),
    ("limits_rational", "medium", "Find lim_{x→2} (x^2-4)/(x-2).",
     "Factor: (x^2-4)=(x-2)(x+2), so limit = 4.",
     ["4", "x+2", "0", "2"]),
    ("limits_piecewise", "medium", "Find lim_{x→0} |x|/x.",
     "Left limit -1 and right limit 1, so the limit does not exist.",
     ["Does not exist", "1", "-1", "0"]),
    ("limits_exp", "hard", "Find lim_{x→0} (e^x-1)/x.", "The limit is 1.",
     ["1", "0", "Does not exist", "e"]),
]


def pool():
    """Flatten templates into a list of concrete rows to sample from."""
    items = []
    for topic, diff, q, ref, answers in TEMPLATES:
        for s in answers:
            items.append((topic, diff, q, ref, s))
    return items


POOL = pool()


def sample_rows(n: int, start_id: int = 1):
    chosen = random.choices(POOL, k=n)  # with replacement (lets us scale up)
    rows = []
    for i, (topic, diff, q, ref, s) in enumerate(chosen, start=start_id):
        rows.append(make_row(i, topic, diff, q, ref, s))
    return rows


def hard_rows(n: int = 60):
    """
    Hard set emphasizes adversarial student answers:
    - off-topic
    - confusing +C in derivatives
    - common misconceptions (sign, missing absolute value, missing evaluation)
    """
    curated = [
        ("derivatives_power", "medium", "Differentiate f(x)=x^5.", "f'(x)=5x^4.", "5x^4 + C"),
        ("derivatives_log", "hard", "Differentiate f(x)=ln|x|.", "f'(x)=1/x for x≠0.", "1/|x|"),
        ("integrals_log", "hard", "Compute ∫ 1/(x-1) dx.", "∫1/(x-1) dx = ln|x-1| + C.", "ln|x| + C"),
        ("limits_trig", "hard", "Find lim_{x→0} (1-cos x)/x^2.", "The limit is 1/2.", "1"),
        ("limits_piecewise", "medium", "Find lim_{x→0} |x|/x.",
         "Left limit -1 and right limit 1, so the limit does not exist.", "1"),
        ("integrals_trig", "medium", "Compute ∫ sin(x) dx.", "∫sin(x) dx = -cos(x) + C.", "cos(x) + C"),
        ("limits_exp", "hard", "Find lim_{x→0} (e^x-1)/x.", "The limit is 1.", "0"),
        ("derivatives_chain", "hard", "Differentiate f(x)=ln(3x).", "f'(x)=1/x.", "1/(3x)"),
    ]

    rows = []
    i = 1
    for topic, diff, q, ref, s in curated:
        rows.append(make_row(i, topic, diff, q, ref, s))
        i += 1

    # fill remaining with medium/hard + some off-topic noise
    candidates = [x for x in POOL if x[1] in ("medium", "hard")]
    while len(rows) < n:
        topic, diff, q, ref, s = random.choice(candidates)
        if random.random() < 0.12:
            s = random.choice(["I don't know.", "42", "Because math is hard.", "It depends on the weather."])
            diff = "hard"
        rows.append(make_row(i, topic, diff, q, ref, s))
        i += 1

    return rows


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in FIELDS})


if __name__ == "__main__":
    write_csv(OUTDIR / "grader_inputs_dev.csv", sample_rows(30))
    write_csv(OUTDIR / "grader_inputs_full.csv", sample_rows(200))
    write_csv(OUTDIR / "grader_inputs_hard.csv", hard_rows(60))
    print("Wrote datasets/graders_inputs_{dev,full,hard}.csv")
