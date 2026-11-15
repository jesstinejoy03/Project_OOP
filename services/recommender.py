"""CopingRecommender: ranks exercises using the user's own past ratings."""
from typing import Dict, List, Optional, Sequence, Tuple

from models.exercise import Exercise, default_exercises
from services.database import DatabaseManager

PRIOR_RATING = 3.0   # assumed rating for an exercise the user has never tried
PRIOR_WEIGHT = 2     # how many "virtual" ratings the prior is worth
MIN_RATING, MAX_RATING = 1, 5

# exercise name -> (sum of the ratings, how many ratings)
RatingStats = Dict[str, Tuple[int, int]]


class CopingRecommender:
    """Suggests exercises that target an emotion, best-rated first.

    score = (sum_of_ratings + PRIOR_RATING * PRIOR_WEIGHT) / (count + PRIOR_WEIGHT)
    so unrated exercises start neutral and move up or down as the user rates them.
    """

    def __init__(self, database: DatabaseManager,
                 exercises: Optional[Sequence[Exercise]] = None):
        self._db = database
        self._exercises: List[Exercise] = (
            list(exercises) if exercises is not None else default_exercises())

    @property
    def exercises(self) -> List[Exercise]:
        return list(self._exercises)

    def candidates(self, emotion: str) -> List[Exercise]:
        matches = [e for e in self._exercises if e.helps_with(emotion)]
        return matches or list(self._exercises)

    def score(self, exercise: Exercise, stats: RatingStats) -> float:
        total, count = stats.get(exercise.name, (0, 0))
        return (total + PRIOR_RATING * PRIOR_WEIGHT) / (count + PRIOR_WEIGHT)

    def recommend(self, emotion: str, limit: int = 3) -> List[Exercise]:
        stats = self._db.rating_stats(emotion)
        ranked = sorted(self.candidates(emotion), key=lambda e: self.score(e, stats), reverse=True)
        return ranked[:limit]

    def record_rating(self, exercise: Exercise, emotion: Optional[str],
                      rating: int) -> None:
        """Store a rating against every emotion it is evidence for.

        Ratings are looked up per emotion, so a rating filed under an emotion the
        exercise does not target - for example "general" when the user starts an
        exercise from the unfiltered toolkit - would never be read again. When
        the emotion does not apply, credit each emotion the exercise helps with.
        """
        if not MIN_RATING <= rating <= MAX_RATING:
            raise ValueError(f"Rating must be between {MIN_RATING} and {MAX_RATING}.")
        if emotion and exercise.helps_with(emotion):
            targets: List[str] = [emotion]
        else:
            targets = list(exercise.target_emotions)
        for target in targets:
            self._db.add_rating(exercise.name, target, rating)
