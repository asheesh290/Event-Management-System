# ems_project/views.py
from django.shortcuts import render

def api_overview(request):
    """
    Renders the assignment overview used at /api/
    """
    return render(request, 'overview.html')
