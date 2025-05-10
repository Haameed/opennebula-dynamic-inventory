import re

def sanitize_name(name, rule_set):
    """Sanitize a name (VM or label) using the provided rule set."""
    if not name or not rule_set:
        return None
    prefix = rule_set.get('prefix', '')
    result = name
    for rule in rule_set.get('name_rules', []):
        pattern = rule.get('pattern', '')
        replacement = rule.get('replacement', '')
        result = re.sub(pattern, replacement, result)
    return f"{prefix}{result}" if result else None

def sanitize_attribute(value, rule_set):
    """Sanitize an attribute value using the provided rule set."""
    if not value or not rule_set:
        return None
    prefix = rule_set.get('prefix', '')
    result = value
    for rule in rule_set.get('value_rules', []):
        pattern = rule.get('pattern', '')
        replacement = rule.get('replacement', '')
        result = re.sub(pattern, replacement, result)
    return f"{prefix}{result}" if result else None