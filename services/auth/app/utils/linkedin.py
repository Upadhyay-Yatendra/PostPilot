import re

def extract_linkedin_username(url: str) -> str:
    """
    Extracts the LinkedIn username from a profile URL.
    Example:
        https://www.linkedin.com/in/yatendra-upadhyay/ -> yatendra-upadhyay
    """
    match = re.search(r"linkedin\.com/in/([^/]+)/?", url)
    if not match:
        raise ValueError("Invalid LinkedIn URL format")
    return match.group(1)
