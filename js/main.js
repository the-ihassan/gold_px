document.addEventListener('DOMContentLoaded', () => {
  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    const savedTheme = localStorage.getItem('goldpx-theme');
    if (savedTheme === 'light') document.body.classList.add('light-mode');
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('light-mode');
      const isLight = document.body.classList.contains('light-mode');
      localStorage.setItem('goldpx-theme', isLight ? 'light' : 'dark');
      themeToggle.textContent = isLight ? '☾' : '☀';
    });
    themeToggle.textContent = document.body.classList.contains('light-mode') ? '☾' : '☀';
  }

  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
  }

  const canvas = document.createElement('canvas');
  canvas.id = 'bg-canvas';
  canvas.setAttribute('aria-hidden', 'true');
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  let width = 0;
  let height = 0;
  let dpr = Math.min(window.devicePixelRatio || 1, 2);
  let particles = [];
  const pointer = { x: null, y: null, active: false };
  const particleCount = window.innerWidth < 768 ? 70 : 110;

  class Particle {
    constructor() {
      this.reset();
    }

    reset() {
      this.x = Math.random() * width;
      this.y = Math.random() * height;
      this.vx = (Math.random() - 0.5) * 0.5;
      this.vy = (Math.random() - 0.5) * 0.5;
      this.radius = Math.random() * 2.4 + 1.1;
      this.alpha = Math.random() * 0.75 + 0.35;
    }

    update() {
      this.x += this.vx;
      this.y += this.vy;

      if (this.x < 0 || this.x > width) this.vx *= -1;
      if (this.y < 0 || this.y > height) this.vy *= -1;

      if (pointer.active && pointer.x !== null) {
        const dx = this.x - pointer.x;
        const dy = this.y - pointer.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 140) {
          const force = (140 - dist) / 140;
          this.x += (dx / dist) * force * 1.8;
          this.y += (dy / dist) * force * 1.8;
        }
      }
    }

    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 230, 110, ${this.alpha})`;
      ctx.shadowBlur = 12;
      ctx.shadowColor = 'rgba(255, 215, 0, 0.9)';
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  function resizeCanvas() {
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    particles = Array.from({ length: particleCount }, () => new Particle());
  }

  function drawConnections() {
    for (let i = 0; i < particles.length; i += 1) {
      for (let j = i + 1; j < particles.length; j += 1) {
        const a = particles[i];
        const b = particles[j];
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < 110) {
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = `rgba(255, 230, 110, ${0.16 * (1 - distance / 110)})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      }
    }

    if (pointer.active && pointer.x !== null) {
      particles.forEach((particle) => {
        const dx = particle.x - pointer.x;
        const dy = particle.y - pointer.y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < 140) {
          ctx.beginPath();
          ctx.moveTo(particle.x, particle.y);
          ctx.lineTo(pointer.x, pointer.y);
          ctx.strokeStyle = `rgba(255, 230, 110, ${0.24 * (1 - distance / 140)})`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }
      });
    }
  }

  function animate() {
    ctx.clearRect(0, 0, width, height);
    particles.forEach((particle) => {
      particle.update();
      particle.draw();
    });
    drawConnections();
    requestAnimationFrame(animate);
  }

  function setPointerPosition(event) {
    const rect = canvas.getBoundingClientRect();
    pointer.x = event.clientX - rect.left;
    pointer.y = event.clientY - rect.top;
    pointer.active = true;
  }

  window.addEventListener('resize', resizeCanvas);
  window.addEventListener('mousemove', (event) => setPointerPosition(event));
  window.addEventListener('mouseleave', () => {
    pointer.active = false;
  });
  window.addEventListener('touchmove', (event) => {
    if (event.touches[0]) {
      setPointerPosition(event.touches[0]);
    }
  }, { passive: true });
  window.addEventListener('touchend', () => {
    pointer.active = false;
  });

  resizeCanvas();
  animate();

  const apiBaseUrl = (window.GOLDPX_API_BASE || 'http://127.0.0.1:8001').replace(/\/$/, '');

  const authForm = document.getElementById('auth-form');
  const authFeedback = document.getElementById('auth-feedback');
  const switchAuth = document.getElementById('switch-auth');
  const authButton = authForm?.querySelector('button[type="submit"]');
  const authFullNameField = document.getElementById('auth-fullname-field');
  let authMode = 'login';

  if (authForm && authFeedback && authButton) {
    const setAuthMode = (mode) => {
      authMode = mode;
      authButton.textContent = mode === 'login' ? 'Sign In' : 'Create Account';
      authButton.dataset.mode = mode;
      if (switchAuth) {
        switchAuth.textContent = mode === 'login' ? 'Create Account' : 'Already have account?';
      }
      if (authFullNameField) {
        authFullNameField.style.display = mode === 'signup' ? 'block' : 'none';
      }
    };

    if (switchAuth) {
      switchAuth.addEventListener('click', () => {
        setAuthMode(authMode === 'login' ? 'signup' : 'login');
      });
    }

    authForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(authForm);
      const payload = authMode === 'login'
        ? {
            email: formData.get('email'),
            password: formData.get('password'),
          }
        : {
            full_name: formData.get('full_name') || formData.get('email')?.toString().split('@')[0] || 'Guest',
            email: formData.get('email'),
            phone: '',
            password: formData.get('password'),
          };
      const endpoint = authMode === 'login' ? '/api/v1/auth/login' : '/api/v1/auth/signup';
      authFeedback.className = 'notice';
      authFeedback.textContent = 'Please wait...';
      authFeedback.classList.add('show');
      authButton.disabled = true;
      try {
        const response = await fetch(`${apiBaseUrl}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        const result = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(result.detail || 'Authentication failed');
        authFeedback.className = 'notice show';
        authFeedback.textContent = authMode === 'login' ? 'Signed in successfully.' : 'Account created successfully.';
        localStorage.setItem('goldpx-auth-token', result.access_token || '');
      } catch (error) {
        authFeedback.className = 'notice error show';
        authFeedback.textContent = error.message || 'Unable to authenticate';
      } finally {
        authButton.disabled = false;
      }
    });
    setAuthMode('login');
  }

  const feedbackForm = document.getElementById('feedback-form');
  const feedbackNotice = document.getElementById('feedback-notice');

  if (feedbackForm && feedbackNotice) {
    feedbackForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const data = new FormData(feedbackForm);
      feedbackNotice.className = 'notice show';
      feedbackNotice.textContent = `Thanks ${data.get('name') || 'there'}! Your feedback has been received.`;
      feedbackForm.reset();
    });
  }

  const bookingForm = document.getElementById('booking-form');
  const feedback = document.getElementById('form-feedback');

  if (bookingForm && feedback) {
    bookingForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const submitButton = bookingForm.querySelector('button[type="submit"]');
      const originalLabel = submitButton?.textContent || 'Submit Request';

      feedback.className = 'notice';
      feedback.textContent = 'Submitting your booking request...';
      feedback.classList.add('show');
      submitButton.disabled = true;
      submitButton.textContent = 'Submitting...';

      const payload = Object.fromEntries(new FormData(bookingForm).entries());
      const body = {
        customer_name: payload.customer_name,
        phone: payload.phone,
        email: payload.email || null,
        city: payload.city,
        venue: payload.venue,
        event_type: payload.event_type,
        event_date: payload.event_date,
        budget: payload.budget ? Number(payload.budget) : null,
        decoration_type: payload.decoration_type || null,
        lighting_type: payload.lighting_type || null,
        pixel_requirement: payload.pixel_requirement || null,
        special_notes: payload.special_notes || null,
      };

      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/bookings/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });

        const result = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(result.detail || 'Unable to submit booking right now.');
        }

        feedback.className = 'notice show';
        feedback.textContent = `Booking received successfully. Your reference is ${result.reference_no || 'pending'}. We are forwarding it to email and WhatsApp now.`;
        bookingForm.reset();

        const bookingText = `New booking request from ${body.customer_name || 'Guest'}\nPhone: ${body.phone || 'N/A'}\nEmail: ${body.email || 'N/A'}\nEvent: ${body.event_type || 'N/A'}\nDate: ${body.event_date || 'N/A'}\nVenue: ${body.venue || 'N/A'}\nBudget: ${body.budget || 'N/A'}\nNotes: ${body.special_notes || 'N/A'}`;
        const mailtoLink = `mailto:ihassan.dev@outlook.com?subject=${encodeURIComponent('New GOLD Px Booking Request')}&body=${encodeURIComponent(bookingText)}`;
        const whatsappLink1 = `https://wa.me/923145355656?text=${encodeURIComponent(bookingText)}`;
        const whatsappLink2 = `https://wa.me/923335079575?text=${encodeURIComponent(bookingText)}`;
        window.open(mailtoLink, '_blank');
        window.open(whatsappLink1, '_blank');
        window.open(whatsappLink2, '_blank');
      } catch (error) {
        feedback.className = 'notice error show';
        feedback.textContent = error.message || 'Something went wrong. Please try again.';
      } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalLabel;
      }
    });
  }
});
