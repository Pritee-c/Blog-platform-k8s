import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import toast from 'react-hot-toast';
import { LogIn } from 'lucide-react';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const result = await login(formData.email, formData.password);
      
      if (result.success) {
        toast.success('Login successful!');
        navigate('/dashboard');
      } else {
        toast.error(result.error);
      }
    } catch (error) {
      toast.error('An error occurred during login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="container" style={{ paddingTop: '2rem', maxWidth: '400px' }}>
      <div className="card">
        <div className="card-header text-center">
          <LogIn size={48} style={{ margin: '0 auto 1rem', color: '#3182ce' }} />
          <h1 className="card-title">Login to Your Account</h1>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              className="form-input"
              value={formData.email}
              onChange={handleChange}
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              className="form-input"
              value={formData.password}
              onChange={handleChange}
              required
              placeholder="Enter your password"
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%' }}
            disabled={isLoading}
          >
            {isLoading && <span className="spinner"></span>}
            Sign In
          </button>
        </form>

        <div className="text-center mt-4">
          <p style={{ color: '#6b7280' }}>
            Don't have an account?{' '}
            <Link to="/register" style={{ color: '#3182ce', textDecoration: 'none' }}>
              Sign up here
            </Link>
          </p>
        </div>

        <div className="mt-4" style={{ 
          padding: '1rem', 
          backgroundColor: '#f0f9ff', 
          borderRadius: '0.5rem',
          border: '1px solid #bfdbfe'
        }}>
          <p style={{ fontSize: '0.875rem', color: '#1e40af', marginBottom: '0.5rem' }}>
            <strong>Demo Accounts:</strong>
          </p>
          <p style={{ fontSize: '0.875rem', color: '#1e40af', marginBottom: '0.25rem' }}>
            Admin: admin@blog.com / password123
          </p>
          <p style={{ fontSize: '0.875rem', color: '#1e40af' }}>
            Author: author@blog.com / password123
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;