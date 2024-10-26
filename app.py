from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATA_FILE = 'data.json'
REPORTS_FILE = 'reports.json'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_posts():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_posts(posts):
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(posts, file, ensure_ascii=False, indent=4)


def load_reports():
    try:
        with open(REPORTS_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_reports(reports):
    with open(REPORTS_FILE, 'w', encoding='utf-8') as file:
        json.dump(reports, file, ensure_ascii=False, indent=4)


def format_date(date_string):
    date_obj = datetime.fromisoformat(date_string)
    return date_obj.strftime('%Y-%m-%d')


app.jinja_env.filters['format_date'] = format_date


def save_report(post_id, reason):
    reports = load_reports()
    new_report = {
        'post_id': post_id,
        'reason': reason,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    reports.append(new_report)
    save_reports(reports)


@app.route('/')
def index():
    query = request.args.get('query', '').lower()
    posts = load_posts()

    if query:
        posts = [post for post in posts if query in post['content'].lower() or any(query in tag.lower() for tag in post['tags'])]

    return render_template('index.html', posts=posts)


@app.route('/post/<int:post_id>')
def post_detail(post_id):
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    if post:
        return render_template('post_detail.html', post=post)
    else:
        return "Post not found", 404


@app.route('/add')
def add():
    return render_template('add_post.html')


@app.route('/add_post', methods=['POST'])
def add_post():
    posts = load_posts()
    content = request.form.get('content')
    tags = request.form.get('tags').split(',')

    # Server-side validation for word limits
    if len(content.split()) > 600:
        flash('The "Main text" section must not exceed 600 words.')
        return redirect(url_for('add'))

    if len(tags) > 20:
        flash('A maximum of 20 tags is allowed.')
        return redirect(url_for('add'))

    # Handle photo uploads (up to 1)
    photos = request.files.getlist('photos')
    
    if len(photos) > 1:
        flash('You can upload a maximum of 1 photo.')
        return redirect(url_for('add'))

    photo_filenames = []
    
    for photo in photos:
        if photo and allowed_file(photo.filename):
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            photo_filenames.append(photo_filename)

    new_post = {
        'id': len(posts) + 1,
        'content': content,
        'tags': [tag.strip() for tag in tags],
        'date': datetime.now().isoformat(),
        'photos': photo_filenames  # Store filenames if uploaded
    }

    posts.append(new_post)
    save_posts(posts)

    return redirect(url_for('index'))


# Route for handling report
@app.route('/report_post/<int:post_id>', methods=['POST'])
def report_post(post_id):
    reason = request.form.get('reason')
    save_report(post_id, reason)
    flash('Your report has been submitted!')
    return redirect(url_for('post_detail', post_id=post_id))


if __name__ == '__main__':
    app.run(debug=True, port=9050)
