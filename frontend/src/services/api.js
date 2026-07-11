const API_URL = '?? $url = "https://trends-dylan-fabrics-congress.trycloudflare.com/api/bookings"  /api';

export async function getBookings() {
  const res = await fetch(${API_URL}/bookings);
  return res.json();
}

export async function createBooking(data) {
  const res = await fetch(${API_URL}/bookings, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}



