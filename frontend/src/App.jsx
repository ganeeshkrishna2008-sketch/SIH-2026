import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import DashboardView from './views/DashboardView';
import VehicleSearchView from './views/VehicleSearchView';
import TrajectoryView from './views/TrajectoryView';
import AnalyticsView from './views/AnalyticsView';
import AlertsView from './views/AlertsView';
import ANPRView from './views/ANPRView';
import CameraActivityView from './views/CameraActivityView';
import { fetchAlerts } from './services/api';

export default function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [selectedPlate, setSelectedPlate] = useState('TS09AB1234');
  const [pendingAlertCount, setPendingAlertCount] = useState(0);
  const [themeMode, setThemeMode] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  useEffect(() => {
    localStorage.setItem('theme', themeMode);
    
    const applyTheme = () => {
      const isDark = 
        themeMode === 'dark' || 
        (themeMode === 'device' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        
      if (isDark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    };

    applyTheme();

    if (themeMode === 'device') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handler = () => applyTheme();
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
  }, [themeMode]);

  useEffect(() => {
    async function loadAlertStats() {
      try {
        const alerts = await fetchAlerts();
        const pending = alerts.filter(a => a.status === 'PENDING_REVIEW').length;
        setPendingAlertCount(pending);
      } catch (err) {
        console.error('Error fetching alert stats:', err);
      }
    }
    loadAlertStats();
  }, [currentTab]);

  const handleSelectPlate = (plate) => {
    setSelectedPlate(plate);
    setCurrentTab('trajectory');
  };

  const handleSearchNavigateToTrajectory = (plate) => {
    setSelectedPlate(plate);
    setCurrentTab('trajectory');
  };

  const handleNavigateToSearch = (plate) => {
    setSelectedPlate(plate);
    setCurrentTab('search');
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans transition-colors duration-200">
      <Navbar themeMode={themeMode} setThemeMode={setThemeMode} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          currentTab={currentTab}
          setCurrentTab={setCurrentTab}
          alertCount={pendingAlertCount}
        />

        <main className="flex-1 overflow-y-auto p-6 bg-slate-900/30">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'dashboard' && (
              <DashboardView onSelectPlate={handleSelectPlate} />
            )}
            {currentTab === 'anpr' && (
              <ANPRView />
            )}
            {currentTab === 'search' && (
              <VehicleSearchView
                initialPlate={selectedPlate}
                onNavigateToTrajectory={handleSearchNavigateToTrajectory}
              />
            )}
            {currentTab === 'camera-activity' && (
              <CameraActivityView
                onNavigateToVehicleHistory={handleNavigateToSearch}
              />
            )}
            {currentTab === 'trajectory' && (
              <TrajectoryView selectedPlate={selectedPlate} />
            )}
            {currentTab === 'analytics' && (
              <AnalyticsView />
            )}
            {currentTab === 'alerts' && (
              <AlertsView onSelectPlate={handleSelectPlate} />
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
