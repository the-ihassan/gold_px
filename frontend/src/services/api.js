const API_URL = 'https://cheers-springer-asked-announcements.trycloudflare.com';

export async function registerUser(data) {
  const res = await fetch(${API_URL}/register, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return res.json();
}
export async function getBookings() {
  const res = await fetch(${API_URL}/bookings);
  return res.json();
}
export async function createBooking(data) {
  const res = await fetch(${API_URL}/bookings, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  return res.json();
}

