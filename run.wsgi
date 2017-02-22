import sys, logging

sys.path.insert(0, '/var/www/dependencywatcher')
logging.basicConfig(stream=sys.stderr)

from dependencywatcher.website.webapp import app as application

