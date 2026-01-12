from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import uuid

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blog_user:BlogPass123!@localhost/blog_cms'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'blog-cms-secret-key-2026-super-secure'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=1)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize extensions
db = SQLAlchemy(app)
cors = CORS(app)
jwt = JWTManager(app)

# Add request logging
@app.before_request
def log_request_info():
    if request.method == 'POST' and 'posts' in request.path:
        print(f"=== INCOMING REQUEST ===")
        print(f"Method: {request.method}")
        print(f"Path: {request.path}")
        print(f"Headers: {dict(request.headers)}")
        print(f"Content Type: {request.content_type}")
        print(f"Authorization Header: {request.headers.get('Authorization', 'MISSING')}")

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print("JWT TOKEN EXPIRED")
    return jsonify({'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"INVALID JWT TOKEN: {error}")
    return jsonify({'error': 'Invalid token'}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"MISSING JWT TOKEN: {error}")
    return jsonify({'error': 'Authorization token required'}), 401

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('admin', 'author'), default='author')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    posts = db.relationship('Post', backref='author', lazy=True)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    posts = db.relationship('Post', backref='category', lazy=True)

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(250), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    featured_image = db.Column(db.String(500))
    status = db.Column(db.Enum('draft', 'published'), default='draft')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime)
    
    comments = db.relationship('Comment', backref='post', lazy=True)

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('pending', 'approved', 'rejected'), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper functions
def create_slug(title):
    import re
    return re.sub(r'[^\w\s-]', '', title.lower()).replace(' ', '-')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            'access_token': access_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            }
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'author')
    )
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'access_token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
    })

@app.route('/api/posts', methods=['GET'])
def get_posts():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status', 'published')
    
    posts = Post.query.filter_by(status=status).order_by(Post.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [{
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'content': post.content,
            'excerpt': post.excerpt,
            'featured_image': post.featured_image,
            'status': post.status,
            'author': {
                'id': post.author.id,
                'username': post.author.username
            },
            'category': {
                'id': post.category.id,
                'name': post.category.name
            } if post.category else None,
            'created_at': post.created_at.isoformat(),
            'published_at': post.published_at.isoformat() if post.published_at else None
        } for post in posts.items],
        'total': posts.total,
        'pages': posts.pages,
        'current_page': posts.page
    })

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get_or_404(post_id)
    return jsonify({
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'content': post.content,
        'excerpt': post.excerpt,
        'featured_image': post.featured_image,
        'status': post.status,
        'meta_title': post.meta_title,
        'meta_description': post.meta_description,
        'author': {
            'id': post.author.id,
            'username': post.author.username
        },
        'category': {
            'id': post.category.id,
            'name': post.category.name
        } if post.category else None,
        'created_at': post.created_at.isoformat(),
        'published_at': post.published_at.isoformat() if post.published_at else None
    })

@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        print("=== CREATE POST FUNCTION CALLED ===")
        print("Request method:", request.method)
        print("Request headers:", dict(request.headers))
        
        user_id = int(get_jwt_identity())
        print("User ID from JWT:", user_id)
        
        data = request.get_json()
        print("Received JSON data:", data)
        print("Request data type:", type(data))
        
        # Validate required fields
        if not data.get('title') or not data.get('title').strip():
            return jsonify({'error': 'Title is required'}), 422
        
        content = data.get('content', '').strip()
        # Check for empty content or just empty HTML tags
        if not content or content in ['<p><br></p>', '<p></p>', '<br>', '']:
            return jsonify({'error': 'Content is required'}), 422
        
        slug = create_slug(data['title'])
        # Ensure unique slug
        counter = 1
        original_slug = slug
        while Post.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Handle category_id - convert empty string to None
        category_id = data.get('category_id')
        if category_id == '' or category_id == 'null':
            category_id = None
        elif category_id:
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
        
        return jsonify({'message': 'Post created successfully', 'post_id': post.id}), 201
        
    except Exception as e:
        print("Error creating post:", str(e))
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/posts/<int:post_id>', methods=['PUT'])
@jwt_required()
def update_post(post_id):
    user_id = int(get_jwt_identity())
    post = Post.query.get_or_404(post_id)
    
    # Check if user owns the post or is admin
    user = User.query.get(user_id)
    if post.author_id != user_id and user.role != 'admin':
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
    return jsonify({'message': 'Post updated successfully'})

@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@jwt_required()
def delete_post(post_id):
    user_id = int(get_jwt_identity())
    post = Post.query.get_or_404(post_id)
    
    # Check if user owns the post or is admin
    user = User.query.get(user_id)
    if post.author_id != user_id and user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post deleted successfully'})

@app.route('/api/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'slug': cat.slug,
        'description': cat.description
    } for cat in categories])

# Test endpoint to check JWT authentication
@app.route('/api/test-auth', methods=['GET'])
@jwt_required()
def test_auth():
    print("=== TEST AUTH ENDPOINT CALLED ===")
    user_id = int(get_jwt_identity())
    print("User ID from JWT:", user_id)
    return jsonify({'message': 'Authentication working', 'user_id': user_id})

@app.route('/api/categories', methods=['POST'])
@jwt_required()
def create_category():
    data = request.get_json()
    
    category = Category(
        name=data['name'],
        slug=create_slug(data['name']),
        description=data.get('description')
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({'message': 'Category created successfully', 'category_id': category.id}), 201

@app.route('/api/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    
    comment = Comment(
        post_id=data['post_id'],
        author_name=data['author_name'],
        author_email=data['author_email'],
        content=data['content']
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({'message': 'Comment submitted for approval'}), 201

@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    comments = Comment.query.filter_by(post_id=post_id, status='approved').order_by(Comment.created_at.desc()).all()
    return jsonify([{
        'id': comment.id,
        'author_name': comment.author_name,
        'content': comment.content,
        'created_at': comment.created_at.isoformat()
    } for comment in comments])

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add UUID to prevent filename conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'filename': filename, 'url': f'/api/uploads/{filename}'})
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
