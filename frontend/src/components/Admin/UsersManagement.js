import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import adminApi from '../../services/adminApi';
import { useAuth } from '../../context/AuthContext';
import './UsersManagement.css';

const UsersManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedUser, setSelectedUser] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [pagination, setPagination] = useState({ page: 1, total: 0, page_size: 20 });
    
    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('');
    
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const fetchUsers = useCallback(async () => {
        try {
            setLoading(true);
            const data = await adminApi.getUsers({
                page: pagination.page,
                page_size: pagination.page_size,
                search: searchTerm,
                role: roleFilter,
            });
            setUsers(data.users);
            setPagination(prev => ({ ...prev, total: data.total, total_pages: data.total_pages }));
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.page_size, searchTerm, roleFilter]);

    useEffect(() => {
        fetchUsers();
    }, [fetchUsers]);

    const handleViewUser = async (userId) => {
        try {
            const userData = await adminApi.getUserDetail(userId);
            setSelectedUser(userData);
            setShowModal(true);
        } catch (err) {
            alert('Failed to load user details: ' + err.message);
        }
    };

    const handleUpdateUser = async (e) => {
        e.preventDefault();
        try {
            await adminApi.updateUser(selectedUser.id, {
                role: selectedUser.role,
                department: selectedUser.department,
                first_name: selectedUser.first_name,
                last_name: selectedUser.last_name,
                email: selectedUser.email,
            });
            alert('User updated successfully!');
            setShowModal(false);
            fetchUsers();
        } catch (err) {
            alert('Failed to update user: ' + err.message);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
        
        try {
            await adminApi.deleteUser(userId);
            alert('User deleted successfully!');
            fetchUsers();
        } catch (err) {
            alert('Failed to delete user: ' + err.message);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <div className="header-content">
                    <h1>Admin Dashboard - Users</h1>
                    <div className="header-actions">
                        <span className="user-info">Welcome, {user?.first_name || user?.username}</span>
                        <button onClick={handleLogout} className="btn-logout">Logout</button>
                    </div>
                </div>
            </header>

            <nav className="admin-nav">
                <button className="nav-btn" onClick={() => navigate('/admin/dashboard')}>Dashboard</button>
                <button className="nav-btn" onClick={() => navigate('/admin/tickets')}>Tickets</button>
                <button className="nav-btn active" onClick={() => navigate('/admin/users')}>Users</button>
            </nav>

            <main className="dashboard-content">
                <div className="page-header">
                    <h2>User Management</h2>
                </div>

                <div className="filters-section">
                    <input
                        type="text"
                        placeholder="Search by name, username, email, K-number..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-input"
                    />
                    
                    <select
                        value={roleFilter}
                        onChange={(e) => setRoleFilter(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Roles</option>
                        <option value="student">Student</option>
                        <option value="staff">Staff</option>
                        <option value="admin">Admin</option>
                    </select>
                    
                    <button onClick={fetchUsers} className="btn-refresh">Refresh</button>
                </div>

                {loading ? (
                    <div className="loading">Loading users...</div>
                ) : error ? (
                    <div className="error">Error: {error}</div>
                ) : (
                    <>
                        <div className="users-table-container">
                            <table className="users-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Username</th>
                                        <th>Name</th>
                                        <th>Email</th>
                                        <th>K-Number</th>
                                        <th>Department</th>
                                        <th>Role</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((usr) => (
                                        <tr key={usr.id}>
                                            <td>{usr.id}</td>
                                            <td>{usr.username}</td>
                                            <td>{usr.first_name} {usr.last_name}</td>
                                            <td>{usr.email}</td>
                                            <td>{usr.k_number}</td>
                                            <td>{usr.department || '-'}</td>
                                            <td>
                                                <span className={`role-badge ${usr.role}`}>
                                                    {usr.role}
                                                </span>
                                            </td>
                                            <td className="actions-cell">
                                                <button
                                                    onClick={() => handleViewUser(usr.id)}
                                                    className="btn-action btn-view"
                                                >
                                                    View/Edit
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteUser(usr.id)}
                                                    className="btn-action btn-delete"
                                                    disabled={Number(usr.id) === Number(user?.id)}
                                                    title={Number(usr.id) === Number(user?.id) ? "Cannot delete your own account" : "Delete user"}
                                                >
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="pagination">
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                                disabled={pagination.page === 1}
                                className="btn-page"
                            >
                                Previous
                            </button>
                            <span className="page-info">
                                Page {pagination.page} of {pagination.total_pages || 1}
                            </span>
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                                disabled={pagination.page >= pagination.total_pages}
                                className="btn-page"
                            >
                                Next
                            </button>
                        </div>
                    </>
                )}
            </main>

            {showModal && selectedUser && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2>Edit User #{selectedUser.id}</h2>
                        
                        <form onSubmit={handleUpdateUser}>
                            <div className="modal-section">
                                <h3>User Information</h3>
                                <p><strong>Username:</strong> {selectedUser.username}</p>
                                <p><strong>K-Number:</strong> {selectedUser.k_number}</p>
                            </div>

                            <div className="modal-section">
                                <h3>Edit User Details</h3>
                                
                                <div className="form-group">
                                    <label>First Name</label>
                                    <input
                                        type="text"
                                        value={selectedUser.first_name}
                                        onChange={(e) => setSelectedUser({ ...selectedUser, first_name: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Last Name</label>
                                    <input
                                        type="text"
                                        value={selectedUser.last_name}
                                        onChange={(e) => setSelectedUser({ ...selectedUser, last_name: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Email</label>
                                    <input
                                        type="email"
                                        value={selectedUser.email}
                                        onChange={(e) => setSelectedUser({ ...selectedUser, email: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Department</label>
                                    <input
                                        type="text"
                                        value={selectedUser.department || ''}
                                        onChange={(e) => setSelectedUser({ ...selectedUser, department: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Role</label>
                                    <select
                                        value={selectedUser.role}
                                        onChange={(e) => setSelectedUser({ ...selectedUser, role: e.target.value })}
                                    >
                                        <option value="student">Student</option>
                                        <option value="staff">Staff</option>
                                        <option value="admin">Admin</option>
                                    </select>
                                </div>
                            </div>

                            <div className="modal-actions">
                                <button type="submit" className="btn-save">Save Changes</button>
                                <button type="button" onClick={() => setShowModal(false)} className="btn-cancel">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UsersManagement;
