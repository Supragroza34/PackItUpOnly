const API_BASE_URL = 'http://localhost:8000/api/admin';

class AdminAPI {
    // ================= AUTHENTICATION =================
    
    async login(username, password) {
        const response = await fetch(`${API_BASE_URL}/login/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ username, password }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Login failed');
        }
        
        return response.json();
    }
    
    async logout() {
        const response = await fetch(`${API_BASE_URL}/logout/`, {
            method: 'POST',
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Logout failed');
        }
        
        return response.json();
    }
    
    async getCurrentUser() {
        const response = await fetch(`${API_BASE_URL}/current-user/`, {
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch user');
        }
        
        return response.json();
    }
    
    // ================= DASHBOARD =================
    
    async getDashboardStats() {
        const response = await fetch(`${API_BASE_URL}/dashboard/stats/`, {
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard stats');
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
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch tickets');
        }
        
        return response.json();
    }
    
    async getTicketDetail(ticketId) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/`, {
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch ticket details');
        }
        
        return response.json();
    }
    
    async updateTicket(ticketId, data) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/update/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to update ticket');
        }
        
        return response.json();
    }
    
    async deleteTicket(ticketId) {
        const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}/delete/`, {
            method: 'DELETE',
            credentials: 'include',
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
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        
        return response.json();
    }
    
    async getUserDetail(userId) {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/`, {
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch user details');
        }
        
        return response.json();
    }
    
    async updateUser(userId, data) {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/update/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
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
            credentials: 'include',
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
            credentials: 'include',
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch staff list');
        }
        
        return response.json();
    }
}

export default new AdminAPI();
