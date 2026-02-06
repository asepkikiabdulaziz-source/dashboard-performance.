import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import App from './App.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import './index.css'

// Ant Design theme configuration
const theme = {
    token: {
        colorPrimary: '#1890ff',
        borderRadius: 8,
        colorBgContainer: '#ffffff',
    },
}

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <ConfigProvider theme={theme}>
            <ErrorBoundary>
                <App />
            </ErrorBoundary>
        </ConfigProvider>
    </React.StrictMode>,
)
