import pandas as pd
import numpy as np
import joblib
import xgboost as xgb
import re
import os
import secrets
import webbrowser
from threading import Timer

from flask import Flask, render_template, request, redirect, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from product import product_bp
from scipy.sparse import hstack

# ================= SECURITY: ENV VARIABLES =================
from dotenv import load_dotenv
load_dotenv()

# CHANGED: TextBlob replaced with VADER - see FeatureExtraction.ipynb
# comment for the full reasoning. Must match training exactly.
#
# CHANGED (BM+EN support): VADER's lexicon is English-only by default,
# so Bahasa Melayu sentiment words (e.g. "bagus", "teruk", "tipu") would
# otherwise score as neutral. apply_malay_lexicon() patches in a BM
# sentiment lexicon + BM negation words (tak, tidak, bukan, etc). This
# MUST be called identically here and in FeatureExtraction.ipynb, or
# training and live prediction will score sentiment differently for the
# same review text. See malay_sentiment.py for the full word list and
# known limitations (it is a hand-built lexicon, not exhaustive).
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from malay_sentiment import apply_malay_lexicon

vader_analyzer = SentimentIntensityAnalyzer()
apply_malay_lexicon(vader_analyzer)


# ================= CLEAN TEXT =================
def clean_review(text):
    text = str(text).lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9 ]", "", text)
    return text


# ================= RULE-BASED PATTERNS (EN + BM) =================
# CHANGED (BM+EN support): superlative_pattern / detail_pattern /
# genuine_phrase_pattern used to be English-only, which meant a Malay
# review like "mesti beli, penghantaran cepat" could never trigger the
# hype/genuine signals that an equivalent English review would. Moved to
# review_patterns.py (shared with FeatureExtraction.ipynb) so the same
# BM+EN phrase coverage is used for both pseudo-label construction and
# the live "Why This Result?" breakdown shown to users - if these two
# ever go out of sync, the breakdown shown to a user would describe
# different logic than what actually built the training labels.
from review_patterns import (
    superlative_pattern,
    detail_pattern,
    genuine_phrase_pattern,
)


# ================= APP INIT =================
app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
if not os.environ.get("FLASK_SECRET_KEY"):
    print("WARNING: FLASK_SECRET_KEY not set in environment - using a "
          "random temporary key. Sessions will not persist across "
          "restarts. Set FLASK_SECRET_KEY in a .env file for real use.")

app.register_blueprint(product_bp)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ================= MONGO DB =================
app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fake_review_db")
mongo = PyMongo(app)

print("MONGO_URI:", os.environ.get("MONGO_URI")) 
try: 
    mongo.cx.server_info() 
    print("MongoDB Connected Successfully") 
except Exception as e: 
    print("MongoDB Connection Failed")
    print(e)

bcrypt = Bcrypt(app)

# ================= LOAD MODELS =================
rf_model = joblib.load("rf_model.pkl")
tfidf = joblib.load("tfidf.pkl")
xgb_model = joblib.load("xgb_model.pkl")
scaler = joblib.load("scaler.pkl")
imputer = joblib.load("imputer.pkl")
num_cols = joblib.load("feature_columns.pkl")
burst_threshold = joblib.load("burst_threshold.pkl")


