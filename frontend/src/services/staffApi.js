const isLocal = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const API_BASE_URL = isLocal
    ? "http://localhost:8000/api/staff"
    : `${window.location.origin}/api/staff`;

function formatValidationErrors(obj) {
    if (!obj || typeof obj !== 'object') return '';
    const parts = [];
    for (const [key, val] of Object.entries(obj)) {
        const msg = Array.isArray(val) ? val.join(' ') : String(val);
        if (msg) parts.push(`${key}: ${msg}`);
    }
    return parts.length ? parts.join('; ') : '';
}

function getAuthHeaders() {
    const token = sessionStorage.getItem('access');
    return {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
}

class StaffApi {
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
        const response = await fetch(`${API_BASE_URL}/dashboard/${ticketId}/reassign/`, {
            method: 'PATCH',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        
        const body = await response.json().catch(() => ({}));
        
        if (!response.ok) {
            const msg = body.error || (typeof body === 'object' && body.detail) || formatValidationErrors(body);
            throw new Error(msg || 'Failed to reassign ticket');
        }
        
        return body;
    }
}

const staffApiInstance = new StaffApi();
export default staffApiInstance;