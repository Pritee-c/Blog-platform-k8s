import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { Plus, Edit, Trash2, Eye, Calendar, User } from 'lucide-react';
import toast from 'react-hot-toast';

const Dashboard = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const { user } = useAuth();

  useEffect(() => {
    fetchPosts();
  }, [filter]);

  const fetchPosts = async () => {
    try {
      const response = await api.get('/posts', {
        params: { 
          status: filter === 'all' ? undefined : filter,
          per_page: 20 
        }
      });
      setPosts(response.data.posts);
    } catch (error) {
      console.error('Error fetching posts:', error);
      toast.error('Error fetching posts');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post?')) {
      return;
    }

    try {
      await api.delete(`/posts/${postId}`);
      setPosts(posts.filter(post => post.id !== postId));
      toast.success('Post deleted successfully');
    } catch (error) {
      console.error('Error deleting post:', error);
      toast.error('Error deleting post');
    }
  };

  const getStatusBadge = (status) => {
    const badgeClass = status === 'published' ? 'badge-success' : 'badge-warning';
    return <span className={`badge ${badgeClass}`}>{status}</span>;
  };

  if (loading) {
    return (
      <div className="container text-center" style={{ padding: '2rem' }}>
        <div className="spinner"></div>
        Loading dashboard...
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '2rem' }}>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            Dashboard
          </h1>
          <p style={{ color: '#6b7280' }}>
            Welcome back, {user?.username}! Manage your blog posts here.
          </p>
        </div>
        <Link to="/create-post" className="btn btn-primary flex items-center gap-2">
          <Plus size={18} />
          New Post
        </Link>
      </div>

      <div className="card">
        <div className="card-header">
          <div className="flex justify-between items-center">
            <h2 className="card-title">Your Posts</h2>
            <div className="flex gap-2">
              <button
                onClick={() => setFilter('all')}
                className={`btn ${filter === 'all' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                All
              </button>
              <button
                onClick={() => setFilter('published')}
                className={`btn ${filter === 'published' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                Published
              </button>
              <button
                onClick={() => setFilter('draft')}
                className={`btn ${filter === 'draft' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.875rem', padding: '0.5rem 1rem' }}
              >
                Drafts
              </button>
            </div>
          </div>
        </div>

        {posts.length === 0 ? (
          <div className="text-center" style={{ padding: '2rem' }}>
            <h3>No posts found</h3>
            <p style={{ color: '#6b7280', marginBottom: '1rem' }}>
              {filter === 'all' 
                ? "You haven't created any posts yet." 
                : `No ${filter} posts found.`}
            </p>
            <Link to="/create-post" className="btn btn-primary">
              <Plus size={16} style={{ marginRight: '0.5rem' }} />
              Create Your First Post
            </Link>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #e5e7eb' }}>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Title</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Status</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Category</th>
                  <th style={{ padding: '1rem', textAlign: 'left', fontWeight: '600' }}>Date</th>
                  <th style={{ padding: '1rem', textAlign: 'center', fontWeight: '600' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {posts.map((post) => (
                  <tr key={post.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '1rem' }}>
                      <div>
                        <h4 style={{ marginBottom: '0.25rem', fontWeight: '500' }}>
                          {post.title}
                        </h4>
                        {post.excerpt && (
                          <p style={{ 
                            fontSize: '0.875rem', 
                            color: '#6b7280',
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}>
                            {post.excerpt}
                          </p>
                        )}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      {getStatusBadge(post.status)}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                      {post.category?.name || 'Uncategorized'}
                    </td>
                    <td style={{ padding: '1rem', fontSize: '0.875rem', color: '#6b7280' }}>
                      <div className="flex items-center gap-1">
                        <Calendar size={14} />
                        {new Date(post.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td style={{ padding: '1rem' }}>
                      <div className="flex justify-center gap-2">
                        {post.status === 'published' && (
                          <Link
                            to={`/post/${post.slug}`}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.75rem', padding: '0.5rem' }}
                            title="View Post"
                          >
                            <Eye size={14} />
                          </Link>
                        )}
                        <Link
                          to={`/edit-post/${post.id}`}
                          className="btn btn-secondary"
                          style={{ fontSize: '0.75rem', padding: '0.5rem' }}
                          title="Edit Post"
                        >
                          <Edit size={14} />
                        </Link>
                        <button
                          onClick={() => handleDeletePost(post.id)}
                          className="btn btn-danger"
                          style={{ fontSize: '0.75rem', padding: '0.5rem' }}
                          title="Delete Post"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;