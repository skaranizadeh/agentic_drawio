# Agentic Flowchart Generator

An AI-powered web application that automatically generates flowcharts from natural language instructions using OpenAI and Draw.io.

## Features

- **AI-Powered Planning** - Converts natural language instructions into structured flowchart plans
- **Automatic Diagram Generation** - Transforms plans into Draw.io XML format
- **Live Preview & Editing** - Real-time diagram preview with Draw.io embedded editor
- **Export Functionality** - Download diagrams as .drawio files
- **XML Editing** - View and manually edit generated XML

## Prerequisites

- Python 3.7+
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd agentic-flowchart
```

2. Install dependencies:
```bash
pip install flask openai python-dotenv
```

3. Create a `.env` file in the root directory:
```
OPENAI_API_KEY=your_openai_api_key_here
```
for local server uncomment these two lines: 
          # from dotenv import load_dotenv

          # load_dotenv()

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:3001
```

3. Follow the workflow:
   - Enter flowchart instructions (e.g., "User login flow with password reset")
   - Review and edit the generated plan
   - Click "Generate Diagram" to create the flowchart
   - Download or further edit as needed

## Project Structure

```
├── app.py              # Flask backend with OpenAI integration
├── templates/
│   └── index.html      # Main UI with Draw.io integration
├── .env                # Environment variables (create this)
└── README.md           # This file
```

## How It Works

1. **Natural Language → Plan**: Uses OpenAI GPT-4o-mini to convert instructions into structured nodes and edges
2. **Plan → XML**: Transforms the plan into Draw.io-compatible XML format
3. **XML → Visual**: Renders the diagram using embedded Draw.io editor
4. **Interactive Editing**: Allows real-time modifications and exports

## Technologies Used

- **Backend**: Flask, OpenAI API
- **Frontend**: HTML5, JavaScript, Draw.io
- **AI Model**: GPT-4o-mini
