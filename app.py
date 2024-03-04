
from flask import Flask, render_template

app = Flask(__name__)

# Define your sec_data values here or import them from your script

@app.route('/')
def index():
    # Pass sec_data to the HTML template
    sec_data = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]  # Example sec_data
    return render_template('data2.html',)

if __name__ == '__main__':
    app.run(debug=True)