# ================= FEATURE ENGINEERING =================
def extract_features(review, product_name):

    original_review = str(review)
    words = original_review.split()

    review_length = len(words)
    avg_word_length = np.mean([len(w) for w in words]) if words else 0
    unique_word_ratio = len(set(words)) / max(len(words), 1)
    word_count = len(words)

    capital_ratio = sum(c.isupper() for c in original_review) / max(len(original_review), 1)
    exclamation_count = original_review.count("!")
    question_count = original_review.count("?")

    emoji_pattern = re.compile(r"[\U0001F300-\U0001FAFF]")
    emoji_count = len(emoji_pattern.findall(original_review))
    emoji_density = emoji_count / max(word_count, 1)

    cleaned_review = clean_review(original_review)
    tfidf_vec = tfidf.transform([cleaned_review])
    cleaned_words = cleaned_review.split()

    # ================= BASIC NLP =================
    if len(cleaned_words) < 2:
        bst_score = 0
    else:
        repetition_ratio = len(cleaned_words) / (len(set(cleaned_words)) + 1)
        bst_score = min(1.0, repetition_ratio / 5)

    # SENTIMENT SCORING - must match FeatureExtraction.ipynb's text basis.
    # Training now scores "original_review_for_sentiment" (see
    # CleanAll.ipynb patch): noise like URLs/seller-boilerplate removed,
    # but punctuation, casing, and all words (incl. negators like "tak",
    # "not") kept intact, since VADER depends on those for accuracy.
    # A live user submission has no scraping noise to strip in the first
    # place, so `original_review` here is already an equivalent match -
    # do NOT switch this to `cleaned_review` (which has stopwords,
    # punctuation, and negators stripped by clean_review() above; that
    # would silently break sentiment accuracy and reintroduce the
    # train/live mismatch this comment is warning you about).
    try:
        sentiment_score = vader_analyzer.polarity_scores(original_review)["compound"]
    except Exception:
        sentiment_score = 0.0

    sentiment_intensity = abs(sentiment_score)

    # ================= RULE FLAGS =================
    short_review_flag = 1 if word_count < 5 else 0
    BST_flag = 1 if bst_score > 0.5 else 0
    extreme_sentiment_flag = 1 if abs(sentiment_score) > 0.7 else 0

    exclamation_spam_flag = 1 if exclamation_count >= 3 else 0
    superlative_flag = 1 if superlative_pattern.search(original_review) else 0
    detailed_review_flag = 1 if (
        word_count >= 6 and detail_pattern.search(original_review)
    ) else 0
    short_but_genuine_flag = 1 if (
        exclamation_count < 3 and genuine_phrase_pattern.search(original_review)
    ) else 0

    experience_pattern = re.compile(
    r"\b(selepas|setelah|hari pertama|minggu pertama|bulan pertama|"
    r"kali penggunaan|digunakan|guna selama|baru guna)\b",
    re.I
)

    experience_flag = 1 if experience_pattern.search(original_review) else 0

    # ================= DB-DEPENDENT FEATURES =================
    duplicate_review_flag = 1 if mongo.db.reviews.find_one({
        "product": product_name,
        "review": review
    }) else 0

    day_ago = datetime.now() - timedelta(days=1)
    daily_review_count = mongo.db.reviews.count_documents({
        "product": product_name,
        "timestamp": {"$gte": day_ago}
    })

    burst_activity_flag = 1 if daily_review_count >= burst_threshold else 0

    last_review = mongo.db.reviews.find_one(
        {"product": product_name},
        sort=[("timestamp", -1)]
    )
    if last_review and "timestamp" in last_review:
        time_delta_sec = (datetime.now() - last_review["timestamp"]).total_seconds()
    else:
        time_delta_sec = 999999

    live_num_features = pd.DataFrame([{
        "BST_score": bst_score,
        "sentiment_score": sentiment_score,
        "sentiment_intensity": sentiment_intensity,
        "review_length": review_length,
        "avg_word_length": avg_word_length,
        "unique_word_ratio": unique_word_ratio,
        "word_count": word_count,
        "capital_ratio": capital_ratio,
        "emoji_density": emoji_density,
        "exclamation_count": exclamation_count,
        "question_count": question_count,
        "daily_review_count": daily_review_count,
        "time_delta_sec": time_delta_sec,
        "short_review_flag": short_review_flag,
        "BST_flag": BST_flag,
        "extreme_sentiment_flag": extreme_sentiment_flag,
        "duplicate_review_flag": duplicate_review_flag,
        "burst_activity_flag": burst_activity_flag,
        "exclamation_spam_flag": exclamation_spam_flag,
        "superlative_flag": superlative_flag,
        "detailed_review_flag": detailed_review_flag,
        "short_but_genuine_flag": short_but_genuine_flag,
    }])

    live_num_features = imputer.transform(live_num_features[num_cols])
    live_num_features = scaler.transform(live_num_features)

    X = hstack([tfidf_vec, live_num_features])
    X = X.tocsr()

    flags = {
        "short_review_flag": short_review_flag,
        "duplicate_review_flag": duplicate_review_flag,
        "burst_activity_flag": burst_activity_flag,
        "BST_flag": BST_flag,
        "extreme_sentiment_flag": extreme_sentiment_flag,
        "exclamation_spam_flag": exclamation_spam_flag,
        "superlative_flag": superlative_flag,
        "detailed_review_flag": detailed_review_flag,
        "short_but_genuine_flag": short_but_genuine_flag,
        "experience_flag": experience_flag,
    }

    raw_values = {
        "word_count": word_count,
        "BST_score": round(bst_score, 3),
        "sentiment_score": round(sentiment_score, 3),
        "exclamation_count": exclamation_count,
        "daily_review_count": daily_review_count,
        "burst_threshold": round(float(burst_threshold), 2),
        "time_delta_sec": round(time_delta_sec, 1),
    }

    return X, sentiment_score, flags, raw_values


