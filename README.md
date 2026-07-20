# Carbon Footprint Calculator using AI — Carbon Footprint Calculator (100% Python)

A pure-Python recreation of the Carbon Footprint Calculator using AI carbon footprint calculator UI,
built with **Streamlit**. No HTML/JS files — everything (UI, styling,
charts, and the emissions engine) is Python.

## Features

- **5-step calculator wizard**: Home Energy, Transport, Flights, Diet, Lifestyle
- **Live estimate** while you fill in the form
- **Results dashboard**: hero footprint number, footprint badge (Low/Moderate/High/Very High),
  Eco Score gauge (0-100), emissions breakdown donut chart, and a
  "how do you compare" bar chart vs. Global/EU/US averages
- **Personalized Action Plan**: auto-generated recommendation cards ranked
  by estimated CO2e savings
- **Reduction Goal planner**: pick a target % reduction and see exactly
  how much to cut from each category to hit it
- **History log** of past assessments
- **Light / dark mode** toggle

## Project structure

```
ecotrace_app/
├── app.py            # Streamlit UI + page routing (run this)
├── calculations.py   # Pure-Python emissions engine (no UI deps — unit testable)
├── charts.py          # Matplotlib chart builders (eco score, breakdown, comparison)
├── styles.py          # CSS (light/dark theme)
├── requirements.txt
└── README.md
```

## Setup & run

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Sanity-checking the emissions engine on its own

`calculations.py` has no Streamlit dependency, so you can test the math
directly:

```bash
python calculations.py
```

This prints the breakdown, total footprint, eco score, and sample
recommendations for the default inputs.

## Notes on the numbers

Emission factors (kg CO2e per kWh, per km, per diet type, etc.) are
simplified, published-average estimates — good for an educational /
awareness tool, not a certified carbon audit. They're documented at the
top of `calculations.py` if you want to tune them to a specific country's
grid mix or your own data.
