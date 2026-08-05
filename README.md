<p align="center">
  <h1 align="center">HalalEdge — AI-Powered Halal Stock Screener</h1>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Vercel-Deployed-black?style=for-the-badge&logo=vercel" alt="Vercel">
  <img src="https://img.shields.io/badge/Render-Deployed-46E3B7?style=for-the-badge&logo=render" alt="Render">
</p>

<p align="center">
  An intelligent stock screening platform combining <strong>AI-driven price prediction</strong>, <strong>sentiment analysis</strong>, and <strong>Shariah compliance filtering</strong> for Muslim investors.
</p>

<p align="center">
  <img src="app_images/dashboard-overview.jpeg" alt="Dashboard overview" width="31%">
  <img src="app_images/screening-results.jpeg" alt="Screening results" width="31%">
  <img src="app_images/portfolio-view.jpeg" alt="Portfolio view" width="31%">
</p>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI-Powered Predictions** | Multi-model ensemble using LSTM, FinBERT, and XGBoost for accurate stock price forecasting |
| ☪️ **Shariah Compliance Screening** | Automated filtering based on Islamic finance principles — debt ratios, business activity, and revenue sources |
| 📊 **Interactive Stock Charts** | Real-time candlestick charts with technical indicators powered by Chart.js |
| 💼 **Portfolio Tracker** | Track holdings, monitor P&L, and view portfolio allocation breakdowns |
| 📰 **Real-time Sentiment Analysis** | NLP-driven news sentiment scoring using FinBERT transformer models |
| 🔐 **Secure JWT Authentication** | Industry-standard JSON Web Token auth with bcrypt password hashing |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5 · CSS3 · JavaScript (ES6+) · Chart.js |
| **Backend** | Python · FastAPI · SQLAlchemy · Uvicorn |
| **AI/ML** | scikit-learn · XGBoost · HuggingFace Transformers (FinBERT) |
| **Database** | PostgreSQL · Supabase |
| **Deployment** | Vercel (Frontend) · Render (Backend API) |
| **Auth** | JWT · bcrypt · python-jose |

---

## 🚀 Local Development Setup

### Prerequisites

- Python 3.12+
- Node.js (optional, for local static serving)
- PostgreSQL or a [Supabase](https://supabase.com) project

### 1. Clone the Repository

```bash
git clone https://github.com/MohammadMohid03/HalalEdge.git
cd HalalEdge
```

### 2. Set Up the Backend

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment Variables

Create `backend/.env` with the following:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
SECRET_KEY=your-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 4. Start the Backend Server

```bash
uvicorn backend.main:app --reload --port 8000
```

### 5. Serve the Frontend

Open `index.html` directly in your browser, or use a local server:

```bash
# Using Python
python -m http.server 5500

# Using VS Code Live Server extension (recommended)
```

Visit `http://localhost:5500` to view the app.

---

## ☁️ Deployment Guide

### Frontend → Vercel

1. Push the repo to GitHub
2. Import the project on [Vercel](https://vercel.com)
3. Vercel auto-detects `vercel.json` — no build step needed
4. Your frontend will be live at `https://halaledge.vercel.app`

### Backend → Render

1. Create a new **Web Service** on [Render](https://render.com)
2. Connect your GitHub repo
3. Render auto-detects `render.yaml` blueprint
4. Set environment variables (`DATABASE_URL`, `SECRET_KEY`) in the Render dashboard
5. Your API will be live at `https://halaledge-api.onrender.com`

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/auth/signup` | Register a new user | ❌ |
| `POST` | `/api/auth/login` | Login and receive JWT | ❌ |
| `GET` | `/api/auth/me` | Get current user profile | ✅ |
| `GET` | `/api/stocks/search?q={query}` | Search for stocks | ❌ |
| `GET` | `/api/stocks/{symbol}` | Get stock details + chart data | ❌ |
| `GET` | `/api/stocks/{symbol}/predict` | Get AI price prediction | ❌ |
| `GET` | `/api/portfolio` | Get user's portfolio | ✅ |
| `POST` | `/api/portfolio/add` | Add stock to portfolio | ✅ |
| `DELETE` | `/api/portfolio/{id}` | Remove stock from portfolio | ✅ |
| `GET` | `/api/watchlist` | Get user's watchlist | ✅ |
| `POST` | `/api/watchlist/add` | Add stock to watchlist | ✅ |

---

## 📁 Project Structure

```
HalalEdge/
├── index.html                 # Landing page
├── screener.html              # Stock screener
├── stock.html                 # Individual stock view
├── portfolio.html             # Portfolio tracker
├── login.html                 # Login page
├── signup.html                # Signup page
├── learn.html                 # Educational content
├── about.html                 # About page
├── css/
│   ├── style.css              # Global styles
│   ├── home.css               # Landing page styles
│   ├── screener.css           # Screener styles
│   ├── stock.css              # Stock page styles
│   ├── portfolio.css          # Portfolio styles
│   ├── auth.css               # Auth page styles
│   ├── learn.css              # Learn page styles
│   └── about.css              # About page styles
├── js/
│   ├── main.js                # Shared utilities + API config
│   ├── home.js                # Landing page logic
│   ├── screener.js            # Screener logic
│   ├── stock.js               # Stock page logic
│   ├── portfolio.js           # Portfolio logic
│   ├── auth.js                # Auth logic
│   └── learn.js               # Learn page logic
├── backend/
│   ├── main.py                # FastAPI app entry point
│   ├── config.py              # App configuration
│   ├── database.py            # Database connection
│   ├── requirements.txt       # Python dependencies
│   ├── models/                # SQLAlchemy models
│   ├── routers/               # API route handlers
│   │   ├── auth.py            # Auth endpoints
│   │   ├── stocks.py          # Stock endpoints
│   │   ├── portfolio.py       # Portfolio endpoints
│   │   ├── predictions.py     # AI prediction endpoints
│   │   └── watchlist.py       # Watchlist endpoints
│   ├── schemas/               # Pydantic schemas
│   └── services/              # Business logic
├── vercel.json                # Vercel deployment config
├── render.yaml                # Render deployment blueprint
├── Procfile                   # Process file for deployment
├── runtime.txt                # Python runtime version
└── .gitignore                 # Git ignore rules
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Built with ❤️ by <a href="https://github.com/MohammadMohid03">Mohammad Mohid</a>
</p>
