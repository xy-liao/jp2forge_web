import os
import markdown
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe

def get_markdown_content(filename):
    """
    Read and convert a Markdown file to HTML
    """
    docs_dir = os.path.join(settings.BASE_DIR, 'docs')
    filepath = os.path.join(docs_dir, f"{filename}.md")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Convert Markdown to HTML using Python-Markdown
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'toc', 'fenced_code', 'codehilite']
        )
        return mark_safe(html_content)
    except FileNotFoundError:
        return None

def docs_view(request, doc_name):
    """
    View to render a Markdown documentation file
    """
    content = get_markdown_content(doc_name)
    
    if content is None:
        raise Http404("Documentation page not found")
    
    context = {
        'title': doc_name.replace('_', ' ').title(),
        'content': content
    }
    return render(request, 'docs/markdown_page.html', context)

def docs_index(request):
    """
    Documentation index page
    """
    # Get all available documentation files
    docs_dir = os.path.join(settings.BASE_DIR, 'docs')
    docs_files = []
    
    for file in os.listdir(docs_dir):
        if file.endswith('.md') and not file.startswith('.'):
            name = file[:-3]
            title = name.replace('_', ' ').title()
            docs_files.append({
                'name': name,
                'title': title
            })
    
    context = {
        'title': 'Documentation',
        'docs_files': docs_files
    }
    return render(request, 'docs/index.html', context)