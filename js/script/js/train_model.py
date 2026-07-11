import pandas as pd
import pickle
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score


# Load Excel files
fake = pd.read_excel("Fake.xlsx")
real = pd.read_excel("True.xlsx")

# Add labels
fake["label"] = 0   # Fake
real["label"] = 1   # Real

# Combine datasets
data = pd.concat([fake, real], ignore_index=True)

# Text cleaning
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-zA-Z\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Assuming news content column name is 'text'
data["text"] = data["text"].apply(clean_text)

X = data["text"]
y = data["label"]

# TF-IDF
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(X)

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train Model
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# Accuracy
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Accuracy: {accuracy*100:.2f}%")

# Create model folder if not exists
os.makedirs("model", exist_ok=True)

# Save files
pickle.dump(model, open("model/model.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))

print("Model and Vectorizer saved successfully!")
