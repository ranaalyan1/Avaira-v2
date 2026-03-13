import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6 animate-slide-in" data-testid="not-found-page">
      <div className="cyber-card p-8 max-w-md w-full text-center">
        <p className="font-mono text-xs text-avaira-dim tracking-wider">ERROR 404</p>
        <h1 className="font-heading font-bold text-3xl text-foreground uppercase mt-2">Page Not Found</h1>
        <p className="font-mono text-xs text-avaira-muted mt-3">
          The route you requested does not exist.
        </p>
        <Link to="/" className="cyber-btn inline-block bg-avaira-primary text-white px-4 py-2 font-heading text-xs mt-6">
          Return Home
        </Link>
      </div>
    </div>
  );
}
