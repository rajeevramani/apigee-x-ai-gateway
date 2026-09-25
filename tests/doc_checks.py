"""Small stdlib-only checks for this repository's Markdown conventions.

Not a general Markdown/YAML parser, Apigee validator or semantic reviewer.
Anchor rules live in heading_anchors; link syntax lives in markdown_links.
"""
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


def check_examples(root, expected):
    """Return asset-relative path -> XML, independent of reference host file."""
    found = {}
    for doc in sorted((root / 'references').rglob('*.md')):
        text = doc.read_text(encoding='utf-8')
        pattern = re.compile(
            r'^Example source: `([^`\n]+)`\n\s*\n```xml\n(.*?)\n```[ \t]*(?=\n|$)',
            re.M | re.S)
        matches = list(pattern.finditer(text))
        starts = {match.start() for match in matches}
        markers = {match.start() for match in re.finditer(r'Example\s+source\b', text, re.I)}
        if markers != starts:
            raise AssertionError(f'malformed Example source marker: {doc}')
        for match in matches:
            source, snippet = match.groups()
            asset = (doc.parent / source).resolve()
            if not asset.is_relative_to((root / 'assets/examples').resolve()):
                raise AssertionError(f'example outside assets/examples: {doc}: {source}')
            name = asset.relative_to(root.resolve()).as_posix()
            if name in found:
                raise AssertionError(f'duplicate example: {doc}: {name}')
            if not asset.is_file():
                raise AssertionError(f'missing asset: {doc}: {name}')
            if snippet.strip() != asset.read_text(encoding='utf-8').strip():
                raise AssertionError(f'mismatched snippet: {doc}: {name}')
            found[name] = snippet
    missing, extra = set(expected) - found.keys(), found.keys() - set(expected)
    if missing or extra:
        raise AssertionError(f'example coverage: missing={sorted(missing)}, extra={sorted(extra)}')
    return found


def markdown_documents(root):
    # Explicit public roots only; never traverse .env or hidden trees.
    return [*(root / name for name in ('SKILL.md', 'README.md')),
            *([root / name for name in ('CHANGELOG.md', 'EVALUATION.md') if (root / name).exists()]),
            *sorted((root / 'labs').rglob('*.md')),
            *sorted((root / 'references').rglob('*.md'))]


def without_fences(text):
    lines, fence = [], None
    for line in text.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            lines.append('')
        elif marker:
            fence = marker[1]
            lines.append('')
        else:
            lines.append(line)
    if fence:
        raise AssertionError('unclosed Markdown fence')
    return '\n'.join(lines)


def heading_anchors(text):
    import html
    import unicodedata
    text = without_fences(text)
    explicit = re.findall(r'<(?:a|[a-z][a-z0-9]*)\b[^>]*?\b(?:id|name)=[\"\']([^\"\']+)[\"\']', text, re.I)
    if len(explicit) != len(set(explicit)):
        raise AssertionError('duplicate explicit anchor')
    used = set(explicit)
    for heading in re.findall(r'^ {0,3}#{1,6}\s+(.+?)\s*$', text, re.M):
        heading = re.sub(r'\s+#+\s*$', '', heading)
        heading = re.sub(r'!?\[([^\]]+)\]\([^)]*\)', r'\1', heading)
        heading = re.sub(r'\[([^\]]+)\]\[[^\]]*\]', r'\1', heading)
        heading = re.sub(r'<[^>]+>', '', heading)
        heading = html.unescape(heading).lower()
        # Code-span underscores are literal, not emphasis delimiters.
        heading = ''.join(
            part.strip('`') if part.startswith('`') else
            re.sub(r'(?<!\w)(_+)(.+?)\1(?!\w)', r'\2', part).replace('*', '').replace('~', '')
            for part in re.split(r'(`+[^`]*`+)', heading))
        base = ''.join(c for c in heading if c in '-_' or c.isspace() or
                       unicodedata.category(c)[0] in 'LNM').replace(' ', '-')
        slug, index = base, 0
        while slug in used:
            index += 1
            slug = f'{base}-{index}'
        used.add(slug)
    return used


def markdown_links(text):
    """Inline/image links and reference definitions; ignore code examples.

    Checking every definition also covers collapsed/shortcut references. Full
    undefined references fail; lone [1] citations without definitions are prose.
    Supports angle destinations, optional titles and one nested parenthesis pair.
    """
    text = without_fences(text)
    definitions = {}
    definition = re.compile(r'^ {0,3}\[([^\]]+)\]:[ \t]*(<[^>]*>|\S+)')
    previous = ''
    for line in text.splitlines():
        match = definition.match(line)
        if match:
            label, destination = match.groups()
            # Repository subset: definition runs start at BOF or after a blank
            # line. CommonMark definitions cannot interrupt a prose paragraph.
            # Check before stripping code spans, which can hide that paragraph.
            if previous.strip() and not definition.match(previous):
                raise AssertionError(f'reference definition needs blank separator: {label}')
            key = ' '.join(label.lower().split())
            if key in definitions:
                raise AssertionError(f'duplicate reference definition: {label}')
            definitions[key] = destination.strip('<>')
        previous = line
    text = re.sub(r'(`+).*?\1', '', text)
    links = list(definitions.values())
    text = re.sub(r'^ {0,3}\[[^\]]+\]:.*$', '', text, flags=re.M)
    inline = re.compile(r'!?\[[^\]\n]*\]\(\s*(<[^>]*>|(?:[^\s()\\]|\\.|\([^()]*\))*)(?:\s+[\"\'][^\n]*?[\"\'])?\s*\)')
    links.extend(match[1].strip('<>') for match in inline.finditer(text))
    text = inline.sub('', text)
    for label, reference in re.findall(r'\[([^\]\n]+)\]\[([^\]\n]*)\]', text):
        key = ' '.join((reference or label).lower().split())
        if key not in definitions:
            if label.isdigit() and reference.isdigit():
                continue  # Adjacent bibliography citations [1][2], not defined links.
            raise AssertionError(f'undefined reference: {reference or label}')
    return links


