const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal ? 'http://localhost:8000/api/admin' : `${window.location.origin}/api/admin`;

// Format DRF serializer errors { "field": ["msg"] } into a string
function formatValidationErrors(obj) {
    if (!obj || typeof obj !== 'object') return '';
    const parts = [];
    for (const [key, val] of Object.entries(obj)) {
        const msg = Array.isArray(val) ? val.join(' ') : String(val);
        if (msg) parts.push(`${key}: ${msg}`);
    }
    return parts.length ? parts.join('; ') : '';
}

// Helper to get auth headers with JWT token
function getAuthHeaders() {
    const token = sessionStorage.getItem('access');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
}

class AdminAPI {
    // ================= AUTHENTICATION =================
    // Note: Login now uses the common JWT endpoint at /api/auth/token/
    // So we don't need separate admin login/logout methods
    
    async getCurrentUser() {
        const base = isLocal ? 'http://localhost:8000' : window.location.origin;
        const response = await fetch(`${base}/api/users/me/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch user');
        }
        
        return response.json();
    }
    
    // ================= DASHBOARD =================
    
    async getDashboardStats() {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            const text = await response.text();
            let message = 'Failed to fetch dashboard stats';
            if (response.status === 401) message = 'Please log in again.';
            else if (response.status === 403) message = 'Access denied. Admin only.';
            else if (text) message = `${message}: ${text}`;
            throw new Error(message);
        }
        
        return response.json();
    }
    
    // ================= TICKETS =================
    
    async getTickets(params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.search) queryParams.append('search', params.search);
        if (params.status) queryParams.append('status', params.status);
        if (params.priority) queryParams.append('priority', params.priority);
        if (params.department) queryParams.append('department', params.department);
        if (params.assigned_to) queryParams.append('assigned_to', params.assigned_to);
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const url = `${API_BASE_URL}/tickets/?${queryParams.toString()}`;
        const response = await fetch(url, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch tickets');
        }
        
        return response.json();
    }
    
    async getTicketDetail(ticketId) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch ticket details');
        }
        
        return response.json();
    }
    
    async updateTicket(ticketId, data) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/update/`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        
        const body = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            // DRF validation errors: { "field": ["message"] } or backend { "error": "..." }
            const msg = body.error || (typeof body === 'object' && body.detail) || formatValidationErrors(body);
            throw new Error(msg || 'Failed to update ticket');
        }
        
        return body;
    }
    
    async deleteTicket(ticketId) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/delete/`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete ticket');
        }
        
        return response.json();
    }
    
    // ================= USERS =================
    
    async getUsers(params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.search) queryParams.append('search', params.search);
        if (params.role) queryParams.append('role', params.role);
        if (params.page) queryParams.append('page', params.page);
        if (params.page_size) queryParams.append('page_size', params.page_size);
        
        const url = `${API_BASE_URL}/users/?${queryParams.toString()}`;
        const response = await fetch(url, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        
        return response.json();
    }
    
    async getUserDetail(userId) {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch user details');
        }
        
        return response.json();
    }
    
    async updateUser(userId, data) {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/update/`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update user');
        }
        
        return response.json();
    }
    
    async deleteUser(userId) {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/delete/`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to delete user');
        }
        
        return response.json();
    }
    
    // ================= STAFF LIST =================
    
    async getStaffList() {
        const response = await fetch(`${API_BASE_URL}/staff/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch staff list');
        }
        
        return response.json();
    }
    
    // ================= STATISTICS =================
    
    async getStatistics(params = {}) {
        const queryParams = new URLSearchParams();
        
        if (params.days) queryParams.append('days', params.days);
        if (params.start_date) queryParams.append('start_date', params.start_date);
        if (params.end_date) queryParams.append('end_date', params.end_date);
        
        const url = `${API_BASE_URL}/statistics/?${queryParams.toString()}`;
        const response = await fetch(url, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch statistics');
        }
        
        return response.json();
    }
}

const adminApiInstance = new AdminAPI();
export default adminApiInstance;
