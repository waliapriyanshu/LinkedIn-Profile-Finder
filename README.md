# 🔍 LinkedIn Profile Finder for Job Descriptions

## Overview

This tool was built for the **Synapse Annual AI Hackathon** challenge titled _“Sourcing Agent”_. It identifies the most relevant public LinkedIn profiles for a given job description using keyword extraction, Google search via SerpAPI, and AI-powered scoring using Gemini (Google GenAI).

## Challenge Description

Challenge link: [Sourcing Agent Challenge](https://www.notion.so/synapseint/Synapse-Annual-First-Ever-AI-Hackathon-Sourcing-Agent-Challenge-21f96e231c3a80fd997dcb60f517e760)

---

## 💡 Features

- Extracts job-specific keywords using basic NLP logic.
- Performs automated Google search using SerpAPI to find public LinkedIn profiles.
- Uses Gemini (Google GenAI) to contextually evaluate and score profile matches.
- Stores results in a local SQLite database.

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
- **SerpAPI** – For Google search results
- **Google GenAI (Gemini)** – For profile scoring
- **SQLite** – For storing results
- **Requests** – For HTTP requests
- **concurrent.futures** – For parallel processing

---

## 📦 Files

- `linkedin_profile_finder.py` – Main script
- `requirements.txt` – Dependencies
- `README.md` – Project documentation

---

## 🚀 Future Improvements

- Improve contextual matching using embeddings
- Integrate resume parsing and ATS scoring
- Add caching and rate-limit handling
- Build a UI for recruiter-friendly interaction
