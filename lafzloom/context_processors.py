from lafzloom.jinja2 import csrf_input as csrf_input_func


def csrf_input(request):
    return {'csrf_input': csrf_input_func(request)}
