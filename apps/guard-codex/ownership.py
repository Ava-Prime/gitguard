from pathlib import Path

# Constants for magic numbers
MIN_CODEOWNERS_PARTS = 2
PATTERN_INDEX = 0
OWNERS_START_INDEX = 1
AT_PREFIX_INDEX = 1


def parse_codeowners(text: str) -> list[tuple[str, list[str]]]:
    """
    Parse CODEOWNERS file content into rules.

    Args:
        text: Content of CODEOWNERS file

    Returns:
        List of tuples containing (pattern, list_of_owners)
    """
    rules = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) >= MIN_CODEOWNERS_PARTS:
            pattern = parts[PATTERN_INDEX]
            owners = parts[OWNERS_START_INDEX:]
            rules.append((pattern, owners))
    return rules


def owner_for(path: str, rules: list[tuple[str, list[str]]]) -> tuple[str, list[str]] | None:
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
        return handle[AT_PREFIX_INDEX:]
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
