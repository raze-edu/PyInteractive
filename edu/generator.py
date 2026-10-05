"""Math Exercise Generator for Addition, Subtraction, Multiplication, and Division.
Generates balanced, curriculum-aligned exercise sets across Easy, Medium, and Hard difficulties,
using all appropriate interactive exercise types (NumberLine, EquationSlots, MatchPairs,
TypeAnswer, MultipleChoice, FractionVisual).
"""
import random
from typing import List, Optional, Tuple
from .exercises import (
    BaseExercise,
    NumberLineExercise,
    EquationSlotsExercise,
    MatchPairsExercise,
    TypeAnswerExercise,
    MultipleChoiceExercise,
    FractionVisualExercise
)

class MathGenerator:
    """Generates varied interactive math exercises for arithmetic operations and difficulty levels."""

    @staticmethod
    def generate_lesson(
        operation: str = "addition",  # "addition", "subtraction", "multiplication", "division", "mixed"
        difficulty: str = "easy",     # "easy", "medium", "hard"
        count: int = 8
    ) -> List[BaseExercise]:
        """Generates a complete list of interactive exercises for the chosen operation and difficulty."""
        exercises: List[BaseExercise] = []
        op_list = ["addition", "subtraction", "multiplication", "division"]
        
        # Cycle through diverse exercise types
        exercise_types = ["number_line", "equation_slots", "type_answer", "multiple_choice", "match_pairs"]
        
        for i in range(count):
            cur_op = random.choice(op_list) if operation == "mixed" else operation
            ex_type = exercise_types[i % len(exercise_types)]
            
            ex = MathGenerator.generate_single(cur_op, difficulty, ex_type)
            exercises.append(ex)
            
        return exercises

    @staticmethod
    def generate_single(operation: str, difficulty: str, exercise_type: str) -> BaseExercise:
        """Dispatches exercise generation to the respective operator method."""
        if operation == "addition":
            return MathGenerator._gen_addition(difficulty, exercise_type)
        elif operation == "subtraction":
            return MathGenerator._gen_subtraction(difficulty, exercise_type)
        elif operation == "multiplication":
            return MathGenerator._gen_multiplication(difficulty, exercise_type)
        elif operation == "division":
            return MathGenerator._gen_division(difficulty, exercise_type)
        else:
            return MathGenerator._gen_addition(difficulty, exercise_type)

    @staticmethod
    def _make_ticks(target_val: int, count: int = 7) -> List[int]:
        """Generates a clean list of sorted ticks containing target_val."""
        candidates = [1, 2, 5, 10, 15, 20, 25, 50, 100]
        ideal_step = max(1, target_val // 4)
        step = min(candidates, key=lambda c: abs(c - ideal_step))
        desired_idx = count // 2
        start_val = target_val - desired_idx * step
        if start_val < 0:
            start_val = 0
            if target_val > 0 and (target_val % desired_idx == 0):
                step = target_val // desired_idx
        ticks = [start_val + i * step for i in range(count)]
        if target_val not in ticks:
            ticks[desired_idx] = target_val
            ticks = sorted(list(set(ticks)))
            while len(ticks) < count:
                ticks.append(ticks[-1] + step)
        return sorted(ticks)

    # --------------------------------------------------------------------------
    # ADDITION
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_addition(difficulty: str, exercise_type: str) -> BaseExercise:
        if difficulty == "easy":
            a = random.randint(10, 35)
            b = random.randint(5, 25)
            c = random.randint(5, 20)
        elif difficulty == "medium":
            a = random.randint(30, 90)
            b = random.randint(20, 70)
            c = random.randint(15, 50)
        else:  # hard
            a = random.randint(120, 450)
            b = random.randint(80, 350)
            c = random.randint(50, 200)

        total_3 = a + b + c
        total_2 = a + b

        if exercise_type == "number_line":
            ticks = MathGenerator._make_ticks(total_3)

            fmt = random.choice([
                f"{a} + {b} + {c} = [ ]",
                f"[ ] = {a} + {b} + {c}"
            ])
            return NumberLineExercise(
                title="Answer on the line",
                equation_format=fmt,
                correct_value=total_3,
                ticks=ticks,
                help_tip="Add the numbers together step by step, then slide the marker to mark your total on the number line."
            )

        elif exercise_type == "equation_slots":
            # [ ] = total_3 with a + b + c
            tokens = [(str(a), False), ("+", True), (str(b), False), ("+", True), (str(c), False)]
            # Add distractors
            distractor1 = (str(max(1, a - 5)), False)
            distractor2 = ("-", True)
            bank = tokens + [distractor1, distractor2]
            random.shuffle(bank)
            
            return EquationSlotsExercise(
                title="Complete the equation",
                target_equation=f"[ ] = {total_3}",
                target_value=total_3,
                num_slots=5,
                bank_tokens=bank,
                help_tip="Select numbers and plus signs from the bank to create an addition expression that equals the target."
            )

        elif exercise_type == "type_answer":
            fmt = f"{a} + {b} + {c} = [ ]" if difficulty != "easy" else f"{a} + {b} = [ ]"
            ans = str(total_3 if difficulty != "easy" else total_2)
            return TypeAnswerExercise(
                title="Type the answer",
                equation_format=fmt,
                correct_answer=ans,
                help_tip="Add the numbers together, or use the Toolkit calculator on the bottom left for scratch work."
            )

        elif exercise_type == "multiple_choice":
            # Missing addend: a + [ ] = total_2
            choices = [str(b), str(b + 10), str(max(1, b - 10))]
            random.shuffle(choices)
            return MultipleChoiceExercise(
                title="Fill in the blank",
                question_text=f"{a} + [ ] = {total_2}",
                choices=choices,
                correct_choice_index=choices.index(str(b)),
                help_tip="Find the missing number that adds with the first number to make the target sum."
            )

        else:  # match_pairs
            # 3 addition pairs
            pairs = []
            for _ in range(3):
                x = random.randint(10, 40) if difficulty == "easy" else random.randint(30, 120)
                y = random.randint(5, 30) if difficulty == "easy" else random.randint(20, 80)
                pairs.append((f"{x} + {y}", str(x + y)))
            return MatchPairsExercise(
                text_pairs=pairs,
                title="Match the pairs",
                help_tip="Calculate each sum on the left and match it to its total on the right."
            )

    # --------------------------------------------------------------------------
    # SUBTRACTION
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_subtraction(difficulty: str, exercise_type: str) -> BaseExercise:
        if difficulty == "easy":
            start = random.randint(40, 90)
            sub1 = random.randint(10, 25)
            sub2 = random.randint(5, 15)
        elif difficulty == "medium":
            start = random.randint(150, 400)
            sub1 = random.randint(30, 90)
            sub2 = random.randint(10, 40)
        else:  # hard
            start = random.randint(450, 950)
            sub1 = random.randint(100, 300)
            sub2 = random.randint(30, 100)

        result_3 = start - sub1 - sub2
        result_2 = start - sub1

        if exercise_type == "number_line":
            ticks = MathGenerator._make_ticks(result_3)

            fmt = f"{start} - {sub1} - {sub2} = [ ]"
            return NumberLineExercise(
                title="Answer on the line",
                equation_format=fmt,
                correct_value=result_3,
                ticks=ticks,
                help_tip="Subtract step by step from left to right, then mark your answer on the line."
            )

        elif exercise_type == "equation_slots":
            tokens = [(str(start), False), ("-", True), (str(sub1), False), ("-", True), (str(sub2), False)]
            distractor1 = (str(sub1 + 10), False)
            distractor2 = ("-", True)
            bank = tokens + [distractor1, distractor2]
            random.shuffle(bank)
            return EquationSlotsExercise(
                title="Complete the equation",
                target_equation=f"[ ] = {result_3}",
                target_value=result_3,
                num_slots=5,
                bank_tokens=bank,
                help_tip="Place the numbers and minus signs to form an expression that subtracts down to the target."
            )

        elif exercise_type == "type_answer":
            fmt = f"{start} - {sub1} - {sub2} = [ ]"
            return TypeAnswerExercise(
                title="Type the answer",
                equation_format=fmt,
                correct_answer=str(result_3),
                help_tip="Subtract the first number, then subtract the second number."
            )

        elif exercise_type == "multiple_choice":
            choices = [str(result_2), str(result_2 + 10), str(max(0, result_2 - 10))]
            random.shuffle(choices)
            return MultipleChoiceExercise(
                title="Fill in the blank",
                question_text=f"{start} - {sub1} = [ ]",
                choices=choices,
                correct_choice_index=choices.index(str(result_2)),
                help_tip="Subtract the two numbers to find the correct difference."
            )

        else:  # match_pairs
            pairs = []
            for _ in range(3):
                s = random.randint(50, 100) if difficulty == "easy" else random.randint(120, 300)
                sub = random.randint(10, 40) if difficulty == "easy" else random.randint(30, 90)
                pairs.append((f"{s} - {sub}", str(s - sub)))
            return MatchPairsExercise(
                text_pairs=pairs,
                title="Match the pairs",
                help_tip="Solve each subtraction and connect it with the matching difference."
            )

    # --------------------------------------------------------------------------
    # MULTIPLICATION
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_multiplication(difficulty: str, exercise_type: str) -> BaseExercise:
        if difficulty == "easy":
            m1 = random.choice([2, 3, 4, 5, 10])
            m2 = random.randint(2, 9)
        elif difficulty == "medium":
            m1 = random.randint(6, 12)
            m2 = random.randint(6, 12)
        else:  # hard
            m1 = random.randint(12, 25)
            m2 = random.randint(6, 15)

        prod = m1 * m2

        if exercise_type == "number_line":
            ticks = MathGenerator._make_ticks(prod)
            return NumberLineExercise(
                title="Answer on the line",
                equation_format=f"{m1} × {m2} = [ ]",
                correct_value=prod,
                ticks=ticks,
                help_tip="Think of multiplication as repeated addition, or multiply the factors to find the product."
            )

        elif exercise_type == "equation_slots":
            tokens = [(str(m1), False), ("×", True), (str(m2), False)]
            distractor1 = (str(m2 + 1), False)
            distractor2 = ("+", True)
            bank = tokens + [distractor1, distractor2]
            random.shuffle(bank)
            return EquationSlotsExercise(
                title="Complete the equation",
                target_equation=f"[ ] = {prod}",
                target_value=prod,
                num_slots=3,
                bank_tokens=bank,
                help_tip="Select two factors and the multiplication sign to produce the target number."
            )

        elif exercise_type == "type_answer":
            return TypeAnswerExercise(
                title="Type the answer",
                equation_format=f"{m1} × {m2} = [ ]",
                correct_answer=str(prod),
                help_tip="Multiply the two numbers to calculate their product."
            )

        elif exercise_type == "multiple_choice":
            if difficulty == "hard":
                # Distributive expansion: e.g. 5(x + 4) = 5x + [ ]
                k = random.randint(4, 9)
                c = random.randint(3, 8)
                ans = str(k * c)
                choices = [ans, str(k + c), str(k * c + 5)]
                random.shuffle(choices)
                return MultipleChoiceExercise(
                    title="Fill in the blank",
                    question_text=f"{k}(x + {c}) = {k}x + [ ]",
                    choices=choices,
                    correct_choice_index=choices.index(ans),
                    help_tip="Use the distributive law: multiply the factor outside by each term inside: a(x + b) = ax + ab."
                )
            else:
                choices = [str(prod), str(prod + m1), str(max(1, prod - m1))]
                random.shuffle(choices)
                return MultipleChoiceExercise(
                    title="Fill in the blank",
                    question_text=f"{m1} × [ ] = {prod}",
                    choices=[str(m2), str(m2 + 2), str(max(1, m2 - 2))],
                    correct_choice_index=0,
                    help_tip="Find the factor that multiplies with the first number to give the product."
                )

        else:  # match_pairs
            pairs = []
            for _ in range(3):
                x = random.randint(3, 9) if difficulty == "easy" else random.randint(6, 12)
                y = random.randint(3, 9) if difficulty == "easy" else random.randint(6, 12)
                pairs.append((f"{x} × {y}", str(x * y)))
            return MatchPairsExercise(
                text_pairs=pairs,
                title="Match the pairs",
                help_tip="Calculate each multiplication and match it to its product."
            )

    # --------------------------------------------------------------------------
    # DIVISION
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_division(difficulty: str, exercise_type: str) -> BaseExercise:
        if difficulty == "easy":
            divisor = random.choice([2, 3, 4, 5, 10])
            quotient = random.randint(2, 8)
        elif difficulty == "medium":
            divisor = random.randint(4, 12)
            quotient = random.randint(5, 12)
        else:  # hard
            divisor = random.randint(8, 20)
            quotient = random.randint(12, 35)

        dividend = divisor * quotient

        if exercise_type == "number_line":
            ticks = MathGenerator._make_ticks(quotient)
            return NumberLineExercise(
                title="Answer on the line",
                equation_format=f"{dividend} ÷ {divisor} = [ ]",
                correct_value=quotient,
                ticks=ticks,
                help_tip="Determine how many times the divisor fits into the dividend, and mark that quotient."
            )

        elif exercise_type == "equation_slots":
            tokens = [(str(dividend), False), ("÷", True), (str(divisor), False)]
            distractor1 = (str(dividend + divisor), False)
            distractor2 = ("-", True)
            bank = tokens + [distractor1, distractor2]
            random.shuffle(bank)
            return EquationSlotsExercise(
                title="Complete the equation",
                target_equation=f"[ ] = {quotient}",
                target_value=quotient,
                num_slots=3,
                bank_tokens=bank,
                help_tip="Place the dividend, division sign, and divisor to create the quotient."
            )

        elif exercise_type == "type_answer":
            return TypeAnswerExercise(
                title="Type the answer",
                equation_format=f"{dividend} ÷ {divisor} = [ ]",
                correct_answer=str(quotient),
                help_tip="Divide the first number by the second to find the quotient."
            )

        elif exercise_type == "multiple_choice":
            choices = [str(quotient), str(quotient + 2), str(max(1, quotient - 2))]
            random.shuffle(choices)
            return MultipleChoiceExercise(
                title="Fill in the blank",
                question_text=f"{dividend} ÷ [ ] = {quotient}",
                choices=[str(divisor), str(divisor + 2), str(max(1, divisor - 2))],
                correct_choice_index=0,
                help_tip="Find the number that divides into the dividend to yield the quotient."
            )

        else:  # match_pairs
            pairs = []
            for _ in range(3):
                d = random.randint(2, 6) if difficulty == "easy" else random.randint(4, 12)
                q = random.randint(3, 8) if difficulty == "easy" else random.randint(6, 12)
                div = d * q
                pairs.append((f"{div} ÷ {d}", str(q)))
            return MatchPairsExercise(
                text_pairs=pairs,
                title="Match the pairs",
                help_tip="Solve each division problem and link it to its matching quotient."
            )
