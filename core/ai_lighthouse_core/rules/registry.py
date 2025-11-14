from typing import Dict, Type
from .base import BaseRule

_RULES: Dict[str, Type[BaseRule]] = {}

def register(rule_cls: Type[BaseRule]):
  _RULES[rule_cls.id] = rule_cls
  return rule_cls
  
def get_all_rules() -> Dict[str, Type[BaseRule]]:
  return [cls() for cls in _RULES.values()]

def get_rule_by_id(rule_id: str) -> Type[BaseRule]:
  cls = _RULES.get(rule_id)
  return cls() if cls else None