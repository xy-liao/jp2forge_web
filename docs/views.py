import os
import re
import markdown
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_GET

# Define a hardcoded mapping of documentation files and their paths
DOCUMENTATION_FILES = {
    'installation': os.path.join(settings.BASE_DIR, 'docs', 'installation.md'),
    'user_guide': os.path.join(settings.BASE_DIR, 'docs', 'user_guide.md'),
    'troubleshooting': os.path.join(settings.BASE_DIR, 'docs', 'troubleshooting.md'),
    'docker_setup': os.path.join(settings.BASE_DIR, 'docs', 'docker_setup.md'),
    'README': os.path.join(settings.BASE_DIR, 'docs', 'README.md')
}

def extract_headings(markdown_text):
    """
    Extract headings from markdown text to create a hierarchical table of contents
    """
    toc_items = []
    # Match headings (##, ###, etc.) - we're interested in h2 (##), h3 (###), and h4 (####)
    # Use a more efficient regex that avoids catastrophic backtracking
    pattern = r'^(#{2,4})\s+(.+)$'
    
    for line in markdown_text.split('\n'):
        match = re.match(pattern, line)
        if match:
            level = len(match.group(1))  # Number of # symbols
            title = match.group(2).strip()
            # Create a valid ID from the title (lowercase, replace spaces with hyphens)
            heading_id = title.lower().replace(' ', '-').replace(':', '').replace('.', '')
            heading_id = re.sub(r'[^\w-]', '', heading_id)
            
            # Only include h2, h3, and h4 headings (levels 2, 3, and 4)
            if 2 <= level <= 4:
                toc_items.append({
                    'level': level,
                    'title': title,
                    'id': heading_id
                })
    
    return toc_items

def get_markdown_content(doc_key):
    """
    Read and convert a Markdown file to HTML using a hardcoded lookup
    """
    if doc_key not in DOCUMENTATION_FILES:
        return None, None
        
    filepath = DOCUMENTATION_FILES[doc_key]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract headings for TOC before converting to HTML
        toc_items = extract_headings(content)
        
        # Convert Markdown to HTML using Python-Markdown
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'toc', 'fenced_code', 'codehilite']
        )
        
        # Add id attributes to heading tags for TOC links
        for item in toc_items:
            heading_level = item['level']
            heading_tag = f'<h{heading_level}>'
            heading_with_id = f'<h{heading_level} id="{item["id"]}">'
            html_content = html_content.replace(
                heading_tag + item['title'],
                heading_with_id + item['title'],
                1  # Replace only the first occurrence
            )
        
        return mark_safe(html_content), toc_items
    except FileNotFoundError:
        return None, None

def render_doc_page(request, doc_key, title=None):
    """Helper function to render a documentation page"""
    content, toc_items = get_markdown_content(doc_key)
    
    if content is None:
        raise Http404("Documentation page not found")
    
    context = {
        'title': title or doc_key.replace('_', ' ').title(),
        'content': content,
        'toc_items': toc_items,
        'page_name': doc_key.lower()  # Used to highlight active nav item
    }
    return render(request, 'docs/markdown_page.html', context)

# Individual view functions for each documentation page
@require_GET
def docs_installation(request):
    return render_doc_page(request, 'installation', 'Installation Guide')

@require_GET
def docs_user_guide(request):
    return render_doc_page(request, 'user_guide', 'User Guide')

@require_GET
def docs_troubleshooting(request):
    return render_doc_page(request, 'troubleshooting', 'Troubleshooting')

@require_GET
def docs_docker_setup(request):
    return render_doc_page(request, 'docker_setup', 'Docker Setup Guide')

@require_GET
def docs_readme(request):
    return render_doc_page(request, 'README', 'Documentation Home')

# Generic view function for viewing any documentation by its key
@require_GET
def view_documentation(request, doc_key):
    """
    Generic view function to render any documentation page by its key
    This provides compatibility between the static HTML templates
    and the dynamic Markdown-based documentation system.
    """
    # Format the title nicely by replacing underscores with spaces and capitalizing
    title = doc_key.replace('_', ' ').title()
    return render_doc_page(request, doc_key, title)

@require_GET
def docs_index(request):
    """
    Documentation index page
    """
    docs_files = []
    
    # List all available documentation based on our hardcoded mapping
    for doc_id, filepath in DOCUMENTATION_FILES.items():
        if os.path.isfile(filepath):
            title = doc_id.replace('_', ' ').title()
            docs_files.append({
                'name': doc_id,
                'title': title
            })
    
    context = {
        'title': 'Documentation',
        'docs_files': docs_files
    }
    return render(request, 'docs/index.html', context)