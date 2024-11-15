import requests
from bs4 import BeautifulSoup
import time
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for
import pandas as pd
from scraper import scrape_yellow_pages  # Import the updated scraper function
import os
from celery_config import make_celery
import ssl

app = Flask(__name__)

# Celery Configuration using Redis URL from environment variable
redis_url = os.getenv('REDIS_URL', 'rediss://red-csrlobggph6c73b8o3tg:GsHXpplWrrF5QTUUN3Dr6HgZOo8bryN5@oregon-redis.render.com:6379')

app.config['CELERY_BROKER_URL'] = redis_url
app.config['CELERY_RESULT_BACKEND'] = redis_url

# Set SSL context for Redis
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Use ssl.CERT_REQUIRED if you have certificates

# Set Celery broker transport options for SSL
app.config['CELERY_BROKER_TRANSPORT_OPTIONS'] = {
    'visibility_timeout': 3600,  # Timeout for unacknowledged messages
    'max_connections': 5,        # Reduce to limit concurrent connections
    'ssl': {
        'ssl_cert_reqs': ssl.CERT_NONE  # Adjust as needed
    }
}

# Configure Redis backend for SSL
app.config['CELERY_REDIS_BACKEND_USE_SSL'] = {
    'ssl_cert_reqs': ssl.CERT_NONE  # Adjust as needed
}

celery = make_celery(app)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get user input from the form
        keyword = request.form.get('keyword')
        location = request.form.get('location')
        max_pages = int(request.form.get('max_pages'))

        # Start background scraping task
        task = scrape_yellow_pages_task.apply_async(args=[keyword, location, max_pages])

        # Redirect to a page where the user can wait for the task completion
        return redirect(url_for('task_status', task_id=task.id))

    return render_template('index.html')

@app.route('/status/<task_id>')
def task_status(task_id):
    task = scrape_yellow_pages_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        # Something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

@celery.task(bind=True)
def scrape_yellow_pages_task(self, keyword, location, max_pages):
    try:
        listings = scrape_yellow_pages(keyword, location, max_pages)

        # Save results to a CSV file
        output_file = 'yellow_pages_results.csv'
        df = pd.DataFrame(listings)
        df.to_csv(output_file, index=False)

        return {'current': 100, 'total': 100, 'status': 'Task completed!', 'result': output_file}
    except Exception as e:
        raise self.retry(exc=e, countdown=60, max_retries=2)  # Fewer retries, longer delay

@app.route('/download')
def download():
    output_file = 'yellow_pages_results.csv'
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
