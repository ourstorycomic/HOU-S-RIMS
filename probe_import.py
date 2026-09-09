import importlib
m = importlib.import_module('API.routes.submissions')
print('MODULE:', m)
print('FILE:', getattr(m, '__file__', None))
print('HAS:', hasattr(m, 'submissions_bp'))
print('ATTR:', getattr(m, 'submissions_bp', None))
