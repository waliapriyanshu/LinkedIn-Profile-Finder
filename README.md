# 🔍 LinkedIn Profile Finder for Job Descriptions

## Overview

This tool was built for the **Synapse Annual AI Hackathon** challenge titled _“Sourcing Agent”_. It identifies the most relevant public LinkedIn profiles for a given job description using keyword extraction, Google search via SerpAPI, and AI-powered scoring using Gemini (Google GenAI).

## Challenge Description

Challenge link: [Sourcing Agent Challenge](https://www.notion.so/synapseint/Synapse-Annual-First-Ever-AI-Hackathon-Sourcing-Agent-Challenge-21f96e231c3a80fd997dcb60f517e760)

---

## 💡 Features

- Extracts job-specific keywords using NLP.
- Performs automated Google search using SerpAPI to find public LinkedIn profiles.
- Uses Gemini (Google GenAI) to contextually evaluate and score profile matches.
- Outputs top-ranked LinkedIn profiles and stores results in a local SQLite database.

---

## 🧰 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/linkedin-profile-finder.git
cd linkedin-profile-finder
```

### 2. Install Dependencies

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set API Keys

Create a `.env` file or set these environment variables:

```bash
export SERPAPI_API_KEY="your_serpapi_key"
export GOOGLE_API_KEY="your_google_genai_key"
```

### 4. Run the Script

```bash
python linkedin_profile_finder.py
```

> 💡 Ensure you have internet access. The tool uses APIs that require connectivity.

---

## 🛠 Tech Stack

- **Python**
- **SerpAPI** – Google search results
- **Google GenAI (Gemini)** – Profile scoring
- **SQLite** – Storing search results
- **fuzzywuzzy + Levenshtein** – Keyword-based matching
- **BeautifulSoup** – Snippet cleaning

---

## 📦 Files

- `linkedin_profile_finder.py` – Main script
- `requirements.txt` – Dependencies
- `README.md` – Project documentation

---

## 🚀 Future Improvements

- Advanced contextual matching using embeddings
- Resume matching and parsing integration
- Rate-limit mitigation strategies (API pool, caching)
- UI for recruiter input/output visualization
