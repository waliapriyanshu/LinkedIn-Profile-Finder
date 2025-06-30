"""
LinkedIn Sourcing Agent
A scalable AI-powered tool for sourcing, scoring, and reaching out to candidates
"""

import os
import json
import time
import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from serpapi import GoogleSearch
from google import genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERP_API_KEY = os.getenv("SERP_API_KEY", "44c44e29e5b90a3b71e18a6ce6d9762f3808103f9d9cc843451d4b407f21a7d6")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")

# Initialize Gemini client for message generation only
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY != "your-gemini-api-key-here" else None

# Elite schools and top companies for scoring
ELITE_SCHOOLS = {
    "mit", "stanford", "harvard", "yale", "princeton", "columbia", 
    "berkeley", "caltech", "carnegie mellon", "cornell", "upenn",
    "oxford", "cambridge", "eth zurich", "imperial college", "georgia tech",
    "cmu", "university of california", "uc berkeley", "uc san diego"
}

TOP_TECH_COMPANIES = {
    "google", "facebook", "meta", "amazon", "apple", "microsoft", 
    "netflix", "uber", "airbnb", "stripe", "openai", "anthropic",
    "tesla", "spacex", "nvidia", "salesforce", "databricks", "palantir",
    "github", "gitlab", "atlassian", "slack", "zoom", "dropbox"
}

@dataclass
class Candidate:
    """Data class for candidate information"""
    name: str
    linkedin_url: str
    headline: str = ""
    location: str = ""
    company: str = ""
    summary: str = ""

@dataclass
class ScoredCandidate:
    """Data class for scored candidate"""
    name: str
    linkedin_url: str
    fit_score: float
    score_breakdown: Dict[str, float]
    
@dataclass
class CandidateWithMessage:
    """Data class for candidate with outreach message"""
    candidate: str
    message: str

