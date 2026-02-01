import ReactECharts from 'echarts-for-react';

const ForecastChart = ({ historicalData, forecastData }) => {
    if (!historicalData || !forecastData || historicalData.length === 0 || forecastData.length === 0) {
        return <div style={{ textAlign: 'center', padding: '40px' }}>No data available</div>;
    }

    // Combine historical and forecast data
    const regions = [...new Set([...historicalData.map(d => d.region), ...forecastData.map(d => d.region)])];

    const option = {
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'cross'
            }
        },
        legend: {
            data: regions.flatMap(r => [`Region ${r} - Historical`, `Region ${r} - Forecast`]),
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
            boundaryGap: false,
            data: [
                ...historicalData.map(d => d.week_start.substring(5, 10)),
                ...forecastData.map(d => d.week_start.substring(5, 10))
            ].filter((v, i, a) => a.indexOf(v) === i)
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
            const histData = historicalData.filter(d => d.region === region);
            const fcstData = forecastData.filter(d => d.region === region);

            return [
                {
                    name: `Region ${region} - Historical`,
                    type: 'line',
                    smooth: true,
                    data: histData.map(d => d.revenue),
                    lineStyle: {
                        width: 3
                    },
                    emphasis: {
                        focus: 'series'
                    }
                },
                {
                    name: `Region ${region} - Forecast`,
                    type: 'line',
                    smooth: true,
                    data: Array(histData.length).fill('-').concat(fcstData.map(d => d.forecast_revenue)),
                    lineStyle: {
                        type: 'dashed',
                        width: 2
                    },
                    itemStyle: {
                        opacity: 0.6
                    },
                    emphasis: {
                        focus: 'series'
                    }
                }
            ];
        })
    };

    return <ReactECharts option={option} style={{ height: '350px' }} />;
};

export default ForecastChart;
