import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./layout/AppShell";
import SetupPage from "./features/setup/SetupPage";
import FleetPage from "./features/fleet/FleetPage";
import VehiclesPage from "./features/vehicles/VehiclesPage";
import CommandsPage from "./features/commands/CommandsPage";
import DeveloperPage from "./features/developer/DeveloperPage";
import "./layout/AppShell.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/setup" replace />} />
          <Route path="setup" element={<SetupPage />} />
          <Route path="fleet" element={<FleetPage />} />
          <Route path="vehicles" element={<VehiclesPage />} />
          <Route path="commands" element={<CommandsPage />} />
          <Route path="developer" element={<DeveloperPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
