from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from datetime import datetime
from dotenv import load_dotenv
import os
import logging
import re

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
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(500))
    status = db.Column(db.Enum('draft', 'published'), default='draft')
    author_id = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer)
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
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

# Helper functions
def create_slug(title):
    """Convert title to URL-safe slug"""
    return re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')

# Routes
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'post-service'}), 200

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """Get all published posts with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status', 'published')
        
        query = Post.query.filter_by(status=status).order_by(Post.published_at.desc())
        posts = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'posts': [{
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content': post.content,
                'excerpt': post.excerpt,
                'featured_image': post.featured_image,
                'status': post.status,
                'author_id': post.author_id,
                'category_id': post.category_id,
                'created_at': post.created_at.isoformat(),
                'published_at': post.published_at.isoformat() if post.published_at else None
            } for post in posts.items],
            'total': posts.total,
            'pages': posts.pages,
            'current_page': posts.page
        }), 200
    except Exception as e:
        logger.error(f"Get posts error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get single post by ID"""
    try:
        post = Post.query.get_or_404(post_id)
        return jsonify({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'content': post.content,
            'excerpt': post.excerpt,
            'featured_image': post.featured_image,
            'status': post.status,
            'author_id': post.author_id,
            'category_id': post.category_id,
            'meta_title': post.meta_title,
            'meta_description': post.meta_description,
            'created_at': post.created_at.isoformat(),
            'published_at': post.published_at.isoformat() if post.published_at else None
        }), 200
    except Exception as e:
        logger.error(f"Get post error: {str(e)}")
        return jsonify({'error': 'Post not found'}), 404

@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    """Create a new post (requires JWT)"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validation
        if not data.get('title') or not data.get('title').strip():
            return jsonify({'error': 'Title is required'}), 400
        
        content = data.get('content', '').strip()
        if not content or content in ['<p><br></p>', '<p></p>', '<br>', '']:
            return jsonify({'error': 'Content is required'}), 400
        
        # Create unique slug
        slug = create_slug(data['title'])
        counter = 1
        original_slug = slug
        while Post.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        category_id = data.get('category_id')
        if category_id in ['', 'null', None]:
            category_id = None
        else:
            try:
                category_id = int(category_id)
            except (ValueError, TypeError):
                category_id = None
        
        post = Post(
            title=data['title'].strip(),
            slug=slug,
            content=content,
            excerpt=data.get('excerpt', '').strip() if data.get('excerpt') else None,
            featured_image=data.get('featured_image'),
            status=data.get('status', 'draft'),
            author_id=user_id,
            category_id=category_id,
            meta_title=data.get('meta_title', '').strip() if data.get('meta_title') else None,
            meta_description=data.get('meta_description', '').strip() if data.get('meta_description') else None
        )
        
        if post.status == 'published':
            post.published_at = datetime.utcnow()
        
        db.session.add(post)
        db.session.commit()
        
        logger.info(f"Post created by user {user_id}: {post.id}")
        return jsonify({'message': 'Post created successfully', 'post_id': post.id}), 201
        
    except Exception as e:
        logger.error(f"Create post error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    """Update a post (requires JWT, owner or admin)"""
    try:
        user_id = int(get_jwt_identity())
        post = Post.query.get_or_404(post_id)
        
        # Authorization check (simplified - service trusts gateway validation)
        if post.author_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if 'title' in data:
            post.title = data['title']
            post.slug = create_slug(data['title'])
        
        if 'content' in data:
            post.content = data['content']
        
        if 'excerpt' in data:
            post.excerpt = data['excerpt']
        
        if 'featured_image' in data:
            post.featured_image = data['featured_image']
        
        if 'status' in data:
            old_status = post.status
            post.status = data['status']
            if old_status != 'published' and data['status'] == 'published':
                post.published_at = datetime.utcnow()
        
        if 'category_id' in data:
            post.category_id = data['category_id']
        
        if 'meta_title' in data:
            post.meta_title = data['meta_title']
        
        if 'meta_description' in data:
            post.meta_description = data['meta_description']
        
        db.session.commit()
        logger.info(f"Post {post_id} updated by user {user_id}")
        return jsonify({'message': 'Post updated successfully'}), 200
        
    except Exception as e:
        logger.error(f"Update post error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    """Delete a post (requires JWT, owner or admin)"""
    try:
        user_id = int(get_jwt_identity())
        post = Post.query.get_or_404(post_id)
        
        # Authorization check
        if post.author_id != user_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        db.session.delete(post)
        db.session.commit()
        logger.info(f"Post {post_id} deleted by user {user_id}")
        return jsonify({'message': 'Post deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Delete post error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    try:
        categories = Category.query.all()
        return jsonify([{
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'description': cat.description
        } for cat in categories]), 200
    except Exception as e:
        logger.error(f"Get categories error: {str(e)}")
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create a new category (requires JWT)"""
    try:
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        category = Category(
            name=data['name'],
            slug=create_slug(data['name']),
            description=data.get('description')
        )
        
        db.session.add(category)
        db.session.commit()
        logger.info(f"Category created: {category.id}")
        return jsonify({'message': 'Category created successfully', 'category_id': category.id}), 201
        
    except Exception as e:
        logger.error(f"Create category error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Server error'}), 500

@app.route('/api/posts/health', methods=['GET'])
def post_health():
    """Post service health check with DB connection test"""
    try:
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'service': 'post-service',
            'database': 'connected'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'post-service',
            'error': str(e)
        }), 500

# Database initialization
@app.before_request
def create_tables():
    db.create_all()

if __name__ == '__main__':
    app.run(
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', 5002)),
        debug=os.getenv('FLASK_DEBUG', 'False') == 'True'
    )

