from django.http import HttpResponse

def index(request):
    return HttpResponse("MemorySim backend is running.")