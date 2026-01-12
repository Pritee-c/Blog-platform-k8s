# Blog/CMS Platform

A 3-tier Blog/Content Management System built with React, Flask, and MySQL.

## Architecture

```
Frontend (React)  ←→  Backend (Flask API)  ←→  Database (MySQL)
     :3000              :5000                   :3306
```

## Features

- User Authentication (JWT)
- Role-based access (Admin/Author)
- CRUD operations for blog posts
- Category management
- Comment system
- Rich text editor
- Image upload
- SEO-friendly URLs
- Draft/Published status

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Database Setup
```bash
mysql -u root -p
CREATE DATABASE blog_cms;
```

## API Endpoints

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/posts` - Get all posts
- `POST /api/posts` - Create new post
- `GET /api/posts/:id` - Get single post
- `PUT /api/posts/:id` - Update post
- `DELETE /api/posts/:id` - Delete post
- `GET /api/categories` - Get categories
- `POST /api/comments` - Add comment

## Directory Structure

```
├── backend/
│   ├── app.py
│   ├── models/
│   ├── routes/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
└── database/
    └── schema.sql
```