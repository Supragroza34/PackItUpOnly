import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
    fetchUsers, 
    fetchUserDetail, 
    updateUser,
    deleteUser as deleteUserAction 
} from '../../store/slices/adminSlice';
import { logout } from '../../store/slices/authSlice';
import './UsersManagement.css';

const UsersManagement = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    
    const { user } = useSelector((state) => state.auth);
    const { 
        users, 
        usersTotalPages, 
        usersLoading: loading, 
        usersError: error,
        selectedUser
    } = useSelector((state) => state.admin);
    
    const [showModal, setShowModal] = useState(false);
    const [pagination, setPagination] = useState({ page: 1, page_size: 20 });
    const [editedUser, setEditedUser] = useState(null);
    
    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('');

    useEffect(() => {
        dispatch(fetchUsers({
            page: pagination.page,
            page_size: pagination.page_size,
            search: searchTerm,
            role: roleFilter,
        }));
    }, [dispatch, pagination.page, pagination.page_size, searchTerm, roleFilter]);

    const handleViewUser = async (userId) => {
        try {
            await dispatch(fetchUserDetail(userId)).unwrap();
            setEditedUser(selectedUser);
            setShowModal(true);
        } catch (err) {
            alert('Failed to load user details: ' + err);
        }
    };

    useEffect(() => {
        if (selectedUser) {
            setEditedUser(selectedUser);
        }
    }, [selectedUser]);

    const handleUpdateUser = async (e) => {
        e.preventDefault();
        try {
            await dispatch(updateUser({
                userId: editedUser.id,
                updates: {
                    role: editedUser.role,
                    department: editedUser.department,
                    first_name: editedUser.first_name,
                    last_name: editedUser.last_name,
                    email: editedUser.email,
                }
            })).unwrap();
            alert('User updated successfully!');
            setShowModal(false);
        } catch (err) {
            alert('Failed to update user: ' + err);
        }
    };

    const handleDeleteUser = async (userId) => {
        if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
        
        try {
            await dispatch(deleteUserAction(userId)).unwrap();
            alert('User deleted successfully!');
        } catch (err) {
            alert('Failed to delete user: ' + err);
        }
    };

    const handleLogout = async () => {
        await dispatch(logout());
        navigate('/login');
    };

    const refreshUsers = () => {
        dispatch(fetchUsers({
            page: pagination.page,
            page_size: pagination.page_size,
            search: searchTerm,
            role: roleFilter,
        }));
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
                    
                    <button onClick={refreshUsers} className="btn-refresh">Refresh</button>
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
                                Page {pagination.page} of {usersTotalPages || 1}
                            </span>
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                                disabled={pagination.page >= usersTotalPages}
                                className="btn-page"
                            >
                                Next
                            </button>
                        </div>
                    </>
                )}
            </main>

            {showModal && editedUser && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2>Edit User #{editedUser.id}</h2>
                        
                        <form onSubmit={handleUpdateUser}>
                            <div className="modal-section">
                                <h3>User Information</h3>
                                <p><strong>Username:</strong> {editedUser.username}</p>
                                <p><strong>K-Number:</strong> {editedUser.k_number}</p>
                            </div>

                            <div className="modal-section">
                                <h3>Edit User Details</h3>
                                
                                <div className="form-group">
                                    <label>First Name</label>
                                    <input
                                        type="text"
                                        value={editedUser.first_name}
                                        onChange={(e) => setEditedUser({ ...editedUser, first_name: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Last Name</label>
                                    <input
                                        type="text"
                                        value={editedUser.last_name}
                                        onChange={(e) => setEditedUser({ ...editedUser, last_name: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Email</label>
                                    <input
                                        type="email"
                                        value={editedUser.email}
                                        onChange={(e) => setEditedUser({ ...editedUser, email: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Department</label>
                                    <input
                                        type="text"
                                        value={editedUser.department || ''}
                                        onChange={(e) => setEditedUser({ ...editedUser, department: e.target.value })}
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Role</label>
                                    <select
                                        value={editedUser.role}
                                        onChange={(e) => setEditedUser({ ...editedUser, role: e.target.value })}
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