# ================= HOME =================
@app.route("/")
def home():
    user = session.get("user")
    return render_template("index.html", user=user)


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    if session.get("guest"):
        return redirect("/guest_dashboard")

    if "user" not in session:
        return redirect("/login")

    user_email = session["user"]["email"]

    total         = mongo.db.reviews.count_documents({"user_email": user_email})
    fake_count    = mongo.db.reviews.count_documents({"user_email": user_email, "result": "Fake"})
    genuine_count = mongo.db.reviews.count_documents({"user_email": user_email, "result": "Genuine"})

    fake_pct    = round(fake_count    / total * 100, 1) if total > 0 else 0
    genuine_pct = round(genuine_count / total * 100, 1) if total > 0 else 0

    correct_count   = mongo.db.reviews.count_documents({"user_email": user_email, "user_feedback": "correct"})
    incorrect_count = mongo.db.reviews.count_documents({"user_email": user_email, "user_feedback": "incorrect"})
    feedback_total  = correct_count + incorrect_count
    accuracy        = round(correct_count / feedback_total * 100, 1) if feedback_total > 0 else None

    return render_template(
        "dashboard.html",
        user            = session["user"],
        total           = total,
        fake            = fake_count,
        real            = genuine_count,
        fake_pct        = fake_pct,
        genuine_pct     = genuine_pct,
        accuracy        = accuracy,
        feedback_total  = feedback_total,
    )


# ================= GUEST USER =================
@app.route("/guest_dashboard")
def guest_dashboard():

    fake = mongo.db.guest_reviews.count_documents({"result": "Fake"})
    real = mongo.db.guest_reviews.count_documents({"result": "Genuine"})

    total = fake + real

    correct_count = mongo.db.guest_reviews.count_documents({"user_feedback": "correct"})
    incorrect_count = mongo.db.guest_reviews.count_documents({"user_feedback": "incorrect"})
    feedback_total = correct_count + incorrect_count
    accuracy = round((correct_count / feedback_total) * 100, 2) if feedback_total > 0 else None

    return render_template(
        "guest_dashboard.html",
        fake=fake,
        real=real,
        total=total,
        genuine_percentage=round((real / total * 100) if total else 0, 2),
        fake_percentage=round((fake / total * 100) if total else 0, 2),
        accuracy=accuracy,
        feedback_total=feedback_total
    )


# ================= GUEST MODE =================
@app.route("/continue_as_guest")
def continue_as_guest():
    session.clear()
    session["guest"] = True
    return redirect("/dashboard")