class LinkedInSourcingAgent:
    """Main agent class for LinkedIn sourcing operations"""
    
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for storing candidates"""
        self.conn = sqlite3.connect("candidates.db")
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                name TEXT,
                linkedin_url TEXT UNIQUE,
                fit_score REAL,
                score_breakdown TEXT,
                outreach_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()
        
    def run_pipeline(self):
        """Main pipeline that asks for job description and runs the full process"""
        print("=== LinkedIn Sourcing Agent ===")
        print("\nThis agent will:")
        print("1. Find LinkedIn profiles based on your job description")
        print("2. Score candidates using our fit rubric (1-10)")
        print("3. Generate personalized outreach messages")
        
        # Get job description from user
        print("\n" + "="*50)
        print("STEP 1: JOB DESCRIPTION INPUT")
        print("="*50)
        
        print("\nPlease enter the job description (press Enter twice when finished):")
        print("📝 Tip: You can paste long job descriptions - there's no character limit!")
        print("-" * 60)
        
        job_description_lines = []
        empty_line_count = 0
        
        while True:
            try:
                line = input()
                if line.strip() == "":
                    empty_line_count += 1
                    if empty_line_count >= 2:  # Two consecutive empty lines = done
                        break
                    job_description_lines.append(line)
                else:
                    empty_line_count = 0
                    job_description_lines.append(line)
            except EOFError:
                break
        
        job_description = "\n".join(job_description_lines).strip()
        
        if not job_description:
            print("❌ No job description provided. Exiting...")
            return
            
        print(f"\n✅ Job description received ({len(job_description)} characters)")
        
        # Show preview if it's long
        if len(job_description) > 200:
            print(f"📄 Preview (first 200 chars): {job_description[:200]}...")
        else:
            print(f"📄 Full description: {job_description}")
        
        # Generate unique job ID
        job_id = f"job_{int(time.time())}"
        
        # Step 1: Find LinkedIn Profiles
        print("\n" + "="*50)
        print("STEP 2: FINDING LINKEDIN PROFILES")
        print("="*50)
        
        candidates = self.search_linkedin(job_description)
        print(f"✅ Found {len(candidates)} candidate profiles")
        
        if not candidates:
            print("❌ No candidates found. Please try a different job description.")
            return
            
        # Step 2: Score Candidates
        print("\n" + "="*50)
        print("STEP 3: SCORING CANDIDATES")
        print("="*50)
        
        scored_candidates = self.score_candidates(candidates, job_description)
        
        print(f"✅ Scored {len(scored_candidates)} candidates")
        print("\n📊 Top 10 Candidates by Fit Score:")
        print("-" * 60)
        
        for i, candidate in enumerate(scored_candidates[:10], 1):
            print(f"{i:2d}. {candidate['name']:<25} | Score: {candidate['score']}/10")
        
        # Show detailed breakdown for top 3
        print(f"\n🔍 Detailed Score Breakdown (Top 3):")
        print("-" * 80)
        
        for i, candidate in enumerate(scored_candidates[:3], 1):
            print(f"\n{i}. {candidate['name']} - Overall Score: {candidate['score']}/10")
            breakdown = candidate['breakdown']
            print(f"   Education:    {breakdown['education']:.1f}/10  (20% weight)")
            print(f"   Trajectory:   {breakdown['trajectory']:.1f}/10  (20% weight)")
            print(f"   Company:      {breakdown['company']:.1f}/10  (15% weight)")
            print(f"   Experience:   {breakdown['experience']:.1f}/10  (25% weight)")
            print(f"   Location:     {breakdown['location']:.1f}/10  (10% weight)")
            print(f"   Tenure:       {breakdown['tenure']:.1f}/10  (10% weight)")
        
        # Step 3: Generate Outreach
        print("\n" + "="*50)
        print("STEP 4: GENERATING OUTREACH MESSAGES")
        print("="*50)
        
        # Ask user how many messages to generate
        while True:
            try:
                num_messages = input(f"\nHow many outreach messages to generate? (1-{len(scored_candidates)}): ")
                num_messages = int(num_messages)
                if 1 <= num_messages <= len(scored_candidates):
                    break
                else:
                    print(f"Please enter a number between 1 and {len(scored_candidates)}")
            except ValueError:
                print("Please enter a valid number")
        
        top_candidates = scored_candidates[:num_messages]
        messages = self.generate_outreach(top_candidates, job_description)
        
        print(f"✅ Generated {len(messages)} personalized messages")
        
        # Display messages
        print(f"\n📝 Generated Outreach Messages:")
        print("=" * 80)
        
        for i, (candidate, message_data) in enumerate(zip(top_candidates, messages), 1):
            print(f"\n{i}. MESSAGE FOR: {candidate['name']} (Score: {candidate['score']}/10)")
            print("-" * 60)
            print(message_data['message'])
            print("-" * 60)
        
        # Save results
        self.save_results(job_id, top_candidates, messages)
        
        # Final summary
        print(f"\n" + "="*50)
        print("PIPELINE COMPLETE!")
        print("="*50)
        print(f"📊 Summary:")
        print(f"   • Job ID: {job_id}")
        print(f"   • Candidates found: {len(candidates)}")
        print(f"   • Candidates scored: {len(scored_candidates)}")
        print(f"   • Messages generated: {len(messages)}")
        print(f"   • Results saved to database")
        
        # Ask if user wants to see the JSON output
        show_json = input(f"\nWould you like to see the JSON output? (y/n): ").lower().strip()
        if show_json in ['y', 'yes']:
            self.display_json_output(job_id, len(candidates), top_candidates, messages)
    
    def display_json_output(self, job_id: str, total_found: int, candidates: List[Dict], messages: List[Dict]):
        """Display the results in JSON format"""
        print(f"\n📄 JSON OUTPUT:")
        print("=" * 50)
        
        output = {
            "job_id": job_id,
            "candidates_found": total_found,
            "top_candidates": []
        }
        
        for i, candidate in enumerate(candidates):
            output["top_candidates"].append({
                "name": candidate["name"],
                "linkedin_url": candidate["linkedin_url"],
                "fit_score": candidate["score"],
                "score_breakdown": candidate["breakdown"],
                "outreach_message": messages[i]["message"] if i < len(messages) else ""
            })
        
        print(json.dumps(output, indent=2))
        
    def search_linkedin(self, job_description: str) -> List[Dict]:
        """
        Search for LinkedIn profiles based on job description
        Returns: [{"name": "John Doe", "linkedin_url": "...", "headline": "..."}]
        """
        logger.info("Searching LinkedIn for candidates...")
        
        # Extract search terms from job description
        search_terms = self._extract_search_terms(job_description)
        queries = self._build_search_queries(search_terms)
        
        candidates = []
        seen_urls = set()
        
        print(f"🔍 Searching with {len(queries)} different query strategies...")
        
        for i, query in enumerate(queries[:3], 1):  # Limit queries to conserve API calls
            try:
                print(f"   Query {i}: {query}")
                
                # Search using SerpAPI
                params = {
                    "api_key": SERP_API_KEY,
                    "engine": "google",
                    "q": query,
                    "num": 15
                }
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                if "organic_results" in results:
                    for result in results["organic_results"]:
                        link = result.get("link", "")
                        if "linkedin.com/in/" in link and link not in seen_urls:
                            seen_urls.add(link)
                            candidate = self._parse_search_result(result)
                            if candidate:
                                candidates.append(candidate)
                                
            except Exception as e:
                logger.error(f"Search error for query {i}: {e}")
                
        logger.info(f"Found {len(candidates)} candidates")
        return candidates
    
    def score_candidates(self, candidates: List[Dict], job_description: str) -> List[Dict]:
        """
        Score candidates based on fit score rubric
        Returns: [{"name": "...", "score": 8.5, "breakdown": {...}}]
        """
        logger.info(f"Scoring {len(candidates)} candidates...")
        
        scored_candidates = []
        job_info = self._extract_job_info(job_description)
        
        print("📊 Applying fit score rubric...")
        
        for candidate in candidates:
            # Calculate individual scores based on updated rubric
            education_score = self._score_education(candidate)
            trajectory_score = self._score_trajectory(candidate)
            company_score = self._score_company(candidate)
            experience_score = self._score_experience_match(candidate, job_description)
            location_score = self._score_location(candidate, job_info)
            tenure_score = self._score_tenure(candidate)
            
            # Calculate weighted average based on new rubric
            breakdown = {
                "education": education_score,
                "trajectory": trajectory_score,
                "company": company_score,
                "experience": experience_score,
                "location": location_score,
                "tenure": tenure_score
            }
            
            # Weights as specified in new rubric
            weights = {
                "education": 0.20,      # 20%
                "trajectory": 0.20,     # 20%
                "company": 0.15,        # 15%
                "experience": 0.25,     # 25%
                "location": 0.10,       # 10%
                "tenure": 0.10          # 10%
            }
            
            fit_score = sum(breakdown[key] * weights[key] for key in weights)
            
            scored_candidates.append({
                "name": candidate["name"],
                "linkedin_url": candidate["linkedin_url"],
                "score": round(fit_score, 1),
                "breakdown": breakdown
            })
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Scored {len(scored_candidates)} candidates")
        return scored_candidates
    
    def generate_outreach(self, scored_candidates: List[Dict], job_description: str) -> List[Dict]:
        """
        Generate personalized outreach messages for top candidates
        Returns: [{"candidate": "...", "message": "Hi John, I noticed..."}]
        """
        logger.info(f"Generating outreach messages for {len(scored_candidates)} candidates...")
        
        messages = []
        
        print("✍️  Generating personalized messages...")
        
        for i, candidate in enumerate(scored_candidates, 1):
            print(f"   Message {i}/{len(scored_candidates)}: {candidate['name']}")
            
            if gemini_client:
                # Use Gemini for personalized messages
                message = self._generate_ai_message(candidate, job_description)
            else:
                # Fallback to template
                message = self._generate_template_message(candidate, job_description)
                
            messages.append({
                "candidate": candidate["name"],
                "message": message
            })
        
        logger.info(f"Generated {len(messages)} messages")
        return messages
    
    # Private methods for search
    def _extract_search_terms(self, job_description: str) -> Dict:
        """Extract key search terms from job description"""
        text_lower = job_description.lower()
        
        terms = {
            "title": "",
            "skills": [],
            "location": "",
            "seniority": ""
        }
        
        # Extract job title/role
        if any(term in text_lower for term in ["machine learning", "ml engineer", "ai engineer"]):
            terms["title"] = "machine learning engineer"
        elif any(term in text_lower for term in ["data scientist", "data science"]):
            terms["title"] = "data scientist"
        elif any(term in text_lower for term in ["backend engineer", "backend developer"]):
            terms["title"] = "backend engineer"
        elif any(term in text_lower for term in ["frontend engineer", "frontend developer"]):
            terms["title"] = "frontend engineer"
        elif any(term in text_lower for term in ["full stack", "fullstack"]):
            terms["title"] = "full stack engineer"
        elif any(term in text_lower for term in ["devops", "platform engineer"]):
            terms["title"] = "devops engineer"
        elif any(term in text_lower for term in ["product manager"]):
            terms["title"] = "product manager"
        else:
            terms["title"] = "software engineer"
        
        # Extract seniority
        if any(term in text_lower for term in ["senior", "sr.", "lead", "principal", "staff"]):
            terms["seniority"] = "senior"
        elif any(term in text_lower for term in ["junior", "entry", "new grad"]):
            terms["seniority"] = "junior"
        
        # Extract skills
        skill_keywords = [
            "python", "java", "javascript", "typescript", "go", "rust", "c++",
            "react", "node.js", "django", "flask", "spring", "aws", "gcp", "azure",
            "kubernetes", "docker", "tensorflow", "pytorch", "ml", "ai", "nlp",
            "sql", "postgresql", "mongodb", "redis", "elasticsearch"
        ]
        
        for skill in skill_keywords:
            if skill in text_lower:
                terms["skills"].append(skill)
                
        # Extract location
        locations = [
            "san francisco", "mountain view", "palo alto", "san jose", "berkeley",
            "new york", "seattle", "austin", "boston", "chicago", "remote"
        ]
        
        for location in locations:
            if location in text_lower:
                terms["location"] = location
                break
            
        return terms
    
    def _build_search_queries(self, terms: Dict) -> List[str]:
        """Build LinkedIn search queries"""
        queries = []
        title = terms["title"]
        
        # Query 1: Title + Location
        if terms["location"]:
            queries.append(f'site:linkedin.com/in "{title}" "{terms["location"]}"')
        
        # Query 2: Title + Seniority
        if terms["seniority"]:
            queries.append(f'site:linkedin.com/in "{terms["seniority"]} {title}"')
        
        # Query 3: Title + Top Skills
        if terms["skills"]:
            top_skills = terms["skills"][:2]
            skills_str = " ".join([f'"{skill}"' for skill in top_skills])
            queries.append(f'site:linkedin.com/in "{title}" {skills_str}')
            
        # Fallback query
        if not queries:
            queries.append(f'site:linkedin.com/in "{title}"')
            
        return queries
    
    def _parse_search_result(self, result: Dict) -> Optional[Dict]:
        """Parse SerpAPI result into candidate format"""
        try:
            url = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            # Extract name from title
            name = "Unknown"
            headline = ""
            
            # Try different patterns for name extraction
            if " - " in title and "LinkedIn" in title:
                # Pattern: "Name - Title | LinkedIn"
                parts = title.split(" - ")
                name = parts[0].strip()
                if len(parts) > 1:
                    headline = parts[1].split("| LinkedIn")[0].strip()
            elif " | LinkedIn" in title:
                # Pattern: "Name | LinkedIn"
                name = title.split(" | LinkedIn")[0].strip()
            elif "LinkedIn" in title:
                # Remove LinkedIn and clean
                name = title.replace("LinkedIn", "").replace("|", "").strip()
            
            # If name is still Unknown or empty, extract from URL
            if name in ["Unknown", "", "View profile", "LinkedIn"]:
                name = self._extract_name_from_url(url)
            
            # Extract location
            location = ""
            if "Location:" in snippet:
                location_part = snippet.split("Location:")[1].split(".")[0].split("•")[0].strip()
                location = location_part
            elif "Based in" in snippet:
                location_part = snippet.split("Based in")[1].split(".")[0].split("•")[0].strip()
                location = location_part
            
            # Extract company
            company = ""
            if " at " in snippet:
                at_split = snippet.split(" at ")
                if len(at_split) > 1:
                    company = at_split[1].split(".")[0].split("•")[0].strip()[:50]
            
            # If no headline from title, use snippet
            if not headline and snippet:
                headline = snippet.split(".")[0][:100]
            
            return {
                "name": name,
                "linkedin_url": url,
                "headline": headline,
                "location": location,
                "company": company,
                "summary": snippet
            }
            
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return None
    
    def _extract_name_from_url(self, url: str) -> str:
        """Extract name from LinkedIn URL username"""
        try:
            # Extract username from URL
            if "linkedin.com/in/" in url:
                username = url.split("linkedin.com/in/")[-1].strip("/").split("?")[0]
                
                # Remove common suffixes
                username = username.split("-")[0] if username.count("-") > 2 else username
                
                # Remove numbers at the end
                clean_name = ""
                for char in username:
                    if char.isalpha() or char in ["-", "_"]:
                        clean_name += char
                    elif char.isdigit() and len(clean_name) > 3:
                        break
                    else:
                        clean_name += char
                
                if clean_name:
                    # Single word username - capitalize
                    if "-" not in clean_name and "_" not in clean_name:
                        return clean_name.capitalize()
                    elif "-" in clean_name and not clean_name[-1].isdigit():
                        # Hyphenated name like first-last
                        parts = clean_name.split("-")
                        return " ".join(part.capitalize() for part in parts if not part.isdigit())
                    else:
                        # Complex username - try to extract readable part
                        if clean_name.islower():
                            return clean_name.capitalize()
                        else:
                            # Handle camelCase like alexLevin
                            result = ""
                            for i, char in enumerate(clean_name):
                                if i > 0 and char.isupper() and clean_name[i-1].islower():
                                    result += " "
                                result += char
                            return result.title()
                            
            return "Profile User"
            
        except Exception as e:
            logger.error(f"Error extracting name from URL: {e}")
            return "Profile User"
    
    # Updated scoring methods based on new rubric
    def _score_education(self, candidate: Dict) -> float:
        """Score education (20% weight) - Updated rubric"""
        text = f"{candidate.get('headline', '')} {candidate.get('summary', '')}".lower()
        
        # Elite schools (MIT, Stanford, etc.): 9-10
        for school in ELITE_SCHOOLS:
            if school in text:
                return 9.5
        
        # Strong schools: 7-8
        strong_indicators = ["university", "college", "institute of technology", "phd", "doctorate", "master"]
        if any(indicator in text for indicator in strong_indicators):
            if any(deg in text for deg in ["phd", "ph.d", "doctorate"]):
                return 8.5
            elif any(deg in text for deg in ["master", "mba", "m.s.", "ms"]):
                return 7.5
            elif any(deg in text for deg in ["bachelor", "b.s.", "bs", "ba"]):
                return 7.0
            else:
                return 7.0
        
        # Standard universities: 5-6
        return 5.5
    
    def _score_trajectory(self, candidate: Dict) -> float:
        """Score career trajectory (20% weight) - Updated rubric"""
        headline = candidate.get("headline", "").lower()
        summary = candidate.get("summary", "").lower()
        text = f"{headline} {summary}"
        
        # Clear progression: 8-10
        senior_titles = ["principal", "staff", "lead", "senior", "director", "head", "vp", "cto", "chief"]
        mid_titles = ["mid", "ii", "iii", "intermediate"]
        junior_titles = ["junior", "entry", "intern", "associate", "new grad"]
        
        if any(title in text for title in senior_titles):
            return 8.5  # Steady growth to senior level
        elif any(title in text for title in mid_titles):
            return 7.0  # Some progression
        elif any(title in text for title in junior_titles):
            return 4.0  # Limited progression
        
        # Default for unclear trajectory
        return 6.0
    
    def _score_company(self, candidate: Dict) -> float:
        """Score company relevance (15% weight) - Updated rubric"""
        company = candidate.get("company", "").lower()
        headline = candidate.get("headline", "").lower()
        text = f"{company} {headline}"
        
        # Top tech companies: 9-10
        for tech_co in TOP_TECH_COMPANIES:
            if tech_co in text:
                return 9.5
        
        # Relevant industry: 7-8
        relevant_indicators = [
            "tech", "software", "ai", "ml", "fintech", "startup", "saas",
            "cloud", "data", "analytics", "platform", "engineering"
        ]
        if any(indicator in text for indicator in relevant_indicators):
            return 7.5
        
        # Any experience: 5-6
        return 5.5
    
    def _score_experience_match(self, candidate: Dict, job_description: str) -> float:
        """Score experience match (25% weight) - Updated rubric"""
        text = f"{candidate.get('headline', '')} {candidate.get('summary', '')}".lower()
        job_text = job_description.lower()
        
        # Extract key skills from job description
        job_skills = []
        skill_keywords = [
            "python", "java", "javascript", "typescript", "go", "rust", "c++",
            "react", "node.js", "django", "flask", "spring", "aws", "gcp", "azure",
            "kubernetes", "docker", "tensorflow", "pytorch", "ml", "ai", "nlp",
            "machine learning", "deep learning", "sql", "postgresql", "mongodb"
        ]
        
        for skill in skill_keywords:
            if skill in job_text:
                job_skills.append(skill)
        
        # Count skill matches
        matches = sum(1 for skill in job_skills if skill in text)
        total_skills = len(job_skills) if job_skills else 1
        match_ratio = matches / total_skills
        
        # Perfect skill match: 9-10
        if match_ratio >= 0.8:
            return 9.5
        # Strong overlap: 7-8
        elif match_ratio >= 0.5:
            return 7.5
        # Some relevant skills: 5-6
        elif match_ratio >= 0.2:
            return 5.5
        else:
            return 4.0
    
    def _score_location(self, candidate: Dict, job_info: Dict) -> float:
        """Score location match (10% weight) - Updated rubric"""
        candidate_location = candidate.get("location", "").lower()
        job_location = job_info.get("location", "").lower()
        
        # Exact city: 10
        if job_location and job_location in candidate_location:
            return 10.0
        
        # Same metro area mapping
        metro_areas = {
            "san francisco": ["sf", "san francisco", "bay area", "palo alto", "mountain view", "san jose"],
            "new york": ["nyc", "new york", "manhattan", "brooklyn"],
            "seattle": ["seattle", "bellevue", "redmond"],
            "boston": ["boston", "cambridge"],
            "los angeles": ["la", "los angeles", "santa monica"]
        }
        
        # Same metro: 8
        for metro, cities in metro_areas.items():
            if any(city in job_location for city in cities) and any(city in candidate_location for city in cities):
                return 8.0
        
        # Remote-friendly: 6
        if "remote" in candidate_location or "remote" in job_location:
            return 6.0
        
        return 5.0
    
    def _score_tenure(self, candidate: Dict) -> float:
        """Score tenure (10% weight) - Updated rubric"""
        summary = candidate.get("summary", "").lower()
        headline = candidate.get("headline", "").lower()
        text = f"{summary} {headline}"
        
        # Look for tenure indicators
        tenure_patterns = [
            "2 years", "3 years", "two years", "three years",
            "2-3 years", "1-2 years", "4 years", "5 years"
        ]
        
        # 2-3 years average: 9-10
        if any(pattern in text for pattern in ["2 years", "3 years", "two years", "three years", "2-3 years"]):
            return 9.0
        
        # 1-2 years: 6-8
        elif any(pattern in text for pattern in ["1 year", "one year", "1-2 years"]):
            return 7.0
        
        # Look for job hopping indicators
        job_hop_indicators = ["6 months", "3 months", "contract", "freelance"]
        if any(indicator in text for indicator in job_hop_indicators):
            return 3.5  # Job hopping: 3-5
        
        # Check for multiple recent years (might indicate frequent job changes)
        recent_years = [str(year) for year in range(2020, 2026)]
        year_mentions = sum(1 for year in recent_years if year in text)
        
        if year_mentions >= 4:
            return 4.0  # Possible job hopping
        elif year_mentions >= 2:
            return 7.5  # Reasonable tenure
        
        return 6.5  # Default
    
    # Helper methods
    def _extract_job_info(self, job_description: str) -> Dict:
        """Extract key information from job description"""
        text_lower = job_description.lower()
        
        # Extract location
        location = ""
        locations = [
            "san francisco", "mountain view", "palo alto", "san jose", "berkeley",
            "new york", "seattle", "austin", "boston", "chicago"
        ]
        
        for loc in locations:
            if loc in text_lower:
                location = loc
                break
        
        # Extract company name (simple heuristic)
        company = ""
        if " at " in text_lower:
            parts = job_description.split(" at ")
            if len(parts) > 1:
                company = parts[1].split("\n")[0].split(",")[0].strip()
        
        return {
            "location": location,
            "company": company
        }
    
    def _generate_ai_message(self, candidate: Dict, job_description: str) -> str:
        """Generate personalized message using Gemini"""
        try:
            name = candidate['name'] if candidate['name'] not in ["Unknown", "Profile User"] else "there"
            
            # Extract key details for personalization
            job_lines = job_description.split('\n')
            company = "our company"
            role = "this role"
            
            # Try to extract company and role
            for line in job_lines[:3]:
                if " at " in line:
                    parts = line.split(" at ")
                    if len(parts) > 1:
                        company = parts[1].strip()
                        role = parts[0].strip()
                        break
            
            prompt = f"""Write a LinkedIn outreach message (max 150 words) for:
            
