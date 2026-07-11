from flask import Flask, render_template, request, jsonify
import pickle
import re

app = Flask(__name__)

model = pickle.load(open("model/model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))

@app.route("/")
def home():
    return render_template("index.html")

def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z ]", "", text)
    return text

@app.route("/predict", methods=["POST"])
def predict():

    data = request.get_json()
    news = data["news"]

    news = clean_text(news)

    vector = vectorizer.transform([news])

    prediction = model.predict(vector)[0]

    probability = model.predict_proba(vector)

    confidence = round(max(probability[0]) * 100, 2)

    result = "Real" if prediction == 1 else "Fake"

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%"
    })

if __name__ == "__main__":
    app.run(debug=True)
