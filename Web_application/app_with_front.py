from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func, desc
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from confluent_kafka import Producer
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Set a secret key for sessions

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mypassword@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Initialize Kafka producer
producer = Producer({'bootstrap.servers': 'localhost:9092'})

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

# SQLAlchemy models
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))

    reviews = db.relationship('Review', backref='user', lazy=True)

    def get_id(self):
        return self.user_id

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    thumbnail = db.Column(db.Text)
    image = db.Column(db.Text)
    description = db.Column(db.Text)
    yearpublished = db.Column(db.Float)
    minplayers = db.Column(db.Float)
    maxplayers = db.Column(db.Float)
    playingtime = db.Column(db.Float)
    minage = db.Column(db.Float)
    category = db.Column(ARRAY(db.String))
    usersrated = db.Column(db.Float)
    average = db.Column(db.Float)
    bayesaverage = db.Column(db.Float)
    board_game_rank = db.Column(db.Float)

    reviews = db.relationship('Review', backref='game', lazy=True)

class Review(db.Model):
    __tablename__ = 'reviews'
    rating = db.Column(db.Float)
    id = db.Column(db.Integer, db.ForeignKey('games.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    recommendation_list = db.Column(ARRAY(db.Integer))  # List of up to 5 game IDs

    user = db.relationship('User', backref=db.backref('recommendation', uselist=False))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        results = Game.query.filter(Game.name.ilike(f'%{query}%')).all()
    else:
        results = []
    return render_template('search_results.html', query=query, results=results)


@app.route('/top-ranked-games')
def top_ranked_games():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    top_games = Game.query.order_by(Game.board_game_rank.asc()).paginate(page=page, per_page=per_page, error_out=False)
    next_url = url_for('top_ranked_games', page=top_games.next_num) if top_games.has_next else None
    prev_url = url_for('top_ranked_games', page=top_games.prev_num) if top_games.has_prev else None
    return render_template('top_ranked_games.html', games=top_games.items, next_url=next_url, prev_url=prev_url)

@app.route('/top-rated-games')
def top_rated_games():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    top_games = Game.query.order_by(Game.average.desc()).paginate(page=page, per_page=per_page, error_out=False)
    next_url = url_for('top_rated_games', page=top_games.next_num) if top_games.has_next else None
    prev_url = url_for('top_rated_games', page=top_games.prev_num) if top_games.has_prev else None
    return render_template('top_rated_games.html', games=top_games.items, next_url=next_url, prev_url=prev_url)

@app.route('/most-popular-games')
def most_popular_games():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    popular_games = Game.query.order_by(Game.usersrated.desc()).paginate(page=page, per_page=per_page, error_out=False)
    next_url = url_for('most_popular_games', page=popular_games.next_num) if popular_games.has_next else None
    prev_url = url_for('most_popular_games', page=popular_games.prev_num) if popular_games.has_prev else None
    return render_template('most_popular_games.html', games=popular_games.items, next_url=next_url, prev_url=prev_url)

@app.route('/game/<int:id>')
def game_detail(id):
    game = Game.query.get_or_404(id)
    user_rating = None
    if current_user.is_authenticated:
        review = Review.query.filter_by(id=id, user_id=current_user.user_id).first()
        if review:
            user_rating = review.rating

    # Send message to Kafka regardless of user authentication
    user_id = current_user.user_id if current_user.is_authenticated else None
    event = {'event': 'game_viewed', 'user_id': user_id, 'game_id': id}
    producer.produce('user-events', key=str(user_id), value=json.dumps(event), callback=delivery_report)
    producer.flush()

    return render_template('game_detail.html', game=game, user_rating=user_rating)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(email=email).first():
            flash('Email address already exists')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        # Send message to Kafka
        event = {'event': 'user_created', 'user_id': new_user.user_id, 'username': username}
        producer.produce('user-events', key=str(new_user.user_id), value=json.dumps(event), callback=delivery_report)
        producer.flush()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user or not bcrypt.check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('home'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def user_profile():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    user_ratings = Review.query.filter_by(user_id=current_user.user_id).order_by(Review.rating.desc()).paginate(page=page, per_page=per_page, error_out=False)
    rated_games = [
        {
            'game': Game.query.get(review.id),
            'rating': review.rating
        }
        for review in user_ratings.items
    ]
    next_url = url_for('user_profile', page=user_ratings.next_num) if user_ratings.has_next else None
    prev_url = url_for('user_profile', page=user_ratings.prev_num) if user_ratings.has_prev else None

    # Fetch recommendations
    recommendation = Recommendation.query.filter_by(user_id=current_user.user_id).first()
    recommended_games = []
    if recommendation and recommendation.recommendation_list:
        recommended_games = [Game.query.get(game_id) for game_id in recommendation.recommendation_list]

    return render_template('profile.html', user=current_user, rated_games=rated_games, next_url=next_url, prev_url=prev_url, recommended_games=recommended_games)

@app.route('/rate_game/<int:game_id>', methods=['POST'])
@login_required
def rate_game(game_id):
    game = Game.query.get_or_404(game_id)
    rating = float(request.form.get('rating'))
    
    # Check if the user has already rated this game
    review = Review.query.filter_by(id=game_id, user_id=current_user.user_id).first()
    
    if review:
        review.rating = rating
    else:
        new_review = Review(id=game_id, user_id=current_user.user_id, rating=rating)
        db.session.add(new_review)
    
    db.session.commit()

    # Recalculate average rating and users rated
    reviews = Review.query.filter_by(id=game_id).all()
    total_ratings = sum(review.rating for review in reviews)
    num_ratings = len(reviews)
    average_rating = total_ratings / num_ratings
    
    game.average = average_rating
    game.usersrated = game.usersrated + 1
    db.session.commit()
    
    flash('Your rating has been submitted!')
    return redirect(url_for('game_detail', id=game_id))

if __name__ == '__main__':
    app.run(debug=True)
