from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from config import Config
from models.database import db, User, Case, Post
from datetime import datetime
import json
import os

from modules.competitor import compare_competitors
from modules.fake_news import detect_fake_news
from modules.prediction import predict_engagement, predict_single

# ─── APP INIT ─────────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access PulseIQ.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    # ✅ fixed SQLAlchemy 2.0 warning
    return db.session.get(User, int(user_id))


# ─── AUTH ROUTES ──────────────────────────────────────────────

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Welcome back, {user.username}! 👋', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('auth/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email',    '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ─── DASHBOARD ROUTES ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    cases = Case.query.filter_by(user_id=current_user.id)\
                      .order_by(Case.created_at.desc()).all()
    return render_template('dashboard/home.html', cases=cases)


@app.route('/case/new', methods=['GET', 'POST'])
@login_required
def case_new():
    if request.method == 'POST':
        name = request.form.get('name',        '').strip()
        keyword = request.form.get('keyword',     '').strip()
        platform = request.form.get('platform',    'Facebook')
        time_range = request.form.get('time_range',  'Last 7 days')
        description = request.form.get('description', '').strip()

        if not name or not keyword:
            flash('Case name and keyword are required.', 'danger')
            return render_template('dashboard/case_new.html')

        case = Case(
            user_id=current_user.id,
            name=name,
            keyword=keyword,
            platform=platform,
            time_range=time_range,
            description=description,
        )
        db.session.add(case)
        db.session.commit()

        flash(f'Case "{name}" created successfully!', 'success')
        return redirect(url_for('case_detail', case_id=case.id))

    return render_template('dashboard/case_new.html')