@app.route("/exit_guest")
def exit_guest():
    session.clear()
    return redirect("/")


# ================= PREDICT =================
@app.route("/predict", methods=["POST"])
def predict():

    review = request.form.get("review", "")

    if not review or len(review.strip()) < 2:
        return "Please enter a valid review"

    product_name = request.form.get("product_name")
    platform = request.form.get("platform")
    brand = request.form.get("brand")
    category = request.form.get("category")

    # ================= FEATURES =================
    X, sentiment_score, flags, raw_values = extract_features(review, product_name)
    X_array = np.asarray(X.toarray(), dtype=np.float32)

    # ================= RF =================
    rf_proba = rf_model.predict_proba(X_array)[0]
    rf_fake = float(rf_proba[1])

    # ================= XGB =================
    xgb_fake = float(xgb_model.predict(xgb.DMatrix(X_array))[0])

    rf_fake = np.clip(rf_fake, 0, 1)
    xgb_fake = np.clip(xgb_fake, 0, 1)
    final_score = (rf_fake + xgb_fake) / 2

    # =====================================================
    # CALIBRATION ENHANCEMENT
    # =====================================================

    fake_flag_keys = [
        "short_review_flag",
        "duplicate_review_flag",
        "burst_activity_flag",
        "BST_flag",
        "extreme_sentiment_flag",
        "exclamation_spam_flag",
        "superlative_flag"
    ]

    genuine_flag_keys = [
        "detailed_review_flag",
        "short_but_genuine_flag",
        "experience_flag"
    ]
    fake_flags_triggered = sum(flags[k] for k in fake_flag_keys)
    genuine_flags_triggered = sum(flags[k] for k in genuine_flag_keys)

    # =====================================================
    # CASE 1:
    # No fake signals detected
    # =====================================================

    if fake_flags_triggered == 0:

        # no suspicious behaviour at all
        final_score *= 0.55

        # ordinary length reviews are usually genuine
        if raw_values["word_count"] >= 6:
            final_score *= 0.85

        # additional genuine evidence
        if genuine_flags_triggered > 0:
            final_score *= 0.80

    # =====================================================
    # FINAL DECISION
    # =====================================================

    confidence = round(final_score * 100, 1)

    if final_score > 0.55:
        label = "Fake"
        final_pred = 1
    else:
        label = "Genuine"
        final_pred = 0

    if sentiment_score > 0.05:
        sentiment_label = "Positive"
    elif sentiment_score < -0.05:
        sentiment_label = "Negative"
    else:
        sentiment_label = "Neutral"

    behavior = round(
        min(100, confidence + 10)
        if final_pred == 0
        else max(0, 100 - confidence),
        1
    )

    # ================= EXPLAINABILITY BREAKDOWN =================
    breakdown = [
        {
            "feature": "Short review",
            "value": f"{raw_values['word_count']} words",
            "triggered": bool(flags["short_review_flag"]),
            "direction": "fake",
            "explanation": "Reviews under 5 words are flagged as a fake signal, even though some genuine reviewers are just brief."
        },
        {
            "feature": "Duplicate review",
            "value": "Seen before for this product" if flags["duplicate_review_flag"] else "Not seen before",
            "triggered": bool(flags["duplicate_review_flag"]),
            "direction": "fake",
            "explanation": "This exact review text has appeared 3+ times for this product - a strong fake signal, though identical short praise can happen genuinely too."
        },
        {
            "feature": "Burst activity",
            "value": f"{raw_values['daily_review_count']} reviews today (threshold {raw_values['burst_threshold']})",
            "triggered": bool(flags["burst_activity_flag"]),
            "direction": "fake",
            "explanation": "This product is receiving an unusually high number of reviews today (top 5% of training data) - could mean manipulation, or a real promotion driving traffic."
        },
        {
            "feature": "Repetition (burstiness)",
            "value": f"BST score {raw_values['BST_score']}",
            "triggered": bool(flags["BST_flag"]),
            "direction": "fake",
            "explanation": "The review repeats the same words unusually often relative to its length."
        },
        {
            "feature": "Extreme sentiment",
            "value": f"sentiment {raw_values['sentiment_score']}",
            "triggered": bool(flags["extreme_sentiment_flag"]),
            "direction": "fake",
            "explanation": "Sentiment is very strongly positive or negative - exaggerated tone is common in fake reviews."
        },
        {
            "feature": "Exclamation spam",
            "value": f"{raw_values['exclamation_count']} '!' marks",
            "triggered": bool(flags["exclamation_spam_flag"]),
            "direction": "fake",
            "explanation": "3 or more exclamation marks - excessive punctuation is common in hype-style fake reviews."
        },
        {
            "feature": "Hype phrasing",
            "value": "Generic hype phrase detected" if flags["superlative_flag"] else "None detected",
            "triggered": bool(flags["superlative_flag"]),
            "direction": "fake",
            "explanation": "Contains generic hype phrasing (e.g. 'best ever', 'must buy', 'highly recommend') often seen in incentivized/fake reviews."
        },
        {
            "feature": "Detailed review",
            "value": f"{raw_values['word_count']} words with specific detail" if flags["detailed_review_flag"] else "No specific detail found",
            "triggered": bool(flags["detailed_review_flag"]),
            "direction": "genuine",
            "explanation": "Long reviews with a concrete specific detail (a number of days/hours/etc.) look like a real personal experience - this pulls the prediction toward genuine."
        },
        {
            "feature": "Common genuine phrasing",
            "value": "Calm, common review phrasing detected" if flags["short_but_genuine_flag"] else "None detected",
            "triggered": bool(flags["short_but_genuine_flag"]),
            "direction": "genuine",
            "explanation": "Uses ordinary, calm phrasing real buyers commonly use (e.g. 'fast delivery', 'no issues so far', 'as described') without spammy punctuation - this pulls the prediction toward genuine even for short reviews."
        },
    ]

    triggered_fake = [b for b in breakdown if b["triggered"] and b["direction"] == "fake"]
    triggered_genuine = [b for b in breakdown if b["triggered"] and b["direction"] == "genuine"]

    if not triggered_fake and not triggered_genuine:

        if label == "Genuine":
            summary_note = (
            "No suspicious rule-based signals were detected. "
            "The review shows normal writing behaviour and is "
            "classified as Genuine."
        )
        else:
            summary_note = (
            "Although no explicit rule-based signals were triggered, "
            "the machine learning model detected textual patterns "
            "similar to fake reviews from the training data."
        )

    elif not triggered_fake:

        summary_note = (
        f"No fake signals were triggered and "
        f"{len(triggered_genuine)} genuine signal(s) were detected."
    )

    elif not triggered_genuine:

        summary_note = (
        f"{len(triggered_fake)} fake signal(s) were detected."
    )

    else:

        summary_note = (
        f"{len(triggered_fake)} fake signal(s) were detected, "
        f"but partially offset by "
        f"{len(triggered_genuine)} genuine signal(s)."
    )

    import json
    breakdown_json = json.dumps(breakdown)

    data = {
        "product": product_name,
        "platform": platform,
        "brand": brand,
        "category": category,
        "review": review,
        "result": label,
        "sentiment": sentiment_label,
        "confidence": confidence,
        "behavior": behavior,
        "fake_probability": round(final_score * 100, 2),
        "rf_score": round(rf_fake * 100, 1),
        "xgb_score": round(xgb_fake * 100, 1),
        "breakdown": breakdown,
        "breakdown_json": breakdown_json,
        "summary_note": summary_note,
    }

    # ================= GUEST AUTO-SAVE =================
    # ADDED: guests no longer need to click "Save to History" - their
    # result is written to guest_reviews automatically, right here,
    # before result.html even renders. This matches what /save_result
    # used to do manually for guests (see that route for the original
    # button-triggered version, kept as-is for registered users).
    #
    # Why duplicate the save logic here instead of calling save_result()
    # directly: save_result() reads from request.form (the POST body of
    # the SAVE button's form submission on result.html), but at this
    # point in /predict there is no such form yet - we only have `data`
    # built from the model's own output. Re-using request.form here
    # would be reading the wrong request entirely.
    #
    # data["breakdown"] is stored directly (not breakdown_json) since
    # we're inserting into Mongo directly here, not round-tripping
    # through an HTML hidden field like /save_result does.
    if session.get("guest"):
        current_time = datetime.now()
        guest_data = {
            "platform": platform,
            "category": category,
            "brand": brand,
            "product": product_name,
            "review": review,
            "result": label,
            "sentiment": sentiment_label,
            "confidence": confidence,
            "fake_probability": round(final_score * 100, 2),
            "breakdown": breakdown,
            "summary_note": summary_note,
            "date": current_time.strftime("%d-%m-%Y"),
            "time": current_time.strftime("%H:%M:%S"),
            "timestamp": current_time,
        }
        mongo.db.guest_reviews.insert_one(guest_data)
        # Let the template know saving already happened automatically,
        # so it can skip showing a manual "Save to History" button for
        # guests (see result.html patch - registered users still get
        # the manual button, since only guest auto-save was requested).
        data["guest_auto_saved"] = True

    return render_template("result.html", data=data, user=session.get("user"))


