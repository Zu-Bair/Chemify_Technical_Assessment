from datetime import datetime

from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint

app = Flask(__name__)

# Making DB connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(10), nullable=False, default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    __table_args__ = (
        CheckConstraint(status.in_(['Pending', 'Doing', 'Blocked', 'Done']), name='valid_status'),
    )


# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


# Task History model
class TaskHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    task = db.relationship('Task', backref=db.backref('history', lazy=True))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('task_history', lazy=True))
    deleted_at = db.Column(db.DateTime, default=datetime.utcnow)


# Route to create a user
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data.get('name')

    user = User(name=name)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User created successfully', 'user_id': user.id}), 201


# Route to get a user
@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': {
        'id': user.id,
        'name': user.name
    }})


# Route to update a user
@app.route('/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    name = data.get('name')

    user.name = name
    db.session.commit()

    return jsonify({'message': 'User updated successfully'})


# Route to delete a user
@app.route('/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'})
