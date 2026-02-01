import ReactECharts from 'echarts-for-react';

const RegionComparison = ({ data }) => {
    if (!data || data.length === 0) {
        return <div style={{ textAlign: 'center', padding: '40px' }}>No data available</div>;
    }

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            }
        },
        legend: {
            data: ['Revenue', 'Achievement Rate (%)', 'Growth Rate (%)'],
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
            data: data.map(d => `Region ${d.region}`)
        },
        yAxis: [
            {
                type: 'value',
                name: 'Revenue',
                position: 'left',
                axisLabel: {
                    formatter: function (value) {
                        return (value / 1000000).toFixed(1) + 'M';
                    }
                }
            },
            {
                type: 'value',
                name: 'Percentage',
                position: 'right',
                axisLabel: {
                    formatter: '{value}%'
                }
            }
        ],
        series: [
            {
                name: 'Revenue',
                type: 'bar',
                data: data.map(d => d.total_revenue),
                itemStyle: {
                    color: '#1890ff'
                },
                emphasis: {
                    focus: 'series'
                }
            },
            {
                name: 'Achievement Rate (%)',
                type: 'line',
                yAxisIndex: 1,
                data: data.map(d => d.achievement_rate),
                smooth: true,
                itemStyle: {
                    color: '#52c41a'
                },
                emphasis: {
                    focus: 'series'
                }
            },
            {
                name: 'Growth Rate (%)',
                type: 'line',
                yAxisIndex: 1,
                data: data.map(d => d.growth_rate),
                smooth: true,
                itemStyle: {
                    color: '#fa8c16'
                },
                emphasis: {
                    focus: 'series'
                }
            }
        ]
    };

    return <ReactECharts option={option} style={{ height: '350px' }} />;
};

export default RegionComparison;
