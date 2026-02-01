
import React, { useState, useRef } from 'react';
import { Tabs, Input, Button, Space } from 'antd';
import { BranchesOutlined, TagsOutlined, DatabaseOutlined, ShopOutlined, RadiusSettingOutlined, DollarOutlined, SearchOutlined, BankOutlined } from '@ant-design/icons';
import MasterCrud from '../../components/admin/MasterCrud';
import { useAuth } from '../../contexts/AuthContext';

const MasterData = () => {
    const { user } = useAuth();
    const isSuperAdmin = user?.role === 'super_admin';

    // --- Search Helper ---
    const [searchText, setSearchText] = useState('');
    const [searchedColumn, setSearchedColumn] = useState('');
    const searchInput = useRef(null);

    const handleSearch = (selectedKeys, confirm, dataIndex) => {
        confirm();
        setSearchText(selectedKeys[0]);
        setSearchedColumn(dataIndex);
    };

    const handleReset = (clearFilters) => {
        clearFilters();
        setSearchText('');
    };

    const getColumnSearchProps = (dataIndex, nestedPath = null) => ({
        filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters, close }) => (
            <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
                <Input
                    ref={searchInput}
                    placeholder={`Search ${dataIndex}`}
                    value={selectedKeys[0]}
                    onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                    onPressEnter={() => handleSearch(selectedKeys, confirm, dataIndex)}
                    style={{ marginBottom: 8, display: 'block' }}
                />
                <Space>
                    <Button
                        type="primary"
                        onClick={() => handleSearch(selectedKeys, confirm, dataIndex)}
                        icon={<SearchOutlined />}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Search
                    </Button>
                    <Button
                        onClick={() => clearFilters && handleReset(clearFilters)}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Reset
                    </Button>
                </Space>
            </div>
        ),
        filterIcon: (filtered) => (
            <SearchOutlined style={{ color: filtered ? '#1677ff' : undefined }} />
        ),
        onFilter: (value, record) => {
            // Handle nested path if provided (e.g. ref_distributors.parent_kd_dist)
            const recordValue = nestedPath
                ? nestedPath.split('.').reduce((o, i) => o?.[i], record)
                : record[dataIndex];

            return (recordValue || '').toString().toLowerCase().includes(value.toLowerCase());
        },
        filterDropdownProps: {
            onOpenChange: (visible) => {
                if (visible) {
                    setTimeout(() => searchInput.current?.select(), 100);
                }
            },
        },
    });


    // --- Shared Company Column (Super Admin Only) ---
    const companyColumn = {
        title: 'Company ID',
        dataIndex: 'company_id',
        type: 'text', // Editable
        required: true,
        initialValue: 'ID001', // Default
        ...getColumnSearchProps('company_id'),
        sorter: (a, b) => (a.company_id || '').localeCompare(b.company_id || '')
    };

    // --- 1. BRANCH CONFIGURATION ---

    // Cleaned up hierarchy logic as per request (GRBM removed)

    const branchColumns = [
        ...(isSuperAdmin ? [companyColumn] : []),
        {
            title: 'Branch ID',
            dataIndex: 'id',
            type: 'text',
            required: true,
            disabled: true, // Read-only
            width: '15%',
            ...getColumnSearchProps('id'),
            sorter: (a, b) => (a.id || '').localeCompare(b.id || '')
        },
        {
            title: 'Branch Name',
            dataIndex: 'name',
            type: 'text',
            required: true,
            disabled: true, // Read-only
            // No width = takes remaining space
            ...getColumnSearchProps('name'),
            sorter: (a, b) => (a.name || '').localeCompare(b.name || '')
        },
        {
            title: 'Region',
            dataIndex: 'region_code',
            type: 'select',
            lookupEndpoint: '/admin/master/regions',
            lookupValue: 'region_code',
            lookupLabel: 'name',
            required: true,
            width: '20%',
            ...getColumnSearchProps('region_code'),
            sorter: (a, b) => (a.region_code || '').localeCompare(b.region_code || '')
        }
    ];

    // --- 2. DISTRIBUTOR CONFIGURATION ---
    const distributorColumns = [
        ...(isSuperAdmin ? [companyColumn] : []),
        {
            title: 'Distributor Code',
            dataIndex: 'kd_dist',
            type: 'text',
            required: true,
            disabled: true, // Read-only as per request
            ...getColumnSearchProps('kd_dist'),
            sorter: (a, b) => (a.kd_dist || '').localeCompare(b.kd_dist || '')
        },
        {
            title: 'Distributor Name',
            dataIndex: 'name',
            type: 'text',
            required: true,
            disabled: true, // Read-only as per request
            ...getColumnSearchProps('name'),
            sorter: (a, b) => (a.name || '').localeCompare(b.name || '')
        },
        {
            title: 'Branch', // Renamed from Area
            dataIndex: 'branch_id', // Database column
            type: 'select',
            lookupEndpoint: '/admin/master/branches',
            lookupValue: 'id',
            lookupLabel: 'name',
            required: true,
            // Editable (not disabled)
            ...getColumnSearchProps('branch_id', 'ref_branches.name'),
            render: (_, record) => record.ref_branches?.name || record.branch_id,
            sorter: (a, b) => (a.ref_branches?.name || '').localeCompare(b.ref_branches?.name || '')
        },
        {
            title: 'Region (Auto)',
            dataIndex: 'region_code',
            type: 'text',
            hidden: true, // Hide in form
            render: (text, record) => record.ref_branches?.region_code || '-',
            sorter: (a, b) => (a.ref_branches?.region_code || '').localeCompare(b.ref_branches?.region_code || '')
        },
        {
            title: 'Price Zone',
            dataIndex: 'price_zone_id',
            type: 'select',
            lookupEndpoint: '/admin/master/price_zones',
            lookupValue: 'id',
            lookupLabel: 'description',
            required: true,
            // Editable
            ...getColumnSearchProps('price_zone_id'),
            sorter: (a, b) => (a.price_zone_id || '').localeCompare(b.price_zone_id || '')
        },
        {
            title: 'GRBM (Auto)',
            dataIndex: 'grbm_code',
            type: 'text',
            hidden: true, // Hide in form
            render: (text, record) => record.ref_branches?.grbm_code || '-',
            sorter: (a, b) => (a.ref_branches?.grbm_code || '').localeCompare(b.ref_branches?.grbm_code || '')
        }
    ];

    // --- 3. PMA CONFIGURATION (Hierarchy View) ---
    const pmaColumns = [
        // 1. PMA Itself
        {
            title: 'PMA Code',
            dataIndex: 'pma_code',
            type: 'text',
            required: true,
            disabled: true, // Info only
            ...getColumnSearchProps('pma_code'),
            sorter: (a, b) => (a.pma_code || '').localeCompare(b.pma_code || '')
        },
        {
            title: 'PMA Name',
            dataIndex: 'pma_name',
            type: 'text',
            required: true,
            disabled: true, // Info only
            ...getColumnSearchProps('pma_name'),
            sorter: (a, b) => (a.pma_name || '').localeCompare(b.pma_name || '')
        },
        // Analysis Columns
        {
            title: 'Kd Dist Ori',
            dataIndex: 'kd_dist_ori',
            type: 'text',
            disabled: true, // Info only
            ...getColumnSearchProps('kd_dist_ori'),
            sorter: (a, b) => (a.kd_dist_ori || '').localeCompare(b.kd_dist_ori || '')
        },
        {
            title: 'Parent Kd Dist',
            dataIndex: 'parent_kd_dist',
            type: 'select',
            formOrder: 100, // Force to bottom of Edit Form
            lookupEndpoint: '/admin/master/distributors',
            lookupValue: 'kd_dist',
            lookupLabel: 'name',
            // disabled: true, // Now editable per request
            render: (_, record) => record.ref_distributors?.parent_kd_dist || record.parent_kd_dist || '-',
            // Custom search logic for nested
            ...getColumnSearchProps('parent_kd_dist', 'ref_distributors.parent_kd_dist'),
            sorter: (a, b) => (a.ref_distributors?.parent_kd_dist || '').localeCompare(b.ref_distributors?.parent_kd_dist || '')
        },
        // Distributor (Renamed to Area)
        {
            title: 'Area',
            dataIndex: 'distributor_id',
            type: 'select',
            lookupEndpoint: '/admin/master/distributors',
            lookupValue: 'kd_dist',
            lookupLabel: 'name',
            required: true,
            disabled: true, // Info only
            ...getColumnSearchProps('distributor_id', 'ref_distributors.name'),
            render: (_, record) => record.ref_distributors?.name || record.distributor_id,
            sorter: (a, b) => (a.ref_distributors?.name || '').localeCompare(b.ref_distributors?.name || '')
        }
    ];

    // --- 4. LOOKUP CONFIGURATION (Generic) ---
    const createLookupColumns = (category) => [
        {
            title: 'Code',
            dataIndex: 'code',
            type: 'text',
            required: true
        },
        {
            title: 'Name',
            dataIndex: 'name',
            type: 'text',
            required: true
        },
        {
            title: 'Category',
            dataIndex: 'category',
            type: 'text',
            hidden: true,
            initialValue: category
        }
    ];

    // --- 3. REGION CONFIGURATION ---
    const regionColumns = [
        ...(isSuperAdmin ? [companyColumn] : []),
        {
            title: 'Region Code',
            dataIndex: 'region_code',
            type: 'text',
            required: true,
            ...getColumnSearchProps('region_code'),
            sorter: (a, b) => (a.region_code || '').localeCompare(b.region_code || '')
        },
        {
            title: 'Region Name',
            dataIndex: 'name',
            type: 'text',
            required: true,
            ...getColumnSearchProps('name'),
            sorter: (a, b) => (a.name || '').localeCompare(b.name || '')
        },
        {
            title: 'GRBM',
            dataIndex: 'grbm_code',
            type: 'select',
            lookupEndpoint: '/admin/master/grbm',
            lookupValue: 'grbm_code',
            lookupLabel: 'name',
            required: true,
            // Now Editable!
            ...getColumnSearchProps('grbm_code'),
            sorter: (a, b) => (a.grbm_code || '').localeCompare(b.grbm_code || '')
        }
    ];

    // --- 5. PRICE ZONE CONFIGURATION ---
    const priceZoneColumns = [
        ...(isSuperAdmin ? [companyColumn] : []),
        {
            title: 'ID',
            dataIndex: 'id',
            type: 'text',
            required: true,
            ...getColumnSearchProps('id'),
            sorter: (a, b) => (a.id || '').localeCompare(b.id || '')
        },
        {
            title: 'Description',
            dataIndex: 'description',
            type: 'text',
            required: true,
            ...getColumnSearchProps('description'),
            sorter: (a, b) => (a.description || '').localeCompare(b.description || '')
        }
    ];

    const items = [
        {
            key: 'pma',
            label: <span><RadiusSettingOutlined /> PMA</span>,
            children: <MasterCrud
                title="PMA Hierarchy"
                endpoint="/admin/master/pma"
                columns={pmaColumns}
                rowKey="id"
                allowDelete={false}
            />
        },
        {
            key: 'distributors',
            label: <span><ShopOutlined /> Distributors</span>,
            children: <MasterCrud
                title="Distributor Management"
                endpoint="/admin/master/distributors"
                columns={distributorColumns}
                rowKey="kd_dist"
                allowDelete={false}
            />
        },
        {
            key: 'branches',
            label: <span><BankOutlined /> Branches</span>,
            children: <MasterCrud
                title="Branch Management"
                endpoint="/admin/master/branches"
                columns={branchColumns}
                allowDelete={false}
            />
        },
        {
            key: 'regions',
            label: <span><TagsOutlined /> Regions</span>,
            children: <MasterCrud
                title="Region Master"
                endpoint="/admin/master/regions"
                columns={regionColumns}
                rowKey="region_code"
            />
        },
        {
            key: 'grbm',
            label: <span><DatabaseOutlined /> GRBM</span>,
            children: <MasterCrud
                title="GRBM Master"
                endpoint="/admin/master/grbm"
                columns={[
                    { title: 'GRBM Code', dataIndex: 'grbm_code', type: 'text', required: true },
                    { title: 'GRBM Name', dataIndex: 'name', type: 'text', required: true }
                ]}
                rowKey="grbm_code"
            />
        },
        {
            key: 'price_zone',
            label: <span><DollarOutlined /> Price Zones</span>,
            children: <MasterCrud
                title="Price Zone Master"
                endpoint="/admin/master/price_zones"
                columns={priceZoneColumns}
                rowKey="id"
            />
        }
    ];

    return (
        <div style={{ padding: 24, background: '#fff' }}>
            <h2>Master Data Management</h2>
            <p style={{ color: 'gray' }}>Manage generic system lookups and hierarchy references.</p>
            <h3>Current Role: {user?.role} {isSuperAdmin ? '(SUPER)' : ''}</h3>
            <Tabs defaultActiveKey="pma" items={items} />
        </div>
    );
};

export default MasterData;
