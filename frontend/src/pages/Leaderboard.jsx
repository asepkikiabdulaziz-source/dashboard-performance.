import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Table, Select, Input, Tag, Card, Row, Col, Statistic, Progress, Tooltip, Space, Button, Modal, message, Skeleton, Alert, Typography } from 'antd';
import {
    TrophyOutlined,
    SearchOutlined,
    StarFilled,
    DownOutlined,
    RightOutlined,
    FireOutlined,
    RocketOutlined,
    AimOutlined,
    SafetyCertificateOutlined
} from '@ant-design/icons';
import api from '../api';
import '../styles/Leaderboard.css';
import nabatiLogo from '../assets/logo_nabati.png';

const { Option } = Select;
const { Title, Text } = Typography;

const Leaderboard = () => {
    const { user } = useAuth();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Data states
    const [regions, setRegions] = useState([]);
    const [leaderboardData, setLeaderboardData] = useState([]);
    const [cutoffDate, setCutoffDate] = useState(null);

    // Filter states
    const [selectedRegion, setSelectedRegion] = useState(null);
    const [selectedDivision, setSelectedDivision] = useState(null);
    const [searchText, setSearchText] = useState('');

    // Expanded rows state
    const [expandedRowKeys, setExpandedRowKeys] = useState([]);

    // Load initial data
    useEffect(() => {
        loadInitialData();
    }, []);

    // Fetch leaderboard when filters change
    useEffect(() => {
        if (selectedRegion) {
            fetchData();
        }
    }, [selectedRegion, selectedDivision]);

    const loadInitialData = async () => {
        try {
            setLoading(true);

            const regionsResponse = await api.get('/leaderboard/regions');
            const regionsData = regionsResponse.data.regions || [];
            setRegions(regionsData);

            // Get cut-off date
            const cutoffResponse = await api.get('/leaderboard/cutoff-date');
            setCutoffDate(cutoffResponse.data.cutoff_date);

            // Determine initial region
            let initialRegion = null;

            // SUPERADMIN/NATIONAL behavior
            if (user.region === 'ALL') {
                initialRegion = 'ALL';
            } else {
                initialRegion = user.region;
            }

            // Fallback if user region not in list (rare)
            if (!initialRegion && regionsData.length > 0) {
                initialRegion = regionsData[0].code;
            }

            console.log("Setting initial region:", initialRegion);

            // Set region (will trigger useEffect to fetch leaderboard)
            if (initialRegion) {
                setSelectedRegion(initialRegion);
            } else {
                // IMPORTANT: Release loading if no region to trigger fetch
                setLoading(false);
            }

        } catch (err) {
            console.error('Error loading initial data:', err);
            setError('Failed to load initial data. Please try again.');
            setLoading(false);
        }
    };

    // State for Top 1 Modal
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [topSummaryData, setTopSummaryData] = useState([]);
    const [loadingModal, setLoadingModal] = useState(false);

    // Fetch data
    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            // Fetch main leaderboard
            const params = {};
            if (selectedDivision) {
                params.division = selectedDivision;
            }
            if (selectedRegion) {
                params.region = selectedRegion;
            }

            console.log("Fetching with params:", params);
            const response = await api.get('/leaderboard', { params });
            // console.log("Leaderboard API Response:", response); // Removed debug log
            setLeaderboardData(response.data || []);

        } catch (err) {
            console.error("Error fetching data:", err);
            setError('Failed to fetch leaderboard data. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    // Fetch Top 1 Summary for Modal
    const fetchTopSummary = async () => {
        setLoadingModal(true);
        try {
            const response = await api.get('/leaderboard/top-summary');
            setTopSummaryData(response.data || []);
        } catch (err) {
            console.error("Error fetching top summary:", err);
            message.error('Failed to load Top 1 Summary');
        } finally {
            setLoadingModal(false);
        }
    };

    // Handle Modal Open
    const showModal = () => {
        setIsModalVisible(true);
        fetchTopSummary();
    };

    // Get score tier badge
    const getScoreTier = (score) => {
        if (score >= 350) return { label: 'PLATINUM', color: '#b37feb', icon: <StarFilled /> };
        if (score >= 300) return { label: 'GOLD', color: '#faad14', icon: <TrophyOutlined /> };
        if (score >= 250) return { label: 'SILVER', color: '#8c8c8c', icon: <FireOutlined /> };
        if (score >= 200) return { label: 'BRONZE', color: '#d4b896', icon: <RocketOutlined /> };
        return { label: 'BASIC', color: '#d9d9d9', icon: <AimOutlined /> };
    };

    const getRankBadge = (rank) => {
        if (rank === 1) return <span style={{ fontSize: '24px' }}>🥇</span>;
        if (rank === 2) return <span style={{ fontSize: '24px' }}>🥈</span>;
        if (rank === 3) return <span style={{ fontSize: '24px' }}>🥉</span>;
        return <span style={{ fontSize: '18px', fontWeight: 'bold', color: '#666' }}>{rank}</span>;
    };

    // Expandable row render - showing score breakdown
    const expandedRowRender = (record) => {
        const maxScore = 500; // Approximate max possible score

        return (
            <div className="score-breakdown">
                <Row gutter={[16, 16]}>
                    {/* Left Column - OMS Progress */}
                    <Col xs={24} md={12}>
                        <Card size="small" title="💰 OMSET PERFORMANCE" bordered={false}>
                            <div className="score-item">
                                <div className="score-label">OMS P1 (24%)</div>
                                <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px' }}>
                                    Target: Rp {((record.target * 0.24) || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}
                                </div>
                                <Progress
                                    percent={Math.min((record.omset_p1 / (record.target * 0.24) * 100), 100)}
                                    size="small"
                                    strokeColor="#52c41a"
                                    format={() => `Rp ${(record.omset_p1 || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`}
                                />
                                <div className="score-points">Points: {record.pts_omset_p1 || 0} / 50</div>
                            </div>
                            <div className="score-item">
                                <div className="score-label">OMS P2 (49%)</div>
                                <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px' }}>
                                    Target: Rp {((record.target * 0.49) || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}
                                </div>
                                <Progress
                                    percent={Math.min((record.omset_p2 / (record.target * 0.49) * 100), 100)}
                                    size="small"
                                    strokeColor="#1890ff"
                                    format={() => `Rp ${(record.omset_p2 || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`}
                                />
                                <div className="score-points">Points: {record.pts_omset_p2 || 0} / 50</div>
                            </div>
                            <div className="score-item">
                                <div className="score-label">OMS P3 (75%)</div>
                                <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px' }}>
                                    Target: Rp {((record.target * 0.75) || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}
                                </div>
                                <Progress
                                    percent={Math.min((record.omset_p3 / (record.target * 0.75) * 100), 100)}
                                    size="small"
                                    strokeColor="#fa8c16"
                                    format={() => `Rp ${(record.omset_p3 || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`}
                                />
                                <div className="score-points">Points: {record.pts_omset_p3 || 0} / 50</div>
                            </div>
                            <div className="score-item">
                                <div className="score-label">OMS P4 (100%)</div>
                                <div style={{ fontSize: '11px', color: '#999', marginBottom: '4px' }}>
                                    Target: Rp {(record.target || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}
                                </div>
                                <Progress
                                    percent={Math.min((record.omset_p4 / record.target * 100), 100)}
                                    size="small"
                                    strokeColor="#722ed1"
                                    format={() => `Rp ${(record.omset_p4 || 0).toLocaleString('id-ID', { maximumFractionDigits: 0 })}`}
                                />
                                <div className="score-points">Points: {record.pts_omset_p4 || 0} / 50</div>
                            </div>
                        </Card>
                    </Col>

                    {/* Right Column - ROA & Others */}
                    <Col xs={24} md={12}>
                        <Card size="small" title="📊 ROA & METRICS" bordered={false}>
                            <Space direction="vertical" style={{ width: '100%' }} size="small">
                                {/* Total CB at top */}
                                <div style={{
                                    padding: '8px 12px',
                                    background: '#e6f7ff',
                                    borderRadius: '4px',
                                    marginBottom: '8px'
                                }}>
                                    <strong>Total CB: {record.total_customer || 0}</strong>
                                </div>

                                {/* EC Daily */}
                                <div className="metric-row">
                                    <span className="metric-label">EC Daily:</span>
                                    <Tag color="blue">{record.effective_calls || 0}</Tag>
                                    <span className="metric-score">{record.pts_ec || 0} pts</span>
                                </div>

                                {/* ROA P1 */}
                                <div className="metric-row">
                                    <div style={{ width: '100%' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span className="metric-label">ROA P1 Weekly (70%):</span>
                                            <span className="metric-score">Points: {record.pts_roa_p1 ?? 0} / 15</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.7)} |
                                            Actual: <Tag color={record.roa_p1 >= Math.round((record.total_customer || 0) * 0.7) ? 'green' : 'red'}>
                                                {record.roa_p1 || 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>

                                {/* ROA P2 */}
                                <div className="metric-row">
                                    <div style={{ width: '100%' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span className="metric-label">ROA P2 Weekly (90%):</span>
                                            <span className="metric-score">Points: {record.pts_roa_p2 ?? 0} / 15</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.9)} |
                                            Actual: <Tag color={record.roa_p2 >= Math.round((record.total_customer || 0) * 0.9) ? 'green' : 'red'}>
                                                {record.roa_p2 || 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>

                                {/* ROA P3 */}
                                <div className="metric-row">
                                    <div style={{ width: '100%' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span className="metric-label">ROA P3 Weekly (100%):</span>
                                            <span className="metric-score">Points: {record.pts_roa_p3 ?? 0} / 15</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999' }}>
                                            Target: {record.total_customer || 0} |
                                            Actual: <Tag color={record.roa_p3 >= (record.total_customer || 0) ? 'green' : 'red'}>
                                                {record.roa_p3 || 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>

                                {/* ROA PARETO */}
                                <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px dashed #d9d9d9' }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#722ed1' }}>ROA PARETO (3 items × 30 pts each)</div>

                                    {/* WFR-E02K */}
                                    <div style={{ paddingLeft: '12px', marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• WFR-E02K (75%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_WFR_E02K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.75)} |
                                            Actual: <Tag color={record.roa_WFR_E02K >= Math.round((record.total_customer || 0) * 0.75) ? 'green' : 'red'} size="small">
                                                {record.roa_WFR_E02K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>

                                    {/* NXT-E02K */}
                                    <div style={{ paddingLeft: '12px', marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• NXT-E02K (75%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_NXT_E02K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.75)} |
                                            Actual: <Tag color={record.roa_NXT_E02K >= Math.round((record.total_customer || 0) * 0.75) ? 'green' : 'red'} size="small">
                                                {record.roa_NXT_E02K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>

                                    {/* NXC-E02K */}
                                    <div style={{ paddingLeft: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• NXC-E02K (75%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_NXC_E02K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.75)} |
                                            Actual: <Tag color={record.roa_NXC_E02K >= Math.round((record.total_customer || 0) * 0.75) ? 'green' : 'red'} size="small">
                                                {record.roa_NXC_E02K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>

                                {/* ROA PERANG */}
                                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px dashed #d9d9d9' }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#fa541c' }}>ROA PERANG (3 items × 30 pts each)</div>

                                    {/* WFR-E05K */}
                                    <div style={{ paddingLeft: '12px', marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• WFR-E05K (50%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_WFR_E05K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.50)} |
                                            Actual: <Tag color={record.roa_WFR_E05K >= Math.round((record.total_customer || 0) * 0.50) ? 'green' : 'red'} size="small">
                                                {record.roa_WFR_E05K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>

                                    {/* CSD-E02K */}
                                    <div style={{ paddingLeft: '12px', marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• CSD-E02K (50%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_CSD_E02K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.50)} |
                                            Actual: <Tag color={record.roa_CSD_E02K >= Math.round((record.total_customer || 0) * 0.50) ? 'green' : 'red'} size="small">
                                                {record.roa_CSD_E02K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>

                                    {/* ROL-E500 */}
                                    <div style={{ paddingLeft: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• ROL-E500 (50%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_ROL_E500 ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.50)} |
                                            Actual: <Tag color={record.roa_ROL_E500 >= Math.round((record.total_customer || 0) * 0.50) ? 'green' : 'red'} size="small">
                                                {record.roa_ROL_E500 ?? 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>

                                {/* ROA FUTURE */}
                                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px dashed #d9d9d9' }}>
                                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#13c2c2' }}>ROA FUTURE (2 items × 30 pts each)</div>

                                    {/* TBK-E01K */}
                                    <div style={{ paddingLeft: '12px', marginBottom: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• TBK-E01K (50%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_TBK_E01K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.50)} |
                                            Actual: <Tag color={record.roa_TBK_E01K >= Math.round((record.total_customer || 0) * 0.50) ? 'green' : 'red'} size="small">
                                                {record.roa_TBK_E01K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>

                                    {/* ROL-E01K */}
                                    <div style={{ paddingLeft: '12px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                            <span style={{ fontWeight: '500' }}>• ROL-E01K (50%):</span>
                                            <span style={{ fontSize: '12px' }}>Points: {record.pts_roa_ROL_E01K ?? 0} / 30</span>
                                        </div>
                                        <div style={{ fontSize: '11px', color: '#999', paddingLeft: '12px' }}>
                                            Target: {Math.round((record.total_customer || 0) * 0.50)} |
                                            Actual: <Tag color={record.roa_ROL_E01K >= Math.round((record.total_customer || 0) * 0.50) ? 'green' : 'red'} size="small">
                                                {record.roa_ROL_E01K ?? 0}
                                            </Tag>
                                        </div>
                                    </div>
                                </div>
                            </Space>
                        </Card>
                    </Col>
                </Row>
            </div>
        );
    };

    // Simplified main table columns - CUSTOM USER REQUEST
    const columns = [
        {
            title: <span style={{ whiteSpace: 'nowrap' }}>RANK</span>,
            dataIndex: 'rank_regional',
            key: 'rank',
            width: 75,
            fixed: 'left',
            align: 'center',
            render: (rank) => <div className="rank-cell">{getRankBadge(rank)}</div>,
            sorter: (a, b) => a.rank_regional - b.rank_regional,
        },
        {
            title: 'NIK',
            dataIndex: 'nik',
            key: 'nik',
            width: 80,
            align: 'center',
            responsive: ['md'],
        },
        {
            title: 'NAMA SALESMAN',
            dataIndex: 'salesman_name',
            key: 'name',
            width: 200,
            fixed: 'left',
            render: (name, record) => (
                <div className="salesman-cell">
                    <div style={{ fontSize: '13px', fontWeight: '500' }}>
                        {`${record.salesman_code}-${record.division}-${name}`}
                    </div>
                </div>
            ),
            sorter: (a, b) => a.salesman_name.localeCompare(b.salesman_name),
        },
        {
            title: 'AREA',
            dataIndex: 'area', // Directly use 'area' from BigQuery
            key: 'area',
            width: 120,
            align: 'center',
            responsive: ['sm'],
            render: (area) => <span style={{ fontSize: '12px' }}>{area}</span>,
        },
        {
            title: 'SALDO',
            dataIndex: 'points_balance',
            key: 'saldo',
            width: 80,
            align: 'center',
            responsive: ['md'],
            render: (val) => <span style={{ fontWeight: '500', fontSize: '12px' }}>{val ?? 0}</span>,
            sorter: (a, b) => (a.points_balance || 0) - (b.points_balance || 0),
        },
        {
            title: 'BLN INI',
            dataIndex: 'month_score',
            key: 'month_score',
            width: 90,
            align: 'center',
            render: (val) => <span style={{ fontWeight: 'bold', color: '#1890ff', fontSize: '13px' }}>{val ?? 0}</span>,
            sorter: (a, b) => (a.month_score || 0) - (b.month_score || 0),
        },
        {
            title: 'TOTAL POIN',
            dataIndex: 'total_score',
            key: 'total_score',
            width: 120,
            align: 'center',
            render: (score) => (
                <div className="score-cell">
                    <div className="score-value" style={{ color: getScoreTier(score).color }}>
                        <span style={{ fontSize: '18px', fontWeight: 'bold' }}>{score || 0}</span>
                    </div>
                </div>
            ),
            sorter: (a, b) => (a.total_score || 0) - (b.total_score || 0),
            defaultSortOrder: 'descend',
        },
    ];

    // Filter data by search text
    const filteredData = (leaderboardData || []).filter(item =>
        item.salesman_name && item.salesman_name.toLowerCase().includes(searchText.toLowerCase())
    );

    // Calculate summary stats
    const totalSalesman = filteredData.length;
    const avgScore = totalSalesman > 0
        ? filteredData.reduce((sum, item) => sum + (item.total_score || 0), 0) / totalSalesman
        : 0;
    const topScore = totalSalesman > 0
        ? Math.max(...filteredData.map(item => item.total_score || 0))
        : 0;

    return (
        <div className="leaderboard-container">
            {/* National/Regional Identity Alert */}
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
                                    <Tag color={user.region === 'ALL' ? "gold" : "blue"} style={{ borderRadius: '12px', fontWeight: 'bold' }}>
                                        Scope: {user.region === 'ALL' ? "NATIONAL (ALL)" : user.region}
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

            {/* Umroh Monitoring Banner - Clean Full-Width Design */}
            <div className="banner-container" style={{
                background: 'linear-gradient(90deg, #0d2a7a 0%, #163c92 50%, #0d2a7a 100%)',
                borderRadius: '8px',
                height: 'min(80px, 15vw)',
                marginBottom: '20px',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                position: 'relative',
                overflow: 'hidden',
                boxShadow: '0 6px 20px rgba(0,0,0,0.15)',
            }}>
                {/* Subtle Metallic Sheen */}
                <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.05) 0%, transparent 70%)',
                    zIndex: 1
                }} />

                {/* Actual Nabati Logo */}
                <div style={{
                    position: 'absolute',
                    left: 'max(20px, 5%)',
                    zIndex: 4,
                }}>
                    <img
                        src={nabatiLogo}
                        alt="Nabati Logo"
                        style={{
                            height: 'clamp(35px, 9vw, 55px)',
                            filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
                            objectFit: 'contain'
                        }}
                    />
                </div>

                {/* Text Container - Clean & Bold */}
                <div style={{
                    textAlign: 'center',
                    zIndex: 3,
                    width: '100%',
                    paddingLeft: 'clamp(100px, 22%, 160px)',
                    paddingRight: 'min(100px, 20%)'
                }}>
                    <h1 style={{
                        color: 'white',
                        margin: 0,
                        fontSize: 'clamp(14px, 3.8vw, 22px)',
                        fontWeight: 900,
                        letterSpacing: '1px',
                        textTransform: 'uppercase',
                        lineHeight: 1.1,
                        textShadow: '0 2px 4px rgba(0,0,0,0.4)'
                    }}>
                        MONITORING GRAND PRIZE UMROH
                    </h1>
                    <div style={{
                        fontSize: 'clamp(10px, 3vw, 16px)',
                        fontWeight: 700,
                        letterSpacing: '1.5px',
                        textTransform: 'uppercase',
                        color: 'rgba(255,255,255,0.9)',
                        marginTop: '2px'
                    }}>
                        PERIODE JANUARI - JUNI 2026
                    </div>
                </div>
            </div>

            {/* Top Slicers & Meta Pills */}
            <div style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '8px',
                marginBottom: '20px',
                flexWrap: 'wrap'
            }}>
                {/* Region Pill Slicer */}
                <div style={{
                    background: '#eeeeee',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    border: '1px solid #dddddd',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                    minHeight: '36px'
                }}>
                    <span style={{ fontSize: '9px', color: '#666', fontWeight: 800 }}>REGION:</span>
                    <Select
                        size="small"
                        variant="borderless"
                        style={{ minWidth: 'min(120px, 25vw)', fontWeight: 700, fontSize: '11px' }}
                        value={selectedRegion}
                        onChange={setSelectedRegion}
                        showSearch
                        optionFilterProp="children"
                        disabled={user?.region !== 'ALL'}
                        placeholder="Pilih Region"
                    >
                        {regions.map(region => (
                            <Select.Option key={region.code} value={region.code || ""}>
                                {region.name}
                            </Select.Option>
                        ))}
                    </Select>
                </div>

                {/* Division Pill Slicer */}
                <div style={{
                    background: '#eeeeee',
                    padding: '4px 12px',
                    borderRadius: '8px',
                    border: '1px solid #dddddd',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                    minHeight: '40px'
                }}>
                    <span style={{ fontSize: '10px', color: '#666', fontWeight: 800 }}>DIVISI:</span>
                    <Select
                        size="small"
                        variant="borderless"
                        style={{ minWidth: '100px', fontWeight: 700, fontSize: '13px' }}
                        value={selectedDivision}
                        onChange={setSelectedDivision}
                        allowClear
                        placeholder="Semua"
                    >
                        <Option value="AEGDA">SAEG</Option>
                        <Option value="AEPDA">SAEP</Option>
                    </Select>
                </div>

                {/* Update Date Pill */}
                {cutoffDate && (
                    <div style={{
                        background: '#eeeeee',
                        padding: '4px 16px',
                        borderRadius: '8px',
                        border: '1px solid #dddddd',
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                        minHeight: '40px'
                    }}>
                        <span style={{
                            fontSize: '8px',
                            color: '#999',
                            fontWeight: 800,
                            textTransform: 'uppercase',
                            lineHeight: 1
                        }}>UPDATE</span>
                        <span style={{ fontSize: '13px', fontWeight: 700, color: '#444' }}>
                            {new Date(cutoffDate).toLocaleDateString('en-US', {
                                month: 'short', day: 'numeric', year: 'numeric'
                            })}
                        </span>
                    </div>
                )}

                {/* Summary Button */}
                {user?.region === 'ALL' && (
                    <Button
                        type="primary"
                        icon={<TrophyOutlined />}
                        onClick={showModal}
                        style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none',
                            height: '40px',
                            padding: '0 16px',
                            borderRadius: '8px',
                            fontWeight: '700',
                            fontSize: '11px'
                        }}
                    >
                        SUMMARY
                    </Button>
                )}
            </div>

            {/* Redesigned Search Bar - Cleaner integration */}
            <div style={{ maxWidth: '400px', margin: '0 auto 24px auto' }}>
                <Input
                    placeholder="Cari nama salesman..."
                    prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                    value={searchText}
                    onChange={e => setSearchText(e.target.value)}
                    allowClear
                    size="middle"
                    style={{ borderRadius: '20px', border: '1px solid #d9d9d9' }}
                />
            </div>

            {/* Summary Statistics */}
            <Row gutter={16} style={{ marginBottom: '24px' }}>
                <Col xs={24} sm={8}>
                    <Card className="stat-card">
                        <Statistic
                            title="Total Salesman"
                            value={totalSalesman}
                            prefix={<TrophyOutlined />}
                            valueStyle={{ color: '#1890ff' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card className="stat-card">
                        <Statistic
                            title="Top Score"
                            value={topScore}
                            suffix="pts"
                            prefix={<StarFilled />}
                            valueStyle={{ color: '#faad14' }}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={8}>
                    <Card className="stat-card">
                        <Statistic
                            title="Average Score"
                            value={avgScore}
                            precision={0}
                            suffix="pts"
                            valueStyle={{ color: '#52c41a' }}
                        />
                    </Card>
                </Col>
            </Row>

            {/* Leaderboard Table */}
            <Card styles={{ body: { padding: '12px' } }}>
                <div style={{ marginBottom: '8px', color: '#666', fontSize: '11px' }}>
                    💡 <strong>Tip:</strong> Klik baris untuk detail score
                </div>
                {loading ? (
                    <div style={{ padding: '20px' }}>
                        <Skeleton active paragraph={{ rows: 1 }} title={false} style={{ marginBottom: '20px' }} />
                        {[...Array(5)].map((_, i) => (
                            <div key={i} style={{ display: 'flex', gap: '15px', marginBottom: '15px' }}>
                                <Skeleton.Button active size="small" style={{ width: 40 }} />
                                <Skeleton.Input active size="small" style={{ width: 120 }} />
                                <Skeleton.Input active size="small" style={{ width: 80 }} />
                                <Skeleton.Input active size="small" style={{ width: 100 }} />
                                <Skeleton.Input active size="small" style={{ flex: 1 }} />
                            </div>
                        ))}
                    </div>
                ) : (
                    <Table
                        columns={columns}
                        dataSource={filteredData}
                        rowKey="salesman_code"
                        pagination={{
                            pageSize: 20,
                            showSizeChanger: true,
                            showTotal: (total) => `Total ${total} salesman`,
                            pageSizeOptions: ['10', '20', '50', '100']
                        }}
                        expandable={{
                            expandedRowRender,
                            expandedRowKeys,
                            onExpandedRowsChange: setExpandedRowKeys,
                            expandIcon: ({ expanded, onExpand, record }) => (
                                expanded ?
                                    <DownOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#1890ff' }} /> :
                                    <RightOutlined onClick={e => onExpand(record, e)} style={{ cursor: 'pointer', color: '#999' }} />
                            ),
                        }}
                        scroll={{ x: 800 }}
                        size="small"
                        bordered
                        rowClassName={(record, index) =>
                            record.rank_regional <= 3 ? 'top-performer-row' : ''
                        }
                    />
                )}
            </Card>

            {/* Top 1 Summary Modal */}
            <Modal
                title={<span style={{ fontSize: '16px', fontWeight: 'bold' }}>🏆 Top 1 Salesman per Region</span>}
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                footer={null}
                width={800}
            >
                {loadingModal ? (
                    <div style={{ padding: '20px' }}>
                        {[...Array(3)].map((_, i) => (
                            <div key={i} style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
                                <Skeleton.Input active size="small" style={{ width: 80 }} />
                                <Skeleton.Button active size="small" style={{ width: 50 }} />
                                <Skeleton.Input active size="small" style={{ flex: 1 }} />
                                <Skeleton.Input active size="small" style={{ width: 60 }} />
                            </div>
                        ))}
                    </div>
                ) : (
                    <Table
                        dataSource={topSummaryData}
                        pagination={false}
                        size="small"
                        rowKey={(record) => `${record.region}-${record.division}`}
                        bordered
                        columns={[
                            {
                                title: 'REGION',
                                dataIndex: 'region',
                                key: 'region',
                                width: 120,
                                align: 'center',
                                onCell: (record, index) => {
                                    const sameRegion = topSummaryData.filter(r => r.region === record.region);
                                    const firstIndex = topSummaryData.findIndex(r => r.region === record.region);
                                    if (index === firstIndex) {
                                        return { rowSpan: sameRegion.length };
                                    }
                                    return { rowSpan: 0 };
                                },
                                render: (value) => <strong>{value}</strong>,
                            },
                            {
                                title: 'DIV',
                                dataIndex: 'division',
                                key: 'division',
                                width: 80,
                                align: 'center',
                                render: (div) => <Tag color={div === 'AEGDA' ? 'blue' : 'green'}>{div}</Tag>
                            },
                            {
                                title: 'NIK',
                                dataIndex: 'nik',
                                key: 'nik',
                                align: 'center',
                                width: 100,
                            },
                            {
                                title: 'SALESMAN',
                                dataIndex: 'salesman_name',
                                key: 'salesman_name',
                                render: (name) => <span style={{ fontWeight: '500' }}>{name}</span>
                            },
                            {
                                title: 'POINT',
                                dataIndex: 'total_score',
                                key: 'point',
                                align: 'right',
                                width: 100,
                                render: (score) => <span style={{ fontWeight: 'bold', fontSize: '15px' }}>{score}</span>
                            }
                        ]}
                    />
                )}
            </Modal >
        </div >
    );
};

export default Leaderboard;
