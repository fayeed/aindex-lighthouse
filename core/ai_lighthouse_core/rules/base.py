from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List, Union


class Impact(Enum):
  """Enumeration for issue impact severity."""
  HIGH = "high"
  MEDIUM = "medium"
  LOW = "low"
  CRITICAL = "critical"

  def __str__(self) -> str:
    return self.value

@dataclass
class Issue:
  id: str
  title: str
  description: str
  impact: Union[Impact, str] = Impact.LOW  # prefer `Impact`, accepts legacy strings
  selector: Optional[str] = None
  recommendation: Optional[str] = None
  auto_fix: Optional[Dict[str, Any]] = None # optional snippet or instructions for auto-fixing
  data: Optional[Dict[str, Any]] = None # additional data related to the issue
  
class BaseRule:
  """
    Minimal rule contract for AI Lighthouse rules.
    Implement `run(html: str, url: str, soup: BeautifulSoup) -> List[Issue]` in subclasses.
  """
  id: str = "base-rule"
  title: str = "Base Rule"
  impact: Impact = Impact.LOW
  tags: List[str] = []
  
  def run(self, html: str, url: str, soup, headers: Dict[str, str] = None) -> List[Issue]:
    """
      Run the rule against the provided HTML content and return a list of issues found.
      
      Args:
        html (str): The raw HTML content of the page.
        url (str): The URL of the page being analyzed.
        soup (BeautifulSoup): Parsed HTML content using BeautifulSoup.
      Returns:
        List[Issue]: A list of issues found by this rule.
    """
    
    raise NotImplementedError("Subclasses must implement the run method.")
  
