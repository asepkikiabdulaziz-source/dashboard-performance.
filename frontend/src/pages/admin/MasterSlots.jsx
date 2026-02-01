import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Table, Card, Input, Button, Tag, Space, Modal, Form, Select, App, Descriptions, Spin, Row, Col, Tooltip, Timeline } from 'antd';
import { SearchOutlined, UserAddOutlined, TeamOutlined, FilterOutlined, DeploymentUnitOutlined, HistoryOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import debounce from 'lodash/debounce';
import api from '../../api';

// --- Debounce Select Component for Employee Search ---
function DebounceSelect({ fetchOptions, debounceTimeout = 800, ...props }) {
    const [fetching, setFetching] = useState(false);
    const [options, setOptions] = useState([]);
    const fetchRef = useRef(0);

    const debounceFetcher = useMemo(() => {
        const loadOptions = (value) => {
            fetchRef.current += 1;
            const fetchId = fetchRef.current;
            setOptions([]);
            setFetching(true);

            fetchOptions(value).then((newOptions) => {
                if (fetchId !== fetchRef.current) return; // Ignore stale requests
                setOptions(newOptions);
                setFetching(false);
            });
        };
        return debounce(loadOptions, debounceTimeout);
    }, [fetchOptions, debounceTimeout]);

    return (
        <Select
            labelInValue
            filterOption={false}
            onSearch={debounceFetcher}
            notFoundContent={fetching ? <Spin size="small" /> : null}
            {...props}
            options={options}
            showSearch
        />
    );
}

const MasterSlots = () => {
    const { message } = App.useApp();
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(false);
    const [pagination, setPagination] = useState({ current: 1, pageSize: 15, total: 0 }); // Increased page size

    // Filters & Slicers
    const [form] = Form.useForm();
    const [searchText, setSearchText] = useState('');
    const [searchInput, setSearchInput] = useState('');
    const [roleFilter, setRoleFilter] = useState([]);
    const [regionFilter, setRegionFilter] = useState([]);
    const [branchFilter, setBranchFilter] = useState([]);
    const [depoFilter, setDepoFilter] = useState([]);
    const [divFilter, setDivFilter] = useState([]);
    const [isNplOnly, setIsNplOnly] = useState(false); // If applicable, though not in slots usually, but for consistency if needed

    // Lookups
    const [regions, setRegions] = useState([]);
    const [branches, setBranches] = useState([]);
    const [depos, setDepos] = useState([]);
    // Dynamic Lookups
    const [masterRoles, setMasterRoles] = useState([]);
    const [masterDivisions, setMasterDivisions] = useState([]);
    const [masterLevels, setMasterLevels] = useState([]);

    // Modals & State
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedSlot, setSelectedSlot] = useState(null);
    const [assignForm] = Form.useForm();
    const [assigning, setAssigning] = useState(false);

    // Edit Slot Modal
    const [editForm] = Form.useForm();
    const [isEditOpen, setIsEditOpen] = useState(false);
    const [editing, setEditing] = useState(false);
    const [editScope, setEditScope] = useState('DEPO');

    // History Modal
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [historyData, setHistoryData] = useState([]);
    const [loadingHistory, setLoadingHistory] = useState(false);

    // Create Slot Modal
    const [isCreateOpen, setIsCreateOpen] = useState(false);
    const [creating, setCreating] = useState(false);
    const [createScope, setCreateScope] = useState('DEPO'); // Track scope for dynamic form

    // FORCE RESET EDIT FORM STATE 
    // Fixes issue where cancelling an edit persists the local state to other slots
    useEffect(() => {
        if (isEditOpen && selectedSlot) {
            console.log("Resetting Edit Form for:", selectedSlot.slot_code);
            setEditScope(selectedSlot.scope || 'DEPO');
            editForm.resetFields();
        }
    }, [isEditOpen, selectedSlot, editForm]);

    // Fetch Lookups
    useEffect(() => {
        const loadLookups = async () => {
            try {
                const [rRes, bRes, dRes, roleRes, divRes, levRes] = await Promise.all([
                    api.get('/admin/master/regions'),
                    api.get('/admin/master/branches'),
                    api.get('/admin/master/distributors'),
                    api.get('/admin/master/roles'),
                    api.get('/admin/master/divisions'),
                    api.get('/admin/master/lookup/LEVEL')
                ]);
                setRegions(rRes.data);
                setBranches(bRes.data);
                setDepos(dRes.data);
                setMasterRoles(roleRes.data);
                setMasterDivisions(divRes.data);
                // Sort Levels numerically if possible, or trust API order
                setMasterLevels(levRes.data.sort((a, b) => parseInt(a.code) - parseInt(b.code)));
            } catch (e) {
                console.error("Failed to load lookups", e);
            }
        };
        loadLookups();
    }, []);

    // Optimized Bulk Fetch
    const fetchSlots = async () => {
        setLoading(true);
        try {
            // Fetch ALL slots (up to 10k to be safe for now, can be increased)
            const response = await api.get('/admin/slots/', {
                params: { page_size: 10000 }
            });
            setSlots(response.data.data || []);
        } catch (error) {
            console.error(error);
            message.error('Failed to load slots data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSlots();
    }, []);

    // --- High Performance Hierarchy Enrichment ---
    // Maps each slot to its Region and Branch and resolves missing NAMES locally
    const enrichedSlots = useMemo(() => {
        if (!slots.length) return [];

        // Helper to normalize IDs for lookups
        const normalize = (val) => val ? String(val).trim().toUpperCase() : null;

        // 0. PRE-INDEXING: Create Maps for O(1) lookups (Instead of O(N) .find in a loop)
        const regionsMap = new Map(regions.map(r => [normalize(r.region_code), r]));
        const branchesMap = new Map(branches.map(b => [normalize(b.id), b]));
        const deposMap = new Map(depos.map(d => [normalize(d.kd_dist), d]));
        const divisionsMap = new Map(masterDivisions.map(div => [normalize(div.division_id), div]));

        return slots.map(slot => {
            // 1. Initial IDs (Direct from Slot)
            let d_id = normalize(slot.depo_id);
            let b_id = null;
            let r_id = null;

            let d_name = slot.depo_name;
            let b_name = slot.branch_name;
            let r_name = slot.region_name;
            let div_name = slot.division_name;

            const cleanScopeId = normalize(slot.scope_id);
            const cleanDivId = normalize(slot.division_id);
            const slotRole = (slot.role || slot.role_id || '').trim().toUpperCase();

            // 2. Map Scope ID to the correct hierarchical level if applicable
            if (slot.scope === 'REGION' && cleanScopeId) {
                r_id = cleanScopeId;
            } else if (slot.scope === 'BRANCH' && cleanScopeId) {
                b_id = cleanScopeId;
            } else if (slot.scope === 'DEPO' && cleanScopeId) {
                if (!d_id) d_id = cleanScopeId;
            }

            // 3. Hierarchical Resolution (O(1) Map Lookups)
            if (d_id) {
                const d = deposMap.get(d_id);
                if (d) {
                    d_name = d.name;
                    b_id = normalize(d.branch_id) || b_id;
                }
            }

            if (b_id) {
                const b = branchesMap.get(b_id);
                if (b) {
                    b_name = b.name;
                    r_id = normalize(b.region_code) || r_id;
                }
            }

            if (r_id) {
                const reg = regionsMap.get(r_id);
                if (reg) r_name = reg.name;
            }

            // 4. Resolve Division Name
            if (cleanDivId && !div_name) {
                const div = divisionsMap.get(cleanDivId);
                if (div) div_name = div.division_name;
            }

            return {
                ...slot,
                _role: slotRole,
                _region_id: r_id,
                _branch_id: b_id,
                _depo_id: d_id,
                _depo_name: d_name || d_id || 'GLOBAL',
                _branch_name: b_name,
                _region_name: r_name,
                _division_name: div_name || cleanDivId
            };
        });
    }, [slots, branches, depos, regions, masterDivisions]);

    // --- Helper for Robust ID Comparison ---
    const isIdInList = (id, list) => {
        if (!id || !list || list.length === 0) return false;
        const cleanId = String(id).trim().toUpperCase();
        return list.some(item => String(item).trim().toUpperCase() === cleanId);
    };

    // --- High Performance Frontend Filtering Logic ---
    // --- High Performance Master-Data Driven Slicers ---
    // Ensures all locations are selectable regardless of slot presence
    const getDependentOptions = (fieldName, baseList, currentFilters) => {
        if (!baseList) return [];

        // 1. Regions: Always show all
        if (fieldName === 'region_id') return baseList;

        // 2. Branches: Filter by selected Regions
        if (fieldName === 'branch_id') {
            if (!regionFilter || regionFilter.length === 0) return baseList;
            return baseList.filter(opt => {
                const b = branches.find(item => String(item.id).toUpperCase() === String(opt.value).toUpperCase());
                return b && isIdInList(b.region_code, regionFilter);
            });
        }

        // 3. Depos: Filter by selected Branches (or Regions)
        if (fieldName === 'depo_id') {
            const hasBranchFilter = branchFilter && branchFilter.length > 0;
            const hasRegionFilter = regionFilter && regionFilter.length > 0;

            if (!hasBranchFilter && !hasRegionFilter) return baseList;

            return baseList.filter(opt => {
                const d = depos.find(item => String(item.kd_dist).toUpperCase() === String(opt.value).toUpperCase());
                if (!d) return false;

                // Branch filter takes precedence
                if (hasBranchFilter) {
                    return isIdInList(d.branch_id, branchFilter);
                }

                // Fallback to Region filter (trace Depo -> Branch -> Region)
                if (hasRegionFilter) {
                    const b = branches.find(item => String(item.id).toUpperCase() === String(d.branch_id).toUpperCase());
                    return b && isIdInList(b.region_code, regionFilter);
                }
                return true;
            });
        }

        // 4. Role & Division: Show all available in master data (Management flexibility)
        return baseList;
    };

    const processedSlots = useMemo(() => {
        return enrichedSlots.filter(item => {
            // 1. Position/Role Match - Only filter if something is selected
            const roleMatch = !roleFilter || roleFilter.length === 0 ||
                roleFilter.some(r => String(r).trim().toUpperCase() === item._role);

            // 2. Division Match
            const divMatch = !divFilter || divFilter.length === 0 ||
                (item.division_id && isIdInList(item.division_id, divFilter));

            // 3. Hierarchy Match (Simplified intersection check for robustness)
            // If a region is selected, slot must match region.
            // If a branch is selected, slot must match branch.
            // If a depo is selected, slot must match depo.
            const regionMatch = !regionFilter || regionFilter.length === 0 ||
                isIdInList(item._region_id, regionFilter);

            const branchMatch = !branchFilter || branchFilter.length === 0 ||
                isIdInList(item._branch_id, branchFilter);

            const depoMatch = !depoFilter || depoFilter.length === 0 ||
                isIdInList(item._depo_id, depoFilter);

            // 4. Search Match
            const s = searchText ? searchText.toLowerCase().trim() : '';
            const searchMatch = !s ||
                (item.slot_code || '').toLowerCase().includes(s) ||
                (item.sales_code || '').toLowerCase().includes(s) ||
                (item.current_name || '').toLowerCase().includes(s) ||
                (item.current_nik || '').toLowerCase().includes(s) ||
                (item._depo_name || '').toLowerCase().includes(s) ||
                (item._branch_name || '').toLowerCase().includes(s) ||
                (item._region_name || '').toLowerCase().includes(s);

            // ALL conditions must be met (Intersection)
            return roleMatch && divMatch && depoMatch && regionMatch && branchMatch && searchMatch;
        });
    }, [enrichedSlots, searchText, roleFilter, divFilter, depoFilter, regionFilter, branchFilter]);

    const dependentOptions = useMemo(() => {
        // Standard Hierarchy Slicers (Master Data Driven)
        // Normalized matching for robust cascading
        const filteredBranchesMaster = regionFilter.length > 0
            ? branches.filter(b => isIdInList(b.region_code, regionFilter))
            : branches;

        const filteredDeposMaster = branchFilter.length > 0
            ? depos.filter(d => isIdInList(d.branch_id, branchFilter))
            : (regionFilter.length > 0
                ? depos.filter(d => filteredBranchesMaster.some(b => String(b.id).trim().toUpperCase() === String(d.branch_id).trim().toUpperCase()))
                : depos);

        // Data-Driven Slicers (For Role and Division)
        // These stay intersection-based for better UX in choosing categories
        const current = {
            role_id: roleFilter,
            division_id: divFilter,
            depo_id: depoFilter,
            region_id: regionFilter,
            branch_id: branchFilter
        };

        return {
            roles: getDependentOptions('role_id', masterRoles.map(r => ({ text: r.role_name, value: r.role_id || "" })), current),
            divisions: getDependentOptions('division_id', masterDivisions.map(d => ({ text: d.division_name, value: d.division_id || "" })), current),

            // Core hierarchy follows master tables relationship
            regions: regions.map(r => ({ text: r.name, value: r.region_code || "" })),
            branches: filteredBranchesMaster.map(b => ({ text: b.name, value: b.id || "" })),
            depos: filteredDeposMaster.map(d => ({ text: d.name, value: d.kd_dist || "" })),
        };
    }, [enrichedSlots, roleFilter, divFilter, depoFilter, regionFilter, branchFilter, masterRoles, masterDivisions, depos, regions, branches]);

    // Handlers (Instant Frontend)
    const handleTableChange = (newPagination) => {
        setPagination(prev => ({ ...prev, current: newPagination.current }));
    };

    // Handlers (Debounced Search)
    const debouncedSearch = useMemo(
        () => debounce((value) => {
            setSearchText(value);
            setPagination(prev => ({ ...prev, current: 1 }));
        }, 300),
        []
    );

    const handleSearch = (value) => {
        setSearchInput(value); // Visual update (Instant)
        debouncedSearch(value); // Filter update (Delayed)
    };

    const handleRoleFilter = (values) => {
        setRoleFilter(values);
        setPagination(prev => ({ ...prev, current: 1 }));
    };

    const handleRegionChange = (values) => {
        setRegionFilter(values);
        setPagination(prev => ({ ...prev, current: 1 }));
    };

    const handleBranchChange = (values) => {
        setBranchFilter(values);
        setPagination(prev => ({ ...prev, current: 1 }));
    };

    const handleDepoChange = (values) => {
        setDepoFilter(values);
        setPagination(prev => ({ ...prev, current: 1 }));
    };

    const handleDivChange = (values) => {
        setDivFilter(values);
        setPagination(prev => ({ ...prev, current: 1 }));
    };

    // Employee Searcher for Dropdown
    const fetchEmployeeList = async (username) => {
        if (!username) return [];

        try {
            const response = await api.get('/admin/employees/', {
                params: {
                    search: username,
                    page: 1,
                    page_size: 10,
                    role: 'all' // We want to see all employees to assign
                }
            });

            return response.data.data.map(emp => ({
                label: `${emp.full_name} (${emp.nik}) - ${emp.role_id}`,
                value: emp.nik, // We send NIK to backend
            }));
        } catch (error) {
            console.error(error);
            return [];
        }
    };

    const handleAssign = async (values) => {
        setAssigning(true);
        try {
            // values.employee is { label:..., value: NIK } because of labelInValue
            const nik = values.employee.value;

            await api.post(`/admin/slots/${selectedSlot.slot_code}/assign`, {
                nik: nik,
                reason: values.reason
            });

            message.success(`Successfully assigned to ${selectedSlot.slot_code}`);
            setIsModalOpen(false);
            assignForm.resetFields();
            fetchSlots();
        } catch (error) {
            message.error(error.response?.data?.detail || 'Assignment failed');
        } finally {
            setAssigning(false);
        }
    };

    // History Handler
    const handleViewHistory = async (slot) => {
        setSelectedSlot(slot);
        setIsHistoryOpen(true);
        setLoadingHistory(true);
        try {
            const res = await api.get(`/admin/slots/${slot.slot_code}/history`);
            setHistoryData(res.data.data);
        } catch (e) {
            message.error('Failed to load history');
        } finally {
            setLoadingHistory(false);
        }
    };

    // Edit Handler
    const handleEditSlot = (slot) => {
        setSelectedSlot(slot);
        setEditScope(slot.scope || 'DEPO'); // Initialize scope state
        setIsEditOpen(true);
    };

    const submitEditSlot = async (values) => {
        setEditing(true);
        try {
            await api.put(`/admin/slots/${selectedSlot.slot_code}`, values);
            message.success('Slot updated');
            setIsEditOpen(false);
            fetchSlots(pagination.current, searchText, roleFilter);
        } catch (e) {
            message.error('Update failed');
        } finally {
            setEditing(false);
        }
    };

    // Create Handler
    const submitCreateSlot = async (values) => {
        setCreating(true);
        try {
            await api.post('/admin/slots/', values);
            message.success('Slot created successfully');
            fetchSlots();
        } catch (e) {
            message.error(e.response?.data?.detail || 'Failed to create slot');
        } finally {
            setCreating(false);
        }
    };

    // Columns
    const columns = [
        {
            title: 'Hierarchy',
            key: 'hierarchy',
            width: 60,
            render: (_, record) => (
                <Tooltip title={`Reporting to: ${record.parent_slot_code || 'None'}`}>
                    <DeploymentUnitOutlined
                        style={{
                            color: record.parent_slot_code ? '#1890ff' : '#d9d9d9',
                            fontSize: '16px'
                        }}
                    />
                </Tooltip>
            )
        },
        {
            title: 'Slot Identity',
            key: 'identity',
            width: 200,
            render: (_, record) => (
                <div style={{ lineHeight: '1.2' }}>
                    <div style={{ fontWeight: 600, fontSize: '14px', color: '#1f1f1f' }}>
                        {record.role || record.role_id || 'Position'}
                    </div>
                    <Space size={4} style={{ fontSize: '12px', color: '#8c8c8c' }}>
                        <span style={{ fontFamily: 'monospace' }}>{record.sales_code}</span>
                        {record.level && record.level !== 99 && (
                            <Tag color="geekblue" style={{ margin: 0, fontSize: '10px', lineHeight: '16px' }}>Rank {record.level}</Tag>
                        )}
                    </Space>
                    <div style={{ fontSize: '10px', color: '#bfbfbf', marginTop: 2, fontFamily: 'monospace' }}>
                        {record.slot_code}
                    </div>
                </div>
            )
        },
        {
            title: 'Location',
            key: 'location',
            width: 180,
            render: (_, record) => (
                <div style={{ lineHeight: '1.2' }}>
                    <div style={{ fontWeight: 600, color: '#1890ff' }}>
                        {record._depo_name}
                    </div>
                    <Space split={<span style={{ color: '#d9d9d9' }}>|</span>} style={{ fontSize: '11px', color: '#595959' }}>
                        {record._division_name && <span>{record._division_name}</span>}
                        {record.scope !== 'DEPO' && <span>{record.scope}</span>}
                        {record._branch_name && <span>{record._branch_name}</span>}
                    </Space>
                </div>
            )
        },
        {
            title: 'Current Holder',
            key: 'holder',
            render: (_, record) => (
                record.current_nik ? (
                    <Card size="small" styles={{ body: { padding: '8px' } }} variant="borderless" style={{ background: '#f6ffed', border: '1px solid #b7eb8f' }}>
                        <div style={{ fontWeight: 'bold', color: '#389e0d' }}>{record.current_name}</div>
                        <div style={{ fontSize: '11px', color: '#666' }}>
                            {record.current_nik} • Joined: {record.assigned_since?.split('T')[0]}
                        </div>
                    </Card>
                ) : (
                    <Tag color="red" style={{ width: '100%', textAlign: 'center' }}>VACANT</Tag>
                )
            )
        },
        {
            title: 'Action',
            key: 'action',
            width: 150,
            render: (_, record) => (
                <Space>
                    <Tooltip title="Edit details">
                        <Button
                            icon={<EditOutlined />}
                            size="small"
                            onClick={() => handleEditSlot(record)}
                        />
                    </Tooltip>
                    <Tooltip title="View History">
                        <Button
                            icon={<HistoryOutlined />}
                            size="small"
                            onClick={() => handleViewHistory(record)}
                        />
                    </Tooltip>
                    <Tooltip title="Assign Employee">
                        <Button
                            type="primary"
                            ghost
                            size="small"
                            icon={<UserAddOutlined />}
                            onClick={() => {
                                setSelectedSlot(record);
                                setIsModalOpen(true);
                            }}
                        />
                    </Tooltip>
                </Space>
            )
        }
    ];

    return (
        <Card
            title={
                <Space>
                    <TeamOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
                    <span style={{ fontSize: '18px' }}>Master Slots Management</span>
                </Space>
            }
            extra={
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setIsCreateOpen(true)}
                >
                    Add Slot
                </Button>
            }
            styles={{ body: { padding: '0 24px 24px' } }}
        >
            {/* Premium Slicers Section */}
            <div style={{
                marginBottom: 24,
                marginTop: 20,
                background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
                padding: '24px',
                borderRadius: '16px',
                border: '1px solid #dee2e6',
                boxShadow: '0 4px 12px rgba(0,0,0,0.03)'
            }}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} sm={12} lg={5}>
                        <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 8, color: '#495057', display: 'flex', alignItems: 'center' }}>
                            <FilterOutlined style={{ marginRight: 8, color: '#1890ff' }} />
                            REGION
                        </div>
                        <Select
                            mode="multiple"
                            style={{ width: '100%' }}
                            placeholder="All Regions"
                            allowClear
                            maxTagCount="responsive"
                            onChange={handleRegionChange}
                            value={regionFilter}
                            options={dependentOptions.regions.map(r => ({ label: r.text, value: r.value }))}
                        />
                    </Col>
                    <Col xs={24} sm={12} lg={5}>
                        <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 8, color: '#495057' }}>BRANCH</div>
                        <Select
                            mode="multiple"
                            style={{ width: '100%' }}
                            placeholder="All Branches"
                            allowClear
                            maxTagCount="responsive"
                            onChange={handleBranchChange}
                            value={branchFilter}
                            options={dependentOptions.branches.map(b => ({ label: b.text, value: b.value }))}
                        />
                    </Col>
                    <Col xs={24} sm={12} lg={5}>
                        <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 8, color: '#495057' }}>LOCATION / DEPO</div>
                        <Select
                            mode="multiple"
                            style={{ width: '100%' }}
                            placeholder="All Locations"
                            allowClear
                            maxTagCount="responsive"
                            onChange={handleDepoChange}
                            value={depoFilter}
                            options={dependentOptions.depos.map(d => ({ label: d.text, value: d.value }))}
                        />
                    </Col>
                    <Col xs={24} sm={12} lg={5}>
                        <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 8, color: '#495057' }}>DIVISION</div>
                        <Select
                            mode="multiple"
                            style={{ width: '100%' }}
                            placeholder="All Divisions"
                            allowClear
                            maxTagCount="responsive"
                            onChange={handleDivChange}
                            value={divFilter}
                            options={dependentOptions.divisions.map(d => ({ label: d.text, value: d.value }))}
                        />
                    </Col>
                    <Col xs={24} sm={12} lg={4}>
                        <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: 8, color: '#495057' }}>POSITION / ROLE</div>
                        <Select
                            mode="multiple"
                            style={{ width: '100%' }}
                            placeholder="All Roles"
                            allowClear
                            maxTagCount="responsive"
                            onChange={handleRoleFilter}
                            value={roleFilter}
                            options={dependentOptions.roles.map(r => ({ label: r.text, value: r.value }))}
                        />
                    </Col>
                </Row>

                <div style={{ marginTop: 20, paddingTop: 16, borderTop: '1px border-dashed #dee2e6' }}>
                    <Row gutter={16} align="middle">
                        <Col flex="auto">
                            <Input
                                size="large"
                                placeholder="Cari Slot, Nama Karyawan, NIK, atau Lokasi (Instan)..."
                                prefix={<SearchOutlined style={{ color: '#1890ff' }} />}
                                onChange={e => handleSearch(e.target.value)}
                                value={searchInput}
                                allowClear
                                style={{ borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}
                            />
                        </Col>
                    </Row>
                </div>
            </div>

            <Table
                dataSource={processedSlots}
                columns={columns}
                rowKey="slot_code"
                pagination={{
                    ...pagination,
                    showSizeChanger: true,
                    showTotal: (total) => `Total ${total} Slots`
                }}
                loading={loading}
                onChange={handleTableChange}
                size="middle"
                bordered
                virtual
                scroll={{ y: 650, x: 1200 }}
            />

            {/* Assignment Modal */}
            <Modal
                title={
                    <Space>
                        <UserAddOutlined />
                        <span>Assign Employee</span>
                    </Space>
                }
                open={isModalOpen}
                onCancel={() => setIsModalOpen(false)}
                footer={null}
                destroyOnHidden
            >
                {selectedSlot && (
                    <Form form={assignForm} layout="vertical" onFinish={handleAssign}>
                        <div style={{ background: '#f5f5f5', padding: '16px', borderRadius: '8px', marginBottom: '20px' }}>
                            <Descriptions size="small" column={1}>
                                <Descriptions.Item label="Target Slot"><b>{selectedSlot.slot_code}</b></Descriptions.Item>
                                <Descriptions.Item label="Position">{selectedSlot.sales_code}</Descriptions.Item>
                                <Descriptions.Item label="Replacing">
                                    {selectedSlot.current_name ? (
                                        <span style={{ color: '#fa8c16' }}>{selectedSlot.current_name} (Will be removed)</span>
                                    ) : (
                                        <span style={{ color: '#52c41a' }}>VACANT (New Assignment)</span>
                                    )}
                                </Descriptions.Item>
                            </Descriptions>
                        </div>

                        <Form.Item
                            label="Search Employee"
                            name="employee"
                            rules={[{ required: true, message: 'Please select an employee' }]}
                            help="Type name or NIK to search"
                        >
                            <DebounceSelect
                                placeholder="e.g. 'Budi' or '12345'"
                                fetchOptions={fetchEmployeeList}
                                style={{ width: '100%' }}
                            />
                        </Form.Item>

                        <Form.Item
                            label="Reason / Note"
                            name="reason"
                            initialValue="New Assignment"
                        >
                            <Input.TextArea rows={2} placeholder="Optional note for this assignment" />
                        </Form.Item>

                        <Form.Item style={{ marginTop: 30 }}>
                            <Button type="primary" htmlType="submit" loading={assigning} block size="large">
                                Confirm Assignment
                            </Button>
                        </Form.Item>
                    </Form>
                )}
            </Modal>

            {/* Edit Slot Modal */}
            <Modal
                title="Edit Slot Details"
                open={isEditOpen}
                onCancel={() => setIsEditOpen(false)}
                footer={null}
                destroyOnHidden
            >
                <Form
                    form={editForm}
                    layout="vertical"
                    onFinish={submitEditSlot}
                    initialValues={{
                        sales_code: selectedSlot?.sales_code,
                        role: selectedSlot?.role,
                        level: selectedSlot?.level,
                        division_id: selectedSlot?.division_id,
                        depo_id: selectedSlot?.depo_id,
                        scope: selectedSlot?.scope,
                        scope_id: selectedSlot?.scope_id,
                        slot_code: selectedSlot?.slot_code,
                        parent_slot_code: selectedSlot?.parent_slot_code
                    }}
                >
                    <>
                        <Form.Item label="Slot Code" name="slot_code">
                            <Input disabled style={{ color: '#000' }} />
                        </Form.Item>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item label="Sales Code" name="sales_code">
                                    <Input />
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item label="Role" name="role">
                                    <Select>
                                        {masterRoles.map(r => (
                                            <Select.Option key={r.role_id} value={r.role_id || ""}>{r.role_name}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item label="Level" name="level">
                                    <Select>
                                        {masterLevels.map(l => (
                                            <Select.Option key={l.code} value={l.code ? parseInt(l.code) : 0}>{l.code} - {l.name}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item label="Parent Slot" name="parent_slot_code">
                                    <Input placeholder="Parent Slot Code" />
                                </Form.Item>
                            </Col>
                        </Row>

                        <Row gutter={16}>
                            <Col span={12}>
                                <Form.Item label="Division" name="division_id">
                                    <Select>
                                        {masterDivisions.map(d => (
                                            <Select.Option key={d.division_id} value={d.division_id || ""}>{d.division_name}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </Col>
                            <Col span={12}>
                                <Form.Item label="Scope" name="scope">
                                    <Select onChange={(val) => {
                                        setEditScope(val);
                                        editForm.setFieldsValue({ depo_id: null, scope_id: null });
                                    }}>
                                        <Select.Option value="DEPO">DEPO</Select.Option>
                                        <Select.Option value="BRANCH">BRANCH</Select.Option>
                                        <Select.Option value="REGION">REGION</Select.Option>
                                        <Select.Option value="NATIONAL">NATIONAL</Select.Option>
                                    </Select>
                                </Form.Item>
                            </Col>
                        </Row>

                        {/* Dynamic Fields */}
                        {editScope === 'DEPO' && (
                            <Form.Item label="Depo / Location" name="depo_id">
                                <Select showSearch optionFilterProp="children" allowClear
                                    onChange={(val) => editForm.setFieldsValue({ scope_id: val })}
                                >
                                    {depos.map(d => <Select.Option key={d.kd_dist} value={d.kd_dist || ""}>{d.name} ({d.kd_dist})</Select.Option>)}
                                </Select>
                            </Form.Item>
                        )}

                        {editScope === 'BRANCH' && (
                            <Form.Item label="Branch" name="scope_id">
                                <Select showSearch optionFilterProp="children">
                                    {branches.map(b => <Select.Option key={b.id} value={b.id || ""}>{b.name}</Select.Option>)}
                                </Select>
                            </Form.Item>
                        )}

                        {editScope === 'REGION' && (
                            <Form.Item label="Region" name="scope_id">
                                <Select showSearch optionFilterProp="children">
                                    {regions.map(r => <Select.Option key={r.region_code} value={r.region_code || ""}>{r.name}</Select.Option>)}
                                </Select>
                            </Form.Item>
                        )}

                        <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
                            <Button onClick={() => setIsEditOpen(false)} style={{ flex: 1 }}>
                                Cancel
                            </Button>
                            <Button type="primary" htmlType="submit" loading={editing} style={{ flex: 1 }}>
                                Save Changes
                            </Button>
                        </div>
                    </>
                </Form>
            </Modal>

            {/* History Modal */}
            <Modal
                title="Assignment History"
                open={isHistoryOpen}
                onCancel={() => setIsHistoryOpen(false)}
                footer={null}
                width={600}
            >
                {loadingHistory ? <Spin /> : (
                    <Timeline
                        mode="left"
                        items={historyData.length > 0 ? historyData.map((h, idx) => ({
                            key: idx,
                            color: h.end_date ? 'gray' : 'green',
                            label: h.start_date,
                            children: (
                                <>
                                    <p><b>{h.employee_name}</b> ({h.nik})</p>
                                    <p>{h.reason || 'No specific reason'}</p>
                                    <p style={{ fontSize: '12px', color: '#999' }}>
                                        {h.start_date} - {h.end_date || 'Present'}
                                    </p>
                                </>
                            )
                        })) : [{ children: <p>No history found.</p> }]}
                    />
                )}
            </Modal>

            {/* Create Slot Modal */}
            <Modal
                title={
                    <Space>
                        <PlusOutlined />
                        <span>Create New Slot</span>
                    </Space>
                }
                open={isCreateOpen}
                onCancel={() => setIsCreateOpen(false)}
                footer={null}
                destroyOnHidden
                width={600}
            >
                <Form
                    layout="vertical"
                    onFinish={submitCreateSlot}
                    initialValues={{
                        scope: 'DEPO',
                        is_active: true,
                        level: 1
                    }}
                >
                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="Slot Code"
                                name="slot_code"
                                rules={[{ required: true, message: 'Required' }]}
                                help="Unique identifier (e.g., SL-JKT-001)"
                            >
                                <Input placeholder="SL-XXX-001" />
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="Sales Code"
                                name="sales_code"
                                rules={[{ required: true, message: 'Required' }]}
                            >
                                <Input placeholder="e.g., SO, SM, BM" />
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item
                                label="Role"
                                name="role"
                                rules={[{ required: true, message: 'Required' }]}
                            >
                                <Select>
                                    {masterRoles.map(r => (
                                        <Select.Option key={r.role_id} value={r.role_id || ""}>{r.role_name}</Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item label="Level" name="level">
                                <Select>
                                    {masterLevels.map(l => (
                                        <Select.Option key={l.code} value={l.code ? parseInt(l.code) : 0}>{l.code} - {l.name}</Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>

                    <Row gutter={16}>
                        <Col span={12}>
                            <Form.Item label="Division" name="division_id">
                                <Select allowClear>
                                    {masterDivisions.map(d => (
                                        <Select.Option key={d.division_id} value={d.division_id || ""}>{d.division_name}</Select.Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={12}>
                            <Form.Item
                                label="Scope"
                                name="scope"
                                rules={[{ required: true }]}
                            >
                                <Select onChange={(val) => setCreateScope(val)}>
                                    <Select.Option value="DEPO">DEPO</Select.Option>
                                    <Select.Option value="BRANCH">BRANCH</Select.Option>
                                    <Select.Option value="REGION">REGION</Select.Option>
                                    <Select.Option value="NATIONAL">NATIONAL</Select.Option>
                                </Select>
                            </Form.Item>
                        </Col>
                    </Row>

                    {/* Dynamic Location Fields */}
                    {createScope === 'DEPO' && (
                        <Form.Item
                            label="Depo / Location"
                            name="depo_id"
                            rules={[{ required: true, message: 'Depo required' }]}
                        >
                            <Select showSearch optionFilterProp="children">
                                {depos.map(d => <Select.Option key={d.kd_dist} value={d.kd_dist || ""}>{d.name}</Select.Option>)}
                            </Select>
                        </Form.Item>
                    )}

                    {createScope === 'BRANCH' && (
                        <Form.Item
                            label="Branch"
                            name="scope_id"
                            rules={[{ required: true, message: 'Branch required' }]}
                        >
                            <Select showSearch optionFilterProp="children">
                                {branches.map(b => <Select.Option key={b.id} value={b.id || ""}>{b.name}</Select.Option>)}
                            </Select>
                        </Form.Item>
                    )}

                    {createScope === 'REGION' && (
                        <Form.Item
                            label="Region"
                            name="scope_id"
                            rules={[{ required: true, message: 'Region required' }]}
                        >
                            <Select showSearch optionFilterProp="children">
                                {regions.map(r => <Select.Option key={r.region_code} value={r.region_code || ""}>{r.name}</Select.Option>)}
                            </Select>
                        </Form.Item>
                    )}

                    {createScope === 'NATIONAL' && (
                        <div style={{ padding: '12px', background: '#f0f0f0', borderRadius: '4px', marginBottom: '16px' }}>
                            <p style={{ margin: 0, color: '#666' }}>
                                ℹ️ National scope - no specific location required
                            </p>
                        </div>
                    )}

                    <Form.Item label="Parent Slot" name="parent_slot_code" help="Leave empty if no parent">
                        <Input placeholder="e.g., SL-MGR-001" />
                    </Form.Item>

                    <Button type="primary" htmlType="submit" loading={creating} block size="large">
                        Create Slot
                    </Button>
                </Form>
            </Modal>
        </Card>
    );
};

export default MasterSlots;
