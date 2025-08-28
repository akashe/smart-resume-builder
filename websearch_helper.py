"""
Helper functions for WebSearch integration
This module provides WebSearch functionality when called from Streamlit environment
"""

from typing import Dict, Any, List
import streamlit as st

def perform_company_websearch(company_name: str) -> Dict[str, Any]:
    """
    Perform actual web search using WebSearch tool available in Streamlit
    
    This function should be called from the Streamlit UI where WebSearch is available
    """
    
    search_results = {
        "company_name": company_name,
        "searches_performed": [],
        "insights": {
            "culture": [],
            "technology": [],
            "scale": [],
            "hiring": []
        },
        "raw_data": []
    }
    
    # Define search queries
    search_queries = [
        {
            "query": f"{company_name} engineering culture team values",
            "category": "culture",
            "purpose": "Understanding company culture and engineering values"
        },
        {
            "query": f"{company_name} technology stack architecture platform",
            "category": "technology", 
            "purpose": "Learning about tech stack and architecture preferences"
        },
        {
            "query": f"{company_name} company size funding employees growth",
            "category": "scale",
            "purpose": "Understanding company scale and growth stage"
        },
        {
            "query": f"{company_name} interview process hiring technical questions",
            "category": "hiring",
            "purpose": "Learning about interview process and what they look for"
        }
    ]
    
    # Perform searches (this would use actual WebSearch tool in Streamlit)
    for search_item in search_queries:
        try:
            # In actual implementation, this would be:
            # search_results = st.websearch(search_item["query"])
            # 
            # For each result:
            # content = st.webfetch(result["url"], prompt=f"Extract information about {company_name} {search_item['purpose']}")
            
            # For now, simulate search structure
            mock_search_result = {
                "query": search_item["query"],
                "category": search_item["category"],
                "status": "ready_for_websearch",
                "would_search": [
                    f"{company_name} official website/careers page",
                    f"{company_name} engineering blog posts",
                    f"News articles about {company_name}",
                    f"Employee reviews on sites like Glassdoor",
                    f"Technical talks or presentations by {company_name} engineers"
                ],
                "analysis_prompt": f"Extract information about {company_name} {search_item['purpose']}"
            }
            
            search_results["searches_performed"].append(mock_search_result)
            
        except Exception as e:
            print(f"Search failed for {search_item['query']}: {e}")
            continue
    
    return search_results

def extract_company_insights_from_search_results(search_results: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Process search results to extract actionable company insights
    """
    
    insights = {
        "culture_insights": [],
        "tech_insights": [],
        "scale_insights": [], 
        "hiring_insights": [],
        "positioning_advice": []
    }
    
    company_name = search_results.get("company_name", "")
    
    # Process each search result
    for search in search_results.get("searches_performed", []):
        category = search.get("category", "")
        
        if category == "culture":
            insights["culture_insights"].append(f"Research {company_name} culture from official sources")
            insights["positioning_advice"].append("Align language with company values and culture")
            
        elif category == "technology":
            insights["tech_insights"].append(f"Analyze {company_name} tech stack and architecture")
            insights["positioning_advice"].append("Match technical experience with their stack")
            
        elif category == "scale":
            insights["scale_insights"].append(f"Understand {company_name} growth stage and scale")
            insights["positioning_advice"].append("Frame experience at appropriate scale level")
            
        elif category == "hiring":
            insights["hiring_insights"].append(f"Research {company_name} interview process")
            insights["positioning_advice"].append("Prepare for their specific interview style")
    
    return insights

def format_websearch_results_for_display(search_results: Dict[str, Any]) -> str:
    """
    Format search results for display in Streamlit UI
    """
    
    company_name = search_results.get("company_name", "Unknown Company")
    
    display_text = f"# 🔍 Web Research Plan for {company_name}\n\n"
    
    searches = search_results.get("searches_performed", [])
    
    if searches:
        display_text += f"**Prepared {len(searches)} targeted searches:**\n\n"
        
        for i, search in enumerate(searches, 1):
            display_text += f"## {i}. {search['category'].title()} Research\n"
            display_text += f"**Query:** {search['query']}\n\n"
            display_text += f"**Purpose:** {search.get('analysis_prompt', 'General research')}\n\n"
            
            if search.get('would_search'):
                display_text += "**Sources to analyze:**\n"
                for source in search['would_search']:
                    display_text += f"• {source}\n"
                display_text += "\n"
    
    else:
        display_text += "No searches configured.\n\n"
    
    display_text += "---\n"
    display_text += "💡 **Note:** This shows the research plan. Actual WebSearch integration would fetch live data from these sources.\n"
    
    return display_text