from typing import Dict, Any, List, Tuple
from openai import OpenAI
import os
import json
from company_analyzer import CompanyAnalyzer

class PositioningCoach:
    """AI coach that helps translate and position resume content for different company types"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.company_analyzer = CompanyAnalyzer()
        
        # Translation patterns for common technologist language
        self.translation_patterns = {
            # Your natural language → Different company contexts
            "implemented latest tech": {
                "startup": "drove technical innovation and competitive advantage",
                "enterprise": "led digital transformation initiatives",
                "consulting": "delivered cutting-edge solutions for clients",
                "big_tech": "adopted emerging technologies at scale",
                "finance": "modernized technology stack while ensuring compliance"
            },
            
            "built it quickly": {
                "startup": "delivered MVP ahead of schedule",
                "enterprise": "accelerated time-to-market through agile delivery",
                "consulting": "exceeded client timeline expectations",
                "big_tech": "optimized development velocity for rapid iteration",
                "finance": "streamlined delivery while maintaining regulatory standards"
            },
            
            "new technology": {
                "startup": "emerging technology stack",
                "enterprise": "strategic technology adoption",
                "consulting": "innovative client solutions",
                "big_tech": "next-generation platform technologies",
                "finance": "modern, compliant technology solutions"
            },
            
            "microservices": {
                "startup": "scalable service architecture",
                "enterprise": "enterprise service architecture with governance",
                "consulting": "modular, client-adaptable solutions",
                "big_tech": "distributed systems architecture",
                "finance": "secure, auditable service architecture"
            },
            
            "machine learning": {
                "startup": "AI-driven product features",
                "enterprise": "enterprise AI and analytics capabilities", 
                "consulting": "data science solutions for client outcomes",
                "big_tech": "large-scale ML systems and infrastructure",
                "finance": "quantitative modeling and risk analytics"
            },
            
            "prototype": {
                "startup": "rapid product validation",
                "enterprise": "proof of concept for strategic initiatives",
                "consulting": "solution demonstration and validation",
                "big_tech": "experimental feature development",
                "finance": "model validation and testing framework"
            }
        }
        
        # Industry wisdom and hidden rules
        self.industry_wisdom = {
            "startup": {
                "golden_rules": [
                    "Emphasize speed, ownership, and direct business impact",
                    "Show resourcefulness and ability to wear multiple hats",
                    "Highlight metrics that show growth or efficiency gains",
                    "Demonstrate adaptability and learning agility"
                ],
                "avoid": [
                    "Over-engineered solutions or gold-plating",
                    "Long development cycles or extensive planning phases",
                    "Rigid processes or bureaucratic language",
                    "Technologies that don't add immediate value"
                ],
                "key_phrases": [
                    "rapid iteration", "MVP", "product-market fit", 
                    "scrappy", "resourceful", "direct impact"
                ]
            },
            
            "enterprise": {
                "golden_rules": [
                    "Emphasize scalability, maintainability, and governance",
                    "Show cross-team collaboration and stakeholder management",
                    "Highlight process improvements and risk mitigation",
                    "Demonstrate enterprise architecture thinking"
                ],
                "avoid": [
                    "Experimental or unproven technologies",
                    "Quick hacks or technical shortcuts", 
                    "Solo work without team collaboration",
                    "Disrupting existing workflows without consideration"
                ],
                "key_phrases": [
                    "enterprise-grade", "scalable", "governance",
                    "stakeholder alignment", "strategic initiative"
                ]
            },
            
            "big_tech": {
                "golden_rules": [
                    "Scale is everything - mention users, requests, data volumes",
                    "System design and architecture are highly valued",
                    "Technical leadership and mentoring are important",
                    "Cross-functional impact and collaboration matter"
                ],
                "avoid": [
                    "Small-scale personal projects without context",
                    "Technologies not commonly used at big tech",
                    "Individual contributor work without broader impact",
                    "Lack of quantified metrics and scale"
                ],
                "key_phrases": [
                    "large-scale", "distributed systems", "millions of users",
                    "cross-functional", "technical leadership"
                ]
            },
            
            "consulting": {
                "golden_rules": [
                    "Everything should be framed in terms of client value",
                    "Adaptability across industries is crucial",
                    "Methodology and frameworks demonstrate professionalism",
                    "Communication and presentation skills are key"
                ],
                "avoid": [
                    "Internal-only projects without client context",
                    "Personal learning or exploration without deliverables",
                    "Technical details without business context",
                    "Single-industry or technology focus"
                ],
                "key_phrases": [
                    "client success", "stakeholder management", "cross-industry",
                    "methodology", "deliverable", "engagement"
                ]
            },
            
            "finance": {
                "golden_rules": [
                    "Compliance and risk management are paramount",
                    "Quantified business impact is essential",
                    "Stability and reliability over innovation",
                    "Regulatory knowledge is highly valued"
                ],
                "avoid": [
                    "Experimental or unregulated technologies",
                    "Rapid changes without proper governance",
                    "Lack of attention to security and compliance",
                    "Technologies that introduce regulatory risk"
                ],
                "key_phrases": [
                    "compliant", "risk mitigation", "audit-ready",
                    "regulatory", "quantified ROI"
                ]
            }
        }

    def analyze_and_reposition(self, resume_data: Dict[str, Any], job_description: str, company_name: str = "") -> Dict[str, Any]:
        """Complete analysis and repositioning recommendations"""
        
        try:
            # Analyze company DNA
            company_analysis = self.company_analyzer.analyze_company_dna(job_description, company_name)
            
            # Analyze current resume fit
            fit_analysis = self.company_analyzer.analyze_resume_company_fit(resume_data, company_analysis)
            
            # Generate repositioning recommendations
            repositioning_suggestions = self._generate_repositioning_suggestions(
                resume_data, company_analysis, fit_analysis
            )
            
            return {
                "company_analysis": company_analysis,
                "fit_analysis": fit_analysis, 
                "repositioning_suggestions": repositioning_suggestions
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            # Return safe defaults
            return {
                "company_analysis": {
                    "company_type": "tech",
                    "confidence": 0.5,
                    "values_scores": {"innovation": 0.5, "stability": 0.5},
                    "top_values": ["innovation", "collaboration"],
                    "red_flags": ["Analysis error occurred"],
                    "golden_signals": ["Professional experience"],
                    "positioning_advice": {"emphasize": [], "avoid": [], "language_tips": []}
                },
                "fit_analysis": {
                    "overall_fit_score": 0.7,
                    "strengths": ["Experience matches general requirements"],
                    "gaps": ["Analysis needs refinement"],
                    "positioning_opportunities": [],
                    "red_flag_risks": []
                },
                "repositioning_suggestions": {
                    "experience_translations": [],
                    "summary_recommendations": [],
                    "skills_repositioning": [],
                    "language_changes": [],
                    "overall_strategy": {
                        "golden_rules": ["Focus on impact and results"],
                        "things_to_avoid": ["Generic descriptions"],
                        "key_phrases_to_use": ["delivered", "improved", "collaborated"]
                    }
                }
            }

    def _generate_repositioning_suggestions(self, resume_data: Dict[str, Any], 
                                          company_analysis: Dict[str, Any], 
                                          fit_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific suggestions for repositioning resume content"""
        
        company_type = company_analysis['company_type']
        wisdom = self.industry_wisdom.get(company_type, {})
        
        suggestions = {
            "experience_translations": [],
            "summary_recommendations": [],
            "skills_repositioning": [],
            "language_changes": [],
            "overall_strategy": []
        }
        
        # Analyze each experience entry
        for i, experience in enumerate(resume_data.get('experience', [])):
            exp_suggestions = self._reposition_experience_entry(experience, company_type, company_analysis)
            if exp_suggestions:
                suggestions["experience_translations"].append({
                    "experience_index": i,
                    "company": experience.get('company', 'Unknown'),
                    "position": experience.get('position', 'Unknown'),
                    "suggestions": exp_suggestions
                })
        
        # Summary recommendations
        if resume_data.get('summary', {}).get('sentences'):
            summary_suggestions = self._reposition_summary(
                resume_data['summary']['sentences'], company_type, company_analysis
            )
            suggestions["summary_recommendations"] = summary_suggestions
        
        # Skills repositioning
        if resume_data.get('skills'):
            skills_suggestions = self._reposition_skills(
                resume_data['skills'], company_type, company_analysis
            )
            suggestions["skills_repositioning"] = skills_suggestions
        
        # Overall strategy based on company wisdom
        if wisdom:
            suggestions["overall_strategy"] = {
                "golden_rules": wisdom.get("golden_rules", []),
                "things_to_avoid": wisdom.get("avoid", []),
                "key_phrases_to_use": wisdom.get("key_phrases", [])
            }
        
        return suggestions

    def _reposition_experience_entry(self, experience: Dict[str, Any], 
                                   company_type: str, company_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate repositioning suggestions for a single experience entry"""
        
        suggestions = []
        
        # Analyze accomplishments for repositioning opportunities
        accomplishments = experience.get('accomplishments', [])
        
        for acc in accomplishments:
            # Use AI to generate company-specific repositioning
            repositioned = self._ai_reposition_accomplishment(acc, company_type, company_analysis)
            if repositioned and repositioned != acc:
                suggestions.append({
                    "original": acc,
                    "repositioned": repositioned,
                    "reasoning": f"Better aligned with {company_type} preferences"
                })
        
        # Check role summaries too
        role_summaries = experience.get('role_summaries', [])
        for summary in role_summaries:
            repositioned = self._ai_reposition_role_summary(summary, company_type, company_analysis)
            if repositioned and repositioned != summary:
                suggestions.append({
                    "original": summary,
                    "repositioned": repositioned,
                    "reasoning": f"Emphasizes {company_type} values better"
                })
        
        return suggestions

    def _ai_reposition_accomplishment(self, accomplishment: str, 
                                    company_type: str, company_analysis: Dict[str, Any]) -> str:
        """Use AI to reposition an accomplishment for a specific company type"""
        
        prompt = f"""
        Reposition this accomplishment for a {company_type} company:
        
        Original: "{accomplishment}"
        
        Company prefers: {company_analysis.get('top_values', [])}
        Company red flags: {company_analysis.get('red_flags', [])}
        Company golden signals: {company_analysis.get('golden_signals', [])}
        
        Rules for {company_type}:
        - {self.industry_wisdom.get(company_type, {}).get('golden_rules', ['Focus on impact'])[0]}
        - Avoid: {self.industry_wisdom.get(company_type, {}).get('avoid', ['Generic language'])[0]}
        
        Return ONLY the repositioned accomplishment, keeping the same core facts but changing emphasis and language.
        Make it sound more appealing to this company type while staying truthful.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI repositioning failed: {e}")
            return accomplishment

    def _ai_reposition_role_summary(self, role_summary: str, 
                                   company_type: str, company_analysis: Dict[str, Any]) -> str:
        """Use AI to reposition a role summary for a specific company type"""
        
        prompt = f"""
        Reposition this role summary for a {company_type} company:
        
        Original: "{role_summary}"
        
        Company values: {company_analysis.get('top_values', [])}
        
        For {company_type} companies, emphasize:
        {chr(10).join(['- ' + rule for rule in self.industry_wisdom.get(company_type, {}).get('golden_rules', [])[:2]])}
        
        Return ONLY the repositioned role summary, same facts but better framing for this company type.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI repositioning failed: {e}")
            return role_summary

    def _reposition_summary(self, sentences: List[str], 
                           company_type: str, company_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate repositioning suggestions for summary sentences"""
        
        suggestions = []
        
        for sentence in sentences:
            # Generate company-specific version
            repositioned = self._ai_reposition_summary_sentence(sentence, company_type, company_analysis)
            if repositioned and repositioned != sentence:
                suggestions.append({
                    "original": sentence,
                    "repositioned": repositioned,
                    "reasoning": f"Better resonates with {company_type} hiring managers"
                })
        
        return suggestions

    def _ai_reposition_summary_sentence(self, sentence: str, 
                                       company_type: str, company_analysis: Dict[str, Any]) -> str:
        """Reposition a summary sentence for a specific company type"""
        
        prompt = f"""
        Reposition this summary sentence for a {company_type} company:
        
        Original: "{sentence}"
        
        Company type: {company_type}
        Company values: {company_analysis.get('top_values', [])}
        
        Use language that resonates with {company_type} hiring managers.
        Keep the same core message but adjust emphasis and terminology.
        
        Return ONLY the repositioned sentence.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"AI repositioning failed: {e}")
            return sentence

    def _reposition_skills(self, skills: Dict[str, List[str]], 
                          company_type: str, company_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest skills repositioning based on company type"""
        
        suggestions = {
            "emphasize": [],
            "de_emphasize": [],
            "add_context": [],
            "reframe": []
        }
        
        # Company-specific skill preferences
        if company_type == "enterprise":
            # Enterprise loves governance, scalability, integration
            for category, skill_list in skills.items():
                if any(skill.lower() in ["kubernetes", "docker", "microservices"] for skill in skill_list):
                    suggestions["add_context"].append(
                        "Add context about enterprise deployment, scaling, and governance for containerization skills"
                    )
                    
        elif company_type == "startup":
            # Startups love full-stack, rapid development
            suggestions["emphasize"].append("Highlight versatility and full-stack capabilities")
            suggestions["de_emphasize"].append("Reduce emphasis on specialized enterprise tools")
            
        elif company_type == "big_tech":
            # Big tech loves scale, distributed systems, performance
            suggestions["emphasize"].append("Emphasize distributed systems, performance optimization, and scale")
            
        return suggestions

    def get_translation_suggestion(self, original_text: str, company_type: str) -> str:
        """Get quick translation suggestion based on common patterns"""
        
        original_lower = original_text.lower()
        
        # Check for common patterns
        for pattern, translations in self.translation_patterns.items():
            if pattern in original_lower:
                return translations.get(company_type, original_text)
        
        return original_text  # No translation found

    def generate_positioning_report(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a comprehensive positioning report"""
        
        company_analysis = analysis_result["company_analysis"]
        fit_analysis = analysis_result["fit_analysis"]
        suggestions = analysis_result["repositioning_suggestions"]
        
        report = f"""
# 🎯 Resume Positioning Report

## 🏢 Company Analysis
- **Type**: {company_analysis['company_type'].title()}
- **Confidence**: {company_analysis['confidence'] * 100:.0f}%
- **Top Values**: {', '.join(company_analysis['top_values'])}

## 📊 Current Fit Score: {fit_analysis['overall_fit_score'] * 100:.0f}%

### ✅ Your Strengths
{chr(10).join(['- ' + strength for strength in fit_analysis.get('strengths', [])])}

### ⚠️ Areas for Improvement  
{chr(10).join(['- ' + gap for gap in fit_analysis.get('gaps', [])])}

## 🔄 Repositioning Strategy

### Golden Rules for {company_analysis['company_type'].title()} Companies:
{chr(10).join(['- ' + rule for rule in suggestions['overall_strategy'].get('golden_rules', [])])}

### Key Phrases to Use:
{', '.join(suggestions['overall_strategy'].get('key_phrases_to_use', []))}

### Things to Avoid:
{chr(10).join(['- ' + avoid for avoid in suggestions['overall_strategy'].get('things_to_avoid', [])])}
        """
        
        return report.strip()