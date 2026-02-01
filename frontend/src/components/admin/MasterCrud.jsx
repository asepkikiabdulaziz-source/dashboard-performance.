
import React, { useState, useEffect } from 'react';
import { Table, Button, Modal, Form, Input, Select, App, Popconfirm, Card, Space, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import api from '../../api';

/**
 * MasterCrud - A Generic Component for Master Data Management
 * 
 * @param {string} title - Title of the section (e.g. "Branch Management")
 * @param {string} endpoint - Base API endpoint (e.g. "/admin/master/branches")
 * @param {Array} columns - Column definitions with extra props for forms
 *   - type: 'text' | 'select' | 'number'
 *   - lookupEndpoint: API to fetch select options
 *   - lookupValue: Field for value (default: code)
 *   - lookupLabel: Field for label (default: name)
 *   - required: boolean
 */
const MasterCrud = ({
    title,
    endpoint,
    columns,
    transformPayload, // Renamed from transformData
    transformData, // Restore original for fetch logic
    rowKey = 'id', // Optional: custom row key (e.g. 'kd_dist' or 'pma_code')
    allowDelete = true
}) => {
    const { message } = App.useApp(); // Use hook from App context
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [modalVisible, setModalVisible] = useState(false);
    const [editingItem, setEditingItem] = useState(null);
    const [form] = Form.useForm();
    const [lookups, setLookups] = useState({});


    // === 1. Fetch Data ===
    const fetchData = async () => {
        setLoading(true);
        try {
            const response = await api.get(`${endpoint}`);
            let finalData = response.data;
            if (transformData) {
                finalData = transformData(finalData);
            }
            setData(finalData);
        } catch (error) {
            message.error(`Failed to load ${title}: ${error.message}`);
        } finally {
            setLoading(false);
        }
    };

    // === 2. Fetch Lookups (Smart Dropdowns) ===
    useEffect(() => {
        const fetchLookups = async () => {
            const newLookups = {};
            for (const col of columns) {
                if (col.type === 'select' && col.lookupEndpoint) {
                    try {
                        const res = await api.get(`${col.lookupEndpoint}`);
                        newLookups[col.dataIndex] = res.data;
                    } catch (e) {
                        console.error(`Failed to load lookup for ${col.dataIndex}`, e);
                    }
                }
            }
            setLookups(newLookups);
        };
        fetchLookups();
        fetchData();
    }, [endpoint]); // Re-run if endpoint changes

    // === 3. CRUD Operations ===
    // Fix: Set form values strictly after modal/form is visible/mounted
    useEffect(() => {
        if (modalVisible) {
            // Small timeout to ensure Form instance is connected
            const timer = setTimeout(() => {
                if (editingItem) {
                    // DEBUG TYPE MISMATCH
                    if (editingItem.parent_kd_dist !== undefined) {
                        console.log('DEBUG FORM VALUE:', editingItem.parent_kd_dist, typeof editingItem.parent_kd_dist);
                        const lookupOpts = lookups['parent_kd_dist'] || [];
                        if (lookupOpts.length > 0) {
                            const sample = lookupOpts[0];
                            // lookupValue is 'kd_dist' based on MasterData config
                            const val = sample['kd_dist'];
                            console.log('DEBUG OPTION VALUE:', val, typeof val);
                        } else {
                            console.log('DEBUG OPTIONS: Empty');
                        }
                    }
                    form.setFieldsValue(editingItem);
                } else {
                    form.resetFields();
                    const initialValues = {};
                    columns.forEach(c => {
                        if (c.initialValue) initialValues[c.dataIndex] = c.initialValue;
                    });
                    form.setFieldsValue(initialValues);
                }
            }, 0);
            return () => clearTimeout(timer);
        }
    }, [modalVisible, editingItem, form]);

    const handleAdd = () => {
        setEditingItem(null);
        setModalVisible(true);
    };

    const handleEdit = (record) => {
        // Flatten nested data for Form (mismatch fix)
        const formRecord = { ...record };
        if (record.ref_distributors && record.ref_distributors.parent_kd_dist) {
            formRecord.parent_kd_dist = record.ref_distributors.parent_kd_dist;
        }

        setEditingItem(formRecord);
        console.log('Editing Record (Fixed):', formRecord); // DEBUG
        setModalVisible(true);
    };

    const handleDelete = async (record) => {
        try {
            const id = record[rowKey];
            await api.delete(`${endpoint}/${id}`);
            message.success('Deleted successfully');
            fetchData();
        } catch (error) {
            message.error('Failed to delete: ' + (error.response?.data?.detail || error.message));
        }
    };

    const handleSubmit = async (values) => {
        try {
            if (editingItem) {
                // UPDATE (Use the rowKey prop for the identifier)
                const id = editingItem[rowKey];
                await api.put(`${endpoint}/${id}`, values);
                message.success('Updated successfully');
            } else {
                // CREATE
                await api.post(`${endpoint}`, values);
                message.success('Created successfully');
            }
            setModalVisible(false);
            fetchData();
        } catch (error) {
            message.error('Operation failed: ' + (error.response?.data?.detail || error.message));
        }
    };

    // === 4. Generate Table Columns ===
    const tableColumns = [
        ...columns.map(col => ({
            ...col, // Inherit all other props (sorter, filters, width, etc.)
            title: col.title,
            dataIndex: col.dataIndex,
            key: col.key || col.dataIndex,
            render: (text, record) => {
                // Priority 1: Custom Render (if provided in column definition)
                if (col.render) {
                    return col.render(text, record);
                }

                // Priority 2: Lookup Render (if type='select')
                if (col.type === 'select' && lookups[col.dataIndex]) {
                    const found = lookups[col.dataIndex].find(
                        item => item[col.lookupValue || 'code'] === text
                    );
                    return found ? <Tag style={{ fontSize: '13px', padding: '2px 8px' }}>{found[col.lookupLabel || 'name']}</Tag> : text;
                }

                // Priority 3: Default Text
                return text;
            }
        })),
        {
            title: 'Actions',
            key: 'actions',
            width: 120,
            render: (_, record) => (
                <Space>
                    <Button
                        type="text"
                        icon={<EditOutlined style={{ color: 'blue' }} />}
                        onClick={() => handleEdit(record)}
                    />
                    {allowDelete !== false && (
                        <Popconfirm
                            title="Deletion"
                            description="Are you sure to delete this item?"
                            onConfirm={() => handleDelete(record)}
                            okText="Yes" cancelText="No"
                        >
                            <Button
                                type="text"
                                icon={<DeleteOutlined style={{ color: 'red' }} />}
                            />
                        </Popconfirm>
                    )}
                </Space>
            )
        }
    ];

    return (
        <Card
            title={title}
            extra={
                <Space>
                    <Button icon={<ReloadOutlined />} onClick={fetchData}>Refresh</Button>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>Add New</Button>
                </Space>
            }
            variant="borderless"
            style={{ marginBottom: 24 }}
        >

            <Table
                columns={tableColumns}
                dataSource={data}
                rowKey={rowKey || (record => record.id || record.code)}
                loading={loading}
                pagination={{ pageSize: 10 }}
            />

            <Modal
                title={editingItem ? `Edit ${title}` : `Add New ${title}`}
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                onOk={() => form.submit()}
                destroyOnHidden
            >
                <Form form={form} layout="vertical" onFinish={handleSubmit}>
                    {[...columns]
                        .sort((a, b) => (a.formOrder || 0) - (b.formOrder || 0))
                        .map(col => (
                            <Form.Item
                                key={col.dataIndex}
                                name={col.dataIndex}
                                label={col.title}
                                rules={[{ required: col.required, message: `Please input ${col.title}` }]}
                                hidden={col.hidden} // e.g. for ID fields
                            >
                                {col.type === 'select' ? (
                                    <Select
                                        placeholder={`Select ${col.title}`}
                                        loading={!lookups[col.dataIndex]}
                                        allowClear
                                        disabled={col.disabled}
                                        showSearch
                                        optionFilterProp="children"
                                        filterOption={(input, option) =>
                                            (option?.children ?? '').toString().toLowerCase().includes(input.toLowerCase())
                                        }
                                        onChange={(val) => {
                                            if (col.onChange) {
                                                col.onChange(val, form);
                                            }
                                        }}
                                    >
                                        {(lookups[col.dataIndex] || []).map(opt => (
                                            <Select.Option
                                                key={opt[col.lookupValue || 'code']}
                                                value={opt[col.lookupValue || 'code'] || ""}
                                            >
                                                {opt[col.lookupLabel || 'name']}
                                                <span style={{ color: '#999', marginLeft: 8, fontSize: '0.8em' }}>
                                                    ({opt[col.lookupValue || 'code']})
                                                </span>
                                            </Select.Option>
                                        ))}
                                    </Select>
                                ) : (
                                    <Input disabled={col.disabled} />
                                )}
                            </Form.Item>
                        ))}
                </Form>
            </Modal>
        </Card>
    );
};

export default MasterCrud;
