"""
calculations.py
================
Pure-Python emissions engine for Carbon Footprint Calculator using AI.

No Streamlit / UI imports live here on purpose - this module can be
unit tested completely on its own (see the __main__ block at the
bottom, or tests/test_calculations.py).
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# EMISSION FACTORS  (tonnes CO2e, calibrated to give sensible round numbers)
# ---------------------------------------------------------------------------

ELECTRICITY_KG_PER_KWH = 0.35          # grid-average carbon intensity
GAS_KG_PER_M3 = 1.6

VEHICLE_KG_PER_KM = {
    "None": 0.0,
    "Electric": 0.05,
    "Hybrid": 0.10,
    "Petrol": 0.192,
    "Diesel": 0.171,
}
PUBLIC_TRANSPORT_KG_PER_KM = 0.07

SHORT_HAUL_FLIGHT_T = 0.15   # tonnes CO2e per short-haul (<3h) return flight
LONG_HAUL_FLIGHT_T = 0.60    # tonnes CO2e per long-haul (>3h) return flight

DIET_BASE_T = {
    "Vegan": 1.5,
    "Vegetarian": 1.7,
    "Pescatarian": 1.9,
    "Mixed": 2.5,
    "High Meat": 3.3,
}
FOOD_WASTE_MULTIPLIER = {"Low": 0.90, "Medium": 1.00, "High": 1.15}

SHOPPING_BASE_T = {"Low": 0.30, "Medium": 0.72, "High": 1.10, "Very High": 1.50}
CLOTHING_T_PER_ITEM = 0.02
STREAMING_T_PER_HOUR_PER_DAY = 0.02

# Reference points used to grade the footprint
MAX_FOOTPRINT_REFERENCE = 14.6     # ~ tonnes/year used as the "0 score" anchor
GLOBAL_AVG_T = 4.7
EU_AVG_T = 6.8
US_AVG_T = 14.9

FOOTPRINT_BADGES = [
    (3.0, "Low Footprint"),
    (5.0, "Moderate Footprint"),
    (8.0, "High Footprint"),
    (float("inf"), "Very High Footprint"),
]

ECO_SCORE_BANDS = [
    (80, "Green Citizen"),
    (60, "Sustainable User"),
    (40, "Needs Improvement"),
    (0, "High Carbon User"),
]

CATEGORY_TIPS = {
    "Diet": "Incorporate more plant-based meals.",
    "Home Energy": "Improve insulation or switch to renewables.",
    "Lifestyle": "Buy second-hand or reduce overall consumption.",
    "Transport": "Use public transport more frequently or bike.",
}


# ---------------------------------------------------------------------------
# INPUT MODEL
# ---------------------------------------------------------------------------
@dataclass
class UserInputs:
    # Home Energy
    electricity_kwh: float = 250
    renewable_pct: float = 20
    gas_m3: float = 50
    # Transport
    vehicle_type: str = "Petrol"
    car_km: float = 300
    public_transport_km: float = 50
    # Flights
    short_haul_flights: int = 0
    long_haul_flights: int = 0
    # Diet
    diet_type: str = "Mixed"
    food_waste: str = "Medium"
    # Lifestyle
    shopping_habits: str = "Medium"
    clothing_items: int = 12
    streaming_hours: float = 2


# ---------------------------------------------------------------------------
# CORE CALCULATIONS
# ---------------------------------------------------------------------------
def home_energy_t(u: UserInputs) -> float:
    elec_t = u.electricity_kwh * 12 * ELECTRICITY_KG_PER_KWH / 1000
    elec_t *= (1 - u.renewable_pct / 100)
    gas_t = u.gas_m3 * 12 * GAS_KG_PER_M3 / 1000
    return elec_t + gas_t


def transport_t(u: UserInputs) -> float:
    vehicle_factor = VEHICLE_KG_PER_KM.get(u.vehicle_type, 0.0)
    car_t = u.car_km * 12 * vehicle_factor / 1000
    public_t = u.public_transport_km * 12 * PUBLIC_TRANSPORT_KG_PER_KM / 1000
    flights_t = (u.short_haul_flights * SHORT_HAUL_FLIGHT_T
                 + u.long_haul_flights * LONG_HAUL_FLIGHT_T)
    return car_t + public_t + flights_t


def diet_t(u: UserInputs) -> float:
    base = DIET_BASE_T.get(u.diet_type, DIET_BASE_T["Mixed"])
    mult = FOOD_WASTE_MULTIPLIER.get(u.food_waste, 1.0)
    return base * mult


def lifestyle_t(u: UserInputs) -> float:
    base = SHOPPING_BASE_T.get(u.shopping_habits, SHOPPING_BASE_T["Medium"])
    clothing = u.clothing_items * CLOTHING_T_PER_ITEM
    streaming = u.streaming_hours * STREAMING_T_PER_HOUR_PER_DAY
    return base + clothing + streaming


def emissions_breakdown(u: UserInputs) -> dict:
    """Returns {category: tonnes} for the 4 headline categories."""
    return {
        "Home Energy": round(home_energy_t(u), 2),
        "Transport": round(transport_t(u), 2),
        "Diet": round(diet_t(u), 2),
        "Lifestyle": round(lifestyle_t(u), 2),
    }


def total_footprint(u: UserInputs) -> float:
    breakdown = emissions_breakdown(u)
    return round(sum(breakdown.values()), 2)


def footprint_badge(total: float) -> str:
    for threshold, label in FOOTPRINT_BADGES:
        if total < threshold:
            return label
    return FOOTPRINT_BADGES[-1][1]


def eco_score(total: float) -> int:
    score = 100 - (total / MAX_FOOTPRINT_REFERENCE) * 100
    return max(0, min(100, round(score)))


def eco_score_label(score: int) -> str:
    for threshold, label in ECO_SCORE_BANDS:
        if score >= threshold:
            return label
    return ECO_SCORE_BANDS[-1][1]


def comparison_data(total: float) -> list:
    """(label, tonnes) pairs used for the 'How do you compare?' bar chart."""
    return [
        ("You", total),
        ("Global Avg", GLOBAL_AVG_T),
        ("EU Avg", EU_AVG_T),
        ("US Avg", US_AVG_T),
    ]


# ---------------------------------------------------------------------------
# RECOMMENDATION ENGINE
# ---------------------------------------------------------------------------
@dataclass
class Recommendation:
    category: str
    title: str
    description: str
    savings_t: float


def generate_recommendations(u: UserInputs, top_n: int = 3) -> list:
    candidates = []

    d_t = diet_t(u)
    if u.diet_type in ("Mixed", "High Meat"):
        vegetarian_t = DIET_BASE_T["Vegetarian"] * FOOD_WASTE_MULTIPLIER.get(u.food_waste, 1.0)
        saving = round(max(d_t - vegetarian_t, 0), 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Diet", "Adopt a plant-rich diet",
                "Shifting to a vegetarian or flexitarian diet reduces agricultural emissions.",
                saving,
            ))

    if u.food_waste in ("Medium", "High"):
        saving = round(d_t * 0.13, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Diet", "Reduce food waste",
                "Planning meals and freezing leftovers can cut your diet emissions by 10-15%.",
                saving,
            ))

    if u.renewable_pct < 100:
        current_elec_t = u.electricity_kwh * 12 * ELECTRICITY_KG_PER_KWH / 1000 * (1 - u.renewable_pct / 100)
        saving = round(current_elec_t * 0.75, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Home Energy", "Switch to a green energy tariff",
                "Moving to 100% renewable energy can drastically reduce your home emissions.",
                saving,
            ))

    if u.gas_m3 > 20:
        saving = round(u.gas_m3 * 12 * GAS_KG_PER_M3 / 1000 * 0.15, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Home Energy", "Improve home insulation",
                "Better insulation typically cuts heating-related gas use by 10-20%.",
                saving,
            ))

    if u.vehicle_type in ("Petrol", "Diesel") and u.car_km > 100:
        saving = round(u.car_km * 12 * VEHICLE_KG_PER_KM[u.vehicle_type] / 1000 * 0.25, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Transport", "Drive less, use public transport",
                "Swapping some car trips for public transport or cycling cuts fuel emissions directly.",
                saving,
            ))

    if u.shopping_habits in ("High", "Very High") or u.clothing_items > 15:
        saving = round(lifestyle_t(u) * 0.20, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Lifestyle", "Buy fewer, longer-lasting items",
                "Cutting back on fast fashion and impulse purchases reduces embedded carbon.",
                saving,
            ))

    if (u.short_haul_flights + u.long_haul_flights) > 0:
        saving = round(u.long_haul_flights * LONG_HAUL_FLIGHT_T * 0.5
                        + u.short_haul_flights * SHORT_HAUL_FLIGHT_T * 0.5, 2)
        if saving > 0:
            candidates.append(Recommendation(
                "Transport", "Fly less, or offset flights",
                "Combining trips or choosing rail for shorter journeys avoids high per-km flight emissions.",
                saving,
            ))

    candidates.sort(key=lambda r: r.savings_t, reverse=True)
    return candidates[:top_n]


def goal_based_plan(u: UserInputs, reduction_percent: float) -> dict:
    """
    Splits a target percentage reduction proportionally across the 4
    breakdown categories (biggest contributors shrink the most).
    Returns {"target_footprint": float, "steps": [(category, tonnes), ...]}
    """
    breakdown = emissions_breakdown(u)
    total = sum(breakdown.values())
    target_reduction = total * (reduction_percent / 100)

    steps = []
    if total > 0:
        for category, value in sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True):
            share = value / total
            steps.append((category, round(target_reduction * share, 1)))

    return {
        "current_footprint": round(total, 2),
        "target_footprint": round(total - target_reduction, 1),
        "target_reduction": round(target_reduction, 2),
        "steps": steps,
    }


if __name__ == "__main__":
    # Quick sanity check against the reference example (matches the
    # EcoTrace screenshots: 250kWh/20%/50m3 energy, Petrol 300km/50km
    # transport, no flights, Mixed/Medium diet, Medium/12/2 lifestyle).
    u = UserInputs()
    breakdown = emissions_breakdown(u)
    total = total_footprint(u)
    print("Breakdown:", breakdown)
    print("Total:", total, "tonnes CO2e/year")
    print("Badge:", footprint_badge(total))
    score = eco_score(total)
    print("Eco score:", score, "-", eco_score_label(score))
    print("Comparison:", comparison_data(total))
    print("\nRecommendations:")
    for r in generate_recommendations(u):
        print(f"  [{r.category}] {r.title} (-{r.savings_t}t): {r.description}")
    print("\nGoal plan (20% reduction):")
    plan = goal_based_plan(u, 20)
    for k, v in plan.items():
        print(f"  {k}: {v}")
