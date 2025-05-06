import os
import markdown
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe

# Define a hardcoded mapping of documentation files and their paths
DOCUMENTATION_FILES = {
    'installation': os.path.join(settings.BASE_DIR, 'docs', 'installation.md'),
    'user_guide': os.path.join(settings.BASE_DIR, 'docs', 'user_guide.md'),
    'troubleshooting': os.path.join(settings.BASE_DIR, 'docs', 'troubleshooting.md'),
    'docker_setup': os.path.join(settings.BASE_DIR, 'docs', 'docker_setup.md'),
    'bnf_compliance_improvements': os.path.join(settings.BASE_DIR, 'docs', 'bnf_compliance_improvements.md'),
    'README': os.path.join(settings.BASE_DIR, 'docs', 'README.md')
}

def get_markdown_content(doc_key):
    """
    Read and convert a Markdown file to HTML using a hardcoded lookup
    """
    if doc_key not in DOCUMENTATION_FILES:
        return None
        
    filepath = DOCUMENTATION_FILES[doc_key]
    
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

def render_doc_page(request, doc_key, title=None):
    """Helper function to render a documentation page"""
    content = get_markdown_content(doc_key)
    
    if content is None:
        raise Http404("Documentation page not found")
    
    context = {
        'title': title or doc_key.replace('_', ' ').title(),
        'content': content
    }
    return render(request, 'docs/markdown_page.html', context)

# Individual view functions for each documentation page
def docs_installation(request):
    return render_doc_page(request, 'installation', 'Installation Guide')

def docs_user_guide(request):
    return render_doc_page(request, 'user_guide', 'User Guide')

def docs_troubleshooting(request):
    return render_doc_page(request, 'troubleshooting', 'Troubleshooting')

def docs_docker_setup(request):
    return render_doc_page(request, 'docker_setup', 'Docker Setup Guide')

def docs_bnf_compliance(request):
    return render_doc_page(request, 'bnf_compliance_improvements', 'BnF Compliance Improvements')

def docs_readme(request):
    return render_doc_page(request, 'README', 'Documentation Home')

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