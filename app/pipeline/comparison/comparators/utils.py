from rapidfuzz import fuzz

def compare_strings(s1: str, s2: str, algorithm: str) -> int:
    """
    Returns an integer score from 0 to 100 based on the algorithm.
    """
    if not s1 or not s2:
        return 0
        
    s1 = s1.strip().lower()
    s2 = s2.strip().lower()
    
    if algorithm == "exact":
        return 100 if s1 == s2 else 0
    elif algorithm == "rapidfuzz_ratio":
        # RapidFuzz returns 0-100 float, we cast to int
        return int(fuzz.ratio(s1, s2))
    elif algorithm == "rapidfuzz_partial":
        return int(fuzz.partial_ratio(s1, s2))
    elif algorithm == "rapidfuzz_token_sort":
        return int(fuzz.token_sort_ratio(s1, s2))
    else:
        # Default to exact if unknown
        return 100 if s1 == s2 else 0
