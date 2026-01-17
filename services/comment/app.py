from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')

# Initialize extensions
db = SQLAlchemy(app)
cors = CORS(app)
jwt = JWTManager(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logger.warning("JWT Token expired")
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logger.warning(f"Invalid JWT token: {error}")
    return jsonify({'error': 'Invalid token'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    logger.warning(f"Missing JWT token: {error}")
    return jsonify({'error': 'Authorization token required'}), 401

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'comment-service'}), 200

@app.route('/api/comments', methods=['POST'])
def create_comment():
    """Create a new comment (public, no auth required for frontend)"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('post_id') or not data.get('author_name') or not data.get('content'):
            return jsonify({'error': 'Post ID, author name, and content required'}), 400
        
        comment = Comment(
            post_id=data['post_id'],
            author_name=data['author_name'].strip(),
            author_email=data['author_email'].strip() if data.get('author_email') else None,
            content=data['content'].strip(),
            status='pending'  # Comments start as pending (moderation)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f"Comment created on post {comment.post_id}: {comment.id}")
        return jsonify({
            'message': 'Comment created successfully',
            'comment_id': comment.id
        }), 201
        
    except Exception as e:
        logger.error(f"Create comment error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/post/<int:post_id>', methods=['GET'])
def get_comments(post_id):
    """Get all approved comments for a post"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        comments = Comment.query.filter_by(
            post_id=post_id,
            status='approved'
        ).order_by(Comment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'comments': [{
                'id': comment.id,
                'post_id': comment.post_id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            } for comment in comments.items],
            'total': comments.total,
            'pages': comments.pages,
            'current_page': comments.page
        }), 200
        
    except Exception as e:
        logger.error(f"Get comments error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
def delete_comment(comment_id):
    """Delete a comment (requires JWT for moderation)"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        db.session.delete(comment)
        db.session.commit()
        logger.info(f"Comment {comment_id} deleted")
        return jsonify({'message': 'Comment deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete comment error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/<int:comment_id>/approve', methods=['PUT'])
@jwt_required()
def approve_comment(comment_id):
    """Approve a comment (requires JWT for moderation)"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.status = 'approved'
        db.session.commit()
        logger.info(f"Comment {comment_id} approved")
        return jsonify({'message': 'Comment approved'}), 200
        
    except Exception as e:
        logger.error(f"Approve comment error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/<int:comment_id>/reject', methods=['PUT'])
@jwt_required()
def reject_comment(comment_id):
    """Reject a comment (requires JWT for moderation)"""
    try:
        comment = Comment.query.get_or_404(comment_id)
        comment.status = 'rejected'
        db.session.commit()
        logger.info(f"Comment {comment_id} rejected")
        return jsonify({'message': 'Comment rejected'}), 200
        
    except Exception as e:
        logger.error(f"Reject comment error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/pending', methods=['GET'])
@jwt_required()
def get_pending_comments():
    """Get all pending comments for moderation (requires JWT)"""
    try:
        pending = Comment.query.filter_by(status='pending').order_by(
            Comment.created_at.asc()
        ).all()
        
        return jsonify({
            'pending_comments': [{
                'id': comment.id,
                'post_id': comment.post_id,
                'author_name': comment.author_name,
                'author_email': comment.author_email,
                'content': comment.content,
                'created_at': comment.created_at.isoformat()
            } for comment in pending]
        }), 200
        
    except Exception as e:
        logger.error(f"Get pending comments error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/comments/health', methods=['GET'])
def comment_health():
    """Comment service health check with DB connection test"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'service': 'comment-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'comment-service',
            'error': str(e)
        }), 500

# Database initialization
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5003)),
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )

