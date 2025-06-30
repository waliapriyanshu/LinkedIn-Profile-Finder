# LinkedIn Profile Finder for Job Descriptions

## 🔍 Overview

This tool was built as part of the **Synapse Annual AI Hackathon** challenge, "Sourcing Agent". The goal is to find the best-matching LinkedIn profiles for a given job description using AI.

It reads a job description, extracts relevant keywords, performs Google searches to identify potential LinkedIn profiles, and filters them based on match score.

## 🧠 Challenge Description

Challenge link: [Sourcing Agent Challenge](https://www.notion.so/synapseint/Synapse-Annual-First-Ever-AI-Hackathon-Sourcing-Agent-Challenge-21f96e231c3a80fd997dcb60f517e760)

## 💡 Features

- Extracts job-specific keywords using NLP.
- Uses Google Search API to find LinkedIn profiles.
- Calculates similarity scores based on profile descriptions.
- Outputs the top-ranked LinkedIn profiles.

## 🧰 Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/linkedin-profile-finder.git
   cd linkedin-profile-finder
   ```

2. **Install Dependencies**
   Create a virtual environment and install required libraries:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

3. **Run the Script**
   ```bash
   python linkedin_profile_finder.py
   ```

> Make sure you have internet access as it uses Google Search.

## 📦 Files

- `linkedin_profile_finder.py`: Main script
- `requirements.txt`: Python dependencies
- `README.md`: This file

## 🛠 Tech Stack

- Python
- BeautifulSoup
- Requests
- FuzzyWuzzy
- Scikit-learn
- Google Search API

## 🚀 Future Improvements

- Add OpenAI/GPT-powered job-resume matching.
- Integrate with LinkedIn API for direct profile scraping.
- Improve keyword extraction using spaCy or LLMs.
