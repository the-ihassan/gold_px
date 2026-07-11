from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

users = []
bookings = [
    {'id': 1, 'client': 'Sarah Johnson', 'event': 'Wedding', 'date': '2026-08-15', 'status': 'Confirmed'}
]
testimonials = [
    {'id': 1, 'name': 'Sarah', 'text': 'Gold PX transformed our wedding!', 'rating': 5}
]

@app.route('/')
def home():
    return jsonify({'message': 'GOLD PX API is live!'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    for user in users:
        if user['email'] == data['email']:
            return jsonify({'error': 'User already exists'}), 400
    new_user = {
        'id': len(users) + 1,
        'name': data['name'],
        'email': data['email'],
        'password': data['password']
    }
    users.append(new_user)
    return jsonify({'success': True, 'user': new_user}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    for user in users:
        if user['email'] == data['email'] and user['password'] == data['password']:
            return jsonify({'success': True, 'user': user})
    return jsonify({'error': 'Invalid credentials'}), 401

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
