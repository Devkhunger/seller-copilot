import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      const message = this.state.error?.message || "Something went wrong while loading this page.";

      return (
        <main className="grid min-h-screen place-items-center bg-slate-50 p-5">
          <div className="card w-full max-w-xl">
            <p className="text-xs font-black uppercase tracking-wide text-merchant">AI Seller Copilot</p>
            <h1 className="mt-2 text-3xl font-black text-slate-900">We hit a render error</h1>
            <p className="mt-3 text-slate-600">{message}</p>
            <p className="mt-3 text-sm text-slate-500">Try refreshing the page. If you recently deployed, make sure the latest frontend bundle is live and your session is still valid.</p>
            <button className="btn mt-5" onClick={() => window.location.reload()}>Refresh page</button>
          </div>
        </main>
      );
    }

    return this.props.children;
  }
}
