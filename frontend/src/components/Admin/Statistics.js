import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchStatistics } from '../../store/slices/adminSlice';
import { logout } from '../../store/slices/authSlice';
import './Statistics.css';

const Statistics = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    
    const { user } = useSelector((state) => state.auth);
    const { statistics, statisticsLoading: loading, statisticsError: error } = useSelector((state) => state.admin);
    
    // Date filter state (default: last 30 days)
    const [dateFilter, setDateFilter] = useState({
        days: 30,
        startDate: '',
        endDate: '',
    });
    
    // Calculate default dates for custom range
    useEffect(() => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - 30);
        
        setDateFilter(prev => ({
            ...prev,
            startDate: start.toISOString().split('T')[0],
            endDate: end.toISOString().split('T')[0],
        }));
    }, []);
    
    // Fetch statistics on mount and when filter changes
    useEffect(() => {
        if (dateFilter.startDate && dateFilter.endDate) {
            dispatch(fetchStatistics({
                start_date: new Date(dateFilter.startDate).toISOString(),
                end_date: new Date(dateFilter.endDate + 'T23:59:59').toISOString(),
            }));
        }
    }, [dispatch, dateFilter.startDate, dateFilter.endDate]);
    
    const handleLogout = async () => {
        await dispatch(logout());
        navigate('/login');
    };
    
    const handleQuickFilter = (days) => {
        const end = new Date();
        const start = new Date();
        start.setDate(start.getDate() - days);
        
        setDateFilter({
            days: days,
            startDate: start.toISOString().split('T')[0],
            endDate: end.toISOString().split('T')[0],
        });
    };
    
    const handleExportStatistics = () => {
        const token = localStorage.getItem('access');
        const url = `/api/admin/export/statistics-csv/?start_date=${new Date(dateFilter.startDate).toISOString()}&end_date=${new Date(dateFilter.endDate + 'T23:59:59').toISOString()}`;
        
        fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status} ${response.statusText}`);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ticket_statistics_${dateFilter.startDate}_to_${dateFilter.endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => alert('Failed to export statistics: ' + err.message));
    };
    
    const handleExportAllTickets = () => {
        const token = localStorage.getItem('access');
        const url = `/api/admin/export/tickets-csv/?start_date=${new Date(dateFilter.startDate).toISOString()}&end_date=${new Date(dateFilter.endDate + 'T23:59:59').toISOString()}`;
        
        fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Export failed: ${response.status} ${response.statusText}`);
            }
            return response.blob();
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `all_tickets_${dateFilter.startDate}_to_${dateFilter.endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => alert('Failed to export tickets: ' + err.message));
    };
    
    const formatHours = (hours) => {
        if (hours === null || hours === undefined) return 'N/A';
        if (hours < 24) return `${hours.toFixed(1)} hours`;
        const days = Math.floor(hours / 24);
        const remainingHours = Math.floor(hours % 24);
        return `${days}d ${remainingHours}h`;
    };
    
    return (
        <div className="admin-dashboard">
            {/* Top bar - matching admin dashboard style */}
            <div className="dashboard-topbar">
                <h1>👋 Welcome, {user?.first_name || user?.username || 'Admin'}</h1>
                <div className="dashboard-topbar-actions">
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/dashboard')}
                    >
                        Dashboard
                    </button>
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/tickets')}
                    >
                        Tickets
                    </button>
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/users')}
                    >
                        Users
                    </button>
                    <button 
                        className="nav-tab active"
                        onClick={() => navigate('/admin/statistics')}
                    >
                        Statistics
                    </button>
                    <button className="logout-btn" onClick={handleLogout}>
                        Log Out
                    </button>
                </div>
            </div>

            <main className="dashboard-content">
                <div className="page-header">
                    <h2>Ticket Statistics & Analytics</h2>
                </div>
                
                {/* Date Filter Section */}
                <div className="filters-section">
                    <div className="quick-filters">
                        <button 
                            className={`quick-filter-btn ${dateFilter.days === 7 ? 'active' : ''}`}
                            onClick={() => handleQuickFilter(7)}
                        >
                            Last 7 Days
                        </button>
                        <button 
                            className={`quick-filter-btn ${dateFilter.days === 30 ? 'active' : ''}`}
                            onClick={() => handleQuickFilter(30)}
                        >
                            Last 30 Days
                        </button>
                        <button 
                            className={`quick-filter-btn ${dateFilter.days === 90 ? 'active' : ''}`}
                            onClick={() => handleQuickFilter(90)}
                        >
                            Last 90 Days
                        </button>
                    </div>
                    
                    <div className="custom-date-range">
                        <label>
                            Start Date:
                            <input 
                                type="date" 
                                value={dateFilter.startDate}
                                max={dateFilter.endDate}
                                onChange={(e) => {
                                    setDateFilter(prev => ({ 
                                        ...prev, 
                                        startDate: e.target.value, 
                                        days: null 
                                    }));
                                }}
                                className="date-input"
                            />
                        </label>
                        <label>
                            End Date:
                            <input 
                                type="date" 
                                value={dateFilter.endDate}
                                min={dateFilter.startDate}
                                onChange={(e) => {
                                    setDateFilter(prev => ({ 
                                        ...prev, 
                                        endDate: e.target.value, 
                                        days: null 
                                    }));
                                }}
                                className="date-input"
                            />
                        </label>
                    </div>
                    
                    <div className="export-buttons">
                        <button onClick={handleExportStatistics} className="btn-export">
                            📊 Export Statistics CSV
                        </button>
                        <button onClick={handleExportAllTickets} className="btn-export">
                            📄 Export All Tickets CSV
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="loading">Loading statistics...</div>
                ) : error ? (
                    <div className="error">Error: {error}</div>
                ) : statistics && statistics.department_statistics ? (
                    <>
                        {/* Overall Summary */}
                        <div className="stats-summary">
                            <div className="summary-card">
                                <div className="summary-count">{statistics.total_tickets}</div>
                                <div className="summary-label">Total Tickets</div>
                            </div>
                            <div className="summary-card">
                                <div className="summary-count">{statistics.department_statistics.length}</div>
                                <div className="summary-label">Departments</div>
                            </div>
                        </div>
                        
                        {/* Department Statistics Table */}
                        <div className="statistics-table-container">
                            <h3>Department Breakdown</h3>
                            <table className="statistics-table">
                                <thead>
                                    <tr>
                                        <th>Department</th>
                                        <th>Total Tickets</th>
                                        <th>Pending</th>
                                        <th>In Progress</th>
                                        <th>Resolved</th>
                                        <th>Closed</th>
                                        <th>Avg Resolution Time</th>
                                        <th>Avg Response Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {statistics.department_statistics.map((dept) => (
                                        <tr key={dept.department}>
                                            <td className="dept-name">{dept.department}</td>
                                            <td className="total-count">{dept.total_tickets}</td>
                                            <td>{dept.status_breakdown.pending}</td>
                                            <td>{dept.status_breakdown.in_progress}</td>
                                            <td>{dept.status_breakdown.resolved}</td>
                                            <td>{dept.status_breakdown.closed}</td>
                                            <td>{formatHours(dept.avg_resolution_time_hours)}</td>
                                            <td>{formatHours(dept.avg_response_time_hours)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                        
                        {/* Priority Distribution */}
                        <div className="statistics-table-container">
                            <h3>Priority Distribution by Department</h3>
                            <table className="statistics-table">
                                <thead>
                                    <tr>
                                        <th>Department</th>
                                        <th>Low</th>
                                        <th>Medium</th>
                                        <th>High</th>
                                        <th>Urgent</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {statistics.department_statistics.map((dept) => (
                                        <tr key={dept.department}>
                                            <td className="dept-name">{dept.department}</td>
                                            <td>{dept.priority_breakdown.low}</td>
                                            <td>{dept.priority_breakdown.medium}</td>
                                            <td>{dept.priority_breakdown.high}</td>
                                            <td>{dept.priority_breakdown.urgent}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </>
                ) : (
                    <div className="no-data">No statistics available for the selected date range.</div>
                )}
            </main>
        </div>
    );
};

export default Statistics;
