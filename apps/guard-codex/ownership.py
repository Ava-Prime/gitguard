from pathlib import Path
from typing import List, Tuple, Optional

def parse_codeowners(text: str) -> List[Tuple[str, List[str]]]:
    """
    Parse CODEOWNERS file content into rules.
    
    Args:
        text: Content of CODEOWNERS file
        
    Returns:
        List of tuples containing (pattern, list_of_owners)
    """
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            pattern = parts[0]
            owners = parts[1:]
            rules.append((pattern, owners))
    return rules

def owner_for(path: str, rules: List[Tuple[str, List[str]]]) -> Optional[Tuple[str, List[str]]]:
    """
    Find the best matching owner rule for a given path.
    
    Args:
        path: File path to check
        rules: List of CODEOWNERS rules
        
    Returns:
        Tuple of (pattern, owners) for the best match, or None if no match
    """
    best = None
    for pattern, handles in rules:
        # Convert CODEOWNERS pattern to pathlib-compatible pattern
        # Replace ** with * for pathlib matching
        pathlib_pattern = pattern.replace("**", "*")
        
        try:
            if Path(path).match(pathlib_pattern):
                best = (pattern, handles)
        except ValueError:
            # Handle invalid patterns gracefully
            continue
    
    return best

def normalize_owner_handle(handle: str) -> str:
    """
    Normalize owner handle for consistent storage.
    
    Args:
        handle: Raw owner handle from CODEOWNERS
        
    Returns:
        Normalized handle
    """
    # Remove @ prefix if present for consistency
    if handle.startswith("@"):
        return handle[1:]
    return handle

def get_owner_type(handle: str) -> str:
    """
    Determine if owner is a team or individual user.
    
    Args:
        handle: Owner handle
        
    Returns:
        "team" if handle contains "/", "user" otherwise
    """
    normalized = normalize_owner_handle(handle)
    return "team" if "/" in normalized else "user"