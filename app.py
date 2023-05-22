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


# Route to get tasks of a user
@app.route('/users/<user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    user_tasks = []
    for task in tasks:
        user_tasks.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'status': task.status,
            'user_id': task.user_id
        })

    return jsonify({'tasks': user_tasks})


# Route to create a task for a user
@app.route('/users/<user_id>/tasks', methods=['POST'])
def create_user_task(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    status = data.get('status', 'Pending')

    task = Task(title=title, description=description, status=status, user_id=user_id)
    db.session.add(task)
    db.session.commit()

    return jsonify({'message': 'Task created successfully'}), 201


# Route to delete a task of a user
@app.route('/users/<user_id>/tasks/<task_id>', methods=['DELETE'])
def delete_user_task(user_id, task_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    task = Task.query.filter_by(id=task_id, user_id=user_id).first()
    if not task:
        return jsonify({'error': 'Task not found'}), 404

    # Create a TaskHistory record
    task_history = TaskHistory(
        task_id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        user_id=task.user_id
    )
    db.session.add(task_history)

    # Delete the task from the Task table
    db.session.delete(task)
    db.session.commit()

    return jsonify({'message': 'Task deleted successfully'})


# Route to get task history for a user
@app.route('/users/<user_id>/task-history', methods=['GET'])
def get_user_task_history(user_id):

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    task_history = TaskHistory.query.filter_by(user_id=user_id).all()
    task_history_data = []
    for history in task_history:
        task_history_data.append({
            'id': history.id,
            'task_id': history.task_id,
            'title': history.title,
            'description': history.description,
            'status': history.status,
            'deleted_at': history.deleted_at,
        })

    return jsonify(task_history_data)


if __name__ == '__main__':
    app.run(debug=True)


