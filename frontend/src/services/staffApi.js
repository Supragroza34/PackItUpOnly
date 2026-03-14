const API_BASE_URL = 'http://localhost:8000/api/staff';

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
    const token = localStorage.getItem('access');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
}

class StaffApi{
    // ================= STAFF LIST =================
    
    async getStaffList() {
        const response = await fetch(`${API_BASE_URL}/list/`, {
            headers: getAuthHeaders(),
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch staff list');
        }
        
        return response.json();
    }
    
    async reassignTicket(ticketId, data) {
        const response = await fetch(`${API_BASE_URL}/dashboard/${ticketId}/reassign`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        
        const body = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            // DRF validation errors: { "field": ["message"] } or backend { "error": "..." }
            const msg = body.error || (typeof body === 'object' && body.detail) || formatValidationErrors(body);
            throw new Error(msg || 'Failed to reassign ticket');
        }
        
        return body;
    }
}

const staffApiInstance = new StaffApi();
export default staffApiInstance;