import { Component } from 'react';
import { clearAuthStorage } from '../utils/storage';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, info) {
        console.error('Unhandled application error:', error, info);
    }

    handleReload = () => {
        if (typeof window !== 'undefined') {
            window.location.reload();
        }
    };

    handleReset = () => {
        clearAuthStorage();
        this.handleReload();
    };

    render() {
        if (!this.state.hasError) {
            return this.props.children;
        }

        return (
            <div
                style={{
                    minHeight: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: '#f5f5f5',
                    color: '#1a1a1a',
                    padding: '24px'
                }}
            >
                <div style={{ maxWidth: '520px', textAlign: 'center' }}>
                    <h1 style={{ marginBottom: '12px' }}>Aplikasi gagal dimuat</h1>
                    <p style={{ marginBottom: '24px', color: '#4b4b4b' }}>
                        Coba muat ulang. Jika masih blank, reset data lokal untuk
                        menghapus sesi yang rusak.
                    </p>
                    <div
                        style={{
                            display: 'flex',
                            gap: '12px',
                            justifyContent: 'center',
                            flexWrap: 'wrap'
                        }}
                    >
                        <button
                            type="button"
                            onClick={this.handleReload}
                            style={{
                                padding: '10px 16px',
                                borderRadius: '6px',
                                border: '1px solid #1a1a1a',
                                background: '#1a1a1a',
                                color: '#ffffff',
                                cursor: 'pointer'
                            }}
                        >
                            Muat Ulang
                        </button>
                        <button
                            type="button"
                            onClick={this.handleReset}
                            style={{
                                padding: '10px 16px',
                                borderRadius: '6px',
                                border: '1px solid #d9d9d9',
                                background: '#ffffff',
                                color: '#1a1a1a',
                                cursor: 'pointer'
                            }}
                        >
                            Reset Data Lokal
                        </button>
                    </div>
                </div>
            </div>
        );
    }
}

export default ErrorBoundary;