def check_links(root, documents):
    resolved = set()
    for doc in documents:
        text = doc.read_text(encoding='utf-8')
        heading_anchors(text)  # Also reject duplicate explicit IDs without inbound links.
        for link in markdown_links(text):
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (doc.parent / unquote(parsed.path)).resolve() if parsed.path else doc.resolve()
            if not target.is_relative_to(root.resolve()):
                raise AssertionError(f'link outside public repository: {doc}: {link}')
            relative = target.relative_to(root.resolve())
            if any(part.startswith('.') for part in relative.parts):
                raise AssertionError(f'link to private path: {doc}: {link}')
            if not target.is_file():
                raise AssertionError(f'missing link: {doc}: {link}')
            if parsed.fragment and target.suffix.lower() == '.md':
                if unquote(parsed.fragment) not in heading_anchors(target.read_text(encoding='utf-8')):
                    raise AssertionError(f'broken anchor: {doc}: {link}')
            resolved.add(relative.as_posix())
    return resolved


def frontmatter(text):
    """Parse the existing flat YAML subset, refusing unsupported shapes.

    Keys use [a-z][a-z0-9_-]*. Values are single-line plain/quoted strings or
    inline lists of lowercase alphabetic strings. Quoted escapes/doubled quotes,
    YAML indicators, comments, nested/block shapes and typed scalars are refused.
    No YAML dependency or loader-schema migration is introduced by these tests.
    """

    match = re.match(r'\A---\n(.*?)\n---(?:\n|$)', text, re.S)
    if not match:
        raise AssertionError('missing frontmatter delimiters')
    fields = {}
    for line in match[1].splitlines():
        item = re.fullmatch(r'([a-z][a-z0-9_-]*):[ \t]+(\S(?:.*\S)?)', line)
        if not item or item[1] in fields:
            raise AssertionError(f'invalid or duplicate frontmatter field: {line}')
        key, value = item.groups()
        if value.startswith('[') and value.endswith(']'):
            parts = [part.strip() for part in value[1:-1].split(',')]
            if any(not re.fullmatch(r'''(?:[a-z]+|"[a-z]+"|'[a-z]+')''', part) for part in parts):
                raise AssertionError('invalid frontmatter inline string list')
            value = [part.strip('\"\'') for part in parts]
        elif value.startswith(('\"', "'")):
            if len(value) < 2 or value[-1] != value[0] or value[0] in value[1:-1] or '\\' in value:
                raise AssertionError('invalid quoted frontmatter scalar')
            value = value[1:-1]
        elif (value.lower() in ('true', 'false', 'null', '~', 'yes', 'no', 'on', 'off', '>', '|')
              or value[0] in '{}[]|>!&*%@`#,:?-'
              or re.search(r':(?:\s|$)|\s#', value)
              or value.lower().lstrip('+-') in ('.inf', '.nan')
              or re.fullmatch(r'[-+]?(?:\d[\d_]*(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?', value)
              or re.fullmatch(r'[-+]?0[xXoObB][0-9a-fA-F_]+', value)
              or re.match(r'\d{4}-\d\d-\d\d(?:$|[Tt ])', value)
              or re.fullmatch(r'\d+(?::[0-5]?\d)+(?:\.\d+)?', value)):
            raise AssertionError('unsupported frontmatter scalar')
        fields[key] = value
    return fields


def validate_metadata(fields):
    """Require a valid skill name, a description and a semver version.

    Other flat fields are optional; platforms is checked only when present.
    """
    required = {'name', 'description', 'version'}
    if not required <= fields.keys():
        raise AssertionError('required top-level metadata shape changed')
    for key in required:
        if not isinstance(fields[key], str) or not fields[key].strip():
            raise AssertionError(f'metadata {key} must be a nonempty string')
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', fields['name']):
        raise AssertionError('invalid skill name')
    if not re.fullmatch(r'(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)', fields['version']):
        raise AssertionError('invalid version')
    if 'platforms' in fields:
        platforms = fields['platforms']
        if not isinstance(platforms, list) or not platforms or any(
                p not in {'linux', 'macos', 'windows'} for p in platforms) or len(set(platforms)) != len(platforms):
            raise AssertionError('platforms must be a nonempty unique supported-platform list')
