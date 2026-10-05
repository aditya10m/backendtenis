from app.analytics.config import technique_weights, movement_weights, serve_weights

consistency_weights = {
    'preparation_quality': 0.25,
    'follow_through': 0.25,
    'balance_score': 0.25,
    'head_stability': 0.25,
}


class ScoringEngine:
    """Deterministic scoring engine. No randomness, no LLM-generated scores."""

    def _calc(self, metrics: dict, weights: dict) -> float | None:
        total = 0.0
        weight_sum = 0.0
        for key, weight in weights.items():
            if key in metrics and metrics[key] is not None:
                value = max(0.0, min(100.0, float(metrics[key])))
                total += value * weight
                weight_sum += weight
        if weight_sum == 0:
            return None
        return round(total / weight_sum, 1)

    def calculate_technique_score(self, metrics: dict) -> float | None:
        return self._calc(metrics, technique_weights)

    def calculate_movement_score(self, metrics: dict) -> float | None:
        return self._calc(metrics, movement_weights)

    def calculate_serve_score(self, metrics: dict) -> float | None:
        return self._calc(metrics, serve_weights)

    def calculate_consistency_score(self, metrics: dict) -> float | None:
        return self._calc(metrics, consistency_weights)

    def calculate_overall_score(
        self,
        technique: float | None,
        movement: float | None,
        serve: float | None,
        consistency: float | None,
    ) -> float | None:
        weighted = [
            (technique, 0.30),
            (movement, 0.25),
            (serve, 0.25),
            (consistency, 0.20),
        ]
        total = 0.0
        weight_sum = 0.0
        for score, weight in weighted:
            if score is not None:
                total += score * weight
                weight_sum += weight
        if weight_sum == 0:
            return None
        return round(total / weight_sum, 1)
