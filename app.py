from flask import Flask, render_template, request, send_file, jsonify
import pandas as pd
from scraper import scrape_yellow_pages  # Import the updated scraper function

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        # Get user input from the form
        keyword = request.form.get('keyword')
        location = request.form.get('location')
        max_pages = int(request.form.get('max_pages'))

        # Call the updated scraper function
        listings = scrape_yellow_pages(keyword, location, max_pages)

        # Save results to a CSV file
        output_file = 'yellow_pages_results.csv'
        df = pd.DataFrame(listings)
        df.to_csv(output_file, index=False)

        # Return a JSON response indicating success
        return jsonify({"status": "success"})

    return render_template('index.html')

@app.route('/download')
def download():
    output_file = 'yellow_pages_results.csv'
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
