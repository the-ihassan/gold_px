import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const res = await fetch('https://ihassandev.pythonanywhere.com/api/bookings');
        if (res.ok) {
          const data = await res.json();
          setBookings(data);
        }
      } catch (err) {
        console.error('Failed to fetch bookings');
      }
    };
    fetchBookings();
  }, []);

  return (
    <div className="container" style={{ paddingTop: '4rem' }}>
      <h2 style={{ color: 'var(--gold)', marginBottom: '2rem' }}>Your Dashboard</h2>
      <div className="services-grid">
        {bookings.length > 0 ? (
          bookings.map(b => (
            <div key={b.id} className="service-card fade-in-visible" style={{ opacity: 1, transform: 'none' }}>
              <h3 style={{ color: 'var(--cyan)' }}>{b.event}</h3>
              <p>Client: {b.client}</p>
              <p>Date: {b.date}</p>
              <span style={{ background: b.status === 'Confirmed' ? '#10B981' : '#F59E0B', padding: '0.3rem 1rem', borderRadius: '20px', fontSize: '0.8rem' }}>{b.status}</span>
            </div>
          ))
        ) : (
          <p style={{ color: '#9CA3AF', gridColumn: '1 / -1', textAlign: 'center', padding: '4rem 0' }}>No bookings yet. Start from Booking page!</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
