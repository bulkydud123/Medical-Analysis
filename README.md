# Symptom Checker

A small educational web app that estimates which of 10 common conditions
best matches a set of reported symptoms. Python (Flask) backend, plain
HTML/CSS/JS frontend, no external services or API keys required.

**This is a teaching demo, not a medical device.** Don't use it for real
diagnosis — see a clinician for actual symptoms.

## How it works

- `dataset.csv` is a small hand-built table of 10 diseases × 18 symptoms.
  Each cell is `P(symptom present | disease)`, plus a `prior` column for
  roughly how common each condition is.
- `app.py` treats the checked symptoms as a simplified Naive Bayes
  classifier: it multiplies together (in log-space) the probability of
  each symptom being present or absent, given each disease, then
  converts the resulting scores into a 0–100% "certainty" per disease
  with softmax so they sum to 100%.
- The frontend (`templates/index.html`, `static/app.js`, `static/style.css`)
  is a checkbox questionnaire that posts the selected symptoms to
  `/api/diagnose` and renders the ranked results as bars.

## Run it locally

```bash
cd symptom-checker
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

## Customize

- **Add a disease**: add a new row to `dataset.csv` with a `prior` and a
  probability (0–1) for every symptom column.
- **Add a symptom**: add a new column to *every* row in `dataset.csv`,
  then add a friendly label for it in `SYMPTOM_LABELS` in `app.py`
  (optional — otherwise it falls back to a title-cased version of the
  column name).
- **Change the model**: the whole scoring logic lives in the `diagnose()`
  function in `app.py` if you want to swap in a different approach
  (e.g. weighted scoring, a real ML classifier, scikit-learn, etc).
- **Point at a different dataset file**: set the `DATASET_PATH` env var
  instead of overwriting `dataset.csv`, e.g.
  `DATASET_PATH=other.csv python app.py`.

## Swapping in a raw, per-case dataset

`app.py` expects an *aggregated*, disease-level CSV:
`disease,prior,symptom_1,symptom_2,...` where each symptom cell is
`P(symptom | disease)` between 0 and 1.

Many public symptom datasets (like the augmented Kaggle-style one this
project ships with) are instead *per-case*: one row per patient/case, a
disease-name column, and 0/1 columns for every symptom. Use
`prepare_dataset.py` to convert one of those into the format the app
needs:

```bash
python prepare_dataset.py raw_dataset.csv dataset.csv
```

This groups rows by disease and computes each symptom's probability as
the fraction of that disease's cases where it appeared, and each
disease's prior as its share of total cases. Options:

```bash
# If the disease/label column isn't auto-detected
python prepare_dataset.py raw_dataset.csv dataset.csv --label-col condition

# Drop diseases with very few recorded cases (noisy probabilities)
python prepare_dataset.py raw_dataset.csv dataset.csv --min-cases 10
```

The bundled `dataset.csv` was generated this way from
`Final_Augmented_dataset_Diseases_and_Symptoms.csv` (773 diseases, 377
symptoms) — run `prepare_dataset.py` again any time you get a new raw
export to regenerate it.

## Project structure

```
symptom-checker/
├── app.py                # Flask backend + scoring logic
├── dataset.csv            # aggregated disease/symptom probability table
├── prepare_dataset.py      # converts a raw per-case CSV into dataset.csv
├── requirements.txt
├── templates/
│   └── index.html          # questionnaire page (with search box)
└── static/
    ├── style.css
    └── app.js                # fetch() calls to /api/diagnose, search filter
```
