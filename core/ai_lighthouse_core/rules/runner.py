import asyncio
from typing import Dict, Any
from bs4 import BeautifulSoup
from .registry import get_all_rules
from .base import Issue


def run_rules_on_html(
    html: str, url: str, headers: Dict[str, str] = None
) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "lxml")
    results = []
    total_impact_score = 0
    impact_map = {
        "low": 1,
        "medium": 3,
        "high": 5,
        "critical": 7,
    }

    async def _run_rule(rule):
        try:
            maybe_awaitable = rule.run(html, url, soup, headers)
            print(f"Running rule {rule.id}...")
            if asyncio.iscoroutine(maybe_awaitable):
                issues = await maybe_awaitable
                print(f"Async rule {rule.id} returned {len(issues)} issues.")
            else:
                issues = maybe_awaitable
        except Exception as e:
            issues = [
                Issue(
                    id=getattr(rule, "id", "unknown"),
                    title=f"Rule error: {getattr(rule,'id', 'unknown')}",
                    description=f"Exception while running rule: {e}",
                    impact="low",
                    recommendation="Check rule implementation and logs.",
                )
            ]

        return rule, issues
      
    async def _run_all():
        from . import crawlability
        
        tasks = [_run_rule(rule) for rule in get_all_rules()]
        print(f"Running {len(tasks)} rules asynchronously...")
        return await asyncio.gather(*tasks)
      
    compledted = asyncio.run(_run_all())
    
    for rule, issues in compledted:
        for issue in issues:
          if isinstance(issue, Issue):
              issue_dict = {
                  "id": issue.id,
                  "title": issue.title,
                  "description": issue.description,
                  "impact": str(issue.impact),
                  "selector": issue.selector,
                  "recommendation": issue.recommendation,
                  "auto_fix": issue.auto_fix,
                  "data": issue.data,
              }
          else:
              issue_dict = issue  # assume it's already a dict
          
          results.append(issue_dict)
          total_impact_score += impact_map.get(str(issue.impact).lower(), 1)
          
    max_possible = len(get_all_rules()) * 7
    normalized = 100
    if max_possible > 0:
      normalized = max(0, min(100, int(100 - (total_impact_score / max_possible) * 100)))

    return {
        "url": url,
        "score": normalized,
        "issues": results,
        "num_issues": len(results),
    }
    
    
if __name__ == "__main__":
    sample_html = "<html><head><title>Test</title></head><body><h1>Hello World</h1></body></html>"
    sample_url = "http://google.com"
    report = run_rules_on_html(sample_html, sample_url)
    import json
    print(json.dumps(report, indent=2))