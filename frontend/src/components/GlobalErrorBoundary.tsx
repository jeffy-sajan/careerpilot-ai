import { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";
import { Topbar } from "./ui-kit";

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class GlobalErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col min-h-screen bg-background">
          <Topbar title="Unexpected Error" />
          <div className="flex flex-1 items-center justify-center p-4">
            <div className="text-center space-y-6 max-w-md w-full">
              <div className="mx-auto w-24 h-24 bg-destructive/10 rounded-full flex items-center justify-center mb-6">
                <AlertTriangle className="w-12 h-12 text-destructive" />
              </div>

              <div className="space-y-2">
                <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
                  Something went wrong
                </h1>
                <p className="text-muted-foreground text-sm">
                  We're sorry, but an unexpected error occurred. Our team has
                  been notified.
                </p>
                {this.state.error && process.env.NODE_ENV === "development" && (
                  <div className="mt-4 p-4 bg-muted/50 rounded text-left overflow-auto max-h-48 text-xs font-mono text-muted-foreground">
                    {this.state.error.toString()}
                  </div>
                )}
              </div>

              <div className="flex justify-center pt-4">
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center justify-center h-10 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md text-sm font-medium transition-colors"
                >
                  <RefreshCcw className="w-4 h-4 mr-2" />
                  Refresh Page
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
