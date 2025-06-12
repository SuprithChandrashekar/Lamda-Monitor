# Lambda Monitor

A real-time monitoring system for tracking and analyzing social media posts from political figures and industry leaders.

## Features

- Monitors social media posts from political figures and industry leaders (Twitter, Truth Social)
- AI-powered analysis of post content and market impact
- Real-time notifications for high-priority posts
- Customizable watchlists and alerts
- Historical post search and analysis
- Interactive web dashboard built with FastAPI

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Lamda_Monitor.git
cd Lamda_Monitor
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Linux/macOS
source venv/bin/activate
# On Windows
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
- Copy `.env.example` to `.env`
- Fill in your API keys and other configuration

5. Initialize the database:
```bash
python -m src.database.init_db
```

6. Start the application:
```bash
python -m src.main
```

## Project Structure

```
├── src/               # Source code
│   ├── analyzers/     # AI analysis modules
│   ├── database/      # Database models and connection
│   ├── fetchers/      # Social media API integrations
│   ├── frontend/      # Web interface
│   ├── notifiers/     # Notification system
│   ├── config.py      # Configuration
│   └── main.py        # FastAPI application
├── start.py           # Convenience startup script
└── tests/             # Test suite
```

## API Documentation

Once the application is running, visit `http://localhost:8000/docs` for the interactive API documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details
