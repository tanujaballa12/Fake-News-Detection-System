import pandas as pd
import pickle
import re
import os

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Load Excel files
fake = pd.read_excel("dataset/fake.xlsx")
real = pd.read_excel("dataset/true.xlsx")

# Add labels
fake["label"] = 0   # Fake
real["label"] = 1   # Real

# Combine datasets
data = pd.concat([fake, real], ignore_index=True)

print(data["label"].value_counts())
print("Dataset Shape:", data.shape)
print("Columns:", data.columns.tolist())
print("Fake News:", len(fake))
print("Real News:", len(real))

# Text cleaning
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Rename title column because it is actually category
data.rename(
    columns={"title": "category"},
    inplace=True
)

# Clean category and news text
data["category"] = data["category"].fillna("").apply(clean_text)
data["text"] = data["text"].fillna("").apply(clean_text)


# Use only actual news text for training
data["combined_text"] = (
    data["category"] + " " + data["text"]
)


# ===============================
# DATASET CHECK BEFORE TRAINING
# ===============================

print("\nDataset Information")

print("Total Records:", len(data))

print("\nLabel Distribution:")
print(data["label"].value_counts())

print("\nDuplicate Rows:")
print(data.duplicated().sum())

print("\nDuplicate News Texts:")
print(data["combined_text"].duplicated().sum())


# Remove duplicate news articles
data = data.drop_duplicates(
    subset=["combined_text"]
).reset_index(drop=True)


print("\nAfter Removing Duplicates:")
print("Total Records:", len(data))

# ===============================
# TRAINING DATA
# ===============================

X = data["combined_text"]
y = data["label"]


# TF-IDF
vectorizer = TfidfVectorizer(
    stop_words="english",
    max_features=50000,
    ngram_range=(1, 2),
    min_df=1,
    sublinear_tf=True
)

X = vectorizer.fit_transform(X)

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

model = LogisticRegression(
    max_iter=5000,
    C=3.0
)

# TRAIN MODEL
model.fit(X_train, y_train)

# EVALUATE MODEL
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print(f"\nAccuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(y_test, predictions))

# Create model folder
os.makedirs("model", exist_ok=True)

# Save model and vectorizer
with open("model/model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("model/vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("\nModel and Vectorizer saved successfully!")
