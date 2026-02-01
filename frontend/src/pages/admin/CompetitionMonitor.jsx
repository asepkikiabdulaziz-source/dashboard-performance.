import React, { useState, useEffect, useMemo } from 'react';
import {
    Card,
    Typography,
    Table,
    Tabs,
    Tag,
    Row,
    Col,
    Statistic,
    Spin,
    Badge,
    App,
    Empty,
    Button
} from 'antd';
import {
    TrophyOutlined,
    CrownOutlined,
    RiseOutlined,
    FallOutlined,
    SafetyCertificateOutlined,
    WarningOutlined,
    GoldOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../api';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const CompetitionMonitor = () => {
    const { user } = useAuth();
    const { message: messageApi } = App.useApp();

    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('ass'); // ass, bm, rbm
    const [data, setData] = useState([]);

    useEffect(() => {
        fetchData(activeTab);
    }, [activeTab]);

    const fetchData = async (level) => {
        setLoading(true);
        try {
            const response = await api.get(`/api/dashboard/competition/${level}`);
            setData(response.data.data || []);
        } catch (error) {
            console.error(error);
            messageApi.error('Failed to load competition data');
        } finally {
            setLoading(false);
        }
    };

    // Process data for Podium (Top 3) and List (Rest)
    const { top3, rest } = useMemo(() => {
        // Sort by rank just in case
        const sorted = [...data].sort((a, b) => a.rank - b.rank);
        return {
            top3: sorted.slice(0, 3),
            rest: sorted.slice(3)
        };
    }, [data]);

    const columns = [
        {
            title: 'Rank',
            dataIndex: 'rank',
            key: 'rank',
            width: 80,
            align: 'center',
            render: (rank) => {
                let color = '#d9d9d9';
                if (rank === 1) color = '#FFD700'; // Gold
                if (rank === 2) color = '#C0C0C0'; // Silver
                if (rank === 3) color = '#CD7F32'; // Bronze

                if (rank <= 3) {
                    return <Badge count={<CrownOutlined style={{ color }} />} style={{ backgroundColor: 'transparent' }} />;
                }
                return <Tag color="default">#{rank}</Tag>;
            }
        },
        {
            title: activeTab === 'ass' ? 'Area / Name' : (activeTab === 'bm' ? 'Branch' : 'Regional'),
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (
                <div>
                    <Text strong>{text}</Text>
                    {record.region && <div style={{ fontSize: '11px', color: '#8c8c8c' }}>{record.region}</div>}
                </div>
            )
        },
        {
            title: 'Omset Ach%',
            dataIndex: 'omset_ach',
            key: 'omset_ach',
            align: 'right',
            render: (val) => {
                const color = val >= 100 ? '#3f8600' : '#cf1322';
                return <Text style={{ color }} strong>{val?.toFixed(2)}%</Text>;
            },
            sorter: (a, b) => a.omset_ach - b.omset_ach
        },
        {
            title: 'ROA Ach%',
            dataIndex: 'roa_ach',
            key: 'roa_ach',
            align: 'right',
            render: (val) => (
                <Text>{val?.toFixed(2)}%</Text>
            ),
            sorter: (a, b) => a.roa_ach - b.roa_ach
        },
        {
            title: 'Total Points',
            dataIndex: 'total_point',
            key: 'total_point',
            align: 'center',
            render: (val) => <Tag color="blue">{val?.toLocaleString()}</Tag>,
            sorter: (a, b) => a.total_point - b.total_point
        },
        {
            title: 'Reward / Penalty',
            dataIndex: 'reward',
            key: 'reward',
            align: 'right',
            render: (val) => {
                if (val > 0) {
                    return <Text type="success" strong>+ {val.toLocaleString()}</Text>;
                } else if (val < 0) {
                    return <Text type="danger" strong>{val.toLocaleString()}</Text>;
                }
                return <Text type="secondary">-</Text>;
            },
            sorter: (a, b) => a.reward - b.reward
        }
    ];

    const getPodiumStyle = (rank) => {
        let height = '140px';
        let bg = '#f0f2f5';
        let border = 'none';
        let scale = '1';
        let zIndex = 1;

        if (rank === 1) {
            height = '180px';
            bg = 'linear-gradient(180deg, #fff1b8 0%, #fff 100%)';
            border = '2px solid #FFD700';
            scale = '1.1';
            zIndex = 2;
        } else if (rank === 2) {
            height = '160px';
            bg = 'linear-gradient(180deg, #e6f7ff 0%, #fff 100%)';
            border = '2px solid #C0C0C0';
        } else {
            bg = 'linear-gradient(180deg, #fff7e6 0%, #fff 100%)';
            border = '2px solid #CD7F32';
        }

        return {
            height,
            background: bg,
            border,
            borderRadius: '12px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '16px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            transform: `scale(${scale})`,
            zIndex,
            position: 'relative'
        };
    };

    return (
        <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
            {/* Header Section */}
            <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                <Title level={2} style={{ margin: 0, color: '#1f1f1f' }}>
                    MONITORING KOMPETISI AMO
                </Title>
                <Title level={4} style={{ margin: '8px 0', color: '#1890ff' }}>
                    PERIODE JANUARI 2026
                </Title>
                <div style={{ marginTop: '16px' }}>
                    <Tag icon={<SafetyCertificateOutlined />} color="success">Official Data</Tag>
                    <Tag icon={<RiseOutlined />} color="blue">Live Perfomance</Tag>
                </div>
            </div>

            {/* Tabs & Content */}
            <Card
                bordered={false}
                style={{ borderRadius: '16px', boxShadow: '0 4px 24px rgba(0,0,0,0.05)' }}
                bodyStyle={{ padding: '24px' }}
            >
                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    type="card"
                    size="large"
                    centered
                >
                    <TabPane tab={<span><TrophyOutlined />ASS Ranking</span>} key="ass" />
                    <TabPane tab={<span><GoldOutlined />BM Ranking</span>} key="bm" />
                    <TabPane tab={<span><CrownOutlined />RBM Ranking</span>} key="rbm" />
                </Tabs>

                <Spin spinning={loading}>
                    {/* Podium Section */}
                    {top3.length > 0 && (
                        <div style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'flex-end',
                            height: '240px',
                            gap: '24px',
                            margin: '40px 0 60px 0'
                        }}>
                            {/* Rank 2 */}
                            {top3[1] && (
                                <div style={{ width: '220px', ...getPodiumStyle(2) }}>
                                    <div style={{ position: 'absolute', top: '-15px', background: '#C0C0C0', color: '#fff', padding: '4px 12px', borderRadius: '20px', fontWeight: 'bold' }}>#2</div>
                                    <Text strong style={{ fontSize: '16px', textAlign: 'center' }}>{top3[1].name}</Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>{top3[1].region}</Text>
                                    <div style={{ marginTop: '12px', textAlign: 'center' }}>
                                        <Statistic value={top3[1].total_point} valueStyle={{ fontSize: '20px', color: '#1f1f1f' }} suffix="pts" />
                                    </div>
                                    <Tag color="success" style={{ marginTop: '8px' }}>+ {top3[1].reward?.toLocaleString()}</Tag>
                                </div>
                            )}

                            {/* Rank 1 */}
                            {top3[0] && (
                                <div style={{ width: '260px', ...getPodiumStyle(1) }}>
                                    <div style={{ position: 'absolute', top: '-20px', background: '#FFD700', color: '#fff', padding: '6px 16px', borderRadius: '20px', fontWeight: 'bold', fontSize: '16px', boxShadow: '0 4px 8px rgba(255, 215, 0, 0.4)' }}>
                                        <CrownOutlined /> #1
                                    </div>
                                    <Text strong style={{ fontSize: '20px', textAlign: 'center', marginTop: '12px' }}>{top3[0].name}</Text>
                                    <Text type="secondary" style={{ fontSize: '13px' }}>{top3[0].region}</Text>
                                    <div style={{ marginTop: '16px', textAlign: 'center' }}>
                                        <Statistic value={top3[0].total_point} valueStyle={{ fontSize: '28px', color: '#cf1322', fontWeight: 'bold' }} suffix="pts" />
                                    </div>
                                    <Tag color="gold" style={{ marginTop: '12px', padding: '4px 12px', fontSize: '14px' }}>🏆 + {top3[0].reward?.toLocaleString()}</Tag>
                                </div>
                            )}

                            {/* Rank 3 */}
                            {top3[2] && (
                                <div style={{ width: '220px', ...getPodiumStyle(3) }}>
                                    <div style={{ position: 'absolute', top: '-15px', background: '#CD7F32', color: '#fff', padding: '4px 12px', borderRadius: '20px', fontWeight: 'bold' }}>#3</div>
                                    <Text strong style={{ fontSize: '16px', textAlign: 'center' }}>{top3[2].name}</Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>{top3[2].region}</Text>
                                    <div style={{ marginTop: '12px', textAlign: 'center' }}>
                                        <Statistic value={top3[2].total_point} valueStyle={{ fontSize: '20px', color: '#1f1f1f' }} suffix="pts" />
                                    </div>
                                    <Tag color="success" style={{ marginTop: '8px' }}>+ {top3[2].reward?.toLocaleString()}</Tag>
                                </div>
                            )}
                        </div>
                    )}

                    {top3.length === 0 && !loading && <Empty description="No data found for this category" />}

                    {/* Full Table */}
                    <Table
                        dataSource={data}
                        columns={columns}
                        rowKey="rank"
                        pagination={{ pageSize: 50 }}
                        className="competition-table"
                        rowClassName={(record) => {
                            if (record.reward < 0) return 'row-penalty';
                            if (record.rank <= 3) return 'row-top3';
                            return '';
                        }}
                    />

                    {/* Styles for Table Highlight */}
                    <style>{`
                        .row-penalty {
                            background-color: #fff1f0;
                        }
                        .row-penalty:hover > td {
                            background-color: #ffccc7 !important;
                        }
                        .row-top3 {
                            background-color: #f6ffed;
                        }
                    `}</style>
                </Spin>
            </Card>
        </div>
    );
};

export default CompetitionMonitor;
