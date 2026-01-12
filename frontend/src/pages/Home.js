import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { Calendar, User, Eye, MessageCircle } from 'lucide-react';

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await api.get('/posts?status=published');
      setPosts(response.data.posts);
    } catch (error) {
      console.error('Error fetching posts:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container text-center" style={{ padding: '2rem' }}>
        <div className="spinner"></div>
        Loading posts...
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <div className="text-center mb-6">
        <h1 style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          Welcome to Our Blog
        </h1>
        <p style={{ fontSize: '1.25rem', color: '#6b7280' }}>
          Discover amazing content and join our community
        </p>
      </div>

      {posts.length === 0 ? (
        <div className="text-center">
          <h2>No posts available yet.</h2>
          <p>Check back later for new content!</p>
        </div>
      ) : (
        <div className="grid grid-2">
          {posts.map((post) => (
            <article key={post.id} className="card">
              {post.featured_image && (
                <img 
                  src={post.featured_image} 
                  alt={post.title}
                  style={{
                    width: '100%',
                    height: '200px',
                    objectFit: 'cover',
                    borderRadius: '0.5rem',
                    marginBottom: '1rem'
                  }}
                />
              )}
              
              <div className="card-header">
                <h2 className="card-title">
                  <Link 
                    to={`/post/${post.slug}`}
                    style={{ textDecoration: 'none', color: 'inherit' }}
                  >
                    {post.title}
                  </Link>
                </h2>
              </div>

              {post.excerpt && (
                <p style={{ 
                  marginBottom: '1rem', 
                  color: '#6b7280',
                  lineHeight: '1.6' 
                }}>
                  {post.excerpt}
                </p>
              )}

              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4" style={{ fontSize: '0.875rem', color: '#9ca3af' }}>
                  <div className="flex items-center gap-1">
                    <User size={16} />
                    {post.author.username}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar size={16} />
                    {new Date(post.published_at).toLocaleDateString()}
                  </div>
                  {post.category && (
                    <span className="badge badge-info">
                      {post.category.name}
                    </span>
                  )}
                </div>

                <Link 
                  to={`/post/${post.slug}`}
                  className="btn btn-primary"
                  style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
                >
                  <Eye size={16} style={{ marginRight: '0.5rem' }} />
                  Read More
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
};

export default Home;