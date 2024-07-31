from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import func, desc
import urllib.parse

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mypassword@localhost:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQLAlchemy models
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))

    reviews = db.relationship('Review', backref='user', lazy=True)

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

# Routes
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.limit(10).all()
    return jsonify([{
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email
    } for user in users])

@app.route('/games', methods=['GET'])
def get_games():
    games = Game.query.limit(10).all()
    return jsonify([{
        'id': game.id,
        'name': game.name,
        'thumbnail': game.thumbnail,
        'image': game.image,
        'description': game.description,
        'yearpublished': game.yearpublished,
        'minplayers': game.minplayers,
        'maxplayers': game.maxplayers,
        'playingtime': game.playingtime,
        'minage': game.minage,
        'category': game.category,
        'usersrated': game.usersrated,
        'average': game.average,
        'bayesaverage': game.bayesaverage,
        'board_game_rank': game.board_game_rank
    } for game in games])

@app.route('/reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.limit(10).all()
    return jsonify([{
        'rating': review.rating,
        'id': review.id,
        'user_id': review.user_id
    } for review in reviews])

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.filter_by(user_id=user_id).first()
    if user:
        user_reviews = Review.query.filter_by(user_id=user_id).all()
        reviews = [{
            'rating': review.rating,
            'id': review.id,
            'user_id': review.user_id
        } for review in user_reviews]
        return jsonify({
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'reviews': reviews
        })
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/game/<int:id>', methods=['GET'])
def get_game(id):
    game = Game.query.filter_by(id=id).first()
    if game:
        game_reviews = Review.query.filter_by(id=id).all()
        reviews = [{
            'rating': review.rating,
            'id': review.id,
            'user_id': review.user_id
        } for review in game_reviews]
        return jsonify({
            'id': game.id,
            'name': game.name,
            'thumbnail': game.thumbnail,
            'image': game.image,
            'description': game.description,
            'yearpublished': game.yearpublished,
            'minplayers': game.minplayers,
            'maxplayers': game.maxplayers,
            'playingtime': game.playingtime,
            'minage': game.minage,
            'category': game.category,
            'usersrated': game.usersrated,
            'average': game.average,
            'bayesaverage': game.bayesaverage,
            'board_game_rank': game.board_game_rank,
            'reviews': reviews
        })
    else:
        return jsonify({'message': 'Game not found'}), 404

@app.route('/games/category/<path:category>', methods=['GET'])
def get_games_by_category(category):
    category = urllib.parse.unquote(category)  # Decode the category
    games = Game.query.filter(func.cast(Game.category, ARRAY(db.String)).contains([category])).all()
    return jsonify([{
        'id': game.id,
        'name': game.name,
        'thumbnail': game.thumbnail,
        'image': game.image,
        'description': game.description,
        'yearpublished': game.yearpublished,
        'minplayers': game.minplayers,
        'maxplayers': game.maxplayers,
        'playingtime': game.playingtime,
        'minage': game.minage,
        'category': game.category,
        'usersrated': game.usersrated,
        'average': game.average,
        'bayesaverage': game.bayesaverage,
        'board_game_rank': game.board_game_rank
    } for game in games])

@app.route('/games/categories', methods=['GET'])
def get_categories():
    categories = db.session.query(Game.category).all()
    unique_categories = set()
    for category_list in categories:
        if category_list[0]:  # Check if category_list[0] is not None
            unique_categories.update(category_list[0])
    return jsonify(sorted(unique_categories))

@app.route('/games/top-rated', methods=['GET'])
def get_top_rated_games():
    games = Game.query.order_by(desc(Game.average)).limit(10).all()
    top_rated_games = [{'id': g.id, 'name': g.name, 'average': g.average} for g in games]
    return jsonify({'top_rated_games': top_rated_games})

@app.route('/games/most-popular', methods=['GET'])
def get_most_popular_games():
    games = Game.query.order_by(desc(Game.usersrated)).limit(10).all()
    most_popular_games = [{'id': g.id, 'name': g.name, 'usersrated': g.usersrated} for g in games]
    return jsonify({'most_popular_games': most_popular_games})

@app.route('/games/top-ranked', methods=['GET'])
def get_top_ranked_games():
    games = Game.query.order_by(Game.board_game_rank).limit(10).all()
    top_ranked_games = [{'id': g.id, 'name': g.name, 'board_game_rank': g.board_game_rank} for g in games]
    return jsonify({'top_ranked_games': top_ranked_games})

if __name__ == '__main__':
    app.run(debug=True)
