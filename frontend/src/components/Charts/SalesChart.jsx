import ReactECharts from 'echarts-for-react';

const SalesChart = ({ data }) => {
    if (!data || data.length === 0) {
        return <div style={{ textAlign: 'center', padding: '40px' }}>No data available</div>;
    }

    // Group data by region
    const regions = [...new Set(data.map(d => d.region))];

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            },
            formatter: function (params) {
                let result = `<strong>${params[0].axisValue}</strong><br/>`;
                params.forEach(param => {
                    const value = new Intl.NumberFormat('id-ID', {
                        style: 'currency',
                        currency: 'IDR',
                        minimumFractionDigits: 0,
                    }).format(param.value);
                    result += `${param.marker} ${param.seriesName}: ${value}<br/>`;
                });
                return result;
            }
        },
        legend: {
            data: regions.map(r => `Region ${r}`),
            top: 0
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '60px',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            boundaryGap: false,
            data: [...new Set(data.map(d => d.week_start.substring(5, 10)))]  // MM-DD format
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: function (value) {
                    return (value / 1000000).toFixed(1) + 'M';
                }
            }
        },
        series: regions.map(region => {
            const regionData = data.filter(d => d.region === region);
            return {
                name: `Region ${region}`,
                type: 'line',
                smooth: true,
                data: regionData.map(d => d.revenue),
                emphasis: {
                    focus: 'series'
                }
            };
        }),
        dataZoom: [
            {
                type: 'inside',
                start: 0,
                end: 100
            },
            {
                start: 0,
                end: 100
            }
        ]
    };

    return <ReactECharts option={option} style={{ height: '350px' }} />;
};

export default SalesChart;
