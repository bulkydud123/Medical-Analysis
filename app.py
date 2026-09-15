"""
Symptom Checker — a small educational disease-probability estimator.

Backend logic:
  For each candidate disease we treat every symptom as an independent
  binary feature (a simplified Naive Bayes model). The dataset stores
  P(symptom present | disease) for each disease/symptom pair, plus a
  prior P(disease) reflecting roughly how common the condition is.

  Given the symptoms the user checked, we compute, for each disease:

      log_score = log(prior)
                  + sum_over_symptoms[ x * log(p) + (1-x) * log(1-p) ]

  where x = 1 if the symptom was reported, 0 otherwise, and p is the
  dataset probability for that disease/symptom pair. The log_scores
  are then converted into a normalized "certainty" percentage across
  all diseases with a softmax, so the output always sums to 100%.

  This is a teaching/demo tool, NOT a medical device. It should never
  be used for real diagnosis.
"""

import csv
import math
import os

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Point DATASET_PATH at any CSV shaped like: disease,prior,symptom_1,symptom_2,...
# Override via env var, e.g.  DATASET_PATH=my_other_dataset.csv python app.py
DATASET_PATH = os.environ.get(
    "DATASET_PATH",
    os.path.join(os.path.dirname(__file__), "dataset.csv"),
)

# Cap how many symptom checkboxes/results get sent to the frontend template
# on initial load, mostly relevant for very large datasets. The search box
# in the UI filters client-side across all of them regardless.
EPS = 1e-6  # avoids log(0) for probabilities stored as exactly 0 or 1


def load_dataset():
    """Read dataset.csv into a list of disease records."""
    diseases = []
    symptom_names = []
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        symptom_names = [c for c in reader.fieldnames if c not in ("disease", "prior")]
        for row in reader:
            diseases.append({
                "name": row["disease"],
                "prior": float(row["prior"]),
                "symptoms": {s: float(row[s]) for s in symptom_names},
            })
    return diseases, symptom_names


DISEASES, SYMPTOMS = load_dataset()

# Optional manual overrides for how a symptom key is displayed, e.g.
# {"shortness_of_breath": "Shortness of breath"}. Anything not listed here
# falls back to auto-formatting the column name (underscores/hyphens -> spaces,
# each word capitalized), so this dict can just stay empty for a new dataset.
SYMPTOM_LABELS = {}


def label_for(symptom_key):
    if symptom_key in SYMPTOM_LABELS:
        return SYMPTOM_LABELS[symptom_key]
    return symptom_key.replace("_", " ").replace("-", " ").strip().capitalize()


def clamp(p):
    return min(max(p, EPS), 1 - EPS)


def diagnose(selected_symptoms):
    """Return diseases ranked by certainty (%) given a set of selected symptom keys."""
    selected = set(selected_symptoms)
    log_scores = {}

    for disease in DISEASES:
        score = math.log(clamp(disease["prior"]))
        for symptom in SYMPTOMS:
            p = clamp(disease["symptoms"][symptom])
            if symptom in selected:
                score += math.log(p)
            else:
                score += math.log(1 - p)
        log_scores[disease["name"]] = score

    # Softmax normalization -> percentages that sum to 100
    max_score = max(log_scores.values())
    exp_scores = {name: math.exp(s - max_score) for name, s in log_scores.items()}
    total = sum(exp_scores.values())
    certainty = {name: (v / total) * 100 for name, v in exp_scores.items()}

    ranked = sorted(certainty.items(), key=lambda kv: kv[1], reverse=True)
    return [{"disease": name, "certainty": round(pct, 1)} for name, pct in ranked]


@app.route("/")
def index():
    symptom_list = [{"key": s, "label": label_for(s)} for s in SYMPTOMS]
    # Sort alphabetically by label so the (potentially long) checklist and
    # the client-side search box are easy to scan.
    symptom_list.sort(key=lambda s: s["label"])
    return render_template(
        "index.html",
        symptoms=symptom_list,
        disease_count=len(DISEASES),
        symptom_count=len(SYMPTOMS),
    )


@app.route("/api/diagnose", methods=["POST"])
def api_diagnose():
    data = request.get_json(silent=True) or {}
    selected = data.get("symptoms", [])
    if not isinstance(selected, list):
        return jsonify({"error": "symptoms must be a list"}), 400

    valid = [s for s in selected if s in SYMPTOMS]
    if not valid:
        return jsonify({"error": "Select at least one symptom."}), 400

    results = diagnose(valid)[:20]  # only the frontend's top picks are useful
    return jsonify({"results": results, "symptom_count": len(valid)})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
