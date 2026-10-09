"""Curriculum and lesson definitions reproducing the exercises from the example snapshots."""
from typing import List
from .exercises import (
    BaseExercise,
    NumberLineExercise,
    EquationSlotsExercise,
    MatchPairsExercise,
    FractionVisualExercise,
    GeometryCutExercise,
    DotPlotExercise,
    MultipleChoiceExercise,
    TypeAnswerExercise,
    CoordinateGridExercise,
    Cylinder3DExercise
)

def create_default_curriculum() -> List[BaseExercise]:
    """Generates the full curriculum sequence matching all example exercises."""
    return [
        # 1. Answer on the line (snapshot 1)
        NumberLineExercise(
            title="Answer on the line",
            equation_format="210 - 60 - 15 = [ ]",
            correct_value=135,
            ticks=[0, 135, 270, 405, 540, 675, 810],
            initial_tick_index=0,
            help_tip="Subtract step-by-step: first subtract the tens, then subtract the remaining ones. Then slide the marker to your answer on the line."
        ),
        
        # 2. Complete the equation: target 275 (snapshot 2, 3)
        EquationSlotsExercise(
            title="Complete the equation",
            target_equation="[ ] = 275",
            target_value=275,
            num_slots=5,
            bank_tokens=[
                ("-", True),
                ("-", True),
                ("5", False),
                ("350", False),
                ("10", False),
                ("70", False),
                ("-", True),
            ],
            help_tip="Pick a large starting number tile, then subtract smaller values from the bank to reach the target total."
        ),

        # 3. Complete the equation: target 248 (snapshot 7)
        EquationSlotsExercise(
            title="Complete the equation",
            target_equation="248 = [ ]",
            target_value=248,
            num_slots=5,
            bank_tokens=[
                ("400", False),
                ("-", True),
                ("150", False),
                ("-", True),
                ("2", False),
                ("+", True),
                ("6", False)
            ],
            help_tip="Choose numbers from the tile bank that subtract down to the target total. Watch the minus signs!"
        ),

        # 4. Answer on the line (snapshot 8)
        NumberLineExercise(
            title="Answer on the line",
            equation_format="[ ] = 400 - 10 - 5",
            correct_value=385,
            ticks=[0, 385, 770, 1155, 1540, 1925, 2310],
            initial_tick_index=0,
            help_tip="Calculate the subtractions from left to right, then find and mark that position on the number line."
        ),

        # 5. Type the answer (snapshot 9)
        TypeAnswerExercise(
            title="Type the answer",
            equation_format="400 - 20 - 1 = [ ]",
            correct_answer="379",
            help_tip="Break the calculation into steps, or open the Toolkit calculator on the bottom left for your scratch work."
        ),

        # 6. Match the pairs: fraction multiplication (snapshots 10 - 13)
        MatchPairsExercise(
            title="Match the pairs",
            pairs=[
                ("2/3 · 2/2", 6, 4),  # 4/6
                ("1/3 · 2/2", 6, 2),  # 2/6
                ("1/2 · 2/2", 4, 2),  # 2/4
            ],
            help_tip="Match the fraction multiplication expressions with their circle models."
        ),

        # 7. Show this another way: simplified fraction (snapshot 15)
        FractionVisualExercise(
            mode="type_equivalent",
            prompt_fraction="6/8",
            target_slices=8,
            target_shaded=6,
            initial_shaded=6,
            accepted_fractions=["3/4", "6/8"],
            title="Show this another way",
            help_tip="Count the shaded slices out of the total slices, then reduce the fraction by dividing both top and bottom by their common factor."
        ),

        # 8. Select the answer: fraction visual (snapshot 17)
        MultipleChoiceExercise(
            title="Select the answer",
            question_text="1/2 · 1/1 = [ ]",
            choices=["1/2", "2/2"],
            correct_choice_index=0,
            diagram_type="visual_fractions",
            help_tip="Multiplying by 1/1 (one whole) leaves the fraction unchanged."
        ),

        # 9. Show this another way: slice pie (snapshot 18)
        FractionVisualExercise(
            mode="interactive_slices",
            prompt_fraction="2/6",
            target_slices=3,
            target_shaded=1,
            title="Show this another way",
            help_tip="Simplify the given fraction to find the equivalent portion of the circle to shade."
        ),

        # 10. Fill in the blank: right triangle area (snapshot 19, 20)
        MultipleChoiceExercise(
            title="Fill in the blank",
            question_text="The area of a right triangle is _____ the rectangle's area.",
            character_speech="The area of a right triangle is _____ the rectangle's area.",
            choices=["half of", "twice"],
            correct_choice_index=0,
            diagram_type="grid_rectangle",
            diagram_data={"w": 6, "h": 4},
            help_tip="Any rectangle cut along its diagonal splits into two equal right triangles."
        ),

        # 11. Create the shapes: right triangles cut (snapshot 21, 23)
        GeometryCutExercise(
            title="Create the shapes",
            grid_size=(8, 8),
            rect_bounds=(2, 2, 4, 4),
            target_shape_name="two right triangles",
            help_tip="Drag the cutting line endpoints to opposite corners (diagonal) to make two right triangles!"
        ),

        # 12. Select the mode: dot plot (snapshot 25)
        DotPlotExercise(
            mode_type="select",
            ticks=[10, 11, 12, 13, 14, 15],
            target_mode=14,
            initial_counts={10: 1, 11: 2, 12: 1, 13: 1, 14: 3, 15: 0},
            choices=[11, 12, 14],
            help_tip="Look for the number on the axis with the highest stack of dots."
        ),

        # 13. Plot the data with mode = -1 (snapshot 28)
        DotPlotExercise(
            mode_type="plot",
            ticks=[-2, -1, 0, 1, 2, 3],
            target_mode=-1,
            initial_counts={-2: 1, -1: 1, 0: 1, 1: 1, 2: 1, 3: 0},
            help_tip="Add dots to make the target number the column with the highest stack in the plot."
        ),

        # 14. Plot the data with mode = 3 (snapshot 29)
        DotPlotExercise(
            mode_type="plot",
            ticks=[0, 1, 2, 3, 4, 5],
            target_mode=3,
            initial_counts={0: 0, 1: 1, 2: 1, 3: 1, 4: 1, 5: 0},
            help_tip="Add dots to make the target number the column with the highest stack in the plot."
        ),

        # 15. Fill in the blank: algebra distribution (snapshot 30, 31)
        MultipleChoiceExercise(
            title="Fill in the blank",
            question_text="6(x - 1) = [ ] - 6",
            choices=["-6x - 6", "6x + 6", "6x"],
            correct_choice_index=2,
            help_tip="Apply the distributive property: multiply the factor outside by each term inside the parentheses: a(b - c) = ab - ac."
        ),

        # 16. Fill in the blank: algebra distribution (snapshot 32)
        MultipleChoiceExercise(
            title="Fill in the blank",
            question_text="7(x + 4) = 7x + [ ]",
            choices=["28", "-28", "4"],
            correct_choice_index=0,
            help_tip="Apply the distributive property: multiply the factor outside by each term inside the parentheses: a(b + c) = ab + ac."
        ),

        # 17. Place the point at (3, 5) on coordinate grid (todo snapshots)
        CoordinateGridExercise(
            prompt="Place the point at (3, 5)",
            target_points=[(3, 5)],
            mode="place_point",
            x_range=(-6, 6),
            y_range=(-6, 6),
            instruction="Click or drag to place the point at (3, 5) on the coordinate grid."
        ),

        # 18. Create a graph with points at... (todo snapshots)
        CoordinateGridExercise(
            prompt="Create a graph with points at:",
            target_points=[(-2, 0), (0, 1), (2, 2), (4, 3)],
            mode="create_graph",
            x_range=(-6, 6),
            y_range=(-6, 6),
            table_data=[(-2, 0), (0, 1), (2, 2), (4, 3)],
            instruction="Plot all points from the table and adjust them on the graph."
        ),

        # 19. Show x on the line from 2D coordinate grid (todo snapshots)
        NumberLineExercise(
            title="Show x on the line",
            equation_format="Show x on the line",
            correct_value=-4,
            ticks=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
            initial_tick_index=5,
            prompt_grid_point=(-4, 2),
            highlight_coord="x",
            help_tip="Look at the x-axis projection of the plotted grid point and slide the marker to -4."
        ),

        # 20. Enter the x-value with on-screen keypad (todo snapshots)
        TypeAnswerExercise(
            title="Enter the x-value",
            equation_format="x = [ ]",
            correct_answer="3",
            prompt_coord=(3, -2),
            highlight_coord="x",
            show_keypad=True,
            help_tip="The first number in the coordinate pair (x, y) is the x-value."
        ),

        # 21. Match the pairs: Coordinate Grid to coordinate pair (todo snapshots)
        MatchPairsExercise(
            title="Match the pairs",
            grid_pairs=[
                ("(3, 4)", (3, 4)),
                ("(-2, 3)", (-2, 3)),
                ("(1, -3)", (1, -3))
            ],
            help_tip="Match each coordinate notation with its plotted location on the grid."
        ),

        # 22. Logarithm Concept speech bubble (todo snapshots)
        MultipleChoiceExercise(
            title="Logarithm concept",
            question_text="Fill in the blank [ ]",
            character_speech="Logarithms undo exponentiation! Since 2³ = 8, then log₂(8) is _____.",
            choices=["3", "2", "8"],
            correct_choice_index=0,
            help_tip="A logarithm outputs the exponent required to produce the value from the base."
        ),

        # 23. Complete the pattern table: Exponential to Logarithmic (todo snapshots)
        MultipleChoiceExercise(
            title="Complete the pattern",
            question_text="Select the missing logarithmic equation [ ]",
            choices=["log_7(49) = 2", "log_2(49) = 7", "log_7(2) = 49"],
            correct_choice_index=0,
            diagram_type="pattern_table",
            diagram_data={
                "headers": ["Exponential", "Logarithmic"],
                "rows": [
                    ("7¹ = 7", "log_7(7) = 1"),
                    ("7² = 49", "?")
                ]
            },
            help_tip="Observe how base 7 and exponent 2 translate to log_7(49) = 2."
        ),

        # 24. Create a base area: Interactive 3D Cylinder (todo snapshots)
        Cylinder3DExercise(
            prompt="Create a base area of 9π",
            target_val=9,
            mode="base_area",
            min_slider=1,
            max_slider=8,
            initial_slider=2,
            instruction="Adjust the slider until radius r produces a base area of 9π."
        ),

        # 25. Create a volume: Interactive 3D Cylinder (todo snapshots)
        Cylinder3DExercise(
            prompt="Create a volume of 36π",
            target_val=36,
            mode="volume",
            fixed_radius=3,
            min_slider=1,
            max_slider=10,
            initial_slider=2,
            instruction="Adjust the height slider to achieve a volume of 36π (since π · 3² · h = 36π)."
        ),

        # 26. Cross section of a cylinder (todo snapshots)
        MultipleChoiceExercise(
            title="Cross section",
            question_text="Select the cross section that is parallel to the base of the cylinder.",
            choices=["circle", "triangle", "rectangle"],
            correct_choice_index=0,
            diagram_type="cylinder_3d",
            diagram_data={"r": 3, "h": 5, "show_r": False, "show_h": False, "highlight_base": True},
            help_tip="Slicing a cylinder parallel to its circular base yields a congruent circle."
        ),
    ]
