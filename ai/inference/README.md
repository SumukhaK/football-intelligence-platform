# inference

Loads a trained model and returns structured match predictions.

## Modules

| Module | Responsibility |
|---|---|
| `predictor.py` | `MatchPredictor` — wraps `TrainedModel`; `MatchPrediction` dataclass |

## Usage

```python
from pathlib import Path
from inference.predictor import MatchPredictor
import pandas as pd

predictor = MatchPredictor.from_path(Path("models/latest/model.joblib"))

features = pd.DataFrame([{
    "home_elo": 1550.0,
    "away_elo": 1480.0,
    # ... all 42 feature columns
}])

result = predictor.predict(features, home_team="Arsenal", away_team="Chelsea")
print(result.predicted_result)        # "H", "D", or "A"
print(result.probability_home)        # float in [0, 1]
```

## Contract

- `predict()` raises `ValueError` if any required feature column is missing.
- Probabilities always sum to 1.0 (softmax output from XGBoost).
- `predicted_result` is always one of the classes the model was trained on.
