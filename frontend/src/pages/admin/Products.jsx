import React, { useState, useEffect, useMemo } from 'react';
import {
    Table,
    Button,
    Space,
    Modal,
    Form,
    Input,
    InputNumber,
    Select,
    Switch,
    Tag,
    Typography,
    Popconfirm,
    Card,
    Tabs,
    AutoComplete,
    Badge,
    App,
    Radio
} from 'antd';
import {
    PlusOutlined,
    EditOutlined,
    DeleteOutlined,
    DownloadOutlined,
    SearchOutlined,
    ReloadOutlined,
    ExportOutlined,
    StarOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import api from '../../api';

const { Option } = Select;
const { TabPane } = Tabs;

const Products = () => {
    const { user, hasPermission } = useAuth();
    const [flatProducts, setFlatProducts] = useState([]); // All products fetched from API
    const [displayData, setDisplayData] = useState([]); // Tree data after filters/sort
    const [categories, setCategories] = useState([]);
    const [principals, setPrincipals] = useState([]);
    const [brands, setBrands] = useState([]);
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(false);

    // Ant Design message hook
    const { message: messageApi } = App.useApp();

    // Pagination State
    const [pagination, setPagination] = useState({
        current: 1,
        pageSize: 10,
        total: 0
    });

    const [modalVisible, setModalVisible] = useState(false);
    const [editingProduct, setEditingProduct] = useState(null);
    const [form] = Form.useForm();
    const [searchText, setSearchText] = useState('');
    const [categoryFilter, setCategoryFilter] = useState([]);
    const [brandFilter, setBrandFilter] = useState([]);
    const [activeFilter, setActiveFilter] = useState([]);
    const [nplFilter, setNplFilter] = useState(null);
    const [principalFilter, setPrincipalFilter] = useState([]);
    const [priceSegmentFilter, setPriceSegmentFilter] = useState([]);
    const [companyFilter, setCompanyFilter] = useState([]);
    const [identitySortField, setIdentitySortField] = useState('product_name');
    const [sorters, setSorters] = useState([{ field: 'product_name', order: 'ascend', priority: 5 }]);

    // Get official lists for filters
    // Get official lists for filters - ensuring uniqueness to avoid key warnings
    const getUniqueList = (list) => {
        const map = new Map();
        list.forEach(item => {
            if (item.id && !map.has(String(item.id).trim().toUpperCase())) {
                map.set(String(item.id).trim().toUpperCase(), { text: item.name || item.id, value: item.id });
            }
        });
        return Array.from(map.values()).sort((a, b) => (a.text || '').localeCompare(b.text || ''));
    };

    const officialCategories = getUniqueList(categories);
    const officialPrincipals = getUniqueList(principals);
    const officialBrands = getUniqueList(brands);
    const officialCompanies = getUniqueList(companies);



    const getDependentOptions = (fieldName, baseList, currentFilters, isRaw = false) => {
        const otherFilters = { ...currentFilters };
        delete otherFilters[fieldName];

        const reachableProducts = flatProducts.filter(node => {
            const catMatch = !otherFilters.category_id || otherFilters.category_id.length === 0 ||
                (node.category_id && otherFilters.category_id.some(c => String(c).toUpperCase() === String(node.category_id).trim().toUpperCase()));
            const brandMatch = !otherFilters.brand_id || otherFilters.brand_id.length === 0 ||
                (node.brand_id && otherFilters.brand_id.some(b => String(b).toUpperCase() === String(node.brand_id).trim().toUpperCase()));
            const principalMatch = !otherFilters.principal_id || otherFilters.principal_id.length === 0 ||
                (node.principal_id && otherFilters.principal_id.some(p => String(p).toUpperCase() === String(node.principal_id).trim().toUpperCase()));
            const companyMatch = !otherFilters.company_id || otherFilters.company_id.length === 0 ||
                (node.company_id && otherFilters.company_id.some(c => String(c).toUpperCase() === String(node.company_id).trim().toUpperCase()));
            const priceMatch = !otherFilters.price_segment || otherFilters.price_segment.length === 0 ||
                (node.price_segment && otherFilters.price_segment.some(p => String(p).toUpperCase() === String(node.price_segment).trim().toUpperCase()));

            const activeMatch = !otherFilters.active_states || otherFilters.active_states.length === 0 ||
                otherFilters.active_states.includes(node.is_active);
            const nplMatch = otherFilters.npl_filter === null || node.is_npl === otherFilters.npl_filter;

            const searchMatch = !searchText ||
                node.product_name.toLowerCase().includes(searchText.toLowerCase()) ||
                node.sku_code.toLowerCase().includes(searchText.toLowerCase());

            return catMatch && brandMatch && principalMatch && companyMatch && priceMatch && activeMatch && nplMatch && searchMatch;
        });

        if (fieldName === 'status') {
            const options = [];
            if (reachableProducts.some(p => p.is_active === true)) options.push({ text: 'Active', value: true });
            if (reachableProducts.some(p => p.is_active === false)) options.push({ text: 'Inactive', value: false });
            if (reachableProducts.some(p => p.is_npl === true)) options.push({ text: 'NPL', value: 'npl' });
            return options;
        }

        if (isRaw) {
            const available = [...new Set(reachableProducts.map(p => String(p[fieldName] || '').trim()))]
                .filter(Boolean)
                .sort();
            return available.map(v => ({ text: v, value: v }));
        }

        const availableIds = new Set(reachableProducts.map(p => String(p[fieldName] || '').trim().toUpperCase()));
        return baseList.filter(opt => availableIds.has(String(opt.value).trim().toUpperCase()));
    };

    const dependentFilters = useMemo(() => {
        const currentFilters = {
            category_id: categoryFilter,
            brand_id: brandFilter,
            principal_id: principalFilter,
            company_id: companyFilter,
            price_segment: priceSegmentFilter,
            active_states: activeFilter,
            npl_filter: nplFilter
        };

        return {
            categories: getDependentOptions('category_id', officialCategories, currentFilters),
            principals: getDependentOptions('principal_id', officialPrincipals, currentFilters),
            brands: getDependentOptions('brand_id', officialBrands, currentFilters),
            companies: getDependentOptions('company_id', officialCompanies, currentFilters),
            priceSegments: getDependentOptions('price_segment', [], currentFilters, true),
            status: getDependentOptions('status', [], currentFilters)
        };
    }, [flatProducts, categoryFilter, brandFilter, principalFilter, companyFilter, priceSegmentFilter, activeFilter, nplFilter, searchText, officialCategories, officialPrincipals, officialBrands, officialCompanies]);

    useEffect(() => {
        let isMounted = true;
        const init = async () => {
            if (!hasPermission('product.manage')) {
                if (isMounted) messageApi.error('Access denied. Missing permissions.');
                return;
            }
            await fetchProducts();
            await fetchCategories();
            await fetchPrincipals();
            await fetchBrands();
            await fetchCompanies();
        };
        init();
        return () => { isMounted = false; };
    }, [user]);

    const fetchCategories = async () => {
        try {
            const response = await api.get('/admin/products/categories');
            setCategories(response.data || []);
        } catch (error) {
            messageApi.error('Failed to fetch categories');
        }
    };

    const fetchPrincipals = async () => {
        try {
            const response = await api.get('/admin/products/principals');
            setPrincipals(response.data || []);
        } catch (error) {
            messageApi.error('Failed to fetch principals');
        }
    };

    const fetchBrands = async () => {
        try {
            const response = await api.get('/admin/products/brands');
            setBrands(response.data || []);
        } catch (error) {
            messageApi.error('Failed to fetch brands');
        }
    };

    const fetchCompanies = async () => {
        try {
            const response = await api.get('/admin/products/companies');
            setCompanies(response.data || []);
        } catch (error) {
            messageApi.error('Failed to fetch companies');
        }
    };

    const getOfficialName = (list, id) => {
        if (!id) return '-';
        const official = list.find(item =>
            String(item.id).trim().toUpperCase() === String(id).trim().toUpperCase()
        );
        return official ? official.name : id;
    };

    const fetchProducts = async () => {
        setLoading(true);
        try {
            const response = await api.get('/admin/products', {
                params: {
                    page: 1,
                    page_size: 2000, // Fetch all for tree view
                }
            });

            const { data } = response.data;
            setFlatProducts(data || []);
            processTreeData(data || [], searchText, categoryFilter, brandFilter, activeFilter, nplFilter, principalFilter, priceSegmentFilter, sorters);
        } catch (error) {
            messageApi.error('Failed to fetch products');
        } finally {
            setLoading(false);
        }
    };

    // Helper to build tree and apply filters/sort
    const processTreeData = (data, search, cat, brand, active, npl, principal, priceSegment, sorters, company = []) => {
        // 1. Strict Master Filter (Flat) - Normalized Comparison
        let flatFiltered = data.filter(node => {
            const catMatch = cat.length === 0 ||
                (node.category_id && cat.some(c => c.toUpperCase() === node.category_id.trim().toUpperCase()));
            const brandMatch = brand.length === 0 ||
                (node.brand_id && brand.some(b => b.toUpperCase() === node.brand_id.trim().toUpperCase()));
            const activeMatch = active === null || (Array.isArray(active) ? (active.length === 0 || active.includes(node.is_active)) : node.is_active === active);
            const nplMatch = npl === null || node.is_npl === npl;
            const principalMatch = principal.length === 0 ||
                (node.principal_id && principal.some(p => p.toUpperCase() === node.principal_id.trim().toUpperCase()));
            const priceMatch = priceSegment.length === 0 ||
                (node.price_segment && priceSegment.some(p => p.toUpperCase() === node.price_segment.trim().toUpperCase()));
            const companyMatch = company.length === 0 ||
                (node.company_id && company.some(c => c.toUpperCase() === node.company_id.trim().toUpperCase()));

            return catMatch && brandMatch && activeMatch && nplMatch && principalMatch && priceMatch && companyMatch;
        });

        const buildTree = (items, parentCode = null, level = 0) => {
            const children = items
                .filter(item => {
                    if (parentCode === null) {
                        const hasParentInList = items.some(p => p.sku_code === item.parent_sku_code && p.sku_code !== item.sku_code);
                        return !hasParentInList || item.parent_sku_code === item.sku_code;
                    }
                    return item.parent_sku_code === parentCode && item.sku_code !== parentCode;
                })
                .map(item => {
                    const nodeChildren = buildTree(items, item.sku_code, level + 1);
                    const node = { ...item, level };
                    if (nodeChildren && nodeChildren.length > 0) {
                        node.children = nodeChildren;
                    }
                    return node;
                });
            return children;
        };

        const initialTree = buildTree(flatFiltered);

        // 2. Recursive Search Filter (Hierarchical)
        const applySearch = (nodes) => {
            if (!search) return nodes;

            const results = [];
            nodes.forEach(node => {
                const nameMatch = node.product_name.toLowerCase().includes(search.toLowerCase());
                const skuMatch = node.sku_code.toLowerCase().includes(search.toLowerCase());
                const aliasMatch = node.short_name && node.short_name.toLowerCase().includes(search.toLowerCase());
                const brandTxtMatch = node.brand_id && node.brand_id.toLowerCase().includes(search.toLowerCase());
                const parentSkuMatch = node.parent_sku_code && node.parent_sku_code.toLowerCase().includes(search.toLowerCase());
                const parentNameMatch = node.parent_sku_name && node.parent_sku_name.toLowerCase().includes(search.toLowerCase());

                const selfMatch = nameMatch || skuMatch || aliasMatch || brandTxtMatch || parentSkuMatch || parentNameMatch;

                let filteredChildren = [];
                if (node.children) {
                    filteredChildren = applySearch(node.children);
                }

                if (selfMatch || filteredChildren.length > 0) {
                    const matchedNode = { ...node };
                    if (filteredChildren.length > 0) {
                        matchedNode.children = filteredChildren;
                    } else {
                        delete matchedNode.children;
                    }
                    results.push(matchedNode);
                }
            });
            return results;
        };

        const searchedTree = applySearch(initialTree);

        // Recursive tree sorting
        const sortTree = (nodes) => {
            if (!nodes || nodes.length === 0) return [];
            if (!sorters || sorters.length === 0) return nodes;

            const sortedNodes = [...nodes].sort((a, b) => {
                for (const sortInfo of sorters) {
                    const { field, order } = sortInfo;
                    if (!order) continue;

                    let valA = a[field];
                    let valB = b[field];

                    if (valA === null || valA === undefined) valA = '';
                    if (valB === null || valB === undefined) valB = '';

                    if (valA === valB) continue;

                    const multiplier = order === 'ascend' ? 1 : -1;
                    if (typeof valA === 'string' && typeof valB === 'string') {
                        return valA.localeCompare(valB) * multiplier;
                    }
                    return (valA > valB ? 1 : -1) * multiplier;
                }
                return 0;
            });

            return sortedNodes.map(node => {
                if (node.children && node.children.length > 0) {
                    return { ...node, children: sortTree(node.children) };
                }
                return node;
            });
        };

        const sortedTree = sortTree(searchedTree);

        // Final tree data
        setDisplayData(sortedTree);
    };

    useEffect(() => {
        processTreeData(flatProducts, searchText, categoryFilter, brandFilter, activeFilter, nplFilter, principalFilter, priceSegmentFilter, sorters, companyFilter);
    }, [flatProducts, searchText, categoryFilter, brandFilter, activeFilter, nplFilter, principalFilter, priceSegmentFilter, sorters, companyFilter, categories, brands, principals, companies]);

    const handleTableChange = (newPagination, filters, sorter) => {
        // Define priorities (Smaller = More Important)
        const sortPriority = {
            'category_id': 1,
            'brand_id': 2,
            'principal_id': 3,
            'price_segment': 4,
            'product_name': 5,
            'is_active': 6
        };

        // Multi-level Sorter
        const sorterArray = Array.isArray(sorter) ? sorter : (sorter.field ? [sorter] : []);
        const newSorters = sorterArray
            .map(s => {
                const field = s.field === 'product_name' ? identitySortField : s.field;
                return {
                    field: field,
                    order: s.order,
                    priority: sortPriority[field] || 99
                };
            })
            .filter(s => s.order)
            .sort((a, b) => a.priority - b.priority);

        if (newSorters.length === 0) {
            setSorters([{ field: 'product_name', order: 'ascend', priority: 5 }]);
        } else {
            setSorters(newSorters);
        }

        // Excel-like Filters (Selective Update)
        if ('product_name' in filters) setSearchText(filters.product_name ? (filters.product_name[0] || '') : '');
        if ('category_id' in filters) setCategoryFilter(filters.category_id || []);
        if ('brand_id' in filters) setBrandFilter(filters.brand_id || []);
        if ('brand_merged' in filters) setBrandFilter(filters.brand_merged || []);
        if ('principal_id' in filters) setPrincipalFilter(filters.principal_id || []);
        if ('price_segment' in filters) setPriceSegmentFilter(filters.price_segment || []);
        if ('company_id' in filters) setCompanyFilter(filters.company_id || []);

        // Handling Status (Active/Inactive + NPL)
        if ('status' in filters) {
            const statusVals = filters.status || [];
            const hasNpl = statusVals.includes('npl');
            const activeValues = statusVals.filter(v => v !== 'npl');
            setActiveFilter(activeValues);
            setNplFilter(hasNpl ? true : null);
        }
    };

    const handleReset = () => {
        setSearchText('');
        setCategoryFilter([]);
        setBrandFilter([]);
        setActiveFilter([]);
        setNplFilter(null);
        setPrincipalFilter([]);
        setPriceSegmentFilter([]);
        setSorters([{ field: 'product_name', order: 'ascend' }]);
        messageApi.success('Filters reset');
    };
    const handleSearch = () => {
        // Search is now real-time via useEffect but we keep the button for UX
        messageApi.info('Searching catalog...', 0.5);
    };

    const handleCreate = () => {
        setEditingProduct(null);
        form.resetFields();
        setModalVisible(true);
    };

    const handleEdit = (record) => {
        setEditingProduct(record);
        form.setFieldsValue(record);
        setModalVisible(true);
    };

    const handleDelete = async (sku_code) => {
        try {
            await api.delete(`/admin/products/${sku_code}`);
            messageApi.success('Product deleted successfully');
            fetchProducts();
        } catch (error) {
            messageApi.error('Failed to delete product');
        }
    };

    const handleSubmit = async (values) => {
        try {
            if (editingProduct) {
                await api.put(`/admin/products/${editingProduct.sku_code}`, values);
                messageApi.success('Product updated successfully');
            } else {
                await api.post('/admin/products', values);
                messageApi.success('Product created successfully');
            }
            setModalVisible(false);
            fetchProducts();
        } catch (error) {
            messageApi.error(error.response?.data?.detail || 'Operation failed');
        }
    };

    const handleExport = async () => {
        try {
            messageApi.info('Exporting data...');
            const response = await api.get('/admin/products', {
                params: { page_size: 2000 }
            });

            const data = response.data.data;
            const headers = ['SKU', 'Name', 'Category', 'Brand', 'Principal', 'Price Segment', 'Variant', 'Status'];
            const csvContent = [
                headers.join(','),
                ...data.map(item => [
                    item.sku_code,
                    `"${item.product_name}"`,
                    item.category_id,
                    item.brand_id,
                    item.principal_id,
                    item.price_segment,
                    item.variant,
                    item.is_active ? 'Active' : 'Inactive'
                ].join(','))
            ].join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'products.csv');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            messageApi.success('Export completed');
        } catch (error) {
            messageApi.error('Export failed');
        }
    };

    const columns = [
        {
            title: 'Identity',
            dataIndex: 'product_name',
            key: 'product_name',
            width: 450,
            fixed: 'left',
            sorter: { multiple: 5 },
            sortOrder: sorters.find(s => s.field === 'product_name')?.order || null,
            filteredValue: searchText ? [searchText] : null,
            filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
                <div style={{ padding: 12, minWidth: 280 }}>
                    <div style={{ marginBottom: 16 }}>
                        <Typography.Text strong style={{ fontSize: '12px' }}>Sort Identity By</Typography.Text>
                        <div style={{ marginTop: 4 }}>
                            <Radio.Group
                                size="small"
                                value={identitySortField}
                                onChange={e => {
                                    setIdentitySortField(e.target.value);
                                    // Trigger a fake table change to re-sort
                                    const currentNameSorter = sorters.find(s => s.field === identitySortField) || { order: 'ascend' };
                                    handleTableChange(pagination, {}, { field: 'product_name', order: currentNameSorter.order });
                                }}
                            >
                                <Radio.Button value="product_name">Name</Radio.Button>
                                <Radio.Button value="sku_code">SKU</Radio.Button>
                                <Radio.Button value="brand_id">Brand</Radio.Button>
                                <Radio.Button value="parent_sku_code">Parent</Radio.Button>
                            </Radio.Group>
                        </div>
                    </div>
                    <div style={{ marginBottom: 12 }}>
                        <Typography.Text strong style={{ fontSize: '12px' }}>Search Master Identity</Typography.Text>
                        <Input
                            placeholder="Name, SKU, Parent, Alias, etc..."
                            value={selectedKeys[0]}
                            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
                            onPressEnter={() => confirm()}
                            style={{ width: '100%', marginTop: 4 }}
                            prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                        />
                    </div>
                    <div style={{ marginBottom: 16 }}>
                        <Typography.Text strong style={{ fontSize: '12px' }}>Brand Quick-Filter</Typography.Text>
                        <Select
                            mode="multiple"
                            style={{ width: '100%', marginTop: 4 }}
                            placeholder="Select Brands"
                            value={brandFilter}
                            onChange={(val) => setBrandFilter(val)}
                            maxTagCount="responsive"
                            allowClear
                        >
                            {dependentFilters.brands.map(b => (
                                <Select.Option key={b.value} value={b.value || ""}>{b.text}</Select.Option>
                            ))}
                        </Select>
                    </div>
                    <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                        <Button
                            type="primary"
                            onClick={() => confirm()}
                            size="small"
                        >
                            Apply Filters
                        </Button>
                        <Button onClick={() => {
                            clearFilters();
                            setBrandFilter([]);
                        }} size="small">
                            Reset
                        </Button>
                    </Space>
                </div>
            ),
            filterIcon: filtered => <SearchOutlined style={{ color: filtered || brandFilter.length > 0 ? '#1890ff' : undefined }} />,
            render: (text, record) => (
                <div style={{
                    padding: '8px 0',
                    borderLeft: record.level > 0 ? (record.level === 1 ? '3px solid #69c0ff' : '3px solid #adc6ff') : 'none',
                    paddingLeft: record.level > 0 ? '16px' : 0,
                    marginLeft: record.level > 0 ? (record.level === 1 ? '-14px' : '-16px') : 0,
                    background: record.level > 0 ? (record.level === 1 ? 'linear-gradient(90deg, #f0f5ff 0%, #ffffff 100%)' : 'linear-gradient(90deg, #f5f5f5 0%, #ffffff 100%)') : 'transparent',
                    borderRadius: '0 4px 4px 0',
                    display: 'flex',
                    flexDirection: 'column',
                    width: 'calc(100% + 20px)'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{
                            fontFamily: 'SFMono-Regular, Consolas, Courier New, monospace',
                            fontSize: '9px',
                            padding: '1px 4px',
                            background: record.level > 0 ? '#1890ff' : '#f0f0f0',
                            border: '1px solid #d9d9d9',
                            borderRadius: '3px',
                            color: record.level > 0 ? '#fff' : '#434343',
                            fontWeight: 700
                        }}>{record.sku_code}</span>
                        <span style={{
                            fontWeight: record.level === 0 ? 700 : 500,
                            fontSize: record.level === 0 ? '14px' : '13px',
                            color: record.level === 0 ? '#141414' : '#434343'
                        }}>{text}</span>
                    </div>

                    <div style={{ marginBottom: '6px', display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center' }}>
                        {record.short_name && (
                            <Tag style={{ fontSize: '10px', margin: 0, background: '#fff', border: '1px solid #f0f0f0', fontStyle: 'italic', color: '#595959' }}>
                                "{record.short_name}"
                            </Tag>
                        )}
                        {record.brand_id && (
                            <Tag style={{ fontSize: '10px', margin: 0, background: '#fff7e6', color: '#d46b08', border: 'none', fontWeight: 600 }}>
                                {getOfficialName(brands, record.brand_id)}
                            </Tag>
                        )}
                        {record.variant && (
                            <span style={{ fontSize: '11px', color: '#8c8c8c' }}>• {record.variant}</span>
                        )}
                    </div>

                    {record.parent_sku_code && record.level > 0 && (
                        <div style={{
                            fontSize: '11px',
                            color: '#1890ff',
                            background: '#e6f7ff',
                            padding: '2px 8px',
                            borderRadius: '4px',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            marginTop: '2px'
                        }}>
                            <span style={{ fontWeight: 800 }}>↴ PARENT:</span>
                            <span style={{ fontWeight: 600 }}>{record.parent_sku_code}</span>
                            <span style={{ fontSize: '10px', opacity: 0.8 }}>{record.parent_sku_name}</span>
                        </div>
                    )}
                </div>
            )
        },
        {
            title: 'Category',
            dataIndex: 'category_id',
            key: 'category_id',
            width: 140,
            sorter: { multiple: 1 },
            sortOrder: sorters.find(s => s.field === 'category_id')?.order || null,
            filteredValue: categoryFilter.length > 0 ? categoryFilter : null,
            filters: dependentFilters.categories,
            filterSearch: true,
            filterMultiple: true,
            render: (catId) => (
                <Tag style={{ fontSize: '10px', background: '#f0f5ff', color: '#1d39c4', border: 'none', fontWeight: 600 }}>
                    {getOfficialName(categories, catId)}
                </Tag>
            )
        },
        {
            title: 'Principal',
            dataIndex: 'principal_id',
            key: 'principal_id',
            width: 160,
            sorter: { multiple: 2 },
            sortOrder: sorters.find(s => s.field === 'principal_id')?.order || null,
            filteredValue: principalFilter.length > 0 ? principalFilter : null,
            filters: dependentFilters.principals,
            filterSearch: true,
            filterMultiple: true,
            render: (p) => (
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#434343' }}>
                    {getOfficialName(principals, p)}
                </span>
            )
        },
        {
            title: 'Price Segment (Eceran)',
            dataIndex: 'price_segment',
            key: 'price_segment',
            width: 160,
            sorter: { multiple: 3 },
            sortOrder: sorters.find(s => s.field === 'price_segment')?.order || null,
            filteredValue: priceSegmentFilter.length > 0 ? priceSegmentFilter : null,
            filters: dependentFilters.priceSegments,
            filterSearch: true,
            filterMultiple: true,
            render: (p) => <span style={{ fontSize: '12px', color: '#595959' }}>{p || '-'}</span>
        },
        {
            title: 'Company',
            dataIndex: 'company_id',
            key: 'company_id',
            width: 120,
            filteredValue: companyFilter.length > 0 ? companyFilter : null,
            filters: dependentFilters.companies,
            render: (cid) => (
                <Tag color="blue" style={{ fontSize: '10px' }}>
                    {getOfficialName(companies, cid)}
                </Tag>
            )
        },
        {
            title: 'UOM Conversion',
            key: 'uom',
            width: 180,
            render: (_, record) => {
                const parts = [];
                if (record.uom_small) parts.push({ label: record.uom_small, qty: 1 });
                if (record.uom_medium && record.isi_pcs_per_medium) parts.push({ label: record.uom_medium, qty: record.isi_pcs_per_medium });
                if (record.uom_large && record.isi_pcs_per_large) parts.push({ label: record.uom_large, qty: record.isi_pcs_per_large });

                return (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        {parts.map((p, i) => (
                            <React.Fragment key={p.label}>
                                <div style={{ textAlign: 'center', minWidth: '35px' }}>
                                    <div style={{ fontSize: '10px', fontWeight: 700, color: '#262626', lineHeight: '1' }}>{p.label}</div>
                                    <div style={{ fontSize: '9px', color: '#8c8c8c' }}>{p.qty}</div>
                                </div>
                                {i < parts.length - 1 && <div style={{ color: '#d9d9d9', fontSize: '10px' }}>➔</div>}
                            </React.Fragment>
                        ))}
                        {parts.length === 0 && <span style={{ color: '#bfbfbf' }}>-</span>}
                    </div>
                );
            }
        },
        {
            title: 'Status',
            dataIndex: 'is_active',
            key: 'status',
            width: 120,
            sorter: { multiple: 6 },
            sortOrder: sorters.find(s => s.field === 'is_active')?.order || null,
            filteredValue: (activeFilter.length > 0 || nplFilter) ? [...activeFilter, ...(nplFilter ? ['npl'] : [])] : null,
            filters: dependentFilters.status,
            filterMultiple: true,
            render: (is_active, record) => (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <Tag
                        color={is_active ? 'success' : 'default'}
                        style={{
                            borderRadius: '12px',
                            fontSize: '10px',
                            fontWeight: 600,
                            textAlign: 'center',
                            marginRight: 0,
                            padding: '0 10px',
                            border: 'none',
                            background: is_active ? '#f6ffed' : '#f5f5f5',
                            color: is_active ? '#389e0d' : '#8c8c8c'
                        }}
                    >
                        {is_active ? '● ACTIVE' : '○ INACTIVE'}
                    </Tag>
                    {record.is_npl && (
                        <Tag color="orange" style={{ fontSize: '9px', borderRadius: '4px', border: 'none', marginRight: 0, textAlign: 'center' }}>NEW LAUNCH</Tag>
                    )}
                </div>
            )
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 100,
            fixed: 'right',
            render: (_, record) => (
                <Space size="small">
                    <Button
                        type="link"
                        size="small"
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    />
                    <Popconfirm
                        title="Delete product?"
                        onConfirm={() => handleDelete(record.sku_code)}
                        okText="Yes"
                        cancelText="No"
                    >
                        <Button
                            type="link"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                        />
                    </Popconfirm>
                </Space>
            )
        }
    ];

    return (
        <App>
            <div style={{ padding: 24 }}>
                <Card>
                    <div style={{ marginBottom: 24 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                            <div>
                                <Typography.Title level={3} style={{ margin: 0, fontWeight: 700, letterSpacing: '-0.5px' }}>
                                    Product Management
                                </Typography.Title>
                                <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                                    Manage your product catalog, evolution, and UOM conversions.
                                </Typography.Text>
                            </div>
                            <Space size="middle">
                                <Button icon={<ExportOutlined />} onClick={handleExport} style={{ fontWeight: 500 }}>Export</Button>
                                <Button icon={<ReloadOutlined />} onClick={() => fetchProducts()} style={{ fontWeight: 500 }}>Refresh</Button>
                                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate} style={{ fontWeight: 600, padding: '0 20px' }}>Add Product</Button>
                            </Space>
                        </div>

                        <div style={{
                            background: '#fafafa',
                            padding: '16px',
                            borderRadius: '10px',
                            border: '1px solid #f0f0f0',
                            display: 'flex',
                            gap: 12,
                            flexWrap: 'wrap',
                            alignItems: 'center'
                        }}>
                            <Input
                                placeholder="Search by SKU or Product Name"
                                prefix={<SearchOutlined style={{ color: '#bfbfbf' }} />}
                                style={{ width: 320, height: 36 }}
                                value={searchText}
                                onChange={(e) => setSearchText(e.target.value)}
                                onPressEnter={handleSearch}
                                allowClear
                            />
                            <Button type="primary" onClick={handleReset} style={{ height: 36, padding: '0 24px', fontWeight: 600 }}>
                                Reset All Filters
                            </Button>

                            {/* Company Filter (Admin Only) */}
                            {companies.length > 0 && (
                                <Select
                                    mode="multiple"
                                    style={{ width: 200 }}
                                    placeholder="Filter by Company"
                                    value={companyFilter}
                                    onChange={setCompanyFilter}
                                    allowClear
                                >
                                    {dependentFilters.companies.map(c => (
                                        <Select.Option key={c.value} value={c.value || ""}>{c.text}</Select.Option>
                                    ))}
                                </Select>
                            )}
                        </div>
                    </div>

                    <Table
                        columns={columns}
                        dataSource={displayData}
                        loading={loading}
                        rowKey="sku_code"
                        pagination={false}
                        scroll={{ x: 1500, y: 'calc(100vh - 380px)' }}
                        size="small"
                        onChange={handleTableChange}
                        indentSize={32}
                        expandable={{
                            defaultExpandAllRows: false,
                            expandIcon: ({ expanded, onExpand, record }) =>
                                record.children ? (
                                    <div
                                        onClick={e => onExpand(record, e)}
                                        style={{
                                            cursor: 'pointer',
                                            marginRight: 8,
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            width: 20,
                                            height: 20,
                                            borderRadius: '4px',
                                            background: expanded ? '#fff1f0' : '#f6ffed',
                                            border: `1px solid ${expanded ? '#ffa39e' : '#b7eb8f'}`,
                                            color: expanded ? '#cf1322' : '#389e0d',
                                            fontWeight: 'bold',
                                            fontSize: '14px'
                                        }}
                                    >
                                        {expanded ? '−' : '+'}
                                    </div>
                                ) : <span style={{ width: 28 }} />
                        }}
                    />
                </Card>

                <Modal
                    title={editingProduct ? 'Edit Product' : 'Create Product'}
                    open={modalVisible}
                    onCancel={() => setModalVisible(false)}
                    footer={null}
                    width={700}
                >
                    <Form
                        form={form}
                        layout="vertical"
                        onFinish={handleSubmit}
                        initialValues={{ is_active: true, is_npl: false }}
                    >
                        <Tabs defaultActiveKey="1">
                            <TabPane tab="Basic Info" key="1">
                                <Form.Item
                                    name="sku_code"
                                    label="SKU Code"
                                    rules={[{ required: true, message: 'Please enter SKU code' }]}
                                >
                                    <Input disabled={!!editingProduct} />
                                </Form.Item>
                                <Form.Item
                                    name="product_name"
                                    label="Product Name"
                                    rules={[{ required: true, message: 'Please enter product name' }]}
                                >
                                    <Input />
                                </Form.Item>
                                <Form.Item
                                    name="short_name"
                                    label="Short Name"
                                >
                                    <Input />
                                </Form.Item>
                                <Form.Item
                                    name="parent_sku_code"
                                    label="Parent SKU"
                                >
                                    <AutoComplete
                                        options={flatProducts.map(p => ({ value: p.sku_code, label: `${p.sku_code} - ${p.product_name}` }))}
                                        placeholder="Select parent product"
                                        filterOption={(inputValue, option) =>
                                            option.label.toUpperCase().indexOf(inputValue.toUpperCase()) !== -1
                                        }
                                    />
                                </Form.Item>
                                <Form.Item
                                    name="category_id"
                                    label="Category"
                                    rules={[{ required: true, message: 'Please select category' }]}
                                >
                                    <Select showSearch>
                                        {categories.map(cat => (
                                            <Select.Option key={cat.id} value={cat.id || ""}>{cat.name}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                                <Form.Item
                                    name="brand_id"
                                    label="Brand"
                                    rules={[{ required: true, message: 'Please select brand' }]}
                                >
                                    <Select showSearch>
                                        {brands.map(b => (
                                            <Select.Option key={b.id} value={b.id || ""}>{b.name || b.id}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                                <Form.Item
                                    name="principal_id"
                                    label="Principal"
                                >
                                    <Select showSearch allowClear>
                                        {principals.map(p => (
                                            <Select.Option key={p.id} value={p.id || ""}>{p.name || p.id}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                                <Form.Item
                                    name="variant"
                                    label="Variant"
                                >
                                    <Input />
                                </Form.Item>
                                <Form.Item
                                    name="price_segment"
                                    label="Price Segment"
                                >
                                    <Input />
                                </Form.Item>
                                <Form.Item
                                    name="company_id"
                                    label="Company"
                                    rules={[{ required: true, message: 'Please select company' }]}
                                >
                                    <Select showSearch>
                                        {companies.map(c => (
                                            <Select.Option key={c.id} value={c.id || ""}>{c.name || c.id}</Select.Option>
                                        ))}
                                    </Select>
                                </Form.Item>
                            </TabPane>

                            <TabPane tab="Unit of Measure" key="2">
                                <Typography.Text type="secondary">Small UOM</Typography.Text>
                                <Space style={{ display: 'flex', marginBottom: 16 }}>
                                    <Form.Item name="uom_small" label="Unit Name" style={{ marginBottom: 0 }}>
                                        <Input placeholder="e.g., PCS" />
                                    </Form.Item>
                                    <Form.Item name="isi_pcs_per_small" label="Conversion" style={{ marginBottom: 0 }}>
                                        <InputNumber min={0} placeholder="pieces" />
                                    </Form.Item>
                                </Space>

                                <Typography.Text type="secondary">Medium UOM</Typography.Text>
                                <Space style={{ display: 'flex', marginBottom: 16 }}>
                                    <Form.Item name="uom_medium" label="Unit Name" style={{ marginBottom: 0 }}>
                                        <Input placeholder="e.g., BOX" />
                                    </Form.Item>
                                    <Form.Item name="isi_pcs_per_medium" label="Conversion" style={{ marginBottom: 0 }}>
                                        <InputNumber min={0} placeholder="pieces" />
                                    </Form.Item>
                                </Space>

                                <Typography.Text type="secondary">Large UOM</Typography.Text>
                                <Space style={{ display: 'flex', marginBottom: 16 }}>
                                    <Form.Item name="uom_large" label="Unit Name" style={{ marginBottom: 0 }}>
                                        <Input placeholder="e.g., CARTON" />
                                    </Form.Item>
                                    <Form.Item name="isi_pcs_per_large" label="Conversion" style={{ marginBottom: 0 }}>
                                        <InputNumber min={0} placeholder="pieces" />
                                    </Form.Item>
                                </Space>
                            </TabPane>

                            <TabPane tab="Status" key="3">
                                <Form.Item name="is_active" valuePropName="checked" label="Active Status">
                                    <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
                                </Form.Item>
                                <Form.Item name="is_npl" valuePropName="checked" label="New Product Launch (NPL)">
                                    <Switch checkedChildren="NPL" unCheckedChildren="Regular" />
                                </Form.Item>
                            </TabPane>
                        </Tabs>

                        <Form.Item style={{ marginTop: 16 }}>
                            <Space style={{ display: 'flex', justifyContent: 'flex-end' }}>
                                <Button onClick={() => setModalVisible(false)}>Cancel</Button>
                                <Button type="primary" htmlType="submit">
                                    {editingProduct ? 'Update' : 'Create'}
                                </Button>
                            </Space>
                        </Form.Item>
                    </Form>
                </Modal>
            </div>
        </App >
    );
};

export default Products;
