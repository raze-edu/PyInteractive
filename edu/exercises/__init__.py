"""Exercises package for EduMath."""
from .base import BaseExercise
from .number_line import NumberLineExercise
from .equation_slots import EquationSlotsExercise
from .match_pairs import MatchPairsExercise
from .fraction_visual import FractionVisualExercise
from .geometry_cut import GeometryCutExercise
from .dot_plot import DotPlotExercise
from .multiple_choice import MultipleChoiceExercise
from .type_answer import TypeAnswerExercise

__all__ = [
    "BaseExercise",
    "NumberLineExercise",
    "EquationSlotsExercise",
    "MatchPairsExercise",
    "FractionVisualExercise",
    "GeometryCutExercise",
    "DotPlotExercise",
    "MultipleChoiceExercise",
    "TypeAnswerExercise"
]
