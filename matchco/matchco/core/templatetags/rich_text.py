from html import escape
from html.parser import HTMLParser
import re
from urllib.parse import urlparse

from django import template
from django.utils.safestring import mark_safe


register = template.Library()


class _RichTextSanitizer(HTMLParser):
    """Small allow-list sanitizer for HTML authored in the rich-text editor."""

    TAGS = {
        'a', 'blockquote', 'br', 'caption', 'code', 'col', 'colgroup', 'div', 'em',
        'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'iframe',
        'img', 'li', 'ol', 'p', 'pre', 's', 'source', 'span', 'strong', 'sub', 'sup',
        'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'u', 'ul', 'video',
    }
    ATTRIBUTES = {
        'a': {'href', 'title', 'target', 'rel'},
        'col': {'span'},
        'colgroup': {'span'},
        'div': {'class', 'style'},
        'figure': {'class'},
        'iframe': {'class', 'src', 'title', 'width', 'height', 'frameborder', 'allow', 'allowfullscreen'},
        'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
        'li': {'data-list'},
        'ol': {'class'},
        'p': {'class', 'style'},
        'pre': {'class'},
        'source': {'src', 'type'},
        'span': {'class', 'style'},
        'strong': {'style'},
        'em': {'style'},
        's': {'style'},
        'u': {'style'},
        'table': {'class', 'style'},
        'td': {'colspan', 'rowspan'},
        'th': {'colspan', 'rowspan', 'scope'},
        'ul': {'class'},
        'video': {'src', 'poster', 'width', 'height', 'controls', 'preload'},
    }
    VOID_TAGS = {'br', 'hr', 'col', 'source', 'img'}
    SKIP_TAGS = {'script', 'style', 'object', 'embed'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.skip_depth = 0
        self.tag_stack = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.skip_depth:
            if tag in self.SKIP_TAGS:
                self.skip_depth += 1
            return
        if tag in self.SKIP_TAGS:
            self.skip_depth = 1
            return
        if tag not in self.TAGS:
            return
        safe_attrs = []
        for name, value in attrs:
            name = name.lower()
            if name not in self.ATTRIBUTES.get(tag, set()) or value is None:
                continue
            if tag == 'li' and name == 'data-list' and value not in {'bullet', 'ordered'}:
                continue
            if name == 'class':
                allowed_classes = {
                    'ql-align-center', 'ql-align-right', 'ql-align-justify',
                    'ql-font-serif', 'ql-font-monospace',
                    'ql-size-small', 'ql-size-large', 'ql-size-huge',
                    'ql-syntax', 'ql-video',
                }
                classes = [item for item in value.split() if item in allowed_classes]
                if not classes:
                    continue
                value = ' '.join(classes)
            if name == 'style':
                safe_styles = []
                for declaration in value.split(';'):
                    if ':' not in declaration:
                        continue
                    property_name, property_value = [part.strip().lower() for part in declaration.split(':', 1)]
                    if property_name not in {'color', 'background-color', 'text-align', 'font-family', 'font-size'}:
                        continue
                    if property_name in {'color', 'background-color'}:
                        valid_value = re.fullmatch(r'(?:#[0-9a-f]{3,8}|rgba?\([0-9\s,.%]+\)|[a-z]+)', property_value)
                    elif property_name == 'text-align':
                        valid_value = property_value in {'left', 'center', 'right', 'justify'}
                    elif property_name == 'font-family':
                        valid_value = re.fullmatch(r'[a-z0-9 ,"\'-]+', property_value)
                    else:
                        valid_value = re.fullmatch(r'[0-9.]+(?:px|pt|em|rem|%|vh|vw)', property_value)
                    if not valid_value:
                        continue
                    safe_styles.append(f'{property_name}: {property_value}')
                if not safe_styles:
                    continue
                value = '; '.join(safe_styles)
            if name == 'href':
                parsed = urlparse(value.strip())
                if parsed.scheme and parsed.scheme not in {'http', 'https', 'mailto'}:
                    continue
            if tag in {'img', 'source', 'video'} and name in {'src', 'poster'}:
                parsed = urlparse(value.strip())
                if parsed.scheme not in {'http', 'https'}:
                    continue
            if tag == 'iframe' and name == 'src':
                parsed = urlparse(value.strip())
                if parsed.scheme not in {'http', 'https'} or parsed.netloc.lower() not in {
                    'www.youtube.com', 'youtube.com', 'www.youtube-nocookie.com',
                    'player.vimeo.com', 'vimeo.com',
                }:
                    continue
            if name == 'allowfullscreen':
                value = 'allowfullscreen'
            safe_attrs.append(f' {name}="{escape(value, quote=True)}"')
        self.output.append(f'<{tag}{"".join(safe_attrs)}>')
        if tag not in self.VOID_TAGS:
            self.tag_stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.skip_depth:
            if tag in self.SKIP_TAGS:
                self.skip_depth -= 1
            return
        if tag in self.TAGS and tag not in self.VOID_TAGS:
            self.output.append(f'</{tag}>')
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.tag_stack.pop()

    def handle_data(self, data):
        if not self.skip_depth:
            data = data.replace('\r\n', '\n').replace('\r', '\n')
            if self.tag_stack and self.tag_stack[-1] not in {'pre', 'code'}:
                self.output.append(escape(data).replace('\n', '<br>'))
            else:
                self.output.append(escape(data))


@register.filter(is_safe=True)
def rich_text(value):
    """Render editor HTML safely while preserving plain text content."""
    if value is None:
        return ''
    parser = _RichTextSanitizer()
    parser.feed(str(value))
    parser.close()
    return mark_safe(''.join(parser.output))
