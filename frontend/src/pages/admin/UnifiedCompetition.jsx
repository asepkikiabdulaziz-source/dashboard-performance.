import React, { useState, useEffect } from 'react';
import { Tabs, Card } from 'antd';
import { TrophyOutlined, CrownOutlined } from '@ant-design/icons';
import Leaderboard from '../Leaderboard';
import GenericCompetitionMonitor from './GenericCompetitionMonitor';
import api from '../../api';
import '../../styles/CompetitionMonitor.css';

const { TabPane } = Tabs;

const UnifiedCompetition = () => {
    const [activeMainTab, setActiveMainTab] = useState('umroh');
    const [competitions, setCompetitions] = useState([]);
    const [selectedCompetition, setSelectedCompetition] = useState(null);
    const [loading, setLoading] = useState(false);

    // Fetch available competitions for AMO tab
    useEffect(() => {
        fetchCompetitions();
    }, []);

    const fetchCompetitions = async () => {
        try {
            setLoading(true);
            const response = await api.get('/competitions/list');
            const comps = response.data.data || [];
            setCompetitions(comps);

            // Auto-select first competition if available
            if (comps.length > 0 && !selectedCompetition) {
                setSelectedCompetition(comps[0]);
            }
        } catch (error) {
            console.error("Failed to load competitions", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="competition-container">
            <Tabs
                activeKey={activeMainTab}
                onChange={setActiveMainTab}
                type="card"
                size="large"
                centered
                style={{ background: 'white', padding: '24px', borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}
                items={[
                    {
                        key: 'umroh',
                        label: (
                            <span style={{ fontSize: '16px', fontWeight: 500 }}>
                                <CrownOutlined /> Grand Prize Umroh
                            </span>
                        ),
                        children: (
                            <div style={{ marginTop: '24px' }}>
                                <Leaderboard />
                            </div>
                        )
                    },
                    {
                        key: 'amo',
                        label: (
                            <span style={{ fontSize: '16px', fontWeight: 500 }}>
                                <TrophyOutlined /> Kompetisi AMO
                            </span>
                        ),
                        children: selectedCompetition ? (
                            <GenericCompetitionMonitor
                                competitionId={selectedCompetition.id}
                                title={selectedCompetition.title}
                                period={selectedCompetition.period}
                                embedded={true}
                            />
                        ) : (
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                <p>Tidak ada kompetisi aktif</p>
                            </div>
                        )
                    }
                ]}
            />
        </div>
    );
};

export default UnifiedCompetition;
