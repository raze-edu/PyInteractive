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
    FractionVisualExercise,
    CoordinateGridExercise,
    Cylinder3DExercise
)

class MathGenerator:
    """Generates varied interactive math exercises for arithmetic operations and difficulty levels."""

    @staticmethod
    def generate_lesson(
        operation: str = "addition",  # "addition", "subtraction", "multiplication", "division", "coordinates", "logarithms", "cylinder", "mixed"
        difficulty: str = "easy",     # "easy", "medium", "hard"
        count: int = 8
    ) -> List[BaseExercise]:
        """Generates a complete list of interactive exercises for the chosen operation and difficulty."""
        exercises: List[BaseExercise] = []
        op_list = ["addition", "subtraction", "multiplication", "division", "coordinates", "logarithms", "cylinder"]

        if operation == "coordinates":
            exercise_types = ["place_point", "create_graph", "number_line", "type_answer", "multiple_choice", "match_pairs"]
        elif operation == "logarithms":
            exercise_types = ["concept", "pattern_table", "identify_parts", "multiple_choice", "match_pairs", "type_answer"]
        elif operation == "cylinder":
            exercise_types = ["cylinder_3d_base", "cylinder_3d_vol", "cross_section", "radius_choice", "base_area_choice", "volume_choice"]
        else:
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
        elif operation == "coordinates":
            return MathGenerator._gen_coordinates(difficulty, exercise_type)
        elif operation == "logarithms":
            return MathGenerator._gen_logarithms(difficulty, exercise_type)
        elif operation == "cylinder":
            return MathGenerator._gen_cylinder(difficulty, exercise_type)
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

    # --------------------------------------------------------------------------
    # CARTESIAN COORDINATES & GRAPHING
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_coordinates(difficulty: str, exercise_type: str) -> BaseExercise:
        bound = 4 if difficulty == "easy" else (6 if difficulty == "medium" else 8)
        x_range = (-bound - 1, bound + 1)
        y_range = (-bound - 1, bound + 1)

        # Generate a non-zero coordinate
        x = random.choice([v for v in range(-bound, bound + 1) if v != 0])
        y = random.choice([v for v in range(-bound, bound + 1) if v != 0])

        if exercise_type == "place_point":
            return CoordinateGridExercise(
                prompt=f"Place the point at ({x}, {y})",
                target_points=[(x, y)],
                mode="place_point",
                x_range=x_range,
                y_range=y_range,
                instruction="Click or drag to place the point on the coordinate grid."
            )

        elif exercise_type == "create_graph":
            slope = random.choice([-2, -1, 1, 2])
            intercept = random.choice([-2, -1, 0, 1, 2])
            xs = [-2, 0, 2] if bound >= 4 else [-1, 0, 1]
            table_pts = [(xi, slope * xi + intercept) for xi in xs]
            return CoordinateGridExercise(
                prompt="Create a graph with points at:",
                target_points=table_pts,
                mode="create_graph",
                x_range=x_range,
                y_range=y_range,
                table_data=table_pts,
                instruction="Plot all points from the table and adjust them on the graph."
            )

        elif exercise_type == "number_line":
            target = x if random.random() < 0.5 else y
            coord_name = "x" if target == x else "y"
            ticks = list(range(x_range[0], x_range[1] + 1))
            return NumberLineExercise(
                equation_format=f"Show {coord_name} on the line",
                correct_value=target,
                ticks=ticks,
                initial_tick_index=len(ticks) // 2,
                title=f"Show {coord_name} on the line",
                help_tip=f"Identify the {coord_name}-coordinate of ({x}, {y}) and locate it on the number line.",
                prompt_grid_point=(x, y) if random.random() < 0.5 else None,
                prompt_coord=(x, y) if random.random() >= 0.5 else None,
                highlight_coord=coord_name
            )

        elif exercise_type == "type_answer":
            target = x if random.random() < 0.5 else y
            coord_name = "x" if target == x else "y"
            return TypeAnswerExercise(
                equation_format=f"{coord_name} = [ ]",
                correct_answer=str(target),
                title=f"Enter the {coord_name}-value",
                help_tip=f"Find the {coord_name}-coordinate and type the number into the answer box.",
                prompt_grid_point=(x, y) if random.random() < 0.5 else None,
                prompt_coord=(x, y) if random.random() >= 0.5 else None,
                highlight_coord=coord_name,
                show_keypad=True
            )

        elif exercise_type == "multiple_choice":
            choices = [f"({x}, {y})", f"({-x}, {y})", f"({x}, {-y})"]
            choice_pts = {0: (x, y), 1: (-x, y), 2: (x, -y)}
            return MultipleChoiceExercise(
                title="Select the match",
                question_text=f"Which graph represents ({x}, {y})?",
                choices=choices,
                correct_choice_index=0,
                diagram_type="visual_grids",
                diagram_data={"choice_points": choice_pts, "x_range": (-5, 5), "y_range": (-5, 5)},
                help_tip="Look for the point plotted at the given x and y values."
            )

        else:  # match_pairs
            pts = [
                (random.choice([-4, -3, -2, 2, 3]), random.choice([-4, -3, 2, 3, 4]))
                for _ in range(3)
            ]
            grid_pairs = [(f"({px}, {py})", (px, py)) for px, py in pts]
            return MatchPairsExercise(
                grid_pairs=grid_pairs,
                title="Match the pairs",
                help_tip="Match each coordinate pair with its plotted point on the grid."
            )

    # --------------------------------------------------------------------------
    # LOGARITHMS & EXPONENTIAL FUNCTIONS
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_logarithms(difficulty: str, exercise_type: str) -> BaseExercise:
        if difficulty == "easy":
            b = random.choice([2, 3, 5, 10])
            exp = random.choice([1, 2, 3])
        elif difficulty == "medium":
            b = random.choice([2, 4, 6, 7])
            exp = random.choice([2, 3, 4])
        else:
            b = random.choice([2, 3, 5, 8])
            exp = random.choice([3, 4, 5])

        val = b ** exp

        if exercise_type == "concept":
            speech = f"Logarithms invert exponentials. Since {b}^{exp} = {val}, log_{b}({val}) is _____."
            return MultipleChoiceExercise(
                title="Logarithm concept",
                question_text="Fill in the blank [ ]",
                character_speech=speech,
                choices=[str(exp), str(b), str(val)],
                correct_choice_index=0,
                help_tip="A logarithm answers the question: to what power must the base be raised to produce the argument?"
            )

        elif exercise_type == "pattern_table":
            rows = [
                (f"{b}^1 = {b}", f"log_{b}({b}) = 1"),
                (f"{b}^2 = {b**2}", f"log_{b}({b**2}) = 2"),
                (f"{b}^{exp} = {val}", "?")
            ]
            choices = [f"log_{b}({val}) = {exp}", f"log_{val}({b}) = {exp}", f"log_{b}({exp}) = {val}"]
            return MultipleChoiceExercise(
                title="Complete the pattern",
                question_text="Select the missing logarithmic equation [ ]",
                choices=choices,
                correct_choice_index=0,
                diagram_type="pattern_table",
                diagram_data={"headers": ["Exponential", "Logarithmic"], "rows": rows},
                help_tip="Follow the row-by-row pattern connecting exponential equations to logarithmic form."
            )

        elif exercise_type == "identify_parts":
            target_part = random.choice(["base", "argument", "exponent"])
            if target_part == "base":
                correct_ans = str(b)
                distractors = [str(val), str(exp)]
            elif target_part == "argument":
                correct_ans = str(val)
                distractors = [str(b), str(exp)]
            else:
                correct_ans = str(exp)
                distractors = [str(b), str(val)]

            choices = [correct_ans] + distractors
            return MultipleChoiceExercise(
                title="Select the part",
                question_text=f"In the equation log_{b}({val}) = {exp}, select the {target_part}.",
                choices=choices,
                correct_choice_index=0,
                help_tip=f"The base is {b}, the argument inside is {val}, and the result is the exponent {exp}."
            )

        elif exercise_type == "multiple_choice":
            choices = [
                f"log_{b}({val}) = {exp}",
                f"log_{val}({b}) = {exp}",
                f"log_{b}({exp}) = {val}"
            ]
            return MultipleChoiceExercise(
                title="Select the match",
                question_text=f"Which logarithm matches {b}^{exp} = {val}?",
                choices=choices,
                correct_choice_index=0,
                help_tip=f"b^y = x translates directly to log_b(x) = y."
            )

        elif exercise_type == "type_answer":
            return TypeAnswerExercise(
                equation_format=f"log_{b}({val}) = [ ]",
                correct_answer=str(exp),
                title="Evaluate logarithm",
                help_tip=f"Determine the power needed on base {b} to equal {val}."
            )

        else:  # match_pairs
            pairs = []
            test_bases = [(2, 3), (3, 2), (5, 2)]
            for tb, te in test_bases:
                pairs.append((f"log_{tb}({tb**te})", str(te)))
            return MatchPairsExercise(
                text_pairs=pairs,
                title="Match the pairs",
                help_tip="Match each logarithm expression with its calculated exponent value."
            )

    # --------------------------------------------------------------------------
    # CYLINDER 3D GEOMETRY & VOLUME
    # --------------------------------------------------------------------------
    @staticmethod
    def _gen_cylinder(difficulty: str, exercise_type: str) -> BaseExercise:
        r = random.randint(2, 4) if difficulty == "easy" else (random.randint(3, 6) if difficulty == "medium" else random.randint(4, 8))
        h = random.randint(3, 6) if difficulty == "easy" else (random.randint(4, 8) if difficulty == "medium" else random.randint(5, 10))

        base_area = r * r
        volume = base_area * h

        if exercise_type == "cylinder_3d_base":
            return Cylinder3DExercise(
                prompt=f"Create a base area of {base_area}π",
                target_val=base_area,
                mode="base_area",
                min_slider=1,
                max_slider=8,
                initial_slider=max(1, (r + 2) % 8),
                instruction="Drag the slider to adjust the radius and match the base area."
            )

        elif exercise_type == "cylinder_3d_vol":
            return Cylinder3DExercise(
                prompt=f"Create a volume of {volume}π",
                target_val=volume,
                mode="volume",
                fixed_radius=r,
                min_slider=1,
                max_slider=10,
                initial_slider=max(1, (h + 3) % 10),
                instruction="Drag the slider to adjust height and achieve the target volume."
            )

        elif exercise_type == "cross_section":
            return MultipleChoiceExercise(
                title="Cross section",
                question_text="Select the cross section parallel to the base of the cylinder.",
                choices=["circle", "triangle", "rectangle"],
                correct_choice_index=0,
                diagram_type="cylinder_3d",
                diagram_data={"r": r, "h": h, "show_r": False, "show_h": False, "highlight_base": True},
                help_tip="A plane slicing horizontally parallel to the circular base produces a circle."
            )

        elif exercise_type == "radius_choice":
            choices = [str(r), str(h), str(r + 2)]
            return MultipleChoiceExercise(
                title="Cylinder dimensions",
                question_text="Select the length of the radius of the base.",
                choices=choices,
                correct_choice_index=0,
                diagram_type="cylinder_3d",
                diagram_data={"r": r, "h": h, "show_r": True, "show_h": True},
                help_tip="The radius is the distance from the center of the base circle to its edge."
            )

        elif exercise_type == "base_area_choice":
            choices = [f"{base_area}π", f"{2 * r}π", f"{r * h}π"]
            return MultipleChoiceExercise(
                title="Base area",
                question_text="Select the area of the base of the cylinder.",
                choices=choices,
                correct_choice_index=0,
                diagram_type="cylinder_3d",
                diagram_data={"r": r, "h": h, "show_r": True, "show_h": False, "highlight_base": True},
                help_tip="Base area formula is A = π · r²."
            )

        else:  # volume_choice
            choices = [f"{volume}π", f"{base_area + h}π", f"{r * h}π"]
            return MultipleChoiceExercise(
                title="Cylinder volume",
                question_text="Select the volume of the cylinder.",
                choices=choices,
                correct_choice_index=0,
                diagram_type="cylinder_3d",
                diagram_data={
                    "r": r,
                    "h": h,
                    "show_r": True,
                    "show_h": True,
                },
                help_tip="Volume of a cylinder is base area times height: V = (π · r²) · h."
            )
