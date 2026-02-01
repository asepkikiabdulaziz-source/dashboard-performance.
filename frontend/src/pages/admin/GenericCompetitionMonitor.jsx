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
    Button,
    Select,
    Alert
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
import '../../styles/CompetitionMonitor.css';
import nabatiLogo from '../../assets/logo_nabati.png';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const GenericCompetitionMonitor = ({ competitionId, title, period, embedded = false }) => {
    const { user } = useAuth();
    const { message: messageApi } = App.useApp();

    // Default tab based on role
    const [activeTab, setActiveTab] = useState(() => {
        const role = user?.role?.toLowerCase();
        if (user?.region === 'ALL') return 'rbm'; // National scope sees everything, RBM is highest
        if (role === 'ass') return 'ass';
        if (role === 'bm') return 'bm';
        if (role === 'rbm') return 'rbm';
        return 'ass';
    });

    const [loading, setLoading] = useState(false);
    const [data, setData] = useState([]);
    const [metadata, setMetadata] = useState({ tgl_update: null, ideal: null });

    // Reset data when competition changes
    useEffect(() => {
        setData([]);
        setActiveTab('ass');
    }, [competitionId]);

    useEffect(() => {
        if (competitionId) {
            fetchData(competitionId, activeTab);
        }
    }, [competitionId, activeTab]);

    // Reset filters and fetch when switching tabs
    useEffect(() => {
        setSelectedRegion('ALL');
        setSelectedZonaBM('ALL');
        setSelectedZonaRBM('ALL');
        if (competitionId) {
            fetchData(competitionId, activeTab, 'ALL');
        }
    }, [activeTab]);

    const fetchData = async (compId, level, regionOverride = null) => {
        setLoading(true);
        try {
            // Use override or selectedRegion
            const region = regionOverride !== null ? regionOverride : selectedRegion;
            const url = `/dashboard/competition/${compId}/${level}${region !== 'ALL' ? `?region=${encodeURIComponent(region)}` : ''}`;

            const response = await api.get(url);
            const rawData = response.data.data || [];

            if (response.data.metadata) {
                setMetadata(response.data.metadata);
            }

            const processedData = rawData.map((item, index) => ({
                ...item,
                key: `${item.name}_${item.region}_${index}`
            }));

            setData(processedData);
        } catch (error) {
            console.error(error);
            messageApi.error('Failed to load competition data');
        } finally {
            setLoading(false);
        }
    };

    // Region/Zone Filter State
    const [selectedRegion, setSelectedRegion] = useState('ALL');
    const [selectedZonaBM, setSelectedZonaBM] = useState('ALL');
    const [selectedZonaRBM, setSelectedZonaRBM] = useState('ALL');

    const regions = useMemo(() => {
        const unique = [...new Set(data.map(item => item.region).filter(Boolean))];
        return ['ALL', ...unique.sort()];
    }, [data]);

    const zonasBM = useMemo(() => {
        const unique = [...new Set(data.map(item => item.zona_bm).filter(Boolean))];
        return ['ALL', ...unique.sort()];
    }, [data]);

    const zonasRBM = useMemo(() => {
        const unique = [...new Set(data.map(item => item.zona_rbm).filter(Boolean))];
        return ['ALL', ...unique.sort()];
    }, [data]);

    // Derived Data (Filtered)
    const filteredData = useMemo(() => {
        let result = data;

        // ASS: filter by REGION
        if (activeTab === 'ass' && selectedRegion !== 'ALL') {
            result = result.filter(item => item.region === selectedRegion);
        }

        // BM: filter by ZONA_BM
        if (activeTab === 'bm' && selectedZonaBM !== 'ALL') {
            result = result.filter(item => item.zona_bm === selectedZonaBM);
        }

        // RBM: filter by ZONA_RBM
        if (activeTab === 'rbm' && selectedZonaRBM !== 'ALL') {
            result = result.filter(item => item.zona_rbm === selectedZonaRBM);
        }

        return result.sort((a, b) => a.rank - b.rank);
    }, [data, selectedRegion, selectedZonaBM, selectedZonaRBM, activeTab]);

    // Process data for Podium (Top 3) and List (Rest)
    const { top3, rest } = useMemo(() => {
        const sorted = [...filteredData]; // Use filtered data
        return {
            top3: sorted.slice(0, 3),
            rest: sorted.slice(3)
        };
    }, [filteredData]);

    // Specific columns for ASS and BM based on user request
    const columns = useMemo(() => {
        if (activeTab === 'ass') {
            return [
                {
                    title: 'Rank',
                    dataIndex: 'rank',
                    key: 'rank',
                    width: 70,
                    align: 'center',
                    render: (rank) => {
                        if (rank === 1) return <Badge count={<CrownOutlined style={{ color: '#FFD700' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 2) return <Badge count={<CrownOutlined style={{ color: '#C0C0C0' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 3) return <Badge count={<CrownOutlined style={{ color: '#CD7F32' }} />} style={{ backgroundColor: 'transparent' }} />;
                        return <Tag color="default">#{rank}</Tag>;
                    }
                },
                {
                    title: 'NIK',
                    dataIndex: 'nik',
                    key: 'nik',
                    render: (val) => <Text type="secondary" style={{ fontSize: '12px' }}>{val}</Text>
                },
                {
                    title: 'Nama ASS',
                    dataIndex: 'name', // Mapped from NAMA_ASS in backend
                    key: 'name',
                    render: (val) => <Text strong>{val}</Text>
                },
                {
                    title: 'Cabang',
                    dataIndex: 'cabang',
                    key: 'cabang',
                    render: (val, record) => (
                        <div>
                            <Text>{val}</Text>
                            <div style={{ fontSize: '10px', color: '#8c8c8c' }}>{record.region}</div>
                        </div>
                    )
                },
                {
                    title: 'Total Point',
                    dataIndex: 'total_point',
                    key: 'total_point',
                    align: 'center',
                    render: (val) => <Tag color="blue" style={{ fontSize: '14px', padding: '4px 10px' }}>{val?.toLocaleString()}</Tag>,
                    sorter: (a, b) => a.total_point - b.total_point
                },
                {
                    title: 'Reward',
                    dataIndex: 'reward',
                    key: 'reward',
                    align: 'right',
                    render: (val) => {
                        const style = { fontWeight: 'bold' };
                        if (val > 0) return <Text type="success" style={style}>+ {val.toLocaleString()}</Text>;
                        if (val < 0) return <Text type="danger" style={style}>{val.toLocaleString()}</Text>;
                        return <Text type="secondary">-</Text>;
                    },
                    sorter: (a, b) => a.reward - b.reward
                }
            ];
        }

        if (activeTab === 'bm') {
            return [
                {
                    title: 'Rank',
                    dataIndex: 'rank',
                    key: 'rank',
                    width: 70,
                    align: 'center',
                    render: (rank) => {
                        if (rank === 1) return <Badge count={<CrownOutlined style={{ color: '#FFD700' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 2) return <Badge count={<CrownOutlined style={{ color: '#C0C0C0' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 3) return <Badge count={<CrownOutlined style={{ color: '#CD7F32' }} />} style={{ backgroundColor: 'transparent' }} />;
                        return <Tag color="default">#{rank}</Tag>;
                    }
                },
                {
                    title: 'Cabang',
                    dataIndex: 'cabang',
                    key: 'cabang',
                    render: (val) => <Text strong>{val}</Text>
                },
                {
                    title: 'Region',
                    dataIndex: 'region',
                    key: 'region',
                    render: (val, record) => (
                        <div>
                            <Text>{val}</Text>
                            <div style={{ fontSize: '10px', color: '#8c8c8c' }}>{record.zona_bm}</div>
                        </div>
                    )
                },
                {
                    title: 'Total Point',
                    dataIndex: 'total_point',
                    key: 'total_point',
                    align: 'center',
                    render: (val) => <Tag color="blue" style={{ fontSize: '14px', padding: '4px 10px' }}>{val?.toLocaleString()}</Tag>,
                    sorter: (a, b) => a.total_point - b.total_point
                },
                {
                    title: 'Reward',
                    dataIndex: 'reward',
                    key: 'reward',
                    align: 'right',
                    render: (val) => {
                        const style = { fontWeight: 'bold' };
                        if (val > 0) return <Text type="success" style={style}>+ {val.toLocaleString()}</Text>;
                        if (val < 0) return <Text type="danger" style={style}>{val.toLocaleString()}</Text>;
                        return <Text type="secondary">-</Text>;
                    },
                    sorter: (a, b) => a.reward - b.reward
                }
            ];
        }

        if (activeTab === 'rbm') {
            return [
                {
                    title: 'Rank',
                    dataIndex: 'rank',
                    key: 'rank',
                    width: 70,
                    align: 'center',
                    render: (rank) => {
                        if (rank === 1) return <Badge count={<CrownOutlined style={{ color: '#FFD700' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 2) return <Badge count={<CrownOutlined style={{ color: '#C0C0C0' }} />} style={{ backgroundColor: 'transparent' }} />;
                        if (rank === 3) return <Badge count={<CrownOutlined style={{ color: '#CD7F32' }} />} style={{ backgroundColor: 'transparent' }} />;
                        return <Tag color="default">#{rank}</Tag>;
                    }
                },
                {
                    title: 'Region',
                    dataIndex: 'region',
                    key: 'region',
                    render: (val) => <Text>{val}</Text>
                },
                {
                    title: 'Total Point',
                    dataIndex: 'total_point',
                    key: 'total_point',
                    align: 'center',
                    render: (val) => <Tag color="blue" style={{ fontSize: '14px', padding: '4px 10px' }}>{val?.toLocaleString()}</Tag>,
                    sorter: (a, b) => a.total_point - b.total_point
                },
                {
                    title: 'Reward',
                    dataIndex: 'reward',
                    key: 'reward',
                    align: 'right',
                    render: (val) => {
                        const style = { fontWeight: 'bold' };
                        if (val > 0) return <Text type="success" style={style}>+ {val.toLocaleString()}</Text>;
                        if (val < 0) return <Text type="danger" style={style}>{val.toLocaleString()}</Text>;
                        return <Text type="secondary">-</Text>;
                    },
                    sorter: (a, b) => a.reward - b.reward
                }
            ];
        }

        // Fallback for BM/RBM (Original columns)
        return [
            {
                title: 'Rank',
                dataIndex: 'rank',
                key: 'rank',
                width: 80,
                align: 'center',
                render: (rank) => <Tag color="default">#{rank}</Tag>
            },
            {
                title: activeTab === 'bm' ? 'Branch' : 'Regional',
                dataIndex: 'name',
                key: 'name',
                render: (text, record) => (
                    <div>
                        <Text strong>{text}</Text>
                        <div style={{ fontSize: '11px', color: '#8c8c8c' }}>{record.region}</div>
                    </div>
                )
            },
            {
                title: 'Omset Ach',
                dataIndex: 'omset_ach',
                key: 'omset_ach',
                align: 'right',
                render: (val) => <Text>{val?.toFixed(2)}%</Text>
            },
            {
                title: 'Total Point',
                dataIndex: 'total_point',
                key: 'total_point',
                align: 'center',
                render: (val) => <Tag color="blue">{val?.toLocaleString()}</Tag>
            },
            {
                title: 'Reward',
                dataIndex: 'reward',
                key: 'reward',
                align: 'right',
                render: (val) => {
                    if (val > 0) return <Text type="success">+ {val.toLocaleString()}</Text>;
                    if (val < 0) return <Text type="danger">{val.toLocaleString()}</Text>;
                    return <Text type="secondary">-</Text>;
                }
            }
        ];
    }, [activeTab]);

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

    if (!competitionId) {
        return <Empty description="Select a competition" />;
    }

    const content = (
        <>
            {!embedded && (
                <div className="competition-header">
                    <div style={{ textAlign: 'center', marginBottom: '40px' }}>
                        <Title level={2} style={{ margin: 0, color: '#1f1f1f' }}>
                            {title || 'COMPETITION LEADERBOARD'}
                        </Title>
                        <h4 style={{ color: '#1890ff', margin: '8px 0' }}>{period}</h4>
                        <div style={{ marginTop: '16px' }}>
                            {metadata.tgl_update && (
                                <Tag color="purple">Update: {metadata.tgl_update}</Tag>
                            )}
                            {metadata.ideal && (
                                <Tag color="cyan">Target Ideal: {(metadata.ideal * 100).toFixed(2)}%</Tag>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* User Context Contextual Info */}
            {user && (
                <div style={{ marginBottom: '16px', maxWidth: '1200px', margin: '0 auto 16px auto' }}>
                    <Alert
                        message={
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span>
                                    Viewing as: <Text strong>{user.role?.toUpperCase()}</Text>
                                    {user.name && <Text style={{ marginLeft: 8 }}>({user.name})</Text>}
                                </span>
                                {user.region && (
                                    <Tag color="blue" style={{ borderRadius: '12px' }}>
                                        Scope: {user.region}
                                    </Tag>
                                )}
                            </div>
                        }
                        type="info"
                        showIcon
                        icon={<SafetyCertificateOutlined />}
                        style={{ borderRadius: '12px', background: 'rgba(230, 247, 255, 0.7)', backdropFilter: 'blur(10px)', border: '1px solid #91d5ff' }}
                    />
                </div>
            )}

            {/* Tabs & Content */}
            {!embedded ? (
                <Card
                    className="competition-card"
                    variant="borderless"
                    style={{ borderRadius: '16px', boxShadow: '0 4px 24px rgba(0,0,0,0.05)' }}
                    styles={{ body: { padding: '24px' } }}
                >
                    <Tabs
                        activeKey={activeTab}
                        onChange={setActiveTab}
                        type="card"
                        size="large"
                        centered
                        items={[
                            { key: 'ass', label: <span><TrophyOutlined />ASS Ranking</span> },
                            ...(user?.role?.toLowerCase() !== 'ass' || user?.region === 'ALL' || user?.role?.toLowerCase() === 'super_admin' || user?.role?.toLowerCase() === 'admin' ? [
                                { key: 'bm', label: <span><GoldOutlined />BM Ranking</span> }
                            ] : []),
                            ...(user?.role?.toLowerCase() === 'rbm' || user?.region === 'ALL' || user?.role?.toLowerCase() === 'super_admin' || user?.role?.toLowerCase() === 'admin' ? [
                                { key: 'rbm', label: <span><CrownOutlined />RBM Ranking</span> }
                            ] : [])
                        ]}
                    />

                    {/* Region/Zone Filter for ASS/BM */}
                    {activeTab === 'ass' && (
                        <div style={{ margin: '16px 0', textAlign: 'right' }}>
                            <span style={{ marginRight: '8px', color: '#595959' }}>Filter Region:</span>
                            <Select
                                value={selectedRegion}
                                onChange={setSelectedRegion}
                                style={{ width: 200 }}
                                options={regions.map(r => ({ label: r || "N/A", value: r || "" }))}
                            />
                        </div>
                    )
                    }

                    {
                        activeTab === 'bm' && (
                            <div style={{ margin: '16px 0', textAlign: 'right' }}>
                                <span style={{ marginRight: '8px', color: '#595959' }}>Filter Zona BM:</span>
                                <Select
                                    value={selectedZonaBM}
                                    onChange={setSelectedZonaBM}
                                    style={{ width: 200 }}
                                    options={zonasBM.map(z => ({ label: z || "N/A", value: z || "" }))}
                                />
                            </div>
                        )
                    }

                    {
                        activeTab === 'rbm' && (
                            <div style={{ margin: '16px 0', textAlign: 'right' }}>
                                <span style={{ marginRight: '8px', color: '#595959' }}>Filter Zona RBM:</span>
                                <Select
                                    value={selectedZonaRBM}
                                    onChange={setSelectedZonaRBM}
                                    style={{ width: 200 }}
                                    options={zonasRBM.map(z => ({ label: z || "N/A", value: z || "" }))}
                                />
                            </div>
                        )
                    }

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
                            dataSource={filteredData}
                            columns={columns}
                            pagination={{ pageSize: 50 }}
                            className="competition-table"

                            // Expandable Row for Detail Breakdown
                            expandable={{
                                expandedRowRender: (record) => (
                                    <div style={{ padding: '16px', background: '#fafafa', borderRadius: '8px' }}>
                                        <h4 style={{ margin: '0 0 12px 0', color: '#1890ff' }}>Point Breakdown Calculation</h4>
                                        <Row gutter={[24, 24]}>
                                            <Col span={8}>
                                                <Card size="small" title="Omset Point" variant="borderless">
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Target:</Text>
                                                        <Text>{record.target?.toLocaleString()}</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Omset:</Text>
                                                        <Text strong>{record.omset?.toLocaleString()}</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Achievement:</Text>
                                                        <Text strong style={{ color: record.omset_ach >= 100 ? '#3f8600' : '#cf1322' }}>
                                                            {record.omset_ach?.toFixed(2)}%
                                                        </Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                        <Text type="secondary">Points:</Text>
                                                        <Tag color="geekblue" style={{ fontSize: '14px' }}>+{record.point_oms}</Tag>
                                                    </div>
                                                </Card>
                                            </Col>
                                            <Col span={8}>
                                                <Card size="small" title="ROA Point" variant="borderless">
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">CB:</Text>
                                                        <Text>{record.cb?.toLocaleString()}</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Act ROA:</Text>
                                                        <Text strong>{record.act_roa?.toLocaleString()}</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Achievement:</Text>
                                                        <Text strong>{record.roa_ach?.toFixed(2)}%</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                        <Text type="secondary">Points:</Text>
                                                        <Tag color="purple" style={{ fontSize: '14px' }}>+{record.point_roa}</Tag>
                                                    </div>
                                                </Card>
                                            </Col>
                                            <Col span={8}>
                                                <Card size="small" title="ROA 10 Krt Point" variant="borderless">
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                        <Text type="secondary">Total ROA 10 Krt:</Text>
                                                        <Text strong>{record.total_roa_10krt?.toLocaleString()}</Text>
                                                    </div>
                                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                        <Text type="secondary">Points:</Text>
                                                        <Tag color="cyan" style={{ fontSize: '14px' }}>+{record.point_roa_10krt}</Tag>
                                                    </div>
                                                </Card>
                                            </Col>
                                        </Row>
                                        <div style={{ marginTop: '16px', textAlign: 'right', borderTop: '1px solid #f0f0f0', paddingTop: '12px' }}>
                                            <Text>Total Points: </Text>
                                            <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>{record.total_point}</Text>
                                        </div>
                                    </div>
                                ),
                                rowExpandable: (record) => activeTab === 'ass' || activeTab === 'bm' || activeTab === 'rbm', // Expandable for all tabs
                            }}

                            rowClassName={(record) => {
                                if (record.rank === 1) return 'top-1-row';
                                if (record.rank === 2) return 'top-2-row';
                                if (record.rank === 3) return 'top-3-row';
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
            ) : null}
        </>
    );

    if (embedded) {
        return (
            <>
                {/* Professional Header - Matching Grand Prize Style */}
                <div style={{
                    marginBottom: '24px',
                    padding: '16px 32px',
                    background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #1e40af 100%)',
                    borderRadius: '12px',
                    boxShadow: '0 4px 16px rgba(30, 58, 138, 0.2)',
                    position: 'relative',
                    overflow: 'hidden',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                }}>
                    {/* Background Pattern with Gradation */}
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        background: 'radial-gradient(circle at 20% 50%, rgba(255, 255, 255, 0.1) 0%, transparent 40%), radial-gradient(circle at 80% 50%, rgba(59, 130, 246, 0.3) 0%, transparent 50%)',
                        pointerEvents: 'none'
                    }} />

                    {/* Logo on Left */}
                    <div style={{ position: 'relative', zIndex: 1, flex: '0 0 auto' }}>
                        <img
                            src={nabatiLogo}
                            alt="Nabati"
                            style={{
                                height: '40px'
                            }}
                        />
                    </div>

                    {/* Title Section - Centered */}
                    <div style={{ position: 'relative', zIndex: 1, flex: '1 1 auto', textAlign: 'center' }}>
                        <h1 style={{
                            color: 'white',
                            fontSize: '22px',
                            fontWeight: 700,
                            margin: '0 0 2px 0',
                            letterSpacing: '0.5px',
                            textTransform: 'uppercase'
                        }}>
                            {title || 'MONITORING KOMPETISI AMO'}
                        </h1>
                        <p style={{
                            color: 'rgba(255,255,255,0.95)',
                            fontSize: '13px',
                            margin: 0,
                            fontWeight: 500,
                            letterSpacing: '0.3px'
                        }}>
                            {period || 'PERIODE TIDAK DIKETAHUI'}
                        </p>
                    </div>

                    {/* Empty space on right for balance */}
                    <div style={{ flex: '0 0 auto', width: '40px' }} />
                </div>

                {/* Metadata Info - Below Header, Right Aligned */}
                {(metadata.tgl_update || metadata.ideal) && (
                    <div style={{
                        display: 'flex',
                        gap: '12px',
                        justifyContent: 'flex-end',
                        marginBottom: '24px'
                    }}>
                        {metadata.tgl_update && (
                            <div style={{
                                background: '#f5f5f5',
                                padding: '10px 16px',
                                borderRadius: '8px',
                                border: '1px solid #e0e0e0'
                            }}>
                                <Text style={{ color: '#666', fontSize: '11px', display: 'block', marginBottom: '2px', textTransform: 'uppercase' }}>Update</Text>
                                <Text style={{ color: '#262626', fontSize: '14px', fontWeight: 600 }}>{metadata.tgl_update}</Text>
                            </div>
                        )}
                        {metadata.ideal && (
                            <div style={{
                                background: '#f5f5f5',
                                padding: '10px 16px',
                                borderRadius: '8px',
                                border: '1px solid #e0e0e0'
                            }}>
                                <Text style={{ color: '#666', fontSize: '11px', display: 'block', marginBottom: '2px', textTransform: 'uppercase' }}>Target Ideal</Text>
                                <Text style={{ color: '#262626', fontSize: '14px', fontWeight: 600 }}>{(metadata.ideal * 100).toFixed(2)}%</Text>
                            </div>
                        )}
                    </div>
                )}

                <Tabs
                    activeKey={activeTab}
                    onChange={setActiveTab}
                    type="card"
                    size="large"
                    centered
                    items={[
                        { key: 'ass', label: <span><TrophyOutlined />ASS Ranking</span> },
                        { key: 'bm', label: <span><GoldOutlined />BM Ranking</span> },
                        { key: 'rbm', label: <span><CrownOutlined />RBM Ranking</span> }
                    ]}
                />

                {/* Region/Zone Filter for ASS/BM */}
                {activeTab === 'ass' && (
                    <div style={{ margin: '16px 0', textAlign: 'right' }}>
                        <span style={{ marginRight: '8px', color: '#595959' }}>Filter Region:</span>
                        <Select
                            value={selectedRegion}
                            onChange={setSelectedRegion}
                            style={{ width: 200 }}
                            options={regions.map(r => ({ label: r || "N/A", value: r || "" }))}
                        />
                    </div>
                )}

                {activeTab === 'bm' && (
                    <div style={{ margin: '16px 0', textAlign: 'right' }}>
                        <span style={{ marginRight: '8px', color: '#595959' }}>Filter Zona BM:</span>
                        <Select
                            value={selectedZonaBM}
                            onChange={setSelectedZonaBM}
                            style={{ width: 200 }}
                            options={zonasBM.map(z => ({ label: z || "N/A", value: z || "" }))}
                        />
                    </div>
                )}

                {activeTab === 'rbm' && (
                    <div style={{ margin: '16px 0', textAlign: 'right' }}>
                        <span style={{ marginRight: '8px', color: '#595959' }}>Filter Zona RBM:</span>
                        <Select
                            value={selectedZonaRBM}
                            onChange={setSelectedZonaRBM}
                            style={{ width: 200 }}
                            options={zonasRBM.map(z => ({ label: z || "N/A", value: z || "" }))}
                        />
                    </div>
                )}

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
                            {/* Same podium code as non-embedded */}
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

                            {top3[0] && (
                                <div style={{ width: '240px', ...getPodiumStyle(1) }}>
                                    <div style={{ position: 'absolute', top: '-15px', background: '#FFD700', color: '#fff', padding: '4px 12px', borderRadius: '20px', fontWeight: 'bold' }}>#1</div>
                                    <Text strong style={{ fontSize: '18px', textAlign: 'center' }}>{top3[0].name}</Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>{top3[0].region}</Text>
                                    <div style={{ marginTop: '12px', textAlign: 'center' }}>
                                        <Statistic value={top3[0].total_point} valueStyle={{ fontSize: '24px', color: '#1f1f1f', fontWeight: 'bold' }} suffix="pts" />
                                    </div>
                                    <Tag color="gold" style={{ marginTop: '8px', fontSize: '14px' }}>+ {top3[0].reward?.toLocaleString()}</Tag>
                                </div>
                            )}

                            {top3[2] && (
                                <div style={{ width: '220px', ...getPodiumStyle(3) }}>
                                    <div style={{ position: 'absolute', top: '-15px', background: '#CD7F32', color: '#fff', padding: '4px 12px', borderRadius: '20px', fontWeight: 'bold' }}>#3</div>
                                    <Text strong style={{ fontSize: '16px', textAlign: 'center' }}>{top3[2].name}</Text>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>{top3[2].region}</Text>
                                    <div style={{ marginTop: '12px', textAlign: 'center' }}>
                                        <Statistic value={top3[2].total_point} valueStyle={{ fontSize: '20px', color: '#1f1f1f' }} suffix="pts" />
                                    </div>
                                    <Tag color="warning" style={{ marginTop: '8px' }}>+ {top3[2].reward?.toLocaleString()}</Tag>
                                </div>
                            )}
                        </div>
                    )}

                    {top3.length === 0 && !loading && <Empty description="No data found for this category" />}

                    {/* Full Table - Same for both modes */}
                    <Table
                        dataSource={filteredData}
                        columns={columns}
                        pagination={{ pageSize: 50 }}
                        className="competition-table"
                        virtual
                        scroll={{ y: 600, x: 1200 }}
                        expandable={{
                            expandedRowRender: (record) => (
                                <div style={{ padding: '16px', background: '#fafafa', borderRadius: '8px' }}>
                                    <h4 style={{ margin: '0 0 12px 0', color: '#1890ff' }}>Point Breakdown Calculation</h4>
                                    <Row gutter={[24, 24]}>
                                        <Col span={8}>
                                            <Card size="small" title="Omset Point" variant="borderless">
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Target:</Text>
                                                    <Text>{record.target?.toLocaleString()}</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Omset:</Text>
                                                    <Text strong>{record.omset?.toLocaleString()}</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Achievement:</Text>
                                                    <Text strong style={{ color: record.omset_ach >= 100 ? '#3f8600' : '#cf1322' }}>
                                                        {record.omset_ach?.toFixed(2)}%
                                                    </Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                    <Text type="secondary">Points:</Text>
                                                    <Tag color="geekblue" style={{ fontSize: '14px' }}>+{record.point_oms}</Tag>
                                                </div>
                                            </Card>
                                        </Col>
                                        <Col span={8}>
                                            <Card size="small" title="ROA Point" variant="borderless">
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">CB:</Text>
                                                    <Text>{record.cb?.toLocaleString()}</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Act ROA:</Text>
                                                    <Text strong>{record.act_roa?.toLocaleString()}</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Achievement:</Text>
                                                    <Text strong>{record.roa_ach?.toFixed(2)}%</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                    <Text type="secondary">Points:</Text>
                                                    <Tag color="purple" style={{ fontSize: '14px' }}>+{record.point_roa}</Tag>
                                                </div>
                                            </Card>
                                        </Col>
                                        <Col span={8}>
                                            <Card size="small" title="ROA 10 Krt Point" variant="borderless">
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                                    <Text type="secondary">Total ROA 10 Krt:</Text>
                                                    <Text strong>{record.total_roa_10krt?.toLocaleString()}</Text>
                                                </div>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #f0f0f0' }}>
                                                    <Text type="secondary">Points:</Text>
                                                    <Tag color="cyan" style={{ fontSize: '14px' }}>+{record.point_roa_10krt}</Tag>
                                                </div>
                                            </Card>
                                        </Col>
                                    </Row>
                                    <div style={{ marginTop: '16px', padding: '12px', background: '#e6f7ff', borderRadius: '4px', borderLeft: '3px solid #1890ff' }}>
                                        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>{record.total_point}</Text>
                                    </div>
                                </div>
                            ),
                            rowExpandable: (record) => activeTab === 'ass' || activeTab === 'bm' || activeTab === 'rbm',
                        }}
                        rowClassName={(record) => {
                            if (record.rank === 1) return 'top-1-row';
                            if (record.rank === 2) return 'top-2-row';
                            if (record.rank === 3) return 'top-3-row';
                            return '';
                        }}
                    />
                </Spin>
            </>
        );
    }

    return (
        <div className="competition-container">
            {content}
        </div>
    );
};

export default GenericCompetitionMonitor;