Candidate: {name}
Their background: {candidate.get('headline', 'Software Engineer')}
Current company: {candidate.get('company', 'N/A')}
Score: {candidate['score']}/10

Job: {role} at {company}

Make it personal and reference their background. Keep it professional and concise.
Start with "Hi {name}," and don't use placeholder brackets."""

            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            
            # Clean up any remaining placeholders
            message = response.text.strip()
            message = message.replace("[Candidate Name]", name)
            message = message.replace("[Your Name]", "")
            message = message.replace("[Your Title]", "")
            
            return message
            
        except Exception as e:
            logger.error(f"AI message generation failed: {e}")
            return self._generate_template_message(candidate, job_description)
    
    def _generate_template_message(self, candidate: Dict, job_description: str) -> str:
        """Generate message from template"""
        name = candidate['name'] if candidate['name'] not in ["Unknown", "Profile User"] else "there"
        headline = candidate.get('headline', 'software engineer')
        
        # Extract company/role from job description
        job_lines = job_description.split('\n')
        company = "our company"
        role = "an exciting opportunity"
        
        for line in job_lines[:3]:
            if " at " in line:
                parts = line.split(" at ")
                if len(parts) > 1:
                    company = parts[1].strip()
                    role = parts[0].strip()
                    break
        
        return f"""Hi {name},

I noticed your background as a {headline} and was impressed by your experience at {candidate.get('company', 'your current company')}.

We're looking for someone for a {role} position at {company}. Given your background and skills, I think you'd be a great fit for this opportunity.

Would you be open to a brief chat about this role?

Best regards"""

    def save_results(self, job_id: str, candidates: List[Dict], messages: List[Dict]):
        """Save results to database"""
        cursor = self.conn.cursor()
        
        for i, candidate in enumerate(candidates):
            message = messages[i]["message"] if i < len(messages) else ""
            
            cursor.execute('''
                INSERT OR REPLACE INTO candidates 
                (job_id, name, linkedin_url, fit_score, score_breakdown, outreach_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                job_id,
                candidate["name"],
                candidate["linkedin_url"],
                candidate["score"],
                json.dumps(candidate["breakdown"]),
                message
            ))
        
        self.conn.commit()
        logger.info(f"Saved {len(candidates)} candidates to database")

# Main execution
def main():
    """Main entry point - runs the interactive pipeline"""
    try:
        agent = LinkedInSourcingAgent()
        agent.run_pipeline()
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()