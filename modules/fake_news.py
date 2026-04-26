from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import re

# ── Expanded training data (60 samples, balanced) ─────────────
TRAIN_TEXTS = [
    # ── FAKE (30 samples) ─────────────────────────────────────
    "BREAKING: Scientists confirm 5G towers spread deadly virus to humans",
    "Government secretly putting microchips in COVID vaccines revealed",
    "Shocking truth: Moon landing was completely staged by NASA insiders",
    "URGENT: Drinking bleach cures all diseases doctors don't want you to know",
    "Celebrity found dead in suspicious circumstances media is covering up",
    "Secret society controls all world governments exposed insider reveals",
    "Miracle cure for cancer suppressed by pharmaceutical companies for profit",
    "Aliens living among us government confirms in leaked classified documents",
    "Bank collapse imminent withdraw all your money immediately before it's too late",
    "New world order plan to reduce population by 90 percent fully leaked",
    "Politician secretly working for foreign enemy exposed in leaked document",
    "Chemtrails proven to contain mind control chemicals scientist whistleblower says",
    "Facebook deleting accounts that share this post about the truth wake up",
    "You won't believe what they found in tap water government desperately hiding",
    "This one weird trick destroys belly fat doctors absolutely hate it share now",
    "SHARE BEFORE DELETED: The truth about what really happened on 9/11",
    "Mainstream media refuses to cover this massive government cover-up exposed",
    "Warning conspiracy hidden agenda they don't want you to know the truth",
    "Exclusive leaked documents prove vaccines cause autism scientists confirm",
    "Urgent alert: banks preparing to freeze all accounts this weekend panic",
    "They are poisoning our food supply with chemicals approved by corrupt FDA",
    "Hollywood elites running secret underground trafficking network fully exposed",
    "You won't believe what NASA is hiding about Mars colonization program",
    "Scientists threatened into silence about flat earth proof leaked documents",
    "HOAX: Climate change is a lie manufactured by globalists to control energy",
    "Shocking revelation: elections are completely rigged insider whistleblower",
    "Deep state planning to microchip entire population through water supply",
    "Breaking exclusive: major celebrity secretly died months ago media blackout",
    "Miracle plant cures diabetes in 3 days big pharma is suppressing it",
    "Anonymous insider reveals truth about moon being artificial alien structure",

    # ── REAL (30 samples) ─────────────────────────────────────
    "The stock market closed higher today following positive monthly jobs report",
    "Scientists publish new peer-reviewed research on climate change in Nature journal",
    "City council approves annual budget for new public transportation infrastructure",
    "University researchers develop more efficient solar panel technology for homes",
    "Sports team wins national championship after defeating rivals in final match",
    "New study published in Lancet shows benefits of Mediterranean diet for heart",
    "Tech company announces quarterly earnings that beat analyst expectations today",
    "Local government invests in new infrastructure for clean water access program",
    "International climate summit focuses on renewable energy transition strategy",
    "Research shows regular exercise significantly improves mental health outcomes",
    "New legislation passed by senate to improve worker safety regulations nationwide",
    "Museum opens new exhibition celebrating indigenous cultural heritage this month",
    "Public health officials recommend annual flu vaccination for adults this season",
    "Economic report released today shows steady growth in manufacturing sector output",
    "Scientists discover new species of deep sea fish in Pacific Ocean expedition",
    "Government releases annual budget report showing reduced deficit year over year",
    "University study confirms link between sleep quality and cognitive performance",
    "Global temperature records published by meteorological agencies show warming trend",
    "Pharmaceutical company completes phase 3 clinical trials for new heart medication",
    "New electric vehicle sales figures released by Department of Energy show growth",
    "International space station crew completes scheduled maintenance spacewalk today",
    "Central bank announces interest rate decision following monthly economic review",
    "World Health Organization releases updated guidelines for antibiotic use globally",
    "Tech giant reports data breach affecting user accounts urges password reset",
    "Olympic committee announces host city selection for 2032 games following vote",
    "Scientists confirm gravitational wave detection from neutron star collision event",
    "New environmental protection regulations signed into law by president today",
    "Annual survey shows majority of citizens satisfied with public healthcare system",
    "Research institute publishes findings on renewable energy adoption rate trends",
    "Stock exchange regulators announce new rules for high frequency trading firms",
]

