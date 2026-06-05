import { Link } from "react-router-dom";
import { AlertCircle, ArrowLeft, Home } from "lucide-react";
import { Topbar } from "../components/ui-kit";

export default function NotFoundPage() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Topbar title="Page Not Found" />
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="text-center space-y-6 max-w-md w-full">
          <div className="mx-auto w-24 h-24 bg-muted/50 rounded-full flex items-center justify-center mb-6">
            <AlertCircle className="w-12 h-12 text-muted-foreground" />
          </div>

          <div className="space-y-2">
            <h1 className="font-display text-4xl font-bold tracking-tight text-foreground">
              404
            </h1>
            <h2 className="text-xl font-medium text-foreground">
              Page not found
            </h2>
            <p className="text-muted-foreground">
              The page you're looking for doesn't exist or has been moved.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
            <Link
              to=".."
              onClick={(e) => {
                e.preventDefault();
                window.history.back();
              }}
              className="inline-flex items-center justify-center h-10 px-4 py-2 bg-secondary text-secondary-foreground hover:bg-secondary/80 rounded-md text-sm font-medium transition-colors"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Go Back
            </Link>
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-center h-10 px-4 py-2 bg-primary text-primary-foreground hover:bg-primary/90 rounded-md text-sm font-medium transition-colors"
            >
              <Home className="w-4 h-4 mr-2" />
              Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
