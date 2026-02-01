import { useState, useEffect } from 'react';
import { Layout, Tabs, Alert } from 'antd';
import { useAuth } from '../contexts/AuthContext';
import styles from '../styles/AdminPanel.module.css';
import Products from './admin/Products';
import Employees from './admin/Employees';
import MasterData from './admin/MasterData';
import MasterSlots from './admin/MasterSlots';
import { ShoppingOutlined, UserOutlined, DatabaseOutlined, TeamOutlined } from '@ant-design/icons';

const { Content } = Layout;

const AdminPanel = () => {
    const { user, hasPermission } = useAuth();
    const [activeTab, setActiveTab] = useState('products');

    const canManageProducts = hasPermission('product.manage');
    const canManageEmployees = hasPermission('auth.user.manage');
    const canViewMasterData = hasPermission('master.data.view');

    // If user has NO admin permissions at all, deny access
    if (!canManageProducts && !canManageEmployees && !canViewMasterData) {
        return (
            <div style={{ padding: '50px', textAlign: 'center' }}>
                <Alert
                    message="Access Denied"
                    description="You don't have permission to access the Admin Panel."
                    type="error"
                    showIcon
                />
            </div>
        );
    }

    const items = [];

    if (canManageProducts) {
        items.push({
            key: 'products',
            label: (
                <span>
                    <ShoppingOutlined />
                    Product Management
                </span>
            ),
            children: <Products />,
        });
    }

    if (canManageEmployees) {
        items.push({
            key: 'employees',
            label: (
                <span>
                    <UserOutlined />
                    Employee Management
                </span>
            ),
            children: <Employees />,
        });
    }

    if (canManageEmployees) { // Assuming slots managed by same people who manage employees
        items.push({
            key: 'slots',
            label: (
                <span>
                    <TeamOutlined />
                    Master Slots
                </span>
            ),
            children: <MasterSlots />,
        });
    }

    if (canViewMasterData) {
        items.push({
            key: 'master',
            label: (
                <span>
                    <DatabaseOutlined />
                    Master Data
                </span>
            ),
            children: <MasterData />,
        });
    }

    // Ensure activeTab is valid (defaults to first available item if current not found)
    useEffect(() => {
        if (items.length > 0 && !items.find(i => i.key === activeTab)) {
            setActiveTab(items[0].key);
        }
    }, [items, activeTab]);

    return (
        <Layout className={styles.layout}>
            <Content className={styles.content}>
                <div className={styles.container}>
                    <Tabs
                        defaultActiveKey="products"
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        items={items}
                        size="large"
                        type="card"
                        style={{ marginTop: 16 }}
                    />
                </div>
            </Content>
        </Layout>
    );
};

export default AdminPanel;
