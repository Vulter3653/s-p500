import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Dashboard render failure", error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.error) {
      return <main className="fatal-error"><h1>연구 보고서를 표시하지 못했습니다.</h1><p>브라우저에서 데이터 처리 중 오류가 발생했습니다.</p><pre>{String(this.state.error?.message || this.state.error)}</pre><button type="button" onClick={() => window.location.reload()}>다시 불러오기</button></main>;
    }
    return this.props.children;
  }
}