# ================= HISTORY =================
@app.route("/history")
def history():

    if "user" not in session:
        return redirect("/login")

    search = request.args.get("search")

    query = {"user_email": session["user"]["email"]}

    if search:
        query["review"] = {"$regex": search, "$options": "i"}

    reviews = list(mongo.db.reviews.find(query))

    return render_template("history.html", reviews=reviews, search=search)


# ================= DELETE HISTORY =================
@app.route("/delete/<id>")
def delete(id):

    if "user" not in session:
        return redirect("/login")

    mongo.db.reviews.delete_one({
        "_id": ObjectId(id),
        "user_email": session["user"]["email"]
    })

    return redirect("/history")


# ================= DETECTION =================
@app.route("/detection")
def detection():

    user = session.get("user")

    return render_template(
        "detection.html",
        user=user,
        products=list(mongo.db.products.find())
    )


# ================= SECURITY: BASIC LOGIN RATE LIMITING =================
from collections import defaultdict
import time as _time

_login_attempts = defaultdict(list)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300


def _is_rate_limited(email):
    now = _time.time()
    attempts = [t for t in _login_attempts[email] if now - t < LOGIN_WINDOW_SECONDS]
    _login_attempts[email] = attempts
    return len(attempts) >= LOGIN_MAX_ATTEMPTS


