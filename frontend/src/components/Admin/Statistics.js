import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchStatistics } from '../../store/slices/adminSlice';
import { logout } from '../../store/slices/authSlice';
import './Statistics.css';
import AdminTopbar from "./AdminTopbar";

const Statistics = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    
    const { user } = useSelector((state) => state.auth);
    const { statistics, statisticsLoading: loading, statisticsError: error } = useSelector((state) => state.admin);
    const [viewMode, setViewMode] = useState('table');
    
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
    
    const exportCsv = (type) => {
        const token = sessionStorage.getItem('access');
        const endpoint = type === 'statistics'
            ? '/api/admin/export/statistics-csv/'
            : '/api/admin/export/tickets-csv/';
        const url = `${endpoint}?start_date=${new Date(dateFilter.startDate).toISOString()}&end_date=${new Date(dateFilter.endDate + 'T23:59:59').toISOString()}`;
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
            a.download = `${type === 'statistics' ? 'ticket_statistics' : 'all_tickets'}_${dateFilter.startDate}_to_${dateFilter.endDate}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        })
        .catch(err => alert(`Failed to export ${type === 'statistics' ? 'statistics' : 'tickets'}: ` + err.message));
    };

    const handleExportStatistics = () => exportCsv('statistics');
    const handleExportAllTickets = () => exportCsv('tickets');
    
    const formatHours = (hours) => {
        if (hours === null || hours === undefined) return 'N/A';
        if (hours < 24) return `${hours.toFixed(1)} hours`;
        const days = Math.floor(hours / 24);
        const remainingHours = Math.floor(hours % 24);
        return `${days}d ${remainingHours}h`;
    };

    const departmentTotals = statistics?.department_statistics?.map((dept) => ({
        label: dept.department,
        value: dept.total_tickets,
    })) || [];

    const statusTotals = (statistics?.department_statistics || []).reduce(
        (acc, dept) => {
            acc.pending += dept.status_breakdown.pending || 0;
            acc.in_progress += dept.status_breakdown.in_progress || 0;
            acc.resolved += dept.status_breakdown.resolved || 0;
            acc.closed += dept.status_breakdown.closed || 0;
            return acc;
        },
        { pending: 0, in_progress: 0, resolved: 0, closed: 0 }
    );

    const priorityTotals = (statistics?.department_statistics || []).reduce(
        (acc, dept) => {
            acc.low += dept.priority_breakdown.low || 0;
            acc.medium += dept.priority_breakdown.medium || 0;
            acc.high += dept.priority_breakdown.high || 0;
            acc.urgent += dept.priority_breakdown.urgent || 0;
            return acc;
        },
        { low: 0, medium: 0, high: 0, urgent: 0 }
    );

    const statusGraphRows = [
        { label: 'Pending', key: 'pending', colorClass: 'bar-pending' },
        { label: 'In Progress', key: 'in_progress', colorClass: 'bar-in-progress' },
        { label: 'Resolved', key: 'resolved', colorClass: 'bar-resolved' },
        { label: 'Closed', key: 'closed', colorClass: 'bar-closed' },
    ];

    const priorityGraphRows = [
        { label: 'Low', key: 'low', colorClass: 'bar-priority-low' },
        { label: 'Medium', key: 'medium', colorClass: 'bar-priority-medium' },
        { label: 'High', key: 'high', colorClass: 'bar-priority-high' },
        { label: 'Urgent', key: 'urgent', colorClass: 'bar-priority-urgent' },
    ];

    const maxStatusValue = Math.max(
        1,
        ...statusGraphRows.map((row) => statusTotals[row.key] || 0)
    );

    const maxDepartmentValue = Math.max(
        1,
        ...departmentTotals.map((row) => row.value || 0)
    );

    const maxPriorityValue = Math.max(
        1,
        ...priorityGraphRows.map((row) => priorityTotals[row.key] || 0)
    );
    
    return (
        <div className="admin-dashboard">
            <AdminTopbar user={user} handleLogout={handleLogout} />

            <main className="dashboard-content">
                <div className="page-header">
                    <h2>Ticket Statistics & Analytics</h2>
                    <div className="view-toggle" aria-label="Statistics view mode">
                        <button
                            className={`view-toggle-btn ${viewMode === 'table' ? 'active' : ''}`}
                            onClick={() => setViewMode('table')}
                        >
                            Table View
                        </button>
                        <button
                            className={`view-toggle-btn ${viewMode === 'graph' ? 'active' : ''}`}
                            onClick={() => setViewMode('graph')}
                        >
                            Graph View
                        </button>
                    </div>
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

                        {viewMode === 'graph' ? (
                            <div className="graphs-grid">
                                <div className="graph-card">
                                    <h3>Status Distribution</h3>
                                    <div className="bar-graph">
                                        {statusGraphRows.map((row) => {
                                            const value = statusTotals[row.key] || 0;
                                            const width = (value / maxStatusValue) * 100;
                                            return (
                                                <div className="bar-row" key={row.key}>
                                                    <span className="bar-label">{row.label}</span>
                                                    <div className="bar-track">
                                                        <div
                                                            className={`bar-fill ${row.colorClass}`}
                                                            style={{ width: `${width}%` }}
                                                        />
                                                    </div>
                                                    <span className="bar-value">{value}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="graph-card">
                                    <h3>Tickets by Department</h3>
                                    <div className="bar-graph">
                                        {departmentTotals.map((row) => {
                                            const width = (row.value / maxDepartmentValue) * 100;
                                            return (
                                                <div className="bar-row" key={row.label}>
                                                    <span className="bar-label">{row.label}</span>
                                                    <div className="bar-track">
                                                        <div
                                                            className="bar-fill bar-department"
                                                            style={{ width: `${width}%` }}
                                                        />
                                                    </div>
                                                    <span className="bar-value">{row.value}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="graph-card">
                                    <h3>Priority Distribution</h3>
                                    <div className="bar-graph">
                                        {priorityGraphRows.map((row) => {
                                            const value = priorityTotals[row.key] || 0;
                                            const width = (value / maxPriorityValue) * 100;
                                            return (
                                                <div className="bar-row" key={row.key}>
                                                    <span className="bar-label">{row.label}</span>
                                                    <div className="bar-track">
                                                        <div
                                                            className={`bar-fill ${row.colorClass}`}
                                                            style={{ width: `${width}%` }}
                                                        />
                                                    </div>
                                                    <span className="bar-value">{value}</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <>
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
                        )}
                    </>
                ) : (
                    <div className="no-data">No statistics available for the selected date range.</div>
                )}
            </main>
        </div>
    );
};

export default Statistics;
