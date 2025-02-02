from django.shortcuts import render
from django.http import Http404

# Custom 404 view
def custom_404(request, exception):
    return render(request, '404.html', status=404)