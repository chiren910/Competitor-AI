import re

def markdown_to_plaintext(markdown_text):
    """
    Convert markdown text to plain text while:
    1. Preserving structure (headings, lists, paragraphs)
    2. Removing all URLs and links completely
    3. Cleaning up artifacts and malformed markdown
    """
    if not markdown_text:
        return ""

    markdown_text = clean_repeated_patterns(markdown_text)

    segments = re.split(r'(```[\s\S]*?```)', markdown_text)
    processed_segments = []

    for i, segment in enumerate(segments):
        if i % 2 == 1 and segment.startswith('```'):
            lines = segment.split('\n')
            if len(lines) > 1:
                code_content = '\n'.join(lines[1:-1]) if len(lines) > 2 else ""
                processed_segments.append(f"\n\n{code_content}\n\n")
            else:
                processed_segments.append(segment.replace('```', '').strip())
        else:
            processed_segments.append(process_normal_text(segment))

    plain_text = ''.join(processed_segments)
    plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)
    plain_text = remove_all_urls(plain_text)
    plain_text = post_process_cleanup(plain_text)

    return plain_text.strip()


def remove_all_urls(text):
    text = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', text)
    text = re.sub(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)', '', text)
    text = re.sub(r'<https?:\/\/[^>]+>', '', text)
    text = re.sub(r'\S+@\S+', '', text)
    return text


def clean_repeated_patterns(text):
    """Efficient repeated pattern cleaner for large markdown"""
    if not text:
        return ""

    lines = text.split('\n')
    clean_lines = []
    pattern_counts = {}

    # Count pattern occurrences
    for line in lines:
        stripped = line.strip()
        if len(stripped) > 5:
            pattern_key = simplify_for_pattern_matching(stripped)
            pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1

    repeating_patterns = {k for k, v in pattern_counts.items() if v >= 3}
    seen_patterns = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            clean_lines.append('')
            continue

        pattern_key = simplify_for_pattern_matching(stripped)
        if pattern_key in repeating_patterns:
            if pattern_key not in seen_patterns:
                clean_lines.append(stripped)
                seen_patterns.add(pattern_key)
        else:
            clean_lines.append(stripped)

    return '\n'.join(clean_lines)


def simplify_for_pattern_matching(text):
    if not text:
        return ""

    simplified = re.sub(r'\d+', '', text)
    simplified = re.sub(r'[^\w\s]', '', simplified)
    simplified = simplified.lower()
    simplified = re.sub(r'\s+', ' ', simplified).strip()
    return simplified[:20] if len(simplified) > 20 else simplified


def process_normal_text(text):
    if not text:
        return ""

    lines = []
    for line in text.split('\n'):
        header_match = re.match(r'^(#{1,6})\s+(.+)', line)
        if header_match:
            header_text = header_match.group(2).strip()
            lines.append(f"{header_text}")
            lines.append("")
            continue

        line = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', line)
        line = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', line)
        line = re.sub(r'`(.*?)`', r'\1', line)
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        line = re.sub(r'__(.*?)__', r'\1', line)
        line = re.sub(r'\*(.*?)\*', r'\1', line)
        line = re.sub(r'_(.*?)_', r'\1', line)

        if re.match(r'^(\s*)[-*+](\s+)', line):
            line = re.sub(r'^(\s*)[-*+](\s+)', r'\1- ', line)
        elif re.match(r'^(\s*)\d+\.(\s+)', line):
            line = re.sub(r'^(\s*)\d+\.(\s+)', r'\1- ', line)

        line = re.sub(r'^>\s*', '', line)

        if re.match(r'^[\s\|]*[-]{2,}[\s\|]*$', line):
            continue

        if line.strip():
            lines.append(line)

    return '\n'.join(lines)


def post_process_cleanup(text):
    if not text:
        return ""

    text = remove_all_urls(text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text
