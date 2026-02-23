import React, { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { checkAuth } from '../store/slices/authSlice';

const PrivateRoute = ({ children }) => {
    const dispatch = useDispatch();
    const { user, loading, error } = useSelector((state) => state.auth);

    useEffect(() => {
        // Only check auth if we don't already have a user
        if (!user) {
            dispatch(checkAuth());
        }
    }, [dispatch, user]);

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

    if (error) {
        console.error('Auth error in PrivateRoute:', error);
    }

    return user ? children : <Navigate to="/login" />;
};

export default PrivateRoute;
