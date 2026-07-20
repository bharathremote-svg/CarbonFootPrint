"""
train.py

Generates a synthetic dataset from the deterministic emissions engine
(in `calculations.py`) and trains a RandomForestRegressor to predict
annual carbon footprint given user inputs. Saves a joblib artifact to
`models/model.pkl` containing the model, scaler, and feature names.
"""

import os
import random
import numpy as np
import pandas as pd
from joblib import dump

from calculations import (
    UserInputs, total_footprint, VEHICLE_KG_PER_KM, DIET_BASE_T,
    SHOPPING_BASE_T, FOOD_WASTE_MULTIPLIER,
)
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

FEATURE_NAMES = [
    "electricity_kwh",
    "renewable_pct",
    "gas_m3",
    "car_km",
    "public_transport_km",
    "short_haul_flights",
    "long_haul_flights",
    "vehicle_factor",
    "diet_value",
    "food_waste_mult",
    "shopping_value",
    "clothing_items",
    "streaming_hours",
]

RNG = np.random.default_rng(42)


def sample_input():
    u = UserInputs()
    u.electricity_kwh = float(RNG.integers(0, 1001))
    u.renewable_pct = float(RNG.integers(0, 101))
    u.gas_m3 = float(RNG.integers(0, 201))
    # transport
    u.vehicle_type = RNG.choice(list(VEHICLE_KG_PER_KM.keys()))
    u.car_km = float(RNG.integers(0, 3001))
    u.public_transport_km = float(RNG.integers(0, 1001))
    # flights
    u.short_haul_flights = int(RNG.integers(0, 7))
    u.long_haul_flights = int(RNG.integers(0, 5))
    # diet
    u.diet_type = RNG.choice(list(DIET_BASE_T.keys()))
    u.food_waste = RNG.choice(list(FOOD_WASTE_MULTIPLIER.keys()))
    # lifestyle
    u.shopping_habits = RNG.choice(list(SHOPPING_BASE_T.keys()))
    u.clothing_items = int(RNG.integers(0, 61))
    u.streaming_hours = float(RNG.integers(0, 13))
    return u


def extract_features(u: UserInputs):
    vehicle_factor = VEHICLE_KG_PER_KM.get(u.vehicle_type, 0.0)
    diet_value = DIET_BASE_T.get(u.diet_type, sum(DIET_BASE_T.values())/len(DIET_BASE_T))
    food_mult = FOOD_WASTE_MULTIPLIER.get(u.food_waste, 1.0)
    shopping_value = SHOPPING_BASE_T.get(u.shopping_habits, SHOPPING_BASE_T["Medium"])

    return [
        u.electricity_kwh,
        u.renewable_pct,
        u.gas_m3,
        u.car_km,
        u.public_transport_km,
        u.short_haul_flights,
        u.long_haul_flights,
        vehicle_factor,
        diet_value,
        food_mult,
        shopping_value,
        u.clothing_items,
        u.streaming_hours,
    ]


def main():
    N = 3000
    X = []
    y = []
    for _ in range(N):
        u = sample_input()
        X.append(extract_features(u))
        y.append(total_footprint(u))

    X = np.array(X)
    y = np.array(y)

    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["carbon_footprint"] = y
    df.to_csv("models/synthetic_dataset.csv", index=False)

    # Train model pipeline
    scaler = StandardScaler()
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    pipe = Pipeline([("scaler", scaler), ("model", model)])
    pipe.fit(X, y)

    artifact = {
        "pipeline": pipe,
        "feature_names": FEATURE_NAMES,
    }
    os.makedirs("models", exist_ok=True)
    dump(artifact, "models/model.pkl")
    print("Saved models/model.pkl and synthetic dataset (models/synthetic_dataset.csv)")


if __name__ == "__main__":
    main()
