import ReactECharts from 'echarts-for-react';

const TargetChart = ({ data }) => {
    if (!data || data.length === 0) {
        return <div style={{ textAlign: 'center', padding: '40px' }}>No data available</div>;
    }

    // Group by region
    const regions = [...new Set(data.map(d => d.region))];

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
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
            data: regions.flatMap(r => [`Region ${r} - Target`, `Region ${r} - Actual`]),
            top: 0,
            type: 'scroll'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '80px',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: [...new Set(data.map(d => d.week_start.substring(5, 10)))]
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: function (value) {
                    return (value / 1000000).toFixed(1) + 'M';
                }
            }
        },
        series: regions.flatMap(region => {
            const regionData = data.filter(d => d.region === region);
            return [
                {
                    name: `Region ${region} - Target`,
                    type: 'bar',
                    data: regionData.map(d => d.target),
                    itemStyle: {
                        opacity: 0.6
                    }
                },
                {
                    name: `Region ${region} - Actual`,
                    type: 'bar',
                    data: regionData.map(d => d.actual),
                    itemStyle: {
                        opacity: 0.9
                    }
                }
            ];
        })
    };

    return <ReactECharts option={option} style={{ height: '350px' }} />;
};

export default TargetChart;