def _record_failed_attempt(email):
    _login_attempts[email].append(_time.time())


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        if _is_rate_limited(email):
            return "Too many failed login attempts. Please try again in a few minutes."

        user = mongo.db.users.find_one({"email": email})

        if user and bcrypt.check_password_hash(user["password"], password):

            session.clear()

            session["user"] = {
                "_id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"]
            }

            return redirect("/dashboard")

        _record_failed_attempt(email)
        return "Invalid login"

    return render_template("login.html")


# ================= SIGNUP =================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        # NEW: confirm_password field added to signup.html so the user
        # can catch a typo before the account is created. Checked here
        # on the server too - never trust client-side JS alone, since a
        # request can always be sent directly without running the page's
        # validateSignup() script.
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            return "Password and Confirm Password do not match"

        # Minimum 6 characters
        if len(password) < 6:
            return "Password must be at least 6 characters long"
        # Must contain at least one number
        if not any(c.isdigit() for c in password):
            return "Password must contain at least one number"

        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return "Please enter a valid email address"

        if mongo.db.users.find_one({"email": email}):
            return "User exists"

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")

        mongo.db.users.insert_one({
            "username": username,
            "email": email,
            "password": hashed
        })

        return redirect("/login")

    return render_template("signup.html")


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= PROFILE =================
@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/login")

    return render_template("profile.html", user=session["user"])


