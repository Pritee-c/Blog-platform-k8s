import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { Calendar, User, ArrowLeft, MessageCircle, Send } from 'lucide-react';
import toast from 'react-hot-toast';

const PostDetail = () => {
  const { slug } = useParams();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [commentForm, setCommentForm] = useState({
    author_name: '',
    author_email: '',
    content: ''
  });
  const [submittingComment, setSubmittingComment] = useState(false);

  useEffect(() => {
    fetchPost();
  }, [slug]);

  const fetchPost = async () => {
    try {
      // Since we're using slug, we need to get all posts and find the one with matching slug
      // In a real app, you'd have a dedicated endpoint for this
      const response = await api.get('/posts?status=published');
      const foundPost = response.data.posts.find(p => p.slug === slug);
      
      if (foundPost) {
        setPost(foundPost);
        await fetchComments(foundPost.id);
      } else {
        toast.error('Post not found');
      }
    } catch (error) {
      console.error('Error fetching post:', error);
      toast.error('Error loading post');
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async (postId) => {
    try {
      const response = await api.get(`/posts/${postId}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!commentForm.author_name.trim() || !commentForm.author_email.trim() || !commentForm.content.trim()) {
      toast.error('All fields are required');
      return;
    }

    setSubmittingComment(true);

    try {
      await api.post('/comments', {
        post_id: post.id,
        ...commentForm
      });
      
      toast.success('Comment submitted for approval!');
      setCommentForm({
        author_name: '',
        author_email: '',
        content: ''
      });
      
      // In a real app, you might want to refresh comments if they're auto-approved
    } catch (error) {
      console.error('Error submitting comment:', error);
      toast.error('Error submitting comment');
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleCommentChange = (e) => {
    setCommentForm({
      ...commentForm,
      [e.target.name]: e.target.value
    });
  };

  if (loading) {
    return (
      <div className="container text-center" style={{ padding: '2rem' }}>
        <div className="spinner"></div>
        Loading post...
      </div>
    );
  }

  if (!post) {
    return (
      <div className="container text-center" style={{ padding: '2rem' }}>
        <h1>Post Not Found</h1>
        <p>The post you're looking for doesn't exist or has been removed.</p>
        <Link to="/" className="btn btn-primary">
          <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} />
          Back to Home
        </Link>
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '2rem', maxWidth: '800px' }}>
      <Link to="/" className="btn btn-secondary mb-4 flex items-center gap-2">
        <ArrowLeft size={16} />
        Back to Posts
      </Link>

      <article className="card">
        {post.featured_image && (
          <img 
            src={post.featured_image} 
            alt={post.title}
            style={{
              width: '100%',
              height: '300px',
              objectFit: 'cover',
              borderRadius: '0.5rem',
              marginBottom: '2rem'
            }}
          />
        )}

        <header style={{ marginBottom: '2rem' }}>
          <h1 style={{ 
            fontSize: '2.5rem', 
            fontWeight: 'bold', 
            marginBottom: '1rem',
            lineHeight: '1.2'
          }}>
            {post.title}
          </h1>
          
          <div className="flex items-center gap-4" style={{ 
            fontSize: '0.875rem', 
            color: '#6b7280',
            paddingBottom: '1rem',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <div className="flex items-center gap-1">
              <User size={16} />
              {post.author.username}
            </div>
            <div className="flex items-center gap-1">
              <Calendar size={16} />
              {new Date(post.published_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </div>
            {post.category && (
              <span className="badge badge-info">
                {post.category.name}
              </span>
            )}
          </div>
        </header>

        <div 
          style={{ 
            fontSize: '1.125rem',
            lineHeight: '1.8',
            color: '#374151'
          }}
          dangerouslySetInnerHTML={{ __html: post.content }}
        />
      </article>

      {/* Comments Section */}
      <div className="card mt-6">
        <div className="card-header">
          <h3 className="card-title flex items-center gap-2">
            <MessageCircle size={20} />
            Comments ({comments.length})
          </h3>
        </div>

        {comments.length > 0 && (
          <div style={{ marginBottom: '2rem' }}>
            {comments.map((comment) => (
              <div 
                key={comment.id} 
                style={{ 
                  padding: '1rem',
                  borderBottom: '1px solid #e5e7eb',
                  marginBottom: '1rem'
                }}
              >
                <div className="flex justify-between items-center mb-2">
                  <h4 style={{ fontWeight: '600', color: '#374151' }}>
                    {comment.author_name}
                  </h4>
                  <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                    {new Date(comment.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p style={{ lineHeight: '1.6', color: '#4b5563' }}>
                  {comment.content}
                </p>
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleCommentSubmit}>
          <h4 style={{ marginBottom: '1rem', fontWeight: '600' }}>
            Leave a Comment
          </h4>
          
          <div className="grid grid-2 gap-4">
            <div className="form-group">
              <label htmlFor="author_name" className="form-label">Name *</label>
              <input
                type="text"
                id="author_name"
                name="author_name"
                className="form-input"
                value={commentForm.author_name}
                onChange={handleCommentChange}
                required
                placeholder="Your name"
              />
            </div>

            <div className="form-group">
              <label htmlFor="author_email" className="form-label">Email *</label>
              <input
                type="email"
                id="author_email"
                name="author_email"
                className="form-input"
                value={commentForm.author_email}
                onChange={handleCommentChange}
                required
                placeholder="Your email (will not be published)"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="content" className="form-label">Comment *</label>
            <textarea
              id="content"
              name="content"
              className="form-input form-textarea"
              value={commentForm.content}
              onChange={handleCommentChange}
              required
              placeholder="Write your comment here..."
              rows="4"
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary flex items-center gap-2"
            disabled={submittingComment}
          >
            {submittingComment && <span className="spinner"></span>}
            <Send size={16} />
            Submit Comment
          </button>
          
          <p style={{ 
            fontSize: '0.875rem', 
            color: '#6b7280',
            marginTop: '0.5rem'
          }}>
            Your comment will be reviewed before being published.
          </p>
        </form>
      </div>
    </div>
  );
};

export default PostDetail;