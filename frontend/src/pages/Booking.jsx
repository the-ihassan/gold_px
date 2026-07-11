import React, { useState } from 'react';

const Booking = () => {
  const [form, setForm] = useState({ client: '', event: '', date: '' });
  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });
  const handleSubmit = async (e) => {
    e.preventDefault();
    // API call to PythonAnywhere backend
    try {
      const res = await fetch('https://ihassandev.pythonanywhere.com/api/bookings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form)
      });
      if (res.ok) alert('✅ Booking sent successfully!');
    } catch (err) {
      alert('⚠️ Could not connect to server. Please try again later.');
    }
  };

  return (
    <div className="container" style={{ paddingTop: '4rem' }}>
      <h2 style={{ color: 'var(--gold)', marginBottom: '2rem' }}>Book Your Lighting Experience</h2>
      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Your Name</label>
            <input name="client" value={form.client} onChange={handleChange} required />
          </div>
          <div className="form-group">
            <label>Event Type</label>
            <select name="event" value={form.event} onChange={handleChange} required>
              <option value="">Select</option>
              <option>Wedding</option>
              <option>Corporate Gala</option>
              <option>Concert</option>
            </select>
          </div>
          <div className="form-group">
            <label>Event Date</label>
            <input type="date" name="date" value={form.date} onChange={handleChange} required />
          </div>
          <button type="submit" className="btn-submit">Submit Booking</button>
        </form>
      </div>
    </div>
  );
};

export default Booking;