@app.route('/case/<int:case_id>')
@login_required
def case_detail(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()
    return render_template('dashboard/case_detail.html', case=case, posts=posts)


@app.route('/case/<int:case_id>/delete', methods=['POST'])
@login_required
def case_delete(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    # delete all posts in this case first
    Post.query.filter_by(case_id=case_id).delete()
    db.session.delete(case)
    db.session.commit()
    flash(f'Case "{case.name}" deleted.', 'info')
    return redirect(url_for('dashboard'))


# ─── DATA COLLECTION ──────────────────────────────────────────

@app.route('/case/<int:case_id>/collect', methods=['POST'])
@login_required
def collect_data(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()

    try:
        # ✅ FIXED: use scrapers not apify_client
        from scrapers.facebook_scraper import fetch_facebook_posts

        posts_data = fetch_facebook_posts(
            keyword=case.keyword,
            max_posts=app.config.get('MAX_POSTS_PER_CASE', 50),
            apify_token=app.config.get('APIFY_TOKEN', '')
        )

        # Clear old posts for this case before re-collecting
        Post.query.filter_by(case_id=case_id).delete()

        count = 0
        for item in posts_data:
            post = Post(
                case_id=case.id,
                post_id=str(item.get('id', '')),
                text=item.get('text') or item.get('message',    ''),
                author=item.get('authorName') or item.get(
                    'pageName', 'Unknown'),
                likes=item.get('likesCount') or item.get('likes',    0),
                shares=item.get('sharesCount') or item.get('shares',   0),
                comments=item.get('commentsCount') or item.get('comments', 0),
                platform='Facebook',
                post_url=item.get('url', ''),
                raw_json=json.dumps(item),
            )
            db.session.add(post)
            count += 1

        db.session.commit()
        flash(f'✅ Successfully collected {count} posts!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Data collection failed: {str(e)}', 'danger')

    return redirect(url_for('case_detail', case_id=case_id))


# ─── MODULE ROUTES ────────────────────────────────────────────

@app.route('/case/<int:case_id>/sentiment')
@login_required
def module_sentiment(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    results = []
    counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}

    if posts:
        from modules.sentiment import analyze_sentiment
        results = analyze_sentiment(posts)
        for r in results:
            counts[r['label']] += 1

    return render_template('modules/sentiment.html',
                           case=case, results=results, counts=counts)


@app.route('/case/<int:case_id>/trending')
@login_required
def module_trending(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    hashtags = []
    keywords = []

    if posts:
        from modules.trending import extract_trending, extract_keywords
        hashtags = extract_trending(posts)
        keywords = extract_keywords(posts)

    return render_template('modules/trending.html',
                           case=case, hashtags=hashtags, keywords=keywords)


@app.route('/case/<int:case_id>/network')
@login_required
def module_network(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    stats = {}
    network_data = {'nodes': [], 'edges': []}
    max_score = 0    # ✅ default safe value

    if posts:
        from modules.network import build_network
        stats, network_data, _ = build_network(posts)

        # ✅ safely calculate max_score
        if stats.get('top_nodes'):
            scores = [n['score'] for n in stats['top_nodes']]
            max_score = max(scores) if scores else 0

    return render_template('modules/network.html',
                           case=case,
                           network_data=json.dumps(network_data),
                           stats=stats,
                           max_score=max_score)   # ✅ pass it


@app.route('/case/<int:case_id>/influencer')
@login_required
def module_influencer(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    influencers = []

    if posts:
        from modules.influencer import detect_influencers
        influencers = detect_influencers(posts)

    return render_template('modules/influencer.html',
                           case=case, influencers=influencers)


@app.route('/case/<int:case_id>/segmentation')
@login_required
def module_segmentation(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    segments = []

    if posts:
        from modules.segmentation import segment_users
        segments = segment_users(posts)

    return render_template('modules/segmentation.html',
                           case=case, segments=segments)


@app.route('/case/<int:case_id>/fake-news')
@login_required
def module_fake_news(case_id):
    case = Case.query.get_or_404(case_id)
    posts = Post.query.filter_by(case_id=case_id).all()

    results = detect_fake_news(posts) if posts else []

    # ✅ Compute counts HERE in Python, pass to template
    fake_count = sum(1 for r in results if r['label'] == 'Fake')
    real_count = sum(1 for r in results if r['label'] == 'Real')

    return render_template(
        'modules/fake_news.html',
        case=case,
        results=results,
        fake_count=fake_count,   # ✅ passed explicitly
        real_count=real_count,   # ✅ passed explicitly
    )


@app.route('/case/<int:case_id>/recommendation')
@login_required
def module_recommendation(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    recommendations = []

    if posts:
        from modules.recommendation import get_recommendations
        recommendations = get_recommendations(posts)

    return render_template('modules/recommendation.html',
                           case=case, recommendations=recommendations)


@app.route('/case/<int:case_id>/visualization')
@login_required
def module_visualization(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    # ✅ Convert posts to dicts for Chart.js in template
    posts_json = []
    for p in posts:
        posts_json.append({
            'text': p.text or '',
            'author': p.author or 'Unknown',
            'likes': p.likes or 0,
            'shares': p.shares or 0,
            'comments': p.comments or 0,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        })

    return render_template('modules/visualization.html',
                           case=case, posts=posts_json)


@app.route('/case/<int:case_id>/ad_campaign', methods=['GET'])
@login_required
def module_ad_campaign(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    return render_template('modules/ad_campaign.html', case=case, metrics=None)


@app.route('/case/<int:case_id>/ad_campaign/calculate', methods=['POST'])
@login_required
def calculate_ad_metrics(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()

    from modules.ad_campaign import calculate_metrics
    metrics = calculate_metrics(
        clicks=float(request.form.get('clicks',      0) or 0),
        impressions=float(request.form.get('impressions', 1) or 1),
        conversions=float(request.form.get('conversions', 0) or 0),
        spend=float(request.form.get('spend',       1) or 1),
        revenue=float(request.form.get('revenue',     0) or 0),
    )
    return render_template('modules/ad_campaign.html',
                           case=case, metrics=metrics)


@app.route('/case/<int:case_id>/competitor')
@login_required
def module_competitor(case_id):
    case = Case.query.get_or_404(case_id)
    all_cases = Case.query.filter_by(user_id=current_user.id).all()

    keyword_a = request.args.get('keyword_a', case.keyword).strip()
    keyword_b = request.args.get('keyword_b', '').strip()
    case_b_id = request.args.get('case_b_id', type=int)
    comparison = {}

    if keyword_a and keyword_b:
        # Posts for Brand A — always from current case
        posts_a = Post.query.filter_by(case_id=case_id).all()

        # Posts for Brand B — from selected case or current case
        if case_b_id and case_b_id != case_id:
            posts_b = Post.query.filter_by(case_id=case_b_id).all()
        else:
            # Fallback: filter by keyword_b within current case
            posts_b = [p for p in Post.query.filter_by(case_id=case_id).all()
                       if keyword_b.lower() in (p.text or '').lower()
                       or keyword_b.lower() in (p.author or '').lower()]

        comparison = compare_competitors(
            posts_a, posts_b,
            keyword_a, keyword_b
        )

    return render_template('modules/competitor.html',
                           case=case,
                           all_cases=all_cases,
                           comparison=comparison,
                           keyword_a=keyword_a,
                           keyword_b=keyword_b,
                           case_b_id=case_b_id)


@app.route('/case/<int:case_id>/prediction')
@login_required
def module_prediction(case_id):
    case = Case.query.get_or_404(case_id)
    posts = Post.query.filter_by(case_id=case_id).all()
    # ✅ pass as 'results' — template uses 'results'
    results = predict_engagement(posts) if len(posts) >= 10 else {}
    return render_template('modules/prediction.html',
                           case=case,
                           results=results,
                           new_prediction=None)


@app.route('/case/<int:case_id>/prediction/new', methods=['POST'])
@login_required
def predict_new_post(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    new_prediction = None

    post_text = request.form.get('post_text', '').strip()
    hour = int(request.form.get('hour', 12) or 12)
    weekday = int(request.form.get('day',  1) or 1)

    if not post_text:
        flash('Please enter some post text.', 'warning')
        return redirect(url_for('module_prediction', case_id=case_id))

    if len(posts) >= 10:
        # ✅ Use predict_single — trains on existing posts,
        #    predicts for the new text without touching the DB
        new_prediction = predict_single(posts, post_text, hour, weekday)
    else:
        flash('Need at least 10 posts to make a prediction.', 'warning')
        return redirect(url_for('module_prediction', case_id=case_id))

    # ✅ Re-run full module results so charts still render
    results = predict_engagement(posts)

    # ✅ render_template directly — NOT redirect
    #    (redirect loses new_prediction value)
    return render_template(
        'modules/prediction.html',
        case=case,
        results=results,
        new_prediction=new_prediction,
    )


@app.route('/case/<int:case_id>/realtime')
@login_required
def module_realtime(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    # ✅ FIXED: was missing stats entirely
    stats = {}
    if posts:
        from modules.realtime import get_realtime_stats
        stats = get_realtime_stats(posts)

    return render_template('modules/realtime.html',
                           case=case, stats=stats)


# ─── REPORT ROUTES ────────────────────────────────────────────

@app.route('/case/<int:case_id>/report/html')
@login_required
def download_html_report(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    from reports.html_generator import generate_html_report, build_results_data

    results_data = build_results_data(case, posts)
    output_path = os.path.join('reports', 'output',
                               f'report_case_{case_id}.html')

    success, path = generate_html_report(
        case, posts, results_data, output_path)

    if success:
        return send_file(path,
                         as_attachment=True,
                         download_name=f'PulseIQ_{case.name}_Report.html')
    else:
        flash(f'❌ Report generation failed: {path}', 'danger')
        return redirect(url_for('case_detail', case_id=case_id))


@app.route('/case/<int:case_id>/report/pdf')
@login_required
def download_pdf_report(case_id):
    case = Case.query.filter_by(
        id=case_id, user_id=current_user.id).first_or_404()
    posts = Post.query.filter_by(case_id=case_id).all()

    from reports.pdf_generator import generate_pdf_report
    from reports.html_generator import build_results_data

    results_data = build_results_data(case, posts)
    output_path = os.path.join('reports', 'output',
                               f'report_case_{case_id}.pdf')

    success, path = generate_pdf_report(case, posts, results_data, output_path)

    if success:
        return send_file(path,
                         as_attachment=True,
                         download_name=f'PulseIQ_{case.name}_Report.pdf')
    else:
        flash(f'❌ PDF generation failed: {path}', 'danger')
        return redirect(url_for('case_detail', case_id=case_id))


# ─── RUN ──────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ PulseIQ database ready.")
    app.run(debug=True)
