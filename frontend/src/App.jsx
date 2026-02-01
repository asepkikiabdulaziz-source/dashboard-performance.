import { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AdminPanel from './pages/AdminPanel';
import UnifiedCompetition from './pages/admin/UnifiedCompetition';
import { Spin, Button, Space, App as AntdApp } from 'antd';
import { DashboardOutlined, ToolOutlined, TrophyOutlined, LogoutOutlined } from '@ant-design/icons';

const AppContent = () => {
    const { user, login, logout, loading, hasPermission } = useAuth();
    const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'competition', or 'admin'

    // RBAC: Check if user has ANY admin permission
    const hasAdminAccess = user && (
        hasPermission('product.manage') ||
        hasPermission('auth.user.manage') ||
        hasPermission('master.data.view')
    );

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100vh'
            }}>
                <Spin size="large" />
            </div>
        );
    }

    if (!user) {
        return <Login />;
    }

    // Navigation buttons component as a Top Bar
    const NavigationButtons = () => (
        <div style={{
            padding: '0 24px',
            height: '64px',
            background: '#ffffff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
            position: 'sticky',
            top: 0,
            zIndex: 1000
        }}>
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    cursor: 'pointer',
                    gap: '12px'
                }}
                onClick={() => setCurrentView('dashboard')}
            >
                <div style={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    width: '32px',
                    height: '32px',
                    borderRadius: '8px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    color: 'white'
                }}>
                    <DashboardOutlined />
                </div>
                <span style={{
                    fontWeight: 800,
                    fontSize: '18px',
                    color: '#1a1a1a',
                    letterSpacing: '-0.5px'
                }}>
                    NABATI<span style={{ color: '#667eea' }}>CUAN</span>
                </span>
            </div>

            <Space size="middle">
                {currentView !== 'dashboard' && (
                    <Button
                        type="text"
                        icon={<DashboardOutlined />}
                        onClick={() => setCurrentView('dashboard')}
                        style={{ fontWeight: 500 }}
                    >
                        Dashboard
                    </Button>
                )}
                {currentView !== 'competition' && (
                    <Button
                        type="text"
                        icon={<TrophyOutlined />}
                        onClick={() => setCurrentView('competition')}
                        style={{ fontWeight: 500 }}
                    >
                        Kompetisi
                    </Button>
                )}
                {hasAdminAccess && currentView !== 'admin' && (
                    <Button
                        type="text"
                        icon={<ToolOutlined />}
                        onClick={() => setCurrentView('admin')}
                        style={{ fontWeight: 500 }}
                    >
                        Admin Panel
                    </Button>
                )}

                <div style={{ height: '24px', width: '1px', background: '#f0f0f0', margin: '0 8px' }} />

                <Space size="small">
                    <span style={{ fontSize: '12px', color: '#8c8c8c' }}>{user.name}</span>
                    <Button
                        danger
                        type="primary"
                        size="small"
                        icon={<LogoutOutlined />}
                        onClick={logout}
                    >
                        Logout
                    </Button>
                </Space>
            </Space>
        </div>
    );

    // Show appropriate view
    if (currentView === 'admin' && hasAdminAccess) {
        return (
            <div>
                <NavigationButtons />
                <AdminPanel />
            </div>
        );
    }

    if (currentView === 'competition') {
        return (
            <div>
                <NavigationButtons />
                <UnifiedCompetition />
            </div>
        );
    }

    return (
        <div>
            <NavigationButtons />
            <Dashboard />
        </div>
    );
};

function App() {
    return (
        <AuthProvider>
            <AntdApp>
                <AppContent />
            </AntdApp>
        </AuthProvider>
    );
}

export default App;
