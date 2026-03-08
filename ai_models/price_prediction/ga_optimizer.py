"""
Genetic Algorithm hyper-parameter optimisation for the LSTM price predictor.
Uses DEAP to evolve: hidden_size, num_layers, learning_rate, batch_size, epochs.
"""

import os
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from deap import base, creator, tools, algorithms

from .model import PriceLSTM

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# ---------------------------------------------------------------------------
# Evaluation helper — train a model with given hyper-parameters
# ---------------------------------------------------------------------------

def _train_and_evaluate(X_train, y_train, X_val, y_val, params):
    """
    Train PriceLSTM with `params` dict and return validation RMSE.
    params keys: hidden_size, num_layers, lr, batch_size, epochs
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = PriceLSTM(
        input_size=X_train.shape[2],
        hidden_size=params["hidden_size"],
        num_layers=params["num_layers"],
        dropout=0.2,
    ).to(device)

    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=params["lr"])

    train_ds = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32),
    )
    loader = DataLoader(train_ds, batch_size=params["batch_size"], shuffle=True)

    model.train()
    for _ in range(params["epochs"]):
        for xb, yb in loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()

    # Validation
    model.eval()
    with torch.no_grad():
        preds = model(torch.tensor(X_val, dtype=torch.float32).to(device)).cpu().numpy()
    rmse = float(np.sqrt(np.mean((preds - y_val) ** 2)))
    return rmse, model


# ---------------------------------------------------------------------------
# DEAP GA setup
# ---------------------------------------------------------------------------

# Search space boundaries
SPACE = {
    "hidden_size": (32, 128),
    "num_layers":  (1, 3),
    "lr":          (1e-4, 1e-2),
    "batch_size":  (16, 64),
    "epochs":      (20, 80),
}


def _decode_individual(ind):
    """Map a float-gene individual [0-1]^5 into concrete hyper-parameters."""
    g = ind
    return {
        "hidden_size": int(SPACE["hidden_size"][0] + g[0] * (SPACE["hidden_size"][1] - SPACE["hidden_size"][0])),
        "num_layers":  int(SPACE["num_layers"][0]  + g[1] * (SPACE["num_layers"][1]  - SPACE["num_layers"][0])),
        "lr":          SPACE["lr"][0]          + g[2] * (SPACE["lr"][1]          - SPACE["lr"][0]),
        "batch_size":  int(SPACE["batch_size"][0]  + g[3] * (SPACE["batch_size"][1]  - SPACE["batch_size"][0])),
        "epochs":      int(SPACE["epochs"][0]      + g[4] * (SPACE["epochs"][1]      - SPACE["epochs"][0])),
    }


def run_ga(X_train, y_train, X_val, y_val,
           population_size=8, generations=5, verbose=True):
    """
    Run a small GA to find the best LSTM hyper-parameters.
    Returns best_params dict and the best trained model.
    """

    # DEAP creator setup (avoid re-registration warnings)
    if not hasattr(creator, "FitnessMin"):
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_float, n=5)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind):
        params = _decode_individual(ind)
        rmse, _ = _train_and_evaluate(X_train, y_train, X_val, y_val, params)
        return (rmse,)

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.2, indpb=0.3)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=population_size)

    # Clamp genes to [0, 1] after crossover / mutation
    def clamp(ind):
        for i in range(len(ind)):
            ind[i] = max(0.0, min(1.0, ind[i]))
        return ind

    best_rmse = float("inf")
    best_params = None
    best_model = None

    for gen in range(generations):
        # Evaluate
        fitnesses = list(map(toolbox.evaluate, pop))
        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        # Track best
        for ind in pop:
            if ind.fitness.values[0] < best_rmse:
                best_rmse = ind.fitness.values[0]
                best_params = _decode_individual(ind)

        if verbose:
            fits = [ind.fitness.values[0] for ind in pop]
            print(f"  GA Gen {gen+1}/{generations}  best_rmse={min(fits):.5f}  avg={np.mean(fits):.5f}")

        # Selection + variation
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        for c1, c2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                toolbox.mate(c1, c2)
                del c1.fitness.values
                del c2.fitness.values
        for mutant in offspring:
            if random.random() < 0.3:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        for ind in offspring:
            clamp(ind)

        pop[:] = offspring

    # Re-train final best model to return it
    if verbose:
        print(f"  GA finished — best params: {best_params}  RMSE={best_rmse:.5f}")
    _, best_model = _train_and_evaluate(X_train, y_train, X_val, y_val, best_params)
    return best_params, best_model, best_rmse
