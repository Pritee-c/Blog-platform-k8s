import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactQuill from 'react-quill';
import 'react-quill/dist/quill.snow.css';
import api from '../services/api';
import toast from 'react-hot-toast';
import { Save, Eye } from 'lucide-react';

const CreatePost = () => {
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    excerpt: '',
    category_id: '',
    status: 'draft',
    meta_title: '',
    meta_description: ''
  });
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingCategories, setIsLoadingCategories] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await api.get('/categories');
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
      toast.error('Error fetching categories');
    } finally {
      setIsLoadingCategories(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error('Title is required');
      return;
    }

    if (!formData.content.trim()) {
      toast.error('Content is required');
      return;
    }

    setIsLoading(true);

    try {
      const dataToSubmit = {
        ...formData,
        category_id: formData.category_id || null
      };

      await api.post('/posts', dataToSubmit);
      toast.success('Post created successfully!');
      navigate('/dashboard');
    } catch (error) {
      console.error('Error creating post:', error);
      toast.error(error.response?.data?.error || 'Error creating post');
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

  const handleContentChange = (content) => {
    setFormData({
      ...formData,
      content
    });
  };

  const quillModules = {
    toolbar: [
      [{ 'header': [1, 2, 3, false] }],
      ['bold', 'italic', 'underline', 'strike'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      ['blockquote', 'code-block'],
      ['link', 'image'],
      ['clean']
    ]
  };

  const quillFormats = [
    'header', 'bold', 'italic', 'underline', 'strike',
    'list', 'bullet', 'blockquote', 'code-block',
    'link', 'image'
  ];

  if (isLoadingCategories) {
    return (
      <div className="container text-center" style={{ padding: '2rem' }}>
        <div className="spinner"></div>
        Loading...
      </div>
    );
  }

  return (
    <div className="container" style={{ paddingTop: '2rem', maxWidth: '800px' }}>
      <div className="card">
        <div className="card-header">
          <h1 className="card-title">Create New Post</h1>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title" className="form-label">Title *</label>
            <input
              type="text"
              id="title"
              name="title"
              className="form-input"
              value={formData.title}
              onChange={handleChange}
              required
              placeholder="Enter post title"
            />
          </div>

          <div className="form-group">
            <label htmlFor="excerpt" className="form-label">Excerpt</label>
            <textarea
              id="excerpt"
              name="excerpt"
              className="form-input form-textarea"
              value={formData.excerpt}
              onChange={handleChange}
              placeholder="Brief description of the post"
              rows="3"
            />
          </div>

          <div className="form-group">
            <label htmlFor="category_id" className="form-label">Category</label>
            <select
              id="category_id"
              name="category_id"
              className="form-input form-select"
              value={formData.category_id}
              onChange={handleChange}
            >
              <option value="">Select a category</option>
              {categories.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Content *</label>
            <ReactQuill
              value={formData.content}
              onChange={handleContentChange}
              modules={quillModules}
              formats={quillFormats}
              placeholder="Write your post content here..."
            />
          </div>

          <div className="grid grid-2 gap-4">
            <div className="form-group">
              <label htmlFor="meta_title" className="form-label">SEO Title</label>
              <input
                type="text"
                id="meta_title"
                name="meta_title"
                className="form-input"
                value={formData.meta_title}
                onChange={handleChange}
                placeholder="SEO optimized title"
                maxLength="60"
              />
              <small style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                {formData.meta_title.length}/60 characters
              </small>
            </div>

            <div className="form-group">
              <label htmlFor="meta_description" className="form-label">SEO Description</label>
              <textarea
                id="meta_description"
                name="meta_description"
                className="form-input"
                value={formData.meta_description}
                onChange={handleChange}
                placeholder="SEO meta description"
                maxLength="160"
                rows="3"
              />
              <small style={{ color: '#6b7280', fontSize: '0.875rem' }}>
                {formData.meta_description.length}/160 characters
              </small>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="status" className="form-label">Status</label>
            <select
              id="status"
              name="status"
              className="form-input form-select"
              value={formData.status}
              onChange={handleChange}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>

          <div className="flex gap-4 justify-between">
            <button
              type="button"
              onClick={() => navigate('/dashboard')}
              className="btn btn-secondary"
            >
              Cancel
            </button>
            
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setFormData({ ...formData, status: 'draft' });
                  setTimeout(() => handleSubmit(new Event('submit')), 100);
                }}
                className="btn btn-secondary flex items-center gap-2"
                disabled={isLoading}
              >
                <Save size={16} />
                Save Draft
              </button>
              
              <button
                type="button"
                onClick={() => {
                  setFormData({ ...formData, status: 'published' });
                  setTimeout(() => handleSubmit(new Event('submit')), 100);
                }}
                className="btn btn-primary flex items-center gap-2"
                disabled={isLoading}
              >
                {isLoading && <span className="spinner"></span>}
                <Eye size={16} />
                Publish
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreatePost;