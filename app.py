from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'finansbank-secret-key-2024-vitec'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ═══════════════════════════════════════════════════════
#  MODELS
# ═══════════════════════════════════════════════════════

class User(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role          = db.Column(db.String(20), default='user')   # 'user' | 'admin'
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def is_admin(self):
        return self.role == 'admin'


class Article(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    section    = db.Column(db.String(50), nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author     = db.relationship('User', backref='articles')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published  = db.Column(db.Boolean, default=True)


class Message(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(120), nullable=False)
    subject    = db.Column(db.String(200), nullable=False)
    body       = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read    = db.Column(db.Boolean, default=False)


# ═══════════════════════════════════════════════════════
#  AUTH DECORATORS
# ═══════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Необходимо войти в систему.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Необходимо войти в систему.', 'warning')
            return redirect(url_for('login'))
        user = db.session.get(User, session['user_id'])
        if not user or not user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.before_request
def load_user():
    g.user = None
    if 'user_id' in session:
        g.user = db.session.get(User, session['user_id'])


# ═══════════════════════════════════════════════════════
#  PUBLIC PAGES
# ═══════════════════════════════════════════════════════

@app.route('/')
def index():
    news = Article.query.filter_by(section='news', published=True).order_by(Article.created_at.desc()).limit(3).all()
    return render_template('index.html', news=news)


@app.route('/deposits')
def deposits():
    articles = Article.query.filter_by(section='deposits', published=True).order_by(Article.created_at.desc()).all()
    return render_template('section.html', articles=articles, section_title='Вклады и депозиты',
                           section_key='deposits', section_icon='piggy-bank',
                           section_desc='Выгодные условия хранения и приумножения ваших средств.')


@app.route('/credits')
def credits():
    articles = Article.query.filter_by(section='credits', published=True).order_by(Article.created_at.desc()).all()
    return render_template('section.html', articles=articles, section_title='Кредиты',
                           section_key='credits', section_icon='credit-card',
                           section_desc='Кредитные продукты для физических и юридических лиц.')


@app.route('/services')
def services():
    articles = Article.query.filter_by(section='services', published=True).order_by(Article.created_at.desc()).all()
    return render_template('section.html', articles=articles, section_title='Услуги',
                           section_key='services', section_icon='briefcase',
                           section_desc='Полный спектр банковских услуг для вас и вашего бизнеса.')


@app.route('/news')
def news():
    articles = Article.query.filter_by(section='news', published=True).order_by(Article.created_at.desc()).all()
    return render_template('section.html', articles=articles, section_title='Новости',
                           section_key='news', section_icon='newspaper',
                           section_desc='Актуальные новости и события банка.')


@app.route('/about')
def about():
    articles = Article.query.filter_by(section='about', published=True).order_by(Article.created_at.desc()).all()
    return render_template('section.html', articles=articles, section_title='О банке',
                           section_key='about', section_icon='building-columns',
                           section_desc='История, миссия и ценности ФинансБанка.')


@app.route('/article/<int:article_id>')
def article_detail(article_id):
    article = Article.query.get_or_404(article_id)
    if not article.published and (not g.user or not g.user.is_admin()):
        abort(404)
    return render_template('articles/detail.html', article=article)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        body    = request.form.get('body', '').strip()
        if not all([name, email, subject, body]):
            flash('Пожалуйста, заполните все поля.', 'danger')
        else:
            msg = Message(name=name, email=email, subject=subject, body=body)
            db.session.add(msg)
            db.session.commit()
            flash('Ваше сообщение отправлено! Мы свяжемся с вами в ближайшее время.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html')


@app.route('/sitemap')
def sitemap():
    return render_template('sitemap.html')


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        results = Article.query.filter(
            Article.published == True,
            (Article.title.ilike(f'%{q}%')) | (Article.body.ilike(f'%{q}%'))
        ).order_by(Article.created_at.desc()).all()
    return render_template('search.html', results=results, query=q)


# ═══════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        error = None
        if not username or not email or not password:
            error = 'Все поля обязательны для заполнения.'
        elif password != confirm:
            error = 'Пароли не совпадают.'
        elif len(password) < 6:
            error = 'Пароль должен содержать не менее 6 символов.'
        elif User.query.filter_by(username=username).first():
            error = 'Пользователь с таким именем уже существует.'
        elif User.query.filter_by(email=email).first():
            error = 'Пользователь с таким email уже существует.'
        if error:
            flash(error, 'danger')
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('index'))
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Неверное имя пользователя или пароль.', 'danger')
        else:
            session['user_id'] = user.id
            flash(f'Добро пожаловать, {user.username}!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


# ═══════════════════════════════════════════════════════
#  ADMIN
# ═══════════════════════════════════════════════════════

@app.route('/admin')
@admin_required
def admin_dashboard():
    total_articles  = Article.query.count()
    total_users     = User.query.count()
    unread_msgs     = Message.query.filter_by(is_read=False).count()
    recent_articles = Article.query.order_by(Article.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html',
                           total_articles=total_articles,
                           total_users=total_users,
                           unread_msgs=unread_msgs,
                           recent_articles=recent_articles)


@app.route('/admin/articles')
@admin_required
def admin_articles():
    articles = Article.query.order_by(Article.created_at.desc()).all()
    return render_template('admin/articles.html', articles=articles)


@app.route('/admin/article/new', methods=['GET', 'POST'])
@admin_required
def admin_article_new():
    if request.method == 'POST':
        title     = request.form.get('title', '').strip()
        body      = request.form.get('body', '').strip()
        section   = request.form.get('section', '').strip()
        published = request.form.get('published') == 'on'
        if not title or not body or not section:
            flash('Заполните все обязательные поля.', 'danger')
        else:
            article = Article(title=title, body=body, section=section,
                              author_id=g.user.id, published=published)
            db.session.add(article)
            db.session.commit()
            flash('Статья создана.', 'success')
            return redirect(url_for('admin_articles'))
    return render_template('admin/article_form.html', article=None)


@app.route('/admin/article/<int:article_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_article_edit(article_id):
    article = Article.query.get_or_404(article_id)
    if request.method == 'POST':
        article.title     = request.form.get('title', '').strip()
        article.body      = request.form.get('body', '').strip()
        article.section   = request.form.get('section', '').strip()
        article.published = request.form.get('published') == 'on'
        article.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Статья обновлена.', 'success')
        return redirect(url_for('admin_articles'))
    return render_template('admin/article_form.html', article=article)


@app.route('/admin/article/<int:article_id>/delete', methods=['POST'])
@admin_required
def admin_article_delete(article_id):
    article = Article.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    flash('Статья удалена.', 'success')
    return redirect(url_for('admin_articles'))


@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/new', methods=['GET', 'POST'])
@admin_required
def admin_user_new():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'user')
        error = None
        if not username or not email or not password:
            error = 'Все поля обязательны.'
        elif User.query.filter_by(username=username).first():
            error = 'Имя пользователя занято.'
        elif User.query.filter_by(email=email).first():
            error = 'Email уже используется.'
        if error:
            flash(error, 'danger')
        else:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Пользователь создан.', 'success')
            return redirect(url_for('admin_users'))
    return render_template('admin/user_form.html', user=None)


@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_user_edit(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username', '').strip()
        user.email    = request.form.get('email', '').strip()
        user.role     = request.form.get('role', 'user')
        new_pw = request.form.get('password', '')
        if new_pw:
            user.set_password(new_pw)
        db.session.commit()
        flash('Пользователь обновлён.', 'success')
        return redirect(url_for('admin_users'))
    return render_template('admin/user_form.html', user=user)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == g.user.id:
        flash('Нельзя удалить самого себя.', 'danger')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('Пользователь удалён.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/messages')
@admin_required
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@app.route('/admin/messages/<int:msg_id>/read', methods=['POST'])
@admin_required
def admin_message_read(msg_id):
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin_messages'))


# ═══════════════════════════════════════════════════════
#  ERROR HANDLERS
# ═══════════════════════════════════════════════════════

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ═══════════════════════════════════════════════════════
#  SEED DATABASE
# ═══════════════════════════════════════════════════════

def seed_db():
    if User.query.count() > 0:
        return

    admin = User(username='admin', email='admin@finansbank.ru', role='admin')
    admin.set_password('admin123')
    client = User(username='client', email='client@mail.ru', role='user')
    client.set_password('client123')
    db.session.add_all([admin, client])
    db.session.commit()

    articles = [
        # ── DEPOSITS ──
        Article(title='Вклад «Надёжный» — 12% годовых',
                body='''<p>Вклад <strong>«Надёжный»</strong> — классический инструмент сохранения капитала с фиксированной ставкой 12% годовых.</p>
<h5>Условия</h5><ul>
<li>Минимальная сумма: 50 000 ₽</li>
<li>Срок: 6, 12 или 24 месяца</li>
<li>Выплата процентов: в конце срока или ежемесячно</li>
<li>Пополнение: не предусмотрено</li>
<li>Досрочное снятие: с потерей начисленных процентов</li>
</ul>
<p>Вклад застрахован в АСВ на сумму до 1 400 000 ₽. Оформить можно онлайн или в любом отделении банка.</p>''',
                section='deposits', author_id=1, published=True,
                created_at=datetime(2026, 4, 23, 10, 0)),
        Article(title='Вклад «Прогрессивный» — ставка до 14%',
                body='''<p>Вклад <strong>«Прогрессивный»</strong> предусматривает увеличение процентной ставки по мере роста остатка.</p>
<h5>Шкала ставок</h5><ul>
<li>До 100 000 ₽ — 10% годовых</li>
<li>100 000–500 000 ₽ — 12% годовых</li>
<li>От 500 000 ₽ — 14% годовых</li>
</ul>
<p>Срок: от 3 до 36 месяцев. Пополнение разрешено в первые 30 дней. Проценты капитализируются ежеквартально.</p>''',
                section='deposits', author_id=1, published=True,
                created_at=datetime(2026, 4, 24, 11, 0)),
        Article(title='Детский вклад «Будущее» — копим вместе',
                body='''<p>Вклад <strong>«Будущее»</strong> открывается на имя ребёнка до 18 лет родителями или законными представителями.</p>
<ul>
<li>Ставка: 11% годовых с ежегодной капитализацией</li>
<li>Срок: до совершеннолетия ребёнка</li>
<li>Пополнение: в любое время без ограничений</li>
<li>Минимальный взнос: 1 000 ₽</li>
</ul>
<p>При накоплении от 300 000 ₽ ставка автоматически повышается до 12%.</p>''',
                section='deposits', author_id=1, published=True,
                created_at=datetime(2026, 4, 25, 9, 0)),
        Article(title='Накопительный счёт «Онлайн» — без заморозки',
                body='''<p>Счёт <strong>«Онлайн»</strong> — гибкий инструмент без фиксированного срока.</p>
<ul>
<li>Ставка: 9,5% на среднемесячный остаток</li>
<li>Пополнение и снятие без ограничений</li>
<li>Минимальный остаток для начисления: 1 000 ₽</li>
<li>Открытие только через интернет-банк или приложение</li>
</ul>
<p>Идеально для формирования финансовой подушки безопасности.</p>''',
                section='deposits', author_id=1, published=True,
                created_at=datetime(2026, 4, 26, 14, 0)),
        Article(title='Валютный депозит — защита в евро и юанях',
                body='''<p>Депозит <strong>«Стабильность»</strong> позволяет хранить средства в иностранной валюте.</p>
<h5>Ставки по валютам</h5><ul>
<li>Доллар США (USD) — 3% годовых</li>
<li>Евро (EUR) — 2,5% годовых</li>
<li>Китайский юань (CNY) — 4% годовых</li>
</ul>
<p>Минимальная сумма: 500 USD / 500 EUR / 3 000 CNY. Срок: 6 или 12 месяцев.</p>''',
                section='deposits', author_id=1, published=True,
                created_at=datetime(2026, 4, 27, 10, 0)),

        # ── CREDITS ──
        Article(title='Потребительский кредит до 3 000 000 ₽',
                body='''<p>Кредит <strong>«На любые цели»</strong> — без залога и поручителей.</p>
<ul>
<li>Сумма: 50 000–3 000 000 ₽</li>
<li>Ставка: от 14,9% годовых</li>
<li>Срок: 1–7 лет</li>
<li>Решение онлайн за 15 минут</li>
<li>Досрочное погашение без штрафов</li>
</ul>
<p>Требования: гражданство РФ, возраст 21–70 лет, стаж от 3 месяцев, доход от 25 000 ₽/мес.</p>''',
                section='credits', author_id=1, published=True,
                created_at=datetime(2026, 4, 23, 12, 0)),
        Article(title='Ипотека «Семейная» — 6% годовых',
                body='''<p>Программа <strong>«Семейная ипотека»</strong> для семей с детьми, рождёнными с 01.01.2018.</p>
<ul>
<li>Ставка: 6% (субсидируется государством)</li>
<li>Первоначальный взнос: от 20%</li>
<li>Сумма: до 12 000 000 ₽ (Москва/СПб)</li>
<li>Срок: до 30 лет</li>
<li>Объект: первичный рынок</li>
</ul>''',
                section='credits', author_id=1, published=True,
                created_at=datetime(2026, 4, 24, 13, 0)),
        Article(title='Автокредит «Движение» — новые и б/у авто',
                body='''<p>Автокредит <strong>«Движение»</strong> — выгодные условия для покупки любого автомобиля.</p>
<ul>
<li>Новые авто — от 12,5% годовых</li>
<li>Авто с пробегом — от 16% годовых</li>
<li>Первоначальный взнос: от 10%</li>
<li>Сумма: до 5 000 000 ₽, срок до 7 лет</li>
</ul>
<p>Доступна программа трейд-ин: зачёт старого авто в первоначальный взнос.</p>''',
                section='credits', author_id=1, published=True,
                created_at=datetime(2026, 4, 25, 11, 0)),
        Article(title='Кредитная карта «Кэшбэк Про»',
                body='''<p>Карта <strong>«Кэшбэк Про»</strong> — умный финансовый инструмент с реальной выгодой.</p>
<ul>
<li>Кэшбэк 5% в категориях «Рестораны» и «АЗС»</li>
<li>Кэшбэк 1% на все остальные покупки</li>
<li>Беспроцентный период до 120 дней</li>
<li>Лимит до 1 000 000 ₽</li>
<li>Бесплатное обслуживание при обороте от 10 000 ₽/мес.</li>
</ul>''',
                section='credits', author_id=1, published=True,
                created_at=datetime(2026, 4, 26, 10, 0)),
        Article(title='Рефинансирование — объедините до 5 кредитов',
                body='''<p>Программа <strong>«Рефинансирование»</strong> снижает нагрузку на бюджет.</p>
<ul>
<li>Ставка: от 12% годовых</li>
<li>Сумма: 100 000–5 000 000 ₽</li>
<li>Срок: до 7 лет</li>
<li>Объединение кредитов наличными, автокредитов, карт</li>
</ul>
<p>Среднее снижение платежа — 25–40% в месяц.</p>''',
                section='credits', author_id=1, published=True,
                created_at=datetime(2026, 4, 27, 9, 0)),

        # ── SERVICES ──
        Article(title='Дебетовая карта «Максимум»',
                body='''<p>Карта <strong>«Максимум»</strong> — всё в одном инструменте.</p>
<ul>
<li>До 8% годовых на остаток по счёту</li>
<li>Кэшбэк до 3% на все покупки</li>
<li>Бесплатное снятие наличных в любых банкоматах России</li>
<li>Бесплатные переводы по СБП</li>
</ul>
<p>Обслуживание бесплатно при покупках от 5 000 ₽/мес. или остатке от 30 000 ₽.</p>''',
                section='services', author_id=1, published=True,
                created_at=datetime(2026, 4, 23, 9, 0)),
        Article(title='Мобильное приложение ФинансБанк',
                body='''<p><strong>ФинансБанк Онлайн</strong> — полноценный банк в вашем смартфоне, 24/7.</p>
<ul>
<li>Открытие вкладов и счетов онлайн</li>
<li>Переводы по номеру карты, телефона или СБП</li>
<li>Оплата ЖКХ, налогов, штрафов, мобильной связи</li>
<li>Управление кредитами и просмотр графика платежей</li>
</ul>
<p>Доступно для iOS и Android. Двухфакторная аутентификация и биометрический вход.</p>''',
                section='services', author_id=1, published=True,
                created_at=datetime(2026, 4, 24, 10, 0)),
        Article(title='РКО для бизнеса — три тарифа',
                body='''<p>Расчётно-кассовое обслуживание для ИП и юридических лиц.</p>
<h5>Тарифы</h5><ul>
<li><strong>Старт</strong> — 0 ₽/мес.: 3 бесплатных платёжных поручения</li>
<li><strong>Бизнес</strong> — 990 ₽/мес.: 20 бесплатных поручений</li>
<li><strong>Профи</strong> — 2 490 ₽/мес.: неограниченное количество</li>
</ul>
<p>Открытие счёта онлайн за 1 рабочий день. Интеграция с 1С и онлайн-кассами.</p>''',
                section='services', author_id=1, published=True,
                created_at=datetime(2026, 4, 25, 12, 0)),
        Article(title='Эквайринг — приём оплаты картами и QR',
                body='''<p>Торговый и интернет-эквайринг от ФинансБанка.</p>
<ul>
<li>Комиссия: от 1,4% для торговли, от 1,8% для услуг</li>
<li>Терминалы в аренду или в собственность</li>
<li>Зачисление средств на следующий рабочий день</li>
<li>Техподдержка 24/7</li>
</ul>
<p>Готовые модули для 1С-Битрикс, WordPress/WooCommerce, Tilda. Мобильный mPOS для выездной торговли.</p>''',
                section='services', author_id=1, published=True,
                created_at=datetime(2026, 4, 26, 11, 0)),
        Article(title='Страхование жизни и имущества',
                body='''<p>Комплексные программы страховой защиты от партнёров ФинансБанка.</p>
<ul>
<li><strong>Защита жизни</strong> — до 10 000 000 ₽ при НС</li>
<li><strong>Защита имущества</strong> — квартира, дом, дача</li>
<li><strong>Путешественник</strong> — ВЗР от 350 ₽</li>
<li><strong>Защита кредита</strong> — страхование жизни заёмщика</li>
</ul>
<p>Оформление полиса онлайн за 3 минуты. Выплаты в течение 10 рабочих дней.</p>''',
                section='services', author_id=1, published=True,
                created_at=datetime(2026, 4, 27, 13, 0)),

        # ── NEWS ──
        Article(title='ФинансБанк снизил ставку по ипотеке до 10,5%',
                body='''<p>С 23 апреля 2026 года ФинансБанк снижает базовую ставку по стандартным ипотечным программам до <strong>10,5% годовых</strong>.</p>
<p>Решение принято в связи с изменением ключевой ставки ЦБ России. Новые условия распространяются на все заявки с 23 апреля 2026 года. Заёмщики с ранее одобренными условиями могут запросить пересмотр в течение 30 дней.</p>''',
                section='news', author_id=1, published=True,
                created_at=datetime(2026, 4, 23, 8, 0)),
        Article(title='Открытие нового отделения на Арбате — 25 апреля',
                body='''<p>25 апреля 2026 года ФинансБанк открыл новое отделение по адресу <strong>ул. Арбат, д. 12</strong>.</p>
<p>Формат «банк нового поколения»: открытое пространство, живая очередь без талонов, зоны самообслуживания. Часы работы: пн–пт 9:00–21:00, сб 10:00–18:00. До 30 апреля 2026 года всем новым клиентам отделения — приветственный кэшбэк 500 ₽.</p>''',
                section='news', author_id=1, published=True,
                created_at=datetime(2026, 4, 25, 8, 0)),
        Article(title='ФинансБанк — в топ-10 надёжных банков России 2026',
                body='''<p>По рейтингу агентства «Эксперт РА» ФинансБанк занял <strong>8-е место</strong> среди частных банков с рейтингом <strong>ruA+</strong> и прогнозом «стабильный».</p>
<p>Аналитики отметили высокий уровень достаточности капитала (H1.0 = 18,4%), низкую долю просроченных кредитов (2,1%) и устойчивую клиентскую базу.</p>''',
                section='news', author_id=1, published=True,
                created_at=datetime(2026, 4, 26, 9, 0)),
        Article(title='Запуск мобильного приложения 2.0 — 27 апреля',
                body='''<p>27 апреля 2026 года выпущена новая версия приложения <strong>«ФинансБанк 2.0»</strong>.</p>
<ul>
<li>Новый интерфейс в стиле Material You</li>
<li>Встроенный финансовый помощник на базе ИИ</li>
<li>Категоризация расходов и умные лимиты</li>
<li>Виджеты на рабочий стол iOS и Android</li>
</ul>
<p>Обновившиеся до 30 апреля 2026 года получают бонус 100 ₽ на счёт.</p>''',
                section='news', author_id=1, published=True,
                created_at=datetime(2026, 4, 27, 10, 0)),
        Article(title='Партнёрство с Ozon Fintech — 28 апреля',
                body='''<p>28 апреля 2026 года ФинансБанк и Ozon Fintech подписали соглашение о стратегическом партнёрстве.</p>
<p>Клиенты получат кэшбэк до <strong>7%</strong> при оплате картой «Максимум» на Ozon. Совместная карта <strong>«ФинансБанк × Ozon»</strong> выйдет в мае 2026 года.</p>''',
                section='news', author_id=1, published=True,
                created_at=datetime(2026, 4, 28, 11, 0)),

        # ── ABOUT ──
        Article(title='История ФинансБанка — 30 лет надёжности',
                body='''<p>ФинансБанк основан в <strong>1996 году</strong> в Москве. За три десятилетия вырос до 2,5 млн клиентов и 180 отделений по всей России.</p>
<h5>Ключевые вехи</h5><ul>
<li><strong>1996</strong> — получение генеральной лицензии ЦБ РФ</li>
<li><strong>2003</strong> — выход в регионы, 12 городов</li>
<li><strong>2008–2009</strong> — прохождение кризиса без господдержки</li>
<li><strong>2015</strong> — запуск мобильного банкинга</li>
<li><strong>2020</strong> — рост клиентской базы на 40% в период пандемии</li>
<li><strong>2026</strong> — 2,5 млн клиентов, 180 отделений</li>
</ul>''',
                section='about', author_id=1, published=True,
                created_at=datetime(2026, 4, 23, 8, 0)),
        Article(title='Миссия и ценности банка',
                body='''<p>Миссия: <strong>«Делать финансы простыми, доступными и надёжными для каждого»</strong>.</p>
<h5>Ценности</h5><ul>
<li><strong>Надёжность</strong> — обязательства выполняются точно в срок</li>
<li><strong>Прозрачность</strong> — никаких скрытых комиссий</li>
<li><strong>Клиентоцентричность</strong> — каждый клиент важен</li>
<li><strong>Инновации</strong> — постоянное внедрение технологий</li>
<li><strong>Ответственность</strong> — перед клиентами и обществом</li>
</ul>''',
                section='about', author_id=1, published=True,
                created_at=datetime(2026, 4, 24, 9, 0)),
        Article(title='Руководство банка',
                body='''<h5>Председатель правления</h5>
<p><strong>Андрей Викторович Белов</strong> — возглавляет банк с 2018 года, ранее занимал позиции топ-менеджера в Сбербанке и ВТБ. Кандидат экономических наук, выпускник МГУ и London Business School.</p>
<h5>Наблюдательный совет</h5>
<p>7 независимых директоров с опытом в банкинге, праве и корпоративном управлении. Банк ежегодно публикует отчётность по МСФО с аудитом «Большой четвёрки».</p>''',
                section='about', author_id=1, published=True,
                created_at=datetime(2026, 4, 25, 10, 0)),
        Article(title='Лицензии и надзор ЦБ РФ',
                body='''<p>ФинансБанк работает под надзором Центрального банка Российской Федерации.</p>
<h5>Лицензии</h5><ul>
<li>Генеральная лицензия на банковские операции № 3147 от 14.03.1996</li>
<li>Лицензия профессионального участника рынка ценных бумаг</li>
<li>Лицензия на управление ценными бумагами</li>
</ul>
<p>Участник системы страхования вкладов АСВ: вклады физлиц застрахованы до <strong>1 400 000 ₽</strong>.</p>''',
                section='about', author_id=1, published=True,
                created_at=datetime(2026, 4, 26, 9, 0)),
        Article(title='Социальная ответственность — «Финансы для будущего»',
                body='''<p>Программа КСО ФинансБанка охватывает образование, экологию и благотворительность.</p>
<ul>
<li><strong>Финансовая грамотность</strong> — бесплатные семинары в школах и библиотеках</li>
<li><strong>Поддержка молодёжи</strong> — 50 стипендий студентам финансовых специальностей ежегодно</li>
<li><strong>Экология</strong> — программа безбумажного банкинга, снижение CO₂ на 30% к 2030 году</li>
<li><strong>Благотворительность</strong> — 1% от прибыли в фонды помощи детям</li>
</ul>
<p>В 2025 году проведено 200+ образовательных мероприятий, охват — более 15 000 участников.</p>''',
                section='about', author_id=1, published=True,
                created_at=datetime(2026, 4, 27, 10, 0)),
    ]

    db.session.add_all(articles)
    db.session.commit()
    print('Database seeded successfully.')


with app.app_context():
    db.create_all()
    seed_db()

@app.context_processor
def inject_recent_news():
    recent_news = Article.query.filter_by(section='news', published=True).order_by(Article.created_at.desc()).limit(4).all()
    return dict(recent_news=recent_news)

@app.context_processor
def inject_unread():
    from flask import request as req
    if req.endpoint and req.endpoint.startswith('admin'):
        unread = Message.query.filter_by(is_read=False).count()
    else:
        unread = 0
    return dict(unread_count=unread)

if __name__ == '__main__':
    app.run(debug=True)