# ================= UPDATE PROFILE =================
@app.route('/update_profile', methods=['POST'])
def update_profile():

    if 'user' not in session:
        return redirect('/login')

    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    # NEW: confirm_password field added to profile.html (under New
    # Password) so the user can catch a typo before it overwrites their
    # real password. Only relevant when password is actually being
    # changed - if both fields are left blank, the existing password is
    # kept exactly as before (no mismatch check needed in that case).
    confirm_password = request.form.get('confirm_password', '')

    user_id = session['user']['_id']

    update_data = {
        "username": username,
        "email": email
    }

    if password and password.strip() != "":

        if password != confirm_password:
            return "New Password and Confirm Password do not match"

        if len(password) < 6:
            return "Password must be at least 6 characters long"

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        update_data["password"] = hashed

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    updated_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    session['user'] = {
        "_id": str(updated_user["_id"]),
        "username": updated_user["username"],
        "email": updated_user["email"]
    }

    session.modified = True

    return redirect('/profile')


# ================= SAVE RESULT =================
@app.route("/save_result", methods=["POST"])
def save_result():

    print("DEBUG save_result | session:", dict(session), "| form_keys:", list(request.form.keys()))

    current_time = datetime.now()

    import json
    breakdown_raw = request.form.get("breakdown_json", "")
    try:
        breakdown = json.loads(breakdown_raw) if breakdown_raw else []
    except (json.JSONDecodeError, TypeError):
        breakdown = []

    data = {
        "platform": request.form["platform"],
        "category": request.form["category"],
        "brand": request.form["brand"],
        "product": request.form["product"],

        "review": request.form["review"],
        "result": request.form["result"],
        "sentiment": request.form["sentiment"],
        "confidence": request.form["confidence"],
        "fake_probability": float(request.form.get("confidence", 0)),
        "breakdown": breakdown,
        "summary_note": request.form.get("summary_note", ""),

        "date": current_time.strftime("%d-%m-%Y"),
        "time": current_time.strftime("%H:%M:%S"),
        "timestamp": current_time
    }

    if "user" in session:
        data["user_email"] = session["user"]["email"]
        data["user_name"] = session["user"]["username"]

        mongo.db.reviews.insert_one(data)

        return """
        <script>
            alert('Saved successfully!');
            window.location.href='/history';
        </script>
        """

    elif session.get("guest"):
        mongo.db.guest_reviews.insert_one(data)

        return """
        <script>
            alert('Saved! Guest results are not tied to an account, so you cannot look this specific result up again - but it now counts toward the community stats on the guest dashboard.');
            window.location.href='/guest_dashboard';
        </script>
        """

    else:
        return """
        <script>
            alert("Please log in or continue as guest before saving.");
            window.location.href='/login';
        </script>
        """


# ================= FEEDBACK =================
@app.route("/feedback/<review_id>", methods=["POST"])
def feedback(review_id):

    if "user" not in session:
        return redirect("/login")

    verdict = request.form.get("verdict")
    if verdict not in ("correct", "incorrect"):
        return "Invalid feedback value", 400

    try:
        oid = ObjectId(review_id)
    except Exception:
        return "Invalid review id", 400

    result = mongo.db.reviews.update_one(
        {"_id": oid, "user_email": session["user"]["email"]},
        {"$set": {"user_feedback": verdict}}
    )

    if result.matched_count == 0:
        return "Review not found", 404

    return redirect("/history")


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        Timer(1, open_browser).start()

    app.run(debug=True)
