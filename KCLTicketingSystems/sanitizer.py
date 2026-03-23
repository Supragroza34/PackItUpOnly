"""
HTML sanitization for ticket additional_details field.
Only allows: bold, italic, lists (ordered/unordered), indentation.
"""

import bleach

# Allowed HTML tags for rich-text formatting
ALLOWED_TAGS = [
    'b', 'strong',      # bold
    'i', 'em',          # italic
    'ol', 'ul', 'li',   # lists
    'br',               # line breaks
    'div', 'p',         # block structure
]

# Allowed attributes - data-indent for indentation tracking
ALLOWED_ATTRIBUTES = {
    'div': ['data-indent'],
    'p': ['data-indent'],
}


def sanitize_additional_details(html_content):
    """
    Sanitize HTML content to only allow bold, italic, lists, and indentation.
    
    Args:
        html_content: HTML string from the rich-text editor
        
    Returns:
        Sanitized HTML string with only allowed tags and attributes
    """
    if not html_content:
        return ""
    
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,  # Remove disallowed tags entirely instead of escaping
    )
