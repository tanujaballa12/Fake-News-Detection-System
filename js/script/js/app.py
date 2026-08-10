from flask import Flask, request, jsonify, session, redirect, render_template
from news_api_checker import verify_news
import sqlite3
import pickle
import re
import pandas as pd
from difflib import SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.secret_key = "fake_news_secret_key"

model = pickle.load(open("model/model.pkl", "rb"))
vectorizer = pickle.load(open("model/vectorizer.pkl", "rb"))
@app.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")


    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()


    # Total predictions
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM predictions
        WHERE user_id=?
        """,
        (session["user_id"],)
    )

    total_predictions = cursor.fetchone()[0]


    # Fake news count
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM predictions
        WHERE user_id=?
        AND prediction LIKE '%Fake%'
        """,
        (session["user_id"],)
    )

    fake_count = cursor.fetchone()[0]


    # Real news count
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM predictions
        WHERE user_id=?
        AND prediction LIKE '%Real%'
        """,
        (session["user_id"],)
    )

    real_count = cursor.fetchone()[0]


    conn.close()


    return render_template(
        "index.html",
        total_predictions=total_predictions,
        fake_count=fake_count,
        real_count=real_count
    )
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text 
dataset = pd.concat([
    pd.read_excel("dataset/true.xlsx"),
    pd.read_excel("dataset/fake.xlsx")
], ignore_index=True)

dataset["category"] = dataset["category"].fillna("").apply(clean_text)
dataset["text"] = dataset["text"].fillna("").apply(clean_text)
dataset["combined_text"] = dataset["text"]
# Convert all dataset articles into TF-IDF vectors
dataset_vectors = vectorizer.transform(dataset["combined_text"])

def verify_dataset(news):

    cleaned = clean_text(news)

    # Convert user news into TF-IDF vector
    news_vector = vectorizer.transform([cleaned])

    # Compare with every article
    similarities = cosine_similarity(news_vector, dataset_vectors).flatten()

    # Find highest similarity
    best_index = similarities.argmax()
    best_similarity = similarities[best_index]

    row = dataset.iloc[best_index]

    print("Best Similarity:", best_similarity)
    print("Best Source:", row["Web"])
    print("Best Label:", row["label"])
    print("Best Category:", row["category"])

    if best_similarity >= 0.60:

      return {
        "verified": True,
        "source": row["Web"],
        "category": row["category"],
        "text": row["text"],
        "label": row["label"],
        "similarity": round(best_similarity * 100, 2)
    }
    return {
    "verified": False,
    "source": "",
    "category": "",
    "label": -1,
    "similarity": round(best_similarity * 100, 2)
}
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("news.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(username,email,password) VALUES (?,?,?)",
                (username, email, password)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered. Please login."

        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("news.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/")

        return "Invalid Login"
    

    return render_template("login.html")
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]      
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/admin")

        return "Invalid Admin Login"

    return render_template("admin_login.html")
@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/admin-login")

    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT users.username,
           predictions.news_text,
           predictions.prediction,
           predictions.timestamp
    FROM predictions
    JOIN users
    ON users.id = predictions.user_id
    ORDER BY predictions.id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return render_template("admin.html", rows=rows)

@app.route("/admin-logout")
def admin_logout():

    session.pop("admin", None)

    return redirect("/admin-login")

@app.route("/predict", methods=["POST"])
def predict():

    print("PREDICT ROUTE HIT")

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first"
        })


    data = request.get_json()

    news = data.get("news", "")


    if not news.strip():

        return jsonify({
            "prediction": "Please enter news text",
            "confidence": "0%",
            "verified": False,
            "source": "",
            "matched_category": "",
        })


    if len(news.split()) < 5:

        return jsonify({
            "prediction": "Please enter a complete news article",
            "confidence": "0%",
            "verified": False,
            "source": "",
            "matched_category": "",
            "similarity": 0
        })


    # ===============================
    # PERSONAL CLAIM CHECK
    # ===============================

    if news.lower().startswith(("i ", "my ", "we ")):

        result = "Unverified Personal Claim"

        conn = sqlite3.connect("news.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO predictions
            (user_id, news_text, prediction)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                news,
                result
            )
        )

        conn.commit()
        conn.close()


        return jsonify({
            "prediction": result,
            "confidence": "0%",
            "verified": False,
            "source": "No news source found",
           "matched_category": "",
            "similarity": 0
        })


    # ===============================
    # MACHINE LEARNING PREDICTION
    # ===============================

    cleaned_news = clean_text(news)

    vector = vectorizer.transform([cleaned_news])


    prediction = model.predict(vector)[0]

    print("Model Prediction Value:", prediction)
    print("Classes:", model.classes_)


    probabilities = model.predict_proba(vector)


    fake_prob = probabilities[0][0]
    real_prob = probabilities[0][1]


    confidence = round(
        max(fake_prob, real_prob) * 100,
        2
    )


    print("Fake Probability:", fake_prob)
    print("Real Probability:", real_prob)
    print("Confidence:", confidence)



    if prediction == 1:
        ml_result = "Predicted Real News"
    else:
        ml_result = "Predicted Fake News"

    # ===============================
    # DATASET + NEWS API VERIFICATION
    # ===============================

    dataset_result = verify_dataset(news)

    if dataset_result["verified"]:
        news_result = dataset_result
    else:
        news_result = verify_news(news)

    print("FINAL NEWS RESULT:", news_result)

    # ===============================
    # FINAL DECISION
    # ===============================

    if dataset_result["verified"]:

        if dataset_result["label"] == 1:
            result = "Verified Real News"
        else:
            result = "Verified Fake News"

    else:

        if news_result["verified"]:
            result = "Verified Real News"

        elif (
            news_result.get("source", "")
            and news_result.get("similarity", 0) >= 40
            and confidence >= 70
        ):
            result = "Real News Found In Source"

        elif prediction == 0 and confidence >= 85:
            result = "Predicted Fake News"

        elif prediction == 1 and confidence >= 90:
            result = "Likely Real News (Source Not Confirmed)"

        else:
            result = "News Verification Inconclusive"

    # ===============================
    # SAVE HISTORY
    # ===============================

    conn = sqlite3.connect("news.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO predictions
        (user_id, news_text, prediction)
        VALUES (?, ?, ?)
        """,
        (
            session["user_id"],
            news,
            result
        )
    )

    conn.commit()
    conn.close()

    # ===============================
    # RETURN RESPONSE
    # ===============================

    return jsonify({
        "prediction": result,
        "confidence": f"{confidence}%",
        "verified": news_result.get("verified", False),
        "source": news_result.get("source", "No source found"),
        "url": news_result.get("url", ""),
        "matched_category": news_result.get("category", ""),
        "similarity": news_result.get("similarity", 0)
    })

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("news.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT news_text, prediction, timestamp
        FROM predictions
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    history = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        history=history
    )


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
