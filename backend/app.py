from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging
import uuid

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    anon_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_uuid = db.Column(db.String(36), db.ForeignKey('post.uuid'), nullable=False)
    anon_name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class UserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    anon_name = db.Column(db.String(50), nullable=False)
    action_type = db.Column(db.String(10), nullable=False)  # 'post', 'comment', 'like', 'dislike'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

db.create_all()

# Setup logging
logging.basicConfig(filename='safety_logs.txt', level=logging.INFO, format='%(asctime)s %(message)s')

def log_user_activity(anon_name, request, action, content=""):
    ip = request.remote_addr
    user_agent = request.user_agent.string
    logging.info(f'[{anon_name}]: Device: {user_agent}; IP Address: {ip}; Action: {action}; Content: {content}; Time: {datetime.now()}')

def is_moderator(request):
    user_agent = request.user_agent.string
    with open('moderators.txt') as f:
        moderators = f.read().splitlines()
    for line in moderators:
        if user_agent in line:
            return line.split(',')[1]  # Return the unique moderator name
    return None

@app.route('/')
def index():
    new_visitor = Visitor()
    db.session.add(new_visitor)
    db.session.commit()
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/posts', methods=['GET', 'POST'])
def handle_posts():
    if request.method == 'POST':
        data = request.get_json()
        new_post = Post(anon_name=data['anon_name'], content=data['content'])
        db.session.add(new_post)
        db.session.commit()
        log_user_activity(data['anon_name'], request, 'post', data['content'])
        return jsonify({'message': 'Post created', 'uuid': new_post.uuid}), 201

    posts = Post.query.all()
    return jsonify([{
        'id': post.id,
        'uuid': post.uuid,
        'anon_name': f'<i class="fas fa-user-shield blue-moderator-icon"></i> {post.anon_name}' if is_moderator(request) else post.anon_name,
        'content': post.content,
        'likes': post.likes,
        'dislikes': post.dislikes,
        'comments': Comment.query.filter_by(post_uuid=post.uuid).count()
    } for post in posts])

@app.route('/posts/<string:post_uuid>/comments', methods=['GET', 'POST'])
def handle_comments(post_uuid):
    if request.method == 'POST':
        data = request.get_json()
        new_comment = Comment(post_uuid=post_uuid, anon_name=data['anon_name'], content=data['content'])
        db.session.add(new_comment)
        db.session.commit()
        log_user_activity(data['anon_name'], request, 'comment', data['content'])
        return jsonify({'message': 'Comment added'}), 201

    comments = Comment.query.filter_by(post_uuid=post_uuid).all()
    return jsonify([{
        'id': comment.id,
        'anon_name': f'<i class="fas fa-user-shield blue-moderator-icon"></i> {comment.anon_name}' if is_moderator(request) else comment.anon_name,
        'content': comment.content
    } for comment in comments])

@app.route('/posts/<int:post_id>/like', methods=['POST'])
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    anon_name = request.headers.get('Anon-Name')

    existing_action = UserAction.query.filter_by(post_id=post_id, anon_name=anon_name).first()
    if existing_action:
        if existing_action.action_type == 'like':
            return jsonify({'message': 'Already liked'}), 400
        elif existing_action.action_type == 'dislike':
            post.dislikes -= 1
            db.session.delete(existing_action)
    
    new_action = UserAction(post_id=post_id, anon_name=anon_name, action_type='like')
    post.likes += 1
    db.session.add(new_action)
    db.session.commit()
    log_user_activity(anon_name, request, 'like')
    return jsonify({'likes': post.likes})

@app.route('/posts/<int:post_id>/dislike', methods=['POST'])
def dislike_post(post_id):
    post = Post.query.get_or_404(post_id)
    anon_name = request.headers.get('Anon-Name')

    existing_action = UserAction.query.filter_by(post_id=post_id, anon_name=anon_name).first()
    if existing_action:
        if existing_action.action_type == 'dislike':
            return jsonify({'message': 'Already disliked'}), 400
        elif existing_action.action_type == 'like':
            post.likes -= 1
            db.session.delete(existing_action)
    
    new_action = UserAction(post_id=post_id, anon_name=anon_name, action_type='dislike')
    post.dislikes += 1
    db.session.add(new_action)
    db.session.commit()
    log_user_activity(anon_name, request, 'dislike')
    return jsonify({'dislikes': post.dislikes})

@app.route('/stats', methods=['GET'])
def get_stats():
    total_visitors = Visitor.query.count()
    total_posts = Post.query.count()
    return jsonify({
        'total_visitors': total_visitors,
        'total_posts': total_posts
    })

@app.route('/posts/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    moderator_name = is_moderator(request)
    if not moderator_name:
        return jsonify({'message': 'Unauthorized'}), 403

    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    log_user_activity(moderator_name, request, 'delete_post', str(post_id))
    return jsonify({'message': 'Post deleted'})

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    moderator_name = is_moderator(request)
    if not moderator_name:
        return jsonify({'message': 'Unauthorized'}), 403

    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    log_user_activity(moderator_name, request, 'delete_comment', str(comment_id))
    return jsonify({'message': 'Comment deleted'})

if __name__ == '__main__':
    app.run(debug=True)
