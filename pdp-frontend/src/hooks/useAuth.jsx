import { createContext, useContext, useState, useEffect } from 'react';
import { pdpApi } from '../api/pdpClient';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Check if user is already logged in
        const token = pdpApi.getToken();
        if (token) {
            pdpApi.me()
                .then(userData => setUser(userData))
                .catch(() => pdpApi.logout())
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (username, password) => {
        const data = await pdpApi.login(username, password);
        setUser(data.user);
        return data;
    };

    const logout = () => {
        pdpApi.logout();
        setUser(null);
    };

    const value = {
        user,
        loading,
        login,
        logout,
        isAuthenticated: !!user,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
