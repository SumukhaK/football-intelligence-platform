"""Time-weighted Dixon-Coles goals model, fitted per league (ADR 009).

Home goals ~ Poisson(lambda), away goals ~ Poisson(mu), with

    log lambda = intercept + home_advantage + attack[home] - defence[away]
    log mu     = intercept + attack[away] - defence[home]

and the Dixon-Coles factor tau adjusting 0-0, 1-0, 0-1 and 1-1. Each match
is weighted by exp(-xi * days before the fit date), and an L2 penalty pulls
every strength toward a prior: the league average (0, since the unpenalised
intercept carries the league's scoring level) for established teams,
and the average of the three weakest established teams for newcomers such as
promoted sides, mirroring the Elo rule in ADR 008.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize

HOME_GOALS = "full_time_home_goals"
AWAY_GOALS = "full_time_away_goals"
_RHO_BOUND = 0.25
_TAU_FLOOR = 1e-10
_WEAKEST_TEAMS = 3


@dataclass(frozen=True)
class GoalsModelConfig:
    """Fitting settings; ``xi`` and ``l2`` are tuned on the validation season."""

    # Tuned on 2022/23 (docs/reports/goals-model.md): a weight halves in
    # about 7.5 months.
    xi: float = 0.003
    l2: float = 8.0
    window_days: int = 1461  # four years; older matches weigh under 1/18
    newcomer_weight: float = 8.0  # weighted matches below which a team is new
    fit_rho: bool = True


@dataclass(frozen=True)
class DixonColesParams:
    """A fitted model for one league: everything needed to score a fixture."""

    competition: str
    attack: dict[str, float]
    defence: dict[str, float]
    intercept: float
    home_advantage: float
    rho: float
    newcomer_attack: float
    newcomer_defence: float
    fitted_before: str
    n_matches: int
    config: GoalsModelConfig = field(default_factory=GoalsModelConfig)

    def expected_goals(self, home_team: str, away_team: str) -> tuple[float, float]:
        """Poisson means (lambda, mu) for a fixture; unknown teams are newcomers."""
        a_home = self.attack.get(home_team, self.newcomer_attack)
        d_home = self.defence.get(home_team, self.newcomer_defence)
        a_away = self.attack.get(away_team, self.newcomer_attack)
        d_away = self.defence.get(away_team, self.newcomer_defence)
        lam = float(np.exp(self.intercept + self.home_advantage + a_home - d_away))
        mu = float(np.exp(self.intercept + a_away - d_home))
        return lam, mu

    def to_dict(self) -> dict[str, Any]:
        """JSON-ready representation."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DixonColesParams:
        """Rebuild from :meth:`to_dict` output."""
        values = dict(data)
        values["config"] = GoalsModelConfig(**values["config"])
        return cls(**values)


@dataclass(frozen=True)
class _Data:
    home: np.ndarray
    away: np.ndarray
    x: np.ndarray
    y: np.ndarray
    weight: np.ndarray
    n_teams: int


def fit_dixon_coles(
    matches: pd.DataFrame,
    before: pd.Timestamp,
    config: GoalsModelConfig | None = None,
    competition: str = "",
) -> DixonColesParams:
    """Fit on matches strictly before ``before``, within the configured window.

    ``matches`` needs ``match_date``, ``home_team``, ``away_team`` and the
    full-time goal columns. Raises ``ValueError`` if no match qualifies.
    """
    config = config or GoalsModelConfig()
    window = _window(matches, before, config.window_days)
    if window.empty:
        raise ValueError(f"No matches before {before.date()} to fit {competition}")
    teams = sorted(set(window["home_team"]) | set(window["away_team"]))
    data = _encode(window, teams, before, config.xi)

    zeros = np.zeros(2 * len(teams))
    first = _optimise(data, zeros, config, start=None)
    exposure = np.bincount(data.home, data.weight, len(teams)) + np.bincount(
        data.away, data.weight, len(teams)
    )
    new = exposure < config.newcomer_weight
    attack, defence = first[: len(teams)], first[len(teams) : 2 * len(teams)]
    newcomer = _weakest_average(attack, defence, ~new)
    solution = first
    if new.any():
        prior = zeros.copy()
        prior[: len(teams)][new] = newcomer[0]
        prior[len(teams) :][new] = newcomer[1]
        solution = _optimise(data, prior, config, start=first)

    n = len(teams)
    return DixonColesParams(
        competition=competition,
        attack=dict(zip(teams, map(float, solution[:n]), strict=True)),
        defence=dict(zip(teams, map(float, solution[n : 2 * n]), strict=True)),
        intercept=float(solution[2 * n]),
        home_advantage=float(solution[2 * n + 1]),
        rho=float(solution[2 * n + 2]),
        newcomer_attack=float(newcomer[0]),
        newcomer_defence=float(newcomer[1]),
        fitted_before=str(before.date()),
        n_matches=int(len(window)),
        config=config,
    )


def _window(matches: pd.DataFrame, before: pd.Timestamp, days: int) -> pd.DataFrame:
    dates = pd.to_datetime(matches["match_date"])
    start = before - pd.Timedelta(days=days)
    return matches[(dates < before) & (dates >= start)]


