"""XGBoost model trainer for the multi-class match outcome prediction task."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder

from training.configuration import TrainingConfig
from training.splitter import DataSplit


@dataclass
class TrainedModel:
    """All artifacts produced by a single training run."""

    booster: xgb.XGBClassifier
    label_encoder: LabelEncoder
    imputer: SimpleImputer
    feature_names: list[str]
    classes: list[str]
    best_iteration: int


class ModelTrainer:
    """Trains an XGBoost multi-class classifier on a DataSplit."""

    def train(self, split: DataSplit, config: TrainingConfig) -> TrainedModel:
        """Fit the model on train split, using val split for early stopping."""
        label_encoder = LabelEncoder()
        y_train_enc = label_encoder.fit_transform(split.y_train)
        y_val_enc = label_encoder.transform(split.y_val)

        imputer = SimpleImputer(strategy="median")
        X_train_imp = imputer.fit_transform(split.X_train)
        X_val_imp = imputer.transform(split.X_val)

        num_class = len(label_encoder.classes_)
        booster = xgb.XGBClassifier(
            objective="multi:softprob",
            num_class=num_class,
            learning_rate=config.learning_rate,
            max_depth=config.max_depth,
            n_estimators=config.n_estimators,
            subsample=config.subsample,
            colsample_bytree=config.colsample_bytree,
            random_state=config.random_seed,
            eval_metric="mlogloss",
            early_stopping_rounds=config.early_stopping_rounds,
            verbosity=0,
        )
        booster.fit(
            X_train_imp,
            y_train_enc,
            eval_set=[(X_val_imp, y_val_enc)],
            verbose=False,
        )
        best_iter = (
            int(booster.best_iteration)
            if booster.best_iteration is not None
            else config.n_estimators
        )

        return TrainedModel(
            booster=booster,
            label_encoder=label_encoder,
            imputer=imputer,
            feature_names=list(split.X_train.columns),
            classes=[str(c) for c in label_encoder.classes_],
            best_iteration=best_iter,
        )

    def predict(
        self,
        model: TrainedModel,
        X: pd.DataFrame,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Return (string_labels, probability_matrix) for a feature DataFrame."""
        X_imp = model.imputer.transform(X)
        y_enc = model.booster.predict(X_imp)
        y_prob = model.booster.predict_proba(X_imp)
        y_labels: np.ndarray = model.label_encoder.inverse_transform(y_enc)
        return y_labels, y_prob
