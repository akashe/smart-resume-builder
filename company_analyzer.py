from typing import Dict, Any, List, Tuple
from openai import OpenAI
import os
import json
import re

class CompanyAnalyzer:
    """Analyze job descriptions to understand company culture, values, and hidden preferences"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Company type indicators
        self.company_indicators = {
            "startup": [
                "startup", "scale-up", "growth stage", "series a", "series b", "venture backed",
                "fast-paced", "wearing many hats", "early stage", "founding team", "equity",
                "mvp", "product-market fit", "bootstrapped", "disruptive", "innovative"
            ],
            "big_tech": [
                "faang", "google", "facebook", "amazon", "apple", "microsoft", "netflix",
                "meta", "alphabet", "distributed systems", "massive scale", "billions of users",
                "petabyte", "global infrastructure", "large-scale systems"
            ],
            "enterprise": [
                "enterprise", "fortune 500", "established company", "industry leader",
                "global organization", "multinational", "corporate", "traditional",
                "legacy systems", "compliance", "governance", "risk management",
                "stakeholder management", "enterprise architecture"
            ],
            "consulting": [
                "consulting", "client-facing", "client solutions", "professional services",
                "project-based", "client delivery", "billable hours", "engagement",
                "multiple clients", "client success", "implementation", "advisory"
            ],
            "finance": [
                "fintech", "financial services", "banking", "investment", "trading",
                "regulatory compliance", "sox", "pci", "financial modeling",
                "risk assessment", "audit", "capital markets"
            ],
            "healthtech": [
                "healthcare", "medical", "biotech", "pharmaceutical", "clinical",
                "fda", "hipaa", "patient data", "medical devices", "life sciences"
            ]
        }
        
        # Values indicators
        self.values_indicators = {
            "innovation": [
                "cutting-edge", "latest technology", "emerging tech", "research",
                "experimental", "prototype", "proof of concept", "innovation",
                "disruptive", "breakthrough", "pioneering", "state-of-the-art"
            ],
            "stability": [
                "proven", "established", "reliable", "stable", "mature",
                "production-ready", "enterprise-grade", "battle-tested",
                "robust", "scalable", "maintainable", "long-term"
            ],
            "speed": [
                "fast-paced", "rapid", "agile", "quick", "accelerated",
                "time-to-market", "iterative", "sprint", "deadline-driven",
                "fast delivery", "rapid prototyping", "mvp"
            ],
            "scale": [
                "large-scale", "massive", "millions", "billions", "global",
                "distributed", "high-volume", "enterprise-scale",
                "petabyte", "high-throughput", "concurrent users"
            ],
            "process": [
                "methodology", "framework", "best practices", "standards",
                "governance", "compliance", "documentation", "process improvement",
                "quality assurance", "code review", "testing"
            ],
            "leadership": [
                "lead", "mentor", "manage", "guide", "coordinate",
                "cross-functional", "stakeholder", "team leadership",
                "people management", "influence", "drive alignment"
            ]
        }

    def research_company_with_web_search(self, company_name: str) -> Dict[str, Any]:
        """Research company using web search to get detailed information"""
        
        company_info = {
            "company_name": company_name,
            "type_indicators": [],
            "culture_signals": [],
            "tech_preferences": [],
            "size_stage": "",
            "recent_context": []
        }
        
        # This would be called from the UI using WebSearch tool
        # For now, return structure that can be populated
        return company_info

    def analyze_company_dna(self, job_description: str, company_name: str = "") -> Dict[str, Any]:
        """
        Comprehensive analysis of company culture and values from job description
        """
        
        # Basic analysis using keywords
        company_type = self._detect_company_type(job_description, company_name)
        values_scores = self._calculate_values_scores(job_description)
        
        # AI-powered deep analysis
        ai_analysis = self._ai_deep_analysis(job_description, company_name)
        
        # Combine analyses
        analysis = {
            "company_name": company_name,
            "company_type": company_type,
            "confidence": self._calculate_confidence(job_description, company_type),
            "values_scores": values_scores,
            "top_values": self._get_top_values(values_scores),
            "hiring_manager_signals": ai_analysis.get("hiring_manager_type", "unknown"),
            "red_flags": ai_analysis.get("red_flags", []),
            "golden_signals": ai_analysis.get("golden_signals", []),
            "hidden_preferences": ai_analysis.get("hidden_preferences", {}),
            "language_preferences": ai_analysis.get("language_preferences", {}),
            "positioning_advice": self._generate_positioning_advice(company_type, values_scores)
        }
        
        return analysis

    def _detect_company_type(self, job_description: str, company_name: str) -> str:
        """Detect company type based on keywords and patterns"""
        
        text_to_analyze = (job_description + " " + company_name).lower()
        type_scores = {}
        
        for company_type, indicators in self.company_indicators.items():
            score = 0
            for indicator in indicators:
                if indicator in text_to_analyze:
                    # Weight by importance (longer phrases = more specific)
                    weight = len(indicator.split())
                    score += weight
            type_scores[company_type] = score
        
        # Return type with highest score, default to "tech" if no clear match
        if not type_scores or max(type_scores.values()) == 0:
            return "tech"
        
        return max(type_scores, key=type_scores.get)

    def _calculate_values_scores(self, job_description: str) -> Dict[str, float]:
        """Calculate values scores based on keyword frequency and context"""
        
        text = job_description.lower()
        values_scores = {}
        
        for value_type, indicators in self.values_indicators.items():
            score = 0
            for indicator in indicators:
                count = text.count(indicator)
                # Weight by phrase length and frequency
                weight = len(indicator.split())
                score += count * weight
            
            # Normalize score
            max_possible = len(indicators) * 3  # Assume max 3 occurrences per indicator
            normalized_score = min(score / max_possible, 1.0) if max_possible > 0 else 0.0
            values_scores[value_type] = round(normalized_score, 2)
        
        return values_scores

    def _ai_deep_analysis(self, job_description: str, company_name: str) -> Dict[str, Any]:
        """Use AI to extract subtle cultural indicators and preferences"""
        
        prompt = f"""
        Analyze this job description and return valid JSON only.
        
        Company: {company_name}
        Job Description: {job_description[:2000]}
        
        Return this exact JSON structure (no additional text):
        {{
            "hiring_manager_type": "technical_leader",
            "red_flags": ["Experimental technologies without proven results", "Lack of collaborative experience"],
            "golden_signals": ["System design thinking", "Cross-team collaboration"],
            "hidden_preferences": {{
                "prefers_generalists_vs_specialists": "balanced",
                "values_depth_vs_breadth": "balanced",
                "innovation_tolerance": "medium",
                "risk_tolerance": "moderate"
            }},
            "language_preferences": {{
                "avoid_phrases": ["bleeding edge", "quick hack"],
                "golden_phrases": ["scalable", "maintainable"],
                "technical_depth_expected": "medium"
            }}
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            print(f"DEBUG: AI response content: {content[:200]}...")  # Debug output
            
            # Clean the response - remove any markdown formatting
            if content.startswith('```json'):
                content = content.replace('```json', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            # Try to parse JSON
            try:
                parsed_result = json.loads(content)
                return parsed_result
            except json.JSONDecodeError as json_error:
                print(f"JSON parsing failed: {json_error}")
                print(f"Raw content: {content}")
                
                # Fallback: create a basic response
                return {
                    "hiring_manager_type": "business_focused",
                    "red_flags": ["Unable to parse AI response"],
                    "golden_signals": ["Standard professional experience"],
                    "hidden_preferences": {
                        "prefers_generalists_vs_specialists": "balanced",
                        "values_depth_vs_breadth": "balanced",
                        "innovation_tolerance": "medium",
                        "risk_tolerance": "moderate"
                    },
                    "language_preferences": {
                        "avoid_phrases": [],
                        "golden_phrases": [],
                        "technical_depth_expected": "medium"
                    }
                }
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return {
                "hiring_manager_type": "unknown",
                "red_flags": ["Analysis unavailable"],
                "golden_signals": ["Standard professional experience"],
                "hidden_preferences": {
                    "prefers_generalists_vs_specialists": "balanced",
                    "values_depth_vs_breadth": "balanced", 
                    "innovation_tolerance": "medium",
                    "risk_tolerance": "moderate"
                },
                "language_preferences": {
                    "avoid_phrases": [],
                    "golden_phrases": [],
                    "technical_depth_expected": "medium"
                }
            }

    def _calculate_confidence(self, job_description: str, company_type: str) -> float:
        """Calculate confidence in company type detection"""
        
        if not company_type or company_type == "tech":
            return 0.5  # Low confidence for generic classification
        
        indicators = self.company_indicators.get(company_type, [])
        text = job_description.lower()
        
        matches = sum(1 for indicator in indicators if indicator in text)
        confidence = min(matches / len(indicators) * 2, 1.0)  # Scale to 0-1
        
        return round(confidence, 2)

    def _get_top_values(self, values_scores: Dict[str, float], top_n: int = 3) -> List[str]:
        """Get top N values based on scores"""
        
        sorted_values = sorted(values_scores.items(), key=lambda x: x[1], reverse=True)
        return [value for value, score in sorted_values[:top_n] if score > 0.1]

    def _generate_positioning_advice(self, company_type: str, values_scores: Dict[str, float]) -> Dict[str, List[str]]:
        """Generate specific positioning advice based on company analysis"""
        
        advice = {
            "emphasize": [],
            "avoid": [],
            "language_tips": []
        }
        
        # Company type specific advice
        if company_type == "startup":
            advice["emphasize"].extend([
                "Speed of execution and rapid delivery",
                "Ownership and initiative-taking",
                "Resource efficiency and scrappy solutions",
                "Direct impact on business metrics"
            ])
            advice["avoid"].extend([
                "Over-engineered solutions",
                "Long development cycles",
                "Corporate bureaucracy mentions"
            ])
            
        elif company_type == "enterprise":
            advice["emphasize"].extend([
                "Scalability and maintainability",
                "Process improvement and standardization", 
                "Cross-team collaboration",
                "Risk mitigation and stability"
            ])
            advice["avoid"].extend([
                "Experimental or unproven technologies",
                "Quick hacks or shortcuts",
                "Solo contributor achievements only"
            ])
            
        elif company_type == "big_tech":
            advice["emphasize"].extend([
                "Large-scale system design",
                "Performance optimization at scale",
                "Cross-functional impact",
                "Technical leadership and mentoring"
            ])
            advice["avoid"].extend([
                "Small-scale personal projects",
                "Technologies not used at big tech",
                "Lack of quantified impact"
            ])
        
        # Values-based advice
        if values_scores.get("innovation", 0) > 0.6:
            advice["language_tips"].append("Use 'cutting-edge', 'emerging tech', 'innovation'")
        elif values_scores.get("stability", 0) > 0.6:
            advice["language_tips"].append("Use 'proven', 'reliable', 'enterprise-grade'")
            
        if values_scores.get("scale", 0) > 0.6:
            advice["language_tips"].append("Emphasize numbers: users, requests, data volume")
            
        if values_scores.get("leadership", 0) > 0.6:
            advice["language_tips"].append("Highlight mentoring, cross-team work, influence")
        
        return advice

    def analyze_resume_company_fit(self, resume_data: Dict[str, Any], company_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well a resume fits with company preferences"""
        
        fit_analysis = {
            "overall_fit_score": 0.0,
            "strengths": [],
            "gaps": [],
            "positioning_opportunities": [],
            "red_flag_risks": []
        }
        
        # Analyze fit using AI
        prompt = f"""
        Analyze the fit between this resume and company preferences:
        
        Company Analysis:
        - Type: {company_analysis['company_type']}
        - Top Values: {company_analysis['top_values']}
        - Red Flags: {company_analysis['red_flags']}
        - Golden Signals: {company_analysis['golden_signals']}
        
        Resume Summary:
        - Experience: {len(resume_data.get('experience', []))} positions
        - Skills: {list(resume_data.get('skills', {}).keys())}
        - Projects: {len(resume_data.get('projects', []))} projects
        
        Sample Experience Entry:
        {resume_data.get('experience', [{}])[0] if resume_data.get('experience') else 'None'}
        
        Return JSON analysis:
        {{
            "overall_fit_score": 0.85,
            "strengths": ["List what matches well"],
            "gaps": ["List what's missing or misaligned"],
            "positioning_opportunities": ["How to reframe existing experience"],
            "red_flag_risks": ["Things that might concern this company"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            ai_analysis = json.loads(response.choices[0].message.content)
            fit_analysis.update(ai_analysis)
            
        except Exception as e:
            print(f"Fit analysis failed: {e}")
        
        return fit_analysis