def _encode(
    window: pd.DataFrame, teams: list[str], before: pd.Timestamp, xi: float
) -> _Data:
    index = {team: i for i, team in enumerate(teams)}
    age = (before - pd.to_datetime(window["match_date"])).dt.days.to_numpy()
    return _Data(
        home=window["home_team"].map(index).to_numpy(),
        away=window["away_team"].map(index).to_numpy(),
        x=window[HOME_GOALS].to_numpy(dtype=float),
        y=window[AWAY_GOALS].to_numpy(dtype=float),
        weight=np.exp(-xi * age),
        n_teams=len(teams),
    )


def _weakest_average(
    attack: np.ndarray, defence: np.ndarray, established: np.ndarray
) -> tuple[float, float]:
    """Mean attack and defence of the weakest established teams."""
    if not established.any():
        return 0.0, 0.0
    # A higher defence value means fewer goals conceded.
    strength = attack + defence
    order = np.argsort(np.where(established, strength, np.inf))
    weakest = order[: min(_WEAKEST_TEAMS, int(established.sum()))]
    return float(attack[weakest].mean()), float(defence[weakest].mean())


def _optimise(
    data: _Data, prior: np.ndarray, config: GoalsModelConfig, start: np.ndarray | None
) -> np.ndarray:
    n = data.n_teams
    mean_goals = (data.weight @ (data.x + data.y)) / (2 * data.weight.sum())
    initial = [np.log(max(mean_goals, 0.1)), 0.25, 0.0]
    x0 = start if start is not None else np.concatenate([prior, initial])
    rho_bound = (-_RHO_BOUND, _RHO_BOUND) if config.fit_rho else (0.0, 0.0)
    bounds = [(None, None)] * (2 * n + 2) + [rho_bound]
    result = minimize(
        _objective,
        x0,
        args=(data, prior, config.l2),
        jac=True,
        method="L-BFGS-B",
        bounds=bounds,
    )
    return np.asarray(result.x)


def _objective(
    theta: np.ndarray, data: _Data, prior: np.ndarray, l2: float
) -> tuple[float, np.ndarray]:
    """Penalised weighted negative log-likelihood and its gradient."""
    n = data.n_teams
    attack, defence = theta[:n], theta[n : 2 * n]
    intercept, home_adv, rho = theta[2 * n], theta[2 * n + 1], theta[2 * n + 2]
    log_lam = intercept + home_adv + attack[data.home] - defence[data.away]
    log_mu = intercept + attack[data.away] - defence[data.home]
    lam, mu = np.exp(log_lam), np.exp(log_mu)
    tau, d_lam, d_mu, d_rho = _tau_terms(data.x, data.y, lam, mu, rho)

    w = data.weight
    loglik = w * (data.x * log_lam - lam + data.y * log_mu - mu + np.log(tau))
    # Derivatives of each match's log-likelihood w.r.t. log lambda and log mu.
    g_lam = w * (data.x - lam + lam * d_lam)
    g_mu = w * (data.y - mu + mu * d_mu)

    grad = np.zeros_like(theta)
    grad[:n] -= np.bincount(data.home, g_lam, n) + np.bincount(data.away, g_mu, n)
    grad[n : 2 * n] += np.bincount(data.away, g_lam, n) + np.bincount(
        data.home, g_mu, n
    )
    grad[2 * n] = -(g_lam.sum() + g_mu.sum())
    grad[2 * n + 1] = -g_lam.sum()
    grad[2 * n + 2] = -(w * d_rho).sum()

    offset = theta[: 2 * n] - prior
    grad[: 2 * n] += 2 * l2 * offset
    return float(-loglik.sum() + l2 * (offset**2).sum()), grad


def _tau_terms(
    x: np.ndarray, y: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """tau and the derivatives of log tau w.r.t. lambda, mu and rho."""
    tau = np.ones_like(lam)
    d_lam, d_mu, d_rho = (np.zeros_like(lam) for _ in range(3))
    s00 = (x == 0) & (y == 0)
    s01 = (x == 0) & (y == 1)
    s10 = (x == 1) & (y == 0)
    s11 = (x == 1) & (y == 1)
    tau[s00] = 1 - lam[s00] * mu[s00] * rho
    tau[s01] = 1 + lam[s01] * rho
    tau[s10] = 1 + mu[s10] * rho
    tau[s11] = 1 - rho
    tau = np.maximum(tau, _TAU_FLOOR)
    d_lam[s00] = -mu[s00] * rho / tau[s00]
    d_mu[s00] = -lam[s00] * rho / tau[s00]
    d_rho[s00] = -lam[s00] * mu[s00] / tau[s00]
    d_lam[s01] = rho / tau[s01]
    d_rho[s01] = lam[s01] / tau[s01]
    d_mu[s10] = rho / tau[s10]
    d_rho[s10] = mu[s10] / tau[s10]
    d_rho[s11] = -1 / tau[s11]
    return tau, d_lam, d_mu, d_rho
