import React from 'react';

type ErrorBoundaryState = {
  error: Error | null;
  errorStack?: string;
};

export default class ErrorBoundary extends React.Component<
  React.PropsWithChildren,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Ensure this shows up in the browser console.
    console.error('Unhandled UI error:', error, errorInfo);
    this.setState({ errorStack: errorInfo.componentStack ?? undefined });
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (!this.state.error) {
      return this.props.children;
    }

    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-3xl mx-auto bg-white border border-red-200 rounded-lg shadow p-6">
          <h1 className="text-xl font-semibold text-red-700 mb-2">UI crashed</h1>
          <p className="text-gray-700 mb-4">
            Something threw an exception while rendering. The details are logged to the browser
            console.
          </p>

          <div className="mb-4">
            <div className="text-sm font-medium text-gray-900 mb-1">Error</div>
            <pre className="text-xs bg-gray-900 text-gray-100 p-3 rounded overflow-auto">
              {this.state.error.message}
            </pre>
          </div>

          {this.state.errorStack && (
            <div className="mb-4">
              <div className="text-sm font-medium text-gray-900 mb-1">Component stack</div>
              <pre className="text-xs bg-gray-100 text-gray-800 p-3 rounded overflow-auto">
                {this.state.errorStack}
              </pre>
            </div>
          )}

          <button
            onClick={this.handleReload}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Reload
          </button>
        </div>
      </div>
    );
  }
}
