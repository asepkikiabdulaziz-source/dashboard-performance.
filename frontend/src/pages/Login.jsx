import { useState } from 'react';
import { Form, Input, Button, Card, Alert, Divider, Typography, Space, Tag } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import styles from '../styles/Login.module.css';

const { Title, Text, Paragraph } = Typography;

const Login = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const { login } = useAuth();

    const onFinish = async (values) => {
        setLoading(true);
        setError('');

        const result = await login(values.email, values.password);

        if (!result.success) {
            setError(result.error);
        }

        setLoading(false);
    };

    const quickLogin = async (email, password) => {
        setLoading(true);
        setError('');
        const result = await login(email, password);
        if (!result.success) {
            setError(result.error);
        }
        setLoading(false);
    };

    return (
        <div className={styles.container}>
            <div className={styles.background}>
                <div className={styles.shape}></div>
                <div className={styles.shape}></div>
            </div>

            <Card className={styles.loginCard}>
                <div className={styles.header}>
                    <Title level={2} style={{ marginBottom: 0 }}>
                        Dashboard Performance
                    </Title>
                    <Text type="secondary">Professional Analytics Platform</Text>
                </div>

                {error && (
                    <Alert
                        message="Login Failed"
                        description={error}
                        type="error"
                        closable
                        onClose={() => setError('')}
                        style={{ marginBottom: 24 }}
                    />
                )}

                <Form
                    name="login"
                    onFinish={onFinish}
                    layout="vertical"
                    size="large"
                >
                    <Form.Item
                        name="email"
                        rules={[
                            { required: true, message: 'Please input your email!' },
                            { type: 'email', message: 'Please enter a valid email!' }
                        ]}
                    >
                        <Input
                            prefix={<UserOutlined />}
                            placeholder="Email"
                        />
                    </Form.Item>

                    <Form.Item
                        name="password"
                        rules={[{ required: true, message: 'Please input your password!' }]}
                    >
                        <Input.Password
                            prefix={<LockOutlined />}
                            placeholder="Password"
                        />
                    </Form.Item>

                    <Form.Item>
                        <Button
                            type="primary"
                            htmlType="submit"
                            loading={loading}
                            block
                            size="large"
                            icon={<LoginOutlined />}
                        >
                            Sign In
                        </Button>
                    </Form.Item>
                </Form>

                <Divider>Demo Accounts</Divider>

                <Space direction="vertical" style={{ width: '100%' }} size="small">
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        Quick login for demo:
                    </Text>

                    <Button
                        block
                        onClick={() => quickLogin('admin@company.com', 'admin123')}
                        loading={loading}
                        style={{ textAlign: 'left' }}
                    >
                        <Space>
                            <Tag color="red">Admin</Tag>
                            <Text>All Regions Access</Text>
                        </Space>
                    </Button>

                    <Button
                        block
                        onClick={() => quickLogin('user-a@company.com', 'password123')}
                        loading={loading}
                        style={{ textAlign: 'left' }}
                    >
                        <Space>
                            <Tag color="blue">Region A</Tag>
                            <Text>Region A Only</Text>
                        </Space>
                    </Button>

                    <Button
                        block
                        onClick={() => quickLogin('user-b@company.com', 'password123')}
                        loading={loading}
                        style={{ textAlign: 'left' }}
                    >
                        <Space>
                            <Tag color="green">Region B</Tag>
                            <Text>Region B Only</Text>
                        </Space>
                    </Button>

                    <Button
                        block
                        onClick={() => quickLogin('user-c@company.com', 'password123')}
                        loading={loading}
                        style={{ textAlign: 'left' }}
                    >
                        <Space>
                            <Tag color="orange">Region C</Tag>
                            <Text>Region C Only</Text>
                        </Space>
                    </Button>
                </Space>

                <Divider />

                <Paragraph type="secondary" style={{ fontSize: '12px', textAlign: 'center', marginBottom: 0 }}>
                    Row-Level Security Demo • Each user sees only their region's data
                </Paragraph>
            </Card>
        </div>
    );
};

export default Login;
