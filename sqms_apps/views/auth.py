from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

allowed_groups = ['superadmin', 'admin-mgoqa', 'user-mgoqa', 'data-control','admin-mining',
                  'admin-hauling','admin-survey','admin-ot',
                  'manager-mgoqa','superintendent-mgoqa','manager-mining','superintendent-mining'
                  ]
dashboard_redirects = {
    'superadmin'    : 'index-mgoqa',
    'admin-mgoqa'   : 'index-mgoqa',
    'user-mgoqa'    : 'index-mgoqa',
    'data-control'  : 'index-mgoqa',
    'admin-mining'  : 'index-mining',
    'admin-hauling' : 'index-mining',
    'admin-ot'      : 'index-selling',
}

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password, using='sqms_db')
        print(f"Authenticated user: {user}")
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Get user's groups and determine the appropriate redirect
                user_groups = user.groups.values_list('name', flat=True)  # Get group names
                for group in user_groups:
                    if group in allowed_groups:
                        redirect_url = dashboard_redirects.get(group, 'index-mgoqa')
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'success': True, 'redirect_url': redirect_url})
                        return redirect(redirect_url)
                
                # Fallback if no group match
                error_message = 'User does not belong to any allowed group.'
            else:
                error_message = 'User account is disabled.'
        else:
            error_message = 'Invalid username or password.'

        # Return error message for Ajax or regular requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})
        else:
            return render(request, 'auth/pages-auth.html', {'error_message': error_message})
    else:
        return render(request, 'auth/pages-auth.html')
    
# def login_view(request):
#     if request.method == 'POST':
#         username = request.POST.get('username')
#         password = request.POST.get('password')
        
#         user = authenticate(request, username=username, password=password, using='sqms_db')
        
#         print(f"Authenticated user: {user}")
        
#         if user is not None:
#             if user.is_active:
#                 login(request, user)
#                 if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#                     return JsonResponse({'success': True, 'message': 'Login successful'})
#                 return redirect('index-mgoqa')
#             else:
#                 error_message = 'User account is disabled.'
#         else:
#             error_message = 'Invalid username or password.'

#         if request.headers.get('x-requested-with') == 'XMLHttpRequest':
#             return JsonResponse({'success': False, 'message': error_message})
#         else:
#             return render(request, 'auth/pages-auth.html', {'error_message': error_message})
#     else:
#         return render(request, 'auth/pages-auth.html')
