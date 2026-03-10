"""Token counting utilities for message content."""


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using improved word-based method.
    More accurate than simple word count by accounting for:
    - Punctuation and special characters
    - Common tokenization patterns
    - Average token-to-word ratio (~0.75 for English)
    
    Args:
        text: The text content to estimate tokens for
        
    Returns:
        Estimated token count as integer
    """
    if not text:
        return 0
    
    # Split by whitespace
    words = text.split()
    word_count = len(words)
    
    # Count characters (tokens often correlate with character count)
    char_count = len(text)
    
    # Estimate: average of word-based and character-based estimates
    # Typical: ~4 chars per token, ~1.3 words per token
    char_estimate = char_count / 4
    word_estimate = word_count * 1.3
    
    # Use the higher estimate (more conservative)
    return int(max(char_estimate, word_estimate))


def estimate_tokens_for_messages(messages: list) -> int:
    """
    Estimate total tokens for a list of messages.
    
    Args:
        messages: List of message dicts with 'content' key
        
    Returns:
        Total estimated token count
    """
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
    return total

