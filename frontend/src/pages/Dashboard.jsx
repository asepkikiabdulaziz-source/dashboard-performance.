import { useState, useEffect } from 'react';
import {
    Layout,
    Card,
    Row,
    Col,
    Statistic,
    Button,
    Space,
    Typography,
    Tag,
    DatePicker,
    Spin,
    message,
    Avatar
} from 'antd';
import {
    ArrowUpOutlined,
    ArrowDownOutlined,
    LogoutOutlined,
    DollarOutlined,
    TrophyOutlined,
    RiseOutlined,
    ThunderboltOutlined,
    UserOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import api from '../api';
import SalesChart from '../components/Charts/SalesChart';
import TargetChart from '../components/Charts/TargetChart';
import ForecastChart from '../components/Charts/ForecastChart';
import RegionComparison from '../components/Charts/RegionComparison';
import styles from '../styles/Dashboard.module.css';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const Dashboard = () => {
    const { user, logout } = useAuth();
    const [loading, setLoading] = useState(true);
    const [kpis, setKpis] = useState(null);
    const [salesData, setSalesData] = useState([]);
    const [targetData, setTargetData] = useState([]);
    const [forecastData, setForecastData] = useState([]);
    const [regionComparison, setRegionComparison] = useState([]);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [kpisRes, salesRes, targetRes, forecastRes] = await Promise.all([
                api.get('/dashboard/kpis'),
                api.get('/dashboard/sales'),
                api.get('/dashboard/targets'),
                api.get('/dashboard/forecast')
            ]);

            setKpis(kpisRes.data);
            setSalesData(salesRes.data);
            setTargetData(targetRes.data);
            setForecastData(forecastRes.data);

            // Only fetch region comparison for admin
            if (user.region === 'ALL') {
                const regionRes = await api.get('/dashboard/region-comparison');
                setRegionComparison(regionRes.data);
            }
        } catch (error) {
            message.error('Failed to fetch dashboard data');
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0,
        }).format(value);
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <Spin size="large" />
            </div>
        );
    }

    return (
        <Layout className={styles.layout}>
            <Content className={styles.content}>
                <div className={styles.container}>
                    {/* Page Header */}
                    <div className={styles.pageHeader}>
                        <div>
                            <Title level={2} style={{ marginBottom: 8 }}>
                                Sales Dashboard
                            </Title>
                            <Text type="secondary">
                                {user.region === 'ALL'
                                    ? 'Overview of all regions'
                                    : `Region ${user.region} Performance`}
                            </Text>
                        </div>
                        <Space>
                            <Button type="primary" onClick={fetchData}>
                                Refresh Data
                            </Button>
                        </Space>
                    </div>

                    {/* KPI Cards */}
                    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                        <Col xs={24} sm={12} lg={6}>
                            <Card className={styles.kpiCard}>
                                <Statistic
                                    title="Total Revenue"
                                    value={kpis ? kpis.total_revenue : 0}
                                    prefix={<DollarOutlined style={{ color: '#1890ff' }} />}
                                    formatter={(value) => formatCurrency(value)}
                                    valueStyle={{ color: '#1890ff' }}
                                />
                            </Card>
                        </Col>

                        <Col xs={24} sm={12} lg={6}>
                            <Card className={styles.kpiCard}>
                                <Statistic
                                    title="Achievement Rate"
                                    value={kpis ? kpis.achievement_rate : 0}
                                    prefix={<TrophyOutlined style={{ color: (kpis?.achievement_rate || 0) >= 100 ? '#52c41a' : '#faad14' }} />}
                                    suffix="%"
                                    valueStyle={{ color: (kpis?.achievement_rate || 0) >= 100 ? '#52c41a' : '#faad14' }}
                                />
                            </Card>
                        </Col>

                        <Col xs={24} sm={12} lg={6}>
                            <Card className={styles.kpiCard}>
                                <Statistic
                                    title="Growth Rate"
                                    value={Math.abs(kpis?.growth_rate || 0)}
                                    prefix={(kpis?.growth_rate || 0) >= 0 ? (
                                        <ArrowUpOutlined style={{ color: '#52c41a' }} />
                                    ) : (
                                        <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
                                    )}
                                    suffix="%"
                                    valueStyle={{ color: (kpis?.growth_rate || 0) >= 0 ? '#52c41a' : '#ff4d4f' }}
                                />
                            </Card>
                        </Col>

                        <Col xs={24} sm={12} lg={6}>
                            <Card className={styles.kpiCard}>
                                <Statistic
                                    title="Next Month Forecast"
                                    value={kpis ? kpis.next_month_forecast : 0}
                                    prefix={<ThunderboltOutlined style={{ color: '#722ed1' }} />}
                                    formatter={(value) => formatCurrency(value)}
                                    valueStyle={{ color: '#722ed1' }}
                                />
                            </Card>
                        </Col>
                    </Row>

                    {/* Charts Row 1 */}
                    <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                        <Col xs={24} lg={12}>
                            <Card title="Sales Revenue Trend" className={styles.chartCard}>
                                <SalesChart data={salesData} />
                            </Card>
                        </Col>

                        <Col xs={24} lg={12}>
                            <Card title="Target vs Actual" className={styles.chartCard}>
                                <TargetChart data={targetData} />
                            </Card>
                        </Col>
                    </Row>

                    {/* Charts Row 2 */}
                    <Row gutter={[16, 16]}>
                        <Col xs={24}>
                            <Card title="13-Week Forecast" className={styles.chartCard}>
                                <ForecastChart
                                    historicalData={salesData}
                                    forecastData={forecastData}
                                />
                            </Card>
                        </Col>
                    </Row>

                    {/* Region Comparison (Admin Only) */}
                    {user.region === 'ALL' && regionComparison.length > 0 && (
                        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                            <Col xs={24}>
                                <Card title="Region Comparison" className={styles.chartCard}>
                                    <RegionComparison data={regionComparison} />
                                </Card>
                            </Col>
                        </Row>
                    )}
                </div>
            </Content>
        </Layout>
    );
};

export default Dashboard;
