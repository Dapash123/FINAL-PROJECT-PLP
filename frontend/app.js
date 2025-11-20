// app.js

const API_URL = 'http://localhost:5000';

function setUserSession(user, token) {
    localStorage.setItem('harvesthub_user', JSON.stringify(user));
    localStorage.setItem('harvesthub_token', token);
}
function getUserSession() {
    const user = localStorage.getItem('harvesthub_user');
    const token = localStorage.getItem('harvesthub_token');
    return user && token ? { user: JSON.parse(user), token } : null;
}
function clearUserSession() {
    localStorage.removeItem('harvesthub_user');
    localStorage.removeItem('harvesthub_token');
}

function showMessage(msg, type = 'info') {
    let el = document.getElementById('msg-box');
    if (!el) {
        el = document.createElement('div');
        el.id = 'msg-box';
        document.body.appendChild(el);
    }
    el.textContent = msg;
    el.className = 'msg-box ' + type;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

document.addEventListener('DOMContentLoaded', function() {
    // Animate forms and main content
    document.querySelectorAll('form').forEach(form => form.classList.add('fade-in'));
    const main = document.querySelector('main');
    if (main) main.classList.add('slide-up');

    // Logout handler (if logout button exists)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function() {
            clearUserSession();
            window.location.href = 'login.html';
        });
    }

    // Redirect to login if not authenticated (dashboard only)
    if (window.location.pathname.includes('dashboard')) {
        const session = getUserSession();
        if (!session) {
            window.location.href = 'login.html';
            return;
        }
        loadFoodListings(session.token);
    }

    // Login form handler
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            loginForm.classList.add('form-success');
            const email = loginForm.email.value;
            const password = loginForm.password.value;
            try {
                const res = await fetch(`${API_URL}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await res.json();
                if (res.ok && data.token) {
                    setUserSession(data.user, data.token);
                    showMessage('Login successful!', 'success');
                    setTimeout(() => window.location.href = 'dashboard.html', 800);
                } else {
                    showMessage(data.message || 'Login failed', 'error');
                }
            } catch (err) {
                showMessage('Network error', 'error');
            }
        });
    }

    // Register form handler
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            registerForm.classList.add('form-success');
            const name = registerForm.name.value;
            const email = registerForm.email.value;
            const password = registerForm.password.value;
            const role = registerForm.role.value;
            try {
                const res = await fetch(`${API_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, email, password, role })
                });
                const data = await res.json();
                if (res.ok && data.token) {
                    setUserSession(data.user, data.token);
                    showMessage('Registration successful!', 'success');
                    setTimeout(() => window.location.href = 'dashboard.html', 800);
                } else {
                    showMessage(data.message || 'Registration failed', 'error');
                }
            } catch (err) {
                showMessage('Network error', 'error');
            }
        });
    }

    // Food posting form handler
    const foodForm = document.getElementById('foodForm');
    if (foodForm) {
        foodForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            foodForm.classList.add('form-success');
            const session = getUserSession();
            if (!session) {
                showMessage('Please login first', 'error');
                return;
            }
            const formData = new FormData();
            formData.append('photo', foodForm.photo.files[0]);
            formData.append('description', foodForm.description.value);
            formData.append('location', foodForm.location.value);
            // Simulate AI estimation
            formData.append('quantity', Math.floor(Math.random()*100+10) + 'kg');
            formData.append('shelf_life', Math.floor(Math.random()*5+2) + ' days');
            try {
                const res = await fetch(`${API_URL}/food`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${session.token}` },
                    body: formData
                });
                const data = await res.json();
                if (res.ok) {
                    showMessage('Food posted!', 'success');
                    loadFoodListings(session.token);
                    foodForm.reset();
                } else {
                    showMessage(data.message || 'Failed to post food', 'error');
                }
            } catch (err) {
                showMessage('Network error', 'error');
            }
        });
    }

    // Flip card animation for food listings
    const foodListings = document.getElementById('food-listings');
    if (foodListings) {
        foodListings.addEventListener('click', function(e) {
            const card = e.target.closest('.food-card');
            if (card) {
                card.classList.toggle('flipped');
            }
            // Claim button
            if (e.target.classList.contains('claim-btn')) {
                e.stopPropagation();
                claimFood(card.dataset.id);
            }
        });
    }
});

async function loadFoodListings(token) {
    const foodListings = document.getElementById('food-listings');
    if (!foodListings) return;
    foodListings.innerHTML = '<div class="loading">Loading...</div>';
    try {
        const res = await fetch(`${API_URL}/food`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (res.ok && Array.isArray(data.food)) {
            foodListings.innerHTML = '';
            data.food.forEach(item => {
                foodListings.innerHTML += renderFoodCard(item);
            });
        } else {
            foodListings.innerHTML = '<div>No food listings found.</div>';
        }
    } catch (err) {
        foodListings.innerHTML = '<div class="error">Failed to load listings.</div>';
    }
}

function renderFoodCard(item) {
    return `<div class="food-card" data-id="${item.id}">
        <div class="food-card-inner">
            <div class="food-card-front">
                <img src="${item.photo_url || 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=400&q=80'}" alt="${item.description}" class="food-img">
                <div class="food-info">
                    <h4>${item.description}</h4>
                    <p>Location: ${item.location}</p>
                    <p>Quantity: ${item.quantity || 'N/A'}</p>
                </div>
            </div>
            <div class="food-card-back">
                <h4>Estimated Shelf Life</h4>
                <p>${item.shelf_life || 'N/A'}</p>
                <h4>Posted by</h4>
                <p>${item.poster_name || 'Unknown'}</p>
                <button class="claim-btn">Claim</button>
            </div>
        </div>
    </div>`;
}

async function claimFood(foodId) {
    const session = getUserSession();
    if (!session) {
        showMessage('Please login first', 'error');
        return;
    }
    // Simulate payment for suppliers
    if (session.user.role === 'supplier') {
        showMessage('Processing payment (simulated)...', 'info');
        await new Promise(r => setTimeout(r, 1200));
        showMessage('Payment successful! Food claimed.', 'success');
    } else {
        showMessage('Food claimed!', 'success');
    }
    // Send claim to backend (optional, stub)
    // await fetch(`${API_URL}/match`, { ... })
    loadFoodListings(session.token);
}
