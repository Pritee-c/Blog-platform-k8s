import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, User, Edit, Home } from 'lucide-react';

const Header = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header">
      <div className="container">
        <div className="header-content">
          <Link to="/" className="logo">
            Blog CMS
          </Link>
          
          <nav className="nav">
            <Link to="/" className="flex items-center gap-2">
              <Home size={18} />
              Home
            </Link>
            
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="flex items-center gap-2">
                  <Edit size={18} />
                  Dashboard
                </Link>
                <Link to="/create-post" className="btn btn-primary">
                  New Post
                </Link>
                <div className="flex items-center gap-2">
                  <User size={18} />
                  <span>Welcome, {user?.username}</span>
                </div>
                <button 
                  onClick={handleLogout}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary">
                  Login
                </Link>
                <Link to="/register" className="btn btn-primary">
                  Register
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;