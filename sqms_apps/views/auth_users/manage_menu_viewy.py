from django.shortcuts import render, redirect
from ...models import Menu
from ...forms.forms_permission_menu import MenuForm
from django.contrib import messages

def manage_menu(request):
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu created/updated successfully.")
            return redirect('manage_menu')
    else:
        form = MenuForm()
    
    menus = Menu.objects.all()
    return render(request, 'manage_menu.html', {'form': form, 'menus': menus})
