// AppLayout — authenticated shell wrapping all protected pages
import { Outlet } from "react-router-dom";
import { AppSidebar } from "../components/AppSidebar";

export default function AppLayout() {
  return (
    <div className="flex min-h-screen w-full bg-background">
      <AppSidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Outlet />
      </div>
    </div>
  );
}
