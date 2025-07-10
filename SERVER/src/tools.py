from langchain_tavily import TavilySearch
from langchain.agents import tool
import datetime

class ToolKit:

    @tool
    def search(query: str) -> list[str]:
        """
        Search the internet for real-time information.

        This tool is useful for retrieving up-to-date content such as:
        - Breaking news headlines
        - Current weather conditions
        - Live stock market data
        - Sports scores and updates
        - Other time-sensitive information

        Args:
            query (str): The search query string describing what to look up.
        """
        tavily_obj = TavilySearch(max_results=4)
        res = tavily_obj.invoke(query)
        return res
    
    @tool
    def get_current_date_time(format: str = "%Y-%m-%d %H:%M%S") -> str:
        """Return the current date and time in the specified format"""
        curr_time = datetime.datetime.now()
        formatted_time = curr_time.strftime(format)
        return formatted_time