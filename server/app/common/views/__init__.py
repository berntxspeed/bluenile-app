def is_json(request):
    content_type = request.headers.get('Content-Type')
    return content_type == 'application/json'
    