TRAIN_LABELS = (
    [1] * 30 +   # 1 = Fake
    [0] * 30     # 0 = Real
)

# ── Train pipeline once at module import ─────────────────────
_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        stop_words='english',
        max_features=2000,        # ↑ more features = better accuracy
        ngram_range=(1, 2),       # unigrams + bigrams
        sublinear_tf=True,        # log scaling for term frequency
    )),
    ('clf', LogisticRegression(
        max_iter=1000,
        C=0.8,                    # slight regularization
        random_state=42,
        class_weight='balanced',  # handle any class imbalance
    ))
])
_pipeline.fit(TRAIN_TEXTS, TRAIN_LABELS)


def _clean_text(text):
    """Remove URLs, special chars, normalize whitespace."""
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'[^a-zA-Z\s!?]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _heuristic_boost(text, fake_prob):
    """
    Lightly adjust ML probability using heuristic signals.
    Avoids pure heuristic bias while still catching obvious cases.
    """
    t = text.lower()

    # Strong fake signals → nudge probability up (max +0.15)
    fake_signals = [
        'breaking', 'urgent', 'shocking', 'wake up',
        'share before deleted', 'they don\'t want you',
        'hidden truth', 'cover-up', 'exposed', 'hoax',
        'conspiracy', 'you won\'t believe', 'mainstream media',
        'whistleblower', 'miracle cure', 'secret society',
        'deep state', 'microchip', 'suppressed',
    ]
    real_signals = [
        'study confirms', 'research shows', 'scientists say',
        'according to', 'published in', 'peer reviewed',
        'official report', 'data shows', 'statistics show',
        'university study', 'clinical trial', 'government releases',
    ]

    boost = 0.0
    for sig in fake_signals:
        if sig in t:
            boost += 0.03    # small nudge per signal, max ~0.15
    for sig in real_signals:
        if sig in t:
            boost -= 0.03

    # Excessive caps → slight fake signal
    caps = sum(1 for c in text if c.isupper())
    if len(text) > 0 and caps / len(text) > 0.35:
        boost += 0.05

    # Cap the total boost to ±0.15 so ML score stays dominant
    boost = max(-0.15, min(0.15, boost))
    return max(0.0, min(1.0, fake_prob + boost))


def detect_fake_news(posts):
    """
    Classify posts as Fake or Real using TF-IDF + Logistic Regression.
    Returns a list of result dicts sorted by fake_prob descending.
    """
    results = []

    for post in posts:
        text = post.text or ''
        if not text.strip():
            continue

        cleaned = _clean_text(text)
        proba = _pipeline.predict_proba([cleaned])[0]
        fake_prob = float(proba[1])

        # Apply heuristic boost (keeps ML as primary signal)
        fake_prob = _heuristic_boost(text, fake_prob)
        real_prob = 1.0 - fake_prob

        fake_pct = round(fake_prob * 100, 1)
        real_pct = round(real_prob * 100, 1)

        # ✅ Threshold = 0.60 → balanced Fake/Real split
        label = 'Fake' if fake_prob >= 0.60 else 'Real'

        results.append({
            'id': getattr(post, 'id', None),
            'text': (text[:110] + '...') if len(text) > 110 else text,
            'author': getattr(post, 'author', None) or 'Unknown',
            'label': label,
            'fake_prob': fake_pct,
            'real_prob': real_pct,
            'confidence': fake_pct if label == 'Fake' else real_pct,
            'likes': getattr(post, 'likes', 0) or 0,
            'source': getattr(post, 'source', ''),
        })

    # Sort: highest fake probability first
    results.sort(key=lambda x: x['fake_prob'], reverse=True)
    return results
