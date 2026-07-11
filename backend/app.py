from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# Explicitly allow GitHub Pages domain & localhost
CORS(app, origins=["https://the-ihassan.github.io", "http://localhost:3000"])

bookings = [
    {'id': 1, 'client': 'Sarah Johnson', 'event': 'Wedding', 'date': '2026-08-15', 'status': 'Confirmed'}
]
testimonials = [
    {'id': 1, 'name': 'Sarah', 'text': 'Gold PX transformed our wedding!', 'rating': 5}
]

@app.route('/')
def home():
    return jsonify({'message': 'GOLD PX API is live!'})

@app.route('/api/bookings', methods=['GET', 'POST'])
def bookings_api():
    if request.method == 'POST':
        new = request.json
        new['id'] = len(bookings) + 1
        bookings.append(new)
        return jsonify(new), 201
    return jsonify(bookings)

@app.route('/api/testimonials', methods=['GET'])
def testimonials_api():
    return jsonify(testimonials)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
