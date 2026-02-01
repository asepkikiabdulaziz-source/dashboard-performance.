import { useState, useEffect } from 'react';
import {
    Table,
    Button,
    Space,
    Modal,
    Form,
    Input,
    Select,
    Switch,
    Card,
    Alert,
    message,
    Tag,
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    UserAddOutlined,
    ReloadOutlined,
    ImportOutlined,
    ExportOutlined,
    InboxOutlined,
    SearchOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../api';

const { Option } = Select;

const Employees = () => {
    const { hasPermission } = useAuth();
    const [employees, setEmployees] = useState([]);
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(false);

    // Pagination State
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 10,
        total: 0
    });

    const [searchText, setSearchText] = useState('');
    const [roleFilter, setRoleFilter] = useState('all');

    const [modalVisible, setModalVisible] = useState(false);
    const [editingEmployee, setEditingEmployee] = useState(null);
    const [createAuthUser, setCreateAuthUser] = useState(false);
    const [form] = Form.useForm();
    const [messageApi, contextHolder] = message.useMessage();

    // Import State
    const [importVisible, setImportVisible] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [importResults, setImportResults] = useState(null);

    useEffect(() => {
        if (!hasPermission('auth.user.manage')) {
            message.error('Access Denied');
            return;
        }
        fetchEmployees();
        fetchRoles();
    }, []);

    const fetchRoles = async () => {
        try {
            const response = await api.get('/admin/employees/roles');
            setRoles(response.data);
        } catch (error) {
            console.error('Failed to fetch roles');
        }
    };

    const fetchEmployees = async (page = 1, pageSize = 10) => {
        setLoading(true);
        try {
            const response = await api.get('/admin/employees/', {
                params: {
                    page,
                    page_size: pageSize,
                    search: searchText,
                    role: roleFilter
                }
            });

            // New Response Format: { data, total, page, pageSize }
            const { data, total } = response.data;

            setEmployees(data);
            setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: pageSize,
                total: total
            }));

        } catch (error) {
            messageApi.error('Failed to fetch employees');
        } finally {
            setLoading(false);
        }
    };

    const handleTableChange = (newPagination) => {
        fetchEmployees(newPagination.current, newPagination.pageSize);
    };

    const handleExport = async () => {
        try {
            const response = await api.get('/admin/employees/export', {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `employees_export_${new Date().getTime()}.csv`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (error) {
            messageApi.error('Export failed');
        }
    };

    const handleUpload = async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        setUploading(true);

        try {
            const response = await api.post('/admin/employees/upload', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setImportResults(response.data);
            if (response.data.valid_rows > 0) {
                messageApi.success(`Imported ${response.data.valid_rows} employees successfully`);
                fetchEmployees();
            }
            if (response.data.invalid_rows > 0) {
                messageApi.warning(`${response.data.invalid_rows} rows failed validation`);
            }
        } catch (error) {
            messageApi.error('Upload failed: ' + (error.response?.data?.detail || error.message));
        } finally {
            setUploading(false);
        }
    };

    const handleCreate = () => {
        setEditingEmployee(null);
        setCreateAuthUser(false);
        form.resetFields();
        setModalVisible(true);
    };

    const handleEdit = (record) => {
        setEditingEmployee(record);
        setCreateAuthUser(false);
        form.setFieldsValue({
            ...record,
            is_active: record.is_active
        });
        setModalVisible(true);
    };

    const handleSubmit = async (values) => {
        try {
            if (editingEmployee) {
                await api.put(`/admin/employees/${editingEmployee.nik}`, values);
                messageApi.success('Employee updated successfully');
            } else {
                await api.post('/admin/employees/', values);
                messageApi.success('Employee (and User) created successfully');
            }
            setModalVisible(false);
            fetchEmployees(pagination.current, pagination.pageSize);
        } catch (error) {
            console.error(error);
            const errorMsg = error.response?.data?.detail || 'Operation failed';
            messageApi.error(errorMsg);
        }
    };

    const columns = [
        {
            title: 'NIK',
            dataIndex: 'nik',
            key: 'nik',
            width: 120,
        },
        {
            title: 'Name',
            dataIndex: 'full_name',
            key: 'full_name',
            width: 200,
        },
        {
            title: 'Role',
            dataIndex: 'role_name',
            key: 'role_name',
            width: 150,
            render: (role, record) => {
                const r = record.role_id?.toUpperCase();
                let color = 'default';
                if (r === 'ADMIN') color = 'red';
                else if (r === 'SPV' || r === 'SUPERVISOR') color = 'blue';
                else if (r === 'SALESMAN' || r === 'SALES') color = 'green';
                else if (r === 'BM' || r === 'RBM') color = 'purple';

                return (
                    <Tag color={color}>
                        {role || record.role_id}
                    </Tag>
                );
            }
        },
        {
            title: 'Email',
            dataIndex: 'email',
            key: 'email',
            width: 200,
        },
        {
            title: 'System Access',
            dataIndex: 'auth_user_id',
            key: 'auth_user_id',
            width: 120,
            render: (auth_id) => (
                <Tag color={auth_id ? 'purple' : 'default'}>
                    {auth_id ? 'Enabled' : 'No Access'}
                </Tag>
            )
        },
        {
            title: 'Status',
            dataIndex: 'is_active',
            key: 'is_active',
            width: 100,
            render: (isActive) => (
                <Tag color={isActive ? 'success' : 'default'}>
                    {isActive ? 'Active' : 'Inactive'}
                </Tag>
            )
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 120,
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    >
                        Edit
                    </Button>
                </Space>
            )
        }
    ];

    const errorColumns = [
        {
            title: 'Row',
            dataIndex: 'row_number',
            key: 'row_number',
            width: 60,
        },
        {
            title: 'NIK',
            dataIndex: ['row_data', 'nik'],
            key: 'nik',
            width: 100,
        },
        {
            title: 'Name',
            dataIndex: ['row_data', 'full_name'],
            key: 'full_name',
            width: 150,
        },
        {
            title: 'Role',
            dataIndex: ['row_data', 'role_id'],
            key: 'role',
            width: 100,
        },
        {
            title: 'Error',
            dataIndex: 'error_message',
            key: 'error',
            render: (text) => <span style={{ color: 'red' }}>{text}</span>
        }
    ];

    return (
        <div style={{ padding: 24 }}>
            {contextHolder}
            <Card>
                <div style={{ marginBottom: 16 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                        <div style={{ fontSize: 16, fontWeight: 'bold' }}>Employee Management</div>
                        <Space>
                            <Button icon={<ImportOutlined />} onClick={() => { setImportVisible(true); setImportResults(null); }}>
                                Import CSV
                            </Button>
                            <Button icon={<ExportOutlined />} onClick={handleExport}>
                                Export CSV
                            </Button>
                            <Button icon={<ReloadOutlined />} onClick={() => fetchEmployees(1, pagination.pageSize)}>
                                Refresh
                            </Button>
                            <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                                Add Employee
                            </Button>
                        </Space>
                    </div>

                    {/* Search & Filter Bar */}
                    <Space style={{ width: '100%', justifyContent: 'flex-start' }}>
                        <Input
                            placeholder="Search by Name or NIK"
                            prefix={<SearchOutlined />}
                            style={{ width: 300 }}
                            value={searchText}
                            onChange={e => setSearchText(e.target.value)}
                            onPressEnter={() => fetchEmployees(1, pagination.pageSize)}
                            allowClear
                        />
                        <Select
                            defaultValue="all"
                            style={{ width: 200 }}
                            onChange={val => {
                                setRoleFilter(val);
                            }}
                        >
                            <Select.Option value="all">All Roles</Select.Option>
                            {roles.map(role => (
                                <Select.Option key={role.role_id} value={role.role_id || ""}>
                                    {role.role_name || role.role_id}
                                </Select.Option>
                            ))}
                        </Select>
                        <Button type="primary" onClick={() => fetchEmployees(1, pagination.pageSize)}>Search</Button>
                    </Space>
                </div>

                <Table
                    columns={columns}
                    dataSource={employees}
                    rowKey="nik"
                    loading={loading}
                    pagination={{
                        current: pagination.current,
                        pageSize: pagination.pageSize,
                        total: pagination.total,
                        showSizeChanger: true,
                        showTotal: (total) => `Total ${total} employees`
                    }}
                    onChange={handleTableChange}
                />
            </Card>

            {/* Import Modal */}
            <Modal
                title="Import Employees (CSV/Excel)"
                open={importVisible}
                onCancel={() => setImportVisible(false)}
                footer={null}
                width={800}
            >
                {!importResults ? (
                    <div style={{ padding: 20, textAlign: 'center', border: '1px dashed #d9d9d9', borderRadius: 4 }}>
                        <p className="ant-upload-drag-icon">
                            <InboxOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                        </p>
                        <p className="ant-upload-text">Dataset Upload</p>
                        <p className="ant-upload-hint">
                            Support for a single or bulk upload. Strictly prohibit from uploading company data.
                        </p>
                        <input
                            type="file"
                            accept=".csv, .xls, .xlsx"
                            style={{ marginTop: 10 }}
                            onChange={(e) => {
                                if (e.target.files?.[0]) handleUpload(e.target.files[0]);
                            }}
                            disabled={uploading}
                        />
                        {uploading && <div style={{ marginTop: 10 }}>Uploading...</div>}
                    </div>
                ) : (
                    <div>
                        <div style={{ marginBottom: 16 }}>
                            <Alert
                                message={`Upload Complete. Valid: ${importResults.valid_rows}, Failed: ${importResults.invalid_rows}`}
                                type={importResults.invalid_rows > 0 ? "warning" : "success"}
                                showIcon
                            />
                        </div>
                        {importResults.invalid_rows > 0 && (
                            <>
                                <h4>Failed Rows Details:</h4>
                                <Table
                                    columns={errorColumns}
                                    dataSource={importResults.errors}
                                    rowKey="row_number"
                                    size="small"
                                    pagination={{ pageSize: 5 }}
                                    scroll={{ y: 240 }}
                                />
                            </>
                        )}
                        <Button type="primary" onClick={() => { setImportVisible(false); setImportResults(null); }} style={{ marginTop: 16 }}>
                            Close
                        </Button>
                    </div>
                )}
            </Modal>

            <Modal
                title={editingEmployee ? `Edit Employee: ${editingEmployee.full_name}` : 'Create New Employee'}
                open={modalVisible}
                onCancel={() => setModalVisible(false)}
                footer={null}
                width={600}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{ is_active: true, create_auth_user: false }}
                >
                    <Form.Item
                        name="nik"
                        label="NIK"
                        rules={[{ required: true, message: 'Please enter NIK' }]}
                    >
                        <Input placeholder="Employee ID" disabled={!!editingEmployee} />
                    </Form.Item>

                    <Form.Item
                        name="full_name"
                        label="Full Name"
                        rules={[{ required: true, message: 'Please enter full name' }]}
                    >
                        <Input placeholder="John Doe" />
                    </Form.Item>

                    <Form.Item
                        name="role_id"
                        label="Role"
                        rules={[{ required: true, message: 'Please select role' }]}
                    >
                        <Select placeholder="Select role">
                            {roles.map(role => (
                                <Select.Option key={role.role_id} value={role.role_id || ""}>
                                    {role.role_name || role.role_id}
                                </Select.Option>
                            ))}
                        </Select>
                    </Form.Item>

                    <Form.Item
                        name="email"
                        label="Email"
                        rules={[
                            { type: 'email', message: 'Invalid email format' },
                            { required: createAuthUser, message: 'Email is required for system access' }
                        ]}
                    >
                        <Input placeholder="john@example.com" />
                    </Form.Item>

                    <Form.Item
                        name="phone_number"
                        label="Phone Number"
                    >
                        <Input placeholder="+62..." />
                    </Form.Item>

                    {/* Access Control Sections Omitted for brevity, but logic should be here */}
                    {(!editingEmployee || !editingEmployee.auth_user_id) && (
                        <Card size="small" style={{ marginBottom: 24, background: '#f9f9f9' }}>
                            <Form.Item
                                name="create_auth_user"
                                valuePropName="checked"
                                noStyle
                            >
                                <Switch
                                    onChange={(checked) => setCreateAuthUser(checked)}
                                    checkedChildren={<UserAddOutlined />}
                                    unCheckedChildren={<UserAddOutlined />}
                                />
                            </Form.Item>
                            <span style={{ marginLeft: 8, fontWeight: 500 }}>
                                {editingEmployee ? 'Grant System Access Now' : 'Grant System Access'}
                            </span>

                            {createAuthUser && (
                                <div style={{ marginTop: 16 }}>
                                    <Form.Item
                                        name="password"
                                        label="Initial Password"
                                        rules={[{ required: true, message: 'Password is required' }]}
                                    >
                                        <Input.Password placeholder="Min. 6 characters" />
                                    </Form.Item>
                                </div>
                            )}
                        </Card>
                    )}

                    <Form.Item
                        name="is_active"
                        label="Status"
                        valuePropName="checked"
                    >
                        <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
                    </Form.Item>

                    <div style={{ textAlign: 'right' }}>
                        <Space>
                            <Button onClick={() => setModalVisible(false)}>Cancel</Button>
                            <Button type="primary" htmlType="submit">
                                {editingEmployee ? 'Update' : 'Create'}
                            </Button>
                        </Space>
                    </div>
                </Form>
            </Modal>
        </div>
    );
};

export default Employees;
