from yarl import URL


def normalize_url(url: str) -> str:
    """Normalizes a URL string by applying consistent formatting rules.

    This function processes the URL to ensure uniformity by:
    - Stripping the 'www.' prefix from the host.
    - Upgrading the 'http' scheme to 'https'.
    - Removing trailing slashes from the path (defaulting to '/' if empty).
    - Sorting query parameters alphabetically.
    - Removing any URL fragment.

    Args:
        url (str): The raw URL string to be normalized.

    Returns:
        str: The normalized URL string.
    """

    u = URL(url)
    
    host = u.host.lstrip('www.') if u.host else ''
    scheme = 'https' if u.scheme == 'http' else u.scheme
    
    normalized = u.with_scheme(scheme).with_host(host)
    
    path = normalized.path.rstrip('/') or '/'
    normalized = normalized.with_path(path)
    
    query_parts = sorted(u.query.items())
    normalized = normalized.with_query(query_parts)
    
    return str(normalized.with_fragment(None))