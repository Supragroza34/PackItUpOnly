import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { checkAuth } from '../store/slices/authSlice';
import { useAuth } from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
    const dispatch = useDispatch();
    const { user: reduxUser, loading: reduxLoading } = useSelector((state) => state.auth);
    const { user: contextUser } = useAuth();

    const user = reduxUser ?? contextUser;

    useEffect(() => {
        if (!reduxUser && sessionStorage.getItem('access')) {
            dispatch(checkAuth());
        }
    }, [dispatch, reduxUser]);
    const loading = reduxLoading && !user;

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                fontSize: '18px',
                color: '#666'
            }}>
                Loading...
            </div>
        );
    }

    return user ? children : <Navigate to="/login" />;
};

export default PrivateRoute;
