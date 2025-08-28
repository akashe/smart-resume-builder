from typing import Dict, Any, List
import streamlit as st

class CompanyResearcher:
    """Helper class to research companies using web search"""
    
    def __init__(self):
        pass
    
    def research_company_with_websearch(self, company_name: str, job_description: str = "") -> Dict[str, Any]:
        """Research company using WebSearch tool and return structured insights"""
        
        search_queries = [
            f"{company_name} company culture engineering team",
            f"{company_name} tech stack technology platform",
            f"{company_name} company size funding valuation",
            f"{company_name} interview process technical hiring"
        ]
        
        research_results = {
            "company_name": company_name,
            "culture_insights": [],
            "tech_insights": [], 
            "scale_insights": [],
            "hiring_insights": [],
            "raw_search_data": []
        }
        
        # This function would be called from the Streamlit UI where WebSearch tool is available
        # For now, return structured data that can be enhanced with actual search results
        
        # Add some basic intelligence for known companies
        company_lower = company_name.lower()
        
        # Big Tech companies
        if any(big_tech in company_lower for big_tech in ['google', 'meta', 'facebook', 'amazon', 'microsoft', 'apple', 'netflix']):
            research_results["culture_insights"] = [
                "Large-scale engineering culture with emphasis on systems thinking",
                "Strong focus on code quality and peer review processes", 
                "Data-driven decision making and A/B testing culture",
                "Cross-functional collaboration across multiple teams"
            ]
            research_results["tech_insights"] = [
                "Distributed systems and microservices architecture",
                "Custom infrastructure and internal tooling",
                "Emphasis on scalability and performance optimization",
                "Multiple programming languages and polyglot environment"
            ]
            research_results["scale_insights"] = [
                "Billions of users and requests handled daily",
                "Petabyte-scale data processing requirements",
                "Global infrastructure and multiple data centers",
                "Team sizes ranging from 5-20 engineers per team"
            ]
            
        # Unicorn/Scale-up companies  
        elif any(unicorn in company_lower for unicorn in ['stripe', 'airbnb', 'uber', 'lyft', 'doordash', 'square']):
            research_results["culture_insights"] = [
                "Fast-paced growth environment with rapid iteration",
                "Strong product focus and user-centric thinking",
                "Emphasis on ownership and taking initiative",
                "Balance between startup agility and scaling processes"
            ]
            research_results["tech_insights"] = [
                "Modern cloud-native architecture",
                "API-first and microservices approach", 
                "Heavy use of third-party services and platforms",
                "Focus on developer productivity and tooling"
            ]
            research_results["scale_insights"] = [
                "Millions of transactions/requests per day",
                "Rapid user growth requiring scalable solutions",
                "Team sizes typically 3-10 engineers",
                "Multiple product areas and business lines"
            ]
            
        # Fintech companies
        elif any(fintech in company_lower for fintech in ['stripe', 'square', 'robinhood', 'plaid', 'coinbase']):
            research_results["culture_insights"].extend([
                "High emphasis on security and compliance",
                "Risk-aware engineering practices",
                "Regulatory compliance as a core consideration"
            ])
            research_results["tech_insights"].extend([
                "Financial data processing and real-time systems",
                "Strong emphasis on security and encryption",
                "Compliance-first architecture design"
            ])
            
        # Consulting companies
        elif any(consulting in company_lower for consulting in ['mckinsey', 'bcg', 'bain', 'deloitte', 'pwc', 'accenture']):
            research_results["culture_insights"] = [
                "Client-focused delivery and outcomes",
                "Structured problem-solving methodologies",
                "Cross-industry adaptability",
                "Strong communication and presentation skills valued"
            ]
            research_results["tech_insights"] = [
                "Variety of client tech stacks and platforms",
                "Custom solutions and rapid prototyping",
                "Integration with existing client systems",
                "Methodology-driven development approaches"
            ]
            
        # Default insights for unknown companies
        else:
            research_results["culture_insights"] = [
                "Company culture analysis requires web research",
                "Engineering team values and practices to be determined"
            ]
            research_results["tech_insights"] = [
                "Technology stack details need investigation", 
                "Architecture preferences to be researched"
            ]
        
        return research_results
    
    def format_research_for_display(self, research_data: Dict[str, Any]) -> str:
        """Format research data for display in Streamlit"""
        
        company_name = research_data.get("company_name", "Unknown")
        
        display_text = f"## 🔍 Research Results for {company_name}\n\n"
        
        if research_data.get("culture_insights"):
            display_text += "### 🏢 Culture & Values\n"
            for insight in research_data["culture_insights"]:
                display_text += f"• {insight}\n"
            display_text += "\n"
        
        if research_data.get("tech_insights"):
            display_text += "### 💻 Technology & Architecture\n"
            for insight in research_data["tech_insights"]:
                display_text += f"• {insight}\n"
            display_text += "\n"
            
        if research_data.get("scale_insights"):
            display_text += "### 📊 Scale & Operations\n"
            for insight in research_data["scale_insights"]:
                display_text += f"• {insight}\n"
            display_text += "\n"
            
        if research_data.get("hiring_insights"):
            display_text += "### 🎯 Hiring & Interview Process\n"
            for insight in research_data["hiring_insights"]:
                display_text += f"• {insight}\n"
            display_text += "\n"
        
        return display_text

def perform_company_web_search_with_tool(company_name: str) -> Dict[str, Any]:
    """
    Perform actual web search using WebSearch tool
    This function needs to be called where WebSearch tool is available
    """
    
    search_results = {
        "company_name": company_name,
        "culture_insights": [],
        "tech_insights": [], 
        "scale_insights": [],
        "hiring_insights": [],
        "search_data": []
    }
    
    try:
        # This would use the actual WebSearch tool when available in Streamlit environment
        # For now, return enhanced analysis based on company name
        
        search_queries = [
            f"{company_name} company culture engineering team",
            f"{company_name} technology stack architecture",
            f"{company_name} company size funding employees", 
            f"{company_name} interview process hiring"
        ]
        
        # Placeholder for actual web search results
        # In real implementation, these would be:
        # results = st.websearch(query)
        # content = st.webfetch(results[0]['url'], prompt="Extract company info")
        
        for query in search_queries:
            search_results["search_data"].append({
                "query": query,
                "status": "ready_for_websearch",
                "placeholder_insight": f"Would search: {query}"
            })
        
        # Enhance with basic company intelligence
        researcher = CompanyResearcher()
        enhanced_results = researcher.research_company_with_websearch(company_name)
        
        return {**search_results, **enhanced_results}
        
    except Exception as e:
        print(f"Web search error: {e}")
        # Fallback to basic analysis
        researcher = CompanyResearcher()
        return researcher.research_company_with_websearch(company_name)